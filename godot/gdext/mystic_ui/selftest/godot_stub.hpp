// godot_stub.hpp — stub Variant/Array/Dictionary/String/Color/Vector2/Rect2/
// Packed* untuk MENJALANKAN ui_processor.cpp di luar engine (self-test).
//
// Meniru SEMANTIK Godot 4.3 yang dipakai kode generated (pola
// godot/gdext/mystic_maps/selftest/godot_stub.hpp, ditambah Rect2 karena
// MysticUI mengembalikan geometri panel/kartu/tombol):
//
//   * Dictionary ordered (urutan insert) — core/variant/dictionary.h.
//   * Array::size() = int64_t; Packed*::size() = int64_t.
//   * Color menyimpan float; r8() = round(v*255) clamped — round-trip
//     Color(n/255) -> n dijamin untuk n 0..255 (properti yang dipakai
//     seluruh rantai paritas warna tema).
//   * Vector2 menyimpan float; koordinat jalur integral (< 2^24) sehingga
//     float(int) eksak dan int(float) kembali sama.
//   * Rect2 menyimpan float — posisi/size UI integral sehingga round-trip
//     int(Rect2.position) eksak.
//
// Stub ini BUKAN bagian lib: tidak ikut SConstruct (Glob hanya src/*.cpp).
// Kalau generator menambah method/include baru, stub + shim harus ikut —
// self-test gagal compile kalau lupa, dan oracle paritas membandingkan
// daftar method yang di-bind dengan daftar di berkas ini.
#ifndef MYSTIC_UI_SELFTEST_GODOT_STUB_H
#define MYSTIC_UI_SELFTEST_GODOT_STUB_H

#include <cctype>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <memory>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

namespace godot {

class Variant;
class Array;
class Dictionary;

class String {
public:
    std::string data;

    String() {}
    String(const char *p_from) : data(p_from ? p_from : "") {}
    String(const std::string &p_from) : data(p_from) {}

    static String num_int64(int64_t value) {
        char buf[32];
        snprintf(buf, sizeof(buf), "%lld", (long long)value);
        return String(std::string(buf));
    }

    int64_t length() const { return (int64_t)data.size(); }
    bool is_empty() const { return data.empty(); }

    // Godot: substr(from, len) — len < 0 berarti sampai akhir; indeks di luar
    // rentang dijepit (core/string/ustring.cpp).
    String substr(int64_t p_from, int64_t p_len) const {
        const int64_t total = (int64_t)data.size();
        if (p_from < 0) {
            p_from = total + p_from;
            if (p_from < 0) {
                p_from = 0;
            }
        }
        if (p_from > total) {
            p_from = total;
        }
        if (p_len < 0 || p_from + p_len > total) {
            p_len = total - p_from;
        }
        return String(data.substr((size_t)p_from, (size_t)p_len));
    }

    String operator+(const String &other) const { return String(data + other.data); }
    String &operator+=(const String &other) {
        data += other.data;
        return *this;
    }
    // Godot String::strip_edges() default: BOTH (buang spasi/tab/newline).
    String strip_edges() const {
        size_t begin = 0;
        size_t end = data.size();
        while (begin < end && isspace((unsigned char)data[begin])) {
            begin++;
        }
        while (end > begin && isspace((unsigned char)data[end - 1])) {
            end--;
        }
        return String(data.substr(begin, end - begin));
    }

    String to_lower() const {
        std::string out = data;
        for (size_t i = 0; i < out.size(); i++) {
            out[i] = (char)tolower((unsigned char)out[i]);
        }
        return String(out);
    }

    // Godot String::capitalize(): huruf pertama tiap kata jadi kapital,
    // sisanya kecil (core/string/ustring.cpp).
    String capitalize() const {
        std::string out = data;
        bool cap_next = true;
        for (size_t i = 0; i < out.size(); i++) {
            const unsigned char c = (unsigned char)out[i];
            if (isalpha(c)) {
                out[i] = (char)(cap_next ? toupper(c) : tolower(c));
                cap_next = false;
            } else {
                cap_next = true;
            }
        }
        return String(out);
    }

