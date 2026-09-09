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
| Skor match (klaster skor: combo, NEW BEST, kill hero, popup achievement) | Tidak ada sistem combo (`Max Combo` tidak dihitung), save tanpa best per level (badge `NEW BEST!` mustahil), kill hero tidak membayar +150 dan tanpa atribusi killer, popup achievement `NEW HERO UNLOCKED!` tidak ada (hanya baris teks Fase 12) | Klaster skor diport 1:1 + dikunci oracle `match_scoring`/`MatchScoringParityTest` (oracle menjalankan `Game.update` pygame SUNGGUHAN headless — unit betulan mati via `take_damage`, dua run seed beda harus identik): (1) **combo** — mesin state `ComboCounter.gd` frame @60fps (max_timer 120 = 2 dtk, target scale 1.3, color flash 20, expiry `last_combo`) diputar `GameManager._tick_combo` (akumulator 60Hz; membeku saat pause/menu/intro paritas `EffectManager.update`); `max_combo` dibaca **sebelum** `add_kill` (quirk pygame: rantai N kill berurutan → max_combo N−1) dan hanya menyala untuk kill minion RED oleh damage apa pun termasuk netral tanpa sumber; (2) **NEW BEST!** — `SaveManager.get/update_level_stats` (kunci save `level_stats` per level: attempts/playtime/total_kills/max_combo all-time bahkan saat kalah; best_score/best_time/wins hanya saat menang, time 0 diabaikan, sama-rata tidak beri flag) dipanggil `_grant_meta_reward` lalu flag `GameManager.new_best_score/new_best_time` membuntuti baris Final Score/Match Time panel game-over; (3) **kill hero +150** — `GameManager.register_hero_death` membayar FLAT 150 ke tim lawan KORBAN (hero merah mati → gold+skor pemain, hero biru → saldo AI, siapa pun pembunuhnya) + atribusi `killer.kills` hanya untuk hero pembunuh tim lawan (tower/minion/self/netral tidak); kematian minion kini dinilai dari tim korban (`register_minion_death`) sehingga kill netral pun membayar seperti pygame; `_rewarded` direset saat hero hidup lagi — respawn (600 frame) tidak membayar dua kali; (4) **popup achievement** — `AchievementPopup.gd` (antrean, tampil 180 frame, pengganti muncul di frame yang sama, slide 300px ease-out-back, panel 280×60 @(W−300,180), header `A C H I E V E M E N T`) dipicu `GameManager.unlock_achievement` (signal → FX HUD, pola `EffectManager.unlock_achievement`); trigger `NEW HERO UNLOCKED!` + deskripsi `… now FREE in Hero Shop!` dari `_auto_unlock_defeated_boss_heroes` (sudah-own → tanpa popup). Belum teruji/sengaja terbuka: komposit piksel badge combo + popup (font/shadow/ikon/truncation ellipsis judul), notifikasi tier sidepanel pygame (tidak ada sidepanel Godot), ~~popup gold `+nG` kematian minion~~ (data/antrean/posisi kini terkunci FASE 15 — baris reward minion+menara), tampilan BEST SCORE/best time di level-select (data `level_stats` sudah tertulis — ranah menu). Reward gold/skor kematian boss + atribusi/popup SLAYER mini/true kini terkunci FASE 14 (baris berikutnya); reward kematian minion + menara + popup gold `+nG` kini terkunci FASE 15 (baris reward minion+menara). |
| Reward kematian boss (FASE 14) | Boss mati hanya dicatat tipenya dan memainkan cinematic; tidak membayar gold/skor, unlock boss baru tersimpan saat menang, tidak ada SLAYER maupun popup `+nG` | `Boss.take_damage → die(source) → GameManager.register_boss_death` mengikuti blok `Game.update` pygame `_core.py:2113–2163`: bayar **nilai runtime `boss.gold_reward`** ke gold+skor PEMAIN, tanpa memandang killer/tim boss, tanpa meta gold/combo/total_kills; `bosses_defeated_this_run` menghitung setiap instans, `bosses_defeated_this_match` dan `unlocked_bosses` unik berurutan. Boss unlock langsung dipersist dan bertahan saat kalah; hero gratis tetap menunggu menang. Guard per instans mencegah callback/tween/tick ganda. `_process_boss_kill` menambah `killer.kills` hanya hero lawan (hero yang sudah mati tetap valid); hanya hero **blue** menambah counter mini/true dan ID dedup in-match + popup `MINI BOSS SLAYER!` / `TRUE BOSS SLAYER!`, deskripsi dan ikon skull persis pygame. **HERO SLAYER tetap DIHAPUS**. Popup pertama-kali `BOSS/TRUE BOSS: … Defeated!` (owned vs tuntutan menghancurkan castle) tetap sesudah SLAYER. `FloatingTextQueue` + `WorldPopups`: gold `+{amount}G` di `(boss.x,boss.y−10)`, RGB `(255,220,50)`, font 18, velocity `(0,−1.5)`, 50 frame; map SLAYER di `(boss.x,boss.y−40)` via cabang critical (pygame menambah `!` lagi), jitter/drift, FIFO/cap 300 (berbagi dengan `DamageNumber` legacy lewat WeakRef), scale dan expiry frame diport. Ekor frame efek selesai sebelum pause cinematic; Main melepas active boss dan mengonsumsi satu pending mini pada frame kematian. Dikunci `boss_death_rewards` / `BossDeathRewardParityTest`; **piksel** font/shadow/glow/komposit cinematic dan audio SFX belum diuji. |
| Reward kematian minion + menara (FASE 15) | Minion merah mati tanpa popup gold `+nG`; reward menara lewat `award_kill` TIM PEMBUNUH (menara merah dihancurkan sumber netral/tanpa killer malah membayar AI — pygame memakai TIM KORBAN), tanpa guard anti bayar ganda, `red_towers_destroyed` belum diaudit sekali-per-menara | Klaster reward minion+menara mengikuti blok `Game.update` pygame `_core.py:2196–2227` lewat `Minion.die()/Tower.die() → GameManager.register_minion_death/register_tower_death` (menggantikan `award_kill` killer): (1) **minion** — dinilai TIM KORBAN: minion RED oleh damage apa pun (hero biru/merah/mati, tower, minion, nexus, boss, self, netral tanpa sumber) membayar gold+skor pemain + `total_kills` + combo, minion biru membayar AI **tanpa** popup; (2) **popup gold `+nG`** — `add_gold_popup(x, y−10, reward)` hanya minion RED (menara & minion biru tanpa popup — pygame tidak memanggilnya), via `FloatingTextQueue`/`WorldPopups` FASE 14: velocity `(0,−1.5)` decay 0.95, lifetime 50, scale 0.3→1.0 spring, x_drift RNG per situs; (3) **menara** — TIM KORBAN: menara RED hancur oleh apa pun membayar gold+skor pemain (nilai runtime `gold_reward` = 100/150), menara biru membayar AI, `total_kills` tidak naik, `red_towers_destroyed` naik TEPAT SEKALI per menara merah (syarat true boss ≥6); (4) **guard** — flag `reward_processed` per instans = `_rewarded` pygame (die() ulang/pukul mayat/callback ganda tidak membayar dua kali; flag hero dibuka lagi saat respawn); (5) urutan operasi persis pygame: gold → score → popup → total_kills → max_combo **dibaca SEBELUM add_kill** (quirk: rantai N kill berurutan → max_combo N−1). Nilai reward runtime diuji (goblin 8/orc 18/troll 45/dark_rider 65, skala nexus, override, tower outer 100/inner 150). Dikunci `minion_tower_rewards` / `MinionTowerRewardParityTest` (20 skenario oracle `Game.update` dua seed); **piksel** font/shadow popup tetap milik bucket piksel FX. |
| Dispatch kematian terpusat (FASE 16) | Sebagian jalur damage menulis HP ≤0 TANPA memanggil `die()`, jadi reward tidak pernah dibayar: peluru menara (`Tower._spawn_bullet`) dan nexus (`Nexus._shoot`), kit boss, kit skill hero (`Hero.kit_hit`), item on-hit, cleave, reflect Bristleback/Thornmail, dan serangan ranged. Hanya `take_damage()` per node yang memanggil `die()` sendiri, sehingga pemanggil yang menulis `hp`/`apply_damage` langsung melewati pembayaran. Sumber peluru juga belum diputus, sehingga peluru menara bisa memberi kill credit dan memantulkan Bristleback — padahal pygame `Bullet._on_hit` memanggil `take_damage` TANPA `source` (`_entity.py:246–248`) | Semua jalur damage Godot lewat `CombatSystem.apply_damage`, jadi keputusan “unit ini mati” ditaruh DI SINI sebagai satu pintu: `death_dispatch_enabled` (default true) + langkah 10 — sesudah mitigasi/shield/reflect/thornmail/on-hit penyerang, persis pygame yang masih mengeksekusi reflect saat korban “baru mati” — jika `dmg > 0` dan `hp <= 0`, `_dispatch_death` memanggil `die()` unit yang benar menurut jenisnya: Hero/Boss `die(source)` (atribusi kill memakai OBJEK source), Tower `die(from_team, source)`, Minion/Nexus `die(from_team)`. Reward/popup/counter tetap lewat `register_*` FASE 13–15 dan tidak membayar dua kali (guard `reward_processed` + guard `is_dead` di tiap `die()`); `Minion.die()` dijadikan idempoten seperti Tower/Hero/Boss. **Source diputus (null)** di peluru menara, peluru nexus, dan serangan minion — paritas `Bullet._on_hit` (`_entity.py:246–248`) dan `Minion.update` (`_entity.py:5580–5581`): peluru/pukulan minion tidak pernah memberi kill credit, reflect Bristleback/Thornmail, maupun blind (semua syarat `source is not None`). `Hero.kit_hit` meneruskan `src` dengan `trigger_on_hit=false`: damage SKILL tetap dispatch kematian + atribusi kill/reflect, tetapi tidak memicu jaket on-hit serangan dasar — persis pygame yang memanggil `take_damage(source=hero, school=…)` tanpa `on_basic_attack_hit`. Dikunci `death_dispatch` / `DeathDispatchParityTest` (21 skenario **jalur serangan nyata**: peluru normal/cannon/ice, melee, proyektil ranged, minion, skill/kit, + guard tanpa kematian dan mayat dipukul ulang). Snapshot per unit HANYA `dead/hp/rewarded/team` — identitas pembunuh sengaja tidak direkam karena `Tower.die(killer_team, _killer)` MEMBUANG killer; atribusi dibaca dari hasil akhirnya (`hero.kills`). **Piksel** damage number/ledakan cannon dan **audio** (menara hancur, minion mati, hentakan proyektil) BELUM TERUJI. |
| UI/HUD in-match (toko/panel/banner/klik/hotkey) | Panel/label/tombol dibangun manual tanpa oracle: income memakai `"%.1f"` engine yang tak terverifikasi, angka cooldown `ceil(detiks)` (60f tampil "1"), gate equip melee `< 110` + magic via `dmg_school` (46 hero role-magic salah), klik tanah kosong = deselect (bukan perintah gerak), tanpa klik kanan, tanpa tombol N, tanpa catatan skor/kill/timer/unlock match, pause tanpa panel, game-over tanpa stat | Seksi fixture `ui_hud` menjalankan draw pygame ASLI headless (82 skenario draw, 31 kasus klik, 28 hotkey, 222 hero predikat, kurva banner 121 titik, baterai touch-rect) dan diputar ulang `UiHudParityTest`. Kanon tunggal `HudLayout.gd`: `format_gold_rate` bit-eksak IEEE-754 (terbukti identik Python: baterai oracle + fuzz 200.000 nilai, 0 beda — `GameManager`/`HUD` delegasi), ribuan/match-time/mode/cooldown (`frames//60+1`), easing banner (slide-in 0.4 BACK OUT → tahan 1.0 → slide-out 0.6 BACK IN + subtitle letterspaced), nama castle (Lv6+ CITADEL), touch-rect 48px (center integer pygame), dan semesta TERTUTUP `ui_key` tombol toko yang diaudit tiap layar. Perilaku yang disamakan: panel hero (`Lv.n`, `hp/max`, `UPGRADE HERO (300G)`/`M A X   L E V E L`, `AUTO-CAST ON` no-op, `ITEM FORGE  (n/6)` → tab item, chip slot → forge, X = deselect), toko (suffix `MAX`/`DIMILIKI`, alasan disabled `MELEE ONLY`/`MAGIC ONLY`/`POOR`/`FULL`/`OWNED` di `ui_data`+tooltip, tanpa tombol jual di Lv1 + fallback +50G via handler, tutup seusai beli hero/bangun menara), gate equip (`range > 80` tolak melee_only; magic via `ItemDB.is_magic_hero` berbasis ROLE), prioritas klik (slot → nexus → hero biru → perintah → menara biru → deselect; tanah kosong + hero hidup = MOVE tetap dipilih; klik kanan = tutup + MOVE), hotkey H (toggle toko, paritas) + B (ekstensi Godot) + N (victory → next; defeat/last diam) + R/ESC, pause (panel 400×400 @(440,160), 4 tombol 300×48 seurutan, mode line), game-over (`VICTORY! LV.n`/`DEFEAT LV.n`, 5 baris stat termasuk `Max Combo` + penanda `NEW BEST!` — dikunci `match_scoring`/`MatchScoringParityTest`, `NEW LEVEL UNLOCKED!`, `NEW HERO: …`, tombol next hanya victory+ada-lanjut). Beda disengaja yang dikunci eksplisit: UI Godot berbahasa Indonesia, toko satu-scroll tanpa halaman (himpunan 33 id direplay), klik musuh = move-to + aggro otomatis (tanpa `follow_target`), baris NEW HERO ditampilkan (pygame menghitung tapi tidak me-render), klik-kanan di atas panel tertelan. Belum teruji/sengaja terbuka: piksel (lebar chip metrik-font, gradien/shadow/dekorasi banner, ikon, kartu item, komposit badge combo + popup achievement), popup unlock geser (350×230), notifikasi tier combo sidepanel pygame, ~~popup gold `+nG` kill minion~~ (terkunci FASE 15 — baris reward minion+menara), bangunan toko di map, sistem taktis (hold G/F/T/C/B/D), kontrol sentuh di layar, dan teks intro level (perilaku/skip-nya milik `CinematicTest`) — combo/`Max Combo`, badge `NEW BEST!`, skor kill-hero +150 + atribusi killer, dan popup achievement `NEW HERO UNLOCKED!` kini TERKUNCI di baris klaster skor + `match_scoring`/`MatchScoringParityTest`. |

