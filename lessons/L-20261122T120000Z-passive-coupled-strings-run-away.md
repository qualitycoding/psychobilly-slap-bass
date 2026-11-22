---
id: L-20261122T120000Z-passive-coupled-strings-run-away
title: Eight individually passive waveguide strings ran away to Infs through the sympathetic coupling
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Critical
tags: [tech:dsp, phase:implementation, kind:wrong-assumption]
recorded_by: implementer
run: impl-20261122T000000Z-psychobilly-slap-bass
recorded_at: 2026-11-22T12:00:00Z
---
## Trigger
Many high notes held ringing simultaneously on a shared 8-voice pool (pluginval's audio-processing sweep at 48-96 kHz; reproduced on x86 with a note/gesture/velocity sweep).
## What went wrong
Each string's loop gain was proven passive (< 1), which was assumed to make the voice bank stable. But the D-019 sympathetic coupling injects other voices' outputs into each delay line at full amplitude, so the correlated mode (all strings in phase) has closed-loop gain ~loopGain + k*(N-1) = 0.9997 + 0.105*7 ~ 1.73 per circulation. Clustered high notes (small nInt) grew exponentially to ±1e308 and emitted Infs. It surfaced only on the macOS pluginval run; Linux/Windows passed the same seeded sequence by luck of which random notes clustered.
## Correction
Bound the delay-line state to |x| <= 8 (kStringStateCeiling, D-045) — a finite string-excursion limit that only engages in runaway. Normal rendering stays ~1e0 internally; all 24 frozen tests and 11/11 freeze manifest pass unchanged. A standalone finiteness sweep (scripts/check_engine_finiteness.py) now runs in CI.
## Prevention rule
For any network of coupled feedback loops, audit the closed-loop gain of the WORST eigenmode, not per-loop gain. If the coupling matrix's max eigenvalue pushes any mode above unity, add a bounded-state (excursion limit) or reduce coupling gain; then prove finiteness with a hostile sweep (many voices, high pitch, long hold).
## Detection check
scripts/check_engine_finiteness.py exits 0 (no non-finite output samples across rates x block sizes x notes x gestures x velocities).
## Evidence
psychobilly-slap-bass D-045; pluginval run 45015418249 (macOS, 20/600 Infs); CI green at afa515e3.
