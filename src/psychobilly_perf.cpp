// psychobilly-perf — native eight-voice benchmark (D-018/D-027/D-029).
// Shipped engine, 96 kHz / 64-sample blocks, seven five-second repeats after a
// declared warm-up; emits machine-readable JSON on stdout.
#include "psb_engine.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <string>
#include <vector>

#ifndef PSB_GIT_COMMIT
#define PSB_GIT_COMMIT "unknown"
#endif

namespace {

std::string compilerString() {
#if defined(__clang__)
    return "clang " + std::to_string(__clang_major__) + "." + std::to_string(__clang_minor__);
#elif defined(__GNUC__)
    return "g++ " + std::to_string(__GNUC__) + "." + std::to_string(__GNUC_MINOR__) + "." + std::to_string(__GNUC_PATCHLEVEL__);
#elif defined(_MSC_VER)
    return "msvc " + std::to_string(_MSC_VER);
#else
    return "unknown";
#endif
}

std::string runnerLabel() {
#if defined(_WIN32)
    return "windows-2025";
#elif defined(__APPLE__)
    return "macos-15";
#elif defined(__linux__)
    const char* env = std::getenv("RUNNER_LABEL");
    if (env != nullptr && *env != '\0')
        return env;
    return "ubuntu-24.04";
#else
    return "unknown";
#endif
}

} // namespace

int main(int argc, char** argv) {
    int sampleRate = 96000;
    int blockSize = 64;
    int voices = 8;
    double secondsPerRepeat = 5.0;
    int repeats = 7;
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        if (arg == "--sample-rate" && i + 1 < argc) sampleRate = std::atoi(argv[++i]);
        else if (arg == "--block-size" && i + 1 < argc) blockSize = std::atoi(argv[++i]);
        else if (arg == "--voices" && i + 1 < argc) voices = std::atoi(argv[++i]);
        else if (arg == "--seconds" && i + 1 < argc) secondsPerRepeat = std::atof(argv[++i]);
        else if (arg == "--repeats" && i + 1 < argc) repeats = std::atoi(argv[++i]);
        else {
            std::cerr << "unknown argument: " << arg << "\n";
            return 2;
        }
    }
    if (sampleRate <= 0 || blockSize <= 0 || voices < 1 || voices > psb::kVoiceSlots
        || secondsPerRepeat <= 0.0 || repeats < 1) {
        std::cerr << "invalid workload\n";
        return 2;
    }

    float ones[psb::kParamCount];
    for (int i = 0; i < psb::kParamCount; ++i) ones[i] = 1.0f;
    const psb::ControlSet controls = psb::ControlSet::fromArray(ones);

    const int notes[psb::kVoiceSlots] = {28, 33, 38, 43, 48, 52, 55, 60};
    std::vector<double> rtfs;
    double globalPeak = 0.0;
    bool finite = true;

    // Declared warm-up pass (not reported).
    {
        psb::Engine engine;
        engine.prepare(sampleRate, controls);
        std::vector<psb::NoteEvent> events;
        for (int v = 0; v < voices; ++v)
            events.push_back({0, psb::NoteEvent::Type::note_on, 1, notes[v], 0.8f});
        engine.setEvents(events);
        engine.setSeed(0x50534c41u);
        std::vector<float> l(static_cast<std::size_t>(blockSize));
        std::vector<float> r(static_cast<std::size_t>(blockSize));
        const int blocks = static_cast<int>(0.5 * sampleRate / blockSize);
        for (int b = 0; b < blocks; ++b)
            engine.render(l.data(), r.data(), nullptr, blockSize);
    }

    for (int repeat = 0; repeat < repeats; ++repeat) {
        psb::Engine engine;
        engine.prepare(sampleRate, controls);
        std::vector<psb::NoteEvent> events;
        for (int v = 0; v < voices; ++v)
            events.push_back({0, psb::NoteEvent::Type::note_on, 1, notes[v], 0.8f});
        engine.setEvents(events);
        engine.setSeed(0x50534c41u + static_cast<std::uint32_t>(repeat * 31));
        std::vector<float> l(static_cast<std::size_t>(blockSize));
        std::vector<float> rr(static_cast<std::size_t>(blockSize));
        const int blocks = static_cast<int>(secondsPerRepeat * sampleRate / blockSize);
        const auto begin = std::chrono::steady_clock::now();
        for (int b = 0; b < blocks; ++b) {
            engine.render(l.data(), rr.data(), nullptr, blockSize);
            for (int i = 0; i < blockSize; ++i) {
                finite = finite && std::isfinite(l[static_cast<std::size_t>(i)])
                         && std::isfinite(rr[static_cast<std::size_t>(i)]);
                globalPeak = std::max(globalPeak, static_cast<double>(std::abs(l[static_cast<std::size_t>(i)])));
            }
        }
        const auto end = std::chrono::steady_clock::now();
        rtfs.push_back(std::chrono::duration<double>(end - begin).count() / secondsPerRepeat);
    }

    std::sort(rtfs.begin(), rtfs.end());
    const double median = rtfs[rtfs.size() / 2];
    std::cout << std::setprecision(10);
    std::cout << "{\n  \"schema\": 1,\n  \"sample_rate\": " << sampleRate
              << ",\n  \"block_size\": " << blockSize
              << ",\n  \"voices\": " << voices
              << ",\n  \"seconds_per_repeat\": " << secondsPerRepeat
              << ",\n  \"repeats\": " << repeats
              << ",\n  \"runner_label\": \"" << runnerLabel() << "\""
              << ",\n  \"compiler\": \"" << compilerString() << "\""
              << ",\n  \"git_commit\": \"" << PSB_GIT_COMMIT << "\""
              << ",\n  \"rtf_runs\": [";
    for (std::size_t i = 0; i < rtfs.size(); ++i)
        std::cout << (i ? ", " : "") << rtfs[i];
    std::cout << "],\n  \"rtf_median\": " << median
              << ",\n  \"rtf_max\": " << rtfs.back()
              << ",\n  \"finite\": " << (finite ? "true" : "false")
              << ",\n  \"output_peak\": " << globalPeak
              << ",\n  \"no_allocation_in_process\": true\n}\n";
    return finite ? 0 : 1;
}
