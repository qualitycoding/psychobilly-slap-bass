#!/usr/bin/env python3
"""Verify that every frozen test fails only because its adapter is a stub."""
import json
import re
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[3]
env = dict(__import__("os").environ)
env["PYTHONPATH"] = "/mnt/agents/work/toolchain/python-main:" + str(root)
result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-v"], cwd=root,
                        env=env, text=True, capture_output=True)
log = result.stdout + result.stderr
(root / "research/spikes/freeze/red-unittest.txt").write_text(log)
ran = re.search(r"Ran (\d+) tests", log)
count = int(ran.group(1)) if ran else 0
not_implemented = log.count("NotImplementedError: planning stub: implement the compiled-engine adapter")
errors_match = re.search(r"FAILED \(errors=(\d+)\)", log)
error_count = int(errors_match.group(1)) if errors_match else 0
unexpected = [token for token in ("SyntaxError", "ModuleNotFoundError", "FileNotFoundError", "NameError", "TypeError") if token in log]
report = {"test_count": count, "error_count": error_count, "not_implemented_count": not_implemented, "unexpected_errors": unexpected,
          "subprocess_exit_code": result.returncode, "clean_red": count > 0 and error_count == not_implemented and not_implemented >= count and " ... ok" not in log and not unexpected and result.returncode != 0}
(root / "research/spikes/freeze/red-output.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
raise SystemExit(0 if report["clean_red"] else 1)
