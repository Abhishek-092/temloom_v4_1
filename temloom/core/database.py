#!/usr/bin/env python3
"""
temloom/core/database.py — Air-Gapped Persistence & SERIALIZABLE Lease Engine.
Supports embedded transactional SQLite (zero external daemon required for instant
local / air-gapped execution) and PostgreSQL 16 + VictoriaMetrics in container deployments.
"""

import os
import json
import sqlite3
import tempfile
import threading
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple

DEFAULT_DB_PATH = os.environ.get(
    "TEMLOOM_DB_PATH",
    os.path.join(tempfile.gettempdir(), "temloom_v4_1.db"),
)
MIGRATION_001_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "db", "migrations", "001_init_temloom_v4_1.sql",
)


class TemloomDatabase:
    """Thread-safe transactional database engine enforcing Schemas 1-15 and SERIALIZABLE leases."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._lock = threading.RLock()
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=15.0, isolation_level="IMMEDIATE")
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=MEMORY;")
        conn.execute("PRAGMA synchronous=OFF;")
        return conn

    def _init_schema(self):
        with self._lock:
            conn = self._connect()
            try:
                if os.path.exists(MIGRATION_001_PATH):
                    with open(MIGRATION_001_PATH, "r") as f:
                        sql = f.read()
                    conn.executescript(sql)
                conn.commit()
            finally:
                conn.close()

    def execute_write(self, query: str, params: tuple = ()) -> int:
        with self._lock:
            conn = self._connect()
            try:
                cur = conn.execute(query, params)
                conn.commit()
                return cur.lastrowid or 0
            finally:
                conn.close()

    def execute_query(self, query: str, params: tuple = (), role: str = "temloom_core_rw") -> List[Dict[str, Any]]:
        # Enforce strict anti-leakage and role separation:
        q_low = query.lower()
        if role == "feature_extractor" and ("injected_fault_records" in q_low or "ground_truth_incident_labels" in q_low):
            raise PermissionError("ANTI-LEAKAGE VIOLATION: Feature extractor is strictly forbidden from reading ground-truth tables!")
        if role == "temloom_copilot_ro" and any(w in q_low for w in ("insert ", "update ", "delete ", "drop ", "alter ")):
            raise PermissionError("RBAC VIOLATION: temloom_copilot_ro has strictly SELECT-only access!")
        with self._lock:
            conn = self._connect()
            try:
                cur = conn.execute(query, params)
                return [dict(r) for r in cur.fetchall()]
            finally:
                conn.close()

    def acquire_bandwidth_lease(
        self,
        target_path_id: str,
        incident_id: str,
        current_load_mbps: float,
        requested_mbps: float,
        capacity_mbps: float,
        max_util_pct: float = 80.0,
        ttl_ms: int = 120000,
    ) -> Tuple[bool, Optional[str], float]:
        """
        Stage 2 Atomic SERIALIZABLE Bandwidth Reservation Lease.
        Prevents concurrent TOCTOU race conditions when multiple incidents attempt to
        divert traffic onto the same backup tunnel/path simultaneously.
        """
        now_ms = int(time.time() * 1000)
        with self._lock:
            conn = self._connect()
            try:
                conn.execute("BEGIN IMMEDIATE")
                # Expire old leases first
                conn.execute(
                    "UPDATE bandwidth_reservation_leases SET lease_state = 'EXPIRED' WHERE expires_at_utc_ms <= ? AND lease_state = 'ACTIVE'",
                    (now_ms,),
                )
                row = conn.execute(
                    "SELECT COALESCE(SUM(reserved_mbps), 0.0) AS in_flight FROM bandwidth_reservation_leases WHERE target_path_id = ? AND lease_state = 'ACTIVE' AND incident_id != ?",
                    (target_path_id, incident_id),
                ).fetchone()
                in_flight_mbps = float(row["in_flight"]) if row else 0.0
                projected_mbps = current_load_mbps + in_flight_mbps + requested_mbps
                projected_pct = (projected_mbps / max(1.0, capacity_mbps)) * 100.0

                if projected_pct > max_util_pct:
                    conn.rollback()
                    return False, None, round(projected_pct, 2)

                lease_id = str(uuid.uuid4())
                conn.execute(
                    """INSERT INTO bandwidth_reservation_leases
                       (lease_id, target_path_id, incident_id, reserved_mbps, created_at_utc_ms, expires_at_utc_ms, lease_state)
                       VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE')""",
                    (lease_id, target_path_id, incident_id, requested_mbps, now_ms, now_ms + ttl_ms),
                )
                conn.commit()
                return True, lease_id, round(projected_pct, 2)
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def release_bandwidth_lease(self, lease_id: str, new_state: str = "RELEASED"):
        self.execute_write(
            "UPDATE bandwidth_reservation_leases SET lease_state = ? WHERE lease_id = ?",
            (new_state, lease_id),
        )
