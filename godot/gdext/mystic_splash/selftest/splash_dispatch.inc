// ═══ GENERATED — JANGAN SUNTING TANGAN ═══
// Tabel perintah self-test untuk SELURUH API MysticSplash (62 fungsi).
// Dibangkitkan tools/gen_splash_cpp.py bersama splash_processor.{h,cpp};
// diperiksa ulang oleh tools/test_splash_cpp_selftest.py (closed-world:
// jumlah entri == jumlah bind_static_method di _bind_methods).

// {nama, jumlah argumen, pemanggil}
    {"module_names", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::module_names());
    }},
    {"module_names_string", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::module_names_string());
    }},
    {"api_signature", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::api_signature());
    }},
    {"game_name", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::game_name());
    }},
    {"tagline", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::tagline());
    }},
    {"hint_text", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::hint_text());
    }},
    {"splash_duration", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::splash_duration());
    }},
    {"logo_paths", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::logo_paths());
    }},
    {"accent", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::accent());
    }},
    {"accent_2", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::accent_2());
    }},
    {"text_main", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::text_main());
    }},
    {"text_dim", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::text_dim());
    }},
    {"gradient_stops", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::gradient_stops());
    }},
    {"particle_colors", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::particle_colors());
    }},
    {"font_sizes", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::font_sizes());
    }},
    {"font_fallback_sizes", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::font_fallback_sizes());
    }},
    {"font_styles", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::font_styles());
    }},
    {"particle_count", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::particle_count());
    }},
    {"particle_ranges", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::particle_ranges());
    }},
    {"particle_move", 6, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::particle_move(to_double(a[0], e), to_double(a[1], e), to_double(a[2], e), to_double(a[3], e), to_double(a[4], e), to_double(a[5], e)));
    }},
    {"particle_wrapped", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::particle_wrapped(to_double(a[0], e)));
    }},
    {"particle_wrap_y", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::particle_wrap_y(to_double(a[0], e)));
    }},
    {"particle_advance", 8, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::particle_advance(to_double(a[0], e), to_double(a[1], e), to_double(a[2], e), to_double(a[3], e), to_double(a[4], e), to_double(a[5], e), to_double(a[6], e), to_double(a[7], e)));
    }},
    {"particle_twinkle", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::particle_twinkle(to_double(a[0], e), to_double(a[1], e)));
    }},
    {"particle_channel", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::particle_channel(to_int(a[0], e), to_double(a[1], e)));
    }},
    {"particle_draw_color", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::particle_draw_color(to_color(a[0], e), to_double(a[1], e)));
    }},
    {"particle_draw_radius", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::particle_draw_radius(to_double(a[0], e)));
    }},
    {"particle_draw_pos", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::particle_draw_pos(to_double(a[0], e), to_double(a[1], e)));
    }},
    {"fade_in", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::fade_in(to_double(a[0], e)));
    }},
    {"fade_out_normal", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::fade_out_normal(to_double(a[0], e)));
    }},
    {"fade_out_skip", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::fade_out_skip(to_double(a[0], e)));
    }},
    {"overall_alpha", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::overall_alpha(to_double(a[0], e), to_bool(a[1], e)));
    }},
    {"overall_alpha_godot", 3, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::overall_alpha_godot(to_double(a[0], e), to_bool(a[1], e), to_double(a[2], e)));
    }},
    {"title_alpha", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::title_alpha(to_double(a[0], e)));
    }},
    {"is_done", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::is_done(to_double(a[0], e), to_bool(a[1], e)));
    }},
    {"is_done_godot", 3, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::is_done_godot(to_double(a[0], e), to_bool(a[1], e), to_double(a[2], e)));
    }},
    {"draw_visible", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::draw_visible(to_double(a[0], e)));
    }},
    {"title_alpha_drawn", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::title_alpha_drawn(to_int(a[0], e), to_double(a[1], e)));
    }},
    {"timings", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::timings());
    }},
    {"bg_step_h", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::bg_step_h(to_int(a[0], e)));
    }},
    {"bg_band_count", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::bg_band_count(to_int(a[0], e)));
    }},
    {"bg_band_rect", 3, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::bg_band_rect(to_int(a[0], e), to_int(a[1], e), to_int(a[2], e)));
    }},
    {"bg_band_color", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::bg_band_color(to_int(a[0], e), to_int(a[1], e)));
    }},
    {"bg_bands", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::bg_bands(to_int(a[0], e), to_int(a[1], e)));
    }},
    {"vignette_frames", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::vignette_frames(to_int(a[0], e), to_int(a[1], e)));
    }},
    {"content_center", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::content_center(to_int(a[0], e), to_int(a[1], e)));
    }},
    {"logo_center_y", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::logo_center_y(to_double(a[0], e), to_bool(a[1], e)));
    }},
    {"logo_scale", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::logo_scale(to_int(a[0], e), to_int(a[1], e)));
    }},
    {"logo_base_size", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::logo_base_size(to_int(a[0], e), to_int(a[1], e)));
    }},
    {"logo_grow_quant", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::logo_grow_quant(to_double(a[0], e)));
    }},
    {"logo_grow_size", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::logo_grow_size(to_vector2(a[0], e), to_double(a[1], e)));
    }},
    {"logo_glow_radius", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::logo_glow_radius(to_int(a[0], e), to_int(a[1], e)));
    }},
    {"logo_glow_rect", 3, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::logo_glow_rect(to_double(a[0], e), to_double(a[1], e), to_int(a[2], e)));
    }},
    {"logo_glow_rings", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::logo_glow_rings(to_int(a[0], e)));
    }},
    {"logo_offsets", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::logo_offsets());
    }},
    {"title_glow_layers", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::title_glow_layers(to_bool(a[0], e)));
    }},
    {"title_glow_surface", 3, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::title_glow_surface(to_rect2(a[0], e), to_int(a[1], e), to_int(a[2], e)));
    }},
    {"title_glow_fill", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::title_glow_fill(to_double(a[0], e)));
    }},
    {"accent_gap", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::accent_gap(to_int(a[0], e)));
    }},
    {"accent_lines", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::accent_lines(to_double(a[0], e)));
    }},
    {"hint_pos", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::hint_pos(to_int(a[0], e), to_int(a[1], e)));
    }},
    {"hint_alpha", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticSplash::hint_alpha(to_double(a[0], e)));
    }},
