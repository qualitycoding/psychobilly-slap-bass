# Decisions and decision rules

- **D-001 — Licensing:** license project source and combined binaries under AGPL-3.0-only, not the initially proposed GPL-3.0, because JUCE 9 offers AGPLv3 or a commercial licence. Verify the 9.0.5 licence text before freeze.
- **D-002 — Framework pin:** use JUCE 9.0.5 at `d60b7a78030661574a615b586d9325ba7a7fa7dd`, as requested if JUCE 9 exists.
- **D-003 — Mutation testing:** opt out for 0.1.0 because the suite combines realtime DSP, host validation and listening gates; a mature, low-cost mutation configuration has not been measured. Reconsider after the first implementation suite has a measured runtime.
- **D-004 — DSP architecture candidate:** evaluate an extended digital-waveguide string with fractional delay and frequency-dependent damping, a nonlinear string–fingerboard collision/contact path, and a separate body/radiation path. The pitched/body and contact components must remain separately controllable through the shipped mix. This is a candidate pending R6 stability, control and performance spikes, not a realism claim.
- **D-005 — Host validator:** pin pluginval v1.0.4 at `ed19c2c16b57a6d94db391bea3ef4a80b769d5bf`; run strictness 7, a fixed random seed, explicit sample rates and block sizes, and an additional repeated/randomised stress invocation from the first binary-producing step. Any disabled test requires a recorded waiver and cannot be used to conceal a failure.
- **D-006 — CI runner labels:** use `windows-2025` for Windows x64, `macos-15` for Apple Silicon and `ubuntu-24.04` for Linux x64. Do not use moving `-latest` labels.
- **D-070 — Pluck/body reference set:** use the seven pinned CC0 VSCO 2 CE pizzicato candidates recorded in `research/reference-candidates/manifest.json` for ordinary pluck/body blind comparisons and reference-spread analysis. Re-fetch by pinned URL and require the recorded SHA-256 before use.
- **D-071 — Slap validation fallback:** because no redistributable slap-specific reference has been verified, assess slap character through reproducible event-file demos and the fixed human listening questions, with no A/B-against-slap-reference claim. Ordinary pluck/body A/B coverage remains separate and cannot substitute for slap approval.

## Execution forks

- If a dependency or host is unreachable, retry the same authenticated operation at most three times with bounded backoff; if still unreachable, record the exact evidence and use the pre-decided CI path or halt when no equivalent exists.
- If a check fails, do not weaken or skip it; correct the implementation or write `TEST_CHALLENGE.md` when the frozen check itself is invalid.
- For an unanticipated situation, choose the most reversible option that does not expand scope and log it in `DEVIATIONS.md`; halt for changes to frozen tests, security, data integrity, public interfaces or research integrity.
