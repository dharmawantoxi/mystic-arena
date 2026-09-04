# ============================================================================
# heroes/nyzrak_fx.py
# ----------------------------------------------------------------------------
# NYZRAK — COMBAT / GAME-FEEL ENGINE  (screen-space live layer)
#
# Badan Nyzrak (rig pixel-art wyvern + rider) digambar lewat ``_NS_nyzrak``
# (bosses/level3.py).  Semua yang butuh gerak 60 fps sejati — trail tombak,
# partikel es/salju, proyektil shard, beam Arctic Burn, impact, guncangan
# layar, hit-stop — hidup di modul ini dan digambar LANGSUNG ke layar pada
# skala 1:1 tiap frame (tidak pernah masuk canvas sprite yang di-cache).
#
# Pembagian kerja (tidak ada efek yang digambar dua kali):
#
#   RENDERER (canvas, ter-cache)         MODUL INI (layar, hidup)
#   -----------------------------        --------------------------------
#   rig pixel-art + selout + rim         trail tombak dari histori posisi
#   bayangan kontak, tanah beku          partikel (salju, serpihan, debu)
#   telegraph tanah E/R                  PROYEKTIL shard (sistem nyata)
#   pose, napas, sayap                   BEAM Q + nova R + kurungan E
#   fallback FX canvas (tanpa modul)     IMPACT FX + flash + hit-stop + shake
#                                        overlay DEBUG_CHARACTER
#
# 100% PROSEDURAL. Tidak ada PNG / JPG / GIF / sprite-sheet / image.load.
#
# Isi modul
#   NYZRAK_PALETTE      palette khusus karakter (kontrak 9 kunci + ramp)
#   Particle            partikel penuh (acc, gravity, rotasi, fade, drag)
#   ParticleSystem      pool + burst + cap, reusable
#   SwingTrail          weapon trail prosedural dari histori posisi tombak
#   ImpactFX            flash + shockwave + debris + slash fragment
#   NyzrakProjectile    proyektil modular (spawn->travel->hit->destroy)
#   ProjectileSystem    manajer proyektil
#   SkillFX             lifecycle FX skill (cast->charge->release->fade)
#   NyzrakFXDirector    satu instance per unit, mengikat semua di atas
#   draw_debug_overlay  hitbox/hurtbox/state/frame/FPS/particle/skill/timer
#   API modul           tick / reset_all / notify_* / draw_*_layer
# ============================================================================

import math
import random

import pygame

try:                                 # bus game-feel bersama (semua karakter)
    from heroes import combat_feel as _feel
except Exception:                    # pragma: no cover - build minimal
    _feel = None


# ============================================================================
# 0.  KONFIGURASI
# ============================================================================

#: Debug visual untuk karakter NYZRAK: hitbox, hurtbox, jangkauan, state
#: animasi, frame, FPS, jumlah partikel, state skill, timer serangan.
DEBUG_CHARACTER = False

#: Master switch — kalau False, modul jadi no-op murah (badan tetap jalan).
NYZRAK_FX_ENABLED = True

#: Batas keras jumlah partikel hidup per director (anti-kebocoran FPS).
MAX_PARTICLES = 170

#: Batas keras proyektil visual per director.
MAX_PROJECTILES = 18

#: Panjang histori trail senjata (jumlah sample posisi tombak).
TRAIL_SAMPLES = 14

#: Batas dampak aktif per director & skill sekaligus di layar.
MAX_IMPACTS = 8
MAX_SKILLS = 4

#: Simulasi game berjalan pada langkah tetap 1/60 s.
FIXED_DT = 1.0 / 60.0

#: Kecepatan proyektil (px/detik, ruang layar).
SHARD_SPEED = 620.0
SPLINTER_SPEED = 540.0

#: Radius EFEK di ruang layar (visual; damage tetap milik gameplay).
WORLD_RADIUS = {"q": 190.0, "w": 70.0, "e": 44.0, "r": 180.0}

#: Durasi skill (frame @60fps) — HARUS sama dengan _NS_nyzrak.SKILL_DUR
#: dan AI base_boss (q/w/e/r).
SKILL_DUR = {"q": 50, "w": 50, "e": 70, "r": 90}


# ============================================================================
# 1.  PALETTE  —  wyvern rider: teal dingin + es biru + frost ungu
# ============================================================================

NYZRAK_PALETTE = {
    # ── kontrak palette karakter (9 kunci wajib) ────────────────────
    "outline":    (3,    5,  10),
    "shadow":     (8,   35,  75),
    "dark":       (18,  70,  90),
    "body":       (45, 135, 155),
    "mid":        (75, 155, 220),
    "light":      (150, 210, 245),
    "highlight":  (200, 235, 250),
    "weapon":     (105, 115, 135),
    "fx":         (230, 245, 255),

    # ── ramp es (bolt / trail / impact) ─────────────────────────────
    "fx_darkest": (8,   35,  75),
    "fx_dark":    (30,  85, 155),
    "fx_mid":     (75, 155, 220),
    "fx_light":   (150, 210, 245),
    "fx_bright":  (200, 235, 250),
    "fx_hot":     (230, 245, 255),
    "fx_white":   (250, 253, 255),

    # ── ramp frost ungu (skill Q) ───────────────────────────────────
    "frost_darkest": (25,  10,  60),
    "frost_dark":    (65,  30, 130),
    "frost_mid":     (125, 75, 200),
    "frost_light":   (175, 130, 240),
    "frost_bright":  (215, 180, 255),
    "frost_hot":     (240, 220, 255),

    # ── logam tombak (spark) ────────────────────────────────────────
    "steel_dark": (48,   55,  70),
    "steel_mid":  (105, 115, 135),
    "steel_edge": (225, 230, 245),
    "steel_hot":  (245, 250, 255),

    # ── bahan fisik: jubah, bulu, emas ──────────────────────────────
    "robe":       (55,   50, 105),
    "robe_dark":  (25,   20,  55),
    "fur":        (210, 220, 235),
    "brass":      (200, 165,  60),
    "brass_hot":  (240, 210, 110),

    # ── napas dingin / salju / asap ─────────────────────────────────
    "smoke":      (30,   42,  66),
    "mist":       (70,  110, 150),
    "snow":       (235, 245, 255),
}

P = NYZRAK_PALETTE

#: Kunci yang disalin dari palet renderer supaya warna karakter dan
#: warna efek tidak pernah melenceng.
_PALETTE_SYNC = {
    "outline": "shadow_deep",
    "shadow": "ice_darkest",
    "dark": "wy_dark",
    "body": "wy_mid",
    "mid": "ice_mid",
    "light": "ice_light",
    "highlight": "ice_bright",
    "weapon": "metal_mid",
    "fx": "ice_hot",
    "fx_darkest": "ice_darkest",
    "fx_dark": "ice_dark",
    "fx_mid": "ice_mid",
    "fx_light": "ice_light",
    "fx_bright": "ice_bright",
    "fx_hot": "ice_hot",
    "fx_white": "ice_pure",
    "frost_darkest": "frost_darkest",
    "frost_dark": "frost_dark",
    "frost_mid": "frost_mid",
    "frost_light": "frost_light",
    "frost_bright": "frost_bright",
    "frost_hot": "frost_hot",
    "steel_dark": "metal_dark",
    "steel_mid": "metal_mid",
    "steel_edge": "metal_shine",
    "robe": "robe_dark",
    "robe_dark": "robe_darkest",
}

_PALETTE_SYNCED = False


def _sync_palette():
    """Salin warna tema dari ``_NS_nyzrak.PALETTE`` sekali saja."""
    global _PALETTE_SYNCED
    if _PALETTE_SYNCED:
        return
    _PALETTE_SYNCED = True
    R = _renderer()
    if R is None:
        return
    pal = getattr(R, "PALETTE", None)
    if not isinstance(pal, dict):
        return
    for dst, src in _PALETTE_SYNC.items():
        col = pal.get(src)
        if col is not None:
            P[dst] = tuple(int(c) for c in col[:3])


# ============================================================================
# 2.  JEMBATAN KE RENDERER  (satu sumber geometri & pose)
# ============================================================================

_RENDERER = None          # None = belum dicari, False = tidak ada


def _renderer():
    """``_NS_nyzrak`` atau None. Diimpor malas: modul boss besar."""
    global _RENDERER
    if _RENDERER is None:
        try:
            from bosses.level3 import _NS_nyzrak as N
            _RENDERER = N
        except Exception:                      # pragma: no cover
            _RENDERER = False
    return _RENDERER or None


def _fallback_pose(boss):
    """(action, phase, ap) tanpa renderer: baca atribut yang sudah ada."""
    skill = getattr(boss, "active_skill", None)
    if skill in ("q", "w", "e", "r"):
        action = "cast_" + skill
        dur = float(SKILL_DUR.get(skill, 50))
        timer = float(getattr(boss, "active_skill_timer", 0) or 0)
        return action, float(getattr(boss, "pulse", 0.0) or 0.0), \
            min(1.0, max(0.0, 1.0 - timer / dur))
    if bool(getattr(boss, "_nyz_attack_active", False)):
        return "attack", float(getattr(boss, "pulse", 0.0) or 0.0), \
            min(1.0, max(0.0, float(getattr(boss, "_nyz_attack_progress", 0.0) or 0.0)))
    return "idle", float(getattr(boss, "pulse", 0.0) or 0.0), 0.0


def pose_of(boss):
    """(action, phase, ap) — pose yang SEDANG digambar badan."""
    R = _renderer()
    if R is None:
        return _fallback_pose(boss)
    try:
        return R._resolve_pose(boss)
    except Exception:                          # pragma: no cover
        return _fallback_pose(boss)


def anim_state(boss):
    """Dict lengkap dari controller animasi (state/prioritas/sub-fase)."""
    R = _renderer()
    moving = bool(getattr(boss, "_nyz_move_mag", 0.3) > 0.3)
    run = float(getattr(boss, "_nyz_move_mag", 0.0)) > 2.4
    if R is not None:
        try:
            return R._NyzAnimController.resolve(boss, moving, run)
        except Exception:                      # pragma: no cover
            pass
    action, phase, ap = _fallback_pose(boss)
    return {"state": action.upper(), "action": action, "phase": phase,
            "ap": ap, "skill": getattr(boss, "active_skill", None),
            "skill_t01": ap if action.startswith("cast") else 0.0,
            "stage": "-", "death_t": 0.0}


def render_scale(boss):
    """Faktor normalisasi pipeline hero. Jalur boss = 1.0."""
    v = getattr(boss, "_render_scale", None)
    if v is None:
        return 1.0
    try:
        v = float(v)
    except (TypeError, ValueError):
        return 1.0
    if v <= 0.02:
        return 1.0
    return max(0.05, min(1.6, v))


def body_scale(boss):
    """Skala rig -> piksel layar (rig sudah 2x dari renderer)."""
    return render_scale(boss)


def ground_dy(boss):
    """Jarak jangkar -> garis tanah, piksel layar."""
    R = _renderer()
    dy = getattr(R, "GROUND_DY", 55) if R is not None else 55
    return int(round(float(dy) * render_scale(boss)))


