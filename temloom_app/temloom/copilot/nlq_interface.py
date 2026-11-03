#!/usr/bin/env python3
"""
temloom/copilot/nlq_interface.py — Stateful Multi-Turn Natural Language Query Engine
(IDLE -> CLARIFY -> CONFIRM -> SIMULATE / REPORT -> IDLE) with deterministic keyword,
node, and SLA-tier intent resolution (AETH-7.7).
"""

from typing import Dict, Any, List
from temloom.core.database import TemloomDatabase
from temloom.copilot.rag_retriever import HybridRRFRetriever

FAULT_INTENT_MAP = {
    "bgp": "BGP_FLAP_CASCADE",
    "ospf": "OSPF_STORM",
    "flap": "BGP_FLAP_CASCADE",
    "rfc2439": "BGP_FLAP_CASCADE",
    "congestion": "LINK_CONGESTION",
    "saturation": "LINK_CONGESTION",
    "queue": "QOS_STARVATION",
    "qos": "QOS_STARVATION",
    "latency": "LATENCY_DRIFT",
    "delay": "LATENCY_DRIFT",
    "tunnel": "TUNNEL_REKEY_EXHAUSTION",
    "ipsec": "TUNNEL_REKEY_EXHAUSTION",
    "rekey": "TUNNEL_REKEY_EXHAUSTION",
    "replay": "ANTI_REPLAY_OVERFLOW",
    "policy": "POLICY_DRIFT",
    "drift": "POLICY_DRIFT",
    "srlg": "AMBIGUOUS_CAUSE_SET",
    "ambiguous": "AMBIGUOUS_CAUSE_SET",
}

KNOWN_NODES = ["pe1", "pe2", "p1", "ce-branch1", "ce-branch2", "ce-hub", "ce-hub1", "ce-dc", "br1", "br2", "wan0", "tun-br1"]
KNOWN_SLAS = ["voip", "video", "database", "bulk"]


class MultiTurnNLQEngine:
    def __init__(self, db: TemloomDatabase = None):
        self.db = db or TemloomDatabase()
        self.retriever = HybridRRFRetriever(self.db)
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
        self.session_state: Dict[str, str] = {}

    def detect_intent(self, question: str, history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        combined = " ".join([h.get("content", "") for h in (history or [])[-2:]] + [question]).lower()
        fault_cat = None
        for kw, cat in FAULT_INTENT_MAP.items():
            if kw in combined:
                fault_cat = cat
                break
        nodes = [n for n in KNOWN_NODES if n in combined]
        sla = next((s for s in KNOWN_SLAS if s in combined), None)
        is_sim = any(w in combined for w in ("simulate", "what if", "clonal", "reroute", "shift"))
        state = "SIMULATE" if is_sim else ("REPORT" if (fault_cat or nodes) else "CLARIFY")
        return {
            "dialogue_state": state,
            "resolved_fault_category": fault_cat or "GENERAL_NOC_QUERY",
            "resolved_nodes": nodes,
            "resolved_sla_tag": sla,
        }

    def ask(self, question: str, session_id: str = "default") -> Dict[str, Any]:
        history = self.sessions.setdefault(session_id, [])
        intent = self.detect_intent(question, history)
        self.session_state[session_id] = intent["dialogue_state"]

        enriched_query = f"{question} {intent['resolved_fault_category']} {' '.join(intent['resolved_nodes'])}"
        rag = self.retriever.retrieve(enriched_query, top_k=3)
        chunks = rag["results"]
        top_chunk = chunks[0] if chunks else None

        if top_chunk:
            nodes_str = ", ".join(intent["resolved_nodes"]) or "global"
            header = (
                f"**[TEMLOOM Air-Gapped Copilot — State: `{intent['dialogue_state']}` | "
                f"Intent: `{intent['resolved_fault_category']}` | Nodes: `{nodes_str}`]**"
            )
            sub = (
                f"Based on retrieved runbook **`{top_chunk['doc_code']}` ({top_chunk['doc_title']})** "
                f"(RRF score={top_chunk['rrf_score']}, BM25 rank=#{top_chunk['bm25_rank']}, pgvector rank=#{top_chunk['vec_rank']}):"
            )
            answer = header + "\n\n" + sub + "\n\n" + top_chunk["sanitized_text"][:650]
        else:
            answer = "No matching runbook chunk found in the local air-gapped knowledge base."

        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": answer})
        return {
            "session_id": session_id,
            "question": question,
            "intent": intent,
            "answer": answer,
            "retrieved_chunks": chunks,
            "history_turns": len(history),
        }

    def reset_session(self, session_id: str = "default"):
        self.sessions[session_id] = []
        self.session_state[session_id] = "IDLE"
