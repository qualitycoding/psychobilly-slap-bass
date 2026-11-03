# Research question tree

## Software engineering

- **Q-E01 — Framework:** Which exact JUCE 9.0.5 commit, licence, CMake minimum, module layout and Linux packages are required? Informs D-001/D-002, T-001–T-009, S-001.
- **Q-E02 — Plug-in contract:** Which processor, parameter, state, bus, MIDI, pitch-bend and editor interfaces satisfy a VST3 instrument without deprecated or guessed APIs? Informs D-010–D-019, T-040–T-059, S-005/S-006.
- **Q-E03 — Host validation:** Which stable `pluginval` release and verified CLI options validate VST3 on all three target runners? Informs D-020, T-050, S-007/S-008.
- **Q-E04 — Realtime safety:** How will allocation, locking, denormals, voice stealing, automation, re-prepare and state restoration be exercised under host-like stress? Informs D-021–D-024, T-051–T-058.
- **Q-E05 — CI:** Which versioned GitHub runner labels, action commits and dependency pins cover every intake platform without `-latest` or unverified flags? Informs D-025–D-028, T-060–T-064, S-008.
- **Q-E06 — Performance:** What workload and measured baseline produce a meaningful per-runner performance budget? Informs T-059 and the benchmark spike; no unmeasured number may become a gate.
- **Q-E07 — Security and malformed input:** What state/event validation, resource limits and dependency scans match the no-network threat model? Informs T-065–T-069.
- **Q-E08 — Offline renderer:** What event-file schema, seed semantics, metadata and output rules make demos deterministic and reproducible without normalising away gain defects? Informs D-030–D-033, T-070–T-075.

## Audio and acoustics

- **Q-A01 — Playing mechanics:** What distinguishes rockabilly/psychobilly slap double bass from ordinary pizzicato in excitation, fingerboard contact and rhythmic use? Informs D-040–D-043.
- **Q-A02 — String model:** Which real-time string formulation supports E1–G2 open strings, stopped notes, pluck position, damping and sympathetic coupling without unstable delay lengths? Informs D-044–D-047 and the architecture spike.
- **Q-A03 — Slap model:** Which combination of broadband contact, string/fingerboard impact and body excitation produces the audible slap without becoming a generic percussion layer? Informs D-048–D-050, T-080–T-089.
- **Q-A04 — Body model:** Which body/radiation approximation is computationally practical and capable of matching measured references? Informs D-051–D-053 and the architecture spike.
- **Q-A05 — Expressive mapping:** How should velocity and each user control affect the model across its full range while remaining monotonic, bounded and independent of note-specific tuning? Informs D-054–D-061 and mapping spikes.
- **Q-A06 — Output:** What gain staging prevents inter-voice clipping and non-finite output while preserving transient contrast? Informs D-062, T-090–T-094.

## Reference validation

- **Q-R01 — References:** Are there isolated slap-double-bass recordings with explicit CC0/CC-BY or equivalent redistribution rights, downloadable audio, attribution metadata and checksums? Informs D-070 and S-LISTEN.
- **Q-R02 — Reference segmentation:** How will notes and slap events be segmented, onset-checked and loudness-matched without analysing transitions or clipped material? Informs T-100–T-109.
- **Q-R03 — Quantitative gates:** Which onset, pitch, decay, spectral and slap-transient metrics are measurable on both reference and candidate, and what thresholds are supported by reference spread plus planning spikes? Informs T-110–T-119.
- **Q-R04 — Listening design:** Which 12 matched pairs, start-window cuts, seed rule, demos and weak-spot questions test realism rather than only steady state? Informs G-004 and S-LISTEN.
- **Q-R05 — Fallback:** If no suitable slap reference can be redistributed, what lawful comparison still provides useful evidence without pretending that an ordinary pizzicato reference validates slap realism? Informs D-071 and the gate definition.
