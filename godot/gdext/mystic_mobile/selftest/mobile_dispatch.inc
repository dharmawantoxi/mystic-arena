// ═══ GENERATED — JANGAN SUNTING TANGAN ═══
// Tabel perintah self-test untuk SELURUH API MysticMobile (66 fungsi).
// Dibangkitkan tools/gen_mobile_cpp.py bersama mobile_processor.{h,cpp};
// diperiksa ulang oleh tools/test_mobile_cpp_selftest.py (closed-world:
// jumlah entri == jumlah bind_static_method di _bind_methods).

// {nama, jumlah argumen, pemanggil}
    {"module_names", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::module_names());
    }},
    {"module_names_string", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::module_names_string());
    }},
    {"api_signature", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::api_signature());
    }},
    {"touch_constants", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::touch_constants());
    }},
    {"motion_velocity", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::motion_velocity(to_double(a[0], e), to_double(a[1], e)));
    }},
    {"motion_exceeds_slop", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::motion_exceeds_slop(to_double(a[0], e)));
    }},
    {"scroll_notch", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::scroll_notch(to_double(a[0], e)));
    }},
    {"tap_is_double", 3, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::tap_is_double(to_double(a[0], e), to_double(a[1], e), to_double(a[2], e)));
    }},
    {"release_is_fling", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::release_is_fling(to_bool(a[0], e), to_double(a[1], e)));
    }},
    {"fling_steps", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::fling_steps(to_double(a[0], e)));
    }},
    {"fling_direction", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::fling_direction(to_double(a[0], e)));
    }},
    {"fling_decay", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::fling_decay(to_double(a[0], e)));
    }},
    {"fling_active", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::fling_active(to_double(a[0], e)));
    }},
    {"long_press_due", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::long_press_due(to_double(a[0], e)));
    }},
    {"dispatch_button", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::dispatch_button(to_string(a[0], e), to_int(a[1], e)));
    }},
    {"hud_min_tap", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::hud_min_tap());
    }},
    {"hud_button_rects", 4, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::hud_button_rects(to_int(a[0], e), to_int(a[1], e), to_int(a[2], e), to_int(a[3], e)));
    }},
    {"hud_hit_rect", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::hud_hit_rect(to_rect2(a[0], e)));
    }},
    {"hud_button_contains", 3, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::hud_button_contains(to_bool(a[0], e), to_rect2(a[1], e), to_vector2(a[2], e)));
    }},
    {"hud_visibility", 7, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::hud_visibility(to_bool(a[0], e), to_bool(a[1], e), to_bool(a[2], e), to_bool(a[3], e), to_bool(a[4], e), to_bool(a[5], e), to_bool(a[6], e)));
    }},
    {"hud_press_anim_next", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::hud_press_anim_next(to_double(a[0], e)));
    }},
    {"hud_colors", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::hud_colors());
    }},
    {"hud_skill_labels", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::hud_skill_labels());
    }},
    {"hud_skill_names", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::hud_skill_names());
    }},
    {"tactical_actions", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::tactical_actions());
    }},
    {"quality_levels", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::quality_levels());
    }},
    {"quality_preset", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::quality_preset(to_string(a[0], e)));
    }},
    {"quality_defaults", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::quality_defaults());
    }},
    {"particle_ratio_effective", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::particle_ratio_effective(to_double(a[0], e), to_double(a[1], e)));
    }},
    {"fx_load_target", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::fx_load_target(to_int(a[0], e)));
    }},
    {"fx_load_next", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::fx_load_next(to_double(a[0], e), to_double(a[1], e)));
    }},
    {"fx_token_budgets", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::fx_token_budgets(to_double(a[0], e)));
    }},
    {"auto_detect_quality", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::auto_detect_quality(to_bool(a[0], e)));
    }},
    {"adaptive_thresholds", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::adaptive_thresholds());
    }},
    {"adaptive_quality_decision", 3, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::adaptive_quality_decision(to_string(a[0], e), to_double(a[1], e), to_int(a[2], e)));
    }},
    {"logical_size", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::logical_size());
    }},
    {"detect_android", 3, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::detect_android(to_bool(a[0], e), to_bool(a[1], e), to_bool(a[2], e)));
    }},
    {"touch_mode", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::touch_mode(to_bool(a[0], e), to_string(a[1], e)));
    }},
    {"safe_area", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::safe_area(to_bool(a[0], e)));
    }},
    {"panel_zones", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::panel_zones());
    }},
    {"panel_popup_pos", 8, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::panel_popup_pos(to_bool(a[0], e), to_int(a[1], e), to_int(a[2], e), to_int(a[3], e), to_int(a[4], e), to_int(a[5], e), to_int(a[6], e), to_int(a[7], e)));
    }},
    {"panel_pos_bawah", 7, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::panel_pos_bawah(to_bool(a[0], e), to_int(a[1], e), to_int(a[2], e), to_int(a[3], e), to_int(a[4], e), to_int(a[5], e), to_int(a[6], e)));
    }},
    {"window_to_logical", 5, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::window_to_logical(to_double(a[0], e), to_double(a[1], e), to_double(a[2], e), to_double(a[3], e), to_double(a[4], e)));
    }},
    {"pointer_to_logical", 6, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::pointer_to_logical(to_int(a[0], e), to_double(a[1], e), to_double(a[2], e), to_double(a[3], e), to_double(a[4], e), to_double(a[5], e)));
    }},
    {"debug_modes", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::debug_modes());
    }},
    {"debug_next_mode", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::debug_next_mode(to_int(a[0], e)));
    }},
    {"debug_wrap_mode", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::debug_wrap_mode(to_int(a[0], e)));
    }},
    {"debug_is_enabled", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::debug_is_enabled(to_int(a[0], e)));
    }},
    {"fps_color", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::fps_color(to_double(a[0], e)));
    }},
    {"debug_slow_frame", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::debug_slow_frame(to_double(a[0], e)));
    }},
    {"perf_log_line", 7, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::perf_log_line(to_double(a[0], e), to_double(a[1], e), to_double(a[2], e), to_double(a[3], e), to_string(a[4], e), to_string(a[5], e), to_string(a[6], e)));
    }},
    {"attack_sound_kind", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::attack_sound_kind(to_double(a[0], e)));
    }},
    {"tower_sound_kind", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::tower_sound_kind(to_string(a[0], e)));
    }},
    {"sound_kinds", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::sound_kinds());
    }},
    {"sound_config", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::sound_config());
    }},
    {"sound_patterns", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::sound_patterns());
    }},
    {"frame_sound_budget", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::frame_sound_budget());
    }},
    {"play_gate", 5, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::play_gate(to_double(a[0], e), to_double(a[1], e), to_int(a[2], e), to_bool(a[3], e), to_int(a[4], e)));
    }},
    {"combat_stats_text", 4, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::combat_stats_text(to_int(a[0], e), to_int(a[1], e), to_int(a[2], e), to_int(a[3], e)));
    }},
    {"cloud_constants", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::cloud_constants());
    }},
    {"payload_gate", 6, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::payload_gate(to_bool(a[0], e), to_bool(a[1], e), to_bool(a[2], e), to_int(a[3], e), to_bool(a[4], e), to_bool(a[5], e)));
    }},
    {"payload_summary", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::payload_summary(to_array(a[0], e), to_double(a[1], e)));
    }},
    {"build_constants", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::build_constants());
    }},
    {"build_key_files", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::build_key_files());
    }},
    {"fingerprint_text", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::fingerprint_text(to_int(a[0], e), to_int(a[1], e)));
    }},
    {"build_label", 3, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticMobile::build_label(to_string(a[0], e), to_string(a[1], e), to_string(a[2], e)));
    }},
