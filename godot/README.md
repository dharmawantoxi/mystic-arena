# Mystic Arena — Godot Edition

Port GPU dari versi `pygame-ce`. **Baseline visual = silhouette pygame** (`scripts/render/UnitSilhouette.gd`: circle/polygon, 0 sprite, 0 tulang); Kaizen sudah "naik kelas" — terdaftar di `RendererRegistry.HERO`, jadi di arena ia tampil sebagai rig `Skeleton2D` 19 tulang + shader hamon + wind ribbon, sementara 221 hero lain tetap silhouette.

Lapisan gameplay MOBA-nya juga sudah diport (2026-09-06): **menara 4 jalur + 18 slot bangun**, **nexus/castle dengan shield → menang/kalah**, **skill QWER**, **toko item 6 slot (33 item)**, dan **ekonomi identik pygame** (3 gold/s + 0.3/level, pengali difficulty, milli-gold). Lihat bagian "Gameplay yang sudah diport" di bawah.

## Quick Start

```bash
# 1. Convert data pygame -> Godot JSON (sudah jalan, 222 hero, 216 boss, 54 level)
python tools/convert_to_godot.py

# 2. Buka di Godot 4.3+ (diuji di 4.7.2 Forward+)
godot godot/project.godot
# F5 -> arena 1280x720 langsung terisi: map forest digambar prosedural,
# 2 nexus (Radiant/Dire) + 18 slot menara di 3 lane, 6 hero Radiant + 6 hero Dire,
# wave minion tiap 25 detik, mini boss turun sesuai levels.json (wave 10/15/25),
# true boss Abaddon turun setelah 6 menara Dire hancur,
# HUD emas/wave/announcer + bar nexus + skill bar QWER + toko (B), damage number.
```

### Kontrol pemain

| Input | Efek |
|---|---|
| **klik kiri** | pilih unit: hero Radiant (→ skill bar + toko) · menara milikmu (→ tab MENARA) · nexus (→ tab NEXUS) · lingkaran slot di lane (→ bangun menara) |
| `Q` `W` `E` `R` | cast skill hero yang sedang dipilih (bisa juga lewat tombol di skill bar) |
| `B` | buka/tutup toko (MENARA · ITEM · HERO · NEXUS) |
| `D` | ganti difficulty: easy (gold ×1.25) → normal (×1.0) → hard (×0.75) |
| `ENTER` | setelah VICTORY/DEFEAT: mulai ulang level yang sama |
| `P` / `ESC` | pause (`get_tree().paused`; hero & minion ikut beku). `ESC` juga menutup toko |

Hero Radiant yang tidak dipilih tetap bertarung sendiri (AI + auto-cast skill); yang dipilih berhenti auto-cast dan menunggu input QWER — sama seperti pygame.

### Tombol debug

| Tombol | Efek |
|---|---|
| `F1` | respawn roster (reset pertempuran, nexus & slot ikut dibuat ulang) |
| `T` | ganti tema map: forest → desert → ice → abyss |
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
   `map_components/themes.py`. Begitu `assets/tilesets/<tema>.tres` di-import, fallback otomatis mati.
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
| `Castle` + `NEXUS_LEVELS` | `scenes/base/Nexus.gd` + `data/nexus.json` | Lv1 4000 HP → Lv5 15000 HP, Castle Shield menyerap 1:1 lalu sisa damage −88%, shield gratis sampai wave 10 lalu 850g, upgrade mempertahankan rasio HP + shield |
| menang/kalah | `GameManager.end_match()` + `HUD` banner | Nexus Dire hancur = VICTORY (meta reward 3000 + 100×level disimpan ke save), nexus Radiant hancur = DEFEAT. `ENTER` = main lagi |
| `Game._generate_build_slots_from_lanes` | `Main._generate_build_slots()` | 3 slot × 3 lane × 2 tim, fraksi persis pygame (top/bot 0.15/0.30/0.45, mid 0.10/0.25/0.40, Dire dicerminkan) |
| `hero_skills/_bundle.py` (6 kelas skill) | `scripts/skills/SkillBook.gd` | Q = `skill_cooldown` hero (Kaizen 300f, Grimjaw 420f, Sylara 360f), W 4s, E 7s, R 15s + CDR item. Hero tanpa tabel memakai skill generik |
| `hero_items.py` (33 item, 6 slot) | `scripts/items/ItemDB.gd` + `ItemInventory.gd` + `data/items*.json` | Harga flat 4500g, cap atk speed 0.2-2.5 / lifesteal 1.75 / CDR 0.5 / skill amp 0.5 / evasion 0.5 / move speed 0.4, pasif Cleave + Corroder, 4 aura (Steel Aegis, Everfrost, Solar Brand, Searbrand) |
| `HERO_LEVELS` (Lv1-15) | `data/hero_levels.json` + `HeroDB.level_data()` | hp/damage/skill multiplier per level, biaya upgrade 300 → 8000, boss hero ×1.6 |
| ekonomi `_core.py` | `GameManager._process()` | `(3 + 0.3×(level−1)) × pengali_difficulty` gold/s, gold awal `(350 + 100×(level−1)) × pengali`, pecahan disimpan sebagai milli-gold (persis loop 60-frame pygame), AI tim Dire menabung dengan laju sama |
| `AIPlayer` (membangun menara) | `GameManager.ai_try_build_or_upgrade()` | Dipanggil `Main` tiap 5 detik: upgrade menara yang ada (jalur acak) atau bangun di slot kosong |
| mini boss / true boss | `Main._boss_tick()` | Mini boss dari `levels.json["mini_bosses"]` (satu aktif pada satu waktu), true boss setelah 6 menara Dire hancur (`_core.py` 2089) |

### Deviasi yang disengaja (dicatat, bukan bug)

- **`hp_regen` item sekarang benar-benar dipakai.** Di pygame `HeroItemInventory.get_hp_regen()` ada tapi tidak pernah dipanggil `_entity.py`; di Godot diterapkan sebagai HP/detik (dekat base 180 HP/s, di luar base 9 HP/s + regen item).
- **17 item aktif, `on_attack`, `bash`, dan `multishot` belum diport.** Efek pasif/aura/stat sudah; item aktif butuh lapisan input + cooldown UI sendiri.
- **Proyektil skill instan** (damage langsung + FX partikel), bukan entitas proyektil terpisah seperti `_spawn_skill_projectile` pygame. Basic attack hero ranged, menara, dan minion ranged tetap memakai proyektil (`TowerBullet.gd`).
- **AI dire disederhanakan**: hanya menara + gold. AIPlayer pygame (6000+ baris: retreat, item build, skill combo) belum diport.
- **Sekolah damage** diambil dari penyerang (`DamageSchool.resolve`), dot `fire`/`ice` netral — paritas `resolve_damage_school` pygame.

## Asset Pipeline

- `godot/data/*.json` — hasil convert, dibaca `HeroDB`/`BossDB`.
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
