# SYLARA — GODOT-NATIVE WIND RANGER RIG (REBUILD)

> Referensi kualitas & gerak: **Wind Ranger (Dota 2)** — elven archer.
> Render: **100% kode, nol aset** (seluruh bentuk dari primitif `_draw()`).
> Logika: **Godot native** — sinyal event-driven, observasi state read-only,
> dan tween/timer engine. Seluruh logika pygame yang tertinggal di rig lama
> (release-first karena "paritas pygame", kontrak zero-impact FX, workaround
> monotonic ap, state swing melee, komentar paritas) **dihilangkan**.

## 1. Arsitektur (satu script = satu tanggung jawab)

```
SylaraSkeleton.tscn
└── SylaraSkeleton (root Node2D, class_name SylaraSkeleton)
    │     state machine + blending pose + drive() API + sinyal
    ├── Renderer  (SylaraRenderer.gd)   pose → _draw() berlapis, 360° aim
    ├── SkillFX   (SylaraSkillFX.gd)    sinyal → rangkaian VFX pooled
    └── Feel      (SylaraCombatFeel.gd) sinyal → audio + shake + hit-stop
```

Mendukung (script terpisah, dipakai-ulang):

| Berkas | Isi |
|---|---|
| `SylaraAnimator.gd` | state → pose target (tulis pakai-ulang, nol alokasi) |
| `SylaraPose.gd` | data pose tulang + aura + tether |
| `SylaraArrow.gd` | visual proyektil basic attack (subclass TowerBullet, hanya `_draw`) |
| `SylaraPalette.gd` | warna terkontrol (BASE→SHADOW→HIGHLIGHT→MAGIC ACCENT) |

## 2. Pola Godot native yang dipakai

- **Event-driven via sinyal** — root memancarkan:
  - `bow_released` — tali dilepas (setiap tembakan: awal siklus ATAU wrap ap);
  - `skill_cast(key)` — skill mulai;
  - `skill_released(key, aim_point)` — momen Powershot TEBAR (charge habis);
  - `character_hurt` / `character_died` — showcase.
  SkillFX & Feel **menghubungkan** sinyal di `_ready()` — tidak ada polling
  `_process` di lapisan FX/feel.
- **Observasi state hero (read-only)** — animasi skill disinkronkan ke
  timer kit hero **asli** (`_focus_fire_timer` 180, `_windrun_timer` 180,
  `_shackle_timer` 150, `_powershot_timer` 60 frame) — bukan durasi
  perkiraan. Fallback durasi tetap hanya untuk demo standalone.
- **Bidik 360°** — root mengubah posisi target (dunia) ke ruang lokal rig
  (otomatis membatalkan flip `scale.x` Hero), lalu me-smooth dengan
  `lerp_angle` (rate 16/s). Busur berputar bebas mengikuti target; tubuh
  tetap menghadap sumbu hadap (twist torso/kepalanya halus).
- **Impact terjadwal lewat Tween node** — impact Powershot = 0.35 dtk
  setelah tebar (momen mendarat kerucut). Tween milik node Feel: kalau rig
  dibebaskan duluan, callback ikut mati (aman freed-instance).
- **Kematian arena via sinyal `GameManager.hero_died`** — hero di-hide alur
  respawn, tapi paket perpisahan angin tetap menyala (aktor VFX hidup di
  layer dunia, bukan di bawah node hero).

## 3. Pemetaan skill ke Wind Ranger (Dota 2)

Gameplay kit (damage/cooldown) **tidak diubah** — milik `HeroSkillKit.gd`
(shared, terkunci test paritas). Yang di-rewrite total adalah **gerak &
rasa visual**:

| Skill game | Wind Ranger | Durasi (frame) | Perilaku visual |
|---|---|---|---|
| **Q — Focus Fire** | Focus Fire (attack speed) | 180 (3 dtk) | Tembak cepat (siklus attack loop) + aura cincin energi di busur + streak per-panah ke target asli + ring lock-on di target |
| **W — Windrun** | Windrun (move speed + evasion) | 180 (3 dtk) | Burst gale 6-arah + cincin aura 70px + trail angin di belakang (digambar renderer, gratis) + sprint pose condong |
| **E — Shackle Shot** | Shackle Shot (root target) | 150 (2.5 dtk) | Cast: angkat-draw-snap; sulur melesat nock→target; lalu pose tahan + **tether sulur** ke target (quadratic bezier + node daun + cincin akar denyut, digambar renderer selama buff) |
| **R — Powershot** | Powershot (channel → shot) | 60 (1 dtk) | Channel: kuda-kuda lebar, full draw, tremor di puncak, sedotan angin, garis bidik putus-putus; **TEBAR** saat charge habis (deteksi transisi state): lunge + kerucut 5 panah + gale tunnel + impact terjadwal (hit-stop 0.04 + shake 0.12) |
| **Basic attack** | — | per cooldown | Siklus loop tembak: RELEASE→FOLLOW→RAISE→DRAW (wrap). Panah `SylaraArrow` (wind arrow: kristal + fletching zamrud + jejak angin) lahir dari nock busur. Kilatan tali-snap kecil di setiap lepas (1 aktor, 0.08 dtk) — ringan, tanpa hit-stop/shake |

