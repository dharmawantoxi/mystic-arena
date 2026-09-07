# Mystic Arena — Godot Edition

Port GPU dari versi `pygame-ce`. **Visual 222 unit kini hasil bake renderer
pygame asli** (Fase 5, Opsi A): `tools/convert_to_godot.py --units-png`
me-render 6 hero masterwork + 216 boss lewat choke point cache sprite game
(`_call_renderer_on_canvas`, `heroes/__init__.py:1729`) menjadi strip PNG
per unit di `assets/units/`, lalu `BakedSprite` (scene generik + manifest
`data/baked_units.json`) mengirisnya jadi animasi idle/walk/attack — jadi
pose, warna, dan proporsi identik dengan pygame tanpa port ribuan baris
renderer per boss. Kaizen tetap tertinggi kelasnya: rig `Skeleton2D` 19
tulang + shader hamon via `RendererRegistry.HERO` (urutan lookup: rig
custom > strip bake > `UnitSilhouette`).

Lapisan gameplay MOBA-nya juga sudah diport (2026-09-06): **menara 4 jalur + 18 slot bangun**, **nexus/castle dengan shield → menang/kalah**, **skill QWER**, **toko item 6 slot (33 item)**, dan **ekonomi identik pygame** (3 gold/s + 0.3/level, pengali difficulty, milli-gold). Lihat bagian "Gameplay yang sudah diport" di bawah.

**Menu utama + progresi level** juga jalan (sesi 2026-09-06 kedua): boot jatuh ke **MENU UTAMA** (`scenes/ui/MainMenu.gd`, state machine paritas `MenuState` pygame: MAIN / LEVEL_SELECT / HERO_SHOP / SETTINGS / HOW_TO_PLAY / CREDITS / PAUSE), pilih level 1–54 dari `levels.json` (nama, deskripsi, tema, mini boss, true boss, kunci `unlock_after_level`), HERO SHOP pakai meta gold, volume SFX/BGM tersimpan di save, dan setelah VICTORY tekan **ENTER** untuk lanjut ke level berikutnya (tema map + boss berbeda).

## Quick Start

```bash
# 1. Convert data pygame -> Godot JSON (222 hero, 216 boss, 54 level, 54 tema map)
#    Sekaligus menyalin assets/sounds/*.wav -> godot/assets/sounds/ (untuk AudioManager;
#    folder itu di-gitignore, jalankan ulang converter setelah clone).
#    Butuh pygame + SDL dummy (export_themes membaca map_components/themes.py):
python3 -m venv ~/.venv-mystic && ~/.venv-mystic/bin/pip install "pygame-ce==2.5.*"   # sekali saja
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy ~/.venv-mystic/bin/python tools/convert_to_godot.py

# 2. Buka di Godot 4.3+ (diuji di 4.7.2 Forward+)
godot godot/project.godot
# F5 -> MENU UTAMA -> MULAI GAME -> pilih kartu LEVEL 1 -> MAIN.
# Arena 1280x720: map forest, 2 nexus, 18 slot menara di 3 lane, 6 hero per tim,
# wave minion tiap 25 detik, mini boss sesuai levels.json (wave 10/15/25),
# true boss Abaddon setelah 6 menara Dire hancur, HUD + skill bar QWER + toko (B).
# Menang -> ENTER lanjut LEVEL 2 (tema desert, boss razak/khalros/gorath/alchemist).
```

### Kontrol pemain

| Input | Efek |
|---|---|
| **klik kiri** | pilih unit: hero Radiant (→ skill bar + toko) · menara milikmu (→ tab MENARA) · nexus (→ tab NEXUS) · lingkaran slot di lane (→ bangun menara) |
| `Q` `W` `E` `R` | cast skill hero yang sedang dipilih (bisa juga lewat tombol di skill bar) |
| `B` | buka/tutup toko (MENARA · ITEM · HERO · NEXUS) |
| `D` | ganti difficulty: easy (gold ×1.25) → normal (×1.0) → hard (×0.75 + enemy scaling) |
| `ENTER` | setelah VICTORY: **lanjut level berikutnya** · setelah DEFEAT: ulangi level |
| `R` | setelah menang/kalah: replay level yang sama (is_replay → reward 1500/200, bukan 3000) |
| `P` / `ESC` | menu PAUSE (RESUME / PENGATURAN / MENU UTAMA / KELUAR — paritas `MenuState.PAUSE`); ESC setelah menang/kalah = menu utama |

Hero Radiant yang tidak dipilih tetap bertarung sendiri (AI + auto-cast skill); yang dipilih berhenti auto-cast dan menunggu input QWER — sama seperti pygame.

### Tombol debug

| Tombol | Efek |
|---|---|
| `F1` | respawn roster (reset pertempuran, nexus & slot ikut dibuat ulang) |
| `T` | ganti tema map: siklus 54 palet dari `data/themes.json` (forest → desert → ice → volcanic → …) |
| `SPASI` | "beli" 1 hero random untuk Radiant (lewat `GameManager.try_buy_hero`) |

Untuk Kaizen showcase saja: double-click `godot/scenes/demo/KaizenDemo.tscn` → **Run Current Scene**.
Siklus idle 3s → walk 3s → attack loop (hamon kilat + wind ribbon). SPACE=force attack, F=flip, R=reset.

## "F5 cuma layar hitam" — penyebab & perbaikannya

Log dulu berhenti di `[GameManager] Start Level 1 — gold 1000` dan viewport tetap gelap. Itu **bukan**
crash: memang tidak ada satu node pun yang menggambar. Yang hilang (dan sekarang sudah ada):

