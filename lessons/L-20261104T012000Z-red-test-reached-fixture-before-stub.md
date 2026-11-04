---
id: L-20261104T012000Z-red-test-reached-fixture-before-stub
title: Red tests must reach the stub before external fixtures
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Low
tags: [tech:python, phase:freeze, kind:testing]
recorded_by: planner
run: 20261103T230504Z-psychobilly-slap-bass
recorded_at: 2026-11-04T01:20:00Z
---
## Trigger
A frozen test reads external reference WAVs before its first adapter call during red verification.
## What went wrong
T-014 failed with `FileNotFoundError` instead of the intended `NotImplementedError`, so the red run did not prove the test itself was fixture-complete.
## Correction
Moved candidate rendering/analysis ahead of reference-file access and tightened the red verifier to compare unittest error count with stub-error count and reject unexpected exception types or passing tests.
## Prevention rule
During red verification, invoke the stub before any optional downloaded fixture access, and require every reported error to be the explicit planning-stub exception.
## Detection check
`research/spikes/freeze/red-output.json` has `clean_red:true`, nonzero test/error counts, equal error and stub-exception counts, and no unexpected errors.
## Evidence
Initial R6 red run had 20 tests but one fixture-access error; corrected before freeze.
