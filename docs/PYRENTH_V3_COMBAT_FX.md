# Pyrenth v3 — Renderer + Combat FX & Game Feel (100% prosedural)

> Rewrite penuh sistem **visual dan rasa tempur** untuk **PYRENTH — The
> Devourer** (mini-boss level 4, `bosses/level4.py :: _NS_pyrenth`).
> **100% prosedural**: tidak ada PNG / JPG / GIF / sprite-sheet / aset
> eksternal, tidak ada `pygame.image.load`. Semua bentuk dibangun dari
> `pygame.Surface`, `pygame.draw`, `pygame.transform`, `pygame.mask`,
> `Rect`, dan `Vector2`.
>
> Dokumen ini memaparkan renderer (rig, palet, pose, controller animasi)
> **dan** sistem tempurnya (ayunan pedang api ber-ARC, trail, proyektil,
> skill FX q/w/e/r, impact, hit-stop, screen shake, debug). Polanya
> mengikuti [`VOKRAHN_V3_COMBAT_FX.md`](VOKRAHN_V3_COMBAT_FX.md),
> [`ZHAROK_V3_COMBAT_FX.md`](ZHAROK_V3_COMBAT_FX.md), dan
> [`IGNIS_DRACHORN_V3_COMBAT_FX.md`](IGNIS_DRACHORN_V3_COMBAT_FX.md).

---

## 1. Masalah yang sebenarnya

Rig pyrenth lama (v1, ±1.870 baris di `level4.py`) sudah bisa bergerak,
tapi punya cacat struktural yang sama dengan vokrahn v1:

1. **Pose dipilih dari `if` bertingkat** atas `timer` / `active_skill`.
   Tidak ada nama state, prioritas, fase serangan, hit window, atau
   delta time. `_update_attack_anim` v1 hanya menghitung frame integer
   dan tidak pernah menyentuh jam nyata — animasi terikat frame rate.
2. **Pedang teleport.** Ayunan digambar sebagai pose statis; posisi
   tangan di-hardcode per pose (`_draw_attack_arms` dsb.) sehingga bilah
   melompat dari jaga ke tebas tanpa busur, dan `_draw_sword_swing_arc`
   menggambar busur hias yang **tidak menempel** pada mata pedang.
3. **Durasi skill tidak sinkron dengan gameplay.** Pose-draw v1
   memakai q=70 / w=55 / e=70 / r=60 frame, sedangkan AI di
   `base_boss.py` men-set `active_skill_timer` q=50 / w=40 / e=60 /
   r=70. FX selesai di waktu yang salah — kadang sebelum damage, kadang
   jauh sesudahnya.
4. **Semua efek hidup di dalam canvas badan.** Di lane hero badan
   di-cache lalu di-`smoothscale`; efek ikut **beku** dan **menyusut**.
5. **Tidak ada game feel**: damage instan, tanpa hit-stop, tanpa shake,
   tanpa impact flash terarah.
6. **Tidak ada mode debug** sama sekali.

## 2. Pemecahan: pisahkan badan dari efek

| Lapisan | Lokasi | Memiliki |
|---|---|---|
| **Renderer (badan + telegraph + fallback)** | `bosses/level4.py :: _NS_pyrenth` (L2957–5457) | rig demon-lord bersayap, palet 10-band, pose, **controller animasi** (`_update_pyr_anim`), **ARC pedang api** (`_blade_arc` / `blade_geometry`), lunge R (`_lunge_offset`), bayangan, aura hellfire, rune tanah, seluruh FX skill **fallback canvas** (Q/W/E/R), swing arc + impact, debug overlay |
| **Lapisan hidup 1:1** | `heroes/pyrenth_fx.py` (baru, 3.902 baris) | swing trail, particle system, proyektil Doom Bolt & Soul Ember, impact FX, skill FX q/w/e/r (6 fase lifecycle), afterimage lunge, overlay debug — semuanya di **ruang layar**, skala 1.0 |
| **Bus game feel (dipakai bersama)** | `heroes/combat_feel.py` (sudah ada) | hit-stop global 0.03–0.08 s, screen shake meluruh, delta-time frame |

Kenapa pembagian ini penting:

* lapisan hidup digambar **di luar** sprite cache → 60 fps sejati, tidak
  pernah beku dan tidak pernah ikut menyusut;
