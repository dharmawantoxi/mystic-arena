# Zharok v3 — Renderer + Combat FX & Game Feel (100% prosedural)

> Rewrite penuh sistem **visual dan rasa tempur** untuk **ZHAROK — The
> Emberborn Archer** (mini-boss level 4 + hero yang bisa dibuka,
> `bosses/level4.py :: _NS_zharok`). Tetap **100% prosedural**: tidak ada
> PNG / JPG / GIF / sprite-sheet / aset eksternal dan tidak ada
> `pygame.image.load`. Semua bentuk dibangun dari `pygame.Surface`,
> `pygame.draw`, `pygame.transform`, `Rect`, dan `Vector2`.
>
> Dokumen ini memaparkan renderer (rig, palet, pose, controller animasi)
> **dan** sistem tempurnya (sabetan, trail, proyektil, skill FX, impact,
> hit-stop, screen shake, debug). Polanya sengaja mengikuti
> [`IGNIS_DRACHORN_V3_COMBAT_FX.md`](IGNIS_DRACHORN_V3_COMBAT_FX.md) dan
> menumpang di atas [`ZHAROK_V2_RENDERER.md`](ZHAROK_V2_RENDERER.md) — v3
> **tidak membuang** v2, ia membungkusnya.

---

## 1. Masalah yang sebenarnya

Zharok v2 sudah punya rig pixel-art yang bagus (55-swatch palette, timeline
archery 7-keyframe, FX skill world-space). Yang belum ada justru lapisan di
sekitarnya:

1. **Semua efek hidup di dalam canvas badan.** Di lane hero, badan
   di-*cache* lalu di-`smoothscale`. Anak panah, bara, dan FX skill yang
   digambar ke canvas yang sama ikut **beku** dan ikut **menyusut**.
2. **Tidak ada controller animasi.** Pose dipilih dari `if` bertingkat atas
   `timer` / `active_skill`. Tidak ada nama state, prioritas, fase serangan,
   atau delta time — tidak ada satu tempat pun yang bisa ditanya *"sekarang
   frame berapa, fase apa, boleh kena tidak"*.
3. **Zharok tidak punya jawaban untuk musuh yang menempel.** Sebagai
   pemanah murni ia tetap menembak dari jarak 5 px. Tidak ada sabetan,
   jadi tidak ada ARC, tidak ada trail senjata.
4. **Tidak ada game feel.** Damage instan: tanpa hit-stop, tanpa shake
   terarah, tanpa impact flash. Panah 400 damage terasa sama dengan 12.
5. **Proyektil v2 bulat polos.** `FireArrow` menggambar lingkaran + garis;
   tidak ada inti, glow, sirip, rotasi, atau partikel jejak.

## 2. Pemecahan: pisahkan badan dari efek

| Lapisan | File | Memiliki |
|---|---|---|
| **Renderer (badan + telegraph + fallback)** | `bosses/level4.py :: _NS_zharok` | rig, palet, pose, **controller animasi**, ARC stave busur, bayangan, aura api, rune tanah, **seluruh fallback canvas v2** saat modul FX absen |
| **Lapisan hidup 1:1** | `heroes/zharok_fx.py` (baru, ±3.4k baris) | swing trail, particle system, proyektil Fire Arrow & Soul Skull, impact FX, skill FX q/w/e/r, afterimage, overlay debug — semuanya di **ruang layar**, skala 1.0 |
| **Bus game feel (dipakai bersama)** | `heroes/combat_feel.py` (sudah ada) | hit-stop global, screen shake, delta-time frame |

Kenapa pembagian ini penting:

* lapisan hidup digambar **di luar** sprite cache → 60 fps sejati, tidak
  pernah beku dan tidak pernah ikut menyusut;
* renderer tetap **satu-satunya pemilik geometri badan**. Lapisan hidup
  tidak menghitung ulang pose — ia **membaca** `bow_geometry()`,
  `_bow_arc()`, `_zh_state`, `_zh_attack_progress` lewat jembatan malas
  `_renderer()`. Stave dan trail tidak mungkin berbeda satu frame pun;
