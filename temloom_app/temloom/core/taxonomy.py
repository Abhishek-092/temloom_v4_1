#!/usr/bin/env python3
"""
temloom/core/taxonomy.py — Single Source of Truth for TEMLOOM's Fault Taxonomy,
Per-Service SLA Tiers, and Tiered Autonomy Policy Matrix (incorporating AETH-7.3).

Every subsystem (fault injector, telemetry collector, Models G1-G4, 4-layer DAG RCA,
Clonal Counterfactual Search, 4-stage Safety Gate, and 5-Workbench GUI) imports
from this module so enum names, SLA thresholds, and hard-locked autonomy floors
never drift across files.
"""

from typing import Dict, Any, List
import json
import os

# Canonical Fault & Hazard Catalogue across all 4 TEMLOOM domains
FAULTS: List[Dict[str, Any]] = [
    {
        "id": 0,
        "label": "Healthy",
        "issue_category": "NORMAL",
        "domain": "NONE",
        "display": "Healthy / Nominal",
        "action": "NO_ACTION",
        "playbook_id": "PB-NONE",
        "critical": False,
    },
    {
        "id": 1,
        "label": "latency",
        "issue_category": "LATENCY_DRIFT",
        "domain": "LINK",
        "display": "Latency Drift / Blackhole",
        "action": "REROUTE_BRANCH",
        "playbook_id": "PB-STEER-BULK-AF21",
        "critical": False,
    },
    {
        "id": 2,
        "label": "loss",
        "issue_category": "TUNNEL_REKEY_EXHAUSTION",
        "domain": "TUNNEL",
        "display": "Packet Loss / Tunnel Rekey Exhaustion",
        "action": "REROUTE_BRANCH",
        "playbook_id": "PB-TUNNEL-REKEY-STEER",
        "critical": True,
    },
    {
        "id": 3,
        "label": "corrupt",
        "issue_category": "ANTI_REPLAY_OVERFLOW",
        "domain": "TUNNEL",
        "display": "Frame Corruption / Anti-Replay Drop",
        "action": "REROUTE_BRANCH",
        "playbook_id": "PB-TUNNEL-REKEY-STEER",
        "critical": False,
    },
    {
        "id": 4,
        "label": "rate",
        "issue_category": "LINK_CONGESTION",
        "domain": "LINK",
        "display": "Link Congestion / Queue Saturation",
        "action": "QOS_SHAPE_QUEUE",
        "playbook_id": "PB-STEER-BULK-AF21",
        "critical": True,
    },
    {
        "id": 5,
        "label": "flap",
        "issue_category": "BGP_FLAP_CASCADE",
        "domain": "ROUTING",
        "display": "BGP / OSPF Control-Plane Flap Cascade",
        "action": "CORE_PATH_FAILOVER",
        "playbook_id": "PB-BGP-LOCALPREF",
        "critical": True,
    },
    {
        "id": 6,
        "label": "policy_drift",
        "issue_category": "POLICY_DRIFT",
        "domain": "POLICY",
        "display": "SD-WAN Controller Policy Drift",
        "action": "CONTROLLER_POLICY_ROLLBACK",
        "playbook_id": "PB-ROLLBACK-GOLDEN-POLICY",
        "critical": True,
    },
]

NUM_CLASSES = len(FAULTS)
LABEL_TO_ID = {f["label"]: f["id"] for f in FAULTS}
ID_TO_INFO = {f["id"]: f for f in FAULTS}
ID_TO_LABEL = {f["id"]: f["label"] for f in FAULTS}
ID_TO_DISPLAY = {f["id"]: f["display"] for f in FAULTS}
DISPLAY_TO_INFO = {f["display"]: f for f in FAULTS}
CATEGORY_TO_INFO = {f["issue_category"]: f for f in FAULTS}

