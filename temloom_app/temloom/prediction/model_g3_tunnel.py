#!/usr/bin/env python3
"""
temloom/prediction/model_g3_tunnel.py — TEMLOOM Domain C Engine (Model G3):
Multivariate IPSec Tunnel Survival, IKEv2 DH Rekey & Anti-Replay Exhaustion Engine.
"""

import math
import time
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd

class BaselineT1_StaticDPDThreshold:
    name = "Baseline T-A: Static Jitter/Loss/DPD Threshold"
    def predict_run(self, df: pd.DataFrame, dt_min: float = 0.25) -> Dict[str, Any]:
        t0 = time.perf_counter()
        n = len(df)
        w = np.zeros(n, dtype=int)
        ttv = np.full(n, np.nan)
        for i in range(n):
            if df["tun_jitter_ms"].iat[i] >= 13.0 or df["esp_seq_loss_pct"].iat[i] >= 1.6 or df["replay_drops_pps"].iat[i] >= 20.0:
                w[i] = 1
                ttv[i] = 1.0
        return {"warnings": w, "pred_ttv_min": ttv, "latency_ms": (time.perf_counter() - t0) * 1000.0 / n}


class BaselineT2_SingleMetricJitterEWMA:
    name = "Baseline T-B: Single-Metric Jitter EWMA"
    def predict_run(self, df: pd.DataFrame, dt_min: float = 0.25) -> Dict[str, Any]:
        t0 = time.perf_counter()
        n = len(df)
        w = np.zeros(n, dtype=int)
        ttv = np.full(n, np.nan)
        j_ewma = 1.8
        for i in range(n):
            j_ewma = 0.35 * df["tun_jitter_ms"].iat[i] + 0.65 * j_ewma
            j_slope = (j_ewma - df["tun_jitter_ms"].iat[max(0, i - 8)]) / 2.0 if i >= 8 else 0.0
            if j_ewma + 8.0 * j_slope >= 14.5:
                w[i] = 1
                ttv[i] = max(0.5, (15.0 - j_ewma) / max(0.2, j_slope))
        return {"warnings": w, "pred_ttv_min": ttv, "latency_ms": (time.perf_counter() - t0) * 1000.0 / n}


class ModelG3_TunnelRekeyHazardEngine:
    """
    TEMLOOM Domain C Engine (Model G3):
    Multivariate Tunnel Survival & IKEv2 Rekey Hazard Engine:
    - 3-step median glitch clamp on BFD jitter/loss to reject T6 2-tick transient glitches
    - Channel 1: Jitter + ESP Sequence Loss Trajectory
    - Channel 2: Anti-Replay Window Drop Velocity
    - Channel 3: IKEv2 Rekey Handshake Latency + DH Retry Hazard relative to Remaining SA Lifetime
    """
    name = "TEMLOOM Model G3: Multivariate Tunnel & IKEv2 Rekey Hazard Engine"
    def predict_run(self, df: pd.DataFrame, dt_min: float = 0.25) -> Dict[str, Any]:
        t0 = time.perf_counter()
        n = len(df)
        w = np.zeros(n, dtype=int)
        ttv = np.full(n, np.nan)

        jit = df["tun_jitter_ms"].values
        loss = df["esp_seq_loss_pct"].values
        rep = df["replay_drops_pps"].values
        rekey_lat = df["ike_rekey_lat_ms"].values
        retries = df["ike_dh_retries"].values
        sa_life = df["sa_rem_life_min"].values

        j_ewma, l_ewma, r_ewma, k_ewma = 1.8, 0.04, 0.2, 45.0
        consec = 0

        for i in range(n):
            # 3-step causal rolling median filter suppresses 1-2 tick transient BFD echo glitches (T6)
            j_med = float(np.median(jit[max(0, i - 2):i + 1]))
            l_med = float(np.median(loss[max(0, i - 2):i + 1]))

            j_ewma = 0.28 * j_med + 0.72 * j_ewma
            l_ewma = 0.28 * l_med + 0.72 * l_ewma
            r_ewma = 0.28 * rep[i] + 0.72 * r_ewma
            k_ewma = 0.28 * rekey_lat[i] + 0.72 * k_ewma

            if i >= 8:
                j_slope = (j_ewma - jit[i - 8]) / (8.0 * dt_min)
                l_slope = (l_ewma - loss[i - 8]) / (8.0 * dt_min)
                r_slope = (r_ewma - rep[i - 8]) / (8.0 * dt_min)
                k_slope = (k_ewma - rekey_lat[i - 8]) / (8.0 * dt_min)
            else:
                j_slope = l_slope = r_slope = k_slope = 0.0

            recent_retries = float(np.sum(retries[max(0, i - 4):i + 1]))

            haz_jit_loss = (
                (j_slope >= 0.75 and j_ewma + 10.0 * j_slope >= 14.8 and j_ewma >= 4.2)
                or (l_slope >= 0.12 and l_ewma + 10.0 * l_slope >= 1.9 and l_ewma >= 0.42)
            )
            haz_replay = (r_slope >= 1.4 and r_ewma >= 5.0) or (r_ewma >= 18.0)
            haz_rekey = (recent_retries >= 2.0 and k_slope >= 35.0 and sa_life[i] <= 12.0)

            if i >= 8 and (haz_jit_loss or haz_replay or haz_rekey):
                consec += 1
                if consec >= 3:
                    w[i] = 1
                    cands = []
                    if haz_jit_loss and j_slope > 0.35 and j_ewma < 15.0:
                        cands.append((15.0 - j_ewma) / (j_slope * 1.35))
                    if haz_jit_loss and l_slope > 0.08 and l_ewma < 2.0:
                        cands.append((2.0 - l_ewma) / (l_slope * 1.35))
                    if haz_replay and r_slope > 0.3:
                        cands.append(max(0.5, (25.0 - r_ewma) / (r_slope * 1.35)))
                    if haz_rekey:
                        cands.append(max(0.5, (sa_life[i] - 2.5) * 0.65))
                    ttv[i] = float(min(cands)) if cands else 2.5
            else:
                consec = max(0, consec - 1)

        return {"warnings": w, "pred_ttv_min": ttv, "latency_ms": (time.perf_counter() - t0) * 1000.0 / n}


