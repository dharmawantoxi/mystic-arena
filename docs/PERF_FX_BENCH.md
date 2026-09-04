# Audit performa FX — apa yang paling banyak bikin lag

Tanggal: 2026-09-04 (sandbox, pygame-ce 2.5.8, dummy video driver)

## Cara mengukur

```bash
# satu hero FX per modul
python3 tools/bench_fx_heroes.py --frames 30 --multi 1 --quality high

# 4 hero FX berbarengan (simulasi combat ramai)
python3 tools/bench_fx_heroes.py --frames 25 --multi 4 --quality high

# beban combat dikunci ke 0.35 (governor aktif)
python3 tools/bench_fx_heroes.py --frames 25 --multi 4 --quality high --load 0.35
```

Metadata: permukaan 1280x720, quality `high`, `multi = 4` unit sejenis.
Angka ini pengukuran relatif di CPU sandbox — di HP biasanya 2–5x lebih
mahal, jadi perbandingan antar modul yang penting, bukan absolutnya.
Budget acuan 60 FPS = 16.7 ms/frame; 30 FPS = 33.3 ms/frame.

## Hasil sebelum perbaikan (baseline)

`fx_load = 1.0`, 4 unit per modul:

| Peringkat | Modul FX          | ms/frame | partikel | muat-budget 60fps |
|---:|---|---:|---:|---:|
| 1 | ancient_apparition | 8.33 | 666 | 2.0x |
| 2 | gornak             | 7.64 | 680 | 2.2x |
| 3 | thalgryn           | 7.15 | 351 | 2.3x |
| 4 | gorath             | 6.94 | 260 | 2.4x |
| 5 | grimjaw            | 5.78 | 223 | 2.9x |
| 6 | varkul             | 5.68 | 310 | 2.9x |
| 7 | nyxara             | 5.41 | 265 | 3.1x |
| 8 | zharok             | 5.06 |  23 | 3.3x |
| 9 | kunkka             | 4.32 | 104 | 3.9x |
| 10 | gravefang          | 4.20 | 181 | 4.0x |

Kesimpulan pertama: **seorang FX yang mahal saja sudah memakan 30–50%
budget frame**. Dengan 2–3 hero jenis itu di layar, lag sangat masuk akal.

## Akar masalah yang ditemukan

### 1. Sebagian modul tidak mematuhi FX governor

`mobile/perf.py` punya governor `set_fx_load()/fx_load()`:
makin banyak hero live-FX aktif, `Quality.particle_ratio` makin rendah,
dan semua modul harus menurunkan jumlah partikel.

Sebelum audit, modul berikut **mengembalikan jumlah tetap** atau hanya
memakai preset `quality` (bukan `quality x fx_load`), sehingga governor
tidak menurunkan partikel saat combat ramai:

- `varkul_fx.py`
- `zharok_fx.py`
- `ignis_drachorn_fx.py`
- `pyrenth_fx.py`
- `vokrahn_fx.py`
- `xerathis_fx.py`
- `alchemist_fx.py`
- `razak_fx.py`

Contoh paling jelas: `varkul` tetap menggambar ~310 partikel pada
`fx_load=0.35` maupun `fx_load=1.0`; `zharok` praktis tidak turun.

### 2. Partikel disalin / di-premultiply tiap frame

Beberapa modul memakai `_blit_faded` yang untuk tiap partikel melakukan
`surf.copy()` lalu `set_alpha`, atau `blit_add` yang menyalin surface ke
scratch + `fill(BLEND_RGB_MULT)` + blit tambahan.

Biaya ini **per partikel per frame** dan langsung terlihat di profil:

- `.copy()` / `Surface.copy` (sangat sering di `zharok`, `varkul`, `ignis`,
  `vokrahn`, `xerathis`, `pyrenth`, `nyzrak`, `krobellus`, `alchemist`)
- `fill(BLEND_*)` untuk premultiply
- blit tambahan

### 3. Cache surface "bocor" karena kunci warna berubah tiap frame

`zharok` partikel `ember` menghitung `col = _mix(fire_darkest, color, t)`
setiap frame. Karena `t` berubah sedikit demi sedikit, kunci cache
`(size, color)` hampir selalu berbeda → `ember_surface()` **membentuk
surface baru tiap partikel tiap frame** (2.5k panggilan per 40 frame di
profil). Ini membatalkan caching yang sudah ada.

