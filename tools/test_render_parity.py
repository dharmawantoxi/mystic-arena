#!/usr/bin/env python3
"""test_render_parity.py — oracle blok `effects.py` di `_render.py` untuk port
Godot (percikan pukulan, ledakan kematian, panah jalur lane).

Kenapa tool sendiri: ketiga blok ini tidak punya state pertandingan — bisa
dijalankan berdiri sendiri, deterministik, dan murah. Fixture yang dihasilkan
(`godot/tests/fixtures/render_fx.json`) diputar ulang
`godot/tests/RenderFxParityTest.tscn` lewat KELAS PRODUKSINYA (`HitSpark.gd`,
`DeathBurst.gd`, `SparkField.gd`, `PathPreview.gd`).

Yang dijalankan adalah kode pygame SUNGGUHAN, bukan rumus yang disalin:

  * `HitParticle.update/draw` (`_render.py:461-491`) — jejak
    `pygame.draw.circle` + `pygame.transform.scale` + `Surface.blit` +
    `set_alpha` direkam lewat Surface turunan, lalu DITURUNKAN jadi op
    (pusat = posisi blit + pusat sprite × faktor skala; radius ikut skala;
    alpha = alpha lingkaran × alpha sprite). Jadi angka yang dibandingkan
    adalah hasil rasterisasi pygame, bukan tafsiran kita atas kodenya.
  * `DeathExplosion` (`:494-570`) — palet tim, preset small/medium/large,
    kilat pusat 8 frame, dan URUTAN konsumsi `random.uniform/choice/randint`
    (angle → speed → warna → ukuran spark → lifetime) direkam; Godot mereplay
    urutan nilai yang sama lewat `rng` ter-script, jadi jumlah/urutan/rentang
    roll ikut terkunci, bukan cuma hasilnya.
  * `EffectManager.add_hit_particles` (`:712-741`) + `add_death_explosion`
    (`:743-747`) + batas `MAX_PARTICLES 500` / `MAX_EXPLOSIONS 80`
    (`:609-611`) — jumlah partikel per `count`, palet, dan aturan trim.
  * `PathPreview.show/update/draw` (`:1275-1370`) — jejak
    `pygame.draw.polygon` + `Surface.blit` SUNGGUHAN pada jalur lane ASLI
    (`map_components.generators.PathGenerator`, sumber yang sama dengan
    `MapRenderer.get_lane_path` yang dipakai `_core.py:1756-1762`), termasuk
    fade in 20 frame / fade out 40 frame, `offset = int(t*2) % 20`, dan pola
    pulse `(i // 8 + offset // 5) % 4`.
  * jumlah percikan per situs pemanggil (`count=4/6/10`) dan ukuran ledakan
    (`'small'/'medium'/'large'`) di-PIN dari TEKS SUMBER `_entity.py`,
    `bosses/base_boss.py`, `tactical_commands.py` — pola yang hilang bikin
    tool GAGAL, tidak diam-diam meloloskan perubahan.

CATATAN (temuan audit pada kode pygame, disimpan di fixture):
`EffectManager.add_hit_particles` membaca `mobile.perf.Quality` — default
desktop/HIGH adalah `particles=True`, `particle_ratio=0.70`, jadi pygame
sebenarnya membulatkan `count` menjadi 4→3, 6→4, 10→7. Lapisan adaptive
quality belum ada di Godot (lihat AUDIT_ULANG_DARI_AWAL.md §3), jadi port
memakai rasio 1.0 (jumlah penuh) dan faktanya direkam di `py_quality` supaya
selisihnya terlihat, bukan terkubur.

Jalankan:
  python3 tools/test_render_parity.py                  # gate drift + kunci statis Godot
  python3 tools/test_render_parity.py --write-fixture  # regenerasi fixture
"""
import argparse
import json
import os
import random
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
sys.path.insert(0, ROOT)

FIXTURE = os.path.join(ROOT, "godot", "tests", "fixtures", "render_fx.json")
RENDER_PY = os.path.join(ROOT, "_render.py")
GODOT = os.path.join(ROOT, "godot")
TOOL = os.path.relpath(os.path.abspath(__file__), ROOT)

PASS = []


def check(cond, msg):
    if not cond:
        raise AssertionError("GAGAL: %s" % msg)
    PASS.append(msg)


# ══════════════════════════════════════════════════════════
#  1. Perekam jejak gambar pygame (Surface turunan + patch draw/scale)
# ══════════════════════════════════════════════════════════

_CAP = None


class Capture(object):
    """Kumpulan jejak satu panggilan draw()."""

    def __init__(self):
        self.ops = []
        self.scaled = {}   # id(hasil) -> (surface_induk, (w, h))
        self.keep = []     # jaga referensi supaya id() tidak didaur ulang

    def record_blit(self, source, dest):
        dx, dy = float(dest[0]), float(dest[1])
        alpha = source.get_alpha()
        shapes, factor = self._resolve(source)
        for sh in shapes:
            color = list(sh["color"])
            if len(color) < 4:
                color = color + [255]
            if alpha is not None:
                color[3] = int(color[3] * int(alpha) / 255)
            if sh["kind"] == "circle":
                self.ops.append({
                    "op": "circle",
                    "x": dx + sh["center"][0] * factor,
                    "y": dy + sh["center"][1] * factor,
                    "r": sh["radius"] * factor,
                    "color": color,
                })
            else:
                self.ops.append({
                    "op": "polygon",
                    "points": [[dx + p[0], dy + p[1]] for p in sh["points"]],
                    "color": color,
                })

    def _resolve(self, source):
        entry = self.scaled.get(id(source))
        if entry is not None:
            parent, size = entry
            shapes = getattr(parent, "_shapes", [])
            return shapes, float(size[0]) / float(parent.get_width())
        return getattr(source, "_shapes", []), 1.0


