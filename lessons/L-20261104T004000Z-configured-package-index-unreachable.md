---
id: L-20261104T004000Z-configured-package-index-unreachable
title: Verify the configured package index before diagnosing a package installation
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Low
tags: [tech:python, tech:cmake, phase:research, kind:environment]
recorded_by: planner
run: 20261103T230504Z-psychobilly-slap-bass
recorded_at: 2026-11-04T00:40:00Z
---
## Trigger
Pinned Python packages fail to install because the environment's configured package index does not resolve.
## What went wrong
The initial installation relied on the configured mirror without first establishing that it was reachable; the mirror `pypi.mirrors.msh.team` did not resolve.
## Correction
Retried the same pinned package set with `--index-url https://pypi.org/simple`; installation succeeded and the package versions were recorded.
## Prevention rule
When a package-index DNS or connection failure occurs, identify the configured index and switch explicitly to the verified public PyPI index without changing package pins; do not treat the failure as evidence that a package version is unavailable.
## Detection check
The pinned install command exits zero and a version report matches every requested package version.
## Evidence
`research/spikes/toolchain/setup-output.json`; no credentials or private package material involved.
