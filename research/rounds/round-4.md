# R4 — Depth verification

Date: 2026-11-04.

## Outcomes

- C-010 is narrowed to a single-source practitioner observation and marked non-load-bearing. D-004's separate contact/body paths remain an architecture hypothesis to be falsified or retained through R6 and human listening, not an asserted acoustic fact.
- C-014 verifies the five selected GitHub Action tags against full commit SHAs in `research/spikes/toolchain/action-pins.json`.
- C-015 verifies successful downloads, byte counts and SHA-256 hashes for the Linux, Windows and macOS pluginval v1.0.4 archives.
- C-016 verifies the public-PyPI fallback, CMake 3.31.6 and 3.22.4 execution, NumPy/SciPy/SoundFile pins and pluginval CLI startup.
- C-017/C-018 verify the pinned JUCE processor, bus, editor, XML state and APVTS realtime-boundary APIs from source.
- D-007 fixes a host-parameter-only interface with no bespoke editor. D-008 keeps locking state operations out of audio processing. D-009 records the Linux ARM64/libc waivers without weakening any declared platform. D-010 fixes the package-index fallback. D-011 pre-decides an exact pluginval race fallback without permitting a moving branch or suppressed test.

## Corrections and lessons

- `L-20261104T004000Z-configured-package-index-unreachable` records the failed configured mirror and successful identical-pin public-PyPI retry.
- `L-20261104T004100Z-cmake-package-needs-data-and-exec-bits` records the no-exec mount and incomplete CMake staging failures and the verified complete-data-tree correction.

## Claim status

All load-bearing registered claims are now `verified` or `corroborated`. C-010 remains `single-source` but is non-load-bearing and cannot justify a design or test by itself. No realism or listening claim has been made.

## Remaining adversarial questions

R5 must challenge pluginval false-success/false-failure modes, the stable-validator race, JUCE licence and API assumptions, runner/architecture drift, nonlinear collision stability, sympathetic/voice lifecycle runaway, listening side bias and evidence-branch disclosure. The exact issue #149 fix commit is recorded, but its fallback conditions still require adversarial review.

## Remaining empirical questions

R6 must exercise the proposed string/contact/body architecture across at least three notes and three dynamics; sample rates 44.1–96 kHz and extreme controls; bounded eight-voice lifecycle and sympathetic coupling; known-answer analysis; reference/candidate metric spread; and realistic per-runner performance. Numeric realism and performance thresholds remain unfrozen until those outputs exist.

Round status: complete.