def _install_capture_patch(pygame):
    """Ganti `pygame.Surface`/`draw.circle`/`draw.polygon`/`transform.scale`
    dengan versi perekam. Kembalikan fungsi pemulih."""
    real_surface = pygame.Surface
    real_circle = pygame.draw.circle
    real_polygon = pygame.draw.polygon
    real_scale = pygame.transform.scale

    class Tracked(real_surface):
        def blit(self, source, dest, *a, **k):
            if _CAP is not None:
                _CAP.record_blit(source, dest)
            return real_surface.blit(self, source, dest, *a, **k)

    def surface_factory(size, flags=0, depth=0, masks=None):
        # `depth=0` EKSPLISIT ditolak pygame saat SRCALPHA ("no standard
        # masks exist for given bitdepth with alpha"), jadi argumennya
        # hanya diteruskan kalau pemanggil memang mengisinya.
        if masks is not None:
            surf = Tracked(size, flags, depth, masks)
        elif depth:
            surf = Tracked(size, flags, depth)
        else:
            surf = Tracked(size, flags)
        surf._shapes = []
        if _CAP is not None:
            _CAP.keep.append(surf)
        return surf

    def circle(surface, color, center, radius, width=0, *a, **k):
        # Bentuk sprite direkam SELALU (bukan hanya di dalam jendela
        # capture): `HitParticle._psurf` digambar saat __init__, jauh
        # sebelum draw() pertama.
        if hasattr(surface, "_shapes"):
            surface._shapes.append({"kind": "circle", "color": list(color),
                                    "center": (float(center[0]),
                                               float(center[1])),
                                    "radius": float(radius),
                                    "width": int(width)})
        return real_circle(surface, color, center, radius, width, *a, **k)

    def polygon(surface, color, points, *a, **k):
        if hasattr(surface, "_shapes"):
            surface._shapes.append({"kind": "polygon", "color": list(color),
                                    "points": [[float(p[0]), float(p[1])]
                                               for p in points]})
        return real_polygon(surface, color, points, *a, **k)

    def scale(surface, size, *a, **k):
        result = real_scale(surface, size, *a, **k)
        if _CAP is not None:
            _CAP.scaled[id(result)] = (surface,
                                       (result.get_width(), result.get_height()))
            _CAP.keep.append(result)
        return result

    pygame.Surface = surface_factory
    pygame.draw.circle = circle
    pygame.draw.polygon = polygon
    pygame.transform.scale = scale

    def restore():
        pygame.Surface = real_surface
        pygame.draw.circle = real_circle
        pygame.draw.polygon = real_polygon
        pygame.transform.scale = real_scale

    return restore


def capture(pygame, draw_fn, size=(1400, 800)):
    """Jalankan draw_fn(surface) dan kembalikan op hasil jejak NYATA."""
    global _CAP
    cap = Capture()
    _CAP = cap
    try:
        dest = pygame.Surface(size, pygame.SRCALPHA)
        draw_fn(dest)
    finally:
        _CAP = None
    return cap.ops


class RecordingRandom(object):
    """Mewakili modul `random` pygame: meneruskan ke random asli (sudah
    di-seed) dan MENCATAT urutan konsumsi. `choice` dicatat sebagai indeks
    supaya replay Godot memakai daftar warnanya sendiri."""

    def __init__(self, seed):
        self.seed = seed
        self.calls = []
        self._saved = None

    def __enter__(self):
        random.seed(self.seed)
        self._saved = (random.uniform, random.randint, random.choice)
        random.uniform = self._uniform
        random.randint = self._randint
        random.choice = self._choice
        return self

    def __exit__(self, *exc):
        random.uniform, random.randint, random.choice = self._saved
        return False

    def _uniform(self, a, b):
        v = self._saved[0](a, b)
        self.calls.append({"fn": "uniform", "args": [a, b], "value": v})
        return v

    def _randint(self, a, b):
        v = self._saved[1](a, b)
        self.calls.append({"fn": "randint", "args": [a, b], "value": int(v)})
        return v

    def _choice(self, seq):
        v = self._saved[2](seq)
        self.calls.append({"fn": "choice", "args": [list(seq)],
                           "value": int(list(seq).index(v))})
        return v


def _round3(value):
    """Bulatkan ke 6 desimal: jejak pygame dan float Godot boleh beda ULP."""
    if isinstance(value, float):
        return round(value, 6)
    return value


def _norm_ops(ops):
    out = []
    for op in ops:
        row = {"op": op["op"], "color": [int(c) for c in op["color"]]}
        if op["op"] == "circle":
            row["x"] = _round3(op["x"])
            row["y"] = _round3(op["y"])
            row["r"] = _round3(op["r"])
        else:
            row["points"] = [[_round3(p[0]), _round3(p[1])]
                             for p in op["points"]]
        out.append(row)
    return out


# ══════════════════════════════════════════════════════════
#  2. Skenario: HitParticle / DeathExplosion / add_hit_particles
# ══════════════════════════════════════════════════════════

def _particle_row(p):
    return {"x": _round3(p.x), "y": _round3(p.y),
            "vx": _round3(p.vx), "vy": _round3(p.vy),
            "color": list(p.color), "lifetime": int(p.lifetime),
            "max_lifetime": int(p.max_lifetime), "size": int(p.size),
            "pbase": int(p._pbase), "alive": bool(p.alive)}


