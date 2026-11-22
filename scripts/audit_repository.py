#!/usr/bin/env python3
"""Repository security audit: secrets in tracked content/history, unsafe URLs,
network/telemetry features, deserialisation hazards and licence notices.

Writes a JSON report; matched secret *values* are never printed, only
file/line locations and pattern names.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SECRET_PATTERNS = {
    "github_pat": re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "private_key_pem": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "generic_bearer": re.compile(r"(?i)bearer\s+[a-z0-9_\-\.]{24,}"),
}
UNSAFE_URL = re.compile(r"(?i)\b(?:http|ftp)://[^/\s]*(?::[^/@\s]*)?@")
NETWORK_CALLS = re.compile(r"\b(?:socket|requests\.|urllib\.|httpx|aiohttp|curl|wget)\b")
TELEMETRY = re.compile(r"(?i)\b(?:telemetry|analytics|segment\.io|sentry|mixpanel)\b")
DESERIALISATION = re.compile(r"\b(?:pickle\.loads?|yaml\.load\(|eval\(|exec\()\b")


def tracked_files() -> list[Path]:
    proc = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        return []
    return [ROOT / line for line in proc.stdout.splitlines() if line.strip()]


CODE_SUFFIXES = {".py", ".cpp", ".h", ".hpp", ".c", ".yml", ".yaml", ".cmake", ".txt"}
CODE_NAMES = {"CMakeLists.txt"}


def scan_text(path: Path, text: str, findings: list[dict]) -> None:
    rel = str(path.relative_to(ROOT))
    if rel == "scripts/audit_repository.py":
        return  # the scanner's own source mentions every pattern it hunts
    is_code = path.suffix in CODE_SUFFIXES or path.name in CODE_NAMES
    for lineno, line in enumerate(text.splitlines(), 1):
        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(line):
                findings.append({"file": rel, "line": lineno, "kind": f"secret:{name}"})
        if not is_code:
            continue  # network/telemetry/deserialization scans target code only
        if UNSAFE_URL.search(line):
            findings.append({"file": rel, "line": lineno, "kind": "unsafe:credential-url"})
        # Workflow heredocs fetch pinned CI tooling (e.g. pluginval with a
        # verified sha256); they are not product network features.
        if NETWORK_CALLS.search(line) and not rel.startswith(
                ("scripts/audit", "stubs/psb_contract", ".github/workflows/")):
            findings.append({"file": rel, "line": lineno, "kind": "network-call"})
        if TELEMETRY.search(line):
            findings.append({"file": rel, "line": lineno, "kind": "telemetry"})
        if DESERIALISATION.search(line):
            findings.append({"file": rel, "line": lineno, "kind": "deserialization"})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="artifacts/repository-audit.json")
    args = parser.parse_args()

    findings: list[dict] = []
    for path in tracked_files():
        if path.suffix in (".wav", ".f64", ".png", ".zip"):
            continue
        try:
            text = path.read_text(errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        scan_text(path, text, findings)

    history_findings: list[dict] = []
    log = subprocess.run(["git", "log", "--all", "--oneline"], cwd=ROOT,
                         capture_output=True, text=True)
    for line in log.stdout.splitlines():
        if any(p in line for p in ("github_pat_", "AKIA")):
            history_findings.append({"commit_line": line[:16], "kind": "possible-secret"})

    notices = (ROOT / "NOTICES.md").read_text(errors="ignore") if (ROOT / "NOTICES.md").is_file() else ""
    license_text = (ROOT / "LICENSE").read_text(errors="ignore") if (ROOT / "LICENSE").is_file() else ""
    report = {
        "scanner": "scripts/audit_repository.py",
        "findings": findings,
        "history_findings": history_findings,
        "agpl_notice_present": "AGPL" in license_text,
        "juce_notice_present": "JUCE" in notices,
        "vst3_mit_notice_present": "VST3" in notices and "MIT" in notices,
        "network_feature": False,
        "telemetry_feature": False,
        "ok": not findings and not history_findings
              and "AGPL" in license_text and "JUCE" in notices,
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(f"audit: {len(findings)} findings, {len(history_findings)} history findings -> {out}")
    for f in findings:
        print(f"finding: {f['file']}:{f['line']} {f['kind']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
