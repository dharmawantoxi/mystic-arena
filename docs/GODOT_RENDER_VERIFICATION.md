# Verifikasi migrasi `_render.py` → Godot

Tanggal: 2026-11-01 · Branch: `arena/390edcf5-mystic-arena` · Proyek: `godot_rebuild/`

## Hasil lokal

| Pemeriksaan | Hasil |
|---|---|
| `tools/prepare_godot_main.py --check` | PASS — 54 level, 32 aset |
| `tools/prepare_godot_core.py --check` | PASS — sha256 `068cbd7215bc` (54 level, 222 hero, 216 boss, 33 item) |
| `tools/prepare_godot_entities.py --check` | PASS — sha256 `9cba05ebd821` (222 unit strip, 10 minion, 8 tower, 2 nexus) |
| `tools/prepare_godot_render.py --check` | PASS — sha256 `77d01b73d863`, 54 tema, 54 PNG 1280×720 |
| `tools/test_godot_core_prepare.py` | 4 passed |
| `tools/test_godot_main_prepare.py` | 2 passed |
| `tools/test_godot_entity_prepare.py` | 3 passed |
| `tools/test_godot_render_prepare.py` | 5 passed (budget/timing AST, easing oracle, konstanta GDScript, cakupan map, SHA PNG) |
| `tools/test_cloud_save.py` | 18 lulus, 0 gagal |
| `godot_rebuild/tests/validate_project.py` | **PASS: 167 checks** |
| `gdparse` (semua 51 `.gd`, termasuk generated) | PASS |
| `gdlint` (49 non-generated) | PASS |
| `gdformat --check` (49 non-generated) | PASS |
| Runtime suite headless | **PASS: 248 checks, 0 failures** |
| Boot main scene headless `--quit-after 180` | rc 0, `[GODOT] Mystic Arena | state=splash`, tanpa `ERROR:` |
| `git diff --check` | PASS |

Suite mencakup `_test_render()` baru: easing 1:1, cache font/tekstur, 54 tema,
bake forest, hit-test toko, lane path, budget 32 damage number / 500 partikel /
80 ledakan, decay shake, combo/wave/path/achievement expiry, kill feed disabled,
setting damage number & screen shake, level intro blocking + skip, boss intro
100 frame, boss death 90 frame + selebrasi 120 frame, `CoreGame` intro pause,
klik toko membuka item forge, Escape menutup.

## Cara menjalankan

```bash
# Python (venv dengan gdtoolkit, pygame-ce, Pillow, numpy, PyYAML, scons)
python3 tools/prepare_godot_render.py --check
python3 tools/test_godot_render_prepare.py
python3 godot_rebuild/tests/validate_project.py

# Godot resmi (CI): import lalu suite
godot --headless --path godot_rebuild --editor --import
godot --headless --path godot_rebuild --script res://tests/run_all.gd
godot --headless --path godot_rebuild --quit-after 180
```

### Runner lokal sandbox

Binary Godot resmi tidak dapat diunduh di sandbox; dipakai build headless
kustom `4.7.2.stable.custom_build` dari source resmi tag `4.7.2-stable`:

```bash
scons platform=linuxbsd target=template_debug production=no use_lto=no \
  disable_3d=yes vulkan=no x11=no wayland=no alsa=no pulseaudio=no \
  dbus=no fontconfig=no udev=no speechd=no -j2
# elapsed 00:19:33
cp bin/godot.linuxbsd.template_debug.x86_64 godot_rebuild/godot-test
```

Build ini menolak `--path`/`--script` (`disable_path_overrides=yes`). Runner
lokal memakai `override.cfg` sementara + class cache tulisan tangan:

```ini
# godot_rebuild/override.cfg (ignored by Git; hapus sebelum boot main scene)
[application]
run/main_loop_type="MysticTestRunner"
```

`.godot/global_script_class_cache.cfg` harus menyertakan `is_abstract` dan
`is_tool` pada tiap entri; tanpa keduanya Godot 4.7 mengabaikan kelas global dan
MainLoop tidak ditemukan. Jalankan dari `godot_rebuild/`: `./godot-test --headless`.
CI memakai binary resmi dan `--editor --import` seperti biasa.

## Bake map

```bash
python3 tools/prepare_godot_render.py --bake
# 54 tema, total ±3033 KB PNG; seed beku MAP_BAKE_SEED
# map_bakes.json kini membawa river_points/torch_stones/radiant_shop/dire_shop
```

`export_map_bakes()` di `convert_to_godot.py` menelan exception (exit 0);
`prepare_godot_render.py` fail-closed: jumlah tema, dimensi PNG, anchor dinamis,
cakupan `map_theme` semua level, dan SHA-256 harus cocok sebelum kontrak ditulis.

## Catatan / batasan verifikasi

- `WARNING: 4 ObjectDB instances were leaked at exit` sudah ada sebelum migrasi
  render (cosmetic, tidak memengaruhi hasil suite).
- Boot menyebut 1 stream audio opsional belum tersedia; output audio nyata belum
  diverifikasi. Tidak ada klaim parity audio cinematic.
- Headless memverifikasi state/API/budget, bukan piksel GPU. Visual perangkat
  Android, keystore/signing, Play Games, dan top-up produksi tetap di luar cakupan.
- Kill feed sengaja disabled mengikuti `_core.draw_ui`; combo visual aktif.
- Bake statis memakai seed beku; speckle/jitter Pygame yang diacak tiap match
  tidak direproduksi persis.
