"""Ukur bbox hasil render boss ke canvas besar (cek kebutuhan ukuran canvas)."""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.getcwd())
import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))
from mobile import perf  # noqa: E402

perf.install_font_cache()
perf.Quality.apply("high")
import _core  # noqa: E402,F401
from _core import Game  # noqa: E402
from bosses.base_boss import Boss  # noqa: E402
from _entity import Minion  # noqa: E402

screen = pygame.display.set_mode((1280, 720))
g = Game(screen, level_number=1)
g.level_intro = None
g.boss_intro = None
lane = g.map_renderer.get_lane_path("mid")

TYPES = sys.argv[1:] or ["aeralith", "okeanora", "vraskhan", "gornak", "varkul",
                         "abaddon", "morgath", "aurethzar", "naraka", "kagetsuka"]
SIZE = 1400
C = SIZE // 2
canvas = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)

print(f"{'boss':16s} {'state':10s} {'bbox w×h':>12s}  half_needed")
for t in TYPES:
    b = Boss(t, lane)
    b.entrance_timer = 0
    b.x, b.y = 640.0, 360.0
    foe = Minion("goblin", "blue", "mid")
    foe.x, foe.y = 640.0 + b.range * 0.9, 360.0
    foes = [foe]
    for state in ("idle", "walk", "attack", "skill"):
        # bangun state
        for _ in range(4):
            b.update([] if state in ("idle", "walk") else foes, [], [])
        if state == "walk":
            b.x += 3.0
        if state == "attack":
            b.update(foes, [], [])
            b.timer = max(1, int(b.attack_cooldown * 0.6))
        if state == "skill":
            b.active_skill = "q"
            b.active_skill_timer = 25
        for _ in range(3):
            b.pulse += 0.05
            b.anim_time += 1
        canvas.fill((0, 0, 0, 0))
        b._render_scale = 1.0
        try:
            from bosses.base_boss import _get_boss_draw_func
            fn = _get_boss_draw_func(t)
            fn(canvas, b, C, C)
        except Exception as exc:
            print(f"{t:16s} {state:10s} ERROR {type(exc).__name__}: {exc}")
            continue
        finally:
            try:
                del b._render_scale
            except AttributeError:
                pass
        r = canvas.get_bounding_rect(min_alpha=8)
        half = max(abs(r.left - C), abs(r.right - C), abs(r.top - C),
                   abs(r.bottom - C))
        print(f"{t:16s} {state:10s} {r.width:5d}×{r.height:<5d}  {half}")
