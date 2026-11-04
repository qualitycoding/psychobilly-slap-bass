---
id: K-20261104T005000Z-juce-905-parser-and-macos-limits
statement: "JUCE 9.0.5 adds parser nesting/entity limits and documents macOS 12.0 as its default deployment target."
status: current
supersedes: []
tags: [tech:juce, subject:malformed-state, subject:macos-deployment, phase:research]
applies_to_version: "9.0.5"
source: { url: "https://raw.githubusercontent.com/juce-framework/JUCE/d60b7a78030661574a615b586d9325ba7a7fa7dd/BREAKING_CHANGES.md", doi: "", title: "JUCE 9.0.5 BREAKING_CHANGES.md", locator: "Version 9.0.5 ValueTree/JSON/XML and macOS target entries", accessed: "2026-11-04", tier: 1 }
confidence: verified
derived_from: [C-019]
discovered_by: planner
run: 20261103T230504Z-psychobilly-slap-bass
recorded_at: 2026-11-04T00:50:00Z
---
Parser hardening does not replace a product-level byte cap and schema validation. State must be rejected before APVTS replacement when its size, root, schema, parameter IDs or values are invalid.
