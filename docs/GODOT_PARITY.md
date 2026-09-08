# Status paritas Godot ↔ Pygame

**Acuan perilaku adalah versi Pygame di repository ini. Godot belum setara
sepenuhnya.** Data catalog yang sama, sprite hasil bake, dan build Android yang
berhasil tidak membuktikan bahwa alur permainan, UI, atau efeknya sudah sama.

Dokumen ini membedakan koreksi yang diuji dari bagian port yang masih parsial.
Roadmap lama di `GODOT_MIGRATION.md` mencatat implementasi komponen, bukan
sertifikasi paritas seluruh game.

## Koreksi alur pertandingan — 8 September 2026

| Bagian | Godot sebelumnya | Perilaku sekarang / acuan Pygame |
|---|---|---|
| Roster awal | 6 hero gratis per tim | Kedua tim mulai kosong. Pemain dan AI membeli hero dengan gold (`Game.reset`, `AIPlayer.__init__`). |
| Unlock awal | Keenam starter langsung terbuka | Save baru mendapat Kaizen. Unlock pada save lama **tidak dicabut**. Unlock permanen hanya izin membeli, bukan summon gratis. |
| Pembelian hero | API menerima hero terkunci, duplikat, dan roster tanpa batas | Catalog valid, unlocked, gold cukup, satu hero per tipe, maksimal 5 hero **termasuk yang mati**. Spawn pemain di depan toko Radiant (`Game.try_buy_hero`). |
| Kematian hero | Node dihapus; satu tim habis memulai ulang seluruh arena setelah 3 detik | Hero yang sama respawn setelah 10 detik di base sendiri. Level, item biasa, dan statistik tetap. Holy Rapier rontok. Debuff dibersihkan; cooldown W/E/R dan state kit (mis. charge Sylara) **membeku** lalu berjalan lagi setelah respawn, dan respawn menyetel HANYA Q siap — persis `Hero.respawn` (`Game.update`, `Hero.respawn`). |
| Waktu respawn | Callback timer bisa bertahan melewati restart/pause | Timer milik match, membeku ketika pause/intro, dibuang saat restart/menu. |
| Wave pertama | Langsung, termasuk selama intro | Persiapan 5 detik **setelah** intro dilewati; mulai pada wave 0 (`Game.reset`). |
| Wave berikutnya | Otomatis setiap 25 detik walau wave sebelumnya hidup | Interval 25 detik adalah minimum. Antrean kedua tim dan semua minion hidup harus sudah habis (`Game.update_waves`). |
| Spawn minion | Satu komposisi dibagi ke tiga lane, spawn serentak, cap 24/tim | Satu komposisi penuh **per lane**, urutan top → mid → bot, interval 20 frame/60 FPS per tim. Tidak memotong wave elite yang berisi 33 minion/tim. |
| Komposisi wave | Tabel diindeks nomor wave | Tabel diindeks **level nexus tim sendiri**, lalu tambahan elite pada wave 4/7/10/13 (`Game._get_wave_composition`). |
| Stat minion | Skala dari nexus terkuat kedua tim + bonus 8%/wave | HP/damage, kecepatan, cooldown, gold reward, regen dan prioritas target mengikuti level nexus sendiri. Hard scaling diterapkan hanya pada minion merah ketika spawn (`Minion.__init__`, `Game.update_waves`). |
| Jalur minion | Lane hanya label; berjalan diagonal ke base lawan | Mulai dari ujung lane yang benar dan mengikuti waypoint maju/mundur sesuai tim (`Minion._move_forward`). |
| Ekonomi AI | Gold awal dan income sama dengan pemain | Mulai dengan `STARTING_GOLD` (350), income `GOLD_PER_SECOND + wave_number`. AI membangun/draft memakai saldo ini (`AIPlayer.__init__`, `Game.update`). |
| Nexus AI | Tidak ada eskalasi wave otomatis | Naik ke level 2/3/4/5 pada wave 4/7/10/13, sebelum menghitung komposisi baru (`Game._auto_scale_ai_castle`). |
| Mini boss | Wave tetap dari JSON | Wave unik diacak tiap match: easy 20–40, normal/hard 11–30, urutan dan tipe boss tetap (`Game._roll_mini_boss_schedule`). |
| Data boss | BossDB hanya hp/damage/speed/range/cooldown/radius | `bosses.json` diekspor converter dari `boss_data.py` + `hero_archetypes`: armor/MR tematik, ability/ability2 (cooldown, damage, range, heal), jarak kiting, dan bendera `uses_smart_ai` hasil AST `Boss.update` — 216 baris cocok dengan oracle Pygame (`BossCoreParityTest`). |
| Resilience boss | Tidak ada; hit besar menembus | `damage_reduction` 30% (true) / 20% (mini), anti-burst cap 8% / 12% max HP, tenacity slow/atk_slow (×0.5, cap 0.35) dan resist stun 55% (`Boss.__init__`, `Boss.take_damage`, `Boss.apply_slow/apply_debuff`). |
| Enrage / Frenzy | Tidak ada | True boss enrage di HP ≤50% (×1.25/×1.25/cd ×0.75 min 18), mini frenzy di HP ≤40% (×1.15/×1.20/cd ×0.80 min 20) + callout + shake; nilai dibandingkan dengan hasil `Boss.update()` Pygame sungguhan di fixture. |
| Entrance boss | Langsung bergerak/menyerang | Freeze entrance 3 s (true) / 2 s (mini); cooldown serangan tidak jalan selama entrance. |
| True boss ability2 | Tidak ada | Heal `max_hp × ability2_heal_pct` saat HP < 30% dengan cooldown ability2. |
| Cleave & ability generik | Serangan dasar hanya kena target | Cleave 40% radius 80 ke musuh lain (netral sekolah); boss tanpa smart-AI memakai `_use_ability` (damage/range/cooldown dari data, lock serangan 60 frame, shake) persis `base_boss.py`. |
| Smart-AI boss musuh (79 tipe) | Rantai `elif boss_type` di `Boss.update` pygame tidak diport; semua boss memakai ability generik | `BossKit.gd` dihasilkan `tools/gen_boss_smart_ai.py` dari AST `bosses/base_boss.py`: dispatch 79 boss + 116 helper Q/W/E/R — koefisien, target, timing, dan urutan kondisi persis sumber (summon, dash, transform, dot/debuff area, buff, heal, knockback, combo angka). State kit per instans; jembatan frame↔detik satu tempat di `Boss.gd` (`kit_enemies`/`kit_get_stats`/`kit_skill_hit`/`kit_apply_slow`/`kit_lock_attack`/…). `gen_boss_smart_ai.py --check` di CI menjaga hasil generate tidak drift diam-diam. Boss tanpa smart-AI tetap ability generik. |
| Facing boss | Arah hadap di-update tiap frame walau boss diam di luar jangkauan | `_face()` dipanggil hanya di cabang dalam-jangkauan `update` pygame (kiter yang hold tidak berbalik); facing awal -1 (`Boss.__init__`); kunci arah hadap selama ayunan serangan dasar 6–15 frame (`_attack_lock_timer`). |
| Skill hero (222) | `SkillBook.gd` tabel efek generik per-detik; 6 starter hand-written belum diaudit koefisien/target/timing; SEMUA boss-hero memakai substitusi generik | `HeroSkillKit.gd` di-transpile 1:1 dari `hero_skills/_bundle.py` oleh `tools/gen_hero_skill_kit.py`: dispatch registry 66 resep `_cast_*` + `_generic_cast`/`_fallback_cast` untuk sisanya — koefisien, guard jangkauan (slack 1.15 hanya di acquire), prioritas auto-cast R→E(2+)→W(hp<0.4%)→Q, CDR+spell-vamp, dan urutan timer frame persis `Hero.update`. `SkillBook.gd` jadi facade UI tipis (tanpa state sendiri). Fixture oracle `hero_skills` = 222 hero × 4 skenario (118.293 event) diputar ulang `HeroSkillParityTest`; `gen_hero_skill_kit.py --check` + scope-check dijaga CI. |
| Catch-up stat hero | Buff melee normalisasi hp/damage di `get_balanced_stats` + koreksi starter saja | `HeroDB.catchup_base` mirror `hero_balance.starter_catchup_stats`: MENIMPA stat dasar SEMUA hero dari katalog MENTAH, `k = 1 + 0.32 × (1 − min(1, unlocks/12)) × sisa-hp`; hpK=1+(k−1)·1,25, dmgK=1+(k−1)·0,85; level-1/no-save → ×1,40/×1,272. `get_balanced_stats` tidak lagi mem-buff hp/damage melee (speed/cd tetap dinormalisasi ke px/s dan detik). |
| Sumber unlock catch-up (progresi) | `_catchup_unlocks()` Godot hard-code **0**: GameManager tidak menyimpan daftar hero yang dibeli/di-unlock lintas-save, jadi tiap save memakai bonus starter PENUH (×1,40 HP / ×1,272 dmg) — identik save BARU pygame walau roster pemain sudah penuh | Rantai sumber pygame diport utuh: save `purchased_heroes` (`_system.SaveManager.load`/`get_empty_save`) → `Game.reset` (_core.py:1596-1604, termasuk AUTO-GRANT `kaizen` untuk save kosong) → `__main__.game_instance` → `Hero.__init__` (`hero_balance.boss_unlocks_for_purchases` = `len()` hero BUKAN starter). Di Godot: `SaveManager.data["unlocked_heroes"]` (kunci lama Godot = padanan `purchased_heroes`) → `GameManager.purchased_heroes` (REFERENSI ke array save; diikat `bind_purchased_heroes()` di `start_level`, **dilepas dengan mengganti binding — bukan `clear()`** di `return_to_menu`, paritas `game_instance = None` main.py:587) → `GameManager.catchup_unlocks()` → `Hero._catchup_unlocks()`. Berlaku untuk hero KEDUA tim (pygame membaca daftar yang sama untuk hero AI). Unlock yang masuk di tengah match (boss dikalahkan) langsung terhitung karena array-nya dibagi referensi; hero yang SUDAH berdiri tidak dihitung ulang (sama seperti pygame). Save pemain tidak dimigrasi/dihapus: unlock lama dipakai apa adanya, penulisan hanya saat starter benar-benar baru di-grant. Dikunci fixture `hero_catchup_unlocks` + `HeroCatchupUnlockParityTest`. |
| Kaizen | Rig buatan ulang selalu mengalahkan sprite Pygame | Arena normal memakai bake renderer Pygame. Rig alternatif tetap ada di `KaizenDemo.tscn`, atau opt-in `mystic/rendering/experimental_hero_rigs`. |
| Kontrol demo | D/F1/T/SPACE mengubah match normal | Dinonaktifkan default; hanya aktif dengan `Main.enable_debug_controls`. Pilih difficulty di menu sebelum bermain. |
| Jalur damage basic hero | Pipeline school-aware satu-untuk-semua: physical→armor node, magic→MR, netral→tanpa mitigasi; armor hero = snapshot node; amp setelah mitigasi; block sebelum armor floor 1; blind dibaca dari status TARGET; crit buff tidak pernah aktif; lifesteal/cleave memakai damage post-mitigasi; reflect thornmail bertipe 'normal' | `CombatSystem.apply_damage` kini dispatch per jenis target, mirror `take_damage` pygame masing-masing: HERO = amp `int(round)` → armor ITEM (live dari inventory + aura, dikikis shred, negatif = bonus) utk SEMUA damage non-`fire`, TANPA magic_resist → block SETELAH armor (amount milik defender, aura guard menimpa tanpa roll, floor 0) → Bristleback; MINION = amp → shred bonus (double-dip) → armor−shred/MR; BOSS = amp → shred bonus → reduction−shred×0.06 (cap 0.60)/MR → resilience+cap, blind hanya `normal` bersource; TOWER = armor/MR sekolah; NEXUS = shield `int(x×(1−0.88))` truncation. Kalkulasi penyerang `calc_damage` = `_do_attack` pygame (bonus item → crit buff kit `int(×2)` → crit item `int(×mult)`; pembulatan `py_round` banker ala Python). Lifesteal float pra-mitigasi (ranged `int()` saat spawn), cleave netral tanpa source, Morgath serang instan 'normal', peluru menara/minion netral, boss ranged 'normal'. Dikunci `HeroBasicAttackParityTest` (29 skenario + probe get_block). |
| Roll RNG guard & item | Roll combat tidak pernah teruji: damage uji bertipe `fire` (netral deterministik) sehingga windrun tidak pernah me-roll dan shadow realm hanya tampak sebagai bhp flat di harness skill | Dikunci fixture `hero_rng_guards` (14 skenario, 47 roll ter-script) + replay `HeroRngGuardParityTest`. Oracle menjalankan `take_damage`/`_do_attack` pygame ASLI dengan `random.random` DI-MONKEYPATCH per situs roll (`_entity.py::take_damage`, `hero_items.py::roll_crit` — pemanggil lain jatuh ke RNG asli, double-run seed beda tetap dijalankan); Godot memutar ulang lewat hook `ParityRng` di `CombatSystem.apply_damage` + `ItemInventory.roll_crit` (tanpa begin() = `randf()` global — perilaku produksi tak berubah) dan membandingkan HP + JUMLAH/nilai/URUTAN roll yang terkonsumsi. Windrun (Sylara W): fisik = `normal`/`projectile` dengan sekolah bukan magic — termasuk netral TANPA source; `0.75` persis TIDAK meleset (strict); sihir/fire tidak me-roll; flag mati tanpa roll. Shadow realm (Zephyr W): kebal total SEMUA damage tanpa roll, dipotong sebelum windrun/wall/veil. Urutan guard shadow → windrun (roll) → wind wall → veil → evasion terkunci lewat jumlah roll per tahap. Crit Dead Edge me-roll di `calc_damage` SEBELUM mitigasi target (crit buff men-diskip roll; ranged: roll crit saat spawn lalu roll block saat mendarat), block Scarlet Bulwark me-roll setelah armor utk semua non-fire (floor 0), miss = SATU roll `max(evasion, blind)`, True Strike tanpa roll, windrun penyerang ikut me-roll pada reflect Bristleback (nested take_damage). |

