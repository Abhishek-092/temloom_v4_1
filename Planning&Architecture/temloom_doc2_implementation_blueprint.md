# DOCUMENT 2: TEMLOOM — Complete Engineering Implementation Blueprint

**Project Name:** TEMLOOM  
**Document ID:** `TEMLOOM-IMPL-BLUEPRINT-v4.1`  
**Companion Volumes:** `Document 1 (System Architecture v4.1)`, `Document 3 (Experimental Validation Plan v4.1)`, `Document 4 (Requirements Traceability Matrix v4.1)`, `Document 5 (GUI Overview & Interface Specification v4.1)`, `Comparative Review & Changelog (temloom_aether_review_and_changelog.md)`

---

## 1. Fifteen Concrete Dataset & Telemetry Schemas (Section 1.3)

Every record ingested, generated, or emitted by TEMLOOM conforms to one of the **15 strict schemas** below (governed by canonical enums in `temloom/core/taxonomy.py`). Across all 15 schemas:
- **Timestamp Semantics:** `observed_at_utc_ms` (64-bit integer UTC epoch milliseconds when sampled/emitted) and `bucket_15s_utc_ms` (64-bit integer 15,000 ms grid ceiling used for causal point-in-time joins over $(t - 15\text{s}, t]$).
- **Entity Identifier Format:** `entity_canonical_id` formatted as `site_id:device_id:layer:sub_entity` (e.g., `br1:ce-br1:iface:eth0`, `br1:ce-br1:tunnel:tun-br1`, `global:sdwan:controller:ctrl-1`).
- **Explicit Missingness Rule:** Unavailable measurements are stored as `NULL` with `is_missing = true` and `freshness_state IN ('FRESH', 'DEGRADED_POLLING', 'STALE_TELEMETRY')`—never silently interpolated or zero-filled.

### Schema 1: Interface Telemetry (`interface_telemetry` — Source: SNMPv3 IF-MIB / Entity-MIB, 15s Poll)
| Field Name | Data Type | Units | Req / Nullable | Validation Rule |
| :--- | :--- | :--- | :---: | :--- |
| `bucket_15s_utc_ms` | `BIGINT` | `ms (UTC)` | Req / `NOT NULL` | `bucket_15s_utc_ms % 15000 == 0` |
| `observed_at_utc_ms` | `BIGINT` | `ms (UTC)` | Req / `NOT NULL` | `observed_at_utc_ms <= bucket_15s_utc_ms` |
| `entity_canonical_id` | `VARCHAR(96)` | ID | Req / `NOT NULL` | Regex `^[a-z0-9\-]+:[a-z0-9\-]+:iface:[a-z0-9\-\./]+$` |
| `capacity_mbps` | `DOUBLE PRECISION` | `Mbps` | Req / `NOT NULL` | `> 0.0` |
| `utilization_mbps` | `DOUBLE PRECISION` | `Mbps` | Opt / `NULLABLE` | `0.0 <= val <= capacity_mbps * 1.05` (`NULL` if poll missed) |
| `utilization_pct` | `DOUBLE PRECISION` | `%` | Opt / `NULLABLE` | `0.0 <= val <= 105.0` |
| `in_octets_delta` | `BIGINT` | `bytes` | Opt / `NULLABLE` | `>= 0` (monotonic wrap-corrected via $2^{64}$) |
| `out_octets_delta` | `BIGINT` | `bytes` | Opt / `NULLABLE` | `>= 0` |
| `in_ucast_pkts_delta` | `BIGINT` | `packets` | Opt / `NULLABLE` | `>= 0` |
| `out_ucast_pkts_delta`| `BIGINT` | `packets` | Opt / `NULLABLE` | `>= 0` |
| `in_errors_delta` | `INTEGER` | `errors` | Opt / `NULLABLE` | `>= 0` (`ifInErrors`) |
| `out_errors_delta` | `INTEGER` | `errors` | Opt / `NULLABLE` | `>= 0` (`ifOutErrors`) |
| `in_discards_delta` | `INTEGER` | `packets` | Opt / `NULLABLE` | `>= 0` (`ifInDiscards`) |
| `out_discards_delta` | `INTEGER` | `packets` | Opt / `NULLABLE` | `>= 0` (`ifOutDiscards`) |
| `cpu_load_pct` | `DOUBLE PRECISION` | `%` | Opt / `NULLABLE` | `0.0 <= val <= 100.0` |
| `mem_used_pct` | `DOUBLE PRECISION` | `%` | Opt / `NULLABLE` | `0.0 <= val <= 100.0` |
| `optical_rx_dbm` | `DOUBLE PRECISION` | `dBm` | Opt / `NULLABLE` | `-40.0 <= val <= 5.0` |
| `oper_status` | `VARCHAR(16)` | Enum | Req / `NOT NULL` | `IN ('UP', 'DOWN', 'TESTING', 'UNKNOWN')` |
| `is_missing` | `BOOLEAN` | Flag | Req / `NOT NULL` | `true` when SNMPv3 poll timed out |
| `freshness_state` | `VARCHAR(24)` | Enum | Req / `NOT NULL` | `IN ('FRESH', 'DEGRADED_POLLING', 'STALE_TELEMETRY')` |

- **Representative Record (`Schema 1`):**
```json
{"bucket_15s_utc_ms": 1793545200000, "observed_at_utc_ms": 1793545198420, "entity_canonical_id": "hub1:ce-hub1:iface:wan0", "capacity_mbps": 100.0, "utilization_mbps": 88.4, "utilization_pct": 88.4, "in_octets_delta": 165750000, "out_octets_delta": 165750000, "in_ucast_pkts_delta": 142000, "out_ucast_pkts_delta": 141850, "in_errors_delta": 0, "out_errors_delta": 0, "in_discards_delta": 0, "out_discards_delta": 42, "cpu_load_pct": 34.2, "mem_used_pct": 48.0, "optical_rx_dbm": -6.4, "oper_status": "UP", "is_missing": false, "freshness_state": "FRESH"}
```

### Schema 2: Latency & Jitter Telemetry (`latency_jitter_telemetry` — Source: BFD / TWAMP / IP-SLA / 10-Burst ICMP Probes, 15s Agg)
| Field Name | Data Type | Units | Req / Nullable | Validation Rule |
| :--- | :--- | :--- | :---: | :--- |
| `bucket_15s_utc_ms` | `BIGINT` | `ms (UTC)` | Req / `NOT NULL` | `bucket_15s_utc_ms % 15000 == 0` |
| `observed_at_utc_ms` | `BIGINT` | `ms (UTC)` | Req / `NOT NULL` | `<= bucket_15s_utc_ms` |
| `entity_canonical_id` | `VARCHAR(96)` | ID | Req / `NOT NULL` | Link or path canonical ID (`mpls-link-mab-1`) |
| `rtt_mean_ms` | `DOUBLE PRECISION` | `ms` | Opt / `NULLABLE` | `> 0.0` (`NULL` if probe lost) |
| `rtt_p95_ms` | `DOUBLE PRECISION` | `ms` | Opt / `NULLABLE` | `>= rtt_mean_ms` |
| `jitter_mean_ms` | `DOUBLE PRECISION` | `ms` | Opt / `NULLABLE` | `>= 0.0` (RFC 3550 inter-arrival jitter) |
| `bfd_echo_var_ms2` | `DOUBLE PRECISION` | `ms^2` | Opt / `NULLABLE` | `>= 0.0` |
| `packet_loss_pct` | `DOUBLE PRECISION` | `%` | Opt / `NULLABLE` | `0.0 <= val <= 100.0` |
| `is_missing` | `BOOLEAN` | Flag | Req / `NOT NULL` | `true` if probe unreachable |
| `freshness_state` | `VARCHAR(24)` | Enum | Req / `NOT NULL` | `IN ('FRESH', 'DEGRADED_POLLING', 'STALE_TELEMETRY')` |

- **Representative Record (`Schema 2`):**
```json
{"bucket_15s_utc_ms": 1793545200000, "observed_at_utc_ms": 1793545199100, "entity_canonical_id": "core:mpls:link:mpls-link-mab-1", "rtt_mean_ms": 21.6, "rtt_p95_ms": 26.4, "jitter_mean_ms": 4.2, "bfd_echo_var_ms2": 0.48, "packet_loss_pct": 0.35, "is_missing": false, "freshness_state": "FRESH"}
```

