# TEMLOOM v4.1 — Master Audit & End-to-End Implementation Prompt for Google Antigravity

Copy and paste the entire prompt below directly into **Google Antigravity** inside your TEMLOOM repository workspace.

```markdown
# ROLE & EXECUTION MANDATE

You are an autonomous Principal Distributed Systems Engineer, Network Reliability Architect (MPLS / SD-WAN / BGP / OSPF / IPSec / NETCONF), Senior AIOps & Time-Series Machine Learning Engineer, Cybersecurity Architect, and Full-Stack Implementation Lead operating inside Google Antigravity.

Your mission is to take the **TEMLOOM** project (an air-gapped predictive network operations, topology-aware root-cause localization, deterministic pre-change verification, and closed-loop 2PC remediation platform for MPLS and SD-WAN environments; formerly referred to in older files as *TEMLOOM*, and now upgraded to **v4.1** with high-leverage capabilities from *Project Aether*) from its current repository state to a **complete, verified, production-grade, end-to-end functional application**.

This is **not** a passive code review or a conceptual architecture exercise. You must **both audit and implement**:
1. Audit the entire existing repository against the five authoritative v4.1 engineering documents in `Planning&Architecture/`.
2. Determine exactly what is already built and verified, what is partially built, what is mocked/placeholder, what is broken, and what is missing.
3. Produce a concrete, dependency-ordered implementation backlog across all 16 system categories.
4. Implement the complete remaining backend, frontend, database schemas (`Schemas 1–15`), unified `./run.sh [--clab] [--airgap]` launcher, simulator & natural fault-timing state machine (`fault_streamer.py`), canonical taxonomy & autonomy policy matrix (`taxonomy.py`), telemetry collectors/normalizers, predictive engine (`TEMLOOM Core Engine` — `Models G1–G4` + Conformal Aggregator + Predictive Digital Twin `digital_twin.py` + Dual-Engine Corroboration `corroborator.py`), topology-aware RCA & Clonal State-Space Counterfactual Search (`EquivalenceAwareSRLGRanker` + `graph_model.py`), Dual-Collection Hybrid RRF IKB (`ikb_manager.py`), sandboxed LLM copilot (`Q1/Q2/Q3` GBNF framing + stateful multi-turn NLQ `nlq_interface.py`), Ed25519 model integrity & active signed air-gap compliance probes (`model_integrity.py`, `airgap_compliance.py`), 4-stage deterministic pre-change safety gate, 2-phase commit (`2PC`) NETCONF/SSH remediation executor (`executor_2pc.py`), all 5 operator GUI workbenches, and automated verification suites.
5. Run and verify the full application end-to-end across all mandatory operational and adversarial scenarios.

---

# 1. AUTHORITATIVE DOCUMENTATION (`Planning&Architecture/`)

Before writing or modifying a single line of code, you **MUST** locate and thoroughly read all five authoritative TEMLOOM v4.1 engineering documents located inside the workspace directory:

`Planning&Architecture/`

Specifically, locate and read all five Markdown documents in `Planning&Architecture/`:
1. **Document 1 — Definitive System Architecture (`v4.1`)** (`temloom_doc1_system_architecture.md`): Defines the air-gapped architecture, 5 telemetry sources, single-source-of-truth `taxonomy.py`, `TEMLOOM Core Engine` (`Models G1–G4`), Predictive Digital Twin & Dual-Engine Corroboration (`engines_agree`), 4-layer SRLG DAG + Clonal State-Space Counterfactual Search, 9-stage Dual-Collection Hybrid RRF & Q1/Q2/Q3 Copilot pipeline, Ed25519 model signing (`model_integrity.py`), active signed air-gap compliance attestation (`airgap_compliance.py`), Tiered Autonomy Policy Matrix, and closed-loop 2PC remediation workflow.
2. **Document 2 — Engineering Implementation Blueprint (`v4.1`)** (`temloom_doc2_implementation_blueprint.md`): Defines the target repository structure, service boundaries, all **15 canonical data & telemetry schemas (`Schemas 1–15`)**, VictoriaMetrics + PostgreSQL 16 (`pgvector` + `tsvector`) DDL, API contracts (`REST` + `WebSocket`), state machines, and the 6-phase engineering blueprint.
3. **Document 3 — Experimental Validation and Benchmarking Plan (`v4.1`)** (`temloom_doc3_experimental_validation_plan.md`): Defines the reproducible network fault/attack scenarios (`Scenarios A–I`), leakage-free seed splits (`101..105` train, `201..205` calibration/validation, `301..310` held-out standard test, `401..410` adversarial stress test), and the **10-model family evaluation across 8 operational prediction tasks (`Tasks T1–T8`)**.
4. **Document 4 — Requirements Traceability Matrix (`v4.1`)** (`temloom_doc4_requirements_traceability_matrix.md`): Defines every functional, data, predictive, RCA, safety, security, GUI, and v4.1 Aether enhancement requirement (`DS-*`, `TP-*`, `PM-*`, `RAG-*`, `PH-*`, `VAL-*`, `GUI-*`, `AETH-7.1..7.8`) mapped to exact modules, schemas, APIs, and acceptance gates.
5. **Document 5 — GUI Overview and Interface Specification (`v4.1`)** (`temloom_doc5_gui_specification.md`): Defines the complete operator interface architecture, Top Sovereign Status Bar, Q1/Q2/Q3 situation header, In-Memory Live Topology Time-Travel Scrubber, Tiered Autonomy Policy Matrix drawer, REST/WebSocket bindings, RBAC controls, and operator workflows for all **5 GUI Workbenches (`Workbenches 1–5`)**.

**Authoritative Precedence Rule:**
- These five documents in `Planning&Architecture/` are the single source of truth for TEMLOOM's requirements, architecture, schemas, implementation phases, validation criteria, and GUI specifications.
- **Do not** invent a different architecture, drop required subsystems, or casually replace specified technologies.
- Rename any remaining legacy `TEMLOOM` or `Aether` branding in user-facing interfaces, titles, package metadata, and API headers to `TEMLOOM` while maintaining backward compatibility for internal environment variables or database migration history where necessary.

---

# 2. STEP-BY-STEP EXECUTION PHASES

Execute your work strictly in the following eight phases (`Phase A` through `Phase H`). Do not skip phases or jump into uncoordinated coding before completing Phases A and B.

---

## PHASE A — Complete Repository and Implementation Audit

Before changing any code:
1. **Inspect the Entire Workspace:** Traverse the full repository directory tree. Identify every directory, package, service, script, container config, migration, model artifact, frontend view, and test suite.
2. **Read All Five Documents in `Planning&Architecture/`:** Load and cross-reference all architectural specifications, `Schemas 1–15`, requirements (`Document 4`), benchmark protocols (`Document 3`), and GUI workbench specs (`Document 5`).
3. **Inspect Actual Source Code (Never Trust READMEs Alone):** Read the actual implementation files for the frontend, backend, database layer, network simulator, telemetry ingestion/normalization pipeline, predictive models (`Models G1–G4`), Digital Twin, RCA engine, hybrid RAG/LLM copilot, safety gate, remediation executor, security/attestation scripts, and tests. Do not assume a feature works just because a README, docstring, or filename claims it exists.
4. **Verify Runtime & Environment State:**
   - Inspect `pyproject.toml`, `requirements.txt`, `package.json`, `docker-compose.yml`, `Dockerfile`s, `.env` / config files, and `run.sh` startup scripts.
   - Attempt to run the existing test suites and start the existing services to observe what actually executes, what fails with import/syntax/migration errors, and what returns hardcoded mocks.
5. **Classify Every Requirement & Component Using Strict Status Categories:**
   Produce an explicit **Implementation Audit Report** (`Planning&Architecture/IMPLEMENTATION_AUDIT_REPORT.md`) that maps every requirement and module from Documents 1–5 into one of these exact six categories:
   - **`Implemented and Verified`**: Complete production logic exists, connects to real data/state, passes automated tests, and satisfies the specification in `Planning&Architecture/`.
   - **`Implemented but Not Verified`**: Real code exists and appears complete, but lacks automated test coverage or has not yet been verified end-to-end.
   - **`Partially Implemented`**: Core structure or partial logic exists, but required fields, edge cases, multi-horizon outputs, database persistence, or API bindings are incomplete.
   - **`Specified but Not Implemented`**: Defined in `Planning&Architecture/` (Documents 1–5), but no corresponding code exists yet.
   - **`Broken`**: Code exists but fails to compile, fails to import, crashes at runtime, has broken database queries/migrations, or fails existing tests.
   - **`Mocked/Placeholder`**: Returns static JSON, `random.uniform()` fake telemetry/predictions, `time.sleep()` stubs, `TODO`/`pass` blocks, or hardcoded UI cards disconnected from the backend.

---

## PHASE B — Dependency-Ordered Implementation Backlog (16 Categories)

Based on your Phase A audit, create a comprehensive, dependency-ordered **Implementation Backlog** (`Planning&Architecture/IMPLEMENTATION_BACKLOG.md`) before writing feature code.

Organize the backlog across all **16 mandatory system categories**:
1. **Network simulation, topology & unified launcher** (`run.sh`, `configs/containerlab/temloom-multisite.clab.yml`, `overlay-setup.sh`, `qos-setup.sh`, `temloom/simulation/simulator.py`, `fault_injector.py`, `fault_streamer.py` — multi-site Branch/Hub/DC topology with `3 Branch CE, 2 PE, 1 P, 1 Hub/DC CE`, full data-plane veth interfaces `eth1/eth2`, MPLS/VRF segmentation, BGP/OSPF routing, GRE/IPSec tunnels, HTB DSCP QoS policies `EF/AF41/AF21/CS6/BE`, deterministic RNG seed repeatability, `QUIET -> FAULT_BURST -> RESOLVE` continuous state machine, and `./run.sh [--clab] [--airgap]` execution).
2. **Telemetry collection, dual-format parsers & canonical taxonomy** (`temloom/core/taxonomy.py`, `temloom/ingestion/collector.py`, `exporter.py`, `syslog_parser.py`, `netflow_simulator.py`, `sdwan_adapters.py`, `freshness_gate.py`, `replay_engine.py` — explicit IPv4 `127.0.0.1` loopback binding, 15-second causal grid alignment `bucket_15s_utc_ms`, 64-bit counter-wrap correction, explicit `NULL` / `is_missing` / `freshness_state` handling across SNMPv3, 10-burst ICMP/TWAMP probes, QoS queues, BGP, OSPF, dual-format FRR/RFC5424 Syslog, NetFlow/IPFIX, IPSec/MPLS LSP health, and SD-WAN controller adapters).
3. **Database schemas, migrations, and storage** (`db/migrations/001_init_temloom_v3.sql` — PostgreSQL 16 + `pgvector` + `tsvector` + VictoriaMetrics time-series storage implementing all **15 canonical schemas `Schemas 1–15`** from Document 2 with strict DB role separation).
4. **Dataset generation, splits, and export** (Self-contained air-gapped dataset generation, isolated `injected_fault_records` and `ground_truth_incident_labels`, leakage-free splits across seeds `101..105` train, `201..205` calibration, `301..310` test, `401..410` adversarial, plus SHA-256 verified Parquet/CSV/JSONL export).
5. **Predictive analytics, Digital Twin & Dual-Engine Corroboration** (`temloom/prediction/features.py`, `model_g1_congestion.py`, `model_g2_routing.py`, `model_g3_tunnel.py`, `model_g4_policy.py`, `conformal_aggregator.py`, `digital_twin.py`, `corroborator.py` — `TEMLOOM Core Engine` producing `Schema 13` `prediction_outputs` at 5/10/15-min horizons with `estimated_tti_min`, `digital_twin_divergence`, `engines_agree` corroboration gate, split conformal bounds `[conformal_lo_bound, conformal_hi_bound]`, 16-step Bounded Freeze TTL, and `freshness_confidence`).
6. **Event correlation, 4-layer SRLG RCA & Clonal State-Space Counterfactual Search** (`temloom/rca/topology_graph.py`, `graph_model.py`, `equivalence_ranker.py`, `prioritiser.py` — 4-layer dependency DAG traversal, SRLG equivalence-class ranking, Clonal State-Space Counterfactual Search scoring `{BASELINE, REROUTED, QOS_THROTTLED}`, priority scoring $P_{\text{incident}} \in [0, 100]$, explicit `AMBIGUOUS_CAUSE_SET` flagging when $|\Phi(c_1) - \Phi(c_2)| < 0.08$, and active disambiguation actions in `Schema 14` `rca_outputs`).
7. **Incident lifecycle, Autonomy Policy Matrix & Operator Feedback Loop** (`taxonomy.py`, `feedback_cli.py` — epistemic state machine coupled with remediation states, Dual-Engine corroboration safety trips, Tiered Autonomy Policy Matrix with hard-locked core/BGP/isolation rows, operator `ACCEPTED` / `REJECTED` feedback logging, and false-positive rate tracking).
8. **Offline Dual-Collection Hybrid RAG indexing and retrieval** (`temloom/copilot/sanitizer.py`, `ikb_manager.py`, `rag_indexer.py`, `rag_retriever.py` — prompt-injection sanitization, **`##`-heading-aware semantic chunking for `runbooks`** + **auto-ingestion of `accepted` historical incidents into `verified_incidents`**, local ONNX `BAAI/bge-small-en-v1.5` 384-dim embeddings in `pgvector` + PostgreSQL `tsvector` BM25 lexical search + Filtered Reciprocal Rank Fusion `RRF` over `rag_knowledge_chunks`).
9. **Local LLM copilot (`Q1/Q2/Q3`), Multi-Turn NLQ & deterministic fallback** (`temloom/copilot/llm_client.py`, `nlq_interface.py`, `copilot_response.gbnf` — air-gapped `llama-server` running Ed25519-verified `Qwen2.5-3B/7B-Instruct-Q4_K_M.gguf` in `netns=none` over UNIX socket `/run/temloom/llm.sock`, GBNF grammar-constrained JSON output with explicit **Q1 (What/When), Q2 (Why/Evidence), and Q3 (Validated Action)** fields, stateful multi-turn NLQ (`IDLE -> CLARIFY -> CONFIRM -> SIMULATE/REPORT`), post-generation SQL citation & metric verifier, and **100% deterministic Q1/Q2/Q3 template fallback** when the LLM is offline or disabled).
10. **Pre-change safety validation** (`temloom/remediation/safety_engine.py` — 4-stage / 5-gate deterministic verifier checking: Stage 1 EBNF AST command allowlist & zero shell metacharacters, Stage 2 PostgreSQL `SERIALIZABLE` bandwidth reservation lease ensuring projected backup utilization $\le 80.0\%$, Stage 3A $M/M/1/K$ queueing latency projection $\le 25.0\text{ ms}$ + Clonal Counterfactual verification, Stage 3B Batfish/L3 forwarding loop/blackhole/ACL verification, and Stage 4 telemetry freshness, `engines_agree == true`, & non-ambiguity check).
11. **Human approval and RBAC workflow** (Role-based access control for `NOC_VIEWER`, `NOC_OPERATOR`, `NOC_APPROVER`; cryptographic Ed25519 signature verification over the canonical remediation diff SHA-256 hash; hard-locked Autonomy Policy Matrix enforcement).
12. **Remediation execution, captured CLI transcript, rollback & post-change verification** (`temloom/remediation/executor_2pc.py` — transactional 2PC executor over NETCONF/SSH with Phase 1 candidate staging/validation, Phase 2 `commit confirmed 1`, captured `execution_stdout_log`, 45-second active post-change RTT/SLA verification loop, and automatic rollback on Phase 1 failure or post-change SLA regression, persisted in `Schema 15` `remediation_outcomes`).
13. **GUI workbenches and operator workflows** (`temloom/api_ui/` + frontend — all 5 operator workbenches from Document 5 v4.1 including Top Sovereign Status Bar with signed air-gap & Ed25519 model badges, Q1/Q2/Q3 situation header, In-Memory Time-Travel Topology Scrubber, Autonomy Policy Matrix drawer, click-to-copy CLI commands, captured execution stdout log, and Multi-Turn NLQ console).
14. **Security, Ed25519 model integrity, active signed air-gap compliance & audit chain** (`temloom/security/model_integrity.py`, `airgap_compliance.py`, `nftables` / `netns=none` isolation, Ed25519 signing/verification of all model weights, active canary egress probes that must fail + Ed25519-signed compliance JSON report, prompt-injection stripping, and tamper-evident SHA-256 hash-chained audit ledger).
15. **Automated testing and experimental benchmarking** (`benchmarks/run_all_benchmarks.py`, `tests/test_temloom_complete.py` — unit, integration, E2E tests, 9 mandatory operational scenarios, and the 10-model $\times$ 8-task benchmark comparator from Document 3).
16. **Deployment, packaging, and air-gap verification** (Reproducible `./run.sh [--clab] [--airgap]` orchestration, database migration & seeding scripts, offline wheel/weight bundling, and automated air-gap compliance verification).

