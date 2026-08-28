# ================================
# mobile/hud.py
# HUD sentuh: pengganti SEMUA tombol keyboard & controller
#
# Peta pengganti:
#   Q / W / E / R  -> 4 tombol skill bulat (kanan bawah) - DIHAPUS v27 auto-cast
#   H              -> tombol SHOP (buka via bangunan HERO SHOP)
#   ESC            -> tombol JEDA (kanan atas)
#   F8 / debug     -> tombol kecil FPS
#   R (replay)     -> REPLAY button on victory/defeat screen
#   N (next level) -> NEXT LEVEL button
#   SPACE (skip)   -> SKIP button during cinematic
#   G,T,C,B,D      -> Tactical commands HANYA di side panel (sesuai request user)
#                     D = ATTACK DAMAGE DEALER (fokus hero musuh
#                     dengan damage terbanyak)
#
# Semua tombol memakai ukuran >= 48x48 dp (rekomendasi Google) dan
# berada di dalam safe-area supaya tidak tertutup poni/gesture bar.
# ================================

import math

import pygame

from mobile import platform_utils as plat
from mobile.perf import Quality
import ui_theme

GOLD = (255, 200, 70)
GOLD_DIM = (150, 118, 40)
BG = (16, 14, 22, 205)
BG_ACTIVE = (60, 48, 20, 235)
WHITE = (235, 235, 245)
GREY = (120, 120, 135)
RED = (210, 70, 70)

# Sisi minimum area sentuh, dalam piksel logis 1280x720.
MIN_TAP = 80

SKILL_LABELS = {"q": "Q", "w": "W", "e": "E", "r": "R"}
SKILL_NAMES = {"q": "SKILL 1", "w": "SKILL 2", "e": "SKILL 3", "r": "ULTI"}

# Action tactical command (tombol side panel). Sama dengan konstanta
# di tactical_commands.TacticalCommand; dipakai main.py untuk melacak
# tombol yang sedang DITAHAN (mode HOLD: perintah terus aktif sampai
# jari/tuts dilepas).
TACTICAL_ACTIONS = ("gather", "protect_tower", "protect_castle",
                    "attack_boss", "attack_damage_dealer")


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
        self.cooldown = 0.0
        self.press_anim = 0.0
        self.hit_rect = self.rect.inflate(24, 24)
        if self.hit_rect.width < MIN_TAP or self.hit_rect.height < MIN_TAP:
            self.hit_rect = self.rect.inflate(
                max(0, MIN_TAP - self.rect.width),
                max(0, MIN_TAP - self.rect.height))

    def contains(self, pos):
        return self.visible and self.hit_rect.collidepoint(pos)

    def press(self):
        self.press_anim = 1.0