### Schema 3: QoS & Queue Statistics (`qos_queue_telemetry` — Source: SNMP Cisco-Class-Based-QoS-MIB / Linux `tc -s qdisc`, 15s Poll)
| Field Name | Data Type | Units | Req / Nullable | Validation Rule |
| :--- | :--- | :--- | :---: | :--- |
| `bucket_15s_utc_ms` | `BIGINT` | `ms (UTC)` | Req / `NOT NULL` | `bucket_15s_utc_ms % 15000 == 0` |
| `entity_canonical_id` | `VARCHAR(96)` | ID | Req / `NOT NULL` | `site:router:qos_queue:iface:class` |
| `dscp_class` | `VARCHAR(16)` | DSCP | Req / `NOT NULL` | `IN ('EF', 'AF41', 'AF21', 'CS6', 'BE')` |
| `service_sla_tag` | `VARCHAR(24)` | SLA Tier | Req / `NOT NULL` | `IN ('voip', 'video', 'database', 'bulk', 'default')` (from `taxonomy.py`) |
| `queue_depth_pkts` | `INTEGER` | `packets` | Opt / `NULLABLE` | `0 <= val <= queue_limit_pkts` |
| `queue_limit_pkts` | `INTEGER` | `packets` | Req / `NOT NULL` | `> 0` |
| `queue_drops_pps` | `DOUBLE PRECISION` | `pkt/s` | Opt / `NULLABLE` | `>= 0.0` (`cbQosCMDropPkt64` rate) |
| `tx_rate_mbps` | `DOUBLE PRECISION` | `Mbps` | Opt / `NULLABLE` | `>= 0.0` |
| `traffic_share_ratio` | `DOUBLE PRECISION` | `ratio` | Opt / `NULLABLE` | `0.0 <= val <= 1.0` |
| `is_missing` | `BOOLEAN` | Flag | Req / `NOT NULL` | Boolean |

- **Representative Record (`Schema 3`):**
```json
{"bucket_15s_utc_ms": 1793545200000, "entity_canonical_id": "br1:ce-br1:qos_queue:eth0:EF", "dscp_class": "EF", "service_sla_tag": "voip", "queue_depth_pkts": 54, "queue_limit_pkts": 64, "queue_drops_pps": 14.8, "tx_rate_mbps": 24.5, "traffic_share_ratio": 0.28, "is_missing": false}
```

### Schema 4: BGP Protocol Events (`bgp_protocol_events` — Source: FRR `bgpd` Socket / BMP / Dual-Format Syslog, Event-Driven + 15s Agg)
| Field Name | Data Type | Units | Req / Nullable | Validation Rule |
| :--- | :--- | :--- | :---: | :--- |
| `event_uuid` | `UUID` | ID | Req / `NOT NULL` | Deterministic UUIDv5 deduplication key |
| `observed_at_utc_ms` | `BIGINT` | `ms (UTC)` | Req / `NOT NULL` | Event emission timestamp |
| `bucket_15s_utc_ms` | `BIGINT` | `ms (UTC)` | Req / `NOT NULL` | Ceiling 15s alignment bucket |
| `entity_canonical_id` | `VARCHAR(96)` | ID | Req / `NOT NULL` | `site:router:bgp_peer:peer_ip` |
| `peer_asn` | `INTEGER` | ASN | Req / `NOT NULL` | `1 <= peer_asn <= 4294967295` |
| `vrf_name` | `VARCHAR(32)` | VRF | Req / `NOT NULL` | e.g., `vrf-voice`, `vrf-data`, `default` |
| `event_subtype` | `VARCHAR(32)` | Enum | Req / `NOT NULL` | `IN ('ADJ_UP', 'ADJ_DOWN', 'ROUTE_UPDATE', 'ROUTE_WITHDRAW', 'FLAP_DAMPED')` |
| `updates_count_15s` | `INTEGER` | `msgs` | Req / `NOT NULL` | `>= 0` |
| `withdraws_count_15s` | `INTEGER` | `msgs` | Req / `NOT NULL` | `>= 0` |
| `rfc2439_flap_penalty`| `DOUBLE PRECISION` | `penalty` | Req / `NOT NULL` | `>= 0.0` (suppress threshold = `2000.0`) |
| `hawkes_intensity` | `DOUBLE PRECISION` | `rate/min` | Req / `NOT NULL` | `>= 0.0` ($\lambda_{\text{BGP}}(t)$) |

- **Representative Record (`Schema 4`):**
```json
{"event_uuid": "a18c4029-4f1b-5210-9c12-08a41e773190", "observed_at_utc_ms": 1793545194110, "bucket_15s_utc_ms": 1793545200000, "entity_canonical_id": "br1:ce-br1:bgp_peer:10.255.0.2", "peer_asn": 65000, "vrf_name": "vrf-voice", "event_subtype": "ROUTE_WITHDRAW", "updates_count_15s": 6, "withdraws_count_15s": 3, "rfc2439_flap_penalty": 845.0, "hawkes_intensity": 2.64}
```

### Schema 5: OSPF Protocol Events (`ospf_protocol_events` — Source: FRR `ospfd` Socket / Syslog, Event-Driven + 15s Agg)
| Field Name | Data Type | Units | Req / Nullable | Validation Rule |
| :--- | :--- | :--- | :---: | :--- |
| `event_uuid` | `UUID` | ID | Req / `NOT NULL` | Unique event ID |
| `observed_at_utc_ms` | `BIGINT` | `ms (UTC)` | Req / `NOT NULL` | Event timestamp |
| `bucket_15s_utc_ms` | `BIGINT` | `ms (UTC)` | Req / `NOT NULL` | 15s grid bucket |
| `entity_canonical_id` | `VARCHAR(96)` | ID | Req / `NOT NULL` | `site:router:ospf_nbr:nbr_router_id` |
| `ospf_area` | `VARCHAR(24)` | Area | Req / `NOT NULL` | e.g., `0.0.0.0` |
| `adj_state` | `VARCHAR(24)` | Enum | Req / `NOT NULL` | `IN ('FULL', 'TWOWAY', 'EXSTART', 'INIT', 'DOWN')` |
| `lsa_updates_15s` | `INTEGER` | `LSAs` | Req / `NOT NULL` | `>= 0` |
| `spf_runs_15s` | `INTEGER` | `runs` | Req / `NOT NULL` | `>= 0` |
| `convergence_time_ms` | `DOUBLE PRECISION` | `ms` | Opt / `NULLABLE` | `>= 0.0` |

- **Representative Record (`Schema 5`):**
```json
{"event_uuid": "b29d5130-5a2c-5321-8d23-19b52f884201", "observed_at_utc_ms": 1793545196000, "bucket_15s_utc_ms": 1793545200000, "entity_canonical_id": "br1:ce-br1:ospf_nbr:10.0.0.254", "ospf_area": "0.0.0.0", "adj_state": "FULL", "lsa_updates_15s": 14, "spf_runs_15s": 2, "convergence_time_ms": 410.5}
```

### Schema 6: Syslog Events (`syslog_events` — Source: Dual-Format FRR Native & RFC 5424 Syslog Listener, Port 514)
| Field Name | Data Type | Units | Req / Nullable | Validation Rule |
| :--- | :--- | :--- | :---: | :--- |
| `syslog_uuid` | `UUID` | ID | Req / `NOT NULL` | Deduplicated hash over `(host, facility, severity, msg, 1s_bucket)` |
| `observed_at_utc_ms` | `BIGINT` | `ms (UTC)` | Req / `NOT NULL` | Device timestamp (NTP/PTP synced) |
| `bucket_15s_utc_ms` | `BIGINT` | `ms (UTC)` | Req / `NOT NULL` | 15s alignment bucket |
| `entity_canonical_id` | `VARCHAR(96)` | ID | Req / `NOT NULL` | `site:router:system:syslog` |
| `facility_program` | `VARCHAR(32)` | Facility | Req / `NOT NULL` | e.g., `bgpd`, `ospfd`, `charon`, `kernel` |
| `severity_level` | `INTEGER` | `0..7` | Req / `NOT NULL` | `0 (Emerg) <= val <= 7 (Debug)` |
| `mnemonic_code` | `VARCHAR(48)` | Code | Req / `NOT NULL` | e.g., `BGP-5-ADJCHANGE`, `LINK-3-UPDOWN`, `SYS-5-CONFIG_I` |
| `sanitized_message` | `TEXT` | Text | Req / `NOT NULL` | Stripped of prompt-injection patterns by `sanitizer.py` |

- **Representative Record (`Schema 6`):**
```json
{"syslog_uuid": "c30e6241-6b3d-5432-9e34-20c63a995312", "observed_at_utc_ms": 1793545197250, "bucket_15s_utc_ms": 1793545200000, "entity_canonical_id": "br1:ce-br1:system:syslog", "facility_program": "charon", "severity_level": 4, "mnemonic_code": "IKEV2-4-REKEY_RETRY", "sanitized_message": "14[IKE] retransmitting request 2 of CREATE_CHILD_SA for reqid 101 (tun-br1-sa), DH group ECP_384"}
```

