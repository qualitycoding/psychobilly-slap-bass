# Psychobilly Slap Bass 0.1.0

A source-built VST3 instrument specialising in psychobilly slap double bass:
four extended digital-waveguide strings (one per voice) with pluck excitation,
bounded fingerboard collision/contact, body/radiation filtering, sympathetic
coupling across eight voices, velocity response and deterministic seeded
variation. Headless: no editor window, no standalone app, no sample playback.

Licence: AGPL-3.0-only (JUCE 9.0.5 open licence; see `LICENSE` and
`THIRD-PARTY-NOTICES.md`). Public binary release is gated separately (G-002);
this repository ships source and CI evidence only.

## Layout

- `src/` — C++20 engine (`psb_engine.h`, `psb_dsp.h`), offline renderer
  (`psychobilly_render.cpp`), native benchmark (`psychobilly_perf.cpp`),
  JUCE VST3 processor (`src/plugin/`), identity probe (`psb_plugin_info.cpp`).
- `stubs/psb_contract.py` — adapter between the frozen contract tests and the
  compiled engine.
- `tests/` — frozen contract tests (do not modify; see `tests/FROZEN_MANIFEST.sha256`).
- `demos/events/` — ten reproducible D-024 event documents.
- `scripts/` — freeze verification, repository audit, artifact verification,
  blind-pair construction and scoring.

## Build

Requirements: CMake ≥ 3.22, a C++20 compiler, Python 3.12 with the packages in
`requirements.txt` (install with `pip --target .tools/python` and set
`PYTHONPATH` on no-symlink mounts).

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DPSB_BUILD_VST3=ON -DPSB_BUILD_DEMOS=ON
cmake --build build --config Release --parallel 2
ctest --test-dir build -C Release --output-on-failure
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

JUCE 9.0.5 is fetched by CMake FetchContent at the pinned tag commit
`d60b7a78030661574a615b586d9325ba7a7fa7dd`. VST3 is the only plug-in format.
Set `-DPSB_BUILD_VST3=OFF` to build only the headless tools without fetching JUCE.

## Use

The plug-in exposes exactly eight host parameters (`pluck_slap`,
`slap_brightness`, `body_resonance`, `sustain`, `string_tension`,
`attack_noise`, `mechanical_noise`, `output_level`), omni MIDI in, stereo out,
±2-semitone pitch bend (centre 8192), eight-voice polyphony with
quietest-then-oldest stealing and 10 ms retrigger crossfade. The audio thread
never allocates, locks, or touches files or the network.

Offline rendering:

```sh
psychobilly-render --input events.jsonl --output demo.wav --metadata demo.json
```

Exit codes: 0 success, 2 invalid input (fails closed), 3 I/O error.
Renders are deterministic for a fixed seed in a pinned environment; the
shipped path has no normalisation (`normalisation_applied: false` in the
provenance record).