def score_domain_runs(model, runs: List[Dict[str, Any]], dt_min: float = 0.25) -> Dict[str, Any]:
    det_flags = []
    lead_times = []
    ttv_maes = []
    false_alarms = 0
    true_warnings = 0
    total_hours = 0.0
    latencies = []

    for r in runs:
        df = r["df"]
        out = model.predict_run(df, dt_min=dt_min)
        w = out["warnings"]
        pttv = out["pred_ttv_min"]
        latencies.append(out["latency_ms"])
        t_arr = df["time_min"].values
        n = len(df)
        total_hours += (n * dt_min) / 60.0

        episodes = []
        in_ep = False
        ep_start_t = 0.0
        ep_idx = 0
        last_w = -10
        for i in range(n):
            if w[i] == 1:
                if not in_ep:
                    in_ep = True
                    ep_start_t = float(t_arr[i])
                    ep_idx = i
                last_w = i
            else:
                if in_ep and (i - last_w) > 2:
                    episodes.append((ep_start_t, ep_idx))
                    in_ep = False
        if in_ep:
            episodes.append((ep_start_t, ep_idx))

        ev_start = r["event_start_min"]
        if r["has_sla_violation"]:
            sla_t = r["sla_time_min"]
            valid_eps = [(t0, idx) for (t0, idx) in episodes if ev_start <= t0 <= sla_t]
            for (t0, _) in episodes:
                if t0 < ev_start:
                    false_alarms += 1
            if valid_eps:
                det_flags.append(1)
                true_warnings += 1
                first_t, first_idx = valid_eps[0]
                actual_lt = sla_t - first_t
                lead_times.append(actual_lt)
                if not np.isnan(pttv[first_idx]):
                    ttv_maes.append(abs(float(pttv[first_idx]) - actual_lt))
            else:
                det_flags.append(0)
        else:
            false_alarms += len(episodes)

    recall = float(np.mean(det_flags)) if det_flags else 0.0
    fa_hr = false_alarms / max(1e-9, total_hours)
    prec = true_warnings / max(1, true_warnings + false_alarms)
    return {
        "model": model.name,
        "recall": round(recall, 4),
        "false_alarms_total": int(false_alarms),
        "false_alarms_per_hour": round(fa_hr, 4),
        "precision": round(prec, 4),
        "median_lead_time_min": round(float(np.median(lead_times)), 3) if lead_times else 0.0,
        "ttv_mae_min": round(float(np.mean(ttv_maes)), 3) if ttv_maes else 0.0,
        "latency_ms_per_step": round(float(np.mean(latencies)), 4),
    }


