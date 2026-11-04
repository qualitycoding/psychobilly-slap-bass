# Requirements, tests and delivery traceability

Every row is a completion obligation. A step is not complete merely because its files exist: its cited frozen tests, workflow assertions and evidence post-conditions must pass on the pushed implementation commit.

| ID | Success criterion | Frozen verification | Producing step(s) |
|---|---|---|---|
| SC-001 | Source builds as a VST3-only instrument named `Psychobilly Slap Bass`, version `0.1.0`, with the D-020 host identity, MIDI input, stereo output and no editor. | T-001; native pluginval coverage assertions | S-010, S-020, S-080 |
| SC-002 | Exactly eight host parameters expose the D-021 identifiers, order, ranges and defaults; host state follows D-022 without audio-thread locking. | T-002, T-005 | S-020, S-050 |
| SC-003 | Four extended-waveguide strings provide pluck, contact/collision, body/radiation and bounded sympathetic paths with deterministic velocity and pitch-bend behaviour. | T-010, T-011, T-013, T-014, T-015 | S-030, S-040 |
| SC-004 | Eight voices implement D-019 stealing/retrigger/crossfade and all declared realtime-safety constraints. | T-011, T-040; pluginval lifecycle coverage | S-040, S-080 |
| SC-005 | All controls have the frozen monotonic audible-proxy effect and the extreme-corner output remains finite, non-subnormal and below the frozen peak limit. | T-012, T-013 | S-030, S-040 |
| SC-006 | Known-answer pitch, onset, decay and centroid measurements meet D-017; ordinary-pluck comparison meets its frozen bound without claiming perceptual realism. | T-014, T-015 | S-030, S-060 |
| SC-007 | The offline CLI accepts only D-024 event files, renders deterministic 24-bit stereo WAV and writes D-025 provenance with no normalisation. | T-020–T-023 | S-050, S-060 |
| SC-008 | Untrusted state, MIDI/events, automation and files fail safely; scans find no committed secret, dependency vulnerability or forbidden runtime service. | T-030, T-031; S-090 scan reports | S-050, S-090 |
| SC-009 | Native jobs cover every declared platform; versioned actions/runners, pinned tools and asserted artifacts make CI reproducible and non-skipping. | Workflow post-conditions; T-001–T-040; T-050 bundle checks | S-070, S-080 |
| SC-010 | The 96 kHz/64-sample eight-voice workload meets D-018 per CI runner, with measured history and regression control. | T-040 and uploaded JSON | S-080 |
| SC-011 | Ten reproducible demos and twelve balanced blind pairs support G-004; seeds, keys and disclosed rounds follow the listening protocol. | T-050, T-051; human gate record | S-100, S-LISTEN |
| SC-012 | Independent code/adversarial reviews, final evidence, retrospectives and gated knowledge transfer complete without silently weakening tests. | Review/gate post-conditions; frozen-manifest check | S-REVIEW, S-ADVERSARIAL, S-RETRO, S-KNOW |

## Reverse test map

| Test | Requirement and decision coverage |
|---|---|
| T-001 | SC-001; A-001/A-005; D-002/D-020 |
| T-002 | SC-002; A-004; D-007/D-021 |
| T-003 | SC-001; D-020 |
| T-004 | SC-001/SC-003; D-023 |
| T-005 | SC-002/SC-008; D-008/D-012/D-022 |
| T-010 | SC-003; D-004/D-016/D-023 |
| T-011 | SC-003/SC-004; D-019/D-023 |
| T-012 | SC-005; D-017/D-021 |
| T-013 | SC-003/SC-005; D-016/D-017 |
| T-014 | SC-006; D-017/D-070 |
| T-015 | SC-006; D-017/D-027 |
| T-020 | SC-007/SC-008; D-024 |
| T-021 | SC-007/SC-008; D-024 |
| T-022 | SC-007; D-024/D-025 |
| T-023 | SC-007; A-017; D-024/D-025 |
| T-030 | SC-008; A-012/A-013; D-026 |
| T-031 | SC-008; D-026 |
| T-040 | SC-004/SC-010; D-018/D-027 |
| T-050 | SC-011; D-015/D-070/D-071 |
| T-051 | SC-011; D-015/D-071 |

## CI platform mapping

| Intake target | Native CI job | Waiver |
|---|---|---|
| Ubuntu 24.04 x64 | `ubuntu-24.04` build, tests, pluginval and performance | None |
| Windows 11 x64 | `windows-2025` build, tests, pluginval and performance; S-000 verifies the image reports a supported Windows 11 build | None |
| macOS 15+ Apple Silicon | `macos-15` build, tests, pluginval and performance with deployment target 12.0 | None |
| ARM64 Linux | None | D-009: out of scope |
| Alternative libc | None | D-009: glibc Ubuntu is the only declared Linux target |
| Oldest supported CMake | Additional `ubuntu-24.04` job with CMake 3.22.4 | None |

All matrix jobs use `fail-fast: false`. The generation branch supplies planning evidence only; implementation results must come from the implementation branch and its CI runs.
