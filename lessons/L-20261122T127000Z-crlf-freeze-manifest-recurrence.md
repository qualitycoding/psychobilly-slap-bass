---
id: L-20261122T127000Z-crlf-freeze-manifest-recurrence
title: Recurrence of the CRLF manifest lesson — a Python sha256 freeze verifier failed 11/11 on Windows
status: active
supersedes: []
recurrence_of: L-20261028T210000Z-crlf-breaks-hash-manifests-on-windows
occurrences: 2
severity: Medium
tags: [tech:git, tech:github-actions, tech:python, phase:verification, kind:environment]
recorded_by: implementer
run: impl-20261122T000000Z-psychobilly-slap-bass
recorded_at: 2026-11-22T12:57:00Z
---
## Trigger
A frozen-test manifest (`tests/FROZEN_MANIFEST.sha256`) verified by a Python script over working-tree bytes; the repo had no `.gitattributes`, and the previous fix (from the recurrence target) lived in a different repository.
## What went wrong
`actions/checkout` on Windows applied CRLF conversion, so all 11 hashed files differed byte-wise from their Linux-generated digests ("0/11 frozen files verified"). The earlier lesson fixed this with path-scoped `text eol=lf`; this repo repeated the mistake with a different verifier, so the failure mode had to be rediscovered from scratch.
## Correction
Ship a root `.gitattributes` with `* -text` (never convert any path), which is stronger than pinning hashed paths to LF: it protects every byte-sensitive check, present and future. Run the freeze verification on Windows in CI.
## Prevention rule
Byte-hash verification and line-ending conversion are incompatible repository-wide. The rule from the recurrence target generalizes: whenever ANY verifier hashes working-tree bytes, the repo root gets an attributes file, and the verifier runs on Windows. Treat `.gitattributes` as required scaffolding for any repo with a hash manifest — check for it at intake.
## Detection check
`python scripts/verify_freeze.py` reports 11/11 on the Windows job.
## Evidence
psychobilly-slap-bass CI run 44949930585 job 136985400381 (0/11); fixed by fc44e46.
