#!/usr/bin/env python3
"""
temloom/ingestion/freshness_gate.py — Causal 15s Alignment, 64-Bit Monotonic Counter-Wrap
Clamp, Explicit NULL Missingness Gate, and Quarantine DLQ Manager (DS-1.2).
"""

import math
import time
import uuid
from typing import Dict, Any, Optional, Tuple
from temloom.core.database import TemloomDatabase

UINT64_MAX = (1 << 64) - 1


class TelemetryFreshnessAndQualityGate:
    def __init__(self, db: TemloomDatabase = None):
        self.db = db or TemloomDatabase()
        self.missing_streaks: Dict[str, int] = {}
        self.wrap_clamp_count: int = 0
        self.quarantined_count: int = 0

    @staticmethod
    def align_to_15s_bucket(observed_at_utc_ms: int) -> int:
        """Aligns timestamp to causal 15,000 ms ceiling bucket so observed_at_utc_ms <= bucket_15s_utc_ms."""
        rem = observed_at_utc_ms % 15000
        return observed_at_utc_ms if rem == 0 else (observed_at_utc_ms + (15000 - rem))

    def compute_counter_delta(
        self, prev_counter: int, curr_counter: int, max_bps_capacity: float = 10_000_000_000.0, dt_sec: float = 15.0
    ) -> Tuple[int, bool]:
        """Handles 64-bit monotonic counter wraps and clamps impossible unphysical counter spikes (Scenario I)."""
        max_bytes = int((max_bps_capacity / 8.0) * dt_sec * 1.05)
        if curr_counter >= prev_counter:
            delta = curr_counter - prev_counter
            if delta > max_bytes:
                self.wrap_clamp_count += 1
                return max_bytes, True
            return delta, False
        # Counter wrapped or reset
        wrapped_delta = (UINT64_MAX - prev_counter) + curr_counter + 1
        if 0 <= wrapped_delta <= max_bytes:
            self.wrap_clamp_count += 1
            return wrapped_delta, True
        # Router counter reset to small value
        self.wrap_clamp_count += 1
        return min(curr_counter, max_bytes), True

    def evaluate_freshness(
        self, entity_id: str, value: Optional[float], poll_lag_sec: float = 0.0
    ) -> Tuple[Optional[float], bool, str]:
        """
        Never silently replaces NULL/NaN with healthy zeros.
        Returns (preserved_value, is_missing, freshness_state).
        """
        is_missing = (value is None) or (isinstance(value, float) and math.isnan(value)) or (poll_lag_sec > 45.0)
        if is_missing:
            streak = self.missing_streaks.get(entity_id, 0) + 1
            self.missing_streaks[entity_id] = streak
            state = "STALE_TELEMETRY" if (streak >= 3 or poll_lag_sec > 45.0) else "DEGRADED_POLLING"
            return None, True, state

        self.missing_streaks[entity_id] = 0
        state = "DEGRADED_POLLING" if poll_lag_sec > 15.0 else "FRESH"
        return float(value), False, state

    def quarantine_record(self, source_type: str, reason: str, raw_payload: str):
        self.quarantined_count += 1
        now_ms = int(time.time() * 1000)
        self.db.execute_write(
            """INSERT INTO telemetry_quarantine_dlq
               (dlq_id, observed_at_utc_ms, source_type, rejection_reason, raw_payload)
               VALUES (?, ?, ?, ?, ?)""",
            (str(uuid.uuid4()), now_ms, source_type, reason, raw_payload[:2000]),
        )
