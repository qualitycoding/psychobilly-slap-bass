# S-005 research contract reconciliation report

Result: **pass; refrozen explicit-red contract ready for S-010, but S-010 was not started**.

## Changes

D-032–D-043 now specify explicit pluck/pop/slap/ghost gestures, schema 2 articulation events, MIDI channel-1 keyswitches 24/25/26/27, dynamic onset glide, bounded contact/retrigger diagnostics, compact fitted output models, independent pitch/slap buses and an independent articulation listening bundle. The eight APVTS parameters and ten-demo count remain unchanged. Schema 1 remains valid; schema 3 and malformed articulation events are rejected.

New tests: T-016 (known-answer and rendered glide versus static inharmonicity), T-017 (gesture direction/collision/ghost/retrigger), T-018 (output models and independent buses), T-052 (twelve sealed articulation pairs, three per gesture). T-020/T-021 cover both event schemas and rejection boundaries. New adapter stub entry points are `make_articulation_blind_pairs` and `output_model_contract`.

## Explicit-red history

1. Attempt 1 produced an articulation-fixture assertion before reaching the stub. The fixture was corrected to construct invalid schema-2 text without asking the valid-event helper to accept an unknown gesture.
2. Attempt 2 reached stubs but then evaluated absent subtest results, producing a `KeyError`. T-017 was restructured so every postcondition runs inside its own stub-reaching subtest.
3. Attempt 3 passed clean-red: **24 tests / 267 errors / 267 expected stub failures / zero unexpected errors**.
4. Freeze markers were restored on exactly `tests/_support.py`, `test_dsp.py`, `test_events.py` and `test_listening.py`; all ten manifest entries were regenerated. The manifest passed and the final verifier again reported 24/267/267 with no unexpected errors.

Attempts 1 and 2 logs are retained alongside the final evidence. No red result was converted into implementation success.

## Reviews and reference route

`reviews/S005_CONTRACT_REVIEW.md` records eight findings and resolutions. `premortem/S005_ADDENDUM.md` supplements the risk review; `ASSUMPTION_AUDIT.md` now explicitly rejects the premise that articulation audio already exists. Traceability and planning counts are updated.

`research/calibration/REFERENCE_PLAN.md` and its consent template define a lawful project-owned recording route. **No articulation reference audio has been obtained.** S-025 must produce cleared pluck/pop/slap/ghost recordings or block S-100/G-004. Commercial artist audio remains excluded from Git and evidence.

## Stop condition

The frozen manifest and final clean-red checks pass. No production C++, CMake project, VST3, compiled adapter, renderer, demo or listening evidence was created. Execution stops before S-010 as requested.
