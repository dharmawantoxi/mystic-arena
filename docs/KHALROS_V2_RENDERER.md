# Khalros v2 — Pixel Masterwork + Skill FX

Penulisan ulang total renderer Khalros (`bosses/level2.py`, namespace
`_NS_khalros`) ke standar **Thorne v2 Pixel Masterwork + v2.1 Skill FX**, sekelas
`RAZAK_V2_RENDERER.md` / `GORATH_V2_RENDERER.md`. 100% prosedural: tidak ada PNG,
sprite-sheet, atau `pygame.image.load` — diverifikasi oleh test.

Alasan rewrite: versi v1 menggambar barbar dari ~450 warna dan satu lingkaran
stroke per skill. Siluetnya sempit (71 × 80 px), kapaknya tenggelam di balik
badan, dan telegraph-nya berupa cincin vektor 1 px yang terbaca sebagai garis UI,
bukan cahaya di lantai.

## Before / after

| | v1 | v2 |
|---|---|---|
| Badan di layar (bbox) | 71 × 80 px | **69 × 110 px** (lebih ramping, jauh lebih tinggi) |
| Kaki | 16 px rig per paha, dua lidi terpisah oleh celah latar | **menyatu jadi satu dasar 36 px rig**: pelindung lutut, betis bulu, boot melebar |
| Kapak saat `facing = -1` | dicermin vertikal (salah arah), ujung bilah lepas dari trail | cermin horizontal, `_axe_tip_local` = arah bilah |
| Rig native | digambar langsung di skala tampil | 92 × 157 px pada `RIG_SCALE` **1.5×**, diturunkan `SCALE` sekali |
| Warna unik (idle, stride 2) | 452 | **1 497** (3,3× lebih kaya) |
| Ramp per material | 2–3 band, hue sama | 4–7 band dengan **hue-shift** (gelap → merah-cokelat, terang → kuning) |
| Keyframe serangan | 1 (lerp tunggal) | **7 + frame IMPACT** di `ap = 0.54` |
| Siluet | mulus/lonjong | bergerigi via `_tuft_points` (jenggot, jubah, hem, sepatu) |
| Senjata | ditempel, kadang tertutup badan | solver grip + bilah, **pass `late=True`** di atas kepala |
| Telegraph skill | px canvas (menyusut di lane hero) | **world-space** Q 70 / W 120 / E 85 / R 200 px dunia |
| FX tanah | stroke `circle`/`ellipse` | decal ber-falloff (`_ground_scorch` + `_zone_fill` + `_ground_ring` + `_rune_ring`) |
| Biaya idle / R (steady) | 1.13 / 1.11 ms | 1.49 / 2.68 ms (budget keluarga 3.5 ms) |
| Cache permukaan | tidak ada | 0.15 MB setelah 4 cast penuh (razak 0.03, gorath 0.04) |

## Kenapa tingginya naik tapi lebarnya turun

Khalros adalah mini-boss level 2 yang berdiri, bukan terbang: tinggi 109 px
membuatnya terbaca sebagai "bapak perburuan" di antara razak (107) dan gorath
(98) tanpa menabrak label. Tabel ukuran keluarga, metode sama (canvas 528,
`_render_scale = 1.0`, `min_alpha = 100`):

| | razak | **khalros** | gorath | alchemist |
|---|---|---|---|---|
| bbox (w × h) | 96 × 107 | **100 × 121** | 112 × 98 | 130 × 133 |

Dua aturan yang tidak boleh dilanggar saat menyentuh bagian ini:

1. **SATU `SCALE` (0.68) untuk semua jalur** — boss, lane hero, portrait. Rig
   di-*author* 1.5× lalu diturunkan sekali di `_compose_body`. Lebar badan ikut
   jadi 69 px saat kaki ditebalkan dan itu disengaja: yang dibatasi adalah
   TINGGI (88–133 px, dikunci test) karena label + HP bar bergantung pada puncak
   siluet. Memecah scale per
   jalur merusak normalisasi `_measure_native_size` di `heroes/__init__.py` dan
   membuat hero menyusut/TIDAK seragam.
