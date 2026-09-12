// splash_selftest.cpp — JALANKAN splash_processor.cpp di luar engine.
//
// Pola godot/gdext/mystic_ui/selftest/ui_selftest.cpp: deklarasi kelas TIDAK
// disalin — splash_processor.h ikut di-parse apa adanya (include godot-cpp
// diarahkan ke shim kosong oleh -Ishim + godot_stub.hpp), jadi API yang diuji
// selalu sama dengan API hasil generate.
//
// Protokol: satu perintah per baris di stdin, field dipisah TAB
//   <id>\t<perintah>\t[<arg>\t...]
// Perintah:
//   bind                      — panggil MysticSplash::_bind_methods()
//                               (memastikan seluruh bind_static_method bisa
//                               dibangun)
//   count                     — jumlah entri tabel perintah (closed-world CI)
//   fn\t<nama>\t<arg>...      — panggil satu fungsi MysticSplash dengan
//                               argumen Variant; tabel perintah datang dari
//                               splash_dispatch.inc HASIL GENERATOR, jadi
//                               fungsi baru otomatis bisa diuji tanpa
//                               menyunting berkas ini.
// Balasan satu baris: <id>\t<teks Variant hasil>.
//
// Teks Variant: "int:3", "str:abc", "bool:true", "float:0.5", "nil",
// "color:28,55,32,255", "v2:100,200", "rect:10,10,20,20", "[...]", "{k=v,...}".
// Driver Python (tools/test_splash_cpp_selftest.py) membangun perintah dari
// oracle pygame splash_screen.py (fixture splash_parity.json) + generator dan
// membandingkan balasannya.
//
// Build + jalan (butuh compiler saja, tanpa godot-cpp):
//   g++ -std=c++17 -O0 -I godot/gdext/mystic_splash/selftest
//       -I godot/gdext/mystic_splash/selftest/shim
//       -o /tmp/splash_selftest godot/gdext/mystic_splash/selftest/splash_selftest.cpp
//   printf 'a\tfn\tsplash_duration\n' | /tmp/splash_selftest   -> a\tfloat:3
#include "godot_stub.hpp"

#include <cstdlib>
#include <cstring>
#include <functional>
#include <iostream>
#include <string>
#include <utility>
#include <vector>

// Header asli (ui_processor.h) menarik godot-cpp; guard-nya sudah disiapkan
// (stub menyediakan RefCounted/GDCLASS, shim menetralkan include godot-cpp),
// lalu definisi kelas datang dari header hasil generate itu sendiri.
#include "../src/splash_processor.cpp"

using namespace godot;

// _bind_methods() protected di header hasil generate (seperti godot-cpp biasa);
// kelas turunan boleh memanggilnya, jadi harness tidak perlu memodifikasi
// berkas generated.
struct MysticSplashBindingProbe : public MysticSplash {
    static void run() { MysticSplash::_bind_methods(); }
};

