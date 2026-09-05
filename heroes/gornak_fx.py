"""
heroes/gornak_fx.py — GORNAK COMBAT FX v5 (lapisan hidup, rewrite total)
=========================================================================

Lapisan "juicy" untuk Gornak Spellbreaker yang digambar DI LUAR sprite
cache: trail ayunan, proyektil mana, impact, skill lifecycle 4-fase,
partikel pooled, screen-shake + hit-stop. Renderer boss
(bosses/gornak_v5.py) tetap memegang pose & telegraph dunia; modul ini
HANYA membaca state — tidak pernah menulis angka gameplay.

Pakta arsitektur (docs/GORNAK_V5_REWRITE.md):
  * SATU sumber pose: ``_renderer().G._resolve_pose`` — jangkar bilah,
    spawn bolt, dan trail badan unit yang sama, bukan tebakan.
  * pooling penuh: Partikel/ImpactFX/SkillFX/Proyektil memakai free-list;
    TIDAK ada alokasi baru per frame selama pertempuran normal.
  * permukaan statis di-cache (glow, cincin, pelat rune, star sprite).
  * FX TIDAK PERNAH mengubah damage/ cooldown/ target — hanya visual +
    feel bus (hit-stop/shake) yang memang milik visual.
  * E=100 / R=180 px dunia: cincin telegraph milik RENDERER (canvas),
    modul ini menambah lapisan hidup dengan radius dunia yang sama
    (``WORLD_RADIUS`` dikali kompensasi ``_render_scale``).
  * basic attack TIDAK memicu impact FX (aturan repo: impact eksklusif
    skill) — ayunan memberi trail + gust; ``notify_melee_impact`` tetap
    tersedia untuk tooling.

Semua nama publik v3/v4 dipertahankan (director, attach/owns, tick,
notify_*, Particle, ParticleSystem, SwingTrail, ImpactFX, projectile
system, SkillFX, ring/glow surface, cache helpers) supaya
tools/test_gornak_v3_combat.py, tools/_audit_* dan overlay debug tidak
perlu berubah.
"""

import math

import pygame

#: Flag global — matikan untuk membandingkan renderer murni.
GORNAK_FX_ENABLED = True
#: Debug lane hero: hitbox, hurtbox, jangkauan, partikel, state.
DEBUG_CHARACTER = False

FIXED_DT = 1.0 / 60.0          # tick tanpa argumen = langkah 60 fps
BOLT_SPEED = 14.0              # px/frame ruang-layar (visual-only)

#: Jumlah maksimum partikel AKTIF. Di atas ini partikel lama tidak
#: dibuang — sistem memakai POOL tetap, jadi tidak ada alokasi baru.
MAX_PARTICLES = 170
MAX_PROJECTILES = 16
#: Titik riwayat bilah per sisi (trail); TETAP teralokasi — push hanya
#: menggeser isi, tidak pernah append saat pool penuh.
TRAIL_SAMPLES = 14
MAX_IMPACTS = 8
MAX_SKILLS = 4

WORLD_RADIUS = {"q": 44.0, "w": 30.0, "e": 100.0, "r": 180.0}
#: pengali skala lapisan hidup (mobile boleh mengecilkan; renderer punya
#: G._fx_scale sendiri untuk kanvasnya)
_fx_scale = 1.0
#: offset ground pada kanvas boss (sinkron _NS_gornak.GROUND_DY)
GROUND_Y = 54.0
#: frame sebelum akhir timer R saat singularitas LEPAS (meniru _bundle)
VOID_RELEASE_FROM = 24
SKILL_TOTAL = {"q": 0.78, "w": 0.52, "e": 1.16, "r": 1.72}

#: Sinkron dengan bosses/gornak_v5.py (loader malas, nilai cadangan sama).
try:
    from bosses.gornak_v5 import _NS_gornak as _GR
    SKILL_DUR = _GR.SKILL_DUR
except Exception:                                  # pragma: no cover
    _GR = None
    SKILL_DUR = {"q": 40, "w": 25, "e": 60, "r": 90}

#: Batas fase AYUNAN untuk lapisan hidup. Sama seperti renderer:
#: pita/trail boleh muncul sedikit lebih awal dari fase resmi.
ATTACK_PHASES = (
    ("ANTICIPATION", 0.00, 0.16),
    ("WINDUP",       0.16, 0.30),
    ("SWING",        0.30, 0.46),
    ("IMPACT",       0.46, 0.60),
    ("FOLLOW",       0.60, 0.74),
    ("IMPACT_HOLD",  0.74, 0.90),
    ("RECOVERY",     0.90, 1.00),
)

ANIM_PRIORITY = {
    "IDLE": 0, "WALK": 10, "RUN": 15, "VICTORY": 20, "CHARGE": 30,
    "CAST": 35, "ATTACK": 40, "SWING": 45, "SKILL": 50, "SPECIAL": 55,
    "HIT": 60, "HURT": 65, "DEATH": 100,
}


def attack_phase(p):
    """Nama fase ayunan untuk progres 0..1 (jalur live; lihat renderer)."""
    p = max(0.0, min(1.0, float(p)))
    for name, a, b in ATTACK_PHASES:
        if a <= p < b:
            return name
    return "RECOVERY"


# ═════════════════════════════════════════════════════════════════════
# PALET — SATU sumber: palet renderer. ``_sync_palette`` menyalin ulang
# tiap pergantian arena; angka di bawah = nilai renderer v5 (dijaga
# tools/test_gornak_v3_combat.py::test_palet_... dari drift).
# ═════════════════════════════════════════════════════════════════════
GORNAK_PALETTE = {
    # ramp utama karakter (IDENTITAS ANTI-MAGE: nilai cadangan = renderer
    # v5; saat import _sync_palette menyalin ulang dari sumbernya)
    "dark":      (24, 64, 128),
    "mid":       (56, 132, 208),
    "light":     (108, 190, 236),
    "highlight": (164, 222, 250),
    "body":      (122, 134, 152),
    "weapon":    (150, 214, 242),
    "outline":   (7, 6, 12),
    "shadow":    (0, 0, 0),
    "fx":        (208, 238, 255),
    # ramp efek (eksklusif lapisan hidup)
    "fx_darkest": (10, 14, 44),
    "fx_dark":    (12, 28, 68),
    "fx_mid":     (56, 132, 208),
    "fx_light":   (108, 190, 236),
    "fx_bright":  (164, 222, 250),
    "fx_hot":     (208, 238, 255),
    "fx_white":   (240, 251, 255),
    "steel_dark": (28, 44, 66),
    "steel_mid":  (88, 128, 168),
    "steel_edge": (150, 214, 242),
    "steel_hot":  (208, 242, 255),
    "brass":      (150, 124, 84),
    "brass_hot":  (206, 184, 140),
    "robe":       (34, 52, 92),
    "dust":       (118, 116, 128),
    "ash":        (84, 90, 106),
    "smoke":      (44, 52, 70),
}

#: kunci FX -> kunci palet renderer (satu-satunya jembatan yang sah)
_PALETTE_SYNC = {
    "dark":      "magic_dark",
    "mid":       "magic_mid",
    "light":     "magic_light",
    "highlight": "magic_hot",
    "fx":        "magic_shine",
    "fx_darkest": "magic_void",
    "fx_dark":   "magic_darkest",
    "fx_mid":    "magic_mid",
    "fx_light":  "magic_light",
    "fx_bright": "magic_hot",
    "fx_hot":    "magic_shine",
    "fx_white":  "magic_core",
    "body":      "skin_mid",
    "weapon":    "blade_light",
    "steel_dark": "blade_dark",
    "steel_mid": "blade_mid",
    "steel_edge": "blade_shine",
    "outline":   "armor_darkest",
    "shadow":    "shadow",
}
_PALETTE_SYNCED = False


def _renderer():
    """Muat renderer hidup sekali (bosses/level1 -> _NS_gornak)."""
    global _RENDERER
    if _RENDERER is None:
        from bosses.level1 import _NS_gornak
        _RENDERER = _NS_gornak
    return _RENDERER


_RENDERER = None


def _sync_palette():
    """Salin palet renderer ke palet FX (dipanggil tiap pergantian arena)."""
    global _PALETTE_SYNCED
    if _PALETTE_SYNCED:
        return
    _PALETTE_SYNCED = True
    try:
        G = _renderer()
    except Exception:
        return
    for dst, src in _PALETTE_SYNC.items():
        col = G.PALETTE.get(src)
        if col:
            GORNAK_PALETTE[dst] = tuple(col)
    P = GORNAK_PALETTE
    P["fx_white"] = P["fx_white"]


_sync_palette()
P = dict(GORNAK_PALETTE)     # alias cepat ala v3 (API lama dipakai test)


# ═════════════════════════════════════════════════════════════════════
# KUALITAS (mobile/perf) — anggaran partikel/glow/shake per perangkat.
# ═════════════════════════════════════════════════════════════════════
def _quality():
    try:
        from mobile.perf import Quality as Q
        return Q
    except Exception:                          # pragma: no cover
        return None


def _budget_particles(n):
    q = _quality()
    if q is None:
        return n
    return max(1, int(round(n * getattr(q, "particle_ratio", 1.0))))


def _glow_allowed():
    q = _quality()
    return True if q is None else bool(getattr(q, "glow_allowed", True))


def _shake_allowed():
    q = _quality()
    return True if q is None else bool(getattr(q, "shake_allowed", True))


# ═════════════════════════════════════════════════════════════════════
# PERMUKAAN STATIS — glow/ring/star di-cache; pool scratch tanpa alokasi
# ═════════════════════════════════════════════════════════════════════
_SURF_CACHE = {}
_SURF_CACHE_MAX = 384
_SCRATCH = []


def _scratch(size):
    """Pinjam surface SRCALPHA sized ``size`` (harus dikembalikan)."""
    for i, s in enumerate(_SCRATCH):
        if s.get_size() == size and not s.must_lock():
            return _SCRATCH.pop(i)
    return pygame.Surface(size, pygame.SRCALPHA)


def _give_back(s):
    if len(_SCRATCH) < 24 and s is not None:
        _SCRATCH.append(s)


def _blit_faded(surface, src, x, y, alpha, special=None):
    """Blit dengan alpha 0..255 TANPA menyalin permukaan."""
    if alpha <= 4:
        return
    if alpha >= 252 and special is None:
        surface.blit(src, (x, y))
        return
    old = src.get_alpha()
    src.set_alpha(max(4, min(255, int(alpha))))
    if special is None:
        surface.blit(src, (x, y))
    else:
        surface.blit(src, (x, y), special_flags=special)
    src.set_alpha(old)


