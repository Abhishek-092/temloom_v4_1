# TEMLOOM v4.1 — Comparative Architectural Review of Project Aether & Complete Document Changelog

**Project Name:** TEMLOOM

**Document ID:** `TEMLOOM-AETHER-REVIEW-CHANGELOG-v4.1`

**Scope:** Rigorous engineering evaluation of the uploaded **Project Aether** reference architecture (`README.md`, `COMMANDS.md`, `llm_copilot.md`, `requirements.txt`) against **TEMLOOM v4.0**, technical justification of what was adopted vs. rejected, and an exact document-by-document changelog across `Documents 1–5` and the `Google Antigravity Master Prompt`.

## 1. Executive Summary of the Comparative Review

We audited all four uploaded Project Aether specification files (`README.md`, `COMMANDS.md`, `llm_copilot.md`, and `requirements.txt`) against the five authoritative TEMLOOM v4.0 engineering documents.

**Core Engineering Verdict:**

1. **TEMLOOM v4.0's core mathematical, database, safety, and execution foundations are significantly stronger than Project Aether's**—specifically in quad-domain predictive accuracy (`Models G1–G4` vs. BiLSTM/Prophet), distribution-free 90% split conformal calibration, unified PostgreSQL 16 (`pgvector` + `tsvector` Hybrid RRF + `SERIALIZABLE` bandwidth leases) + VictoriaMetrics storage, GBNF grammar-locked `netns=none` UNIX-socket LLM sandboxing, prompt-injection sanitization (`10/10` block rate), and closed-loop 2-Phase Commit (`2PC`) NETCONF/SSH remediation with 45-second post-change verification and automatic rollback (whereas Aether explicitly notes its remediation is open-loop and lacks data-plane veth pairs `eth1/eth2`).

2. **However, Project Aether contains eight concrete, high-leverage operational, security-attestation, and UX mechanisms that genuinely make TEMLOOM stronger** when integrated into TEMLOOM's rigorous architecture. We have engineered all eight enhancements directly into **TEMLOOM v4.1** across `Documents 1–5` and the `Google Antigravity Master Prompt`.

## 2. Subsystem-by-Subsystem Technical Comparison (Project Aether vs. TEMLOOM v4.0 -> TEMLOOM v4.1)