## Belum setara — jangan ditandai selesai

- ~~**Reward kematian boss belum membayar gold/skor, tracking unlock langsung,
  popup SLAYER mini/true, dan data/antrean `+nG` belum diport.**~~
  **Ditutup FASE 14** oleh oracle `boss_death_rewards` + replay seluruh
  daftar headless `BossDeathRewardParityTest` (lihat tabel dan seksi tes).
  Yang **murni piksel tetap BELUM teruji**: raster/font, anti-alias,
  shadow/glow, ikon skull/ellipsis judul, penumpukan popup terhadap
  flash/dissolve/perayaan boss dan camera shake. SFX dipanggil tetapi
  bunyi/mix tidak diverifikasi headless. Ini bukan sertifikasi visual
  atau audio seluruh efek kematian boss.

- ~~**Popup gold `+nG` kematian minion belum diport, reward menara masih
  membayar tim pembunuh (bukan tim korban), dan kematian minion/menara
  tanpa guard anti bayar ganda.**~~
  **Ditutup FASE 15** oleh oracle `minion_tower_rewards` + replay seluruh
  daftar headless `MinionTowerRewardParityTest` (lihat baris tabel reward
  minion+menara dan seksi tes). Yang TETAP TERBUKA di jalur ini,
  eksplisit: (1) **piksel** popup gold (raster font, shadow, anti-alias,
  penumpukan vs FX lain) — data/antrean/gerak/scale/lifetime sudah
  terkunci; (2) ~~**dispatch kematian pre-existing**~~ — **DITUTUP
  FASE 16**: `CombatSystem.apply_damage` langkah 10 `_dispatch_death`
  kini memanggil `die()` untuk SEMUA jalur damage lethal (peluru
  menara/nexus, kit boss/hero, item on-hit, cleave, reflect, ranged),
  dikunci oracle `death_dispatch` + `DeathDispatchParityTest`;
  (3) **jual menara** tidak menghasilkan refund
  reward di KEDUA engine (paritas, bukan gap); (4) regen/aura nexus
  menghidupkan unit tanpa reset flag `reward_processed` (pariter dengan
  pygame `_rewarded` yang juga tidak direset oleh mekanik itu).

