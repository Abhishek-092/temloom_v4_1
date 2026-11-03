#!/usr/bin/env python3
"""
temloom/copilot/rag_retriever.py — Hybrid Lexical (BM25) + Vector Cosine Retriever
with Filtered Reciprocal Rank Fusion (RRF, k=20) over `rag_knowledge_chunks`.
"""

import json
import re
import time
from typing import Dict, Any, List
from temloom.core.database import TemloomDatabase
from temloom.copilot.ikb_manager import compute_deterministic_embedding_384d, DualCollectionIKBManager


class HybridRRFRetriever:
    def __init__(self, db: TemloomDatabase = None, rrf_k: int = 20):
        self.db = db or TemloomDatabase()
        self.rrf_k = rrf_k
        rows = self.db.execute_query("SELECT COUNT(*) AS c FROM rag_knowledge_chunks")
        if not rows or rows[0]["c"] == 0:
            DualCollectionIKBManager(self.db).seed_all()

    def retrieve(self, query_text: str, top_k: int = 3) -> Dict[str, Any]:
        t0 = time.perf_counter()
        chunks = self.db.execute_query(
            "SELECT * FROM rag_knowledge_chunks", role="temloom_copilot_ro"
        )
        if not chunks:
            return {"results": [], "latency_ms": 0.0}

        q_tokens = set(re.findall(r"[a-z0-9_\-\.]+", query_text.lower()))
        q_emb = compute_deterministic_embedding_384d(query_text)

        bm25_scores = []
        vec_scores = []

        for idx, ch in enumerate(chunks):
            txt_low = (ch["doc_title"] + " " + ch["sanitized_text"] + " " + ch["protocol_tags"]).lower()
            c_tokens = re.findall(r"[a-z0-9_\-\.]+", txt_low)
            token_set = set(c_tokens)
            overlap = sum(2.5 if qt in ch["chunk_id"].lower() else (1.5 if qt in token_set else 0.0) for qt in q_tokens)
            bm25_scores.append((idx, overlap))

            c_emb = json.loads(ch["embedding_json"])
            dot = sum(a * b for a, b in zip(q_emb, c_emb))
            vec_scores.append((idx, dot))

        bm25_ranked = [idx for idx, _ in sorted(bm25_scores, key=lambda x: x[1], reverse=True)]
        vec_ranked = [idx for idx, _ in sorted(vec_scores, key=lambda x: x[1], reverse=True)]

        bm25_pos = {idx: rank + 1 for rank, idx in enumerate(bm25_ranked)}
        vec_pos = {idx: rank + 1 for rank, idx in enumerate(vec_ranked)}

        fused = []
        for idx, ch in enumerate(chunks):
            r_bm25 = bm25_pos[idx]
            r_vec = vec_pos[idx]
            rrf_score = (1.0 / (self.rrf_k + r_bm25)) + (1.0 / (self.rrf_k + r_vec))
            fused.append({
                "chunk_id": ch["chunk_id"],
                "doc_code": ch["chunk_id"].split("::")[0],
                "collection_type": ch["collection_type"],
                "doc_title": ch["doc_title"],
                "sanitized_text": ch["sanitized_text"],
                "bm25_rank": r_bm25,
                "vec_rank": r_vec,
                "rrf_score": round(rrf_score, 5),
                "sha256_hash": ch["sha256_hash"],
            })

        fused.sort(key=lambda x: x["rrf_score"], reverse=True)
        latency_ms = round((time.perf_counter() - t0) * 1000.0, 3)
        return {"results": fused[:top_k], "latency_ms": latency_ms}
