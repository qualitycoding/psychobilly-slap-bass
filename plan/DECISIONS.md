
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

## D-041 — Schema 2 and MIDI articulation mapping

Renderer schema 1 remains valid with its original legacy behaviour. Schema 2 requires `articulation` on every `note_on`, with exactly `pluck`, `pop`, `slap` or `ghost`; `note_off` must not carry the field. Unknown articulations, schema 2 notes missing the field and schema 3 are rejected. On MIDI channel 1, latched keyswitches 24/25/26/27 select pluck/pop/slap/ghost respectively and do not sound notes. Keyswitches are outside the supported pitched-note range. The eight APVTS parameters are unchanged.

## D-042 — Research diagnostic contracts

T-016 extends the analyser with `onset_pitch_cents`, `pitch_glide_cents`, `pitch_glide_tau_s`, `pitch_glide_monotonic` and `static_partial_stretch_cents`, using known-answer dynamic-chirp and static-stretch signals. T-017 requires gesture direction, bounded collision count, finite output, muted ghost balance and measured same-string residual/continuity metadata. T-018 requires `pitch_bus` and `slap_bus` diagnostic components plus an output-model contract naming `compact_fitted`, `piezo`, `magnetic` and `microphone`, with no runtime FEM. These are measured adapter obligations, not permission to hardcode success.

## D-043 — Project-owned articulation reference route

`research/calibration/REFERENCE_PLAN.md` defines the lawful S-025 recording route and its blocking conditions. S-005 completion means the route, consent template and repository hygiene exist, not that audio has already been recorded. The sealed articulation bundle contains three pairs each for pluck, pop, slap and ghost, balanced to six reference-A and six reference-B pairs. Commercial artist audio and private consent forms remain outside Git and evidence.
