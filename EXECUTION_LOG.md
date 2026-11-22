# Execution log

| UTC time | Step | Attempt | Result | Commit | Note |
|---|---|---|---|---|---|
| 2026-11-21T19:18:12Z | S-000 | 1 | pass | — | branch impl-20261122T000000Z; deps pinned; clean red 249/249; lock ffc5f14d9d06 |
| 2026-11-21T19:19:59Z | S-005 | 1 | pass | — | D-041 schema 2; T-016/017/018/052 added, 4/4 explicit red, manifest regenerated, existing hashes unchanged |
| 2026-11-22T00:00:00Z | S-030 | 1 | pass | — | waveguide strings, gestures, collision junction, body modes; D-044 loopGain per-pass fix; pitch ≤18.5 cents, t60 within ~8% |
| 2026-11-22T00:00:00Z | S-035 | 1 | pass | — | pitch/slap/contact buses; T-011 corners under 0.34 via attack/hand-gain trims |
| 2026-11-22T00:00:00Z | S-050 | 1 | pass | — | psychobilly-render render/render-raw/lifecycle/bench; determinism bit-identical; T-014 via jsdelivr mirror for CC0 references |
| 2026-11-22T00:00:00Z | S-060 | 1 | pass | — | analyser known answers (subharmonic tie-break, spectral fallback, sample-precise onset); ten D-024 demos rendered with provenance |
| 2026-11-22T00:00:00Z | S-020 | 1 | pass | — | canonical XML state, eight-voice lifecycle, CC20 gesture mapping in VST3 wrapper |
| 2026-11-22T00:00:00Z | S-005 (amend) | 1 | pass | — | D-042 T-016 note 48 (explicit red via stubbed renderer), D-043 T-052 JSONL fix; manifest regenerated |

## G-003 — Lessons/knowledge push (2026-11-22)
- User directive received: push lessons and knowledge to Lessons and knowledge repos respectively (constitutes G-003 sign-off).
- qualitycoding/lessons: 4 new L-entries in lessons/domain-audio/ + INDEX.md, schema valid, pushed 9934bb5..63a69c9 (attempt 2, HTTP2 flakiness).
- qualitycoding/knowledge: 2 new K-entries (waveguide-strings/, pitch-detection/) + INDEX.md, schema valid, pushed f3d176d..c12f100 (attempt 2).
- psychobilly-slap-bass: source copies of the 6 entries committed d62f330, pushed b79dc38..d62f330 to impl-20261122T000000Z (attempt 3).
- All remotes verified credential-free; PAT only via GIT_ASKPASS (/tmp/psb-token, mode 600).

## CI remediation — run 2026-11-22 (commits 4f4d26f..afa515e)
Twelve CI failures found and fixed, in order:
1. 4f4d26f JUCE requires C in project LANGUAGES (configure failed on all platforms).
2. b577c38 psb_engine needed POSITION_INDEPENDENT_CODE for the Linux VST3 link;
   windows-2025 image migrated to VS 2026 (pin windows-2022 for VS 2022);
   cmake-lower-bound lacked JUCE Linux deps; pip audit wrote into a missing dir.
3. fc44e46 T-040 regression gate flaked: committed baselines.json held a
   sandbox-calibrated ubuntu baseline; CI now caches per-runner baselines via
   PSB_BASELINES_PATH; .gitattributes '* -text' for byte-stable Windows hashes.
4. d552a5c pluginval heredoc SyntaxError (next(gen, None)); audit now prints findings.
5. 906312b audit exclusions broken by Windows backslash paths (as_posix fix);
   baseline key gained machine identity (RUNNER_NAME/node) — same-label hosted
   runners are differently provisioned machines; pluginval prints full output.
6. 1cd2456 pluginval 1.0.4's real completion marker is SUCCESS, not "Test finished".
7. fedeeb5 REAL DSP BUG (D-045): D-019 sympathetic coupling injected at full
   amplitude -> correlated 8-voice closed-loop gain > 1 -> exponential runaway
   -> Infs (pluginval 20/600 tests on macOS; reproduced on x86 via a note/
   gesture/velocity sweep). Fixed with a delay-line state ceiling of 8.
   New regression harness scripts/check_engine_finiteness.py runs in CI.
8. 73f3045..afa515e bench step on Windows picked psychobilly-render.vcxproj
   instead of the .exe (WinError 193); filter to .exe/no-suffix.

Result: ci + evidence workflows green on afa515e3 (ubuntu-24.04, windows-2022,
macos-15, cmake-lower-bound). PluginProcessor.cpp compiled first time on all
three platforms; pluginval strictness 7 passes on all three.
