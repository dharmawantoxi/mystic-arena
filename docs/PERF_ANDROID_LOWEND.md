# Optimasi performa HP low-end (v32)

Tanggal: 2026-09-05 · sandbox: pygame-ce 2.5.8, SDL 2.32.10, Python 3.11,
driver video `dummy` (tanpa GPU) · skenario ukur: **120 minion + 10 hero
bertarung, semua skill di-auto-cast**

Dokumen ini lanjutan `PERF_FX_BENCH.md`. Ronde sebelumnya memangkas
partikel FX; ronde ini menyerang **biaya tetap per hero per frame**, yang
ternyata justru sumber lag terbesar yang tersisa.

---

## 1. Cara mengukur (dan kenapa alat lamanya tidak cukup)

`tools/bench_wave.py` memberi satu angka ms/frame. Selisih 1 ms hilang di
dalam noise antar-run (terukur: run yang sama bisa berbeda 1,2 ms). Tiga
alat baru ditambahkan supaya setiap klaim di bawah bisa diulang:

| Alat | Fungsi |
|---|---|
| `tools/bench_phase.py` | pecah waktu frame **per fase** (`perf.PHASES`) + statistik cache sprite hero. `--keep-alive` membuat jumlah hero stabil supaya hasil bisa dibandingkan. `--miss-time` mengukur ms/frame di dalam jalur cache-miss. |
| `tools/bench_hero_miss.py` | biaya **satu** cache-miss render hero, dipecah per tahap. Deterministik → selisih kecil pun terlihat. |
| `tools/bench_fx_layers.py` | biaya lapisan FX hidup (`heroes/*_fx.py`) per modul, dipisah lapisan tanah vs lapisan atas. |

Dua penjaga regresi:

| Uji | Yang dijaga |
|---|---|
| `tools/test_hero_sprite_parity.py` | sprite hero jalur baru **identik piksel-per-piksel** dengan jalur lama |
| `tools/test_fx_ground_budget.py` | anggaran lapisan FX tanah tidak membekukan simulasi FX, dan tidak membuat FX berkedip |

Angka frame dilaporkan sebagai **minimum dari 7 ulangan** (bukan
rata-rata) karena benchmark ini CPU-bound: nilai minimum paling dekat ke
biaya sebenarnya.

---

## 2. Hasil pengukuran awal: ke mana waktu frame habis

`tools/bench_phase.py --quality low --minions 120 --heroes 10` (PC):

| Fase | ms/frame | % |
|---|---:|---:|
| **e.hero** | **8,83** | **74,3%** |
| e.minion | 1,66 | 14,0% |
| map | 0,50 | 4,2% |
| e.base | 0,39 | 3,3% |
| lainnya | 0,51 | 4,2% |

Tiga per empat waktu frame habis untuk **menggambar hero**. Dipecah lagi
(10 hero hidup):

| Bagian | ms/frame |
|---|---:|
| lapisan FX hidup hero (`_live_fx_pre` + `_live_fx_post`) | **6,56** |
| jalur cache-MISS sprite hero | 1,79 |
| blit sprite (cache hit) + HP bar/papan nama | ~0,5 |

Dan di dalam satu cache-miss sprite hero:

| Tahap | ms | % |
|---|---:|---:|
| renderer prosedural | 1,39 | 49,7% |
| **`canvas.get_bounding_rect()`** | **1,08** | **38,4%** |
| `_finish_hd_sprite` (mask + rim light + outline) | 0,22 | 8,0% |
| alokasi `Surface` | 0,05 | 1,8% |
| `smoothscale` | 0,04 | 1,4% |
| `subsurface().copy()` | 0,02 | 0,8% |
| **TOTAL** | **2,80** | |

Penyebab baris kedua: ukuran canvas sprite hero diturunkan dari
**jangkauan serang** (rata-rata terukur 434×434 = 188.584 px), padahal isi
sprite-nya hanya ~89×89. `get_bounding_rect(min_alpha=8)` memindai SEMUA
piksel itu untuk menemukan kotak 89×89 — 38% biaya satu miss terbuang
untuk memindai ruang kosong.

---

## 3. Yang diubah

### a. Ukuran canvas sprite hero DIPELAJARI, bukan dihitung dari range

Canvas sekarang berukuran **sebesar isi yang benar-benar tergambar**, dan
ukuran itu dipelajari per `(tipe hero, jenis pose)` — bukan per pose.
Pembedaan ini penting: kunci pose skill selalu baru (lihat
`_hero_cache_key`), jadi geometri per pose tidak pernah dipakai ulang;
geometri per (tipe, pose) dipakai terus sepanjang match.

Konten yang menyentuh tepi canvas membesarkannya lagi lalu render ulang,
jadi **tidak ada FX yang terpotong**.