def build_spark_scenarios(pygame, rend):
    """HitParticle dengan velocity/lifetime/size EKSPLISIT (tanpa RNG) —
    mengunci gerak + aturan scale/alpha + cutoff `alpha <= 0`."""
    cases = [
        {"name": "ukuran2_full", "x": 640.5, "y": 360.25,
         "color": [255, 200, 100], "velocity": [1.5, -2.0],
         "lifetime": 15, "size": 2, "steps": 16},
        {"name": "ukuran3_miring", "x": -12.0, "y": 731.75,
         "color": [100, 200, 255], "velocity": [-2.25, 0.5],
         "lifetime": 20, "size": 3, "steps": 21},
        {"name": "ukuran5_besar", "x": 100.0, "y": 100.0,
         "color": [255, 100, 100], "velocity": [0.0, 3.0],
         "lifetime": 35, "size": 5, "steps": 36},
    ]
    out = []
    for case in cases:
        p = rend.HitParticle(case["x"], case["y"], tuple(case["color"]),
                             tuple(case["velocity"]),
                             lifetime=case["lifetime"], size=case["size"])
        check(p.gravity == 0.15,
              "HitParticle.gravity harus 0.15, dapat %s" % p.gravity)
        check(p._pbase == max(1, int(case["size"])),
              "sprite pra-render HitParticle = max(1, size)")
        frames = []
        for step in range(case["steps"]):
            ops = capture(pygame, p.draw)
            frames.append({"step": step, "lifetime": int(p.lifetime),
                           "alive": bool(p.alive), "ops": _norm_ops(ops)})
            p.update()
        check(all(f["ops"] or not f["alive"] or f["lifetime"] <= 0
                  for f in frames),
              "partikel hidup selalu menghasilkan op (kecuali alpha 0)")
        out.append({"name": case["name"], "init": case, "frames": frames,
                    "final": _particle_row(p)})
    return out


def build_burst_scenarios(pygame, rend):
    """DeathExplosion: RNG direkam (seed tetap) supaya replay Godot memakai
    urutan nilai yang sama."""
    cases = [
        {"name": "small_blue", "x": 320.0, "y": 240.0, "team": "blue",
         "size": "small", "seed": 1234, "steps": 40},
        {"name": "medium_red", "x": 640.5, "y": 360.5, "team": "red",
         "size": "medium", "seed": 99, "steps": 40},
        {"name": "medium_blue", "x": 900.0, "y": 120.0, "team": "blue",
         "size": "medium", "seed": 7, "steps": 40},
        {"name": "large_red", "x": 1100.0, "y": 600.0, "team": "red",
         "size": "large", "seed": 2026, "steps": 40},
    ]
    sample_frames = (0, 1, 7, 8, 9, 20, 34, 39)
    out = []
    for case in cases:
        with RecordingRandom(case["seed"]) as rec:
            burst = rend.DeathExplosion(case["x"], case["y"],
                                        team=case["team"], size=case["size"])
        want_count = {"small": 8, "medium": 15, "large": 25}[case["size"]]
        check(len(burst.particles) == want_count,
              "DeathExplosion('%s') harus %d partikel, dapat %d"
              % (case["size"], want_count, len(burst.particles)))
        check(burst.flash_timer == 8 and burst.flash_max == 8,
              "kilat pusat DeathExplosion = 8 frame")
        # Baris partikel HARUS difoto sebelum loop frame: pygame membuang
        # partikel yang mati di `DeathExplosion.update`, jadi setelah 40 frame
        # `burst.particles` sudah kosong dan fixture mencatat 0 partikel
        # (ketangkap replay Godot CI: "8 partikel != pygame 0").
        rows = [_particle_row(p) for p in burst.particles]
        check(len(rows) == want_count,
              "baris partikel '%s' harus %d, dapat %d"
              % (case["name"], want_count, len(rows)))
        frames = []
        for step in range(case["steps"]):
            if step in sample_frames:
                ops = capture(pygame, burst.draw)
                frames.append({"step": step, "flash": int(burst.flash_timer),
                               "alive": bool(burst.alive),
                               "ops": _norm_ops(ops)})
            burst.update()
        check(not burst.alive,
              "setelah %d frame ledakan '%s' harus mati"
              % (case["steps"], case["name"]))
        out.append({"name": case["name"], "init": case,
                    "rng_calls": rec.calls,
                    "particles": rows,
                    "frames": frames})
    return out


def build_hit_scenarios(pygame, rend):
    """EffectManager.add_hit_particles — jumlah/palet/trim + batas 500/80."""
    effects = rend.EffectManager()
    check(effects.MAX_PARTICLES == 500 and effects.MAX_EXPLOSIONS == 80,
          "batas EffectManager harus 500 partikel / 80 ledakan")
    cases = [
        {"name": "minion_red", "x": 300.0, "y": 400.0, "team": "red",
         "count": 4, "seed": 4242},
        {"name": "boss_red", "x": 640.0, "y": 300.0, "team": "red",
         "count": 6, "seed": 555},
        {"name": "castle_blue", "x": 90.0, "y": 620.0, "team": "blue",
         "count": 10, "seed": 8080},
        {"name": "chain_blue", "x": 700.0, "y": 500.0, "team": "blue",
         "count": 6, "seed": 31337},
    ]
    out = []
    for case in cases:
        effects.particles = []
        with RecordingRandom(case["seed"]) as rec:
            effects.add_hit_particles(case["x"], case["y"],
                                      team=case["team"], count=case["count"])
        # TANPA mobile.perf di proses ini Quality tetap terbaca; rasio efektif
        # direkam terpisah di py_quality, jadi di sini jumlah partikel bisa
        # berbeda dari `count` mentah. Bandingkan dengan rumus pygame.
        try:
            from mobile.perf import Quality
            ratio = Quality.particle_ratio
            enabled = Quality.particles
        except Exception:
            ratio, enabled = 1.0, True
        want = max(0, int(round(case["count"] * ratio))) if enabled else 0
        check(len(effects.particles) == want,
              "add_hit_particles(count=%d, ratio=%s) harus %d partikel, dapat %d"
              % (case["count"], ratio, want, len(effects.particles)))
        ops = capture(pygame, effects.draw)
        out.append({"name": case["name"], "init": case,
                    "rng_calls": rec.calls,
                    "particles": [_particle_row(p) for p in effects.particles],
                    "ops": _norm_ops(ops)})
    return out


