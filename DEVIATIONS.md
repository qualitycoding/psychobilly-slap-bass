# Deviations

Every substitution of a pinned version, mirror, timeout, package, config or
workflow is recorded here with evidence. None relaxes a frozen test, gate or
threshold.

## Local sandbox environment (implementation host)

1. **Implementation host OS is Debian 12, not Ubuntu 24.04.** The sandbox has no
   root and no apt; JUCE's Linux development packages (ALSA, Xinerama, Xrandr,
   Xcursor and runtime libs) were obtained as Debian bookworm `.deb`s from
   `deb.debian.org` and extracted with `dpkg -x` into a local sysroot
   (`/tmp/psb-tools/sysroot` during the run; CI installs the same packages via
   apt on `ubuntu-24.04`). Package names and ABI versions match the JUCE 9.0.5
   CMake requirements; the authoritative Ubuntu 24.04 build runs in CI.
   Evidence: `research/spikes/toolchain/setup-output.json` pattern; CI job logs.
2. **No-root sysroot instead of system install.** Same packages, different
   install location (`CMAKE_PREFIX_PATH`/`PKG_CONFIG_PATH` point at the
   sysroot). No JUCE or engine source/config change.
3. **CMake 3.31.6 installed from the PyPI wheel** into a local tools directory
   (the sandbox PATH has no cmake). Same upstream version as pinned; CI uses
   the runner-provided CMake plus the 3.22.4 lower-bound job.
4. **JUCE 9.0.5 fetched as the pinned tag-commit tarball** for the local build
   (full-commit FetchContent clone of the ~1.3 GB JUCE history exceeds the
   sandbox network budget). `CMakeLists.txt` keeps the mandated
   `FetchContent` declaration with `GIT_SHALLOW FALSE` at the pinned commit,
   which is what CI executes; locally the identical source tree is supplied via
   `FETCHCONTENT_SOURCE_DIR_JUCE`. The tarball is the GitHub-generated archive
   of the pinned tag commit `d60b7a78030661574a615b586d9325ba7a7fa7dd`.
5. **Binaries are executed from `/tmp`, not the checkout.** The durable mount
   forbids exec bits, so built binaries are copied to an executable location
   before running (recorded lesson L-20261104T004100Z). CI runs on a normal
   filesystem. The adapter additionally honours `PSB_BUILD_DIR` for this.
6. **Local runner label mapping.** `psychobilly-perf` reports the GitHub runner
   label matching the host OS family (`ubuntu-24.04` for Linux,
   `windows-2025`, `macos-15`); the `RUNNER_LABEL` environment variable
   overrides it. Local sandbox measurements are recorded to
   `build/performance/baselines-local.json` (untracked) so they never
   contaminate CI baselines in `performance/baselines.json` (D-029); CI runs
   (GITHUB_ACTIONS=true) record and enforce against the repository file.
7. **Network installs ran in detached retry loops** per the standing convention
   for the intermittently reachable hosts (github.com, raw.githubusercontent.com,
   files.pythonhosted.org, deb.debian.org).

## Planning-branch record gap

8. **D-001..D-027 full texts are not present on the generation branch.**
   `plan/DECISIONS.md` contains only D-028..D-031; the HANDOFF references
   D-001..D-027 as binding. Their operative contents were reconstructed from
   the frozen tests (`tests/`), the traceability matrix (`plan/TRACEABILITY.md`),
   the verified R6 spike (`research/spikes/dsp/`) and `plan/PLAN.md`; where the
   lifecycle spike code and D-019's textual rule conflicted (steal-tie age
   direction), the D-record text was treated as binding and the spike code as
   the stale artifact. Where the spike's output-gain curve could not satisfy
   the frozen T-023 ratio, the D-021 mapping `gain = 4^(2*(output_level-1))`
   (identical to the spike curve within 0.1 dB, exact 4.0 ratio at the frozen
   probe points) was used. No frozen test was modified.

## Runtime code choices within frozen contracts

9. **Analyser t60 on signals without a measurable decay returns NaN** instead
   of raising, because frozen T-012 calls `analyse` on steady tones and reads
   only onset/centroid. Gates that consume t60 (T-013) fail loudly on NaN.
10. **Implementation-host tmpfs is wiped unpredictably** (both `/tmp` and
    `/var/tmp` observed reaped mid-build). All durable artifacts live on the
    `/mnt/agents` mount (which forbids exec bits): the sysroot, the pip
    package set and the cmake wheel install live next to the checkout, and
    built binaries are compiled into a fresh tmp directory at the start of
    each verification run (`PSB_BUILD_DIR`). The full JUCE VST3 build runs in
    tmp with a resume loop and its products are copied back into `build/`
    immediately after linking. CI is unaffected (normal runners).
11. **JUCE 9.0.5 API adjustments in the plug-in wrapper** (no contract
    change): `project()` declares `LANGUAGES C CXX` because JUCE 9 requires
    the C language enabled; the parameter-ID probe reads
    `AudioProcessorParameterWithID::paramID` (JUCE 9 removed the base-class
    `getParameterID()` virtual); the bundle identifier is stringised with
    `JUCE_STRINGIFY(JucePlugin_CFBundleIdentifier)` (the macro expands to an
    unquoted token sequence). Verified against the pinned JUCE source at
    `d60b7a78030661574a615b586d9325ba7a7fa7dd`.