| Architectural Dimension | Project Aether (`README.md`, `COMMANDS.md`, `llm_copilot.md`) | TEMLOOM v4.0 Baseline | Engineering Verdict & TEMLOOM v4.1 Resolution | 
| ----- | ----- | ----- | ----- | 
| **1. Cryptographic Model & Air-Gap Attestation** | Implements **Ed25519 model weight signing (`model_integrity.py --sign / --verify`)** and an **Active Zero-Egress Canary Probe (`airgap_compliance.py`)** that probes `8.8.8.8`, `pypi.org`, etc. (all must fail) and emits an **Ed25519-signed compliance JSON report** (`GET /api/compliance`), plus `./run.sh --clab --airgap` dual-namespace execution. | Used SHA-256 model version hashes and passive `nftables` / `netns=none` rules; used Ed25519 only for Stage 4 operator remediation approvals. | **ADOPTED INTO TEMLOOM v4.1 (`AETH-7.1` & `AETH-7.2`):** Added `temloom/security/model_integrity.py` (Ed25519 signing/verification of `Models G1–G4`, conformal state, ONNX embeddings, and GGUF weights), `airgap_compliance.py` (active canary egress probes + Ed25519-signed attestation report), and `./run.sh --clab --airgap`. | 
| **2. Single Source of Truth Taxonomy & Autonomy Governance** | Centralizes all fault classes, per-service SLA tags (`voip`, `database`, `bulk`), and an **Operator-Configurable Autonomy Policy Matrix** in `taxonomy.py`, where critical actions (`CORE_PATH_FAILOVER`, `NODE_ISOLATION`) are **hard-locked (`🔒 locked`)** in code to `RECOMMEND_ONLY`. | Defined schema enums in SQL/Pydantic and required human Ed25519 sign-off for all 2PC actions, but lacked a single centralized `taxonomy.py` module and a live-inspectable Autonomy Policy Matrix UI with hard-locked vs. configurable confidence floors. | **ADOPTED INTO TEMLOOM v4.1 (`AETH-7.3`):** Added `temloom/core/taxonomy.py` as the single source of truth for fault enums, `service_sla_tag`, and the **Tiered Autonomy Policy Matrix** (with `CORE_PATH_FAILOVER`, `BGP_LOCALPREF_SHIFT`, `CONTROLLER_POLICY_ROLLBACK`, and `NODE_ISOLATION` permanently hard-locked to `RECOMMEND_ONLY` + human Ed25519 sign-off). | 
| **3. Predictive Analytics Engine** | Uses a 5-class PyTorch BiLSTM+Attention classifier (`~82%` accuracy, `20–43s` live lead time), LSTM Autoencoder, TTF Regressor, EMA Bollinger threshold, and notes Prophet seasonality fails without hours of cyclical history. | Uses **Quad-Domain Physics-Informed Engines (`Models G1–G4`)** (`97.14%` std / `100.0%` adv link recall, `100%` routing recall with `0.0 FA/hr`, `97.5%` tunnel recall, `4.75m–6.88m` median lead times) + **Direct 90% Split Conformal Calibration (`89.20%` strict coverage)** with 16-step Bounded Freeze TTL. | **RETAINED TEMLOOM `Models G1–G4` + CONFORMAL CALIBRATION (Benchmark-Backed):** Our Document 3 benchmark of 200 held-out runs proved BiLSTM has **68% higher false alarms (`0.588` vs. `0.350 FA/hr`) and 2x worse TTI MAE (`2.77m` vs. `1.38m`)** than `Model G1`, and confirmed Aether's finding that Prophet fails on short windows (`6.36 FA/hr`). | 
| **4. Digital Twin Divergence & Dual-Engine Corroboration** | Computes `digital_twin_divergence` (`digital_twin.py`: Holt-Winters trend forecast vs. NetworkX graph state) and enforces a **Dual-Model Corroboration Gate (`aether_corroborator.py`)**: statistical model and deterministic NetworkX graph must agree (`engines_agree = true`), otherwise a **Safety Trip** downgrades to `RECOMMEND_ONLY`. | Computed multi-horizon forecasts and 4-layer DAG RCA coverage scores, but did not expose an explicit `digital_twin_divergence` scalar or a formal `engines_agree` corroboration safety trip between the time-series predictor and the NetworkX flow graph. | **ADOPTED INTO TEMLOOM v4.1 (`AETH-7.4`):** Added `digital_twin.py` (`digital_twin_divergence`) and `corroborator.py` (`engines_agree`) into `Schema 13` (`prediction_outputs`) and Stage 4 of the Safety Engine so any disagreement between `Models G1–G4` and the NetworkX graph model automatically triggers a Safety Trip downgrade. | 
| **5. Counterfactual Topology Search (`Clonal State-Space Search`)** | `graph_model.py` clones the live NetworkX topology into counterfactual candidate states (`BASELINE`, `REROUTED`, `QOS_THROTTLED`) and scores each candidate against per-service SLA tags (`voip`, `database`, `bulk`) + computes MPLS `lsp_health_score`. | Validated a proposed remediation playbook against Stage 2 (`SERIALIZABLE` lease $\le 80\%$) and Stage 3 (`M/M/1/K` + `Batfish`), but did not pre-score counterfactual graph clones (`BASELINE` vs. `REROUTED` vs. `QOS_THROTTLED`) during RCA. | **ADOPTED INTO TEMLOOM v4.1 (`AETH-7.5`):** Added Clonal State-Space Counterfactual Search (`clonal_search_scores` in `Schema 14`) and `lsp_health_score` (`Schema 8`) so TEMLOOM mathematically ranks `BASELINE`, `REROUTED`, and `QOS_THROTTLED` graph clones before running Stage 2/3 safety verification. | 
| **6. Offline RAG Architecture & Incident Knowledge Base (`IKB`)** | Uses `ikb_manager.py` with two collections—`runbooks` (split semantically by markdown `##` headings) and `incidents` (auto-ingested ACP JSONL logs)—backed by dense-only ChromaDB (`all-MiniLM-L6-v2`). Also includes an **Operator Accept/Reject Feedback loop (`feedback_cli.py`)** tracking false-positive rates per fault class. | Used PostgreSQL 16 `pgvector` (`BAAI/bge-small-en-v1.5` ONNX) + `tsvector` BM25 fused via **Filtered Reciprocal Rank Fusion (`RRF`)** (`100% Recall@3` in `0.61 ms`), with prompt-injection sanitization (`sanitizer.py`), but stored all chunks in a single logical pool without operator Accept/Reject feedback gating. | **HYBRID UPGRADE IN TEMLOOM v4.1 (`AETH-7.6` & `AETH-7.7`):** Retained PostgreSQL 16 `pgvector + tsvector` Hybrid RRF (which outperforms dense-only ChromaDB on exact CLI/BGP mnemonics), while adopting Aether's **Dual-Collection IKB (`runbooks` split by `##` headings + `verified_incidents`)** and **Operator Accept/Reject Feedback Loop (`feedback_cli.py`)** so only `ACCEPTED` / `CONFIRMED_OUTCOME` incidents enter positive precedent retrieval. | 
| **7. Offline LLM Runtime, Q1/Q2/Q3 Framing & Multi-Turn NLQ** | Structures every incident explanation around **Q1 (What fails & when), Q2 (Why risk is elevated), and Q3 (What corrective action to take)**, and provides a stateful **Multi-Turn NLQ Interface (`nlq_interface.py`: `IDLE -> CLARIFY -> CONFIRM -> SIMULATE/REPORT`)** with deterministic keyword/node intent pre-filtering. Uses Ollama on TCP port `11434` with free-form output parsing. | Used `llama-server` (`Qwen2.5-3B/7B-Instruct-Q4_K_M.gguf`) in a `netns=none` sandbox over UNIX socket `/run/temloom/llm.sock` with strict **GBNF grammar enforcement (`copilot_response.gbnf`)** and SQL citation verification, plus deterministic Jinja2 fallback. | **HYBRID UPGRADE IN TEMLOOM v4.1 (`AETH-7.6` & `AETH-7.7`):** Retained TEMLOOM's hardened `netns=none` UNIX-socket `llama-server` and GBNF grammar lock (rejecting unauthenticated TCP loopback and fragile free-form regex parsing), while upgrading `copilot_response.gbnf` and the Jinja2 fallback to explicitly emit **Q1 / Q2 / Q3 situation sections** and adding Aether's **stateful Multi-Turn NLQ state machine (`nlq_interface.py`)**. | 
| **8. Pre-Change Verification & Remediation Execution** | Open-loop remediation: generates CLI commands (click-to-copy or unverified `docker exec` logged in Remediation Log), but explicitly notes in `README.md` that it **does not verify the action worked or auto-roll-back**. | **Closed-loop 4-Stage Safety Gate** (`AST Allowlist` + `SERIALIZABLE Bandwidth Lease <= 80%` + `M/M/1/K RTT <= 25ms` + `Batfish Loop/Blackhole Check`) + **Paired-Router 2PC (`commit confirmed 1`) with 45s post-change verification & `<5s` automatic rollback**. | **RETAINED TEMLOOM CLOSED-LOOP 2PC + ADOPTED CAPTURED CLI TRANSCRIPT (`AETH-7.8`):** Kept TEMLOOM's closed-loop 4-stage safety gate and 2PC auto-rollback, and added Aether's **captured router command stdout/stderr transcript (`execution_stdout_log` in `Schema 15`)** and click-to-copy CLI inspector in Workbench 1. | 
| **9. Simulation Fidelity & Fault-Timing State Machine** | Includes a **Natural Fault-Timing State Machine (`fault_streamer.py`: `QUIET -> FAULT_BURST -> RESOLVE`)** and dual-format FRR/RFC5424 `syslog_parser.py`, plus explicit `127.0.0.1` IPv4 binding to avoid IPv6 `::1` timeouts. Note: Aether's `COMMANDS.md` noted data-plane `eth1/eth2` veth links were missing in its container setup. | Full data-plane veth/tunnel topology and 32 deterministic benchmark scenarios (`A..L, R1..R6, T1..T6, ADV-1..8`), but lacked a continuous natural state-machine streamer (`QUIET -> FAULT_BURST -> RESOLVE`) for open-ended live NOC operation. | **ADOPTED INTO TEMLOOM v4.1 (`DS-1.1A/B/E`):** Kept TEMLOOM's full data-plane veth/tunnel topology (`eth1/eth2` + `overlay-setup.sh` + `qos-setup.sh`), and added Aether's **`fault_streamer.py` (`QUIET -> FAULT_BURST -> RESOLVE`)**, dual-format `syslog_parser.py`, and explicit `127.0.0.1` IPv4 socket binding rule. | 
| **10. Operator GUI & Time-Travel Topology Playback** | 7-view SPA featuring a **Q1/Q2/Q3 Overview Header**, **In-Memory Live Time-Travel Topology Scrubber (`▶ Live`)**, **Autonomy Policy Matrix Editor**, **Remediation Action Log**, and **Signed Air-Gap Compliance Badge**. | 5-Workbench engineering & NOC console (`Workbenches 1–5`) covering Live NOC 2PC, Telemetry/Dataset Pipeline, Simulation/Experiment Replay, 10-Model Registry/Comparator, and Hybrid RAG/LLM Observability. | **ADOPTED INTO TEMLOOM v4.1 (`AETH-7.8` & `Doc 5 v4.1`):** Embedded Aether's **Q1/Q2/Q3 Situation Header**, **In-Memory Live Topology Time-Travel Scrubber**, **Tiered Autonomy Policy Matrix Drawer**, **Click-to-Copy + Captured CLI Transcript Log**, **Operator Accept/Reject Feedback buttons**, and **Signed Air-Gap/Model Integrity Badges** directly into TEMLOOM's 5-Workbench architecture. | 

