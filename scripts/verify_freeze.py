#!/usr/bin/env python3
"""Cross-platform frozen-file integrity check (Windows replacement for sha256sum -c)."""
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "tests" / "FROZEN_MANIFEST.sha256"


def main() -> int:
    failures = 0
    checked = 0
    for line in MANIFEST.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        digest, rel = line.split(None, 1)
        path = ROOT / rel
        checked += 1
        if not path.is_file():
            print(f"MISSING {rel}")
            failures += 1
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != digest:
            print(f"CHANGED {rel}")
            failures += 1
        else:
            print(f"OK {rel}")
    print(f"{checked - failures}/{checked} frozen files verified")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
