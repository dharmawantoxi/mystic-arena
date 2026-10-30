# Migrasi folder `heroes/` (Pygame → Godot)

Folder `heroes/` adalah folder terbesar di sisi Pygame: **34 modul, 101.262 baris**.
Isinya bukan satu lapisan, melainkan **dua**:

1. **Pipeline renderer** — `HERO_RENDERERS` (6 starter), rumus skala terukur,
   cache sprite, cache pose, dan anggaran render per frame.
2. **Lapisan FX hidup** — 27 modul `*_fx.py` (partikel, trail, decal tanah,
   proyektil skill) yang digerakkan oleh bus bersama di `__init__.py` beserta
   **governor beban combat** (`mobile/perf.py`).

Laporan ini memetakan **setiap** modul: mana yang sudah diport (dan lewat apa),
mana yang belum, dan deviasi yang disengaja. Sumber kebenarannya oracle
`godot_rebuild/tests/heroes_folder_source_oracle.py` + fixture
`tests/fixtures/heroes_folder_source.json`; pengujian native ada di
`tests/heroes_folder_checks.gd`.

## 1. Ringkasan status

| Lapisan | Sumber Pygame | Padanan Godot | Status |
|---|---|---|---|
| Renderer hero + skala + atlas | `HERO_RENDERERS`, `_get_hero_scale`, cache sprite/pose | `data/art/heroes.json` + `scripts/ui/hero_art.gd`, `hero_anim.gd` | Diport (bake) |
| 6 namespace starter | `_bundle.py` (`_NS_grimjaw` … `_NS_zephyr`) | atlas `non_boss` (6 entri) | Diport (bake) |
| 4 renderer pixel-art | `kaizen_v1.py`, `vex_v1.py`, `grimjaw_v1.py`, `sylara_v1.py` | atlas hasil render efektif (setelah `install(legacy_cls)`) | Diport (bake) |
| Rasa pertarungan | `combat_feel.py` (`HitStop`, shake, `FIXED_DT`) | `scripts/match/hit_stop_runtime.gd`, `scripts/combat/skill_feedback.gd`, `effect_manager.gd` | Diport |
| Bus FX + governor beban | `__init__.py` (`_LIVE_FX_HEROES`, `begin_fx_frame`, `count_busy_fx_heroes`, `_FX_GROUND_LEFT`) + `mobile/perf.py` | `scripts/ui/hero_fx_bus.gd` + `scripts/settings/fx_governor.gd` | Diport (baru) |
| 27 direktor FX | `*_fx.py` (72.594 baris) | **belum ada** | BELUM |
| Trik `sys.modules` | `_install_aliases`, `_EXTRA` | tidak perlu (`preload` eksplisit) | Tidak portabel |

Angka kunci: 222 hero + 228 atlas di manifest, `phases` 8, `hero_scale` rentang
0,352–1,268 (= klamp sumber 0,40–1,70 × `HERO_GLOBAL_SCALE` 0,78), governor FX
dengan token 140/18/10 dan lantai 56/10/5.

## 2. Tabel per berkas (34 modul)