- **UI/HUD/toko/menu:** perilaku in-match kini diuji oracle (`ui_hud` +
  `UiHudParityTest` — lihat tabel di atas: format, banner, biaya, gate,
  klik, hotkey, pause, game-over, audit `ui_key`). Klaster SKOR match
  (combo/`Max Combo`, badge `NEW BEST!`, kill hero +150 + atribusi
  killer, popup achievement `NEW HERO UNLOCKED!`) juga sudah terkunci
  (`match_scoring`/`MatchScoringParityTest` — lihat baris tabel klaster
  skor). Yang TETAP TERBUKA, eksplisit: (1) **piksel** — lebar chip
  (metrik font), gradien/shadow/dekorasi banner, ikon skill, kartu item,
  komposit visual badge combo + popup achievement (termasuk truncation
  ellipsis judul yang bergantung metrik font), dan seluruh komposit
  lain belum lolos perbandingan screenshot; (2) **popup unlock geser**
  (geometri 350×230 tercatat di fixture tapi Godot hanya menampilkan
  baris teks) — popup achievement SUDAH diport (`AchievementPopup.gd`);
  (3) **bangunan toko di map** (klik gedung ITEM FORGE/HERO SHOP —
  Godot membuka toko via B/H); (4) **sistem taktis**
  (`tactical_commands.py`: hold G/F/T/C/B/D — belum diport; B dipakai
  Godot sebagai toggle toko) + notifikasi tier combo sidepanel pygame
  (`beri_tahu_global` — Godot tanpa sidepanel); (5) **kontrol sentuh
  di layar** (data tombol+visibilitas diport di `HudLayout`, UI-nya
  belum ada); (6) **teks intro level** (sudah diport visual, replay
  teks belum ada — `CinematicTest` mengunci perilaku/skip);
  (7) **transaksi Hero Shop meta** di `MainMenu.gd` belum punya oracle
  sendiri; (8) beda kecil yang didokumentasikan di kode: hero mati +
  klik kosong menutup juga tokonya di Godot (pygame membiarkan
  `shop_open`), klik kanan di atas panel toko tertelan (pygame menutup
  popup dari mana saja), baris stat + `MUNDUR` di panel hero adalah
  tambahan Godot.
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
  Yang SUDAH setara + teruji dari blok ini termasuk **sumber jumlah unlock
  catch-up** (`hero_catchup_unlocks`/`HeroCatchupUnlockParityTest`: kunci
  save, auto-grant starter, hitungan `boss_unlocks_for_purchases`, stat hero
  hasilnya, dan jaminan unlock save lama tidak hilang). Reward/atribusi/unlock kematian boss juga
  sudah teruji di FASE 14 (`boss_death_rewards`); rincian di bawah. Yang TETAP TERBUKA
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
  pygame menghitung subtitle ini tapi tidak me-render-nya) DAN popup
  achievement `NEW HERO UNLOCKED!` kini ikut diport + dikunci
  (`GameManager.unlock_achievement` → signal → `AchievementPopup.gd`,
  fixture `match_scoring` — lihat baris tabel klaster skor). Yang tetap
  terbuka di jalur ini: tampilan **BEST SCORE/best time per level di
  LEVEL SELECT** pygame (`_core.py:4257-4271` + `SaveManager.format_time`)
  belum diport — data `level_stats` sudah ditulis ke save, UI menu-nya
  belum; (5) slot save tunggal + `level_stats` Godot baru terisi sejak
  port ini (save lama tidak dimigrasi — backfill `level_stats: {}`,
  statistik mulai terkumpul dari sekarang, isi lama pygame tidak
  diimpor).
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

