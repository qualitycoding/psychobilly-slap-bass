# Psychobilly Slap Bass 0.1.0 — implementation plan

**Status: READY**  
**Profiles:** `software`; `audio = true`; `software.deploys = false`  
**Planning counts:** 29 claims (24 verified, 4 corroborated, 1 non-load-bearing single-source); 20 frozen test functions / 249 clean-red cases (host 5, DSP 6, events 4, operational/security 2, performance 1, listening 2); 16 steps; 4 human gates. Pre-mortem: 0 unresolved Critical/High; residual 4 Medium and 2 Low plus external store-access Medium. Assumption audit: 49 confirmed premises, 0 falsified, 5 unverifiable future/external items, all gated or risk-tracked. Planning review findings: 0 unresolved Critical/High; implementation review and adversarial breaks not yet run. Mutation testing: opted out (D-003).

This plan is self-contained and zero-question during execution except at its explicit human gates. Read `HANDOFF.md`, all D-records and the frozen tests before starting. Metrics establish regressions and physical plausibility only; they never establish perceptual realism.

## S-000 — Environment and access verification

1. Create `impl-<run_id>` from the generation branch. Keep all implementation commits there.
2. Run `plan/ENVIRONMENT.md` setup and version checks. Verify repository write permission and public source/archive reachability without printing or persisting credentials. Do not reuse the planning credential.
3. Verify JUCE and every pluginval archive hash, action SHA, runner label and native host toolchain. Confirm the frozen manifest and clean-red baseline.
4. Start `EXECUTION_LOG.md`; every subsequent attempt appends UTC time, step, attempt, pass/fail/blocked, commit and note.

**Done when:** all checks pass and the log exists. **On failure:** write `BLOCKED.md` and halt before delivery work.

## S-010 — Build skeleton, licensing and adapter boundary

1. Add C++20/CMake 3.22 project and pinned JUCE FetchContent. Configure only VST3 plus the headless `psychobilly-render` executable and native performance harness. Define `PSB_BUILD_VST3` and `PSB_BUILD_DEMOS`.
2. Implement D-020 identity/bus/MIDI/editor contracts, D-021 APVTS layout and host-safe parameter atomics. State entry points must not run in audio processing.
3. Add AGPL-3.0-only licence, third-party notices, README build/use instructions, `requirements.txt` and cross-platform `scripts/verify_freeze.py`. Implement the compiled-engine adapter behind `stubs/psb_contract.py` without editing the stub's public semantics or any frozen test.
4. Build all three native targets and run T-001/T-002.

**Done when:** VST3 identity/parameters are measured by the adapter, no AU/AAX/standalone/sample-player target exists, and notices are present.

## S-020 — MIDI, state and voice host integration

1. Implement D-023 MIDI parsing, sample-accurate note/automation/pitch-bend ordering, safe note filtering and zero-velocity note-on handling.
2. Implement D-022 canonical XML state with D-012 size/depth/content validation. Invalid input leaves active audio unchanged; no exceptions cross the host boundary.
3. Allocate eight voice slots and all delay/coupling storage at preparation. Implement D-019 quietest-then-oldest stealing, same-note retrigger and 10 ms crossfade. No allocation, lock, file, logging or network call in `processBlock`.
4. Run T-003–T-005 and lifecycle portions of T-011.

**Done when:** host/state/MIDI tests pass under repeated prepare/reset/reconfigure cycles.

## S-030 — String, excitation and body DSP

1. Translate the D-004/D-016 planning candidate into four extended digital-waveguide strings: fractional delay, frequency-dependent loop damping, pluck filtering and bounded fingerboard collision/contact excitation.
2. Add separate body/radiation filtering, attack and mechanical noise, deterministic seeded variation and D-019 sympathetic input from exactly the other seven outputs with radius `0.105`.
3. Implement all D-021 mappings, radiation cutoff `350 + 350*string_tension` Hz, fixed shipped-path mix scale `0.24` and D-021 output gain. No renderer normalisation or hidden safety gain may alter the measured shipped path.
4. Sanitise coefficients at rate changes and bound nonlinear/delay states. Denormal prevention must not mute valid low-level output.
5. Run T-010, T-012, T-013 and T-015; preserve failing diagnostic output rather than tuning the analyser around it.

**Done when:** known answers, finite/extreme-corner limits and monotonic control checks pass at every frozen rate/note/velocity.

## S-040 — Voice lifecycle and performance instrumentation

1. Complete eight-voice allocation/stealing/crossfade and click-free note-off/retrigger behaviour. Make reset and sample-rate changes deterministic.
2. Add a native benchmark using the shipped engine, eight active voices, 96 kHz, 64-sample blocks, seven five-second runs after a declared warm-up. Preallocation is required; benchmark-only simplifications are forbidden.
3. Emit JSON with every run, median/max RTF, runner OS/CPU/core count, compiler, commit and environment-lock hash. Enforce maximum RTF `<=0.25`; once a valid baseline exists, also enforce the D-018 10% bootstrapped regression rule.
4. Run T-011 and T-040 locally on every available native target.

