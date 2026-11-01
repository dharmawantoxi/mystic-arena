# Verifikasi migrasi `hero_archetypes.py` → Godot

Tanggal: 2026-11-01 · Branch: `arena/d6307f36-mystic-arena` · Proyek: `godot_rebuild/`

## Hasil lokal

| Pemeriksaan | Hasil |
|---|---|
| `tools/prepare_godot_main.py --check` | PASS — 54 level, 32 aset |
| `tools/prepare_godot_core.py --check` | PASS — sha256 `068cbd7215bc` |
| `tools/prepare_godot_archetypes.py --check` | PASS — 222 hero, 216 boss; sha256 `19d0e08bb74c` |
| `tools/prepare_godot_entities.py --check` | PASS — sha256 `9cba05ebd821` |
| `tools/prepare_godot_render.py --check` | PASS — sha256 `77d01b73d863`, 54 tema |
| `tools/prepare_godot_system.py --check` | PASS — sha256 `a6b5508c7681`, 17 suara, 3 slot |
| `tools/test_godot_core_prepare.py` | 4 passed |
| `tools/test_godot_main_prepare.py` | 2 passed |
| `tools/test_godot_entity_prepare.py` | 3 passed |
| `tools/test_godot_archetypes_prepare.py` | 7 passed |
| `tools/test_godot_render_prepare.py` | 5 passed |
| `tools/test_godot_system_prepare.py` | 5 passed |
| `tools/test_cloud_save.py` | 18 lulus, 0 gagal |
| `godot_rebuild/tests/validate_project.py` | **PASS: 216 checks** |
| `gdparse` (56 `.gd`, termasuk generated) | PASS |
| `gdlint` + `gdformat --check` (54 non-generated) | PASS |
| Runtime suite headless | **PASS: 832 checks, 0 failures** |
| Boot main scene headless `--quit-after 180` | rc 0, `[GODOT] Mystic Arena | state=splash`, tanpa `ERROR:` |
| `git diff --check` | PASS |

`_test_archetypes()` baru membandingkan runtime GDScript dengan oracle Python
untuk seluruh 222 hero dan 216 boss, 27 kasus override manual hero, 5 fallback/
presedensi tabel boss, 22 kasus profil/clamp/pembulatan half-to-even, 7 kasus setup
boss, dan 12 titik kurva mitigasi. Tes juga mengunci wiring `BattleUnit`,
`EntityCombat`, pemisahan atribut item berbasis role, label toko, serta fail-closed
`CoreData` bila kontrak arketipe hilang. `_test_app()` tambahan memastikan toko
hero benar-benar membuat 222 label sekolah/tier/power dan tooltip snapshot.

## Cara menjalankan

```bash
python3 tools/prepare_godot_archetypes.py --check
python3 tools/test_godot_archetypes_prepare.py
python3 godot_rebuild/tests/validate_project.py

# Godot resmi (CI)
godot --headless --path godot_rebuild --editor --import
godot --headless --path godot_rebuild --script res://tests/run_all.gd
godot --headless --path godot_rebuild --quit-after 180
```

### Runner lokal sandbox

Build headless kustom `4.7.2.stable.custom_build` dari source resmi tag
`4.7.2-stable` (elapsed **00:24:24.98**):

```bash
scons platform=linuxbsd target=template_debug production=no use_lto=no \
  disable_3d=yes vulkan=no x11=no wayland=no alsa=no pulseaudio=no \
  dbus=no fontconfig=no udev=no speechd=no accesskit=no -j2
cp bin/godot.linuxbsd.template_debug.x86_64 godot_rebuild/godot-test
```

Runner lokal memakai `override.cfg` sementara (`run/main_loop_type="MysticTestRunner"`)
dan `.godot/global_script_class_cache.cfg` tulisan tangan berisi 53 kelas dengan
`is_abstract`/`is_tool`. Hapus `override.cfg` sebelum boot main scene. CI memakai
binary resmi + `--editor --import`.

## Catatan / batasan verifikasi

- `WARNING: 4 ObjectDB instances were leaked at exit` saat suite/boot sudah ada
  sebelum migrasi ini (cosmetic). Tidak ada `SCRIPT ERROR:` atau `ERROR:`.
- Boot menyebut 1 stream audio opsional belum tersedia; output audio nyata belum
  diverifikasi. Tes audio memverifikasi state/throttle/gating, bukan suara.
- Headless memverifikasi state/API/paritas data, bukan piksel GPU atau perangkat
  Android. Label toko diuji sebagai node/teks, bukan screenshot visual.
- Tier/power tetap snapshot analyzer; tidak ada reklasifikasi atau rebalance.
- Atribut item `magic_only` tetap berbasis role seperti `hero_items.py`, terpisah
  dari sekolah damage hasil analisis. Keyword role native yang sudah ada tidak
  diperluas dalam migrasi ini.
- Rounding tiap tahap, blind/true-strike, resilience, dan cap per-hit boss secara
  keseluruhan tetap milik pipeline `_entity.py`/boss; migrasi ini memverifikasi
  nilai sekolah/armor/MR, urutan shred armor boss, cap reduksi 0.60, dan cap MR
  0.45 yang dipakai pipeline tersebut.
- Play Games, top-up produksi, keystore/signing, dan perangkat nyata tetap di luar
  cakupan. Tidak ada klaim layanan tersebut aktif tanpa konfigurasi/plugin.
