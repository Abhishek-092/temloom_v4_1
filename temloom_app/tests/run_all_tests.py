#!/usr/bin/env python3
"""
tests/run_all_tests.py — Zero-Dependency Universal Test Runner for TEMLOOM v4.1.
Discovers and executes every `test_*` function across all 8 test modules in `tests/`,
automatically injecting `temp_db` fixtures where requested.
"""

import glob
import importlib.util
import inspect
import os
import sys
import tempfile
import traceback

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from temloom.core.database import TemloomDatabase


def run_suite() -> int:
    test_dir = os.path.dirname(os.path.abspath(__file__))
    test_files = sorted(glob.glob(os.path.join(test_dir, "test_*.py")))
    passed = 0
    failed = 0

    print("=" * 72)
    print("  TEMLOOM v4.1 — Automated Unit, Integration, Security & E2E Test Suite")
    print("=" * 72)

    for fpath in test_files:
        mod_name = os.path.basename(fpath)[:-3]
        spec = importlib.util.spec_from_file_location(mod_name, fpath)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        for name, fn in inspect.getmembers(mod, inspect.isfunction):
            if not name.startswith("test_"):
                continue
            sig = inspect.signature(fn)
            try:
                if "temp_db" in sig.parameters:
                    with tempfile.TemporaryDirectory() as tmpdir:
                        tdb = TemloomDatabase(db_path=os.path.join(tmpdir, "test.db"))
                        fn(tdb)
                else:
                    fn()
                print(f"  [PASS] {mod_name}::{name}")
                passed += 1
            except Exception as e:
                print(f"  [FAIL] {mod_name}::{name} -> {e}")
                traceback.print_exc()
                failed += 1

    print("=" * 72)
    print(f"  Test Summary: {passed} passed, {failed} failed (Total: {passed + failed})")
    print("=" * 72)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_suite())
