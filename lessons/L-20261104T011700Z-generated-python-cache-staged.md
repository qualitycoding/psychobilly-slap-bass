---
id: L-20261104T011700Z-generated-python-cache-staged
title: Exclude generated Python bytecode from research evidence commits
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Low
tags: [tech:python, tech:git, phase:research, kind:process]
recorded_by: planner
run: 20261103T230504Z-psychobilly-slap-bass
recorded_at: 2026-11-04T01:17:00Z
---
## Trigger
A broad `git add research` after importing a spike module stages `__pycache__` bytecode alongside source and JSON evidence.
## What went wrong
The R6 commit included a generated, platform-specific `.pyc` file that is not a reproducible source or output artifact.
## Correction
Removed the generated cache from version control and added a repository ignore rule for Python bytecode/cache directories.
## Prevention rule
Before a broad research staging operation, inspect the staged file list and ignore `__pycache__/`, `*.py[cod]` and local build outputs; commit only source, deterministic outputs and intended evidence.
## Detection check
`git ls-files` returns no `.pyc` or `__pycache__` paths and `git status --short` shows no generated cache as an intended addition.
## Evidence
R6 initial local commit `9189d1f`; corrected immediately before the research checkpoint was considered complete.
