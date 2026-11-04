---
id: K-20261104T004700Z-apvts-state-not-realtime-safe
statement: "APVTS atomic parameter reads are realtime-oriented, but copyState and replaceState use locks and must stay out of processBlock."
status: current
supersedes: []
tags: [tech:juce, subject:realtime-state, phase:research]
applies_to_version: "9.0.5"
source: { url: "https://raw.githubusercontent.com/juce-framework/JUCE/d60b7a78030661574a615b586d9325ba7a7fa7dd/modules/juce_audio_processors/utilities/juce_AudioProcessorValueTreeState.h", doi: "", title: "JUCE 9.0.5 AudioProcessorValueTreeState.h", locator: "lines 340–346 and 378–404", accessed: "2026-11-04", tier: 1 }
confidence: verified
derived_from: [C-018]
discovered_by: planner
run: 20261103T230504Z-psychobilly-slap-bass
recorded_at: 2026-11-04T00:47:00Z
---
Cache raw atomic pointers during setup. State serialisation and restoration belong in host callbacks off the audio thread, with malformed-state validation before replacement.