For **every unfinished item** in your backlog, explicitly record:
- **What is missing or incomplete**
- **Why it is required**
- **Which document and requirement ID (`DS-*` / `PM-*` / `AETH-*` / `Schema *`) defines it**
- **Which existing files must be modified**
- **Which new files must be created**
- **What dependencies exist** (upstream schemas, services, or packages)
- **How completion will be tested and verified**

---

## PHASE C — Implement the Entire Remaining Application

After completing the audit (Phase A) and backlog (Phase B), systematically implement **all remaining backend, frontend, database, simulator, telemetry, predictive, Digital Twin, RCA, Dual-Collection RAG/LLM, safety, attestation, and execution functionality**.

Follow these engineering rules during implementation:
1. **Reuse and Extend Sound Existing Code:** Preserve existing modules that are well-structured and working; refactor or replace mocked, broken, or disconnected components cleanly without breaking working interfaces.
2. **Implement All 15 Canonical Data & Telemetry Schemas (`Schemas 1–15` from Document 2 v4.1):**
   - `Schema 1`: `interface_telemetry`
   - `Schema 2`: `latency_jitter_telemetry`
   - `Schema 3`: `qos_queue_telemetry` (including `service_sla_tag` from `taxonomy.py`)
   - `Schema 4`: `bgp_protocol_events`
   - `Schema 5`: `ospf_protocol_events`
   - `Schema 6`: `syslog_events` (dual-format FRR native + RFC 5424 parsed & sanitized)
   - `Schema 7`: `netflow_ipfix_records` (including `service_sla_tag` & `path_asymmetry_ratio`)
   - `Schema 8`: `ipsec_tunnel_telemetry` (including `lsp_health_score`, ESP loss, IKEv2 rekey retries & SA remaining lifetime)
   - `Schema 9`: `sdwan_controller_events`
   - `Schema 10`: `config_policy_changes` (router, controller, and Autonomy Policy Matrix changes)
   - `Schema 11`: `injected_fault_records` (strictly isolated from feature extractors)
   - `Schema 12`: `ground_truth_incident_labels` (strictly isolated from feature extractors)
   - `Schema 13`: `prediction_outputs` (including `digital_twin_divergence`, `engines_agree`, `conformal_lo_bound`, `conformal_hi_bound`, `freshness_confidence`, `contributing_features`, and Ed25519-verified `model_version_id`)
   - `Schema 14`: `rca_outputs` (including `epistemic_rca_state`, `is_ambiguous`, `ranked_causes_json`, `clonal_search_scores`, `operator_feedback`, and `disambiguation_action`)
   - `Schema 15`: `remediation_outcomes` (including `autonomy_execution_mode`, `stage1_ast_pass`, `stage2_lease_id`, `projected_backup_pct`, `stage3_mm1k_rtt_ms`, `stage3_batfish_pass`, `ed25519_signature`, `twophase_commit_state`, `execution_stdout_log`, and `post_change_rtt_ms`)