class TouchHUD:
    """Kumpulan tombol layar + logika gambarnya."""

    def __init__(self, get_font):
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

        # KIRI ATAS, TEPAT DI BAWAH PANEL GOLD
        # Kalau panel kanan tersedia, tombol jeda & FPS pindah ke sana
        self._panel_ada = plat.get_panel_rect() is not None
        _bx = max(22, safe.left + 6)
        _by = 76
        self.buttons["pause"] = TouchButton(
            "pause", pygame.Rect(_bx, _by, 52, 52),
            "II", shape="round", font_size=22)

        self.buttons["debug"] = TouchButton(
            "debug", pygame.Rect(_bx + 84, _by, 52, 52),
            "FPS", shape="round", font_size=16, color=(120, 200, 255))

        # Tombol kontekstual (victory/defeat/skip)
        self.buttons["skip"] = TouchButton(
            "skip", pygame.Rect(right - 170, bottom - 74, 160, 58),
            "SKIP  >>", shape="capsule", font_size=20, visible=False)

        mid = plat.LOGICAL_WIDTH // 2
        self.buttons["replay"] = TouchButton(
            "replay", pygame.Rect(mid - 310, bottom - 100, 165, 62),
            "REPLAY", shape="capsule", font_size=20, visible=False)
        self.buttons["next_level"] = TouchButton(
            "next_level", pygame.Rect(mid - 115, bottom - 100, 200, 62),
            "NEXT LEVEL", shape="capsule", font_size=18, visible=False,
            color=(120, 230, 140))
        self.buttons["menu"] = TouchButton(
            "menu", pygame.Rect(mid + 115, bottom - 100, 165, 62),
            "MENU", shape="capsule", font_size=22, visible=False)

        self.buttons["back"] = TouchButton(
            "back", pygame.Rect(safe.left + 8, safe.top + 6, 104, 58),
            "< BACK", shape="capsule", font_size=20, visible=False)

        # CATATAN: Tombol tactical GATHER/PROTECT TOWER/CASTLE/ATTACK BOSS
        # HANYA ada di side panel (mobile/sidepanel.py) sesuai permintaan user.
        # Tidak lagi di HUD bawah agar map bersih, dan indikator hanya muncul
        # sesaat di map saat command di-klik.

    # ── sinkronisasi dengan kondisi game ──────────────
    def sync(self, game, state, cinematic_active=False):
        in_game = state == "game" and game is not None
        playing = in_game and getattr(game, "state", "") == "playing"
        ended = in_game and getattr(game, "state", "") in ("victory", "defeat")

        panel = getattr(self, "_panel_ada", False)
        self.buttons["pause"].visible = bool(
            playing and not cinematic_active and not panel)
        self.buttons["debug"].visible = bool(
            self.show_debug_button and not cinematic_active and not panel)
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

        for btn in self.buttons.values():
            if btn.press_anim > 0:
                btn.press_anim = max(0.0, btn.press_anim - 0.12)

    # ── input ─────────────────────────────────────────
    def hit_test(self, pos):
        if not self.visible:
            return None
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
        ring = btn.color if btn.enabled else GREY

        if not Quality.cheap_alpha:
            pygame.draw.circle(surface, (16, 14, 22), (cx, cy), r)
            pygame.draw.circle(surface, ring, (cx, cy), r, 3)
        else:
            # Glow lembut di belakang tombol (cache -> murah)
            surface.blit(ui_theme._radial(r * 2 + 44, r * 2 + 44,
                                          btn.color, 46),
                         (cx - r - 22, cy - r - 22))
            base = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
            c = r + 4
            pygame.draw.circle(base, BG_ACTIVE if btn.press_anim else BG,
                               (c, c), r)
            pygame.draw.circle(base, ring, (c, c), r, 3)
            # Cincin dalam halus (identitas premium)
            pygame.draw.circle(base, (255, 255, 255),
                               (c, c), r - 6, 1)
            surface.blit(base, (cx - c, cy - c))

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
        ring = btn.color if btn.enabled else GREY
        if not Quality.cheap_alpha:
            pygame.draw.rect(surface, (16, 14, 22), rect,
                             border_radius=radius)
            pygame.draw.rect(surface, ring,
                             rect, 2, border_radius=radius)
        else:
            # Glow lembut (cache)
            surface.blit(ui_theme._radial(rect.w + 36, rect.h + 28,
                                          btn.color, 40),
                         (rect.x - 18, rect.y - 14))
            panel = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(panel, BG_ACTIVE if btn.press_anim else BG,
                             panel.get_rect(), border_radius=radius)
            pygame.draw.rect(panel, ring,
                             panel.get_rect(), 2, border_radius=radius)
            # Sorot tepi atas (kedalaman)
            pygame.draw.line(panel, (255, 255, 255),
                             (rect.w // 4, 2),
                             (rect.w * 3 // 4, 2), 1)
            surface.blit(panel, rect.topleft)

        font = self._get_font(btn.font_size, "body_bold")
        txt = font.render(btn.label, True, WHITE if btn.enabled else (170, 170, 180))
        surface.blit(txt, txt.get_rect(center=rect.center))


# ═══════════════════════════════════════════════════════
# PENERJEMAH AKSI HUD -> API GAME LAMA
# ═══════════════════════════════════════════════════════
def apply_hud_action(action, ctx):
    game = ctx.get("game")
    menu = ctx.get("menu")

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

    # Tactical commands tetap didukung via sidepanel (action sama).
    # MODE HOLD: penekanan tombol = MULAI menahan perintah; perintah
    # terus aktif sampai jari/tuts dilepas (pelepasan ditangani
    # main.py / KEYUP -> tactical.hold_end). Tap cepat tetap
    # berperilaku seperti tekanan biasa.
    if game is not None and getattr(game, 'tactical', None):
        if action in TACTICAL_ACTIONS:
            if action == "protect_tower":
                tower = getattr(game, 'selected_tower', None)
                if tower is not None and tower.team == "blue":
                    game.tactical.hold_start(action, tower)
                else:
                    game.tactical.hold_start(action)
            else:
                game.tactical.hold_start(action)
            return True

    return False
