# Verifikasi migrasi `lighting.py` → Godot

Dokumen ini mencatat cara memeriksa port lighting dan hasil gate lokal.
Paritas pixel diuji terhadap `pygame==2.6.1` backend smoothscale `GENERIC`.

## Perintah

```bash
# Oracle / kontrak (butuh pygame 2.6.1)
python3 tools/prepare_godot_lighting.py --check
python3 tools/test_godot_lighting_prepare.py
python3 tools/test_lighting_parity.py
python3 tools/test_hero_lighting.py

# Validator proyek native
python3 godot_rebuild/tests/validate_project.py

# Suite Godot headless (dari godot_rebuild/, setelah prepare assets)
./godot-test --headless

# Boot singkat tanpa override test runner
rm -f override.cfg
./godot-test --headless --quit-after 5

# Python/cloud regression lain
python3 tools/test_cloud_save.py

# GDScript static gates
gdparse $(find godot_rebuild -name '*.gd')
gdlint $(find godot_rebuild -name '*.gd' -not -path '*/entities/generated/*')
gdformat --check $(find godot_rebuild -name '*.gd' -not -path '*/entities/generated/*')
```

## Hasil lokal

| Gate | Hasil |
|---|---|
| `prepare_godot_lighting.py --check` | PASS, kontrak sha `8aee00fb0869…` |
| `test_godot_lighting_prepare.py` | 6 tes OK |
| `validate_project.py` | 295 checks PASS |
| Suite native `run_all.gd` | 3173 checks, 0 failures |
| Cakupan lighting | 8 contour/bbox, 40 gradient, 19 apply pixel, cache, runtime opt-in, fail-closed loader |
| `test_lighting_parity.py` | lulus dengan pygame 2.6.1 |
| `test_hero_lighting.py` | lulus (regresi sumber: satu pass per lane, cache, kill-switch) |
| Cloud-save | 18 tes OK |
| Boot headless singkat | rc 0 (1 stream audio opsional belum tersedia) |
| gdformat/gdlint/gdparse | 61 file unchanged, lint/parse bersih |

Catatan lingkungan: build engine headless kustom lokal melaporkan 4 ObjectDB
instances leaked pada exit. Warning yang sama muncul pada baseline pre-lighting
setelah aset audio disiapkan, jadi tidak diperkenalkan oleh perubahan lighting.
Gate CI memakai runtime Godot resmi; jangan mengklaim bersih leak lokal jika
warning itu masih ada.

## Yang diverifikasi fixture

- Threshold alpha 170/171, sprite kecil/sparse, pulau terpisah, translucent,
  dan RGB pada piksel transparan.
- Gradient canonical dan hasil smoothscale untuk ukuran kecil, non-kelipatan,
  dan besar; hash RGB exact serta sampel pertama/terakhir.
- Urutan blend: gradient MULT→ADD, terminator, rim ADD; alpha tetap.
- Opsi custom rim/shade hero/boss, `gradient=false`, `two_band=false`, box
  clamped, box invalid, dan wrapper disabled.
- Perilaku partial-error rim color invalid (gradient/terminator tetap terjadi,
  rim dilewati) sesuai `apply_to_rig` pygame.
- Cache ukuran bounded dan reset; jalur `EntityVisuals` tidak memproses ulang
  strip baked, menghormati quality low, dan memakai ulang tekstur lit.

## Batas verifikasi

- Belum ada pengukuran GPU visual, FPS perangkat nyata, atau Android build.
- Tidak ada rebake sprite; aset baked yang sudah ada tidak diubah.
- Layanan nyata (top-up/voucher, Play Games, cloud produksi) tidak disentuh dan
  tidak diklaim berhasil dari gate ini.
