#!/usr/bin/env python3
"""Score a recorded blind-listening round (S-LISTEN; D-028)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from stubs.psb_contract import score_blind  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", default="build/listening/round-1")
    parser.add_argument("--answers", required=True,
                        help="twelve letters, e.g. ABBAAABBAABB (recorded before decoding)")
    args = parser.parse_args()
    answers = list(args.answers.strip().upper())
    if len(answers) != 12 or any(a not in "AB" for a in answers):
        print("answers must be exactly twelve letters A or B")
        return 2
    result = score_blind(args.bundle, answers)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["numeric_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
