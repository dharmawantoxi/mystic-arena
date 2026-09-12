// maps_selftest.cpp — JALANKAN maps_processor.cpp di luar engine.
//
// Pola godot/gdext/mystic_levels/selftest/levels_selftest.cpp: meng-include
// .cpp hasil generator APA ADANYA lewat stub godot_stub.hpp, jadi yang
// dieksekusi adalah kode yang sama persis dengan yang masuk lib .so.
//
// Protokol: satu perintah per baris di stdin, field dipisah TAB
//   <id>\t<perintah>\t[<arg>\t...]
// Teks Variant: "int:3", "str:abc", "bool:true", "nil", "color:28,55,32,255",
// "v2:100,200", "v2s:[v2:1,2,v2:3,4]", "pc:[color:..]", "[...]", "{k=v,...}".
// Balasan satu baris: <id>\t<teks Variant hasil>. Driver Python
// (tools/test_maps_cpp_selftest.py) membangun perintah dari oracle
// map_components/_bundle.py dan membandingkan balasannya.
//
// Build + jalan (butuh compiler saja, tanpa godot-cpp):
//   g++ -std=c++17 -O0 -I godot/gdext/mystic_maps/selftest
//       -I godot/gdext/mystic_maps/selftest/shim
//       -o /tmp/maps_selftest godot/gdext/mystic_maps/selftest/maps_selftest.cpp
//   printf 'a\tcount\n' | /tmp/maps_selftest     -> a\tint:54
#include "godot_stub.hpp"

#include <cstdlib>
#include <cstring>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

// Header asli (maps_processor.h) menarik godot-cpp; guard-nya sudah
// didefinisikan godot_stub.hpp sehingga include di baris pertama .cpp jadi
// no-op dan deklarasi kelas datang dari stub.
#include "../src/maps_processor.cpp"

using namespace godot;

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
        "bool:", "int:", "float:", "str:", "color:", "v2:", "v2s:", "pc:", "nil",
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