def build_caps(pygame, rend):
    """Batas anti-unbounded-growth: buang yang TERTUA.

    Rasio kualitas dinetralkan (1.0) selama skenario ini — dengan preset HIGH
    pygame memangkas `count` jadi 0.7x sehingga 600 permintaan tidak akan
    pernah menyentuh batas 500 dan trim-nya tidak teruji."""
    effects = rend.EffectManager()
    saved = None
    try:
        from mobile.perf import Quality
        saved = Quality._particle_ratio
        Quality.particle_ratio = 1.0
    except Exception:
        pass
    try:
        with RecordingRandom(3):
            for i in range(60):
                effects.add_hit_particles(float(i), 0.0, team="red", count=10)
            particles_after = len(effects.particles)
            first_x = effects.particles[0].x
            for i in range(90):
                effects.add_death_explosion(float(i), 0.0, team="red",
                                            size="small")
            explosions_after = len(effects.explosions)
            first_ex = effects.explosions[0].x
    finally:
        if saved is not None:
            from mobile.perf import Quality
            Quality.particle_ratio = saved
    check(particles_after == 500,
          "partikel dipangkas ke MAX_PARTICLES 500, dapat %d"
          % particles_after)
    check(explosions_after == 80,
          "ledakan dipangkas ke MAX_EXPLOSIONS 80, dapat %d"
          % explosions_after)
    # 600 permintaan - 500 batas = 100 partikel tertua terbuang = 10 call
    # pertama (10 partikel per call), jadi x pertama yang tersisa = 10.
    check(first_x == 10.0,
          "yang dibuang adalah partikel TERTUA (x pertama tersisa = 10), "
          "dapat %s" % first_x)
    check(first_ex == 10.0,
          "yang dibuang adalah ledakan TERTUA (x pertama tersisa = 10), "
          "dapat %s" % first_ex)
    return {"max_particles": rend.EffectManager.MAX_PARTICLES,
            "max_explosions": rend.EffectManager.MAX_EXPLOSIONS,
            "added_particles": 600, "particles_after": particles_after,
            "first_particle_x": first_x,
            "added_explosions": 90, "explosions_after": explosions_after,
            "first_explosion_x": first_ex}


# ══════════════════════════════════════════════════════════
#  3. PathPreview — jalur lane ASLI PathGenerator
# ══════════════════════════════════════════════════════════

def build_path_preview(pygame, rend, _core):
    from map_components.generators import PathGenerator
    lanes = PathGenerator.generate_lanes(_core.SCREEN_WIDTH,
                                        _core.SCREEN_HEIGHT)
    paths = [[list(pt) for pt in lane] for lane in lanes]
    check([len(p) for p in paths] == [111, 65, 101],
          "jumlah titik lane PathGenerator berubah (top/mid/bot) — port "
          "ArenaMap.get_lane_path harus ikut diperiksa: %s"
          % [len(p) for p in paths])
    preview = rend.PathPreview()
    check(preview.duration == 120,
          "PathPreview.duration harus 120 frame, dapat %s" % preview.duration)
    preview.show([list(lane) for lane in lanes])
    check(preview.active and preview.timer == 120,
          "show() mengaktifkan preview dengan timer penuh")

    samples = (1, 2, 10, 19, 20, 21, 40, 60, 80, 81, 82, 100, 118, 119,
               120, 121)
    timeline = []
    frames = []
    anim = 137   # sembarang: mengunci offset = int(t*2) % 20
    for step in range(1, 131):
        preview.update()
        if step in samples:
            ops = capture(pygame, lambda s: preview.draw(s, anim))
            frames.append({"step": step, "timer": int(preview.timer),
                           "active": bool(preview.active),
                           "anim": int(anim), "ops": _norm_ops(ops)})
        ratio = 1.0
        if preview.timer > preview.duration - 20:
            ratio = (preview.duration - preview.timer) / 20.0
        elif preview.timer < 40:
            ratio = preview.timer / 40.0
        timeline.append({"step": step, "timer": int(preview.timer),
                         "active": bool(preview.active),
                         "alpha": int(200 * ratio),
                         "arrows": len(frames[-1]["ops"])
                         if step in samples else None})
        anim += 1
    check(not preview.active and preview.paths == [],
          "setelah 120 frame preview mati dan jalur dibuang")
    arrows_per_frame = len([1 for lane in lanes
                            for i in range(0, len(lane) - 1, 8)])
    full = [f for f in frames if f["timer"] == 100]
    check(full and len(full[0]["ops"]) == arrows_per_frame,
          "satu panah tiap 8 titik jalur: %d panah, dapat %s"
          % (arrows_per_frame, full and len(full[0]["ops"])))
    return {"paths": paths, "duration": preview.duration, "timeline": timeline,
            "frames": frames, "arrows_per_frame": arrows_per_frame}


# ══════════════════════════════════════════════════════════
#  4. PIN dari teks sumber pygame + klaim dead code
# ══════════════════════════════════════════════════════════