### 4. Yang memang tetap berat: modul "selalu aktif" berbasis partikel besar

`gornak`, `gorath`, `ancient_apparition`, `thalgryn`, `grimjaw` sudah
mematuhi governor, tetapi dengan 4 unit tetap 5–8 ms/frame karena memang
punya banyak partikel + trail + skill berlapis. Ini kandidat utama untuk
pengurangan intensitas default (mis. preset medium di HP menengah).

## Perbaikan yang sudah diterapkan

### a. Semua modul FX kini membaca `Quality.particle_ratio`

- `alchemist_fx.py`, `razak_fx.py`: `_quality()` memakai
  `Quality.particle_ratio` (dulu `Quality.quality`).
- `varkul_fx.py`, `zharok_fx.py`, `ignis_drachorn_fx.py`,
  `pyrenth_fx.py`, `vokrahn_fx.py`, `xerathis_fx.py`: `particle_budget()`
  baru mengikuti `Quality.particle_ratio`.

### b. `ParticleSystem` benar-benar memakai anggaran partikel

Pada modul yang sebelumnya mengabaikan anggaran, `burst()` kini menurunkan
jumlah partikel sesuai `particle_budget()` (burst besar diskalakan; burst
satu partikel ditolak secara probabilistik agar tetap tidak kedap-kedip).
`spawn()` juga diberi gerbang probabilitas agar emisi kontinu ikut turun.

### c. Tidak ada lagi `surf.copy()` per partikel pada jalur non-additif

`_blit_faded` pada `varkul`, `zharok`, `ignis_drachorn`, `vokrahn`,
`xerathis`, `pyrenth`, `alchemist`, `nyzrak`, `krobellus` sekarang memakai
`Surface.set_alpha` langsung pada surface cache (visual sama, tanpa
alokasi salinan). Jalur additif yang memang butuh premultiply tetap
mempertahankan perilakunya di modul yang dirancang begitu.

### d. Cache warna zharok dikuantisasi

`zharok_fx` sekarang memakai `_quant_color()` (langkah 24) pada kunci
cache semua surface kecil (`glow`, `ember`, `ring`, `pool`, `arc_ring`),
sehingga partikel ember memakai ulang surface yang sudah dibangun alih-alih
membentuknya ulang tiap frame.

## Hasil setelah perbaikan

`fx_load = 0.35`, 4 unit per modul (satu run terbaru; ada variasi acak):

| Modul | Sebelum | Sesudah | Penurunan |
|---|---:|---:|---:|
| varkul | 5.74 ms | 4.08 ms | -29% |
| zharok | 5.65 ms | 2.79 ms | -51% |
| vokrahn | 2.53 ms | 1.46 ms | -42% |
| xerathis | 2.21 ms | 1.79 ms | -19% |
| pyrenth | 2.31 ms | 1.35 ms | -42% |
| razak | 3.39 ms | 2.84 ms | -16% |

`fx_load = 1.0` juga bergerak turun, tetapi beban FX pada combat ramai
adalah masalah utama; itu sebabnya perubahan yang paling terasa adalah
saat governor aktif.

Angka bervariasi antar run karena ada komponen acak; yang penting tren
turun pada modul yang sebelumnya tidak di-scale.

## Ronde 2: 5 hero starter (kasus yang dikeluhkan pemain)

Starter = `kaizen`, `grimjaw`, `sylara`, `vex`, `zephyr` (pasangan
populer yang biasa di-letakkan barengan). Benchmark skenario terburuk:
5 hero sejenis, semua skill (q/w/e/r) + impact aktif bersamaan.

### Akar masalah ronde 2

1. **Governor lama tidak cukup agresif.** Dengan `_FX_BASE_HEROES=3`,
   `_FX_LOAD_EXP=0.5`, 5 hero aktif hanya turun ke ~0.78 — hampir tidak
   berpengaruh. Sekarang `BASE=1.5`, `EXP=1.1`, `MIN=0.20` membuat 5 hero
   aktif settle di `fx_load ≈ 0.27`, sehingga partikel dan detail skill
   ikut turun nyata.