## 3. Detailed Summary of All Changes Made Across the Deliverable Suite (`v4.0 -> v4.1`)

### 3.1 Changes in `Document 1: Definitive System Architecture` (`temloom_doc1_system_architecture.md` — `v4.1`)

1. **Section 1.1 (Architecture Audit Table):** Updated all 4 capability rows to incorporate `taxonomy.py`, the `QUIET -> FAULT_BURST -> RESOLVE` state machine (`fault_streamer.py`), Predictive Digital Twin Divergence (`digital_twin.py`), Dual-Engine Corroboration (`engines_agree`), Dual-Collection IKB (`ikb_manager.py`), Q1/Q2/Q3 situation framing, stateful Multi-Turn NLQ (`nlq_interface.py`), Clonal State-Space Counterfactual Search, Ed25519 model weight signing (`model_integrity.py`), and active signed air-gap compliance probes (`airgap_compliance.py`).

2. **Section 2.1 (Five Mandatory Telemetry Sources):**

   * Added the **IPv4 Loopback Binding Rule (`127.0.0.1`)** in Source A to prevent silent IPv6 (`::1`) timeout stalls on Linux.

   * Added **Dual-Format FRR Native & RFC 5424 Syslog Parsing (`syslog_parser.py`)** in Source B.

   * Added **Per-Service SLA Tier Mapping (`taxonomy.py`)** and **MPLS LSP Health Scores** in Source C.

   * Added the **Natural Fault-Timing State Machine (`QUIET -> FAULT_BURST -> RESOLVE` via `fault_streamer.py`)** in Source E.

