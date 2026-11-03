# RB-105: SRLG vs. Hub Interface Epistemic Ambiguity Disambiguation Protocol

## Symptoms & Equivalence-Aware Ranker Indicators
- Simultaneous degradation across `br1:ce-br1:tunnel:tun-br1` and `br2:ce-br2:tunnel:tun-br2`
- Top two root-cause candidates `core:mpls:srlg:transport-A-hub1` (`score=0.842`) and `hub1:ce-hub1:iface:wan0` (`score=0.819`) have score gap `|Delta Phi| = 0.023 < 0.08`
- Incident flagged as `epistemic_rca_state = 'AMBIGUOUS_CAUSE_SET'` (`is_ambiguous = true`)

## Mandatory Safety Rule & Disambiguation Procedure
- Automated/one-click 2PC remediation is **strictly blocked** while `is_ambiguous == true`
- Execute out-of-band SNMPv3 poll on `hub1:ce-hub1:iface:wan0` (`POLL_SNMPV3_IFMIB_NOW(hub1:ce-hub1:iface:wan0)`) to inspect `ifInErrors` and optical DOM Rx power (`optical_rx_dbm`) before unlocking Stage 4 remediation