* kalau `heroes.zharok_fx` gagal diimpor, `owns()` bernilai False dan
  renderer menggambar semuanya sendiri — visual kehilangan polish,
  **tidak pernah** kehilangan efek.

### 2.1 Pengaman `recently_drawn()`

Di lane hero, yang memanggil `draw_ground_layer` / `draw_live_layer` adalah
pipeline `heroes/__init__.py`, **bukan** renderer. Kalau renderer dipanggil
langsung (alat uji, integrasi lain, potret), tidak ada yang menggambar
lapisan hidup — dan mematikan fallback canvas di situ berarti karakter
kehilangan seluruh FX-nya **diam-diam**.

```python
# bosses/level4.py :: _NS_zharok._live_fx
owned = bool(mod.owns(boss))
if owned and not want_draw:
    owned = bool(mod.recently_drawn(boss))   # ada yang menggambarnya?
```

`recently_drawn(unit, max_age=0.35)` True hanya kalau director punya posisi
layar dan `draw_age <= max_age`. Dikunci oleh
`test_canvas_fallback_when_nobody_draws_live_layer`.

## 3. Render order

**Per karakter** (dipakai apa adanya di kedua jalur):

```
bayangan → tungkai belakang → panggul → tulang rusuk → jubah → tengkorak
        → stave busur → tungkai depan → highlight pixel
        → attack FX (trail, muzzle flash) → skill FX → partikel
```

**Global** (satu frame arena):

```
ground → ground FX (draw_ground_layer) → bayangan → partikel belakang
       → badan → partikel depan → proyektil → impact FX
       → live layer (draw_live_layer) → damage text → UI
```

`draw_ground_layer` dipanggil **sebelum** sprite, `draw_live_layer`
**sesudah** — itulah kenapa telegraph tanah tidak pernah menutupi badan dan
trail selalu di atasnya.

## 4. Controller animasi (`_NS_zharok._update_zharok_anim`)

Satu-satunya sumber kebenaran state/fase/timing. Lapisan hidup, overlay
debug, dan alat uji semuanya membacanya dari sini.

| State | Prioritas | Pemicu |
|---|---|---|
| `IDLE` | 0 | diam |
| `WALK` | 10 | bergerak, `_zh_speed <= 1.6` |
| `RUN` | 15 | bergerak, `_zh_speed > 1.6` |
| `CHARGE` | 30 | serangan aktif, `progress < 0.12` |
| `CAST` | 35 | membidik (jarak jauh), `0.30 <= progress < 0.62` |
| `ATTACK` | 40 | serangan aktif, sisa timeline |
| `SWING` | 45 | Ember Cleave (jarak dekat), `progress < 0.62` |
| `SKILL` | 50 | `active_skill in (q, w, e)` |
| `SPECIAL` | 55 | `active_skill == "r"` |
| `HIT` | 60 | cadangan (dipakai lapisan FX) |
| `HURT` | 65 | `hurt_flash_timer > 0` |
| `DEATH` | 100 | `alive == False` — mengunci semuanya |

**Delta time nyata** diambil dari `pygame.time.get_ticks()` dan dijepit ke
`(0, 0.05]` s; frame yang melonjak (loading, alt-tab) jatuh balik ke 1/60
supaya animasi tidak pernah teleport.

**Timeline serangan** dibaca dari `timer` engine yang menghitung **mundur**:
lonjakan naik = serangan baru. Progres dinormalkan ke `anim_len =
clamp(cooldown-1, 10, 30)` frame sehingga tarikan busur tetap punya bobot
walau cooldown-nya panjang.

| Fase | Rentang | Isi |
|---|---|---|
| `ANTICIPATION` | 0.00–0.12 | badan turun, stave ditarik ke belakang |
| `WINDUP` | 0.12–0.30 | tali ditarik / stave diangkat tinggi |
| `SWING` | 0.30–0.50 | sapuan / bidikan mengunci |
| `IMPACT` | 0.50–0.62 | **frame kena** di `0.52` |
| `FOLLOW` | 0.62–0.82 | overshoot, kain tertinggal |
| `RECOVERY` | 0.82–1.00 | kembali ke garda |