1. `scenes/main.tscn` tidak punya script root — `start_level()` hanya `print` + emit signal, tidak ada
   yang men-spawn unit. → ditambah `scenes/main/Main.gd` (roster + wave + framing kamera).
2. `ArenaMap.tscn` berisi 4 `TileMapLayer` tanpa `tile_set` (`assets/tilesets/*.tres` belum dibuat),
   dan 2 `Sprite2D` toko tanpa texture → 0 piksel tergambar. → `ArenaMap.gd._draw()` sekarang
   menggambar terrain/lane/river/base/toko/decor prosedural memakai palette asli
   `map_components/themes.py` (54 tema via `data/themes.json`). Begitu
   `assets/tilesets/<tema>.tres` di-import, fallback otomatis mati.
3. `Camera2D` ada di (0,0), padahal arena 0..1280 × 0..720 → isi arena (mis. base Radiant di
   y=620) berada di luar view. → kamera dipusatkan ke (640,360) + `limit_*` dikunci ke ukuran arena.
4. `Boss.tscn` tidak punya visual sama sekali (AnimatedSprite2D kosong, partikel tanpa material) →
   boss tak terlihat walau menghajar hero. → `UnitSilhouette` (badan + tanduk) + boss bar + AI.
5. `Hero.gd` fallback kotak/`SpriteFrames` null tidak pernah tergambar. → default `UnitSilhouette`
   pygame; `autoplay` dihapus dari .tscn (menghilangkan error spam tiap spawn).
6. `Engine.time_scale` di-hit-stop diubah dari node unit yang bisa `queue_free()` di tengah `await`
   (game bisa "nyangkut" 0.05 ≈ layar tampak beku). → hit-stop pindah ke `GameManager` dengan
   watchdog waktu nyata.

Catatan kecil yang juga sudah dibereskan:

- `Color("rrggbb")` **tanpa `#`** di Godot = warna tidak valid (jadi hitam/transparan). `PALETTE`
  Kaizen dan palette map sekarang semuanya `Color("#rrggbb")`.
- `Color8()` tidak boleh dipakai di dalam `const` (bukan konstanta yang dikenali GDScript) —
  pakai `Color("#...")`.
- Cek statis tanpa engine:
  `python3 godot/tools/tscn_lint.py godot/scenes/*.tscn`,
  `python3 godot/tools/check_refs.py godot` (ext_resource, preload, dan `$Node/Path`), dan
  `python3 godot/tools/particles_lint.py godot` (properti CPUParticles2D vs GPUParticles2D).
- **CPUParticles2D ≠ GPUParticles2D.** Node CPU tidak punya `process_material`:
  semua parameter emisi adalah properti node (`direction`/`gravity` = **Vector2**,
  skala = `scale_amount_min/max`). Node GPU kebalikannya — semua di
  `ParticleProcessMaterial` (Vector3, `scale_min/max`). Tertukar = tidak ketahuan
  saat parse, tapi runtime melempar
  `Invalid assignment of property or key 'process_material' ... on a base object of type 'CPUParticles2D'`
  tepat saat FX dipakai. Semua partikel game (cuaca map, aura boss, burst hero,
  impact proyektil skill, wind Kaizen) memakai CPU supaya aman di renderer
  Compatibility Android/GLES; `particles_lint.py` menjaganya.

## Parse error: `Cannot infer the type` / autoload gagal dikompilasi

`var nilai := ekspresi` hanya aman kalau tipe ekspresi diketahui saat compile.
Hasil lookup `Dictionary` atau pemanggilan method lewat variabel dinamis
(seperti `db`, `cs`, atau `status`) tidak selalu bisa diinfer. Gunakan tipe
hasil yang eksplisit, misalnya `var p: Dictionary = db.passive(item_id)` atau
`var amount: float = cs.calc_skill_damage(hero, mult)`.

Deklarasi terkait sudah diperbaiki di `ItemInventory`, `SkillBook`, `CombatSystem`,
`TowerDB`, dan `Main`. Error kompilasi pada `Hero.gd` / `Tower.gd` serta kegagalan
autoload adalah efek berantai dari script dependensi, bukan scene yang hilang.

Validasi dengan **binary Godot** dari root repository (pemeriksa statis di atas
mengecek sintaks/referensi, bukan inferensi tipe GDScript):

```bash
godot --headless --path godot --editor --import
godot --headless --path godot --quit-after 120
```

Pastikan log tidak mengandung `SCRIPT ERROR`, `Parse Error`, atau `Compile Error`;
exit code editor saja tidak cukup karena Godot bisa tetap keluar dengan kode 0.

### Parse error: `Too many arguments for "get()"` di AIPlayer / Node

`Dictionary.get(key, default)` boleh menerima dua argumen, tetapi `Object.get(property)`
(hanya satu argumen) yang dipakai untuk node dari `get_nodes_in_group()` atau hero
hidup. Perbaikan terkait:

1. Lane minion di `AIPlayer._assign_hero_lane()` memakai `m.get("lane")` (bukan default).
2. Minion menyimpan `lane`, diteruskan `Main` lewat `GameManager.spawn_minion()` untuk
   kedua tim; default `"mid"`, argumen keempat tetap pengali stat.
3. `Hero.die` menaikkan `killer.kills` lewat `killer.get("kills")` (satu argumen).
4. `ItemDB.is_magic_hero` / `suggest_item` membaca role & range lewat helper yang aman
   untuk Node **dan** Dictionary (dipakai AI saat beli item).

