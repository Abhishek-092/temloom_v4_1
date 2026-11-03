#!/usr/bin/env python3
import numpy as np
from temloom.simulation.simulator import (
    NetworkTelemetrySimulator,
    generate_routing_scenario,
    generate_tunnel_scenario,
    generate_policy_drift_scenario,
)
from temloom.prediction.model_g1_congestion import TemloomModelG1CongestionEngine
from temloom.prediction.model_g2_routing import ModelG2_HawkesCUSUMRoutingEngine
from temloom.prediction.model_g3_tunnel import ModelG3_TunnelRekeyHazardEngine
from temloom.prediction.model_g4_policy import ModelG4_PolicyDriftAndNetFlowEngine
from temloom.prediction.conformal_aggregator import OnlineSplitConformalAggregator
from temloom.prediction.digital_twin import DigitalTwin, TrendForecaster
from temloom.prediction.corroborator import DualEngineCorroborator
from temloom.rca.graph_model import ClonalGraphEngine


def test_quad_domain_models_g1_to_g4():
    sim = NetworkTelemetrySimulator()
    scen_a = sim.generate_scenario("S1_gradual_congestion_ramp", seed=301)
    g1 = TemloomModelG1CongestionEngine()
    out1 = g1.predict_run(scen_a["df"])
    assert int(np.sum(out1["warnings"])) > 0

    scen_b = generate_routing_scenario("R2_RFC2439_Flap_Damping_Suppression", seed=301)
    g2 = ModelG2_HawkesCUSUMRoutingEngine()
    out2 = g2.predict_run(scen_b["df"])
    assert int(np.sum(out2["warnings"])) > 0

    # Benign planned single-peer reset (R5) must produce 0 false alarms
    scen_r5 = generate_routing_scenario("R5_Benign_Planned_Single_Peer_Reset", seed=301)
    out_r5 = g2.predict_run(scen_r5["df"])
    assert int(np.sum(out_r5["warnings"])) == 0

    scen_c = generate_tunnel_scenario("T1_IKEv2_Rekey_Retry_Exhaustion", seed=301)
    g3 = ModelG3_TunnelRekeyHazardEngine()
    out3 = g3.predict_run(scen_c["df"])
    assert int(np.sum(out3["warnings"])) > 0

    scen_d = generate_policy_drift_scenario(seed=301)
    g4 = ModelG4_PolicyDriftAndNetFlowEngine()
    out4 = g4.predict_run(scen_d["df"])
    assert int(np.sum(out4["warnings"])) > 0


def test_conformal_bounded_freeze_and_corroborator():
    conf = OnlineSplitConformalAggregator(alpha=0.10, freeze_ttl_steps=16)
    lo, hi, hw, fconf = conf.compute_interval(88.0, missing_fraction_5m=0.0)
    assert lo < 88.0 < hi and fconf >= 0.90

    # Trigger regime shift bounded freeze
    conf.update_residual(100.0, 60.0, regime_shift_detected=True)
    assert conf.freeze_counter == 15

    # Test Dual-Engine Corroborator Safety Trip on Disagreement
    corr = DualEngineCorroborator()
    trip = corr.evaluate_corroboration("LINK_CONGESTION", 0.92, graph_projects_violation=False)
    assert trip["engines_agree"] is False
    assert trip["autonomy_execution_mode"] == "RECOMMEND_ONLY"
    assert "SAFETY TRIPPED" in trip["rationale"]