| Modul | Baris | Status | Bukti / catatan |
|---|---|---|---|
| `__init__.py` | 3.374 | Diport (terbelah) | Pipeline renderer → bake atlas; bus FX + anggaran + pose quantum → `hero_fx_bus.gd` & `fx_governor.gd`; `_install_aliases` → tidak portabel |
| `_bundle.py` | 16.769 | Diport (bake) | 6 namespace starter (12 fungsi `draw_*`) dirender ke atlas; 4 pemanggilan `install(legacy_cls)` menimpa namespace sebelum bake |
| `combat_feel.py` | 311 | Diport | `HitStop` (0,03–0,08 s, cap 5 langkah) → `hit_stop_runtime.gd`; shake → `effect_manager.gd`; volume skill → `skill_feedback.gd` |
| `abaddon_fx.py` | 1.129 | BELUM | Direktor FX live, 29 `def`, `MAX_PARTICLES` 57 |
| `alchemist_fx.py` | 2.665 | BELUM | 52 `def`, `MAX_PARTICLES` 102 |
| `ancient_apparition_fx.py` | 2.808 | BELUM | 59 `def`, `MAX_PARTICLES` 102 |
| `gorath_fx.py` | 2.928 | BELUM | 55 `def`, `MAX_PARTICLES` 102 |
| `gornak_fx.py` | 3.014 | BELUM | 50 `def`, `MAX_PARTICLES` 102 |
| `gravefang_fx.py` | 2.713 | BELUM | 52 `def`, `MAX_PARTICLES` 144 |
| `gravewake_fx.py` | 2.403 | BELUM | 55 `def`, `MAX_PARTICLES` 102 |
| `grimjaw_fx.py` | 3.034 | BELUM | 46 `def`, `MAX_PARTICLES` 108 |
| `grimjaw_v1.py` | 2.699 | Diport (bake) | `install(legacy_cls)` → subclass `_NS_grimjaw`; dipakai saat bake |
| `ignis_drachorn_fx.py` | 3.230 | BELUM | 62 `def`, `MAX_PARTICLES` 126 |
| `kaizen_fx.py` | 2.909 | BELUM | 45 `def`, `MAX_PARTICLES` 96; hit-stop `on_cast` sudah diport ke tabel battle |
| `kaizen_v1.py` | 1.419 | Diport (bake) | Renderer V1; `hero_scale` tertanam 0,4971 |
| `khalros_fx.py` | 1.904 | BELUM | 38 `def`, `MAX_PARTICLES` 72, tanpa `ProjectileSystem` |
| `krobellus_fx.py` | 2.114 | BELUM | 40 `def`, `MAX_PARTICLES` 132 |
| `kunkka_fx.py` | 2.363 | BELUM | 52 `def`, `MAX_PARTICLES` 102 |
| `nyxara_fx.py` | 2.596 | BELUM | 48 `def`, `MAX_PARTICLES` 132 |
| `nyzrak_fx.py` | 2.207 | BELUM | 45 `def`, `MAX_PARTICLES` 102 |
| `pyrenth_fx.py` | 3.942 | BELUM | 74 `def`, `MAX_PARTICLES` 120 (modul FX terbesar) |
| `razak_fx.py` | 2.952 | BELUM | 55 `def`, `MAX_PARTICLES` 102 |
| `sylara_fx.py` | 3.532 | BELUM | 59 `def`, `MAX_PARTICLES` 99 |
| `sylara_v1.py` | 2.567 | Diport (bake) | Renderer V1 |
| `syrentha_fx.py` | 2.404 | BELUM | 54 `def`, `MAX_PARTICLES` 102 |
| `thalgryn_fx.py` | 1.674 | BELUM | 45 `def`, `MAX_PARTICLES` 102 |
| `varkul_fx.py` | 2.568 | BELUM | 57 `def`, `MAX_PARTICLES` 114 |
| `vex_fx.py` | 3.783 | BELUM | 56 `def`, `MAX_PARTICLES` 102; hit-stop `on_cast` sudah diport |
| `vex_v1.py` | 1.529 | Diport (bake) | Renderer V1 |
| `vhalzun_fx.py` | 2.626 | BELUM | 49 `def`, `MAX_PARTICLES` 132 |
| `vokrahn_fx.py` | 3.596 | BELUM | 74 `def`, `MAX_PARTICLES` 120 |
| `xerathis_fx.py` | 1.936 | BELUM | 49 `def`, `MAX_PARTICLES` 114 |
| `zephyr_fx.py` | 2.096 | BELUM | 30 `def`, `MAX_PARTICLES` 96; satu-satunya modul tanpa `attach()`/`owns()` |
| `zharok_fx.py` | 3.468 | BELUM | 70 `def`, `MAX_PARTICLES` 120 |

## 3. Runner-up: 27 direktor FX live (semuanya BELUM)

