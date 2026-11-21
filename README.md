# Psychobilly Slap Bass

VST3 instrument plugin (JUCE 9.0.5, C++20) modelling a psychobilly slap
double bass: bidirectional waveguide strings with pluck/pop/slap/ghost
gestures, nonlinear fingerboard collisions, modal body and separate
pitch/slap buses. AGPL-3.0-only — see LICENSE and NOTICES.md.

## Build

Requires CMake >= 3.22 (main development pin 3.31.6), a C++20 compiler and
Python 3.12 with the pinned analysis dependencies:

```sh
python3 -m pip install -r requirements.txt
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DPSB_BUILD_VST3=ON
cmake --build build --config Release --parallel
ctest --test-dir build -C Release --output-on-failure
```

`PSB_BUILD_VST3=ON` fetches the pinned JUCE commit (9.0.5,
d60b7a78030661574a615b586d9325ba7a7fa7dd) via FetchContent. Headless
environments can build the offline renderer only with `-DPSB_BUILD_VST3=OFF`;
the VST3 target needs the platform SDK packages described by JUCE's CMake
documentation (X11 development libraries on Linux, Xcode on macOS, Visual
Studio 2022 on Windows).

The built VST3 appears under `build/Psychobilly_Slap_Bass_artefacts/`.
Parameters: pluck_slap, slap_brightness, body_resonance, sustain,
string_tension, attack_noise, mechanical_noise, output_level (all 0..1).

## Offline renderer and tests

```sh
./build/psychobilly-render version
./build/psychobilly-render render --input demos/events/demo-01-short-melody.jsonl \
    --output demo.wav --metadata demo.json
./build/psychobilly-render lifecycle
./build/psychobilly-render bench
python3 -m unittest discover -s tests -p 'test_*.py' -v   # needs the built renderer
python3 scripts/verify_freeze.py                           # Windows-safe freeze check
```

## Demos

`demos/events/` holds ten schema-2 JSONL event documents; matching 24-bit
48 kHz WAV renders and D-025 provenance JSON live in `demos/wav/` and
`demos/metadata/`. No normalisation is applied to the shipped path.

## Listening evidence

G-004 blind listening bundles are built with `scripts/make_blind_pairs.py`
(twelve sealed pairs, six references per side) and scored with
`scripts/score_blind.py`. Never commit credentials; see plan/ENVIRONMENT.md
for the pinned toolchain and CI evidence requirements.
