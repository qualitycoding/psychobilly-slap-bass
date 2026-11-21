#!/usr/bin/env python3
"""Score recorded blind-listening answers against the sealed key."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from stubs.psb_contract import score_blind  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle_dir")
    parser.add_argument("answers", help="12 letters, e.g. AABBABAABABA or a JSON file")
    args = parser.parse_args()
    if Path(args.answers).is_file():
        answers = json.loads(Path(args.answers).read_text())
    else:
        answers = [ch.strip().upper() for ch in args.answers.split(",")]
    result = score_blind(args.bundle_dir, answers)
    print(json.dumps(result, indent=2))
    return 0 if result["numeric_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
