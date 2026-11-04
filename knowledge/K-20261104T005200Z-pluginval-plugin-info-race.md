---
id: K-20261104T005200Z-pluginval-plugin-info-race
statement: "Stable pluginval v1.0.4 predates an exact PluginInfoTest message-thread fix recorded by issue #149 and commit fea38e7."
status: current
supersedes: []
tags: [tech:juce, subject:pluginval, subject:validator-race, phase:research]
applies_to_version: "v1.0.4; fix fea38e7ed6a5e35b2e9122bb5685fc3dc8fe9a01"
source: { url: "https://github.com/Tracktion/pluginval/commit/fea38e7ed6a5e35b2e9122bb5685fc3dc8fe9a01", doi: "", title: "PluginInfoTest message-thread fix", locator: "PluginInfoTest thread requirement and CHANGELIST diff", accessed: "2026-11-04", tier: 1 }
confidence: corroborated
derived_from: [C-021]
discovered_by: planner
run: 20261103T230504Z-psychobilly-slap-bass
recorded_at: 2026-11-04T00:52:00Z
---
Use stable v1.0.4 first. Only a reproduced matching race permits the exact fixed-commit fallback; a moving development branch and test suppression are not equivalent alternatives.