Error `Main.gd: Failed to compile depended scripts` dan `Nonexistent function 'new'
in base 'GDScript'` adalah efek berantai karena script AI gagal dikompilasi — jangan
mengganti `.new()` atau menghapus AI dari Main. Uji regresinya (setelah import):

```bash
godot --headless --path godot res://tests/AIPlayerTest.tscn --quit-after 120
```

Harus muncul `[AIPlayerTest] PASS` tanpa error script. Tes memuat Main, memeriksa lane
wave kedua tim, dan memastikan AI memilih minion biru hidup terdekat di lane paling
ramai (atau menara terdekat jika tidak ada minion). Juga menutup regresi
`Object.get(prop, default)` pada `Hero.die` (atribusi kill) dan
`ItemDB.suggest_item` / `is_magic_hero` (dipakai AI beli item). Tes tidak memulai
match atau menulis save.

Smoke battle (menu → level 1 → hero/minion/wave/AI), setelah import yang sama:

```bash
godot --headless --path godot res://tests/BattleSmokeTest.tscn --quit-after 180
```

Harus muncul `[BattleSmokeTest] PASS` tanpa error script.

`Unable to open Android 'build-tools' directory` adalah masalah konfigurasi SDK
editor yang **terpisah**. Jika ingin export Android, instal Android SDK Build-Tools
melalui SDK Manager dan arahkan **Editor Settings → Export → Android → Android SDK
Path** ke root SDK (yang berisi folder `build-tools/`), bukan ke folder build-tools
itu sendiri. SDK Android tidak dibutuhkan untuk menjalankan versi desktop dengan F5.

## Gameplay yang sudah diport (2026-09-06)

