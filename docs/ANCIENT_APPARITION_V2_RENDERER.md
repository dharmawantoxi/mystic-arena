# Ancient Apparition v2 — Pixel Masterwork + Skill FX

Upgrade renderer Ancient Apparition (`bosses/level3.py`, namespace `_NS_ancient_apparition`, dialiaskan di `heroes/_bundle.py` sebagai `_NS_ancient_apparition` / `_NS_ancientapparition`) ke standar **Thorne v2 Pixel Masterwork + v2.1 Skill FX**. 100% prosedural: tanpa PNG, sprite-sheet, atau `pygame.image.load`.

## Before / after

| | v1 | v2 |
|---|---|---|
| Rig native (idle) | 68 × 82 px | **83 × 128 px** (`RIG_SCALE` 1.5×) |
| Warna unik arena / portrait LOD | 22 / — | **120 / 181** |
| Bbox di arena | 100 × 110 px | **130 × 140 px** (`SCALE = 0.68`) |
| Keyframe serangan | 1 (lerp tunggal) | **Multi-keyframe + IMPACT flare** di `ap=0.44` |
| Telegraph skill | px canvas biasa | **world-space** Q 80 / W 65 / E 70 / R 80 px dunia |
| Visual Skill FX | 1 tahap statis | **3 tahap dinamis** (Aktivasi / Steady / Dissipation & Erupsi) |
| Biaya cache-miss | ~2.3 ms | **1.3–2.1 ms** pose dasar, **2.5–3.2 ms** skill (budget 3.5 ms) |

**Desain Skala Rig & Auto-Normalisasi:** Ancient Apparition adalah True Boss Level-3 sekaligus Playable Hero. Rig di-*author* 1.5× lebih besar di resolusi native untuk memaksimalkan kepadatan detail kristal dan facet es kosmik, lalu diintegrasikan lewat satu konstanta `SCALE = 0.68` yang konsisten untuk semua jalur rendering (boss, hero lane, portrait).

## Pixel-art Discipline

1. **Ramp 5-Band dengan Hue-Shift Kosmik** — Es primordial 6 band (shadow deep `(2,5,12)` → void deep `(4,8,22)` → ice dark `(22,48,96)` → ice mid `(55,110,180)` → cyan bright `(200,245,255)` → ice pure `(255,255,255)`).
2. **Selout** — Setiap kristal, stalaktit, dan cakar menaruh salinan bayangan `shadow_deep` tergeser `(+facing, +1)` untuk keterbacaan siluet tinggi di atas background terrain apa pun.
3. **Siluet Bergerigi & Kristal Tajam** — `_draw_ice_shard`, `_draw_frost_crystal_spike`, `_spark_star`, `_tuft_points`, dan `_jagged_crack` memberikan tepi es permafrost yang tajam dan dinamis.
4. **Specular Clusters** — Kilau intan dan kristal es di ujung tanduk mahkota, tulang lengan, cakar, dan inti kosmik.
5. **Dither Lattice** — Tekstur dither klasik pixel-art (`_dither_dots`) pada transisi bayangan skirt es dan kristal tubuh.
6. **Top-Left Key Light & Rim Pass** — Konsisten dengan `lighting.LIGHT_DIR` menggunakan pass komposit `_composite_boss_body` dengan `rim_add=(150, 225, 255)`.

## Anatomi & Identitas Visual

- **Mahkota Kristal Kosmik (Ice Crown)**: 5 tanduk kristal es berjenjang dengan apex spike tertinggi dan intan mengambang berdenyut di atas kepala.
- **Wajah Hantu Kosmik (Void Cowl & Ghostly Face)**: Cowl es berongga dengan mata biru menyala dan kabut dingin halus yang berdenyut misterius.
- **Inti Primordial (Primordial Core)**: Inti pusaran energi kosmik di dalam dada kristal berlapis, memancarkan gelombang cahaya cyan terang.
- **Rok Stalaktit Es (Ice Skirt)**: 7 bilah stalaktit es bergoyang mengikuti inersia melayang, dihiasi dither lattice dan retakan permafrost.
- **Satelit Kristal Orbit (Orbital Shards)**: 4 kristal intan melayang yang berputar mengelilingi badan dalam bidang 3D (2 di layer belakang, 2 di layer depan).
- **Lengan & Cakar Es (Ice Claws)**: Tulang lengan kristal beruas dengan 3 cakar tajam bercahaya.

