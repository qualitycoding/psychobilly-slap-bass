cmake_minimum_required(VERSION 3.22)

project(PsychobillySlapBass VERSION 0.1.0 LANGUAGES C CXX)

option(PSB_BUILD_VST3 "Build the Psychobilly Slap Bass VST3 plug-in" ON)
option(PSB_BUILD_DEMOS "Build the headless renderer and performance harness" ON)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Static MSVC runtime for our CLI tools so the CI smoke probes run on stock
# runner images without a redistributable install (Git Bash maps a missing
# vcruntime DLL to the confusing exit code 127 with no output).
if(MSVC)
    set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
endif()

execute_process(
    COMMAND git rev-parse HEAD
    WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
    OUTPUT_VARIABLE PSB_GIT_COMMIT
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_QUIET)
if(NOT PSB_GIT_COMMIT)
    set(PSB_GIT_COMMIT "unknown")
endif()

add_library(psb_engine INTERFACE)
target_include_directories(psb_engine INTERFACE "${CMAKE_CURRENT_SOURCE_DIR}/src")
target_compile_features(psb_engine INTERFACE cxx_std_20)

if(PSB_BUILD_DEMOS)
    add_executable(psychobilly-render src/psychobilly_render.cpp)
    target_link_libraries(psychobilly-render PRIVATE psb_engine)
    target_compile_definitions(psychobilly-render PRIVATE
        PSB_GIT_COMMIT="${PSB_GIT_COMMIT}")

    add_executable(psychobilly-perf src/psychobilly_perf.cpp)
    target_link_libraries(psychobilly-perf PRIVATE psb_engine)
    target_compile_definitions(psychobilly-perf PRIVATE
        PSB_GIT_COMMIT="${PSB_GIT_COMMIT}")

    enable_testing()
    add_test(NAME probe COMMAND psychobilly-render --probe)
    add_test(NAME render-smoke
        COMMAND psychobilly-render
            --input "${CMAKE_CURRENT_SOURCE_DIR}/demos/events/demo-01-short-melody.jsonl"
            --output "${CMAKE_BINARY_DIR}/smoke.wav"
            --metadata "${CMAKE_BINARY_DIR}/smoke.json")
endif()

if(PSB_BUILD_VST3)
    include(FetchContent)
    FetchContent_Declare(
        JUCE
        GIT_REPOSITORY https://github.com/juce-framework/JUCE.git
        GIT_TAG d60b7a78030661574a615b586d9325ba7a7fa7dd
        GIT_SHALLOW FALSE)
    FetchContent_MakeAvailable(JUCE)

    juce_add_plugin(PsychobillySlapBass
        COMPANY_NAME "QualityCoding"
        COMPANY_WEBSITE "https://github.com/qualitycoding"
        COMPANY_EMAIL "qualitycoding@localhost"
        PLUGIN_MANUFACTURER_CODE Qual
        PLUGIN_CODE Psb1
        FORMATS VST3
        PRODUCT_NAME "Psychobilly Slap Bass"
        BUNDLE_ID com.qualitycoding.psychobillyslapbass
        IS_SYNTH TRUE
        NEEDS_MIDI_INPUT TRUE
        NEEDS_MIDI_OUTPUT FALSE
        IS_MIDI_EFFECT FALSE
        VST3_CATEGORIES Instrument
        EDITOR_WANTS_KEYBOARD_FOCUS FALSE
        COPY_PLUGIN_AFTER_BUILD FALSE)

    target_sources(PsychobillySlapBass PRIVATE
        src/plugin/PsychobillySlapBassProcessor.cpp)

    target_compile_definitions(PsychobillySlapBass PRIVATE
        JUCE_WEB_BROWSER=0
        JUCE_USE_CURL=0
        JUCE_VST3_CAN_REPLACE_VST2=0
        JUCE_DISPLAY_SPLASH_SCREEN=0
        JUCE_STRICT_REFCOUNTEDPOINTER=1
        PSB_GIT_COMMIT="${PSB_GIT_COMMIT}")

    target_link_libraries(PsychobillySlapBass PRIVATE
        juce::juce_audio_utils
        juce::juce_audio_processors
        juce::juce_gui_extra
        juce::juce_recommended_config_flags
        juce::juce_recommended_lto_flags
        juce::juce_recommended_warning_flags)

    add_executable(psb-plugin-info src/psb_plugin_info.cpp)
    target_link_libraries(psb-plugin-info PRIVATE
        PsychobillySlapBass
        juce::juce_audio_utils
        juce::juce_audio_processors
        juce::juce_gui_extra)
endif()
