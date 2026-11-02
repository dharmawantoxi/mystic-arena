# Verifikasi migrasi `localization.py` → Godot

Dokumen ini mencatat cara memeriksa port lokalisasi dan hasil gate lokal.
Paritas string diuji terhadap `localization.py` asli; tidak membutuhkan pygame.

## Perintah

```bash
# Oracle / kontrak
python3 tools/prepare_godot_localization.py --check
python3 tools/test_godot_localization_prepare.py
python3 tools/test_godot_localization_parity.py
python3 tools/test_localization.py

# Validator proyek native
python3 godot_rebuild/tests/validate_project.py

# Suite Godot headless (dari godot_rebuild/, setelah prepare assets)
./godot-test --headless

# Boot singkat tanpa override test runner
rm -f override.cfg
./godot-test --headless --quit-after 5

# Regresi terkait
python3 tools/test_cloud_save.py
python3 tools/test_hero_lighting.py
python3 tools/test_lighting_parity.py

# GDScript static gates
gdparse $(find godot_rebuild -name '*.gd')
gdlint $(find godot_rebuild -name '*.gd' -not -path '*/entities/generated/*')
gdformat --check $(find godot_rebuild -name '*.gd' -not -path '*/entities/generated/*')
```

## Hasil lokal

| Gate | Hasil |
|---|---|
| `prepare_godot_localization.py --check` | PASS, sha `b3f6ede52b8a…` |
| `test_godot_localization_prepare.py` | 6 tes OK |
| `test_godot_localization_parity.py` | PASS, 224 kunci × 2 bahasa |
| `test_localization.py` | PASS |
| `validate_project.py` | 318 checks PASS |
| Suite native `run_all.gd` | 3673 checks, 0 failures |
| Cakupan lokalisasi | 448 tr, 22 missing-args, 5 language switch, 4 label fallback, 4 edge, format subset, CoreData delegation, fail-closed loader |
| Boot headless singkat | rc 0 (1 stream audio opsional belum tersedia) |
| Cloud-save | 18 tes OK |
| Lighting regression | `test_hero_lighting.py` dan `test_lighting_parity.py` PASS |
| gdformat/gdlint/gdparse | 63 file unchanged, lint/parse bersih |

Catatan lingkungan: build engine headless kustom lokal melaporkan 4 ObjectDB
instances leaked pada exit. Warning yang sama muncul pada baseline sebelum
perubahan lokalisasi (setelah aset audio disiapkan), jadi tidak diperkenalkan
oleh PR ini. Gate CI memakai runtime Godot resmi.

## Yang diverifikasi fixture

- Semua 224 kunci dalam `id` dan `en` dengan args contoh deterministik.
- Placeholder hilang mengembalikan template utuh, bukan hasil partial.
- Nilai ekstra diabaikan; kunci tidak dikenal mengembalikan kunci.
- Bahasa invalid/kosong/kapital salah aman kembali ke `id`.
- Label bahasa kosong memakai bahasa aktif; label tidak dikenal fallback label
  Indonesia.
- `CoreData.text()` mendelegasikan ke `Localization.tr_for()` dan fallback
  bahasa invalid ke Indonesia.
- Kontrak hilang/rusak gagal closed (`valid()` false, `load_error` terisi).

## Batas verifikasi

- Belum semua literal UI lama dipanggil melalui `CoreData.text()`; adopsi kunci
  per layar dapat dilakukan bertahap tanpa mengubah tabel sumber.
- Tidak ada terjemahan bahasa baru atau perubahan teks sumber.
- Belum ada pengukuran perangkat nyata/Android build untuk pilihan bahasa.
- Layanan nyata (cloud, top-up/voucher, Play Games) tidak disentuh dan tidak
  diklaim berhasil dari gate ini.
