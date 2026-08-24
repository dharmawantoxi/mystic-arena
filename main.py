# ================================
# main.py - ENTRY POINT (Android / touchscreen first)
#
# Versi lama (keyboard + controller) disimpan di
# main_desktop_legacy.py sebagai rujukan.
#
# Jalan di 3 mode:
#   Android            -> otomatis fullscreen + kontrol sentuh
#   PC (uji layout HP) -> MYSTIC_FORCE_TOUCH=1 python main.py
#   PC (normal)        -> mouse + keyboard tetap berfungsi
# ================================

import os
import sys

import pygame

# ═══════════════════════════════════════════════════════
# 1. AUDIO: buffer kecil = latensi rendah, tapi jangan terlalu
#    kecil di Android (crackling). 1024 = kompromi aman.
#    WAJIB sebelum pygame.init().
# ═══════════════════════════════════════════════════════
try:
    pygame.mixer.pre_init(frequency=44100, size=-16, channels=2,
                          buffer=1024)
except Exception:
    pass

pygame.init()

# ═══════════════════════════════════════════════════════
# 2. PATCH PERFORMA - HARUS sebelum modul game di-import,
#    karena sebagian modul membuat font saat di-import.
# ═══════════════════════════════════════════════════════
from mobile import platform_utils as plat          # noqa: E402
from mobile import perf                            # noqa: E402

adaptive = perf.install_all(is_android=plat.TOUCH_MODE)

from mobile import touch as touch_mod              # noqa: E402
from mobile import hud as hud_mod                  # noqa: E402
from mobile import debug as debug_mod              # noqa: E402
from mobile import diagnostics as diag_mod         # noqa: E402
from mobile import bootcheck as bootcheck_mod      # noqa: E402
from mobile import combat_audio as audio_mod       # noqa: E402
from mobile import sidepanel as panel_mod          # noqa: E402

debug_mod.install_crash_handler()

# ═══════════════════════════════════════════════════════
# 3. LAYAR (SCALED = koordinat tetap 1280x720, GPU yang scaling)
# ═══════════════════════════════════════════════════════
# create_display() mengembalikan permukaan yang HARUS digambari game.
# Di mode "native" itu surface 720p terpisah; plat.present() yang
# menyalinnya ke layar. Di mode "scaled" keduanya sama.
screen = plat.create_display(vsync=True)

# ═══════════════════════════════════════════════════════
# 4. MODUL GAME
# ═══════════════════════════════════════════════════════
import _core                                        # noqa: E402,F401
from settings import TITLE                          # noqa: E402
from game import Game                               # noqa: E402
from menu import Menu                               # noqa: E402
from splash_screen import SplashScreen              # noqa: E402
from _render import get_font                        # noqa: E402

pygame.display.set_caption(TITLE)

STATE_SPLASH, STATE_MENU, STATE_GAME, STATE_PAUSE = (
    "splash", "menu", "game", "pause")

# Event siklus hidup Android (tidak ada di semua versi pygame)
APP_BG = getattr(pygame, "APP_WILLENTERBACKGROUND", -1)
APP_FG = getattr(pygame, "APP_DIDENTERFOREGROUND", -2)


def _cinematic_active(game):
    if game is None:
        return False
    for name in ("level_intro", "boss_intro"):
        obj = getattr(game, name, None)
        if obj is not None:
            try:
                if obj.is_active():
                    return True
            except Exception:
                pass
    death = getattr(game, "boss_death", None)
    if death is not None and getattr(death, "celebration_active", False):
        return True
    return False


def _handle_background(sound_mgr):
    """
    Android mematikan render saat app di-minimize. Kalau kita tetap
    memutar loop, baterai habis & SDL bisa crash. Jadi kita tidur
    sampai app kembali ke depan.
    """
    print("[LIFECYCLE] app masuk background - pause")
    try:
        pygame.mixer.pause()
        pygame.mixer.music.pause()
    except Exception:
        pass
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == APP_FG:
                waiting = False
        pygame.time.wait(120)
    print("[LIFECYCLE] app kembali ke depan - resume")
    try:
        pygame.mixer.unpause()
        pygame.mixer.music.unpause()
    except Exception:
        pass
    return True