### Schema 7: NetFlow / IPFIX Flow Records (`netflow_ipfix_records` — Source: `softflowd` / `pmacct` / `netflow_simulator.py`, 15s Active Timeout)
| Field Name | Data Type | Units | Req / Nullable | Validation Rule |
| :--- | :--- | :--- | :---: | :--- |
| `flow_record_id` | `UUID` | ID | Req / `NOT NULL` | Unique flow slice ID |
| `bucket_15s_utc_ms` | `BIGINT` | `ms (UTC)` | Req / `NOT NULL` | 15s export bucket |
| `entity_canonical_id` | `VARCHAR(96)` | ID | Req / `NOT NULL` | Exporting router + egress interface/tunnel ID |
| `src_subnet_prefix` | `VARCHAR(32)` | CIDR | Req / `NOT NULL` | Valid IPv4/IPv6 prefix (`10.10.1.0/24`) |
| `dst_subnet_prefix` | `VARCHAR(32)` | CIDR | Req / `NOT NULL` | Valid IPv4/IPv6 prefix (`10.20.0.0/24`) |
| `ip_protocol` | `INTEGER` | Proto | Req / `NOT NULL` | `6 (TCP), 17 (UDP), 50 (ESP), 1 (ICMP)` |
| `dscp_value` | `INTEGER` | `0..63` | Req / `NOT NULL` | `46 (EF), 34 (AF41), 18 (AF21), 0 (BE)` |
| `app_class` | `VARCHAR(32)` | App | Req / `NOT NULL` | `IN ('voip_rtp', 'video_conf', 'erp_sql', 'bulk_backup', 'best_effort')` |
| `service_sla_tag` | `VARCHAR(24)` | SLA Tier | Req / `NOT NULL` | `IN ('voip', 'video', 'database', 'bulk', 'default')` |
| `direction` | `VARCHAR(16)` | Enum | Req / `NOT NULL` | `IN ('FORWARD', 'RETURN')` |
| `bytes_delta` | `BIGINT` | `bytes` | Req / `NOT NULL` | `> 0` |
| `packets_delta` | `BIGINT` | `packets` | Req / `NOT NULL` | `> 0` |
| `flow_duration_ms` | `INTEGER` | `ms` | Req / `NOT NULL` | `>= 0` |
| `path_asymmetry_ratio`| `DOUBLE PRECISION` | `ratio` | Opt / `NULLABLE` | `0.0 <= val <= 1.0` ($\|B_{\text{fwd}}-B_{\text{ret}}\|/(B_{\text{fwd}}+B_{\text{ret}})$) |

- **Representative Record (`Schema 7`):**
```json
{"flow_record_id": "d41f7352-7c4e-5543-af45-31d74b006423", "bucket_15s_utc_ms": 1793545200000, "entity_canonical_id": "br1:ce-br1:tunnel:tun-br1", "src_subnet_prefix": "10.10.1.0/24", "dst_subnet_prefix": "10.99.0.0/24", "ip_protocol": 17, "dscp_value": 46, "app_class": "voip_rtp", "service_sla_tag": "voip", "direction": "FORWARD", "bytes_delta": 27187500, "packets_delta": 181250, "flow_duration_ms": 15000, "path_asymmetry_ratio": 0.042}
```

