# Audit Paritas Visual pygame ↔ Godot

Audit ulang dari nol pada **2026-09-10**, tanpa membaca dokumen lama.
Semua angka di bawah diukur ulang di sesi ini (re-bake nyata, bukan klaim).

Cara mengulang audit ini:

```bash
python3 -m pip install pygame-ce pillow
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 tools/visual_parity_audit.py --full
```

Keluar dengan kode `1` kalau ada FAIL, jadi bisa langsung dipasang di CI
(sudah: langkah **Audit paritas visual** di `.github/workflows/godot-check.yml`).

---

## Ringkasan

| # | Temuan | Dampak tampilan | Status |
|---|--------|-----------------|--------|
| 1 | Menara, minion, nexus **tidak pernah di-port** — Godot menggambar placeholder geometris | **Sangat besar** | ✅ Diperbaiki (bake Fase 7) |
| 2 | Bake **tidak deterministik**: hasilnya berubah tergantung ada/tidaknya Pillow | **Besar** | ✅ Diperbaiki |
| 3 | Tidak ada penjaga keusangan bake (yang ada hanya cek jumlah berkas) | Menengah | ✅ Diperbaiki |
| 4 | Strip 222 hero/boss & 54 map ternyata **tidak usang** | — | ✅ Terverifikasi |
| 5 | Palet warna `ui_theme.py` ↔ `UiTheme.gd` | — | ✅ 32/32 identik |
| 6 | 2 renderer pygame rusak di jalur skill (`sasori/e`, `vex/q`) | Kecil | ⚠️ Dilaporkan, belum diperbaiki |

**Jadi: tampilan beda bukan karena bake hero/boss usang, dan bukan karena
palet warna.** Dua penyebab utamanya adalah #1 dan #2.

---

## 1. Menara, minion, nexus belum pernah di-port (penyebab terbesar)

Fase 5 dulu hanya membake **hero + boss**. Menara, minion, dan nexus tidak
pernah menyusul, sehingga Godot menggambarnya dari primitif geometris:

| Komponen | Godot (sebelumnya) | pygame (sumber kebenaran) |
|---|---|---|
| Menara | `Tower.gd::_draw()` — **21** panggilan `draw_*` (segitiga + lingkaran) | `towers/_bundle.py` — **7.274 baris** (4 jenis × 6 level: bata, obor, perisai, paku keling, kilat moncong) |
| Minion | `UnitSilhouette.gd::_draw()` — **56** panggilan `draw_*` (bola/elips) | `minions/_bundle.py` — **9.531 baris** (5 rig lengkap + animasi jalan/serang) |
| Nexus | `Nexus.gd::_draw()` — **19** panggilan `draw_*` | `_entity.py` `class Castle` — **1.637 baris** (5 level kastil, gerbang, menara, obor, aura) |

Dalam satu match ada **puluhan minion dan belasan menara** sekaligus — jadi
inilah yang paling terasa sebagai "tampilannya beda".

### Perbaikan: bake Fase 7

