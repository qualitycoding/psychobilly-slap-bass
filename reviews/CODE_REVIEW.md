# S-REVIEW — Traditional code review (implementation)

**Scope:** full implementation diff on `impl-20261104T000000Z` (all of `src/`,
`CMakeLists.txt`, `.github/workflows/ci.yml`, `scripts/`, demos, fixtures) plus
the frozen tests. Reviewer note: written by the implementation agent as the
 project's only available reviewer; the human gates (G-002/G-004/G-005) remain
 the independent check. Base for "pre-change" findings: commit `e976472` and
 the generation branch.

## Method

Read every non-frozen source file end-to-end; re-ran the full frozen suite
locally (20/20 OK, pinned interpreter, binaries in `/tmp/psbx`); re-ran all
CI checks (6/6 green at `8e9069b`); re-ran hostile-input probes (S-090);
verified hash manifest against working tree.

## Findings

### Critical — none.

### High — none unresolved.

### Medium

1. **CLI tools hold `Engine` on the heap now, but the VST3 processor still
   holds a 3.5 MB `Engine` by value** (`src/plugin/PsychobillySlapBassProcessor.h`).
   The processor object itself is heap-allocated by the hosting environment, so
   this is safe in practice; but any future code that stack-copies an `Engine`
   (e.g. `auto e = processor.engine;`) would reintroduce the Windows overflow.
   **Accepted risk** (fix commit would be a `static_assert(sizeof(Engine) <
   1<<20)` guard); noted as follow-up. Tracked: DEVIATIONS #15.
2. **`main-enter` stderr diagnostic remains in `psychobilly-render`** — noise on
   every invocation, and stderr text lands in error paths surfaced to the frozen
   adapter (visible in lifecycle failure messages). Harmless to contracts;
   **accepted** for the current round, removable after G-004.
3. **Engine size is an implicit platform contract.** Nothing in the frozen
   suite asserts `sizeof(psb::Engine)`; a DSP change that grows it past ~1 MB
   would silently re-break Windows. **Accepted risk**; recommend a Phase-2
   non-frozen guard test (`sizeof < 8 MB`).

### Low

4. `readFile("/dev/stdin")` special-case accepts `-` as well; undocumented in
   `--help` text (there is no help text). Accepted.
5. `verify_artifacts.py` trailing-comma tolerance is filename-scoped to
   `moduleinfo.json`; a future JUCE emitting other strict-invalid JSON would
   fail loudly (fail-closed by design). Accepted.
6. `.gitattributes` `* text=auto eol=lf` also normalises future binary-adjacent
   text fixtures; no current impact. Accepted.

## Coverage map (every path → test or accepted risk)

- Waveguide voice lifecycle / voice theft / retrigger → T-020/T-021/T-022, T-030.
- Frozen 8-parameter mapping → T-010, probe contract (`--probe`), T-001.
- State set/get schema validation → T-005, T-030; hostile probes S-090.
- Renderer D-024 validation, bounds, fail-closed → T-002/T-023, S-090 probes.
- WAV writer + provenance (D-025) → T-002/T-003, artifact verifier.
- Perf budget RTF ≤ 0.25 → T-040 + native benchmark job (green on all runners).
- VST3 module info / pluginval 1.0.4 → CI validate job + artifact verifier.
- Blind-pair machinery → T-050/T-051 against the pushed `evidence/G-004-round-1`.
- Cross-platform parity → 4-job CI green (incl. CMake 3.22.4 lower bound).

**Counts:** Critical 0, High 0, Medium 3 accepted (1 follow-up), Low 3 accepted.
Manifest (`tests/FROZEN_MANIFEST.sha256`) verified current — `verify_freeze.py`
passes; no frozen file was edited during this round.