def main():
    global screen
    # ═══ SUARA ═══
    from sound_manager import SoundManager
    sound_mgr = SoundManager()
    sound_mgr.load_all()
    sound_mgr.play_bgm('bgm_battle.wav', loop=True, fade_ms=3000)
    sound_mgr.play_ambient('ambient_forest', volume_mult=0.8)

    clock = pygame.time.Clock()
    frame_timer = perf.FrameTimer()

    touch = touch_mod.TouchManager()
    hud = hud_mod.TouchHUD(get_font)
    # Tombol FPS: TAMPIL selama masih menyetel performa.
    # Untuk rilis Play Store, ganti baris ini jadi:
    #     hud.show_debug_button = False
    # Tombol FPS tampil (di bawah panel gold). Untuk rilis Play Store
    # cukup set MYSTIC_DEBUG=0 atau ubah baris ini jadi False.
    # Tombol FPS DIMATIKAN secara default (v30): game sudah lancar,
    # dan panel debug itu sendiri memakan 4 ms dari 12,5 ms waktu
    # gambar. Masih bisa dinyalakan untuk diagnosa dengan
    # MYSTIC_DEBUG=1, atau tekan-tahan tombol JEDA.
    hud.show_debug_button = os.environ.get("MYSTIC_DEBUG") == "1"
    debug = debug_mod.DebugOverlay(get_font, frame_timer)

    # ═══ LAYAR DIAGNOSTIK (Android / MYSTIC_BOOTCHECK=1) ═══
    # Menampilkan info tampilan, benchmark, dan penghitung sentuhan.
    # Bisa dimatikan permanen dari dalam layarnya.
    if bootcheck_mod.should_show():
        if not bootcheck_mod.run(screen, get_font, touch):
            pygame.quit()
            sys.exit()
        touch.cancel()
    else:
        diag_mod.run_all(screen)

    # Benchmark baru saja menentukan Quality.cheap_alpha. Buffer render
    # dibuat SEBELUM itu, jadi pelacak alpha-blit belum sempat dipasang.
    # Buat ulang sekarang supaya pelacaknya aktif di perangkat lambat.
    try:
        from mobile import blitwatch
        from mobile import fastblit
        perlu_ulang = False
        if blitwatch.enabled() and not isinstance(
                screen, blitwatch.WatchedSurface):
            perlu_ulang = True
        # Jalur cepat alpha baru diputuskan oleh benchmark barusan.
        if fastblit.AKTIF and not isinstance(screen, fastblit.FastSurface):
            perlu_ulang = True
        if perlu_ulang:
            screen = plat.create_display(vsync=True)
            print("[DISPLAY] buffer render dibuat ulang "
                  "(jalur cepat=%s)" % fastblit.AKTIF)
    except Exception as exc:
        print("[DISPLAY] gagal memasang pelacak: %s" % exc)

    # Suara tempur dimuat SETELAH layar siap supaya tidak menambah
    # waktu tampil splash. Gagal memuat tidak menghentikan game.
    try:
        audio_mod.init()
    except Exception as exc:
        print("[AUDIO] init gagal: %s" % exc)

    # Panel kanan (kalau layarnya lebih lebar dari 16:9).
    side = panel_mod.SidePanel(get_font)
    panel_mod.daftarkan(side)
    if side.aktif:
        print("[PANEL] panel kanan aktif: %s" % (side.rect,))

    def _gambar_panel(g=None):
        """
        Panel kanan digambar SEBELUM game supaya popup yang pindah ke
        panel (panel hero, popup upgrade) tergambar DI ATASNYA.
        """
        if not side.aktif:
            return
        perf.PHASES.mark("panel")
        try:
            # Ada popup yang menggambar ke dalam panel? Kalau ya, panel
            # harus dipulihkan penuh tiap frame.
            paksa = bool(g is not None and (
                getattr(g, "selected_hero", None)
                or getattr(g, "popup_target", None)
                or getattr(g, "build_popup_slot", None)))
            side.draw(plat.get_full_surface(), g, clock,
                      clock.get_time(), paksa_blit=paksa)
        except Exception as exc:
            print("[PANEL] gagal menggambar: %s" % exc)
            side.aktif = False
        perf.PHASES.end()

    menu = Menu(screen)
    menu.controller_mgr = None          # tidak ada controller di HP
    splash = SplashScreen(screen)

    game = None
    current_state = STATE_SPLASH

    import __main__
    __main__.game_instance = None

    info = plat.get_device_info()
    print("=" * 60)
    print("  MYSTIC ARENA - MOBILE BUILD")
    print("  device : %s" % info["model"])
    print("  android: %s (API %s)" % (info["android_release"],
                                      info["api_level"]))
    print("  input  : %s" % ("TOUCH" if plat.TOUCH_MODE else "MOUSE/KEYBOARD"))
    print("  quality: %s" % perf.Quality.level)
    print("=" * 60)

    claimed = set()
    splash_last = pygame.time.get_ticks()
    running = True

    # ═══════════════════════════════════════════════════════
    # LANGKAH SIMULASI TETAP (fixed timestep)
    #
    # Logika game ini berbasis FRAME: sekali update() = satu langkah
    # yang dirancang untuk 60 langkah/detik. Kalau render hanya
    # sanggup 17 FPS, dulu update juga cuma 17x/detik sehingga
    # SEMUANYA bergerak 28% kecepatan -> terasa "slow motion",
    # bukan sekadar patah-patah.
    #
    # Sekarang waktu nyata diakumulasi dan update() dijalankan
    # sebanyak yang diperlukan untuk mengejar. update() hanya
    # 0,5 ms (render 52 ms), jadi mengejar 3-4 langkah nyaris gratis.
    #
    # MAX_CATCHUP membatasi kejaran supaya tidak terjadi "spiral
    # kematian" saat ada hentakan panjang (mis. GC atau loading).
    # ═══════════════════════════════════════════════════════
    FIXED_DT_MS = 1000.0 / 60.0
    MAX_CATCHUP = 8          # 8 langkah = frame 133 ms masih terkejar
    sim_acc = 0.0
    sim_steps = 0
    sim_capped = 0           # berapa kali mentok (waktu game tertinggal)

    while running:
        # ─────────────────────────────── EVENT
        frame_timer.start("event")
        perf.new_frame_budget()      # jatah konversi sprite frame ini
        audio_mod.new_frame()        # jatah suara tempur frame ini
        touch.update()
        ctx = {"game": game, "menu": menu, "debug": debug,
               "request_pause": False}

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue
            if event.type == APP_BG:
                touch.cancel()
                if not _handle_background(sound_mgr):
                    running = False
                continue

            if touch.process_event(event):
                continue

            # ── keyboard: hanya untuk pengembangan di PC ──
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F8:
                    debug.toggle()
                elif event.key == pygame.K_ESCAPE:
                    if current_state == STATE_GAME:
                        ctx["request_pause"] = True
                    elif current_state == STATE_MENU:
                        menu.handle_key(event.key)
                elif current_state == STATE_GAME and game:
                    game.handle_key(event.key)
                elif current_state in (STATE_MENU, STATE_PAUSE):
                    menu.handle_key(event.key)

        # ─────────────────────────────── AKSI SENTUH
        cine = _cinematic_active(game)
        hud.sync(game, current_state, cine)

        for action in touch.collect():
            tid = action.touch_id

            # Tahan tombol jeda = buka/tutup overlay debug.
            # (dicek sebelum filter `claimed` karena sentuhan yang
            #  sama sudah diklaim HUD saat "down")
            if action.kind == "long_press" and current_state == STATE_GAME:
                _pb = side.buttons.get("pause") if side.aktif else None
                if ((_pb is not None and _pb.contains(action.pos))
                        or hud.buttons["pause"].contains(action.pos)):
                    debug.toggle()
                    plat.vibrate(30)
                    continue

            if action.kind == "down":
                hit = None
                if current_state == STATE_GAME:
                    # Panel diperiksa DULU: koordinatnya di luar peta,
                    # jadi tidak mungkin bentrok dengan tombol HUD.
                    # `game` ikut dikirim supaya panel tahu saat ada
                    # popup (upgrade tower, build, panel hero) yang
                    # menutupi tombol command - kalau tertutup, klik
                    # harus sampai ke popup, bukan "tembus" ke command.
                    hit = side.hit_test(action.pos, game=game)
                    if hit:
                        plat.vibrate(15)
                    if not hit:
                        hit = hud.hit_test(action.pos)
                if hit:
                    claimed.add(tid)
                    hud_mod.apply_hud_action(hit, ctx)
                # CATATAN v30: dulu di sini ada `elif side.blocks(...)`
                # yang mengklaim SEMUA sentuhan di area panel supaya
                # tidak tembus ke peta. Itu BUG: sejak popup upgrade
                # hero, popup tower, dan popup castle pindah ke panel,
                # klaim itu justru memblokir tombol-tombolnya sendiri -
                # semuanya jadi tidak bisa ditekan.
                #
                # Sekarang sentuhan di panel diteruskan seperti biasa
                # ke Game.handle_click(); yang mencegah "tembus ke
                # peta" adalah penjaga di _handle_left_click, yang
                # menolak klik di luar arena SETELAH semua tombol UI
                # diperiksa.
                continue

            if tid in claimed:
                if action.kind == "release":
                    claimed.discard(tid)
                continue

            if current_state == STATE_SPLASH:
                if action.kind in ("tap", "long_press"):
                    splash.skip()

            elif current_state == STATE_MENU:
                touch_mod.dispatch_to_menu(action, menu)

            elif current_state == STATE_GAME:
                if cine and action.kind == "tap":
                    hud_mod.apply_hud_action("skip", ctx)
                else:
                    touch_mod.dispatch_to_game(action, game)

            elif current_state == STATE_PAUSE:
                touch_mod.dispatch_to_menu(action, menu)

        if ctx.get("request_pause") and current_state == STATE_GAME:
            current_state = STATE_PAUSE
            menu.show_pause()

        # ─────────────────────────────── UPDATE + DRAW
        frame_timer.start("update")

        if current_state == STATE_SPLASH:
            now = pygame.time.get_ticks()
            dt = min(0.05, (now - splash_last) / 1000.0)
            splash_last = now
            splash.update(dt)
            _gambar_panel()
            frame_timer.start("draw")
            splash.draw()
            if splash.is_done():
                current_state = STATE_MENU

        elif current_state == STATE_MENU:
            sim_acc += min(clock.get_time(), 250)
            _n = 0
            while sim_acc >= FIXED_DT_MS and _n < MAX_CATCHUP:
                menu.update()
                sim_acc -= FIXED_DT_MS
                _n += 1
            if _n == 0:
                pass
            _gambar_panel()
            frame_timer.start("draw")
            menu.draw()

            if menu.action == "play":
                level = getattr(menu, 'selected_level', 1)
                game = Game(screen, level_number=level)
                __main__.game_instance = game
                current_state = STATE_GAME
                menu.action = None
                perf.clear_text_caches()
                sound_mgr.play_bgm('bgm_battle.wav', loop=True, fade_ms=1500)
            elif menu.action == "quit":
                running = False

        elif current_state == STATE_GAME:
            # Kejar waktu nyata: 1 langkah = 1/60 detik
            sim_acc += min(clock.get_time(), 250)   # buang hentakan
            sim_steps = 0
            while sim_acc >= FIXED_DT_MS and sim_steps < MAX_CATCHUP:
                game.update()
                sim_acc -= FIXED_DT_MS
                sim_steps += 1
            if sim_steps >= MAX_CATCHUP:
                # Mentok: frame ini lebih lambat dari 8 langkah.
                # Sisa akumulator TIDAK dibuang total (itu bikin waktu
                # game melompat/tersendat); disisakan setengah supaya
                # kejaran berlanjut halus di frame berikutnya.
                sim_acc = min(sim_acc * 0.5, FIXED_DT_MS * 3)
                sim_capped += 1
            debug.extra["sim"] = "%dx/frame  mentok %d" % (sim_steps,
                                                           sim_capped)

            _gambar_panel(game)
            frame_timer.start("draw")
            game.draw()
            perf.PHASES.mark("hud")
            hud.draw(screen, getattr(game, "animation_time", 0))
            perf.PHASES.end()

            if getattr(game, 'next_level_requested', False):
                from levels import get_next_level
                nxt = get_next_level(game.level_number)
                if nxt:
                    game = Game(screen, level_number=nxt)
                    __main__.game_instance = game
                    perf.clear_text_caches()
                    sound_mgr.play_bgm('bgm_battle.wav', loop=True,
                                       fade_ms=1500)
                else:
                    game.next_level_requested = False

            elif getattr(game, 'replay_requested', False):
                game = Game(screen, level_number=game.level_number,
                            is_replay=True)
                __main__.game_instance = game
                perf.clear_text_caches()
                sound_mgr.play_bgm('bgm_battle.wav', loop=True, fade_ms=1500)

            elif getattr(game, 'return_to_menu_requested', False):
                current_state = STATE_MENU
                menu.show_main()
                menu.action = None
                game = None
                __main__.game_instance = None
                perf.clear_text_caches()

        elif current_state == STATE_PAUSE:
            frame_timer.start("draw")
            if game:
                game.draw()
            sim_acc += min(clock.get_time(), 250)
            _n = 0
            while sim_acc >= FIXED_DT_MS and _n < MAX_CATCHUP:
                menu.update()
                sim_acc -= FIXED_DT_MS
                _n += 1
            menu.draw()

            if menu.action == "resume":
                current_state = STATE_GAME
                menu.action = None
            elif menu.action == "main_menu":
                current_state = STATE_MENU
                menu.show_main()
                menu.action = None
                game = None
                __main__.game_instance = None
            elif menu.action == "quit":
                running = False

        # ─────────────────────────────── OVERLAY DEBUG
        debug.update(clock, game)
        perf.PHASES.mark("overlay")
        debug.draw(screen, clock, game, touch)
        perf.PHASES.end()

        try:
            from mobile import blitwatch
            if blitwatch.enabled():
                blitwatch.new_frame()
        except Exception:
            pass

        frame_timer.start("flip")
        plat.present()
        frame_timer.stop()

        # ─────────────────────────────── FPS
        # Preset kualitas menentukan batas atas FPS di HP (LOW = 30).
        # Setting pemain hanya boleh MENURUNKAN, bukan menaikkan.
        try:
            from game_settings import GameSettings
            limit = GameSettings().fps_limit
        except Exception:
            limit = 0
        if not limit or limit <= 0:
            limit = perf.Quality.target_fps
        elif plat.TOUCH_MODE:
            limit = min(limit, perf.Quality.target_fps)
        clock.tick(limit)
        adaptive.update(clock.get_fps())

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
