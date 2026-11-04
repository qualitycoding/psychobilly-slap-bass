# Implementation environment

All versions and immutable identifiers below were existence-checked during planning. Setup evidence is `research/spikes/toolchain/setup-output.json`; action pins and validator archive hashes are in the adjacent JSON records. The implementer must print the runner image version, OS/architecture, compiler, CMake, Python and dependency versions in every CI job. A runner label is not a toolchain pin.

## Repository and language

- Implementation branch: `impl-<run_id>` from the generation branch; never implement on the generation branch.
- C++20; JUCE `9.0.5`, commit `d60b7a78030661574a615b586d9325ba7a7fa7dd`, fetched by full commit in CMake `FetchContent` with `GIT_SHALLOW FALSE`.
- VST3 only; JUCE's SPDX inventory records VST3 SDK 3.8.0 under MIT. Preserve JUCE, VST3 and other third-party notices.
- CMake main `3.31.6`; lower-bound job `3.22.4`; project minimum `3.22`.
- Python `3.12.x`; NumPy `2.2.6`, SciPy `1.15.3`, SoundFile `0.13.1`, pip-audit `2.10.0`.
- Python package index: `https://pypi.org/simple` (the configured mirror was unavailable; D-010).
- S-010 creates `requirements.txt` containing exactly:
  ```text
  numpy==2.2.6
  scipy==1.15.3
  soundfile==0.13.1
  pip-audit==2.10.0
  ```
  Installation resolves and records transitive versions in `environment-lock.txt`; the lock's SHA-256 enters every render provenance record. Any later version difference is a deviation, not a silent update.

## Local setup

Run from the implementation checkout. Use a Python virtual environment where the host supports it; in a mount that forbids symlinks, use `python3 -m pip --target .tools/python` and set `PYTHONPATH` instead. Never execute binaries directly from a no-exec mount: copy the complete CMake package, including its data directory, to an executable local location.

```sh
python3 --version
python3 -m pip install --index-url https://pypi.org/simple -r requirements.txt
cmake --version
git rev-parse HEAD
sha256sum -c tests/FROZEN_MANIFEST.sha256
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

The unit-test command must initially fail only through the planning stubs. After implementation it must pass; the frozen files themselves remain unchanged. On Windows use `py -3.12`, `python -m pip`, `python -m unittest`, and the repository's `scripts/verify_freeze.py` rather than `sha256sum`.

## Native build tools

- `ubuntu-24.04`: runner-provided GCC and Ninja; install only the JUCE Linux development packages named by the pinned JUCE CMake documentation. Record the exact apt package versions in the job log and lock artifact.
- `windows-2025`: runner-provided Visual Studio 2022/MSVC x64 and CMake; configure with `-A x64`. S-000 verifies that the image identifies a supported Windows 11 build.
- `macos-15`: Apple Silicon, runner-provided Xcode/Clang; set `CMAKE_OSX_DEPLOYMENT_TARGET=12.0` and do not request AU.
- The separate oldest-toolchain Linux job replaces only CMake with `3.22.4`; all other pins remain identical.

Canonical configure/build/test commands (the CI scripts select the platform-specific generator and plug-in path):

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DPSB_BUILD_VST3=ON -DPSB_BUILD_DEMOS=ON
cmake --build build --config Release --parallel 2
ctest --test-dir build -C Release --output-on-failure
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

These commands are backed by the CMake configure/build/version spikes and C-014–C-018. The project options are new public build interfaces to implement in S-010; unsupported generators or missing SDK packages stop S-000 with `BLOCKED.md`.

## pluginval 1.0.4

Download only the platform archive recorded in `research/spikes/toolchain/pluginval-archives.json`, then assert its byte count and SHA-256 before extraction:

| Platform | Bytes | SHA-256 |
|---|---:|---|
| Linux | 5911681 | `c01c49d8063965c4c2dea8324468336768f5c9139e0b1caebde14c2400b55352` |
| Windows | 2408590 | `c08e61ce3b96db41636f8ec7e76f4c7e2c13ebdac7fa1b5a1f52b4f32ec715ab` |
| macOS | 9202795 | `3c4c533bda0c5059eea3ddaea752d757ee2025041f0f47e6bcb0e87f6082b29f` |

Run `pluginval --version` and require `1.0.4`. Primary validation command, with the platform path substituted:

```sh
pluginval --validate <PsychobillySlapBass.vst3> --strictness-level 7 --sample-rates 44100,48000,88200,96000 --block-sizes 64,128,256,512,1024 --random-seed 5265473 --timeout-ms 120000 --repeat 3 --randomise --output-dir artifacts/pluginval --output-filename pluginval-primary --verbose
```

Do not pass `--skip-gui-tests` or `--disabled-tests`. The timeout is a liveness bound, not permission to ignore a crash. S-080's log parser must assert completion, zero failures, all expected test families, the requested rates/block sizes/repeats and absence of skips/disabled tests; exit code zero alone fails closed.

Only if the exact known post-release `PluginInfoTest` race is reproduced with matching evidence may D-011's exact fixed pluginval source commit be built and used as a second validator. The stable run and failure log remain artifacts; a different failure never qualifies for fallback.

## GitHub Actions pins

Use full commit SHAs, not moving tags:

```text
actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1                 # v7.0.1
actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0          # v7.1.0
actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9       # v7.0.2
actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333     # v8.0.2
actions/cache@55cc8345863c7cc4c66a329aec7e433d2d1c52a9                 # v6.1.0
```

Every job has `contents: read` unless a narrower permission is possible; no job receives the planning PAT. Cache keys include the lock hash, runner OS/architecture and dependency identity. Never cache credentials or build outputs as trusted test evidence.

## Security and evidence commands

```sh
python -m pip_audit -r requirements.txt --no-deps --disable-pip --strict --format json --output artifacts/pip-audit.json
python3 scripts/audit_repository.py --output artifacts/repository-audit.json
python3 scripts/verify_artifacts.py artifacts
```

`pip-audit` flags are verified against the pinned 2.10.0 PyPI documentation; no vulnerability may be ignored without a human-approved G-005 rescope. `audit_repository.py` is implemented in S-090 and must scan tracked content/history for credential patterns, reject network/telemetry/account code and report third-party licence notices. `verify_artifacts.py` fails for missing, empty or schema-invalid logs, WAVs, JSON or provenance.

## CI matrix and artifacts

`fail-fast: false` is mandatory. Native jobs are `ubuntu-24.04`, `windows-2025`, `macos-15`; an additional Ubuntu job uses CMake 3.22.4. D-009 waives ARM64 Linux and alternative libc because neither is a supported target. Performance runs natively on each of the three principal runners, never under emulation.

Each principal job uploads: build/configuration logs, frozen-test output, pluginval logs and coverage assertion, performance JSON, security reports, commit/environment manifest and VST3 artifact with notices. The Ubuntu demo job additionally uploads ten WAVs, ten JSON metadata files, ten event inputs and the sealed blind-pair bundle. Upload steps assert every file exists and is non-empty before `actions/upload-artifact` runs. No public release occurs here.