| UI/HUD in-match (toko/panel/banner/klik/hotkey) | Panel/label/tombol dibangun manual tanpa oracle: income memakai `"%.1f"` engine yang tak terverifikasi, angka cooldown `ceil(detiks)` (60f tampil "1"), gate equip melee `< 110` + magic via `dmg_school` (46 hero role-magic salah), klik tanah kosong = deselect (bukan perintah gerak), tanpa klik kanan, tanpa tombol N, tanpa catatan skor/kill/timer/unlock match, pause tanpa panel, game-over tanpa stat | Seksi fixture `ui_hud` menjalankan draw pygame ASLI headless (82 skenario draw, 31 kasus klik, 28 hotkey, 222 hero predikat, kurva banner 121 titik, baterai touch-rect) dan diputar ulang `UiHudParityTest`. Kanon tunggal `HudLayout.gd`: `format_gold_rate` bit-eksak IEEE-754 (terbukti identik Python: baterai oracle + fuzz 200.000 nilai, 0 beda — `GameManager`/`HUD` delegasi), ribuan/match-time/mode/cooldown (`frames//60+1`), easing banner (slide-in 0.4 BACK OUT → tahan 1.0 → slide-out 0.6 BACK IN + subtitle letterspaced), nama castle (Lv6+ CITADEL), touch-rect 48px (center integer pygame), dan semesta TERTUTUP `ui_key` tombol toko yang diaudit tiap layar. Perilaku yang disamakan: panel hero (`Lv.n`, `hp/max`, `UPGRADE HERO (300G)`/`M A X   L E V E L`, `AUTO-CAST ON` no-op, `ITEM FORGE  (n/6)` → tab item, chip slot → forge, X = deselect), toko (suffix `MAX`/`DIMILIKI`, alasan disabled `MELEE ONLY`/`MAGIC ONLY`/`POOR`/`FULL`/`OWNED` di `ui_data`+tooltip, tanpa tombol jual di Lv1 + fallback +50G via handler, tutup seusai beli hero/bangun menara), gate equip (`range > 80` tolak melee_only; magic via `ItemDB.is_magic_hero` berbasis ROLE), prioritas klik (slot → nexus → hero biru → perintah → menara biru → deselect; tanah kosong + hero hidup = MOVE tetap dipilih; klik kanan = tutup + MOVE), hotkey H (toggle toko, paritas) + B (ekstensi Godot) + N (victory → next; defeat/last diam) + R/ESC, pause (panel 400×400 @(440,160), 4 tombol 300×48 seurutan, mode line), game-over (`VICTORY! LV.n`/`DEFEAT LV.n`, 4 baris stat, `NEW LEVEL UNLOCKED!`, `NEW HERO: …`, tombol next hanya victory+ada-lanjut). Beda disengaja yang dikunci eksplisit: UI Godot berbahasa Indonesia, toko satu-scroll tanpa halaman (himpunan 33 id direplay), klik musuh = move-to + aggro otomatis (tanpa `follow_target`), baris NEW HERO ditampilkan (pygame menghitung tapi tidak me-render), klik-kanan di atas panel tertelan. Belum teruji/sengaja terbuka: piksel (lebar chip metrik-font, gradien/shadow/dekorasi banner, ikon, kartu item), popup unlock geser + popup achievement, sistem combo (`Max Combo`), badge `NEW BEST!` (tanpa best per level di save), skor kill-hero +150 (tanpa atribusi killer), bangunan toko di map, sistem taktis (hold G/F/T/C/B/D), kontrol sentuh di layar, dan teks intro level (perilaku/skip-nya milik `CinematicTest`). |

