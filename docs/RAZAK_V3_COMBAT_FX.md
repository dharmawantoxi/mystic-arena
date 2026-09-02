# Razak v3 — Combat FX & Game Feel (lapisan hidup 100% prosedural)

> Rewrite penuh sistem tempur **RAZAK** (Fire Rider, mini boss level 2 yang
> juga bisa dipakai sebagai hero). Tetap **100% prosedural**: tidak ada
> PNG / JPG / GIF / sprite-sheet / texture eksternal. Semua dibangun dari
> `pygame.Surface`, `pygame.draw`, `pygame.transform`, `Rect`, `Vector2`,
> dan `pygame.mask` API sejenis yang dipakai pipeline.
>
> Dokumen ini memaparkan **sistem tempurnya** (animation controller, swing
> attack, weapon trail, projectile, skill FX, impact, particle, hit-stop,
> screen shake, debug overlay). Untuk geometri badan & disiplin pixel-art
> renderer masterwork, lihat [`RAZAK_V2_RENDERER.md`](RAZAK_V2_RENDERER.md).

---

## 1. Masalah yang sebenarnya

Sesudah pass renderer v2 (`bosses/level2.py::_NS_razak` — bat api + goblin
rider + flamethrower), tempurnya belum selive keluarga Gornak/Grimjaw, dan
penyebabnya arsitektural:

1. **Sprite di-cache & di-kuantisasi.** `heroes/__init__.py` memakai ulang
   gambar selama pose sama; efek yang digambar **ke dalam canvas cache**
   ikut beku (smear ayunan patah-patah, flash hanya berganti tiap 2 frame).
2. **Canvas di-smoothscale.** Skala pipeline hero ≈ 0.75–0.8, jadi FX
   in-canvas ikut menyusut dan lembek — bukan chunky pixel-art.
3. **Tidak ada animation controller bernama.** `_update_attack_anim`
   menghitung `_razak_attack_progress` untuk pose, tapi tidak ada nama fase,
   prioritas state, delta-time — tidak ada yang bisa ditanya "sekarang fase
   apa, sudah berapa detik".
4. **Tidak ada game feel.** Damage instan melee & skill AOE di
   `bosses/base_boss.py` tidak memicu hit-stop, shake, atau impact FX.
5. **Tidak ada particle/projectile system hidup.** Molotov v2
   (`NapalmProjectile`/`NapalmPatch`) digambar ke canvas dan ikut kuantisasi.

## 2. Pemecahan: pisahkan badan dari efek

| Lapisan | File | Memiliki |
|---|---|---|
| **Renderer (badan + telegraph)** | `bosses/level2.py :: _NS_razak` | rig masterwork v2, palet, pose & keyframe machete, controller timer serangan, marker tanah Q/W/E/R, pita/impact **fallback** saat modul FX tidak dimuat |
| **Lapisan hidup 1:1** | `heroes/razak_fx.py` (baru) | trail machete api dari histori posisi nyata, particle system berbatas, molotov napalm dengan lifecycle penuh, SkillFX Q/W/E/R, impact FX, animation state machine cermin, hit-flash, overlay debug |
| **Bus game feel (shared)** | `heroes/combat_feel.py` | hit-stop global 0.03–0.08 s, screen shake meluruh, delta-time frame — dipakai bersama Zephyr & Gornak |

Jaminan arsitektur (sama dengan kontrak Gornak v3):

* lapisan hidup digambar **di luar** sprite cache → 60 fps sejati pada skala
  layar 1.0, tidak pernah menyusut atau beku;
* renderer tetap satu-satunya pemilik **geometri badan** — lapisan hidup
  *membaca* `_grip_screen / _tip_screen / _gun_end_screen /
  _swing_hitbox / _resolve_pose` lewat jembatan malas (`_renderer()`), jadi
  bilah, trail, dan hitbox tidak mungkin beda frame;
* kalau `heroes.razak_fx` gagal diimpor, `owns()` = False dan renderer
  menggambar pita + impact pop in-canvas sendiri — visual kehilangan
  polish, **tidak pernah** kehilangan efek;
* **nol perubahan gameplay/balance**: damage tetap milik
  `bosses/base_boss.py` (`_razak_q/w/e/r`) dan `_entity.py`; lapisan hidup
  hanya *membaca* state (`active_skill`, `active_skill_timer`,
  `_razak_attack_progress`, `hp`, `alive`) dan mendeteksi tepi
  (edge-triggered).

## 3. Isi `heroes/razak_fx.py`