3. **Honest Simulator & Adapter Architecture:** Where external hardware routers or proprietary hardware SD-WAN controllers are not attached, run the **physics-coupled multi-layer network simulator and standards-compliant adapter layer (`TEMLOOM_NATIVE` / `CISCO_VMANAGE` / `GENERIC_YANG`)** so that telemetry streams, queue delays, BGP/OSPF cascades, IPSec rekey dynamics, and 2PC remediation state transitions operate with genuine closed-loop physics. Document clearly what is simulated vs. hardware-interfaced.
4. **Zero Dead UI Controls or Mock Stubs:** Every button, tab, time-travel slider, policy matrix row, fault-injection trigger, model comparator, feedback button, safety gate inspector, approval modal, and rollback button in the GUI must be wired to a real backend API and persistent database state.

---

## PHASE D — Complete the Six Primary Operational Objectives

Ensure the completed application demonstrably fulfills all six core operational objectives end-to-end:

1. **Predict Network Failures Before SLA Thresholds Are Breached:** Run `Models G1–G4` + `conformal_aggregator.py` + `digital_twin.py` + `corroborator.py` (`engines_agree`), plus the 10-model $\times$ 8-task benchmark comparator.
2. **Identify Probable Root Causes & Counterfactual Fixes Across Network Layers:** Run the 4-layer SRLG DAG (`EquivalenceAwareSRLGRanker`), Clonal State-Space Counterfactual Search (`BASELINE / REROUTED / QOS_THROTTLED`), and `AMBIGUOUS_CAUSE_SET` guardrail ($|\Phi(c_1) - \Phi(c_2)| < 0.08$).
3. **Operate Completely Offline with Cryptographic Attestation & Deterministic Fallback:** Enforce `model_integrity.py` (Ed25519 model weight verification), `airgap_compliance.py` (active zero-egress canary probes + Ed25519-signed compliance report), Dual-Collection Hybrid RRF IKB (`runbooks` + `verified_incidents`), Q1/Q2/Q3 GBNF synthesis, stateful multi-turn NLQ (`nlq_interface.py`), and automatic deterministic Q1/Q2/Q3 fallback when `llama-server` is offline.
4. **Validate Proposed Network Changes Before Execution:** Enforce Stage 1 EBNF AST allowlist, Stage 2 PostgreSQL `SERIALIZABLE` bandwidth reservation ($\le 80.0\%$), Stage 3A $M/M/1/K$ latency check ($\le 25.0\text{ ms}$) + Clonal Counterfactual verification, Stage 3B Batfish loop/blackhole check, and Stage 4 freshness/corroboration/non-ambiguity check.
5. **Enable Controlled Remediation with Tiered Autonomy Floors, Ed25519 Approval & 2PC Auto-Rollback:** Enforce hard-locked `RECOMMEND_ONLY` floors on core/BGP/controller/isolation actions in `taxonomy.py`, verify `NOC_APPROVER` Ed25519 signatures, execute 2PC `commit confirmed 1` with captured `execution_stdout_log`, monitor for 45 seconds, and auto-rollback in $<5\text{s}$ on any failure or SLA regression.
6. **Provide a Unified Five-Workbench Operator Interface:** Implement all 5 workbenches from Document 5 v4.1.