def spear_points(boss, x, y):
    """(grip, tip, info) tombak dalam piksel layar — sumber bentuk trail."""
    R = _renderer()
    if R is not None:
        try:
            st = R._spear_state(boss, x, y)
            return st["grip"], st["tip"], st
        except Exception:                      # pragma: no cover
            pass
    action, phase, ap = pose_of(boss)
    facing = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
    grip = pygame.Vector2(x + 14 * facing, y - 44)
    return grip, grip + pygame.Vector2(10 * facing, -28), {
        "grip": grip, "active": False, "angle": -1.0, "action": action,
        "ap": ap, "facing": facing}


# ============================================================================
# 3.  ANGGARAN EFEK  (menghormati preset kualitas mobile)
# ============================================================================

def _quality():
    try:
        from mobile.perf import Quality
        return Quality
    except Exception:                          # pragma: no cover
        return None


def particle_budget():
    """Faktor jumlah partikel (0.0 = partikel dimatikan total)."""
    Q = _quality()
    if Q is None:
        return 1.0
    if not getattr(Q, "particles", True):
        return 0.0
    return float(getattr(Q, "particle_ratio", 1.0))


def glow_allowed():
    Q = _quality()
    return True if Q is None else bool(getattr(Q, "glow", True))


def shake_allowed():
    if _feel is not None:
        try:
            return bool(_feel.shake_allowed())
        except Exception:
            pass
    return True


# ============================================================================
# 4.  CACHE SURFACE PROSEDURAL  (dibangun sekali, dipakai semua unit)
# ============================================================================

_CACHE = {}
_CACHE_MAX = 128