## Belum setara — jangan ditandai selesai

- **UI/HUD/toko/menu:** perilaku in-match kini diuji oracle (`ui_hud` +
  `UiHudParityTest` — lihat tabel di atas: format, banner, biaya, gate,
  klik, hotkey, pause, game-over, audit `ui_key`). Yang TETAP TERBUKA,
  eksplisit: (1) **piksel** — lebar chip (metrik font), gradien/shadow/
  dekorasi banner, ikon skill, kartu item, dan seluruh komposit visual
  belum lolos perbandingan screenshot; (2) **popup unlock geser**
  (geometri 350×230 tercatat di fixture tapi Godot hanya menampilkan
  baris teks) + **popup achievement** `NEW HERO UNLOCKED!`;
  (3) **sistem combo** (`Max Combo` — Godot tidak punya);
  (4) **badge `NEW BEST!`** (SaveManager tak menyimpan best per level);
  (5) **skor kill-hero +150** (tanpa atribusi killer);
  (6) **bangunan toko di map** (klik gedung ITEM FORGE/HERO SHOP —
  Godot membuka toko via B/H); (7) **sistem taktis**
  (`tactical_commands.py`: hold G/F/T/C/B/D — belum diport; B dipakai
  Godot sebagai toggle toko); (8) **kontrol sentuh di layar**
  (data tombol+visibilitas diport di `HudLayout`, UI-nya belum ada);
  (9) **teks intro level** (sudah diport visual, replay teks belum ada —
  `CinematicTest` mengunci perilaku/skip); (10) **transaksi Hero Shop
  meta** di `MainMenu.gd` belum punya oracle sendiri; (11) beda kecil
  yang didokumentasikan di kode: hero mati + klik kosong menutup juga
  tokonya di Godot (pygame membiarkan `shop_open`), klik kanan di atas
  panel toko tertelan (pygame menutup popup dari mana saja), baris stat
  + `MUNDUR` di panel hero adalah tambahan Godot.