| Komponen | Ringkasan |
|---|---|
| `RAZAK_PALETTE` | kontrak 9 kunci (`outline..fx`) + ramp api (`fire_*`), bat (`bat_*`), kulit/samak/kuningan/baja/asap/goggle biru; disinkronkan dari `_NS_razak.PALETTE` lewat `_PALETTE_SYNC` (satu karakter, satu warna) |
| `Particle` | `position, velocity, acceleration, life, max_life, size, rotation, rotation_speed, alpha, gravity, color, color_end, drag, fade_pow`; bentuk: `pixel, glow, spark, shard, streak, ember, smoke, fire` — hard-edge, pixel-snapped |
| `ParticleSystem` | pool reusable + cap keras (`MAX_PARTICLES=170`), `spawn/burst/stream/update/draw`, lapisan `back/front`, jumlah mengikuti preset kualitas mobile (`particle_budget`) |
| `SwingTrail` | histori `(grip, tip, umur)` → **sector cincin** yang disapu ujung bilah (pita ramping di tepi luar + inti + glint putih), umur 0.26 s, potong strip saat arah berbalik, sapuan total dibatasi `MAX_SWEEP=1.95`; murni turunan lintasan bilah |
| `ImpactFX` | flash bintang 8 arah kompak, shockwave elips berarah, spoke debris, 3 slash-fragment busur, kritik pilar emas; varian `slash/napalm/flame/dash/storm/hurt` |
| `RazakProjectile` | kontrak penuh `position/velocity/speed/damage/lifetime/target/radius/rotation/trail/particles/active`; lifecycle `SPAWN→TRAVEL→TRAIL→HIT→IMPACT→DESTROY`; arc parabolik, botol kuningan berputar + sumbu menyala + trail asap→api, tumbukan radius vs target, callback `on_impact`; **visual-only** (damage tetap di `base_boss._razak_q`) |
| `ProjectileSystem` | cap 12, spawn/update/draw + auto-cleanup |
| `SkillFX` | lifecycle `CAST→CHARGE→RELEASE→AREA→IMPACT→FADE` untuk Q/W/E/R: kolam napalm lengket (Q), kerucut api 3 band ke target (W), lompat firefly + landing (E), 8 pilar api mengorbit + erupsi (R) |
| `RazakFXDirector` | satu per unit: state machine + event FX (lihat §4) |
| `draw_debug_overlay` | `DEBUG_CHARACTER=True` → hitbox ayunan, hurtbox, attack range, lingkar tumbukan proyektil, jangkar bilah, state/fase/FPS/jumlah partikel/timer skill |
| API modul | `attach / owns / director_for / tick / reset_all / total_particles / total_projectiles / draw_ground_layer / draw_live_layer / notify_melee_impact / notify_projectile_impact / notify_skill_impact / notify_skill_cast / notify_hurt / spawn_napalm / hit_stop / shake / should_freeze_frame / clear_cache / cache_size / attack_phase / pose_of / machete_points / gun_end` |

## 4. Animation controller (cermin renderer)

| State | Prioritas |
|---|---|
| `IDLE` 10 → `WALK` 20 → `RUN` 25 → `CHARGE` 40 → `ATTACK` 45 → `SWING` 50 → `CAST` 55 → `SKILL` 56 → `SPECIAL` 60 → `HIT` 62 → `HURT` 65 → `DEATH` 100 | angka besar = menang; DEATH mengunci |

Timeline serangan (satu sumber kebenaran, dibaca dari renderer):

```
ATTACK_PHASES = (
  ("ANTICIPATION", 0.00, 0.09), ("WINDUP", 0.09, 0.30),
  ("SWING", 0.30, 0.50), ("IMPACT", 0.50, 0.62),
  ("FOLLOW", 0.62, 0.80), ("RECOVERY", 0.80, 1.00))
ATTACK_WINDUP_END = 0.30; ATTACK_SWING_END = 0.62
```

Keyframe `_attack_pose(ap)`: 0 / 0.14 / 0.30 / 0.48 / 0.54 / 0.72 / 1.0 —
machete ditarik ke belakang (`arm_a -2.35`), ayunan tercepat (0.48),
**IMPACT** (0.54, squash + bintang), follow rebound (0.72). `impact`
adalah `1 - |ap - 0.54| / 0.10`.

Jembatan renderer (dipakai lapisan hidup, tidak ada salinan geometri):

* `_resolve_pose(boss, moving) → (action, phase, ap)` — persis dispatch
  renderer (dash > attack > walk > idle);
* `_machete_grip_local / _machete_tip_local` — ruang lokal rig (arm 14 px,
  blade 28 px, sudut blade = `arm_a + π/4·facing`);
* `_gun_end_local` — moncong flamethrower (Q/W origin api);
* `_local(boss, x, y, ...)` — shift badan (lunge/bob/lean/tremble/sway)
  diterapkan **sekali** lalu `× SCALE`, sehingga FX tidak pernah lepas
  dari badan;
* `_swing_hitbox(boss, x, y)` — AABB grip→tip + pad 10, aktif hanya
  `0.30 ≤ ap ≤ 0.78`.