// Pecah daftar elemen dipisah koma — atom v2:x,y / color:r,g,b,a MENGANDUNG
// koma, jadi potongan tanpa prefiks Variant digabung kembali ke elemen
// sebelumnya ("v2:90" + "590" -> "v2:90,590"). Tanda kurung sudah dilindungi
// split_top_level (v2s:[...] bersarang tidak terpotong).
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
        const float a = parts.size() == 4 ? (float)strtod(parts[3].c_str(), nullptr) / 255.0f : 1.0f;
        return Variant(Color(r, g, b, a));
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
    if (starts_with(text, "v2:")) {
        const std::vector<std::string> parts = split_all(drop_prefix(text, "v2:"), ',');
        if (parts.size() != 2) {
            r_error = "v2 butuh 2 komponen: " + text;
            return Variant();
        }
        return Variant(Vector2((float)strtod(parts[0].c_str(), nullptr),
                (float)strtod(parts[1].c_str(), nullptr)));
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

int64_t to_int64(const Variant &value, std::string &r_error) {
    r_error.clear();
    switch (value.type) {
        case Variant::INT: return value.i;
        case Variant::FLOAT: return (int64_t)value.f;
        case Variant::BOOL: return value.b ? 1 : 0;
        default: break;
    }
    r_error = "argumen bukan angka: " + value.to_text();
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

PackedVector2Array to_v2s(const Variant &value, std::string &r_error) {
    r_error.clear();
    if (value.type == Variant::PACKED_V2 && value.pv2) {
        return *value.pv2;
    }
    r_error = "argumen bukan v2s: " + value.to_text();
    return PackedVector2Array();
}

Array to_array(const Variant &value, std::string &r_error) {
    r_error.clear();
    if (value.type == Variant::ARRAY && value.arr) {
        return *value.arr;
    }
    r_error = "argumen bukan array: " + value.to_text();
    return Array();
}

std::string run_command(const std::string &cmd, const std::vector<std::string> &args,
                        std::string &r_error) {
    r_error.clear();

    if (cmd == "signature") {
        return Variant(MysticMaps::catalog_signature()).to_text();
    }
    if (cmd == "bind") {
        MysticMaps::_bind_methods();
        return Variant().to_text();
    }
    if (cmd == "count") {
        return Variant((int64_t)MysticMaps::theme_count()).to_text();
    }
    if (cmd == "tile") {
        return Variant((int64_t)MysticMaps::tile_size()).to_text();
    }
    if (cmd == "names") {
        return Variant(MysticMaps::theme_names()).to_text();
    }
    if (cmd == "palettes") {
        return Variant(MysticMaps::palettes()).to_text();
    }
    if (cmd == "theme") {
        std::string err;
        const std::string text = require_arg(args, 0, err);
        if (!err.empty()) { r_error = err; return std::string(); }
        const int64_t index = to_int64(parse_variant(text, err), err);
        if (!err.empty()) { r_error = err; return std::string(); }
        return Variant(MysticMaps::build_theme(index)).to_text();
    }
    if (cmd == "theme_by_name") {
        std::string err;
        const std::string text = require_arg(args, 0, err);
        if (!err.empty()) { r_error = err; return std::string(); }
        const Variant name = parse_variant(text, err);
        if (!err.empty()) { r_error = err; return std::string(); }
        if (name.type != Variant::STRING || !name.str) {
            r_error = "nama tema harus str";
            return std::string();
        }
        return Variant(MysticMaps::get_theme(*name.str)).to_text();
    }
    if (cmd == "theme_index") {
        std::string err;
        const std::string text = require_arg(args, 0, err);
        if (!err.empty()) { r_error = err; return std::string(); }
        const Variant name = parse_variant(text, err);
        if (!err.empty()) { r_error = err; return std::string(); }
        if (name.type != Variant::STRING || !name.str) {
            r_error = "nama tema harus str";
            return std::string();
        }
        return Variant((int64_t)MysticMaps::theme_index(*name.str)).to_text();
    }
    if (cmd == "all_themes_size") {
        return Variant((int64_t)MysticMaps::all_themes().size()).to_text();
    }
    if (cmd == "curve") {
        std::string err;
        const std::string wps = require_arg(args, 0, err);
        if (err.empty()) {
            require_arg(args, 1, err);
        }
        if (!err.empty()) { r_error = err; return std::string(); }
        const PackedVector2Array waypoints = to_v2s(parse_variant(wps, err), err);
        if (!err.empty()) { r_error = err; return std::string(); }
        const int64_t smoothness = to_int64(parse_variant(args[1], err), err);
        if (!err.empty()) { r_error = err; return std::string(); }
        return Variant(MysticMaps::make_curved_path(waypoints, smoothness)).to_text();
    }
    if (cmd == "lanes") {
        std::string err;
        const std::string ws = require_arg(args, 0, err);
        if (err.empty()) {
            require_arg(args, 1, err);
        }
        if (!err.empty()) { r_error = err; return std::string(); }
        const int64_t map_w = to_int64(parse_variant(ws, err), err);
        if (err.empty()) {
            const int64_t map_h = to_int64(parse_variant(args[1], err), err);
            if (err.empty()) {
                return Variant(MysticMaps::generate_lanes(map_w, map_h)).to_text();
            }
        }
        r_error = err;
        return std::string();
    }
    if (cmd == "river") {
        std::string err;
        const std::string ws = require_arg(args, 0, err);
        if (err.empty()) {
            require_arg(args, 1, err);
        }
        if (!err.empty()) { r_error = err; return std::string(); }
        const int64_t map_w = to_int64(parse_variant(ws, err), err);
        if (err.empty()) {
            const int64_t map_h = to_int64(parse_variant(args[1], err), err);
            if (err.empty()) {
                return Variant(MysticMaps::generate_river(map_w, map_h)).to_text();
            }
        }
        r_error = err;
        return std::string();
    }
    if (cmd == "decor") {
        std::string err;
        for (size_t i = 0; i < 5 && err.empty(); i++) {
            require_arg(args, i, err);
        }
        if (!err.empty()) { r_error = err; return std::string(); }
        const int64_t map_w = to_int64(parse_variant(args[0], err), err);
        const int64_t map_h = err.empty() ? to_int64(parse_variant(args[1], err), err) : 0;
        const PackedVector2Array lane_points =
            err.empty() ? to_v2s(parse_variant(args[2], err), err) : PackedVector2Array();
        const PackedVector2Array river_points =
            err.empty() ? to_v2s(parse_variant(args[3], err), err) : PackedVector2Array();
        const Array shops =
            err.empty() ? to_array(parse_variant(args[4], err), err) : Array();
        if (!err.empty()) {
            r_error = err;
            return std::string();
        }
        return Variant(MysticMaps::generate_decorations(map_w, map_h, lane_points, river_points, shops)).to_text();
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
