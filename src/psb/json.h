// Minimal strict JSON parser/serializer for the psb event/metadata contracts.
// Supports exactly the JSON subset used by D-024/D-025 documents: objects,
// arrays, strings, finite numbers, booleans, null. No duplicates are enforced
// here; schema validation happens at the contract layer. AGPL-3.0-only.
#pragma once

#include <cctype>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <map>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace psbjson
{

struct Value;
using ValuePtr = std::shared_ptr<Value>;

struct Value
{
    enum Type { Null, Bool, Number, String, Array, Object } type = Null;
    bool boolean = false;
    double number = 0.0;
    std::string str;
    std::vector<ValuePtr> array;
    std::map<std::string, ValuePtr> object;

    bool isNumber() const { return type == Number; }
    bool isString() const { return type == String; }
    double asNumber() const { return number; }
    const std::string& asString() const { return str; }
    bool has(const std::string& key) const { return object.count(key) != 0; }
    ValuePtr get(const std::string& key) const
    {
        auto it = object.find(key);
        return it == object.end() ? nullptr : it->second;
    }
};

class ParseError : public std::runtime_error
{
public:
    explicit ParseError(const std::string& m) : std::runtime_error(m) {}
};

class Parser
{
public:
    explicit Parser(const std::string& text) : t_(text) {}

    ValuePtr parse()
    {
        skipWs();
        auto v = parseValue();
        skipWs();
        if (pos_ != t_.size()) fail("trailing content");
        return v;
    }

private:
    const std::string& t_;
    size_t pos_ = 0;

    [[noreturn]] void fail(const std::string& m) { throw ParseError("JSON parse error at byte " + std::to_string(pos_) + ": " + m); }
    char peek() { return pos_ < t_.size() ? t_[pos_] : '\0'; }
    char next()
    {
        if (pos_ >= t_.size()) fail("unexpected end");
        return t_[pos_++];
    }
    void skipWs()
    {
        while (pos_ < t_.size() && (t_[pos_] == ' ' || t_[pos_] == '\t' || t_[pos_] == '\n' || t_[pos_] == '\r')) ++pos_;
    }
    void expect(char c)
    {
        if (next() != c) fail(std::string("expected '") + c + "'");
    }

    ValuePtr parseValue()
    {
        skipWs();
        auto v = std::make_shared<Value>();
        switch (peek())
        {
            case 'n': expectLit("null"); v->type = Value::Null; return v;
            case 't': expectLit("true"); v->type = Value::Bool; v->boolean = true; return v;
            case 'f': expectLit("false"); v->type = Value::Bool; v->boolean = false; return v;
            case '"': v->type = Value::String; v->str = parseString(); return v;
            case '[':
            {
                next();
                v->type = Value::Array;
                skipWs();
                if (peek() == ']') { next(); return v; }
                while (true)
                {
                    v->array.push_back(parseValue());
                    skipWs();
                    if (peek() == ',') { next(); continue; }
                    expect(']');
                    return v;
                }
            }
            case '{':
            {
                next();
                v->type = Value::Object;
                skipWs();
                if (peek() == '}') { next(); return v; }
                while (true)
                {
                    skipWs();
                    std::string key = parseString();
                    skipWs();
                    expect(':');
                    if (v->object.count(key)) fail("duplicate key '" + key + "'");
                    v->object[key] = parseValue();
                    skipWs();
                    if (peek() == ',') { next(); continue; }
                    expect('}');
                    return v;
                }
            }
            default: return parseNumber();
        }
    }

    void expectLit(const char* lit)
    {
        for (const char* p = lit; *p; ++p)
            if (next() != *p) fail("invalid literal");
    }

    std::string parseString()
    {
        expect('"');
        std::string out;
        while (true)
        {
            char c = next();
            if (c == '"') return out;
            if (c == '\\')
            {
                char e = next();
                switch (e)
                {
                    case '"': out += '"'; break;
                    case '\\': out += '\\'; break;
                    case '/': out += '/'; break;
                    case 'b': out += '\b'; break;
                    case 'f': out += '\f'; break;
                    case 'n': out += '\n'; break;
                    case 'r': out += '\r'; break;
                    case 't': out += '\t'; break;
                    case 'u':
                    {
                        unsigned cp = 0;
                        for (int i = 0; i < 4; ++i)
                        {
                            char h = next();
                            cp <<= 4;
                            if (h >= '0' && h <= '9') cp += (unsigned) (h - '0');
                            else if (h >= 'a' && h <= 'f') cp += (unsigned) (h - 'a' + 10);
                            else if (h >= 'A' && h <= 'F') cp += (unsigned) (h - 'A' + 10);
                            else fail("bad \\u escape");
                        }
                        // encode UTF-8 (BMP only; the contract is ASCII)
                        if (cp < 0x80) out += (char) cp;
                        else if (cp < 0x800) { out += (char) (0xC0 | (cp >> 6)); out += (char) (0x80 | (cp & 0x3F)); }
                        else { out += (char) (0xE0 | (cp >> 12)); out += (char) (0x80 | ((cp >> 6) & 0x3F)); out += (char) (0x80 | (cp & 0x3F)); }
                        break;
                    }
                    default: fail("bad escape");
                }
            }
            else
            {
                if ((unsigned char) c < 0x20) fail("control character in string");
                out += c;
            }
        }
    }

    ValuePtr parseNumber()
    {
        auto v = std::make_shared<Value>();
        v->type = Value::Number;
        const char* begin = t_.c_str() + pos_;
        char* end = nullptr;
        double d = std::strtod(begin, &end);
        if (end == begin) fail("invalid number");
        pos_ += (size_t) (end - begin);
        if (!std::isfinite(d)) fail("non-finite number");
        v->number = d;
        return v;
    }
};

inline std::string escape(const std::string& s)
{
    std::string out;
    for (char c : s)
    {
        switch (c)
        {
            case '"': out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            case '\n': out += "\\n"; break;
            case '\r': out += "\\r"; break;
            case '\t': out += "\\t"; break;
            default:
                if ((unsigned char) c < 0x20) { char b[8]; snprintf(b, sizeof b, "\\u%04x", c); out += b; }
                else out += c;
        }
    }
    return out;
}

} // namespace psbjson
