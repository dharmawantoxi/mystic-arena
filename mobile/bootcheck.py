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
    return os.environ.get("MYSTIC_BOOTCHECK") == "1"


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

    # Audio disiapkan DI SINI, sebelum layar digambar, supaya bagian
    # AUDIO menampilkan keadaan yang sebenarnya. Kalau menunggu
    # main.py, laporannya masih kosong saat layar ini tampil dan
    # terlihat seolah tidak ada berkas suara sama sekali.
    try:
        from mobile import combat_audio as _ca
        _ca.init()
    except Exception as exc:
        print("[BOOTCHECK] init audio gagal: %s" % exc)

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
    # Jarak antar tombol >= 24 px: area sentuhnya dilebarkan 20 px
    # per sisi, jadi kalau terlalu rapat ketukan bisa salah tombol.
    buttons = [
        _Btn((W - 210, H - 82, 190, 60), "MULAI GAME", "start", OK),
        _Btn((30, H - 82, 250, 60), "GANTI MODE", "mode"),
        _Btn((305, H - 82, 250, 60), "JANGAN TAMPILKAN LAGI",
             "never", DIM),
        _Btn((580, H - 82, 150, 60), "UJI ULANG", "bench", DIM),
        _Btn((755, H - 82, 160, 60), "UJI SUARA", "audio",
             (180, 160, 255)),
    ]
    uji_audio_hasil = ""

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
                        elif b.action == "audio":
                            # Bunyikan satu contoh tiap jenis serangan
                            # secara berurutan. Kalau ada yang tidak
                            # terdengar, jenis itu yang bermasalah -
                            # tidak perlu masuk permainan dulu.
                            try:
                                from mobile import combat_audio as _ca
                                _ca.init(paksa=True)
                                hasil = _ca.uji_semua()
                                ok_n = sum(1 for _, o in hasil if o)
                                uji_audio_hasil = (
                                    "uji suara: %d/%d berbunyi -> %s"
                                    % (ok_n, len(hasil),
                                       ", ".join(k for k, o in hasil
                                                 if not o) or "semua OK"))
                            except Exception as exc:
                                uji_audio_hasil = "uji suara gagal: %s" % exc
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
        yy = y + 24
        rows = [
            ("mode aktif", mode),
            ("driver", info.get("video_driver", "?")),
            ("SCALED", info.get("SCALED")),
            ("jendela", info.get("window_size", "?")),
            ("surface", info.get("surface_size", "?")),
            ("bitsize", info.get("bitsize", "?")),
            ("arch", "%s / %s-bit" % (info.get("arch", "?"),
                                      info.get("bits", "?"))),
            ("skala", info.get("scale_factor", "?")),
        ]
        for k, v in rows:
            screen.blit(f.render("%-11s %s" % (k, v), True, FG), (48, yy))
            yy += 19

        # ── PENANDA RESEP PYGAME ──
        # Menjawab satu pertanyaan yang tiga kali menyesatkan kita:
        # "apakah pygame di APK ini benar-benar hasil kompilasi resep
        # terbaru, atau diambil lagi dari cache?"
        mark = diag.RESULTS.get("pygame_mark")
        if mark:
            screen.blit(f.render("resep pygame  %s" % mark, True, OK),
                        (48, yy))
        else:
            # Di PC ini wajar (pygame dari pip). Di HP ini ALARM:
            # berarti pygame diambil dari cache, bukan dikompilasi.
            w_mark = BAD if plat.IS_ANDROID else DIM
            screen.blit(f.render("resep pygame  TANPA PENANDA%s"
                                 % (" (CACHE!)" if plat.IS_ANDROID else ""),
                                 True, w_mark), (48, yy))
        yy += 19
        npatch = diag.RESULTS.get("neon_patch")
        if npatch is not None:
            screen.blit(f_small.render(
                "tambalan NEON: %s"
                % (", ".join(npatch) if npatch else "TIDAK ADA"),
                True, OK if npatch else BAD), (48, yy))
            yy += 18

        # ── kolom kanan: benchmark (SEMUA angka, ternormalkan) ──
        screen.blit(f_head.render("BIAYA OPERASI   ms | ns per piksel",
                                  True, FG), (575, y))
        yb2 = y + 24
        try:
            from mobile import _bench_core as bc
            groups = diag.RESULTS.get("groups") or bc.GROUPS
            for judul, keys in groups:
                screen.blit(f_small.render(judul, True, ACCENT), (575, yb2))
                yb2 += 17
                for k in keys:
                    v = bench.get(k)
                    if v is None:
                        screen.blit(f_small.render("  %-24s GAGAL" % k,
                                                   True, BAD), (583, yb2))
                        yb2 += 16
                        continue
                    nsp = bc.ns_per_px(bench, k)
                    if nsp is None:
                        warna = OK if v < 4 else (WARN if v < 10 else BAD)
                        teks = "  %-24s %7.2f ms" % (k, v)
                    else:
                        warna = (OK if nsp <= bc.NS_SEHAT else
                                 (WARN if nsp < bc.NS_CURIGA else BAD))
                        teks = "  %-24s %7.2f ms %7.1f ns/px" % (k, v, nsp)
                    screen.blit(f_small.render(teks, True, warna),
                                (583, yb2))
                    yb2 += 16
        except Exception as exc:
            screen.blit(f_small.render("gagal menampilkan: %s" % exc,
                                       True, BAD), (583, yb2))
            yb2 += 17

        # ── status optimasi (biar kegagalan langsung kelihatan) ──
        try:
            from mobile.perf import Quality as _Q
            _on = not _Q.cheap_alpha
            txt = ("MODE HEMAT: %s | sprite cache: %s | kualitas: %s"
                   % ("AKTIF" if _on else "MATI",
                      "AKTIF" if _Q.sprite_cache else "mati", _Q.level))
            screen.blit(f.render(txt, True, OK if _on else BAD),
                        (36, yy + 8))
            yy += 32
        except Exception:
            pass

        # ── sentuhan ──
        yb = yy + 10
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

        # ══ AUDIO ══
        # Bagian ini menjawab "kenapa suaranya tidak keluar" tanpa
        # perlu adb dan tanpa tebak-tebakan: terlihat langsung apakah
        # foldernya ada, berapa berkas yang benar-benar ditemukan di
        # dalam APK, dan berkas mana yang dipakai tiap jenis serangan.
        ya = yb + 76
        try:
            from mobile import combat_audio as _ca
            lap = _ca.LAPORAN
            ada = lap.get("dir_ada")
            n_berkas = len(lap.get("berkas") or [])
            warna = OK if (ada and n_berkas) else BAD
            screen.blit(f_head.render("AUDIO", True, FG), (36, ya))
            ya += 24
            screen.blit(f.render(
                "folder %s   berkas %d   mixer %s"
                % ("ADA" if ada else "TIDAK ADA", n_berkas,
                   lap.get("mixer", "?")), True, warna), (48, ya))
            ya += 20
            pj = lap.get("per_jenis") or {}
            if pj:
                ringkas = "  ".join(
                    "%s %d" % (k.replace("_attack", "").replace("_shoot", ""),
                               len(v)) for k, v in pj.items())
                kosong = [k for k, v in pj.items() if not v]
                screen.blit(f_small.render(ringkas, True,
                                           WARN if kosong else OK),
                            (48, ya))
                ya += 18
            for baris in _wrap(lap.get("catatan", ""), 68)[:2]:
                screen.blit(f_small.render(baris, True, DIM), (48, ya))
                ya += 17
            if uji_audio_hasil:
                screen.blit(f_small.render(uji_audio_hasil, True, ACCENT),
                            (48, ya))
                ya += 17
        except Exception as exc:
            screen.blit(f_small.render("audio: %s" % exc, True, BAD),
                        (48, ya))
            ya += 17

        # ── kesimpulan ──
        # Ditaruh di KOLOM KIRI (bukan melintang penuh) karena kolom
        # kanan sekarang berisi 5 grup pengukuran dan tumbuh sampai
        # sekitar y=600. Melintang penuh membuat keduanya bertabrakan.
        yv = ya + 10
        screen.blit(f_head.render("KESIMPULAN", True, FG), (36, yv))
        yv += 24
        pairs = diag.RESULTS.get("verdict_pairs")
        if not pairs:
            pairs = [("WARN", v) for v in verdict]
        warna_map = {"OK": OK, "WARN": WARN, "BAD": BAD}
        batas_y = H - 112
        for lv, line in pairs:
            if yv > batas_y:
                break
            for chunk in _wrap(line, 68):
                if yv > batas_y:
                    break
                screen.blit(f_small.render(chunk, True,
                                           warna_map.get(lv, WARN)),
                            (48, yv))
                yv += 15

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