- **Visual unit:** bake menyamakan sumber pose hero/boss, bukan seluruh komposit
  live FX. Minion, tower dan nexus masih memakai gambar prosedural pengganti.
  Kuantisasi pose, lighting, cuaca dan efek skill juga belum lolos perbandingan
  screenshot menyeluruh.
- **Skill hero:** koefisien/target/timing kini 1:1 dengan `hero_skills/_bundle.py`
  dan dikunci `HeroSkillParityTest` (222 hero × 4 skenario). Guard
  **windrun** (roll RNG 75% evade fisik) dan **shadow realm** (kebal total)
  kini TERUJI PENUH di harness terpisah `hero_rng_guards`/`HeroRngGuardParityTest`
  (oracle dengan roll ter-script, urutan guard + jumlah konsumsi roll
  dibandingkan — dulu keduanya mirror manual `_entity.py:4537-4585` yang
  hanya tampak sebagai bhp flat karena damage uji bertipe `fire`).
  Yang masih terbuka: proyektil skill (`_spawn_skill_projectile`) tetap
  VISUAL-only di kedua sisi (damage instan), jadi 520 px/s travel-time
  tidak memengaruhi state — dan tidak diuji. `_try_auto_cast` Godot
  memakai ulang list `_kit_lists()` (bukan list argumen yang dilempar
  Game.update) — sama isinya saat run normal.
`Hero.auto_cast_enabled` default True seperti pygame v27 (auto-cast juga
untuk hero terpilih; gate False hanya dipakai harness replay).
  `_catchup_unlocks()` kini membaca daftar unlock lintas-save
  (`SaveManager.unlocked_heroes` -> `GameManager.purchased_heroes`) dan
  dikunci `HeroCatchupUnlockParityTest` — lihat tabel di atas.
- **Visual skill smart-AI boss:** blok `heroes/<boss>_fx` pygame
  (notify_skill_cast/impact: flash, shockwave, serpihan, beam per boss)
  diganti aproksimasi Godot — callout nama skill + cincin ekspansi
  `KitShockRing.gd` pada posisi/radius panggilan yang sama. **Perilaku**
  (koefisien, target, timing, frame) diverifikasi `BossSmartAIParityTest`;
  tampilan visualnya belum diaudit piksel-per-piksel dan dibiarkan terbuka.
  Aura ability/enrage juga belum (test `test_boss_true_aura_parity` baru
  mencakup aura true boss).