## 5. Skill FX: pusat & lifecylce

| Skill | Nama | Radius dunia | Total (dtk) | Pusat |
|---|---|---|---|---|
| Q | Sticky Napalm | 75 | 1.05 | target (ledak di titik mendarat molotov) |
| W | Flamebreak | 95 | 1.00 | arah moncong (kerucut ke target) |
| E | Firefly Dash | 80 | 0.90 | landing (posisi BARU setelah dash) |
| R | Firestorm | 180 | 1.85 | caster (8 pilar mengorbit) |

Sinkronisasi impact:
* **Q**: renderer hanya memberi *timing window*
  (`boss._razak_live_proj_window = True` saat `_spawn_napalm` dipanggil);
  lapisan hidup melempar molotov di koordinat layar 1:1 dari `gun_end`,
  dan `on_impact` membuat kolam + ImpactFX. Kalau lapisan hidup tidak
  dimiliki, molotov v2 canvas tetap jalan (fallback).
* **W**: director memantau `active_skill_timer` → `d.impacted()` di 55%
  durasi (momen damage AOE) — skill tidak pernah di-paksa phase.
* **E**: director mendeteksi lompatan `> 24 px` dalam satu frame saat
  `skill == "e"` → `on_dash_land(x, y)`.
* **R**: `d.impacted()` di 35% durasi (erupsi) + `_feel_hit_stop(0.06)`.

## 6. Impact & game feed (bus SHARED)

`notify_melee_impact(hero, target, damage, crit)` — dipanggil dari
`_entity.py` (`hero_type == 'razak'`, melee instan) dan
`bosses/base_boss.py` (`boss_type == 'razak'`): flash bintang kompak,
3 slash-fragment, shockwave elips, spoke debris, particle burst
(streak/shards/smoke), `shake(4.0+3.4·pw)`, dan hit-stop
`0.036 + 0.019·pw (+0.014 kritik)` — diklem bus ke 2–5 frame simulasi
(= 0.033–0.083 s).

`notify_projectile_impact(...)` — jalur proyektil generik `_entity.py`
(range 130 → serangan dasar hero Razak mendarat lewat bolt generik).

`notify_skill_impact(...)` — Q/W/E/R dari base_boss; W/E/R memakai
dedupe per-kind dalam window 0.16–0.18 s supaya tidak dobel.

Dedupe: `_impact_dedupe` memakai `(kind, x, y, time)`; `ImpactFX` maks
`MAX_IMPACTS=8`; `SkillFX` maks `MAX_SKILLS=4` (yang tua dibuang).

## 7. Supresi ganda & fallback

Renderer (`draw_razak`) memanggil `_live_fx(boss, surface, x, y,
want_draw, portrait)`:

* jalur boss (`want_draw=True`): `draw_ground_layer` dipanggil langsung di
  sini, lalu `draw_live_layer` setelah foreground — tidak ada dobel;
* jalur hero (`render_hero`): `heroes/__init__._live_fx_pre/_post` yang
  menggambar dua lapisan itu, renderer hanya `attach(boss)`;
* `_fx_owned(boss) == True` → renderer **menekan** pita canvas, shockwave,
  ground patches, molotov v2, dan foreground skill canvas;
* `RAZAK_FX_ENABLED == False` / import gagal → `owned == False` → semua
  fallback canvas hidup seperti sebelum rewrite (kompatibilitas penuh).

## 8. Integrasi engine

| Titik | Perubahan |
|---|---|
| `heroes/__init__.py` | `"razak"` di `_LIVE_FX_HEROES` dan `_LIVE_FX_PATHS` |
| `_core.py` | `"razak_fx"` pada loop partikel HUD debug |
| `_entity.py` | `hero_type == 'razak'` → `notify_melee_impact` (melee) & `notify_projectile_impact` (bolt generik, range 130) |
| `bosses/base_boss.py` | `boss_type == 'razak'` → `notify_melee_impact` (melee machete) & `notify_skill_impact` (W/E/R) |
| `bosses/level2.py` | jembatan `_live_module/_live_fx/_fx_owned` + `boss=boss` threading + `_spawn_napalm` handshake |

## 9. Verifikasi

```
python3 -m pytest tools/test_razak_v3_combat.py -q     # 40 tes kontrak
python3 tools/_audit_razak_v3.py                        # 48 cek + 7 lembar preview
python3 tools/test_level2_masterwork.py                 # gate renderer level2
```

Mustahil gagal diam-diam: audit memeriksa palet sinkron, busur ayunan,
trail berisi & meluruh, cap partikel, lifecycle proyektil + skill,
hit-stop 2–5 frame, shake kembali 0, supresi ganda, aftermath bersih
(0 partikel setelah 420 frame), API publik lama utuh (54/54), dan budget
frame. Lembar preview ditulis ke `docs/razak_v3_*.png`.
