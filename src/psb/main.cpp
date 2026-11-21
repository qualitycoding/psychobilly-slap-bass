// psychobilly-render — offline renderer, raw adapter bridge, voice-lifecycle
// reporter and native benchmark for the Psychobilly Slap Bass engine.
// AGPL-3.0-only.
//
// D-024 CLI:   psychobilly-render --input events.jsonl --output demo.wav --metadata demo.json
// Exit codes: 0 success, 2 invalid input/path/validation, 3 internal failure.
#include "engine.h"
#include "json.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

namespace
{

// ---------------- SHA-256 (public domain style implementation) ----------------
class Sha256
{
public:
    Sha256() { reset(); }
    void reset()
    {
        h_[0] = 0x6a09e667; h_[1] = 0xbb67ae85; h_[2] = 0x3c6ef372; h_[3] = 0xa54ff53a;
        h_[4] = 0x510e527f; h_[5] = 0x9b05688c; h_[6] = 0x1f83d9ab; h_[7] = 0x5be0cd19;
        total_ = 0;
        buflen_ = 0;
    }
    void update(const uint8_t* data, size_t len)
    {
        total_ += len;
        while (len--)
        {
            buf_[buflen_++] = *data++;
            if (buflen_ == 64) { transform(); buflen_ = 0; }
        }
    }
    std::string hexDigest()
    {
        uint64_t bits = total_ * 8;
        uint8_t pad = 0x80;
        update(&pad, 1);
        uint8_t zero = 0;
        while (buflen_ != 56) update(&zero, 1);
        uint8_t lenb[8];
        for (int i = 0; i < 8; ++i) lenb[i] = (uint8_t) (bits >> (56 - 8 * i));
        // bypass total_ accounting trick: manual
        for (auto b : lenb) { buf_[buflen_++] = b; if (buflen_ == 64) { transform(); buflen_ = 0; } }
        std::string out;
        char tmp[8];
        for (uint32_t x : h_) { snprintf(tmp, sizeof tmp, "%08x", x); out += tmp; }
        return out;
    }
    static std::string ofFile(const std::string& path)
    {
        std::ifstream f(path, std::ios::binary);
        Sha256 s;
        char buf[65536];
        while (f) { f.read(buf, sizeof buf); s.update((const uint8_t*) buf, (size_t) f.gcount()); }
        return s.hexDigest();
    }
    static std::string ofString(const std::string& s_)
    {
        Sha256 s;
        s.update((const uint8_t*) s_.data(), s_.size());
        return s.hexDigest();
    }
    static std::string ofVector(const std::vector<double>& v)
    {
        Sha256 s;
        s.update((const uint8_t*) v.data(), v.size() * sizeof(double));
        return s.hexDigest();
    }

private:
    uint32_t h_[8];
    uint8_t buf_[64];
    size_t buflen_ = 0;
    uint64_t total_ = 0;