- **Mitigasi damage hero — TERUTUP audit basic attack (7 September 2026):**
  blok armor `Hero.take_damage` pygame (armor ITEM utk SEMUA damage non-
  `fire`, tanpa MR) kini di-mirror persis oleh `CombatSystem` per jenis
  target dan dikunci `HeroBasicAttackParityTest` — detail di tabel di atas.
  Yang masih TERBUKA di jalur ini (eksplisit, tidak disembunyikan):
  (1) **rend crit Sanguine Thorn belum ada sama sekali** di item Godot
  (item aktif Soul Rend — silence/amp/target — belum diport; pygame
  `_do_attack` crit pasti 150% ke target bertanda); (2) **roll block
  Scarlet Bulwark 55%, roll crit Dead Edge, evasion item, dan blind < 1.0
  kini DIREPLAY** penuh lewat `hero_rng_guards`/`HeroRngGuardParityTest`
  (roll ter-script, urutan+jumlah konsumsi dibandingkan) — yang masih
  tanpa oracle: roll blind BOSS (pygame-nya di `bosses/base_boss.py`,
  Godot tetap `randf()` langsung) dan proc item on-attack/on-damage
  (bash/chain/frostbite/miasma/empower/entangle/static charge);
  (3) **context hero aktif**
  (`resolve_damage_school` cabang `target_is_hero=True` utk damage tanpa
  source dari skill hero) belum diport — hanya memengaruhi guard
  windrun/bristleback-magic utk skill tanpa source, belum teruji;
  (4) **serangan minion ranged Godot masih proyektil** (`projectile`,
  bisa ditangkis Wind Wall) sementara pygame menyerang instan `normal`
  tanpa source — school-nya kini netral (angka mitigasi sama), tapi tipe
  damage & timing travel masih beda — ranah audit jalur minion tersendiri;
  (5) travel time proyektil hero/boss ranged (visual, damage instan di
  pygame boss) tidak diuji.
- **Perintah taktis dan kontrol pemain:** `tactical_commands.py` belum diport;
  kontrol gerak/target dan overlay sentuh Android belum lengkap.
- **Progresi/settings:** kunci difficulty sepanjang run, reset progresi karena
  ganti mode, statistik/achievement, semua pilihan settings dan migrasi/cloud
  save belum setara. Tidak menghapus save pengguna untuk menyamarkan selisih.
  Yang SUDAH setara + teruji dari blok ini hanyalah **sumber jumlah unlock
  catch-up** (`hero_catchup_unlocks`/`HeroCatchupUnlockParityTest`: kunci
  save, auto-grant starter, hitungan `boss_unlocks_for_purchases`, stat hero
  hasilnya, dan jaminan unlock save lama tidak hilang). Yang TETAP TERBUKA
  di jalur progresi ini, eksplisit:
  (1) **penempatan auto-grant starter beda**: Godot memberi `kaizen` saat
  save di-backfill (load), pygame saat `Game.reset`. Jumlah unlock
  catch-up sama-sama 0, tetapi status OWNED `kaizen` di Hero Shop untuk
  save yang benar-benar baru muncul lebih awal di Godot — belum
  disamakan karena mengubahnya menyentuh alur save;
  (2) **multi-slot save + migrasi legacy + cloud save** (`_system.py`
  NUM_SLOTS/`migrate_legacy_save`, `mobile/cloud_save.py`) belum ada di
  Godot: satu berkas `user://mystic_save.json`, jadi `get_slot_info`,
  playtime, dan `level_stats` belum diport;
  (3) **alur pembelian hero di Hero Shop meta** (`_unlock_hero_in_meta_shop`:
  syarat `unlock_require_boss`, potong `meta_gold`, harga 4500) ada di
  `MainMenu.gd` tetapi belum punya oracle sendiri — yang diuji harness ini
  hanya AKIBAT daftar unlock terhadap catch-up, bukan validasi transaksinya;
  (4) `heroes_unlocked_this_match` kini DIPORT (`GameManager` +
  baris `NEW HERO: …` di panel game-over, dikunci `UiHudParityTest` —
  pygame menghitung subtitle ini tapi tidak me-render-nya); yang tetap
  terbuka hanya **popup achievement** `NEW HERO UNLOCKED!` (FX peta).
- **Android/performa:** lolos tes headless bukan pengujian visual, sentuh,
  performa perangkat, ataupun verifikasi APK/AAB.

## Tes yang menjaga koreksi ini

Dari root repository, dengan `pygame-ce` dan Godot 4.3+ terpasang:

```bash
# Fixture dievaluasi dari fungsi Pygame asli, bukan salinan rumus Godot:
python tools/test_godot_match_parity.py

# BossKit.gd adalah hasil generate — tidak boleh drift dari base_boss.py:
python3 tools/gen_boss_smart_ai.py --check

# HeroSkillKit.gd adalah hasil generate — tidak boleh drift dari hero_skills/:
python3 tools/gen_hero_skill_kit.py --check

# Import resource lalu jalankan scene regresi:
godot --headless --path godot --editor --import
godot --headless --path godot res://tests/GameplayParityTest.tscn --quit-after 300
godot --headless --path godot res://tests/BattleSmokeTest.tscn --quit-after 180
godot --headless --path godot res://tests/AIPlayerTest.tscn --quit-after 120
godot --headless --path godot res://tests/CinematicTest.tscn --quit-after 960
godot --headless --path godot res://tests/BossCoreParityTest.tscn --quit-after 420
godot --headless --path godot res://tests/BossSmartAIParityTest.tscn --quit-after 2400
godot --headless --path godot res://tests/HeroSkillParityTest.tscn --quit-after 900
godot --headless --path godot res://tests/HeroBasicAttackParityTest.tscn --quit-after 120
godot --headless --path godot res://tests/HeroRngGuardParityTest.tscn --quit-after 120
godot --headless --path godot res://tests/HeroCatchupUnlockParityTest.tscn --quit-after 120
godot --headless --path godot res://tests/UiHudParityTest.tscn --quit-after 400
```

