#ifndef MYSTIC_SPLASH_PROCESSOR_H
#define MYSTIC_SPLASH_PROCESSOR_H

// ═══ GENERATED — JANGAN SUNTING TANGAN ═══
// Sumber    : splash_screen.py (splashscreen pembuka: logo + judul)
// Generator : tools/gen_splash_cpp.py (AST Python -> C++, bukan terjemahan
//             tangan)
// Regenerasi: python3 tools/gen_splash_cpp.py
// Cek CI    : python3 tools/gen_splash_cpp.py --check
// Desain    : docs/SPLASH_GODOTPP.md
//
// Port splash_screen.py ke Godot C++ GDExtension: lapisan MODEL (timing +
// fade, alpha judul, gerak/twinkle partikel, gradien + vignette latar,
// geometri logo, glow judul + garis aksen, posisi/alpha hint). Renderer
// piksel (pygame.draw / _draw Godot) tidak diport dan memanggil angka dari
// sini; metrik font diterima sebagai parameter (pola FASE 36).

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

class MysticSplash : public RefCounted {
    GDCLASS(MysticSplash, RefCounted);

public:
    static Array module_names();
    static String module_names_string();
    static String api_signature();
    static String game_name();
    static String tagline();
    static String hint_text();
    static double splash_duration();
    static Array logo_paths();
    static Color accent();
    static Color accent_2();
    static Color text_main();
    static Color text_dim();
    static Dictionary gradient_stops();
    static Array particle_colors();
    static Dictionary font_sizes();
    static Dictionary font_fallback_sizes();
    static Dictionary font_styles();
    static int64_t particle_count();
    static Dictionary particle_ranges();
    static Dictionary particle_move(double x, double y, double speed, double drift, double phase, double elapsed);
    static bool particle_wrapped(double y);
    static double particle_wrap_y(double screen_h);
    static Dictionary particle_advance(double x, double y, double speed, double drift, double phase, double elapsed, double screen_h, double respawn_x);
    static double particle_twinkle(double elapsed, double phase);
    static int64_t particle_channel(int64_t channel, double twinkle);
    static Color particle_draw_color(const Color & base, double twinkle);
    static int64_t particle_draw_radius(double r);
    static Vector2 particle_draw_pos(double x, double y);
    static double fade_in(double t);
    static double fade_out_normal(double t);
    static double fade_out_skip(double t);
    static double overall_alpha(double t, bool skipped);
    static double overall_alpha_godot(double t, bool skipped, double skip_t);
    static int64_t title_alpha(double t);
    static bool is_done(double t, bool skipped);
    static bool is_done_godot(double t, bool skipped, double skip_t);
    static bool draw_visible(double alpha);
    static int64_t title_alpha_drawn(int64_t title_alpha, double overall);
    static Dictionary timings();
    static int64_t bg_step_h(int64_t screen_h);
    static int64_t bg_band_count(int64_t screen_h);
    static Rect2 bg_band_rect(int64_t i, int64_t step_h, int64_t screen_w);
    static Color bg_band_color(int64_t i, int64_t screen_h);
    static Array bg_bands(int64_t screen_w, int64_t screen_h);
    static Array vignette_frames(int64_t screen_w, int64_t screen_h);
    static Vector2 content_center(int64_t screen_w, int64_t screen_h);
    static double logo_center_y(double base_y, bool has_logo);
    static double logo_scale(int64_t img_w, int64_t img_h);
    static Vector2 logo_base_size(int64_t img_w, int64_t img_h);
    static double logo_grow_quant(double elapsed);
    static Vector2 logo_grow_size(const Vector2 & base, double gq);
    static int64_t logo_glow_radius(int64_t ww, int64_t hh);
    static Rect2 logo_glow_rect(double cx, double cy, int64_t glow_r);
    static Array logo_glow_rings(int64_t glow_r);
    static Dictionary logo_offsets();
    static Array title_glow_layers(bool cheap);
    static Rect2 title_glow_surface(const Rect2 & text_rect, int64_t layer, int64_t spread);
    static int64_t title_glow_fill(double alpha);
    static int64_t accent_gap(int64_t text_w);
    static Array accent_lines(double alpha);
    static Vector2 hint_pos(int64_t screen_w, int64_t screen_h);
    static int64_t hint_alpha(double overall);

    // ── helper internal (dipakai fungsi ter-bind; TIDAK di-bind) ──
    static int64_t py_round(double value);
    static int64_t py_int(double value);

protected:
    static void _bind_methods();
};

} // namespace godot

#endif // MYSTIC_SPLASH_PROCESSOR_H
