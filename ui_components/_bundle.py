"""
ui_components/_bundle.py - semua komponen UI

Gabungan dari 11 file:
  - base_ui.py               level modul
  - hero_portraits.py        namespace _NS_hero_portraits
  - build_popup.py           namespace _NS_build_popup
  - build_slots.py           namespace _NS_build_slots
  - hero_panel.py            namespace _NS_hero_panel
  - hero_shop.py             namespace _NS_hero_shop
  - hover_indicators.py      namespace _NS_hover_indicators
  - notification.py          namespace _NS_notification
  - overlay.py               namespace _NS_overlay
  - popup_renderer.py        namespace _NS_popup_renderer
  - shop_hints.py            namespace _NS_shop_hints

Modul dibungkus kelas `_NS_<nama>` supaya simbol bernama
sama tidak saling menimpa.

Di level modul (tidak dibungkus): base_ui

Duplikat yang dibuang: hero_panel (237 baris)

File asli dihapus; nama submodul didaftarkan ke
sys.modules oleh __init__.py, jadi semua baris
`from ui_components.<modul> import ...` tetap jalan.
"""
import pygame
import math
from settings import *


# ====================================================================
# base_ui.py  (dependensi internal - modul lain mengimpor simbolnya langsung)
# ====================================================================
# ui_components/base_ui.py
# Base class untuk semua UI components
# ================================



