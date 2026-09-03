# Vokrahn v3 — Renderer + Combat FX & Game Feel (100% prosedural)

> Rewrite penuh sistem **visual dan rasa tempur** untuk **VOKRAHN — The
> Chaos Knight** (mini-boss level 4, `bosses/level4.py :: _NS_vokrahn`).
> **100% prosedural**: tidak ada PNG / JPG / GIF / sprite-sheet / aset
> eksternal, tidak ada `pygame.image.load`. Semua bentuk dibangun dari
> `pygame.Surface`, `pygame.draw`, `pygame.transform`, `Rect`, dan
> `Vector2`.
>
> Dokumen ini memaparkan renderer (rig, palet, pose, controller animasi)
> **dan** sistem tempurnya (ayunan greatsword ber-ARC, trail, proyektil,
> skill FX q/w/e/r, impact, hit-stop, screen shake, debug). Polanya
> mengikuti [`ZHAROK_V3_COMBAT_FX.md`](ZHAROK_V3_COMBAT_FX.md) dan
> [`IGNIS_DRACHORN_V3_COMBAT_FX.md`](IGNIS_DRACHORN_V3_COMBAT_FX.md).

---

## 1. Masalah yang sebenarnya

Rig vokrahn lama (v1, ±1.800 baris di `level4.py`) sudah bisa bergerak,
tapi:

1. **Pose dipilih dari `if` bertingkat** atas `timer` / `active_skill` —
   tidak ada nama state, prioritas, fase serangan, hit window, atau delta
   time. Tidak ada satu tempat pun yang bisa ditanya *"frame berapa, fase
   apa, boleh kena tidak"*.
2. **Pedang teleport.** Ayunan digambar sebagai 2–3 frame pose statis;
   bilah melompat dari posisi jaga ke posisi tebas tanpa busur.
3. **Semua efek hidup di dalam canvas badan.** Di lane hero, badan
   di-cache lalu di-`smoothscale` — efek ikut **beku** dan ikut
   **menyusut**.
4. **Proyektil v1 bulat** (lingkaran + glow), tanpa trail, tanpa rotasi,
   tanpa kontrak atribut modular.
5. **Tidak ada game feel**: damage instan, tanpa hit-stop, tanpa shake,
   tanpa impact flash terarah.
6. **Skill FX v1 = lingkaran generik** — W dan R (keduanya AoE 220)
   terlihat identik; Q tidak punya koridor bidik yang terbaca.

## 2. Pemecahan: pisahkan badan dari efek

| Lapisan | Lokasi | Memiliki |
|---|---|---|
| **Renderer (badan + telegraph + fallback)** | `bosses/level4.py :: _NS_vokrahn` (L4830–7204) | rig ksatria-kuda 9-lapis, palet 9-band, pose, **controller animasi** (`_update_vok_anim`), **ARC greatsword** (`_sword_arc` / `sword_geometry`), dash offset (`_dash_offset`), bayangan, aura chaos, rune tanah, seluruh FX skill **fallback canvas** (Q/W/E/R), swing arc + impact, debug overlay |
| **Lapisan hidup 1:1** | `heroes/vokrahn_fx.py` (baru, 3.555 baris) | swing trail, particle system, proyektil Chaos Bolt & Chaos Brand, impact FX, skill FX q/w/e/r (6 fase lifecycle), afterimage dash, overlay debug — semuanya di **ruang layar**, skala 1.0 |
| **Bus game feel (dipakai bersama)** | `heroes/combat_feel.py` (sudah ada) | hit-stop global 0.03–0.08 s, screen shake meluruh, delta-time frame |

Kenapa pembagian ini penting:

* lapisan hidup digambar **di luar** sprite cache → 60 fps sejati, tidak
  pernah beku dan tidak pernah ikut menyusut;
* renderer tetap **satu-satunya pemilik geometri badan**. Lapisan hidup
  tidak menghitung ulang pose — ia **membaca** `sword_geometry()`,
  `_sword_arc()`, `_dash_offset()`, `_vok_state`, `_vok_attack_progress`
  lewat jembatan malas `_renderer()`. Bilah dan trail tidak mungkin
  berbeda satu frame pun;
* kalau `heroes.vokrahn_fx` gagal diimpor, `owns()` bernilai False dan
  renderer menggambar semuanya sendiri (fallback canvas v1 dipertahankan
  utuh) — visual kehilangan polish, **tidak pernah** kehilangan efek.

