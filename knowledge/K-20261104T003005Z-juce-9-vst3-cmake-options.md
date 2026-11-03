---
id: K-20261104T003005Z-juce-9-vst3-cmake-options
statement: "JUCE 9.0.5 CMake supports VST3-only plug-in declaration with IS_SYNTH and NEEDS_MIDI_INPUT, disables VST2 replacement by default with JUCE_VST3_CAN_REPLACE_VST2=0, and provides NEEDS_CURL and NEEDS_WEB_BROWSER controls."
status: current
supersedes: []
tags: [tech:juce, tech:cmake, subject:juce-cmake-api, phase:research]
applies_to_version: "9.0.5"
source: { url: "https://raw.githubusercontent.com/juce-framework/JUCE/d60b7a78030661574a615b586d9325ba7a7fa7dd/extras/Build/CMake/JUCEUtils.cmake", doi: "", title: "JUCE 9.0.5 JUCEUtils.cmake", locator: "lines 255–270, 1564–1585, 2276–2304, 2465", accessed: "2026-11-04", tier: 1 }
confidence: verified
derived_from: [C-005]
discovered_by: planner
run: 20261103T230504Z-psychobilly-slap-bass
recorded_at: 2026-11-04T00:30:05Z
---
JUCE 9.0.5 CMake supports VST3-only plug-in declaration with IS_SYNTH and NEEDS_MIDI_INPUT, disables VST2 replacement by default with JUCE_VST3_CAN_REPLACE_VST2=0, and provides NEEDS_CURL and NEEDS_WEB_BROWSER controls. Confidence is `verified` during R2; R4/R5/R6 must preserve or upgrade every load-bearing claim before freeze. This item does not claim perceptual realism or listening validation.
