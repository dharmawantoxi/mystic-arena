# Mystic Arena — Godot Edition

Port GPU dari versi `pygame-ce`. **Baseline visual = silhouette pygame** (`scripts/render/UnitSilhouette.gd`: circle/polygon, 0 sprite, 0 tulang); Kaizen sudah "naik kelas" — terdaftar di `RendererRegistry.HERO`, jadi di arena ia tampil sebagai rig `Skeleton2D` 19 tulang + shader hamon + wind ribbon, sementara 221 hero lain tetap silhouette.

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
  `python3 godot/tools/tscn_lint.py godot/scenes/*.tscn` dan
  `python3 godot/tools/check_refs.py godot` (ext_resource, preload, dan `$Node/Path`).

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
| `AIPlayer` (membangun menara) | `GameManager.ai_try_build_or_upgrade()` | Dipanggil `Main` tiap 5 detik: upgrade menara yang ada (jalur acak) atau bangun di slot kosong |
| mini boss / true boss | `Main._boss_tick()` | Mini boss dari `levels.json["mini_bosses"]` (satu aktif pada satu waktu), true boss setelah 6 menara Dire hancur (`_core.py` 2089) |

### Deviasi yang disengaja (dicatat, bukan bug)

- **Menu utama disederhanakan dari pygame.** Tidak diport: multi-slot save (SLOT_SELECT), dialog TOP UP hero gold + voucher, cloud save Play Games, slider master/voice volume, dan kunci difficulty `run_difficulty` (di Godot difficulty bebas diganti; pygame menguncinya sampai semua level tamat — `_core.py:2416-2430`). Sisanya (state, kunci level, reward, hero shop) paritas.
- **`hp_regen` item sekarang benar-benar dipakai.** Di pygame `HeroItemInventory.get_hp_regen()` ada tapi tidak pernah dipanggil `_entity.py`; di Godot diterapkan sebagai HP/detik (dekat base 180 HP/s, di luar base 9 HP/s + regen item).
- **17 item aktif SUDAH diport** (`ItemInventory.tick()`), tapi **tanpa tombol** — dan itu memang benar: di pygame item aktif semuanya *auto-trigger*, tiap deskripsi menulis "(auto)" (`hero_items.py:628/668/1283`). Pemicunya cuma tiga: `hp_threshold` (HP turun), `trigger_enemies` (N musuh dekat), atau punya target. Menambah hotbar justru menyimpang dari sumber kebenaran. Satu pengecualian: Static Charge (`thunder_coil`) terpicu saat pemilik KENA damage dengan peluang 20% (`on_damage_taken` `hero_items.py:2449`), bukan saat menyerang — disambung lewat `Hero.take_damage`.
- **`on_attack`, `bash`, `multishot` belum diport.** Lima item `on_attack` (Arc Chain, Frostbite, Miasma, Entangle), dua `bash`, satu `multishot`; plus pasif Empower Strike (`runic_gavel`) & Leviathan Vitality (`leviathan_heart`).
- **Proyektil skill instan** (damage langsung + FX partikel), bukan entitas proyektil terpisah seperti `_spawn_skill_projectile` pygame. Basic attack hero ranged, menara, dan minion ranged tetap memakai proyektil (`TowerBullet.gd`).
- **AI dire disederhanakan**: hanya menara + gold. AIPlayer pygame (6000+ baris: retreat, item build, skill combo) belum diport.
- **`play_positional` (`_system.py:615-629`) sengaja TIDAK diport.** Tidak ada satu pun call site di repo pygame — dead code, jadi tidak ada yang bisa dijaga paritasnya.
- **Preset kualitas `mobile.perf.Quality`** (yang di pygame mengurangi jumlah partikel/fog di HP kentang) tidak ikut diport ke cuaca Godot: pengurangan beban di sana urusan setelan render Godot, bukan cabang `try/except import` per tema.
- **Sekolah damage** diambil dari penyerang (`DamageSchool.resolve`), dot `fire`/`ice` netral — paritas `resolve_damage_school` pygame.

## Asset Pipeline

- `godot/data/*.json` — hasil convert, dibaca `HeroDB`/`BossDB`/`ArenaMap`. Ikut repo (bukan
  gitignore), jadi port jalan tanpa menjalankan converter dulu; `themes.json` tidak ada →
  `ArenaMap` mundur ke 4 palet const `THEMES`.
- `godot/assets/sounds/*.wav` — **di-gitignore** (duplikat 15 MB dari `assets/sounds/`, sumber
  kebenaran tetap di sana). Jalankan converter setelah clone, kalau belum `AudioManager`
  no-op + log sekali dan game tetap jalan tanpa suara.
- `godot/assets/heroes/<hero>/SpriteFrames.tres` — buat dari Aseprite: `File → Export Sprite Sheet` → import ke Godot `AnimatedSprite2D`.
- `godot/assets/shaders/outline.gdshader` — outline 1-pass + hit flash + rim light (ganti 5 blit manual pygame).
- `godot/shaders/hamon.gdshader` — hamon temper katana Kaizen (wave + temper cloud + attack pulse).

## Renderer (pygame dulu, upgrade satu-satu)

Default arena: `scripts/render/UnitSilhouette.gd` — shadow, kaki, torso, kepala, senjata kit
(hash `hero_type`), flash hit. Godot 4.3-safe (tanpa `draw_ellipse`).

Custom per unit: isi `scripts/render/RendererRegistry.gd` — **Kaizen sudah terdaftar**:

```
const HERO := {
    "kaizen": preload("res://scenes/hero/kaizen/KaizenSkeleton.tscn"),
}
```

Kalau key tidak ada, tetap silhouette. Gameplay (`Hero.gd` AI/damage/skill) tidak berubah — `Hero._drive_visual()` memanggil `drive(phase, action, attack_progress, facing, is_moving, skill, delta)` tiap frame, jadi skill QWER Kaizen ikut menggerakkan tulang (Steel Wind / Dash Strike / Wind Wall / Sweep / Tornado).

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
