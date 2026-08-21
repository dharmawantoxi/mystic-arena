# ================================
# mobile/hud.py
# HUD sentuh: pengganti SEMUA tombol keyboard & controller
#
# Peta pengganti:
#   Q / W / E / R  -> 4 tombol skill bulat (kanan bawah)
#   H              -> tombol SHOP
#   ESC            -> tombol JEDA (kanan atas)
#   F8 / debug     -> tombol kecil FPS (bisa dimatikan di rilis)
#   R (replay)     -> tombol ULANGI di layar kalah/menang
#   N (next level) -> tombol LEVEL BERIKUTNYA
#   SPACE (skip)   -> tombol LEWATI saat cinematic
#
# Semua tombol memakai ukuran >= 48x48 dp (rekomendasi Google) dan
# berada di dalam safe-area supaya tidak tertutup poni/gesture bar.
# ================================

import math

import pygame

from mobile import platform_utils as plat
from mobile.perf import Quality

GOLD = (255, 200, 70)
GOLD_DIM = (150, 118, 40)
BG = (16, 14, 22, 205)
BG_ACTIVE = (60, 48, 20, 235)
WHITE = (235, 235, 245)
GREY = (120, 120, 135)
RED = (210, 70, 70)

SKILL_LABELS = {"q": "Q", "w": "W", "e": "E", "r": "R"}
SKILL_NAMES = {"q": "SKILL 1", "w": "SKILL 2", "e": "SKILL 3", "r": "ULTI"}


class TouchButton:
    """Tombol sentuh sederhana: lingkaran atau kapsul."""

    def __init__(self, action, rect, label, sub="", shape="round",
                 color=GOLD, font_size=26, visible=True):
        self.action = action
        self.rect = pygame.Rect(rect)
        self.label = label
        self.sub = sub
        self.shape = shape
        self.color = color
        self.font_size = font_size
        self.visible = visible
        self.enabled = True
        self.cooldown = 0.0        # 0..1 (1 = belum siap)
        self.press_anim = 0.0
        # area sentuh diperbesar 12 px di tiap sisi (jempol tidak presisi)
        self.hit_rect = self.rect.inflate(24, 24)

    def contains(self, pos):
        return self.visible and self.hit_rect.collidepoint(pos)

    def press(self):
        self.press_anim = 1.0


