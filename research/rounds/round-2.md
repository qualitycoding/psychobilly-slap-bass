# R2 — Breadth research

Date: 2026-11-04. Planner: Kimi K3.1 fallback for the unavailable named tiers.

## Engineering

- Cloned JUCE `9.0.5` at `d60b7a78030661574a615b586d9325ba7a7fa7dd` and inspected its licence, root CMake file, CMake utilities, and module tree. Confirmed CMake 3.22 minimum, AGPLv3/commercial licensing, the `juce_audio_processors_headless` location of `juce_AudioProcessor.h`, and VST3/CMake switches. Claims C-002–C-005.
- Cloned pluginval `v1.0.4` at `ed19c2c16b57a6d94db391bea3ef4a80b769d5bf`. Its own `README.md` and `Source/CommandLine.cpp` verify headless validation, strictness 1–10, random seeds, repeat/randomise options, sample-rate lists and block-size lists. The release remains the latest stable release returned by GitHub on 2026-11-04. Claim C-006.
- Confirmed versioned GitHub-hosted runner labels for the three intake platforms. The matrix will use `ubuntu-24.04`, `windows-2025`, and `macos-15`, never `-latest`. Claim C-007.

## Acoustics and synthesis

- The 1998 Karjalainen–Välimäki–Tolonen paper supports extended Karplus–Strong/digital-waveguide strings and plucking/sympathetic extensions (C-008).
- Evangelista and Eckerholm (2010), Sections III and IV-C, provide explicit nonlinear string–fingerboard collision models for slapping and popping. They also identify output discontinuities in the earlier split-string Rank–Kubin method. This is architecture prior art, not evidence that a new implementation will sound realistic (C-009).
- Donovan Stokes distinguishes fingerboard/contact and F-hole/pitched output in upright slap-bass recording. This currently has only one Tier-4 source (C-010), so R4 must corroborate the architectural implication or record a residual risk.
- No implemented DSP or final realism threshold was produced in this round.

## Reference research

- Inspected VSCO 2 CE `Strings/Solo Contrabass/Pizz` at commit `440300901dfe9275fd84e0b7763af1f8443ae62e` and downloaded seven candidates covering F♯0, A1 and G♯2, multiple velocities and round robins.
- Recorded byte counts, source URLs and SHA-256 hashes in `research/reference-candidates/manifest.json`; verified 44.1 kHz, stereo, 16-bit WAV format. The repository supplies these under CC0 (C-011).
- The files are explicitly labelled pizzicato. They support ordinary pluck/body comparison only, not psychobilly slap realism (C-012).
- Exploratory analysis in `research/reference-candidates/analysis.json` found the strongest 20–300 Hz FFT bin at the second harmonic for all seven files. This is a diagnostic against using spectral maximum as pitch, not an f0 measurement or a realism threshold (C-013).
- Raw candidate WAVs were transient downloads and were removed after hashing/analysis. The implementation plan will re-fetch exact pinned URLs and assert the frozen hashes before creating evidence.

## Questions answered

Q-E01, Q-E02, Q-E03, Q-E05 and Q-E08 now have verified starting points. Q-A01–Q-A04 have architecture candidates. Q-R01 and Q-R05 have a lawful partial reference set and a demos-only slap fallback.

## Questions carried forward

1. Exact public interfaces, parameter ranges, state format and renderer event schema.
2. Architecture stability, full-range control behaviour and performance under eight voices.
3. Numeric metric thresholds derived from candidate/reference spread rather than intuition.
4. pluginval release compatibility with JUCE 9-produced VST3 binaries and headless CI behaviour.
5. Action commit pins, downloadable pluginval archive hashes and setup commands.
6. A second source for the two-source upright-slap acoustics claim.
7. Whether the demos-only slap listening design is sufficiently transparent and discriminating without a slap reference.

Round status: complete; proceed to R3 gap synthesis, then targeted depth/adversarial/empirical rounds.