`ATTACK_ACTIVE_WINDOW = (0.38, 0.62)`, `ATTACK_IMPACT_FRAME = 0.52` —
angka `0.52` sengaja dipertahankan dari timeline archery v2
(`_attack_pose` memuncak tepat di sana), jadi v2 dan v3 kena di frame yang
sama. Tabel ini **identik** di renderer dan di `zharok_fx`
(`assert F.ATTACK_PHASES == NS.ATTACK_PHASES`).

## 5. Melee: Ember Cleave — ARC stave busur

Zharok v3 punya jawaban jarak dekat. Satu ambang, satu angka:

```python
MELEE_REACH = 74.0     # px dunia; sama di zharok_fx, _NS_zharok, base_boss
```

Di bawah ambang ia **menyabet dengan badan busur** (`action="melee"`,
`_zh_melee_swing = True`); di atasnya ia menembak. `base_boss` memakai
angka yang sama untuk memilih `notify_melee_impact` vs
`notify_projectile_impact`, jadi animasi dan damage tidak pernah beda
pendapat.

`BOW_ARC` — (t0, t1, theta0, theta1, ease). `theta` = sudut stave dari
sumbu **atas** (rad):

| Fase | t | theta | Ease |
|---|---|---|---|
| ANTICIPATION | 0.00–0.12 | 2.30 → 1.92 | `out` |
| WIND-UP | 0.12–0.30 | 1.92 → −1.16 | `io` |
| SWING | 0.30–0.50 | −1.16 → 1.74 | `oc` |
| IMPACT | 0.50–0.62 | 1.74 → 2.06 | `hold` |
| FOLLOW THROUGH | 0.62–0.82 | 2.06 → 2.64 | `io` |
| RECOVERY | 0.82–1.00 | 2.64 → 2.30 | `io` |

Loop tertutup (`theta(0) == theta(1)`) dan **langkah maksimum < 0.30 rad**
per 1/200 progres — senjata tidak pernah teleport. Dikunci oleh
`test_bow_arc_continuity`.

### 5.1 Satu sumber geometri senjata

```python
grip, tip_hi, tip_lo, theta = NS.bow_geometry(facing, action, phase, ap)
```

Mengembalikan offset **ruang layar** (sudah dikali `SCALE = 0.62`) relatif
jangkar badan. Renderer memakainya untuk menggambar stave; `zharok_fx`
memakainya lewat `bow_points()` untuk trail dan titik lahir proyektil.
Panjang stave konstan `2 * STAVE_HALF * SCALE` di **semua** pose, grip
selalu tepat di tengah kedua limb, dan facing `-1` adalah cermin sempurna
dari facing `+1` — ketiganya dikunci oleh `test_bow_geometry_single_source`.

Trail (`SwingTrail`, `TRAIL_SAMPLES = 10`) merekam histori posisi tip stave
lalu menggambarnya sebagai poligon translucent + arc memudar + partikel
pixel. Ia **meluruh sendiri**: 180 frame tanpa sabetan → `history` kosong.

## 6. Projectile system (modular)

`BaseProjectile` memenuhi kontrak penuh: `position`, `velocity`, `speed`,
`damage`, `lifetime`, `target`, `radius`, `rotation`, `trail`, `particles`,
`active` — `position`/`velocity` benar-benar `pygame.Vector2`, dan semua
integrasi memakai delta time.

Lifecycle: **SPAWN → TRAVEL → TRAIL → HIT → IMPACT FX → DESTROY.**

| Kelas | Dipakai | Kecepatan | Bentuk |
|---|---|---|---|
| `FireArrowProjectile` | serangan dasar, voli Q | 760 / 840 px/s | inti putih-panas + glow beranulus + kepala runcing + sirip + rotasi mengikuti kecepatan + trail bara |
| `SoulSkullProjectile` | R (Burning Army) | 310 px/s | tengkorak chunky + soket menyala + ekor jiwa berombak + partikel abu |

