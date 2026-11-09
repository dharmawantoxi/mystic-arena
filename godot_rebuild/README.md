# Mystic Arena — port `main.py` dan `_core.py` ke Godot 4

Proyek native untuk **application shell + core gameplay** Mystic Arena. Buka
`project.godot` dengan **Godot 4.7.2 Standard** (bukan .NET), lalu tekan **F5**.
Gameplay default sekarang `scenes/CoreGame.tscn`.

> **Batas migrasi:** loop aplikasi, ekonomi, wave, combat data-driven, save slot,
> menu/progres, input/controller, pengaturan, developer mode, dan kontrak
> top-up/cloud sudah native. Registri `hero_skills/`, helper `BaseSkill`, durasi
> visual, cooldown/range/AoE, dan dispatch ke `HeroSkillKit.gd` kini punya
> kontrak hash, oracle Python, serta parity test aktif di `run_all.gd`. Yang
> **belum** diklaim parity adalah rig/sprite/cinematic Pygame per hero/boss,
> fidelitas piksel FX/audio, plugin Play Games nyata, dan server top-up nyata.
> Layanan eksternal mengembalikan status unavailable/unverified, bukan sukses
> palsu. Kode Python tetap utuh sebagai referensi/oracle. Lihat
> `docs/GODOT_HERO_SKILLS_MIGRATION.md` dan
> `docs/GODOT_HERO_SKILLS_VERIFICATION.md`.

## Migrasi renderer heroes

`HeroVisuals.gd` menyediakan pemilih pose native dan progress cast skill.
`HeroCombatFeel.gd` menyediakan bus hit-stop/shake per match; feedback skill
lima starter ditranspilasi ke `generated/HeroFeedback.gd` dari AST Python.
`ZephyrBolt.gd` menggambar bolt prosedural native; 80 kasus geometri direkam
dari fungsi Python asli. Blending glow/rasterisasi belum parity piksel.
`HeroLiveFx.gd` menambahkan partikel impact skill Zephyr (pool per owner,
cap 96, quality budget, slow-motion dan cleanup); full director tetap parsial.
Oracle tersedia melalui `tools/prepare_godot_zephyr_particles.py --check`.
`ZephyrSwingTrail.gd` menambahkan trail tiga lapis dengan sampled staff
attachment dari rig Python. Body/trail Zephyr memakai timeline serangan yang
sama; periksa `tools/prepare_godot_zephyr_trail.py --check`. Ini belum port
seluruh rig/director atau pembuktian parity piksel.
Particle renderer mencakup pixel/streak/shard/spark/glow dan fallback pixel;
12 trajectory fixture serta smoke render Pygame menguji command/helper sumber,
bukan parity piksel native. Full director tetap tertinggal.
`ZephyrSkill.gd` memindahkan lifecycle/emisi q/w/e/r, dipicu cast sukses, cap
3 per owner, dengan oracle AST dan random tape. Jalankan
`tools/prepare_godot_zephyr_skill.py --check`. Front SkillFX (release glow/ring, area rune, impact ring) sudah native dengan
312 oracle kasus; ground haze/ring/retakan juga native dengan 288 oracle kasus.
Ground digambar di bawah karakter dan menunggu update fase pertama. Blending/raster native belum
parity piksel.
`ZephyrDirectorState.gd` memindahkan prioritas state, phase attack dan debu
start swing. Oracle mencakup 31 sampel; adapter memakai timer animasi native
setelah simulasi. Body procedural rig dan full orchestration tetap belum selesai.
`ZephyrVisualProjectile.gd` dan sistemnya menyediakan visual bolt independen:
homing, ribbon, tail particles, impact/expiry dan cap 14 per owner. API eksplisit
`HeroLiveFx.spawn_visual_projectile` tidak mengganti damage projectile gameplay
atau menambah bolt otomatis ke semua cast. Oracle menguji tujuh skenario dan
manager, termasuk pemeriksaan shim terhadap Pygame Vector2 asli.
`GrimjawHurt.gd` menambahkan foreground hurt streak dan empat band flash khusus
Grimjaw; cap 108 dan budget round-to-even berasal dari sumber. `GrimjawParticle`
dan pool-nya menambahkan ember/smoke, back/front layer, serta death edge
8 ember + 5 smoke dan shake sekali. Stream serta tujuh bentuk partikel
(termasuk glow/spark Grimjaw) sudah native. `GrimjawSkill.gd` kini menghubungkan
lifecycle/emisi q/w/e/r ke cast sukses (cap 3), serta front ring coretan, rune
dan chevron (780 oracle kasus). Ground FX, paket tambahan on_cast, live palette
sync dan full director Grimjaw masih tertinggal.
`ZephyrHurt.gd` menambahkan observer penurunan HP, tiga hurt streak dan hit
flash 0.16 detik. Observasi memakai clock FX sebelum simulasi (damage baru
terlihat tick berikutnya); source-prefix oracle tersedia di fixture partikel.
`ZephyrImpact.gd` menambahkan flash/shockwave/slash/spark untuk benturan skill,
dengan cap 8 per owner dan oracle/helper smoke test Pygame. Jalankan
`tools/prepare_godot_zephyr_impact.py --check`; blending/rasterisasi native
masih belum parity piksel.
Kontrak `data/heroes_renderers.json` memvalidasi sumber `heroes/`, atlas 222
unit, dan status migrasi per modul (bukan klaim seluruh FX sudah native). Jalankan `python3 tools/prepare_godot_heroes.py --check` dan
`python3 tools/test_godot_heroes_prepare.py`. Cakupan dan batas parity visual
tercantum di [catatan migrasi heroes](../docs/GODOT_HEROES_MIGRATION.md).

