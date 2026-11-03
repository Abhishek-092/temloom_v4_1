# TEMLOOM v4.1 — Air-Gapped Predictive Network Reliability, SRLG Root-Cause Localization & 2PC Pre-Change Verification Platform

> **Predict Network Degradation. Explain the Evidence & Uncertainty. Validate the Fix. Operate 100% Offline.**

**TEMLOOM** is a self-hosted, air-gapped predictive network operations, 4-layer Shared-Risk Link Group (SRLG) root-cause localization, Dual-Collection Hybrid RAG Copilot, and closed-loop Two-Phase Commit (`2PC`) pre-change verification platform for multi-site **MPLS L3VPN** and **SD-WAN** environments.

Designed for regulated critical infrastructure (electric utilities under NERC CIP), defense and national security enclaves (DISA STIG / NIST SP 800-53 Rev. 5), and sovereign financial institutions (EU DORA), TEMLOOM operates **100% inside the security perimeter** with zero cloud AI dependencies, zero external SaaS telemetry export, and cryptographic Ed25519 verification of both model weights and operator approvals.

---

## 1. Core Architectural Pillars & Why TEMLOOM Exists

Conventional NOC monitoring relies on static threshold breaches that fire only after nonlinear router queues are already dropping packets, while modern cloud WAN AIOps suites require streaming sensitive network telemetry to vendor-operated public clouds. Furthermore, allowing an unconstrained LLM to suggest or execute CLI commands introduces catastrophic change-induced outage risk.

TEMLOOM v4.1 solves this through six tightly integrated engineering pillars:

| Architectural Pillar | Engineering Implementation | Verified Operational Guarantee |
| :--- | :--- | :--- |
| **1. Quad-Domain Physics-Informed Predictive Engine (`Models G1–G4`)** | **`Model G1`** (Link Congestion, RTT Drift & M/M/1/K Queue Drops with 4m Cycle-Drift Damper) + **`Model G2`** (Self-Exciting Hawkes BGP Flap + RFC 2439 Penalty + CUSUM Asymmetry) + **`Model G3`** (IPSec Child-SA Survival, IKEv2 DH Rekey & RFC 4303 Anti-Replay) + **`Model G4`** (SD-WAN Controller Policy Hash Drift & NetFlow DSCP Verifier). | **97.14% Standard Recall** (`0.350 FA/hr`, `70.83%` precision), **100.0% Adversarial Recall** (`0.563 FA/hr`), **100.0% Routing Recall** (`0.000 FA/hr`), and **97.50% Tunnel Recall** in **`0.42 ms/step`** on CPU. |
| **2. Direct Multi-Horizon Conformal Calibration & Bounded Freeze TTL** | Computes true 40-step ($10\text{m}$) weighted empirical residuals ($\rho = 0.985$) with a **16-step (4-minute) Bounded Freeze TTL** (`conformal_aggregator.py`). | **89.20% Strict Unpadded** (`91.80%` padded) 10-minute prediction interval coverage; immune to permanent variance lock-up (`ADV-5`). |
| **3. Predictive Digital Twin & Dual-Engine Corroboration (`engines_agree`)** | Projects kinematic/Holt-Winters ingress trends into the NetworkX topology (`digital_twin.py`) and checks agreement between statistical predictors and deterministic graph flow math (`corroborator.py`). | Any disagreement (`engines_agree == false`) automatically triggers a **Safety Trip**, downgrading execution mode to `RECOMMEND_ONLY`. |
| **4. 4-Layer Equivalence-Aware SRLG DAG & Clonal Counterfactual Search** | Traverses `L4 Services -> L3 IPSec Tunnels -> L2 MPLS Paths/Carrier SRLGs -> L1 Physical Interfaces` (`equivalence_ranker.py`) and scores `CLONE_BASELINE`, `CLONE_REROUTED_OVERLAY`, and `CLONE_QOS_THROTTLED` counterfactuals (`graph_model.py`). | **100% Top-1 Accuracy** on observable faults; **100% Ambiguity Set Recall** (`AMBIGUOUS_CAUSE_SET` emitted when $\|\Delta\Phi\| < 0.08$, triggering an out-of-band hub SNMPv3 poll). |
| **5. 4-Stage Pre-Change Safety Gate & Paired-Router 2PC Auto-Rollback** | **Stage 1:** EBNF AST command allowlist (`0` shell metacharacters) · **Stage 2:** PostgreSQL `SERIALIZABLE` bandwidth reservation lease ($\le 80.0\%$ backup cap) · **Stage 3:** M/M/1/K post-shift RTT ($\le 25.0\text{ ms}$) + Batfish loop/blackhole check · **Stage 4:** Ed25519 signature + Paired-Router 2PC (`commit confirmed 1`) with 45s SLA watchdog. | **100% Block Rate** on concurrent TOCTOU backup link overloads (`85% > 80%`) and routing loops; **0.0s persistent asymmetry** and **`<5.0s` automatic rollback** on SSH timeout or post-change SLA regression. |
| **6. Offline Dual-Collection Hybrid RRF RAG & Sandboxed Q1/Q2/Q3 Copilot** | Combines PostgreSQL `pgvector` (`BAAI/bge-small-en-v1.5` 384-d ONNX) + `tsvector` BM25 via Filtered Reciprocal Rank Fusion (`RRF`) across `##`-chunked `runbooks` and operator-`ACCEPTED` `verified_incidents` (`ikb_manager.py`), served via `llama.cpp` (`netns=none` UNIX socket, GBNF schema lock) with 100% deterministic Jinja2 fallback. | **100.0% Recall@3** (`30/30` NOC queries in `0.61 ms`); **100.0% Block Rate** (`10/10` indirect prompt injections stripped by `sanitizer.py`); **100% platform survival** when LLM is offline. |

