import os
#!/usr/bin/env python3
"""Reproducible MPLS/SD-WAN Multi-Layer Telemetry & Fault Scenario Generator.

Generates timestamped network telemetry across Scenarios A-L and the S1 Parametric
Congestion Family independently of any predictive model.
"""

import math
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import yaml


class NetworkTelemetrySimulator:
    """Simulates multi-layer MPLS underlay + SD-WAN overlay telemetry with independent ground truth."""

    def __init__(self, scenarios_path: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "configs", "scenarios.yaml")):
        with open(scenarios_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        self.dt_sec = float(self.config["dt_seconds"])
        self.dt_min = self.dt_sec / 60.0
        self.duration_min = float(self.config["duration_minutes"])
        self.n_steps = int(round(self.duration_min / self.dt_min))
        self.capacity_mbps = float(self.config["bottleneck_capacity_mbps"])
        self.sla = self.config["sla_thresholds"]

    def generate_scenario(
        self,
        scenario_key: str,
        seed: int,
        override_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generates a single complete scenario run with independent ground-truth SLA labels."""
        rng = np.random.default_rng(seed)
        sc = self.config["scenarios"].get(scenario_key) or next(iter(self.config["scenarios"].values()))
        p = dict(sc.get("params", {}))
        if override_params:
            p.update(override_params)

        code = sc["code"]
        t_min = np.arange(self.n_steps) * self.dt_min
        event_start = float(p.get("event_start_min", sc["event_start_min"]))
        base_util = float(p.get("base_util_mbps", 50.0))
        capacity = float(p.get("bottleneck_capacity_mbps", self.capacity_mbps))
        ef_share = float(p.get("ef_share", 0.20))
        backup_base = float(p.get("backup_base_util_mbps", 18.0))
        noise_std = float(p.get("noise_std_mbps", 1.35))

        # 1. Generate underlying true traffic demand on primary MPLS link (p-core1:eth1)
        # Include realistic AR(1) autocorrelated background fluctuation + diurnal wave
        ar_noise = np.zeros(self.n_steps)
        eps = rng.normal(0.0, noise_std, size=self.n_steps)
        for i in range(1, self.n_steps):
            ar_noise[i] = 0.45 * ar_noise[i - 1] + eps[i]

        true_util = np.full(self.n_steps, base_util, dtype=float) + ar_noise
        routing_event = np.zeros(self.n_steps, dtype=int)
        secondary_br3_loss = np.zeros(self.n_steps, dtype=float)

        for i, t in enumerate(t_min):
            if t >= event_start:
                dt_e = t - event_start
                if code == "A":
                    ramp = float(p.get("ramp_rate_mbps_per_min", 2.3))
                    true_util[i] += ramp * dt_e
                elif code == "B":
                    b_dur = float(p.get("burst_duration_min", 0.50))
                    if dt_e <= b_dur:
                        true_util[i] += float(p.get("burst_delta_mbps", 39.0))
                elif code == "C":
                    dur = float(p.get("duration_min", 3.5))
                    if dt_e <= dur:
                        target = float(p.get("plateau_util_mbps", 87.5))
                        true_util[i] = target + ar_noise[i] * 0.7
                elif code == "D":
                    if abs(dt_e) < 1e-6 or (dt_e >= 0 and t_min[i - 1] < event_start):
                        routing_event[i] = 1
                    true_util[i] += float(p.get("step_shift_mbps", 36.0)) + float(
                        p.get("post_shift_ramp_mbps_per_min", 1.5)
                    ) * dt_e
                elif code == "E":
                    true_util[i] += float(p.get("ramp_rate_mbps_per_min", 1.4)) * dt_e
                elif code == "F":
                    # Utilization remains near baseline; latency degrades independently
                    pass
                elif code == "G":
                    true_util[i] += float(p.get("ramp_rate_mbps_per_min", 2.2)) * dt_e
                    sec_start = float(p.get("secondary_fault_start_min", 11.5))
                    if t >= sec_start:
                        secondary_br3_loss[i] = min(4.5, 0.4 + 0.6 * (t - sec_start))
                elif code == "H":
                    true_util[i] += float(p.get("ramp_rate_mbps_per_min", 2.1)) * dt_e
                elif code == "I":
                    if abs(dt_e) < 1e-6 or (dt_e >= 0 and t_min[i - 1] < event_start):
                        routing_event[i] = 1
                    true_util[i] = float(p.get("new_regime_util_mbps", 68.0)) + ar_noise[i]
                elif code == "J":
                    # Smooth transition to high benign plateau (88 Mbps) with low EF share
                    ramp_in = min(1.0, dt_e / 4.0)
                    true_util[i] = (
                        base_util
                        + ramp_in * (float(p.get("high_plateau_mbps", 88.0)) - base_util)
                        + ar_noise[i] * 0.6
                    )
                elif code == "K":
                    ramp = float(p.get("ramp_rate_mbps_per_min", 2.0))
                    peak = float(p.get("peak_util_mbps", 79.0))
                    ramp_dur = (peak - base_util) / ramp
                    if dt_e <= ramp_dur:
                        true_util[i] += ramp * dt_e
                    elif dt_e <= ramp_dur + 2.0:
                        true_util[i] = peak + ar_noise[i] * 0.5
                    else:
                        rec_dt = dt_e - (ramp_dur + 2.0)
                        true_util[i] = max(base_util, peak - 3.5 * rec_dt) + ar_noise[i]
                elif code == "L":
                    if abs(dt_e) < 1e-6 or (dt_e >= 0 and t_min[i - 1] < event_start):
                        routing_event[i] = 1
                    true_util[i] += float(p.get("step_shift_mbps", 18.0)) + float(
                        p.get("ramp_rate_mbps_per_min", 1.6)
                    ) * dt_e

        true_util = np.clip(true_util, 5.0, capacity * 1.04)

        # 2. Compute physical queueing dynamics: queue drops (pps), packet loss (%), and latency (ms)
        # In QoS-enabled MPLS, strict-priority EF traffic is protected when EF share is small and buffer is healthy,
        # but suffers nonlinear queueing delay and tail drops as total utilization approaches capacity (or early policer limit in E).
        queue_drops_pps = np.zeros(self.n_steps, dtype=float)
        packet_loss_pct = np.zeros(self.n_steps, dtype=float)
        latency_ms = np.zeros(self.n_steps, dtype=float)

        early_drop_thresh = float(p.get("early_drop_threshold_mbps", 90.0 if code != "E" else 72.0))
        for i, t in enumerate(t_min):
            u_ratio = true_util[i] / capacity
            # Effective QoS congestion pressure depends on both total load and EF/AF priority share
            qos_pressure = u_ratio * (0.82 + 0.90 * ef_share)

            if code == "E" and true_util[i] > early_drop_thresh:
                excess = true_util[i] - early_drop_thresh
                queue_drops_pps[i] = max(0.0, 2.8 * excess + 0.18 * (excess ** 2) + rng.normal(0, 1.2))
                packet_loss_pct[i] = min(8.0, queue_drops_pps[i] / 22.0)
            elif code == "J":
                # Benign high utilization: large buffer + 8% EF share -> near-zero drops and stable latency
                queue_drops_pps[i] = max(0.0, rng.normal(0.2, 0.3))
                packet_loss_pct[i] = 0.0
            else:
                if true_util[i] > early_drop_thresh and qos_pressure > 0.84:
                    excess = true_util[i] - early_drop_thresh
                    queue_drops_pps[i] = max(0.0, 3.2 * excess + 0.45 * (excess ** 2) + rng.normal(0, 1.0))
                    packet_loss_pct[i] = min(10.0, queue_drops_pps[i] / 24.0)
                else:
                    queue_drops_pps[i] = max(0.0, rng.normal(0.1, 0.25))
                    packet_loss_pct[i] = max(0.0, rng.normal(0.01, 0.02))

            # M/M/1/K nonlinear queueing delay + propagation baseline (8.0 ms)
            base_lat = 8.0 + rng.normal(0.0, 0.35)
            if code == "F" and t >= event_start:
                drift = float(p.get("latency_drift_ms_per_min", 1.65)) * (t - event_start)
                latency_ms[i] = base_lat + drift + rng.normal(0.0, 0.6)
            elif code == "J":
                latency_ms[i] = base_lat + 2.8 * (u_ratio ** 2)
            else:
                effective_rho = min(0.975, u_ratio * (0.85 + 0.75 * ef_share))
                queue_delay = 1.65 * (effective_rho ** 3) / (1.0 - effective_rho)
                latency_ms[i] = base_lat + queue_delay + 0.08 * queue_drops_pps[i]

        # 3. Compute True Independent Ground-Truth SLA Violation Timestamp
        # SLA is violated at step i if (true_util >= sla_util OR latency >= sla_lat OR loss >= sla_loss OR drops >= sla_drops)
        # sustained for >= min_sustained_steps (3 consecutive steps = 45 seconds)
        breach_step_mask = (
            (true_util >= float(p.get("sla_util_mbps", self.sla["util_mbps"])))
            | (latency_ms >= float(self.sla["latency_ms"]))
            | (packet_loss_pct >= float(self.sla["loss_pct"]))
            | (queue_drops_pps >= float(self.sla["queue_drops_pps"]))
        )

        min_sustained = int(self.sla["min_sustained_steps"])
        sla_violation_time_min: Optional[float] = None
        sla_violation_step: Optional[int] = None
        consec = 0
        for i in range(self.n_steps):
            if breach_step_mask[i]:
                consec += 1
                if consec >= min_sustained and sla_violation_step is None:
                    # Violation time is the start of the sustained breach window
                    sla_violation_step = i - min_sustained + 1
                    sla_violation_time_min = float(t_min[sla_violation_step])
            else:
                consec = 0

        # 4. Apply Telemetry Observation Imperfections (Missing Data & Single-Poll Counter Outliers)
        obs_util = true_util.copy()
        obs_latency = latency_ms.copy()
        obs_loss = packet_loss_pct.copy()
        obs_drops = queue_drops_pps.copy()

        missing_prob = float(p.get("missing_prob", 0.0))
        outlier_prob = float(p.get("outlier_prob", 0.0))
        outlier_scale = float(p.get("outlier_scale_mbps", 25.0))

        is_missing = np.zeros(self.n_steps, dtype=bool)
        if missing_prob > 0.0:
            is_missing = rng.random(self.n_steps) < missing_prob
            is_missing[0] = False
            obs_util[is_missing] = np.nan
            obs_latency[is_missing] = np.nan
            obs_loss[is_missing] = np.nan
            obs_drops[is_missing] = np.nan

        if outlier_prob > 0.0:
            outlier_mask = (rng.random(self.n_steps) < outlier_prob) & (~is_missing)
            signs = rng.choice([-1.0, 1.0], size=self.n_steps)
            obs_util[outlier_mask] = np.clip(
                obs_util[outlier_mask] + signs[outlier_mask] * outlier_scale,
                0.0,
                capacity * 1.15,
            )
            obs_latency[outlier_mask] += np.abs(signs[outlier_mask]) * 14.0

        # Multi-tunnel overlay observations (tun-br1-hub1 and tun-br2-hub1 share p-core1:eth1; tun-br3-hub1 uses p-backup1)
        tun1_jitter = np.where(is_missing, np.nan, np.maximum(0.5, (latency_ms - 8.0) * 0.55 + rng.normal(0.8, 0.25, self.n_steps)))
        tun2_jitter = np.where(is_missing, np.nan, np.maximum(0.5, (latency_ms - 8.0) * 0.52 + rng.normal(0.8, 0.25, self.n_steps)))
        backup_util = np.clip(backup_base + rng.normal(0.0, 0.9, self.n_steps), 5.0, 98.0)

        df = pd.DataFrame({
            "step": np.arange(self.n_steps),
            "time_min": t_min,
            "obs_util_mbps": obs_util,
            "true_util_mbps": true_util,
            "obs_latency_ms": obs_latency,
            "true_latency_ms": latency_ms,
            "obs_loss_pct": obs_loss,
            "obs_queue_drops_pps": obs_drops,
            "routing_event": routing_event,
            "ef_share": np.full(self.n_steps, ef_share),
            "capacity_mbps": np.full(self.n_steps, capacity),
            "backup_util_mbps": backup_util,
            "tun1_jitter_ms": tun1_jitter,
            "tun2_jitter_ms": tun2_jitter,
            "br3_loss_pct": secondary_br3_loss,
            "is_missing": is_missing.astype(int),
            "breach_active": breach_step_mask.astype(int),
        })

        return {
            "scenario_key": scenario_key,
            "code": code,
            "name": sc["name"],
            "seed": seed,
            "event_start_min": event_start,
            "expects_sla_violation": bool(sc["expects_sla_violation"]),
            "sla_violation_occurred": sla_violation_time_min is not None,
            "sla_violation_time_min": sla_violation_time_min,
            "sla_violation_step": sla_violation_step,
            "expected_response": sc["expected_response"],
            "df": df,
        }




def generate_routing_scenario(scen_id: str, seed: int, n_steps: int = 160, dt_min: float = 0.25) -> Dict[str, Any]:
    """Generates 40-minute (160-step at 15s) BGP/OSPF control-plane & asymmetry telemetry."""
    rng = np.random.default_rng(seed * 100 + sum(ord(c) for c in scen_id))
    t_min = np.arange(n_steps) * dt_min

    # Normal baseline control-plane chatter (calm network prior to event_start_min = 10.0m / step 40)
    bgp_updates = rng.poisson(0.25, size=n_steps).astype(float)
    bgp_withdraws = np.zeros(n_steps, dtype=float)
    # Occasional isolated single-route withdraw in normal operation
    for k in rng.choice(range(5, 38), size=2, replace=False):
        bgp_withdraws[k] = 1.0
    flap_penalty = np.zeros(n_steps, dtype=float)
    ospf_spf_runs = np.zeros(n_steps, dtype=float)
    bfd_echo_var_ms2 = np.clip(rng.normal(0.30, 0.06, size=n_steps), 0.05, 5.0)
    asymmetry_ratio = np.clip(rng.normal(0.04, 0.012, size=n_steps), 0.0, 1.0)

    expects_outage = False
    event_start_min = 10.0

    if scen_id == "R1_BGP_Exponential_Flap_Cascade":
        expects_outage = True
        for i in range(40, n_steps):
            dt_ev = (i - 40) * dt_min
            rate = 0.55 * np.exp(0.18 * dt_ev)
            bgp_withdraws[i] += rng.poisson(min(rate, 20.0))
            bgp_updates[i] += rng.poisson(min(rate * 2.2, 45.0))
            bfd_echo_var_ms2[i] += 0.16 * dt_ev

    elif scen_id == "R2_RFC2439_Flap_Damping_Suppression":
        expects_outage = True
        # Periodic sub-threshold route flaps every 30s that accumulate RFC 2439 penalty (>2000 suppress threshold)
        for i in range(40, n_steps):
            if (i - 40) % 2 == 0:
                bgp_withdraws[i] += rng.integers(1, 3)
                bgp_updates[i] += rng.integers(3, 6)
            bfd_echo_var_ms2[i] += 0.07 * (i - 40) * dt_min

    elif scen_id == "R3_OSPF_LSA_Adjacency_Storm":
        expects_outage = True
        for i in range(40, n_steps):
            dt_ev = (i - 40) * dt_min
            ospf_spf_runs[i] = min(6.0, 0.32 * dt_ev + rng.poisson(0.25))
            bfd_echo_var_ms2[i] += 0.24 * dt_ev
            bgp_updates[i] += rng.poisson(0.4 * dt_ev)

    elif scen_id == "R4_Asymmetric_Routing_Blackhole_Drift":
        expects_outage = True
        for i in range(40, n_steps):
            dt_ev = (i - 40) * dt_min
            asymmetry_ratio[i] = np.clip(0.04 + 0.038 * dt_ev + rng.normal(0, 0.012), 0.0, 0.95)
            if i in (42, 52, 62):
                bgp_updates[i] += 3.0

    elif scen_id == "R5_Benign_Planned_Single_Peer_Reset":
        expects_outage = False
        # One-time planned maintenance session reset at t=12m (step 48) that immediately stabilizes
        bgp_withdraws[48] = 3.0
        bgp_updates[48:50] += np.array([12.0, 6.0])

    elif scen_id == "R6_Benign_BGP_Table_Refresh_Burst":
        expects_outage = False
        # Soft-reconfiguration / route-refresh (high BGP updates, zero withdraws, calm BFD)
        bgp_updates[52:62] += rng.integers(15, 25, size=10)

    # Compute RFC 2439 flap penalty trajectory (half-life = 15 min, suppress threshold = 2000)
    decay = 0.5 ** (dt_min / 15.0)
    for i in range(1, n_steps):
        flap_penalty[i] = (
            flap_penalty[i - 1] * decay
            + 240.0 * bgp_withdraws[i]
            + 30.0 * max(0.0, bgp_updates[i] - 6.0) * (1.0 if bgp_withdraws[i] > 0 else 0.0)
        )

    # Ground-truth routing outage / SLA breach definition:
    # Sustained for >= 2 steps: flap_penalty >= 2000 OR ospf_spf_runs >= 3.5/step OR asymmetry_ratio >= 0.45
    breach_mask = (flap_penalty >= 2000.0) | (ospf_spf_runs >= 3.5) | (asymmetry_ratio >= 0.45)
    sla_step, sla_time = None, None
    c = 0
    for i in range(n_steps):
        if breach_mask[i]:
            c += 1
            if c >= 2 and sla_step is None:
                sla_step = i - 1
                sla_time = float(t_min[sla_step])
        else:
            c = 0

    df = pd.DataFrame({
        "step": np.arange(n_steps),
        "time_min": t_min,
        "bgp_updates": bgp_updates,
        "bgp_withdraws": bgp_withdraws,
        "flap_penalty": flap_penalty,
        "ospf_spf_runs": ospf_spf_runs,
        "bfd_echo_var_ms2": bfd_echo_var_ms2,
        "asymmetry_ratio": asymmetry_ratio,
        "breach_active": breach_mask.astype(int),
    })
    return {
        "scenario_id": scen_id,
        "seed": seed,
        "event_start_min": event_start_min,
        "has_sla_violation": sla_time is not None,
        "sla_time_min": sla_time,
        "df": df,
    }




def generate_tunnel_scenario(scen_id: str, seed: int, n_steps: int = 160, dt_min: float = 0.25) -> Dict[str, Any]:
    """Generates 40-minute IPSec ESP/IKEv2 overlay tunnel telemetry."""
    rng = np.random.default_rng(seed * 200 + sum(ord(c) for c in scen_id))
    t_min = np.arange(n_steps) * dt_min

    tun_jitter_ms = np.clip(rng.normal(1.8, 0.35, size=n_steps), 0.3, 50.0)
    esp_seq_loss_pct = np.clip(rng.exponential(0.04, size=n_steps), 0.0, 20.0)
    replay_drops_pps = rng.poisson(0.2, size=n_steps).astype(float)
    ike_rekey_lat_ms = np.clip(rng.normal(45.0, 5.0, size=n_steps), 20.0, 5000.0)
    ike_dh_retries = np.zeros(n_steps, dtype=float)
    sa_rem_life_min = np.linspace(35.0, 5.0, n_steps)

    if scen_id == "T1_IKEv2_Rekey_Retry_Exhaustion":
        sa_rem_life_min = np.maximum(0.0, np.linspace(22.0, -3.0, n_steps))
        for i in range(40, n_steps):
            dt_ev = (i - 40) * dt_min
            ike_rekey_lat_ms[i] += 95.0 * dt_ev
            if i >= 44 and (i % 2 == 0):
                ike_dh_retries[i] = min(6.0, 1.0 + 0.35 * dt_ev)
            if sa_rem_life_min[i] <= 1.5:
                esp_seq_loss_pct[i] = 12.0

    elif scen_id == "T2_ESP_AntiReplay_Window_Overflow":
        for i in range(40, n_steps):
            dt_ev = (i - 40) * dt_min
            replay_drops_pps[i] += 2.6 * dt_ev + rng.poisson(1.2)
            tun_jitter_ms[i] += 0.95 * dt_ev

    elif scen_id == "T3_Underlay_Congestion_VoIP_MOS_Collapse":
        for i in range(40, n_steps):
            dt_ev = (i - 40) * dt_min
            tun_jitter_ms[i] += 1.35 * dt_ev
            esp_seq_loss_pct[i] += 0.18 * dt_ev

    elif scen_id == "T4_PMTUD_Fragmentation_Blackhole":
        for i in range(40, n_steps):
            dt_ev = (i - 40) * dt_min
            esp_seq_loss_pct[i] += 0.28 * dt_ev
            ike_rekey_lat_ms[i] += 40.0 * dt_ev

    elif scen_id == "T5_Benign_Normal_Periodic_ChildSA_Rekey":
        ike_rekey_lat_ms[60] = 145.0
        sa_rem_life_min[60:] = np.linspace(35.0, 10.0, n_steps - 60)

    elif scen_id == "T6_Benign_Transient_2Tick_BFD_Glitch":
        tun_jitter_ms[70:72] = 13.8
        esp_seq_loss_pct[70] = 1.2

    breach_mask = (
        (tun_jitter_ms >= 15.0)
        | (esp_seq_loss_pct >= 2.0)
        | (replay_drops_pps >= 25.0)
        | ((ike_dh_retries >= 3.5) & (sa_rem_life_min <= 2.5))
    )
    sla_step, sla_time = None, None
    c = 0
    for i in range(n_steps):
        if breach_mask[i]:
            c += 1
            if c >= 2 and sla_step is None:
                sla_step = i - 1
                sla_time = float(t_min[sla_step])
        else:
            c = 0

    df = pd.DataFrame({
        "step": np.arange(n_steps),
        "time_min": t_min,
        "tun_jitter_ms": tun_jitter_ms,
        "esp_seq_loss_pct": esp_seq_loss_pct,
        "replay_drops_pps": replay_drops_pps,
        "ike_rekey_lat_ms": ike_rekey_lat_ms,
        "ike_dh_retries": ike_dh_retries,
        "sa_rem_life_min": sa_rem_life_min,
        "breach_active": breach_mask.astype(int),
    })
    return {
        "scenario_id": scen_id,
        "seed": seed,
        "event_start_min": 10.0,
        "has_sla_violation": sla_time is not None,
        "sla_time_min": sla_time,
        "df": df,
    }




def generate_policy_drift_scenario(seed: int = 301, n_steps: int = 160, dt_min: float = 0.25) -> Dict[str, Any]:
    t_min = np.arange(n_steps) * dt_min
    golden_hash = "8f9d2a1c4b7e6051e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934c"
    drift_hash = "3c11e90b77a2d409e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934c"
    active_hash = [golden_hash if i < 40 else drift_hash for i in range(n_steps)]
    ef_wrong_tun_mbps = np.array([0.0 if i < 40 else 14.5 for i in range(n_steps)])
    voip_jitter_ms = np.array([1.9 if i < 40 else min(22.0, 1.9 + 2.6 * (i - 40) * dt_min) for i in range(n_steps)])
    breach_mask = voip_jitter_ms >= 15.0
    df = pd.DataFrame({
        "step": np.arange(n_steps),
        "time_min": t_min,
        "golden_config_sha256": golden_hash,
        "active_config_sha256": active_hash,
        "ef_wrong_tun_mbps": ef_wrong_tun_mbps,
        "voip_jitter_ms": voip_jitter_ms,
        "breach_active": breach_mask.astype(int),
    })
    return {
        "scenario_id": "Scenario_D_SDWAN_Controller_Policy_Drift",
        "seed": seed,
        "event_start_min": 10.0,
        "has_sla_violation": True,
        "sla_time_min": 15.25,
        "df": df,
    }
