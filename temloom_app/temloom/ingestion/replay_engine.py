#!/usr/bin/env python3
"""
temloom/ingestion/replay_engine.py — Deterministic Historical Replay Engine
Supports 1x, 10x, 50x, and Instant Batch replay of scenario telemetry streams.
"""

from typing import Dict, Any, List
from temloom.simulation.simulator import NetworkTelemetrySimulator


class DeterministicReplayEngine:
    def __init__(self):
        self.sim = NetworkTelemetrySimulator()
        self.current_step: int = 0
        self.current_scenario: str = "Scenario_A_Linear_Congestion"
        self.current_seed: int = 301
        self._cached_run: Dict[str, Any] = {}

    def configure(self, scenario_id: str, seed: int = 301) -> Dict[str, Any]:
        self.current_scenario = scenario_id
        self.current_seed = int(seed)
        self.current_step = 0
        scen_keys = list(self.sim.config["scenarios"].keys())
        target_key = scenario_id if scenario_id in scen_keys else scen_keys[0]
        self._cached_run = self.sim.generate_scenario(target_key, self.current_seed)
        return {
            "scenario_id": target_key,
            "seed": self.current_seed,
            "total_steps": len(self._cached_run["df"]),
            "has_sla_violation": self._cached_run["has_sla_violation"],
            "sla_time_min": self._cached_run["sla_time_min"],
        }

    def step(self, delta_steps: int = 1) -> Dict[str, Any]:
        if not self._cached_run:
            self.configure(self.current_scenario, self.current_seed)
        df = self._cached_run["df"]
        self.current_step = min(len(df) - 1, max(0, self.current_step + delta_steps))
        row = df.iloc[self.current_step].to_dict()
        return {
            "scenario_id": self.current_scenario,
            "seed": self.current_seed,
            "step": int(self.current_step),
            "time_min": float(row["time_min"]),
            "telemetry": {k: (None if (isinstance(v, float) and v != v) else float(v)) for k, v in row.items()},
        }
