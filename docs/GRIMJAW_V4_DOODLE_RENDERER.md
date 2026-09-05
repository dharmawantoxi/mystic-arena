# Grimjaw v4 — Renderer Doodle Sketch

Penulisan ulang total renderer Grimjaw (`heroes/_bundle.py`, namespace
`_NS_grimjaw`) dari pixel-masterwork v2 ke **doodle sketch** — dari nol,
bukan patch. 100% prosedural: tidak ada PNG, sprite-sheet, atau
`pygame.image.load` — diverifikasi oleh test v3 (larangan string
`surf(`, `load_asset`, `.png`, dll).

Alasan rewrite (permintaan pengguna): renderer lama dianggap "jelek
sekali"; gaya baru = **sketsa spidol tangan**: outline tinta gelap
ber-gores dua pass, warna blok flat, wobble sub-piksel deterministik,
arsiran hatch, dan marker angular untuk AOE. Lapisan FX live
(`heroes/grimjaw_fx.py`) ikut di-doodle-kan lewat builder bersamanya
tanpa menyentuh arsitektur pooling/timer.

Dokumen ini menggantikan `GRIMJAW_V2_RENDERER.md` (pixel masterwork,
dipertahankan sebagai referensi historis).

## Before / after

| | pixel v2 | doodle v4 |
|---|---|---|
| Gaya | ramp 4–5 band + hue-shift, selout, dither | **blok flat + outline spidol 2 pass + hatch** |
| Warna unik (idle native) | 142 | **38** (blok flat per bagian; portrait LOD 39) |
| Rig native (bbox idle) | 74 × 186 | **73 × 189** (skeleton metric sama: telapak +68..76, mane ≈ −102..−106) |
| Tinggi di layar | ~75 px | **~78 px** (scale 0.412, jendela probe 40–130 tetap valid) |
| Outline | selout bergerigi + rim light | **tinta (20,17,23) 2 pass**: pass-2 = jitter skala 1.3 + offset (0.9, −0.7), garis rangkap khas coretan |
| Bayangan | ramp hue-shift | **arsiran hatch** (`_hatch_patch`) + `_scribble` |
| Marker AOE | cincin kontinu | **tick radial angular** (Q: 26 tick, radius 70 dunia) + bracket sudut |
| Loop attack | closure ap=1.0 = idle | **tetap** (diff < 120 px = hanya combat-glow mata) |
| Pose attack | 10 unik (stance→strike→rest) | **tetap 10 unik**, puncak y=−80 @0.37, pendaratan (85, 43) |
| Bilah | flame blade curve 11·t² | **tetap** (solver grip/tip/angle/len + ATTACK_* timeline tidak berubah) |
| Biaya render (median) | idle 1.4 ms | idle **2.4 ms**, attack 2.5 ms (budget 3.5 ms cache-miss; steady = blit cache) |

## Kontrak yang TIDAK berubah

- Entry point `draw_grimjaw(surface, hero, x, y)` + alias `draw_hero`;
  kelas tetap `_NS_grimjaw`; **seluruh** simbol `_EXTRA['grimjaw']`
  (114 nama) tetap didefinisikan.
- Helper geometri bilah untuk `grimjaw_fx.blade_points()` dan test arah
  swing: `_blade_angle`, `_blade_grip_local`, `_blade_tip_local`,
  `_blade_len`, konstanta `ATTACK_*`.
- Seluruh key `PALETTE` (nilai berubah, nama tetap); `DEBUG_CHARACTER`
  tetap `False`.
- Skeleton metrics (kaki, mane, grip ~(17,3), blade 52/58) sehingga
  scale pipeline (~0.41) dan probe window 40–130 px tidak bergeser.
- Timer/skill gameplay: Q=Blade Fury, W=Healing Ward, E=Critical
  Strike, R=Omnislash; durasi visual mengikuti
  `SKILL_VISUAL_DURATION` yang sama.
- Cache & buffer: pool `_static` (cap 96), `_GHOST_BUF` 220²,
  `_OMNI_BUF` 12 bucket 240².

## Perhalus ala khalros (pass v4.1)

Setelah gaya doodle dasar jalan, dilakukan pass "perhalus" mengikuti
resep halusnya Khalros (`_NS_khalros` di `bosses/level2.py`):

