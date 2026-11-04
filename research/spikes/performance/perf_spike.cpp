// Planning-only eight-voice workload spike; not production plug-in code.
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <string>
#include <vector>

namespace {
constexpr int voicesCount = 8;
constexpr int sampleRate = 96000;
constexpr int blockSize = 64;
constexpr double secondsPerRepeat = 5.0;

struct Rng {
    std::uint32_t state;
    float next() {
        state ^= state << 13;
        state ^= state >> 17;
        state ^= state << 5;
        return static_cast<float>(state) / 2147483648.0f - 1.0f;
    }
};

struct Biquad {
    float b0 = 1.0f, b1 = 0.0f, b2 = 0.0f, a1 = 0.0f, a2 = 0.0f;
    float z1 = 0.0f, z2 = 0.0f;
    float process(float x) {
        const float y = b0 * x + z1;
        z1 = b1 * x - a1 * y + z2;
        z2 = b2 * x - a2 * y;
        return y;
    }
};

struct Voice {
    std::vector<float> line;
    std::size_t write = 0;
    float loopState = 0.0f;
    float previous = 0.0f;
    float f0 = 55.0f;
    Biquad body[3][2];

    void prepare(float frequency, std::uint32_t seed) {
        f0 = frequency;
        const float delay = static_cast<float>(sampleRate) / f0;
        line.assign(static_cast<std::size_t>(std::ceil(delay)) + 3, 0.0f);
        Rng rng {seed};
        for (auto& x : line)
            x = 0.12f * rng.next();
        write = 0;
        loopState = 0.0f;
        previous = 0.0f;
        for (auto& channel : body)
            for (auto& filter : channel)
                filter = Biquad {};
    }

    float process(float sympathetic) {
        const float delay = static_cast<float>(sampleRate) / f0;
        const float read = std::fmod(static_cast<float>(write) - delay + static_cast<float>(line.size()), static_cast<float>(line.size()));
        const auto i0 = static_cast<std::size_t>(read);
        const float frac = read - static_cast<float>(i0);
        const float x = (1.0f - frac) * line[i0] + frac * line[(i0 + 1) % line.size()];
        loopState += 0.475f * (x - loopState);
        const float limited = std::clamp(x, -0.08f, 0.08f);
        const float correction = -0.62f * (x - limited);
        line[write] = 0.9995f * loopState + correction + 0.015f * sympathetic;
        write = (write + 1) % line.size();
        previous = x;
        return x;
    }
};

float midiHz(int note) {
    return 440.0f * std::pow(2.0f, static_cast<float>(note - 69) / 12.0f);
}
} // namespace

int main() {
    const int notes[voicesCount] = {28, 33, 38, 43, 48, 52, 55, 60};
    std::vector<double> rtfs;
    double globalPeak = 0.0;
    bool finite = true;
    for (int repeat = 0; repeat < 7; ++repeat) {
        Voice voices[voicesCount];
        for (int v = 0; v < voicesCount; ++v)
            voices[v].prepare(midiHz(notes[v]), 0x50534c41U + static_cast<unsigned>(repeat * 31 + v));
        std::vector<float> left(blockSize), right(blockSize), latest(voicesCount);
        const int blocks = static_cast<int>(secondsPerRepeat * sampleRate / blockSize);
        const auto begin = std::chrono::steady_clock::now();
        for (int block = 0; block < blocks; ++block) {
            std::fill(left.begin(), left.end(), 0.0f);
            std::fill(right.begin(), right.end(), 0.0f);
            for (int i = 0; i < blockSize; ++i) {
                float sum = 0.0f;
                for (const auto& voice : voices)
                    sum += voice.previous;
                for (int v = 0; v < voicesCount; ++v) {
                    const float sympathetic = sum - voices[v].previous;
                    latest[v] = voices[v].process(sympathetic);
                }
                for (int v = 0; v < voicesCount; ++v) {
                    left[i] += 0.018f * latest[v];
                    right[i] += 0.018f * (0.98f * latest[v] + 0.02f * voices[v].previous);
                }
            }
            for (int i = 0; i < blockSize; ++i) {
                finite = finite && std::isfinite(left[i]) && std::isfinite(right[i]);
                globalPeak = std::max(globalPeak, static_cast<double>(std::max(std::abs(left[i]), std::abs(right[i]))));
            }
        }
        const auto end = std::chrono::steady_clock::now();
        const double elapsed = std::chrono::duration<double>(end - begin).count();
        rtfs.push_back(elapsed / secondsPerRepeat);
    }
    std::sort(rtfs.begin(), rtfs.end());
    const double mean = std::accumulate(rtfs.begin(), rtfs.end(), 0.0) / rtfs.size();
    double variance = 0.0;
    for (double x : rtfs)
        variance += (x - mean) * (x - mean);
    const double cv = std::sqrt(variance / rtfs.size()) / mean;
    std::cout << std::setprecision(10)
              << "{\n  \"schema\": 1,\n"
              << "  \"sample_rate\": " << sampleRate << ",\n"
              << "  \"block_size\": " << blockSize << ",\n"
              << "  \"voices\": " << voicesCount << ",\n"
              << "  \"seconds_per_repeat\": " << secondsPerRepeat << ",\n"
              << "  \"repeats\": 7,\n"
              << "  \"compiler\": \"g++ 12.2.0 -std=c++17 -O3 -DNDEBUG\",\n"
              << "  \"rtf_runs\": [";
    for (std::size_t i = 0; i < rtfs.size(); ++i)
        std::cout << (i ? ", " : "") << rtfs[i];
    const double proposedLimit = std::min(0.80, std::max(0.25, rtfs.back() * 4.0));
    const double regressionAllowance = std::max(0.10, 3.0 * cv);
    std::cout << "],\n"
              << "  \"rtf_min\": " << rtfs.front() << ",\n"
              << "  \"rtf_median\": " << rtfs[rtfs.size() / 2] << ",\n"
              << "  \"rtf_max\": " << rtfs.back() << ",\n"
              << "  \"rtf_coefficient_of_variation\": " << cv << ",\n"
              << "  \"finite\": " << (finite ? "true" : "false") << ",\n"
              << "  \"output_peak\": " << globalPeak << ",\n"
              << "  \"proposed_absolute_rtf_limit_per_runner\": " << proposedLimit << ",\n"
              << "  \"proposed_baseline_regression_allowance\": " << regressionAllowance << ",\n"
              << "  \"scope\": \"Linux sandbox workload evidence only; native CI must establish each runner baseline. No realtime guarantee or listening claim.\"\n"
              << "}\n";
    return finite && rtfs.back() < 1.0 ? 0 : 1;
}
