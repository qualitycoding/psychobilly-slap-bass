#!/usr/bin/env python3
"""Artifact verification (S-070/S-090): fails for missing, empty or
schema-invalid logs, WAVs, JSON or provenance records under a directory."""
from __future__ import annotations

import json
import sys
import wave
from pathlib import Path


def check_wav(path: Path) -> list[str]:
    problems = []
    try:
        with wave.open(str(path), "rb") as w:
            if w.getnframes() <= 0 or w.getframerate() <= 0:
                problems.append(f"{path.name}: empty wav")
            if w.getsampwidth() != 3:
                problems.append(f"{path.name}: not 24-bit")
    except (wave.Error, OSError) as exc:
        problems.append(f"{path.name}: unreadable wav: {exc}")
    return problems


def _strip_trailing_commas(text: str) -> str:
    # JUCE's VST3 moduleinfo.json is emitted with trailing commas (valid for
    # the JUCE parser, strict-invalid JSON). Tolerate it here.
    out, i, in_str, esc = [], 0, False, False
    while i < len(text):
        ch = text[i]
        if in_str:
            out.append(ch)
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            i += 1
            continue
        if ch == '"':
            in_str = True
            out.append(ch)
            i += 1
            continue
        if ch == ",":
            j = i + 1
            while j < len(text) and text[j] in " \t\r\n":
                j += 1
            if j < len(text) and text[j] in "}]":
                i += 1  # drop the comma
                continue
        out.append(ch)
        i += 1
    return "".join(out)


def check_json(path: Path, required: set[str] | None = None) -> list[str]:
    problems = []
    try:
        text = path.read_text()
        if path.name == "moduleinfo.json":
            text = _strip_trailing_commas(text)
        data = json.loads(text)
    except (json.JSONDecodeError, OSError) as exc:
        return [f"{path.name}: invalid json: {exc}"]
    if required is not None and not required.issubset(set(data)):
        problems.append(f"{path.name}: missing provenance keys {sorted(required - set(data))}")
    return problems


PROVENANCE_KEYS = {"git_commit", "environment_lock_sha256", "seed", "controls",
                   "input_sha256", "event_sha256", "wav_sha256", "sample_rate",
                   "frames", "peak", "rms", "utc_timestamp", "hardware",
                   "thread_count", "normalisation_applied"}


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: verify_artifacts.py <directory>")
        return 2
    root = Path(sys.argv[1])
    if not root.is_dir():
        print(f"not a directory: {root}")
        return 1
    problems: list[str] = []
    files = [p for p in sorted(root.rglob("*")) if p.is_file()]
    if not files:
        print(f"no artifacts under {root}")
        return 1
    for path in files:
        if path.stat().st_size == 0:
            problems.append(f"{path.relative_to(root)}: empty file")
            continue
        suffix = path.suffix.lower()
        if suffix == ".wav":
            problems += check_wav(path)
        elif suffix == ".json":
            problems += check_json(path)
        elif suffix == ".jsonl":
            lines = [ln for ln in path.read_text(errors="ignore").splitlines() if ln.strip()]
            if not lines:
                problems.append(f"{path.relative_to(root)}: empty jsonl")
            else:
                for ln in lines:
                    try:
                        json.loads(ln)
                    except json.JSONDecodeError:
                        problems.append(f"{path.relative_to(root)}: bad jsonl line")
                        break
    # Render-provenance records must be complete when present.
    for path in files:
        if path.suffix == ".json" and "metadata" in path.name or path.name.startswith("demo-"):
            if path.suffix == ".json":
                problems += [f"{path.relative_to(root)}: {p}" for p in check_json(path, PROVENANCE_KEYS)]
    if problems:
        print("\n".join(problems))
        return 1
    print(f"artifacts OK ({len(files)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