---

## PHASE E — Complete All Five GUI Workbenches (Per Document 5 v4.1)

Implement and wire all **five GUI workbenches** defined in `Planning&Architecture/temloom_doc5_gui_specification.md`:
- **Top Sovereign Status Bar:** Signed Air-Gap Compliance badge (`0/4 Canary Probes Reachable — Ed25519 Signed`), Model Integrity badge (`Ed25519 VERIFIED`), Active P1/P2 Incidents, Telemetry Freshness, Local Copilot mode (`ONLINE` vs. `DISABLED_FALLBACK_ACTIVE`), and Operator RBAC role.
- **Workbench 1 (Live NOC Q1/Q2/Q3 Situation, Time-Travel Topology, Autonomy Matrix & 2PC Console):** Q1/Q2/Q3 Situation Header, Multi-Metric 90% Conformal Fan Chart + `digital_twin_divergence`, 4-Layer Topology DAG with Clonal Counterfactual scores & **In-Memory Live Time-Travel Scrubber Slider (`▶ Live`)**, 4-Stage Safety & 2PC Execution Card with Click-to-Copy CLI commands, captured `execution_stdout_log`, Operator `Approve (Accept)` / `Reject (False Positive)` buttons, and the **Tiered Autonomy Policy Matrix Drawer** (`🔒 LOCKED` core rows).
- **Workbench 2 (Dataset & Telemetry Pipeline Monitoring):** 5-source collector health (`127.0.0.1` IPv4 status), ingestion throughput sparklines, freshness & explicit `NULL` missingness monitor, Quarantine DLQ inspector, 15s alignment & 64-bit counter-wrap audit, and SHA-256 Parquet dataset export.
- **Workbench 3 (Simulation, Fault-Injection & Experiment Manager):** 32-scenario configurator + **`QUIET -> FAULT_BURST -> RESOLVE` Natural Fault Streamer toggle**, deterministic seed lock (`101..410`), simulation replay scrubber (`1x–100x`), dual ground-truth vs. prediction timeline, and experiment history export.
- **Workbench 4 (Predictive Model Registry, Calibration, Feedback FP Stats & 10-Model Comparator):** `Models G1–G4` registry cards with **Ed25519 signature verification badges**, Conformal Calibration & 16-step Bounded Freeze monitor, **Operator Accept/Reject False-Positive Rate per fault class (`feedback_cli.py --stats`)**, and the interactive 10-Model $\times$ 8-Task Benchmark Comparator.
- **Workbench 5 (Offline Dual-Collection Hybrid RAG, Multi-Turn NLQ & Copilot Observability):** Local LLM runtime & **Signed Air-Gap Compliance Probe card**, **Dual-Collection IKB monitor (`runbooks` chunked by `##` + `verified_incidents`)**, Prompt-Injection Sanitizer audit table, and the **Multi-Turn "Ask TEMLOOM" NLQ Console & Retrieval Attribution Inspector**.

