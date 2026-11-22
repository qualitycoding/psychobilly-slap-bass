---
id: L-20261122T124000Z-pluginval-success-marker
title: Asserting on pluginval's assumed "Test finished" string failed fully green validation runs
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Medium
tags: [tech:pluginval, tech:juce, phase:verification, kind:tooling]
recorded_by: implementer
run: impl-20261122T000000Z-psychobilly-slap-bass
recorded_at: 2026-11-22T12:40:00Z
---
## Trigger
A CI step asserting pluginval success via `"Test finished" in log or "finished" in log.lower()` after `proc.returncode == 0`.
## What went wrong
pluginval 1.0.4 never prints "Test finished" — it ends with "SUCCESS" (pass) or "FAILURE" (fail). The returncode check passed, all suites printed "Completed tests in pluginval / ...", and then the string assertion failed the step on Linux and Windows even though validation was fully green. On macOS a real failure (Infs, see L-20261122T120000Z) was hidden behind the wrong assertion message, and the per-test detail was truncated by printing only the log tail.
## Correction
Assert `proc.returncode == 0` and `"SUCCESS" in log`; print the full validator output before asserting; upload artifacts with `if: always()` so failing validation leaves its report.
## Prevention rule
Assert on a tool's documented/observed output for its exact pinned version, captured once from a real run — never on strings "it probably prints". When a validator step fails, the first question is "what did it actually print": capture everything, every time.
## Detection check
pluginval step green on all three OSes; a forced FAILURE run shows the failing suite's detail in the log and uploaded artifact.
## Evidence
psychobilly-slap-bass CI runs 45013121472, 45014538907; fixed by 1cd2456.
