#include "splash_processor.h"

#include <godot_cpp/core/class_db.hpp>

#include <cmath>

// ═══ GENERATED — JANGAN SUNTING TANGAN ═══
// Sumber    : splash_screen.py
// Generator : tools/gen_splash_cpp.py
// Regenerasi: python3 tools/gen_splash_cpp.py
// Cek CI    : python3 tools/gen_splash_cpp.py --check
//
// Setiap fungsi menyebut baris sumber Python yang direplikasi. Angka yang
// diekstrak generator datang dari AST (bukan salinan tangan); perilakunya
// dikunci oracle pygame + self-test tanpa engine.

namespace godot {

// Replika round() CPython: half-to-even (round(2.5) == 2, round(-2.5) == -2).
// Dipakai kuantisasi tumbuh logo: round((0.85 + 0.15*grow) * 20) / 20.0.
int64_t MysticSplash::py_round(double value) {
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

// Replika int() CPython: trunc ke arah nol (bukan floor, bukan round).
// Dipakai SEMUA kanal warna/alpha/koordinat splash: int(255 * min(...)),
// int(ch * (0.35 + 0.65*tw)), int(140 * a), int(alpha * 0.28), int(x).
int64_t MysticSplash::py_int(double value) {
    return (int64_t)value;
}

// Daftar modul sumber splash (urutan bundle) — oracle memakai daftar ini untuk audit closed-world.
Array MysticSplash::module_names() {

    Array out;
    out.push_back(String("splash_screen"));
    return out;
}

// Gabungan module_names() dengan koma (untuk cap jari + log).
String MysticSplash::module_names_string() {

    Array names = module_names();
    String out;
    for (int64_t i = 0; i < names.size(); i++) {
        if (i > 0) {
            out += String(",");
        }
        out += (String)names[i];
    }
    return out;
}

// Cap jari API: jumlah modul + fungsi (dipakai loader membuktikan backend C++ benar-benar jalan, dicetak sekali per perubahan backend).
String MysticSplash::api_signature() {

    return String("splash_v1:1mod:62fn:");
}

// GAME_NAME (splash_screen.py:22).
String MysticSplash::game_name() {

    return String("MYSTIC ARENA");
}

// Tagline di bawah judul (_draw_logo_or_title baris 257).
String MysticSplash::tagline() {

    return String("A MOBA TOWER DEFENSE ADVENTURE");
}

// Teks hint skip (draw baris 178).
String MysticSplash::hint_text() {

    return String("Tap anywhere to skip");
}

// SPLASH_DURATION (splash_screen.py:23) — detik sebelum auto-pindah.
double MysticSplash::splash_duration() {

    return 3.0;
}

// LOGO_PATHS (splash_screen.py:24) — urutan pencarian file logo.
Array MysticSplash::logo_paths() {
    Array out;
    out.push_back(String("assets/logo.png"));
    out.push_back(String("assets/splash_logo.png"));
    out.push_back(String("assets/logo.jpg"));
    out.push_back(String("assets/logo.jpeg"));
    return out;
}

// ACCENT (splash_screen.py:32) = (255, 190, 60).
Color MysticSplash::accent() {

    return Color(255.0f / 255.0f, 190.0f / 255.0f, 60.0f / 255.0f);
}

// ACCENT_2 (splash_screen.py:33) = (200, 140, 255).
Color MysticSplash::accent_2() {

    return Color(200.0f / 255.0f, 140.0f / 255.0f, 255.0f / 255.0f);
}

// TEXT_MAIN (splash_screen.py:34) = (245, 240, 230).
Color MysticSplash::text_main() {

    return Color(245.0f / 255.0f, 240.0f / 255.0f, 230.0f / 255.0f);
}

// TEXT_DIM (splash_screen.py:35) = (160, 155, 170).
Color MysticSplash::text_dim() {

    return Color(160.0f / 255.0f, 155.0f / 255.0f, 170.0f / 255.0f);
}

// Tiga stop gradien latar (draw baris 178): top/mid/bot.
Dictionary MysticSplash::gradient_stops() {

    Dictionary out;
    out["top"] = Color(8.0f / 255.0f, 8.0f / 255.0f, 18.0f / 255.0f);
    out["mid"] = Color(22.0f / 255.0f, 16.0f / 255.0f, 38.0f / 255.0f);
    out["bot"] = Color(6.0f / 255.0f, 6.0f / 255.0f, 14.0f / 255.0f);
    return out;
}

// Palet warna partikel (_make_particles baris 115), urutan choice.
Array MysticSplash::particle_colors() {
    Array out;
    out.push_back(Color(255.0f / 255.0f, 210.0f / 255.0f, 120.0f / 255.0f));
    out.push_back(Color(230.0f / 255.0f, 160.0f / 255.0f, 255.0f / 255.0f));
    out.push_back(Color(255.0f / 255.0f, 245.0f / 255.0f, 230.0f / 255.0f));
    out.push_back(Color(180.0f / 255.0f, 200.0f / 255.0f, 255.0f / 255.0f));
    return out;
}

// Ukuran font utama (_init_fonts baris 69): presents=body_bold, title/title_below=Cinzel, sub=body_semibold, hint=body_medium.
Dictionary MysticSplash::font_sizes() {
    Dictionary out;
    out["presents"] = (int64_t)34;
    out["title"] = (int64_t)92;
    out["title_below"] = (int64_t)66;
    out["sub"] = (int64_t)22;
    out["hint"] = (int64_t)16;
    return out;
}

// Ukuran font fallback pygame (_init_fonts baris 69).
Dictionary MysticSplash::font_fallback_sizes() {
    Dictionary out;
    out["presents"] = (int64_t)40;
    out["title"] = (int64_t)110;
    out["title_below"] = (int64_t)80;
    out["sub"] = (int64_t)26;
    out["hint"] = (int64_t)18;
    return out;
}

// Gaya font per peran (_init_fonts baris 69): body_bold / body_semibold / body_medium; title memakai Cinzel.
Dictionary MysticSplash::font_styles() {

    Dictionary out;
    out["presents"] = String("body_bold");
    out["title"] = String("title");
    out["title_below"] = String("title");
    out["sub"] = String("body_semibold");
    out["hint"] = String("body_medium");
    return out;
}

// Jumlah partikel latar (__init__ baris 55: _make_particles(46)).
int64_t MysticSplash::particle_count() {

    return 46;
}

// Rentang random.uniform per kunci partikel (_make_particles baris 111). x/y memakai ukuran layar, phase memakai math.tau.
Dictionary MysticSplash::particle_ranges() {
    Dictionary out;
    out["r_lo"] = 0.6;
    out["r_hi"] = 2.4;
    out["speed_lo"] = 0.08;
    out["speed_hi"] = 0.35;
    out["drift_lo"] = -0.12;
    out["drift_hi"] = 0.12;
    out["phase_lo"] = 0;
    out["phase_hi"] = 6.283185307179586;
    out["phase_hi"] = M_PI * 2.0;
    return out;
}

// Satu langkah gerak partikel (update baris 136): y -= speed; x += drift + sin(elapsed*0.8 + phase)*0.05. Mengembalikan posisi BARU (double, BUKAN Vector2 — komponen Vector2 Godot float32 akan memangkas presisi stream partikel).
Dictionary MysticSplash::particle_move(double x, double y, double speed, double drift, double phase, double elapsed) {

    Dictionary out;
    out["y"] = y - speed;
    out["x"] = x + drift + std::sin(elapsed * 0.8 + phase) * 0.05;
    return out;
}

// Predikat wrap vertikal (update baris 136: p["y"] < -6).
bool MysticSplash::particle_wrapped(double y) {

    return y < -6.0;
}

// Nilai y sesudah wrap (update baris 136: self.h + 6).
double MysticSplash::particle_wrap_y(double screen_h) {

    return screen_h + 6.0;
}

// Langkah partikel LENGKAP (update baris 136): gerak + wrap; x baru sesudah wrap diserahkan pemanggil (RNG pygame global tak ber-seed, jadi tidak ada stream yang bisa direplika).
Dictionary MysticSplash::particle_advance(double x, double y, double speed, double drift, double phase, double elapsed, double screen_h, double respawn_x) {

    Dictionary moved = particle_move(x, y, speed, drift, phase, elapsed);
    double nx = (double)moved["x"];
    double ny = (double)moved["y"];
    bool wrapped = particle_wrapped(ny);
    if (wrapped) {
        ny = particle_wrap_y(screen_h);
        nx = respawn_x;
    }
    Dictionary out;
    out["x"] = nx;
    out["y"] = ny;
    out["wrapped"] = wrapped;
    return out;
}

// Faktor kelip partikel (draw baris 178): 0.5 + 0.5*sin(elapsed*2.5 + phase).
double MysticSplash::particle_twinkle(double elapsed, double phase) {

    return 0.5 + 0.5 * std::sin(elapsed * 2.5 + phase);
}

// Satu kanal warna partikel (draw baris 178): int(ch * (0.35 + 0.65*tw)) — trunc int() Python, bukan round.
int64_t MysticSplash::particle_channel(int64_t channel, double twinkle) {

    return py_int((double)channel * (0.35 + 0.65 * twinkle));
}

// Warna gambar partikel (draw baris 178) — ketiga kanal di-trunc.
Color MysticSplash::particle_draw_color(const Color & base, double twinkle) {

    double factor = 0.35 + 0.65 * twinkle;
    return Color((double)py_int((double)base.get_r8() * factor) / 255.0,
                 (double)py_int((double)base.get_g8() * factor) / 255.0,
                 (double)py_int((double)base.get_b8() * factor) / 255.0);
}

// Radius gambar partikel (draw baris 178): max(1, int(r)) — trunc.
int64_t MysticSplash::particle_draw_radius(double r) {

    int64_t radius = py_int(r);
    return radius > 1 ? radius : 1;
}

// Posisi gambar partikel (draw baris 178): (int(x), int(y)) — trunc.
Vector2 MysticSplash::particle_draw_pos(double x, double y) {

    return Vector2((double)py_int(x), (double)py_int(y));
}

// Kurva fade in (_overall_alpha baris 167): min(1, t/0.4).
double MysticSplash::fade_in(double t) {

    double v = t / 0.4;
    return v < 1.0 ? v : 1.0;
}

// Kurva fade out normal (_overall_alpha baris 167): clamp((dur - t)/0.45, 0, 1).
double MysticSplash::fade_out_normal(double t) {

    double v = (3.0 - t) / 0.45;
    if (v < 0.0) {
        return 0.0;
    }
    return v < 1.0 ? v : 1.0;
}

// Kurva fade out saat skip (_overall_alpha baris 167): max(0, 1 - t/0.25). Python memakai t = elapsed TOTAL (bukan sejak skip) — lihat overall_alpha vs overall_alpha_godot.
double MysticSplash::fade_out_skip(double t) {

    double v = 1.0 - t / 0.25;
    return v < 0.0 ? 0.0 : v;
}

// Alpha keseluruhan SEMANTIK PYGAME (_overall_alpha baris 167): fade_in(t) * (skipped ? fade_out_skip(t) : fade_out_normal(t)). Perhatikan: cabang skip memakai elapsed TOTAL, jadi skip sesudah 0.25 dtk langsung menghasilkan alpha 0 (fade tidak terlihat).
double MysticSplash::overall_alpha(double t, bool skipped) {

    double out = fade_in(t);
    if (skipped) {
        out *= fade_out_skip(t);
    } else {
        out *= fade_out_normal(t);
    }
    if (out < 0.0) {
        return 0.0;
    }
    return out < 1.0 ? out : 1.0;
}

// Alpha keseluruhan SEMANTIK PORT GODOT: sama dengan overall_alpha tapi cabang skip memakai `skip_t` (detik sejak skip) — deviasi SplashScreen.gd yang DITUTUP FASE 38 untuk fade, dipertahankan di sini hanya sebagai pembanding A/B harness.
double MysticSplash::overall_alpha_godot(double t, bool skipped, double skip_t) {

    double out = fade_in(t);
    if (skipped) {
        out *= fade_out_skip(skip_t);
    } else {
        out *= fade_out_normal(t);
    }
    if (out < 0.0) {
        return 0.0;
    }
    return out < 1.0 ? out : 1.0;
}

// Alpha judul (update baris 136): 0 sebelum 0.5 dtk, lalu int(255 * min(1, (t-0.5)/0.6)) — trunc int() Python.
int64_t MysticSplash::title_alpha(double t) {

    if (t < 0.5) {
        return 0;
    }
    double v = (t - 0.5) / 0.6;
    if (v > 1.0) {
        v = 1.0;
    }
    return py_int((double)255 * v);
}

// Predikat selesai SEMANTIK PYGAME (update baris 136): skipped ? elapsed >= 0.25 : elapsed >= dur — lagi-lagi elapsed TOTAL.
bool MysticSplash::is_done(double t, bool skipped) {

    if (skipped) {
        return t >= 0.25;
    }
    return t >= 3.0;
}

// Predikat selesai SEMANTIK PORT GODOT: cabang skip memakai skip_t (detik sejak skip). Deviasi SplashScreen.gd pra-FASE 38.
bool MysticSplash::is_done_godot(double t, bool skipped, double skip_t) {

    if (skipped) {
        return skip_t >= 0.25;
    }
    return t >= 3.0;
}

// Gerbang draw (draw baris 178): alpha > 0.001.
bool MysticSplash::draw_visible(double alpha) {

    return alpha > 0.001;
}

// Alpha judul SESUDAH dikalikan alpha keseluruhan (_draw_logo_or_title baris 257): int(title_alpha * a) — trunc.
int64_t MysticSplash::title_alpha_drawn(int64_t title_alpha, double overall) {

    return py_int((double)title_alpha * overall);
}

// Seluruh konstanta waktu/alpha splash dalam satu Dictionary (untuk log + fixture): durasi, kurva fade, ambang judul, kuantisasi tumbuh, epsilon draw.
Dictionary MysticSplash::timings() {

    Dictionary out;
    out["duration"] = 3.0;
    out["fade_in"] = 0.4;
    out["fade_out"] = 0.45;
    out["skip_fade"] = 0.25;
    out["skip_done"] = 0.25;
    out["title_delay"] = 0.5;
    out["title_ramp"] = 0.6;
    out["title_max"] = (int64_t)255;
    out["grow_time"] = 0.9;
    out["alpha_epsilon"] = 0.001;
    return out;
}

// Tinggi satu batang gradien (draw baris 178): max(1, h // 48).
int64_t MysticSplash::bg_step_h(int64_t screen_h) {

    int64_t step = screen_h / 48;
    return step > 1 ? step : 1;
}

// Jumlah batang gradien (draw baris 178): len(range(0, h, step_h)).
int64_t MysticSplash::bg_band_count(int64_t screen_h) {

    int64_t step = bg_step_h(screen_h);
    return (screen_h + step - 1) / step;
}

// Rect satu batang gradien (draw baris 178): (0, i, w, step_h).
Rect2 MysticSplash::bg_band_rect(int64_t i, int64_t step_h, int64_t screen_w) {

    return Rect2((double)0, (double)i, (double)screen_w, (double)step_h);
}

// Warna satu batang gradien (draw baris 178): f = i/h; dua segmen lerp top->mid (f<0.55) lalu mid->bot, kanal di-trunc int() Python.
Color MysticSplash::bg_band_color(int64_t i, int64_t screen_h) {

    double f = (double)i / (double)screen_h;
    int64_t top[3] = {8, 8, 18};
    int64_t mid[3] = {22, 16, 38};
    int64_t bot[3] = {6, 6, 14};
    double f2;
    const int64_t *from;
    const int64_t *to;
    if (f < 0.55) {
        f2 = f / 0.55;
        from = top;
        to = mid;
    } else {
        f2 = (f - 0.55) / 0.45;
        from = mid;
        to = bot;
    }
    return Color((double)py_int((double)from[0]
                    + ((double)to[0] - (double)from[0]) * f2) / 255.0,
                 (double)py_int((double)from[1]
                    + ((double)to[1] - (double)from[1]) * f2) / 255.0,
                 (double)py_int((double)from[2]
                    + ((double)to[2] - (double)from[2]) * f2) / 255.0);
}

// SELURUH batang gradien (rect + warna) untuk satu ukuran layar — dipakai renderer Godot memanggang latar SEKALI (paritas _bg_cache pygame, draw baris 178).
Array MysticSplash::bg_bands(int64_t screen_w, int64_t screen_h) {

    Array out;
    int64_t step = bg_step_h(screen_h);
    for (int64_t i = 0; i < screen_h; i += step) {
        Dictionary row;
        row["rect"] = bg_band_rect(i, step, screen_w);
        row["color"] = bg_band_color(i, screen_h);
        out.push_back(row);
    }
    return out;
}

// SELURUH bingkai vignette (draw baris 178): i dari 140 turun 2; alpha = min(255, int(2.2*(140-i))) lalu rect (i, i, w-2i, h-2i). Bingkai TERAKHIR (i=4..2) ber-alpha 255 sehingga interior latar pygame hitam pekat — perilaku yang dulu hilang di port Godot.
Array MysticSplash::vignette_frames(int64_t screen_w, int64_t screen_h) {

    Array out;
    for (int64_t i = 140; i > 0; i += -2) {
        int64_t alpha = py_int(2.2 * (double)(140 - i));
        if (alpha > 255) {
            alpha = 255;
        }
        Dictionary row;
        row["rect"] = Rect2((double)i, (double)i,
                            (double)(screen_w - 2 * i),
                            (double)(screen_h - 2 * i));
        row["alpha"] = alpha;
        out.push_back(row);
    }
    return out;
}

// Jangkar konten (draw baris 178): (w // 2, h // 2).
Vector2 MysticSplash::content_center(int64_t screen_w, int64_t screen_h) {

    return Vector2((double)(screen_w / 2), (double)(screen_h / 2));
}

// Titik tengah logo (draw baris 178): base_y - (26 kalau ada logo).
double MysticSplash::logo_center_y(double base_y, bool has_logo) {

    return has_logo ? base_y - 26 : base_y;
}

// Skala logo (baris 257): min(340/w, 320/h, 1.0).
double MysticSplash::logo_scale(int64_t img_w, int64_t img_h) {

    double s = 340.0 / (double)img_w;
    double h = 320.0 / (double)img_h;
    if (h < s) {
        s = h;
    }
    return s < 1.0 ? s : 1.0;
}

// Ukuran dasar logo sesudah skala (baris 257): max(1, int(dim*scale)).
Vector2 MysticSplash::logo_base_size(int64_t img_w, int64_t img_h) {

    double s = logo_scale(img_w, img_h);
    int64_t w = py_int((double)img_w * s);
    int64_t h = py_int((double)img_h * s);
    return Vector2((double)(w > 1 ? w : 1), (double)(h > 1 ? h : 1));
}

// Kuantisasi tumbuh logo (baris 257): round((0.85 + 0.15*grow) * 20) / 20 — round() CPython half-to-even, supaya animasi tumbuh hanya memakai sedikit ukuran tekstur (cache).
double MysticSplash::logo_grow_quant(double elapsed) {

    double grow = elapsed / 0.9;
    if (grow > 1.0) {
        grow = 1.0;
    }
    double raw = (0.85 + 0.15 * grow) * 20;
    return (double)py_round(raw) / (double)20;
}

// Ukuran logo pada kuantisasi tumbuh (baris 257): max(1, int(dim*gq)).
Vector2 MysticSplash::logo_grow_size(const Vector2 & base, double gq) {

    int64_t w = py_int((double)base.x * gq);
    int64_t h = py_int((double)base.y * gq);
    return Vector2((double)(w > 1 ? w : 1), (double)(h > 1 ? h : 1));
}

// Radius glow emas di belakang logo (baris 257): max(ww, hh) // 2 + 30.
int64_t MysticSplash::logo_glow_radius(int64_t ww, int64_t hh) {

    int64_t m = ww > hh ? ww : hh;
    return m / 2 + 30;
}

// Rect glow logo (baris %d): persegi 2*glow_r berpusat (cx, cy).
Rect2 MysticSplash::logo_glow_rect(double cx, double cy, int64_t glow_r) {

    return Rect2(cx - (double)glow_r, cy - (double)glow_r,
                 (double)(glow_r * 2), (double)(glow_r * 2));
}

// Cincin glow logo (baris 257): g dari glow_r turun -3; alpha = int(12 * (1 - g/glow_r)) — trunc.
Array MysticSplash::logo_glow_rings(int64_t glow_r) {

    Array out;
    for (int64_t g = glow_r; g > 0; g += -3) {
        Dictionary row;
        row["r"] = g;
        row["alpha"] = py_int((double)12
                              * (1.0 - (double)g / (double)glow_r));
        out.push_back(row);
    }
    return out;
}

// Offset vertikal teks cabang logo vs cabang teks-saja (baris 257): judul rect.bottom+46, tagline rect.bottom+88, tagline cabang teks base_y+66.
Dictionary MysticSplash::logo_offsets() {

    Dictionary out;
    out["logo_lift"] = (int64_t)26;
    out["title_below"] = (int64_t)46;
    out["sub_below"] = (int64_t)88;
    out["sub_text_only"] = (int64_t)66;
    return out;
}

// Lapisan glow judul saat jalur murah (baris 318): [(24,1),(14,2),(8,3)]; kosong kalau jalur mahal (mobile.perf.Quality.cheap_alpha False).
Array MysticSplash::title_glow_layers(bool cheap) {

    Array out;
    if (!cheap) {
        return out;
    }
    Dictionary l0;
    l0["layer"] = (int64_t)24;
    l0["spread"] = (int64_t)1;
    out.push_back(l0);
    Dictionary l1;
    l1["layer"] = (int64_t)14;
    l1["spread"] = (int64_t)2;
    out.push_back(l1);
    Dictionary l2;
    l2["layer"] = (int64_t)8;
    l2["spread"] = (int64_t)3;
    out.push_back(l2);
    return out;
}

// Rect permukaan glow judul SESUDAH smoothscale (baris 318): posisi (rect.x - layer - 1, rect.y - layer - 1), ukuran bertambah 2*layer + 2*spread.
Rect2 MysticSplash::title_glow_surface(const Rect2 & text_rect, int64_t layer, int64_t spread) {

    double x = text_rect.position.x - (double)layer - 1;
    double y = text_rect.position.y - (double)layer - 1;
    double w = text_rect.size.x + (double)(layer * 2) + (double)(spread * 2);
    double h = text_rect.size.y + (double)(layer * 2) + (double)(spread * 2);
    return Rect2(x, y, w, h);
}

// Alpha isi glow judul (baris 318): int(alpha * 0.28) — trunc.
int64_t MysticSplash::title_glow_fill(double alpha) {

    return py_int(alpha * 0.28);
}

// Jarak garis aksen dari tengah judul (baris 318): rect.w // 2 + 18.
int64_t MysticSplash::accent_gap(int64_t text_w) {

    return text_w / 2 + 18;
}

// Spesifikasi garis aksen kiri-kanan judul (baris 318): off -6 emas / +6 ungu, warna dikalikan (alpha/255)*0.85 lalu trunc; panjang 46, lebar 2. Posisi ujung dihitung renderer dari gap = accent_gap().
Array MysticSplash::accent_lines(double alpha) {

    Array out;
    {
        Color col = Color(255.0f / 255.0f, 190.0f / 255.0f, 60.0f / 255.0f);
        double fac = (alpha / 255.0) * 0.85;
        Color lc((double)py_int((double)col.get_r8() * fac) / 255.0,
                 (double)py_int((double)col.get_g8() * fac) / 255.0,
                 (double)py_int((double)col.get_b8() * fac) / 255.0);
        Dictionary row;
        row["off"] = (int64_t)-6;
        row["color"] = lc;
        row["width"] = (int64_t)2;
        row["len"] = (int64_t)46;
        out.push_back(row);
    }
    {
        Color col = Color(200.0f / 255.0f, 140.0f / 255.0f, 255.0f / 255.0f);
        double fac = (alpha / 255.0) * 0.85;
        Color lc((double)py_int((double)col.get_r8() * fac) / 255.0,
                 (double)py_int((double)col.get_g8() * fac) / 255.0,
                 (double)py_int((double)col.get_b8() * fac) / 255.0);
        Dictionary row;
        row["off"] = (int64_t)6;
        row["color"] = lc;
        row["width"] = (int64_t)2;
        row["len"] = (int64_t)46;
        out.push_back(row);
    }
    return out;
}

// Titik tengah teks hint (draw baris 178): (w // 2, h - 48).
Vector2 MysticSplash::hint_pos(int64_t screen_w, int64_t screen_h) {

    return Vector2((double)(screen_w / 2),
                   (double)(screen_h - 48));
}

// Alpha teks hint (draw baris 178): int(140 * a) — trunc.
int64_t MysticSplash::hint_alpha(double overall) {

    return py_int((double)140 * overall);
}


void MysticSplash::_bind_methods() {
    ClassDB::bind_static_method("MysticSplash", D_METHOD("module_names"), &MysticSplash::module_names);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("module_names_string"), &MysticSplash::module_names_string);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("api_signature"), &MysticSplash::api_signature);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("game_name"), &MysticSplash::game_name);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("tagline"), &MysticSplash::tagline);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("hint_text"), &MysticSplash::hint_text);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("splash_duration"), &MysticSplash::splash_duration);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("logo_paths"), &MysticSplash::logo_paths);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("accent"), &MysticSplash::accent);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("accent_2"), &MysticSplash::accent_2);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("text_main"), &MysticSplash::text_main);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("text_dim"), &MysticSplash::text_dim);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("gradient_stops"), &MysticSplash::gradient_stops);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("particle_colors"), &MysticSplash::particle_colors);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("font_sizes"), &MysticSplash::font_sizes);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("font_fallback_sizes"), &MysticSplash::font_fallback_sizes);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("font_styles"), &MysticSplash::font_styles);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("particle_count"), &MysticSplash::particle_count);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("particle_ranges"), &MysticSplash::particle_ranges);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("particle_move", "x", "y", "speed", "drift", "phase", "elapsed"), &MysticSplash::particle_move);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("particle_wrapped", "y"), &MysticSplash::particle_wrapped);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("particle_wrap_y", "screen_h"), &MysticSplash::particle_wrap_y);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("particle_advance", "x", "y", "speed", "drift", "phase", "elapsed", "screen_h", "respawn_x"), &MysticSplash::particle_advance);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("particle_twinkle", "elapsed", "phase"), &MysticSplash::particle_twinkle);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("particle_channel", "channel", "twinkle"), &MysticSplash::particle_channel);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("particle_draw_color", "base", "twinkle"), &MysticSplash::particle_draw_color);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("particle_draw_radius", "r"), &MysticSplash::particle_draw_radius);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("particle_draw_pos", "x", "y"), &MysticSplash::particle_draw_pos);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("fade_in", "t"), &MysticSplash::fade_in);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("fade_out_normal", "t"), &MysticSplash::fade_out_normal);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("fade_out_skip", "t"), &MysticSplash::fade_out_skip);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("overall_alpha", "t", "skipped"), &MysticSplash::overall_alpha);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("overall_alpha_godot", "t", "skipped", "skip_t"), &MysticSplash::overall_alpha_godot);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("title_alpha", "t"), &MysticSplash::title_alpha);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("is_done", "t", "skipped"), &MysticSplash::is_done);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("is_done_godot", "t", "skipped", "skip_t"), &MysticSplash::is_done_godot);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("draw_visible", "alpha"), &MysticSplash::draw_visible);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("title_alpha_drawn", "title_alpha", "overall"), &MysticSplash::title_alpha_drawn);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("timings"), &MysticSplash::timings);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("bg_step_h", "screen_h"), &MysticSplash::bg_step_h);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("bg_band_count", "screen_h"), &MysticSplash::bg_band_count);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("bg_band_rect", "i", "step_h", "screen_w"), &MysticSplash::bg_band_rect);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("bg_band_color", "i", "screen_h"), &MysticSplash::bg_band_color);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("bg_bands", "screen_w", "screen_h"), &MysticSplash::bg_bands);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("vignette_frames", "screen_w", "screen_h"), &MysticSplash::vignette_frames);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("content_center", "screen_w", "screen_h"), &MysticSplash::content_center);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("logo_center_y", "base_y", "has_logo"), &MysticSplash::logo_center_y);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("logo_scale", "img_w", "img_h"), &MysticSplash::logo_scale);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("logo_base_size", "img_w", "img_h"), &MysticSplash::logo_base_size);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("logo_grow_quant", "elapsed"), &MysticSplash::logo_grow_quant);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("logo_grow_size", "base", "gq"), &MysticSplash::logo_grow_size);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("logo_glow_radius", "ww", "hh"), &MysticSplash::logo_glow_radius);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("logo_glow_rect", "cx", "cy", "glow_r"), &MysticSplash::logo_glow_rect);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("logo_glow_rings", "glow_r"), &MysticSplash::logo_glow_rings);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("logo_offsets"), &MysticSplash::logo_offsets);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("title_glow_layers", "cheap"), &MysticSplash::title_glow_layers);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("title_glow_surface", "text_rect", "layer", "spread"), &MysticSplash::title_glow_surface);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("title_glow_fill", "alpha"), &MysticSplash::title_glow_fill);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("accent_gap", "text_w"), &MysticSplash::accent_gap);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("accent_lines", "alpha"), &MysticSplash::accent_lines);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("hint_pos", "screen_w", "screen_h"), &MysticSplash::hint_pos);
    ClassDB::bind_static_method("MysticSplash", D_METHOD("hint_alpha", "overall"), &MysticSplash::hint_alpha);
}

} // namespace godot
