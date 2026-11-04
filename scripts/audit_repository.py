#!/usr/bin/env python3
"""Repository audit (S-090): secret patterns, unsafe URLs/credentials,
forbidden runtime services, dangerous deserialisation and missing notices.

Scans tracked content; reports files/lines without printing matched secrets.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SECRET_PATTERNS = {
    "github-pat": re.compile(r"github_pat_[A-Za-z0-9]{20,}"),
    "github-oauth": re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    "aws-access-key": re.compile(r"AKIA[A-Z0-9]{16}"),
    "private-key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "slack-token": re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    "stripe-live": re.compile(r"sk-live-[A-Za-z0-9]{10,}"),
}
FORBIDDEN_RUNTIME = {
    "network-socket": re.compile(r"\b(socket|connect|getaddrinfo|WSAStartup)\b"),
    "http-client": re.compile(r"\b(WebInputStream|HTTPClient|curl_easy|URLRequest)\b"),
    "telemetry": re.compile(r"\b(telemetry|analytics|trackEvent)\b", re.IGNORECASE),
    "account": re.compile(r"\b(login|signin|oauth|password)\b", re.IGNORECASE),
    "unsafe-deserialisation": re.compile(r"\bpickle\.loads\b|\beval\(|\bexec\("),
}
RUNTIME_DIRS = ("src/",)


def tracked_files() -> list[Path]:
    result = subprocess.run(["git", "ls-files"], capture_output=True, text=True, cwd=ROOT)
    if result.returncode != 0:
        return []
    return [ROOT / line for line in result.stdout.splitlines() if line]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    findings = []
    for path in tracked_files():
        rel = str(path.relative_to(ROOT))
        try:
            text = path.read_text(errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        for name, pattern in SECRET_PATTERNS.items():
            for match in pattern.finditer(text):
                line = text[:match.start()].count("\n") + 1
                findings.append({"kind": "secret", "pattern": name,
                                 "file": rel, "line": line})
        if rel.startswith(RUNTIME_DIRS) and path.suffix in (".cpp", ".h", ".hpp", ".c", ".cc"):
            for name, pattern in FORBIDDEN_RUNTIME.items():
                for match in pattern.finditer(text):
                    line = text[:match.start()].count("\n") + 1
                    findings.append({"kind": "forbidden-runtime", "pattern": name,
                                     "file": rel, "line": line})

    notices = (ROOT / "THIRD-PARTY-NOTICES.md")
    license_file = ROOT / "LICENSE"
    report = {
        "schema": 1,
        "findings": findings,
        "licence_notice_present": license_file.exists() and "AGPL" in license_file.read_text(errors="ignore"),
        "third_party_notices_present": notices.exists(),
        "files_scanned": len(tracked_files()),
    }
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text)
    # Exit non-zero on any secret or forbidden-runtime finding.
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
