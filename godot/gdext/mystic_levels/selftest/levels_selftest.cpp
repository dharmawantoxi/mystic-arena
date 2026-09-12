// levels_selftest.cpp — JALANKAN levels_processor.cpp di luar engine.
//
// Kenapa: memverifikasi tabel 54 level + logika helper C++ tidak harus menunggu
// build godot-cpp (±10 menit) atau engine Godot terunduh. Berkas ini
// meng-include .cpp hasil generator APA ADANYA (bukan salinan logikanya) lewat
// stub Variant/Array/Dictionary di godot_stub.hpp, jadi yang dieksekusi adalah
// kode yang sama persis dengan yang masuk lib .so.
//
// Protokol: satu perintah per baris di stdin, field dipisah TAB
//   <id>\t<count>\t[<arg>\t...]
// Argumen = teks Variant (lihat parse_variant: "int:3", "float:1.05",
// "str:abc", "bool:true", "nil", "[int:1,float:2.0]"). Balasan satu baris
//   <id>\t<teks Variant hasil>
// Driver Python (tools/test_levels_cpp_selftest.py) yang membangun daftar
// perintah dari oracle levels/level_data.py dan membandingkan balasannya.
//
// Build + jalan (butuh compiler saja, tanpa godot-cpp):
//   g++ -std=c++17 -O0 -I godot/gdext/mystic_levels/selftest
//       -I godot/gdext/mystic_levels/selftest/shim
//       -o /tmp/levels_selftest godot/gdext/mystic_levels/selftest/levels_selftest.cpp
//   (satu perintah; baris dipisah di sini hanya supaya tidak jadi komentar
//   multi-baris karena backslash di ujung baris //)
//   printf 'a\tcount\n' | /tmp/levels_selftest     -> a\tint:54
//
// Perutean argumen mengikuti LevelDBLoader.gd: hanya nilai yang loader benar-
// benar kirim ke C++ (int / float bulat) yang boleh masuk; tipe lain = error,
// supaya self-test tidak diam-diam "memperbaiki" deviasi yang sudah diputuskan
// di loader (contoh: get_level_config("3") dan get_next_level(3.0) tetap di
// jalur GDScript karena Python-nya berbeda).
#include "godot_stub.hpp"

#include <cstdlib>
#include <cstring>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

// Header asli (levels_processor.h) menarik godot-cpp; guard-nya sudah
// didefinisikan godot_stub.hpp sehingga include di baris pertama .cpp jadi
// no-op dan deklarasi kelas datang dari stub.
#include "../src/levels_processor.cpp"

using namespace godot;