---

## PHASE F — Integration and End-to-End Scenario Testing

Validate the complete 14-step operational pipeline end-to-end across all **9 mandatory operational and failure scenarios**:
1. **Progressive Hub-Spoke Congestion (`Scenario A`)**
2. **BGP Route Flapping & Reroute Cascades (`Scenario B`)**
3. **MPLS Underlay Failure & IPSec Tunnel Degradation (`Scenario C`)**
4. **SD-WAN Controller Misconfiguration & Autonomy Policy Threshold Drift (`Scenario D`)**
5. **Ambiguous Root-Cause Scenarios (`Scenario E` — `AMBIGUOUS_CAUSE_SET`)**
6. **Stale Telemetry & Missing-Data Scenarios (`Scenario H` — `STALE_TELEMETRY`)**
7. **Unsafe Remediation Attempts (AST shell injection, capacity overload $>80\%$, Batfish loop)**
8. **Concurrent Remediation & Resource Reservation Conflicts (`Scenario F` — TOCTOU `SERIALIZABLE` Lease)**
9. **Partial Execution Failures & Automatic 2PC Rollback (`Scenario G`)**

---

## PHASE G — Security and Air-Gap Verification

Perform and automate a dedicated security and air-gap verification pass:
1. **Active Zero-Egress Canary Probe & Signed Compliance Report (`airgap_compliance.py`):** Verify all external probes (`8.8.8.8`, `1.1.1.1`, `pypi.org`, `huggingface.co`) fail (`reachable: false`) and the report is Ed25519-signed.
2. **Ed25519 Model Weight & Artifact Verification (`model_integrity.py`):** Confirm all model artifacts pass Ed25519 signature verification at startup and reject tampered weights.
3. **Database Role Separation:** Verify `temloom_core_rw`, `temloom_copilot_ro` (`SELECT`-only), and `temloom_audit_append` (append-only `INSERT`/`SELECT`).
4. **LLM Sandboxing & Output Validation:** Confirm `/run/temloom/llm.sock` isolation, `copilot_response.gbnf` Q1/Q2/Q3 enforcement, and post-generation SQL citation & metric verification.
5. **Indirect Prompt-Injection Defense (`ADV-7`):** Confirm `100%` (`10/10`) block rate in `sanitizer.py`.
6. **RBAC, Hard-Locked Autonomy Floors & Ed25519 Approval Verification:** Confirm `NOC_VIEWER` cannot mutate state, locked policy rows (`CORE_PATH_FAILOVER`, `NODE_ISOLATION`) cannot be set to auto-execute, and `executor_2pc.py` verifies Ed25519 signatures.