Terukur (`tools/bench_hero_miss.py --quality low`):

| | sebelum | sesudah |
|---|---:|---:|
| ukuran canvas | 240–684 px | 152–252 px |
| `get_bounding_rect` + crop + alokasi | 1,295 ms | 0,251 ms |
| **TOTAL satu cache-miss** | **2,761 ms** | **1,692 ms (−38,7%)** |

### b. Kotak crop di-cache per pose + canvas dipakai ulang

Untuk pose yang kuncinya berulang (attack/idle), kotak crop disimpan dan
`get_bounding_rect` tidak dipanggil lagi — cukup periksa 4 strip sempit
(±2.000 px, ~0,01 ms) di sekeliling kotak. Canvas `Surface` juga dipakai
ulang per ukuran, dan yang dibersihkan hanya bekas tinta sebelumnya.

### c. Pass "HD" sprite hero dimatikan di preset LOW

`_finish_hd_sprite` menjalankan `mask.from_surface` + 8 `mask.draw` +
`to_surface` + rim light. Di PC 0,22 ms per miss; di ARM operasi
`pygame.mask` jauh lebih mahal. Sekarang diatur `Quality.hd_edge` dan
`Quality.hero_lighting` (mati di LOW). Badan, warna tim, dan animasi hero
tidak berubah — yang hilang hanya rim light 1 px dan garis tepi gelap.

### d. Anggaran render penuh hero per frame

Cache-miss datang **bergerombol**: begitu wave masuk, banyak hero ganti
pose di frame yang sama. `bench_wave.py` merekam draw p95 18,9 ms padahal
rata-ratanya 10,8 ms — selisih itulah yang dirasakan pemain sebagai
"patah". Sekarang jumlah render penuh per frame dibatasi
(`Quality.max_hero_render`: 2/3/6 untuk LOW/MEDIUM/HIGH); yang kehabisan
jatah memakai ulang sprite terakhirnya (1–2 frame lebih tua). Controller
pose tetap dimajukan, jadi animasi tidak pernah membeku. Hero yang belum
punya sprite tidak pernah ditunda.

### e. Anggaran lapisan FX tanah — sumber penghematan terbesar

Profil lapisan FX (`tools/bench_fx_layers.py`, 10 hero, LOW):

| modul | tanah | atas | total |
|---|---:|---:|---:|
| razak | 0,37 | 0,87 | 1,24 |
| grimjaw | 0,31 | 0,82 | 1,12 |
| kunkka | 0,68 | 0,39 | 1,07 |
| alchemist | 0,42 | 0,50 | 0,93 |
| lainnya (5 hero) | 0,79 | 1,31 | 2,10 |
| **total** | **2,57** | **3,99** | **6,56** |

Governor partikel sudah memangkas partikel sampai ~6% di skenario ini,
jadi biaya yang tersisa **bukan partikel** — ini ratusan panggilan
`pygame.draw.*` dan `blit` per hero per frame (profil: 18 blit + 27
circle + 20 line + 14 polygon per hero). Di HP, kode Python 3–5× lebih
lambat: 6,56 ms di PC = 20–33 ms di HP.

Yang dibatasi **hanya lapisan tanah** (aura/cincin/decal di bawah kaki
hero): `Quality.fx_ground_budget` = 3/6/tak-terbatas untuk
LOW/MEDIUM/HIGH. Lapisan ATAS (visual skill, trail, proyektil, impact)
tetap digambar penuh untuk semua hero setiap frame.

> **⚠ Jebakan yang benar-benar terjadi saat fitur ini dibuat.**
> Versi pertama melewatkan seluruh `mod.draw_ground_layer()`. Ternyata di
> semua 27 modul `heroes/*_fx.py` fungsi itu berisi tiga hal —
> `attach(hero)`, `tick()`, lalu `draw_ground()`. Melewatkan seluruhnya
> membuat **simulasi FX ikut membeku** dan lapisan atasnya pun mati:
>
> ```
> lewatkan seluruh fungsi : lapisan atas 0,03 ms/frame  (FX MATI)
> lewati gambarnya saja   : lapisan atas 3,99 ms/frame  (utuh)
> ```
>
> Sekarang `attach()` + `tick()` tetap dijalankan; hanya `draw_ground`
> yang dilewati. `tools/test_fx_ground_budget.py` mengunci perilaku ini
> (uji itu terbukti GAGAL kalau `tick()` dilewati lagi).

Hero yang dapat jatah **stabil** (urutan gambar hero tetap, hero pemain
lebih dulu), jadi tidak ada hiasan yang hilang-timbul antar frame.

### f. Lantai kuantisasi pose mengikuti preset