Semua 27 mengekspos `tick()`, `draw_ground_layer()`, `draw_live_layer()`,
`reset_all()`, `total_particles()`, dan `MAX_PARTICLES`. `attach()`/`owns()`
opsional (zephyr tidak punya); `stats()` hanya ada di 12 modul.

| Hero | Modul | Baris | `def` | `MAX_PARTICLES` | Entry point opsional |
|---|---|---|---|---|---|
| zephyr | `zephyr_fx.py` | 2.096 | 30 | 96 | tanpa `attach`, `owns`, `stats` |
| gornak | `gornak_fx.py` | 3.014 | 50 | 102 | tanpa `stats` |
| grimjaw | `grimjaw_fx.py` | 3.034 | 46 | 108 | tanpa `stats` |
| kaizen | `kaizen_fx.py` | 2.909 | 45 | 96 | tanpa `stats` |
| vex | `vex_fx.py` | 3.783 | 56 | 102 | tanpa `stats` |
| sylara | `sylara_fx.py` | 3.532 | 59 | 99 | tanpa `stats` |
| abaddon | `abaddon_fx.py` | 1.129 | 29 | 57 | tanpa `ProjectileSystem` |
| gorath | `gorath_fx.py` | 2.928 | 55 | 102 | lengkap 12/12 |
| razak | `razak_fx.py` | 2.952 | 55 | 102 | tanpa `stats` |
| khalros | `khalros_fx.py` | 1.904 | 38 | 72 | tanpa `ProjectileSystem` |
| alchemist | `alchemist_fx.py` | 2.665 | 52 | 102 | tanpa `stats` |
| ancient_apparition | `ancient_apparition_fx.py` | 2.808 | 59 | 102 | tanpa `stats` |
| nyzrak | `nyzrak_fx.py` | 2.207 | 45 | 102 | tanpa `stats` |
| xerathis | `xerathis_fx.py` | 1.936 | 49 | 114 | lengkap 12/12 |
| varkul | `varkul_fx.py` | 2.568 | 57 | 114 | lengkap 12/12 |
| ignis_drachorn | `ignis_drachorn_fx.py` | 3.230 | 62 | 126 | lengkap 12/12 |
| zharok | `zharok_fx.py` | 3.468 | 70 | 120 | lengkap 12/12 |
| vokrahn | `vokrahn_fx.py` | 3.596 | 74 | 120 | lengkap 12/12 |
| pyrenth | `pyrenth_fx.py` | 3.942 | 74 | 120 | lengkap 12/12 |
| krobellus | `krobellus_fx.py` | 2.114 | 40 | 132 | tanpa `stats` |
| vhalzun | `vhalzun_fx.py` | 2.626 | 49 | 132 | lengkap 12/12 |
| nyxara | `nyxara_fx.py` | 2.596 | 48 | 132 | lengkap 12/12 |
| gravefang | `gravefang_fx.py` | 2.713 | 52 | 144 | lengkap 12/12 |
| thalgryn | `thalgryn_fx.py` | 1.674 | 45 | 102 | tanpa `stats` |
| kunkka | `kunkka_fx.py` | 2.363 | 52 | 102 | tanpa `stats` |
| syrentha | `syrentha_fx.py` | 2.404 | 54 | 102 | tanpa `stats` |
| gravewake | `gravewake_fx.py` | 2.403 | 55 | 102 | tanpa `stats` |

Kontrak native untuk direktor ini sudah disiapkan: `HeroFxBus.FX_CONTRACT`
berisi dua belas nama yang sama, dan bus memanggil `attach` → `tick` →
`draw_ground_layer` / `draw_live_layer` lewat `_invoke()`, sehingga modul yang
tidak punya `attach()` (kasus zephyr) tetap berjalan tanpa perubahan bus.

## 4. Yang sudah diport, dan buktinya

### 4.1 Pipeline renderer → atlas bake

