#!/usr/bin/env python3
"""
temloom/security/audit_ledger.py — Tamper-Evident SHA-256 Hash-Chained Audit Ledger.
Every state transition, safety gate check, operator feedback, policy matrix update,
and 2PC execution is cryptographically linked to the previous record's SHA-256 hash.
"""

import hashlib
import json
import time
from typing import Dict, Any, List, Tuple
from temloom.core.database import TemloomDatabase

GENESIS_HASH = "0" * 64


class TamperEvidentAuditLedger:
    def __init__(self, db: TemloomDatabase = None):
        self.db = db or TemloomDatabase()

    def append_event(
        self,
        actor_id: str,
        actor_role: str,
        action_type: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        now_ms = int(time.time() * 1000)
        rows = self.db.execute_query(
            "SELECT entry_hash FROM audit_log_chain ORDER BY seq_id DESC LIMIT 1"
        )
        prev_hash = rows[0]["entry_hash"] if rows else GENESIS_HASH
        payload_json = json.dumps(payload, sort_keys=True)
        canonical_str = f"{now_ms}|{actor_id}|{actor_role}|{action_type}|{payload_json}|{prev_hash}"
        entry_hash = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

        seq_id = self.db.execute_write(
            """INSERT INTO audit_log_chain
               (logged_at_utc_ms, actor_id, actor_role, action_type, payload_json, prev_hash, entry_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (now_ms, actor_id, actor_role, action_type, payload_json, prev_hash, entry_hash),
        )
        return {
            "seq_id": seq_id,
            "logged_at_utc_ms": now_ms,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "action_type": action_type,
            "prev_hash": prev_hash,
            "entry_hash": entry_hash,
        }

    def verify_chain(self) -> Tuple[bool, int, str]:
        rows = self.db.execute_query("SELECT * FROM audit_log_chain ORDER BY seq_id ASC")
        expected_prev = GENESIS_HASH
        for r in rows:
            if r["prev_hash"] != expected_prev:
                return False, r["seq_id"], f"Broken prev_hash at seq_id={r['seq_id']}"
            canonical_str = (
                f"{r['logged_at_utc_ms']}|{r['actor_id']}|{r['actor_role']}|"
                f"{r['action_type']}|{r['payload_json']}|{r['prev_hash']}"
            )
            recomputed = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
            if recomputed != r["entry_hash"]:
                return False, r["seq_id"], f"Tampered payload at seq_id={r['seq_id']}"
            expected_prev = r["entry_hash"]
        return True, len(rows), "OK"

    def list_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        rows = self.db.execute_query(
            "SELECT * FROM audit_log_chain ORDER BY seq_id DESC LIMIT ?", (limit,)
        )
        for r in rows:
            try:
                r["payload"] = json.loads(r["payload_json"])
            except Exception:
                r["payload"] = {}
        return rows