# Per-Service SLA Thresholds (used by Clonal Graph Search & Safety Engine)
SERVICE_SLA_TIERS: Dict[str, Dict[str, Any]] = {
    "voip": {
        "dscp": "EF",
        "dscp_val": 46,
        "latency_ms_max": 30.0,
        "jitter_ms_max": 15.0,
        "packet_loss_pct_max": 0.5,
        "priority": 1,
    },
    "video": {
        "dscp": "AF41",
        "dscp_val": 34,
        "latency_ms_max": 50.0,
        "jitter_ms_max": 20.0,
        "packet_loss_pct_max": 1.0,
        "priority": 2,
    },
    "database": {
        "dscp": "AF21",
        "dscp_val": 18,
        "latency_ms_max": 50.0,
        "jitter_ms_max": 25.0,
        "packet_loss_pct_max": 0.1,
        "priority": 2,
    },
    "bulk": {
        "dscp": "BE",
        "dscp_val": 0,
        "latency_ms_max": 250.0,
        "jitter_ms_max": 100.0,
        "packet_loss_pct_max": 2.0,
        "priority": 3,
    },
    "default": {
        "dscp": "BE",
        "dscp_val": 0,
        "latency_ms_max": 100.0,
        "jitter_ms_max": 30.0,
        "packet_loss_pct_max": 1.0,
        "priority": 99,
    },
}

# Tiered Autonomy Policy Matrix with Hard-Locked Safety Floors (AETH-7.3)
# Core/BGP/Controller/Isolation actions are permanently locked (locked=True) to RECOMMEND_ONLY.
DEFAULT_ACTION_POLICY: Dict[str, Dict[str, Any]] = {
    "REROUTE_BRANCH": {
        "min_conf": 0.80,
        "hard_floor_conf": 0.75,
        "auto_execute": True,
        "locked": False,
        "description": "Steer non-critical branch traffic onto pre-validated backup SD-WAN tunnel",
    },
    "QOS_SHAPE_QUEUE": {
        "min_conf": 0.75,
        "hard_floor_conf": 0.70,
        "auto_execute": True,
        "locked": False,
        "description": "Shape / throttle bulk AF21/BE queues during congestion to protect EF VoIP",
    },
    "CORE_PATH_FAILOVER": {
        "min_conf": 0.90,
        "hard_floor_conf": 0.90,
        "auto_execute": False,
        "locked": True,
        "description": "Failover primary core MPLS/BGP path via local-pref / AS-prepend (LOCKED: Human Ed25519 Required)",
    },
    "CONTROLLER_POLICY_ROLLBACK": {
        "min_conf": 0.90,
        "hard_floor_conf": 0.90,
        "auto_execute": False,
        "locked": True,
        "description": "Rollback SD-WAN controller AAR policy to golden SHA-256 hash (LOCKED: Human Ed25519 Required)",
    },
    "NODE_ISOLATION": {
        "min_conf": 0.99,
        "hard_floor_conf": 0.99,
        "auto_execute": False,
        "locked": True,
        "description": "Isolate a suspected rogue or compromised router node (LOCKED: Human Ed25519 Required)",
    },
    "NO_ACTION": {
        "min_conf": 1.00,
        "hard_floor_conf": 1.00,
        "auto_execute": False,
        "locked": True,
        "description": "System nominal — no mitigation required",
    },
}


def info_for_id(class_id: int) -> Dict[str, Any]:
    return ID_TO_INFO.get(int(class_id), ID_TO_INFO[0])


def info_for_category(issue_category: str) -> Dict[str, Any]:
    return CATEGORY_TO_INFO.get(issue_category, ID_TO_INFO[0])


def get_effective_policy_matrix(override_path: str = None) -> Dict[str, Dict[str, Any]]:
    """Loads operator policy overrides while enforcing locked rows and detectability of drift."""
    import copy
    matrix = copy.deepcopy(DEFAULT_ACTION_POLICY)
    if override_path and os.path.exists(override_path):
        try:
            with open(override_path, "r") as f:
                overrides = json.load(f)
            for act, vals in overrides.items():
                if act in matrix:
                    if matrix[act]["locked"]:
                        # Locked rows can NEVER enable auto_execute
                        matrix[act]["auto_execute"] = False
                    else:
                        if "min_conf" in vals:
                            matrix[act]["min_conf"] = float(vals["min_conf"])
                        if "auto_execute" in vals:
                            matrix[act]["auto_execute"] = bool(vals["auto_execute"])
                        matrix[act]["policy_drift_violation"] = (
                            matrix[act]["min_conf"] < matrix[act]["hard_floor_conf"]
                        )
        except Exception:
            pass
    return matrix


def policy_for_action(action: str, override_path: str = None) -> Dict[str, Any]:
    matrix = get_effective_policy_matrix(override_path)
    return matrix.get(
        action,
        {
            "min_conf": 1.0,
            "hard_floor_conf": 1.0,
            "auto_execute": False,
            "locked": True,
            "description": "unknown action",
        },
    )
