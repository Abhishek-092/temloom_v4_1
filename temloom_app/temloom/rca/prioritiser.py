#!/usr/bin/env python3
"""
temloom/rca/prioritiser.py — Deterministic Incident Priority Scorer P_incident in [0, 100].
"""

from typing import List, Optional


def compute_incident_priority(
    anomaly_score: float,
    estimated_tti_min: Optional[float],
    affected_services: List[str],
    freshness_state: str = "FRESH",
    is_ambiguous: bool = False,
) -> float:
    """
    Combines hazard severity (0..45 pts), Time-to-Impact urgency (0..35 pts),
    and service SLA criticality (0..20 pts), minus staleness penalty (-15 pts).
    """
    sev_pts = min(45.0, max(0.0, float(anomaly_score) * 45.0))
    if estimated_tti_min is None or estimated_tti_min <= 0:
        tti_pts = 15.0
    else:
        tti_pts = max(5.0, min(35.0, 35.0 * (1.0 - min(estimated_tti_min, 15.0) / 18.0)))

    sla_pts = 10.0
    if any("voip" in s for s in affected_services):
        sla_pts = 20.0
    elif any("video" in s or "erp" in s for s in affected_services):
        sla_pts = 15.0

    penalty = 15.0 if freshness_state == "STALE_TELEMETRY" else (5.0 if is_ambiguous else 0.0)
    return round(float(min(100.0, max(0.0, sev_pts + tti_pts + sla_pts - penalty))), 1)
