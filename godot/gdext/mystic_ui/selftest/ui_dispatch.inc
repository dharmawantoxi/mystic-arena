// ═══ GENERATED — JANGAN SUNTING TANGAN ═══
// Tabel perintah self-test untuk SELURUH API MysticUI (80 fungsi).
// Dibangkitkan tools/gen_ui_cpp.py bersama ui_processor.{h,cpp};
// diperiksa ulang oleh tools/test_ui_cpp_selftest.py (closed-world:
// jumlah entri == jumlah bind_static_method di _bind_methods).

// {nama, jumlah argumen, pemanggil}
    {"module_names", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::module_names());
    }},
    {"module_names_string", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::module_names_string());
    }},
    {"api_signature", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::api_signature());
    }},
    {"tower_type_colors", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::tower_type_colors());
    }},
    {"tower_cards", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::tower_cards());
    }},
    {"build_cost", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::build_cost());
    }},
    {"notification_duration", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::notification_duration());
    }},
    {"close_button_rect", 3, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::close_button_rect(to_int(a[0], e), to_int(a[1], e), to_int(a[2], e)));
    }},
    {"hp_bar_color", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::hp_bar_color(to_double(a[0], e)));
    }},
    {"hp_bar_fill", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::hp_bar_fill(to_int(a[0], e), to_double(a[1], e)));
    }},
    {"shadow_rect", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::shadow_rect(to_rect2(a[0], e), to_vector2(a[1], e)));
    }},
    {"popup_width", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::popup_width(to_int(a[0], e), to_int(a[1], e)));
    }},
    {"build_popup_rect", 4, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::build_popup_rect(to_int(a[0], e), to_int(a[1], e), to_int(a[2], e), to_int(a[3], e)));
    }},
    {"target_popup_rect", 5, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::target_popup_rect(to_int(a[0], e), to_int(a[1], e), to_int(a[2], e), to_int(a[3], e), to_int(a[4], e)));
    }},
    {"build_popup_buttons", 3, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::build_popup_buttons(to_int(a[0], e), to_int(a[1], e), to_int(a[2], e)));
    }},
    {"build_gold_text", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::build_gold_text(to_int(a[0], e)));
    }},
    {"build_button_style", 3, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::build_button_style(to_bool(a[0], e), to_bool(a[1], e), to_color(a[2], e)));
    }},
    {"hover_hit", 3, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::hover_hit(to_rect2(a[0], e), to_vector2(a[1], e), to_bool(a[2], e)));
    }},
    {"slot_blit_offset", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::slot_blit_offset());
    }},
    {"slot_surface_rect", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::slot_surface_rect(to_int(a[0], e), to_int(a[1], e)));
    }},
    {"slot_pulse", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::slot_pulse(to_double(a[0], e)));
    }},
    {"slot_cost_bg", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::slot_cost_bg(to_int(a[0], e), to_int(a[1], e)));
    }},
    {"slot_cost_text", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::slot_cost_text());
    }},
    {"portrait_scan_step", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::portrait_scan_step());
    }},
    {"portrait_alpha_min", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::portrait_alpha_min());
    }},
    {"portrait_crop_box", 6, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::portrait_crop_box(to_int(a[0], e), to_int(a[1], e), to_int(a[2], e), to_int(a[3], e), to_int(a[4], e), to_int(a[5], e)));
    }},
    {"portrait_scale_size", 4, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::portrait_scale_size(to_int(a[0], e), to_int(a[1], e), to_int(a[2], e), to_int(a[3], e)));
    }},
    {"portrait_gray_weight", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::portrait_gray_weight());
    }},
    {"hero_panel_rect", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::hero_panel_rect(to_int(a[0], e)));
    }},
    {"hero_panel_layout", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::hero_panel_layout(to_int(a[0], e), to_int(a[1], e)));
    }},
    {"skill_key_font_size", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::skill_key_font_size(to_int(a[0], e)));
    }},
    {"skill_badge_rect", 4, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::skill_badge_rect(to_int(a[0], e), to_int(a[1], e), to_int(a[2], e), to_int(a[3], e)));
    }},
    {"cooldown_seconds", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::cooldown_seconds(to_int(a[0], e)));
    }},
    {"cooldown_overlay_h", 3, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::cooldown_overlay_h(to_int(a[0], e), to_double(a[1], e), to_double(a[2], e)));
    }},
    {"item_forge_label", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::item_forge_label(to_int(a[0], e), to_int(a[1], e)));
    }},
    {"hero_upgrade_label", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::hero_upgrade_label(to_int(a[0], e)));
    }},
    {"max_level_label", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::max_level_label());
    }},
    {"autocast_label", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::autocast_label(to_bool(a[0], e)));
    }},
    {"shop_panel_rect", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::shop_panel_rect(to_int(a[0], e), to_int(a[1], e)));
    }},
    {"shop_tabs", 4, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::shop_tabs(to_int(a[0], e), to_int(a[1], e), to_int(a[2], e), to_int(a[3], e)));
    }},
    {"shop_content", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::shop_content(to_int(a[0], e), to_int(a[1], e)));
    }},
    {"shop_hero_list", 3, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::shop_hero_list(to_array(a[0], e), to_dict(a[1], e), to_string(a[2], e)));
    }},
    {"shop_grid", 6, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::shop_grid(to_int(a[0], e), to_int(a[1], e), to_int(a[2], e), to_int(a[3], e), to_int(a[4], e), to_int(a[5], e)));
    }},
    {"shop_card_rects", 4, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::shop_card_rects(to_int(a[0], e), to_int(a[1], e), to_int(a[2], e), to_int(a[3], e)));
    }},
    {"shop_card_state", 5, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::shop_card_state(to_bool(a[0], e), to_int(a[1], e), to_int(a[2], e), to_int(a[3], e), to_int(a[4], e)));
    }},
    {"shop_scroll_thumb", 5, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::shop_scroll_thumb(to_int(a[0], e), to_int(a[1], e), to_int(a[2], e), to_int(a[3], e), to_int(a[4], e)));
    }},
    {"shop_scroll_buttons", 4, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::shop_scroll_buttons(to_int(a[0], e), to_int(a[1], e), to_int(a[2], e), to_int(a[3], e)));
    }},
    {"shop_gold_text", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::shop_gold_text(to_int(a[0], e)));
    }},
    {"shop_owned_text", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::shop_owned_text(to_int(a[0], e), to_int(a[1], e)));
    }},
    {"shop_empty_state", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::shop_empty_state(to_string(a[0], e)));
    }},
    {"hover_target", 5, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::hover_target(to_double(a[0], e), to_double(a[1], e), to_array(a[2], e), to_array(a[3], e), to_bool(a[4], e)));
    }},
    {"tower_tooltip_lines", 5, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::tower_tooltip_lines(to_string(a[0], e), to_int(a[1], e), to_int(a[2], e), to_int(a[3], e), to_int(a[4], e)));
    }},
    {"tooltip_rects", 4, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::tooltip_rects(to_double(a[0], e), to_double(a[1], e), to_int(a[2], e), to_int(a[3], e)));
    }},
    {"slot_hover_rects", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::slot_hover_rects(to_int(a[0], e), to_int(a[1], e)));
    }},
    {"slot_hint_text", 0, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::slot_hint_text());
    }},
    {"hover_pulses", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::hover_pulses(to_double(a[0], e)));
    }},
    {"notification_entry", 2, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::notification_entry(to_string(a[0], e), to_color(a[1], e)));
    }},
    {"notification_push", 3, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::notification_push(to_array(a[0], e), to_string(a[1], e), to_color(a[2], e)));
    }},
    {"newly_unlocked_level", 3, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::newly_unlocked_level(to_int(a[0], e), to_array(a[1], e), to_int(a[2], e)));
    }},
    {"unlock_popup", 4, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::unlock_popup(to_int(a[0], e), to_int(a[1], e), to_int(a[2], e), to_int(a[3], e)));
    }},
    {"overlay_stats_panel", 3, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::overlay_stats_panel(to_int(a[0], e), to_int(a[1], e), to_int(a[2], e)));
    }},
    {"overlay_stats_rows", 7, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::overlay_stats_rows(to_int(a[0], e), to_string(a[1], e), to_int(a[2], e), to_int(a[3], e), to_int(a[4], e), to_bool(a[5], e), to_bool(a[6], e)));
    }},
    {"action_hint_tokens", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::action_hint_tokens(to_string(a[0], e)));
    }},
    {"achievements_text", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::achievements_text(to_int(a[0], e)));
    }},
    {"achievements_layout", 3, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::achievements_layout(to_int(a[0], e), to_int(a[1], e), to_int(a[2], e)));
    }},
    {"tower_specials", 7, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::tower_specials(to_int(a[0], e), to_double(a[1], e), to_int(a[2], e), to_bool(a[3], e), to_int(a[4], e), to_double(a[5], e), to_double(a[6], e)));
    }},
    {"tower_title", 5, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::tower_title(to_string(a[0], e), to_int(a[1], e), to_int(a[2], e), to_int(a[3], e), to_string(a[4], e)));
    }},
    {"nexus_stat_lines", 4, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::nexus_stat_lines(to_string(a[0], e), to_int(a[1], e), to_int(a[2], e), to_int(a[3], e)));
    }},
    {"castle_name", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::castle_name(to_int(a[0], e)));
    }},
    {"castle_shield_section", 5, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::castle_shield_section(to_bool(a[0], e), to_bool(a[1], e), to_bool(a[2], e), to_int(a[3], e), to_int(a[4], e)));
    }},
    {"regen_shield_section", 4, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::regen_shield_section(to_bool(a[0], e), to_bool(a[1], e), to_int(a[2], e), to_int(a[3], e)));
    }},
    {"tower_path_buttons", 3, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::tower_path_buttons(to_int(a[0], e), to_int(a[1], e), to_int(a[2], e)));
    }},
    {"path_button_name", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::path_button_name(to_string(a[0], e)));
    }},
    {"path_cost_text", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::path_cost_text(to_int(a[0], e)));
    }},
    {"tower_upgrade_buttons", 3, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::tower_upgrade_buttons(to_int(a[0], e), to_int(a[1], e), to_int(a[2], e)));
    }},
    {"tower_max_layout", 4, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::tower_max_layout(to_int(a[0], e), to_int(a[1], e), to_int(a[2], e), to_int(a[3], e)));
    }},
    {"upgrade_preview_text", 3, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::upgrade_preview_text(to_int(a[0], e), to_int(a[1], e), to_int(a[2], e)));
    }},
    {"shop_hint_pos", 5, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::shop_hint_pos(to_double(a[0], e), to_double(a[1], e), to_int(a[2], e), to_int(a[3], e), to_int(a[4], e)));
    }},
    {"shop_hint_bg", 4, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::shop_hint_bg(to_int(a[0], e), to_int(a[1], e), to_int(a[2], e), to_int(a[3], e)));
    }},
    {"shop_hint_pulse", 1, [](const std::vector<Variant> &a, std::string &e) -> Variant {
        (void)a; (void)e;
        return Variant(MysticUI::shop_hint_pulse(to_double(a[0], e)));
    }},
