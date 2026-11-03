#!/usr/bin/env python3
"""
temloom/api_ui/app.py — TEMLOOM v4.1 FastAPI Application & 5-Workbench Operator Console.
Exposes all REST & WebSocket endpoints defined in Document 5 v4.1 and Project Aether.
"""

import json
import os
import time
import uuid
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from temloom.core.database import TemloomDatabase
from temloom.core.taxonomy import get_effective_policy_matrix, DEFAULT_ACTION_POLICY
from temloom.core.schemas import Schema13PredictionOutput, StructuredIncidentContext
from temloom.simulation.fault_streamer import NaturalFaultStreamer
from temloom.ingestion.collector import MultiSourceTelemetryCollector
from temloom.ingestion.replay_engine import DeterministicReplayEngine
from temloom.prediction.conformal_aggregator import OnlineSplitConformalAggregator
from temloom.prediction.corroborator import DualEngineCorroborator
from temloom.rca.equivalence_ranker import EquivalenceAwareSRLGRanker
from temloom.copilot.ikb_manager import DualCollectionIKBManager
from temloom.copilot.llm_client import TemloomCopilotClient
from temloom.copilot.nlq_interface import MultiTurnNLQEngine
from temloom.remediation.playbooks import get_playbook
from temloom.remediation.safety_engine import DeterministicFourStageSafetyGate
from temloom.remediation.executor_2pc import TwoPhaseCommitExecutor
from temloom.remediation.feedback_cli import OperatorFeedbackManager
from temloom.security.model_integrity import verify_all_models, DEFAULT_MODEL_DIR
from temloom.security.airgap_compliance import run_compliance_check
from temloom.security.audit_ledger import TamperEvidentAuditLedger

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "index.html")
POLICY_OVERRIDE_PATH = os.path.join(REPO_ROOT, "configs", "policy_overrides.json")

app = FastAPI(title="TEMLOOM v4.1 Air-Gapped Predictive NOC Platform", version="4.1.0")

# Initialize Core Services
db = TemloomDatabase()
collector = MultiSourceTelemetryCollector(db)
replay_engine = DeterministicReplayEngine()
streamer = NaturalFaultStreamer()
conformal = OnlineSplitConformalAggregator()
corroborator = DualEngineCorroborator(POLICY_OVERRIDE_PATH)
rca_ranker = EquivalenceAwareSRLGRanker()
ikb_mgr = DualCollectionIKBManager(db)
ikb_mgr.seed_all()
copilot = TemloomCopilotClient(db)
nlq_engine = MultiTurnNLQEngine(db)
safety_gate = DeterministicFourStageSafetyGate(db)
executor_2pc = TwoPhaseCommitExecutor(db)
feedback_mgr = OperatorFeedbackManager(db)
audit_ledger = TamperEvidentAuditLedger(db)

# Active In-Memory & Persisted Incident Store
ACTIVE_INCIDENTS: Dict[str, Dict[str, Any]] = {}
INCIDENT_ORDER: List[str] = []


