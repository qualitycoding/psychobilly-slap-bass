// Psychobilly Slap Bass 0.1.0 — core DSP engine.
// C++ translation of the verified planning candidate (research/spikes/dsp/dsp_spike.py,
// round-6 corrections applied). Float sample engine, deterministic seeded RNG,
// no allocation after preparation (A-006 realtime-safety contract).
#pragma once

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>

namespace psb {

inline float midiHz(int note) {
    return 440.0f * std::pow(2.0f, static_cast<float>(note - 69) / 12.0f);
}

// Parameter order is the frozen D-021/APVTS order (tests/_support.py DEFAULTS).
inline constexpr int kParamCount = 8;
inline constexpr std::array<const char*, kParamCount> kParamIds = {
    "pluck_slap", "slap_brightness", "body_resonance", "sustain",
    "string_tension", "attack_noise", "mechanical_noise", "output_level"};
inline constexpr std::array<float, kParamCount> kParamDefaults = {
    0.35f, 0.55f, 0.45f, 0.70f, 0.50f, 0.20f, 0.15f, 0.75f};

struct ControlSet {
    float pluck_slap = 0.35f;
    float slap_brightness = 0.55f;
    float body_resonance = 0.45f;
    float sustain = 0.70f;
    float string_tension = 0.50f;
    float attack_noise = 0.20f;
    float mechanical_noise = 0.15f;
    float output_level = 0.75f;

    static ControlSet fromArray(const float* values) {
        ControlSet c;
        c.pluck_slap = values[0];
        c.slap_brightness = values[1];
        c.body_resonance = values[2];
        c.sustain = values[3];
        c.string_tension = values[4];
        c.attack_noise = values[5];
        c.mechanical_noise = values[6];
        c.output_level = values[7];
        return c;
    }
    void clamp01() {
        pluck_slap = std::clamp(pluck_slap, 0.0f, 1.0f);
        slap_brightness = std::clamp(slap_brightness, 0.0f, 1.0f);
        body_resonance = std::clamp(body_resonance, 0.0f, 1.0f);
        sustain = std::clamp(sustain, 0.0f, 1.0f);
        string_tension = std::clamp(string_tension, 0.0f, 1.0f);
        attack_noise = std::clamp(attack_noise, 0.0f, 1.0f);
        mechanical_noise = std::clamp(mechanical_noise, 0.0f, 1.0f);
        output_level = std::clamp(output_level, 0.0f, 1.0f);
    }
};

// Deterministic xorshift32; uniform in [-1, 1).
struct Rng {
    std::uint32_t state = 0x50534c41u;
    float next() {
        state ^= state << 13;
        state ^= state >> 17;
        state ^= state << 5;
        return static_cast<float>(static_cast<std::int32_t>(state)) / 2147483648.0f;
    }
};

// Direct-form-II transposed biquad.
struct Biquad {
    float b0 = 1.0f, b1 = 0.0f, b2 = 0.0f, a1 = 0.0f, a2 = 0.0f;
    float z1 = 0.0f, z2 = 0.0f;
    float process(float x) {
        const float y = b0 * x + z1;
        z1 = b1 * x - a1 * y + z2;
        z2 = b2 * x - a2 * y;
        return y;
    }
    void reset() { z1 = z2 = 0.0f; }

    // scipy.signal.butter(2, cutoff, fs=sr) as one second-order section.
    static Biquad butterworth2(float cutoffHz, float sampleRate) {
        const float w0 = 2.0f * 3.14159265358979323846f * cutoffHz / sampleRate;
        const float cosw = std::cos(w0);
        const float alpha = std::sin(w0) / (2.0f * 0.70710678118654752440f);
        const float a0 = 1.0f + alpha;
        Biquad b;
        b.b0 = (1.0f - cosw) * 0.5f / a0;
        b.b1 = (1.0f - cosw) / a0;
        b.b2 = b.b0;
        b.a1 = -2.0f * cosw / a0;
        b.a2 = (1.0f - alpha) / a0;
        return b;
    }

