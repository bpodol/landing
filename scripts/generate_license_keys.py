#!/usr/bin/env python3
"""Generate the Ed25519 key pair used for public free licenses."""

import argparse
import base64
import subprocess
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_KEY_FILE = ROOT / ".license-private-key.b64"
PUBLIC_KEY_FILE = ROOT / "license-public-key.b64"


def private_key_is_ignored() -> bool:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", "check-ignore", "-q", "--", PRIVATE_KEY_FILE.name],
        cwd=ROOT,
        check=False,
    )
    return result.returncode == 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="overwrite an existing private key")
    args = parser.parse_args()

    if not private_key_is_ignored():
        raise SystemExit(f"Refusing to generate: {PRIVATE_KEY_FILE.name} is not ignored by Git")
    if PRIVATE_KEY_FILE.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite existing {PRIVATE_KEY_FILE.name}; use --force explicitly")

    private_key = Ed25519PrivateKey.generate()
    private_raw = private_key.private_bytes(
        serialization.Encoding.Raw,
        serialization.PrivateFormat.Raw,
        serialization.NoEncryption(),
    )
    public_raw = private_key.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    PRIVATE_KEY_FILE.write_text(base64.b64encode(private_raw).decode("ascii") + "\n", encoding="ascii")
    PUBLIC_KEY_FILE.write_text(base64.b64encode(public_raw).decode("ascii") + "\n", encoding="ascii")

    print(f"Created {PRIVATE_KEY_FILE.name}")
    print(f"Created {PUBLIC_KEY_FILE.name}")
    print(f"WARNING: Never commit {PRIVATE_KEY_FILE.name}; store an encrypted offline backup.")
    print(f"Add {PRIVATE_KEY_FILE.name} as the LICENSE_PRIVATE_KEY_B64 GitHub Actions secret.")


if __name__ == "__main__":
    main()
