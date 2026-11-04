# R5 — Adversarial pass

Date: 2026-11-04. No separate agent or named model tier is exposed in this environment; the pass used the recorded tier substitution and an explicit attempt-to-falsify stance.

## Searches and challenges

- Searched JUCE 9.0.5 breaking changes and VST3 issue reports; inspected the pinned breaking-change document rather than relying on recall.
- Rechecked pluginval's latest-release API after finding a 2.0.0 development-branch changelist. The API still identifies v1.0.4 as latest stable, so C-006 stands; no unreleased development branch was substituted.
- Read pluginval issue #149, the exact fix diff, test-loop skip conditions and command-line exit handling.
- Inspected JUCE's licence and SPDX inventory, including the VST3 SDK package.
- Re-read the collision paper for stability qualifications. Its nonlinear junction avoids the earlier output discontinuity, but that does not prove stability of this project's future parameter mappings, feedback, voice lifecycle or floating-point implementation; R6 remains necessary.
- Re-read the listening protocol for seed disclosure and side bias. Balanced side assignment and evidence hygiene are fixed by D-015.

## Findings

1. **C-019:** JUCE 9.0.5 has explicit ValueTree/JSON/XML nesting and entity-expansion limits and documents macOS 12.0. The product still needs its own input byte cap and shallow schema because library parser limits do not validate product semantics. D-012.
2. **C-020:** the bundled VST3 SDK is identified as 3.8.0/MIT in JUCE's SPDX inventory. Third-party notices are mandatory package artifacts under D-013.
3. **C-021:** stable pluginval's known `PluginInfoTest` race has an exact maintainer fix. D-011 permits that commit only after a matching reproduced failure and retained evidence.
4. **C-022:** pluginval can legitimately skip tests by configuration. Exit zero without log/content assertions would be inadequate evidence; D-014 closes that false-success path.
5. No new evidence corroborates C-010. It remains non-load-bearing and cannot justify realism.
6. No listening evidence exists yet. Numerical or validator success cannot establish psychobilly slap character.

## Claim audit

C-001–C-009 and C-011–C-020/C-022 are `verified` where noted; C-007–C-009 and C-021 are `corroborated`. Every load-bearing claim meets the research bar. C-010 is non-load-bearing and `single-source`. R5 added load-bearing claims C-019–C-022, so saturation is not claimed before R6.

## R6 falsification targets

- The architecture may be unstable, excessively clicky, insensitive to controls, too costly, or unable to produce useful candidate/reference spread.
- Sympathetic coupling and voice stealing may create feedback, allocation or abrupt cuts.
- Analysis code may pass on trivial sine waves yet fail on second-harmonic-dominant bass tones.
- The local sandbox cannot establish Windows/macOS/GitHub-runner performance or host validation; those dimensions must be named CI checks rather than reported as locally green.

Round status: complete.