2. **Label clearance.** Rantai piksel teratas tiap pose diukur ulang setelah kaki
   ditebalkan (tingginya tidak bergeser): idle −65, walk
   −67, attack −69, Q −73, W −83, R −127 dari `y`. Karena itu
   `BOSS_LABEL_TOP["khalros"] = 72` di `bosses/base_boss.py` — kalau pose R
   dibuat lebih tinggi, nilai itu harus ikut naik, kalau tidak HP bar duduk di
   atas kepalanya.

## Pixel-art discipline

1. **Ramp 4–7 band + hue-shift** — kulit 6 (darah→ungu gelap di bawah, kuning
   oranye di atas), baja bilah 5, kulit jubah 5, tulang tanduk 4, emas 4, api
   7, asap 5. Tidak ada dua band dengan hue yang sama.
2. **Selout** — salinan `shadow_deep` tiap poligon di `(+facing, +1)`; outline
   hitam 1 px empat arah dipasang **setelah** penskalaan dan **setelah** pass
   cahaya, di `_draw_khalros_body`.
3. **Siluet bergerigi** — `_tuft_points` memecah jenggot, hem cawat, ujung jubah
   dan punggung sepatu bot jadi zigzag deterministik (seed per bagian, jadi tidak
   berkedip antar frame).
4. **Specular cluster** — 2–3 piksel `*_high`/`*_shine` di pauldron, bilah kapak,
   tanduk, dan mata elang; bukan satu titik putih.
5. **Dither band** — `_dither_dots` di transisi perut, lipatan jubah, dan bara
   tanah supaya gradasi tidak jadi garis.
6. **Key light kiri-atas** — `_lighting.apply_to_rig(sub, rim_add=(44, 26, 16),
   shade_mul=170)` pada sub-surface yang sudah di-scale, tepat sebelum outline.
   `NO_LIGHT=1` pada `tools/_shot_khalros_v2.py` menampilkan versi tanpa pass ini
   untuk memeriksa apakah paletnya berdiri sendiri (berdiri).

## Anatomi & senjata

Helm bertanduk ivory dengan palang perunggu, mata merah menyala di bawah brow
ridge, jenggot kusut tiga band dengan dua cincin perunggu. Pauldron tulang +
jubah kulit serigala di punggung (mata jahit terlihat), cawat kulit ber-hem
bergerigi, ikat pinggang dengan giggs tulang, sepatu bot berbulu. Elang peliharaan
duduk di bahu belakang — kepalanya bergerak, sayapnya mengepak saat `rage`, dan
menoleh mengikuti arah.

Dua kapak: **kapak tempur** di tangan depan (gagang `AXE_HANDLE = 24`, bilah
`AXE_BLADE = 27`, fuller gelap, edge highlight, berpijar `hot` saat impact) dan
**kapak cadangan** tersandang di punggung — hanya kepala bilahnya yang muncul di
atas bahu (`size` 0.68 supaya tidak jadi tombak yang melebarkan siluet). Grip dan
ujung bilah dihitung dari satu solver (`_axe_grip_local` / `_axe_tip_local`), jadi
ayunan, lempar, dan bawa-an memakai geometri yang sama — tidak ada kapak yang
"melayang".

### Proporsi kaki

Keluhan yang masuk setelah pass pertama: *"kakinya terlalu kurus sehingga terlihat
tidak proporsional"*. Akar masalahnya tiga, dan ketiganya sekarang dikunci
`test_legs_are_proportional_and_mirror_consistent` (diukur di ruang rig 1:1 pada
lapisan kaki saja, jadi tidak terganggu jubah/elang/kapak):

