---
id: K-20261104T003004Z-juce-9-headless-audioprocessor-path
statement: "In JUCE 9.0.5 the AudioProcessor interface is in juce_audio_processors_headless/processors/juce_AudioProcessor.h, while AudioProcessorValueTreeState remains in juce_audio_processors/utilities; offline DSP code must not include paths assumed from earlier JUCE layouts."
status: current
supersedes: []
tags: [tech:juce, subject:juce-headless-modules, phase:research]
applies_to_version: "9.0.5"
source: { url: "https://github.com/juce-framework/JUCE/tree/d60b7a78030661574a615b586d9325ba7a7fa7dd/modules", doi: "", title: "JUCE 9.0.5 module source tree", locator: "modules/juce_audio_processors_headless/processors/juce_AudioProcessor.h; modules/juce_audio_processors/utilities/juce_AudioProcessorValueTreeState.h", accessed: "2026-11-04", tier: 1 }
confidence: verified
derived_from: [C-004]
discovered_by: planner
run: 20261103T230504Z-psychobilly-slap-bass
recorded_at: 2026-11-04T00:30:04Z
---
In JUCE 9.0.5 the AudioProcessor interface is in juce_audio_processors_headless/processors/juce_AudioProcessor.h, while AudioProcessorValueTreeState remains in juce_audio_processors/utilities; offline DSP code must not include paths assumed from earlier JUCE layouts. Confidence is `verified` during R2; R4/R5/R6 must preserve or upgrade every load-bearing claim before freeze. This item does not claim perceptual realism or listening validation.