Keduanya **bukan lingkaran polos**: `test_arrow_is_not_a_plain_circle`
menembak dua panah ke arah tegak lurus dan menuntut siluetnya berbeda
(dan memanjang), serta `rotation`-nya mengikuti arah terbang.

Cap keras `MAX_PROJECTILES = 22`; yang tertua dibuang lebih dulu.

## 7. Skill FX (`SkillFX`) — lifecycle penuh

| Fase | t | Isi |
|---|---|---|
| `CAST` | 0.00–0.16 | tanda mula, tarikan energi ke kaster |
| `CHARGE` | 0.16–0.34 | pengisian, getaran, telegraph tumbuh |
| `RELEASE` | 0.34–0.46 | pelepasan + flash |
| `AREA` | 0.46–0.74 | efek area / perjalanan |
| `IMPACT` | 0.74–0.86 | benturan, shockwave, serpihan |
| `AFTER` | 0.86–1.00 | asap & bara sisa, memudar habis |

| Skill | Nama | Radius dunia | Bentuk (sengaja **tidak** semuanya lingkaran) |
|---|---|---|---|
| Q | Strafe | 250 | koridor bidik **meruncing** + chevron maju + reticle kurung siku + voli 6 panah |
| W | Skeleton Walk | 200 | kolam asap ungu + cincin arc + hantu tulang |
| E | Death Pact | 150 | **pentagram** + tengkorak melayang + berkas jiwa |
| R | Burning Army | 220 | retakan magma **bergerigi** + pilar api + kolom cahaya + 5 tengkorak jiwa |

Radius dan durasi **sama persis** dengan gameplay:
`WORLD_RADIUS == {q:250, w:200, e:150, r:220}` dan
`SKILL_DUR == {q:50, w:40, e:60, r:80}` frame, cocok dengan
`base_boss._cast_zharok_*` maupun `_NS_zharok.SKILL_RADIUS`.

### 7.1 Telegraph AoE HARUS lingkaran

Elips perspektif itu cantik, tapi radius damage E dan R adalah **lingkaran
di ruang dunia** — pemain membaca jangkauannya dari cincin itu. Jadi
`_gnd_e` dan `_gnd_r` selalu menggambar `ring_surface()` **lingkaran penuh**
di radius dunia yang tepat; pentagram, retakan, dan elips hanya dekorasi di
atasnya. Dikunci dua kali: `test_aoe_telegraph_is_a_true_circle` (v3) dan
`test_skill_telegraph_radius_is_exact` (v2, sampling 180 arah).

### 7.2 Progres dikunci ke timer engine

Tes v2 me-render **satu frame terisolasi** pada `active_skill_timer`
tertentu. Kalau progres FX hanya menumpuk `dt`, `age ≈ 0` → radius 0 →
telegraph hilang. Karena itu `ZharokFXDirector.sync()` memaksa:

```python
prog = 1.0 - active_skill_timer / SKILL_DUR[key]
skill_fx.set_engine_progress(prog)      # melompat maju, tidak pernah mundur
```

`set_engine_progress` memetakan progres engine ke `ENGINE_SPAN = 0.86` dari
total lifecycle, jadi tahap `AFTER` tetap punya ruang untuk memudar setelah
pose skill selesai. Dikunci oleh `test_engine_progress_drives_skill_fx`.

## 8. Particle system

`Particle` menyimpan `position`, `velocity`, `acceleration`, `life`,
`max_life`, `size`, `rotation`, `rotation_speed`, `alpha`, `gravity`,
`color` (+ `drag`, `shape`, `layer`, `additive`, `scatter`).

Penyimpanan internalnya **skalar ber-`__slots__`** dan properti
`position`/`velocity`/`acceleration` mengembalikan `Vector2` sesuai
kontrak — pool 200 partikel jauh lebih murah tanpa ratusan objek `Vector2`
baru per frame di jalur update yang panas.

