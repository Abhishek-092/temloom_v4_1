-- 001_init_temloom_v4_1.sql
-- Authoritative PostgreSQL 16 (pgvector + tsvector) & SQLite Compatible DDL for Schemas 1-15

CREATE TABLE IF NOT EXISTS interface_telemetry (
    bucket_15s_utc_ms BIGINT NOT NULL,
    observed_at_utc_ms BIGINT NOT NULL,
    entity_canonical_id VARCHAR(96) NOT NULL,
    capacity_mbps DOUBLE PRECISION NOT NULL,
    utilization_mbps DOUBLE PRECISION,
    utilization_pct DOUBLE PRECISION,
    in_octets_delta BIGINT,
    out_octets_delta BIGINT,
    in_ucast_pkts_delta BIGINT,
    out_ucast_pkts_delta BIGINT,
    in_errors_delta INTEGER,
    out_errors_delta INTEGER,
    in_discards_delta INTEGER,
    out_discards_delta INTEGER,
    cpu_load_pct DOUBLE PRECISION,
    mem_used_pct DOUBLE PRECISION,
    optical_rx_dbm DOUBLE PRECISION,
    oper_status VARCHAR(16) NOT NULL,
    is_missing BOOLEAN NOT NULL DEFAULT FALSE,
    freshness_state VARCHAR(24) NOT NULL DEFAULT 'FRESH',
    PRIMARY KEY (bucket_15s_utc_ms, entity_canonical_id)
);

CREATE TABLE IF NOT EXISTS latency_jitter_telemetry (
    bucket_15s_utc_ms BIGINT NOT NULL,
    observed_at_utc_ms BIGINT NOT NULL,
    entity_canonical_id VARCHAR(96) NOT NULL,
    rtt_mean_ms DOUBLE PRECISION,
    rtt_p95_ms DOUBLE PRECISION,
    jitter_mean_ms DOUBLE PRECISION,
    bfd_echo_var_ms2 DOUBLE PRECISION,
    packet_loss_pct DOUBLE PRECISION,
    is_missing BOOLEAN NOT NULL DEFAULT FALSE,
    freshness_state VARCHAR(24) NOT NULL DEFAULT 'FRESH',
    PRIMARY KEY (bucket_15s_utc_ms, entity_canonical_id)
);

CREATE TABLE IF NOT EXISTS qos_queue_telemetry (
    bucket_15s_utc_ms BIGINT NOT NULL,
    entity_canonical_id VARCHAR(96) NOT NULL,
    dscp_class VARCHAR(16) NOT NULL,
    service_sla_tag VARCHAR(24) NOT NULL DEFAULT 'default',
    queue_depth_pkts INTEGER,
    queue_limit_pkts INTEGER NOT NULL,
    queue_drops_pps DOUBLE PRECISION,
    tx_rate_mbps DOUBLE PRECISION,
    traffic_share_ratio DOUBLE PRECISION,
    is_missing BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (bucket_15s_utc_ms, entity_canonical_id, dscp_class)
);

CREATE TABLE IF NOT EXISTS bgp_protocol_events (
    event_uuid VARCHAR(64) PRIMARY KEY,
    observed_at_utc_ms BIGINT NOT NULL,
    bucket_15s_utc_ms BIGINT NOT NULL,
    entity_canonical_id VARCHAR(96) NOT NULL,
    peer_asn INTEGER NOT NULL,
    vrf_name VARCHAR(32) NOT NULL,
    event_subtype VARCHAR(32) NOT NULL,
    updates_count_15s INTEGER NOT NULL,
    withdraws_count_15s INTEGER NOT NULL,
    rfc2439_flap_penalty DOUBLE PRECISION NOT NULL,
    hawkes_intensity DOUBLE PRECISION NOT NULL
);