    String replace(const String &what, const String &with) const {
        if (what.data.empty()) {
            return *this;
        }
        std::string out;
        size_t pos = 0;
        while (true) {
            const size_t hit = data.find(what.data, pos);
            if (hit == std::string::npos) {
                out += data.substr(pos);
                break;
            }
            out += data.substr(pos, hit - pos);
            out += with.data;
            pos = hit + what.data.size();
        }
        return String(out);
    }

    bool contains(const String &needle) const {
        return data.find(needle.data) != std::string::npos;
    }

    bool begins_with(const String &prefix) const {
        return data.size() >= prefix.data.size() &&
               data.compare(0, prefix.data.size(), prefix.data) == 0;
    }

    bool operator==(const String &other) const { return data == other.data; }
    bool operator!=(const String &other) const { return data != other.data; }
};

inline String operator+(const char *p_left, const String &p_right) {
    return String(p_left) + p_right;
}
inline String operator+(const String &p_left, const char *p_right) {
    return p_left + String(p_right);
}

class Color {
public:
    float r = 0.0f, g = 0.0f, b = 0.0f, a = 1.0f;

    Color() {}
    Color(float p_r, float p_g, float p_b, float p_a = 1.0f)
        : r(p_r), g(p_g), b(p_b), a(p_a) {}

    static int64_t channel8(float v) {
        long rounded = lround((double)v * 255.0);
        if (rounded < 0) {
            return 0;
        }
        if (rounded > 255) {
            return 255;
        }
        return (int64_t)rounded;
    }
    int64_t r8() const { return channel8(r); }
    int64_t g8() const { return channel8(g); }
    int64_t b8() const { return channel8(b); }
    int64_t a8() const { return channel8(a); }

    bool operator==(const Color &other) const {
        return r == other.r && g == other.g && b == other.b && a == other.a;
    }
};

class Vector2 {
public:
    float x = 0.0f, y = 0.0f;

    Vector2() {}
    Vector2(float p_x, float p_y) : x(p_x), y(p_y) {}

    bool operator==(const Vector2 &other) const { return x == other.x && y == other.y; }
};

class Rect2 {
public:
    Vector2 position;
    Vector2 size;

    Rect2() {}
    Rect2(float p_x, float p_y, float p_w, float p_h)
        : position(p_x, p_y), size(p_w, p_h) {}
    Rect2(const Vector2 &p_position, const Vector2 &p_size)
        : position(p_position), size(p_size) {}

    bool operator==(const Rect2 &other) const {
        return position == other.position && size == other.size;
    }

    // Godot Rect2::has_point: mengembalikan false untuk sisi max (x >= end).
    bool has_point(const Vector2 &p_point) const {
        return p_point.x >= position.x && p_point.x < position.x + size.x &&
               p_point.y >= position.y && p_point.y < position.y + size.y;
    }
};

class PackedVector2Array {
public:
    std::vector<Vector2> items;

    PackedVector2Array() {}

    int64_t size() const { return (int64_t)items.size(); }
    bool is_empty() const { return items.empty(); }
    void resize(int64_t p_size) { items.resize((size_t)p_size); }
    void append(const Vector2 &p_value) { items.push_back(p_value); }
    Vector2 &operator[](int64_t p_index) { return items[(size_t)p_index]; }
    const Vector2 &operator[](int64_t p_index) const { return items[(size_t)p_index]; }
};

class PackedColorArray {
public:
    std::vector<Color> items;

    PackedColorArray() {}

    int64_t size() const { return (int64_t)items.size(); }
    bool is_empty() const { return items.empty(); }
    void resize(int64_t p_size) { items.resize((size_t)p_size); }
    void append(const Color &p_value) { items.push_back(p_value); }
    Color &operator[](int64_t p_index) { return items[(size_t)p_index]; }
    const Color &operator[](int64_t p_index) const { return items[(size_t)p_index]; }
};

class Variant {
public:
    enum Type { NIL, BOOL, INT, FLOAT, STRING, DICTIONARY, ARRAY, COLOR, VECTOR2, RECT2, PACKED_V2, PACKED_COLOR };
    enum Operator { OP_EQUAL, OP_NOT_EQUAL };