# Seluruh runtime di bawah memakai user:// sementara, BUKAN save pengguna:
export XDG_DATA_HOME="$(mktemp -d)"
trap 'rm -rf "$XDG_DATA_HOME"' EXIT

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
godot --headless --path godot res://tests/MatchScoringParityTest.tscn --quit-after 300
godot --headless --path godot res://tests/BossDeathRewardParityTest.tscn --quit-after 600
godot --headless --path godot res://tests/MinionTowerRewardParityTest.tscn --quit-after 600
godot --headless --path godot res://tests/DeathDispatchParityTest.tscn --quit-after 600
python3 godot/tools/test_godot_log_gate.py
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

`BossDeathRewardParityTest` memutar ulang **seluruh** seksi
`boss_death_rewards` (objek JSON, bukan pembacaan string kode). Oracle
menjalankan `Boss.take_damage`, `Game.update`, `_process_boss_kill`,
`_unlock_achievement`, `EffectManager.add_gold_popup`/`FloatingText.update`
dan write+reload `SaveManager` pygame ASLI; sumber damage tidak ikut
simulasi arena, income/wave dibekukan, FX kontak hit diisolasi dari
klaster reward. Dua seed berbeda wajib menghasilkan jejak identik.
Daftar headless tertutup yang **semuanya direplay**, bukan hanya dicatat:

