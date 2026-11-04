// Psychobilly Slap Bass 0.1.0 — VST3 processor (D-020/D-021/D-022/D-023).
// Headless: no editor. All state lives in the host; the audio thread performs
// no allocation, locking, file or network access (A-006).
#pragma once

#include "../psb_engine.h"

#include <juce_audio_processors/juce_audio_processors.h>
#include <juce_audio_utils/juce_audio_utils.h>

class PsychobillySlapBassProcessor : public juce::AudioProcessor {
public:
    PsychobillySlapBassProcessor();
    ~PsychobillySlapBassProcessor() override = default;

    void prepareToPlay(double sampleRate, int samplesPerBlock) override;
    void releaseResources() override {}
    bool isBusesLayoutSupported(const BusesLayout& layouts) const override;
    void processBlock(juce::AudioBuffer<float>&, juce::MidiBuffer&) override;
    void processBlock(juce::AudioBuffer<double>&, juce::MidiBuffer&) override;

    juce::AudioProcessorEditor* createEditor() override { return nullptr; }
    bool hasEditor() const override { return false; }

    const juce::String getName() const override { return JucePlugin_Name; }
    bool acceptsMidi() const override { return true; }
    bool producesMidi() const override { return false; }
    bool isMidiEffect() const override { return false; }
    double getTailLengthSeconds() const override { return 6.0; }

    int getNumPrograms() override { return 1; }
    int getCurrentProgram() override { return 0; }
    void setCurrentProgram(int) override {}
    const juce::String getProgramName(int) override { return {}; }
    void changeProgramName(int, const juce::String&) override {}

    void getStateInformation(juce::MemoryBlock& destData) override;
    void setStateInformation(const void* data, int sizeInBytes) override;

    static juce::AudioProcessorValueTreeState::ParameterLayout createParameterLayout();

    juce::AudioProcessorValueTreeState apvts;

private:
    template <typename FloatType>
    void process(juce::AudioBuffer<FloatType>&, juce::MidiBuffer&);

    psb::Engine engine_;
    double lastSampleRate_ = 0.0;
    float pitchBendSemis_ = 0.0f;
    std::uint32_t noteSeedCounter_ = 0;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(PsychobillySlapBassProcessor)
};