### 2.1 Pengaman `recently_drawn()`

Di lane hero, sprite bisa di-cache (fase baru tiap N frame) sehingga
`draw_vokrahn` **tidak** selalu dipanggil. Lapisan hidup boleh mengambil
alih FX canvas hanya kalau `recently_drawn(unit)` benar — kalau tidak,
fallback canvas tetap hidup. Ini diuji oleh
`test_canvas_fallback_when_nobody_draws_live_layer`.

## 3. Urutan gambar (kontrak render)

Di `draw_vokrahn` (L6969), per frame:

```
1.  _update_vok_anim(boss, moving)      # controller: dt, state, fase
2.  lapisan hidup GROUND   (live.draw_ground_layer)  → set _vok_suppress_canvas_fx
3.  aura chaos + rune tanah (canvas, di bawah badan)
4.  telegraph ground W/R  (canvas, HANYA jika tidak di-own lapisan hidup)
5.  phantom R  (canvas, di belakang badan)
6.  bayangan + chaos wisps (back)
7.  _draw_vok_body  →  sub-surface rig 9-lapis:
        bayangan-kuda → ekor → kaki belakang → badan kuda → maned
        → torso ksatria + jubah → perisai → kepala + tanduk
        → pedang api (grip dari sword_geometry) → lengan depan
        → highlight → wisps (front)
      posisi badan digeser _dash_offset(ap) saat skill E
8.  FX canvas foreground (HANYA jika tidak di-own):
        swing arc + impact flash, dash trail, proyektil v1 (Q),
        charge glow Q, duri W foreground
9.  lapisan hidup FRONT (live.draw_live_layer):
        trail, partikel, proyektil, skill FX, impact, afterimage
10. _draw_vokrahn_debug  (hanya jika DEBUG_CHARACTER)
```

Konsekuensi: partikel **latar** (debu, abu) digambar lapisan ground;
cahaya & percikan **depan** digambar lapisan front. Di fallback canvas
urutan yang sama dipertahankan sehingga karakter terlihat konsisten
meski modul FX absen.

## 4. Controller animasi (`_NS_vokrahn`)

```
IDLE(0)  WALK(10)  RUN(15)  CHARGE(30)  CAST(35)  ATTACK(40)
SWING(45)  SKILL(50)  SPECIAL(55)  HIT(60)  HURT(65)  DEATH(100)
```

* **Delta time nyata** dari `pygame.time.get_ticks()` (clamped 0, 50 ms —
  kalau tidak, 1/60 s).
* **Prioritas** = nilai di atas; state tertinggi menang (DEATH > HURT >
  HIT > SPECIAL > SKILL > SWING > ATTACK > CAST/CHARGE > WALK/RUN > IDLE).
* **Timeline serangan**: `boss.timer` engine menghitung mundur; lompatan
  naik ke cooldown = serangan baru. Progress = frame / `min(cooldown-1,
  30)`, di-clamp 0..1.
* **Fase serangan** (SATU tabel, dibaca renderer, lapisan hidup, dan
  tes):

  | Fase | Progres |
  |---|---|
  | ANTICIPATION | 0.00–0.12 |
  | WINDUP | 0.12–0.30 |
  | SWING | 0.30–0.50 |
  | IMPACT | 0.50–0.62 |
  | FOLLOW | 0.62–0.82 |
  | RECOVERY | 0.82–1.00 |

  Hit window aktif = `(0.38, 0.62)`, frame impact = `0.52` — angka yang
  **sama** di renderer, di lapisan hidup (momen impact FX), dan di tes.
* **Vokrahn selalu melee** (greatsword 96 px jangkauan) — tidak ada
  percabangan bidik; state `CAST` hanya untuk skill (bidik Q/W).

## 5. ARC greatsword — satu sumber kebenaran

`SWORD_ARC` (tabel `(t0, t1, phi0, phi1, ease)`) + `_sword_lift()`
dihubungkan oleh `_sword_arc(progress) -> (phi, lift)`. `sword_geometry(
facing, action, phase, attack_progress) -> (grip, tip, ujung_bawah, phi)`
adalah **satu-satunya** fungsi yang menghitung posisi pedang:

* panjang bilah **konstan** 48 px di semua pose (ditegaskan tes
  `test_sword_geometry_single_source`);
* loop tertutup: `phi(0) == phi(1) == 0.96` rad (posisi jaga), langkah
  maksimum ≈ 0.31 rad per 1/200 progres — **bilah tidak pernah
  teleport** (tes `test_sword_arc_continuity`);