RENDER_PATTERNS = [
    ("gravity", r"self\.gravity = (0\.15)"),
    ("friction", r"self\.vx \*= (0\.95)"),
    ("hit_alpha", r"alpha = int\(255 \* alpha_ratio\)"),
    ("hit_size", r"current_size = max\(1, int\(self\.size \* alpha_ratio\)\)"),
    ("flash_timer", r"self\.flash_timer = (8)"),
    ("flash_radius", r"size = int\((20) \* intensity\)"),
    ("max_particles", r"MAX_PARTICLES = (500)"),
    ("max_explosions", r"MAX_EXPLOSIONS = (80)"),
    ("hit_speed", r"speed = random\.uniform\(1, (2\.5)\)"),
    ("hit_life", r"lifetime=random\.randint\((12), (20)\)"),
    ("hit_size_range", r"size=random\.randint\((2), (3)\)"),
    ("burst_speed", r"speed = random\.uniform\((1\.5), (4)\)"),
    ("burst_life", r"lifetime=random\.randint\((20), (35)\)"),
    ("preview_duration", r"self\.duration = (120)"),
    ("preview_alpha", r"alpha = int\((200) \* alpha_ratio\)"),
    ("preview_fade_in", r"if self\.timer > self\.duration - (20):"),
    ("preview_fade_out", r"elif self\.timer < (40):"),
    ("preview_offset", r"offset = int\(animation_time \* (2)\) % (20)"),
    ("preview_step", r"for i in range\(0, len\(lane_path\) - 1, (8)\):"),
    ("preview_ahead", r"if i \+ (4) < len\(lane_path\):"),
    ("preview_pulse", r"pulse_i = \(i // 8 \+ offset // (5)\) % (4)"),
]


def pin_render_source():
    src = open(RENDER_PY, encoding="utf-8").read()
    out = {}
    for key, pat in RENDER_PATTERNS:
        m = re.search(pat, src)
        check(m is not None,
              "pola sumber `%s` tidak ditemukan di _render.py — pygame "
              "berubah: sesuaikan port Godot lalu regenerasi fixture" % key)
        out[key] = [float(v) if "." in v else int(v) for v in m.groups()]
    return out


def _owner_class(lines, index):
    """Nama class pemilik baris ke-`index` (1-based)."""
    owner = ""
    for i, line in enumerate(lines[:index], 1):
        if line.startswith("class "):
            owner = line.split("(")[0][6:].strip().rstrip(":")
    return owner


def _scan(rel, pattern):
    """Cari pola di SATU berkas (boleh lintas baris — call site pygame
    sering dipecah jadi dua baris)."""
    path = os.path.join(ROOT, rel)
    src = open(path, encoding="utf-8").read()
    lines = src.split("\n")
    out = []
    for m in re.finditer(pattern, src):
        idx = src.count("\n", 0, m.start()) + 1
        out.append({"file": rel, "line": idx,
                    "class": _owner_class(lines, idx),
                    "groups": list(m.groups())})
    return out


HIT_PATTERN = r"add_hit_particles\([^()]*?count=(\d+)\)"
EXPLOSION_PATTERN = r"add_death_explosion\([^()]*?size='(\w+)'\)"


def pin_call_sites():
    """Jumlah percikan + ukuran ledakan dari situs pemanggil pygame."""
    hits = (_scan("_entity.py", HIT_PATTERN)
            + _scan("bosses/base_boss.py", HIT_PATTERN)
            + _scan("hero_items.py", HIT_PATTERN))
    check(len(hits) == 4,
          "call site add_hit_particles pygame harus 4 (Castle, Minion, Boss, "
          "chain item), dapat %s" % [h["file"] + ":" + str(h["line"])
                                     for h in hits])
    by_class = {}
    for h in hits:
        by_class.setdefault(h["class"], []).append(int(h["groups"][0]))
    explosions = (_scan("_entity.py", EXPLOSION_PATTERN)
                  + _scan("bosses/base_boss.py", EXPLOSION_PATTERN)
                  + _scan("tactical_commands.py", EXPLOSION_PATTERN))
    sizes = {}
    for h in explosions:
        sizes.setdefault(h["file"], []).append(h["groups"][0])
    check(sizes.get("_entity.py") == ["medium"]
          and sizes.get("bosses/base_boss.py") == ["large"]
          and sizes.get("tactical_commands.py") == ["small", "small"],
          "ukuran ledakan pygame berubah: %s" % sizes)
    return {"hit_particles": hits, "by_class": by_class,
            "death_explosion": explosions, "sizes": sizes}


def find_call_sites(pattern, skip=()):
    hits = []
    rx = re.compile(pattern)
    skip = tuple(skip) + (TOOL,)
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in
                       (".git", "__pycache__", ".godot", "node_modules")]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), ROOT)
            if rel.startswith(skip):
                continue
            try:
                with open(os.path.join(dirpath, fn), encoding="utf-8") as fh:
                    for i, line in enumerate(fh, 1):
                        if rx.search(line):
                            hits.append("%s:%d" % (rel, i))
            except (UnicodeDecodeError, OSError):
                continue
    return hits


def build_dead_claims():
    """Klaim 'tidak diport karena pygame sendiri tidak memakainya' — dijaga
    supaya tetap benar (pola klaim dead-code FASE 25 di _system.py)."""
    out = {}
    kill_draw = find_call_sites(r"kill_feed\.(draw|add_kill)\b",
                                skip=("_render.py",))
    out["kill_feed_render"] = {"sites": kill_draw}
    check(len(kill_draw) == 0,
          "`KillFeed.add_kill/draw` harus tetap tanpa pemanggil (pygame tidak "
          "pernah menampilkannya, jadi Godot tidak memportnya): %s"
          % kill_draw[:6])
    popup_use = find_call_sites(r"popup_anim\.(get_scale|get_offset_y)\b")
    out["popup_animation_render"] = {"sites": popup_use}
    check(len(popup_use) == 0,
          "`PopupAnimation.get_scale/get_offset_y` harus tetap tanpa pemanggil "
          "(show/hide/update dipanggil _core.py tapi hasilnya tidak pernah "
          "digambar): %s" % popup_use[:6])
    preview_draw = find_call_sites(r"path_preview\.(draw|show)\b")
    out["path_preview_users"] = {"sites": preview_draw}
    check(len(preview_draw) >= 2,
          "PathPreview harus tetap punya konsumen (draw + show), kalau tidak "
          "port Godot tidak lagi memindahkan perilaku apa pun: %s"
          % preview_draw[:6])
    return out


