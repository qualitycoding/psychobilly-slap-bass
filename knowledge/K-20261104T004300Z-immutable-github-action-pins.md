---
id: K-20261104T004300Z-immutable-github-action-pins
statement: "The five CI action tags resolve to immutable commit SHAs recorded in the toolchain evidence."
status: current
supersedes: []
tags: [tech:github-actions, subject:ci-action-pins, phase:research]
applies_to_version: "checkout v7.0.1; setup-python v7.1.0; upload-artifact v7.0.2; download-artifact v8.0.2; cache v6.1.0"
source: { url: "research/spikes/toolchain/action-pins.json", doi: "", title: "Local action tag-to-commit verification", locator: "all five action records", accessed: "2026-11-04", tier: 1 }
confidence: verified
derived_from: [C-014]
discovered_by: planner
run: 20261103T230504Z-psychobilly-slap-bass
recorded_at: 2026-11-04T00:43:00Z
---
Use full commit SHAs in workflow `uses` fields and retain the human-readable tags as comments. A tag alone is not the frozen identity.
