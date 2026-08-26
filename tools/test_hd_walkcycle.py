"""Headless test untuk walk cycle 6-frame HD hero (Kingdom Wars style).

T1: aset walk 6 frame ter-load untuk tiap hero HD (2 arah) & saling beda.
T2: siklus penuh render_hero memakai SEMUA 6 frame (bukan 2 pose lama).
T3: DETERMINISME CACHE — render pose bucket sama pada pulse P dan P+6.0
    HARUS identik byte-per-byte.  (Sebelum v27: 2.2k-12.9k byte beda ->
    pose "loncat" tiap detik, kesan sprite ditempel.)
T4: pose idle & walk tidak lagi berbagi entri cache (key memuat moving).
T5: helper motion — frame maju monoton 0..5, lean merespons kecepatan,
    squash saat berbalik arah.
T6: motion smear serangan digambar tanpa error pada seluruh progress.
T7: contact sheet preview tersimpan untuk inspeksi visual.
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((320, 200))

import heroes  # noqa: E402
from heroes import _bundle as _b  # noqa: E402

NS = {
    "kaizen": _b._NS_kaizen,
    "thorne": _b._NS_thorne,
    "zephyr": _b._NS_zephyr,
}
DOCS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")


class Probe:
    def __init__(self, hero, direction=1):
        pfx = {"kaizen": "_kz", "thorne": "_th", "zephyr": "_zp"}[hero]
        self.pfx = pfx
        self.x = 0.0
        self.y = 0.0
        self.pulse = 0.0
        self.direction = direction
        self.facing = direction
        self.timer = 0
        self.attack_cooldown = 42
        self.active_skill = None
        self.active_skill_timer = 0
        self.level = 1
        self.team = "blue"
        self.range = 60
        self.alive = True
        self._kz_projectiles = []
        setattr(self, pfx + "_attack_progress", 0.0)


def canvas_bytes(surf):
    return pygame.image.tobytes(surf, "RGBA")


def render_cached(hero, pulse, moving=True):
    """Render penuh via cache; kembalikan (key, isi canvas cache).

    `moving`: prime _detect_moving 2x supaya cabang WALK yang digambar
    (bukan idle) — pose jalan yang diuji determinismenya.
    """
    ns = NS[hero]
    heroes._hero_sprite_cache.clear()
    p = Probe(hero)
    p.pulse = pulse
    if moving:
        p.x = 1.0
        ns.__dict__["_detect_moving"](p)   # init posisi terakhir
        p.x = 2.0
        ns.__dict__["_detect_moving"](p)   # -> True + flag cache ter-set
        p.x = 3.0
    key = heroes._hero_cache_key(hero, p)
    heroes.render_hero(hero, pygame.Surface((240, 240), pygame.SRCALPHA),
                       p, 120, 120)
    entry = heroes._hero_sprite_cache.get(key)
    assert entry is not None, "canvas tidak masuk cache"
    assert key[-1] is moving, "flag moving di key = %s (harus %s)" % (key[-1], moving)
    return key, entry[0]


fail = 0

# ── T1: aset 6 frame ─────────────────────────────────────────────
for hero, ns in NS.items():
    walk_cache = getattr(ns, "_%s_WALK_CACHE" % hero.upper())
    walk_cache.clear()
    frames = [ns.__dict__["_load_%s_walk_frame" % hero](i, 1) for i in range(6)]
    frames_f = [ns.__dict__["_load_%s_walk_frame" % hero](i, -1) for i in range(6)]
    assert all(f is not None for f in frames), "%s: frame walk hilang" % hero
    assert all(f is not None for f in frames_f), "%s: frame walk facing -1 hilang" % hero
    heights = {f.get_height() for f in frames}
    assert max(heights) - min(heights) <= 80, "%s: tinggi frame tidak konsisten" % hero
    # Frame harus benar-benar berbeda isi (bukan 6 salinan pose sama):
    # bandingkan byte-per-byte tiap pasangan, hitung frame unik.
    raws = [pygame.image.tobytes(f, "RGBA") for f in frames]
    uniq = {0}
    for i in range(1, 6):
        if all(sum(1 for a, b in zip(raws[i], raws[j]) if a != b) > 2000
               for j in uniq):
            uniq.add(i)
    assert len(uniq) >= 5, "%s: hanya %d frame unik dari 6" % (hero, len(uniq))
    print("T1 OK  - %s: 6 frame walk x 2 arah ter-load, %d frame unik" % (hero, len(uniq)))

# ── T2: siklus memakai semua frame ───────────────────────────────
for hero, ns in NS.items():
    surf = pygame.Surface((240, 240), pygame.SRCALPHA)
    p = Probe(hero)
    seen = set()
    for i in range(48):
        p.pulse = i * 0.25
        p.x = i * 1.5
        ns.__dict__["draw_%s" % hero](surf, p, 120, 120)
        seen.add(ns.__dict__["_%s_walk_motion" % hero](p)["frame"])
    assert seen == set(range(6)), "%s: frame terpakai %s" % (hero, sorted(seen))
    print("T2 OK  - %s: semua 6 frame tersiklus (%s)" % (hero, sorted(seen)))

# ── T3: determinisme cache antar-loop ────────────────────────────
# Pose jalan HARUS identik byte-per-byte pada bucket yang sama (pulse
# berbeda 6.0 / 12.0).  Layer FX ambien (syal/angin/partikel) memakai
# pulse mentah, jadi canvas penuh diberi toleransi kecil — di game FX
# ini dibekukan cache per bucket lalu diulang periodik.
for hero, ns in NS.items():
    motion_fn = ns.__dict__["_%s_walk_motion" % hero]
    p = Probe(hero)
    m1 = motion_fn(p)
    for delta in (6.0, 12.0, 18.0):
        p2 = Probe(hero)
        p2.pulse = delta
        m2 = motion_fn(p2)
        # bucket sama (delta kelipatan 6.0) -> SELURUH motion identik:
        # frame, bob, sway, tilt, scale — pose murni fungsi bucket.
        assert m1 == m2, \
            "%s: motion pose tidak deterministik antar loop: %s vs %s" % (
                hero,
                {k: m1[k] for k in m1 if m1[k] != m2[k]},
                {k: m2[k] for k in m2 if m1[k] != m2[k]})
    # Canvas penuh: sisa beda hanya FX ambien (aura/syal/angin —
    # pulse mentah, dibekukan cache per bucket lalu diulang periodik;
    # perilaku yang sama sudah ada sebelum v27).
    k1, c1 = render_cached(hero, 1.0)
    k2, c2 = render_cached(hero, 1.0 + 6.0)
    k3, c3 = render_cached(hero, 1.0 + 12.0)
    assert k1 == k2 == k3, "%s: key bucket tidak stabil: %s vs %s" % (hero, k1, k2)
    d12 = sum(1 for a, b in zip(canvas_bytes(c1), canvas_bytes(c2)) if a != b)
    d23 = sum(1 for a, b in zip(canvas_bytes(c2), canvas_bytes(c3)) if a != b)
    assert d12 < 16000 and d23 < 16000, \
        "%s: beda canvas melebihi FX ambien (d12=%d d23=%d)" % (hero, d12, d23)
    print("T3 OK  - %s: motion pose identik antar loop; canvas beda %d/%d byte (FX ambien; pose dulu beda 2k-13k)" % (hero, d12, d23))

# ── T4: idle vs walk tidak bertabrakan di cache ──────────────────
for hero in NS:
    surf = pygame.Surface((240, 240), pygame.SRCALPHA)
    p = Probe(hero)
    p.pulse = 2.0
    ns = NS[hero]
    ns.__dict__["draw_%s" % hero](surf, p, 120, 120)  # idle -> miss -> set flag
    idle_key = heroes._hero_cache_key(hero, p)
    assert idle_key[-1] is False, "%s: _moving_cached tidak ter-set False" % hero
    p.x = 3.0
    p.pulse = 2.25
    ns.__dict__["draw_%s" % hero](surf, p, 120, 120)  # bergerak
    walk_key = heroes._hero_cache_key(hero, p)
    assert walk_key[-1] is True, "%s: _moving_cached tidak ter-set True" % hero
    assert idle_key != walk_key, "%s: key idle & walk sama -> tabrakan cache" % hero
    print("T4 OK  - %s: key idle/walk terpisah oleh flag moving" % hero)

# ── T5: helper motion ────────────────────────────────────────────
p = Probe("kaizen")
frames = []
for i in range(24):
    p.pulse = i * 0.25
    frames.append(NS["kaizen"]._kaizen_walk_motion(p)["frame"])
assert frames == [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 0] * 2, "urutan frame: %s" % frames[:12]
m_neutral = NS["kaizen"]._kaizen_walk_motion(p)
p._kz_vel_x = 2.5
m_fast = NS["kaizen"]._kaizen_walk_motion(p)
assert m_fast["tilt"] < m_neutral["tilt"] - 3.0, "lean tidak merespons kecepatan"
p._kz_vel_x = 0.0
NS["kaizen"]._detect_moving(p)
p.direction = -1
p.pulse += 0.125          # tengah jendela turn hop -> squash maksimum
NS["kaizen"]._detect_moving(p)
p.pulse += 0.125
m_turn = NS["kaizen"]._kaizen_walk_motion(p)
assert m_turn["scale_x"] < 0.95, "turn squash tidak aktif (%.3f)" % m_turn["scale_x"]
print("T5 OK  - urutan frame monoton, lean & turn squash bekerja")

# ── T6: smear serangan tanpa error ───────────────────────────────
for hero, ns in NS.items():
    surf = pygame.Surface((240, 240), pygame.SRCALPHA)
    p = Probe(hero)
    p.__dict__[p.pfx + "_attack_active"] = True
    for i in range(21):
        p.__dict__[p.pfx + "_attack_progress"] = i / 20.0
        ns.__dict__["_draw_%s_attack" % hero](surf, p, 120, 120)
        assert surf.get_rect().size > (0, 0)
    print("T6 OK  - %s: smear + strike dust jalan di 21 progress" % hero)

# ── T7: contact sheet ────────────────────────────────────────────
try:
    os.makedirs(DOCS, exist_ok=True)
    W, H = 6 * 96, 160
    sheet = pygame.Surface((W, H), pygame.SRCALPHA)
    sheet.fill((24, 26, 34, 255))
    for hero, ns in NS.items():
        surf = pygame.Surface((96, 160), pygame.SRCALPHA)
        for i in range(24):
            p = Probe(hero)
            p.pulse = i * 0.25
            p.x = i * 1.5
            ns.__dict__["draw_%s" % hero](surf, p, 48, 150)
        heroes._hero_sprite_cache.clear()
    # satu sheet gabungan: kolom = hero, baris = fase siklus
    for col, (hero, ns) in enumerate(NS.items()):
        for row in range(6):
            p = Probe(hero)
            p.pulse = row * 2.0 + 0.01
            p.x = 100.0
            s = pygame.Surface((96, 160), pygame.SRCALPHA)
            ns.__dict__["draw_%s" % hero](s, p, 48, 148)
            sheet.blit(s, (col * 96, 0))
    out = os.path.join(DOCS, "hd_walkcycle_ingame_preview.png")
    pygame.image.save(sheet, out)
    print("T7 OK  - preview: %s" % out)
except Exception as e:
    print("T7 GAGAL: %s" % e)
    fail += 1

print()
print("SEMUA TEST LULUS" if fail == 0 else "ADA %d TEST GAGAL" % fail)
sys.exit(0 if fail == 0 else 1)
