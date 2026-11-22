---
id: L-20261122T126000Z-backslash-paths-break-startswith-exclusions
title: Path exclusions in a portable scanner silently failed on Windows because str(Path) uses backslashes
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Medium
tags: [tech:python, tech:github-actions, phase:verification, kind:tooling]
recorded_by: implementer
run: impl-20261122T000000Z-psychobilly-slap-bass
recorded_at: 2026-11-22T12:55:00Z
---
## Trigger
A repository scanner excluding its own source and known-sanctioned paths with `rel.startswith(("scripts/audit", "stubs/psb_contract", ".github/workflows/"))`, clean on Linux and macOS.
## What went wrong
On Windows, `str(Path(...).relative_to(root))` produces backslash separators (`scripts\audit_repository.py`), so every forward-slash `startswith` exclusion failed and the scan reported 7 self-findings that could not reproduce on Linux — including the scanner's own pattern definitions and CI heredoc downloads.
## Correction
Normalize before matching: `rel = path.relative_to(ROOT).as_posix()`.
## Prevention rule
In any script that matches relative paths against literal prefixes/suffixes (exclusions, allowlists, manifest filters), normalize with `.as_posix()` (or match on `path.parts`). A check that passes on Linux and fails only on Windows is a portability bug in the check, not a Windows problem.
## Detection check
The audit reports 0 findings on every OS, and a deliberate probe file is found on every OS.
## Evidence
psychobilly-slap-bass CI run 45014538907 (7 findings, Windows-only); fixed by 906312b.