### Schema 8: IPSec & MPLS LSP Tunnel Statistics (`ipsec_tunnel_telemetry` — Source: StrongSwan VICI + Overlay BFD + MPLS LDP Health, 15s Poll)
| Field Name | Data Type | Units | Req / Nullable | Validation Rule |
| :--- | :--- | :--- | :---: | :--- |
| `bucket_15s_utc_ms` | `BIGINT` | `ms (UTC)` | Req / `NOT NULL` | 15s grid bucket |
| `entity_canonical_id` | `VARCHAR(96)` | ID | Req / `NOT NULL` | `site:router:tunnel:tun_name` |
| `underlay_path_id` | `VARCHAR(96)` | ID | Req / `NOT NULL` | Bound MPLS/INET underlay path ID |
| `tunnel_state` | `VARCHAR(24)` | Enum | Req / `NOT NULL` | `IN ('ESTABLISHED', 'REKEYING', 'DEGRADED', 'DOWN')` |
| `lsp_health_score` | `DOUBLE PRECISION` | `0..1` | Req / `NOT NULL` | `0.0 <= val <= 1.0` (Graph model LSP composite health) |
| `availability_pct` | `DOUBLE PRECISION` | `%` | Opt / `NULLABLE` | `0.0 <= val <= 100.0` |
| `tunnel_rtt_ms` | `DOUBLE PRECISION` | `ms` | Opt / `NULLABLE` | `> 0.0` |
| `tunnel_jitter_ms` | `DOUBLE PRECISION` | `ms` | Opt / `NULLABLE` | `>= 0.0` |
| `esp_seq_loss_pct` | `DOUBLE PRECISION` | `%` | Opt / `NULLABLE` | `0.0 <= val <= 100.0` (ESP sequence gap ratio) |
| `replay_drops_pps` | `DOUBLE PRECISION` | `pkt/s` | Opt / `NULLABLE` | `>= 0.0` ([RFC 4303](https://www.rfc-editor.org/info/rfc4303/) anti-replay window drops) |
| `ike_rekey_lat_ms` | `DOUBLE PRECISION` | `ms` | Opt / `NULLABLE` | `>= 0.0` (`CREATE_CHILD_SA` RTT) |
| `ike_dh_retries` | `INTEGER` | `retries` | Opt / `NULLABLE` | `>= 0` |
| `sa_rem_life_min` | `DOUBLE PRECISION` | `minutes` | Opt / `NULLABLE` | Remaining time until Child-SA hard expiry |
| `is_missing` | `BOOLEAN` | Flag | Req / `NOT NULL` | Boolean |

- **Representative Record (`Schema 8`):**
```json
{"bucket_15s_utc_ms": 1793545200000, "entity_canonical_id": "br1:ce-br1:tunnel:tun-br1", "underlay_path_id": "core:mpls:srlg:transport-A-hub1", "tunnel_state": "REKEYING", "lsp_health_score": 0.74, "availability_pct": 100.0, "tunnel_rtt_ms": 22.8, "tunnel_jitter_ms": 6.4, "esp_seq_loss_pct": 0.12, "replay_drops_pps": 0.4, "ike_rekey_lat_ms": 385.0, "ike_dh_retries": 3, "sa_rem_life_min": 7.5, "is_missing": false}
```

### Schema 9: SD-WAN Controller Events (`sdwan_controller_events` — Source: `SDWANControllerAdapter`, 15s Poll / Webhook)
| Field Name | Data Type | Units | Req / Nullable | Validation Rule |
| :--- | :--- | :--- | :---: | :--- |
| `event_uuid` | `UUID` | ID | Req / `NOT NULL` | Unique controller event ID |
| `bucket_15s_utc_ms` | `BIGINT` | `ms (UTC)` | Req / `NOT NULL` | 15s grid bucket |
| `entity_canonical_id` | `VARCHAR(96)` | ID | Req / `NOT NULL` | `global:sdwan:controller:ctrl_id` |
| `adapter_driver` | `VARCHAR(32)` | Driver | Req / `NOT NULL` | `IN ('TEMLOOM_NATIVE', 'CISCO_VMANAGE', 'GENERIC_YANG')` |
| `controller_health` | `VARCHAR(16)` | Enum | Req / `NOT NULL` | `IN ('HEALTHY', 'DEGRADED', 'UNREACHABLE')` |
| `connected_sites_cnt` | `INTEGER` | `sites` | Req / `NOT NULL` | `>= 0` |
| `aar_policy_name` | `VARCHAR(64)` | Policy | Req / `NOT NULL` | e.g., `AAR-VOICE-GOLD` |
| `selected_tunnel_id` | `VARCHAR(96)` | Tunnel | Req / `NOT NULL` | Active tunnel selected for SLA class |
| `aar_decision_reason` | `VARCHAR(64)` | Enum | Req / `NOT NULL` | `IN ('SLA_COMPLIANT', 'JITTER_BREACH_FAILOVER', 'MANUAL_PIN', 'POLICY_DRIFT')` |
| `policy_drift_detected`| `BOOLEAN` | Flag | Req / `NOT NULL` | `true` when `active_policy_hash != golden_policy_hash` |

- **Representative Record (`Schema 9`):**
```json
{"event_uuid": "e52a8463-8d5f-5654-bf56-42e85c117534", "bucket_15s_utc_ms": 1793545200000, "entity_canonical_id": "global:sdwan:controller:ctrl-1", "adapter_driver": "TEMLOOM_NATIVE", "controller_health": "HEALTHY", "connected_sites_cnt": 4, "aar_policy_name": "AAR-VOICE-GOLD", "selected_tunnel_id": "br1:ce-br1:tunnel:tun-br1-inet", "aar_decision_reason": "POLICY_DRIFT", "policy_drift_detected": true}
```

### Schema 10: Configuration & Autonomy Policy Changes (`config_policy_changes` — Source: FRR/NETCONF Diff + Controller & Autonomy Matrix Audit)
| Field Name | Data Type | Units | Req / Nullable | Validation Rule |
| :--- | :--- | :--- | :---: | :--- |
| `change_id` | `UUID` | ID | Req / `NOT NULL` | Primary key |
| `observed_at_utc_ms` | `BIGINT` | `ms (UTC)` | Req / `NOT NULL` | Commit timestamp |
| `bucket_15s_utc_ms` | `BIGINT` | `ms (UTC)` | Req / `NOT NULL` | 15s grid bucket |
| `entity_canonical_id` | `VARCHAR(96)` | ID | Req / `NOT NULL` | Router, controller, or `global:policy:autonomy_matrix` |
| `actor_identity` | `VARCHAR(64)` | Actor | Req / `NOT NULL` | Operator username or `TEMLOOM_2PC_EXECUTOR` |
| `golden_config_sha256`| `CHAR(64)` | SHA-256 | Req / `NOT NULL` | Approved baseline hash |
| `active_config_sha256`| `CHAR(64)` | SHA-256 | Req / `NOT NULL` | Post-commit running-config hash |
| `is_unintended_drift` | `BOOLEAN` | Flag | Req / `NOT NULL` | `true` if change lacks an approved change/2PC ticket or violates `taxonomy.py` floor |
| `unified_diff_text` | `TEXT` | Diff | Req / `NOT NULL` | Unified CLI/YANG/Policy JSON diff stanza |

- **Representative Record (`Schema 10`):**
```json
{"change_id": "f63b9574-9e60-5765-c067-53f96d228645", "observed_at_utc_ms": 1793545189000, "bucket_15s_utc_ms": 1793545200000, "entity_canonical_id": "global:sdwan:controller:ctrl-1", "actor_identity": "manual_cli_admin", "golden_config_sha256": "8f9d2a1c4b7e6051e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934c", "active_config_sha256": "3c11e90b77a2d409e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934c", "is_unintended_drift": true, "unified_diff_text": "- match dscp EF set tunnel tun-br1-mpls\n+ match dscp EF set tunnel tun-br1-inet"}
```

### Schema 11: Injected Fault Records (`injected_fault_records` — Source: Out-of-Band Fault Injector, Strictly Isolated)
| Field Name | Data Type | Units | Req / Nullable | Validation Rule |
| :--- | :--- | :--- | :---: | :--- |
| `fault_id` | `UUID` | ID | Req / `NOT NULL` | Primary key |
| `experiment_id` | `VARCHAR(64)` | ID | Req / `NOT NULL` | Experiment run identifier |
| `scenario_id` | `VARCHAR(64)` | ID | Req / `NOT NULL` | e.g., `Scenario_A`, `R2_RFC2439`, `ADV-7` |
| `random_seed` | `INTEGER` | Seed | Req / `NOT NULL` | Deterministic RNG seed (`101..410`) |
| `fault_category` | `VARCHAR(32)` | Enum | Req / `NOT NULL` | `IN ('CONGESTION', 'LATENCY_DRIFT', 'QOS_DROP', 'BGP_FLAP', 'OSPF_STORM', 'ASYMMETRY', 'TUNNEL_REKEY', 'POLICY_DRIFT', 'SRLG_FAULT', 'BENIGN_STRESS')` |
| `affected_entity_id` | `VARCHAR(96)` | ID | Req / `NOT NULL` | Target device/interface/tunnel ID |
| `related_entities_json`| `JSONB` | List | Req / `NOT NULL` | Downstream dependent tunnels & services |
| `start_utc_ms` | `BIGINT` | `ms (UTC)` | Req / `NOT NULL` | Fault onset timestamp |
| `end_utc_ms` | `BIGINT` | `ms (UTC)` | Req / `NOT NULL` | Fault end timestamp |
| `fault_severity` | `VARCHAR(16)` | Enum | Req / `NOT NULL` | `IN ('NONE_BENIGN', 'MODERATE', 'SEVERE', 'CRITICAL')` |
| `fault_parameters` | `JSONB` | JSON | Req / `NOT NULL` | Exact slope, flap rate, or loss parameters injected |
| `injection_succeeded` | `BOOLEAN` | Flag | Req / `NOT NULL` | Verified by injector return code |

- **Representative Record (`Schema 11`):**
```json
{"fault_id": "074ca685-0f71-5876-d178-640a7e339756", "experiment_id": "EXP-20261101-STD-301", "scenario_id": "Scenario_A_Linear_Congestion", "random_seed": 301, "fault_category": "CONGESTION", "affected_entity_id": "core:mpls:link:mpls-link-mab-1", "related_entities_json": ["br1:ce-br1:tunnel:tun-br1", "br2:ce-br2:tunnel:tun-br2", "br1:service:voip_rtp"], "start_utc_ms": 1793544600000, "end_utc_ms": 1793546400000, "fault_severity": "CRITICAL", "fault_parameters": {"ramp_mbps_per_min": 1.8, "ef_share": 0.28}, "injection_succeeded": true}
```

### Schema 12: Ground-Truth Incident Labels (`ground_truth_incident_labels` — Source: Independent SLA Evaluator)
| Field Name | Data Type | Units | Req / Nullable | Validation Rule |
| :--- | :--- | :--- | :---: | :--- |
| `gt_incident_id` | `UUID` | ID | Req / `NOT NULL` | Primary key |
| `fault_id` | `UUID` | FK | Req / `NOT NULL` | References `injected_fault_records(fault_id)` |
| `expects_sla_breach` | `BOOLEAN` | Flag | Req / `NOT NULL` | `true` for breach scenarios, `false` for benign stress |
| `sla_breach_occurred` | `BOOLEAN` | Flag | Req / `NOT NULL` | Physical SLA threshold crossed for $\ge K$ steps |
| `sla_breach_onset_ms` | `BIGINT` | `ms (UTC)` | Opt / `NULLABLE` | Exact timestamp of physical SLA breach onset |
| `recovery_utc_ms` | `BIGINT` | `ms (UTC)` | Opt / `NULLABLE` | Timestamp when metrics returned below SLA |
| `expected_impact_json`| `JSONB` | JSON | Req / `NOT NULL` | Expected SLA metric & service degradation |
| `actual_impact_json` | `JSONB` | JSON | Req / `NOT NULL` | Realized peak utilization, RTT, loss, drops |
| `detected_by_system` | `BOOLEAN` | Flag | Req / `NOT NULL` | Evaluated post-hoc by benchmark harness |
| `predicted_before_sla`| `BOOLEAN` | Flag | Req / `NOT NULL` | `alert_utc_ms < sla_breach_onset_ms` |
| `realized_lead_min` | `DOUBLE PRECISION` | `minutes` | Opt / `NULLABLE` | `(sla_breach_onset_ms - alert_utc_ms) / 60000.0` |

- **Representative Record (`Schema 12`):**
```json
{"gt_incident_id": "185db796-1082-5987-e289-751b8f440867", "fault_id": "074ca685-0f71-5876-d178-640a7e339756", "expects_sla_breach": true, "sla_breach_occurred": true, "sla_breach_onset_ms": 1793545275000, "recovery_utc_ms": 1793545365000, "expected_impact_json": {"sla_metric": "utilization_mbps >= 95.0 or rtt_ms >= 30.0"}, "actual_impact_json": {"peak_util_mbps": 96.4, "peak_rtt_ms": 34.2, "peak_drops_pps": 31.0}, "detected_by_system": true, "predicted_before_sla": true, "realized_lead_min": 6.50}
```

### Schema 13: Structured Prediction & Digital Twin Outputs (`prediction_outputs` — Section 3.3 Contract)
| Field Name | Data Type | Units | Req / Nullable | Validation Rule |
| :--- | :--- | :--- | :---: | :--- |
| `prediction_id` | `UUID` | ID | Req / `NOT NULL` | Primary key |
| `bucket_15s_utc_ms` | `BIGINT` | `ms (UTC)` | Req / `NOT NULL` | 15s prediction timestamp |
| `entity_canonical_id` | `VARCHAR(96)` | ID | Req / `NOT NULL` | Monitored link, peer, tunnel, or controller |
| `issue_category` | `VARCHAR(32)` | Enum | Req / `NOT NULL` | `IN ('LINK_CONGESTION', 'LATENCY_DRIFT', 'QOS_STARVATION', 'BGP_FLAP_CASCADE', 'OSPF_STORM', 'PATH_ASYMMETRY', 'TUNNEL_REKEY_EXHAUSTION', 'ANTI_REPLAY_OVERFLOW', 'POLICY_DRIFT', 'NORMAL')` |
| `prediction_horizon_m`| `DOUBLE PRECISION` | `minutes` | Req / `NOT NULL` | Target forecast horizon (`5.0, 10.0, 15.0`) |
| `estimated_tti_min` | `DOUBLE PRECISION` | `minutes` | Opt / `NULLABLE` | Point Time-to-Impact (`NULL` if no active hazard) |
| `model_anomaly_score` | `DOUBLE PRECISION` | `0..1` | Req / `NOT NULL` | Deterministic hazard severity score $\in [0.0, 1.0]$ |
| `digital_twin_divergence`| `DOUBLE PRECISION` | `0..1` | Opt / `NULLABLE` | Forecast-vs-NetworkX graph flow divergence (`digital_twin.py`) |
| `engines_agree` | `BOOLEAN` | Flag | Req / `NOT NULL` | `true` when statistical model & NetworkX graph model both corroborate hazard |
| `conformal_alpha` | `DOUBLE PRECISION` | `0..1` | Req / `NOT NULL` | Miscoverage rate $\alpha = 0.10$ ($90\%$ nominal coverage) |
| `conformal_lo_bound` | `DOUBLE PRECISION` | Metric unit | Req / `NOT NULL` | Lower $90\%$ empirical residual bound $L_{t,h}$ |
| `conformal_hi_bound` | `DOUBLE PRECISION` | Metric unit | Req / `NOT NULL` | Upper $90\%$ empirical residual bound $U_{t,h}$ |
| `freshness_confidence`| `DOUBLE PRECISION` | `0..1` | Req / `NOT NULL` | Data-quality weight $\text{clip}(1 - 1.5 m_t, 0.40, 0.98)$ |
| `contributing_features`| `JSONB` | JSON | Req / `NOT NULL` | Top-5 ranked hazard features & exact telemetry values |
| `model_identifier` | `VARCHAR(48)` | ID | Req / `NOT NULL` | e.g., `TEMLOOM_Model_G1_Congestion` |
| `model_version_id` | `VARCHAR(64)` | SemVer+Sig | Req / `NOT NULL` | e.g., `v4.1.0-ed25519:9a4f12` (verified by `model_integrity.py`) |
| `linked_incident_id` | `UUID` | FK | Opt / `NULLABLE` | References `epistemic_incidents(incident_id)` |

- **Representative Record (`Schema 13`):**
```json
{"prediction_id": "296ec807-2193-5098-f39a-862c9a551978", "bucket_15s_utc_ms": 1793544885000, "entity_canonical_id": "core:mpls:link:mpls-link-mab-1", "issue_category": "LINK_CONGESTION", "prediction_horizon_m": 10.0, "estimated_tti_min": 6.50, "model_anomaly_score": 0.89, "digital_twin_divergence": 0.34, "engines_agree": true, "conformal_alpha": 0.10, "conformal_lo_bound": 79.8, "conformal_hi_bound": 102.0, "freshness_confidence": 0.98, "contributing_features": {"haz_util": true, "haz_lat": false, "haz_drops": true, "s_short_mbps_min": 1.85, "s_med_mbps_min": 1.78, "d_ewma_pps": 9.4}, "model_identifier": "TEMLOOM_Model_G1_Congestion", "model_version_id": "v4.1.0-ed25519:9a4f12", "linked_incident_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"}
```

### Schema 14: Root-Cause Analysis & Clonal Counterfactual Outputs (`rca_outputs` — Source: `EquivalenceAwareSRLGRanker` + `graph_model.py`)
| Field Name | Data Type | Units | Req / Nullable | Validation Rule |
| :--- | :--- | :--- | :---: | :--- |
| `rca_output_id` | `UUID` | ID | Req / `NOT NULL` | Primary key |
| `incident_id` | `UUID` | FK | Req / `NOT NULL` | References `epistemic_incidents(incident_id)` |
| `bucket_15s_utc_ms` | `BIGINT` | `ms (UTC)` | Req / `NOT NULL` | Evaluation timestamp |
| `epistemic_rca_state` | `VARCHAR(32)` | Enum | Req / `NOT NULL` | `IN ('SUSPECTED_CAUSE', 'AMBIGUOUS_CAUSE_SET', 'VERIFIED_CAUSE')` |
| `is_ambiguous` | `BOOLEAN` | Flag | Req / `NOT NULL` | `true` when $\|\Phi(c_1) - \Phi(c_2)\| < 0.08$ |
| `ranked_causes_json` | `JSONB` | List | Req / `NOT NULL` | Ordered list of `{entity_id, layer, score, coverage, telemetry_corr}` |
| `clonal_search_scores`| `JSONB` | JSON | Req / `NOT NULL` | Counterfactual topology scores `{BASELINE, REROUTED, QOS_THROTTLED}` |
| `affected_services` | `JSONB` | List | Req / `NOT NULL` | Downstream services & branches impacted (`service_sla_tag`) |
| `priority_score` | `DOUBLE PRECISION` | `0..100` | Req / `NOT NULL` | Deterministic $P_{\text{incident}} \in [0.0, 100.0]$ |
| `operator_feedback` | `VARCHAR(16)` | Enum | Req / `NOT NULL` | `IN ('PENDING', 'ACCEPTED', 'REJECTED')` (`feedback_cli.py`) |
| `disambiguation_action`| `VARCHAR(128)` | Action | Opt / `NULLABLE` | Out-of-band SNMP poll target when `is_ambiguous = true` |

- **Representative Record (`Schema 14`):**
```json
{"rca_output_id": "3a7fd918-32a4-5109-a40b-973d0b662089", "incident_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479", "bucket_15s_utc_ms": 1793544885000, "epistemic_rca_state": "AMBIGUOUS_CAUSE_SET", "is_ambiguous": true, "ranked_causes_json": [{"entity_id": "core:mpls:srlg:transport-A-hub1", "layer": "L2_CARRIER_SRLG", "score": 0.842}, {"entity_id": "hub1:ce-hub1:iface:wan0", "layer": "L1_INTERFACE", "score": 0.819}], "clonal_search_scores": {"BASELINE": 0.18, "REROUTED": 0.94, "QOS_THROTTLED": 0.76}, "affected_services": ["br1:service:voip_rtp", "br2:service:video_conf"], "priority_score": 84.6, "operator_feedback": "PENDING", "disambiguation_action": "POLL_SNMPV3_IFMIB_NOW(hub1:ce-hub1:iface:wan0)"}
```

### Schema 15: Remediation Outcomes (`remediation_outcomes` — Source: 4-Stage Safety Engine & 2PC Executor)
| Field Name | Data Type | Units | Req / Nullable | Validation Rule |
| :--- | :--- | :--- | :---: | :--- |
| `remediation_id` | `UUID` | ID | Req / `NOT NULL` | Primary key |
| `incident_id` | `UUID` | FK | Req / `NOT NULL` | References `epistemic_incidents(incident_id)` |
| `playbook_id` | `VARCHAR(32)` | ID | Req / `NOT NULL` | e.g., `PB-STEER-BULK-AF21`, `PB-BGP-LOCALPREF` |
| `autonomy_execution_mode`| `VARCHAR(24)` | Enum | Req / `NOT NULL` | `IN ('RECOMMEND_ONLY', 'PRE_VALIDATED_STAGED')` (`taxonomy.py` matrix) |
| `stage1_ast_pass` | `BOOLEAN` | Flag | Req / `NOT NULL` | EBNF token allowlist & zero shell metacharacters |
| `stage2_lease_id` | `UUID` | FK | Opt / `NULLABLE` | References `bandwidth_reservation_leases(lease_id)` |
| `projected_backup_pct`| `DOUBLE PRECISION` | `%` | Req / `NOT NULL` | Must be $\le 80.0\%$ to pass Stage 2 |
| `stage3_mm1k_rtt_ms` | `DOUBLE PRECISION` | `ms` | Req / `NOT NULL` | Must be $\le 25.0\text{ ms}$ to pass Stage 3A |
| `stage3_batfish_pass` | `BOOLEAN` | Flag | Req / `NOT NULL` | Zero loops, blackholes, or ACL drops |
| `ed25519_approver_id` | `VARCHAR(64)` | Actor | Opt / `NULLABLE` | Operator who signed the approval token |
| `ed25519_signature` | `VARCHAR(128)` | Hex | Opt / `NULLABLE` | Verified Ed25519 signature over diff hash |
| `twophase_commit_state`| `VARCHAR(32)` | Enum | Req / `NOT NULL` | `IN ('BLOCKED_SAFETY', 'AWAITING_APPROVAL', 'COMMITTED_2PC', 'ABORTED_PHASE1', 'AUTO_ROLLED_BACK', 'CONFIRMED_OUTCOME')` |
| `execution_stdout_log`| `TEXT` | Log | Opt / `NULLABLE` | Captured router NETCONF/CLI `docker exec` / SSH transcript |
| `post_change_rtt_ms` | `DOUBLE PRECISION` | `ms` | Opt / `NULLABLE` | Measured 45s post-change RTT |

- **Representative Record (`Schema 15`):**
```json
{"remediation_id": "4b80ea29-43b5-521a-b51c-084e1c773190", "incident_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479", "playbook_id": "PB-STEER-BULK-AF21", "autonomy_execution_mode": "RECOMMEND_ONLY", "stage1_ast_pass": true, "stage2_lease_id": "9c1208a4-1e77-4319-8a18-c40294f1b521", "projected_backup_pct": 50.0, "stage3_mm1k_rtt_ms": 11.4, "stage3_batfish_pass": true, "ed25519_approver_id": "noc_lead_sharma", "ed25519_signature": "ed25519:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069", "twophase_commit_state": "CONFIRMED_OUTCOME", "execution_stdout_log": "vtysh -c 'configure terminal' -c 'route-map PB-STEER-BULK-AF21 permit 10' -> COMMIT_OK", "post_change_rtt_ms": 11.2}
```

---

## 2. Six-Phase Implementation Plan Mapped to Modules, Schemas & Verification Gates (Section 5)

Table 2 maps the **Six Authoritative Implementation Phases** (`Phase 1` through `Phase 6`) to their concrete engineering tasks, modules, schemas, and exit gates.

| Implementation Phase | Mandatory Tasks Covered | Modules Created / Refactored | Schemas Produced / Consumed | Verification Gate & Exit Criteria |
| :--- | :--- | :--- | :---: | :--- |
| **PHASE 1: Network Simulation & Unified Launcher** | Establish Branch/Hub/DC topology (`3 Branch CE, 2 PE, 1 P, 1 Hub/DC CE`) with full data-plane veth links (`eth1/eth2`), MPLS/VRF segmentation, BGP/OSPF routing, GRE/IPSec overlays (`overlay-setup.sh`), HTB DSCP QoS (`qos-setup.sh`), multi-class traffic (`EF, AF41, AF21, BE`), deterministic fault injection + `QUIET -> FAULT_BURST -> RESOLVE` state machine (`fault_streamer.py`), independent ground-truth generation, and unified `./run.sh [--clab] [--airgap]` launcher. | `run.sh`, `configs/containerlab/temloom-multisite.clab.yml`, `overlay-setup.sh`, `qos-setup.sh`, `temloom/simulation/simulator.py`, `fault_injector.py`, `fault_streamer.py` | Produces `Schemas 11 & 12` + raw router/tunnel streams | Same `experiment_id` + `random_seed` produces bit-identical telemetry and ground-truth labels across runs; `./run.sh --clab --airgap` runs lab on host and analytics in zero-egress netns; `ground_truth_*` tables isolated from feature extractors. |
| **PHASE 2: Telemetry Pipeline & Taxonomy** | Implement canonical `taxonomy.py` (fault classes, SLA tiers, autonomy floors); SNMPv3, dual-format FRR/RFC5424 Syslog (`syslog_parser.py`), BGP/OSPF, NetFlow/IPFIX (`netflow_simulator.py`), IPSec/MPLS LSP tunnel health, and SD-WAN controller (`SDWANControllerAdapter`) collection over explicit `127.0.0.1` IPv4 sockets; normalize to canonical schemas; align to 15s causal grid; persist to VictoriaMetrics & PostgreSQL; implement deterministic replay & Parquet export. | `temloom/core/taxonomy.py`, `temloom/ingestion/collector.py`, `syslog_parser.py`, `sdwan_adapters.py`, `freshness_gate.py`, `replay_engine.py`, `db/migrations/001_init_temloom_v3.sql` | Produces & validates `Schemas 1–10`; exports SHA-256 `Parquet` | Zero silent interpolation of `NULL` values; 100% counter-wrap clamp (`Scenario I`); automatic transition to `STALE_TELEMETRY` at $>45\text{s}$ poll lag (`Scenario H`); zero IPv6 `localhost` timeout stalls. |
| **PHASE 3: Predictive Modelling, Digital Twin & Cryptographic Attestation** | Construct leakage-free datasets (`101..105` train, `201..205` val, `301..310` test, `401..410` adv); engineer causal features; benchmark 10 candidate model families across 8 tasks; implement `Model G1` (Link), `Model G2` (Routing), `Model G3` (Tunnel), `Model G4` (Policy Drift); implement $\text{TTI}_t$ & direct conformal calibration; implement **Predictive Digital Twin (`digital_twin.py`)** + **Dual-Engine Corroboration (`corroborator.py`)**; implement **Ed25519 Model Signing (`model_integrity.py`)** & **Active Signed Air-Gap Compliance Probe (`airgap_compliance.py`)**. | `temloom/prediction/features.py`, `model_g1_congestion.py`, `model_g2_routing.py`, `model_g3_tunnel.py`, `model_g4_policy.py`, `conformal_aggregator.py`, `digital_twin.py`, `corroborator.py`, `temloom/security/model_integrity.py`, `airgap_compliance.py` | Consumes `Schemas 1–10`; produces `Schema 13` (`prediction_outputs`) + signed compliance report | Domain A Recall `97.14%` std / `100.0%` adv (`89.20%` strict 10m coverage); Domain B Recall `100.0%` (`0.0` FA/hr, `5.0m` lead); Domain C Recall `97.50%` (`5.25m` lead); combined latency `<0.60 ms/step`; 100% Ed25519 model signature & zero-egress probe pass. |
| **PHASE 4: Offline LLM & Dual-Collection IKB Deployment** | Select, quantize & Ed25519-sign `Qwen2.5-3B/7B-Instruct-Q4_K_M.gguf`; package offline wheels/weights; enforce `nftables` & `netns=none` air-gap; deploy `llama-server` & PostgreSQL `pgvector + tsvector`; implement prompt-injection-sanitized **`##`-heading-aware runbook chunking (`384` tokens)** + **operator-verified incident auto-ingestion (`ikb_manager.py`)**, `bge-small-en-v1.5` ONNX embeddings & Hybrid RRF retrieval. | `temloom/copilot/sanitizer.py`, `ikb_manager.py`, `rag_indexer.py`, `rag_retriever.py`, `llm_client.py`, `copilot_response.gbnf` | Populates & queries `rag_knowledge_chunks` (`runbooks` + `verified_incidents`) | Hybrid RRF achieves `100.0% Recall@3` (`0.61 ms/query`) across 30 NOC queries; sanitizer blocks `100%` (`10/10`) of indirect prompt-injection attacks; `0` outbound WAN packets. |
| **PHASE 5: Copilot Q1/Q2/Q3, Multi-Turn NLQ & Clonal 2PC Safety** | Construct `StructuredIncidentContext` combining live SQL/MetricsQL evidence (`Schemas 1–10, 13, 14`) with Top-3 RAG chunks; implement 4-layer DAG RCA + **Clonal State-Space Counterfactual Search (`graph_model.py`)** (`Schema 14`), priority scorer $P_{\text{inc}}$, **stateful multi-turn NLQ (`nlq_interface.py`)**, **Q1/Q2/Q3 GBNF-validated explanations**, **operator feedback CLI (`feedback_cli.py`)**, **Tiered Autonomy Policy Matrix**, and 4-stage deterministic safety + closed-loop 2PC (`Schema 15`). | `temloom/rca/topology_graph.py`, `graph_model.py`, `equivalence_ranker.py`, `prioritiser.py`, `temloom/copilot/nlq_interface.py`, `temloom/remediation/safety_engine.py`, `executor_2pc.py`, `feedback_cli.py`, `temloom/api_ui/app.py` | Produces `Schemas 14 & 15` + `CopilotStructuredResponse` (`Q1/Q2/Q3`) | Passes all 22 safety, AST shell-injection, concurrent TOCTOU lease (`85% > 80%` blocked), Batfish loop rejection, clonal counterfactual scoring, and partial-SSH 2PC rollback unit tests; 100% deterministic Q1/Q2/Q3 fallback if LLM is stopped. |
| **PHASE 6: Scenario Validation** | Execute end-to-end validation across **Scenario A** (Hub-Spoke Congestion), **Scenario B** (BGP Flap & Reroute Cascade), **Scenario C** (Intermittent MPLS Underlay & Tunnel Degradation), and **Scenario D** (SD-WAN Controller Misconfiguration & Policy Drift), plus **Scenarios E, F, G**, recording all 11 evaluation metrics. | `benchmarks/run_all_benchmarks.py`, `tests/test_temloom_complete.py` | Evaluates `Schemas 11–15` end-to-end | All 4 mandatory scenarios (`A, B, C, D`) and 3 safety/ambiguity scenarios (`E, F, G`) pass pre-registered lead-time, RCA Top-1/Ambiguity-Set, citation grounding, and rollback gates. |


---

## 3. Expected Canonical Repository File Tree Structure (`TEMLOOM v4.1`)

```text
temloom/                                             # Repository root
├── README.md                                        # System overview, quick-start, and architecture summary
├── COMMANDS.md                                      # Operator & evaluator CLI verification guide
├── requirements.txt                                 # Pinned offline-installable Python dependencies
├── pyproject.toml                                   # Package metadata, pytest, and ruff configuration
├── docker-compose.yml                               # VictoriaMetrics + PostgreSQL 16 (pgvector + tsvector) stack
├── run.sh                                           # Unified one-command launcher (synthetic | --clab | --airgap | stop | destroy)
│
├── Planning&Architecture/                           # Authoritative Engineering Specification Suite (Read First by Antigravity)
│   ├── temloom_doc1_system_architecture.md          # Document 1: Definitive System Architecture (v4.1)
│   ├── temloom_doc2_implementation_blueprint.md     # Document 2: Engineering Implementation Blueprint & 15 Schemas (v4.1)
│   ├── temloom_doc3_experimental_validation_plan.md # Document 3: Experimental Validation & 10-Model Zoo Plan (v4.1)
│   ├── temloom_doc4_requirements_traceability_matrix.md # Document 4: Requirements Traceability Matrix (v4.1)
│   ├── temloom_doc5_gui_specification.md            # Document 5: 5-Workbench GUI Overview & Interface Specification (v4.1)
│   ├── temloom_aether_review_and_changelog.md       # Comparative Architectural Review (Aether vs. TEMLOOM) & v4.1 Changelog
│   ├── IMPLEMENTATION_AUDIT_REPORT.md               # Phase A Output: Requirement-by-requirement codebase audit
│   ├── IMPLEMENTATION_BACKLOG.md                    # Phase B Output: 16-category dependency-ordered implementation backlog
│   └── FINAL_IMPLEMENTATION_REPORT.md               # Phase H Output: Clean-start verification & handover report
│
├── configs/                                         # Network Topology, Router, Overlay, QoS & Scenario Configurations
│   ├── scenarios.yaml                               # Pre-registered parameters for Scenarios A..L, R1..R6, T1..T6, ADV-1..8
│   ├── experiment_config.yaml                       # Deterministic seed splits (101..105, 201..205, 301..310, 401..410)
│   ├── policy_overrides.json                        # Operator-persisted Autonomy Policy Matrix thresholds (floor-enforced)
│   └── containerlab/
│       ├── temloom-multisite.clab.yml               # 7-node multi-site MPLS L3VPN + SD-WAN topology (pe1, p1, pe2, ce-hub1, ce-br1..2, ce-dc)
│       ├── mpls-frr-setup.sh                        # MPLS kernel labels + FRRouting (OSPF, LDP, MP-BGP, VRFs) + eth1/eth2 data-plane veths
│       ├── overlay-setup.sh                         # StrongSwan IPSec / GRE SD-WAN overlay tunnels over MPLS & INET transports
│       └── qos-setup.sh                             # Linux tc HTB + DSCP class queues (EF, AF41, AF21, CS6, BE)
│
├── db/                                              # Database DDL Migrations & Role Separation Scripts
│   └── migrations/
│       ├── 001_init_temloom_v4_1.sql                # Creates Schemas 1–15 tables, pgvector HNSW, tsvector GIN, and audit hash chain triggers
│       └── 002_roles_and_permissions.sql            # Enforces temloom_core_rw, temloom_copilot_ro (SELECT-only), and temloom_audit_append
│
├── keys/                                            # Cryptographic Verification Keys (Private Keys Kept Offline)
│   ├── temloom_model_key.pub.pem                    # Ed25519 public key for verifying signed model weights & air-gap compliance reports
│   └── temloom_approver_keys.pub.json               # Registered NOC_APPROVER Ed25519 public keys for Stage 4 2PC approvals
│
├── knowledge_base/                                  # Offline Hybrid RAG Corpus (Indexed into rag_knowledge_chunks)
│   ├── runbooks/                                    # Collection 1: Static Markdown Runbooks (chunked semantically by ## headings)
│   │   ├── RB-100_topology_and_vrf_reference.md     # Multi-site nodes, interfaces, SRLGs, VRFs, and SLA classes
│   │   ├── RB-101_link_congestion_and_qos.md        # M/M/1/K queue saturation, DSCP shaping, and bulk traffic steering
│   │   ├── RB-102_mpls_bgp_ospf_flap_recovery.md    # RFC 2439 route-flap damping, BGP local-preference, and OSPF SPF storms
│   │   ├── RB-103_ipsec_rekey_and_antireplay.md     # StrongSwan IKEv2 CREATE_CHILD_SA rekey exhaustion & RFC 4303 replay drops
│   │   ├── RB-104_sdwan_policy_drift_rollback.md    # Controller AAR policy hash verification and golden config restoration
│   │   └── RB-105_srlg_ambiguity_disambiguation.md  # Out-of-band SNMPv3 hub polling for indistinguishable SRLG vs. WAN faults
│   └── verified_incidents/                          # Collection 2: Dynamic Operator-Accepted Incident Precedents
│       └── accepted_incidents.jsonl                 # Synced from PostgreSQL where operator_feedback == 'ACCEPTED'
│
├── saved_models/                                    # Offline Model Weights, Conformal Calibration Bundles & Ed25519 Signatures
│   ├── model_g1_congestion_v4_1.json                # Model G1 parameters & initial conformal residual quantiles (.sig alongside)
│   ├── model_g2_routing_v4_1.json                   # Model G2 Hawkes + CUSUM parameters (.sig alongside)
│   ├── model_g3_tunnel_v4_1.json                    # Model G3 Survival + IKEv2 rekey hazard parameters (.sig alongside)
│   ├── model_g4_policy_v4_1.json                    # Model G4 Policy-drift & NetFlow DSCP verifier rules (.sig alongside)
│   ├── candidate_baselines/                         # Fitted weights for candidate models (Hist-GBDT, BiLSTM+Attention, RF, IF)
│   ├── embeddings/
│   │   └── bge-small-en-v1.5.onnx                   # Local 384-dim ONNX embedding model (+ .sig)
│   └── llm_gguf/
│       └── Qwen2.5-3B-Instruct-Q4_K_M.gguf          # Local quantized GGUF weight file (+ .sig)
│
├── datasets/                                        # Versioned Air-Gapped Parquet Datasets & Manifests
│   ├── dataset_manifest.json                        # SHA-256 hashes, seed splits, row counts, and schema version
│   └── parquet/                                     # Exported Parquet partitions for Schemas 1–12
│
├── temloom/                                         # Core Python Application Package
│   ├── __init__.py
│   ├── core/                                        # Phase 2: Canonical Schemas, Taxonomy & Config
│   │   ├── __init__.py
│   │   ├── taxonomy.py                              # Single source of truth: fault enums, service_sla_tag, & hard-locked Autonomy Matrix
│   │   ├── schemas.py                               # Pydantic v2 models enforcing Schemas 1–15 contracts
│   │   └── database.py                              # PostgreSQL 16 (asyncpg/psycopg) & VictoriaMetrics client pools (127.0.0.1 IPv4)
│   │
│   ├── simulation/                                  # Phase 1: Physics-Coupled Simulator & Fault Injection
│   │   ├── __init__.py
│   │   ├── simulator.py                             # Multi-layer MPLS/SD-WAN traffic, M/M/1/K queue, BGP/OSPF, & IPSec physics engine
│   │   ├── traffic_generator.py                     # iperf3 Containerlab CE-to-CE flow generator + synthetic fallback
│   │   ├── fault_injector.py                        # Out-of-band scenario fault injector writing exclusively to Schemas 11 & 12
│   │   └── fault_streamer.py                        # Natural fault-timing state machine (QUIET -> FAULT_BURST -> RESOLVE)
│   │
│   ├── ingestion/                                   # Phase 2: 5-Source Telemetry Collectors, Parsers & Replay
│   │   ├── __init__.py
│   │   ├── exporter.py                              # Threaded SNMPv3 / IF-MIB / FRR / 10-burst ICMP RTT & jitter exporter
│   │   ├── collector.py                             # Async multi-source normalizer aligning records to 15s causal buckets
│   │   ├── syslog_parser.py                         # Dual-format parser (FRR native logs + RFC 5424 %BGP-5-ADJCHANGE / OSPF)
│   │   ├── netflow_simulator.py                     # NetFlow v9 / IPFIX 5-tuple DSCP flow collector & simulator
│   │   ├── sdwan_adapters.py                        # Pluggable SDWANControllerAdapter (TEMLOOM_NATIVE, CISCO_VMANAGE, GENERIC_YANG)
│   │   ├── freshness_gate.py                        # 64-bit counter-wrap clamp, NULL preservation, & 45s STALE_TELEMETRY gate
│   │   └── replay_engine.py                         # Deterministic 1x–100x historical Parquet/DB stream replay engine
│   │
│   ├── prediction/                                  # Phase 3: Quad-Domain Predictive Engine, Conformal & Digital Twin
│   │   ├── __init__.py
│   │   ├── features.py                              # Strictly causal rolling feature extractor (zero access to Schemas 11 & 12)
│   │   ├── model_g1_congestion.py                   # Model G1: Decoupled 3-channel link congestion, RTT drift & QoS queue drops
│   │   ├── model_g2_routing.py                      # Model G2: Self-exciting Hawkes BGP flap + RFC 2439 penalty + CUSUM asymmetry
│   │   ├── model_g3_tunnel.py                       # Model G3: IPSec Child-SA survival, IKEv2 DH rekey & anti-replay exhaustion
│   │   ├── model_g4_policy.py                       # Model G4: SD-WAN controller policy-hash drift & AAR DSCP verifier
│   │   ├── conformal_aggregator.py                  # Direct 10m split conformal calibrator (90% bounds + 16-step Bounded Freeze TTL)
│   │   ├── digital_twin.py                          # Holt-Winters / kinematic trend forecast vs. NetworkX graph flow divergence
│   │   └── corroborator.py                          # Dual-Engine Corroboration Gate (engines_agree safety trip logic)
│   │
│   ├── rca/                                         # Phase 5: 4-Layer DAG Root-Cause Analysis & Clonal Counterfactuals
│   │   ├── __init__.py
│   │   ├── topology_graph.py                        # 4-layer dependency graph (L1 Interface <-> L2 SRLG/MPLS <-> L3 Tunnel <-> L4 Service)
│   │   ├── graph_model.py                           # Clonal State-Space Counterfactual Search (BASELINE / REROUTED / QOS_THROTTLED) & LSP health
│   │   ├── equivalence_ranker.py                    # EquivalenceAwareSRLGRanker + AMBIGUOUS_CAUSE_SET detector (|Delta Phi| < 0.08)
│   │   └── prioritiser.py                           # Deterministic incident priority scorer P_incident in [0, 100]
│   │
│   ├── copilot/                                     # Phase 4 & 5: Offline Hybrid RAG, Sandboxed LLM & Multi-Turn NLQ
│   │   ├── __init__.py
│   │   ├── sanitizer.py                             # Prompt-injection & control-token stripper for untrusted syslog/RAG text
│   │   ├── ikb_manager.py                           # Dual-collection IKB manager (##-chunked runbooks + ACCEPTED verified_incidents)
│   │   ├── rag_indexer.py                           # ONNX bge-small-en-v1.5 384-dim embedder + PostgreSQL pgvector/tsvector indexer
│   │   ├── rag_retriever.py                         # Filtered Reciprocal Rank Fusion (RRF, k=20) hybrid retriever
│   │   ├── copilot_response.gbnf                    # Strict GBNF grammar enforcing Q1/Q2/Q3 JSON schema & citations
│   │   ├── llm_client.py                            # UNIX-socket (/run/temloom/llm.sock) llama.cpp client + Post-Gen SQL Citation Verifier + Jinja2 Fallback
│   │   └── nlq_interface.py                         # Stateful multi-turn NLQ engine (IDLE -> CLARIFY -> CONFIRM -> SIMULATE/REPORT)
│   │
│   ├── remediation/                                 # Phase 5: 4-Stage Pre-Change Safety Gate, Feedback & 2PC Executor
│   │   ├── __init__.py
│   │   ├── playbooks.py                             # Parameterized CLI/NETCONF remediation & inverse rollback templates
│   │   ├── safety_engine.py                         # Stage 1 AST Allowlist, Stage 2 SERIALIZABLE Lease (<=80%), Stage 3 M/M/1/K + Batfish, Stage 4 Freshness/Ambiguity
│   │   ├── executor_2pc.py                          # Paired-router 2PC (commit confirmed 1), 45s post-change verifier, <5s auto-rollback, & stdout capture
│   │   └── feedback_cli.py                          # Operator Accept/Reject feedback processor & per-class false-positive rate calculator
│   │
│   ├── security/                                    # Phase 3 & 4: Defense-Grade Cryptographic Attestation & Audit Chain
│   │   ├── __init__.py
│   │   ├── model_integrity.py                       # Ed25519 model weight & artifact signer/verifier (--sign / --verify)
│   │   ├── airgap_compliance.py                     # Active zero-egress canary probe (8.8.8.8, pypi.org, etc.) + Ed25519-signed compliance report
│   │   └── audit_ledger.py                          # Append-only SHA-256 hash-chained audit writer & chain verifier
│   │
│   └── api_ui/                                      # Phase 5: FastAPI Backend & 5-Workbench Operator/Engineering GUI
│       ├── __init__.py
│       ├── app.py                                   # FastAPI application, REST endpoints (/api/v1/*), WebSocket streams (/ws/*), & RBAC middleware
│       ├── templates/                               # Server-rendered Jinja2 + HTMX templates (100% local assets)
│       │   ├── base.html                            # Top Sovereign Status Bar (Signed Air-Gap & Ed25519 badges) + 5-Workbench Navigation Rail
│       │   ├── workbench1_noc_console.html          # Q1/Q2/Q3 header, Conformal Fan, 4-Layer DAG + Time-Travel Slider, 2PC Gate, & Policy Matrix Drawer
│       │   ├── workbench2_telemetry_pipeline.html   # 5-source collector health, throughput, freshness/NULL matrix, DLQ, & Parquet export
│       │   ├── workbench3_simulation_manager.html   # Scenario & Natural Streamer configurator, seed lock, 1x–100x scrubber, & GT vs. Pred timeline
│       │   ├── workbench4_model_registry.html       # Models G1–G4 registry, Ed25519 badges, Conformal Freeze TTL, Feedback FP stats, & 10-Model Comparator
│       │   ├── workbench5_rag_copilot.html          # LLM sandbox status, Signed Air-Gap card, Dual-Collection IKB stats, Sanitizer log, & Multi-Turn NLQ
│       │   └── copilot_fallback_brief.j2            # Deterministic Q1/Q2/Q3 Jinja2 fallback template when llama-server is offline
│       └── static/                                  # 100% Self-Hosted CSS, JS, Local Fonts (Inter, JetBrains Mono) & SVG Icons (Zero CDN)
│           ├── css/
│           ├── js/
│           └── fonts/
│
├── benchmarks/                                      # Phase 3 & 6: Reproducible Evaluation & Model Zoo Benchmark Harness
│   ├── run_all_benchmarks.py                        # Master runner executing all 320 held-out/adversarial runs & checking GATE-01..11
│   ├── train_and_evaluate.py                        # Leakage-free training (Seeds 101..105), calibration (201..205), & held-out evaluation (301..310)
│   ├── hostile_audit_suite.py                       # Adversarial evaluation across unseen fault families ADV-1..8 (Seeds 401..410)
│   ├── tri_domain_and_rag_benchmarks.py             # Domain B (Routing R1..R6), Domain C (Tunnel T1..T6), 30-query RAG Recall@3, & 10-case prompt injection
│   ├── full_model_zoo_and_scenario_d_benchmark.py   # 10-Model Family x 8-Task benchmark comparator & Scenario D Policy Drift verifier
│   └── results/                                     # Generated JSON/Markdown benchmark artifacts
│       ├── tri_domain_results.json
│       └── extended_model_zoo_results.json
│
└── tests/                                           # Automated Unit, Integration, Security & End-to-End Scenario Tests
    ├── conftest.py                                  # Shared fixtures, isolated test DB/simulator setup
    ├── test_schemas_and_taxonomy.py                 # Validates all 15 Pydantic/SQL schemas & taxonomy.py hard-locked safety floors
    ├── test_telemetry_and_freshness.py              # Tests 15s causal alignment, 64-bit counter wrap, NULL preservation, & STALE_TELEMETRY
    ├── test_models_and_conformal.py                 # Tests Models G1–G4, 90% conformal coverage, Bounded Freeze TTL, & Digital Twin corroboration
    ├── test_rca_and_clonal_search.py                # Tests 4-layer DAG ranking, AMBIGUOUS_CAUSE_SET guardrails, & Clonal Counterfactual search
    ├── test_rag_sanitizer_and_nlq.py                # Tests 10/10 prompt-injection block rate, Dual-Collection RRF, GBNF Q1/Q2/Q3, & Deterministic Fallback
    ├── test_safety_and_2pc_rollback.py              # Tests AST allowlist, concurrent SERIALIZABLE TOCTOU leases, Batfish loop block, & <5s 2PC auto-rollback
    ├── test_security_and_airgap.py                  # Tests Ed25519 model_integrity.py verification, airgap_compliance.py canary probes, & SHA-256 audit chain
    └── test_temloom_complete.py                     # End-to-end integration suite verifying all 9 mandatory operational scenarios (Scenarios A–I)
```
