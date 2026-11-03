#!/usr/bin/env python3
from temloom.remediation.safety_engine import DeterministicFourStageSafetyGate
from temloom.remediation.executor_2pc import TwoPhaseCommitExecutor


def test_4stage_safety_toctou_lease_and_2pc_rollback(temp_db):
    gate = DeterministicFourStageSafetyGate(temp_db)
    executor = TwoPhaseCommitExecutor(temp_db)

    # 1. Disallowed shell metacharacter command blocked at Stage 1 AST
    bad_ast = gate.validate_remediation_plan(
        incident_id="inc-ast",
        playbook_id="PB-STEER-BULK-AF21",
        custom_commands=["vtysh -c 'show ip bgp'; rm -rf /"],
    )
    assert bad_ast.stage1_ast_pass is False
    assert bad_ast.twophase_commit_state == "BLOCKED_SAFETY"

    # 2. Ambiguous root cause blocked at Stage 4
    ambig_plan = gate.validate_remediation_plan(
        incident_id="inc-amb",
        playbook_id="PB-STEER-BULK-AF21",
        is_ambiguous=True,
    )
    assert ambig_plan.twophase_commit_state == "BLOCKED_SAFETY"

    # 3. Concurrent TOCTOU Bandwidth Lease (Scenario F):
    # Backup tunnel starts at 18 Mbps / 100 Mbps.
    # Incident 1 reserves +32 Mbps -> 50.0% <= 80.0% (PASS)
    plan1 = gate.validate_remediation_plan(
        incident_id="inc-lease-1",
        playbook_id="PB-STEER-BULK-AF21",
        current_backup_load_mbps=18.0,
        diverted_traffic_mbps=32.0,
        backup_capacity_mbps=100.0,
    )
    assert plan1.twophase_commit_state == "AWAITING_APPROVAL"
    assert plan1.projected_backup_pct == 50.0

    # Incident 2 simultaneously requests +35 Mbps on the same backup path -> 18 + 32 + 35 = 85.0% > 80.0% (BLOCKED!)
    plan2 = gate.validate_remediation_plan(
        incident_id="inc-lease-2",
        playbook_id="PB-STEER-BULK-AF21",
        current_backup_load_mbps=18.0,
        diverted_traffic_mbps=35.0,
        backup_capacity_mbps=100.0,
    )
    assert plan2.twophase_commit_state == "BLOCKED_SAFETY"
    assert plan2.projected_backup_pct == 85.0

    # 4. 2PC Phase 1 SSH Timeout -> ABORTED_PHASE1 with 0.0s asymmetry
    plan_abort = gate.validate_remediation_plan(
        incident_id="inc-abort",
        playbook_id="PB-BGP-LOCALPREF",
        current_backup_load_mbps=18.0,
        diverted_traffic_mbps=10.0,
    )
    res_abort = executor.execute_2pc(plan_abort, approver_id="noc_lead", simulate_phase1_ssh_timeout=True)
    assert res_abort.twophase_commit_state == "ABORTED_PHASE1"
    assert "discard-changes" in res_abort.execution_stdout_log

    # 5. 2PC Phase 2 Post-Change SLA Regression -> AUTO_ROLLED_BACK
    plan_rb = gate.validate_remediation_plan(
        incident_id="inc-rb",
        playbook_id="PB-BGP-LOCALPREF",
        current_backup_load_mbps=18.0,
        diverted_traffic_mbps=10.0,
    )
    res_rb = executor.execute_2pc(plan_rb, approver_id="noc_lead", simulate_post_change_sla_regression=True)
    assert res_rb.twophase_commit_state == "AUTO_ROLLED_BACK"
    assert "REVERTED_OK" in res_rb.execution_stdout_log

    # 6. Normal 2PC Execution -> CONFIRMED_OUTCOME
    res_ok = executor.execute_2pc(plan1, approver_id="noc_lead")
    assert res_ok.twophase_commit_state == "CONFIRMED_OUTCOME"
    assert res_ok.post_change_rtt_ms <= 25.0
