#include "ui_processor.h"

#include <godot_cpp/core/class_db.hpp>

#include <cmath>

// ═══ GENERATED — JANGAN SUNTING TANGAN ═══
// Sumber    : ui_components/_bundle.py
// Generator : tools/gen_ui_cpp.py
// Regenerasi: python3 tools/gen_ui_cpp.py
// Cek CI    : python3 tools/gen_ui_cpp.py --check
//
// Setiap fungsi menyebut baris sumber Python yang direplikasi. Angka yang
// diekstrak generator datang dari AST (bukan salinan tangan); perilakunya
// dikunci oracle pygame + self-test tanpa engine.

namespace godot {

// Replika round() CPython: half-to-even (round(2.5) == 2, round(-2.5) == -2).
int64_t MysticUI::py_round(double value) {
    double floored = std::floor(value);
    double diff = value - floored;
    if (diff > 0.5) {
        return (int64_t)(floored + 1.0);
    }
    if (diff < 0.5) {
        return (int64_t)floored;
    }
    int64_t parity = (int64_t)floored;
    return (parity % 2 == 0) ? parity : parity + 1;
}

// Replika f"{value:,}" Python (pemisah ribuan).
String MysticUI::thousands(int64_t value) {
    bool neg = value < 0;
    int64_t mag = neg ? -(value + 1) + 1 : value;
    String digits = String::num_int64(mag);
    String out;
    while (digits.length() > 3) {
        out = String(",") + digits.substr(digits.length() - 3, 3) + out;
        digits = digits.substr(0, digits.length() - 3);
    }
    return (neg ? String("-") : String()) + digits + out;
}

// Daftar submodul ui_components (urutan bundle) — oracle memakai daftar ini untuk audit closed-world.
Array MysticUI::module_names() {

    Array out;
    out.push_back(String("base_ui"));
    out.push_back(String("hero_portraits"));
    out.push_back(String("build_popup"));
    out.push_back(String("build_slots"));
    out.push_back(String("hero_panel"));
    out.push_back(String("hero_shop"));
    out.push_back(String("hover_indicators"));
    out.push_back(String("notification"));
    out.push_back(String("overlay"));
    out.push_back(String("popup_renderer"));
    out.push_back(String("shop_hints"));
    return out;
}

// Gabungan module_names() dengan koma (untuk cap jari + log).
String MysticUI::module_names_string() {

    String out;
    Array names = module_names();
    for (int64_t i = 0; i < names.size(); i++) {
        if (i > 0) {
            out += String(",");
        }
        out += (String)names[i];
    }
    return out;
}

// Cap jari API: jumlah modul + fungsi (dipakai loader membuktikan backend C++ benar-benar jalan, dicetak sekali per perubahan backend).
String MysticUI::api_signature() {

    return String("ui_v1:11mod:80fn:");
}

// TOWER_TYPE_COLORS (settings/_core.py, via AST) — warna main/dark 4 tipe menara.
Dictionary MysticUI::tower_type_colors() {
    Dictionary out;
    Dictionary archer;
    archer["main"] = Color(100.0f / 255.0f, 220.0f / 255.0f, 120.0f / 255.0f);
    archer["dark"] = Color(50.0f / 255.0f, 140.0f / 255.0f, 70.0f / 255.0f);
    out["archer"] = archer;
    Dictionary cannon;
    cannon["main"] = Color(200.0f / 255.0f, 100.0f / 255.0f, 60.0f / 255.0f);
    cannon["dark"] = Color(140.0f / 255.0f, 60.0f / 255.0f, 30.0f / 255.0f);
    out["cannon"] = cannon;
    Dictionary ice;
    ice["main"] = Color(120.0f / 255.0f, 200.0f / 255.0f, 255.0f / 255.0f);
    ice["dark"] = Color(60.0f / 255.0f, 130.0f / 255.0f, 200.0f / 255.0f);
    out["ice"] = ice;
    Dictionary mage;
    mage["main"] = Color(180.0f / 255.0f, 80.0f / 255.0f, 220.0f / 255.0f);
    mage["dark"] = Color(110.0f / 255.0f, 40.0f / 255.0f, 150.0f / 255.0f);
    out["mage"] = mage;
    return out;
}

// Kartu 4 tipe menara di BuildPopup (BuildPopup._draw_tower_buttons baris 777) — urutan = urutan grid 2x2.
Array MysticUI::tower_cards() {
    Array out;
    Dictionary c0;
    c0["type"] = String("archer");
    c0["name"] = String("Archer");
    c0["desc"] = String("Fast single");
    c0["color"] = Color(100.0f / 255.0f, 220.0f / 255.0f, 120.0f / 255.0f);
    out.push_back(c0);
    Dictionary c1;
    c1["type"] = String("cannon");
    c1["name"] = String("Cannon");
    c1["desc"] = String("AOE + Burn");
    c1["color"] = Color(200.0f / 255.0f, 100.0f / 255.0f, 60.0f / 255.0f);
    out.push_back(c1);
    Dictionary c2;
    c2["type"] = String("ice");
    c2["name"] = String("Ice");
    c2["desc"] = String("Slow move+atk");
    c2["color"] = Color(120.0f / 255.0f, 200.0f / 255.0f, 255.0f / 255.0f);
    out.push_back(c2);
    Dictionary c3;
    c3["type"] = String("mage");
    c3["name"] = String("Mage");
    c3["desc"] = String("Chain + Debuff");
    c3["color"] = Color(180.0f / 255.0f, 80.0f / 255.0f, 220.0f / 255.0f);
    out.push_back(c3);
    return out;
}

// Biaya bangun menara (BuildPopup._draw_tower_buttons).
int64_t MysticUI::build_cost() {
    return 100;
}

// Durasi satu notifikasi dalam frame (Notification.add_notification: 'timer': 180 — 3 detik @60fps).
int64_t MysticUI::notification_duration() {
    return 180;
}

// Rect tombol X (BaseUIComponent._draw_close_button baris 123; default size=44).
Rect2 MysticUI::close_button_rect(int64_t x, int64_t y, int64_t size) {

    return Rect2((double)x, (double)y, (double)size, (double)size);
}

// Warna isi HP bar (BaseUIComponent._draw_hp_bar: >0.5 hijau, >0.25 kuning, selain itu merah; batas 0.5 / 0.25).
Color MysticUI::hp_bar_color(double ratio) {

    if (ratio > 0.5) {
        return Color(50.0f / 255.0f, 200.0f / 255.0f, 50.0f / 255.0f);
    }
    if (ratio > 0.25) {
        return Color(255.0f / 255.0f, 220.0f / 255.0f, 0.0f / 255.0f);
    }
    return Color(220.0f / 255.0f, 50.0f / 255.0f, 50.0f / 255.0f);
}

// Lebar isi HP bar: int(w * ratio) — trunc, bukan pembulatan.
int64_t MysticUI::hp_bar_fill(int64_t w, double ratio) {

    return (int64_t)((double)w * ratio);
}

// Rect surface bayangan (_draw_shadow_rect: surface = rect + 2*offset, blit di rect - offset).
Rect2 MysticUI::shadow_rect(const Rect2 & rect, const Vector2 & offset) {

    return Rect2(rect.position.x - offset.x, rect.position.y - offset.y,
            rect.size.x + offset.x * 2.0, rect.size.y + offset.y * 2.0);
}

// Lebar popup setelah pemadatan panel kanan (BuildPopup.draw / PopupRenderer.draw: w = min(w, max(1, panel_w - 16))); panel_w<=0 = tidak ada panel.
int64_t MysticUI::popup_width(int64_t design_w, int64_t panel_w) {

    if (panel_w <= 0) {
        return design_w;
    }
    int64_t limit = panel_w - 16;
    if (limit < 1) {
        limit = 1;
    }
    return design_w < limit ? design_w : limit;
}

// Posisi popup build di atas peta (BuildPopup.draw baris 689: px = slot_x - w//2, py = slot_y - h - 30, seluruh clamp layar). Balasan: x/y/w/h + konektor ke slot.
Dictionary MysticUI::build_popup_rect(int64_t slot_x, int64_t slot_y, int64_t screen_w, int64_t screen_h) {

    int64_t w = 400;
    int64_t h = 300;
    int64_t px = slot_x - w / 2;
    int64_t py = slot_y - h - 30;
    if (px < 10) {
        px = 10;
    }
    if (px + w > screen_w - 10) {
        px = screen_w - w - 10;
    }
    if (py < 10) {
        py = slot_y + 30;
    }
    if (py + h > screen_h - 10) {
        py = screen_h - h - 10;
    }
    if (py < 10) {
        py = 10;
    }
    Dictionary out;
    out["x"] = (int64_t)px;
    out["y"] = (int64_t)py;
    out["w"] = (int64_t)w;
    out["h"] = (int64_t)h;
    Array line;
    line.push_back(Vector2((double)(px + w / 2), (double)(py + h)));
    line.push_back(Vector2((double)slot_x, (double)(slot_y - 10)));
    out["connector"] = line;
    return out;
}

// Posisi popup menara/nexus di atas peta (PopupRenderer.draw baris 3568: 380x440; py < TOP_BAR_HEIGHT+10 digeser ke BAWAH target lalu di-clamp lagi).
Dictionary MysticUI::target_popup_rect(int64_t target_x, int64_t target_y, int64_t screen_w, int64_t screen_h, int64_t top_bar_h) {

    int64_t w = 380;
    int64_t h = 440;
    int64_t px = target_x - w / 2;
    int64_t py = target_y - h - 40;
    if (px < 10) {
        px = 10;
    }
    if (px + w > screen_w - 10) {
        px = screen_w - w - 10;
    }
    if (py < top_bar_h + 10) {
        py = target_y + 40;
    }
    if (py + h > screen_h - 10) {
        py = screen_h - h - 10;
    }
    if (py < top_bar_h + 10) {
        py = top_bar_h + 10;
    }
    Dictionary out;
    out["x"] = (int64_t)px;
    out["y"] = (int64_t)py;
    out["w"] = (int64_t)w;
    out["h"] = (int64_t)h;
    Array line;
    line.push_back(Vector2((double)(px + w / 2), (double)(py + h)));
    line.push_back(Vector2((double)target_x, (double)(target_y - 10)));
    out["connector"] = line;
    return out;
}

// Grid 2x2 kartu menara (BuildPopup._draw_tower_buttons baris 793: btn_w=(popup_w-50)//2, h=78, start_y=py+62, gap 12/10).
Array MysticUI::build_popup_buttons(int64_t px, int64_t py, int64_t popup_w) {

    Array out;
    int64_t btn_w = (popup_w - 50) / 2;
    int64_t btn_h = 78;
    int64_t start_y = py + 62;
    for (int64_t i = 0; i < 4; i++) {
        int64_t col = i % 2;
        int64_t row = i / 2;
        int64_t bx = px + 15 + col * (btn_w + 12);
        int64_t by = start_y + row * (btn_h + 10);
        out.push_back(Rect2((double)bx, (double)by, (double)btn_w,
                (double)btn_h));
    }
    return out;
}

// Teks gold popup build (f"Gold: {gold:,}  (Cost: 100)").
String MysticUI::build_gold_text(int64_t gold) {

    return String("Gold: ") + thousands(gold) + String("  (Cost: 100)");
}

// Warna kartu menara (BuildPopup._draw_tower_buttons): fill gradasi dark/lighter dari warna tipe + border + warna teks nama/desc/biaya.
Dictionary MysticUI::build_button_style(bool can_afford, bool hover, const Color & color) {

    // godot-cpp 4.3 mengekspos Color::get_r8() (dibaca binder dari properti
    // `r8` GDScript) — BUKAN color.r8(). Semantiknya CLAMP(Math::round(r*255))
    // sehingga sama dengan r8() stub self-test.
    int64_t cr = color.get_r8();
    int64_t cg = color.get_g8();
    int64_t cb = color.get_b8();
    int64_t dr = (int64_t)((double)cr * 0.30) + 18;
    int64_t dg = (int64_t)((double)cg * 0.30) + 18;
    int64_t db = (int64_t)((double)cb * 0.30) + 18;
    int64_t lr = (int64_t)((double)cr * 0.45) + 40;
    if (lr > 255) { lr = 255; }
    int64_t lg = (int64_t)((double)cg * 0.45) + 40;
    if (lg > 255) { lg = 255; }
    int64_t lb = (int64_t)((double)cb * 0.45) + 40;
    if (lb > 255) { lb = 255; }
    int64_t br = (int64_t)((double)cr * 0.22) + 12;
    int64_t bg = (int64_t)((double)cg * 0.22) + 12;
    int64_t bb = (int64_t)((double)cb * 0.22) + 12;
    Dictionary out;
    out["fill_top"] = Color((double)(hover ? lr : dr) / 255.0,
            (double)(hover ? lg : dg) / 255.0,
            (double)(hover ? lb : db) / 255.0);
    out["fill_bottom"] = Color((double)br / 255.0, (double)bg / 255.0,
            (double)bb / 255.0);
    out["border"] = can_afford ? color
            : Color(70.0 / 255.0, 70.0 / 255.0, 80.0 / 255.0);
    out["name_color"] = can_afford ? Color(255.0f / 255.0f, 255.0f / 255.0f, 255.0f / 255.0f) : Color(150.0f / 255.0f, 150.0f / 255.0f, 150.0f / 255.0f);
    out["desc_color"] = can_afford ? Color(215.0f / 255.0f, 222.0f / 255.0f, 240.0f / 255.0f) : Color(150.0f / 255.0f, 150.0f / 255.0f, 150.0f / 255.0f);
    out["cost_color"] = can_afford ? Color(255.0f / 255.0f, 220.0f / 255.0f, 110.0f / 255.0f) : Color(150.0f / 255.0f, 150.0f / 255.0f, 150.0f / 255.0f);
    out["corner_ticks"] = can_afford;
    out["interactive"] = can_afford;
    return out;
}

// Hover pygame (rect.collidepoint) yang digerbangi flag enabled — dipakai semua kartu/pill interaktif.
bool MysticUI::hover_hit(const Rect2 & rect, const Vector2 & mouse, bool enabled) {

    if (!enabled) {
        return false;
    }
    return rect.has_point(mouse);
}

// Offset blit surface slot (BuildSlots.draw baris 870: (sx-20, sy-17)).
Vector2 MysticUI::slot_blit_offset() {
    return Vector2(-20, -17);
}

// Rect surface slot 40x38 di koordinat layar (origin lokal (20,17)).
Rect2 MysticUI::slot_surface_rect(int64_t sx, int64_t sy) {
    return Rect2((double)(sx -20), (double)(sy -17), 40.0, 38.0);
}

// Denyut slot: int(round(sin(t*0.08)*2)) — round Python half-to-even, dipakai sebagai kunci cache + radius glow/plus.
int64_t MysticUI::slot_pulse(double animation_time) {

    return py_round(std::sin(animation_time * 0.08) * 2.0);
}

// Rect label biaya '100G' di slot biru (BuildSlots._draw_blue_slot: Rect(sx-18, sy+18, 36, 14)).
Rect2 MysticUI::slot_cost_bg(int64_t sx, int64_t sy) {
    return Rect2((double)(sx -18), (double)(sy + 18), 36.0, 14.0);
}

// Label biaya slot menara (hard-coded di surface slot).
String MysticUI::slot_cost_text() {
    return String("100G");
}

// Langkah pemindaian bbox portrait (HeroPortraits._crop_and_scale: range(0, ch, 2)).
int64_t MysticUI::portrait_scan_step() {
    return 2;
}

// Ambang alpha bbox portrait (HeroPortraits._crop_and_scale: pixel[3] > 10).
int64_t MysticUI::portrait_alpha_min() {
    return 10;
}

// Kotak crop dari bbox hasil scan + padding (HeroPortraits._crop_and_scale: pad 4, clamp ke canvas, None kalau kosong).
Dictionary MysticUI::portrait_crop_box(int64_t min_x, int64_t min_y, int64_t max_x, int64_t max_y, int64_t canvas_w, int64_t canvas_h) {

    Dictionary out;
    if (max_x <= min_x || max_y <= min_y) {
        out["valid"] = false;
        return out;
    }
    int64_t pad = 4;
    if (min_x - pad > 0) { min_x -= pad; } else { min_x = 0; }
    if (min_y - pad > 0) { min_y -= pad; } else { min_y = 0; }
    if (max_x + pad < canvas_w) { max_x += pad; } else { max_x = canvas_w; }
    if (max_y + pad < canvas_h) { max_y += pad; } else { max_y = canvas_h; }
    int64_t crop_w = max_x - min_x;
    int64_t crop_h = max_y - min_y;
    if (crop_w <= 0 || crop_h <= 0) {
        out["valid"] = false;
        return out;
    }
    out["valid"] = true;
    out["x"] = (int64_t)min_x;
    out["y"] = (int64_t)min_y;
    out["w"] = (int64_t)crop_w;
    out["h"] = (int64_t)crop_h;
    return out;
}

// Ukuran hasil smoothscale portrait (HeroPortraits._crop_and_scale: scale = min(tw/cw, th/ch, 1.0), new = max(1, int(crop*scale))).
Dictionary MysticUI::portrait_scale_size(int64_t crop_w, int64_t crop_h, int64_t target_w, int64_t target_h) {

    double scale_x = (double)target_w / (double)crop_w;
    double scale_y = (double)target_h / (double)crop_h;
    double scale = scale_x < scale_y ? scale_x : scale_y;
    if (scale > 1.0) {
        scale = 1.0;
    }
    int64_t new_w = (int64_t)((double)crop_w * scale);
    int64_t new_h = (int64_t)((double)crop_h * scale);
    if (new_w < 1) { new_w = 1; }
    if (new_h < 1) { new_h = 1; }
    Dictionary out;
    out["w"] = (int64_t)new_w;
    out["h"] = (int64_t)new_h;
    out["scale"] = (double)scale;
    return out;
}

// Bobot grayscale portrait (HeroPortraits._apply_grayscale: 0.299/0.587/0.114) — pemanggil mengalikan kanal dan trunc ke uint8.
Dictionary MysticUI::portrait_gray_weight() {

    Dictionary out;
    out["r"] = (double)0.299;
    out["g"] = (double)0.587;
    out["b"] = (double)0.114;
    return out;
}

// Panel hero bottom-left 280x276 (HeroPanel.draw baris 1089: (20, H-296), atau posisi panel kanan dari platform).
Rect2 MysticUI::hero_panel_rect(int64_t screen_h) {
    return Rect2((double)20, (double)(screen_h - 296), 280.0, 276.0);
}

// Semua rect HeroPanel relatif ke (px, py) — baris 1089: HP bar, 4 skill slot (38px gap 10), toggle auto-cast, item forge, upgrade (masing-masing 22px, jarak 30/38/28).
Dictionary MysticUI::hero_panel_layout(int64_t px, int64_t py) {

    Dictionary out;
    out["panel"] = Rect2((double)px, (double)py, 280.0, 276.0);
    out["close"] = close_button_rect(px + 26, py + 6, 22);
    out["title_y"] = (int64_t)(py + 10);
    out["level_y"] = (int64_t)(py + 18);
    out["hp_bar"] = Rect2((double)(px + 12), (double)(py + 34), 256.0, 8.0);
    out["hp_text_y"] = (int64_t)(py + 46);
    Array skills;
    int64_t start_x = px + 14;
    int64_t y = py + 66;
    for (int64_t i = 0; i < 4; i++) {
        skills.push_back(Rect2((double)(start_x + i * (38 + 10)),
                (double)y, 38.0, 38.0));
    }
    out["skills"] = skills;
    out["autocast"] = Rect2((double)(px + 10), (double)(py + 118),
            260.0, 22.0);
    out["item_slots_y"] = (int64_t)(py + 148);
    out["item_forge"] = Rect2((double)(px + 10), (double)(py + 186),
            260.0, 22.0);
    out["upgrade"] = Rect2((double)(px + 10), (double)(py + 214), 260.0,
            22.0);
    return out;
}

// Ukuran font badge tombol skill (HeroPanel._draw_skill_slot: <=2 huruf 14, <=4 huruf 12, selain itu 10).
int64_t MysticUI::skill_key_font_size(int64_t label_len) {

    if (label_len <= 2) {
        return 14;
    }
    if (label_len <= 4) {
        return 12;
    }
    return 10;
}

// Badge huruf tombol skill di pojok kanan-bawah slot (kw = lebar teks + 6; Rect(x+size-kw-2, y+size-13, kw, 11)).
Rect2 MysticUI::skill_badge_rect(int64_t x, int64_t y, int64_t size, int64_t key_w) {

    return Rect2((double)(x + size - key_w - 2), (double)(y + size - 13),
            (double)key_w, 11.0);
}

// Label detik cooldown pygame: cooldown // 60 + 1 (frame <= 0 = siap / tanpa label).
int64_t MysticUI::cooldown_seconds(int64_t frames) {

    if (frames <= 0) {
        return 0;
    }
    return frames / 60 + 1;
}

// Tinggi overlay gelap cooldown: int(size * cooldown / cooldown_max) (HeroPanel._draw_skill_slot). Argumen double → pembagian float Python. cooldown_max 0 dijaga eksplisit: Python melempar ZeroDivisionError, C++ mengembalikan 0 (tanpa guard, int() dari NaN/Inf tidak terdefinisi).
int64_t MysticUI::cooldown_overlay_h(int64_t size, double cooldown, double cooldown_max) {

    if (cooldown_max <= 0.0) {
        return 0;
    }
    return (int64_t)((double)size * (cooldown / cooldown_max));
}

// Label tombol ITEM FORGE (DUA spasi sebelum kurung — persis pygame).
String MysticUI::item_forge_label(int64_t used, int64_t max_slots) {

    return String("ITEM FORGE  (") + String::num_int64(used) + String("/")
            + String::num_int64(max_slots) + String(")");
}

// Label tombol upgrade hero: UPGRADE HERO ({cost}G).
String MysticUI::hero_upgrade_label(int64_t cost) {

    return String("UPGRADE HERO (") + String::num_int64(cost) + String("G)");
}

// Label MAX LEVEL — ui_theme.letter() menyisipkan spasi antar huruf, jadi teksnya 17 karakter (dipakai pemanggil untuk mengukur lebar).
String MysticUI::max_level_label() {
    return String("M A X   L E V E L");
}

// Label toggle auto-cast.
String MysticUI::autocast_label(bool is_auto) {

    return is_auto ? String("AUTO-CAST ON") : String("AUTO-CAST OFF");
}

// Panel HERO SHOP 1100x700 terpusat (HeroShop._render_shop baris 1570; panel_y minimal 16 supaya tombol X tidak keluar frame).
Rect2 MysticUI::shop_panel_rect(int64_t screen_w, int64_t screen_h) {

    int64_t panel_x = (screen_w - 1100) / 2;
    int64_t panel_y = (screen_h - 700) / 2;
    if (panel_y < 16) {
        panel_y = 16;
    }
    return Rect2((double)panel_x, (double)panel_y, 1100.0, 700.0);
}

// Tab toko hero (HeroShop._draw_hero_cards baris 1813: tab_w 150, tab_h 30, total lebar = n*tab_w + 10, terpusat pada panel).
Array MysticUI::shop_tabs(int64_t panel_x, int64_t panel_w, int64_t panel_y, int64_t header_h) {

    Array out;
    int64_t tab_w = 150;
    int64_t tab_h = 30;
    int64_t tab_y = panel_y + header_h + 10;
    int64_t total_tab_w = tab_w * 2 + 10;
    int64_t tab_start_x = panel_x + (panel_w - total_tab_w) / 2;
    Dictionary t0;
    t0["id"] = String("starter");
    t0["label"] = String("STARTER");
    t0["color"] = Color(100.0f / 255.0f, 200.0f / 255.0f, 255.0f / 255.0f);
    t0["rect"] = Rect2((double)(tab_start_x + 0 * (tab_w + 10)),
            (double)tab_y, (double)tab_w, (double)tab_h);
    out.push_back(t0);
    Dictionary t1;
    t1["id"] = String("boss");
    t1["label"] = String("BOSS HEROES");
    t1["color"] = Color(255.0f / 255.0f, 150.0f / 255.0f, 100.0f / 255.0f);
    t1["rect"] = Rect2((double)(tab_start_x + 1 * (tab_w + 10)),
            (double)tab_y, (double)tab_w, (double)tab_h);
    out.push_back(t1);
    return out;
}

// Area konten kartu (HeroShop._draw_hero_cards: tab_y = panel_y + header_h + 10, content_top = tab_y + tab_h + 10, content_bottom = panel_y + 700 - 20).
Dictionary MysticUI::shop_content(int64_t panel_y, int64_t header_h) {

    int64_t tab_y = panel_y + header_h + 10;
    int64_t content_top = tab_y + 30 + 10;
    int64_t content_bottom = panel_y + 700 - 20;
    Dictionary out;
    out["tab_y"] = (int64_t)tab_y;
    out["top"] = (int64_t)content_top;
    out["bottom"] = (int64_t)content_bottom;
    out["height"] = (int64_t)(content_bottom - content_top);
    return out;
}

// Filter daftar hero per tab (HeroShop._draw_hero_cards: tab starter = bukan boss, tab boss = boss; hero yang tidak ada di katalog dibuang, urutan = urutan array purchased).
Array MysticUI::shop_hero_list(const Array & purchased, const Dictionary & is_boss, const String & tab) {

    Array out;
    for (int64_t i = 0; i < purchased.size(); i++) {
        String ht = purchased[i];
        if (!is_boss.has(ht)) {
            continue;
        }
        bool boss = (bool)is_boss[ht];
        if (tab == String("starter") && !boss) {
            out.push_back(ht);
        } else if (tab == String("boss") && boss) {
            out.push_back(ht);
        }
    }
    return out;
}

// Tata letak grid kartu + scroll (HeroShop._draw_hero_cards baris 1901: kartu 340x120, 2 per baris, gap 20/12, scroll di-clamp 0..max, kartu di luar content ditandai tidak terlihat).
Dictionary MysticUI::shop_grid(int64_t panel_x, int64_t panel_w, int64_t content_top, int64_t content_bottom, int64_t count, int64_t scroll) {

    int64_t card_w = 340;
    int64_t card_h = 120;
    int64_t per_row = 2;
    int64_t gap_x = 20;
    int64_t gap_y = 12;
    int64_t content_height = content_bottom - content_top;
    int64_t total_width = card_w * per_row + gap_x;
    int64_t start_x = panel_x + (panel_w - total_width) / 2;
    int64_t total_rows = (count + per_row - 1) / per_row;
    int64_t total_content_h = total_rows * (card_h + gap_y);
    int64_t max_scroll = total_content_h - content_height;
    if (max_scroll < 0) {
        max_scroll = 0;
    }
    int64_t clamped = scroll;
    if (clamped < 0) {
        clamped = 0;
    }
    if (clamped > max_scroll) {
        clamped = max_scroll;
    }
    Array rects;
    Array visible;
    for (int64_t i = 0; i < count; i++) {
        int64_t col = i % per_row;
        int64_t row = i / per_row;
        int64_t cx = start_x + col * (card_w + gap_x);
        int64_t cy = content_top + row * (card_h + gap_y) - clamped;
        rects.push_back(Rect2((double)cx, (double)cy, (double)card_w,
                (double)card_h));
        bool shown = !(cy + card_h < content_top || cy > content_bottom);
        visible.push_back(shown);
    }
    Dictionary out;
    out["card_w"] = (int64_t)card_w;
    out["card_h"] = (int64_t)card_h;
    out["per_row"] = (int64_t)per_row;
    out["gap_x"] = (int64_t)gap_x;
    out["gap_y"] = (int64_t)gap_y;
    out["start_x"] = (int64_t)start_x;
    out["total_rows"] = (int64_t)total_rows;
    out["total_height"] = (int64_t)total_content_h;
    out["max_scroll"] = (int64_t)max_scroll;
    out["scroll"] = (int64_t)clamped;
    out["rects"] = rects;
    out["visible"] = visible;
    return out;
}

// Isi kartu hero compact (HeroShop._draw_compact_card baris 1958: portrait 60 di kiri, info mulai x+82, baris statistik y+68 jarak 56, tombol 90x30 di kanan).
Dictionary MysticUI::shop_card_rects(int64_t cx, int64_t cy, int64_t cw, int64_t ch) {

    int64_t portrait = 60;
    int64_t btn_w = 90;
    int64_t btn_h = 30;
    Dictionary out;
    out["card"] = Rect2((double)cx, (double)cy, (double)cw, (double)ch);
    out["portrait"] = Rect2((double)(cx + 10),
            (double)(cy + (ch - portrait) / 2), (double)portrait,
            (double)portrait);
    out["info_x"] = (int64_t)(cx + 10 + portrait + 12);
    out["info_y"] = (int64_t)(cy + 10);
    out["title_y"] = (int64_t)(cy + 34);
    out["role_y"] = (int64_t)(cy + 54);
    out["stats_y"] = (int64_t)(cy + 78);
    out["stat_gap"] = (int64_t)56;
    out["button"] = Rect2((double)(cx + cw - btn_w - 12),
            (double)(cy + (ch - btn_h) / 2), (double)btn_w, (double)btn_h);
    return out;
}

// State tombol kartu hero (HeroShop._draw_compact_card): owned -> ACTIVE, hero penuh -> MAX, gold kurang -> harga (abu), selain itu beli (dua nada hover). Balasan: state/label/warna/interactive.
Dictionary MysticUI::shop_card_state(bool owned, int64_t hero_count, int64_t max_owned, int64_t gold, int64_t cost) {

    Dictionary out;
    String label = String::num_int64(cost) + String("G");
    if (owned) {
        out["state"] = String("owned");
        out["label"] = String("ACTIVE");
        out["bg"] = Color(40.0f / 255.0f, 80.0f / 255.0f, 40.0f / 255.0f);
        out["border"] = Color(100.0f / 255.0f, 180.0f / 255.0f, 100.0f / 255.0f);
        out["text_color"] = Color(150.0f / 255.0f, 255.0f / 255.0f, 150.0f / 255.0f);
        out["interactive"] = false;
        return out;
    }
    if (hero_count >= max_owned) {
        out["state"] = String("max");
        out["label"] = String("MAX");
        out["bg"] = Color(60.0f / 255.0f, 40.0f / 255.0f, 40.0f / 255.0f);
        out["border"] = Color(180.0f / 255.0f, 80.0f / 255.0f, 80.0f / 255.0f);
        out["text_color"] = Color(255.0f / 255.0f, 150.0f / 255.0f, 150.0f / 255.0f);
        out["interactive"] = false;
        return out;
    }
    if (gold < cost) {
        out["state"] = String("cant_afford");
        out["label"] = label;
        out["bg"] = Color(50.0f / 255.0f, 50.0f / 255.0f, 50.0f / 255.0f);
        out["border"] = Color(130.0f / 255.0f, 130.0f / 255.0f, 130.0f / 255.0f);
        out["text_color"] = Color(200.0f / 255.0f, 150.0f / 255.0f, 150.0f / 255.0f);
        out["interactive"] = false;
        return out;
    }
    out["state"] = String("buy");
    out["label"] = label;
    out["bg"] = Color(35.0f / 255.0f, 140.0f / 255.0f, 45.0f / 255.0f);
    out["bg_hover"] = Color(40.0f / 255.0f, 170.0f / 255.0f, 50.0f / 255.0f);
    out["border"] = Color(100.0f / 255.0f, 220.0f / 255.0f, 100.0f / 255.0f);
    out["border_hover"] = Color(130.0f / 255.0f, 255.0f / 255.0f, 130.0f / 255.0f);
    out["text_color"] = Color(255.0f / 255.0f, 255.0f / 255.0f, 255.0f / 255.0f);
    out["interactive"] = true;
    return out;
}

// Thumb scroll (HeroShop._draw_scroll_indicator: ratio = h/(h+max), thumb_h = max(20, int(h*ratio)), thumb_y = y + int((h-thumb_h)*pos/max)). max_scroll <= 0 -> Rect kosong.
Rect2 MysticUI::shop_scroll_thumb(int64_t x, int64_t y, int64_t height, int64_t scroll, int64_t max_scroll) {

    if (max_scroll <= 0) {
        return Rect2();
    }
    double ratio = (double)height / (double)(height + max_scroll);
    int64_t thumb_h = (int64_t)((double)height * ratio);
    if (thumb_h < 20) {
        thumb_h = 20;
    }
    int64_t thumb_y = y + (int64_t)((double)(height - thumb_h)
            * ((double)scroll / (double)max_scroll));
    return Rect2((double)x, (double)thumb_y, 8.0, (double)thumb_h);
}

// Tombol scroll atas/bawah 20x20 (HeroShop._draw_hero_cards; hanya didaftarkan bila max_scroll > 0 — keputusan pemanggil).
Array MysticUI::shop_scroll_buttons(int64_t panel_x, int64_t panel_w, int64_t content_top, int64_t content_bottom) {

    Array out;
    out.push_back(Rect2((double)(panel_x + panel_w - 25),
            (double)content_top, 20.0, 20.0));
    out.push_back(Rect2((double)(panel_x + panel_w - 25),
            (double)(content_bottom - 20), 20.0, 20.0));
    return out;
}

// Teks badge gold header toko (f"GOLD: {gold:,}").
String MysticUI::shop_gold_text(int64_t gold) {
    return String("GOLD: ") + thousands(gold);
}

// Teks badge kepemilikan hero (f"{n}/{max} Heroes").
String MysticUI::shop_owned_text(int64_t owned, int64_t max_owned) {

    return String::num_int64(owned) + String("/")
            + String::num_int64(max_owned) + String(" Heroes");
}

// Pesan state kosong per tab (HeroShop._draw_hero_cards).
Dictionary MysticUI::shop_empty_state(const String & tab) {

    Dictionary out;
    if (tab == String("boss")) {
        out["msg"] = String("No boss heroes unlocked yet");
        out["hint"] = String("Defeat bosses to unlock their hero!");
    } else {
        out["msg"] = String("No starter heroes unlocked");
        out["hint"] = String("Visit Hero Shop from Main Menu!");
    }
    return out;
}

// Target hover (HoverIndicators.update baris 2556): popup/shop terbuka = tidak ada; menara radius 25, slot radius 20; yang pertama menang.
Dictionary MysticUI::hover_target(double mx, double my, const Array & towers, const Array & slots, bool blocked) {

    Dictionary out;
    out["kind"] = String("-");
    out["index"] = (int64_t)-1;
    if (blocked) {
        return out;
    }
    for (int64_t i = 0; i < towers.size(); i++) {
        Vector2 p = towers[i];
        if (std::sqrt((p.x - mx) * (p.x - mx) + (p.y - my) * (p.y - my))
                <= 25) {
            out["kind"] = String("tower");
            out["index"] = (int64_t)i;
            return out;
        }
    }
    for (int64_t i = 0; i < slots.size(); i++) {
        Vector2 p = slots[i];
        if (std::sqrt((p.x - mx) * (p.x - mx) + (p.y - my) * (p.y - my))
                <= 20) {
            out["kind"] = String("slot");
            out["index"] = (int64_t)i;
            return out;
        }
    }
    return out;
}

// Isi tooltip menara (HoverIndicators._draw_tower_tooltip: nama+Lv, DMG/RNG, Kills).
Array MysticUI::tower_tooltip_lines(const String & name, int64_t level, int64_t damage, int64_t range, int64_t kills) {

    Array out;
    out.push_back(name + String(" Lv.") + String::num_int64(level));
    out.push_back(String("DMG: ") + String::num_int64(damage)
            + String("  RNG: ") + String::num_int64(range));
    out.push_back(String("Kills: ") + String::num_int64(kills));
    return out;
}

// Kotak tooltip dari lebar/tinggi teks yang SUDAH diukur pemanggil (HoverIndicators._draw_tower_tooltip: tooltip y = int(y-60), bg = (x - w//2, y - h), shadow +4, panah bawah 5px).
Dictionary MysticUI::tooltip_rects(double tower_x, double tower_y, int64_t bg_w, int64_t bg_h) {

    int64_t tooltip_x = (int64_t)tower_x;
    int64_t tooltip_y = (int64_t)(tower_y - 60.0);
    int64_t bg_x = tooltip_x - bg_w / 2;
    int64_t bg_y = tooltip_y - bg_h;
    Dictionary out;
    out["x"] = (int64_t)bg_x;
    out["y"] = (int64_t)bg_y;
    out["bg"] = Rect2((double)bg_x, (double)bg_y, (double)bg_w, (double)bg_h);
    out["shadow"] = Rect2((double)(bg_x - 2), (double)(bg_y - 2),
            (double)(bg_w + 4), (double)(bg_h + 4));
    Array arrow;
    arrow.push_back(Vector2((double)(tooltip_x - 4), (double)(bg_y + bg_h)));
    arrow.push_back(Vector2((double)tooltip_x, (double)(bg_y + bg_h + 5)));
    arrow.push_back(Vector2((double)(tooltip_x + 4), (double)(bg_y + bg_h)));
    out["arrow"] = arrow;
    return out;
}

// Glow + kotak hint slot (HoverIndicators._draw_slot_hover: glow 80x80 di (slot-40), hint 100x18 di (slot-50, slot-36)).
Dictionary MysticUI::slot_hover_rects(int64_t sx, int64_t sy) {

    Dictionary out;
    out["glow"] = Rect2((double)(sx - 40), (double)(sy - 40), 80.0, 80.0);
    out["hint"] = Rect2((double)(sx - 50), (double)(sy - 36), 100.0, 18.0);
    return out;
}

// Label hint saat slot di-hover.
String MysticUI::slot_hint_text() {
    return String("TAP TO BUILD");
}

// Alpha animasi hover (HoverIndicators: pulse range = sin(t*0.1)*0.2+0.8, glow slot = sin(t*0.15)*0.3+0.7; alpha pygame = int(30*pulse) dan int(180*pulse)).
Dictionary MysticUI::hover_pulses(double animation_time) {

    double range_pulse = std::sin(animation_time * 0.1) * 0.2 + 0.8;
    double slot_pulse = std::sin(animation_time * 0.15) * 0.3 + 0.7;
    Dictionary out;
    out["range_fill_alpha"] = (int64_t)(30.0 * range_pulse);
    out["range_border_alpha"] = (int64_t)(180.0 * range_pulse);
    out["slot_pulse"] = slot_pulse;
    return out;
}

// Entri satu notifikasi (Notification.add_notification: text/color/timer=180).
Dictionary MysticUI::notification_entry(const String & text, const Color & color) {

    Dictionary out;
    out["text"] = text;
    out["color"] = color;
    out["timer"] = (int64_t)180;
    return out;
}

// Antrean notifikasi: salinan baru dengan satu entri ditambahkan (add_notification.append) — sumber tidak pernah menyisipkan ke tengah.
Array MysticUI::notification_push(const Array & messages, const String & text, const Color & color) {

    Array out = messages.duplicate();
    out.push_back(notification_entry(text, color));
    return out;
}

// Level yang BARU terbuka (Overlay._get_newly_unlocked_level: level sekarang sudah selesai dan level berikutnya belum). Balasan -1 = tidak ada.
int64_t MysticUI::newly_unlocked_level(int64_t current, const Array & completed, int64_t next_level) {

    if (next_level <= 0) {
        return -1;
    }
    bool current_done = false;
    bool next_done = false;
    for (int64_t i = 0; i < completed.size(); i++) {
        int64_t v = completed[i];
        if (v == current) {
            current_done = true;
        }
        if (v == next_level) {
            next_done = true;
        }
    }
    if (current_done && !next_done) {
        return next_level;
    }
    return -1;
}

// Popup LEVEL UNLOCKED (Overlay._draw_level_unlock_popup baris 2818: slide 30 frame ease-out-cubic 400px, alpha ramp 15 frame, 340x220 di (cx+220+slide, cy-100)).
Dictionary MysticUI::unlock_popup(int64_t timer, int64_t delay, int64_t cx, int64_t cy) {

    int64_t elapsed = timer - delay;
    Dictionary out;
    out["visible"] = elapsed >= 0;
    if (elapsed < 0) {
        out["slide_x"] = (int64_t)0;
        out["alpha"] = (int64_t)0;
        out["rect"] = Rect2();
        return out;
    }
    int64_t slide_duration = 30;
    int64_t offset_x = 0;
    if (elapsed < slide_duration) {
        double progress = (double)elapsed / (double)slide_duration;
        double eased = 1.0 - std::pow(1.0 - progress, 3.0);
        offset_x = (int64_t)((1.0 - eased) * (double)400);
    }
    int64_t alpha = (int64_t)(255.0 * ((double)elapsed / (double)15));
    if (alpha > 255) {
        alpha = 255;
    }
    out["slide_x"] = (int64_t)offset_x;
    out["alpha"] = (int64_t)alpha;
    out["rect"] = Rect2((double)(cx + 220 + offset_x), (double)(cy - 100),
            (double)340, (double)220);
    return out;
}

// Panel statistik akhir match (Overlay._draw_stats baris 2803: lebar 500, tinggi rows*38+24, baris y+15+i*32, badge NEW BEST 118x22).
Dictionary MysticUI::overlay_stats_panel(int64_t cx, int64_t cy, int64_t rows) {

    int64_t panel_w = 500;
    int64_t panel_h = rows * 38 + 24;
    int64_t panel_x = cx - panel_w / 2;
    int64_t panel_y = cy - 100;
    Dictionary out;
    out["rect"] = Rect2((double)panel_x, (double)panel_y, (double)panel_w,
            (double)panel_h);
    out["label_x"] = (int64_t)(panel_x + 20);
    out["value_right_x"] = (int64_t)(panel_x + panel_w - 20);
    Array rows_out;
    for (int64_t i = 0; i < rows; i++) {
        int64_t y = panel_y + 15 + i * 32;
        Dictionary row;
        row["y"] = (int64_t)y;
        row["badge"] = Rect2((double)(panel_x + panel_w / 2 - 30),
                (double)(y - 3), 118.0, 22.0);
        rows_out.push_back(row);
    }
    out["rows"] = rows_out;
    return out;
}

// Isi 5 baris statistik akhir match (Overlay._draw_stats: skor ribuan, waktu m:ss dari pemanggil, wave, kill, combo xN + flag NEW BEST).
Array MysticUI::overlay_stats_rows(int64_t score, const String & time_str, int64_t waves, int64_t kills, int64_t combo, bool best_score, bool best_time) {

    Array out;
    String labels[5] = { String("Final Score"), String("Match Time"),
            String("Waves Survived"), String("Total Kills"),
            String("Max Combo") };
    String values[5] = { thousands(score), time_str, String::num_int64(waves),
            String::num_int64(kills),
            String("x") + String::num_int64(combo) };
    bool bests[5] = { best_score, best_time, false, false, false };
    for (int64_t i = 0; i < 5; i++) {
        Dictionary row;
        row["label"] = labels[i];
        row["value"] = values[i];
        row["new_best"] = bests[i];
        out.push_back(row);
    }
    return out;
}

// Parse hint aksi (Overlay._draw_action_hint: re.findall '\[([^\]]+)\]\s*([^[\]]*)' + re.sub sisa teks). Balasan items (key/desc berpasangan) + plain (teks di luar keycap). Pemindai di sini meniru regex itu LANGKAH DEMI LANGKAH: kunci = isi [...] tanpa ']', spasi setelah ']' dimakan (\s* di luar grup), desc = sampai '[' / ']' berikutnya.
Dictionary MysticUI::action_hint_tokens(const String & action) {

    Dictionary out;
    Array items;
    String plain;
    int64_t i = 0;
    int64_t length = action.length();
    while (i < length) {
        String ch = action.substr(i, 1);
        if (ch == String("[")) {
            int64_t close = -1;
            for (int64_t j = i + 1; j < length; j++) {
                if (action.substr(j, 1) == String("]")) {
                    close = j;
                    break;
                }
            }
            if (close > i + 1) {
                String key = action.substr(i + 1, close - i - 1);
                int64_t k = close + 1;
                while (k < length && action.substr(k, 1).strip_edges().length() == 0) {
                    k++;
                }
                int64_t m = k;
                while (m < length && action.substr(m, 1) != String("[")
                        && action.substr(m, 1) != String("]")) {
                    m++;
                }
                Dictionary item;
                item["key"] = key;
                item["desc"] = action.substr(k, m - k).strip_edges();
                items.push_back(item);
                i = m;
                continue;
            }
        }
        plain += ch;
        i++;
    }
    out["items"] = items;
    out["plain"] = plain.strip_edges();
    return out;
}

// Teks jumlah achievement (Overlay._draw_achievements).
String MysticUI::achievements_text(int64_t count) {

    return String::num_int64(count) + String(" Achievements Unlocked!");
}

// Layout ikon + teks achievement (Overlay._draw_achievements baris 2803: total = 26 + lebar teks, ikon tx+11, teks tx+26, y = cy+250).
Dictionary MysticUI::achievements_layout(int64_t cx, int64_t cy, int64_t text_w) {

    int64_t total_w = 26 + text_w;
    int64_t tx = cx - total_w / 2;
    Dictionary out;
    out["text_x"] = (int64_t)(tx + 26);
    out["text_y"] = (int64_t)(cy + 241);
    out["icon_x"] = (int64_t)(tx + 11);
    out["icon_y"] = (int64_t)(cy + 250);
    out["total_w"] = (int64_t)total_w;
    return out;
}

// Daftar ability khusus menara (PopupRenderer._get_tower_specials baris 3936) — ambang > 0, urutan tetap: Splash, Slow, Chain, Double Shot, Burn, AtkSlow, SkillDown.
Array MysticUI::tower_specials(int64_t splash, double slow, int64_t chain, bool double_shot, int64_t burn_dps, double atk_slow, double skill_down) {

    Array out;
    if (splash > 0) {
        out.push_back(String("Splash ") + String::num_int64(splash));
    }
    if (slow > 0.0) {
        out.push_back(String("Slow ")
                + String::num_int64((int64_t)(slow * 100.0)) + String("%"));
    }
    if (chain > 1) {
        out.push_back(String("Chain x") + String::num_int64(chain));
    }
    if (double_shot) {
        out.push_back(String("Double Shot"));
    }
    if (burn_dps > 0) {
        out.push_back(String("Burn ") + String::num_int64(burn_dps)
                + String("/s"));
    }
    if (atk_slow > 0.0) {
        out.push_back(String("AtkSlow ")
                + String::num_int64((int64_t)(atk_slow * 100.0))
                + String("%"));
    }
    if (skill_down > 0.0) {
        out.push_back(String("SkillDown ")
                + String::num_int64((int64_t)(skill_down * 100.0))
                + String("%"));
    }
    return out;
}

// Judul popup menara (PopupRenderer._draw_tower_content: kalau "{name} Lv.{n}" lebih lebar dari popup_w-90 -> "Lv.{n} {Tipe}" dengan Title-Case ala Python str.title()).
String MysticUI::tower_title(const String & name, int64_t level, int64_t title_w, int64_t popup_w, const String & tower_type) {

    String full = name + String(" Lv.") + String::num_int64(level);
    if (title_w > popup_w - 90) {
        return String("Lv.") + String::num_int64(level) + String(" ")
                + tower_type.capitalize();
    }
    return full;
}

// Tiga baris stat nexus (PopupRenderer._draw_nexus_content: minion power diformat pemanggil = str(minion_scale) ala Python).
Array MysticUI::nexus_stat_lines(const String & minion_scale, int64_t ai_level, int64_t damage, int64_t range) {

    Array out;
    out.push_back(String("Minion Power: x") + minion_scale);
    out.push_back(String("AI Level: ") + String::num_int64(ai_level)
            + String("/5"));
    out.push_back(String("DMG: ") + String::num_int64(damage)
            + String("  RNG: ") + String::num_int64(range));
    return out;
}

// Nama castle dari level nexus (PopupRenderer._draw_nexus_content baris 3657: 1..5, selain itu CITADEL).
String MysticUI::castle_name(int64_t nexus_level) {

    if (nexus_level == 1) { return String("OUTPOST"); }
    if (nexus_level == 2) { return String("WATCHTOWER"); }
    if (nexus_level == 3) { return String("FORTRESS"); }
    if (nexus_level == 4) { return String("STRONGHOLD"); }
    if (nexus_level == 5) { return String("ROYAL CASTLE"); }
    return String("CITADEL");
}

// Bagian castle shield popup nexus (PopupRenderer._draw_castle_shield_section): gratis wave 1-10 / sudah dibeli / bisa dibeli (gold cukup) / - (tidak ada). `next_y` = y+46 kalau pill digambar.
Dictionary MysticUI::castle_shield_section(bool free_shield, bool purchased, bool can_buy, int64_t cost, int64_t gold) {

    Dictionary out;
    out["state"] = String("-");
    out["label"] = String();
    out["next_y"] = (int64_t)0;
    if (free_shield) {
        out["state"] = String("free");
        out["label"] = String("CASTLE SHIELD: FREE (WAVE 1-10)");
        out["kind"] = String("cyan");
        out["next_y"] = (int64_t)46;
        return out;
    }
    if (purchased) {
        out["state"] = String("on");
        out["label"] = String("CASTLE SHIELD: ON");
        out["kind"] = String("success");
        out["next_y"] = (int64_t)46;
        return out;
    }
    if (can_buy) {
        out["state"] = String("buy");
        out["label"] = String("ACTIVATE SHIELD (") + String::num_int64(cost)
                + String("G)");
        out["kind"] = gold >= cost ? String("gold") : String("locked");
        out["interactive"] = gold >= cost;
        out["next_y"] = (int64_t)46;
        return out;
    }
    return out;
}

// Bagian regen shield menara level >= 4 (PopupRenderer._draw_regen_shield_section).
Dictionary MysticUI::regen_shield_section(bool active, bool can_buy, int64_t cost, int64_t gold) {

    Dictionary out;
    out["state"] = String("-");
    if (active) {
        out["state"] = String("on");
        out["label"] = String("REGEN SHIELD: ON");
        out["kind"] = String("success");
        return out;
    }
    if (can_buy) {
        out["state"] = String("buy");
        out["label"] = String("REGEN SHIELD (") + String::num_int64(cost)
                + String("G)");
        out["kind"] = gold >= cost ? String("gold") : String("locked");
        out["interactive"] = gold >= cost;
        return out;
    }
    return out;
}

// 4 kartu pilihan path level 1 (PopupRenderer._draw_tower_path_buttons baris 3936: btn_w = (popup_w-46)//2, h 68, gap 12/8, mulai y+26).
Array MysticUI::tower_path_buttons(int64_t px, int64_t y, int64_t popup_w) {

    Array out;
    int64_t btn_w = (popup_w - 46) / 2;
    int64_t btn_h = 68;
    int64_t start_y = y + 26;
    for (int64_t i = 0; i < 4; i++) {
        int64_t col = i % 2;
        int64_t row = i / 2;
        int64_t bx = px + 15 + col * (btn_w + 12);
        int64_t by = start_y + row * (btn_h + 8);
        out.push_back(Rect2((double)bx, (double)by, (double)btn_w,
                (double)btn_h));
    }
    return out;
}

// Nama pada kartu path (info['name'] tanpa suffix ' Tower').
String MysticUI::path_button_name(const String & tower_info_name) {

    return tower_info_name.replace(String(" Tower"), String());
}

// Label biaya kartu path / tombol.
String MysticUI::path_cost_text(int64_t cost) {

    return String::num_int64(cost) + String("G");
}

// Tombol UPGRADE + SELL level 2+ (PopupRenderer._draw_tower_upgrade_button: btn_w = (popup_w-46)//2, h 40, sell di px+27+btn_w).
Dictionary MysticUI::tower_upgrade_buttons(int64_t px, int64_t y, int64_t popup_w) {

    int64_t btn_w = (popup_w - 46) / 2;
    int64_t btn_h = 40;
    Dictionary out;
    out["upgrade"] = Rect2((double)(px + 15), (double)y, (double)btn_w,
            (double)btn_h);
    out["sell"] = Rect2((double)(px + 27 + btn_w), (double)y, (double)btn_w,
            (double)btn_h);
    return out;
}

// Panel MAX LEVEL + jual (PopupRenderer._draw_tower_max_level: MAX terpusat y+14, tombol SELL 150x34 (popup_w-150)//2 di y+36 bila nilai jual > 0).
Dictionary MysticUI::tower_max_layout(int64_t px, int64_t y, int64_t popup_w, int64_t sell_value) {

    Dictionary out;
    out["max_center_x"] = (int64_t)(px + popup_w / 2);
    out["max_center_y"] = (int64_t)(y + 14);
    if (sell_value > 0) {
        out["sell"] = Rect2((double)(px + (popup_w - 150) / 2),
                (double)(y + 36), 150.0, 34.0);
    } else {
        out["sell"] = Rect2();
    }
    return out;
}

// Baris preview upgrade (PopupRenderer._draw_tower_upgrade_button: "Lv{n}: DMG {dmg} HP {hp}").
String MysticUI::upgrade_preview_text(int64_t next_level, int64_t damage, int64_t hp) {

    return String("Lv") + String::num_int64(next_level) + String(": DMG ")
            + String::num_int64(damage) + String(" HP ")
            + String::num_int64(hp);
}

// Posisi hint toko di peta (ShopHints.draw baris 4090: shop_pos + anchor + pulse vertikal; anchor ITEM FORGE (82,-30), HERO SHOP (-82,44)).
Vector2 MysticUI::shop_hint_pos(double sx, double sy, int64_t ax, int64_t ay, int64_t pulse) {

    return Vector2(sx + (double)ax, sy + (double)ay + (double)pulse);
}

// Kotak pill hint dari teks terukur (ShopHints._draw_single_hint: get_rect(center) lalu inflate(16, 8) — center integer pygame).
Rect2 MysticUI::shop_hint_bg(int64_t center_x, int64_t center_y, int64_t text_w, int64_t text_h) {

    int64_t bg_w = text_w + 16;
    int64_t bg_h = text_h + 8;
    return Rect2((double)(center_x - text_w / 2 - 8),
            (double)(center_y - text_h / 2 - 4), (double)bg_w,
            (double)bg_h);
}

// Denyut vertikal hint toko: int(sin(t*0.06)*2) — trunc ke arah nol, BUKAN round.
int64_t MysticUI::shop_hint_pulse(double animation_time) {

    return (int64_t)(std::sin(animation_time * 0.06) * 2.0);
}


void MysticUI::_bind_methods() {
    ClassDB::bind_static_method("MysticUI", D_METHOD("module_names"), &MysticUI::module_names);
    ClassDB::bind_static_method("MysticUI", D_METHOD("module_names_string"), &MysticUI::module_names_string);
    ClassDB::bind_static_method("MysticUI", D_METHOD("api_signature"), &MysticUI::api_signature);
    ClassDB::bind_static_method("MysticUI", D_METHOD("tower_type_colors"), &MysticUI::tower_type_colors);
    ClassDB::bind_static_method("MysticUI", D_METHOD("tower_cards"), &MysticUI::tower_cards);
    ClassDB::bind_static_method("MysticUI", D_METHOD("build_cost"), &MysticUI::build_cost);
    ClassDB::bind_static_method("MysticUI", D_METHOD("notification_duration"), &MysticUI::notification_duration);
    ClassDB::bind_static_method("MysticUI", D_METHOD("close_button_rect", "x", "y", "size"), &MysticUI::close_button_rect);
    ClassDB::bind_static_method("MysticUI", D_METHOD("hp_bar_color", "ratio"), &MysticUI::hp_bar_color);
    ClassDB::bind_static_method("MysticUI", D_METHOD("hp_bar_fill", "w", "ratio"), &MysticUI::hp_bar_fill);
    ClassDB::bind_static_method("MysticUI", D_METHOD("shadow_rect", "rect", "offset"), &MysticUI::shadow_rect);
    ClassDB::bind_static_method("MysticUI", D_METHOD("popup_width", "design_w", "panel_w"), &MysticUI::popup_width);
    ClassDB::bind_static_method("MysticUI", D_METHOD("build_popup_rect", "slot_x", "slot_y", "screen_w", "screen_h"), &MysticUI::build_popup_rect);
    ClassDB::bind_static_method("MysticUI", D_METHOD("target_popup_rect", "target_x", "target_y", "screen_w", "screen_h", "top_bar_h"), &MysticUI::target_popup_rect);
    ClassDB::bind_static_method("MysticUI", D_METHOD("build_popup_buttons", "px", "py", "popup_w"), &MysticUI::build_popup_buttons);
    ClassDB::bind_static_method("MysticUI", D_METHOD("build_gold_text", "gold"), &MysticUI::build_gold_text);
    ClassDB::bind_static_method("MysticUI", D_METHOD("build_button_style", "can_afford", "hover", "color"), &MysticUI::build_button_style);
    ClassDB::bind_static_method("MysticUI", D_METHOD("hover_hit", "rect", "mouse", "enabled"), &MysticUI::hover_hit);
    ClassDB::bind_static_method("MysticUI", D_METHOD("slot_blit_offset"), &MysticUI::slot_blit_offset);
    ClassDB::bind_static_method("MysticUI", D_METHOD("slot_surface_rect", "sx", "sy"), &MysticUI::slot_surface_rect);
    ClassDB::bind_static_method("MysticUI", D_METHOD("slot_pulse", "animation_time"), &MysticUI::slot_pulse);
    ClassDB::bind_static_method("MysticUI", D_METHOD("slot_cost_bg", "sx", "sy"), &MysticUI::slot_cost_bg);
    ClassDB::bind_static_method("MysticUI", D_METHOD("slot_cost_text"), &MysticUI::slot_cost_text);
    ClassDB::bind_static_method("MysticUI", D_METHOD("portrait_scan_step"), &MysticUI::portrait_scan_step);
    ClassDB::bind_static_method("MysticUI", D_METHOD("portrait_alpha_min"), &MysticUI::portrait_alpha_min);
    ClassDB::bind_static_method("MysticUI", D_METHOD("portrait_crop_box", "min_x", "min_y", "max_x", "max_y", "canvas_w", "canvas_h"), &MysticUI::portrait_crop_box);
    ClassDB::bind_static_method("MysticUI", D_METHOD("portrait_scale_size", "crop_w", "crop_h", "target_w", "target_h"), &MysticUI::portrait_scale_size);
    ClassDB::bind_static_method("MysticUI", D_METHOD("portrait_gray_weight"), &MysticUI::portrait_gray_weight);
    ClassDB::bind_static_method("MysticUI", D_METHOD("hero_panel_rect", "screen_h"), &MysticUI::hero_panel_rect);
    ClassDB::bind_static_method("MysticUI", D_METHOD("hero_panel_layout", "px", "py"), &MysticUI::hero_panel_layout);
    ClassDB::bind_static_method("MysticUI", D_METHOD("skill_key_font_size", "label_len"), &MysticUI::skill_key_font_size);
    ClassDB::bind_static_method("MysticUI", D_METHOD("skill_badge_rect", "x", "y", "size", "key_w"), &MysticUI::skill_badge_rect);
    ClassDB::bind_static_method("MysticUI", D_METHOD("cooldown_seconds", "frames"), &MysticUI::cooldown_seconds);
    ClassDB::bind_static_method("MysticUI", D_METHOD("cooldown_overlay_h", "size", "cooldown", "cooldown_max"), &MysticUI::cooldown_overlay_h);
    ClassDB::bind_static_method("MysticUI", D_METHOD("item_forge_label", "used", "max_slots"), &MysticUI::item_forge_label);
    ClassDB::bind_static_method("MysticUI", D_METHOD("hero_upgrade_label", "cost"), &MysticUI::hero_upgrade_label);
    ClassDB::bind_static_method("MysticUI", D_METHOD("max_level_label"), &MysticUI::max_level_label);
    ClassDB::bind_static_method("MysticUI", D_METHOD("autocast_label", "is_auto"), &MysticUI::autocast_label);
    ClassDB::bind_static_method("MysticUI", D_METHOD("shop_panel_rect", "screen_w", "screen_h"), &MysticUI::shop_panel_rect);
    ClassDB::bind_static_method("MysticUI", D_METHOD("shop_tabs", "panel_x", "panel_w", "panel_y", "header_h"), &MysticUI::shop_tabs);
    ClassDB::bind_static_method("MysticUI", D_METHOD("shop_content", "panel_y", "header_h"), &MysticUI::shop_content);
    ClassDB::bind_static_method("MysticUI", D_METHOD("shop_hero_list", "purchased", "is_boss", "tab"), &MysticUI::shop_hero_list);
    ClassDB::bind_static_method("MysticUI", D_METHOD("shop_grid", "panel_x", "panel_w", "content_top", "content_bottom", "count", "scroll"), &MysticUI::shop_grid);
    ClassDB::bind_static_method("MysticUI", D_METHOD("shop_card_rects", "cx", "cy", "cw", "ch"), &MysticUI::shop_card_rects);
    ClassDB::bind_static_method("MysticUI", D_METHOD("shop_card_state", "owned", "hero_count", "max_owned", "gold", "cost"), &MysticUI::shop_card_state);
    ClassDB::bind_static_method("MysticUI", D_METHOD("shop_scroll_thumb", "x", "y", "height", "scroll", "max_scroll"), &MysticUI::shop_scroll_thumb);
    ClassDB::bind_static_method("MysticUI", D_METHOD("shop_scroll_buttons", "panel_x", "panel_w", "content_top", "content_bottom"), &MysticUI::shop_scroll_buttons);
    ClassDB::bind_static_method("MysticUI", D_METHOD("shop_gold_text", "gold"), &MysticUI::shop_gold_text);
    ClassDB::bind_static_method("MysticUI", D_METHOD("shop_owned_text", "owned", "max_owned"), &MysticUI::shop_owned_text);
    ClassDB::bind_static_method("MysticUI", D_METHOD("shop_empty_state", "tab"), &MysticUI::shop_empty_state);
    ClassDB::bind_static_method("MysticUI", D_METHOD("hover_target", "mx", "my", "towers", "slots", "blocked"), &MysticUI::hover_target);
    ClassDB::bind_static_method("MysticUI", D_METHOD("tower_tooltip_lines", "name", "level", "damage", "range", "kills"), &MysticUI::tower_tooltip_lines);
    ClassDB::bind_static_method("MysticUI", D_METHOD("tooltip_rects", "tower_x", "tower_y", "bg_w", "bg_h"), &MysticUI::tooltip_rects);
    ClassDB::bind_static_method("MysticUI", D_METHOD("slot_hover_rects", "sx", "sy"), &MysticUI::slot_hover_rects);
    ClassDB::bind_static_method("MysticUI", D_METHOD("slot_hint_text"), &MysticUI::slot_hint_text);
    ClassDB::bind_static_method("MysticUI", D_METHOD("hover_pulses", "animation_time"), &MysticUI::hover_pulses);
    ClassDB::bind_static_method("MysticUI", D_METHOD("notification_entry", "text", "color"), &MysticUI::notification_entry);
    ClassDB::bind_static_method("MysticUI", D_METHOD("notification_push", "messages", "text", "color"), &MysticUI::notification_push);
    ClassDB::bind_static_method("MysticUI", D_METHOD("newly_unlocked_level", "current", "completed", "next_level"), &MysticUI::newly_unlocked_level);
    ClassDB::bind_static_method("MysticUI", D_METHOD("unlock_popup", "timer", "delay", "cx", "cy"), &MysticUI::unlock_popup);
    ClassDB::bind_static_method("MysticUI", D_METHOD("overlay_stats_panel", "cx", "cy", "rows"), &MysticUI::overlay_stats_panel);
    ClassDB::bind_static_method("MysticUI", D_METHOD("overlay_stats_rows", "score", "time_str", "waves", "kills", "combo", "best_score", "best_time"), &MysticUI::overlay_stats_rows);
    ClassDB::bind_static_method("MysticUI", D_METHOD("action_hint_tokens", "action"), &MysticUI::action_hint_tokens);
    ClassDB::bind_static_method("MysticUI", D_METHOD("achievements_text", "count"), &MysticUI::achievements_text);
    ClassDB::bind_static_method("MysticUI", D_METHOD("achievements_layout", "cx", "cy", "text_w"), &MysticUI::achievements_layout);
    ClassDB::bind_static_method("MysticUI", D_METHOD("tower_specials", "splash", "slow", "chain", "double_shot", "burn_dps", "atk_slow", "skill_down"), &MysticUI::tower_specials);
    ClassDB::bind_static_method("MysticUI", D_METHOD("tower_title", "name", "level", "title_w", "popup_w", "tower_type"), &MysticUI::tower_title);
    ClassDB::bind_static_method("MysticUI", D_METHOD("nexus_stat_lines", "minion_scale", "ai_level", "damage", "range"), &MysticUI::nexus_stat_lines);
    ClassDB::bind_static_method("MysticUI", D_METHOD("castle_name", "nexus_level"), &MysticUI::castle_name);
    ClassDB::bind_static_method("MysticUI", D_METHOD("castle_shield_section", "free_shield", "purchased", "can_buy", "cost", "gold"), &MysticUI::castle_shield_section);
    ClassDB::bind_static_method("MysticUI", D_METHOD("regen_shield_section", "active", "can_buy", "cost", "gold"), &MysticUI::regen_shield_section);
    ClassDB::bind_static_method("MysticUI", D_METHOD("tower_path_buttons", "px", "y", "popup_w"), &MysticUI::tower_path_buttons);
    ClassDB::bind_static_method("MysticUI", D_METHOD("path_button_name", "tower_info_name"), &MysticUI::path_button_name);
    ClassDB::bind_static_method("MysticUI", D_METHOD("path_cost_text", "cost"), &MysticUI::path_cost_text);
    ClassDB::bind_static_method("MysticUI", D_METHOD("tower_upgrade_buttons", "px", "y", "popup_w"), &MysticUI::tower_upgrade_buttons);
    ClassDB::bind_static_method("MysticUI", D_METHOD("tower_max_layout", "px", "y", "popup_w", "sell_value"), &MysticUI::tower_max_layout);
    ClassDB::bind_static_method("MysticUI", D_METHOD("upgrade_preview_text", "next_level", "damage", "hp"), &MysticUI::upgrade_preview_text);
    ClassDB::bind_static_method("MysticUI", D_METHOD("shop_hint_pos", "sx", "sy", "ax", "ay", "pulse"), &MysticUI::shop_hint_pos);
    ClassDB::bind_static_method("MysticUI", D_METHOD("shop_hint_bg", "center_x", "center_y", "text_w", "text_h"), &MysticUI::shop_hint_bg);
    ClassDB::bind_static_method("MysticUI", D_METHOD("shop_hint_pulse", "animation_time"), &MysticUI::shop_hint_pulse);
}

} // namespace godot
