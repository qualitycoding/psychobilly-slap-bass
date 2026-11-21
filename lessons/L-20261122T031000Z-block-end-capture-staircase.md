---
id: L-20261122T031000Z-block-end-capture-staircase
title: Per-tick diagnostic captures written after each block created a staircase that let tests pass vacuously
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: High
tags: [tech:testing, phase:implementation, kind:false-positive]
recorded_by: implementer
run: impl-20261122T000000Z-psychobilly-slap-bass
recorded_at: 2026-11-22T03:10:00Z
---
## Trigger
An offline render captured per-tick bus values ("lastPitchedBus" style members) after filling each block, then stamped every sample of that block with the final value.
## What went wrong
All component buses appeared as per-block constants (contact/attack nearly zero everywhere). Gesture comparisons and contact-decay assertions passed vacuously on near-zero signals, and centroid measures on the contact bus were floating-point garbage - a false green on frozen gates.
## Correction
Capture the per-tick values into per-sample buffers inside the block fill loop and copy them out sample by sample; re-runs then exercised the buses genuinely and exposed real mapping defects.
## Prevention rule
Per-sample diagnostics must be recorded at the same temporal resolution they are consumed; review any "last value" capture used for measurement as a false-positive risk.
## Detection check
Assert per-sample variance inside every measurement window of a component capture; a component that is bit-identical across long runs of samples is a staircase, not a signal.
## Evidence
reviews/CODE_REVIEW.md in psychobilly-slap-bass (finding 1); fixes verified by T-013/T-017/T-018 green.