3. **Section 3.2 & 3.3 (Telemetry Pipeline Diagram & Correlation):** Added `taxonomy.py` in the Normaliser stage and **`Predictive Digital Twin (digital_twin.py)` + `Dual-Engine Corroboration Gate (corroborator.py)`** in the Correlation stage, specifying how disagreement (`engines_agree == false`) triggers an automatic Safety Trip downgrade to `RECOMMEND_ONLY`.

4. **Section 4 & 4.1 (Nine-Stage Offline LLM & Dual-Collection IKB Pipeline):**

   * Updated the 9-stage diagram and specification to include **Dual-Collection Hybrid RAG (`runbooks` split semantically by `##` headings + `verified_incidents` gated by operator `ACCEPTED` feedback)** via `ikb_manager.py`.

   * Added **Q1 / Q2 / Q3 Epistemic Operator Framing** (`q1_what_fails_and_when`, `q2_why_risk_elevated`, `q3_validated_corrective_action`) to `copilot_response.gbnf` and the deterministic fallback.

   * Added the **Stateful Multi-Turn NLQ State Machine (`nlq_interface.py`: `IDLE -> CLARIFY -> CONFIRM -> SIMULATE/REPORT`)** with deterministic intent and node pre-filtering.

5. **New Section 5 (Defense-Grade Cryptographic Integrity, Tiered Autonomy & Air-Gap Attestation):**

   * Specified **Ed25519 Model Weight & Calibration Artifact Signing (`temloom/security/model_integrity.py`)**.

   * Specified **Active Zero-Egress Air-Gap Compliance Probe & Signed Attestation (`temloom/security/airgap_compliance.py`)** and the `./run.sh --clab --airgap` dual-namespace execution pattern.

   * Specified the **Tiered Autonomy Policy Matrix with Hard-Locked Safety Floors (`taxonomy.py` + `safety_engine.py`)**.

