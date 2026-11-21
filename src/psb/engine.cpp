// Psychobilly Slap Bass — headless DSP engine implementation.
// AGPL-3.0-only.
//
// Physical model summary (plan/DECISIONS.md D-016/D-019/D-021/D-032..D-036):
//  * eight voices, each driving one bidirectional waveguide string with
//    fractional (allpass) delay, frequency-dependent loop damping, and a smooth
//    amplitude-dependent downward onset pitch glide (extra delay relaxing to
//    zero, distinct from static stiffness inharmonicity, which the D-033
//    complexity ladder keeps optional);
//  * explicit gestures: outward pluck, outward pop/rebound, inward slap and
//    muted ghost (D-032), shaped deterministic excitation bursts plus a single
//    nonlinear fingerboard contact junction with bounded repeated collision
//    (fast-decaying contact envelope, D-033);
//  * sympathetic input from exactly the other seven voice outputs (D-019,
//    radius kCouplingRadius = 0.105);
//  * compact modal body (four resonators) fed by the pitched sum; internal
//    piezo/magnetic/microphone flavour via the fixed shipped-path blend; pitch
//    and slap/contact buses kept separate (D-036), radiation cutoff
//    350 + 350*string_tension Hz on the shipped pitched path;
//  * fixed shipped-path mix scale 0.24 and D-021 control mappings, with the
//    output_level taper 2^(4*level - 2). No renderer normalisation exists.
#include "engine.h"

#include <algorithm>
#include <cmath>

namespace psb
{

namespace
{
constexpr double kTwoPi = 6.28318530717958647692;

inline double midiHz(double note) { return 440.0 * std::pow(2.0, (note - 69.0) / 12.0); }
inline double sanitise_(double x) { return std::abs(x) < 1e-300 ? 0.0 : x; }
} // namespace

struct Engine::OnePoleLp
{
    double a = 1.0, y = 0.0, lastFc = -1.0;
    void setCutoff(double fc, double fs)
    {
        if (fc == lastFc) return;
        lastFc = fc;
        a = 1.0 - std::exp(-kTwoPi * std::min(fc, 0.45 * fs) / fs);
    }
    double process(double x)
    {
        y += a * (x - y);
        return sanitise_(y);
    }
    void reset() { y = 0.0; }
    // low-frequency phase delay in samples: (1-a)/a
    double phaseDelay() const { return (1.0 - a) / a; }
};

struct Engine::OnePoleHp
{
    double a = 1.0, lp = 0.0, lastFc = -1.0;
    void setCutoff(double fc, double fs)
    {
        if (fc == lastFc) return;
        lastFc = fc;
        a = 1.0 - std::exp(-kTwoPi * std::min(fc, 0.45 * fs) / fs);
    }
    double process(double x)
    {
        lp += a * (x - lp);
        return sanitise_(x - lp);
    }
    void reset() { lp = 0.0; }
};

struct Engine::Resonator
{
    double b0 = 0, b2 = 0, a1 = 0, a2 = 0;
    double x1 = 0, x2 = 0, y1 = 0, y2 = 0;
    void setMode(double f, double q, double gain, double fs)
    {
        const double w = kTwoPi * f / fs;
        const double alpha = std::sin(w) / (2.0 * q);
        const double a0 = 1.0 + alpha;
        b0 = alpha * gain / a0;
        b2 = -alpha * gain / a0;
        a1 = -2.0 * std::cos(w) / a0;
        a2 = (1.0 - alpha) / a0;
    }
    double process(double x)
    {
        const double y = b0 * x + b2 * x2 - a1 * y1 - a2 * y2;
        x2 = x1; x1 = x;
        y2 = y1; y1 = y;
        return sanitise_(y);
    }
    void reset() { x1 = x2 = y1 = y2 = 0.0; }
};

// One bidirectional waveguide string: fractional (allpass) delay, loop
// damping, amplitude-dependent downward onset glide, one nonlinear contact
// junction with a fast-decaying collision envelope.
struct Engine::WaveguideString
{
    std::array<double, kMaxDelay> buf{};
    int w = 0;
    int nInt = 100;
    double apA = 0.0, apState = 0.0;
    OnePoleLp loopLp;
    double loopGain = 0.999;
    double t60 = 1.0;
    int loopGainN = -1; // nInt value loopGain was computed for
    double baseDelay = 100.0;
    double glideExtra = 0.0;
    double glideRate = 0.0;
    double contactEnv = 0.0;
    double contactEnvRate = 0.0;
    double collisionThreshold = 0.10;
    double collisionWeight = 0.5;
    int collisionCooldown = 0;
    int dampedLeft = 0;
    double fs = 48000.0;