### Siklus serangan (loop tembak beruntun)

Dengan fire-rate cepat (mis. Focus Fire), siklus dasar adalah SATU LOOP
kontinu — `RELEASE (0.00) → FOLLOW-THROUGH (0.14) → RAISE (0.46) →
DRAW (0.64) → wrap → RELEASE`. Lepas tali diletakkan di DEPAN siklus (di
sini `Hero._shoot_projectile` sudah melepas proyektilnya) sehingga
tembak-beruntun terbaca sebagai pemanah sungguhan: setiap tembakan adalah
hasil DRAW ekor siklus sebelumnya. `bow_released` terpicu oleh (a) masuk
state attack, atau (b) **ap wrap** (attack_timer di-set ulang oleh hero).

## 4. Logika pygame yang DIHILANGKAN dari rig

| Lama (port pygame) | Sekarang (Godot native) |
|---|---|
| Release-first dipaksakan + dikunci komentar "paritas pygame, tidak boleh digeser" | Siklus loop penuh yang didesain utuh; posisi release = hasil desain animasi, bukan constraint port |
| State `swing` melee (riposte saat target ≤ 64 px) + `last_attack_kind` | Dihapus — Wind Ranger murni ranged; tidak ada melee |
| Workaround ap monoton (`_prev_ap` anti-geser) karena semantik timer pygame | ap wrap dideteksi sebagai event tembak baru (perilaku normal Godot) |
| Kontrak "basic attack = ZERO impact FX/shake/hit-stop (kontrak test pygame)" | Design decision feel: kilatan tali-snap kecil (visual), tanpa hit-stop/shake |
| Skill progress = `skill_t / 3.0` (perkiraan durasi tetap) | Dibaca dari timer kit hero asli (180/180/150/60 frame) |
| Death anim = "kontrak paritas hide instan" | Kematian arena = alur respawn game (hero di-hide); VFX perpisahan via sinyal `GameManager.hero_died`; state death showcase via `play("death")` |
| Semua komentar/justifikasi "paritas pygame" di rig | Justifikasi desain (referensi Wind Ranger) |

## 5. Kontrak integrasi (TIDAK berubah, jadi `Hero.gd` utuh)

- `drive(phase, action, attack_progress, facing, is_moving, skill, delta)`
  — dipanggil `Hero._drive_visual` tiap physics frame (duck-typed,
  sama untuk semua rig).
- `handles_skill_fx(key) -> true` — Hero melewatkan FX skill generik.
- `spawn_attack_projectile(t, dmg) -> Node2D` — opt-in: `Hero._shoot_projectile`
  memakai `SylaraArrow` dengan parameter TowerBullet identik (speed 520,
  team, school, source); perilaku homing/hit/damage diwarisi TowerBullet.
- Digambar menghadap **+x**; flip `scale.x` dilakukan Hero di `Visual`.
- `RendererRegistry.HERO["sylara"]` tetap menunjuk
  `res://scenes/hero/sylara/SylaraSkeleton.tscn` (flag
  `mystic/rendering/experimental_hero_rigs` default ON; fallback bake
  strip pygame untuk rig LAMA — rig ini sendiri 100% kode).

## 6. Anggaran performa (Android)

- **1 CanvasItem** per karakter (semua layer di satu `_draw()`).
- **Nol alokasi per frame**: pose pakai-ulang (2 instance), Dictionary FK
  per-draw (murah, tak terakumulasi), tidak ada `Pose.new()`/`instantiate()`.
- **VFX pooled** (`VFXManager`, 32 aktor arena): tiap skill ≤ ~12 aktor
  puncak; aura per-durasi (trail, tether, cincin fokus, garis bidik)
  digambar **renderer** — nol aktor pool selama buff berjalan.
- **Audio** via `AudioManager` (throttle engine): basic attack = suara
  hero_ranged (Hero), cast = `hero_skill` (kit), R = `hero_ranged` di tebar
  + `explosion` 0.22 di impact.
