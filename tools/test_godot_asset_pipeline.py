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
     (kecuali bullet_hit yang memang dokumentasi — lihat ALLOWED_MISSING_AUDIO);
  7. kontainer audio: nama ".wav" di assets/sounds/ TIDAK selalu RIFF — pygame
     memutar apa saja lewat SDL_mixer, Godot memilih importer dari EKSTENSI.
     7 Ogg Vorbis + 1 MP3 di repo ini harus disalin converter dengan ekstensi
     yang benar (.ogg/.mp3), kalau tidak importer WAV menolaknya dan 8 SFX
     (ui_click, ui_buy, ui_sell, ui_upgrade, ui_error, victory, minion_hit,
     ambient_forest) senyap di AAB.
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

## Nama di AudioManager.SFX_NAMES yang memang tidak punya berkas audio:
## 'bullet_hit' didaftarkan sebagai dokumentasi port (proyektil pygame tidak
## pernah memuatnya — _scan_sounds() memuat apa pun yang ada di folder), jadi
## ketiadaannya bukan regresi aset.
ALLOWED_MISSING_AUDIO = {"bullet_hit"}

## Jumlah berkas audio yang dimuat SoundManager.load_all (_system.py:543-574)
## + combat_audio mobile — dipakai laporan, bukan angka mati yang dikunci.
EXPECTED_AUDIO_MIN = 24

## Kontainer -> ekstensi yang importer Godot 4.3 kenal: AudioStreamWAV,
## AudioStreamOggVorbis, AudioStreamMP3. Kunci _streams AudioManager adalah
## nama tanpa ekstensi, jadi kontainer mana pun tetap terpanggil sama.
AUDIO_EXT = {"wav": ".wav", "ogg": ".ogg", "mp3": ".mp3"}
## Berkas non-audio yang ikut disalin converter (atribusi aset).
AUDIO_SIDE_FILES = {".txt"}

ICON_COUNT = 33


def _read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError("berkas tidak ada: %s" % path.relative_to(ROOT))
    return path.read_text(encoding="utf-8")