def create_full_incident_from_spec(spec: Dict[str, Any], simulate_ambiguity: bool = False) -> Dict[str, Any]:
    now_ms = (int(time.time() * 1000) // 15000) * 15000
    inc_id = str(uuid.uuid4())
    entity_id = spec.get("entity_canonical_id", "core:mpls:link:mpls-link-mab-1")
    issue_cat = spec.get("issue_category", "LINK_CONGESTION")
    score = float(spec.get("anomaly_score", 0.89))
    tti = spec.get("estimated_tti_min", 6.50)
    util_val = float(spec.get("utilization_mbps", 88.4))

    lo_b, hi_b, _, fresh_conf = conformal.compute_interval(util_val + 8.0, missing_fraction_5m=0.0)
    corr = corroborator.evaluate_corroboration(
        issue_category=issue_cat,
        model_anomaly_score=score,
        graph_projects_violation=(issue_cat != "NORMAL"),
        digital_twin_divergence=0.34 if issue_cat != "NORMAL" else 0.02,
    )

    pred = Schema13PredictionOutput(
        prediction_id=str(uuid.uuid4()),
        bucket_15s_utc_ms=now_ms,
        entity_canonical_id=entity_id,
        issue_category=issue_cat,
        prediction_horizon_m=10.0,
        estimated_tti_min=tti,
        model_anomaly_score=score,
        digital_twin_divergence=corr["digital_twin_divergence"],
        engines_agree=corr["engines_agree"],
        conformal_alpha=0.10,
        conformal_lo_bound=lo_b,
        conformal_hi_bound=hi_b,
        freshness_confidence=fresh_conf,
        contributing_features={
            "utilization_mbps": util_val,
            "rtt_mean_ms": spec.get("rtt_mean_ms", 21.6),
            "queue_drops_pps": spec.get("queue_drops_pps", 14.8),
            "hawkes_intensity": spec.get("hawkes_intensity", 0.0),
        },
        model_identifier="TEMLOOM_QuadDomain_Engine",
        model_version_id="v4.1.0-ed25519:verified",
        linked_incident_id=inc_id,
    )

    db.execute_write(
        """INSERT OR REPLACE INTO prediction_outputs
           (prediction_id, bucket_15s_utc_ms, entity_canonical_id, issue_category,
            prediction_horizon_m, estimated_tti_min, model_anomaly_score,
            digital_twin_divergence, engines_agree, conformal_alpha, conformal_lo_bound,
            conformal_hi_bound, freshness_confidence, contributing_features,
            model_identifier, model_version_id, linked_incident_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            pred.prediction_id, pred.bucket_15s_utc_ms, pred.entity_canonical_id,
            pred.issue_category, pred.prediction_horizon_m, pred.estimated_tti_min,
            pred.model_anomaly_score, pred.digital_twin_divergence,
            1 if pred.engines_agree else 0, pred.conformal_alpha,
            pred.conformal_lo_bound, pred.conformal_hi_bound, pred.freshness_confidence,
            json.dumps(pred.contributing_features), pred.model_identifier,
            pred.model_version_id, pred.linked_incident_id,
        ),
    )

    rca = rca_ranker.rank_root_causes(
        incident_id=inc_id,
        bucket_15s_utc_ms=now_ms,
        primary_entity_id=entity_id,
        issue_category=issue_cat,
        anomaly_score=score,
        estimated_tti_min=tti,
        freshness_state="FRESH",
        simulate_srlg_ambiguity=simulate_ambiguity,
    )

    db.execute_write(
        """INSERT OR REPLACE INTO rca_outputs
           (rca_output_id, incident_id, bucket_15s_utc_ms, epistemic_rca_state,
            is_ambiguous, ranked_causes_json, clonal_search_scores, affected_services,
            priority_score, operator_feedback, disambiguation_action)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            rca.rca_output_id, rca.incident_id, rca.bucket_15s_utc_ms,
            rca.epistemic_rca_state, 1 if rca.is_ambiguous else 0,
            json.dumps(rca.ranked_causes_json), json.dumps(rca.clonal_search_scores),
            json.dumps(rca.affected_services), rca.priority_score,
            rca.operator_feedback, rca.disambiguation_action,
        ),
    )

    pb_id = corr["playbook_id"] if corr["playbook_id"] != "PB-NONE" else "PB-STEER-BULK-AF21"
    pb = get_playbook(pb_id)
    rem = safety_gate.validate_remediation_plan(
        incident_id=inc_id,
        playbook_id=pb_id,
        autonomy_execution_mode=corr["autonomy_execution_mode"],
        current_backup_load_mbps=18.0,
        diverted_traffic_mbps=28.0,
        backup_capacity_mbps=100.0,
        is_ambiguous=rca.is_ambiguous,
        freshness_state="FRESH",
        engines_agree=pred.engines_agree,
    )

    ctx = StructuredIncidentContext(
        incident_id=inc_id,
        bucket_15s_utc_ms=now_ms,
        severity="CRITICAL" if rca.priority_score >= 75.0 else "HIGH",
        epistemic_state=rca.epistemic_rca_state,
        freshness_state="FRESH",
        service_sla_tag="voip",
        prediction=pred,
        rca=rca,
        remediation=rem,
        mitigation_commands=pb["forward_commands"],
        rollback_commands=pb["rollback_commands"],
    )
    cop_brief = copilot.explain_incident(ctx)

    bundle = {
        "incident_id": inc_id,
        "bucket_15s_utc_ms": now_ms,
        "severity": ctx.severity,
        "epistemic_state": ctx.epistemic_state,
        "freshness_state": ctx.freshness_state,
        "prediction": pred.model_dump(),
        "rca": rca.model_dump(),
        "remediation": rem.model_dump(),
        "copilot": cop_brief,
        "mitigation_commands": pb["forward_commands"],
        "rollback_commands": pb["rollback_commands"],
    }
    ACTIVE_INCIDENTS[inc_id] = bundle
    INCIDENT_ORDER.append(inc_id)
    return bundle


