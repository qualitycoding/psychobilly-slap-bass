# R3 — Synthesis and gap analysis

Date: 2026-11-04.

## Claim audit

- C-001–C-006 and C-011–C-013 are `verified` by pinned source, release metadata or local empirical inspection.
- C-007–C-009 are `corroborated` with at least one Tier-1 source.
- **C-010 remains `single-source` and load-bearing.** The two-output-source description comes from a practitioner article. R4 must find independent support or reduce the design premise to an architecture hypothesis tested by listening rather than an asserted acoustic fact.
- No claim was downgraded in R3. The earlier GPL premise was already falsified and corrected by C-002/D-001; it is not silently retained.

## Contradictions and version risks

1. pluginval v1.0.4 is built with JUCE 8.0.3 according to its release notes, while the product uses JUCE 9.0.5. This is not itself incompatibility: pluginval hosts a VST3 through its format interface. It is a test-environment version difference to exercise empirically on each OS, not a reason to substitute an unpinned development build.
2. JUCE 9's headless module split invalidates include paths remembered from earlier versions. All implementation includes and target linkage must be compiled in the first binary step; no uncompiled JUCE glue is acceptable.
3. VSCO's pizzicato licence and audio quality do not solve slap-reference coverage. Treating those files as slap evidence would contradict D-071 and the listening protocol.
4. The references' strongest low-band FFT bin is the second harmonic. Any pitch gate based on the largest spectral peak would be invalid; known-answer analyser tests must precede metric thresholds.

## New questions

Added Q-E09–Q-E11, Q-A07–Q-A09 and Q-R06–Q-R07 to `research/QUESTIONS.md`. They cover immutable CI dependencies, editor/headless behaviour, public contracts, collision stability, voice lifecycle, analyser correctness, attainable thresholds and partial-coverage listening scoring.

## R4 depth targets

- Corroborate or qualify C-010.
- Pin action commits and downloadable tool archives; verify exact setup/invocation documentation at those pins.
- Inspect the pinned JUCE processor, parameter, state, MIDI and bus APIs needed for literal interface declarations.
- Resolve editor/headless CI behaviour and event/state validation constraints.

## R5 adversarial targets

Search for JUCE 9.0.5 breaking changes and licence restrictions, pluginval limitations/false-success modes, GitHub runner architecture mismatch, collision instability, blind-test side bias and evidence-branch secret/publication risks.

## R6 empirical targets

Run architecture/contact/control/analyser/performance/reference-spread spikes. No perceptual or performance threshold may be frozen before its supporting spike output exists.

Round status: complete. The load-bearing claim set still has one below-bar item (C-010) and several empirically testable premises, so research continues.
