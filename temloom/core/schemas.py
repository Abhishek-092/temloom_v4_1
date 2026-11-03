#!/usr/bin/env python3
"""
temloom/core/schemas.py — Canonical Pydantic v2 Data Contracts for All 15 Schemas
(Document 2, Section 1.3: Schemas 1..15) + AnomalyContextPacket (ACP) Bridge.
"""

from typing import Optional, List, Dict, Any, Literal
from datetime import datetime, timezone
import uuid
import json
from pydantic import BaseModel as _PydanticBaseModel, Field
try:
    from pydantic import field_validator
    HAS_PYDANTIC_V2 = True
except ImportError:
    from pydantic import validator as field_validator
    HAS_PYDANTIC_V2 = False

class BaseModel(_PydanticBaseModel):
    def model_dump(self, *args, **kwargs):
        if hasattr(super(), "model_dump"):
            return super().model_dump(*args, **kwargs)
        return self.dict(*args, **kwargs)



class Schema1InterfaceTelemetry(BaseModel):
    bucket_15s_utc_ms: int
    observed_at_utc_ms: int
    entity_canonical_id: str
    capacity_mbps: float = Field(gt=0.0)
    utilization_mbps: Optional[float] = None
    utilization_pct: Optional[float] = None
    in_octets_delta: Optional[int] = Field(default=0, ge=0)
    out_octets_delta: Optional[int] = Field(default=0, ge=0)
    in_ucast_pkts_delta: Optional[int] = Field(default=0, ge=0)
    out_ucast_pkts_delta: Optional[int] = Field(default=0, ge=0)
    in_errors_delta: Optional[int] = Field(default=0, ge=0)
    out_errors_delta: Optional[int] = Field(default=0, ge=0)
    in_discards_delta: Optional[int] = Field(default=0, ge=0)
    out_discards_delta: Optional[int] = Field(default=0, ge=0)
    cpu_load_pct: Optional[float] = Field(default=25.0, ge=0.0, le=100.0)
    mem_used_pct: Optional[float] = Field(default=42.0, ge=0.0, le=100.0)
    optical_rx_dbm: Optional[float] = Field(default=-6.5, ge=-40.0, le=5.0)
    oper_status: Literal["UP", "DOWN", "TESTING", "UNKNOWN"] = "UP"
    is_missing: bool = False
    freshness_state: Literal["FRESH", "DEGRADED_POLLING", "STALE_TELEMETRY"] = "FRESH"

    @field_validator("bucket_15s_utc_ms")
    @classmethod
    def check_grid(cls, v: int) -> int:
        if v % 15000 != 0:
            raise ValueError("bucket_15s_utc_ms must be aligned to 15,000 ms grid")
        return v


class Schema2LatencyJitterTelemetry(BaseModel):
    bucket_15s_utc_ms: int
    observed_at_utc_ms: int
    entity_canonical_id: str
    rtt_mean_ms: Optional[float] = None
    rtt_p95_ms: Optional[float] = None
    jitter_mean_ms: Optional[float] = None
    bfd_echo_var_ms2: Optional[float] = 0.30
    packet_loss_pct: Optional[float] = Field(default=0.0, ge=0.0, le=100.0)
    is_missing: bool = False
    freshness_state: Literal["FRESH", "DEGRADED_POLLING", "STALE_TELEMETRY"] = "FRESH"


class Schema3QosQueueTelemetry(BaseModel):
    bucket_15s_utc_ms: int
    entity_canonical_id: str
    dscp_class: Literal["EF", "AF41", "AF21", "CS6", "BE"] = "EF"
    service_sla_tag: Literal["voip", "video", "database", "bulk", "default"] = "voip"
    queue_depth_pkts: Optional[int] = 0
    queue_limit_pkts: int = Field(default=64, gt=0)
    queue_drops_pps: Optional[float] = Field(default=0.0, ge=0.0)
    tx_rate_mbps: Optional[float] = Field(default=0.0, ge=0.0)
    traffic_share_ratio: Optional[float] = Field(default=0.25, ge=0.0, le=1.0)
    is_missing: bool = False