`GameplayParityTest` membaca `godot/tests/fixtures/match_parity.json`: ekonomi
54 level × 3 difficulty, 50 komposisi wave, 25 kombinasi minion/nexus, eskalasi
nexus AI dan titik spawn. Tes runtime juga memeriksa pembelian/duplikat/cap,
respawn individu dan team wipe, pause, antrean wave, jalur, restart dan menu.
`BattleSmokeTest` membeli hero melalui API yang sebenarnya, bukan lagi
menganggap roster demo sebagai syarat sukses.

`BossCoreParityTest` membandingkan `godot/data/bosses.json` dengan 216 baris
oracle `boss_core` (stat boss + flag smart-AI dari `Boss.update`, dan nilai
enrage dari pemanggilan `update()` Pygame yang sebenarnya), lalu menguji
perilaku runtime node Boss.gd: resilience/anti-burst, entrance freeze, aggro,
tenacity (slow/atk_slow/stun), heal true boss, cleave, dan ability generik
boss tanpa smart-AI.

`BossSmartAIParityTest` memutar ulang 237 skenario oracle `boss_smart_ai`
(3 skenario × 79 boss: gerombolan dengan HP bertahap, duo HP rendah, target
tunggal di tepi jangkauan) pada node `Boss.gd` asli yang menjalankan
`BossKit.gd`, lalu membandingkan jejak event per frame — cast skill, damage,
heal/shield, slow, kunci serangan, knockback, dash, enrage, facing, buff
speed/damage — plus state kit final (timer Q/W/E/R, buff, posisi clone,
target). Serangan dasar dimatikan di KEDUA sisi supaya jejak murni Q/W/E/R;
oracle dihasilkan dari `Boss.update` Pygame sungguhan lewat
`python tools/test_godot_match_parity.py --write-fixture`.

`HeroSkillParityTest` memutar ulang seksi fixture `hero_skills` (STRING JSON
kompak; 222 hero × skenario cluster/edge/combo/empty) pada node `Hero.gd` +
`HeroSkillKit.gd` yang sebenarnya: cast skrip (force-ready = cooldown dinolkan
di KEDUA sisi), urutan timer persis `Hero.update` (Q-- → active-- → WER-- →
`update_timers`), hit harness `fire` tiap 37 frame dari f30 (menggerakkan
guard konsumsi kit: shadow realm & Bristleback DR+reflect), floor hp 1.0.
Dibandingkan: jejak event per frame (attempt/cast/ask/bhp/bmove/bspd/batk/
bface/dmg/alock/emove/slow) + state final (4 cooldown, active_skill, diff kit
vs instance segar, kondisi probe). Serangan dasar dan gerak TIDAK di-simulasikan
di harness ini (serangan dasar dikunci `HeroBasicAttackParityTest` di bawah).
Regenerasi fixture HANYA bila `hero_skills/_bundle.py` atau `_entity.py`
berubah — pygame tidak pernah disetel mengikuti Godot.

`HeroBasicAttackParityTest` memutar ulang seksi fixture `hero_basic_attack`
(STRING JSON kompak; 29 skenario + 3 probe get_block) pada node
Hero/Minion/Boss/Tower/Nexus ASLI + `CombatSystem.apply_damage` yang
sebenarnya. Oracle pygame menjalankan `Hero._do_attack` betulan (melee &
ranged: bonus item → crit buff `int(×2)` → crit item → lifesteal float /
`int()` saat spawn → cleave netral) DAN memanggil `take_damage` tiap jenis
target dengan matriks damage-type × school × state (armor item, aura live,
shred, amp, block aura, blind penyerang, wind wall, bristleback + reflect,
thornmail, MR minion, rumus shred boss, armor menara, int truncation shield
castle). Skenario bebas RNG dan dijalankan dua kali dengan seed berbeda saat
generate — hasil harus identik. Dibandingkan: `max_hp`/`hp0` tiap unit,
HP semua unit tiap event (fase spawn & hit utk ranged), damage + school
proyektil, dan nilai `get_block()` (amount mengikuti melee/ranged PEMILIK).
Regenerasi fixture HANYA bila `_entity.py`/`hero_items.py`/`bosses/` berubah.

`HeroRngGuardParityTest` memutar ulang seksi fixture `hero_rng_guards`
(STRING JSON kompak; 14 skenario, 58 event HP, 47 roll ter-script) pada
node Hero ASLI + `CombatSystem.apply_damage`/`ItemInventory.roll_crit`
yang sebenarnya. Oracle pygame menjalankan `take_damage`/`_do_attack`
asli dengan `random.random` DI-MONKEYPATCH: hanya panggilan dari
`_entity.py::take_damage` dan `hero_items.py::roll_crit` yang mengonsumsi
urutan nilai skenario — pemanggil lain (audio/FX) jatuh ke RNG asli, dan
tiap skenario tetap dijalankan dua kali dengan seed beda supaya roll
liar yang memengaruhi hasil ditolak saat generate. Sisi Godot memakai
hook `ParityRng` (script kosong = `randf()` global, jadi perilaku
produksi tidak berubah): harness memasang script lewat `begin()`,
melepasnya lewat `end()`, lalu membandingkan HP semua unit tiap event
DAN daftar nilai roll yang benar-benar dikonsumsi — jumlah, nilai, dan
urutan. Roll yang hilang/bertambah/tertukar di salah satu engine gagal
tes. Cakupan: windrun (Sylara W — fisik = normal/projectile non-magic
termasuk netral tanpa source, 0.75 persis tidak meleset, sihir/fire tanpa
roll), shadow realm (Zephyr W — kebal total tanpa roll), urutan prioritas
guard shadow → windrun → wind wall → veil → evasion, roll block Scarlet
Bulwark 55% (setelah armor, non-fire, floor 0), roll crit Dead Edge 25%
(sebelum mitigasi target; crit buff men-diskip; ranged: roll crit saat
spawn lalu roll block saat mendarat), evasion Monarch Wings 28%, blind
< 1.0 penyerang (satu roll `max(ev, blind)`, True Strike tanpa roll),
dan windrun pada reflect Bristleback (nested take_damage). Regenerasi
fixture HANYA bila `_entity.py`/`hero_items.py` berubah.