CREATE TABLE IF NOT EXISTS ospf_protocol_events (
    event_uuid VARCHAR(64) PRIMARY KEY,
    observed_at_utc_ms BIGINT NOT NULL,
    bucket_15s_utc_ms BIGINT NOT NULL,
    entity_canonical_id VARCHAR(96) NOT NULL,
    ospf_area VARCHAR(24) NOT NULL,
    adj_state VARCHAR(24) NOT NULL,
    lsa_updates_15s INTEGER NOT NULL,
    spf_runs_15s INTEGER NOT NULL,
    convergence_time_ms DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS syslog_events (
    syslog_uuid VARCHAR(64) PRIMARY KEY,
    observed_at_utc_ms BIGINT NOT NULL,
    bucket_15s_utc_ms BIGINT NOT NULL,
    entity_canonical_id VARCHAR(96) NOT NULL,
    facility_program VARCHAR(32) NOT NULL,
    severity_level INTEGER NOT NULL,
    mnemonic_code VARCHAR(48) NOT NULL,
    sanitized_message TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS netflow_ipfix_records (
    flow_record_id VARCHAR(64) PRIMARY KEY,
    bucket_15s_utc_ms BIGINT NOT NULL,
    entity_canonical_id VARCHAR(96) NOT NULL,
    src_subnet_prefix VARCHAR(32) NOT NULL,
    dst_subnet_prefix VARCHAR(32) NOT NULL,
    ip_protocol INTEGER NOT NULL,
    dscp_value INTEGER NOT NULL,
    app_class VARCHAR(32) NOT NULL,
    service_sla_tag VARCHAR(24) NOT NULL DEFAULT 'default',
    direction VARCHAR(16) NOT NULL,
    bytes_delta BIGINT NOT NULL,
    packets_delta BIGINT NOT NULL,
    flow_duration_ms INTEGER NOT NULL,
    path_asymmetry_ratio DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS ipsec_tunnel_telemetry (
    bucket_15s_utc_ms BIGINT NOT NULL,
    entity_canonical_id VARCHAR(96) NOT NULL,
    underlay_path_id VARCHAR(96) NOT NULL,
    tunnel_state VARCHAR(24) NOT NULL,
    lsp_health_score DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    availability_pct DOUBLE PRECISION,
    tunnel_rtt_ms DOUBLE PRECISION,
    tunnel_jitter_ms DOUBLE PRECISION,
    esp_seq_loss_pct DOUBLE PRECISION,
    replay_drops_pps DOUBLE PRECISION,
    ike_rekey_lat_ms DOUBLE PRECISION,
    ike_dh_retries INTEGER,
    sa_rem_life_min DOUBLE PRECISION,
    is_missing BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (bucket_15s_utc_ms, entity_canonical_id)
);

CREATE TABLE IF NOT EXISTS sdwan_controller_events (
    event_uuid VARCHAR(64) PRIMARY KEY,
    bucket_15s_utc_ms BIGINT NOT NULL,
    entity_canonical_id VARCHAR(96) NOT NULL,
    adapter_driver VARCHAR(32) NOT NULL,
    controller_health VARCHAR(16) NOT NULL,
    connected_sites_cnt INTEGER NOT NULL,
    aar_policy_name VARCHAR(64) NOT NULL,
    selected_tunnel_id VARCHAR(96) NOT NULL,
    aar_decision_reason VARCHAR(64) NOT NULL,
    policy_drift_detected BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS config_policy_changes (
    change_id VARCHAR(64) PRIMARY KEY,
    observed_at_utc_ms BIGINT NOT NULL,
    bucket_15s_utc_ms BIGINT NOT NULL,
    entity_canonical_id VARCHAR(96) NOT NULL,
    actor_identity VARCHAR(64) NOT NULL,
    golden_config_sha256 CHAR(64) NOT NULL,
    active_config_sha256 CHAR(64) NOT NULL,
    is_unintended_drift BOOLEAN NOT NULL DEFAULT FALSE,
    unified_diff_text TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS injected_fault_records (
    fault_id VARCHAR(64) PRIMARY KEY,
    experiment_id VARCHAR(64) NOT NULL,
    scenario_id VARCHAR(64) NOT NULL,
    random_seed INTEGER NOT NULL,
    fault_category VARCHAR(32) NOT NULL,
    affected_entity_id VARCHAR(96) NOT NULL,
    related_entities_json TEXT NOT NULL,
    start_utc_ms BIGINT NOT NULL,
    end_utc_ms BIGINT NOT NULL,
    fault_severity VARCHAR(16) NOT NULL,
    fault_parameters TEXT NOT NULL,
    injection_succeeded BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS ground_truth_incident_labels (
    gt_incident_id VARCHAR(64) PRIMARY KEY,
    fault_id VARCHAR(64) NOT NULL,
    expects_sla_breach BOOLEAN NOT NULL,
    sla_breach_occurred BOOLEAN NOT NULL,
    sla_breach_onset_ms BIGINT,
    recovery_utc_ms BIGINT,
    expected_impact_json TEXT NOT NULL,
    actual_impact_json TEXT NOT NULL,
    detected_by_system BOOLEAN NOT NULL DEFAULT FALSE,
    predicted_before_sla BOOLEAN NOT NULL DEFAULT FALSE,
    realized_lead_min DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS prediction_outputs (
    prediction_id VARCHAR(64) PRIMARY KEY,
    bucket_15s_utc_ms BIGINT NOT NULL,
    entity_canonical_id VARCHAR(96) NOT NULL,
    issue_category VARCHAR(32) NOT NULL,
    prediction_horizon_m DOUBLE PRECISION NOT NULL,
    estimated_tti_min DOUBLE PRECISION,
    model_anomaly_score DOUBLE PRECISION NOT NULL,
    digital_twin_divergence DOUBLE PRECISION,
    engines_agree BOOLEAN NOT NULL DEFAULT TRUE,
    conformal_alpha DOUBLE PRECISION NOT NULL DEFAULT 0.10,
    conformal_lo_bound DOUBLE PRECISION NOT NULL,
    conformal_hi_bound DOUBLE PRECISION NOT NULL,
    freshness_confidence DOUBLE PRECISION NOT NULL,
    contributing_features TEXT NOT NULL,
    model_identifier VARCHAR(48) NOT NULL,
    model_version_id VARCHAR(64) NOT NULL,
    linked_incident_id VARCHAR(64)
);

CREATE TABLE IF NOT EXISTS rca_outputs (
    rca_output_id VARCHAR(64) PRIMARY KEY,
    incident_id VARCHAR(64) NOT NULL,
    bucket_15s_utc_ms BIGINT NOT NULL,
    epistemic_rca_state VARCHAR(32) NOT NULL,
    is_ambiguous BOOLEAN NOT NULL DEFAULT FALSE,
    ranked_causes_json TEXT NOT NULL,
    clonal_search_scores TEXT NOT NULL,
    affected_services TEXT NOT NULL,
    priority_score DOUBLE PRECISION NOT NULL,
    operator_feedback VARCHAR(16) NOT NULL DEFAULT 'PENDING',
    disambiguation_action VARCHAR(128)
);

CREATE TABLE IF NOT EXISTS remediation_outcomes (
    remediation_id VARCHAR(64) PRIMARY KEY,
    incident_id VARCHAR(64) NOT NULL,
    playbook_id VARCHAR(32) NOT NULL,
    autonomy_execution_mode VARCHAR(24) NOT NULL DEFAULT 'RECOMMEND_ONLY',
    stage1_ast_pass BOOLEAN NOT NULL,
    stage2_lease_id VARCHAR(64),
    projected_backup_pct DOUBLE PRECISION NOT NULL,
    stage3_mm1k_rtt_ms DOUBLE PRECISION NOT NULL,
    stage3_batfish_pass BOOLEAN NOT NULL,
    ed25519_approver_id VARCHAR(64),
    ed25519_signature VARCHAR(160),
    twophase_commit_state VARCHAR(32) NOT NULL,
    execution_stdout_log TEXT,
    post_change_rtt_ms DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS bandwidth_reservation_leases (
    lease_id VARCHAR(64) PRIMARY KEY,
    target_path_id VARCHAR(96) NOT NULL,
    incident_id VARCHAR(64) NOT NULL,
    reserved_mbps DOUBLE PRECISION NOT NULL,
    created_at_utc_ms BIGINT NOT NULL,
    expires_at_utc_ms BIGINT NOT NULL,
    lease_state VARCHAR(24) NOT NULL DEFAULT 'ACTIVE'
);

CREATE TABLE IF NOT EXISTS rag_knowledge_chunks (
    chunk_id VARCHAR(96) PRIMARY KEY,
    collection_type VARCHAR(32) NOT NULL DEFAULT 'runbook',
    doc_title VARCHAR(128) NOT NULL,
    category VARCHAR(32) NOT NULL,
    protocol_tags TEXT NOT NULL,
    sanitized_text TEXT NOT NULL,
    embedding_json TEXT NOT NULL,
    sha256_hash CHAR(64) NOT NULL,
    indexed_at_utc_ms BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log_chain (
    seq_id INTEGER PRIMARY KEY AUTOINCREMENT,
    logged_at_utc_ms BIGINT NOT NULL,
    actor_id VARCHAR(64) NOT NULL,
    actor_role VARCHAR(32) NOT NULL,
    action_type VARCHAR(48) NOT NULL,
    payload_json TEXT NOT NULL,
    prev_hash CHAR(64) NOT NULL,
    entry_hash CHAR(64) NOT NULL
);

CREATE TABLE IF NOT EXISTS telemetry_quarantine_dlq (
    dlq_id VARCHAR(64) PRIMARY KEY,
    observed_at_utc_ms BIGINT NOT NULL,
    source_type VARCHAR(32) NOT NULL,
    rejection_reason VARCHAR(128) NOT NULL,
    raw_payload TEXT NOT NULL
);