| Bagian | pass pertama | v2 final (rig px) |
|---|---|---|
| Paha | ±8, dua garis dengan celah latar di tengah | ±11.5, **dua paha menyatu** (nol celah) |
| Lutut | tanpa massa (taper langsung) | ±8.5 + **pelindung lutut kulit** + paku kuningan |
| Betis | ±5 di pergelangan | ±9.5 (gastrocnemius) → ±6.5 pergelangan, bulu + dither |
| Sepatu | ±6/±8, sol 14 px | ±9/±11, **sol 19 px** (tumit 8.5 / ujung 10.5, ikut ter-mirror) |
| Cawat | hem sampai +28 menutup seluruh paha | hem +26 → lutut dan paha terbaca |

Minimum lebar per baris: paha 30, lutut 24, betis 20 px rig; sepatu tidak boleh lebih
sempit dari 75% paha — karakter harus terlihat **berpijak**, bukan bertumpu.

### Aturan cermin

`facing` membalik **hadap**, bukan atas-bawah. Cara salah yang sempat dipakai:
`ang = angle * f`. Hasilnya kapak idle yang harusnya menengadah ke kiri menukik ke
kanan bawah — dan yang lebih parah, arah bilah tidak lagi sama dengan
`_axe_tip_local`, jadi trail ayunan + bintang impact mendarat di udara, bukan di
besi. Aturan yang benar (di `_draw_axe_swinging` dan `_draw_axe_held`):

```python
ca, sa = math.cos(angle) * f, math.sin(angle)   # hanya X yang dicermin
ang = math.atan2(sa, ca)
```

Jarak yang ditulis sebagai offset murni (mis. `bx + L * 0.5` pada bilah kapak
cadangan) ikut dikalikan `f`, dan sol kaki dihitung sebagai tumit/ujung terpisah:
`NS._rect(ax - c * f, ..., width)` TIDAK ikut ter-mirror (lebarnya tetap), jadi sol
bergeser seluruhnya ke satu sisi saat menghadap kiri dan terbaca sebagai goresan
lepas di samping kaki.

## Animasi

- **Foot solver** untuk jalan/lari: dua kaki + lutut + sol dihitung per fase,
  sol menyentuh tanah di `+66` rig px, bob vertikal mengikuti; saat **charge**
  kaki dilipat dan badan melayang (afterimage 4× di belakang).
- **Inersia sekunder**: jubah (`cape_lag`), jenggot (`beard_lag`), dan elang
  tertinggal dari akselerasi badan — di walk ±2 px, di ayunan −7 px, jadi
  siluetnya tidak terasa kaku.
- **Living idle**: napas, sway, kedip mata elang, denyut bara, jenggot bergoyang
  — 12 signature idle dan 12 signature walk berbeda semuanya (dikunci test
  `test_rig_has_real_animation_frames`).
- **Attack 7 keyframe** (`_attack_pose`): rise → tension (tremble 1 px) →
  overtop → **IMPACT di `ap = 0.54`** → follow-through → recover, dengan smear
  sabit tiga lapis, bintang benturan, dan retakan tanah di frame impact.
- **`late=True`, pass senjata kedua** (`_draw_khalros_body_raw`): setelah kepala
  digambar, sisi DEPAN (bilah + tangan penggenggam) dilukis ulang supaya kapak
  tidak hilang di balik helm/tanduk tepat pada frame yang paling dibaca pemain.
  Pass ini melukis ulang piksel yang sama, bukan menambah lapisan, jadi siluet
  tetap identik.
- **Badan bereaksi ke state skill**: mata membara + jenggot menegang saat
  `w`/`r` (rage), kepala menunduk + tangan siap lempar saat `q`/`e` (hunting).

## Skill FX (3 tahap, world-space)

Semua FX dikompensasi `_fx_scale = 1 / _render_scale` (cap **2.6**) dan
`_ring_r(boss, world_px, surface)` mengubah radius dunia → px canvas sekaligus
meng-clamp ke dalam canvas, jadi telegraph **di layar** tidak menyusut saat
sprite di-cache.

