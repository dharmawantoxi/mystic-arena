# Verifikasi migrasi `hero_skills/` → Godot

Tanggal: **2026-11-03**. Branch: `arena/aba17c41-mystic-arena`.
Lingkup: kontrak `hero_skills/` tertutup, oracle Python, façade `HeroSkills.gd`,
wiring runtime, parity test GDScript, integrasi `run_all.gd` /
`validate_project.py` / dua workflow CI, dan rekonsiliasi klaim README.

## Lingkungan uji lokal

- Python 3.11.2; gdtoolkit 4.5.0 (`gdparse`, `gdlint`, `gdformat`); pygame
  2.6.1 untuk discovery seluruh `test_godot_*_prepare.py`.
- Godot **4.7.2.stable.custom_build** headless dibangun dari tag resmi
  `4.7.2-stable` (`codeload.github.com`) memakai SCons 4.11.1 + SCU, 2 core.
  X11/Wayland/audio backend/fontconfig/3D-physics dimatikan; modul
  Ogg/Vorbis/MP3 diaktifkan agar `AudioDirector.gd` bisa diparse. Fallback
  fontconfig pada source lokal dibungkam khusus untuk binary uji. Binary dan
  source Godot **tidak** di-commit.
- Aset audio opsional disalin dengan `python3 tools/prepare_godot_main.py`
  sebelum impor ulang. `.godot/`, `*.import`, dan `*.uid` hasil impor berada di
  `.gitignore`, bukan bagian patch migrasi.

## Hasil aktual

| Gate | Hasil |
|---|---|
| `python3 tools/prepare_godot_hero_skills.py --check` | PASS — 66 resep, 222 handler, 91 state key; SHA-256 kontrak `ef42a57b7334` |
| `python3 tools/test_godot_hero_skills_prepare.py` | **6 OK** |
| `python3 tools/prepare_godot_entities.py --check` | PASS — 2 kit, sprite 222/10/8/2; SHA-256 `9cba05ebd821` |
| `python3 tools/test_godot_entity_prepare.py` | **3 OK** |
| `python3 -m unittest discover -s tools -p 'test_godot_*_prepare.py'` | **79 OK** (SDL dummy; pygame 2.6.1) |
| `python3 godot_rebuild/tests/validate_project.py` | **588 PASS** |
| `gdparse $(find godot_rebuild -name '*.gd')` | PASS, termasuk generated kit |
| `gdlint` seluruh `.gd` non-generated | PASS |
| `gdformat --check` seluruh `.gd` non-generated | PASS — **87 file unchanged** |
| `godot --headless --path godot_rebuild --editor --import` | RC 0, tanpa `SCRIPT ERROR:`/`ERROR:`/`Parse Error`/`FAIL:` |
| `godot --headless --path godot_rebuild --script res://tests/run_all.gd` | **6941 checks, 0 failures** |
| `godot --headless --path godot_rebuild --quit-after 180` | RC 0, marker `[GODOT] Mystic Arena`, tanpa script error |
| `git diff --check` | PASS |

SHA-256 fixture oracle `hero_skills_parity.json`: `cd9c87c13ce1…`.
SHA-256 `HeroSkillKit.gd` aktif: `ddc43b0f7356…`; kontrak mengunci hash
sumber gabungan `f4f540d8d1b4…`, hash per file, dan hash tiga tool exporter.

Catatan transparan: percobaan suite pertama memakai binary custom sebelum aset
audio disalin, menghasilkan 9 kegagalan audio opsional. Setelah
`prepare_godot_main.py`, impor ulang, dan modul Ogg/Vorbis/MP3 diaktifkan,
suite final mencatat **0 failures**. Peringatan `dummy PhysicsServer3D`, satu
stream audio opsional, `logo.png` dimuat sebagai image, dan 4 ObjectDB leak
saat exit bukan `SCRIPT ERROR:`/`ERROR:` dan tidak menggagalkan gate.

## Cakupan parity `HeroSkillsParityTest.run()`

`godot_rebuild/tests/HeroSkillsParityTest.gd` membandingkan runtime GDScript
dengan fixture yang dihasilkan dari `hero_skills/_bundle.py` asli:

- kontrak: hash sumber/kit, 222 handler, 66 resep, 91 state key, 330 fungsi
  statis, `REQUIRE_TARGET`, slack `1.15`, fallback `200`, dan 4 durasi visual
  default;
- 223 klasifikasi hero (222 hero + unknown) dan handler starter/boss;
- 892 kasus durasi visual (223 hero × `q/w/e/r`) termasuk override
  `nyzrak`/`vhalzun` dan starter;
- 868 slot resep (216 boss + unknown × 4), serta fallback resep kosong;
- 16 kasus cooldown `-4/0/1/17` per slot dan penolakan slot asing;
- 7 kasus `_skill_range` (numeric, `None`, `0` → `skill_data`, string invalid
  → fallback, `attack_range` lebih besar, fallback khusus, nilai negatif);
- 3 geometri `enemies_in_range` dengan indeks + jarak Euclidean, 4 AoE damage
  truncation + jumlah event, dan 37 rencana trigger cooldown
  (`cooldown_field`, `max_field`, timer visual, shake, volume suara);
- wiring runtime: `CoreData.skills`, `HeroSkills.shared()`, `setup_hero` →
  `h.kit`, penolakan hero unknown, `target_reach(100) == 115`;
- fail-closed: kontrak hilang membuat `HeroSkills` dan `CoreData` tidak valid.

## CI

`godot-check.yml` dan `godot-rebuild.yml` menjalankan
`python3 tools/prepare_godot_hero_skills.py --check` dan
`python3 tools/test_godot_hero_skills_prepare.py`, dengan path filter
`hero_skills/**`, exporter/test tool, `HeroSkills.gd`, dan
`HeroSkillsParityTest.gd`. `validate_project.py` mengunci hash, cakupan,
wiring, fixture, panggilan `SkillsParity.run(self)`, dan perintah CI.
`run_all.gd` mengeksekusi parity test bersama 8 modul parity lain.

## Batasan verifikasi

- Binary custom tidak membuktikan rendering GPU/X11/Wayland, perangkat Android,
  audio output sesungguhnya, Play Games, server top-up produksi, atau signing.
- Yang diuji parity adalah registri, angka, helper, timer, geometri, damage,
  dan dispatch; bukan fidelitas piksel rig/skill/cinematic Pygame, popup,
  shake, atau keluaran audio.
- Header generated `HeroSkillKit.gd` masih menyebut regression legacy
  `godot/tests/HeroSkillParityTest.tscn`; cakupan aktif adalah
  `godot_rebuild/tests/HeroSkillsParityTest.gd` dan workflow di atas.
- Tidak ada rebalance atau efek baru; `hero_skills/` tetap oracle dan
  `HeroSkillKit.gd` tetap generated dari `tools/prepare_godot_entities.py`.
