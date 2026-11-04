# R6 — Empirical verification

Date: 2026-11-04.

## Falsified initial assumptions

- The exhaustive 256-corner interpreted spike exceeded the call lifetime. `L-20261104T010000Z-spike-workload-exceeded-call-lifetime` records the correction to 18 deterministic extreme configurations (all-zero, all-one, each single control high/low), retaining 162 rate/note/control cases.
- The first run failed: unconstrained pitch analysis produced octave errors on real references, slap-brightness measurement was non-monotonic, and extreme output reached 1.20208. No threshold from that run was accepted.
- Global corrections were then applied: note-conditioned matched-event pitch search (while retaining unconstrained known-answer tests), brightness filtering of both contact components, excitation/radiation filtering, and reduced fixed mix gain. The ordinary-pluck reference preset removes contact, attack and mechanical noise rather than pretending a pizzicato reference contains slap.
- The initial model was much brighter than the references. A global radiation-filter mechanism reduced the discrepancy; no per-note tuning or post-render normalisation was used.

## Verified outputs

- C-023: 54 architecture runs (six pitches, three dynamics, three rates) and 162 extreme runs are finite; extreme peaks are below full scale. Two final DSP runs produced identical SHA-256 `2386d34ff68f85fc21821d65e20822753b39a56e53dce52e0e1b91008d9de211`.
- C-024: all known-answer tests pass. Matched reference/candidate pitch spread supports the 21-cent regression limit in D-017.
- C-025: all eight controls strictly increase their designated measurement at `0, 0.25, 0.5, 0.75, 1` with fixed excitation seed.
- C-026: 256 lifecycle events remain within eight slots; steals and retriggers both occur. Coupling spectral radius is 0.105.
- C-027: the measured ordinary-pluck spectral comparison limit is 1.433155096971784 log2. Decay mismatch is 2.983474685004709 log2 and remains diagnostic, not a realism pass.
- C-028: native eight-voice 96 kHz/64-sample workload, seven five-second repeats, maximum RTF 0.021304663 and finite output. D-018 sets a conservative 0.25 per-runner ceiling and 10% baseline allowance; no Windows/macOS/CI performance is claimed locally.

## Research closure

R6 added C-023–C-028 and verified them in the same round. All load-bearing claims are `verified` or `corroborated`; C-010 remains non-load-bearing. There are no unresolved contradictions. The six-round maximum is reached, so research closes without claiming a seventh saturation round. Numerical results do not establish psychobilly realism or listening approval.

Round status: complete. Next: interface-first specification and frozen red tests.