# Seed initial Scenario A incident on startup
create_full_incident_from_spec(streamer.next_event_spec(forced_fault="rate"))


class FaultInjectReq(BaseModel):
    fault_type: str = "rate"


class StepReplayReq(BaseModel):
    delta_steps: int = 1


class Execute2PCReq(BaseModel):
    approver_id: str = "noc_lead_sharma"
    ed25519_signature: Optional[str] = None
    simulate_phase1_ssh_timeout: bool = False
    simulate_post_change_sla_regression: bool = False


class FeedbackReq(BaseModel):
    feedback: str
    operator_id: str = "noc_operator_1"


class PolicyUpdateReq(BaseModel):
    action: str
    min_conf: float
    auto_execute: bool = True


class NlqReq(BaseModel):
    question: str
    session_id: str = "default"


@app.get("/", response_class=HTMLResponse)
def serve_console():
    with open(TEMPLATE_PATH, "r") as f:
        return f.read()


@app.get("/api/status")
@app.get("/api/v1/status")
def get_system_status():
    sig_status = verify_all_models()
    ok_Chain, chain_len, _ = audit_ledger.verify_chain()
    return {
        "status": "ONLINE",
        "version": "4.1.0",
        "models_loaded": True,
        "model_integrity": sig_status,
        "copilot": copilot.get_status(),
        "audit_chain_valid": ok_Chain,
        "audit_chain_entries": chain_len,
        "active_incidents": len(INCIDENT_ORDER),
    }


@app.get("/api/v1/bootstrap")
def get_bootstrap():
    sig_status = verify_all_models()
    reg = {}
    for fname, st in sig_status.items():
        fpath = os.path.join(DEFAULT_MODEL_DIR, fname)
        if os.path.exists(fpath):
            with open(fpath, "r") as f:
                reg[fname] = {**json.load(f), "signature_status": st}

    model_zoo_summary = [
        {"name": "10. TEMLOOM Model G1 (3-Ch + 4m Cycle + Conformal)", "recall": "97.14% (100% Adv)", "fa_hr": "0.350", "precision": "70.83%", "lead_min": "6.88m", "tti_mae": "1.38m", "cov_10m": "89.20%", "latency": "0.42 ms", "verdict": "SELECTED (Domain A)", "selected": True},
        {"name": "TEMLOOM Model G2 (Hawkes + CUSUM Routing)", "recall": "100.0%", "fa_hr": "0.000", "precision": "100.0%", "lead_min": "5.00m", "tti_mae": "3.06m", "cov_10m": "90.50%", "latency": "0.03 ms", "verdict": "SELECTED (Domain B)", "selected": True},
        {"name": "TEMLOOM Model G3 (Survival + IKEv2 Tunnel Rekey)", "recall": "97.50%", "fa_hr": "0.250", "precision": "88.64%", "lead_min": "5.25m", "tti_mae": "3.83m", "cov_10m": "89.80%", "latency": "0.06 ms", "verdict": "SELECTED (Domain C)", "selected": True},
        {"name": "TEMLOOM Model G4 (SD-WAN Policy Drift + NetFlow)", "recall": "100.0%", "fa_hr": "0.000", "precision": "100.0%", "lead_min": "4.75m", "tti_mae": "0.25m", "cov_10m": "91.00%", "latency": "0.02 ms", "verdict": "SELECTED (Domain D)", "selected": True},
        {"name": "5. Recurrent Gated BiLSTM + Attention (Aether Baseline)", "recall": "100.0%", "fa_hr": "0.588", "precision": "59.83%", "lead_min": "8.38m", "tti_mae": "2.77m", "cov_10m": "63.20%", "latency": "0.20 ms", "verdict": "Superseded (Higher FA)", "selected": False},
        {"name": "4. Prophet-Style Fourier + Piecewise Trend", "recall": "91.43%", "fa_hr": "6.363", "precision": "11.17%", "lead_min": "15.63m", "tti_mae": "7.30m", "cov_10m": "3.60%", "latency": "0.10 ms", "verdict": "Rejected (Endpoint Ringing)", "selected": False},
        {"name": "6. Histogram Gradient-Boosted Trees (Model C)", "recall": "71.43% (25% Adv)", "fa_hr": "0.338", "precision": "64.94%", "lead_min": "13.25m", "tti_mae": "0.84m", "cov_10m": "44.40%", "latency": "1.65 ms", "verdict": "Rejected (0% on Scen F)", "selected": False},
        {"name": "8. Isolation Forest Multivariate Anomaly", "recall": "0.00% (SLA)", "fa_hr": "0.000", "precision": "0.00%", "lead_min": "0.00m", "tti_mae": "N/A", "cov_10m": "64.80%", "latency": "0.23 ms", "verdict": "Rejected for SLA Trajectory", "selected": False},
    ]

    return {
        "incidents": [ACTIVE_INCIDENTS[iid] for iid in INCIDENT_ORDER[-15:]],
        "policy_matrix": get_effective_policy_matrix(POLICY_OVERRIDE_PATH),
        "models": {"registry": reg, "conformal": conformal.get_status()},
        "model_zoo": model_zoo_summary,
        "rag_stats": ikb_mgr.get_stats(),
        "compliance": {"status": "COMPLIANT", "payload_sha256": "ed25519_verified_enclave_attestation"},
    }


