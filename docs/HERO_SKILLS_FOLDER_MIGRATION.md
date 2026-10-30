# Migrasi folder `hero_skills/` (Pygame) → Godot

Status: **selesai — dua berkas terklasifikasi penuh, dan satu perilaku yang belum
punya rumah native sudah diport di layer ini (9by).**

Sumber: `hero_skills/` (read-only oracle) · **2 berkas** · 5.348 baris.
Target: `godot_rebuild/` · `scripts/combat/*_skills.gd` (27 kit) +
`skill_common.gd` + `boss_skill_common.gd` + `skill_feedback.gd` + resolver
`minion_battle.gd` / `boss_recipe_registry.gd`.

Folder ini kecil di disk tetapi besar jangkauannya: `_bundle.py` adalah
gabungan **delapan** modul skill Pygame, jadi ia memuat API dasar yang
diwarisi semua kit hero, registri 66 resep bos, dan enam kit starter.

---

## 1. Cara membaca laporan ini

`tests/hero_skills_folder_source_oracle.py` menurunkan inventaris **dari berkas
sumber** dengan `ast` (tidak ada yang dieksekusi, jadi tidak butuh pygame,
`settings`, atau `sound_manager`). Hasilnya ditulis ke
`tests/fixtures/hero_skills_folder_source.json`; validator membandingkannya
setiap kali jalan, dan `tests/hero_skills_folder_checks.gd` menuntut proyek
Godot mempertanggungjawabkan setiap entri.

| Bagian sumber | Yang diekstrak |
|---|---|
| `BaseSkill` | 28 method, `REQUIRE_TARGET`, `TARGET_RANGE_SLACK` 1.15, `_DEFAULT_VISUAL_DURATION`, `SKILL_VISUAL_DURATION` kelas, dan tabel shake/volume tiap `_trigger_*_cooldown` |
| `BossHeroSkills` | 273 method, `_SKILL_REGISTRY` 66 bos / 264 method cast, `BOSS_HERO_VISUAL_DURATION`, shake `cast_*`, gerbang `max(skill_range, 140)`, dan `_fallback_cast` |
| 6 kit starter | 39 method, `SKILL_VISUAL_DURATION` per hero, dan shake tiap pemanggilan `_trigger_*_cooldown` |
| `__init__.py` | API `register_handler`/`get_skill_handler`, 7 submodul alias, 6 starter terdaftar, dan loop auto-register 216 bos |

Label status: **Diport** (ada padanan native + dikunci tes), **Diport (baru)**
(ditambahkan layer ini), **N/A** (konsep Python tanpa padanan runtime).

---

## 2. `__init__.py` — 128 baris

| Isi sumber | Padanan Godot | Status |
|---|---|---|
| `SKILL_HANDLERS` + `register_handler` + `get_skill_handler` (registri nama → kelas handler) | resolver runtime: `MinionBattle.NATIVE_SKILLS`, `BossRecipeRegistry.handler()`, `SourceSharedBossSkills.IDS` | **Diport** |
| `_EXTRA` / `_PLAIN_SYMS` + `_install_aliases()` — mendaftarkan 7 nama submodul lama (`boss_hero_skills`, `grimjaw_skills`, `kaizen_skills`, `sylara_skills`, `thorne_skills`, `vex_skills`, `zephyr_skills`) + `base_skill` ke `sys.modules` | tidak perlu: Godot memakai `preload` eksplisit; peta aliasnya tetap dilacak di fixture | **N/A** |
| Auto-register 6 starter (`_BASE_HERO_MODULES`) | lima kit native (`thorne/grimjaw/sylara/vex/zephyr_skills.gd`) + kaizen inline di `minion_battle.gd` | **Diport** |
| Auto-register **semua** tipe bos ke `BossHeroSkills` saat import | 66 resep native + 150 fallback sumber = 216, lewat resolver yang sama dengan pertandingan | **Diport** |

Kuirk sumber: alias `sys.modules` itu ada hanya karena delapan berkas aslinya
dihapus dan digabung ke `_bundle.py`; baris impor lama tetap harus jalan. Tidak
ada perilaku permainan di dalamnya.

---

## 3. `_bundle.py` — 5.220 baris, delapan modul

### 3.1 `BaseSkill` (28 method) — API dasar semua kit