| Skill | Durasi | Radius | Aktivasi | Steady | Telegraph lantai |
|---|---|---|---|---|---|
| **Q Wild Axes** | 50 | 70 (di **target**) | whirl 3 kapak + bintang + 2 `AxeProjectile` di 0.30–0.44 | kapak berputar di orbit, trail busur | scorch + zone-fill + **ring tepat 70 px dunia** di target, rune ring dalam, 3 cakar konvergen, chevron berbaris dari caster ke target, ring konvergen di paruh kedua |
| **W Call of the Wild** | 60 | 120 (di caster) | pilar tanah 4× + shockwave ganda | 2 serigala ter-cache mengorbit, 3 arcs auman | ring 120 px + dashed ring + **mote emas penyembuh** naik, retakan mangsa |
| **E Boar Charge** | 45 | 85 (di caster/target lintasan) | debum + poof | overlay babi hutan + 4 afterimage (SATU render, di-blit) | ring pendaratan 85 px + debu jalur + scorch tertinggal |
| **R Hawk Storm** | 70 | 200 (di caster) | kolom angin + shockwave + bintang 8-spike | 6 elang menukik di 0.62 R + penanda tanah + mote bulu | ring 200 px + zone-fill badai + rune ring berputar + 7 streak + 6 chevron masuk + ring konvergen |

Aktivasi setiap skill memicu `_draw_shockwave` pada 12 frame pertama
(`age < 12`); test `test_activation_shockwave_window` mengunci bahwa gelombang itu
ADA di `age = 6` (bbox > 40 px) dan HILANG di `age = 13` (tidak ada piksel di atas
alpha 100).

Durasi dan radius adalah **angka AI**, bukan angka estetika: `SKILL_DUR` dibaca
dari `active_skill_timer = 50/60/45/70` dan `SKILL_RADIUS` dari `dist <= 70/120/85/200`
di `bosses/base_boss.py::_khalros_q/w/e/r`. Test `test_skill_durations_match_ai`
dan `test_skill_radius_matches_gameplay` mem-parse sumber AI sebagai teks dan
menolak kalau keduanya tidak cocok — jadi desainer tidak bisa mengubah hitbox
tanpa mengubah gambarnya (dan sebaliknya).

## FX tanah = decal ber-falloff (bukan stroke)

| Primitif | Fungsi |
| --- | --- |
| `_ground_scorch` | alas gosong ber-tepi gumpalan lembut → efek menempel di lantai |
| `_zone_fill` | wash zona **edge-weighted** (pekat di tepi, bening di tengah) |
| `_ground_ring` | batas AOE ber-gradien kuadratik; inti cincin di `radius + thickness + 1` |
| `_rune_ring` | cincin busur berputar; sudut dikunci ke dalam satu pitch segmen |
| `_glow` | gradien radial ter-cache (pengganti tumpukan `_aacircle`) |
| `_decal` / `_blit_decal` | LRU 48 entri; radius di-kuantisasi supaya cache nyangkut |

Dua jebakan yang sudah dibayar mahal dan jangan diulang:

1. **`BLEND_RGBA_ADD` mengabaikan alpha per-piksel.** Decal additive yang diisi
   gradien `(*color, a)` akan menjenuhkan RGB-nya dan muncul sebagai **piringan
   putih keras** — persis penyebab v1 terlihat rusak. Solusinya `_premul`:
   builder additive menulis `color * (a / 255)` di RGB dengan alpha 255, dan
   annulus dibangun dari luar ke dalam dengan `width = 1`. Test
   `test_additive_decals_are_premultiplied` menjaga ini. Lapisan ambient idle
   sengaja non-additive supaya tetap di bawah `min_alpha = 100` milik
   `_measure_native_size`.
2. **Kuantisasi radius: kasar untuk lapisan lunak, halus untuk cincin gameplay.**
   `_coarse()` membulatkan radius ke `max(10, r // 14)` untuk scorch / zone / glow
   — tanpa itu satu cast menghasilkan 40+ varian decal, LRU 48 di-*thrash*, dan
   setiap frame membangun ulang piringan 400–600 px. `_ground_ring` tetap
   `_quantize(r, 6)` karena radiusnya adalah **batas pukul** yang harus jatuh di
   angka AI (meleset 10 px terasa tidak adil bagi pemain).

