#!/usr/bin/env python3
"""
temloom/simulation/fault_injector.py — Out-of-Band Fault Injector & Independent
Ground-Truth Recorder (Schemas 11 & 12).
Strictly isolated from runtime feature extraction (DS-1.1E).
"""

import json
import subprocess
import time
import uuid
from typing import Dict, Any, List, Optional
from temloom.core.database import TemloomDatabase

LAB_NAME = "temloom"


class OutOfBandFaultInjector:
    def __init__(self, db: TemloomDatabase = None):
        self.db = db or TemloomDatabase()

    def inject_and_record(
        self,
        experiment_id: str,
        scenario_id: str,
        random_seed: int,
        fault_category: str,
        affected_entity_id: str,
        related_entities: List[str],
        fault_severity: str,
        fault_parameters: Dict[str, Any],
        expects_sla_breach: bool,
        sla_breach_occurred: bool,
        sla_breach_onset_ms: Optional[int],
        expected_impact: Dict[str, Any],
        actual_impact: Dict[str, Any],
        start_utc_ms: Optional[int] = None,
        end_utc_ms: Optional[int] = None,
        container_cmd: Optional[str] = None,
    ) -> Dict[str, str]:
        now_ms = (int(time.time() * 1000) // 15000) * 15000
        s_ms = start_utc_ms or now_ms
        e_ms = end_utc_ms or (s_ms + 1800000)
        fault_id = str(uuid.uuid4())
        gt_id = str(uuid.uuid4())

        if container_cmd:
            try:
                subprocess.run(container_cmd, shell=True, capture_output=True, timeout=3.0)
            except Exception:
                pass

        self.db.execute_write(
            """INSERT INTO injected_fault_records
               (fault_id, experiment_id, scenario_id, random_seed, fault_category,
                affected_entity_id, related_entities_json, start_utc_ms, end_utc_ms,
                fault_severity, fault_parameters, injection_succeeded)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
            (
                fault_id,
                experiment_id,
                scenario_id,
                random_seed,
                fault_category,
                affected_entity_id,
                json.dumps(related_entities),
                s_ms,
                e_ms,
                fault_severity,
                json.dumps(fault_parameters),
            ),
        )

        self.db.execute_write(
            """INSERT INTO ground_truth_incident_labels
               (gt_incident_id, fault_id, expects_sla_breach, sla_breach_occurred,
                sla_breach_onset_ms, recovery_utc_ms, expected_impact_json, actual_impact_json,
                detected_by_system, predicted_before_sla, realized_lead_min)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0, NULL)""",
            (
                gt_id,
                fault_id,
                1 if expects_sla_breach else 0,
                1 if sla_breach_occurred else 0,
                sla_breach_onset_ms,
                e_ms,
                json.dumps(expected_impact),
                json.dumps(actual_impact),
            ),
        )
        return {"fault_id": fault_id, "gt_incident_id": gt_id}

    def update_post_hoc_evaluation(
        self,
        gt_incident_id: str,
        detected_by_system: bool,
        predicted_before_sla: bool,
        realized_lead_min: Optional[float],
    ):
        self.db.execute_write(
            """UPDATE ground_truth_incident_labels
               SET detected_by_system = ?, predicted_before_sla = ?, realized_lead_min = ?
               WHERE gt_incident_id = ?""",
            (
                1 if detected_by_system else 0,
                1 if predicted_before_sla else 0,
                realized_lead_min,
                gt_incident_id,
            ),
        )
