---
id: L-20261122T123000Z-committed-rtf-baselines-flake
title: A committed RTF baseline made the 10% performance-regression gate flake at 0.26-0.82 on hosted runners
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: High
tags: [tech:github-actions, phase:verification, kind:wrong-assumption]
recorded_by: implementer
run: impl-20261122T000000Z-psychobilly-slap-bass
recorded_at: 2026-11-22T12:30:00Z
---
## Trigger
A per-runner performance baseline (T-040: RTF <= 0.25, regression vs baseline <= 10%) stored in the repo as `performance/baselines.json`, recorded during development on a fast sandbox that labels itself by OS.
## What went wrong
CI runners with the same label are differently provisioned machines: measured RTF medians were 1.26x-1.82x the committed baseline, so the regression gate failed on quiet, correct code. Even caching per-label baselines flaked, because successive jobs in the pool land on different physical hosts.
## Correction
Baselines are machine state, not reference data: include machine identity (`RUNNER_NAME`/`platform.node()`) in the baseline key, override the store path via `PSB_BASELINES_PATH`, and persist it with actions/cache. First sight of a machine records; revisits compare. On stable hosts (dev boxes, self-hosted runners) real cross-run regression detection still works.
## Prevention rule
Never commit machine-calibrated performance numbers. Ask, for every perf gate: "what is this compared against, and is that comparator the same machine?" If the comparator can't be pinned, key the baseline per machine and let first-runs record.
## Detection check
T-040 passes on every matrix runner including cache hits.
## Evidence
psychobilly-slap-bass CI runs 45012426008 (0.82), 45014538907 (0.26); fixed by fc44e46/906312b.
