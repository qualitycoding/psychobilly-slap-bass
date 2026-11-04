#include "PsychobillySlapBassProcessor.h"

namespace {

psb::ControlSet controlsFromApvts(juce::AudioProcessorValueTreeState& apvts) {
    float values[psb::kParamCount];
    for (int i = 0; i < psb::kParamCount; ++i) {
        const auto* param = apvts.getRawParameterValue(psb::kParamIds[static_cast<std::size_t>(i)]);
        values[i] = param != nullptr ? juce::jlimit(0.0f, 1.0f, param->load()) : psb::kParamDefaults[static_cast<std::size_t>(i)];
    }
    return psb::ControlSet::fromArray(values);
}

} // namespace

PsychobillySlapBassProcessor::PsychobillySlapBassProcessor()
    : AudioProcessor(BusesProperties().withOutput("Output", juce::AudioChannelSet::stereo(), true)),
      apvts(*this, nullptr, "PARAMS", createParameterLayout()) {}

juce::AudioProcessorValueTreeState::ParameterLayout PsychobillySlapBassProcessor::createParameterLayout() {
    std::vector<std::unique_ptr<juce::RangedAudioParameter>> params;
    for (int i = 0; i < psb::kParamCount; ++i) {
        params.push_back(std::make_unique<juce::AudioParameterFloat>(
            juce::ParameterID(psb::kParamIds[static_cast<std::size_t>(i)], 1),
            psb::kParamIds[static_cast<std::size_t>(i)],
            juce::NormalisableRange<float>(0.0f, 1.0f, 0.001f),
            psb::kParamDefaults[static_cast<std::size_t>(i)]));
    }
    return {params.begin(), params.end()};
}

bool PsychobillySlapBassProcessor::isBusesLayoutSupported(const BusesLayout& layouts) const {
    return layouts.getMainOutputChannelSet() == juce::AudioChannelSet::stereo()
        && layouts.getMainInputChannelSet() == juce::AudioChannelSet::disabled();
}

void PsychobillySlapBassProcessor::prepareToPlay(double sampleRate, int) {
    engine_.prepare(sampleRate, controlsFromApvts(apvts));
}

template <typename FloatType>
void PsychobillySlapBassProcessor::process(juce::AudioBuffer<FloatType>& buffer,
                                           juce::MidiBuffer& midi) {
    const int numSamples = buffer.getNumSamples();
    if (buffer.getNumChannels() < 2)
        return;

    // Host-safe parameter reads (std::atomic<float>*, D-021/D-018 claim C-018).
    // Re-prepare only when the sample rate changed; preparation resets voices.
    if (getSampleRate() != lastSampleRate_) {
        lastSampleRate_ = getSampleRate();
        engine_.prepare(getSampleRate(), controlsFromApvts(apvts));
    } else {
        engine_.setControls(controlsFromApvts(apvts));
    }

    std::vector<psb::NoteEvent> events;
    events.reserve(static_cast<std::size_t>(midi.getNumEvents()) + 1);
    for (const auto metadata : midi) {
        const auto& message = metadata.getMessage();
        const int sample = metadata.samplePosition;
        if (message.isNoteOn()) {
            events.push_back({sample, psb::NoteEvent::Type::note_on,
                              message.getChannel(), message.getNoteNumber(),
                              juce::jlimit(0.0f, 1.0f, message.getFloatVelocity())});
        } else if (message.isNoteOff()) {
            events.push_back({sample, psb::NoteEvent::Type::note_off,
                              message.getChannel(), message.getNoteNumber(), 0.0f});
        } else if (message.isPitchWheel()) {
            // 14-bit pitch bend, centre 8192, +/-2 semitones (D-020/D-023).
            const float normalised = (static_cast<float>(message.getPitchWheelValue()) - 8192.0f) / 8192.0f;
            pitchBendSemis_ = juce::jlimit(-2.0f, 2.0f, normalised * 2.0f);
        }
    }

    // Sample-accurate ordering with stable equal-sample order (D-023).
    std::stable_sort(events.begin(), events.end(),
                     [](const psb::NoteEvent& a, const psb::NoteEvent& b) {
                         return a.sample < b.sample;
                     });
    engine_.setEvents(events);
    engine_.setSeed(0x50534c41u);
    std::vector<float> left(static_cast<std::size_t>(numSamples)),
        right(static_cast<std::size_t>(numSamples));
    engine_.render(left.data(), right.data(), nullptr, numSamples);

    for (int i = 0; i < numSamples; ++i) {
        buffer.setSample(0, i, static_cast<FloatType>(left[static_cast<std::size_t>(i)]));
        buffer.setSample(1, i, static_cast<FloatType>(right[static_cast<std::size_t>(i)]));
    }
}

void PsychobillySlapBassProcessor::processBlock(juce::AudioBuffer<float>& buffer,
                                                juce::MidiBuffer& midi) {
    process(buffer, midi);
}

void PsychobillySlapBassProcessor::processBlock(juce::AudioBuffer<double>& buffer,
                                                juce::MidiBuffer& midi) {
    process(buffer, midi);
}

void PsychobillySlapBassProcessor::getStateInformation(juce::MemoryBlock& destData) {
    // Canonical D-022 XML state (all eight parameters, frozen order).
    juce::XmlElement root("PsychobillySlapBass");
    root.setAttribute("schema", "1");
    for (int i = 0; i < psb::kParamCount; ++i) {
        auto* param = root.createNewChildElement("PARAM");
        param->setAttribute("id", psb::kParamIds[static_cast<std::size_t>(i)]);
        param->setAttribute("value",
            juce::String(apvts.getRawParameterValue(psb::kParamIds[static_cast<std::size_t>(i)])->load()));
    }
    copyXmlToBinary(root, destData);
}

void PsychobillySlapBassProcessor::setStateInformation(const void* data, int sizeInBytes) {
    // Fail closed (D-012/D-022): malformed or future-schema state leaves the
    // active processor state unchanged and throws nothing across the boundary.
    if (sizeInBytes <= 0 || sizeInBytes > 65536)
        return;
    std::unique_ptr<juce::XmlElement> root(getXmlFromBinary(data, static_cast<size_t>(sizeInBytes)));
    if (root == nullptr || !root->hasTagName("PsychobillySlapBass")
        || root->getStringAttribute("schema") != "1")
        return;
    if (root->getNumChildElements() != psb::kParamCount)
        return;
    for (int i = 0; i < psb::kParamCount; ++i) {
        auto* param = root->getChildElement(i);
        if (param == nullptr || !param->hasTagName("PARAM")
            || param->getStringAttribute("id") != psb::kParamIds[static_cast<std::size_t>(i)]
            || param->getNumChildElements() != 0)
            return;
        const float value = param->getDoubleAttribute("value", -1.0);
        if (value < 0.0f || value > 1.0f || !std::isfinite(value))
            return;
    }
    for (int i = 0; i < psb::kParamCount; ++i) {
        auto* param = root->getChildElement(i);
        if (auto* target = apvts.getParameter(psb::kParamIds[static_cast<std::size_t>(i)]))
            target->setValueNotifyingHost(juce::jlimit(0.0f, 1.0f,
                static_cast<float>(param->getDoubleAttribute("value"))));
    }
}

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter() {
    return new PsychobillySlapBassProcessor();
}
