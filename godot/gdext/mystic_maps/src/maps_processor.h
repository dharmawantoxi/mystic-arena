#ifndef MYSTIC_MAPS_PROCESSOR_H
#define MYSTIC_MAPS_PROCESSOR_H

// ═══ GENERATED — JANGAN SUNTING TANGAN ═══
// Sumber    : map_components/_bundle.py (palettes, themes, generators)
// Generator : tools/gen_maps_cpp.py (AST Python -> C++, bukan terjemahan tangan)
// Regenerasi: python3 tools/gen_maps_cpp.py
// Cek CI    : python3 tools/gen_maps_cpp.py --check
// Desain    : docs/AUDIT_ULANG_DARI_AWAL.md
//
// Port map_components/_bundle.py (54 tema, 77 kunci union, PathGenerator +
// DecorationGenerator) ke Godot C++ GDExtension. API = permukaan modul
// palettes/themes/generators: konstanta palet, get_theme, make_curved_path,
// generate_lanes, generate_river, generate_decorations.

#include <godot_cpp/classes/ref_counted.hpp>
#include <godot_cpp/core/class_db.hpp>
#include <godot_cpp/variant/array.hpp>
#include <godot_cpp/variant/color.hpp>
#include <godot_cpp/variant/dictionary.hpp>
#include <godot_cpp/variant/packed_color_array.hpp>
#include <godot_cpp/variant/packed_vector2_array.hpp>
#include <godot_cpp/variant/string.hpp>
#include <godot_cpp/variant/variant.hpp>
#include <godot_cpp/variant/vector2.hpp>
#include <cstdint>

namespace godot {

class MysticMaps : public RefCounted {
    GDCLASS(MysticMaps, RefCounted);

public:
    // ── palettes.py ──
    static int64_t tile_size();
    static Dictionary palettes();
    // ── themes.py ──
    static Array theme_names();
    static int64_t theme_count();
    static Dictionary get_theme(const String &theme_name);
    static Dictionary all_themes();
    static String catalog_signature();
    // ── generators.py: PathGenerator ──
    static PackedVector2Array make_curved_path(const PackedVector2Array &waypoints, int64_t smoothness);
    static Dictionary generate_lanes(int64_t map_w, int64_t map_h);
    static PackedVector2Array generate_river(int64_t map_w, int64_t map_h);
    // ── generators.py: DecorationGenerator ──
    static Dictionary generate_decorations(int64_t map_w, int64_t map_h,
        const PackedVector2Array &lane_points, const PackedVector2Array &river_points,
        const Array &shop_positions);

    // ── helper (dipakai loader + harness paritas; juga di-bind) ──
    // Tema ke-`index` sebagai Dictionary segar (urutan kunci = urutan literal
    // dict Python tema itu). Index di luar jangkauan -> Dictionary kosong.
    static Dictionary build_theme(int64_t index);
    // Indeks tema untuk nama, -1 kalau tidak ada (scan linear = paritas
    // THEMES.get; get_theme memakai forest untuk -1).
    static int64_t theme_index(const String &theme_name);

protected:
    static void _bind_methods();
};

} // namespace godot

#endif // MYSTIC_MAPS_PROCESSOR_H
