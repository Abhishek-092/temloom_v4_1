#!/usr/bin/env python3
"""temloom/copilot/rag_indexer.py — Wrapper exposing DualCollectionIKBManager indexing."""
from temloom.copilot.ikb_manager import DualCollectionIKBManager

def reindex_all(db=None):
    mgr = DualCollectionIKBManager(db=db)
    return mgr.seed_all()
