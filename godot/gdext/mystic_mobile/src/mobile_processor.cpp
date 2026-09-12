#include "mobile_processor.h"

#include <godot_cpp/core/class_db.hpp>

#include <cctype>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <string>

// ═══ GENERATED — JANGAN SUNTING TANGAN ═══
// Sumber    : mobile/*.py
// Generator : tools/gen_mobile_cpp.py
// Regenerasi: python3 tools/gen_mobile_cpp.py
// Cek CI    : python3 tools/gen_mobile_cpp.py --check
//
// Setiap fungsi menyebut baris sumber Python yang direplikasi. Angka yang
// diekstrak generator datang dari AST (bukan salinan tangan); perilakunya
// dikunci oracle mobile/*.py ASLI + self-test tanpa engine
// (tools/test_mobile_cpp_selftest.py).

namespace godot {

// `//` Python: floor ke arah -inf (C++ `/` memotong ke arah nol).
int64_t MysticMobile::py_floordiv(int64_t a, int64_t b) {
    int64_t q = a / b;
    if ((a % b != 0) && ((a < 0) != (b < 0))) {
        q--;
    }
    return q;
}

// `%` Python: tanda mengikuti pembagi (C++ % tanda mengikuti dividend).
int64_t MysticMobile::py_mod(int64_t a, int64_t b) {
    int64_t r = a % b;
    if (r != 0 && ((r < 0) != (b < 0))) {
        r += b;
    }
    return r;
}

Array MysticMobile::module_names() {

Array out;
out.push_back(String("touch"));
out.push_back(String("hud"));
out.push_back(String("perf"));
out.push_back(String("platform_utils"));
out.push_back(String("debug"));
out.push_back(String("combat_audio"));
out.push_back(String("cloud_save"));
out.push_back(String("buildinfo"));
return out;
}

String MysticMobile::module_names_string() {

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

String MysticMobile::api_signature() {

// Cap jari API: jumlah modul + fungsi (dipakui loader membuktikan backend C++
// benar-benar jalan; string ini TAHAN STRIP jadi juga di-grep CI dari .so).
return String("mobile_v1:8mod:66fn:");
}

Dictionary MysticMobile::touch_constants() {

// Ambang gesture dalam koordinat logis 1280x720 (touch.py:28-33) + literal
// mesin gesture di _motion/_up/update.
Dictionary out;
    out[Variant(String("tap_slop"))] = (int64_t)14 /* touch.py:27 TAP_SLOP */;
    out[Variant(String("long_press_ms"))] = (int64_t)450 /* touch.py:28 LONG_PRESS_MS */;
    out[Variant(String("double_tap_ms"))] = (int64_t)280 /* touch.py:29 DOUBLE_TAP_MS */;
    out[Variant(String("scroll_step"))] = (int64_t)42 /* touch.py:30 SCROLL_STEP */;
    out[Variant(String("fling_friction"))] = 0.90000000000000002 /* touch.py:31 FLING_FRICTION */;
    out[Variant(String("fling_min_speed"))] = 0.59999999999999998 /* touch.py:32 FLING_MIN_SPEED */;
    out[Variant(String("double_tap_radius_px"))] = (int64_t)40 /* touch.py:226 literal _up */;
    out[Variant(String("fling_arm_speed"))] = (int64_t)4 /* touch.py:236 literal _up */;
    out[Variant(String("fling_divisor"))] = 0.34999999999999998 /* touch.py:258 literal update */;
    out[Variant(String("fling_max_steps"))] = (int64_t)3 /* touch.py:259 literal update */;
    out[Variant(String("velocity_keep"))] = 0.59999999999999998 /* touch.py:206 _motion */;
    out[Variant(String("velocity_new"))] = 0.40000000000000002 /* touch.py:206 _motion */;
return out;
}

double MysticMobile::motion_velocity(double p_prev_velocity, double p_dy) {

// touch.py:206 TouchManager._motion: tp.velocity = tp.velocity * 0.59999999999999998 + dy * 0.40000000000000002
return p_prev_velocity * 0.59999999999999998 + p_dy * 0.40000000000000002;
}

bool MysticMobile::motion_exceeds_slop(double p_total_dist) {

// touch.py:247-249 TouchManager._motion: total > TAP_SLOP -> tp.moved = True
// (geser di bawah ambang masih dianggap tap saat jari dilepas).
return p_total_dist > (int64_t)14;
}

Dictionary MysticMobile::scroll_notch(double p_accum) {

// touch.py:258-263 TouchManager._motion — SATU langkah loop:
//   while abs(scroll_accum) >= SCROLL_STEP:
//       direction = -1 if scroll_accum > 0 else 1
//       scroll_accum -= SCROLL_STEP * (1 if scroll_accum > 0 else -1)
// Pemanggil mengulang selama abs(accum) >= scroll_step.
const int64_t direction = (p_accum > 0.0) ? -1 : 1;
const double sub = (int64_t)42 * ((p_accum > 0.0) ? 1.0 : -1.0);
Dictionary out;
out[Variant(String("direction"))] = Variant(direction);
out[Variant(String("accum"))] = Variant(p_accum - sub);
return out;
}

bool MysticMobile::tap_is_double(double p_dt_ms, double p_dx, double p_dy) {

// touch.py:279-283 TouchManager._up: (now - last_tap_time) * 1000.0 <
// DOUBLE_TAP_MS and abs(dx) < 40 and abs(dy) < 40
return p_dt_ms < (int64_t)280 && std::fabs(p_dx) < (int64_t)40 && std::fabs(p_dy) < (int64_t)40;
}

bool MysticMobile::release_is_fling(bool p_moved, double p_velocity) {

// touch.py:236 TouchManager._up: elif tp.moved and abs(tp.velocity) > (int64_t)4:
return p_moved && std::fabs(p_velocity) > (int64_t)4;
}

int64_t MysticMobile::fling_steps(double p_velocity) {

// touch.py:258/259 TouchManager.update:
//   steps = int(abs(v) / (SCROLL_STEP * 0.34999999999999998)); range(min(steps, 3))
const double denom = (int64_t)42 * 0.34999999999999998;
const int64_t steps = (int64_t)(std::fabs(p_velocity) / denom);
const int64_t cap = (int64_t)3;
return (steps < cap) ? steps : cap;
}

int64_t MysticMobile::fling_direction(double p_velocity) {

// touch.py:324 TouchManager.update: value=-1 if self.fling_velocity > 0 else 1
return (p_velocity > 0.0) ? -1 : 1;
}

double MysticMobile::fling_decay(double p_velocity) {

// touch.py:321 TouchManager.update: self.fling_velocity *= FLING_FRICTION
return p_velocity * 0.90000000000000002;
}

bool MysticMobile::fling_active(double p_velocity) {

// touch.py:320 TouchManager.update: if abs(self.fling_velocity) >
// FLING_MIN_SPEED (di bawah itu inersia di-nol-kan)
return std::fabs(p_velocity) > 0.59999999999999998;
}

bool MysticMobile::long_press_due(double p_held_ms) {

// touch.py:251 TouchManager.update: (now - tp.start_time) * 1000.0 >=
// LONG_PRESS_MS -> long_press sekali (long_fired)
return p_held_ms >= (int64_t)450;
}

int64_t MysticMobile::dispatch_button(const String & p_kind, int64_t p_value) {

// touch.py:333-343 dispatch_to_game: tap -> klik kiri (1),
// long_press -> klik kanan (3), scroll -> 4 (naik, value<0) / 5 (turun).
if (p_kind == String("tap")) {
    return 1;
}
if (p_kind == String("long_press")) {
    return 3;
}
if (p_kind == String("scroll")) {
    return (p_value < 0) ? 4 : 5;
}
return 0;
}

int64_t MysticMobile::hud_min_tap() {

// hud.py:38 MIN_TAP: sisi minimum area sentuh, px logis 1280x720
// (>= 48dp rekomendasi Google; dipakai 80).
return (int64_t)80;
}

Dictionary MysticMobile::hud_button_rects(int64_t p_safe_left, int64_t p_safe_top, int64_t p_safe_right, int64_t p_safe_bottom) {

// hud.py:91-128 TouchHUD._build_layout — rect tombol dalam koordinat logis.
// pause + debug kiri atas di bawah panel gold; skip/replay/next/menu
// kontekstual di dasar safe area; back kiri atas (menu).
const int64_t bx = std::max((int64_t)22, p_safe_left + 6);
const int64_t by = 76;
const int64_t mid = 1280 / 2;
Dictionary out;
    out[Variant(String("pause"))] = Rect2((double)bx, (double)by, 52.0, 52.0);
    out[Variant(String("debug"))] = Rect2((double)(bx + 84), (double)by, 52.0, 52.0);
    out[Variant(String("skip"))] = Rect2((double)(p_safe_right - 170), (double)(p_safe_bottom - 74), 160.0, 58.0);
    out[Variant(String("replay"))] = Rect2((double)(mid - 310), (double)(p_safe_bottom - 100), 165.0, 62.0);
    out[Variant(String("next_level"))] = Rect2((double)(mid - 115), (double)(p_safe_bottom - 100), 200.0, 62.0);
    out[Variant(String("menu"))] = Rect2((double)(mid + 115), (double)(p_safe_bottom - 100), 165.0, 62.0);
    out[Variant(String("back"))] = Rect2((double)(p_safe_left + 8), (double)(p_safe_top + 6), 104.0, 58.0);
return out;
}

Rect2 MysticMobile::hud_hit_rect(const Rect2 & p_rect) {

// hud.py:67-69 TouchButton.__init__: hit_rect = rect.inflate(24, 24); kalau
// lebih kecil dari MIN_TAP (80) di salah satu sumbu -> inflate tambahan
// supaya area sentuh memenuhi minimum (pygame Rect.inflate: center tetap).
const int64_t x = (int64_t)p_rect.position.x;
const int64_t y = (int64_t)p_rect.position.y;
const int64_t w = (int64_t)p_rect.size.x;
const int64_t ht = (int64_t)p_rect.size.y;
// pygame Rect.inflate(dx, dy): ukuran tumbuh TOTAL dx/dy (bukan per sisi),
// sudut kiri-atas mundur dx/2 (pembagian bulat) supaya pusat tetap.
const int64_t inf = (int64_t)24;
int64_t hx = x - py_floordiv(inf, 2);
int64_t hy = y - py_floordiv(inf, 2);
int64_t hw = w + inf;
int64_t hht = ht + inf;
const int64_t min_tap = (int64_t)80;
if (hw < min_tap || hht < min_tap) {
    const int64_t dx = std::max((int64_t)0, min_tap - w);
    const int64_t dy = std::max((int64_t)0, min_tap - ht);
    hx = x - py_floordiv(dx, 2);
    hy = y - py_floordiv(dy, 2);
    hw = w + dx;
    hht = ht + dy;
}
return Rect2((double)hx, (double)hy, (double)hw, (double)hht);
}

bool MysticMobile::hud_button_contains(bool p_visible, const Rect2 & p_hit_rect, const Vector2 & p_pos) {

// hud.py:73-74 TouchButton.contains: self.visible and
// self.hit_rect.collidepoint(pos) — sisi max TIDAK termasuk (semantik
// pygame.Rect.collidepoint).
if (!p_visible) {
    return false;
}
return p_pos.x >= p_hit_rect.position.x &&
       p_pos.x < p_hit_rect.position.x + p_hit_rect.size.x &&
       p_pos.y >= p_hit_rect.position.y &&
       p_pos.y < p_hit_rect.position.y + p_hit_rect.size.y;
}

Dictionary MysticMobile::hud_visibility(bool p_playing, bool p_ended, bool p_victory, bool p_has_next_level, bool p_cinematic_active, bool p_panel_ada, bool p_show_debug_button) {

// hud.py:136-161 TouchHUD.sync — visibility tiap tombol. `has_next_level`
// pygame datang dari levels.get_next_level(level_number) is not None
// (jalur engine, hanya ditanya saat ended+victory).
Dictionary out;
    out[Variant(String("pause"))] = p_playing && !p_cinematic_active && !p_panel_ada;
    out[Variant(String("debug"))] = p_show_debug_button && !p_cinematic_active && !p_panel_ada;
    out[Variant(String("skip"))] = p_cinematic_active;
    out[Variant(String("replay"))] = p_ended;
    out[Variant(String("menu"))] = p_ended;
    out[Variant(String("next_level"))] = p_ended && p_victory && p_has_next_level;
return out;
}

double MysticMobile::hud_press_anim_next(double p_press_anim) {

// hud.py:162-164 TouchHUD.sync: press_anim = max(0.0, press_anim - 0.12)
const double next = p_press_anim - 0.12;
return (next < 0.0) ? 0.0 : next;
}

Dictionary MysticMobile::hud_colors() {

// hud.py:37-43 palet HUD sentuh.
Dictionary out;
    out[Variant(String("gold"))] = Color((float)255 / 255.0f, (float)200 / 255.0f, (float)70 / 255.0f, (float)255 / 255.0f);
    out[Variant(String("gold_dim"))] = Color((float)150 / 255.0f, (float)118 / 255.0f, (float)40 / 255.0f, (float)255 / 255.0f);
    out[Variant(String("bg"))] = Color((float)16 / 255.0f, (float)14 / 255.0f, (float)22 / 255.0f, (float)205 / 255.0f);
    out[Variant(String("bg_active"))] = Color((float)60 / 255.0f, (float)48 / 255.0f, (float)20 / 255.0f, (float)235 / 255.0f);
    out[Variant(String("white"))] = Color((float)235 / 255.0f, (float)235 / 255.0f, (float)245 / 255.0f, (float)255 / 255.0f);
    out[Variant(String("grey"))] = Color((float)120 / 255.0f, (float)120 / 255.0f, (float)135 / 255.0f, (float)255 / 255.0f);
    out[Variant(String("red"))] = Color((float)210 / 255.0f, (float)70 / 255.0f, (float)70 / 255.0f, (float)255 / 255.0f);
return out;
}

Dictionary MysticMobile::hud_skill_labels() {

// hud.py:40 SKILL_LABELS (tombol skill dihapus v27 auto-cast; dipertahankan
// untuk paritas data).
Dictionary out;
    out[Variant(String("q"))] = "Q";
    out[Variant(String("w"))] = "W";
    out[Variant(String("e"))] = "E";
    out[Variant(String("r"))] = "R";
return out;
}

Dictionary MysticMobile::hud_skill_names() {

// hud.py:41 SKILL_NAMES.
Dictionary out;
    out[Variant(String("q"))] = "SKILL 1";
    out[Variant(String("w"))] = "SKILL 2";
    out[Variant(String("e"))] = "SKILL 3";
    out[Variant(String("r"))] = "ULTI";
return out;
}

Array MysticMobile::tactical_actions() {

// hud.py:47-48 TACTICAL_ACTIONS — sama dengan konstanta
// tactical_commands.TacticalCommand (mode HOLD tombol side panel).
Array out;
out.push_back(String("gather"));
out.push_back(String("protect_tower"));
out.push_back(String("protect_castle"));
out.push_back(String("attack_boss"));
out.push_back(String("attack_damage_dealer"));
return out;
}

Array MysticMobile::quality_levels() {

// perf.py:448: LOW, MEDIUM, HIGH = "low", "medium", "high"
Array out;
out.push_back(String("low"));
out.push_back(String("medium"));
out.push_back(String("high"));
return out;
}

Dictionary MysticMobile::quality_preset(const String & p_level) {

// perf.py:500-578 _Quality.apply — preset efek per level. Level tak dikenal
// berperilaku seperti HIGH tanpa screen_shake (low/med = false) — semantik
// perbandingan == Python direplikasi apa adanya.
const bool low = p_level == String("low");
const bool med = p_level == String("medium");
Dictionary out;
    out[Variant(String("particles"))] = !low;
    out[Variant(String("particle_ratio"))] = low ? 0.20000000000000001 : (med ? 0.40000000000000002 : 0.69999999999999996);
    out[Variant(String("fog"))] = !low;
    out[Variant(String("shadows"))] = true;
    out[Variant(String("soft_shadows"))] = !(low || med);
    out[Variant(String("glow"))] = !low;
    out[Variant(String("screen_shake"))] = p_level == String("high");
    out[Variant(String("aa_circles"))] = !low;
    out[Variant(String("floating_decor"))] = !low;
    out[Variant(String("max_damage_numbers"))] = low ? (int64_t)8 : (med ? (int64_t)16 : (int64_t)32);
    out[Variant(String("target_fps"))] = low ? (int64_t)30 : (int64_t)60;
    out[Variant(String("hd_edge"))] = !low;
    out[Variant(String("hero_lighting"))] = !low;
    out[Variant(String("max_hero_render"))] = low ? (int64_t)3 : (med ? (int64_t)4 : (int64_t)8);
    out[Variant(String("skill_quant_floor"))] = low ? (int64_t)12 : (med ? (int64_t)8 : (int64_t)4);
    out[Variant(String("atk_quant_floor"))] = low ? (int64_t)6 : (med ? (int64_t)4 : (int64_t)3);
    out[Variant(String("fx_ground_budget"))] = low ? (int64_t)2 : (med ? (int64_t)3 : (int64_t)6);
return out;
}

Dictionary MysticMobile::quality_defaults() {

// perf.py:469-481 _Quality.__init__ — properti perangkat yang TIDAK boleh
// ditimpa preset (diukur SEKALI oleh apply_device_profile).
Dictionary out;
    out[Variant(String("cheap_alpha"))] = true;
    out[Variant(String("use_colorkey_sprites"))] = false;
    out[Variant(String("max_alpha_px"))] = (int64_t)1000000;
    out[Variant(String("colorkey_gain"))] = 1.0;
    out[Variant(String("sprite_cache"))] = false;
    out[Variant(String("base_particle_ratio"))] = 1.0;
return out;
}

double MysticMobile::particle_ratio_effective(double p_base_ratio, double p_fx_load) {

// perf.py:487-496 Quality.particle_ratio: base * fx_load()
return p_base_ratio * p_fx_load;
}

double MysticMobile::fx_load_target(int64_t p_n_active) {

// perf.py:632-647 set_fx_load: target beban FX dari jumlah hero aktif.
// (1.0 / n) ** 1.5 dengan lantai 0.10000000000000001.
const double n = (double)((p_n_active < 0) ? 0 : p_n_active);
if (n <= 1.0) {
    return 1.0;
}
const double raw = std::pow(1.0 / n, 1.5);
return (raw < 0.10000000000000001) ? 0.10000000000000001 : raw;
}

double MysticMobile::fx_load_next(double p_current, double p_target) {

// perf.py:648 set_fx_load: _FX_LOAD += (target - _FX_LOAD) * _FX_LOAD_SMOOTH
return p_current + (p_target - p_current) * 0.40000000000000002;
}

Dictionary MysticMobile::fx_token_budgets(double p_load) {

// perf.py:623-629 _reset_fx_tokens — anggaran KERAS token spawn per frame
// (int() Python = trunc; load >= lantai sehingga selalu positif).
const double load = std::max(0.10000000000000001, p_load);
Dictionary out;
out[Variant(String("particles"))] = Variant(std::max(
    (int64_t)(int64_t)56, (int64_t)((double)(int64_t)140 * load)));
out[Variant(String("projectiles"))] = Variant(std::max(
    (int64_t)(int64_t)10, (int64_t)((double)(int64_t)18 * load)));
out[Variant(String("skill_projectiles"))] = Variant(std::max(
    (int64_t)(int64_t)5, (int64_t)((double)(int64_t)10 * load)));
return out;
}

String MysticMobile::auto_detect_quality(bool p_is_android) {

// perf.py:861-873 auto_detect_quality: Android mulai LOW (30 FPS stabil sejak
// detik pertama, pemain bisa naikkan di Settings), desktop HIGH.
if (!p_is_android) {
    return String("high");
}
return String("low");
}

Dictionary MysticMobile::adaptive_thresholds() {

// perf.py:882-891 AdaptiveQuality.__init__ (+ cooldown update).
Dictionary out;
    out[Variant(String("low_fps"))] = (int64_t)26;
    out[Variant(String("high_fps"))] = (int64_t)52;
    out[Variant(String("window"))] = (int64_t)90;
    out[Variant(String("cooldown_down"))] = (int64_t)180;
    out[Variant(String("cooldown_up"))] = (int64_t)300;
return out;
}

Dictionary MysticMobile::adaptive_quality_decision(const String & p_level, double p_avg, int64_t p_cooldown) {

// perf.py:890-911 AdaptiveQuality.update — keputusan SETELAH jendela sampel
// penuh; akumulasi sampel + jendela (90 frame) tetap di backend pemanggil.
Dictionary out;
if (p_cooldown > 0) {
    out[Variant(String("action"))] = Variant(String("wait"));
    out[Variant(String("new_level"))] = Variant(p_level);
    out[Variant(String("new_cooldown"))] = Variant(p_cooldown - 1);
    return out;
}
if (p_avg < (int64_t)26 && !(p_level == String("low"))) {
    // apply(LOW if Quality.level == MEDIUM else MEDIUM); cooldown = 180
    out[Variant(String("action"))] = Variant(String("down"));
    out[Variant(String("new_level"))] = Variant(
        String((p_level == String("medium")) ? "low" : "medium"));
    out[Variant(String("new_cooldown"))] = Variant((int64_t)(int64_t)180);
    return out;
}
if (p_avg > (int64_t)52 && !(p_level == String("high"))) {
    // apply(HIGH if Quality.level == MEDIUM else MEDIUM); cooldown = 300
    out[Variant(String("action"))] = Variant(String("up"));
    out[Variant(String("new_level"))] = Variant(
        String((p_level == String("medium")) ? "high" : "medium"));
    out[Variant(String("new_cooldown"))] = Variant((int64_t)(int64_t)300);
    return out;
}
out[Variant(String("action"))] = Variant(String("none"));
out[Variant(String("new_level"))] = Variant(p_level);
out[Variant(String("new_cooldown"))] = Variant((int64_t)0);
return out;
}

Vector2 MysticMobile::logical_size() {

// platform_utils.py:38-39 LOGICAL_WIDTH/HEIGHT.
return Vector2((float)1280, (float)720);
}

bool MysticMobile::detect_android(bool p_env_android_argument, bool p_env_android_private, bool p_has_getandroidapilevel) {

// platform_utils.py:45-52 _detect_android: python-for-android menyetel
// ANDROID_ARGUMENT/ANDROID_PRIVATE; CPython resmi punya
// sys.getandroidapilevel. Nilai env dikirim sebagai bool oleh backend.
if (p_env_android_argument) {
    return true;
}
if (p_env_android_private) {
    return true;
}
return p_has_getandroidapilevel;
}

bool MysticMobile::touch_mode(bool p_is_android, const String & p_force_touch_env) {

// platform_utils.py:60: TOUCH_MODE = IS_ANDROID or
// (os.environ.get("MYSTIC_FORCE_TOUCH", "0") == "1")
return p_is_android || p_force_touch_env == String("1");
}

Rect2 MysticMobile::safe_area(bool p_touch_mode) {

// platform_utils.py:616-622 get_safe_area — rect aman dari poni/gesture bar;
// tombol HUD ditaruh di dalam rect ini.
if (!p_touch_mode) {
    return Rect2(0.0f, 0.0f, (float)1280, (float)720);
}
const int64_t m = 28;
return Rect2((float)m, (float)10, (float)(1280 - 2 * m), (float)(720 - 20));
}

Dictionary MysticMobile::panel_zones() {

// platform_utils.py:504-505 ZONA_POPUP_Y/ZONA_BAWAH_H — pembagian jalur tetap
// panel kanan supaya isi tidak pernah saling menimpa.
Dictionary out;
    out[Variant(String("zona_popup_y"))] = (int64_t)430;
    out[Variant(String("zona_bawah_h"))] = (int64_t)120;
return out;
}

Variant MysticMobile::panel_popup_pos(bool p_has_panel, int64_t p_px, int64_t p_py, int64_t p_pw, int64_t p_ph, int64_t p_w, int64_t p_h, int64_t p_atas) {

// platform_utils.py:462-475 panel_popup_pos — posisi popup di dalam panel
// kanan, atau NIL kalau panel tidak ada / popup tidak muat. Pembagian pakai
// py_floordiv (`//` Python) supaya panel lebih pendek dari popup tetap persis.
if (!p_has_panel || p_w > p_pw - 8) {
    return Variant();
}
const int64_t x = p_px + py_floordiv(p_pw - p_w, 2);
const int64_t y = std::max(p_atas,
                           std::min(py_floordiv(p_ph - p_h, 2),
                                    p_ph - p_h - 12));
return Variant(Vector2((float)x, (float)y));
}

Variant MysticMobile::panel_pos_bawah(bool p_has_panel, int64_t p_px, int64_t p_py, int64_t p_pw, int64_t p_ph, int64_t p_w, int64_t p_h) {

// platform_utils.py:508-524 panel_pos_bawah — SLOT TETAP popup di jalur
// ZONA_POPUP_Y; kalau panel terlalu pendek, dorong ke atas seperlunya.
if (!p_has_panel || p_w > p_pw - 8) {
    return Variant();
}
const int64_t x = p_px + py_floordiv(p_pw - p_w, 2);
int64_t y = p_py + 430;
if (y + p_h > p_py + p_ph - 120) {
    y = std::max(p_py + 8, p_py + p_ph - 120 - p_h);
}
return Variant(Vector2((float)x, (float)y));
}

Vector2 MysticMobile::window_to_logical(double p_x, double p_y, double p_scale, double p_off_x, double p_off_y) {

// platform_utils.py:583-593 window_to_logical — piksel jendela -> logis
// 1280x720. Python `scale or 1.0`: 0.0/None dianggap 1.0.
const double s = (p_scale == 0.0) ? 1.0 : p_scale;
return Vector2((float)((p_x - p_off_x) / s),
               (float)((p_y - p_off_y) / s));
}

Vector2 MysticMobile::pointer_to_logical(int64_t p_mode, double p_x, double p_y, double p_scale, double p_off_x, double p_off_y) {

// platform_utils.py:564-580 pointer_to_logical — mode 0 = native: piksel
// jendela perlu dipetakan; mode lain (scaled_*): SDL sudah menerjemahkan,
// koordinat kembali sebagai double apa adanya.
if (p_mode == 0) {
    return window_to_logical(p_x, p_y, p_scale, p_off_x, p_off_y);
}
return Vector2((float)p_x, (float)p_y);
}

Array MysticMobile::debug_modes() {

// debug.py:24 _MODE_NAMES — OFF -> RINGKAS -> LENGKAP -> GRAFIK -> OFF.
Array out;
out.push_back(String("off"));
out.push_back(String("mini"));
out.push_back(String("full"));
out.push_back(String("graph"));
return out;
}

int64_t MysticMobile::debug_next_mode(int64_t p_mode) {

// debug.py:66-69 DebugOverlay.toggle: self.mode = (self.mode + 1) % 4
return (p_mode + 1) % 4;
}

int64_t MysticMobile::debug_wrap_mode(int64_t p_mode) {

// debug.py:71-72 DebugOverlay.set_mode: self.mode = mode % 4
return p_mode % 4;
}

bool MysticMobile::debug_is_enabled(int64_t p_mode) {

// debug.py:75-76 DebugOverlay.enabled: mode != MODE_OFF
return p_mode != (int64_t)0;
}

Color MysticMobile::fps_color(double p_fps) {

// debug.py:41-46 _color_for_fps: >= 50 OK, >= 30 WARN, selain itu BAD.
if (p_fps >= (int64_t)50) {
    return Color((float)120 / 255.0f, (float)235 / 255.0f, (float)140 / 255.0f, (float)255 / 255.0f);
}
if (p_fps >= (int64_t)30) {
    return Color((float)255 / 255.0f, (float)205 / 255.0f, (float)90 / 255.0f, (float)255 / 255.0f);
}
return Color((float)255 / 255.0f, (float)110 / 255.0f, (float)110 / 255.0f, (float)255 / 255.0f);
}

bool MysticMobile::debug_slow_frame(double p_frame_ms) {

// debug.py:87 DebugOverlay.update: if frame_ms > 33: _slow_frames += 1
return p_frame_ms > (int64_t)33;
}

String MysticMobile::perf_log_line(double p_fps, double p_avg_frame_ms, double p_upd_ms, double p_draw_ms, const String & p_quality, const String & p_entity_counts, const String & p_memory) {

// debug.py:95-102 DebugOverlay._log_line — baris log perf (stdout/logcat).
// Bagian numerik pakai snprintf %.1f (pembulatan benar atas nilai biner,
// glibc == CPython); bagian str digabung lewat String (API godot-cpp).
char buf[96];
snprintf(buf, sizeof(buf),
         "[PERF] fps=%.1f frame=%.1fms upd=%.1f draw=%.1f q=",
         p_fps, p_avg_frame_ms, p_upd_ms, p_draw_ms);
String out(buf);
out += p_quality;
out += String(" ent=");
out += p_entity_counts;
out += String(" mem=");
out += p_memory;
return out;
}

String MysticMobile::attack_sound_kind(double p_distance) {

// combat_audio.py:272-278 jenis_serangan: jarak >= AMBANG_RANGED (100) ->
// ranged, selain itu melee. `float(jarak or 0)`: 0 tetap 0.
return (p_distance >= (int64_t)100) ? String("hero_ranged") : String("hero_melee");
}

String MysticMobile::tower_sound_kind(const String & p_tower_type) {

// combat_audio.py:281-288 jenis_tower: pemetaan tipe menara -> jenis suara,
// default archer (dict.get(tower_type, TOWER_ARCHER)).
if (p_tower_type == String("cannon")) {
    return String("tower_cannon");
}
if (p_tower_type == String("ice")) {
    return String("tower_ice");
}
if (p_tower_type == String("mage")) {
    return String("tower_mage");
}
return String("tower_archer");
}

Array MysticMobile::sound_kinds() {

// combat_audio.py:38-44 konstanta jenis suara tempur.
Array out;
out.push_back(String("hero_melee"));
out.push_back(String("hero_ranged"));
out.push_back(String("tower_archer"));
out.push_back(String("tower_cannon"));
out.push_back(String("tower_ice"));
out.push_back(String("tower_mage"));
out.push_back(String("minion_hit"));
return out;
}

Dictionary MysticMobile::sound_config() {

// combat_audio.py:47-54 _KONFIG — jenis -> (volume dasar, jeda minimum ms,
// boleh rebut channel).
Dictionary out;
    {
        Array cfg;
        cfg.push_back(Variant(0.78000000000000003));
        cfg.push_back(Variant((int64_t)90));
        cfg.push_back(Variant(false));
        out[Variant(String("hero_melee"))] = Variant(cfg);
    }
    {
        Array cfg;
        cfg.push_back(Variant(0.71999999999999997));
        cfg.push_back(Variant((int64_t)90));
        cfg.push_back(Variant(false));
        out[Variant(String("hero_ranged"))] = Variant(cfg);
    }
    {
        Array cfg;
        cfg.push_back(Variant(0.62));
        cfg.push_back(Variant((int64_t)110));
        cfg.push_back(Variant(false));
        out[Variant(String("tower_archer"))] = Variant(cfg);
    }
    {
        Array cfg;
        cfg.push_back(Variant(0.62));
        cfg.push_back(Variant((int64_t)110));
        cfg.push_back(Variant(false));
        out[Variant(String("tower_cannon"))] = Variant(cfg);
    }
    {
        Array cfg;
        cfg.push_back(Variant(0.62));
        cfg.push_back(Variant((int64_t)110));
        cfg.push_back(Variant(false));
        out[Variant(String("tower_ice"))] = Variant(cfg);
    }
    {
        Array cfg;
        cfg.push_back(Variant(0.62));
        cfg.push_back(Variant((int64_t)110));
        cfg.push_back(Variant(false));
        out[Variant(String("tower_mage"))] = Variant(cfg);
    }
    {
        Array cfg;
        cfg.push_back(Variant(0.5));
        cfg.push_back(Variant((int64_t)140));
        cfg.push_back(Variant(false));
        out[Variant(String("minion_hit"))] = Variant(cfg);
    }
return out;
}

Dictionary MysticMobile::sound_patterns() {

// combat_audio.py:66-73 POLA — jenis -> pola nama berkas (fnmatch).
Dictionary out;
    {
        Array pats;
        pats.push_back(String("hero_melee"));
        pats.push_back(String("hero_melee_*"));
        out[Variant(String("hero_melee"))] = Variant(pats);
    }
    {
        Array pats;
        pats.push_back(String("hero_ranged"));
        pats.push_back(String("hero_ranged_*"));
        out[Variant(String("hero_ranged"))] = Variant(pats);
    }
    {
        Array pats;
        pats.push_back(String("tower_archer"));
        pats.push_back(String("tower_archer_*"));
        out[Variant(String("tower_archer"))] = Variant(pats);
    }
    {
        Array pats;
        pats.push_back(String("tower_cannon"));
        pats.push_back(String("tower_cannon_*"));
        out[Variant(String("tower_cannon"))] = Variant(pats);
    }
    {
        Array pats;
        pats.push_back(String("tower_ice"));
        pats.push_back(String("tower_ice_*"));
        out[Variant(String("tower_ice"))] = Variant(pats);
    }
    {
        Array pats;
        pats.push_back(String("tower_mage"));
        pats.push_back(String("tower_mage_*"));
        out[Variant(String("tower_mage"))] = Variant(pats);
    }
    {
        Array pats;
        pats.push_back(String("minion_hit"));
        pats.push_back(String("minion_hit_*"));
        out[Variant(String("minion_hit"))] = Variant(pats);
    }
return out;
}

int64_t MysticMobile::frame_sound_budget() {

// combat_audio.py:213 _sisa_frame = [4] — anggaran suara non-rebut per frame
// (new_frame() mengisi ulang tiap frame).
return (int64_t)4;
}

String MysticMobile::play_gate(double p_now_ms, double p_last_ms, int64_t p_jeda_ms, bool p_boleh_rebut, int64_t p_sisa_frame) {

// combat_audio.py:244-269 play() — gerbang urut: jeda per jenis lalu anggaran
// frame. Pencarian channel mixer + pemilihan berkas acak tetap di backend
// (mixer tidak ada di C++ murni). Default last_ms pygame = -99999.
if (p_now_ms - p_last_ms < (double)p_jeda_ms) {
    return String("tolak_jeda");
}
if (!p_boleh_rebut && p_sisa_frame <= 0) {
    return String("tolak_anggaran");
}
return String("main");
}

String MysticMobile::combat_stats_text(int64_t p_main, int64_t p_tolak_jeda, int64_t p_tolak_anggaran, int64_t p_tolak_channel) {

// combat_audio.py:308-313 ringkas() — format persis (dua spasi setelah main).
const int64_t total = p_tolak_jeda + p_tolak_anggaran + p_tolak_channel;
char buf[160];
snprintf(buf, sizeof(buf),
         "suara: main %lld  ditolak %lld (jeda %lld / anggaran %lld / "
         "kanal %lld)",
         (long long)p_main, (long long)total, (long long)p_tolak_jeda,
         (long long)p_tolak_anggaran, (long long)p_tolak_channel);
return String(buf);
}

Dictionary MysticMobile::cloud_constants() {

// cloud_save.py:47, 183-185 konstanta payload cloud.
Dictionary out;
    out[Variant(String("cloud_magic"))] = "MYSTIC_ARENA_CLOUD";
    out[Variant(String("cloud_version"))] = (int64_t)1;
    out[Variant(String("payload_magic"))] = "MYSTIC_ARENA_BACKUP";
    out[Variant(String("payload_version"))] = (int64_t)1;
    out[Variant(String("num_slots"))] = (int64_t)3;
    out[Variant(String("checksum_exempt_key"))] = "checksum";
return out;
}

String MysticMobile::payload_gate(bool p_is_dict, bool p_magic_ok, bool p_version_ok, int64_t p_version, bool p_slots_ok, bool p_checksum_ok) {

// cloud_save.py:260-285 parse_payload — urutan validasi + pesan persis.
// "File corrupt (not valid JSON)" ditangani backend pemanggil (hasil parser
// JSON); checksum dihitung engine-side (canonical JSON + sha256);
// version_ok = False untuk payload yang int(version) -nya gagal (Python
// except -> "File corrupt (bad version)").
if (!p_is_dict) {
    return String("File corrupt (unexpected structure)");
}
if (!p_magic_ok) {
    return String("Not a Mystic Arena save file");
}
if (!p_version_ok) {
    return String("File corrupt (bad version)");
}
if (p_version < 1 || p_version > (int64_t)1) {
    char buf[96];
    snprintf(buf, sizeof(buf), "Save version %lld not supported",
             (long long)p_version);
    return String(buf);
}
if (!p_slots_ok) {
    return String("Save contains no data");
}
if (!p_checksum_ok) {
    return String("File corrupt (checksum mismatch)");
}
return String();
}

Dictionary MysticMobile::payload_summary(const Array & p_slots, double p_exported_at) {

// cloud_save.py:288-322 get_payload_summary — level tertinggi, gold terbanyak,
// timestamp terbaru. exported_at_str (strftime localtime) tetap di backend.
// try/except per slot direplikasi: kesalahan di tengah slot MENGHENTIKAN
// sisa baris slot itu (hasil sebagian tetap berlaku), lalu lanjut slot
// berikutnya. int()/float() Python atas string angka direplikasi
// (py_int_of/py_float_of); string non-angka = exception -> lewati sisa slot.
// Python max(0, x) mempertahankan tipe operand yang menang, jadi level
// tertinggi dilacak per tipe (int dari JSON save; float kalau ada fraksi).
int64_t highest_i = 0;
double highest_f = 0.0;
bool highest_is_float = false;
int64_t best_gold = 0;
double newest_played = 0.0;
for (int64_t i = 0; i < p_slots.size(); i++) {
    const Variant slot_v = p_slots.get(i);
    Dictionary data = slot_v;  // operator Dictionary; non-dict -> kosong
    // completed = data.get("completed_levels", []) or []
    const Variant completed = data.get(Variant(String("completed_levels")),
                                       Variant(Array()));
    if (bool(completed)) {
        // Python: max(completed) — truthy non-list ATAU elemen non-angka
        // melempar exception -> lewati sisa slot.
        const Array completed_arr = completed;
        bool skip_rest = false;
        double local_max = 0.0;
        bool local_is_float = false;
        bool first = true;
        if (completed.get_type() != Variant::ARRAY) {
            skip_rest = true;  // max(str) -> max(int, str) TypeError
        }
        for (int64_t j = 0; !skip_rest && j < completed_arr.size(); j++) {
            const Variant item = completed_arr.get(j);
            const Variant::Type it = item.get_type();
            if (it != Variant::INT && it != Variant::FLOAT &&
                    it != Variant::BOOL) {
                skip_rest = true;  // TypeError di max()
                break;
            }
            // max() Python atomik: max parsial TIDAK boleh menyentuh
            // highest sebelum seluruh list lolos (commit di bawah).
            const double v = (it == Variant::FLOAT)
                                 ? (double)item
                                 : (double)(int64_t)item;
            if (first || v > local_max) {
                local_max = v;
                local_is_float = (it == Variant::FLOAT);
                first = false;
            }
        }
        if (skip_rest) {
            continue;
        }
        if (!first) {
            const double cur =
                    highest_is_float ? highest_f : (double)highest_i;
            if (local_max > cur) {
                if (local_is_float) {
                    highest_f = local_max;
                    highest_is_float = true;
                } else {
                    highest_i = (int64_t)local_max;
                    highest_is_float = false;
                }
            }
        }
    }
    // best_gold = max(best_gold, int(data.get("meta_gold", 0)))
    const Variant gold = data.get(Variant(String("meta_gold")),
                                  Variant((int64_t)0));
    bool gold_ok = true;
    int64_t gold_int = 0;
    const Variant::Type gt = gold.get_type();
    if (gt == Variant::INT) {
        gold_int = (int64_t)gold;
    } else if (gt == Variant::BOOL) {
        gold_int = bool(gold) ? 1 : 0;
    } else if (gt == Variant::FLOAT) {
        gold_int = (int64_t)gold;  // int(): trunc ke arah nol
    } else if (gt == Variant::STRING) {
        gold_ok = py_int_of_string(gold, gold_int);  // int("12") / gagal lain
    } else {
        gold_ok = false;  // TypeError -> lewati sisa slot
    }
    if (!gold_ok) {
        continue;
    }
    if (gold_int > best_gold) {
        best_gold = gold_int;
    }
    // newest_played = max(..., float(data.get("slot_last_played", 0) or 0))
    Variant played = data.get(Variant(String("slot_last_played")),
                              Variant((int64_t)0));
    if (!bool(played)) {
        played = Variant((int64_t)0);  // `or 0`: falsy -> 0
    }
    bool played_ok = true;
    double played_f = 0.0;
    const Variant::Type pt = played.get_type();
    if (pt == Variant::INT) {
        played_f = (double)(int64_t)played;
    } else if (pt == Variant::BOOL) {
        played_f = bool(played) ? 1.0 : 0.0;
    } else if (pt == Variant::FLOAT) {
        played_f = (double)played;
    } else if (pt == Variant::STRING) {
        played_ok = py_float_of_string(played, played_f);
    } else {
        played_ok = false;
    }
    if (!played_ok) {
        continue;
    }
    if (played_f > newest_played) {
        newest_played = played_f;
    }
}
Dictionary out;
out[Variant(String("highest_level"))] =
        highest_is_float ? Variant(highest_f) : Variant(highest_i);
out[Variant(String("meta_gold"))] = Variant(best_gold);
out[Variant(String("slot_count"))] = Variant((int64_t)p_slots.size());
out[Variant(String("exported_at"))] = Variant(p_exported_at);
out[Variant(String("newest_played"))] = Variant(newest_played);
return out;
}

bool MysticMobile::py_int_of_string(const String & p_text, int64_t & p_out) {

// int(str) Python: strip whitespace, tanda opsional, digit saja.
std::string s = p_text.utf8().get_data();
size_t i = 0;
while (i < s.size() && std::isspace((unsigned char)s[i])) {
    i++;
}
size_t j = s.size();
while (j > i && std::isspace((unsigned char)s[j - 1])) {
    j--;
}
bool neg = false;
if (i < j && (s[i] == '+' || s[i] == '-')) {
    neg = s[i] == '-';
    i++;
}
if (i >= j) {
    return false;
}
int64_t value = 0;
for (size_t k = i; k < j; k++) {
    if (s[k] < '0' || s[k] > '9') {
        return false;
    }
    value = value * 10 + (s[k] - '0');
}
p_out = neg ? -value : value;
return true;
}

bool MysticMobile::py_float_of_string(const String & p_text, double & p_out) {

// float(str) Python (subset JSON-ish): strip whitespace, tanda opsional,
// digit + opsional '.' digit + opsional eksponen e/E.
std::string s = p_text.utf8().get_data();
size_t i = 0;
while (i < s.size() && std::isspace((unsigned char)s[i])) {
    i++;
}
size_t j = s.size();
while (j > i && std::isspace((unsigned char)s[j - 1])) {
    j--;
}
std::string body = s.substr(i, j - i);
if (body.empty()) {
    return false;
}
char *endp = nullptr;
const double value = strtod(body.c_str(), &endp);
if (endp != body.c_str() + body.size()) {
    return false;
}
p_out = value;
return true;
}

Dictionary MysticMobile::build_constants() {

// buildinfo.py:13-14 penanda build.
Dictionary out;
    out[Variant(String("build_id"))] = "v35-skema-final";
    out[Variant(String("build_date"))] = "2026-08-22";
return out;
}

Array MysticMobile::build_key_files() {

// buildinfo.py:16-22 _KEY_FILES — berkas kunci fingerprint.
Array out;
out.push_back(String("_core.py"));
out.push_back(String("_render.py"));
out.push_back(String("splash_screen.py"));
out.push_back(String("main.py"));
out.push_back(String("mobile/perf.py"));
out.push_back(String("mobile/blitwatch.py"));
out.push_back(String("mobile/bootcheck.py"));
out.push_back(String("ui_components/_bundle.py"));
return out;
}

String MysticMobile::fingerprint_text(int64_t p_total_bytes, int64_t p_found) {

// buildinfo.py:23-37 fingerprint: "%05X/%d" % (total % 0x100000, found)
char buf[64];
snprintf(buf, sizeof(buf), "%05X/%d",
         (unsigned long long)(p_total_bytes % 0x100000),
         (long long)p_found);
return String(buf);
}

String MysticMobile::build_label(const String & p_build_id, const String & p_build_date, const String & p_fingerprint) {

// buildinfo.py:40-41 label(): "BUILD %s (%s) fp=%s"
String out("BUILD ");
out += p_build_id;
out += String(" (");
out += p_build_date;
out += String(") fp=");
out += p_fingerprint;
return out;
}

void MysticMobile::_bind_methods() {
    ClassDB::bind_static_method("MysticMobile", D_METHOD("module_names"), &MysticMobile::module_names);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("module_names_string"), &MysticMobile::module_names_string);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("api_signature"), &MysticMobile::api_signature);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("touch_constants"), &MysticMobile::touch_constants);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("motion_velocity", "prev_velocity", "dy"), &MysticMobile::motion_velocity);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("motion_exceeds_slop", "total_dist"), &MysticMobile::motion_exceeds_slop);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("scroll_notch", "accum"), &MysticMobile::scroll_notch);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("tap_is_double", "dt_ms", "dx", "dy"), &MysticMobile::tap_is_double);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("release_is_fling", "moved", "velocity"), &MysticMobile::release_is_fling);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("fling_steps", "velocity"), &MysticMobile::fling_steps);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("fling_direction", "velocity"), &MysticMobile::fling_direction);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("fling_decay", "velocity"), &MysticMobile::fling_decay);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("fling_active", "velocity"), &MysticMobile::fling_active);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("long_press_due", "held_ms"), &MysticMobile::long_press_due);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("dispatch_button", "kind", "value"), &MysticMobile::dispatch_button);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("hud_min_tap"), &MysticMobile::hud_min_tap);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("hud_button_rects", "safe_left", "safe_top", "safe_right", "safe_bottom"), &MysticMobile::hud_button_rects);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("hud_hit_rect", "rect"), &MysticMobile::hud_hit_rect);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("hud_button_contains", "visible", "hit_rect", "pos"), &MysticMobile::hud_button_contains);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("hud_visibility", "playing", "ended", "victory", "has_next_level", "cinematic_active", "panel_ada", "show_debug_button"), &MysticMobile::hud_visibility);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("hud_press_anim_next", "press_anim"), &MysticMobile::hud_press_anim_next);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("hud_colors"), &MysticMobile::hud_colors);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("hud_skill_labels"), &MysticMobile::hud_skill_labels);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("hud_skill_names"), &MysticMobile::hud_skill_names);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("tactical_actions"), &MysticMobile::tactical_actions);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("quality_levels"), &MysticMobile::quality_levels);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("quality_preset", "level"), &MysticMobile::quality_preset);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("quality_defaults"), &MysticMobile::quality_defaults);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("particle_ratio_effective", "base_ratio", "fx_load"), &MysticMobile::particle_ratio_effective);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("fx_load_target", "n_active"), &MysticMobile::fx_load_target);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("fx_load_next", "current", "target"), &MysticMobile::fx_load_next);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("fx_token_budgets", "load"), &MysticMobile::fx_token_budgets);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("auto_detect_quality", "is_android"), &MysticMobile::auto_detect_quality);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("adaptive_thresholds"), &MysticMobile::adaptive_thresholds);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("adaptive_quality_decision", "level", "avg", "cooldown"), &MysticMobile::adaptive_quality_decision);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("logical_size"), &MysticMobile::logical_size);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("detect_android", "env_android_argument", "env_android_private", "has_getandroidapilevel"), &MysticMobile::detect_android);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("touch_mode", "is_android", "force_touch_env"), &MysticMobile::touch_mode);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("safe_area", "touch_mode"), &MysticMobile::safe_area);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("panel_zones"), &MysticMobile::panel_zones);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("panel_popup_pos", "has_panel", "px", "py", "pw", "ph", "w", "h", "atas"), &MysticMobile::panel_popup_pos);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("panel_pos_bawah", "has_panel", "px", "py", "pw", "ph", "w", "h"), &MysticMobile::panel_pos_bawah);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("window_to_logical", "x", "y", "scale", "off_x", "off_y"), &MysticMobile::window_to_logical);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("pointer_to_logical", "mode", "x", "y", "scale", "off_x", "off_y"), &MysticMobile::pointer_to_logical);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("debug_modes"), &MysticMobile::debug_modes);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("debug_next_mode", "mode"), &MysticMobile::debug_next_mode);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("debug_wrap_mode", "mode"), &MysticMobile::debug_wrap_mode);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("debug_is_enabled", "mode"), &MysticMobile::debug_is_enabled);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("fps_color", "fps"), &MysticMobile::fps_color);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("debug_slow_frame", "frame_ms"), &MysticMobile::debug_slow_frame);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("perf_log_line", "fps", "avg_frame_ms", "upd_ms", "draw_ms", "quality", "entity_counts", "memory"), &MysticMobile::perf_log_line);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("attack_sound_kind", "distance"), &MysticMobile::attack_sound_kind);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("tower_sound_kind", "tower_type"), &MysticMobile::tower_sound_kind);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("sound_kinds"), &MysticMobile::sound_kinds);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("sound_config"), &MysticMobile::sound_config);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("sound_patterns"), &MysticMobile::sound_patterns);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("frame_sound_budget"), &MysticMobile::frame_sound_budget);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("play_gate", "now_ms", "last_ms", "jeda_ms", "boleh_rebut", "sisa_frame"), &MysticMobile::play_gate);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("combat_stats_text", "main", "tolak_jeda", "tolak_anggaran", "tolak_channel"), &MysticMobile::combat_stats_text);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("cloud_constants"), &MysticMobile::cloud_constants);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("payload_gate", "is_dict", "magic_ok", "version_ok", "version", "slots_ok", "checksum_ok"), &MysticMobile::payload_gate);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("payload_summary", "slots", "exported_at"), &MysticMobile::payload_summary);


    ClassDB::bind_static_method("MysticMobile", D_METHOD("build_constants"), &MysticMobile::build_constants);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("build_key_files"), &MysticMobile::build_key_files);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("fingerprint_text", "total_bytes", "found"), &MysticMobile::fingerprint_text);
    ClassDB::bind_static_method("MysticMobile", D_METHOD("build_label", "build_id", "build_date", "fingerprint"), &MysticMobile::build_label);
}

} // namespace godot