    Type type = NIL;
    bool b = false;
    int64_t i = 0;
    double f = 0.0;
    std::shared_ptr<String> str;
    std::shared_ptr<Dictionary> dict;
    std::shared_ptr<Array> arr;
    Color c;
    Vector2 v2;
    Rect2 rect;
    std::shared_ptr<PackedVector2Array> pv2;
    std::shared_ptr<PackedColorArray> pcol;

    Variant() : type(NIL) {}
    Variant(bool p_b) : type(BOOL), b(p_b) {}
    Variant(int p_i) : type(INT), i(p_i) {}
    Variant(int64_t p_i) : type(INT), i(p_i) {}
    Variant(double p_f) : type(FLOAT), f(p_f) {}
    Variant(const String &p_s) : type(STRING), str(std::make_shared<String>(p_s)) {}
    Variant(const char *p_s) : type(STRING), str(std::make_shared<String>(p_s)) {}
    Variant(const Color &p_c) : type(COLOR), c(p_c) {}
    Variant(const Vector2 &p_v) : type(VECTOR2), v2(p_v) {}
    Variant(const Rect2 &p_r) : type(RECT2), rect(p_r) {}
    Variant(const PackedVector2Array &p_p) : type(PACKED_V2), pv2(std::make_shared<PackedVector2Array>(p_p)) {}
    Variant(const PackedColorArray &p_p)
        : type(PACKED_COLOR), pcol(std::make_shared<PackedColorArray>(p_p)) {}

    Variant(const Dictionary &p_d);
    Variant(const Array &p_a);

    bool is_nil() const { return type == NIL; }
    bool is_numeric() const { return type == INT || type == FLOAT; }
    double numeric() const { return type == INT ? (double)i : f; }

    explicit operator bool() const;
    operator String() const { return str ? *str : String(); }

    // Godot Variant punya operator int64/int/bool. Kode generated memakai
    // `int64_t v = arr[i];` — tiru konversinya (INT -> i, FLOAT -> trunc).
    operator int64_t() const {
        switch (type) {
            case INT: return i;
            case FLOAT: return (int64_t)f;
            case BOOL: return b ? 1 : 0;
            default: return 0;
        }
    }
    operator int() const { return (int)(int64_t)(*this); }
    operator Vector2() const { return v2; }
    operator Rect2() const { return rect; }
    operator Color() const { return c; }

    bool same_value(const Variant &other) const;

    static void evaluate(const Operator &op, const Variant &a, const Variant &b,
                         Variant &r_ret, bool &r_valid) {
        bool equal = false;
        bool valid = true;
        if (a.is_numeric() && b.is_numeric()) {
            equal = a.numeric() == b.numeric();
        } else if (a.type == b.type) {
            equal = a.same_value(b);
        } else {
            valid = false;
        }
        if (op == OP_NOT_EQUAL && valid) {
            equal = !equal;
        }
        r_ret = Variant(equal);
        r_valid = valid;
    }

    std::string to_text() const;
};

class Array {
public:
    std::vector<Variant> items;

    Array() {}

    int64_t size() const { return (int64_t)items.size(); }
    bool is_empty() const { return items.empty(); }
    void resize(int64_t p_size) { items.resize((size_t)p_size); }
    void push_back(const Variant &p_value) { items.push_back(p_value); }
    Variant &operator[](int64_t p_index) { return items[(size_t)p_index]; }
    const Variant &operator[](int64_t p_index) const { return items[(size_t)p_index]; }

    // Godot Array::duplicate() menghasilkan salinan (default deep=false, tapi
    // untuk int/str/color/dict hasilnya sama karena Variant di sini memegang
    // shared_ptr layaknya Ref<Resource>).
    Array duplicate() const { return *this; }
};

class Dictionary {
public:
    std::vector<std::pair<Variant, Variant>> pairs;

    Dictionary() {}

