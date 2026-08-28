# MAIN.PY - Entry Point dengan Controller Support
# ================================

import pygame
import sys
import _core  # noqa: E402  # muat semua bundle + pasang alias modul lama
from settings import *
from game import Game
from menu import Menu, MenuState
from controller_manager import ControllerManager, InputMode
from splash_screen import SplashScreen


def _snap_cursor_to_menu_button(controller, menu):
    """Snap cursor ke button terdekat di menu"""
    if not controller.is_controller_mode():
        return

    # Snap ke button terdekat di menu.buttons
    if hasattr(menu, 'buttons') and menu.buttons:
        controller.snap_to_nearest_button(menu.buttons)

def _menu_is_scrollable(menu):
    """True kalau layar menu sekarang punya list yang bisa di-scroll."""
    try:
        from menu import MenuState
        return menu.state in (MenuState.HERO_SHOP,
                              MenuState.LEVEL_SELECT)
    except Exception:
        return False


def main():
    pygame.init()
    pygame.display.set_caption(TITLE)

    # ═══ Init Sound System ═══
    from sound_manager import SoundManager
    sound_mgr = SoundManager()
    sound_mgr.load_all()
    sound_mgr.play_bgm('bgm_battle.wav', loop=True, fade_ms=3000)
    sound_mgr.play_ambient('ambient_forest', volume_mult=0.8)

    # ═══ Init Controller ═══
    controller = ControllerManager()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), vsync=1)
    clock = pygame.time.Clock()

    # ═══ GAME STATES ═══
    STATE_SPLASH = "splash"
    STATE_MENU = "menu"
    STATE_GAME = "game"
    STATE_PAUSE = "pause"

    current_state = STATE_SPLASH
    game = None
    menu = Menu(screen)
    menu.controller_mgr = controller  # Pass controller ke menu

    # ═══ SPLASH SCREEN (tampil sebelum menu) ═══
    splash = SplashScreen(screen)

    # Register global
    import __main__
    __main__.game_instance = None

    print("=" * 65)
    print("  MOBA TOWER DEFENSE")
    print("=" * 65)
    print()
    if controller.connected:
        info = controller.get_controller_info()
        print(f"  Controller: {info['name']}")
        print(f"  Type: {info['type']}")
    else:
        print("  Controller: Not detected")
    print()
    print("  Toggle input: Click 'INPUT' button in menu")
    print("=" * 65)

    # ═══ MAIN LOOP ═══
    from fps_counter import FPSCounter
    fps_counter = FPSCounter()

    splash_last_ticks = pygame.time.get_ticks()
    running = True
    while running:
        # ═══════════════════════════════════════
        # EVENT HANDLING (Keyboard + Mouse)
        # ═══════════════════════════════════════
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                # ← TAMBAH INI (toggle FPS counter, semua state)
                if event.key == pygame.K_F8:
                    fps_counter.toggle()
                if current_state == STATE_SPLASH:
                    splash.skip()
                elif current_state == STATE_MENU:
                    menu.handle_key(event.key)
                elif current_state == STATE_GAME:
                    if game and game.state != "playing":
                        # Victory/Defeat screen → delegate ke game_input
                        game.handle_key(event.key)
                    elif event.key == pygame.K_ESCAPE:
                        if not (game.shop_open or game.popup_target
                                or game.build_popup_slot
                                or game.selected_hero
                                or game.selected_tower):
                            current_state = STATE_PAUSE
                            menu.show_pause()
                            # Lepas hold tactical (KEYUP bisa jatuh di
                            # layar pause - jangan sampai nyangkut).
                            if getattr(game, 'tactical', None):
                                game.tactical.hold_end()
                        else:
                            game.handle_key(event.key)
                    else:
                        game.handle_key(event.key)
                elif current_state == STATE_PAUSE:
                    menu.handle_key(event.key)

            elif event.type == pygame.KEYUP:
                # Lepas tactical command yang sedang di-hold lewat
                # tuts G/T/C/B/D/F (perintah terus aktif selama
                # tuts ditahan, berhenti saat dilepas).
                if current_state == STATE_GAME and game:
                    game.handle_key_up(event.key)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Mouse click hanya kalau bukan controller mode
                if not controller.is_controller_mode():
                    if current_state == STATE_SPLASH:
                        splash.skip()
                    elif current_state == STATE_MENU:
                        menu.handle_click(event.pos, event.button)
                    elif current_state == STATE_GAME:
                        game.handle_click(event.pos, event.button)
                    elif current_state == STATE_PAUSE:
                        menu.handle_click(event.pos, event.button)

        # ═══════════════════════════════════════
        # CONTROLLER (hanya kalau controller mode aktif)
        # ═══════════════════════════════════════
        if controller.is_controller_mode() and controller.connected:
            controller.update()  # Update cursor position
            actions = controller.get_pressed_actions()

            for action in actions:
                # ─── SPLASH ───
                if current_state == STATE_SPLASH:
                    # Tombol apa pun di controller -> skip splash
                    splash.skip()

                # ─── MENU ───
                if current_state == STATE_MENU:
                    if action == 'confirm':
                        menu.handle_click(
                            controller.get_cursor_pos(), 1)
                    elif action in ('cancel', 'back'):
                        menu.handle_key(pygame.K_ESCAPE)
                    elif action == 'stick_right':
                        # R3 = snap cursor ke tombol terdekat
                        _snap_cursor_to_menu_button(controller, menu)
                    elif action == 'stick_left':
                        fps_counter.toggle()

                    # ═══ SCROLL (right stick) ═══
                    elif action == 'scroll_up':
                        menu.handle_click(
                            controller.get_cursor_pos(), 4)
                    elif action == 'scroll_down':
                        menu.handle_click(
                            controller.get_cursor_pos(), 5)

                    # ═══ D-PAD BIG JUMP untuk menu screens ═══
                    # (Level Select, Slot Selection, Hero Shop pakai grid)
                    elif action == 'dpad_up':
                        if _menu_is_scrollable(menu):
                            # Di layar shop: d-pad = scroll list
                            menu.handle_click(
                                controller.get_cursor_pos(), 4)
                        else:
                            controller.cursor_y = max(
                                0, controller.cursor_y - 150)
                            _snap_cursor_to_menu_button(controller, menu)
                    elif action == 'dpad_down':
                        if _menu_is_scrollable(menu):
                            menu.handle_click(
                                controller.get_cursor_pos(), 5)
                        else:
                            controller.cursor_y = min(
                                SCREEN_HEIGHT, controller.cursor_y + 150)
                            _snap_cursor_to_menu_button(controller, menu)
                    elif action == 'dpad_left':
                        controller.cursor_x = max(0,
                                                  controller.cursor_x - 300)
                        _snap_cursor_to_menu_button(controller, menu)
                    elif action == 'dpad_right':
                        controller.cursor_x = min(SCREEN_WIDTH,
                                                  controller.cursor_x + 300)
                        _snap_cursor_to_menu_button(controller, menu)

                # ─── GAME ───
                elif current_state == STATE_GAME:
                    if action == 'confirm':
                        # ═══ CINEMATIC SKIP dengan A button ═══
                        # Kalau ada cinematic aktif, A button skip
                        if game.level_intro and game.level_intro.is_active():
                            game.level_intro.handle_skip(key=pygame.K_SPACE)
                            continue
                        elif game.boss_intro and game.boss_intro.is_active():
                            game.boss_intro.handle_skip(key=pygame.K_SPACE)
                            continue
                        elif game.boss_death and \
                                game.boss_death.celebration_active:
                            game.boss_death.handle_skip(key=pygame.K_SPACE)
                            continue

                        # ═══ VICTORY SCREEN: PLAY NEXT LEVEL (shortcut A) ═══
                        if game.state == "victory":
                            if 'play_next_level' in game.ui_buttons:
                                from levels import get_next_level
                                next_lvl = get_next_level(game.level_number)
                                if next_lvl:
                                    game.next_level_requested = True
                                    controller.rumble(0.4, 10)
                                    continue

                        # Default: click at cursor
                        game.handle_click(
                            controller.get_cursor_pos(), 1)

                    elif action == 'cancel':
                        # B = close UI berurutan (stack)
                        if game.shop_open:
                            game.shop_open = False
                        elif game.build_popup_slot:
                            game.close_build_popup()
                        elif game.popup_target:
                            game.close_popup()
                        elif game.selected_hero:
                            game.selected_hero.selected = False
                            game.selected_hero = None
                        elif game.selected_tower:
                            game.selected_tower.selected = False
                            game.selected_tower = None
                        else:
                            current_state = STATE_PAUSE
                            menu.show_pause()

                    elif action == 'skill_q':
                        if game.state != "playing":
                            # Layar victory/defeat: X/Square = REPLAY
                            # (padanan tombol R di keyboard)
                            game.handle_key(pygame.K_r)
                        else:
                            game.handle_key(pygame.K_q)
                        controller.rumble(0.4, 10)
                    elif action == 'skill_w':
                        game.handle_key(pygame.K_w)
                        controller.rumble(0.4, 10)
                    elif action == 'skill_e':
                        game.handle_key(pygame.K_e)
                        controller.rumble(0.4, 10)
                    elif action == 'skill_r':
                        if game.state == "victory":
                            # Layar victory: RB/R1 = NEXT LEVEL
                            # (padanan tombol N di keyboard)
                            game.handle_key(pygame.K_n)
                        else:
                            game.handle_key(pygame.K_r)
                        controller.rumble(0.8, 20)
                    elif action == 'start':
                        current_state = STATE_PAUSE
                        menu.show_pause()
                        # Lepas hold tactical (jangan nyangkut di pause)
                        if getattr(game, 'tactical', None):
                            game.tactical.hold_end()
                    elif action == 'back':
                        # VIEW/SELECT = kembali ke menu (padanan ESC
                        # di layar victory/defeat)
                        if game.state != "playing":
                            game.return_to_menu_requested = True
                        else:
                            current_state = STATE_PAUSE
                            menu.show_pause()
                            # Lepas hold tactical (jangan nyangkut)
                            if getattr(game, 'tactical', None):
                                game.tactical.hold_end()
                    elif action == 'left_trigger':
                        game.handle_key(pygame.K_h)
                    elif action == 'right_trigger':
                        game.handle_click(
                            controller.get_cursor_pos(), 3)
                    elif action == 'stick_left':
                        fps_counter.toggle()
                    elif action == 'stick_right':
                        # R3 = snap cursor ke tombol UI terdekat
                        if getattr(game, 'ui_buttons', None):
                            controller.snap_to_nearest_button(
                                game.ui_buttons)
                    elif action == 'scroll_up':
                        game.handle_click(
                            controller.get_cursor_pos(), 4)
                    elif action == 'scroll_down':
                        game.handle_click(
                            controller.get_cursor_pos(), 5)

                    # D-pad: quick cursor jump
                    # (kalau shop kebuka -> scroll list, lebih berguna)
                    elif action == 'dpad_up':
                        if game.shop_open:
                            game.handle_click(
                                controller.get_cursor_pos(), 4)
                        else:
                            controller.cursor_y = max(
                                0, controller.cursor_y - 80)
                    elif action == 'dpad_down':
                        if game.shop_open:
                            game.handle_click(
                                controller.get_cursor_pos(), 5)
                        else:
                            controller.cursor_y = min(
                                SCREEN_HEIGHT, controller.cursor_y + 80)
                    elif action == 'dpad_left':
                        controller.cursor_x = max(0,
                                                  controller.cursor_x - 100)
                    elif action == 'dpad_right':
                        controller.cursor_x = min(SCREEN_WIDTH,
                                                  controller.cursor_x + 100)
                # ─── PAUSE ───
                elif current_state == STATE_PAUSE:
                    if action == 'confirm':
                        menu.handle_click(
                            controller.get_cursor_pos(), 1)
                    elif action in ('cancel', 'start'):
                        menu.action = "resume"
                    elif action == 'back':
                        menu.action = "resume"
                    elif action == 'stick_right':
                        _snap_cursor_to_menu_button(controller, menu)
        # ═══════════════════════════════════════
        # STATE UPDATE & DRAW
        # ═══════════════════════════════════════

        # ─── SPLASH STATE ───
        if current_state == STATE_SPLASH:
            now_ticks = pygame.time.get_ticks()
            dt_splash = min(0.05, (now_ticks - splash_last_ticks) / 1000.0)
            splash_last_ticks = now_ticks
            splash.update(dt_splash)
            splash.draw()

            if splash.is_done():
                current_state = STATE_MENU

        # ─── MENU STATE ───
        elif current_state == STATE_MENU:
            menu.update()
            menu.draw()

            if menu.action == "play":
                # Load level yang dipilih
                selected_level = getattr(menu, 'selected_level', 1)
                game = Game(screen, level_number=selected_level)
                game.controller_mgr = controller
                __main__.game_instance = game
                current_state = STATE_GAME
                menu.action = None
                sound_mgr.play_bgm('bgm_battle.wav', loop=True,
                                   fade_ms=1500)
            elif menu.action == "quit":
                running = False

        # ─── GAME STATE ───
        elif current_state == STATE_GAME:
            game.update()
            game.draw()

            # ═══ HANDLE LEVEL TRANSITIONS ═══
            if game and getattr(game, 'next_level_requested', False):
                from levels import get_next_level
                next_lvl = get_next_level(game.level_number)
                if next_lvl:
                    game = Game(screen, level_number=next_lvl)
                    game.controller_mgr = controller
                    __main__.game_instance = game
                    sound_mgr.play_bgm('bgm_battle.wav', loop=True,
                                       fade_ms=1500)

            if game and getattr(game, 'replay_requested', False):
                lvl = game.level_number
                game = Game(screen, level_number=lvl, is_replay=True)
                game.controller_mgr = controller
                __main__.game_instance = game
                sound_mgr.play_bgm('bgm_battle.wav', loop=True,
                                   fade_ms=1500)

            if game and getattr(game, 'return_to_menu_requested', False):
                current_state = STATE_MENU
                menu.show_main()
                menu.action = None
                game = None
                __main__.game_instance = None

        # ─── PAUSE STATE ───
        elif current_state == STATE_PAUSE:
            if game:
                game.draw()
            menu.update()
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

        # ═══ CONTROLLER CURSOR + HOVER HIGHLIGHT ═══
        if (controller.is_controller_mode() and controller.connected
                and current_state != STATE_SPLASH):
            anim_time = 0
            if game and current_state == STATE_GAME:
                anim_time = game.animation_time

            # Find UI button yang lagi di-hover (untuk highlight)
            hover_rect = None

            if current_state == STATE_MENU:
                if hasattr(menu, 'buttons') and menu.buttons:
                    hover_rect = controller.find_ui_button_at_cursor(
                        menu.buttons)
            elif current_state == STATE_GAME:
                if game and game.ui_buttons:
                    hover_rect = controller.find_ui_button_at_cursor(
                        game.ui_buttons)
            elif current_state == STATE_PAUSE:
                if hasattr(menu, 'buttons') and menu.buttons:
                    hover_rect = controller.find_ui_button_at_cursor(
                        menu.buttons)

            controller.draw_cursor(screen, anim_time,
                                   hover_rect=hover_rect)

        fps_counter.update(clock)
        fps_counter.draw(screen)

        pygame.display.flip()

        # ═══ FPS COUNTER (update + draw) ═══
        fps_counter.update(clock)
        fps_counter.draw(screen)

        pygame.display.flip()

        # ═══ FPS LIMIT (pakai clock yang sudah ada) ═══
        from game_settings import GameSettings
        _settings = GameSettings()
        fps_limit = _settings.fps_limit if _settings.fps_limit > 0 else 60
        if fps_limit > 0:
            clock.tick(fps_limit)
        else:
            clock.tick()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()




# ================================
