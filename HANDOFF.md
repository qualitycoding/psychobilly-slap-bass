# Implementer handoff

This generation branch contains a frozen plan, not an implemented instrument. Execute only on a new `impl-<run_id>` branch. Planning spikes and stubs are evidence/contracts, not production DSP.

## Mandatory protocol rules

The following rules are reproduced verbatim from `qualitycoding/skills/protocols/planning-protocol.md` v3.11:

- **Rule 9 — Integrity `[All]`:** “No step may fabricate, cherry-pick without disclosure, or manually alter data, test results, benchmarks, or figures.”
- **Rule 10 — Human Gates `[All]`:** “At a gate, the implementer halts, writes `GATE-<id>.md` summarizing the evidence, and waits for human sign-off.”
- **Rule 14 — Honest Verification & Gating `[All]`:** “A check that cannot fail is not a check.” Its binding controls include: “No swallowed failures”, “Artifact post-conditions”, “Budgets gate”, “Baselines bootstrap”, “Per-environment targets”, and “Substitutions are deviations.” Read the complete rule in the governing protocol before execution.

Also controlling:

> **STOP INSTRUCTION:** this planning run stops after its plan is pushed. The implementing run must not deploy, release, deposit, publish, or submit anything except the explicitly authorised source/evidence pushes. Public binaries require G-002.

## Reading order

1. `plan/PROFILE.md`, `plan/ASSUMPTIONS.md`, `plan/DECISIONS.md`.
2. `plan/TRACEABILITY.md`, `plan/ENVIRONMENT.md`, `plan/GATES.md`.
3. `stubs/psb_contract.py` and every `tests/test_*.py` plus `tests/_support.py`.
4. `research/claims.json`, `research/SOURCES.md`, R6 spike records and `premortem/`.
5. `plan/PLAN.md` in step order.

D-001–D-027 are binding. D-070/D-071 are the reference/listening records. If identifiers appear non-sequential, do not renumber them.

## Frozen-test procedure

Before implementation:

```sh
sha256sum -c tests/FROZEN_MANIFEST.sha256
python3 research/spikes/freeze/red_verify.py
```

The red verifier must report explicit planning-stub exceptions only. After implementation:

```sh
sha256sum -c tests/FROZEN_MANIFEST.sha256
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

On Windows run `python scripts/verify_freeze.py` instead of `sha256sum`. Never modify a file beginning `# FROZEN — DO NOT MODIFY` to make implementation pass. A genuinely missing requirement follows this sequence: record a D-amendment; unfreeze only affected tests; add the test; prove explicit red against stubs; restore the freeze; regenerate every manifest hash; rerun cold-read and affected pre-mortem review.

## Execution and deviations

- S-000 is first; S-RETRO and S-KNOW are last. Append one `EXECUTION_LOG.md` row per attempt.
- A failed prerequisite writes `BLOCKED.md` and halts delivery. Never improvise around missing access or an unverified dependency.
- Record every version, mirror, timeout, package, config or workflow substitution in `DEVIATIONS.md`, with evidence and a lesson where it corrects a mistake.
- All numeric gates read measured output. Adapters may not return hardcoded success. No renderer normalisation is permitted.
- Do not claim perceptual realism from DSP metrics. G-004 is mandatory and limited to three disclosed rounds.
- CI artifacts and source pushes are authorised implementation activities; public binary release is not.

## Delivery boundaries

The deliverable is a VST3 source project, headless renderer, tests, native CI artifacts and listening evidence. No standalone app, AU, AAX, sample player, account, telemetry, network feature or retained user data. The host owns state; the audio thread performs no allocation, locking, file or network operation. Preserve all licence notices.