`ParticleSystem` memakai **pool tetap dengan kursor melingkar**: runtime
tidak pernah mengalokasi partikel baru, yang tertua dipakai ulang. Jadi
`MAX_PARTICLES = 200` adalah batas keras yang mustahil dilanggar.

`burst(x, y, count, direction=, spread=, speed=, life=, size=, colors=,
gravity=, drag=, shape=, rotation_speed=, scatter=, lift=)` menangani
semua ledakan terarah dalam satu panggilan. Bentuk yang tersedia: `ember`,
`streak`, `flame`, `smoke`, `bone`, `debris`, `dust`, `spark`, `ring`,
`rune`, `skullbit`.

## 9. Impact & game feel

| Kejadian | Hit-stop | Shake | Visual |
|---|---|---|---|
| Ember Cleave mendarat | 0.045 s (crit 0.06) | 6 / 0.20 s | flash bintang, sabit api, serpihan tulang + bara |
| Panah mendarat | 0.03 s | 3 / 0.14 s | flash kecil, percikan bara terarah |
| Q Strafe | 0.035 s | 8 / 0.22 s | flash koridor, debu |
| E Death Pact | 0.05 s | 12 / 0.28 s | nova jiwa + shockwave |
| R Burning Army | 0.06 s | 18 / 0.40 s | kolom cahaya + shockwave ganda |

Semuanya lewat `heroes/combat_feel.py`, yang **menjepit** hit-stop ke
0.03–0.08 s (`HIT_STOP_MIN`/`MAX`, maksimum 5 langkah simulasi) dan
meluruhkan shake berbasis trauma. Impact flash memakai `Surface` transparan
terpisah, bukan `fill` ke layar.

## 10. Catatan teknis: `BLEND_RGB_ADD` mengabaikan alpha

```python
# SALAH — alpha per-piksel diabaikan, gradien jadi cakram warna penuh
surface.blit(glow_rgba, pos, special_flags=pygame.BLEND_RGB_ADD)

# BENAR — premultiply dulu: blit normal ke atas hitam, baru ditambahkan
buf = _opaque(w, h)            # surface hitam dari pool
buf.blit(glow_rgba, (0, 0))
surface.blit(buf, pos, special_flags=pygame.BLEND_RGB_ADD)
```

Itulah tugas `blit_add()` / `_blit_faded()` di §4 modul FX. Semua dekal
radial juga dibangun dari **anulus**, bukan tumpukan cakram, supaya tepinya
tetap pixel-art dan tidak menelan karakter.

### 10.1 Renderer kanvas v2 kena jebakan yang sama

`_NS_zharok._blit_decal` di `bosses/level4.py` — jalur cadangan yang dipakai
saat lapisan hero tidak aktif (potret, preview, unit yang tidak ter-*attach*)
— menambahkan dekal mentah persis seperti baris "SALAH" di atas. Akibatnya
aura api Zharok tampil sebagai **cakram oranye pekat bertepi keras** yang
menelan siluetnya, dan telegraf AoE kehilangan gradiennya.

Dua sifat pygame yang menjebak di sini:

| Sifat | Akibat |
| --- | --- |
| `BLEND_RGB_ADD`/`BLEND_RGBA_ADD` menambah kanal warna **tanpa melihat alpha** | gradien jadi cakram penuh bertepi keras |
| `Surface.set_alpha()` **diabaikan** oleh blit ber-`special_flags` | peredupan pada mode add tidak pernah terjadi |

Perbaikannya menghindari lintasan per-frame sama sekali. Karena fungsi
`pygame.draw.*` **menimpa** piksel (bukan mem-blend), premultiply dan
peredupan bisa dipanggang langsung ke dalam warna yang digambar builder:

```python
@staticmethod
def _pmc(col, a, pm, k=255):        # premultiplied color
    if k < 255:                     # k = peredupan, ikut dipanggang
        a = a * k / 255.0
    a = max(0, min(255, int(a)))
    if not pm:
        return (col[0], col[1], col[2], a)
    return (col[0] * a // 255, col[1] * a // 255, col[2] * a // 255, a)
```