class Schema4BgpProtocolEvent(BaseModel):
    event_uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    observed_at_utc_ms: int
    bucket_15s_utc_ms: int
    entity_canonical_id: str
    peer_asn: int = Field(default=65000, ge=1, le=4294967295)
    vrf_name: str = "vrf-voice"
    event_subtype: Literal["ADJ_UP", "ADJ_DOWN", "ROUTE_UPDATE", "ROUTE_WITHDRAW", "FLAP_DAMPED"]
    updates_count_15s: int = Field(ge=0)
    withdraws_count_15s: int = Field(ge=0)
    rfc2439_flap_penalty: float = Field(ge=0.0)
    hawkes_intensity: float = Field(ge=0.0)


class Schema5OspfProtocolEvent(BaseModel):
    event_uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    observed_at_utc_ms: int
    bucket_15s_utc_ms: int
    entity_canonical_id: str
    ospf_area: str = "0.0.0.0"
    adj_state: Literal["FULL", "TWOWAY", "EXSTART", "INIT", "DOWN"] = "FULL"
    lsa_updates_15s: int = Field(ge=0)
    spf_runs_15s: int = Field(ge=0)
    convergence_time_ms: Optional[float] = 120.0


class Schema6SyslogEvent(BaseModel):
    syslog_uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    observed_at_utc_ms: int
    bucket_15s_utc_ms: int
    entity_canonical_id: str
    facility_program: str
    severity_level: int = Field(ge=0, le=7)
    mnemonic_code: str
    sanitized_message: str


class Schema7NetflowIpfixRecord(BaseModel):
    flow_record_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bucket_15s_utc_ms: int
    entity_canonical_id: str
    src_subnet_prefix: str
    dst_subnet_prefix: str
    ip_protocol: int = 17
    dscp_value: int = Field(ge=0, le=63)
    app_class: Literal["voip_rtp", "video_conf", "erp_sql", "bulk_backup", "best_effort"]
    service_sla_tag: Literal["voip", "video", "database", "bulk", "default"] = "voip"
    direction: Literal["FORWARD", "RETURN"] = "FORWARD"
    bytes_delta: int = Field(gt=0)
    packets_delta: int = Field(gt=0)
    flow_duration_ms: int = Field(default=15000, ge=0)
    path_asymmetry_ratio: Optional[float] = Field(default=0.04, ge=0.0, le=1.0)


class Schema8IpsecTunnelTelemetry(BaseModel):
    bucket_15s_utc_ms: int
    entity_canonical_id: str
    underlay_path_id: str
    tunnel_state: Literal["ESTABLISHED", "REKEYING", "DEGRADED", "DOWN"] = "ESTABLISHED"
    lsp_health_score: float = Field(default=1.0, ge=0.0, le=1.0)
    availability_pct: Optional[float] = Field(default=100.0, ge=0.0, le=100.0)
    tunnel_rtt_ms: Optional[float] = 14.0
    tunnel_jitter_ms: Optional[float] = 1.8
    esp_seq_loss_pct: Optional[float] = 0.04
    replay_drops_pps: Optional[float] = 0.2
    ike_rekey_lat_ms: Optional[float] = 45.0
    ike_dh_retries: Optional[int] = 0
    sa_rem_life_min: Optional[float] = 30.0
    is_missing: bool = False


class Schema9SdwanControllerEvent(BaseModel):
    event_uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bucket_15s_utc_ms: int
    entity_canonical_id: str = "global:sdwan:controller:ctrl-1"
    adapter_driver: Literal["TEMLOOM_NATIVE", "CISCO_VMANAGE", "GENERIC_YANG"] = "TEMLOOM_NATIVE"
    controller_health: Literal["HEALTHY", "DEGRADED", "UNREACHABLE"] = "HEALTHY"
    connected_sites_cnt: int = Field(default=4, ge=0)
    aar_policy_name: str = "AAR-VOICE-GOLD"
    selected_tunnel_id: str = "br1:ce-br1:tunnel:tun-br1-mpls"
    aar_decision_reason: Literal["SLA_COMPLIANT", "JITTER_BREACH_FAILOVER", "MANUAL_PIN", "POLICY_DRIFT"] = "SLA_COMPLIANT"
    policy_drift_detected: bool = False


class Schema10ConfigPolicyChange(BaseModel):
    change_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    observed_at_utc_ms: int
    bucket_15s_utc_ms: int
    entity_canonical_id: str
    actor_identity: str
    golden_config_sha256: str
    active_config_sha256: str
    is_unintended_drift: bool = False
    unified_diff_text: str