def build_quality_note():
    try:
        from mobile.perf import Quality
        return {"available": True, "particles": bool(Quality.particles),
                "particle_ratio": float(Quality.particle_ratio),
                "level": str(Quality.level)}
    except Exception as exc:                      # pragma: no cover
        return {"available": False, "particles": True, "particle_ratio": 1.0,
                "level": "unavailable: %s" % exc}


# ══════════════════════════════════════════════════════════
#  5. Kunci statis sisi Godot (tanpa engine: baca sumber .gd)
# ══════════════════════════════════════════════════════════

def gd_read(rel):
    with open(os.path.join(GODOT, rel), encoding="utf-8") as fh:
        return fh.read()


def gd_const(src, name):
    m = re.search(r"^const[ \t]+%s[ \t]*(?::[ \t]*[\w\[\]]+)?[ \t]*(?:=|:=)"
                  r"[ \t]*([^\n#]+)" % re.escape(name), src, re.M)
    return m.group(1).strip() if m else None


def gd_num(src, name):
    raw = gd_const(src, name)
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def gd_array(src, name):
    m = re.search(r"^const[ \t]+%s[ \t]*(?::[ \t]*Array)?[ \t]*(?:=|:)[ \t]*"
                  r"\[([^\]]*)\]" % re.escape(name), src, re.M)
    if not m:
        return None
    try:
        return [float(x) for x in m.group(1).split(",") if x.strip()]
    except ValueError:
        return None


_GD_FAILS = []


def gd_check(cond, msg):
    if cond:
        PASS.append("godot-source")
    else:
        _GD_FAILS.append(msg)


def _eq(got, want):
    if got is None:
        return False
    return len(got) == len(want) and all(
        abs(float(a) - float(b)) < 1e-9 for a, b in zip(got, want))


