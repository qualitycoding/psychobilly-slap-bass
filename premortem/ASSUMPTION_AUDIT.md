# Assumption and premise audit

A fresh adversarial pass attempted to falsify every intake assumption, decision premise, non-corroborated research claim and silent frozen-test premise. `Confirmed` means the requirement is explicit and its present factual premise remains supported; it does not mean an unimplemented future result has already passed.

## Intake assumptions

| ID | Premise and falsification check | Verdict | Evidence / consequence |
|---|---|---|---|
| A-001 | Product is VST3-only; another required format would falsify. | confirmed | User intent, D-020, T-001 |
| A-002 | Three named desktop targets are buildable/testable. | unverifiable | Labels exist, but implementation/host behaviour is future; S-000/native CI, R-004/R-007 |
| A-003 | Four-string pluck/slap/body/sympathy candidate is the product direction, not proven realism. | confirmed | D-004/D-016, C-008–C-010/C-023; G-004 |
| A-004 | Eight controls plus velocity/bend are required. | confirmed | D-021/D-023, T-002/T-004/T-012 |
| A-005 | JUCE 9 exists and 9.0.5 is the selected C++20/CMake framework. | confirmed | C-001–C-003/C-017/C-018, D-002 |
| A-006 | Eight voices/realtime safety and all target performance are attainable. | unverifiable | Linux spike only; native S-040/S-080, R-004 |
| A-007 | Automated plus human listening validation is required; user is listener. | confirmed | D-015/D-071, G-004 |
| A-008 | 0.1.0 source/CI only; public binaries need approval. | confirmed | D-013, G-002 |
| A-009 | Privacy constraints are binding; best-effort maintenance is not a measured guarantee. | confirmed | D-026, S-090; maintenance limitation retained |
| A-010 | Intended users are psychobilly musicians/producers. | unverifiable | No user research claimed; G-004 is the product check, R-009 |
| A-011 | Rates/host format and 48 kHz demos are explicit requirements. | confirmed | D-020/D-024, native/pluginval matrix |
| A-012 | Untrusted host/render inputs define the threat boundary. | confirmed | D-026, T-005/T-020/T-021/T-030 |
| A-013 | Host/local/CI evidence are the only data locations. | confirmed | D-025/D-026/D-030, T-051 |
| A-014 | SemVer starts at 0.1.0. | confirmed | D-020 |
| A-015 | Both stores were writable at intake and remain writable now. | unverifiable | Current credential is unavailable; S-000/S-KNOW checks and bundle fallback, R-013 |
| A-016 | Subject tags correctly classify the work. | confirmed | Present throughout claims/knowledge/lessons |
| A-017 | Same-lock determinism is testable; cross-platform bitwise identity is not claimed. | confirmed | T-023; floating comparison premise checked in D-025 |
| A-018 | Only redistribution-cleared references enter evidence. | confirmed | C-011/C-012, D-070, attribution/checksums |

## Decision premises

