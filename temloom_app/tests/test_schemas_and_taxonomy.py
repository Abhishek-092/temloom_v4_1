#!/usr/bin/env python3
from temloom.core.taxonomy import FAULTS, DEFAULT_ACTION_POLICY, get_effective_policy_matrix
from temloom.core.schemas import (
    Schema1InterfaceTelemetry,
    Schema2LatencyJitterTelemetry,
    Schema3QosQueueTelemetry,
    Schema4BgpProtocolEvent,
    Schema5OspfProtocolEvent,
    Schema6SyslogEvent,
    Schema7NetflowIpfixRecord,
    Schema8IpsecTunnelTelemetry,
    Schema9SdwanControllerEvent,
    Schema10ConfigPolicyChange,
    Schema11InjectedFaultRecord,
    Schema12GroundTruthIncidentLabel,
    Schema13PredictionOutput,
    Schema14RcaOutput,
    Schema15RemediationOutcome,
)


def test_all_15_schemas_validate_cleanly():
    b_ms = 1793545200000
    s1 = Schema1InterfaceTelemetry(bucket_15s_utc_ms=b_ms, observed_at_utc_ms=b_ms - 500, entity_canonical_id="hub1:ce-hub1:iface:wan0", capacity_mbps=100.0, utilization_mbps=88.4)
    assert s1.bucket_15s_utc_ms == b_ms

    # Unaligned bucket must fail validation
    try:
        Schema1InterfaceTelemetry(bucket_15s_utc_ms=b_ms + 123, observed_at_utc_ms=b_ms, entity_canonical_id="hub1:ce-hub1:iface:wan0", capacity_mbps=100.0)
        assert False, 'Expected ValueError'
    except ValueError:
        pass

    s2 = Schema2LatencyJitterTelemetry(bucket_15s_utc_ms=b_ms, observed_at_utc_ms=b_ms, entity_canonical_id="core:mpls:link:mpls-link-mab-1", rtt_mean_ms=21.6)
    s3 = Schema3QosQueueTelemetry(bucket_15s_utc_ms=b_ms, entity_canonical_id="br1:ce-br1:qos_queue:eth0:EF", dscp_class="EF", service_sla_tag="voip", queue_drops_pps=14.8)
    s4 = Schema4BgpProtocolEvent(observed_at_utc_ms=b_ms, bucket_15s_utc_ms=b_ms, entity_canonical_id="br1:ce-br1:bgp_peer:10.255.0.2", event_subtype="ROUTE_WITHDRAW", updates_count_15s=6, withdraws_count_15s=3, rfc2439_flap_penalty=845.0, hawkes_intensity=2.64)
    s5 = Schema5OspfProtocolEvent(observed_at_utc_ms=b_ms, bucket_15s_utc_ms=b_ms, entity_canonical_id="br1:ce-br1:ospf_nbr:10.0.0.254", lsa_updates_15s=14, spf_runs_15s=2)
    s6 = Schema6SyslogEvent(observed_at_utc_ms=b_ms, bucket_15s_utc_ms=b_ms, entity_canonical_id="br1:ce-br1:system:syslog", facility_program="bgpd", severity_level=4, mnemonic_code="BGP-5-ADJCHANGE", sanitized_message="neighbor down")
    s7 = Schema7NetflowIpfixRecord(bucket_15s_utc_ms=b_ms, entity_canonical_id="br1:ce-br1:tunnel:tun-br1", src_subnet_prefix="10.10.1.0/24", dst_subnet_prefix="10.99.0.0/24", dscp_value=46, app_class="voip_rtp", service_sla_tag="voip", bytes_delta=10000, packets_delta=100)
    s8 = Schema8IpsecTunnelTelemetry(bucket_15s_utc_ms=b_ms, entity_canonical_id="br1:ce-br1:tunnel:tun-br1", underlay_path_id="core:mpls:srlg:transport-A-hub1", lsp_health_score=0.78)
    s9 = Schema9SdwanControllerEvent(bucket_15s_utc_ms=b_ms)
    s10 = Schema10ConfigPolicyChange(observed_at_utc_ms=b_ms, bucket_15s_utc_ms=b_ms, entity_canonical_id="global:sdwan:controller:ctrl-1", actor_identity="admin", golden_config_sha256="a"*64, active_config_sha256="b"*64, is_unintended_drift=True, unified_diff_text="diff")
    s11 = Schema11InjectedFaultRecord(experiment_id="EXP-1", scenario_id="Scen_A", random_seed=301, fault_category="CONGESTION", affected_entity_id="core:mpls:link:mpls-link-mab-1", related_entities_json=["br1:service:voip_rtp"], start_utc_ms=b_ms, end_utc_ms=b_ms+60000, fault_severity="CRITICAL", fault_parameters={"slope": 1.8})
    s12 = Schema12GroundTruthIncidentLabel(fault_id=s11.fault_id, expects_sla_breach=True, sla_breach_occurred=True, expected_impact_json={}, actual_impact_json={})
    s13 = Schema13PredictionOutput(bucket_15s_utc_ms=b_ms, entity_canonical_id="core:mpls:link:mpls-link-mab-1", issue_category="LINK_CONGESTION", estimated_tti_min=6.5, model_anomaly_score=0.89, digital_twin_divergence=0.34, engines_agree=True, conformal_lo_bound=79.8, conformal_hi_bound=102.0, freshness_confidence=0.98, contributing_features={"u": 88.4}, model_identifier="G1", model_version_id="v4.1")
    s14 = Schema14RcaOutput(incident_id="inc-1", bucket_15s_utc_ms=b_ms, epistemic_rca_state="SUSPECTED_CAUSE", is_ambiguous=False, ranked_causes_json=[{"entity_id": "core:mpls:link:mpls-link-mab-1", "score": 0.91}], clonal_search_scores={"winner": "CLONE_REROUTED_OVERLAY"}, affected_services=["br1:service:voip_rtp"], priority_score=86.5)
    s15 = Schema15RemediationOutcome(incident_id="inc-1", playbook_id="PB-STEER-BULK-AF21", stage1_ast_pass=True, projected_backup_pct=46.0, stage3_mm1k_rtt_ms=11.4, stage3_batfish_pass=True, twophase_commit_state="CONFIRMED_OUTCOME")
    assert all([s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14, s15])


def test_taxonomy_hard_locked_autonomy_floors():
    assert len(FAULTS) == 7
    matrix = get_effective_policy_matrix()
    assert matrix["CORE_PATH_FAILOVER"]["locked"] is True
    assert matrix["CORE_PATH_FAILOVER"]["auto_execute"] is False
    assert matrix["NODE_ISOLATION"]["locked"] is True
    assert matrix["CONTROLLER_POLICY_ROLLBACK"]["locked"] is True
