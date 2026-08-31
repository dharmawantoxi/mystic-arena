# Razak v2 — Pixel Masterwork + Skill FX

Upgrade renderer Razak (`bosses/level2.py`, namespace `_NS_razak`) ke standar
**Thorne v2 Pixel Masterwork + v2.1 Skill FX**. 100% prosedural: tidak ada PNG,
sprite-sheet, atau `pygame.image.load`. Razak = goblin penunggang kelelawar
merah dengan flamethrower — skill: Sticky Napalm (Q), Flamebreak (W), dash
Firefly (E), Firestorm (R).

## Before / after

| | v1 | v2 |
|---|---|---|
| Rig native (idle) | 81 × 54 px | **123 × 84 px** (`RIG_SCALE` 1.5×) |
| Buffer rig | 240 × 260 (jangkar 120/130) | 176 × 152 (`RIG_OX/OY` 88/92) |
| Warna unik rig | ~90 | **193** |
| Bbox di arena | ~90 × 70 | 96 × 107 (**tetap ≤ alchemist true boss 130×119**) |
| Keyframe serangan | 1 (lerp tunggal) | **7 + frame IMPACT** di `ap=0.54` |
| Telegraph skill | px canvas (menyusut) | **world-space** Q 75 / W 95 / E 80 / R 180 px dunia |
| Biaya cache-miss | ~0.9 ms | 0.8–1.0 ms pose, 1.1–2.9 ms saat skill (budget 3.5 ms) |

**Kenapa rig tidak membesar di layar.** Razak adalah mini-boss level-2:
`tools/test_level2_masterwork.py` mengunci `alchemist (true boss) ≥ razak`,
dan label + HP bar duduk relatif ke `radius`. Polanya mengikuti
`GORATH_V2_RENDERER.md`: rig di-*author* 1.5× lebih besar di resolusi native
(kepadatan detail naik), lalu ditampilkan lewat **satu** `SCALE = 0.62` yang
dipakai jalur boss, lane hero, dan portrait. Jangan memisahkan scale per
jalur — itu merusak normalisasi `_measure_native_size` di
`heroes/__init__.py`.

## Pixel-art discipline

1. **Ramp 4–6 band dengan hue-shift** — kulit goblin 6 band (bayangan
   zaitun-gelap → highlight kuning-hijau), bulu kelelawar 6 (merah-bata →
   oranye), membran sayap 4, kuningan flamethrower 5, kulit-samak 4, kain
   biru aviator 4, tulang 3, logam 4, api 7 (darkest → white).
2. **Selout** — tiap limb menaruh salinan `shadow_deep` di `(+facing, +1)`;
   komposit akhir menambah outline hitam 1 px 4 arah **setelah** penskalaan.
3. **Siluet bergerigi** — `_tuft_points` memecah bulu leher/dada kelelawar,
   telinga sobek, dan hem syal jadi zigzag deterministik; jari sayap
   meruncing ke cakar.
4. **Specular cluster** — 2–3 titik (`*_high` → `*_shine`) di tangki bahan
   bakar, laras kuningan, goggle biru, dan gigi taring; bukan satu piksel
   putih.
5. **Dither band** — `_dither_dots` di transisi perut kelelawar dan membran
   sayap.
6. **Key light kiri-atas** — konsisten dengan `lighting.LIGHT_DIR`; pass
   akhir `_lighting.apply_to_rig`.

## Anatomi & senjata

**Kelelawar**: tubuh gempal ber-bulu 6 band dengan perut terang, kepala
moncong pesek + hidung daun, dua taring bawah, telinga besar sobek-sobek,
mata oranye menyala, sayap membran 4 band dengan tulang jari terbaca +
cakar di siku, ekor ber-inersia, kaki mencengkeram saat terbang.
**Goblin rider**: kulit hijau 6 band, kepala besar bertelinga runcing,
goggle aviator biru (lensa specular), helm kulit, syal ber-inersia, gigi
menyeringai. **Gear**: flamethrower kuningan 5 band — laras ber-ring,
tabung bahan bakar ganda di punggung dengan gauge + selang, pilot flame
kecil menyala di muzzle saat idle; parang (machete) tulang-gagang di
tangan belakang untuk pose attack.

## Animasi

- **Wing-beat solver** (pengganti foot solver — Razak terbang): dua sayap
  mengepak berlawanan fase dengan membran yang melengkung mengikuti
  kecepatan kepak; bob badan dikunci ke fase kepakan supaya hover terasa
  ditopang sayap.
