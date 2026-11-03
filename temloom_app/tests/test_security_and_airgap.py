#!/usr/bin/env python3
from temloom.security.model_integrity import verify_all_models
from temloom.security.airgap_compliance import run_compliance_check, verify_compliance_report
from temloom.security.audit_ledger import TamperEvidentAuditLedger


def test_ed25519_model_signatures_and_airgap_attestation():
    res = verify_all_models()
    assert all(status == "OK" for status in res.values())

    rep = run_compliance_check()
    assert rep["status"] == "COMPLIANT"
    assert all(p["reachable"] is False for p in rep["probes"])
    assert verify_compliance_report(rep) is True


def test_anti_leakage_db_roles_and_sha256_audit_chain(temp_db):
    # Feature extractor role is strictly blocked from reading ground-truth tables
    try:
        temp_db.execute_query("SELECT * FROM injected_fault_records", role="feature_extractor")
        assert False
    except PermissionError:
        pass
    try:
        temp_db.execute_query("SELECT * FROM ground_truth_incident_labels", role="feature_extractor")
        assert False
    except PermissionError:
        pass

    # Copilot role is strictly blocked from mutating tables
    try:
        temp_db.execute_query("DELETE FROM rag_knowledge_chunks", role="temloom_copilot_ro")
        assert False
    except PermissionError:
        pass

    # SHA-256 hash chain verification
    ledger = TamperEvidentAuditLedger(temp_db)
    ledger.append_event("op1", "NOC_OPERATOR", "TEST_EVENT_1", {"a": 1})
    ledger.append_event("op2", "NOC_APPROVER", "TEST_EVENT_2", {"b": 2})
    ok, count, msg = ledger.verify_chain()
    assert ok is True and count == 2 and msg == "OK"