def _audio_container(path: Path) -> str:
    """Kontainer asli berkas audio dari magic bytes (bukan dari namanya).

    Cermin audio_container_ext() di tools/convert_to_godot.py — kalau keduanya
    beda, salinan Godot akan di-import dengan importer yang salah.
    """
    with path.open("rb") as fh:
        head = fh.read(64)
    if head[:4] == b"RIFF" and head[8:12] == b"WAVE":
        return "wav"
    if head[:4] == b"OggS":
        # Ogg bisa Vorbis (didukung Godot 4.3) atau Opus/Speex/FLAC (tidak).
        return "ogg" if b"\x01vorbis" in head else "ogg-unsupported"
    if head[:3] == b"ID3":
        size = ((head[6] & 0x7F) << 21 | (head[7] & 0x7F) << 14
                | (head[8] & 0x7F) << 7 | (head[9] & 0x7F))
        with path.open("rb") as fh:
            fh.seek(10 + size)
            nxt = fh.read(2)
        if len(nxt) == 2 and nxt[0] == 0xFF and nxt[1] & 0xE0 == 0xE0:
            return "mp3"
        return "unknown"
    if len(head) >= 2 and head[0] == 0xFF and head[1] & 0xE0 == 0xE0:
        return "mp3"
    return "unknown"


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
    src_dir = ASSETS / "sounds"
    if not src_dir.is_dir():
        raise AssertionError("assets/sounds/ tidak ada — sumber audio hilang")

    # stem -> (kontainer, ekstensi di nama berkas)
    sources = {}
    for path in sorted(src_dir.iterdir()):
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        if ext in AUDIO_EXT.values():
            sources[path.stem] = (_audio_container(path), ext)
        elif ext not in AUDIO_SIDE_FILES:
            raise AssertionError("assets/sounds/%s ekstensinya %s — bukan "
                                 "audio yang dikenal Godot (%s) dan bukan "
                                 "berkas pendamping (%s)"
                                 % (path.name, ext,
                                    "/".join(AUDIO_EXT.values()),
                                    "/".join(sorted(AUDIO_SIDE_FILES))))
    if len(sources) < EXPECTED_AUDIO_MIN:
        raise AssertionError("assets/sounds/ cuma %d berkas audio (diharapkan "
                             ">= %d — SoundManager.load_all + combat_audio)"
                             % (len(sources), EXPECTED_AUDIO_MIN))

    # 7a. Kontainernya harus yang importer Godot 4.3 dukung.
    bad = sorted("%s=%s" % (s, c) for s, (c, _) in sources.items()
                 if c not in AUDIO_EXT)
    if bad:
        raise AssertionError("kontainer audio tidak didukung Godot 4.3: %s — "
                             "konversi ke WAV/Ogg Vorbis/MP3" % ", ".join(bad))

    # 7b. Nama ".wav" yang isinya bukan RIFF harus diluruskan converter.
    misnamed = sorted(s for s, (c, e) in sources.items() if AUDIO_EXT[c] != e)
    conv = _read(CONVERTER)
    for needle in ("def audio_container_ext(", 'b"RIFF"', 'b"OggS"', 'b"ID3"',
                   'b"\\x01vorbis"', "AUDIO_EXTS"):
        if needle not in conv:
            raise AssertionError("convert_to_godot.py kehilangan %s — 8 berkas "
                                 "audio yang namanya .wav tapi isinya Ogg/MP3 "
                                 "akan gagal import di Godot" % needle)
    audio = _read(AUDIO_MANAGER_GD)
    m = re.search(r"^const AUDIO_EXTS: Array = \[([^\]]+)\]", audio, re.M)
    if not m:
        raise AssertionError("AudioManager.gd kehilangan const AUDIO_EXTS")
    listed = set(re.findall(r'"(\.[a-z0-9]+)"', m.group(1)))
    if listed != set(AUDIO_EXT.values()):
        raise AssertionError("AudioManager.AUDIO_EXTS %s != %s (ekstensi yang "
                             "bisa dihasilkan converter)"
                             % (sorted(listed), sorted(AUDIO_EXT.values())))
    if "get_extension()" not in audio:
        raise AssertionError("AudioManager._scan_sounds() harus menyaring "
                             "lewat get_extension() supaya .ogg/.mp3 ikut "
                             "termuat, bukan cuma .wav")

    # 6. Daftar SFX vs berkas yang benar-benar ada (per stem, bukan per .wav).
    block = re.search(r"const SFX_NAMES: Array = \[(.*?)\n\]", audio, re.S)
    if not block:
        raise AssertionError("AudioManager.gd kehilangan const SFX_NAMES")
    names = set(re.findall(r'"([a-z_0-9]+)"', block.group(1)))
    if not names:
        raise AssertionError("SFX_NAMES kosong — pola baca daftar gagal")
    missing = sorted(n for n in names - set(sources) if n not in ALLOWED_MISSING_AUDIO)
    if missing:
        raise AssertionError("AudioManager menyebut SFX tanpa berkas di "
                             "assets/sounds/: %s — tambah berkasnya atau hapus "
                             "namanya dari SFX_NAMES" % ", ".join(missing))
    unused = sorted(set(sources) - names - {"bgm_battle", "ambient_forest"})
    per_container = {}
    for _, (c, _) in sources.items():
        per_container[c] = per_container.get(c, 0) + 1
    print("[aset] suara: %d berkas audio di assets/sounds/ (%s) · %d nama SFX "
          "terdaftar · di luar daftar: %s"
          % (len(sources),
             " + ".join("%d %s" % (per_container[c], c)
                        for c in sorted(per_container)),
             len(names), ", ".join(unused) or "-"))
    if misnamed:
        print("[aset] suara: %d nama .wav yang kontainernya bukan RIFF "
              "(converter meluruskannya jadi %s): %s"
              % (len(misnamed),
                 ", ".join(sorted({AUDIO_EXT[sources[s][0]] for s in misnamed})),
                 ", ".join(misnamed)))

    # 7c. Salinan di godot/assets/sounds/ (kalau ada) harus satu per stem,
    # ekstensinya == kontainer, dan tidak ada sisa salinan basi.
    dst = GODOT_ASSETS / "sounds"
    if dst.is_dir():
        copies = {}
        for path in sorted(dst.iterdir()):
            if not path.is_file() or path.suffix.lower() not in AUDIO_EXT.values():
                continue
            copies.setdefault(path.stem, []).append(path.suffix.lower())
        if set(copies) != set(sources):
            raise AssertionError("godot/assets/sounds/ tidak cocok dengan "
                                 "assets/sounds/: kurang %s · lebih %s — "
                                 "jalankan ulang converter --assets"
                                 % (sorted(set(sources) - set(copies)) or "-",
                                    sorted(set(copies) - set(sources)) or "-"))
        dupes = sorted(s for s, e in copies.items() if len(e) > 1)
        if dupes:
            raise AssertionError("salinan audio dobel (sisa ekstensi lama akan "
                                 "tetap di-import Godot dan error lagi): %s"
                                 % ", ".join(dupes))
        wrong = sorted("%s%s (harusnya %s)"
                       % (s, copies[s][0], AUDIO_EXT[sources[s][0]])
                       for s in copies if copies[s][0] != AUDIO_EXT[sources[s][0]])
        if wrong:
            raise AssertionError("ekstensi salinan != kontainernya: %s — "
                                 "jalankan ulang converter --assets"
                                 % ", ".join(wrong))
        per_ext = {}
        for exts in copies.values():
            per_ext[exts[0]] = per_ext.get(exts[0], 0) + 1
        print("[aset] godot/assets/sounds/: %d berkas tersalin (%s)"
              % (len(copies),
                 " + ".join("%d %s" % (per_ext[e], e) for e in sorted(per_ext))))


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
