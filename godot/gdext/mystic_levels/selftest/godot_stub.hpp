// godot_stub.hpp — stub Variant/Array/Dictionary/String untuk MENJALANKAN
// levels_processor.cpp di luar engine (self-test, lihat levels_selftest.cpp).
//
// Kenapa ada: memverifikasi tabel + logika C++ tidak harus menunggu build
// godot-cpp (±10 menit) atau mengunduh engine Godot. Berkas ini meniru SEMANTIK
// Godot yang dipakai kode generated, dibaca dari sumber engine 4.3:
//
//   * Dictionary ordered (urutan insert) — core/variant/dictionary.h memakai
//     vector pasangan + map indeks, jadi `keys()` mengikuti urutan tulis.
//   * Array::size() bertanda tangan int64_t (BUKAN size_t) — itu sebabnya kode
//     generated bebas menulis `for (int64_t i = 0; i < haystack.size(); i++)`.
//   * Array::has()/find() memakai Variant::hash_compare yang STRICT tipe
//     (core/variant/variant.cpp:3309 `if (type != p_variant.type) return false`)
//     — itu sebabnya MysticLevels::py_contains TIDAK memakainya dan memilih
//     Variant::evaluate(OP_EQUAL) yang numerik lintas tipe.
//   * Variant::evaluate(OP_EQUAL) terdaftar untuk pasangan tipe yang sama,
//     INT<->FLOAT (numerik), dan keluarga string; pasangan lain -> valid=false
//     (core/variant/variant_op.cpp:522-528). bool vs int TIDAK terdaftar, jadi
//     `True == 1` ala Python tidak punya padanan — deviasi itu dikunci
//     deviation_battery di godot/tests/fixtures/level_data.json.
//   * JSON.parse_string mengubah SEMUA angka jadi double (core/io/json.cpp:341)
//     — hanya relevan untuk backend GDScript (LevelDB.gd menormalkan ulang),
//     dicatat di sini supaya stub ini tidak "memperbaiki" tipe secara diam-diam.
//
// Stub ini BUKAN bagian lib: tidak ikut SConstruct (Glob hanya src/*.cpp) dan
// tidak pernah dimuat engine. Kalau generator menambah method baru, tambahkan
// deklarasinya di kelas MysticLevels paling bawah — self-test gagal compile
// kalau lupa, dan tools/test_godot_level_data_parity.py membandingkan daftar
// method yang di-bind dengan daftar di berkas ini.
#ifndef MYSTIC_LEVELS_SELFTEST_GODOT_STUB_H
#define MYSTIC_LEVELS_SELFTEST_GODOT_STUB_H

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

// String tipis di atas std::string (UTF-8), cukup untuk kode generated.
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

    String operator+(const String &other) const { return String(data + other.data); }
    String &operator+=(const String &other) {
        data += other.data;
        return *this;
    }
    bool operator==(const String &other) const { return data == other.data; }
    bool operator!=(const String &other) const { return data != other.data; }
};

// godot-cpp juga menyediakan operator+ non-member (literal di kiri), dipakai
// katalog_signature(): `sig += ":" + String::num_int64(mini_total);`
inline String operator+(const char *p_left, const String &p_right) {
    return String(p_left) + p_right;
}
inline String operator+(const String &p_left, const char *p_right) {
    return p_left + String(p_right);
}

class Variant {
public:
    enum Type { NIL, BOOL, INT, FLOAT, STRING, DICTIONARY, ARRAY };

    // Operator pembanding yang dipakai stub evaluate (Godot: OP_EQUAL dkk.).
    enum Operator { OP_EQUAL, OP_NOT_EQUAL };

    Type type = NIL;
    bool b = false;
    int64_t i = 0;
    double f = 0.0;
    std::shared_ptr<String> str;
    std::shared_ptr<Dictionary> dict;
    std::shared_ptr<Array> arr;

    Variant() : type(NIL) {}
    Variant(bool p_b) : type(BOOL), b(p_b) {}
    Variant(int p_i) : type(INT), i(p_i) {}
    Variant(int64_t p_i) : type(INT), i(p_i) {}
    Variant(double p_f) : type(FLOAT), f(p_f) {}
    Variant(const String &p_s) : type(STRING), str(std::make_shared<String>(p_s)) {}
    Variant(const char *p_s) : type(STRING), str(std::make_shared<String>(p_s)) {}

    // Konstruksi dari Dictionary/Array didefinisikan setelah keduanya lengkap.
    Variant(const Dictionary &p_d);
    Variant(const Array &p_a);

    bool is_nil() const { return type == NIL; }
    bool is_numeric() const { return type == INT || type == FLOAT; }
    double numeric() const { return type == INT ? (double)i : f; }

    // Truthiness ala Godot (dipakai `bool(equal)` di py_contains).
    explicit operator bool() const;

    bool same_value(const Variant &other) const;

    // Godot: Variant::evaluate(OP_EQUAL, ...) — valid=false untuk pasangan tipe
    // tanpa evaluator terdaftar (mis. BOOL vs INT), bukan error/crash.
    static void evaluate(const Operator &op, const Variant &a, const Variant &b,
                         Variant &r_ret, bool &r_valid) {
        bool equal = false;
        bool valid = true;
        if (a.is_numeric() && b.is_numeric()) {
            equal = a.numeric() == b.numeric(); // INT<->FLOAT terdaftar (numerik)
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

    // Ringkasan stabil untuk laporan self-test (dibaca driver Python).
    std::string to_text() const;
};

// Array Godot: ukuran bertanda int64_t, elemen Variant.
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
};

// Dictionary ordered: vector pasangan (urutan insert) + pencarian linear.
// Jumlah kunci per level belasan, jadi linear search lebih jelas daripada map.
class Dictionary {
public:
    std::vector<std::pair<Variant, Variant>> pairs;

    Dictionary() {}

    bool is_empty() const { return pairs.empty(); }
    int64_t size() const { return (int64_t)pairs.size(); }
    bool has_key_variant(const Variant &key) const;
    Variant &operator[](const Variant &key);
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

// ClassDB::bind_static_method + D_METHOD cukup jadi no-op di self-test: yang
// diuji tabel + logika, bukan lapisan binding (itu ranah engine test
// LevelDataGdextParityTest). Alamat tiap method static tetap dievaluasi, jadi
// method yang hilang/berubah tanda tangan tetap gagal compile di sini.
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

// Deklarasi kelas yang didefinisikan levels_processor.cpp. Header asli
// (levels_processor.h) dilewati lewat include guard-nya karena menarik
// godot-cpp; daftar method di sini harus sama dengan yang di-bind generator
// (diperiksa tools/test_godot_level_data_parity.py).
#ifndef MYSTIC_LEVELS_PROCESSOR_H
#define MYSTIC_LEVELS_PROCESSOR_H
namespace godot {
class MysticLevels {
public:
    static Array all_levels();
    static Variant get_level_config(int64_t level_number);
    static int64_t get_level_count();
    static bool is_level_unlocked(int64_t level_number, const Array &completed_levels);
    static Variant get_next_level(int64_t current_level);
    static Dictionary build_row(int64_t index);
    static int64_t row_index(int64_t level_number);
    static bool py_contains(const Array &haystack, const Variant &needle);
    static String catalog_signature();
    static void _bind_methods();
};
} // namespace godot
#endif

#endif // MYSTIC_LEVELS_SELFTEST_GODOT_STUB_H