namespace {

bool starts_with(const std::string &text, const char *prefix) {
    const size_t len = strlen(prefix);
    return text.size() >= len && text.compare(0, len, prefix) == 0;
}

std::string drop_prefix(const std::string &text, const char *prefix) {
    return text.substr(strlen(prefix));
}

// Pisah di koma/titik-koma tingkat atas saja (kurung siku/kurung kurawal
// dihitung kedalamannya), supaya "[int:1,[int:2]]" tidak terpotong di tengah.
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

// Teks -> Variant (kebalikan Variant::to_text di godot_stub.hpp).
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
    if (!text.empty() && text[0] == '[' && text[text.size() - 1] == ']') {
        const std::string inner = text.substr(1, text.size() - 2);
        Array out;
        if (!inner.empty()) {
            for (const std::string &part : split_top_level(inner, ',')) {
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
            for (const std::string &part : split_top_level(inner, ',')) {
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

Array parse_array(const std::string &text, std::string &r_error) {
    Variant value = parse_variant(text, r_error);
    if (!r_error.empty()) {
        return Array();
    }
    if (value.type != Variant::ARRAY || !value.arr) {
        r_error = "argumen harus array: " + text;
        return Array();
    }
    return *value.arr;
}

// Variant -> int64_t persis konversi argumen Godot (FLOAT dipangkas ke nol
// desimal, BOOL jadi 0/1). String sengaja DITOLAK: LevelDBLoader._int_key
// mengembalikan null untuk non-angka sehingga pemakai turun ke GDScript, dan
// self-test harus menolak juga supaya deviasi itu tidak tertutup di sini.
int64_t to_int64(const Variant &value, std::string &r_error) {
    r_error.clear();
    switch (value.type) {
        case Variant::INT: return value.i;
        case Variant::FLOAT: return (int64_t)value.f;
        case Variant::BOOL: return value.b ? 1 : 0;
        default: break;
    }
    r_error = "argumen bukan angka (loader merutekannya ke GDScript): " + value.to_text();
    return 0;
}

std::string require_arg(const std::vector<std::string> &args, size_t index,
                        std::string &r_error) {
    r_error.clear();
    if (index >= args.size()) {
        r_error = "argumen kurang";
        return std::string();
    }
    return args[index];
}

// Satu perintah -> teks hasil. r_error terisi kalau perintah/argumen salah.
std::string run_command(const std::string &cmd, const std::vector<std::string> &args,
                        std::string &r_error) {
    r_error.clear();

    if (cmd == "count") {
        return Variant((int64_t)MysticLevels::get_level_count()).to_text();
    }
    if (cmd == "signature") {
        return Variant(MysticLevels::catalog_signature()).to_text();
    }
    if (cmd == "bind") {
        // Menyentuh _bind_methods() supaya D_METHOD + ClassDB::bind_static_method
        // (dan alamat tiap method static) ikut terkompilasi di self-test.
        MysticLevels::_bind_methods();
        return Variant().to_text();
    }
    if (cmd == "all_levels_size") {
        const Array rows = MysticLevels::all_levels();
        return Variant((int64_t)rows.size()).to_text();
    }
    if (cmd == "all_row") {
        std::string err;
        const std::string text = require_arg(args, 0, err);
        if (!err.empty()) { r_error = err; return std::string(); }
        const int64_t index = to_int64(parse_variant(text, err), err);
        if (!err.empty()) { r_error = err; return std::string(); }
        const Array rows = MysticLevels::all_levels();
        if (index < 0 || index >= (int64_t)rows.size()) {
            return Variant().to_text(); // di luar jangkauan -> NIL
        }
        return rows[index].to_text();
    }
    if (cmd == "row") {
        std::string err;
        const std::string text = require_arg(args, 0, err);
        if (!err.empty()) { r_error = err; return std::string(); }
        const int64_t index = to_int64(parse_variant(text, err), err);
        if (!err.empty()) { r_error = err; return std::string(); }
        return Variant(MysticLevels::build_row(index)).to_text();
    }
    if (cmd == "row_index") {
        std::string err;
        const std::string text = require_arg(args, 0, err);
        if (!err.empty()) { r_error = err; return std::string(); }
        const int64_t key = to_int64(parse_variant(text, err), err);
        if (!err.empty()) { r_error = err; return std::string(); }
        return Variant(MysticLevels::row_index(key)).to_text();
    }
    if (cmd == "config") {
        std::string err;
        const std::string text = require_arg(args, 0, err);
        if (!err.empty()) { r_error = err; return std::string(); }
        const int64_t key = to_int64(parse_variant(text, err), err);
        if (!err.empty()) { r_error = err; return std::string(); }
        return MysticLevels::get_level_config(key).to_text();
    }
    if (cmd == "next") {
        std::string err;
        const std::string text = require_arg(args, 0, err);
        if (!err.empty()) { r_error = err; return std::string(); }
        const int64_t key = to_int64(parse_variant(text, err), err);
        if (!err.empty()) { r_error = err; return std::string(); }
        return MysticLevels::get_next_level(key).to_text();
    }
    if (cmd == "unlock") {
        std::string err;
        const std::string level_text = require_arg(args, 0, err);
        if (err.empty()) {
            require_arg(args, 1, err);
        }
        if (!err.empty()) { r_error = err; return std::string(); }
        const int64_t key = to_int64(parse_variant(level_text, err), err);
        if (err.empty()) {
            const Array completed = parse_array(args[1], err);
            if (err.empty()) {
                return Variant(MysticLevels::is_level_unlocked(key, completed)).to_text();
            }
        }
        r_error = err;
        return std::string();
    }
    if (cmd == "contains") {
        std::string err;
        const std::string haystack_text = require_arg(args, 0, err);
        if (err.empty()) {
            require_arg(args, 1, err);
        }
        if (!err.empty()) { r_error = err; return std::string(); }
        const Array haystack = parse_array(haystack_text, err);
        if (!err.empty()) { r_error = err; return std::string(); }
        const Variant needle = parse_variant(args[1], err);
        if (!err.empty()) { r_error = err; return std::string(); }
        return Variant(MysticLevels::py_contains(haystack, needle)).to_text();
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
