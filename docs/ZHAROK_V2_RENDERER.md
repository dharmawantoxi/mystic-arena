# Zharok v2 — Pixel Masterwork + Skill FX

Upgrade renderer Zharok (`bosses/level4.py`, namespace `_NS_zharok`) ke standar
**Thorne v2 Pixel Masterwork + v2.1 Skill FX** (lihat `docs/THORNE_V2_RENDERER.md`).
100% prosedural: tidak ada PNG, sprite-sheet, atau `pygame.image.load`.

## Before / after

| | v1 (Geometri Dasar) | v2 (Masterwork + FX v2.1) |
|---|---|---|
| Rig native (idle) | 48 × 72 px | **57 × 130 px** (`RIG_SCALE` 1.5× native) |
| Buffer rig | 200 × 200 (jangkar 100/100) | **156 × 172** (`RIG_OX/OY` 78/102) |
| Palette & Shading | Flat RGB (12 warna) | **55-swatch HD Emberborn** (4–8 band ramps) |
| Warna unik komposit | ~120 | **1178+ warna** |
| Warna portrait LOD | — | 47 warna raw + micro-detail |
| Bbox di arena | 70 × 90 px | **88 × 128 px** (family safe level-4 mini boss) |
| Keyframe serangan | 1 pose statis | **7 keyframe archery** + **frame IMPACT** di `ap=0.52` |
| Telegraph skill | px canvas statis | **World-space** Q 250 / W 200 / E 150 / R 220 px dunia |
| Visual stages skill | 1 tahap (konstan) | **3 tahap dinamis** (Aktivasi / Steady / Erupsi) |
| Proyektil kustom | Garis sederhana | **FireArrow** multi-layer + **BurningSkull** minions |
| Biaya cache-miss | ~1.5 ms | **1.4 ms** pose dasar, **1.5–3.0 ms** skill FX |

**Kenapa rig tidak membesar liar di layar.** Zharok adalah mini-boss pemanah api level-4.
Ukuran arena dikunci aman di kelas keluarga mini boss level-4 (di bawah true boss Ignis Drachorn 170×170 px).
Rig di-*author* 1.5× di resolusi native (57×130 px) untuk kerapatan pixel-art yang padat,
lalu ditampilkan lewat satu `SCALE = 0.62` yang konsisten di semua mode rendering.

## Pixel-art discipline

1. **Ramp 4–8 band dengan hue-shift**
   - *Bone Ivory (7-band)*: `bone_darkest` (32,22,16) → `bone_mid` (142,114,68) → `bone_shine` (255,246,212) & `bone_rim` (255,240,200).
   - *Hellfire (8-band)*: `fire_darkest` (48,10,8) → `fire_mid` (210,68,18) → `fire_bright` (255,124,32) → `fire_white` (255,252,220).
   - *Soulfire Core (4-band)*: `soul_dark` (160,25,10) → `soul_glow` (255,245,180).
   - *Obsidian Cloth (6-band)*: `hood_darkest` (14,8,12) → `hood_light` (148,54,52) → `hood_trim` (228,140,80).
   - *Leather (5-band)*, *Metal (6-band)*, *Gold (4-band)*, *Wood Bow (4-band)*, *Smoke/Ash (4-band)*.
2. **Selout (Selective Outlining)**
   - Tiap poligon/tulang/elemen menggambar bayangan `shadow_deep` pada offset `(+facing, +1)`.
   - Komposit akhir menambahkan outline siluet hitam 1 px di 4 arah setelah downscale.
3. **Siluet bergerigi & organik**
   - `_tuft_points` memecah jubah compang-camping (tattered hood/cape) dan lidah api helm menjadi geometri bergerigi prosedural deterministik.
4. **Specular cluster**
   - Highlight tidak berupa titik putih tunggal, melainkan cluster 2–3 piksel (`bone_high` → `bone_shine` → `bone_rim`) pada tengkorak, clavicle, dan bow limbs.
5. **Dither band**
   - `_dither_dots` pada transisi jubah obsidian dan bayangan tulang.
6. **Key light kiri-atas & Pass Pencahayaan**
   - Konsisten dengan `lighting.LIGHT_DIR`; pass akhir `_lighting.apply_to_rig(sub, rim_add=(48,22,16), shade_mul=168)`.

## Anatomi & Signature Weapons

- **Hooded Skull & Hellfire Plume**: Tengkorak kerangka bertaring dengan soket mata menyala (ember pulse), dibungkus jubah bertudung compang-camping dan mahkota lidah api bertingkat.
- **Glowing Ribcage & Heart Soulfire**: Tulang rusuk 5 lapis dengan detak bara jiwa (soulfire) berdenyut di dalam rongga dada.
- **Flaming Recurve Bow**: Stave kayu melengkung ganda dengan fitting emas kuno, bowstring api berenergi tinggi, dan pelepasan lidah api di kedua ujungnya.
- **Quiver & Hellfire Arrows**: Tempat anak panah kulit bersabuk emas di punggung dengan 3 anak panah berujung api menyala.
- **Skeleton Pelvis & Leg Solver**: Pinggul tulang dengan sabuk kulit berikat gesper emas dan kaki kerangka berknee-joint dinamis.

## Animasi Hidup (7-Keyframe Archery Timeline)

