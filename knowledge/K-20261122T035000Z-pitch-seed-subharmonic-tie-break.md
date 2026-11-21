---
id: K-20261122T035000Z-pitch-seed-subharmonic-tie-break
title: Harmonic-sum pitch seed needs a highest-frequency tie-break, not amplitude weighting
recorded_at: 2026-11-22T03:50:00Z
source: psychobilly-slap-bass T-012 known-answer debugging
---
Spectral pitch seeding by summing harmonic amplitudes `sum(|X(k*f)|)` is robust
against a dominant second harmonic, but two failure modes need explicit rules:

1. Amplitude weighting (`/h`) re-introduces octave errors: with components
   0.22 at f, 1.0 at 2f, 0.35 at 3f, `/h` weighting scores 2f above f. Use an
   unweighted sum.
2. With a missing fundamental (components only at 2f, 3f, 4f), f and f/2 tie
   exactly. Break ties toward the HIGHEST-frequency near-maximal candidate
   (within ~10% of the best score), which selects f, while ordinary spectra
   still select their true fundamental because the fundamental's score is
   strictly maximal.

On burst-dominated short windows (<= 4 cycles) autocorrelation can be negative
at every in-window lag; fall back to the parabolically interpolated spectral
peak inside the conditioned expected window rather than returning silence.