* lapisan hidup (`sword_points`, `sword_tip`, `sword_angle`,
  `launch_point`) membaca fungsi ini; tabel cadangan di
  `vokrahn_fx.SWORD_ARC` **identik** (ditegaskan tes) dan hanya dipakai
  kalau renderer tak bisa diimpor.

**Dash (skill E)**: `_dash_offset(progress)` — keluar 80 px (0→0.302,
easing out), tahan (0.302–0.605), kembali (0.605→1.0). Lapisan hidup
mengonversi basis waktu `t` (0..1 atas umur FX penuh, yang 14% terakhinya
adalah ekor AFTER) ke progres engine dengan `eng = t / ENGINE_SPAN`
(`ENGINE_SPAN = 0.86`) **sebelum** memanggil fungsi renderer — diuji oleh
`test_dash_offset_bridge`.

## 6. Lapisan hidup (`heroes/vokrahn_fx.py`)

Komponen (semua ber-cap, semua meluruh, tidak ada satu pun efek abadi):

| Komponen | Cap | Catatan |
|---|---|---|
| `ParticleSystem` + `Particle` | `MAX_PARTICLES = 200` | position/velocity/acceleration (Vector2), life/max_life, size, rotation(_speed), alpha, gravity, drag, shape (ember/dust/shard/spark), burst/spread/directional |
| `SwingTrail` | `TRAIL_SAMPLES = 10` | menyimpan POSISI LAMA grip (bukan pose sekarang); digambar additif premultiply; meluruh ~0.3 s |
| `ProjectileSystem` | `MAX_PROJECTILES = 22` | `ChaosBoltProjectile` (panah api memanjang + sirip, rotasi mengikuti arah) & `ChaosBrandProjectile` (bintang chaos 5-titik, W). Lifecycle SPAWN→TRAVEL→TRAIL→HIT→IMPACT→DESTROY |
| `SkillFX` | `MAX_SKILLS = 5` | lifecycle 6 fase `CAST→CHARGE→RELEASE→AREA→IMPACT→AFTER` (tabel `SKILL_PHASES`), dikunci ke timer engine lewat `set_engine_progress` (monoton) |
| `ImpactFX` | `MAX_IMPACTS = 9` | flash bintang + sabit + serpihan + ring; transparan, tidak menutupi siluet |
| `Afterimage` | `MAX_AFTERIMAGES = 7` | salinan **surface rig tersimpan** (`NS._last_rig`) — ghost pose selalu benar tanpa menggambar ulang badan; dash E digeser manual mengikuti jalur `dash_offset` |
| pool director | `MAX_DIRECTORS = 12` | LRU per unit (boss lane + hero lane) |
| cache decal | `_CACHE_CAP = 210` | glow/ring/spike/taper — premultiply + blit additif yang **menghormati alpha** (`blit_add`) |

### 6.1 Bentuk skill (tidak semua lingkaran)

| Skill | Telegraph / visual |
|---|---|
| **Q — Chaos Bolt** (250, 50 f) | koridor bidik **menyempit** (`taper_lane`) panjang 250 px ke arah target + rune tick + charge orb di gagang pedang |
| **W — Crimson Quake** (220, 60 f) | **cincin lingkaran penuh** radius dunia 220 (jangkar `y+10`) + duri chaos + kisi retakan; duri foreground di layer front |
| **E — Chaos Strike** (150, 50 f) | bukan AoE: **dash 80 px** — telegraph jalur (lane tipis ke titik pendaratan), afterimage, kejut pendaratan di titik target |
| **R — Realm of Chaos** (220, 80 f) | **cincin lingkaran penuh** 220 + bintang chaos 8-titik + rune spiral + phantom di belakang badan |

Radius & durasi FX **sama persis** dengan radius damage dan
`active_skill_timer` AI di `base_boss.py` (ditegaskan
`test_skill_radius_matches_gameplay`, termasuk scan sumber).

### 6.2 Notifikasi dari AI (bridge `base_boss.py`)

* melee: `notify_melee_impact(self, self.target, self.damage, False)`
  (guard `boss_type == 'vokrahn'`) — vokrahn selalu melee, tidak ada
  cabang jarak;
* tiap skill: `notify_skill_cast(self, 'q'|'w'|'e'|'r')` lalu
  `notify_skill_impact(...)` di titik damage (Q/E di target; W/R di
  tengah boss, radius 220) — cast+impact yang sama **dedup** (Satu
  SkillFX, di-update di tempat), jadi tidak ada efek dobel.

