#!/usr/bin/env python3
"""Assert CI artifacts exist, are non-empty and schema-valid."""
import json
import sys
from pathlib import Path

REQUIRED_JSON = [
    "performance.json",
    "repository-audit.json",
    "pip-audit.json",
    "environment.json",
]
REQUIRED_LOGS = ["build.log", "frozen-tests.log", "pluginval-primary.log"]
REQUIRED_DEMO_COUNTS = {"wav": 10, "json": 10, "jsonl": 10}


def fail(msg: str) -> None:
    print(f"verify_artifacts: FAIL {msg}")
    sys.exit(1)


def main() -> int:
    artifacts = Path(sys.argv[1] if len(sys.argv) > 1 else "artifacts")
    if not artifacts.is_dir():
        fail(f"artifacts directory missing: {artifacts}")
    for name in REQUIRED_JSON:
        path = artifacts / name
        if not path.is_file() or path.stat().st_size == 0:
            fail(f"missing or empty {name}")
        try:
            json.loads(path.read_text())
        except json.JSONDecodeError:
            fail(f"invalid JSON {name}")
    for name in REQUIRED_LOGS:
        path = artifacts / name
        if not path.is_file() or path.stat().st_size == 0:
            fail(f"missing or empty {name}")
    for suffix, count in REQUIRED_DEMO_COUNTS.items():
        found = len(list(artifacts.glob(f"demos/*.{suffix}")))
        if found != count:
            fail(f"expected {count} .{suffix} demo files, found {found}")
    for wav in sorted((artifacts / "demos").glob("*.wav")):
        if wav.stat().st_size < 44:
            fail(f"wav too small: {wav.name}")
        if wav.read_bytes()[:4] != b"RIFF":
            fail(f"wav bad magic: {wav.name}")
    print("verify_artifacts: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
