#!/usr/bin/env python3
"""Gerbang statis migrasi aset pygame -> project Godot.

    python3 tools/test_godot_asset_pipeline.py

TIDAK butuh pygame dan TIDAK butuh Godot — semuanya dibaca dari berkas, jadi
cek ini jalan di langkah "Linter statis" godot-check.yml sebelum engine
diunduh (hitungan milidetik).

Kenapa perlu: aset biner Godot adalah SALINAN yang di-gitignore
(`godot/assets/sounds/`, `godot/assets/items/`, `godot/assets/presplash.png`)
— sumber kebenarannya `assets/` pygame. Rantainya panjang dan setiap mata
rantai bisa putus dalam diam:

    assets/items/*.png  --convert_to_godot.py --assets-->  godot/assets/items/
                      --.gitignore (tidak ikut repo)-->    CI menyalin ulang
                      --ItemIcons.gd (res://assets/items/)--> Button.icon

Putus di mana pun, gejalanya baru kelihatan saat dimainkan: game sunyi, ikon
item jadi badge warna, atau boot splash bawaan Godot. Yang dikunci di sini:

  1. closed-world ikon item: 33 entri items.json <-> 33 PNG assets/items/
     (item baru tanpa ikon, atau ikon yatim, gagal di sini);
  2. converter punya export_sounds/export_items_png/export_presplash dan mode
     `--assets` yang TIDAK menuntut numpy/pygame (dipanggil CI sebelum Godot);
  3. .gitignore menutup ketiga salinan (±19 MB tidak boleh masuk git 2x);
  4. kedua workflow Godot menyalin aset SEBELUM engine dijalankan/di-export
     (exporter hanya memaksa presplash.png ikut AAB kalau berkasnya ada —
     EditorExportPlatform::get_forced_export_files);
  5. project.godot memakai presplash sebagai boot splash + berkas sumbernya
     ada, dan ItemIcons.gd menunjuk folder yang sama dengan tujuan converter
     serta memeriksa ResourceLoader.exists() sebelum load() (load ke path
     yang hilang mencetak error yang menggagalkan godot_log_gate);
  6. daftar SFX AudioManager tidak menyebut suara yang berkasnya tidak ada
     (kecuali bullet_hit yang memang dokumentasi — lihat ALLOWED_MISSING_WAV).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ASSETS = ROOT / "assets"
GODOT = ROOT / "godot"
GODOT_ASSETS = GODOT / "assets"
CONVERTER = ROOT / "tools/convert_to_godot.py"
GITIGNORE = ROOT / ".gitignore"
PROJECT_GODOT = GODOT / "project.godot"
ITEM_ICONS_GD = GODOT / "scripts/utils/ItemIcons.gd"
AUDIO_MANAGER_GD = GODOT / "scripts/autoload/AudioManager.gd"
WORKFLOW_CHECK = ROOT / ".github/workflows/godot-check.yml"
WORKFLOW_ANDROID = ROOT / ".github/workflows/build-android-godot.yml"

## Path res:// yang dibaca script Godot — harus sama dengan tujuan salinan
## converter (godot/assets/<folder> -> res://assets/<folder>).
ITEM_ICONS_RES = "res://assets/items/"
SOUND_RES = "res://assets/sounds/"
PRESPLASH_RES = "res://assets/presplash.png"

## Salinan yang di-gitignore: folder/berkas -> sumber di assets/ pygame.
DUPLICATES = {
    "godot/assets/sounds/": "assets/sounds/",
    "godot/assets/items/": "assets/items/",
    "godot/assets/presplash.png": "assets/presplash.png",
}

## Nama di AudioManager.SFX_NAMES yang memang tidak punya berkas .wav:
## 'bullet_hit' didaftarkan sebagai dokumentasi port (proyektil pygame tidak
## pernah memuatnya — _scan_sounds() memuat apa pun yang ada di folder), jadi
## ketiadaannya bukan regresi aset.
ALLOWED_MISSING_WAV = {"bullet_hit"}

## Jumlah .wav yang dimuat SoundManager.load_all (_system.py:543-574) +
## combat_audio mobile — dipakai laporan, bukan angka mati yang dikunci.
EXPECTED_WAV_MIN = 24

ICON_COUNT = 33


def _read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError("berkas tidak ada: %s" % path.relative_to(ROOT))
    return path.read_text(encoding="utf-8")


# ══════════════════════════════════════════════════════════
#  1. Ikon item: items.json <-> assets/items/
# ══════════════════════════════════════════════════════════

def check_item_icons() -> None:
    items = json.loads(_read(GODOT / "data/items.json"))
    if not isinstance(items, dict):
        raise AssertionError("items.json harus object id -> data item")
    if len(items) != ICON_COUNT:
        raise AssertionError("items.json %d item, diharapkan %d (regenerasi: "
                             "python3 tools/convert_to_godot.py)"
                             % (len(items), ICON_COUNT))

    icons = {}
    for item_id, data in items.items():
        icon = str(data.get("icon", ""))
        if not icon.endswith(".png"):
            raise AssertionError("item %s: field icon harus .png (dapat %r)"
                                 % (item_id, icon))
        icons[item_id] = icon
        if not (ASSETS / "items" / icon).is_file():
            raise AssertionError("item %s: assets/items/%s tidak ada — ikon "
                                 "wajib ikut repo pygame (sumber kebenaran "
                                 "ItemIcons.gd)" % (item_id, icon))

    on_disk = {p.name for p in (ASSETS / "items").glob("*.png")}
    orphans = sorted(on_disk - set(icons.values()))
    if orphans:
        raise AssertionError("ikon yatim di assets/items/ (tidak dirujuk "
                             "items.json): %s — hapus atau daftarkan di "
                             "hero_items.ITEM_CATALOG lalu regenerasi"
                             % ", ".join(orphans))

    # Konvensi (bukan hukum): nama ikon == id item. Dilaporkan supaya
    # penyimpangan sadar, bukan karena salah ketik di hero_items.py.
    off_convention = sorted(i for i in icons if icons[i] != "%s.png" % i)
    convention = "%d/%d mengikuti konvensi <id>.png" % (
        len(icons) - len(off_convention), len(icons))
    if off_convention:
        convention += " (penyimpangan: %s)" % ", ".join(off_convention)

    # Kalau salinan Godot sudah dibuat (habis menjalankan converter), isinya
    # harus lengkap — kalau belum ada, itu normal (folder di-gitignore).
    dst = GODOT_ASSETS / "items"
    if dst.is_dir():
        copied = {p.name for p in dst.glob("*.png")}
        missing = sorted(set(icons.values()) - copied)
        if missing:
            raise AssertionError("godot/assets/items/ tidak lengkap (%d "
                                 "hilang: %s) — jalankan ulang python3 "
                                 "tools/convert_to_godot.py --assets"
                                 % (len(missing), ", ".join(missing[:6])))
        status = "salinan Godot lengkap (%d PNG)" % len(copied)
    else:
        status = "salinan Godot belum dibuat (converter belum dijalankan)"

    print("[aset] ikon item: %d entri items.json == %d PNG assets/items/ · %s"
          % (len(icons), len(on_disk), convention))
    print("[aset] godot/assets/items/: %s" % status)


# ══════════════════════════════════════════════════════════
#  2. Converter: fungsi salin + mode --assets tanpa numpy
# ══════════════════════════════════════════════════════════

def check_converter() -> None:
    src = _read(CONVERTER)
    for fn in ("def export_sounds(", "def export_items_png(",
               "def export_presplash(", "def export_bin_assets("):
        if fn not in src:
            raise AssertionError("tools/convert_to_godot.py kehilangan %s"
                                 % fn.rstrip("("))
    # Mode --assets harus bercabang SEBELUM _require_numpy(): CI memanggilnya
    # tepat setelah checkout, tanpa venv/pygame/numpy. Dicari sebagai
    # PERNYATAAN di awal baris (bukan teks bebas) supaya komentar yang
    # menyebut namanya tidak ikut terhitung.
    assets_at = src.find('if "--assets" in _argv')
    numpy_call = re.search(r"^\s*_require_numpy\(\)\s*$", src, re.M)
    if assets_at < 0:
        raise AssertionError('convert_to_godot.py tidak punya mode "--assets"')
    if numpy_call is None or assets_at > numpy_call.start():
        raise AssertionError('mode "--assets" harus diputus SEBELUM '
                             "_require_numpy() supaya bisa jalan tanpa numpy")
    # Jalur default (tanpa flag) juga harus menyalin aset biner.
    default_tail = src[src.rfind('if __name__ == "__main__":'):]
    for call in ("export_sounds()", "export_items_png()", "export_presplash()"):
        if call not in default_tail:
            raise AssertionError("converter tanpa flag harus memanggil %s "
                                 "(sekarang cuma mode --assets yang menyalin)"
                                 % call)
    # Tujuan salinan harus sama dengan yang dibaca ItemIcons.gd/AudioManager.
    for pair in (('os.path.join(ROOT, "godot", "assets", "items")',
                  "godot/assets/items"),
                 ('os.path.join(ROOT, "godot", "assets", "sounds")',
                  "godot/assets/sounds")):
        if pair[0] not in src:
            raise AssertionError("converter tidak menulis ke %s" % pair[1])
    print("[aset] converter: export_sounds/items_png/presplash + mode "
          "--assets (tanpa numpy/pygame) OK")


# ══════════════════════════════════════════════════════════
#  3. .gitignore menutup salinan
# ══════════════════════════════════════════════════════════

def check_gitignore() -> None:
    ignore = _read(GITIGNORE)
    aktif = {line.strip() for line in ignore.splitlines()
             if line.strip() and not line.strip().startswith("#")}
    for dup in DUPLICATES:
        if dup not in aktif:
            raise AssertionError(".gitignore harus menutup %s (duplikat %s — "
                                 "sumber kebenaran tetap di assets/ pygame)"
                                 % (dup, DUPLICATES[dup]))
    print("[aset] .gitignore: %d salinan aset biner tidak ikut repo"
          % len(DUPLICATES))


# ══════════════════════════════════════════════════════════
#  4. CI menyalin sebelum engine jalan
# ══════════════════════════════════════════════════════════

def check_ci() -> None:
    check = _read(WORKFLOW_CHECK)
    copy_cmd = "tools/convert_to_godot.py --assets"
    if copy_cmd not in check:
        raise AssertionError("godot-check.yml tidak menyalin aset biner "
                             "(%s) — ikon item teruji sebagai badge fallback "
                             "dan boot splash mencetak error ke log" % copy_cmd)
    if check.find(copy_cmd) > check.find("--import"):
        raise AssertionError("godot-check.yml: penyalinan aset harus SEBELUM "
                             "langkah `godot --headless --import`")

    android = _read(WORKFLOW_ANDROID)
    if copy_cmd not in android:
        raise AssertionError("build-android-godot.yml tidak menyalin aset "
                             "biner — AAB sunyi, ikon item fallback, dan "
                             "presplash tidak ikut PCK")
    if android.find(copy_cmd) > android.find("Import project"):
        raise AssertionError("build-android-godot.yml: penyalinan aset harus "
                             "SEBELUM import/export (exporter hanya memaksa "
                             "presplash.png ikut PCK kalau berkasnya ada)")
    print("[aset] CI: godot-check + build-android-godot menyalin aset "
          "sebelum engine dijalankan")


# ══════════════════════════════════════════════════════════
#  5. Sisi Godot: boot splash + folder ikon
# ══════════════════════════════════════════════════════════

def check_godot_side() -> None:
    project = _read(PROJECT_GODOT)
    m = re.search(r'^boot_splash/image="([^"]+)"', project, re.M)
    if not m:
        raise AssertionError("project.godot kehilangan boot_splash/image "
                             "(padanan presplash buildozer.spec:79)")
    splash_res = m.group(1)
    if splash_res != PRESPLASH_RES:
        raise AssertionError("boot_splash/image %s != %s (tujuan salinan "
                             "export_presplash di converter)"
                             % (splash_res, PRESPLASH_RES))
    if not (ASSETS / "presplash.png").is_file():
        raise AssertionError("assets/presplash.png hilang — converter tidak "
                             "punya sumber untuk disalin")
    # Salinannya di-gitignore: kalau sudah ada (habis converter dijalankan)
    # harus berkas, bukan folder.
    splash_fs = GODOT_ASSETS / "presplash.png"
    if splash_fs.exists() and not splash_fs.is_file():
        raise AssertionError("godot/assets/presplash.png bukan berkas")
    # Warna latar splash harus tetap sama dengan presplash_color buildozer.
    if "boot_splash/bg_color=Color(0.0431373, 0.0392157, 0.0705882, 1)" not in project:
        raise AssertionError("boot_splash/bg_color berubah — buildozer.spec:78 "
                             "memakai android.presplash_color #0B0A12")

    icons = _read(ITEM_ICONS_GD)
    if "class_name ItemIcons" not in icons:
        raise AssertionError("ItemIcons.gd kehilangan class_name ItemIcons")
    icon_dir = re.search(r'^const ITEMS_DIR := "([^"]+)"', icons, re.M)
    if not icon_dir:
        raise AssertionError("ItemIcons.gd kehilangan const ITEMS_DIR")
    if icon_dir.group(1) != ITEM_ICONS_RES:
        raise AssertionError("ItemIcons.ITEMS_DIR %s != tujuan converter %s"
                             % (icon_dir.group(1), ITEM_ICONS_RES))
    if "ResourceLoader.exists(" not in icons:
        raise AssertionError("ItemIcons.gd harus memeriksa ResourceLoader."
                             "exists() sebelum load() — load ke path hilang "
                             "mencetak 'Error opening file' dan menggagalkan "
                             "godot_log_gate di CI")

    audio = _read(AUDIO_MANAGER_GD)
    sound_dir = re.search(r'^const SOUNDS_DIR := "([^"]+)"', audio, re.M)
    if not sound_dir or sound_dir.group(1) != SOUND_RES:
        raise AssertionError("AudioManager.SOUNDS_DIR harus %s" % SOUND_RES)
    print("[aset] Godot: boot_splash/image=%s · ItemIcons.ITEMS_DIR=%s · "
          "AudioManager.SOUNDS_DIR=%s"
          % (splash_res, icon_dir.group(1), sound_dir.group(1)))


# ══════════════════════════════════════════════════════════
#  6. Suara: daftar SFX vs berkas yang benar-benar ada
# ══════════════════════════════════════════════════════════

def check_sounds() -> None:
    wavs = {p.stem for p in (ASSETS / "sounds").glob("*.wav")}
    if len(wavs) < EXPECTED_WAV_MIN:
        raise AssertionError("assets/sounds/ cuma %d .wav (diharapkan >= %d — "
                             "SoundManager.load_all + combat_audio)"
                             % (len(wavs), EXPECTED_WAV_MIN))

    audio = _read(AUDIO_MANAGER_GD)
    block = re.search(r"const SFX_NAMES: Array = \[(.*?)\n\]", audio, re.S)
    if not block:
        raise AssertionError("AudioManager.gd kehilangan const SFX_NAMES")
    names = set(re.findall(r'"([a-z_0-9]+)"', block.group(1)))
    if not names:
        raise AssertionError("SFX_NAMES kosong — pola baca daftar gagal")
    missing = sorted(n for n in names - wavs if n not in ALLOWED_MISSING_WAV)
    if missing:
        raise AssertionError("AudioManager menyebut SFX tanpa berkas .wav di "
                             "assets/sounds/: %s — tambah berkasnya atau "
                             "hapus namanya dari SFX_NAMES" % ", ".join(missing))
    unused = sorted(wavs - names - {"bgm_battle", "ambient_forest"})
    print("[aset] suara: %d .wav di assets/sounds/ · %d nama SFX terdaftar · "
          "di luar daftar: %s"
          % (len(wavs), len(names), ", ".join(unused) or "-"))

    dst = GODOT_ASSETS / "sounds"
    if dst.is_dir():
        copied = len(list(dst.glob("*.wav")))
        if copied != len(wavs):
            raise AssertionError("godot/assets/sounds/ punya %d .wav, sumbernya "
                                 "%d — jalankan ulang converter --assets"
                                 % (copied, len(wavs)))
        print("[aset] godot/assets/sounds/: %d .wav tersalin" % copied)


def main() -> int:
    check_item_icons()
    check_converter()
    check_gitignore()
    check_ci()
    check_godot_side()
    check_sounds()
    print("Asset pipeline Godot: OK")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as exc:
        print("FAIL: %s" % exc)
        sys.exit(1)
