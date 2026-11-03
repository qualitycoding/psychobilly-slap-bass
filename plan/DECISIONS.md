# Decisions and decision rules

- **D-001 — Licensing:** license project source and combined binaries under AGPL-3.0-only, not the initially proposed GPL-3.0, because JUCE 9 offers AGPLv3 or a commercial licence. Verify the 9.0.5 licence text before freeze.
- **D-002 — Framework pin:** use JUCE 9.0.5 at `d60b7a78030661574a615b586d9325ba7a7fa7dd`, as requested if JUCE 9 exists.
- **D-003 — Mutation testing:** opt out for 0.1.0 because the suite combines realtime DSP, host validation and listening gates; a mature, low-cost mutation configuration has not been measured. Reconsider after the first implementation suite has a measured runtime.

## Execution forks

- If a dependency or host is unreachable, retry the same authenticated operation at most three times with bounded backoff; if still unreachable, record the exact evidence and use the pre-decided CI path or halt when no equivalent exists.
- If a check fails, do not weaken or skip it; correct the implementation or write `TEST_CHALLENGE.md` when the frozen check itself is invalid.
- For an unanticipated situation, choose the most reversible option that does not expand scope and log it in `DEVIATIONS.md`; halt for changes to frozen tests, security, data integrity, public interfaces or research integrity.