| Sistem pygame | Port Godot | Catatan |
|---|---|---|
| `Tower` + `TOWER_UPGRADE_PATHS` (4 jalur, Lv1-6) | `scenes/tower/Tower.gd` + `scripts/core/TowerDB.gd` + `data/towers.json` | Archer (Lv6 double shot) · Cannon (splash + burn) · Ice (slow + atk slow, Lv6 AOE) · Mage (chain + skill down + anti-heal). Build 100g, upgrade 175/325/550/850/1300, shield = 40% HP, HP regen 0.3/frame setelah 5s tanpa damage, Regen Shield 850g (Lv4+) |
| `Castle` + `NEXUS_LEVELS` | `scenes/base/Nexus.gd` + `data/nexus.json` | Lv1 4000 HP → Lv5 15000 HP, Castle Shield menyerap 1:1 lalu sisa damage −88%, shield gratis sampai wave 10 lalu 850g, upgrade mempertahankan rasio HP + shield. Level castle awal dari levels.json: Radiant `starting_castle_level`, Dire `castle_start_level` **hanya di hard** (paritas `_core.py:1504-1508`) |
| menang/kalah | `GameManager.end_match()` + `HUD` banner | Nexus Dire hancur = VICTORY, nexus Radiant hancur = DEFEAT. Meta reward paritas `_grant_meta_reward` (`_core.py:2365-2456`): menang pertama `meta_gold_reward_win` (3000), replay win 1500 sekali lalu 200 unlimited (via `replay_reward_counts`), kalah 0 — ditulis ke save kunci `meta_gold`, guard `_meta_reward_granted`. `ENTER` = level berikutnya |
| `MenuState` + Menu pygame | `scenes/ui/MainMenu.gd` | State machine MAIN/LEVEL_SELECT/HERO_SHOP/SETTINGS/HOW_TO_PLAY/CREDITS/PAUSE, dibangun 100% dari kode (pola HUD/ShopPanel). LEVEL_SELECT: 54 kartu dari `BossDB.levels` + kunci `unlock_after_level` (`is_level_unlocked` paritas `level_data.py:2318`) + pemilih difficulty. HERO_SHOP: unlock hero pakai meta gold (paritas `_unlock_hero_in_meta_shop` `_core.py:5298`) → `SaveManager.unlock_hero()` |
| progresi level | `GameManager.next_level()` / `is_replay` + `GameManagerConnector.starting_level` | ENTER setelah menang → `get_next_level` paritas (`level_data.py:2340`); replay → `is_replay=true` (paritas `main.py:576`). Connector tidak lagi hardcoded level 1: `start_match(n)` dipanggil menu |
| enemy scaling hard | `GameManager.enemy_*_mult` + `Main`/`Boss`/`Minion` | `enemy_scaling_enabled = (difficulty == "hard")`; hp ×1.15, damage ×1.10 dari levels.json (`_core.py:1476-1483`). Diterapkan saat spawn: minion merah `apply_enemy_scaling` (`_core.py:1792-1796`), mini/true boss `apply_scaling` (`_core.py:1822/2097`) |
| unlock hero boss | `GameManager._auto_unlock_defeated_boss_heroes()` | Boss yang dikalahkan di match yang DIMENANGKAN → hero-nya gratis masuk `unlocked_heroes` + `unlocked_bosses` (paritas `_core.py:2322-2355`); kalah = tidak dapat. Boss yang dikalahkan tapi belum dimenangkan → bisa DIBELI 4500 meta gold di HERO SHOP |
| `SoundManager` + `mobile/combat_audio.py` | `scripts/autoload/AudioManager.gd` | BGM `bgm_track` per level (`start_level` → `play_bgm`), SFX UI/victory/defeat, **suara tempur penuh** (lihat baris berikut). Volume = `MASTER_VOLUME 0.7` × slider sfx/bgm dari `SaveManager.data["settings"]` — paritas `SoundManager.play` (`_system.py:589-598`), dibaca dari memory jadi tidak ada tulis file per frame. Aset 24 .wav disalin converter ke `godot/assets/sounds/` (di-gitignore) |
| suara tempur (`combat_audio.py` skema v35) | `AudioManager.play_combat()` + 14 call site | 7 jenis suara: `hero_melee`/`hero_ranged` (Hero **dan** Boss, ambang jarak 100), `tower_archer`/`tower_cannon`/`tower_ice`/`tower_mage` (tim biru 1.0 / merah 0.8), `minion_hit` (semua jenis minion). Tiga pengaman pygame ikut: jeda per jenis 90/110/140 ms, anggaran 4 suara/frame, volume dasar 0.50-0.78. Ditambah `minion_death` 0.7 (throttle 120 ms), `goblin_spawn` 0.7, `hero_spawn`, `hero_skill` (volume per tombol q .8/w .6/e .7/r 1.0), `wave_start` 0.6, `nexus_hit` 0.7 (hanya castle biru, hanya kalau HP benar-benar turun), `tower_destroyed` 0.8, `explosion` (boss 1.5/1.0 `force`, splash cannon 0.3), `ui_sell`/`ui_upgrade`/`ui_buy`/`ui_error` dari `ShopPanel._run()`. Statistik penolakan dicetak 10 detik sekali, bukan per event |
| `map_components/themes.py` (54 palet) | `data/themes.json` + `ArenaMap._load_themes()` | `export_themes()` di converter mengubah tuple RGB pygame → hex; `ArenaMap` merge ke palet runtime saat `_ready` (const `THEMES` tidak bisa di-merge langsung: Dictionary const Godot 4 read-only rekursif). Warna palet dari JSON, `modulate`/`light`/`energy` tetap kurasi manual untuk 4 tema pertama. Nama tak dikenal → forest (paritas `get_theme`). Dekor ikut tema **dan ikut sisi peta**: pohon rimbun/batu berlumut hanya di Radiant, pohon mati (`has_dead_trees`) + tulang (`has_bones`) + nisan (`has_gravestones`) hanya di Dire — paritas `generate_all` (`_bundle.py:4767-4821`) yang memakai `_is_radiant()`/`_is_dire()`. Ambang jenis ditumpuk supaya jenis opsional jadi aksen (ambang tetap bikin tema ice keluar 49 kristal dari 70). Jalur juga memakai `path_moss`/`path_crack` (`_draw_cobblestone_tile` `:5206`) — tema volcanic = retakan lava menyala |
| `DynamicRenderer` partikel + fog (`map_components/_bundle.py:5370-5560`) | `ArenaMap._apply_weather()` + 2 `CPUParticles2D` | `particle_type` & `fog_*` tiap tema diekspor `export_themes()` lalu dipakai, bukan cuma disimpan. Yang ditiru adalah **gerak**, bukan warna: snow turun (`vy 0.3..0.8` px/frame `:5398-5400`), ember/acid naik (`vy -0.8..-0.3` `:5405-5408`), sand/mist menyapu mendatar (`vx 0.5..1.5` `:5401-5404`), firefly/ash/spirit melayang. Nilai px/frame pygame dikali 60 (`PYGAME_FPS`) jadi px/detik. Kabut = lapisan tipis dari `fog_color` + `fog_alpha` + `fog_count`. `CPUParticles2D` dipilih (bukan GPU) supaya aman di Android/GLES. Tipe `ash`/`spirit`/`mist`/`acid` yang di pygame TIDAK tergambar (tidak ada cabang di `_draw_particles`) di sini tergambar |
| `SoundManager.play_ambient` (`_system.py:688-710`) | `AudioManager.play_ambient()` / `stop_ambient()` | Loop `ambient_forest` di `AudioStreamPlayer` TERPISAH dari BGM (pygame juga pakai `ambient_channel` sendiri), volume `MASTER_VOLUME × ambient_volume 0.25 × 0.8` — pengali 0.8 dari call site `main.py:164`. Fade masuk 2 dtk / keluar 1,5 dtk (`fade_ms` pygame). Mulai di `GameManager.start_level()`, berhenti di `end_match()` + `return_to_menu()`, dibekukan saat menu PAUSE. Loop dipaksa lewat sinyal `finished` (jangan bergantung pada flag loop hasil import .wav) |
| `Game._generate_build_slots_from_lanes` | `Main._generate_build_slots()` | 3 slot × 3 lane × 2 tim, fraksi persis pygame (top/bot 0.15/0.30/0.45, mid 0.10/0.25/0.40, Dire dicerminkan) |
| `hero_skills/_bundle.py` (6 kelas skill) | `scripts/skills/SkillBook.gd` | Q = `skill_cooldown` hero (Kaizen 300f, Grimjaw 420f, Sylara 360f), W 4s, E 7s, R 15s + CDR item. Hero tanpa tabel memakai skill generik |
| `hero_items.py` (33 item, 6 slot) | `scripts/items/ItemDB.gd` + `ItemInventory.gd` + `data/items*.json` | Harga flat 4500g, cap atk speed 0.2-2.5 / lifesteal 1.75 / CDR 0.5 / skill amp 0.5 / evasion 0.5 / move speed 0.4, pasif Cleave + Corroder, 4 aura (Steel Aegis, Everfrost, Solar Brand, Searbrand) |
| `HERO_LEVELS` (Lv1-15) | `data/hero_levels.json` + `HeroDB.level_data()` | hp/damage/skill multiplier per level, biaya upgrade 300 → 8000, boss hero ×1.6 |
| ekonomi `_core.py` | `GameManager._process()` | `(3 + 0.3×(level−1)) × pengali_difficulty` gold/s, gold awal `(350 + 100×(level−1)) × pengali`, pecahan disimpan sebagai milli-gold (persis loop 60-frame pygame), AI tim Dire menabung dengan laju sama |
| `AIPlayer` (6000+ baris) | `scripts/systems/AIPlayer.gd` + `Hero.gd` | Port penuh: `_ai_brain`/`_ai_elite` (`_entity.py:6027-6051`), `_ai_reserve` (tabungan draft hero), `think_timer` + beberapa aksi per tick, `_ai_step` 6 prioritas (build menara → beli hero → upgrade hero → beli item → upgrade menara → Regen Shield → Castle Shield → nexus). Gold dipakai dari `GameManager.ai_gold` (pygame `AIPlayer.gold`). Item dibeli pakai `ItemDB.suggest_item()` = paritas `hero_items.suggest_item_for_hero` (`hero_items.py:2936`); kontrol hero per-frame `_control_heroes()` + `_assign_hero_lane()`; **retreat HP <20% → base → heal → keluar di 80%** ada di `Hero.gd` (paritas `_entity.py:3983-4028`); **kombo auto-cast R→E(2+)→W(<40%)→Q** paritas `_try_auto_cast` (`_entity.py:4149-4240`); Kaizen Q Steel Wind↔Dash Strike bergantian di `SkillBook` (paritas `_bundle.py:3969`) |
| mini boss / true boss | `Main._boss_tick()` | Mini boss dari `levels.json["mini_bosses"]` (satu aktif pada satu waktu), true boss setelah 6 menara Dire hancur (`_core.py` 2089) |

