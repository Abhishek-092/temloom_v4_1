#!/usr/bin/env python3
from temloom.rca.equivalence_ranker import EquivalenceAwareSRLGRanker


def test_rca_ranking_ambiguity_and_clonal_search():
    ranker = EquivalenceAwareSRLGRanker()
    # Unambiguous link congestion
    rca1 = ranker.rank_root_causes(
        incident_id="inc-unambig",
        bucket_15s_utc_ms=1793545200000,
        primary_entity_id="core:mpls:link:mpls-link-mab-1",
        issue_category="LINK_CONGESTION",
        anomaly_score=0.91,
        simulate_srlg_ambiguity=False,
    )
    assert rca1.is_ambiguous is False
    assert rca1.epistemic_rca_state == "SUSPECTED_CAUSE"
    assert "winner" in rca1.clonal_search_scores

    # Ambiguous SRLG vs Hub WAN interface (Scenario E)
    rca_amb = ranker.rank_root_causes(
        incident_id="inc-ambig",
        bucket_15s_utc_ms=1793545200000,
        primary_entity_id="core:mpls:srlg:transport-A-hub1",
        issue_category="TUNNEL_REKEY_EXHAUSTION",
        anomaly_score=0.88,
        simulate_srlg_ambiguity=True,
    )
    assert rca_amb.is_ambiguous is True
    assert rca_amb.epistemic_rca_state == "AMBIGUOUS_CAUSE_SET"
    assert rca_amb.disambiguation_action is not None

    # Resolve via out-of-band SNMPv3 poll
    resolved = ranker.resolve_ambiguity_via_snmp_poll(rca_amb)
    assert resolved.is_ambiguous is False
    assert resolved.epistemic_rca_state == "VERIFIED_CAUSE"