class Schema11InjectedFaultRecord(BaseModel):
    fault_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    experiment_id: str
    scenario_id: str
    random_seed: int
    fault_category: Literal[
        "CONGESTION", "LATENCY_DRIFT", "QOS_DROP", "BGP_FLAP", "OSPF_STORM",
        "ASYMMETRY", "TUNNEL_REKEY", "POLICY_DRIFT", "SRLG_FAULT", "BENIGN_STRESS"
    ]
    affected_entity_id: str
    related_entities_json: List[str]
    start_utc_ms: int
    end_utc_ms: int
    fault_severity: Literal["NONE_BENIGN", "MODERATE", "SEVERE", "CRITICAL"]
    fault_parameters: Dict[str, Any]
    injection_succeeded: bool = True


class Schema12GroundTruthIncidentLabel(BaseModel):
    gt_incident_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    fault_id: str
    expects_sla_breach: bool
    sla_breach_occurred: bool
    sla_breach_onset_ms: Optional[int] = None
    recovery_utc_ms: Optional[int] = None
    expected_impact_json: Dict[str, Any]
    actual_impact_json: Dict[str, Any]
    detected_by_system: bool = False
    predicted_before_sla: bool = False
    realized_lead_min: Optional[float] = None


class Schema13PredictionOutput(BaseModel):
    prediction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bucket_15s_utc_ms: int
    entity_canonical_id: str
    issue_category: Literal[
        "LINK_CONGESTION", "LATENCY_DRIFT", "QOS_STARVATION", "BGP_FLAP_CASCADE",
        "OSPF_STORM", "PATH_ASYMMETRY", "TUNNEL_REKEY_EXHAUSTION",
        "ANTI_REPLAY_OVERFLOW", "POLICY_DRIFT", "NORMAL"
    ]
    prediction_horizon_m: float = 10.0
    estimated_tti_min: Optional[float] = None
    model_anomaly_score: float = Field(ge=0.0, le=1.0)
    digital_twin_divergence: Optional[float] = 0.0
    engines_agree: bool = True
    conformal_alpha: float = 0.10
    conformal_lo_bound: float
    conformal_hi_bound: float
    freshness_confidence: float = Field(ge=0.0, le=1.0)
    contributing_features: Dict[str, Any]
    model_identifier: str
    model_version_id: str
    linked_incident_id: Optional[str] = None


class Schema14RcaOutput(BaseModel):
    rca_output_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    incident_id: str
    bucket_15s_utc_ms: int
    epistemic_rca_state: Literal["SUSPECTED_CAUSE", "AMBIGUOUS_CAUSE_SET", "VERIFIED_CAUSE"]
    is_ambiguous: bool
    ranked_causes_json: List[Dict[str, Any]]
    clonal_search_scores: Dict[str, Any]
    affected_services: List[str]
    priority_score: float = Field(ge=0.0, le=100.0)
    operator_feedback: Literal["PENDING", "ACCEPTED", "REJECTED"] = "PENDING"
    disambiguation_action: Optional[str] = None


class Schema15RemediationOutcome(BaseModel):
    remediation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    incident_id: str
    playbook_id: str
    autonomy_execution_mode: Literal["RECOMMEND_ONLY", "PRE_VALIDATED_STAGED"] = "RECOMMEND_ONLY"
    stage1_ast_pass: bool
    stage2_lease_id: Optional[str] = None
    projected_backup_pct: float
    stage3_mm1k_rtt_ms: float
    stage3_batfish_pass: bool
    ed25519_approver_id: Optional[str] = None
    ed25519_signature: Optional[str] = None
    twophase_commit_state: Literal[
        "BLOCKED_SAFETY", "AWAITING_APPROVAL", "COMMITTED_2PC",
        "ABORTED_PHASE1", "AUTO_ROLLED_BACK", "CONFIRMED_OUTCOME"
    ]
    execution_stdout_log: Optional[str] = None
    post_change_rtt_ms: Optional[float] = None


class StructuredIncidentContext(BaseModel):
    """Unified Stage 6 Incident Context Packet (uniting Schemas 10, 13, 14, 15)."""
    incident_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bucket_15s_utc_ms: int
    timestamp_iso: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "HIGH"
    epistemic_state: str = "SUSPECTED_CAUSE"
    freshness_state: str = "FRESH"
    service_sla_tag: str = "voip"
    prediction: Schema13PredictionOutput
    rca: Schema14RcaOutput
    remediation: Optional[Schema15RemediationOutcome] = None
    mitigation_commands: List[str] = Field(default_factory=list)
    rollback_commands: List[str] = Field(default_factory=list)
