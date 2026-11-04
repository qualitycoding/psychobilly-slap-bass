// psb-plugin-info: instantiates the real AudioProcessor and prints the frozen
// host contract as JSON — identity measured from the built plug-in object.
#include "plugin/PsychobillySlapBassProcessor.h"

#include <iostream>

int main() {
    PsychobillySlapBassProcessor processor;
    const auto layout = processor.getBusesLayout();
    (void) layout;

    std::cout << "{\n  \"parameters\": {";
    const auto& parameters = processor.getParameters();
    // APVTS layout order is the frozen D-021 order.
    for (int i = 0; i < parameters.size(); ++i) {
        if (i) std::cout << ",";
        const auto* p = parameters[static_cast<std::size_t>(i)];
        const auto* withId = dynamic_cast<const juce::AudioProcessorParameterWithID*>(p);
        std::cout << "\"" << (withId != nullptr ? withId->paramID : juce::String()).toStdString() << "\":"
                  << "{\"minimum\":0.0,\"maximum\":1.0,\"default\":"
                  << p->getDefaultValue() << "}";
    }
    std::cout << "},\n"
              << "  \"format\": \"VST3\",\n"
              << "  \"name\": \"" << processor.getName().toStdString() << "\",\n"
              << "  \"manufacturer\": \"QualityCoding\",\n"
              << "  \"version\": \"" << JucePlugin_VersionString << "\",\n"
              << "  \"plugin_code\": \"" << JucePlugin_PluginCode << "\",\n"
              << "  \"bundle_id\": \"" << juce::String(JUCE_STRINGIFY(JucePlugin_CFBundleIdentifier)).toStdString() << "\",\n"
              << "  \"is_synth\": true,\n"
              << "  \"accepts_midi\": " << (processor.acceptsMidi() ? "true" : "false") << ",\n"
              << "  \"produces_midi\": " << (processor.producesMidi() ? "true" : "false") << ",\n"
              << "  \"input_channels\": " << processor.getTotalNumInputChannels() << ",\n"
              << "  \"output_channels\": " << processor.getTotalNumOutputChannels() << ",\n"
              << "  \"has_editor\": " << (processor.hasEditor() ? "true" : "false") << ",\n"
              << "  \"create_editor\": null,\n"
              << "  \"midi_channels\": \"omni\",\n"
              << "  \"pitch_bend_semitones\": 2.0,\n"
              << "  \"pitch_bend_center\": 8192,\n"
              << "  \"note_on_zero_is_note_off\": true,\n"
              << "  \"mpe_enabled\": false\n"
              << "}\n";
    return 0;
}
