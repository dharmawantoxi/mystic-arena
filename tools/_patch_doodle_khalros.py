#!/usr/bin/env python3
"""Patch renderer badan Khalros ke gaya doodle (pengganti sekali).

Menyisipkan helper doodle sebelum `_draw_khalros_body_raw` lalu mengganti
isi `_draw_khalros_body_raw` dari `def _draw_khalros_body_raw` sampai
`def _draw_beast_cape`. Idempotent: kalau sudah ada `_DL_HATCH`, skip.
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "bosses", "level2.py")

with io.open(SRC, "r", encoding="utf-8") as fh:
    text = fh.read()

if "_DL_HATCH" in text:
    print("SKIP: helper doodle sudah ada")
    raise SystemExit(0)

HELPERS = '''
    # ===================================================================
    # DOODLE PRIMITIVES  (sketsa spidol: outline gores + flat + arsiran)
    # ===================================================================
    def _dl_jit(i, seed):
        """Jitter deterministik -1..1 untuk goresan tangan (stabil)."""
        x = math.sin(i * 127.1 + seed * 311.7) * 43758.5453
        return (x - math.floor(x)) * 2.0 - 1.0

    def _doodle_seg(surface, color, p0, p1, width, seed, wobble=1.1):
        """Satu garis spidol ber-gores (beberapa sub-segmen offset)."""
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        n = max(1, int(math.hypot(dx, dy) / 7.0))
        for i in range(n):
            t0, t1 = i / n, (i + 1) / n
            j0 = _NS_khalros._dl_jit(seed * 3 + i, seed)
            j1 = _NS_khalros._dl_jit(seed * 3 + i + 1, seed)
            x0 = p0[0] + dx * t0 + j0 * wobble
            y0 = p0[1] + dy * t0 + j0 * wobble
            x1 = p0[0] + dx * t1 + j1 * wobble
            y1 = p0[1] + dy * t1 + j1 * wobble
            pygame.draw.line(surface, color, (int(x0), int(y0)),
                             (int(x1), int(y1)), int(max(1, width)))

    def _doodle_line(surface, color, pts, width=4, seed=0, wobble=1.1,
                     close=False):
        """Polyline spidol tebal; close=True menutup loop."""
        seq = pts[:]
        if close and len(seq) > 2:
            seq = seq + [seq[0]]
        for i in range(len(seq) - 1):
            _NS_khalros._doodle_seg(surface, color, seq[i], seq[i + 1],
                                    width, seed + i, wobble)

    def _doodle_poly(surface, fill, outline, pts, width=4, seed=0,
                     wobble=1.2):
        """Polygon doodle: isi flat + outline spidol tebal ber-gores."""
        pts = [(float(p[0]), float(p[1])) for p in pts]
        if fill is not None and len(pts) >= 3:
            pygame.draw.polygon(surface, fill,
                                [(int(p[0]), int(p[1])) for p in pts])
        if outline is not None:
            _NS_khalros._doodle_line(surface, outline, pts, width, seed,
                                     wobble, close=True)

    def _doodle_inside(poly, px, py):
        """Ray-cast point-in-polygon."""
        n = len(poly)
        inside = False
        j = n - 1
        for i in range(n):
            xi, yi = poly[i]
            xj, yj = poly[j]
            if ((yi > py) != (yj > py)) and \\
                    (px < (xj - xi) * (py - yi) / (yj - yi + 1e-9) + xi):
                inside = not inside
            j = i
        return inside

    def _doodle_hatch(surface, color, pts, spacing=6, angle=0.55,
                      width=1, alpha=150):
        """Arsiran coret-coretan diagonal di dalam poligon."""
        if len(pts) < 3:
            return
        pts = [(float(p[0]), float(p[1])) for p in pts]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        x0, x1 = min(xs), max(xs)
        y0, y1 = min(ys), max(ys)
        ca, sa = math.cos(angle), math.sin(angle)
        col = (color[0], color[1], color[2], _NS_khalros._alpha(alpha)) \\
            if len(color) >= 4 else (*color, int(alpha))
        edge = [(int(p[0]), int(p[1])) for p in pts]
        step = max(3, int(spacing))
        # garis miring: sampel dari kiri-bawah ke kanan-atas
        length = int((x1 - x0) + (y1 - y0))
        for k in range(0, length + 1, step):
            ax, ay = x0 + k, y1
            bx, by = ax + (y1 - y0), y0
            for _i in range(0, 18):
                t = _i / 18.0
                px = ax + (bx - ax) * t
                py = ay + (by - ay) * t
                if _NS_khalros._doodle_inside(edge, px, py):
                    pygame.draw.circle(surface, col, (int(px), int(py)),
                                       max(1, width))

    def _doodle_dot(surface, color, pts, r=3):
        """Marker titik spidol."""
        for (x, y) in pts:
            pygame.draw.circle(surface, color, (int(x), int(y)),
                               max(1, int(r)))

'''

ANCHOR = "    def _draw_khalros_body_raw(surface, cx, cy, facing, phase, action,\n"
i = text.index(ANCHOR)

# Sisipkan helper sebelum anchor
text = text[:i] + HELPERS + text[i:]

# Ganti isi _draw_khalros_body_raw sampai def _draw_beast_cape
start = text.index(ANCHOR)
end = text.index("    def _draw_beast_cape", start)

NEW_BODY = '''    def _draw_khalros_body_raw(surface, cx, cy, facing, phase, action,
                               attack_progress=0, boss=None):
        """Rig DOODLE - Khalros Beastlord, 100% prosedural.

        Gaya sketsa spidol: outline hitam tebal ber-gores, warna blok flat,
        arsiran coret-coretan, proporsi kartun. Koordinat lokal ~sama dgn
        rig masterwork supaya ukuran DI LAYAR tetap sekelas keluarga level-2:
        (0,0) = jangkar panggul, x maju (``facing``), y ke bawah; puncak
        tanduk -100, sol sepatu +66, jangkar kepala -58.
        """
        NS = _NS_khalros
        P = NS.PALETTE
        f = 1 if facing >= 0 else -1
        attack = action == "attack"
        ap = max(0.0, min(1.0, attack_progress)) if attack else 0.0
        pose = NS._attack_pose(ap) if attack else None

        # ═══ gerak badan + inersia sekunder (sama dgn rig masterwork) ═══
        breath = math.sin(phase * 0.72)
        lean = sway = root_y = tremble = 0
        cape_lag = beard_lag = 0.0
        stride = (0.0, 0.0, 0.0, 0.0, 0.0)
        if action == "walk":
            sw_a, sw_b, lf_a, lf_b, contact, bob = NS._stride_solver(
                "walk", phase)
            stride = (sw_a, sw_b, lf_a, lf_b, contact)
            lean = 2 * f
            root_y = int(bob)
            cape_lag = -3.0
            beard_lag = -2.0
        elif action == "attack":
            lean = int(pose["lean"]) * f
            root_y = int(pose["dip"])
            tremble = 1 if pose["tremble"] else 0
            cape_lag = -pose["lean"] * 0.55
            beard_lag = -pose["lean"] * 0.35
        elif action == "charge":
            lean = 7 * f
            root_y = 2
            cape_lag = -7.0
            beard_lag = -5.0
            stride = (0.42, -0.42, 1.5, 0.0, 0.0)
        elif action == "cast":
            lean = 1 * f
            root_y = int(breath * 1.4)
            cape_lag = math.sin(phase * 1.4) * 2.0
            beard_lag = math.sin(phase * 1.1) * 1.4
        else:
            lean = int(math.sin(phase * 0.5 + 1.1) * 1.5)
            root_y = int(breath * 1.9)
            cape_lag = math.sin(phase * 0.55) * 2.2
            beard_lag = math.sin(phase * 0.5) * 1.8
            stride = (math.sin(phase * 0.7) * 0.06,
                      -math.sin(phase * 0.7) * 0.06, 0.0, 0.0, 0.0)

        ox = int(cx) + lean + tremble
        oy = int(cy) + root_y
        rage = bool(boss is not None and getattr(boss, "active_skill", None)
                    in ("w", "r"))

        # ═══ lapisan belakang -> depan ═══
        NS._draw_beast_cape(surface, ox, oy, f, phase, action, cape_lag)
        NS._draw_hawk_companion(surface, ox - 27 * f, oy - 50, f, phase,
                                action, rage)
        NS._draw_legs(surface, ox, oy, f, phase, action, stride)
        NS._draw_loincloth(surface, ox, oy + 6, phase, sway, action=action)
        NS._draw_torso(surface, ox, oy - 1, phase, sway, action=action,
                       rage=rage, ap=ap)
        NS._draw_shoulders(surface, ox, oy - 6, phase, f, action=action,
                           rage=rage)
        if action in ("attack", "charge"):
            NS._draw_attack_arms(surface, ox, oy, f, phase,
                                 ap if attack else 0.0, action=action)
        else:
            NS._draw_idle_arms(surface, ox, oy, f, phase, action=action)
        NS._draw_khalros_head(surface, ox, oy - 58, f, phase, action=action,
                              rage=rage, beard_lag=beard_lag, ap=ap)
        # ── pass depan: senjata di atas kepala ──
        if action in ("attack", "charge"):
            NS._draw_attack_arms(surface, ox, oy, f, phase,
                                 ap if attack else 0.0, action=action,
                                 late=True)
        else:
            NS._draw_idle_arms(surface, ox, oy, f, phase, action=action,
                               late=True)

'''
text = text[:start] + NEW_BODY + text[end:]

with io.open(SRC, "w", encoding="utf-8") as fh:
    fh.write(text)
print("OK: helper doodle + _draw_khalros_body_raw diganti")
