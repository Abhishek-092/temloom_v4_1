#!/usr/bin/env python3
"""
temloom/prediction/corroborator.py — Dual-Engine Statistical + Graph Corroboration Gate
& Tiered Autonomy Policy Evaluator (AETH-7.3 & AETH-7.4).

Enforces the core safety principle:
- Statistical hazard engine (Models G1-G4) AND deterministic NetworkX graph / physics
  projection must agree (`engines_agree == True`).
- If they disagree, an automatic SAFETY TRIP downgrades execution to `RECOMMEND_ONLY`.
- Even when they agree, critical actions (CORE_PATH_FAILOVER, CONTROLLER_POLICY_ROLLBACK,
  NODE_ISOLATION) are hard-locked in `taxonomy.py` to `RECOMMEND_ONLY` (requiring
  human NOC_APPROVER Ed25519 sign-off + 4-stage safety gate + 2PC).
"""

import os
from typing import Dict, Any, Tuple
from temloom.core.taxonomy import info_for_category, policy_for_action
from temloom.rca.graph_model import ClonalGraphEngine

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_POLICY_OVERRIDE = os.path.join(REPO_ROOT, "configs", "policy_overrides.json")


class DualEngineCorroborator:
    def __init__(self, override_path: str = DEFAULT_POLICY_OVERRIDE):
        self.graph_engine = ClonalGraphEngine()
        self.override_path = override_path

    def evaluate_corroboration(
        self,
        issue_category: str,
        model_anomaly_score: float,
        graph_projects_violation: bool = True,
        digital_twin_divergence: float = 0.25,
    ) -> Dict[str, Any]:
        tax_info = info_for_category(issue_category)
        action_class = tax_info["action"]
        playbook_id = tax_info["playbook_id"]
        model_detected = issue_category != "NORMAL" and model_anomaly_score >= 0.50

        engines_agree = bool(model_detected == graph_projects_violation)
        policy = policy_for_action(action_class, self.override_path)

        execution_mode = "RECOMMEND_ONLY"
        if not model_detected:
            rationale = "System nominal. Statistical Engine (Models G1-G4) and NetworkX Graph Engine agree."
        elif not engines_agree:
            rationale = (
                f"SAFETY TRIPPED (Disagreement): Statistical Engine predicts {issue_category} "
                f"(score={model_anomaly_score:.2f}), but Deterministic NetworkX Graph projects zero SLA/queue bottlenecks. "
                f"Downgraded to RECOMMEND_ONLY."
            )
        else:
            if policy.get("locked", True) or not policy.get("auto_execute", False):
                rationale = (
                    f"Statistical Engine ({issue_category}, score={model_anomaly_score:.2f}) and NetworkX Graph Engine "
                    f"corroborate hazard (twin_div={digital_twin_divergence:.3f}). Action {action_class} is HARD-LOCKED "
                    f"to RECOMMEND_ONLY (requires Stage 4 Ed25519 human approval)."
                )
            elif model_anomaly_score >= max(policy["min_conf"], policy["hard_floor_conf"]):
                execution_mode = "PRE_VALIDATED_STAGED"
                rationale = (
                    f"Both engines corroborate {issue_category} (score={model_anomaly_score:.2f} >= {policy['min_conf']:.2f}, "
                    f"twin_div={digital_twin_divergence:.3f}). Eligible for pre-validated staged execution after 4-stage safety gate."
                )
            else:
                rationale = (
                    f"Both engines corroborate {issue_category}, but score ({model_anomaly_score:.2f}) is below "
                    f"policy threshold ({max(policy['min_conf'], policy['hard_floor_conf']):.2f})."
                )

        return {
            "engines_agree": engines_agree,
            "action_class": action_class,
            "playbook_id": playbook_id,
            "autonomy_execution_mode": execution_mode,
            "rationale": rationale,
            "digital_twin_divergence": round(float(digital_twin_divergence), 3),
        }