### Deviasi yang disengaja (dicatat, bukan bug)

- **Menu utama disederhanakan dari pygame.** Tidak diport: multi-slot save (SLOT_SELECT), dialog TOP UP hero gold + voucher, cloud save Play Games, slider master/voice volume, dan kunci difficulty `run_difficulty` (di Godot difficulty bebas diganti; pygame menguncinya sampai semua level tamat — `_core.py:2416-2430`). Sisanya (state, kunci level, reward, hero shop) paritas.
- **`hp_regen` item sekarang benar-benar dipakai.** Di pygame `HeroItemInventory.get_hp_regen()` ada tapi tidak pernah dipanggil `_entity.py`; di Godot diterapkan sebagai HP/detik (dekat base 180 HP/s, di luar base 9 HP/s + regen item).
- **17 item aktif SUDAH diport** (`ItemInventory.tick()`), tapi **tanpa tombol** — dan itu memang benar: di pygame item aktif semuanya *auto-trigger*, tiap deskripsi menulis "(auto)" (`hero_items.py:628/668/1283`). Pemicunya cuma tiga: `hp_threshold` (HP turun), `trigger_enemies` (N musuh dekat), atau punya target. Menambah hotbar justru menyimpang dari sumber kebenaran. Satu pengecualian: Static Charge (`thunder_coil`) terpicu saat pemilik KENA damage dengan peluang 20% (`on_damage_taken` `hero_items.py:2449`), bukan saat menyerang — disambung lewat `Hero.take_damage`.
- **Efek on-attack** (Bash, Piercing Bash, Arc Chain/Lightning, Frostbite, Miasma + Polycephaly multishot, Empower Strike, Entangle) dipanggil dari `Hero.try_attack` untuk melee dan `TowerBullet._on_hit` untuk proyektil hero — meniru dua pintu pygame (`on_basic_attack_hit` / `on_ranged_attack_hit`). Keduanya bermuara ke `ItemInventory.on_attack_hit()`, padanan `_on_hit_common` (`hero_items.py:2519-2666`), dengan urutan proc yang sama persis. Lifesteal & cleave TIDAK ikut di jalur ranged karena di pygame sudah dibayar saat proyektil dilepas.
- **`on_attack`, `bash`, `multishot`, dan pasif sudah diport** (Fase 5b): Arc Chain/Lightning, Frostbite, Miasma + Polycephaly multishot, Entangle, Bash/Piercing Bash, Empower Strike, Leviathan Vitality — semuanya lewat `ItemInventory.on_attack_hit()`.
- **Proyektil skill = visual homing, damage tetap instan** — paritas `_spawn_skill_projectile` pygame (`_entity.py:4509-4530`): proyektil `damage=0` + `is_skill` hanya memberi visual terarah, damage otoritatif tetap instan di `SkillBook` (sama seperti pygame — `hero_skills/_bundle.py` yang menghitung damage). Implementasi: `scenes/fx/SkillProjectile.gd` (Node2D self-drawn, pola `TowerBullet`), dipanggil dari 3 call site paritas — Sylara R Powershot per musuh kena (`_bundle.py:4461`), Vex Q Arcane Orb (`:4820`), Vex E Astral Imprisonment (`:4924`). Batas 6/hero, umur 72f (target mati 36f), jarak 380px, snap ke target + impact FX hanya kalau target masih hidup — semua `_entity.py:3225-3232 / 3827-3943`. Satu deviasi kecil: peluru basic attack (`TowerBullet`) tidak ikut dihitung dalam cap-6; node terpisah dengan umur 4 detik + mati saat target mati. Gambar panah/orb = port fallback `_draw_projectile` (`_entity.py:4976-5210`); ornamen per-hero `heroes/*_fx.draw_arcane_orb` adalah fase visual terpisah.
- **AI dire**: port `AIPlayer` pygame di `scripts/systems/AIPlayer.gd` — tapi ada dua deviasi yang dicatat: (1) pygame AI mulai dengan roster KOSONG dan membeli semua hero dengan gold sendiri; Godot tetap meng-seed 6 hero merah (`ENEMY_ROSTER`) sesuai alur battle yang sudah ada, dan karena 6 ≥ `AI_MAX_HEROES` (5) cabang beli hero aktif lagi kalau roster turun di bawah 5; (2) statistik `total_built`/`total_upgraded`/`total_skills_cast` dkk. tidak diport (hanya untuk HUD/debug pygame, tidak memengaruhi keputusan). Saldo AI: pygame `AIPlayer.gold` dimulai 350, Godot `GameManager.ai_gold` = gold awal pemain (keputusan port ekonomi sebelumnya).
- **`play_positional` (`_system.py:615-629`) sengaja TIDAK diport.** Tidak ada satu pun call site di repo pygame — dead code, jadi tidak ada yang bisa dijaga paritasnya.
- **Preset kualitas `mobile.perf.Quality`** (yang di pygame mengurangi jumlah partikel/fog di HP kentang) tidak ikut diport ke cuaca Godot: pengurangan beban di sana urusan setelan render Godot, bukan cabang `try/except import` per tema.
- **Flash putih saat kena damage = `hurt_flash_timer` pygame, dideteksi dari `hp` yang turun.** `scripts/render/HurtFlash.gd` dipakai bersama Hero/Minion/Boss: 8 frame @60fps (`DURATION = 8.0/60.0`) turun linear, targetnya `silhouette.flash_amount` → `custom_visual.modulate` → fallback (`hit_flash_mat` hero / `body` minion / `sprite` boss). **Deteksinya menonton `hp`, bukan hook di `take_damage()`** — persis alasan pygame menaruhnya di `update()` (`_entity.py:5545-5551`, `bosses/base_boss.py:609-610`): damage masuk dari banyak pintu, dan di port Godot `take_damage()` hampir tidak pernah dipanggil karena `Hero._attack`, `TowerBullet`, `SkillBook`, item, dan reflect semuanya memanggil `CombatSystem.apply_damage()` langsung. Satu pengecualian yang disengaja: **hero** memakai `watch_hp = false` (flash hanya lewat `trigger()` dari `take_damage`/`play_hit_fx`), karena pygame tidak punya hurt flash hero dan menyalakannya tiap pukulan sama saja dengan memberi flash pada serangan dasar — dilarang kontrak di atas. Minion: pygame MENYIMPAN `hurt_flash_timer` tapi tidak pernah menggambarnya (tidak ada cabang di draw minion); di Godot digambar, sejalan dengan keputusan yang sama pada partikel cuaca `ash`/`spirit`/`mist`/`acid`.
- **Impact FX korban = SKILL saja, serangan dasar NOL FX.** Kontrak pemilik game (dikunci `tools/test_basic_attack_no_impact_fx.py`; komentar sumber `_entity.py:4376-4384`): benturan serangan dasar tidak boleh memicu flash/spark/shockwave/hit-stop, karena di combat ramai tumpukannya menutupi sprite. Karena itu `Hero.play_hit_fx()` (burst `FX/HitParticles` + flash putih) di-hook dari `SkillBook._damage()` — BUKAN dari `Hero.take_damage()` atau `CombatSystem.apply_damage()` yang dilewati semua jalur damage termasuk basic attack, tower, dan minion. Warna burst mengikuti `fill_color` caster supaya terbaca siapa yang memukul; ada jeda 0,08 detik per hero (`HIT_FX_COOLDOWN`) supaya skill AoE + ticker DoT tidak saling membatalkan burst lewat `restart()`. Minion/boss belum punya node partikel korban, jadi `has_method("play_hit_fx")` melewatinya dengan aman.
- **Sekolah damage** diambil dari penyerang (`DamageSchool.resolve`), dot `fire`/`ice` netral — paritas `resolve_damage_school` pygame.

