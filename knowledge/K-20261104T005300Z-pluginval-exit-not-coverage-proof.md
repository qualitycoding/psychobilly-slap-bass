---
id: K-20261104T005300Z-pluginval-exit-not-coverage-proof
statement: "pluginval v1.0.4 can skip tests by strictness, GUI options or a disabled-test list, so exit zero alone does not prove the frozen validation coverage ran."
status: current
supersedes: []
tags: [tech:juce, subject:pluginval, subject:validation-coverage, phase:research]
applies_to_version: "v1.0.4"
source: { url: "https://raw.githubusercontent.com/Tracktion/pluginval/ed19c2c16b57a6d94db391bea3ef4a80b769d5bf/Source/PluginTests.cpp", doi: "", title: "pluginval v1.0.4 PluginTests.cpp", locator: "test-loop strictness/GUI/disabled continue conditions", accessed: "2026-11-04", tier: 1 }
confidence: verified
derived_from: [C-022]
discovered_by: planner
run: 20261103T230504Z-psychobilly-slap-bass
recorded_at: 2026-11-04T00:53:00Z
---
CI asserts the log's product identity, options, requested test matrix and absence of failure/disabled markers in addition to the process exit code. Independent host and DSP tests remain required.