**Done when:** measured data—not hardcoded success—meets D-018, or work halts at G-005.

## S-050 — Offline renderer and input boundaries

1. Implement `psychobilly-render --input <events.jsonl> --output <demo.wav> --metadata <demo.json>` exactly as D-024, including limits, equal-sample ordering and exit codes 0/2/3.
2. Reject unknown/duplicate/malformed fields, non-finite numbers, path ambiguity and output/input aliasing. Stream or bound memory by the event/frame limits; never trust a declared duration before validating it.
3. Render stereo 24-bit PCM at 48 kHz for demos and support 44.1/48/96 kHz for validated input. Write D-025 provenance including `normalisation_applied:false`.
4. Implement secure host-state and renderer adapters; run T-020–T-023 and T-030/T-031.

**Done when:** repeat renders are bit-identical in the same pinned environment, malformed inputs fail closed and active host sound survives invalid state.

## S-060 — Analysis and reproducible demo corpus

1. Implement the frozen analysers in `stubs/psb_contract.py`: matched-note pitch conditioning only for T-014, unconstrained known answers, onset, exponential T60 and spectral centroid. Never derive a pass from an expected value returned by the synth itself.
2. Run ordinary-pluck comparison against all seven D-070 CC0 references and report each result plus the frozen spread bound. Retain the decay mismatch as diagnostic, not realism evidence.
3. Add these ten D-024 JSONL files under `demos/events/` and render the matching WAV/JSON files at 48 kHz:
   - `demo-01-short-melody`: walking/psychobilly melodic phrase across the four strings.
   - `demo-02-fast-passage`: dense sixteenth-note alternate-string figure with retrigger/stealing stress.
   - `demo-03-dynamics`: matched phrase at softest through loudest velocities.
   - `demo-04-slow-sustain`: long sustained notes, note-off and sympathetic decay.
   - `demo-05-pluck-slap`: fixed phrase sweeping `pluck_slap` through all five frozen values.
   - `demo-06-brightness-body`: separate `slap_brightness` and `body_resonance` sweeps.
   - `demo-07-tension-sustain`: separate `string_tension` and `sustain` sweeps with pitch-bend centre/range checks.
   - `demo-08-noises-output`: separate attack/mechanical noise and output-level sweeps.
   - `demo-09-low-register`: lowest supported notes, open-string-like resonance and collision-heavy playing.
   - `demo-10-high-register`: highest supported notes, fast release and deliberately exposed weak slap/collision mode.
4. Assert ten events, ten WAVs and ten metadata records, hashes and provenance. Run T-014 and T-050/T-051.

**Done when:** every metric passes and the complete demo corpus is reproducible from text events.

## S-070 — Native CI and artifact integrity

1. Add workflows using only the exact action/runner pins in ENVIRONMENT, `fail-fast:false`, least-privilege permissions and independent evidence concurrency. Include the CMake 3.22.4 lower-bound job.
2. Run native build, frozen tests, pluginval and performance on Ubuntu, Windows and macOS. Do not mark unsupported or skipped jobs successful.
3. Add artifact existence/non-emptiness/schema assertions before upload; retain raw logs and machine-readable summaries. Never use `continue-on-error`, `|| true`, forced exit zero or a disabled-test list.
4. Add a source-artifact workflow only. Any public release workflow remains absent until G-002.

**Done when:** pushed-commit CI is green independently on all declared targets and each required artifact can be downloaded and verified.

## S-080 — Validator coverage and performance history

1. Run the exact primary pluginval command in ENVIRONMENT. Parse logs for D-014 coverage, requested configuration, expected test families, repeats, completion and zero skips/failures.
2. Apply D-011 only to a matching reproduced stable `PluginInfoTest` race; otherwise fix the plug-in. Keep both stable and any permitted fallback evidence.
3. Store per-runner performance history keyed by commit and lock hash. Run the bootstrap regression comparison without hiding individual maxima.
4. Run the complete frozen suite and native stress cycles at all declared rates/block sizes. Upload evidence and assert its digest.

**Done when:** validators demonstrably exercised the required surface and D-018 passes per runner; otherwise invoke G-005.

## S-090 — Security, licence and operational audit

1. Implement and run `scripts/audit_repository.py`: tracked content and history secret patterns, unsafe URL/credential handling, network/telemetry/account/retained-data features, dangerous deserialisation and missing notices. Report files/lines without printing matched secrets.
2. Run the pinned pip-audit command and review native/JUCE/VST3 dependency advisories at their exact pins. No ignore is permitted without G-005.
3. Exercise oversized/deep state, malformed JSONL, extreme automation/MIDI, long renders, path collisions, unwritable outputs, repeated resets and resource exhaustion. Fail safely with bounded resources.
4. Verify source/CI artifacts contain licence notices and no credentials; produce `artifacts/repository-audit.json`, dependency report and operational audit.

