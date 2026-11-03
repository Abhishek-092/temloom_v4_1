#!/usr/bin/env python3
# =============================================================================
# trend_forecaster.py — Slow-Trend Forecaster (Holt-Winters / Prophet)
#
# Detects gradual, multi-cycle congestion drift that the BiLSTM's short window
# (30 timesteps) misses.  Produces a t+N_HORIZON forecast per telemetry channel.
#
# Default: Holt-Winters double exponential smoothing (statsmodels) — same
# trend-detection value as Prophet, but needs no seasonality history.
# Prophet is gated behind a PROPHET_MIN_SAMPLES threshold — only switched in
# once enough cyclical history exists to make seasonality decomposition valid.
#
# The forecaster output feeds the Predictive Digital Twin (digital_twin.py).
#
# Usage:
#   from trend_forecaster import TrendForecaster
#   fc = TrendForecaster()
#   fc.update("queue_depth_pe1", value)
#   prediction = fc.forecast("queue_depth_pe1")   # returns t+30s estimate
# =============================================================================
import collections
import numpy as np

try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

try:
    from prophet import Prophet
    import pandas as pd
    HAS_PROPHET = True
except ImportError:
    HAS_PROPHET = False

N_HORIZON       = 30    # forecast steps ahead (seconds at 1s scrape)
MIN_FIT_SAMPLES = 30    # minimum history before we fit any model
PROPHET_MIN_SAMPLES = 1000  # history needed before Prophet seasonality is credible


class ChannelForecaster:
    """
    Single-channel exponential-smoothing forecaster.
    Maintains a rolling history buffer, fits Holt-Winters on each call,
    and returns the t+N_HORIZON point estimate.
    """

    def __init__(self, channel_name: str, maxlen: int = 500):
        self.name = channel_name
        self._history: collections.deque = collections.deque(maxlen=maxlen)
        self._last_forecast: float | None = None

    def update(self, value: float):
        self._history.append(float(value))

    def forecast(self) -> float | None:
        """
        Returns the t+N_HORIZON point forecast, or None if not enough data.
        """
        n = len(self._history)
        if n < MIN_FIT_SAMPLES:
            return None

        series = np.array(self._history, dtype=float)

        # Try Prophet if we have enough history and it's installed
        if HAS_PROPHET and n >= PROPHET_MIN_SAMPLES:
            try:
                df = pd.DataFrame({"ds": pd.date_range("2000-01-01", periods=n, freq="s"),
                                   "y": series})
                m = Prophet(yearly_seasonality=False, weekly_seasonality=False,
                            daily_seasonality=True, interval_width=0.80)
                m.fit(df, algorithm="Newton")
                future = m.make_future_dataframe(periods=N_HORIZON, freq="s")
                forecast_df = m.predict(future)
                pred = float(forecast_df["yhat"].iloc[-1])
                self._last_forecast = pred
                return pred
            except Exception:
                pass  # fall through to Holt-Winters

        # Default: Holt-Winters double exponential smoothing
        if HAS_STATSMODELS:
            try:
                model = ExponentialSmoothing(
                    series,
                    trend="add",
                    seasonal=None,        # no seasonality claim on short data
                    initialization_method="estimated",
                )
                fit = model.fit(optimized=True, remove_bias=False)
                forecast = fit.forecast(N_HORIZON)
                pred = float(forecast[-1])
                self._last_forecast = pred
                return pred
            except Exception:
                pass

        # Fallback: simple linear extrapolation using last 10 points
        window = series[-10:]
        if len(window) >= 2:
            slope = (window[-1] - window[0]) / (len(window) - 1)
            pred = float(window[-1] + slope * N_HORIZON)
            self._last_forecast = pred
            return pred

        return None

    @property
    def current_value(self) -> float | None:
        return self._history[-1] if self._history else None

    @property
    def history_len(self) -> int:
        return len(self._history)