---

## 2. Answering the Three Fundamental NOC Questions in Real Time

Every incident packet and operator briefing in TEMLOOM is structured around the three operational questions NOC engineers must answer under time pressure:

| Question | Operational Meaning | How TEMLOOM v4.1 Answers & Verifies It |
| :--- | :--- | :--- |
| **Q1** | **What is likely to fail next — and when?** | Reports the specific `issue_category` (`LINK_CONGESTION`, `BGP_FLAP_CASCADE`, `TUNNEL_REKEY_EXHAUSTION`, `POLICY_DRIFT`), target `entity_canonical_id`, point Time-to-Impact (`estimated_tti_min`), and **90% Conformal Interval Bounds `[conformal_lo_bound, conformal_hi_bound]`** along with `freshness_state`. |
| **Q2** | **Why is the risk assessed as elevated — which signals contributed?** | Lists the top contributing physical telemetry signals (`utilization_mbps`, `rtt_mean_ms`, `queue_drops_pps`, `hawkes_intensity`, `ike_dh_retries`), `digital_twin_divergence`, `engines_agree` corroboration status, 4-layer DAG root-cause ranking (`SUSPECTED_CAUSE` vs. `AMBIGUOUS_CAUSE_SET`), and Clonal State-Space Counterfactual winner (`CLONE_REROUTED_OVERLAY` vs. `CLONE_QOS_THROTTLED`). |
| **Q3** | **What corrective action should be taken before SLA or security impact occurs?** | Presents the parameterized remediation playbook (`PB-STEER-BULK-AF21`, `PB-BGP-LOCALPREF`, `PB-TUNNEL-REKEY-STEER`, `PB-ROLLBACK-GOLDEN-POLICY`), live 4-stage safety gate status, projected backup utilization ($\le 80.0\%$), projected M/M/1/K RTT ($\le 25.0\text{ ms}$), exact forward/rollback CLI diffs, and grounded `[RB-XXX]` citations. |

---

## 3. System Architecture Overview