class TouchHUD:
    """Kumpulan tombol layar + logika gambarnya."""

    def __init__(self, get_font):
        """get_font(size, style) -> pygame.font.Font (pakai cache game)."""
        self._get_font = get_font
        self.buttons = {}
        self.visible = True
        self.show_debug_button = True
        self._build_layout()

    # ── tata letak ────────────────────────────────────
    def _build_layout(self):
        safe = plat.get_safe_area()
        right = safe.right
        bottom = safe.bottom

        # ═══ 4 tombol skill, pola kipas di kanan bawah ═══
        r_big = 46
        r_small = 38
        cx, cy = right - 92, bottom - 92

        self.buttons["skill_r"] = TouchButton(
            "skill_r", pygame.Rect(cx - r_big, cy - r_big,
                                   r_big * 2, r_big * 2),
            "R", "ULTI", color=(255, 140, 60), font_size=30)

        positions = {
            "skill_e": (cx - 108, cy - 6),
            "skill_w": (cx - 74, cy - 100),
            "skill_q": (cx + 12, cy - 128),
        }
        for act, (bx, by) in positions.items():
            self.buttons[act] = TouchButton(
                act, pygame.Rect(bx - r_small, by - r_small,
                                 r_small * 2, r_small * 2),
                SKILL_LABELS[act[-1]], SKILL_NAMES[act[-1]])

        # ═══ Tombol aksi kiri bawah ═══
        self.buttons["shop"] = TouchButton(
            "shop", pygame.Rect(safe.left + 8, bottom - 68, 108, 52),
            "SHOP", shape="capsule", font_size=22)

        # ═══ Kanan atas: jeda + debug ═══
        self.buttons["pause"] = TouchButton(
            "pause", pygame.Rect(right - 62, safe.top + 6, 54, 54),
            "II", shape="round", font_size=26)

        self.buttons["debug"] = TouchButton(
            "debug", pygame.Rect(right - 128, safe.top + 6, 54, 54),
            "FPS", shape="round", font_size=17, color=(120, 200, 255))

        # ═══ Tombol kontekstual ═══
        self.buttons["skip"] = TouchButton(
            "skip", pygame.Rect(right - 150, bottom - 60, 140, 48),
            "LEWATI  >>", shape="capsule", font_size=20, visible=False)

        mid = plat.LOGICAL_WIDTH // 2
        self.buttons["replay"] = TouchButton(
            "replay", pygame.Rect(mid - 250, bottom - 96, 150, 56),
            "ULANGI", shape="capsule", font_size=22, visible=False)
        self.buttons["next_level"] = TouchButton(
            "next_level", pygame.Rect(mid - 80, bottom - 96, 190, 56),
            "LEVEL LANJUT", shape="capsule", font_size=20, visible=False,
            color=(120, 230, 140))
        self.buttons["menu"] = TouchButton(
            "menu", pygame.Rect(mid + 130, bottom - 96, 150, 56),
            "MENU", shape="capsule", font_size=22, visible=False)

        self.buttons["back"] = TouchButton(
            "back", pygame.Rect(safe.left + 8, safe.top + 6, 92, 50),
            "< BACK", shape="capsule", font_size=20, visible=False)

    # ── sinkronisasi dengan kondisi game ──────────────
    def sync(self, game, state, cinematic_active=False):
        """Tentukan tombol mana yang tampil & status cooldown-nya."""
        in_game = state == "game" and game is not None
        hero = getattr(game, "selected_hero", None) if in_game else None
        playing = in_game and getattr(game, "state", "") == "playing"
        ended = in_game and getattr(game, "state", "") in ("victory",
                                                           "defeat")

        for key in ("skill_q", "skill_w", "skill_e", "skill_r"):
            btn = self.buttons[key]
            btn.visible = bool(playing and hero and hero.alive
                               and not cinematic_active)
            if btn.visible:
                try:
                    cds = hero.get_skill_cooldowns()
                    btn.cooldown = max(0.0, min(1.0, cds.get(key[-1], 0.0)))
                    btn.enabled = hero.is_skill_ready(key[-1])
                except Exception:
                    btn.cooldown, btn.enabled = 0.0, True

        self.buttons["shop"].visible = bool(playing and not cinematic_active)
        self.buttons["pause"].visible = bool(playing and not cinematic_active)
        self.buttons["debug"].visible = bool(self.show_debug_button
                                             and not cinematic_active)
        self.buttons["skip"].visible = bool(cinematic_active)

        self.buttons["replay"].visible = ended
        self.buttons["menu"].visible = ended
        show_next = False
        if ended and getattr(game, "state", "") == "victory":
            try:
                from levels import get_next_level
                show_next = get_next_level(game.level_number) is not None
            except Exception:
                show_next = False
        self.buttons["next_level"].visible = show_next

        # animasi tekan
        for btn in self.buttons.values():
            if btn.press_anim > 0:
                btn.press_anim = max(0.0, btn.press_anim - 0.12)

    # ── input ─────────────────────────────────────────
    def hit_test(self, pos):
        """Kembalikan action id kalau titik sentuh mengenai tombol HUD."""
        if not self.visible:
            return None
        # urutan terbalik: tombol terakhir digambar = paling atas
        for btn in reversed(list(self.buttons.values())):
            if btn.contains(pos):
                btn.press()
                return btn.action
        return None

    def blocks(self, pos):
        return self.hit_test(pos) is not None

    # ── gambar ────────────────────────────────────────
    def draw(self, surface, anim_time=0.0):
        if not self.visible:
            return
        for btn in self.buttons.values():
            if not btn.visible:
                continue
            if btn.shape == "round":
                self._draw_round(surface, btn, anim_time)
            else:
                self._draw_capsule(surface, btn)

    def _draw_round(self, surface, btn, anim_time):
        cx, cy = btn.rect.center
        r = btn.rect.width // 2
        press = int(btn.press_anim * 3)

        if not Quality.cheap_alpha:
            # Gambar langsung: hindari surface sementara + alpha blit
            pygame.draw.circle(surface, (16, 14, 22), (cx, cy), r)
            pygame.draw.circle(surface, btn.color if btn.enabled else GREY,
                               (cx, cy), r, 3)
        else:
            base = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
            c = r + 4
            pygame.draw.circle(base, BG_ACTIVE if btn.press_anim else BG,
                               (c, c), r)
            ring = btn.color if btn.enabled else GREY
            pygame.draw.circle(base, ring, (c, c), r, 3)
            surface.blit(base, (cx - c, cy - c))

        # busur cooldown (searah jarum jam, sisa waktu)
        if btn.cooldown > 0.001:
            if Quality.cheap_alpha:
                shade = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(shade, (0, 0, 0, 150), (r, r), r)
                surface.blit(shade, (cx - r, cy - r))
            else:
                pygame.draw.circle(surface, (22, 20, 28), (cx, cy),
                                   int(r * btn.cooldown))
            end = -math.pi / 2 + (1.0 - btn.cooldown) * math.tau
            try:
                pygame.draw.arc(surface, btn.color,
                                pygame.Rect(cx - r + 2, cy - r + 2,
                                            r * 2 - 4, r * 2 - 4),
                                -math.pi / 2, end, 4)
            except Exception:
                pass

        font = self._get_font(btn.font_size + press, "body_bold")
        txt = font.render(btn.label, True,
                          WHITE if btn.enabled else (170, 170, 180))
        surface.blit(txt, txt.get_rect(center=(cx, cy - 2)))

        if btn.sub and btn.rect.width > 70:
            small = self._get_font(11, "body")
            sub = small.render(btn.sub, True, GOLD_DIM)
            surface.blit(sub, sub.get_rect(center=(cx, cy + 20)))

    def _draw_capsule(self, surface, btn):
        rect = btn.rect
        radius = rect.height // 2
        if not Quality.cheap_alpha:
            pygame.draw.rect(surface, (16, 14, 22), rect,
                             border_radius=radius)
            pygame.draw.rect(surface, btn.color if btn.enabled else GREY,
                             rect, 2, border_radius=radius)
        else:
            panel = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(panel, BG_ACTIVE if btn.press_anim else BG,
                             panel.get_rect(), border_radius=radius)
            pygame.draw.rect(panel, btn.color if btn.enabled else GREY,
                             panel.get_rect(), 2, border_radius=radius)
            surface.blit(panel, rect.topleft)

        font = self._get_font(btn.font_size, "body_bold")
        txt = font.render(btn.label, True, WHITE)
        surface.blit(txt, txt.get_rect(center=rect.center))


