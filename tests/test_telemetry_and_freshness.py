#!/usr/bin/env python3
from temloom.ingestion.freshness_gate import TelemetryFreshnessAndQualityGate, UINT64_MAX
from temloom.ingestion.syslog_parser import SyslogParser
from temloom.ingestion.sdwan_adapters import SDWANControllerAdapter
from temloom.ingestion.collector import MultiSourceTelemetryCollector
from temloom.core.schemas import Schema1InterfaceTelemetry


def test_counter_wrap_and_missingness_gate(temp_db):
    gate = TelemetryFreshnessAndQualityGate(temp_db)
    # 64-bit counter wrap across UINT64_MAX
    delta, clamped = gate.compute_counter_delta(UINT64_MAX - 1000, 500)
    assert delta == 1501
    assert clamped is True

    # Missing poll preserves None (never silently zero-fills) and transitions to STALE_TELEMETRY after 3 misses
    v1, m1, s1 = gate.evaluate_freshness("hub1:ce-hub1:iface:wan0", None)
    v2, m2, s2 = gate.evaluate_freshness("hub1:ce-hub1:iface:wan0", None)
    v3, m3, s3 = gate.evaluate_freshness("hub1:ce-hub1:iface:wan0", None)
    assert v1 is None and m1 is True and s1 == "DEGRADED_POLLING"
    assert v3 is None and m3 is True and s3 == "STALE_TELEMETRY"


def test_dual_format_syslog_parser():
    parser = SyslogParser()
    e1 = parser.parse_line("2026/06/28 12:00:00 BGP: 10.0.0.2 went from Established to Idle")
    e2 = parser.parse_line("Jun 28 12:00:02 frr bgpd: %BGP-5-ADJCHANGE: neighbor 10.0.0.1 Down")
    assert e1 is not None and e1["type"] == "bgp_neighbor_down"
    assert e2 is not None and e2["type"] == "bgp_neighbor_down"


def test_sdwan_adapter_and_parquet_export(temp_db):
    adapter = SDWANControllerAdapter("TEMLOOM_NATIVE")
    s9_nom, s10_nom = adapter.poll_controller(1793545200000)
    assert s9_nom.policy_drift_detected is False

    adapter.inject_policy_drift()
    s9_drift, s10_drift = adapter.poll_controller(1793545200000)
    assert s9_drift.policy_drift_detected is True
    assert s10_drift.is_unintended_drift is True

    coll = MultiSourceTelemetryCollector(temp_db)
    coll.ingest_interface_metric(Schema1InterfaceTelemetry(
        bucket_15s_utc_ms=1793545200000, observed_at_utc_ms=1793545199000,
        entity_canonical_id="hub1:ce-hub1:iface:wan0", capacity_mbps=100.0, utilization_mbps=82.0
    ))
    coll.ingest_sdwan_event(s9_drift)
    coll.ingest_config_change(s10_drift)
    manifest = coll.export_parquet_snapshot()
    assert "dataset_version_id" in manifest
    assert manifest["total_rows"] >= 3
