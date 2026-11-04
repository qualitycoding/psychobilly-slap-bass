#!/usr/bin/env python3
"""Cross-platform frozen-manifest verification (Windows replacement for sha256sum).

Fails non-zero if any frozen file is missing or its SHA-256 differs.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tests" / "FROZEN_MANIFEST.sha256"


def main() -> int:
    if not MANIFEST.exists():
        print(f"missing manifest: {MANIFEST}")
        return 1
    failures = []
    for line in MANIFEST.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        expected, _, rel = line.partition("  ")
        if not rel:
            # tolerate "<hash> *<path>" binary marker
            expected, _, rel = line.partition(" *")
        path = ROOT / rel
        if not path.exists():
            failures.append(f"MISSING {rel}")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != expected:
            failures.append(f"HASH-MISMATCH {rel}")
    if failures:
        print("\n".join(failures))
        return 1
    print("frozen manifest OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
