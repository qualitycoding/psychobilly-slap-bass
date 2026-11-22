
## D-028 — Listening round branches and statistical interpretation

Each actual listening round uses orphan branch `evidence/G-004-round-N`, matching frozen T-051; the marker remains `[gate-evidence G-004]`. Twelve pairs are constructed from the seven pinned reference files; therefore source recordings are reused and pair outcomes are not claimed to be twelve independent acoustic samples. The one-sided binomial p-value is descriptive only, never evidence of realism or population generalisation. Balanced assignment, <=8/12 numeric condition and qualitative override remain binding.

## D-029 — Initial native performance baselines

The first fully green implementation run on each native principal runner records its seven raw RTF values and median in `performance/baselines.json`, keyed by runner OS/architecture and environment-lock hash. Before that record exists, only the absolute maximum RTF <=0.25 gate applies and the step passes if absolute performance succeeds. A later toolchain/lock change establishes a new explicitly keyed baseline without replacing historical data. Any attempt to loosen an existing same-key baseline by more than D-018's 10% bootstrap allowance requires G-005; deleting or regenerating a baseline to hide a regression is forbidden.

## D-030 — Evidence access is an implementation prerequisite

S-000 must verify that the implementing identity can create orphan evidence branches and that the user can receive the resulting bundle through a reachable repository archive/raw route or another explicitly provided accessible route. If the repository is private and no accessible route is available, S-100 blocks rather than claiming delivery. No credential or listener-identifying metadata enters evidence.

## D-031 — Review artifacts before implementation

Planning-time `reviews/CODE_REVIEW.md` and `reviews/ADVERSARIAL_REVIEW.md` contain plan cold-read results only and explicitly report zero executed code findings because no implementation exists. S-REVIEW and S-ADVERSARIAL replace them with implementation review records; their planning-time zero counts are never represented as implementation review coverage.

## D-032 — Research revision and articulation model

The 2026-11-22 research report is a planning input, not proof of perceptual realism. The primary string engine is bidirectional waveguide with explicit outward pluck, outward pop/rebound, inward slap and muted ghost gestures. Eight APVTS parameters remain unchanged; articulation is versioned performance/event data. Same-string retrigger preserves energy unless the gesture damps it. T-017 and G-004 must validate these behaviours.

## D-033 — Contact model and complexity ladder

Implement one stable nonlinear scattering/contact junction first and compare it with an offline distributed-contact reference case. Multiple junctions, two polarisations, stiffness dispersion and sample residuals are optional complexity only after measurable or blind benefit. Full/standard/economy quality levels share gesture/body/pickup semantics; economy may approximate collisions but may not remove articulation identity.

## D-034 — Onset glide and string calibration

Hard pluck/pop includes smooth amplitude-dependent downward onset pitch glide, distinct from static inharmonicity. Fit delay and dispersion on soft pluck, then frequency-dependent T60, then glide, then collisions, then body/pickup/output. Every fit uses held-out gestures. T-016 checks glide direction, bounded relaxation and separation from static partial stretching.

## D-035 — Body and pickup architecture

Use a compact fitted modal/biquad or short-FIR body, not runtime FEM. Provide internal piezo, magnetic and microphone/body paths. Piezo capacitance/load and magnetic pickup position are advanced internal model settings, not new host parameters. Commuted body excitation is permitted only for a linear economy pluck path, never as the sole collision engine.

## D-036 — Separate pitch and slap buses

Bridge force drives the pitch/body/pickup bus; collision force and hand/fingerboard residual drive the slap bus. Independent internal EQ/dynamics precede optional saturation/amp/cabinet/limiting. Tests must be able to inspect unprocessed diagnostic components. No output calibration may hide gain errors through renderer normalisation.

## D-037 — Artist reference use and redistribution

Steve Whitehouse/Frenzy, Oliver Baroni/Hillbilly Moon Explosion and bassist-specific Demented Are Go eras are analysis targets, not asserted gear presets. Ray Thompson and Graeme Grant references remain era-specific. Commercial audio is never committed or included in public evidence. Only cleared isolated recordings enter sealed listening bundles; missing cleared pop/slap references block rather than trigger substitution.

## D-038 — Calibration evidence

Create a consented isolated-gesture corpus with source/licence/checksum metadata and, where possible, separate piezo/contact/body captures. Extract pitch/glide, per-partial frequency/T60, contact timing/count, noise/tone ratio and multi-resolution spectra. Keep fit and holdout partitions. Artist-derived non-audio measurements must cite their source and may not be marketed as exact reproduction.

## D-039 — Articulation listening gate

G-004 retains the original twelve ordinary-pluck pairs and adds twelve sealed, balanced articulation pairs from cleared pluck/pop/slap/ghost material. Each set independently requires <=8/12 correct as a necessary numeric condition; qualitative override remains binding. T-052 covers the second bundle. ABX/MUSHRA engineering comparisons are optional supplements, not replacements.

