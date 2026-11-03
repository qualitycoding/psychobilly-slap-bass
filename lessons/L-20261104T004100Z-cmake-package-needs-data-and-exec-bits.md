---
id: L-20261104T004100Z-cmake-package-needs-data-and-exec-bits
title: Stage the complete CMake package when a mount cannot execute binaries
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Medium
tags: [tech:cmake, tech:python, phase:research, kind:environment]
recorded_by: planner
run: 20261103T230504Z-psychobilly-slap-bass
recorded_at: 2026-11-04T00:41:00Z
---
## Trigger
A Python-provided CMake binary is installed on a mount that forbids executable files, or only its `bin` directory is copied to executable local storage.
## What went wrong
Invoking the mounted binary raised `PermissionError`; copying only `bin` avoided that error but caused `Could not find CMAKE_ROOT` because CMake's adjacent data files were missing. The oldest package also did not provide the assumed `python -m cmake` entry point.
## Correction
Copied the complete `cmake/data` directory for each pinned package to local storage, restored executable bits under `bin`, and invoked `<staged>/bin/cmake --version` directly.
## Prevention rule
When restaging Python-provided CMake from a no-exec mount, copy the complete `cmake/data` tree, restore executable bits only in its `bin` directory, and invoke the staged binary directly rather than relying on a module entry point.
## Detection check
Both staged binaries print their exact expected versions and exit zero without `CMAKE_ROOT` errors.
## Evidence
`research/spikes/toolchain/setup-output.json` records successful CMake 3.31.6 and 3.22.4 version checks.