| ID | Premise checked | Verdict | Evidence / risk |
|---|---|---|---|
| D-001 | JUCE open licence is AGPL-3.0-only/commercial. | confirmed | C-001, K-…003002 |
| D-002 | Exact JUCE commit/tag exists. | confirmed | C-002 |
| D-003 | Mutation opt-out is deliberate for this suite/ROI. | confirmed | Decision recorded; reviews remain mandatory |
| D-004 | Extended waveguide/contact/body is a feasible candidate, not an established perceptual model. | confirmed | C-008/C-009/C-023 |
| D-005 | pluginval 1.0.4 and strictness/options exist. | confirmed | C-006/C-022 |
| D-006 | Versioned runner labels exist. | confirmed | C-007/C-014 |
| D-007 | Host-only parameters and null editor satisfy scope. | confirmed | C-017, T-001/T-002 |
| D-008 | APVTS state copy/replacement locks and stays off audio thread. | confirmed | C-018 |
| D-009 | ARM64/libc waivers match declared targets. | confirmed | A-002, TRACEABILITY |
| D-010 | Public PyPI serves identical pins. | confirmed | C-016 setup output |
| D-011 | Only the exact matching race qualifies for fixed-source fallback. | confirmed | C-021 issue/fix |
| D-012 | State cap/shallow validation and macOS 12 premise are supported. | confirmed | C-019; T-005 hostile cases |
| D-013 | Licence/notice/source-only artifacts meet scope. | confirmed | C-001/C-020, G-002 |
| D-014 | Exit zero requires coverage assertions. | confirmed | C-022 |
| D-015 | Balanced sealed/new-seed rounds and three-round limit follow listening protocol. | confirmed | Skill §§2/5/7, T-050/T-051 |
| D-016 | Candidate is numerically bounded with fixed shipped-path gain. | confirmed | C-023/C-024 R6 output; realism explicitly unverified |
| D-017 | Numeric regression limits are empirically attainable and not realism claims. | confirmed | C-023–C-027 |
| D-018 | Native per-runner performance can be guaranteed from Linux spike. | unverifiable | Only budget/procedure confirmed; R-004, G-005 |
| D-019 | Eight-slot lifecycle/coupling candidate is bounded and deterministic. | confirmed | C-026, T-011 |
| D-020 | Host identity/bus/note-range contract is internally consistent. | confirmed | T-001/T-003/T-004 |
| D-021 | Eight parameter contracts/defaults/mappings are complete. | confirmed | T-002/T-012, R6 monotonic spike |
| D-022 | Canonical state is uniquely validateable and invalid state preserves audio. | confirmed | T-005 and shallow XML contract |
| D-023 | Omni/12-TET/bend/note-off conventions are unambiguous. | confirmed | T-004/T-010/T-011 |
| D-024 | Event and CLI contracts bound all external input. | confirmed | T-020–T-023 |
| D-025 | Provenance records enough to reproduce without normalisation. | confirmed | T-022/T-023 and environment-lock hash |
| D-026 | Security boundary covers runtime, repository and evidence. | confirmed | T-030/T-031/T-051, S-090 |
| D-027 | Adapter must measure compiled engine and red failures reach stubs first. | confirmed | red-output 249/249 explicit stub errors |
| D-028 | Round branches match T-051; reused references preclude independence claim. | confirmed | T-051, seven-file manifest; p-value narrowed |
| D-029 | Baseline creation/update cannot hide regressions. | confirmed | Rule 14 baseline requirements and S-040/S-080 |
| D-030 | Evidence access must be tested rather than inferred from push success. | confirmed | S-000/S-100 blocking rule |
| D-031 | Planning zero findings are not implementation coverage. | confirmed | Review headers and replacement steps |
| D-070 | Seven pinned CC0 files are ordinary-pluck reference candidates. | confirmed | C-011/C-012/C-013, manifest hashes |
| D-071 | Those references cannot validate slap; demos carry that judgement. | confirmed | C-010 non-load-bearing, G-004 |

## Research and frozen-test premises

- **C-010 — unverifiable as a general acoustic claim; confirmed only as a attributed practitioner observation.** It is `single-source`, non-load-bearing and cannot justify architecture/realism. R-006/R-009 and D-071 contain the consequence.
- **All other claims:** 24 `verified` and 4 `corroborated`; each was re-checked against its recorded source/output and none remains `single-source` or `inferred`.
- **Frozen tests:** fixtures are present and hash-locked; all 20 functions/249 cases reach explicit stubs, so no test silently passes or fails from syntax/import/fixture/type errors. Numeric thresholds trace to R6 measurements. Tests measure contracts/proxies, not perceptual realism. `tests/FROZEN_MANIFEST.sha256` verification remains mandatory.
- **Reference analyser:** matched-event conditioning cannot leak into known-answer tests; T-015 independently challenges pitch/onset/T60/centroid. Confirmed by C-024/C-027.
- **No implementation outcome is presumed:** build, native performance, pluginval, host ABI and listening remain future checks with blocking/gate behaviour.

## Audit result

**Confirmed: 49 requirement/premise items; falsified: 0; unverifiable future/external items: 5** (A-002, A-006, A-010, A-015, D-018), plus C-010 narrowly retained as non-load-bearing observation. Every unverifiable item maps to R-004/R-007/R-009/R-013 and a test or gate. No falsified load-bearing item remains; no L/K amendment pair is required. The separate cold-read branch mismatch is recorded by L-20261104T013500Z and D-028.