## 7. Game feel

* **Hit-stop** 0.03–0.08 s (`combat_feel`, ditegaskan
  `test_hit_stop_and_shake`); benturan melee berat memakai nilai atas.
* **Screen shake** meluruh eksponensial (`shake_strength`,
  `shake_duration`) — diuji sampai nol.
* **Impact flash** via surface transparan (bukan `fill` layar).
* Budget partikel & glow di-lowercase saat banyak unit
  (`particle_budget()`, `glow_allowed()`).

## 8. `DEBUG_CHARACTER`

Flag **global per modul**, default `False`, di kedua sisi:
`_NS_vokrahn.DEBUG_CHARACTER` (renderer: hitbox/hurtbox jangkauan 96 px,
busur pedang, state, frame, dt, fase, hit window, partikel/skill count)
dan `vokrahn_fx.DEBUG_CHARACTER` (overlay lapisan hidup: radius skill,
trail, proyektil, afterimage, FPS). Mengubah flag tidak menyentuh
apa pun selain memanggil `_draw_vokrahn_debug` / `draw_debug_overlay`.

## 9. Daftar perubahan per file

### `bosses/level4.py` (9.957 → 10.486 baris)

Seluruh `_NS_vokrahn` lama (L4826–6670 v1) **diganti** kelas V3
(L4830–7204). Bagian lain file (pyrenth, ignis_drachorn, dll.) tidak
disentuh. Isi kelas baru, berurutan:

1. Konstanta: `DEBUG_CHARACTER`, `GROUND_DY`, `SKILL_DUR`,
   `SKILL_RADIUS`, `MELEE_REACH`, `ATTACK_ACTIVE_WINDOW`,
   `ATTACK_IMPACT_FRAME`, `ATTACK_PHASES`, `ANIM_STATES` (12 state),
   `SWORD_ARC`, `_SWORD_HALF`, `_GRIP`, `PALETTE` (9-band + 9 kunci
   kontrak outline/shadow/dark/body/mid/light/highlight/weapon/fx).
2. Helper draw (`_clamp`, `_aacircle`, `_aaline`, `_poly`, `_ellipse`,
   `_rect`, `_target_position`, `_draw_chaos_spike`, `_draw_ember`).
3. Proyektil canvas v1 dipertahankan (`ChaosBolt`, `ImpactBurst`,
   `_manage_projectiles`, `_spawn_chaos_bolt`, `_spawn_burst`) — API lama
   tetap berfungsi sebagai fallback.
4. Jembatan live: `_live_module`, `live_fx_ready`, `_live_fx`.
5. Controller: `_ease`, `attack_phases_order`, `attack_phase`,
   `_sword_lift`, `_sword_arc`, `sword_geometry`, `_dash_offset`,
   `_detect_moving`, `_update_vok_anim`, `_update_attack_anim` (compat),
   `_resolve_pose_vok`.
6. Rig 9-lapis: `_draw_vok_body_raw`, `_draw_vok_body` (menyimpan
   `NS._last_rig` + `_last_rig_off` untuk afterimage), punggung-kuda
   (`_draw_cape`, `_draw_horse_tail`, `_draw_horse_body`,
   `_draw_horse_legs`, `_draw_horse_head`, `_draw_horse_mane`),
   ksatria (`_draw_knight_torso`, `_draw_shield`, `_draw_knight_head`,
   `_draw_knight_arm_pair` + variasi pose lengan, `_draw_gauntlet`),
   pedang (`_draw_flaming_sword_line`).
7. Lingkungan: `_draw_chaos_wisps`, `_draw_shadow`, `_draw_chaos_aura`,
   `_draw_ground_runes`, `_draw_sword_swing_arc`, `_draw_swing_impact`.
8. FX skill fallback canvas: `_handle_skill_projectiles`,
   `_draw_q_charge_glow`, `_draw_realm_of_chaos_ground`,
   `_draw_realm_of_chaos`, `_draw_phantasm_ground`,
   `_draw_phantasm_illusions`, `_draw_dash_trail_fx`.
9. Entri: `draw_vokrahn` (L6969, urutan render §3), `_draw_vokrahn_debug`
   (L7095+), `draw_boss` (L7198, dispatcher per `boss_type`).

### `heroes/vokrahn_fx.py` (baru, 3.555 baris)

