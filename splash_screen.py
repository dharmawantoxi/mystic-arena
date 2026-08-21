# ================================
# splash_screen.py
# Splashscreen pembuka game (logo + judul game)
#
# CARA PAKAI LOGO GAMBAR:
#   Letakkan file logo di salah satu path di bawah (paling atas dicek dulu):
#     - assets/logo.png
#     - assets/splash_logo.png
#     - assets/logo.jpg
#   Kalau tidak ada file gambar, otomatis pakai logo TEKS animasi.
# ================================

import math
import os
import random

import pygame

# ═══════════════════════════════════════════════════════
# KONFIGURASI (ganti sesuai branding Anda)
# ═══════════════════════════════════════════════════════
GAME_NAME = "MYSTIC ARENA"       # <- ganti nama game Anda
SPLASH_DURATION = 3.0            # detik (auto pindah ke menu)
LOGO_PATHS = [
    "assets/logo.png",
    "assets/splash_logo.png",
    "assets/logo.jpg",
    "assets/logo.jpeg",
]

# Warna aksen (bisa disesuaikan)
ACCENT = (255, 190, 60)          # emas
ACCENT_2 = (200, 140, 255)       # ungu terang
TEXT_MAIN = (245, 240, 230)      # putih hangat
TEXT_DIM = (160, 155, 170)       # abu-ungu