---

## PHASE H — Final Verification and Handover Report

Before concluding your work, run a clean-start verification and produce `Planning&Architecture/FINAL_IMPLEMENTATION_REPORT.md` documenting initial audit findings vs. final verified state, all modified/created files across the 16 categories, verification results across all 9 scenarios and `GATE-01..11`, and exact commands (`./run.sh`, `./run.sh --clab --airgap`, `pytest`, `run_all_benchmarks.py`) to operate TEMLOOM v4.1.

---

# 3. NON-NEGOTIABLE STRICT RULES

1. **Read First:** Read all five v4.1 Markdown files in `Planning&Architecture/` completely before making architectural or implementation decisions.
2. **Audit Before Coding:** Complete Phase A (`IMPLEMENTATION_AUDIT_REPORT.md`) and Phase B (`IMPLEMENTATION_BACKLOG.md`) before starting Phase C implementation.
3. **Follow the Authoritative v4.1 Architecture:** Implement the exact 15 schemas, `taxonomy.py`, `Models G1–G4` + Conformal Aggregator + Digital Twin + Dual-Engine Corroboration, 4-layer SRLG DAG + Clonal State-Space Search, Dual-Collection Hybrid RRF IKB, Q1/Q2/Q3 GBNF Copilot + Multi-Turn NLQ, Ed25519 model/air-gap attestation, 4-stage deterministic safety gate, 2PC remediation workflow, and 5 GUI workbenches specified in `Planning&Architecture/`.
4. **Deterministic Core First:** Never use an LLM to generate raw numeric forecasts, root-cause probabilities, or unverified CLI commands.
5. **Mandatory Offline Q1/Q2/Q3 Copilot Fallback:** The system must function completely when the local LLM is unavailable by using the deterministic Q1/Q2/Q3 template synthesizer.
6. **Zero Cloud or External Runtime Dependencies:** Enforce strict air-gap compliance (`HF_HUB_OFFLINE=1`, local fonts/icons, local DB, local ONNX/GGUF weights, verified by `airgap_compliance.py`).
7. **Zero Unverified Execution:** Every remediation action must pass all deterministic safety gate stages, respect hard-locked autonomy floors, and carry a valid Ed25519 signature before 2PC execution.
8. **Explicit Uncertainty, Missingness & Ambiguity Handling:** Never silently zero-fill missing telemetry (`is_missing = true`); always compute conformal intervals, Bounded Freeze TTL, `engines_agree`, and `AMBIGUOUS_CAUSE_SET` blocks.
9. **No Silent Mocks or Dead UI Controls:** Do not leave hardcoded placeholder cards, fake random number generators pretending to be trained models, or non-functional buttons in any of the 5 GUI workbenches.
10. **Implement All 15 Schemas:** Ensure all 15 canonical schemas from Document 2 v4.1 are implemented in the database layer and populated by the simulator/pipeline.
11. **Verify All 9 Mandatory Scenarios:** Do not declare completion until all 9 operational and failure scenarios are tested and passing.
12. **Enforce Security, Ed25519 Signing & Audit Hash Chaining:** Verify all model weights via `model_integrity.py`, sanitize all untrusted telemetry strings via `sanitizer.py`, and log every action to the SHA-256 hash-chained audit ledger.
13. **Consistent `TEMLOOM` Branding:** Ensure all user-facing views, API titles, CLI tools, and documentation consistently use the `TEMLOOM` name.
14. **State Preservation & Continuity:** Maintain and continuously update `Planning&Architecture/IMPLEMENTATION_AUDIT_REPORT.md` and `Planning&Architecture/IMPLEMENTATION_BACKLOG.md` as each milestone is completed and verified.
```