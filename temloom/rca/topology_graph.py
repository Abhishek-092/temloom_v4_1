#!/usr/bin/env python3
"""
temloom/rca/topology_graph.py — 4-Layer Network Dependency DAG (L1 Physical Interface
<-> L2 Carrier SRLG / MPLS Underlay <-> L3 IPSec/GRE Overlay Tunnel <-> L4 Application Service).
"""

from typing import Dict, Any, List


class FourLayerTopologyDAG:
    """Canonical 4-Layer Multi-Site MPLS + SD-WAN Dependency Graph."""

    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {
            # Layer 1: Physical Router Interfaces
            "hub1:ce-hub1:iface:wan0": {"layer": "L1_INTERFACE", "site": "ce-hub", "role": "hub_wan", "capacity_mbps": 100.0},
            "br1:ce-br1:iface:eth0": {"layer": "L1_INTERFACE", "site": "ce-branch1", "role": "branch_wan", "capacity_mbps": 50.0},
            "br2:ce-br2:iface:eth0": {"layer": "L1_INTERFACE", "site": "ce-branch2", "role": "branch_wan", "capacity_mbps": 50.0},
            "core:pe1:iface:eth1": {"layer": "L1_INTERFACE", "site": "pe1", "role": "provider_edge", "capacity_mbps": 100.0},
            "core:p1:iface:eth1": {"layer": "L1_INTERFACE", "site": "p1", "role": "provider_core", "capacity_mbps": 100.0},
            "core:pe2:iface:eth1": {"layer": "L1_INTERFACE", "site": "pe2", "role": "provider_edge", "capacity_mbps": 100.0},
            # Layer 2: MPLS Core Links & Shared-Risk Link Groups (SRLG)
            "core:mpls:link:mpls-link-mab-1": {"layer": "L2_MPLS_LINK", "site": "core", "role": "mpls_underlay", "capacity_mbps": 100.0},
            "core:mpls:srlg:transport-A-hub1": {"layer": "L2_CARRIER_SRLG", "site": "core", "role": "srlg_conduit", "capacity_mbps": 100.0},
            # Layer 3: IPSec / SD-WAN Overlay Tunnels & BGP Peers
            "br1:ce-br1:tunnel:tun-br1": {"layer": "L3_OVERLAY_TUNNEL", "site": "ce-branch1", "underlay": "core:mpls:srlg:transport-A-hub1"},
            "br1:ce-br1:tunnel:tun-br1-backup": {"layer": "L3_OVERLAY_TUNNEL", "site": "ce-branch1", "underlay": "inet-broadband-b"},
            "br2:ce-br2:tunnel:tun-br2": {"layer": "L3_OVERLAY_TUNNEL", "site": "ce-branch2", "underlay": "core:mpls:srlg:transport-A-hub1"},
            "br1:ce-br1:bgp_peer:10.255.0.2": {"layer": "L3_BGP_PEER", "site": "ce-branch1", "underlay": "core:mpls:link:mpls-link-mab-1"},
            "global:sdwan:controller:ctrl-1": {"layer": "L3_SDWAN_CONTROLLER", "site": "global", "underlay": "mgmt-plane"},
            # Layer 4: Critical Enterprise & Defence Services
            "br1:service:voip_rtp": {"layer": "L4_SERVICE", "sla_tag": "voip", "dscp": "EF"},
            "br2:service:video_conf": {"layer": "L4_SERVICE", "sla_tag": "video", "dscp": "AF41"},
            "br1:service:erp_sql": {"layer": "L4_SERVICE", "sla_tag": "database", "dscp": "AF21"},
            "br2:service:bulk_backup": {"layer": "L4_SERVICE", "sla_tag": "bulk", "dscp": "BE"},
        }

        # Directed causal dependencies: parent (upstream cause) -> list of downstream victims
        self.children_map: Dict[str, List[str]] = {
            "core:mpls:srlg:transport-A-hub1": [
                "hub1:ce-hub1:iface:wan0",
                "core:mpls:link:mpls-link-mab-1",
                "br1:ce-br1:tunnel:tun-br1",
                "br2:ce-br2:tunnel:tun-br2",
                "br1:service:voip_rtp",
                "br2:service:video_conf",
                "br1:service:erp_sql",
            ],
            "hub1:ce-hub1:iface:wan0": [
                "br1:ce-br1:tunnel:tun-br1",
                "br2:ce-br2:tunnel:tun-br2",
                "br1:service:voip_rtp",
                "br2:service:video_conf",
            ],
            "core:mpls:link:mpls-link-mab-1": [
                "br1:ce-br1:tunnel:tun-br1",
                "br1:ce-br1:bgp_peer:10.255.0.2",
                "br1:service:voip_rtp",
                "br1:service:erp_sql",
            ],
            "br1:ce-br1:bgp_peer:10.255.0.2": [
                "br1:ce-br1:tunnel:tun-br1",
                "br1:service:voip_rtp",
            ],
            "br1:ce-br1:tunnel:tun-br1": [
                "br1:service:voip_rtp",
                "br1:service:erp_sql",
            ],
            "global:sdwan:controller:ctrl-1": [
                "br1:ce-br1:tunnel:tun-br1",
                "br1:service:voip_rtp",
            ],
        }

    def get_blast_radius(self, root_entity_id: str) -> List[str]:
        return self.children_map.get(root_entity_id, ["br1:service:voip_rtp"])

    def to_svg_topology_dict(self) -> Dict[str, Any]:
        return {
            "nodes": [{"id": k, **v} for k, v in self.nodes.items()],
            "edges": [
                {"source": parent, "target": child}
                for parent, children in self.children_map.items()
                for child in children
            ],
        }