def check_godot_source(fixture):
    pins = fixture["py_pins"]
    spark = gd_read("scripts/render/HitSpark.gd")
    for name, want in (("GRAVITY", pins["gravity"][0]),
                       ("FRICTION", pins["friction"][0]),
                       ("SPEED_MIN", 1.0), ("SPEED_MAX", 3.0)):
        got = gd_num(spark, name)
        gd_check(got is not None and abs(got - float(want)) < 1e-9,
                 "HitSpark.%s harus %s, dapat %s" % (name, want, got))
    gd_check(_eq(gd_array(spark, "DEFAULT_COLOR"), [255, 200, 100]),
             "HitSpark.DEFAULT_COLOR harus (255,200,100) pygame")
    for needle, why in (
            ("x += vx", "posisi diperbarui lebih dulu"),
            ("vy += gravity", "gravitasi ditambahkan SETELAH posisi "
                              "(urutan `HitParticle.update`)"),
            ("vx *= FRICTION", "gesekan 0.95 hanya pada sumbu x"),
            ("if lifetime <= 0:", "mati saat lifetime habis, bukan < 0"),
            ("int(255.0 * ratio)", "alpha = int(255 * sisa umur)"),
            ("maxi(1, int(float(size) * ratio))",
             "ukuran = max(1, int(size * ratio)) — menyusut, tidak hilang"),
            ("- float(int(floorf(side / 2.0))) + center * factor",
             "pusat sprite = posisi blit + pusat kanvas x faktor skala "
             "(pygame mem-blit di `int(x) - ukuran*3//2`; base genap + ukuran "
             "gasal jatuh di setengah piksel — jejak fixture menguncinya)")):
        gd_check(needle in spark, "HitSpark.gd: %s" % why)

    burst = gd_read("scripts/render/DeathBurst.gd")
    for name, want in (("FLASH_MAX", 8), ("FLASH_RADIUS", 20),
                       ("PRESET_SMALL_COUNT", 8), ("PRESET_MEDIUM_COUNT", 15),
                       ("PRESET_LARGE_COUNT", 25), ("SPEED_MIN", 1.5),
                       ("SPEED_MAX", 4.0), ("LIFE_MIN", 20), ("LIFE_MAX", 35)):
        got = gd_num(burst, name)
        gd_check(got is not None and abs(got - float(want)) < 1e-9,
                 "DeathBurst.%s harus %s, dapat %s" % (name, want, got))
    gd_check(_eq(gd_array(burst, "PRESET_SMALL_SPARK"), [2, 4])
             and _eq(gd_array(burst, "PRESET_MEDIUM_SPARK"), [3, 5])
             and _eq(gd_array(burst, "PRESET_LARGE_SPARK"), [4, 6]),
             "DeathBurst rentang spark small/medium/large harus (2,4)/(3,5)/(4,6)")
    gd_check(_eq(gd_array(burst, "FLASH_COLOR"), [255, 255, 200]),
             "DeathBurst.FLASH_COLOR harus (255,255,200)")
    palettes = fixture["palettes"]
    for name, key in (("TEAM_BLUE", "burst_blue"), ("TEAM_RED", "burst_red")):
        got = re.search(r"^const[ \t]+%s[ \t]*:[ \t]*Array[ \t]*=[ \t]*(\[\[.*?\]\])"
                        % name, burst, re.M | re.S)
        gd_check(got is not None,
                 "DeathBurst.%s harus literal array-of-array" % name)
        if got:
            parsed = json.loads(got.group(1))
            gd_check(parsed == palettes[key],
                     "DeathBurst.%s harus %s, dapat %s"
                     % (name, palettes[key], parsed))
    gd_check("not particles.is_empty() or flash_timer > 0" in burst,
             "DeathBurst.is_alive = partikel ADA atau kilat masih jalan")
    ops_body = burst.split("func build_ops()", 1)
    gd_check(len(ops_body) == 2, "DeathBurst harus punya build_ops()")
    if len(ops_body) == 2:
        body = ops_body[1]
        gd_check(0 <= body.index("if flash_timer > 0:")
                 < body.index("for p in particles:"),
                 "kilat pusat digambar SEBELUM partikel (urutan blit pygame "
                 "`DeathExplosion.draw`)")

    field = gd_read("scripts/render/SparkField.gd")
    for name, want in (("MAX_PARTICLES", pins["max_particles"][0]),
                       ("MAX_EXPLOSIONS", pins["max_explosions"][0]),
                       ("HIT_SPEED_MIN", 1.0),
                       ("HIT_SPEED_MAX", pins["hit_speed"][0]),
                       ("HIT_LIFE_MIN", pins["hit_life"][0]),
                       ("HIT_LIFE_MAX", pins["hit_life"][1]),
                       ("HIT_SIZE_MIN", pins["hit_size_range"][0]),
                       ("HIT_SIZE_MAX", pins["hit_size_range"][1])):
        got = gd_num(field, name)
        gd_check(got is not None and abs(got - float(want)) < 1e-9,
                 "SparkField.%s harus %s, dapat %s" % (name, want, got))
    for name, key in (("HIT_BLUE", "hit_blue"), ("HIT_RED", "hit_red")):
        got = re.search(r"^const[ \t]+%s[ \t]*:[ \t]*Array[ \t]*=[ \t]*(\[\[.*?\]\])"
                        % name, field, re.M | re.S)
        gd_check(got is not None, "SparkField.%s harus literal" % name)
        if got:
            parsed = json.loads(got.group(1))
            gd_check(parsed == fixture["palettes"][key],
                     "SparkField.%s harus %s, dapat %s"
                     % (name, fixture["palettes"][key], parsed))
    gd_check("particles.pop_front()" in field and "explosions.pop_front()" in field,
             "trim harus membuang entri TERTUA (pygame `del [0:...]` / `del [0]`)")
    gd_check("_py_round(" in field,
             "pemangkasan count*particle_ratio memakai pembulatan Python "
             "(banker's rounding), bukan roundf Godot")

    preview = gd_read("scenes/fx/PathPreview.gd")
    for name, want in (("DURATION", pins["preview_duration"][0]),
                       ("FADE_IN", pins["preview_fade_in"][0]),
                       ("FADE_OUT", pins["preview_fade_out"][0]),
                       ("BASE_ALPHA", pins["preview_alpha"][0]),
                       ("OFFSET_SPEED", pins["preview_offset"][0]),
                       ("OFFSET_MOD", pins["preview_offset"][1]),
                       ("ARROW_STEP", pins["preview_step"][0]),
                       ("DIR_AHEAD", pins["preview_ahead"][0]),
                       ("PULSE_SHIFT", pins["preview_pulse"][0]),
                       ("PULSE_CYCLE", pins["preview_pulse"][1]),
                       ("SIZE_PULSE", 8), ("SIZE_DIM", 5)):
        got = gd_num(preview, name)
        gd_check(got is not None and abs(got - float(want)) < 1e-9,
                 "PathPreview.%s harus %s, dapat %s" % (name, want, got))
    gd_check(_eq(gd_array(preview, "ARROW_COLOR"), [255, 100, 100]),
             "PathPreview.ARROW_COLOR harus (255,100,100)")
    for needle, why in (
            ("floorf((-cos_a * float(size)) / 2.0)",
             "setengah panah memakai FLOOR pygame (`// 2`), bukan trunc"),
            ("int(neg_cos_half - pos_sin_half)",
             "titik ke-2 panah = floor(-cos*S/2) - floor(sin*S/2) — TIDAK boleh "
             "disederhanakan jadi + floor(-sin*S/2) (beda 1 px untuk nilai "
             "non-bulat; jejak polygon fixture menguncinya)"),
            ("int(neg_sin_half - pos_cos_half)",
             "titik ke-3 panah = floor(-sin*S/2) - floor(cos*S/2)"),
            ("(int(floorf(float(i) / float(ARROW_STEP))) + shift)",
             "pulse = (i // 8 + offset // 5) % 4"),
            ("while i < count - 1:", "range(0, len-1, 8) — titik terakhir dilewati"),
            ("if dist == 0.0:", "`math.hypot(...) or 1` pygame: jarak 0 jadi 1")):
        gd_check(needle in preview, "PathPreview.gd: %s" % why)

    # Situs pemanggil Godot vs jumlah pygame.
    by_class = fixture["call_sites"]["by_class"]
    combat = gd_read("scripts/systems/CombatSystem.gd")
    body = combat.split("func _hit_spark_count(", 1)
    gd_check(len(body) == 2, "CombatSystem harus punya _hit_spark_count")
    if len(body) == 2:
        counts = body[1].split("func ", 1)[0]
        for needle, cls, why in (("return 4", "Minion", "minion 4 percikan"),
                                 ("return 6", "Boss", "boss 6 percikan"),
                                 ("return 10", "Castle", "castle 10 percikan")):
            want = by_class.get(cls, [None])[0]
            gd_check(needle in counts and want == int(needle.split()[1]),
                     "CombatSystem._hit_spark_count %s (%s) harus %s, pygame %s"
                     % (why, cls, needle, want))
        gd_check("return 0" in counts,
                 "hero & menara tidak punya call site pygame -> 0 percikan")
    gd_check("GameManager.spark_fx.add_hit_particles(" in combat,
             "percikan harus lewat SparkField milik GameManager (satu "
             "EffectManager global), bukan list per-node")

    minion = gd_read("scenes/minion/Minion.gd")
    gd_check('add_death_explosion(global_position.x,' in minion
             and 'global_position.y, team, "medium")' in minion,
             "Minion.die harus memicu ledakan 'medium' (paritas _entity.py:5863)")
    boss = gd_read("scenes/boss/Boss.gd")
    gd_check('add_death_explosion(global_position.x,' in boss
             and 'global_position.y, team, "large")' in boss,
             "Boss.die harus memicu ledakan 'large' (paritas base_boss.py:6076)")
    tactical = gd_read("scripts/systems/TacticalCommands.gd")
    smalls = re.findall(r'add_death_explosion\([^\n]*\n?[^\n]*"small"\)',
                        tactical)
    gd_check(len(smalls) == 2,
             "TacticalCommands harus memicu 2 ledakan 'small' (gather + "
             "protect castle), dapat %d" % len(smalls))

    main = gd_read("scenes/main/Main.gd")
    gd_check('_show_path_preview()' in main
             and "func _on_wave_started(" in main,
             "path preview harus dipicu dari _on_wave_started (paritas "
             "_core.py:1762 di blok wave-start)")
    gd_check('const PREVIEW_LANES: Array = ["top", "mid", "bot"]' in main,
             "urutan lane preview harus top, mid, bot (paritas _core.py:1757)")
    gm = gd_read("scripts/autoload/GameManager.gd")
    gd_check("var spark_fx = SparkFieldScript.new()" in gm
             and "spark_fx.advance(delta)" in gm
             and gm.count("spark_fx.reset()") == 2,
             "GameManager memiliki + men-tick spark_fx dan meresetnya di "
             "start_level + return_to_menu")
    if _GD_FAILS:
        print("[render_fx] %d kunci statis Godot gagal:" % len(_GD_FAILS))
        for f in _GD_FAILS:
            print("  - " + f)
        return False
    return True