    // scipy.signal.iirpeak(f, Q, fs=sr): unity-gain-at-peak resonator.
    // scipy computes bw = w0/Q (rad/sample) and uses the form:
    //   r = bw/2; b0 = r/(1+r); b2 = -b0; a1 = -2cos(w0)/(1+r); a2 = (1-r)/(1+r)
    static Biquad iirPeak(float frequencyHz, float q, float sampleRate) {
        const float w0 = 2.0f * 3.14159265358979323846f * frequencyHz / sampleRate;
        const float r = (w0 / q) * 0.5f;
        const float norm = 1.0f / (1.0f + r);
        const float cosw = std::cos(w0);
        Biquad b;
        b.b0 = r * norm;
        b.b1 = 0.0f;
        b.b2 = -b.b0;
        b.a1 = -2.0f * cosw * norm;
        b.a2 = (1.0f - r) * norm;
        return b;
    }
};

inline float flushDenormal(float x) {
    return (std::fabs(x) < 1.17549435e-38f) ? 0.0f : x;
}

// Fixed-capacity storage so no allocation happens after preparation.
inline constexpr int kMaxLineSize = 6000;        // 96 kHz / 16 Hz + margin
inline constexpr int kMaxNoiseSamples = 16384;   // >= 0.12 s at 96 kHz

// One sounding string with its per-note output paths.
class StringInstance {
public:
    void prepare(float sampleRate, float frequency, float velocity,
                 const ControlSet& controls, std::uint32_t seed) {
        sampleRate_ = sampleRate;
        frequency_ = std::clamp(frequency, 16.0f, 1200.0f);
        velocity_ = std::clamp(velocity, 0.0f, 1.0f);
        controls_ = controls;
        controls_.clamp01();
        seed_ = seed;

        const float delay = sampleRate_ / frequency_;
        lineSize_ = std::min(kMaxLineSize, static_cast<int>(std::ceil(delay)) + 3);
        write_ = 0;
        loopState_ = 0.0f;

        // Excitation: white noise, comb-differenced at the pluck position,
        // then one-pole low-pass [0.30] / [1, -0.70] (spike translation).
        Rng rng {seed_};
        std::array<float, kMaxLineSize> noise {};
        for (int i = 0; i < lineSize_; ++i)
            noise[static_cast<std::size_t>(i)] = rng.next();
        const int shift = std::max(1, static_cast<int>(0.18f * delay));
        float lp = 0.0f;
        for (int i = 0; i < lineSize_; ++i) {
            const float comb = noise[static_cast<std::size_t>((i + shift) % lineSize_)];
            const float x = 0.32f * velocity_ * (noise[static_cast<std::size_t>(i)] - 0.65f * comb);
            lp = 0.42f * x + 0.58f * lp;
            line_[static_cast<std::size_t>(i)] = lp;
        }

        const float t60 = 0.20f * std::pow(12.0f, controls_.sustain);
        loopGain_ = std::min(0.99995f, std::pow(10.0f, -3.0f / (frequency_ * t60)));
        filterAlpha_ = 0.35f + 0.25f * controls_.string_tension;
        threshold_ = std::max(0.035f, 0.27f - 0.105f * velocity_ - 0.045f * controls_.string_tension);

        const float radCut = std::clamp(300.0f + 6.0f * frequency_, 350.0f, 2800.0f)
                           * (0.75f + 0.50f * controls_.string_tension);
        radiation_ = Biquad::butterworth2(radCut, sampleRate_);
        body1_ = Biquad::iirPeak(82.0f, 1.1f, sampleRate_);
        body2_ = Biquad::iirPeak(190.0f, 1.8f, sampleRate_);
        body3_ = Biquad::iirPeak(430.0f, 2.2f, sampleRate_);
        contactFilter_ = OnePole {};
        collisionFilter_ = OnePole {};
        contactFilter_.alpha = collisionFilter_.alpha = 0.10f + 0.85f * controls_.slap_brightness;

        // Noise component buffers (bounded, preallocated).
        contactLen_ = std::min(kMaxNoiseSamples, static_cast<int>(0.040f * sampleRate_));
        attackLen_ = std::min(kMaxNoiseSamples, static_cast<int>(0.018f * sampleRate_));
        mechLen_ = std::min(kMaxNoiseSamples, static_cast<int>(0.120f * sampleRate_));
        for (int i = 0; i < contactLen_; ++i)
            contactNoise_[static_cast<std::size_t>(i)] = rng.next() * std::exp(-static_cast<float>(i) / std::max(1.0f, 0.009f * sampleRate_));
        for (int i = 0; i < attackLen_; ++i)
            attackNoise_[static_cast<std::size_t>(i)] = rng.next() * std::exp(-static_cast<float>(i) / std::max(1.0f, 0.004f * sampleRate_));
        for (int i = 0; i < mechLen_; ++i)
            mechNoise_[static_cast<std::size_t>(i)] = rng.next() * std::exp(-static_cast<float>(i) / std::max(1.0f, 0.030f * sampleRate_));
        pos_ = 0;
        released_ = false;
        releaseGain_ = 1.0f;
        active_ = true;
        lastPitchedRaw_ = 0.0f;
    }

