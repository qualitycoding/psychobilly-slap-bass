---
id: K-20261104T004600Z-juce-host-only-processor-contract
statement: "JUCE 9.0.5 supplies the processor, bus, processBlock and XML state APIs needed for a host-parameter-only VST3 with no editor."
status: current
supersedes: []
tags: [tech:juce, subject:processor-contract, phase:research]
applies_to_version: "9.0.5"
source: { url: "https://raw.githubusercontent.com/juce-framework/JUCE/d60b7a78030661574a615b586d9325ba7a7fa7dd/modules/juce_audio_processors_headless/processors/juce_AudioProcessor.h", doi: "", title: "JUCE 9.0.5 AudioProcessor.h", locator: "lines 65–83, 221, 292, 1006–1034, 1149–1204, 1403–1415 and 1432", accessed: "2026-11-04", tier: 1 }
confidence: verified
derived_from: [C-017]
discovered_by: planner
run: 20261103T230504Z-psychobilly-slap-bass
recorded_at: 2026-11-04T00:46:00Z
---
The processor implements `hasEditor() == false` and `createEditor() == nullptr`; the CI GUI skip is therefore a statement about product scope rather than a concealed GUI defect.
