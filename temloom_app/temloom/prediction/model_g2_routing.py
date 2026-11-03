#!/usr/bin/env python3
"""
temloom/prediction/model_g2_routing.py — TEMLOOM Domain B Engine (Model G2):
Self-Exciting Hawkes Process & Page-Hinkley CUSUM Routing Instability Engine.
"""

import math
import time
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd

class BaselineR1_StaticFlapThreshold:
    name = "Baseline R-A: Static Flap/SPF Threshold"
    def predict_run(self, df: pd.DataFrame, dt_min: float = 0.25) -> Dict[str, Any]:
        t0 = time.perf_counter()
        n = len(df)
        w = np.zeros(n, dtype=int)
        ttv = np.full(n, np.nan)
        for i in range(1, n):
            cond = (
                df["flap_penalty"].iat[i] >= 1750.0
                or df["bgp_withdraws"].iat[i] >= 6.0
                or df["ospf_spf_runs"].iat[i] >= 3.0
                or df["asymmetry_ratio"].iat[i] >= 0.40
            )
            if cond:
                w[i] = 1
                ttv[i] = 1.0
        return {"warnings": w, "pred_ttv_min": ttv, "latency_ms": (time.perf_counter() - t0) * 1000.0 / n}


class BaselineR2_EWMAChurnRate:
    name = "Baseline R-B: Rolling EWMA Churn Rate"
    def predict_run(self, df: pd.DataFrame, dt_min: float = 0.25) -> Dict[str, Any]:
        t0 = time.perf_counter()
        n = len(df)
        w = np.zeros(n, dtype=int)
        ttv = np.full(n, np.nan)
        ewma_upd = 0.0
        ewma_wdr = 0.0
        for i in range(n):
            ewma_upd = 0.3 * df["bgp_updates"].iat[i] + 0.7 * ewma_upd
            ewma_wdr = 0.3 * df["bgp_withdraws"].iat[i] + 0.7 * ewma_wdr
            if ewma_upd >= 7.0 or ewma_wdr >= 1.8 or df["ospf_spf_runs"].iat[i] >= 2.2:
                w[i] = 1
                ttv[i] = 3.0
        return {"warnings": w, "pred_ttv_min": ttv, "latency_ms": (time.perf_counter() - t0) * 1000.0 / n}


class ModelG2_HawkesCUSUMRoutingEngine:
    """
    TEMLOOM Domain B Engine (Model G2):
    1. Self-Exciting Hawkes Intensity Estimator over BGP Withdraws & Corroborated Flap Penalty:
       - Requires recurrence across >= 3 distinct ticks in an 8-step window (rejects R5 single-peer planned reset)
       - Ignores pure BGP UPDATE refreshes with zero withdraws (rejects R6 table refresh burst)
    2. OSPF SPF Velocity + BFD Echo Variance Corroboration Channel.
    3. Page-Hinkley CUSUM + Slope Extrapolation on Forward/Return Traffic Asymmetry Ratio.
    """
    name = "TEMLOOM Model G2: Hawkes Self-Exciting Intensity + CUSUM Asymmetry Engine"
    def predict_run(self, df: pd.DataFrame, dt_min: float = 0.25) -> Dict[str, Any]:
        t0 = time.perf_counter()
        n = len(df)
        w = np.zeros(n, dtype=int)
        ttv = np.full(n, np.nan)

        wdr = df["bgp_withdraws"].values
        pen = df["flap_penalty"].values
        spf = df["ospf_spf_runs"].values
        bfd = df["bfd_echo_var_ms2"].values
        asym = df["asymmetry_ratio"].values

        hawkes_intensity = 0.0
        spf_ewma = 0.0
        asym_ewma = 0.04
        consec = 0

        for i in range(n):
            hawkes_intensity = hawkes_intensity * math.exp(-0.55 * dt_min) + 0.90 * wdr[i]
            spf_ewma = 0.28 * spf[i] + 0.72 * spf_ewma
            asym_ewma = 0.28 * asym[i] + 0.72 * asym_ewma

            pen_slope_short = (pen[i] - pen[i - 4]) / (4.0 * dt_min) if i >= 4 else 0.0
            pen_slope_med = (pen[i] - pen[i - 8]) / (8.0 * dt_min) if i >= 8 else 0.0
            spf_slope = (spf_ewma - float(np.mean(spf[max(0, i - 8):max(1, i - 4)]))) / (6.0 * dt_min) if i >= 8 else 0.0
            asym_slope = (asym_ewma - float(np.mean(asym[max(0, i - 8):max(1, i - 4)]))) / (6.0 * dt_min) if i >= 8 else 0.0
            bfd_slope = (bfd[i] - bfd[i - 8]) / (8.0 * dt_min) if i >= 8 else 0.0

            # Recurrence count: how many distinct steps in the last 8 steps had BGP withdraws > 0?
            # A planned single-step peer reset (R5) has active_wdr_ticks == 1 and pen_slope_short <= 0 after the step!
            active_wdr_ticks = int(np.sum(wdr[max(0, i - 8):i + 1] >= 1.0))

            haz_bgp = (
                active_wdr_ticks >= 2
                and pen_slope_short > 25.0
                and (
                    (pen_slope_med >= 95.0 and pen[i] >= 550.0)
                    or (hawkes_intensity >= 2.2 and bfd[i] >= 0.55)
                )
            )
            haz_ospf = (spf_ewma >= 0.70 and bfd_slope >= 0.08 and bfd[i] >= 0.65) or (spf_ewma >= 1.35)
            haz_asym = (asym_slope >= 0.020 and asym_ewma >= 0.12) or (asym_ewma >= 0.30)

            if i >= 8 and (haz_bgp or haz_ospf or haz_asym):
                consec += 1
                if consec >= 2:
                    w[i] = 1
                    cands = []
                    if haz_bgp and pen_slope_med > 20.0:
                        cands.append(max(0.5, (2000.0 - pen[i]) / pen_slope_med))
                    if haz_ospf:
                        eff_spf_s = max(0.22, spf_slope)
                        cands.append(max(0.5, (3.5 - spf_ewma) / eff_spf_s))
                    if haz_asym and asym_slope > 0.005:
                        cands.append(max(0.5, (0.45 - asym_ewma) / asym_slope))
                    ttv[i] = float(min(cands)) if cands else 3.0
            else:
                consec = max(0, consec - 1)

        return {"warnings": w, "pred_ttv_min": ttv, "latency_ms": (time.perf_counter() - t0) * 1000.0 / n}