## Menjalankan

Dari root repositori:

```bash
# satu kali: salin font/gambar/audio dan ekspor metadata 54 level
python3 tools/prepare_godot_main.py
python3 tools/prepare_godot_core.py

# kontrak hero_skills/ (Python oracle -> native data + fixture)
python3 tools/prepare_godot_entities.py --check
python3 tools/prepare_godot_hero_skills.py --check
python3 tools/test_godot_hero_skills_prepare.py

# impor aset native, lalu jalankan
godot --path godot_rebuild --editor --import
godot --path godot_rebuild

# alternatif tanpa PATH: gunakan path binary Godot Anda
```

Tidak membutuhkan pygame, Python runtime, plugin .NET, atau GDExtension.
Python hanya dipakai alat persiapan/tes. Jika binary bernama `godot4`, ganti
perintah di atas. Font/gambar sudah disertakan; audio yang hilang tidak
menghentikan aplikasi. Jalankan alat persiapan setelah mengubah aset sumber.

## Struktur

| Berkas | Tanggung jawab |
|---|---|
| `scenes/Main.tscn`, `scripts/Main.gd` | Root scene dan orkestrator pengganti `main()` |
| `scripts/core/AppState.gd` | Transisi splash → menu → game ↔ pause |
| `scripts/core/FixedClock.gd` | Simulasi 60 Hz, clamp 250 ms, maksimal 4 catch-up |
| `scripts/core/GestureTracker.gd` | Tap, double tap, long press, drag, scroll, fling |
| `scripts/core/GameSettings.gd` | Preferensi audio/FPS/gameplay di `user://godot_settings.cfg` |
| `scripts/core/MatchModel.gd` | Simulasi pertandingan, wave, combat, AI, reward |
| `scripts/core/HeroSkills.gd`, `data/hero_skills.json` | Kontrak/registri 222 handler skill, helper `BaseSkill`, façade ke kit generated |
| `scripts/entities/generated/HeroSkillKit.gd` | Transpilasi Q/W/E/R bespoke dari `hero_skills/_bundle.py` |
| `tests/HeroSkillsParityTest.gd`, `tests/fixtures/hero_skills_parity.json` | Paritas kontrak + oracle Python yang dipanggil `run_all.gd` |
| `scripts/core/SaveRepository.gd` | 3 save slot, progres, statistik, voucher/top-up dedupe |
| `scripts/core/ControllerCore.gd` | State machine controller native |
| `scripts/core/DevMode.gd` | Developer hotkey/cheat gated debug |
| `scripts/game/CoreGame.gd` | GameplayPort default: input, shop, dev, hasil |
| `scripts/ports/CloudSavePort.gd` | Kontrak Play Games; default unavailable |
| `scripts/ports/TopupPort.gd` | HTTP top-up; memerlukan MYSTIC_TOPUP_URL |
| `scripts/core/LevelCatalog.gd` | Metadata level dan urutan next-level |
| `scripts/audio/AudioDirector.gd` | BGM, ambient, 32 voice SFX, fade dan pause background |
| `scripts/ui/` | Splash, menu, pause, HUD, pengaturan dan diagnostik |
| `scripts/ports/GameplayPort.gd` | Kontrak integrasi gameplay native |
| `tests/run_all.gd` | Regresi headless dengan adapter gameplay/cloud palsu |

