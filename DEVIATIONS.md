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
