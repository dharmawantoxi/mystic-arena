# ============================================================================
# heroes/gornak_fx.py
# ----------------------------------------------------------------------------
# GORNAK — COMBAT / GAME-FEEL ENGINE  (screen-space live layer)
#
# Badan Gornak digambar lewat ``_NS_gornak`` (bosses/level1.py) ke canvas
# yang DI-CACHE lalu di-scale oleh pipeline hero.  Artinya semua yang butuh
# gerak 60 fps sejati — trail bilah, partikel, proyektil, impact, guncangan
# layar — TIDAK boleh hidup di dalam canvas itu: hasilnya ikut terkunci
# pada kuantisasi pose (2 frame per pose) dan menyusut bersama sprite.
# Modul ini adalah lapisan hidup tersebut: digambar langsung ke layar pada
# skala 1:1 tiap frame, dengan delta-time nyata.
#
# Pembagian kerja (sengaja, supaya tidak ada efek yang digambar 2x):
#
#   RENDERER (canvas, ter-cache)      MODUL INI (layar, hidup)
#   -----------------------------     -----------------------------------
#   rig + selout + rim light          trail bilah dari histori posisi nyata
#   bayangan kontak, rune tanah       partikel (debu, bara, serpihan rune)
#   TELEGRAPH cincin E/R (100/180 px) PROYEKTIL Mana Break (sistem nyata)
#   pose, foot solver, napas          IMPACT FX + flash + hit-stop + shake
#   after-image blink                 overlay DEBUG_CHARACTER
#
# 100% PROSEDURAL. Tidak ada PNG / JPG / GIF / sprite-sheet / image.load.
# Semua bentuk dibuat dengan pygame.draw + pygame.Surface + pygame.transform.
#
# Isi modul
#   GORNAK_PALETTE      palette khusus karakter (kontrak 9 kunci + ramp)
#   Particle            partikel penuh (acc, gravity, rotasi, fade, drag)
#   ParticleSystem      pool + burst + cap, reusable
#   SwingTrail          weapon trail prosedural dari histori posisi bilah
#   ImpactFX            flash + shockwave + debris + slash fragment
#   GornakProjectile    proyektil modular (spawn->travel->hit->destroy)
#   ProjectileSystem    manajer proyektil
#   SkillFX             lifecycle FX skill (cast->charge->release->fade)
#   GornakFXDirector    satu instance per unit, mengikat semua di atas
#   draw_debug_overlay  hitbox/hurtbox/state/frame/FPS/particle/skill/timer
#   API modul           tick / reset_all / notify_* / draw_*_layer
# ============================================================================

import math
import random

import pygame

try:                                 # bus game-feel bersama (zephyr & gornak)
    from heroes import combat_feel as _feel
except Exception:                    # pragma: no cover - build minimal
    _feel = None


# ============================================================================
# 0.  KONFIGURASI
# ============================================================================

#: Debug visual untuk karakter GORNAK: hitbox, hurtbox, jangkauan, state
#: animasi, frame, FPS, jumlah partikel, state skill, timer serangan.
DEBUG_CHARACTER = False

#: Master switch — kalau False, modul jadi no-op murah (badan tetap jalan).
GORNAK_FX_ENABLED = True

#: Batas keras jumlah partikel hidup per director (anti-kebocoran FPS).
MAX_PARTICLES = 102

#: Batas keras proyektil visual per director.
MAX_PROJECTILES = 9

#: Panjang histori trail senjata (jumlah sample posisi bilah).
TRAIL_SAMPLES = 9

#: Batas dampak aktif per director & skill sekaligus di layar.
MAX_IMPACTS = 4
MAX_SKILLS = 2

#: Simulasi game berjalan pada langkah tetap 1/60 s.
FIXED_DT = 1.0 / 60.0

#: Kecepatan bolt Mana Break (px/detik, ruang dunia).
BOLT_SPEED = 780.0

#: Radius EFEK di ruang dunia. E/R = radius gameplay sebenarnya, Q/W =
#: radius visual (tidak ada AOE gameplay di skill itu).
WORLD_RADIUS = {"q": 44.0, "w": 30.0, "e": 100.0, "r": 180.0}

#: Umur FX skill dalam DETIK. Sinkron dengan ``_NS_gornak.SKILL_DUR``
#: (40/25/60/90 langkah simulasi = 0.67/0.42/1.00/1.50 s) plus sisa
#: after-glow supaya efek tidak "terpotong" saat pose skill selesai.
SKILL_TOTAL = {"q": 0.78, "w": 0.52, "e": 1.16, "r": 1.72}

#: Durasi pose per skill (frame) — dipakai untuk memetakan umur FX ke
#: fase yang sama dengan yang dibaca renderer.
SKILL_DUR = {"q": 40, "w": 25, "e": 60, "r": 90}


# ============================================================================
# 1.  PALETTE  —  dark-fantasy anti-mage: baja dingin + ungu anti-sihir
# ============================================================================

GORNAK_PALETTE = {
    # ── kontrak palette karakter (9 kunci wajib) ────────────────────
    "outline":    (7,    6,  12),
    "shadow":     (24,   5,  44),
    "dark":       (58,  19, 108),
    "body":       (96, 100, 128),
    "mid":        (130,  55, 200),
    "light":      (186, 111, 241),
    "highlight":  (221, 161, 255),
    "weapon":     (164, 170, 196),
    "fx":         (245, 210, 255),

    # ── ramp sihir anti-mana (bolt / trail / impact) ────────────────
    "fx_darkest": (24,    5,  44),
    "fx_dark":    (58,   19, 108),
    "fx_mid":     (130,  55, 200),
    "fx_light":   (186, 111, 241),
    "fx_bright":  (221, 161, 255),
    "fx_hot":     (245, 210, 255),
    "fx_white":   (255, 246, 255),

    # ── baja bilah (spark & cut) ────────────────────────────────────
    "steel_dark": (36,   34,  52),
    "steel_mid":  (96,  100, 128),
    "steel_edge": (212, 218, 242),
    "steel_hot":  (236, 244, 255),

    # ── bahan fisik: kulit, jubah, kuningan ─────────────────────────
    "skin":       (148,   88,  48),
    "robe":       (58,    36,  90),
    "brass":      (172,  132,  51),
    "brass_hot":  (230,  202, 116),

    # ── sisa pembakaran (debu / asap / arang) ───────────────────────
    "smoke":      (34,   20,  46),
    "ash":        (72,   48,  88),
    "dust":       (120,  96,  78),
}

P = GORNAK_PALETTE

#: Kunci yang boleh disalin dari palet renderer supaya warna karakter
#: dan warna efek tidak pernah berbeda "satu derajat".
_PALETTE_SYNC = {
    "outline": "armor_darkest",
    "shadow": "magic_darkest",
    "dark": "magic_dark",
    "mid": "magic_mid",
    "light": "magic_light",
    "highlight": "magic_hot",
    "weapon": "blade_light",
    "fx": "magic_shine",
    "fx_darkest": "magic_darkest",
    "fx_dark": "magic_dark",
    "fx_mid": "magic_mid",
    "fx_light": "magic_light",
    "fx_bright": "magic_hot",
    "fx_hot": "magic_shine",
    "steel_dark": "blade_dark",
    "steel_mid": "blade_mid",
    "steel_edge": "blade_shine",
}

_PALETTE_SYNCED = False


def _sync_palette():
    """Salin warna tema dari ``_NS_gornak.PALETTE`` sekali saja.

    Renderer adalah satu-satunya sumber kebenaran untuk material karakter;
    efek hidup tidak boleh punya salinan yang lalu melenceng.  Kalau
    renderer tidak tersedia (tooling minimal), nilai literal di atas dipakai.
    """
    global _PALETTE_SYNCED
    if _PALETTE_SYNCED:
        return
    _PALETTE_SYNCED = True
    G = _renderer()
    if G is None:
        return
    pal = getattr(G, "PALETTE", None)
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
    """``_NS_gornak`` atau None. Diimpor malas: modul boss besar."""
    global _RENDERER
    if _RENDERER is None:
        try:
            from bosses.level1 import _NS_gornak as G
            _RENDERER = G
        except Exception:                      # pragma: no cover
            _RENDERER = False
    return _RENDERER or None


def _fallback_pose(boss):
    """(action, phase, ap) tanpa renderer: baca atribut yang sudah ada."""
    skill = getattr(boss, "active_skill", None)
    action = getattr(boss, "_gnk_pose_action", None)
    if action is None:
        action = {"q": "surge", "w": "blink", "e": "ward",
                  "r": "void"}.get(skill)
    if action is None:
        action = ("attack" if getattr(boss, "_gnk_attack_active", False)
                  else "idle")
    phase = float(getattr(boss, "pulse", 0.0) or 0.0)
    ap = 0.0
    if action == "attack":
        raw = float(getattr(boss, "_gnk_attack_progress", 0.0) or 0.0)
        ap = min(1.0, max(0.0, raw))
        if 0.30 <= raw < 0.60:
            ap = 0.79
    return action, phase, ap


def pose_of(boss):
    """(action, phase, ap) — pose yang SEDANG digambar badan."""
    G = _renderer()
    if G is None:
        return _fallback_pose(boss)
    try:
        return G._resolve_pose(boss, bool(getattr(boss, "_moving_cached",
                                                  False)))
    except Exception:                          # pragma: no cover
        return _fallback_pose(boss)


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
    """Skala rig -> piksel layar (SCALE renderer dikali normalisasi hero)."""
    G = _renderer()
    k = getattr(G, "SCALE", 1.32) if G is not None else 1.32
    return float(k) * render_scale(boss)


def screen_point(boss, x, y, local, action=None, phase=None, ap=None):
    """Ruang lokal rig -> piksel layar.

    Sama persis dengan ``_NS_gornak._local_to_screen``, tapi memakai skala
    normalisasi hero supaya efek hidup menempel di badan pada KEDUA jalur
    (arena 1:1 dan lane hero yang sprite-nya di-kecilkan).
    """
    G = _renderer()
    facing = getattr(boss, "direction", None)
    if facing is None:
        facing = getattr(boss, "facing", 1)
    f = 1 if (facing or 1) >= 0 else -1
    if action is None or phase is None or ap is None:
        action, phase, ap = pose_of(boss)
    lean = root_y = 0
    lift = 4.0
    k = body_scale(boss)
    if G is not None:
        try:
            lean, root_y = G._rig_shift(action, phase, ap)
        except Exception:                      # pragma: no cover
            lean = root_y = 0
        lift = float(getattr(G, "LIFT", 4))
    return (int(round(x + (local[0] * f + lean * f) * k)),
            int(round(y - lift * render_scale(boss)
                      + (local[1] + root_y) * k)))


def blade_points(boss, x, y, back=False):
    """(grip, tip) bilah dalam piksel layar — sumber bentuk trail."""
    G = _renderer()
    action, phase, ap = pose_of(boss)
    if G is None:
        grip_l = (12, 2)
        tip_l = (40, -18) if not back else (-14, 10)
    else:
        try:
            grip = (G._back_grip_local(action, ap, phase) if back
                    else G._front_grip_local(action, ap, phase))
            tip_l = G._tip_local(action, phase, ap, back)
            grip_l = (int(grip[0]), int(grip[1]))
        except Exception:                      # pragma: no cover
            grip_l, tip_l = (12, 2), (36, -6)
    grip = screen_point(boss, x, y, grip_l, action, phase, ap)
    tip = screen_point(boss, x, y, tip_l, action, phase, ap)
    return pygame.Vector2(grip), pygame.Vector2(tip)


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
    """Apakah guncangan boleh dipakai untuk game feel (bukan hanya kamera).

    Setting "screen shake" pemain HANYA mengatur kamera (sudah ditegakkan
    di EffectManager); hit-stop & getaran FX karakter lain tetap boleh
    membaca angka yang sama, jadi mirror-nya tidak ikut dimatikan.
    Yang dimatikan di sini cuma preset kualitas rendah (mobile).
    """
    Q = _quality()
    return True if Q is None else bool(getattr(Q, "screen_shake", True))


# ============================================================================
# 4.  HELPER WARNA & CACHING
# ============================================================================

def _clamp_color(color):
    """Jepit komponen ke 0-255, pastikan tuple int 3-kanal."""
    if type(color) is tuple and len(color) >= 3:
        _r, _g, _b = color[0], color[1], color[2]
        if (type(_r) is int and type(_g) is int and type(_b) is int
                and 0 <= _r <= 255 and 0 <= _g <= 255 and 0 <= _b <= 255):
            return (_r, _g, _b)
    return tuple(max(0, min(255, int(c))) for c in color[:3])


def _mix(a, b, t):
    """Interpolasi linear dua warna RGB."""
    t = max(0.0, min(1.0, float(t)))
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


def _hash01(seed):
    """Pseudo-random deterministik [0,1) dari integer.

    Deterministik itu wajib: key surface cache tidak boleh berubah tiap
    frame, kalau tidak cache-nya tidak pernah kena.
    """
    h = int(seed) * 2654435761 & 0xFFFFFFFF
    h ^= h >> 16
    h = (h * 2246822519) & 0xFFFFFFFF
    return (h & 0xFFFF) / 65535.0


_SURF_CACHE = {}
_SURF_CACHE_MAX = 384


