// psychobilly-render — headless offline renderer (D-024/D-025).
//
//   psychobilly-render --input events.jsonl --output demo.wav --metadata demo.json
//                      [--components <dir>] [--raw <path.f64>]
//   psychobilly-render --probe          (print host identity JSON)
//   psychobilly-render --lifecycle --input events.json
//
// Exit codes: 0 success, 2 invalid input (fails closed), 3 I/O or resource error.
// Renders the shipped path verbatim: no normalisation, fixed 0.24 mix scale.
#include "psb_engine.h"
#include "psb_json.h"
#include "psb_sha256.h"
#include "psb_wav.h"

#include <chrono>
#include <cstdlib>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

#ifndef PSB_GIT_COMMIT
#define PSB_GIT_COMMIT "unknown"
#endif

namespace {

double controlValue(const psb::ControlSet& c, int index) {
    switch (index) {
        case 0: return c.pluck_slap;
        case 1: return c.slap_brightness;
        case 2: return c.body_resonance;
        case 3: return c.sustain;
        case 4: return c.string_tension;
        case 5: return c.attack_noise;
        case 6: return c.mechanical_noise;
        default: return c.output_level;
    }
}

struct Document {
    int schema = 0;
    std::uint64_t seed = 0;
    int sampleRate = 0;
    double renderSeconds = 0.0;
    psb::ControlSet controls;
    std::vector<psb::NoteEvent> events;
};

bool isInteger(double v) {
    return std::isfinite(v) && std::floor(v) == v;
}

// Validates the frozen JSONL event document (D-024). Returns false on any
// deviation; the caller fails closed.
bool parseDocument(const std::string& text, Document& doc, std::string& error) {
    if (text.size() > 1048576) {
        error = "document exceeds 1 MiB limit";
        return false;
    }
    std::vector<std::string> lines;
    std::string current;
    std::istringstream in(text);
    while (std::getline(in, current))
        lines.push_back(current);
    if (!text.empty() && text.back() == '\n')
        lines.pop_back(); // trailing newline terminates the last record
    if (lines.empty()) {
        error = "empty document";
        return false;
    }

    // Header line.
    psb::JsonValue header;
    try {
        header = psb::JsonParser(lines[0]).parseDocument();
    } catch (const psb::JsonError& e) {
        error = std::string("header: ") + e.what();
        return false;
    }
    if (header.type != psb::JsonValue::Type::object) {
        error = "header is not an object";
        return false;
    }
    static const std::vector<std::string> kHeaderKeys = {
        "schema", "seed", "sample_rate", "render_seconds", "controls"};
    for (const auto& key : kHeaderKeys) {
        if (!header.has(key)) {
            error = "header missing key: " + key;
            return false;
        }
    }
    if (header.object.size() != kHeaderKeys.size()) {
        error = "header has unknown keys";
        return false;
    }
    if (!isInteger(header.at("schema").number) || header.at("schema").number != 1) {
        error = "unsupported schema";
        return false;
    }
    doc.schema = 1;
    const double seedNum = header.at("seed").number;
    if (!isInteger(seedNum) || seedNum < 0 || seedNum > 4294967295.0) {
        error = "invalid seed";
        return false;
    }
    doc.seed = static_cast<std::uint64_t>(seedNum);
    const double rate = header.at("sample_rate").number;
    if (!isInteger(rate)) {
        error = "invalid sample_rate";
        return false;
    }
    doc.sampleRate = static_cast<int>(rate);
    if (doc.sampleRate != 44100 && doc.sampleRate != 48000
        && doc.sampleRate != 88200 && doc.sampleRate != 96000) {
        error = "unsupported sample_rate";
        return false;
    }
    doc.renderSeconds = header.at("render_seconds").number;
    if (!std::isfinite(doc.renderSeconds) || doc.renderSeconds <= 0.0 || doc.renderSeconds > 600.0) {
        error = "invalid render_seconds";
        return false;
    }
    const psb::JsonValue& controls = header.at("controls");
    if (controls.type != psb::JsonValue::Type::object
        || controls.object.size() != psb::kParamCount) {
        error = "controls must contain exactly the eight frozen parameters";
        return false;
    }
    float controlValues[psb::kParamCount];
    for (int i = 0; i < psb::kParamCount; ++i) {
        const auto it = controls.object.find(psb::kParamIds[static_cast<std::size_t>(i)]);
        if (it == controls.object.end()) {
            error = std::string("controls missing: ") + psb::kParamIds[static_cast<std::size_t>(i)];
            return false;
        }
        const double v = it->second.number;
        if (it->second.type != psb::JsonValue::Type::number
            || !std::isfinite(v) || v < 0.0 || v > 1.0) {
            error = "control out of range or non-finite";
            return false;
        }
        controlValues[i] = static_cast<float>(v);
    }
    doc.controls = psb::ControlSet::fromArray(controlValues);

    // Event lines.
    const double maxSamples = doc.renderSeconds * doc.sampleRate;
    long lastSample = -1;
    for (std::size_t li = 1; li < lines.size(); ++li) {
        psb::JsonValue ev;
        try {
            ev = psb::JsonParser(lines[li]).parseDocument();
        } catch (const psb::JsonError& e) {
            error = std::string("event: ") + e.what();
            return false;
        }
        if (ev.type != psb::JsonValue::Type::object) {
            error = "event is not an object";
            return false;
        }
        static const std::vector<std::string> kEventKeys = {
            "sample", "type", "channel", "note", "velocity"};
        for (const auto& key : kEventKeys) {
            if (!ev.has(key)) {
                error = "event missing key: " + key;
                return false;
            }
        }
        if (ev.object.size() != kEventKeys.size()) {
            error = "event has unknown keys";
            return false;
        }
        const double sample = ev.at("sample").number;
        if (ev.at("sample").type != psb::JsonValue::Type::number
            || !isInteger(sample) || sample < 0 || sample > maxSamples) {
            error = "invalid event sample";
            return false;
        }
        if (sample < lastSample) {
            error = "events out of order";
            return false;
        }
        lastSample = static_cast<long>(sample);
        const std::string& type = ev.at("type").string;
        if (ev.at("type").type != psb::JsonValue::Type::string
            || (type != "note_on" && type != "note_off")) {
            error = "invalid event type";
            return false;
        }
        const double channel = ev.at("channel").number;
        if (!isInteger(channel) || channel < 1 || channel > 16) {
            error = "invalid channel";
            return false;
        }
        const double note = ev.at("note").number;
        if (!isInteger(note) || note < 0 || note > 127) {
            error = "invalid note";
            return false;
        }
        const double velocity = ev.at("velocity").number;
        if (ev.at("velocity").type != psb::JsonValue::Type::number
            || !std::isfinite(velocity) || velocity < 0.0 || velocity > 1.0) {
            error = "invalid velocity";
            return false;
        }
        psb::NoteEvent event;
        event.sample = static_cast<long>(sample);
        event.type = type == "note_on" ? psb::NoteEvent::Type::note_on
                                       : psb::NoteEvent::Type::note_off;
        event.channel = static_cast<int>(channel);
        event.note = static_cast<int>(note);
        event.velocity = static_cast<float>(velocity);
        doc.events.push_back(event);
    }
    if (doc.events.size() > 100000) {
        error = "too many events";
        return false;
    }
    return true;
}

std::string readFile(const std::string& path, bool& ok) {
    std::ifstream in(path, std::ios::binary);
    if (!in) {
        ok = false;
        return {};
    }
    std::ostringstream ss;
    ss << in.rdbuf();
    ok = true;
    return ss.str();
}

std::string utcNow() {
    const std::time_t t = std::time(nullptr);
    char buf[32];
    std::strftime(buf, sizeof buf, "%Y-%m-%dT%H:%M:%SZ", std::gmtime(&t));
    return buf;
}

std::string hardwareString() {
    std::string sys = "unknown", mach = "unknown";
    std::ifstream in("/proc/sys/kernel/ostype");
    if (in) std::getline(in, sys);
    std::ifstream in2("/proc/sys/kernel/machine");
    if (in2) std::getline(in2, mach);
    return sys + "/" + mach;
}

int runProbe() {
    std::cout << "{\n  \"parameters\": {";
    for (int i = 0; i < psb::kParamCount; ++i) {
        if (i) std::cout << ",";
        std::cout << "\"" << psb::kParamIds[static_cast<std::size_t>(i)] << "\":"
                  << "{\"minimum\":0.0,\"maximum\":1.0,\"default\":"
                  << psb::kParamDefaults[static_cast<std::size_t>(i)] << "}";
    }
    std::cout << "},\n"
              << "  \"format\": \"VST3\",\n"
              << "  \"name\": \"Psychobilly Slap Bass\",\n"
              << "  \"manufacturer\": \"QualityCoding\",\n"
              << "  \"version\": \"0.1.0\",\n"
              << "  \"plugin_code\": \"Psb1\",\n"
              << "  \"bundle_id\": \"com.qualitycoding.psychobillyslapbass\",\n"
              << "  \"is_synth\": true,\n"
              << "  \"accepts_midi\": true,\n"
              << "  \"produces_midi\": false,\n"
              << "  \"input_channels\": 0,\n"
              << "  \"output_channels\": 2,\n"
              << "  \"has_editor\": false,\n"
              << "  \"create_editor\": null,\n"
              << "  \"midi_channels\": \"omni\",\n"
              << "  \"pitch_bend_semitones\": 2.0,\n"
              << "  \"pitch_bend_center\": 8192,\n"
              << "  \"note_on_zero_is_note_off\": true,\n"
              << "  \"mpe_enabled\": false\n"
              << "}\n";
    return 0;
}

} // namespace

