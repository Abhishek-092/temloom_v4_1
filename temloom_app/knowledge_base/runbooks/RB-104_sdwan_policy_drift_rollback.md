# RB-104: SD-WAN Controller Misconfiguration & Policy Hash Drift Rollback

## Symptoms & Model G4 Indicators
- `sdwan_controller_events` reports `policy_drift_detected = true` (`active_config_sha256 != golden_config_sha256`) on `AAR-VOICE-GOLD`
- NetFlow/IPFIX records show DSCP EF (`46`) VoIP packets routed onto congested internet tunnel `tun-br1-inet` instead of `tun-br1-mpls`
- Or Autonomy Policy Matrix threshold `min_conf` tampered below `taxonomy.py` `hard_floor_conf`

## Validated Remediation Playbook (`PB-ROLLBACK-GOLDEN-POLICY` / `CONTROLLER_POLICY_ROLLBACK`)
- Rollback SD-WAN controller policy `AAR-VOICE-GOLD` to golden SHA-256 baseline `8f9d2a1c4b7e6051` and restore `REROUTE_BRANCH` `min_conf = 0.80`:
  ```
  sdwan-controller policy rollback AAR-VOICE-GOLD --to-sha256 8f9d2a1c4b7e6051
  ```
