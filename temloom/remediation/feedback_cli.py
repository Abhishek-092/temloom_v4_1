#!/usr/bin/env python3
"""
temloom/remediation/feedback_cli.py — Operator Accept/Reject Feedback Processor &
Per-Class Empirical False-Positive Rate Tracker.
"""

import argparse
import json
import os
from collections import defaultdict
from typing import Dict, Any, List
from temloom.core.database import TemloomDatabase
from temloom.copilot.ikb_manager import DualCollectionIKBManager, INCIDENTS_PATH
from temloom.security.audit_ledger import TamperEvidentAuditLedger


class OperatorFeedbackManager:
    def __init__(self, db: TemloomDatabase = None):
        self.db = db or TemloomDatabase()
        self.audit = TamperEvidentAuditLedger(self.db)

    def record_feedback(
        self, incident_id: str, feedback: str, operator_id: str = "noc_operator_1"
    ) -> Dict[str, Any]:
        fb_norm = feedback.strip().upper()
        if fb_norm not in ("ACCEPTED", "REJECTED"):
            raise ValueError("feedback must be ACCEPTED or REJECTED")

        self.db.execute_write(
            "UPDATE rca_outputs SET operator_feedback = ? WHERE incident_id = ?",
            (fb_norm, incident_id),
        )

        # If ACCEPTED, append to verified_incidents JSONL and sync into RAG IKB
        if fb_norm == "ACCEPTED":
            rows = self.db.execute_query(
                """SELECT r.incident_id, p.issue_category, p.entity_canonical_id, p.estimated_tti_min
                   FROM rca_outputs r
                   LEFT JOIN prediction_outputs p ON r.incident_id = p.linked_incident_id
                   WHERE r.incident_id = ? LIMIT 1""",
                (incident_id,),
            )
            cat = rows[0]["issue_category"] if rows and rows[0].get("issue_category") else "LINK_CONGESTION"
            ent = rows[0]["entity_canonical_id"] if rows and rows[0].get("entity_canonical_id") else "core:mpls:link:mpls-link-mab-1"
            os.makedirs(os.path.dirname(INCIDENTS_PATH), exist_ok=True)
            with open(INCIDENTS_PATH, "a") as f:
                f.write(json.dumps({
                    "incident_id": incident_id,
                    "issue_category": cat,
                    "entity_canonical_id": ent,
                    "operator_feedback": "ACCEPTED",
                    "summary": f"Operator-verified incident {incident_id[:8]} ({cat} on {ent}): confirmed root cause and mitigation.",
                }) + "\n")
            DualCollectionIKBManager(self.db).ingest_verified_incidents()

        self.audit.append_event(
            actor_id=operator_id,
            actor_role="NOC_OPERATOR",
            action_type=f"INCIDENT_FEEDBACK_{fb_norm}",
            payload={"incident_id": incident_id, "feedback": fb_norm},
        )
        return {"incident_id": incident_id, "operator_feedback": fb_norm}

    def compute_fp_stats(self) -> Dict[str, Any]:
        rows = self.db.execute_query(
            """SELECT COALESCE(p.issue_category, 'LINK_CONGESTION') AS issue_category,
                      r.operator_feedback
               FROM rca_outputs r
               LEFT JOIN prediction_outputs p ON r.incident_id = p.linked_incident_id"""
        )
        by_class = defaultdict(lambda: {"total_labelled": 0, "accepted": 0, "rejected_fp": 0, "pending": 0})
        for r in rows:
            cat = r["issue_category"]
            fb = (r["operator_feedback"] or "PENDING").upper()
            if fb == "ACCEPTED":
                by_class[cat]["total_labelled"] += 1
                by_class[cat]["accepted"] += 1
            elif fb == "REJECTED":
                by_class[cat]["total_labelled"] += 1
                by_class[cat]["rejected_fp"] += 1
            else:
                by_class[cat]["pending"] += 1

        stats = {}
        for cat, d in by_class.items():
            tot = d["total_labelled"]
            fp_rate = round((d["rejected_fp"] / tot) * 100.0, 2) if tot > 0 else 0.0
            stats[cat] = {**d, "fp_rate_pct": fp_rate}
        return {"by_fault_class": stats, "total_incidents": len(rows)}


def main():
    ap = argparse.ArgumentParser(description="TEMLOOM Operator Feedback CLI")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--incident-id")
    ap.add_argument("--feedback", choices=["ACCEPTED", "REJECTED", "accepted", "rejected"])
    args = ap.parse_args()

    mgr = OperatorFeedbackManager()
    if args.incident_id and args.feedback:
        res = mgr.record_feedback(args.incident_id, args.feedback)
        print(json.dumps(res, indent=2))
    else:
        print(json.dumps(mgr.compute_fp_stats(), indent=2))


if __name__ == "__main__":
    main()
