---
id: K-20261104T004500Z-pinned-toolchain-staging
statement: "The pinned CMake/Python analysis toolchain and pluginval CLI were empirically installed or executed; CMake requires complete data-tree staging on a no-exec mount."
status: current
supersedes: []
tags: [tech:cmake, tech:python, subject:toolchain-setup, phase:research]
applies_to_version: "CMake 3.31.6/3.22.4; NumPy 2.2.6; SciPy 1.15.3; SoundFile 0.13.1; pluginval 1.0.4"
source: { url: "research/spikes/toolchain/setup-output.json", doi: "", title: "Local pinned toolchain setup evidence", locator: "main, oldest, pluginval and notes", accessed: "2026-11-04", tier: 1 }
confidence: verified
derived_from: [C-016]
discovered_by: planner
run: 20261103T230504Z-psychobilly-slap-bass
recorded_at: 2026-11-04T00:45:00Z
---
Use the public PyPI fallback without changing pins. On this sandbox, copy the complete `cmake/data` tree and invoke its staged `bin/cmake`; copying only executables is insufficient.
