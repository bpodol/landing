#!/usr/bin/env python3
"""Verify the public license and its payload/signature tamper resistance."""

import base64
import json
from datetime import datetime
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


ROOT = Path(__file__).resolve().parents[1]


def decode_urlsafe(value: str) -> bytes:
    return base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)


def expect_invalid(public_key: Ed25519PublicKey, signature: bytes, payload: bytes) -> None:
    try:
        public_key.verify(signature, payload)
    except InvalidSignature:
        return
    raise AssertionError("tampered license unexpectedly verified")


def main() -> None:
    public_raw = base64.b64decode((ROOT / "license-public-key.b64").read_text(encoding="ascii").strip(), validate=True)
    if len(public_raw) != 32:
        raise AssertionError("public key must decode to exactly 32 bytes")
    document = json.loads((ROOT / "licenses" / "free-license.json").read_text(encoding="utf-8"))
    payload_bytes = decode_urlsafe(document["payload"])
    signature = decode_urlsafe(document["signature"])
    public_key = Ed25519PublicKey.from_public_bytes(public_raw)
    public_key.verify(signature, payload_bytes)

    payload = json.loads(payload_bytes.decode("utf-8"))
    assert payload["schema"] == 1
    assert payload["product"] == "plo-rangelab"
    assert payload["license_type"] == "public-free"
    issued = datetime.fromisoformat(payload["issued_at"].replace("Z", "+00:00"))
    expires = datetime.fromisoformat(payload["expires_at"].replace("Z", "+00:00"))
    assert expires > issued
    assert abs((expires - issued).total_seconds() - 35 * 86400) <= 1

    changed_payload = bytearray(payload_bytes)
    changed_payload[0] ^= 1
    expect_invalid(public_key, signature, bytes(changed_payload))
    changed_signature = bytearray(signature)
    changed_signature[0] ^= 1
    expect_invalid(public_key, bytes(changed_signature), payload_bytes)
    print("License signature, fields, 35-day validity, and tamper tests passed")


if __name__ == "__main__":
    main()