| Konstanta / perilaku sumber | Nilai sumber | Jejak native |
|---|---|---|
| `HERO_GLOBAL_SCALE` | 0,78 | dipakai saat bake → `hero_scale` |
| `HERO_TARGET_HEIGHT` | 65 px | tinggi sel atlas |
| `_HERO_REF_ASPECT` | 1,6 | diagonal target |
| `HERO_SIZE_WIDTH_WEIGHT` | 0,0 (tinggi murni) | sama |
| `_DEFAULT_HERO_SCALE` | 0,65 | fallback bake |
| klamp skala | 0,40 – 1,70 | `hero_scale` manifest ∈ 0,312–1,326 |
| `HERO_ANIM_PHASES` | 8 | `phases: 8` di manifest |
| `HERO_ATK_QUANT` / `HERO_SKILL_QUANT` | 4 / 6 | **DEVIASI**: atlas dipaku 3 / 2 |
| `_HERO_SCALE_OVERRIDE` | kosong | tidak ada padanan (sumber kosong) |
| `HERO_RENDERERS` | 6 starter | `non_boss` manifest = 6 nama yang sama |

Bukti tambahan: 222 hero, 228 atlas, `meta.hero_scale` per hero, dan
`scripts/ui/hero_art.gd` membaca manifest yang sama (`meta()` mengembalikan
`hero_scale`, `radius`, `top_offset`, `cooldown`).

### 4.2 `_bundle.py` dan empat `*_v1.py`

`_bundle.py` bukan file mati: ia menggabungkan 6 namespace starter sebagai
**class** `_NS_<hero>` lalu, di baris 16.732–16.769, menjalankan
`_NS_kaizen = _install_kaizen_v1(_NS_kaizen)` (dan vex, grimjaw, sylara).
Artinya renderer **efektif** untuk keempat hero itu adalah implementasi
pixel-art V1, dan itulah yang dirender ke atlas — terlihat dari `hero_scale`
khas V1 (kaizen 0,4971; grimjaw 0,4609; sylara 0,6259; vex 0,5895) yang berbeda
dari renderer lama. Karena itu keempat `*_v1.py` diklasifikasikan **Diport
(bake)**, bukan "usang".

### 4.3 Bus FX hidup + governor beban (`hero_fx_bus.gd`, `fx_governor.gd`)

| Simbol sumber | Padanan native |
|---|---|
| `_LIVE_FX_HEROES` (set 27 hero) | `HeroFxBus.LIVE_FX_HEROES` (27, urutan sumber) |
| `_LIVE_FX_PATHS` | `fixture.live_fx.paths` + registrasi eksplisit `register(hero_id, director)` |
| `begin_fx_frame(active_count)` | `HeroFxBus.begin_fx_frame(active_count)` |
| `fx_frame()` | `HeroFxBus.fx_frame()` |
| `_fx_busy` / `count_busy_fx_heroes` | `HeroFxBus.is_busy()` / `count_busy_fx_heroes()` |
| `_live_fx_pre` / `_live_fx_post` | `HeroFxBus.draw_ground()` / `draw_live()` |
| `_reset_fx_ground_budget` + `_FX_GROUND_LEFT` | `FxGovernor.ground_budget()` + `HeroFxBus.ground_budget_left()` |
| `MYSTIC_FX_GROUND=0` | `HeroFxBus.set_ground_effects_enabled()` / `OS.get_environment` |
| `_skill_quant` / `_atk_quant` | `HeroFxBus.skill_quant()` / `atk_quant()` (lewat `FxGovernor`) |
| `Quality.particle_ratio`, `skill_quant_floor`, `atk_quant_floor`, `fx_ground_budget`, `max_hero_render` | `FxGovernor.particle_ratio()`, `skill_quant()`, `atk_quant()`, `ground_budget()`, `max_hero_render()` |
| `set_fx_load` / `fx_load` / `reset_fx_load` | `FxGovernor.set_fx_load()` / `fx_load()` / `reset_fx_load()` |
| `claim_fx_particle` / `refund_fx_particle` / `allow_skill_projectile` | `FxGovernor.claim_particle()` / `refund_particle()` / `allow_skill_projectile()` |
| `_wrap_fx_spawn` + `_install_global_fx_caps` | `HeroFxBus.guard_spawn(kind, before, after)` (aturan refund yang sama) |

