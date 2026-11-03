#!/usr/bin/env python3
"""
temloom/security/model_integrity.py — Ed25519 Model Weight & Artifact Signing & Verification
(TEMLOOM Models G1-G4, ONNX & GGUF Integrity Attestation).
"""

import os
import sys
import json
import hashlib
import argparse
from typing import Dict, List, Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding, PublicFormat, PrivateFormat, NoEncryption,
    load_pem_private_key, load_pem_public_key,
)
from cryptography.exceptions import InvalidSignature

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_KEY_DIR = os.path.join(REPO_ROOT, "keys")
DEFAULT_MODEL_DIR = os.path.join(REPO_ROOT, "saved_models")
SIG_MANIFEST = "model_signatures.json"

DEFAULT_MODEL_FILES = [
    "model_g1_congestion_v4_1.json",
    "model_g2_routing_v4_1.json",
    "model_g3_tunnel_v4_1.json",
    "model_g4_policy_v4_1.json",
]


class IntegrityError(RuntimeError):
    """Raised when any model artifact fails Ed25519 cryptographic signature verification."""


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_keys(key_dir: str = DEFAULT_KEY_DIR) -> Dict[str, str]:
    os.makedirs(key_dir, exist_ok=True)
    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()

    priv_path = os.path.join(key_dir, "temloom_model_key.pem")
    pub_path = os.path.join(key_dir, "temloom_model_key.pub.pem")

    with open(priv_path, "wb") as f:
        f.write(priv.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()))
    os.chmod(priv_path, 0o600)

    with open(pub_path, "wb") as f:
        f.write(pub.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo))

    return {"private_key": priv_path, "public_key": pub_path}


def sign_models(
    key_dir: str = DEFAULT_KEY_DIR,
    model_dir: str = DEFAULT_MODEL_DIR,
    model_files: Optional[List[str]] = None,
) -> Dict[str, Dict[str, str]]:
    priv_path = os.path.join(key_dir, "temloom_model_key.pem")
    if not os.path.exists(priv_path):
        generate_keys(key_dir)

    with open(priv_path, "rb") as f:
        priv = load_pem_private_key(f.read(), password=None)

    files_to_sign = model_files or DEFAULT_MODEL_FILES
    manifest: Dict[str, Dict[str, str]] = {}
    for fname in files_to_sign:
        fpath = os.path.join(model_dir, fname)
        if not os.path.exists(fpath):
            continue
        digest = sha256_file(fpath)
        sig = priv.sign(digest.encode("utf-8"))
        manifest[fname] = {
            "sha256": digest,
            "signature": sig.hex(),
            "algorithm": "Ed25519",
        }

    out_path = os.path.join(model_dir, SIG_MANIFEST)
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)
    return manifest


def verify_all_models(
    key_dir: str = DEFAULT_KEY_DIR,
    model_dir: str = DEFAULT_MODEL_DIR,
    model_files: Optional[List[str]] = None,
) -> Dict[str, str]:
    pub_path = os.path.join(key_dir, "temloom_model_key.pub.pem")
    manifest_path = os.path.join(model_dir, SIG_MANIFEST)
    files_to_check = model_files or DEFAULT_MODEL_FILES

    if not os.path.exists(pub_path):
        return {f: "NO_KEY" for f in files_to_check}
    if not os.path.exists(manifest_path):
        return {f: "NO_SIGNATURE" for f in files_to_check}

    with open(pub_path, "rb") as f:
        pub = load_pem_public_key(f.read())
    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    results: Dict[str, str] = {}
    tampered: List[str] = []
    for fname in files_to_check:
        fpath = os.path.join(model_dir, fname)
        if not os.path.exists(fpath):
            results[fname] = "MISSING"
            continue
        if fname not in manifest:
            results[fname] = "NO_SIGNATURE"
            continue
        expected_hash = manifest[fname]["sha256"]
        sig_bytes = bytes.fromhex(manifest[fname]["signature"])
        actual_hash = sha256_file(fpath)
        if actual_hash != expected_hash:
            results[fname] = "TAMPERED"
            tampered.append(fname)
            continue
        try:
            pub.verify(sig_bytes, actual_hash.encode("utf-8"))
            results[fname] = "OK"
        except InvalidSignature:
            results[fname] = "TAMPERED"
            tampered.append(fname)

    if tampered:
        raise IntegrityError(
            f"CRITICAL SECURITY ALERT: Model Ed25519 integrity check FAILED for {tampered}. "
            f"Dropping to SUPERVISED_FALLBACK mode — autonomous execution disabled."
        )
    return results


def main():
    parser = argparse.ArgumentParser(description="TEMLOOM Ed25519 Model Integrity Manager")
    parser.add_argument("--generate-keys", action="store_true")
    parser.add_argument("--sign", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--key-dir", default=DEFAULT_KEY_DIR)
    parser.add_argument("--model-dir", default=DEFAULT_MODEL_DIR)
    args = parser.parse_args()

    if args.generate_keys:
        paths = generate_keys(args.key_dir)
        print(f"[+] Generated Ed25519 keys: {paths}")
    elif args.sign:
        manifest = sign_models(args.key_dir, args.model_dir)
        print(f"[+] Signed {len(manifest)} model artifacts.")
    elif args.verify:
        res = verify_all_models(args.key_dir, args.model_dir)
        print(json.dumps(res, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