    void setup(double f0, double sustain, double fsRate)
    {
        fs = fsRate;
        loopLp.setCutoff(400.0 + 4500.0 * sustain * sustain, fs);
        // the loop lowpass adds a frequency-independent phase delay of (1-a)/a
        // samples at the fundamental; shorten the target delay to compensate
        baseDelay = fs / f0 - loopLp.phaseDelay();
        w = 0;
        buf.fill(0.0);
        apState = 0.0;
        glideExtra = 0.0;
        contactEnv = 0.0;
        collisionCooldown = 0;
        dampedLeft = 0;
        applyT60(sustain);
    }

    void applyT60(double sustain)
    {
        t60 = 0.5 * std::pow(10.0, 1.05 * sustain);
        // loopGain is applied once per full circulation of the delay line
        // (every nInt samples), so it must carry the per-pass loss
        // 10^(-3 * nInt / (t60 * fs)); it is recomputed lazily in process()
        // whenever nInt changes. Passive gain only: the one-pole loop filter
        // adds negligible extra loss at the fundamental, and folding it into
        // the gain would push net loop gain above unity at low frequencies
        // and make the string self-oscillate.
        loopGainN = -1; // force recompute
    }

    // gesture: 0 outward pluck, 1 outward pop/rebound, 2 inward slap, 3 muted ghost
    void excite(Rng& rng, double velocity, int gesture, double sustain, double fsRate)
    {
        fs = fsRate;
        static const double kBurstMs[4] = {4.0, 8.0, 1.5, 1.0};
        static const double kBurstFc[4] = {3500.0, 7000.0, 10000.0, 1100.0};
        static const double kBurstGain[4] = {1.0, 1.15, 0.85, 0.35};
        static const double kCollisionWeight[4] = {0.5, 0.9, 1.0, 0.6};
        static const double kGlideWeight[4] = {0.08, 1.0, 0.5, 0.0};
        const int g = gesture & 3;
        const int burstLen = std::max(8, (int) (fs * kBurstMs[g] / 1000.0));
        OnePoleLp shape;
        shape.setCutoff(kBurstFc[g], fs);
        const double gain = velocity * kBurstGain[g];
        // inject the burst immediately upstream of the read pointer so the loop
        // picks it up on the next pass (writing at the write pointer would be
        // overwritten before the read pointer reaches it)
        const int readPos = (w - nInt) % kMaxDelay;
        for (int i = 0; i < burstLen; ++i)
        {
            const double n = rng.uniform() * 2.0 - 1.0;
            buf[((readPos + i) % kMaxDelay + kMaxDelay) % kMaxDelay] +=
                shape.process(n) * gain * (1.0 - (double) i / burstLen);
        }
        collisionWeight = kCollisionWeight[g];
        collisionThreshold = 0.06 + 0.20 * velocity;
        contactEnv = 1.0;
        contactEnvRate = std::exp(-1.0 / (0.12 * fs));
        if (g == 3)
            dampedLeft = (int) (0.060 * fs);
        // released-string tension spike: the delay line starts SHORT (pitch
        // sharp) and relaxes back to baseDelay as the glide envelope decays
        const double depthCents = std::min(120.0, 150.0 * velocity * velocity * kGlideWeight[g]);
        glideExtra = -baseDelay * (1.0 - std::pow(2.0, -depthCents / 1200.0));
        glideRate = std::exp(-1.0 / (0.070 * fs));
        loopLp.setCutoff(400.0 + 4500.0 * sustain * sustain, fs);
        applyT60(sustain);
    }