- Sprite legacy `Hero.tscn` tetap di-disable oleh `setup_visual()` (jalur
  registry).

## 7. Berkas yang pernah ada & dihapus (histori rebuild v1)

Rebuild v1 (2026-09) menghapus legacy `Sylara.gd`, `SylaraCombat.gd`,
`SylaraSkill.gd`, `SylaraHitFeedback.gd`, `SylaraArrow.gd` (versi lama),
`SylaraAura.gd`, dan scene `Sylara.tscn` — semuanya diganti arsitektur
modular di atas. Rebuild **v2 (dokumen ini, 2026-09-16)** menulis ulang
logika seluruh rig menjadi Godot native (lihat bagian 4) — nama berkas &
skena tetap, kontrak `Hero.gd` utuh.

## 8. Demo & verifikasi

```
godot --path godot res://scenes/demo/SylaraDemo.tscn
```

Sejak 2026-09-17 `SylaraDemo.tscn` memamerkan **rig satu file V10.5**
(`SylaraV105.tscn`, lihat bagian 9) — bukan siklus auto `drive()` rig
modular di atas. Keyboard desktop (lapisan tipis demo, bukan milik rig):
`WASD`/panah gerak, `SPACE` attack, `1/2/3/4` Q/W/E/R, `H` hurt,
`K` death, `L` revive. Sentuh: joystick + tombol bawaan rig
(ATTACK/Q/W/E/R + HURT/DEATH/REVIVE).

Rig modular bagian 1-7 tetap menjadi **visual arena** Sylara
(`RendererRegistry.HERO["sylara"]`, dikunci `GameplayParityTest`) dan
diverifikasi lewat arena main + suite parity. CI statis: `gdparse` +
`godot/tools/tscn_lint.py` + `check_refs.py` + `particles_lint.py`;
CI runtime: `godot-check.yml` (engine headless + suite parity).
Gameplay Sylara (damage/CD/W- evade/R powershot) dikunci
`HeroSkillParityTest` & fixture `match_parity.json` — tidak tersentuh.

## 9. Sylara V10.5 — rig satu file standalone (`SylaraV105.gd`)

Selain rig modular arena di atas, Sylara juga punya versi **satu file**
(sekalian jadi arena uji karakter solo): `scenes/hero/sylara/SylaraV105.gd`
+ `SylaraV105.tscn`. Semua logika dalam SATU script `CharacterBody2D`:

| Fitur | Detail |
|---|---|
| **Kamera dinamis** | `Camera2D` dibuat script di `_ready()`; `position_smoothing_speed = 6.0` (smooth lag — Sylara melesat mendahului kamera) |
| **Windrun sprint** | toggle (bukan durasi): `windrun_speed = 480` px/dtk (vs 200 jalan); analog lepas → otomatis lanjut lari ke arah aim; kaki animasi 0.04 dtk |
| **Ghost trail** | tiap 0.04 dtk saat windrun, bayangan sprite windrun (tinta hijau, alpha 0.7 → 0) mengikuti posisi — digambar `_draw()` sendiri, tanpa node tambahan |
| **Skill** | basic attack (frame 3), Q Focus Fire (tembak cepat frame 1/3), W Windrun (toggle), E Shackle Shot (tornado expanding di depan), R Powershot (channel 6 frame + panah 1100 px/dtk) |
| **UI mobile bawaan** | `CanvasLayer` + joystick virtual (inner class `TouchJoystick`) + tombol ATTACK/Q/W/E/R + tombol tes HURT/DEATH/REVIVE |
| **Dunia** | grid rumput 64px + pohon/batu prosedural (31×21 grid, cull ±600×400 px) agar perpindahan terasa jelas |
| **Glow** | `WorldEnvironment` + `Environment.glow` (blend SCREEN) — dibuat script |

Aturan pakai:
- **Standalone**: `SylaraV105.tscn` langsung (F5) atau `SylaraDemo.tscn`
  (HUD + keyboard desktop).
- **TIDAK untuk arena**: script ini CharacterBody2D utuh — gerak, input,
  kamera, WorldEnvironment, UI semua miliknya. Arena sudah punya
  CharacterBody2D (Hero) + kamera frame + layout mobile sendiri; menaruh
  rig ini di bawah `Hero/Visual` akan bentrok (nested body, kamera kedua,
  UI ganda). Arena Sylara tetap rig modular `SylaraSkeleton.tscn`.
- Script V10.5 adalah sumber kebenaran karakter (dipertahankan apa adanya
  saat integrasi) — fitur baru Sylara masuk ke sini dulu, baru dipertimbangkan
  sinkronisasi ke rig modular.