* renderer tetap **satu-satunya pemilik geometri badan**. Lapisan hidup
  tidak menghitung ulang pose — ia **membaca** `blade_geometry()`,
  `_blade_arc()`, `_lunge_offset()`, `_pyr_state`,
  `_pyr_attack_progress` lewat jembatan malas `_renderer()`. Bilah dan
  trail tidak mungkin berbeda satu frame pun;
* kalau `heroes.pyrenth_fx` gagal diimpor, `owns()` bernilai False dan
  renderer menggambar semuanya sendiri (fallback canvas dipertahankan
  utuh) — visual kehilangan polish, **tidak pernah** kehilangan efek.

### 2.1 Pengaman `recently_drawn()`

Di lane hero sprite bisa di-cache sehingga `draw_pyrenth` **tidak**
selalu dipanggil tiap frame. Lapisan hidup boleh mengambil alih FX
canvas hanya kalau `recently_drawn(unit)` benar; kalau tidak, fallback
canvas dinyalakan lagi. Diuji oleh
`test_canvas_fallback_when_nobody_draws_live_layer`.

## 3. Urutan gambar (kontrak render)

Di `draw_pyrenth`, per frame:

```
1. CONTROLLER      _detect_moving -> _update_pyr_anim -> _resolve_pose_pyr
2. GROUND FX       live.draw_ground_layer  (telegraph AoE, kolam api)
3. VISUAL SHIFT    _lunge_offset (R) / sin-lunge (attack) / recoil (hurt)
4. AURA + RUNE     _draw_hellfire_aura, _draw_ground_runes
5. SHADOW + WISPS  _draw_shadow (y+58), _draw_hellfire_wisps (y+42)
6. BADAN           _draw_pyr_body  (buffer -> crop -> flash -> outline ->
                                    rim light -> blit; rig disimpan)
7. FALLBACK FX     proyektil canvas + skill FX canvas  [hanya bila !owned]
8. LIVE LAYER      live.draw_live_layer (trail, partikel, proyektil,
                                         skill FX, impact, afterimage)
9. DEBUG           _draw_pyrenth_debug   [bila DEBUG_CHARACTER]
```

Rig digambar ke buffer `320×240` (`RIG_OX/OY = 160/140`), dipotong dengan
`get_bounding_rect()`, lalu diberi outline hitam 4 arah dan rim light
(`lighting.apply_to_rig(rim_add=(52,22,12), shade_mul=170)`). Hasilnya
disimpan di `_last_rig` / `_last_rig_off` supaya lapisan hidup bisa
memakai salinannya sebagai afterimage tanpa menggambar ulang badan.

## 4. Controller animasi (`_NS_pyrenth`)

`_update_pyr_anim(boss, moving)` adalah satu-satunya penentu state.
Ia memakai **delta time nyata** (`pygame.time.get_ticks()`, dt dibatasi
≤ 1/20 s) dan menulis kontrak atribut berikut:

```
_pyr_last_ms _pyr_dt _pyr_prev_timer
_pyr_attack_active _pyr_attack_frame _pyr_attack_progress _pyr_attack_phase
_pyr_hit_window _pyr_speed
_pyr_state _pyr_state_prev _pyr_state_time _pyr_state_priority
_pyr_pose_action _pyr_phase _pyr_suppress_canvas_fx
```

12 state master dengan prioritas (`ANIM_STATES`):

| state | prioritas | pemicu |
|---|---|---|
| IDLE | 0 | default |
| WALK | 10 | bergerak, speed ≤ 1.2 |
| RUN | 15 | bergerak, speed > 1.2 |
| CHARGE | 30 | fase awal skill |
| CAST | 35 | skill q / w |
| ATTACK | 40 | timeline serangan aktif |
| SWING | 45 | serangan di dalam fase SWING/IMPACT |
| SKILL | 50 | skill q / w / e |
| SPECIAL | 55 | skill r (Infernal Blade) |
| HIT | 60 | flash damage singkat |
| HURT | 65 | `hurt_flash_timer` |
| DEATH | 100 | `alive` False |

Timeline serangan (`ATTACK_PHASES`), progress 0..1:

```
ANTICIPATION .00–.12   WINDUP .12–.30   SWING .30–.50
IMPACT       .50–.62   FOLLOW .62–.82   RECOVERY .82–1.0
```

