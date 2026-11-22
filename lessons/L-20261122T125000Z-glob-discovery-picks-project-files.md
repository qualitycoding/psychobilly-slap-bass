---
id: L-20261122T125000Z-glob-discovery-picks-project-files
title: Globbing a build tree for the test executable matched the .vcxproj and failed with WinError 193
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Medium
tags: [tech:python, tech:github-actions, tech:msvc, phase:verification, kind:tooling]
recorded_by: implementer
run: impl-20261122T000000Z-psychobilly-slap-bass
recorded_at: 2026-11-22T12:50:00Z
---
## Trigger
Locating the built test binary with `next(p for p in Path("build").rglob("psychobilly-render*") if p.is_file() ...)` on a Visual Studio generator build.
## What went wrong
rglob order put `build/psychobilly-render.vcxproj` first (also matching: `.vcxproj.filters`, `.exe.recipe`, `.lastbuildstate`, `.lib`/`.exp` next to the real `.exe`). The script tried to execute the project file: `OSError: [WinError 193] %1 is not a valid Win32 application`. Exclusion lists kept missing the next project artifact.
## Correction
Filter by what the artifact IS, not by what it is not: keep only suffix in (".exe", "") — executables on Windows have .exe, on POSIX no suffix. Print the candidate list for diagnosis.
## Prevention rule
When a CI step discovers built binaries by glob, assert the discovered path is executable-shaped (suffix allowlist) and print candidates on mismatch. rglob order is filesystem-dependent: never let `next()` over an unfiltered glob choose what to run.
## Detection check
Windows performance step runs `psychobilly-render bench` and writes performance.json.
## Evidence
psychobilly-slap-bass CI runs 45015418249, 45017555022 (WinError 193); fixed by afa515e.
