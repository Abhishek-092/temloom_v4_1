# RB-100: TEMLOOM Multi-Site MPLS & SD-WAN Topology Reference

## Site Layout & Node Roles
- `pe1` (Provider Edge 1, AS 65000, VRF CUST / vrf-voice / vrf-data, Mgmt IP 172.20.20.2)
- `p1` (Provider Core P-Router, AS 65000, LDP Label Switch Router, Mgmt IP 172.20.20.4)
- `pe2` (Provider Edge 2, AS 65000, VRF CUST, Mgmt IP 172.20.20.3)
- `ce-hub` / `ce-hub1` (Customer Edge Hub Router, AS 65003, `hub1:ce-hub1:iface:wan0` 100 Mbps)
- `ce-branch1` / `ce-br1` (Customer Edge Branch 1, AS 65001, `br1:ce-br1:iface:eth0` 50 Mbps)
- `ce-branch2` / `ce-br2` (Customer Edge Branch 2, AS 65002, `br2:ce-br2:iface:eth0` 50 Mbps)
- `ce-dc` (Customer Edge Data Center, AS 65004, `dc:ce-dc:iface:eth0` 100 Mbps)

## Critical SLA Paths & Per-Service Thresholds
- VoIP (`voip_rtp`, DSCP EF 46): `ce-branch1 -> pe1 -> p1 -> pe2 -> ce-dc` (Max RTT: 30.0 ms, Max Jitter: 15.0 ms, Max Loss: 0.5%)
- Video (`video_conf`, DSCP AF41 34): `ce-branch2 -> pe2 -> p1 -> pe1 -> ce-hub` (Max RTT: 50.0 ms, Max Jitter: 20.0 ms)
- Database (`erp_sql`, DSCP AF21 18): `ce-branch1 -> pe1 -> p1 -> pe2 -> ce-dc` (Max RTT: 50.0 ms, Max Loss: 0.1%)
- Bulk Transfer (`bulk_backup`, DSCP BE 0): Best-effort backup traffic (Max RTT: 250.0 ms)