- **Inersia sekunder**: ekor kelelawar dan syal goblin tertinggal dari
  akselerasi badan; telinga ikut lag saat berbelok.
- **Living idle**: napas, sway, kedip goggle deterministik, pilot flame
  bergoyang, gauge bergetar.
- **Attack 7 keyframe** (`_attack_pose`): wind-up parang → tension →
  strike → **IMPACT (0.54)** → follow-through → recover, dengan smear
  sabit api 3 band (`_draw_machete_swing_arc`) dan bintang impact.
  Proyektil napalm dispawn di jendela `0.34–0.46` (guard
  `boss._razak_proj_spawned`).
- **Dash (E)**: pose membungkuk aerodinamis + 4 afterimage — satu ghost
  dirender sekali lalu di-blit 4× dengan alpha menurun (murah).

## Skill FX (3 tahap, world-space)

Semua FX dikompensasi `_fx_scale = 1/_render_scale` (cap 2.6) supaya
ukurannya **di layar** tidak menyusut bersama sprite cache; telegraph
memakai `_ring_r` yang mengubah radius dunia → px canvas. FX tanah
memakai decal ber-falloff (pola Gorath): `_ground_scorch` + `_zone_fill`
edge-weighted + `_ground_ring` gradien + `_rune_ring` berputar.

| Skill | Durasi | Aktivasi | Steady | Telegraph |
|---|---|---|---|---|
| **Q Sticky Napalm** | 40 | lob proyektil napalm (arc + trail api) | globs lengket menyala, bara berdenyut, impact splat 2 ring di 0.55–0.95 | **ring tepat 75 px dunia di TARGET** + zona gosong + rune ring + chevron masuk |
| **W Flamebreak** | 50 | muzzle core putih + kerucut api ke target | semburan kerucut 3 band bergolak + ember | **ring tepat 95 px dunia di TARGET** + retakan magma + zona edge-weighted |
| **E Firefly** | 35 | bintang hentak 8-spike saat mendarat | dashed ring berputar + ring konvergen mengecil + jejak api memudar | **ring pendaratan tepat 80 px dunia di CASTER** |
| **R Firestorm** | 90 | pilar aktivasi + shockwave ganda | **8 pilar api** mengorbit di `0.62·R`, erupsi pusat + wisp spiral | **ring AOE tepat 180 px dunia di CASTER** + rune ring + ring konvergen + retakan |

Aktivasi tiap skill juga memicu `_draw_shockwave` pada 12 frame pertama
(`age < 12`). Kolom api pilar (hot spot R) dirender lewat sprite ter-cache
`_draw_fire_pillar` (`_PILLAR_CACHE`, kunci `(height//4, width,
phase-bucket)`), bukan tumpukan `aacircle` ber-alpha per frame.

## Performa & cache

Surface statis (aura, bayangan ber-`lift`, glow radial, pilar api) dibangun
sekali lalu di-blit. Terukur (median, canvas 528×528): idle 0.84 / walk
0.83 / attack 0.96 ms; Q 1.10 / W 1.87 / E 1.79 / R 2.89 ms — semuanya di
bawah budget 3.5 ms dan hanya dibayar saat cache miss. Jalur pipeline hero
(`heroes.render_hero`) ~0.58 ms/frame.

## Kompatibilitas

Semua nama & signature publik lama dipertahankan (50 nama, diverifikasi
test): `draw_razak`, `draw_boss`, `_draw_razak_full(_raw)`,
`_draw_shadow(..., lift=0)`, `_draw_shockwave`, `NapalmProjectile`,
`NapalmPatch`, `_manage_projectiles(_no_patches)`, `_spawn_napalm`,
seluruh `_draw_*` bagian tubuh dan skill, serta primitif
`_clamp/_aacircle/_aaline/_poly/_ellipse/_rect`. Init cache tetap lazy
(`if not hasattr`) untuk `_razak_projectiles`/`_razak_patches`, dan patch
tanah di-skip saat `_skip_renderer_projectiles` (render ke cache canvas).

## Tools

- `tools/test_level2_masterwork.py` — regresi level-2 (bbox keluarga,
  flash body-only, shadow lift, durasi literal, shockwave, frame unik).
- `tools/_audit_razak_v2.py` — audit terukur + 5 preview sheet.
- `tools/test_grimjaw_masterwork.py` — paritas kosakata FX antar renderer
  v2 (razak masuk `_family_namespaces()` + 3 test khusus).
- `tools/_razak_v1_snapshot.py` — snapshot renderer v1 untuk sheet
  before/after.
- Preview: `docs/razak_v2_{review,anim_strip,ingame,skills,before_after}.png`.