1. **216 boss**: nama/kelas/nilai reward dari instans asli, reward tidak
   berubah oleh hard scaling, payout runtime gold/skor/AI/counter.
   Set tipe harus sama persis dengan `BossDB` (hilang/asing/ganda gagal).
2. **37 skenario `Game.update`** pada Main/HUD/Boss/Hero/Minion/Tower/Nexus
   Godot nyata: last-hit hero blue/red/netral/hero mati, tower/minion/
   castle/boss/self/tanpa sumber, tim sama vs lawan, source berbeda dari
   `from_team`, nonlethal → last-hit berubah, guard alive/defeated, null
   active boss, callback ganda, boss tipe sama berulang, counter mini/true
   independen, ID achievement dedup, reward runtime 0/17/123456, hard
   scaling, owned vs belum-owned, unlock lama, flag damage numbers off,
   jeda cinematic dan pending mini pada frame yang sama. Snapshot
   gold/skor/ai_gold/total_kills/combo/max_combo/killer.kills, daftar
   tracking, event popup, current/queue/timer achievement, **semua field
   non-piksel** floating text, posisi+nominal event gold, data save +
   jumlah/urutan write sungguhan dibandingkan rekursif (key asing juga
   gagal). Kill hero biasa diuji eksplisit **tanpa HERO SLAYER**.
3. **5 baterai antrean**: formatting (0, negatif, angka besar), posisi
   pecahan/negatif, RGB/font/critical, lifetime 50 frame + gerak/scale,
   drift, FIFO 302 entri → cap 300, buang tertua, expiry tidak menghapus
   popup baru, gold tetap muncul meski damage numbers off/cap kualitas 1,
   campuran teks SLAYER + gold dengan anggaran damage 2. RNG hanya situs
   `FloatingText.__init__`/`add_damage_number` yang di-pin: jenis/range/
   nilai/jumlah/urutan panggilan ikut direplay lewat Callable lokal queue.
   Akumulator diuji dua half-frame per frame, bukan hanya fungsi tick.
   **3 baterai FIFO bersama** juga mempertemukan node `DamageNumber`
   legacy nyata dengan popup gold (damage→gold, gold→damage, flag off),
   termasuk disposal node lama; batas 300 bukan antrean gold terpisah.
   Soft-cap pygame membuang SATU entri tertua, bukan menguras sampai
   cap kualitas. Renderer lama tetap menggambar dirinya sendiri; adapter
   WeakRef hanya menyatukan FIFO/budget, bukan mengklaim pikselnya setara.
4. **Menang dan kalah**: `end_match` sungguhan + reload disk; boss unlock
   sudah persisten sebelum hasil, kalah tidak memberikan hero gratis,
   menang menambah hero + popup `NEW HERO UNLOCKED!` tanpa membayar ulang
   gold/skor boss. Sentinel data lain dan meta gold tetap benar.
5. **Lifecycle**: counter/list/ID dari `Game.reset` pygame vs `start_level`
   Godot; popup match lama dibuang, menu melepas binding `unlocked_bosses`
   tanpa `clear()` milik save; match berikutnya bisa rebind unlock lama.

CI menjalankan scene ini dengan `XDG_DATA_HOME` baru agar save pengguna
bahkan tidak dibaca/ditulis bila harness berhenti di tengah. Harness juga
mem-snapshot/memulihkan data+file seperti `MatchScoringParityTest`.
`SaveManager.saved` diamati setelah file ditutup, bukan mock save yang
selalu sukses. Gate mewajibkan `[BossDeathRewardParityTest] PASS` dan
menolak error runtime **serta baris `[...Test] FAIL` meskipun ada PASS**;
5 regresi Python untuk gate turut dijalankan. Fixture lama tetap identik;
kode pygame tidak diubah untuk menyesuaikan port.

