#ifndef MYSTIC_MOBILE_PROCESSOR_H
#define MYSTIC_MOBILE_PROCESSOR_H

// ═══ GENERATED — JANGAN SUNTING TANGAN ═══
// Sumber    : mobile/ (touch, hud, perf, platform_utils, debug, combat_audio,
//             cloud_save, buildinfo)
// Generator : tools/gen_mobile_cpp.py (AST Python -> C++, bukan terjemahan
//             tangan)
// Regenerasi: python3 tools/gen_mobile_cpp.py
// Cek CI    : python3 tools/gen_mobile_cpp.py --check
// Desain    : docs/AUDIT_ULANG_DARI_AWAL.md
//
// Port paket `mobile/` ke Godot C++ GDExtension: lapisan KEPUTUSAN murni
// (ambang gesture, rect + visibility tombol HUD, preset kualitas + adaptive
// quality, zona panel kanan, warna overlay debug, gate suara tempur,
// validasi + ringkasan payload cloud, label build). Piksel (pygame.draw /
// Surface), mixer SDL, I/O berkas, dan jembatan Android tidak diport —
// backend masing-masing memanggil angka dari sini.

#include <godot_cpp/classes/ref_counted.hpp>
#include <godot_cpp/core/class_db.hpp>
#include <godot_cpp/variant/array.hpp>
#include <godot_cpp/variant/color.hpp>
#include <godot_cpp/variant/dictionary.hpp>
#include <godot_cpp/variant/rect2.hpp>
#include <godot_cpp/variant/string.hpp>
#include <godot_cpp/variant/variant.hpp>
#include <godot_cpp/variant/vector2.hpp>
#include <cstdint>

namespace godot {

class MysticMobile : public RefCounted {
    GDCLASS(MysticMobile, RefCounted);

public:
    static Array module_names();
    static String module_names_string();
    static String api_signature();
    static Dictionary touch_constants();
    static double motion_velocity(double p_prev_velocity, double p_dy);
    static bool motion_exceeds_slop(double p_total_dist);
    static Dictionary scroll_notch(double p_accum);
    static bool tap_is_double(double p_dt_ms, double p_dx, double p_dy);
    static bool release_is_fling(bool p_moved, double p_velocity);
    static int64_t fling_steps(double p_velocity);
    static int64_t fling_direction(double p_velocity);
    static double fling_decay(double p_velocity);
    static bool fling_active(double p_velocity);
    static bool long_press_due(double p_held_ms);
    static int64_t dispatch_button(const String & p_kind, int64_t p_value);
    static int64_t hud_min_tap();
    static Dictionary hud_button_rects(int64_t p_safe_left, int64_t p_safe_top, int64_t p_safe_right, int64_t p_safe_bottom);
    static Rect2 hud_hit_rect(const Rect2 & p_rect);
    static bool hud_button_contains(bool p_visible, const Rect2 & p_hit_rect, const Vector2 & p_pos);
    static Dictionary hud_visibility(bool p_playing, bool p_ended, bool p_victory, bool p_has_next_level, bool p_cinematic_active, bool p_panel_ada, bool p_show_debug_button);
    static double hud_press_anim_next(double p_press_anim);
    static Dictionary hud_colors();
    static Dictionary hud_skill_labels();
    static Dictionary hud_skill_names();
    static Array tactical_actions();
    static Array quality_levels();
    static Dictionary quality_preset(const String & p_level);
    static Dictionary quality_defaults();
    static double particle_ratio_effective(double p_base_ratio, double p_fx_load);
    static double fx_load_target(int64_t p_n_active);
    static double fx_load_next(double p_current, double p_target);
    static Dictionary fx_token_budgets(double p_load);
    static String auto_detect_quality(bool p_is_android);
    static Dictionary adaptive_thresholds();
    static Dictionary adaptive_quality_decision(const String & p_level, double p_avg, int64_t p_cooldown);
    static Vector2 logical_size();
    static bool detect_android(bool p_env_android_argument, bool p_env_android_private, bool p_has_getandroidapilevel);
    static bool touch_mode(bool p_is_android, const String & p_force_touch_env);
    static Rect2 safe_area(bool p_touch_mode);
    static Dictionary panel_zones();
    static Variant panel_popup_pos(bool p_has_panel, int64_t p_px, int64_t p_py, int64_t p_pw, int64_t p_ph, int64_t p_w, int64_t p_h, int64_t p_atas);
    static Variant panel_pos_bawah(bool p_has_panel, int64_t p_px, int64_t p_py, int64_t p_pw, int64_t p_ph, int64_t p_w, int64_t p_h);
    static Vector2 window_to_logical(double p_x, double p_y, double p_scale, double p_off_x, double p_off_y);
    static Vector2 pointer_to_logical(int64_t p_mode, double p_x, double p_y, double p_scale, double p_off_x, double p_off_y);
    static Array debug_modes();
    static int64_t debug_next_mode(int64_t p_mode);
    static int64_t debug_wrap_mode(int64_t p_mode);
    static bool debug_is_enabled(int64_t p_mode);
    static Color fps_color(double p_fps);
    static bool debug_slow_frame(double p_frame_ms);
    static String perf_log_line(double p_fps, double p_avg_frame_ms, double p_upd_ms, double p_draw_ms, const String & p_quality, const String & p_entity_counts, const String & p_memory);
    static String attack_sound_kind(double p_distance);
    static String tower_sound_kind(const String & p_tower_type);
    static Array sound_kinds();
    static Dictionary sound_config();
    static Dictionary sound_patterns();
    static int64_t frame_sound_budget();
    static String play_gate(double p_now_ms, double p_last_ms, int64_t p_jeda_ms, bool p_boleh_rebut, int64_t p_sisa_frame);
    static String combat_stats_text(int64_t p_main, int64_t p_tolak_jeda, int64_t p_tolak_anggaran, int64_t p_tolak_channel);
    static Dictionary cloud_constants();
    static String payload_gate(bool p_is_dict, bool p_magic_ok, bool p_version_ok, int64_t p_version, bool p_slots_ok, bool p_checksum_ok);
    static Dictionary payload_summary(const Array & p_slots, double p_exported_at);
    static bool py_int_of_string(const String &text, int64_t &out);
    static bool py_float_of_string(const String &text, double &out);
    static Dictionary build_constants();
    static Array build_key_files();
    static String fingerprint_text(int64_t p_total_bytes, int64_t p_found);
    static String build_label(const String & p_build_id, const String & p_build_date, const String & p_fingerprint);
    // ── helper internal (dipakai fungsi ter-bind; TIDAK di-bind) ──
    // `//` Python (floor ke arah -inf); `%` Python untuk pembagi positif.
    static int64_t py_floordiv(int64_t a, int64_t b);
    static int64_t py_mod(int64_t a, int64_t b);

protected:
    static void _bind_methods();
};

} // namespace godot

#endif // MYSTIC_MOBILE_PROCESSOR_H
