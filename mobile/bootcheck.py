# ================================
# mobile/bootcheck.py
# LAYAR DIAGNOSTIK DI PERANGKAT
#
# Muncul sebelum game (hanya di Android atau MYSTIC_BOOTCHECK=1).
# Tujuannya satu: menjawab tiga pertanyaan tanpa perlu adb —
#   1. Apakah sentuhan sampai ke game?   -> penghitung event + titik
#   2. Kenapa lambat?                    -> benchmark + kesimpulan
#   3. Mode tampilan mana yang cepat?    -> bisa diganti & disimpan
#
# Sengaja digambar sesederhana mungkin (kotak + teks) supaya tetap
# responsif walaupun perangkatnya sedang bermasalah.
#
# Layar ini bisa dimatikan permanen dari dalam layar itu sendiri
# (tombol JANGAN TAMPILKAN LAGI) atau lewat MYSTIC_BOOTCHECK=0.
# ================================

import os
import time

import pygame

from mobile import platform_utils as plat
from mobile import diagnostics as diag

BG = (12, 10, 20)
FG = (225, 228, 240)
DIM = (150, 155, 175)
OK = (120, 235, 140)
WARN = (255, 205, 90)
BAD = (255, 110, 110)
ACCENT = (255, 200, 70)

AUTO_CONTINUE_SEC = 45


def _flag_file():
    return os.path.join(plat.get_writable_dir(), "skip_bootcheck.txt")


def should_show():
    env = os.environ.get("MYSTIC_BOOTCHECK")
    if env == "1":
        return True
    if env == "0":
        return False
    if os.path.exists(_flag_file()):
        return False
    return plat.IS_ANDROID


def _disable_forever():
    try:
        with open(_flag_file(), "w") as fh:
            fh.write("1")
    except Exception:
        pass


class _Btn:
    def __init__(self, rect, label, action, color=ACCENT):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.action = action
        self.color = color

    def hit(self, pos):
        return self.rect.inflate(20, 20).collidepoint(pos)