`add` dan tingkat peredupan (`_fade_level`, 8 langkah) ikut jadi bagian kunci
cache dekal, jadi satu dekal dibangun sekali lalu dipakai apa adanya:

```python
surface.blit(decal, pos, special_flags=pygame.BLEND_RGBA_ADD)   # 0.07 ms
```

Hasil builder ber-`pm` terbukti identik dengan `surface.premul_alpha()`
(selisih maksimum 1/255, murni pembulatan integer) tetapi **tanpa lintasan
tambahan pada jalur cache-miss** — jalur yang justru diukur audit v2.

Pendekatan yang dicoba lalu dibuang, semuanya karena biaya per-frame pada
dekal 528×528:

| Cara | Biaya | Vonis |
| --- | --- | --- |
| `fill(color, BLEND_RGBA_MULT)` untuk meredupkan | 2.41 ms | jauh terlalu mahal |
| `copy()` + `BLEND_RGBA_MULT` | 2.80 ms | sama saja |
| premultiply ke buffer opaque + `BLEND_RGB_ADD` | 0.61 ms | tidak menulis alpha → telegraf tak terlihat di kanvas SRCALPHA |
| tambahan mask alpha `BLEND_RGBA_MIN` | +0.30 ms | benar, tapi e/r tembus anggaran (8.9 ms) |
| `premul_alpha()` di-cache per dekal | 0.74 ms/dekal baru | radius berdenyut → nyaris selalu miss |
| **panggang di builder (`_pmc`)** | **0 ms** | dipakai |

Catatan penting untuk siapa pun yang menyentuh ini lagi: blit normal ke
buffer SRCALPHA **transparan tidak** mem-premultiply (RGB sumber lolos apa
adanya, hanya alpha yang diskala); hanya tujuan **opaque** yang
mem-premultiply. Asumsi sebaliknya adalah sumber bug ini.

## 11. Kualitas & performa

* `MAX_PARTICLES = 200`, `MAX_PROJECTILES = 22`, `TRAIL_SAMPLES = 10`,
  `MAX_IMPACTS = 9`, `MAX_SKILLS = 5`, `MAX_AFTERIMAGES = 7`,
  `MAX_DIRECTORS = 12`, `_CACHE_CAP = 210` — semuanya batas keras.
* Surface glow/ring/ember di-cache dengan kunci (bentuk, radius, warna) dan
  di-evict FIFO; `clear_cache()` mengosongkannya saat ganti level.
* Tidak ada efek berumur tak terbatas: 2000 tick tanpa input → partikel,
  proyektil, skill, dan impact semuanya nol (`test_fx_bounded_and_reset`).
* Anggaran: **±8.0 ms/frame** untuk badan + seluruh lapisan FX dengan skill
  R aktif di kanvas 900×700 (batas 16 ms), dan **1.9 ms** untuk pose dasar
  cache-miss (batas v2 4.0 ms).
* Perbaikan blend di §10.1 tidak menaikkan anggaran: skill q tetap ±1.95 ms
  (nilai v2 sebelum perbaikan: 1.99 ms), e/r ±3.1 ms pada audit cache-miss
  (batas 3.5 ms). Dua tes mengunci perilakunya —
  `test_additive_decals_respect_alpha` (glow harus meluruh dan menulis
  alpha) dan `test_decal_caches_are_bounded` (cache dekal/premul/fade
  tetap terbatas walau kunci terus berubah).

## 12. Debug mode

`DEBUG_CHARACTER = False` ada di **dua** tempat dan keduanya default mati:
`heroes.zharok_fx.DEBUG_CHARACTER` (overlay FX) dan
`_NS_zharok.DEBUG_CHARACTER` (overlay rig). Saat dinyalakan, overlay
menampilkan: hitbox, hurtbox, jangkauan serangan + `MELEE_REACH`, radius
tabrakan proyektil, state animasi + frame, FPS, jumlah partikel, state
skill + progres, dan timer serangan + fase.

