# S-000 environment and access report

Result: **pass for local S-000 setup and baseline verification**. Implementation branch `impl-20261121T163454Z-psychobilly-slap-bass` was created from revised-plan commit `a83d1fe79108287cf8be1cc1009cc5f66582d363`. Repository write access was demonstrated by branch creation; no credential is stored in repository files.

Verified locally: Python 3.12.12; NumPy 2.2.6; SciPy 1.15.3; SoundFile 0.13.1; pip-audit 2.10.0; CMake 3.31.6 and 3.22.4; GCC 12.2 C++20 compile/run; Linux pluginval 1.0.4. Windows and macOS pluginval archives match the frozen byte counts and SHA-256 values as well as the Linux archive. JUCE 9.0.5's full commit and all five immutable action pins were resolved through authenticated GitHub API queries. Source documents for `ubuntu-24.04`, `windows-2025` and `macos-15` runner images were also reachable.

The original frozen manifest passed. The untouched baseline reported **20 tests / 249 errors / 249 expected NotImplementedError stub failures / zero unexpected errors**, with subprocess exit 1 and `clean_red:true`. An earlier baseline attempt failed because SoundFile was absent; that result was not counted as clean and led to the pinned environment setup.

Scope limitation: this is an ephemeral Debian x86_64 sandbox, not a declared delivery runner. No Ubuntu 24.04, Windows 11 or macOS 15 native build/test result is claimed. Those remain S-070/S-080 obligations. No VST3, CMake project, production adapter or binary has been created.

Evidence: `toolchain-verification.json`, `environment-lock.txt`, `remote-pin-verification.json`, `runner-image-verification.json`, `original-manifest.txt`, `original-red.json` and `original-red-unittest.txt`. Transport recovery is recorded in `DEVIATIONS.md`.