class BaseUIComponent:
    """
    Base class untuk semua UI component.
    Setiap component inherit dan override draw().
    """

    def __init__(self, ui_renderer):
        self.ui = ui_renderer      # UIRenderer instance
        self.game = ui_renderer.game  # shortcut ke game

    # ═══════════════════════════════════════
    # SHARED UTILITIES
    # ═══════════════════════════════════════

    def draw(self, surface):
        """Override di subclass"""
        pass

    def _draw_shadow_rect(self, surface, rect, alpha=150,
                          border_radius=8, offset=(5, 5)):
        """Reusable shadow drawing"""
        shadow_surf = pygame.Surface(
            (rect.width + offset[0] * 2,
             rect.height + offset[1] * 2), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, alpha),
                         (offset[0], offset[1],
                          rect.width, rect.height),
                         border_radius=border_radius)
        surface.blit(shadow_surf,
                     (rect.x - offset[0],
                      rect.y - offset[1]))

    def _draw_hp_bar(self, surface, x, y, w, h, hp_ratio,
                      show_bg=True):
        """Reusable HP bar drawing"""
        if show_bg:
            pygame.draw.rect(surface, (40, 0, 0), (x, y, w, h))

        fill = int(w * hp_ratio)
        if fill > 0:
            if hp_ratio > 0.5:
                hp_color = GREEN
            elif hp_ratio > 0.25:
                hp_color = YELLOW
            else:
                hp_color = RED
            pygame.draw.rect(surface, hp_color, (x, y, fill, h))

        pygame.draw.rect(surface, WHITE, (x, y, w, h), 1)

    def _draw_close_button(self, surface, x, y, size=20,
                            button_id='close', style='rect'):
        """
        Reusable close button (X).
        style: 'rect' atau 'circle'
        """
        close_rect = pygame.Rect(x, y, size, size)

        # Hover detection
        mx, my = pygame.mouse.get_pos()
        is_hover = close_rect.collidepoint(mx, my)

        if style == 'circle':
            # Round close button
            if is_hover:
                glow_surf = pygame.Surface(
                    (size + 10, size + 10), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (255, 80, 80, 100),
                                   ((size + 10) // 2,
                                    (size + 10) // 2),
                                   size // 2 + 3)
                surface.blit(glow_surf, (x - 5, y - 5))

            pygame.draw.circle(surface,
                               (200, 40, 40) if is_hover
                               else (150, 30, 30),
                               close_rect.center, size // 2)
            pygame.draw.circle(surface, (255, 255, 255),
                               close_rect.center, size // 2, 2)

            # X symbol
            offset = size // 4
            pygame.draw.line(surface, (255, 255, 255),
                             (close_rect.centerx - offset,
                              close_rect.centery - offset),
                             (close_rect.centerx + offset,
                              close_rect.centery + offset), 3)
            pygame.draw.line(surface, (255, 255, 255),
                             (close_rect.centerx + offset,
                              close_rect.centery - offset),
                             (close_rect.centerx - offset,
                              close_rect.centery + offset), 3)
        else:
            # Rect close button
            if is_hover:
                pygame.draw.rect(surface, (255, 60, 60), close_rect,
                                 border_radius=3)
                pygame.draw.rect(surface, WHITE, close_rect, 2,
                                 border_radius=3)
            else:
                pygame.draw.rect(surface, RED, close_rect,
                                 border_radius=3)
                pygame.draw.rect(surface, WHITE, close_rect, 1,
                                 border_radius=3)

            close_font = pygame.font.Font(None, 22)
            close_t = close_font.render("X", True, WHITE)
            close_text_rect = close_t.get_rect(center=close_rect.center)
            surface.blit(close_t, close_text_rect)

        # Register button
        self.game.ui_buttons[button_id] = close_rect
        return close_rect



# ================================


# ====================================================================
# hero_portraits.py
# ====================================================================
class _NS_hero_portraits:
    """Namespace hero_portraits - isi asli tidak diubah."""

    # ================================
    # GANTI SELURUH FILE ui_components/hero_portraits.py
    # 100% AUTO-GENERATE - ZERO manual portraits
    # ================================



    class HeroPortraits:
        """
        100% auto-generate portraits dari existing renderers.
        Tidak perlu manual portrait sama sekali.
        Tambah boss/hero baru = portrait otomatis muncul.
        """

        _cache = {}

        @staticmethod
        def draw(surface, hero_type, cx, cy, stats, owned=False):
            """Draw portrait - 100% auto dari renderer"""
            cache_key = (hero_type, owned)

            if cache_key not in _NS_hero_portraits.HeroPortraits._cache:
                portrait = _NS_hero_portraits.HeroPortraits._try_auto_render(
                    hero_type, stats, owned)
                _NS_hero_portraits.HeroPortraits._cache[cache_key] = portrait

            cached = _NS_hero_portraits.HeroPortraits._cache[cache_key]
            if cached is not None:
                rect = cached.get_rect(center=(cx, cy))
                surface.blit(cached, rect)
                return

            # Final fallback
            color_main = stats["color"]
            color_dark = stats["color_dark"]
            if owned:
                # Redupkan, bukan abu-abu rata, biar siluet tetap kebaca
                color_main = tuple(int(c * 0.45) for c in color_main)
                color_dark = tuple(int(c * 0.45) for c in color_dark)
            _NS_hero_portraits.HeroPortraits._draw_generic(
                surface, cx, cy, color_main, color_dark)

        @staticmethod
        def _try_auto_render(hero_type, stats, owned):
            """Auto render portrait dari boss atau hero renderer"""
            pw, ph = 60, 70

            # ═══ TRY 1: Boss renderer ═══
            portrait = _NS_hero_portraits.HeroPortraits._try_boss_renderer(
                hero_type, stats, pw, ph, owned)
            if portrait:
                return portrait

            # ═══ TRY 2: Hero renderer ═══
            portrait = _NS_hero_portraits.HeroPortraits._try_hero_renderer(
                hero_type, stats, pw, ph, owned)
            if portrait:
                return portrait

            # ═══ TRY 3: Cari alias (misal drakar_true → drakar) ═══
            base_type = hero_type.replace("_true", "")
            if base_type != hero_type:
                portrait = _NS_hero_portraits.HeroPortraits._try_boss_renderer(
                    base_type, stats, pw, ph, owned)
                if portrait:
                    return portrait

            return None

        @staticmethod
        def _try_boss_renderer(hero_type, stats, pw, ph, owned):
            """Coba render dari bosses/{hero_type}.py"""
            try:
                draw_func = None

                # Cek BOSS_RENDERERS registry dulu
                try:
                    from heroes import BOSS_RENDERERS
                    draw_func = BOSS_RENDERERS.get(hero_type)
                except Exception:
                    pass

                # Fallback: import langsung
                if not draw_func:
                    import importlib
                    try:
                        module = importlib.import_module(
                            f"bosses.{hero_type}")
                    except ImportError:
                        return None

                    # Coba nama fungsi standar dulu
                    func_name = f"draw_{hero_type}"
                    if hasattr(module, func_name):
                        draw_func = getattr(module, func_name)
                    else:
                        # Sebagian file boss nama fungsinya beda dari
                        # nama file (mis. ancient_apparition.py ->
                        # draw_apparition). Cari kandidat lain daripada
                        # jatuh ke portrait generic.
                        for cand in dir(module):
                            if (cand.startswith("draw_")
                                    and cand != "draw_boss"):
                                draw_func = getattr(module, cand)
                                break
                        if not draw_func and hasattr(module, "draw_boss"):
                            draw_func = getattr(module, "draw_boss")

                if not draw_func:
                    return None

                # Render
                canvas_w, canvas_h = 200, 200
                canvas = pygame.Surface((canvas_w, canvas_h),
                                         pygame.SRCALPHA)

                fake = _NS_hero_portraits._make_fake_boss(hero_type, canvas_w, canvas_h)

                try:
                    draw_func(canvas, fake, fake.x, fake.y)
                except Exception as e:
                    print(f"[PORTRAIT] Boss render error "
                          f"{hero_type}: {e}")
                    return None

                return _NS_hero_portraits.HeroPortraits._crop_and_scale(
                    canvas, pw, ph, owned)

            except Exception:
                return None

        @staticmethod
        def _try_hero_renderer(hero_type, stats, pw, ph, owned):
            """Coba render dari heroes/{hero_type}.py"""
            try:
                draw_func = None

                try:
                    from heroes import HERO_RENDERERS
                    draw_func = HERO_RENDERERS.get(hero_type)
                except Exception:
                    pass

                if not draw_func:
                    return None

                canvas_w, canvas_h = 160, 160
                canvas = pygame.Surface((canvas_w, canvas_h),
                                         pygame.SRCALPHA)

                fake = _NS_hero_portraits._make_fake_hero(hero_type, stats,
                                        canvas_w, canvas_h)

                try:
                    draw_func(canvas, fake,
                              int(fake.x), int(fake.y))
                except Exception as e:
                    print(f"[PORTRAIT] Hero render error "
                          f"{hero_type}: {e}")
                    return None

                return _NS_hero_portraits.HeroPortraits._crop_and_scale(
                    canvas, pw, ph, owned)

            except Exception:
                return None

        @staticmethod
        def _crop_and_scale(canvas, target_w, target_h, owned):
            """Crop non-transparent area lalu scale"""
            cw, ch = canvas.get_size()
            min_x, min_y = cw, ch
            max_x, max_y = 0, 0

            for sy in range(0, ch, 2):
                for sx in range(0, cw, 2):
                    pixel = canvas.get_at((sx, sy))
                    if pixel[3] > 10:
                        min_x = min(min_x, sx)
                        min_y = min(min_y, sy)
                        max_x = max(max_x, sx)
                        max_y = max(max_y, sy)

            if max_x <= min_x or max_y <= min_y:
                return None

            pad = 4
            min_x = max(0, min_x - pad)
            min_y = max(0, min_y - pad)
            max_x = min(cw, max_x + pad)
            max_y = min(ch, max_y + pad)

            crop_w = max_x - min_x
            crop_h = max_y - min_y
            if crop_w <= 0 or crop_h <= 0:
                return None

            cropped = canvas.subsurface(
                (min_x, min_y, crop_w, crop_h)).copy()

            scale_x = target_w / crop_w
            scale_y = target_h / crop_h
            scale = min(scale_x, scale_y, 1.0)

            new_w = max(1, int(crop_w * scale))
            new_h = max(1, int(crop_h * scale))

            scaled = pygame.transform.smoothscale(
                cropped, (new_w, new_h))

            if owned:
                scaled = _NS_hero_portraits.HeroPortraits._apply_grayscale(scaled)

            return scaled

        @staticmethod
        def _apply_grayscale(surface):
            """Convert surface ke grayscale"""
            gray = surface.copy()
            try:
                arr = pygame.surfarray.pixels3d(gray)
                gray_vals = (arr[:, :, 0] * 0.299 +
                             arr[:, :, 1] * 0.587 +
                             arr[:, :, 2] * 0.114).astype('uint8')
                arr[:, :, 0] = gray_vals
                arr[:, :, 1] = gray_vals
                arr[:, :, 2] = gray_vals
                del arr
            except Exception:
                gray.fill((80, 80, 80),
                          special_flags=pygame.BLEND_RGB_MULT)
            return gray

        @staticmethod
        def clear_cache():
            """Clear cache saat level/settings change"""
            _NS_hero_portraits.HeroPortraits._cache.clear()

        @staticmethod
        def _draw_generic(surface, cx, cy, color_main, color_dark):
            """Ultimate fallback kalau renderer tidak ada"""
            for i in range(5):
                px = cx - 8 + i * 4
                pygame.draw.polygon(surface, (255, 200, 60), [
                    (px, cy - 16), (px + 2, cy - 22),
                    (px + 4, cy - 16)])
            pygame.draw.circle(surface, (0, 0, 0), (cx, cy - 8), 10)
            pygame.draw.circle(surface, color_main, (cx, cy - 8), 9)
            pygame.draw.circle(surface, (255, 255, 255),
                               (cx - 3, cy - 10), 1)
            pygame.draw.circle(surface, (255, 255, 255),
                               (cx + 3, cy - 10), 1)
            pygame.draw.rect(surface, color_dark,
                             (cx - 10, cy + 2, 20, 18),
                             border_radius=4)
            pygame.draw.rect(surface, color_main,
                             (cx - 9, cy + 3, 18, 16),
                             border_radius=3)
            pygame.draw.circle(surface, (255, 220, 100),
                               (cx, cy + 10), 3)
            pygame.draw.circle(surface, (255, 255, 255),
                               (cx, cy + 10), 1)


    # ═══════════════════════════════════════════════════════
    # FAKE ENTITY FACTORIES
    # ═══════════════════════════════════════════════════════

    class _FakeEntity:
        """
        Fake entity untuk render portrait.

        PENTING: JANGAN pakai __getattr__ yang mengembalikan 0 untuk
        atribut apapun. Renderer boss memakai pola:

            if not hasattr(boss, "_xx_projectiles"):
                boss._xx_projectiles = []
            for p in boss._xx_projectiles:   # <- meledak kalau isinya 0

        Kalau __getattr__ selalu sukses, hasattr() selalu True, list
        tidak pernah diinisialisasi, lalu `for p in 0` -> TypeError.
        Itu bikin 18 dari 28 portrait boss gagal diam-diam.

        Solusi: biarkan atribut tak dikenal raise AttributeError seperti
        object biasa, supaya guard hasattr() di renderer bekerja normal.
        """

        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)


    def _make_fake_boss(hero_type, canvas_w, canvas_h):
        """
        Fake boss object untuk portrait render.

        Atribut list/cache internal renderer (mis. _ab_projectiles,
        _razak_patches) SENGAJA tidak diisi di sini, supaya guard
        `if not hasattr(...)` di renderer jalan dan menginisialisasi
        list-nya sendiri.
        """
        return _NS_hero_portraits._FakeEntity(
            x=canvas_w // 2,
            y=canvas_h // 2 + 20,
            hp=1000,
            max_hp=1000,
            damage=50,
            base_damage=50,
            range=100,
            speed=1.0,
            attack_cooldown=40,
            timer=0,
            attack_timer=0,
            direction=1,
            facing=1,
            pulse=0.5,
            anim_time=0,
            target=None,
            alive=True,
            boss_type=hero_type,
            hero_type=hero_type,
            boss_class="mini",
            team="blue",
            radius=30,
            level=1,
            selected=False,
            active_skill=None,
            active_skill_timer=0,
            # Skill state yang dibaca langsung (bukan lewat hasattr)
            flux_target=None,
            flux_active_timer=0,
            vortex_x=0,
            vortex_y=0,
            vortex_active_timer=0,
            mana_void_x=0,
            mana_void_y=0,
            blink_from_x=0,
            blink_from_y=0,
            rage_active=False,
            rage_timer=0,
            defense_boost=False,
            defense_timer=0,
            clones_active_timer=0,
            clones_positions=[],
            w_target_x=0,
            w_target_y=0,
            w_dir_x=1,
            w_dir_y=0,
            r_dir_x=1,
            r_dir_y=0,
            cold_feet_target_x=0,
            cold_feet_target_y=0,
            shield_active=False,
            shield_timer=0,
            arcane_buff_active=False,
            arcane_buff_timer=0,
            dragon_form_active=False,
            dragon_form_timer=0,
            dragon_blood_active=False,
            dragon_blood_timer=0,
            hurt_flash_timer=0,
            entrance_timer=0,
            ability_active=False,
            ability_active_timer=0,
        )


    def _make_fake_hero(hero_type, stats, canvas_w, canvas_h):
        """Buat fake hero object untuk portrait render"""
        fake = _NS_hero_portraits._FakeEntity()
        fake.x = float(canvas_w // 2)
        fake.y = float(canvas_h // 2 + 10)
        fake.hero_type = hero_type
        fake.hp = stats.get("hp", 500)
        fake.max_hp = fake.hp
        fake.damage = stats.get("damage", 30)
        fake.range = stats.get("range", 100)
        fake.attack_cooldown = stats.get("attack_cooldown", 40)
        fake.attack_timer = 0
        fake.speed = stats.get("speed", 1.5)
        fake.facing = 1
        fake.direction = 1      # alias Boss-compat
        fake.timer = 0          # alias Boss-compat
        fake.boss_type = hero_type
        fake.boss_class = "mini"
        fake.active_skill = None
        fake.active_skill_timer = 0
        fake.pulse = 0.5
        fake.target = None
        fake.alive = True
        fake.team = "blue"
        fake.radius = 16
        fake.color = stats["color"]
        fake.color_dark = stats["color_dark"]
        fake.level = 1
        fake.selected = False
        fake.skill_active = False
        fake.skill_timer = 0
        fake.skill_cooldown_max = 300
        fake.skill_data = stats
        fake.is_retreating = False
        fake.kills = 0
        fake.deaths = 0
        fake.name = stats.get("name", hero_type)
        fake.title = stats.get("title", "")
        fake.walk_cycle = 0
        fake.is_moving = False
        fake.anim_time = 0

        # Hero-specific skill states (semua False/0)
        skill_attrs = [
            '_blade_fury_active', '_blade_fury_timer',
            '_omnislash_active', '_omnislash_timer',
            '_heal_ward_active', '_heal_ward_timer',
            '_heal_ward_pos',
            '_focus_fire_active', '_focus_fire_timer',
            '_powershot_charging', '_powershot_timer',
            '_shackle_active', '_shackle_timer',
            '_shackle_target',
            '_sanity_eclipse_active', '_sanity_eclipse_timer',
            '_astral_prison_active', '_astral_prison_timer',
            '_astral_prison_target',
            '_essence_flux_active', '_essence_flux_timer',
            '_windrun_active', '_windrun_timer',
            '_wind_wall_timer',
            '_ulti_active', '_ulti_timer',
            '_is_dashing', '_dash_timer',
            '_q_stack', '_q_reset_timer',
            '_bristleback_active', '_bristleback_timer',
            '_warpath_active', '_warpath_timer',
            '_spraying_quills', '_spray_timer',
            '_viscous_nose_active', '_viscous_nose_timer',
            '_shadow_realm_active', '_shadow_realm_timer',
            '_bedlam_active', '_bedlam_timer',
            '_bramble_active', '_bramble_timer',
            '_curse_active', '_curse_timer',
            '_curse_target',
            '_crit_buff_active', '_crit_buff_timer',
            '_original_speed', '_original_damage',
            '_original_attack_cd',
            '_rage_active', '_rage_timer',
            '_war_cry_timer',
            '_fortify_active', '_fortify_timer',
            '_holy_shield_active', '_holy_shield_timer',
        ]

        for attr in skill_attrs:
            if attr.endswith('_pos'):
                setattr(fake, attr, (0, 0))
            elif attr.endswith('_target'):
                setattr(fake, attr, None)
            elif 'active' in attr or 'charging' in attr \
                    or 'dashing' in attr or 'spraying' in attr:
                setattr(fake, attr, False)
            else:
                setattr(fake, attr, 0)

        # Movement detection
        fake._last_x = fake.x
        fake._last_y = fake.y

        return fake

# ====================================================================
# build_popup.py
# ====================================================================
class _NS_build_popup:
    """Namespace build_popup - isi asli tidak diubah."""

    # ui_components/build_popup.py
    # Popup untuk pilih tipe tower saat build
    # ================================



    class BuildPopup(BaseUIComponent):
        """
        Popup dengan 4 button pilih tower type:
        Archer, Cannon, Ice, Mage
        """

        def draw(self, surface):
            """Draw build popup"""
            g = self.game
            slot = g.build_popup_slot

            if not slot:
                return

            popup_w = 300
            popup_h = 200

            px = int(slot['x']) - popup_w // 2
            py = int(slot['y']) - popup_h - 30

            # Clamp posisi
            if px < 10:
                px = 10
            if px + popup_w > SCREEN_WIDTH - 10:
                px = SCREEN_WIDTH - popup_w - 10
            if py < 10:
                py = int(slot['y']) + 30

            # Line pointer ke slot
            pygame.draw.line(surface, GOLD,
                             (px + popup_w // 2, py + popup_h),
                             (int(slot['x']), int(slot['y']) - 10), 2)

            # Shadow
            shadow_surf = pygame.Surface((popup_w + 10, popup_h + 10),
                                         pygame.SRCALPHA)
            pygame.draw.rect(shadow_surf, (0, 0, 0, 150),
                             (5, 5, popup_w, popup_h), border_radius=8)
            surface.blit(shadow_surf, (px - 5, py - 5))

            # Background
            pygame.draw.rect(surface, (25, 30, 45),
                             (px, py, popup_w, popup_h),
                             border_radius=8)
            pygame.draw.rect(surface, GOLD,
                             (px, py, popup_w, popup_h),
                             2, border_radius=8)

            # Title
            title = self.ui.font_medium.render(
                "BUILD TOWER", True, YELLOW)
            title_rect = title.get_rect(
                center=(px + popup_w // 2, py + 18))
            surface.blit(title, title_rect)

            # Gold info
            gold_font = pygame.font.Font(None, 16)
            gold_text = gold_font.render(f"Your Gold: {g.gold}G",
                                         True, GOLD)
            surface.blit(gold_text, (px + 15, py + 40))

            # Close button (X)
            self._draw_close_button(surface,
                                     px + popup_w - 25, py + 5,
                                     size=20,
                                     button_id='build_close',
                                     style='rect')

            # Tower type buttons (2x2 grid)
            self._draw_tower_buttons(surface, px, py, popup_w)

        def _draw_tower_buttons(self, surface, px, py, popup_w):
            """Draw 4 tower type buttons"""
            g = self.game

            tower_types = [
                ('archer', 'Archer', 'Fast, single target',
                 TOWER_TYPE_COLORS['archer']['main']),
                ('cannon', 'Cannon', 'AOE splash damage',
                 TOWER_TYPE_COLORS['cannon']['main']),
                ('ice', 'Ice', 'Slow enemies',
                 TOWER_TYPE_COLORS['ice']['main']),
                ('mage', 'Mage', 'Multi-target chain',
                 TOWER_TYPE_COLORS['mage']['main']),
            ]

            cost = 100
            can_afford = g.gold >= cost

            btn_w = (popup_w - 40) // 2
            btn_h = 55

            for i, (ttype, name, desc, color) in enumerate(tower_types):
                col = i % 2
                row = i // 2

                bx = px + 15 + col * (btn_w + 10)
                by = py + 60 + row * (btn_h + 8)

                bg_color = color if can_afford else DARK_GRAY
                btn_rect = pygame.Rect(bx, by, btn_w, btn_h)
                pygame.draw.rect(surface, bg_color, btn_rect,
                                 border_radius=4)
                pygame.draw.rect(surface, WHITE, btn_rect, 2,
                                 border_radius=4)

                # Name
                name_font = pygame.font.Font(None, 20)
                name_t = name_font.render(name, True,
                                          WHITE if can_afford else GRAY)
                surface.blit(name_t, (bx + 8, by + 5))

                # Description
                desc_font = pygame.font.Font(None, 13)
                desc_t = desc_font.render(desc, True,
                                          WHITE if can_afford else GRAY)
                surface.blit(desc_t, (bx + 8, by + 24))

                # Cost
                cost_font = pygame.font.Font(None, 16)
                cost_t = cost_font.render(f"{cost}G", True,
                                          GOLD if can_afford else GRAY)
                surface.blit(cost_t, (bx + 8, by + 38))

                g.ui_buttons[f'build_{ttype}'] = btn_rect




    # ================================


# ====================================================================
# build_slots.py
# ====================================================================
class _NS_build_slots:
    """Namespace build_slots - isi asli tidak diubah."""

    # ui_components/build_slots.py
    # Build slot markers (empty spots untuk build tower)
    # ================================



    class BuildSlots(BaseUIComponent):
        """
        Draw empty build slot markers:
        - Blue slots (interactive) dengan plus icon + cost label
        - Red slots (visual only)
        """

        def draw(self, surface):
            """Draw semua build slots (slot surface DI-CACHE)"""
            g = self.game
            pulse = math.sin(g.animation_time * 0.08) * 2
            pk = int(round(pulse))

            # Blue slots (interactive)
            bsurf = getattr(self, "_blue_slot_cache", {})
            if pk not in bsurf:
                bsurf[pk] = self._render_blue_slot_surface(pk)
                self._blue_slot_cache = bsurf
            bslot = bsurf[pk]

            rsurf = getattr(self, "_red_slot_surf", None)
            if rsurf is None:
                rsurf = self._render_red_slot_surface()
                self._red_slot_surf = rsurf

            for slot in g.build_slots_blue:
                if slot['taken']:
                    continue
                sx, sy = slot['x'], slot['y']
                surface.blit(bslot, (sx - 20, sy - 17))

            # Red slots (visual only)
            for slot in g.build_slots_red:
                if slot['taken']:
                    continue
                sx, sy = slot['x'], slot['y']
                surface.blit(rsurf, (sx - 20, sy - 17))

        def _render_blue_slot_surface(self, pk):
            """Render satu slot biru ke surface (origin lokal 20,17)."""
            s = pygame.Surface((40, 38), pygame.SRCALPHA)
            # Ground shadow
            pygame.draw.ellipse(s, (0, 0, 0, 100), (2, 29, 36, 8))
            # Stone platform
            pygame.draw.circle(s, (80, 80, 90), (20, 22), 16)
            pygame.draw.circle(s, (120, 120, 130), (20, 21), 15)
            pygame.draw.circle(s, (160, 160, 170), (20, 20), 13)
            pygame.draw.circle(s, (100, 100, 110), (20, 20), 13, 1)
            # Inner pattern
            pygame.draw.circle(s, (140, 140, 150), (20, 20), 10)
            pygame.draw.circle(s, (180, 180, 190), (18, 18), 5)
            # Glow (radius ikut pulse)
            pygame.draw.circle(s, (100, 200, 255, 60),
                               (20, 20), 15 + pk)
            # Plus icon
            plus_size = 8 + pk
            pygame.draw.rect(s, (30, 60, 120),
                             (20 - plus_size // 2 - 1, 15,
                              plus_size + 2, 4))
            pygame.draw.rect(s, (30, 60, 120),
                             (18, 17 - plus_size // 2 - 1,
                              4, plus_size + 2))
            pygame.draw.rect(s, (100, 200, 255),
                             (20 - plus_size // 2, 16,
                              plus_size, 2))
            pygame.draw.rect(s, (100, 200, 255),
                             (19, 17 - plus_size // 2,
                              2, plus_size))
            pygame.draw.rect(s, (200, 240, 255),
                             (20 - plus_size // 2, 16,
                              plus_size // 2, 1))
            pygame.draw.rect(s, (200, 240, 255),
                             (19, 17 - plus_size // 2,
                              1, plus_size // 2))
            # Cost label
            cost_text = pygame.font.Font(None, 14).render(
                "100G", True, GOLD)
            cost_bg = pygame.Rect(5, 35, 30, 12)
            pygame.draw.rect(s, (0, 0, 0), cost_bg, border_radius=3)
            pygame.draw.rect(s, GOLD, cost_bg, 1, border_radius=3)
            s.blit(cost_text,
                   cost_text.get_rect(center=cost_bg.center))
            return s

        def _render_red_slot_surface(self):
            """Render satu slot merah (statis) ke surface."""
            s = pygame.Surface((40, 38), pygame.SRCALPHA)
            pygame.draw.circle(s, (60, 20, 20), (20, 20), 10)
            pygame.draw.circle(s, (100, 40, 40), (20, 20), 9)
            pygame.draw.circle(s, (140, 60, 60), (19, 19), 6)
            pygame.draw.line(s, (200, 80, 80),
                             (17, 16), (23, 22), 1)
            pygame.draw.line(s, (200, 80, 80),
                             (23, 16), (17, 22), 1)
            return s

        # ═══════════════════════════════════════
        # BLUE SLOT (Interactive)
        # ═══════════════════════════════════════

        def _draw_blue_slot(self, surface, slot, pulse):
            """Draw blue interactive build slot"""
            sx, sy = slot['x'], slot['y']

            # Ground shadow
            pygame.draw.ellipse(surface, (0, 0, 0, 100),
                                (sx - 18, sy + 12, 36, 8))

            # Stone platform
            pygame.draw.circle(surface, (80, 80, 90), (sx, sy + 5), 16)
            pygame.draw.circle(surface, (120, 120, 130), (sx, sy + 4), 15)
            pygame.draw.circle(surface, (160, 160, 170), (sx, sy + 3), 13)
            pygame.draw.circle(surface, (100, 100, 110), (sx, sy + 3), 13, 1)

            # Inner pattern
            pygame.draw.circle(surface, (140, 140, 150), (sx, sy + 3), 10)
            pygame.draw.circle(surface, (180, 180, 190), (sx - 2, sy + 1), 5)

            # Plus icon
            plus_size = 8 + int(pulse)

            # Glow
            glow_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (100, 200, 255, 60),
                               (20, 20), 15 + int(pulse))
            surface.blit(glow_surf, (sx - 20, sy - 17))

            # Plus outline
            pygame.draw.rect(surface, (30, 60, 120),
                             (sx - plus_size // 2 - 1, sy - 2,
                              plus_size + 2, 4))
            pygame.draw.rect(surface, (30, 60, 120),
                             (sx - 2, sy - plus_size // 2 - 1,
                              4, plus_size + 2))

            # Plus body
            pygame.draw.rect(surface, (100, 200, 255),
                             (sx - plus_size // 2, sy - 1,
                              plus_size, 2))
            pygame.draw.rect(surface, (100, 200, 255),
                             (sx - 1, sy - plus_size // 2,
                              2, plus_size))

            # Plus highlight
            pygame.draw.rect(surface, (200, 240, 255),
                             (sx - plus_size // 2, sy - 1,
                              plus_size, 1))
            pygame.draw.rect(surface, (200, 240, 255),
                             (sx - 1, sy - plus_size // 2,
                              1, plus_size))

            # Cost label
            cost_font = pygame.font.Font(None, 14)
            cost_text = cost_font.render("100G", True, GOLD)
            cost_bg = pygame.Rect(sx - 15, sy + 18, 30, 12)
            pygame.draw.rect(surface, (0, 0, 0), cost_bg, border_radius=3)
            pygame.draw.rect(surface, GOLD, cost_bg, 1, border_radius=3)
            cost_rect = cost_text.get_rect(center=cost_bg.center)
            surface.blit(cost_text, cost_rect)

        # ═══════════════════════════════════════
        # RED SLOT (Visual only)
        # ═══════════════════════════════════════

        def _draw_red_slot(self, surface, slot):
            """Draw red visual-only slot"""
            sx, sy = slot['x'], slot['y']

            pygame.draw.circle(surface, (60, 20, 20), (sx, sy + 3), 10)
            pygame.draw.circle(surface, (100, 40, 40), (sx, sy + 3), 9)
            pygame.draw.circle(surface, (140, 60, 60), (sx - 1, sy + 2), 6)

            pygame.draw.line(surface, (200, 80, 80),
                             (sx - 3, sy - 1), (sx + 3, sy + 5), 1)
            pygame.draw.line(surface, (200, 80, 80),
                             (sx + 3, sy - 1), (sx - 3, sy + 5), 1)




    # ================================


# ====================================================================
# hero_panel.py
# ====================================================================
class _NS_hero_panel:
    """Namespace hero_panel - isi asli tidak diubah."""

    # ui_components/hero_panel.py
    # Panel hero info di bottom-left (saat hero selected)
    # ================================



    class HeroPanel(BaseUIComponent):
        """
        Panel hero info di bottom-left saat hero di-select:
        - Name & Level
        - HP bar
        - 4 skill slots (Q, W, E, R) dengan cooldown
        - Upgrade hero button
        - Close button (X)
        """

        def draw(self, surface):
            """Draw hero panel"""
            g = self.game
            h = g.selected_hero

            if not h or not h.alive:
                return

            panel_w = 260
            panel_h = 165
            px = 20
            py = SCREEN_HEIGHT - panel_h - 20

            # Shadow
            shadow_surf = pygame.Surface((panel_w + 10, panel_h + 10),
                                         pygame.SRCALPHA)
            pygame.draw.rect(shadow_surf, (0, 0, 0, 120),
                             (5, 5, panel_w, panel_h), border_radius=8)
            surface.blit(shadow_surf, (px - 5, py - 5))

            # Background
            pygame.draw.rect(surface, (25, 30, 45),
                             (px, py, panel_w, panel_h),
                             border_radius=8)
            pygame.draw.rect(surface, h.color,
                             (px, py, panel_w, panel_h),
                             2, border_radius=8)

            # Title
            title = self.ui.font_small.render(
                f"{h.name} Lv.{h.level}", True, WHITE)
            surface.blit(title, (px + 10, py + 8))

            # Close button (X)
            self._draw_close_button(surface,
                                     px + panel_w - 25, py + 5,
                                     size=20,
                                     button_id='hero_close',
                                     style='rect')

            # HP bar
            y = py + 28
            bar_w = panel_w - 20
            self._draw_hp_bar(surface, px + 10, y, bar_w, 6,
                               h.hp / h.max_hp)

            # HP text
            hp_t = self.ui.font_tiny.render(
                f"{int(h.hp)}/{h.max_hp}", True, WHITE)
            surface.blit(hp_t, (px + 10, y + 8))

            # 4 skill slots (Q, W, E, R)
            y += 22
            skill_size = 40
            skill_gap = 8
            start_x = px + 10

            is_auto = h.auto_cast_enabled

            self._draw_skill_slot(surface, start_x, y, skill_size,
                                  self._skill_key_label("Q"),
                                  h.skill_timer,
                                  h.skill_cooldown_max,
                                  h.color, is_auto=is_auto)
            self._draw_skill_slot(surface,
                                  start_x + skill_size + skill_gap, y,
                                  skill_size,
                                  self._skill_key_label("W"),
                                  h.w_cooldown, h.w_cooldown_max,
                                  (100, 200, 255),
                                  is_auto=is_auto)
            self._draw_skill_slot(surface,
                                  start_x + (skill_size + skill_gap) * 2, y,
                                  skill_size,
                                  self._skill_key_label("E"),
                                  h.e_cooldown, h.e_cooldown_max,
                                  (100, 255, 100),
                                  is_auto=is_auto)
            self._draw_skill_slot(surface,
                                  start_x + (skill_size + skill_gap) * 3, y,
                                  skill_size,
                                  self._skill_key_label("R"),
                                  h.r_cooldown, h.r_cooldown_max,
                                  (255, 100, 100),
                                  is_ultimate=True,
                                  is_auto=is_auto)

            # ═══ AUTO-CAST TOGGLE ═══
            y += skill_size + 8
            self._draw_autocast_toggle(surface, px, y, panel_w, h)

            # Upgrade button
            y += 28
            self._draw_upgrade_button(surface, px, y, panel_w, h)

        def _draw_upgrade_button(self, surface, px, y, panel_w, hero):
            """Draw upgrade hero button"""
            g = self.game

            if hero.level < MAX_HERO_LEVEL:
                cost = hero.upgrade_cost()
                can_up = g.gold >= cost

                btn_rect = pygame.Rect(px + 10, y, panel_w - 20, 22)
                bg = CYAN if can_up else DARK_GRAY
                pygame.draw.rect(surface, bg, btn_rect, border_radius=3)
                pygame.draw.rect(surface, WHITE, btn_rect, 1,
                                 border_radius=3)
                up_t = self.ui.font_tiny.render(
                    f"UPGRADE HERO ({cost}G)",
                    True, WHITE if can_up else GRAY)
                up_text_rect = up_t.get_rect(center=btn_rect.center)
                surface.blit(up_t, up_text_rect)

                g.ui_buttons['popup_upgrade_hero'] = btn_rect
            else:
                max_t = self.ui.font_tiny.render(
                    "★ MAX LEVEL ★", True, YELLOW)
                max_rect = max_t.get_rect(
                    center=(px + panel_w // 2, y + 11))
                surface.blit(max_t, max_rect)

        def _draw_autocast_toggle(self, surface, px, y, panel_w, hero):
            """Draw auto-cast toggle button"""
            g = self.game

            btn_rect = pygame.Rect(px + 10, y, panel_w - 20, 22)

            is_auto = hero.auto_cast_enabled

            # Colors
            if is_auto:
                bg_color = (60, 180, 80)  # green (ON)
                border_col = (100, 220, 100)
                label = "⚡ AUTO-CAST: ON"
                text_color = WHITE
            else:
                bg_color = (60, 60, 70)  # gray (OFF)
                border_col = (150, 150, 160)
                label = "◇ AUTO-CAST: OFF"
                text_color = (200, 200, 210)

            pygame.draw.rect(surface, bg_color, btn_rect, border_radius=3)
            pygame.draw.rect(surface, border_col, btn_rect, 1,
                             border_radius=3)

            toggle_text = self.ui.font_tiny.render(
                label, True, text_color)
            toggle_rect = toggle_text.get_rect(center=btn_rect.center)
            surface.blit(toggle_text, toggle_rect)

            # Register button
            g.ui_buttons['toggle_autocast'] = btn_rect

        def _skill_key_label(self, slot):
            """
            Label tombol skill sesuai input mode.
            Keyboard   -> Q / W / E / R
            Controller -> X / Y / LB / RB  (Xbox), dst.
            """
            try:
                mgr = getattr(self.game, 'controller_mgr', None)
                if mgr is not None and mgr.is_controller_mode():
                    return mgr.get_button_label(f'skill_{slot.lower()}')
            except Exception:
                pass
            return slot

        def _draw_skill_slot(self, surface, x, y, size, key_letter,
                             cooldown, cooldown_max, color,
                             is_ultimate=False, is_auto=False):
            """Draw single skill slot dengan cooldown overlay"""
            # Background
            bg_color = (30, 30, 45) if cooldown > 0 else color
            border_color = (150, 150, 150) if cooldown > 0 else WHITE

            pygame.draw.rect(surface, bg_color,
                             (x, y, size, size), border_radius=4)

            # Cooldown overlay
            if cooldown > 0:
                cd_ratio = cooldown / cooldown_max
                cd_height = int(size * cd_ratio)
                cd_surf = pygame.Surface((size, cd_height),
                                         pygame.SRCALPHA)
                cd_surf.fill((0, 0, 0, 180))
                surface.blit(cd_surf, (x, y + (size - cd_height)))

                # Cooldown text
                cd_seconds = cooldown // 60 + 1
                cd_font = pygame.font.Font(None, 22)
                cd_t = cd_font.render(str(cd_seconds), True, WHITE)
                cd_rect = cd_t.get_rect(
                    center=(x + size // 2, y + size // 2))
                shadow = cd_font.render(str(cd_seconds), True, (0, 0, 0))
                surface.blit(shadow, (cd_rect.x + 1, cd_rect.y + 1))
                surface.blit(cd_t, cd_rect)
            else:
                # Ultimate ready glow
                if is_ultimate:
                    pygame.draw.rect(surface, (255, 220, 100),
                                     (x - 2, y - 2, size + 4, size + 4),
                                     2, border_radius=4)

            # ═══ AUTO-CAST INDICATOR (green border) ═══
            if is_auto:
                # Green pulsing border overlay
                pulse = math.sin(
                    pygame.time.get_ticks() * 0.008) * 0.3 + 0.7
                auto_color = (100, 255, 100)
                pygame.draw.rect(surface, auto_color,
                                 (x, y, size, size), 3,
                                 border_radius=4)
            else:
                # Normal border
                pygame.draw.rect(surface, border_color,
                                 (x, y, size, size), 2,
                                 border_radius=4)

            # Key letter (bottom right)
            # Label controller bisa panjang (LB / RB / TRIANGLE),
            # jadi lebar badge ikut teks + font mengecil otomatis.
            label = str(key_letter)
            fsize = 14 if len(label) <= 2 else (12 if len(label) <= 4 else 10)
            key_font = pygame.font.Font(None, fsize)
            key_t = key_font.render(label, True, YELLOW)
            bw = max(10, key_t.get_width() + 4)
            bh = max(10, key_t.get_height() + 1)
            key_bg = pygame.Rect(x + size - bw - 1, y + size - bh - 1, bw, bh)
            pygame.draw.rect(surface, (0, 0, 0), key_bg,
                             border_radius=2)
            key_rect = key_t.get_rect(center=key_bg.center)
            surface.blit(key_t, key_rect)

            # ═══ "A" BADGE (auto indicator, top-left) ═══
            if is_auto:
                badge_bg = pygame.Rect(x + 2, y + 2, 12, 12)
                pygame.draw.rect(surface, (0, 100, 0), badge_bg,
                                 border_radius=2)
                pygame.draw.rect(surface, (100, 255, 100), badge_bg, 1,
                                 border_radius=2)
                badge_text = pygame.font.Font(None, 12).render(
                    "A", True, (200, 255, 200))
                badge_rect = badge_text.get_rect(center=badge_bg.center)
                surface.blit(badge_text, badge_rect)




    # ================================
    # GANTI SELURUH FILE ui_components/hero_portraits.py
    # 100% AUTO-GENERATE - ZERO manual portraits
    # ================================





    # ═══════════════════════════════════════════════════════
    # FAKE ENTITY FACTORIES
    # ═══════════════════════════════════════════════════════

    class _FakeEntity:
        """Safe fake entity - return 0 untuk attribute apapun"""
        def __getattr__(self, name):
            return 0


    def _make_fake_boss(hero_type, canvas_w, canvas_h):
        """Buat fake boss object untuk portrait render"""
        fake = _NS_hero_panel._FakeEntity()
        fake.x = canvas_w // 2
        fake.y = canvas_h // 2 + 20
        fake.hp = 1000
        fake.max_hp = 1000
        fake.damage = 50
        fake.range = 100
        fake.attack_cooldown = 40
        fake.timer = 0
        fake.direction = 1
        fake.pulse = 0.5
        fake.target = None
        fake.alive = True
        fake.boss_type = hero_type
        fake.team = "blue"
        fake.radius = 30
        fake.active_skill = None
        fake.active_skill_timer = 0
        fake.flux_target = None
        fake.flux_active_timer = 0
        fake.vortex_x = 0
        fake.vortex_y = 0
        fake.vortex_active_timer = 0
        fake.mana_void_x = 0
        fake.mana_void_y = 0
        fake.blink_from_x = 0
        fake.blink_from_y = 0
        fake.rage_active = False
        fake.defense_boost = False
        fake.clones_active_timer = 0
        fake.clones_positions = []
        fake.w_target_x = 0
        fake.w_target_y = 0
        fake.w_dir_x = 1
        fake.w_dir_y = 0
        fake.r_dir_x = 1
        fake.r_dir_y = 0
        fake.cold_feet_target_x = 0
        fake.cold_feet_target_y = 0
        fake.shield_active = False
        fake.shield_timer = 0
        fake.arcane_buff_active = False
        fake.arcane_buff_timer = 0
        fake.base_damage = 50
        return fake


    def _make_fake_hero(hero_type, stats, canvas_w, canvas_h):
        """Buat fake hero object untuk portrait render"""
        fake = _NS_hero_panel._FakeEntity()
        fake.x = float(canvas_w // 2)
        fake.y = float(canvas_h // 2 + 10)
        fake.hero_type = hero_type
        fake.hp = stats.get("hp", 500)
        fake.max_hp = fake.hp
        fake.damage = stats.get("damage", 30)
        fake.range = stats.get("range", 100)
        fake.attack_cooldown = stats.get("attack_cooldown", 40)
        fake.attack_timer = 0
        fake.speed = stats.get("speed", 1.5)
        fake.facing = 1
        fake.pulse = 0.5
        fake.target = None
        fake.alive = True
        fake.team = "blue"
        fake.radius = 16
        fake.color = stats["color"]
        fake.color_dark = stats["color_dark"]
        fake.level = 1
        fake.selected = False
        fake.skill_active = False
        fake.skill_timer = 0
        fake.skill_cooldown_max = 300
        fake.skill_data = stats
        fake.is_retreating = False
        fake.kills = 0
        fake.deaths = 0
        fake.name = stats.get("name", hero_type)
        fake.title = stats.get("title", "")
        fake.walk_cycle = 0
        fake.is_moving = False
        fake.anim_time = 0

        # Hero-specific skill states (semua False/0)
        skill_attrs = [
            '_blade_fury_active', '_blade_fury_timer',
            '_omnislash_active', '_omnislash_timer',
            '_heal_ward_active', '_heal_ward_timer',
            '_heal_ward_pos',
            '_focus_fire_active', '_focus_fire_timer',
            '_powershot_charging', '_powershot_timer',
            '_shackle_active', '_shackle_timer',
            '_shackle_target',
            '_sanity_eclipse_active', '_sanity_eclipse_timer',
            '_astral_prison_active', '_astral_prison_timer',
            '_astral_prison_target',
            '_essence_flux_active', '_essence_flux_timer',
            '_windrun_active', '_windrun_timer',
            '_wind_wall_timer',
            '_ulti_active', '_ulti_timer',
            '_is_dashing', '_dash_timer',
            '_q_stack', '_q_reset_timer',
            '_bristleback_active', '_bristleback_timer',
            '_warpath_active', '_warpath_timer',
            '_spraying_quills', '_spray_timer',
            '_viscous_nose_active', '_viscous_nose_timer',
            '_shadow_realm_active', '_shadow_realm_timer',
            '_bedlam_active', '_bedlam_timer',
            '_bramble_active', '_bramble_timer',
            '_curse_active', '_curse_timer',
            '_curse_target',
            '_crit_buff_active', '_crit_buff_timer',
            '_original_speed', '_original_damage',
            '_original_attack_cd',
            '_rage_active', '_rage_timer',
            '_war_cry_timer',
            '_fortify_active', '_fortify_timer',
            '_holy_shield_active', '_holy_shield_timer',
        ]

        for attr in skill_attrs:
            if attr.endswith('_pos'):
                setattr(fake, attr, (0, 0))
            elif attr.endswith('_target'):
                setattr(fake, attr, None)
            elif 'active' in attr or 'charging' in attr \
                    or 'dashing' in attr or 'spraying' in attr:
                setattr(fake, attr, False)
            else:
                setattr(fake, attr, 0)

        # Movement detection
        fake._last_x = fake.x
        fake._last_y = fake.y

        return fake




    # ================================


# ====================================================================
# hero_shop.py
# ====================================================================
class _NS_hero_shop:
    """Namespace hero_shop - isi asli tidak diubah."""

    # ui_components/hero_shop.py
    # Modern hero shop dengan pixel art portraits
    # ================================



    class HeroShop(BaseUIComponent):
        """
        Modern hero shop overlay:
        - Gradient background dengan glow
        - Header dengan gold info & owned count
        - 6 hero cards dengan portraits
        - Buy buttons dengan multiple states
        - Close button (X) round style
        """

        def draw(self, surface):
            """Main draw method - dengan cache untuk performance"""
            g = self.game

            # Render langsung, tanpa cache
            self._render_shop(surface)

        def _render_shop(self, surface):
            """Render shop content"""
            g = self.game

            # Dark overlay
            self._draw_overlay(surface)

            # Main panel
            panel_w = 1100
            panel_h = 700
            panel_x = (SCREEN_WIDTH - panel_w) // 2
            panel_y = (SCREEN_HEIGHT - panel_h) // 2

            self._draw_panel(surface, panel_x, panel_y, panel_w, panel_h)
            header_h = 70
            self._draw_header(surface, panel_x, panel_y, panel_w, header_h)
            self._draw_title(surface, panel_x, panel_y, panel_w)
            self._draw_gold_info(surface, panel_x, panel_y)
            self._draw_owned_info(surface, panel_x, panel_y, panel_w)
            self._draw_shop_close_button(surface, panel_x, panel_y, panel_w)
            self._draw_hero_cards(surface, panel_x, panel_y, panel_w,
                                  header_h)
        # ═══════════════════════════════════════
        # BACKGROUND & PANEL
        # ═══════════════════════════════════════

        def _draw_overlay(self, surface):
            """Dark overlay background"""
            from mobile.perf import darken
            darken(surface, 220)

        def _draw_panel(self, surface, panel_x, panel_y, panel_w, panel_h):
            """Main panel - OPTIMIZED (no per-pixel gradient)"""
            # Shadow
            shadow_surf = pygame.Surface(
                (panel_w + 20, panel_h + 20), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surf, (0, 0, 0, 150),
                             (10, 10, panel_w, panel_h),
                             border_radius=15)
            surface.blit(shadow_surf, (panel_x - 10, panel_y - 10))

            # Solid background (BUKAN gradient per-pixel)
            pygame.draw.rect(surface, (25, 30, 50),
                             (panel_x, panel_y, panel_w, panel_h),
                             border_radius=15)

            # Simple 3-step gradient (cuma 3 rect, bukan 700 lines)
            third = panel_h // 3
            pygame.draw.rect(surface, (22, 27, 48),
                             (panel_x + 2, panel_y + 2,
                              panel_w - 4, third),
                             border_radius=15)
            pygame.draw.rect(surface, (28, 33, 55),
                             (panel_x + 2, panel_y + third,
                              panel_w - 4, third))
            pygame.draw.rect(surface, (33, 38, 62),
                             (panel_x + 2, panel_y + third * 2,
                              panel_w - 4, third),
                             border_radius=15)

            # Gold border
            pygame.draw.rect(surface, (255, 200, 50),
                             (panel_x, panel_y, panel_w, panel_h),
                             3, border_radius=15)
            pygame.draw.rect(surface, (255, 220, 100),
                             (panel_x + 2, panel_y + 2,
                              panel_w - 4, panel_h - 4),
                             1, border_radius=13)

        def _draw_header(self, surface, panel_x, panel_y, panel_w, header_h):
            """Header bar dengan gradient + separator line"""
            header_surf = pygame.Surface((panel_w, header_h),
                                         pygame.SRCALPHA)
            for i in range(header_h):
                t = i / header_h
                alpha = int(180 - t * 100)
                pygame.draw.line(header_surf,
                                 (60, 40, 15, alpha),
                                 (0, i), (panel_w, i))
            surface.blit(header_surf, (panel_x, panel_y))

            # Header separator line
            pygame.draw.line(surface, (255, 200, 50),
                             (panel_x + 20, panel_y + header_h),
                             (panel_x + panel_w - 20, panel_y + header_h),
                             2)

        def _draw_title(self, surface, panel_x, panel_y, panel_w):
            """Title dengan shadow effect"""
            try:
                title_font = pygame.font.Font(None, 48)
            except:
                title_font = self.ui.font_big

            # Title shadow
            for offset in range(3, 0, -1):
                shadow = title_font.render("HERO SHOP", True, (0, 0, 0))
                shadow.set_alpha(80)
                shadow_rect = shadow.get_rect(
                    center=(panel_x + panel_w // 2 + offset,
                            panel_y + 35 + offset))
                surface.blit(shadow, shadow_rect)

            # Main title
            title = title_font.render("HERO SHOP", True,
                                      (255, 220, 100))
            title_rect = title.get_rect(
                center=(panel_x + panel_w // 2, panel_y + 35))
            surface.blit(title, title_rect)

        # ═══════════════════════════════════════
        # INFO BADGES
        # ═══════════════════════════════════════

        def _draw_gold_info(self, surface, panel_x, panel_y):
            """Gold info di header (kiri)"""
            g = self.game

            gold_bg = pygame.Rect(panel_x + 25, panel_y + 22, 200, 30)
            pygame.draw.rect(surface, (40, 30, 10), gold_bg,
                             border_radius=15)
            pygame.draw.rect(surface, GOLD, gold_bg, 2,
                             border_radius=15)

            try:
                info_font = pygame.font.Font(None, 22)
            except:
                info_font = self.ui.font_medium

            # Coin icon
            pygame.draw.circle(surface, (255, 200, 50),
                               (panel_x + 45, panel_y + 37), 8)
            pygame.draw.circle(surface, (200, 150, 30),
                               (panel_x + 45, panel_y + 37), 8, 2)

            coin_font = pygame.font.Font(None, 16)
            dollar = coin_font.render("$", True, (100, 60, 10))
            dollar_rect = dollar.get_rect(
                center=(panel_x + 45, panel_y + 37))
            surface.blit(dollar, dollar_rect)

            # Gold amount
            gold_text = info_font.render(
                f"GOLD: {g.gold:,}", True, (255, 220, 100))
            surface.blit(gold_text, (panel_x + 60, panel_y + 28))

        def _draw_owned_info(self, surface, panel_x, panel_y, panel_w):
            """Owned count badge di kanan header"""
            from settings import MAX_HEROES_OWNED
            g = self.game

            owned_bg = pygame.Rect(
                panel_x + panel_w - 205, panel_y + 22, 180, 30)
            pygame.draw.rect(surface, (10, 30, 40), owned_bg,
                             border_radius=15)
            pygame.draw.rect(surface, (100, 200, 255), owned_bg, 2,
                             border_radius=15)

            try:
                info_font = pygame.font.Font(None, 22)
            except:
                info_font = self.ui.font_medium

            # Hero icon
            hero_icon_x = panel_x + panel_w - 195
            hero_icon_y = panel_y + 37
            pygame.draw.circle(surface, (100, 200, 255),
                               (hero_icon_x, hero_icon_y - 2), 4)
            pygame.draw.rect(surface, (100, 200, 255),
                             (hero_icon_x - 3, hero_icon_y + 1, 6, 5))

            owned_text = info_font.render(
                f"{len(g.heroes)}/{MAX_HEROES_OWNED} Heroes",
                True, (150, 220, 255))
            surface.blit(owned_text, (panel_x + panel_w - 175,
                                      panel_y + 28))

        def _draw_shop_close_button(self, surface, panel_x, panel_y,
                                      panel_w):
            """Round close button (X) di corner"""
            g = self.game

            close_size = 32
            close_rect = pygame.Rect(
                panel_x + panel_w - close_size - 15,
                panel_y - 15,
                close_size, close_size)

            # Hover detection
            mx, my = pygame.mouse.get_pos()
            is_hover_close = close_rect.collidepoint(mx, my)

            # Glow effect
            if is_hover_close:
                glow_surf = pygame.Surface(
                    (close_size + 10, close_size + 10), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (255, 80, 80, 100),
                                   ((close_size + 10) // 2,
                                    (close_size + 10) // 2),
                                   close_size // 2 + 3)
                surface.blit(glow_surf,
                             (close_rect.x - 5, close_rect.y - 5))

            # Button base (round)
            pygame.draw.circle(surface,
                               (200, 40, 40) if is_hover_close
                               else (150, 30, 30),
                               close_rect.center, close_size // 2)
            pygame.draw.circle(surface, (255, 255, 255),
                               close_rect.center, close_size // 2, 2)

            # X symbol
            pygame.draw.line(surface, (255, 255, 255),
                             (close_rect.centerx - 7, close_rect.centery - 7),
                             (close_rect.centerx + 7, close_rect.centery + 7),
                             3)
            pygame.draw.line(surface, (255, 255, 255),
                             (close_rect.centerx + 7, close_rect.centery - 7),
                             (close_rect.centerx - 7, close_rect.centery + 7),
                             3)

            g.ui_buttons['shop_close'] = close_rect

        # ═══════════════════════════════════════
        # HERO CARDS GRID
        # ═══════════════════════════════════════
        def _draw_hero_cards(self, surface, panel_x, panel_y, panel_w,
                             header_h):
            """Draw hero cards dengan tab + scroll system"""
            from settings import get_all_hero_types, MAX_HEROES_OWNED
            g = self.game

            # ═══ INIT STATE ═══
            if not hasattr(g, '_shop_tab'):
                g._shop_tab = 'starter'
            if not hasattr(g, '_shop_scroll'):
                g._shop_scroll = 0

            all_heroes = get_all_hero_types()
            purchased = g.purchased_heroes

            # ═══ TABS ═══
            tab_y = panel_y + header_h + 10
            tab_h = 30

            tabs = [
                ('starter', 'STARTER', (100, 200, 255)),
                ('boss', 'BOSS HEROES', (255, 150, 100)),
            ]

            tab_w = 150
            total_tab_w = tab_w * len(tabs) + 10
            tab_start_x = panel_x + (panel_w - total_tab_w) // 2

            for i, (tab_id, tab_label, tab_color) in enumerate(tabs):
                tx = tab_start_x + i * (tab_w + 10)
                tab_rect = pygame.Rect(tx, tab_y, tab_w, tab_h)

                is_active = g._shop_tab == tab_id
                mx, my = pygame.mouse.get_pos()
                is_hover = tab_rect.collidepoint(mx, my)

                if is_active:
                    pygame.draw.rect(surface, (40, 50, 80),
                                     tab_rect, border_radius=6)
                    pygame.draw.rect(surface, tab_color,
                                     tab_rect, 3, border_radius=6)
                else:
                    bg = (30, 35, 55) if is_hover else (20, 25, 40)
                    pygame.draw.rect(surface, bg,
                                     tab_rect, border_radius=6)
                    pygame.draw.rect(surface, (80, 90, 110),
                                     tab_rect, 2, border_radius=6)

                try:
                    tab_font = pygame.font.Font(None, 20)
                except:
                    tab_font = self.ui.font_small

                text_color = tab_color if is_active else (150, 160, 180)
                tab_text = tab_font.render(tab_label, True, text_color)
                tab_text_rect = tab_text.get_rect(center=tab_rect.center)
                surface.blit(tab_text, tab_text_rect)

                g.ui_buttons[f'shop_tab_{tab_id}'] = tab_rect

            # ═══ FILTER HEROES ═══
            hero_list = []
            for ht in purchased:
                if ht not in all_heroes:
                    continue
                stats = all_heroes[ht]
                is_boss = stats.get("is_boss_hero", False)

                if g._shop_tab == 'starter' and not is_boss:
                    hero_list.append(ht)
                elif g._shop_tab == 'boss' and is_boss:
                    hero_list.append(ht)

            # ═══ CONTENT AREA ═══
            content_top = tab_y + tab_h + 10
            content_bottom = panel_y + 700 - 20  # panel height
            content_height = content_bottom - content_top

            # ═══ EMPTY STATE ═══
            if not hero_list:
                try:
                    no_hero_font = pygame.font.Font(None, 28)
                    hint_font = pygame.font.Font(None, 20)
                except:
                    no_hero_font = self.ui.font_big
                    hint_font = self.ui.font_small

                cx = panel_x + panel_w // 2
                cy = content_top + 120

                if g._shop_tab == 'boss':
                    msg = "No boss heroes unlocked yet"
                    hint = "Defeat bosses to unlock their hero!"
                else:
                    msg = "No starter heroes unlocked"
                    hint = "Visit Hero Shop from Main Menu!"

                no_hero = no_hero_font.render(msg, True, (200, 200, 220))
                no_hero_rect = no_hero.get_rect(center=(cx, cy))
                surface.blit(no_hero, no_hero_rect)

                hint_text = hint_font.render(hint, True, (255, 220, 100))
                hint_rect = hint_text.get_rect(center=(cx, cy + 35))
                surface.blit(hint_text, hint_rect)
                return

            # ═══ CARD LAYOUT ═══
            card_w = 340
            card_h = 120  # compact horizontal card
            cards_per_row = 2
            gap_x = 20
            gap_y = 12

            total_width = card_w * cards_per_row + gap_x
            start_x = panel_x + (panel_w - total_width) // 2

            # Calculate total rows & scroll
            total_rows = (len(hero_list) + cards_per_row - 1) // cards_per_row
            total_content_h = total_rows * (card_h + gap_y)
            max_scroll = max(0, total_content_h - content_height)

            # Clamp scroll
            g._shop_scroll = max(0, min(max_scroll, g._shop_scroll))

            # ═══ CLIP AREA (biar tidak draw di luar content) ═══
            clip_rect = pygame.Rect(panel_x, content_top,
                                    panel_w, content_height)
            old_clip = surface.get_clip()
            surface.set_clip(clip_rect)

            # ═══ DRAW CARDS ═══
            for i, hero_type in enumerate(hero_list):
                col = i % cards_per_row
                row = i // cards_per_row

                cx = start_x + col * (card_w + gap_x)
                cy = content_top + row * (card_h + gap_y) - g._shop_scroll

                # Skip kalau di luar visible area
                if cy + card_h < content_top or cy > content_bottom:
                    continue

                self._draw_compact_card(surface, hero_type, cx, cy,
                                        card_w, card_h)

            # Reset clip
            surface.set_clip(old_clip)

            # ═══ SCROLL INDICATOR ═══
            if max_scroll > 0:
                self._draw_scroll_indicator(
                    surface, panel_x + panel_w - 20,
                    content_top, content_height,
                    g._shop_scroll, max_scroll)

                # Register scroll buttons
                scroll_up_rect = pygame.Rect(
                    panel_x + panel_w - 25, content_top, 20, 20)
                scroll_down_rect = pygame.Rect(
                    panel_x + panel_w - 25,
                    content_bottom - 20, 20, 20)
                g.ui_buttons['shop_scroll_up'] = scroll_up_rect
                g.ui_buttons['shop_scroll_down'] = scroll_down_rect

        def _draw_compact_card(self, surface, hero_type, cx, cy, cw, ch):
            """Compact horizontal hero card — info kiri, button kanan"""
            from settings import get_all_hero_types, MAX_HEROES_OWNED
            g = self.game
            all_heroes = get_all_hero_types()
            stats = all_heroes[hero_type]
            owned = any(h.hero_type == hero_type for h in g.heroes)
            cost = stats.get("cost", 400)
            can_afford = g.gold >= cost

            color_main = stats["color"]
            color_dark = stats["color_dark"]

            # Hover
            mx, my = pygame.mouse.get_pos()
            card_rect = pygame.Rect(cx, cy, cw, ch)
            is_hover = card_rect.collidepoint(mx, my) and not owned \
                       and len(g.heroes) < MAX_HEROES_OWNED

            # ═══ CARD BG ═══
            if owned:
                bg_color = (25, 40, 30)
            else:
                bg_color = (25, 30, 50)

            # Shadow
            shadow_surf = pygame.Surface((cw + 6, ch + 6), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surf, (0, 0, 0, 100),
                             (3, 3, cw, ch), border_radius=8)
            surface.blit(shadow_surf, (cx - 3, cy - 3))

            pygame.draw.rect(surface, bg_color,
                             (cx, cy, cw, ch), border_radius=8)

            # Hover glow
            if is_hover:
                glow_surf = pygame.Surface((cw + 12, ch + 12),
                                           pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (*color_main, 60),
                                 (0, 0, cw + 12, ch + 12),
                                 border_radius=10)
                surface.blit(glow_surf, (cx - 6, cy - 6))

            # Border
            border_color = (100, 220, 100) if owned else (
                (255, 255, 255) if is_hover else color_main)
            border_w = 3 if is_hover else 2
            pygame.draw.rect(surface, border_color,
                             (cx, cy, cw, ch), border_w, border_radius=8)

            # ═══ LEFT: PORTRAIT (small) ═══
            portrait_size = 60
            portrait_x = cx + 10
            portrait_y = cy + (ch - portrait_size) // 2

            # Portrait bg
            pygame.draw.rect(surface, (15, 20, 30),
                             (portrait_x, portrait_y,
                              portrait_size, portrait_size),
                             border_radius=4)
            pygame.draw.rect(surface, color_main,
                             (portrait_x, portrait_y,
                              portrait_size, portrait_size),
                             1, border_radius=4)

            # Draw portrait
            from ui_components.hero_portraits import HeroPortraits
            HeroPortraits.draw(
                surface, hero_type,
                portrait_x + portrait_size // 2,
                portrait_y + portrait_size // 2 + 3,
                stats, owned=False)

            # ═══ CENTER: INFO ═══
            info_x = cx + 10 + portrait_size + 12
            info_y = cy + 10

            # Name
            try:
                name_font = pygame.font.Font(None, 24)
            except:
                name_font = self.ui.font_medium

            name_surf = name_font.render(stats["name"], True, (255, 255, 255))
            surface.blit(name_surf, (info_x, info_y))

            # Title
            title_surf = self.ui.font_tiny.render(
                stats["title"], True, (180, 190, 210))
            surface.blit(title_surf, (info_x, info_y + 22))

            # Role badge
            role_text = stats["role"].upper()
            role_font = pygame.font.Font(None, 13)
            role_surf = role_font.render(role_text, True, color_main)
            role_bg = pygame.Rect(info_x, info_y + 38, 80, 16)
            pygame.draw.rect(surface, (0, 0, 0), role_bg,
                             border_radius=8)
            pygame.draw.rect(surface, color_main, role_bg, 1,
                             border_radius=8)
            role_rect = role_surf.get_rect(center=role_bg.center)
            surface.blit(role_surf, role_rect)

            # Stats row (mini)
            stats_y = info_y + 60
            mini_stats = [
                ("HP", stats["hp"], (255, 100, 100)),
                ("DMG", stats["damage"], (255, 200, 100)),
                ("RNG", stats["range"], (100, 200, 255)),
            ]

            stat_font = pygame.font.Font(None, 13)
            for j, (label, value, col) in enumerate(mini_stats):
                sx = info_x + j * 50
                label_surf = stat_font.render(label, True, col)
                surface.blit(label_surf, (sx, stats_y))

                val_font = pygame.font.Font(None, 16)
                val_surf = val_font.render(str(value), True, (255, 255, 255))
                surface.blit(val_surf, (sx, stats_y + 12))

            # ═══ RIGHT: BUTTON ═══
            btn_w = 90
            btn_h = 30
            btn_x = cx + cw - btn_w - 12
            btn_y = cy + (ch - btn_h) // 2

            btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

            if owned:
                pygame.draw.rect(surface, (40, 80, 40), btn_rect,
                                 border_radius=5)
                pygame.draw.rect(surface, (100, 180, 100), btn_rect,
                                 2, border_radius=5)
                btn_text = "ACTIVE"
                btn_color = (150, 255, 150)
            elif len(g.heroes) >= MAX_HEROES_OWNED:
                pygame.draw.rect(surface, (60, 40, 40), btn_rect,
                                 border_radius=5)
                pygame.draw.rect(surface, (180, 80, 80), btn_rect,
                                 2, border_radius=5)
                btn_text = "MAX"
                btn_color = (255, 150, 150)
            elif not can_afford:
                pygame.draw.rect(surface, (50, 50, 50), btn_rect,
                                 border_radius=5)
                pygame.draw.rect(surface, (130, 130, 130), btn_rect,
                                 2, border_radius=5)
                btn_text = f"{cost}G"
                btn_color = (200, 150, 150)
            else:
                btn_hover = btn_rect.collidepoint(mx, my)
                btn_bg = (40, 170, 50) if btn_hover else (35, 140, 45)
                btn_border = (130, 255, 130) if btn_hover else (100, 220, 100)

                pygame.draw.rect(surface, btn_bg, btn_rect,
                                 border_radius=5)
                pygame.draw.rect(surface, btn_border, btn_rect,
                                 2, border_radius=5)
                btn_text = f"{cost}G"
                btn_color = (255, 255, 255)

            try:
                btn_font = pygame.font.Font(None, 20)
            except:
                btn_font = self.ui.font_small

            btn_surf = btn_font.render(btn_text, True, btn_color)
            btn_text_rect = btn_surf.get_rect(center=btn_rect.center)
            surface.blit(btn_surf, btn_text_rect)

            g.ui_buttons[f'shop_buy_{hero_type}'] = btn_rect

        def _draw_scroll_indicator(self, surface, x, y, height,
                                   scroll_pos, max_scroll):
            """Draw scroll bar indicator"""
            # Track
            pygame.draw.rect(surface, (30, 35, 50),
                             (x, y, 8, height), border_radius=4)
            pygame.draw.rect(surface, (60, 70, 90),
                             (x, y, 8, height), 1, border_radius=4)

            # Thumb
            if max_scroll > 0:
                thumb_ratio = height / (height + max_scroll)
                thumb_h = max(20, int(height * thumb_ratio))
                thumb_y = y + int((height - thumb_h) *
                                  (scroll_pos / max_scroll))

                pygame.draw.rect(surface, (100, 130, 180),
                                 (x, thumb_y, 8, thumb_h),
                                 border_radius=4)
                pygame.draw.rect(surface, (150, 180, 220),
                                 (x + 1, thumb_y + 1, 6, thumb_h - 2),
                                 border_radius=3)

            # Up arrow
            pygame.draw.polygon(surface, (150, 180, 220), [
                (x + 4, y + 3),
                (x + 1, y + 8),
                (x + 7, y + 8),
            ])

            # Down arrow
            pygame.draw.polygon(surface, (150, 180, 220), [
                (x + 4, y + height - 3),
                (x + 1, y + height - 8),
                (x + 7, y + height - 8),
            ])



        def _draw_card(self, surface, hero_type, cx, cy, cw, ch):
            """Draw single hero card"""
            from settings import get_all_hero_types
            g = self.game
            all_heroes = get_all_hero_types()
            stats = all_heroes[hero_type]
            owned = any(h.hero_type == hero_type for h in g.heroes)
            cost = stats.get("cost", 400)
            can_afford = g.gold >= cost  # ← pakai gold in-game

            # Hover detection
            mx, my = pygame.mouse.get_pos()
            card_rect = pygame.Rect(cx, cy, cw, ch)
            is_hover = card_rect.collidepoint(mx, my) and not owned \
                       and len(g.heroes) < MAX_HEROES_OWNED

            # Determine colors
            color_main = stats["color"]
            color_dark = stats["color_dark"]
            if owned:
                color_main = (100, 100, 100)
                color_dark = (60, 60, 60)

            # Draw card layers
            self._draw_card_bg(surface, cx, cy, cw, ch, color_dark, is_hover)
            self._draw_card_border(surface, cx, cy, cw, ch, color_main,
                                   is_hover)
            self._draw_card_portrait(surface, cx, cy, hero_type, stats,
                                     color_main, owned)
            self._draw_card_info(surface, cx, cy, cw, stats, color_main,
                                 owned)
            self._draw_card_stats(surface, cx, cy, cw, stats)
            self._draw_card_skill(surface, cx, cy, cw, stats, color_main)
            self._draw_card_button(surface, cx, cy, cw, ch, hero_type,
                                   stats, owned, can_afford, is_hover)

        def _draw_card_bg(self, surface, cx, cy, cw, ch, color_dark,
                          is_hover):
            """Card background - OPTIMIZED"""
            # Shadow
            shadow_surf = pygame.Surface((cw + 10, ch + 10), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surf, (0, 0, 0, 120),
                             (5, 5, cw, ch), border_radius=12)
            surface.blit(shadow_surf, (cx - 5, cy - 5))

            # Solid background (OPTIMIZED - bukan per-pixel gradient)
            dark_color = (
                int(color_dark[0] * 0.35),
                int(color_dark[1] * 0.35),
                int(color_dark[2] * 0.35))
            light_color = (
                int(color_dark[0] * 0.55),
                int(color_dark[1] * 0.55),
                int(color_dark[2] * 0.55))

            # 2-step gradient (top dark, bottom lighter)
            half = ch // 2
            pygame.draw.rect(surface, dark_color,
                             (cx, cy, cw, half))
            pygame.draw.rect(surface, light_color,
                             (cx, cy + half, cw, ch - half))

            # Rounded corners overlay
            pygame.draw.rect(surface, dark_color,
                             (cx, cy, cw, ch),
                             border_radius=12)
            pygame.draw.rect(surface, dark_color,
                             (cx + 1, cy + 1, cw - 2, ch - 2),
                             border_radius=11)

        def _draw_card_border(self, surface, cx, cy, cw, ch, color_main,
                                is_hover):
            """Card border + hover glow"""
            # Hover glow
            if is_hover:
                glow_surf = pygame.Surface((cw + 20, ch + 20),
                                           pygame.SRCALPHA)
                pygame.draw.rect(glow_surf,
                                 (*color_main, 80),
                                 (0, 0, cw + 20, ch + 20),
                                 border_radius=15)
                surface.blit(glow_surf, (cx - 10, cy - 10))

            # Border (double)
            border_color = (255, 255, 255) if is_hover else color_main
            border_width = 3 if is_hover else 2
            pygame.draw.rect(surface, border_color,
                             (cx, cy, cw, ch),
                             border_width, border_radius=12)
            pygame.draw.rect(surface, (*color_main, 150),
                             (cx + 4, cy + 4, cw - 8, ch - 8),
                             1, border_radius=10)

        def _draw_card_portrait(self, surface, cx, cy, hero_type, stats,
                                  color_main, owned):
            """Portrait box + mini pixel art hero"""
            portrait_size = 90
            portrait_x = cx + 15
            portrait_y = cy + 15

            # Portrait BG dengan gradient
            for i in range(portrait_size):
                t = i / portrait_size
                r = int(15 + t * 10)
                g_c = int(20 + t * 10)
                b = int(30 + t * 15)
                pygame.draw.line(surface, (r, g_c, b),
                                 (portrait_x, portrait_y + i),
                                 (portrait_x + portrait_size,
                                  portrait_y + i))

            # Portrait border
            pygame.draw.rect(surface, color_main,
                             (portrait_x, portrait_y,
                              portrait_size, portrait_size),
                             2, border_radius=6)

            # Inner shadow
            pygame.draw.rect(surface, (0, 0, 0, 100),
                             (portrait_x + 2, portrait_y + 2,
                              portrait_size - 4, portrait_size - 4),
                             1, border_radius=4)

            # DRAW MINI HERO PORTRAIT
            HeroPortraits.draw(
                surface, hero_type,
                portrait_x + portrait_size // 2,
                portrait_y + portrait_size // 2 + 5,
                stats, owned)

        def _draw_card_info(self, surface, cx, cy, cw, stats, color_main,
                              owned):
            """Name, title, role badge (kanan portrait)"""
            info_x = cx + 15 + 90 + 15  # portrait_x + portrait_size + 15
            info_y = cy + 15

            # Name
            try:
                name_font = pygame.font.Font(None, 32)
            except:
                name_font = self.ui.font_medium

            # Name shadow
            name_shadow = name_font.render(stats["name"], True, (0, 0, 0))
            name_shadow.set_alpha(150)
            surface.blit(name_shadow, (info_x + 1, info_y + 1))

            # Name main
            name_color = (200, 200, 200) if owned else (255, 255, 255)
            name_surf = name_font.render(stats["name"], True, name_color)
            surface.blit(name_surf, (info_x, info_y))

            # Title
            title_color = (180, 180, 180) if owned else (200, 200, 220)
            title_surf = self.ui.font_tiny.render(stats["title"], True,
                                                    title_color)
            surface.blit(title_surf, (info_x, info_y + 30))

            # Role badge
            role_bg = pygame.Rect(info_x, info_y + 48, 100, 22)
            pygame.draw.rect(surface, (0, 0, 0, 150), role_bg,
                             border_radius=11)
            pygame.draw.rect(surface, color_main, role_bg, 1,
                             border_radius=11)
            role_surf = self.ui.font_tiny.render(
                stats["role"].upper(), True, color_main)
            role_rect = role_surf.get_rect(center=role_bg.center)
            surface.blit(role_surf, role_rect)

        def _draw_card_stats(self, surface, cx, cy, cw, stats):
            """Stats row (HP, DMG, RNG, SPD) dengan icons"""
            stats_y = cy + 120
            stat_items = [
                ("HP", stats["hp"], (255, 100, 100)),
                ("DMG", stats["damage"], (255, 200, 100)),
                ("RNG", stats["range"], (100, 200, 255)),
                ("SPD", stats["speed"], (100, 255, 150)),
            ]

            stat_width = (cw - 30) // 4
            for idx, (icon, value, icon_color) in enumerate(stat_items):
                stat_x = cx + 15 + idx * stat_width

                # Stat card mini
                stat_bg = pygame.Rect(stat_x, stats_y, stat_width - 5, 35)
                pygame.draw.rect(surface, (0, 0, 0, 100), stat_bg,
                                 border_radius=6)
                pygame.draw.rect(surface, (255, 255, 255, 30),
                                 stat_bg, 1, border_radius=6)

                # Label (di atas)
                try:
                    icon_font = pygame.font.Font(None, 14)
                except:
                    icon_font = self.ui.font_tiny
                icon_surf = icon_font.render(icon, True, icon_color)
                icon_rect = icon_surf.get_rect(
                    center=(stat_x + (stat_width - 5) // 2, stats_y + 8))
                surface.blit(icon_surf, icon_rect)

                # Value (di bawah)
                value_str = str(value)
                if isinstance(value, float):
                    value_str = f"{value:.1f}"

                try:
                    value_font = pygame.font.Font(None, 20)
                except:
                    value_font = self.ui.font_small
                value_surf = value_font.render(
                    value_str, True, (255, 255, 255))
                value_rect = value_surf.get_rect(
                    center=(stat_x + (stat_width - 5) // 2, stats_y + 24))
                surface.blit(value_surf, value_rect)

        def _draw_card_skill(self, surface, cx, cy, cw, stats, color_main):
            """Skill info dengan background box + word wrap"""
            skill_y = cy + 160
            skill_box_h = 50

            # Skill background box
            skill_bg = pygame.Rect(cx + 15, skill_y, cw - 30, skill_box_h)
            pygame.draw.rect(surface, (0, 0, 0, 120), skill_bg,
                             border_radius=6)
            pygame.draw.rect(surface, (*color_main, 100), skill_bg, 1,
                             border_radius=6)

            # Skill icon (glowing dot)
            pygame.draw.circle(surface, color_main,
                               (cx + 28, skill_y + 12), 5)
            pygame.draw.circle(surface, (255, 255, 255),
                               (cx + 26, skill_y + 10), 2)

            # Skill name
            try:
                skill_font = pygame.font.Font(None, 18)
            except:
                skill_font = self.ui.font_small
            skill_surf = skill_font.render(
                stats["skill_name"], True, color_main)
            surface.blit(skill_surf, (cx + 42, skill_y + 5))

            # Skill desc (word wrap ke 2 baris)
            desc = stats["skill_desc"]
            desc_font = pygame.font.Font(None, 13)

            # Word wrap
            words = desc.split()
            lines = []
            current_line = ""
            max_width = cw - 55

            for word in words:
                test_line = current_line + word + " "
                if desc_font.size(test_line)[0] > max_width:
                    if current_line:
                        lines.append(current_line.strip())
                    current_line = word + " "
                else:
                    current_line = test_line

            if current_line:
                lines.append(current_line.strip())

            # Draw max 2 lines
            for i, line in enumerate(lines[:2]):
                desc_surf = desc_font.render(line, True, (180, 180, 200))
                surface.blit(desc_surf, (cx + 42, skill_y + 25 + i * 12))

        def _draw_card_button(self, surface, cx, cy, cw, ch, hero_type,
                              stats, owned, can_afford, is_hover):
            """Summon button — pakai gold in-game"""
            from settings import get_all_hero_types
            g = self.game

            btn_y = cy + ch - 38
            btn_rect = pygame.Rect(cx + 20, btn_y, cw - 40, 32)

            # Register button
            g.ui_buttons[f'shop_buy_{hero_type}'] = btn_rect

            # Get summon cost
            all_heroes = get_all_hero_types()
            hero_stats = all_heroes.get(hero_type, stats)
            cost = hero_stats.get("cost", 400)
            can_afford_gold = g.gold >= cost

            # Determine button state
            if owned:
                # ACTIVE (sudah di-summon di battle)
                self._draw_button_owned(surface, btn_rect)
                btn_text = "ACTIVE IN BATTLE"
                btn_color = (100, 200, 100)
            elif len(g.heroes) >= MAX_HEROES_OWNED:
                # MAX HEROES
                self._draw_button_max(surface, btn_rect)
                btn_text = f"MAX HEROES ({MAX_HEROES_OWNED})"
                btn_color = (200, 100, 100)
            elif not can_afford_gold:
                # CANNOT AFFORD
                self._draw_button_cant_afford(surface, btn_rect)
                btn_text = f"SUMMON ({cost}G)"
                btn_color = (255, 150, 150)
            else:
                # CAN SUMMON
                self._draw_button_buy(surface, btn_rect, is_hover)
                btn_text = f"SUMMON ({cost}G)"
                btn_color = (255, 255, 255)

            # Button text
            try:
                btn_font = pygame.font.Font(None, 22)
            except:
                btn_font = self.ui.font_small
            btn_surf = btn_font.render(btn_text, True, btn_color)
            btn_text_rect = btn_surf.get_rect(center=btn_rect.center)
            surface.blit(btn_surf, btn_text_rect)

        def _draw_button_owned(self, surface, btn_rect):
            """OWNED button style"""
            pygame.draw.rect(surface, (40, 60, 40), btn_rect,
                             border_radius=6)
            pygame.draw.rect(surface, (80, 120, 80), btn_rect, 2,
                             border_radius=6)

        def _draw_button_max(self, surface, btn_rect):
            """MAX HEROES button style"""
            pygame.draw.rect(surface, (60, 40, 40), btn_rect,
                             border_radius=6)
            pygame.draw.rect(surface, (120, 80, 80), btn_rect, 2,
                             border_radius=6)

        def _draw_button_buy(self, surface, btn_rect, is_hover):
            """Green buy button - OPTIMIZED"""
            # Solid green (bukan gradient per-pixel)
            pygame.draw.rect(surface, (40, 170, 40), btn_rect,
                             border_radius=6)
            # Lighter top half
            top_rect = pygame.Rect(btn_rect.x, btn_rect.y,
                                    btn_rect.width, btn_rect.height // 2)
            pygame.draw.rect(surface, (50, 190, 50), top_rect,
                             border_radius=6)

            border_col = (150, 255, 150) if is_hover else (100, 200, 100)
            pygame.draw.rect(surface, border_col, btn_rect,
                             2, border_radius=6)

            if is_hover:
                glow_surf = pygame.Surface(
                    (btn_rect.width + 10, btn_rect.height + 10),
                    pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (100, 255, 100, 100),
                                 (0, 0, btn_rect.width + 10,
                                  btn_rect.height + 10),
                                 border_radius=8)
                surface.blit(glow_surf,
                             (btn_rect.x - 5, btn_rect.y - 5))

        def _draw_button_cant_afford(self, surface, btn_rect):
            """Red-gray button (can't afford)"""
            pygame.draw.rect(surface, (60, 30, 30), btn_rect,
                             border_radius=6)
            pygame.draw.rect(surface, (150, 80, 80), btn_rect, 2,
                             border_radius=6)




    # ================================


# ====================================================================
# hover_indicators.py
# ====================================================================
class _NS_hover_indicators:
    """Namespace hover_indicators - isi asli tidak diubah."""

    # ui_components/hover_indicators.py
    # Hover indicators (tower range, slot highlight)
    # ================================



    class HoverIndicators(BaseUIComponent):
        """
        Handle hover states & visual indicators:
        - Tower range circle saat hover
        - Tower tooltip info
        - Build slot glow saat hover
        - "CLICK TO BUILD" hint
        """

        def update(self):
            """Update hover states (detect what mouse is hovering)"""
            g = self.game
            g.hovered_tower = None
            g.hovered_slot = None

            # Skip kalau popup/shop terbuka
            if g.shop_open or g.popup_target or g.build_popup_slot:
                return

            # Check tower hover
            for t in g.towers:
                if not t.alive:
                    continue
                dist = math.hypot(t.x - g.mouse_x, t.y - g.mouse_y)
                if dist <= 25:
                    g.hovered_tower = t
                    return

            # Check build slot hover
            for slot in g.build_slots_blue:
                if slot['taken']:
                    continue
                dist = math.hypot(slot['x'] - g.mouse_x,
                                  slot['y'] - g.mouse_y)
                if dist <= 20:
                    g.hovered_slot = slot
                    return

        def draw(self, surface):
            """Draw hover indicators"""
            g = self.game

            # Tower hover: range circle + tooltip
            if g.hovered_tower:
                self._draw_tower_range_hover(surface, g.hovered_tower)
                self._draw_tower_tooltip(surface, g.hovered_tower)

            # Build slot hover: highlight
            if g.hovered_slot:
                self._draw_slot_hover(surface, g.hovered_slot)

        # ═══════════════════════════════════════
        # TOWER HOVER
        # ═══════════════════════════════════════

        def _draw_tower_range_hover(self, surface, tower):
            """Range circle saat hover tower"""
            pulse = math.sin(self.game.animation_time * 0.1) * 0.2 + 0.8

            # OPTIMASI: dulu Surface 1280x720 tiap frame hanya untuk
            # satu lingkaran. Sekarang surface sebesar lingkarannya
            # saja, diambil dari pool.
            from mobile.perf import POOL as _POOL
            _rad = int(tower.range)
            _size = _rad * 2 + 8
            _ox = int(tower.x) - _rad - 4
            _oy = int(tower.y) - _rad - 4
            range_surf = _POOL.get(_size, _size)
            _cx_l, _cy_l = _rad + 4, _rad + 4

            # Fill area
            pygame.draw.circle(range_surf,
                               (100, 200, 255, int(30 * pulse)),
                               (_cx_l, _cy_l), _rad)

            # Outer border
            pygame.draw.circle(range_surf,
                               (150, 220, 255, int(180 * pulse)),
                               (_cx_l, _cy_l), _rad, 2)

            # Dashed inner border (rotating)
            num_dashes = 24
            for i in range(num_dashes):
                if i % 2 == 0:
                    start_angle = (i / num_dashes) * math.pi * 2 + \
                                  self.game.animation_time * 0.02
                    end_angle = ((i + 1) / num_dashes) * math.pi * 2 + \
                                self.game.animation_time * 0.02

                    for a in [start_angle, end_angle]:
                        dx = math.cos(a) * (tower.range - 3)
                        dy = math.sin(a) * (tower.range - 3)
                        pygame.draw.circle(range_surf,
                                           (255, 255, 255, 200),
                                           (int(_cx_l + dx),
                                            int(_cy_l + dy)), 2)

            surface.blit(range_surf, (_ox, _oy))
            _POOL.release(range_surf)

        def _draw_tower_tooltip(self, surface, tower):
            """Small tooltip di atas tower"""
            tooltip_x = int(tower.x)
            tooltip_y = int(tower.y - 60)

            lines = [
                f"{tower.name} Lv.{tower.level}",
                f"DMG: {tower.damage}  RNG: {tower.range}",
                f"Kills: {tower.kills}",
            ]

            font = pygame.font.Font(None, 14)

            # Calculate size
            max_width = 0
            total_height = 0
            line_surfs = []
            for line in lines:
                surf = font.render(line, True, (255, 255, 255))
                line_surfs.append(surf)
                max_width = max(max_width, surf.get_width())
                total_height += surf.get_height() + 2

            # Background
            bg_w = max_width + 12
            bg_h = total_height + 6
            bg_x = tooltip_x - bg_w // 2
            bg_y = tooltip_y - bg_h

            # Shadow
            shadow = pygame.Surface((bg_w + 4, bg_h + 4), pygame.SRCALPHA)
            pygame.draw.rect(shadow, (0, 0, 0, 100),
                             (2, 2, bg_w, bg_h), border_radius=4)
            surface.blit(shadow, (bg_x - 2, bg_y - 2))

            # BG
            pygame.draw.rect(surface, (20, 25, 40),
                             (bg_x, bg_y, bg_w, bg_h),
                             border_radius=4)
            pygame.draw.rect(surface, tower.color,
                             (bg_x, bg_y, bg_w, bg_h),
                             2, border_radius=4)

            # Draw lines
            y = bg_y + 4
            for i, line_surf in enumerate(line_surfs):
                text_rect = line_surf.get_rect(
                    centerx=tooltip_x, top=y)
                surface.blit(line_surf, text_rect)
                y += line_surf.get_height() + 2

            # Arrow pointing down
            arrow_pts = [
                (tooltip_x - 4, bg_y + bg_h),
                (tooltip_x, bg_y + bg_h + 5),
                (tooltip_x + 4, bg_y + bg_h),
            ]
            pygame.draw.polygon(surface, tower.color, arrow_pts)

        # ═══════════════════════════════════════
        # SLOT HOVER
        # ═══════════════════════════════════════

        def _draw_slot_hover(self, surface, slot):
            """Highlight glow saat hover build slot"""
            pulse = math.sin(self.game.animation_time * 0.15) * 0.3 + 0.7

            # Glow
            glow_surf = pygame.Surface((80, 80), pygame.SRCALPHA)
            for r in range(35, 15, -3):
                alpha = int((35 - r) * 6 * pulse)
                if alpha > 0:
                    pygame.draw.circle(glow_surf,
                                       (100, 200, 255, alpha),
                                       (40, 40), r)
            surface.blit(glow_surf, (slot['x'] - 40, slot['y'] - 40))

            # Click hint
            hint_font = pygame.font.Font(None, 14)
            hint_text = hint_font.render("TAP TO BUILD", True,
                                         (255, 255, 255))
            hint_bg = pygame.Rect(slot['x'] - 40, slot['y'] - 32, 80, 12)
            pygame.draw.rect(surface, (0, 0, 0, 200), hint_bg,
                             border_radius=3)
            pygame.draw.rect(surface, (100, 200, 255), hint_bg, 1,
                             border_radius=3)
            hint_rect = hint_text.get_rect(center=hint_bg.center)
            surface.blit(hint_text, hint_rect)





    class Notification(BaseUIComponent):
        """Popup notification (achievements, alerts, dll)"""

        def __init__(self, ui_renderer):
            super().__init__(ui_renderer)
            self.messages = []  # queue

        def add_notification(self, text, color=(255, 255, 255)):
            """Add notification to queue"""
            self.messages.append({
                'text': text,
                'color': color,
                'timer': 180,  # 3 detik
            })

        def draw(self, surface):
            """Draw notifications"""
            # ... logic
            pass




    # ================================


# ====================================================================
# notification.py
# ====================================================================
class _NS_notification:
    """Namespace notification - isi asli tidak diubah."""

    class Notification(BaseUIComponent):
        """Popup notification (achievements, alerts, dll)"""

        def __init__(self, ui_renderer):
            super().__init__(ui_renderer)
            self.messages = []  # queue

        def add_notification(self, text, color=(255, 255, 255)):
            """Add notification to queue"""
            self.messages.append({
                'text': text,
                'color': color,
                'timer': 180,  # 3 detik
            })

        def draw(self, surface):
            """Draw notifications"""
            # ... logic
            pass

# ====================================================================
# overlay.py
# ====================================================================
class _NS_overlay:
    """Namespace overlay - isi asli tidak diubah."""

    # ui_components/overlay.py
    # Victory / Defeat overlay screen
    # ================================



    class Overlay(BaseUIComponent):
        """
        Victory/Defeat elaborate screen:
        - Animated background dengan rays & glow
        - Big title dengan shadow layers
        - Sparkles (victory only)
        - Stats panel (score, waves, kills, combo)
        - Level unlocked popup (victory + next level available)
        - Action hint (press R/N/ESC)
        - Achievement count
        """

        def __init__(self, ui_renderer):
            super().__init__(ui_renderer)
            # Trigger unlock popup delay
            self.unlock_popup_delay = 90  # 1.5 detik delay
            self.unlock_popup_timer = 0

        def draw(self, surface, title, color, subtitle, action):
            """Draw victory/defeat overlay"""
            g = self.game

            # Animated backdrop
            # OPTIMASI: gradien ini tidak pernah berubah, tapi dulu
            # digambar ulang 720 baris SETIAP frame.
            from mobile.perf import cached_render

            def _paint_gradient(surf):
                for i in range(SCREEN_HEIGHT):
                    alpha = int(180 * (1 - abs(i - SCREEN_HEIGHT / 2) /
                                       (SCREEN_HEIGHT / 2) * 0.3))
                    pygame.draw.line(surf, (10, 10, 20, alpha),
                                     (0, i), (SCREEN_WIDTH, i))

            surface.blit(cached_render(("end_gradient", SCREEN_WIDTH,
                                        SCREEN_HEIGHT),
                                       SCREEN_WIDTH, SCREEN_HEIGHT,
                                       _paint_gradient), (0, 0))

            cx = SCREEN_WIDTH // 2
            cy = SCREEN_HEIGHT // 2
            t = g.animation_time * 0.05

            # Draw layers (order matters)
            self._draw_rays(surface, cx, cy, color, t)
            self._draw_central_glow(surface, cx, cy, color)
            self._draw_title(surface, cx, cy, title, color, t)
            self._draw_sparkles(surface, cx, cy, title, color, t)
            self._draw_stats(surface, cx, cy, color)

            # ═══ LEVEL UNLOCKED POPUP (victory only) ═══
            if "VICTORY" in title:
                self._update_unlock_popup()
                self._draw_level_unlock_popup(surface, cx, cy)

            self._draw_action_hint(surface, cx, cy, action, t)
            self._draw_achievements(surface, cx, cy)

        def _update_unlock_popup(self):
            """Update timer for delayed popup"""
            if self.unlock_popup_timer < self.unlock_popup_delay:
                self.unlock_popup_timer += 1

        def _get_newly_unlocked_level(self):
            """
            Return level number kalau baru saja unlock next level.
            None kalau tidak ada level baru.
            """
            g = self.game
            from levels import get_next_level, get_level_config

            current_lvl = g.level_number
            next_lvl = get_next_level(current_lvl)

            if next_lvl is None:
                return None

            # Cek apakah level ini baru saja "diunlock"
            # Yaitu: level saat ini menang → next level jadi accessible
            completed = g.save_data.get('completed_levels', [])
            if current_lvl in completed:
                # Cek apakah next_lvl BELUM pernah dimenangkan
                # (kalau sudah, artinya bukan "newly unlocked")
                if next_lvl not in completed:
                    return next_lvl

            return None

        # ═══════════════════════════════════════
        # BACKGROUND EFFECTS
        # ═══════════════════════════════════════

        def _draw_rays(self, surface, cx, cy, color, t):
            """Draw rotating rays"""
            from mobile.perf import POOL as _POOL
            ray_surf = _POOL.get(SCREEN_WIDTH, SCREEN_HEIGHT)

            for i in range(12):
                angle = (i / 12) * math.pi * 2 + t * 0.3
                ray_len = 400 + math.sin(t + i) * 50
                end_x = cx + math.cos(angle) * ray_len
                end_y = cy + math.sin(angle) * ray_len

                perp_angle = angle + math.pi / 2
                perp_dist = 30
                p1 = (end_x + math.cos(perp_angle) * perp_dist,
                      end_y + math.sin(perp_angle) * perp_dist)
                p2 = (end_x - math.cos(perp_angle) * perp_dist,
                      end_y - math.sin(perp_angle) * perp_dist)

                pygame.draw.polygon(ray_surf, (*color, 30), [
                    (cx, cy), p1, p2])

            surface.blit(ray_surf, (0, 0))
            _POOL.release(ray_surf)

        def _draw_central_glow(self, surface, cx, cy, color):
            """Draw central glow circles"""
            from mobile.perf import POOL as _POOL
            for r in range(200, 50, -20):
                alpha = int((200 - r) / 200 * 60)
                glow_surf = _POOL.get(r * 2, r * 2)
                pygame.draw.circle(glow_surf, (*color, alpha),
                                   (r, r), r)
                surface.blit(glow_surf, (cx - r, cy - r))
                _POOL.release(glow_surf)

        # ═══════════════════════════════════════
        # TITLE
        # ═══════════════════════════════════════

        def _draw_title(self, surface, cx, cy, title, color, t):
            """Draw big title dengan shadow layers"""
            # Pulse effect
            pulse = math.sin(t * 2) * 0.05 + 1.0
            title_size = int(96 * pulse)

            try:
                title_font = pygame.font.Font(None, title_size)
            except:
                title_font = self.ui.font_huge

            # Shadow layers (depth effect)
            for offset in range(5, 0, -1):
                shadow = title_font.render(title, True, (0, 0, 0))
                shadow.set_alpha(60)
                shadow_rect = shadow.get_rect(
                    center=(cx + offset, cy - 180 + offset))
                surface.blit(shadow, shadow_rect)

            # Main title
            title_surf = title_font.render(title, True, color)
            title_rect = title_surf.get_rect(center=(cx, cy - 180))
            surface.blit(title_surf, title_rect)

        def _draw_sparkles(self, surface, cx, cy, title, color, t):
            """Draw sparkles (victory only)"""
            if "VICTORY" not in title:
                return

            for i in range(8):
                sparkle_angle = t + i * math.pi / 4
                sparkle_dist = 100 + math.sin(t + i) * 20
                sx = cx + math.cos(sparkle_angle) * sparkle_dist
                sy = cy - 180 + math.sin(sparkle_angle) * 30

                pygame.draw.circle(surface, (255, 255, 200),
                                   (int(sx), int(sy)), 3)
                pygame.draw.circle(surface, color,
                                   (int(sx), int(sy)), 2)

        # ═══════════════════════════════════════
        # STATS PANEL
        # ═══════════════════════════════════════

        def _draw_stats(self, surface, cx, cy, color):
            """Draw stats panel di tengah dengan NEW BEST badges"""
            g = self.game

            # Calculate match time
            import time as _time
            match_time = int(_time.time() - g.match_start_time)
            time_str = f"{match_time // 60}:{match_time % 60:02d}"

            # Stats dengan flag NEW BEST
            stats = [
                (f"Final Score", f"{g.score:,}",
                 getattr(g, 'new_best_score', False)),
                (f"Match Time", time_str,
                 getattr(g, 'new_best_time', False)),
                (f"Waves Survived", f"{g.wave_number}", False),
                (f"Total Kills", f"{g.total_kills}", False),
                (f"Max Combo", f"x{g.max_combo}", False),
            ]

            stats_font = pygame.font.Font(None, 24)
            label_font = pygame.font.Font(None, 18)
            badge_font = pygame.font.Font(None, 14)

            panel_w = 440
            panel_h = len(stats) * 32 + 20
            panel_x = cx - panel_w // 2
            panel_y = cy - 100

            # Panel BG
            panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            pygame.draw.rect(panel_surf, (20, 20, 30, 200),
                             (0, 0, panel_w, panel_h),
                             border_radius=8)
            pygame.draw.rect(panel_surf, color,
                             (0, 0, panel_w, panel_h), 2,
                             border_radius=8)
            surface.blit(panel_surf, (panel_x, panel_y))

            # Draw stat rows
            for i, (label, value, is_new_best) in enumerate(stats):
                y = panel_y + 15 + i * 32

                # Label (kiri)
                label_surf = label_font.render(label, True, (180, 180, 200))
                surface.blit(label_surf, (panel_x + 20, y))

                # NEW BEST badge (kalau ada)
                if is_new_best:
                    # Pulse effect
                    import math as _math
                    pulse = _math.sin(
                        pygame.time.get_ticks() * 0.008) * 0.3 + 0.7

                    badge_w = 90
                    badge_h = 22
                    badge_x = panel_x + panel_w // 2 - 30
                    badge_y = y - 3

                    badge_alpha = int(255 * pulse)

                    # Badge bg (gold gradient)
                    badge_surf = pygame.Surface(
                        (badge_w, badge_h), pygame.SRCALPHA)
                    for j in range(badge_h):
                        t = j / badge_h
                        r = int(200 + t * 55)
                        g_c = int(150 + t * 70)
                        b = int(30 + t * 30)
                        pygame.draw.line(
                            badge_surf, (r, g_c, b, badge_alpha),
                            (0, j), (badge_w, j))

                    # Border
                    pygame.draw.rect(badge_surf,
                                     (255, 255, 200, badge_alpha),
                                     (0, 0, badge_w, badge_h),
                                     2, border_radius=4)

                    surface.blit(badge_surf, (badge_x, badge_y))

                    # Badge text
                    badge_text = badge_font.render(
                        "★ NEW BEST!", True, (80, 40, 0))
                    badge_text_rect = badge_text.get_rect(
                        center=(badge_x + badge_w // 2,
                                badge_y + badge_h // 2))
                    surface.blit(badge_text, badge_text_rect)

                # Value (kanan) - color berubah kalau new best
                value_color = (255, 220, 100) if is_new_best else color
                value_surf = stats_font.render(value, True, value_color)
                value_rect = value_surf.get_rect(
                    topright=(panel_x + panel_w - 20, y - 2))
                surface.blit(value_surf, value_rect)

        # ═══════════════════════════════════════
        # LEVEL UNLOCKED POPUP (NEW!)
        # ═══════════════════════════════════════

        def _draw_level_unlock_popup(self, surface, cx, cy):
            """Draw popup kalau baru unlock next level"""
            # Cek delay dulu
            if self.unlock_popup_timer < self.unlock_popup_delay:
                return

            # Cek apakah ada next level yang baru unlock
            new_level = self._get_newly_unlocked_level()
            if new_level is None:
                return

            # Get level config
            from levels import get_level_config
            from bosses.boss_data import get_all_boss_types

            next_config = get_level_config(new_level)
            if not next_config:
                return

            # ═══ ANIMATION PROGRESS ═══
            # Slide in from right (30 frames after delay)
            elapsed_after_delay = self.unlock_popup_timer - \
                self.unlock_popup_delay
            slide_duration = 30

            if elapsed_after_delay < slide_duration:
                slide_progress = elapsed_after_delay / slide_duration
                # Ease out cubic
                eased = 1 - (1 - slide_progress) ** 3
                offset_x = int((1 - eased) * 400)
            else:
                offset_x = 0

            alpha = min(255, int(255 * (elapsed_after_delay / 15)))

            # ═══ POPUP POSITION (di kanan panel stats) ═══
            popup_w = 340
            popup_h = 220
            popup_x = cx + 220 + offset_x  # slide from right
            popup_y = cy - 100

            # ═══ POPUP BACKGROUND ═══
            # Shadow
            shadow_surf = pygame.Surface(
                (popup_w + 10, popup_h + 10), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surf, (0, 0, 0, 150),
                             (5, 5, popup_w, popup_h), border_radius=12)
            surface.blit(shadow_surf, (popup_x - 5, popup_y - 5))

            # Panel BG (gold gradient)
            popup_surf = pygame.Surface(
                (popup_w, popup_h), pygame.SRCALPHA)

            for i in range(popup_h):
                t = i / popup_h
                r = int(40 + t * 20)
                g_c = int(30 + t * 15)
                b = int(10 + t * 5)
                pygame.draw.line(popup_surf, (r, g_c, b, alpha),
                                 (0, i), (popup_w, i))

            # Gold border
            pygame.draw.rect(popup_surf, (255, 220, 100, alpha),
                             (0, 0, popup_w, popup_h),
                             3, border_radius=12)
            pygame.draw.rect(popup_surf, (255, 250, 180, alpha),
                             (2, 2, popup_w - 4, popup_h - 4),
                             1, border_radius=10)

            surface.blit(popup_surf, (popup_x, popup_y))

            # ═══ GLOW EFFECT (pulse) ═══
            pulse = math.sin(pygame.time.get_ticks() * 0.005) * 0.3 + 0.7
            glow_alpha = int(80 * pulse * (alpha / 255))

            glow_surf = pygame.Surface(
                (popup_w + 30, popup_h + 30), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (255, 220, 100, glow_alpha),
                             (0, 0, popup_w + 30, popup_h + 30),
                             border_radius=18)
            surface.blit(glow_surf, (popup_x - 15, popup_y - 15))
            surface.blit(popup_surf, (popup_x, popup_y))

            # ═══ LOCK ICON (opened) di top ═══
            icon_cx = popup_x + 40
            icon_cy = popup_y + 30

            # Lock body (opened)
            pygame.draw.rect(surface, (100, 100, 130),
                             (icon_cx - 8, icon_cy - 2, 16, 14),
                             border_radius=2)
            pygame.draw.rect(surface, (60, 60, 90),
                             (icon_cx - 8, icon_cy - 2, 16, 14),
                             2, border_radius=2)

            # Lock arc (opened - miring)
            pygame.draw.arc(surface, (100, 100, 130),
                            (icon_cx - 6, icon_cy - 18, 12, 18),
                            math.pi * 0.2, math.pi * 1.2, 3)

            # Keyhole (unlocked - green glow)
            keyhole_pulse = math.sin(
                pygame.time.get_ticks() * 0.008) * 0.3 + 0.7
            keyhole_alpha = int(255 * keyhole_pulse)

            keyhole_surf = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(keyhole_surf,
                               (100, 255, 100, keyhole_alpha),
                               (5, 5), 3)
            pygame.draw.circle(keyhole_surf,
                               (255, 255, 255, keyhole_alpha),
                               (5, 5), 1)
            surface.blit(keyhole_surf, (icon_cx - 5, icon_cy + 2))

            # ═══ "NEW LEVEL UNLOCKED!" TEXT ═══
            try:
                title_font = pygame.font.Font(None, 22)
            except:
                title_font = self.ui.font_small

            title_text = title_font.render(
                "NEW LEVEL UNLOCKED!", True, (255, 220, 100))

            # Shadow
            title_shadow = title_font.render(
                "NEW LEVEL UNLOCKED!", True, (0, 0, 0))
            title_shadow.set_alpha(100)
            surface.blit(title_shadow, (popup_x + 66, popup_y + 15))
            surface.blit(title_text, (popup_x + 65, popup_y + 14))

            # ═══ LEVEL NUMBER + NAME ═══
            try:
                lvl_font = pygame.font.Font(None, 28)
                name_font = pygame.font.Font(None, 22)
            except:
                lvl_font = self.ui.font_medium
                name_font = self.ui.font_small

            lvl_text = lvl_font.render(
                f"LEVEL {new_level}", True, (255, 255, 255))
            surface.blit(lvl_text, (popup_x + 65, popup_y + 35))

            name_text = name_font.render(
                next_config["name"], True, (200, 200, 220))
            surface.blit(name_text, (popup_x + 65, popup_y + 60))

            # ═══ SEPARATOR ═══
            pygame.draw.line(surface, (255, 220, 100),
                             (popup_x + 15, popup_y + 85),
                             (popup_x + popup_w - 15, popup_y + 85), 1)

            # ═══ BOSS PREVIEW (silhouette + name) ═══
            boss_type = next_config.get("true_boss", "abaddon")
            all_bosses = get_all_boss_types()
            boss_data = all_bosses.get(boss_type, {})

            boss_name = boss_data.get("name", "???")
            boss_class = boss_data.get("boss_class", "true")
            boss_color = boss_data.get("color", (150, 100, 200))
            boss_entrance = boss_data.get(
                "entrance_color", (150, 100, 200))

            # Mini boss silhouette (kiri)
            silhouette_cx = popup_x + 55
            silhouette_cy = popup_y + 135

            # Aura
            aura_pulse = math.sin(
                pygame.time.get_ticks() * 0.004) * 0.3 + 0.7
            aura_r = int(35 * aura_pulse)

            aura_surf = pygame.Surface(
                (aura_r * 2, aura_r * 2), pygame.SRCALPHA)
            for r in range(aura_r, 5, -3):
                a = int((aura_r - r) * 3)
                if a > 0:
                    pygame.draw.circle(aura_surf,
                                       (*boss_entrance, a),
                                       (aura_r, aura_r), r)
            surface.blit(aura_surf,
                         (silhouette_cx - aura_r,
                          silhouette_cy - aura_r))

            # Silhouette body (mini)
            body_pts = [
                (silhouette_cx - 15, silhouette_cy - 5),
                (silhouette_cx - 10, silhouette_cy - 20),
                (silhouette_cx, silhouette_cy - 25),
                (silhouette_cx + 10, silhouette_cy - 20),
                (silhouette_cx + 15, silhouette_cy - 5),
                (silhouette_cx + 18, silhouette_cy + 10),
                (silhouette_cx + 12, silhouette_cy + 22),
                (silhouette_cx - 12, silhouette_cy + 22),
                (silhouette_cx - 18, silhouette_cy + 10),
            ]

            pygame.draw.polygon(surface, (0, 0, 0), body_pts)
            pygame.draw.polygon(surface, boss_color, [
                (silhouette_cx - 13, silhouette_cy - 5),
                (silhouette_cx - 9, silhouette_cy - 18),
                (silhouette_cx, silhouette_cy - 23),
                (silhouette_cx + 9, silhouette_cy - 18),
                (silhouette_cx + 13, silhouette_cy - 5),
                (silhouette_cx + 16, silhouette_cy + 8),
                (silhouette_cx + 10, silhouette_cy + 20),
                (silhouette_cx - 10, silhouette_cy + 20),
                (silhouette_cx - 16, silhouette_cy + 8),
            ])

            # Crown spikes
            num_spikes = 5 if boss_class == "true" else 3
            for i in range(num_spikes):
                spike_offset = (i - num_spikes // 2) * 8
                spike_x = silhouette_cx + spike_offset
                pygame.draw.polygon(surface, (0, 0, 0), [
                    (spike_x - 3, silhouette_cy - 25),
                    (spike_x, silhouette_cy - 33),
                    (spike_x + 3, silhouette_cy - 25),
                ])

            # Glowing eyes
            eye_pulse = math.sin(
                pygame.time.get_ticks() * 0.008) * 0.3 + 0.7
            for eye_x_off in [-6, 6]:
                eye_x = silhouette_cx + eye_x_off
                eye_y = silhouette_cy - 12

                glow_surf = pygame.Surface((10, 10), pygame.SRCALPHA)
                for r in range(4, 0, -1):
                    a = int(200 * eye_pulse - r * 30)
                    if a > 0:
                        pygame.draw.circle(glow_surf,
                                           (*boss_entrance, a),
                                           (5, 5), r)
                surface.blit(glow_surf, (eye_x - 5, eye_y - 5))

                pygame.draw.circle(surface, boss_entrance,
                                   (eye_x, eye_y), 2)
                pygame.draw.circle(surface, (255, 255, 255),
                                   (eye_x, eye_y), 1)

            # ═══ BOSS INFO (kanan silhouette) ═══
            boss_info_x = popup_x + 100

            # Boss label
            boss_label = pygame.font.Font(None, 14).render(
                "FINAL BOSS", True, (255, 100, 100))
            surface.blit(boss_label, (boss_info_x, popup_y + 100))

            # Boss name
            boss_name_font = pygame.font.Font(None, 24)
            boss_name_surf = boss_name_font.render(
                boss_name, True, boss_entrance)
            surface.blit(boss_name_surf, (boss_info_x, popup_y + 115))

            # Difficulty preview
            diff_label = pygame.font.Font(None, 12).render(
                "DIFFICULTY", True, (150, 170, 190))
            surface.blit(diff_label, (boss_info_x, popup_y + 145))

            hp_mult = next_config.get("enemy_hp_mult", 1.0)
            diff_level = min(5, int(hp_mult * 2.5))

            for i in range(5):
                bar_x = boss_info_x + i * 14
                bar_y = popup_y + 160
                if i < diff_level:
                    if i >= 3:
                        bar_col = (255, 100, 80)
                    elif i >= 1:
                        bar_col = (255, 200, 80)
                    else:
                        bar_col = (100, 220, 100)
                else:
                    bar_col = (60, 60, 70)
                pygame.draw.rect(surface, bar_col,
                                 (bar_x, bar_y, 10, 8),
                                 border_radius=2)

            # ═══ "PLAY NEXT LEVEL" BUTTON ═══
            btn_w = popup_w - 30
            btn_h = 30
            btn_x = popup_x + 15
            btn_y = popup_y + popup_h - 40

            # Detect hover
            mx, my = pygame.mouse.get_pos()
            btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
            is_hover = btn_rect.collidepoint(mx, my)

            # Button glow
            if is_hover:
                btn_glow_surf = pygame.Surface(
                    (btn_w + 10, btn_h + 10), pygame.SRCALPHA)
                pygame.draw.rect(btn_glow_surf,
                                 (100, 255, 100, 120),
                                 (0, 0, btn_w + 10, btn_h + 10),
                                 border_radius=8)
                surface.blit(btn_glow_surf,
                             (btn_x - 5, btn_y - 5))

            # Button bg
            btn_color = (40, 180, 60) if is_hover else (30, 140, 50)
            border_col = (150, 255, 150) if is_hover else (100, 200, 100)

            pygame.draw.rect(surface, btn_color,
                             (btn_x, btn_y, btn_w, btn_h),
                             border_radius=6)
            pygame.draw.rect(surface, border_col,
                             (btn_x, btn_y, btn_w, btn_h),
                             2, border_radius=6)

            # Button text
            try:
                btn_font = pygame.font.Font(None, 22)
            except:
                btn_font = self.ui.font_small

            btn_text = btn_font.render(
                "▶ PLAY NEXT LEVEL", True, (255, 255, 255))
            btn_text_rect = btn_text.get_rect(center=btn_rect.center)

            # Shadow
            btn_shadow = btn_font.render(
                "▶ PLAY NEXT LEVEL", True, (0, 0, 0))
            surface.blit(btn_shadow,
                         (btn_text_rect.x + 1, btn_text_rect.y + 1))
            surface.blit(btn_text, btn_text_rect)

            # Register button untuk click handling
            g = self.game
            g.ui_buttons['play_next_level'] = btn_rect

        # ═══════════════════════════════════════
        # ACTION HINT & ACHIEVEMENTS
        # ═══════════════════════════════════════

        def _draw_action_hint(self, surface, cx, cy, action, t):
            """Draw action hint dengan pulse"""
            action_y = cy + 200
            hint_pulse = int(math.sin(t * 3) * 30 + 200)
            hint_color = (hint_pulse, hint_pulse, hint_pulse)

            action_font = pygame.font.Font(None, 22)
            action_surf = action_font.render(action, True, hint_color)
            action_rect = action_surf.get_rect(center=(cx, action_y))
            surface.blit(action_surf, action_rect)

        def _draw_achievements(self, surface, cx, cy):
            """Draw achievement count di bawah"""
            g = self.game

            if not g.achievements_unlocked:
                return

            ach_y = cy + 240
            ach_font = pygame.font.Font(None, 16)
            ach_text = ach_font.render(
                f"🏆 {len(g.achievements_unlocked)} Achievements Unlocked!",
                True, (255, 220, 50))
            ach_rect = ach_text.get_rect(center=(cx, ach_y))
            surface.blit(ach_text, ach_rect)




    # ================================


# ====================================================================
# popup_renderer.py
# ====================================================================
class _NS_popup_renderer:
    """Namespace popup_renderer - isi asli tidak diubah."""

    # ui_components/popup_renderer.py
    # Tower & Nexus popup renderer
    # ================================



    class PopupRenderer(BaseUIComponent):
        """
        Handle popup untuk tower & nexus (castle):
        - Dispatcher (cek type popup)
        - Nexus content (HP, stats, upgrade)
        - Tower content:
          * Lvl 1: path selection (4 tower types)
          * Lvl 2+: upgrade + sell buttons
        """

        def draw(self, surface):
            """Main popup dispatcher"""
            g = self.game
            target = g.popup_target

            if not target:
                return

            popup_w = 260
            popup_h = 260

            px = int(target.x) - popup_w // 2
            py = int(target.y) - popup_h - 40

            # Clamp posisi
            if px < 10:
                px = 10
            if px + popup_w > SCREEN_WIDTH - 10:
                px = SCREEN_WIDTH - popup_w - 10
            if py < TOP_BAR_HEIGHT + 10:
                py = int(target.y) + 40

            # Line pointer ke target
            pygame.draw.line(surface, GOLD,
                             (px + popup_w // 2, py + popup_h),
                             (int(target.x), int(target.y) - 10), 2)

            # Shadow
            shadow_surf = pygame.Surface((popup_w + 10, popup_h + 10),
                                         pygame.SRCALPHA)
            pygame.draw.rect(shadow_surf, (0, 0, 0, 150),
                             (5, 5, popup_w, popup_h), border_radius=8)
            surface.blit(shadow_surf, (px - 5, py - 5))

            # BG
            pygame.draw.rect(surface, (25, 30, 45),
                             (px, py, popup_w, popup_h),
                             border_radius=8)
            pygame.draw.rect(surface, GOLD,
                             (px, py, popup_w, popup_h),
                             2, border_radius=8)

            # Close button (X)
            self._draw_close_button(surface,
                                     px + popup_w - 25, py + 5,
                                     size=20,
                                     button_id='popup_close',
                                     style='rect')

            # ═══ DISPATCH CONTENT BERDASARKAN TYPE ═══
            if g.popup_type == "nexus_blue":
                self._draw_nexus_content(surface, px, py, popup_w,
                                         g.blue_base, True)
            elif g.popup_type == "nexus_red":
                self._draw_nexus_content(surface, px, py, popup_w,
                                         g.red_base, False)
            elif g.popup_type == "tower":
                self._draw_tower_content(surface, px, py, popup_w, target)

        # ═══════════════════════════════════════
        # NEXUS CONTENT
        # ═══════════════════════════════════════

        def _draw_nexus_content(self, surface, px, py, popup_w, nexus,
                                 is_own):
            """Content popup castle/nexus"""
            g = self.game
            team_color = BLUE_LIGHT if is_own else RED_LIGHT

            castle_names = {
                1: "OUTPOST", 2: "WATCHTOWER", 3: "FORTRESS",
                4: "STRONGHOLD", 5: "ROYAL CASTLE"
            }
            name = castle_names.get(nexus.level, "CITADEL")

            # Title
            title = self.ui.font_medium.render(
                f"{name} Lv.{nexus.level}", True, team_color)
            surface.blit(title, (px + 15, py + 8))

            y = py + 40

            # HP text
            hp_lbl = self.ui.font_small.render(
                f"HP: {nexus.hp}/{nexus.max_hp}", True, WHITE)
            surface.blit(hp_lbl, (px + 15, y))
            y += 20

            # HP bar
            bar_w = popup_w - 30
            self._draw_hp_bar(surface, px + 15, y, bar_w, 8,
                               nexus.hp / nexus.max_hp)
            y += 15

            # Stats
            nx_data = NEXUS_LEVELS[nexus.level]
            stats_t = self.ui.font_tiny.render(
                f"Minion Scale: x{nx_data['minion_scale']}",
                True, LIGHT_GRAY)
            surface.blit(stats_t, (px + 15, y))
            y += 14

            ai_t = self.ui.font_tiny.render(
                f"AI Level: {nx_data['minion_ai_level']}/5",
                True, LIGHT_GRAY)
            surface.blit(ai_t, (px + 15, y))
            y += 14

            dmg_t = self.ui.font_tiny.render(
                f"Damage: {nexus.damage}  Range: {nexus.range}",
                True, LIGHT_GRAY)
            surface.blit(dmg_t, (px + 15, y))
            y += 20

            # Upgrade button (hanya own castle)
            if is_own:
                self._draw_nexus_upgrade(surface, px, py, popup_w,
                                          nexus, y, castle_names)
            else:
                info_t = self.ui.font_tiny.render(
                    "[Enemy Castle - Destroy to Win!]", True, RED_LIGHT)
                info_rect = info_t.get_rect(
                    center=(px + popup_w // 2, y + 10))
                surface.blit(info_t, info_rect)

        def _draw_nexus_upgrade(self, surface, px, py, popup_w, nexus, y,
                                  castle_names):
            """Draw upgrade button untuk nexus"""
            g = self.game

            if nexus.level < MAX_NEXUS_LEVEL:
                cost = nexus.upgrade_cost()
                can_up = g.gold >= cost
                bg = (100, 200, 255) if can_up else DARK_GRAY

                # Next level preview
                next_name = castle_names.get(nexus.level + 1, "CITADEL")
                preview_t = self.ui.font_tiny.render(
                    f"Upgrade to: {next_name}", True, CYAN)
                surface.blit(preview_t, (px + 15, y))
                y += 16

                btn_rect = pygame.Rect(px + 15, y, popup_w - 30, 32)
                pygame.draw.rect(surface, bg, btn_rect,
                                 border_radius=4)
                pygame.draw.rect(surface, WHITE, btn_rect,
                                 2, border_radius=4)

                btn_t = self.ui.font_small.render(
                    f"UPGRADE ({cost}G)",
                    True, WHITE if can_up else GRAY)
                btn_text_rect = btn_t.get_rect(center=btn_rect.center)
                surface.blit(btn_t, btn_text_rect)

                g.ui_buttons['popup_upgrade_nexus'] = btn_rect
            else:
                max_t = self.ui.font_small.render(
                    "★ MAX LEVEL - CITADEL ★", True, YELLOW)
                max_rect = max_t.get_rect(
                    center=(px + popup_w // 2, y + 15))
                surface.blit(max_t, max_rect)

        # ═══════════════════════════════════════
        # TOWER CONTENT
        # ═══════════════════════════════════════

        def _draw_tower_content(self, surface, px, py, popup_w, tower):
            """Content popup tower"""
            g = self.game

            # Title
            title_text = f"{tower.name} Lv.{tower.level}"
            title = self.ui.font_medium.render(title_text, True, tower.color)
            surface.blit(title, (px + 15, py + 8))

            y = py + 40

            # HP
            hp_lbl = self.ui.font_small.render(
                f"HP: {tower.hp}/{tower.max_hp}", True, WHITE)
            surface.blit(hp_lbl, (px + 15, y))
            y += 18

            # HP bar
            bar_w = popup_w - 30
            self._draw_hp_bar(surface, px + 15, y, bar_w, 6,
                               tower.hp / tower.max_hp)
            y += 12

            # Stats
            stats_lines = [
                f"DMG: {tower.damage}  RNG: {tower.range}",
                f"Kills: {tower.kills}  Lane: {tower.lane.upper() if tower.lane else '-'}",
            ]
            for line in stats_lines:
                t = self.ui.font_tiny.render(line, True, LIGHT_GRAY)
                surface.blit(t, (px + 15, y))
                y += 13

            # Special abilities
            special = self._get_tower_specials(tower)
            if special:
                sp_text = " | ".join(special)
                sp_t = self.ui.font_tiny.render(sp_text, True, YELLOW)
                surface.blit(sp_t, (px + 15, y))
                y += 14

            y += 4

            # Enemy tower info
            if not tower.is_player_built:
                info_t = self.ui.font_tiny.render(
                    "[Enemy Tower]", True, RED_LIGHT)
                info_rect = info_t.get_rect(
                    center=(px + popup_w // 2, y + 10))
                surface.blit(info_t, info_rect)
                return

            # Max level
            if not tower.can_upgrade():
                self._draw_tower_max_level(surface, px, popup_w, tower, y)
                return

            # ═══ UPGRADE OPTIONS ═══
            # Level 1 → 2: pilih path (4 buttons)
            if tower.level == 1:
                self._draw_tower_path_buttons(surface, px, y, popup_w,
                                                tower)
            # Level 2+: upgrade + sell buttons
            else:
                self._draw_tower_upgrade_button(surface, px, y, popup_w,
                                                  tower)

        def _get_tower_specials(self, tower):
            """Get list special abilities untuk tower"""
            special = []
            if tower.splash > 0:
                special.append(f"Splash: {tower.splash}")
            if tower.slow > 0:
                special.append(f"Slow: {int(tower.slow * 100)}%")
            if tower.chain > 1:
                special.append(f"Chain: {tower.chain}")
            if tower.double_shot:
                special.append("DOUBLE SHOT")
            return special

        def _draw_tower_max_level(self, surface, px, popup_w, tower, y):
            """Draw max level info + sell button"""
            g = self.game

            max_t = self.ui.font_small.render(
                "★ MAX LEVEL ★", True, YELLOW)
            max_rect = max_t.get_rect(
                center=(px + popup_w // 2, y + 15))
            surface.blit(max_t, max_rect)

            y += 30
            sell_val = tower.sell_value()
            if sell_val > 0:
                sell_rect = pygame.Rect(px + 60, y, 100, 24)
                pygame.draw.rect(surface, RED_DARK, sell_rect,
                                 border_radius=3)
                pygame.draw.rect(surface, WHITE, sell_rect, 1,
                                 border_radius=3)
                sell_t = self.ui.font_tiny.render(
                    f"SELL {sell_val}G", True, WHITE)
                sell_text_rect = sell_t.get_rect(center=sell_rect.center)
                surface.blit(sell_t, sell_text_rect)
                g.ui_buttons['popup_sell_tower'] = sell_rect

        # ═══════════════════════════════════════
        # TOWER PATH SELECTION (Level 1 → 2)
        # ═══════════════════════════════════════

        def _draw_tower_path_buttons(self, surface, px, y, popup_w, tower):
            """Draw 4 tower path buttons (untuk lvl 1→2)"""
            g = self.game

            title_up = self.ui.font_tiny.render(
                "CHOOSE UPGRADE PATH:", True, YELLOW)
            surface.blit(title_up, (px + 15, y))
            y += 16

            btn_w = (popup_w - 40) // 2
            btn_h = 42

            paths = ["archer", "cannon", "ice", "mage"]
            for i, path_type in enumerate(paths):
                col = i % 2
                row = i // 2

                bx = px + 15 + col * (btn_w + 10)
                by = y + row * (btn_h + 6)

                self._draw_single_path_button(surface, bx, by, btn_w,
                                                btn_h, path_type, tower)

        def _draw_single_path_button(self, surface, bx, by, btn_w, btn_h,
                                        path_type, tower):
            """Draw satu path button"""
            g = self.game

            info = TOWER_TYPE_INFO[path_type]
            colors = TOWER_TYPE_COLORS[path_type]
            cost = tower.upgrade_cost(path_type)
            can_afford = g.gold >= cost

            btn_rect = pygame.Rect(bx, by, btn_w, btn_h)
            bg = colors["main"] if can_afford else DARK_GRAY

            pygame.draw.rect(surface, bg, btn_rect,
                             border_radius=3)
            pygame.draw.rect(surface, WHITE, btn_rect,
                             2, border_radius=3)

            name_t = self.ui.font_tiny.render(
                info["name"].replace(" Tower", ""),
                True, WHITE if can_afford else GRAY)
            surface.blit(name_t, (bx + 5, by + 3))

            cost_t = self.ui.font_tiny.render(
                f"{cost}G", True, WHITE if can_afford else GRAY)
            surface.blit(cost_t, (bx + 5, by + 17))

            spec_t = pygame.font.Font(None, 12).render(
                info["special"][:15],
                True, WHITE if can_afford else GRAY)
            surface.blit(spec_t, (bx + 5, by + 30))

            g.ui_buttons[f'popup_upgrade_path_{path_type}'] = btn_rect

        # ═══════════════════════════════════════
        # TOWER UPGRADE + SELL (Level 2+)
        # ═══════════════════════════════════════

        def _draw_tower_upgrade_button(self, surface, px, y, popup_w,
                                         tower):
            """Draw upgrade + sell button (untuk lvl 2+)"""
            g = self.game

            cost = tower.upgrade_cost()
            can_up = g.gold >= cost

            next_lvl = tower.level + 1
            next_stats = TOWER_UPGRADE_PATHS[tower.tower_type][next_lvl]

            # Preview
            preview_t = self.ui.font_tiny.render(
                f"Next Lv.{next_lvl}: DMG {next_stats['damage']} | HP {next_stats['hp']}",
                True, CYAN)
            surface.blit(preview_t, (px + 15, y))
            y += 14

            desc_t = self.ui.font_tiny.render(
                next_stats.get('desc', ''), True, YELLOW)
            surface.blit(desc_t, (px + 15, y))
            y += 16

            btn_w = (popup_w - 40) // 2

            # Upgrade button
            up_rect = pygame.Rect(px + 15, y, btn_w, 28)
            bg = CYAN if can_up else DARK_GRAY
            pygame.draw.rect(surface, bg, up_rect,
                             border_radius=4)
            pygame.draw.rect(surface, WHITE, up_rect, 1,
                             border_radius=4)
            up_t = self.ui.font_tiny.render(
                f"UPGRADE ({cost}G)",
                True, WHITE if can_up else GRAY)
            up_text_rect = up_t.get_rect(center=up_rect.center)
            surface.blit(up_t, up_text_rect)
            g.ui_buttons['popup_upgrade_tower'] = up_rect

            # Sell button
            sell_val = tower.sell_value()
            sell_rect = pygame.Rect(px + 25 + btn_w, y, btn_w, 28)
            pygame.draw.rect(surface, RED_DARK, sell_rect,
                             border_radius=4)
            pygame.draw.rect(surface, WHITE, sell_rect, 1,
                             border_radius=4)
            sell_t = self.ui.font_tiny.render(
                f"SELL ({sell_val}G)", True, WHITE)
            sell_text_rect = sell_t.get_rect(center=sell_rect.center)
            surface.blit(sell_t, sell_text_rect)
            g.ui_buttons['popup_sell_tower'] = sell_rect




    # ================================


# ====================================================================
# shop_hints.py
# ====================================================================
class _NS_shop_hints:
    """Namespace shop_hints - isi asli tidak diubah."""

    # ui_components/shop_hints.py
    # Floating hint di atas shop buildings
    # ================================



    class ShopHints(BaseUIComponent):
        """
        Draw floating "HERO SHOP" hint di atas shop building
        dengan animated pulse effect.
        """

        def draw(self, surface):
            """Draw hints di semua shop building"""
            g = self.game
            pulse = math.sin(g.animation_time * 0.06) * 3

            for shop_pos, label in [
                (g.map_renderer.radiant_shop_pos, "HERO SHOP"),
                (g.map_renderer.dire_shop_pos, "HERO SHOP"),
            ]:
                self._draw_single_hint(surface, shop_pos, label, pulse)

        def _draw_single_hint(self, surface, shop_pos, label, pulse):
            """Draw single hint di 1 shop"""
            sx, sy = shop_pos
            hint_y = sy - 65 + int(pulse)

            # Background
            hint_font = pygame.font.Font(None, 18)
            hint_text = hint_font.render(label, True, GOLD)
            hint_rect = hint_text.get_rect(center=(sx, hint_y))
            bg_rect = hint_rect.inflate(14, 6)

            # Glow
            glow_surf = pygame.Surface(
                (bg_rect.width + 10, bg_rect.height + 10),
                pygame.SRCALPHA)
            pygame.draw.rect(glow_surf,
                             (255, 200, 50, 30),
                             (0, 0, glow_surf.get_width(),
                              glow_surf.get_height()),
                             border_radius=8)
            surface.blit(glow_surf,
                         (bg_rect.x - 5, bg_rect.y - 5))

            pygame.draw.rect(surface, (20, 15, 5),
                             bg_rect, border_radius=5)
            pygame.draw.rect(surface, GOLD,
                             bg_rect, 2, border_radius=5)
            surface.blit(hint_text, hint_rect)

            # Sub-hint
            sub_font = pygame.font.Font(None, 14)
            sub_text = sub_font.render("TAP TO OPEN", True, LIGHT_GRAY)
            sub_rect = sub_text.get_rect(center=(sx, hint_y + 14))
            surface.blit(sub_text, sub_rect)


# ====================================================================
# DEDUPE: HeroPortraits
# ====================================================================
# hero_panel.py dulu punya salinan kelas HeroPortraits
# sendiri (238 baris) yang daftar metodenya IDENTIK dengan
# hero_portraits.py, dan tidak pernah diimpor dari luar.
# Salinan itu dibuang; rujukan diarahkan ke yang asli.
_NS_hero_panel.HeroPortraits = _NS_hero_portraits.HeroPortraits

