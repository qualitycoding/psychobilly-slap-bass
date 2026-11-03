---
id: K-20261104T003003Z-juce-9-cmake-minimum
statement: "JUCE 9.0.5 requires CMake 3.22 or newer."
status: current
supersedes: []
tags: [tech:juce, tech:cmake, subject:juce-build, phase:research]
applies_to_version: "9.0.5"
source: { url: "https://raw.githubusercontent.com/juce-framework/JUCE/d60b7a78030661574a615b586d9325ba7a7fa7dd/CMakeLists.txt", doi: "", title: "JUCE 9.0.5 CMakeLists.txt", locator: "line 33: cmake_minimum_required(VERSION 3.22)", accessed: "2026-11-04", tier: 1 }
confidence: verified
derived_from: [C-003]
discovered_by: planner
run: 20261103T230504Z-psychobilly-slap-bass
recorded_at: 2026-11-04T00:30:03Z
---
JUCE 9.0.5 requires CMake 3.22 or newer. Confidence is `verified` during R2; R4/R5/R6 must preserve or upgrade every load-bearing claim before freeze. This item does not claim perceptual realism or listening validation.
