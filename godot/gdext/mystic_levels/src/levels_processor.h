#ifndef MYSTIC_LEVELS_PROCESSOR_H
#define MYSTIC_LEVELS_PROCESSOR_H

// ═══ GENERATED — JANGAN SUNTING TANGAN ═══
// Sumber    : levels/level_data.py
// Generator : tools/gen_levels_cpp.py (AST Python -> C++, bukan terjemahan tangan)
// Regenerasi: python3 tools/gen_levels_cpp.py
// Cek CI    : python3 tools/gen_levels_cpp.py --check
// Desain    : docs/AUDIT_ULANG_DARI_AWAL.md
//
// Port levels/level_data.py (54 level, 17 field) ke Godot C++ GDExtension.
// API = persis ekspor levels/__init__.py: ALL_LEVELS, get_level_config,
// get_level_count, is_level_unlocked, get_next_level.

#include <godot_cpp/classes/ref_counted.hpp>
#include <godot_cpp/core/class_db.hpp>
#include <godot_cpp/variant/array.hpp>
#include <godot_cpp/variant/dictionary.hpp>
#include <godot_cpp/variant/string.hpp>
#include <godot_cpp/variant/variant.hpp>
#include <cstdint>

namespace godot {

class MysticLevels : public RefCounted {
    GDCLASS(MysticLevels, RefCounted);

public:
    // ── API publik (paritas levels/__init__.py) ──
    static Array all_levels();
    static Variant get_level_config(int64_t level_number);
    static int64_t get_level_count();
    static bool is_level_unlocked(int64_t level_number, const Array &completed_levels);
    static Variant get_next_level(int64_t current_level);

    // ── helper (dipakai loader + harness paritas; juga di-bind) ──
    // Baris katalog ke-`index` sebagai Dictionary segar (urutan kunci = urutan
    // literal dict Python). Index di luar jangkauan -> Dictionary kosong.
    static Dictionary build_row(int64_t index);
    // Indeks baris untuk level_number, -1 kalau tidak ada (scan linear =
    // paritas loop `for lvl in ALL_LEVELS` di get_level_config Python).
    static int64_t row_index(int64_t level_number);
    // `needle in haystack` semantik Python (== numerik int/float), BUKAN
    // Array.has() Godot yang strict-tipe (hash_compare).
    static bool py_contains(const Array &haystack, const Variant &needle);
    // Tanda tangan katalog: bukti lib termuat + tabelnya generasi yang sama.
    static String catalog_signature();

protected:
    static void _bind_methods();
};

} // namespace godot

#endif // MYSTIC_LEVELS_PROCESSOR_H
