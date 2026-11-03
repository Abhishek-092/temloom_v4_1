#!/usr/bin/env python3
"""Master Leakage-Free Training, Validation, and Held-Out Evaluation Pipeline for TEMLOOM."""

import json
import os
import tracemalloc
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
import yaml

from simulator import NetworkTelemetrySimulator
from models import (
    OperationalBaselineModel,
    RobustStatisticalModel,
    MultivariateGBDTModel,
    CUSUMHoltModel,
    HybridTemloomModel,
    RootCauseLocalizationBenchmark,
)


def evaluate_model_on_runs(
    model: Any,
    runs: List[Dict[str, Any]],
    dt_min: float = 0.25,
    min_actionable_lead_min: float = 2.0,
    strict_unpadded_coverage: bool = False,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Computes all 11 operational metrics across a set of scenario runs."""
    # tracemalloc disabled for fast loop
    per_run_records = []

    incident_recalls = []
    actionable_useful_flags = []
    lead_times = []
    detection_delays = []
    ttv_maes = []
    coverage_hits = []
    interval_widths = []
    latencies_ms = []

    total_false_alarms = 0
    total_true_warnings = 0
    total_operating_hours = 0.0
    missed_incidents = 0
    total_incidents = 0

    for run in runs:
        df = run["df"]
        out = model.predict_run(df, dt_min=dt_min)
        w = out["warnings"]
        pred_ttv = out["pred_ttv_min"]
        lo = out["lower_bound"]
        hi = out["upper_bound"]
        latencies_ms.append(float(out["latency_ms_per_step"]))

        t_arr = df["time_min"].values
        n = len(df)
        total_operating_hours += (n * dt_min) / 60.0

        episodes: List[Tuple[float, float, int]] = []
        in_ep = False
        ep_start_t = 0.0
        ep_start_idx = 0
        last_w_idx = -10
        for i in range(n):
            if w[i] == 1:
                if not in_ep:
                    in_ep = True
                    ep_start_t = float(t_arr[i])
                    ep_start_idx = i
                last_w_idx = i
            else:
                if in_ep and (i - last_w_idx) > 2:
                    episodes.append((ep_start_t, float(t_arr[last_w_idx]), ep_start_idx))
                    in_ep = False
        if in_ep:
            episodes.append((ep_start_t, float(t_arr[last_w_idx]), ep_start_idx))

        valid_cov = 0
        hit_cov = 0
        pad = 0.0 if strict_unpadded_coverage else 2.0
        for i in range(8, n - 40):
            if not np.isnan(lo[i]) and not np.isnan(hi[i]):
                interval_widths.append(float(hi[i] - lo[i]))
                true_future_u = float(df["true_util_mbps"].iat[i + 40])
                if np.max(df["routing_event"].values[i : i + 41]) == 0:
                    valid_cov += 1
                    if (lo[i] - pad) <= true_future_u <= (hi[i] + pad):
                        hit_cov += 1
        if valid_cov > 0:
            coverage_hits.append(hit_cov / valid_cov)

        ev_start = float(run["event_start_min"])
        has_breach = bool(run["sla_violation_occurred"])
        t_breach = run["sla_violation_time_min"]

        run_false_alarms = 0
        run_detected = False
        run_lead_time = np.nan
        run_det_delay = np.nan
        run_ttv_mae = np.nan
        run_actionable = False

        if has_breach and t_breach is not None:
            total_incidents += 1
            for (ep_s, ep_e, ep_idx) in episodes:
                if ep_s < ev_start - 0.25:
                    run_false_alarms += 1
                elif ep_s <= t_breach and not run_detected:
                    run_detected = True
                    total_true_warnings += 1
                    run_lead_time = float(t_breach - ep_s)
                    run_det_delay = float(max(0.0, ep_s - ev_start))
                    run_actionable = run_lead_time >= min_actionable_lead_min
                    ttv_errs = []
                    for k in range(ep_idx, min(n, ep_idx + 12)):
                        if t_arr[k] <= t_breach and not np.isnan(pred_ttv[k]):
                            actual_rem = t_breach - float(t_arr[k])
                            ttv_errs.append(abs(float(pred_ttv[k]) - actual_rem))
                    if ttv_errs:
                        run_ttv_mae = float(np.mean(ttv_errs))

            incident_recalls.append(1.0 if run_detected else 0.0)
            actionable_useful_flags.append(1.0 if run_actionable else 0.0)
            if run_detected:
                lead_times.append(run_lead_time)
                detection_delays.append(run_det_delay)
                if not np.isnan(run_ttv_mae):
                    ttv_maes.append(run_ttv_mae)
            else:
                missed_incidents += 1
        else:
            for _ in episodes:
                run_false_alarms += 1

        total_false_alarms += run_false_alarms
        per_run_records.append({
            "model": model.name,
            "scenario_code": run["code"],
            "scenario_name": run["name"],
            "seed": run["seed"],
            "has_sla_violation": has_breach,
            "sla_violation_time_min": t_breach,
            "detected": run_detected,
            "actionable_useful": run_actionable,
            "lead_time_min": run_lead_time,
            "detection_delay_min": run_det_delay,
            "ttv_mae_min": run_ttv_mae,
            "false_alarms": run_false_alarms,
            "latency_ms_per_step": out["latency_ms_per_step"],
        })

    _, peak_mem_bytes = tracemalloc.get_traced_memory()
    

    fa_per_hour = total_false_alarms / max(1e-6, total_operating_hours)
    precision = total_true_warnings / max(1, total_true_warnings + total_false_alarms)

    noisy_runs = [r for r in per_run_records if r["scenario_code"] in ("H", "L")]
    noisy_recall = float(np.mean([1.0 if r["detected"] else 0.0 for r in noisy_runs])) if noisy_runs else 0.0
    benign_runs = [r for r in per_run_records if not r["has_sla_violation"]]
    benign_fa_rate = float(np.mean([r["false_alarms"] for r in benign_runs])) if benign_runs else 0.0
    robustness_score = float(np.clip(noisy_recall - 0.35 * benign_fa_rate, 0.0, 1.0))

    summary_metrics = {
        "model": model.name,
        "incident_recall": round(float(np.mean(incident_recalls)) if incident_recalls else 0.0, 4),
        "missed_incidents": int(missed_incidents),
        "total_incidents": int(total_incidents),
        "false_alarms_total": int(total_false_alarms),
        "false_alarms_per_hour": round(float(fa_per_hour), 4),
        "precision": round(float(precision), 4),
        "median_lead_time_min": round(float(np.median(lead_times)) if lead_times else 0.0, 3),
        "iqr25_lead_time_min": round(float(np.percentile(lead_times, 25)) if lead_times else 0.0, 3),
        "iqr75_lead_time_min": round(float(np.percentile(lead_times, 75)) if lead_times else 0.0, 3),
        "mean_lead_time_min": round(float(np.mean(lead_times)) if lead_times else 0.0, 3),
        "median_detection_delay_min": round(float(np.median(detection_delays)) if detection_delays else 0.0, 3),
        "ttv_mae_min": round(float(np.mean(ttv_maes)) if ttv_maes else np.nan, 3),
        "empirical_interval_coverage": round(float(np.mean(coverage_hits)) if coverage_hits else np.nan, 3),
        "mean_interval_width_mbps": round(float(np.mean(interval_widths)) if interval_widths else np.nan, 3),
        "robustness_score": round(robustness_score, 3),
        "actionable_usefulness_rate": round(float(np.mean(actionable_useful_flags)) if actionable_useful_flags else 0.0, 4),
        "inference_latency_ms_per_step": round(float(np.mean(latencies_ms)), 4),
        "peak_memory_kb": round(peak_mem_bytes / 1024.0, 2),
    }
    return summary_metrics, per_run_records


def run_s1_parametric_family(
    sim: NetworkTelemetrySimulator,
    models: List[Any],
) -> pd.DataFrame:
    """Section 5.8: Executes the exact arithmetic S1 unit test + parametric family sweep."""
    sweep_configs = [
        {"case": "S1_Canonical_Unit_Test", "base_util_mbps": 50.0, "ramp_rate_mbps_per_min": 2.3, "noise_std_mbps": 0.05, "missing_prob": 0.0},
        {"case": "S1_Fast_Ramp_3.8Mbps", "base_util_mbps": 50.0, "ramp_rate_mbps_per_min": 3.8, "noise_std_mbps": 1.4, "missing_prob": 0.0},
        {"case": "S1_Slow_Ramp_1.5Mbps", "base_util_mbps": 55.0, "ramp_rate_mbps_per_min": 1.5, "noise_std_mbps": 1.4, "missing_prob": 0.0},
        {"case": "S1_High_Start_70Mbps", "base_util_mbps": 70.0, "ramp_rate_mbps_per_min": 2.3, "noise_std_mbps": 1.4, "missing_prob": 0.0},
        {"case": "S1_Heavy_Noise_4.5Mbps", "base_util_mbps": 50.0, "ramp_rate_mbps_per_min": 2.3, "noise_std_mbps": 4.5, "missing_prob": 0.0},
        {"case": "S1_Missing_20pct_Outliers", "base_util_mbps": 50.0, "ramp_rate_mbps_per_min": 2.3, "noise_std_mbps": 2.0, "missing_prob": 0.20, "outlier_prob": 0.04},
    ]
    rows = []
    for cfg in sweep_configs:
        case_name = cfg["case"]
        params = {k: v for k, v in cfg.items() if k != "case"}
        params["event_start_min"] = 5.0
        run = sim.generate_scenario("Scenario_A_Gradual_Congestion", seed=501, override_params=params)
        for m in models:
            _, recs = evaluate_model_on_runs(m, [run], dt_min=sim.dt_min)
            r = recs[0]
            rows.append({
                "case": case_name,
                "model": m.name,
                "sla_breach_min_elapsed": round(float(r["sla_violation_time_min"] - 5.0), 2) if r["sla_violation_time_min"] else np.nan,
                "detected": r["detected"],
                "lead_time_min": round(float(r["lead_time_min"]), 2) if not np.isnan(r["lead_time_min"]) else 0.0,
                "ttv_mae_min": round(float(r["ttv_mae_min"]), 2) if not np.isnan(r["ttv_mae_min"]) else np.nan,
                "false_alarms": r["false_alarms"],
            })
    return pd.DataFrame(rows)


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "experiment_config.yaml"), "r", encoding="utf-8") as f:
        exp_cfg = yaml.safe_load(f)

    sim = NetworkTelemetrySimulator(os.path.join(here, "scenarios.yaml"))
    scenario_keys = list(sim.config["scenarios"].keys())

    train_seeds = exp_cfg["splits_and_leakage_control"]["train_seeds"]
    val_seeds = exp_cfg["splits_and_leakage_control"]["val_seeds"]
    test_seeds = exp_cfg["splits_and_leakage_control"]["held_out_test_seeds"]

    train_runs = [sim.generate_scenario(k, s) for s in train_seeds for k in scenario_keys]
    val_runs = [sim.generate_scenario(k, s) for s in val_seeds for k in scenario_keys]
    test_runs = [sim.generate_scenario(k, s) for s in test_seeds for k in scenario_keys]

    model_a = OperationalBaselineModel()
    model_b = RobustStatisticalModel()
    model_c = MultivariateGBDTModel(n_estimators=45, max_depth=3, learning_rate=0.12, prob_threshold=0.52)
    model_c.fit_on_scenarios(train_runs, dt_min=sim.dt_min)

    model_d = CUSUMHoltModel()
    model_e = HybridTemloomModel(gbdt_model=model_c, conformal_alpha=0.10, decay_rho=0.985, freeze_enabled=True)
    model_e.calibrate_on_validation(val_runs, dt_min=sim.dt_min)

    models = [model_a, model_b, model_c, model_d, model_e]

    summary_rows = []
    all_test_records = []
    for m in models:
        metrics, recs = evaluate_model_on_runs(m, test_runs, dt_min=sim.dt_min, strict_unpadded_coverage=True)
        summary_rows.append(metrics)
        all_test_records.extend(recs)
        print(
            f"[TEST] {m.name:65s} | Recall={metrics['incident_recall']:.3f} | "
            f"FA/hr={metrics['false_alarms_per_hour']:.3f} | MedLead={metrics['median_lead_time_min']:.2f}m | "
            f"Prec={metrics['precision']:.3f} | TTV_MAE={metrics['ttv_mae_min']:.2f}m | Cov={metrics['empirical_interval_coverage']}"
        )

    df_results = pd.DataFrame(summary_rows)
    df_results.to_csv(os.path.join(here, "results.csv"), index=False)

    df_per_run = pd.DataFrame(all_test_records)
    df_per_scen = (
        df_per_run.groupby(["model", "scenario_code", "scenario_name", "has_sla_violation"], as_index=False)
        .agg(
            detection_rate=("detected", "mean"),
            actionable_rate=("actionable_useful", "mean"),
            median_lead_time_min=("lead_time_min", "median"),
            mean_ttv_mae_min=("ttv_mae_min", "mean"),
            mean_false_alarms_per_run=("false_alarms", "mean"),
        )
    )
    df_per_scen.to_csv(os.path.join(here, "per_scenario_results.csv"), index=False)

    df_s1 = run_s1_parametric_family(sim, models)
    df_s1.to_csv(os.path.join(here, "s1_parametric_results.csv"), index=False)

    rca_bench = RootCauseLocalizationBenchmark()
    rca_results = rca_bench.run_benchmark(n_trials_per_mode=40, seed=2026)

    summary_payload = {
        "experiment_id": exp_cfg["experiment_id"],
        "environment": exp_cfg["environment"],
        "dataset_splits": {
            "train_runs": len(train_runs),
            "validation_runs": len(val_runs),
            "held_out_test_runs": len(test_runs),
            "total_test_operating_hours_per_model": round(len(test_runs) * (sim.duration_min / 60.0), 1),
        },
        "held_out_model_comparison": summary_rows,
        "rca_localization_benchmark": rca_results,
    }

    with open(os.path.join(here, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, indent=2)

    print("Saved results.csv, per_scenario_results.csv, s1_parametric_results.csv, and summary.json.")


if __name__ == "__main__":
    main()
