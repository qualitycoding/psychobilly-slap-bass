#!/usr/bin/env python3
"""Construct a sealed blind-listening bundle (S-100; D-015/D-070/D-071)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from stubs.psb_contract import make_blind_pairs  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--references", default="fixtures/references")
    parser.add_argument("--candidates", default="build/listening/candidates")
    parser.add_argument("--output", default="build/listening/round-1")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--window", default="start")
    args = parser.parse_args()
    bundle = make_blind_pairs(args.references, args.candidates, args.output,
                              args.seed, args.window)
    print({k: bundle[k] for k in ("pair_count", "reference_a_count",
                                  "reference_b_count", "demo_count")})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
