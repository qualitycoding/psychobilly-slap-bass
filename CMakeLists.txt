# Psychobilly Slap Bass — build definition (AGPL-3.0-only).
# Pure C++20 headless engine and tools build everywhere; the VST3 target
# additionally requires the pinned JUCE 9.0.5 FetchContent checkout.
cmake_minimum_required(VERSION 3.22)
project(PsychobillySlapBass VERSION 0.1.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(PSB_BUILD_VST3 "Build the VST3 plug-in (requires JUCE)" ON)
option(PSB_BUILD_DEMOS "Build the headless renderer/benchmark tools" ON)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

add_library(psb_engine STATIC src/psb/engine.cpp)
target_include_directories(psb_engine PUBLIC src)
# The VST3 module links psb_engine into a shared object; static archives must
# be PIC or the Linux link fails with R_X86_64_PC32 relocations.
set_target_properties(psb_engine PROPERTIES POSITION_INDEPENDENT_CODE ON)
if(MSVC)
  target_compile_options(psb_engine PRIVATE /fp:precise /W4)
else()
  target_compile_options(psb_engine PRIVATE -O3 -ffp-contract=off -Wall -Wextra)
endif()

if(PSB_BUILD_DEMOS)
  add_executable(psychobilly-render src/psb/main.cpp)
  target_link_libraries(psychobilly-render PRIVATE psb_engine)
  enable_testing()
  add_test(NAME renderer-smoke COMMAND psychobilly-render version)
endif()

if(PSB_BUILD_VST3)
  include(FetchContent)
  # JUCE 9.0.5 pinned by full commit (A-005/ENVIRONMENT.md); shallow clone of a
  # full-commit pin is not possible, so GIT_SHALLOW stays FALSE.
  FetchContent_Declare(
    JUCE
    GIT_REPOSITORY https://github.com/juce-framework/JUCE.git
    GIT_TAG d60b7a78030661574a615b586d9325ba7a7fa7dd
    GIT_SHALLOW FALSE
  )
  FetchContent_MakeAvailable(JUCE)

  juce_add_plugin(psb_vst3
    COMPANY_NAME "QualityCoding"
    COMPANY_WEBSITE "https://github.com/qualitycoding"
    COMPANY_EMAIL "nobody@example.invalid"
    PLUGIN_MANUFACTURER_CODE Qc01
    PLUGIN_CODE Psb1
    FORMATS VST3
    PRODUCT_NAME "Psychobilly Slap Bass"
    IS_SYNTH TRUE
    NEEDS_MIDI_INPUT TRUE
    NEEDS_MIDI_OUTPUT FALSE
    IS_MIDI_EFFECT FALSE
    EDITOR_WANTS_KEYBOARD_FOCUS FALSE
    COPY_PLUGIN_AFTER_BUILD FALSE
  )

  target_sources(psb_vst3 PRIVATE src/plugin/PluginProcessor.cpp)
  target_compile_definitions(psb_vst3 PRIVATE
    JUCE_VST3_CAN_REPLACE_VST2=0
    JUCE_WEB_BROWSER=0
    JUCE_USE_CURL=0
    JUCE_DISPLAY_SPLASH_SCREEN=0
    PSB_VERSION="0.1.0"
  )
  target_link_libraries(psb_vst3 PRIVATE
    juce::juce_audio_processors
    juce::juce_audio_processors_headless
    juce::juce_audio_utils
    psb_engine
    juce::juce_recommended_config_flags
    juce::juce_recommended_lto_flags
  )
endif()
