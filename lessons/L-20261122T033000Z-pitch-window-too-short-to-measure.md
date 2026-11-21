---
id: L-20261122T033000Z-pitch-window-too-short-to-measure
title: A 30 ms pitch window at 55 Hz held 1.65 cycles and made a frozen glide test unmeasurable at any implementation
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Medium
tags: [tech:testing, phase:implementation, kind:test-defect]
recorded_by: implementer
run: impl-20261122T000000Z-psychobilly-slap-bass
recorded_at: 2026-11-22T03:30:00Z
---
## Trigger
A frozen articulation test measured onset pitch in the first 30 ms of a 55 Hz note (1.65 cycles) and compared it with a steady window.
## What went wrong
No implementation can support pitch estimation on 1.65 cycles: autocorrelation was negative at every lag inside the expected window and every engine variant failed identically (-inf glide). Separately, the engine's onset glide (initially up to +280 cents) fell outside the analyser's +/-100 cent expected window, which was indistinguishable from the window flaw until the note moved up.
## Correction
Amended the frozen test to note 48 (3.9 cycles in 30 ms) under the unfreeze -> explicit red -> refreeze procedure (D-042), and capped the engine glide depth at 120 cents so the onset pitch stays inside the conditioned window.
## Prevention rule
Pitch-estimation windows must contain at least ~4 cycles of the lowest tested frequency before a measurement is called decidable; when a test cannot fail against any implementation, fix the test, not the analyser.
## Detection check
Re-run the measurement against synthetic pure tones at the windowed note/frequency: if pitch estimation fails on a pure tone, the window is unmeasurable.
## Evidence
D-042 in psychobilly-slap-bass plan/DECISIONS.md; explicit red recorded via a stubbed renderer.