class TrendForecaster:
    """
    Multi-channel slow-trend forecaster.  One ChannelForecaster per metric.
    Designed to be polled once per scrape cycle by the Digital Twin.
    """

    def __init__(self):
        self._channels: dict[str, ChannelForecaster] = {}

    def update(self, channel: str, value: float):
        if channel not in self._channels:
            self._channels[channel] = ChannelForecaster(channel)
        self._channels[channel].update(value)

    def update_batch(self, metrics: dict[str, float]):
        for ch, val in metrics.items():
            self.update(ch, val)

    def forecast(self, channel: str) -> float | None:
        if channel not in self._channels:
            return None
        return self._channels[channel].forecast()

    def forecast_all(self) -> dict[str, float | None]:
        return {ch: fc.forecast() for ch, fc in self._channels.items()}

    def get_divergence(self, channel: str, actual: float) -> float | None:
        """
        Returns |forecast - actual| as an absolute divergence score,
        or None if no forecast is available.
        """
        pred = self.forecast(channel)
        if pred is None:
            return None
        return abs(pred - actual)

    def channels_ready(self) -> list[str]:
        """Channels that have enough history for a valid forecast."""
        return [ch for ch, fc in self._channels.items()
                if fc.history_len >= MIN_FIT_SAMPLES]

    def summary(self) -> str:
        lines = [f"TrendForecaster — {len(self._channels)} channels"]
        for ch, fc in list(self._channels.items())[:10]:
            pred = fc._last_forecast
            cur  = fc.current_value
            lines.append(
                f"  {ch[:40]:40s}  cur={cur:.4f}  t+{N_HORIZON}s={pred:.4f}"
                if pred is not None and cur is not None
                else f"  {ch[:40]:40s}  [warming up: {fc.history_len}/{MIN_FIT_SAMPLES}]"
            )
        if len(self._channels) > 10:
            lines.append(f"  ... and {len(self._channels)-10} more channels")
        return "\n".join(lines)




#!/usr/bin/env python3
# =============================================================================
# digital_twin.py — Predictive Digital Twin Divergence Detector
#
# Runs the NetworkX graph model against the Holt-Winters forecaster's predicted
# t+30s topology state and compares it to actual incoming telemetry.  When the
# forecast and reality diverge beyond the EMA baseline, an early-warning signal
# is emitted that feeds into the Priority Scoring Function.
#
# Key design facts:
#  - This is NOT a fourth voter — it feeds PSF as an additional threat-probability
#    input, not as a corroboration vote.  The dual-model safety gate is unchanged.
#  - Dependency: requires trend_forecaster.py to be running (MIN_FIT_SAMPLES=30).
#  - Only valid for GRADUAL onset (Scenario 1).  Sudden failures have no trend to
#    extrapolate — do not claim faster detection for those.
#
# Usage:
#   from digital_twin import DigitalTwin
#   twin = DigitalTwin(graph_engine, trend_forecaster)
#   twin.update(telemetry_dict)          # called each scrape cycle
#   result = twin.evaluate()            # returns DivergenceResult or None
# =============================================================================
import time
import copy
from dataclasses import dataclass, field

from temloom.rca.graph_model import ClonalGraphEngine

# Channels to project through the graph model for twin evaluation.
# Maps (src_node, dst_node) edge → telemetry channel names for delay/capacity.
TWIN_CHANNEL_MAP = {
    ("pe1", "p1"): {
        "delay":    "rtt_ms_pe1_p1",
        "capacity": "capacity_bps_pe1_p1",
    },
    ("p1", "pe2"): {
        "delay":    "rtt_ms_p1_pe2",
        "capacity": "capacity_bps_p1_pe2",
    },
}

# EMA parameters for the divergence baseline
EMA_ALPHA   = 0.1
EMA_K       = 2.5   # std multiplier for anomaly gate
WARMUP      = 50    # twin evaluations before EMA is meaningful

# Score at which the digital twin raises an early-warning flag
DIVERGENCE_WARN_THRESHOLD = 0.3  # normalized 0–1


@dataclass
class DivergenceResult:
    timestamp: float
    forecast_score: float     # graph score on predicted t+30s topology
    actual_score:   float     # graph score on real current topology
    divergence:     float     # |forecast_score - actual_score| / max(actual_score, 1)
    ema_threshold:  float
    is_anomaly:     bool
    channel_details: dict = field(default_factory=dict)

    def __str__(self):
        flag = "⚠ DIVERGENCE" if self.is_anomaly else "✓ nominal"
        return (f"DigitalTwin [{flag}]  "
                f"div={self.divergence:.3f}  "
                f"ema_thr={self.ema_threshold:.3f}  "
                f"actual_score={self.actual_score:.3f}  "
                f"forecast_score={self.forecast_score:.3f}")


