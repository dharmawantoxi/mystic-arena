# Migrasi `lighting.py` ke Godot

`lighting.py` (239 baris) adalah **pass pencahayaan per-sprite** milik renderer prosedural Pygame: dari mask alpha sprite ia menurunkan gradien arah (nilai RGB dikali `GRAD_DARK..GRAD_LIGHT` + sheen), rim light di kontur yang menghadap cahaya (RGB di-ADD `RIM_ADD`), dan terminator dua band di kontur bayangan (RGB di-MULT `SHADE_MUL`, band kedua `BAND2_RATIO`). Semua diturunkan dari mask, jadi bebas bentuk — dipakai boss (`bosses/level*.py` lewat `apply_to_rig`) dan jalur hero `_finish_hd_sprite`.

Port awal (layer **9aq**) hanya membawa **matematika mask** + **adapter vektor** ke `scripts/ui/sprite_lighting.gd`, karena `godot_rebuild` menggambar vektor/baked art. Layer **9cl** menutup sisanya: seluruh 21 simbol diklasifikasikan eksplisit dan **pipeline bitmap** (`_sized`, `contour_masks`, `apply`, `_bbox_of`, `apply_to_rig`, `reset_gradient_cache`) kini ikut diport dan diuji piksel-per-piksel.

Sumber kebenaran: `godot_rebuild/tests/sprite_lighting_source_oracle.py`. Oracle menjalankan **fungsi asli** `lighting.py` di bawah shim pygame yang kini punya `Mask.to_surface`, `Surface.blit` dengan blend SDL (`BLEND_RGB_MULT` = `d*s/255`, `BLEND_RGB_ADD` = `min(255, d+s)`), `subsurface`, dan `smoothscale`. Fixture: `tests/fixtures/sprite_lighting_source.json`. Suite native: `tests/sprite_lighting_checks.gd` (blok 9aq + 9cl).

## 1. Ringkasan

| Ukuran | Nilai |
| --- | --- |
| Baris `lighting.py` | 239 |
| Kelas | 0 (modul fungsional) |
| Fungsi | 8 |
| Konstanta modul | 12 |
| Impor | 1 (`pygame`) |
| Simbol terklasifikasi | **21** (8 fungsi + 12 konstanta + impor) |
| Grid gradien kanonik | 28×28 (784 sel) |
| Kasus piksel `apply` | 6 (400 + 64 + 1296 + 12 + 0 + 20 piksel) |

| Kind | Jumlah | Arti |
| --- | --- | --- |
| `ported` | 9 | 8 fungsi + `_SIZE_CACHE` punya padanan native |
| `data` | 10 | 10 konstanta tunable diport verbatim |
| `folded` | 1 | impor `pygame` (tidak ada API piksel yang perlu diikat) |
| `deviation` | 1 | `_CANON_CACHE` tidak diport (D1) |

## 2. Klasifikasi simbol

| Simbol | Kind | Target native |
| --- | --- | --- |
| `LIGHT_DIR` | data | `const LIGHT_DIR := Vector2i(-1, -1)` |
| `RIM_ADD` | data | `const RIM_ADD := Vector3i(30, 26, 44)` |
| `SHADE_MUL` | data | `const SHADE_MUL := 168` |
| `BAND2_RATIO` | data | `const BAND2_RATIO := 0.42` |
| `MASK_ALPHA` | data | `const MASK_ALPHA := 170` |
| `GRADIENT_ENABLED` | data | `const GRADIENT_ENABLED := true` |
| `GRAD_DARK` / `GRAD_LIGHT` / `GRAD_SHEEN` | data | tiga `const` gradien |
| `_GRAD_STEPS` | data | `const GRAD_STEPS := 28` |
| `_SIZE_CACHE` | ported | `static var _size_cache` + `SIZE_CACHE_LIMIT` 64 |
| `_CANON_CACHE` | deviation | — (D1) |
| `_shifted_mask` | ported | `rim_shade_cells` (geseran = selisih himpunan) |
| `_canonical` | ported | `canonical_table` (`gradient_t`/`gradient_mul`/`gradient_add`) |
| `_sized` | ported | `sized_grid` (+ `_axis`) |
| `reset_gradient_cache` | ported | `reset_gradient_cache` |
| `contour_masks` | ported | `contour_masks` (+ `mask_cells`, `MIN_SIZE`, `MIN_SOLID`) |
| `apply` | ported | `apply` |
| `_bbox_of` | ported | `bbox_of` |
| `apply_to_rig` | ported | `apply_to_rig` |
| `import pygame` | folded | header port (`## Port of "lighting.py"`) |

Adapter vektor dari 9aq tetap menjadi jalur produksi: `gradient_t`, `lit_color`, `rim_color`, `shade_color`, `band2_mul`, `classify_edges`, `inward_normal`, `vertex_colors`, `circle_points`, `should_light` — dipakai `scenes/prototype/prototype_view.gd::_draw_lit_polygon` untuk siluet hero dan badan boss.