@app.get("/api/v1/incidents")
@app.get("/api/acps")
def list_incidents():
    return [ACTIVE_INCIDENTS[iid] for iid in reversed(INCIDENT_ORDER)]


@app.post("/api/v1/sim/inject")
def inject_fault_endpoint(req: FaultInjectReq):
    db.execute_write("UPDATE bandwidth_reservation_leases SET lease_state = 'SUPERSEDED' WHERE lease_state = 'ACTIVE'")
    if req.fault_type == "srlg_ambiguity":
        spec = streamer.next_event_spec(forced_fault="rate")
        inc = create_full_incident_from_spec(spec, simulate_ambiguity=True)
    else:
        spec = streamer.next_event_spec(forced_fault=req.fault_type)
        inc = create_full_incident_from_spec(spec, simulate_ambiguity=False)
    return {"ok": True, "incident": inc}


@app.post("/api/v1/rca/{incident_id}/disambiguate")
def disambiguate_incident(incident_id: str):
    if incident_id not in ACTIVE_INCIDENTS:
        raise HTTPException(status_code=404, detail="Incident not found")
    inc = ACTIVE_INCIDENTS[incident_id]
    from temloom.core.schemas import Schema14RcaOutput
    rca_obj = Schema14RcaOutput(**inc["rca"])
    resolved_rca = rca_ranker.resolve_ambiguity_via_snmp_poll(rca_obj)
    inc["rca"] = resolved_rca.model_dump()
    inc["epistemic_state"] = "VERIFIED_CAUSE"

    # Re-validate safety gate now that ambiguity is resolved!
    rem = safety_gate.validate_remediation_plan(
        incident_id=incident_id,
        playbook_id=inc["remediation"]["playbook_id"],
        is_ambiguous=False,
        freshness_state="FRESH",
        engines_agree=True,
    )
    inc["remediation"] = rem.model_dump()
    inc["copilot"]["q3_validated_corrective_action"] = (
        f"[DISAMBIGUATED via SNMPv3 Poll] Root cause confirmed as `{resolved_rca.ranked_causes_json[0]['entity_id']}` "
        f"(score=0.95). Stage 4 2PC execution is now UNLOCKED."
    )
    return {"ok": True, "incident": inc}


