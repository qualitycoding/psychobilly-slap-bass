---
id: K-20261122T130000Z-coupled-sympathetic-loop-gain
statement: "A bank of N passive coupled feedback loops is not passive as a system: if cross-coupling gain k is injected at full amplitude, the correlated mode has closed-loop gain ~g + k*(N-1), which exceeds 1 for modest k and runs away exponentially; stability must be analyzed per eigenmode of the coupling matrix, and a bounded state (excursion limit) guarantees finiteness."
status: current
supersedes: []
tags: [domain:audio, tech:dsp, subject:waveguide-strings, phase:implementation]
applies_to_version: "psychobilly-slap-bass 0.1.0"
source: {"url": "https://github.com/qualitycoding/psychobilly-slap-bass/blob/impl-20261122T000000Z/plan/DECISIONS.md", "doi": "", "title": "psychobilly-slap-bass D-045 delay-line state ceiling", "locator": "D-045", "accessed": "2026-11-22", "tier": 2}
confidence: verified
derived_from: [D-045]
discovered_by: implementer
run: impl-20261122T000000Z-psychobilly-slap-bass
recorded_at: 2026-11-22T13:00:00Z
---
Each loop of a coupled waveguide bank may be individually stable (loop gain
g < 1) while the bank is unstable. With N strings and cross-coupling radius k
injected at full amplitude into each delay line, the all-in-phase eigenmode of
the coupling matrix has eigenvalue k*(N-1), so the mode gain per circulation
is ~g + k*(N-1); for N = 8, k = 0.105, g = 0.9997 this is ~1.73 > 1 and the
state grows exponentially (reached ±1e308 and emitted Infs within seconds when
clustered high notes — small nInt — rang on a shared voice pool). Decay-rate
or per-loop checks cannot see this; the worst eigenmode of the coupling matrix
decides stability. Remedies: reduce k so g + k*(N-1) <= 1 (usually inaudibly
small k), or keep the coupling and bound the loop state — e.g. clamp the
delay-line write to an excursion ceiling (|x| <= 8 for signals of order 1),
which caps every derived signal and engages only during runaway. Prove
finiteness with a hostile sweep: many simultaneous voices, high pitch, long
hold, all sample rates and block sizes (psychobilly-slap-bass
scripts/check_engine_finiteness.py).