`MatchScoringParityTest` memutar ulang seksi fixture `match_scoring`
(objek biasa, bukan string kompak) atas kode Godot yang sebenarnya.
Oracle pygame menjalankan `Game.update` SUNGGUHAN headless (Game +
Minion/Hero/Tower betulan, kematian lewat `take_damage` asli, dua run
seed beda harus identik, dan guard internal menolak perubahan state di
langkah tanpa kill ter-script). Yang direplay: (1) mesin state
`ComboCounter` murni per frame — count/timer/last_combo/color_flash/
display_scale/target_scale, termasuk quirk `max_combo` yang dibaca
SEBELUM `add_kill` dan expiry 120 frame; (2) data draw combo dari draw
pygame asli — label ambang, warna dasar + pulsa flash (ruang 0..255),
anchor (W−100, 100), label (cx, cy−30), bar 80×4 @(cx−40, cy+40) +
lebar isi per sisa timer; (3) 9 skenario reward `Game.update` —
gold/score/ai_gold/total_kills/max_combo/combo per frame + atribusi
`killer.kills` (kill netral/self/tower/minion tanpa atribusi, +150 tim
korban, respawn 600 frame tanpa bayar ganda) pada node Minion/Hero/
Tower ASLI yang di-step `GameManager._tick_combo`/`_update_hero_
respawns` 1/60 per frame script; (4) `SaveManager.get/update_level_
stats` (9 kasus: flag NEW BEST, best hanya saat menang, max_combo
all-time, time 0 diabaikan) pada dict awam tanpa menyentuh save; (5)
state machine `AchievementPopup` (antrean, 180 frame, pengganti di
frame yang sama) + kurva slide 181 titik + teks/warna panel; (6)
trigger popup `NEW HERO UNLOCKED!` dari `_auto_unlock_defeated_boss_
heroes` via signal `achievement_unlocked` (5 kasus termasuk sudah-
owned → tanpa popup); (7) integrasi `end_match` penuh — `start_level`
+ `end_match` menulis `level_stats` save, menyalakan flag NEW BEST,
baris panel game-over (Max Combo + NEW BEST! + NEW HERO), dan memancarkan
popup; defeat menulis statistik tanpa best. Harness mem-snapshot
`SaveManager.data` DAN berkas `user://mystic_save.json` lalu memulihkan
keduanya. Regenerasi fixture HANYA bila `_core.py`/`_render.py`/
`_system.py`/`_entity.py` berubah.

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

`MinionTowerRewardParityTest` memutar ulang **seluruh** seksi
`minion_tower_rewards` (objek JSON, 20 skenario) pada node
Minion/Hero/Tower Godot ASLI + `GameManager` sungguhan. Oracle
menjalankan `Game.update` pygame ASLI headless (`_core.py:2196–2227`
dipanggil betulan, kematian lewat `take_damage` asli, dua run seed beda
harus identik, FX kontak hit diisolasi dari jejak, guard internal
menolak perubahan state di langkah tanpa kill ter-script). Skenario
mencakup: minion merah oleh hero biru/mati/merah, tower, minion, nexus,
boss, self, netral tanpa sumber, override `team:""`, variasi jenis
minion (goblin/orc/troll/undead/dark_rider + skala nexus), menara
outer/inner kedua tim, kematian beda tim + jenis campur SATU FRAME,
10-kill berurutan (quirk max_combo 9), 6-kill berjeda (max_combo 5),
expiry combo 120 frame, antrean popup FIFO teracak-deklarasi,
flag damage numbers off (popup gold tetap muncul), dan unit
dead-on-spawn (minion + menara). Kunci anti bayar ganda TIGA lapis:
pukul mayat
(`take_damage` ulang pada unit mati), `die()` ulang, dan callback
`register_*_death` langsung — semuanya tak boleh membayar/popup/counter
dua kali; flag hero dibuka lagi saat respawn. Dibandingkan rekursif
closed-world per langkah: gold/score/ai_gold/total_kills/max_combo/combo
(count/timer/last_combo)/red_towers_destroyed/kills
(unit+sources)/rewarded/seluruh field non-piksel floating text/
gold_events posisi+nominal/daftar+urutan konsumsi RNG popup. Dua seed
harus identik. Harness men-step `GameManager._tick_combo`/
`_update_hero_respawns`/`world_popups.advance` 1/60 per frame skrip
(pola `MatchScoringParityTest` — income dibekukan `GOLD_PER_SECOND=0`
di oracle); cinematic di-clear dan SceneTree di-unpause supaya tick
manual berjalan. Regenerasi fixture HANYA bila `_core.py`/`_entity.py`
berubah.

`DeathDispatchParityTest` memutar ulang **seluruh** seksi `death_dispatch`
(objek JSON, 21 skenario) pada node Hero/Minion/Tower Godot ASLI +
`GameManager`/`CombatSystem` sungguhan. Beda penting dari FASE 15: oracle
TIDAK memakai `take_damage(10**9)`, melainkan **jalur serangan pygame
sunnguhan** — `Tower._shoot → Bullet.update → Bullet._on_hit`
(`take_damage(dmg, team, 'projectile')` TANPA source), `Hero._do_attack`
(melee instan `source=hero, school=…`; ranged lewat `_spawn_projectile` +
`Hero.update`), `Minion.update` (`take_damage(dmg, team)` netral), dan
`take_damage(source=hero, school=…)` untuk jalur skill/kit — lalu loop
reward `Game.update` membayar di frame berikutnya. Godot mereplay lewat
jalur produksi yang sama: `Tower._shoot(CombatSystem)` → `TowerBullet`
diterbangkan dengan `_physics_process` manual (deterministik) →
`_on_hit` → `apply_damage`; `Hero.try_attack()`; `Minion.try_attack()`;
dan `CombatSystem.apply_damage` langsung untuk skill/DoT. **Tidak ada**
`register_minion_death`/`register_tower_death`/`register_hero_death`
manual dan **tidak ada** `die()` langsung — reward boleh muncul HANYA
sebagai akibat dispatch, dan `_run_kill` pola FASE 15 sengaja tidak
dipakai karena justru melewati dispatch yang diuji.

