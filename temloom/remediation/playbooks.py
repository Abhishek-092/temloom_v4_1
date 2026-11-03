#!/usr/bin/env python3
"""
temloom/remediation/playbooks.py — Parameterized Forward & Inverse Rollback CLI/NETCONF
Remediation Playbooks (combining TEMLOOM 2PC stanzas).
"""

from typing import Dict, Any, List

PLAYBOOK_CATALOGUE: Dict[str, Dict[str, Any]] = {
    "PB-STEER-BULK-AF21": {
        "action_class": "QOS_SHAPE_QUEUE",
        "title": "Steer AF21/BE Bulk Traffic to Backup Tunnel & Shape Queue 1:30",
        "relieved_links": ["core:mpls:link:mpls-link-mab-1", "pe1-p1", "p-core1:eth1"],
        "target_backup_path": "br1:ce-br1:tunnel:tun-br1-backup",
        "forward_commands": [
            "vtysh -c 'configure terminal' -c 'route-map PB-STEER-BULK-AF21 permit 10' -c 'match ip dscp af21' -c 'set interface tun-br1-backup' -c 'end'",
            "tc class change dev eth2 parent 1:1 classid 1:30 htb rate 1mbit ceil 1mbit prio 2",
        ],
        "rollback_commands": [
            "vtysh -c 'configure terminal' -c 'no route-map PB-STEER-BULK-AF21 permit 10' -c 'end'",
            "tc class change dev eth2 parent 1:1 classid 1:30 htb rate 1mbit ceil 3mbit prio 2",
        ],
    },
    "PB-BGP-LOCALPREF": {
        "action_class": "CORE_PATH_FAILOVER",
        "title": "Shift Primary BGP Local-Preference to Secondary PE2 Path (2PC Paired Commit)",
        "relieved_links": ["br1:ce-br1:bgp_peer:10.255.0.2", "core:mpls:link:mpls-link-mab-1", "p-core1:eth1"],
        "target_backup_path": "br1:ce-br1:tunnel:tun-br1-backup",
        "forward_commands": [
            "vtysh -c 'configure terminal' -c 'route-map RM-PREFER-SECONDARY permit 10' -c 'set local-preference 250' -c 'end'",
            "vtysh -c 'configure terminal' -c 'router bgp 65000 vrf vrf-voice' -c 'neighbor 10.255.0.2 route-map RM-PREFER-SECONDARY in' -c 'end'",
        ],
        "rollback_commands": [
            "vtysh -c 'configure terminal' -c 'router bgp 65000 vrf vrf-voice' -c 'no neighbor 10.255.0.2 route-map RM-PREFER-SECONDARY in' -c 'end'",
        ],
    },
    "PB-TUNNEL-REKEY-STEER": {
        "action_class": "REROUTE_BRANCH",
        "title": "Proactive IKEv2 Child-SA Rekey & Secondary Overlay Pinning",
        "relieved_links": ["br1:ce-br1:tunnel:tun-br1", "core:mpls:srlg:transport-A-hub1"],
        "target_backup_path": "br1:ce-br1:tunnel:tun-br1-backup",
        "forward_commands": [
            "swanctl --rekey --child tun-br1-sa",
            "ip route replace 10.99.0.0/24 dev tun-br1-backup metric 10",
        ],
        "rollback_commands": [
            "ip route replace 10.99.0.0/24 dev tun-br1 metric 10",
        ],
    },
    "PB-ROLLBACK-GOLDEN-POLICY": {
        "action_class": "CONTROLLER_POLICY_ROLLBACK",
        "title": "Rollback SD-WAN Controller Policy AAR-VOICE-GOLD to Golden SHA-256 Baseline",
        "relieved_links": ["global:sdwan:controller:ctrl-1", "br1:ce-br1:tunnel:tun-br1-inet"],
        "target_backup_path": "br1:ce-br1:tunnel:tun-br1-mpls",
        "forward_commands": [
            "sdwan-controller policy rollback AAR-VOICE-GOLD --to-sha256 8f9d2a1c4b7e6051e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934c",
        ],
        "rollback_commands": [
            "sdwan-controller policy status AAR-VOICE-GOLD",
        ],
    },
}


def get_playbook(playbook_id: str) -> Dict[str, Any]:
    return PLAYBOOK_CATALOGUE.get(playbook_id, PLAYBOOK_CATALOGUE["PB-STEER-BULK-AF21"])