- **Living Idle**: Pernapasan rongga dada, ayunan halus kain jubah, denyut bara mata, dan wisp api melayang.
- **Walk Solver**: Foot solver kerangka dengan langkah terangkat (lift & stride) dan jejak bara di tanah.
- **Attack Pose Timeline (7 keyframes)**:
  - `ap = 0.00`: Stance bidik awal.
  - `ap = 0.20`: Tarikan busur awal (anticipation, draw = 0.6, pull = 12px).
  - `ap = 0.40`: Tarikan penuh (full draw = 1.0, pull = 20px, getaran busur).
  - `ap = 0.46`: Transisi pelepasan (release release anticipation).
  - `ap = 0.52`: **FRAME IMPACT** (lunge maksimum, smear arc busur, flash bintang 8-sudut, spawn `FireArrow`).
  - `ap = 0.70`: Recoil busur & follow-through.
  - `ap = 1.00`: Kembali ke stance netral.

## Skill FX v2.1 (World-Space, 3 Tahap Visual)

Semua skill dihitung dalam **world-space** (`_ring_r` & `_fx_scale` terkompensasi `1/_render_scale` hingga cap `2.6`):

1. **Q — Strafe (Multi-Arrow Barrage, 50f, Radius 250 px dunia)**
   - *Tahap 1 (Aktivasi)*: Shockwave tanah awal, aim laser merah-oranye ber-chevron mengarah ke posisi target.
   - *Tahap 2 (Steady / Multishot)*: Rentetan kilatan muzzle flash di busur, pelepasan berkala `FireArrow`, reticle target berputar.
   - *Tahap 3 (Telegraph / Cooloff)*: Embers dampak di target, pendinginan busur.
2. **W — Skeleton Walk (Stealth Smoke Cloak, 40f, Radius 200 px dunia)**
   - *Tahap 1 (Aktivasi)*: Ledakan shockwave debu & abu, cincin asap menyebar cepat.
   - *Tahap 2 (Steady / Ghost Veil)*: Kabut asap tebal berputar (`_rune_ring`), siluet hantu tembus pandang, wisp abu berorbit.
   - *Tahap 3 (Emergence)*: Shockwave re-materialisasi saat Zharok muncul kembali ke bentuk fisik padat.
3. **E — Death Pact (Hellfire Sacrifice / Blast, 60f, Radius 150 px dunia)**
   - *Tahap 1 (Aktivasi)*: Pentagram tanah berapi, cincin runik berkonvergensi ke arah dalam.
   - *Tahap 2 (Steady / Demon Skull)*: Tengkorak raksasa melayang di atas kastor dengan mata api menyembur dan sinar kanal jiwa.
   - *Tahap 3 (Erupsi)*: Ledakan shockwave cincin 150 px dunia, patch tanah hangus (`_ground_scorch`).
4. **R — Burning Army (Infernal Army Summoning, 80f, Radius 220 px dunia)**
   - *Tahap 1 (Aktivasi)*: Retakan tanah magma bergerigi (`_jagged_crack` 6 cabang), pilar api vertikal membubung.
   - *Tahap 2 (Steady / Summon)*: Cincin lahar 220 px dunia, pemanggilan 5 tengkorak berapi (`BurningSkull`) yang mengorbit caster.
   - *Tahap 3 (Erupsi)*: Molten scorch zone di tanah, rune api berputar pendinginan.

## Decal Engine & Performa

- Primitif ber-caching (`_DECAL_CACHE`, max 128 entri):
  - `_ground_ring`: Cincin ber-falloff halus anti cincin kawat 1 px.
  - `_zone_fill`: Area fill berbobot tepi (edge-weighted).
  - `_rune_ring`: Cincin segmen melengkung ber-taper.
  - `_ground_scorch`: Patch hangus organik dengan blob acak deterministik.
  - `_glow`: Cahaya radial lembut.
- Waktu render per frame:
  - Pose dasar: **1.4 ms**
  - Skill Q / W: **1.5 – 2.0 ms**
  - Skill E / R: **2.4 – 2.6 ms** (jauh di bawah budget 3.5 ms).

## Backwards Compatibility

100% kompatibel mundur. Semua 48 simbol dan fungsi publik `_NS_zharok` dipertahankan:
- `draw_zharok(surface, boss, x, y)`
- `draw_boss(surface, boss, x, y)`
- `FireArrow`, `BurningSkull`
- Semua helper pose (`_draw_zh_idle`, `_draw_zh_walk`, `_draw_zh_attack`, `_draw_zh_strafe`, `_draw_zh_smoke`, `_draw_zh_ecast`, `_draw_zh_rcast`)
- Semua helper anatomi (`_draw_hood_back`, `_draw_quiver`, `_draw_pelvis`, `_draw_skeleton_legs`, `_draw_ribcage`, `_draw_hooded_skull`, `_draw_flaming_bow`, dll.)

## Verifikasi & Dokumen Preview

Jalankan pengujian dan audit:
```bash
python3 tools/test_zharok_masterwork.py
python3 tools/_audit_zharok_v2.py
```

Preview sheets yang dihasilkan di folder `docs/`:
- `docs/zharok_v2_review.png` — Hero card review sheet dengan 4 panel pose & skill.
- `docs/zharok_v2_anim_strip.png` — Strip animasi Idle (8f), Walk (8f), Attack (10f).
- `docs/zharok_v2_in_game.png` — Skala dan konteks visual di battlefield arena.
- `docs/zharok_v2_skill_fx.png` — Visual 3 tahap (Aktivasi / Steady / Erupsi) untuk Q, W, E, R.
- `docs/zharok_v2_before_after.png` — Perbandingan komparatif v1 vs v2.
