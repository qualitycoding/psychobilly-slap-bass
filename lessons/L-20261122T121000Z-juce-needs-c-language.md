---
id: L-20261122T121000Z-juce-needs-c-language
title: JUCE's CMake requires C in project LANGUAGES even for pure-C++ plugins
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Medium
tags: [tech:juce, tech:cmake, phase:build, kind:tooling]
recorded_by: implementer
run: impl-20261122T000000Z-psychobilly-slap-bass
recorded_at: 2026-11-22T12:10:00Z
---
## Trigger
Adding JUCE via FetchContent to a project declared with `project(... LANGUAGES CXX)` (engine and CLI only, no C sources).
## What went wrong
CMake configure failed on every platform at `build/_deps/juce-src/CMakeLists.txt:40`: "A C compiler is required to build targets that depend on JUCE. Add 'C' to your project's LANGUAGES." JUCE compiles some C sources (libjpg etc.) and checks the project's language list before building juceaide.
## Correction
`project(PsychobillySlapBass VERSION 0.1.0 LANGUAGES C CXX)`.
## Prevention rule
For any CMake project that will ever pull in JUCE (or other C-implementing dependencies), declare `LANGUAGES C CXX` from the start; the headless engine phase is not proof the full build is C-free.
## Detection check
CI configure step passes on all three platforms on the first JUCE-enabled commit.
## Evidence
psychobilly-slap-bass CI runs 44949930585 (fail) -> 45011296442 (fixed by 4f4d26f).