namespace {

bool starts_with(const std::string &text, const char *prefix) {
    const size_t len = strlen(prefix);
    return text.size() >= len && text.compare(0, len, prefix) == 0;
}

std::string drop_prefix(const std::string &text, const char *prefix) {
    return text.substr(strlen(prefix));
}

std::vector<std::string> split_top_level(const std::string &text, char sep) {
    std::vector<std::string> out;
    std::string current;
    int depth = 0;
    for (size_t i = 0; i < text.size(); i++) {
        const char c = text[i];
        if (c == '[' || c == '{') {
            depth++;
        } else if (c == ']' || c == '}') {
            depth--;
        }
        if (c == sep && depth == 0) {
            out.push_back(current);
            current.clear();
            continue;
        }
        current += c;
    }
    if (!current.empty() || !text.empty()) {
        out.push_back(current);
    }
    return out;
}

std::vector<std::string> split_all(const std::string &text, char sep) {
    std::vector<std::string> out;
    std::string current;
    for (size_t i = 0; i < text.size(); i++) {
        if (text[i] == sep) {
            out.push_back(current);
            current.clear();
            continue;
        }
        current += text[i];
    }
    out.push_back(current);
    return out;
}

bool starts_with_variant_prefix(const std::string &part) {
    static const char *prefixes[] = {
        "bool:", "int:", "float:", "str:", "color:", "v2:", "rect:",
        "v2s:", "pc:", "nil",
    };
    if (!part.empty() && (part[0] == '[' || part[0] == '{')) {
        return true;
    }
    for (size_t i = 0; i < sizeof(prefixes) / sizeof(prefixes[0]); i++) {
        if (starts_with(part, prefixes[i])) {
            return true;
        }
    }
    return false;
}

// Pecah daftar elemen dipisah koma — atom v2:x,y / color:r,g,b,a / rect:x,y,w,h
// MENGANDUNG koma, jadi potongan tanpa prefiks Variant digabung kembali ke
// elemen sebelumnya ("v2:90" + "590" -> "v2:90,590").
std::vector<std::string> split_elements(const std::string &inner) {
    const std::vector<std::string> raw = split_top_level(inner, ',');
    std::vector<std::string> out;
    for (size_t i = 0; i < raw.size(); i++) {
        if (!out.empty() && !starts_with_variant_prefix(raw[i])) {
            out.back() += "," + raw[i];
        } else {
            out.push_back(raw[i]);
        }
    }
    return out;
}

Variant parse_variant(const std::string &text, std::string &r_error) {
    r_error.clear();
    if (text == "nil" || text == "nil:null") {
        return Variant();
    }
    if (starts_with(text, "bool:")) {
        return Variant(drop_prefix(text, "bool:") == "true");
    }
    if (starts_with(text, "int:")) {
        return Variant((int64_t)strtoll(drop_prefix(text, "int:").c_str(), nullptr, 10));
    }
    if (starts_with(text, "float:")) {
        return Variant(strtod(drop_prefix(text, "float:").c_str(), nullptr));
    }
    if (starts_with(text, "str:")) {
        return Variant(String(drop_prefix(text, "str:").c_str()));
    }
    if (starts_with(text, "color:")) {
        const std::vector<std::string> parts = split_all(drop_prefix(text, "color:"), ',');
        if (parts.size() != 3 && parts.size() != 4) {
            r_error = "color butuh 3/4 kanal: " + text;
            return Variant();
        }
        const float r = (float)strtod(parts[0].c_str(), nullptr) / 255.0f;
        const float g = (float)strtod(parts[1].c_str(), nullptr) / 255.0f;
        const float b = (float)strtod(parts[2].c_str(), nullptr) / 255.0f;
        const float a = parts.size() == 4
                            ? (float)strtod(parts[3].c_str(), nullptr) / 255.0f
                            : 1.0f;
        return Variant(Color(r, g, b, a));
    }
    if (starts_with(text, "v2:")) {
        const std::vector<std::string> parts = split_all(drop_prefix(text, "v2:"), ',');
        if (parts.size() != 2) {
            r_error = "v2 butuh 2 komponen: " + text;
            return Variant();
        }
        return Variant(Vector2((float)strtod(parts[0].c_str(), nullptr),
                               (float)strtod(parts[1].c_str(), nullptr)));
    }
    if (starts_with(text, "rect:")) {
        const std::vector<std::string> parts = split_all(drop_prefix(text, "rect:"), ',');
        if (parts.size() != 4) {
            r_error = "rect butuh 4 komponen: " + text;
            return Variant();
        }
        return Variant(Rect2((float)strtod(parts[0].c_str(), nullptr),
                             (float)strtod(parts[1].c_str(), nullptr),
                             (float)strtod(parts[2].c_str(), nullptr),
                             (float)strtod(parts[3].c_str(), nullptr)));
    }
    if (starts_with(text, "v2s:")) {
        const std::string rest = drop_prefix(text, "v2s:");
        if (rest.size() < 2 || rest[0] != '[' || rest[rest.size() - 1] != ']') {
            r_error = "v2s harus [..]: " + text;
            return Variant();
        }
        PackedVector2Array out;
        const std::string inner = rest.substr(1, rest.size() - 2);
        if (!inner.empty()) {
            for (const std::string &part : split_elements(inner)) {
                std::string err;
                const Variant v = parse_variant(part, err);
                if (!err.empty()) {
                    r_error = err;
                    return Variant();
                }
                if (v.type != Variant::VECTOR2) {
                    r_error = "elemen v2s bukan v2: " + part;
                    return Variant();
                }
                out.append(v.v2);
            }
        }
        return Variant(out);
    }
    if (starts_with(text, "pc:")) {
        const std::string rest = drop_prefix(text, "pc:");
        if (rest.size() < 2 || rest[0] != '[' || rest[rest.size() - 1] != ']') {
            r_error = "pc harus [..]: " + text;
            return Variant();
        }
        PackedColorArray out;
        const std::string inner = rest.substr(1, rest.size() - 2);
        if (!inner.empty()) {
            for (const std::string &part : split_elements(inner)) {
                std::string err;
                const Variant v = parse_variant(part, err);
                if (!err.empty()) {
                    r_error = err;
                    return Variant();
                }
                if (v.type != Variant::COLOR) {
                    r_error = "elemen pc bukan color: " + part;
                    return Variant();
                }
                out.append(v.c);
            }
        }
        return Variant(out);
    }
    if (!text.empty() && text[0] == '[' && text[text.size() - 1] == ']') {
        const std::string inner = text.substr(1, text.size() - 2);
        Array out;
        if (!inner.empty()) {
            for (const std::string &part : split_elements(inner)) {
                std::string err;
                out.push_back(parse_variant(part, err));
                if (!err.empty()) {
                    r_error = err;
                    return Variant();
                }
            }
        }
        return Variant(out);
    }
    if (!text.empty() && text[0] == '{' && text[text.size() - 1] == '}') {
        const std::string inner = text.substr(1, text.size() - 2);
        Dictionary out;
        if (!inner.empty()) {
            for (const std::string &part : split_elements(inner)) {
                const size_t eq = part.find('=');
                if (eq == std::string::npos) {
                    r_error = "dict tanpa '=': " + part;
                    return Variant();
                }
                std::string err;
                const Variant key = parse_variant(part.substr(0, eq), err);
                if (!err.empty()) {
                    r_error = err;
                    return Variant();
                }
                const Variant value = parse_variant(part.substr(eq + 1), err);
                if (!err.empty()) {
                    r_error = err;
                    return Variant();
                }
                out[key] = value;
            }
        }
        return Variant(out);
    }
    r_error = "teks Variant tak dikenal: " + text;
    return Variant();
}

// ── Konverter argumen (dipakai ui_dispatch.inc hasil generator) ──────────

int64_t to_int(const Variant &value, std::string &r_error) {
    switch (value.type) {
        case Variant::INT: return value.i;
        case Variant::FLOAT: return (int64_t)value.f;
        case Variant::BOOL: return value.b ? 1 : 0;
        default: break;
    }
    r_error = "argumen bukan angka: " + value.to_text();
    return 0;
}

double to_double(const Variant &value, std::string &r_error) {
    switch (value.type) {
        case Variant::INT: return (double)value.i;
        case Variant::FLOAT: return value.f;
        case Variant::BOOL: return value.b ? 1.0 : 0.0;
        default: break;
    }
    r_error = "argumen bukan angka: " + value.to_text();
    return 0.0;
}

bool to_bool(const Variant &value, std::string &r_error) {
    switch (value.type) {
        case Variant::BOOL: return value.b;
        case Variant::INT: return value.i != 0;
        case Variant::FLOAT: return value.f != 0.0;
        default: break;
    }
    r_error = "argumen bukan bool: " + value.to_text();
    return false;
}

String to_string(const Variant &value, std::string &r_error) {
    if (value.type == Variant::STRING && value.str) {
        return *value.str;
    }
    r_error = "argumen bukan str: " + value.to_text();
    return String();
}

Color to_color(const Variant &value, std::string &r_error) {
    if (value.type == Variant::COLOR) {
        return value.c;
    }
    r_error = "argumen bukan color: " + value.to_text();
    return Color();
}

Vector2 to_vector2(const Variant &value, std::string &r_error) {
    if (value.type == Variant::VECTOR2) {
        return value.v2;
    }
    r_error = "argumen bukan v2: " + value.to_text();
    return Vector2();
}

Rect2 to_rect2(const Variant &value, std::string &r_error) {
    if (value.type == Variant::RECT2) {
        return value.rect;
    }
    r_error = "argumen bukan rect: " + value.to_text();
    return Rect2();
}

Array to_array(const Variant &value, std::string &r_error) {
    if (value.type == Variant::ARRAY && value.arr) {
        return *value.arr;
    }
    r_error = "argumen bukan array: " + value.to_text();
    return Array();
}

Dictionary to_dict(const Variant &value, std::string &r_error) {
    if (value.type == Variant::DICTIONARY && value.dict) {
        return *value.dict;
    }
    r_error = "argumen bukan dict: " + value.to_text();
    return Dictionary();
}

// Konverter yang belum dipakai API saat ini (String/Array/Dictionary) tetap
// dipertahankan: begitu generator menambah fungsi berargumen tipe itu, tabel
// perintah langsung memakainya. Ambil alamatnya supaya -Wall tidak ribut.
namespace {
struct ConverterKeepAlive {
    ConverterKeepAlive() {
        (void)&to_string;
        (void)&to_array;
        (void)&to_dict;
    }
};
const ConverterKeepAlive _converter_keep_alive;
} // namespace

// ── Tabel perintah dari generator ────────────────────────────────────────

using CommandFn = std::function<Variant(const std::vector<Variant> &, std::string &)>;

struct Command {
    const char *name;
    size_t argc;
    CommandFn fn;
};

const Command COMMANDS[] = {
#include "splash_dispatch.inc"
};

const size_t COMMAND_COUNT = sizeof(COMMANDS) / sizeof(COMMANDS[0]);

const Command *find_command(const std::string &name) {
    for (size_t i = 0; i < COMMAND_COUNT; i++) {
        if (name == COMMANDS[i].name) {
            return &COMMANDS[i];
        }
    }
    return nullptr;
}

std::string run_command(const std::string &cmd, const std::vector<std::string> &args,
                        std::string &r_error) {
    r_error.clear();

    if (cmd == "bind") {
        MysticSplashBindingProbe::run();
        return Variant().to_text();
    }
    if (cmd == "count") {
        return Variant((int64_t)COMMAND_COUNT).to_text();
    }
    if (cmd == "fn") {
        if (args.empty()) {
            r_error = "fn butuh nama fungsi";
            return std::string();
        }
        const Command *entry = find_command(args[0]);
        if (entry == nullptr) {
            r_error = "fungsi tak terdaftar: " + args[0];
            return std::string();
        }
        if (args.size() - 1 != entry->argc) {
            r_error = "jumlah argumen salah untuk " + args[0];
            return std::string();
        }
        std::vector<Variant> values;
        for (size_t i = 1; i < args.size(); i++) {
            std::string err;
            values.push_back(parse_variant(args[i], err));
            if (!err.empty()) {
                r_error = err;
                return std::string();
            }
        }
        return entry->fn(values, r_error).to_text();
    }

    r_error = "perintah tak dikenal: " + cmd;
    return std::string();
}

} // namespace

int main() {
    std::ios::sync_with_stdio(false);
    std::string line;
    while (std::getline(std::cin, line)) {
        if (line.empty()) {
            continue;
        }
        const std::vector<std::string> fields = split_top_level(line, '\t');
        const std::string id = fields.empty() ? std::string("?") : fields[0];
        const std::string cmd = fields.size() > 1 ? fields[1] : std::string();
        std::vector<std::string> args;
        for (size_t i = 2; i < fields.size(); i++) {
            args.push_back(fields[i]);
        }
        std::string error;
        const std::string result = run_command(cmd, args, error);
        std::cout << id << '\t' << (error.empty() ? result : "error:" + error) << '\n';
    }
    std::cout.flush();
    return 0;
}
