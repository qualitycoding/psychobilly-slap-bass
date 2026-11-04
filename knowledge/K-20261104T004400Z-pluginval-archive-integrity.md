---
id: K-20261104T004400Z-pluginval-archive-integrity
statement: "All three pluginval v1.0.4 release archives have recorded byte counts and SHA-256 hashes from successful downloads."
status: current
supersedes: []
tags: [tech:juce, subject:pluginval, tech:github-actions, phase:research]
applies_to_version: "v1.0.4"
source: { url: "research/spikes/toolchain/pluginval-archives.json", doi: "", title: "Local pluginval archive verification", locator: "Linux, Windows and macOS records", accessed: "2026-11-04", tier: 1 }
confidence: verified
derived_from: [C-015]
discovered_by: planner
run: 20261103T230504Z-psychobilly-slap-bass
recorded_at: 2026-11-04T00:44:00Z
---
CI must fail before execution if a downloaded archive's byte count or SHA-256 differs from the committed record.