## 3. Pipeline bitmap yang diport di layer ini

| Fungsi | Perilaku sumber yang dipertahankan |
| --- | --- |
| `mask_cells` | `pygame.mask.from_surface(surface, alpha)`: alpha **di atas** ambang masuk mask |
| `contour_masks` | guard `w <= 2`/`h <= 2`, guard `< 24` sel, rim = sel tanpa tetangga `-s`, shade = sel tanpa tetangga `+s`, band2 = shade(width 2) − shade(width 1) |
| `bbox_of` | bbox gabungan `get_bounding_rects`; `Rect2i()` kosong bila tak ada piksel solid |
| `sized_grid` | grid kanonik 28×28 di-resample ke ukuran kotak (identitas di 28×28), cache ≤ 64 ukuran |
| `apply` | urutan sumber: gradien (MULT lalu ADD) → terminator band1 (`168`) → band2 (`218`) → rim ADD; hanya RGB, alpha tidak disentuh |
| `apply_to_rig` | `enabled=false` = no-op; selain itu panggil `apply` |
| `reset_gradient_cache` | kosongkan cache kotak |

Hasil piksel `apply` diverifikasi **exact** untuk 6 kasus fixture (400 + 64 + 1296 + 12 + 0 + 20 piksel, tanpa toleransi), termasuk kasus `box`: sprite 40×40 yang hanya dipanggang gradien di kotak acuan 28×28 (piksel di luar kotak tetap warna dasar). Argumen `box` sumber berupa tuple `(x, y, w, h)`; API native memakai `Rect2i` dengan urutan yang sama.

## 4. Deviasi terdokumentasi

| Kode | Hal | Deviasi | Alasan |
| --- | --- | --- | --- |
| D1 | `_CANON_CACHE` | tidak diport; grid kanonik dibangun ulang tiap `sized_grid` miss | 784 sel, jauh lebih murah daripada menyimpan state global; hasilnya identik |
| D2 | `_sized` | sampler bilinear native (identitas di 28×28) menggantikan `pygame.transform.smoothscale` | filter pygame tidak tersedia di GDScript; kasus 28×28 (satu-satunya yang dipakai fixture) identik, ukuran lain bisa beda ≤ 1 LSB |
| D3 | `apply` | tidak punya pemanggil produksi: rebuild menggambar vektor (adapter) dan art boss/hero sudah baked `.webp` | pass bitmap tetap diport + diuji agar berkas 100% termigrasi dan siap dipakai jalur raster |
| D4 | `_bbox_of`, `reset_gradient_cache` | **tidak pernah dipanggil** oleh sumber sendiri | tetap diport supaya API modul utuh; tidak ada perilaku pemain yang bergantung padanya |
| D5 | `apply_to_rig` | tidak menangkap `pygame.error`/`ValueError` (GDScript tidak melempar itu); guard ukuran/`< 24` sel yang menggantikan | kebijakan "jangan gagalkan render" tetap: gambar kembali apa adanya |
| D6 | blend | aritmetika blend SDL ditiru di buffer RGBA8: `d*s/255` (truncating) dan `min(255, d+s)` | menjaga hasil piksel identik dengan `BLEND_RGB_MULT`/`BLEND_RGB_ADD` |

## 5. Cara menjalankan

```bash
python3 godot_rebuild/tests/sprite_lighting_source_oracle.py --write   # tulis fixture
python3 godot_rebuild/tests/sprite_lighting_source_oracle.py --check   # cek sinkron sumber
python3 godot_rebuild/tests/validate_project.py                        # blok 9aq + 9cl
godot --headless --script tests/run_all.gd                             # suite native (PC/CI)
```

`tests/sprite_lighting_checks.gd` memverifikasi konstanta, grid kanonik 28×28, himpunan rim/shade/band2 untuk 3 bentuk, adapter vektor, ditambah (9cl) inventaris 239 baris/8 fungsi/12 konstanta/21 simbol, klasifikasi + token hidup, bbox 3 bentuk + sprite kosong, identitas resample 28×28, sampler kotak 12×12, `reset_gradient_cache`, `apply_to_rig` on/off, dan piksel `apply` untuk semua 5 kasus.

## 6. Status paritas

Terbukti: matematika mask, grid gradien, dan **seluruh output piksel `apply`** identik dengan sumber pada kasus yang tidak melibatkan filter resample pygame; klasifikasi 21 simbol lengkap dengan token hidup. Belum terbukti: tampilan akhir di layar (komposisi dengan art baked) dan perilaku di perangkat Android — keduanya butuh run Godot + screenshot seed/state sama, sesuai kriteria paritas proyek. Validator statis dan fixture **bukan** bukti paritas visual.
