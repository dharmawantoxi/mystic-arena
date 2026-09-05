# Khalros v2 — Doodle Sketch + Skill FX

Penulisan ulang total renderer Khalros (`bosses/level2.py`, namespace
`_NS_khalros`) dari pixel-masterwork lama ke **doodle sketch**. 100% prosedural:
tidak ada PNG, sprite-sheet, atau `pygame.image.load` — diverifikasi oleh test.

Alasan rewrite (permintaan pengguna): renderer pixel lama dianggap jelek. Gaya
baru = **sketsa spidol/pensil tangan**: outline hitam tebal ber-gores (wobble
sub-piksel deterministik), warna blok flat cerah, arsiran coret-coretan untuk
bayangan, proporsi kartun, latar gelap dipertahankan. Gaya ini bebas saya pilih
("Bebas, kasih yang terbaik"), dan selera pengguna menyetujui arah "rewrite
semua".

Yang TIDAK berubah (agar gameplay tetap jalan): koordinat rig lokal yang sama,
`SCALE = 0.68` tunggal untuk semua jalur, durasi/radius skill dunia
(Q70/W120/E85/R200), seluruh nama publik v1 (57), path `draw_khalros` /
`_draw_khalros_body(_raw)` / `AxeProjectile`, dan FX skill 3 tahap.

## Before / after

| | pixel v1 | doodle v2 |
|---|---|---|
| Gaya | kotak-kotak ~450 warna, ramp 4–7 band + hue-shift | **blok flat + outline spidol tebal ber-gores + hatch** |
| Outline | selout bergerigi `_tuft_points` + rim light | outline hitam 1 px empat arah (tetap, agar siluet tertutup) + **outline gores tebal per poligon** |
| Warna unik (idle, stride 2) | 452 | 1 497 (tetap kaya: blok flat per bagian) |
| Badan di layar (bbox) | 69 × 110 px | **~100 × 115 px** (tetap sekelas keluarga: razak 96×107, gorath 112×98) |
| Rig native | 92 × 157 px pada `RIG_SCALE` 1.5× | **210 × 192 px buffer** pada `RIG_SCALE` 1.5× (extent semua pose + margin) |
| Kaki | dua lidi dengan celah | **menyatu jadi dasar kokoh**: pelindung lutut, betis bulu, boot melebar |
| Keyframe serangan | 7 + IMPACT 0.54 | **tetap 7 + IMPACT 0.54** (doodle tidak membuang animasi) |
| Senjata | solver grip + bilah, pass `late=True` | solver grip + bilah, pass `late=True` di atas kepala |
| Telegraph skill | px canvas | **world-space** Q 70 / W 120 / E 85 / R 200 px dunia |
| FX tanah | decal ber-falloff | **tetap decal ber-falloff** (`_ground_scorch` + `_zone_fill` + `_ground_ring` + `_rune_ring`) |
| Biaya idle / R (steady) | 1.13 / 1.11 ms | **0.40 / 1.94 ms** (budget keluarga 3.5 ms; jauh lebih cepat karena pose-cache) |
| Pose cache | tidak ada | **LRU 48 per kuantum pose** (idiom `_NS_alchemist`) |

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

## Doodle discipline

Primitif sketsa ada di `_NS_khalros` (sekitar baris 5610–5714):

| Primitif | Fungsi |
| --- | --- |
| `_dl_jit(i, seed)` | jitter deterministik −1..1 (`math.sin` hash) untuk goresan tangan yang stabil antar frame |
| `_doodle_seg` | satu garis spidol ber-gores (beberapa sub-segmen offset) |
| `_doodle_line` | polyline spidol tebal; subdivisi + jitter dihitung sekali lalu **satu `pygame.draw.lines`** (bukan ratusan `draw.line`) |
| `_doodle_poly` | poligon doodle: isi flat + outline spidol tebal ber-gores |
| `_doodle_inside` | ray-cast point-in-polygon (untuk hatch) |
| `_doodle_hatch` | arsiran coret-coretan diagonal di dalam poligon (titik acak deterministik) |
| `_doodle_dot` | marker titik spidol |

Aturan yang dipakai:

1. **Blok flat, bukan ramp.** Setiap bagian memakai 1–2 warna dasar + satu warna
   gelap untuk tepi bawah. Tidak ada `_lighting.apply_to_rig` (pass cahaya
   pixel-art **dimatikan** di `_compose_body`) supaya warna tetap flat — komentar
   di sana menjelaskan: "doodle keeps flat colors". `_doodle_poly` mengisi
   `pygame.draw.polygon` dengan warna penuh lalu menimpa outline gores.
2. **Outline spidol ber-gores.** `_doodle_line`/`_doodle_poly` memakai `wobble`
   (0.9–1.2) dan `seed` per bagian sehingga tiap garis "bergetar" halus seperti
   digambar tangan — tapi deterministik, jadi tidak berkedip antar frame.
3. **Arsiran = bayangan.** `_doodle_hatch` mengisi bagian bawah (perut, paha,
   jubah, cawat) dengan coret-coretan diagonal warna gelap, bukan gradasi.
4. **Outline 1 px tetap.** `_compose_body` memproduksi `edge` (salinan `sub`
   yang di-`BLEND_RGBA_MULT` jadi hitam) dan `_draw_khalros_body` men-blit 4×
   di sekitar untuk siluet tertutup — konvensi keluarga dipertahankan.
5. **Warna tetap hidup di atas latar gelap.** Palet doodle memakai warna cerah
   (kulit, baja, api, emas) yang kontras dengan `bg` karakter `(24,21,28)`.