2. **Emisi kontinu tidak lewat `burst()`.** Banyak sumber partikel
   (aura, trail, idle skill) memanggil `ParticleSystem.spawn()` langsung,
   sehingga meski `burst()` sudah memakai anggaran, jumlah partikel tetap
   tinggi. Sekarang `spawn()` punya gerbang probabilitas di semua modul
   starter (dan modul mana pun yang memakai `_in_burst`).
3. **Detail skill tidak diskalakan.** Cincin putus-putus, retakan tanah,
   dan rune menggambar jumlah segmen tetap per hero. Sekarang jumlah
   segmen/retakan/chevron dikalikan `skill_detail()` (turunan
   `Quality.particle_ratio`) — intensitas dikurangi, tidak ada frame
   skill yang dilewati.
4. **`_clamp_color()` panas.** Genexpr + `max/min` dipanggil ribuan kali
   per frame di 5 hero. Fast path untuk warna tuple int valid memangkas
   sebagian besar biaya warna.

### Hasil 5 hero starter (skill-matic, 5 unit per modul)

`fx_load` di-settle lewat governor (≈0.27), `quality=high`:

| Modul | ms (5 unit) | ms/hero | partikel |
|---|---:|---:|---:|
| kaizen  | 1.89 | 0.38 | 26 |
| grimjaw | 4.40 | 0.88 | 119 |
| sylara  | 2.71 | 0.54 | 27 |
| vex     | 1.34 | 0.27 | 19 |
| zephyr  | 2.64 | 0.53 | 75 |
| **total** | **12.98** | 2.60 | — |

Sebelum perbaikan ronde 2 total skenario yang sama sekitar **20 ms/frame**
pada PC; jadi total turun ~35%. Di HP dengan multiplier ~2x, angka ini
berada di sekitar 26 ms/frame — sudah masuk wilayah 30–40 FPS/30 FPS yang
jauh lebih stabil dibandingkan >40 ms sebelumnya.

### Yang diubah di ronde 2

- `mobile/perf.py`: kurva governor lebih agresif (`BASE=1.5`, `EXP=1.1`,
  `MIN=0.20`, `SMOOTH=0.35`).
- `zephyr_fx.py`, `grimjaw_fx.py`, `kaizen_fx.py`, `sylara_fx.py`,
  `vex_fx.py`: `particle_budget()`/`skill_detail()` + gerbang `spawn()`
  + detail skill dinamis + `_clamp_color()` fast path.
- `burst/stream/ring` memakai bendera `_in_burst` supaya anggaran hanya
  dihitung sekali (tidak double-scale) — ini menjaga kontrak tes
  "burst menghormati anggaran kualitas".

## Rekomendasi berikutnya

1. **Jalankan `tools/bench_fx_heroes.py` di HP asli** (atau
   `tools/bench_mobile.py`) dan bandingkan. Angka PC kepala saja tidak
   cukup; alpha blit bisa jauh lebih lambat di ARM.
2. **Turunkan preset default** di perangkat menengah (`MEDIUM`) sebelum
   memperbaiki visual lagi. `Q.particle_ratio` sekarang bekerja pada semua
   modul, jadi preset langsung terukur.
3. **Perketat governor untuk 4+ hero**: turunkan `_FX_BASE_HEROES` atau
   `_FX_LOAD_MIN` di `mobile/perf.py` bila HP 30 FPS masih tidak cukup.
4. **`gornak` / `gorath` / `ancient_apparition` / `thalgryn` / `grimjaw`**:
   masih berat karena partikel + trail berlapis. Perlu audit khusus
   biaya per lapisan dan prioritas skill mana yang boleh tetap penuh.
5. **Cache additif pra-skala** untuk `varkul`/`zharok`: bila pengurangan
   partikel masih belum cukup, tambahkan cache premultiply alpha (mis.
   `(ukuran, warna_kuantisasi, bucket_alpha)`) agar `blit_add` tidak perlu
   menyalin surface tiap frame.
6. **Kalibrasi governor di HP asli**: konstanta baru ini sengaja lebih
   agresif untuk 5 hero. Sebelum naik lagi, ukur dulu di perangkat target
   agar tidak memangkas visual secara berlebihan di skenario 1–2 hero.