`ATTACK_ACTIVE_WINDOW = (0.38, 0.62)` dan `ATTACK_IMPACT_FRAME = 0.52`
adalah **satu angka yang dipakai bersama** renderer dan lapisan FX
(`F.ATTACK_* == NS.ATTACK_*`, dikunci oleh tes).

Panjang animasi = `clamp(attack_cooldown - 1, 10, 30)` frame, sehingga
serangan cepat tidak pernah membuat busur terpotong.

## 5. ARC pedang api — satu sumber kebenaran

`BLADE_ARC` adalah 6 segmen `(t0, t1, phi0, phi1, ease)` dalam ruang
layar (`y` ke bawah), dengan `tip = grip + (facing·cos φ·L, −sin φ·L)`:

```
.00–.12  0.96 →  2.18  out    angkat dari jaga
.12–.30  2.18 →  2.88  io     wind-up ke atas-belakang
.30–.50  2.88 → −1.31  oc     tebasan cepat (melewati .52 = IMPACT)
.50–.62 −1.31 → −1.05  hold   tahan di titik benturan
.62–.82 −1.05 → −0.44  io     follow-through
.82–1.0 −0.44 →  0.96  io     kembali ke jaga
```

Loop **tertutup** (`φ(0) == φ(1)`) dan langkah maksimum < 0.35 rad per
1/200 progres — bilah mustahil teleport (`test_blade_arc_continuity`).

`blade_geometry(facing, action, phase, attack_progress)` mengembalikan
`(grip, tip_hi, tip_lo, phi)` dan **semua posisi tangan diturunkan
darinya** — `_grip_screen`, `_draw_weapon_arm`, `_draw_off_arm` membangun
lengan dua-segmen dengan tekukan siku tegak lurus mengikuti grip. Jadi
tangan tidak pernah lepas dari gagang di pose mana pun, dan panjang bilah
konstan di semua pose (`test_blade_geometry_single_source`).

`heroes/pyrenth_fx.py` menyimpan tabel cadangan **identik** tapi selalu
membaca fungsi renderer bila tersedia (`F.BLADE_ARC == NS.BLADE_ARC`).

### 5.1 Lunge R

`_lunge_offset(progress)` memberi dorongan maju **46 px** pada rentang
progress engine 0.302–0.605, kembali 0 saat skill selesai. FX membacanya
lewat `F.lunge_offset(unit, t)` dengan konversi basis waktu
(`t_engine = t_fx / ENGINE_SPAN`, `ENGINE_SPAN = 0.86`), dikunci oleh
`test_lunge_offset_bridge`.

## 6. Lapisan hidup (`heroes/pyrenth_fx.py`)

* **Particle system** — bentuk `ember / soul / shard / smoke / spark`,
  batas keras `MAX_PARTICLES`, pool director `MAX_DIRECTORS = 12`.
* **SwingTrail** — merekam histori posisi **bilah nyata** (bukan busur
  tiruan) sebanyak `TRAIL_SAMPLES`.
* **Proyektil modular** — `DoomBoltProjectile` (rantai kutukan Q) dan
  `SoulEmberProjectile` (tetesan jiwa teal bermata, W) berbagi kontrak
  `BaseProjectile`: `spawn → travel → trail → hit → impact FX → destroy`.
* **SkillFX** — lifecycle 6 fase (`SKILL_PHASES`), umur dislaved ke
  `active_skill_timer` lewat `set_engine_progress()` yang **monoton naik**
  sehingga satu frame terisolasi di tengah skill tetap digambar di radius
  yang benar.
* **ImpactFX** — flash, sabit api terarah, shockwave, serpihan; jenis
  `melee / skill / projectile / quake`.
* **Afterimage** — salinan rig renderer (`_last_rig`) untuk lunge R.

### 6.1 Bentuk skill (tidak semua lingkaran)

| skill | identitas | bentuk |
|---|---|---|
| **Q — Doom Chain** | rantai kutukan single-target (200) | koridor bidik + rantai bercincin + orb muatan di ujung bilah |
| **W — Devour** | serap jiwa + heal 8% | berkas jiwa masuk + tetesan jiwa mengorbit + cakar besar |
| **E — Scorched Earth** | AoE 180 | cincin duri api r=60/40 + retakan magma + bara |
| **R — Infernal Blade** | ultimate AoE 220 | lunge 46 px + sabetan raksasa + cincin telegraph 220 |

