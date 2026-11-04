---
id: L-20261104T010000Z-spike-workload-exceeded-call-lifetime
title: Bound sample-loop spike workloads before launching them
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Medium
tags: [domain:audio, tech:python, phase:research, kind:environment]
recorded_by: planner
run: 20261103T230504Z-psychobilly-slap-bass
recorded_at: 2026-11-04T01:00:00Z
---
## Trigger
A deterministic Python sample-loop spike multiplies full extreme-control corners by sample rates, notes and durations, then exceeds the foreground tool-call lifetime without producing its output artifact.
## What went wrong
The initial R6 spike used all 256 eight-control corners at three rates and three notes, creating over one hundred million interpreted sample iterations; the call timed out and the process remained active.
## Correction
Stopped only the confirmed spike process and reduced the extreme matrix to a deterministic pairwise-plus-single-control set while retaining every control at both extremes and all required rates and notes.
## Prevention rule
Before launching an interpreted audio sample loop, compute total sample iterations and keep each foreground run within a measured small workload; use deterministic pairwise extreme cases and checkpoint independent stages rather than an exhaustive control-product run.
## Detection check
The spike prints its planned case/sample counts before synthesis and writes a complete parsing JSON output within the foreground call budget; no prior spike process remains active.
## Evidence
R6 `dsp_spike.py` initial run exceeded the call deadline on 2026-11-04 and produced no output; no implementation or test result was claimed.