## Kontrol

- Klik/sentuh untuk memilih level dan berinteraksi dengan arena.
- **Esc / Back / II:** pause atau lanjut. Konfirmasi sebelum kembali/keluar.
- **Tahan II 450 ms:** diagnostik; **F8 / FPS:** mode ringkas/detail.
- **Q/W/E/R**, **H**, serta tombol layar: diteruskan ke gameplay adapter.
- **G/F, T, C, B, D:** tahan tactical; pelepasan semua sumber diperlukan
  sebelum perintah berakhir. Pause/background membatalkan semua hold.
- **Space / SKIP:** lewati cinematic yang dilaporkan adapter.
- **F7/F9/F10/F11:** permintaan review rig diteruskan ke adapter; renderer
  review Python sendiri belum termasuk port ini.
- `MYSTIC_FORCE_TOUCH=1`, `MYSTIC_DEBUG=1`, atau `-- --debug` untuk pengujian.

## Menghubungkan gameplay

1. Buat scene gameplay native dengan root `Control` dan script
   `extends GameplayPort` (atau script turunan kelas tersebut).
2. Implementasikan `combat_ready() -> true`, `simulation_step()` dan metode
   input yang dibutuhkan. Jangan memakai `_physics_process()` kedua untuk
   combat: `Main` memanggil `simulation_step()` pada timestep tetap.
3. Pilih scene itu di properti **Game Scene** pada root `Main.tscn`.
4. Gunakan sinyal `next_level_requested`, `replay_requested`,
   `menu_requested`, `pause_requested`; jangan mengganti scene tree sendiri.
5. Implementasikan `hold_begin/end` dan `release_all_holds` jika memakai
   tactical command. `configure(level, replay)` menerima pilihan pemain.

`Main.cloud_service_path` dapat menunjuk node native yang memiliki `poll()`.
Ini hanya titik integrasi, **bukan** implementasi Google Play Games/cloud save.
Tanpa service tersebut aplikasi berjalan lokal tanpa menjanjikan sinkronisasi.

## Tes

```bash
python3 tools/prepare_godot_main.py --check
python3 tools/prepare_godot_core.py --check
python3 tools/test_godot_core_prepare.py
python3 godot_rebuild/tests/validate_project.py
python3 tools/test_godot_main_prepare.py
godot --headless --path godot_rebuild --editor --import
godot --headless --path godot_rebuild --script res://tests/run_all.gd
godot --headless --path godot_rebuild --quit-after 180
```

Dengan gdtoolkit 4.5.0:

```bash
gdparse $(find godot_rebuild -name '*.gd')
gdlint $(find godot_rebuild -name '*.gd')
gdformat --check $(find godot_rebuild -name '*.gd')
```

CI `.github/workflows/godot-rebuild.yml` menjalankan persiapan aset, guardrail
sumber, lint, impor, regresi, serta boot scene utama dengan Godot 4.7.2.
Tes memakai adapter palsu hanya untuk verifikasi kontrak; bukan gameplay.

Lihat [catatan migrasi core](../docs/GODOT_CORE_MIGRATION.md),
[hasil verifikasi core](../docs/GODOT_CORE_VERIFICATION.md), serta catatan
[entry point](../docs/GODOT_MAIN_MIGRATION.md) sebelumnya.

## Ekspor Android (belum diverifikasi perangkat)

Preset **Android** tersedia dengan orientasi landscape dari `project.godot`,
ARM64, min SDK 24, target SDK 36, dan application ID versi Pygame. Instal JDK 17,
Android SDK serta export templates Godot 4.7.2 melalui editor. Konfigurasikan
keystore debug/release lokal, lalu Export Project. Jangan mengubah application ID
untuk update aplikasi yang sudah terbit. Kredensial tidak disimpan di repo.
Preset ini belum menghasilkan atau memvalidasi APK/AAB di lingkungan pengerjaan.
