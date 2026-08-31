"""
bosses/level1.py - Semua boss Level 1

Gabungan dari 4 file terpisah:
  - gornak               (mini boss)
  - morgath              (mini boss)
  - drakar               (mini boss)
  - abaddon              (TRUE BOSS)

Tiap boss dibungkus dalam kelas namespace `_NS_<nama>`
supaya PALETTE dan fungsi helper-nya TIDAK saling
menimpa - 91 simbol bentrok antar file boss, termasuk
PALETTE, _aacircle, _draw_shadow, _target_position.

Kode di dalam tiap namespace aslinya TIDAK diubah isinya; hanya
referensi antar-simbol yang diberi prefix.

KECUALI gornak: namespace-nya adalah Pixel Masterwork v2 + Skill FX v2.1
(Thorne bar: ramp 4-5 band, selout, tuft, specular cluster, dither,
FX world-space lewat _fx_scale). Regresi: tools/test_gornak_masterwork.py,
audit: tools/_audit_gornak_v2.py, sheet: tools/_shot_gornak_masterwork.py.

Entry point publik ada di bagian paling bawah file.
"""

import math
import random
import pygame

# Penanda: file ini berisi BANYAK boss (1 true + 3 mini).
# Dipakai heroes/__init__.py agar tidak menebak fungsi draw_*
# secara longgar, yang bisa mengembalikan boss yang salah.
_IS_LEVEL_BUNDLE = True

# ====================================================================
# GORNAK (ANTI-MAGE) - Mini Boss  ·  PROCEDURAL MASTERWORK RIG
# ====================================================================
import math
import pygame

try:                     # pass cahaya bersama; opsional supaya file boss
    import lighting as _lighting          # tetap bisa di-load sendiri
except Exception:        # pragma: no cover
    _lighting = None


class _NS_gornak:
    """Namespace gornak - Anti-Mage mini boss (Pixel Masterwork v2).

    Renderer 100% prosedural (tanpa PNG, sprite sheet, atau image.load).
    Standar Thorne v2 Pixel Masterwork + Thorne v2.1 Skill FX:

    * SATU bone rig 2D berlapis. Sendi dihitung tiap frame dari
      ``phase``/``action``. Telapak DIPATOK di ``GROUND_DY``.
    * Twin blade pose-driven; ujung bilah = sumber slash/proc Q.
    * Pixel-art: ramp 4-5 band + hue-shift, selout sisi bayangan,
      siluet cape/loincloth bergerigi (``_tuft_points``), specular
      cluster 1-2 px, dither 50% di kain/greave, key light kiri-atas.
    * Gornak adalah mini-boss 1:1 DAN hero (pipeline menormalkan).
      Ukuran arena dikunci paritas keluarga (HP bar, vs Abaddon);
      kepadatan detail naik, bukan bbox 1.5x di jalur boss.
    * Skill FX world-space lewat ``_fx_scale`` (= 1/_render_scale,
      cap 2.6): 3 fase (telegraph / aktivasi / steady), telegraph
      E=100 px dunia, R=180 px dunia.
    * Aura/mist/bayangan ter-cache (``_static``). Portrait LOD
      membuang FX arena.
    """

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    _STATIC_SURFACES = {}

    # ── SKALA BADAN ───────────────────────────────────────────────
    # Rujuran keluarga (diukur dari render, alpha>=100):
    #   boss 1x : morgath H82/W120, drakar H138/W190, abaddon H122/W150
    #   hero    : kaizen 75x83, grimjaw 74x79, vex 75x83, sylara 77x90
    # Renderer lama hanya 87x53 (W/H 0.61) -> terlihat seperti tiang kecil
    # di samping boss/hero lain. SCALE memperbesar rig, LIFT memindahkan
    # jangkar ke bawah (kepala lebih tinggi di atas titik (x,y)) supaya
    # pipeline HD hero menormalkan tingginya SAMA seperti hero lain, dan
    # stance/blade spread membuat rasio W/H masuk ~1.0 seperti sepupunya.
    SCALE = 1.32
    # Jangkar boss = pusat hitbox; LIFT memindahkan badan ke bawah supaya
    # wajah tidak tertutup HP bar boss (digambar di y-r-15..y-r-7) TAPI
    # tinggi di atas jangkar tetap besar - itu yang dipakai pipeline HD hero
    # untuk menormalkan ukuran, jadi hero Gornak tetap setinggi Kaizen/
    # Grimjaw (75-77 px) alih-alih membesar 2x.
    LIFT = 4
    # Telapak dalam RUANG LOKAL; garis tanah dunia diturunkan dari sini
    # supaya bayangan, rune tanah, dan telapak tidak pernah saling lepas.
    FEET_DY = 44
    GROUND_DY = int(round(FEET_DY * SCALE)) - LIFT        # ~ 46

    # Buffer rig: dibatasi dari extents TERUKUR semua pose (idle/walk/
    # attack/surge/ward/void/blink, dua LOD): anchor -> left -66, top -88,
    # right +96, bottom +58, + margin 4 px. Buffer sekecil mungkin karena
    # outline siluet meng-copy-nya 5x per frame.
    RIG_W, RIG_H = 176, 160
    RIG_OX, RIG_OY = 74, 96

    # Bidang acuan untuk pass cahaya (lighting.py): kotak TETAP di dalam
    # buffer rig, bukan bbox hasil render per frame. Alasannya dua: (a) kalau
    # acuan ikut bbox, arah cahaya bergeser tiap ganti pose dan terbaca
    # sebagai lampu berkedip; (b) bbox yang berubah-buat membuat cache
    # ukuran gradien miss tiap frame (+1,5 ms, terukur).
    GRAD_BOX = (RIG_OX - 54, RIG_OY - 52, 126, 102)

    # Durasi status skill (frame) - HARUS sama dengan active_skill_timer yang
    # diisi AI boss (bosses/base_boss.py) dan skill hero
    # (hero_skills/_bundle.py). Kalau konstanta ini lebih kecil, pose skill
    # "menggantung" di frame terakhir; kalau lebih besar, animasinya
    # terpotong di tengah. Dikunci oleh tools/test_gornak_masterwork.py.
    SKILL_DUR = {"q": 40, "w": 25, "e": 60, "r": 90}

    # Penanda "sedang di-render ke canvas hero" (lane). Dipasang per-frame
    # oleh draw_gornak, dipakai _draw_gnk_rig_at untuk memutuskan siapa yang
    # mengerjakan pass cahaya - hindari rim dobel di lane dan rim nol di shop.
    class _HERO_LANE:
        v = False

    PALETTE = {
        # Kulit sawo matang berdebu (cahaya dari depan-atas)
        "skin_darkest": (34, 17, 11),
        "skin_dark": (84, 44, 25),
        "skin_mid": (154, 94, 52),
        "skin_light": (205, 148, 96),
        "skin_shine": (240, 192, 142),
        "skin_high": (252, 222, 182),

        # Mohawk (ungu sihir)
        "hair_darkest": (24, 8, 38),
        "hair_dark": (52, 18, 84),
        "hair_mid": (106, 45, 158),
        "hair_light": (160, 98, 214),
        "hair_shine": (216, 172, 252),

        # Jenggot & alis
        "beard_darkest": (22, 12, 12),
        "beard_dark": (44, 25, 22),
        "beard_mid": (72, 43, 34),

        # Kain jubah / loincloth
        "robe_darkest": (12, 7, 21),
        "robe_dark": (32, 19, 52),
        "robe_mid": (60, 38, 92),
        "robe_light": (98, 66, 140),
        "robe_edge": (152, 116, 194),

        # Baja "spellbreaker"
        "armor_darkest": (7, 6, 12),
        "armor_dark": (24, 22, 34),
        "armor_mid": (74, 70, 96),
        "armor_light": (138, 132, 164),
        "armor_shine": (206, 202, 232),

        # Bilah silver-biru + garis temper
        # Bilah sengaja DITURUNKAN satu tingkat dari nilai tertinggi:
        # selama blade_shine = 246, mata (yang harusnya focal point) kalah
        # terangi senjatanya sendiri, dan pandangan jatuh ke pedang.
        # Hierarki nilai yang benar: mata > krist > pelat > bilah.
        "blade_dark": (34, 32, 50),
        "blade_mid": (98, 102, 130),
        "blade_light": (166, 172, 198),
        "blade_shine": (214, 220, 244),
        "blade_hamon": (168, 196, 236),

        # Kulit tan & kuningan paku
        "leather_dark": (48, 29, 18),
        "leather_mid": (88, 55, 33),
        "leather_light": (132, 89, 54),
        "brass_dark": (96, 68, 24),
        "brass_mid": (170, 130, 50),
        "brass_light": (228, 200, 114),

        # Aura anti-sihir (FX utama)
        "magic_darkest": (25, 5, 45),
        "magic_dark": (60, 20, 110),
        "magic_mid": (130, 55, 200),
        "magic_light": (185, 110, 240),
        "magic_hot": (220, 160, 255),
        "magic_shine": (245, 210, 255),

        # Mata menyala
        "eye_dark": (58, 18, 78),
        "eye_mid": (180, 90, 220),
        "eye_light": (240, 180, 255),
        "eye_glow": (255, 235, 255),

        # v2 extra ramps (kunci lama tetap)
        "magic_void": (38, 8, 72),
        "magic_core": (255, 236, 255),
        "blade_edge": (188, 204, 236),

        "shadow": (0, 0, 0),
        "shadow_deep": (4, 2, 8),
        "white": (255, 255, 255),
    }

    # ==================================================================
    # PRIMITIF HELPER (mendukung warna alpha lewat surface sementara)
    # ==================================================================
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_gornak._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius <= 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4),
                                  pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius,
                               width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_gornak.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius,
                                     width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_gornak._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        width = max(1, int(width))
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width - 2
            min_y = min(sy, ey) - width - 2
            w = abs(ex - sx) + width * 4 + 6
            h = abs(ey - sy) + width * 4 + 6
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.line(temp, color, (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), width)
            surface.blit(temp, (min_x, min_y))
            return
        if _NS_gornak.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color[:3], (sx, sy), (ex, ey))
                return
            except Exception:
                pass
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), width)

    def _poly(surface, color, points):
        if not points or len(points) < 3:
            return
        color = _NS_gornak._clamp(color)
        if len(color) == 4 and color[3] < 255:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, min_y = min(xs) - 2, min(ys) - 2
            w = max(xs) - min_x + 4
            h = max(ys) - min_y + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.polygon(temp, color,
                                [(p[0] - min_x, p[1] - min_y) for p in points])
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.polygon(surface, color[:3], points)

    def _ellipse(surface, color, rect, width=0):
        color = _NS_gornak._clamp(color)
        rx, ry, rw, rh = int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3])
        if rw <= 0 or rh <= 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, rw, rh), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3], (rx, ry, rw, rh), width)

    def _rect(surface, color, rect):
        color = _NS_gornak._clamp(color)
        rx, ry, rw, rh = int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3])
        if rw <= 0 or rh <= 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, rw, rh))
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3], (rx, ry, rw, rh))


    # ==================================================================
    # V2.1 FX VOCABULARY (standar Thorne - world-space + pixel-art)
    # ==================================================================
    def _mix(a, b, t):
        """Blend linear dua warna palette (t=0 -> a, t=1 -> b)."""
        t = max(0.0, min(1.0, t))
        return _NS_gornak._clamp(
            (a[0] + (b[0] - a[0]) * t,
             a[1] + (b[1] - a[1]) * t,
             a[2] + (b[2] - a[2]) * t))

    def _hash01(i):
        """Pseudo-random deterministik 0..1 (stabil antar frame & cache)."""
        x = math.sin(i * 127.1 + 311.7) * 43758.5453
        return x - math.floor(x)

    def _static(key, builder):
        surf = _NS_gornak._STATIC_SURFACES.get(key)
        if surf is None:
            surf = builder()
            _NS_gornak._STATIC_SURFACES[key] = surf
        return surf

    def _fx_scale(boss):
        """Faktor skala efek skill.

        Hero dirender ke canvas lalu dikecilkan ``_render_scale`` saat
        di-blit -> efek ikut menyusut. Dengan faktor ini efek digambar
        lebih besar di canvas sehingga ukurannya DI LAYAR setara boss
        asli (world-space). Boss asli (tanpa _render_scale) = 1.0.
        """
        scale = getattr(boss, "_render_scale", None)
        if not scale:
            return 1.0
        return max(1.0, min(2.6, 1.0 / float(scale)))

    def _ring_r(boss, world_r):
        """Radius canvas untuk ``world_r`` piksel dunia."""
        return max(1, int(round(float(world_r) * _NS_gornak._fx_scale(boss))))

    def _world_to_local(boss, x, y, wx, wy):
        """Titik dunia -> ruang gambar renderer (clamp ke canvas)."""
        scale = getattr(boss, "_render_scale", None)
        if scale is None:
            return int(wx), int(wy)
        scale = float(scale) or 1.0
        ox = (float(wx) - float(getattr(boss, "x", x))) / scale
        oy = (float(wy) - float(getattr(boss, "y", y))) / scale
        rng = int(getattr(boss, "range", 130) or 130)
        half = max(120, int(rng / scale) + 40)
        max_off = half - 20
        d = math.hypot(ox, oy)
        if d > max_off:
            ox *= max_off / d
            oy *= max_off / d
        return int(x + ox), int(y + oy)

    def _spark_star(surface, cx, cy, size, color, alpha, spikes=6, rot=0.4,
                    core=None):
        """Bintang kilat: spike panjang-pendek selang-seling + inti."""
        if alpha <= 0 or size <= 0:
            return
        for k in range(spikes):
            ang = rot + k * math.pi * 2 / spikes
            ln = size * (1.0 if k % 2 == 0 else 0.55)
            _NS_gornak._aaline(surface, (*color, alpha),
                               (int(cx), int(cy)),
                               (int(cx + math.cos(ang) * ln),
                                int(cy + math.sin(ang) * ln * .8)),
                               2 if k % 2 == 0 else 1)
        if core:
            _NS_gornak._aacircle(surface, (*core, alpha), (int(cx), int(cy)),
                                 max(1, int(size * .3)))

    def _chevron(surface, cx, cy, ang, size, color, alpha, width=3):
        """Satu panah '>' menghadap arah ``ang`` (telegraph bergerak)."""
        if alpha <= 0 or size <= 0:
            return
        ca, sa = math.cos(ang), math.sin(ang)
        px, py = -sa, ca
        tipx, tipy = cx + ca * size, cy + sa * size
        for s in (-1, 1):
            _NS_gornak._aaline(
                surface, (*color, alpha),
                (int(cx + px * s * size * .55 - ca * size * .5),
                 int(cy + py * s * size * .55 - sa * size * .5)),
                (int(tipx), int(tipy)), width)

    def _dashed_ring(surface, cx, cy, radius, color, alpha, phase,
                     segments=10, thick=3, span=0.6, squash=.92):
        """Cincin putus-putus yang berputar (marker AOE / rune ring)."""
        if alpha <= 0 or radius <= 1:
            return
        for i in range(segments):
            a0 = phase + i * math.pi * 2 / segments
            a1 = a0 + math.pi * 2 / segments * span
            p0 = (cx + math.cos(a0) * radius,
                  cy + math.sin(a0) * radius * squash)
            p1 = (cx + math.cos(a1) * radius,
                  cy + math.sin(a1) * radius * squash)
            _NS_gornak._aaline(surface, (*color, alpha), p0, p1, thick)

    def _jagged_crack(surface, cx, cy, ang, length, colors, alpha, seed,
                      width=3):
        """Retakan tanah berzigzag (3 segmen) dengan seam menyala."""
        if alpha <= 0 or length <= 0:
            return
        x, y, a = cx, cy, ang
        pts = [(x, y)]
        for i in range(3):
            a += (_NS_gornak._hash01(seed * 7 + i * 13) - .5) * .8
            seg = length / 3.0
            x += math.cos(a) * seg
            y += math.sin(a) * seg * .55
            pts.append((x, y))
        for i in range(len(pts) - 1):
            _NS_gornak._aaline(surface, (*colors[0], alpha),
                               pts[i], pts[i + 1], width + 2)
            _NS_gornak._aaline(surface, (*colors[1], alpha),
                               pts[i], pts[i + 1], width)

    def _tuft_points(spine, depth=4.0, min_len=7.0, seed=0):
        """Ubah spine halus menjadi tepi bergerigi (pixel-art fur)."""
        if not spine:
            return spine
        out = [spine[0]]
        for i in range(len(spine) - 1):
            ax, ay = spine[i]
            bx, by = spine[i + 1]
            seg = math.hypot(bx - ax, by - ay)
            n = max(1, int(seg / min_len))
            nx, ny = (by - ay), -(bx - ax)
            ln = math.hypot(nx, ny) or 1.0
            nx, ny = nx / ln, ny / ln
            for j in range(n):
                t = (j + 0.5) / n
                px, py = ax + (bx - ax) * t, ay + (by - ay) * t
                d = depth * (0.55 + 0.45 * _NS_gornak._hash01(
                    i * 7 + j * 13 + seed))
                if j % 2 == 0:
                    out.append((px + nx * d, py + ny * d))
                else:
                    out.append((px - nx * d * 0.45, py - ny * d * 0.45))
            out.append((bx, by))
        return out

    def _dither_dots(surface, color, points, alpha=70):
        """Checkerboard 50% 1-px (band dither klasik)."""
        a = _NS_gornak._alpha(alpha)
        col = (*_NS_gornak._clamp(color)[:3], a)
        for x, y in points:
            ix, iy = int(x), int(y)
            if (ix + iy) & 1:
                _NS_gornak._rect(surface, col, (ix, iy, 1, 1))

    def _skill_progress(boss, skill):
        dur = float(_NS_gornak.SKILL_DUR.get(skill, 40) or 40)
        timer = int(getattr(boss, "active_skill_timer", 0) or 0)
        return max(0.0, min(1.0, 1.0 - timer / dur))

    def _clamp_fx_xy(boss, x, y, px, py):
        """Jaga FX di dalam canvas hero (rumus = _canvas_size_for)."""
        scale = getattr(boss, "_render_scale", None)
        if scale is None:
            return int(px), int(py)
        scale = float(scale) or 1.0
        rng = int(getattr(boss, "range", 130) or 130)
        half = max(120, int(rng / scale) + 40)
        max_off = half - 12
        ox, oy = px - x, py - y
        d = math.hypot(ox, oy)
        if d > max_off:
            ox *= max_off / d
            oy *= max_off / d
        return int(x + ox), int(y + oy)

    # ==================================================================
    # KOORDINAT TARGET (kompensasi scale untuk jalur hero offscreen)
    # ==================================================================
    def _target_position(boss, x, y):
        """Posisi target dalam ruang jangkar (x, y) renderer ini."""
        target = getattr(boss, "target", None)
        scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
        if target is not None and getattr(target, "alive", True):
            # Hero di-render ke canvas offscreen lalu di-scale saat blit
            # (heroes/__init__.py), jadi titik canvas harus
            # = (delta dunia)/scale supaya proyektil mendarat TEPAT di
            # target setelah blit. Boss digambar langsung di layar
            # (scale = 1) jadi tidak terpengaruh.
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        return (int(x + 120.0 / scale * getattr(boss, "direction", 1)),
                int(y))

    # ==================================================================
    # STATE ANIMASI
    # ==================================================================
    def _update_gnk_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 38)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_gnk_previous_timer", 0))
        active = bool(getattr(boss, "_gnk_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._gnk_attack_active = True
            boss._gnk_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._gnk_attack_frame = int(getattr(boss, "_gnk_attack_frame",
                                                  0)) + 1
        elif timer <= 0:
            boss._gnk_attack_active = False
            boss._gnk_attack_frame = 0
            active = False

        boss._gnk_previous_timer = timer
        boss._gnk_attack_progress = (
            min(1.0, boss._gnk_attack_frame / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        cur_x = float(getattr(boss, "x", 0.0))
        cur_y = float(getattr(boss, "y", 0.0))
        if not hasattr(boss, "_gnk_last_x"):
            boss._gnk_last_x = cur_x
            boss._gnk_last_y = cur_y
            return False
        moved = abs(cur_x - boss._gnk_last_x) + abs(cur_y - boss._gnk_last_y)
        boss._gnk_last_x = cur_x
        boss._gnk_last_y = cur_y
        return moved > 0.3

    # ==================================================================
    # POSE STATE - satu sumber kebenaran untuk rig DAN semua FX
    # ==================================================================
    ACTIONS = ("idle", "walk", "attack", "surge", "ward", "void")

    def _resolve_pose(boss, moving=False):
        """(action, phase, ap) - dipakai rig DAN anchor FX agar sinkron.

        Murni/tanpa efek samping: boleh dipanggil ulang oleh fungsi efek.
        """
        active_skill = getattr(boss, "active_skill", None)
        if active_skill == "e":
            action = "ward"
        elif active_skill == "r":
            action = "void"
        elif active_skill == "q":
            action = "surge"
        elif active_skill == "w":
            action = "blink"
        elif (getattr(boss, "_gnk_attack_active", False)
              or getattr(boss, "timer", 0) >
              getattr(boss, "attack_cooldown", 40) - 15):
            action = "attack"
        elif moving:
            action = "walk"
        else:
            action = "idle"

        phase = float(getattr(boss, "pulse", 0.0))
        if action == "walk":
            phase *= 2.0
        ap = 0.0
        if action == "attack":
            raw = max(0.0, min(1.0, float(getattr(boss, "_gnk_attack_progress",
                                                  0.0))))
            # anticipation / impact hold / rebound - lihat _attack_curve
            ap = _NS_gornak._attack_curve(raw)
            boss._gnk_attack_raw = raw
        return action, phase, ap

    # Tinggi badan dalam RUANG LOKAL (y=0 = garis pinggang, + = ke bawah).
    # Punggung bahu & pusat kepala dibuat konstanta supaya seluruh bagian
    # (dan semua anchor FX) ikut berubah konsisten saat dituning.
    # Total badan (ruang lokal, sebelum SCALE): krist -40 -> telapak +44.
    # Setelah SCALE x1.32 + LIFT: ~115 px tinggi, cukup untuk mini boss tapi
    # wajah tetap di bawah HP bar boss (y-r-15..y-r-7).
    HEAD_Y = -24
    SHOULDER_Y = -14
    # Sendi bahu (x = ke depan mengikuti arah hadap)
    SHOULDER_FRONT = (12, SHOULDER_Y)
    SHOULDER_BACK = (-11, SHOULDER_Y - 1)

    def _attack_curve(ap):
        """Remap progres mentah (0..1) -> waktu pose (0..1), MONOTON naik.

        Yang membuat animasi serangan 2D terasa murah bukan jumlah frame,
        tapi tidak adanya: (a) anticipation yang jelas, (b) HOLD satu-dua
        frame di impact, (c) follow-through yang tidak langsung "ditarik"
        balik. Kurva ini memberi ketiganya; recovery sengaja tidak pernah
        turun (versi sinus dulu membuat bilah terlihat mundur sesaat).

        Batas segmen dipilih supaya jatuh PERSIS di batas fase
        _blade_angle / _front_grip_local: pose-time 0.26 = puncak wind-up,
        0.79 = impact, dan setelahnya recovery.
        """
        if ap <= 0.0:
            return 0.0
        if ap < 0.28:                       # anticipation: diperlambat
            t = ap / 0.28
            return 0.26 * (t ** 0.75)
        if ap < 0.50:                       # tebasan: sangat cepat
            t = (ap - 0.28) / 0.22
            return 0.26 + 0.53 * (t ** 0.5)
        if ap < 0.62:                       # IMPACT HOLD (nyaris beku)
            t = (ap - 0.50) / 0.12
            return 0.79 + 0.05 * t
        t = (ap - 0.62) / 0.38              # follow-through -> siap
        return 0.84 + 0.16 * (t ** 0.85)

    def _portrait_blade_angle(back=False):
        """Sudut bilah mode portrait: rapat ke badan, ujung menukik ke bawah.

        Lihat _front_grip_local(compact=...): HeroPortraits meng-crop bbox
        lalu men-scale-nya ke kartu, jadi figur yang LEBAR (bilah terentang)
        justru terKECIL di kartu yang sama. Dengan bilah ditarik masuk, bbox
        menyempit dan figur ter-render ~1.3x lebih besar - wajah & zirah
        akhirnya terbaca di Hero Shop.
        """
        return 0.62 if not back else -0.68

    def _blade_angle(phase, action, ap=0.0, back=False):
        """Sudut bilah (radian, dari garis lurus-bawah; + = ke depan).

        0 = moncong ke bawah, +pi/2 = lurus ke depan, ~pi = ke atas,
        -pi/2 = lurus ke belakang. Ditabel per-pose, BUKAN diturunkan dari
        arah lengan, supaya bilah tidak pernah menyayat menembus badannya
        sendiri. Depan dan belakang sengaja TIDAK simetris: bilah depan
        diangkat (memberi arah + massa di kuadran atas, seperti surai
        Grimjam / ponytail Kaizen yang membuat hero lain terbaca di lane),
        bilah belakang menukik ke bawah-belakang (menyeimbangkan bobot dan
        tetap melebar ke kiri supaya siluet tidak jadi tiang sempit).
        """
        s = math.sin(phase * 1.72)
        if action == "attack":
            # Semua jalur rotasi ada di SISI DEPAN badan, jadi tidak ada satu
            # frame pun bilah melintasi torso atau kepala. `ap` di sini sudah
            # lewat _attack_curve() (anticipation -> swing -> HOLD -> rebound).
            if ap < 0.26:                       # wind-up (1.78 -> 2.92)
                t = ap / 0.26
                return (1.78 + 1.14 * t, -1.00 - 1.92 * t)[back]
            if ap < 0.79:                       # tebasan (2.92 -> 0.30)
                t = (ap - 0.26) / 0.53
                return (2.92 - 2.62 * t, -2.92 + 1.92 * t)[back]
            t = (ap - 0.79) / 0.21             # recovery -> siap
            return (0.30 + 1.48 * t, -1.00)[back]
        if action == "surge":                  # Q: tusukan mana medatar
            return (1.45, -1.45)[back]
        if action == "ward":                   # E: dua bilah tegak = garda
            return (3.02, -3.02)[back]
        if action == "void":                   # R: kedua bilah dibuka ke atas
            return (2.40, -2.40)[back]
        if action == "blink":
            return (0.62, -0.62)[back]
        if action == "walk":
            return (1.78 + s * 0.10, -1.00 - s * 0.10)[back]
        # Siap: bilah DEPAN terangkat diagonal ke depan-atas, bilah belakang
        # menukik ke belakang-bawah. Versi dua bilah sejajar horizontal
        # terbaca sebagai "palang" putih lebar yang menenggelamkan badan di
        # skala hero; sudut asimetris ini tetap menjaga lebar siluet
        # (W/H ~1.05) tapi membuat kepala & dada jadi subjek. Nilai ini
        # juga titik awal/akhir ayunan -> tidak ada frame "snap".
        w = math.sin(phase * 0.5) * 0.05
        return (1.78 + w, -1.00 - w)[back]

    def _front_grip_local(action, ap=0.0, phase=0.0, compact=False):
        """Pergelangan tangan depan (pegangan bilah utama), ruang lokal.

        compact=True dipakai mode portrait: HeroPortraits meng-crop bbox
        lalu men-scale-nya ke kartu, jadi konten yang LEBAR (bilah terentang
        ke kanan-kiri) justru membuat figur terKECIL di kartu yang sama.
        Dengan bilah ditarik rapat ke badan, bbox menyempit -> figur
        ter-render ~1.3x lebih besar, wajah & zirah terbaca.
        """
        rest = _NS_gornak.SHOULDER_Y + 16
        if compact:
            return (12, rest + 2)
        if action == "attack":
            # Tangan tetap di sisi depan badan sepanjang ayunan - x tidak
            # pernah melewati garis tengah, jadi bilah tidak menutupi wajah.
            # Batas segmen mengikuti _attack_curve(): 0-0.26 angkat,
            # 0.26-0.79 tebas (dengan HOLD di ~0.78), 0.79-1 recovery.
            if ap < 0.26:
                t = min(1.0, ap / 0.26) ** 0.9
                return (int(15 - 13 * t), int(rest - 27 * t))
            if ap < 0.79:
                t = (ap - 0.26) / 0.53
                return (int(2 + 21 * t), int(rest - 27 + 33 * t))
            t = (ap - 0.79) / 0.18
            return (int(23 - 8 * t), int(rest + 6 - 4 * t))
        if action == "surge":
            return (23, rest + 3)
        if action == "ward":
            return (14, rest - 9)
        if action == "void":
            return (19, rest - 15)
        if action == "blink":
            return (16, rest - 2)
        if action == "walk":
            s = math.sin(phase * 1.72)
            return (int(15 + s * 3), int(rest - s * 2))
        return (15, rest + int(math.sin(phase * 0.62)))

    def _back_grip_local(action, ap=0.0, phase=0.0, compact=False):
        """Pergelangan tangan belakang (bilah pendek, grip terbalik)."""
        rest = _NS_gornak.SHOULDER_Y + 17
        if compact:
            return (-13, rest + 3)
        if action == "attack":
            if ap < 0.26:
                t = min(1.0, ap / 0.26) ** 0.9
                return (int(-19 - 5 * t), int(rest - 24 * t))
            if ap < 0.79:
                t = (ap - 0.26) / 0.53
                return (int(-24 - 3 * t), int(rest - 24 + 30 * t))
            t = (ap - 0.79) / 0.21
            return (int(-27 + 8 * t), int(rest + 6 - 3 * t))
        if action == "surge":
            return (-21, rest - 3)
        if action == "ward":
            return (-20, rest - 11)
        if action == "void":
            return (-21, rest - 14)
        if action == "blink":
            return (-20, rest - 1)
        if action == "walk":
            s = math.sin(phase * 1.72)
            return (int(-19 + s * 3), int(rest + s * 2))
        return (-19, rest + int(math.sin(phase * 0.62 + 1.1)))

    def _elbow(a, b, bend):
        """Siku 2-tulang: titik tengah + offset tegak lurus.

        Membuat lengan selalu tersambung (tidak pernah "lepas" seperti
        sticker) dan lengkungannya bisa diarahkan per sisi.
        """
        mx = (a[0] + b[0]) * 0.5
        my = (a[1] + b[1]) * 0.5
        dx = b[0] - a[0]
        dy = b[1] - a[1]
        ln = math.hypot(dx, dy) or 1.0
        return (int(mx + (-dy / ln) * bend), int(my + (dx / ln) * bend))

    def _arm_chain(shoulder, grip, phase, action, ap=0.0, back=False):
        """(elbow, blade_angle) - siku dari lengan, sudut dari tabel pose."""
        elbow = _NS_gornak._elbow(shoulder, grip, -4.5 if not back else 5.0)
        return elbow, _NS_gornak._blade_angle(phase, action, ap, back)

    def _blade_len(action, back=False):
        # Panjang bilah adalah sumber LEBAR utamanya siluet: pedang yang
        # dipegang menyamping membuat karakter pemegang dua bilah terbaca
        # penuh, bukan setiinggi tiang.
        if back:
            return 25 if action != "attack" else 29
        if action == "attack":
            return 42
        if action == "surge":
            return 44
        return 36

    def _head_bob(action, phase, ap):
        """Offset kepala (dx, dy) ruang lokal.

        Yang membuat rig terasa "hidup" bukan jumlah sendi, tapi kepala yang
        TIDAK merekat mati ke torso: dia mengangkat sedikit saat langkah
        (ayunan kontrarotasi), menunduk saat ayunan bilah, dan bergoyang
        halus saat idle.
        """
        if action == "walk":
            sw = math.sin(phase * 1.72)
            return (int(-sw * 1.2), int(abs(math.sin(phase * 1.15)) * -1.4))
        if action == "attack":
            return (int(math.sin(ap * math.pi) * 2.4),
                    -int(math.sin(ap * math.pi) * 1.4))
        if action == "void":
            return (-1, -2)
        if action == "ward":
            return (0, -1)
        return (int(math.sin(phase * 0.31) * 0.9),
                int(math.sin(phase * 0.62 + 0.8) * 0.8))

    def _rig_shift(action, phase, ap):
        """(lean, root_y) badan; kaki TIDAK ikut bergeser (menapak)."""
        lean = 0
        root_y = int(math.sin(phase * 0.62) * 1.2)
        if action == "walk":
            lean = int(math.sin(phase * 1.72) * 2)
            root_y -= int(abs(math.sin(phase * 1.15)) * 2.5)
        elif action == "attack":
            t = math.sin(ap * math.pi)
            lean = int(t * 6)
            root_y += int(t * 2)
        elif action == "surge":
            lean = 3
            root_y -= 1
        elif action in ("void", "ward"):
            root_y -= 2
        elif action == "surge":
            lean = 3
            root_y -= 1
        elif action == "blink":
            lean = 1
            root_y -= 1
        return lean, root_y

    def _s(v):
        """Ukuran ruang lokal (lebar garis, radius) -> piksel layar."""
        return max(1, int(round(v * _NS_gornak.SCALE)))

    def _local_to_screen(cx, cy, facing, lean, root_y, lx, ly):
        """SATU pemetaan lokal -> layar: skala, arah hadap, bob/lean.

        Semua bagian tubuh dan semua titik jangkar efek (ujung bilah,
        pergelangan tangan) melewati fungsi ini, jadi ukuran boleh diubah
        lewat satu angka tanpa membuat efek lepas dari badan.
        """
        f = 1 if facing >= 0 else -1
        k = _NS_gornak.SCALE
        return (int(cx + (lx * f + lean * f) * k),
                int(cy - _NS_gornak.LIFT + (ly + root_y) * k))

    def _local(boss, x, y, action, phase, ap, lx, ly):
        """Ruang lokal rig -> piksel surface (dipakai FX eksternal)."""
        facing = getattr(boss, "direction", 1) or 1
        lean, root_y = _NS_gornak._rig_shift(action, phase, ap)
        return _NS_gornak._local_to_screen(x, y, facing, lean, root_y, lx, ly)

    def _tip_local(action, phase, ap=0.0, back=False):
        """Ujung bilah dalam ruang lokal (rig & FX pakai angka yang sama)."""
        grip = (_NS_gornak._front_grip_local(action, ap, phase) if not back
                else _NS_gornak._back_grip_local(action, ap, phase))
        shoulder = (_NS_gornak.SHOULDER_FRONT if not back
                    else _NS_gornak.SHOULDER_BACK)
        _, angle = _NS_gornak._arm_chain(shoulder, grip, phase, action, ap,
                                        back)
        L = _NS_gornak._blade_len(action, back)
        return (int(grip[0] + math.sin(angle) * L),
                int(grip[1] + math.cos(angle) * L))

    def _tip_screen(boss, x, y, back=False):
        action, phase, ap = _NS_gornak._resolve_pose(boss)
        # FX selalu memakai pose yang sama dengan badan (lihat
        # _resolve_pose yang murni), jadi bolt/proc tidak pernah lepas.
        return _NS_gornak._local(boss, x, y, action, phase, ap,
                                 *_NS_gornak._tip_local(action, phase, ap, back))

    # ==================================================================
    # ENTRY POINT
    # ==================================================================
    def draw_gornak(surface, boss, x, y):
        """Entry point Boss.draw() sekaligus heroes.render_hero()."""
        # jalur hero (lane): heroes/__init__ men-set _render_scale sebelum
        # memanggil renderer, dan _finish_hd_sprite sudah menambah
        # rim/terminator -> pass di sini dilewati (lihat _draw_gnk_rig_at).
        _NS_gornak._HERO_LANE.v = hasattr(boss, "_render_scale")
        _NS_gornak._update_gnk_attack_anim(boss)
        action, phase, ap = _NS_gornak._resolve_pose(
            boss, _NS_gornak._detect_moving(boss))
        boss._gnk_pose_action = action
        skill = getattr(boss, "active_skill", None)
        timer = int(getattr(boss, "active_skill_timer", 0))
        portrait = bool(getattr(boss, "_portrait_hd", False))
        facing = getattr(boss, "direction", 1) or 1
        flash = _NS_gornak._alpha(170 * (getattr(boss, "hurt_flash_timer", 0)
                                         / 8.0))

        # ── Latar. Dibuang total saat portrait supaya auto-crop Hero Shop
        #    terisi wajah & material, bukan lingkaran efek.
        if not portrait:
            _NS_gornak._draw_anti_magic_field(surface, x, y, phase, skill)
            _NS_gornak._draw_ground_rune(surface, x, y, phase, skill)
            if skill == "q":
                _NS_gornak._draw_manabreak_ground(surface, boss, x, y, timer,
                                                   phase)
            elif skill == "w":
                _NS_gornak._draw_blink_ground(surface, boss, x, y, timer,
                                              phase)
            elif skill == "r":
                _NS_gornak._draw_manavoid_ground(surface, boss, x, y, timer,
                                                 phase)
            # PERTAGAS v2.1: gelombang kejut aktivasi (12 frame pertama)
            # world-space lewat _fx_scale + bintang spike.
            if skill in _NS_gornak.SKILL_DUR:
                age = _NS_gornak.SKILL_DUR[skill] - timer
                if 0 <= age < 12:
                    st = age / 12.0
                    fs = _NS_gornak._fx_scale(boss)
                    a = _NS_gornak._alpha(235 * (1 - st))
                    rr = int((16 + st * 50) * fs)
                    gy = y + _NS_gornak.GROUND_DY
                    _NS_gornak._ellipse(
                        surface, (*_NS_gornak.PALETTE["magic_mid"], a),
                        (x - rr, gy - rr // 3, rr * 2,
                         max(4, rr * 2 // 3)), 2)
                    _NS_gornak._ellipse(
                        surface, (*_NS_gornak.PALETTE["magic_shine"], a),
                        (x - rr // 2, gy - rr // 6, rr,
                         max(3, rr // 3)), 1)
                    _NS_gornak._spark_star(
                        surface, x, gy - 4, int(10 * fs * (1 - st)),
                        _NS_gornak.PALETTE["magic_hot"], a, spikes=8,
                        rot=st * 1.4, core=_NS_gornak.PALETTE["magic_shine"])

        # ── Karakter
        if action == "blink":
            _NS_gornak._draw_gnk_blink(surface, boss, x, y, timer, portrait,
                                       flash)
        else:
            if not portrait:
                _NS_gornak._draw_shadow(surface, x, y + _NS_gornak.GROUND_DY)
            _NS_gornak._draw_gnk_rig_at(surface, x, y, facing, phase, action,
                                        ap, portrait, flash)
            if action == "attack" and not portrait:
                _NS_gornak._draw_crescent_slash(surface, x, y, facing, phase,
                                                ap)
            elif action == "walk" and not portrait:
                # Debu langkah: dua kepul kecil tepat saat telapak mendarat,
                # jadi bobot badan terasa menekan tanah (bukan character
                # meluncur di atas lantai).
                _NS_gornak._draw_footfall_dust(surface, x, y, facing, phase)

        # ── Foreground FX
        if not portrait:
            if skill == "q":
                _NS_gornak._draw_manabreak_foreground(surface, boss, x, y,
                                                       timer, phase)
            elif skill == "e":
                _NS_gornak._draw_counterspell_foreground(surface, boss, x, y,
                                                          timer, phase)
            elif skill == "r":
                _NS_gornak._draw_manavoid_foreground(surface, boss, x, y,
                                                     timer, phase)

    def _draw_gnk_rig_at(surface, x, y, facing, phase, action, ap, detail,
                         flash=0):
        """Rig -> buffer -> outline gelap 1 px -> satu blit murah.

        Mode portrait Hero Shop memakai kanvas kecil (160x160 di
        ui_components HeroPortraits) dan meng-crop dari bbox: kalau badan
        digambar dengan anchor di pinggang, bilah depan yang panjang
        melewati tepi kanan dan TERPOTONG. Jadi di mode itu konten dipusatkan
        pada bbox-nya sendiri; jalur boss (1x) tidak berubah sama sekali.
        """
        buf = pygame.Surface((_NS_gornak.RIG_W, _NS_gornak.RIG_H),
                             pygame.SRCALPHA)
        _NS_gornak._draw_gnk_rig(buf, _NS_gornak.RIG_OX, _NS_gornak.RIG_OY,
                                 facing, phase, action, ap, detail)
        if flash > 0:
            lit = buf.copy()
            lit.fill((255, 246, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
            lit.set_alpha(flash)
            buf.blit(lit, (0, 0))
        # Jalur BOSS digambar langsung ke layar 1:1, jadi TIDAK melewati
        # _finish_hd_sprite (yang sudah memberi rim+terminator ke hero).
        # Di sinilah cahaya itu dipasang untuk boss. Saat hero-path
        # (scale != 1.0) pass-nya dilewati supaya tidak dua kali; mode
        # portrait tetap dipakai karena HeroPortraits tidak memanggil
        # _finish_hd_sprite sama sekali.
        # Aturan: pass cahaya dipasang di SINI hanya kalau sprite ini TIDAK
        # akan dilewatkan ke heroes._finish_hd_sprite (yang sudah memasang
        # pass yang sama):
        #   * boss 1x (scale 1.0)          -> pasang di sini
        #   * lane hero (scale != 1.0)      -> jangan (nanti dobel)
        #   * Hero Shop (tanpa _render_scale, portrait) -> pasang di sini,
        #     karena HeroPortraits tidak memanggil _finish_hd_sprite sama
        #     sekali. Ciri mode shop: attribute hero TIDAK punya
        #     _render_scale sama sekali (jalur lane selalu men-set-nya).
        if _lighting is not None and not _NS_gornak._HERO_LANE.v:
            _lighting.apply_to_rig(
                buf, rim_add=(32, 26, 46), shade_mul=160,
                box=_NS_gornak.GRAD_BOX if not detail else None)
        ox = int(x) - _NS_gornak.RIG_OX
        oy = int(y) - _NS_gornak.RIG_OY
        if detail:                      # portrait: pusatkan konten
            used = buf.get_bounding_rect(min_alpha=1)
            if used.width > 0:
                ox = int(x) - (used.left + used.width // 2)
                oy = int(y) - (used.top + used.height // 2)
        # Outline siluet (4 arah) - sama seperti Sylara: jalur hero memang
        # menambah satu tepi lagi di _finish_hd_sprite, dan hasilnya justru
        # dipakai sebagai acuan keluarga, jadi tidak perlu di-skip.
        edge = buf.copy()
        edge.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            surface.blit(edge, (ox + dx, oy + dy))
        surface.blit(buf, (ox, oy))
        return buf

    # Pose lama tetap tersedia (dipakai tool debug/preview).
    def _draw_gnk_idle(surface, boss, x, y):
        _NS_gornak._draw_gnk_rig_at(surface, x, y,
                                    getattr(boss, "direction", 1) or 1,
                                    float(getattr(boss, "pulse", 0.0)),
                                    "idle", 0.0, False)

    def _draw_gnk_walk(surface, boss, x, y):
        _NS_gornak._draw_gnk_rig_at(surface, x, y,
                                    getattr(boss, "direction", 1) or 1,
                                    float(getattr(boss, "pulse", 0.0)) * 2.0,
                                    "walk", 0.0, False)

    def _draw_gnk_attack(surface, boss, x, y, ap=0.5):
        _NS_gornak._draw_gnk_rig_at(surface, x, y,
                                    getattr(boss, "direction", 1) or 1,
                                    float(getattr(boss, "pulse", 0.0)),
                                    "attack", ap, False)

    def _draw_gnk_blink(surface, boss, x, y, timer, portrait, flash):
        """Blink: after-image RIG YANG SAMA + dissolve di garis kaki."""
        duration = _NS_gornak.SKILL_DUR["w"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = getattr(boss, "direction", 1) or 1
        phase = float(getattr(boss, "pulse", 0.0))
        if progress < 0.30:
            alpha_t = 1.0 - progress / 0.30
        elif progress < 0.68:
            alpha_t = 0.14
        else:
            alpha_t = (progress - 0.68) / 0.32

        if not portrait:
            _NS_gornak._draw_shadow(surface, x, y + _NS_gornak.GROUND_DY)

        rig, ax, ay = _NS_gornak._compose_outline(x, y, facing, phase, "blink",
                                                  0.0, portrait)
        if progress < 0.80:
            for i in (3, 2, 1):
                rig.set_alpha(_NS_gornak._alpha(80 * alpha_t / i))
                surface.blit(rig, (x - ax - facing * i * 8, y - ay + i))
        rig.set_alpha(_NS_gornak._alpha(70 + 185 * min(1.0, alpha_t)))
        surface.blit(rig, (x - ax, y - ay))
        rig.set_alpha(255)

        if not portrait:
            p = _NS_gornak.PALETTE
            gy = y + _NS_gornak.GROUND_DY
            for i in range(8):
                t = (phase * 0.5 + i * 0.125) % 1.0
                gx = x + int(math.sin(i * 1.7) * (10 + t * 16))
                a = _NS_gornak._alpha(190 * (1 - t) * alpha_t)
                if a > 0:
                    _NS_gornak._aacircle(surface, (*p["magic_mid"], a),
                                         (gx, gy - int(t * 12)), 2)
                    _NS_gornak._aacircle(surface, (*p["magic_shine"], a),
                                         (gx, gy - int(t * 12)), 1)

    def _compose_outline(x, y, facing, phase, action, ap, detail):
        """Rig + outline gelap 1 px sebagai SATU surface (perlu untuk
        after-image blink yang mengatur alpha sendiri).

        Return ``(surface, anchor_x, anchor_y)``: titik dalam surface yang
        jatuh tepat di dunia ``(x, y)``.
        """
        buf = pygame.Surface((_NS_gornak.RIG_W, _NS_gornak.RIG_H),
                             pygame.SRCALPHA)
        _NS_gornak._draw_gnk_rig(buf, _NS_gornak.RIG_OX, _NS_gornak.RIG_OY,
                                 facing, phase, action, ap, detail)
        pad = 1
        out = pygame.Surface((_NS_gornak.RIG_W + pad * 2,
                              _NS_gornak.RIG_H + pad * 2), pygame.SRCALPHA)
        edge = buf.copy()
        edge.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        # Selout: outline gelap hanya sisi bayangan (kanan-bawah relatif
        # hadap). Key light kiri-atas (lighting.LIGHT_DIR = (-1, -1));
        # sisi cahaya dibiarkan bersih — rim 1 px ada di _draw_gnk_rimlight.
        sx = 1 if facing >= 0 else -1
        for dx, dy in ((sx, 0), (0, 1), (sx, 1)):
            out.blit(edge, (pad + dx, pad + dy))
        out.blit(buf, (pad, pad))
        return out, _NS_gornak.RIG_OX + pad, _NS_gornak.RIG_OY + pad

    def _draw_gnk_rig(surface, cx, cy, facing, phase, action, ap=0.0,
                      detail=False):
        """BONE RIG 2D BERLAPIS - seluruh badan dihitung dari sendi.

        ``cx, cy`` = anchor (pusat boss / garis pinggul). Urutan gambar
        belakang -> depan, jadi pedang belakang di balik torso dan pedang
        depan paling depan, seperti sprite sheet referensi.
        """
        p = _NS_gornak.PALETTE
        f = 1 if facing >= 0 else -1
        lean, root_y = _NS_gornak._rig_shift(action, phase, ap)

        def pt(dx, dy):
            """Sendi badan (ikut bob/lean)."""
            return _NS_gornak._local_to_screen(cx, cy, f, lean, root_y, dx, dy)

        def ptg(dx, dy):
            """Sendi yang terpatok tanah (telapak kaki tidak ikut bob)."""
            return _NS_gornak._local_to_screen(cx, cy, f, lean, 0, dx, dy)

        def poly(color, coords, outline=True):
            pts = [pt(dx, dy) for dx, dy in coords]
            if outline:
                _NS_gornak._poly(surface, p["shadow_deep"],
                                  [(qx + f, qy + 1) for qx, qy in pts])
            _NS_gornak._poly(surface, color, pts)
            return pts

        def poly_free(color, pts, outline=True):
            if outline:
                _NS_gornak._poly(surface, p["shadow_deep"],
                                  [(qx + f, qy + 1) for qx, qy in pts])
            _NS_gornak._poly(surface, color, pts)

        def dot(color, dx, dy, r, outline=True):
            sx, sy = pt(dx, dy)
            rr = _NS_gornak._s(r)
            if outline:
                _NS_gornak._aacircle(surface, p["shadow_deep"],
                                     (sx + f, sy + 1), rr + 1)
            _NS_gornak._aacircle(surface, color, (sx, sy), rr)

        def limb(a, b, width, base, light=None):
            aa, bb = pt(*a), pt(*b)
            w = _NS_gornak._s(width)
            _NS_gornak._aaline(surface, p["shadow_deep"],
                               (aa[0] + f, aa[1] + 1),
                               (bb[0] + f, bb[1] + 1), w + 2)
            _NS_gornak._aaline(surface, base, aa, bb, w)
            if light:
                off = -1 if f > 0 else 1
                _NS_gornak._aaline(surface, light, (aa[0] + off, aa[1] - 1),
                                   (bb[0] + off, bb[1] - 1),
                                   max(1, _NS_gornak._s(width // 3)))

        breath = math.sin(phase * 0.62)
        stride = (math.sin(phase * 1.72) if action == "walk" else 0.0)
        ward = action == "ward"
        void = action == "void"
        surge = action == "surge"

        portrait = bool(detail)
        front_grip = _NS_gornak._front_grip_local(action, ap, phase,
                                                 compact=portrait)
        back_grip = _NS_gornak._back_grip_local(action, ap, phase,
                                               compact=portrait)
        front_elbow, front_angle = _NS_gornak._arm_chain(
            _NS_gornak.SHOULDER_FRONT, front_grip, phase, action, ap)
        back_elbow, back_angle = _NS_gornak._arm_chain(
            _NS_gornak.SHOULDER_BACK, back_grip, phase, action, ap, back=True)
        if portrait:
            front_angle = _NS_gornak._portrait_blade_angle(False)
            back_angle = _NS_gornak._portrait_blade_angle(True)

        # 1. Jubah belakang - memberi kedalaman pada siluet
        _NS_gornak._draw_gnk_cape_back(surface, pt, poly_free, f, phase,
                                       action)

        # 2. Kaki - telapak dipatok di GROUND_DY
        _NS_gornak._draw_gnk_legs(surface, pt, ptg, poly_free, f, phase,
                                  action, stride)

        # 3. Tangan + bilah belakang (di balik badan)
        _NS_gornak._draw_gnk_arm(surface, pt, poly_free, dot, limb, f, phase,
                                 action, ap, _NS_gornak.SHOULDER_BACK,
                                 back_elbow, back_grip, back_angle,
                                 _NS_gornak._blade_len(action, True),
                                 back=True)

        # 4. Torso + harness + pelat spellbreaker
        _NS_gornak._draw_gnk_torso(surface, pt, poly_free, dot, f, phase,
                                   breath, ward, void)

        # 5. Sabuk, loincloth, rantai besi
        _NS_gornak._draw_gnk_belt(surface, pt, poly_free, dot, f, phase,
                                  action, stride)

        # 6. Pauldron bertingkat
        _NS_gornak._draw_gnk_pauldrons(surface, pt, poly_free, dot, f, phase,
                                       breath)

        # 7. Leher + kepala (rahang, jenggot kepang, mohawk nempel)
        _NS_gornak._draw_gnk_head(surface, pt, poly_free, dot, f, phase,
                                  action, ward, void)

        # 8. Tangan + bilah depan (paling depan)
        _NS_gornak._draw_gnk_arm(surface, pt, poly_free, dot, limb, f, phase,
                                 action, ap, _NS_gornak.SHOULDER_FRONT,
                                 front_elbow, front_grip, front_angle,
                                 _NS_gornak._blade_len(action), back=False,
                                 ward=ward, void=void, surge=surge)

        # 9. Rim light ungu - sinyal warna tema (lihat docstring-nya)
        _NS_gornak._draw_gnk_rimlight(surface, pt, f, phase, ward, void)

        # 10. Pass material portrait-only
        if detail:
            _NS_gornak._draw_gnk_masterwork_details(surface, pt, f, phase,
                                                    action)
            _NS_gornak._draw_gnk_weave(surface, pt, f)

    # ==================================================================
    # BAGIAN TUBUH
    # ==================================================================
    # Prinsip di 720p: yang dibaca hanyalah NILAI (terang/gelap) dan
    # SILUET, bukan garis halus. Setiap bagian karenanya dibatasi 2-3
    # lapis nilai, dan garis penanda (otot, jahitan) hanya muncul di
    # pass portrait.
    # ==================================================================

    def _draw_gnk_cape_back(surface, pt, poly_free, f, phase, action):
        """Half-mantle kulit di punggung: MEMBINGKAI badan, tidak
        melebarinya. Tepi bawah robek dan berayun oleh phase."""
        p = _NS_gornak.PALETTE
        sway = int(math.sin(phase * 1.05) * 2)
        if action in ("walk", "attack"):
            sway -= 2
        outer = [(-15, -19), (-19, -6), (-22 + sway, 10), (-17 + sway, 17),
                 (-11 + sway, 9), (-6 + sway, 16), (0, 7), (4, -8), (2, -19)]
        # Tepi bawah bergerigi (pixel-art tuft) - depth kecil supaya
        # tidak melewati buffer rig / garis HP.
        hem_spine = [(-22 + sway, 10), (-17 + sway, 17), (-11 + sway, 9),
                     (-6 + sway, 16), (0, 7)]
        tuft = _NS_gornak._tuft_points(hem_spine, depth=2.2, min_len=4.0,
                                       seed=11)
        outer = [(-15, -19), (-19, -6)] + tuft + [(4, -8), (2, -19)]
        poly_free(p["robe_darkest"], [pt(*q) for q in outer])
        inner = [(-14, -17), (-17, -6), (-20 + sway, 8), (-15 + sway, 14),
                 (-10 + sway, 8), (-5 + sway, 13), (0, 6), (3, -8), (1, -17)]
        poly_free(p["robe_dark"], [pt(*q) for q in inner], outline=False)
        _NS_gornak._aaline(surface, p["robe_mid"], pt(-10, -14),
                           pt(-12 + sway, 4), 1)
        poly_free(p["robe_light"], [pt(-9, -12), pt(-12 + sway, 1),
                                   pt(-9 + sway, 7), pt(-6, -6)],
                  outline=False)
        # Rim di tepi robek: 1 px terang membuat sobekan terbaca sebagai
        # KAIN (bukan lubang gelap) di skala 1x.
        hem = [(-16 + sway, 9), (-12 + sway, 15), (-8 + sway, 8),
               (-4 + sway, 14), (0, 6)]
        for i in range(len(hem) - 1):
            _NS_gornak._aaline(surface, p["robe_edge"], pt(*hem[i]),
                               pt(*hem[i + 1]), 1)
        # Dither 50% di sisi bayangan jubah (kanan-bawah, 1 px).
        dots = [pt(-18 + sway, 6), pt(-16 + sway, 10), pt(-14 + sway, 13),
                pt(-12 + sway, 8), pt(-10 + sway, 12), pt(-8 + sway, 7)]
        _NS_gornak._dither_dots(surface, p["robe_darkest"], dots, 110)

    def _draw_gnk_legs(surface, pt, ptg, poly_free, f, phase, action, stride):
        """Dua kaki berotot: paha -> pelindung lutut -> greave -> boot.

        Pass hero-baru: blok tulang kering tidak lagi memakai armor_light
        (di skala hero kaki terbaca sebagai dua balok abu-abu pucat yang
        menyatu dengan loincloth). Sekarang paha & betis gelap dengan SATU
        garis tepi terang di sisi cahaya + kap kuningan di ujung boot, jadi
        kedua kaki terpisah dan tetap terbaca.
        """
        p = _NS_gornak.PALETTE
        hip_y = 4
        ground = _NS_gornak.FEET_DY
        for side in (-1, 1):
            if action == "walk":
                dx = int(stride * 8) * side
                lift = int(max(0.0, -stride * side) * 4)
            elif action == "attack":
                dx = 8 if side > 0 else -7
                lift = 0
            elif action in ("surge", "void"):
                dx = 7 if side > 0 else -7
                lift = 0
            else:
                dx = 4 if side > 0 else -6
                lift = 0
            front = side > 0
            hip_x = side * 7
            knee_x = hip_x + int(dx * 0.55) + side
            foot_x = hip_x + dx + side * 2
            knee_y = (hip_y + ground) // 2 - lift
            fy = ground - lift
            # Paha: satu blok gelap + satu blok tengah + garis cahaya tipis
            poly_free(p["skin_darkest"], [pt(hip_x - 6, hip_y),
                                          pt(hip_x + 5, hip_y),
                                          pt(knee_x + 4, knee_y),
                                          pt(knee_x - 5, knee_y)])
            if front:
                poly_free(p["skin_dark"], [pt(hip_x - 5, hip_y + 1),
                                          pt(hip_x + 4, hip_y + 1),
                                          pt(knee_x + 3, knee_y - 1),
                                          pt(knee_x - 4, knee_y - 1)],
                          outline=False)
                poly_free(p["skin_mid"], [pt(hip_x - 4, hip_y + 2),
                                          pt(hip_x + 1, hip_y + 2),
                                          pt(knee_x - 1, knee_y - 4),
                                          pt(knee_x - 3, knee_y - 4)],
                          outline=False)
            # Pembungkus kain di paha (identik dengan loincloth -> kaki
            # menyatu dengan badan, bukan dua tabung terpisah)
            poly_free(p["robe_dark"], [pt(hip_x - 6, hip_y + 7),
                                       pt(hip_x + 5, hip_y + 7),
                                       pt(hip_x + 5, hip_y + 13),
                                       pt(hip_x - 6, hip_y + 13)])
            if front:
                poly_free(p["robe_mid"], [pt(hip_x - 4, hip_y + 8),
                                          pt(hip_x + 2, hip_y + 8),
                                          pt(hip_x + 2, hip_y + 12),
                                          pt(hip_x - 4, hip_y + 12)],
                          outline=False)
            # Pelindung lutut
            poly_free(p["armor_darkest"], [pt(knee_x - 4, knee_y - 3),
                                           pt(knee_x + 4, knee_y - 3),
                                           pt(knee_x + 4, knee_y + 3),
                                           pt(knee_x - 4, knee_y + 3)])
            poly_free(p["armor_mid"], [pt(knee_x - 3, knee_y - 2),
                                       pt(knee_x + 2, knee_y - 2),
                                       pt(knee_x + 2, knee_y + 2),
                                       pt(knee_x - 3, knee_y + 2)],
                          outline=False)
            _NS_gornak._aacircle(surface, p["armor_shine"], pt(knee_x - 1,
                                                              knee_y - 1), 1)
            # Shina gelap + satu garis tepi cahaya
            poly_free(p["armor_dark"], [pt(knee_x - 4, knee_y + 2),
                                        pt(knee_x + 4, knee_y + 2),
                                        ptg(foot_x + 4, fy - 7),
                                        ptg(foot_x - 4, fy - 7)])
            if front:
                poly_free(p["armor_mid"], [pt(knee_x - 3, knee_y + 3),
                                           pt(knee_x + 1, knee_y + 3),
                                           ptg(foot_x + 1, fy - 8),
                                           ptg(foot_x - 3, fy - 8)],
                          outline=False)
                _NS_gornak._aaline(surface, p["armor_light"],
                                   pt(knee_x - 2, knee_y + 4),
                                   ptg(foot_x - 2, fy - 7), 1)
                # Dither band di sisi bayangan greave (1 px, key light kiri-atas)
                dots = []
                for k in range(4):
                    t = (k + 0.5) / 4.0
                    gx = knee_x + (foot_x - knee_x) * t + 2
                    gy = (knee_y + 3) + (fy - 8 - (knee_y + 3)) * t
                    dots.append(ptg(gx, gy) if gy > knee_y + 6 else pt(gx, gy))
                _NS_gornak._dither_dots(surface, p["armor_darkest"], dots, 90)
            # Boot gelap + kap kuningan, sol DATAR di garis tanah
            toe = 4 if f > 0 else -4
            poly_free(p["leather_dark"], [ptg(foot_x - 5, fy - 7),
                                          ptg(foot_x + 5, fy - 7),
                                          ptg(foot_x + toe + 2, fy - 2),
                                          ptg(foot_x + toe, fy),
                                          ptg(foot_x - toe, fy),
                                          ptg(foot_x - 6, fy - 3)])
            poly_free(p["leather_mid"], [ptg(foot_x - 4, fy - 6),
                                         ptg(foot_x + 4, fy - 6),
                                         ptg(foot_x + toe + 1, fy - 3),
                                         ptg(foot_x - 5, fy - 3)],
                        outline=False)
            # Garis break terang di pergelangan: tanpa ini paha-celana-boot
            # jadi satu kolom cokelat dan kaki "hilang" di skala hero.
            _NS_gornak._aaline(surface, p["leather_light"],
                               ptg(foot_x - 5, fy - 7),
                               ptg(foot_x + 4, fy - 7), 1)
            _NS_gornak._aaline(surface, p["brass_mid"],
                               ptg(foot_x + toe - 1, fy - 4),
                               ptg(foot_x + toe + 2, fy - 2), 2)
            if lift <= 0:
                _NS_gornak._aaline(surface, p["shadow_deep"],
                                   ptg(foot_x - 5, fy + 1),
                                   ptg(foot_x + 5, fy + 1), 2)
            else:
                _NS_gornak._aaline(surface, (*p["shadow"], 80),
                                   ptg(foot_x - 4, _NS_gornak.FEET_DY),
                                   ptg(foot_x + 4, _NS_gornak.FEET_DY), 2)

    def _draw_gnk_torso(surface, pt, poly_free, dot, f, phase, breath, ward,
                        void):
        """Dada bidang (V-taper) + pelat spellbreaker BERCAHAYA + rune ungu.

        Pass hero-baru: pelat baja dinaikkan ke armor_light/shine (sebelumnya
        armor_mid yang di skala hero menyatu dengan kulit sehingga seluruh
        badan jadi satu blob coklat), dan rantai pemutus sihir dibuat jadi
        tiga titik magic_hot yang jelas - itu "sinyal warna" yang dipakai
        Grimjaw (api) / Vex (void cyan) / Kaizen (angin biru) supaya unit
        terbaca dari jauh.
        """
        p = _NS_gornak.PALETTE
        sh = _NS_gornak.SHOULDER_Y
        twist = int(math.sin(phase * 1.05))
        poly_free(p["skin_darkest"], [pt(-14 + twist, sh - 1),
                                      pt(13 + twist, sh - 1), pt(10, 4),
                                      pt(-11, 4)])
        poly_free(p["skin_dark"], [pt(-12 + twist, sh), pt(12 + twist, sh),
                                   pt(9, 3), pt(-10, 3)], outline=False)
        poly_free(p["skin_mid"], [pt(-10 + twist, sh + 1),
                                  pt(9 + twist, sh + 1), pt(7, -2),
                                  pt(-8, -2)], outline=False)
        # Blok cahaya di bahu-dada (satu bentuk besar, bukan garis halus)
        poly_free(p["skin_light"], [pt(-9 + twist, sh + 1),
                                    pt(6 + twist, sh + 1), pt(4, sh + 7),
                                    pt(-8, sh + 6)], outline=False)
        poly_free(p["skin_shine"], [pt(-7 + twist, sh + 2),
                                    pt(2 + twist, sh + 2), pt(1, sh + 5),
                                    pt(-6, sh + 5)], outline=False)
        # Bayangan miring di bawah pektoral + highlight mikro: dua nilai
        # ini yang membuat dada terbaca BERBUKUK, bukan papan cokelat datar
        # saat di-zoom di kartu Hero Shop.
        poly_free(p["skin_dark"], [pt(-9 + twist, sh + 7), pt(-1 + twist, sh + 8),
                                   pt(-2 + twist, sh + 10),
                                   pt(-9 + twist, sh + 9)], outline=False)
        _NS_gornak._aaline(surface, p["skin_high"], pt(-7 + twist, sh + 4),
                           pt(-2 + twist, sh + 4), 1)
        # Garis tengah + perut (nilai, bukan outline)
        _NS_gornak._aaline(surface, p["skin_dark"], pt(twist, sh + 3),
                           pt(0, 2), 1)
        _NS_gornak._aaline(surface, p["skin_dark"], pt(-5, -2), pt(5, -2), 1)
        _NS_gornak._aaline(surface, p["skin_dark"], pt(-4, 1), pt(4, 1), 1)
        # Sabuk kulit diagonal - satu jalur tipis (dulu 5 px: jadi palang)
        _NS_gornak._aaline(surface, p["leather_dark"], pt(12 + twist, sh),
                           pt(-9, 3), 3)
        _NS_gornak._aaline(surface, p["leather_light"], pt(12 + twist, sh),
                           pt(-9, 3), 1)
        # Pelat spellbreaker: satu bentuk gelap dengan TEPI atas terang dan
        # SATU permata ungu. Pass-pass sebelumnya menaruh garis silang +
        # tiga titik rune di sini; di skala 720p itu terbaca sebagai noda
        # lavender, bukan detail. Satu fokus terang = satu bacaan jelas.
        poly_free(p["armor_darkest"], [pt(-12, sh + 1), pt(-1, sh + 2),
                                       pt(0, -5), pt(-11, -6)])
        poly_free(p["armor_mid"], [pt(-11, sh + 2), pt(-2, sh + 3),
                                   pt(-1, -5), pt(-10, -6)], outline=False)
        _NS_gornak._aaline(surface, p["armor_shine"], pt(-11, sh + 3),
                           pt(-2, sh + 4), 2)
        _NS_gornak._aaline(surface, p["armor_darkest"], pt(-1, sh + 3),
                           pt(0, -5), 1)
        hot = 0.40 + (0.60 if (ward or void) else 0.0)
        a = _NS_gornak._alpha(150 + 105 * hot *
                              (0.72 + 0.28 * math.sin(phase * 2.2)))
        gemx, gemy = pt(-6, sh + 5)
        _NS_gornak._aacircle(surface, (*p["magic_mid"], a), (gemx, gemy), 3)
        _NS_gornak._aacircle(surface, (*p["magic_hot"], min(255, a + 40)),
                             (gemx, gemy), 2)
        _NS_gornak._rect(surface, (*p["magic_shine"], 255),
                         (gemx - 1, gemy - 1, 2, 2))
        # Cincin kuningan di ujung harness - geser ke tengah-tulang-dada
        # (di sisi kiri dia terbaca sebagai bintik nyasar) dan buang
        # highlight putihnya: satu nilai saja sudah cukup terbaca.
        dot(p["brass_dark"], -1, -7, 2)
        dot(p["brass_mid"], -1, -7, 1)

    def _draw_gnk_belt(surface, pt, poly_free, dot, f, phase, action, stride):
        """Sabuk + gesper berlian ungu, loincloth, rantai lempengan besi."""
        p = _NS_gornak.PALETTE
        sway = int(math.sin(phase * 1.1) * 2)
        if action == "walk":
            sway += int(stride * 2)
        poly_free(p["leather_dark"], [pt(-12, 1), pt(12, 1), pt(12, 7),
                                      pt(-12, 7)])
        poly_free(p["leather_mid"], [pt(-11, 2), pt(11, 2), pt(11, 6),
                                     pt(-11, 6)], outline=False)
        _NS_gornak._aaline(surface, p["leather_light"], pt(-11, 2), pt(11, 2),
                           1)
        for bx in (-8, -3, 7):
            _NS_gornak._aacircle(surface, p["brass_mid"], pt(bx, 4), 1)
        poly_free(p["armor_darkest"], [pt(-3, 0), pt(4, 0), pt(4, 8),
                                       pt(-3, 8)])
        poly_free(p["armor_light"], [pt(-2, 1), pt(3, 1), pt(3, 6), pt(-2, 6)],
                  outline=False)
        _NS_gornak._aacircle(surface, p["magic_hot"], pt(0, 4), 2)
        _NS_gornak._aacircle(surface, p["magic_shine"], pt(0, 4), 1)
        # Loincloth bertepi robek. Sengaja sempit (lebar 12, panjang 20):
        # versi lebar mengubah kedua kaki jadi satu tiang ungu dan
        # menghapus silhouette "berdiri".
        # Kain dijatuhkan ke sisi BELAKANG garis tengah: sebelumnya simetris
        # sehingga menutup paha depan dan kaki tampak hilang satu.
        outer = [(-8, 7), (3, 7), (4 + sway, 18), (1 + sway, 24), (-2, 18),
                 (-3, 24), (-6, 18), (-8 + sway, 22), (-10 + sway, 16)]
        hem = [(4 + sway, 18), (1 + sway, 24), (-2, 18), (-3, 24),
               (-6, 18), (-8 + sway, 22), (-10 + sway, 16)]
        tuft = _NS_gornak._tuft_points(hem, depth=1.8, min_len=3.5, seed=3)
        outer = [(-8, 7), (3, 7)] + tuft
        poly_free(p["robe_darkest"], [pt(*q) for q in outer])
        inner = [(-7, 8), (2, 8), (3 + sway, 17), (0 + sway, 21), (-2, 17),
                 (-4, 21), (-7 + sway, 15)]
        poly_free(p["robe_dark"], [pt(*q) for q in inner], outline=False)
        poly_free(p["robe_mid"], [pt(-3, 9), pt(3, 9), pt(3 + sway, 18),
                                  pt(0, 22), pt(-3 + sway, 17)],
                  outline=False)
        _NS_gornak._aaline(surface, p["robe_edge"], pt(-6, 9),
                           pt(-8 + sway, 20), 1)
        # Rantai lempengan pemutus sihir
        for i in range(3):
            yy = 9 + i * 4
            _NS_gornak._aaline(surface, p["armor_shine"], pt(9, yy),
                               pt(11 + int(sway * 0.3), yy + 3), 1)
            _NS_gornak._aacircle(surface, p["armor_light"], pt(10, yy + 1), 1)
        # Kantong kulit
        poly_free(p["leather_dark"], [pt(-13, 8), pt(-8, 8), pt(-7, 15),
                                      pt(-13, 15)])
        poly_free(p["leather_mid"], [pt(-12, 9), pt(-9, 9), pt(-8, 14),
                                     pt(-12, 14)], outline=False)

    def _draw_gnk_pauldrons(surface, pt, poly_free, dot, f, phase, breath):
        """Pauldron baja bertingkat + duri + permata ungu di sisi belakang."""
        p = _NS_gornak.PALETTE
        sh = _NS_gornak.SHOULDER_Y
        for side, scale in ((-1, 0.80), (1, 1.0)):
            sx = side * 15
            sy = sh - 2 - int(breath if side > 0 else 0)
            w = max(4, int(8 * scale))
            h = max(3, int(6 * scale))
            poly_free(p["armor_darkest"], [pt(sx - w, sy - h + 2),
                                          pt(sx + w, sy - h),
                                          pt(sx + w + 1, sy + 2),
                                          pt(sx, sy + h),
                                          pt(sx - w - 1, sy + 2)])
            poly_free(p["armor_mid"], [pt(sx - w + 1, sy - h + 3),
                                       pt(sx + w - 1, sy - h + 3),
                                       pt(sx + w, sy), pt(sx, sy + h - 2),
                                       pt(sx - w, sy)], outline=False)
            # Sisi JAUH dibiarkan gelap (dulu armor_light + shine: jadi
            # "sayat" pucat yang mengungguli wajah). Cahaya dan permata
            # tema ditaruh di sisi DEPAN, searah cahaya.
            lit = p["armor_light"] if side > 0 else p["armor_dark"]
            poly_free(lit, [pt(sx - w + 2, sy - h + 4),
                            pt(sx - 1, sy - h + 4),
                            pt(sx - 1, sy - 1),
                            pt(sx - w + 2, sy - 1)], outline=False)
            if side > 0:
                _NS_gornak._aaline(surface, p["armor_shine"],
                                   pt(sx - w + 2, sy - h + 4),
                                   pt(sx + w - 1, sy - h + 3), 1)
                # Specular cluster 1-2 px (bukan gradien) di pauldron depan.
                hx, hy = pt(sx - 2, sy - h + 3)
                _NS_gornak._rect(surface, p["armor_shine"], (hx, hy, 2, 1))
                _NS_gornak._rect(surface, p["white"], (hx, hy, 1, 1))
            spike = sy - h - (6 if side > 0 else 4)
            poly_free(p["armor_darkest"], [pt(sx - 2, sy - h + 1),
                                           pt(sx + 1, spike),
                                           pt(sx + 3, sy - h + 1)])
            poly_free(p["armor_light"], [pt(sx - 1, sy - h + 1),
                                         pt(sx + 1, spike + 1),
                                         pt(sx + 2, sy - h + 1)],
                      outline=False)
            _NS_gornak._aacircle(surface, p["brass_mid"], pt(sx + side * 4,
                                                            sy + 2), 1)
            if side > 0:
                # Permata tema: 2px saja. Versi 3+2 px tadi jadi blob ungu
                # yang mengambang di bahu dan mencuri fokus dari wajah.
                _NS_gornak._aacircle(surface, p["magic_mid"], pt(sx - 3,
                                                                sy - 1), 2)
                _NS_gornak._rect(surface, p["magic_shine"],
                                 (pt(sx - 3, sy - 1)[0],
                                  pt(sx - 3, sy - 1)[1], 1, 1))

    def _draw_gnk_head(surface, pt, poly_free, dot, f, phase, action, ward,
                       void):
        """KEPALA sebagai subjek: krist mohawk solid, wajah terang, mata
        menyala ber-halo ungu, jenggot kepang, circlet ber-taring.

        Versi awal masterwork masih terlalu "halus": rongga mata selebar 1 px
        dan helai rambut 1 px hilang setelah smoothscale jalur hero, sehingga
        kepala terbaca sebagai blob gelap. Sekarang volume rambut jadi SATU
        massa terang dengan 3 duri (bukan helaian), wajah blok TERANG, dan
        mata dua garis tebal + halo - persis cara Grimjaw (mask putih) atau
        Kaizen (ponytail) mempertahankan focal point di skala kecil.
        """
        p = _NS_gornak.PALETTE
        hy = _NS_gornak.HEAD_Y + int(math.sin(phase * 0.62) * 0.8)
        hx = 2 if action == "attack" else (0 if action == "void" else 1)
        sh = _NS_gornak.SHOULDER_Y

        # Leher & trapezius
        poly_free(p["skin_darkest"], [pt(-6, sh + 1), pt(6, sh + 1),
                                      pt(9, sh + 5), pt(-9, sh + 5)])
        poly_free(p["skin_mid"], [pt(-4, sh + 2), pt(4, sh + 2),
                                  pt(6, sh + 5), pt(-5, sh + 5)],
                  outline=False)

        # Massa rambut belakang (krist) - lebih besar dari tengkorak
        wave = int(math.sin(phase * 1.35) * 1.5)
        if action in ("walk", "attack", "surge"):
            wave -= 2
        crest = [(hx - 10, hy + 6), (hx - 13 + wave, hy - 2),
                 (hx - 11 + wave, hy - 12), (hx - 4, hy - 15),
                 (hx + 4, hy - 11), (hx + 7, hy - 3), (hx + 6, hy + 6)]
        poly_free(p["hair_darkest"], [pt(*q) for q in crest])
        # Pangkal krist ditebelkan 1 px supaya rambut tidak menempel langsung
        # ke dahi terang (kalau menempel, wajah kehilangan bentuknya).
        _NS_gornak._aaline(surface, p["shadow_deep"], pt(hx - 8, hy - 7),
                           pt(hx + 7, hy - 7), 1)
        crest_in = [(hx - 9, hy + 4), (hx - 11 + wave, hy - 2),
                    (hx - 9 + wave, hy - 10), (hx - 4, hy - 13),
                    (hx + 2, hy - 9), (hx + 5, hy - 2), (hx + 4, hy + 4)]
        poly_free(p["hair_mid"], [pt(*q) for q in crest_in], outline=False)
        # 3 duri krist - bentuk besar, BUKAN helai 1 px (hilang saat
        # di-scale). Duri tengah sedikit lebih pendek dan tiap duri
        # dipisah 1 px gelap supaya tidak jadi satu kerucut "topi penyihir".
        for i, (bx, bh) in enumerate(((-10, 11), (-3, 13), (4, 9))):
            tipx = hx + bx - 4 + wave
            tipy = hy - bh
            poly_free(p["hair_light"], [pt(hx + bx - 1, hy - 3), pt(tipx, tipy),
                                       pt(hx + bx + 4, hy - 5)],
                      outline=False)
            poly_free(p["hair_shine"], [pt(hx + bx, hy - 4), pt(tipx + 1,
                                                                tipy + 2),
                                       pt(hx + bx + 2, hy - 5)],
                      outline=False)
        for bx in (-6, 1):
            _NS_gornak._aaline(surface, p["hair_darkest"], pt(hx + bx, hy - 4),
                               pt(hx + bx - 3 + wave, hy - 12), 1)
        # Kuncir: pita rambut ramping yang keluar dari samping kepala dan
        # diikat cincin kuningan - menambah massa di belakang kepala tanpa
        # jadi gumpalan di atas bahu.
        poly_free(p["hair_dark"], [pt(hx - 10, hy - 2), pt(hx - 15 + wave, hy - 1),
                                   pt(hx - 16 + wave, hy + 5),
                                   pt(hx - 12, hy + 4), pt(hx - 9, hy + 1)])
        poly_free(p["hair_mid"], [pt(hx - 11, hy), pt(hx - 14 + wave, hy + 1),
                                 pt(hx - 12, hy + 3)], outline=False)
        _NS_gornak._aacircle(surface, p["brass_mid"], pt(hx - 10, hy), 2)

        # Tengkorak + rahang bidang
        poly_free(p["skin_darkest"], [pt(hx - 8, hy - 7), pt(hx + 8, hy - 7),
                                      pt(hx + 9, hy + 2), pt(hx + 7, hy + 9),
                                      pt(hx - 4, hy + 10), pt(hx - 8, hy + 3)])
        poly_free(p["skin_mid"], [pt(hx - 7, hy - 6), pt(hx + 7, hy - 6),
                                  pt(hx + 8, hy + 2), pt(hx + 6, hy + 8),
                                  pt(hx - 3, hy + 9), pt(hx - 7, hy + 2)],
                  outline=False)
        # WAJAH: terang di tulang pipi, gelap di rongga mata. Aturan yang
        # dipakai Grimjam (mask putih) / Kaizen (belang biru): SATU blok
        # terang kecil + SATU blok gelap, bukan gradasi lebar - kalau lebar,
        # di skala hero wajah jadi "topeng merah muda" tanpa fitur.
        poly_free(p["skin_light"], [pt(hx - 5, hy - 1), pt(hx + 6, hy - 1),
                                    pt(hx + 5, hy + 3), pt(hx - 3, hy + 4)],
                  outline=False)
        poly_free(p["skin_shine"], [pt(hx + 1, hy + 1), pt(hx + 5, hy + 1),
                                     pt(hx + 5, hy + 3),
                                     pt(hx + 1, hy + 3)], outline=False)
        # Dahi (terang, dipisah alis gelap) + cavum mata 4 px
        poly_free(p["skin_mid"], [pt(hx - 6, hy - 6), pt(hx + 7, hy - 6),
                                  pt(hx + 7, hy - 4),
                                  pt(hx - 6, hy - 4)], outline=False)
        poly_free(p["skin_darkest"], [pt(hx - 6, hy - 4), pt(hx + 7, hy - 4),
                                      pt(hx + 7, hy + 0), pt(hx - 6, hy + 0)],
                  outline=False)
        # Mata menyala: dua blok + halo ungu. PLUS kedip berkala - satu
        # frame kelopak turun tiap ~4 dtk, cukup untuk membuat unit terasa
        # hidup di lane tanpa mengorbankan satu piksel pun di pose lain.
        blink = ((phase * 0.6) % 4.2) < 0.16
        if blink:
            poly_free(p["skin_dark"], [pt(hx - 6, hy - 4), pt(hx + 7, hy - 4),
                                       pt(hx + 7, hy - 1),
                                       pt(hx - 6, hy - 1)], outline=False)
        # DUA mata, bukan satu bar: tiap mata 2 px dengan batang hidung gelap
        # 2 px di antaranya. Tanpa pemisah itu, wajah terbaca sebagai satu
        # garis putih (keluhan "wajah masih pita terang" di pass sebelumnya).
        for ex in ((hx - 1, hx + 4) if not blink else ()):
            _NS_gornak._aaline(surface, p["eye_mid"], pt(ex, hy - 2.5),
                               pt(ex + 1, hy - 2.5), 2)
            _NS_gornak._aaline(surface, p["eye_glow"], pt(ex, hy - 2.5),
                               pt(ex + 1, hy - 2.5), 1)
        if not blink:
            _NS_gornak._aaline(surface, p["skin_darkest"], pt(hx + 2, hy - 4),
                               pt(hx + 2, hy + 0), 2)   # batang hidung
        ga = _NS_gornak._alpha(85 + (115 if (ward or void) else 0))
        gx, gy = pt(hx + 1.5, hy - 2.5)
        _NS_gornak._aacircle(surface, (*p["eye_light"], ga), (gx, gy), 3)
        _NS_gornak._aacircle(surface, (*p["magic_hot"], ga // 2), (gx, gy), 5)
        # War paint ungu di pipi (sinyal warna tema, terlihat di 1x)
        wp = _NS_gornak._alpha(190)
        _NS_gornak._aaline(surface, (*p["magic_light"], wp), pt(hx - 4, hy + 1),
                           pt(hx - 1, hy + 3), 1)
        _NS_gornak._aaline(surface, (*p["magic_light"], wp), pt(hx - 5, hy + 2),
                           pt(hx - 2, hy + 4), 1)
        # Hidung & mulut
        _NS_gornak._aaline(surface, p["skin_darkest"], pt(hx + 8, hy + 1),
                           pt(hx + 8, hy + 4), 1)
        _NS_gornak._aaline(surface, p["skin_darkest"], pt(hx + 4, hy + 5),
                           pt(hx + 7, hy + 5), 1)

        # Jenggot kepang: hanya RAHANG BAWAH (dulu sampai hy+16 -> menyatu
        # dengan leher & dada jadi satu massa gelap).
        poly_free(p["beard_darkest"], [pt(hx - 5, hy + 5), pt(hx + 7, hy + 5),
                                       pt(hx + 6, hy + 10), pt(hx + 2, hy + 13),
                                       pt(hx - 3, hy + 10)])
        poly_free(p["beard_mid"], [pt(hx - 3, hy + 6), pt(hx + 5, hy + 6),
                                   pt(hx + 4, hy + 9), pt(hx + 2, hy + 11),
                                   pt(hx - 2, hy + 9)], outline=False)
        # Garis gelap di bawah rahang: memisahkan jenggot dari leher/dada,
        # kalau tidak semuanya jadi satu massa coklat.
        _NS_gornak._aaline(surface, p["shadow_deep"], pt(hx - 5, hy + 11),
                           pt(hx + 6, hy + 10), 1)
        poly_free(p["beard_mid"], [pt(hx + 1, hy + 12), pt(hx + 4, hy + 12),
                                   pt(hx + 3, hy + 15)], outline=False)
        for i in range(3):
            _NS_gornak._aaline(surface, p["beard_darkest"],
                               pt(hx - 2 + i * 3, hy + 6),
                               pt(hx - 1 + i * 3, hy + 13), 1)
        dot(p["brass_dark"], hx + 2, hy + 13, 2)
        _NS_gornak._aacircle(surface, p["brass_mid"], pt(hx + 2, hy + 13), 1)

        # Circlet besi + taring pelipis + permata ungu di dahi
        poly_free(p["armor_darkest"], [pt(hx - 8, hy - 7), pt(hx + 8, hy - 7),
                                       pt(hx + 8, hy - 4), pt(hx - 8, hy - 4)])
        poly_free(p["armor_light"], [pt(hx - 7, hy - 6.5), pt(hx + 7, hy - 6.5),
                                     pt(hx + 7, hy - 5),
                                     pt(hx - 7, hy - 5)], outline=False)
        _NS_gornak._aacircle(surface, p["magic_hot"], pt(hx + 6, hy - 6), 1)
        poly_free(p["armor_mid"], [pt(hx - 9, hy - 6), pt(hx - 9, hy - 11),
                                   pt(hx - 7, hy - 6)], outline=False)
        poly_free(p["armor_mid"], [pt(hx + 8, hy - 6), pt(hx + 9, hy - 11),
                                   pt(hx + 7, hy - 6)], outline=False)

    def _draw_gnk_rimlight(surface, pt, f, phase, ward, void):
        """Rim light ungu tipis di tepi yang menghadap cahaya.

        Ini yang paling hilang dari render sebelumnya: semua hero masterwork
        lain punya "sinyal" warna di tepian (Grimjam api, Vex void cyan,
        Kaizen angin biru) sehingga terbaca saat unit bertumpuk. Gornak
        memakai ungu anti-sihir; 1 px saja, tapi di posisi yang tepat
        (puncak bahu, tepi pelat, punggung bilah, ujung boot).
        """
        p = _NS_gornak.PALETTE
        sh = _NS_gornak.SHOULDER_Y
        hy = _NS_gornak.HEAD_Y + int(math.sin(phase * 0.62) * 0.8)
        pulse = 1.0 if (ward or void) else (0.72 + 0.28 * math.sin(phase * 1.8))
        a = _NS_gornak._alpha(150 * pulse)
        col = (*p["magic_light"], a)
        # Puncak krist saja + tepi pelat: garis di bahu tumpang tindih
        # dengan armor_shine pauldron jadi terlihat seperti noda.
        _NS_gornak._aaline(surface, col, pt(-8, hy - 12), pt(2, hy - 13), 1)
        # Tepi pelat dada & sabuk
        _NS_gornak._aaline(surface, col, pt(-11, sh + 1), pt(-11, -5), 1)
        _NS_gornak._aaline(surface, (*p["magic_hot"], a), pt(-12, 1),
                           pt(12, 1), 1)
        # Garis cahaya di lutut & ujung boot
        for sx in (-5, 9):
            _NS_gornak._aaline(surface, col, pt(sx, 22), pt(sx + 1, 30), 1)
            _NS_gornak._aacircle(surface, col, pt(sx + 1, 41), 1)

    def _draw_gnk_arm(surface, pt, poly_free, dot, limb, f, phase, action, ap,
                      shoulder, elbow, grip, blade_angle, blade_len, back=False,
                      ward=False, void=False, surge=False):
        """Lengan 2-tulang + bracer + bilah. Bayangan antar-bagian cukup
        +2 px; outline luar sudah memberi pemisah, jadi tidak perlu tebal."""
        p = _NS_gornak.PALETTE
        base = p["skin_dark"] if back else p["skin_mid"]
        high = p["skin_mid"] if back else p["skin_light"]
        # Satu tingkat lebih berisi daripada pass sebelumnya: di skala hero
        # bilah yang panjang+terang sempat mendominasi sampai lengan terlihat
        # seperti ranting dan pedang seperti menempel sendiri di dada.
        limb(shoulder, elbow, 6 if back else 7, base, high)
        limb(elbow, grip, 5 if back else 6, base, high)
        # Bracer besi: satu blok di tengah lengan bawah
        bx = int(elbow[0] * 0.4 + grip[0] * 0.6)
        by = int(elbow[1] * 0.4 + grip[1] * 0.6)
        poly_free(p["armor_darkest"], [pt(bx - 3, by - 3), pt(bx + 3, by - 3),
                                       pt(bx + 3, by + 3), pt(bx - 3, by + 3)])
        poly_free(p["armor_light"], [pt(bx - 2, by - 2), pt(bx + 1, by - 2),
                                     pt(bx + 1, by + 2), pt(bx - 2, by + 2)],
                  outline=False)
        # Tangan + highlight buku jari: tanpa ini bilah terlihat "menempel"
        # di dada, bukan digenggam.
        dot(p["skin_darkest"], *grip, 3 if back else 4)
        dot(high, *grip, 2 if back else 3)
        if not back:
            kx, ky = pt(grip[0] + 1, grip[1] - 2)
            _NS_gornak._aacircle(surface, p["skin_shine"], (kx, ky), 2)
        _NS_gornak._draw_gnk_blade(surface, pt, f, grip, blade_angle,
                                   blade_len, phase, action, back=back,
                                   ward=ward, void=void, surge=surge)

    def _draw_gnk_blade(surface, pt, f, grip, angle, length, phase, action,
                        back=False, ward=False, void=False, surge=False):
        """Bilah "spellbreaker" melengkung - dihitung dari grip + sudut.

        Dibuat TERANG (nilai tertinggi ke-2 setelah mata) supaya senjata
        terbaca sebagai senjata, bukan tonjolan gelap seperti sebelumnya.
        """
        p = _NS_gornak.PALETTE
        s, c = math.sin(angle), math.cos(angle)
        segs = 6
        curve = 5.0 if not back else 3.0
        centers = []
        for i in range(segs + 1):
            t = i / segs
            bend = curve * (t * t)
            centers.append((grip[0] + s * length * t + c * bend,
                            grip[1] + c * length * t - s * bend))
        n_x, n_y = c, -s
        left, right = [], []
        for i, (x, y) in enumerate(centers):
            t = i / segs
            wd = (3.0 if not back else 2.2) * (1.0 - t) + 0.7 * t
            left.append((x + n_x * wd, y + n_y * wd))
            right.append((x - n_x * wd, y - n_y * wd))
        body = left + right[::-1]
        poly_pts = [pt(*q) for q in body]
        _NS_gornak._poly(surface, p["shadow_deep"],
                         [(q[0] + f, q[1] + 1) for q in poly_pts])
        _NS_gornak._poly(surface, p["blade_mid"], poly_pts)

        def inset(k):
            out = []
            for (x, y) in body:
                dx = (x - grip[0]) * k
                dy = (y - grip[1]) * k
                out.append(pt(int(x - dx), int(y - dy)))
            return out

        _NS_gornak._poly(surface, p["blade_light"], inset(0.22))
        _NS_gornak._poly(surface, p["blade_shine"], inset(0.52))
        # Rune penyedot mana - hanya saat menyerang / skill
        hot = 0.30 + (0.70 if (ward or void or surge or action == "attack")
                      else 0.0)
        glow_a = _NS_gornak._alpha(150 * hot *
                                   (0.8 + 0.2 * math.sin(phase * 2.2)))
        core = [pt(*q) for q in centers]
        if not back:
            for i in range(len(core) - 1):
                _NS_gornak._aaline(surface, (*p["magic_light"], glow_a),
                                   core[i], core[i + 1], 1)
        # Gagang kulit + cross-guard + pommel
        g1 = pt(grip[0] - int(c * 3), grip[1] + int(s * 3))
        g2 = pt(grip[0] + int(c * 3), grip[1] - int(s * 3))
        _NS_gornak._aaline(surface, p["shadow_deep"], (g1[0] + f, g1[1] + 1),
                           (g2[0] + f, g2[1] + 1), 4)
        _NS_gornak._aaline(surface, p["armor_mid"], g1, g2, 2)
        butt = pt(grip[0] - int(s * 6), grip[1] - int(c * 6))
        gx, gy = pt(*grip)
        _NS_gornak._aaline(surface, p["leather_dark"], (gx, gy), butt, 4)
        _NS_gornak._aaline(surface, p["leather_light"], (gx, gy), butt, 1)
        _NS_gornak._aacircle(surface, p["brass_mid"], butt, 2)
        tip = core[-1]
        _NS_gornak._aacircle(surface, (*p["magic_hot"], glow_a), tip, 2)
        # Specular cluster 1-2 px (bukan gradien) di sisi cahaya bilah.
        if not back and len(core) > 3:
            gl = core[2]
            _NS_gornak._rect(surface, p["blade_shine"], (gl[0] - 1, gl[1] - 1, 2, 1))
            _NS_gornak._rect(surface, p["white"], (gl[0], gl[1] - 1, 1, 1))
        if (ward or void or surge) and not back:
            _NS_gornak._spark_star(
                surface, tip[0], tip[1], 7, p["magic_hot"],
                _NS_gornak._alpha(glow_a * 0.85), spikes=6,
                rot=phase * 1.6, core=p["magic_shine"])

    # ==================================================================
    # PORTRAIT LOD - material tambahan (Hero Shop / panel)
    # ==================================================================
    def _draw_gnk_weave(surface, pt, f):
        """Tenun kain & grain kulit - HANYA portrait LOD.

        Dither 1-px seperti ini justru jadi noise/kasar setelah jalur hero
        men-smoothscale sprite ke 0.7-0.8, jadi dibatasi ke mode detail.
        """
        p = _NS_gornak.PALETTE
        for i in range(9):
            wx, wy = pt(-8 + (i % 4) * 4, 8 + (i // 4) * 4)
            _NS_gornak._rect(surface, (*p["robe_light"], 90), (wx, wy, 1, 1))
        for i in range(7):
            x0, y0 = -12 + i * 4, -12 + (i % 3) * 6
            _NS_gornak._rect(surface, (*p["skin_shine"], 70),
                             (pt(x0, y0)[0], pt(x0, y0)[1], 1, 1))

    def _draw_gnk_masterwork_details(surface, pt, f, phase, action):
        """Detail frekuensi tinggi; di skala arena tanda-tanda ini hanya
        akan menjadi noise, jadi hanya dinyalakan saat portrait."""
        p = _NS_gornak.PALETTE
        hx = 1 if f > 0 else -1
        cy = _NS_gornak.HEAD_Y + int(math.sin(phase * 0.62) * 0.8)
        # Helai rambut ekstra di atas krist
        for i in range(7):
            bx = hx - 7 + i * 2
            by = cy - 7 - abs(i - 3)
            wx = bx - 3 + int(math.sin(phase * 1.4 + i) * 2)
            _NS_gornak._aaline(surface, p["hair_shine"], pt(bx, by),
                               pt(wx, by - 10 - (i % 3)), 1)
        # Serat jenggot
        for i in range(4):
            _NS_gornak._aaline(surface, p["beard_mid"],
                               pt(hx - 4 + i * 2, cy + 5),
                               pt(hx - 3 + i * 2, cy + 12), 1)
        # Alis tebal
        _NS_gornak._aaline(surface, p["beard_darkest"], pt(hx - 1, cy - 4),
                           pt(hx + 6, cy - 5), 1)
        # Grain kulit pada bahu & dada
        for i in range(10):
            dx = -9 + (i % 5) * 4
            dy = -17 + (i // 5) * 8
            _NS_gornak._aaline(surface, (*p["skin_shine"], 110), pt(dx, dy),
                               pt(dx + 1, dy), 1)
        # Otot leher
        _NS_gornak._aaline(surface, p["skin_dark"], pt(hx - 4, -20),
                           pt(hx - 1, -16), 1)
        # Jahitan jubah & loincloth
        for yy in (8, 13, 18):
            _NS_gornak._aaline(surface, (*p["robe_edge"], 150), pt(-15, yy),
                               pt(-10, yy + 1), 1)
        for xx in (-5, 0, 5):
            _NS_gornak._aaline(surface, (*p["robe_light"], 120), pt(xx, 8),
                               pt(xx + 1, 23), 1)
        # Tato rune anti-sihir
        for i in range(4):
            _NS_gornak._aaline(surface, (*p["magic_light"], 140),
                               pt(-12 + i * 2, -13 + i * 6),
                               pt(-10 + i * 2, -11 + i * 6), 1)
        # Ukiran pelat & paku pauldron
        _NS_gornak._aaline(surface, (*p["armor_shine"], 165), pt(-9, -15),
                           pt(0, -14), 1)
        _NS_gornak._aaline(surface, (*p["armor_shine"], 165), pt(-9, -11),
                           pt(-1, -10), 1)
        for sx, sy in ((13, -22), (15, -19), (11, -18), (-13, -21)):
            _NS_gornak._aacircle(surface, (*p["armor_shine"], 150), pt(sx, sy),
                                 1)
        # Ringgit gagang & garis hamon bilah
        for i in range(5):
            t = i / 5
            _NS_gornak._aaline(surface, (*p["blade_hamon"], 170),
                               pt(13 + int(t * 12), 3 - int(t * 15)),
                               pt(14 + int(t * 12), 4 - int(t * 15)), 1)

    def _draw_footfall_dust(surface, x, y, facing, phase):
        """Kepul debu di tapak yang mendarat (deterministik dari phase)."""
        p = _NS_gornak.PALETTE
        contact = abs(math.sin(phase * 1.15))
        if contact > 0.72:
            return
        gy = y + _NS_gornak.GROUND_DY
        k = _NS_gornak._s
        for side in (-1, 1):
            for i in range(3):
                t = (contact + i * 0.3) % 1.0
                a = _NS_gornak._alpha(150 * (1.0 - t) * (0.72 - contact))
                if a <= 0:
                    continue
                px = x + side * k(7 + i * 2 + t * 5) + facing * k(t * 4)
                py = gy - k(t * 5)
                _NS_gornak._aacircle(surface, (*p["robe_edge"], a), (px, py),
                                     max(1, k(2 - t)))
                _NS_gornak._rect(surface, (*p["white"], a // 2),
                                 (px, py, 1, 1))

    # ==================================================================
    # EFEK DASAR - ditundukan pada karakter
    # ==================================================================
    def _draw_shadow(surface, x, y):
        """Bayangan kontak tunggal yang lembek (base_boss menggambar satu
        lagi; ini dipertipis supaya tidak jadi dua piringan hitam)."""
        p = _NS_gornak.PALETTE
        K = _NS_gornak.SCALE
        bw, bh = int(60 * K), int(18 * K)

        def _build():
            sh = pygame.Surface((bw, bh), pygame.SRCALPHA)
            for w, h, a in ((int(42 * K), int(10 * K), 70),
                            (int(30 * K), int(7 * K), 90),
                            (int(18 * K), int(4 * K), 110)):
                _NS_gornak._ellipse(sh, (0, 0, 0, a),
                                    (bw // 2 - w // 2, bh // 2 - h // 2, w, h))
            _NS_gornak._ellipse(sh, (*p["magic_darkest"], 60),
                                (int(6 * K), int(3 * K), int(48 * K), int(12 * K)))
            for side in (-1, 1):
                fx = bw // 2 + int(side * 9 * K)
                _NS_gornak._ellipse(sh, (0, 0, 0, 130),
                                    (fx - int(5 * K), int(bh * 0.62),
                                     int(10 * K), int(4 * K)))
            return sh

        sh = _NS_gornak._static(("gnk_shadow", bw, bh), _build)
        surface.blit(sh, (int(x) - bw // 2, int(y) - bh // 2))

    def _draw_anti_magic_field(surface, x, y, phase, skill):
        """Cahaya lembut MENEMPEL badan + percikan mengorbit siluet."""
        p = _NS_gornak.PALETTE
        pulse = 1.0 if skill else math.sin(phase * 0.7) * 0.25 + 0.72
        K = _NS_gornak.SCALE
        gw, gh = int(80 * K), int(96 * K)
        cx, cy = int(40 * K), int(50 * K)

        def _build():
            glow = pygame.Surface((gw, gh), pygame.SRCALPHA)
            for rx, ry, col, a in ((int(30 * K), int(38 * K), "magic_darkest", 78),
                                   (int(23 * K), int(30 * K), "magic_dark", 96),
                                   (int(16 * K), int(22 * K), "magic_mid", 120)):
                _NS_gornak._ellipse(glow, (*p[col], a),
                                    (cx - rx, cy - ry, rx * 2, ry * 2))
            _NS_gornak._ellipse(glow, (*p["magic_light"], 70),
                                (cx - int(16 * K), cy - int(22 * K),
                                 int(32 * K), int(44 * K)), 1)
            return glow

        glow = _NS_gornak._static(("gnk_aura", gw, gh), _build)
        glow.set_alpha(_NS_gornak._alpha(255 * pulse))
        surface.blit(glow, (int(x) - cx, int(y) - cy + 8))

        n = 6
        for i in range(n):
            ang = ((phase * 0.35 + i / n) % 1.0) * math.tau
            r = _NS_gornak._s(20) + int(math.sin(phase * 1.3 + i * 2) * 3)
            sx = x + int(math.cos(ang) * r * 1.25)
            sy = y + 2 + int(math.sin(ang) * r * 0.8)
            a = _NS_gornak._alpha(120 + 80 * math.sin(phase * 3 + i))
            _NS_gornak._aacircle(surface, (*p["magic_mid"], a), (sx, sy), 2)
            _NS_gornak._aacircle(surface, (*p["magic_shine"], a), (sx, sy), 1)

    def _draw_ground_rune(surface, x, y, phase, skill):
        """Cincin rune di bawah kaki - kecil TAPI terang."""
        p = _NS_gornak.PALETTE
        pulse = math.sin(phase * 1.1) * 0.25 + 0.75
        gy = y + _NS_gornak.GROUND_DY
        bright = 1.15 if skill else 0.95
        rw, rh = _NS_gornak._s(22), _NS_gornak._s(6)
        _NS_gornak._ellipse(surface,
                            (*p["magic_darkest"],
                             _NS_gornak._alpha(150 * pulse * bright)),
                            (x - rw, gy - rh, rw * 2, rh * 2), 2)
        rw2, rh2 = _NS_gornak._s(15), _NS_gornak._s(4)
        _NS_gornak._ellipse(surface,
                            (*p["magic_mid"],
                             _NS_gornak._alpha(140 * pulse * bright)),
                            (x - rw2, gy - rh2, rw2 * 2, rh2 * 2), 1)
        t0, t1 = _NS_gornak._s(18), _NS_gornak._s(24)
        ty0, ty1 = _NS_gornak._s(5), _NS_gornak._s(6)
        for i in range(6):
            ang = phase * 0.4 + i * math.tau / 6
            _NS_gornak._aaline(
                surface,
                (*p["magic_light"], _NS_gornak._alpha(170 * pulse * bright)),
                (x + int(math.cos(ang) * t0), gy + int(math.sin(ang) * ty0)),
                (x + int(math.cos(ang) * t1), gy + int(math.sin(ang) * ty1)), 1)
        irw, irh = _NS_gornak._s(11), _NS_gornak._s(3)
        _NS_gornak._ellipse(surface,
                            (*p["magic_light"],
                             _NS_gornak._alpha(150 * pulse * bright)),
                            (x - irw, gy - irh, irw * 2, irh * 2), 1)
        _NS_gornak._aacircle(surface, (*p["magic_shine"],
                                       _NS_gornak._alpha(200 * pulse)),
                             (int(x), int(gy)), 2)
        if skill in ("e", "r"):
            ew, eh = _NS_gornak._s(26), _NS_gornak._s(7)
            _NS_gornak._ellipse(
                surface, (*p["magic_hot"], _NS_gornak._alpha(120 * pulse)),
                (x - ew, gy - eh, ew * 2, eh * 2), 1)

    def _draw_crescent_slash(surface, x, y, facing, phase, progress):
        """Pita slash dari trail UJUNG BILAH (bukan busur titik melayang)."""
        if progress < 0.24 or progress > 0.92:
            return
        p = _NS_gornak.PALETTE
        lean, root_y = _NS_gornak._rig_shift("attack", phase, progress)

        def scr(lx, ly):
            return _NS_gornak._local_to_screen(x, y, facing, lean, root_y,
                                               lx, ly)

        def tip_at(ap):
            return scr(*_NS_gornak._tip_local("attack", phase, ap))

        steps = 7
        trail = []
        for i in range(steps):
            t = i / (steps - 1)
            trail.append(tip_at(max(0.0, min(1.0, progress - 0.30 + t * 0.30))))
        pivot = scr(*_NS_gornak._front_grip_local("attack", progress, phase))
        fade = 1.0 - max(0.0, (progress - 0.70) / 0.22)
        alpha = _NS_gornak._alpha(230 * fade)
        if alpha <= 0:
            return
        for col, off, mul in (("magic_darkest", 8, 0.62),
                              ("magic_mid", 4, 0.9),
                              ("magic_shine", 1, 1.0)):
            outer, inner = [], []
            for i, q in enumerate(trail):
                t = i / (steps - 1)
                # Lebar pita memuncak dekat bilah dan menipis ke ekor,
                # supaya trail terbaca menyatu dengan senjata (versi
                # seragam menyisakan "serpihan" terpisah di ujung arc).
                w = max(0.5, (1 - abs(t - 0.8)) * off * (0.35 + 0.65 * t))
                vx, vy = q[0] - pivot[0], q[1] - pivot[1]
                ln = math.hypot(vx, vy) or 1.0
                nx, ny = -vy / ln, vx / ln
                outer.append((q[0] + nx * w, q[1] + ny * w))
                inner.append((q[0] - nx * w * 0.55, q[1] - ny * w * 0.55))
            _NS_gornak._poly(surface,
                              (*p[col], _NS_gornak._alpha(alpha * mul)),
                              outer + inner[::-1])
        if 0.40 <= progress <= 0.62:
            tip = trail[-1]
            for i in range(5):
                ang = -math.pi / 2 + i * math.pi / 4
                ex = tip[0] + int(math.cos(ang) * 7)
                ey = tip[1] + int(math.sin(ang) * 7)
                _NS_gornak._aaline(surface, (*p["magic_hot"], alpha), tip,
                                   (ex, ey), 1)
            # IMPACT: bintang spike + shockwave elips kecil
            if 0.50 <= progress <= 0.62:
                hold = 1.0 - abs((progress - 0.56) / 0.06)
                _NS_gornak._spark_star(
                    surface, tip[0], tip[1], 11, p["magic_hot"],
                    _NS_gornak._alpha(alpha * hold), spikes=8,
                    rot=progress * 4.0, core=p["white"])
                wr = int(8 + hold * 10)
                _NS_gornak._ellipse(
                    surface, (*p["magic_shine"], _NS_gornak._alpha(160 * hold)),
                    (tip[0] - wr, tip[1] - wr // 3, wr * 2, max(3, wr * 2 // 3)),
                    1)

    # ==================================================================
    # SKILL Q - MANA BREAK (world-space, 3 fase)
    # Telegraph/charge di ujung bilah -> bolt 3-lapis -> impact retak.
    # ==================================================================
    def _draw_manabreak_ground(surface, boss, x, y, timer, phase):
        """TELEGRAPH + charge di UJUNG BILAH sebelum bolt lepas."""
        p = _NS_gornak.PALETTE
        duration = _NS_gornak.SKILL_DUR["q"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress > 0.34:
            return
        t = progress / 0.34
        fs = _NS_gornak._fx_scale(boss)
        tx, ty = _NS_gornak._tip_screen(boss, x, y)
        r = int((4 + t * 9) * fs)
        for k in range(r + 3, 0, -1):
            a = _NS_gornak._alpha(200 * (r + 3 - k) / (r + 3) * (0.4 + t))
            _NS_gornak._aacircle(surface, (*p["magic_dark"], a), (tx, ty), k)
        for col, rr in (("magic_mid", r), ("magic_light", max(1, r - 2)),
                        ("magic_shine", max(1, r - 4))):
            _NS_gornak._aacircle(surface, p[col], (tx, ty), rr)
        # Cincin konvergen + chevron ke target (telegraph terbaca)
        aim = _NS_gornak._target_position(boss, x, y)
        ang = math.atan2(aim[1] - ty, aim[0] - tx)
        for k in range(3):
            rr = int((18 - t * 10 + k * 6) * fs)
            _NS_gornak._dashed_ring(
                surface, tx, ty, rr, p["magic_light"],
                _NS_gornak._alpha(200 * (1 - t) * (1 - k * 0.2)),
                phase * 2 + k, segments=8, thick=2, span=0.55, squash=0.85)
        for k in range(3):
            d = (12 + k * 10) * fs * (1.0 - t * 0.4)
            _NS_gornak._chevron(
                surface, tx + math.cos(ang) * d, ty + math.sin(ang) * d,
                ang, int(7 * fs), p["magic_hot"],
                _NS_gornak._alpha(220 * (0.4 + t)), width=2)
        _NS_gornak._spark_star(
            surface, tx, ty, int((8 + t * 6) * fs), p["magic_hot"],
            _NS_gornak._alpha(200 * t), spikes=8, rot=phase * 3,
            core=p["magic_shine"])
        for i in range(5):
            a2 = phase * 4 + i * math.tau / 5
            sx = tx + int(math.cos(a2) * (r + 4 * fs))
            sy = ty + int(math.sin(a2) * (r + 4 * fs))
            _NS_gornak._aaline(surface, (*p["magic_hot"], 225), (sx, sy),
                               (tx, ty), 1)

    def _draw_manabreak_foreground(surface, boss, x, y, timer, phase):
        """Bolt mana 3-lapis + glint ujung + impact retak (world-space)."""
        p = _NS_gornak.PALETTE
        duration = _NS_gornak.SKILL_DUR["q"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress <= 0.30:
            return
        t = (progress - 0.30) / 0.70
        fs = _NS_gornak._fx_scale(boss)
        sx, sy = _NS_gornak._tip_screen(boss, x, y)
        tx, ty = _NS_gornak._target_position(boss, x, y)
        bx, by = int(sx + (tx - sx) * t), int(sy + (ty - sy) * t)

        for i in range(9):
            tt = max(0.0, t - i * 0.05)
            px = int(sx + (tx - sx) * tt)
            py = int(sy + (ty - sy) * tt)
            a = _NS_gornak._alpha(230 - i * 22)
            size = max(2, int((8 - i) * fs))
            for col, off in (("magic_darkest", size + 1), ("magic_mid", size),
                             ("magic_light", max(1, size - 2))):
                if off > 0:
                    _NS_gornak._aacircle(surface, (*p[col], a), (px, py), off)
            _NS_gornak._rect(surface, (*p["magic_hot"], a), (px, py, 1, 1))

        # Glint berputar di ujung bolt
        rot = phase * 6 + t * 4
        _NS_gornak._spark_star(
            surface, bx, by, int(10 * fs), p["magic_shine"], 230,
            spikes=6, rot=rot, core=p["white"])
        for col, rr in (("magic_dark", int(10 * fs)), ("magic_mid", int(8 * fs)),
                        ("magic_light", int(5 * fs)), ("magic_shine", int(3 * fs)),
                        ("white", max(1, int(2 * fs)))):
            _NS_gornak._aacircle(surface, p[col], (bx, by), rr)

        if t > 0.86:
            st = (t - 0.86) / 0.14
            radius = int((11 + st * 26) * fs)
            a = _NS_gornak._alpha(240 * (1 - st))
            _NS_gornak._aacircle(surface, (*p["white"], a), (tx, ty),
                                 max(1, int(7 * fs * (1 - st))))
            _NS_gornak._aacircle(surface, (*p["magic_darkest"], a), (tx, ty),
                                 radius + 2, 3)
            _NS_gornak._aacircle(surface, (*p["magic_mid"], a), (tx, ty),
                                 max(1, radius - 4), 2)
            _NS_gornak._spark_star(
                surface, tx, ty, int(16 * fs * (1 - st)), p["magic_hot"], a,
                spikes=8, rot=st * 2, core=p["white"])
            for i in range(8):
                ang = i * math.pi / 4 + st * 0.5
                _NS_gornak._jagged_crack(
                    surface, tx, ty, ang, int((18 + st * 16) * fs),
                    (p["magic_darkest"], p["magic_hot"]), a, i + 3, width=2)

    # ==================================================================
    # SKILL W - BLINK (world-space departure / arrival)
    # ==================================================================
    def _draw_blink_ground(surface, boss, x, y, timer, phase):
        p = _NS_gornak.PALETTE
        duration = _NS_gornak.SKILL_DUR["w"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        fs = _NS_gornak._fx_scale(boss)
        gy = y + _NS_gornak.GROUND_DY
        if progress < 0.5:
            t = progress / 0.5
            r = int((10 + t * 15) * fs)
            a = _NS_gornak._alpha(240 * (1 - t))
        else:
            t = (progress - 0.5) / 0.5
            r = int((24 - t * 12) * fs)
            a = _NS_gornak._alpha(240 * t)
        if a <= 0:
            return
        _NS_gornak._ellipse(surface, (*p["magic_dark"], a),
                            (x - r - 3, gy - (r + 3) // 3, (r + 3) * 2,
                             max(3, (r + 3) // 2)), 1)
        _NS_gornak._ellipse(surface, (*p["magic_mid"], a),
                            (x - r, gy - r // 3, r * 2, max(3, r // 2)), 2)
        _NS_gornak._ellipse(surface, (*p["magic_hot"], a),
                            (x - r // 2, gy - r // 6, r, max(2, r // 4)), 2)
        _NS_gornak._dashed_ring(
            surface, x, gy, r + int(6 * fs), p["magic_light"], a,
            phase * 3, segments=9, thick=2, span=0.5, squash=0.42)
        if progress >= 0.5:
            r2 = int((24 + t * 14) * fs)
            a2 = _NS_gornak._alpha(200 * (1 - t))
            _NS_gornak._ellipse(surface, (*p["magic_shine"], a2),
                                (x - r2, gy - r2 // 3, r2 * 2,
                                 max(3, r2 // 2)), 1)
            _NS_gornak._spark_star(
                surface, x, gy - 6, int(12 * fs * (1 - t)), p["magic_hot"],
                a2, spikes=8, rot=t * 2, core=p["magic_shine"])
        for i in range(7):
            ang = phase * 2 + i * math.tau / 7
            _NS_gornak._rect(surface, (*p["magic_shine"], a),
                             (x + int(math.cos(ang) * (r + 3)),
                              gy + int(math.sin(ang) * max(1, r // 4)), 1, 1))

    # ==================================================================
    # SKILL E - COUNTERSPELL (AOE 100 px dunia)
    # Telegraph ring tepat 100 + kubah heksagon 3-lapis + stars.
    # ==================================================================
    def _draw_counterspell_foreground(surface, boss, x, y, timer, phase):
        p = _NS_gornak.PALETTE
        duration = _NS_gornak.SKILL_DUR["e"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        fs = _NS_gornak._fx_scale(boss)
        grow = 1.0
        if progress < 0.16:
            grow = 0.55 + (progress / 0.16) * 0.45
        elif progress > 0.86:
            grow = 1.0 - (progress - 0.86) / 0.14 * 0.35
        fade = 1.0 - max(0.0, (progress - 0.9)) * 8
        a_main = _NS_gornak._alpha(225 * fade)

        # TELEGRAPH: ring jangkauan TEPAT 100 px dunia
        wr = _NS_gornak._ring_r(boss, 100)
        gy = y + _NS_gornak.GROUND_DY
        # Ring solid 3-komponen (tanpa temp SRCALPHA) supaya radius 100
        # dunia tetap murah di canvas hero.
        if fade > 0.15:
            _NS_gornak._aacircle(surface, p["magic_light"],
                                 (int(x), int(y)), wr, max(2, int(2 * fs)))
        _NS_gornak._dashed_ring(
            surface, x, y, wr, p["magic_light"],
            _NS_gornak._alpha(210 * fade), phase * 1.4,
            segments=14, thick=max(2, int(2 * fs)), span=0.55, squash=1.0)
        _NS_gornak._dashed_ring(
            surface, x, y, max(4, int(wr * (0.72 + 0.10 * math.sin(phase * 3)))),
            p["magic_hot"], _NS_gornak._alpha(160 * fade), -phase * 1.1,
            segments=10, thick=2, span=0.45, squash=1.0)
        # Cincin konvergen di awal
        if progress < 0.28:
            conv = 1.0 - progress / 0.28
            _NS_gornak._aacircle(
                surface, (*p["magic_shine"], _NS_gornak._alpha(200 * conv)),
                (int(x), int(y)), max(4, int(wr * (0.35 + 0.65 * conv))), 2)
        for i in range(4):
            ang = i * math.pi / 2 + phase * 0.4
            _NS_gornak._chevron(
                surface,
                x + math.cos(ang) * wr * 0.82,
                y + math.sin(ang) * wr * 0.82,
                ang + math.pi, int(10 * fs), p["magic_hot"], a_main, width=2)

        # AKTIVASI: kubah heksagon memeluk badan + bintang
        rx = int(_NS_gornak._s(24) * grow * max(1.0, fs * 0.55))
        ry = int(_NS_gornak._s(33) * grow * max(1.0, fs * 0.55))
        cx0, cy0 = int(x), int(y) - 3
        breath = math.sin(phase * 2.4) * 1.2 * fs
        pts = []
        for i in range(6):
            ang = -math.pi / 2 + i * math.tau / 6 + phase * 0.25
            pts.append((cx0 + int(math.cos(ang) * (rx + breath)),
                        cy0 + int(math.sin(ang) * (ry + breath))))
        x0 = min(q[0] for q in pts) - 4
        y0 = min(q[1] for q in pts) - 4
        w = max(q[0] for q in pts) - x0 + 8
        h = max(q[1] for q in pts) - y0 + 8
        fill = pygame.Surface((max(4, w), max(4, h)), pygame.SRCALPHA)
        sh = [(q[0] - x0, q[1] - y0) for q in pts]
        _NS_gornak._poly(fill, (*p["magic_darkest"],
                                _NS_gornak._alpha(64 * grow)), sh)
        _NS_gornak._poly(fill, (*p["magic_dark"], _NS_gornak._alpha(72 * grow)),
                         sh[1:-1] + [sh[0]])
        surface.blit(fill, (x0, y0))
        for i in range(6):
            q, r2 = pts[i], pts[(i + 1) % 6]
            _NS_gornak._aaline(surface, (*p["magic_mid"], a_main), q, r2, 2)
            _NS_gornak._aaline(surface, (*p["magic_shine"], a_main), q, r2, 1)
            _NS_gornak._aacircle(surface, (*p["magic_hot"], a_main), q, 3)
            _NS_gornak._rect(surface, (*p["white"], a_main), (q[0], q[1], 1, 1))
        if progress < 0.20:
            _NS_gornak._spark_star(
                surface, x, y - 8, int(14 * fs * (1 - progress / 0.20)),
                p["magic_hot"], a_main, spikes=8, rot=progress * 5,
                core=p["white"])
        # STEADY: mote orbit di ring 100
        for i in range(8):
            ang = phase * 1.3 + i * math.tau / 8
            mx = x + math.cos(ang) * wr
            my = y + math.sin(ang) * wr
            _NS_gornak._aacircle(surface, (*p["magic_light"], a_main),
                                 (int(mx), int(my)), max(1, int(2 * fs)))
            _NS_gornak._rect(surface, (*p["magic_shine"], a_main),
                             (int(mx), int(my), 1, 1))

    # ==================================================================
    # SKILL R - MANA VOID (AOE 180 px dunia di CASTER)
    # Telegraph 180 + pilar + funnel. Drain mote dari target (opsional).
    # ==================================================================
    def _draw_manavoid_ground(surface, boss, x, y, timer, phase):
        p = _NS_gornak.PALETTE
        duration = _NS_gornak.SKILL_DUR["r"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        fs = _NS_gornak._fx_scale(boss)
        wr = _NS_gornak._ring_r(boss, 180)
        gy = y + _NS_gornak.GROUND_DY
        a = _NS_gornak._alpha(220 * min(1.0, progress * 3))
        # Telegraph ring TEPAT 180 px dunia di caster (gameplay AOE).
        # 3-komponen = tanpa alokasi temp raksasa.
        if a > 40:
            _NS_gornak._aacircle(surface, p["magic_light"],
                                 (int(x), int(y)), wr, max(3, int(2 * fs)))
        _NS_gornak._dashed_ring(
            surface, x, y, wr, p["magic_light"], a,
            phase * 0.9, segments=16, thick=max(2, int(2 * fs)),
            span=0.55, squash=1.0)
        _NS_gornak._ellipse(surface, (*p["magic_darkest"], a),
                            (x - wr, gy - wr // 4, wr * 2,
                             max(4, wr // 2)), 2)
        if progress < 0.55:
            t = progress / 0.55
            for i in range(8):
                ang = i * math.tau / 8 + 0.2
                _NS_gornak._jagged_crack(
                    surface, x, gy, ang, int(wr * 0.55 * t),
                    (p["magic_darkest"], p["magic_hot"]),
                    _NS_gornak._alpha(190 * t), i + 5, width=2)
            for i in range(4):
                ang = i * math.pi / 2 + phase * 0.3
                _NS_gornak._chevron(
                    surface,
                    x + math.cos(ang) * wr * 0.78,
                    y + math.sin(ang) * wr * 0.78,
                    ang + math.pi, int(12 * fs), p["magic_hot"],
                    _NS_gornak._alpha(210 * t), width=2)

    def _draw_manavoid_foreground(surface, boss, x, y, timer, phase):
        p = _NS_gornak.PALETTE
        duration = _NS_gornak.SKILL_DUR["r"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        fs = _NS_gornak._fx_scale(boss)
        action = "void"
        wr = _NS_gornak._ring_r(boss, 180)
        # Inti void di CASTER (gameplay: mana_void_x = self.x)
        cx, cy = int(x), int(y) - 4
        aim = _NS_gornak._target_position(boss, x, y)

        if progress < 0.22:
            # AKTIVASI: pilar 3 lapis (clamp tinggi) + shockwave + bintang
            t = progress / 0.22
            a = _NS_gornak._alpha(240 * (1 - t * 0.25))
            ph = min(int(100 * fs), 240)
            for col, w, mul in (("magic_darkest", 18, 1.0),
                                ("magic_mid", 10, 0.85),
                                ("magic_shine", 4, 0.55)):
                ww = max(2, int(w * fs * (1.1 - t * 0.3)))
                hh = int(ph * mul)
                _NS_gornak._ellipse(
                    surface, (*p[col], a),
                    (cx - ww, cy - hh, ww * 2, hh + 8))
            _NS_gornak._spark_star(
                surface, cx, cy - int(20 * fs), int(18 * fs * (1 - t)),
                p["magic_hot"], a, spikes=8, rot=t * 3, core=p["white"])
            rr = int(wr * (0.25 + t * 0.75))
            _NS_gornak._aacircle(surface, (*p["magic_mid"], a), (cx, cy), rr, 3)

        if progress < 0.50:
            t = progress / 0.5
            # Drain mote: target -> dada (arah "mencuri mana")
            chest = _NS_gornak._local(boss, x, y, action, phase, 0.0,
                                      0, _NS_gornak.SHOULDER_Y + 4)
            for back in (False, True):
                grip = (_NS_gornak._front_grip_local(action, 0.0, phase)
                        if not back else
                        _NS_gornak._back_grip_local(action, 0.0, phase))
                hx, hy = _NS_gornak._local(boss, x, y, action, phase, 0.0,
                                           *grip)
                _NS_gornak._aaline(surface,
                                   (*p["magic_dark"], _NS_gornak._alpha(150 * t)),
                                   (hx, hy), (cx, cy), max(2, int(3 * fs)))
                _NS_gornak._aaline(surface,
                                   (*p["magic_mid"], _NS_gornak._alpha(200 * t)),
                                   (hx, hy), (cx, cy), max(1, int(2 * fs)))
            for i in range(6):
                tt = (phase * 0.7 + i / 6.0) % 1.0
                mx = int(aim[0] + (chest[0] - aim[0]) * tt)
                my = int(aim[1] + (chest[1] - aim[1]) * tt
                         - math.sin(tt * math.pi) * 7 * fs)
                aa = _NS_gornak._alpha(210 * (1 - abs(tt - 0.5) * 1.2) * t)
                if aa > 0:
                    _NS_gornak._aacircle(surface, (*p["magic_light"], aa),
                                         (mx, my), max(1, int(2 * fs)))
                    _NS_gornak._rect(surface, (*p["magic_shine"], aa),
                                     (mx, my, 1, 1))
            core = int((6 + t * 8) * fs)
            for r in range(core + 2, 0, -1):
                aa = _NS_gornak._alpha(235 * (core + 2 - r) / (core + 2))
                _NS_gornak._aacircle(surface, (*p["magic_darkest"], aa),
                                     (cx, cy), r)
            _NS_gornak._aacircle(surface, p["magic_mid"], (cx, cy), core)
            _NS_gornak._aacircle(surface, p["magic_hot"], (cx, cy),
                                 max(1, core - 3))
        elif progress < 0.68:
            t = (progress - 0.50) / 0.18
            intensity = math.sin(t * math.pi)
            r = int((22 + t * 30) * fs)
            a = _NS_gornak._alpha(240 * intensity)
            _NS_gornak._aacircle(surface, (*p["magic_darkest"], a), (cx, cy),
                                 r + 3, 4)
            _NS_gornak._aacircle(surface, (*p["magic_dark"], a), (cx, cy), r, 3)
            _NS_gornak._aacircle(surface, (*p["magic_mid"], a), (cx, cy),
                                 max(1, r - 6), 2)
            _NS_gornak._aacircle(surface, (*p["magic_shine"], a), (cx, cy),
                                 max(1, int(r * 0.35)))
            _NS_gornak._spark_star(
                surface, cx, cy, int(20 * fs * intensity), p["magic_hot"], a,
                spikes=10, rot=t * 4, core=p["white"])
            for i in range(12):
                ang = i * math.tau / 12
                ex = cx + int(math.cos(ang) * min(wr, r + 8 * fs))
                ey = cy + int(math.sin(ang) * min(wr, r + 8 * fs) * 0.85)
                _NS_gornak._aaline(surface, (*p["magic_hot"], a), (cx, cy),
                                   (ex, ey), 2 if i % 3 == 0 else 1)
        else:
            t = (progress - 0.68) / 0.32
            for i in range(10):
                tt = (phase * 0.5 + i * 0.1) % 1.0
                px = cx + int(math.sin(phase * 1.4 + i) * (14 + i) * fs)
                py = cy - int(tt * 30 * fs)
                a = _NS_gornak._alpha(200 * (1 - t) * (1 - tt))
                if a > 0:
                    _NS_gornak._aacircle(surface, (*p["magic_dark"], a),
                                         (px, py), max(1, int(3 * fs)))
                    _NS_gornak._aacircle(surface, (*p["magic_mid"], a),
                                         (px, py), max(1, int(2 * fs)))
                    _NS_gornak._rect(surface, (*p["magic_shine"], a),
                                     (px, py, 1, 1))
        # Rim violet di badan (badan tetap subjek)
        rim = _NS_gornak._alpha(110 * min(1.0, progress * 3))
        rw, rh = int(_NS_gornak._s(15) * max(1.0, fs * 0.5)), \
            int(_NS_gornak._s(21) * max(1.0, fs * 0.5))
        _NS_gornak._ellipse(surface, (*p["magic_light"], rim),
                            (int(x) - rw, int(y) - rh - _NS_gornak.LIFT,
                             rw * 2, rh * 2 + _NS_gornak._s(2)), 1)


# ====================================================================
# MORGATH (ARC WARDEN) - Mini Boss
# ====================================================================
import math
import pygame


class _NS_morgath:
    """Namespace morgath - Arc Warden mini boss (ranged lightning caster).

    PIXEL MASTERWORK V2 + SKILL FX V2.1 (standar Thorne v2 / Gornak v2):

    * SATU bone rig 2D berlapis, ~1.5x di resolusi native. Ukuran arena
      otomatis ternormalisasi pipeline hero (heroes/__init__.py) - yang
      naik adalah KEPADATAN detail, bukan ukuran layar. Jalur mini boss
      (tanpa _render_scale) di-fit ke paritas keluarga lewat BOSS_FIT
      supaya hierarki boss (abaddon > gornak > morgath) tetap terkunci.
    * Disiplin pixel-art: ramp 4-5 band hue-shift, selout sisi bayangan,
      siluet bergerigi (hem cape/skirt via _tuft_points), specular
      cluster 1-2 px, dither band 50%, key light kiri-atas.
    * Anatomi baru: hood berlipat + orb kristal 5-band + shard orbit +
      antena arc; cuirass + pauldron rivet + gorget; grimoire di sabuk;
      SENJATA KHAS: arc staff "Tempus" tertanam (finial kristal melayang).
    * Animasi: foot solver, cape/staff/tassel inertia, idle hidup,
      serang multi-keyframe dengan frame IMPACT + smear berlapis.
    * Skill Q/W/E/R world-space lewat _fx_scale (1/_render_scale, cap
      2.6): 3 fase (telegraph / aktivasi / steady), E = 90 px dunia,
      R clone = +/-60 px dunia, W pool di target, Q jalur ke target.
    * Aura/mist/bayangan/dome di-cache (_static); FX di-clamp ke canvas.
    """

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    _STATIC_SURFACES = {}

    # ── SKALA BADAN ───────────────────────────────────────────────
    # Koordinat lokal x1.5 dari rig lama. SCALE = px native per unit
    # lokal; SATU skala untuk semua jalur (boss 1x, lane hero native,
    # portrait) - sama seperti Thorne/Gornak v2. heroes/__init__.py
    # mengukur jalur boss lalu menormalkan lane, jadi yang dikunci di
    # sini adalah UKURAN ARENA: badan padat ~103 px, di bawah gornak
    # 119 (kontrak keluarga gornak >= 1.05x morgath) dan jauh di atas
    # rig v1 (~55 px).
    SCALE = 0.74
    K_BOSS = 0.74     # kompatibilitas nama: jalur boss = skala penuh
    # LIFT = jarak dunia (px) jangkar -> badan ke bawah, supaya
    # wajah (orb) tidak tertutup HP bar boss (y-r-15..y-r-7).
    LIFT = 4
    # Hem jubah dalam RUANG LOKAL; garis tanah dunia diturunkan dari
    # sini supaya bayangan/rune/hem tidak pernah saling lepas.
    FEET_DY = 60
    GROUND_DY = int(round(FEET_DY * K_BOSS)) - LIFT        # = 42

    # Buffer rig native (dibatasi extents semua pose + margin 4 px;
    # dikunci tools/test_morgath_masterwork.py + audit).
    RIG_W, RIG_H = 154, 117
    RIG_OX, RIG_OY = 77, 68

    # Bidang acuan cahaya TETAP (arah lampu tidak boleh bergeser antar
    # pose = lampu berkedip; kotak tetap juga menjaga cache gradien).
    GRAD_BOX = (RIG_OX - 30, RIG_OY - 47, 62, 90)

    # Durasi visual skill (frame) - mengikuti active_skill_timer yang
    # diisi base_boss.py & hero_skills/_bundle.py (q=50 w=40 e=90 r=60).
    SKILL_DUR = {"q": 50, "w": 40, "e": 90, "r": 60}

    # Sendi dalam RUANG LOKAL (y=0 jangkar, + ke bawah).
    WAIST_Y = -12
    SHOULDER_Y = -33
    SHOULDER_FRONT = (15, SHOULDER_Y)
    SHOULDER_BACK = (-16.5, SHOULDER_Y - 1.5)
    ORB_CENTER = (3, -46.5)
    ORB_R = 13.5
    CROWN_Y = -66

    # Muzzle beam = telapak cast di puncak thrust (beam lahir dari
    # TELAPAK, bukan angka lepas - dikunci test).
    MOR_MUZZLE = (40.5, -22.5)

    # Titik tancap arc staff (kaki staff menapak di tanah).
    STAFF_BASE = (-22, 60)

    # Penanda "render ke canvas hero" (lane) + skala aktif + skill
    # aktif. Dipasang per-frame oleh draw_morgath.
    class _MOR_LANE:
        v = False

    class _MOR_K:
        v = 0.74          # = SCALE: satu skala untuk semua jalur

    class _MOR_SKILL:
        v = None

    PALETTE = {
        # Robe / cloak (dark purple, hue-shift ke biru-violet di bayangan)
        "robe_darkest": (10, 6, 22),
        "robe_dark": (28, 18, 50),
        "robe_mid": (56, 38, 94),
        "robe_light": (98, 70, 150),
        "robe_edge": (152, 112, 204),

        # Armor plating (dark blue-steel, highlight dingin)
        "armor_darkest": (7, 11, 24),
        "armor_dark": (24, 38, 62),
        "armor_mid": (54, 82, 116),
        "armor_light": (106, 144, 184),
        "armor_shine": (178, 208, 238),

        # Gold trim (hue-shift: bayangan cokelat, highlight hangat)
        "gold_dark": (72, 52, 18),
        "gold_mid": (158, 122, 52),
        "gold_light": (228, 192, 108),
        "gold_shine": (255, 234, 168),

        # Crystal orb (bright cyan-blue, material utama sihir)
        "orb_darkest": (4, 14, 38),
        "orb_dark": (18, 52, 124),
        "orb_mid": (58, 126, 214),
        "orb_light": (128, 196, 250),
        "orb_hot": (198, 232, 254),
        "orb_shine": (240, 250, 255),

        # Lightning/arc (electric blue-white)
        "arc_darkest": (13, 27, 74),
        "arc_dark": (38, 86, 184),
        "arc_mid": (88, 156, 236),
        "arc_light": (176, 216, 252),
        "arc_hot": (228, 244, 255),
        "arc_shine": (255, 255, 255),

        # Flux purple (accent W)
        "flux_darkest": (24, 7, 44),
        "flux_dark": (62, 24, 106),
        "flux_mid": (128, 58, 196),
        "flux_light": (188, 128, 238),
        "flux_hot": (224, 178, 255),

        # Skin (hands/face edges) - shadowed violet
        "skin_darkest": (32, 27, 50),
        "skin_dark": (72, 62, 96),
        "skin_mid": (126, 112, 156),
        "skin_light": (176, 162, 206),

        # Arc staff (dark wood + steel + crystal finial)
        "staff_dark": (34, 24, 44),
        "staff_mid": (72, 52, 86),
        "staff_light": (122, 96, 150),

        # Grimoire / leather
        "leather_dark": (40, 26, 34),
        "leather_mid": (84, 56, 66),
        "leather_light": (136, 100, 110),
        "page_light": (214, 200, 186),

        # Ground rune
        "rune_dark": (13, 23, 56),
        "rune_mid": (56, 104, 194),
        "rune_light": (146, 196, 252),

        "shadow": (0, 0, 0),
        "shadow_deep": (3, 2, 8),
        "white": (255, 255, 255),
    }

    # ================================================================
    # PRIMITIF HELPER (alpha aman lewat surface sementara)
    # ================================================================
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _mix(a, b, t):
        t = max(0.0, min(1.0, float(t)))
        return _NS_morgath._clamp((
            a[0] + (b[0] - a[0]) * t,
            a[1] + (b[1] - a[1]) * t,
            a[2] + (b[2] - a[2]) * t))

    def _hash01(seed):
        """Pseudo-random deterministik 0..1 (aman untuk cache sprite)."""
        h = int(seed) * 2654435761 & 0xFFFFFFFF
        h ^= h >> 16
        return (h & 0xFFFF) / 65535.0

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_morgath._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius <= 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4),
                                  pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2),
                               radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_morgath.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy),
                                     radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_morgath._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        width = max(1, int(width))
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width - 2
            min_y = min(sy, ey) - width - 2
            w = abs(ex - sx) + width * 4 + 6
            h = abs(ey - sy) + width * 4 + 6
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.line(temp, color,
                             (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), width)
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), width)

    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_morgath._clamp(color)
        if len(color) == 4 and color[3] < 255:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, min_y = min(xs) - 2, min(ys) - 2
            w = max(xs) - min_x + 4
            h = max(ys) - min_y + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            shifted = [(p[0] - min_x, p[1] - min_y) for p in points]
            pygame.draw.polygon(temp, color, shifted)
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.polygon(surface, color[:3], points)

    def _ellipse(surface, color, rect, width=0):
        color = _NS_morgath._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, rw, rh), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3], rect, width)

    def _rect(surface, color, rect):
        color = _NS_morgath._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, rw, rh))
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3], rect)

    def _static(key, builder):
        """Ambil/bangun surface statis (alokasi hanya saat cache miss)."""
        surf = _NS_morgath._STATIC_SURFACES.get(key)
        if surf is None:
            surf = builder()
            _NS_morgath._STATIC_SURFACES[key] = surf
        return surf

    def _dither_rows(surface, x0, x1, y0, rows, color, w=1, seed=0):
        """Pita dither 50%: baris titik selang-seling (klasik pixel-art)."""
        for r in range(rows):
            y = int(y0) + r
            for x in range(int(x0) + ((r + seed) % 2), int(x1), 2):
                _NS_morgath._rect(surface, color, (x, y, w, w))

    def _jagged_line(surface, color, start, end, jitter=4, segments=6,
                     width=2):
        """Garis petir zigzag deterministik (nama publik lama)."""
        color = _NS_morgath._clamp(color)
        prev = start
        for i in range(1, segments + 1):
            t = i / segments
            bx = int(start[0] + (end[0] - start[0]) * t)
            by = int(start[1] + (end[1] - start[1]) * t)
            if i < segments:
                dx = end[0] - start[0]
                dy = end[1] - start[1]
                length = max(1.0, math.hypot(dx, dy))
                perp_x = -dy / length
                perp_y = dx / length
                jit = (math.sin(t * 12 + start[0]) - 0.5) * jitter * 2
                bx += int(perp_x * jit)
                by += int(perp_y * jit)
            pygame.draw.line(surface, color, prev, (bx, by), width)
            prev = (bx, by)

    # ------------------------------------------------------------------
    # FX helper primitives (standar Thorne v2.1 / Gornak v2)
    # ------------------------------------------------------------------
    def _fx_scale(boss):
        """Kompensasi efek world-space: 1/_render_scale, cap 2.6."""
        scale = getattr(boss, "_render_scale", None)
        if not scale:
            return 1.0
        return max(1.0, min(2.6, 1.0 / float(scale)))

    def _ring_r(boss, world_px, surface):
        """Radius dunia (px) -> px canvas, di-clamp ke dalam cache."""
        scale = getattr(boss, "_render_scale", None)
        r = float(world_px) / float(scale) if scale else float(world_px)
        margin = min(surface.get_width(), surface.get_height()) // 2 - 10
        return int(max(4, min(r, margin)))

    def _world_to_local(boss, x, y, wx, wy):
        """Titik DUNIA -> ruang gambar renderer (clamp ke canvas).

        Hero dirender ke canvas di pusat lalu di-scale _render_scale:
        1 px canvas = _render_scale px dunia. Boss asli (tanpa
        _render_scale) digambar langsung di dunia -> titik apa adanya.
        """
        scale = getattr(boss, "_render_scale", None)
        if scale is None:
            return int(wx), int(wy)
        scale = float(scale) or 1.0
        ox = (float(wx) - float(getattr(boss, "x", x))) / scale
        oy = (float(wy) - float(getattr(boss, "y", y))) / scale
        rng = int(getattr(boss, "range", 130) or 130)
        half = max(120, int(rng / scale) + 40)
        max_off = half - 20
        d = math.hypot(ox, oy)
        if d > max_off:
            ox *= max_off / d
            oy *= max_off / d
        return int(x + ox), int(y + oy)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return _NS_morgath._world_to_local(boss, x, y,
                                               target.x, target.y)
        scale = getattr(boss, "_render_scale", None)
        if scale:
            rng = int(getattr(boss, "range", 130) or 130)
            half = max(120, int(rng / float(scale)) + 40)
            dist = min(250 / float(scale), half - 20)
        else:
            dist = 250
        return int(x + dist * getattr(boss, "direction", 1)), int(y)

    def _spark_star(surface, cx, cy, size, color, alpha, spikes=6,
                    rot=0.4, core=None):
        """Bintang spike selang-seling untuk impact/aktivasi."""
        if alpha <= 0 or size <= 0:
            return
        alpha = max(0, min(255, int(alpha)))
        for k in range(spikes):
            ang = rot + k * math.tau / spikes
            ln = size * (1.0 if k % 2 == 0 else 0.55)
            _NS_morgath._aaline(surface, (*color, alpha),
                                (int(cx), int(cy)),
                                (int(cx + math.cos(ang) * ln),
                                 int(cy + math.sin(ang) * ln * .82)),
                                2 if k % 2 == 0 else 1)
        if core:
            _NS_morgath._aacircle(surface, (*core, alpha),
                                  (int(cx), int(cy)),
                                  max(1, int(size * .28)))

    def _chevron(surface, cx, cy, ang, size, color, alpha, width=3):
        """Panah telegraph '>' menghadap arah ``ang``."""
        if alpha <= 0 or size <= 0:
            return
        ca, sa = math.cos(ang), math.sin(ang)
        px_, py_ = -sa, ca
        tipx, tipy = cx + ca * size, cy + sa * size
        for side in (-1, 1):
            _NS_morgath._aaline(
                surface, (*color, max(0, min(255, int(alpha)))),
                (int(cx + px_ * side * size * .55 - ca * size * .5),
                 int(cy + py_ * side * size * .55 - sa * size * .5)),
                (int(tipx), int(tipy)), width)

    def _dashed_ring(surface, cx, cy, radius, color, alpha, phase,
                     segments=10, thick=3, span=0.6, squash=.92):
        """Cincin rune putus-putus yang berputar (marker AOE)."""
        if alpha <= 0 or radius <= 1:
            return
        alpha = max(0, min(255, int(alpha)))
        for i in range(segments):
            a0 = phase + i * math.tau / segments
            a1 = a0 + math.tau / segments * span
            p0 = (cx + math.cos(a0) * radius,
                  cy + math.sin(a0) * radius * squash)
            p1 = (cx + math.cos(a1) * radius,
                  cy + math.sin(a1) * radius * squash)
            _NS_morgath._aaline(surface, (*color, alpha), p0, p1, thick)

    def _jagged_crack(surface, cx, cy, ang, length, colors, alpha, seed,
                      width=3):
        """Retakan tanah zigzag deterministik dengan seam menyala."""
        if alpha <= 0 or length <= 0:
            return
        x0, y0, a = float(cx), float(cy), float(ang)
        pts = [(x0, y0)]
        for i in range(4):
            a += (_NS_morgath._hash01(seed * 17 + i * 31) - .5) * .75
            seg = length / 4.0
            x0 += math.cos(a) * seg
            y0 += math.sin(a) * seg * .55
            pts.append((x0, y0))
        alpha = max(0, min(255, int(alpha)))
        for i in range(len(pts) - 1):
            _NS_morgath._aaline(surface, (*colors[0], alpha),
                                pts[i], pts[i + 1], width + 2)
            _NS_morgath._aaline(surface, (*colors[1], alpha),
                                pts[i], pts[i + 1], width)

    def _tuft_points(spine, depth=4.0, min_len=7.0, seed=0):
        """Ubah spine halus menjadi siluet bergerigi deterministik."""
        out = [spine[0]]
        for i in range(len(spine) - 1):
            ax, ay = spine[i]
            bx, by = spine[i + 1]
            seg = math.hypot(bx - ax, by - ay)
            n = max(1, int(seg / max(1.0, min_len)))
            nx_, ny_ = (by - ay), -(bx - ax)
            ln = math.hypot(nx_, ny_) or 1.0
            nx_, ny_ = nx_ / ln, ny_ / ln
            for j in range(n):
                t = (j + 0.5) / n
                px_, py_ = ax + (bx - ax) * t, ay + (by - ay) * t
                d = depth * (0.55 + 0.45 *
                             _NS_morgath._hash01(seed + i * 31 + j * 7))
                out.append((px_ + nx_ * d, py_ + ny_ * d))
            out.append((bx, by))
        return out



    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_morgath(surface, boss, x, y):
        """Entry point untuk Boss.draw() sekaligus heroes.render_hero()."""
        # Beam-only pass (hero): body sudah di-blit ter-scale oleh
        # heroes/__init__.py; di sini hanya beam yang digambar, pada
        # koordinat & skala dunia = identik dengan versi mini boss.
        if getattr(boss, "_beam_pass_only", False):
            _NS_morgath._draw_mor_beam_pass(surface, boss, x, y)
            return

        # Jalur hero (lane): heroes/__init__ men-set _render_scale, dan
        # _finish_hd_sprite sudah menambah rim/terminator -> pass cahaya
        # di _draw_mor_rig_at dilewati (supaya tidak dobel).
        _NS_morgath._MOR_LANE.v = hasattr(boss, "_render_scale")
        _NS_morgath._MOR_K.v = _NS_morgath.SCALE
        _NS_morgath._MOR_SKILL.v = getattr(boss, "active_skill", None)
        _NS_morgath._update_mor_attack_anim(boss)
        action, pulse, ap = _NS_morgath._resolve_mor_pose(
            boss, _NS_morgath._detect_moving(boss))
        boss._mor_pose_action = action
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        portrait = bool(getattr(boss, "_portrait_hd", False))
        facing = getattr(boss, "direction", 1) or 1
        flash = _NS_morgath._alpha(170 * (getattr(boss, "hurt_flash_timer", 0)
                                          / 8.0))

        # ── Latar. Dibuang total saat portrait supaya auto-crop Hero
        #    Shop terisi wajah & material (orb), bukan lingkaran efek.
        if not portrait:
            _NS_morgath._draw_arc_aura(surface, x, y, pulse)
            gy = _NS_morgath._ground_dy()
            _NS_morgath._draw_ground_rune(surface, x, y + gy,
                                          pulse, active_skill)
            if active_skill == "q":
                _NS_morgath._draw_sparkwraith_ground(surface, boss, x, y,
                                                     skill_timer, pulse)
            elif active_skill == "w":
                _NS_morgath._draw_flux_ground(surface, boss, x, y,
                                              skill_timer, pulse)
            elif active_skill == "e":
                _NS_morgath._draw_magneticfield_ground(surface, boss, x, y,
                                                       skill_timer, pulse)
            elif active_skill == "r":
                _NS_morgath._draw_tempest_ground(surface, boss, x, y,
                                                 skill_timer, pulse)
            # AKTIVASI: gelombang kejut + bintang saat skill dilepas
            _NS_morgath._draw_skill_activation(surface, boss, x, y,
                                               active_skill, skill_timer,
                                               pulse)

        # ── Karakter (SATU rig masterwork; hem dipatok di garis tanah)
        if not portrait:
            _NS_morgath._draw_shadow(surface, x, y + _NS_morgath._ground_dy())
        _NS_morgath._draw_mor_rig_at(surface, x, y, facing, pulse, action,
                                     ap, portrait, flash)

        # Beam petir lahir dari telapak cast (MOR_MUZZLE). Skip saat beam
        # digambar terpisah langsung di layar skala 1.0 (heroes/__init__).
        if action == "attack" and not getattr(boss, "_skip_beam", False):
            _NS_morgath._draw_lightning_projectile(
                surface, boss, x, y, _NS_morgath._mor_progress(boss))

        # Tempest Double clones
        if active_skill == "r":
            _NS_morgath._draw_tempest_clone(surface, boss, x, y,
                                            skill_timer, pulse)

        # Foreground FX
        if active_skill == "q":
            _NS_morgath._draw_sparkwraith_foreground(surface, boss, x, y,
                                                     skill_timer, pulse)
        elif active_skill == "w":
            _NS_morgath._draw_flux_foreground(surface, boss, x, y,
                                              skill_timer, pulse)
        elif active_skill == "e":
            _NS_morgath._draw_magneticfield_foreground(surface, boss, x, y,
                                                       skill_timer, pulse)
        elif active_skill == "r":
            _NS_morgath._draw_tempest_foreground(surface, boss, x, y,
                                                 skill_timer, pulse)

    def _ground_dy():
        """Offset garis tanah pada ruang gambar aktif (canvas/world)."""
        k = _NS_morgath._MOR_K.v
        return int(round(_NS_morgath.FEET_DY * k
                         - _NS_morgath.LIFT * k / _NS_morgath.K_BOSS))

    def _lift_now():
        return _NS_morgath.LIFT * _NS_morgath._MOR_K.v / _NS_morgath.K_BOSS

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_mor_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_mor_previous_timer", 0))
        active = bool(getattr(boss, "_mor_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._mor_attack_active = True
            boss._mor_attack_frame = 0
            # Kunci arah + posisi target saat serangan dimulai (beam
            # terbang lurus ke titik yang SAMA selama animasi).
            boss._mor_attack_dir = int(getattr(boss, "direction", 1))
            _t = getattr(boss, "target", None)
            if _t is not None and getattr(_t, "alive", True):
                boss._mor_attack_target = (
                    int(_t.x) - int(getattr(boss, "x", 0)),
                    int(_t.y) - int(getattr(boss, "y", 0)))
            else:
                tx, ty = _NS_morgath._target_position(
                    boss, getattr(boss, "x", 0), getattr(boss, "y", 0))
                boss._mor_attack_target = (
                    int(tx) - int(getattr(boss, "x", 0)),
                    int(ty) - int(getattr(boss, "y", 0)))
            active = True
        elif active and timer > 0:
            boss._mor_attack_frame = int(getattr(boss, "_mor_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._mor_attack_active = False
            boss._mor_attack_frame = 0
            active = False

        boss._mor_previous_timer = timer
        boss._mor_attack_progress = (
            min(1.0, getattr(boss, "_mor_attack_frame", 0)
                / max(1, cooldown - 1)) if active else 0.0)

    def _detect_moving(boss):
        if not hasattr(boss, "_mor_last_x"):
            boss._mor_last_x = boss.x
            boss._mor_last_y = boss.y
            return False
        dx = abs(boss.x - boss._mor_last_x)
        dy = abs(boss.y - boss._mor_last_y)
        boss._mor_last_x = boss.x
        boss._mor_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _mor_progress(boss):
        # LIVE dari attack_timer (bukan counter frame yang cuma naik
        # saat renderer dipanggil) - beam live tetap mulus 60fps.
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_mor_attack_active", False):
            return max(0.0, min(1.0, (cd - 1 - t)
                                  / max(1.0, float(cd - 1))))
        return 0.0

    def _mor_attack_curve(ap):
        """Progres mentah 0..1 -> waktu pose 0..1, MONOTON naik.

        Sama seperti kurva Gornak: anticipation jelas, HOLD di impact,
        follow-through yang tidak ditarik balik. 0.35 = puncak charge,
        0.55 = beam mulai mengalir (pose 0.77, telapak sudah di muzzle).
        """
        if ap <= 0.0:
            return 0.0
        if ap < 0.45:                       # charge: tarik bahu, diperlambat
            t = ap / 0.45
            return 0.35 * (t ** 0.7)
        if ap < 0.62:                       # thrust: sangat cepat
            t = (ap - 0.45) / 0.17
            return 0.35 + 0.55 * (t ** 0.5)
        if ap < 0.80:                       # IMPACT HOLD (nyaris beku)
            t = (ap - 0.62) / 0.18
            return 0.90 + 0.06 * t
        t = (ap - 0.80) / 0.20              # release -> siap
        return 0.96 + 0.04 * (t ** 0.8)

    def _attack_pose(ap):
        """Interpolasi keyframe serang -> dict pose.

        Keyframe: (progress, bob, lean, hand_x, hand_y, flare, tremble)
          0.00  rest      : tangan di sisi badan
          0.14  wind-up   : badan turun, tangan tarik belakang
          0.35  tension   : gemetar 1 px, node telapak charge penuh
          0.62  thrust    : tangan terdorong tercepat (smear aktif)
          0.90  IMPACT    : HOLD di muzzle (burst bintang di FX)
          0.96  release   : follow-through
          1.00  recover   : kembali istirahat
        """
        keys = (
            (0.00, 0, 0.0, 22.5, -10.5, 1.00, 0),
            (0.14, 3, -3.0, 16.5, -16.5, 1.00, 0),
            (0.35, 4, -4.5, 10.5, -19.5, 1.15, 1),
            (0.62, -1, 2.5, 34.5, -21.0, 1.25, 0),
            (0.90, 2, 4.5, 40.5, -22.5, 1.30, 0),
            (0.96, 1, 2.0, 40.5, -22.5, 1.15, 0),
            (1.00, 0, 0.0, 22.5, -10.5, 1.00, 0),
        )
        ap = max(0.0, min(1.0, ap))
        for i in range(len(keys) - 1):
            k0, k1 = keys[i], keys[i + 1]
            if k0[0] <= ap <= k1[0]:
                span = max(1e-6, k1[0] - k0[0])
                t = (ap - k0[0]) / span
                t = t * t * (3 - 2 * t)          # smoothstep
                vals = tuple(a + (b - a) * t
                             for a, b in zip(k0[1:6], k1[1:6]))
                flare = k0[5] + (k1[5] - k0[5]) * t
                tremble = 1 if (k0[6] and t < 0.9) else 0
                return {"bob": int(round(vals[0])), "lean": vals[1],
                        "hand": (vals[2], vals[3]),
                        "flare": flare, "tremble": tremble}
        return {"bob": 0, "lean": 0.0, "hand": (22.5, -10.5),
                "flare": 1.0, "tremble": 0}

    def _resolve_mor_pose(boss, moving=False):
        """(action, phase, ap) - dipakai rig DAN jangkar FX agar sinkron."""
        skill = getattr(boss, "active_skill", None)
        if skill == "q":
            action = "point"
        elif skill == "w":
            action = "channel"
        elif skill == "e":
            action = "erect"
        elif skill == "r":
            action = "ascend"
        elif (getattr(boss, "_mor_attack_active", False)
              or getattr(boss, "timer", 0) >
              getattr(boss, "attack_cooldown", 40) - 15):
            action = "attack"
        elif moving:
            action = "walk"
        else:
            action = "idle"

        phase = float(getattr(boss, "pulse", 0.0))
        if action == "walk":
            phase *= 2.0
        ap = 0.0
        if action == "attack":
            ap = _NS_morgath._mor_attack_curve(_NS_morgath._mor_progress(boss))
        return action, phase, ap

    def _cast_hand_local(action, ap, phase):
        """Telapak tangan depan (pe cast) dalam ruang lokal."""
        if action == "attack":
            pose = _NS_morgath._attack_pose(ap)
            return pose["hand"]
        bob = math.sin(phase * 0.9)
        if action == "point":                    # Q: menunjuk, summon wraith
            return (33.0, -39.0 + bob)
        if action == "channel":                  # W: kedua tangan menyalurkan
            return (22.5, -4.5 + bob)
        if action == "erect":                    # E: merentang mendirikan field
            return (30.0, 1.5)
        if action == "ascend":                   # R: mengangkat memanggil double
            return (16.5, -48.0)
        if action == "walk":
            return (19.5 + math.sin(phase * 2.0) * 3.0, -10.5)
        return (22.5, -10.5 + bob)               # idle: tangan di sisi badan

    def _back_hand_local(action, ap, phase):
        bob = math.sin(phase * 0.9 + 0.6)
        if action == "attack":
            return (-25.5, -4.5)
        if action == "channel":
            return (-22.5, -4.5 + bob)
        if action == "erect":
            return (-30.0, 1.5)
        if action == "ascend":
            return (-18.0, -46.5)
        if action == "walk":
            return (-19.5 - math.sin(phase * 2.0) * 3.0, -7.5)
        return (-22.5, -7.5 + bob)

    def _mor_elbow(a, b, bend):
        """Sendi siku: titik tengah digeser tegak-lurus sepanjang `bend`."""
        mx, my = (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = max(1.0, math.hypot(dx, dy))
        return (mx - dy / length * bend, my + dx / length * bend)

    def _mor_shift(action, phase, ap):
        """(lean_x, root_y) - lean geser badan atas; root = napas pada
        bagian ATAS hem (hem/telapak tetap dipatok di garis tanah)."""
        bob = math.sin(phase * 0.9) * 2.0
        lean, root = 0.0, bob
        if action == "walk":
            root = -abs(math.sin(phase * 2.0)) * 2.4
            lean = math.sin(phase) * 1.2
        elif action == "attack":
            pose = _NS_morgath._attack_pose(ap)
            lean, root = pose["lean"], 0.0
        elif action == "ascend":
            root = -4.5 - bob
        return lean, root

    def _muzzle_offset_world():
        """(dx, dy) dunia dari jangkar ke muzzle (facing=+1).
        Beam selalu digambar di ruang dunia (skala 1.0)."""
        k = _NS_morgath.K_BOSS
        return (int(round(_NS_morgath.MOR_MUZZLE[0] * k)),
                int(round(-_NS_morgath.LIFT
                          + _NS_morgath.MOR_MUZZLE[1] * k)))

    def _skill_hand_world(boss, x, y, skill):
        """Posisi telapak cast DUNIA untuk stance skill (nama publik
        lama dipertahankan - FX canvas pakai _skill_hand_canvas)."""
        action = {"q": "point", "w": "channel", "e": "erect",
                  "r": "ascend"}.get(skill, "idle")
        phase = float(getattr(boss, "pulse", 0.0))
        hx, hy = _NS_morgath._cast_hand_local(action, 0.0, phase)
        f = getattr(boss, "direction", 1) or 1
        k = _NS_morgath.K_BOSS
        return (int(x + hx * f * k),
                int(y - _NS_morgath.LIFT + hy * k))

    def _skill_hand_canvas(boss, x, y, skill):
        """Posisi telapak cast pada ruang gambar aktif (canvas/world)."""
        action = {"q": "point", "w": "channel", "e": "erect",
                  "r": "ascend"}.get(skill, "idle")
        phase = float(getattr(boss, "pulse", 0.0))
        hx, hy = _NS_morgath._cast_hand_local(action, 0.0, phase)
        f = getattr(boss, "direction", 1) or 1
        k = _NS_morgath._MOR_K.v
        return (int(x + hx * f * k),
                int(y - _NS_morgath._lift_now() + hy * k))

    # ------------------------------------------------------------
    # POSE ROUTERS (wrapper tipis, kompatibel tool preview lama)
    # ------------------------------------------------------------
    def _draw_mor_idle(surface, boss, x, y):
        _NS_morgath._draw_mor_rig_at(
            surface, x, y, getattr(boss, "direction", 1) or 1,
            float(getattr(boss, "pulse", 0.0)), "idle", 0.0, False)

    def _draw_mor_walk(surface, boss, x, y):
        _NS_morgath._draw_mor_rig_at(
            surface, x, y, getattr(boss, "direction", 1) or 1,
            float(getattr(boss, "pulse", 0.0)) * 2.0, "walk", 0.0, False)

    def _draw_mor_attack(surface, boss, x, y):
        progress = _NS_morgath._mor_progress(boss)
        _NS_morgath._draw_mor_rig_at(
            surface, x, y, getattr(boss, "direction", 1) or 1,
            float(getattr(boss, "pulse", 0.0)), "attack",
            _NS_morgath._mor_attack_curve(progress), False)
        if not getattr(boss, "_skip_beam", False):
            _NS_morgath._draw_lightning_projectile(surface, boss, x, y,
                                                    progress)

    def _draw_mor_beam_pass(surface, boss, x, y):
        """Gambar HANYA beam pada koordinat dunia (skala 1.0)."""
        _NS_morgath._update_mor_attack_anim(boss)
        _NS_morgath._draw_lightning_projectile(
            surface, boss, x, y, _NS_morgath._mor_progress(boss))



    # ============================================================
    # RIG RENDER
    # ============================================================
    def _rig_buffer(facing, phase, action, ap=0.0, detail=False):
        """Buffer rig pada skala aktif (native/hero atau BOSS_FIT)."
        Dipakai _draw_mor_rig_at DAN _draw_tempest_clone."""
        k = _NS_morgath._MOR_K.v
        bw = max(2, int(round(_NS_morgath.RIG_W * k / _NS_morgath.SCALE)))
        bh = max(2, int(round(_NS_morgath.RIG_H * k / _NS_morgath.SCALE)))
        box = (int(round(_NS_morgath.RIG_OX * k / _NS_morgath.SCALE)),
               int(round(_NS_morgath.RIG_OY * k / _NS_morgath.SCALE)))
        buf = pygame.Surface((bw, bh), pygame.SRCALPHA)
        _NS_morgath._draw_mor_rig(buf, box[0], box[1], facing, phase,
                                  action, ap, detail)
        return buf, box

    def _draw_mor_rig_at(surface, x, y, facing, phase, action, ap, detail,
                         flash=0):
        """Rig -> buffer -> outline gelap 1 px -> satu blit (pola Gornak).

        Buffer ukurannya mengikuti skala aktif: native (hero/portrait)
        atau BOSS_FIT (mini boss 1x) - outline selalu tajam 1 px.
        Mode portrait Hero Shop memusatkan konten pada bbox-nya sendiri.
        """
        k = _NS_morgath._MOR_K.v
        buf, box = _NS_morgath._rig_buffer(facing, phase, action, ap,
                                           detail)
        if flash > 0:
            lit = buf.copy()
            lit.fill((255, 240, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
            lit.set_alpha(flash)
            buf.blit(lit, (0, 0))
        # Pass cahaya hanya kalau sprite ini TIDAK dilewatkan ke
        # heroes._finish_hd_sprite (jalur lane sudah memberi
        # rim+terminator - dipasang dua kali jadi dobel).
        if _lighting is not None and not _NS_morgath._MOR_LANE.v:
            gb = tuple(int(round(v * k / _NS_morgath.SCALE))
                       for v in _NS_morgath.GRAD_BOX)
            _lighting.apply_to_rig(
                buf, rim_add=(30, 34, 52), shade_mul=160,
                box=gb if not detail else None)
        ox = int(x) - box[0]
        oy = int(y) - box[1]
        if detail:                       # portrait: pusatkan konten
            used = buf.get_bounding_rect(min_alpha=1)
            if used.width > 0:
                ox = int(x) - (used.left + used.width // 2)
                oy = int(y) - (used.top + used.height // 2)
        # Outline siluet (4 arah) - acuan keluarga masterwork.
        edge = buf.copy()
        edge.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        for ddx, ddy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            surface.blit(edge, (ox + ddx, oy + ddy))
        surface.blit(buf, (ox, oy))
        return buf

    def _draw_mor_rig(surface, cx, cy, facing, phase, action, ap=0.0,
                      detail=False):
        """Satu bone rig 2D berlapis: cape -> staff -> lengan belakang ->
        boots -> rok jubah -> torso -> sabuk+grimoire -> pauldron
        belakang -> kepala -> lengan cast -> pauldron depan -> FX.
        Semua titik lewat pt()/ptg() supaya ukuran cukup diubah dari
        SATU konstanta SCALE (atau K_BOSS di jalur mini boss)."""
        P = _NS_morgath.PALETTE
        k = _NS_morgath._MOR_K.v
        f = 1 if facing >= 0 else -1
        lean, root = _NS_morgath._mor_shift(action, phase, ap)
        lift = _NS_morgath._lift_now()
        tremble = 0.0
        if action == "attack":
            pose = _NS_morgath._attack_pose(ap)
            if pose["tremble"]:
                tremble = (_NS_morgath._hash01(int(phase * 13.7) % 1024)
                           - 0.5) * 1.2

        def pt(dx, dy):
            """Bagian yang ikut napas/lean/tremble (badan atas)."""
            return (int(cx + (dx * f + (lean + tremble) * f) * k),
                    int(cy - lift + (dy + root) * k))

        def ptg(dx, dy):
            """Bagian yang DIPATOK ke tanah (hem jubah, staff, telapak)."""
            return (int(cx + (dx * f + lean * f) * k),
                    int(cy - lift + dy * k))

        def _w(v):
            return max(1, int(round(v * k / _NS_morgath.SCALE)))

        # ---- bagian tubuh, belakang -> depan ----
        _NS_morgath._mor_draw_cape(surface, ptg, _w, f, phase, action)
        _NS_morgath._mor_draw_staff(surface, pt, ptg, _w, f, phase,
                                    action, ap)
        _NS_morgath._mor_draw_arm_back(surface, pt, _w, f, phase, action,
                                       ap)
        if action == "walk":
            _NS_morgath._mor_draw_boots(surface, ptg, _w, f, phase)
        _NS_morgath._mor_draw_skirt(surface, ptg, _w, f, phase, action)
        _NS_morgath._mor_draw_torso(surface, pt, _w, f, phase, action)
        _NS_morgath._mor_draw_belt(surface, ptg, _w, f, phase, action)
        _NS_morgath._mor_draw_pauldron(surface, pt, _w, f, phase,
                                       back=True)
        _NS_morgath._mor_draw_head(surface, pt, _w, f, phase, action, ap)
        _NS_morgath._mor_draw_arm_cast(surface, pt, _w, f, phase, action,
                                       ap)
        if action == "attack":
            _NS_morgath._draw_attack_smear(surface, pt, _w, f, ap)
            _NS_morgath._draw_attack_impact(surface, pt, _w, f, ap, phase)
        _NS_morgath._mor_draw_pauldron(surface, pt, _w, f, phase,
                                       back=False)
        _NS_morgath._draw_rig_ambient(surface, pt, _w, f, phase, action)
        if detail:
            _NS_morgath._mor_draw_masterwork_details(surface, pt, _w, f,
                                                     phase, action)

    # ------------------------------------------------------------
    # BAGIAN TUBUH (ruang lokal: y=0 jangkar, + ke bawah; +x = depan)
    # ------------------------------------------------------------
    def _mor_draw_cape(surface, ptg, _w, f, phase, action):
        """Cape besar mengalir di belakang; hem bergerigi (_tuft_points)
        + dither band + rim cahaya kiri-atas (secondary motion)."""
        P = _NS_morgath.PALETTE
        sway = math.sin(phase * 0.8) * 3.0
        if action == "walk":
            sway += math.sin(phase * 1.5) * 3.0
        elif action == "ascend":
            sway -= 4.0                       # jubah berkibar saat naik
        lag = math.sin(phase * 0.55 + 0.7) * 1.5     # overshoot lembut

        def cp(dx, dy):
            # sway membesar ke arah hem (bawah), nol di bahu
            grow = max(0.0, (dy + 33.0) / 93.0)
            return ptg(dx - f * (sway + lag) * grow, dy)

        # Spine hem (dasar) + siluet bergerigi deterministik
        hem = [(-46, 52), (-40, 57), (-31, 59.5), (-21, 60)]
        tuft = _NS_morgath._tuft_points(hem, depth=3.0, min_len=5.5,
                                        seed=7)
        panel = [(-13.5, -34.5), (13.5, -34.5), (19.5, -21),
                 (15, 0), (6, 24), (-2, 44), (-8, 56)]
        panel += tuft
        panel += [(-34, 56), (-45, 46), (-50, 30), (-52, 8),
                  (-49, -16), (-36, -30), (-24, -34.5)]
        _NS_morgath._poly(surface, P["shadow_deep"],
                          [cp(x + 1, y + 1) for x, y in panel])
        _NS_morgath._poly(surface, P["robe_darkest"],
                          [cp(x, y) for x, y in panel])
        # Bidang tengah
        mid = [(-9, -33), (11, -33), (15, -20), (12, -2),
               (5, 20), (-2, 40), (-9, 54), (-24, 52),
               (-33, 44), (-30, 10), (-22, -16)]
        _NS_morgath._poly(surface, P["robe_dark"],
                          [cp(x, y) for x, y in mid])
        # Panel cahaya kiri-atas (key light)
        _NS_morgath._poly(surface, P["robe_mid"],
                          [cp(x, y) for x, y in
                           [(-24, -34), (-36, -30), (-48, -14),
                            (-49, 6), (-44, 20), (-33, 26),
                            (-26, 10), (-20, -14)]])
        # Garis lipatan (3 nada gelap -> mid)
        for i, tone in enumerate(("robe_darkest", "robe_darkest",
                                  "robe_mid", "robe_mid")):
            bx = -30 + i * 9
            pygame.draw.line(surface, P[tone], cp(bx, -8 + i * 3),
                             cp(bx - 4, 46 - i), _w(1))
        # Dither band 50% di transisi panel tengah
        y0 = -6.0
        _NS_morgath._dither_rows(surface, cp(-14, y0)[0],
                                 cp(4, y0)[0], cp(0, y0)[1],
                                 2, P["robe_mid"], w=_w(1), seed=1)
        # Rim cahaya di siluet atas (sisi terang)
        for a, b in (((-13.5, -34.5), (-24, -34.5)),
                     ((-24, -34.5), (-36, -30)),
                     ((-36, -30), (-48, -14))):
            _NS_morgath._aaline(surface, P["robe_edge"], cp(*a), cp(*b),
                                _w(1))
        # Tepi depan tertangkap cahaya orb
        _NS_morgath._aaline(surface, P["robe_light"], cp(15, -30),
                            cp(17, -14), _w(1))
        _NS_morgath._aaline(surface, P["robe_mid"], cp(17, -14),
                            cp(11, 10), _w(1))

    def _mor_draw_staff(surface, pt, ptg, _w, f, phase, action, ap):
        """ARC STAFF 'Tempus' - senjata khas: shaft kayu-ungu 3-band
        tertanam di tanah, collar emas, finial bulan sabit + kristal
        melayang. Grip = tangan belakang (staff ikut pose = inertia)."""
        P = _NS_morgath.PALETTE
        hand = _NS_morgath._back_hand_local(action, ap, phase)
        gx, gy = pt(*hand)
        sway = math.sin(phase * 2.0) * 2.2 if action == "walk" else 0.0
        bx, by = ptg(_NS_morgath.STAFF_BASE[0] + sway,
                     _NS_morgath.STAFF_BASE[1])
        # Selout sisi bayangan lalu shaft 3-band
        _NS_morgath._aaline(surface, P["shadow_deep"],
                            (gx + _w(1), gy + _w(1)),
                            (bx + _w(1), by + _w(1)), _w(5.6))
        _NS_morgath._aaline(surface, P["staff_dark"], (gx, gy), (bx, by),
                            _w(4.6))
        _NS_morgath._aaline(surface, P["staff_mid"], (gx, gy), (bx, by),
                            _w(3.0))
        _NS_morgath._aaline(surface, P["staff_light"], (gx, gy),
                            (gx + (bx - gx) * 0.42, gy + (by - gy) * 0.42),
                            _w(1))
        # Serat kayu (2 goresan pendek)
        for tt in (0.30, 0.55):
            px_ = gx + (bx - gx) * tt
            py_ = gy + (by - gy) * tt
            _NS_morgath._aaline(surface, P["staff_dark"],
                                (int(px_ - _w(1.2)), int(py_)),
                                (int(px_ + _w(1.2)), int(py_ + _w(2))),
                                _w(1))
        # Collar emas
        for tt in (0.26, 0.60):
            px_ = gx + (bx - gx) * tt
            py_ = gy + (by - gy) * tt
            _NS_morgath._aaline(surface, P["gold_dark"],
                                (int(px_), int(py_)),
                                (int(px_ + _w(0.4)), int(py_ + _w(0.4))),
                                _w(5.4))
            _NS_morgath._aaline(surface, P["gold_mid"],
                                (int(px_), int(py_)),
                                (int(px_ + _w(0.4)), int(py_ + _w(0.4))),
                                _w(3.0))
            _NS_morgath._aaline(surface, P["gold_light"],
                                (int(px_ - _w(0.8)), int(py_)),
                                (int(px_ - _w(0.4)), int(py_ + _w(0.4))),
                                _w(1))
        # Sepatu kaki staff (flare kecil menapak)
        _NS_morgath._ellipse(surface, P["armor_dark"],
                             (bx - _w(4.5), by - _w(1.4), _w(9), _w(3)), 0)
        _NS_morgath._aaline(surface, P["armor_mid"],
                            (bx - _w(3.2), by - _w(0.4)),
                            (bx + _w(3.2), by - _w(0.4)), _w(1))
        # ── Finial: bulan sabit + kristal melayang ──
        bob = math.sin(phase * 1.6) * 1.4
        fx, fy = gx + _w(1.5), gy - _w(9.0) + _w(bob * 0.4)
        for r_, col, w_ in ((_w(4.6), P["gold_dark"], _w(1.6)),
                            (_w(3.4), P["gold_mid"], _w(1.4)),
                            (_w(2.2), P["gold_light"], _w(1))):
            _NS_morgath._aacircle(surface, col, (int(fx), int(fy)), r_, w_)
        # Kristal kecil (5 band, warna inti ikut skill)
        skill = _NS_morgath._MOR_SKILL.v
        core_col = {"w": P["flux_light"], "e": P["arc_hot"],
                    "r": P["white"], "q": P["arc_light"]}.get(
                        skill, P["orb_light"])
        cx_, cy_ = int(fx), int(fy - _w(4.6 + bob * 0.3))
        _NS_morgath._aacircle(surface, P["orb_dark"], (cx_, cy_), _w(2.8))
        _NS_morgath._aacircle(surface, P["orb_mid"], (cx_, cy_), _w(2.0))
        _NS_morgath._aacircle(surface, core_col, (cx_, cy_), _w(1.2))
        _NS_morgath._rect(surface, P["orb_shine"],
                          (cx_ - _w(1.0), cy_ - _w(1.0), _w(0.8), _w(0.8)))
        # Glow redup di sekitar kristal saat skill aktif
        if skill:
            _NS_morgath._aacircle(surface,
                                  (*core_col, 60), (cx_, cy_), _w(4.2))

    def _mor_morph_shoulder_chain(shoulder, hand, bend):
        elbow = _NS_morgath._mor_elbow(shoulder, hand, bend)
        return elbow

    def _mor_sleeve(surface, pt, _w, f, shoulder, elbow, hand,
                    base, edge, dim=False):
        """Lengan berjubah: dua segmen meruncing + cuff emas + elbow pad."""
        P = _NS_morgath.PALETTE
        sh, el, hd = pt(*shoulder), pt(*elbow), pt(*hand)

        def seg(a, b, w_a, w_b, color):
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = max(1.0, math.hypot(dx, dy))
            px, py = -dy / L, dx / L
            pts = [(a[0] + px * w_a, a[1] + py * w_a),
                   (b[0] + px * w_b, b[1] + py * w_b),
                   (b[0] - px * w_b, b[1] - py * w_b),
                   (a[0] - px * w_a, a[1] - py * w_a)]
            _NS_morgath._poly(surface, color,
                              [(int(qx), int(qy)) for qx, qy in pts])

        if not dim:
            seg((sh[0] + 1, sh[1] + 1), (el[0] + 1, el[1] + 1),
                _w(4.6), _w(3.8), P["shadow_deep"])
        seg(sh, el, _w(4.4), _w(3.6), base)
        seg(el, hd, _w(3.6), _w(2.9), base)
        # Garis tepi terang di sisi atas lengan
        _NS_morgath._aaline(surface, edge, sh, hd, _w(1))
        # Elbow pad (lingkaran kecil armor)
        ep = pt(*elbow)
        _NS_morgath._aacircle(surface, P["armor_dark"], ep, _w(2.2))
        _NS_morgath._aacircle(surface, P["armor_mid"], ep, _w(1.4))
        # Manset emas di pergelangan
        ex, ey = el[0] + (hd[0] - el[0]) * 0.8, el[1] + (hd[1] - el[1]) * 0.8
        wx, wy = el[0] + (hd[0] - el[0]) * 0.97, el[1] + (hd[1] - el[1]) * 0.97
        _NS_morgath._aaline(surface, P["gold_dark"],
                            (int(ex), int(ey)), (int(wx), int(wy)), _w(4.4))
        _NS_morgath._aaline(surface, P["gold_mid"],
                            (int(ex), int(ey)), (int(wx), int(wy)), _w(2.6))

    def _mor_draw_arm_back(surface, pt, _w, f, phase, action, ap):
        """Lengan belakang: lebih redup; menggenggam arc staff."""
        P = _NS_morgath.PALETTE
        shoulder = _NS_morgath.SHOULDER_BACK
        hand = _NS_morgath._back_hand_local(action, ap, phase)
        elbow = _NS_morgath._mor_morph_shoulder_chain(shoulder, hand, -4.5)
        _NS_morgath._mor_sleeve(surface, pt, _w, f, shoulder, elbow, hand,
                                P["robe_darkest"], P["robe_dark"], dim=True)
        # Gauntlet grip + node redup
        hp = pt(*hand)
        _NS_morgath._aacircle(surface, P["armor_dark"], hp, _w(3.6))
        _NS_morgath._aacircle(surface, P["armor_mid"], hp, _w(2.6))
        _NS_morgath._rect(surface, P["armor_shine"],
                          (hp[0] - _w(0.8), hp[1] - _w(0.8),
                           _w(0.9), _w(0.9)))
        glow = 1.0 if action == "attack" else 0.5
        _NS_morgath._aacircle(surface, P["arc_dark"], hp,
                              _w(2.6 * glow), _w(1))
        if action == "attack" and ap < 0.4:
            _NS_morgath._aacircle(surface, P["arc_mid"], hp, _w(1.6),
                                  _w(1))

    def _mor_draw_boots(surface, ptg, _w, f, phase):
        """FOOT SOLVER: ujung sepatu mengintip dari hem saat walk;
        telapak terangkat bergantian + debu tapak + shadow kontak."""
        P = _NS_morgath.PALETTE
        FE = _NS_morgath.FEET_DY
        ph = phase * 2.0
        for side, sxo in ((0, 12.0), (1, -10.0)):
            s = math.sin(ph + side * math.pi)
            lift = max(0.0, s) * 4.2
            sx = sxo + math.cos(ph + side * math.pi) * 1.5
            toe = [(sx - 4.5, FE - 6 - lift), (sx + 6, FE - 6 - lift),
                   (sx + 7.5, FE - lift), (sx - 4.5, FE - lift)]
            _NS_morgath._poly(surface, P["armor_dark"],
                              [ptg(x, y) for x, y in toe])
            _NS_morgath._poly(surface, P["armor_mid"],
                              [ptg(x, y) for x, y in
                               [(sx - 2.5, FE - 5.5 - lift),
                                (sx + 5, FE - 5.5 - lift),
                                (sx + 6.5, FE - 1 - lift),
                                (sx - 2.5, FE - 1 - lift)]])
            _NS_morgath._aaline(surface, P["armor_shine"],
                                ptg(sx - 1.5, FE - 5 - lift),
                                ptg(sx + 3.5, FE - 5 - lift), _w(1))
            # Bayangan kontak (hanya saat menapak)
            if lift < 1.2:
                bpx, bpy = ptg(sx + 1, FE)
                _NS_morgath._ellipse(surface, (*P["shadow"], 90),
                                     (bpx - _w(5), bpy - _w(1),
                                      _w(10), _w(2)), 0)
            # Debu saat menapak (silang nol dari atas ke bawah)
            if 0.15 < (ph + side * math.pi) % math.tau < 0.55:
                dpx, dpy = ptg(sx - 1.5, FE - 1)
                _NS_morgath._aacircle(surface, (*P["robe_edge"], 90),
                                      (dpx - _w(1.5), dpy), _w(1.2))
                _NS_morgath._aacircle(surface, (*P["robe_edge"], 60),
                                      (dpx + _w(1.5), dpy - _w(1)), _w(1))



    def _mor_draw_skirt(surface, ptg, _w, f, phase, action):
        """Rok jubah A-line; hem bergigi/scallop DIPATOK di FEET_DY
        (tidak melayang) + tabard rune arc + pita hem emas."""
        P = _NS_morgath.PALETTE
        FE = _NS_morgath.FEET_DY
        hem_sway = math.sin(phase * 1.7) * 1.8 if action == "walk" else 0.0

        def sp(dx, dy):
            return ptg(dx + f * hem_sway * max(0.0, dy / FE), dy)

        # Hem bergerigi deterministik (siluet pixel-art)
        hem_spine = [(-26, 55), (-17, 60), (-8, 60), (0, 60),
                     (9, 60), (18, 60), (27, 56)]
        tuft = _NS_morgath._tuft_points(hem_spine, depth=2.6, min_len=5,
                                        seed=23)
        skirt = [(-15, -12), (15, -12), (22, 0), (28, 18), (32, 40)]
        skirt += tuft
        skirt += [(-28, 40), (-24, 14), (-15, -4)]
        _NS_morgath._poly(surface, P["shadow_deep"],
                          [sp(x + 1, y + 1) for x, y in skirt])
        _NS_morgath._poly(surface, P["robe_mid"],
                          [sp(x, y) for x, y in skirt])
        # Bidang depan lebih terang (puncak jubah ke depan)
        front = [(-9, -11), (15, -11), (20, 2), (25, 20),
                 (28, 40), (24, 50), (16, 54), (8, 55), (0, 55),
                 (-6, 50), (-4, 26), (-7, 2)]
        _NS_morgath._poly(surface, P["robe_light"],
                          [sp(x, y) for x, y in front])
        # Sisi belakang masuk bayangan
        back = [(-9, -11), (-7, 2), (-4, 26), (-6, 50),
                (-16, 52), (-24, 48), (-27, 38), (-22, 14), (-14, -2)]
        _NS_morgath._poly(surface, P["robe_dark"],
                          [sp(x, y) for x, y in back])
        # Dither band 50% di panel belakang
        _NS_morgath._dither_rows(surface, sp(-20, 30)[0], sp(-6, 30)[0],
                                 sp(0, 30)[1], 2, P["robe_darkest"],
                                 w=_w(1), seed=2)
        # Lipatan vertikal meruncing ke pinggang
        for fx, tone in ((-3, "robe_mid"), (8, "robe_edge"),
                         (-14, "robe_darkest"), (18, "robe_mid")):
            _NS_morgath._aaline(surface, P[tone], sp(fx, -6),
                                sp(fx * 1.7, FE - 4), _w(1))
        # Tabard tengah: pita logam gelap + trim emas + rune arc
        tab = [(-6, -11), (6, -11), (7.5, 20), (4.5, 44), (0, 48),
               (-4.5, 44), (-7.5, 20)]
        _NS_morgath._poly(surface, P["armor_darkest"],
                          [sp(x, y) for x, y in tab])
        _NS_morgath._aaline(surface, P["gold_mid"], sp(-6, -10),
                            sp(-7.5, 20), _w(1))
        _NS_morgath._aaline(surface, P["gold_mid"], sp(-7.5, 20),
                            sp(-4.5, 44), _w(1))
        _NS_morgath._aaline(surface, P["gold_mid"], sp(6, -10),
                            sp(7.5, 20), _w(1))
        _NS_morgath._aaline(surface, P["gold_mid"], sp(7.5, 20),
                            sp(4.5, 44), _w(1))
        # Rune arc di tabard - warnanya ikut skill aktif (badan bereaksi)
        skill = _NS_morgath._MOR_SKILL.v
        rune_col = {"w": P["flux_light"], "e": P["arc_hot"],
                    "r": P["white"], "q": P["arc_light"]}.get(
                        skill, P["arc_mid"])
        rune = [(0, 18), (4.5, 24), (0, 30), (-4.5, 24)]
        _NS_morgath._poly(surface, P["arc_dark"], [sp(x, y) for x, y in rune])
        _NS_morgath._poly(surface, rune_col,
                          [sp(x * 0.7, 24 + (y - 24) * 0.7)
                           for x, y in rune])
        dot = sp(0, 24)
        _NS_morgath._rect(surface, P["arc_hot"],
                          (dot[0], dot[1], _w(1.2), _w(1.2)))
        # Pita hem emas redup + titik rune
        _NS_morgath._aaline(surface, P["gold_dark"], sp(-26, 52),
                            sp(27, 52), _w(1))
        for i in range(-3, 4):
            rx = i * 8
            _NS_morgath._rect(surface, P["rune_mid"],
                              (sp(rx, 52)[0], sp(rx, 52)[1],
                               _w(1), _w(1)))

    def _mor_draw_torso(surface, pt, _w, f, phase, action):
        """Cuirass dada: pelat baja-biru 5-band + trim emas + keystone
        arc menyala + dither band transisi ke skirt."""
        P = _NS_morgath.PALETTE
        breath = math.sin(phase * 0.9) * 1.1
        bw = 1.0 + breath * 0.05

        def tp(dx, dy):
            if dy > -34:                     # lebar napas hanya di dada
                dx *= bw
            return pt(dx, dy)

        chest = [(-15, -34), (15, -34), (18, -21), (14, -8),
                 (-14, -8), (-18, -21)]
        _NS_morgath._poly(surface, P["armor_dark"],
                          [tp(x + 1, y + 1) for x, y in chest])
        _NS_morgath._poly(surface, P["armor_mid"],
                          [tp(x, y) for x, y in chest])
        # Pelat dada kiri-kanan (nada terang menangkap cahaya atas-kiri)
        _NS_morgath._poly(surface, P["armor_light"],
                          [tp(x, y) for x, y in
                           [(-13.5, -33), (-1.5, -33), (-1.5, -15),
                            (-6, -18), (-12, -21)]])
        _NS_morgath._poly(surface, P["armor_light"],
                          [tp(x, y) for x, y in
                           [(1.5, -33), (13.5, -33), (12, -21),
                            (6, -18), (1.5, -15)]])
        # Specular cluster kiri-atas (1-2 px disengaja, bukan gradien)
        _NS_morgath._poly(surface, P["armor_shine"],
                          [tp(x, y) for x, y in
                           [(-10.5, -31.5), (-3, -31.5), (-3, -24),
                            (-9, -25.5)]])
        _NS_morgath._rect(surface, P["armor_shine"],
                          (tp(-10.5, -31.5)[0], tp(-10.5, -31.5)[1],
                           _w(1), _w(1)))
        _NS_morgath._poly(surface, P["armor_shine"],
                          [tp(x, y) for x, y in
                           [(3, -31.5), (10.5, -31.5), (9, -25.5),
                            (3, -24)]])
        # Garis tengah + jahitan pelat
        _NS_morgath._aaline(surface, P["armor_darkest"], tp(0, -33),
                            tp(0, -9), _w(1))
        _NS_morgath._aaline(surface, P["armor_darkest"], tp(-15, -19.5),
                            tp(15, -19.5), _w(1))
        # Dither band 50% di tepi bawah cuirass (transisi armor-skirt)
        _NS_morgath._dither_rows(surface, tp(-11, -10)[0],
                                 tp(11, -10)[0], tp(0, -10)[1],
                                 2, P["armor_darkest"], w=_w(1), seed=3)
        # Keystone arc di ulu hati (ikon faksi: sumber petir) - menyala
        # mengikuti skill aktif (badan bereaksi ke state skill)
        skill = _NS_morgath._MOR_SKILL.v
        key_col = {"w": P["flux_light"], "e": P["arc_hot"],
                   "r": P["white"], "q": P["arc_light"]}.get(
                       skill, P["arc_mid"])
        key = [(0, -28.5), (4.5, -24), (0, -18), (-4.5, -24)]
        _NS_morgath._poly(surface, P["arc_dark"],
                          [tp(x, y) for x, y in key])
        _NS_morgath._poly(surface, key_col,
                          [tp(x * 0.7, -24 + (y + 24) * 0.3)
                           for x, y in key])
        hot = tp(0, -24)
        _NS_morgath._rect(surface, P["arc_hot"],
                          (hot[0], hot[1], _w(1.2), _w(1.2)))
        if skill:
            _NS_morgath._aacircle(surface, (*key_col, 70),
                                  (hot[0], hot[1]), _w(4.5))
        # Kerah gorget: pita emas gelap di leher
        collar = [(-12, -35.5), (12, -35.5), (15, -33), (-15, -33)]
        _NS_morgath._poly(surface, P["gold_dark"],
                          [tp(x, y) for x, y in collar])
        _NS_morgath._aaline(surface, P["gold_light"], tp(-10.5, -34.5),
                            tp(10.5, -34.5), _w(1))

    def _mor_draw_belt(surface, ptg, _w, f, phase, action):
        """Sabuk pinggang + gesper + GRIMOIRE berantai di pinggul +
        dua rumbai (inertia/secondary motion)."""
        P = _NS_morgath.PALETTE
        band = [(-16.5, -13.5), (16.5, -13.5), (16.5, -6), (-16.5, -6)]
        _NS_morgath._poly(surface, P["robe_darkest"],
                          [ptg(x, y) for x, y in band])
        _NS_morgath._aaline(surface, P["gold_mid"], ptg(-16.5, -12),
                            ptg(16.5, -12), _w(1))
        _NS_morgath._aaline(surface, P["gold_dark"], ptg(-16.5, -6),
                            ptg(16.5, -6), _w(1))
        # Gesper arc
        buck = [(0, -15), (4.5, -10.5), (0, -6), (-4.5, -10.5)]
        _NS_morgath._poly(surface, P["gold_mid"],
                          [ptg(x, y) for x, y in buck])
        c = ptg(0, -10.5)
        _NS_morgath._rect(surface, P["arc_light"],
                          (c[0], c[1], _w(1), _w(1)))
        # ── Grimoire: buku sihir berantai di pinggul belakang ──
        sway = math.sin(phase * 1.3) * 1.5
        if action == "walk":
            sway += math.sin(phase * 2.0) * 2.4
        bx0 = -22.0 + f * sway * 0.4
        # rantai dari sabuk
        _NS_morgath._aaline(surface, P["gold_dark"], ptg(-14, -6),
                            ptg(bx0, 2), _w(1))
        book = [(bx0 - 4, 1), (bx0 + 4, 1), (bx0 + 4.5, 8),
                (bx0, 12), (bx0 - 4.5, 8)]
        _NS_morgath._poly(surface, P["shadow_deep"],
                          [ptg(x + 1, y + 1) for x, y in book])
        _NS_morgath._poly(surface, P["leather_dark"],
                          [ptg(x, y) for x, y in book])
        _NS_morgath._poly(surface, P["leather_mid"],
                          [ptg(x, y) for x, y in
                           [(bx0 - 2.5, 1.5), (bx0 + 2.5, 1.5),
                            (bx0 + 3, 7.5), (bx0, 10.5), (bx0 - 3, 7.5)]])
        # halaman + rune
        _NS_morgath._aaline(surface, P["page_light"], ptg(bx0, 1.5),
                            ptg(bx0, 10.5), _w(1))
        rp = ptg(bx0, 5)
        _NS_morgath._rect(surface, P["flux_light"],
                          (rp[0], rp[1], _w(1), _w(1)))
        # pojok logam + gesper buku
        _NS_morgath._rect(surface, P["gold_mid"],
                          (ptg(bx0 - 4, 1)[0], ptg(bx0 - 4, 1)[1],
                           _w(1.2), _w(1.2)))
        _NS_morgath._rect(surface, P["gold_mid"],
                          (ptg(bx0 + 2.8, 1)[0], ptg(bx0 + 2.8, 1)[1],
                           _w(1.2), _w(1.2)))
        # ── Rumbai: mengayun saat walk, menggantung saat idle ──
        for hx in (-9, 9):
            ex = hx + f * sway
            _NS_morgath._aaline(surface, P["gold_dark"], ptg(hx, -6),
                                ptg(ex, 18), _w(1))
            bead = ptg(ex, 19.5)
            _NS_morgath._aacircle(surface, P["gold_light"], bead,
                                  _w(2.1))
            dot = ptg(ex - 0.6, 18.9)
            _NS_morgath._rect(surface, P["gold_shine"],
                              (dot[0], dot[1], _w(1), _w(1)))

    def _mor_draw_pauldron(surface, pt, _w, f, phase, back=False):
        """Pelat bahu berlapis 3 + rivet + stud arc: sumber siluet
        'penuh' ke samping (selout sisi bayangan)."""
        P = _NS_morgath.PALETTE
        breath = math.sin(phase * 0.9) * 0.75
        if back:
            cx0, cy0 = -18.0, -36.0 + breath * 0.5
            sizes = ((9.75, 6.0), (11.25, 6.75))
            base, top = P["armor_dark"], P["armor_mid"]
            edge = P["armor_mid"]
        else:
            cx0, cy0 = 18.0, -37.5 + breath * 0.5
            sizes = ((10.5, 6.75), (12.75, 7.5), (14.25, 8.25))
            base, top = P["armor_mid"], P["armor_light"]
            edge = P["gold_mid"]
        for i, (rx, ry) in enumerate(sizes):
            ox = cx0 - i * 1.5
            oy = cy0 + i * 4.8
            plate = [(ox - rx, oy + ry * 0.4), (ox - rx * 0.7, oy - ry),
                     (ox + rx * 0.4, oy - ry * 0.9),
                     (ox + rx, oy - ry * 0.2),
                     (ox + rx * 0.8, oy + ry * 0.6), (ox, oy + ry)]
            _NS_morgath._poly(surface, P["armor_darkest"],
                              [pt(x + 1.2, y + 1.2) for x, y in plate])
            _NS_morgath._poly(surface, base if i else P["armor_darkest"],
                              [pt(x, y) for x, y in plate])
            _NS_morgath._poly(surface, top,
                              [pt(x, y) for x, y in
                               [(ox - rx * 0.6, oy - ry * 0.7),
                                (ox + rx * 0.2, oy - ry * 0.6),
                                (ox + rx * 0.5, oy - ry * 0.1),
                                (ox - rx * 0.4, oy - ry * 0.2)]])
            if i == len(sizes) - 1:
                _NS_morgath._aaline(surface, edge,
                                    pt(ox - rx + 1.5, oy + ry * 0.5),
                                    pt(ox + rx * 0.4, oy + ry * 0.7),
                                    _w(1))
        # Rivet (dither dots) + specular cluster
        for i in range(3):
            rx_ = cx0 - 3 + i * 3
            rp = pt(rx_, cy0 + 1.5 + i * 4.0)
            _NS_morgath._rect(surface, P["armor_shine"],
                              (rp[0], rp[1], _w(1), _w(1)))
        sp_ = pt(cx0 + (3.0 if not back else -1.5), cy0 - 3.0)
        _NS_morgath._rect(surface, P["armor_shine"],
                          (sp_[0], sp_[1], _w(1.2), _w(1.2)))
        # Paku arc kecil di pelat teratas
        stud = pt(cx0 + (3.0 if not back else -1.5), cy0 - 3.0)
        _NS_morgath._aacircle(surface, P["arc_light"], stud, _w(1.6))
        _NS_morgath._aacircle(surface, P["arc_shine"], stud, _w(0.8))

    def _mor_draw_head(surface, pt, _w, f, phase, action, ap):
        """Hood dalam + ORB KRISTAL 5-band (focal point PALING terang)
        + shard orbit + antena arc + mahkota diadem."""
        P = _NS_morgath.PALETTE
        ox, oy = _NS_morgath.ORB_CENTER
        hover = math.sin(phase * 1.3) * 0.75
        skill = _NS_morgath._MOR_SKILL.v
        core_col = {"w": P["flux_light"], "e": P["arc_hot"],
                    "r": P["white"], "q": P["arc_light"]}.get(
                        skill, P["orb_hot"])

        # --- Antena arc (sirip logam) dari sisi hood -----------------
        # Puncak dijaga supaya rel <= CY-62 (4 px LIFT + 0.8 skala):
        # tidak boleh menyentuh HP bar boss (y-r-15..y-r-7).
        fin_f = [(7.5, -61.5), (15, -72), (19.5, -71), (13.5, -60)]
        fin_b = [(-9, -61.5), (-15, -71), (-12, -72), (-4.5, -63)]
        _NS_morgath._poly(surface, P["armor_dark"],
                          [pt(x, y) for x, y in fin_b])
        _NS_morgath._poly(surface, P["armor_mid"],
                          [pt(x, y) for x, y in fin_f])
        _NS_morgath._rect(surface, P["armor_shine"],
                          (pt(10.5, -71)[0], pt(10.5, -71)[1],
                           _w(1.2), _w(1.2)))
        tip_f, tip_b = pt(17.25, -72.2), pt(-13.5, -72.0)
        _NS_morgath._rect(surface, core_col if skill else P["arc_light"],
                          (tip_f[0], tip_f[1], _w(1.8), _w(1.8)))
        _NS_morgath._rect(surface, P["arc_mid"],
                          (tip_b[0], tip_b[1], _w(1.5), _w(1.5)))
        # Tell charge: percikan melompat antar ujung antena
        if (action == "attack" and 0.02 < ap < 0.9) or skill:
            a = _NS_morgath._alpha(min(1.0, ap / 0.3) * 230) \
                if action == "attack" else 200
            _NS_morgath._jagged_line(surface, (*P["arc_hot"], a),
                                     tip_b, tip_f, jitter=_w(3), segments=4,
                                     width=_w(1.4))
            _NS_morgath._jagged_line(surface, (*P["arc_light"], a),
                                     pt(-13.5, -71.5),
                                     pt(17.25, -70.5),
                                     jitter=_w(2), segments=4, width=_w(1))

        # --- Hood luar ------------------------------------------------
        hood = [(-16.5, -34.5), (-21, -45), (-17, -57), (-9, -64),
                (0, -66), (9, -64), (17, -57), (20, -45),
                (16.5, -36), (9, -31.5), (-9, -31.5)]
        _NS_morgath._poly(surface, P["shadow_deep"],
                          [pt(x + 1, y + 1) for x, y in hood])
        _NS_morgath._poly(surface, P["robe_dark"],
                          [pt(x, y) for x, y in hood])
        # Volume sisi terang (cahaya depan-atas / kiri-atas)
        _NS_morgath._poly(surface, P["robe_mid"],
                          [pt(x, y) for x, y in
                           [(-4.5, -63), (7.5, -61.5), (15, -54),
                            (18, -43.5), (13.5, -37.5), (6, -57)]])
        _NS_morgath._poly(surface, P["robe_light"],
                          [pt(x, y) for x, y in
                           [(0, -64.5), (7.5, -61.5), (12, -55.5),
                            (3, -58.5)]])
        # Lipatan hood
        for lx, tone in ((-12, "robe_darkest"), (-6, "robe_darkest"),
                         (12, "robe_edge")):
            _NS_morgath._aaline(surface, P[tone], pt(lx, -55.5),
                                pt(lx + f * 1.5, -39), _w(1))
        # Puncak hood menukik ke depan
        peak = [(-3, -66), (4.5, -67.5), (10.5, -63), (3, -64.5)]
        _NS_morgath._poly(surface, P["robe_mid"],
                          [pt(x, y) for x, y in peak])
        # Mahkota diadem emas di puncak
        _NS_morgath._aaline(surface, P["gold_dark"], pt(-12, -61.5),
                            pt(0, -66), _w(1.4))
        _NS_morgath._aaline(surface, P["gold_dark"], pt(0, -66),
                            pt(12, -61.5), _w(1.4))
        _NS_morgath._rect(surface, P["gold_shine"],
                          (pt(0, -66)[0], pt(0, -66)[1],
                           _w(1.2), _w(1.2)))

        # --- Lubang wajah: gelap pekat, jadi orb menonjol --------------
        hole = [(-9, -57), (9, -57), (12, -45), (9, -39),
                (-7.5, -40.5), (-10.5, -46.5)]
        _NS_morgath._poly(surface, P["shadow_deep"],
                          [pt(x, y) for x, y in hole])
        _NS_morgath._poly(surface, P["robe_darkest"],
                          [pt(x, y) for x, y in
                           [(-9, -57), (9, -57), (10.5, -51),
                            (-9, -52.5)]])

        # --- ORB kristal (nilai TERTINGGI di seluruh sprite) ----------
        oc = pt(ox, oy + hover)
        orad = _NS_morgath.ORB_R
        pulse = math.sin(phase * 2.2) * 0.5 + 0.5
        # Halo lembut (dua lingkaran alpha - murah)
        _NS_morgath._aacircle(surface, (*P["orb_dark"], 46), oc,
                              _w(orad + 7.5))
        _NS_morgath._aacircle(surface, (*P["orb_mid"], 60), oc,
                              _w(orad + 3))
        # Cangkang kristal (5 band)
        _NS_morgath._aacircle(surface, P["orb_dark"], oc, _w(orad))
        _NS_morgath._aacircle(surface, P["orb_mid"], oc, _w(orad - 2.2))
        # Bayangan kristal: pita gelap bawah-kanan (selout internal)
        low = (oc[0] + _w(2.2), oc[1] + _w(3.0))
        _NS_morgath._aacircle(surface, P["orb_darkest"], low,
                              _w(orad - 6.75))
        _NS_morgath._aacircle(surface, P["orb_dark"], low,
                              _w(orad - 9.0))
        # Facet lines (2 goresan halus, kristal bersegi)
        _NS_morgath._aaline(surface, P["orb_darkest"], oc,
                            (oc[0] - _w(7), oc[1] - _w(7)), _w(1))
        _NS_morgath._aaline(surface, P["orb_darkest"],
                            (oc[0] + _w(6), oc[1] + _w(6)),
                            (oc[0] + _w(3), oc[1] + _w(9)), _w(1))
        # Pusaran energi: dua busur orbit (ikuti phase)
        for i in range(2):
            ang = phase * 2.4 + i * math.pi
            sx = math.cos(ang) * (orad - 5.25)
            sy = math.sin(ang) * (orad - 5.25) * 0.55
            p1 = pt(ox + sx, oy + hover + sy)
            p2 = pt(ox + sx * 0.4, oy + hover + sy * 0.4 - 2.25)
            _NS_morgath._aaline(surface, P["orb_light"], p1, p2, _w(2))
        # Inti panas: denyut dengan phase (flare saat skill aktif)
        flare = 1.0 + (0.8 if skill else 0.0) * pulse
        core = (oc[0], oc[1] - _w(2.25))
        _NS_morgath._aacircle(surface, core_col, core,
                              _w(3.9 * flare + pulse))
        _NS_morgath._aacircle(surface, P["orb_shine"], core,
                              _w(2.1 + pulse * 0.75))
        # Glint kaca kiri-atas (specular cluster, bukan gradien)
        _NS_morgath._rect(surface, P["orb_shine"],
                          (oc[0] - _w(6), oc[1] - _w(6.75),
                           _w(1.8), _w(1.8)))
        _NS_morgath._rect(surface, P["white"],
                          (oc[0] - _w(4.5), oc[1] - _w(7.5),
                           _w(1), _w(1)))
        # Pecahan rune mengorbit orb (4 shard + glint)
        for i in range(4):
            ang = phase * 1.6 + i * (math.pi / 2.0)
            rx = math.cos(ang) * (orad + 6.75)
            ry = math.sin(ang) * (orad + 6.75) * 0.6
            shp = pt(ox + rx, oy + hover + ry)
            s = _w(1.8)
            _NS_morgath._poly(surface, P["arc_light"],
                              [(shp[0], shp[1] - s), (shp[0] + s, shp[1]),
                               (shp[0], shp[1] + s), (shp[0] - s, shp[1])])
            _NS_morgath._rect(surface, P["arc_shine"],
                              (shp[0] - _w(0.6), shp[1] - _w(0.6),
                               _w(0.9), _w(0.9)))
        # Ring flare tipis saat ultimate
        if skill == "r":
            _NS_morgath._dashed_ring(surface, oc[0], oc[1],
                                     _w(orad + 9), P["arc_hot"],
                                     180, phase * 3, segments=8,
                                     thick=_w(1.4), span=0.5)

        # --- Bibir hood menangkap cahaya orb ---------------------------
        _NS_morgath._aaline(surface, P["robe_light"], pt(-7.5, -40.5),
                            pt(9, -40.5), _w(1))
        _NS_morgath._aaline(surface, P["robe_edge"], pt(9, -40.5),
                            pt(12, -46.5), _w(1))

    def _mor_draw_arm_cast(surface, pt, _w, f, phase, action, ap):
        """Lengan cast depan: pose-driven; telapak = muzzle beam.
        Node sihir di telapak menyala sesuai skill (badan bereaksi)."""
        P = _NS_morgath.PALETTE
        shoulder = _NS_morgath.SHOULDER_FRONT
        hand = _NS_morgath._cast_hand_local(action, ap, phase)
        elbow = _NS_morgath._mor_morph_shoulder_chain(shoulder, hand, 5.25)
        _NS_morgath._mor_sleeve(surface, pt, _w, f, shoulder, elbow, hand,
                                P["robe_dark"], P["robe_mid"], dim=False)

        hp = pt(*hand)
        # Gauntlet
        _NS_morgath._aacircle(surface, P["armor_dark"], hp, _w(4.2))
        _NS_morgath._aacircle(surface, P["armor_mid"], hp, _w(3.2))
        _NS_morgath._aacircle(surface, P["armor_light"], hp, _w(2.0))
        _NS_morgath._aacircle(surface, P["armor_shine"],
                              (hp[0] - _w(0.9), hp[1] - _w(0.9)),
                              _w(1.1))

        # Node sihir di telapak: ukuran mengikuti pose + skill
        skill = _NS_morgath._MOR_SKILL.v
        if skill == "w":
            node_col, glow_col = P["flux_light"], P["flux_mid"]
        elif skill == "r":
            node_col, glow_col = P["white"], P["arc_hot"]
        elif skill == "e":
            node_col, glow_col = P["arc_hot"], P["arc_mid"]
        else:
            node_col, glow_col = P["arc_hot"], P["arc_mid"]
        if action == "attack":
            charge = 1.0 if ap >= 0.9 else min(1.0, ap / 0.35)
            node_r = 3.0 + 4.5 * charge
        elif action in ("point", "channel", "ascend"):
            node_r = 4.5
        elif action == "erect":
            node_r = 3.3
        else:
            node_r = 2.4
        pulse = math.sin(phase * 4.0) * 0.5 + 0.5
        nr = node_r + pulse * 0.9
        _NS_morgath._aacircle(surface, (*glow_col, 70), hp, _w(nr + 4.5))
        _NS_morgath._aacircle(surface, P["arc_dark"], hp, _w(nr))
        _NS_morgath._aacircle(surface, P["arc_mid"], hp, _w(nr - 1.5))
        _NS_morgath._aacircle(surface, node_col, hp, _w(nr - 3.3))
        _NS_morgath._aacircle(surface, P["arc_shine"], hp,
                              _w(max(1, nr - 5.1)))
        # Mini fork berdenyut saat charge penuh / stance skill
        if (action == "attack" and ap >= 0.35) or action in ("point",
                                                             "ascend"):
            for i in range(3):
                ang = phase * 5.0 + i * math.pi * 2.0 / 3.0
                tip = pt(hand[0] + math.cos(ang) * 9.0,
                         hand[1] + math.sin(ang) * 9.0)
                _NS_morgath._jagged_line(surface, P["arc_hot"], hp, tip,
                                         jitter=2.25, segments=2,
                                         width=_w(1.4))



    # ------------------------------------------------------------
    # ATTACK FX (smear berlapis + frame IMPACT)
    # ------------------------------------------------------------
    def _draw_attack_smear(surface, pt, _w, f, ap):
        """Smear dorong 3-band dari tangan tarik -> muzzle (jendela
        thrust) + leading edge terang di telapak sekarang."""
        if not (0.35 <= ap <= 0.92):
            return
        P = _NS_morgath.PALETTE
        t = max(0.0, min(1.0, (ap - 0.35) / 0.45))
        fade = int(200 * math.sin(min(1.0, t * 1.4) * math.pi * 0.5))
        hand = _NS_morgath._cast_hand_local("attack", ap, 0.0)
        hx, hy = hand
        # Band dari belakang tangan ke telapak sekarang (tapered)
        x0, x1 = hx - 30.0, hx + 1.5
        for seg in range(12):
            s0, s1 = seg / 12.0, (seg + 1) / 12.0
            wx = 0.5 + math.sin(s0 * math.pi) * 0.5        # taper
            y0 = hy - 9.0 * wx + math.sin(s0 * 14.0 + f * 3) * 1.2
            y1 = hy - 9.0 * (0.5 + math.sin(s1 * math.pi) * 0.5) \
                + math.sin(s1 * 14.0 + f * 3) * 1.2
            a0 = pt(x0 + (x1 - x0) * s0, y0)
            a1 = pt(x0 + (x1 - x0) * s1, y1)
            _NS_morgath._aaline(surface,
                                (*P["arc_darkest"], int(fade * 0.6)),
                                a0, a1, _w(7))
            _NS_morgath._aaline(surface, (*P["arc_mid"], fade), a0, a1,
                                _w(4))
            _NS_morgath._aaline(surface, (*P["arc_light"], fade), a0, a1,
                                _w(2))
        # Core terang di sepanjang poros + glint berjalan
        a0 = pt(x0, hy - 2.0)
        a1 = pt(x1, hy - 2.0)
        _NS_morgath._aaline(surface, (*P["arc_hot"], fade), a0, a1, _w(1))
        gx = pt(hx + 2.0, hy - 2.0)
        _NS_morgath._rect(surface, P["white"],
                          (gx[0], gx[1], _w(1.4), _w(1.4)))

    def _draw_attack_impact(surface, pt, _w, f, ap, phase):
        """Frame IMPACT: bintang 8-spike + shockwave ganda + forks +
        serpihan di muzzle (jendela HOLD 0.86..0.98)."""
        if not (0.86 <= ap <= 0.98):
            return
        P = _NS_morgath.PALETTE
        t = max(0.0, min(1.0, (ap - 0.86) / 0.12))
        fade = int(235 * (1 - t))
        mx, my = pt(*_NS_morgath.MOR_MUZZLE)
        _NS_morgath._spark_star(surface, mx, my, _w(15 * (1 - t * 0.5)),
                                P["arc_shine"], fade, spikes=8,
                                rot=0.25, core=P["white"])
        for k, rr in enumerate((_w(9 + t * 22), _w(5 + t * 13))):
            _NS_morgath._aacircle(
                surface, (*P["arc_light" if k == 0 else "arc_hot"],
                          fade), (mx, my), rr, _w(1.4))
        for i in range(4):
            ang = i * math.pi / 2.0 + phase * 0.4
            tip = (mx + math.cos(ang) * _w(16 * (1 - t * 0.4)),
                   my + math.sin(ang) * _w(10 * (1 - t * 0.4)))
            _NS_morgath._jagged_line(surface, P["arc_hot"], (mx, my), tip,
                                     jitter=2.0, segments=3, width=_w(1))
        # Serpihan batu/energi (deterministik)
        for i in range(5):
            ang = -2.8 + i * 0.45
            d0 = _w(10 + t * (24 + i * 5))
            cxx = mx + math.cos(ang) * d0
            cyy = my + math.sin(ang) * d0 * 0.7 + t * t * _w(26)
            _NS_morgath._aacircle(surface, P["arc_darkest"],
                                  (int(cxx), int(cyy)), _w(1.6))
            _NS_morgath._aacircle(surface, P["arc_dark"],
                                  (int(cxx - _w(0.5)), int(cyy - _w(0.5))),
                                  _w(0.9))

    # ------------------------------------------------------------
    # AMBIENT LIFE (idle/walk) + PORTRAIT LOD
    # ------------------------------------------------------------
    def _draw_rig_ambient(surface, pt, _w, f, phase, action):
        """Idle hidup: mote naik, percik antena; walk: debu belakang."""
        P = _NS_morgath.PALETTE
        if action == "walk":
            for i in range(3):
                t = (phase * 0.2 + i / 3.0) % 1.0
                mx = -f * (24 + i * 10) - int(t * 12)
                my = 50 - t * 24
                p = pt(mx, my)
                _NS_morgath._aacircle(surface,
                                      (*P["robe_edge"], int(100 * (1 - t))),
                                      p, _w(1.4))
            return
        # mote sihir naik dari hem
        for i in range(3):
            t = (phase * 0.16 + i / 3.0) % 1.0
            mx = math.sin(phase + i * 2.1) * (24 + i * 6)
            my = 36 - t * 110
            p = pt(mx, my)
            _NS_morgath._rect(surface, (*P["arc_mid"], int(140 * (1 - t))),
                              (p[0], p[1], _w(1.2), _w(1.2)))
            _NS_morgath._rect(surface, (*P["arc_hot"], int(110 * (1 - t))),
                              (p[0], p[1], _w(0.8), _w(0.8)))
        # percik antena sesekali (deterministik, aman cache; jitter di
        # ruang lokal lewat _w supaya profil skala boss/lane identik;
        # puncak dijaga <= CY-62 agar tidak menyentuh HP bar boss)
        if int(phase * 3.0) % 8 < 2 and action in ("idle",):
            t0 = pt(-13.5, -70.5)
            t1 = pt(17.25, -70.5)
            _NS_morgath._jagged_line(surface, (*P["arc_light"], 160),
                                     t0, t1, jitter=_w(2), segments=4,
                                     width=_w(1))

    def _mor_draw_masterwork_details(surface, pt, _w, f, phase, action):
        """Micro-detail khusus portrait LOD (Hero Shop)."""
        P = _NS_morgath.PALETTE
        # jahitan hood (tick silang)
        for i in range(4):
            xx = -9 + i * 5
            _NS_morgath._aaline(surface, P["robe_edge"], pt(xx, -60 + i),
                                pt(xx + 2, -57 + i), _w(1))
            _NS_morgath._aaline(surface, P["robe_edge"], pt(xx + 2, -60 + i),
                                pt(xx, -57 + i), _w(1))
        # facet kristal ekstra
        _NS_morgath._aaline(surface, P["orb_light"],
                            pt(3 - 5, -46.5 - 5), pt(3 + 5, -46.5 - 5),
                            _w(1))
        # goresan pauldron + kilau rivet
        for a in (-0.7, -0.2, 0.3):
            _NS_morgath._aaline(surface, P["armor_mid"], pt(-24, -36),
                                pt(-24 - math.cos(a) * 9,
                                   -36 + math.sin(a) * 9), _w(1))
        _NS_morgath._aaline(surface, P["armor_mid"], pt(24, -38),
                            pt(24 + 7, -41), _w(1))
        # serat jubah hem
        for i in range(6):
            _NS_morgath._aaline(surface,
                                P["robe_edge"] if i % 2 else P["robe_mid"],
                                pt(-24 + i * 9, 52),
                                pt(-22 + i * 9, 60 - (i % 3)), _w(1))
        # halaman grimoire
        _NS_morgath._aaline(surface, P["page_light"], pt(-23, 3),
                            pt(-21, 10), _w(1))
        # rune staff
        for i in range(3):
            _NS_morgath._rect(surface, P["gold_shine"],
                              (pt(-23 + i * 2, -20 + i * 14)[0],
                               pt(-23 + i * 2, -20 + i * 14)[1],
                               _w(1), _w(1)))
        # kilau campuran khusus portrait (warna BARU = LOD lebih kaya)
        _NS_morgath._aaline(surface,
                            _NS_morgath._mix(P["orb_light"], P["white"],
                                             .4),
                            pt(1, -58), pt(7, -56), _w(1))
        _NS_morgath._aaline(surface,
                            _NS_morgath._mix(P["gold_light"], P["white"],
                                             .5),
                            pt(-11, -61.5), pt(0, -64), _w(1))
        # skala material portrait (masing-masing mix = warna unik baru)
        _NS_morgath._aaline(surface,
                            _NS_morgath._mix(P["orb_mid"], P["orb_hot"],
                                             .45),
                            pt(-5, -52), pt(5, -52), _w(1))
        _NS_morgath._aaline(surface,
                            _NS_morgath._mix(P["robe_light"],
                                             P["robe_edge"], .55),
                            pt(-13, -47), pt(-9, -44), _w(1))
        _NS_morgath._aaline(surface,
                            _NS_morgath._mix(P["armor_light"], P["white"],
                                             .3),
                            pt(13, -41), pt(18, -39), _w(1))
        _NS_morgath._rect(surface,
                          _NS_morgath._mix(P["gold_mid"],
                                           P["gold_shine"], .4),
                          (pt(9, -47)[0], pt(9, -47)[1], _w(1), _w(1)))
        _NS_morgath._rect(surface,
                          _NS_morgath._mix(P["arc_mid"], P["white"], .35),
                          (pt(-13, -68)[0], pt(-13, -68)[1],
                           _w(1), _w(1)))
        _NS_morgath._rect(surface,
                          _NS_morgath._mix(P["flux_mid"], P["white"], .4),
                          (pt(13, -68)[0], pt(13, -68)[1],
                           _w(1), _w(1)))
        _NS_morgath._aaline(surface,
                            _NS_morgath._mix(P["staff_mid"],
                                             P["staff_light"], .5),
                            pt(-27, 2), pt(-25, 10), _w(1))
        _NS_morgath._rect(surface,
                          _NS_morgath._mix(P["leather_light"],
                                           P["gold_mid"], .45),
                          (pt(5, 12)[0], pt(5, 12)[1], _w(1), _w(1)))

    # ============================================================
    # LIGHTNING PROJECTILE (basic attack) — BOLT MEWAH v2.3
    # ============================================================
    def _glow_sprite(radius=24):
        """Bloom radial prosedural (cache statis per ukuran, tanpa
        image.load)."""
        key = "morgath_bolt_glow_%d" % int(radius)

        def build():
            r = int(radius)
            s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            c = r + 1
            for rr, k, al in ((r, "arc_dark", 36),
                              (int(r * .68), "arc_mid", 64),
                              (int(r * .44), "arc_light", 104),
                              (int(r * .22), "arc_hot", 168)):
                _NS_morgath._aacircle(s, (*_NS_morgath.PALETTE[k], al),
                                      (c, c), rr)
            return s
        return _NS_morgath._static(key, build)

    def _draw_lightning_projectile(surface, boss, x, y, progress):
        """Bolt petir mewah dari telapak (v2.3) — bukan garis polos:
        chord 3-lapis morph per-frame dengan offset heliks + echo arc
        menyambar kembali + ghost chord dobel-eksposur + pulse energi
        berjalan + mach rings + corona berputar + ranting letik +
        trail after-image hollow + mote bara berwarna + bloom radial
        + percik las di telapak + glint orbit + benturan berlapis
        (scorch, ring ganda + ring tunda, bintang 8, garis radial,
        fork jagged, serpihan berekor). 100% prosedural &
        deterministik per-frame."""
        if progress < 0.55:
            return

        # ═══ KOMPENSASI SCALE HERO ═══
        # Beam digambar di ruang dunia skala 1.0 (beam pass hero &
        # jalur boss). _render_scale mungkin tersisa di-set; kompensasi
        # tetap dipasang supaya panggilan langsung (tool preview) juga
        # identik dengan versi mini boss.
        inv = 1.0 / max(0.3, float(getattr(boss, "_render_scale", 1.0)
                                   or 1.0))

        def W(w):
            return max(1, int(math.ceil(w * inv)))

        def _A(a):
            return _NS_morgath._alpha(a * min(1.4, inv))

        def R(r):
            return max(1, int(round(r * inv)))

        def clamp_xy(px, py):
            # efek tidak boleh lolos dari canvas cache (clamp kontrak)
            return (max(0, min(surface.get_width() - 1, int(px))),
                    max(0, min(surface.get_height() - 1, int(py))))

        def blit_glow(gx, gy, alpha, grow=1.0):
            r = max(8, int(round(24 * grow * inv)))
            spr = _NS_morgath._glow_sprite(r)
            spr.set_alpha(_A(alpha))
            surface.blit(spr, (int(gx - r - 1), int(gy - r - 1)))
            spr.set_alpha(255)

        facing = getattr(boss, "_mor_attack_dir", None)
        if facing is None:
            facing = boss.direction
        if hasattr(boss, "_mor_attack_target"):
            scl = float(getattr(boss, "_render_scale", 1.0) or 1.0)
            ox, oy = boss._mor_attack_target
            tx, ty = int(x + ox / scl), int(y + oy / scl)
        else:
            tx, ty = _NS_morgath._target_position(boss, x, y)

        # Lahir dari TELAPAK cast rig (MOR_MUZZLE) di semua skala render
        mdx, mdy = _NS_morgath._muzzle_offset_world()
        start_x = x + facing * int(round(mdx * inv))
        start_y = y + int(round(mdy * inv))

        t = (progress - 0.55) / 0.45
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        ph = float(getattr(boss, "pulse", 0.0))
        P = _NS_morgath.PALETTE

        dx = bx - start_x
        dy = by - start_y
        length = max(1.0, math.hypot(dx, dy))
        nx, ny = -dy / length, dx / length

        def chord_pt(s):
            return (int(start_x + dx * s), int(start_y + dy * s))

        # ═══ 0) BLOOM RADIAL (telapak + kepala) ═══
        blit_glow(bx, by, 205)
        blit_glow(start_x, start_y, 145, grow=0.6)

        # ═══ 1) GHOST CHORD (dobel-eksposur, offset tegak lurus) ═══
        # Echo samar seluruh bentuk chord, digeser sedikit — memberi
        # kedalaman listrik (2 citra sekaligus) sebelum chord utama.
        goff = -1.6 * inv
        for i in range(1, 8):
            s0 = (i - 1) / 7
            s1 = i / 7
            a0 = (start_x + dx * s0 + nx * goff,
                  start_y + dy * s0 + ny * goff)
            a1 = (start_x + dx * s1 + nx * goff,
                  start_y + dy * s1 + ny * goff)
            _NS_morgath._aaline(surface, (*P["arc_darkest"], _A(70)),
                                (int(a0[0]), int(a0[1])),
                                (int(a1[0]), int(a1[1])), W(1))

        # ═══ 2) ECHO ARC — leader menyambar balik ke chord ═══
        # 2 busur petir melompat keluar lalu menyambung kembali ke
        # jalur utama (sisi kiri/kanan), khas sambaran listrik asli.
        for k in range(2):
            s_a = 0.22 + 0.36 * k
            s_b = s_a + 0.20
            p_a = chord_pt(s_a)
            p_b = chord_pt(s_b)
            side = 1.0 if (k + int(progress * 26)) % 2 == 0 else -1.0
            bulge = (9.0 + k * 4.0) * inv * side
            m1 = (start_x + dx * (s_a + 0.07) + nx * bulge,
                  start_y + dy * (s_a + 0.07) + ny * bulge)
            m2 = (start_x + dx * (s_a + 0.13) + nx * bulge * 0.55,
                  start_y + dy * (s_a + 0.13) + ny * bulge * 0.55)
            pts = [p_a, (int(m1[0]), int(m1[1])),
                   (int(m2[0]), int(m2[1])), p_b]
            for li, (key, al, w) in enumerate(
                    (("arc_dark", 120, W(2)), ("arc_light", 190, W(1)))):
                for j in range(1, len(pts)):
                    _NS_morgath._aaline(surface, (*P[key], _A(al)),
                                        pts[j - 1], pts[j], w)

        # ═══ 3) CHORD UTAMA: polyline berliku morph hidup ═══
        segs = 7
        pts0 = [(start_x, start_y)]
        for i in range(1, segs + 1):
            s0 = (i - 1) / segs
            s1 = i / segs
            sm = (s0 + s1) / 2
            off = (math.sin(sm * 9.5 + ph * 2.1 + progress * 13.7)
                   + math.sin(sm * 23.0 - ph * 1.3 + progress * 21.3) * .45)
            off *= (4.8 if i % 2 else 3.4) * inv
            ex = start_x + dx * s1
            ey = start_y + dy * s1
            if i == segs:
                ex, ey = bx, by
            pts0.append((int(start_x + dx * sm + nx * off),
                         int(start_y + dy * sm + ny * off)))
            pts0.append((int(ex), int(ey)))
        # 3 lapis pita: lebar menirus + offset heliks antar lapis
        for li, (key, base_w, al) in enumerate(
                (("arc_dark", 5, 130), ("arc_mid", 3, 210),
                 ("arc_light", 1, 245))):
            off = li * 0.9 * inv
            prev = (pts0[0][0] + int(nx * off), pts0[0][1] + int(ny * off))
            for j in range(1, len(pts0)):
                s = (j - 1) / (len(pts0) - 1)
                w = max(1, int(round(base_w * (1.0 - 0.72 * s) * inv)))
                p = (pts0[j][0] + int(nx * off), pts0[j][1] + int(ny * off))
                _NS_morgath._aaline(surface, (*P[key], _A(al)), prev, p, w)
                prev = p
        # Inti menyala di 40% ujung dekat kepala (fokus benturan)
        for j in range(max(0, len(pts0) - 3), len(pts0) - 1):
            _NS_morgath._aaline(surface, (*P["arc_hot"], 255),
                                pts0[j], pts0[j + 1], W(1))

        # ═══ 4) PULSE ENERGI BERJALAN (menyusul kepala) ═══
        # Pita putih menyala berjalan dari telapak menuju kepala 1.6x
        # lebih cepat — ledakan energi di sepanjang lintasan.
        s_band = min(1.0, t * 1.6)
        for k in range(2):
            s_b0 = max(0.0, s_band - 0.045)
            s_b1 = s_band + 0.02
            c0 = (start_x + dx * s_b0 + nx * (0.6 - k) * inv,
                  start_y + dy * s_b0 + ny * (0.6 - k) * inv)
            c1 = (start_x + dx * s_b1 + nx * (0.6 - k) * inv,
                  start_y + dy * s_b1 + ny * (0.6 - k) * inv)
            _NS_morgath._aaline(surface,
                                (*P["arc_shine" if k == 0 else "arc_hot"],
                                 _A(200)),
                                (int(c0[0]), int(c0[1])),
                                (int(c1[0]), int(c1[1])), W(2 - k))
        cxp, cyp = clamp_xy(start_x + dx * s_band, start_y + dy * s_band)
        _NS_morgath._rect(surface, (*P["white"], 255),
                          (cxp, cyp, W(2), W(2)))

        # ═══ 5) RANTING LETIK MENYIMPANG (sisi selang-seling) ═══
        for k, s in ((2, 0.26), (3, 0.46), (4, 0.66)):
            side = 1 if (k + int(progress * 20)) % 2 == 0 else -1
            ax = int(start_x + dx * s)
            ay = int(start_y + dy * s)
            bx2 = int(ax + nx * side * (8 + k) * inv + dx * .12 * inv)
            by2 = int(ay + ny * side * (8 + k) * inv + dy * .12 * inv)
            _NS_morgath._jagged_line(surface, (*P["arc_dark"], _A(150)),
                                     (ax, ay), (bx2, by2),
                                     jitter=2.5 * inv, segments=2,
                                     width=W(2))
            _NS_morgath._jagged_line(surface, (*P["arc_hot"], _A(220)),
                                     (ax, ay), (bx2, by2),
                                     jitter=1.5 * inv, segments=2,
                                     width=W(1))

        # ═══ 6) MACH RINGS (wake kecepatan di belakang kepala) ═══
        # Cincin tipis membesar makin jauh di belakang kepala bolt.
        for g in (1, 2, 3):
            gt = max(0.02, t - 0.045 * g)
            gx, gy = chord_pt(gt)
            _NS_morgath._aacircle(surface,
                                  (*P["arc_mid"], _A(95 - g * 22)),
                                  (gx, gy), R(6 + g * 3), W(1))

        # ═══ 7) TRAIL AFTER-IMAGE HOLLOW + MOTE BARA ═══
        for g in (3, 2, 1):
            gt = max(0.0, t - 0.055 * g)
            gx = int(start_x + dx * gt)
            gy = int(start_y + dy * gt)
            ga = _A(62 - g * 13)
            _NS_morgath._aacircle(surface, (*P["arc_dark"], ga),
                                  (gx, gy), R(4 + g))
            _NS_morgath._aacircle(surface, (*P["arc_mid"], ga + 30),
                                  (gx, gy), R(5 + g), W(1))
        # Mote bara listrik berjatuhan (2 warna, berekor 2 px)
        for i in range(7):
            mt = (0.14 + 0.11 * i
                  + _NS_morgath._hash01(i + int(progress * 30)) * 0.1)
            mt = max(0.0, min(1.0, mt))
            mx = start_x + dx * mt
            my = start_y + dy * mt + (t - mt) * 16 * inv
            key = "arc_mid" if i % 2 == 0 else "flux_light"
            cx0, cy0 = clamp_xy(mx, my)
            _NS_morgath._rect(surface, (*P[key], _A(165)),
                              (cx0, cy0, W(1), W(2)))

        # ═══ 8) KEPALA BOLT: flare 5 lapis + corona + paku + glint ═══
        for radius, key, al in ((10, "arc_darkest", 80),
                                (7, "arc_dark", 140),
                                (5, "arc_mid", 205),
                                (3, "arc_light", 255),
                                (2, "arc_hot", 255)):
            _NS_morgath._aacircle(surface, (*P[key], _A(al)),
                                  (bx, by), R(radius))
        cx0, cy0 = clamp_xy(bx, by)
        _NS_morgath._rect(surface, (*P["white"], 255),
                          (cx0, cy0, W(1), W(1)))
        # Corona 6 paku berputar (2 jagged + 4 lurus, ujung menyala)
        # Semua ujung di luar disk flare kepala (r<=10) supaya tetap
        # putih menyala, tidak tertelan pita gelap flare.
        for i in range(6):
            ang = ph * 2.0 + i * math.pi / 3 + progress * 4.0
            ln = (15.0 if i % 3 == 0 else (13.0 if i % 2 == 0 else 11.0))
            ln *= inv
            px2 = int(math.cos(ang) * ln)
            py2 = int(math.sin(ang) * ln * 0.8)
            sx2 = bx + int(math.cos(ang) * 3 * inv)
            sy2 = by + int(math.sin(ang) * 3 * inv)
            if i % 3 == 0:
                _NS_morgath._jagged_line(surface, P["arc_hot"],
                                         (sx2, sy2), (bx + px2, by + py2),
                                         jitter=1.8 * inv, segments=2,
                                         width=W(1))
            else:
                _NS_morgath._aaline(surface, (*P["arc_hot"], _A(175)),
                                    (sx2, sy2), (bx + px2, by + py2), W(1))
            cx2, cy2 = clamp_xy(bx + px2, by + py2)
            _NS_morgath._rect(surface, (*P["arc_shine"], _A(220)),
                              (cx2, cy2, W(1), W(1)))
        # Dua paku cahaya silang berputar halus di inti
        for i in range(2):
            ga = ph * 2.5 + i * math.pi / 2 + progress * 4.0
            hx = int(math.cos(ga) * 5 * inv)
            hy = int(math.sin(ga) * 4 * inv)
            _NS_morgath._aaline(surface, (*P["arc_hot"], _A(210)),
                                (bx - hx, by - hy), (bx + hx, by + hy),
                                W(1))
        # Glint orbit 3 titik cahaya memutar
        for i in range(3):
            ga = ph * 5.0 + i * math.pi * 2 / 3 + progress * 6.0
            gx = bx + math.cos(ga) * 5.5 * inv
            gy = by + math.sin(ga) * 4.0 * inv
            gx, gy = clamp_xy(gx, gy)
            _NS_morgath._rect(surface, (*P["arc_shine"], _A(235)),
                              (int(gx), int(gy), W(1), W(1)))

        # ═══ 9) PERCIK LAS DI TELAPAK (menyala sepanjang flight) ═══
        # 3 busur kecil menyembur dari muzzle, panjang berkedip-kedip.
        flick = 0.6 + 0.4 * _NS_morgath._hash01(int(progress * 24))
        for i in range(3):
            ang = -0.9 + i * 0.55 + ph * 0.7
            ln = (4 + i * 2.5) * flick * inv
            _NS_morgath._aaline(surface, (*P["arc_hot"], _A(190)),
                                (start_x, start_y),
                                (int(start_x + math.cos(ang) * ln),
                                 int(start_y + math.sin(ang) * ln)),
                                W(1))
        # Bintang pelepasan saat bolt lahir
        if t < 0.25:
            mt2 = t / 0.25
            _NS_morgath._spark_star(surface, start_x, start_y,
                                    int((4 + 6 * (1 - mt2)) * inv),
                                    P["arc_shine"], _A(int(235 * (1 - mt2))),
                                    spikes=6, rot=0.3 + ph, core=P["white"])

        # ═══ 11) BENTURAN BERLAPIS (t > 0.88) ═══
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int((10 + st * 26) * inv)
            alpha = _A(230 * (1 - st))
            # scorch glow di titik benturan
            blit_glow(tx, ty, int(150 * (1 - st)), grow=1.5)
            # ring ganda + ring tunda (micro-ring menyusul)
            _NS_morgath._aacircle(surface, (*P["arc_darkest"], alpha),
                                  (tx, ty), R(radius + 3), W(3))
            _NS_morgath._aacircle(surface, (*P["arc_mid"], alpha),
                                  (tx, ty), R(radius), W(2))
            _NS_morgath._aacircle(surface, (*P["arc_shine"], alpha),
                                  (tx, ty), R(max(1, radius - 6)), W(1))
            st2 = max(0.0, st - 0.35) / 0.65
            _NS_morgath._aacircle(
                surface, (*P["arc_hot"], _A(200 * (1 - st2))),
                (tx, ty), R(max(1, int(radius * 0.55))), W(1))
            _NS_morgath._spark_star(surface, tx, ty,
                                    int((9 + st * 15) * inv),
                                    P["arc_shine"], int(225 * (1 - st)),
                                    spikes=8, rot=0.5, core=P["white"])
            # 8 garis radial lurus
            for i in range(8):
                ang = i * math.pi / 4 + progress * 2.0
                ex = int(tx + math.cos(ang) * radius * 1.05 * inv)
                ey = int(ty + math.sin(ang) * radius * 0.8 * inv)
                _NS_morgath._aaline(surface, (*P["arc_hot"], alpha),
                                    (tx, ty), (ex, ey), W(1))
            # 4 fork jagged di antara garis radial
            for i in range(4):
                ang = (i + 0.5) * math.pi / 2 + progress * 2.0
                ex = int(tx + math.cos(ang) * radius * 1.25 * inv)
                ey = int(ty + math.sin(ang) * radius * 0.95 * inv)
                _NS_morgath._jagged_line(surface, P["arc_shine"],
                                         (tx, ty), (ex, ey),
                                         jitter=2.0 * inv, segments=2,
                                         width=W(1))
            # 8 serpihan deterministik berekor
            for i in range(8):
                a = 0.7 + i * 0.72 + _NS_morgath._hash01(i * 5) * 0.6
                r = (7 + st * 24) * inv
                dx2 = math.cos(a) * r
                dy2 = math.sin(a) * r * 0.55 - st * st * 8 * inv
                cx2, cy2 = clamp_xy(tx + dx2, ty + dy2)
                _NS_morgath._rect(surface, (*P["arc_light"], alpha),
                                  (cx2, cy2, W(1), W(1)))
                cx3, cy3 = clamp_xy(tx + dx2 * 0.6, ty + dy2 * 0.6)
                _NS_morgath._rect(surface, (*P["arc_mid"], alpha),
                                  (cx3, cy3, W(1), W(1)))



    # ============================================================
    # SHADOW / ARC AURA / GROUND RUNE (static cached)
    # ============================================================
    def _draw_shadow(surface, x, y):
        """Bayangan mengikuti lebar hem rig (cached - dibangun sekali)."""
        def build():
            shadow = pygame.Surface((130, 26), pygame.SRCALPHA)
            for radius in range(13, 0, -1):
                alpha = max(0, (13 - radius) * 15)
                pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                    (13 - radius, 13 - radius,
                                     104 + radius * 2, radius * 2))
            pygame.draw.ellipse(shadow, (2, 5, 12, 190), (8, 7, 114, 12))
            return shadow
        shadow = _NS_morgath._static("shadow", build)
        surface.blit(shadow, (x - 65, y - 13))

    def _draw_arc_aura(surface, x, y, phase):
        """Aura elektrik biru di belakang boss (cached) + sparkle &
        busur petir deterministik."""
        P = _NS_morgath.PALETTE
        pulse = math.sin(phase * 0.6) * 0.25 + 0.75

        def build():
            aura = pygame.Surface((280, 240), pygame.SRCALPHA)
            for radius in range(105, 8, -5):
                # Falloff ^4: alpha >= 100 hanya di r <= ~25 px canvas,
                # SELALU di dalam siluet badan di kedua jalur (boss 0.6x
                # maupun lane native 1.38x) - mask pengukuran pipeline
                # (_BODY_ALPHA_THRESHOLD=100) melihat badan, bukan aura.
                f = max(0.0, 1.0 - radius / 105.0)
                alpha = _NS_morgath._alpha(255 * f ** 4)
                if alpha > 0:
                    _NS_morgath._aacircle(aura,
                                          (*P["arc_darkest"], alpha),
                                          (140, 120), radius)
            for radius in range(66, 8, -4):
                f = max(0.0, 1.0 - radius / 66.0)
                alpha = _NS_morgath._alpha(230 * f ** 4)
                if alpha > 0:
                    _NS_morgath._aacircle(aura, (*P["arc_dark"], alpha),
                                          (140, 120), radius)
            return aura
        aura = _NS_morgath._static("arc_aura", build)
        if pulse < 0.92:
            faded = aura.copy()
            faded.set_alpha(int(255 * pulse))
            surface.blit(faded, (x - 140, y - 120))
        else:
            surface.blit(aura, (x - 140, y - 120))

        # Floating electric sparkles (deterministik per phase; alpha di
        # bawah ambang 100 supaya tidak ikut terukur sebagai badan).
        for i in range(12):
            angle = phase * 0.4 + i * math.pi / 6
            r = 48 + int(math.sin(phase + i) * 18)
            sx = x + int(math.cos(angle) * r)
            sy = y - 8 + int(math.sin(angle) * r * 0.5)
            alpha = _NS_morgath._alpha(72 + math.sin(phase * 4 + i) * 20)
            pygame.draw.rect(surface, (*P["arc_mid"], alpha), (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*P["arc_hot"], alpha), (sx, sy, 1, 1))

        # Busur petir sesekali antar sparkle (frame-gated deterministik)
        arc_frame = int(phase * 3) % 8
        if arc_frame < 2:
            for k in range(2):
                a1 = phase * 0.4 + k * math.pi / 6
                a2 = phase * 0.4 + (k + 3) * math.pi / 6
                r = 48
                p1 = (x + int(math.cos(a1) * r),
                      y - 8 + int(math.sin(a1) * r * 0.5))
                p2 = (x + int(math.cos(a2) * r),
                      y - 8 + int(math.sin(a2) * r * 0.5))
                _NS_morgath._jagged_line(surface, (*P["arc_light"], 88),
                                         p1, p2, jitter=4.5, segments=5,
                                         width=1)

    def _draw_ground_rune(surface, x, y, phase, skill):
        """Rune lingkaran biru - rapat di bawah hem jubah (cached).
        Tidak boleh lebih lebar/lebih terang dari badan."""
        P = _NS_morgath.PALETTE
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75

        def build():
            ring = pygame.Surface((112, 38), pygame.SRCALPHA)
            pygame.draw.ellipse(ring, (*P["arc_darkest"], 190),
                                (4, 13, 104, 20), 2)
            pygame.draw.ellipse(ring, (*P["arc_dark"], 200),
                                (12, 16, 88, 14), 1)
            pygame.draw.ellipse(ring, (*P["arc_mid"], 150),
                                (26, 18, 60, 10), 1)
            return ring
        ring = _NS_morgath._static("ground_rune", build)
        surface.blit(ring, (x - 56, y - 19))

        # Rune spokes (pendek, di dalam cincin - dinamis murah)
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = x + int(math.cos(angle) * 28)
            y1 = y + int(math.sin(angle) * 6)
            x2 = x + int(math.cos(angle) * 46)
            y2 = y + int(math.sin(angle) * 10)
            pygame.draw.line(surface, (*P["arc_dark"], 190),
                             (x1, y1), (x2, y2), 1)

        if skill:
            col = {"w": P["flux_mid"], "e": P["arc_hot"],
                   "r": P["arc_shine"], "q": P["arc_light"]}.get(
                       skill, P["arc_hot"])
            pygame.draw.ellipse(surface,
                                (*col, _NS_morgath._alpha(150 * pulse)),
                                (x - 44, y - 14, 88, 28), 1)

    # ============================================================
    # AKTIVASI SKILL (shared): shockwave + bintang + mote
    # ============================================================
    def _draw_skill_activation(surface, boss, x, y, skill, timer, phase):
        """Gelombang kejut aktivasi (12 frame pertama tiap skill)."""
        if skill not in _NS_morgath.SKILL_DUR:
            return
        dur = _NS_morgath.SKILL_DUR[skill]
        age = dur - timer
        if not (0 <= age < 12):
            return
        P = _NS_morgath.PALETTE
        fs = _NS_morgath._fx_scale(boss)
        st = age / 12.0
        a = _NS_morgath._alpha(235 * (1 - st))
        col = {"q": P["arc_light"], "w": P["flux_light"],
               "e": P["arc_hot"], "r": P["arc_shine"]}.get(skill,
                                                           P["arc_light"])
        gy = y + _NS_morgath._ground_dy()
        rr = int((24 + st * 70) * fs)
        rr = min(rr, _NS_morgath._ring_r(boss, 96, surface))
        _NS_morgath._aacircle(surface, (*col, a), (x, gy), rr, 2)
        _NS_morgath._aacircle(surface, (*P["white"], a),
                              (x, gy), max(1, rr // 2), 1)
        _NS_morgath._spark_star(surface, x, gy,
                                int((14 - st * 6) * fs), col,
                                int(210 * (1 - st)), spikes=6, rot=0.35,
                                core=P["white"])
        for i in range(6):
            ang = i * math.pi / 3 + st * 2.0
            mx = x + math.cos(ang) * rr * 0.6
            my = gy + math.sin(ang) * rr * 0.3 - st * 18 * fs
            _NS_morgath._rect(surface, (*col, a), (int(mx), int(my),
                                                   2, 2))



    # ============================================================
    # SKILL Q: SPARK WRAITH (homing electric orb)
    # 3 fase: TELEGRAPH (chevron ke target) -> AKTIVASI (vortex di
    # telapak) -> FLIGHT (trail berlapis + glint) + IMPACT bintang.
    # ============================================================
    def _draw_sparkwraith_ground(surface, boss, x, y, timer, phase):
        """TELEGRAPH: chevron berbaris menuju target + splat marker."""
        P = _NS_morgath.PALETTE
        dur = _NS_morgath.SKILL_DUR["q"]
        progress = max(0.0, min(1.0, 1 - timer / dur))
        fs = _NS_morgath._fx_scale(boss)
        if progress > 0.25:
            return
        fade = int(210 * (0.25 - progress) / 0.25)
        sx, sy = _NS_morgath._skill_hand_canvas(boss, x, y, "q")
        tx, ty = _NS_morgath._target_position(boss, x, y)
        ang = math.atan2(ty - sy, tx - sx)
        dist = math.hypot(tx - sx, ty - sy)
        # garis pandu putus-putus
        for i in range(int(dist // (12 * fs)) + 1):
            t0 = i * 12 * fs
            p0 = (sx + math.cos(ang) * t0, sy + math.sin(ang) * t0)
            p1 = (sx + math.cos(ang) * (t0 + 6 * fs),
                  sy + math.sin(ang) * (t0 + 6 * fs))
            _NS_morgath._aaline(surface, (*P["arc_dark"], fade),
                                p0, p1, 1)
        # chevron berbaris (marching)
        for i in range(6):
            tt = ((phase * 0.35 + i / 6.0) % 1.0)
            cx_ = sx + math.cos(ang) * tt * dist
            cy_ = sy + math.sin(ang) * tt * dist
            _NS_morgath._chevron(surface, cx_, cy_, ang, 9 * fs,
                                 P["arc_light"], fade, width=2)
        # splat marker di target (2 ring putus-putus berlawanan)
        _NS_morgath._dashed_ring(surface, tx, ty, 13 * fs, P["arc_mid"],
                                 fade, phase * 2, segments=8, thick=2,
                                 span=0.5)
        _NS_morgath._dashed_ring(surface, tx, ty, 19 * fs, P["arc_light"],
                                 fade, -phase * 1.6, segments=10, thick=2,
                                 span=0.4)

    def _draw_sparkwraith_foreground(surface, boss, x, y, timer, phase):
        """AKTIVASI vortex + FLIGHT mewah + IMPACT."""
        P = _NS_morgath.PALETTE
        dur = _NS_morgath.SKILL_DUR["q"]
        progress = max(0.0, min(1.0, 1 - timer / dur))
        fs = _NS_morgath._fx_scale(boss)
        tx, ty = _NS_morgath._target_position(boss, x, y)

        if progress < 0.4:
            # ── AKTIVASI: vortex 2 lengan spiral berlawanan + droplet ──
            t = min(1.0, progress / 0.25)
            cx_, cy_ = _NS_morgath._skill_hand_canvas(boss, x, y, "q")
            for arm in range(2):
                for step in range(14):
                    s_t = step / 14.0
                    ang = (phase * 3.0 * (1 if arm == 0 else -1)
                           + arm * math.pi + s_t * math.pi * 2.6)
                    s_r = int(20 * (1 - s_t) * t * fs)
                    px_ = cx_ + math.cos(ang) * s_r
                    py_ = cy_ + math.sin(ang) * s_r
                    _NS_morgath._rect(
                        surface,
                        (*P["arc_light" if arm == 0 else "arc_mid"],
                         _NS_morgath._alpha(200 * (1 - s_t) * t)),
                        (int(px_), int(py_), 2, 2))
            for i in range(6):
                ang = phase * 4 + i * math.pi / 3
                d = (8 + t * 10) * fs
                _NS_morgath._aacircle(
                    surface, (*P["arc_hot"], int(200 * t)),
                    (int(cx_ + math.cos(ang) * d),
                     int(cy_ + math.sin(ang) * d)), max(1, int(2 * fs)))
            _NS_morgath._spark_star(surface, cx_, cy_, int(12 * t * fs),
                                    P["arc_shine"], int(220 * t),
                                    spikes=6, rot=phase, core=P["white"])
            for i in range(3):
                ang = phase * 6 + i * 2.1
                tip = (cx_ + math.cos(ang) * (12 + t * 8) * fs,
                       cy_ + math.sin(ang) * (12 + t * 8) * fs)
                _NS_morgath._jagged_line(surface, P["arc_light"],
                                         (cx_, cy_), tip, jitter=2,
                                         segments=3, width=1)
            return

        # ── FLIGHT: orb menuju target (kurva) + trail 2-tone + glint ──
        t = (progress - 0.4) / 0.5
        t = min(1.0, t)
        start_x, start_y = _NS_morgath._skill_hand_canvas(boss, x, y, "q")
        mid_x = (start_x + tx) / 2
        mid_y = min(start_y, ty) - 45 * fs
        bx = int((1 - t) ** 2 * start_x + 2 * (1 - t) * t * mid_x
                 + t ** 2 * tx)
        by = int((1 - t) ** 2 * start_y + 2 * (1 - t) * t * mid_y
                 + t ** 2 * ty)

        # trail berlapis 2-tone
        for i in range(8):
            trail_t = max(0.0, t - i * 0.06)
            px_ = int((1 - trail_t) ** 2 * start_x
                      + 2 * (1 - trail_t) * trail_t * mid_x
                      + trail_t ** 2 * tx)
            py_ = int((1 - trail_t) ** 2 * start_y
                      + 2 * (1 - trail_t) * trail_t * mid_y
                      + trail_t ** 2 * ty)
            alpha = _NS_morgath._alpha(240 - i * 28)
            size = max(1, int((12 - i) * fs))
            _NS_morgath._aacircle(surface, (*P["arc_darkest"], alpha),
                                  (px_, py_), size)
            _NS_morgath._aacircle(surface, (*P["arc_dark"], alpha),
                                  (px_, py_), max(1, size - int(2 * fs)))
            _NS_morgath._aacircle(surface, (*P["arc_mid"], alpha),
                                  (px_, py_), max(1, size - int(4 * fs)))
        # kepala orb terang + aura
        for r in range(14, 4, -2):
            alpha = _NS_morgath._alpha(90 * (14 - r) / 14)
            _NS_morgath._aacircle(surface, (*P["arc_light"], alpha),
                                  (bx, by), int(r * fs))
        _NS_morgath._aacircle(surface, P["arc_darkest"], (bx, by),
                              int(11 * fs))
        _NS_morgath._aacircle(surface, P["arc_dark"], (bx, by),
                              int(9 * fs))
        _NS_morgath._aacircle(surface, P["arc_mid"], (bx, by),
                              int(6 * fs))
        _NS_morgath._aacircle(surface, P["arc_light"], (bx, by),
                              int(4 * fs))
        _NS_morgath._aacircle(surface, P["arc_shine"], (bx, by),
                              int(2 * fs))
        pygame.draw.rect(surface, P["white"], (bx, by, 1, 1))
        # glint orbit di ujung orb
        for i in range(2):
            ga = phase * 6 + i * math.pi
            gx = bx + int(math.cos(ga) * 6 * fs)
            gy = by + int(math.sin(ga) * 6 * fs)
            pygame.draw.rect(surface, P["white"], (gx, gy, 1, 1))
        # tendril listrik berputar
        for i in range(5):
            angle = phase * 6 + i * math.pi * 2 / 5
            tip = (bx + math.cos(angle) * 15 * fs,
                   by + math.sin(angle) * 15 * fs)
            _NS_morgath._jagged_line(surface, P["arc_hot"], (bx, by),
                                     tip, jitter=3, segments=3, width=1)

        # IMPACT
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int((21 + st * 40) * fs)
            radius = min(radius, _NS_morgath._ring_r(boss, 120, surface))
            alpha = _NS_morgath._alpha(240 * (1 - st))
            _NS_morgath._aacircle(surface, (*P["arc_darkest"], alpha),
                                  (tx, ty), radius + 4, 3)
            _NS_morgath._aacircle(surface, (*P["arc_dark"], alpha),
                                  (tx, ty), radius, 3)
            _NS_morgath._aacircle(surface, (*P["arc_light"], alpha),
                                  (tx, ty), max(1, radius - 8), 2)
            _NS_morgath._spark_star(surface, tx, ty,
                                    int((10 + st * 16) * fs), P["arc_shine"],
                                    int(230 * (1 - st)), spikes=8, rot=0.3,
                                    core=P["white"])
            for i in range(10):
                angle_s = i * math.pi / 5
                ex_ = tx + int(math.cos(angle_s) * radius)
                ey_ = ty + int(math.sin(angle_s) * radius * 0.7)
                _NS_morgath._jagged_line(surface, P["arc_shine"],
                                         (tx, ty), (ex_, ey_),
                                         jitter=3, segments=4, width=1)

    # ============================================================
    # SKILL W: FLUX (purple debuff pool at target)
    # 3 fase: TELEGRAPH (ring konvergen) -> AKTIVASI (pilar ungu) ->
    # STEADY (pool berlapis + rune ring berputar + mote/ember naik).
    # ============================================================
    def _draw_flux_ground(surface, boss, x, y, timer, phase):
        """TELEGRAPH + pool berlapis di target (world-space)."""
        P = _NS_morgath.PALETTE
        dur = _NS_morgath.SKILL_DUR["w"]
        progress = max(0.0, min(1.0, 1 - timer / dur))
        fs = _NS_morgath._fx_scale(boss)
        tx, ty = _NS_morgath._target_position(boss, x, y)
        pool_r = 38
        r = int(pool_r * fs)

        if progress < 0.3:
            # ── TELEGRAPH: 3 ring konvergen + chevron ke dalam ──
            t = progress / 0.3
            fade = int(200 * (1 - t * 0.4))
            for i in range(3):
                rr = int((pool_r + (70 - pool_r) * (1 - t)
                          + i * 9) * fs)
                _NS_morgath._aacircle(surface, (*P["flux_mid"], fade),
                                      (tx, ty), rr, 2)
            for i in range(4):
                ang = phase * 1.2 + i * math.pi / 2
                cxp = tx + math.cos(ang) * (r + 14 * fs)
                cyp = ty + math.sin(ang) * (r + 14 * fs) * 0.5
                _NS_morgath._chevron(surface, cxp, cyp,
                                     ang + math.pi, 8 * fs,
                                     P["flux_light"], fade, width=2)
            return

        if r > 3:
            # pool berlapis: rim panas + alpha pool
            _NS_morgath._ellipse(
                surface, (*P["flux_hot"], 120),
                (tx - r - 3, ty - (r + 3) // 3,
                 (r + 3) * 2, (r + 3) * 2 // 3), 2)
            _NS_morgath._ellipse(surface, (*P["flux_darkest"], 240),
                                 (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            _NS_morgath._ellipse(surface, (*P["flux_dark"], 220),
                                 (tx - r + 3, ty - r // 3 + 2,
                                  r * 2 - 6, r * 2 // 3 - 4))
            _NS_morgath._ellipse(surface, (*P["flux_mid"], 180),
                                 (tx - r + 8, ty - r // 3 + 4,
                                  r * 2 - 16, r * 2 // 3 - 8))
            # rune ring ganda berlawanan arah
            _NS_morgath._dashed_ring(surface, tx, ty, r + 7, P["flux_light"],
                                     200, phase * 2.2, segments=10,
                                     thick=2, span=0.55, squash=0.5)
            _NS_morgath._dashed_ring(surface, tx, ty, r + 14, P["flux_mid"],
                                     160, -phase * 1.7, segments=12,
                                     thick=1, span=0.45, squash=0.5)

    def _draw_flux_foreground(surface, boss, x, y, timer, phase):
        """AKTIVASI pilar ungu + STEADY tendril/mote/ember naik."""
        P = _NS_morgath.PALETTE
        dur = _NS_morgath.SKILL_DUR["w"]
        progress = max(0.0, min(1.0, 1 - timer / dur))
        fs = _NS_morgath._fx_scale(boss)
        tx, ty = _NS_morgath._target_position(boss, x, y)
        r = int(38 * fs)

        # ── AKTIVASI: pilar cahaya 3-lapis + bintang + shockwave ──
        if progress < 0.45:
            t = min(1.0, progress / 0.3)
            top = int(ty - min(110 * fs, 230) * (0.5 + 0.5 * (1 - t)))
            for wd, col, al in ((26, P["flux_dark"], 110),
                                (16, P["flux_mid"], 150),
                                (7, P["flux_light"], 200)):
                _NS_morgath._aaline(surface, (*col, int(al * (1 - t))),
                                    (tx, top), (tx, ty), wd)
            _NS_morgath._spark_star(surface, tx, ty,
                                    int(26 * (1 - t * 0.4)), P["flux_hot"],
                                    int(230 * (1 - t)), spikes=8, rot=0.3,
                                    core=P["white"])
            for k, rmax in ((0, 90), (1, 60)):
                rr = int((16 + t * rmax) * fs)
                _NS_morgath._aacircle(
                    surface,
                    (*P["flux_light" if k == 0 else "flux_hot"],
                     int((210 if k == 0 else 140) * (1 - t))),
                    (tx, ty), rr, 2)
            return

        # ── STEADY: tendril + mote + ember naik + core mendidih ──
        for i in range(8):
            wisp_t = (phase * 0.7 + i * 0.15) % 1.0
            angle = i * math.pi / 4 + phase * 0.3
            wx = tx + int(math.cos(angle) * r * 0.6)
            wy_base = ty + int(math.sin(angle) * r * 0.3)
            wy = wy_base - int(wisp_t * 45 * fs)
            alpha = _NS_morgath._alpha(230 * (1 - wisp_t))
            _NS_morgath._aacircle(surface, (*P["flux_dark"], alpha),
                                  (wx, wy), int(7 * fs))
            _NS_morgath._aacircle(surface, (*P["flux_mid"], alpha),
                                  (wx, wy - 1), int(5 * fs))
            _NS_morgath._aacircle(surface, (*P["flux_light"], alpha),
                                  (wx, wy - 1), int(2 * fs))
            _NS_morgath._rect(surface, (*P["flux_hot"], alpha),
                              (wx, wy - 1, 1, 1))
        # mote & ember naik dari pool
        for i in range(10):
            rise_t = (phase * 0.5 + i * 0.1) % 1.0
            angle = i * math.pi * 2 / 10 + phase * 0.4
            sp_r = r * (0.4 + (i % 3) * 0.25)
            sx = tx + int(math.cos(angle) * sp_r)
            sy = ty + int(math.sin(angle) * sp_r * 0.4) - int(rise_t * 30 * fs)
            alpha = _NS_morgath._alpha(200 * (1 - rise_t))
            if alpha > 0:
                _NS_morgath._rect(surface, (*P["flux_light"], alpha),
                                  (sx, sy, 2, 2))
                _NS_morgath._rect(surface, (*P["flux_hot"], alpha),
                                  (sx, sy, 1, 1))
        # central bubbling core
        core_pulse = math.sin(phase * 3) * 0.4 + 0.6
        for cr in range(8, 0, -1):
            alpha = _NS_morgath._alpha(220 * (8 - cr) / 8 * core_pulse)
            _NS_morgath._aacircle(surface, (*P["flux_mid"], alpha),
                                  (tx, ty), int(cr * fs))
        _NS_morgath._aacircle(surface, P["flux_light"], (tx, ty),
                              int(3 * fs))
        _NS_morgath._aacircle(surface, P["flux_hot"], (tx, ty),
                              int(1 * fs))

    # ============================================================
    # SKILL E: MAGNETIC FIELD (dome shield, range = 90 px dunia)
    # 3 fase: TELEGRAPH (ring 90 dunia) -> AKTIVASI (dome bangkit) ->
    # STEADY (kubah 4 lapis + hex grid + spark berputar).
    # ============================================================
    def _dome_static():
        """Kubah statis (cached): 4 lapis busur + hex grid + rim dots."""
        P = _NS_morgath.PALETTE
        dome = pygame.Surface((300, 150), pygame.SRCALPHA)
        center = (150, 148)
        r = 140
        for layer_i, (thickness, col) in enumerate((
                (5, P["arc_dark"]), (3, P["arc_mid"]),
                (2, P["arc_light"]), (1, P["arc_hot"]))):
            arc_rect = pygame.Rect(center[0] - r + layer_i * 3,
                                   center[1] - r + layer_i * 3,
                                   (r - layer_i * 3) * 2,
                                   (r - layer_i * 3) * 2)
            pygame.draw.arc(dome, col, arc_rect, math.pi, math.tau,
                            thickness)
        # hex grid dalam kubah
        for h_row in range(5):
            for h_col in range(-5, 6):
                grid_x = center[0] + h_col * 14 + (h_row % 2) * 7
                grid_y = center[1] - 6 - h_row * 12
                dist = math.hypot(grid_x - center[0],
                                  grid_y - center[1])
                if dist < r - 10:
                    pygame.draw.rect(dome, (*P["arc_mid"], 150),
                                     (grid_x - 1, grid_y - 1, 3, 3), 1)
        # rim dots statis
        for i in range(14):
            ang = math.pi + (i / 13.0) * math.pi
            ax = center[0] + int(math.cos(ang) * r)
            ay = center[1] + int(math.sin(ang) * r)
            pygame.draw.rect(dome, P["arc_hot"], (ax, ay, 2, 2))
            pygame.draw.rect(dome, P["arc_shine"], (ax, ay, 1, 1))
        return dome

    def _draw_magneticfield_ground(surface, boss, x, y, timer, phase):
        """TELEGRAPH: ring jangkauan TEPAT 90 px dunia + ring konvergen
        + chevron kardinal + rune ring berputar."""
        P = _NS_morgath.PALETTE
        dur = _NS_morgath.SKILL_DUR["e"]
        progress = max(0.0, min(1.0, 1 - timer / dur))
        fs = _NS_morgath._fx_scale(boss)
        gy = y + _NS_morgath._ground_dy()
        r = _NS_morgath._ring_r(boss, 90, surface)
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        # ring jangkauan tebal + inner (selalu, semua fase)
        for i, (rr, col) in enumerate(((r, P["arc_mid"]),
                                       (r - int(5 * fs), P["arc_light"]))):
            _NS_morgath._aacircle(surface, (*col,
                                            int((250 - i * 50) * pulse)),
                                  (x, gy), max(1, rr), 2)
        # rune ring berputar
        _NS_morgath._dashed_ring(surface, x, gy, r + 4, P["arc_hot"],
                                 int(190 * pulse), phase * 1.6,
                                 segments=12, thick=2, span=0.5,
                                 squash=0.45)

        if progress < 0.25:
            # ── TELEGRAPH: ring konvergen mengecil ke 90 + chevron ──
            t = progress / 0.25
            fade = int(210 * (1 - t * 0.5))
            for i in range(2):
                rr = int((90 + (128 - 90) * (1 - t) + i * 8) * fs)
                rr = min(rr, _NS_morgath._ring_r(boss, 132, surface))
                _NS_morgath._aacircle(surface, (*P["arc_light"], fade),
                                      (x, gy), rr, 1)
            for i in range(4):
                ang = i * math.pi / 2 + math.pi / 4
                cxp = x + math.cos(ang) * r
                cyp = gy + math.sin(ang) * r * 0.45
                _NS_morgath._chevron(surface, cxp, cyp, ang, 9 * fs,
                                     P["arc_hot"], fade, width=2)
        elif progress < 0.4:
            # ── AKTIVASI: shockwave ganda + bintang ──
            t = (progress - 0.25) / 0.15
            fade = int(230 * (1 - t))
            _NS_morgath._spark_star(surface, x, gy, int(30 * (1 - t * 0.4)),
                                    P["arc_shine"], fade, spikes=8,
                                    rot=0.3, core=P["white"])
            for k, rmax in ((0, 100), (1, 74)):
                rr = int((r + t * rmax * fs * 0.4) * 0.9)
                _NS_morgath._aacircle(
                    surface,
                    (*P["arc_light" if k == 0 else "arc_hot"], fade),
                    (x, gy), rr, 2)

    def _draw_magneticfield_foreground(surface, boss, x, y, timer, phase):
        """STEADY: kubah besar di atas boss (static cached, scaled)."""
        P = _NS_morgath.PALETTE
        dur = _NS_morgath.SKILL_DUR["e"]
        progress = max(0.0, min(1.0, 1 - timer / dur))
        fs = _NS_morgath._fx_scale(boss)
        gy = y + _NS_morgath._ground_dy()
        r = _NS_morgath._ring_r(boss, 90, surface)
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        build_t = 1.0
        if progress < 0.4:
            build_t = max(0.0, (progress - 0.2) / 0.2)   # dome bangkit
            if build_t <= 0:
                return

        dome = _NS_morgath._static("e_dome", _NS_morgath._dome_static)
        dome = pygame.transform.smoothscale(
            dome, (max(2, r * 2), max(2, int(r * build_t))))
        dome.set_alpha(int(150 + 80 * pulse))
        surface.blit(dome, (x - r, gy - int(r * build_t)))

        # spark berputar di permukaan kubah (deterministik)
        for i in range(6):
            ang = phase * 1.5 + i * math.pi / 3
            arc_angle = math.pi * (0.1 + (i / 6.0) * 0.8)
            ax = x + int(math.cos(math.pi + arc_angle) * r * build_t)
            ay = gy + int(math.sin(math.pi + arc_angle) * r * build_t)
            _NS_morgath._rect(surface, (*P["arc_hot"], 240),
                              (ax, ay, 2, 2))
            _NS_morgath._rect(surface, (*P["arc_shine"], 255),
                              (ax, ay, 1, 1))

        # busur petir acak di dalam kubah (frame-gated deterministik)
        arc_frame = int(phase * 4) % 5
        if arc_frame < 2:
            for k in range(2):
                a1 = phase * 2 + k * 1.7
                a2 = phase * 2 + k * 1.7 + 1.5
                aa1 = math.pi * (0.15 + ((math.sin(a1) + 1) / 2) * 0.7)
                aa2 = math.pi * (0.15 + ((math.sin(a2) + 1) / 2) * 0.7)
                p1 = (x + int(math.cos(math.pi + aa1) * r * build_t),
                      gy + int(math.sin(math.pi + aa1) * r * build_t))
                p2 = (x + int(math.cos(math.pi + aa2) * r * build_t),
                      gy + int(math.sin(math.pi + aa2) * r * build_t))
                _NS_morgath._jagged_line(surface, P["arc_hot"], p1, p2,
                                         jitter=4, segments=6, width=1)

    # ============================================================
    # SKILL R: TEMPEST DOUBLE (ultimate; clone di +/-60 px dunia)
    # 3 fase: TELEGRAPH (ring kembar + retakan) -> AKTIVASI (pilar
    # cahaya + burst radial) -> STEADY (2 ghost clone + tether +
    # ember + wisp spiral).
    # ============================================================
    def _draw_tempest_ground(surface, boss, x, y, timer, phase):
        """TELEGRAPH + twin rune ring di posisi clone (+/-60 dunia)."""
        P = _NS_morgath.PALETTE
        dur = _NS_morgath.SKILL_DUR["r"]
        progress = max(0.0, min(1.0, 1 - timer / dur))
        fs = _NS_morgath._fx_scale(boss)
        facing = getattr(boss, "direction", 1) or 1
        gy = y + _NS_morgath._ground_dy()
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        off = 60 * fs

        # ── TELEGRAPH: retakan zigzag + ring konvergen + chevron ──
        if progress < 0.3:
            t = progress / 0.3
            fade = int(210 * (1 - t * 0.4))
            for side in (-1, 1):
                cxp = int(x + facing * side * off)
                # retakan tanah menuju titik clone (deterministik)
                crack_ang = 0.0 if (facing * side) > 0 else math.pi
                _NS_morgath._jagged_crack(
                    surface, x, gy, crack_ang,
                    int(58 * fs), (P["flux_dark"], P["flux_mid"]),
                    fade, seed=5 + side, width=3)
                _NS_morgath._jagged_crack(
                    surface, x, gy, crack_ang,
                    int(40 * fs), (P["flux_mid"], P["flux_hot"]),
                    int(fade * 0.8), seed=9 + side, width=1)
                rr = int((24 + (1 - t) * 14) * fs)
                _NS_morgath._aacircle(surface, (*P["flux_light"], fade),
                                      (cxp, gy), rr, 2)
                for i in range(3):
                    ang = -side * facing * math.pi / 2 + i * 0.5
                    cxx = cxp + math.cos(ang) * (rr + 10 * fs)
                    cyy = gy + math.sin(ang) * (rr + 10 * fs) * 0.45
                    _NS_morgath._chevron(surface, cxx, cyy,
                                         math.atan2(gy - cyy, x - cxx),
                                         7 * fs, P["flux_hot"], fade,
                                         width=2)

        # twin rune ring di posisi clone (steady)
        for side in (-1, 1):
            cxp = int(x + facing * side * off)
            r = int((34 + math.sin(phase * 2 + side) * 4) * fs)
            alpha = _NS_morgath._alpha(240 * pulse)
            _NS_morgath._aacircle(surface, (*P["flux_mid"], alpha),
                                  (cxp, gy), r, 2)
            _NS_morgath._dashed_ring(surface, cxp, gy, r + 5,
                                     P["flux_light"], int(200 * pulse),
                                     phase * 2.4 * side, segments=10,
                                     thick=2, span=0.5, squash=0.45)

    def _draw_tempest_clone(surface, boss, x, y, timer, phase):
        """Ghost duplicate x2 di +/-60 px dunia + tether listrik."""
        P = _NS_morgath.PALETTE
        dur = _NS_morgath.SKILL_DUR["r"]
        progress = max(0.0, min(1.0, 1 - timer / dur))
        fs = _NS_morgath._fx_scale(boss)
        facing = getattr(boss, "direction", 1) or 1
        if progress < 0.35:
            return
        spawn_t = min(1.0, (progress - 0.35) / 0.25)
        alpha_val = int(215 * spawn_t)

        for side in (-1, 1):
            cxp, cyp = _NS_morgath._world_to_local(
                boss, x, y,
                float(getattr(boss, "x", x)) + facing * side * 60,
                float(getattr(boss, "y", y)))
            buf, box = _NS_morgath._rig_buffer(facing, phase * 1.3,
                                               "idle", 0.0, False)
            tint = pygame.Surface(buf.get_size(), pygame.SRCALPHA)
            tint.fill((110, 150, 235, 255))
            buf.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            buf.set_alpha(alpha_val)
            w = max(1, int(buf.get_width() * fs))
            h = max(1, int(buf.get_height() * fs))
            if fs != 1.0:
                buf = pygame.transform.smoothscale(buf, (w, h))
            surface.blit(buf, (int(cxp - box[0] * fs),
                               int(cyp - box[1] * fs)))
            # ring kecil di kaki clone
            _NS_morgath._ellipse(
                surface, (*P["flux_mid"], 140),
                (int(cxp - 20 * fs), int(cyp + 24 * fs - 2),
                 int(40 * fs), int(5 * fs)), 1)

        # tether listrik caster <-> clone (frame-gated deterministik)
        arc_frame = int(phase * 6) % 4
        if arc_frame < 2:
            for side in (-1, 1):
                cxp, cyp = _NS_morgath._world_to_local(
                    boss, x, y,
                    float(getattr(boss, "x", x)) + facing * side * 60,
                    float(getattr(boss, "y", y)))
                _NS_morgath._jagged_line(surface, P["arc_hot"],
                                         (x, y - 15),
                                         (cxp, cyp - 30 * fs),
                                         jitter=9, segments=8, width=2)
                _NS_morgath._jagged_line(surface, P["arc_shine"],
                                         (x, y - 15),
                                         (cxp, cyp - 30 * fs),
                                         jitter=7, segments=8, width=1)

    def _draw_tempest_foreground(surface, boss, x, y, timer, phase):
        """AKTIVASI pilar + burst petir radial + aftermath bara."""
        P = _NS_morgath.PALETTE
        dur = _NS_morgath.SKILL_DUR["r"]
        progress = max(0.0, min(1.0, 1 - timer / dur))
        fs = _NS_morgath._fx_scale(boss)
        facing = getattr(boss, "direction", 1) or 1
        gy = y + _NS_morgath._ground_dy()

        if progress < 0.45:
            # ── AKTIVASI: pilar cahaya 4 lapis + shockwave ganda ──
            t = min(1.0, progress / 0.3)
            top = int(y - min(120 * fs, 250) * (0.55 + 0.45 * (1 - t)))
            for wd, col, al in ((34, P["arc_darkest"], 120),
                                (22, P["flux_mid"], 150),
                                (12, P["arc_mid"], 190),
                                (4, P["white"], 220)):
                _NS_morgath._aaline(surface, (*col, int(al * (1 - t))),
                                    (x, top), (x, y - 10), wd)
            _NS_morgath._spark_star(surface, x, y - 10,
                                    int(34 * (1 - t * 0.4)), P["arc_shine"],
                                    int(235 * (1 - t)), spikes=8, rot=0.3,
                                    core=P["white"])
            for k, rmax in ((0, 130), (1, 92)):
                rr = int((20 + t * rmax) * fs)
                _NS_morgath._aacircle(
                    surface,
                    (*P["arc_light" if k == 0 else "flux_light"],
                     int((220 if k == 0 else 150) * (1 - t))),
                    (x, y - 10), rr, 2)
            # burst petir radial (12 bolt)
            burst_r = int((44 + t * 60) * fs)
            for i in range(12):
                angle = i * math.pi / 6 + phase * 0.5
                end_x = x + int(math.cos(angle) * burst_r)
                end_y = y - 15 + int(math.sin(angle) * burst_r * 0.8)
                alpha = _NS_morgath._alpha(200 * (1 - t))
                _NS_morgath._jagged_line(surface, P["arc_darkest"],
                                         (x, y - 15), (end_x, end_y),
                                         jitter=6, segments=6, width=4)
                _NS_morgath._jagged_line(surface, P["arc_mid"],
                                         (x, y - 15), (end_x, end_y),
                                         jitter=6, segments=6, width=2)
                _NS_morgath._jagged_line(surface, P["arc_shine"],
                                         (x, y - 15), (end_x, end_y),
                                         jitter=4, segments=6, width=1)
                pygame.draw.rect(surface, (*P["white"], alpha),
                                 (end_x, end_y, 2, 2))
            for r_ in range(15, 0, -1):
                alpha = _NS_morgath._alpha(220 * (1 - t) * (15 - r_) / 15)
                _NS_morgath._aacircle(surface, (*P["arc_light"], alpha),
                                      (x, y - 15), int(r_ * fs))
        else:
            # ── STEADY/aftermath: bara naik + wisp spiral + glint orbit ──
            t = (progress - 0.45) / 0.55
            for i in range(16):
                rise_t = (phase * 0.7 + i * 0.06) % 1.0
                angle = i * math.pi * 2 / 16 + phase * 0.3
                r_sp = (52 + math.sin(phase + i) * 12) * fs
                rx = x + int(math.cos(angle) * r_sp)
                ry = y + 12 + int(math.sin(angle) * r_sp * 0.4) \
                    - int(rise_t * 30 * fs)
                alpha = _NS_morgath._alpha(210 * (1 - t)
                                           * (1 - rise_t * 0.5))
                if alpha > 0:
                    _NS_morgath._rect(surface, (*P["arc_light"], alpha),
                                      (rx, ry, 2, 2))
                    _NS_morgath._rect(surface, (*P["arc_shine"], alpha),
                                      (rx, ry, 1, 1))
            # wisp spiral 2 lengan
            for arm in range(2):
                for j in range(9):
                    a = phase * 2.2 + arm * math.pi + j * 0.38
                    rr = (24 + j * 7.5) * fs
                    al = int(150 * (1 - j / 9) * (1 - t * 0.4))
                    _NS_morgath._aacircle(
                        surface, (*P["flux_light"], al),
                        (int(x + math.cos(a) * rr),
                         int(y - 12 + math.sin(a) * rr * 0.55)), 2)
            # glint orbit di sekitar caster
            for i in range(3):
                a = phase * 1.1 + i * math.pi * 2 / 3
                rr = (40 + math.sin(phase * 1.7 + i) * 8) * fs
                _NS_morgath._rect(
                    surface, (*P["white"],
                              _NS_morgath._alpha(190 * (1 - t * 0.3))),
                    (int(x + math.cos(a) * rr),
                     int(y - 10 + math.sin(a) * rr * 0.5), 2, 2))
            # denyut pusat
            _NS_morgath._aacircle(
                surface,
                (*P["arc_hot"],
                 _NS_morgath._alpha(170 * math.sin(phase * 3) * 0.5 + 90)),
                (x, y - 10), int((28 + 6 * math.sin(phase * 3)) * fs))
            _NS_morgath._aacircle(
                surface, (*P["white"],
                          _NS_morgath._alpha(200 * math.sin(phase * 3)
                                             * 0.5 + 100)),
                (x, y - 10), int((12 + 4 * math.sin(phase * 3)) * fs))
# DRAKAR (AXE) - Mini Boss HD (Redesigned)
# ====================================================================
import math
import pygame


class _NS_drakar:
    """Namespace drakar - PIXEL MASTERWORK v2 + SKILL FX v2.1.

    Rewrite penuh renderer _NS_drakar di bosses/level1.py.
    Tetap 100% prosedural: tidak ada PNG / sprite-sheet / image.load.

    Upgrade dari v1 (ORIGINAL-MAX):
    - RIG ~1.5x lebih besar (240->360) di resolusi native
    - Disiplin pixel-art: ramp 4-5 band hue-shift, selout, siluet bergerigi,
      specular cluster, dither band, key light kiri-atas
    - Anatomi detail: barbarian dengan axe besar, pauldron ber-spike,
      bandolier, rambut liar, janggut ber-lapis
    - Animasi: foot solver, inersia, idle hidup (napas, kedip, dengus),
      serangan 7 keyframe + IMPACT + smear
    - Skill FX world-space via _fx_scale (kompensasi _render_scale, cap 2.6)
    - 3 fase per skill: AKTIVASI, STEADY, TELEGRAPH
    - Primitif FX: _spark_star, _chevron, _dashed_ring, _jagged_crack
    - Body bereaksi ke state skill (crest menyala saat buff)
    - Cache permukaan statis (aura, shadow, mist)
    """

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        "skin_darkest": (55, 15, 15), "skin_dark": (110, 30, 25),
        "skin_mid": (170, 55, 40), "skin_light": (215, 95, 70),
        "skin_shine": (240, 145, 110), "skin_rim": (252, 170, 130),
        "hair_darkest": (8, 6, 10), "hair_dark": (28, 22, 28),
        "hair_mid": (55, 45, 50), "hair_light": (95, 80, 85),
        "leather_darkest": (22, 12, 6), "leather_dark": (55, 32, 18),
        "leather_mid": (95, 62, 38), "leather_light": (140, 100, 65),
        "armor_darkest": (15, 12, 15), "armor_dark": (42, 38, 45),
        "armor_mid": (85, 78, 88), "armor_light": (140, 132, 142),
        "armor_shine": (200, 195, 205),
        "blade_darkest": (18, 15, 22), "blade_dark": (55, 50, 62),
        "blade_mid": (115, 108, 125), "blade_light": (185, 178, 195),
        "blade_shine": (240, 235, 250),
        "blood_darkest": (45, 5, 10), "blood_dark": (110, 15, 20),
        "blood_mid": (185, 25, 35), "blood_light": (235, 55, 60),
        "blood_hot": (255, 100, 90), "blood_shine": (255, 180, 160),
        "rage_darkest": (60, 10, 5), "rage_dark": (140, 30, 15),
        "rage_mid": (220, 55, 30), "rage_light": (255, 110, 60),
        "rage_hot": (255, 180, 120),
        "eye_dark": (80, 30, 10), "eye_mid": (200, 90, 20),
        "eye_light": (255, 180, 60), "eye_glow": (255, 240, 180),
        "rune_dark": (30, 8, 10), "rune_mid": (140, 30, 30),
        "rune_light": (230, 70, 60),
        "gold_dark": (96, 68, 20), "gold_mid": (180, 136, 44),
        "gold_light": (238, 202, 92),
        "ember_dark": (140, 40, 10), "ember_mid": (220, 90, 20),
        "ember_light": (255, 170, 50), "ember_hot": (255, 220, 120),
        "shadow": (0, 0, 0), "shadow_deep": (3, 1, 2),
        "white": (255, 255, 255),
    }

    BODY_W, BODY_H = 360, 360
    BODY_OX, BODY_OY = 180, 186
    _RIG_SCALE = 1.5
    _STATIC_SURFACES = {}
    _DRK_TX = {}
    _DRK_FIN = None
    _DRK_SHADE = None
    _DRK_BUF = None

    def _static(key, builder):
        surf = _NS_drakar._STATIC_SURFACES.get(key)
        if surf is None:
            surf = builder()
            _NS_drakar._STATIC_SURFACES[key] = surf
        return surf

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _rgba(color, alpha):
        r, g, b = color[0], color[1], color[2]
        return (max(0, min(255, int(r))), max(0, min(255, int(g))),
                max(0, min(255, int(b))), max(0, min(255, int(alpha))))

    def _mix(a, b, t):
        t = max(0.0, min(1.0, t))
        return _NS_drakar._clamp(
            (a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t, a[2]+(b[2]-a[2])*t))

    def _hash01(i):
        x = math.sin(i * 127.1 + 311.7) * 43758.5453
        return x - math.floor(x)

    def _aacircle(surface, color, center, radius, width=0):
        if len(color) == 4:
            color = (max(0,min(255,int(color[0]))), max(0,min(255,int(color[1]))),
                     max(0,min(255,int(color[2]))), max(0,min(255,int(color[3]))))
        else:
            color = _NS_drakar._clamp(color)
        if _NS_drakar.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        if len(color) == 4:
            color = (max(0,min(255,int(color[0]))), max(0,min(255,int(color[1]))),
                     max(0,min(255,int(color[2]))), max(0,min(255,int(color[3]))))
        else:
            color = _NS_drakar._clamp(color)
        if _NS_drakar.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_drakar._clamp(color), points)

    def _fx_scale(boss):
        scale = getattr(boss, "_render_scale", None)
        if not scale:
            return 1.0
        return max(1.0, min(2.6, 1.0 / float(scale)))

    def _spark_star(surface, cx, cy, size, color, alpha, spikes=6, rot=0.4, core=None):
        if alpha <= 0 or size <= 0:
            return
        for k in range(spikes):
            ang = rot + k * math.pi * 2 / spikes
            ln = size * (1.0 if k % 2 == 0 else 0.55)
            _NS_drakar._aaline(surface, (*_NS_drakar._clamp(color), alpha),
                               (int(cx), int(cy)),
                               (int(cx+math.cos(ang)*ln), int(cy+math.sin(ang)*ln*.8)),
                               2 if k%2==0 else 1)
        if core:
            _NS_drakar._aacircle(surface, (*core, alpha), (int(cx), int(cy)),
                                 max(1, int(size*.3)))

    def _chevron(surface, cx, cy, ang, size, color, alpha, width=3):
        if alpha <= 0 or size <= 0:
            return
        ca, sa = math.cos(ang), math.sin(ang)
        px, py = -sa, ca
        tipx, tipy = cx+ca*size, cy+sa*size
        for s in (-1, 1):
            _NS_drakar._aaline(
                surface, (*_NS_drakar._clamp(color), alpha),
                (int(cx+px*s*size*.55-ca*size*.5), int(cy+py*s*size*.55-sa*size*.5)),
                (int(tipx), int(tipy)), width)

    def _dashed_ring(surface, cx, cy, radius, color, alpha, phase,
                     segments=10, thick=3, span=0.6, squash=.92):
        if alpha <= 0 or radius <= 1:
            return
        for i in range(segments):
            a0 = phase + i * math.pi * 2 / segments
            a1 = a0 + math.pi * 2 / segments * span
            p0 = (cx+math.cos(a0)*radius, cy+math.sin(a0)*radius*squash)
            p1 = (cx+math.cos(a1)*radius, cy+math.sin(a1)*radius*squash)
            _NS_drakar._aaline(surface, (*_NS_drakar._clamp(color), alpha), p0, p1, thick)

    def _jagged_crack(surface, cx, cy, ang, length, colors, alpha, seed, width=3):
        if alpha <= 0 or length <= 0:
            return
        x, y, a = cx, cy, ang
        pts = [(x, y)]
        for i in range(3):
            a += (_NS_drakar._hash01(seed*7+i*13)-.5)*.8
            seg = length / 3.0
            x += math.cos(a) * seg
            y += math.sin(a) * seg * .55
            pts.append((x, y))
        for i in range(len(pts)-1):
            _NS_drakar._aaline(surface, (*_NS_drakar._clamp(colors[0]), alpha),
                              pts[i], pts[i+1], width+2)
            _NS_drakar._aaline(surface, (*_NS_drakar._clamp(colors[1]), alpha),
                              pts[i], pts[i+1], width)

    def _tuft_points(spine, depth=4.0, min_len=7.0, seed=0):
        out = [spine[0]]
        for i in range(len(spine)-1):
            ax, ay = spine[i]
            bx, by = spine[i+1]
            seg = math.hypot(bx-ax, by-ay)
            n = max(1, int(seg / min_len))
            nx, ny = (by-ay), -(bx-ax)
            ln = math.hypot(nx, ny) or 1.0
            nx, ny = nx/ln, ny/ln
            for j in range(n):
                t = (j+0.5)/n
                px, py = ax+(bx-ax)*t, ay+(by-ay)*t
                d = depth*(0.55+0.45*_NS_drakar._hash01(i*7+j*13+seed))
                if j % 2 == 0:
                    out.append((px+nx*d, py+ny*d))
                else:
                    out.append((px-nx*d*0.45, py-ny*d*0.45))
            out.append((bx, by))
        return out

    def _drk_glow(radius, color, peak=190):
        key = (int(radius), color, int(peak))
        if key not in _NS_drakar._DRK_TX:
            r = int(radius)
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            fmax = peak / 255.0
            for rad in range(r, 0, -1):
                t = 1.0 - rad / float(r)
                f = (t ** 1.8) * fmax
                _NS_drakar._aacircle(s, (int(color[0]*f), int(color[1]*f),
                                         int(color[2]*f), 255), (r, r), rad)
            _NS_drakar._DRK_TX[key] = s
        return _NS_drakar._DRK_TX[key]

    def _drk_outline(buf, flash=0):
        B = _NS_drakar
        if B._DRK_FIN is None:
            B._DRK_FIN = pygame.Surface((B.BODY_W+2, B.BODY_H+2), pygame.SRCALPHA)
            sh = pygame.Surface((B.BODY_W+2, B.BODY_H+2), pygame.SRCALPHA)
            h, w = B.BODY_H+2, B.BODY_W+2
            for yy in range(h):
                v = int(255 - 70*(yy/float(h)))
                pygame.draw.line(sh, (v,v,v,255), (0,yy), (w,yy))
            for xx in range(0, w, 2):
                v = int(255 - 30*(xx/float(w)))
                s2 = pygame.Surface((2, h), pygame.SRCALPHA)
                s2.fill((v,v,v,255))
                sh.blit(s2, (xx, 0), special_flags=pygame.BLEND_RGBA_MULT)
            B._DRK_SHADE = sh
        out = B._DRK_FIN
        out.fill((0,0,0,0))
        pad = 1
        edge = buf.copy()
        edge.fill((0,0,0,255), special_flags=pygame.BLEND_RGBA_MULT)
        light = edge.copy()
        light.fill((255,214,170,0), special_flags=pygame.BLEND_RGB_ADD)
        dark = edge.copy()
        dark.fill((10,5,7,0), special_flags=pygame.BLEND_RGB_ADD)
        out.blit(light, (pad-1, pad-1))
        out.blit(light, (pad, pad-1))
        out.blit(light, (pad-1, pad))
        out.blit(dark, (pad+1, pad))
        out.blit(dark, (pad, pad+1))
        out.blit(dark, (pad+1, pad+1))
        out.blit(buf, (pad, pad))
        out.blit(B._DRK_SHADE, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
        if flash > 0:
            w = int(235 * min(1.0, flash/8.0))
            if w > 0:
                m = pygame.mask.from_surface(buf, 50)
                wht = m.to_surface(setcolor=(w, int(w*0.92), int(w*0.82), 255),
                                   unsetcolor=(0,0,0,0))
                out.blit(wht, (pad, pad), special_flags=pygame.BLEND_RGB_ADD)
        return out

    def _drk_body_surface(mode, facing, phase_q, prog_q, flash=0, **kwargs):
        B = _NS_drakar
        if B._DRK_BUF is None:
            B._DRK_BUF = pygame.Surface((B.BODY_W, B.BODY_H), pygame.SRCALPHA)
        buf = B._DRK_BUF
        buf.fill((0,0,0,0))
        ox, oy = B.BODY_OX, B.BODY_OY
        if mode == "idle":
            bob = int(math.sin(phase_q*0.5)*9)
            B._draw_drk_body(buf, ox, oy+bob, facing, phase_q, "idle", **kwargs)
        elif mode == "walk":
            bob = int(abs(math.sin(phase_q*1.1))*7)
            sway = int(math.sin(phase_q*0.8)*4)
            B._draw_drk_body(buf, ox+sway, oy-bob+3, facing, phase_q, "walk", **kwargs)
        elif mode == "attack":
            B._draw_drk_body(buf, ox, oy, facing, phase_q, "attack", prog_q, **kwargs)
        else:
            spin = prog_q * math.pi * 8
            bob = int(math.sin(prog_q*math.pi)*-7)
            B._draw_drk_body(buf, ox, oy+bob, facing, phase_q, "helix",
                             spin_angle=spin, **kwargs)
        return B._drk_outline(buf, flash)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        return int(x + 220/float(getattr(boss,"_render_scale",1.0) or 1.0)*getattr(boss,"direction",1)), int(y)

    def draw_drakar(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_drakar._detect_moving(boss)
        _NS_drakar._update_drk_attack_anim(boss)
        attacking = (getattr(boss, "_drk_attack_active", False)
                     or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15)
        fs = _NS_drakar._fx_scale(boss)

        _NS_drakar._draw_rage_aura(surface, x, y, pulse)
        _NS_drakar._draw_ground_ring(surface, boss, x, y+114, pulse, active_skill)

        if active_skill == "q":
            _NS_drakar._draw_battlehunger_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_drakar._draw_counterhelix_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_drakar._draw_berserkerscall_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_drakar._draw_cullingblade_ground(surface, boss, x, y, skill_timer, pulse)

        if active_skill in ("q","w","e","r"):
            dur = {"q":90,"w":45,"e":60,"r":60}[active_skill]
            age = dur - skill_timer
            if 0 <= age < 12:
                st = age / 12.0
                a = int(235*(1-st))
                rr = int((16+st*50)*fs)
                gy = y + 114
                pygame.draw.ellipse(surface, (255,80,50,a),
                                    (x-rr, gy-rr//3, rr*2, max(4,rr*2//3)), 2)
                pygame.draw.ellipse(surface, (255,200,150,a),
                                    (x-rr//2, gy-rr//6, rr, max(3,rr//3)), 1)
                _NS_drakar._spark_star(surface, x, gy, int(20*fs),
                                       _NS_drakar.PALETTE["rage_light"],
                                       a, spikes=8, rot=pulse,
                                       core=_NS_drakar.PALETTE["rage_hot"])

        facing = int(getattr(boss, "direction", 1)) or 1
        cd = max(2, int(getattr(boss, "attack_cooldown", 46)))
        t_now = int(getattr(boss, "timer", 0))
        atk_p = max(0.0, min(1.0, (cd-1-t_now)/float(cd-1))) if attacking else 0.0
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        ox, oy = _NS_drakar.BODY_OX, _NS_drakar.BODY_OY

        body_kw = {}
        if active_skill == "q": body_kw["battlehunger"] = True
        if active_skill == "w": body_kw["helix_active"] = True
        if active_skill == "e": body_kw["berserk_call"] = True
        if getattr(boss, "rage_active", False): body_kw["rage_mode"] = True

        def _blit_body(spr):
            img = spr if facing > 0 else pygame.transform.flip(spr, True, False)
            surface.blit(img, (x-ox, y-oy))

        if active_skill == "w":
            p = max(0.0, min(1.0, 1-skill_timer/45.0))
            lift_h = int(math.sin(p*math.pi)*7)
            _NS_drakar._draw_shadow(surface, x, y+120, lift_h)
            _NS_drakar._draw_rage_mist(surface, x, y+90, pulse, intense=True)
            _NS_drakar._draw_drk_helix_fx(surface, boss, x, y, skill_timer, pulse)
            _blit_body(_NS_drakar._drk_body_surface("helix", facing, pulse, p, flash, **body_kw))
        elif attacking:
            if atk_p < 0.15:
                t2 = atk_p / 0.15; lunge = -int(t2*6)*facing; lift = -int(t2*6)
            elif atk_p < 0.40:
                t2 = (atk_p-0.15)/0.25; lunge = -int(6+t2*6)*facing; lift = int(-6+t2*15)
            elif atk_p < 0.55:
                t2 = (atk_p-0.40)/0.15; t_ease = 1-(1-t2)**2
                lunge = int((-12+t_ease*42))*facing; lift = int(9-t_ease*15)
            elif atk_p < 0.70:
                t2 = (atk_p-0.55)/0.15; shake_x = int(math.sin(t2*30)*4*(1-t2))
                lunge = int(30+shake_x)*facing; lift = int(-6-t2*3)
            else:
                t2 = (atk_p-0.70)/0.30; t_ease = 1-(1-t2)**2
                lunge = int(30*(1-t_ease))*facing; lift = int(-9+t_ease*9)
            _NS_drakar._draw_shadow(surface, x+lunge, y+120, lift)
            _NS_drakar._draw_rage_mist(surface, x+lunge, y+90, pulse, intense=True)
            _blit_body(_NS_drakar._drk_body_surface("attack", facing, pulse, atk_p, flash, **body_kw))
            _NS_drakar._draw_axe_slash_trail(surface, boss, x+lunge, y-lift, atk_p)
            if 0.53 <= atk_p <= 0.70:
                _NS_drakar._draw_impact_burst(surface, boss, x+lunge, y-lift, atk_p)
        elif moving:
            phase = pulse * 2.0
            bob = int(abs(math.sin(phase*1.1))*7)
            sway = int(math.sin(phase*0.8)*4)
            _NS_drakar._draw_shadow(surface, x+sway, y+120, bob)
            _NS_drakar._draw_rage_mist(surface, x+sway, y+90, phase, trail=True, facing=facing)
            _blit_body(_NS_drakar._drk_body_surface("walk", facing, phase, 0.0, flash, **body_kw))
        else:
            bob_i = int(math.sin(pulse*0.5)*9)
            _NS_drakar._draw_shadow(surface, x, y+120, max(0, -bob_i))
            _NS_drakar._draw_rage_mist(surface, x, y+90, pulse)
            _blit_body(_NS_drakar._drk_body_surface("idle", facing, pulse, 0.0, flash, **body_kw))

        if getattr(boss, "rage_active", False):
            g = _NS_drakar._drk_glow(69, _NS_drakar.PALETTE["rage_mid"], 70)
            surface.blit(g, (x-69, y-90), special_flags=pygame.BLEND_RGBA_ADD)
            g2 = _NS_drakar._drk_glow(10, _NS_drakar.PALETTE["rage_light"], 110)
            surface.blit(g2, (x+9*facing-10, y-60), special_flags=pygame.BLEND_RGBA_ADD)
        if getattr(boss, "defense_boost", False):
            for i in range(3):
                a = pulse*3+i*2.1
                sx = x-18+int(math.sin(a)*6)
                sy = y-36+int(math.cos(a*1.3)*7)
                _NS_drakar._aacircle(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["armor_shine"],
                                     150+int(70*math.sin(a*2))), (sx, sy), 2)

        if active_skill == "q":
            _NS_drakar._draw_battlehunger_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_drakar._draw_berserkerscall_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_drakar._draw_cullingblade_foreground(surface, boss, x, y, skill_timer, pulse)

    def _update_drk_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_drk_previous_timer", 0))
        active = bool(getattr(boss, "_drk_attack_active", False))
        if timer >= cooldown-1 and previous <= 1:
            boss._drk_attack_active = True; boss._drk_attack_frame = 0
            boss._drk_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._drk_attack_frame = int(getattr(boss, "_drk_attack_frame", 0))+1
        elif timer <= 0:
            boss._drk_attack_active = False; boss._drk_attack_frame = 0; active = False
        boss._drk_previous_timer = timer
        boss._drk_attack_progress = (
            min(1.0, getattr(boss, "_drk_attack_frame", 0)/max(1, cooldown-1))
            if active else 0.0)

    def _detect_moving(boss):
        if not hasattr(boss, "_drk_last_x"):
            boss._drk_last_x = boss.x; boss._drk_last_y = boss.y; return False
        dx = abs(boss.x - boss._drk_last_x); dy = abs(boss.y - boss._drk_last_y)
        boss._drk_last_x = boss.x; boss._drk_last_y = boss.y
        return dx + dy > 0.3

    def _draw_drk_helix_fx(surface, boss, x, y, timer, phase):
        duration = 45
        progress = max(0.0, min(1.0, 1-timer/duration))
        spin = progress * math.pi * 8
        bob = int(math.sin(progress*math.pi)*-7)
        fs = _NS_drakar._fx_scale(boss)
        slash_surf = pygame.Surface((420, 420), pygame.SRCALPHA)
        center = (210, 210)
        radius = int(108 * fs)
        for arm_i in range(2):
            arm_start = spin + arm_i * math.pi
            arc_pts = []
            for i in range(25):
                a = arm_start + math.pi*0.9*i/24
                arc_pts.append((center[0]+int(math.cos(a)*radius),
                                center[1]+int(math.sin(a)*radius*0.7)))
            for r_off, thick, color, a_mult in [
                (6,15,"blood_darkest",0.7),(3,12,"blood_dark",0.85),
                (0,9,"blood_mid",1.0),(-2,6,"blood_light",1.0),(-3,3,"blood_hot",1.0)]:
                for k in range(len(arc_pts)-1):
                    fade = 1-(k/len(arc_pts))
                    av = _NS_drakar._alpha(240*a_mult*fade)
                    if av <= 0: continue
                    pygame.draw.line(slash_surf,
                        _NS_drakar._rgba(_NS_drakar.PALETTE[color], av),
                        arc_pts[k], arc_pts[k+1], thick)
            if arc_pts:
                tip = arc_pts[-1]
                pygame.draw.rect(slash_surf, _NS_drakar._rgba(_NS_drakar.PALETTE["blade_shine"],255), (tip[0],tip[1],4,4))
                pygame.draw.rect(slash_surf, _NS_drakar._rgba(_NS_drakar.PALETTE["white"],255), (tip[0],tip[1],3,3))
        for i in range(28):
            angle = spin*0.5+i*math.pi/14
            r_p = radius+int(math.sin(phase+i)*18)-12
            px = center[0]+int(math.cos(angle)*r_p)
            py = center[1]+int(math.sin(angle)*r_p*0.7)
            alpha = _NS_drakar._alpha(220)
            pygame.draw.rect(slash_surf, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"],alpha), (px,py,4,4))
            pygame.draw.rect(slash_surf, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_hot"],alpha), (px,py,3,3))
        surface.blit(slash_surf, (x-210, y-210+bob))

    def _draw_drk_body(surface, cx, cy, facing, phase, action, attack_progress=0,
                       spin_angle=0, **kwargs):
        rage_mode = kwargs.get("rage_mode", False)
        _NS_drakar._draw_drk_legs(surface, cx, cy+42, facing, phase, action)
        _NS_drakar._draw_drk_waist(surface, cx, cy+21, facing, phase)
        _NS_drakar._draw_drk_torso(surface, cx, cy-9, facing, phase, action, rage_mode=rage_mode)
        _NS_drakar._draw_drk_head(surface, cx, cy-45, facing, phase, action)
        grip_data = _NS_drakar._compute_two_handed_grip(cx, cy, facing, phase, action, attack_progress, spin_angle)
        _NS_drakar._draw_drk_arm_two_handed_back(surface, cx, cy-6, facing, phase, grip_data["back_hand"], action)
        _NS_drakar._draw_axe(surface, grip_data["axe_head"][0], grip_data["axe_head"][1],
                             facing, grip_data["axe_angle"], action, attack_progress, pommel_pos=grip_data["pommel"])
        _NS_drakar._draw_drk_arm_two_handed_front(surface, cx, cy-6, facing, phase, grip_data["front_hand"], action, attack_progress)

    def _draw_drk_legs(surface, cx, cy, facing, phase, action):
        if action == "walk":
            stride = math.sin(phase*2)*7
            back_lift = max(0,-math.sin(phase*2))*6
            front_lift = max(0,math.sin(phase*2))*6
        else:
            stride = 0; back_lift = front_lift = 0
        _NS_drakar._draw_leg(surface, cx-13+int(stride), cy-int(back_lift), facing, back=True)
        _NS_drakar._draw_leg(surface, cx+13-int(stride), cy-int(front_lift), facing, back=False)

    def _draw_leg(surface, cx, cy, facing, back=False):
        pygame.draw.rect(surface, _NS_drakar.PALETTE["shadow_deep"], (cx-10,cy-21,22,27))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_darkest"], (cx-10,cy-21,21,25))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_dark"], (cx-9,cy-21,16,24))
        if not back:
            pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_mid"], (cx-6,cy-19,10,21))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_light"], (cx-3,cy-18,3,15))
        for strap_y in (cy-15, cy-6):
            pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_darkest"], (cx-10,strap_y,21,3))
            if not back:
                pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_mid"], (cx-9,strap_y,18,1))
            for stud_x in (cx-6, cx+4):
                pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_dark"], (stud_x,strap_y,3,3))
                if not back: pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_light"], (stud_x,strap_y,1,1))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["shadow_deep"], (cx-9,cy+6,19,9))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_darkest"], (cx-9,cy+6,18,9))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_dark"], (cx-7,cy+6,15,7))
        if not back:
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_mid"], (cx-7,cy+6,12,4))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_light"], (cx-6,cy+6,7,1))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_shine"], (cx-4,cy+6,3,1))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["shadow_deep"], (cx-12,cy+15,27,15))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_darkest"], (cx-12,cy+15,25,13))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_dark"], (cx-10,cy+15,21,12))
        if not back:
            pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_mid"], (cx-9,cy+15,15,7))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_light"], (cx-7,cy+16,9,4))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_darkest"], (cx-12,cy+22,27,6))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_dark"], (cx-12,cy+22,25,4))
        if not back:
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_mid"], (cx-10,cy+22,22,3))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_light"], (cx-9,cy+22,18,1))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_light"], (cx+facing*9,cy+25,3,3))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_shine"], (cx+facing*9,cy+25,1,1))

    def _draw_drk_waist(surface, cx, cy, facing, phase):
        pygame.draw.rect(surface, _NS_drakar.PALETTE["shadow_deep"], (cx-33,cy-9,67,15))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_darkest"], (cx-31,cy-9,64,15))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_dark"], (cx-31,cy-9,63,12))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_mid"], (cx-30,cy-7,60,7))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_light"], (cx-27,cy-7,9,3))
        for sx_off in (-24,-15,-6,12,21):
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_darkest"], (cx+sx_off-1,cy-3,6,6))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_dark"], (cx+sx_off,cy-3,4,4))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_mid"], (cx+sx_off,cy-3,3,3))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_light"], (cx+sx_off,cy-3,1,1))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["shadow_deep"], (cx-9,cy-9,21,16))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_darkest"], (cx-9,cy-9,19,16))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_dark"], (cx-7,cy-9,16,15))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_mid"], (cx-6,cy-7,13,12))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_light"], (cx-6,cy-7,4,3))
        rune_pulse = math.sin(phase*2)*0.3+0.7
        for r in range(7,0,-1):
            _NS_drakar._aacircle(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"],
                _NS_drakar._alpha(120*(7-r)/7*rune_pulse)), (cx+1,cy), r)
        pygame.draw.rect(surface, _NS_drakar.PALETTE["blood_darkest"], (cx-3,cy-3,8,7))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["blood_mid"], (cx-1,cy-1,6,4))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["blood_hot"], (cx,cy,3,1))
        loin_pts = [(cx-13,cy+4),(cx+13,cy+4),(cx+10,cy+18),(cx+4,cy+24),(cx-4,cy+24),(cx-10,cy+18)]
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["shadow_deep"], [(px+1,py+1) for px,py in loin_pts])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["leather_darkest"], loin_pts)
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["leather_dark"],
            [(cx-10,cy+4),(cx+10,cy+4),(cx+7,cy+18),(cx,cy+22),(cx-7,cy+18)])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["leather_mid"],
            [(cx-4,cy+6),(cx+4,cy+6),(cx+3,cy+18),(cx,cy+21),(cx-3,cy+18)])
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_darkest"], (cx,cy+6), (cx,cy+22), 1)
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_dark"], (cx-1,cy+22,4,3))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_light"], (cx,cy+22,2,1))

    def _draw_drk_torso(surface, cx, cy, facing, phase, action, rage_mode=False):
        breath = math.sin(phase*0.6)*3
        if action == "attack": breath += math.sin(phase*3)*1.5
        skin_base = _NS_drakar.PALETTE["skin_mid"]
        if rage_mode:
            rp = 0.3+0.2*math.sin(phase*4)
            skin_base = _NS_drakar._mix(skin_base, _NS_drakar.PALETTE["blood_mid"], rp)
        torso_pts = [(cx-27,cy-6),(cx-30,cy+9),(cx-25,cy+24),(cx+25,cy+24),
                     (cx+30,cy+9),(cx+27,cy-6),(cx+18,cy-15),(cx-18,cy-15)]
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["shadow_deep"], [(px+3,py+3) for px,py in torso_pts])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["skin_darkest"], torso_pts)
        _NS_drakar._poly(surface, _NS_drakar._clamp(skin_base),
            [(cx-25,cy-3+int(breath)),(cx-28,cy+9),(cx-22,cy+22),(cx+22,cy+22),
             (cx+28,cy+9),(cx+25,cy-3+int(breath)),(cx+15,cy-13),(cx-15,cy-13)])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["skin_light"],
            [(cx-21,cy+int(breath)),(cx-24,cy+9),(cx-18,cy+18),(cx+18,cy+18),
             (cx+24,cy+9),(cx+21,cy+int(breath)),(cx+12,cy-10),(cx-12,cy-10)])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["skin_shine"],
            [(cx-15,cy+1+int(breath)),(cx-4,cy+1+int(breath)),(cx-7,cy+12),(cx-15,cy+9)])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["skin_shine"],
            [(cx+4,cy+1+int(breath)),(cx+15,cy+1+int(breath)),(cx+15,cy+9),(cx+7,cy+12)])
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_rim"], (cx-12,cy+3+int(breath),4,1))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_rim"], (cx+7,cy+3+int(breath),4,1))
        pygame.draw.line(surface, _NS_drakar.PALETTE["skin_darkest"], (cx,cy-7+int(breath)), (cx,cy+18), 3)
        for i,y_off in enumerate((9,15,19)):
            for x_side in (-1,1):
                pygame.draw.line(surface, _NS_drakar.PALETTE["skin_darkest"],
                    (cx+x_side*3,cy+y_off),(cx+x_side*10,cy+y_off),1)
            pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_light"], (cx-7,cy+y_off-1,3,1))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_light"], (cx+4,cy+y_off-1,3,1))
        pygame.draw.line(surface, _NS_drakar.PALETTE["skin_darkest"], (cx+6,cy-4+int(breath)), (cx+15,cy+4), 1)
        pygame.draw.line(surface, _NS_drakar.PALETTE["skin_shine"], (cx+7,cy-3+int(breath)), (cx+13,cy+3), 1)
        for dx_off in (-8,-4,4,8):
            pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_light"], (cx+dx_off,cy+16,1,1))
        strap_start = (cx-27,cy-4); strap_end = (cx+27,cy+22)
        pygame.draw.line(surface, _NS_drakar.PALETTE["shadow_deep"],
            (strap_start[0]+1,strap_start[1]+1),(strap_end[0]+1,strap_end[1]+1),8)
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_darkest"], strap_start, strap_end, 7)
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_dark"], strap_start, strap_end, 6)
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_mid"],
            (strap_start[0],strap_start[1]-1),(strap_end[0],strap_end[1]-1),3)
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_light"],
            (strap_start[0],strap_start[1]-2),(strap_end[0],strap_end[1]-2),1)
        _NS_drakar._draw_shoulder_pauldron(surface, cx-facing*24, cy-12, facing)
        _NS_drakar._draw_bare_shoulder(surface, cx+facing*21, cy-12, facing)

    def _draw_shoulder_pauldron(surface, cx, cy, facing):
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["shadow_deep"],
            [(cx-13,cy+12),(cx-15,cy+4),(cx-10,cy-7),(cx-4,cy-12),
             (cx+6,cy-12),(cx+12,cy-7),(cx+15,cy+4),(cx+13,cy+12)])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["armor_darkest"],
            [(cx-12,cy+10),(cx-13,cy+4),(cx-9,cy-6),(cx-4,cy-10),
             (cx+6,cy-10),(cx+10,cy-6),(cx+13,cy+4),(cx+12,cy+10)])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["armor_dark"],
            [(cx-10,cy+9),(cx-12,cy+4),(cx-7,cy-4),(cx-3,cy-9),
             (cx+4,cy-9),(cx+9,cy-4),(cx+12,cy+4),(cx+10,cy+9)])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["armor_mid"],
            [(cx-7,cy+7),(cx-10,cy+3),(cx-6,cy-3),(cx-1,cy-7),
             (cx+3,cy-7),(cx+7,cy-3),(cx+10,cy+3),(cx+7,cy+7)])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["armor_light"],
            [(cx-4,cy),(cx-1,cy-4),(cx+1,cy-4),(cx+3,cy),(cx,cy+3),(cx-3,cy+3)])
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_shine"], (cx-1,cy-1,3,3))
        for x_off, height in [(-7,9),(-1,12),(6,9)]:
            sx = cx+x_off; st_y = cy-10-height
            _NS_drakar._poly(surface, _NS_drakar.PALETTE["shadow_deep"],
                [(sx+1,st_y+1),(sx-4+1,cy-7+1),(sx+4+1,cy-7+1)])
            _NS_drakar._poly(surface, _NS_drakar.PALETTE["armor_darkest"],
                [(sx,st_y),(sx-4,cy-7),(sx+4,cy-7)])
            _NS_drakar._poly(surface, _NS_drakar.PALETTE["armor_dark"],
                [(sx,st_y),(sx-3,cy-7),(sx+3,cy-7)])
            _NS_drakar._poly(surface, _NS_drakar.PALETTE["armor_mid"],
                [(sx,st_y),(sx-1,cy-7),(sx+3,cy-7)])
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_light"], (sx,st_y,1,3))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_shine"], (sx,st_y,1,1))
        for rx_off in (-9,0,9):
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_darkest"], (cx+rx_off-1,cy+6,3,3))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_light"], (cx+rx_off,cy+6,1,1))

    def _draw_bare_shoulder(surface, cx, cy, facing):
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_darkest"], (cx-8,cy-4,16,18))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_dark"], (cx-7,cy-3,14,16))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_mid"], (cx-5,cy-2,10,14))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_light"], (cx-3,cy-1,6,8))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_shine"], (cx-1,cy,2,2))

    def _draw_drk_arm_two_handed_front(surface, cx, cy, facing, phase, hand_pos, action, attack_progress=0):
        hx, hy = hand_pos
        pygame.draw.line(surface, _NS_drakar.PALETTE["shadow_deep"], (cx+facing*20,cy+2), (hx,hy), 12)
        pygame.draw.line(surface, _NS_drakar.PALETTE["skin_darkest"], (cx+facing*20,cy+2), (hx,hy), 10)
        pygame.draw.line(surface, _NS_drakar.PALETTE["skin_dark"], (cx+facing*20,cy+2), (hx,hy), 8)
        pygame.draw.line(surface, _NS_drakar.PALETTE["skin_mid"], (cx+facing*20,cy+1), (hx,hy), 4)
        pygame.draw.line(surface, _NS_drakar.PALETTE["skin_light"], (cx+facing*20,cy), (hx,hy), 2)
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_darkest"], (hx,hy), (hx+facing*5,hy+8), 10)
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_dark"], (hx,hy), (hx+facing*5,hy+8), 8)
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_mid"], (hx,hy), (hx+facing*5,hy+7), 4)
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_darkest"], (hx-5,hy-3,12,10))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_dark"], (hx-4,hy-2,10,8))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_mid"], (hx-3,hy-1,7,6))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_dark"], (hx-4,hy+2,10,4))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_mid"], (hx-3,hy+2,8,2))

    def _draw_drk_arm_two_handed_back(surface, cx, cy, facing, phase, hand_pos, action):
        hx, hy = hand_pos
        pygame.draw.line(surface, _NS_drakar.PALETTE["shadow_deep"], (cx-facing*18,cy+2), (hx,hy), 12)
        pygame.draw.line(surface, _NS_drakar.PALETTE["skin_darkest"], (cx-facing*18,cy+2), (hx,hy), 10)
        pygame.draw.line(surface, _NS_drakar.PALETTE["skin_dark"], (cx-facing*18,cy+2), (hx,hy), 8)
        pygame.draw.line(surface, _NS_drakar.PALETTE["skin_mid"], (cx-facing*18,cy+1), (hx,hy), 4)

    def _compute_two_handed_grip(cx, cy, facing, phase, action, attack_progress=0, spin_angle=0):
        if action == "attack":
            p = attack_progress
            if p < 0.15:
                t=p/0.15; axe_angle=-0.8-t*0.5; axe_x=cx+facing*(30-t*10); axe_y=cy-20-t*15
            elif p < 0.40:
                t=(p-0.15)/0.25; axe_angle=-1.3+t*0.3; axe_x=cx+facing*(20+t*5); axe_y=cy-35+t*10
            elif p < 0.55:
                t=(p-0.40)/0.15; t_ease=1-(1-t)**2
                axe_angle=-1.0+t_ease*2.5; axe_x=cx+facing*(25+t_ease*40); axe_y=cy-25+t_ease*20
            elif p < 0.70:
                t=(p-0.55)/0.15; axe_angle=1.5-t*0.5; axe_x=cx+facing*(65-t*20); axe_y=cy-5+t*5
            else:
                t=(p-0.70)/0.30; t_ease=1-(1-t)**2
                axe_angle=1.0*(1-t_ease)-0.8*t_ease; axe_x=cx+facing*(45-t_ease*15); axe_y=cy+t_ease*5
        elif action == "helix":
            axe_angle = spin_angle
            axe_x = cx+int(math.cos(spin_angle)*40)*facing
            axe_y = cy-10+int(math.sin(spin_angle)*15)
        else:
            bob = math.sin(phase*0.6)*2; axe_angle = -0.8
            axe_x = cx+facing*30; axe_y = cy-20+int(bob)
        pommel_x = axe_x-int(math.cos(axe_angle)*30)*facing
        pommel_y = axe_y-int(math.sin(axe_angle)*30)
        front_hand = (axe_x-int(math.cos(axe_angle)*15)*facing, axe_y-int(math.sin(axe_angle)*15))
        back_hand = (axe_x-int(math.cos(axe_angle)*25)*facing, axe_y-int(math.sin(axe_angle)*25))
        return {"axe_head":(axe_x,axe_y),"axe_angle":axe_angle,"pommel":(pommel_x,pommel_y),
                "front_hand":front_hand,"back_hand":back_hand}

    def _draw_axe(surface, cx, cy, facing, angle, action, attack_progress, pommel_pos=None):
        """Draw MENACING two-handed axe - v2.
        - Besar crescent blade (48px) dengan 16-point sweep.
        - 6-layer gradient halus (offset kecil untuk blending).
        - Rotasi blade konsisten dengan axe_angle.
        - Darah kecil sebagai splatter, bukan lingkaran.
        - Handle kayu dengan bungkus kulit.
        """
        if pommel_pos is None:
            pommel_pos = (cx-int(math.cos(angle)*28)*facing, cy-int(math.sin(angle)*28))
        px, py = pommel_pos

        # ===== HANDLE (kayu gelap + bungkus kulit) =====
        # Shadow
        pygame.draw.line(surface, (10, 8, 6), (px+1,py+1), (cx+1,cy+1), 10)
        # Kayu lapis
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_darkest"], (px,py), (cx,cy), 10)
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_dark"], (px,py), (cx,cy), 8)
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_mid"], (px,py), (cx,cy), 6)
        # Light highlight
        mx = (px + cx) // 2; my = (py + cy) // 2
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_light"], (mx-2,my-1), (mx+2,my+1), 1)
        # Leather wrap texture
        dx = cx - px; dy = cy - py
        h_len = max(1, math.hypot(dx, dy))
        nx = -dy / h_len; ny = dx / h_len
        for i in range(5):
            t = 0.12 + i * 0.16
            gx = int(px + dx * t); gy = int(py + dy * t)
            wrap = [(gx-2-int(nx*2), gy-2-int(ny*2)), (gx+2-int(nx*2), gy+2-int(ny*2)),
                    (gx+2+int(nx*2), gy+2+int(ny*2)), (gx-2+int(nx*2), gy-2+int(ny*2))]
            _NS_drakar._poly(surface, _NS_drakar.PALETTE["leather_darkest"], wrap)

        # ===== POMMEL (emas besar) =====
        pygame.draw.rect(surface, _NS_drakar.PALETTE["shadow_deep"], (px-6,py-6,13,13))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["gold_dark"], (px-5,py-5,11,11))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["gold_mid"], (px-4,py-4,9,9))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["gold_light"], (px-3,py-3,5,5))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["white"], (px-2,py-2,2,2))

        # ===== COLLAR (baja tebal) =====
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_darkest"], (cx-6,cy-6,13,13))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_dark"], (cx-5,cy-5,11,11))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_mid"], (cx-4,cy-4,9,9))
        for rx, ry in [(-3,-3),(3,-3),(-3,3),(3,3)]:
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_light"], (cx+rx,cy+ry,2,2))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_shine"], (cx+rx,cy+ry,1,1))

        # ===== BLADE CRESCENT - BESAR & MENACING =====
        blade_size = 48  # Big but reasonable
        blade_angle = angle + math.pi/2 * facing

        # Sweep crescent dengan 16 points untuk smooth curve
        NUM_PTS = 16
        sweep = math.pi * 0.80  # 144 derajat
        crescent_outer = []
        crescent_inner = []
        for i in range(NUM_PTS):
            t = i / (NUM_PTS - 1.0)
            a = blade_angle - sweep/2 + t * sweep
            # Outer - melengkung menjauh dari pusat
            crescent_outer.append((cx + int(math.cos(a) * blade_size),
                                   cy + int(math.sin(a) * blade_size)))
            # Inner - dengan curve agar blade tajam di ujung
            # Tebal di tengah, tipis di ujung (seperti axe sungguhan)
            thickness = math.sin(t * math.pi)  # 0..1..0
            ir = blade_size * (0.20 + 0.55 * thickness)
            crescent_inner.append((cx + int(math.cos(a) * ir),
                                   cy + int(math.sin(a) * ir)))

        # 6 lapis blade - offset kecil agar blending halus
        layers = [
            (4, "shadow_deep"),
            (3, "blade_darkest"),
            (2, "blade_dark"),
            (0, "blade_mid"),
            (-1, "blade_light"),
            (-2, "blade_shine"),
        ]
        for off, color_key in layers:
            color = _NS_drakar.PALETTE[color_key]
            poly = []
            for (ox, oy) in crescent_outer:
                poly.append((ox + int(math.cos(blade_angle) * off),
                             oy + int(math.sin(blade_angle) * off)))
            for (ix, iy) in reversed(crescent_inner):
                poly.append((ix + int(math.cos(blade_angle) * off * 0.4),
                             iy + int(math.sin(blade_angle) * off * 0.4)))
            if len(poly) >= 3:
                _NS_drakar._poly(surface, color, poly)

        # EDGE HIGHLIGHT di cutting edge (ujung dalam blade)
        edge_pts = [(ix + int(math.cos(blade_angle) * (-2)),
                     iy + int(math.sin(blade_angle) * (-2)))
                    for (ix, iy) in crescent_inner]
        for i in range(len(edge_pts) - 1):
            _NS_drakar._aaline(surface, _NS_drakar.PALETTE["blade_shine"],
                             edge_pts[i], edge_pts[i+1], 1)
        for i in range(len(edge_pts) - 1):
            _NS_drakar._aaline(surface, _NS_drakar.PALETTE["white"],
                             edge_pts[i], edge_pts[i+1], 1)

        # SPECULAR CLUSTER di bagian paling lebar blade
        spec_idx = NUM_PTS // 2 - 1
        spec_x, spec_y = crescent_outer[spec_idx]
        sx = spec_x + int(math.cos(blade_angle) * (-1))
        sy = spec_y + int(math.sin(blade_angle) * (-1))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["blade_shine"], (sx-2, sy-1, 5, 3))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["white"], (sx-1, sy, 3, 1))
        # Second spec cluster
        sx2, sy2 = crescent_outer[spec_idx - 2]
        pygame.draw.rect(surface, _NS_drakar.PALETTE["blade_shine"], (sx2-1, sy2-1, 3, 2))

        # DARAH di blade saat attack - SPLATTER kecil (bukan lingkaran besar)
        if action == "attack" and attack_progress > 0.3:
            intensity = min(1.0, (attack_progress - 0.3) / 0.35)
            rng = _NS_drakar._hash01
            for i in range(10):
                t = 0.2 + i * 0.07
                idx = min(int(t * NUM_PTS), NUM_PTS - 1)
                bx, by = crescent_outer[idx]
                offset = int(rng(i*13 + attack_progress*50) * 10 - 5)
                bx += int(math.cos(blade_angle) * offset)
                by += int(math.sin(blade_angle) * offset)
                # Splatter kecil 3x3, 2x2, atau 1x1
                size = 2 + (int(rng(i*7+3)) % 2)
                pygame.draw.rect(surface, _NS_drakar.PALETTE["blood_darkest"],
                                 (bx-1, by-1, size+1, size+1))
                pygame.draw.rect(surface, _NS_drakar.PALETTE["blood_dark"],
                                 (bx, by, size, size))
                if intensity > 0.7 and rng(i*11) > 0.4:
                    pygame.draw.rect(surface, _NS_drakar.PALETTE["blood_mid"],
                                     (bx, by, size-1, size-1))

        # GLOW EFFECT saat attack - aura merah tipis di blade edge
        if action == "attack" and attack_progress > 0.35:
            intensity = min(1.0, (attack_progress - 0.35) / 0.3)
            glow_r = max(1, int(8 * intensity))
            for i in range(0, NUM_PTS, 3):
                gx, gy = crescent_inner[i]
                for r in range(glow_r, 0, -1):
                    alpha = int(60 * intensity * (glow_r - r + 1) / glow_r)
                    if alpha > 0:
                        rage_color = _NS_drakar.PALETTE["rage_dark"]
                        _NS_drakar._aacircle(surface,
                            (rage_color[0], rage_color[1], rage_color[2], alpha),
                            (gx, gy), r)

    def _draw_drk_head(surface, cx, cy, facing, phase, action):
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_darkest"], (cx-8,cy+12,16,10))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_dark"], (cx-7,cy+12,14,9))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_mid"], (cx-5,cy+13,10,7))
        head_pts = [(cx-12,cy+8),(cx-14,cy),(cx-12,cy-10),(cx-8,cy-15),(cx+8,cy-15),
                    (cx+12,cy-10),(cx+14,cy),(cx+12,cy+8),(cx+8,cy+12),(cx-8,cy+12)]
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["shadow_deep"], [(px+2,py+2) for px,py in head_pts])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["skin_darkest"], head_pts)
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["skin_dark"],
            [(cx-11,cy+7),(cx-13,cy),(cx-11,cy-9),(cx-7,cy-14),(cx+7,cy-14),
             (cx+11,cy-9),(cx+13,cy),(cx+11,cy+7)])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["skin_mid"],
            [(cx-9,cy+5),(cx-11,cy-1),(cx-9,cy-8),(cx-5,cy-12),(cx+5,cy-12),
             (cx+9,cy-8),(cx+11,cy-1),(cx+9,cy+5)])
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_light"], (cx-6,cy-6,8,5))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_shine"], (cx-4,cy-5,4,2))
        for eye_side in (-1, 1):
            ex=cx+eye_side*5; ey=cy-3
            pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_darkest"], (ex-3,ey-2,6,4))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["eye_dark"], (ex-2,ey-1,4,3))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["eye_mid"], (ex-1,ey-1,3,2))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["eye_light"], (ex,ey-1,1,1))
            if action == "attack":
                _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["eye_glow"], (ex,ey), 3)
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_darkest"], (cx-9,cy-6,18,3))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_dark"], (cx-8,cy-6,16,2))
        _NS_drakar._draw_wild_hair(surface, cx, cy-14, facing, phase)
        _NS_drakar._draw_beard(surface, cx, cy+6, facing, phase)
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_dark"], (cx-2,cy-1,4,5))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_mid"], (cx-1,cy,2,3))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_light"], (cx-1,cy,1,1))

    def _draw_wild_hair(surface, cx, cy, facing, phase):
        hair_pts = [(cx-14,cy+4),(cx-16,cy-2),(cx-14,cy-8),(cx-8,cy-12),(cx,cy-14),
                    (cx+8,cy-12),(cx+14,cy-8),(cx+16,cy-2),(cx+14,cy+4)]
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["hair_darkest"], hair_pts)
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["hair_dark"],
            [(cx-12,cy+3),(cx-14,cy-2),(cx-12,cy-7),(cx-6,cy-11),(cx,cy-13),
             (cx+6,cy-11),(cx+12,cy-7),(cx+14,cy-2),(cx+12,cy+3)])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["hair_mid"],
            [(cx-8,cy),(cx-10,cy-4),(cx-6,cy-8),(cx,cy-10),(cx+6,cy-8),(cx+10,cy-4),(cx+8,cy)])
        spine = [(cx-14,cy+2),(cx-10,cy-6),(cx,cy-12),(cx+10,cy-6),(cx+14,cy+2)]
        tufts = _NS_drakar._tuft_points(spine, depth=5.0, min_len=6, seed=42)
        if len(tufts) > 2:
            pygame.draw.lines(surface, _NS_drakar.PALETTE["hair_dark"], False,
                             [(int(x),int(y)) for x,y in tufts], 2)
        for i in range(3):
            hx=cx-4+i*4; hy=cy-8-int(_NS_drakar._hash01(i*11)*4)
            pygame.draw.rect(surface, _NS_drakar.PALETTE["hair_light"], (hx,hy,2,1))

    def _draw_beard(surface, cx, cy, facing, phase):
        beard_pts = [(cx-10,cy),(cx-12,cy+6),(cx-8,cy+14),(cx-3,cy+18),
                     (cx+3,cy+18),(cx+8,cy+14),(cx+12,cy+6),(cx+10,cy)]
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["hair_darkest"], beard_pts)
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["hair_dark"],
            [(cx-8,cy+1),(cx-10,cy+6),(cx-6,cy+13),(cx-2,cy+16),(cx+2,cy+16),
             (cx+6,cy+13),(cx+10,cy+6),(cx+8,cy+1)])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["hair_mid"],
            [(cx-5,cy+2),(cx-7,cy+6),(cx-4,cy+11),(cx,cy+14),(cx+4,cy+11),
             (cx+7,cy+6),(cx+5,cy+2)])
        for i in range(5):
            bx=cx-4+i*2; by=cy+5+int(_NS_drakar._hash01(i*17)*6)
            pygame.draw.rect(surface, _NS_drakar.PALETTE["hair_light"], (bx,by,1,1))

    def _draw_axe_slash_trail(surface, boss, cx, cy, progress):
        if progress < 0.3 or progress > 0.75: return
        t = (progress-0.3)/0.45
        alpha = _NS_drakar._alpha(220*(1-abs(t-0.5)*2))
        facing = getattr(boss, "_drk_attack_dir", 1)
        trail_surf = pygame.Surface((300, 200), pygame.SRCALPHA)
        tcx, tcy = 150, 100
        for thick, color, a_mult in [
            (14,"blood_darkest",0.5),(10,"blood_dark",0.7),
            (6,"blood_mid",1.0),(3,"blood_light",1.0),(1,"blood_hot",1.0)]:
            arc_pts = []
            start_ang = -math.pi*0.4+t*math.pi*0.3
            end_ang = start_ang+math.pi*0.8
            for step in range(16):
                st = step/15; a = start_ang+st*(end_ang-start_ang)
                r = 50+st*20
                arc_pts.append((tcx+int(math.cos(a)*r)*facing, tcy+int(math.sin(a)*r*0.7)))
            for k in range(len(arc_pts)-1):
                fade = 1-(k/len(arc_pts))
                a_val = _NS_drakar._alpha(alpha*a_mult*fade)
                if a_val <= 0: continue
                pygame.draw.line(trail_surf, _NS_drakar._rgba(_NS_drakar.PALETTE[color], a_val),
                                 arc_pts[k], arc_pts[k+1], thick)
        surface.blit(trail_surf, (cx-150, cy-100))

    def _draw_impact_burst(surface, boss, cx, cy, progress):
        t = (progress-0.53)/0.17
        intensity = math.sin(t*math.pi)
        fs = _NS_drakar._fx_scale(boss)
        _NS_drakar._spark_star(surface, cx+int(30*boss.direction), cy,
            int(24*fs*intensity), _NS_drakar.PALETTE["blood_light"],
            int(220*intensity), spikes=6, rot=progress*3, core=_NS_drakar.PALETTE["blood_hot"])
        rr = int(35*fs*(0.5+t*0.5))
        if rr > 2:
            pygame.draw.ellipse(surface,
                _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"], int(180*intensity)),
                (cx-rr,cy-rr//3,rr*2,max(4,rr*2//3)), 3)
            pygame.draw.ellipse(surface,
                _NS_drakar._rgba(_NS_drakar.PALETTE["blood_hot"], int(140*intensity)),
                (cx-rr+4,cy-rr//3+2,max(1,rr*2-8),max(2,rr*2//3-4)), 2)
        for i in range(5):
            ang=i*math.pi*2/5+progress*2; dist=int(20*fs*t)
            sx=cx+int(math.cos(ang)*dist); sy=cy+int(math.sin(ang)*dist*0.6)
            sz=max(1,int(4*(1-t)))
            pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["armor_dark"], int(200*intensity)),
                (sx,sy,sz,sz))

    def _draw_rage_mist(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        count = 12 if intense else 6
        for i in range(count):
            t = (phase*0.3+i*0.15)%1.0
            px = cx+int(math.sin(phase+i*1.7)*20)+(facing*int(t*10) if trail else 0)
            py = cy-int(t*40)
            alpha = _NS_drakar._alpha(180*(1-t))
            size = max(1, int(3*(1-t)))
            if i%3==0:
                pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["ember_dark"],alpha),
                    (px,py,size+1,size+1))
            pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["ember_mid"],alpha),
                (px,py,size,size))
            if t < 0.5:
                pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["ember_light"],alpha),
                    (px,py,1,1))

    def _draw_shadow(surface, x, y, lift=0):
        """Kontak bayangan - mengecil saat lift naik, dasar tetap menapak."""
        w0 = 150
        h0 = 40
        w = max(60, w0 - lift * 8)
        h = max(15, h0 - lift * 3)
        s = pygame.Surface((w0, h0), pygame.SRCALPHA)
        # Bottom-anchored: ellipse drawn so bottom of ellipse is at bottom of surface
        off_x = (w0 - w) // 2
        off_y = h0 - h
        pygame.draw.ellipse(s, (0,0,0,120), (off_x+2, off_y+2, max(1,w-4), max(1,h-4)))
        pygame.draw.ellipse(s, (0,0,0,80), (off_x+w//6, off_y+h//6, max(1,w-w//3), max(1,h-h//3)))
        # Always blit at same position so bottom stays fixed
        surface.blit(s, (x-w0//2, y-h0//2))

    def _draw_rage_aura(surface, x, y, phase):
        def build_aura():
            s = pygame.Surface((390, 260), pygame.SRCALPHA)
            for r in range(120, 0, -2):
                a = int(40*(120-r)/120)
                pygame.draw.ellipse(s, (*_NS_drakar.PALETTE["rage_darkest"], a),
                    (195-r, 130-r//2, r*2, r))
            return s
        aura = _NS_drakar._static("rage_aura", build_aura)
        pulse_alpha = int(200+55*math.sin(phase*1.5))
        aura.set_alpha(min(255, pulse_alpha))
        surface.blit(aura, (x-195, y-50))

    def _draw_ground_ring(surface, boss, x, y, phase, skill):
        fs = _NS_drakar._fx_scale(boss)
        r = int(65 * fs)
        pulse = 0.7 + 0.3*math.sin(phase*2)
        alpha = _NS_drakar._alpha(180*pulse)
        _NS_drakar._dashed_ring(surface, x, y, r,
            _NS_drakar.PALETTE["rune_dark"], alpha, phase*0.3, segments=12, thick=3, squash=0.4)
        _NS_drakar._dashed_ring(surface, x, y, int(r*0.7),
            _NS_drakar.PALETTE["rune_mid"], int(alpha*0.7),
            -phase*0.5, segments=8, thick=2, squash=0.4)
        for i in range(6):
            ang=phase*0.2+i*math.pi/3
            rx=x+int(math.cos(ang)*r*0.85); ry=y+int(math.sin(ang)*r*0.35)
            pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["rune_light"], alpha), (rx,ry,3,3))

    def _draw_battlehunger_ground(surface, boss, x, y, timer, phase):
        fs = _NS_drakar._fx_scale(boss)
        duration = 90
        progress = max(0.0, min(1.0, 1-timer/duration))
        tx, ty = x, y+105
        if progress < 0.15:
            t = progress/0.15; rr = int(80*fs*t)
            a = int(230*(1-t*0.5))
            pygame.draw.ellipse(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_dark"],a),
                (tx-rr,ty-rr//3,rr*2,max(4,rr*2//3)), 3)
            _NS_drakar._spark_star(surface, tx, ty, int(22*fs),
                _NS_drakar.PALETTE["blood_light"], int(200*(1-t)),
                spikes=8, rot=phase, core=_NS_drakar.PALETTE["rage_light"])
        if progress >= 0.1:
            r = int(80*fs*min(1.0,(progress-0.1)*2))
            if r > 3:
                for off, color, a_mult in [
                    (0,"blood_darkest",1.0),(4,"blood_dark",0.85),(8,"rage_mid",0.7)]:
                    pygame.draw.ellipse(surface,
                        _NS_drakar._rgba(_NS_drakar.PALETTE[color], _NS_drakar._alpha(220*a_mult)),
                        (tx-r+off, ty-r//3+off, max(1,r*2-off*2), max(2,r*2//3-off)))
                if progress > 0.2:
                    for i in range(5):
                        ang=i*math.pi*2/5+phase*0.1
                        _NS_drakar._jagged_crack(surface, tx, ty, ang, int(50*fs),
                            (_NS_drakar.PALETTE["blood_darkest"], _NS_drakar.PALETTE["blood_mid"]),
                            int(160*min(1.0,(progress-0.2)*3)), seed=i*7+13)
                for i in range(8):
                    t=(phase*0.5+i*0.12)%1.0
                    mx=tx+int(math.sin(phase+i*2)*r*0.4); my=ty-int(t*30*fs)
                    a=int(160*(1-t))
                    pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["ember_mid"],a), (mx,my,2,2))

    def _draw_battlehunger_foreground(surface, boss, x, y, timer, phase):
        fs = _NS_drakar._fx_scale(boss)
        duration = 90
        progress = max(0.0, min(1.0, 1-timer/duration))
        tx, ty = x, y+105
        r = int(80*fs*min(1.0, progress*3))
        if r < 5: return
        for i in range(8):
            col_angle=i*math.pi*2/8+phase*0.15
            col_dist=int(r*0.55)
            col_x=tx+int(math.cos(col_angle)*col_dist)
            col_y_base=ty+int(math.sin(col_angle)*col_dist*0.4)
            for layer in range(6):
                layer_t=(phase*0.7+i*0.3+layer*0.15)%1.0
                layer_y=col_y_base-int(layer_t*54)
                layer_alpha=_NS_drakar._alpha(220*(1-layer_t))
                layer_w=int(9+layer_t*4); layer_h=int(6+layer_t*4)
                pygame.draw.ellipse(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_darkest"],layer_alpha),
                    (col_x-layer_w, layer_y-layer_h, layer_w*2, layer_h*2))
                pygame.draw.ellipse(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["rage_mid"],layer_alpha),
                    (col_x-layer_w+3, layer_y-layer_h+3, max(1,layer_w*2-6), max(1,layer_h*2-6)))
                pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["rage_light"],layer_alpha),
                    (col_x,layer_y-2,2,2))
        core_pulse = math.sin(phase*3)*0.4+0.6
        for cr in range(15,0,-1):
            alpha = _NS_drakar._alpha(200*(15-cr)/15*core_pulse)
            _NS_drakar._aacircle(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"],alpha), (tx,ty), cr)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["rage_light"], (tx,ty), 5)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["rage_hot"], (tx,ty), 2)
        for i in range(24):
            angle=i*math.pi*2/24+phase*0.4
            sp_r=int(r*(0.4+(i%3)*0.2))
            sx=tx+int(math.cos(angle)*sp_r); sy=ty+int(math.sin(angle)*sp_r*0.4)
            alpha = _NS_drakar._alpha(200)
            pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"],alpha), (sx,sy,3,3))
            pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_light"],alpha), (sx,sy,1,1))

    def _draw_counterhelix_ground(surface, boss, x, y, timer, phase):
        fs = _NS_drakar._fx_scale(boss)
        duration = 45
        progress = max(0.0, min(1.0, 1-timer/duration))
        r = int((90+progress*45)*fs)
        alpha = _NS_drakar._alpha(240*(1-progress*0.5))
        if progress < 0.1:
            t = progress/0.1
            _NS_drakar._spark_star(surface, x, y+114, int(28*fs),
                _NS_drakar.PALETTE["blood_light"], int(200*(1-t)),
                spikes=8, rot=phase*2, core=_NS_drakar.PALETTE["blood_hot"])
        _NS_drakar._dashed_ring(surface, x, y+114, r,
            _NS_drakar.PALETTE["blood_dark"], alpha, phase*0.8, segments=12, thick=4, squash=0.4)
        _NS_drakar._dashed_ring(surface, x, y+114, int(r*0.75),
            _NS_drakar.PALETTE["blood_mid"], int(alpha*0.8),
            -phase*1.2, segments=10, thick=3, squash=0.4)
        spin = progress*math.pi*6
        for i in range(4):
            a = spin+i*math.pi/2
            arc_pts = []
            for step in range(12):
                st = step/11; arc_a = a+st*math.pi/3
                arc_pts.append((x+int(math.cos(arc_a)*(r-8)), y+114+int(math.sin(arc_a)*(r-8)*0.4)))
            for k in range(len(arc_pts)-1):
                pygame.draw.line(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_light"],alpha),
                    arc_pts[k], arc_pts[k+1], 4)
                pygame.draw.line(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_hot"],alpha),
                    arc_pts[k], arc_pts[k+1], 2)
        for i in range(6):
            ga = phase*2+i*math.pi/3
            gx = x+int(math.cos(ga)*r*0.6); gy = y+114+int(math.sin(ga)*r*0.25)
            pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_shine"],alpha), (gx,gy,2,2))

    def _draw_berserkerscall_ground(surface, boss, x, y, timer, phase):
        fs = _NS_drakar._fx_scale(boss)
        duration = 60
        progress = max(0.0, min(1.0, 1-timer/duration))
        if progress < 0.2:
            t = progress/0.2; rr = int(40*fs*t); a = int(230*(1-t*0.3))
            pygame.draw.ellipse(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"],a),
                (x-rr,y+114-rr//3,rr*2,max(4,rr*2//3)), 3)
            _NS_drakar._spark_star(surface, x, y+114, int(18*fs),
                _NS_drakar.PALETTE["rage_light"], int(200*(1-t)), spikes=6, rot=phase)
        if progress > 0.15:
            t = (progress-0.15)/0.85
            r = int((67+t*120)*fs)
            base_alpha = _NS_drakar._alpha(240*(1-t))
            _NS_drakar._dashed_ring(surface, x, y+114, r,
                _NS_drakar.PALETTE["blood_mid"], base_alpha, phase*0.6, segments=14, thick=3, squash=0.4)
            for i in range(8):
                ang = i*math.pi*2/8+phase*0.3
                _NS_drakar._chevron(surface,
                    x+int(math.cos(ang)*r), y+114+int(math.sin(ang)*r*0.4),
                    ang, int(10*fs), _NS_drakar.PALETTE["blood_light"], base_alpha, width=2)

    def _draw_berserkerscall_foreground(surface, boss, x, y, timer, phase):
        fs = _NS_drakar._fx_scale(boss)
        duration = 60
        progress = max(0.0, min(1.0, 1-timer/duration))
        if progress < 0.3:
            t = progress/0.3; glow_r = int((18+t*18)*fs)
            for r in range(glow_r+9,0,-1):
                alpha = _NS_drakar._alpha(180*(glow_r+9-r)/(glow_r+9)*t)
                _NS_drakar._aacircle(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_dark"],alpha), (x,y-6), r)
            _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["blood_mid"], (x,y-6), 15)
            _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["rage_light"], (x,y-6), 9)
            _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["rage_hot"], (x,y-6), 4)
            _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["white"], (x,y-6), 2)
            for i in range(12):
                angle=i*math.pi/6
                mist_x=x+int(math.cos(angle)*45*fs*t); mist_y=y-12+int(math.sin(angle)*37*fs*t)
                alpha = _NS_drakar._alpha(200*t)
                _NS_drakar._aacircle(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"],alpha), (mist_x,mist_y), 6)
                _NS_drakar._aacircle(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["rage_light"],alpha), (mist_x,mist_y), 3)
        else:
            t = (progress-0.3)/0.7; wave_r = int(t*195*fs)
            for i in range(28):
                angle=i*math.pi*2/28
                px=x+int(math.cos(angle)*wave_r); py=y-12+int(math.sin(angle)*wave_r*0.7)
                alpha = _NS_drakar._alpha(240*(1-t))
                _NS_drakar._aacircle(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_dark"],alpha), (px,py), 7)
                _NS_drakar._aacircle(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"],alpha), (px,py), 6)
                _NS_drakar._aacircle(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["rage_light"],alpha), (px,py), 3)
                pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["rage_hot"],alpha), (px,py,3,3))
                pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["white"],alpha), (px,py,1,1))
            for i in range(14):
                angle=i*math.pi/7
                inner_r=int(wave_r*0.65); outer_r=wave_r
                p1=(x+int(math.cos(angle)*inner_r), y-12+int(math.sin(angle)*inner_r*0.7))
                p2=(x+int(math.cos(angle)*outer_r), y-12+int(math.sin(angle)*outer_r*0.7))
                alpha = _NS_drakar._alpha(220*(1-t))
                pygame.draw.line(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_light"],alpha), p1, p2, 4)
                pygame.draw.line(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["rage_hot"],alpha), p1, p2, 2)

    def _draw_cullingblade_ground(surface, boss, x, y, timer, phase):
        fs = _NS_drakar._fx_scale(boss)
        tx, ty = _NS_drakar._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1-timer/duration))
        if progress < 0.4:
            t = progress/0.4; r = int(75*fs*t); alpha = _NS_drakar._alpha(200*t)
            _NS_drakar._dashed_ring(surface, tx, ty, r,
                _NS_drakar.PALETTE["blood_dark"], alpha, phase*0.8, segments=10, thick=4, squash=0.4)
            for i in range(6):
                ang=i*math.pi/3+phase*0.5
                _NS_drakar._chevron(surface, tx+int(math.cos(ang)*r), ty+int(math.sin(ang)*r*0.4),
                    ang+math.pi, int(12*fs), _NS_drakar.PALETTE["blood_light"], alpha, width=2)
            _NS_drakar._spark_star(surface, tx, ty, int(15*fs*t),
                _NS_drakar.PALETTE["blood_hot"], int(180*t), spikes=4, rot=phase*2)
        if progress >= 0.4:
            t = (progress-0.4)/0.6
            r = int((75+t*45)*fs); alpha = _NS_drakar._alpha(240*(1-t*0.5))
            pygame.draw.ellipse(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_darkest"],alpha),
                (tx-r,ty-r//3,r*2,r*2//3))
            pygame.draw.ellipse(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_dark"],alpha),
                (tx-r+7,ty-r//3+6,max(1,r*2-14),max(2,r*2//3-12)))
            for i in range(7):
                ang=i*math.pi*2/7+0.3
                _NS_drakar._jagged_crack(surface, tx, ty, ang, int(60*fs),
                    (_NS_drakar.PALETTE["blood_darkest"], _NS_drakar.PALETTE["blood_mid"]),
                    int(180*(1-t)), seed=i*11+7)

    def _draw_cullingblade_foreground(surface, boss, x, y, timer, phase):
        fs = _NS_drakar._fx_scale(boss)
        tx, ty = _NS_drakar._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1-timer/duration))
        if progress < 0.4:
            t = progress/0.4; facing = boss.direction
            charge_x = x+facing*60; charge_y = y-9; cr = int((12+t*15)*fs)
            for r in range(cr+10,0,-1):
                alpha = _NS_drakar._alpha(220*(cr+10-r)/(cr+10))
                _NS_drakar._aacircle(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_darkest"],alpha), (charge_x,charge_y), r)
            for r in range(cr,0,-1):
                alpha = _NS_drakar._alpha(240*(cr-r+1)/cr)
                _NS_drakar._aacircle(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"],alpha), (charge_x,charge_y), r)
            _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["blood_light"], (charge_x,charge_y), max(1,cr-4))
            _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["rage_light"], (charge_x,charge_y), max(1,cr-7))
            _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["rage_hot"], (charge_x,charge_y), max(1,cr-10))
            _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["white"], (charge_x,charge_y), max(1,cr-13))
        elif progress < 0.65:
            t = (progress-0.4)/0.25; intensity = math.sin(t*math.pi)
            slash_len = int((97+t*37)*fs)
            for slash_dir in [(1,1),(1,-1)]:
                dx,dy = slash_dir
                p1 = (tx-dx*slash_len, ty-dy*slash_len); p2 = (tx+dx*slash_len, ty+dy*slash_len)
                for thick, color, a_mult in [
                    (16,"blood_darkest",0.6),(12,"blood_dark",0.8),(8,"blood_mid",1.0),
                    (5,"blood_light",1.0),(3,"blood_hot",1.0),(1,"blood_shine",1.0)]:
                    alpha = _NS_drakar._alpha(255*intensity*a_mult)
                    if alpha <= 0: continue
                    pygame.draw.line(surface, _NS_drakar._rgba(_NS_drakar.PALETTE[color], alpha), p1, p2, thick)
            for r in range(int(37*fs),0,-1):
                alpha = _NS_drakar._alpha(240*intensity*(int(37*fs)-r)/max(1,int(37*fs)))
                _NS_drakar._aacircle(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_hot"],alpha), (tx,ty), r)
            _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["blood_shine"], (tx,ty), int(15*fs))
            _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["white"], (tx,ty), int(7*fs))
            _NS_drakar._spark_star(surface, tx, ty, int(30*fs*intensity),
                _NS_drakar.PALETTE["blood_light"], int(220*intensity),
                spikes=8, rot=phase*4, core=_NS_drakar.PALETTE["white"])
            for i in range(20):
                angle=i*math.pi/10; spatter_len=int(slash_len*0.8)
                sx=tx+int(math.cos(angle)*spatter_len); sy=ty+int(math.sin(angle)*spatter_len)
                alpha = _NS_drakar._alpha(240*intensity)
                pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"],alpha), (sx,sy,5,5))
                pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_hot"],alpha), (sx,sy,4,4))
                pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_shine"],alpha), (sx,sy,2,2))
        else:
            t = (progress-0.65)/0.35
            for i in range(18):
                fall_t = (phase*0.5+i*0.1)%1.0
                rx=tx+int(math.sin(phase+i)*60); ry=ty-36+int(fall_t*60)
                alpha = _NS_drakar._alpha(220*(1-t)*(1-fall_t*0.5))
                if alpha > 0:
                    pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_dark"],alpha), (rx,ry,4,6))
                    pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"],alpha), (rx,ry,3,4))
            for slash_dir in [(1,1),(1,-1)]:
                dx,dy = slash_dir; slash_len=60
                p1=(tx-dx*slash_len, ty-dy*slash_len); p2=(tx+dx*slash_len, ty+dy*slash_len)
                alpha = _NS_drakar._alpha(150*(1-t))
                pygame.draw.line(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_dark"],alpha), p1, p2, 4)
                pygame.draw.line(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"],alpha), p1, p2, 2)

class _NS_abaddon:
    """Namespace abaddon - ORIGINAL-MAX: sprite flame + aura cache,
    hurt flash, bayangan reaktif. Isi seni asli tidak diubah."""

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ORIGINAL-MAX caches (dibangun lazy, piksel identik dengan draw asli)
    _AB_FLAME = {}     # sprite cyan flame per (s, alpha//8)
    _AB_AURA1 = None   # gradien aura gelap (pulse via set_alpha)
    _AB_AURA2 = None   # gradien glow cyan
    _AB_BUF = None     # buffer body saat hurt flash
    _AB_SHADOW = None  # tekstur bayangan (reaktif via lift)

    # ---------------------------------------------------------------------------
    # HD Color Palette - Abaddon inspired dark purple / cyan flame
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Cape / cloth - deep purple
        "cape_darkest":   (18,   8,  32),
        "cape_dark":      (35,  20,  62),
        "cape_mid":       (60,  38, 105),
        "cape_light":     (95,  70, 155),
        "cape_high":      (140, 115, 195),
        "cape_shine":     (185, 165, 225),

        # Armor - dark purple/black with gold trim
        "armor_darkest":  (12,   8,  22),
        "armor_dark":     (28,  20,  48),
        "armor_mid":      (55,  42,  85),
        "armor_light":    (95,  78, 130),
        "armor_high":     (150, 130, 180),

        # Gold trim
        "gold_darkest":   (65,  42,  10),
        "gold_dark":      (115, 85,  25),
        "gold_mid":       (175, 140, 45),
        "gold_light":     (225, 190, 85),
        "gold_shine":     (250, 225, 145),

        # Horse body - dark blue-purple
        "horse_darkest":  (10,  15,  30),
        "horse_dark":     (25,  35,  60),
        "horse_mid":      (50,  70, 105),
        "horse_light":    (85, 115, 155),
        "horse_high":     (135, 170, 200),

        # Cyan flame / mist - the signature color
        "flame_darkest":  (5,   45,  55),
        "flame_dark":     (15,  95, 115),
        "flame_mid":      (40, 170, 185),
        "flame_light":    (95, 230, 235),
        "flame_bright":   (160, 250, 250),
        "flame_hot":      (215, 255, 255),
        "flame_white":    (240, 255, 255),

        # Sword blade - cyan energy blade
        "blade_darkest":  (30,  55,  70),
        "blade_dark":     (60, 120, 145),
        "blade_mid":      (110, 190, 210),
        "blade_light":    (170, 235, 240),
        "blade_shine":    (220, 250, 250),

        # Purple magic (for skills)
        "magic_darkest":  (20,   5,  50),
        "magic_dark":     (55,  25, 115),
        "magic_mid":      (105, 60, 180),
        "magic_light":    (165, 120, 225),
        "magic_bright":   (210, 175, 250),
        "magic_hot":      (240, 220, 255),

        # Eye glow
        "eye_dark":       (30,  90, 100),
        "eye_mid":        (90, 200, 205),
        "eye_bright":     (170, 245, 245),
        "eye_hot":        (230, 255, 255),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (3,   4,   8),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_abaddon._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_abaddon.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_abaddon._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width
            min_y = min(sy, ey) - width
            w = abs(ex - sx) + width * 4 + 4
            h = abs(ey - sy) + width * 4 + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.line(temp, color,
                             (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), max(1, width))
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), max(1, width))


    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_abaddon._clamp(color)
        if len(color) == 4 and color[3] < 255:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, min_y = min(xs) - 2, min(ys) - 2
            w = max(xs) - min_x + 4
            h = max(ys) - min_y + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            shifted = [(p[0] - min_x, p[1] - min_y) for p in points]
            pygame.draw.polygon(temp, color, shifted)
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.polygon(surface, color[:3], points)


    def _ellipse(surface, color, rect, width=0):
        color = _NS_abaddon._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, rw, rh), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3], rect, width)


    def _rect(surface, color, rect, border_radius=0):
        color = _NS_abaddon._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, rw, rh), border_radius=border_radius)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3], rect, border_radius=border_radius)


    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            # Konversi koordinat DUNIA target ke ruang jangkar (x, y)
            # DENGAN kompensasi scale. Hero di-render ke canvas
            # offscreen lalu di-scale saat blit (heroes/__init__.py),
            # jadi titik canvas harus = (delta dunia)/scale supaya
            # beam/proyektil mendarat TEPAT di target setelah blit.
            # Boss yang digambar langsung di layar tidak terpengaruh
            # (scale = 1).
            scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        return int(x + 200 / float(getattr(boss, "_render_scale", 1.0) or 1.0) * getattr(boss, "direction", 1)), int(y)


    # ---------------------------------------------------------------------------
    # Cyan flame helper
    # ---------------------------------------------------------------------------
    def _draw_cyan_flame(surface, x, y, size, phase, alpha=255):
        """Draw a cyan mist flame particle. ORIGINAL-MAX: hasil draw
        di-cache sebagai sprite per (s, alpha//8) - piksel identik,
        posisi tetap kontinu; hanya draw-call yang diganti blit."""
        flick = math.sin(phase * 3) * 0.15 + 1.0
        s = int(size * flick)
        if s < 1:
            return
        a = min(255, int(alpha)) // 8 * 8
        key = (s, a)
        B = _NS_abaddon
        cache = B._AB_FLAME
        if key not in cache:
            r = s + 4
            f = pygame.Surface((r * 2, r * 2 + 4), pygame.SRCALPHA)
            cx0, cy0 = r, r + 2
            B._aacircle(f, (*B.PALETTE["flame_darkest"], a // 3),
                        (cx0, cy0), s + 3)
            B._aacircle(f, (*B.PALETTE["flame_dark"], a // 2),
                        (cx0, cy0), s + 1)
            B._aacircle(f, (*B.PALETTE["flame_mid"], a), (cx0, cy0), s)
            B._aacircle(f, (*B.PALETTE["flame_light"], a), (cx0, cy0 - 1),
                        max(1, s - 2))
            B._aacircle(f, (*B.PALETTE["flame_bright"], min(255, a)),
                        (cx0, cy0 - 2), max(1, s - 4))
            if s > 3:
                B._aacircle(f, (*B.PALETTE["flame_hot"], min(255, a)),
                            (cx0, cy0 - 3), max(1, s - 6))
            cache[key] = f
        spr = cache[key]
        surface.blit(spr, (x - (s + 4), y - (s + 6)))


    def _draw_flame_streamer(surface, x, y, height, phase, alpha=220):
        """Draw a rising cyan flame streamer."""
        for i in range(height):
            t = i / max(1, height)
            wave = math.sin(phase * 3 + t * 5) * 2
            size = int(3 * (1 - t * 0.7))
            if size < 1:
                break
            fx = x + int(wave)
            fy = y - i
            f_alpha = int(alpha * (1 - t * 0.6))
            _NS_abaddon._draw_cyan_flame(surface, fx, fy, size, phase, f_alpha)


    # ---------------------------------------------------------------------------
    # PROJECTILE / EFFECT SYSTEM
    # ---------------------------------------------------------------------------
    class MistCoilProjectile:
        """Q - Purple/cyan orb projectile."""
        def __init__(self, sx, sy, tx, ty, speed=6.0):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            self.trail = []

        def update(self):
            if not self.alive:
                return
            self.age += 1
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < self.speed + 4:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 14:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            if not self.alive and self.age < 3:
                return

            # Long misty trail (purple/cyan)
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(40 + i * 15)
                r = max(1, 6 - (len(self.trail) - i) // 2)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_dark"], alpha), (tx, ty), r + 2)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_mid"], alpha), (tx, ty), r)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_mid"], alpha // 2),
                          (tx, ty), max(1, r - 1))

            if self.alive:
                px, py = int(self.x), int(self.y)
                # Multi-layer orb
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_darkest"], 180), (px, py), 10)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_dark"], 220), (px, py), 8)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_mid"], 240), (px, py), 6)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_mid"], 240), (px, py), 4)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], 250), (px, py), 3)
                _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_hot"], (px, py), 2)
                _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_white"], (px, py), 1)

                # Mist trails
                for i in range(4):
                    angle = phase * 4 + i * math.pi / 2
                    sx = px + int(math.cos(angle) * 10)
                    sy = py + int(math.sin(angle) * 10)
                    _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_light"], 200), (sx, sy), 2)
                    _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_hot"], (sx, sy), 1)


    class DarknessGaleProjectile:
        """E - Dark wave/gale that travels forward."""
        def __init__(self, sx, sy, direction, max_dist=250):
            self.x = float(sx)
            self.y = float(sy)
            self.direction = direction
            self.max_dist = max_dist
            self.speed = 11.0
            self.alive = True
            self.age = 0
            self.max_age = 25

        def update(self):
            if not self.alive:
                return
            self.age += 1
            self.x += self.speed * self.direction
            if self.age >= self.max_age:
                self.alive = False

        def draw(self, surface, phase):
            if not self.alive and self.age < 2:
                return
            t = self.age / self.max_age
            alpha = int(255 * (1 - t * 0.5))
            px, py = int(self.x), int(self.y)

            # Elongated gale/wind streak
            for i in range(-6, 7):
                # Multiple parallel streaks
                for streak_off in (-4, 0, 4):
                    streak_y = py + i * 2 + streak_off
                    # Length varies
                    for length_i in range(20):
                        lt = length_i / 20
                        lx = px - int(lt * 40) * self.direction
                        ly = streak_y + int(math.sin(lt * 5 + phase + i) * 2)

                        w_alpha = int(alpha * (1 - abs(i) / 7) * (1 - lt * 0.4))
                        if w_alpha <= 0:
                            continue

                        _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_dark"], w_alpha),
                                  (lx, ly), 2)
                        _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_dark"], w_alpha),
                                  (lx, ly), 1)

            # Bright forward core
            for i in range(-4, 5):
                core_y = py + i * 2
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_mid"], alpha),
                          (px, core_y), 3)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], alpha),
                          (px, core_y), 2)
                _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_hot"], (px, core_y), 1)

            # Bright tip
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], alpha),
                      (px + 8 * self.direction, py), 4)
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_hot"],
                      (px + 8 * self.direction, py), 3)
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_white"],
                      (px + 8 * self.direction, py), 1)


    class DeathSeverWave:
        """R - Purple crescent wave."""
        def __init__(self, sx, sy, direction, max_dist=200):
            self.x = float(sx)
            self.y = float(sy)
            self.direction = direction
            self.max_dist = max_dist
            self.speed = 9.0
            self.alive = True
            self.age = 0
            self.max_age = 22

        def update(self):
            if not self.alive:
                return
            self.age += 1
            self.x += self.speed * self.direction
            if self.age >= self.max_age:
                self.alive = False

        def draw(self, surface, phase):
            if not self.alive:
                return
            t = self.age / self.max_age
            alpha = int(255 * (1 - t * 0.4))
            px, py = int(self.x), int(self.y)

            # Purple crescent wave
            for i in range(-14, 15):
                curve = math.cos(i * 0.2) * 8
                vy = py + i * 2
                vx = px + int(curve) * self.direction

                w_alpha = int(alpha * (1 - abs(i) / 15))
                if w_alpha <= 0:
                    continue

                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_darkest"], w_alpha),
                          (vx, vy), 5)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_dark"], w_alpha),
                          (vx, vy), 4)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_mid"], w_alpha),
                          (vx, vy), 3)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_light"], w_alpha),
                          (vx, vy), 2)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_bright"], w_alpha),
                          (vx, vy), 1)

            # Bright core arc
            for i in range(-12, 13):
                curve = math.cos(i * 0.2) * 8
                vy = py + i * 2
                vx = px + int(curve) * self.direction
                core_alpha = int(alpha * (1 - abs(i) / 13))
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_hot"], core_alpha),
                          (vx, vy), 2)
                _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["white"], (vx, vy), 1)

            # Trailing purple sparks
            for i in range(6):
                angle = phase * 3 + i * math.pi / 3
                r = 15 + int(math.sin(phase + i) * 4)
                sx = px + int(math.cos(angle) * r) * self.direction
                sy = py + int(math.sin(angle) * r)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_bright"], alpha), (sx, sy), 2)
                _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["magic_hot"], (sx, sy), 1)


    # ---------------------------------------------------------------------------
    # State management
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_ab_last_x"):
            boss._ab_last_x = boss.x
            boss._ab_last_y = boss.y
            return False
        dx = abs(boss.x - boss._ab_last_x)
        dy = abs(boss.y - boss._ab_last_y)
        boss._ab_last_x = boss.x
        boss._ab_last_y = boss.y
        return dx + dy > 0.3


    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_ab_prev_timer", 0))
        active = bool(getattr(boss, "_ab_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._ab_attack_active = True
            boss._ab_attack_frame = 0
            active = True
        elif active:
            boss._ab_attack_frame = int(getattr(boss, "_ab_attack_frame", 0)) + 1
            if boss._ab_attack_frame > cooldown:
                boss._ab_attack_active = False
                boss._ab_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._ab_attack_active = False
            boss._ab_attack_frame = 0
            active = False

        boss._ab_prev_timer = timer
        boss._ab_attack_progress = (
            min(1.0, getattr(boss, "_ab_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_ab_projectiles"):
            boss._ab_projectiles = []
        for p in boss._ab_projectiles:
            p.update()
            p.draw(surface, phase)
        boss._ab_projectiles = [p for p in boss._ab_projectiles
                               if p.alive or p.age < 8]


    def _spawn_mist_coil(boss, x, y):
        if not hasattr(boss, "_ab_projectiles"):
            boss._ab_projectiles = []
        tx, ty = _NS_abaddon._target_position(boss, x, y)
        sx = x + 26 * boss.direction
        sy = y - 10
        boss._ab_projectiles.append(_NS_abaddon.MistCoilProjectile(sx, sy, tx, ty, speed=6.5))


    def _spawn_darkness_gale(boss, x, y):
        if not hasattr(boss, "_ab_projectiles"):
            boss._ab_projectiles = []
        sx = x + 30 * boss.direction
        sy = y - 8
        boss._ab_projectiles.append(_NS_abaddon.DarknessGaleProjectile(sx, sy, boss.direction))


    def _spawn_death_sever(boss, x, y):
        if not hasattr(boss, "_ab_projectiles"):
            boss._ab_projectiles = []
        sx = x + 30 * boss.direction
        sy = y - 8
        boss._ab_projectiles.append(_NS_abaddon.DeathSeverWave(sx, sy, boss.direction))


    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_abaddon(surface, boss, x, y):
        """Entry point."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_abaddon._detect_moving(boss)
        _NS_abaddon._update_attack_anim(boss)

        attacking = (
            getattr(boss, "_ab_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 50) - 15
        )

        # ---------- Background layers ----------
        _NS_abaddon._draw_dark_aura(surface, x, y, pulse)
        _NS_abaddon._draw_ground_runes(surface, x, y + 48, pulse, active_skill)

        # ---------- Character body ----------
        # ORIGINAL-MAX hurt flash: saat kena hit, body dirender ke buffer
        # lalu siluetnya dibanjiri putih-hangat (paritas keluarga).
        # Skill R dilewati (beam ke target lebih besar dari buffer).
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        if flash > 0 and active_skill != "r":
            B = _NS_abaddon
            if B._AB_BUF is None:
                B._AB_BUF = pygame.Surface((200, 200), pygame.SRCALPHA)
            tgt, tx, ty = B._AB_BUF, 100, 110
            tgt.fill((0, 0, 0, 0))
        else:
            tgt, tx, ty, flash = surface, x, y, 0

        if active_skill == "q":
            _NS_abaddon._draw_abaddon_mist_coil(tgt, boss, tx, ty, skill_timer, pulse)
        elif active_skill == "e":
            _NS_abaddon._draw_abaddon_darkness_gale(tgt, boss, tx, ty, skill_timer, pulse)
        elif active_skill == "r":
            _NS_abaddon._draw_abaddon_death_sever(tgt, boss, tx, ty, skill_timer, pulse)
        elif attacking:
            _NS_abaddon._draw_abaddon_melee_attack(tgt, boss, tx, ty)
        elif moving:
            _NS_abaddon._draw_abaddon_walk(tgt, boss, tx, ty)
        else:
            _NS_abaddon._draw_abaddon_idle(tgt, boss, tx, ty)

        if flash > 0:
            surface.blit(tgt, (x - tx, y - ty))
            w = int(235 * min(1.0, flash / 8.0))
            if w > 0:
                m = pygame.mask.from_surface(tgt, 50)
                wht = m.to_surface(setcolor=(w, int(w * 0.9), int(w * 0.8),
                                             255),
                                   unsetcolor=(0, 0, 0, 0))
                # bayangan tanah ikut masuk buffer pose; jangan ikut
                # menyala (flash hanya badan, seperti drakar)
                wht.fill((0, 0, 0, 0),
                         pygame.Rect(0, ty + 46, 200, 200 - (ty + 46)))
                surface.blit(wht, (x - tx, y - ty),
                             special_flags=pygame.BLEND_RGB_ADD)

        # Aphotic Shield goes over body
        if active_skill == "w":
            _NS_abaddon._draw_aphotic_shield(surface, boss, x, y, skill_timer, pulse)

        # ---------- Projectiles ----------
        _NS_abaddon._manage_projectiles(boss, surface, pulse)


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_abaddon_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.8) * 2)
        _NS_abaddon._draw_shadow(surface, x, y + 58, max(0, -bob))
        _NS_abaddon._draw_horse_flame_base(surface, x, y + 45, boss.pulse)
        _NS_abaddon._draw_abaddon_full(surface, x, y + bob, boss.direction, boss.pulse, "idle")


    def _draw_abaddon_walk(surface, boss, x, y):
        phase = boss.pulse * 2.2
        bob = int(abs(math.sin(phase * 1.3)) * 3)
        sway = int(math.sin(phase) * 2)
        _NS_abaddon._draw_shadow(surface, x + sway, y + 58, bob)
        _NS_abaddon._draw_horse_flame_base(surface, x + sway, y + 45, phase, trail=True,
                              facing=boss.direction)
        _NS_abaddon._draw_abaddon_full(surface, x + sway, y - bob, boss.direction, phase, "walk")


    def _draw_abaddon_melee_attack(surface, boss, x, y):
        """Sword swing on horseback."""
        progress = getattr(boss, "_ab_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        lunge = int(math.sin(progress * math.pi) * 4) * boss.direction
        _NS_abaddon._draw_shadow(surface, x + lunge, y + 58)
        _NS_abaddon._draw_horse_flame_base(surface, x + lunge, y + 45, boss.pulse, intense=True)
        _NS_abaddon._draw_abaddon_full(surface, x + lunge, y, boss.direction, boss.pulse,
                          "melee", progress)
        _NS_abaddon._draw_sword_swing_trail(surface, x + lunge, y - 8, boss.direction, progress)


    def _draw_abaddon_mist_coil(surface, boss, x, y, timer, phase):
        """Q - Mist Coil cast."""
        cast_duration = 45
        elapsed = cast_duration - timer
        progress = max(0.0, min(1.0, elapsed / cast_duration))

        if 0.3 < progress < 0.4 and not getattr(boss, "_ab_coil_spawned", False):
            _NS_abaddon._spawn_mist_coil(boss, x, y)
            boss._ab_coil_spawned = True
        if progress < 0.2 or progress > 0.9:
            boss._ab_coil_spawned = False

        _NS_abaddon._draw_shadow(surface, x, y + 58)
        _NS_abaddon._draw_horse_flame_base(surface, x, y + 45, phase, intense=True)
        _NS_abaddon._draw_abaddon_full(surface, x, y, boss.direction, phase, "cast", progress)

        # Casting glow on sword tip
        if 0.15 < progress < 0.5:
            sword_x = x + 32 * boss.direction
            sword_y = y - 20
            glow_pulse = math.sin(phase * 4) * 0.3 + 0.7
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_dark"], 180),
                      (sword_x, sword_y), int(12 * glow_pulse))
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_mid"], 220),
                      (sword_x, sword_y), int(8 * glow_pulse))
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], 240),
                      (sword_x, sword_y), int(5 * glow_pulse))
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_hot"],
                      (sword_x, sword_y), max(1, int(3 * glow_pulse)))


    def _draw_abaddon_darkness_gale(surface, boss, x, y, timer, phase):
        """E - Darkness Gale cast."""
        cast_duration = 40
        elapsed = cast_duration - timer
        progress = max(0.0, min(1.0, elapsed / cast_duration))

        if 0.3 < progress < 0.4 and not getattr(boss, "_ab_gale_spawned", False):
            _NS_abaddon._spawn_darkness_gale(boss, x, y)
            boss._ab_gale_spawned = True
        if progress < 0.2 or progress > 0.9:
            boss._ab_gale_spawned = False

        _NS_abaddon._draw_shadow(surface, x, y + 58)
        _NS_abaddon._draw_horse_flame_base(surface, x, y + 45, phase, intense=True)
        _NS_abaddon._draw_abaddon_full(surface, x, y, boss.direction, phase, "cast", progress)


    def _draw_abaddon_death_sever(surface, boss, x, y, timer, phase):
        """R - Death Sever cast."""
        cast_duration = 50
        elapsed = cast_duration - timer
        progress = max(0.0, min(1.0, elapsed / cast_duration))

        if 0.35 < progress < 0.45 and not getattr(boss, "_ab_sever_spawned", False):
            _NS_abaddon._spawn_death_sever(boss, x, y)
            boss._ab_sever_spawned = True
        if progress < 0.2 or progress > 0.9:
            boss._ab_sever_spawned = False

        lunge = int(math.sin(progress * math.pi) * 6) * boss.direction
        _NS_abaddon._draw_shadow(surface, x + lunge, y + 58)
        _NS_abaddon._draw_horse_flame_base(surface, x + lunge, y + 45, phase, intense=True)
        _NS_abaddon._draw_abaddon_full(surface, x + lunge, y, boss.direction, phase,
                          "melee", progress)
        _NS_abaddon._draw_sword_purple_trail(surface, x + lunge, y - 8, boss.direction,
                                 progress, phase)


    # ===================================================================
    # FULL COMPOSITE - Abaddon + Horse
    # ===================================================================
    def _draw_abaddon_full(surface, cx, cy, facing, phase, action,
                          attack_progress=0):
        """Draw horse + Abaddon rider composition."""
        # Horse (drawn first as background)
        _NS_abaddon._draw_horse(surface, cx, cy + 15, facing, phase)

        # Abaddon rider on top
        _NS_abaddon._draw_abaddon_rider(surface, cx, cy - 8, facing, phase, action,
                           attack_progress)


    # ===================================================================
    # HORSE (ghostly mount)
    # ===================================================================
    def _draw_horse(surface, cx, cy, facing, phase):
        """Ghostly horse mount with cyan flames."""
        step = math.sin(phase * 1.5) * 1

        # Horse body (elongated oval)
        body_pts = [
            (cx - 25 * facing, cy - 2),
            (cx - 22 * facing, cy - 10),
            (cx - 10 * facing, cy - 12),
            (cx + 10 * facing, cy - 12),
            (cx + 20 * facing, cy - 10),
            (cx + 25 * facing, cy - 5),
            (cx + 23 * facing, cy + 8),
            (cx + 12 * facing, cy + 12),
            (cx - 12 * facing, cy + 12),
            (cx - 22 * facing, cy + 8),
        ]
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in body_pts])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_darkest"], body_pts)
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_dark"], [
            (cx - 23 * facing, cy - 1),
            (cx - 20 * facing, cy - 8),
            (cx - 10 * facing, cy - 10),
            (cx + 10 * facing, cy - 10),
            (cx + 18 * facing, cy - 8),
            (cx + 23 * facing, cy - 4),
            (cx + 21 * facing, cy + 7),
            (cx + 10 * facing, cy + 10),
            (cx - 10 * facing, cy + 10),
            (cx - 20 * facing, cy + 7),
        ])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_mid"], [
            (cx - 18 * facing, cy - 3),
            (cx - 15 * facing, cy - 7),
            (cx - 5 * facing, cy - 8),
            (cx + 5 * facing, cy - 8),
            (cx + 15 * facing, cy - 7),
            (cx + 20 * facing, cy - 3),
            (cx + 15 * facing, cy + 6),
            (cx - 15 * facing, cy + 6),
        ])

        # Body highlight (top of back)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["horse_light"], (cx - 5 * facing, cy - 7), 3)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["horse_high"], (cx - 6 * facing, cy - 8), 1)

        # ===== FRONT LEGS =====
        for leg_off in (-8, 0):
            lx = cx + (12 + leg_off) * facing
            # Upper leg
            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["shadow_deep"],
                    (lx + 1, cy + 11), (lx + int(step) + 1, cy + 20), 4)
            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["horse_darkest"],
                    (lx, cy + 11), (lx + int(step), cy + 20), 3)
            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["horse_dark"],
                    (lx, cy + 11), (lx + int(step), cy + 20), 2)
            # Lower leg (dissolves into flame)
            for h in range(8):
                t = h / 8
                fy = cy + 20 + h
                fx = lx + int(step)
                f_alpha = int(200 * (1 - t * 0.5))
                _NS_abaddon._draw_cyan_flame(surface, fx, fy, max(1, 3 - h // 2),
                                phase + h, f_alpha)

        # ===== BACK LEGS =====
        for leg_off in (-8, 0):
            lx = cx + (-12 - leg_off) * facing
            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["shadow_deep"],
                    (lx + 1, cy + 11), (lx - int(step) + 1, cy + 20), 4)
            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["horse_darkest"],
                    (lx, cy + 11), (lx - int(step), cy + 20), 3)
            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["horse_dark"],
                    (lx, cy + 11), (lx - int(step), cy + 20), 2)
            # Flame at hoof
            for h in range(8):
                t = h / 8
                fy = cy + 20 + h
                fx = lx - int(step)
                f_alpha = int(200 * (1 - t * 0.5))
                _NS_abaddon._draw_cyan_flame(surface, fx, fy, max(1, 3 - h // 2),
                                phase + h + 2, f_alpha)

        # ===== HORSE NECK =====
        neck_x = cx + 20 * facing
        neck_y = cy - 8
        neck_top_x = cx + 26 * facing
        neck_top_y = cy - 20

        # Neck shape
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_darkest"], [
            (neck_x - 3 * facing, neck_y),
            (neck_x + 3 * facing, neck_y - 2),
            (neck_top_x + 4 * facing, neck_top_y),
            (neck_top_x - 3 * facing, neck_top_y + 3),
        ])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_dark"], [
            (neck_x - 2 * facing, neck_y - 1),
            (neck_x + 3 * facing, neck_y - 2),
            (neck_top_x + 3 * facing, neck_top_y + 1),
            (neck_top_x - 2 * facing, neck_top_y + 3),
        ])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_mid"], [
            (neck_x, neck_y - 1),
            (neck_x + 2 * facing, neck_y - 2),
            (neck_top_x + 2 * facing, neck_top_y + 1),
            (neck_top_x - 1 * facing, neck_top_y + 3),
        ])

        # ===== HORSE HEAD =====
        head_x = neck_top_x + 2 * facing
        head_y = neck_top_y

        # Head shape (elongated)
        head_pts = [
            (head_x - 5 * facing, head_y - 3),
            (head_x + 3 * facing, head_y - 5),
            (head_x + 12 * facing, head_y - 2),
            (head_x + 13 * facing, head_y + 3),
            (head_x + 8 * facing, head_y + 6),
            (head_x - 3 * facing, head_y + 5),
            (head_x - 6 * facing, head_y + 2),
        ]
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["shadow_deep"], [(p[0] + 1, p[1] + 1) for p in head_pts])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_darkest"], head_pts)
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_dark"], [
            (head_x - 4 * facing, head_y - 2),
            (head_x + 3 * facing, head_y - 4),
            (head_x + 11 * facing, head_y - 1),
            (head_x + 12 * facing, head_y + 3),
            (head_x + 7 * facing, head_y + 5),
            (head_x - 3 * facing, head_y + 4),
            (head_x - 5 * facing, head_y + 1),
        ])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_mid"], [
            (head_x - 2 * facing, head_y - 1),
            (head_x + 2 * facing, head_y - 3),
            (head_x + 9 * facing, head_y - 1),
            (head_x + 10 * facing, head_y + 2),
            (head_x + 5 * facing, head_y + 4),
            (head_x - 2 * facing, head_y + 3),
        ])

        # Horse ears
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_darkest"], [
            (head_x + 1 * facing, head_y - 5),
            (head_x + 3 * facing, head_y - 5),
            (head_x + 2 * facing, head_y - 9),
        ])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_darkest"], [
            (head_x + 5 * facing, head_y - 5),
            (head_x + 7 * facing, head_y - 5),
            (head_x + 6 * facing, head_y - 9),
        ])

        # Horse glowing eye
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["shadow_deep"],
                  (head_x + 5 * facing, head_y), 2)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_dark"],
                  (head_x + 5 * facing, head_y), max(1, int(2 * eye_pulse)))
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_bright"],
                  (head_x + 5 * facing, head_y), 1)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_hot"],
                  (head_x + 5 * facing, head_y - 1), 1)

        # Nostril
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["shadow_deep"],
                  (head_x + 11 * facing, head_y + 2), 1)

        # ===== HORSE MANE (cyan flames along neck) =====
        for i in range(6):
            t = i / 6
            mane_x = neck_x + int((neck_top_x - neck_x) * t) - 3 * facing
            mane_y = neck_y + int((neck_top_y - neck_y) * t) - 2
            _NS_abaddon._draw_flame_streamer(surface, mane_x, mane_y + 3, 6 + i, phase + i,
                                200)

        # ===== HORSE TAIL (flame) =====
        tail_x = cx - 25 * facing
        tail_y = cy - 3
        for i in range(6):
            t = i / 6
            # Tail curves down
            tx = tail_x - int(t * 15) * facing
            ty = tail_y + int(t * 15) + int(math.sin(phase + i) * 2)
            _NS_abaddon._draw_flame_streamer(surface, tx, ty, 8 - i, phase + i, 200)

        # Also curling tail flame
        for i in range(4):
            angle = math.pi * (0.6 + i * 0.15)
            fx = tail_x + int(math.cos(angle) * 10) * facing
            fy = tail_y + int(math.sin(angle) * 12)
            _NS_abaddon._draw_cyan_flame(surface, fx, fy, 4 - i, phase + i, 220)

        # ===== HORSE SADDLE/HARNESS =====
        # Saddle blanket (purple)
        saddle_pts = [
            (cx - 10 * facing, cy - 12),
            (cx + 12 * facing, cy - 12),
            (cx + 10 * facing, cy - 5),
            (cx - 12 * facing, cy - 5),
        ]
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["cape_darkest"], saddle_pts)
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["cape_dark"], [
            (cx - 8 * facing, cy - 11),
            (cx + 10 * facing, cy - 11),
            (cx + 8 * facing, cy - 6),
            (cx - 10 * facing, cy - 6),
        ])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["cape_mid"], [
            (cx - 6 * facing, cy - 10),
            (cx + 6 * facing, cy - 10),
            (cx + 5 * facing, cy - 7),
            (cx - 7 * facing, cy - 7),
        ])

        # Gold saddle trim
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_dark"],
                (cx - 10 * facing, cy - 5), (cx + 10 * facing, cy - 5), 2)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_mid"],
                (cx - 10 * facing, cy - 5), (cx + 10 * facing, cy - 5), 1)

        # Reins (from Abaddon's hand to horse head)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["leather_mid"] if "leather_mid" in _NS_abaddon.PALETTE
                else _NS_abaddon.PALETTE["cape_darkest"],
                (cx + 5 * facing, cy - 10), (head_x + 2 * facing, head_y + 3), 1)


    # ===================================================================
    # ABADDON RIDER
    # ===================================================================
    def _draw_abaddon_rider(surface, cx, cy, facing, phase, action,
                           attack_progress=0):
        """Draw Abaddon on horseback."""
        # Cape (flowing behind)
        _NS_abaddon._draw_cape(surface, cx, cy + 5, facing, phase, action)

        # Rider legs (visible sitting on horse)
        _NS_abaddon._draw_rider_legs(surface, cx, cy + 12, facing, phase)

        # Torso armor
        _NS_abaddon._draw_torso(surface, cx, cy - 3, phase)

        # Pauldrons
        _NS_abaddon._draw_pauldrons(surface, cx, cy - 10, phase)

        # Arms (one holding sword, one holding reins)
        if action in ("melee",):
            _NS_abaddon._draw_melee_arms(surface, cx, cy - 3, facing, phase, attack_progress)
        elif action == "cast":
            _NS_abaddon._draw_casting_arms(surface, cx, cy - 3, facing, phase, attack_progress)
        else:
            _NS_abaddon._draw_idle_arms(surface, cx, cy - 3, facing, phase)

        # Head with hood
        _NS_abaddon._draw_hooded_head(surface, cx, cy - 22, facing, phase)

        # Floating cyan flames around body
        _NS_abaddon._draw_body_flames(surface, cx, cy, phase)


    def _draw_cape(surface, cx, cy, facing, phase, action):
        """Purple flowing cape."""
        wave = math.sin(phase * 0.8) * 3
        wave2 = math.sin(phase * 1.2 + 0.5) * 2

        cape_outer = [
            (cx - 14, cy - 20),
            (cx - 20, cy - 5),
            (cx - 24 - int(wave), cy + 12),
            (cx - 22 - int(wave2), cy + 25),
            (cx - 10, cy + 30 + int(abs(wave))),
            (cx + 10, cy + 30 + int(abs(wave))),
            (cx + 22 + int(wave2), cy + 25),
            (cx + 24 + int(wave), cy + 12),
            (cx + 20, cy - 5),
            (cx + 14, cy - 20),
        ]
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in cape_outer])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["cape_darkest"], cape_outer)

        cape_mid = [
            (cx - 12, cy - 18),
            (cx - 18, cy - 5),
            (cx - 22 - int(wave * 0.7), cy + 10),
            (cx - 18 - int(wave2 * 0.7), cy + 22),
            (cx - 6, cy + 26),
            (cx + 6, cy + 26),
            (cx + 18 + int(wave2 * 0.7), cy + 22),
            (cx + 22 + int(wave * 0.7), cy + 10),
            (cx + 18, cy - 5),
            (cx + 12, cy - 18),
        ]
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["cape_dark"], cape_mid)

        cape_inner = [
            (cx - 10, cy - 15),
            (cx - 15, cy - 5),
            (cx - 18, cy + 8),
            (cx - 10, cy + 20),
            (cx, cy + 22),
            (cx + 10, cy + 20),
            (cx + 18, cy + 8),
            (cx + 15, cy - 5),
            (cx + 10, cy - 15),
        ]
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["cape_mid"], cape_inner)

        # Cape highlights
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["cape_light"],
                (cx - 8, cy - 12), (cx - 12, cy + 15), 1)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["cape_light"],
                (cx + 8, cy - 12), (cx + 12, cy + 15), 1)


    def _draw_rider_legs(surface, cx, cy, facing, phase):
        """Rider legs on horse."""
        for side in (-1, 1):
            # Thigh (goes to knee)
            thigh_x = cx + side * 5
            thigh_top = cy
            thigh_bot = cy + 8

            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["shadow_deep"],
                    (thigh_x + 1, thigh_top + 1), (thigh_x + 1, thigh_bot + 1), 6)
            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["armor_darkest"],
                    (thigh_x, thigh_top), (thigh_x, thigh_bot), 5)
            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["armor_dark"],
                    (thigh_x, thigh_top), (thigh_x, thigh_bot), 3)
            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["armor_mid"],
                    (thigh_x - 1, thigh_top), (thigh_x - 1, thigh_bot), 1)

            # Boot area (sticking out below horse)
            boot_x = thigh_x
            boot_y = thigh_bot + 4
            _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["shadow_deep"],
                  (boot_x - 4, boot_y - 2, 8, 8))
            _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["armor_darkest"],
                  (boot_x - 3, boot_y - 2, 7, 7))
            _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["armor_dark"],
                  (boot_x - 3, boot_y - 2, 7, 5))
            # Gold boot detail
            _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["gold_dark"], (boot_x - 3, boot_y, 7, 1))
            _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["gold_mid"], (boot_x - 3, boot_y, 6, 1))


    def _draw_torso(surface, cx, cy, phase):
        """Torso armor."""
        # Shadow
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["shadow_deep"], [
            (cx - 12 + 2, cy - 8 + 2), (cx + 12 + 2, cy - 8 + 2),
            (cx + 11 + 2, cy + 12 + 2), (cx - 11 + 2, cy + 12 + 2),
        ])

        torso_pts = [
            (cx - 12, cy - 8),
            (cx + 12, cy - 8),
            (cx + 13, cy + 5),
            (cx + 10, cy + 12),
            (cx - 10, cy + 12),
            (cx - 13, cy + 5),
        ]
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["armor_darkest"], torso_pts)
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["armor_dark"], [
            (cx - 10, cy - 6),
            (cx + 10, cy - 6),
            (cx + 11, cy + 5),
            (cx + 8, cy + 10),
            (cx - 8, cy + 10),
            (cx - 11, cy + 5),
        ])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["armor_mid"], [
            (cx - 7, cy - 3),
            (cx + 7, cy - 3),
            (cx + 8, cy + 4),
            (cx + 5, cy + 8),
            (cx - 5, cy + 8),
            (cx - 8, cy + 4),
        ])

        # Gold trim (V-shape on chest)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_dark"],
                (cx - 10, cy - 6), (cx, cy + 8), 2)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_dark"],
                (cx + 10, cy - 6), (cx, cy + 8), 2)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_mid"],
                (cx - 9, cy - 5), (cx, cy + 7), 1)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_mid"],
                (cx + 9, cy - 5), (cx, cy + 7), 1)

        # Central gem (cyan)
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_darkest"], (cx, cy + 1), 4)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_dark"], (cx, cy + 1), 3)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_mid"], (cx, cy + 1),
                  max(1, int(3 * pulse)))
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_bright"], (cx, cy + 1),
                  max(1, int(2 * pulse)))
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_hot"], (cx, cy + 1), 1)

        # Gold outline
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["gold_mid"], (cx, cy + 1), 4, 1)

        # Belt
        _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["cape_darkest"], (cx - 13, cy + 10, 26, 4))
        _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["cape_dark"], (cx - 12, cy + 10, 24, 3))
        _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["gold_dark"], (cx - 3, cy + 10, 6, 4))
        _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["gold_mid"], (cx - 2, cy + 10, 4, 3))


    def _draw_pauldrons(surface, cx, cy, phase):
        """Shoulder pauldrons with spikes."""
        for side in (-1, 1):
            sx = cx + side * 14
            # Shadow
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["shadow_deep"], (sx + 2, cy + 2), 8)
            # Pauldron
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["armor_darkest"], (sx, cy), 7)
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["armor_dark"], (sx - side, cy - 1), 5)
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["armor_mid"], (sx - side, cy - 2), 3)

            # Gold trim
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["gold_dark"], (sx, cy), 7, 2)
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["gold_mid"], (sx, cy), 6, 1)

            # Small spike on top
            _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["armor_darkest"], [
                (sx - 2, cy - 6),
                (sx + 2, cy - 6),
                (sx + side * 2, cy - 12),
            ])
            _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["armor_dark"], [
                (sx - 1, cy - 6),
                (sx + 1, cy - 6),
                (sx + side * 1, cy - 11),
            ])
            # Gold tip
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["gold_mid"],
                      (sx + side * 2, cy - 12), 1)


    def _draw_idle_arms(surface, cx, cy, facing, phase):
        """Idle - one arm with sword down, one holding reins."""
        sway = math.sin(phase * 0.7) * 1

        # Sword arm (facing side)
        ss_x = cx + facing * 13
        ss_y = cy + 2
        se_x = ss_x + facing * 6
        se_y = cy + 10 + int(sway)
        sh_x = se_x + facing * 4
        sh_y = se_y + 12
        _NS_abaddon._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_abaddon._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)

        # Sword pointing down
        _NS_abaddon._draw_energy_sword(surface, sh_x, sh_y, facing, phase, angle=math.pi/2 - 0.2)

        # Reins arm (opposite side, holding reins forward)
        ra_x = cx + (-facing) * 13
        ra_y = cy + 2
        re_x = ra_x + (-facing) * 5
        re_y = cy + 8
        rh_x = re_x + (-facing) * 3
        rh_y = re_y + 4
        _NS_abaddon._draw_arm_segment(surface, ra_x, ra_y, re_x, re_y)
        _NS_abaddon._draw_arm_segment(surface, re_x, re_y, rh_x, rh_y)
        _NS_abaddon._draw_gloved_hand(surface, rh_x, rh_y)


    def _draw_melee_arms(surface, cx, cy, facing, phase, progress):
        """Melee sword swing."""
        # Reins arm stable
        ra_x = cx + (-facing) * 13
        ra_y = cy + 2
        re_x = ra_x + (-facing) * 5
        re_y = cy + 8
        rh_x = re_x + (-facing) * 3
        rh_y = re_y + 4
        _NS_abaddon._draw_arm_segment(surface, ra_x, ra_y, re_x, re_y)
        _NS_abaddon._draw_arm_segment(surface, re_x, re_y, rh_x, rh_y)
        _NS_abaddon._draw_gloved_hand(surface, rh_x, rh_y)

        # Sword arm - swing motion
        ss_x = cx + facing * 13
        ss_y = cy + 2

        if progress < 0.3:
            t = progress / 0.3
            arm_angle = -0.8 + (-1.0) * t
        elif progress < 0.6:
            t = (progress - 0.3) / 0.3
            arm_angle = -1.8 + 2.8 * t
        else:
            t = (progress - 0.6) / 0.4
            arm_angle = 1.0 - 1.5 * t

        se_x = ss_x + int(math.cos(arm_angle) * 12) * facing
        se_y = ss_y + int(math.sin(arm_angle) * 12)
        sh_x = se_x + int(math.cos(arm_angle) * 10) * facing
        sh_y = se_y + int(math.sin(arm_angle) * 10)

        _NS_abaddon._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_abaddon._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)

        # Sword with rotation
        sword_angle = arm_angle + (0.3 if facing > 0 else -0.3)
        _NS_abaddon._draw_energy_sword(surface, sh_x, sh_y, facing, phase, angle=sword_angle,
                          intense=(0.3 < progress < 0.7))


    def _draw_casting_arms(surface, cx, cy, facing, phase, progress):
        """Casting - sword extended forward."""
        # Reins arm
        ra_x = cx + (-facing) * 13
        ra_y = cy + 2
        re_x = ra_x + (-facing) * 5
        re_y = cy + 8
        rh_x = re_x + (-facing) * 3
        rh_y = re_y + 4
        _NS_abaddon._draw_arm_segment(surface, ra_x, ra_y, re_x, re_y)
        _NS_abaddon._draw_arm_segment(surface, re_x, re_y, rh_x, rh_y)
        _NS_abaddon._draw_gloved_hand(surface, rh_x, rh_y)

        # Sword arm - point forward
        ss_x = cx + facing * 13
        ss_y = cy + 2

        if progress < 0.3:
            t = progress / 0.3
            arm_angle = -0.5 - 0.5 * t
        elif progress < 0.5:
            t = (progress - 0.3) / 0.2
            arm_angle = -1.0 + 1.3 * t
        else:
            t = (progress - 0.5) / 0.5
            arm_angle = 0.3 - 0.5 * t

        se_x = ss_x + int(math.cos(arm_angle) * 12) * facing
        se_y = ss_y + int(math.sin(arm_angle) * 12)
        sh_x = se_x + int(math.cos(arm_angle) * 10) * facing
        sh_y = se_y + int(math.sin(arm_angle) * 10)

        _NS_abaddon._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_abaddon._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)

        _NS_abaddon._draw_energy_sword(surface, sh_x, sh_y, facing, phase, angle=arm_angle,
                          intense=(0.2 < progress < 0.5))


    def _draw_arm_segment(surface, x1, y1, x2, y2):
        """Armored arm segment."""
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["shadow_deep"],
                (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), 6)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["armor_darkest"], (x1, y1), (x2, y2), 5)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["armor_dark"], (x1, y1), (x2, y2), 4)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["armor_mid"], (x1, y1), (x2, y2), 2)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["armor_light"], (x1 - 1, y1), (x2 - 1, y2), 1)
        # Gold joint
        mx, my = (x1 + x2) // 2, (y1 + y2) // 2
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["gold_dark"], (mx, my), 3)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["gold_mid"], (mx, my), 2)


    def _draw_gloved_hand(surface, x, y):
        """Armored gauntlet hand."""
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["shadow_deep"], (x + 1, y + 1), 4)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["armor_darkest"], (x, y), 3)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["armor_dark"], (x, y - 1), 2)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["armor_mid"], (x - 1, y - 1), 1)


    def _draw_energy_sword(surface, hx, hy, facing, phase, angle=0, intense=False):
        """Abaddon's cyan energy sword."""
        length = 32
        tip_x = hx + int(math.cos(angle) * length) * facing
        tip_y = hy + int(math.sin(angle) * length)

        perp_angle = angle + math.pi / 2
        px = math.cos(perp_angle) * facing
        py = math.sin(perp_angle)

        # Blade base - crystalline shape
        blade_pts = [
            (hx + int(px * 3), hy + int(py * 3)),
            (hx - int(px * 2), hy - int(py * 2)),
            (tip_x - int(math.cos(angle) * 4) * facing - int(px * 1),
             tip_y - int(math.sin(angle) * 4) - int(py * 1)),
            (tip_x, tip_y),
            (tip_x - int(math.cos(angle) * 4) * facing + int(px * 3),
             tip_y - int(math.sin(angle) * 4) + int(py * 3)),
        ]
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in blade_pts])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["blade_darkest"], blade_pts)

        # Layers
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["blade_dark"], [
            (hx + int(px * 2), hy + int(py * 2)),
            (hx - int(px * 1), hy - int(py * 1)),
            (tip_x, tip_y),
            (hx + int(px * 2) + int(math.cos(angle) * length * 0.5) * facing,
             hy + int(py * 2) + int(math.sin(angle) * length * 0.5)),
        ])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["blade_mid"], [
            (hx + int(px * 1), hy + int(py * 1)),
            (hx, hy),
            (tip_x, tip_y),
        ])

        # Energy glow along blade
        for i in range(6):
            t = i / 6
            bx = int(hx + (tip_x - hx) * t)
            by = int(hy + (tip_y - hy) * t)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_mid"], 200), (bx, by), 3)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], 220), (bx, by), 2)
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_hot"], (bx, by), 1)

        # Bright edge
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["blade_shine"], (hx, hy), (tip_x, tip_y), 2)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["flame_white"], (hx, hy), (tip_x, tip_y), 1)

        # Extra intense glow when swinging
        if intense:
            # Aura around blade
            for i in range(4):
                t = i / 4
                bx = int(hx + (tip_x - hx) * t)
                by = int(hy + (tip_y - hy) * t)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_mid"], 100), (bx, by), 6)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], 150), (bx, by), 4)

        # Guard (crossguard - gold)
        guard_perp_x = int(px * 6)
        guard_perp_y = int(py * 6)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_darkest"],
                (hx + guard_perp_x, hy + guard_perp_y),
                (hx - guard_perp_x, hy - guard_perp_y), 4)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_dark"],
                (hx + guard_perp_x, hy + guard_perp_y),
                (hx - guard_perp_x, hy - guard_perp_y), 3)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_mid"],
                (hx + guard_perp_x, hy + guard_perp_y),
                (hx - guard_perp_x, hy - guard_perp_y), 1)

        # Pommel with cyan gem
        pommel_x = hx - int(math.cos(angle) * 5) * facing
        pommel_y = hy - int(math.sin(angle) * 5)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["gold_darkest"], (pommel_x, pommel_y), 3)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["gold_dark"], (pommel_x, pommel_y), 2)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_bright"], (pommel_x, pommel_y), 1)


    def _draw_hooded_head(surface, cx, cy, facing, phase):
        """Hood with glowing eyes inside."""
        # Neck
        _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["armor_darkest"], (cx - 3, cy + 8, 6, 5))
        _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["armor_dark"], (cx - 2, cy + 8, 4, 4))

        # Hood shape (large purple hood covering head)
        hood_pts = [
            (cx - 12, cy - 2),
            (cx - 11, cy - 10),
            (cx - 6, cy - 14),
            (cx, cy - 16),
            (cx + 6, cy - 14),
            (cx + 11, cy - 10),
            (cx + 12, cy - 2),
            (cx + 13, cy + 8),
            (cx + 7, cy + 12),
            (cx - 7, cy + 12),
            (cx - 13, cy + 8),
        ]
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["shadow_deep"], [(p[0] + 2, p[1] + 2) for p in hood_pts])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["cape_darkest"], hood_pts)

        hood_mid = [
            (cx - 10, cy - 1),
            (cx - 9, cy - 9),
            (cx - 5, cy - 13),
            (cx, cy - 15),
            (cx + 5, cy - 13),
            (cx + 9, cy - 9),
            (cx + 10, cy - 1),
            (cx + 11, cy + 6),
            (cx + 6, cy + 10),
            (cx - 6, cy + 10),
            (cx - 11, cy + 6),
        ]
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["cape_dark"], hood_mid)

        # Hood highlight edge
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["cape_mid"],
                (cx - 9, cy - 9), (cx, cy - 15), 1)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["cape_mid"],
                (cx + 9, cy - 9), (cx, cy - 15), 1)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["cape_light"],
                (cx - 5, cy - 13), (cx, cy - 15), 1)

        # Dark interior of hood
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["shadow_deep"], [
            (cx - 8, cy - 6),
            (cx - 7, cy - 10),
            (cx, cy - 12),
            (cx + 7, cy - 10),
            (cx + 8, cy - 6),
            (cx + 7, cy + 5),
            (cx, cy + 8),
            (cx - 7, cy + 5),
        ])

        # ===== HELM inside hood =====
        # Simple helm shape (visible under hood)
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["armor_darkest"], [
            (cx - 6, cy - 3),
            (cx - 5, cy - 8),
            (cx, cy - 10),
            (cx + 5, cy - 8),
            (cx + 6, cy - 3),
            (cx + 5, cy + 4),
            (cx, cy + 6),
            (cx - 5, cy + 4),
        ])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["armor_dark"], [
            (cx - 5, cy - 2),
            (cx - 4, cy - 7),
            (cx, cy - 9),
            (cx + 4, cy - 7),
            (cx + 5, cy - 2),
            (cx + 4, cy + 3),
            (cx, cy + 5),
            (cx - 4, cy + 3),
        ])

        # Gold helm brow
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_dark"],
                (cx - 5, cy - 5), (cx + 5, cy - 5), 2)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_mid"],
                (cx - 5, cy - 5), (cx + 5, cy - 5), 1)

        # ===== GLOWING EYES =====
        eye_pulse = math.sin(phase * 2) * 0.2 + 0.8
        eye_size = max(1, int(2 * eye_pulse))
        # Eye sockets (dark slits)
        _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["shadow_deep"], (cx - 5, cy - 2, 4, 2))
        _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["shadow_deep"], (cx + 1, cy - 2, 4, 2))
        # Bright cyan eye glow
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_dark"], (cx - 3, cy - 1), eye_size + 1)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_mid"], (cx - 3, cy - 1), eye_size)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_bright"], (cx - 3, cy - 1),
                  max(1, eye_size - 1))
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_hot"], (cx - 3, cy - 1), 1)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_dark"], (cx + 3, cy - 1), eye_size + 1)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_mid"], (cx + 3, cy - 1), eye_size)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_bright"], (cx + 3, cy - 1),
                  max(1, eye_size - 1))
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_hot"], (cx + 3, cy - 1), 1)

        # Eye emission glow
        _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["eye_bright"], int(80 * eye_pulse)),
                  (cx - 3, cy - 1), 5)
        _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["eye_bright"], int(80 * eye_pulse)),
                  (cx + 3, cy - 1), 5)

        # ===== HELM HORNS =====
        for side in (-1, 1):
            # Curved horn
            _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["armor_darkest"], [
                (cx + side * 5, cy - 8),
                (cx + side * 8, cy - 12),
                (cx + side * 12, cy - 20),
                (cx + side * 14, cy - 22),
                (cx + side * 11, cy - 19),
                (cx + side * 7, cy - 11),
            ])
            _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["armor_dark"], [
                (cx + side * 6, cy - 9),
                (cx + side * 8, cy - 12),
                (cx + side * 11, cy - 18),
                (cx + side * 13, cy - 21),
                (cx + side * 10, cy - 18),
                (cx + side * 7, cy - 11),
            ])
            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["armor_mid"],
                    (cx + side * 8, cy - 12),
                    (cx + side * 13, cy - 21), 1)
            # Small cyan glow on horn tip
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_mid"], 180),
                      (cx + side * 14, cy - 22), 2)
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_bright"],
                      (cx + side * 14, cy - 22), 1)

        # Cyan flame streamers coming up from head
        for i in (-4, 0, 4):
            _NS_abaddon._draw_flame_streamer(surface, cx + i, cy - 10, 6, phase + i * 0.3, 180)


    def _draw_body_flames(surface, cx, cy, phase):
        """Cyan flames rising from body."""
        for i in range(6):
            angle = phase * 0.4 + i * math.pi / 3
            radius = 22 + int(math.sin(phase * 0.7 + i) * 4)
            px = cx + int(math.cos(angle) * radius)
            py = cy - 5 + int(math.sin(angle) * radius * 0.5)
            alpha = int(140 + math.sin(phase + i * 0.7) * 60)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_dark"], alpha), (px, py), 2)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], alpha // 2), (px, py), 1)


    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_horse_flame_base(surface, cx, cy, phase, trail=False,
                              facing=1, intense=False):
        """Cyan flame base beneath the ghostly horse."""
        strength = 1.5 if intense else 1.0

        # Base flame mist
        mist = pygame.Surface((150, 45), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        for radius in range(42, 3, -4):
            alpha = int((42 - radius) * 2.0 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_abaddon.PALETTE["flame_darkest"], min(255, alpha)),
                    (75 - radius * 2, 22 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 75, cy - 12))

        # Rising cyan flames
        for i, offset in enumerate((-30, -18, -6, 6, 18, 30)):
            t = (phase * 0.5 + i * 0.17) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 25)
            alpha = max(0, min(255, int(220 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_abaddon._draw_cyan_flame(surface, sx, sy, max(1, 4 - int(t * 3)),
                            phase + i, alpha)

        # Orbiting flame orbs
        for i in range(5):
            angle = phase * 0.9 + i * math.pi * 2 / 5
            r = 28 + int(math.sin(phase + i * 1.3) * 4)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 7)
            _NS_abaddon._draw_cyan_flame(surface, sx, sy, 3, phase + i, 220)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 140 - i * 25)
                _NS_abaddon._draw_cyan_flame(surface, sx, sy, max(2, 4 - i), phase + i, alpha)


    def _draw_shadow(surface, x, y, lift=0):
        """Bayangan REAKTIF + cache: tekstur dibangun sekali; saat badan
        terangkat (lift > 0) mengecil, dasar tetap menapak tanah."""
        B = _NS_abaddon
        if B._AB_SHADOW is None:
            shadow = pygame.Surface((130, 24), pygame.SRCALPHA)
            for radius in range(12, 0, -1):
                alpha = max(0, (12 - radius) * 15)
                pygame.draw.ellipse(
                    shadow, (0, 0, 0, alpha),
                    (12 - radius, 12 - radius, 106 + radius * 2, radius * 2),
                )
            pygame.draw.ellipse(shadow, (*B.PALETTE["flame_darkest"], 60),
                                (10, 5, 108, 12))
            B._AB_SHADOW = shadow
        sh = B._AB_SHADOW
        s = 1.0 - min(0.30, abs(lift) * 0.03)
        if s < 0.999:
            sh = pygame.transform.smoothscale(sh, (int(130 * s), int(24 * s)))
        w, h = sh.get_size()
        surface.blit(sh, (x - w // 2, y + 12 - h))


    def _draw_dark_aura(surface, x, y, phase):
        """Dark purple/cyan background aura. ORIGINAL-MAX: gradien
        dibangun SEKALI; denyut via set_alpha (blit normal menghormati
        alpha permukaan) - piksel setara, ~0.5 ms -> ~0.05 ms."""
        B = _NS_abaddon
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        if B._AB_AURA1 is None:
            aura = pygame.Surface((220, 200), pygame.SRCALPHA)
            for radius in range(88, 5, -4):
                alpha = int((88 - radius) * 1.2)
                if alpha > 0:
                    B._aacircle(aura, (*B.PALETTE["cape_darkest"],
                                       min(255, alpha)), (110, 100), radius)
            B._AB_AURA1 = aura
            aura2 = pygame.Surface((160, 140), pygame.SRCALPHA)
            for radius in range(64, 5, -3):
                alpha = int((64 - radius) * 0.7)
                if alpha > 0:
                    B._aacircle(aura2, (*B.PALETTE["flame_darkest"],
                                        min(255, alpha)), (80, 70), radius)
            B._AB_AURA2 = aura2
        a1 = B._AB_AURA1
        a1.set_alpha(int(pulse * 255))
        surface.blit(a1, (x - 110, y - 100))
        a2 = B._AB_AURA2
        a2.set_alpha(int(pulse * 255))
        surface.blit(a2, (x - 80, y - 70))


    def _draw_ground_runes(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((160, 52), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_abaddon.PALETTE["cape_dark"], 140),
                            (5, 12, 150, 30), 3)
        pygame.draw.ellipse(ring, (*_NS_abaddon.PALETTE["flame_dark"], 170),
                            (25, 16, 110, 22), 2)

        for i in range(10):
            angle = phase * 0.2 + i * math.pi / 5
            x1 = 80 + int(math.cos(angle) * 38)
            y1 = 27 + int(math.sin(angle) * 8)
            x2 = 80 + int(math.cos(angle) * 68)
            y2 = 27 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_abaddon.PALETTE["flame_bright"], 160),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_abaddon.PALETTE["flame_hot"], int(80 * pulse)),
                                (15, 10, 130, 34), 1)

        surface.blit(ring, (x - 80, y - 26))


    def _draw_sword_swing_trail(surface, x, y, facing, progress):
        """Cyan trail during basic sword swing."""
        if progress < 0.3 or progress > 0.7:
            return
        t = (progress - 0.3) / 0.4
        center_x = x + facing * 5
        center_y = y
        radius = 45

        start_angle = -math.pi / 2 - 0.5
        end_angle = math.pi / 4
        current_angle = start_angle + (end_angle - start_angle) * t

        trail_length = 1.5
        segments = 14
        for i in range(segments):
            seg_t = i / segments
            angle = current_angle - trail_length * seg_t
            if angle < start_angle:
                continue

            ax = center_x + int(math.cos(angle) * radius) * facing
            ay = center_y + int(math.sin(angle) * radius)

            alpha_seg = int(220 * (1 - seg_t))
            size = int(4 * (1 - seg_t * 0.4))
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_dark"], alpha_seg),
                      (ax, ay), size + 2)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_mid"], alpha_seg),
                      (ax, ay), size + 1)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], alpha_seg),
                      (ax, ay), size)
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_hot"],
                      (ax, ay), max(1, size - 1))


    def _draw_sword_purple_trail(surface, x, y, facing, progress, phase):
        """Purple trail during Death Sever."""
        if progress < 0.15 or progress > 0.75:
            return

        t = (progress - 0.15) / 0.6
        center_x = x + facing * 5
        center_y = y
        radius = 50

        start_angle = -math.pi / 2 - 0.5
        end_angle = math.pi / 4
        current_angle = start_angle + (end_angle - start_angle) * t

        trail_length = 2.0
        segments = 16
        for i in range(segments):
            seg_t = i / segments
            angle = current_angle - trail_length * seg_t
            if angle < start_angle:
                continue

            ax = center_x + int(math.cos(angle) * radius) * facing
            ay = center_y + int(math.sin(angle) * radius)

            alpha_seg = int(240 * (1 - seg_t))
            size = int(5 * (1 - seg_t * 0.3))
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_darkest"], alpha_seg),
                      (ax, ay), size + 3)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_dark"], alpha_seg),
                      (ax, ay), size + 2)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_mid"], alpha_seg),
                      (ax, ay), size + 1)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_bright"], alpha_seg),
                      (ax, ay), size)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_hot"], alpha_seg),
                      (ax, ay), max(1, size - 1))


    # ===================================================================
    # SKILL W: APHOTIC SHIELD
    # ===================================================================
    def _draw_aphotic_shield(surface, boss, x, y, timer, phase):
        """Bubble shield around Abaddon."""
        progress = max(0.0, min(1.0, 1 - timer / 100))
        pulse = math.sin(phase * 2) * 0.2 + 0.8

        # Shield radius
        radius = int(45 + progress * 5)

        # Multi-layer shield sphere
        shield_layers = [
            (radius + 3, _NS_abaddon.PALETTE["flame_dark"], 100),
            (radius, _NS_abaddon.PALETTE["flame_mid"], 180),
            (radius - 3, _NS_abaddon.PALETTE["flame_light"], 150),
            (radius - 6, _NS_abaddon.PALETTE["flame_bright"], 100),
        ]

        for r, color, alpha in shield_layers:
            a = int(alpha * pulse)
            _NS_abaddon._aacircle(surface, (*color, a), (x, y - 8), r, 3)

        # Bright edge highlights
        _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], int(220 * pulse)),
                  (x, y - 8), radius, 2)
        _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_hot"], int(200 * pulse)),
                  (x, y - 8), radius, 1)

        # Rotating energy bands
        for band_i in range(3):
            band_phase = phase * 1.5 + band_i * math.pi / 3
            # Draw as arc segments (approximated with lines)
            for j in range(-6, 7):
                angle = band_phase + j * 0.15
                bx = x + int(math.cos(angle) * radius * math.cos(band_i * 0.4))
                by = y - 8 + int(math.sin(angle) * radius * math.cos(band_i * 0.4))
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_hot"], 200), (bx, by), 2)
                _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_white"], (bx, by), 1)

        # Small orbs orbiting the shield
        for i in range(6):
            angle = phase * 1.2 + i * math.pi / 3
            ox = x + int(math.cos(angle) * radius)
            oy = y - 8 + int(math.sin(angle) * radius * 0.6)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], 220), (ox, oy), 3)
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_hot"], (ox, oy), 2)
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_white"], (ox, oy), 1)

        # Bright sparks
        for i in range(8):
            angle = phase * 0.8 + i * math.pi / 4
            sx = x + int(math.cos(angle) * (radius + 5))
            sy = y - 8 + int(math.sin(angle) * (radius + 5))
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_shine"] if "flame_shine" in _NS_abaddon.PALETTE
                      else _NS_abaddon.PALETTE["flame_hot"], (sx, sy), 1)


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_abaddon.draw_abaddon(surface, boss, x, y)


# ====================================================================
# ENTRY POINT PUBLIK (dipanggil base_boss.Boss.draw)
# ====================================================================

def draw_gornak(surface, boss, x, y):
    """Entry point gornak."""
    return _NS_gornak.draw_gornak(surface, boss, x, y)

def draw_morgath(surface, boss, x, y):
    """Entry point morgath."""
    return _NS_morgath.draw_morgath(surface, boss, x, y)

def draw_drakar(surface, boss, x, y):
    """Entry point drakar."""
    return _NS_drakar.draw_drakar(surface, boss, x, y)

def draw_abaddon(surface, boss, x, y):
    """Entry point abaddon."""
    return _NS_abaddon.draw_abaddon(surface, boss, x, y)