`HeroCatchupUnlockParityTest` memutar ulang seksi fixture
`hero_catchup_unlocks` (objek biasa, bukan string kompak) pada
`SaveManager`/`GameManager`/node `Hero.gd` yang sebenarnya. Oracle
membaca kode pygame ASLI: kunci save + starter yang di-grant diambil dari
**AST `Game.reset`** (rename diam-diam langsung ketahuan),
`SaveManager.load()` pygame dijalankan atas berkas slot lama di direktori
save SEMENTARA, `boss_unlocks_for_purchases`/`starter_catchup` dipanggil
apa adanya, dan 24 baris stat berasal dari `Hero` pygame SUNGGUHAN yang
dibuat dengan `__main__.game_instance.purchased_heroes` terisi (termasuk
sesudah `upgrade()` — catch-up TIDAK dihitung ulang saat naik level).
Dibandingkan di Godot: konstanta kurva + daftar starter, unlock save lama
tidak hilang sesudah backfill, `GameManager.catchup_unlocks()` untuk 10
isi save (kosong, hanya starter, 6 starter, 1/3/6/12/15 hero non-starter,
entri kembar, dan "di luar match" = 0), 315 multiplier
`HeroDB.starter_catchup_mults`, lalu `base_hp`/`base_damage`/`max_hp`/
`damage` node Hero. Harness TIDAK PERNAH menulis berkas save
(`bind_purchased_heroes(false)`, state `SaveManager.data` di-snapshot dan
dipulihkan). Regresi yang dijaga khusus: `return_to_menu()` melepas
binding daftar unlock **tanpa** menghapus isi save. Regenerasi fixture
HANYA bila `_core.py`/`_entity.py`/`_system.py`/`hero_balance.py`
berubah.

`UiHudParityTest` memutar ulang seksi fixture `ui_hud` (objek biasa, bukan
string kompak) pada node `Main`/`HUD`/`ShopPanel`/`SkillBar`/`MainMenu`
yang sebenarnya. Oracle menjalankan draw pygame ASLI headless dengan
font/mouse/timer/waktu ter-pin: 82 skenario draw (gold/chip/badge, panel
hero, item forge + 6 halaman, shop hero, popup menara/nexus/build, overlay
menang/kalah, pause, intro), 31 kasus klik penuh yang berurutan dalam SATU
`Game` (state mengalir: beli, upgrade, jual, regen, shield, tab, scroll,
prioritas klik dunia, klik kanan, PLAY NEXT LEVEL), 28 hotkey (termasuk
matriks N/R/H/ESC saat victory-L1/victory-L54/defeat), predikat
range/magic 222 hero, tabel biaya hero/menara/nexus/shield/sell, kurva
slide banner 121 titik, baterai format (gold/income/mode/cooldown/
match-time), baterai touch-rect 48px, matriks tombol+visibilitas touch
HUD, dan urutan draw (dokumentasi — Godot memakai scene tree).
Dibandingkan di Godot: teks label HUD/panel/toko/game-over, daftar+
urutan+enabled/disabled+alasan tombol (`ui_key`/`ui_data` dengan audit
closed-world tiap layar — key asing/ganda gagal tes), geometri panel
pause 400×400 + tombol 300×48, kurva easing, dan perilaku klik/hotkey
lewat node sungguhan. Harness mem-snapshot `SaveManager.data` DAN berkas
`user://mystic_save.json` lalu memulihkan keduanya (tidak menyentuh save
pengguna). Regenerasi fixture HANYA bila `_core.py`/`_render.py`/
`hero_items.py`/`ui_components/` berubah.

Jika aturan Pygame memang berubah, sesuaikan Godot, **kemudian** regenerasi:

```bash
python tools/test_godot_match_parity.py --write-fixture
```

CI `godot-check.yml` memeriksa freshness fixture dan log runtime. Sukses berarti
ada penanda `PASS` **dan** tidak ada `SCRIPT ERROR`, `Parse Error`, atau
`Compile Error`; exit code Godot saja tidak cukup.

### Hasil validasi perubahan ini

- Fixture Pygame dan pemeriksaan GDScript, scene/referensi, serta properti
  partikel lulus. Regresi aura boss, serangan dasar tanpa impact FX, dan AI
  easy-mode Pygame juga lulus.
- Godot 4.3: `GameplayParityTest` **1.453 pemeriksaan lulus**;
  `BattleSmokeTest`, `AIPlayerTest`, dan `CinematicTest` juga `PASS`, tanpa
  error script/kompilasi/animasi. `BossCoreParityTest` lulus di CI dengan
  3.717 pemeriksaan (data 216 boss + perilaku inti boss). Gate kini turut
  menolak animasi yang tidak ada dan body fisika yang belum terdaftar di
  space.
- Fase smart-AI: oracle Pygame `boss_smart_ai` lulus lokal
  (`tools/test_godot_match_parity.py` — 79 boss, 237 skenario, 3.867 event),
  `gdparse`/`tscn_lint`/`check_refs`/`particles_lint` lulus, plus scope
  checker lokal `tools/check_bosskit_scope.py` (mencegat kelas Parse Error
  "Identifier not declared" yang lolos gdparse). Replay Godot
  (`BossSmartAIParityTest`) diverifikasi lewat CI `godot-check.yml` pada PR —
  gate lulus = penanda `PASS` dan tanpa `SCRIPT ERROR`/`Parse Error`/
  `Compile Error`.