Dua aturan sumber yang paling mudah salah dan sekarang terkunci di kode + tes:

- **Frame tidak pernah dilewati.** Beban diturunkan lewat *intensitas*
  (`particle_ratio` × `fx_load`), bukan lewat frekuensi gambar — ini yang dulu
  membuat skill FX kedap-kedip.
- **Anggaran lapisan tanah hanya memotong gambar.** Saat `_FX_GROUND_LEFT`
  habis, `attach()` + `tick()` tetap dipanggil; kalau tidak, simulasi FX hero
  ikut membeku dan lapisan atas mati (terukur di sumber: 3,99 → 0,03 ms/frame,
  artinya skill hilang, bukan cuma hiasan lantai).

Governor memakai angka sumber apa adanya: smoothing 0,40; satu hero bebas;
target `max(0,10, (1/n)^1,5)`; token partikel 140 → lantai 56, proyektil FX
18 → 10, proyektil skill 10 → 5 (gate satu arah, tanpa refund).

### 4.4 `combat_feel.py`

`HitStop` sumber menjepit permintaan ke 0,03–0,08 s, mengubahnya ke langkah
simulasi 1/60 dengan `round()`, minimal 1 dan maksimal 5 langkah, lalu memilih
jendela terpanjang. Padanan native `scripts/match/hit_stop_runtime.gd` memakai
konstanta yang sama (`MIN_SECONDS` 0,03, `MAX_SECONDS` 0,08, `MAX_FRAMES` 5,
`FIXED_DT` 1/60), termasuk pembulatan ties-to-even.

Konsekuensi yang penting dan sudah diuji: direktor FX meminta **di bawah**
lantai (kaizen Q 0,021 s, grimjaw Q 0,027 s, vex W 0,025 s, sylara Q 0,02 s),
dan sumber menaikkannya ke 0,03 s = **2 langkah beku**. Tabel
`SOURCE_CAST_HIT_STOP_SECONDS` di `prototype_battle.gd` menyimpan angka mentah
direktor itu; runtime yang menjepit, persis seperti sumber.

## 5. Tes dan oracle

| Artefak | Isi |
|---|---|
| `tests/heroes_folder_source_oracle.py` | Parser `ast` untuk 34 modul + `mobile/perf.py`; tanpa import pygame |
| `tests/fixtures/heroes_folder_source.json` | 34 berkas + baris, 27 direktor (def, cap, entry point), bus, governor, preset, konstanta skala, `combat_feel`, `_bundle`, `_v1` |
| `tests/heroes_folder_checks.gd` | 12 kelompok pemeriksaan: inventaris, registri 27, konstanta governor, 5 preset, matematika smoothing, token & refund, tick frame, anggaran tanah, `is_busy`/busy count, quantum pose, artefak bake, hit-stop |
| `tests/validate_project.py` blok `9bz` | Oracle-vs-folder, kewajiban suite, keberadaan bus/governor, angka kunci, dan laporan ini harus menyebut 34 berkas + 27 direktor |

Cara menjalankan:

```
python godot_rebuild/tests/heroes_folder_source_oracle.py            # verifikasi
python godot_rebuild/tests/heroes_folder_source_oracle.py --write    # tulis fixture
godot --headless --path godot_rebuild -s tests/run_all.gd            # suite native
python godot_rebuild/tests/validate_project.py                       # statis
```

## 6. DEVIASI yang tercatat