**Done when:** T-030/T-031 and all scans pass, findings are resolved, or a Critical/High unresolvable scope issue halts at G-005.

## S-REVIEW — Fresh traditional code review

A reviewer who authored none of the implementation reads the full diff and frozen tests. Review correctness, realtime safety, clarity, duplication, hidden mutation, untested paths, memory/file/input security and exact dependency/advisory status. Write `reviews/CODE_REVIEW.md`, severity-classify every finding and link each to a fix commit or accepted risk. Fix Critical/High findings before proceeding. Any new regression test follows unfreeze → explicit red → implementation → re-freeze; never edit a frozen test merely to obtain green.

**Done when:** no unresolved Critical/High finding, every path is traced to a test or named accepted risk, and the manifest matches the current approved freeze.

## S-ADVERSARIAL — Fresh adversarial review

A second fresh reviewer challenges every A/D premise embodied in code. Fuzz host state, MIDI, event JSON, automation and paths; force allocation/resource failure, invalid rates, extreme block sizes, rapid reconfiguration, voice theft, denormals/NaNs and dependency/validator failure. Confirm that logs and artifact gates cannot report false success. Write `reviews/ADVERSARIAL_REVIEW.md`. Every confirmed break becomes a Phase-2 frozen regression test or explicitly accepted risk; Critical/High breaks block listening and release.

**Done when:** all confirmed breaks are resolved or formally accepted below High, all new tests have clean-red history and full native CI is green again.

## S-100 — Sealed listening evidence

1. On a commit containing `[gate-evidence G-004]`, render the ten demos headlessly and create twelve start-window, one-second blind pairs from matched ordinary-pluck candidate/reference clips. RMS-match to −23 dBFS, fade cut ends and write 24-bit WAV; this pair-only matching does not normalise shipped demos.
2. Use `scripts/make_blind_pairs.py` with a recorded cryptographically generated seed. Exactly six pairs place the reference on A and six on B, shuffled by that seed. Store a sealed base64 key separately from the listener-facing sheet; do not disclose either until answers are recorded.
3. Include reference source/licence/checksum attribution, metric table, commit/environment provenance, `SHA256SUMS`, pair sheet and all ten demos. Push round N to orphan branch `evidence/G-004-round-N` using a dedicated non-cancellable concurrency group. Never include credentials.
4. Provide the branch archive URL and per-file raw URLs; if private, state that and provide an accessible route. Run T-050/T-051 against the actual bundle.

**Done when:** the sealed bundle is reachable, balanced, complete and hash-verified. No realism claim is made before listening.

## S-LISTEN — Human listening gate G-004

Ask the user to play pairs in order on their own headphones, A then B once each, and record which side is the reference. Ask for the twelve letters, whether the demos sound realistic, which sound off and how, and specifically whether slap attack, low register, high register, fast passages and control sweeps are musically convincing.

Record the response verbatim. Only then decode the key with `scripts/score_blind.py`; record score, one-sided p-value, side bias, seed and commit. Numeric pass is no more than 8/12 correct, but any substantive qualitative shortfall overrides it. Ordinary-pluck pairs do not establish slap realism; slap is judged from the demos.

On `iterate`, analyse the listener-identified region/mechanism, make one general targeted change per observed difference, rerun metrics/reviews and build a newly seeded bundle. Do not tune per-note constants to these clips. Maximum three disclosed rounds; then require `proceed-with-rescope` or `stop`. `proceed` completes audio validation only for the evidence actually heard.

## S-RETRO — Retrospective

After all delivery and gate work, collect `EXECUTION_LOG.md`, commits, deviations, blocks, challenges, gates, CI and prior/new lessons into one digest. A fresh reviewer reruns nothing and changes no deliverable. Identify every correction, overlooked check, unapplied/recurrent lesson and new reusable fact. Diff workflows/manifests against ENVIRONMENT and record every unexplained pin/package/timeout/config difference. Write `RETROSPECTIVE.md`; every finding links to an Appendix-compliant `L-` or `K-` item.

**Done when:** the execution history is complete and every finding has a valid lesson or knowledge ID.

## S-KNOW — Gated lessons and knowledge push

Halt at G-003 with the listed IDs/titles/tags and proposed stores. On approval, copy items to the approved store layouts, regenerate indexes and push; retry moved targets up to three times. On rejection, unavailability or no response, create and report the appropriate `lessons-<run_id>.bundle` and/or `knowledge-<run_id>.bundle`. Include the planning agent's lessons and knowledge. `do-not-push` is a valid completion. Never expose credentials in remotes, files or logs.