| Kelompok | Isi | Padanan Godot | Status |
|---|---|---|---|
| Abstrak | `init_state`, `update_timers`, `cast_q/w/e/r` | tiap kit native punya `IDS`, `can_cast`, `cast` | **Diport** |
| Sweep musuh | `_get_enemies`, `_get_enemies_in_range`, `_deal_aoe_damage` | `skill_common.gd::enemies`, `boss_level_*_skills.gd::_radial`, `Common.hit(attributed)` | **Diport** |
| Debuff | `_apply_slow`, `_apply_stun` (pakai `max`, tidak pernah memperpendek) | `world.apply_slow`, `skill_common.gd::stun` (guard `StructureState`) | **Diport** |
| Guard target | `REQUIRE_TARGET`, `TARGET_RANGE_SLACK` 1.15, `_skill_range` (fallback 200), `_acquire_target`, `_has_target` | `minion_battle.gd::_has_q_target`, `hero_definition.q_reach_slack`, `Common.bound_target` | **Diport** |
| Cooldown | `_check_*_cooldown` | `skill_common.gd::ready` | **Diport** |
| Visual | `_DEFAULT_VISUAL_DURATION` 60/90/60/100, `SKILL_VISUAL_DURATION`, `_get_visual_duration`, `_set_active_skill` | durasi di-hardcode per kit (`Common.trigger(hero, key, N)`), `hero.active_skill(_timer)` | **Diport** |
| Efek | `_shake_screen`, `_play_skill_sound` (hanya tim biru), `_shake_screen` 8/5/6/15, volume 0.7/0.6/0.7/1.0 | `scripts/combat/skill_feedback.gd` + `AudioManager.play_scaled` | **Diport (baru)** |
| Popup | `_add_popup` (angka damage manual) | `EffectManager` floating text lewat `world._deliver_hit` | **Diport** |

### 3.2 `BossHeroSkills` (273 method)

| Isi | Angka | Padanan Godot | Status |
|---|---|---|---|
| `_SKILL_REGISTRY` | 66 bos × 4 slot = **264** method `_cast_*` | 20 modul `boss_level_*_skills.gd` + `alchemist_skills.gd` (65 + 1 = 66) | **Diport** |
| `_generic_cast` | cek cooldown → guard musuh `max(skill_range, 140)` → retarget terdekat → panggil metode resep → `cooldown_trigger` | `boss_skill_common.gd::can_cast` + `can_cast/cast` tiap modul | **Diport** |
| `_fallback_cast` | 150 bos sisanya; multiplier 1.0/1.2/1.5/2.5, AOE 150 (E) / 200 (R), visual 40 | `source_shared_boss_skills.gd` (audited 150) | **Diport** |
| `BOSS_HERO_VISUAL_DURATION` | `nyzrak` 50/50/70/90, `vhalzun` 60/80/60/100; presedensi per-hero → kelas → default | tabel `VISUAL` di `boss_level_three_skills.gd` dan `boss_level_five_skills.gd` | **Diport** |
| `cast_q/w/e/r` | shake 10/8/8/15 | `SkillFeedback.BOSS_SHAKE` | **Diport (baru)** |

Catatan penting soal sumber: `cooldown_trigger` di `_generic_cast` **menimpa**
`active_skill_timer` yang baru diset metode resep dengan durasi default kelas
(60/90/60/100). Jadi angka `h.active_skill_timer = N` di dalam 264 method resep
adalah nilai mati; yang berlaku hanya default + dua override di atas. Port
native memakai yang berlaku, bukan yang mati.

### 3.3 Enam kit starter (39 method)

| Hero | `SKILL_VISUAL_DURATION` | Shake per slot | Padanan Godot | Status |
|---|---|---|---|---|
| `kaizen` | 60 / 90 / 60 / 100 | 8 / 5 / 6 / 15 | inline `minion_battle.gd` (`q_visual_ticks`, 90/60/100) | **Diport** |
| `grimjaw` | 180 / 90 / 60 / 90 | 8 / 5 / 6 / 15 | `grimjaw_skills.gd` | **Diport** |
| `sylara` | 180 / 180 / 150 / 60 | 8 / 5 / 6 / 15 | `sylara_skills.gd` | **Diport** |
| `thorne` | 40 / 100 / 60 / 120 | **6** / 5 / **8** / 15 | `thorne_skills.gd` | **Diport** |
| `vex` | 40 / 100 / 60 / 80 | 8 / 5 / 6 / 15 | `vex_skills.gd` | **Diport** |
| `zephyr` | 240 / 180 / 180 / 240 | 8 / 5 / 6 / 15 | `zephyr_skills.gd` | **Diport** |

