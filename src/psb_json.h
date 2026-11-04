// Strict JSON parser for the frozen event-document contract (D-024).
// Rejects duplicates, unknown-number syntax (nan/inf), trailing content.
#pragma once

#include <cstdint>
#include <cstdlib>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

namespace psb {

class JsonError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

struct JsonValue {
    enum class Type { object, array, string, number, boolean, null_ } type = Type::null_;
    std::map<std::string, JsonValue> object;
    std::vector<JsonValue> array;
    std::string string;
    double number = 0.0;
    bool boolean = false;

    const JsonValue& at(const std::string& key) const {
        if (type != Type::object)
            throw JsonError("not an object");
        auto it = object.find(key);
        if (it == object.end())
            throw JsonError("missing key: " + key);
        return it->second;
    }
    bool has(const std::string& key) const {
        return type == Type::object && object.count(key) != 0;
    }
};

class JsonParser {
public:
    explicit JsonParser(const std::string& text) : text_(text) {}

    JsonValue parseDocument() {
        skipWs();
        JsonValue v = parseValue();
        skipWs();
        if (pos_ != text_.size())
            throw JsonError("trailing content");
        return v;
    }

private:
    const std::string& text_;
    std::size_t pos_ = 0;

    [[noreturn]] void fail(const std::string& what) {
        throw JsonError(what + " at offset " + std::to_string(pos_));
    }

    char peek() {
        if (pos_ >= text_.size())
            fail("unexpected end of input");
        return text_[pos_];
    }
    char take() {
        const char c = peek();
        ++pos_;
        return c;
    }
    void expect(char c) {
        if (take() != c)
            fail(std::string("expected '") + c + "'");
    }
    void skipWs() {
        while (pos_ < text_.size()) {
            const char c = text_[pos_];
            if (c == ' ' || c == '\t' || c == '\n' || c == '\r')
                ++pos_;
            else
                break;
        }
    }

    JsonValue parseValue() {
        const char c = peek();
        if (c == '{') return parseObject();
        if (c == '[') return parseArray();
        if (c == '"') {
            JsonValue v;
            v.type = JsonValue::Type::string;
            v.string = parseString();
            return v;
        }
        if (c == 't') {
            expectLiteral("true");
            JsonValue v; v.type = JsonValue::Type::boolean; v.boolean = true; return v;
        }
        if (c == 'f') {
            expectLiteral("false");
            JsonValue v; v.type = JsonValue::Type::boolean; v.boolean = false; return v;
        }
        if (c == 'n') {
            expectLiteral("null");
            JsonValue v; v.type = JsonValue::Type::null_; return v;
        }
        if (c == '-' || (c >= '0' && c <= '9'))
            return parseNumber();
        fail("unexpected character");
    }

    void expectLiteral(const char* lit) {
        for (const char* p = lit; *p; ++p)
            if (take() != *p)
                fail("bad literal");
    }

    std::string parseString() {
        expect('"');
        std::string out;
        while (true) {
            const char c = take();
            if (c == '"')
                return out;
            if (static_cast<unsigned char>(c) < 0x20)
                fail("control character in string");
            if (c == '\\') {
                const char e = take();
                switch (e) {
                    case '"': out += '"'; break;
                    case '\\': out += '\\'; break;
                    case '/': out += '/'; break;
                    case 'b': out += '\b'; break;
                    case 'f': out += '\f'; break;
                    case 'n': out += '\n'; break;
                    case 'r': out += '\r'; break;
                    case 't': out += '\t'; break;
                    case 'u': {
                        unsigned code = 0;
                        for (int i = 0; i < 4; ++i) {
                            const char h = take();
                            code <<= 4;
                            if (h >= '0' && h <= '9') code += static_cast<unsigned>(h - '0');
                            else if (h >= 'a' && h <= 'f') code += static_cast<unsigned>(h - 'a' + 10);
                            else if (h >= 'A' && h <= 'F') code += static_cast<unsigned>(h - 'A' + 10);
                            else fail("bad unicode escape");
                        }
                        if (code < 0x80) {
                            out += static_cast<char>(code);
                        } else if (code < 0x800) {
                            out += static_cast<char>(0xc0 | (code >> 6));
                            out += static_cast<char>(0x80 | (code & 0x3f));
                        } else {
                            out += static_cast<char>(0xe0 | (code >> 12));
                            out += static_cast<char>(0x80 | ((code >> 6) & 0x3f));
                            out += static_cast<char>(0x80 | (code & 0x3f));
                        }
                        break;
                    }
                    default: fail("bad escape");
                }
            } else {
                out += c;
            }
        }
    }

    JsonValue parseNumber() {
        const std::size_t start = pos_;
        if (peek() == '-')
            ++pos_;
        if (pos_ >= text_.size())
            fail("bad number");
        if (text_[pos_] == '0') {
            ++pos_;
        } else if (text_[pos_] >= '1' && text_[pos_] <= '9') {
            while (pos_ < text_.size() && text_[pos_] >= '0' && text_[pos_] <= '9')
                ++pos_;
        } else {
            fail("bad number");
        }
        if (pos_ < text_.size() && text_[pos_] == '.') {
            ++pos_;
            if (pos_ >= text_.size() || text_[pos_] < '0' || text_[pos_] > '9')
                fail("bad fraction");
            while (pos_ < text_.size() && text_[pos_] >= '0' && text_[pos_] <= '9')
                ++pos_;
        }
        if (pos_ < text_.size() && (text_[pos_] == 'e' || text_[pos_] == 'E')) {
            ++pos_;
            if (pos_ < text_.size() && (text_[pos_] == '+' || text_[pos_] == '-'))
                ++pos_;
            if (pos_ >= text_.size() || text_[pos_] < '0' || text_[pos_] > '9')
                fail("bad exponent");
            while (pos_ < text_.size() && text_[pos_] >= '0' && text_[pos_] <= '9')
                ++pos_;
        }
        const std::string token = text_.substr(start, pos_ - start);
        char* end = nullptr;
        const double value = std::strtod(token.c_str(), &end);
        if (end == nullptr || *end != '\0')
            fail("bad number");
        JsonValue v;
        v.type = JsonValue::Type::number;
        v.number = value;
        return v;
    }

    JsonValue parseObject() {
        expect('{');
        JsonValue v;
        v.type = JsonValue::Type::object;
        skipWs();
        if (peek() == '}') {
            ++pos_;
            return v;
        }
        while (true) {
            skipWs();
            std::string key = parseString();
            skipWs();
            expect(':');
            skipWs();
            JsonValue value = parseValue();
            if (!v.object.emplace(std::move(key), std::move(value)).second)
                fail("duplicate key");
            skipWs();
            const char c = take();
            if (c == '}')
                return v;
            if (c != ',')
                fail("expected ',' or '}'");
        }
    }

    JsonValue parseArray() {
        expect('[');
        JsonValue v;
        v.type = JsonValue::Type::array;
        skipWs();
        if (peek() == ']') {
            ++pos_;
            return v;
        }
        while (true) {
            skipWs();
            v.array.push_back(parseValue());
            skipWs();
            const char c = take();
            if (c == ']')
                return v;
            if (c != ',')
                fail("expected ',' or ']'");
        }
    }
};

} // namespace psb