`Quality.skill_quant_floor` = 12/6/2 dan `Quality.atk_quant_floor` = 4/2
untuk LOW/MEDIUM/HIGH. Sebelumnya governor kuantisasi baru agresif kalau
combat ramai, jadi HP kentang tetap membayar miss 2,8 ms per pose walau
hero-nya cuma dua. Preset HIGH tidak berubah sama sekali.

### g. Bayangan minion di-cache

`draw_shadow` mengalokasi `Surface(SRCALPHA)` + menggambar ellipse untuk
**setiap minion setiap frame** (80 minion = 80 alokasi + 80 ellipse per
frame), padahal bentuk dan warnanya tidak pernah berubah. Sekarang
di-cache per `(lebar, tinggi, alpha)`.

---

## 4. Hasil akhir

`tools/bench_phase.py --minions 120 --heroes 10 --keep-alive --frames 300`,
minimum dari 7 ulangan, PC:

| Preset | sebelum | sesudah | penurunan |
|---|---:|---:|---:|
| **LOW** | 12,00 ms | **10,11 ms** | **−15,8%** |
| **MEDIUM** | 14,45 ms | **12,10 ms** | **−16,3%** |
| **HIGH** | 15,96 ms | **14,47 ms** | **−9,3%** |

HIGH turun paling sedikit **memang disengaja**: di HIGH anggaran lapisan
tanah tidak terbatas dan pass HD tetap nyala, jadi hanya canvas-dipelajari
+ anggaran render yang bekerja. Tidak ada visual yang berubah di HIGH.

Biaya satu cache-miss sprite hero (`tools/bench_hero_miss.py --quality low`):
**2,761 ms → 1,692 ms (−38,7%)**.

### Kebenaran visual diuji, bukan diasumsikan

`tools/test_hero_sprite_parity.py` membandingkan sprite hasil jalur baru
dengan jalur lama piksel-per-piksel (RGB + alpha), 36 tipe hero × 6 pose:

```
kualitas=low     216 kombinasi  OK - IDENTIK
kualitas=medium  216 kombinasi  OK - IDENTIK
kualitas=high    216 kombinasi  OK - IDENTIK
```

Satu-satunya perbedaan visual yang disengaja ada di preset LOW: tanpa rim
light/outline 1 px, dan lapisan tanah hanya untuk 3 hero terdekat.

---

## 5. Status pengujian

Semua `tools/test_*.py` dijalankan. Tiga berkas gagal, dan **ketiganya
sudah gagal di commit dasar `78af022` sebelum perubahan ini** (diperiksa
lewat `git worktree`):

- `tools/test_drakar_max.py` — `AssertionError: gornak H=115 vs morgath H=112`
- `tools/test_no_caster_light_pillar.py` — 2 FAIL
- `tools/test_topup_server.py` — HTTP 500 (butuh server top-up jalan)

Yang lolos dan relevan langsung dengan perubahan ini:
`test_hero_sprite_parity`, `test_fx_ground_budget`, `test_fx_stability`,
`test_hero_cache`, `test_hero_hd_render`, `test_hero_pose_cache`,
`test_hero_lighting`, `test_spritecache`,
`test_renderer_projectiles_not_baked`.

---

## 6. Yang belum dikerjakan (jujur)

1. **Semua angka di atas dari CPU sandbox, bukan HP asli.** Kode Python di
   ARM 3–5× lebih lambat, jadi penghematan absolutnya di HP diperkirakan
   3–5× lebih besar (LOW: ~6 ms/frame di PC → ~20–30 ms/frame di HP),
   tetapi itu **perkiraan**, bukan pengukuran. Jalankan
   `tools/bench_phase.py --quality low --keep-alive` di perangkat target
   untuk memastikan.
2. **Lapisan ATAS FX hero (3,99 ms/frame) masih utuh.** Ini sekarang
   komponen tunggal terbesar. Menurunkannya lagi berarti memilih:
   mengoptimasi 27 modul `heroes/*_fx.py` satu per satu, atau menambah
   preset di bawah LOW yang mengurangi detail skill. Keduanya keputusan
   desain grafis, bukan keputusan teknis — jadi tidak diputuskan di sini.
3. **Renderer prosedural hero (1,39 ms per miss)** tidak disentuh; itu
   50–70% biaya miss yang tersisa dan butuh audit per renderer.
4. `e.minion` (1,66 ms/frame) baru kena perbaikan bayangan; sisanya
   belum diaudit.

## 7. Saklar pembanding

Semua optimasi v32 bisa dimatikan sendiri-sendiri untuk pengukuran ulang
(default: NYALA):

```bash
MYSTIC_HERO_CANVAS=0   # canvas kembali sebesar jangkauan serang
MYSTIC_HERO_GEOM=0     # kotak crop dihitung ulang tiap miss
MYSTIC_HERO_DEFER=0    # tanpa anggaran render penuh hero
MYSTIC_FX_GROUND=0     # lapisan FX tanah tanpa batas
```