1. **Lingkaran anti-aliased** — `pygame.draw.aacircle` (pygame-ce)
   lewat helper `_aacircle` (fallback `draw.circle`; warna ber-alpha
   via surface sementara, idiom sama persis dengan khalros). Dipakai
   untuk mata, kancing/stud, medali, tetes darah, mata totem ward,
   dan inti `_doodle_star`; blob kecil yang nyaris bulat
   (`|rx−ry| ≤ 1`, radius ≤ 9) otomatis memakai jalur AA di
   `_ink_ellipse`. Tepi blending-nya benar (alpha partial, tanpa
   fringe gelap).
2. **Satu goresan bersih, bukan sketsa ganda** — pass-2 outline yang
   melenceng (scratchy double stroke) dihapus dari `_marker_poly`,
   `_ink_stroke`, `_ink_polyline`; sebagai gantinya outline utama
   ditebalkan (+1 px untuk width ≥ 2) sehingga bobot tintanya seperti
   spidol besar khas khalros.
3. **Wobble lebih lembut** — amplitudo jitter 1.05 → 0.82 (komponen
   tangensial 0.45 → 0.36), subdivisi lebih kasar (7.5/8 → 10 px,
   `_ink_stroke` 6.5 → 9): goresan tetap terasa tangan tapi tidak
   kasar.
4. **Elips lebih bulat** — jumlah vertex adaptif naik untuk radius
   besar (hingga 20), sehingga pauldron/mask tidak terlihat poligonal.
5. Efek samping positif: satu pass outline = lebih sedikit
   `draw.lines` → **idle turun ke ~1.9–2.0 ms** (dari 2.4).

Kontrak yang tetap utuh: loop closure ap=1.0 (audit lolos), swatch
PALETTE di pipeline final, portrait LOD tetap lebih kaya warna
(114 → 116), stroke tinta tetap solid alpha ≥ 180.

## Engine wobble (inti gaya doodle)

1. **`_hash01` integer finalizer** (bukan sin/floor): perkalian
   `0x9E3779B1` / `0x85EBCA6B` dengan xor-shift — ~6× lebih murah dan
   tetap deterministik terhadap seed.
2. **`_jitters(n, seed, amp)`** menghitung pasangan (normal,
   tangensial) per vertex **sekali per bentuk**; `_apply_jitter(pts,
   js, closed, scale)` memproyeksikannya. `closed=False` menjaga
   endpoint persis (sendi tetap nyambung antar-bentuk).
3. **`_JIT_CACHE`** — array jitter di-cache lintas frame per
   `(n, seed)`: bucket fase animasi terbatas, jadi pose yang di-render
   ulang (cache-miss berulang) mengambil array tanpa menghitung hash.
4. Pass-2 outline memakai jitter yang sama dengan skala 1.3 + offset
   (0.9, −0.7) — garis rangkap "digambar dua kali" ala spidol, bukan
   hash baru.
5. `_ink_polyline` melewati pass-2 bila bbox < 200 px² (detail kecil
   cukup satu gores); `dot` ≤ 2.2 px jadi lingkaran polos (wobble tak
   terbaca); `_flame_tongue` passes=1 bila length < 18; `_scribble`
   12 langkah dengan hash inline.

Signature primitif publik tidak berubah: `_marker_poly`,
`_ink_ellipse`, `_tube`, `_flame_tongue`, `_hatch_patch`,
`_doodle_star`, `_poof`, `_speed_ticks`, `_ember_marks`, `_scribble`,
`_ink_stroke`.

## Warna

Tinta digelapkan sampai siluet tahan lighting pass (audit silhouette):

- `ink` = (20, 17, 23), `ink_soft` = (44, 38, 50),
  `shadow_deep` = (20, 17, 23), `paper` = (250, 246, 236)
- api `fire_mid` = (230, 104, 22), `fire_light` = (248, 168, 48)

## Grounds skill (telegraph world-space di canvas hero)

- **Q Blade Fury** — tick radial angular 26 buah di radius 70 dunia
  (`_ring_r`), plus bracket sudut; terbaca dari segala arah kamera.