def _cache_put(key, surf):
    if len(_CACHE) >= _CACHE_MAX:
        # buang ~ seperempat cache tua agar tidak pernah tumbuh tanpa batas
        for k in list(_CACHE.keys())[:_CACHE_MAX // 4]:
            _CACHE.pop(k, None)
    _CACHE[key] = surf
    return surf


def clear_cache():
    _CACHE.clear()
    _FADE_CACHE.clear()
    _FADE_ORDER.clear()


def cache_size():
    return len(_CACHE)


def glow_surface(radius, color, power=1.0):
    """Halo radial lembut PREMULTIPLIED (cached) — muzzle/impact/nova.

    ``BLEND_RGB_ADD`` MENGABAIKAN kanal alpha, jadi lingkaran ber-RGB
    penuh + alpha menurun berubah menjadi CAKRAM warna solid saat di-blit
    additive — penyebab Nyzrak tertelan bola putih saat R Nova di-cast.
    Intensitas dikalikan ke RGB **dan** disalin ke alpha supaya surface
    yang sama benar untuk blit normal maupun additive.
    """
    key = ("glow", int(radius), tuple(color), round(power, 1))
    s = _CACHE.get(key)
    if s is not None:
        return s
    r = max(1, int(radius))
    size = r * 2 + 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cr, cg, cb = color[:3]
    steps = max(2, int(r / 1.5))
    for i in range(steps, 0, -1):
        rr = int(r * i / steps)
        k = 0.47 * power * (1 - i / (steps + 1)) ** 1.5 + 0.03
        if k <= 0.008:
            continue
        pygame.draw.circle(surf,
                           (int(cr * k), int(cg * k), int(cb * k),
                            min(255, int(255 * k))), (r + 1, r + 1), rr)
    return _cache_put(key, surf)


def spark_surface(length, color):
    """Kilat garis (cached) — dipakai impact star."""
    key = ("spark", int(length), tuple(color))
    s = _CACHE.get(key)
    if s is not None:
        return s
    ln = max(2, int(length))
    surf = pygame.Surface((ln * 2 + 2, 3), pygame.SRCALPHA)
    c = color[:3]
    pygame.draw.line(surf, (*c, 235), (1, 1), (ln * 2 - 1, 1), 1)
    pygame.draw.rect(surf, (*P["fx_white"], 255), (ln, 0, 2, 3))
    return _cache_put(key, surf)


def ring_surface(radius, thickness, color, segments=0):
    """Cincin chunky (cached). segments>0 -> cincin dash zig-zag es."""
    key = ("ring", int(radius), int(thickness), tuple(color), int(segments))
    s = _CACHE.get(key)
    if s is not None:
        return s
    r = max(1, int(radius))
    th = max(1, int(thickness))
    size = (r + th + 2) * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = color[:3]
    if segments <= 0:
        pygame.draw.circle(surf, (*c, 255), (size // 2, size // 2), r, th)
    else:
        for i in range(segments):
            a0 = i * math.pi * 2 / segments
            a1 = a0 + math.pi * 2 / segments * 0.55
            p0 = (size // 2 + math.cos(a0) * r, size // 2 + math.sin(a0) * r)
            p1 = (size // 2 + math.cos(a1) * r, size // 2 + math.sin(a1) * r)
            pygame.draw.line(surf, (*c, 255), p0, p1, th)
    return _cache_put(key, surf)


def shard_surface(size, color):
    """Serpihan es kristal (cached) — quad panah."""
    key = ("shard", int(size), tuple(color))
    s = _CACHE.get(key)
    if s is not None:
        return s
    n = max(2, int(size))
    surf = pygame.Surface((n * 3 + 2, n * 2 + 2), pygame.SRCALPHA)
    c = color[:3]
    cx, cy = surf.get_width() // 2, surf.get_height() // 2
    pts = [(cx + n, cy), (cx - n // 2, cy - n // 3),
           (cx - n, cy), (cx - n // 2, cy + n // 3)]
    pygame.draw.polygon(surf, (*c, 255), pts)
    pygame.draw.polygon(surf, (*P["fx_white"], 200),
                        [(cx + n, cy), (cx - n // 3, cy - n // 4), (cx, cy)])
    return _cache_put(key, surf)


def snowflake_surface(size, color):
    """Bintang salju 6 lengan 1px (cached)."""
    key = ("snow", int(size), tuple(color))
    s = _CACHE.get(key)
    if s is not None:
        return s
    n = max(2, int(size))
    size_sq = n * 2 + 3
    surf = pygame.Surface((size_sq, size_sq), pygame.SRCALPHA)
    c = color[:3]
    c0 = size_sq // 2
    for i in range(6):
        a = i * math.pi / 3
        ex = c0 + math.cos(a) * n
        ey = c0 + math.sin(a) * n
        pygame.draw.line(surf, (*c, 255), (c0, c0), (ex, ey), 1)
        mx = c0 + math.cos(a) * (n - 1)
        my = c0 + math.sin(a) * (n - 1)
        t = a + math.pi / 2
        pygame.draw.line(surf, (*c, 200), (mx, my),
                         (mx + math.cos(t), my + math.sin(t)), 1)
    pygame.draw.rect(surf, (*P["fx_white"], 255), (c0, c0, 1, 1))
    return _cache_put(key, surf)


_FADE_CACHE = {}
_FADE_ORDER = []


def _fade_copy(surf, alpha):
    """Salinan surface yang RGB-nya ikut diredam (untuk blit additive)."""
    a = max(1, min(255, int(alpha))) // 8 * 8 or 8
    key = (id(surf), surf.get_size(), a)
    hit = _FADE_CACHE.get(key)
    if hit is not None:
        return hit[1]
    cp = surf.copy()
    cp.fill((a, a, a, a), special_flags=pygame.BLEND_RGBA_MULT)
    _FADE_CACHE[key] = (surf, cp)          # tahan sumber: id() tetap unik
    _FADE_ORDER.append(key)
    while len(_FADE_ORDER) > 256:
        _FADE_CACHE.pop(_FADE_ORDER.pop(0), None)
    return cp


def _blit_faded(surface, surf, cx, cy, alpha=255.0, additive=False):
    """Blit dengan alpha dinamis tanpa salinan per partikel.

    ``BLEND_RGB_ADD`` MENGABAIKAN set_alpha: kalau jalur aditif blit
    langsung, glow yang "memudar" tetap ditambahkan penuh dan menumpuk
    jadi bercak putih di atas sprite. Jalur aditif karena itu memakai
    salinan ter-cache yang RGB-nya sudah diredam.
    Non-additif memakai set_alpha pada surface cache lalu dipulihkan.
    """
    alpha = max(0.0, min(255.0, alpha))
    if alpha <= 1.0:
        return
    pos = (int(cx - surf.get_width() / 2),
           int(cy - surf.get_height() / 2))
    if additive:
        if alpha < 250.0:
            surf = _fade_copy(surf, alpha)
            pos = (int(cx - surf.get_width() / 2),
                   int(cy - surf.get_height() / 2))
        surface.blit(surf, pos, special_flags=pygame.BLEND_RGB_ADD)
        return
    if alpha >= 254.0:
        surface.blit(surf, pos)
        return
    surf.set_alpha(int(alpha))
    surface.blit(surf, pos)
    surf.set_alpha(255)


# ============================================================================
# 5.  PARTICLE SYSTEM  (pool + burst + cap)
# ============================================================================

class Particle:
    """Partikel penuh: acc, gravity, rotasi, drag, fade, shrink.

    kind: "chunk" (piksel es), "spark" (garis cepat), "shard" (kristal
    quad), "smoke" (puff alpha), "snow" (keping salju), "glint" (kilau +).
    """
    __slots__ = ("x", "y", "vx", "vy", "ax", "ay", "life", "max_life",
                 "size", "rot", "rot_speed", "gravity", "drag", "color",
                 "kind", "layer", "shrink", "fade_pow", "alive")

    def __init__(self):
        self.reset()

    def reset(self):
        self.x = self.y = 0.0
        self.vx = self.vy = 0.0
        self.ax = self.ay = 0.0
        self.life = self.max_life = 1.0
        self.size = 2
        self.rot = 0.0
        self.rot_speed = 0.0
        self.gravity = 0.0
        self.drag = 0.0
        self.color = P["fx_mid"]
        self.kind = "chunk"
        self.layer = "front"        # "front" | "back"
        self.shrink = True
        self.fade_pow = 1.0
        self.alive = False

    # -- properti sesuai kontrak ------------------------------------------
    @property
    def position(self):
        return (self.x, self.y)

    @property
    def velocity(self):
        return (self.vx, self.vy)

    @property
    def acceleration(self):
        return (self.ax, self.ay)

    @property
    def alpha(self):
        return int(255 * max(0.0, self.life / self.max_life) ** self.fade_pow)

    def spawn(self, x, y, vx, vy, life, size, color, **kw):
        self.reset()
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.life = self.max_life = max(0.016, float(life))
        self.size = max(1, int(size))
        self.color = color
        self.kind = kw.get("kind", "chunk")
        self.layer = kw.get("layer", "front")
        self.ax = float(kw.get("ax", 0.0))
        self.ay = float(kw.get("ay", 0.0))
        self.gravity = float(kw.get("gravity", 0.0))
        self.drag = float(kw.get("drag", 0.0))
        self.rot = float(kw.get("rot", random.uniform(0, math.tau)))
        self.rot_speed = float(kw.get("rot_speed", 0.0))
        self.shrink = bool(kw.get("shrink", True))
        self.fade_pow = float(kw.get("fade_pow", 1.0))
        self.alive = True

    def update(self, dt):
        self.life -= dt
        if self.life <= 0.0:
            self.alive = False
            return
        if self.drag > 0.0:
            k = max(0.0, 1.0 - self.drag * dt)
            self.vx *= k
            self.vy *= k
        self.vx += (self.ax + 0.0) * dt
        self.vy += (self.ay + self.gravity) * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.rot_speed:
            self.rot += self.rot_speed * dt

    def draw(self, surface):
        a = self.alpha
        if a <= 1:
            return
        x, y = int(self.x), int(self.y)
        k = self.life / self.max_life
        size = max(1, int(self.size * (k if self.shrink else 1.0)))
        c = self.color
        if self.kind == "chunk":
            # chunky pixel: rect langsung (tanpa alokasi surface), fade
            # lewat penyusutan ukuran — gaya pixel-art + murah.
            s2 = max(1, size // 2)
            pygame.draw.rect(surface, c,
                             (x - s2, y - s2, size, size))
            if size >= 2:
                pygame.draw.rect(surface, P["fx_white"],
                                 (x - s2, y - s2, max(1, size // 2),
                                  max(1, size // 2)))
        elif self.kind == "spark":
            ln = size * 3
            dx = math.cos(self.rot) * ln
            dy = math.sin(self.rot) * ln
            w = 1 if size < 3 else 2
            pygame.draw.line(surface, (*c, a), (x - dx, y - dy),
                             (x + dx, y + dy), w)
            pygame.draw.rect(surface, (*P["fx_white"], a), (x, y, 1, 1))
        elif self.kind == "shard":
            spr = shard_surface(size + 2, c)
            if self.rot:
                spr = pygame.transform.rotate(spr, -math.degrees(self.rot))
            _blit_faded(surface, spr, x, y, a)
        elif self.kind == "smoke":
            r = max(2, int(size * (1.6 - k * 0.6)))
            surf = glow_surface(r, c, 0.55)
            _blit_faded(surface, surf, x, y, a * 0.8)
        elif self.kind == "snow":
            spr = snowflake_surface(size + 2, c)
            if self.rot:
                spr = pygame.transform.rotate(spr, -math.degrees(self.rot))
            _blit_faded(surface, spr, x, y, a)
        elif self.kind == "glint":
            ln = size * 4 * k
            for ang in (self.rot, self.rot + math.pi / 2):
                dx = math.cos(ang) * ln
                dy = math.sin(ang) * ln
                pygame.draw.line(surface, (*c, a), (x - dx, y - dy),
                                 (x + dx, y + dy), 1)
            pygame.draw.rect(surface, (*P["fx_white"], a), (x, y, 1, 1))


class ParticleSystem:
    """Pool partikel dengan batas keras + burst terarah + stream."""

    def __init__(self, cap=MAX_PARTICLES):
        self.cap = int(cap)
        self._pool = [Particle() for _ in range(24)]
        self._live = []

    def _acquire(self):
        if self._pool:
            return self._pool.pop()
        if len(self._live) < self.cap:
            return Particle()
        # penuh: daur ulang partikel tertua
        return self._live.pop(0)

    def count(self):
        return len(self._live)

    def alive(self):
        return len(self._live) > 0

    def clear(self):
        for p in self._live:
            p.alive = False
            self._pool.append(p)
        self._live.clear()

    def spawn(self, x, y, vx, vy, life, size, color, **kw):
        budget = particle_budget()
        if budget <= 0.0:
            return None
        p = self._acquire()
        p.spawn(x, y, vx, vy, life, size, color, **kw)
        self._live.append(p)
        return p

    def burst(self, x, y, count, speed=(70.0, 240.0), life=(0.2, 0.55),
              size=(1, 3), color=None, kind="chunk", layer="front",
              spread=math.tau, ang0=0.0, gravity=0.0, drag=0.0,
              rot_speed=(0, 0)):
        """Ledakan partikel arah acak dalam kerucut [ang0, ang0+spread]."""
        budget = particle_budget()
        if budget <= 0.0:
            return 0
        n = int(count * budget)
        col = color if color is not None else P["fx_light"]
        for _ in range(n):
            a = ang0 + random.uniform(0.0, spread)
            sp = random.uniform(*speed)
            self.spawn(x, y, math.cos(a) * sp, math.sin(a) * sp,
                       random.uniform(*life), random.randint(*size),
                       random.choice((col, P["fx_bright"], P["fx_hot"])),
                       kind=kind, layer=layer, gravity=gravity, drag=drag,
                       rot_speed=random.uniform(*rot_speed))
        return n

    def stream(self, x, y, tx, ty, count, life=(0.3, 0.6), size=(1, 2),
               color=None, kind="chunk"):
        """Partikel mengalir dari (x,y) menuju (tx,ty) — gather charge."""
        budget = particle_budget()
        if budget <= 0.0:
            return 0
        n = int(count * budget)
        col = color if color is not None else P["fx_bright"]
        for _ in range(n):
            t = random.uniform(0.25, 1.0)
            sx = x + (tx - x) * t
            sy = y + (ty - y) * t
            lt = random.uniform(*life)
            self.spawn(sx, sy, (x - sx) / lt, (y - sy) / lt, lt,
                       random.randint(*size),
                       random.choice((col, P["fx_hot"])), kind=kind,
                       layer="back")
        return n

    def update(self, dt):
        dead = []
        for p in self._live:
            p.update(dt)
            if not p.alive:
                dead.append(p)
        if dead:
            for p in dead:
                self._live.remove(p)
                self._pool.append(p)

    def draw(self, surface, layer="front"):
        for p in self._live:
            if p.layer == layer:
                p.draw(surface)


# ============================================================================
# 6.  SWING TRAIL  —  pita sapuan dari histori posisi tombak
# ============================================================================

class SwingTrail:
    """Trail tombak prosedural: menyimpan posisi (grip, tip) lama.

    Ribbon digambar dari pasangan segmen lama->baru dengan lebar proporsional
    kecepatan sudut, memudar sesuai umur — mengikuti ARAH serangan.
    """

    def __init__(self, samples=TRAIL_SAMPLES):
        self.max_samples = samples
        self._hist = []            # [(grip Vector2, tip Vector2, age)]
        self._fade = 0.0

    def reset(self):
        self._hist.clear()
        self._fade = 0.0

    def push(self, grip, tip):
        self._hist.append((pygame.Vector2(grip), pygame.Vector2(tip), 0.0))
        while len(self._hist) > self.max_samples:
            self._hist.pop(0)

    def update(self, dt):
        for i in range(len(self._hist) - 1, -1, -1):
            g, t, age = self._hist[i]
            age += dt
            if age > 0.22:
                self._hist.pop(i)
            else:
                self._hist[i] = (g, t, age)

    def active(self):
        return len(self._hist) >= 3

    def draw(self, surface):
        n = len(self._hist)
        if n < 3:
            return
        # bbox lokal -> temp kecil (bukan surface selebar layar)
        xs = [p.x for g, p, _ in self._hist]
        ys = [p.y for g, p, _ in self._hist]
        pad = 10
        bx = max(0, int(min(xs)) - pad)
        by = max(0, int(min(ys)) - pad)
        bw = int(max(xs)) - bx + pad * 2
        bh = int(max(ys)) - by + pad * 2
        if bw <= 2 or bh <= 2:
            return
        left, right = [], []
        for i in range(n):
            g, t, age = self._hist[i]
            if i < n - 1:
                g2, t2, _ = self._hist[i + 1]
            else:
                g2, t2, _ = self._hist[i - 1]
                g2, t2 = g - (g2 - g), t - (t2 - t)
            dv = t - g
            ln = dv.length()
            if ln < 1.0:
                continue
            nx, ny = -dv.y / ln, dv.x / ln
            k = 1.0 - age / 0.22            # 1 baru -> 0 tua
            w = 1.2 + 3.2 * k
            left.append((t.x + nx * w - bx, t.y + ny * w - by))
            right.append((t.x - nx * w - bx, t.y - ny * w - by))
        if len(left) < 3:
            return
        tmp = pygame.Surface((bw, bh), pygame.SRCALPHA)
        poly = left + right[::-1]
        pygame.draw.polygon(tmp, (*P["fx_dark"], 70), poly)
        pygame.draw.polygon(tmp, (*P["fx_light"], 120), poly)
        # inti terang hanya pada 60% sampel TERBARU (arah ayunan)
        hot = left[: max(3, int(len(left) * 0.6))] + \
            right[: max(3, int(len(right) * 0.6))][::-1]
        if len(hot) >= 3:
            pygame.draw.polygon(tmp, (*P["fx_hot"], 150), hot)
        surface.blit(tmp, (bx, by), special_flags=pygame.BLEND_RGB_ADD)
        # percikan piksel di ujung blade terbaru
        g, t, _ = self._hist[-1]
        pygame.draw.rect(surface, (*P["fx_white"], 220),
                         (int(t.x), int(t.y), 2, 2))


# ============================================================================
# 7.  IMPACT FX  —  flash + shockwave + debris + slash fragments
# ============================================================================

class ImpactFX:
    """Paket umpan balik benturan (visual only; damage di gameplay).

    kind: "spear" (tetesukan es), "frost" (ledakan ungu), "nova" (shockwave
    besar R), "crit" memperbesar + memutihkan.
    """

    LIFE = 0.34

    def __init__(self, x, y, angle=0.0, power=1.0, crit=False,
                 kind="spear", particles=None):
        self.x = float(x)
        self.y = float(y)
        self.angle = float(angle)
        self.power = max(0.4, min(2.4, float(power)))
        self.crit = bool(crit)
        self.kind = kind
        self.age = 0.0
        self.life = self.LIFE * (1.25 if crit else 1.0)
        self.alive = True
        self._seed = random.uniform(0, math.tau)
        if particles is not None:
            self._spawn_debris(particles)

    def _spawn_debris(self, ps):
        n = int(10 + 12 * self.power)
        base = self.angle
        if self.kind == "frost":
            ps.burst(self.x, self.y, n, (90, 320), (0.18, 0.5), (1, 3),
                     P["frost_light"], "shard", "front",
                     spread=math.tau, gravity=340.0, drag=1.2,
                     rot_speed=(-9, 9))
            ps.burst(self.x, self.y, n // 2, (40, 160), (0.25, 0.6), (2, 4),
                     P["frost_bright"], "snow", "front", spread=math.tau,
                     rot_speed=(-5, 5))
        elif self.kind == "nova":
            ps.burst(self.x, self.y, n * 2, (140, 460), (0.25, 0.7), (1, 3),
                     P["fx_bright"], "shard", "front", spread=math.tau,
                     gravity=180.0, drag=1.4, rot_speed=(-7, 7))
            ps.burst(self.x, self.y, n, (30, 120), (0.4, 0.9), (3, 6),
                     P["mist"], "smoke", "back", spread=math.tau)
        else:  # spear
            ps.burst(self.x, self.y, n, (80, 300), (0.16, 0.42), (1, 2),
                     P["fx_light"], "chunk", "front",
                     spread=2.4, ang0=base - 1.2, gravity=380.0, drag=0.9)
            ps.burst(self.x, self.y, n // 2, (120, 420), (0.1, 0.25),
                     (1, 2), P["fx_white"], "spark", "front",
                     spread=2.0, ang0=base - 1.0)
            ps.burst(self.x, self.y, 4, (30, 90), (0.3, 0.6), (2, 4),
                     P["mist"], "smoke", "back", spread=math.tau)

    def update(self, dt):
        self.age += dt
        if self.age >= self.life:
            self.alive = False

    def _ramp(self):
        return max(0.0, 1.0 - self.age / self.life)

    def draw(self, surface):
        k = self._ramp()
        if k <= 0.0:
            return
        pw = self.power
        x, y = int(self.x), int(self.y)
        # 1. bintang flash 4-8 arah (polygon, bukan lingkaran) — temp
        #    seukuran bbox bintang, bukan selebar layar
        spikes = 8 if (self.crit or self.kind == "nova") else 4
        rot = self.angle
        pts = []
        R = (14 + 26 * pw) * (0.5 + 0.5 * k)
        r = R * 0.28
        for i in range(spikes * 2):
            a = rot + i * math.pi / spikes
            rad = R if i % 2 == 0 else r
            pts.append((x + math.cos(a) * rad, y + math.sin(a) * rad))
        xs = [p[0] for p in pts] + [x]
        ys = [p[1] for p in pts] + [y]
        bx = int(min(xs)) - 4
        by = int(min(ys)) - 4
        bw = int(max(xs)) - bx + 4
        bh = int(max(ys)) - by + 4
        if bw <= 2 or bh <= 2:
            return
        flash_col = P["fx_white"] if self.crit else P["fx_hot"]
        tmp = pygame.Surface((bw, bh), pygame.SRCALPHA)
        pts_l = [(px - bx, py - by) for px, py in pts]
        pygame.draw.polygon(tmp, (*flash_col, int(235 * k)), pts_l)
        pygame.draw.polygon(tmp, (*P["fx_bright"], int(160 * k)),
                            [(px * 0.55 + (x - bx) * 0.45,
                              py * 0.55 + (y - by) * 0.45)
                             for px, py in pts_l])
        surface.blit(tmp, (bx, by), special_flags=pygame.BLEND_RGB_ADD)
        # 2. shockwave cincin chunky (dash utk frost/nova)
        rr = (12 + 44 * pw) * (1.0 - k * 0.72)
        if rr > 2:
            segs = 0 if self.kind == "spear" else 10
            col = P["frost_bright"] if self.kind == "frost" else P["fx_bright"]
            ring = ring_surface(int(rr), 2, col, segs)
            _blit_faded(surface, ring, x, y, 220 * k, additive=True)
        # 3. slash fragments (dua sabit mengarah angle)
        if self.kind == "spear":
            for sign in (-1, 1):
                a = self.angle + sign * (0.9 - 0.4 * k)
                ln = (16 + 22 * pw) * k
                x2 = x + math.cos(a) * ln
                y2 = y + math.sin(a) * ln
                pygame.draw.line(surface, (*P["fx_light"], int(200 * k)),
                                 (x, y), (x2, y2), 2)
                pygame.draw.line(surface, (*P["fx_white"], int(160 * k)),
                                 (x, y), (x2, y2), 1)
        # 4. kilau inti
        if k > 0.35:
            gl = glow_surface(int(8 + 10 * pw), P["fx_bright"], 0.9)
            _blit_faded(surface, gl, x, y, 200 * k, additive=True)


# ============================================================================
# 8.  PROJECTILE SYSTEM  —  modular, lifecycle penuh
# ============================================================================

class NyzrakProjectile:
    """Proyektil es modular.

    Lifecycle: SPAWN -> TRAVEL -> TRAIL -> HIT -> IMPACT FX -> DESTROY.
    kind "shard": lanset es berputar (serangan dasar);
         kind "splinter": serpihan cepat (Splinter Blast W).
    """

    def __init__(self, x, y, tx, ty, speed=SHARD_SPEED, damage=0.0,
                 kind="shard", radius=7.0, lifetime=1.6, target=None,
                 homing=0.0, crit=False, particles=None):
        # -- kontrak field -------------------------------------------------
        self.position = pygame.Vector2(float(x), float(y))
        self.velocity = pygame.Vector2(0.0, 0.0)
        self.speed = float(speed)
        self.damage = float(damage)
        self.lifetime = float(lifetime)
        self.target = target
        self.radius = float(radius)
        self.rotation = 0.0
        self.trail = []                  # [(x, y, age)]
        self.particles = particles
        self.active = True
        # -- internal ------------------------------------------------------
        self._tx = float(tx)
        self._ty = float(ty)
        self.kind = kind
        self.homing = float(homing)
        self.crit = bool(crit)
        self.age = 0.0
        self.spin = random.uniform(-8.0, 8.0)
        d = pygame.Vector2(self._tx - self.position.x,
                           self._ty - self.position.y)
        if d.length_squared() < 1.0:
            d = pygame.Vector2(1.0, 0.0)
        self.angle = math.atan2(d.y, d.x)
        self.velocity.from_polar((self.speed, math.degrees(self.angle)))
        self._dist = d.length()
        self._traveled = 0.0
        self._emit = 0.0

    # ------------------------------------------------------------------
    def kill(self, impact=True):
        """DESTROY (+ partikel impact bila impact)."""
        if not self.active:
            return
        self.active = False
        if impact and self.particles is not None:
            self.particles.burst(
                self.position.x, self.position.y, 8, (60, 260),
                (0.15, 0.4), (1, 2), P["fx_light"], "chunk", "front",
                spread=math.tau, gravity=300.0, drag=1.0)
            self.particles.burst(
                self.position.x, self.position.y, 3, (30, 120),
                (0.3, 0.6), (2, 4), P["mist"], "smoke", "back",
                spread=math.tau)

    # ------------------------------------------------------------------
    def update(self, dt, units=None):
        if not self.active:
            return
        self.age += dt
        if self.age >= self.lifetime:
            self.kill(impact=True)
            return
        # target tracking (homing 0..1: seberapa agresif belok)
        if (self.homing > 0.0 and self.target is not None
                and getattr(self.target, "alive", False)):
            tv = pygame.Vector2(
                float(getattr(self.target, "x", self._tx)) - self.position.x,
                float(getattr(self.target, "y", self._ty)) - self.position.y)
            if tv.length_squared() > 1.0:
                want = math.atan2(tv.y, tv.x)
                da = (want - self.angle + math.pi) % math.tau - math.pi
                self.angle += da * min(1.0, self.homing * dt * 8.0)
        self.velocity.from_polar((self.speed, math.degrees(self.angle)))
        step = self.velocity * dt
        self.position += step
        self._traveled += step.length()
        self.rotation += dt * self.spin
        # TRAIL sampling
        self.trail.append((self.position.x, self.position.y, 0.0))
        if len(self.trail) > 10:
            self.trail.pop(0)
        for i, (tx, ty, ta) in enumerate(self.trail):
            self.trail[i] = (tx, ty, ta + dt)
        # partikel ekor
        self._emit -= dt
        if self._emit <= 0.0 and self.particles is not None:
            self._emit = 0.03
            self.particles.spawn(
                self.position.x, self.position.y,
                -self.velocity.x * 0.12 + random.uniform(-25, 25),
                -self.velocity.y * 0.12 + random.uniform(-25, 25),
                random.uniform(0.18, 0.4), random.randint(1, 2),
                P["fx_bright"], kind="chunk", layer="front",
                gravity=60.0)
        # HIT: collision vs unit (visual only) / tiba di titik tujuan
        if units is not None:
            for u in units:
                if not getattr(u, "alive", True):
                    continue
                ux = float(getattr(u, "x", 1e9))
                uy = float(getattr(u, "y", 1e9))
                rr = float(getattr(u, "radius", 14)) + self.radius
                if (self.position.x - ux) ** 2 + \
                        (self.position.y - uy) ** 2 <= rr * rr:
                    self._tx, self._ty = ux, uy
                    self.kill(impact=True)
                    return
        if self._traveled >= self._dist:
            self.kill(impact=True)

    # ------------------------------------------------------------------
    def draw(self, surface):
        # TRAIL memudar
        for i, (tx, ty, ta) in enumerate(self.trail):
            a = max(0.0, 1.0 - ta / 0.22)
            if a <= 0.05:
                continue
            sz = max(1, int((2 if self.kind == "splinter" else 3) * a))
            pygame.draw.rect(surface, (*P["fx_dark"], int(70 * a)),
                             (int(tx) - sz, int(ty) - sz, sz * 2, sz * 2))
        if not self.active:
            return
        x, y = int(self.position.x), int(self.position.y)
        ca, sa = math.cos(self.angle), math.sin(self.angle)
        nx, ny = -sa, ca
        r = self.radius
        # GLOW halo
        if glow_allowed():
            gl = glow_surface(int(r * 2.2), P["fx_mid"], 0.8)
            _blit_faded(surface, gl, x, y, 160, additive=True)
        # DIRECTIONAL SHAPE: kepala lanset 3 lapis + sayat samping
        col_d = P["frost_dark"] if self.kind == "splinter" else P["fx_darkest"]
        col_m = P["frost_mid"] if self.kind == "splinter" else P["fx_mid"]
        col_h = P["frost_hot"] if self.kind == "splinter" else P["fx_hot"]
        head = [
            (x + ca * r * 2.1, y + sa * r * 2.1),
            (x + nx * r * 0.9, y + ny * r * 0.9),
            (x - ca * r * 1.1, y - sa * r * 1.1),
            (x - nx * r * 0.9, y - ny * r * 0.9),
        ]
        pygame.draw.polygon(surface, col_d, head)
        pygame.draw.polygon(surface, col_m, [
            (x + ca * r * 1.6, y + sa * r * 1.6),
            (x + nx * r * 0.5, y + ny * r * 0.5),
            (x - ca * r * 0.7, y - sa * r * 0.7),
            (x - nx * r * 0.5, y - ny * r * 0.5),
        ])
        pygame.draw.polygon(surface, col_h, [
            (x + ca * r * 1.4, y + sa * r * 1.4),
            (x, y), (x - ca * r * 0.3, y - sa * r * 0.3),
        ])
        # inti berputar (kristal kecil) — rotasi terlihat
        rot = self.rotation
        for i in range(3):
            a = rot + i * math.tau / 3
            px = x + math.cos(a) * r * 0.55
            py = y + math.sin(a) * r * 0.55
            pygame.draw.rect(surface, (*P["fx_white"], 210),
                             (int(px), int(py), 1, 1))
        pygame.draw.rect(surface, (*P["fx_white"], 255), (x, y, 2, 2))


class ProjectileSystem:
    """Manajer proyektil + pemilik ImpactFX saat mendarat."""

    def __init__(self, particles=None, cap=MAX_PROJECTILES):
        self.particles = particles
        self.cap = int(cap)
        self.items = []
        self.impacts = []

    def count(self):
        return len(self.items)

    def list(self):
        return self.items

    def clear(self):
        self.items.clear()
        self.impacts.clear()

    def spawn(self, x, y, tx, ty, **kw):
        if len(self.items) >= self.cap:
            self.items.pop(0).kill(impact=False)
        pr = NyzrakProjectile(x, y, tx, ty, particles=self.particles, **kw)
        self.items.append(pr)
        return pr

    def update(self, dt, units=None):
        for pr in self.items:
            was_active = pr.active
            pr.update(dt, units)
            if was_active and not pr.active:
                # IMPACT FX pada titik hancur
                power = 0.7 + min(1.3, pr.damage / 60.0) if pr.damage else 0.9
                self.impacts.append(ImpactFX(
                    pr.position.x, pr.position.y, pr.angle, power,
                    pr.crit, "frost" if pr.kind == "splinter" else "spear",
                    self.particles))
                if len(self.impacts) > MAX_IMPACTS:
                    self.impacts.pop(0)
        self.items = [p for p in self.items if p.active]
        for im in self.impacts:
            im.update(dt)
        self.impacts = [i for i in self.impacts if i.alive]

    def draw(self, surface):
        for pr in self.items:
            pr.draw(surface)
        for im in self.impacts:
            im.draw(surface)


# ============================================================================
# 9.  SKILL FX  —  lifecycle cast -> charge -> release -> area -> after
# ============================================================================

class SkillFX:
    """FX skill Q/W/E/R dengan lifecycle lengkap.

    Progress TIDAK dihitung dari umur sendiri: setiap update director
    memberi t01 = 1 - active_skill_timer/dur supaya FX selalu sinkron
    persis dengan AI (apa pun yang terjadi pada framerate).
    """

    def __init__(self, kind, x, y, particles=None, projectiles=None,
                 radius=None, aim=None):
        self.kind = kind
        self.x = float(x)
        self.y = float(y)
        self.radius = float(radius if radius is not None
                            else WORLD_RADIUS.get(kind, 60.0))
        self.aim = float(aim if aim is not None else 0.0)
        self.t01 = 0.0
        self.dead = False
        self.released = False
        self.erupted = False
        self.nova_done = False
        self.particles = particles
        self.projectiles = projectiles
        self._seed = random.uniform(0, math.tau)
        self._tail = 0.0
        # target titik efek (untuk e: posisi target; lain: depan caster)
        self.ex = self.x + math.cos(self.aim) * 90.0
        self.ey = self.y + math.sin(self.aim) * 40.0 - 10.0

    def set_target_point(self, tx, ty):
        self.ex = float(tx)
        self.ey = float(ty)

    # ------------------------------------------------------------------
    def update(self, dt, t01, boss=None):
        self.t01 = min(1.0, max(0.0, t01))
        ps = self.particles

        # CHARGE: partikel es mengalir masuk ke mata tombak / badan
        if 0.18 <= self.t01 < 0.38 and ps is not None:
            if self._tail <= 0.0:
                self._tail = 0.05
                cx, cy = self.x, self.y - 40
                col = P["frost_bright"] if self.kind == "q" else P["fx_bright"]
                ps.stream(cx + random.uniform(-46, 46),
                          cy + random.uniform(-30, 30),
                          cx, cy, 3, (0.25, 0.45), (1, 2), col, "chunk")
            else:
                self._tail -= dt

        # RELEASE events (sekali)
        if not self.released and self.t01 >= 0.38:
            self.released = True
            self._release()

        # AREA: trailing per skill
        if 0.5 <= self.t01 < 0.78 and ps is not None and \
                self._tail <= 0.0:
            self._tail = 0.06
            if self.kind == "q":
                # serpihan es mengalir sepanjang beam
                t = random.uniform(0.15, 0.95)
                bx = self.x + (self.ex - self.x) * t
                by = (self.y - 44) + (self.ey - (self.y - 44)) * t
                ps.burst(bx, by, 2, (20, 90), (0.2, 0.5), (1, 2),
                         P["frost_bright"], "snow", "front",
                         spread=math.tau, rot_speed=(-6, 6))
            elif self.kind == "r":
                ps.burst(self.x, self.y - 6, 2, (60, 200), (0.3, 0.7),
                         (1, 2), P["fx_bright"], "snow", "front",
                         spread=math.tau, gravity=-40.0, drag=1.0)
        if self._tail > 0.0:
            self._tail -= dt

        # AFTER -> FADE selesai
        if self.t01 >= 1.0:
            self.dead = True

    # ------------------------------------------------------------------
    def _release(self):
        ps = self.particles
        prj = self.projectiles
        if self.kind == "q":
            # muzzle + impact besar di target
            if ps is not None:
                ps.burst(self.x, self.y - 44, 10, (60, 240), (0.2, 0.5),
                         (1, 2), P["frost_bright"], "shard", "front",
                         spread=math.tau, rot_speed=(-8, 8))
        elif self.kind == "w":
            # kerucut serpihan: proyektil SPLINTER betulan
            base = math.atan2(self.ey - (self.y - 20), self.ex - self.x)
            if prj is not None:
                for i in range(6):
                    a = base + (i - 2.5) * 0.16
                    prj.spawn(self.x + math.cos(a) * 24,
                              self.y - 20 + math.sin(a) * 12,
                              self.x + math.cos(a) * 320.0,
                              self.y - 20 + math.sin(a) * 160.0,
                              speed=SPLINTER_SPEED, kind="splinter",
                              radius=5.0, lifetime=0.8, damage=40.0)
            if ps is not None:
                ps.burst(self.x + 20, self.y - 20, 12, (80, 300),
                         (0.15, 0.4), (1, 3), P["fx_light"], "chunk",
                         "front", spread=1.2, ang0=base - 0.6)
        elif self.kind == "e":
            # erupsi kristal di titik target
            if ps is not None:
                ps.burst(self.ex, self.ey, 22, (60, 300), (0.25, 0.7),
                         (1, 3), P["fx_bright"], "shard", "front",
                         spread=math.tau, gravity=420.0, drag=0.8,
                         rot_speed=(-9, 9))
                ps.burst(self.ex, self.ey, 8, (20, 90), (0.4, 0.9), (3, 6),
                         P["mist"], "smoke", "back", spread=math.tau)
        elif self.kind == "r":
            if ps is not None:
                ps.burst(self.x, self.y - 10, 26, (120, 460), (0.25, 0.7),
                         (1, 3), P["fx_bright"], "shard", "front",
                         spread=math.tau, gravity=160.0, drag=1.3,
                         rot_speed=(-8, 8))
                ps.burst(self.x, self.y - 6, 12, (20, 110), (0.5, 1.1),
                         (3, 7), P["mist"], "smoke", "back",
                         spread=math.tau)
                for i in range(6):
                    ps.spawn(self.x + random.uniform(-40, 40),
                             self.y - random.uniform(0, 60), 0, -60.0,
                             random.uniform(0.5, 0.9), 2, P["fx_white"],
                             kind="glint", layer="front")

    # ------------------------------------------------------------------
    def draw_ground(self, surface):
        """Lapisan bawah sprite: telegraph + tanah."""
        k = self.t01
        if self.kind == "e":
            if k < 0.38:
                # telegraph: cincin dash menyempit ke titik target
                rr = int(self.radius * 2.2 * (1.0 - k / 0.38)) + 12
                ring = ring_surface(rr, 2, P["fx_mid"], 10)
                _blit_faded(surface, ring, self.ex, self.ey,
                            140 + 80 * (k / 0.38))
            else:
                # tanah retak es
                fade = max(0.0, 1.0 - max(0.0, (k - 0.75) / 0.25))
                if fade > 0:
                    rr = int(self.radius * 1.6)
                    ring = ring_surface(rr, 2, P["fx_light"], 12)
                    _blit_faded(surface, ring, self.ex, self.ey,
                                150 * fade)
                    for i in range(6):
                        a = self._seed + i * math.tau / 6
                        x0 = self.ex + math.cos(a) * rr * 0.6
                        y0 = self.ey + math.sin(a) * rr * 0.3
                        x1 = self.ex + math.cos(a) * rr * 1.1
                        y1 = self.ey + math.sin(a) * rr * 0.55
                        pygame.draw.line(surface,
                                         (*P["fx_mid"], int(120 * fade)),
                                         (x0, y0), (x1, y1), 1)
        elif self.kind == "r":
            if 0.18 <= k < 0.5:
                fade = 1.0 - abs(k - 0.34) / 0.16
                rr = int(self.radius * (0.4 + k))
                ring = ring_surface(rr, 2, P["fx_bright"], 14)
                _blit_faded(surface, ring, self.x, self.y + 14,
                            max(0.0, 160 * fade))

    # ------------------------------------------------------------------
    def draw_front(self, surface):
        k = self.t01
        if self.kind == "q":
            self._draw_q_beam(surface, k)
        elif self.kind == "w":
            self._draw_w_cone(surface, k)
        elif self.kind == "e":
            self._draw_e_tomb(surface, k)
        elif self.kind == "r":
            self._draw_r_nova(surface, k)

    # ------------------------------------------------------------------
    def _draw_q_beam(self, surface, k):
        """BEAM Arctic Burn: strip kristal bergerigi + inti + riak."""
        if k < 0.38:
            # charge glow di mata tombak
            g = 6 + int(26 * (k / 0.38))
            gl = glow_surface(g, P["frost_mid"], 1.0)
            _blit_faded(surface, gl, self.x, self.y - 44,
                        120 + 120 * (k / 0.38), additive=True)
            return
        fade = max(0.0, 1.0 - max(0.0, (k - 0.78) / 0.22))
        if fade <= 0.0:
            return
        t_ext = min(1.0, (k - 0.38) / 0.10)     # beam menjulur cepat
        sx, sy = self.x, self.y - 44
        ex = sx + (self.ex - sx) * t_ext
        ey = sy + (self.ey - sy) * t_ext
        ux, uy = ex - sx, ey - sy
        dist = math.hypot(ux, uy)
        if dist < 4:
            return
        ux, uy = ux / dist, uy / dist
        nx, ny = -uy, ux
        time = pygame.time.get_ticks() * 0.006
        steps = max(3, int(dist / 7))
        top, bot, core = [], [], []
        for i in range(steps + 1):
            tp = i / steps
            bx = sx + ux * dist * tp
            by = sy + uy * dist * tp
            w = (4.5 + 2.0 * math.sin(time * 3 + tp * 10)) * \
                (1.0 - 0.25 * tp)
            jag = 3.5 * math.sin(tp * 40 + time * 8)     # gerigi es
            top.append((bx + nx * (w + jag), by + ny * (w + jag)))
            bot.append((bx - nx * (w - jag), by - ny * (w - jag)))
            core.append((bx, by))
        # temp seukuran bbox beam
        allp = top + bot
        bxs = int(min(p[0] for p in allp)) - 4
        bys = int(min(p[1] for p in allp)) - 4
        bws = int(max(p[0] for p in allp)) - bxs + 4
        bhs = int(max(p[1] for p in allp)) - bys + 4
        if bws <= 2 or bhs <= 2:
            return
        tmp = pygame.Surface((bws, bhs), pygame.SRCALPHA)
        top_l = [(p[0] - bxs, p[1] - bys) for p in top]
        bot_l = [(p[0] - bxs, p[1] - bys) for p in bot]
        core_l = [(p[0] - bxs, p[1] - bys) for p in core]
        pygame.draw.polygon(tmp, (*P["frost_dark"], int(150 * fade)),
                            top_l + bot_l[::-1])
        pygame.draw.polygon(tmp, (*P["frost_mid"], int(200 * fade)),
                            [(cx + nx * 1.8, cy + ny * 1.8)
                             for cx, cy in core_l]
                            + [(cx - nx * 1.8, cy - ny * 1.8)
                               for cx, cy in core_l[::-1]])
        pygame.draw.polygon(tmp, (*P["frost_hot"], int(235 * fade)),
                            [(cx + nx * 0.8, cy + ny * 0.8)
                             for cx, cy in core_l]
                            + [(cx - nx * 0.8, cy - ny * 0.8)
                               for cx, cy in core_l[::-1]])
        surface.blit(tmp, (bxs, bys), special_flags=pygame.BLEND_RGB_ADD)
        # impact berdenyut di ujung
        pk = 0.5 + 0.5 * math.sin(time * 10)
        gl = glow_surface(int(16 + 10 * pk), P["frost_bright"], 1.0)
        _blit_faded(surface, gl, ex, ey, 210 * fade, additive=True)
        for i in range(4):
            a = time * 2 + i * math.tau / 4
            x2 = ex + math.cos(a) * 16
            y2 = ey + math.sin(a) * 8
            spr = snowflake_surface(3, P["frost_hot"])
            _blit_faded(surface, spr, x2, y2, 200 * fade)

    def _draw_w_cone(self, surface, k):
        """Kerucut Splinter Blast memudar."""
        if k < 0.38:
            return
        fade = max(0.0, 1.0 - (k - 0.38) / 0.4)
        if fade <= 0.0:
            return
        sx, sy = self.x, self.y - 20
        a = math.atan2(self.ey - sy, self.ex - sx)
        ln = 70 * fade + 30
        for i, w in ((-0.5, 10), (0.0, 13), (0.5, 10)):
            x2 = sx + math.cos(a + i * 0.35) * ln
            y2 = sy + math.sin(a + i * 0.35) * ln
            pygame.draw.line(surface, (*P["fx_light"], int(120 * fade)),
                             (sx, sy), (x2, y2), 2)
        gl = glow_surface(int(18 * fade) + 6, P["fx_bright"], 0.9)
        _blit_faded(surface, gl, sx + math.cos(a) * 18,
                    sy + math.sin(a) * 18, 180 * fade, additive=True)

    def _draw_e_tomb(self, surface, k):
        """Kurungan kristal Winter's Curse: pilar faset + paku."""
        if k < 0.38:
            return
        grow = min(1.0, (k - 0.38) / 0.18)
        fade = max(0.0, 1.0 - max(0.0, (k - 0.8) / 0.2))
        if fade <= 0.0:
            return
        cx, cy = self.ex, self.ey
        w = int(20 * grow)
        h = int(46 * grow)
        pts = [(cx - w, cy + 4), (cx - w, cy - h + 6),
               (cx - w // 2, cy - h), (cx + w // 2, cy - h),
               (cx + w, cy - h + 6), (cx + w, cy + 4)]
        pygame.draw.polygon(surface, (*P["fx_darkest"], int(190 * fade)),
                            pts)
        pygame.draw.polygon(surface, (*P["fx_mid"], int(140 * fade)), [
            (cx - w + 3, cy + 3), (cx - w + 3, cy - h + 9),
            (cx - w // 2 + 3, cy - h + 3), (cx + w // 2 - 3, cy - h + 3),
            (cx + w - 3, cy - h + 9), (cx + w - 3, cy + 3)])
        # faset diagonal
        for i in range(3):
            pygame.draw.line(surface, (*P["fx_light"], int(150 * fade)),
                             (cx - w + 4, cy - i * 11),
                             (cx - w // 2, cy - h + i * 6 + 5), 1)
            pygame.draw.line(surface, (*P["fx_light"], int(150 * fade)),
                             (cx + w - 4, cy - i * 11),
                             (cx + w // 2, cy - h + i * 6 + 5), 1)
        pygame.draw.line(surface, (*P["fx_hot"], int(220 * fade)),
                         (cx, cy - h + 3), (cx, cy - 4), 1)
        # paku mahkota
        for off in (-w + 2, 0, w - 2):
            pygame.draw.polygon(surface, (*P["fx_mid"], int(220 * fade)), [
                (cx + off - 3, cy - h + 4), (cx + off + 3, cy - h + 4),
                (cx + off, cy - h - 10 * grow)])
            pygame.draw.line(surface, (*P["fx_white"], int(190 * fade)),
                             (cx + off, cy - h + 2),
                             (cx + off, cy - h - 8 * grow), 1)

    def _draw_r_nova(self, surface, k):
        """Cold Embrace: shockwave ganda + kubah faset + salju orbit."""
        if k < 0.38:
            # energi terkumpul mengecil
            g = int(30 * (1.0 - (k / 0.38))) + 8
            gl = glow_surface(g, P["fx_bright"], 1.0)
            _blit_faded(surface, gl, self.x, self.y - 10,
                        110 + 130 * (k / 0.38), additive=True)
            return
        fade = max(0.0, 1.0 - max(0.0, (k - 0.75) / 0.25))
        if fade <= 0.0:
            return
        cx, cy = self.x, self.y - 8
        # shockwave ring ganda (dash chunky)
        for j, spd in ((0, 1.0), (1, 0.62)):
            rr = int(self.radius * 0.9 * min(1.0, (k - 0.38) / 0.35)
                     * spd + 8)
            if rr > 3:
                ring = ring_surface(rr, 2, P["fx_bright"], 12 + j * 4)
                _blit_faded(surface, ring, cx, cy,
                            int(210 * fade * (1.0 - j * 0.35)),
                            additive=True)
        # kubah faset (panel, bukan lingkaran)
        dome_k = min(1.0, (k - 0.42) / 0.16)
        if dome_k > 0.0:
            R = int(46 * dome_k)
            if R > 5:
                # Panel kubah dibuat sebagai CANGKANG (pita di tepi),
                # bukan segitiga dari titik pusat. Versi lama menggambar
                # 7 baji penuh dari (cx, cy) ke radius 46 — persis di atas
                # badan Nyzrak — sehingga ultimate menutupinya dengan
                # kipas abu-abu buram.
                panels = 7
                inner = 0.62
                for i in range(panels):
                    a0 = i * math.pi / panels + 0.15
                    a1 = (i + 1) * math.pi / panels + 0.15
                    p0 = (cx + math.cos(a0) * R,
                          cy + math.sin(a0) * R * 0.9)
                    p1 = (cx + math.cos(a1) * R,
                          cy + math.sin(a1) * R * 0.9)
                    q1 = (cx + math.cos(a1) * R * inner,
                          cy + math.sin(a1) * R * 0.9 * inner)
                    q0 = (cx + math.cos(a0) * R * inner,
                          cy + math.sin(a0) * R * 0.9 * inner)
                    col = P["fx_mid"] if i % 2 else P["fx_light"]
                    pygame.draw.polygon(
                        surface, (*col, int(70 * fade)), [p0, p1, q1, q0])
                pygame.draw.ellipse(
                    surface, (*P["fx_bright"], int(95 * fade)),
                    (cx - R, cy - int(R * 0.92), R * 2, int(R * 1.84)), 2)
        # salju orbit
        time = pygame.time.get_ticks() * 0.004
        for i in range(7):
            a = time + i * math.tau / 7
            rr = 40 + 26 * dome_k
            x2 = cx + math.cos(a) * rr
            y2 = cy - 10 + math.sin(a) * rr * 0.42
            spr = snowflake_surface(3, P["fx_hot"])
            _blit_faded(surface, spr, x2, y2, 200 * fade)


# ============================================================================
# 10.  DIRECTOR  —  satu instance per unit Nyzrak
# ============================================================================

class NyzrakFXDirector:
    """Mengikat trail + partikel + proyektil + skill FX + impact ke satu
    unit, memantau tepi state (attack/skill/hurt/death) tiap frame."""

    def __init__(self, hero):
        self.hero = hero
        self.particles = ParticleSystem(MAX_PARTICLES)
        self.projectiles = ProjectileSystem(self.particles)
        self.skills = []
        self.impacts = []
        self.trail = SwingTrail()
        self.x = float(getattr(hero, "x", 0.0))
        self.y = float(getattr(hero, "y", 0.0))
        self._prev_action = "idle"
        self._prev_ap = 0.0
        self._prev_skill = None
        self._prev_hurt = 0
        self._prev_alive = True
        self._swing_started = False
        self._released = False
        self._ambient = 0.0
        self._run_puff = 0.0
        self._ghosts = []             # afterimage [(x, y, age, facing)]
        self._hit_flash = 0.0
        self._fps_ema = 60.0
        self._last_dt = FIXED_DT

    # ------------------------------------------------------------------
    # EVENT hooks (dipanggil notify_* / deteksi internal)
    # ------------------------------------------------------------------
    def on_swing_start(self, x, y, facing):
        """Whoosh: debu es dari titik awal ayunan."""
        self.particles.burst(x + 10 * facing, y - 30, 6, (30, 120),
                             (0.2, 0.45), (1, 2), P["fx_light"], "chunk",
                             "front", spread=math.tau, gravity=110.0)
        shake(1.5, 0.1)

    def on_swing_impact_frame(self, x, y, facing):
        """Bingkai IMPACT sapuan melee (aktif walau belum kena target)."""
        self.particles.burst(x + 30 * facing, y - 18, 8, (60, 200),
                             (0.15, 0.4), (1, 2), P["fx_bright"], "chunk",
                             "front", spread=2.0, ang0=-1.2 + (0 if facing > 0 else math.pi),
                             gravity=220.0)

    def on_thrust_release(self, sx, sy, tx, ty):
        """Proyektil serangan dasar (varian thrust)."""
        self.projectiles.spawn(sx, sy, tx, ty, speed=SHARD_SPEED,
                               kind="shard", radius=6.0, lifetime=1.1,
                               damage=getattr(self.hero, "damage", 0.0)
                               or 0.0)
        self.particles.burst(sx, sy, 6, (40, 160), (0.12, 0.3), (1, 2),
                             P["fx_bright"], "spark", "front",
                             spread=1.4, ang0=math.atan2(ty - sy, tx - sx)
                             - 0.7)

    def on_cast(self, x, y, skill, aim=0.0, tx=None, ty=None):
        if len(self.skills) >= MAX_SKILLS:
            self.skills.pop(0)
        fx = SkillFX(skill, x, y, self.particles, self.projectiles,
                     aim=aim)
        if tx is not None and ty is not None:
            fx.set_target_point(tx, ty)
        self.skills.append(fx)
        shake(3.0 if skill != "r" else 5.0, 0.16)

    def on_impact(self, x, y, angle=0.0, power=1.0, crit=False,
                  kind="spear"):
        if len(self.impacts) >= MAX_IMPACTS:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(x, y, angle, power, crit, kind,
                                     self.particles))
        hit_stop(0.033 + min(0.047, 0.02 * power))
        shake(3.0 + 5.0 * power, 0.16 + 0.05 * power)

    def on_hurt(self, amount=1.0):
        self._hit_flash = 0.16
        self.particles.burst(self.x, self.y - 30, int(4 + 6 * amount),
                             (50, 200), (0.15, 0.4), (1, 2),
                             P["fx_light"], "chunk", "front",
                             spread=math.tau, gravity=300.0)

    def on_death(self, x, y):
        """Shatter es: wyvern pecah jadi serpihan."""
        self.particles.burst(x, y - 24, 40, (60, 420), (0.3, 0.9), (1, 4),
                             P["fx_bright"], "shard", "front",
                             spread=math.tau, gravity=420.0, drag=0.6,
                             rot_speed=(-10, 10))
        self.particles.burst(x, y - 10, 14, (20, 120), (0.6, 1.4), (4, 8),
                             P["mist"], "smoke", "back", spread=math.tau)
        self.on_impact(x, y - 20, 0.0, 1.8, True, "nova")
        self.trail.reset()

    # ------------------------------------------------------------------
    # UPDATE — dipanggil tick() tiap frame
    # ------------------------------------------------------------------
    def update(self, dt, x, y):
        hero = self.hero
        if hero is None:
            return
        self.x = float(x)
        self.y = float(y)
        self._last_dt = dt
        if dt > 0:
            self._fps_ema = self._fps_ema * 0.92 + (1.0 / dt) * 0.08

        info = anim_state(hero)
        action, ap = info["action"], info["ap"]
        phase = info["phase"]
        facing = 1 if (getattr(hero, "direction", 1) or 1) >= 0 else -1
        scale = render_scale(hero)

        # ── hurt edge ─────────────────────────────────────────────
        hurt = int(getattr(hero, "hurt_flash_timer", 0) or 0)
        if hurt > 0 and self._prev_hurt <= 0:
            self.on_hurt(1.0)
        self._prev_hurt = hurt
        self._hit_flash = max(0.0, self._hit_flash - dt)

        # ── death edge ────────────────────────────────────────────
        alive = bool(getattr(hero, "alive", True)) and \
            float(getattr(hero, "hp", 1.0) or 0.0) > 0.0
        if self._prev_alive and not alive:
            self.on_death(self.x, self.y)
        self._prev_alive = alive

        # ── attack: trail + release events ────────────────────────
        if action == "attack":
            grip, tip, st = spear_points(hero, x, y)
            self.trail.push(grip, tip)
            # mulai jendela aktif -> whoosh
            if not self._swing_started and st["active"]:
                self._swing_started = True
                self.on_swing_start(x, y, facing)
            # bingkai impact (0.56) -> debu sapuan
            if (self._prev_ap < 0.56 <= ap) and \
                    getattr(_renderer(), "_pose_variant_now", "thrust") == "sweep":
                self.on_swing_impact_frame(x, y, facing)
            # peluncuran proyektil varian thrust
            R = _renderer()
            release = getattr(R, "ATTACK_RELEASE", 0.46) if R else 0.46
            variant = getattr(R, "_pose_variant_now", "thrust") if R else "thrust"
            if not self._released and ap >= release:
                self._released = True
                if variant == "thrust":
                    tgt = getattr(hero, "target", None)
                    if tgt is not None and getattr(tgt, "alive", False):
                        sc = scale
                        tx = x + (tgt.x - self.x) * sc
                        ty = y + (tgt.y - self.y) * sc
                    else:
                        tx = tip.x + facing * 200.0
                        ty = tip.y
                    self.on_thrust_release(tip.x, tip.y, tx, ty)
        else:
            self._swing_started = False
            self._released = False
        self._prev_ap = ap
        self.trail.update(dt)

        # ── skill edge: buat SkillFX baru, target point dari target ─
        skill = getattr(hero, "active_skill", None)
        if skill in SKILL_DUR and skill != self._prev_skill:
            tgt = getattr(hero, "target", None)
            if tgt is not None and getattr(tgt, "alive", False):
                sc = scale
                tx = x + (tgt.x - self.x) * sc
                ty = y + (tgt.y - self.y) * sc
                aim = math.atan2(ty - (y - 30), tx - x)
            else:
                tx = x + 180.0 * facing
                ty = y - 10.0
                aim = 0.0 if facing > 0 else math.pi
            self.on_cast(x, y, skill, aim, tx, ty)
            if skill == "r":
                hit_stop(0.05)
                shake(9.0, 0.3)
        self._prev_skill = skill

        # maju semua skill FX dengan progress dari timer AI
        timer = float(getattr(hero, "active_skill_timer", 0) or 0)
        for fx in self.skills:
            if fx.kind == skill and skill in SKILL_DUR:
                t01 = 1.0 - timer / float(SKILL_DUR[skill])
            else:
                t01 = min(1.0, fx.t01 + dt / 0.8)
            fx.update(dt, t01, hero)
        self.skills = [f for f in self.skills if not f.dead]

        # ── afterimage saat lari / dash ───────────────────────────
        speed = float(getattr(hero, "_nyz_move_mag", 0.0))
        if info["state"] == "RUN" and speed > 2.4:
            self._ghosts.append((x, y, 0.0, facing))
            if len(self._ghosts) > 5:
                self._ghosts.pop(0)
        for gi in range(len(self._ghosts) - 1, -1, -1):
            gx, gy, gage, gf = self._ghosts[gi]
            gage += dt
            if gage > 0.24:
                self._ghosts.pop(gi)
            else:
                self._ghosts[gi] = (gx, gy, gage, gf)

        # ── ambient: salju halus + debu lari ──────────────────────
        self._ambient -= dt
        if self._ambient <= 0.0:
            self._ambient = 0.12
            if particle_budget() > 0.0:
                self.particles.spawn(
                    x + random.uniform(-30, 30) * scale,
                    y - random.uniform(10, 60) * scale,
                    random.uniform(-14, 14), -random.uniform(8, 26),
                    random.uniform(0.5, 1.1),
                    random.randint(1, 2), P["snow"], kind="snow",
                    layer="back", rot_speed=random.uniform(-3, 3))
        if info["state"] == "RUN" and speed > 2.4:
            self._run_puff -= dt
            if self._run_puff <= 0.0:
                self._run_puff = 0.09
                gy = y + ground_dy(hero) - 2
                self.particles.burst(x - facing * 18 * scale, gy, 3,
                                     (20, 90), (0.25, 0.5), (1, 3),
                                     P["mist"], "smoke", "back",
                                     spread=math.pi, ang0=math.pi if facing > 0 else 0.0)

        self.particles.update(dt)
        self.projectiles.update(dt)
        for im in self.impacts:
            im.update(dt)
        self.impacts = [i for i in self.impacts if i.alive]
        self._prev_action = action

    # ------------------------------------------------------------------
    # DRAW — dua lapis (ground: bawah sprite; front: atas sprite)
    # ------------------------------------------------------------------
    def draw_ground(self, surface):
        for fx in self.skills:
            fx.draw_ground(surface)
        self.particles.draw(surface, "back")
        # afterimage siluet wyvern (transparan, di belakang badan)
        for gx, gy, gage, gf in self._ghosts:
            k = 1.0 - gage / 0.24
            if k <= 0.05:
                continue
            sc = render_scale(self.hero) * 1.0
            tmp = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            col = (*P["mid"], int(46 * k))
            pygame.draw.ellipse(tmp, col,
                                (gx - 26 * sc, gy - 26 * sc,
                                 52 * sc, 22 * sc))
            pygame.draw.ellipse(tmp, (*P["light"], int(38 * k)),
                                (gx - 10 * sc, gy - 62 * sc,
                                 20 * sc, 34 * sc))
            pygame.draw.polygon(tmp, (*P["mid"], int(40 * k)), [
                (gx - 30 * sc * gf, gy - 20 * sc),
                (gx + 26 * sc * gf, gy - 20 * sc),
                (gx + 14 * sc * gf, gy - 48 * sc)])
            surface.blit(tmp, (0, 0))

    def draw_front(self, surface, x, y):
        # trail tombak (di atas badan, di bawah proyektil)
        if self.trail.active():
            self.trail.draw(surface)
        self.projectiles.draw(surface)
        self.particles.draw(surface, "front")
        for fx in self.skills:
            fx.draw_front(surface)
        for im in self.impacts:
            im.draw(surface)
        self._draw_hit_flash(surface)
        if DEBUG_CHARACTER:
            draw_debug_overlay(surface, self, x, y)

    def _draw_hit_flash(self, surface):
        """IMPACT FLASH: glow es kecil — BUKAN cakram putih di atas badan.

        Versi lama menggambar lingkaran ``fx_white`` radius ~44 px dengan
        alpha 70, lalu mem-blit-nya ``BLEND_RGB_ADD``. Mode itu MENGABAIKAN
        alpha, jadi yang muncul adalah cakram putih JENUH yang menutupi
        ~75% siluet Nyzrak setiap kali dia kena damage.
        """
        if self._hit_flash <= 0.0:
            return
        k = max(0.0, min(1.0, self._hit_flash / 0.16))
        # Lane boss menggambar flash siluetnya sendiri (hurt_flash_timer);
        # dua flash penuh di frame yang sama terbaca sebagai white-out.
        if int(getattr(self.hero, "hurt_flash_timer", 0) or 0) > 0:
            k *= 0.35
        if k <= 0.02:
            return
        cx, cy = int(self.x), int(self.y - 26)
        rs = render_scale(self.hero)
        r = max(6, int(20 * rs))
        if glow_allowed():
            g = glow_surface(r, P["fx_bright"], 0.5 * k)
            _blit_faded(surface, g, cx, cy, int(220 * k), additive=True)
        s = max(3, int(9 * rs * (0.5 + 0.5 * k)))
        star = spark_surface(s, P["fx_white"])
        star.set_alpha(int(165 * k))
        surface.blit(star, (cx - star.get_width() // 2,
                            cy - star.get_height() // 2))
        star.set_alpha(255)

    def clear(self):
        self.particles.clear()
        self.projectiles.clear()
        self.skills.clear()
        self.impacts.clear()
        self.trail.reset()
        self._ghosts.clear()
        self._hit_flash = 0.0

    def stats(self):
        return {"particles": self.particles.count(),
                "projectiles": self.projectiles.count(),
                "skills": len(self.skills),
                "impacts": len(self.impacts),
                "state": anim_state(self.hero)["state"],
                "fps": self._fps_ema}


# ============================================================================
# 11.  BUS ADAPTER  (hit-stop & shake lewat combat_feel)
# ============================================================================

def _feel_shake(strength, duration):
    if _feel is None:
        return
    try:
        _feel.shake(strength, duration)
    except Exception:                          # pragma: no cover
        pass


def _feel_hit_stop(seconds):
    if _feel is None:
        return
    try:
        _feel.hit_stop(seconds)
    except Exception:                          # pragma: no cover
        pass


def should_freeze_frame():
    """Dipanggil ``Game.update``: True kalau langkah simulasi dibekukan."""
    if not NYZRAK_FX_ENABLED or _feel is None:
        return False
    return _feel.should_freeze_frame()


def hit_stop(seconds=0.045):
    """API publik: minta hit-stop global (dijepit 0.03-0.08 s)."""
    _feel_hit_stop(seconds)


def shake(strength=5.0, duration=0.22):
    """API publik: guncangkan layar."""
    if not shake_allowed():
        return
    _feel_shake(strength, duration)


# ============================================================================
# 12.  DEBUG OVERLAY  (DEBUG_CHARACTER = True)
# ============================================================================

_DEBUG_FONT = None


def _debug_font():
    global _DEBUG_FONT
    if _DEBUG_FONT is None:
        try:
            _DEBUG_FONT = pygame.font.Font(None, 15)
        except Exception:                      # pragma: no cover
            _DEBUG_FONT = False
    return _DEBUG_FONT or None


def draw_debug_overlay(surface, director, x, y):
    f = _debug_font()
    hero = director.hero
    info = anim_state(hero)
    R = _renderer()
    scale = render_scale(hero)
    facing = 1 if (getattr(hero, "direction", 1) or 1) >= 0 else -1

    # hurtbox (lingkaran radius badan)
    rr = int(float(getattr(hero, "radius", 26)) * scale)
    pygame.draw.circle(surface, (90, 220, 90, 160), (int(x), int(y - 24 * scale)), rr, 1)
    # attack range
    rng = int(float(getattr(hero, "range", 95)) * scale)
    pygame.draw.circle(surface, (250, 220, 90, 140),
                       (int(x), int(y - 24 * scale)), rng, 1)
    # hitbox arc saat jendela aktif
    if info["action"] == "attack" and R is not None:
        a0, a1 = R.ATTACK_ACTIVE
        ap = info["ap"]
        col = (255, 90, 90) if a0 <= ap <= a1 else (150, 150, 150)
        grip, tip, st = spear_points(hero, x, y)
        pygame.draw.line(surface, col, grip, tip, 2)
        pygame.draw.circle(surface, col, (int(tip.x), int(tip.y)), 4, 1)
        # sector arc
        ang = st["angle"]
        for i in range(10):
            a = ang - 0.9 + i * 0.2
            ex = grip.x + math.cos(a) * 46 * scale
            ey = grip.y + math.sin(a) * 46 * scale
            pygame.draw.line(surface, (*col, 120), grip, (ex, ey), 1)
    # projectile collision radius
    for pr in director.projectiles.items:
        pygame.draw.circle(surface, (90, 180, 255),
                           (int(pr.position.x), int(pr.position.y)),
                           int(pr.radius), 1)

    if f is None:
        return
    st = director.stats()
    lines = [
        "NYZRAK FX",
        "state : %s (%s)" % (st["state"], info["stage"]),
        "frame : %d" % (_Nyz_frame_index(info)),
        "ap    : %.2f%s" % (info["ap"],
                            " ACTIVE" if info["action"] == "attack" else ""),
        "skill : %s t=%.2f" % (info["skill"] or "-",
                               info["skill_t01"]),
        "atkT  : %s/%s" % (int(getattr(hero, "timer", 0)),
                           int(getattr(hero, "attack_cooldown", 0))),
        "parts : %d  proj: %d" % (st["particles"], st["projectiles"]),
        "skills: %d  imp : %d" % (st["skills"], st["impacts"]),
        "fps(ema): %.0f" % st["fps"],
    ]
    w = 118
    h = len(lines) * 13 + 8
    bx, by = int(x) + 30, int(y) - 120
    bg = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(bg, (0, 0, 0, 170), (0, 0, w, h), border_radius=4)
    pygame.draw.rect(bg, (120, 220, 255, 200), (0, 0, w, h), 1,
                     border_radius=4)
    surface.blit(bg, (bx, by))
    for i, ln in enumerate(lines):
        surface.blit(f.render(ln, True, (200, 240, 255)), (bx + 6, by + 5 + i * 13))


def _Nyz_frame_index(info):
    R = _renderer()
    if R is None:
        return 0
    try:
        return R._NyzAnimController.frame_index(info["state"], info["phase"])
    except Exception:
        return 0


# ============================================================================
# 13.  REGISTRY DIRECTOR + API MODUL
# ============================================================================

_DIRECTORS = []
_LAST_TICK_MS = None


def director_for(hero):
    """Ambil (atau buat) director FX untuk satu unit Nyzrak."""
    _sync_palette()
    d = getattr(hero, "_nyz_fx", None)
    if d is None:
        d = NyzrakFXDirector(hero)
        try:
            hero._nyz_fx = d
        except Exception:                      # pragma: no cover
            return d
        _DIRECTORS.append(d)
        if len(_DIRECTORS) > 12:               # jangkar tua dibuang
            old = _DIRECTORS.pop(0)
            _release(old)
    return d


def _release(director):
    """Lepas director dari registry DAN penanda milik-nya di unit."""
    try:
        if director.hero is not None:
            director.hero._nyz_fx = None
            director.hero._nyz_live_fx = False
    except Exception:                          # pragma: no cover
        pass
    director.clear()


def attach(hero):
    """Pasang lapisan hidup pada unit ini. Return True kalau aktif."""
    if not NYZRAK_FX_ENABLED or hero is None:
        return False
    try:
        director_for(hero)
    except Exception:                          # pragma: no cover
        return False
    try:
        hero._nyz_live_fx = True
    except Exception:                          # pragma: no cover
        return False
    return True


def owns(hero):
    """True kalau lapisan hidup sudah mengambil alih efek unit ini."""
    if not getattr(hero, "_nyz_live_fx", False):
        return False
    d = getattr(hero, "_nyz_fx", None)
    return d is not None and d in _DIRECTORS


def tick(dt=None):
    """Majukan waktu FX satu frame nyata; aman dipanggil berkali-kali."""
    global _LAST_TICK_MS
    if dt is not None:
        step = max(0.0, min(1.0 / 20.0, float(dt)))
        _advance(step)
        return step
    now = pygame.time.get_ticks()
    if now == _LAST_TICK_MS:
        return 0.0                             # frame sama: sudah maju
    if _feel is not None:
        _LAST_TICK_MS = now
        try:
            step = _feel.fx_dt()
        except Exception:                      # pragma: no cover
            step = 0.0
    else:                                      # pragma: no cover - fallback
        if _LAST_TICK_MS is None:
            _LAST_TICK_MS = now
            return 0.0
        ms = now - _LAST_TICK_MS
        _LAST_TICK_MS = now
        if ms <= 0:
            return 0.0
        step = max(1.0 / 240.0, min(1.0 / 20.0, ms / 1000.0))
        if _feel is not None and getattr(_feel, "HITSTOP", None) is not None:
            step *= 0.18
    _advance(step)
    return step


def _advance(step):
    """Langkahkan seluruh director dengan dt yang sama (langkah FX)."""
    if step <= 0.0 or not _DIRECTORS:
        return
    for d in _DIRECTORS:
        h = d.hero
        d.update(step, float(getattr(h, "x", 0.0)),
                 float(getattr(h, "y", 0.0)))


def reset_all():
    """Bersihkan seluruh state FX Nyzrak (ganti level / keluar match)."""
    global _LAST_TICK_MS
    _LAST_TICK_MS = None
    for d in list(_DIRECTORS):
        _release(d)
    _DIRECTORS.clear()


def total_particles():
    """Jumlah partikel Nyzrak hidup di seluruh arena (HUD perf)."""
    return sum(d.particles.count() for d in _DIRECTORS)


# --- hook yang dipanggil heroes/__init__.py + bosses/level3.py -------------

def draw_ground_layer(surface, hero, x, y):
    """Pre-pass: digambar SEBELUM sprite di-blit."""
    if not NYZRAK_FX_ENABLED:
        return
    if not attach(hero):
        return
    tick()
    d = getattr(hero, "_nyz_fx", None)
    if d is not None:
        d.draw_ground(surface)


def draw_live_layer(surface, hero, x, y):
    """Post-pass: digambar SESUDah sprite di-blit."""
    if not NYZRAK_FX_ENABLED:
        return
    d = director_for(hero)
    d.draw_front(surface, x, y)


# --- hook yang dipanggil _entity.py / bosses/base_boss.py -------------------

def notify_melee_impact(hero, target, damage=0, crit=False):
    """Tombak Nyzrak mendarat di target (basic attack melee)."""
    if not NYZRAK_FX_ENABLED or hero is None or target is None:
        return
    try:
        power = 0.75 + min(1.5, float(damage) / 70.0)
    except (TypeError, ValueError):
        power = 1.0
    tx = float(getattr(target, "x", getattr(hero, "x", 0.0)))
    ty = float(getattr(target, "y", getattr(hero, "y", 0.0))) - 6.0
    ang = math.atan2(ty - float(getattr(hero, "y", 0.0)),
                     tx - float(getattr(hero, "x", 0.0)))
    director_for(hero).on_impact(tx, ty, ang, power, bool(crit),
                                 kind="spear")


def notify_projectile_impact(hero, x, y, angle=0.0, damage=0, crit=False,
                             kind="shard"):
    """Proyektil es mengenai target."""
    if not NYZRAK_FX_ENABLED or hero is None:
        return
    try:
        power = 0.7 + min(1.6, float(damage) / 45.0)
    except (TypeError, ValueError):
        power = 1.0
    director_for(hero).on_impact(x, y, angle, power, bool(crit),
                                 kind="frost" if kind == "splinter"
                                 else "spear")


def notify_skill_impact(hero, x, y, radius=None, skill="q"):
    """Skill Nyzrak meledak di sebuah titik (Q/W/E AOE)."""
    if not NYZRAK_FX_ENABLED or hero is None:
        return
    d = director_for(hero)
    if len(d.skills) >= MAX_SKILLS:
        d.skills.pop(0)
    fx = SkillFX(skill, float(getattr(hero, "x", x)),
                 float(getattr(hero, "y", y)), d.particles, d.projectiles,
                 radius)
    fx.set_target_point(x, y)
    fx.t01 = 0.5                     # langsung fase area
    fx.released = True               # jangan spawn ulang release event
    d.skills.append(fx)
    d.on_impact(x, y, 0.0, 1.4 if skill != "r" else 2.0, skill == "r",
                kind="nova" if skill == "r" else "frost")


def notify_skill_cast(hero, skill):
    """Dipanggil jalur gameplay saat skill dilepas (opsional)."""
    if not NYZRAK_FX_ENABLED or hero is None or skill not in SKILL_DUR:
        return
    d = director_for(hero)
    d.on_cast(float(getattr(hero, "x", 0.0)),
              float(getattr(hero, "y", 0.0)), skill)