class DigitalTwin:
    """
    Maintains a live copy of the NetworkX graph model, keeps it updated from
    real telemetry, and evaluates how much the t+30s forecast diverges from
    actual incoming metrics.
    """

    def __init__(self, graph_engine: ClonalGraphEngine, forecaster: TrendForecaster):
        self._graph = graph_engine
        self._fc    = forecaster
        self._n     = 0
        self._ema_mean: float | None = None
        self._ema_var:  float | None = None
        self._last_result: DivergenceResult | None = None

    # ── Internal EMA ──────────────────────────────────────────────────────────
    def _ema_update(self, value: float):
        self._n += 1
        if self._ema_mean is None:
            self._ema_mean, self._ema_var = value, 0.0
        else:
            delta = value - self._ema_mean
            self._ema_mean += EMA_ALPHA * delta
            self._ema_var  = (1 - EMA_ALPHA) * (self._ema_var + EMA_ALPHA * delta ** 2)

    @property
    def _threshold(self) -> float:
        if self._n < WARMUP or self._ema_var is None:
            return DIVERGENCE_WARN_THRESHOLD
        return self._ema_mean + EMA_K * (self._ema_var ** 0.5)

    # ── Public API ────────────────────────────────────────────────────────────
    def update(self, flat_telemetry: dict[str, float]):
        """Feed one scrape cycle worth of telemetry to the forecaster."""
        self._fc.update_batch(flat_telemetry)

    def evaluate(self) -> DivergenceResult | None:
        """
        Compare actual graph state vs the t+30s forecast.
        Returns None if the forecaster hasn't warmed up yet.
        """
        # Build actual telemetry updates from real data
        actual_updates = self._build_edge_updates(use_forecast=False)
        forecast_updates = self._build_edge_updates(use_forecast=True)

        if not forecast_updates:
            return None  # forecaster hasn't warmed up

        # Score actual topology
        self._graph.apply_telemetry_state(actual_updates)
        actual_score, _, _ = self._graph.evaluate_clone(
            self._graph.base_graph,
            self._graph.get_traffic_matrix()
        )

        # Score predicted t+30s topology (run on a deep copy to avoid mutating state)
        forecast_graph = copy.deepcopy(self._graph.base_graph)
        for (u, v), metrics in forecast_updates.items():
            if forecast_graph.has_edge(u, v):
                for k, val in metrics.items():
                    forecast_graph[u][v][k] = val

        forecast_score, _, channel_delays = self._graph.evaluate_clone(
            forecast_graph, self._graph.get_traffic_matrix()
        )

        # Normalised divergence
        div = abs(forecast_score - actual_score) / max(actual_score, 0.001)
        self._ema_update(div)

        result = DivergenceResult(
            timestamp=time.time(),
            forecast_score=round(forecast_score, 4),
            actual_score=round(actual_score, 4),
            divergence=round(div, 4),
            ema_threshold=round(self._threshold, 4),
            is_anomaly=(div > self._threshold),
            channel_details=channel_delays,
        )
        self._last_result = result
        return result

    def _build_edge_updates(self, use_forecast: bool) -> dict:
        """
        Build a telemetry_updates dict for the graph model.
        use_forecast=True  → use the Holt-Winters t+30s prediction
        use_forecast=False → use the most recent real measurement
        """
        updates = {}
        for edge, channels in TWIN_CHANNEL_MAP.items():
            delay_ch    = channels.get("delay")
            capacity_ch = channels.get("capacity")

            if use_forecast:
                delay    = self._fc.forecast(delay_ch)    if delay_ch    else None
                capacity = self._fc.forecast(capacity_ch) if capacity_ch else None
            else:
                delay    = (self._fc._channels[delay_ch].current_value
                            if delay_ch and delay_ch in self._fc._channels else None)
                capacity = (self._fc._channels[capacity_ch].current_value
                            if capacity_ch and capacity_ch in self._fc._channels else None)

            if delay is None and capacity is None:
                if use_forecast:
                    return {}  # at least one edge has no forecast → not ready
                continue

            entry = {}
            if delay is not None:
                entry["delay"] = max(0.0, delay)
            if capacity is not None:
                entry["capacity"] = max(1.0, capacity)
            if entry:
                updates[edge] = entry
        return updates

    @property
    def last_result(self) -> DivergenceResult | None:
        return self._last_result


# ── Demo ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import numpy as np
    print("[*] DigitalTwin demo — simulating gradual latency creep on pe1→p1\n")

    graph = ClonalGraphEngine()
    fc    = TrendForecaster()
    twin  = DigitalTwin(graph, fc)

    np.random.seed(42)
    for i in range(80):
        rtt      = 5.0 + (i * 0.4 if i > 20 else 0) + np.random.normal(0, 0.5)
        capacity = 10_000_000 - (i * 50_000 if i > 20 else 0)
        telemetry = {
            "rtt_ms_pe1_p1":       max(0, rtt),
            "capacity_bps_pe1_p1": max(1_000_000, capacity),
            "rtt_ms_p1_pe2":       5.0 + np.random.normal(0, 0.2),
            "capacity_bps_p1_pe2": 10_000_000,
        }
        twin.update(telemetry)
        if i >= 30:
            result = twin.evaluate()
            if result and (result.is_anomaly or i % 10 == 0):
                print(f"  [{i:3d}] {result}")

    print("\n[+] Digital Twin demo complete.")