6. **Section 6 (Six Authoritative Implementation Phases):** Synchronized Phases 1–6 with all new v4.1 modules.

### 3.2 Changes in `Document 2: Engineering Implementation Blueprint` (`temloom_doc2_implementation_blueprint.md` — `v4.1`)

1. **Updated Schemas in Section 1 (`Schemas 1–15`):**

   * **`Schema 3` (`qos_queue_telemetry`) & `Schema 7` (`netflow_ipfix_records`):** Added `service_sla_tag` (`IN ('voip', 'video', 'database', 'bulk', 'default')` governed by `taxonomy.py`).

   * **`Schema 8` (`ipsec_tunnel_telemetry`):** Added `lsp_health_score` (`DOUBLE PRECISION`, `0.0 <= val <= 1.0`, computed by `graph_model.py`).

   * **`Schema 10` (`config_policy_changes`):** Extended to audit changes to `global:policy:autonomy_matrix` and flag `is_unintended_drift = true` if any edit violates `taxonomy.py` safety floors.

   * **`Schema 13` (`prediction_outputs`):** Added `digital_twin_divergence` (`0..1`), `engines_agree` (`BOOLEAN` Dual-Engine Corroboration flag), Top-5 ranked `contributing_features`, and Ed25519-signed `model_version_id` (`v4.1.0-ed25519:...`).

   * **`Schema 14` (`rca_outputs`):** Added `clonal_search_scores` (`JSONB` scoring `{BASELINE, REROUTED, QOS_THROTTLED}` counterfactual topologies) and `operator_feedback` (`IN ('PENDING', 'ACCEPTED', 'REJECTED')`).

   * **`Schema 15` (`remediation_outcomes`):** Added `autonomy_execution_mode` (`IN ('RECOMMEND_ONLY', 'PRE_VALIDATED_STAGED')`) and `execution_stdout_log` (`TEXT` capturing the exact router NETCONF/CLI transcript).

2. **Section 2 (Table 2 — Six-Phase Implementation Plan):** Added `run.sh`, `overlay-setup.sh`, `qos-setup.sh`, `fault_streamer.py`, `taxonomy.py`, `syslog_parser.py`, `digital_twin.py`, `corroborator.py`, `model_integrity.py`, `airgap_compliance.py`, `ikb_manager.py`, `graph_model.py`, `nlq_interface.py`, and `feedback_cli.py` with corresponding verification exit gates.

### 3.3 Changes in `Document 3: Experimental Validation & Benchmarking Plan` (`temloom_doc3_experimental_validation_plan.md` — `v4.1`)

1. **Section 2.1 (Table 1 — 10-Model Benchmark Comparison):** Explicitly documented the comparison against Project Aether's `Recurrent Gated BiLSTM + Attention + EMA Bollinger` architecture (`0.588 FA/hr` and `2.766m` TTI MAE vs. `Model G1`'s `0.350 FA/hr` and `1.379m` TTI MAE) and `Prophet-Style Fourier` model (`6.363 FA/hr`), explaining why `Model G1` is selected for forecasting while adopting Aether's Top-5 feature attribution, Digital Twin divergence, and Dual-Engine graph corroboration.

2. **Section 2.2 (Table 2 — 8 Prediction Tasks):** Updated Tasks 1, 3, and 6 to reflect Digital Twin flow corroboration (`engines_agree`), `digital_twin_divergence`, and MPLS `lsp_health_score`.

3. **Section 3 (Table 3 — Phase 6 End-to-End Scenario Validation):** Expanded Scenario D to also test **Autonomy Policy Threshold Drift (`REROUTE_BRANCH` lowered to `min_conf=0.10` and restored to `0.82`)**, added `engines_agree` and `clonal_search_scores` verification across Scenarios A–D, and added Ed25519 model integrity & active air-gap probe verification to the test suite.

### 3.4 Changes in `Document 4: Requirements Traceability Matrix` (`temloom_doc4_requirements_traceability_matrix.md` — `v4.1`)