## Performa & cache

Terukur di mesin yang sama, canvas 528 × 528, frame **steady** (state konstan,
cache hangat), median 5 × 25 frame:

| | idle | Q | W | E | R |
|---|---|---|---|---|---|
| khalros v2 | 1.49–1.74 | 1.97–2.19 | 2.19–2.71 | 2.39–2.73 | 2.68–2.90 |
| gorath v2 (pembanding) | 1.52–1.58 | 1.86–2.01 | 2.44 | 1.95–2.07 | 2.72–2.80 |

Semua di bawah budget 3.5 ms. Satu frame **cache-miss penuh** (semua cache
dibersihkan, R aktif, `_render_scale = 0.72`) 6–9 ms, masih ~½ frame budget.
Selama cast bergerak penuh R biayanya 3.85 ms/frame (jalur boss) dan 4.60 ms
(lane hero `_render_scale = 0.72`) — lebih berat dari ultimate razak/gorath
(2.9–3.0 ms) dan itu diketahui: penyebabnya `transform.rotate` pada satu cincin
rune berdiameter ~550 px (0.9–1.1 ms per rotate di mesin ini).

Tiga keputusan yang membuat angka itu mungkin:

- **`_compose_body` sekali render.** `_draw_khalros_charge` dulu menggambar rig
  penuh DUA kali (sekali untuk buffer afterimage, sekali untuk badan) → skill E
  3.84 ms, gagal budget. Sekarang rig dikomposisi sekali, hasilnya di-blit 4×
  dengan alpha menurun lalu sekali solid. E turun ke 2.3–2.7 ms.
- **Hasil rotasi TIDAK di-cache.** Pernah `_rune_ring` menyimpan tiap bucket sudut
  di `_STATIC_SURFACES`; kuncinya radius × bucket → 227 surface 400–580 px =
  **~105 MB per kelas boss** (razak/gorath: 0.03–0.04 MB). Sekarang decal dasarnya
  saja yang di-cache (0.15 MB setelah empat cast penuh) dan rotasinya dikerjakan
  per frame. Dikunci `test_surface_cache_memory_is_bounded` (batas 8 MB).
- **Satu rune ring untuk R.** Cincin angin dalam dipindah ke `_dashed_ring`
  (stroke berfasa, tetap berputar, ~0.05 ms) karena rune ring kedua menambah
  1.9 ms/frame selama ultimate.

Cache statis (aura primordial, bayangan, pelat lantai) dibangun sekali lewat
`_aura_cache` / `_shadow_cache` / `_STATIC_SURFACES`, per frame hanya
`set_alpha` + blit — tidak ada `.copy()` surface besar tiap frame;
`test_static_surfaces_are_cached` membandingkan identitas objeknya.
`_BEAST_CACHE` (binatang: boar/wolf/hawk) maksimum 160 entri, `_DECAL_CACHE`
maksimum 48 (LRU), `_STATIC_SURFACES` maksimum 320.

## Lane hero & lapisan hidup

`heroes/khalros_fx.py` adalah **FX-only** (1 899 baris): tidak ada lagi renderer
badan di sana — `draw()` didelegasikan ke `_draw_khalros_{charge,cast,attack,walk,idle}`,
dan `weapon_grip / weapon_angle / swing_tip` membaca rig lewat `_rig()` (lazy).
Ini menutup duplikasi 261 baris yang membuat dua jalur punya badan berbeda.

Khalros terdaftar di `_LIVE_FX_HEROES` + `_LIVE_FX_PATHS` (`heroes/__init__.py`),
jadi lane hero memakai ground layer (`draw_ground_layer`) dan live layer
(`draw_live_layer`) — sebelumnya khalros punya modul FX lengkap tapi tidak
terdaftar, sehingga layer-nya tidak pernah dipasang dan efek digambar dua kali
(renderer + director). Dalam `draw_khalros`:

```
hero_lane = hasattr(boss, "_render_scale")
live, owned = NS._live_fx(boss, surface, x, y, not hero_lane, portrait)
```

