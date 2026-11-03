#!/usr/bin/env python3
from fastapi.testclient import TestClient
from temloom.api_ui.app import app

client = TestClient(app)


def test_end_to_end_fastapi_workbenches_and_scenarios():
    # 1. Serve 5-Workbench Console HTML
    r_html = client.get("/")
    assert r_html.status_code == 200
    assert "TEMLOOM v4.1" in r_html.text

    # 2. System Status & Bootstrap
    r_boot = client.get("/api/v1/bootstrap")
    assert r_boot.status_code == 200
    boot = r_boot.json()
    assert len(boot["incidents"]) >= 1
    assert len(boot["model_zoo"]) >= 8

    # 3. Inject Scenario E (SRLG Ambiguity) -> Verify blocked until SNMPv3 disambiguation
    r_amb = client.post("/api/v1/sim/inject", json={"fault_type": "srlg_ambiguity"})
    assert r_amb.status_code == 200
    inc_amb = r_amb.json()["incident"]
    assert inc_amb["rca"]["is_ambiguous"] is True
    assert inc_amb["remediation"]["twophase_commit_state"] == "BLOCKED_SAFETY"

    # Disambiguate via out-of-band SNMPv3 poll -> Unlocks Stage 4
    r_dis = client.post(f"/api/v1/rca/{inc_amb['incident_id']}/disambiguate")
    assert r_dis.status_code == 200
    inc_res = r_dis.json()["incident"]
    assert inc_res["rca"]["is_ambiguous"] is False
    assert inc_res["remediation"]["twophase_commit_state"] == "AWAITING_APPROVAL"

    # Execute 2PC Commit -> CONFIRMED_OUTCOME
    r_2pc = client.post(
        f"/api/v1/remediation/{inc_amb['incident_id']}/execute-2pc",
        json={"approver_id": "noc_lead_sharma"},
    )
    assert r_2pc.status_code == 200
    assert r_2pc.json()["remediation"]["twophase_commit_state"] == "CONFIRMED_OUTCOME"

    # 4. Operator Feedback Loop -> ACCEPTED syncs to IKB
    r_fb = client.post(
        f"/api/v1/incidents/{inc_amb['incident_id']}/feedback",
        json={"feedback": "ACCEPTED"},
    )
    assert r_fb.status_code == 200
    assert r_fb.json()["operator_feedback"] == "ACCEPTED"

    # 5. Hard-Locked Autonomy Policy Matrix check
    r_pol_locked = client.put(
        "/api/v1/policy",
        json={"action": "CORE_PATH_FAILOVER", "min_conf": 0.50, "auto_execute": True},
    )
    assert r_pol_locked.status_code == 403

    r_pol_ok = client.put(
        "/api/v1/policy",
        json={"action": "REROUTE_BRANCH", "min_conf": 0.82, "auto_execute": True},
    )
    assert r_pol_ok.status_code == 200

    # 6. Multi-Turn NLQ Copilot & Parquet Export
    r_nlq = client.post("/api/v1/copilot/nlq", json={"question": "How do I fix BGP flap on pe1?"})
    assert r_nlq.status_code == 200
    assert "RB-102" in r_nlq.json()["answer"]

    r_exp = client.post("/api/v1/datasets/export")
    assert r_exp.status_code == 200
    assert "dataset_version_id" in r_exp.json()
