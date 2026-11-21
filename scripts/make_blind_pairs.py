#!/usr/bin/env python3
"""Build a sealed blind A/B listening bundle (S-100 / D-015).

The random seed is recorded here and in the sealed key; keep it under
version control so the bundle layout is reproducible.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from stubs.psb_contract import make_blind_pairs  # noqa: E402

DEFAULT_SEED = 0x50534C41


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--references", default="fixtures/references")
    parser.add_argument("--candidates", default="build/listening/candidates")
    parser.add_argument("--output", default="build/listening/round-1")
    parser.add_argument("--window", default="start", choices=["start", "articulation"])
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    bundle = make_blind_pairs(args.references, args.candidates, args.output,
                              args.seed, args.window)
    print(json.dumps({k: bundle[k] for k in
                      ("pair_count", "reference_a_count", "reference_b_count",
                       "window", "output_dir")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