- **W Healing Ward** — ring dashed radius **90 dunia** (mengikuti
  radius heal gameplay ~100) + totem ward dengan mata `heal_mid`
  menyala hijau (bukan putih) selama ward aktif.
- **E Critical Strike** — cone api di depan + perkakas crit.
- **R Omnislash** — slash arc WINDUP−0.02..0.92, impact flash
  0.52–0.86, crit burst 0.56–0.82, swing trail 0.30–0.88.

## Restyle FX live (`heroes/grimjaw_fx.py`)

Arsitektur pooled/lifecycle/timer **tidak disentuh** (61 test v3 tetap
hijau). Yang berubah hanya isi builder bersama yang di-cache
`_SURF_CACHE` — semua konsumen (partikel, impact, skill FX, wave)
otomatis ikut gaya baru:

| Builder | v3 (lama) | v4 (doodle) |
|---|---|---|
| `glow_surface` | gradien radial halus | **4 band posterized**, pusat band digeser 1 px deterministik |
| `spark_surface` | bintang 4 sudut simetris | **asterisk 5 jarum** sudut/panjang tak rata |
| `ring_surface` | lingkaran `draw.circle` | **cincin wobble** vertex-jitter + pass kedua tipis |
| `ellipse_ring_surface` | elips `draw.ellipse` | **elips parametrik wobble** + pass kedua |
| `ground_glow_surface` | elips gradien premultiplied | **3 band + coretan horizontal** (arsiran spidol) |
| `crescent_surface` | 2 busur `draw.arc` | **busur polyline ber-jitter radial** |
| `draw_blade_wave` | 3 busur halus + glow | **3 busur coret** (`_warc` polyline wobble) + glow posterized |
| `SwingTrail` | 4 band alpha halus | **kontur tinta tepi luar** (lapis 0) + garis inti putih wobble |

Semua builder tetap deterministik per cache-key (jitter dari `_hash01`
pada komponen key), jadi test radius/timing/determinisme tidak berubah.
Larangan aset eksternal tetap dipatuhi.

## Performa

Median pada mesin referensi (528², cache-miss penuh):

| Pose / skill | v2 pixel | v4 doodle |
|---|---|---|
| idle | 1.4 ms | **1.9 ms** (v4.1 perhalus; 2.4 sebelumnya) |
| attack | — | **2.1 ms** |
| Q (skill q) | 1.9–2.4 ms | **2.6 ms** |
| W / E | — | **2.2 / 2.2 ms** |
| R | — | **0.8 ms** |

Dalam budget 3.5 ms untuk semua jalur; steady-state tetap satu blit
dari cache. Optimasi yang membuat doodle sebanding: jitter sekali per
bentuk + `_JIT_CACHE` lintas frame, hash integer, `_ipoints` tanpa
`round`, `dot` kecil polos, pass-2 bersyarat, subdiv 7.5/8.0.

## Verifikasi

- `tools/test_grimjaw_masterwork.py` — 8/8 OK.
- `pytest tools/test_grimjaw_v3_combat.py` — 61 passed.
- `tools/test_swing_anim.py` — 30/30 kombinasi hero×FPS.
- `tools/test_grimjaw_swing_arah.py` — tebasan atas→bawah tervalidasi.
- `tools/test_codebase_heroes.py` — 100%.
- `tools/_audit_grimjaw_v2.py` — **SEMUA CEK LOLOS** (bbox, tinggi
  layar, keunikan frame, loop closure, portrait LOD, marker world-space
  Q/W/E/R, budget ms).

Preview:

- Karakter & pose: [docs/grimjaw_masterwork_preview.png](grimjaw_masterwork_preview.png)
- Portrait LOD: [docs/grimjaw_portrait_preview.png](grimjaw_portrait_preview.png)
- Contact sheet: [docs/grimjaw_animation_strip.png](grimjaw_animation_strip.png)
- Review + skill + in-game: [docs/grimjaw_v2_review.png](grimjaw_v2_review.png),
  [docs/grimjaw_v2_skills.png](grimjaw_v2_skills.png),
  [docs/grimjaw_v2_ingame.png](grimjaw_v2_ingame.png)

Regenerasi sheet: `python tools/_shot_grimjaw_masterwork.py`,
`python tools/grimjaw_anim_demo.py`, `python tools/_audit_grimjaw_v2.py`.