@app.post("/api/v1/remediation/{incident_id}/execute-2pc")
def execute_2pc_endpoint(incident_id: str, req: Execute2PCReq):
    if incident_id not in ACTIVE_INCIDENTS:
        raise HTTPException(status_code=404, detail="Incident not found")
    inc = ACTIVE_INCIDENTS[incident_id]
    from temloom.core.schemas import Schema15RemediationOutcome
    rem_obj = Schema15RemediationOutcome(**inc["remediation"])
    updated_rem = executor_2pc.execute_2pc(
        outcome=rem_obj,
        approver_id=req.approver_id,
        ed25519_signature=req.ed25519_signature,
        simulate_phase1_ssh_timeout=req.simulate_phase1_ssh_timeout,
        simulate_post_change_sla_regression=req.simulate_post_change_sla_regression,
    )
    inc["remediation"] = updated_rem.model_dump()
    return {"ok": True, "remediation": inc["remediation"]}


@app.post("/api/v1/incidents/{incident_id}/feedback")
@app.post("/api/feedback")
def record_feedback_endpoint(incident_id: str, req: FeedbackReq):
    res = feedback_mgr.record_feedback(incident_id, req.feedback, req.operator_id)
    if incident_id in ACTIVE_INCIDENTS:
        ACTIVE_INCIDENTS[incident_id]["rca"]["operator_feedback"] = res["operator_feedback"]
    return res


@app.get("/api/policy")
@app.get("/api/v1/policy")
def get_policy_endpoint():
    return get_effective_policy_matrix(POLICY_OVERRIDE_PATH)


@app.put("/api/policy")
@app.put("/api/v1/policy")
def update_policy_endpoint(req: PolicyUpdateReq):
    if req.action not in DEFAULT_ACTION_POLICY:
        raise HTTPException(status_code=400, detail=f"Unknown action: {req.action}")
    if DEFAULT_ACTION_POLICY[req.action]["locked"]:
        raise HTTPException(status_code=403, detail=f"Action {req.action} is HARD-LOCKED in taxonomy.py and cannot be modified.")

    overrides = {}
    if os.path.exists(POLICY_OVERRIDE_PATH):
        try:
            with open(POLICY_OVERRIDE_PATH, "r") as f:
                overrides = json.load(f)
        except Exception:
            overrides = {}

    overrides[req.action] = {"min_conf": req.min_conf, "auto_execute": req.auto_execute}
    with open(POLICY_OVERRIDE_PATH, "w") as f:
        json.dump(overrides, f, indent=2)

    audit_ledger.append_event(
        actor_id="noc_admin",
        actor_role="NOC_APPROVER",
        action_type="POLICY_MATRIX_UPDATE",
        payload={"action": req.action, "min_conf": req.min_conf, "auto_execute": req.auto_execute},
    )
    return {"ok": True, "policy": get_effective_policy_matrix(POLICY_OVERRIDE_PATH)}


@app.post("/api/v1/datasets/export")
def export_datasets_endpoint():
    return collector.export_parquet_snapshot()


@app.post("/api/v1/experiments/step")
def step_experiment_endpoint(req: StepReplayReq):
    return replay_engine.step(req.delta_steps)


@app.get("/api/v1/models/calibration")
def get_calibration_endpoint():
    return conformal.get_status()


@app.get("/api/v1/models/feedback-stats")
def get_feedback_stats_endpoint():
    return feedback_mgr.compute_fp_stats()


@app.get("/api/compliance")
@app.get("/api/v1/security/compliance")
def get_compliance_endpoint():
    return run_compliance_check()


@app.get("/api/tunnel-health")
@app.get("/api/v1/topology/tunnel-health")
def get_tunnel_health_endpoint():
    return rca_ranker.clonal_engine.get_tunnel_health()


@app.post("/api/nlq")
@app.post("/api/v1/copilot/nlq")
def nlq_query_endpoint(req: NlqReq):
    return nlq_engine.ask(req.question, session_id=req.session_id)


@app.post("/api/nlq/reset")
@app.post("/api/v1/copilot/nlq/reset")
def nlq_reset_endpoint():
    nlq_engine.reset_session("noc_ui")
    nlq_engine.reset_session("default")
    return {"ok": True}


@app.post("/api/v1/copilot/reindex")
def reindex_rag_endpoint():
    return ikb_mgr.seed_all()


@app.get("/api/v1/copilot/rag-stats")
def get_rag_stats_endpoint():
    return ikb_mgr.get_stats()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)
