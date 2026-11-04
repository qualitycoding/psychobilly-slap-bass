// 24-bit PCM RIFF/WAV writer (D-024/D-025 shipped-path output; no normalisation).
#pragma once

#include <cstdint>
#include <fstream>
#include <string>
#include <vector>

namespace psb {

class WavWriter {
public:
    // samples: interleaved stereo float in [-1, 1]; quantised to 24-bit PCM.
    static bool write24(const std::string& path, const std::vector<float>& interleavedStereo,
                        int sampleRate, std::string& error) {
        if (interleavedStereo.size() % 2 != 0) {
            error = "sample count is not stereo-interleaved";
            return false;
        }
        const std::uint32_t frames = static_cast<std::uint32_t>(interleavedStereo.size() / 2);
        const std::uint16_t channels = 2;
        const std::uint16_t bits = 24;
        const std::uint32_t blockAlign = channels * 3;
        const std::uint32_t dataSize = frames * blockAlign;

        std::ofstream out(path, std::ios::binary | std::ios::trunc);
        if (!out) {
            error = "cannot open output file";
            return false;
        }
        auto u32 = [&out](std::uint32_t v) {
            out.put(static_cast<char>(v & 0xff));
            out.put(static_cast<char>((v >> 8) & 0xff));
            out.put(static_cast<char>((v >> 16) & 0xff));
            out.put(static_cast<char>((v >> 24) & 0xff));
        };
        auto u16 = [&out](std::uint16_t v) {
            out.put(static_cast<char>(v & 0xff));
            out.put(static_cast<char>((v >> 8) & 0xff));
        };

        out.write("RIFF", 4);
        u32(36 + dataSize);
        out.write("WAVE", 4);
        out.write("fmt ", 4);
        u32(16);
        u16(1); // PCM
        u16(channels);
        u32(static_cast<std::uint32_t>(sampleRate));
        u32(static_cast<std::uint32_t>(sampleRate) * blockAlign);
        u16(static_cast<std::uint16_t>(blockAlign));
        u16(bits);
        out.write("data", 4);
        u32(dataSize);

        std::vector<char> bytes;
        bytes.reserve(1 << 16);
        for (float f : interleavedStereo) {
            long v = static_cast<long>(f * 8388608.0f); // truncation, matches int24 range scale
            if (v > 8388607L) v = 8388607L;
            if (v < -8388608L) v = -8388608L;
            const std::uint32_t u = static_cast<std::uint32_t>(v) & 0xffffffu;
            bytes.push_back(static_cast<char>(u & 0xff));
            bytes.push_back(static_cast<char>((u >> 8) & 0xff));
            bytes.push_back(static_cast<char>((u >> 16) & 0xff));
            if (bytes.size() >= (1 << 16)) {
                out.write(bytes.data(), static_cast<std::streamsize>(bytes.size()));
                bytes.clear();
            }
        }
        if (!bytes.empty())
            out.write(bytes.data(), static_cast<std::streamsize>(bytes.size()));
        if (!out) {
            error = "write failed";
            return false;
        }
        return true;
    }
};

} // namespace psb
