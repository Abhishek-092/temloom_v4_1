#!/usr/bin/env python3
"""
temloom/ingestion/sdwan_adapters.py — Pluggable Multi-Vendor SD-WAN Controller Adapters
(TEMLOOM_NATIVE, CISCO_VMANAGE, GENERIC_YANG) normalizing controller health, AAR tunnel
selection, and policy-hash drift into Schema 9 and Schema 10 (DS-1.1D).
"""

import hashlib
import time
import uuid
from typing import Tuple
from temloom.core.schemas import Schema9SdwanControllerEvent, Schema10ConfigPolicyChange

GOLDEN_POLICY_STANZA = (
    "policy AAR-VOICE-GOLD\n"
    " match dscp EF set tunnel br1:ce-br1:tunnel:tun-br1-mpls\n"
    " match dscp AF21 set tunnel br1:ce-br1:tunnel:tun-br1-inet\n"
)
GOLDEN_POLICY_HASH = hashlib.sha256(GOLDEN_POLICY_STANZA.encode("utf-8")).hexdigest()


class SDWANControllerAdapter:
    """Base pluggable adapter normalizing controller telemetry into Schemas 9 & 10."""

    def __init__(self, driver_name: str = "TEMLOOM_NATIVE"):
        if driver_name not in ("TEMLOOM_NATIVE", "CISCO_VMANAGE", "GENERIC_YANG"):
            raise ValueError(f"Unsupported SD-WAN driver: {driver_name}")
        self.driver_name = driver_name
        self.active_policy_stanza = GOLDEN_POLICY_STANZA

    def inject_policy_drift(self, misconfigured_tunnel: str = "br1:ce-br1:tunnel:tun-br1-inet"):
        self.active_policy_stanza = (
            f"policy AAR-VOICE-GOLD\n"
            f" match dscp EF set tunnel {misconfigured_tunnel}\n"
            f" match dscp AF21 set tunnel {misconfigured_tunnel}\n"
        )

    def restore_golden_policy(self):
        self.active_policy_stanza = GOLDEN_POLICY_STANZA

    def poll_controller(self, bucket_15s_utc_ms: int = None) -> Tuple[Schema9SdwanControllerEvent, Schema10ConfigPolicyChange]:
        now_ms = int(time.time() * 1000)
        b_ms = bucket_15s_utc_ms or ((now_ms // 15000) * 15000)
        active_hash = hashlib.sha256(self.active_policy_stanza.encode("utf-8")).hexdigest()
        is_drift = active_hash != GOLDEN_POLICY_HASH
        selected_tun = "br1:ce-br1:tunnel:tun-br1-inet" if is_drift else "br1:ce-br1:tunnel:tun-br1-mpls"

        s9 = Schema9SdwanControllerEvent(
            event_uuid=str(uuid.uuid4()),
            bucket_15s_utc_ms=b_ms,
            entity_canonical_id="global:sdwan:controller:ctrl-1",
            adapter_driver=self.driver_name,
            controller_health="HEALTHY",
            connected_sites_cnt=4,
            aar_policy_name="AAR-VOICE-GOLD",
            selected_tunnel_id=selected_tun,
            aar_decision_reason="POLICY_DRIFT" if is_drift else "SLA_COMPLIANT",
            policy_drift_detected=is_drift,
        )

        diff_txt = (
            "- match dscp EF set tunnel br1:ce-br1:tunnel:tun-br1-mpls | + match dscp EF set tunnel br1:ce-br1:tunnel:tun-br1-inet"
            if is_drift
            else "# No policy diff vs golden baseline"
        )
        s10 = Schema10ConfigPolicyChange(
            change_id=str(uuid.uuid4()),
            observed_at_utc_ms=min(now_ms, b_ms),
            bucket_15s_utc_ms=b_ms,
            entity_canonical_id="global:sdwan:controller:ctrl-1",
            actor_identity="manual_cli_admin" if is_drift else "TEMLOOM_BASELINE",
            golden_config_sha256=GOLDEN_POLICY_HASH,
            active_config_sha256=active_hash,
            is_unintended_drift=is_drift,
            unified_diff_text=diff_txt,
        )
        return s9, s10
