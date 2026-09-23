#ifndef MYSTIC_UI_PROCESSOR_H
#define MYSTIC_UI_PROCESSOR_H

// ═══ GENERATED — JANGAN SUNTING TANGAN ═══
// Sumber    : ui_components/_bundle.py (11 submodul komponen UI)
// Generator : tools/gen_ui_cpp.py (AST Python -> C++, bukan terjemahan tangan)
// Regenerasi: python3 tools/gen_ui_cpp.py
// Cek CI    : python3 tools/gen_ui_cpp.py --check
// Desain    : docs/AUDIT_ULANG_DARI_AWAL.md
//
// Port ui_components/_bundle.py ke Godot C++ GDExtension: lapisan LAYOUT +
// STATE + LABEL (geometri panel/kartu/tombol, state machine tombol, label,
// predikat hover). Renderer piksel (pygame.draw / Control Godot) tidak diport
// dan memanggil angka dari sini.

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

class MysticUI : public RefCounted {
    GDCLASS(MysticUI, RefCounted);

public:
    static Array module_names();
    static String module_names_string();
    static String api_signature();
    static Dictionary tower_type_colors();
    static Array tower_cards();
    static int64_t build_cost();
    static int64_t notification_duration();
    static Rect2 close_button_rect(int64_t x, int64_t y, int64_t size);
    static Color hp_bar_color(double ratio);
    static int64_t hp_bar_fill(int64_t w, double ratio);
    static Rect2 shadow_rect(const Rect2 & rect, const Vector2 & offset);
    static int64_t popup_width(int64_t design_w, int64_t panel_w);
    static Dictionary build_popup_rect(int64_t slot_x, int64_t slot_y, int64_t screen_w, int64_t screen_h);
    static Dictionary target_popup_rect(int64_t target_x, int64_t target_y, int64_t screen_w, int64_t screen_h, int64_t top_bar_h);
    static Array build_popup_buttons(int64_t px, int64_t py, int64_t popup_w);
    static String build_gold_text(int64_t gold);
    static Dictionary build_button_style(bool can_afford, bool hover, const Color & color);
    static bool hover_hit(const Rect2 & rect, const Vector2 & mouse, bool enabled);
    static Vector2 slot_blit_offset();
    static Rect2 slot_surface_rect(int64_t sx, int64_t sy);
    static int64_t slot_pulse(double animation_time);
    static Rect2 slot_cost_bg(int64_t sx, int64_t sy);
    static String slot_cost_text();
    static int64_t portrait_scan_step();
    static int64_t portrait_alpha_min();
    static Dictionary portrait_crop_box(int64_t min_x, int64_t min_y, int64_t max_x, int64_t max_y, int64_t canvas_w, int64_t canvas_h);
    static Dictionary portrait_scale_size(int64_t crop_w, int64_t crop_h, int64_t target_w, int64_t target_h);
    static Dictionary portrait_gray_weight();
    static Rect2 hero_panel_rect(int64_t screen_h);
    static Dictionary hero_panel_layout(int64_t px, int64_t py);
    static int64_t skill_key_font_size(int64_t label_len);
    static Rect2 skill_badge_rect(int64_t x, int64_t y, int64_t size, int64_t key_w);
    static int64_t cooldown_seconds(int64_t frames);
    static int64_t cooldown_overlay_h(int64_t size, double cooldown, double cooldown_max);
    static String item_forge_label(int64_t used, int64_t max_slots);
    static String hero_upgrade_label(int64_t cost);
    static String max_level_label();
    static String autocast_label(bool is_auto);
    static Rect2 shop_panel_rect(int64_t screen_w, int64_t screen_h);
    static Array shop_tabs(int64_t panel_x, int64_t panel_w, int64_t panel_y, int64_t header_h);
    static Dictionary shop_content(int64_t panel_y, int64_t header_h);
    static Array shop_hero_list(const Array & purchased, const Dictionary & is_boss, const String & tab);
    static Dictionary shop_grid(int64_t panel_x, int64_t panel_w, int64_t content_top, int64_t content_bottom, int64_t count, int64_t scroll);
    static Dictionary shop_card_rects(int64_t cx, int64_t cy, int64_t cw, int64_t ch);
    static Dictionary shop_card_state(bool owned, int64_t hero_count, int64_t max_owned, int64_t gold, int64_t cost);
    static Rect2 shop_scroll_thumb(int64_t x, int64_t y, int64_t height, int64_t scroll, int64_t max_scroll);
    static Array shop_scroll_buttons(int64_t panel_x, int64_t panel_w, int64_t content_top, int64_t content_bottom);
    static String shop_gold_text(int64_t gold);
    static String shop_owned_text(int64_t owned, int64_t max_owned);
    static Dictionary shop_empty_state(const String & tab);
    static Dictionary hover_target(double mx, double my, const Array & towers, const Array & slots, bool blocked);
    static Array tower_tooltip_lines(const String & name, int64_t level, int64_t damage, int64_t range, int64_t kills);
    static Dictionary tooltip_rects(double tower_x, double tower_y, int64_t bg_w, int64_t bg_h);
    static Dictionary slot_hover_rects(int64_t sx, int64_t sy);
    static String slot_hint_text();
    static Dictionary hover_pulses(double animation_time);
    static Dictionary notification_entry(const String & text, const Color & color);
    static Array notification_push(const Array & messages, const String & text, const Color & color);
    static int64_t newly_unlocked_level(int64_t current, const Array & completed, int64_t next_level);
    static Dictionary unlock_popup(int64_t timer, int64_t delay, int64_t cx, int64_t cy);
    static Dictionary overlay_stats_panel(int64_t cx, int64_t cy, int64_t rows);
    static Array overlay_stats_rows(int64_t score, const String & time_str, int64_t waves, int64_t kills, int64_t combo, bool best_score, bool best_time);
    static Dictionary action_hint_tokens(const String & action);
    static String achievements_text(int64_t count);
    static Dictionary achievements_layout(int64_t cx, int64_t cy, int64_t text_w);
    static Array tower_specials(int64_t splash, double slow, int64_t chain, bool double_shot, int64_t burn_dps, double atk_slow, double skill_down);
    static String tower_title(const String & name, int64_t level, int64_t title_w, int64_t popup_w, const String & tower_type);
    static Array nexus_stat_lines(const String & minion_scale, int64_t ai_level, int64_t damage, int64_t range);
    static String castle_name(int64_t nexus_level);
    static Dictionary castle_shield_section(bool free_shield, bool purchased, bool can_buy, int64_t cost, int64_t gold);
    static Dictionary regen_shield_section(bool active, bool can_buy, int64_t cost, int64_t gold);
    static Array tower_path_buttons(int64_t px, int64_t y, int64_t popup_w);
    static String path_button_name(const String & tower_info_name);
    static String path_cost_text(int64_t cost);
    static Dictionary tower_upgrade_buttons(int64_t px, int64_t y, int64_t popup_w);
    static Dictionary tower_max_layout(int64_t px, int64_t y, int64_t popup_w, int64_t sell_value);
    static String upgrade_preview_text(int64_t next_level, int64_t damage, int64_t hp);
    static Vector2 shop_hint_pos(double sx, double sy, int64_t ax, int64_t ay, int64_t pulse);
    static Rect2 shop_hint_bg(int64_t center_x, int64_t center_y, int64_t text_w, int64_t text_h);
    static int64_t shop_hint_pulse(double animation_time);

    // ── helper internal (dipakai fungsi ter-bind; TIDAK di-bind) ──
    static int64_t py_round(double value);
    static String thousands(int64_t value);

protected:
    static void _bind_methods();
};

} // namespace godot

#endif // MYSTIC_UI_PROCESSOR_H
