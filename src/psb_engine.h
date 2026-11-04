// Eight-voice engine: allocation, quietest-then-oldest stealing, same-note
// retrigger with 10 ms crossfade, sympathetic coupling (spectral radius 0.105),
// frozen mix path (fixed 0.24 scale, no renderer normalisation — D-016/D-021).
#pragma once

#include "psb_dsp.h"

#include <cstdint>
#include <vector>

namespace psb {

inline constexpr int kVoiceSlots = 8;
inline constexpr float kCouplingGain = 0.015f;   // 7 x 0.015 off-diagonal -> radius 0.105
inline constexpr float kCrossfadeSeconds = 0.010f;
inline constexpr float kAttackRampSeconds = 0.010f;

struct NoteEvent {
    long sample = 0;
    enum class Type { note_on, note_off } type = Type::note_on;
    int channel = 1;
    int note = 60;
    float velocity = 0.0f;
};

struct MixView {
    float pitched = 0.0f, body = 0.0f, contact = 0.0f, attack = 0.0f, mechanical = 0.0f;
};

class Engine {
public:
    void prepare(double sampleRate, const ControlSet& controls) {
        sampleRate_ = static_cast<float>(sampleRate);
        controls_ = controls;
        controls_.clamp01();
        for (auto& slot : slots_) {
            slot = Slot {};
        }
        eventCursor_ = 0;
        position_ = 0;
        // All per-instance storage is fixed-capacity; preparation is the only
        // place where (de)allocation may occur.
    }

    void setEvents(const std::vector<NoteEvent>& events) {
        events_ = events;
        eventCursor_ = 0;
    }

    // Update control values without resetting voice state (host automation).
    void setControls(const ControlSet& controls) {
        controls_ = controls;
        controls_.clamp01();
    }

    void setSeed(std::uint32_t seed) { seed_ = seed; }

    void noteOn(int note, float velocity, std::uint32_t seed) {
        noteOnAt(midiHz(note), note, velocity, seed);
    }

    // Frequency-exact note-on (pitch bend): the slot is keyed by MIDI note for
    // note-off matching but oscillates at the supplied frequency.
    void noteOnAt(float frequency, int note, float velocity, std::uint32_t seed) {
        if (velocity <= 0.0f) { // D-023/D-020: zero-velocity note-on is note-off
            noteOff(note);
            return;
        }
        // Planning-spike parity: every slot ages once per note event.
        for (auto& slot : slots_)
            ++slot.age;
        // Same-note retrigger?
        for (auto& slot : slots_) {
            if (slot.active && slot.current.active() && slot.note == note && !slot.releasing) {
                slot.fading = slot.current;
                slot.fadingGain = 1.0f;
                slot.fadingActive = true;
                slot.current.prepare(sampleRate_, frequency, velocity, controls_, seed ^ 0x9e3779b9u);
                slot.velocity = velocity;
                slot.age = 0;
                slot.releasing = false;
                ++retriggers_;
                return;
            }
        }
        // Free slot?
        Slot* target = nullptr;
        for (auto& slot : slots_) {
            if (!slot.active || !slot.current.active()) {
                target = &slot;
                break;
            }
        }
        if (target == nullptr) {
            // D-019: steal the quietest voice; ties broken by oldest age.
            Slot* best = nullptr;
            for (auto& slot : slots_) {
                if (!slot.active)
                    continue;
                if (best == nullptr
                    || slot.velocity < best->velocity
                    || (slot.velocity == best->velocity && slot.age > best->age))
                    best = &slot;
            }
            target = best != nullptr ? best : &slots_[0];
            ++steals_;
        }
        target->active = true;
        target->note = note;
        target->velocity = velocity;
        target->age = 0;
        target->releasing = false;
        target->fadingActive = false;
        target->fadingGain = 0.0f;
        target->attackGain = 0.0f;
        target->current.prepare(sampleRate_, frequency, velocity, controls_, seed);
    }

    void noteOff(int note) {
        for (auto& slot : slots_) {
            if (slot.active && slot.note == note && !slot.releasing) {
                slot.current.release();
                slot.releasing = true;
            }
        }
    }

    // Process `n` samples; events carry sample offsets relative to this call
    // and are applied sample-accurately in stable order (D-023).
    void render(float* left, float* right, MixView* mix, int n) {
        const int total = static_cast<int>(events_.size());
        for (int i = 0; i < n; ++i) {
            while (eventCursor_ < total
                   && events_[static_cast<std::size_t>(eventCursor_)].sample == i) {
                const NoteEvent& ev = events_[static_cast<std::size_t>(eventCursor_)];
                if (ev.type == NoteEvent::Type::note_on)
                    noteOn(ev.note, ev.velocity, seed_ + static_cast<std::uint32_t>(ev.note) * 2654435761u
                           + static_cast<std::uint32_t>(eventCursor_) * 40503u);
                else
                    noteOff(ev.note);
                ++eventCursor_;
            }
            step(left ? &left[i] : nullptr, right ? &right[i] : nullptr,
                 mix ? &mix[i] : nullptr);
        }
        position_ += n;
    }

    long position() const { return position_; }