## Asset Pipeline

- `godot/data/*.json` — hasil convert, dibaca `HeroDB`/`BossDB`/`ArenaMap`. Ikut repo (bukan
  gitignore), jadi port jalan tanpa menjalankan converter dulu; `themes.json` tidak ada →
  `ArenaMap` mundur ke 4 palet const `THEMES`.
- `godot/assets/units/*.png` + `godot/data/baked_units.json` — strip bake 222 unit
  (Fase 5, lihat bagian "Strip bake 222 unit" di atas). **Ikut repo** — bukan duplikat
  file yang sudah ada (suara) melainkan satu-satunya salinan visual ter-bake; tanpa ini
  arena kembali ke `UnitSilhouette`, bukan error.
- `godot/assets/sounds/*.wav` — **di-gitignore** (duplikat 15 MB dari `assets/sounds/`, sumber
  kebenaran tetap di sana). Jalankan converter setelah clone, kalau belum `AudioManager`
  no-op + log sekali dan game tetap jalan tanpa suara.
- `godot/assets/shaders/outline.gdshader` — outline 1-pass + hit flash + rim light (ganti 5 blit manual pygame).
- `godot/shaders/hamon.gdshader` — hamon temper katana Kaizen (wave + temper cloud + attack pulse).

## Renderer (pygame dulu, upgrade satu-satu)

Default arena: `scripts/render/UnitSilhouette.gd` — shadow, kaki, torso, kepala, senjata kit
(hash `hero_type`), flash hit. Godot 4.3-safe (tanpa `draw_ellipse`).

Urutan lookup `RendererRegistry` sejak Fase 5 (semua di
`scripts/render/RendererRegistry.gd`):