## Animasi Living Rig

- **Footless / Floating Inertia**: Entitas tanpa kaki yang melayang bebas dengan secondary sway pada rok es, mahkota, satelit orbit, dan cakar.
- **Living Idle**: Denyut inti kosmik, partikel salju melayang, dan kabut es lembut yang naik dari tanah.
- **Multi-Keyframe Attack**: Windup kosmik, arm thrust dengan smear kristal es, frame IMPACT pada `ap=0.44` dengan ledakan spark star, dan recovery halus.
- **Casting Stances**: Pose channeling kosmik dengan kedua lengan terangkat dan pendaran aura es intens.

## Skill FX Mewah (World-Space, 3 Tahap)

Semua efek skill Ancient Apparition diskalakan dengan `_fx_scale(boss)` (kompensasi `1/_render_scale` dengan cap 2.6) sehingga selalu terlihat megah dan proporsional di layar permainan:

1. **Skill Q: Ice Vortex (Durasi 60 frame, Radius 80 px dunia)**:
   - *Aktivasi*: Telegraph tanah melingkar (radius 80 px) dengan rune es berputar dan chevron konvergen.
   - *Steady*: Tornado badai salju 3D berputar kencang dengan partikel kristal dan orbit snowflake.
   - *Dissipation*: Kabut es permafrost memudar dengan serpihan salju yang tersebar.
2. **Skill W: Frost Beam / Chilling Touch (Durasi 45 frame, Radius 65 px dunia)**:
   - *Aktivasi*: Pengumpulan energi es di tangan caster dengan orb bercahaya dan garis bidik laser ke target.
   - *Steady*: Laser es glasial berkekuatan penuh dengan multi-layer beam, gelombang kejut heliks, dan ledakan benturan di target.
   - *Dissipation*: Sinar terurai menjadi serpihan kristal dan kabut es beku yang tersisa di tanah.
3. **Skill E: Ice Bolt / Shard Barrage (Durasi 50 frame, Radius 70 px dunia)**:
   - *Aktivasi*: Barisan kristal es glasial melayang berjejer di belakang caster sambil mengisi daya.
   - *Steady*: Rentetan proyektil intan es raksasa melesat cepat ke target dengan cincin sonik dan jejak partikel es.
   - *Dissipation*: Ledakan pecah kristal es di target dengan serpihan yang terpental radial dan membeku di tanah.
4. **Skill R: Cold Feet / Glacial Cataclysm (Durasi 90 frame, Radius 80 px dunia)**:
   - *Aktivasi*: Telegraph peringatan tanah berputar ganda dengan retakan es bergerigi tajam.
   - *Steady*: Letusan 12 menara kristal es raksasa melingkar di sekeliling target bersama monolit glasial raksasa di pusat dan ledakan starburst di puncak.
   - *Dissipation*: Menara es retak menjadi pecahan mengambang dan kabut uap permafrost pekat.

## Hasil Validasi & Audit

Semua unit test dan pengujian regresi lulus 100%:
- `tools/test_hero_lighting.py`: PASS
- `tools/test_hero_hd_render.py`: PASS
- `tools/test_swing_anim.py`: PASS
- `tools/test_renderer_projectiles_not_baked.py`: PASS
- `tools/test_grimjaw_masterwork.py`: PASS
- `tools/test_level3_masterwork.py`: PASS
- `tools/_audit_ancient_apparition_v2.py`: PASS (Semua metrik audit rig, warna, performa, dan telegraph world-space tervalidasi)

### Lembar Dokumentasi Visual (`docs/`)
- `ancient_apparition_v2_review.png` — Kartu pose besar (Idle, Walk, Attack, Cold Feet Ult).
- `ancient_apparition_v2_anim_strip.png` — Film strip siklus animasi prosedural.
- `ancient_apparition_v2_ingame.png` — Render ukuran aktual di arena gameplay.
- `ancient_apparition_v2_skills.png` — Rincian 4 skill (Q/W/E/R) dalam 3 tahap visual.
- `ancient_apparition_v2_before_after.png` — Perbandingan komparatif v1 vs v2.
