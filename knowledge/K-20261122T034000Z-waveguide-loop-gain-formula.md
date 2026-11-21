---
id: K-20261122T034000Z-waveguide-loop-gain-formula
title: Waveguide per-pass loop gain for a target T60
recorded_at: 2026-11-22T03:40:00Z
source: psychobilly-slap-bass S-030 implementation and measurement
---
For a delay line of integer length `nInt` samples at rate `fs`, a gain `g` applied
once per circulation multiplies the signal every `nInt` samples. A target T60
(60 dB decay time) therefore requires

    g = 10^(-3 * nInt / (t60 * fs))

because one pass must contribute the whole `-60 dB * nInt / (t60*fs)` fraction
of the total decay. Coding `10^(-3/(t60*fs))` instead makes decay ~nInt times
too slow (e.g. ~870x at 55 Hz / 48 kHz) and leaves a non-decaying sub-audio
floor. Recompute `g` lazily whenever `nInt` changes (pitch glide moves the
integer length), and keep the gain strictly passive (`g <= 1`) so the loop
cannot self-oscillate; fold frequency-dependent damping into the loop filter
rather than into `g`.