1. **Scene custom** (`HERO`/`BOSS` dict) — rig hand-made menang selalu.
   Kaizen terdaftar:
   ```
   const HERO := {
       "kaizen": preload("res://scenes/hero/kaizen/KaizenSkeleton.tscn"),
   }
   ```
2. **Strip bake** (`BakedUnitDB.has_unit`) — 222 unit hasil
   `tools/convert_to_godot.py --units-png` memakai scene generik
   `scenes/render/BakedSprite.tscn`.
3. **UnitSilhouette** — fallback kalau 1 dan 2 tidak ada (mis. clone
   tanpa hasil bake).

Custom per unit: isi `scripts/render/RendererRegistry.gd` — satu baris
preload per hero, otomatis mengungguli strip bake.

Kalau key tidak ada, tetap silhouette. Gameplay (`Hero.gd` AI/damage/skill) tidak berubah — `Hero._drive_visual()` memanggil `drive(phase, action, attack_progress, facing, is_moving, skill, delta)` tiap frame, jadi skill QWER Kaizen ikut menggerakkan tulang (Steel Wind / Dash Strike / Wind Wall / Sweep / Tornado).

## Strip bake 222 unit (Fase 5 — Opsi A)

**Kenapa bake PNG, bukan port renderer prosedural per-hero ke GDScript?**
216 renderer boss (`bosses/level1..54.py`) + 6 hero masterwork
(`heroes/_bundle.py`, 16.723 baris) tidak realistis di-port 1:1 (Bulan +
tidak bisa diverifikasi paritasnya). Bake memakai **renderer pygame asli**
sebagai sumber kebenaran, jadi geometri/warna/pose tidak bisa drift.

```bash
# Hasil: godot/assets/units/<type>.png (222 strip, ±6,5 MB, ikut repo)
#        + godot/data/baked_units.json (manifest: frame/anchor/skala/fps)
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
    ~/.venv-mystic/bin/python tools/convert_to_godot.py --units-png
# --only gornak,sylara = debug 1 unit (manifest TIDAK ditimpa)
```

Per unit, strip berisi grid **[idle 8 | walk 8 | attack 8]** frame, 8
frame per baris (lebar maks 2.216 px — aman untuk batas tekstur 4096 px
GPU mobile), **anchor = telapak kaki** yang diratakan antar frame saat
bake (AnimatedSprite2D cuma punya satu offset untuk semua frame).
Mekanika pose mengikuti pygame persis:

| Aspek | Sumber pygame | Implementasi bake |
|---|---|---|
| fase idle/walk | `int(pulse*2) % 8` (`heroes/__init__.py:1777`, `HERO_ANIM_PHASES` `:1483`) | 8 sampel pulse rata |
| deteksi jalan | `_detect_moving` delta > 0.3 px (`bosses/level1.py:947-962`) | probe digeser 1.4 px/frame |
| pose serang | **mode manual** controller — "alat preview/tes ... hormati" (`bosses/level1.py:873-898`) | set `_XX_attack_progress` per frame |
| frame serang | diturunkan dari sisa timer, bukan jam (`bosses/level1.py:841-842`) | `drive()` memaksa frame dari `attack_progress` |
| skala hero lane | `_get_hero_scale` (`heroes/__init__.py:2148`, target tinggi 65 × global 0.78) | `hero_scale` di manifest → `sprite.scale` |
| skala boss | native 1.0 (`heroes/__init__.py:2873-2878`) | `boss_scale: 1.0` |
| fps idle/walk | fase baru tiap 10 frame hero / 5 frame boss (`_entity.py:1681` vs `base_boss.py:580`) | 6 fps hero / 12 fps boss |
| outline+rim | `_finish_hd_sprite` hanya jalur hero (`heroes/__init__.py:1866+`) | shader outline di `BakedSprite.tscn`, mati untuk boss |
| beam morgath | digambar live, di-skip saat cache (`heroes/__init__.py:2149-2151`) | tidak ikut strip (proyektil Godot yang menggambar) |

Kompresi: PNG palet 256 warna + alpha diperbaiki per entri palet (entri
alpha < 16 dipaksa 0) — 21 MB RGBA → 6,5 MB tanpa halo kotak samar di
area pad. Deterministik: seed per-frame + dt controller ter-jepit 1/60
(`bosses/level1.py:824-826`) → dua kali bake menghasilkan hash PNG
identik (diverifikasi saat pengembangan).

Deviasi yang disengaja (Fase 5; dua yang pertama DITUTUP di Fase 5c
di bawah):

- **Pose skill (q/w/e/r) belum dibake** — selama cast, badan memakai
  pose attack terakhir + FX proyektil Godot (`SkillProjectile.gd`,
  jalur visual skill sejak Fase 5b). Bake pose skill = fase lanjutan
  (timeline per skill beda-beda, `SKILL_VISUAL_DURATION` per namespace).
- **Elite/level tinggi tidak dibake** — bake memakai `boss_class`
  asli dari `boss_data.py` (168 mini + 54 true) pada level 1; bentuk
  elite (mis. `_draw_grimjaw_elite`) menyusul kalau diperlukan.
- **Rim cahaya tim** disederhanakan jadi 2 nilai shader (biru/merah)
  dari 2 tabel RGB pygame (`_HD_RIM_ADD*`, `heroes/__init__.py:1880-1883`).

## Pose skill + rage (Fase 5c — menutup 2 deviasi Fase 5)

Perintah bake sama (`--units-png`); keluarannya bertambah 222 strip
`<type>.skill.png` (±9,2 MB) + 1 strip `drakar.rage.png` dan manifest
**skema 2** (kunci baru `skill_dur`/`skill_anims`/`skills_png` +
geometri strip skill, `rage*` untuk drakar — pembaca skema 1
mengabaikannya, backward-compatible).

