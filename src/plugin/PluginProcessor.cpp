// Psychobilly Slap Bass — JUCE VST3 wrapper around the headless engine.
// AGPL-3.0-only. Articulation stays out of the APVTS contract (D-032):
// the host selects a gesture per channel with CC 20 (0-3); anything else
// or absent maps to outward pluck.
#include "psb/engine.h"

#include <juce_audio_processors/juce_audio_processors.h>

#include <array>
#include <vector>

namespace
{
const std::array<const char*, 8> kParamIds = {
    "pluck_slap", "slap_brightness", "body_resonance", "sustain",
    "string_tension", "attack_noise", "mechanical_noise", "output_level"};

juce::AudioProcessorValueTreeState::ParameterLayout makeLayout()
{
    std::vector<std::unique_ptr<juce::RangedAudioParameter>> params;
    const double defaults[8] = {0.35, 0.55, 0.45, 0.70, 0.50, 0.20, 0.15, 0.75};
    for (int i = 0; i < 8; ++i)
        params.push_back(std::make_unique<juce::AudioParameterFloat>(
            juce::ParameterID(kParamIds[(size_t) i], 1), kParamIds[(size_t) i],
            juce::NormalisableRange<float>(0.0f, 1.0f), (float) defaults[i]));
    return {params.begin(), params.end()};
}
} // namespace

class PsychobillySlapBassProcessor : public juce::AudioProcessor
{
public:
    PsychobillySlapBassProcessor()
        : AudioProcessor(BusesProperties().withOutput("Output", juce::AudioChannelSet::stereo(), true)),
          apvts(*this, nullptr, "PSB_PARAMETERS", makeLayout())
    {
        engine_.prepare(44100.0, 512);
        pullControls();
        for (int ch = 0; ch < 16; ++ch) gestureForChannel_[(size_t) ch] = 0;
    }

    ~PsychobillySlapBassProcessor() override = default;

    const juce::String getName() const override { return "Psychobilly Slap Bass"; }
    bool acceptsMidi() const override { return true; }
    bool producesMidi() const override { return false; }
    bool isMidiEffect() const override { return false; }
    double getTailLengthSeconds() const override { return 8.0; }

    int getNumPrograms() override { return 1; }
    int getCurrentProgram() override { return 0; }
    void setCurrentProgram(int) override {}
    const juce::String getProgramName(int) override { return "Default"; }
    void changeProgramName(int, const juce::String&) override {}

    bool hasEditor() const override { return false; }
    juce::AudioProcessorEditor* createEditor() override { return nullptr; }

    void prepareToPlay(double sampleRate, int samplesPerBlock) override
    {
        engine_.prepare(sampleRate, samplesPerBlock);
    }

    void releaseResources() override {}

    bool isBusesLayoutSupported(const BusesLayout& layouts) const override
    {
        return layouts.getMainOutputChannelSet() == juce::AudioChannelSet::mono()
            || layouts.getMainOutputChannelSet() == juce::AudioChannelSet::stereo();
    }

    void processBlock(juce::AudioBuffer<float>& buffer, juce::MidiBuffer& midi) override
    {
        juce::ScopedNoDenormals noDenormals;
        pullControls();
        const int n = buffer.getNumSamples();
        for (const auto meta : midi)
        {
            const auto& msg = meta.getMessage();
            const int sample = meta.samplePosition;
            const int ch = std::clamp(msg.getChannel(), 1, 16) - 1;
            psb::Event ev{};
            ev.sample = sample;
            ev.channel = ch + 1;
            ev.note = msg.getNoteNumber();
            ev.velocity = msg.getFloatVelocity();
            ev.bend = 8192;
            if (msg.isNoteOn())
            {
                ev.type = psb::Event::Type::note_on;
                ev.gesture = gestureForChannel_[(size_t) ch];
                engine_.addEvent(ev, nullptr);
            }
            else if (msg.isNoteOff())
            {
                ev.type = psb::Event::Type::note_off;
                engine_.addEvent(ev, nullptr);
            }
            else if (msg.isPitchWheel())
            {
                ev.type = psb::Event::Type::pitch_bend;
                ev.bend = msg.getPitchWheelValue();
                engine_.addEvent(ev, nullptr);
            }
            else if (msg.isController() && msg.getControllerNumber() == 20)
            {
                gestureForChannel_[(size_t) ch] = msg.getControllerValue() / 32; // 0-3
            }
        }
        if ((int) blockL_.size() < n)
        {
            blockL_.assign((size_t) n, 0.0);
            blockR_.assign((size_t) n, 0.0);
        }
        engine_.fillBlock(n, blockL_.data(), blockR_.data());
        float* left = buffer.getWritePointer(0);
        float* right = buffer.getNumChannels() > 1 ? buffer.getWritePointer(1) : nullptr;
        for (int i = 0; i < n; ++i)
        {
            left[i] = (float) blockL_[(size_t) i];
            if (right) right[i] = (float) blockR_[(size_t) i];
        }
        for (int ch = buffer.getNumChannels() > 1 ? 2 : 1; ch < buffer.getNumChannels(); ++ch)
            buffer.clear(ch, 0, n);
    }

    // D-022 canonical XML state: <PsychobillySlapBass schema="1"><PARAM .../>
    void getStateInformation(juce::MemoryBlock& destData) override
    {
        juce::XmlElement root("PsychobillySlapBass");
        root.setAttribute("schema", 1);
        for (const char* id : kParamIds)
        {
            auto* param = apvts.getParameter(id);
            auto* child = root.createNewChildElement("PARAM");
            child->setAttribute("id", id);
            child->setAttribute("value", param != nullptr ? (double) param->getValue() : 0.0);
        }
        copyXmlToBinary(root, destData);
    }

    void setStateInformation(const void* data, int sizeInBytes) override
    {
        std::unique_ptr<juce::XmlElement> root(getXmlFromBinary(data, sizeInBytes));
        if (root == nullptr || !root->hasTagName("PsychobillySlapBass")
            || root->getIntAttribute("schema") != 1)
            return; // invalid state leaves active audio unchanged (D-012)
        for (auto* child : root->getChildIterator())
        {
            if (child->getTagName() != "PARAM") continue;
            const juce::String id = child->getStringAttribute("id");
            const double value = child->getDoubleAttribute("value", -1.0);
            if (auto* param = apvts.getParameter(id))
                if (value >= 0.0 && value <= 1.0 && std::isfinite(value))
                    param->setValueNotifyingHost((float) value);
        }
    }

private:
    void pullControls()
    {
        psb::Controls c;
        c.pluck_slap = apvts.getRawParameterValue("pluck_slap")->load();
        c.slap_brightness = apvts.getRawParameterValue("slap_brightness")->load();
        c.body_resonance = apvts.getRawParameterValue("body_resonance")->load();
        c.sustain = apvts.getRawParameterValue("sustain")->load();
        c.string_tension = apvts.getRawParameterValue("string_tension")->load();
        c.attack_noise = apvts.getRawParameterValue("attack_noise")->load();
        c.mechanical_noise = apvts.getRawParameterValue("mechanical_noise")->load();
        c.output_level = apvts.getRawParameterValue("output_level")->load();
        engine_.setControls(c);
    }

    psb::Engine engine_;
    juce::AudioProcessorValueTreeState apvts;
    std::vector<double> blockL_, blockR_;
    std::array<int, 16> gestureForChannel_{};
};

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter()
{
    return new PsychobillySlapBassProcessor();
}