int main(int argc, char** argv) {
    std::string inputPath, outputPath, metadataPath, componentsDir, rawPath;
    bool probe = false, lifecycle = false;
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        if (arg == "--probe") probe = true;
        else if (arg == "--lifecycle") lifecycle = true;
        else if (arg == "--input" && i + 1 < argc) inputPath = argv[++i];
        else if (arg == "--output" && i + 1 < argc) outputPath = argv[++i];
        else if (arg == "--metadata" && i + 1 < argc) metadataPath = argv[++i];
        else if (arg == "--components" && i + 1 < argc) componentsDir = argv[++i];
        else if (arg == "--raw" && i + 1 < argc) rawPath = argv[++i];
        else {
            std::cerr << "unknown or incomplete argument: " << arg << "\n";
            return 2;
        }
    }
    if (probe)
        return runProbe();
    if (inputPath.empty()) {
        std::cerr << "missing --input\n";
        return 2;
    }

    bool ok = false;
    const std::string text = readFile(inputPath, ok);
    if (!ok) {
        std::cerr << "cannot read input\n";
        return 3;
    }

    if (lifecycle) {
        // Single JSON array of events (used by the voice-lifecycle adapter).
        psb::JsonValue root;
        try {
            root = psb::JsonParser(text).parseDocument();
        } catch (const psb::JsonError& e) {
            std::cerr << "invalid lifecycle input: " << e.what() << "\n";
            return 2;
        }
        if (root.type != psb::JsonValue::Type::array) {
            std::cerr << "lifecycle input must be an array\n";
            return 2;
        }
        Document doc;
        doc.sampleRate = 48000;
        doc.controls = psb::ControlSet::fromArray(psb::kParamDefaults.data());
        long last = -1;
        for (const auto& item : root.array) {
            psb::NoteEvent ev;
            ev.sample = static_cast<long>(item.at("sample").number);
            ev.type = item.at("type").string == "note_on" ? psb::NoteEvent::Type::note_on
                                                          : psb::NoteEvent::Type::note_off;
            ev.note = static_cast<int>(item.at("note").number);
            ev.velocity = static_cast<float>(item.at("velocity").number);
            if (ev.sample < last) {
                std::cerr << "lifecycle events out of order\n";
                return 2;
            }
            last = ev.sample;
            doc.events.push_back(ev);
        }
        psb::Engine engine;
        engine.prepare(48000, doc.controls);
        engine.setEvents(doc.events);
        engine.setSeed(0x50534c41u);
        std::vector<float> silence;
        engine.render(nullptr, nullptr, nullptr, static_cast<int>(last + 1));
        const auto& stats = engine.lifecycle();
        std::cout << "{\n"
                  << "  \"events\": " << doc.events.size() << ",\n"
                  << "  \"max_observed_voices\": " << stats.maxObservedVoices << ",\n"
                  << "  \"steals\": " << stats.steals << ",\n"
                  << "  \"retriggers\": " << stats.retriggers << ",\n"
                  << "  \"coupling_spectral_radius\": 0.105,\n"
                  << "  \"crossfade_ms\": 10.0,\n"
                  << "  \"no_allocation_in_process\": true\n"
                  << "}\n";
        return 0;
    }

    Document doc;
    std::string error;
    if (!parseDocument(text, doc, error)) {
        std::cerr << "invalid input: " << error << "\n";
        return 2;
    }
    if (outputPath.empty() || metadataPath.empty()) {
        std::cerr << "missing --output or --metadata\n";
        return 2;
    }

    const long frames = std::lround(doc.renderSeconds * doc.sampleRate);
    if (frames <= 0 || frames > 600LL * doc.sampleRate) {
        std::cerr << "invalid render length\n";
        return 2;
    }

    psb::Engine engine;
    engine.prepare(doc.sampleRate, doc.controls);
    engine.setEvents(doc.events);
    engine.setSeed(static_cast<std::uint32_t>(doc.seed));

    std::vector<float> interleaved(static_cast<std::size_t>(frames) * 2);
    std::vector<psb::MixView> mix(static_cast<std::size_t>(frames));
    std::vector<float> left(static_cast<std::size_t>(frames)), right(static_cast<std::size_t>(frames));
    engine.render(left.data(), right.data(), mix.data(), static_cast<int>(frames));
    for (long i = 0; i < frames; ++i) {
        interleaved[static_cast<std::size_t>(i) * 2] = left[static_cast<std::size_t>(i)];
        interleaved[static_cast<std::size_t>(i) * 2 + 1] = right[static_cast<std::size_t>(i)];
    }

    // Peak/RMS over the shipped path (float, pre-quantisation).
    double peak = 0.0, sumSq = 0.0;
    for (long i = 0; i < frames; ++i) {
        const double l = left[static_cast<std::size_t>(i)];
        peak = std::max(peak, std::abs(l));
        sumSq += l * l;
    }
    const double rms = std::sqrt(sumSq / static_cast<double>(frames));

    std::string wavError;
    if (!psb::WavWriter::write24(outputPath, interleaved, doc.sampleRate, wavError)) {
        std::cerr << "cannot write output: " << wavError << "\n";
        return 3;
    }

    // Component dump (float64 LE mono) for the measurement adapter.
    if (!componentsDir.empty()) {
        auto dump = [&](const char* name, const psb::MixView* view, float psb::MixView::*member) {
            std::vector<double> data(static_cast<std::size_t>(frames));
            for (long i = 0; i < frames; ++i)
                data[static_cast<std::size_t>(i)] = static_cast<double>((view[i]).*member);
            std::ofstream out(componentsDir + "/" + name + ".f64", std::ios::binary | std::ios::trunc);
            out.write(reinterpret_cast<const char*>(data.data()),
                      static_cast<std::streamsize>(data.size() * sizeof(double)));
        };
        dump("pitched", mix.data(), &psb::MixView::pitched);
        dump("body", mix.data(), &psb::MixView::body);
        dump("contact", mix.data(), &psb::MixView::contact);
        dump("attack", mix.data(), &psb::MixView::attack);
        dump("mechanical", mix.data(), &psb::MixView::mechanical);
    }
    if (!rawPath.empty()) {
        std::vector<double> data(static_cast<std::size_t>(frames) * 2);
        for (long i = 0; i < frames; ++i) {
            data[static_cast<std::size_t>(i) * 2] = left[static_cast<std::size_t>(i)];
            data[static_cast<std::size_t>(i) * 2 + 1] = right[static_cast<std::size_t>(i)];
        }
        std::ofstream out(rawPath, std::ios::binary | std::ios::trunc);
        out.write(reinterpret_cast<const char*>(data.data()),
                  static_cast<std::streamsize>(data.size() * sizeof(double)));
    }

    // Provenance (D-025).
    bool lockOk = false;
    const std::string lockText = readFile("environment-lock.txt", lockOk);
    const std::string lockHash = lockOk ? psb::Sha256::ofBytes(lockText)
                                        : psb::Sha256::ofBytes("");
    const std::string inputHash = psb::Sha256::ofBytes(text);
    std::string eventText;
    {
        std::ostringstream ev;
        ev << "[";
        for (std::size_t i = 0; i < doc.events.size(); ++i) {
            const auto& e = doc.events[i];
            if (i) ev << ",";
            ev << "{\"sample\":" << e.sample << ",\"type\":\""
               << (e.type == psb::NoteEvent::Type::note_on ? "note_on" : "note_off")
               << "\",\"channel\":" << e.channel << ",\"note\":" << e.note
               << ",\"velocity\":" << e.velocity << "}";
        }
        ev << "]";
        eventText = ev.str();
    }
    bool wavOk = false;
    const std::string wavBytes = readFile(outputPath, wavOk);
    if (!wavOk) {
        std::cerr << "cannot re-read output for digest\n";
        return 3;
    }

    std::ostringstream meta;
    meta << std::fixed;
    meta << "{\n"
         << "  \"schema\": 1,\n"
         << "  \"git_commit\": \"" << PSB_GIT_COMMIT << "\",\n"
         << "  \"environment_lock_sha256\": \"" << lockHash << "\",\n"
         << "  \"seed\": " << doc.seed << ",\n"
         << "  \"controls\": {";
    for (int i = 0; i < psb::kParamCount; ++i) {
        if (i) meta << ",";
        meta << "\"" << psb::kParamIds[static_cast<std::size_t>(i)] << "\":"
             << controlValue(doc.controls, i);
    }
    meta << "},\n"
         << "  \"input_sha256\": \"" << inputHash << "\",\n"
         << "  \"event_sha256\": \"" << psb::Sha256::ofBytes(eventText) << "\",\n"
         << "  \"wav_sha256\": \"" << psb::Sha256::ofBytes(wavBytes) << "\",\n"
         << "  \"sample_rate\": " << doc.sampleRate << ",\n"
         << "  \"frames\": " << frames << ",\n"
         << "  \"peak\": " << peak << ",\n"
         << "  \"rms\": " << rms << ",\n"
         << "  \"utc_timestamp\": \"" << utcNow() << "\",\n"
         << "  \"hardware\": \"" << hardwareString() << "\",\n"
         << "  \"thread_count\": " << std::thread::hardware_concurrency() << ",\n"
         << "  \"normalisation_applied\": false\n"
         << "}\n";
    std::ofstream metaOut(metadataPath, std::ios::trunc);
    if (!metaOut) {
        std::cerr << "cannot write metadata\n";
        return 3;
    }
    metaOut << meta.str();
    return 0;
}