    static uint32_t rotr(uint32_t x, int n) { return (x >> n) | (x << (32 - n)); }
    void transform()
    {
        static const uint32_t k[64] = {
            0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
            0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
            0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
            0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
            0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
            0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
            0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
            0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
        uint32_t w[64];
        for (int i = 0; i < 16; ++i)
            w[i] = ((uint32_t) buf_[i * 4] << 24) | ((uint32_t) buf_[i * 4 + 1] << 16)
                 | ((uint32_t) buf_[i * 4 + 2] << 8) | buf_[i * 4 + 3];
        for (int i = 16; i < 64; ++i)
        {
            const uint32_t s0 = rotr(w[i - 15], 7) ^ rotr(w[i - 15], 18) ^ (w[i - 15] >> 3);
            const uint32_t s1 = rotr(w[i - 2], 17) ^ rotr(w[i - 2], 19) ^ (w[i - 2] >> 10);
            w[i] = w[i - 16] + s0 + w[i - 7] + s1;
        }
        uint32_t a = h_[0], b = h_[1], c = h_[2], d = h_[3], e = h_[4], f = h_[5], g = h_[6], h = h_[7];
        for (int i = 0; i < 64; ++i)
        {
            const uint32_t s1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
            const uint32_t ch = (e & f) ^ (~e & g);
            const uint32_t t1 = h + s1 + ch + k[i] + w[i];
            const uint32_t s0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
            const uint32_t maj = (a & b) ^ (a & c) ^ (b & c);
            const uint32_t t2 = s0 + maj;
            h = g; g = f; f = e; e = d + t1; d = c; c = b; b = a; a = t1 + t2;
        }
        h_[0] += a; h_[1] += b; h_[2] += c; h_[3] += d;
        h_[4] += e; h_[5] += f; h_[6] += g; h_[7] += h;
    }
};

std::string readFile(const std::string& path, bool* ok)
{
    std::ifstream f(path, std::ios::binary);
    if (!f) { if (ok) *ok = false; return {}; }
    std::ostringstream ss;
    ss << f.rdbuf();
    if (ok) *ok = true;
    return ss.str();
}

bool writeFile(const std::string& path, const std::string& data)
{
    std::ofstream f(path, std::ios::binary | std::ios::trunc);
    if (!f) return false;
    f.write(data.data(), (std::streamsize) data.size());
    return (bool) f;
}

// ---------------- 24-bit PCM WAV writer ----------------
bool writeWav24(const std::string& path, const std::vector<double>& interleaved,
                int sampleRate, std::string* error)
{
    const uint32_t channels = 2;
    const uint32_t frames = (uint32_t) (interleaved.size() / 2);
    const uint32_t bytesPerSample = 3;
    const uint32_t dataSize = frames * channels * bytesPerSample;
    std::ofstream f(path, std::ios::binary | std::ios::trunc);
    if (!f) { if (error) *error = "cannot open output"; return false; }
    auto w32 = [&f](uint32_t v) { char b[4] = {(char) (v & 0xff), (char) ((v >> 8) & 0xff), (char) ((v >> 16) & 0xff), (char) ((v >> 24) & 0xff)}; f.write(b, 4); };
    auto w16 = [&f](uint16_t v) { char b[2] = {(char) (v & 0xff), (char) ((v >> 8) & 0xff)}; f.write(b, 2); };
    f.write("RIFF", 4); w32(36 + dataSize); f.write("WAVE", 4);
    f.write("fmt ", 4); w32(16); w16(1); w16((uint16_t) channels);
    w32((uint32_t) sampleRate); w32((uint32_t) sampleRate * channels * bytesPerSample);
    w16((uint16_t) (channels * bytesPerSample)); w16(24);
    f.write("data", 4); w32(dataSize);
    for (double x : interleaved)
    {
        const double c = std::max(-1.0, std::min(1.0, x));
        int32_t s = (int32_t) std::lround(c * 8388607.0);
        char b[3] = {(char) (s & 0xff), (char) ((s >> 8) & 0xff), (char) ((s >> 16) & 0xff)};
        f.write(b, 3);
    }
    return (bool) f;
}

// ---------------- contract helpers ----------------
const char* kControlNames[8] = {"pluck_slap", "slap_brightness", "body_resonance", "sustain",
                                "string_tension", "attack_noise", "mechanical_noise", "output_level"};

bool parseControls(const psbjson::ValuePtr& v, psb::Controls& out, std::string* error)
{
    if (!v || v->type != psbjson::Value::Object) { if (error) *error = "controls must be an object"; return false; }
    if (v->object.size() != 8) { if (error) *error = "controls must have exactly eight parameters"; return false; }
    double vals[8];
    for (int i = 0; i < 8; ++i)
    {
        auto item = v->get(kControlNames[i]);
        if (!item || !item->isNumber()) { if (error) *error = std::string("missing or non-numeric control ") + kControlNames[i]; return false; }
        vals[i] = item->number;
        if (vals[i] < 0.0 || vals[i] > 1.0) { if (error) *error = std::string("control out of range ") + kControlNames[i]; return false; }
    }
    out.pluck_slap = vals[0]; out.slap_brightness = vals[1]; out.body_resonance = vals[2];
    out.sustain = vals[3]; out.string_tension = vals[4]; out.attack_noise = vals[5];
    out.mechanical_noise = vals[6]; out.output_level = vals[7];
    return true;
}

int gestureFromString(const std::string& g)
{
    if (g == "pluck") return 0;
    if (g == "pop") return 1;
    if (g == "slap") return 2;
    if (g == "ghost") return 3;
    return -1;
}

// strict per-event field validation shared by both event forms (D-024/D-041)
bool parseEventObject(const psbjson::ValuePtr& v, psb::Event& out, int schema, std::string* error)
{
    if (!v || v->type != psbjson::Value::Object) { if (error) *error = "event must be an object"; return false; }
    static const char* required[] = {"sample", "type", "channel", "note", "velocity"};
    for (auto* k : required)
        if (!v->has(k)) { if (error) *error = std::string("missing event field ") + k; return false; }
    for (const auto& kv : v->object)
        if (kv.first != "sample" && kv.first != "type" && kv.first != "channel" && kv.first != "note"
            && kv.first != "velocity" && kv.first != "gesture" && kv.first != "bend")
        { if (error) *error = "unknown event field " + kv.first; return false; }
    auto sample = v->get("sample");
    if (!sample->isNumber() || sample->number < 0 || sample->number != std::floor(sample->number))
    { if (error) *error = "bad event sample"; return false; }
    out.sample = (int64_t) sample->number;
    auto type = v->get("type");
    if (!type->isString()) { if (error) *error = "bad event type"; return false; }
    if (type->str == "note_on") out.type = psb::Event::note_on;
    else if (type->str == "note_off") out.type = psb::Event::note_off;
    else if (type->str == "pitch_bend") out.type = psb::Event::pitch_bend;
    else { if (error) *error = "unknown event type"; return false; }
    auto channel = v->get("channel");
    if (!channel->isNumber() || channel->number < 1 || channel->number > 16 || channel->number != std::floor(channel->number))
    { if (error) *error = "bad channel"; return false; }
    out.channel = (int) channel->number;
    auto note = v->get("note");
    if (!note->isNumber() || note->number < 0 || note->number > 127 || note->number != std::floor(note->number))
    { if (error) *error = "bad note"; return false; }
    out.note = (int) note->number;
    auto vel = v->get("velocity");
    if (!vel->isNumber() || vel->number < 0.0 || vel->number > 1.0) { if (error) *error = "bad velocity"; return false; }
    out.velocity = vel->number;
    if (v->has("gesture"))
    {
        if (schema < 2) { if (error) *error = "gesture requires schema 2"; return false; }
        auto g = v->get("gesture");
        if (g->isString())
        {
            out.gesture = gestureFromString(g->str);
            if (out.gesture < 0) { if (error) *error = "unknown gesture"; return false; }
        }
        else if (g->isNumber() && g->number >= 0 && g->number <= 3 && g->number == std::floor(g->number))
            out.gesture = (int) g->number;
        else { if (error) *error = "bad gesture"; return false; }
    }
    if (v->has("bend"))
    {
        auto b = v->get("bend");
        if (!b->isNumber() || b->number < 0 || b->number > 16383 || b->number != std::floor(b->number))
        { if (error) *error = "bad bend"; return false; }
        out.bend = (int) b->number;
    }
    return true;
}

std::string canonicalEventsJson(const std::vector<psb::Event>& events)
{
    std::string out = "[";
    bool first = true;
    for (const auto& e : events)
    {
        if (!first) out += ",";
        first = false;
        char buf[256];
        const char* types[] = {"note_on", "note_off", "pitch_bend"};
        snprintf(buf, sizeof buf,
                 R"({"sample":%lld,"type":"%s","channel":%d,"note":%d,"velocity":%.17g,"gesture":%d,"bend":%d})",
                 (long long) e.sample, types[(int) e.type], e.channel, e.note, e.velocity, e.gesture, e.bend);
        out += buf;
    }
    return out + "]";
}

std::string shellQuotelessEnv(const char* name)
{
    const char* v = std::getenv(name);
    return v ? v : "";
}

std::string gitCommit()
{
    std::string c = shellQuotelessEnv("PSB_GIT_COMMIT");
    if (!c.empty()) return c;
    return "unknown";
}

std::string hardwareString()
{
    bool ok = false;
    std::string cpu = readFile("/proc/cpuinfo", &ok);
    if (ok)
    {
        auto pos = cpu.find("model name");
        if (pos != std::string::npos)
        {
            auto colon = cpu.find(':', pos);
            auto eol = cpu.find('\n', colon);
            std::string m = cpu.substr(colon + 1, eol - colon - 1);
            while (!m.empty() && m.front() == ' ') m.erase(m.begin());
            if (!m.empty()) return m;
        }
    }
#ifdef _WIN32
    return "windows-x64";
#elif defined(__APPLE__)
    return "apple-silicon";
#else
    return "linux-x64";
#endif
}

int threadCount()
{
    return (int) std::thread::hardware_concurrency();
}

std::string utcNow()
{
    std::time_t t = std::time(nullptr);
    char buf[32];
    std::strftime(buf, sizeof buf, "%Y-%m-%dT%H:%M:%SZ", std::gmtime(&t));
    return buf;
}

std::string provenanceJson(const std::string& inputSha, const std::string& eventSha,
                           const std::string& wavSha, int rate, int64_t frames,
                           double peak, double rms, uint64_t seed,
                           const psb::Controls& controls, const std::string& lockHash)
{
    char buf[1024];
    snprintf(buf, sizeof buf,
        R"({"git_commit":"%s","environment_lock_sha256":"%s","seed":%llu,)"
        R"("controls":{"pluck_slap":%.17g,"slap_brightness":%.17g,"body_resonance":%.17g,)"
        R"("sustain":%.17g,"string_tension":%.17g,"attack_noise":%.17g,)"
        R"("mechanical_noise":%.17g,"output_level":%.17g},)"
        R"("input_sha256":"%s","event_sha256":"%s","wav_sha256":"%s",)"
        R"("sample_rate":%d,"frames":%lld,"peak":%.17g,"rms":%.17g,)"
        R"("utc_timestamp":"%s","hardware":"%s","thread_count":%d,"normalisation_applied":false})",
        gitCommit().c_str(), lockHash.c_str(), (unsigned long long) seed,
        controls.pluck_slap, controls.slap_brightness, controls.body_resonance,
        controls.sustain, controls.string_tension, controls.attack_noise,
        controls.mechanical_noise, controls.output_level,
        inputSha.c_str(), eventSha.c_str(), wavSha.c_str(),
        rate, (long long) frames, peak, rms,
        utcNow().c_str(), hardwareString().c_str(), threadCount());
    return buf;
}

std::string lockHashFromRepo()
{
    // environment-lock.txt lives at the repository root (parent of CWD or CWD).
    for (const char* p : {"environment-lock.txt", "../environment-lock.txt"})
    {
        bool ok = false;
        auto content = readFile(p, &ok);
        if (ok) return Sha256::ofString(content);
    }
    return "unavailable";
}

} // namespace

int main(int argc, char** argv)
{
    if (argc < 2)
    {
        std::cerr << "usage: psychobilly-render <render|render-raw|lifecycle|bench|version> [options]\n";
        return 2;
    }
    const std::string cmd = argv[1];
    try
    {
        if (cmd == "version")
        {
            std::printf(R"({"name":"Psychobilly Slap Bass","version":"0.1.0","format":"VST3","manufacturer":"QualityCoding","plugin_code":"Psb1"})");
            std::printf("\n");
            return 0;
        }

        if (cmd == "render" || cmd == "render-raw")
        {
            std::string inputPath, outputPath, metadataPath, eventsPath, controlsPath, outDir;
            int rate = 0;
            int64_t framesArg = -1;
            uint64_t seed = 0x50534C41ULL;
            for (int i = 2; i < argc; ++i)
            {
                const std::string a = argv[i];
                auto need = [&](const char* name) -> std::string {
                    if (i + 1 >= argc) throw std::runtime_error(std::string("missing value for ") + name);
                    return argv[++i];
                };
                if (a == "--input") inputPath = need("--input");
                else if (a == "--output") outputPath = need("--output");
                else if (a == "--metadata") metadataPath = need("--metadata");
                else if (a == "--events") eventsPath = need("--events");
                else if (a == "--controls") controlsPath = need("--controls");
                else if (a == "--rate") rate = std::stoi(need("--rate"));
                else if (a == "--seed") seed = std::stoull(need("--seed"));
                else if (a == "--frames") framesArg = std::stoll(need("--frames"));
                else if (a == "--outdir") outDir = need("--outdir");
                else throw std::runtime_error("unknown option " + a);
            }

            psb::Controls controls;
            std::vector<psb::Event> events;
            std::string inputSha, eventSha;
            int64_t frames = -1;
            std::string headerCanonical;

            if (cmd == "render")
            {
                if (inputPath.empty() || outputPath.empty() || metadataPath.empty())
                    throw std::runtime_error("--input/--output/--metadata are required");
                if (inputPath == outputPath || inputPath == metadataPath || outputPath == metadataPath)
                    throw std::runtime_error("path aliasing");
                bool ok = false;
                const std::string text = readFile(inputPath, &ok);
                if (!ok) throw std::runtime_error("cannot read input");
                if (text.size() > 1048576) throw std::runtime_error("input too large");
                inputSha = Sha256::ofString(text);

                // JSONL: first line header, remaining lines events
                std::vector<std::string> lines;
                std::string cur;
                std::istringstream ss(text);
                while (std::getline(ss, cur)) lines.push_back(cur);
                if (lines.empty()) throw std::runtime_error("empty document");

                psbjson::Parser headerParser(lines[0]);
                auto header = headerParser.parse();
                if (!header || header->type != psbjson::Value::Object) throw std::runtime_error("bad header");
                for (const auto& kv : header->object)
                    if (kv.first != "schema" && kv.first != "seed" && kv.first != "sample_rate"
                        && kv.first != "render_seconds" && kv.first != "controls")
                        throw std::runtime_error("unknown header field " + kv.first);
                auto schemaV = header->get("schema");
                if (!schemaV || !schemaV->isNumber() || (schemaV->number != 1 && schemaV->number != 2))
                    throw std::runtime_error("bad schema");
                const int schema = (int) schemaV->number;
                auto rateV = header->get("sample_rate");
                if (!rateV || !rateV->isNumber()) throw std::runtime_error("bad sample_rate");
                const double rd = rateV->number;
                if (rd != 44100 && rd != 48000 && rd != 88200 && rd != 96000)
                    throw std::runtime_error("unsupported sample_rate");
                rate = (int) rd;
                auto secondsV = header->get("render_seconds");
                if (!secondsV || !secondsV->isNumber() || secondsV->number <= 0)
                    throw std::runtime_error("bad render_seconds");
                const double seconds = secondsV->number;
                frames = (int64_t) std::llround(seconds * rate);
                if (frames <= 0 || frames > psb::kMaxFrames) throw std::runtime_error("render_seconds out of range");
                auto seedV = header->get("seed");
                if (!seedV || !seedV->isNumber() || seedV->number < 0) throw std::runtime_error("bad seed");
                seed = (uint64_t) seedV->number;
                std::string error;
                if (!parseControls(header->get("controls"), controls, &error)) throw std::runtime_error(error);

                int64_t lastSample = -1;
                for (size_t li = 1; li < lines.size(); ++li)
                {
                    if (lines[li].empty()) continue;
                    psbjson::Parser p(lines[li]);
                    auto ev = p.parse();
                    psb::Event e;
                    if (!parseEventObject(ev, e, schema, &error)) throw std::runtime_error(error);
                    if (e.sample < lastSample) throw std::runtime_error("events out of order");
                    lastSample = e.sample;
                    if (e.sample >= frames) throw std::runtime_error("event beyond declared duration");
                    events.push_back(e);
                }
                if ((int) events.size() > psb::kMaxEvents) throw std::runtime_error("too many events");
            }
            else
            {
                if (eventsPath.empty() || outDir.empty() || rate <= 0 || framesArg <= 0)
                    throw std::runtime_error("--events/--rate/--frames/--outdir are required");
                bool ok = false;
                const std::string text = readFile(eventsPath, &ok);
                if (!ok) throw std::runtime_error("cannot read events");
                psbjson::Parser p(text);
                auto arr = p.parse();
                if (!arr || arr->type != psbjson::Value::Array) throw std::runtime_error("events must be an array");
                std::string error;
                int64_t lastSample = -1;
                for (const auto& item : arr->array)
                {
                    psb::Event e;
                    if (!parseEventObject(item, e, 2, &error)) throw std::runtime_error(error);
                    if (e.sample < lastSample) throw std::runtime_error("events out of order");
                    lastSample = e.sample;
                    events.push_back(e);
                }
                controls = psb::Controls();
                if (!controlsPath.empty())
                {
                    const std::string ctext = readFile(controlsPath, &ok);
                    if (!ok) throw std::runtime_error("cannot read controls");
                    psbjson::Parser cp(ctext);
                    if (!parseControls(cp.parse(), controls, &error)) throw std::runtime_error(error);
                }
                frames = framesArg;
                inputSha = Sha256::ofString(text);
            }

            const std::string eventsCanon = canonicalEventsJson(events);
            eventSha = Sha256::ofString(eventsCanon);

            psb::Engine engine;
            engine.prepare((double) rate, 512);
            engine.setControls(controls);
            engine.setSeed(seed);
            std::string error;
            for (const auto& e : events)
                if (!engine.addEvent(e, &error)) throw std::runtime_error(error);

            auto result = engine.render(frames);
            const auto& mix = result.components.mix;
            const std::string wavSha = Sha256::ofVector(mix);
            const std::string lockHash = lockHashFromRepo();

            if (cmd == "render")
            {
                if (!writeWav24(outputPath, mix, rate, &error)) throw std::runtime_error(error);
                const std::string meta = provenanceJson(inputSha, eventSha, Sha256::ofFile(outputPath),
                                                        rate, frames, result.meta.peak, result.meta.rms,
                                                        seed, controls, lockHash);
                if (!writeFile(metadataPath, meta + "\n")) throw std::runtime_error("cannot write metadata");
            }
            else
            {
                auto writeRaw = [&](const char* name, const std::vector<double>& v) {
                    const std::string path = outDir + "/" + name;
                    std::ofstream f(path, std::ios::binary | std::ios::trunc);
                    f.write((const char*) v.data(), (std::streamsize) (v.size() * sizeof(double)));
                    if (!f) throw std::runtime_error(std::string("cannot write ") + path);
                };
                writeRaw("mix.f64", mix);
                writeRaw("pitched.f64", result.components.pitched);
                writeRaw("contact.f64", result.components.contact);
                writeRaw("body.f64", result.components.body);
                writeRaw("attack.f64", result.components.attack);
                writeRaw("mechanical.f64", result.components.mechanical);
                const std::string meta = provenanceJson(inputSha, eventSha, wavSha, rate, frames,
                                                        result.meta.peak, result.meta.rms, seed,
                                                        controls, lockHash);
                if (!writeFile(outDir + "/meta.json", meta + "\n")) throw std::runtime_error("cannot write metadata");
            }
            return 0;
        }

        if (cmd == "lifecycle")
        {
            std::string eventsPath;
            for (int i = 2; i < argc; ++i)
            {
                if (std::string(argv[i]) == "--events" && i + 1 < argc) eventsPath = argv[++i];
                else throw std::runtime_error("unknown option");
            }
            bool ok = false;
            const std::string text = readFile(eventsPath, &ok);
            if (!ok) throw std::runtime_error("cannot read events");
            psbjson::Parser p(text);
            auto arr = p.parse();
            if (!arr || arr->type != psbjson::Value::Array) throw std::runtime_error("events must be an array");
            psb::Engine engine;
            engine.prepare(48000.0, 512);
            std::string error;
            int64_t lastSample = -1;
            for (const auto& item : arr->array)
            {
                psb::Event e;
                if (!parseEventObject(item, e, 2, &error)) throw std::runtime_error(error);
                if (e.sample < lastSample) throw std::runtime_error("events out of order");
                lastSample = e.sample;
                engine.addEvent(e, &error);
            }
            const int64_t frames = std::max<int64_t>(1, lastSample + 1);
            engine.render(frames); // exercises the allocator for real
            const auto& lc = engine.lifecycle();
            char buf[512];
            snprintf(buf, sizeof buf,
                R"({"max_observed_voices":%d,"steals":%d,"retriggers":%d,)"
                R"("coupling_spectral_radius":%.17g,"crossfade_ms":%.17g,"no_allocation_in_process":%s})",
                lc.max_observed_voices, lc.steals, lc.retriggers,
                lc.coupling_spectral_radius, lc.crossfade_ms,
                lc.no_allocation_in_process ? "true" : "false");
            std::printf("%s\n", buf);
            return 0;
        }

        if (cmd == "bench")
        {
            int rate = 96000, block = 64, voices = 8, repeats = 7;
            double seconds = 5.0;
            for (int i = 2; i < argc; ++i)
            {
                const std::string a = argv[i];
                auto need = [&](const char* n) { if (i + 1 >= argc) throw std::runtime_error(n); return std::string(argv[++i]); };
                if (a == "--rate") rate = std::stoi(need("rate"));
                else if (a == "--block") block = std::stoi(need("block"));
                else if (a == "--voices") voices = std::stoi(need("voices"));
                else if (a == "--seconds") seconds = std::stod(need("seconds"));
                else if (a == "--repeats") repeats = std::stoi(need("repeats"));
                else throw std::runtime_error("unknown option " + a);
            }
            if (rate <= 0 || block <= 0 || voices < 1 || voices > psb::kNumVoices || repeats < 1 || seconds <= 0)
                throw std::runtime_error("bad bench parameters");

            std::vector<double> rtfs;
            bool finite = true;
            // warm-up: one second
            {
                psb::Engine engine;
                engine.prepare((double) rate, block);
                for (int v = 0; v < voices; ++v)
                {
                    psb::Event e;
                    e.sample = 0; e.type = psb::Event::note_on; e.note = 28 + v * 5; e.velocity = 0.8;
                    engine.addEvent(e);
                }
                std::vector<double> l((size_t) block), r((size_t) block);
                const int64_t total = (int64_t) (1.0 * rate);
                for (int64_t b = 0; b < total; b += block) engine.fillBlock(block, l.data(), r.data());
            }
            for (int run = 0; run < repeats; ++run)
            {
                psb::Engine engine;
                engine.prepare((double) rate, block);
                for (int v = 0; v < voices; ++v)
                {
                    psb::Event e;
                    e.sample = 0; e.type = psb::Event::note_on; e.note = 28 + v * 5; e.velocity = 0.8;
                    engine.addEvent(e);
                }
                std::vector<double> l((size_t) block), r((size_t) block);
                const int64_t total = (int64_t) (seconds * rate);
                const auto t0 = std::chrono::steady_clock::now();
                for (int64_t b = 0; b < total; b += block) engine.fillBlock(block, l.data(), r.data());
                const auto t1 = std::chrono::steady_clock::now();
                const double cpu = std::chrono::duration<double>(t1 - t0).count();
                const double rtf = cpu / seconds;
                if (!std::isfinite(rtf)) finite = false;
                rtfs.push_back(rtf);
            }
            std::sort(rtfs.begin(), rtfs.end());
            const double median = rtfs[(size_t) repeats / 2];
            const double mx = rtfs.back();
            std::string per;
            for (double v : rtfs) { char b[64]; snprintf(b, sizeof b, "%.17g,", v); per += b; }
            if (!per.empty()) per.pop_back();
            char buf[1024];
            snprintf(buf, sizeof buf,
                R"({"runs":%d,"finite":%s,"rtf_median":%.17g,"rtf_max":%.17g,"per_run":[%s]})",
                repeats, finite ? "true" : "false", median, mx, per.c_str());
            std::printf("%s\n", buf);
            return 0;
        }

        std::cerr << "unknown command\n";
        return 2;
    }
    catch (const std::exception& e)
    {
        std::cerr << "error: " << e.what() << "\n";
        return 2;
    }
    catch (...)
    {
        std::cerr << "error: internal failure\n";
        return 3;
    }
}
