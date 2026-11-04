---
id: L-20261104T013500Z-plan-evidence-branch-contract-mismatch
title: Listening plan branch pattern must match the frozen adapter contract
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: High
tags: [domain:audio, phase:verification, kind:process]
recorded_by: planner
run: 20261103T230504Z-psychobilly-slap-bass
recorded_at: 2026-11-04T01:35:00Z
---
## Trigger
A plan names generated evidence paths while a frozen adapter test asserts a path pattern.
## What went wrong
S-100 initially named `evidence/G-004`, but T-051 requires `evidence/G-004-round-` plus the round number.
## Correction
D-028 and S-100 now use `evidence/G-004-round-N`; the gate marker remains unchanged.
## Prevention rule
Cross-check every generated path and identifier against the frozen adapter assertions before declaring the plan internally consistent.
## Detection check
`grep` the plan for `evidence/G-004` and confirm each actual branch pattern includes `round-N` as required by T-051.
## Evidence
`tests/test_listening.py` T-051 and `plan/DECISIONS.md` D-028. No secrets.