# ═══════════════════════════════════════════════════════
# PENERJEMAH AKSI HUD -> API GAME LAMA
# ═══════════════════════════════════════════════════════
def apply_hud_action(action, ctx):
    """
    ctx adalah objek/namespace dengan atribut:
        game, menu, state_ref (fungsi set state), fps_counter, debug
    Kembalikan True kalau aksi tertangani.
    """
    game = ctx.get("game")
    menu = ctx.get("menu")

    if action in ("skill_q", "skill_w", "skill_e", "skill_r"):
        if game is None:
            return False
        key = {"skill_q": pygame.K_q, "skill_w": pygame.K_w,
               "skill_e": pygame.K_e, "skill_r": pygame.K_r}[action]
        game.handle_key(key)
        plat.vibrate(18)
        return True

    if action == "shop" and game is not None:
        game.shop_open = not game.shop_open
        return True

    if action == "pause":
        ctx["request_pause"] = True
        return True

    if action == "debug":
        dbg = ctx.get("debug")
        if dbg is not None:
            dbg.toggle()
        return True

    if action == "skip" and game is not None:
        for name in ("level_intro", "boss_intro", "boss_death"):
            obj = getattr(game, name, None)
            if obj is None:
                continue
            try:
                if hasattr(obj, "handle_skip"):
                    obj.handle_skip(key=pygame.K_SPACE)
            except Exception:
                pass
        return True

    if action == "replay" and game is not None:
        game.replay_requested = True
        return True

    if action == "next_level" and game is not None:
        game.next_level_requested = True
        return True

    if action == "menu" and game is not None:
        game.return_to_menu_requested = True
        return True

    if action == "back" and menu is not None:
        menu.handle_key(pygame.K_ESCAPE)
        return True

    return False