Pola yang sama dengan Fase 5: renderer pygame **asli** yang dibake menjadi
strip PNG + manifest. Tidak ada seni yang ditulis ulang di GDScript, jadi
tidak mungkin melenceng.

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 tools/convert_to_godot.py --props-png
```

Hasil (deterministik, terverifikasi dengan bake ulang byte-per-byte):

* `godot/assets/props/minion_<jenis>_<tim>.png` — 10 strip × 24 frame
  (8 idle · 8 jalan · 8 serang)
* `godot/assets/props/tower_<jenis>_<tim>.png` — 8 strip × 36 frame
  (6 level × [4 fase nyala obor + 2 pose tembak])
* `godot/assets/props/nexus_<tim>.png` — 2 strip × 5 frame (level 1–5)
* `godot/data/baked_props.json` — manifest (ukuran sel, titik jangkar, fps)

Total **298 KB** untuk 538 frame.

Sumbu animasi diambil dari kode pygame, bukan ditebak:

| Sumbu | Sumber |
|---|---|
| idle minion | `body_bob = sin(anim_time * 0.06)` → periode 104,72 frame (`minions/_bundle.py:616`) |
| jalan minion | `sin(walk_cycle * 1.5)`, `walk_cycle += 0,25/frame` (`_entity.py:5603`) |
| serang minion | `attack_progress = 1 − timer/attack_anim_max`, maks 24 (`_entity.py:5482`) |
| nyala obor menara | kunci cache `tower.timer % 4` (`_entity.py:1351`) |
| pose tembak menara | `shoot_flash_timer` 8 → 4 (`_entity.py:1351`) |
| ukuran menara | `size = 18 + level` (`_entity.py:1345`) |
| level kastil | kanvas 180×160 di titik (90, 140) lalu skala 0,85 (`_entity.py:1872-1874`) |

### Perubahan kode Godot

* **Baru** `godot/scripts/render/BakedPropDB.gd` — pembaca manifest (pola
  yang sama dengan `BakedUnitDB.gd`).
* `Tower.gd` — `_draw()` dipecah: `_draw_baked_body()` → `_draw_geometric_body()`
  (cadangan) → `_draw_overlays()` (pip level, gelembung shield, bar HP,
  ring seleksi — semua ini digambar pygame di *luar* `render_tower()`,
  jadi tidak ikut bake).
* `Minion.gd` — sprite bake di bawah `$Visual`, digerakkan `_drive_visual()`;
  pose serang **dipaksa dari progress** seperti `BakedSprite.gd` (bukan playback).
  Flash luka (`HurtFlash`) kini menargetkan sprite bake.
* `Nexus.gd` — badan kastil dari bake; halaman batu, shield, bar HP, pip
  level tetap digambar Godot.

**Jaring pengaman:** kalau manifest/tekstur tidak ada, ketiga file jatuh
kembali ke gambar geometris lama. Perilaku pra-Fase 7 tetap utuh.

---

## 2. Bake tidak deterministik (penyebab kedua)

`_save_strip()` dan `_save_map_png()` punya cabang `except ImportError`:

* **dengan Pillow** → PNG palet 256 warna (mode `P`)
* **tanpa Pillow** → `pygame.image.save()` RGBA penuh (mode `RGB`)

Dua mesin yang berbeda menghasilkan aset yang **berbeda total**.

Bukti terukur pada `drakar.png` (kanvas sama, 1520×495):

| Kondisi | Ukuran | Mode PNG |
|---|---|---|
| bake dengan Pillow | 21.195 byte | `P` (256 warna) |
| bake tanpa Pillow | 86.201 byte | `RGBA` |
| selisih piksel | **63,2 % piksel beda**, selisih kanal maks 30, alpha rata-rata 4,19 | |

Lebih parah lagi, repo ini berisi **campuran kedua jenis hasil bake**:

* 445 strip unit → mode `P` (dibake **dengan** Pillow)
* 54 tekstur map → mode `RGB` (dibake **tanpa** Pillow)

Jadi setiap re-bake di mesin lain mengubah ratusan berkas sekaligus — dan
itulah sebabnya perbedaan harus diperiksa satu-satu secara manual.

### Perbaikan

* `_save_strip()` — Pillow sekarang **wajib**. Kalau tidak ada, bake gagal
  dengan pesan jelas (bukan diam-diam pakai encoder lain). Strip tetap
  palet 256 warna → 445 berkas yang sudah ada **tidak berubah**.
* `_save_map_png()` — map **selalu** RGB penuh via `pygame.image.save`
  (tanpa kuantisasi). 54 map cuma ~3 MB total, jadi tidak ada alasan
  mengorbankan gradasi kabut/speckle demi ukuran berkas.
* Hasil: bake ulang **222 unit + 54 map + 20 props menghasilkan berkas yang
  identik byte-per-byte** dengan yang sudah ter-commit (`git status` bersih).

---

## 3. Penjaga keusangan bake (baru)

Dulu `tools/godot_pygame_sync.py` hanya menghitung berkas:

```python
if len(units) < 222: issues.append(...)
if unit_count < 222: issues.append(...)
```

Jumlah 222 **bukan** bukti isinya mutakhir. Dan CI tidak pernah menjalankan
bake sama sekali.

Sekarang:

* **`tools/visual_parity_audit.py`** (baru) — 8 seksi otomatis:

  | Seksi | Yang diperiksa |
  |---|---|
  | `PALET` | konstanta warna `ui_theme.py` vs `UiTheme.gd` |
  | `ENCODER` | bake deterministik (tidak ada fallback bergantung Pillow) |
  | `FRESH-UNIT` | re-bake 222 strip, bandingkan byte |
  | `FRESH-MAP` | re-bake 54 map, bandingkan byte |
  | `FRESH-PROP` | re-bake 20 strip props, bandingkan byte |
  | `COVERAGE` | tiap subsistem punya jalur setia atau masih placeholder |
  | `SMOKE` | semua renderer minion + menara + sampel hero/boss dipanggil |
  | `HARDCODE` | warna `UiTheme` yang ditulis ulang sebagai literal di `.gd` |

  Tanpa `--full` hanya mengambil sampel (~30 detik); `--full` re-bake
  semuanya (~4 menit).

* **CI** — langkah baru di `godot-check.yml` menjalankan
  `visual_parity_audit.py --full --report md` dan mengunggah laporannya.
* **`godot_pygame_sync.py`** — `check_baked_assets()` kini juga memeriksa
  props dan memanggil audit untuk membandingkan byte hasil bake ulang.

---

## 4. Yang ternyata TIDAK bermasalah

Perlu dicatat supaya tidak dicari lagi:

* **Strip 222 hero/boss tidak usang.** Re-bake penuh menghasilkan berkas
  identik byte-per-byte dengan yang ter-commit.
* **54 tekstur map tidak usang** (setelah encoder dibuat deterministik).
* **Palet warna identik** — 32 dari 32 konstanta `ui_theme.py` sama dengan
  `UiTheme.gd`. Tidak ada satu pun warna yang melenceng.

---

## 5. Yang belum beres (perlu keputusan)

1. **Dua renderer pygame rusak di jalur skill** — dilaporkan bake:
   * `sasori/e` → `NameError: name 'random' is not defined`
     (`bosses/level54.py:3278` — modul tidak mengimpor `random`)
   * `vex/q` → `IndexError: list index out of range`
     (`heroes/_bundle.py:13231-13238` — loop 6 di atas list 6 elemen)
   * `ursath/w` → pose statis, ter-drop gerbang

   Di pygame keduanya jatuh ke `_draw_generic_hero` (exception ditangkap
   `_hero_render_sprite`). Di Godot jatuh ke pose attack. **Efeknya sama-sama
   "hero generik", jadi tampilannya justru sudah searah** — tapi perbaikannya
   harus di sisi pygame (dan itu mengubah bake 222 unit).

2. **Efek hidup kastil dibekukan** — obor level 4+ dan aura level 6 dibake
   pada `timer = 0`. Butuh pass efek dinamis terpisah kalau ingin menyala.

3. **Bar HP minion tidak ikut bake** — sengaja, karena pygame menggambarnya
   *live* di luar cache sprite. Godot menggambar bar HP-nya sendiri.

4. **`KillFeed` & `PathPreview`** pygame belum ditemukan padanannya di Godot
   (pemindaian nama; belum diverifikasi apakah memang belum ada atau hanya
   beda nama).

5. **HUD/menu tidak diaudit piksel demi piksel** di sini — sudah dikunci
   `UiHudParityTest.gd` + `godot/tests/fixtures/match_parity.json`.

6. **Satu warna `UiTheme` ditulis ulang sebagai literal** di
   `godot/scenes/ui/TopupDialog.gd` — bukan salah, tapi kalau `UiTheme.gd`
   diubah, berkas ini tidak akan mengikuti.