def _cache_put(key, surf):
    _SURF_CACHE[key] = surf
    if len(_SURF_CACHE) > _SURF_CACHE_MAX:
        for k in list(_SURF_CACHE)[: _SURF_CACHE_MAX // 4]:
            _SURF_CACHE.pop(k, None)


def glow_surface(radius, color, power=1):
    """Halo radial halus PREMULTIPLIED — dibangun sekali, di-cache.

    ``BLEND_RGB_ADD`` MENGABAIKAN kanal alpha pada permukaan biasa, jadi
    gradien yang hanya menurun di alfa berubah jadi CAKRAM warna solid
    saat di-blit additive. Intensitas karena itu dikalikan ke RGB **dan**
    disalin ke alfa (kontrak satu rumah dengan ancient_apparition_fx).
    """
    key = ("glow", int(radius), tuple(color), round(float(power), 2))
    hit = _SURF_CACHE.get(key)
    if hit is not None:
        return hit
    r = max(1, int(radius))
    d = r * 2 + 2
    surf = pygame.Surface((d, d), pygame.SRCALPHA)
    cr, cg, cb = (max(0, min(255, int(v))) for v in color[:3])
    steps = max(3, r // 2)
    pw = max(0.05, min(2.0, float(power)))
    # gambar LUAR->DALAM: lingkaran besar redup dulu, kecil terang terakhir
    # => gradien radial center-bright, tetap premultiplied di tiap piksel.
    for i in range(steps - 1, -1, -1):
        t = i / float(steps - 1 if steps > 1 else 1)
        rr = max(0, int(r * (1.0 - t)))
        k = min(0.92, (0.10 + 0.62 * t) * pw)
        pygame.draw.circle(surf,
                           (int(cr * k), int(cg * k), int(cb * k),
                            min(255, int(255 * k))),
                           (r + 1, r + 1), rr)
    _cache_put(key, surf)
    return surf


def ring_surface(radius, thickness, color, alpha=255, dashed=0):
    """Cincin presisi pada radius PERSIS ``radius`` — cached.

    Dipakai cincin dunia E/R lapisan hidup; ``dashed`` = jumlah segmen
    (0 = penuh). Tebal digambar ke DALAM supaya tepi LUAR tetap
    di radius kontrak.
    """
    key = ("ring", int(radius), int(thickness), tuple(color), int(alpha),
           int(dashed))
    hit = _SURF_CACHE.get(key)
    if hit is not None:
        return hit
    d = int(radius) * 2 + 6
    surf = pygame.Surface((d, d), pygame.SRCALPHA)
    c = d // 2
    col = (*color[:3], _alpha(alpha))
    if dashed >= 2:
        seg = 180 // dashed
        n = max(3, int(radius * 0.22))
        for i in range(dashed):
            a0 = math.tau * i / dashed
            for j in range(n):
                t0 = a0 + math.tau * (j / n) * (seg / 180.0)
                t1 = a0 + math.tau * ((j + 1) / n) * (seg / 180.0)
                pygame.draw.aaline(
                    surf, col,
                    (c + math.cos(t0) * (radius - 0.5),
                     c + math.sin(t0) * (radius - 0.5)),
                    (c + math.cos(t1) * (radius - 0.5),
                     c + math.sin(t1) * (radius - 0.5)),
                    thickness >= 3)
    else:
        for t in range(int(thickness)):
            pygame.draw.circle(surf, col, (c, c), radius - t, 1)
    _cache_put(key, surf)
    return surf


def star_surface(size, color, core=None, spikes=6):
    """Bintang kilat kecil (cached) — pengganti draw garis tiap frame."""
    key = ("star", int(size), tuple(color), tuple(core) if core else None,
           spikes)
    hit = _SURF_CACHE.get(key)
    if hit is not None:
        return hit
    d = int(size) * 2 + 4
    surf = pygame.Surface((d, d), pygame.SRCALPHA)
    c = d // 2
    for k in range(spikes):
        ang = k * math.tau / spikes
        ln = size * (1.0 if k % 2 == 0 else 0.55)
        pygame.draw.line(surf, (*color, 235), (c, c),
                         (c + math.cos(ang) * ln,
                          c + math.sin(ang) * ln * 0.85),
                         2 if k % 2 == 0 else 1)
    if core:
        pygame.draw.circle(surf, (*core, 255), (c, c),
                           max(1, int(size * 0.3)))
    _cache_put(key, surf)
    return surf


def _alpha(v):
    return max(0, min(255, int(v)))


def clear_cache():
    """Kosongkan cache permukaan (dipanggil antar-arena oleh tooling)."""
    _SURF_CACHE.clear()
    _SCRATCH.clear()


def cache_size():
    return len(_SURF_CACHE)


# ═════════════════════════════════════════════════════════════════════
# BUS FEEL — hit-stop / screen-shake SATU bus dengan karakter lain.
# ═════════════════════════════════════════════════════════════════════
try:
    from heroes import combat_feel as _feel
    HITSTOP = _feel.HITSTOP
    SHAKE = _feel.SHAKE
except Exception:                              # pragma: no cover
    _feel = None

    class _FallbackFeel:                       # API kecil yang sama
        pass

    HITSTOP = SHAKE = _FallbackFeel()


def hit_stop(seconds):
    """Tahan SIMULASI (bukan render) beberapa detik — bus SHARED."""
    if _feel is not None:
        _feel.hit_stop(seconds)


def shake(strength, duration=0.22):
    if _feel is not None and _shake_allowed():
        _feel.shake(strength, duration)


def should_freeze_frame():
    """True = render ulang frame terakhir (freeze hit-stop, 1:1)."""
    if _feel is not None:
        return _feel.should_freeze_frame()
    return False


def _feel_dt():
    """Delta lapisan FX: melambat saat hit-stop (freeze terasa, bukan lag)."""
    if _feel is not None:
        v = _feel.fx_dt
        return float(v() if callable(v) else v)
    return FIXED_DT


# ═════════════════════════════════════════════════════════════════════
# JEMBATAN POSE — SATU sumber kebenaran bentuk badan.
# ═════════════════════════════════════════════════════════════════════
def pose_of(hero):
    """(action, phase, ap) yang sedang dipakai BADAN hero saat ini."""
    G = _renderer()
    try:
        return G._resolve_pose(hero, getattr(hero, "_moving_cached", False))
    except Exception:                          # pragma: no cover
        return "idle", 0.0, 0.0


def body_scale(hero):
    """Skala render unit di layar (jalur hero 0.40..1.02, boss 1.0)."""
    return max(0.12, min(1.0, float(getattr(hero, "_render_scale", 1.0)
                                    or 1.0)))


def _lift_of(G, hero):
    return int(getattr(G, "LIFT", 4))


def _ground_dy(hero, G=None):
    G = G or _renderer()
    return float(getattr(G, "GROUND_DY", 54)) * body_scale(hero)


def screen_point(hero, lx, ly, G=None):
    """Titik ruang LOKAL rig -> layar 1:1 (rumus rig, skala render)."""
    G = G or _renderer()
    rs = body_scale(hero)
    f = 1 if getattr(hero, "direction", 1) >= 0 else -1
    action, phase, ap = pose_of(hero)
    lean, root = G._rig_shift(action, phase, ap)
    lift = _lift_of(G, hero)
    k = float(getattr(G, "SCALE", 1.32)) * rs
    x = getattr(hero, "x", 0.0)
    y = getattr(hero, "y", 0.0)
    return (int(x + (lx * f + lean * f) * k),
            int(y - lift * rs + (ly + root) * k))


def blade_points(hero, x=None, y=None, back=False, G=None):
    """(grip, tip) cleaver/belati di layar — segaris dengan badan.

    ``x, y`` opsional: saat renderer memanggil dengan koordinat JANGKAR
    yang bukan hero.x/y (lane), FX ikut jangkar itu, bukan posisi dunia.
    """
    G = G or _renderer()
    rs = body_scale(hero)
    f = 1 if getattr(hero, "direction", 1) >= 0 else -1
    action, phase, ap = pose_of(hero)
    grip = (G._back_grip_local(action, ap, phase) if back else
            G._front_grip_local(action, ap, phase))
    L = G._blade_len(action, back)
    ang = G._blade_angle(phase, action, ap, back)
    lx = grip[0] + math.sin(ang) * L
    ly = grip[1] + math.cos(ang) * L
    lean, root = G._rig_shift(action, phase, ap)
    lift = _lift_of(G, hero)
    k = float(getattr(G, "SCALE", 1.32)) * rs
    ax = float(hero.x if x is None else x)
    ay = float(hero.y if y is None else y)
    sx = int(ax + (grip[0] * f + lean * f) * k)
    sy = int(ay - lift * rs + (grip[1] + root) * k)
    tx = int(ax + (lx * f + lean * f) * k)
    ty = int(ay - lift * rs + (ly + root) * k)
    return (sx, sy), (tx, ty)


# ═════════════════════════════════════════════════════════════════════
# PARTIKEL — pool tetap, tanpa alokasi per frame
# ═════════════════════════════════════════════════════════════════════
class Particle:
    """Satu partikel. Bidang lengkap sesuai master prompt:
    pos/vel/acc + spin + size + dua warna (fade antar ramp) + lapisan."""

    __slots__ = ("pos", "vel", "acc", "life", "max_life", "size",
                 "color", "color_end", "shape", "additive", "drag",
                 "gravity", "alpha", "spin", "rotation", "rotation_speed",
                 "layer", "twinkle", "active", "stretch")

    def __init__(self):
        self.pos = pygame.math.Vector2(0.0, 0.0)
        self.vel = pygame.math.Vector2(0.0, 0.0)
        self.acc = pygame.math.Vector2(0.0, 0.0)
        self.life = 0.0
        self.max_life = 0.4
        self.size = 2.0
        self.color = (255, 255, 255)
        self.color_end = None
        self.shape = "pixel"
        self.additive = True
        self.drag = 0.94
        self.gravity = 0.0
        self.alpha = 255
        self.spin = 0.0
        self.rotation = 0.0
        self.rotation_speed = 0.0
        self.layer = "front"
        self.twinkle = False
        self.stretch = 0.0
        self.active = False

    # alias v3: objeknya HARUS sama dengan self.pos/vel/acc (test
    # membandingkan dengan `is`), jadi ini getter list yang sama.
    @property
    def position(self):
        return self.pos

    @position.setter
    def position(self, v):
        self.pos.x, self.pos.y = float(v[0]), float(v[1])

    @property
    def velocity(self):
        return self.vel

    @velocity.setter
    def velocity(self, v):
        self.vel.x, self.vel.y = float(v[0]), float(v[1])

    @property
    def acceleration(self):
        return self.acc

    @acceleration.setter
    def acceleration(self, v):
        self.acc.x, self.acc.y = float(v[0]), float(v[1])

    def reset(self, x, y, vx, vy, life, size, color, **kw):
        self.pos.x, self.pos.y = float(x), float(y)
        self.vel.x, self.vel.y = float(vx), float(vy)
        self.acc.x, self.acc.y = kw.get("ax", 0.0), kw.get("ay", 0.0)
        self.life = self.max_life = max(0.02, float(life))
        self.size = size
        self.color = color[:3]
        self.color_end = kw.get("color_end")
        self.shape = kw.get("shape", "pixel")
        self.additive = bool(kw.get("additive", True))
        self.drag = kw.get("drag", 0.94)
        self.spin = kw.get("spin", 0.0)
        self.rotation = kw.get("rotation", 0.0)
        self.rotation_speed = kw.get("rotation_speed", 0.0)
        self.layer = kw.get("layer", "front")
        self.twinkle = bool(kw.get("twinkle"))
        self.stretch = kw.get("stretch", 0.0)
        self.gravity = kw.get("gravity", 0.0)
        self.alpha = kw.get("alpha", 255)
        self.active = True

    def spawn(self, x, y, vx, vy, life, size, color, **kw):
        """API lama: isi ulang partikel ini (dipakai test & tooling)."""
        self.reset(x, y, vx, vy, life, size, color, **kw)
        return self

    def update(self, dt):
        self.life -= dt
        if self.life <= 0:
            self.active = False
            return False
        g = self.gravity
        d = self.drag
        self.vel.x = (self.vel.x + self.acc.x * dt) * d
        self.vel.y = (self.vel.y + (self.acc.y + g) * dt) * d
        self.pos.x += self.vel.x * dt
        self.pos.y += self.vel.y * dt
        self.rotation += self.rotation_speed * dt
        return True

    def draw(self, surface):
        if not self.active:
            return
        t = self.life / self.max_life if self.max_life > 0 else 0.0
        a = 255 if t > 0.72 else _alpha(255 * (t / 0.72))
        if self.twinkle and int(self.life * 26) % 3 == 0:
            a = _alpha(a * 0.4)
        col = self.color
        if self.color_end is not None:
            k = 1.0 - t
            col = (int(col[0] + (self.color_end[0] - col[0]) * k),
                   int(col[1] + (self.color_end[1] - col[1]) * k),
                   int(col[2] + (self.color_end[2] - col[2]) * k))
        x, y = int(self.pos[0]), int(self.pos[1])
        s = max(1, int(round(self.size * (0.35 + 0.65 * t))))
        flags = pygame.BLEND_RGB_ADD if self.additive else None
        shp = self.shape
        if shp == "glow":
            spr = glow_surface(s + 2, col)
            _blit_faded(surface, spr, x - spr.get_width() // 2,
                        y - spr.get_height() // 2, a, flags)
        elif shp == "spark":
            spr = star_surface(s, col, P["fx_white"])
            _blit_faded(surface, spr, x - spr.get_width() // 2,
                        y - spr.get_height() // 2, a, flags)
        elif shp == "streak":
            vx, vy = self.vel
            ln = math.hypot(vx, vy) or 1.0
            ux, uy = vx / ln, vy / ln
            ln = min(14.0, 3.0 + ln * 0.28 + self.stretch * 10.0)
            pygame.draw.line(surface, (*col, a),
                             (x, y), (int(x - ux * ln), int(y - uy * ln)),
                             max(1, s // 2) if s > 2 else 1)
        elif shp == "shard":
            ang = self.rotation
            ca, sa = math.cos(ang), math.sin(ang)
            nx, ny = -sa, ca
            l2 = s * (0.9 + self.stretch * 0.5)
            pygame.draw.polygon(surface, (*col, a),
                                [(x + ca * l2, y + sa * l2),
                                 (x + nx * s * 0.55, y + ny * s * 0.55),
                                 (x - ca * l2 * 0.5, y - sa * l2 * 0.5),
                                 (x - nx * s * 0.55, y - ny * s * 0.55)])
        elif shp in ("dust", "smoke"):
            k = 1.0 - t
            rr = s * (1.0 + k * (1.8 if shp == "smoke" else 0.7))
            pygame.draw.circle(surface,
                               (*col, _alpha(a * (0.5 if shp == "smoke"
                                                  else 0.75))),
                               (x, y), max(1, int(rr)))
        else:                                  # "pixel" — satu titik tajam
            pygame.draw.rect(surface, (*col, a), (x, y, s, s))


class ParticleSystem:
    """Pool Partikel dengan cap keras + statistik drop (audit tooling)."""

    __slots__ = ("cap", "pool", "active", "dropped")

    def __init__(self, cap=MAX_PARTICLES):
        self.cap = max(1, min(MAX_PARTICLES, int(cap)))
        self.pool = [Particle() for _ in range(self.cap)]
        self.active = []
        self.dropped = 0

    def spawn(self, x, y, vx, vy, life, size, color, **kw):
        if self.pool:
            p = self.pool.pop()
        elif len(self.active) >= self.cap:
            self.dropped += 1
            return None
        else:
            p = Particle()
        p.reset(x, y, vx, vy, life, size, color, **kw)
        self.active.append(p)
        return p

    def burst(self, x, y, n, speed, color, **kw):
        n = _budget_particles(n) if kw.pop("budgeted", True) else n
        spread = kw.pop("spread", math.tau)
        base = kw.pop("dir", None)
        jitter = kw.pop("jitter", 0.3)
        v = kw.pop("inherit", None)
        life = kw.pop("life", 0.42)
        size = kw.pop("size", 2)
        out = 0
        for i in range(n):
            if base is None:
                ang = (i / float(n)) * spread + (spread / n) * 0.5 \
                    + jitter * ((i * 7919 % 97) / 97.0 - 0.5)
            else:
                ang = base + (i - n / 2.0) * (spread / max(1, n - 1))
            sp = speed * (0.55 + 0.7 * ((i * 104729 % 89) / 89.0))
            p = self.spawn(x, y, math.cos(ang) * sp + (v[0] if v else 0),
                           math.sin(ang) * sp + (v[1] if v else 0),
                           life * (0.65 + 0.7 * ((i * 48611 % 61) / 61.0)),
                           size, color, **kw)
            if p is not None:
                out += 1
        return out

    def stream(self, x, y, vx, vy, count, color, **kw):
        life = kw.pop("life", 0.3)
        size = kw.pop("size", 2)
        n = 0
        for i in range(count):
            j = (i * 2654435761) & 255
            if self.spawn(x + (j - 128) * 0.045,
                          y + (((i * 40503) & 255) - 128) * 0.045,
                          vx * (0.6 + (j & 31) / 60.0),
                          vy * (0.6 + ((i * 77) & 31) / 60.0),
                          life, size, color, **kw) is not None:
                n += 1
        return n

    def count(self):
        return len(self.active)

    def alive(self):
        return self.active

    def update(self, dt):
        act = self.active
        i = 0
        while i < len(act):
            p = act[i]
            if p.update(dt):
                i += 1
            else:
                act[i] = act[-1]
                act.pop()
                if len(self.pool) < self.cap:
                    self.pool.append(p)
        return len(act)

    def draw(self, surface, layer="front"):
        for p in self.active:
            if p.layer == layer and p.active:
                p.draw(surface)

    def clear(self):
        for p in self.active:
            p.active = False
            if len(self.pool) < self.cap:
                self.pool.append(p)
        self.active = []


# ═════════════════════════════════════════════════════════════════════
# TRAIL AYUNAN — histori bilah per frame (bukan lingkaran dekorasi)
# ═════════════════════════════════════════════════════════════════════
class SwingTrail:
    #: kontrak v3 (docs/GORNAK_V3_COMBAT_FX): sapuan maksimum histori +
    #: ambang dot untuk "bilah berbalik" (reset histori, bukan pita koyak)
    MAX_SWEEP = 1.95
    ARC_STEP = 0.16
    MAX_TURN_DOT = math.cos(2.55)
    """Pita bilah 60 fps: dua bilah, dua strip, sector-ribbon geser.

    ``points`` = [(grip(tip lama->baru))]; tiap entri [grip, tip] sepasang
    pygame.math.Vector2 + umur. ``samples`` = kapasitas (API lama: test
    membaca truthiness-nya).
    """

    __slots__ = ("samples", "points", "points_back", "life", "age",
                 "width_boost", "active_side")

    def __init__(self, samples=TRAIL_SAMPLES):
        self.samples = int(samples)
        self.points = []
        self.points_back = []
        self.life = 0.24
        self.age = 0.0
        self.width_boost = 0.0
        self.active_side = "front"

    @staticmethod
    def _ang_delta(a, b):
        """Selisih sudut terbungkus (-pi..pi] — helper busur pita."""
        d = (a - b) % math.tau
        return d - math.tau if d > math.pi else d

    def _jumped(self, strip):
        """Bilah berbalik / teleport > MAX_SWEEP dalam satu frame?
        (ganti pose) -> histori lama harus dibuang, bukan disambung."""
        if len(strip) < 2:
            return False
        p, q = strip[-2], strip[-1]
        a0 = math.atan2(p[1][1] - p[0][1], p[1][0] - p[0][0])
        a1 = math.atan2(q[1][1] - q[0][1], q[1][0] - q[0][0])
        return abs(self._ang_delta(a1, a0)) > self.MAX_SWEEP

    def push(self, grip, tip, grip_b=None, tip_b=None):
        e = [pygame.math.Vector2(grip[0], grip[1]),
             pygame.math.Vector2(tip[0], tip[1]), 0.0]
        self.points.append(e)
        if self._jumped(self.points):
            del self.points[:-1]
        if len(self.points) > self.samples:
            self.points.pop(0)
        if grip_b is not None and tip_b is not None:
            eb = [pygame.math.Vector2(grip_b[0], grip_b[1]),
                  pygame.math.Vector2(tip_b[0], tip_b[1]), 0.0]
            self.points_back.append(eb)
            if len(self.points_back) > self.samples:
                self.points_back.pop(0)
        self.age = 0.0

    def update(self, dt):
        self.age += dt
        dead = []
        for lst in (self.points, self.points_back):
            for e in lst:
                e[2] += dt
                if e[2] > self.life:
                    dead.append(e)
            for e in dead:
                lst.remove(e)
            dead = []
        return bool(self.points)

    def reset(self):
        self.points = []
        self.points_back = []
        self.age = 0.0

    # ------------------------------------------------------------------
    def _draw_strip(self, surface, strip, fade_all):
        if len(strip) < 2 or fade_all <= 0:
            return
        n = len(strip)
        for i in range(1, n):
            g0, t0, a0 = strip[i - 1]
            g1, t1, a1 = strip[i]
            life0 = 1.0 - a0 / self.life
            life1 = 1.0 - a1 / self.life
            if life0 <= 0 or life1 <= 0:
                continue
            # lebar bilah membesar di tengah sapuan (squash FX)
            wmid = (2.2 + 6.4 * math.sin(math.pi * min(1.0, i / (n - 1.0)))
                    + self.width_boost * 3.2)
            t = (life0 + life1) * 0.5
            alpha = _alpha(230 * t * t * fade_all)
            if alpha <= 6:
                continue
            # quad g0-t0 -> g1-t1 dengan tepi luar sedikit di-expande
            gx0, gy0, tx0, ty0 = g0.x, g0.y, t0.x, t0.y
            gx1, gy1, tx1, ty1 = g1.x, g1.y, t1.x, t1.y
            dx, dy = tx0 - gx0, ty0 - gy0
            ln = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / ln, dx / ln
            pts = [(gx0 + nx * 1.2, gy0 + ny * 1.2),
                   (tx0 + nx * wmid * 0.4, ty0 + ny * wmid * 0.4),
                   (tx1 + nx * wmid * 0.3, ty1 + ny * wmid * 0.3),
                   (gx1 - nx * 1.0, gy1 - ny * 1.0)]
            pygame.draw.polygon(surface, (*P["mid"], alpha), pts)
            pts2 = [(tx0 + nx * wmid * 0.4, ty0 + ny * wmid * 0.4),
                    (tx0 - nx * 0.8, ty0 - ny * 0.8),
                    (tx1 - nx * 0.8, ty1 - ny * 0.8),
                    (tx1 + nx * wmid * 0.3, ty1 + ny * wmid * 0.3)]
            pygame.draw.polygon(surface, (*P["fx_hot"], _alpha(alpha *
                                                                0.9)), pts2)

    def draw(self, surface):
        fade = 1.0
        self._draw_strip(surface, self.points, fade)
        self._draw_strip(surface, self.points_back, fade * 0.72)
        # ujung bilah berkilat (spark di tip terbaru)
        if self.points:
            g, t, a = self.points[-1]
            if a < 0.10:
                k = 1.0 - a / 0.10
                _blit_faded(surface, star_surface(5, P["fx_hot"],
                                                  P["fx_white"], 8),
                            int(t.x) - 7, int(t.y) - 7, _alpha(225 * k),
                            pygame.BLEND_RGB_ADD)


# ═════════════════════════════════════════════════════════════════════
# IMPACT — ledakan terarah; pool instance, tanpa alokasi per benturan
# ═════════════════════════════════════════════════════════════════════
class ImpactFX:
    """Benturan satu titik. ``kind`` menentukan bahasa visual:

    blade : tebasan baja — flash bintang + sabit berarah + serpihan
    mana  : proc Q — shard memancar + cincin dua lapis
    ward  : E — panulan: cincin menutup + kilat ungu
    void  : R — IMPLOSI: cincin MENGKONVERGEN, core putih sesaat
    """

    __slots__ = ("x", "y", "angle", "power", "crit", "kind", "ground",
                 "seed", "age", "duration", "active", "rings", "spokes",
                 "cracks")

    _POOL = []

    @classmethod
    def acquire(cls, *a, **kw):
        it = cls._POOL.pop() if cls._POOL else cls(*a, **kw)
        if kw or a:
            it.__init__(*a, **kw)
        it.active = True
        return it

    @classmethod
    def release(cls, it):
        if len(cls._POOL) < MAX_IMPACTS:
            cls._POOL.append(it)

    def __init__(self, x, y, angle=0.0, power=1.0, crit=False,
                 kind="blade", ground=False, seed=0):
        self.x, self.y = float(x), float(y)
        self.angle = float(angle)
        self.power = max(0.2, min(2.0, float(power)))
        self.crit = bool(crit)
        self.kind = kind
        self.ground = bool(ground)
        self.seed = int(seed)
        self.age = 0.0
        self.duration = 0.30 + 0.11 * min(2.0, self.power)
        self.active = True
        # precompute bentuk (deterministik; tidak digambar ulang rawac)
        self.rings = []
        self.spokes = []
        self.cracks = []
        n_sp = 7 if kind != "void" else 9
        for i in range(n_sp):
            h1 = ((self.seed * 73 + i * 131) % 97) / 97.0
            self.spokes.append((i * math.tau / n_sp + h1 * 0.85,
                                0.45 + h1))
        for i in range(4 if kind == "void" else 2):
            self.cracks.append(i * math.tau / 4 +
                               ((self.seed * 31 + i * 57) % 89) / 89.0)
        self.rings.append(0.0)

    def update(self, dt):
        self.age += dt
        if self.age >= self.duration:
            self.active = False
        return self.active

    def draw(self, surface, scale=1.0):
        if not self.active:
            return
        t = min(1.0, self.age / self.duration)
        k = 1.0 - t
        p = P
        pw = self.power
        base_r = (11 + 15 * pw) * scale
        cx, cy = int(self.x), int(self.y)
        add = pygame.BLEND_RGB_ADD
        if self.kind == "void":
            # IMPLOSI: cincin dari luar menutup + flash saat t>0.62
            r0 = base_r * 3.0 * (1.0 - t)
            _blit_faded(surface, ring_surface(max(3, int(r0)), 2,
                                              p["fx_bright"]),
                        cx - int(r0) - 3, cy - int(r0) - 3,
                        _alpha(210 * (0.35 + 0.65 * t)))
            _blit_faded(surface, ring_surface(max(3, int(r0 * 0.55)), 3,
                                              p["fx_hot"]),
                        cx - int(r0 * 0.55) - 3, cy - int(r0 * 0.55) - 3,
                        _alpha(235 * t))
            if t > 0.60:
                fk = (t - 0.60) / 0.40
                spr = glow_surface(int(base_r * 1.5), p["fx_hot"])
                _blit_faded(surface, spr, cx - spr.get_width() // 2,
                            cy - spr.get_height() // 2,
                            _alpha(235 * math.sin(math.pi * fk)), add)
                star = star_surface(int(8 + 22 * fk), p["fx_white"],
                                    p["fx_hot"], 8)
                _blit_faded(surface, star, cx - star.get_width() // 2,
                            cy - star.get_height() // 2,
                            _alpha(255 * (1 - fk)), add)
            for ang, w in self.spokes:
                ln = base_r * 2.4 * (1 - t) * (0.5 + w)
                a = _alpha(150 * k)
                if a > 8:
                    pygame.draw.line(surface, (*p["fx_light"], a),
                                     (cx + math.cos(ang) * ln,
                                      cy + math.sin(ang) * ln),
                                     (cx + math.cos(ang) * ln * 0.72,
                                      cy + math.sin(ang) * ln * 0.72), 2)
            return
        # flash awal
        if t < 0.30:
            fk = 1.0 - t / 0.30
            star = star_surface(int(6 + base_r * 1.15 * fk),
                                p["fx_white"] if self.crit else p["fx_hot"],
                                p["fx_hot"])
            _blit_faded(surface, star, cx - star.get_width() // 2,
                        cy - star.get_height() // 2, _alpha(245 * fk), add)
        # ring utama
        rr = base_r * (0.35 + 1.35 * t)
        _blit_faded(surface, ring_surface(max(3, int(rr)),
                                          2 + (1 if self.crit else 0),
                                          p["fx"]),
                    cx - int(rr) - 3, cy - int(rr) - 3, _alpha(200 * k))
        # sabit berarah (blade) atau cincin penuh (mana/ward)
        if self.kind == "blade":
            arc_a = self.angle - 1.15
            arc_b = self.angle + 1.15
            n = 12
            prev = None
            for i in range(n + 1):
                ang = arc_a + (arc_b - arc_a) * i / float(n)
                pt0 = (cx + math.cos(ang) * rr, cy + math.sin(ang) * rr)
                if prev is not None:
                    a = _alpha(225 * k)
                    pygame.draw.line(surface, (*p["fx_hot"], a), prev,
                                     pt0, max(2, int(2 + 3 * k * pw)))
                prev = pt0
        # shockwave gepeng (ground) — terasa memukul lantai
        if self.ground:
            gr = base_r * (0.6 + 2.1 * t)
            _blit_faded(surface, ring_surface(max(4, int(gr)), 2,
                                              p["mid"]),
                        cx - int(gr) - 3, cy - int(gr * 0.32) - 3,
                        _alpha(150 * k))
        # spoke + crack deterministik
        for ang, w in self.spokes:
            ln = base_r * (0.6 + 1.9 * t) * (0.55 + w)
            x1 = cx + math.cos(ang) * ln
            y1 = cy + math.sin(ang) * ln
            a = _alpha(215 * k)
            if a > 10:
                pygame.draw.line(surface, (*p["fx_light"], a),
                                 (cx + math.cos(ang) * base_r * 0.3,
                                  cy + math.sin(ang) * base_r * 0.3),
                                 (int(x1), int(y1)), 1)
        for ang in self.cracks:
            ln = base_r * 1.6 * t
            if ln > 3:
                pygame.draw.line(
                    surface, (*p["fx_dark"], _alpha(150 * k)),
                    (cx + math.cos(ang) * (base_r + ln * 0.35),
                     cy + math.sin(ang) * (base_r + ln * 0.35)),
                    (cx + math.cos(ang) * (base_r + ln),
                     cy + math.sin(ang) * (base_r + ln)), 1)


# ═════════════════════════════════════════════════════════════════════
# PROYEKTIL MANA — visual-only (damage milik engine; di sini 0)
# ═════════════════════════════════════════════════════════════════════
STATE_TRAVEL, STATE_IMPACT, STATE_DEAD = 0, 1, 2


def draw_mana_bolt(surface, px, py, angle, age, crit=False, radius=None,
                   spin_seed=0):
    """Satu bolt: core putih + mantel ungu + serpihan berputar + ekor."""
    p = P
    if radius is None:
        radius = 4.5 if not crit else 6.0
    r = radius * (1.0 + (0.18 if crit else 0.0))
    add = pygame.BLEND_RGB_ADD
    # ekor: 4 segmen memudar
    ca, sa = math.cos(angle), math.sin(angle)
    for i in range(4):
        d = r + 4 + i * 5.0
        a = _alpha(175 - i * 38)
        pygame.draw.line(surface, (p["mid"][0], p["mid"][1], p["mid"][2],
                                   a),
                         (int(px - ca * (d - 5)), int(py - sa * (d - 5))),
                         (int(px - ca * d), int(py - sa * d)),
                         max(1, 3 - i))
    spr = glow_surface(int(r + 5), p["fx_hot"] if not crit else
                       p["fx_white"])
    _blit_faded(surface, spr, int(px) - spr.get_width() // 2,
                int(py) - spr.get_height() // 2, 210, add)
    # inti lonjong mengikuti arah
    nx, ny = -sa, ca
    pts = [(px + ca * r * 1.9, py + sa * r * 1.9),
           (px + nx * r * 0.75, py + ny * r * 0.75),
           (px - ca * r * 1.15, py - sa * r * 1.15),
           (px - nx * r * 0.75, py - ny * r * 0.75)]
    pygame.draw.polygon(surface, (*p["fx"], 255), pts)
    pygame.draw.circle(surface, (*p["fx_white"], 255), (int(px), int(py)),
                       max(1, int(r * 0.5)))
    # dua shard mengorbit
    for o in range(2):
        ang = age * 9.0 + o * math.pi + spin_seed
        ox, oy = math.cos(ang) * (r + 3.5), math.sin(ang) * (r + 3.5) * .8
        pygame.draw.line(surface, (*p["fx_bright"], 225),
                         (int(px + ox), int(py + oy)),
                         (int(px + ox - ca * 3), int(py + oy - sa * 3)), 2)


class GornakProjectile:
    STATE_TRAVEL = STATE_TRAVEL
    STATE_IMPACT = STATE_IMPACT
    STATE_DEAD = STATE_DEAD

    __slots__ = ("position", "velocity", "speed", "damage", "lifetime",
                 "age", "target", "radius", "rotation", "rotation_speed",
                 "trail", "particles", "active", "state", "spawn_pos",
                 "hit_pos", "crit", "system", "spin_seed", "hit_radius")

    def __init__(self, system=None):
        self.system = system
        self.position = pygame.math.Vector2()
        self.velocity = pygame.math.Vector2()
        self.speed = BOLT_SPEED
        self.damage = 0                 # visual-only; engine yang memukul
        self.lifetime = 1.6
        self.age = 0.0
        self.target = None
        self.radius = 5.0
        self.hit_radius = 10.0
        self.rotation = 0.0
        self.rotation_speed = 6.0
        self.crit = False
        self.trail = []
        self.particles = None
        self.active = False
        self.state = STATE_TRAVEL
        self.spawn_pos = pygame.math.Vector2()
        self.hit_pos = pygame.math.Vector2()
        self.spin_seed = 0.0

    def launch(self, x, y, angle, target=None, speed=None, crit=False,
                spin_seed=None):
        self.position.update(x, y)
        self.spawn_pos.update(x, y)
        sp = float(speed) if speed else BOLT_SPEED
        self.velocity.update(math.cos(angle) * sp, math.sin(angle) * sp)
        self.speed = sp
        self.target = target
        self.crit = bool(crit)
        self.radius = 5.8 if crit else 4.6
        self.age = 0.0
        self.state = STATE_TRAVEL
        self.active = True
        self.trail = [(x, y, 0.0) for _ in range(6)]
        self.spin_seed = (self.position.x * 0.13 + self.position.y * 0.31
                          if spin_seed is None else float(spin_seed))
        return self

    def kill(self):
        """Ditembak jatuh / mengenai target -> transisi IMPACT."""
        if self.state == STATE_TRAVEL:
            self.state = STATE_IMPACT
            self.hit_pos.update(self.position.x, self.position.y)
            if self.system is not None:
                self.system.on_impact(self)

    def update(self, dt):
        if not self.active:
            return False
        self.age += dt
        if self.state == STATE_TRAVEL:
            if self.target is not None and getattr(self.target, "alive",
                                                   True):
                dx = self.target.x - self.position.x
                dy = self.target.y - self.position.y
                dist = math.hypot(dx, dy)
                if dist > 0.001:
                    steer = 5.2 * dt
                    vx, vy = self.velocity.x, self.velocity.y
                    self.velocity.x += (dx / dist * self.speed - vx) * steer
                    self.velocity.y += (dy / dist * self.speed - vy) * steer
            self.position += self.velocity * dt * 60.0
            self.rotation += self.rotation_speed * dt
            for i in range(len(self.trail) - 1, 0, -1):
                tx0, ty0, a0 = self.trail[i - 1]
                self.trail[i] = (tx0, ty0, self.trail[i][2])
            self.trail[0] = (self.position.x, self.position.y, 0.0)
            for i in range(1, len(self.trail)):
                ta = self.trail[i][2] + dt
                self.trail[i] = (self.trail[i][0], self.trail[i][1], ta)
            if self.particles is not None:
                self.particles.stream(
                    self.position.x - self.velocity.x * 0.03,
                    self.position.y - self.velocity.y * 0.03,
                    -self.velocity.x * 0.12, -self.velocity.y * 0.12,
                    _budget_particles(1), P["fx_light"], life=0.20,
                    size=2, shape="pixel", drag=0.9, additive=True)
            if self.target is not None:
                d = math.hypot(self.target.x - self.position.x,
                               self.target.y - self.position.y)
                if d <= self.hit_radius:
                    self.kill()
            elif self.age > self.lifetime:
                self.state = STATE_DEAD
                self.active = False
        elif self.state == STATE_IMPACT:
            if self.age > 0.42:
                self.state = STATE_DEAD
                self.active = False
        return self.active

    def draw(self, surface):
        if not self.active or self.state != STATE_TRAVEL:
            return
        ang = math.atan2(self.velocity.y, self.velocity.x)
        draw_mana_bolt(surface, self.position.x, self.position.y, ang,
                       self.age, self.crit, self.radius, self.spin_seed)

    def draw_impact(self, surface):
        if self.state != STATE_IMPACT:
            return
        t = min(1.0, (self.age) / 0.42)
        k = 1.0 - t
        cx, cy = int(self.hit_pos.x), int(self.hit_pos.y)
        rr = self.radius * (2.4 + 7.0 * t)
        _blit_faded(surface, ring_surface(max(3, int(rr)), 2, P["fx"]),
                    cx - int(rr) - 3, cy - int(rr) - 3, _alpha(220 * k))
        star = star_surface(int(5 + 14 * (1 - t)), P["fx_white"],
                            P["fx_hot"], 8)
        _blit_faded(surface, star, cx - star.get_width() // 2,
                    cy - star.get_height() // 2, _alpha(235 * k),
                    pygame.BLEND_RGB_ADD)


class ProjectileSystem:
    """Pool proyektil visual; ``on_impact`` untuk impact FX + hit-stop."""

    __slots__ = ("cap", "pool", "active", "on_impact", "particles",
                 "dropped")

    def __init__(self, cap=MAX_PROJECTILES, particles=None):
        self.cap = max(1, int(cap))
        self.particles = particles
        self.pool = [GornakProjectile(self) for _ in range(self.cap)]
        self.active = []
        self.dropped = 0
        self.on_impact = None

    def spawn(self, x, y, angle, target=None, speed=None, crit=False,
              spin_seed=None):
        pr = self.pool.pop() if self.pool else None
        if pr is None:
            self.dropped += 1 if len(self.active) >= self.cap else 0
            oldest = self.active[0] if self.active else None
            if oldest is not None:
                self.active.remove(oldest)
                pr = oldest
        pr.launch(x, y, angle, target, speed, crit, spin_seed)
        pr.particles = self.particles
        self.active.append(pr)
        return pr

    def list(self):
        """Proyektil AKTIF (objek). Alat debug/test mengakses field-nya
        langsung - jangan mengembalikkan tuple, kontrak lama begitu."""
        return self.active

    def count(self):
        return len(self.active)

    def clear(self):
        for p in self.active:
            p.active = False
            p.state = STATE_DEAD
            if len(self.pool) < self.cap and p not in self.pool:
                self.pool.append(p)
        self.active = []

    def update(self, dt):
        i = 0
        while i < len(self.active):
            pr = self.active[i]
            if pr.update(dt):
                i += 1
            else:
                self.active.pop(i)
                if len(self.pool) < self.cap:
                    self.pool.append(pr)
        return len(self.active)

    def draw(self, surface, layer="front"):
        for pr in self.active:
            pr.draw(surface)
            if layer == "front":
                pr.draw_impact(surface)


# ═════════════════════════════════════════════════════════════════════
# CINCIN DUNIA E/R — helper modul yang dipakai SkillFX (dan tools).
# Bentuk BUKAN pilar cahaya: selalu cincin datar di lantai, radius
# presisi = radius gameplay, via ring_surface (cache).
# ═════════════════════════════════════════════════════════════════════
def _draw_ground_ring(surface, x, y, r, kind, alpha, comp=1.0):
    if kind == "e":
        return _draw_e(surface, x, y, r, alpha, comp)
    return _draw_r(surface, x, y, r, alpha, comp)


def _draw_e(surface, x, y, r, alpha=255, comp=1.0):
    """Kubah E: ring_surface penuh + genangan dalam dua lapis."""
    rr = max(3, int(r))
    _blit_faded(surface, ring_surface(rr, 2, P["mid"]),
                int(x) - rr - 3, int(y) - int(rr * 0.32) - 3, alpha)
    _blit_faded(surface, glow_surface(max(4, rr // 3), P["fx_dark"]),
                int(x) - rr // 3 - 1, int(y) - rr // 6 - 1, alpha // 2)
    return rr


def _draw_r(surface, x, y, r, alpha=255, comp=1.0):
    """Cincin R di LANTAS (telegraph hisap): ring_surface dashed 10
    segmen — penanda 180 px dunia, bukan kolom cahaya penutup badan."""
    rr = max(3, int(r))
    _blit_faded(surface, ring_surface(rr, 3, P["mid"], alpha, dashed=10),
                int(x) - rr - 3, int(y) - int(rr * 0.32) - 3, alpha)
    inner = max(3, rr * 2 // 5)
    _blit_faded(surface, ring_surface(inner, 2, P["fx_light"], alpha,
                                      dashed=6),
                int(x) - inner - 3, int(y) - inner // 6 - 3,
                alpha * 3 // 4)
    return rr


# ═════════════════════════════════════════════════════════════════════
# SKILL FX — lifecycle 4 fase (charge -> release -> area -> impact ->
# fade) dengan panjang detik yang menjadwalkan ulang timer engine.
# ═════════════════════════════════════════════════════════════════════
class SkillFX:
    """Satu skill yang sedang hidup. BUKAN lingkaran transparan: tiap
    skill punya bahasa bentuk sendiri — Q konduksi, W kabut void,
    E kubah pemantul, R ruang hisap — dengan partikel dan lantai."""

    __slots__ = ("kind", "x", "y", "age", "dur", "radius", "aim",
                 "ground_on", "facing", "particles", "active",
                 "_released", "_impacted", "seed")

    #: (charge, release, area, impact, fade) dalam DETIK
    TIMELINE = {
        "q": (0.20, 0.10, 0.20, 0.12, 0.16),
        "w": (0.14, 0.20, 0.08, 0.04, 0.06),
        "e": (0.30, 0.34, 0.24, 0.14, 0.14),
        "r": (0.46, 0.20, 0.46, 0.22, 0.38),
    }
    POOL = []

    def __init__(self, kind, x, y, particles=None, radius=0.0, aim=0.0,
                 ground=True, facing=1):
        self.kind = kind if kind in self.TIMELINE else "q"
        self.x, self.y = float(x), float(y)
        self.particles = particles
        self.radius = float(radius) or WORLD_RADIUS.get(self.kind, 40.0)
        self.aim = float(aim)
        self.ground_on = bool(ground)
        self.facing = 1 if facing >= 0 else -1
        t0, t1, t2, t3, t4 = self.TIMELINE[self.kind]
        self.dur = t0 + t1 + t2 + t3 + t4
        self.age = 0.0
        self.active = True
        self._released = False
        self._impacted = False
        self.seed = int(abs(x) * 13 + abs(y) * 29) % 997

    # ── pool (aturan perf: instance didaur-ulang, bukan baru) ───────
    @classmethod
    def acquire(cls, *a, **kw):
        s = cls.POOL.pop() if cls.POOL else cls("q", 0.0, 0.0)
        s.__init__(*a, **kw)
        return s

    @classmethod
    def release(cls, s):
        if len(cls.POOL) < MAX_SKILLS * 2:
            cls.POOL.append(s)

    # ── fase ─────────────────────────────────────────────────────────
    def phase(self):
        t = self.age
        ch, rel, area, imp, fade = self.TIMELINE[self.kind]
        if t < ch:
            return "charge", t / ch
        t -= ch
        if t < rel:
            return "release", t / rel
        t -= rel
        if t < area:
            return "area", t / area
        t -= area
        if t < imp:
            return "impact", t / imp
        t -= imp
        return "fade", max(0.0, min(1.0, t / fade))

    @property
    def progress(self):
        return max(0.0, min(1.0, self.age / self.dur))

    def ground_ring_radius(self, scale=1.0):
        """Radius cincin lantai; BERHENTI PERSIS di radius gameplay saat
        fase area (kontrak telegraph: 100/180 px dunia)."""
        ph, t = self.phase()
        grow = {"charge": 0.10 + 0.22 * t,
                "release": 0.36 + 0.40 * t,
                "area": 0.86 + 0.14 * t,
                "impact": 1.0,
                "fade": 1.0}[ph]
        return self.radius * grow * scale

    def update(self, dt):
        self.age += dt
        ph, t = self.phase()
        ps = self.particles
        k = self.kind
        if ps is not None:
            if k == "q" and ph == "charge":
                if int(self.age * 60) % 3 == 0:
                    for i in range(_budget_particles(2)):
                        ang = self.aim + math.pi + (i - 0.5) * 1.1
                        d = 26.0 + 26.0 * t
                        ps.spawn(self.x + math.cos(ang) * d,
                                 self.y + math.sin(ang) * d * 0.8,
                                 -math.cos(ang) * 120.0,
                                 -math.sin(ang) * 90.0,
                                 0.22, 2, P["fx_light"], shape="shard",
                                 rotation=ang, layer="back", drag=0.98)
            elif k == "w" and ph in ("charge", "release"):
                if int(self.age * 60) % 2 == 0:
                    ps.burst(self.x, self.y - 6, 1, 26.0, P["smoke"],
                             life=0.34, size=3, shape="smoke",
                             gravity=-18.0, drag=0.96, layer="back")
            elif k == "e" and ph == "area":
                if int(self.age * 60) % 4 == 0:
                    a = self.age * 3.1 + (self.seed % 7)
                    ps.spawn(self.x + math.cos(a) * 30 * self.facing,
                             self.y - 4 + math.sin(a) * 22,
                             -math.sin(a) * 34.0, math.cos(a) * 24.0,
                             0.3, 2, P["fx_bright"], shape="pixel")
            elif k == "r" and ph == "area":
                if int(self.age * 60) % 2 == 0:
                    for i in range(_budget_particles(2)):
                        a = (self.seed + i * 91 +
                             int(self.age * 60) * 7) % 628 / 100.0
                        d = self.radius * 0.72
                        ps.spawn(self.x + math.cos(a) * d,
                                 self.y + math.sin(a) * d * 0.5,
                                 -math.cos(a) * 190.0,
                                 -math.sin(a) * 130.0,
                                 0.30, 2, P["fx_light"], shape="streak",
                                 drag=0.99, layer="back")
            if ph == "impact" and not self._impacted:
                self._impacted = True
                self._on_impact_burst(ps)
        if self.age >= self.dur:
            self.active = False
        return self.active

    def _on_impact_burst(self, ps):
        k = self.kind
        if k == "q":
            ps.burst(self.x + math.cos(self.aim) * 40,
                     self.y + math.sin(self.aim) * 34, 7, 150.0,
                     P["fx"], life=0.34, size=2, shape="spark")
        elif k == "w":
            ps.burst(self.x, self.y - 8, 9, 120.0, P["fx_bright"],
                     life=0.30, size=2, shape="shard",
                     color_end=P["fx_dark"])
        elif k == "e":
            for i in range(_budget_particles(10)):
                a = i * math.tau / 10 + 0.3
                ps.spawn(self.x + math.cos(a) * 34,
                         self.y - 4 + math.sin(a) * 30,
                         math.cos(a) * 60.0, math.sin(a) * 40.0 - 40.0,
                         0.42, 2, P["fx_hot"], shape="shard",
                         gravity=140.0, rotation=a, drag=0.97)
        else:
            ps.burst(self.x, self.y - 6, 18, 220.0, P["fx_hot"],
                     life=0.5, size=3, shape="shard", spin=9.0,
                     color_end=P["fx_darkest"], gravity=60.0)

    # ── LANTAI ────────────────────────────────────────────────────────
    def draw_ground(self, surface, comp=1.0, ground_dy=54.0):
        if not self.ground_on:
            return
        ph, t = self.phase()
        gy = self.y + ground_dy * comp
        r = self.ground_ring_radius(comp)
        p = P
        if ph == "fade":
            fa = 1 - t
        elif ph == "charge":
            fa = 0.30 + 0.7 * t
        else:
            fa = 1.0
        a = _alpha(200 * fa * (0.4 if ph == "impact" else 1.0))
        if a <= 4:
            return
        if self.kind in ("e", "r"):
            # cincin dunia: presisi berhenti di radius gameplay
            rr = _draw_ground_ring(surface, self.x, gy, r, self.kind, a,
                                   comp)
            _blit_faded(surface, glow_surface(max(4, int(rr * 0.42)),
                                             p["fx_dark"]),
                        int(self.x) - rr * 42 // 100 - 1,
                        int(gy) - rr * 21 // 100 - 1, a // 2)
            if ph in ("area", "impact"):
                for i in range(6):
                    hh = ((self.seed + i * 337) % 97) / 97.0
                    ang = i * math.tau / 6 + hh
                    ln = r * (0.25 + 0.45 * (t if ph == "area" else 1))
                    x0 = self.x + math.cos(ang) * ln * 0.3
                    y0 = gy + math.sin(ang) * ln * 0.1
                    x1 = self.x + math.cos(ang) * ln
                    y1 = gy + math.sin(ang) * ln * 0.32
                    pygame.draw.line(surface, (*p["fx_light"], a // 2 + 40),
                                     (int(x0), int(y0)), (int(x1),
                                                          int(y1)), 1)
                    pygame.draw.line(surface, (*p["fx"], a // 2),
                                     (int(x1), int(y1)),
                                     (int(x1 + math.cos(ang) * 7),
                                      int(y1 + math.sin(ang) * 2.5)), 1)
        else:
            # Q/W: genangan kecil di kaki — penanda, bukan pengalih
            rr = max(4, int(r * (0.34 if self.kind == "q" else 0.5)))
            pygame.draw.ellipse(surface, (*p["fx_dark"], a // 2),
                                (int(self.x) - rr, int(gy) - rr // 3,
                                 rr * 2, max(2, rr // 2)))
            _blit_faded(surface, ring_surface(max(3, rr), 2, p["mid"]),
                        int(self.x) - rr - 3, int(gy) - rr // 4 - 3, a)

    # ── DEPAN ─────────────────────────────────────────────────────────
    def draw_front(self, surface, comp=1.0):
        ph, t = self.phase()
        p = P
        k = self.kind
        x, y = self.x, self.y
        add = pygame.BLEND_RGB_ADD
        if k == "q":
            if ph == "charge":
                rr = int(16 * (1 - t * 0.55) * comp)
                _blit_faded(surface, glow_surface(max(4, rr), p["mid"]),
                            int(x) - rr * 2, int(y) - 20 - rr * 2,
                            _alpha(140 + 100 * t), add)
            if ph in ("release", "area") and t < 0.7:
                for i in range(3):
                    rr = int((8 + 26 * t + i * 9) * comp)
                    _blit_faded(surface, ring_surface(max(3, rr), 1,
                                                      p["fx"]),
                                int(x) - rr - 3, int(y - 16) - rr - 3,
                                _alpha(190 - i * 46))
        elif k == "w":
            fa = {"charge": t, "release": 1.0, "area": 1.0 - t,
                  "impact": 0.4, "fade": 0.0}[ph]
            if fa > 0.02:
                for i in range(5):
                    hh = ((self.seed + i * 91) % 61) / 61.0
                    sx = x + (hh - 0.5) * 34 * comp
                    sy = y - 26 + i * 10
                    pygame.draw.line(surface,
                                     (*p["fx_dark"],
                                      _alpha(235 * fa * (0.5 + 0.5 * hh))),
                                     (int(sx), int(sy)),
                                     (int(sx + self.facing * -10),
                                      int(sy + 7)), 2)
                if ph == "release":
                    spr = glow_surface(int(20 * comp) + 4, p["mid"])
                    _blit_faded(surface, spr, int(x) - spr.get_width() // 2,
                                int(y - 10) - spr.get_height() // 2, 120,
                                add)
        elif k == "e":
            # kubah heksagon yang MENUTUP lalu MELEDAK keluar
            prog = {"charge": 1.0 - 0.5 * t, "release": 0.5 - 0.28 * t,
                    "area": 0.22, "impact": 0.2, "fade": 0.2}[ph]
            rr = max(10.0, 66.0 * prog) * comp
            fa = 1.0 if ph != "fade" else (1 - t)
            pts = []
            for i in range(7):
                ang = i * math.tau / 6 - math.pi / 2 + self.age * 0.9
                pts.append((x + math.cos(ang) * rr * 1.15,
                            y - 6 + math.sin(ang) * rr * 0.94))
            for i in range(6):
                al = _alpha(235 * fa)
                pygame.draw.line(surface, (*p["fx_hot"], al), pts[i],
                                 pts[i + 1],
                                 2 if ph in ("release", "area") else 1)
            if ph == "impact":
                star = star_surface(int(16 * comp) + 6, p["fx_white"],
                                    p["fx_hot"], 6)
                _blit_faded(surface, star, int(x) - star.get_width() // 2,
                            int(y - 8) - star.get_height() // 2,
                            _alpha(240 * (1 - t)), add)
        elif k == "r":
            # ruang hisap: lantai menghitam (cakram gepeng) + cincin
            # konvergen + core putih — BUKAN pilar vertikal (era v3:
            # slab gelap 120px menutupi badan & dibaca "berantakan").
            rr = max(8, int(self.radius * (0.9 - 0.72 * min(
                1.0, t + (0.34 if ph == "area" else 0.0))))) * comp
            gy = y + 54 * comp
            if ph in ("charge", "area"):
                a0 = 132 if ph == "area" else 96
                for i, (fw, fh, ka) in enumerate(((0.58, 0.17, 1.0),
                                                   (0.36, 0.11, 0.85),
                                                   (0.18, 0.06, 1.0))):
                    w = rr * fw * 2
                    h = max(5.0, rr * fh * 2)
                    pygame.draw.ellipse(
                        surface, (*p["fx_dark"], _alpha(a0 * ka)),
                        (int(x - w / 2), int(gy - h / 2 + i * 2 * comp),
                         int(w), int(h)))
                    pygame.draw.ellipse(
                        surface, (*p["fx_bright"], _alpha(a0 * 0.35)),
                        (int(x - w / 2), int(gy - h / 2 + i * 2 * comp),
                         int(w), int(h)), 1)
            if ph in ("area", "impact"):
                n = 3
                for i in range(n):
                    k0 = (self.age * 1.9 + i / n) % 1.0
                    r0 = int(rr * (1.0 - 0.75 * k0))
                    if r0 >= 4:
                        _blit_faded(surface, ring_surface(r0, 2,
                                                          p["fx_bright"]),
                                    int(x) - r0 - 3, int(y - 4) - r0 - 3,
                                    _alpha(200 * (0.3 + 0.7 * k0)))
                core = int((5 + 11 * min(
                    1.0, t + (0.5 if ph == "impact" else 0))) * comp) + 3
                _blit_faded(surface, glow_surface(core, p["fx_hot"]),
                            int(x) - core, int(y - 6) - core,
                            210, add)
                pygame.draw.circle(surface, (*p["fx_white"], 225),
                                   (int(x), int(y - 6)), max(2, core // 4))
            if ph == "fade":
                # gelombang kejut MELEBAR keluar
                rr2 = int(rr * (1 + 3.2 * t))
                _blit_faded(surface, ring_surface(max(4, rr2), 2, p["fx"]),
                            int(x) - rr2 - 3, int(y) - rr2 // 3 - 3,
                            _alpha(220 * (1 - t)))
                r3 = rr2 * 2 // 3
                _blit_faded(surface, ring_surface(max(3, r3), 3,
                                                 p["fx_white"]),
                            int(x) - r3 - 3, int(y) - r3 // 4 - 3,
                            _alpha(235 * (1 - t)))


# ═════════════════════════════════════════════════════════════════════
# DIREKTUR FX (satu per hero)
# ═════════════════════════════════════════════════════════════════════
class GornakFXDirector:
    """Pusat orkestrasi satu Gornak: membaca state hero per frame,
    memicu event feel, dan memelihara trail/particle/projectile/skill.

    Callback opsional (kontrak v3, dipakai _core/Game):
      on_cast(hero, skill) / on_blink(hero, x, y) /
      on_impact(hero, x, y, damage, crit) / on_swing_start(hero, x, y) /
      on_death(hero, x, y)
    """

    def __init__(self, hero):
        self.hero = hero
        self.particles = ParticleSystem(MAX_PARTICLES)
        self.projectiles = ProjectileSystem(MAX_PROJECTILES, self.particles)
        self.projectiles.on_impact = self._projectile_impact
        self.trail = SwingTrail(TRAIL_SAMPLES)
        self.impacts = []
        self.skills = []
        self.state = "IDLE"
        self.anim_phase = 0.0
        self.time = 0.0
        self.void_screen = None
        self._blink_seen = False
        self._void_fired = False
        self._skill_seen = None
        self._swing_phase = None
        self._trail_boost = 0.0
        self._death_done = False
        self._last_cast = None

    # ── transformasi ──────────────────────────────────────────────────
    def screen(self, x=None, y=None):
        """Titik dunia -> layar + skala feel (hero lane: identity)."""
        h = self.hero
        sx = h.x if x is None else x
        sy = h.y if y is None else y
        return sx, sy, body_scale(h)

    # ── event ─────────────────────────────────────────────────────────
    def emit_cast(self, x, y, skill, aim=None):
        """Mulai SkillFX (dipanggil watcher engine ATAU tooling)."""
        if skill not in SKILL_TOTAL:
            return
        h = self.hero
        facing = 1 if getattr(h, "direction", 1) >= 0 else -1
        if aim is None:
            tgt = getattr(h, "target", None)
            if tgt is not None and getattr(tgt, "alive", True):
                aim = math.atan2(tgt.y - y, tgt.x - x)
            else:
                aim = 0.0 if facing >= 0 else math.pi
        if len(self.skills) >= MAX_SKILLS:
            SkillFX.release(self.skills.pop(0))
        self.skills.append(SkillFX.acquire(
            skill, x, y, particles=self.particles,
            radius=WORLD_RADIUS.get(skill, 40.0), aim=aim,
            ground=True, facing=facing))
        self._last_cast = skill
        p = P
        if skill == "q":
            # bolt ditembakkan dari ujung bilah begitu konduksi lepas
            self.spawn_mana_break(x, y)
            _feel.shake(1.6, 0.10, forward_to_camera=False)
        elif skill == "w":
            self.particles.burst(x, y, 8, 90.0, p["smoke"], life=0.32,
                                 size=3, shape="smoke", gravity=-30.0,
                                 layer="back")
        elif skill == "e":
            _feel.hit_stop(0.028)
            self.particles.burst(x, y + 4, 10, 120.0, p["fx_bright"],
                                 life=0.36, size=2, shape="shard",
                                 gravity=140.0, upward=0.5)
        elif skill == "r":
            _feel.shake(3.2, 0.30, forward_to_camera=False)

    def spawn_mana_break(self, x, y):
        """Bolt visual ONLY: damage tetap milik hero_skills (instant)."""
        h = self.hero
        gp, tip = blade_points(h, x, y, False)
        tgt = getattr(h, "target", None)
        if tgt is not None and getattr(tgt, "alive", True):
            aim = math.atan2(tgt.y - tip[1], tgt.x - tip[0])
        else:
            aim = 0.0 if getattr(h, "direction", 1) >= 0 else math.pi
        crit = bool(getattr(h, "crit", False))
        pr = self.projectiles.spawn(tip[0], tip[1], aim, crit=crit,
                                    target=tgt if (tgt is not None and
                                                   getattr(tgt, "alive",
                                                           True)) else None)
        self.particles.burst(tip[0], tip[1], 5, 80.0, P["fx"],
                             life=0.22, size=2, dir=aim, spread=1.1,
                             shape="spark")
        return pr

    def emit_blink(self, x, y, old_x, old_y):
        p = P
        dx, dy = x - old_x, y - old_y
        ln = math.hypot(dx, dy) or 1.0
        ang = math.atan2(dy, dx)
        # burst di TITIK ASAL (kontrak test: <= 26 px dari old position)
        self.particles.burst(old_x, old_y, 8, 150.0, p["fx_light"],
                             life=0.30, size=2, shape="shard", dir=ang,
                             spread=2.6)
        self.particles.burst(old_x, old_y, 4, 40.0, p["smoke"], life=0.4,
                             size=3, shape="smoke", gravity=-20.0,
                             layer="back")
        for i in range(_budget_particles(5)):
            tt = (i + 0.5) / 5.0
            self.particles.spawn(old_x + dx * tt, old_y + dy * tt -
                                 8.0 * math.sin(math.pi * tt),
                                 math.cos(ang) * 30.0, -24.0,
                                 0.22 + 0.05 * i, 2, p["fx_bright"],
                                 shape="streak", stretch=1.8, twinkle=True)
        self.emit_impact(x, y, ang + math.pi, 0.7, False, kind="void")
        _feel.shake(2.4, 0.14, forward_to_camera=False)

    def emit_impact(self, x, y, angle=0.0, power=1.0, crit=False,
                    kind="blade", ground=False):
        if len(self.impacts) >= MAX_IMPACTS:
            ImpactFX.release(self.impacts.pop(0))
        self.impacts.append(ImpactFX.acquire(x, y, angle, power, crit,
                                             kind))
        n = _budget_particles(int(6 + 9 * min(1.5, power)))
        col = (P["fx_white"] if kind == "void" else
               P["fx_hot"] if kind == "mana" else P["steel_hot"])
        self.particles.burst(x, y, n, 130.0 * min(1.4, power), col,
                             life=0.30, size=2, dir=angle, spread=2.2,
                             shape="shard", stretch=1.4,
                             color_end=P["fx_dark"] if kind != "blade"
                             else P["dark"])

    def _projectile_impact(self, pr):
        ang = pr.rotation
        self.emit_impact(pr.hit_pos[0], pr.hit_pos[1], ang, 0.9, pr.crit,
                         kind="mana")
        _feel.hit_stop(0.024)
        _feel.shake(2.0, 0.10, forward_to_camera=False)

    def emit_swing_start(self, x, y, angle=0.0):
        """UAP angin di awal ayunan — BUKAN impact (hitbox engine
        yang memutuskan damage)."""
        p = P
        self.particles.burst(x + math.cos(angle) * 22, y - 6, 5, 90.0,
                             p["fx_bright"], life=0.16, size=1,
                             dir=angle, spread=1.0, shape="streak",
                             stretch=2.2, drag=0.86)

    def emit_void_release(self, x, y):
        """R melepas singularitas di titik pelepasan (kontrak engine)."""
        self.void_screen = (x, y, max(40, int(WORLD_RADIUS["r"])))
        self.emit_impact(x, y, 0.0, 1.5, True, kind="void", ground=True)
        self.particles.burst(x, y, _budget_particles(16), 210.0,
                             P["fx"], life=0.44, size=3, shape="shard",
                             gravity=60.0, color_end=P["fx_darkest"])
        _feel.shake(5.0, 0.28, forward_to_camera=False)
        _feel.hit_stop(0.045)

    def emit_death(self, x, y):
        if self._death_done:
            return
        self._death_done = True
        p = P
        self.particles.burst(x, y - 10, _budget_particles(22), 200.0,
                             p["fx_bright"], life=0.62, size=3,
                             shape="shard", gravity=160.0,
                             color_end=p["fx_dark"], spin=8.0)
        self.particles.burst(x, y - 26, _budget_particles(10), 120.0,
                             p["ember"], life=0.8, size=2, shape="ember",
                             gravity=-60.0, upward=1.2)
        self.emit_impact(x, y, 0.0, 1.5, True, kind="void")
        self.emit_impact(x, y - 18, math.pi / 2, 1.2, False, kind="void")
        _feel.shake(7.0, 0.40, forward_to_camera=False)
        _feel.hit_stop(0.06)

    # ── update per frame ──────────────────────────────────────────────
    def update(self, dt, x=None, y=None):
        if dt <= 0:
            dt = 1e-4
        h = self.hero
        if x is None:
            x = h.x
        if y is None:
            y = h.y
        self.anim_phase += dt
        self.time += dt

        # 1) event engine: cast / blink / void-release / death
        self._watch_engine(dt, x, y)

        # 2) ayunan + trail
        self._watch_swing(dt, x, y)

        # 3) decay
        self.particles.update(dt)
        self.projectiles.update(dt)
        self.trail.update(dt)
        if self._trail_boost > 0.0:
            self._trail_boost = max(0.0, self._trail_boost - dt * 3.2)
        live = []
        for s in self.impacts:
            s.update(dt)
            if s.active:
                live.append(s)
        if len(live) != len(self.impacts):
            for s in self.impacts:
                if not s.active:
                    ImpactFX.release(s)
        self.impacts = live
        live = []
        for s in self.skills:
            s.update(dt)
            if s.active:
                live.append(s)
        for s in self.skills:
            if not s.active:
                SkillFX.release(s)
        self.skills = live
        self._sync_state()

    def _watch_engine(self, dt, x, y):
        h = self.hero
        alive = getattr(h, "alive", True)
        if not alive:
            self.emit_death(x, y)
            return
        self._death_done = False
        skill = getattr(h, "active_skill", None)
        timer = getattr(h, "active_skill_timer", 0)
        if skill != self._skill_seen:
            if skill:
                self.emit_cast(x, y, skill)
                self._blink_seen = False
                self._void_fired = False
            self._skill_seen = skill
        if skill == "w" and getattr(h, "blink_from_x", None) \
                and not self._blink_seen:
            ox, oy = h.blink_from_x, getattr(h, "blink_from_y", y)
            # hanya saat benar-benar sudah melompat (jarak terlihat)
            if abs(x - ox) + abs(y - oy) > 4.0:
                self._blink_seen = True
                self.emit_blink(x, y, ox, oy)
        elif not getattr(h, "blink_from_x", None):
            self._blink_seen = False
        if skill == "r" and not self._void_fired:
            dur = max(1, SKILL_DUR.get("r", 90))
            void_x = getattr(h, "mana_void_x", None)
            if void_x and 0 < timer <= dur - VOID_RELEASE_FROM:
                self._void_fired = True
                self.emit_void_release(void_x,
                                     getattr(h, "mana_void_y", y))
            elif void_x and 0 < timer <= 0.6 * dur:
                self._void_fired = True
                self.emit_void_release(void_x,
                                     getattr(h, "mana_void_y", y))
        if not skill:
            self._void_fired = False
            if not getattr(h, "mana_void_x", None):
                self.void_screen = None

    def _watch_swing(self, dt, x, y):
        h = self.hero
        active = bool(getattr(h, "_gnk_attack_active", False))
        if not active:
            if self._swing_phase is not None:
                self.trail.reset()
            self._swing_phase = None
            return
        # prioritas 1: fase yang DIHASILKAN controller (_gnk_attack_phase);
        # test/tools boleh mengisinya tanpa menyentuh timer engine.
        phase = getattr(h, "_gnk_attack_phase", None) or ""
        raw = float(getattr(h, "_gnk_attack_progress", 0.0) or 0.0)
        if not phase or phase == "NONE":
            phase = attack_phase(max(0.0, min(1.0, raw)))
        if phase != self._swing_phase:
            self._swing_phase = phase
            if phase == "ANTICIPATION":
                gp, tp = blade_points(h, x, y, False)
                self.emit_swing_start(
                    x, y, math.atan2(tp[1] - gp[1], tp[0] - gp[0]))
                self.trail.reset()
            elif phase == "SWING":
                self._trail_boost = 1.0
            elif phase == "IMPACT":
                # tumbukan tebasan bukan urusan lapisan FX (engine yang
                # memutuskan hitbox); di sini: debu tanah + gust pendek
                self.particles.burst(x, y + 6.0, 4, 55.0, P["dust"],
                                      life=0.26, size=2, shape="dust",
                                      gravity=40.0, dir=0.0,
                                      spread=math.pi, layer="back")
        if phase in ("SWING", "IMPACT", "FOLLOW", "IMPACT_HOLD"):
            g0, t0 = blade_points(h, x, y, False)
            g1, t1 = blade_points(h, x, y, True)
            self.trail.push(g0, t0, g1, t1)

    def _sync_state(self):
        h = self.hero
        if not getattr(h, "alive", True):
            self.state = "DEATH"
            return
        skill = getattr(h, "active_skill", None)
        timer = getattr(h, "active_skill_timer", 0)
        if skill and timer > 0:
            dur = max(1, SKILL_DUR[skill])
            raw = 1.0 - timer / float(dur)
            ph = (attack_phase(raw) if skill == "q" else
                  "ANTICIPATION" if raw < 0.28 else
                  "IMPACT" if raw < 0.62 else "FOLLOW")
            self.state = "%s:%s" % (skill.upper(), ph)
            return
        if getattr(h, "hurt_flash_timer", 0) > 0:
            self.state = "HURT"
            return
        if getattr(h, "_gnk_attack_active", False):
            self.state = "ATTACK:%s" % attack_phase(
                1.0 - max(0, getattr(h, "timer", 0)) /
                max(1, getattr(h, "attack_cooldown", 45)))
            return
        self.state = "IDLE"

    # ── render ────────────────────────────────────────────────────────
    def draw_ground(self, surface, x, y):
        comp = body_scale(self.hero) * _fx_scale
        for s in self.skills:
            s.draw_ground(surface, comp, GROUND_Y)
        self.particles.draw(surface, layer="back")

    def draw_front(self, surface, x, y):
        rs = body_scale(self.hero)
        comp = rs * _fx_scale
        self.trail.width_boost = self._trail_boost
        self.trail.draw(surface)
        for s in self.skills:
            s.draw_front(surface, comp)
        for im in self.impacts:
            im.draw(surface, comp)
        self.projectiles.draw(surface)
        self.particles.draw(surface, layer="front")

    # ── introspeksi ───────────────────────────────────────────────────
    def stats(self):
        return {"particles": self.particles.count(),
                "impacts": len(self.impacts),
                "trail": len(self.trail.points) + len(self.trail.points_back),
                "trail_points": len(self.trail.points),
                "projectiles": self.projectiles.count(),
                "skills": len(self.skills),
                "dropped": self.particles.dropped +
                self.projectiles.dropped,
                "state": self.state}

    # alias publik (kontrak lama: test/tooling memanggil on_cast, dll.)
    on_cast = emit_cast
    on_blink = emit_blink
    on_impact = emit_impact
    on_swing_start = emit_swing_start
    on_void_release = emit_void_release
    on_death = emit_death

    def clear(self):
        for s in self.impacts:
            ImpactFX.release(s)
        for s in self.skills:
            SkillFX.release(s)
        self.impacts = []
        self.skills = []
        self.particles.clear()
        self.projectiles.clear()
        self.trail.reset()
        self.void_screen = None
        self.state = "IDLE"
        self.time = 0.0


# ═════════════════════════════════════════════════════════════════════
# TAIL PUBLIK — registry per-hero, tick global, lapisan render, notify.
# ═════════════════════════════════════════════════════════════════════
_DIRECTORS = {}               # id(hero) -> GornakFXDirector
_ORDER = []                   # urutan FIFO untuk eviksi (hero mati/banci)
_MAX_TRACKED = 12
_TICK_MS = {"last": -1}


def _release(hero):
    d = _DIRECTORS.pop(id(hero), None)
    if d is not None:
        try:
            _ORDER.remove(id(hero))
        except ValueError:
            pass
        d.clear()
    if getattr(hero, "_gnk_live_fx", None) is d:
        hero._gnk_live_fx = None
    return d


def director_for(hero):
    """Direktur milik hero (dibuat sekali; maksimum 12 terdaftar)."""
    d = _DIRECTORS.get(id(hero))
    if d is None:
        d = GornakFXDirector(hero)
        _DIRECTORS[id(hero)] = d
        _ORDER.append(id(hero))
        while len(_ORDER) > _MAX_TRACKED:
            old_id = _ORDER.pop(0)
            old = _DIRECTORS.pop(old_id, None)
            if old is not None:
                old.clear()
    return d


def attach(hero):
    """Pasang lapisan hidup pada hero; None jika modul dinonaktifkan."""
    if not GORNAK_FX_ENABLED or hero is None:
        return None
    d = director_for(hero)
    hero._gnk_live_fx = d
    return d


def owns(hero):
    """True HANYA jika direktur hero masih terdaftar hidup.

    Setelah reset_all()/eviksi, pointer basi di hero TIDAK dihitung —
    renderer lalu jatuh ke fallback kanvas, bukan ke state kosong.
    """
    d = getattr(hero, "_gnk_live_fx", None)
    if d is None:
        return False
    return _DIRECTORS.get(id(hero)) is d


def tick(dt=None, frame=None):
    """Maju semua direktur. ``dt=None`` = dt bus SHARED; dua pemanggil
    (loop _core dan pipeline heroes) dalam satu frame SDL yang sama
    tidak boleh menggandakan langkah."""
    if not _DIRECTORS:
        return 0
    if dt is None:
        now = -1
        try:
            now = int(pygame.time.get_ticks())
        except Exception:
            now = -1
        if now >= 0 and now == _TICK_MS["last"]:
            return 0
        _TICK_MS["last"] = now
        dt = _feel_dt()
        if dt <= 0 or dt > 0.1:
            dt = FIXED_DT
    n = 0
    for d in _DIRECTORS.values():
        h = d.hero
        d.update(dt, getattr(h, "x", 0.0), getattr(h, "y", 0.0))
        n += 1
    return n


def draw_ground_layer(surface, hero, x=None, y=None):
    """Telegraph hidup DI BAWAH unit (cincin area SkillFX + puing back)."""
    d = _DIRECTORS.get(id(hero))
    if d is None:
        d = attach(hero)
    if d is None:
        return
    tick()                              # dt bus; guard frame-sama di tick
    if x is None:
        x = getattr(hero, "x", 0.0)
    if y is None:
        y = getattr(hero, "y", 0.0)
    d.draw_ground(surface, x, y)


def draw_live_layer(surface, hero, x=None, y=None):
    """Trail + impact + projectile + skill depan + partikel depan."""
    d = _DIRECTORS.get(id(hero))
    if d is None:
        d = attach(hero)
    if d is None:
        return
    tick()                              # dt bus; guard frame-sama di tick
    if x is None:
        x = getattr(hero, "x", 0.0)
    if y is None:
        y = getattr(hero, "y", 0.0)
    d.draw_front(surface, x, y)
    if DEBUG_CHARACTER:
        draw_debug_overlay(surface, hero, x, y)


# ── notifier engine ──────────────────────────────────────────────────
def notify_skill_cast(hero, skill):
    d = director_for(hero)
    d.emit_cast(getattr(hero, "x", 0.0), getattr(hero, "y", 0.0), skill)


def notify_melee_impact(hero, target, damage=70, crit=False):
    """Tebasan KENA. Power = berat damage; hit-stop selalu di 0.03-0.08 s."""
    d = director_for(hero)
    hx = getattr(hero, "x", 0.0)
    hy = getattr(hero, "y", 0.0)
    if target is not None:
        tx, ty = getattr(target, "x", hx), getattr(target, "y", hy)
    else:
        f = 1 if getattr(hero, "direction", 1) >= 0 else -1
        tx, ty = hx + 30.0 * f, hy
    ang = math.atan2(ty - hy, tx - hx)
    power = max(0.5, min(1.6, damage / 70.0))
    d.emit_impact(tx, ty, ang, power, bool(crit), kind="blade")
    _feel_hit = 0.036 + 0.019 * min(1.5, damage / 70.0)
    if crit:
        _feel_hit += 0.010
    hit_stop(min(0.08, _feel_hit))
    shake(3.4 if crit else 1.5, 0.16 if crit else 0.09)
    d.particles.burst(tx, ty - 4, _budget_particles(4 if crit else 3),
                      70.0, P["dust"], life=0.30, size=2, shape="dust",
                      gravity=-10.0, layer="back")


def notify_projectile_impact(hero, x, y, angle=0.0, damage=0, crit=False,
                             kind="mana"):
    d = director_for(hero)
    power = max(0.6, min(1.4, 0.8 + damage / 220.0))
    d.emit_impact(x, y, angle, power, bool(crit), kind=kind)


def notify_skill_impact(hero, x, y, radius=0.0, skill="e"):
    """Fase IMPACT skill (dipanggil _core saat AoE mengenai)."""
    d = director_for(hero)
    kind = {"q": "mana", "w": "void", "e": "ward", "r": "void"}.get(skill,
                                                                     "blade")
    power = {"q": 1.0, "w": 0.8, "e": 1.2, "r": 1.6}.get(skill, 1.0)
    d.emit_impact(x, y, 0.0, power, skill == "r", kind=kind)
    if skill in ("e", "r"):
        rr = radius or WORLD_RADIUS.get(skill, 100.0)
        n = _budget_particles(10)
        for i in range(n):
            a = i * math.tau / max(1, n)
            d.particles.spawn(x + math.cos(a) * rr, y + math.sin(a) * rr
                              * 0.4,
                              math.cos(a) * 90.0,
                              math.sin(a) * 60.0 - 30.0,
                              0.36, 2, P["fx_light"], shape="shard",
                              rotation=a, gravity=90.0, layer="back")
    if skill == "r":
        shake(5.0, 0.28)
        hit_stop(0.05)


# ── introspeksi / global housekeeping ─────────────────────────────────
def projectiles_for(hero):
    """Daftar snapshot proyektil (dipakai overlay debug renderer)."""
    d = _DIRECTORS.get(id(hero))
    if d is None:
        return []
    out = []
    for pr in d.projectiles.list():
        out.append({"sx": pr.position.x, "sy": pr.position.y,
                    "hit_radius": pr.radius, "age": pr.age,
                    "state": pr.state})
    return out


def total_particles():
    return sum(d.particles.count() for d in _DIRECTORS.values())


def reset_all():
    """Bersihkan SEMUA lapisan hidup + cache surface (anti-efek abadi)."""
    for d in _DIRECTORS.values():
        d.clear()
    _DIRECTORS.clear()
    del _ORDER[:]
    _SURF_CACHE.clear()
    _TICK_MS["last"] = -1
    try:
        from heroes import combat_feel as _f
        _f.reset()
    except Exception:
        pass


def set_fx_scale(s):
    """Mobile/quality: kecilkan lapisan hidup tanpa mengubah gameplay."""
    global _fx_scale
    _fx_scale = max(0.4, min(1.0, float(s)))


def draw_debug_overlay(surface, hero, x=None, y=None):
    """State + partikel + peluru; font bawaan pygame, TANPA file."""
    d = _DIRECTORS.get(id(hero))
    if d is None:
        return
    try:
        font = pygame.font.SysFont(None, 13)
    except Exception:
        return
    if x is None:
        x = getattr(hero, "x", 0.0)
    if y is None:
        y = getattr(hero, "y", 0.0)
    st = d.stats()
    txt = "%s p%d i%d t%d | fps%d" % (
        st["state"], st["particles"], st["impacts"], st["trail"],
        max(1, int(round(1.0 / max(FIXED_DT, _feel_dt())))))
    img = font.render(txt, True, (140, 255, 190))
    surface.blit(img, (int(x) - img.get_width() // 2, int(y) - 92))
    for p in projectiles_for(hero):
        pygame.draw.circle(surface, (255, 90, 240, 190),
                           (int(p["sx"]), int(p["sy"])),
                           int(p["hit_radius"]), 1)
