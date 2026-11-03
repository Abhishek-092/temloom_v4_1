# RB-103: IPSec Tunnel IKEv2 Rekey Exhaustion & RFC 4303 Anti-Replay Drops

## Symptoms & Model G3 Indicators
- StrongSwan `charon` logs `IKEV2-4-REKEY_RETRY`: `CREATE_CHILD_SA` Diffie-Hellman retries (`ike_dh_retries >= 3`) while `sa_rem_life_min <= 7.5m`
- Rising ESP sequence-gap packet loss (`esp_seq_loss_pct`) or RFC 4303 anti-replay window drops (`replay_drops_pps >= 10 pps`)
- MPLS underlay `lsp_health_score` drops below `0.80` on `core:mpls:srlg:transport-A-hub1`

## Validated Remediation Playbook (`PB-TUNNEL-REKEY-STEER` / `REROUTE_BRANCH`)
- Proactively initiate non-disruptive Child-SA rekey and steer VoIP EF traffic to `tun-br1-sec` before SA hard expiry:
  ```
  swanctl --rekey --child tun-br1-sa
  ip route replace 10.99.0.0/24 dev tun-br1-sec metric 10
  ```