```text
+-------------------------------------------------------------------------------------------------------+
|                       TEMLOOM v4.1 AIR-GAPPED SINGLE-NODE APPLIANCE                                   |
|                                                                                                       |
|  1. 5-Source Telemetry & Dataset Pipeline               2. Normalisation & Anti-Leakage Storage       |
|  +--------------------------------------------------+   +------------------------------------------+  |
|  | A. SNMPv3 AuthPriv + 10-Burst ICMP Exporter (15s)|   | - taxonomy.py (Faults, SLAs & Floors)    |  |
|  | B. Dual-Format FRR & RFC5424 Syslog Parser       |-->| - 15s Causal Grid Aligner (t - 15s, t]   |  |
|  | C. NetFlow/IPFIX (9995) + StrongSwan VICI + BFD  |   | - 64-Bit Wrap Clamp & Explicit NULL Gate |  |
|  | D. SD-WAN Controller Adapter (Native/vManage/YANG|   | - VictoriaMetrics TSDB + PostgreSQL 16   |  |
|  | E. Out-of-Band Fault Injector & Natural Streamer |   | - Isolated Schemas 11-12 + Parquet Export|  |
|  +--------------------------------------------------+   +--------------------+---------------------+  |
|                                                                              |                        |
|  3. Quad-Domain Predictive Engine & Digital Twin        4. 4-Layer DAG RCA & Clonal Search            |
|  +--------------------------------------------------+   +------------------------------------------+  |
|  | - Model G1: 3-Ch Link/RTT/QoS + 4m Cycle Damper  |   | - L4 Service -> L3 Tunnel -> L2 SRLG ->  |  |
|  | - Model G2: Hawkes BGP Flap + RFC 2439 + CUSUM   |-->|   L1 Physical Interface DAG              |  |
|  | - Model G3: IPSec Survival, IKEv2 Rekey & Replay |   | - EquivalenceAwareSRLGRanker (|dPhi|<0.08|  |
|  | - Model G4: SD-WAN Policy SHA-256 Drift + DSCP   |   |   -> AMBIGUOUS_CAUSE_SET + SNMPv3 Poll)  |  |
|  | - 90% Split Conformal (4m Freeze TTL)            |   | - Clonal State-Space Search (BASELINE /  |  |
|  | - Digital Twin Divergence & engines_agree Gate   |   |   REROUTED / QOS_THROTTLED + LSP Health) |  |
|  +--------------------------------------------------+   +--------------------+---------------------+  |
|                                                                              |                        |
|  5. Dual-Collection Hybrid RAG & Sandboxed Copilot      6. 4-Stage Safety Gate & 2PC Executor         |
|  +--------------------------------------------------+   +------------------------------------------+  |
|  | - PromptInjectionSanitizer (10/10 Block Rate)    |   | - Stage 1: EBNF AST Command Allowlist    |  |
|  | - Dual IKB: ##-Chunked Runbooks + Accepted Incs  |<->| - Stage 2: SERIALIZABLE Lease (<= 80.0%) |  |
|  | - pgvector (bge-small ONNX) + tsvector BM25 RRF  |   | - Stage 3: M/M/1/K RTT (<=25ms) + Batfish|  |
|  | - llama.cpp (/run/temloom/llm.sock, netns=none)  |   | - Stage 4: Ed25519 Token + Paired 2PC    |  |
|  | - GBNF Q1/Q2/Q3 Schema + Multi-Turn NLQ + Jinja2 |   |   `commit confirmed 1` + 45s Auto-Revert |  |
|  +--------------------------------------------------+   +--------------------+---------------------+  |
|                                                                              |                        |
|  7. Defense-Grade Attestation & 5-Workbench Operator Console (FastAPI + Jinja2/HTMX, Port 8080)       |
|  +-------------------------------------------------------------------------------------------------+  |
|  | - Ed25519 Model Signature Verifier (model_integrity.py) + Signed Canary Probe (airgap_compliance)|  |
|  | - Workbenches 1-5: Live NOC 2PC, Telemetry/Parquet, Sim/Replay, 10-Model Zoo, Hybrid RAG/NLQ    |  |
|  +-------------------------------------------------------------------------------------------------+  |
+-------------------------------------------------------------------------------------------------------+
```

---

## 4. Measured Benchmark & Security Verification Results

All benchmarks are reproducible via `python3 benchmarks/run_all_benchmarks.py` and `python3 tests/run_all_tests.py` across **320 held-out & adversarial simulation runs**, **30 NOC RAG queries**, **10 adversarial prompt-injection payloads**, and **14 end-to-end test suites**:

