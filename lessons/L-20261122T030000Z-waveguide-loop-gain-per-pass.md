---
id: L-20261122T030000Z-waveguide-loop-gain-per-pass
title: Waveguide loop gain was coded per-sample but consumed per-pass, making decay ~nInt times too slow
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: High
tags: [tech:dsp, phase:implementation, kind:correctness]
recorded_by: implementer
run: impl-20261122T000000Z-psychobilly-slap-bass
recorded_at: 2026-11-22T03:00:00Z
---
## Trigger
A bidirectional waveguide string's damping gain was derived from the desired T60 as a per-sample loss and stored once.
## What went wrong
The delay line applies the gain once per full circulation (every nInt samples), so the string decayed ~nInt times too slowly and a non-decaying sub-audio floor (6-40 Hz) accumulated, breaking sustain monotonicity and whole-signal pitch measurements.
## Correction
`loopGain = 10^(-3*nInt/(t60*fs))`, recomputed lazily whenever the integer delay length changes (glide). Measured T60 then matched targets within ~8% across the sustain sweep.
## Prevention rule
When a loop gain feeds a delay-line circulation, write the decay target as loss-per-pass and divide by the pass length in samples before coding; state which temporal unit every gain consumes in a comment next to the constant.
## Detection check
Render a fixed note at the sustain extremes and fit the dB envelope between -5 dB and -45 dB; the fitted T60 must scale monotonically with the sustain control within a small tolerance.
## Evidence
D-044 in psychobilly-slap-bass plan/DECISIONS.md; frozen T-013 sweep values in EXECUTION_LOG.md.