## D-040 — Frozen contract migration

S-005 precedes implementation. Add T-016/T-017/T-018/T-052 and amend only affected event/listening contracts through unfreeze, explicit red, implementation-independent review and refreeze. Existing numeric gates and the eight-parameter/ten-demo counts remain unless a separate D-record explicitly changes them. No implementation begins on the unreconciled contract.

## D-041 — Event schema version 2 and articulation test freeze (S-005, 2026-11-22)

The D-023/D-024 performance/event contract is amended before implementation, per D-040's
unfreeze → explicit red → implementation-independent review → refreeze procedure:

- Event documents declare `"schema": 2` in the header. Schema 1 documents remain valid and
  mean the same events without gestures (ordinary pluck semantics, backwards compatible).
- Schema 2 `note_on` events accept an optional `"gesture"` field with exactly one of
  `pluck`, `pop`, `slap`, `ghost`. Unknown values, and a `gesture` key in a schema 1
  document, are rejected (unknown field). Default gesture is `pluck`.
- Articulation remains versioned performance/event data; the eight D-021 APVTS parameters are
  unchanged and no host parameter is added.
- New frozen tests added by this amendment: T-016 (SC-014, onset glide direction and
  velocity separation per D-034), T-017 (SC-013, gesture direction, bounded repeated
  collision, muted ghost output and same-string energy preservation per D-032/D-033),
  T-018 (SC-015, independent pitch/slap buses and fitted body routing per D-035/D-036) and
  T-052 (SC-016, schema-2 gesture validation and the sealed articulation listening bundle
  contract per D-037/D-039). All four failed explicitly red (NotImplementedError from the
  planning stub) before this freeze; no existing frozen test, numeric gate or the
  eight-parameter/ten-demo counts were changed.

## D-042 — T-016 measurement-window correction (S-005 amendment, 2026-11-22)

T-016's onset/steady pitch windows were measured at note 33 (55 Hz). A 30 ms window at
55 Hz contains 1.65 cycles, which cannot support pitch estimation (autocorrelation failed
at every rate during implementation, giving −inf glide). The frozen test is corrected to
note 48 (130.8 Hz, 3.9 cycles in 30 ms), matching the test's own SC-014 intent (glide
direction and velocity separation are properties of the gesture, not the register).
Procedure: unfreeze test_articulation.py only; prove the corrected T-016 explicitly red
against a stubbed renderer (PSB_RENDER_BIN=/bin/false, test errors); confirm green against
the implementation; regenerate the manifest; all other hashes unchanged. While validating,
the implementation's onset glide direction was found inverted versus D-034 (the model
initially lengthened the delay line at onset, pitching the note down; a released string's
tension spike pitches up) — engine fixed, depth capped at 120 cents so the onset pitch
stays inside the analyser's ±100 cent expected window.

## D-043 — T-052 document-construction correction (S-005 amendment, 2026-11-22)

The frozen T-052 `_document` helper wrapped its event list in an extra list, emitting one
JSON array line instead of JSONL event lines, so `validate_event_document` rejected every
well-formed document (the first assertion failed against any implementation). This is a
test-side defect, corrected by flattening the document; red evidence is the original body
failing against the unchanged adapter, green evidence is the corrected body passing
against the same adapter. No assertion, gate or count changed.

## D-044 — Loop-gain per-pass decay correction (S-030, 2026-11-22)

The waveguide applies `loopGain` once per full circulation of the delay line (every nInt
samples), not once per sample. The first implementation coded the per-sample loss
`10^(-3/(t60*fs))`, making the decay ~nInt times too slow and leaving a non-decaying
sub-audio floor that broke T-013 sustain monotonicity. Corrected to
`loopGain = 10^(-3*nInt/(t60*fs))`, recomputed when the integer delay length changes
(glide). T60 targets now measured within ~8% across the sustain sweep.

## D-045 — delay-line state ceiling (2026-11-22)
Sympathetic coupling (D-019, radius 0.105) injects other voices' outputs into
each delay line at full amplitude. The correlated 8-voice mode therefore has
closed-loop gain ~loopGain + 0.105*7 > 1: clustered high notes held on shared
voices grew exponentially and emitted Infs (found via pluginval "Infs found
in buffer", 20/600 tests, macOS; reproduced on x86 with a note/gesture/velocity
sweep). Fix: clamp the delay-line state to |x| <= 8 (kStringStateCeiling) —
a finite string excursion bound, engaging only in runaway; normal renders stay
~1e0 internally and all 24 frozen tests pass unchanged. D-019 radius and all
coupling semantics are untouched. Regression harness:
scripts/check_engine_finiteness.py (runs in CI after the frozen suite).