## 13. Uji

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 tools/test_zharok_v3_combat.py
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 tools/test_zharok_masterwork.py
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 tools/_audit_zharok_v2.py
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 tools/test_ignis_v3_combat.py
```

`tools/test_zharok_v3_combat.py` (33 grup) mengunci: API modul + renderer
(backward compatible), palet konsisten dua arah, controller animasi,
ambang melee/ranged, kontinuitas ARC, satu sumber geometri busur, trail,
kontrak partikel + gravity + burst, lifecycle panah & tengkorak, bentuk
proyektil non-lingkaran, lifecycle skill 6 fase + dedup, sinkron radius &
durasi dengan AI, progres dari timer engine, telegraph AoE lingkaran,
bentuk skill non-lingkaran, renderer semua pose, mirror facing, potret HD
statis, fallback canvas, pipeline hero-lane, boss level4 lain tetap utuh,
hit-stop + shake, impact flash, overlay debug, integrasi `base_boss`,
registrasi `heroes/__init__`, prosedural murni, batas semua pool, dan
anggaran frame.

## 14. Integrasi engine (semua titik, semua ter-guard)

| Titik | Berkas | Isi |
|---|---|---|
| Registrasi live FX | `heroes/__init__.py` | `"zharok"` masuk `_LIVE_FX_HEROES` + `_LIVE_FX_PATHS["zharok"] = "heroes.zharok_fx"` |
| Benturan serangan dasar | `bosses/base_boss.py` (~L716) | jarak memilih `notify_melee_impact` (≤ `MELEE_REACH`) atau `notify_projectile_impact` |
| Cast Q/W/E/R | `bosses/base_boss.py :: _cast_zharok_*` | `notify_skill_cast` + `notify_skill_impact` di radius yang sama dengan damage |
| Gerbang renderer | `bosses/level4.py :: _NS_zharok._live_fx` | `draw_ground_layer` (boss lane) / `attach` (hero lane) + `recently_drawn` |
| Gambar lapisan hidup | `bosses/level4.py :: draw_zharok` | `live.draw_live_layer` setelah badan, sebelum overlay debug |

Semuanya dibungkus `try/except` dan difilter per `boss_type` — hero atau
boss lain tidak pernah menarik modul FX yang bukan miliknya.

## 15. Ringkasan perubahan per berkas

| # | Berkas | Perubahan |
|---|---|---|
| 1 | `heroes/zharok_fx.py` | **baru**, ±3.4k baris. 17 seksi: konstanta & kontrak, palet tersinkron, jembatan renderer, helper gambar + cache, `Particle`, `ParticleSystem`, `SwingTrail`, `ImpactFX`, proyektil modular, `Afterimage`, `SkillFX`, `ZharokFXDirector`, registri director, API gambar, notifikasi, overlay debug, `__all__` |
| 2 | `bosses/level4.py :: _NS_zharok` | konstanta v3 (`DEBUG_CHARACTER`, `ANIM_STATES`, `ATTACK_PHASES`, `BOW_ARC`, `MELEE_REACH`, `STAVE_HALF`, `GRIP_RIG`), controller `_update_zharok_anim` + `_resolve_pose`, `bow_geometry`, gerbang `_live_fx` + `recently_drawn`, Ember Cleave (`_draw_cleaving_bow`, `_draw_bow_cleave_arms`, `_draw_zh_melee`), afterimage rig, `draw_zharok` dirangkai ulang, overlay `_draw_zharok_debug`. **Seluruh API v2 dipertahankan** |
| 3 | `bosses/base_boss.py` | hook benturan Zharok (melee vs proyektil menurut `MELEE_REACH`) + `notify_skill_cast`/`notify_skill_impact` di keempat `_cast_zharok_*` |
| 4 | `heroes/__init__.py` | `zharok` terdaftar di `_LIVE_FX_HEROES` dan `_LIVE_FX_PATHS` |
| 5 | `tools/test_zharok_v3_combat.py` | **baru**, 33 grup regresi v3 |
| 6 | `docs/ZHAROK_V3_COMBAT_FX.md` | dokumen ini (+ penunjuk dari `ZYHAROK_V2_RENDERER.md`) |
