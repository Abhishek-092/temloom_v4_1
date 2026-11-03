# RB-102: BGP Route Flap Cascade, RFC 2439 Damping & OSPF SPF Storms

## Symptoms & Model G2 Indicators
- Recurring BGP `ROUTE_WITHDRAW` and `ADJ_DOWN` events on `br1:ce-br1:bgp_peer:10.255.0.2` (`%BGP-5-ADJCHANGE`)
- Self-exciting Hawkes intensity `hawkes_intensity >= 2.2` and RFC 2439 flap penalty approaching `2000.0` suppression ceiling
- OSPF SPF recalculations (`spf_runs_15s >= 2`) corroborated by BFD echo variance (`bfd_echo_var_ms2 >= 0.65`)

## Diagnosis Steps
1. Verify BGP session state: `vtysh -c 'show bgp vrf vrf-voice ipv4 unicast summary'`
2. Inspect OSPF neighbor table: `vtysh -c 'show ip ospf neighbor'`
3. Confirm whether event is a single planned peer reset (`Scenario R5`) or a recurring flap cascade (`Scenarios R1/R2`)

## Validated Remediation Playbook (`PB-BGP-LOCALPREF` / `CORE_PATH_FAILOVER`)
- Raise local-preference on backup path (`250`) and apply AS-path prepend on flapping primary peer via 2PC `commit confirmed 1` (LOCKED: Requires `NOC_APPROVER` Ed25519 signature):
  ```
  router bgp 65000 vrf vrf-voice
   neighbor 10.255.0.2 route-map RM-PREFER-SECONDARY out
  route-map RM-PREFER-SECONDARY permit 10
   set local-preference 250
  ```
