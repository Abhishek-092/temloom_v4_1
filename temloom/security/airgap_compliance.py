#!/usr/bin/env python3
"""
temloom/security/airgap_compliance.py — Active Zero-Egress Air-Gap Compliance Probe
& Ed25519-Signed Attestation Report Generator (AETH-7.2).
"""

import os
import sys
import json
import socket
import hashlib
import argparse
from datetime import datetime, timezone
from typing import Dict, Any, List

from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
from cryptography.exceptions import InvalidSignature

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_KEY_DIR = os.path.join(REPO_ROOT, "keys")

PROBE_TARGETS = [
    ("8.8.8.8", 53, "Google Public DNS"),
    ("1.1.1.1", 53, "Cloudflare Public DNS"),
    ("pypi.org", 443, "PyPI Package Index"),
    ("huggingface.co", 443, "HuggingFace Model Hub"),
]

TIMEOUT_S = 1.5


def _probe_target(host: str, port: int, timeout_s: float = TIMEOUT_S) -> Dict[str, Any]:
    res = {"host": host, "port": port, "reachable": False, "error": None}
    try:
        s = socket.create_connection((host, port), timeout=timeout_s)
        s.close()
        res["reachable"] = True
    except Exception as e:
        res["error"] = type(e).__name__
    return res


def run_compliance_check(key_dir: str = DEFAULT_KEY_DIR) -> Dict[str, Any]:
    """Probes external canary endpoints (all MUST fail in an air-gapped enclave) and signs report."""
    ts = datetime.now(timezone.utc).isoformat()
    probes: List[Dict[str, Any]] = []
    for host, port, label in PROBE_TARGETS:
        r = _probe_target(host, port)
        r["label"] = label
        probes.append(r)

    any_breach = any(p["reachable"] for p in probes)
    report: Dict[str, Any] = {
        "report_type": "temloom_airgap_compliance",
        "timestamp": ts,
        "hostname": socket.gethostname(),
        "hf_hub_offline_env": os.environ.get("HF_HUB_OFFLINE", "1") == "1",
        "status": "NON_COMPLIANT" if any_breach else "COMPLIANT",
        "probes": probes,
        "payload_sha256": None,
        "signature": None,
    }
    return sign_compliance_report(report, key_dir=key_dir)


def sign_compliance_report(report: Dict[str, Any], key_dir: str = DEFAULT_KEY_DIR) -> Dict[str, Any]:
    priv_path = os.path.join(key_dir, "temloom_model_key.pem")
    if not os.path.exists(priv_path):
        from temloom.security.model_integrity import generate_keys
        generate_keys(key_dir)

    with open(priv_path, "rb") as f:
        priv = load_pem_private_key(f.read(), password=None)

    clean_payload = {k: v for k, v in report.items() if k not in ("signature", "payload_sha256")}
    canonical_bytes = json.dumps(clean_payload, sort_keys=True).encode("utf-8")
    digest = hashlib.sha256(canonical_bytes).hexdigest()
    sig = priv.sign(digest.encode("utf-8"))
    report["payload_sha256"] = digest
    report["signature"] = sig.hex()
    return report


def verify_compliance_report(report: Dict[str, Any], key_dir: str = DEFAULT_KEY_DIR) -> bool:
    pub_path = os.path.join(key_dir, "temloom_model_key.pub.pem")
    if not os.path.exists(pub_path) or not report.get("signature"):
        return False
    with open(pub_path, "rb") as f:
        pub = load_pem_public_key(f.read())

    clean_payload = {k: v for k, v in report.items() if k not in ("signature", "payload_sha256")}
    canonical_bytes = json.dumps(clean_payload, sort_keys=True).encode("utf-8")
    digest = hashlib.sha256(canonical_bytes).hexdigest()
    if digest != report.get("payload_sha256"):
        return False
    try:
        pub.verify(bytes.fromhex(report["signature"]), digest.encode("utf-8"))
        return True
    except InvalidSignature:
        return False


def main():
    parser = argparse.ArgumentParser(description="TEMLOOM Active Air-Gap Compliance Attestation")
    parser.add_argument("--out", help="Output path for signed JSON report")
    parser.add_argument("--verify", help="Verify an existing JSON report")
    args = parser.parse_args()

    if args.verify:
        with open(args.verify, "r") as f:
            rep = json.load(f)
        ok = verify_compliance_report(rep)
        print(f"Verification: {'VALID' if ok else 'INVALID'}")
        sys.exit(0 if ok else 1)

    rep = run_compliance_check()
    if args.out:
        with open(args.out, "w") as f:
            json.dump(rep, f, indent=2)
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()