6. **Hatch diperhalus untuk biaya.** `_doodle_hatch` memakai `step = max(4,…)`
   dan 12 sampel per garis miring — dikunci agar doodle tidak melebihi budget.

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

Terukur di mesin ini, canvas 528 × 528, frame **steady** (state konst, cache
hangat), median 5 × 25 frame:

| | idle | Q | W | E | R |
|---|---|---|---|---|---|
| khalros doodle v2 | **0.40** | **0.63** | **1.10** | **1.07** | **1.94** |
| gorath v2 (pembanding) | 1.52–1.58 | 1.86–2.01 | 2.44 | 1.95–2.07 | 2.72–2.80 |

Semua jauh di bawah budget 3.5 ms. Cast penuh R **hangat** (median warm) di mesin
ini: khalros **3.56 ms** — setara razak (3.53) dan lebih cepat dari gorath
(3.85). Frame **cache-miss penuh** (semua cache dibersihkan, R aktif,
`_render_scale = 0.72`) ~26 ms (frame pertama membangun semua decal), lalu frame
build decal transien 12–16 ms (masih di bawah 1 frame 60 fps = 16.6 ms), dan
frame steady jatuh ke 2–4 ms.

Keputusan yang membuat angka itu mungkin:

- **Pose LRU cache di `_compose_body`** (idiom `_NS_alchemist`). Key =
  `(action, facing-sign, _pose_bucket(action, phase, ap), rage)`. Untuk `attack`
  bucket dihitung dari `attack_progress` SAJA (29 step), sehingga saat cast R
  yang memegang `ap = 0` konstan, key-nya SAMA tiap frame → komposit doodle yang
  berat (subdivisi + jitter + hatch) tidak dirender ulang. Cast R turun dari
  ~5.7 ms ke **3.56 ms warm**. LRU `_POSE_CACHE_MAX = 48`.
- **`_doodle_line` satu `pygame.draw.lines`.** Dulu tiap polyline memanggil
  ratusan `pygame.draw.line` (per sub-segmen). Sekarang subdivisi + jitter
  dihitung sekali lalu digambar dalam SATU panggilan `lines` — tampilan goresan
  tangan sama, biaya jauh lebih murah.
- **`_compose_body` sekali render.** `_draw_khalros_charge` merender rig sekali
  lalu men-blit 4× (afterimage) + 1× (badan) — E tidak dua kali lebih mahal.
- **Hasil rotasi TIDAK di-cache.** `_rune_ring` hanya meng-cache decal dasarnya;
  rotasi via `transform.rotate` per frame. Dikunci
  `test_surface_cache_memory_is_bounded` (batas 8 MB).
- **Satu rune ring untuk R.** Cincin angin dalam memakai `_dashed_ring` (stroke
  berfasa) supaya tidak menambah `rotate` kedua yang mahal.

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
  rig & ukuran keluarga, proporsi kaki + aturan cermin kapak, **doodle discipline**
  (`_doodle_poly` + ≥8 warna flat), keyframe, inersia, badan-vs-skill,
  durasi/radius vs AI, world-space, 3 tahap per skill, FX di luar badan, jendela
  shockwave, proyektil dua rezim, decal-vs-stroke, falloff, premultiply, edge
  weighting, cache decal, cache statis + batas memori, budget 3.5 ms,
  cache-miss, clamp canvas, semua mode render, hurt flash badan-saja.
- `tools/_patch_doodle_khalros.py` — patch idempoten: sisipkan primitif doodle
  (`_doodle_*`) + ganti `_draw_khalros_body_raw`. Idempoten via `_DL_HATCH`.
- `tools/_patch_doodle_anatomy.py` — patch idempoten: ganti cape/hawk/legs/
  loincloth/torso/shoulders/head/helm. Idempoten via `_DOODLE_FLAG_TORSO`.
- `tools/_patch_doodle_arms.py` — patch idempoten: ganti arm/axe. Idempoten via
  `_DOODLE_FLAG_ARMS`.
- `tools/_shot_khalros_v2.py all` — lembar dokumen: `docs/khalros_v2_poses.png`,
  `_attack_strip.png`, `_skills.png`, `_halftone.png` (8 × 8 pose untuk cek palet).
  `HALFTONE=1`, `NO_LIGHT=1` tersedia.
- `tools/_khalros_v1_snapshot.py` — blok `class _NS_khalros` v1 diambil VERBATIM
  dari `git show main:bosses/level2.py`, untuk sheet before/after + cek paritas.
- `docs/_doodle_crop.png` — crop zoom 4× (6 sel: idle/walk/attack/facing) untuk
  review visual cepat gaya doodle.
- Regresi keluarga yang harus ikut hijau: `tools/test_{level2,gorath,alchemist,
  grimjaw}_masterwork.py`, `tools/test_hero_{cache,hd_render,lighting,pose_cache}.py`,
  `tools/test_boss_no_white_cover.py`.

Catatan pengukur: radius telegraph diuji dari **lumenance hasil-aci di atas lantai
gelap**, bukan dari kanal alpha — decal additive justru menyimpan cahayanya di RGB
dan meninggalkan alpha tinggi, jadi `.a` bukan ukuran jujur untuk "apa yang dilihat
pemain". Jendela sampling cincin diletakkan di sekitar pita terkuat yang
ditemukan, karena inti `_build_falloff_ring` berada di `radius + thickness + 1`
(konvensi keluarga).