12. **Engine bug fixes found by frozen T-014 / T-050** (spike-port defects,
    contracts unchanged): the emitted `pitched` component is now the
    post-radiation-filter signal exactly as in the spike (the radiation
    butterworth at `350 + 350*tension` Hz was computed for the body path but
    the pre-filter tap was returned, leaving the candidate ~2 octaves brighter
    than the reference corpus); the renderer frame count rounds
    `render_seconds * sample_rate` (`lround`) instead of truncating, matching
    the frozen adapter's `round` — the two differ by one frame for
    half-sample document durations (e.g. demo renders), which broke the raw
    float64 reshape in `render()`.

## 13. VST3 moduleinfo.json is not strict JSON

JUCE 9.0.5 emits `moduleinfo.json` inside the `.vst3` bundle with trailing
commas. The JUCE-side parser accepts this, but strict `json.loads` rejects it.
`scripts/verify_artifacts.py` now strips trailing commas (outside strings)
before parsing any file named `moduleinfo.json`, keeping strict validation
for every other JSON artifact.

## 14. Windows CLI executables statically link the MSVC runtime

Git Bash maps a missing `vcruntime140*.dll` to exit code 127 with no output,
which killed the renderer smoke step on `windows-2025`. `CMakeLists.txt`
sets `CMAKE_MSVC_RUNTIME_LIBRARY` to `MultiThreaded` for all targets when
`MSVC` is true, so `psychobilly-render`, `psychobilly-perf` and
`psb-plugin-info` start on stock runner images.

## 15. `psb::Engine` (~3.5 MB) must not live on the stack of CLI entry points

Root cause of the windows-2025 `psychobilly-render.exe` "exit 127 / 0xC00000FD"
failure: `Engine` (8 slots x 4 Karplus-Strong strings of fixed-capacity storage)
is ~3.5 MB, and the CLI tools held it as a local in `main`. Linux/macOS default
to an 8 MB main stack and tolerate this; the Windows 1 MB default stack overflows
in the MSVC prologue (stack probing), before the first statement of `main` runs
- which is why no diagnostic output ever appeared. A cl.exe flag/arch matrix
(/O2 vs /Od, /MD vs /MT, x64 vs x86) all crashed identically, ruling out
codegen. Fix: CLI tools heap-allocate the engine (`std::make_unique`). The VST3
processor holds `Engine` as a member of the heap-allocated plugin instance,
which is unaffected. Diagnostics note: a `main-enter` stderr marker remains in
`psychobilly-render` for future pre-main vs in-main triage.

## 16. `--input /dev/stdin` is honoured as stdin on all OSes

The frozen voice-lifecycle adapter feeds documents via `--input /dev/stdin`.
`/dev/stdin` does not exist on Windows, so the renderer maps `/dev/stdin` (and
`-`) to std::cin. Frozen stub untouched; behaviour on Unix unchanged (reading
the named stream via cin is equivalent for pipe-fed input).

## 17. CI stages extensionless binary aliases for the frozen stub

stubs/psb_contract.py resolves `psychobilly-render`/`psychobilly-perf` by
extensionless name. Windows produces `.exe`; MSYS path magic equates `foo` and
`foo.exe`, so CI stages both names with Python (exact Win32 names) in
build/psb-bin and points PSB_BUILD_DIR at it.

## 18. G-004 round 1 invalidated — reference clips decoded as white noise; answer key on the listener sheet

The blind-listening bundle generator (stubs/psb_contract.py, unmarked adapter)
had two defects. First, `_wav_clip` decoded every WAV as 24-bit byte triples;
the VSCO 2 CE references are 16-bit PCM, so every reference clip was
byte-misaligned noise (verified: correlation ~0.00 with the source recordings;
the round-1 listener uniformly described that side as "white noise" and
answered 0/12 — the exact complement of the sealed sides, since the only
non-noise side was picked every time). Second, ATTRIBUTION.md — part of the
listener-facing bundle — disclosed `reference_on=A/B` per pair in plaintext,
voiding the blinding (S-100 requires the sheet to disclose nothing until
answers are recorded).

Fix (red -> fix, no hash-frozen file touched): `_wav_clip` now dispatches on
`wave.getsampwidth()` (16/24/32-bit) and downmixes channels; the listener
sheet now lists only the pair label. Round-1 evidence branch retained as
invalidated history; round 2 pushed as evidence/G-004-round-2 with all 12
reference clips verified >= 0.999 correlated against the sources. Note:
running the frozen T-050 locally regenerates build/listening/round-1 with the
corrected decoder, so the local round-1 directory no longer matches the pushed
(invalidated) round-1 branch — the pushed branch is the historical record.

## 19. G-004 iterate — ordinary-pluck timbre retune (round 3 candidate)

Round-2 listening: 12/12 reference identification + "sounded like piano".
Root cause measured: candidate centroid was ~440 Hz for every note (fixed
525 Hz radiation filter erased pitch-scaled spectral bloom) with t60 ~2.4 s
(piano-like ring) and a softened excitation transient. Retuned inside
StringInstance (mix path, D-021 control mappings and all frozen contracts
untouched): radiation cutoff now pitch-scaled (clamp(300+6*f0, 350, 2800) *
(0.75+0.5*tension)); t60 base 0.35 -> 0.20 (still monotonic in sustain);
excitation one-pole 0.30 -> 0.42 (brighter pizz transient). Candidate centroid
now scales with pitch (F#0 516 / A1 564 / G#2 687 Hz). Frozen suite 20/20
green, RTF 0.04 <= 0.25. Latent quirk observed (not in scope, unchanged):
a note_on with no matching note_off within the render produces silence.