Cincin telegraph E dan R adalah **lingkaran sejati di radius dunia**
(180 / 220) — sama persis dengan radius damage AI, karena pemain membaca
jangkauan dari cincin itu (`test_aoe_telegraph_is_a_true_circle`).

### 6.2 Notifikasi dari AI (bridge `base_boss.py`)

```python
_pyrfx.notify_melee_impact(self, self.target, self.damage, False)  # L761
_pyrfx.notify_skill_cast(self, 'q' | 'w' | 'e' | 'r')
_pyrfx.notify_skill_impact(self, self.x, self.y, radius=180|220, skill=...)
```

Semua dibungkus `try/except` dan difilter `boss_type == 'pyrenth'`,
sehingga boss lain tidak terpengaruh dan game tetap jalan kalau modul FX
hilang.

## 7. Game feel

* **Hit-stop** 0.03–0.08 s pada impact melee dan impact skill.
* **Screen shake** meluruh (bukan konstan): 12 / 10 / 18 / 25 untuk
  Q / W / E / R, sama dengan `_shake_screen` yang sudah ada.
* **Impact flash** digambar pada surface transparan, bukan `fill` layar.
* `blit_add` mem-**premultiply** alpha sebelum `BLEND_RGB_ADD`, supaya
  glow meluruh alih-alih jadi cakram warna bertepi keras.

## 8. `DEBUG_CHARACTER`

```python
import bosses.level4 as L
from heroes import pyrenth_fx as F
L._NS_pyrenth.DEBUG_CHARACTER = True     # hitbox bilah, hurtbox, range,
F.DEBUG_CHARACTER = True                 # state, fase, FPS, partikel
```

Overlay renderer menampilkan: jangkauan serangan + `MELEE_REACH` +
radius skill aktif (elips tanah), hurtbox, hitbox bilah `grip → tip`
(merah saat hit window terbuka), titik grip, garis proyektil canvas, dan
panel teks berisi state + prioritas, pose, dt/FPS, attack progress +
fase, hit window, timer & cooldown, skill aktif, dan jumlah partikel /
proyektil.

## 9. Daftar perubahan per file

### `bosses/level4.py` (10.486 → 11.116 baris)

Semua di dalam `class _NS_pyrenth` (namespace boss lain **tidak
disentuh** — diverifikasi byte-identik terhadap `HEAD`).

* **Docstring + konstanta kontrak baru**: `DEBUG_CHARACTER`, `_LIVE_MOD`,
  `_last_rig`, `_last_rig_off`, `_body_buf`, `RIG_W/H = 320/240`,
  `RIG_OX/OY = 160/140`, `GROUND_DY = 58`,
  `SKILL_DUR = {q:50, w:40, e:60, r:70}` (kini **sinkron dengan AI**),
  `SKILL_RADIUS = {q:200, w:200, e:180, r:220}`, `MELEE_REACH = 96`,
  `ATTACK_ACTIVE_WINDOW`, `ATTACK_IMPACT_FRAME`, `ATTACK_PHASES`,
  `ANIM_STATES`, `BLADE_ARC`, `_BLADE_HALF = 34.0`, `_GRIP = (26, −8.7)`.
* **Gerbang lapisan hidup**: `_live_module()`, `live_fx_ready()`,
  `_live_fx()` (termasuk fallback `recently_drawn()`).
* **Controller animasi**: `_ease`, `attack_phases_order`, `attack_phase`,
  `_blade_lift`, `_blade_arc`, `blade_geometry`, `_lunge_offset`,
  `_detect_moving` (baru, menulis `_pyr_speed`), `_update_pyr_anim`
  (baru), `_update_attack_anim` (shim kompatibel), `_resolve_pose_pyr`.
* **`draw_pyrenth`** ditulis ulang jadi pipeline komposit 9 langkah.
* **`_handle_skill_projectiles`** memakai `SKILL_DUR` (dulu 70/60
  hardcoded) dan mereset `_pyr_q_spawned` / `_pyr_r_spawned`.
* **`_draw_pyr_body`** dipecah jadi `_draw_pyr_body_raw` (urutan lapis:
  sayap → ekor → tubuh bawah → torso → pauldron → lengan+pedang →
  kepala) + pipeline rig (crop, hit-flash, outline, rim light, simpan).