Modul lapis hidup utuh: konstanta + palet (`VOKRAHN_PALETTE`,
`_PALETTE_SYNC` — warna kerja FX di-*sync* dari palet renderer jadi
keduanya tidak bisa menyimpang), primerif ber-cache (`glow_surface`,
`ring_surface`, `ellipse_ring_surface`, `spike_ring_surface`,
`arc_ring_surface`, `taper_lane`, `spark_star`, `chevron`, `shard_poly`,
`flame_poly`, `crack_points`, `chaos_star_points`, `blit_add`
premultiply), `Particle`/`ParticleSystem`, `SwingTrail`, `ImpactFX`,
`Afterimage`, `BaseProjectile` + `ChaosBoltProjectile` +
`ChaosBrandProjectile` + `ProjectileSystem`, `SkillFX` (6 fase,
`ENGINE_SPAN = 0.86`), `VokrahnFXDirector` (sync/update/draw_ground/
draw_front/push_afterimage/_melee_impact), API global
(`attach/owns/recently_drawn/tick/reset_all/total_particles/stats`,
`draw_ground_layer/draw_live_layer/draw_debug_overlay`,
`notify_melee_impact/notify_projectile_*/notify_skill_*/notify_hurt/
notify_death`), jembatan geometri (`sword_arc/sword_points/sword_tip/
sword_angle/launch_point/dash_offset/pose_of/render_scale/body_scale/
target_point/ring_radius`).

### `heroes/__init__.py`

* `"vokrahn"` ditambahkan ke `_LIVE_FX_HEROES` (L663);
* `"vokrahn": "heroes.vokrahn_fx"` ditambahkan ke `_LIVE_FX_PATHS`
  (L683). Tidak ada perubahan pipeline lain — `render_hero` /
  `_live_fx_pre` / `_live_fx_post` bekerja generik.

### `bosses/base_boss.py`

* `BOSS_LABEL_TOP["vokrahn"]`: 46 → **84** (puncak rig v3 = tanduk di
  ~-78 px, diukur dari render; nilai lama menempatkan HP bar di atas
  kepala).
* Hook melee (±L744): setelah `boss_type == 'vokrahn'` →
  `_vokfx.notify_melee_impact(self, self.target, self.damage, False)`
  (try/except, paritas Zharok).
* `_cast_vokrahn_q/w/e/r` (L3872/3894/3914/3934): masing-masing memanggil
  `notify_skill_cast(self, 'x')` lalu `notify_skill_impact(...)` di titik
  damage (Q/E: di target, 70/60 px; W/R: di tengah boss, radius 220) —
  sama persis dengan cek damage AI (`<= 220`).
* Durasi skill AI **tidak diubah** (50/60/50/80 frame) — renderer & FX
  yang dikontrak padanya.

### `tools/test_vokrahn_v3_combat.py` (baru, 1.072 baris)

38 tes yang mengunci semua kontrak di atas (API, palet, controller,
ARC/bridge, dash bridge, trail, partikel, proyektil, skill lifecycle +
dedup, radius=gameplay, progres engine, telegraph lingkaran 220, bentuk
bukan-lingkaran, renderer semua state, facing/portrait, fallback canvas,
jalur hero, boss lain utuh, additive premultiply, afterimage, cap &
reset, hit-stop/shake, flash transparan, debug, integrasi AI + registry,
prosedural murni, budget frame 16 ms).

## 10. Cara menjalankan tes

```
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 tools/test_vokrahn_v3_combat.py
```

Hasil terakhir: **38/38 PASS**, ~7.5 ms/frame (badan + lapisan FX,
skill R aktif) — di bawah anggaran 16 ms. Regresi tetangga
(`tools/test_zharok_v3_combat.py`, `tools/test_ignis_v3_combat.py`)
tetap PASS.

## 11. Batasan yang disengaja

* `settings.py` hanya ada di lingkungan runtime game (bukan di checkout
  ini), jadi tes tidak mengimpor `bosses.base_boss` — kontrak AI
  divalidasi dengan scan sumber (`test_skill_radius_matches_gameplay`,
  `test_base_boss_integration`).
* Afterimage memakai surface rig **terakhir** yang tersimpan (pose sama,
  posisi digeser) — bukan render ulang per ghost; murah (1 blit) dan
  cukup untuk kesan kecepatan.
* Di lane hero, sprite tetap di-cache; yang hidup 60 fps adalah lapisan
  FX (sesuai arsitektur `render_hero` yang ada).