| # | Perilaku | Sumber | Godot | Alasan / risiko |
|---|---|---|---|---|
| 1 | Granularitas pose skill/attack | dinamis: `HERO_SKILL_QUANT` 6 lalu tangga 2/4/6 → 6/4/8/12, lantai preset 12/8/4; attack 4 dengan lantai 6/4/3 | atlas dipaku `skill_quant` 2, `atk_quant` 3 | Atlas adalah grid pose yang dipanggang sekali; quantum dinamis butuh beberapa bake. Risiko: pose cast terasa lebih halus/kasar dari sumber saat combat ramai — lapisan FX (yang justru paling terlihat) belum diport, jadi dampak visual terbatas pada badan hero |
| 2 | Tanda tangan gambar direktor | `draw_ground_layer(surface, hero, x, y)` | `draw_ground_layer(unit)` | Direktor native memiliki canvas item sendiri; `surface`/offset disuntik saat konstruksi |
| 3 | Penegakan cap spawn | monkey-patch `ParticleSystem.spawn` / `ProjectileSystem.spawn` saat impor | `guard_spawn()` + `claim_*`/`refund_*` eksplisit | GDScript tidak bisa menambal method per instance. **Risiko nyata**: penegakan bergantung pada disiplin direktor saat port — dicek per direktor di suite |
| 4 | Anggaran render penuh hero | `max_hero_render` 3/4/8 + `_claim_hero_render` memakai sprite terakhir | tidak dipakai; atlas statis | Tidak ada render ulang per frame di Godot, jadi anggarannya tidak punya arti. Nilai tetap diekspos (`FxGovernor.max_hero_render()`) demi paritas angka |
| 5 | `sys.modules` alias | `_install_aliases` + `_EXTRA` (6 namespace, 344 simbol) | `preload` eksplisit | Trik impor Python tidak punya padanan; nama modul lama hanya dipakai tool internal |
| 6 | `_HERO_SCALE_OVERRIDE` | `{}` (kosong) | tidak ada | Kalau sumber mengisinya, bake harus diulang — dicatat supaya tidak jadi jebakan |
| 7 | Lantai anggaran tanah | `_FX_GROUND_LEFT` default 99 (tanpa batas) lalu preset 2/3/6 | sama | Bukan deviasi; dicatat karena mudah salah dibaca sebagai "tidak pernah dibatasi" |

## 7. Yang belum: 27 direktor FX (72.594 baris)

Ini gap terbesar yang tersisa di seluruh migrasi. Yang **sudah** tersedia
sebagai fondasi: bus + governor + kontrak 12 entry point + aturan anggaran +
cap token, semuanya beruji. Yang belum: visual dan koreografi tiap hero.

Rencana bertahap (per gelombang, tiap gelombang bisa dirilis sendiri):

1. **Gelombang 1 — starter.** kaizen, grimjaw, sylara, vex, zephyr, thorne-lite
   (5 modul FX, 15.354 baris). Alasan: keenam hero inilah yang tampil di match
   pertama pemain, dan keempat `*_v1` sudah punya atlas.
2. **Gelombang 2 — boss populer.** gornak, gorath, razak, nyzrak, abaddon,
   khalros (14.134 baris), memakai `boss_art.gd` + `hero_projectile_art.gd`
   yang sudah ada.
3. **Gelombang 3 — sisanya.** 16 modul (43.106 baris), termasuk raksasa
   pyrenth/vokrahn/vex-adjacent.

Kriteria tiap direktor dianggap port:
`attach`/`tick`/`draw_ground_layer`/`draw_live_layer`/`reset_all` native,
membaca `FxGovernor.particle_ratio()`, memakai `claim_particle` +
`guard_spawn`, memakai `MAX_PARTICLES` sumber, dan lulus tes native yang
membandingkan jumlah partikel/umur/kecepatan dengan fixture.

## 8. Catatan kejujuran status

- Validator statis dan kelengkapan fixture **bukan** bukti paritas: yang
  dibuktikan suite baru adalah angka governor, urutan guard, semantik anggaran,
  dan artefak bake — bukan tampilan FX 27 hero.
- Belum ada bukti visual: screenshot Godot dari user, rekaman input, maupun uji
  Android untuk lapisan ini.
- Sampai 27 direktor diport, `heroes/` **tidak** boleh disebut selesai; status
  yang benar adalah: pipeline renderer + rasa pertarungan + bus FX **selesai**,
  27 direktor FX **BELUM**.
