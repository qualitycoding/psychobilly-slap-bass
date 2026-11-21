# Code review (S-REVIEW)

**Reviewer limitation (declared up front):** in this environment the review was
performed by the same agent that authored the implementation. There is no
independent fresh reviewer. This document records the review honestly as a
self-review; the human gate (G-002/G-004/G-005) decides whether an independent
re-review is required before release.

## Scope

Full diff of the implementation branch: `src/psb/*`, `src/plugin/*`,
`stubs/psb_contract.py`, `CMakeLists.txt`, `scripts/*`, workflows, demos,
fixtures, docs. Frozen tests were read but not edited (two test-side defect
corrections only, under the D-040 procedure: D-042, D-043).

## Findings

### Medium — component capture originally recorded block-end values (fixed)

`Engine::render()` initially copied the per-tick `last*Bus_` members after each
block, so every sample in a block received the block-end value (a per-block
staircase; contact/attack appeared as constants). T-017 could pass vacuously on
near-zero contacts and T-013 centroid measures were garbage. Fixed by capturing
per-sample inside `fillBlock` through explicit capture buffers. The freeze now
genuinely exercises the buses.

### Medium — loop gain applied per-sample but consumed per-pass (fixed, D-044)

See D-044: decay was ~nInt× too slow, leaving a sub-audio floor. Fixed with the
per-pass gain and lazy recompute on integer-delay change.

### Medium — onset glide inverted vs D-034 (fixed, D-042)

The model lengthened the delay line at onset (pitch drops); a released string's
tension spike pitches up. Fixed (negative `glideExtra`), depth capped at 120
cents so onset pitch stays inside the ±100 cent analyser window.

### Low — `Engine::lifecycle().no_allocation_in_process` is a static claim

It is set `true` at construction rather than measured. `fillBlock` was audited
by reading: no allocation, locks, file or network calls; buffers are allocated
in `render()` (offline) or as reused members in the plugin wrapper. Accepted
risk: the flag itself is not instrumented. Traced to T-015's allocator
statistics contract, which does exercise steals/retriggers/max-voices.

### Low — plugin wrapper has no editor

`createEditor()` returns nullptr and `hasEditor()` is false. pluginval at
strictness 7 runs headless-style tests; GUI hosting in DAWs shows a generic
panel. Accepted for 0.1.0; a real editor is post-G-002 scope.

### Low — VST3 wrapper not compiled in this sandbox

No JUCE checkout or X11 headers locally; the wrapper compiles in CI (native
matrix) for the first time on push. Risk monitored by the CI jobs; any build
failure is fixed on the impl branch before the gates are requested.

## Realtime safety

`processBlock` performs no allocation (member scratch vectors sized at
prepare/first block), no locks, no I/O. Events are queued before block fill in
nondecreasing sample order. `Engine` deletes its copy semantics; voices and
transients are allocated at `prepare()`.

## Security

State XML is schema-checked and range-validated; invalid state leaves active
audio unchanged. The renderer validates every event field, document size,
rate whitelist, equal-sample ordering, and frame/event limits. No network,
telemetry or account code exists in shipped sources; `scripts/audit_repository.py`
reports zero findings (see artifacts/repository-audit.json in CI).

## Verdict

No unresolved Critical/High findings. Medium findings fixed. The manifest
matches the current approved freeze (`sha256sum -c tests/FROZEN_MANIFEST.sha256`
clean).
