# RB-101: Link Congestion, Latency Drift & M/M/1/K Queue Starvation

## Symptoms & Model G1 Indicators
- Rising utilization slope (`util_slope_mbps_per_min > 1.2 Mbps/min`) on `core:mpls:link:mpls-link-mab-1` or `pe1->p1`
- Rising M/M/1/K QoS tail-drop velocity (`cbQosCMDropPkt64` / `queue_drops_pps >= 10 pps`)
- Model G1 forecasts SLA breach (`>= 95.0 Mbps` or `RTT >= 30.0 ms`) within 5–15 minutes
- Clonal State-Space Search scores `CLONE_REROUTED_OVERLAY` or `CLONE_QOS_THROTTLED` superior to `CLONE_BASELINE`

## Diagnosis Steps
1. Inspect interface queue counters: `tc -s qdisc show dev eth1` and SNMP `cbQosCMDropPkt64`
2. Verify NetFlow/IPFIX flow distribution across DSCP EF (46) vs AF21 (18) vs BE (0)
3. Check Stage 2 `SERIALIZABLE` bandwidth reservation lease on `br1:ce-br1:tunnel:tun-br1-backup` (must stay `<= 80.0%`)

## Validated Remediation Playbooks (`PB-STEER-BULK-AF21` / `QOS_SHAPE_QUEUE`)
- Steer AF21/BE bulk flows (`+28 Mbps`) onto secondary tunnel `tun-br1-backup` or throttle bulk class `1:30` to `1mbit`:
  ```
  route-map PB-STEER-BULK-AF21 permit 10
   match ip dscp af21 be
   set interface tun-br1-backup
  ```