    void release() { released_ = true; }
    bool active() const { return active_; }
    float lastOutput() const { return lastPitchedRaw_; }
    void setGain(float g) { gain_ = g; }

    // Returns the pre-mix pitched sample; fills body/contact/attack/mechanical paths.
    float process(float sympathetic, float& bodyOut, float& contactOut,
                  float& attackOut, float& mechOut) {
        if (!active_)
            return 0.0f;

        const float delay = sampleRate_ / frequency_;
        const float read = std::fmod(static_cast<float>(write_) - delay + static_cast<float>(lineSize_),
                                     static_cast<float>(lineSize_));
        const auto i0 = static_cast<std::size_t>(read);
        const float frac = read - static_cast<float>(i0);
        const float x = (1.0f - frac) * line_[i0] + frac * line_[(i0 + 1) % lineSize_];
        loopState_ += filterAlpha_ * (x - loopState_);
        const float clipped = std::clamp(x, -threshold_, threshold_);
        const float excess = x - clipped;
        float write = loopGain_ * loopState_ - 0.62f * excess + 0.015f * sympathetic;
        line_[static_cast<std::size_t>(write_)] = flushDenormal(write);
        write_ = (write_ + 1) % lineSize_;

        // Release ramp (40 ms) after note-off; otherwise the string rings out
        // naturally via loopGain_ < 1.
        if (released_) {
            releaseGain_ -= 1.0f / (0.040f * sampleRate_);
            if (releaseGain_ <= 0.0f) {
                active_ = false;
                return 0.0f;
            }
        }
        const float env = std::max(0.0f, releaseGain_);

        const float pitched = flushDenormal(x);
        lastPitchedRaw_ = pitched;

        const float radiated = radiation_.process(pitched);
        const float body = (body1_.process(radiated) + body2_.process(radiated) + body3_.process(radiated)) / 3.0f;

        float contact = 0.0f, attack = 0.0f, mech = 0.0f;
        if (pos_ < contactLen_)
            contact = contactFilter_.process(contactNoise_[static_cast<std::size_t>(pos_)]);
        if (pos_ < attackLen_)
            attack = attackNoise_[static_cast<std::size_t>(pos_)];
        if (pos_ < mechLen_)
            mech = mechNoise_[static_cast<std::size_t>(pos_)];
        ++pos_;

        bodyOut = body * env;
        contactOut = (0.28f * contact + 1.8f * collisionFilter_.process(excess)) * env;
        attackOut = attack * env;
        mechOut = mech * env;
        return radiated * env;
    }

private:
    struct OnePole {
        float alpha = 0.5f;
        float state = 0.0f;
        float process(float x) {
            state = alpha * x + (1.0f - alpha) * state;
            return state;
        }
    };

    float sampleRate_ = 48000.0f;
    float frequency_ = 55.0f;
    float velocity_ = 0.5f;
    ControlSet controls_{};
    std::uint32_t seed_ = 0;
    std::array<float, kMaxLineSize> line_ {};
    int lineSize_ = 0;
    int write_ = 0;
    float loopState_ = 0.0f;
    float loopGain_ = 0.99f;
    float filterAlpha_ = 0.5f;
    float threshold_ = 0.1f;
    float gain_ = 1.0f;
    float releaseGain_ = 1.0f;
    bool released_ = false;
    bool active_ = false;
    float lastPitchedRaw_ = 0.0f;
    Biquad radiation_, body1_, body2_, body3_;
    OnePole contactFilter_, collisionFilter_;
    std::array<float, kMaxNoiseSamples> contactNoise_ {}, attackNoise_ {}, mechNoise_ {};
    int contactLen_ = 0, attackLen_ = 0, mechLen_ = 0;
    int pos_ = 0;
};

} // namespace psb