    double process(double sympatheticIn, double& contactOut)
    {
        glideExtra *= glideRate;
        contactEnv *= contactEnvRate;
        const double eff = baseDelay + glideExtra;
        const int nNew = std::max(2, (int) std::floor(eff));
        const double frac = eff - std::floor(eff);
        const double a = (1.0 - frac) / (1.0 + frac);
        if (nNew != nInt) { nInt = nNew; apState = 0.0; }
        if (nInt != loopGainN)
        {
            loopGain = std::pow(10.0, -3.0 * (double) nInt / (t60 * fs));
            loopGainN = nInt;
        }

        const int rd = (w - nInt + 2 * kMaxDelay) % kMaxDelay;
        const double x = buf[rd];
        const double apOut = a * x + apState; // first-order allpass fractional delay
        apState = x - a * apOut;
        double v = loopLp.process(apOut);
        const double g = dampedLeft > 0 ? (--dampedLeft, loopGain * 0.5) : loopGain;
        v *= g;

        contactOut = 0.0;
        if (collisionCooldown > 0)
            --collisionCooldown;
        else if (contactEnv * collisionWeight > 0.02 && std::abs(v) > collisionThreshold)
        {
            const double ex = (std::abs(v) - collisionThreshold) * contactEnv * collisionWeight;
            contactOut = std::copysign(ex * 0.9, v);
            v -= std::copysign(ex * 0.4, v);
            collisionCooldown = std::max(8, nInt / 2);
        }

        buf[w] = sanitise_(v + sympatheticIn);
        const double out = buf[(w - nInt / 2 + 2 * kMaxDelay) % kMaxDelay];
        w = (w + 1) % kMaxDelay;
        return sanitise_(out);
    }
};

struct Engine::Transient
{
    bool active = false;
    int type = 0; // 0 attack noise, 1 hand/fingerboard contact
    double gain = 0.0;
    int64_t until = 0;
    OnePoleLp lp;
    OnePoleHp hp;
};

struct Engine::Voice
{
    bool active = false;
    bool ringing = false; // string still has energy after note-off
    int note = 60;
    double velocity = 0.0;
    int gesture = 0;
    int64_t startedAt = 0;
    int64_t silencedAt = -1;
    double amp = 0.0;
    double fade = 1.0;
    double bend = 8192.0;
    WaveguideString string;
};

struct Engine::BusFilters
{
    Resonator bodyModes[4];
    OnePoleLp contactBrightness;
    OnePoleLp radiation;
    OnePoleLp tension;
    OnePoleHp pitchedDc;
    OnePoleLp mech;
    OnePoleLp attackLp;
    OnePoleHp attackHp;
};

double Rng::uniform()
{
    s_ ^= s_ << 13; s_ ^= s_ >> 7; s_ ^= s_ << 17;
    return (double) (s_ >> 11) * (1.0 / 9007199254740992.0);
}

Engine::Engine() : rng_(0) {}

Engine::~Engine()
{
    for (auto* v : voices_) delete v;
    for (auto* t : transients_) delete t;
    delete bus_;
}

void Engine::prepare(double sampleRate, int maxFramesPerBlock)
{
    fs_ = sampleRate;
    blockSize_ = std::max(1, maxFramesPerBlock);
    for (auto*& v : voices_)
    {
        delete v;
        v = new Voice();
    }
    for (auto*& t : transients_)
    {
        delete t;
        t = new Transient();
    }
    delete bus_;
    bus_ = new BusFilters();
    const double modes[4][3] = {{65.0, 9.0, 1.0}, {112.0, 8.0, 0.8}, {163.0, 7.0, 0.6}, {248.0, 5.0, 0.4}};
    for (int m = 0; m < 4; ++m) bus_->bodyModes[m].setMode(modes[m][0], modes[m][1], modes[m][2], fs_);
    bus_->pitchedDc.setCutoff(40.0, fs_);
    bus_->mech.setCutoff(300.0, fs_);
    bus_->attackLp.setCutoff(6000.0, fs_);
    bus_->attackHp.setCutoff(150.0, fs_);
    reset();
}

void Engine::reset()
{
    for (auto* v : voices_)
    {
        v->active = false;
        v->ringing = false;
        v->fade = 1.0;
        v->string = WaveguideString();
    }
    for (auto* t : transients_) *t = Transient();
    nextEvent_ = 0;
    frameCounter_ = 0;
    peak_ = 0.0;
    sumSq_ = 0.0;
    std::fill(prevOuts_, prevOuts_ + kNumVoices, 0.0);
    if (bus_)
    {
        for (auto& m : bus_->bodyModes) m.reset();
        bus_->contactBrightness.reset();
        bus_->radiation.reset();
        bus_->tension.reset();
        bus_->pitchedDc.reset();
        bus_->mech.reset();
        bus_->attackLp.reset();
        bus_->attackHp.reset();
    }
    lifecycle_ = Lifecycle();
}

bool Engine::addEvent(const Event& e, std::string* error)
{
    if ((int) events_.size() >= kMaxEvents) { if (error) *error = "event limit exceeded"; return false; }
    if (!std::isfinite(e.velocity) || e.velocity < 0.0 || e.velocity > 1.0) { if (error) *error = "velocity out of range"; return false; }
    if (e.note < 0 || e.note > 127) { if (error) *error = "note out of range"; return false; }
    if (!events_.empty() && e.sample < events_.back().sample) { if (error) *error = "events out of order"; return false; }
    if (e.gesture < 0 || e.gesture > 3) { if (error) *error = "gesture out of range"; return false; }
    if (e.type == Event::note_on && e.velocity == 0.0)
    {
        Event off = e;
        off.type = Event::note_off;
        events_.push_back(off);
        return true;
    }
    events_.push_back(e);
    return true;
}

void Engine::addTransient(int type, double gain, int64_t untilSample)
{
    for (auto* t : transients_)
        if (!t->active)
        {
            t->active = true;
            t->type = type;
            t->gain = gain;
            t->until = untilSample;
            t->lp.setCutoff(type == 0 ? 6000.0 : 5000.0, fs_);
            t->hp.setCutoff(type == 0 ? 150.0 : 90.0, fs_);
            return;
        }
    // pool exhausted: drop rather than allocate (realtime safety)
}

void Engine::noteOn(const Event& e, int64_t absFrame)
{
    static const double kHandGain[4] = {0.03, 0.55, 0.75, 0.20};
    const int g = e.gesture & 3;

    // same-string retrigger while the voice is active or still ringing:
    // re-excite without clearing the delay line (D-032 energy preservation)
    for (auto* v : voices_)
    {
        if (v->note == e.note && (v->active || (v->ringing && absFrame - v->silencedAt < (int64_t) fs_)))
        {
            ++lifecycle_.retriggers;
            v->active = true;
            v->ringing = false;
            v->velocity = e.velocity;
            v->gesture = g;
            v->amp = std::max(v->amp * 0.999, e.velocity);
            v->startedAt = absFrame;
            v->string.excite(rng_, e.velocity, g, controls_.sustain, fs_);
            addTransient(1, e.velocity * kHandGain[g], absFrame + (int64_t) (fs_ * 0.004));
            addTransient(0, e.velocity * 0.42, absFrame + (int64_t) (fs_ * 0.004));
            return;
        }
    }

    Voice* slot = nullptr;
    for (auto* v : voices_)
        if (!v->active && !v->ringing) { slot = v; break; }
    if (slot == nullptr)
    {
        // steal quietest-then-oldest (D-019)
        slot = voices_[0];
        for (auto* v : voices_)
            if (v->amp < slot->amp - 1e-12
                || (std::abs(v->amp - slot->amp) <= 1e-12 && v->startedAt < slot->startedAt))
                slot = v;
        ++lifecycle_.steals;
    }
    slot->active = true;
    slot->ringing = false;
    slot->note = e.note;
    slot->velocity = e.velocity;
    slot->gesture = g;
    slot->bend = (double) e.bend;
    slot->startedAt = absFrame;
    slot->silencedAt = -1;
    slot->amp = e.velocity;
    slot->fade = 0.0; // 10 ms crossfade in after a steal or fresh start
    const double f0 = midiHz((double) e.note + 2.0 * ((double) e.bend - 8192.0) / 8192.0);
    slot->string.setup(f0, controls_.sustain, fs_);
    slot->string.excite(rng_, e.velocity, g, controls_.sustain, fs_);
    addTransient(1, e.velocity * kHandGain[g], absFrame + (int64_t) (fs_ * 0.004));
    addTransient(0, e.velocity * 0.42, absFrame + (int64_t) (fs_ * 0.004));
    const int active = (int) std::count_if(voices_.begin(), voices_.end(),
                                           [](const Voice* v) { return v->active; });
    lifecycle_.max_observed_voices = std::max(lifecycle_.max_observed_voices, active);
}

void Engine::noteOff(const Event& e)
{
    for (auto* v : voices_)
        if (v->active && v->note == e.note)
        {
            v->active = false;
            v->ringing = true;
            v->silencedAt = frameCounter_;
        }
}

void Engine::dispatchEventsUpTo(int64_t absFrame)
{
    while (nextEvent_ < events_.size() && events_[nextEvent_].sample <= absFrame)
    {
        const Event& e = events_[nextEvent_];
        if (e.type == Event::note_on) noteOn(e, e.sample);
        else if (e.type == Event::note_off) noteOff(e);
        else for (auto* v : voices_) if (v->active) v->bend = (double) e.bend;
        ++nextEvent_;
    }
}

void Engine::refreshFilterCutoffs()
{
    bus_->contactBrightness.setCutoff(400.0 * std::pow(2.0, 3.5 * controls_.slap_brightness), fs_);
    bus_->radiation.setCutoff(350.0 + 350.0 * controls_.string_tension, fs_);
    bus_->tension.setCutoff(300.0 + 3600.0 * controls_.string_tension * controls_.string_tension, fs_);
}

void Engine::tick(double& outL, double& outR, int64_t absFrame)
{
    (void) absFrame;
    refreshFilterCutoffs();
    const double contactGain = 0.05 + 0.95 * controls_.pluck_slap;
    const double bodyGain = 0.10 + 1.0 * controls_.body_resonance;
    const double taper = std::pow(2.0, 4.0 * controls_.output_level - 2.0);
    const double tensionHpAmount = 0.10 + 1.5 * controls_.string_tension;

    double outs[kNumVoices] = {};
    double contacts[kNumVoices] = {};
    const double fadeStep = 1000.0 / (kCrossfadeMs * fs_);
    for (int vi = 0; vi < kNumVoices; ++vi)
    {
        auto* v = voices_[(size_t) vi];
        if (v->fade < 1.0) v->fade = std::min(1.0, v->fade + fadeStep);
        if (!v->active && !v->ringing) { prevOuts_[vi] = 0.0; continue; }
        double sym = 0.0;
        for (int vj = 0; vj < kNumVoices; ++vj)
            if (vj != vi) sym += prevOuts_[vj];
        sym *= kCouplingRadius;
        double cOut = 0.0;
        const double s = v->string.process(sym, cOut) * v->fade;
        outs[vi] = s;
        contacts[vi] = cOut * v->fade;
        v->amp *= 0.99995;
    }

    double stringSum = 0.0, contactSum = 0.0;
    for (int vi = 0; vi < kNumVoices; ++vi)
    {
        stringSum += outs[vi];
        contactSum += contacts[vi];
    }

    double body = 0.0;
    for (auto& m : bus_->bodyModes) body += m.process(stringSum);

    double attack = 0.0, hand = 0.0;
    for (auto* t : transients_)
    {
        if (!t->active) continue;
        if (frameCounter_ >= t->until) { t->active = false; continue; }
        const double n = rng_.uniform() * 2.0 - 1.0;
        const double shaped = t->hp.process(t->lp.process(n));
        if (t->type == 0) attack += shaped * t->gain;
        else hand += shaped * t->gain;
    }

    const double dc = bus_->pitchedDc.process(stringSum);
    const double hpPart = stringSum - bus_->tension.process(stringSum);
    const double pitchedBus = 0.20 * dc + tensionHpAmount * hpPart;
    const double contactBus = bus_->contactBrightness.process(hand + contactSum);
    const double bodyBus = body * bodyGain;
    const double attackBus = bus_->attackLp.process(bus_->attackHp.process(attack)) * controls_.attack_noise;
    const double mechBus = bus_->mech.process(contactBus) * controls_.mechanical_noise;

    const double shippedPitched = bus_->radiation.process(pitchedBus + bodyBus);
    const double mix = kShippedMixScale * taper
        * (shippedPitched + contactGain * contactBus + attackBus + mechBus);

    lastPitchedBus_ = pitchedBus;
    lastContactBusScaled_ = contactGain * contactBus;
    lastBodyBus_ = bodyBus;
    lastAttackBus_ = attackBus;
    lastMechBus_ = mechBus;

    outL = mix;
    outR = mix;
    peak_ = std::max(peak_, std::abs(mix));
    sumSq_ += mix * mix * 2.0;
    std::copy(outs, outs + kNumVoices, prevOuts_);
}

void Engine::fillBlock(int n, double* outL, double* outR,
                       double* capPitched, double* capContact,
                       double* capBody, double* capAttack, double* capMech)
{
    for (int i = 0; i < n; ++i)
    {
        dispatchEventsUpTo(frameCounter_);
        tick(outL[i], outR[i], frameCounter_);
        if (capPitched) capPitched[i] = lastPitchedBus_;
        if (capContact) capContact[i] = lastContactBusScaled_;
        if (capBody) capBody[i] = lastBodyBus_;
        if (capAttack) capAttack[i] = lastAttackBus_;
        if (capMech) capMech[i] = lastMechBus_;
        ++frameCounter_;
    }
}

Engine::RenderResult Engine::render(int64_t frames)
{
    rng_ = Rng(seed_ ? seed_ : 0x50534C41ULL);
    reset();
    RenderResult result;
    auto& c = result.components;
    const size_t stereo = (size_t) frames * 2;
    c.mix.assign(stereo, 0.0);
    c.pitched.assign(stereo, 0.0);
    c.contact.assign(stereo, 0.0);
    c.body.assign(stereo, 0.0);
    c.attack.assign(stereo, 0.0);
    c.mechanical.assign(stereo, 0.0);

    std::vector<double> blockL((size_t) blockSize_), blockR((size_t) blockSize_);
    std::vector<double> capP((size_t) blockSize_), capC((size_t) blockSize_),
        capB((size_t) blockSize_), capA((size_t) blockSize_), capM((size_t) blockSize_);
    for (int64_t base = 0; base < frames; base += blockSize_)
    {
        const int n = (int) std::min<int64_t>(blockSize_, frames - base);
        fillBlock(n, blockL.data(), blockR.data(),
                  capP.data(), capC.data(), capB.data(), capA.data(), capM.data());
        for (int i = 0; i < n; ++i)
        {
            const size_t fr2 = (size_t) (base + i) * 2;
            c.mix[fr2] = blockL[(size_t) i];
            c.mix[fr2 + 1] = blockR[(size_t) i];
            c.pitched[fr2] = c.pitched[fr2 + 1] = capP[(size_t) i];
            c.contact[fr2] = c.contact[fr2 + 1] = capC[(size_t) i];
            c.body[fr2] = c.body[fr2 + 1] = capB[(size_t) i];
            c.attack[fr2] = c.attack[fr2 + 1] = capA[(size_t) i];
            c.mechanical[fr2] = c.mechanical[fr2 + 1] = capM[(size_t) i];
        }
    }

    result.meta.sample_rate = (int) fs_;
    result.meta.frames = frames;
    result.meta.peak = peak_;
    result.meta.rms = std::sqrt(sumSq_ / std::max<int64_t>(1, frames * 2));
    return result;
}

} // namespace psb