`owned` (lapisan hidup sudah mengambil alih) mematikan salinan di-canvas untuk
scorch mark, shockwave, `_manage_projectiles`, dan FX depan; telegraph gameplay
tetap digambar renderer (sama seperti razak/gorath — saat cast, key pose sprite
berubah tiap frame jadi tidak ada cache hit yang menghilangkan cincin).
Proyektil tidak pernah lahir dua kali: live OFF → 2 `AxeProjectile` dari
renderer; live ON → 0 proyektil, `KhalrosSkillFX` milik director yang menggambar
kapaknya sendiri (`test_projectiles_spawn_from_skill_window` mengunci dua-duanya).
Director juga mendaftarkan diri ke governor beban FX (`count_busy_fx_heroes`),
sehingga lapisan FX hero digambar tiap frame tanpa berkedip.

Portrait (`_portrait_hd`) membuang aura, rune lantai, FX, dan proyektil; badan
mengambil komposit yang sama, hanya tanpa lapisan lantai.

## Kompatibilitas

**57 nama publik v1 utuh** — diverifikasi dengan membandingkan
`dir()` terhadap snapshot v1, bukan dengan daftar hardcoded: 157 nama di v2,
`v1 - v2 = ∅`. Termasuk di antaranya `draw_khalros`, `draw_boss`,
`_draw_khalros_body(_raw)`, `_draw_shadow(..., lift=0)`, `_draw_shockwave`,
`AxeProjectile`, `HawkProjectile`, seluruh `_draw_*` bagian tubuh/skill, dan
primitif `_clamp/_aacircle/_aaline/_poly/_ellipse/_rect`. Registry tetap:
`bosses/_boss_index.py → "khalros": ("level2", "draw_khalros")`, shim di EOF
`bosses/level2.py`.

## Tools

- `tools/test_khalros_masterwork.py` — 28 regresi: prosedural, paritas nama v1,
  rig & ukuran keluarga, proporsi kaki + aturan cermin kapak, pixel-art
  discipline, keyframe, inersia, badan-vs-skill,
  durasi/radius vs AI, world-space, 3 tahap per skill, FX di luar badan, jendela
  shockwave, proyektil dua rezim, decal-vs-stroke, falloff, premultiply, edge
  weighting, cache decal, cache statis + batas memori, budget 3.5 ms,
  cache-miss, clamp canvas, semua mode render, hurt flash badan-saja.
- `tools/_audit_khalros_v2.py` — audit terukur (geometri, palet, waktu vs
  tetangga, telegraph diukur dari hasil-aci, kontrak) + `docs/khalros_v2_review.png`
  dan `docs/khalros_v2_before_after.png`.
- `tools/_shot_khalros_v2.py all` — lembar dokumen: `docs/khalros_v2_poses.png`,
  `_attack_strip.png`, `_skills.png`, `_halftone.png` (8 × 8 pose untuk cek palet
  dan rim light). `HALFTONE=1`, `NO_LIGHT=1` tersedia.
- `tools/_khalros_v1_snapshot.py` — blok `class _NS_khalros` v1 diambil VERBATIM
  dari `git show main:bosses/level2.py`, untuk sheet before/after + cek paritas.
- Regresi keluarga yang harus ikut hijau: `tools/test_{level2,gorath,alchemist,
  grimjaw}_masterwork.py`, `tools/test_hero_{cache,hd_render,lighting,pose_cache}.py`,
  `tools/test_boss_no_white_cover.py`.

Catatan pengukur: radius telegraph diuji dari **lumenance hasil-aci di atas lantai
gelap**, bukan dari kanal alpha — decal additive justru menyimpan cahayanya di RGB
dan meninggalkan alpha tinggi, jadi `.a` bukan ukuran jujur untuk "apa yang dilihat
pemain". Jendela sampling cincin diletakkan di sekitar pita terkuat yang
ditemukan, karena inti `_build_falloff_ring` berada di `radius + thickness + 1`
(konvensi keluarga).