Skenario: menara membunuh lewat peluru **normal/cannon (+splash 60%)/ice**,
menara membunuh menara, **hero melee** membunuh minion & hero, **hero
ranged** (proyektil) membunuh minion/menara/hero, **minion** membunuh
menara & minion, damage **skill/kit** membunuh minion & hero, **guard
tanpa kematian** (menara/minion/hero + `direct` 99.999 damage dengan HP
sisa > 0 — dispatch wajib diam total), dan **mayat dipukul ulang**
(dibayar tetap sekali). Dua skenario membuktikan klaim source: korban
ber-`_bristleback_active` yang dipukul **peluru** tidak memantulkan apa
pun (HP menara utuh), sedangkan korban yang sama dipukul **melee hero**
memantulkan 25% ke penyerang — tanpa pasangan ini absennya reflect bisa
saja cuma karena Bristleback tidak pernah aktif. Guard internal oracle
menolak: unit mati di skenario guard, reward tanpa kematian, counter
bergerak tanpa kematian, HP unit non-korban bergerak tanpa script, dan
`kills` hero naik di skenario peluru mana pun. Inventory item dibiarkan
kosong sehingga **tidak ada situs RNG sama sekali** (`roll_crit` berhenti
di `chance <= 0`; evasion/blind/block hanya roll saat peluangnya > 0) —
dua seed berbeda wajib identik. Snapshot dibandingkan rekursif
closed-world per langkah: gold/score/ai_gold/total_kills/max_combo/combo
(count/timer/last_combo)/red_towers_destroyed + per unit
`dead/hp/rewarded/team` + `hero_kills`. Snapshot PRA-serangan ikut
dibandingkan supaya kegagalan menunjuk ke setup, bukan ke dispatch.
Regenerasi fixture HANYA bila `_core.py`/`_entity.py`/`hero_items.py`
berubah.

CI `godot-check.yml` memeriksa freshness fixture dan log runtime. Sukses berarti
ada penanda `PASS` **dan** tidak ada `SCRIPT ERROR`, `Parse Error`, atau
`Compile Error`; exit code Godot saja tidak cukup.

### Hasil validasi perubahan ini