- Fase hero-skill kit: oracle `--check` lulus lokal (222 hero × 4 skenario,
  118.293 event — fixture = perilaku pygame hari ini, sisi pygame tidak
  disentuh), `gen_hero_skill_kit.py --check` dan `check_bosskit_scope.py`
  lulus, seluruh berkas ter-gate `gdparse` + `tscn_lint`/`check_refs`/
  `particles_lint` bersih. Replay `HeroSkillParityTest` (888 skenario penuh,
  driver `Hero.skill_test_step`) lulus di CI `godot-check.yml` run
  34178217267 — tidak ada Godot headless lokal di lingkungan kerja. Tiga
  beda semantik yang ditemukan CI dan dikunci regression test di harness yang
  sama: (1) compound-op field berunit (`h.speed *= 2.0` kit windrun sylara)
  kini diekspansi generator jadi WRITE(READ op val) sehingga px/frame ↔
  px/second round-trip tanpa faktor 60 ikut ter-skala; (2) buff speed melee
  mengikuti `round(x*1.18, 2)` PERSIS (pembulatan desimal dari nilai biner —
  khalros 1.25 → 1.47, bukan 1.48 ala round(147.5)); (3) key kit
  `_base_attack_cd` (backing attr properti `attack_cooldown` di `_entity.py`,
  satuan frame) dipetakan ke `hero.attack_cooldown×60` — Godot menyimpannya
  sebagai field detik di node, bukan entri kit.
- Engine lokal dibangun dari source untuk **headless saja**, tanpa backend
  Vulkan/OpenGL. Pesan engine `No renderers available` pada lingkungan ini
  adalah batasan build pengujian; hasil di atas **bukan** validasi gambar GPU,
  sentuhan perangkat, atau APK/AAB. CI memakai binary Godot standar.
- Fase audit basic hero: oracle `hero_basic_attack` lulus lokal
  (`tools/test_godot_match_parity.py` — 29 skenario × double-run seed beda,
  58 event HP + 3 probe, sisi pygame tidak disentuh), `gdparse`/`tscn_lint`/
  `check_refs`/`particles_lint` + `gen_*  --check` + scope-check lulus lokal.
  Tidak ada Godot headless lokal di lingkungan kerja — replay
  `HeroBasicAttackParityTest` (dan regresi lama lain) diverifikasi lewat CI
  `godot-check.yml` pada PR; gate lulus = penanda `PASS` dan tanpa
  `SCRIPT ERROR`/`Parse Error`/`Compile Error`.
- Fase catch-up unlocks (progresi, FASE 11): oracle `hero_catchup_unlocks`
  lulus lokal (10 isi save, 4 kasus save lama, 315 multiplier, 24 stat hero
  pygame; seksi lama fixture byte-identik — sisi pygame TIDAK disentuh),
  `gdparse`/`tscn_lint`/`check_refs`/`particles_lint` + `gen_* --check` +
  scope-check lulus lokal. Tidak ada Godot headless lokal di lingkungan
  kerja — replay `HeroCatchupUnlockParityTest` diverifikasi lewat CI
  `godot-check.yml` pada PR (langkah baru setelah `HeroRngGuardParityTest`);
  gate lulus = penanda `PASS` dan tanpa `SCRIPT ERROR`/`Parse Error`/
  `Compile Error`. Efek nyata: save dengan 6 hero non-starter membuat
  Kaizen mulai di 660 HP / 40 damage (bukan 770/45 seperti save baru),
  persis angka `Hero` pygame.
- Fase guard RNG (windrun/shadow realm): oracle `hero_rng_guards` lulus
  lokal (14 skenario × double-run seed beda, 58 event HP, 47 roll
  ter-script; seksi lama fixture byte-identik, sisi pygame tidak
  disentuh), `gdparse`/`tscn_lint`/`check_refs`/`particles_lint` +
  `gen_* --check` + scope-check lulus lokal. Hook `ParityRng` dipasang
  di 4 titik roll (windrun/evasion-blind/block di `CombatSystem`,
  crit di `ItemInventory.roll_crit`) — tanpa begin() tetap `randf()`
  global. Tidak ada Godot headless lokal di lingkungan kerja — replay
  `HeroRngGuardParityTest` diverifikasi lewat CI `godot-check.yml`
  pada PR (langkah baru setelah `HeroBasicAttackParityTest`); gate
  lulus = penanda `PASS` dan tanpa `SCRIPT ERROR`/`Parse Error`/
  `Compile Error`.
- Fase UI/HUD in-match (FASE 12): oracle `ui_hud` lulus lokal (82 draw
  headless run pygame asli, 31 klik berurutan, 28 hotkey, 222 predikat
  hero, 121 titik banner, baterai format/touch; seksi lama fixture
  byte-identik — sisi pygame TIDAK disentuh),
  `gdparse`/`tscn_lint`/`check_refs`/`particles_lint` +
  `gen_* --check` + scope-check lulus lokal. `format_gold_rate`
  di-fuzz 200.000 nilai acak: 0 beda vs Python. Tidak ada Godot
  headless lokal di lingkungan kerja — replay `UiHudParityTest`
  (termasuk audit closed-world `ui_key` tiap layar toko)
  diverifikasi lewat CI `godot-check.yml` pada PR (langkah baru
  setelah `HeroCatchupUnlockParityTest`, `--quit-after 400`);
  gate lulus = penanda `PASS` dan tanpa `SCRIPT ERROR`/
  `Parse Error`/`Compile Error`.