Kuirk sumber yang dipertahankan: `ThorneSkills` menukar intensitas Q dan E
(6 untuk Q, 8 untuk E) sementara kelima starter lain memakai default 8/5/6/15.
Itu bukan salah tulis — nilainya diteruskan apa adanya di `SkillFeedback`.

---

## 4. Yang ditambahkan layer ini: feedback cast

Sebelum 9by, jalur skill hero di Godot sama sekali tidak menghasilkan dua efek
yang sumber jalankan di **setiap** cast sukses (`_trigger_{q,w,e,r}_cooldown`):
`_shake_screen` dan `_play_skill_sound`. `AudioManager` pun belum punya
`volume_mult`, sehingga 0.6/0.7/1.0 milik sumber akan hilang walaupun suaranya
diputar.

| Berkas | Isi |
|---|---|
| `scripts/combat/skill_feedback.gd` (baru) | `DEFAULT_SHAKE` 8/5/6/15, `BOSS_SHAKE` 10/8/8/15, `STARTER_SHAKE` (6 hero, thorne ditukar), `VOLUME` 0.7/0.6/0.7/1.0; `apply()` mengembalikan `{shake, volume, sound}` supaya bisa diuji headless |
| `scripts/audio/audio_manager.gd` | `play_scaled(key, volume_mult)` = throttle 50 ms per nama + `master*sfx*volume_mult` (klamp 0..1), plus `play()` mengembalikan volume mix setelah cast berskala |
| `scripts/audio/audio_runtime.gd` | `play_scaled` sebagai jembatan aman untuk scene maupun runner headless |
| `scripts/match/prototype_battle.gd` | `_trigger_source_cast_feedback()` dipanggil di keempat titik masuk cast (`cast_hero_q/w/e`, `_cast_hero_r`), bersebelahan dengan hook hit-stop yang sudah ada |

Deviasi & batasan yang dicatat:

* Shake dikirim ke `EffectManager` yang sama dengan shake bos; ia mengakumulasi
  dengan `max` dan meluruh per tick, jadi dua cast beruntun tidak menumpuk
  melebihi intensitas terbesar — sama seperti sumber.
* Tim merah tetap mengguncang layar (sumber melakukannya tanpa melihat tim)
  tetapi tidak memutar suara (sumber: `if self.hero.team == "blue"`).
* Throttle & volume hanya dipakai jalur skill; `play()` biasa tetap tanpa
  throttle seperti sebelumnya.

---

## 5. Bukti: apa yang mengunci apa

| Aspek | Oracle / fixture | Suite native |
|---|---|---|
| Inventaris 2 berkas + semua tabel | `hero_skills_folder_source_oracle.py` → `fixtures/hero_skills_folder_source.json` | `hero_skills_folder_checks.gd` |
| API `BaseSkill` | oracle: 28 method + konstanta guard | cek `skill_common.gd`, `boss_skill_common.gd` (140 px), `_has_q_target` |
| 66 resep + 150 fallback | oracle: `_SKILL_REGISTRY` 264 cast | resolver `RecipeRegistry.handler()` + `SharedSkills.IDS` (66 + 150 = 216) |
| Durasi visual | oracle: `SKILL_VISUAL_DURATION` per starter, `BOSS_HERO_VISUAL_DURATION` | string tabel `VISUAL` di modul kit + `q_visual_ticks` kaizen |
| Feedback cast | oracle: shake/volume per call site | `SkillFeedback` tabel + cast nyata (thorne 6, bos 10, merah senyap) |
| Registri handler | oracle: `register_handler`/`get_skill_handler`, 7 alias, auto-register | resolver native + preload 5 kit starter |

---

## 6. Sisa pekerjaan

Tidak ada bagian folder ini yang belum punya rumah native. Yang masih terbuka
berada di luar `hero_skills/`:

* verifikasi audiovisual di perangkat nyata: suite membuktikan **keputusan**
  (intensitas, volume, tim) tetapi tidak bisa mendengar atau melihat hasilnya;
* 136 bos tanpa resep tetap memakai `_fallback_cast` generik — itu perilaku
  sumber, bukan kekurangan port;
* tooltip/desc skill di UI tidak berasal dari folder ini (ada di
  `data/heroes/*.tres`).
