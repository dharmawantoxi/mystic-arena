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

4. **`PathPreview` belum ada di Godot — SUDAH DITUTUP (FASE 26, 11 September
   2026).** Pygame menggambar panah merah beranimasi di sepanjang jalur lane
   selama 2 detik (120 frame) setiap wave dimulai (`_render.py:1275-1367`,
   dipicu `_core.py:1762`, digambar `_render.py:789`). Kini ada
   `godot/scenes/fx/PathPreview.gd` (dipicu `Main._show_path_preview()` dari
   `_on_wave_started`, lane dibaca dari `ArenaMap.get_lane_path` dengan urutan
   `top, mid, bot` persis `_core.py:1757`); 130 frame state machine + 490
   polygon dikunci fixture `render_fx.path_preview` dan di-replay
   `RenderFxParityTest` (CI langkah 4v). Peta blok lainnya di
   [RENDER_PY_COVERAGE.md](RENDER_PY_COVERAGE.md). Yang ikut ditutup di fase
   yang sama: `HitParticle` (`:418-493`), `DeathExplosion` (`:494-571`), dan
   lapangan `EffectManager.particles`/`explosions` + batas 500/80
   (`:601-800`) — ketiganya juga belum pernah ada padanannya.

5. **HUD/menu tidak diaudit piksel demi piksel** di sini — sudah dikunci
   `UiHudParityTest.gd` + `godot/tests/fixtures/match_parity.json`.

6. **Satu warna `UiTheme` ditulis ulang sebagai literal** di
   `godot/scenes/ui/TopupDialog.gd` — bukan salah, tapi kalau `UiTheme.gd`
   diubah, berkas ini tidak akan mengikuti.

## 6. Temuan lanjutan (diverifikasi setelah laporan ini terbit)

Audit lanjutan memakai dua pemeriksaan baru (`GEOMETRI`, `CALLGROUP`) dan
menyisir `_render.py` kelas demi kelas. Hasilnya:

* **`KillFeed` BUKAN divergensi** — dibuat (`_render.py:622`) dan di-update
  (`:783`), tetapi `kill_feed.draw` dan `kill_feed.add` tidak pernah
  dipanggil di mana pun. Kode mati: pygame sendiri pun tidak menampilkannya.
  Sejak FASE 26 klaim ini **dikunci mesin**: `tools/test_render_parity.py`
  menulis `render_fx.dead.kill_feed_render.sites` dan gagal kalau suatu hari
  ada call site render di pygame.
* **`PopupAnimation` BUKAN divergensi** — pola yang sama persis
  (`_core.py:2584` membuat, `:2597` update, tanpa `.draw`). Kode mati.
  Dikunci dengan cara yang sama (`render_fx.dead.popup_animation_render`),
  dan `hero_items._fx_chain` (8 call site `add_hit_particles`, count 6 biru)
  tercatat sebagai satu-satunya situs percikan yang **belum** diport.
* **`ScreenShake` DULU divergensi terbesar, sudah diperbaiki** — lihat
  temuan 7.

### Temuan 7: semua screen shake di Godot adalah no-op senyap

`Boss._shake()` dan `Hero.kit_shake()` memanggil
`call_group("camera", "add_trauma", ...)` — tetapi **tidak ada satu pun
skrip di proyek yang mendefinisikan `add_trauma`**. `Camera2D` di
`scenes/main.tscn` adalah node polos tanpa skrip, dan Godot **tidak
mengeluarkan error** untuk `call_group` ke metode yang tidak ada: ia diam
saja. Jadi setiap guncangan layar hilang tanpa jejak, sementara pygame
memanggilnya dari puluhan tempat (modul `heroes/*_fx.py`, boss, menara) dan
menerapkannya ke seluruh surface dunia (`_core.py:2826`).

**Perbaikan:** `godot/scenes/main/GameCamera.gd` (kamera arena + shake),
dipasang ke node `Camera2D` di `scenes/main.tscn`. Angkanya disalin dari
`_render.ScreenShake` (`_render.py:572-599`), bukan dikira-kira:

| perilaku | pygame | GameCamera.gd |
|---|---|---|
| peluruhan | `intensity *= 0.85` per frame | `pow(0.85, delta*60)` |
| beberapa sumber | `max`, tidak menjumlah | `maxf`, tidak menjumlah |
| batas berhenti | `< 0.5` → `0` | `< 0.5` → `0` |
| offset | `randint(-int(i), int(i))` | `randi_range(-span, span)` |
| satuan | piksel | `1.0 trauma = 60 px` |
| UI ikut? | tidak (`draw_ui` terpisah) | tidak (`offset` kamera) |

Satuan `1.0 trauma = 60 px` dipilih karena pemanggil yang sudah ada
memakai `amount / 60.0`: `Boss._shake(25.0)` → trauma `0.4167` → **25 px**,
tepat sama dengan `add_shake(25.0)` di pygame.

### Pemeriksaan baru supaya ini tidak perlu dicek manual lagi

* **`GEOMETRI`** — setiap indeks frame di `baked_units.json` /
  `baked_props.json` harus memunculkan region yang **muat di dalam PNG**, dan
  titik jangkar harus **berada di dalam sel**. 465 grup tervalidasi, bersih.
  Pemeriksaan ini terbukti bergigi lewat uji negatif: anchor nexus yang
  pernah meleset (`[60,107]` pada sel tinggi 106), indeks frame menara di
  luar berkas, dan berkas yang hilang — semuanya tertangkap.
* **`CALLGROUP`** — setiap metode yang dipanggil lewat `call_group` harus
  punya definisi `func` di proyek. Inilah yang akan menangkap temuan 7
  kalau ia muncul lagi di masa depan.

Keduanya sudah masuk `ALL` dan otomatis ikut di `--full`, jadi CI
(`.github/workflows/godot-check.yml`) menjalankannya setiap push.

---

<!-- BEGIN AUTO AUDIT -->
## Hasil audit terakhir (otomatis)

Dihasilkan `tools/visual_parity_audit.py` (`--full` = ya).

```
════════════════════════════════════════════════════════════════════════
AUDIT PARITAS VISUAL  pygame ↔ Godot
════════════════════════════════════════════════════════════════════════
lingkungan: Python 3.11.2  |  Pillow 12.3.0  |  pygame 2.5.8  |  SDL_VIDEODRIVER=dummy

✅ PASS       PALET
      32 konstanta warna dibandingkan

✅ PASS       ENCODER
      _save_strip deterministik
      _save_map_png deterministik
      bake menuntut numpy (tanpa numpy: minion merah beda piksel)
      numpy tersedia (2.4.6)

✅ PASS       FRESH-UNIT
      dibandingkan semua 222 unit

✅ PASS       FRESH-MAP
      dibandingkan semua 54 map

✅ PASS       FRESH-PROP
      dibandingkan 20 strip props

✅ PASS       GEOMETRI
      465 grup frame divalidasi (region + anchor)

✅ PASS       CALLGROUP
      1 metode call_group diperiksa

✅ PASS       COVERAGE
      hero/boss  bake 222 entri
      map        bake 54 entri
      minion     bake 10 entri
      tower      bake 8 entri
      nexus      bake 2 entri
      tower      Godot Tower.gd                                    21 primitif  vs  pygame towers/_bundle.py       7274 baris
      minion     Godot UnitSilhouette.gd                           56 primitif  vs  pygame minions/_bundle.py      9531 baris
      nexus      Godot Nexus.gd                                    19 primitif  vs  pygame _entity.py              6536 baris

✅ PASS       SMOKE
      minion: bersih
      tower: bersih
      hero/boss: bersih

✅ PASS       HARDCODE
      1 pemakaian warna UiTheme yang ditulis ulang sebagai literal di .gd
         godot/scenes/ui/TopupDialog.gd                       1
      (ini bukan salah, tapi titik drift: ubah UiTheme.gd tidak menjangkau berkas ini)

────────────────────────────────────────────────────────────────────────
RINGKASAN: 10 PASS, 0 WARN, 0 FAIL
════════════════════════════════════════════════════════════════════════
```
<!-- END AUTO AUDIT -->