* **Seluruh blok lengan ditulis ulang** berbasis `blade_geometry`:
  `_grip_screen`, `_draw_weapon_arm`, `_draw_off_arm`, lalu
  `_draw_idle_arms`, `_draw_attack_arms`, `_draw_r_arms`,
  `_draw_q_cast_arms`, `_draw_w_cast_arms`, `_draw_e_cast_arms`.
* **`_draw_sword_swing_arc` & `_draw_swing_impact`** ditulis ulang agar
  mengambil titik dari ARC yang sama dengan bilah (pita menempel di mata
  pedang; kilat benturan di ujung bilah, bukan di tengah badan).
* **Debug baru**: `_dbg_font`, `_draw_pyrenth_debug`.
* **API lama dipertahankan**: `_draw_pyr_idle/walk/attack`,
  `_draw_pyr_qcast/wcast/ecast/rcast` (kini pembungkus tipis atas
  `_draw_pyr_cast`), `_manage_projectiles`, `_spawn_doom_chain`,
  `_spawn_infernal_arc`, `DoomChain`, `InfernalArc`, `PALETTE`,
  `draw_boss`.

### `heroes/pyrenth_fx.py` (baru, 3.902 baris)

Modul lapisan hidup lengkap: konstanta + palet `PYRENTH_PALETTE` (+
`_PALETTE_SYNC` ke palet renderer), primitif ber-cache (`glow_surface`
dari annuli, `ring_surface`, `ember_surface`, `blit_add` premultiplied,
`_hash01`, pool scratch), `Particle` / `ParticleSystem` / `SwingTrail` /
`ImpactFX` / `Afterimage`, `BaseProjectile` / `DoomBoltProjectile` /
`SoulEmberProjectile` / `ProjectileSystem`, `SkillFX` 6 fase,
`PyrenthFXDirector`, jembatan geometri (`blade_arc`, `blade_points`,
`blade_tip`, `blade_angle`, `lunge_offset`, `pose_of`, `render_scale`),
notifikasi (`notify_melee_impact`, `notify_projectile_cast/impact`,
`notify_skill_cast/impact`, `notify_hurt`, `notify_death`), dan overlay
debug. `__all__` lengkap dan diverifikasi tidak ada nama menggantung.

### `heroes/__init__.py`

* `"pyrenth"` ditambahkan ke `_LIVE_FX_HEROES`;
* `_LIVE_FX_PATHS["pyrenth"] = "heroes.pyrenth_fx"`.

### `bosses/base_boss.py`

* hook impact melee pyrenth (difilter `boss_type`, `try/except`);
* `notify_skill_cast` di `_cast_pyrenth_q/w/e/r`;
* `notify_skill_impact` di `_cast_pyrenth_e` (radius 180) dan
  `_cast_pyrenth_r` (radius 220).

### `tools/test_pyrenth_v3_combat.py` (baru, 1.091 baris)

38 tes: API + palet, controller (12 state, prioritas, fase, dt),
kontinuitas `BLADE_ARC`, sumber geometri tunggal, jembatan lunge,
swing trail, partikel + batasnya, lifecycle proyektil, lifecycle +
dedup skill, radius = radius gameplay, telegraph lingkaran sejati,
renderer semua state / facing / potret, fallback canvas, lane hero,
boss level4 lain tidak rusak, `blit_add` menghormati alpha, afterimage,
cache terbatas, hit-stop + shake, overlay debug, integrasi AI +
registry, prosedural murni, FX tidak abadi, dan anggaran frame.

## 10. Cara menjalankan tes

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
    python3 tools/test_pyrenth_v3_combat.py
```

Hasil saat ditulis: **38/38 lulus, 6,68 ms/frame** (badan + lapisan FX
dengan skill R aktif — jauh di bawah anggaran 16 ms). Suite vokrahn,
zharok, ignis, dan tes renderer umum tetap lulus tanpa perubahan.

## 11. Batasan yang disengaja

* Pyrenth **selalu melee** — tidak ada mode jarak jauh, jadi controller
  tidak punya percabangan bidik. Proyektil Q/W adalah efek skill, bukan
  serangan dasar.
* Lapisan hidup **tidak** digambar pada potret HD (`_portrait_hd`):
  potret harus statis dan deterministik.
* Nilai damage, cooldown, dan radius **tidak diubah** — rewrite ini
  murni visual + rasa; angka gameplay tetap milik `boss_data.py` dan
  `base_boss.py`.
