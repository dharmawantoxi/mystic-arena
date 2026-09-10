#!/usr/bin/env python3
"""
visual_parity_audit.py — Audit PARITAS VISUAL pygame ↔ Godot dalam satu perintah.

Kenapa alat ini ada
-------------------
Dulu untuk menjawab "apa yang beda antara tampilan Godot dan pygame?" harus
membuka ratusan berkas satu-satu. Alat ini menjalankan semua pemeriksaan
yang bisa diotomatiskan dan mencetak SATU tabel PASS/FAIL. Keluar dengan
kode 1 kalau ada FAIL, jadi bisa langsung dipasang di CI.

Sumber kebenaran TUNGGAL = pygame. Godot hanya boleh membaca:
  * tools/convert_to_godot.py            -> godot/data/*.json
  * tools/convert_to_godot.py --units-png-> godot/assets/units/*.png
  * tools/convert_to_godot.py --maps-png -> godot/assets/maps/*.png
  * tools/convert_to_godot.py --props-png-> godot/assets/props/*.png
  * tools/gen_boss_smart_ai.py           -> godot/scenes/boss/BossKit.gd
  * tools/gen_hero_skill_kit.py          -> godot/scenes/hero/HeroSkillKit.gd

Pemeriksaan
-----------
  1. PALET      — konstanta warna ui_theme.py vs UiTheme.gd (harus identik).
  2. ENCODER    — bake harus deterministik (tidak boleh bergantung pada
                  ada/tidaknya Pillow). Dulu ini menghasilkan 445 strip
                  berbeda hanya karena beda mesin.
  3. FRESH-UNIT — re-bake strip unit, bandingkan byte dengan yang ada.
  4. FRESH-MAP  — re-bake tekstur map, bandingkan byte dengan yang ada.
  5. COVERAGE   — tiap subsistem visual punya jalur setia di Godot?
                  (bake/ported) atau masih placeholder geometris?
  6. SMOKE      — panggil SEMUA renderer pygame (minion + tower + sample
                  hero/boss) dan laporkan yang melempar exception.
  7. HARDCODE   — warna Color("#...") yang ditulis langsung di .gd padahal
                  UiTheme sudah punya namanya (sumber drift warna).

Pemakaian
---------
  python3 tools/visual_parity_audit.py              # cepat (~30 dtk)
  python3 tools/visual_parity_audit.py --full       # re-bake SEMUA (222 unit + 54 map)
  python3 tools/visual_parity_audit.py --report md  # tulis docs/PARITY_AUDIT.md
  python3 tools/visual_parity_audit.py --section palette,encoder

Butuh pygame-ce (dan Pillow untuk bake strip unit).
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

GODOT = os.path.join(ROOT, "godot")


# ══════════════════════════════════════════════════════════════════
#  Infrastruktur laporan
# ══════════════════════════════════════════════════════════════════

## Penanda blok yang ditulis mesin di docs/PARITY_AUDIT.md. Isi di luar
## penanda ini adalah laporan kurasi (ditulis manusia) dan TIDAK boleh
## disentuh `--report md`.
BEGIN = "<!-- BEGIN AUTO AUDIT -->"
END = "<!-- END AUTO AUDIT -->"


def _env_lines():
    """Versi pustaka — dicantumkan di laporan supaya drift encoder mudah
    dilacak (audit ini sensitif terhadap versi Pillow/pygame-ce)."""
    out = ["Python " + sys.version.split()[0]]
    try:
        import PIL
        out.append("Pillow " + PIL.__version__)
    except Exception:
        out.append("Pillow TIDAK ADA")
    try:
        import pygame
        out.append("pygame " + pygame.version.ver)
    except Exception:
        out.append("pygame TIDAK ADA")
    out.append("SDL_VIDEODRIVER=" + os.environ.get("SDL_VIDEODRIVER", "-"))
    return out


class Report:
    def __init__(self):
        self.sections = []   # [(nama, status, [baris...])]
        self.env = []        # baris info lingkungan

    def add(self, name, ok, lines=None, warn_only=False):
        status = "PASS" if ok else ("WARN" if warn_only else "FAIL")
        self.sections.append((name, status, lines or []))

    @property
    def failed(self):
        return [s for s in self.sections if s[1] == "FAIL"]

    def text(self):
        out = ["═" * 72,
               "AUDIT PARITAS VISUAL  pygame ↔ Godot",
               "═" * 72]
        if self.env:
            out.append("lingkungan: " + "  |  ".join(self.env))
        for name, status, lines in self.sections:
            mark = {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "❌"}[status]
            out.append("")
            out.append("%s %-10s %s" % (mark, status, name))
            for ln in lines:
                out.append("      %s" % ln)
        out.append("")
        out.append("─" * 72)
        n_fail = len(self.failed)
        n_warn = len([s for s in self.sections if s[1] == "WARN"])
        out.append("RINGKASAN: %d PASS, %d WARN, %d FAIL"
                   % (len(self.sections) - n_fail - n_warn, n_warn, n_fail))
        if n_fail:
            out.append("Gagal: " + ", ".join(s[0] for s in self.failed))
        out.append("═" * 72)
        return "\n".join(out)


def _gd_files():
    files = []
    for dirpath, dirnames, filenames in os.walk(GODOT):
        if ".git" in dirpath:
            continue
        for fn in filenames:
            if fn.endswith(".gd"):
                files.append(os.path.join(dirpath, fn))
    return sorted(files)


def _read(path):
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read()


# ══════════════════════════════════════════════════════════════════
#  1. PALET — ui_theme.py vs UiTheme.gd
# ══════════════════════════════════════════════════════════════════

def _py_colours(src):
    out = {}
    for m in re.finditer(r'^([A-Z][A-Z0-9_]*)\s*=\s*\(([^)]*)\)', src, re.M):
        nums = [int(x) for x in re.findall(r'\d+', m.group(2))]
        if len(nums) >= 3:
            out[m.group(1)] = tuple(nums[:4]) if len(nums) == 4 else tuple(nums[:3])
    return out


def _num(tok):
    tok = tok.strip()
    if "/" in tok:
        a, b = tok.split("/")
        return float(a) / float(b)
    return float(tok.rstrip("f"))


def _gd_colours(src):
    out = {}
    for m in re.finditer(
            r'^const\s+([A-Z][A-Z0-9_]*)\s*:=\s*Color\("(#?[0-9a-fA-F]{3,8})"\)',
            src, re.M):
        h = m.group(2).lstrip("#")
        if len(h) in (6, 8):
            out[m.group(1)] = tuple(int(h[i:i + 2], 16) for i in range(0, len(h), 2))
    for m in re.finditer(r'^const\s+([A-Z][A-Z0-9_]*)\s*:=\s*Color\(([^)]*)\)',
                         src, re.M):
        name, body = m.group(1), m.group(2)
        if '"' in body or "#" in body:
            continue
        try:
            nums = [_num(x) for x in body.split(",")]
        except ValueError:
            continue
        if len(nums) >= 3:
            out[name] = tuple(int(round(v * 255)) if v <= 1.0001 else int(round(v))
                              for v in nums[:min(4, len(nums))])
    return out


def check_palette():
    py = _py_colours(_read(os.path.join(ROOT, "ui_theme.py")))
    gd = _gd_colours(_read(os.path.join(GODOT, "scripts", "utils", "UiTheme.gd")))
    common = sorted(set(py) & set(gd))
    bad = [(k, py[k], gd[k]) for k in common if py[k] != gd[k]]
    only_py = sorted(set(py) - set(gd))
    lines = ["%d konstanta warna dibandingkan" % len(common)]
    for k, a, b in bad[:20]:
        lines.append("BERBEDA  %-22s pygame=%s  godot=%s" % (k, a, b))
    if only_py:
        lines.append("hanya ada di pygame (tidak dipakai Godot): %s"
                     % ", ".join(only_py[:12]))
    return not bad, lines


# ══════════════════════════════════════════════════════════════════
#  2. ENCODER — bake harus deterministik
# ══════════════════════════════════════════════════════════════════

def check_encoder():
    """Pastikan _save_strip/_save_map_png tidak punya cabang bergantung env."""
    src = _read(os.path.join(ROOT, "tools", "convert_to_godot.py"))
    lines, ok = [], True
    for fname in ("_save_strip", "_save_map_png"):
        m = re.search(r"def %s\(" % fname, src)
        if not m:
            lines.append("%s tidak ditemukan" % fname)
            ok = False
            continue
        start = m.start()
        nxt = re.search(r"\ndef ", src[start + 10:])
        body = src[start:start + 10 + (nxt.start() if nxt else len(src))]
        # Hanya baris KODE (abaikan kemunculan di dalam docstring).
        code_lines = [l for l in body.splitlines()
                      if not re.match(r'^\s*[A-ZÀ-Ý(]', l)]
        code = "\n".join(code_lines)
        # Bahaya BUKAN "except ImportError" itu sendiri (boleh saja untuk
        # menggagalkan bake dengan pesan jelas), melainkan except yang
        # DIAM-DIAM memakai ENCODER LAIN -> keluaran bergantung env.
        fallback = False
        m2 = re.search(r'^\s*except\s+importerror.*?:\s*(?:#.*)?$',
                       code, re.M | re.I)
        if m2:
            rest = code[m2.end():]
            # Ambil blok except (sampai baris berikutnya dengan indentasi
            # <= indentasi 'except').
            ind = len(m2.group(0)) - len(m2.group(0).lstrip())
            blk = []
            for l in rest.splitlines():
                if l.strip() and (len(l) - len(l.lstrip())) <= ind:
                    break
                blk.append(l)
            block = "\n".join(blk)
            if "pygame.image.save" in block or "tobytes" in block:
                fallback = True
        if fallback:
            lines.append("%s masih punya fallback `except ImportError` -> "
                         "keluaran bake bergantung Pillow" % fname)
            ok = False
        elif "PIL" in body and fname == "_save_map_png":
            lines.append("%s memakai Pillow -> map terkuantisasi, "
                         "banding di area gradasi" % fname)
            ok = False
        else:
            lines.append("%s deterministik" % fname)

    # Renderer minion tim merah punya dua jalur: numpy vs BLEND_*. Kalau
    # numpy tidak ada di mesin yang menjalankan bake, minion merah dibakar
    # dengan warna yang BERBEDA — penyebab CI pernah gagal FRESH-PROP
    # sementara mesin lokal lulus. Bake kini menuntut numpy.
    if "_require_numpy" in src:
        lines.append("bake menuntut numpy (tanpa numpy: minion merah beda "
                     "piksel)")
    else:
        lines.append("TIDAK ADA penjaga numpy -> jalur BLEND_* bisa aktif "
                     "tanpa numpy")
        ok = False
    try:
        import numpy
        lines.append("numpy tersedia (%s)" % numpy.__version__)
    except ImportError:
        lines.append("numpy TIDAK ADA -> bake akan gagal sekarang")
        ok = False
    return ok, lines


# ══════════════════════════════════════════════════════════════════
#  3/4. FRESHNESS — re-bake lalu bandingkan byte
# ══════════════════════════════════════════════════════════════════

def _run(cmd, timeout=1800):
    env = os.environ.copy()
    env.setdefault("SDL_VIDEODRIVER", "dummy")
    env.setdefault("SDL_AUDIODRIVER", "dummy")
    env.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    return subprocess.run(cmd, shell=True, cwd=ROOT, env=env,
                          capture_output=True, text=True, timeout=timeout)


def _snapshot(d):
    out = {}
    for fn in sorted(os.listdir(d)):
        if fn.endswith(".png"):
            p = os.path.join(d, fn)
            out[fn] = (os.path.getsize(p), _md5(p))
    return out


def _md5(path, block=1 << 20):
    import hashlib
    h = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            b = f.read(block)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def _git_show(rel):
    """Isi berkas `rel` (relatif ROOT) pada commit tersimpan. None kalau gagal."""
    res = subprocess.run(["git", "show", "HEAD:%s" % rel], cwd=ROOT,
                         capture_output=True)
    if res.returncode != 0:
        return None
    return res.stdout


def _pixels_equal_bytes(old_blob, new_path):
    """True kalau PNG tersimpan dan PNG baru IDENTIK secara piksel."""
    from PIL import Image
    import io
    try:
        with Image.open(io.BytesIO(old_blob)) as ia, \
                Image.open(new_path) as ib:
            if ia.size != ib.size or ia.mode != ib.mode:
                return False
            return ia.tobytes() == ib.tobytes()
    except Exception:
        return False


def _git_restore(rels, lines):
    """Kembalikan berkas ke isi tersimpan (dibatch biar aman)."""
    for i in range(0, len(rels), 40):
        batch = rels[i:i + 40]
        res = subprocess.run(["git", "checkout", "--"] + batch, cwd=ROOT,
                             capture_output=True, text=True)
        if res.returncode != 0:
            lines.append("   gagal mengembalikan %d berkas: %s"
                         % (len(batch), (res.stderr or "")[:120]))


def _classify_stale(stale_rels, lines):
    """Pisahkan 'beda byte' jadi BEDA ISI (FAIL) vs DRIFT ENCODER (WARN).

    Gerbang ini semula membandingkan byte mentah. Itu benar di satu mesin,
    tetapi di CI — yang memasang pygame-ce/Pillow terbaru tanpa patokan —
    ia gagal meski hasil bake IDENTIK secara visual, karena encoder PNG
    versi lain menghasilkan berkas berbeda untuk piksel yang sama. Audit
    ini mengukur PARITAS VISUAL, jadi yang menentukan adalah isinya:
      * piksel berubah -> bake benar-benar usang -> FAIL
      * piksel identik -> hanya beda encoder    -> WARN, berkas dikembalikan
                          ke isi tersimpan supaya working tree tetap bersih
    """
    real, drift = [], []
    for rel in stale_rels:
        old = _git_show(rel)
        if old is not None and _pixels_equal_bytes(old,
                                                   os.path.join(ROOT, rel)):
            drift.append(rel)
        else:
            real.append(rel)
    if real:
        lines.append("USANG — isi piksel berubah (%d): %s"
                     % (len(real), ", ".join(os.path.basename(x)
                                             for x in real[:12])))
    if drift:
        lines.append("DRIFT ENCODER (%d berkas): byte berbeda, piksel IDENTIK"
                     % len(drift))
        lines.append("   penyebab: versi Pillow/pygame-ce di mesin ini beda "
                     "dengan yang menghasilkan bake tersimpan")
        lines.append("   bukan divergensi visual -> tidak digagalkan; "
                     "berkas dikembalikan ke isi tersimpan")
        lines.append("   contoh: %s"
                     % ", ".join(os.path.basename(x) for x in drift[:8]))
        _git_restore(drift, lines)
    return real, drift


def check_fresh_units(full=False, sample=8):
    import json as _json
    units_dir = os.path.join(GODOT, "assets", "units")
    manifest_p = os.path.join(GODOT, "data", "baked_units.json")
    if not os.path.isdir(units_dir) or not os.path.exists(manifest_p):
        return False, ["godot/assets/units atau baked_units.json tidak ada"]
    manifest = _json.loads(_read(manifest_p))
    types = sorted(manifest.get("units", {}))
    if not full:
        # Sampel merata (awal/tengah/akhir) + unit yang pernah bermasalah.
        forced = [t for t in ("drakar", "kaizen", "sasori", "vex")
                  if t in types]
        step = max(1, len(types) // max(1, sample))
        picked = list(dict.fromkeys(forced + types[::step][:sample]))
    else:
        picked = None  # None = bake semua

    before = _snapshot(units_dir)
    mbefore = _md5(manifest_p)
    cmd = "python3 tools/convert_to_godot.py --units-png"
    if picked:
        cmd += " --only " + ",".join(picked)
    res = _run(cmd)
    if res.returncode != 0:
        return False, ["bake gagal: %s" % (res.stderr or res.stdout)[-400:]]
    after = _snapshot(units_dir)
    mafter = _md5(manifest_p)

    stale = [os.path.relpath(os.path.join(units_dir, fn), ROOT)
             for fn in before if fn in after and after[fn] != before[fn]]
    lines = []
    if picked:
        lines.append("dibandingkan %d unit (sampel dari %d)"
                     % (len(picked), len(types)))
    else:
        lines.append("dibandingkan semua %d unit" % len(types))
    _drift = []
    if stale:
        stale, _drift = _classify_stale(stale, lines)
    if mbefore != mafter and not picked:
        lines.append("baked_units.json berubah -> Godot membaca data lama")
    elif mbefore != mafter:
        lines.append("(manifest tidak ditulis karena mode --only)")
    return (not stale), lines, False


def check_fresh_maps(full=False, sample=4):
    maps_dir = os.path.join(GODOT, "assets", "maps")
    manifest_p = os.path.join(GODOT, "data", "map_bakes.json")
    if not os.path.isdir(maps_dir):
        return False, ["godot/assets/maps tidak ada"]
    names = sorted(f[:-4] for f in os.listdir(maps_dir) if f.endswith(".png"))
    if not full:
        step = max(1, len(names) // max(1, sample))
        picked = names[::step][:sample]
    else:
        picked = None
    before = _snapshot(maps_dir)
    mbefore = _md5(manifest_p) if os.path.exists(manifest_p) else ""
    cmd = "python3 tools/convert_to_godot.py --maps-png"
    if picked:
        cmd += " --only " + ",".join(picked)
    res = _run(cmd)
    if res.returncode != 0:
        return False, ["bake gagal: %s" % (res.stderr or res.stdout)[-400:]]
    after = _snapshot(maps_dir)
    mafter = _md5(manifest_p) if os.path.exists(manifest_p) else ""
    stale = [os.path.relpath(os.path.join(maps_dir, fn), ROOT)
             for fn in before if fn in after and after[fn] != before[fn]]
    lines = []
    if picked:
        lines.append("dibandingkan %d map (sampel dari %d)"
                     % (len(picked), len(names)))
    else:
        lines.append("dibandingkan semua %d map" % len(names))
    _drift = []
    if stale:
        stale, _drift = _classify_stale(stale, lines)
    if picked and mbefore != mafter:
        # Mode --only map TIDAK menulis manifest -> kembalikan berkasnya.
        try:
            _run("git checkout -- godot/data/map_bakes.json", timeout=60)
        except Exception:
            pass
        lines.append("(map_bakes.json dikembalikan: mode --only)")
    return (not stale), lines, False


def check_fresh_props(full=False):
    """Re-bake props (minion/menara/nexus) lalu bandingkan byte."""
    props_dir = os.path.join(GODOT, "assets", "props")
    manifest_p = os.path.join(GODOT, "data", "baked_props.json")
    if not os.path.isdir(props_dir):
        return False, ["godot/assets/props tidak ada — jalankan "
                       "tools/convert_to_godot.py --props-png"]
    before = _snapshot(props_dir)
    mbefore = _md5(manifest_p) if os.path.exists(manifest_p) else ""
    res = _run("python3 tools/convert_to_godot.py --props-png")
    if res.returncode != 0:
        return False, ["bake gagal: %s" % (res.stderr or res.stdout)[-400:]]
    after = _snapshot(props_dir)
    mafter = _md5(manifest_p) if os.path.exists(manifest_p) else ""
    stale = [os.path.relpath(os.path.join(props_dir, fn), ROOT)
             for fn in before if fn in after and after[fn] != before[fn]]
    lines = ["dibandingkan %d strip props" % len(after)]
    _drift = []
    if stale:
        stale, _drift = _classify_stale(stale, lines)
    if mbefore != mafter:
        lines.append("baked_props.json berubah -> Godot membaca data lama")
    return (not stale), lines, bool(_drift)


# ══════════════════════════════════════════════════════════════════
#  5. COVERAGE — tiap subsistem visual punya jalur setia?
# ══════════════════════════════════════════════════════════════════

def _count_lines(path):
    try:
        return len(_read(path).splitlines())
    except OSError:
        return 0


def check_coverage():
    """Subsistem visual: apakah Godot menggambar dari bake pygame?"""
    lines = []
    missing = []

    # (label, manifest, kunci, jumlah minimum entri yang diharapkan)
    # Minion 5 jenis x 2 tim, menara 4 jenis x 2 tim, nexus 2 tim.
    specs = [
        ("hero/boss", os.path.join(GODOT, "data", "baked_units.json"), "units",
         222),
        ("map", os.path.join(GODOT, "data", "map_bakes.json"), "maps", 54),
        ("minion", os.path.join(GODOT, "data", "baked_props.json"),
         "minions", 10),
        ("tower", os.path.join(GODOT, "data", "baked_props.json"),
         "towers", 8),
        ("nexus", os.path.join(GODOT, "data", "baked_props.json"),
         "nexus", 2),
    ]
    seen_props = False
    for label, mpath, key, expect in specs:
        if not os.path.exists(mpath):
            lines.append("%-10s BELUM ADA BAKE (manifest %s tidak ada)"
                         % (label, os.path.basename(mpath)))
            missing.append(label)
            continue
        if key in ("minions", "towers", "nexus"):
            if not seen_props:
                data = json.loads(_read(mpath))
                seen_props = True
            got = len(data.get(key, {}))
        else:
            data = json.loads(_read(mpath))
            got = len(data.get(key, {}))
        if got < expect:
            lines.append("%-10s bake %d/%d (target %d)" % (label, got, got, expect))
        else:
            lines.append("%-10s bake %d entri" % (label, got))
        if got == 0:
            missing.append(label)

    # Deteksi renderer placeholder geometris di Godot (jumlah primitif
    # gambar jauh lebih kecil dari renderer pygame-nya).
    placeholders = [
        ("tower", "godot/scenes/tower/Tower.gd", "towers/_bundle.py"),
        ("minion", "godot/scripts/render/UnitSilhouette.gd",
         "minions/_bundle.py"),
        ("nexus", "godot/scenes/base/Nexus.gd", "_entity.py"),
    ]
    for label, gdrel, pyrel in placeholders:
        gd_path = os.path.join(ROOT, gdrel)
        py_path = os.path.join(ROOT, pyrel)
        if not os.path.exists(gd_path):
            continue
        gd_src = _read(gd_path)
        n_calls = len(re.findall(r'\bdraw_[a-z_]+\(', gd_src))
        py_lines = _count_lines(py_path)
        lines.append("%-10s Godot %-42s %3d primitif  vs  pygame %-22s %5d baris"
                     % (label, gdrel.split("/")[-1], n_calls,
                        pyrel, py_lines))
        if label in missing:
            lines.append("           ^ placeholder geometris — Godot TIDAK "
                         "memakai seni pygame")

    return not missing, lines


# ══════════════════════════════════════════════════════════════════
#  6. GEOMETRI — setiap frame di manifest harus MUAT di dalam PNG
# ══════════════════════════════════════════════════════════════════
#
# Kenapa perlu: Godot mengiris strip memakai AtlasTexture dari angka di
# manifest. Kalau indeks/anchor meleset sedikit saja, unit tampil sebagai
# kotak kosong, terpotong, atau melayang — dan satu-satunya cara tahu
# adalah menjalankan Godot dan melihat 222 unit satu-satu. Pemeriksaan ini
# menjawabnya TANPA engine: semua region harus muat di dalam berkas PNG,
# dan titik jangkar harus berada di dalam sel.
#
# Nyata: pemeriksaan inilah yang menangkap anchor nexus (107) yang keluar
# dari tinggi sel (106) sebelum Fase 7 digabung.

def _img_size(res_path):
    """Ukuran (px, py) berkas `res://...` di dalam godot/. None kalau absen."""
    from PIL import Image
    rel = str(res_path).replace("res://", "")
    if not rel:
        return None
    path = os.path.join(GODOT, rel)
    if not os.path.exists(path):
        return None
    with Image.open(path) as im:
        return im.size


## Jumlah frame strip dasar/rage: idle 8 + walk 8 + attack 8 (Fase 5).
UNIT_STYLE_FRAMES = 24


def _check_regions(label, entries, problems):
    """Validasi kumpulan entri manifest: region & anchor harus valid."""
    checked = 0
    for key, e in sorted(entries.items()):
        if not isinstance(e, dict):
            problems.append("%s/%s: entri bukan objek" % (label, key))
            continue
        fpr = int(e.get("frames_per_row", 8))
        # Kumpulkan (berkas, lebar sel, tinggi sel, anchor, [indeks...]).
        # PENTING: strip skill/rage adalah berkas TERPISAH dengan ukuran
        # sel sendiri — jangan divalidasi terhadap strip dasar.
        groups = []
        base_size = _img_size(e.get("png", ""))
        if base_size is None:
            problems.append("%s/%s: berkas tidak ada %s"
                            % (label, key, e.get("png", "")))
            continue
        fw = int(e.get("frame_w", 0))
        fh = int(e.get("frame_h", 0))
        anchor = e.get("anchor", [0, 0])
        idxs = []
        anims = e.get("anims", {})
        if isinstance(anims, dict) and anims:
            for name, spec in anims.items():
                if isinstance(spec, list) and len(spec) == 2:
                    idxs.extend(range(int(spec[0]),
                                      int(spec[0]) + int(spec[1])))
        # menara: levels -> {level: {"idle": [...], "shoot": [...]}}
        levels = e.get("levels", {})
        if isinstance(levels, dict) and levels:
            for lv, spec in levels.items():
                if isinstance(spec, dict):
                    for k2 in ("idle", "shoot"):
                        for i in spec.get(k2, []):
                            idxs.append(int(i))
                else:
                    idxs.append(int(spec))
        # nexus: levels -> {level: indeks}
        # (sudah tercakup cabang else di atas)
        groups.append((base_size, fw, fh, anchor, idxs))
        # strip skill (Fase 5c) — berkas & geometri sendiri
        if e.get("skill_frame_w"):
            ssize = _img_size(e.get("skills_png", ""))
            if ssize is None:
                problems.append("%s/%s: berkas skill tidak ada %s"
                                % (label, key, e.get("skills_png", "")))
            else:
                sfw = int(e.get("skill_frame_w", 0))
                sfh = int(e.get("skill_frame_h", 0))
                sanchor = e.get("skill_anchor", [0, 0])
                sidx = []
                sanims = e.get("skill_anims", {})
                if isinstance(sanims, dict):
                    for name, spec in sanims.items():
                        if isinstance(spec, list) and len(spec) == 2:
                            sidx.extend(range(int(spec[0]),
                                              int(spec[0]) + int(spec[1])))
                groups.append((ssize, sfw, sfh, sanchor, sidx))
        # strip rage (Fase 5c) — berkas & geometri sendiri
        if e.get("rage_frame_w"):
            rsize = _img_size(e.get("rage_png", ""))
            if rsize is None:
                problems.append("%s/%s: berkas rage tidak ada %s"
                                % (label, key, e.get("rage_png", "")))
            else:
                rfw = int(e.get("rage_frame_w", 0))
                rfh = int(e.get("rage_frame_h", 0))
                ranchor = e.get("rage_anchor", [0, 0])
                # Layout rage = layout strip dasar ([idle 8|walk 8|attack 8]).
                groups.append((rsize, rfw, rfh, ranchor,
                               list(range(UNIT_STYLE_FRAMES))))
        for (size, gw, gh, ganchor, gidx) in groups:
            iw, ih = size
            if gw <= 0 or gh <= 0:
                problems.append("%s/%s: ukuran sel %sx%s tidak valid"
                                % (label, key, gw, gh))
                continue
            checked += 1
            if not gidx:
                continue
            for i in gidx:
                col, row = i % fpr, i // fpr
                x1 = (col + 1) * gw
                y1 = (row + 1) * gh
                if x1 > iw or y1 > ih:
                    problems.append(
                        "%s/%s: frame %d keluar dari PNG (%d,%d > %dx%d)"
                        % (label, key, i, x1, y1, iw, ih))
                    break
            if isinstance(ganchor, list) and len(ganchor) >= 2:
                ax, ay = float(ganchor[0]), float(ganchor[1])
                if not (0.0 <= ax <= gw and 0.0 <= ay <= gh):
                    problems.append(
                        "%s/%s: anchor (%g,%g) di luar sel %dx%d"
                        % (label, key, ax, ay, gw, gh))
    return checked


def check_geometry():
    """Semua frame & anchor di baked_units.json / baked_props.json valid."""
    problems = []
    total = 0
    up = os.path.join(GODOT, "data", "baked_units.json")
    pp = os.path.join(GODOT, "data", "baked_props.json")
    if os.path.exists(up):
        d = json.loads(_read(up))
        total += _check_regions("unit", d.get("units", {}), problems)
    if os.path.exists(pp):
        d = json.loads(_read(pp))
        for sec in ("minions", "towers", "nexus"):
            total += _check_regions(sec, d.get(sec, {}), problems)
    lines = ["%d grup frame divalidasi (region + anchor)" % total]
    for p in problems[:20]:
        lines.append("  %s" % p)
    if problems:
        lines.append("  → %d masalah: sprite akan tampil kosong/terpotong "
                     "di Godot" % len(problems))
    return not problems, lines


# ══════════════════════════════════════════════════════════════════
#  7. CALLGROUP — call_group ke metode yang tak ada = NO-OP senyap
# ══════════════════════════════════════════════════════════════════
#
# Inilah penyebab screen shake mati total tanpa ada yang tahu: Boss.gd /
# Hero.gd memanggil call_group("camera", "add_trauma", ...) tetapi tidak ada
# satu pun skrip yang mendefinisikan `add_trauma`. Godot tidak error — ia
# diam saja, dan efeknya hilang dari layar. Pemeriksaan ini mencocokkan
# SETIAP metode yang dipanggil lewat call_group dengan definisi
# `func <nama>(` di proyek, jadi no-op senyap langsung ketahuan.

def check_callgroup():
    """Setiap metode call_group harus punya definisi `func` di suatu .gd."""
    calls, defs = set(), set()
    for dirpath, _dirs, files in os.walk(os.path.join(ROOT, "godot")):
        for name in files:
            if not name.endswith(".gd"):
                continue
            src = _read(os.path.join(dirpath, name))
            for m in re.finditer(r'call_group\(\s*"[^"]*"\s*,\s*"([^"]+)"',
                                 src):
                calls.add(m.group(1))
            for m in re.finditer(r'^\s*func\s+([A-Za-z_]\w*)\s*\(',
                                 src, re.M):
                defs.add(m.group(1))
    missing = sorted(c for c in calls if c not in defs)
    lines = ["%d metode call_group diperiksa" % len(calls)]
    for name in missing[:20]:
        lines.append('  call_group(..., "%s") — TIDAK ada `func %s(` di '
                     "proyek mana pun -> no-op senyap" % (name, name))
    return not missing, lines


# ══════════════════════════════════════════════════════════════════
#  8. SMOKE — panggil renderer pygame, tangkap exception
# ══════════════════════════════════════════════════════════════════

SMOKE_SRC = r'''
import os, sys, traceback
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
sys.path.insert(0, %(root)r)
import pygame
pygame.init(); pygame.display.set_mode((1, 1))
import _core  # noqa
import random

class Stub:
    def __init__(self, **kw): self.__dict__.update(kw)
    def __getattr__(self, n): return 0

out = {"minion": [], "tower": [], "hero": []}

# ── minion ──
from minions import MINION_RENDERERS
for mtype, fn in sorted(MINION_RENDERERS.items()):
    for team in ("blue", "red"):
        for moving in (False, True):
            m = Stub(minion_type=mtype, team=team, walk_cycle=1.0,
                     is_moving=moving, anim_time=10,
                     attack_anim_timer=0, attack_anim_max=1,
                     hp=1, max_hp=1, alive=True, facing=1, x=0, y=0,
                     radius=9, slash_effects=[])
            surf = pygame.Surface((160, 160), pygame.SRCALPHA)
            try:
                random.seed(20260907)
                fn(surf, m, 80, 130)
            except Exception as e:
                out["minion"].append("%%s/%%s/moving=%%s: %%s: %%s"
                                     %% (mtype, team, moving,
                                         type(e).__name__, e))

# ── tower ──
from towers import render_tower
for ttype in ("archer", "cannon", "ice", "mage"):
    for team in ("blue", "red"):
        for lvl in range(1, 7):
            t = Stub(tower_type=ttype, team=team, level=lvl,
                     shoot_flash_timer=0, target=None, x=0, y=0,
                     timer=0, radius=18 + lvl, shield=0, shield_max=0,
                     alive=True, hp=1, max_hp=1, angle=0, selected=False,
                     attack_cooldown=35)
            surf = pygame.Surface((220, 220), pygame.SRCALPHA)
            try:
                random.seed(20260907)
                render_tower(ttype, surf, t, 110, 110, 18 + lvl)
            except Exception as e:
                out["tower"].append("%%s/%%s/L%%d: %%s: %%s"
                                    %% (ttype, team, lvl,
                                        type(e).__name__, e))

# ── hero/boss (sampel) ──
from heroes import HERO_RENDERERS, BOSS_RENDERERS
from bosses.boss_data import MINI_BOSS_TYPES, TRUE_BOSS_TYPES
stats = {}; stats.update(MINI_BOSS_TYPES); stats.update(TRUE_BOSS_TYPES)
types = sorted(set(HERO_RENDERERS) | set(BOSS_RENDERERS))
pick = %(pick)s
for t in pick:
    renderer = HERO_RENDERERS.get(t) or BOSS_RENDERERS.get(t)
    from heroes import _ProbeEntity, _adapt_hero_to_boss
    p = _ProbeEntity(t, 256, 256)
    s = stats.get(t) or {}
    if s:
        p.radius = int(s.get("radius", p.radius))
        p.range = int(s.get("range", p.range))
    p.boss_class = str(s.get("boss_class", "mini"))
    p.facing = 1; p.direction = 1
    _adapt_hero_to_boss(p)
    p.pulse = 1.0; p.timer = 0; p.attack_timer = 0
    p.active_skill = None; p.active_skill_timer = 0
    from heroes import _call_renderer_on_canvas
    surf = pygame.Surface((512, 512), pygame.SRCALPHA)
    try:
        random.seed(20260907)
        _call_renderer_on_canvas(renderer, surf, p, 256, 256)
    except Exception as e:
        out["hero"].append("%%s: %%s: %%s" %% (t, type(e).__name__, e))

import json
print("@@JSON@@" + json.dumps(out))
'''


def check_smoke(sample_hero=40):
    import json as _json
    # Sampel merata supaya cepat; bake penuh menutup sisanya lewat
    # laporan [convert] GAGAL.
    src = SMOKE_SRC % {
        "root": ROOT,
        "pick": "__import__('random').sample(types, min(%d, len(types)))" % sample_hero,
    }
    fd, path = tempfile.mkstemp(suffix=".py")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(src)
        res = _run("python3 %s" % path, timeout=900)
        marker = [l for l in res.stdout.splitlines() if l.startswith("@@JSON@@")]
        if not marker:
            return False, ["smoke test gagal jalan: %s"
                           % (res.stderr or res.stdout)[-400:]]
        out = _json.loads(marker[0][len("@@JSON@@"):])
    finally:
        os.unlink(path)
    lines, bad = [], False
    for key, label in (("minion", "minion"), ("tower", "tower"),
                       ("hero", "hero/boss")):
        errs = out.get(key, [])
        if errs:
            bad = True
            lines.append("%s: %d RUSAK" % (label, len(errs)))
            for e in errs[:8]:
                lines.append("   %s" % e)
        else:
            lines.append("%s: bersih" % label)
    return not bad, lines


# ══════════════════════════════════════════════════════════════════
#  7. HARDCODE — warna literal di .gd yang sudah punya nama di UiTheme
# ══════════════════════════════════════════════════════════════════

def check_hardcode():
    theme = _read(os.path.join(GODOT, "scripts", "utils", "UiTheme.gd"))
    named = set()
    for m in re.finditer(r'Color\("(#[0-9a-fA-F]{6})"\)', theme):
        named.add(m.group(1).lower())
    # Warna yang dipakai tema map/world boleh hardcode (per tema).
    offenders = {}
    total = 0
    for path in _gd_files():
        if path.endswith(("UiTheme.gd",)) or "/tests/" in path:
            continue
        if "ArenaMap" in path or "MenuBackground" in path:
            continue  # palet prosedural, bukan warna design system
        src = _read(path)
        hits = [h.lower() for h in re.findall(r'Color\("(#[0-9a-fA-F]{6})"\)', src)]
        known = [h for h in hits if h in named]
        if known:
            offenders[os.path.relpath(path, ROOT)] = len(known)
            total += len(known)
    lines = ["%d pemakaian warna UiTheme yang ditulis ulang sebagai literal "
             "di .gd" % total]
    for k, v in sorted(offenders.items(), key=lambda kv: -kv[1])[:10]:
        lines.append("   %-52s %d" % (k, v))
    if total:
        lines.append("(ini bukan salah, tapi titik drift: ubah UiTheme.gd "
                     "tidak menjangkau berkas ini)")
    return True, lines, True   # warn_only


# ══════════════════════════════════════════════════════════════════
#  main
# ══════════════════════════════════════════════════════════════════

ALL = ["palette", "encoder", "fresh-unit", "fresh-map", "fresh-prop",
       "geometry", "callgroup", "coverage", "smoke", "hardcode"]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--full", action="store_true",
                    help="re-bake SEMUA unit (222) dan map (54), bukan sampel")
    ap.add_argument("--section", default=",".join(ALL),
                    help="daftar seksi dipisah koma: " + ", ".join(ALL))
    ap.add_argument("--report", choices=["md"],
                    help="tulis juga laporan markdown ke docs/PARITY_AUDIT.md")
    args = ap.parse_args()
    want = set(s.strip() for s in args.section.split(",") if s.strip())

    rep = Report()
    rep.env = _env_lines()

    checks = [
        ("palette", "PALET", lambda: check_palette()),
        ("encoder", "ENCODER", lambda: check_encoder()),
        ("fresh-unit", "FRESH-UNIT",
         lambda: check_fresh_units(full=args.full)),
        ("fresh-map", "FRESH-MAP", lambda: check_fresh_maps(full=args.full)),
        ("fresh-prop", "FRESH-PROP",
         lambda: check_fresh_props(full=args.full)),
        ("geometry", "GEOMETRI", lambda: check_geometry()),
        ("callgroup", "CALLGROUP", lambda: check_callgroup()),
        ("coverage", "COVERAGE", lambda: check_coverage()),
        ("smoke", "SMOKE", lambda: check_smoke()),
        ("hardcode", "HARDCODE", lambda: check_hardcode()),
    ]
    for key, name, fn in checks:
        if key not in want:
            continue
        try:
            rep.add(name, *fn())
        except Exception as exc:
            # Satu seksi yang error tidak boleh menggagalkan audit tanpa
            # alasan: laporan (yang diunggah sebagai artefak) harus selalu
            # memuat penyebabnya, kalau tidak CI hanya bilang "exit code 1".
            import traceback
            tb = traceback.format_exc().strip().splitlines()[-3:]
            rep.add(name, False,
                    ["CRASH %s: %s" % (type(exc).__name__, exc)]
                    + ["   " + l.strip() for l in tb])

    print(rep.text())

    if args.report == "md":
        docs = os.path.join(ROOT, "docs")
        os.makedirs(docs, exist_ok=True)
        p = os.path.join(docs, "PARITY_AUDIT.md")
        block = (BEGIN + "\n"
                 "## Hasil audit terakhir (otomatis)\n\n"
                 "Dihasilkan `tools/visual_parity_audit.py` "
                 "(`--full` = %s).\n\n```\n%s\n```\n"
                 % ("ya" if args.full else "tidak", rep.text())
                 + END)
        old = _read(p) if os.path.exists(p) else ""
        if BEGIN in old and END in old:
            # Ganti HANYA blok otomatis — laporan kurasi (analisis, tabel,
            # keputusan) yang ditulis manusia harus tetap utuh. Dulu berkas
            # ini ditimpa seluruhnya, jadi setiap kali CI jalan, semua
            # narasinya hilang.
            pre, rest = old.split(BEGIN, 1)
            _dropped, post = rest.split(END, 1)
            out = pre + block + post
        else:
            out = old.rstrip() + "\n\n---\n\n" + block + "\n"
        with open(p, "w", encoding="utf-8") as f:
            f.write(out)
        print("\nLaporan ditulis: %s" % p)

    return 1 if rep.failed else 0


if __name__ == "__main__":
    sys.exit(main())