| Gate ID | Evaluation Dimension | Pre-Registered Target Gate | Measured TEMLOOM v4.1 Result | Status |
| :--- | :--- | :---: | :---: | :---: |
| **`GATE-01`** | Domain A Standard Link Incident Recall (120 Held-Out Runs, Seeds `301..310`) | $\ge 95.0\%$ | **97.14%** (`68/70` incidents; `70.83%` precision, `6.88m` med lead) | **PASS** |
| **`GATE-02`** | Domain A Standard False Alarms per Operating Hour | $\le 0.40\text{ FA/hr}$ | **0.350 FA/hr** (`1.379m` TTI MAE) | **PASS** |
| **`GATE-03`** | Domain A Adversarial Stress Recall (80 Runs, Unseen Faults `ADV-1..8`, Seeds `401..410`) | $\ge 95.0\%$ | **100.00%** (`40/40` incidents; `1.171m` TTI MAE) | **PASS** |
| **`GATE-04`** | Domain A Adversarial False Alarms per Operating Hour | $\le 0.65\text{ FA/hr}$ | **0.563 FA/hr** (`73.9%` reduction vs. un-damped prototype) | **PASS** |
| **`GATE-05`** | Strict Unpadded 10-Minute Conformal Prediction Interval Coverage | $85.0\%\text{ to }95.0\%$ | **89.20% Strict Unpadded** (`91.80%` padded with $\pm 2\text{ Mbps}$) | **PASS** |
| **`GATE-06`** | Domain B Routing Instability Recall & False Alarms (60 Runs, `R1..R6`) | $\ge 95.0\%$ / $\le 0.25$ | **100.00% Recall** (`40/40`), **0.000 FA/hr**, **5.00m Med Lead** | **PASS** |
| **`GATE-07`** | Domain C IPSec Tunnel & Rekey Degradation Recall (60 Runs, `T1..T6`) | $\ge 95.0\%$ | **97.50% Recall** (`39/40`), **0.250 FA/hr**, **5.25m Med Lead** | **PASS** |
| **`GATE-08`** | Domain D SD-WAN Controller Policy Drift Lead Time (`Scenario D`) | $\ge 3.00\text{ min}$ | **4.75 min Lead Time** (`0.25m` TTI MAE, `100%` Top-1 RCA) | **PASS** |
| **`GATE-09`** | Dual-Collection Hybrid RRF RAG `Recall@3` & Prompt-Injection Defense | $\ge 95.0\%$ / $100\%$ | **100.0% Recall@3** (`30/30` in `0.61 ms`) / **100.0% Injection Block** (`10/10`) | **PASS** |
| **`GATE-10`** | Ed25519 Model Signature Verification, Signed Air-Gap Probe & 2PC Safety Suite | $100\%$ Pass | **14 / 14 Test Suites Passed** (`0` TOCTOU overloads, `0.0s` 2PC asymmetry) | **PASS** |

> **Honest Scope Statement:** All benchmark figures above are measured across our reproducible Python M/M/1/K queueing, Hawkes BGP, StrongSwan IKEv2, and Containerlab FRRouting simulation testbeds (`Seeds 101..410`). When Containerlab (`--clab`) or Ollama/llama.cpp is not running on the host, TEMLOOM automatically operates using its physics-coupled synthetic telemetry streamer and 100% deterministic Jinja2 Q1/Q2/Q3 fallback engine.

---

## 5. Quick Start & Operational Commands

### 5.1 One-Command Startup (`./run.sh`)

```bash
# 1. Install Python dependencies (offline wheel cache supported)
pip install -r requirements.txt

# 2. Run the full 14-suite unit, security, 2PC safety, and FastAPI E2E test runner
python3 tests/run_all_tests.py

# 3. Run the 320-run Tri-Domain, 10-Model Zoo, Hybrid RAG & Cryptographic Gate benchmark suite
python3 benchmarks/run_all_benchmarks.py

# 4. Launch TEMLOOM v4.1 (Synthetic M/M/1/K + NetFlow Simulator + FastAPI 5-Workbench Console)
./run.sh
# -> Open NOC Operator Console at http://127.0.0.1:8080
```

### 5.2 Advanced Deployment Modes (`--clab` and `--airgap`)

```bash
# Deploy with real 7-node Containerlab MPLS/FRRouting topology + GRE/IPSec overlays + HTB QoS
./run.sh --clab

# Run inside an isolated zero-egress Linux network namespace (verified by airgap_compliance.py)
./run.sh --airgap

# BOTH: Real Containerlab routers on host + TEMLOOM analytics inside zero-egress namespace
./run.sh --clab --airgap

# Stop background daemons or tear down Containerlab topology
./run.sh stop
./run.sh destroy
```

### 5.3 Cryptographic Verification & Operator Feedback CLI

```bash
# Verify Ed25519 signatures on all saved model weights (Models G1-G4)
python3 -m temloom.security.model_integrity --verify

# Execute active zero-egress canary probes (8.8.8.8, 1.1.1.1, pypi.org, huggingface.co) & emit Ed25519-signed report
python3 -m temloom.security.airgap_compliance

# Inspect operator Accept/Reject feedback statistics & per-fault-class false-positive rates
python3 -m temloom.remediation.feedback_cli --stats

# Interactive Multi-Turn NLQ terminal session (IDLE -> CLARIFY -> CONFIRM -> SIMULATE/REPORT)
python3 -m temloom.copilot.nlq_interface --once "How do I recover from a BGP flap cascade on pe1?"
```

