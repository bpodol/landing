#!/usr/bin/env python3
"""Issue the monthly, universally usable signed public license."""

import base64
import binascii
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "licenses" / "free-license.json"


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def main() -> None:
    encoded_key = os.environ.get("LICENSE_PRIVATE_KEY_B64")
    if not encoded_key:
        raise SystemExit("LICENSE_PRIVATE_KEY_B64 is missing")
    try:
        private_raw = base64.b64decode(encoded_key, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise SystemExit("LICENSE_PRIVATE_KEY_B64 is not valid standard Base64") from exc
    if len(private_raw) != 32:
        raise SystemExit("LICENSE_PRIVATE_KEY_B64 must decode to exactly 32 bytes")

    now = datetime.now(timezone.utc).replace(microsecond=0)
    expires = now + timedelta(days=35)
    iso = lambda value: value.isoformat().replace("+00:00", "Z")
    payload = {
        "schema": 1,
        "product": "plo-rangelab",
        "license_type": "public-free",
        "key_id": "free-license-v1",
        "serial": f"free-{now:%Y-%m}",
        "issued_at": iso(now),
        "expires_at": iso(expires),
    }
    payload_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    signature = Ed25519PrivateKey.from_private_bytes(private_raw).sign(payload_bytes)
    document = {"payload": b64url(payload_bytes), "signature": b64url(signature)}

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{OUTPUT.name}.", dir=OUTPUT.parent, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as output_file:
            json.dump(document, output_file, sort_keys=True, separators=(",", ":"))
            output_file.write("\n")
            output_file.flush()
            os.fsync(output_file.fileno())
        os.replace(temporary_name, OUTPUT)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