    // Lifecycle evidence (T-015/D-019).
    struct LifecycleStats {
        long events = 0;
        int maxObservedVoices = 0;
        int steals = 0;
        int retriggers = 0;
    };
    const LifecycleStats& lifecycle() const { return lifecycle_; }
    void resetLifecycle() { lifecycle_ = LifecycleStats {}; }
    int stealCount() const { return steals_; }
    int retriggerCount() const { return retriggers_; }

private:
    struct Slot {
        bool active = false;
        bool releasing = false;
        int note = 0;
        float velocity = 0.0f;
        long age = 0;
        float attackGain = 0.0f;
        StringInstance current;
        StringInstance fading;
        bool fadingActive = false;
        float fadingGain = 0.0f;
    };

    void step(float* left, float* right, MixView* mix) {
        float pitchedSum = 0.0f, bodySum = 0.0f, contactSum = 0.0f, attackSum = 0.0f, mechSum = 0.0f;
        float outputs[kVoiceSlots] = {};
        int activeCount = 0;

        for (int v = 0; v < kVoiceSlots; ++v) {
            Slot& slot = slots_[static_cast<std::size_t>(v)];
            if (!slot.active)
                continue;
            if (!slot.current.active() && !slot.fadingActive) {
                slot.active = false;
                continue;
            }
            ++activeCount;
            outputs[v] = slot.current.active() ? slot.current.lastOutput() : 0.0f;
            if (slot.fadingActive)
                outputs[v] += slot.fading.lastOutput() * slot.fadingGain;
        }
        lifecycle_.maxObservedVoices = std::max(lifecycle_.maxObservedVoices, activeCount);
        lifecycle_.steals = steals_;
        lifecycle_.retriggers = retriggers_;

        const float attackStep = 1.0f / (kAttackRampSeconds * sampleRate_);
        const float fadeStep = 1.0f / (kCrossfadeSeconds * sampleRate_);

        for (int v = 0; v < kVoiceSlots; ++v) {
            Slot& slot = slots_[static_cast<std::size_t>(v)];
            if (!slot.active)
                continue;
            float totalOthers = 0.0f;
            for (int u = 0; u < kVoiceSlots; ++u)
                if (u != v)
                    totalOthers += outputs[u];
            const float sympathetic = kCouplingGain * totalOthers;

            float body = 0.0f, contact = 0.0f, attack = 0.0f, mech = 0.0f;
            float pitched = 0.0f;
            slot.attackGain = std::min(1.0f, slot.attackGain + attackStep);
            if (slot.current.active()) {
                pitched = slot.current.process(sympathetic, body, contact, attack, mech) * slot.attackGain;
                pitchedSum += pitched;
                bodySum += body * slot.attackGain;
                contactSum += contact * slot.attackGain;
                attackSum += attack * slot.attackGain;
                mechSum += mech * slot.attackGain;
            }
            if (slot.fadingActive) {
                slot.fadingGain -= fadeStep;
                if (slot.fadingGain <= 0.0f || !slot.fading.active()) {
                    slot.fadingActive = false;
                    slot.fadingGain = 0.0f;
                } else {
                    float fb = 0.0f, fc = 0.0f, fa = 0.0f, fm = 0.0f;
                    const float fp = slot.fading.process(sympathetic, fb, fc, fa, fm) * slot.fadingGain;
                    pitchedSum += fp;
                    bodySum += fb * slot.fadingGain;
                    contactSum += fc * slot.fadingGain;
                    attackSum += fa * slot.fadingGain;
                    mechSum += fm * slot.fadingGain;
                }
            }
        }

        // Shipped path (D-016): fixed 0.24 mix scale, control weights, output gain.
        const float mixed = 0.24f * (0.75f * pitchedSum
                                     + 0.50f * controls_.body_resonance * bodySum
                                     + controls_.pluck_slap * contactSum
                                     + 0.12f * controls_.attack_noise * attackSum
                                     + 0.025f * controls_.mechanical_noise * mechSum);
        // D-021 output mapping: gain = 4^(2*(output_level-1)); T-023 requires an
        // exact 4.0 RMS ratio between output_level 0.75 and 0.25.
        const float outputGain = std::pow(4.0f, 2.0f * (controls_.output_level - 1.0f));
        const float out = flushDenormal(mixed * outputGain);

        if (left) *left = out;
        if (right) *right = out;
        if (mix) {
            mix->pitched = pitchedSum;
            mix->body = 0.50f * controls_.body_resonance * bodySum;
            mix->contact = controls_.pluck_slap * contactSum;
            mix->attack = 0.12f * controls_.attack_noise * attackSum;
            mix->mechanical = 0.025f * controls_.mechanical_noise * mechSum;
        }
    }

    float sampleRate_ = 48000.0f;
    ControlSet controls_{};
    std::array<Slot, kVoiceSlots> slots_ {};
    std::vector<NoteEvent> events_;
    std::size_t eventCursor_ = 0;
    long position_ = 0;
    std::uint32_t seed_ = 0x50534c41u;
    int steals_ = 0;
    int retriggers_ = 0;
    LifecycleStats lifecycle_;
};

} // namespace psb
