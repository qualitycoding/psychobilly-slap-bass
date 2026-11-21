// Psychobilly Slap Bass — headless DSP engine (C++20, no JUCE dependency).
// AGPL-3.0-only. See LICENSE and NOTICES.md.
#pragma once

#include <array>
#include <cstdint>
#include <string>
#include <vector>

namespace psb
{

inline constexpr int kNumVoices = 8;
inline constexpr double kCouplingRadius = 0.105;   // D-019
inline constexpr double kCrossfadeMs = 10.0;       // D-019
inline constexpr double kShippedMixScale = 0.24;   // D-021 fixed shipped-path mix scale
inline constexpr int kMaxEvents = 65536;
inline constexpr int64_t kMaxFrames = 19200000;    // 200 s at 96 kHz
inline constexpr int kMaxStateBytes = 65536;       // D-012
inline constexpr int kMaxDelay = 8192;
inline constexpr int kMaxTransients = 64;

struct Controls
{
    double pluck_slap = 0.35;
    double slap_brightness = 0.55;
    double body_resonance = 0.45;
    double sustain = 0.70;
    double string_tension = 0.50;
    double attack_noise = 0.20;
    double mechanical_noise = 0.15;
    double output_level = 0.75;
};

struct Event
{
    int64_t sample = 0;
    enum Type : int { note_on, note_off, pitch_bend } type = note_on;
    int channel = 1;
    int note = 60;
    double velocity = 0.0;
    int gesture = 0; // 0 pluck, 1 pop, 2 slap, 3 ghost (D-041 schema 2)
    int bend = 8192; // 14-bit pitch bend, centre 8192 (D-020)
};

struct RenderComponents
{
    std::vector<double> mix, pitched, contact, body, attack, mechanical; // stereo interleaved
};

struct RenderMeta
{
    int sample_rate = 48000;
    int64_t frames = 0;
    double peak = 0.0;
    double rms = 0.0;
};

// Deterministic xorshift64 PRNG; single stream per render for reproducibility.
class Rng
{
public:
    explicit Rng(uint64_t seed) : s_(seed ? seed : 0x9E3779B97F4A7C15ULL) {}
    double uniform(); // [0, 1)
private:
    uint64_t s_;
};

class Engine
{
public:
    Engine();
    ~Engine();
    Engine(const Engine&) = delete;
    Engine& operator=(const Engine&) = delete;

    void prepare(double sampleRate, int maxFramesPerBlock);
    void reset();
    void setControls(const Controls& c) { controls_ = c; }
    void setSeed(uint64_t seed) { seed_ = seed; }

    // Queue one scored event (must be submitted in nondecreasing sample order).
    bool addEvent(const Event& e, std::string* error = nullptr);

    struct RenderResult
    {
        RenderComponents components;
        RenderMeta meta;
    };

    // Offline render of exactly `frames` samples (allocates; not for the audio thread).
    RenderResult render(int64_t frames);

    // Realtime-safe block render: writes n frames of stereo mix into outL/outR.
    // No allocation, locking, file or network access. Call prepare() first and
    // submit events with absolute sample positions before filling blocks.
    void fillBlock(int n, double* outL, double* outR,
                   double* capPitched = nullptr, double* capContact = nullptr,
                   double* capBody = nullptr, double* capAttack = nullptr,
                   double* capMech = nullptr);

    // Voice allocator statistics (T-015 contract); valid after rendering.
    struct Lifecycle
    {
        int max_observed_voices = 0;
        int steals = 0;
        int retriggers = 0;
        double coupling_spectral_radius = kCouplingRadius;
        double crossfade_ms = kCrossfadeMs;
        bool no_allocation_in_process = true;
    };
    const Lifecycle& lifecycle() const { return lifecycle_; }

private:
    struct OnePoleLp;
    struct OnePoleHp;
    struct Resonator;
    struct WaveguideString;
    struct Transient;
    struct Voice;

    struct BusFilters; // engine-level bus filters, allocated at prepare()

    void noteOn(const Event& e, int64_t absFrame);
    void noteOff(const Event& e);
    void addTransient(int type, double gain, int64_t untilSample);
    void dispatchEventsUpTo(int64_t absFrame);
    void tick(double& outL, double& outR, int64_t absFrame);
    void refreshFilterCutoffs();

    double fs_ = 48000.0;
    int blockSize_ = 512;
    Controls controls_;
    std::vector<Event> events_;
    size_t nextEvent_ = 0;
    std::array<Voice*, kNumVoices> voices_{};
    std::array<Transient*, kMaxTransients> transients_{};
    BusFilters* bus_ = nullptr;
    Lifecycle lifecycle_;
    uint64_t seed_ = 0;
    Rng rng_;
    double prevOuts_[kNumVoices] = {};
    int64_t frameCounter_ = 0;
    double peak_ = 0.0;
    double sumSq_ = 0.0;
    // per-tick component buses for offline capture (render() only)
    double lastPitchedBus_ = 0.0, lastContactBusScaled_ = 0.0, lastBodyBus_ = 0.0;
    double lastAttackBus_ = 0.0, lastMechBus_ = 0.0;
};

} // namespace psb
