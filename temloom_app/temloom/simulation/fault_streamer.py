#!/usr/bin/env python3
"""
temloom/simulation/fault_streamer.py — Natural Fault-Timing State Machine
(QUIET -> FAULT_BURST -> RESOLVE) adopted from Project Aether (DS-1.1E) and wired
into TEMLOOM's Quad-Domain Core Engine, Digital Twin, 4-Layer DAG RCA, and DB.
"""

import argparse
import random
import time
from typing import Dict, Any, List, Optional
from temloom.core.taxonomy import FAULTS, LABEL_TO_ID


class NaturalFaultStreamer:
    """
    State Machine:
      - QUIET: Emits healthy baseline heartbeats (every 35-80s in live mode)
      - FAULT_BURST: Emits 2-5 consecutive escalating precursor steps of a selected fault class
      - RESOLVE: Emits 1-2 post-remediation recovery steps before returning to QUIET
    """

    FAULT_TYPES = ["rate", "flap", "loss", "latency", "policy_drift", "corrupt"]
    FAULT_WEIGHTS = [0.25, 0.25, 0.20, 0.15, 0.10, 0.05]

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.state = "QUIET"
        self.active_fault: Optional[str] = None
        self.burst_remaining = 0

    def next_event_spec(self, forced_fault: Optional[str] = None) -> Dict[str, Any]:
        if forced_fault:
            self.state = "FAULT_BURST"
            self.active_fault = forced_fault
            self.burst_remaining = 1
            return self._build_fault_step(forced_fault, step_in_burst=1)

        if self.state == "QUIET":
            # Transition to FAULT_BURST
            self.state = "FAULT_BURST"
            self.active_fault = self.rng.choices(self.FAULT_TYPES, weights=self.FAULT_WEIGHTS, k=1)[0]
            self.burst_remaining = self.rng.randint(2, 4)
            return self._build_fault_step("Healthy", step_in_burst=0)

        if self.state == "FAULT_BURST":
            fault = self.active_fault or "rate"
            step_idx = 5 - self.burst_remaining
            self.burst_remaining -= 1
            if self.burst_remaining <= 0:
                self.state = "RESOLVE"
            return self._build_fault_step(fault, step_in_burst=step_idx)

        # RESOLVE state
        self.state = "QUIET"
        self.active_fault = None
        return self._build_fault_step("Healthy", step_in_burst=0)

    def _build_fault_step(self, label: str, step_in_burst: int) -> Dict[str, Any]:
        mapping = {
            "Healthy": {
                "entity_canonical_id": "core:mpls:link:mpls-link-mab-1",
                "issue_category": "NORMAL",
                "utilization_mbps": 58.0,
                "rtt_mean_ms": 11.2,
                "queue_drops_pps": 0.0,
                "estimated_tti_min": None,
                "anomaly_score": 0.08,
            },
            "rate": {
                "entity_canonical_id": "core:mpls:link:mpls-link-mab-1",
                "issue_category": "LINK_CONGESTION",
                "utilization_mbps": min(94.0, 82.0 + 3.2 * step_in_burst),
                "rtt_mean_ms": min(29.0, 19.5 + 2.4 * step_in_burst),
                "queue_drops_pps": 9.5 + 3.5 * step_in_burst,
                "estimated_tti_min": max(1.5, 7.5 - 1.2 * step_in_burst),
                "anomaly_score": min(0.98, 0.84 + 0.04 * step_in_burst),
            },
            "flap": {
                "entity_canonical_id": "br1:ce-br1:bgp_peer:10.255.0.2",
                "issue_category": "BGP_FLAP_CASCADE",
                "utilization_mbps": 64.0,
                "rtt_mean_ms": 22.4,
                "queue_drops_pps": 4.2,
                "rfc2439_flap_penalty": 750.0 + 280.0 * step_in_burst,
                "hawkes_intensity": 2.45 + 0.45 * step_in_burst,
                "estimated_tti_min": max(1.0, 5.5 - 0.9 * step_in_burst),
                "anomaly_score": min(0.99, 0.89 + 0.03 * step_in_burst),
            },
            "loss": {
                "entity_canonical_id": "br1:ce-br1:tunnel:tun-br1",
                "issue_category": "TUNNEL_REKEY_EXHAUSTION",
                "utilization_mbps": 61.0,
                "rtt_mean_ms": 23.8,
                "queue_drops_pps": 6.0,
                "ike_dh_retries": 3 + step_in_burst,
                "sa_rem_life_min": max(2.8, 8.5 - 1.5 * step_in_burst),
                "estimated_tti_min": max(1.2, 5.25 - 0.8 * step_in_burst),
                "anomaly_score": min(0.97, 0.86 + 0.03 * step_in_burst),
            },
            "latency": {
                "entity_canonical_id": "core:mpls:link:mpls-link-mab-1",
                "issue_category": "LATENCY_DRIFT",
                "utilization_mbps": 54.0,
                "rtt_mean_ms": min(28.5, 21.0 + 2.2 * step_in_burst),
                "queue_drops_pps": 2.1,
                "estimated_tti_min": max(1.5, 8.0 - 1.1 * step_in_burst),
                "anomaly_score": min(0.95, 0.83 + 0.03 * step_in_burst),
            },
            "policy_drift": {
                "entity_canonical_id": "global:sdwan:controller:ctrl-1",
                "issue_category": "POLICY_DRIFT",
                "utilization_mbps": 76.0,
                "rtt_mean_ms": 24.5,
                "queue_drops_pps": 11.2,
                "estimated_tti_min": 4.75,
                "anomaly_score": 0.94,
            },
            "corrupt": {
                "entity_canonical_id": "br1:ce-br1:tunnel:tun-br1",
                "issue_category": "ANTI_REPLAY_OVERFLOW",
                "utilization_mbps": 66.0,
                "rtt_mean_ms": 22.0,
                "queue_drops_pps": 14.0,
                "estimated_tti_min": 5.0,
                "anomaly_score": 0.87,
            },
        }
        spec = dict(mapping.get(label, mapping["Healthy"]))
        spec["fault_label"] = label
        spec["streamer_state"] = self.state
        return spec


def main():
    ap = argparse.ArgumentParser(description="TEMLOOM Natural Fault-Timing State Machine")
    ap.add_argument("--mode", choices=["natural", "cycle"], default="natural")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--inject", choices=NaturalFaultStreamer.FAULT_TYPES + ["Healthy"])
    args = ap.parse_args()

    streamer = NaturalFaultStreamer()
    if args.inject:
        ev = streamer.next_event_spec(forced_fault=args.inject)
        print(f"[+] Injected {args.inject}: {ev}")
        return

    if args.once:
        for f in NaturalFaultStreamer.FAULT_TYPES:
            ev = streamer.next_event_spec(forced_fault=f)
            print(f"[+] Cycle {f}: entity={ev['entity_canonical_id']} cat={ev['issue_category']} TTI={ev['estimated_tti_min']}m")
        return


if __name__ == "__main__":
    main()