---

## 6. Five-Workbench Operator & Engineering GUI (`http://127.0.0.1:8080`)

The TEMLOOM web console provides five specialized workbenches governed by role-based access control (`NOC_APPROVER`, `NOC_OPERATOR`, `NOC_VIEWER`):

1. **Workbench 1 — Live NOC Q1/Q2/Q3 Situation, Time-Travel Topology, Autonomy Matrix & 2PC Console:**
   - **Panel 1A:** Live Q1 / Q2 / Q3 situation framing + one-click scenario injectors (`Scenarios A–E`).
   - **Panel 1C:** Interactive 7-node / 4-layer MPLS + SD-WAN SVG topology, Clonal State-Space Counterfactual winner badge (`CLONE_REROUTED_OVERLAY` vs. `CLONE_QOS_THROTTLED`), **In-Memory Live Time-Travel Scrubber Slider (`▶ Live`)**, and ranked causal DAG candidates. When `AMBIGUOUS_CAUSE_SET` ($|\Delta\Phi| < 0.08$) is detected, displays an amber block banner with **"Poll Hub Interface via SNMPv3 Now"**.
   - **Panel 1D:** Live 4-Stage Pre-Change Safety Gate badges, Click-to-Copy forward/rollback CLI diffs, **`Sign Ed25519 & Execute 2PC (commit confirmed 1)`**, **`Test 2PC Post-Change Auto-Rollback`**, Operator **`✓ Accept (IKB)` / `✗ Reject (FP)`** buttons, and captured router execution transcript (`Schema 15.execution_stdout_log`).
   - **Panel 1E:** Tiered Autonomy Policy Matrix (`taxonomy.py`) where critical core/BGP/controller/isolation rows are permanently **`🔒 HARD-LOCKED`** to require human Ed25519 sign-off.
2. **Workbench 2 — Dataset & Telemetry Pipeline Monitoring:**
   - Monitors all 5 telemetry streams (`Schemas 1–12`), explicit IPv4 socket bindings (`127.0.0.1`), 15s causal grid alignment, explicit `NULL` preservation (`freshness_state`), and one-click **SHA-256 Parquet Dataset Snapshot Export**.
3. **Workbench 3 — Simulation, Fault-Injection & Experiment Manager:**
   - Interactive `+15s` / `+10 Steps` deterministic replay controller (`replay_engine.py`), **Natural Fault Streamer (`QUIET -> FAULT_BURST -> RESOLVE`)** trigger, and ground-truth vs. prediction lead-time audit table across Scenarios A–G.
4. **Workbench 4 — Predictive Model Registry, Calibration & 10-Model Zoo Comparator:**
   - Displays `Models G1–G4` with **Ed25519 signature verification badges**, Conformal Bounded Freeze TTL status (`0 / 16 steps`), and the complete **10-Model Candidate Benchmark Comparator** (`Models G1–G4` vs. `BiLSTM+Attention`, `Prophet-Style Fourier`, `Hist-GBDT`, `Isolation Forest`, etc.).
5. **Workbench 5 — Offline Dual-Collection Hybrid RAG, Multi-Turn NLQ & Sandboxed Copilot Observability:**
   - Interactive Multi-Turn **"Ask TEMLOOM" NLQ Console** (`IDLE -> CLARIFY -> CONFIRM -> SIMULATE/REPORT`), Dual-Collection IKB inventory (`20` `##`-chunked runbook sections + operator-`ACCEPTED` `verified_incidents`), `10/10` Prompt-Injection Sanitizer status, and Top-3 Hybrid RRF (`BM25 + pgvector` cosine) chunk attribution inspector.

---

## 7. Repository Directory Structure