- **FASE 16 — dispatch kematian terpusat (uji lanjut PR #193):** oracle
  freshness lulus lokal dengan `/tmp/parity-venv/bin/python
  tools/test_godot_match_parity.py` (pygame-ce 2.5.8): seksi baru
  `death_dispatch` berisi 21 skenario serangan nyata + 22 serangan
  (tower_bullet×8, hero_melee×4, hero_ranged×4, minion_attack×2,
  skill×2, direct×2), 16 kematian terbayar, 6 skenario guard tanpa
  kematian; dua seed berbeda identik dan seluruh guard internal oracle
  lulus. `--write-fixture` menghasilkan **3.039 baris insert-only** —
  semua seksi fixture lama byte-identik, tidak ada perubahan kode
  runtime pygame, dan save pengguna tidak disentuh
  (`XDG_DATA_HOME=$(mktemp -d)` + `MYSTIC_SAVE_DIR` sementara). Blok
  print `main()` menambah baris `death-dispatch oracle`. Cek statis CI
  langkah 1 lulus lokal: `gdparse` seluruh `.gd` (termasuk
  `DeathDispatchParityTest.gd`), `tscn_lint` 27 scene (termasuk
  `DeathDispatchParityTest.tscn`), `check_refs`, `particles_lint`
  (91 berkas), 5 self-test `godot_log_gate`, `gen_boss_smart_ai --check`,
  `gen_hero_skill_kit --check`, dan `check_bosskit_scope`. Langkah CI
  baru **4l** menjalankan `DeathDispatchParityTest --quit-after 600` di
  user-data terisolasi melalui `godot_log_gate.py`.
  Ronde CI pertama menemukan **tiga drift harness nyata** yang semuanya
  sudah diperbaiki (bukan dilonggarkan): (1) `Hero.__init__` menskala
  `base_hp`/`base_damage` lewat `hero_balance.starter_catchup_stats`
  dengan input `game_instance.purchased_heroes` (`_entity.py:3355-3360`) —
  `make_match_scoring_fixture` (FASE 13) membeli hero dan **tidak
  memulihkan** `__main__.game_instance`, sehingga di proses yang sama
  grimjaw lahir 1093/dmg 41 alih-alih 1120/42; kini `purchased_heroes`
  di-pin kosong di oracle dan `GameManager.purchased_heroes = []` di
  harness Godot; (2) `Hero._passive_heal` 0.15/frame (`_entity.py:3763-3766`)
  menggeser HP korban yang selamat tiap frame — dibekukan di oracle,
  paritas harness Godot yang men-`set_physics_process(false)` sehingga
  `PASSIVE_HEAL_PER_SEC` tidak jalan; (3) selisih 1 damage pada troll
  (763 vs 762) dan Thorne (1958 vs 1957) ternyata **gejala** dari (1),
  bukan bug mitigasi armor — hilang setelah catch-up di-pin. Setelah
  perbaikan, seluruh nilai yang di-flag CI cocok dengan keluaran Godot
  (h0 1120, m0 762, h0 486, h1 1957, attacker 1113, korban 471) dan
  perubahan fixture tetap **terkurung di seksi `death_dispatch`**
  (47 baris, semua ≥ baris 102801; seksi lain byte-identik).
  **Yang TIDAK terverifikasi lokal, eksplisit:** binary Godot 4.3 tidak
  bisa diperoleh di sandbox (release-assets.githubusercontent.com,
  downloads.godotengine.org, conda/ghcr/nix/nuget semuanya diblokir;
  kompilasi dari sumber tidak layak pada 2 CPU / 3 GB RAM), jadi
  `DeathDispatchParityTest` sendiri **maupun regresi FASE 13/14/15 dan
  seluruh daftar headless lainnya tidak dijalankan lokal** — semuanya
  diverifikasi oleh CI PR ini (`gh run watch --exit-status`) dengan
  binary Godot 4.3 standar. Tidak mengklaim pixel/audio parity, tidak
  mengklaim game 100% ekuivalen, dan tidak ada uji Android.

- **FASE 15 — reward kematian minion + menara:** oracle freshness lulus
  lokal: 20 skenario `Game.update` baru (dua seed berbeda identik),
  **semua seksi fixture lama byte-identik** (diff 6.538 baris
  insert-only); tidak ada perubahan kode runtime pygame atau save
  pengguna. `MinionTowerRewardParityTest` lulus **7.993 pemeriksaan**
  dengan Godot **4.3.stable.custom_build** headless lokal melalui gate
  log (PASS + tanpa script/parse/compile error). Ke-13 scene regresi
  lama juga PASS: Gameplay (1.455 checks), Battle, AIPlayer,
  Cinematic, BossCore (3.717), BossSmartAI, HeroSkill,
  HeroBasicAttack, HeroRngGuard, HeroCatchupUnlock, UiHud (1.159 —
  harness award_kill diganti register_*_death node asli),
  MatchScoring (901), BossDeathReward (39.729). `gdparse`, scene/ref/
  particle lint, dua generator `--check`, scope-check, 5 regresi
  log-gate, serta regresi pygame achievement-command, aura boss (46),
  basic-attack-no-impact, damage-school (36), dan easy-mode AI lulus.
  Engine lokal dibangun tanpa backend renderer karena unduhan binary
  diblokir sandbox. CI PR menjalankan binary Godot 4.3 standar,
  termasuk langkah baru `MinionTowerRewardParityTest --quit-after 600`
  di user-data terisolasi; checks CI wajib hijau sebelum squash-merge.
  Tidak mengklaim pixel/audio parity atau uji Android; gap dispatch
  kematian pre-existing didokumentasikan terbuka (bukan ranah fase ini).

- **FASE 14 — reward kematian boss:** oracle freshness lulus lokal:
  216 boss, 37 skenario `Game.update` (dua seed berbeda), 5 baterai
  antrean floating + 3 baterai FIFO bersama `DamageNumber`, 2 hasil
  akhir match (menang/kalah) dan reset. **Semua seksi fixture lama
  byte-identik**; tidak ada perubahan kode runtime pygame atau save
  pengguna. `BossDeathRewardParityTest` lulus **39.729 pemeriksaan**
  dengan Godot **4.3.stable.custom_build** headless lokal, melalui gate
  log (PASS + tanpa script/parse/compile error atau assertion FAIL).
  Ke-12 scene regresi lama juga PASS: Gameplay (1.455 checks), Battle,
  AIPlayer, Cinematic, BossCore (3.717), BossSmartAI, HeroSkill,
  HeroBasicAttack, HeroRngGuard, HeroCatchupUnlock (836), UiHud (1.159),
  MatchScoring (901). `gdparse`, scene/ref/particle lint, dua generator
  `--check`, scope-check, 5 regresi log-gate, serta regresi pygame
  achievement-command, aura boss (46), basic-attack-no-impact,
  damage-school (36), dan easy-mode AI lulus. Engine lokal dibangun
  tanpa backend renderer karena unduhan binary diblokir sandbox;
  pesan `No renderers available` bukan hasil audit piksel. CI PR
  menjalankan **binary Godot 4.3 standar**, termasuk langkah baru
  `BossDeathRewardParityTest --quit-after 600` di user-data terisolasi;
  checks CI wajib hijau sebelum squash-merge. Detail run ada pada
  checks PR FASE 14. Tidak mengklaim pixel/audio parity atau uji Android.

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
- Fase klaster skor (FASE 13): oracle `match_scoring` lulus lokal
  (`tools/test_godot_match_parity.py` — 5 kasus combo, 9 skenario reward
  `Game.update` pygame asli × double-run seed beda, 9 kasus level-stats,
  3 kasus popup + 181 titik slide + 5 trigger NEW HERO; seksi lama
  fixture byte-identik — sisi pygame TIDAK disentuh),
  `gdparse`/`tscn_lint`/`check_refs`/`particles_lint` + `gen_* --check` +
  scope-check lulus lokal. Tidak ada Godot headless lokal di lingkungan
  kerja — replay `MatchScoringParityTest` (termasuk integrasi end_match
  penuh) diverifikasi lewat CI `godot-check.yml` pada PR (langkah baru
  setelah `UiHudParityTest`, `--quit-after 300`); gate lulus = penanda
  `PASS` dan tanpa `SCRIPT ERROR`/`Parse Error`/`Compile Error`.
  Efek nyata: kill hero merah kini +150 gold/skor (hero biru membayar
  AI), rantai kill minion merah menghidupkan combo kanan-atas
  (`x{n}` + label KILLING SPREE! dst + bar 2 detik), panel game-over
  menampilkan `Max Combo: x{n}` dan penanda `NEW BEST!` pada Final
  Score/Match Time saat rekor per level pecah (save `level_stats`), dan
  menang dengan boss baru memunculkan popup `NEW HERO UNLOCKED!`
  (antrean 3 detik, slide dari kanan).
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