def _cache_put(key, surf):
    """Simpan surface; buang 25% entri tertua saat penuh (FIFO ringan)."""
    if len(_SURF_CACHE) >= _SURF_CACHE_MAX:
        for k in list(_SURF_CACHE)[:_SURF_CACHE_MAX // 4]:
            del _SURF_CACHE[k]
    _SURF_CACHE[key] = surf
    return surf


def clear_cache():
    """Kosongkan cache surface (ganti resolusi / ganti level)."""
    _SURF_CACHE.clear()


def cache_size():
    """Jumlah surface yang sedang di-cache (dipakai debug/HUD)."""
    return len(_SURF_CACHE)


def glow_surface(radius, color, power=1.0):
    """Bola cahaya radial, PREMULTIPLIED agar benar untuk blit additive.

    Penting: ``BLEND_RGB_ADD`` mengabaikan kanal alpha. Kalau lingkaran
    digambar RGB penuh + alpha menurun, hasil additive-nya jadi CAKRAM
    solid. Di sini intensitas dikalikan ke RGB DAN disalin ke alpha, jadi
    surface yang sama benar untuk blit normal maupun additive.
    """
    radius = max(2, int(radius)) // 2 * 2
    color = _clamp_color(color)
    power = round(float(power), 2)
    key = ("glow", radius, color, power)
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf
    size = radius * 2 + 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = radius + 1
    steps = max(4, min(radius, 12))
    for i in range(steps, 0, -1):
        t = i / float(steps)
        r = max(1, int(radius * t))
        k = power * (1.0 - t) ** 1.75
        if k <= 0.004:
            continue
        pygame.draw.circle(
            surf,
            (int(color[0] * k), int(color[1] * k), int(color[2] * k),
             min(255, int(255 * k))), (c, c), r)
    return _cache_put(key, surf)


def spark_surface(size, color):
    """Bintang 4 sudut khas pixel-art (hard edge, tanpa gradien)."""
    size = max(3, int(size))
    color = _clamp_color(color)
    key = ("spark", size, color)
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf
    s = size * 2 + 1
    surf = pygame.Surface((s, s), pygame.SRCALPHA)
    c = size
    arm = max(1, size // 3)
    pygame.draw.polygon(surf, (*color, 235),
                        [(c, 0), (c + arm, c), (c, s - 1), (c - arm, c)])
    pygame.draw.polygon(surf, (*color, 185),
                        [(0, c), (c, c - max(1, size // 4)),
                         (s - 1, c), (c, c + max(1, size // 4))])
    pygame.draw.rect(surf, (*P["fx_white"], 255),
                     (c - 1, c - 1, 3, 3))
    return _cache_put(key, surf)


def ring_surface(radius, thickness, color, alpha=255, dashed=0):
    """Cincin energi (opsional terputus ``dashed`` = jumlah segmen)."""
    radius = max(3, int(radius)) // 3 * 3
    thickness = max(1, int(thickness))
    color = _clamp_color(color)
    dashed = int(dashed)
    alpha = int(alpha) // 16 * 16
    key = ("ring", radius, thickness, color, alpha, dashed)
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf
    size = radius * 2 + thickness * 2 + 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size // 2
    if dashed <= 0:
        pygame.draw.circle(surf, (*color, int(alpha)), (c, c), radius,
                           thickness)
    else:
        step = math.tau / dashed
        span = step * 0.56
        for i in range(dashed):
            a0 = i * step
            pts = []
            n = 4
            for j in range(n + 1):
                a = a0 + span * j / float(n)
                pts.append((c + math.cos(a) * radius,
                            c + math.sin(a) * radius))
            for j in range(len(pts) - 1):
                pygame.draw.line(surf, (*color, int(alpha)),
                                 (int(pts[j][0]), int(pts[j][1])),
                                 (int(pts[j + 1][0]), int(pts[j + 1][1])),
                                 thickness)
    return _cache_put(key, surf)


def ellipse_ring_surface(rx, ry, thickness, color, angle_deg=0):
    """Cincin ELIPS berarah — shockwave mendarah, bukan lingkaran polos."""
    rx = max(3, int(rx)) // 3 * 3
    ry = max(2, int(ry)) // 2 * 2
    thickness = max(1, int(thickness))
    color = _clamp_color(color)
    step = int(angle_deg) // 15 * 15
    key = ("ering", rx, ry, thickness, color, step)
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf
    pad = thickness + 2
    base = pygame.Surface((rx * 2 + pad * 2, ry * 2 + pad * 2),
                          pygame.SRCALPHA)
    pygame.draw.ellipse(base, (*color, 255),
                        (pad, pad, rx * 2, ry * 2), thickness)
    if step:
        base = pygame.transform.rotate(base, -step)
    return _cache_put(key, base)


def ground_glow_surface(radius, color, power=0.3):
    """Kabut cahaya di tanah (elips gepeng, premultiplied)."""
    radius = max(4, int(radius))
    color = _clamp_color(color)
    power = round(float(power), 2)
    key = ("gglow", radius, color, power)
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf
    w = radius * 2 + 4
    h = radius + 4
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    steps = max(4, min(radius // 2, 12))
    for i in range(steps, 0, -1):
        t = i / float(steps)
        rx = max(2, int(radius * t))
        ry = max(1, int(radius * t * 0.42))
        k = power * (1.0 - t) ** 1.5
        if k <= 0.004:
            continue
        pygame.draw.ellipse(
            surf,
            (int(color[0] * k), int(color[1] * k), int(color[2] * k),
             min(255, int(255 * k))),
            (w // 2 - rx, h // 2 - ry, rx * 2, ry * 2))
    return _cache_put(key, surf)


def _shard_poly(surface, cx, cy, ang, length, width, color, alpha=255,
                core=None):
    """Serpihan tajam berorientasi (chip rune / pecahan bilah), tanpa AA.

    Digambar LANGSUNG (bukan surface cache yang diputar) — ``transform.rotate``
    mengalokasi surface baru tiap panggilan, dan itu salah satu hal yang
    paling cepat menjatuhkan FPS saat banyak partikel di layar.
    """
    alpha = int(alpha)
    if alpha <= 5:
        return
    ln = max(2, int(length))
    wd = max(1, int(width))
    ca, sa = math.cos(ang), math.sin(ang)
    pts = []
    for dx, dy in ((ln, 0), (-ln // 3, wd), (-ln, 0), (-ln // 3, -wd)):
        pts.append((int(cx) + int(dx * ca - dy * sa),
                    int(cy) + int(dx * sa + dy * ca)))
    pygame.draw.polygon(surface, (*_clamp_color(color), min(255, alpha)), pts)
    if core is not None and ln >= 6:
        pygame.draw.polygon(surface, (*_clamp_color(core), min(255, alpha + 20)),
                            [(int(cx) + int(ln * .6 * ca),
                              int(cy) + int(ln * .6 * sa)),
                             (int(cx) - wd // 2, int(cy) - max(1, wd // 2)),
                             (int(cx) - int(ln * .4), int(cy))])


# --- scratch surface pool: hindari alokasi Surface tiap gambar --------------
_SCRATCH = {}


def _scratch(w, h):
    """Surface sementara transparan berukuran >= (w,h), dipakai ulang."""
    w = max(4, int(w))
    h = max(4, int(h))
    key = (1 << (w - 1).bit_length(), 1 << (h - 1).bit_length())
    s = _SCRATCH.get(key)
    if s is None:
        s = pygame.Surface(key, pygame.SRCALPHA)
        _SCRATCH[key] = s
    else:
        s.fill((0, 0, 0, 0))
    return s


def _blit_faded(surface, surf, cx, cy, alpha=255, additive=False):
    """Blit surface cache di tengah (cx, cy) dengan alpha eksplisit.

    Aturan: SETIAP blit surface cache selalu men-set alpha lewat helper ini,
    supaya tidak ada jalur yang lupa dan mewarisi alpha dari pemakaian
    sebelumnya (surface cache adalah objek yang sama).
    """
    alpha = int(alpha)
    if alpha <= 5:
        return
    if additive:
        surface.blit(surf, (int(cx) - surf.get_width() // 2,
                            int(cy) - surf.get_height() // 2),
                     special_flags=pygame.BLEND_RGB_ADD)
        return
    surf.set_alpha(min(255, alpha))
    surface.blit(surf, (int(cx) - surf.get_width() // 2,
                        int(cy) - surf.get_height() // 2))


# ============================================================================
# 5.  PARTICLE SYSTEM
# ============================================================================

class Particle:
    """Satu partikel prosedural.

    Kontrak atribut: ``pos``/``velocity``/``vel``/``acceleration``/``acc``,
    ``life``, ``max_life``, ``size``, ``rotation``, ``rotation_speed``,
    ``alpha``, ``gravity``, ``color`` — plus ``shape`` (bentuk gambar),
    ``drag``, ``additive``, ``layer``.  Nama pendek dipakai di semua jalur
    panas (``__slots__``, tanpa lookup properti); nama panjang disediakan
    sebagai alias baca untuk overlay debug, alat audit, dan test.
    """

    __slots__ = ("pos", "vel", "acc", "life", "max_life", "size",
                 "rotation", "rotation_speed", "alpha", "gravity",
                 "color", "color_end", "shape", "drag", "additive",
                 "active", "fade_pow", "layer", "seed")

    def __init__(self):
        self.pos = pygame.Vector2()
        self.vel = pygame.Vector2()
        self.acc = pygame.Vector2()
        self.life = 0.0
        self.max_life = 1.0
        self.size = 2.0
        self.rotation = 0.0
        self.rotation_speed = 0.0
        self.alpha = 255
        self.gravity = 0.0
        self.color = P["fx_bright"]
        self.color_end = None
        self.shape = "pixel"
        self.drag = 0.0
        self.additive = False
        self.active = False
        self.fade_pow = 1.0
        self.layer = "front"
        self.seed = 0

    # ── alias baca (kontrak master prompt) ──────────────────────────
    @property
    def position(self):
        return self.pos

    @property
    def velocity(self):
        return self.vel

    @property
    def acceleration(self):
        return self.acc

    # ------------------------------------------------------------------
    def spawn(self, x, y, vx, vy, life, size, color, **kw):
        """Aktifkan partikel ini (dipakai ulang dari pool)."""
        self.pos.update(x, y)
        self.vel.update(vx, vy)
        self.acc.update(float(kw.get("ax", 0.0)), float(kw.get("ay", 0.0)))
        self.life = self.max_life = max(0.02, float(life))
        self.size = float(size)
        self.color = color
        self.color_end = kw.get("color_end")
        self.gravity = float(kw.get("gravity", 0.0))
        self.drag = float(kw.get("drag", 0.0))
        self.rotation = float(kw.get("rotation", 0.0))
        self.rotation_speed = float(kw.get("rotation_speed", 0.0))
        self.alpha = int(kw.get("alpha", 255))
        self.shape = kw.get("shape", "pixel")
        self.additive = bool(kw.get("additive", False))
        self.fade_pow = float(kw.get("fade_pow", 1.0))
        self.layer = kw.get("layer", "front")
        self.seed = int(kw.get("seed", 0))
        self.active = True
        return self

    # ------------------------------------------------------------------
    def update(self, dt):
        """Integrasi gerak; False kalau partikel sudah mati."""
        self.life -= dt
        if self.life <= 0.0:
            self.active = False
            return False
        self.vel.x += self.acc.x * dt
        self.vel.y += (self.acc.y + self.gravity) * dt
        if self.drag:
            damp = max(0.0, 1.0 - self.drag * dt)
            self.vel.x *= damp
            self.vel.y *= damp
        self.pos.x += self.vel.x * dt
        self.pos.y += self.vel.y * dt
        self.rotation += self.rotation_speed * dt
        return True

    # ------------------------------------------------------------------
    def draw(self, surface):
        """Gambar partikel — pixel-snapped, tepi keras, tanpa AA berlebihan."""
        t = self.life / self.max_life
        fade = t ** self.fade_pow
        a = int(self.alpha * fade)
        if a <= 4:
            return
        col = self.color if self.color_end is None \
            else _mix(self.color_end, self.color, fade)
        x = int(self.pos.x)
        y = int(self.pos.y)
        sz = max(1, int(self.size * (0.35 + 0.65 * fade)))
        shape = self.shape

        if shape == "glow":
            if not glow_allowed():
                return
            g = glow_surface(sz * 2, col, round(0.85 * fade, 2))
            surface.blit(g, (x - sz * 2, y - sz * 2),
                         special_flags=pygame.BLEND_RGB_ADD)
            return

        if shape == "spark":
            s = spark_surface(sz + 1, col)
            s.set_alpha(a)
            surface.blit(s, (x - sz - 1, y - sz - 1))
            return

        if shape == "shard":
            # serpihan berputar: debris rune / pecahan bilah
            _shard_poly(surface, x, y, self.rotation, sz * 2,
                        max(1, sz // 2 + 1), col, a, P["fx_white"])
            return

        if shape == "streak":
            v = self.vel
            n = v.length()
            if n < 0.01:
                return
            ux, uy = v.x / n, v.y / n
            ln = max(2, int(sz * 2 + n * 0.022))
            buf = _scratch(ln * 2 + 6, ln * 2 + 6)
            off = ln + 3
            pygame.draw.line(buf, (*col, a), (off, off),
                             (off - int(ux * ln), off - int(uy * ln)),
                             max(1, sz // 2 + 1))
            surface.blit(buf, (x - off, y - off))
            return

        if shape == "dust":
            # kepul debu tanah: TIDAK additive, tepi lunak 1 langkah
            r = sz + 1
            buf = _scratch(r * 2 + 2, r * 2 + 2)
            pygame.draw.rect(buf, (*col, a), (2, 2, sz, sz))
            pygame.draw.rect(buf, (*col, max(0, a // 2)),
                             (1, 3, max(1, sz // 2), max(1, sz // 2)))
            surface.blit(buf, (x - r, y - r))
            return

        # default: kotak chunky (inti terang kalau cukup besar)
        buf = _scratch(sz * 2 + 2, sz * 2 + 2)
        if self.additive:
            # BLEND_RGB_ADD mengabaikan kanal alpha -> fade harus
            # dikodekan di RGB (premultiplied), kalau tidak partikel
            # additive selalu tampil intensitas penuh sampai mati.
            k = max(0.0, min(1.0, a / 255.0))
            col = _clamp_color((col[0] * k, col[1] * k, col[2] * k))
            wc = _clamp_color((P["fx_white"][0] * k,
                               P["fx_white"][1] * k,
                               P["fx_white"][2] * k))
            pygame.draw.rect(buf, (*col, 255), (1, 1, sz, sz))
            if sz >= 3:
                pygame.draw.rect(buf, (*wc, 255),
                                 (1, 1, max(1, sz // 2), max(1, sz // 2)))
            surface.blit(buf, (x - sz // 2, y - sz // 2),
                         special_flags=pygame.BLEND_RGB_ADD)
            return
        pygame.draw.rect(buf, (*col, a), (1, 1, sz, sz))
        if sz >= 3:
            pygame.draw.rect(buf, (*P["fx_white"], min(255, a + 40)),
                             (1, 1, max(1, sz // 2), max(1, sz // 2)))
        surface.blit(buf, (x - sz // 2, y - sz // 2))


class ParticleSystem:
    """Pool partikel reusable: spawn / burst / update / draw, dengan cap."""

    def __init__(self, cap=MAX_PARTICLES):
        self.cap = int(cap)
        self._pool = []
        self._live = []
        self.dropped = 0            # berapa permintaan dibuang (diagnostik)

    # ------------------------------------------------------------------
    def _acquire(self):
        if self._pool:
            return self._pool.pop()
        return Particle()

    def count(self):
        """Jumlah partikel hidup."""
        return len(self._live)

    def alive(self):
        """Partikel hidup (read-only; untuk overlay debug, tes, dan alat audit)."""
        return tuple(self._live)

    def clear(self):
        """Matikan semua partikel (dikembalikan ke pool)."""
        for p in self._live:
            p.active = False
            self._pool.append(p)
        self._live.clear()

    # ------------------------------------------------------------------
    def spawn(self, x, y, vx, vy, life, size, color, **kw):
        """Spawn satu partikel. None kalau penuh / anggaran habis."""
        budget = particle_budget()
        if budget <= 0.0:
            self.dropped += 1
            return None
        room = int(self.cap * budget) - len(self._live)
        if room <= 0:
            self.dropped += 1
            return None
        p = self._acquire().spawn(x, y, vx, vy, life, size, color, **kw)
        self._live.append(p)
        return p

    # ------------------------------------------------------------------
    def burst(self, x, y, count, speed=(60.0, 210.0), life=(0.22, 0.55),
              size=(2, 4), colors=None, spread=math.tau, direction=0.0,
              gravity=0.0, drag=2.2, shape="pixel", additive=False,
              rotation_speed=(0.0, 0.0), fade_pow=1.0, layer="front"):
        """Semburan radial / berarah (``direction`` + ``spread``)."""
        colors = colors or (P["fx_bright"], P["fx_light"], P["fx_hot"])
        budget = particle_budget()
        if budget <= 0.0:
            return 0
        room = int(self.cap * budget) - len(self._live)
        if room <= 0:
            self.dropped += int(count)
            return 0
        n = min(int(count * budget) if budget < 1.0 else int(count), room)
        for i in range(n):
            ang = direction + (random.random() - 0.5) * spread
            spd = random.uniform(speed[0], speed[1])
            self.spawn(
                x, y,
                math.cos(ang) * spd, math.sin(ang) * spd,
                random.uniform(life[0], life[1]),
                random.uniform(size[0], size[1]),
                colors[i % len(colors)],
                gravity=gravity, drag=drag, shape=shape,
                additive=additive, fade_pow=fade_pow, layer=layer,
                rotation=random.random() * math.tau,
                rotation_speed=random.uniform(rotation_speed[0],
                                               rotation_speed[1]),
                seed=i)
        return n

    # ------------------------------------------------------------------
    def stream(self, x, y, tx, ty, count, life=(0.3, 0.6), size=(1, 3),
               colors=None, bow=18.0, layer="back"):
        """Aliran partikel MENJULUR dari (x,y) ke (tx,ty).

        Dipakai R Mana Void (mote mana dihisap dari korban ke dada Gornak)
        dan E Counterspell (mote ditarik masuk ke garda). ``bow``
        melengkungkan lintasan supaya tidak terbaca sebagai garis lurus.
        """
        colors = colors or (P["fx_light"], P["fx_bright"], P["fx_mid"])
        d = math.hypot(tx - x, ty - y)
        if d < 1.0:
            return 0
        ux, uy = (tx - x) / d, (ty - y) / d
        px, py = -uy, ux
        budget = particle_budget()
        if budget <= 0.0:
            return 0
        made = 0
        for i in range(min(int(count), 24)):
            side = random.choice((-1.0, 1.0)) * random.uniform(0.35, 1.0)
            sx = x + px * bow * side
            sy = y + py * bow * side * 0.55
            p = self.spawn(sx, sy, (tx - sx) / max(0.05, life[1]) * 0.9,
                           (ty - sy) / max(0.05, life[1]) * 0.9,
                           random.uniform(*life), random.uniform(*size),
                           colors[i % len(colors)],
                           drag=0.35, shape="pixel", additive=True,
                           layer=layer,
                           rotation=math.atan2(uy, ux),
                           rotation_speed=side * 2.2)
            if p is None:
                break
            made += 1
        return made

    # ------------------------------------------------------------------
    def update(self, dt):
        """Integrasi semua partikel; yang mati masuk pool lagi."""
        if not self._live:
            return
        live = self._live
        keep = []
        pool = self._pool
        for p in live:
            if p.update(dt):
                keep.append(p)
            elif len(pool) < self.cap:
                pool.append(p)
        self._live = keep

    # ------------------------------------------------------------------
    def draw(self, surface, layer="front"):
        """Gambar partikel per lapisan (``layer`` = 'back' / 'front')."""
        if not self._live:
            return
        want_back = layer == "back"
        for p in self._live:
            if (p.layer == "back") == want_back:
                p.draw(surface)


# ============================================================================
# 6.  SWING TRAIL  —  jejak bilah dari histori posisi SUNGGUHAN
# ============================================================================

class SwingTrail:
    """Trail dua bilah berbasis histori posisi (grip, tip) per frame.

    Bentuk pita murni turunan lintasan senjata, jadi trail tidak pernah
    lepas dari bilah walau posenya diubah orang lain. Yang disimpan dua
    pasang titik (bilah depan & belakang) supaya serangan Gornak terbaca
    sebagai GUNTING dua bilah, bukan satu garis.
    """

    def __init__(self, samples=TRAIL_SAMPLES):
        self.samples = int(samples)
        self.points = []                 # [[grip, tip, umur], ...] (depan)
        self.points_back = []            # sama, bilah belakang
        self.life = 0.24
        self.width_boost = 1.0
        self.active = False
        # Wash lebar memakai warna TENGAH (bukan fx_light): di atas
        # background gelap, wash pucat terbaca seperti "bidang kaca",
        # sedangkan violet dalam terbaca seperti energi yang disapu bilah.
        self.color_edge = P["fx_mid"]
        self.color_core = P["fx_bright"]
        self.color_back = P["steel_mid"]

    # ------------------------------------------------------------------
    def reset(self):
        """Kosongkan trail (dipanggil saat ayunan baru mulai)."""
        self.points.clear()
        self.points_back.clear()
        self.active = False

    def push(self, grip, tip, grip_b=None, tip_b=None):
        """Catat satu posisi senjata."""
        self.points.append([pygame.Vector2(grip), pygame.Vector2(tip), 0.0])
        if len(self.points) > self.samples:
            self.points.pop(0)
        if grip_b is not None and tip_b is not None:
            self.points_back.append(
                [pygame.Vector2(grip_b), pygame.Vector2(tip_b), 0.0])
            if len(self.points_back) > self.samples:
                self.points_back.pop(0)
        self.active = True

    # ------------------------------------------------------------------
    def update(self, dt):
        """Tuakan sample; buang yang lewat umur."""
        for lst in (self.points, self.points_back):
            if not lst:
                continue
            for s in lst:
                s[2] += dt
            keep = [s for s in lst if s[2] < self.life]
            if lst is self.points:
                self.points = keep
            else:
                self.points_back = keep
        if not self.points and not self.points_back:
            self.active = False

    # ------------------------------------------------------------------
    #: satu langkah trail tidak boleh membelok lebih tajam dari ini tanpa
    #: memutus strip (arah balik = strip baru, bukan sapuan menembus badan)
    MAX_TURN_DOT = 0.15
    #: langkah sudut maksimum sebelum busur dipecah jadi beberapa quad
    ARC_STEP = 0.16
    #: sweep maksimum satu strip (lebih dari ini = trail melingkari badan
    #: dan berubah jadi "tembok" transparan, jadi ekor tua dibuang)
    MAX_SWEEP = 1.95

    def _ribbon(self, surface, lst, edge, core, tip_col, base_alpha):
        """Satu pita tebasan: sector cincin yang disapu UJUNG bilah.

        Cara naif — polygon [tip_lama, tip_baru, grip_baru, grip_lama] —
        menghasilkan "lembaran" raksasa begitu bilah berputar cepat atau
        berbalik saat recovery, dan bentuknya bukan lagi bekas tebasan.
        Senjata yang BERPUTAR meninggalkan sector cincin di sekitar poros
        grip, antara radius dalam dan radius ujung, dibatasi dua sudut:
        itulah yang digambar di sini.

        Yang membuatnya terbaca sebagai ayunan kelas profesional:

        * pita ramping di tepi LUAR bilah (5.5%-16% panjang bilah, melebar
          ke sampel terbaru) — bukan kipas penuh dari bahu, jadi karakter
          tidak pernah tertutup efek;
        * busur dipecah per ARC_STEP radian -> tepi luar mulus mengikuti
          lintasan, bukan tali lurus antar frame;
        * satu garis 1-2 px tepat di lintasan ujung bilah = glint baja;
        * alpha ~ rank^2 -> ekor tua pudar, ujung baru paling terang, jadi
          akselerasi tebasan terasa walau frame-nya sedikit;
        * langkah sudut besar (frame drop / ayunan super cepat) dibuat
          lebih pudar per sector, dan sapuan total dipotong ke MAX_SWEEP,
          sehingga trail tidak pernah melingkari badan jadi "tembok".
        """
        n = len(lst)
        if n < 2:
            return

        # ── histori -> (poros, sudut, radius, umur) ──────────────────
        nodes = []
        for g, t, age in lst:
            blade = t - g
            r = blade.length()
            if r < 6.0:
                continue                      # bilah terlipat: tak ada busur
            nodes.append((g, math.atan2(blade.y, blade.x), r, age))
        if len(nodes) < 2:
            return

        # ── putus strip saat arah berbalik / bilah nyaris diam ────────
        strips = []
        cur = [nodes[0]]
        prev_dir = 0.0
        for i in range(1, len(nodes)):
            da = self._ang_delta(nodes[i][1], cur[-1][1])
            if abs(da) < 0.035:
                continue                      # tidak ada sapuan -> tidak ada pita
            if prev_dir * da < 0.0:           # arah berbalik -> mulai baru
                if len(cur) > 1:
                    strips.append((cur, prev_dir))
                cur = [nodes[i - 1], nodes[i]]
                prev_dir = da
                continue
            prev_dir = da
            cur.append(nodes[i])
        if len(cur) > 1:
            strips.append((cur, prev_dir))

        # ── gambar ────────────────────────────────────────────────────
        for raw, _pd in strips:
            # pangkas ekor tua sampai total sapuan masuk MAX_SWEEP
            strip = raw
            sweep = 0.0
            keep = 0
            for j in range(len(strip) - 1, 0, -1):
                sweep += abs(self._ang_delta(strip[j][1], strip[j - 1][1]))
                if sweep > self.MAX_SWEEP:
                    keep = j
                    break
            if keep:
                strip = strip[keep:]
            m = len(strip)
            if m < 2:
                continue

            xs, ys = [], []
            for (gx, _a, r, _age) in strip:
                xs += [gx.x - r * 0.20, gx.x + r * 1.12]
                ys += [gx.y - r * 1.12, gx.y + r * 1.12]
            minx, maxx = int(min(xs)) - 2, int(max(xs)) + 2
            miny, maxy = int(min(ys)) - 2, int(max(ys)) + 2
            w, h = maxx - minx, maxy - miny
            if w <= 2 or h <= 2 or w > 1400 or h > 1400:
                continue
            buf = _scratch(w, h)

            def polar(cx, cy, ang, rad):
                return (int(cx + math.cos(ang) * rad) - minx,
                        int(cy + math.sin(ang) * rad) - miny)

            for j in range(m - 1):
                (g0, a0, r0, age0) = strip[j]
                (g1, a1, r1, _age1) = strip[j + 1]
                da = self._ang_delta(a1, a0)
                if abs(da) < 0.02:
                    continue
                fade = max(0.0, 1.0 - age0 / self.life)
                rank = (j + 1) / float(m)
                spread = min(1.0, 0.34 / max(0.05, abs(da)))
                k = (rank ** 2) * fade * self.width_boost * spread
                if k <= 0.012:
                    continue
                thin = 0.05 + 0.075 * rank
                steps = max(1, min(8, int(abs(da) / self.ARC_STEP) + 1))
                outer, inner, cout, cin, glint = [], [], [], [], []
                for q in range(steps + 1):
                    f = q / float(steps)
                    aa = a0 + da * f
                    rr = (r0 + (r1 - r0) * f) * 0.97   # tetap di DALAM ujung
                    ri = rr * (1.0 - thin)
                    rc = rr * (1.0 - thin * 0.40)
                    outer.append(polar(g1.x, g1.y, aa, rr))
                    inner.append(polar(g1.x, g1.y, aa, ri))
                    cout.append(polar(g1.x, g1.y, aa, rr * 0.985))
                    cin.append(polar(g1.x, g1.y, aa, rc))
                    glint.append(polar(g1.x, g1.y, aa, rr))
                # wash lebar: sengaja LEMAH (0.62x) supaya tidak pernah
                # menutupi badan; yang membaca bentuknya adalah inti + glint
                a_edge = int(base_alpha * k * 0.62)
                if a_edge > 5:
                    pygame.draw.polygon(buf, (*edge, a_edge),
                                        outer + inner[::-1])
                a_core = int((base_alpha + 96) * k)
                if a_core > 8:
                    pygame.draw.polygon(buf, (*core, min(255, a_core)),
                                        cout + cin[::-1])
                a_tip = int(235 * k)
                if a_tip > 14:
                    pygame.draw.lines(buf, (*tip_col, min(255, a_tip)),
                                      False, glint, 2 if k > 0.78 else 1)
            surface.blit(buf, (minx, miny))

    @staticmethod
    def _ang_delta(a_new, a_old):
        """Selisih sudut terdekat (-pi..pi); tanda = arah tebasan."""
        return (a_new - a_old + math.pi) % (2.0 * math.pi) - math.pi

    # ------------------------------------------------------------------
    def draw(self, surface):
        """Dua pita: bilah belakang lebih dulu (lebih redup), lalu depan."""
        if self.points_back:
            self._ribbon(surface, self.points_back, P["steel_dark"],
                         self.color_back, P["steel_edge"], 44)
        if self.points:
            self._ribbon(surface, self.points, self.color_edge,
                         self.color_core, P["fx_white"], 88)



# ============================================================================
# 7.  IMPACT FX
# ============================================================================

class ImpactFX:
    """Satu kejadian benturan: flash, shockwave berarah, debris, serpihan.

    ``kind`` memilih bahasa visual supaya setiap serangan terasa berbeda:

        ``blade`` — tebasan baja: shockave mendarah + serpihan bilah
        ``mana``  — Mana Break: cincin patah + retakan zigzag
        ``ward``  — Counterspell: kubah heksagon memancar keluar
        ``void``  — Mana Void: pilar runtuh + serpihan rune berjatuhan
    """

    __slots__ = ("x", "y", "angle", "power", "age", "duration", "crit",
                 "active", "color", "kind", "seed", "ground")

    def __init__(self, x, y, angle=0.0, power=1.0, crit=False,
                 kind="blade", ground=0.0, seed=None):
        self.x = float(x)
        self.y = float(y)
        self.angle = float(angle)
        self.power = max(0.35, min(2.6, float(power)))
        self.age = 0.0
        self.duration = 0.30 + 0.11 * min(2.0, self.power)
        self.crit = bool(crit)
        self.active = True
        self.kind = kind if kind in ("blade", "mana", "ward", "void") \
            else "blade"
        self.ground = float(ground)
        self.seed = random.randint(0, 9999) if seed is None else int(seed)
        self.color = P["fx_hot"] if not crit else P["brass_hot"]

    # ------------------------------------------------------------------
    def update(self, dt):
        self.age += dt
        if self.age >= self.duration:
            self.active = False
        return self.active

    # ------------------------------------------------------------------
    def _ramp(self):
        if self.kind == "blade":
            return P["steel_dark"], P["steel_edge"], P["steel_hot"]
        if self.kind == "ward":
            return P["fx_darkest"], P["fx_light"], P["fx_hot"]
        if self.kind == "void":
            return P["fx_dark"], P["fx_mid"], P["fx_hot"]
        return P["fx_dark"], P["fx_bright"], P["fx_white"]

    # ------------------------------------------------------------------
    def draw(self, surface):
        if not self.active:
            return
        t = min(1.0, self.age / self.duration)
        inv = 1.0 - t
        x, y = int(self.x), int(self.y)
        pw = self.power
        deg = math.degrees(self.angle)
        dark, mid, hot = self._ramp()

        # ── 1. FLASH: bintang 8 sisi, bukan bola putih ───────────────
        if t < 0.24:
            ft = 1.0 - t / 0.24
            gr = int((5 + 10 * pw) * (0.5 + 0.5 * ft)) // 2 * 2 + 2
            if glow_allowed():
                surface.blit(glow_surface(gr, hot, 0.55 * ft),
                             (x - gr, y - gr),
                             special_flags=pygame.BLEND_RGB_ADD)
            ln = (10 + 21 * pw) * ft          # pendek & tebal, bukan benang
            buf = _scratch(int(ln * 2 + 8), int(ln * 2 + 8))
            c = int(ln + 4)
            for i in range(4):
                a = self.angle + k * math.pi / 4
                L = ln if k % 2 == 0 else ln * 0.40
                # garis panjang 2 px, garis pendek 1 px: tetap terbaca
                # sebagai pecahan cahaya, bukan cross-hair vektor
                pygame.draw.line(buf, (*P["fx_white"], int(232 * ft)),
                                 (c, c),
                                 (c + int(math.cos(a) * L),
                                  c + int(math.sin(a) * L)),
                                 2 if k % 2 == 0 else 1)
            surface.blit(buf, (x - c, y - c))

        # ── 2. SHOCKWAVE: elips gepeng TEGAK LURUS arah tebasan ──────
        rr = int((8 + 44 * pw) * (0.25 + 1.0 * t)) // 3 * 3
        th = max(1, int(4 * inv * pw))
        a = int(210 * inv * inv)
        if a > 6 and rr > 4:
            if self.kind == "blade":
                er = ellipse_ring_surface(rr, max(3, int(rr * 0.55)), th,
                                          mid, deg)
            else:
                er = ellipse_ring_surface(rr, max(3, int(rr * 0.8)), th,
                                          mid, 0)
            er.set_alpha(a)
            surface.blit(er, (x - er.get_width() // 2,
                              y - er.get_height() // 2))
            rr2 = int(rr * 0.56)
            if rr2 > 4:
                er2 = ring_surface(rr2, max(1, th - 1), hot, 255,
                                   dashed=8 if self.kind != "blade" else 0)
                er2.set_alpha(int(a * 0.8))
                surface.blit(er2, (x - er2.get_width() // 2,
                                   y - er2.get_height() // 2))

        # ── 3. SPOKE DEBRIS: garis radial memanjang keluar ──────────
        if t < 0.58:
            st = 1.0 - t / 0.58
            r0 = int((6 + 19 * pw) * (0.3 + 1.05 * t))
            for i in range(4):
                ang = self.angle + k * math.pi / 4 + 0.19
                L = (7 + 14 * pw) * st * (1.0 if k % 2 else 0.55)
                pygame.draw.line(
                    surface, _clamp_color(_mix(dark, mid, st)),
                    (x + int(math.cos(ang) * r0),
                     y + int(math.sin(ang) * r0)),
                    (x + int(math.cos(ang) * (r0 + L)),
                     y + int(math.sin(ang) * (r0 + L))),
                    2 if k % 2 else 1)

        # ── 4. SLASH FRAGMENT: 3 busur pecah searah pukulan ──────────
        if t < 0.52 and self.kind in ("blade", "mana"):
            st = 1.0 - t / 0.52
            span = 0.5 + 0.5 * pw
            base_r = int(11 + 28 * pw * (0.4 + t))
            buf = _scratch(base_r * 2 + 16, base_r * 2 + 16)
            c = base_r + 8
            for k in (-1, 0, 1):
                ang0 = self.angle - span / 2 + k * 0.13
                ang1 = ang0 + span
                rad = base_r - abs(k) * 5
                rect = pygame.Rect(c - rad, c - rad, rad * 2, rad * 2)
                col = P["fx_white"] if k == 0 else mid
                try:
                    pygame.draw.arc(buf, (*col, int(225 * st)), rect,
                                    -ang1, -ang0, 3 if k == 0 else 2)
                except (ValueError, pygame.error):
                    pass
            surface.blit(buf, (x - c, y - c))

        # ── 5. RETAKAN ZIGZAG (mana / void) ──────────────────────────
        if t < 0.62 and self.kind in ("mana", "void"):
            st = 1.0 - t / 0.62
            n = 5 if self.kind == "mana" else 7
            for i in range(n):
                base = (self.seed * 0.37) + i * math.tau / n
                length = (16 + 20 * pw) * (0.6 + 0.55 * t)
                px, py = x, y
                ang = base
                for seg in range(3):
                    ang += (_hash01(self.seed + i * 13 + seg) - .5) * 1.1
                    nx = px + math.cos(ang) * (length / 3.0)
                    ny = py + math.sin(ang) * (length / 3.0)
                    pygame.draw.line(surface,
                                     _clamp_color(_mix(dark, hot, 1 - seg * .3)),
                                     (int(px), int(py)), (int(nx), int(ny)),
                                     max(1, 3 - seg))
                    px, py = nx, ny

        # ── 6. KUBAH WARDA (E) — heksagon memancar ──────────────────
        if self.kind == "ward" and t < 0.7:
            st = 1.0 - t / 0.7
            rad = int((14 + 26 * pw) * (0.4 + 0.9 * t))
            for k in range(6):
                a0 = self.angle + k * math.tau / 6 + t * 0.7
                a1 = a0 + math.tau / 6 * 0.62
                x0 = x + math.cos(a0) * rad
                y0 = y + math.sin(a0) * rad * 0.72
                x1 = x + math.cos(a1) * rad
                y1 = y + math.sin(a1) * rad * 0.72
                pygame.draw.line(surface, _clamp_color(mid),
                                 (int(x0), int(y0)), (int(x1), int(y1)),
                                 max(1, int(3 * st) + 1))

        # ── 7. INTI benturan ─────────────────────────────────────────
        if t < 0.40:
            st = 1.0 - t / 0.40
            sz = int((5 + 9 * pw) * (0.5 + 0.5 * st)) // 2 * 2 + 2
            s = spark_surface(sz, self.color if self.crit else hot)
            s.set_alpha(int(255 * st))
            surface.blit(s, (x - sz - 1, y - sz - 1))


# ============================================================================
# 8.  PROJECTILE SYSTEM  —  MANA BREAK
# ============================================================================

class GornakProjectile:
    """Bolt Mana Break — modular, vektor, delta-time.

    Kontrak atribut: ``position, velocity, speed, damage, lifetime,
    target, radius, rotation, trail, particles, active`` (plus
    ``homing``, ``state``, ``kind`` untuk lifecycle-nya).

    Lifecycle: SPAWN -> TRAVEL -> TRAIL -> HIT -> IMPACT FX -> DESTROY

    Proyektil di lapisan FX bersifat VISUAL (``damage=0`` default): damage
    Mana Break tetap dihitung sistem gameplay seperti semula, jadi tidak
    ada perubahan angka keseimbangan — hanya pembawaannya yang jadi nyata.
    """

    STATE_TRAVEL = "travel"
    STATE_IMPACT = "impact"
    STATE_DEAD = "dead"

    def __init__(self, x, y, tx, ty, speed=BOLT_SPEED, damage=0,
                 target=None, radius=7.0, homing=7.5, kind="mana",
                 particles=None, on_impact=None, ground=0.0):
        self.position = pygame.Vector2(x, y)
        self.spawn_pos = pygame.Vector2(x, y)
        d = pygame.Vector2(tx - x, ty - y)
        if d.length_squared() < 1e-6:
            d = pygame.Vector2(1.0, 0.0)
        self.velocity = d.normalize() * float(speed)
        self.speed = float(speed)
        self.damage = damage
        self.lifetime = 0.0
        self.max_lifetime = 1.9
        self.target = target
        self.radius = float(radius)
        self.rotation = math.atan2(self.velocity.y, self.velocity.x)
        self.trail = []                      # [[Vector2, umur], ...]
        self.trail_life = 0.19
        self.particles = particles
        self.active = True
        self.state = self.STATE_TRAVEL
        self.kind = kind
        self.homing = float(homing)
        self.on_impact = on_impact
        self.ground = float(ground)
        self._impact_age = 0.0
        self._emit_acc = 0.0
        self._stamp = 0.0                    # pengatur jarak after-image
        self.hit_pos = pygame.Vector2(tx, ty)
        self.seed = random.randint(0, 9999)

    # ------------------------------------------------------------------
    def kill(self, x=None, y=None):
        """Masuk fase IMPACT di posisi tertentu (dipanggil saat kena / habis)."""
        if self.state != self.STATE_TRAVEL:
            return
        self.state = self.STATE_IMPACT
        self.hit_pos.update(self.position if x is None
                            else pygame.Vector2(x, y))
        self._impact_age = 0.0
        if self.on_impact:
            try:
                self.on_impact(self)
            except Exception:                # pragma: no cover
                pass

    # ------------------------------------------------------------------
    def update(self, dt):
        """Kembalikan False kalau proyektil harus dibuang."""
        if self.state == self.STATE_DEAD:
            return False

        if self.state == self.STATE_IMPACT:
            self._impact_age += dt
            self._age_trail(dt)
            if self._impact_age > 0.26 and not self.trail:
                self.state = self.STATE_DEAD
                self.active = False
                return False
            return True

        self.lifetime += dt
        if self.lifetime > self.max_lifetime:
            self.kill()
            return True                      # satu frame untuk pop-nya

        # ── homing halus ke target yang masih hidup ──────────────────
        tgt = self.target
        if tgt is not None and getattr(tgt, "alive", False):
            to = pygame.Vector2(float(tgt.x), float(tgt.y)) - self.position
            if to.length_squared() > 1.0:
                desired = to.normalize() * self.speed
                self.velocity += (desired - self.velocity) \
                    * min(1.0, self.homing * dt)
                if self.velocity.length_squared() > 1e-6:
                    self.velocity.scale_to_length(self.speed)
        self.rotation = math.atan2(self.velocity.y, self.velocity.x)

        # ── catat trail, lalu maju ───────────────────────────────────
        self.trail.append([pygame.Vector2(self.position), 0.0])
        if len(self.trail) > 14:
            self.trail.pop(0)
        self._age_trail(dt)
        self.position += self.velocity * dt

        # ── emisi partikel ekor (rate-limited, jangan tiap frame) ───
        ps = self.particles
        if ps is not None:
            self._emit_acc += dt
            if self._emit_acc >= 0.03:
                self._emit_acc = 0.0
                ang = self.rotation + math.pi + (random.random() - .5) * 1.2
                spd = random.uniform(24, 78)
                ps.spawn(self.position.x, self.position.y,
                         math.cos(ang) * spd, math.sin(ang) * spd,
                         random.uniform(0.14, 0.3), random.uniform(1.5, 3.2),
                         P["fx_bright"] if random.random() < .5
                         else P["fx_light"],
                         color_end=P["fx_dark"], drag=3.0, shape="pixel",
                         additive=True)

        # ── tumbukan dengan target ───────────────────────────────────
        if tgt is not None and getattr(tgt, "alive", False):
            hit_r = self.radius + float(getattr(tgt, "radius", 12)) + 4.0
            if self.position.distance_squared_to(
                    pygame.Vector2(float(tgt.x), float(tgt.y))) \
                    <= hit_r * hit_r:
                self.kill(tgt.x, tgt.y)
        return True

    def _age_trail(self, dt):
        for s in self.trail:
            s[1] += dt
        if self.trail:
            self.trail = [s for s in self.trail if s[1] < self.trail_life]

    # ------------------------------------------------------------------
    def draw(self, surface):
        """After-image ter-stempel -> bayangan -> bolt -> (impact pop)."""
        # ── after-image: stempel pada JARAK tetap (ciri pixel-art) ──
        n = len(self.trail)
        if n >= 2:
            step = 9.0
            ux, uy = math.cos(self.rotation), math.sin(self.rotation)
            for i in range(n - 1, -1, -1):
                pv, age = self.trail[i]
                fade = max(0.0, 1.0 - age / self.trail_life)
                d = self.spawn_pos.distance_to(pv)
                if (int(d / step) % 2) or fade <= 0.05:
                    continue
                a = int(150 * fade)
                ln = max(2, int(self.radius * (1.3 - 0.6 * fade)))
                _shard_poly(surface, pv.x, pv.y, self.rotation, ln,
                            max(1, int(self.radius * .45)), P["fx_dark"], a)
                pygame.draw.line(surface, _clamp_color(P["fx_mid"]),
                                 (int(pv.x - ux * ln), int(pv.y - uy * ln)),
                                 (int(pv.x + ux * ln * .4),
                                  int(pv.y + uy * ln * .4)),
                                 max(1, int(self.radius * .5)))

        if self.state == self.STATE_IMPACT:
            return

        draw_mana_bolt(surface, self.position.x, self.position.y,
                       self.rotation, age=int(self.lifetime * 60),
                       crit=False, radius=self.radius, spin_seed=self.seed)

    # ------------------------------------------------------------------
    def draw_impact(self, surface):
        """Sisa cahaya sesaat setelah bolt pecah (fase IMPACT)."""
        if self.state != self.STATE_IMPACT:
            return
        t = min(1.0, self._impact_age / 0.26)
        a = int(220 * (1.0 - t))
        if a <= 5:
            return
        x, y = int(self.hit_pos.x), int(self.hit_pos.y)
        r = int((9 + 22 * t) * 1)
        ring = ring_surface(r, max(1, int(3 * (1 - t))), P["fx_light"], 255,
                            dashed=9)
        ring.set_alpha(a)
        surface.blit(ring, (x - ring.get_width() // 2,
                            y - ring.get_height() // 2))
        glint = spark_surface(max(3, int(9 * (1 - t))), P["fx_white"])
        glint.set_alpha(a)
        surface.blit(glint, (x - glint.get_width() // 2,
                             y - glint.get_height() // 2))


class ProjectileSystem:
    """Manajer proyektil: spawn / update / draw / auto-cleanup, dengan cap."""

    def __init__(self, particles=None, cap=MAX_PROJECTILES):
        self.projectiles = []
        self.particles = particles
        self.cap = int(cap)

    def count(self):
        return len(self.projectiles)

    def list(self):
        """Proyektil aktif (read-only) — dipakai debug overlay & tes."""
        return tuple(self.projectiles)

    def clear(self):
        self.projectiles.clear()

    def spawn(self, x, y, tx, ty, **kw):
        """Buat proyektil baru; None kalau sudah mentok cap."""
        if len(self.projectiles) >= self.cap:
            return None
        kw.setdefault("particles", self.particles)
        pr = GornakProjectile(x, y, tx, ty, **kw)
        self.projectiles.append(pr)
        return pr

    def update(self, dt):
        if not self.projectiles:
            return
        self.projectiles = [p for p in self.projectiles if p.update(dt)]

    def draw(self, surface):
        for p in self.projectiles:
            p.draw(surface)
            p.draw_impact(surface)


# ============================================================================
# 9.  SKILL FX  —  lifecycle Q / W / E / R
# ============================================================================

class SkillFX:
    """Efek skill Gornak dengan lifecycle bertahap.

    CAST -> CHARGE -> RELEASE -> TRAVEL/AREA -> IMPACT -> AFTER -> FADE

    Yang digambar di sini adalah bagian yang TIDAK boleh ikut ter-cache:
    mote tersedot, shockwave tanah, retakan, pilar, arus drain, bara.
    Cincin telegraph geometris (E 100 px / R 180 px dunia) tetap milik
    renderer, jadi tidak ada satu pun bentuk yang digambar dua kali.
    """

    #: (charge, release, area, impact, after) dalam DETIK
    TIMELINE = {
        "q": (0.20, 0.10, 0.20, 0.12, 0.16),
        "w": (0.10, 0.10, 0.16, 0.08, 0.08),
        "e": (0.30, 0.12, 0.36, 0.14, 0.24),
        "r": (0.46, 0.20, 0.46, 0.22, 0.38),
    }

    #: (warna gelap, warna terang) per skill — identitas tiap kemampuan
    TINT = {
        "q": ((58, 19, 108), (221, 161, 255)),      # Mana Break
        "w": ((34, 20, 46), (164, 170, 196)),       # Blink: dingin, minim sihir
        "e": ((96, 100, 128), (186, 111, 241)),     # Counterspell: baja+ungu
        "r": ((24, 5, 44), (245, 210, 255)),         # Mana Void: violet pekat
    }

    RADIUS = WORLD_RADIUS

    def __init__(self, kind, x, y, particles=None, radius=None,
                 aim=(0.0, 0.0), ground=0.0, facing=1):
        self.kind = kind if kind in self.TIMELINE else "q"
        self.x = float(x)
        self.y = float(y)
        self.particles = particles
        self.radius = float(radius if radius is not None
                            else self.RADIUS.get(self.kind, 60.0))
        self.aim = (float(aim[0]) - x, float(aim[1]) - y)
        self.ground = float(ground)
        self.facing = 1 if (facing or 1) >= 0 else -1
        tl = self.TIMELINE[self.kind]
        self.t_charge = tl[0]
        self.t_release = self.t_charge + tl[1]
        self.t_area = self.t_release + tl[2]
        self.t_impact = self.t_area + tl[3]
        self.total = min(self.t_impact + tl[4],
                         float(SKILL_TOTAL.get(self.kind, 1.0)))
        self.age = 0.0
        self.active = True
        self.phase = "cast"
        self._released = False
        self._impacted = False
        self._emit = 0.0
        self.seed = random.randint(0, 9999)

    # ------------------------------------------------------------------
    @property
    def aim_angle(self):
        ax, ay = self.aim
        if abs(ax) < 0.01 and abs(ay) < 0.01:
            return 0.0
        return math.atan2(ay, ax)

    # ------------------------------------------------------------------
    def _set_phase(self):
        a = self.age
        if a < self.t_charge:
            self.phase = "charge"
        elif a < self.t_release:
            self.phase = "release"
        elif a < self.t_area:
            self.phase = "area"
        elif a < self.t_impact:
            self.phase = "impact"
        else:
            self.phase = "fade"

    # ------------------------------------------------------------------
    def update(self, dt):
        self.age += dt
        self._set_phase()
        if self.age >= self.total:
            self.active = False
            return False
        ps = self.particles
        if ps is None:
            return True
        kind = self.kind
        R = self.radius
        ang = self.aim_angle

        # CHARGE: mote disedot MASUK (bukan berputar tanpa arah)
        if self.phase == "charge":
            self._emit += dt
            gap = 0.05 if kind != "r" else 0.028
            while self._emit >= gap:
                self._emit -= gap
                a = random.random() * math.tau
                rr = R * random.uniform(0.55, 1.05)
                sx = self.x + math.cos(a) * rr
                sy = self.y + math.sin(a) * rr * 0.5 + self.ground * 0.55
                life = random.uniform(0.24, 0.44)
                ps.spawn(sx, sy,
                         (self.x - sx) / life * 0.85,
                         (self.y + self.ground * 0.4 - sy) / life * 0.7,
                         life, random.uniform(1.5, 3.2),
                         self.TINT[kind][1], color_end=self.TINT[kind][0],
                         drag=0.4, shape="pixel", additive=True,
                         fade_pow=0.6, layer="back")
            if kind == "r":
                # R: tanah di bawah Gornak retak + puing terangkat
                ps.burst(self.x, self.y + self.ground, 4,
                         speed=(20, 70), life=(0.3, 0.6), size=(2, 4),
                         colors=(P["ash"], P["smoke"], self.TINT[kind][0]),
                         gravity=-40.0, drag=1.4, shape="dust",
                         layer="back")

        # RELEASE: pancaran keluar + debu
        elif self.phase == "release" and not self._released:
            self._released = True
            if kind == "q":
                ps.burst(self.x + math.cos(ang) * 6,
                         self.y + math.sin(ang) * 6, 6,
                         speed=(140, 340), life=(0.16, 0.34), size=(2, 4),
                         colors=(P["fx_white"], self.TINT["q"][1],
                                 P["fx_light"]),
                         spread=1.15, direction=ang, drag=3.4,
                         shape="streak", additive=True)
            elif kind == "w":
                ps.burst(self.x, self.y + self.ground * 0.7, 7,
                         speed=(90, 260), life=(0.2, 0.46), size=(2, 5),
                         colors=(P["dust"], P["ash"], self.TINT["w"][1]),
                         spread=math.tau, gravity=210.0, drag=1.6,
                         shape="dust", layer="back")
            else:
                ps.burst(self.x, self.y + self.ground * 0.35, 8,
                         speed=(120, 320), life=(0.2, 0.5), size=(2, 5),
                         colors=(self.TINT[kind][1], P["fx_light"],
                                 P["brass_hot"]),
                         spread=math.tau, gravity=120.0, drag=1.8,
                         shape="shard", rotation_speed=(-15.0, 15.0))

        # AREA: bara / mote naik pelan di sepanjang ring
        elif self.phase == "area":
            self._emit += dt
            gap = 0.075 if kind != "r" else 0.035
            while self._emit >= gap:
                self._emit -= gap
                a = random.random() * math.tau
                rr = R * random.uniform(0.25, 1.0)
                ps.spawn(self.x + math.cos(a) * rr,
                         self.y + self.ground + math.sin(a) * rr * 0.36,
                         random.uniform(-16, 16), random.uniform(-52, -20),
                         random.uniform(0.4, 0.9), random.uniform(1.5, 3.2),
                         self.TINT[kind][1], color_end=self.TINT[kind][0],
                         drag=0.5, shape="pixel", additive=True)
            if kind == "r":
                # arus hisap dari sekitar ke dada Gornak
                ps.stream(self.x + math.cos(ang) * R * 0.8,
                          self.y + self.ground * 0.4 + math.sin(ang) * R * .3,
                          self.x, self.y - 6, 6,
                          life=(0.3, 0.5), size=(2, 3),
                          colors=(self.TINT["r"][1], P["fx_light"],
                                  self.TINT["r"][0]),
                          bow=22.0)

        # IMPACT: retakan + serpihan jatuh
        elif self.phase == "impact" and not self._impacted:
            self._impacted = True
            ps.burst(self.x, self.y + self.ground * 0.2, 6,
                     speed=(90, 240), life=(0.28, 0.6), size=(2, 5),
                     colors=(self.TINT[kind][1], P["steel_mid"], P["ash"]),
                     gravity=430.0, drag=1.0, shape="shard",
                     rotation_speed=(-13.0, 13.0))
        return True

    # ------------------------------------------------------------------
    def draw_ground(self, surface):
        """Lapisan BAWAH karakter: kabut tanah, cincin tekan, retakan."""
        if not self.active:
            return
        dark, hot = self.TINT[self.kind]
        a = self.age
        R = self.radius
        gy = int(self.y + self.ground)
        x = int(self.x)

        # kabut cahaya di tanah — memberi kedalaman, bukan garis saja
        t_all = min(1.0, a / max(0.05, self.total))
        haze = int(R * (0.85 + 0.2 * math.sin(a * 4.2))) // 8 * 8
        power = round(0.32 * (1.0 - abs(t_all - 0.35) * 1.5) / 0.05) * 0.05
        if power > 0.02 and haze >= 8 and glow_allowed():
            hs = ground_glow_surface(haze, dark, power)
            surface.blit(hs, (x - hs.get_width() // 2,
                              gy - hs.get_height() // 2),
                         special_flags=pygame.BLEND_RGB_ADD)

        # gelombang tekan yang MERANGSANG keluar sepanjang fase area
        if self.phase in ("release", "area", "impact"):
            span = max(0.001, self.t_impact - self.t_release)
            t = min(1.0, (a - self.t_release) / span)
            rr = int(self.ground_ring_radius(t))
            al = int(190 * (1.0 - t))
            if rr > 6 and al > 6:
                er = ellipse_ring_surface(rr, max(2, int(rr * 0.34)),
                                          max(1, int(3 * (1 - t)) + 1),
                                          hot, 0)
                er.set_alpha(al)
                surface.blit(er, (x - er.get_width() // 2,
                                   gy - er.get_height() // 2))
            if self.kind in ("e", "r"):
                self._ground_cracks(surface, x, gy, R, hot,
                                    int(180 * (1.0 - t)), t)

    def ground_ring_radius(self, t):
        """Radius gelombang tekan di tanah (world px) untuk umur fraksi t."""
        base = self.radius if self.kind in ("e", "r") else self.radius * 1.6
        return base * (0.35 + 0.75 * t)

    def _ground_cracks(self, surface, cx, cy, R, color, alpha, t):
        if alpha <= 6:
            return
        n = 6
        for i in range(n):
            base = _hash01(self.seed + i * 31) * math.tau
            length = R * (0.42 + _hash01(self.seed + i * 77) * 0.4) * (0.7 + t)
            px, py = cx, cy
            ang = base
            for seg in range(3):
                ang += (_hash01(self.seed + i * 17 + seg) - 0.5) * 0.85
                nx = px + math.cos(ang) * (length / 3.0)
                ny = py + math.sin(ang) * (length / 3.0) * 0.34
                pygame.draw.line(surface, _clamp_color(color),
                                 (int(px), int(py)), (int(nx), int(ny)),
                                 max(1, 3 - seg))
                px, py = nx, ny

    # ------------------------------------------------------------------
    def draw_front(self, surface):
        """Lapisan ATAS karakter: pilar, kubah, sapuan segel, arus hisap."""
        if not self.active:
            return
        dark, hot = self.TINT[self.kind]
        a = self.age
        x, y = int(self.x), int(self.y)
        kind = self.kind

        if kind == "q":
            self._draw_q(surface, x, y, a, hot)
        elif kind == "w":
            self._draw_w(surface, x, y, a, hot)
        elif kind == "e":
            self._draw_e(surface, x, y, a, hot)
        else:
            self._draw_r(surface, x, y, a, hot)

    # -- Q  Mana Break: sapuan segel di ujung bilah -> bolt -----------
    def _draw_q(self, surface, x, y, a, hot):
        if a < self.t_charge:
            t = a / max(0.001, self.t_charge)
            rr = int((10 + 12 * (1.0 - t)) * 1)
            al = int(210 * (0.4 + 0.6 * t))
            ring = ring_surface(max(3, rr), 2, hot, 255, dashed=8)
            ring.set_alpha(al)
            surface.blit(ring, (x - ring.get_width() // 2,
                                y - ring.get_height() // 2))
            self._chevrons(surface, x, y, self.aim_angle,
                           (16 + 10 * t), int(200 * t), hot, 3)
        elif a < self.t_release:
            t = (a - self.t_charge) / max(0.001,
                                          self.t_release - self.t_charge)
            s = spark_surface(max(3, int(10 + 8 * (1 - t))), P["fx_white"])
            s.set_alpha(int(255 * (1 - t * 0.35)))
            surface.blit(s, (x - s.get_width() // 2, y - s.get_height() // 2))

    # -- W  Blink: afterglow + cincin datang --------------------------
    def _draw_w(self, surface, x, y, a, hot):
        t = min(1.0, a / max(0.001, self.total))
        for k in range(2):
            rr = int((12 + 26 * t) + k * 8)
            al = int(170 * (1 - t)) * (1 if k == 0 else 0)
            if al <= 4:
                continue
            ring = ring_surface(rr, 2, hot, 255, dashed=10)
            ring.set_alpha(al)
            surface.blit(ring, (x - ring.get_width() // 2,
                                y - ring.get_height() // 2))
        # streak horizontal: "terpotong ruang", bukan ledakan
        if t < 0.6:
            st = 1.0 - t / 0.6
            for i in range(5):
                off = (_hash01(self.seed + i) - 0.5) * 26
                ln = 12 + 26 * st
                pygame.draw.line(surface, _clamp_color(hot),
                                 (x - int(ln), int(y + off)),
                                 (x - int(ln * 0.35), int(y + off)),
                                 2 if i % 2 else 1)

    # -- E  Counterspell: kubah heksagon + cincin memancar ────────────
    def _draw_e(self, surface, x, y, a, hot):
        t = min(1.0, a / max(0.001, self.total))
        R = self.radius
        if self.phase == "charge":
            k = a / max(0.001, self.t_charge)
            self._hex_dome(surface, x, y - 4, R * (0.35 + 0.65 * k),
                           int(150 * k), hot, a)
        else:
            self._hex_dome(surface, x, y - 4, R * (1.0 - 0.12 * t),
                           int(200 * (1 - t)), hot, a)
            # pancaran keluar: 3 cincin konsetris terputus
            for i in range(3):
                rr = int(R * (0.5 + 0.28 * i) * (0.6 + 0.7 * t))
                al = int(150 * (1 - t)) - i * 25
                if al <= 5 or rr <= 4:
                    continue
                ring = ring_surface(rr, 2, hot, 255, dashed=8 + i * 3)
                ring.set_alpha(al)
                surface.blit(ring, (x - ring.get_width() // 2,
                                    y - 4 - ring.get_height() // 2))

    def _hex_dome(self, surface, cx, cy, radius, alpha, color, spin):
        if alpha <= 6 or radius < 6:
            return
        radius = int(radius)
        buf = _scratch(radius * 2 + 12, radius * 2 + 12)
        c = radius + 6
        n = 6
        pts = []
        for i in range(n):
            ang = spin * 1.1 + i * math.tau / n + math.tau / (n * 2)
            rr = radius * (1.0 if i % 2 == 0 else 0.88)
            pts.append((c + math.cos(ang) * rr, cy - c + math.sin(ang) * rr * 0.86))
        poly = [(int(px), int(c + py)) for px, py in pts]
        pygame.draw.polygon(buf, (*_clamp_color(color), alpha), poly)
        pygame.draw.polygon(buf, (*P["outline"], min(255, alpha + 20)),
                            [(px + 1, py + 1) for px, py in poly], 2)
        surface.blit(buf, (cx - c, cy - c))

    # -- R  Mana Void: arus hisap + shockwave (TANPA pilar cahaya) ────
    def _draw_r(self, surface, x, y, a, hot):
        R = self.radius
        if self.phase == "charge":
            # Pilar cahaya aktivasi DIBUANG. Kolom vertikal 40-128 px
            # yang berdiri tepat di sumbu badan menutupi Gornak selama
            # R di-cast; versi sebelumnya hanya dipersempit, tidak
            # dihapus, jadi karakter tetap tertelan. Fase charge kini
            # tidak menggambar lapisan ini sama sekali.
            return
        if self.phase == "release":
            t = (a - self.t_charge) / max(0.001,
                                          self.t_release - self.t_charge)
            # Pilar putih fase release juga dibuang (alasan sama).
            # Shockwave cincin di bawah tetap hidup sebagai penanda R.
            rr = int(R * (0.25 + 1.05 * t))
            if rr > 6:
                ring = ring_surface(rr, max(1, int(6 * (1 - t)) + 1),
                                    P["fx_white"], 255, dashed=0)
                ring.set_alpha(int(225 * (1 - t)))
                surface.blit(ring, (x - ring.get_width() // 2,
                                    y - ring.get_height() // 2))
        elif self.phase == "area":
            t = (a - self.t_release) / max(0.001,
                                           self.t_area - self.t_release)
            # rune ring berputar di radius gameplay (180 px dunia)
            self._rune_marks(surface, x, y - 6, R, hot,
                             int(160 - 70 * t), a * 2.1, 12)
            self._rune_marks(surface, x, y - 6, R * 0.78, P["fx_light"],
                             int(140 - 60 * t), -a * 1.5, 8)
            self._chevrons(surface, x, y - 6, self.aim_angle, R * 0.6,
                           int(140 * (1 - t)), hot, 2)
        else:
            t = min(1.0, (a - self.t_impact)
                     / max(0.001, self.total - self.t_impact))
            self._rune_marks(surface, x, y - 6, R * (1.0 - 0.2 * t),
                             P["fx_mid"], int(120 * (1 - t)), a * 1.2, 10)

    def _pillar(self, surface, cx, cy, height, width, alpha, color):
        if height < 6 or alpha <= 6:
            return
        width = max(2, int(width))
        buf = _scratch(width * 2 + 10, height + 10)
        w, h = buf.get_size()
        c = w // 2
        base = _clamp_color(color)
        # PENTING: blit di bawah memakai BLEND_RGB_ADD yang MENGABAIKAN
        # kanal alpha (lihat glow_surface). Intensitas tiap lapis harus
        # dikodekan sebagai RGB PREMULTIPLIED -- versi lama menggambar
        # RGB penuh + alpha samar, jadi pilar tampil sebagai berkas putih
        # jenuh selebar badan yang menelan karakter saat R di-cast.
        for i in range(3):
            k = max(0.0, min(1.0, (alpha / (i + 1)) / 255.0))
            col = (int(base[0] * k), int(base[1] * k), int(base[2] * k),
                   255)
            inset = i * 2
            pygame.draw.polygon(
                buf, col,
                [(c - width + inset, h - 2),
                 (c + width - inset, h - 2),
                 (c + max(1, width // 3), 2),
                 (c - max(1, width // 3), 2)])
        # bilah cahaya vertikal di tengah pilar (premultiplied juga)
        kc = max(0.0, min(1.0, min(255, alpha + 30) / 255.0))
        wc = _clamp_color(P["fx_white"])
        pygame.draw.line(buf, (int(wc[0] * kc), int(wc[1] * kc),
                               int(wc[2] * kc), 255),
                         (c, 2), (c, h - 2), max(1, width // 4))
        surface.blit(buf, (int(cx) - c, int(cy) - height),
                     special_flags=pygame.BLEND_RGB_ADD)

    def _rune_marks(self, surface, cx, cy, radius, color, alpha, rot, marks):
        if alpha <= 5 or radius < 6:
            return
        for i in range(marks):
            ang = rot + i * math.tau / marks
            px = cx + math.cos(ang) * radius
            py = cy + math.sin(ang) * radius * 0.30
            sz = 3 if i % 2 else 2
            buf = _scratch(sz * 2 + 6, sz * 2 + 6)
            c = sz + 3
            pygame.draw.polygon(buf, (*_clamp_color(color), alpha),
                                [(c, c - sz - 1), (c + sz + 1, c),
                                 (c, c + sz + 1), (c - sz - 1, c)])
            surface.blit(buf, (int(px) - c, int(py) - c))

    def _chevrons(self, surface, cx, cy, ang, dist, alpha, color, n):
        if alpha <= 6:
            return
        for k in range(n):
            d = dist * (0.55 + 0.45 * k)
            px = cx + math.cos(ang) * d
            py = cy + math.sin(ang) * d
            buf = _scratch(16, 16)
            ca, sa = math.cos(ang), math.sin(ang)
            ox, oy = -sa, ca
            pts = [(8 + ca * 5, 8 + sa * 5),
                   (8 - ca * 3 + ox * 4, 8 - sa * 3 + oy * 4),
                   (8 - ca * 1, 8 - sa * 1),
                   (8 - ca * 3 - ox * 4, 8 - sa * 3 - oy * 4)]
            pygame.draw.polygon(buf, (*_clamp_color(color), alpha), pts)
            surface.blit(buf, (int(px) - 8, int(py) - 8))


# ============================================================================
# 10.  ANIMATION STATE  (cermin ringan dari controller renderer)
# ============================================================================

#: Nama state animasi + prioritasnya (angka besar = lebih penting).
ANIM_PRIORITY = {
    "IDLE": 0,
    "WALK": 10,
    "RUN": 15,
    "CHARGE": 30,
    "CAST": 35,
    "ATTACK": 40,
    "SWING": 45,
    "SKILL": 50,
    "SPECIAL": 55,
    "HIT": 60,
    "HURT": 65,
    "DEATH": 100,
}

#: Fase timeline serangan (fraksi 0..1 dari durasi serangan).
ATTACK_PHASES = (
    ("ANTICIPATION", 0.00, 0.30),
    ("WINDUP",       0.30, 0.46),
    ("SWING",        0.46, 0.60),
    ("IMPACT",       0.60, 0.74),
    ("FOLLOW",       0.74, 0.90),
    ("RECOVERY",     0.90, 1.00),
)


def attack_phase(progress):
    """Nama fase serangan untuk progress 0..1."""
    p = max(0.0, min(1.0, float(progress)))
    for name, a, b in ATTACK_PHASES:
        if a <= p < b:
            return name
    return "RECOVERY"


# ============================================================================
# 11.  DIRECTOR — satu per unit Gornak
# ============================================================================

class GornakFXDirector:
    """Mengikat particle + trail + proyektil + impact + skill FX untuk
    satu unit Gornak (hero MAUPUN mini boss — kodenyma sama, hanya
    sumber transformasinya yang beda)."""

    def __init__(self, hero):
        self.hero = hero
        self.particles = ParticleSystem(MAX_PARTICLES)
        self.projectiles = ProjectileSystem(self.particles)
        self.trail = SwingTrail()
        self.impacts = []
        self.skills = []
        self.state = "IDLE"
        self.prev_state = "IDLE"
        self.state_time = 0.0
        self.anim_phase = "NONE"
        self.swing_active = False
        self.hit_flash = 0.0
        self.time = 0.0
        self.frames = 0
        self.last_x = float(getattr(hero, "x", 0.0))
        self.last_y = float(getattr(hero, "y", 0.0))
        self._swing_seen = False
        self._impact_frame_seen = False
        self._skill_seen = None
        self._last_hp = None
        self._death_done = False
        # peristiwa engine yang sudah dikonsumsi (edge trigger)
        self._blink_seen = False
        self._void_seen = False
        self.void_screen = None       # pusat R di layar, untuk overlay debug

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def on_swing_start(self, x, y, facing):
        """Awal ayunan: trail di-reset + debu antisipasi di kaki."""
        self.trail.reset()
        self.trail.width_boost = 1.0
        self.swing_active = True
        gy = y + _ground_dy(self.hero)
        self.particles.burst(
            x + facing * 7, gy, 2,
            speed=(28, 92), life=(0.18, 0.4), size=(2, 4),
            colors=(P["dust"], P["ash"], P["smoke"]),
            spread=1.2, direction=math.pi if facing > 0 else 0.0,
            gravity=95.0, drag=2.6, shape="dust", layer="back")

    def on_swing_end(self):
        self.swing_active = False

    def on_swing_impact_frame(self, x, y, facing):
        """Sapu udara di frame IMPACT — feedback walau tidak kena apa-apa."""
        action, phase, ap = pose_of(self.hero)
        _g, tip = blade_points(self.hero, x, y, False)
        _gb, tip_b = blade_points(self.hero, x, y, True)
        ang = math.atan2(tip.y - _g.y, tip.x - _g.x) - math.pi / 2
        self.particles.burst(
            tip.x, tip.y, 3,
            speed=(110, 250), life=(0.1, 0.24), size=(1, 3),
            colors=(P["steel_hot"], P["fx_bright"], P["fx_light"]),
            spread=1.5, direction=ang, drag=3.6, shape="streak",
            additive=True)
        self.particles.burst(
            tip_b.x, tip_b.y, 4,
            speed=(70, 170), life=(0.09, 0.2), size=(1, 3),
            colors=(P["steel_edge"], P["fx_light"]),
            spread=1.4, direction=ang + math.pi, drag=3.4, shape="streak",
            additive=True)
        if self.hero is not None:
            self.impacts.append(ImpactFX(tip.x, tip.y, ang, 0.55, False,
                                         kind="blade", ground=0.0,
                                         seed=int(self.frames)))

    def on_cast(self, x, y, skill, aim=None):
        """Skill dilepas: SkillFX + guncangan + (Q) proyektil."""
        if len(self.skills) >= MAX_SKILLS:
            self.skills.pop(0)
        gy = _ground_dy(self.hero)
        G = _renderer()
        if aim is None:
            tgt = getattr(self.hero, "target", None)
            if tgt is not None and getattr(tgt, "alive", False):
                aim = (float(tgt.x), float(tgt.y))
            else:
                facing = 1 if getattr(self.hero, "direction", 1) >= 0 else -1
                aim = (x + facing * 90, y - 6)
        self.skills.append(SkillFX(skill, x, y, self.particles,
                                   aim=aim, ground=gy))
        heavy = skill == "r"
        if shake_allowed():
            _feel_shake(6.0 if not heavy else 13.0,
                        0.16 if not heavy else 0.40)
        if skill == "q":
            self.spawn_mana_break(x, y, aim)
        elif heavy and G is not None:
            # R: pilarnya lahir dari dada -> satu beat freeze
            _feel_hit_stop(0.036)
        self.particles.burst(x, y + gy * 0.4, 5,
                             speed=(60, 190), life=(0.2, 0.5), size=(2, 4),
                             colors=(SkillFX.TINT.get(skill, P["fx_dark"])[0],
                                     P["ash"], P["dust"]),
                             spread=math.tau, gravity=150.0, drag=2.0,
                             shape="dust", layer="back")

    def spawn_mana_break(self, x, y, aim):
        """Lepaskan bolt Mana Break dari UJUNG BILAH ke target."""
        action, phase, ap = pose_of(self.hero)
        _g, tip = blade_points(self.hero, x, y, False)
        tgt = getattr(self.hero, "target", None)
        if tgt is None or not getattr(tgt, "alive", False):
            tgt = None
        pr = self.projectiles.spawn(
            tip.x, tip.y, aim[0], aim[1],
            speed=BOLT_SPEED, damage=0, target=tgt, radius=7.0,
            kind="mana", ground=_ground_dy(self.hero),
            on_impact=lambda p: self.on_impact(p.hit_pos.x, p.hit_pos.y,
                                               p.rotation, 1.15, False,
                                               kind="mana"))
        if pr is not None:
            self.particles.burst(tip.x, tip.y, 3,
                                 speed=(90, 220), life=(0.12, 0.3),
                                 size=(1, 3),
                                 colors=(P["fx_white"], P["fx_bright"]),
                                 spread=1.9, direction=pr.rotation,
                                 drag=3.2, shape="spark", additive=True)
        return pr

    def on_impact(self, x, y, angle=0.0, power=1.0, crit=False,
                  kind="blade"):
        """Benturan mengenai target: flash, spark, debris, shake, hit-stop."""
        if len(self.impacts) >= MAX_IMPACTS:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(x, y, angle, power, crit, kind=kind))
        pw = min(2.0, max(0.35, float(power)))

        if kind == "blade":
            spark, edge, hot = P["steel_hot"], P["fx_light"], P["fx_white"]
        elif kind == "void":
            spark, edge, hot = P["fx_bright"], P["fx_mid"], P["fx_hot"]
        else:
            spark, edge, hot = P["fx_white"], P["fx_bright"], P["fx_light"]

        n = int(9 + 7 * pw) + (6 if crit else 0)
        self.particles.burst(
            x, y, n, speed=(120, 330 + 90 * pw), life=(0.16, 0.42),
            size=(2, 4), colors=(spark, hot, edge),
            spread=2.4, direction=angle, drag=3.6, shape="streak")
        self.particles.burst(
            x, y, int(5 + 3 * pw) + (4 if crit else 0),
            speed=(70, 200), life=(0.3, 0.66), size=(2, 5),
            colors=(edge, P["ash"], P["steel_mid"]),
            gravity=470.0, drag=1.1, shape="shard",
            rotation_speed=(-16.0, 16.0))
        if crit:
            self.particles.burst(
                x, y, 4, speed=(180, 380), life=(0.22, 0.5), size=(2, 4),
                colors=(P["brass_hot"], P["brass"], spark),
                spread=math.tau, gravity=120.0, drag=2.0, shape="spark",
                additive=True)

        if shake_allowed():
            _feel_shake(4.0 + 3.4 * pw + (3.0 if crit else 0.0),
                        0.17 + 0.08 * pw)
        _feel_hit_stop(0.036 + 0.019 * min(1.5, pw) + (0.014 if crit else 0.0))

    def on_hurt(self, amount=1.0):
        """Gornak terkena serangan: flash + percikan baja + debu jubah."""
        self.hit_flash = 0.16
        hx = float(getattr(self.hero, "x", 0.0))
        hy = float(getattr(self.hero, "y", 0.0))
        self.particles.burst(
            hx, hy - 8, 3, speed=(80, 210), life=(0.16, 0.34), size=(2, 4),
            colors=(P["steel_edge"], P["brass_hot"], P["fx_light"]),
            drag=3.0, shape="streak", additive=True)
        self.particles.burst(
            hx, hy + 6, 4, speed=(30, 90), life=(0.24, 0.5), size=(2, 5),
            colors=(P["robe"], P["smoke"]), gravity=200.0, drag=2.0,
            shape="dust", layer="back")

    def _watch_engine_events(self, x, y):
        """Reaksi terhadap state yang DITULIS engine, tanpa mengubahnya.

        Lapisan ini satu arah: hanya membaca field yang sudah ada di
        Hero/Boss/hero_skills (``blink_from_x``, ``mana_void_x``,
        ``active_skill_timer``), jadi tidak ada jalur yang bisa merusak
        damage, cooldown, atau timing skill. Yang dibaca di sini peristiwa
        yang tidak terbaca dari pose saja:

        * W - badan dipindah ke target dan meninggalkan bekas di titik
          asal; burst-nya harus di ``blink_from_x/y``, bukan di badan.
        * R - poros ledakan ada di ``mana_void_x/y`` (pusat AOE dunia),
          bukan di badan, dan dilepas di 60% durasi cast supaya shockwave
          jatuh bersamaan dengan damage-nya, bukan saat tombol ditekan.
        """
        h = self.hero
        skill = getattr(h, "active_skill", None)
        timer = int(getattr(h, "active_skill_timer", 0) or 0)

        # ── W: blink ────────────────────────────────────────────────
        ox = getattr(h, "blink_from_x", None)
        oy = getattr(h, "blink_from_y", None)
        if skill == "w" and ox and not self._blink_seen:
            self._blink_seen = True
            # world -> layar: kamera hanya menggeser (tidak ada zoom),
            # jadi delta dunia = delta layar.
            wx = x + (float(ox) - float(getattr(h, "x", 0.0)))
            wy = y + (float(oy or 0.0) - float(getattr(h, "y", 0.0)))
            self.on_blink(x, y, wx, wy)
        elif skill != "w":
            self._blink_seen = False

        # ── R: rilis Mana Void ──────────────────────────────────────
        if skill == "r":
            dur = max(1, int(SKILL_DUR.get("r", 90)))
            if timer and timer <= int(dur * 0.6) and not self._void_seen \
                    and getattr(h, "mana_void_x", 0):
                self._void_seen = True
                self.on_void_release(x, y)
        else:
            self._void_seen = False

    def on_void_release(self, x, y):
        """Ledakan ULT di PUSAT void: impact dunia + shake + hit-stop.

        Radius dibaca dari ``skill_range`` (180 di boss_data) supaya FX
        dan jendela damage tidak pernah berbeda angka.
        """
        h = self.hero
        vx = float(getattr(h, "mana_void_x", 0.0))
        vy = float(getattr(h, "mana_void_y", 0.0))
        r = max(40.0, float(getattr(h, "skill_range", 180) or 180))
        sx = x + (vx - float(getattr(h, "x", 0.0)))
        sy = y + (vy - float(getattr(h, "y", 0.0)))
        self.void_screen = (sx, sy, r)
        if len(self.impacts) >= MAX_IMPACTS:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(sx, sy, 0.0, 1.9, True, kind="void",
                                     ground=_ground_dy(h),
                                     seed=int(self.frames)))
        self.particles.burst(
            sx, sy, int(16 * particle_budget()),
            speed=(150, 420), life=(0.3, 0.72), size=(2, 6),
            colors=(P["fx_bright"], P["fx_hot"], P["fx_dark"]),
            spread=math.tau, gravity=260.0, drag=1.4, shape="shard",
            rotation_speed=(-13.0, 13.0))
        self.particles.burst(
            sx, sy + _ground_dy(h) * 0.6, 5,
            speed=(60, 170), life=(0.4, 0.8), size=(4, 9),
            colors=(P["smoke"], P["ash"]), gravity=-30.0, drag=1.0,
            shape="smoke", layer="back")
        if shake_allowed():
            _feel_shake(4.8, 0.42)
        _feel_hit_stop(0.040)

    def on_blink(self, x, y, old_x, old_y):
        """Blink mendarat: cincin kedatangan + puing ruang di titik asal."""
        gy = _ground_dy(self.hero)
        self.impacts.append(ImpactFX(x, y + gy * 0.5, 0.0, 0.9, False,
                                     kind="ward", seed=int(self.frames)))
        self.particles.burst(x, y + gy * 0.6, 6,
                             speed=(90, 240), life=(0.2, 0.5), size=(2, 5),
                             colors=(P["dust"], P["ash"], P["steel_edge"]),
                             spread=math.tau, gravity=240.0, drag=1.8,
                             shape="dust", layer="back")
        self.particles.stream(old_x, old_y, x, y, 12, life=(0.2, 0.4),
                              size=(2, 3),
                              colors=(P["fx_light"], P["fx_bright"],
                                      P["fx_mid"]), bow=14.0)
        if shake_allowed():
            _feel_shake(1.7, 0.12)

    def on_death(self, x, y):
        """Kematian: bilah jatuh, segel pecah, debu tanah naik sekali."""
        if self._death_done:
            return
        self._death_done = True
        gy = _ground_dy(self.hero)
        self.trail.reset()
        self.particles.clear()
        self.impacts.append(ImpactFX(x, y + gy * 0.35, -math.pi / 2, 2.2,
                                     True, kind="void", seed=7))
        self.particles.burst(x, y, 11, speed=(90, 320), life=(0.5, 1.1),
                             size=(2, 6),
                             colors=(P["fx_mid"], P["steel_mid"], P["robe"],
                                     P["brass"]),
                             spread=math.tau, gravity=430.0, drag=1.1,
                             shape="shard", rotation_speed=(-18.0, 18.0))
        self.particles.burst(x, y + gy, 8, speed=(40, 150),
                             life=(0.5, 1.0), size=(3, 7),
                             colors=(P["dust"], P["smoke"], P["ash"]),
                             spread=math.tau, gravity=-30.0, drag=1.5,
                             shape="dust", layer="back")
        if shake_allowed():
            _feel_shake(4.5, 0.42)

    # ------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------
    def _resolve_state(self):
        """State yang DIINGINKAN frame ini, dari controller renderer."""
        h = self.hero
        if not getattr(h, "alive", True):
            return "DEATH"
        if self.hit_flash > 0.0:
            return "HURT"
        skill = getattr(h, "active_skill", None)
        if skill:
            return "SPECIAL" if skill == "r" else "SKILL"
        if getattr(h, "_gnk_attack_active", False):
            ph = attack_phase(float(getattr(h, "_gnk_attack_progress", 0.0)))
            if ph in ("ANTICIPATION", "WINDUP"):
                return "CHARGE"
            if ph in ("SWING", "IMPACT"):
                return "SWING"
            return "ATTACK"
        if getattr(h, "_moving_cached", False):
            return "RUN" if float(getattr(h, "speed", 1.0)) >= 2.2 else "WALK"
        # Tidak ada sinyal keras -> ikut state resmi controller renderer
        # (idle/walk sudah dibedakan di sana, dan state "hening" seperti
        # transisi antar-pose tidak perlu ditebak dua kali).
        st = getattr(h, "_gnk_state", None)
        if st in ANIM_PRIORITY:
            return st
        return "IDLE"

    def _update_state(self, dt):
        want = self._resolve_state()
        if want != self.state:
            cur_p = ANIM_PRIORITY.get(self.state, 0)
            new_p = ANIM_PRIORITY.get(want, 0)
            if self.state != "DEATH" and (new_p >= cur_p
                                          or self.state_time > 0.05):
                self.prev_state = self.state
                self.state = want
                self.state_time = 0.0
        self.state_time += dt
        self.anim_phase = str(getattr(self.hero, "_gnk_attack_phase", None)
                              or "NONE")

    # ------------------------------------------------------------------
    def update(self, dt, x, y):
        """Satu langkah simulasi FX. ``x, y`` = posisi layar unit."""
        if dt <= 0.0:
            return
        self.time += dt
        self.frames += 1
        h = self.hero

        # ── damage masuk -> HURT ─────────────────────────────────────
        hp = getattr(h, "hp", None)
        if hp is not None:
            if self._last_hp is not None and hp < self._last_hp - 0.01:
                self.on_hurt((self._last_hp - hp)
                             / max(1.0, float(getattr(h, "max_hp", 1.0))))
            self._last_hp = hp
        if self.hit_flash > 0.0:
            self.hit_flash = max(0.0, self.hit_flash - dt)

        self._update_state(dt)
        self._watch_engine_events(x, y)
        if self.state == "DEATH":
            self.on_death(x, y)

        # ── cast skill (edge-triggered) ──────────────────────────────
        skill = getattr(h, "active_skill", None)
        if skill != self._skill_seen:
            if skill:
                self.on_cast(x, y, skill)
            self._skill_seen = skill

        # ── ayunan: deteksi fase, rekam trail ────────────────────────
        facing = 1 if getattr(h, "direction", 1) >= 0 else -1
        attacking = bool(getattr(h, "_gnk_attack_active", False))
        swinging = attacking and self.anim_phase in ("SWING", "IMPACT",
                                                      "FOLLOW")
        if swinging and not self._swing_seen:
            self.on_swing_start(x, y, facing)
        elif not swinging and self._swing_seen:
            self.on_swing_end()
        self._swing_seen = swinging

        impact_frame = attacking and self.anim_phase == "IMPACT"
        if impact_frame and not self._impact_frame_seen:
            self._impact_frame_seen = True
            self.on_swing_impact_frame(x, y, facing)
        elif not impact_frame:
            self._impact_frame_seen = False

        if swinging:
            grip, tip = blade_points(h, x, y, False)
            grip_b, tip_b = blade_points(h, x, y, True)
            self.trail.push(grip, tip, grip_b, tip_b)

        # ── blink: lompatan posisi > 24 px dalam satu frame ─────────
        jump = math.hypot(x - self.last_x, y - self.last_y)
        if jump > 24.0 and getattr(h, "active_skill", None) == "w":
            self.on_blink(x, y, self.last_x, self.last_y)
        self.last_x = x
        self.last_y = y

        self.trail.update(dt)
        self.particles.update(dt)
        self.projectiles.update(dt)
        if self.impacts:
            self.impacts = [i for i in self.impacts if i.update(dt)]
        if self.skills:
            self.skills = [s for s in self.skills if s.update(dt)]

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------
    def draw_ground(self, surface):
        """GROUND FX + BACK PARTICLES (di bawah sprite)."""
        for s in self.skills:
            s.draw_ground(surface)
        self.particles.draw(surface, layer="back")

    def draw_front(self, surface, x, y):
        """ATTACK TRAIL -> PROJECTILE -> FRONT PARTICLES -> SKILL -> IMPACT."""
        self.trail.draw(surface)
        self.projectiles.draw(surface)
        self.particles.draw(surface, layer="front")
        for s in self.skills:
            s.draw_front(surface)
        for i in self.impacts:
            i.draw(surface)
        if self.hit_flash > 0.0:
            self._draw_hit_flash(surface, x, y)
        if DEBUG_CHARACTER:
            draw_debug_overlay(surface, self)

    def _draw_hit_flash(self, surface, x, y):
        """IMPACT FLASH: glow baja di sekitar badan + kilat kecil di dada.

        House style yang sama dengan zephyr/grimjaw/kaizen/vex: SATU
        ``glow_surface`` additive. Versi lama menambahkan lingkaran PUTIH
        additive radius ~55 px (alpha 120) di atas badan — ~84% area
        karakter jadi blob putih solid TIAP kali kena damage, dan karena
        efek di-retrigger tiap tick damage (serangan minion / DoT),
        Gornak tampak "dibungkus cahaya putih" hampir tanpa jeda di
        tengah baku hantam. Lingkaran itu dihapus; sinyal "kena pukul"
        tetap terbaca dari glow kecil + kilat 4-titik di dada.
        """
        k = max(0.0, min(1.0, self.hit_flash / 0.16))
        # Lane boss menggambar JUGA flash siluet di canvas (hurt_flash_timer
        # -> _draw_gnk_rig_at); dua flash penuh di momen yang sama terbaca
        # sebagai white-out, jadi bagian hidupnya diredam di jalur itu.
        if int(getattr(self.hero, "hurt_flash_timer", 0) or 0) > 0:
            k *= 0.35
        r = int(18 + 14 * k)
        if glow_allowed():
            g = glow_surface(r, P["steel_hot"], 0.55 * k)
            surface.blit(g, (int(x) - r, int(y) - r - 8),
                         special_flags=pygame.BLEND_RGB_ADD)
        # Kilat bintang 4-titik KECIL di dada: tanda benturan yang terbaca
        # tanpa menutupi siluet (spark_surface sudah premultiplied-aman
        # untuk blit normal; alpha diatur lewat set_alpha).
        s = max(3, int(4 + 8 * k))
        star = spark_surface(s, P["fx_white"])
        star.set_alpha(int(170 * k))
        surface.blit(star, (int(x) - s, int(y) - 16 - s))

    # ------------------------------------------------------------------
    def clear(self):
        """Kosongkan semua state FX unit ini (trail/particle/proyektil/impact)."""
        self.particles.clear()
        self.projectiles.clear()
        self.trail.reset()
        self.impacts.clear()
        self.skills.clear()
        self.hit_flash = 0.0
        self.swing_active = False
        self._swing_seen = False
        self._impact_frame_seen = False
        self._skill_seen = None
        self._blink_seen = False
        self._void_seen = False
        self.void_screen = None
        self._last_hp = None
        self._death_done = False

    def stats(self):
        """Ringkasan untuk debug / HUD."""
        return {
            "state": self.state,
            "prev": self.prev_state,
            "phase": self.anim_phase,
            "particles": self.particles.count(),
            "dropped": self.particles.dropped,
            "projectiles": self.projectiles.count(),
            "impacts": len(self.impacts),
            "skills": len(self.skills),
            "trail": len(self.trail.points),
            "cache": cache_size(),
        }


def _ground_dy(boss):
    """Jarak anchor -> garis tanah, dalam piksel layar."""
    G = _renderer()
    dy = getattr(G, "GROUND_DY", 54) if G is not None else 54
    return int(round(float(dy) * render_scale(boss)))


# ============================================================================
# 12.  BUS ADAPTER  (hit-stop & shake lewat combat_feel)
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
    if not GORNAK_FX_ENABLED or _feel is None:
        return False
    return _feel.should_freeze_frame()


def hit_stop(seconds=0.045):
    """API publik: minta hit-stop global."""
    _feel_hit_stop(seconds)


def shake(strength=5.0, duration=0.22):
    """API publik: guncangkan layar."""
    if not shake_allowed():
        return
    _feel_shake(strength, duration)


# ============================================================================
# 13.  BOLT RENDERER BERSAMA
# ============================================================================

def draw_mana_bolt(surface, px, py, angle=0.0, age=0, crit=False,
                   radius=7.0, spin_seed=0):
    """Bolt Mana Break — dipakai lapisan FX dan (kalau perlu) gameplay.

    Prosedural penuh dan BERARAH, bukan lingkaran polos:

        ekor meruncing -> halo lembut -> outline gelap -> kepala panah
        3 lapis -> fuller ungu -> 2 pecahan orbit spiral -> glint ujung

    ``crit`` mengubah ramp jadi kuningan (Mana Break versi spellbreaker
    menyala) supaya pukulan keras terbaca tanpa perlu angka damage.
    """
    x, y = int(px), int(py)
    ca, sa = math.cos(angle), math.sin(angle)
    nx, ny = -sa, ca
    r = float(radius) * (1.18 if crit else 1.0)

    dark = P["brass"] if crit else P["fx_dark"]
    body = P["brass_hot"] if crit else P["fx_mid"]
    edge = P["fx_white"] if crit else P["fx_light"]
    hot = P["brass_hot"] if crit else P["fx_bright"]

    # ── EKOR: poligon meruncing (motion streak) ──────────────────────
    tail = r * 3.9
    buf = _scratch(int(tail * 2 + 14), int(tail * 2 + 14))
    off = int(tail + 7)
    pygame.draw.polygon(buf, (*dark, 118), [
        (x + nx * r * .8 - x + off, y + ny * r * .8 - y + off),
        (x - ca * tail - x + off, y - sa * tail - y + off),
        (x - nx * r * .8 - x + off, y - ny * r * .8 - y + off)])
    pygame.draw.polygon(buf, (*body, 92), [
        (x + nx * r * .42 - x + off, y + ny * r * .42 - y + off),
        (x - ca * tail * .58 - x + off, y - sa * tail * .58 - y + off),
        (x - nx * r * .42 - x + off, y - ny * r * .42 - y + off)])
    surface.blit(buf, (x - off, y - off))

    # ── HALO lembut (additive; ramp gelap supaya siluet tetap terbaca)
    if glow_allowed():
        gr = int(r * 2.05)
        surface.blit(glow_surface(gr, dark, 0.44), (x - gr, y - gr),
                     special_flags=pygame.BLEND_RGB_ADD)

    # ── KEPALA PANAH: bilah layang 3 lapis + fuller ─────────────────
    ln_f, ln_b, wd = r * 3.0, r * 1.45, r * 0.82
    head = [(x + ca * ln_f, y + sa * ln_f),
            (x + nx * wd - ca * r * .15, y + ny * wd - sa * r * .15),
            (x - ca * ln_b, y - sa * ln_b),
            (x - nx * wd - ca * r * .15, y - ny * wd - sa * r * .15)]
    ipoly = [(int(bx), int(by)) for bx, by in head]
    pygame.draw.polygon(surface, P["outline"],
                        [(bx + 1, by + 1) for bx, by in ipoly])
    pygame.draw.polygon(surface, body, ipoly)
    # sisi cahaya (kiri-atas) lebih terang -> volume terbaca
    pygame.draw.polygon(surface, edge, [
        (int(x + ca * ln_f * .80), int(y + sa * ln_f * .80)),
        (int(x + nx * wd * .48), int(y + ny * wd * .48)),
        (int(x - ca * ln_b * .45), int(y - sa * ln_b * .45)),
        (int(x - nx * wd * .14), int(y - ny * wd * .14))])
    # fuller ungu di tengah bilah (garis temper)
    pygame.draw.line(surface, _clamp_color(P["fx_dark"]),
                     (int(x + ca * ln_f * .5), int(y + sa * ln_f * .5)),
                     (int(x - ca * ln_b * .7), int(y - sa * ln_b * .7)),
                     max(1, int(r * .3)))

    # ── 2 PECAHAN mengorbit spiral di pangkal ────────────────────────
    for k in (0, 1):
        sp = (age * 0.42) + k * math.pi + spin_seed * 0.13
        offd = math.sin(sp) * r * 1.05
        bx = x - ca * r * .9 + nx * offd
        by = y - sa * r * .9 + ny * offd
        ln = max(2, int(r * .95))
        _shard_poly(surface, bx, by, angle + math.cos(sp) * .7, ln,
                    max(1, int(r * .34)), hot, 235, P["fx_white"])

    # ── INTI piksel + glint ujung ────────────────────────────────────
    cx, cy = x + int(ca * r * .3), y + int(sa * r * .3)
    s = max(2, int(r * .58))
    pygame.draw.rect(surface, _clamp_color(hot), (cx - s // 2, cy - s // 2,
                                                   s, s))
    pygame.draw.rect(surface, _clamp_color(P["fx_white"]), (cx - 1, cy - 1,
                                                            2, 2))
    pygame.draw.rect(surface, _clamp_color(P["fx_white"]),
                     (int(x + ca * ln_f * .92) - 1,
                      int(y + sa * ln_f * .92) - 1, 2, 2))

    # ── GLINT orbit (3 titik) — "mana yang ikut terhisap" ───────────
    spin = age * 0.30
    for i in range(3):
        a = spin + i * math.tau / 3
        pygame.draw.rect(surface, _clamp_color(edge),
                         (x + int(math.cos(a) * r * 1.85),
                          y + int(math.sin(a) * r * 1.85), 2, 2))


# ============================================================================
# 14.  DEBUG OVERLAY
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


def draw_debug_overlay(surface, director):
    """Hitbox, hurtbox, jangkauan, tumbukan proyektil, state, frame, FPS."""
    h = director.hero
    x = int(getattr(h, "x", 0))
    y = int(getattr(h, "y", 0))
    rad = int(getattr(h, "radius", 16))
    rng = int(getattr(h, "range", 60)) or 60

    # jangkauan serangan
    pygame.draw.circle(surface, (221, 161, 255), (x, y), rng, 1)
    # hurtbox
    pygame.draw.circle(surface, (90, 220, 255), (x, y), rad, 1)
    # hitbox ayunan (jendela hit aktif saja)
    G = _renderer()
    hitbox = None
    if G is not None:
        try:
            hitbox = G._swing_hitbox(h, x, y)
        except Exception:                      # pragma: no cover
            hitbox = None
    if hitbox is None and getattr(h, "_gnk_hit_active", False):
        f = 1 if getattr(h, "direction", 1) >= 0 else -1
        hitbox = pygame.Rect(x if f > 0 else x - rng, y - 22, rng, 44)
    if hitbox is not None:
        pygame.draw.rect(surface, (255, 230, 90), hitbox, 1)
    # tumbukan proyektil
    for pr in director.projectiles.projectiles:
        pygame.draw.circle(surface, (255, 255, 120),
                           (int(pr.position.x), int(pr.position.y)),
                           int(pr.radius), 1)
        pygame.draw.line(surface, (255, 255, 120),
                         (int(pr.position.x), int(pr.position.y)),
                         (int(pr.hit_pos.x), int(pr.hit_pos.y)), 1)
    # jangkar bilah (sumber bentuk trail)
    for back in (False, True):
        grip, tip = blade_points(h, x, y, back)
        col = (120, 255, 200) if not back else (255, 140, 90)
        pygame.draw.line(surface, col, (int(grip.x), int(grip.y)),
                         (int(tip.x), int(tip.y)), 1)

    font = _debug_font()
    if font is None:
        return
    try:
        fps = int(pygame.time.Clock().get_fps())
    except Exception:                          # pragma: no cover
        fps = 0
    st = director.stats()
    hs = _feel.HITSTOP if _feel is not None else None
    lines = [
        "GORNAK %s / %s" % (st["state"], st["phase"]),
        "frame %d  prog %.2f  atkT %d" % (
            int(getattr(h, "_gnk_attack_frame", 0)),
            float(getattr(h, "_gnk_attack_progress", 0.0) or 0.0),
            int(getattr(h, "timer", 0) or 0)),
        "skill %s t=%d" % (getattr(h, "active_skill", None),
                           int(getattr(h, "active_skill_timer", 0) or 0)),
        "part %d  proj %d  imp %d  sk %d" % (
            st["particles"], st["projectiles"], st["impacts"], st["skills"]),
        "shake %.1f  stop %d  fps %d  cache %d" % (
            (_feel.SHAKE.amount if _feel is not None else 0.0),
            (hs.frames if hs is not None else 0), fps, st["cache"]),
    ]
    for i, txt in enumerate(lines):
        img = font.render(txt, True, (232, 200, 255))
        surface.blit(img, (x - 78, y - 104 + i * 13))


# ============================================================================
# 15.  API MODUL — registry, tick, hook render & gameplay
# ============================================================================

_DIRECTORS = []
_LAST_TICK_MS = None


def director_for(hero):
    """Ambil (atau buat) director FX untuk satu unit Gornak."""
    _sync_palette()
    d = getattr(hero, "_gnk_fx", None)
    if d is None:
        d = GornakFXDirector(hero)
        try:
            hero._gnk_fx = d
        except Exception:                      # pragma: no cover
            return d
        _DIRECTORS.append(d)
        if len(_DIRECTORS) > 12:               # jangkar tua dibuang
            old = _DIRECTORS.pop(0)
            _release(old)
    return d


def _release(director):
    """Lepas director dari registry DAN penanda milik-nya di unit.

    Penting: kalau penanda ``_gnk_live_fx`` ditinggal sementara director
    sudah tidak dipanggil lagi, renderer akan terus MELEWATKAN pita ayunan
    di-canvas padahal tidak ada yang menggantinya -> efek hilang total.
    """
    try:
        if director.hero is not None:
            director.hero._gnk_fx = None
            director.hero._gnk_live_fx = False
    except Exception:                          # pragma: no cover
        pass
    director.clear()


def attach(hero):
    """Pasang lapisan hidup pada unit ini (dipanggil renderer / pipeline).

    Sekalian menandai unit supaya renderer TIDAK menggambar efek yang
    sekarang dimiliki lapisan hidup (pita ayunan & proc Mana Break di
    canvas).  Return True kalau lapisan hidup jadi dipakai.
    """
    if not GORNAK_FX_ENABLED or hero is None:
        return False
    try:
        director_for(hero)
    except Exception:                          # pragma: no cover
        return False
    try:
        hero._gnk_live_fx = True
    except Exception:                          # pragma: no cover
        return False
    return True


def owns(hero):
    """True kalau lapisan hidup sudah mengambil alih efek unit ini.

    Dipakai renderer untuk memutuskan apakah pita ayunan & proc Mana Break
    di-canvas masih perlu digambar (fallback) atau tidak.  Unit tanpa
    director — potongan portrait, alat uji, renderer yang dipanggil
    langsung — tetap memakai jalur canvas lama, jadi tidak ada visual yang
    hilang kalau modul FX tidak tersedia.
    """
    if not getattr(hero, "_gnk_live_fx", False):
        return False
    d = getattr(hero, "_gnk_fx", None)
    # Penanda saja tidak cukup: director-nya harus masih TERDAFTAR. Kalau
    # dia kebuang dari registry, lapisan hidup tidak dipanggil lagi dan
    # renderer wajib kembali menggambar fallback-nya.
    return d is not None and d in _DIRECTORS


def tick(dt=None):
    """Majukan waktu FX satu frame nyata; aman dipanggil berkali-kali.

    Delta-time dihitung oleh bus ``combat_feel``: dijit agar lonjakan frame
    (loading / alt-tab) tidak melempar partikel ke luar layar, diperlambat
    saat hit-stop, dan shake hanya dimundurkan sekali walau Zephyr dan
    Gornak sama-sama punya lapisan hidup.

    ``dt`` boleh diisi (alat uji / audit) supaya simulasi FX bisa dijalankan
    dengan langkah tetap tanpa bergantung pada jam SDL.
    """
    global _LAST_TICK_MS
    if dt is not None:
        step = max(0.0, min(1.0 / 20.0, float(dt)))
        _advance(step)
        return step
    # Guard frame-sama: draw_ground_layer() memanggil tick() untuk SETIAP
    # unit, sedangkan _advance() melangkahkan SEMUA director. Tanpa guard
    # ini 4 unit sejenis di layar membuat FX maju ~4x lebih cepat.
    now = pygame.time.get_ticks()
    if now == _LAST_TICK_MS:
        return 0.0                             # frame yang sama: sudah maju
    if _feel is not None:
        _LAST_TICK_MS = now
        try:
            step = _feel.fx_dt()
        except Exception:                      # pragma: no cover
            step = 0.0
    else:                                      # pragma: no cover - fallback
        now = pygame.time.get_ticks()
        if _LAST_TICK_MS is None:
            _LAST_TICK_MS = now
            return 0.0
        ms = now - _LAST_TICK_MS
        _LAST_TICK_MS = now
        if ms <= 0:
            return 0.0
        step = max(1.0 / 240.0, min(1.0 / 20.0, ms / 1000.0))
        if _feel is not None and _feel.HITSTOP.active:
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
    """Bersihkan seluruh state FX Gornak (ganti level / keluar match).

    Sekalian melepas penanda "diambil alih" di setiap unit, supaya
    ``owns()`` dan ``draw_gornak`` kembali ke jalur canvas.
    """
    global _LAST_TICK_MS
    _LAST_TICK_MS = None                       # jangan telan tick pertama
    for d in list(_DIRECTORS):
        _release(d)
    _DIRECTORS.clear()
    if _feel is not None:
        try:
            _feel.reset()
        except Exception:                      # pragma: no cover
            pass



def total_particles():
    """Jumlah partikel Gornak hidup di seluruh arena (dipakai HUD perf)."""
    return sum(d.particles.count() for d in _DIRECTORS)


# --- hook yang dipanggil heroes/__init__.py --------------------------------

def draw_ground_layer(surface, hero, x, y):
    """Pre-pass: digambar SEBELUM sprite hero di-blit."""
    if not GORNAK_FX_ENABLED:
        return
    if not attach(hero):
        return
    tick()
    d = getattr(hero, "_gnk_fx", None)
    if d is not None:
        d.draw_ground(surface)


def draw_live_layer(surface, hero, x, y):
    """Post-pass: digambar SESUDAH sprite hero di-blit."""
    if not GORNAK_FX_ENABLED:
        return
    d = director_for(hero)
    d.draw_front(surface, x, y)


# --- hook yang dipanggil _entity.py / bosses/base_boss.py ------------------

def notify_melee_impact(hero, target, damage=0, crit=False):
    """Bilah Gornak mendarat di target (basic attack melee)."""
    if not GORNAK_FX_ENABLED or hero is None or target is None:
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
                                 kind="blade")


def notify_projectile_impact(hero, x, y, angle=0.0, damage=0, crit=False,
                             kind="mana"):
    """Proyektil / proc Mana Break mengenai target."""
    if not GORNAK_FX_ENABLED or hero is None:
        return
    try:
        power = 0.7 + min(1.6, float(damage) / 45.0)
    except (TypeError, ValueError):
        power = 1.0
    director_for(hero).on_impact(x, y, angle, power, bool(crit), kind=kind)


def notify_skill_impact(hero, x, y, radius=None, skill="q"):
    """Skill Gornak meledak di sebuah titik (E/R AOE)."""
    if not GORNAK_FX_ENABLED or hero is None:
        return
    d = director_for(hero)
    if len(d.skills) >= MAX_SKILLS:
        d.skills.pop(0)
    fx = SkillFX(skill, x, y, d.particles, radius)
    d.skills.append(fx)
    d.on_impact(x, y, 0.0, 1.3 if skill != "r" else 2.0, skill == "r",
                kind="void" if skill == "r" else "ward")


def notify_skill_cast(hero, skill):
    """Dipanggil jalur gameplay saat skill dilepas (opsional).

    Director sudah mendeteksi tepi ``active_skill`` sendiri, jadi fungsi
    ini hanya berguna untuk alat uji / pemanggil yang ingin memaksa FX.
    """
    if not GORNAK_FX_ENABLED or hero is None or skill not in SKILL_DUR:
        return
    d = director_for(hero)
    d.on_cast(float(getattr(hero, "x", 0.0)),
              float(getattr(hero, "y", 0.0)), skill)
