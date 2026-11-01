# Verifikasi migrasi `_system.py` → Godot

Tanggal: 2026-11-01 · Branch: `arena/9de8111f-mystic-arena` · Proyek: `godot_rebuild/`

## Hasil lokal

| Pemeriksaan | Hasil |
|---|---|
| `tools/prepare_godot_main.py --check` | PASS — 54 level, 32 aset |
| `tools/prepare_godot_core.py --check` | PASS — sha256 `068cbd7215bc` |
| `tools/prepare_godot_entities.py --check` | PASS — sha256 `9cba05ebd821` |
| `tools/prepare_godot_render.py --check` | PASS — sha256 `77d01b73d863`, 54 tema |
| `tools/prepare_godot_system.py --check` | PASS — sha256 `a6b5508c7681`, 17 suara, 3 slot |
| `tools/test_godot_core_prepare.py` | 4 passed |
| `tools/test_godot_main_prepare.py` | 2 passed |
| `tools/test_godot_entity_prepare.py` | 3 passed |
| `tools/test_godot_render_prepare.py` | 5 passed |
| `tools/test_godot_system_prepare.py` | 5 passed (kontrak AST, konstanta GDScript, manifest audio, save, urutan bucket) |
| `tools/test_cloud_save.py` | 18 lulus, 0 gagal |
| `godot_rebuild/tests/validate_project.py` | **PASS: 184 checks** |
| `gdparse` (55 `.gd`, termasuk generated) | PASS |
| `gdlint` + `gdformat --check` (53 non-generated) | PASS |
| Runtime suite headless | **PASS: 300 checks, 0 failures** |
| Boot main scene headless `--quit-after 180` | rc 0, `[GODOT] Mystic Arena | state=splash`, tanpa `ERROR:` |
| `git diff --check` | PASS |

`_test_system()` baru mencakup: batas frustum inklusif/eksklusif, SpatialGrid
filter team + keanggotaan + bucket jauh + clear, FpsCounter history/refresh/
avg/min/max/status, AdaptiveQuality ambang high/medium/low, AudioDirector
current_bgm/pause/resume/master volume clamp/positional range + throttle/
stop BGM/ambient, SaveRepository format playtime/time/last-played, migrasi
legacy progress.json → slot 1 + backup + idempotent, all_slot_info, dan wiring
grid MatchModel.

## Cara menjalankan

```bash
python3 tools/prepare_godot_system.py --check
python3 tools/test_godot_system_prepare.py
python3 godot_rebuild/tests/validate_project.py

# Godot resmi (CI)
godot --headless --path godot_rebuild --editor --import
godot --headless --path godot_rebuild --script res://tests/run_all.gd
godot --headless --path godot_rebuild --quit-after 180
```

### Runner lokal sandbox

Build headless kustom `4.7.2.stable.custom_build` dari source resmi tag
`4.7.2-stable` (elapsed **00:23:40**):

```bash
scons platform=linuxbsd target=template_debug production=no use_lto=no \
  disable_3d=yes vulkan=no x11=no wayland=no alsa=no pulseaudio=no \
  dbus=no fontconfig=no udev=no speechd=no -j2
cp bin/godot.linuxbsd.template_debug.x86_64 godot_rebuild/godot-test
```

Runner lokal memakai `override.cfg` sementara (`run/main_loop_type="MysticTestRunner"`)
dan `.godot/global_script_class_cache.cfg` tulisan tangan yang menyertakan
`is_abstract`/`is_tool`. Hapus `override.cfg` sebelum boot main scene. CI memakai
binary resmi + `--editor --import`.

## Catatan / batasan verifikasi

- `WARNING: 4 ObjectDB instances were leaked at exit` saat boot sudah ada sebelum
  migrasi ini (cosmetic). Suite runtime tidak melaporkan `ERROR:`.
- Boot menyebut 1 stream audio opsional belum tersedia; output audio nyata belum
  diverifikasi. Tes audio memverifikasi state/throttle/gating, bukan suara.
- Headless memverifikasi state/API/budget, bukan piksel GPU atau perangkat Android.
- Adaptive quality default mati (`auto_quality=false`); spatial grid dipakai untuk
  target menara, sedangkan target hero/minion masih `enemies_of()` demi stabilitas.
- Play Games, top-up produksi, keystore/signing, dan perangkat nyata tetap di luar
  cakupan.
