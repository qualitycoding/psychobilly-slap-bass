# Adversarial review (S-ADVERSARIAL)

**Reviewer limitation:** same agent as the implementer (see CODE_REVIEW.md).
Treat this as a structured self-challenge; the human gate decides on an
independent re-review.

## Attack surface exercised

1. **Malformed state XML** — random truncation, wrong root tag, `schema="2"`,
   missing PARAMs, duplicate ids, values outside [0,1], non-numeric values:
   all rejected by `validate_state`/`setStateInformation` without touching
   active audio. (T-022/T-030 green.)
2. **Event JSONL fuzzing** — unknown fields, duplicate keys (json.h rejects),
   non-finite numbers, out-of-order samples, samples beyond declared duration,
   rates outside the whitelist, documents over the 1 MiB limit, empty events:
   all fail closed with exit code 2 and no output file written. (T-021/T-023.)
3. **Resource exhaustion** — 256 note-ons in 64-sample steps: voice count
   bounded at 8, steals counted, no growth. 65536-event cap enforced;
   19200000-frame cap enforced; render memory bounded by frame count.
4. **Denormals/NaN** — `sanitise_` zeroes below 1e-300 in the loop; engine
   output checked finite across all frozen rate/note/velocity corners (T-010);
   `ScopedNoDenormals` in the plugin wrapper; bench reports `finite:true`.
5. **Voice theft / retrigger** — same-note retrigger preserves delay-line
   energy (T-017); quietest-then-oldest steal verified by T-015.
6. **False-success gates** — the analyser is not tuned to the synth's own
   expectations: T-014 conditioning uses only the matched note (no synth
   output fed back); T-012 known answers are synthetic signals with
   octave-off and missing-fundamental traps; the listening gate (G-004)
   requires human answers, and `score_blind` fails closed above 8/12.
7. **Secrets** — repo-wide and history scan clean; the planning PAT used for
   push is never committed (remote URL constructed at push time in a detached
   job, credential not persisted in any file).
8. **Dependency advisories** — pip-audit pinned at 2.10.0, `--strict`, no
   ignores (CI artifact `pip-audit.json`).

## Confirmed breaks found during review

- (fixed) Block-staircase component capture — see CODE_REVIEW.md. Would have
  allowed vacuous T-017/T-013 passes; now genuinely measured per sample.
- (fixed) Loop-gain per-pass error — see D-044.
- (fixed) Onset glide inversion — see D-042.
- (fixed) T-052 malformed document construction — see D-043.

## Accepted risks (below High)

- No GUI editor; generic host panel only.
- `no_allocation_in_process` is an audited claim, not an instrumented measure.
- pluginval GUI-side coverage is limited by the headless editor (CI uses the
  exact primary command; no skips are passed).

## Verdict

All confirmed breaks resolved; no Critical/High break remains open. New
regression coverage for the found breaks exists via the corrected frozen
tests themselves (D-042/D-043 amendments plus the previously frozen
T-013/T-016/T-017 gates).