    bool is_empty() const { return pairs.empty(); }
    int64_t size() const { return (int64_t)pairs.size(); }
    bool has_key_variant(const Variant &key) const;
    // Godot Dictionary::has() — sama dengan has_key_variant tapi namanya
    // dipakai kode generated.
    bool has(const Variant &key) const { return has_key_variant(key); }
    Variant &operator[](const Variant &key);
    // Godot Dictionary::operator[] const mengembalikan salinan Variant.
    Variant operator[](const Variant &key) const { return get_const(key); }
    const Variant &get_const(const Variant &key) const;
};

inline Variant::Variant(const Dictionary &p_d)
    : type(DICTIONARY), dict(std::make_shared<Dictionary>(p_d)) {}

inline Variant::Variant(const Array &p_a) : type(ARRAY), arr(std::make_shared<Array>(p_a)) {}

inline Variant::operator bool() const {
    switch (type) {
        case NIL: return false;
        case BOOL: return b;
        case INT: return i != 0;
        case FLOAT: return f != 0.0;
        case STRING: return str && !str->data.empty();
        case DICTIONARY: return dict && !dict->is_empty();
        case ARRAY: return arr && !arr->is_empty();
        case COLOR: return true;
        case VECTOR2: return true;
        case RECT2: return true;
        case PACKED_V2: return pv2 && !pv2->is_empty();
        case PACKED_COLOR: return pcol && !pcol->is_empty();
    }
    return false;
}

inline bool Variant::same_value(const Variant &other) const {
    switch (type) {
        case NIL: return true;
        case BOOL: return b == other.b;
        case INT: return i == other.i;
        case FLOAT: return f == other.f;
        case STRING: return str && other.str && str->data == other.str->data;
        case COLOR: return c == other.c;
        case VECTOR2: return v2 == other.v2;
        case RECT2: return rect == other.rect;
        case PACKED_V2: {
            if (!pv2 || !other.pv2 || pv2->size() != other.pv2->size()) {
                return false;
            }
            for (int64_t idx = 0; idx < pv2->size(); idx++) {
                if (!((*pv2)[idx] == (*other.pv2)[idx])) {
                    return false;
                }
            }
            return true;
        }
        case PACKED_COLOR: {
            if (!pcol || !other.pcol || pcol->size() != other.pcol->size()) {
                return false;
            }
            for (int64_t idx = 0; idx < pcol->size(); idx++) {
                if (!((*pcol)[idx] == (*other.pcol)[idx])) {
                    return false;
                }
            }
            return true;
        }
        case DICTIONARY: {
            if (!dict || !other.dict || dict->size() != other.dict->size()) {
                return false;
            }
            for (int64_t idx = 0; idx < dict->size(); idx++) {
                const Variant &key = dict->pairs[(size_t)idx].first;
                if (!other.dict->has_key_variant(key)) {
                    return false;
                }
                const Variant &mine = dict->pairs[(size_t)idx].second;
                const Variant &theirs = other.dict->get_const(key);
                bool valid = false;
                Variant equal;
                Variant::evaluate(Variant::OP_EQUAL, mine, theirs, equal, valid);
                if (!valid || !bool(equal)) {
                    return false;
                }
            }
            return true;
        }
        case ARRAY: {
            if (!arr || !other.arr || arr->size() != other.arr->size()) {
                return false;
            }
            for (int64_t idx = 0; idx < arr->size(); idx++) {
                bool valid = false;
                Variant equal;
                Variant::evaluate(Variant::OP_EQUAL, (*arr)[idx], (*other.arr)[idx], equal, valid);
                if (!valid || !bool(equal)) {
                    return false;
                }
            }
            return true;
        }
    }
    return false;
}

inline std::string float_text(float v) {
    char buf[40];
    snprintf(buf, sizeof(buf), "%.9g", (double)v);
    return std::string(buf);
}

inline std::string Variant::to_text() const {
    switch (type) {
        case NIL: return "nil:null";
        case BOOL: return std::string("bool:") + (b ? "true" : "false");
        case INT: return std::string("int:") + std::to_string((long long)i);
        case FLOAT: {
            char buf[40];
            snprintf(buf, sizeof(buf), "float:%.17g", f);
            return std::string(buf);
        }
        case STRING: return std::string("str:") + (str ? str->data : std::string());
        case COLOR: {
            char buf[64];
            snprintf(buf, sizeof(buf), "color:%lld,%lld,%lld,%lld",
                    (long long)c.r8(), (long long)c.g8(), (long long)c.b8(), (long long)c.a8());
            return std::string(buf);
        }
        case VECTOR2: {
            return std::string("v2:") + float_text(v2.x) + "," + float_text(v2.y);
        }
        case RECT2: {
            return std::string("rect:") + float_text(rect.position.x) + "," +
                   float_text(rect.position.y) + "," + float_text(rect.size.x) + "," +
                   float_text(rect.size.y);
        }
        case PACKED_V2: {
            std::string out = "v2s:[";
            if (pv2) {
                for (int64_t idx = 0; idx < pv2->size(); idx++) {
                    if (idx) {
                        out += ",";
                    }
                    out += Variant((*pv2)[idx]).to_text();
                }
            }
            return out + "]";
        }
        case PACKED_COLOR: {
            std::string out = "pc:[";
            if (pcol) {
                for (int64_t idx = 0; idx < pcol->size(); idx++) {
                    if (idx) {
                        out += ",";
                    }
                    out += Variant((*pcol)[idx]).to_text();
                }
            }
            return out + "]";
        }
        case DICTIONARY: {
            std::string out = "dict:";
            if (!dict) {
                return out + "{}";
            }
            out += "{";
            for (int64_t idx = 0; idx < dict->size(); idx++) {
                if (idx) {
                    out += ",";
                }
                out += dict->pairs[(size_t)idx].first.to_text();
                out += "=";
                out += dict->pairs[(size_t)idx].second.to_text();
            }
            return out + "}";
        }
        case ARRAY: {
            std::string out = "array:";
            if (!arr) {
                return out + "[]";
            }
            out += "[";
            for (int64_t idx = 0; idx < arr->size(); idx++) {
                if (idx) {
                    out += ",";
                }
                out += (*arr)[idx].to_text();
            }
            return out + "]";
        }
    }
    return "unknown";
}

inline bool Dictionary::has_key_variant(const Variant &key) const {
    for (const auto &pair : pairs) {
        bool valid = false;
        Variant equal;
        Variant::evaluate(Variant::OP_EQUAL, pair.first, key, equal, valid);
        if (valid && bool(equal)) {
            return true;
        }
    }
    return false;
}

inline const Variant &Dictionary::get_const(const Variant &key) const {
    for (const auto &pair : pairs) {
        bool valid = false;
        Variant equal;
        Variant::evaluate(Variant::OP_EQUAL, pair.first, key, equal, valid);
        if (valid && bool(equal)) {
            return pair.second;
        }
    }
    static const Variant nil;
    return nil;
}

inline Variant &Dictionary::operator[](const Variant &key) {
    for (auto &pair : pairs) {
        bool valid = false;
        Variant equal;
        Variant::evaluate(Variant::OP_EQUAL, pair.first, key, equal, valid);
        if (valid && bool(equal)) {
            return pair.second;
        }
    }
    pairs.push_back(std::make_pair(key, Variant()));
    return pairs.back().second;
}

class ClassDB {
public:
    template <typename... Args>
    static void bind_static_method(Args &&...args) {
        (void)std::forward_as_tuple(args...);
    }
    template <typename T>
    static void register_class() {}
};

} // namespace godot

#define D_METHOD(...) ::godot_stub_noop(__VA_ARGS__)
#define DEFVAL(x) ::godot_stub_noop(x)

namespace {
template <typename... Args>
inline int godot_stub_noop(Args &&...args) {
    (void)std::forward_as_tuple(args...);
    return 0;
}
} // namespace

// ── Kelas dasar + makro godot-cpp yang dipakai ui_processor.h ────────────
//
// BEDA dari stub mystic_maps: di sini deklarasi kelas TIDAK disalin ulang.
// ui_processor.h ikut di-parse apa adanya (include godot-cpp-nya diarahkan ke
// shim kosong oleh -Ishim), jadi API stub selalu identik dengan API hasil
// generate — perubahan generator tidak bisa "lupa" disalin ke stub.
namespace godot {
class RefCounted {
public:
    virtual ~RefCounted() {}
};
} // namespace godot

#define GDCLASS(m_class, m_inherits) \
public:                              \
    static void _gdclass_noop() {}

#endif // MYSTIC_UI_SELFTEST_GODOT_STUB_H