def run(screen, get_font, touch):
    """
    Tampilkan layar diagnostik. Kembalikan True kalau game harus
    lanjut, False kalau pemain menutup aplikasi.
    """
    clock = pygame.time.Clock()

    info = diag.log_display_info(screen)
    bench = {}
    verdict = ["mengukur..."]
    try:
        bench = diag.run_benchmark(screen, quick=True)
        verdict = diag.RESULTS.get("verdict", [])
    except Exception as exc:
        verdict = ["benchmark gagal: %s" % exc]

    f_title = get_font(30, "body_bold")
    f_head = get_font(21, "body_bold")
    f = get_font(17, "body")
    f_small = get_font(14, "body")

    W, H = plat.LOGICAL_WIDTH, plat.LOGICAL_HEIGHT
    buttons = [
        _Btn((W - 330, H - 78, 200, 56), "MULAI GAME", "start", OK),
        _Btn((40, H - 78, 260, 56), "GANTI MODE TAMPILAN", "mode"),
        _Btn((320, H - 78, 250, 56), "JANGAN TAMPILKAN LAGI",
             "never", DIM),
        _Btn((590, H - 78, 150, 56), "UJI ULANG", "bench", DIM),
    ]

    mode = plat.get_mode()
    taps = []
    start = time.perf_counter()
    running = True
    result = True

    while running:
        elapsed = time.perf_counter() - start
        sisa = max(0, AUTO_CONTINUE_SEC - int(elapsed))

        touch.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                running = False
            touch.process_event(event)

        for act in touch.collect():
            if act.kind in ("down", "tap"):
                if act.kind == "tap":
                    taps.append((act.pos, time.perf_counter()))
                    taps[:] = taps[-6:]
                for b in buttons:
                    if b.hit(act.pos):
                        if b.action == "start":
                            running = False
                        elif b.action == "never":
                            _disable_forever()
                            running = False
                        elif b.action == "mode":
                            idx = plat.DISPLAY_MODES.index(mode)
                            mode = plat.DISPLAY_MODES[
                                (idx + 1) % len(plat.DISPLAY_MODES)]
                            plat.save_display_mode(mode)
                        elif b.action == "bench":
                            bench = diag.run_benchmark(screen, quick=True)
                            verdict = diag.RESULTS.get("verdict", [])
                        break

        if sisa <= 0:
            running = False

        # ─────────── gambar ───────────
        screen.fill(BG)
        y = 18
        screen.blit(f_title.render("DIAGNOSTIK MYSTIC ARENA", True, ACCENT),
                    (36, y))
        y += 40

        dev = plat.get_device_info()
        screen.blit(f.render(
            "%s | Android %s (API %s) | pygame %s"
            % (dev["model"], dev["android_release"], dev["api_level"],
               dev["pygame"]), True, DIM), (36, y))
        y += 22
        try:
            from mobile.buildinfo import label as _blabel
            screen.blit(f_head.render(_blabel(), True, OK), (36, y))
        except Exception:
            pass
        y += 26

        # ── kolom kiri: display ──
        screen.blit(f_head.render("TAMPILAN", True, FG), (36, y))
        yy = y + 26
        rows = [
            ("mode aktif", mode),
            ("driver", info.get("video_driver", "?")),
            ("SCALED", info.get("SCALED")),
            ("jendela", info.get("window_size", "?")),
            ("surface", info.get("surface_size", "?")),
            ("bitsize", info.get("bitsize", "?")),
            ("skala", info.get("scale_factor", "?")),
        ]
        for k, v in rows:
            screen.blit(f.render("%-11s %s" % (k, v), True, FG), (48, yy))
            yy += 22

        # ── kolom kanan: benchmark ──
        screen.blit(f_head.render("BIAYA OPERASI DASAR (ms)", True, FG),
                    (560, y))
        yy = y + 26
        batas = {"flip": 3.0, "fill_layar": 2.0, "blit_penuh_alpha": 3.0,
                 "blit_alpha_KE_noalpha": 3.0,
                 "100x_blit_kecil": 3.0, "100x_blit_kecil_colorkey": 3.0,
                 "200x_draw.circle": 6.0, "alokasi_surface_penuh": 4.0}
        for k, limit in batas.items():
            v = bench.get(k)
            if v is None:
                continue
            warna = OK if v <= limit else (WARN if v <= limit * 2.5 else BAD)
            screen.blit(f.render("%-22s %7.2f  (sehat < %.0f)"
                                 % (k, v, limit), True, warna), (572, yy))
            yy += 22

        # ── sentuhan ──
        yb = 300
        screen.blit(f_head.render("SENTUHAN", True, FG), (36, yb))
        c = touch.counts
        warna = OK if (c["mouse"] + c["finger"]) else BAD
        screen.blit(f.render(
            "event mouse=%d   finger=%d   tap dikenali=%d"
            % (c["mouse"], c["finger"], c["tap"]), True, warna), (48, yb + 26))
        if touch.last_raw:
            screen.blit(f.render(
                "mentah=%s  ->  logis=(%.0f, %.0f)"
                % (tuple(int(v) for v in touch.last_raw),
                   touch.last_logical[0], touch.last_logical[1]),
                True, DIM), (48, yb + 48))
        else:
            screen.blit(f.render(
                "Sentuh layar di mana saja untuk menguji.",
                True, WARN), (48, yb + 48))

        now = time.perf_counter()
        for pos, t0 in taps:
            age = now - t0
            if age < 2.0:
                r = int(14 + age * 30)
                pygame.draw.circle(screen, (90, 220, 255),
                                   (int(pos[0]), int(pos[1])), r, 2)
                pygame.draw.line(screen, (255, 255, 255),
                                 (pos[0] - 10, pos[1]), (pos[0] + 10, pos[1]))
                pygame.draw.line(screen, (255, 255, 255),
                                 (pos[0], pos[1] - 10), (pos[0], pos[1] + 10))

        # ── kesimpulan ──
        yv = 400
        screen.blit(f_head.render("KESIMPULAN", True, FG), (36, yv))
        yv += 26
        for line in verdict[:4]:
            for chunk in _wrap(line, 108):
                screen.blit(f_small.render(chunk, True, WARN), (48, yv))
                yv += 18

        # ── tombol ──
        for b in buttons:
            pygame.draw.rect(screen, (26, 24, 38), b.rect, border_radius=10)
            pygame.draw.rect(screen, b.color, b.rect, 2, border_radius=10)
            t = f.render(b.label, True, b.color)
            screen.blit(t, t.get_rect(center=b.rect.center))

        screen.blit(f_small.render(
            "Lanjut otomatis dalam %d detik. Ganti mode = keluar-masuk "
            "aplikasi agar berlaku. FPS layar ini: %d"
            % (sisa, int(clock.get_fps())), True, DIM), (36, H - 100))

        plat.present()
        clock.tick(30)

    return result


def _wrap(text, width):
    out, line = [], ""
    for word in str(text).split():
        if len(line) + len(word) + 1 > width:
            out.append(line)
            line = word
        else:
            line = (line + " " + word).strip()
    if line:
        out.append(line)
    return out or [""]