# ══════════════════════════════════════════════════════════
#  main
# ══════════════════════════════════════════════════════════

def _choice_options(calls):
    """Daftar warna yang pygame sodorkan ke `random.choice` (urutan asli)."""
    for c in calls:
        if c["fn"] == "choice":
            return [list(x) for x in c["args"][0]]
    raise AssertionError("tidak ada random.choice terekam")


def _palettes(rend):
    """Palet DIBACA dari pygame (argumen `random.choice` yang direkam),
    bukan disalin dari kode."""
    effects = rend.EffectManager()
    out = {}
    for key, team, kind in (("burst_blue", "blue", "burst"),
                            ("burst_red", "red", "burst"),
                            ("hit_blue", "blue", "hit"),
                            ("hit_red", "red", "hit")):
        with RecordingRandom(11) as rec:
            if kind == "burst":
                rend.DeathExplosion(0, 0, team=team, size="small")
            else:
                effects.particles = []
                effects.add_hit_particles(0, 0, team=team, count=5)
        out[key] = _choice_options(rec.calls)
    check(len(out["burst_blue"]) == 3 and len(out["burst_red"]) == 3,
          "palet ledakan harus 3 warna per tim, dapat %s / %s"
          % (out["burst_blue"], out["burst_red"]))
    check(len(out["hit_blue"]) == 2 and len(out["hit_red"]) == 2,
          "palet percikan pukulan harus 2 warna per tim, dapat %s / %s"
          % (out["hit_blue"], out["hit_red"]))
    return out


def build_fixture():
    import pygame
    pygame.init()
    pygame.display.set_mode((1, 1))
    pygame.font.init()
    import _core                      # noqa: F401 (alias `settings` dini)
    import _render

    pins = pin_render_source()
    call_sites = pin_call_sites()
    restore = _install_capture_patch(pygame)
    try:
        palettes = _palettes(_render)
        sparks = build_spark_scenarios(pygame, _render)
        bursts = build_burst_scenarios(pygame, _render)
        hits = build_hit_scenarios(pygame, _render)
        caps = build_caps(pygame, _render)
        preview = build_path_preview(pygame, _render, _core)
    finally:
        restore()

    fixture = {
        "_generated_by": "tools/test_render_parity.py --write-fixture",
        "py_pins": pins,
        "call_sites": call_sites,
        "palettes": palettes,
        "py_quality": build_quality_note(),
        "spark": sparks,
        "burst": bursts,
        "hit": hits,
        "caps": caps,
        "path_preview": preview,
        "dead": build_dead_claims(),
    }
    return fixture


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-fixture", action="store_true")
    args = ap.parse_args()
    fixture = build_fixture()
    text = json.dumps(fixture, indent=1, sort_keys=True) + "\n"
    if args.write_fixture:
        with open(FIXTURE, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("[render_fx] fixture ditulis: %s (%d byte, %d pemeriksaan)"
              % (os.path.relpath(FIXTURE, ROOT), len(text), len(PASS)))
        return
    if not os.path.exists(FIXTURE):
        raise AssertionError("fixture belum ada — jalankan "
                             "tools/test_render_parity.py --write-fixture")
    with open(FIXTURE, encoding="utf-8") as fh:
        old = fh.read()
    check(old.strip() == text.strip(),
          "fixture render_fx.json basi: perilaku pygame berubah — sesuaikan "
          "Godot lalu regenerasi dengan --write-fixture")
    again = json.dumps(build_fixture(), indent=1, sort_keys=True) + "\n"
    check(again == text, "fixture harus deterministik antar run")
    if not check_godot_source(fixture):
        raise SystemExit(1)
    print("[render_fx] %d pemeriksaan oracle + kunci statis Godot lulus"
          % len(PASS))


if __name__ == "__main__":
    main()