class SplashScreen:
    """Splashscreen: logo + judul game.

    - Auto pindah setelah SPLASH_DURATION detik.
    - Bisa di-skip kapan saja (klik / tombol / controller).
    """

    def __init__(self, screen):
        self.screen = screen
        self.w, self.h = screen.get_size()

        # Waktu (detik)
        self.elapsed = 0.0
        self.skipped = False
        self.done = False

        # Partikel latar
        self.particles = self._make_particles(46)

        # Logo gambar (kalau ada)
        self.logo_img = None
        self._load_logo()

        # Font
        self._init_fonts()

        self.title_alpha = 0

    # ─────────────────────────────────────────────
    # INIT
    # ─────────────────────────────────────────────
    def _init_fonts(self):
        try:
            from _render import get_font as _gf, title_font as _tf
            self.font_presents = _gf(34, "body_bold")
            self.font_title = _tf(92)
            self.font_title_below = _tf(66)
            self.font_sub = _gf(22, "body_semibold")
            self.font_hint = _gf(16, "body_medium")
        except Exception:
            self.font_presents = pygame.font.Font(None, 40)
            self.font_title = pygame.font.Font(None, 110)
            self.font_title_below = pygame.font.Font(None, 80)
            self.font_sub = pygame.font.Font(None, 26)
            self.font_hint = pygame.font.Font(None, 18)

    def _load_logo(self):
        # Resolve path relatif ke folder modul ini (lebih robust),
        # lalu fallback ke working directory.
        base = os.path.dirname(os.path.abspath(__file__))
        for path in LOGO_PATHS:
            candidates = []
            if not os.path.isabs(path):
                candidates.append(os.path.join(base, path))
                candidates.append(os.path.join(os.getcwd(), path))
            else:
                candidates.append(path)
            for cand in candidates:
                if os.path.exists(cand):
                    try:
                        img = pygame.image.load(cand)
                        if img.get_width() > 0:
                            self.logo_img = img
                            return
                    except Exception:
                        continue

    def _make_particles(self, count):
        pts = []
        for _ in range(count):
            pts.append({
                "x": random.uniform(0, self.w),
                "y": random.uniform(0, self.h),
                "r": random.uniform(0.6, 2.4),
                "speed": random.uniform(0.08, 0.35),
                "drift": random.uniform(-0.12, 0.12),
                "phase": random.uniform(0, math.tau),
                "color": random.choice([
                    (255, 210, 120), (230, 160, 255),
                    (255, 245, 230), (180, 200, 255),
                ]),
            })
        return pts

    # ─────────────────────────────────────────────
    # CONTROL
    # ─────────────────────────────────────────────
    def skip(self):
        """Skip splash -> percepat ke fase keluar (fade out cepat)."""
        if not self.done:
            self.skipped = True

    def is_done(self):
        return self.done

    # ─────────────────────────────────────────────
    # UPDATE
    # ─────────────────────────────────────────────
    def update(self, dt):
        self.elapsed += dt

        # Gerakkan partikel
        for p in self.particles:
            p["y"] -= p["speed"]
            p["x"] += p["drift"] + math.sin(self.elapsed * 0.8 + p["phase"]) * 0.05
            if p["y"] < -6:
                p["y"] = self.h + 6
                p["x"] = random.uniform(0, self.w)

        # Hitung fase
        dur = SPLASH_DURATION
        if self.skipped:
            # Skip -> fade out cepat 0.25 dtk
            if self.elapsed >= 0.25:
                self.done = True
        else:
            if self.elapsed >= dur:
                self.done = True

        # Alpha judul (fade in bertahap)
        t = self.elapsed
        if t < 0.5:
            self.title_alpha = 0
        else:
            self.title_alpha = int(255 * min(1.0, (t - 0.5) / 0.6))

    # ─────────────────────────────────────────────
    # DRAW
    # ─────────────────────────────────────────────
    def _overall_alpha(self):
        """Alpha keseluruhan (fade in awal + fade out akhir)."""
        t = self.elapsed
        fade_in = min(1.0, t / 0.4)
        if self.skipped:
            fade_out = max(0.0, 1.0 - t / 0.25)
        else:
            dur = SPLASH_DURATION
            fade_out = min(1.0, max(0.0, (dur - t) / 0.45))
        return max(0.0, min(1.0, fade_in * fade_out))

    def draw(self):
        surf = self.screen
        a = self._overall_alpha()
        if a <= 0.001:
            return

        # ── Background: gradient gelap ──
        bg = pygame.Surface((self.w, self.h))
        top = (8, 8, 18)
        mid = (22, 16, 38)
        bot = (6, 6, 14)
        step_h = max(1, self.h // 48)
        for i in range(0, self.h, step_h):
            f = i / self.h
            if f < 0.55:
                f2 = f / 0.55
                c = [int(top[j] + (mid[j] - top[j]) * f2) for j in range(3)]
            else:
                f2 = (f - 0.55) / 0.45
                c = [int(mid[j] + (bot[j] - mid[j]) * f2) for j in range(3)]
            pygame.draw.rect(bg, tuple(c), (0, i, self.w, step_h))

        # ── Partikel latar ──
        for p in self.particles:
            tw = 0.5 + 0.5 * math.sin(self.elapsed * 2.5 + p["phase"])
            col = tuple(int(ch * (0.35 + 0.65 * tw)) for ch in p["color"])
            pygame.draw.circle(bg, col,
                               (int(p["x"]), int(p["y"])), max(1, int(p["r"])))

        # ── Vignette ──
        vig = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        for i in range(140, 0, -2):
            alpha = min(255, int(2.2 * (140 - i)))
            pygame.draw.rect(vig, (0, 0, 0, alpha),
                             (i, i, self.w - 2 * i, self.h - 2 * i))
        bg.blit(vig, (0, 0))

        surf.blit(bg, (0, 0))

        # ── Konten utama ──
        cx = self.w // 2
        base_y = self.h // 2

        # Logo di tengah (sedikit naik supaya seimbang dengan judul di bawah)
        logo_cy = base_y - (26 if self.logo_img is not None else 0)

        # 1) Logo / judul (bagian tengah)
        self._draw_logo_or_title(surf, cx, logo_cy, a)

        # 2) Hint "Klik / tekan tombol untuk skip"
        hint = self.font_hint.render(
            "Tap anywhere to skip", True, TEXT_DIM)
        hr = hint.get_rect(center=(cx, self.h - 48))
        hint.set_alpha(int(140 * a))
        surf.blit(hint, hr)

    def _draw_logo_or_title(self, surf, cx, base_y, a):
        """Gambar logo (file) kalau ada, selain itu logo teks judul."""
        ta = int(self.title_alpha * a)

        if self.logo_img is not None:
            img = self.logo_img
            # Skala: maks 340px lebar / 320px tinggi (logo persegi muat besar)
            scale = min(340.0 / img.get_width(),
                        320.0 / img.get_height(), 1.0)
            w = max(1, int(img.get_width() * scale))
            h = max(1, int(img.get_height() * scale))
            img2 = pygame.transform.smoothscale(img, (w, h))
            # Scale-in saat muncul + glow
            grow = min(1.0, self.elapsed / 0.9)
            ww = max(1, int(w * (0.85 + 0.15 * grow)))
            hh = max(1, int(h * (0.85 + 0.15 * grow)))
            img3 = pygame.transform.smoothscale(img2, (ww, hh))
            img3.set_alpha(ta)
            rect = img3.get_rect(center=(cx, base_y))
            # glow lembut di belakang logo
            glow_r = max(ww, hh) // 2 + 30
            glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            for g in range(glow_r, 0, -3):
                alpha_g = int(12 * (1 - g / glow_r))
                pygame.draw.circle(glow, (*ACCENT, alpha_g),
                                   (glow_r, glow_r), g)
            surf.blit(glow, (cx - glow_r, rect.centery - glow_r))
            surf.blit(img3, rect)

            # Judul teks di bawah logo (font lebih kecil supaya proporsional)
            title = self.font_title_below.render(GAME_NAME, True, TEXT_MAIN)
            self._draw_glow_title(surf, title, cx, rect.bottom + 46, ta)

            # Tagline kecil di bawah judul
            sub = self.font_sub.render(
                "A MOBA TOWER DEFENSE ADVENTURE", True, TEXT_DIM)
            sub.set_alpha(ta)
            surf.blit(sub, sub.get_rect(center=(cx, rect.bottom + 88)))

        else:
            # Logo teks: judul besar dengan glow
            title = self.font_title.render(GAME_NAME, True, TEXT_MAIN)
            self._draw_glow_title(surf, title, cx, base_y, ta)

            # Subtitle kecil di bawah judul
            sub = self.font_sub.render(
                "A MOBA TOWER DEFENSE ADVENTURE", True, TEXT_DIM)
            sub.set_alpha(ta)
            surf.blit(sub, sub.get_rect(center=(cx, base_y + 66)))

    def _draw_glow_title(self, surf, text_surf, cx, cy, alpha):
        """Gambar teks judul dengan efek glow emas-ungu."""
        if alpha <= 0:
            return
        rect = text_surf.get_rect(center=(cx, cy))

        # Glow berlapis (3 lapis + smoothscale = 24 ms/frame di HP)
        try:
            from mobile.perf import Quality as _Qs
            _cheap = _Qs.cheap_alpha
        except Exception:
            _cheap = True
        for layer, spread in ([(24, 1), (14, 2), (8, 3)] if _cheap
                              else []):
            glow = pygame.Surface(
                (rect.w + layer * 2, rect.h + layer * 2), pygame.SRCALPHA)
            glow.blit(text_surf, (layer, layer))
            glow.fill((*ACCENT, int(alpha * 0.28)),
                      special_flags=pygame.BLEND_RGBA_MULT)
            for _ in range(spread):
                glow = pygame.transform.smoothscale(
                    glow, (glow.get_width() + 2, glow.get_height() + 2))
            surf.blit(glow, (rect.x - layer - 1, rect.y - layer - 1))

        t = surf
        # Teks utama
        text = text_surf.copy()
        text.set_alpha(alpha)
        t.blit(text, rect)

        # Aksen garis di kiri-kanan judul
        gap = rect.w // 2 + 18
        y = rect.centery
        for off, col in [(-6, ACCENT), (6, ACCENT_2)]:
            fac = (alpha / 255.0) * 0.85
            line_c = tuple(int(ch * fac) for ch in col)
            pygame.draw.line(surf, line_c,
                             (cx - gap, y + off),
                             (cx - gap + 46, y + off), 2)
            pygame.draw.line(surf, line_c,
                             (cx + gap, y + off),
                             (cx + gap - 46, y + off), 2)

    def draw_preview_frame(self, path, at_seconds):
        """(untuk testing) render satu frame pada waktu tertentu."""
        # simulasikan update sampai waktu ts
        self.elapsed = at_seconds
        self.title_alpha = int(255 * min(1.0, max(0.0, (at_seconds - 0.5) / 0.6)))
        for p in self.particles:
            p["y"] -= p["speed"] * 60
            if p["y"] < -6:
                p["y"] = self.h + 6
        self.draw()
        pygame.image.save(self.screen, path)
