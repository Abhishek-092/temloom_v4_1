#!/usr/bin/env python3
"""
temloom/ingestion/collector.py — Multi-Source Telemetry Collector, Normalizer & Parquet Exporter.
Ingests Schemas 1-10 into TemloomDatabase and exports SHA-256 versioned Parquet/JSONL bundles.
"""

import hashlib
import json
import os
import time
from typing import Dict, Any, List
import pandas as pd

from temloom.core.database import TemloomDatabase
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
)
from temloom.ingestion.freshness_gate import TelemetryFreshnessAndQualityGate

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATASETS_DIR = os.path.join(REPO_ROOT, "datasets")


class MultiSourceTelemetryCollector:
    def __init__(self, db: TemloomDatabase = None):
        self.db = db or TemloomDatabase()
        self.gate = TelemetryFreshnessAndQualityGate(self.db)

    def ingest_interface_metric(self, rec: Schema1InterfaceTelemetry):
        self.db.execute_write(
            """INSERT OR REPLACE INTO interface_telemetry
               (bucket_15s_utc_ms, observed_at_utc_ms, entity_canonical_id, capacity_mbps,
                utilization_mbps, utilization_pct, in_octets_delta, out_octets_delta,
                in_ucast_pkts_delta, out_ucast_pkts_delta, in_errors_delta, out_errors_delta,
                in_discards_delta, out_discards_delta, cpu_load_pct, mem_used_pct,
                optical_rx_dbm, oper_status, is_missing, freshness_state)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                rec.bucket_15s_utc_ms, rec.observed_at_utc_ms, rec.entity_canonical_id,
                rec.capacity_mbps, rec.utilization_mbps, rec.utilization_pct,
                rec.in_octets_delta, rec.out_octets_delta, rec.in_ucast_pkts_delta,
                rec.out_ucast_pkts_delta, rec.in_errors_delta, rec.out_errors_delta,
                rec.in_discards_delta, rec.out_discards_delta, rec.cpu_load_pct,
                rec.mem_used_pct, rec.optical_rx_dbm, rec.oper_status,
                1 if rec.is_missing else 0, rec.freshness_state,
            ),
        )

    def ingest_latency_metric(self, rec: Schema2LatencyJitterTelemetry):
        self.db.execute_write(
            """INSERT OR REPLACE INTO latency_jitter_telemetry
               (bucket_15s_utc_ms, observed_at_utc_ms, entity_canonical_id, rtt_mean_ms,
                rtt_p95_ms, jitter_mean_ms, bfd_echo_var_ms2, packet_loss_pct, is_missing, freshness_state)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                rec.bucket_15s_utc_ms, rec.observed_at_utc_ms, rec.entity_canonical_id,
                rec.rtt_mean_ms, rec.rtt_p95_ms, rec.jitter_mean_ms,
                rec.bfd_echo_var_ms2, rec.packet_loss_pct,
                1 if rec.is_missing else 0, rec.freshness_state,
            ),
        )

    def ingest_qos_metric(self, rec: Schema3QosQueueTelemetry):
        self.db.execute_write(
            """INSERT OR REPLACE INTO qos_queue_telemetry
               (bucket_15s_utc_ms, entity_canonical_id, dscp_class, service_sla_tag,
                queue_depth_pkts, queue_limit_pkts, queue_drops_pps, tx_rate_mbps,
                traffic_share_ratio, is_missing)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                rec.bucket_15s_utc_ms, rec.entity_canonical_id, rec.dscp_class,
                rec.service_sla_tag, rec.queue_depth_pkts, rec.queue_limit_pkts,
                rec.queue_drops_pps, rec.tx_rate_mbps, rec.traffic_share_ratio,
                1 if rec.is_missing else 0,
            ),
        )

    def ingest_bgp_event(self, rec: Schema4BgpProtocolEvent):
        self.db.execute_write(
            """INSERT OR REPLACE INTO bgp_protocol_events
               (event_uuid, observed_at_utc_ms, bucket_15s_utc_ms, entity_canonical_id,
                peer_asn, vrf_name, event_subtype, updates_count_15s, withdraws_count_15s,
                rfc2439_flap_penalty, hawkes_intensity)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                rec.event_uuid, rec.observed_at_utc_ms, rec.bucket_15s_utc_ms,
                rec.entity_canonical_id, rec.peer_asn, rec.vrf_name, rec.event_subtype,
                rec.updates_count_15s, rec.withdraws_count_15s, rec.rfc2439_flap_penalty,
                rec.hawkes_intensity,
            ),
        )

    def ingest_ospf_event(self, rec: Schema5OspfProtocolEvent):
        self.db.execute_write(
            """INSERT OR REPLACE INTO ospf_protocol_events
               (event_uuid, observed_at_utc_ms, bucket_15s_utc_ms, entity_canonical_id,
                ospf_area, adj_state, lsa_updates_15s, spf_runs_15s, convergence_time_ms)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                rec.event_uuid, rec.observed_at_utc_ms, rec.bucket_15s_utc_ms,
                rec.entity_canonical_id, rec.ospf_area, rec.adj_state,
                rec.lsa_updates_15s, rec.spf_runs_15s, rec.convergence_time_ms,
            ),
        )

    def ingest_syslog_event(self, rec: Schema6SyslogEvent):
        self.db.execute_write(
            """INSERT OR REPLACE INTO syslog_events
               (syslog_uuid, observed_at_utc_ms, bucket_15s_utc_ms, entity_canonical_id,
                facility_program, severity_level, mnemonic_code, sanitized_message)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                rec.syslog_uuid, rec.observed_at_utc_ms, rec.bucket_15s_utc_ms,
                rec.entity_canonical_id, rec.facility_program, rec.severity_level,
                rec.mnemonic_code, rec.sanitized_message,
            ),
        )

    def ingest_netflow_record(self, rec: Schema7NetflowIpfixRecord):
        self.db.execute_write(
            """INSERT OR REPLACE INTO netflow_ipfix_records
               (flow_record_id, bucket_15s_utc_ms, entity_canonical_id, src_subnet_prefix,
                dst_subnet_prefix, ip_protocol, dscp_value, app_class, service_sla_tag,
                direction, bytes_delta, packets_delta, flow_duration_ms, path_asymmetry_ratio)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                rec.flow_record_id, rec.bucket_15s_utc_ms, rec.entity_canonical_id,
                rec.src_subnet_prefix, rec.dst_subnet_prefix, rec.ip_protocol,
                rec.dscp_value, rec.app_class, rec.service_sla_tag, rec.direction,
                rec.bytes_delta, rec.packets_delta, rec.flow_duration_ms, rec.path_asymmetry_ratio,
            ),
        )

    def ingest_tunnel_metric(self, rec: Schema8IpsecTunnelTelemetry):
        self.db.execute_write(
            """INSERT OR REPLACE INTO ipsec_tunnel_telemetry
               (bucket_15s_utc_ms, entity_canonical_id, underlay_path_id, tunnel_state,
                lsp_health_score, availability_pct, tunnel_rtt_ms, tunnel_jitter_ms,
                esp_seq_loss_pct, replay_drops_pps, ike_rekey_lat_ms, ike_dh_retries,
                sa_rem_life_min, is_missing)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                rec.bucket_15s_utc_ms, rec.entity_canonical_id, rec.underlay_path_id,
                rec.tunnel_state, rec.lsp_health_score, rec.availability_pct,
                rec.tunnel_rtt_ms, rec.tunnel_jitter_ms, rec.esp_seq_loss_pct,
                rec.replay_drops_pps, rec.ike_rekey_lat_ms, rec.ike_dh_retries,
                rec.sa_rem_life_min, 1 if rec.is_missing else 0,
            ),
        )

    def ingest_sdwan_event(self, rec: Schema9SdwanControllerEvent):
        self.db.execute_write(
            """INSERT OR REPLACE INTO sdwan_controller_events
               (event_uuid, bucket_15s_utc_ms, entity_canonical_id, adapter_driver,
                controller_health, connected_sites_cnt, aar_policy_name,
                selected_tunnel_id, aar_decision_reason, policy_drift_detected)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                rec.event_uuid, rec.bucket_15s_utc_ms, rec.entity_canonical_id,
                rec.adapter_driver, rec.controller_health, rec.connected_sites_cnt,
                rec.aar_policy_name, rec.selected_tunnel_id, rec.aar_decision_reason,
                1 if rec.policy_drift_detected else 0,
            ),
        )

    def ingest_config_change(self, rec: Schema10ConfigPolicyChange):
        self.db.execute_write(
            """INSERT OR REPLACE INTO config_policy_changes
               (change_id, observed_at_utc_ms, bucket_15s_utc_ms, entity_canonical_id,
                actor_identity, golden_config_sha256, active_config_sha256,
                is_unintended_drift, unified_diff_text)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                rec.change_id, rec.observed_at_utc_ms, rec.bucket_15s_utc_ms,
                rec.entity_canonical_id, rec.actor_identity, rec.golden_config_sha256,
                rec.active_config_sha256, 1 if rec.is_unintended_drift else 0,
                rec.unified_diff_text,
            ),
        )

    def export_parquet_snapshot(self, version_tag: str = "v4.1.0") -> Dict[str, Any]:
        """Exports tables to Parquet/CSV in datasets/parquet/ and writes SHA-256 dataset_manifest.json."""
        parquet_dir = os.path.join(DATASETS_DIR, "parquet")
        os.makedirs(parquet_dir, exist_ok=True)
        tables = [
            "interface_telemetry",
            "latency_jitter_telemetry",
            "qos_queue_telemetry",
            "bgp_protocol_events",
            "ospf_protocol_events",
            "syslog_events",
            "netflow_ipfix_records",
            "ipsec_tunnel_telemetry",
            "sdwan_controller_events",
            "config_policy_changes",
            "injected_fault_records",
            "ground_truth_incident_labels",
        ]
        manifest_files = {}
        total_rows = 0
        combined_hash = hashlib.sha256()

        for tbl in tables:
            rows = self.db.execute_query(f"SELECT * FROM {tbl}")
            df = pd.DataFrame(rows)
            total_rows += len(df)
            csv_path = os.path.join(parquet_dir, f"{tbl}.csv")
            df.to_csv(csv_path, index=False)
            try:
                pq_path = os.path.join(parquet_dir, f"{tbl}.parquet")
                df.to_parquet(pq_path, index=False)
                target_file = pq_path
            except Exception:
                target_file = csv_path

            with open(target_file, "rb") as bf:
                fhash = hashlib.sha256(bf.read()).hexdigest()
            combined_hash.update(fhash.encode("utf-8"))
            manifest_files[tbl] = {
                "file": os.path.basename(target_file),
                "rows": len(df),
                "sha256": fhash,
            }

        dataset_sha = combined_hash.hexdigest()[:16]
        manifest = {
            "dataset_version_id": f"{version_tag}-sha256:{dataset_sha}",
            "exported_at_utc_ms": int(time.time() * 1000),
            "total_rows": total_rows,
            "seed_splits": {
                "train": [101, 102, 103, 104, 105],
                "validation_calibration": [201, 202, 203, 204, 205],
                "held_out_test": list(range(301, 311)),
                "adversarial_unseen": list(range(401, 411)),
            },
            "tables": manifest_files,
        }
        manifest_path = os.path.join(DATASETS_DIR, "dataset_manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        return manifest
