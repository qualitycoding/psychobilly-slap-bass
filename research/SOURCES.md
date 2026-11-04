# Sources and verification notes

Accessed 2026-11-04 unless stated otherwise. Claim IDs provide the machine-readable register in `research/claims.json`.

## Pinned engineering sources

1. **JUCE 9.0.5 release API** — https://api.github.com/repos/juce-framework/JUCE/releases/latest — stable release metadata and tag; local clone resolved tag commit `d60b7a78030661574a615b586d9325ba7a7fa7dd`. C-001.
2. **JUCE 9.0.5 `LICENSE.md`** — https://raw.githubusercontent.com/juce-framework/JUCE/d60b7a78030661574a615b586d9325ba7a7fa7dd/LICENSE.md — read at the pinned commit; AGPLv3/commercial dual licence. C-002.
3. **JUCE 9.0.5 `CMakeLists.txt`** — https://raw.githubusercontent.com/juce-framework/JUCE/d60b7a78030661574a615b586d9325ba7a7fa7dd/CMakeLists.txt — line 33, `cmake_minimum_required(VERSION 3.22)`. C-003.
4. **JUCE 9.0.5 module tree** — https://github.com/juce-framework/JUCE/tree/d60b7a78030661574a615b586d9325ba7a7fa7dd/modules — local inspection found `modules/juce_audio_processors_headless/processors/juce_AudioProcessor.h` and `modules/juce_audio_processors/utilities/juce_AudioProcessorValueTreeState.h`. C-004.
5. **JUCE 9.0.5 `extras/Build/CMake/JUCEUtils.cmake`** — pinned raw URL under the same commit; lines 255–270, 1564–1585, 2276–2304 and 2465 verify dependency controls, plug-in target setup, synth/MIDI arguments and VST2 replacement default. C-005.
6. **JUCE 9.0.5 Linux dependencies** — https://raw.githubusercontent.com/juce-framework/JUCE/d60b7a78030661574a615b586d9325ba7a7fa7dd/docs/Linux%20Dependencies.md — module-by-module package list and disabling flags; used for environment design, with Ubuntu 24.04 CI verification still required.
7. **pluginval latest release API** — https://api.github.com/repos/Tracktion/pluginval/releases/latest — latest stable is v1.0.4; local tag clone resolved `ed19c2c16b57a6d94db391bea3ef4a80b769d5bf`. C-006.
8. **pluginval v1.0.4 `README.md`, `docs/Adding pluginval to CI.md`, and `Source/CommandLine.cpp`** — https://github.com/Tracktion/pluginval/tree/ed19c2c16b57a6d94db391bea3ef4a80b769d5bf — headless invocation and exact option names verified from the pinned source. C-006.
9. **GitHub-hosted runners reference** — https://docs.github.com/en/actions/reference/runners/github-hosted-runners — current versioned labels and architectures. C-007.
10. **GitHub runner-images issue 14748** — https://github.com/actions/runner-images/issues/14748 — official migration notice; independently confirms why `ubuntu-latest` is unsuitable and `ubuntu-24.04` must be explicit. C-007.

## Acoustics literature

11. **Karjalainen, Välimäki and Tolonen (1998), “Plucked-string models: from the Karplus–Strong algorithm to digital waveguides and beyond”** — DOI `10.2307/3681155`; Computer Music Journal 22(3), 17–32. Aalto record: https://research.aalto.fi/en/publications/plucked-string-models-from-the-karplus-strong-algorithm-to-digita/ — author page: http://users.spa.aalto.fi/vpv/publications/cmj98.htm — abstract and aims verify efficient plucked-string, plucking-style and sympathetic-string extensions. C-008.
12. **Evangelista and Eckerholm (2010), “Player–Instrument Interaction Models for Digital Waveguide Synthesis of Guitar: Touch and Collisions”** — DOI `10.1109/TASL.2009.2038822`; IEEE TASLP 18(4), 822–832. Post-print: https://www.diva-portal.org/smash/get/diva2:316228/FULLTEXT01.pdf — Sections III and IV-C, equations (26)–(39), describe collision detection/scattering and slap playing. C-009.
13. **Rank and Kubin (1997), “A waveguide model for slapbass synthesis”** — DOI `10.1109/ICASSP.1997.599670`; ICASSP 1997, volume 1, 443–446. Bibliographic cross-check through the 2010 paper’s reference [9] and https://dl.acm.org/doi/10.5555/1820680.1820691. C-009. The earlier method itself is not selected blindly because the 2010 paper reports discontinuity problems.
14. **Stokes, “Rockabilly Bass”** — https://www.donovanstokes.com/wp-content/uploads/April-08-ISB-Rockabilly-Bass.pdf — “Amplification/Recording for Slap-Style playing” distinguishes fingerboard slap and F-hole pitch sources. Tier 4 practitioner source; C-010 is now explicitly non-load-bearing and does not establish a general acoustic requirement.

## Reference recordings

15. **VSCO 2 CE pinned repository** — https://github.com/sgossner/VSCO-2-CE/tree/440300901dfe9275fd84e0b7763af1f8443ae62e — CC0 licence and `Strings/Solo Contrabass/Pizz` directory. Exact selected URLs, byte counts and SHA-256 values are committed in `research/reference-candidates/manifest.json`. C-011/C-012.
16. **Local exploratory reference analysis** — `research/reference-candidates/analysis.json` — deterministic method and all seven results committed; second-harmonic spectral-max observation is C-013. It is not a perceptual evaluation and not a source of realism thresholds.
17. **Local action pin verification** — `research/spikes/toolchain/action-pins.json` — release tags and full commits for checkout, setup-python, upload-artifact, download-artifact and cache. C-014.
18. **Local pluginval archive verification** — `research/spikes/toolchain/pluginval-archives.json` — exact v1.0.4 release URLs, byte counts and SHA-256 values for all three desktop archives. C-015.
19. **Local toolchain setup evidence** — `research/spikes/toolchain/setup-output.json` — successful public-PyPI installation, staged CMake 3.31.6/3.22.4 execution and pluginval 1.0.4 exit-code checks. C-016.
20. **JUCE 9.0.5 `AudioProcessor.h`** — pinned source under commit `d60b7a78030661574a615b586d9325ba7a7fa7dd` — bus constructors, processing overloads, editor contract, bus-layout callback and XML state helpers. C-017.
21. **JUCE 9.0.5 `AudioProcessorValueTreeState.h/.cpp`** — pinned source under the same commit — atomic parameter access and explicit non-realtime locking semantics for state copy/replacement. C-018.
22. **pluginval issue #149 and fix commit** — https://github.com/Tracktion/pluginval/issues/149 and https://github.com/Tracktion/pluginval/commit/fea38e7ed6a5e35b2e9122bb5685fc3dc8fe9a01 — post-v1.0.4 `PluginInfoTest` message-thread race and exact maintainer fix; informs D-011 and R5 adversarial analysis.