| Aspek | Sumber pygame | Implementasi |
|---|---|---|
| drive skill | `active_skill` + countdown `active_skill_timer` (kunci cache `heroes/__init__.py:1750-1766`) | sweep timer durasi cast → 1, 6 frame/pose |
| durasi cast | sisi-AI (`<X>Skills.SKILL_VISUAL_DURATION` + `BossHeroSkills._SKILL_REGISTRY`, `hero_skills/_bundle.py`) — BUKAN durasi render namespace | `skill_dur` di manifest; dipakai sweep bake + `SkillBook._visual_duration` + countdown `BakedSprite` |
| progress | renderer menghitung sendiri `1-timer/dur` (mis. `_skill_progress`, `heroes/_bundle.py:6807-6811`) | `BakedSprite` memaksa frame dari countdown, prioritas DI ATAS attack |
| pose statis | gerbang bake: selisih vs idle < 1.0 | 1 drop (`ursath/w`, visual identik — benar) + 2 fail renderer rusak (`sasori/e`, `vex/q`) → fallback attack |
| unit berlapis | `heroes/*_fx.py` digambar live di atas sprite (`_bundle.py`) | bake fallback kanvas saja (seperti Fase 5); FX hidup tetap tugas Godot |
| varian rage | `rage_active` 300 frame sejak cast q drakar (`hero_skills/_bundle.py`) | strip `drakar.rage.png` (24 frame idle/walk/attack beraura); `BakedSprite` mengganti pose dasar selama countdown rage |
| bentuk elite | "Elite" ternyata NAMA RIG UTAMA, bukan varian level: `_draw_grimjaw_elite`/`_draw_kaizen_elite` dipanggil tanpa syarat oleh wrapper `_draw_*_body` (`heroes/_bundle.py:1404-1411`, `:7431-7437`); `_draw_zharok_elite` (`bosses/level4.py:2125`) bahkan tak dipanggil. Level tidak dibaca di jalur draw; `boss_class` tetap per tipe | SUDAH tampil di strip dasar Fase 5 — deviasi ditutup sebagai salah-alamat (misnomer), tanpa bake tambahan |

**Jam virtual bake.** Klaim "dua kali bake = hash identik" Fase 5 ternyata
bocor untuk 2 unit: mulut emberwick membaca `get_ticks()` absolut saat
attack (`bosses/level41.py:476`, 4 hash berbeda terukur) dan controller
thalgryn memakai dt jam dinding (`bosses/thalgryn_v4.py:1019-1031).
Perbaikannya dari sisi bake (file `bosses/*.py` tidak boleh diubah):
`get_ticks()` dibekukan ke `_PROBE_TICK` selama SELURUH ekspor —
meniru pola resmi probe paritas game itu sendiri
(`heroes/__init__.py:3085-3103`). Hasil: 220/222 strip dasar
byte-identik dengan Fase 5; emberwick + thalgryn berubah SATU KALI
terdokumentasi, lalu stabil (446 file identik antar dua run penuh).

File penting: `scripts/render/BakedUnitDB.gd` (manifest + tekstur lazy,
FIFO cap 64), `scenes/render/BakedSprite.tscn` + `.gd` (SpriteFrames
dibangun runtime via AtlasTexture — tanpa 222 file .tres).

## Kaizen Skeleton2D (flagship — **sudah** dipakai di arena)

```
godot/scenes/hero/kaizen/KaizenSkeleton.tscn  — 25 Bone2D (Root→Hips→Torso→Chest→Head/Ponytail 3×/Scarf 3×/Katana + Arms/Legs)
godot/scenes/hero/kaizen/KaizenSkeleton.gd   — drive(phase, action, attack_progress, facing) — busur 1 sumber kebenaran (ATTACK_ARC_*), inertia scarf/ponytail, hamon shader time, wind ribbon Line2D
godot/scenes/demo/KaizenDemo.tscn/.gd       — showcase isolasi: F5 Run Current Scene untuk lihat 60fps bone interpolasi vs pygame 6-frame patah
```
Kaizen sudah terdaftar di `RendererRegistry.HERO`, jadi F5 langsung menampilkan rig bertulang di lane mid.
Tip katana: `get_katana_tip_global()`.

## Android Build

`Project → Export → Android → Export AAB` → `godot/build/MysticArena.aab` (1-2 menit, bukan 8-12 menit buildozer).

Package: `io.github.dharmawantoxi.mysticarena` (sama, save cloud tetap kebaca).

### `Unable to open Android 'build-tools' directory`

Ini masalah SDK lokal, terpisah dari parse error GDScript:

1. Di Android Studio → **SDK Manager → SDK Tools**, install **Android SDK Build-Tools**
   sesuai kebutuhan versi Godot yang dipakai.
2. Di Godot → **Editor Settings → Export → Android → Android SDK Path**, pilih
   direktori **root SDK** yang berisi `build-tools/` dan `platform-tools/`, bukan
   direktori `build-tools/` atau subdirektori versinya. Pastikan foldernya bisa dibaca.
3. Buka ulang project setelah SDK/path diperbaiki. Untuk F5 desktop saja, SDK Android
   tidak diperlukan; jangan mengubah script atau menghapus preset export untuk menutupi pesan ini.

Path SDK adalah pengaturan editor per mesin, bukan path yang perlu disimpan di repository.

Lihat `docs/GODOT_MIGRATION.md` untuk roadmap lengkap.
