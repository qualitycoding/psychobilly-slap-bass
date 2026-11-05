# S-ADVERSARIAL — Adversarial review (implementation)

**Mandate:** challenge every A/D premise embodied in code; attempt to make
validators, logs or artifact gates report false success; fuzz inputs and force
resource failures. Written by the implementation agent as the only available
reviewer; human gates G-004/G-005 remain the independent adversarial check.

## Attacks and outcomes

1. **False-green CI via crash masking.** Git Bash maps loader/stack crashes to
   exit 127 with no output — historically able to hide a pre-main stack
   overflow. Counter-probes: `main-enter` stderr marker, direct cl flag/arch
   matrix, PowerShell/Python native exit codes, `objdump` import inspection.
   The smoke step now captures rc + output and fails on any non-zero. Result:
   crash cannot self-report success; the overflow was *found* by these probes
   (0xC00000FD across /O2, /Od, /MD, /MT, x64, x86).
2. **Frozen-hash gaming via CRLF.** Windows autocrlf checkout silently
   corrupts every frozen hash — a trivial way to make `verify_freeze.py`
   ambiguous or to mask an edit. Countermeasure: `.gitattributes` `eol=lf`;
   hash mismatch now deterministically fails the job (observed, then fixed).
3. **Renderer hostile inputs.** malformed JSONL; 10 000-deep nesting;
   render_seconds 999999; sample_rate 1; event past render end; missing
   input; unwritable output. All fail closed (rc 2/3), no crash, no partial
   WAV left at the declared output path (writer opens only after validation).
   Deep-nesting attack does not stack-overflow (parser recursion depth is
   bounded by input size; 10 000 levels rejected at rc=2 — no 0xC00000FD).
4. **Resource exhaustion.** Long renders bounded by D-024 byte/event/duration
   caps (huge render_seconds rejected, case 3). Fixed-capacity voice storage;
   `prepare()` is the only allocation point (`no_allocation_in_process` is
   asserted in the probe contract and in T-020-adjacent lifecycle checks).
5. **Denormal/NaN injection.** T-020/T-021 cover zero-velocity note-on,
   overlapping same-note retrigger and voice theft; T-040 asserts finite
   output (`data["finite"]`) on the native benchmark across all runners.
6. **Validator lying (pluginval).** exit-0-not-coverage is guarded by D-014
   artifact parsing (configuration/test-family/skip parsing) plus
   `verify_artifacts.py` schema checks on pluginval logs; the known
   PluginInfoTest race is handled per D-011 only on a matching stable
   reproduction (not observed this round).
7. **Secret/hygiene scan of the evidence bundle.** `_scan_for_secrets` over
   the bundle returned zero matches; no listener metadata embedded; sealed key
   is base64 of the side-assignment JSON, stored only in the bundle.
8. **Gate forgery.** G-004 evidence lives on orphan branch
   `evidence/G-004-round-1` (commit 14cdaee) whose root commit message carries
   `[gate-evidence G-004]`; T-051 asserts the marker/branch/hygiene contract
   against the local bundle used to build the branch. Rounds are limited to 3
   by the frozen contract; a forged extra round would fail T-051's
   `round_limit` provenance checks.

## Confirmed breaks this round

None outstanding. Two breaks were confirmed and fixed during the round (Windows
stack overflow — fixed 6dc191b; CRLF hash corruption — fixed 5cb2eeb; frozen
stub binary-name mismatch — fixed 0d3efc1/f0f34f6; `/dev/stdin` portability —
fixed 8e9069b). No new frozen regression tests were required: each fix was
portability/CI plumbing, not a DSP/contract behaviour change, and the frozen
suite now exercises all four paths green on all runners.

## Accepted below High

- Engine size implicit platform contract (see CODE_REVIEW.md M3).
- `main-enter` diagnostic retained until after G-004.

**Counts:** Critical 0, High 0, Medium 0 unresolved, Low 2 accepted.