1. **Updated Existing Requirements (`DS-1.1A/B/C/E`, `PM-3.1`, `PM-3.3`, `RAG-4.1`):** Added explicit IPv4 loopback binding, dual-format syslog parsing, `service_sla_tag`, `lsp_health_score`, `fault_streamer.py`, `digital_twin_divergence`, `engines_agree`, and Dual-Collection IKB mappings.

2. **Added Eight New Requirements (`AETH-7.1` through `AETH-7.8`):**

   * **`AETH-7.1`:** Ed25519 Cryptographic Model Weight & Artifact Signing (`model_integrity.py`).

   * **`AETH-7.2`:** Active Zero-Egress Air-Gap Compliance Probe & Signed Attestation (`airgap_compliance.py`) + `./run.sh --clab --airgap`.

   * **`AETH-7.3`:** Single Source of Truth Taxonomy & Tiered Autonomy Policy Matrix (`taxonomy.py`).

   * **`AETH-7.4`:** Predictive Digital Twin Divergence (`digital_twin.py`) & Dual-Engine Corroboration Gate (`corroborator.py`).

   * **`AETH-7.5`:** Clonal State-Space Counterfactual Topology Search (`graph_model.py`).

   * **`AETH-7.6`:** Q1 / Q2 / Q3 Structured Situation Framing & Dual-Collection IKB (`ikb_manager.py`).

   * **`AETH-7.7`:** Operator Accept/Reject Feedback Loop (`feedback_cli.py`) & Multi-Turn Intent-Pre-Filtered NLQ (`nlq_interface.py`).

   * **`AETH-7.8`:** Live In-Memory Topology Time-Travel Scrubber & Captured Remediation Transcript (`execution_stdout_log`).

### 3.5 Changes in `Document 5: GUI Overview and Interface Specification` (`temloom_doc5_gui_specification.md` — `v4.1`)

1. **Top Sovereign Status Bar (Section 2):** Added real-time badges for **`[Air-Gap: SIGNED COMPLIANT (0/4 Probes Reachable)]`** and **`[Model Integrity: Ed25519 VERIFIED]`**.

2. **Workbench 1 (Section 3.1):**

   * Upgraded Panel 1A with the **Q1 / Q2 / Q3 Live Situation Header**.

   * Upgraded Panel 1C with **Clonal Counterfactual Scores (`BASELINE / REROUTED / QOS_THROTTLED`)** and the **In-Memory Live Time-Travel Scrubber Slider (`▶ Live`)**.

   * Upgraded Panel 1D with **Click-to-Copy CLI Commands**, **Captured Router Transcript (`execution_stdout_log`)**, and **Operator `Approve (Accept)` / `Reject (False Positive)` feedback buttons**.

   * Added **Panel 1E: Tiered Autonomy Policy Matrix Drawer** (`GET/PUT /api/v1/policy` with `🔒 LOCKED` core rows).

3. **Workbench 2 (Section 3.2):** Added explicit IPv4 `127.0.0.1` collector socket health and dual-format syslog/NetFlow simulator visibility.

4. **Workbench 3 (Section 3.3):** Added the **Natural Fault-Timing State Machine (`QUIET -> FAULT_BURST -> RESOLVE`)** toggle and Ed25519-signed `model_version_id` lock.

5. **Workbench 4 (Section 3.4):** Added **Ed25519 Model Signature Verification badges** (`model_integrity.py`) and the **Operator Accept/Reject False-Positive Rate per Fault Class tracker (`GET /api/v1/models/feedback-stats`)**.

6. **Workbench 5 (Section 3.5):** Added the **Signed Air-Gap Compliance Probe card (`GET /api/v1/security/compliance`)**, **Dual-Collection IKB monitor (`runbooks` + `verified_incidents`)**, and the interactive **Multi-Turn "Ask TEMLOOM" NLQ Console (`POST /api/v1/copilot/nlq`)**.

### 3.6 Changes in `Google Antigravity Master Prompt` (`temloom_antigravity_build_prompt.md` — `v4.1`)

* Synchronized all 8 execution phases (`Phases A–H`), all 16 backlog categories, all 15 schemas (`Schemas 1–15`), all 5 GUI workbenches, and the 14 strict rules with the **TEMLOOM v4.1** specification so Google Antigravity audits and builds the complete upgraded architecture end to end.