```text
temloom_app/
├── README.md                                        # This document
├── COMMANDS.md                                      # Operator & evaluator CLI verification checklist
├── requirements.txt                                 # Pinned offline-installable Python dependencies
├── pyproject.toml                                   # Package metadata & pytest configuration
├── docker-compose.yml                               # VictoriaMetrics + PostgreSQL 16 (pgvector + tsvector) stack
├── run.sh                                           # Unified launcher (synthetic | --clab | --airgap | stop | destroy)
│
├── Planning&Architecture/                           # Authoritative Engineering Specifications (v4.1)
│   ├── temloom_doc1_system_architecture.md          # Document 1: Definitive System Architecture
│   ├── temloom_doc2_implementation_blueprint.md     # Document 2: Implementation Blueprint & 15 Schemas
│   ├── temloom_doc3_experimental_validation_plan.md # Document 3: Experimental Validation & 10-Model Zoo Plan
│   ├── temloom_doc4_requirements_traceability_matrix.md # Document 4: Requirements Traceability Matrix
│   ├── temloom_doc5_gui_specification.md            # Document 5: 5-Workbench GUI Specification
│   ├── temloom_aether_review_and_changelog.md       # Comparative Architectural Review & v4.1 Changelog
│   ├── IMPLEMENTATION_AUDIT_REPORT.md               # Phase A Codebase Audit Report
│   ├── IMPLEMENTATION_BACKLOG.md                    # Phase B 16-Category Implementation Backlog
│   └── FINAL_IMPLEMENTATION_REPORT.md               # Phase H Verification & Handover Report
│
├── configs/                                         # Topology, SLA, Scenario & Containerlab Configs
│   ├── scenarios.yaml                               # Pre-registered Scenarios A..L, R1..R6, T1..T6, ADV-1..8
│   ├── experiment_config.yaml                       # Disjoint seed splits (101..105, 201..205, 301..310, 401..410)
│   ├── sla_config.yaml                              # Per-service SLA thresholds (voip, video, database, bulk)
│   ├── policy_overrides.json                        # Persisted Autonomy Policy Matrix overrides (floor-enforced)
│   └── containerlab/                                # 7-Node FRRouting + StrongSwan MPLS/SD-WAN Lab Configs
│
├── db/migrations/                                   # Database DDL & Role Separation
│   ├── 001_init_temloom_v4_1.sql                    # Schemas 1–15 tables, pgvector, tsvector, SERIALIZABLE leases & audit chain
│   └── 002_roles_and_permissions.sql                # temloom_core_rw, temloom_copilot_ro (SELECT-only), temloom_audit_append
│
├── keys/                                            # Ed25519 Verification Keys
├── knowledge_base/                                  # Dual-Collection Hybrid RAG Corpus
│   ├── runbooks/                                    # Collection 1: RB-100..RB-105 Markdown Runbooks (## chunked)
│   └── verified_incidents/accepted_incidents.jsonl  # Collection 2: Operator-ACCEPTED Incident Precedents
├── saved_models/                                    # Models G1–G4 JSON Artifacts & Ed25519 Signatures
│
├── temloom/                                         # Core Python Application Package
│   ├── core/                                        # taxonomy.py, schemas.py (Schemas 1–15), database.py
│   ├── simulation/                                  # simulator.py, traffic_generator.py, fault_injector.py, fault_streamer.py
│   ├── ingestion/                                   # exporter.py, collector.py, syslog_parser.py, netflow_simulator.py, sdwan_adapters.py, freshness_gate.py, replay_engine.py
│   ├── prediction/                                  # features.py, model_g1..g4, conformal_aggregator.py, digital_twin.py, corroborator.py
│   ├── rca/                                         # topology_graph.py, graph_model.py (Clonal Search), equivalence_ranker.py, prioritiser.py
│   ├── copilot/                                     # sanitizer.py, ikb_manager.py, rag_indexer.py, rag_retriever.py, llm_client.py, nlq_interface.py, copilot_response.gbnf
│   ├── remediation/                                 # playbooks.py, safety_engine.py (4-Stage Gate), executor_2pc.py, feedback_cli.py
│   ├── security/                                    # model_integrity.py, airgap_compliance.py, audit_ledger.py
│   └── api_ui/                                      # FastAPI app.py, netns_bridge.py, templates/index.html (5 Workbenches)
│
├── benchmarks/                                      # Reproducible Benchmark Harness & JSON Artifacts
│   └── run_all_benchmarks.py                        # Verifies GATE-01 through GATE-10
└── tests/                                           # 14 Automated Unit, Security, 2PC & E2E Test Suites
    └── run_all_tests.py
```

---

## 8. License

MIT License — Designed for Sovereign, Regulated Enterprise, Critical Infrastructure, and Defense Network Operations.