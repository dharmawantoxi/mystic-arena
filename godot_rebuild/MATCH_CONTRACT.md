# Kontrak prototipe pertandingan — wave, gold, build/sell

Mode **Pertandingan awal** di `scenes/prototype/PrototypeMatch.tscn` merupakan subset **level 1 / normal**. Bukan port seluruh `LEVEL_1`, bukan AI asli, dan bukan pengganti game Python yang sudah rilis. Ketiga laboratorium lama tetap terpisah. Nexus biru bisa di-upgrade 1–5, lihat [kontrak nexus](NEXUS_CONTRACT.md); merah tetap tier 1.

## Sumber perilaku

- `_core.py`: `compute_starting_gold`, `compute_gold_per_second`, `Game.reset`, `Game.update` (income), `Game.update_waves`, `Game._get_wave_composition`, `Game._generate_build_slots_from_lanes`, `Game.try_build_tower`, `InputHandler._try_sell_tower`.
- `_entity.py`: `Tower.sell_value`; aturan Archer/nexus mengikuti [kontrak siege](SIEGE_CONTRACT.md).
- `levels/level_data.py`: `LEVEL_1.starting_gold` **1000**. Konstanta legacy `STARTING_GOLD = 350` bukan saldo awal pemain level 1; lawan memakai 350.
- `tests/match_source_oracle.py` mengeksekusi AST metode sumber tersebut tanpa mengimpor Pygame. Hanya dependensi luar scope yang diganti stub: efek/audio, konstruksi minion (untuk mencatat spawn), boss dan auto-upgrade castle lawan. Numerik Tower untuk sale berasal dari metode sumber.
- `tests/fixtures/match_source.json`: dua trace 3.800 tick, komposisi wave, seluruh 18 slot, 12 skenario income dan transaksi build → UI sale. Oracle harus tetap cocok terhadap sumber; runner native membandingkan GDScript terhadap fixture yang sama.

## Clock dan komposisi

Semua waktu adalah **physics tick 60 Hz**, bukan frame render.

1. Reset: wave 0, timer 300, spawn timer kedua tim 0, antrean kosong.
2. Income diproses sebelum scheduler. Timer wave positif dikurangi satu; pemeriksaan wave baru ada pada cabang `elif`, bukan pada tick timer baru menjadi nol.
3. Wave baru hanya dimulai bila timer habis, kedua antrean kosong, dan tidak ada minion hidup. Bangunan **dan hero** tidak menghalangi pemeriksaan ini.
4. Antrean spawn terus dikuras saat timer wave berjalan. Maksimal satu minion per tim setiap 20 tick; blue lalu red; lane atas → tengah → bawah.
5. Spawn timer tetap bertambah ketika idle. Pasangan pertama muncul **tick 301**, berikutnya 321/341/…/461 untuk wave 1 (9 unit per tim).
6. Timer setelah mulai wave = 1500. Jika lapangan selalu bersih, wave berikutnya paling cepat tick **1802**, lalu **3303**. Bila unit masih hidup, timer boleh nol tetapi wave tidak melompat.
7. Komposisi didasarkan pada **castle level per tim + nomor wave**, bukan baris tabel berdasarkan nomor wave saja. Tabel tier-1 di bawah adalah kasus awal; tier 2–5 memakai base berbeda, lihat [kontrak nexus](NEXUS_CONTRACT.md).

| Wave | Komposisi tier-1 per lane/per tim |
|---|---|
| 1–3 | Goblin ×3 |
| 4–6 | Goblin ×3, Orc |
| 7–9 | Goblin ×3, Orc, Undead |
| 10–12 | Goblin ×3, Troll, Dark Rider, Undead |
| 13+ | Goblin ×3, Troll ×2, Dark Rider ×2, Undead |

Wave memanggil aturan shield nexus sumber: gratis sampai wave 10. Paid shield belum dibeli via UI. Tidak ada tombol skip/manual wave. Pertarungan tertentu dapat menahan wave karena unit yang masih hidup; jangan menghapus gate ini hanya agar countdown selalu maju.

## Ekonomi lokal pertandingan

- Blue **1000 G**, red **350 G** saat reset. Tidak ada currency permanen, unlock, save atau koneksi layanan.
- Rumus awal sumber: `int((base + (max(1, level) - 1) × 100) × multiplier)`. Easy 1,25; normal 1; hard 0,75; nilai lain 1. Fungsi formula diuji, dan aturan difficulty sumber sudah tersambung ke world: `set_difficulty()` menyalakan enemy scaling hanya untuk `hard` (level config × 1.15/1.10/1.0), minion merah memakai potongan `int()` itu di atas tier nexus, dan castle-start level biru/merah mengikuti config. Selector level/difficulty di UI **belum tersedia** (sumber memilihnya di settings screen).
- Blue menerima `(3 + (max(1, level) - 1) × 0,3) × multiplier` G per detik. Tiap 60 tick, `round(rate × 1000)` dengan ties-to-even Python ditambahkan ke carry milli-gold, kemudian quotient menjadi gold integer dan remainder disimpan.
- Red menerima `3 + max(0, wave)` G tiap 60 tick. Income aktif saat persiapan, berhenti saat pause/hasil.
- Kill minion/tower masuk ke wallet tepat satu kali melalui selisih kredit authoritative death path. Nexus tidak memberi hadiah kill tower.
- Ledger tiap tim: **saldo = pembukaan + pasif + kill + refund − belanja**. Semua mutasi ekonomi prototipe harus mempertahankan invariant ini.

## Slot dan transaksi

- 9 slot per tim. ID blue 0–8, red 9–17; masing-masing dikelompokkan lane atas/tengah/bawah.
- Titik berasal dari `path[min(int(len(path) × fraction), len(path) − 1)]`, tanpa offset Y minion.
- Blue atas/bawah: 0,15 / 0,30 / 0,45; tengah 0,10 / 0,25 / 0,40.
- Red atas/bawah: 0,85 / 0,70 / 0,55; tengah 0,90 / 0,75 / 0,60.
- Archer tier 1 berharga **100 G**. Verifikasi match aktif, ownership, slot kosong, saldo dan kapasitas **sebelum** spawn/debit. Tidak ada `await`/callback di tengah transaksi.
- Jual tower blue **tier 1** yang hidup mengembalikan **50 G**; refund tier 2–6 mengikuti [kontrak upgrade](UPGRADE_CONTRACT.md), ditambah 425 G bila Regen Shield dibeli melalui domain ([kontrak shield](SHIELD_CONTRACT.md)). `Tower.sell_value()` level 1 di Python sendiri bernilai 0; refund 50 berasal dari fallback **UI** `_try_sell_tower`. Memeriksa entity saja menghasilkan harga salah.
- Sale bukan death: tidak menambah kill atau memberi lawan gold. Bersihkan registry, slot dan projectile terkait. ID tidak didaur ulang; repeat/stale sale tidak dapat menyentuh pengganti tower di slot yang sama.
- UI hanya menangkap satu command build/sell/upgrade/nexus per tick. Upgrade Archer dan nexus membawa expected level. Pergantian seleksi tidak mengubah target command yang sudah ditangkap. Domain memvalidasi ulang ketika dieksekusi. Pause/focus loss membatalkan command tertunda.
- UI tidak boleh menjual nexus, tower lawan, tower mati atau membuat tower di slot lawan. Meskipun UI dilewati, domain tetap menolak.

## Lawan sementara dan perbedaan disengaja

- **Lawan sudah `AIPlayer`.** Defender sementara (tiga Archer terjadwal) dibuang di lapisan 6e; sisi merah sekarang memakai port `AIPlayer` penuh (jadwal, draft, build, upgrade, item, shield) dengan ledger yang sama dan RNG ter-seed. Sakelar satu-satunya adalah `set_ai_enabled()`/`ai_enabled`; detail layer dan run ada di [AI_CONTRACT.md](AI_CONTRACT.md).
- **Slot hancur dibebaskan.** Sumber terlihat membersihkan `taken` ketika sale, tetapi tidak pada destruction; port sengaja memperbaikinya.
- **Backpressure:** cap 120 minion menahan entri antrean yang belum terkirim, bukan menghilangkannya. Dua nexus + 18 slot memerlukan cap 20 struktur dalam mode ini; cap 16 laboratorium siege tidak berubah. Cap projectile 256 dan event 64 diwarisi.
- Jitter spawn wave sudah diport (layer 7b): `uniform(-8, 8)` pada x/y lalu offset lane `-20/0/20`, dengan stream ter-seed supaya replay identik (aliran `random` Python tidak direproduksi). Castle scaling lawan juga sudah diport (layer 7a). Sumber tidak punya rutin separation terpisah — spread-nya hanya offset lane + jitter ini. Yang masih belum: sebagian besar sistem produksi. **Inti entity boss sudah diport (layer 8a)**: `scripts/match/boss_state.gd` + `data/bosses/boss_stats.json` (216 tipe dari `bosses/boss_data.py`), diuji `tests/boss_core_checks.gd`. **Kondisi match boss layer 8b juga sudah diport** di `scripts/match/prototype_battle.gd`: jadwal mini acak, pending FIFO, spawn mini/true, counter `red_towers_destroyed`, reward dan daftar unlock; oracle `match_source_oracle.py` + `tests/boss_match_checks.gd` menguncinya. **Layer 8c menambah** movement waypoint/chase, target terdekat, basic physical attack, cooldown/facing, cleave dan hero target/death registry; `boss_motion_source_oracle.py` + `boss_motion_checks.gd` menguncinya. **Layer 8d menambah** generic ability, smart AI slice awal Gornak/Morgath/Drakar/Abaddon, Q/W/E/R timers, active-skill/cooldown clocks dan true-boss heal; sub-layer 8d-1 menambah smart AI Alchemist, Malzareth, Akashari, Vorenmarr, Nyxarath, Thalgryn, Syrentha, Gravewake, Kunkka, Razak, Kenshiro, Khazan, Wiro, Naraka, Krognarr, Raz, Vraskhan, 41 boss L9 tersisa dan final 17 non-L9 (ancient_apparition, ignis_drachorn, vhorethzir, vaerith, xirthalis, vhyssarion, khalros, gorath, varkul, xerathis, nyzrak, zharok, pyrenth, vokrahn, nyxara, gravefang, vhalzun); `boss_ability_source_oracle.py` + `boss_ability_checks.gd` mengunci parity source (fixture 319 kasus, 79 boss). **Layer 8e**
menambah `boss_clock_source_oracle.py` + `boss_clock_checks.gd`: entrance gate
mini/true, `anim_time`/`pulse`, threshold enrage, modifier sekali, cooldown pulse
dan interaksi slow. **Layer 8f** menambah presentasi intro/death boss saja:
`boss_presentation_source_oracle.py` + `boss_presentation_checks.gd` mengunci
entrance aura/text, death snapshot dan FX tick setelah registry cleanup.
**Layer 8g** menambah jam status/item debuff `TowerDebuffMixin`, burn dan
modifikasi heal boss: `BossState.tick_tower_debuffs()` memajukan clock satu kali
sebelum stun/entrance gate; burn mengakumulasi `burn_dps / 60` dan mengirim
damage tiap 30 tick melalui jalur damage/death boss. Pass item global mengecualikan
`active_boss` agar item clock tidak turun dua kali. Semua enam kenaikan HP AI
boss memakai setter parity sumber: anti-heal lebih dulu, lalu heal amplification;
penurunan HP tidak diubah. Oracle AST `boss_debuff_clock_source_oracle.py`
menjaga lima kasus clock/burn dan empat kasus setter HP, sedangkan
`boss_debuff_clock_checks.gd` memeriksa parity state/payload, tick order,
anti-double-tick, burn death/reward dan kedua jalur heal. Code commit `5e06a24`
lulus CI Godot 4.7.2 [run 37092769125](https://github.com/dharmawantoxi/mystic-arena/actions/runs/37092769125): **1.198.460 native checks**, `validate_project.py` **5.993 static checks**.
**Layer 8h** port target handoff auto-cast untuk boss hero merah: dari unit,
boss aktif, tower dan base hidup, pilih musuh terdekat dalam `skill_range`
inklusif (tie mempertahankan urutan sumber), tetapkan `target_id`/`target_struct`
sebelum auto-cast dan jangan berikan lane order saat target ada. Cakupan sengaja
khusus boss hero; starter tidak berubah. Oracle AST read-only
`boss_hero_ai_source_oracle.py` mengunci enam kasus; `boss_hero_ai_checks.gd`
menguji Gornak, target/lane handoff, serta guard starter. Commit `b728cb6`
lulus CI Godot 4.7.2 [run 37097737800](https://github.com/dharmawantoxi/mystic-arena/actions/runs/37097737800): **1.198.481 native checks**, `validate_project.py` **6.021 static checks**.
**Audit atribusi burn** (`1aa2352`) menutup selisih handoff: `_core.TowerDebuffMixin`
memanggil `take_damage` dengan `burn_team` atau tim entity sebagai fallback;
BossState kini meneruskan/merekam nilai itu, dan unit burn lethal memakai tim
sumber valid untuk kill ledger alih-alih selalu menebak lawan. Jika tim tidak
valid, fallback kill unit sebelumnya tetap dipakai. Fixture oracle yang sudah
menyimpan `damage_calls.from_team` kini dibandingkan pada native; checks juga
meliputi BLUE (`0`) vs fallback red, boss burn lethal dan burn same-team.
Sumber Boss menerima `from_team` tapi tidak menggunakannya lagi; pelacakan boss
menjaga batas pemanggilan, sedangkan ledger unit mengonsumsi tim secara eksplisit.
Audit commit lulus CI Godot 4.7.2
[run 37098998782](https://github.com/dharmawantoxi/mystic-arena/actions/runs/37098998782):
**1.198.492 native checks**, `validate_project.py` **6.024 static checks**.
**Layer 8i** (`4c34f0c`) memindahkan kiting ranged dari `Boss.update` untuk
ancient_apparition, morgath, razak, varkul, xerathis, nyzrak, syrentha,
thalgryn, nyxarath, malzareth, akashari dan vorenmarr. Ekspor stats native kini
membawa `min_distance`/`prefer_distance`; `BossState.move_ranged_kite()`
memilih `back`/`in`/`hold` dengan band histeresis 12 px, hanya untuk 12 tipe
tersebut. `boss_motion_source_oracle.py` mengunci tepat empat trace per boss
(48 kasus; masuk/keluar band untuk kedua mode), sementara `boss_motion_checks.gd`
mereplay trace dan menguji routing pada fixed tick aktif.
Code commit lulus CI Godot 4.7.2
[run 37118164879](https://github.com/dharmawantoxi/mystic-arena/actions/runs/37118164879):
**1.198.870 native checks**, `validate_project.py` **6.030 static checks**.
**Layer 8j** (`433a2e6`; perluasan oracle `a1d6d0f`) membatasi `BossAI.tick()`
ke target dalam `attack_range` inklusif, sesuai cabang `Boss.update`; saat di luar
range, native tetap bergerak namun memberi dispatcher target null agar heal
true-boss tetap berjalan tanpa smart-AI cast/timer tick. Oracle
`boss_motion_source_oracle.py` mencatat empat kasus range/aggro untuk seluruh
79 recipe (316 kasus); native memeriksa target window dan semua cabang dispatcher,
serta menguji batas 150/151 px pada Ancient Apparition.

**Layer 8k** (`b2fd3ad`) mempertahankan source ID Boss pada pukulan dasar utama:
`Boss.update` meneruskan `source=self`, sehingga native `_deliver_hit()` memakai
`boss.id` dan reaktif target/item dapat melihat penyerang. Cleave tetap
`source_id=-1`, sama dengan sumber yang tidak memberi `source`. Oracle AST
merekam 4 skenario × 216 tipe boss (**864 kasus**); native replay memeriksa
pemilihan target, hit/source ID, cooldown/sequence dan batas akuisisi, serta
integrasi refleksi Bristleback tanpa mengubah implementasi hero.
CI Godot 4.7.2 [run 37122525909](https://github.com/dharmawantoxi/mystic-arena/actions/runs/37122525909):
**1.206.378 native checks**, `validate_project.py` **6.120 static checks**.

**Layer 8l** (`7584830`, koreksi fixture `2d4255a`) memindahkan atribusi kill boss
`Game._process_boss_kill` ke jalur kematian native: `_process_boss_kill()` membaca
`boss.last_hit_source_id` (batas serangan dasar 8k + burn/cleave 8g), mengkredit
`killer.kills` hanya bila penyerang adalah hero sungguhan tim lawan, lalu menaikkan
`miniboss_kill_count`/`trueboss_kill_count` hanya untuk hero biru, sebelum reward di
`_process_boss_result()`. Oracle `boss_kill_credit_source_oracle.py` mengeksekusi
cabang kematian `Boss.take_damage` plus `_killer_is_hero`/`_process_boss_kill`/
`_unlock_achievement` asli: 4 skenario x 216 tipe (**864 kasus**); suite native
`boss_kill_credit_checks.gd` mereplay semuanya plus handoff match-step, jalur tanpa
source/non-hero, killer mati dan guard retirement. Banner achievement tetap di luar
scope (presentasi). CI Godot 4.7.2
[run 37125084934](https://github.com/dharmawantoxi/mystic-arena/actions/runs/37125084934):
**1.210.074 native checks**, `validate_project.py` **6.154 static checks**.

**Layer 8m** (`8b6b1a4`, koreksi checks `76580db`) membuat boss terlihat oleh
targeting tower/nexus: `Tower.update` menambahkan boss musuh hidup dalam
`self.range` dari scan `all_units` dan `Castle.update` membangun `enemies` dari
`all_units` (boss elemen terakhir), sedangkan native hanya memindai `units` dan
`structures`. `_structure_target()` kini memakai `super` lalu menambahkan boss
hidup tim lawan dengan batas inklusif dan aturan seri `<=` yang sama. Oracle
`boss_structure_targeting_source_oracle.py` mengeksekusi `Tower._find_target`
dan `Castle._find_target` asli atas daftar musuh kedua call site plus empat cek
struktur source: 8 skenario x 216 tipe boss (**1728 kasus**, termasuk kolom
`expected_without_boss`). `boss_structure_targets_checks.gd` mereplay semuanya
dan menguji tick hidup tower+nexus, guard tim sama dan boss mati. CI Godot 4.7.2
[run 37126929202](https://github.com/dharmawantoxi/mystic-arena/actions/runs/37126929202):
**1.218.942 native checks**, `validate_project.py` **6.186 static checks**.
Yang belum: sebagian besar sistem produksi. Jangan menyebut replay ini parity
seluruh pertandingan Python.
- Restart membuat world, scheduler, ledger dan seleksi baru. Tidak ada saldo/progres yang dibawa lintas pertandingan.
- Kematian nexus pertama menentukan pemenang, membekukan world/economy, membuang antrean spawn/projectile dan membuka hasil otomatis. Entity boss (layer 8a), kondisi match (8b), perilaku dasar (8c), ability/smart AI slice (8d + 8d-1), entrance/enrage clock (8e), presentasi intro/death (8f), TowerDebuffMixin clocks/heal setter (8g), target handoff AI boss hero sebelum lane assignment (8h), audit atribusi `burn_team` (`1aa2352`), ranged-boss kiting/hysteresis (8i), smart-AI attack-range gate (8j), source ID hit dasar (8k), dan atribusi kill boss `Game._process_boss_kill` (8l), dan visibilitas boss pada targeting tower/nexus (8m) sudah dikerjakan. Cakupan boss yang terport mencakup owner tunggal `active_boss`, jadwal/pending mini, trigger true boss, counter `red_towers_destroyed`, reward/unlock, target hero, basic attack/cleave dengan identitas penyerang pada hit utama, kredit kills hero pada kematian boss beserta counter mini/true boss, boss sebagai sasaran serangan tower/nexus (batas inklusif + seri), generic ability, smart recipe Gornak/Morgath/Drakar/Abaddon/Alchemist/Malzareth/Akashari/Vorenmarr/Nyxarath/Thalgryn/Syrentha/Gravewake/Kunkka/Razak/Kenshiro/Khazan/Wiro/Naraka/Krognarr/Raz/Vraskhan + 41 boss L9 tersisa + final 17 non-L9, true-boss heal, entrance/enrage, status/item-debuff clocks, burn, anti-heal/heal amplification, death flash/sparks dan screen shake.

## Bukti dan batas pengujian

Checkpoint Kaizen-1 `0078e79`: [CI Godot 4.7.2 Linux](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36218349274), **4.780 native checks** termasuk suite sebelumnya. Mencakup fixture sumber, kapasitas antrean, seluruh slot, ledger, duplicate/stale/dead transactions, reward, projectile sale cancellation, hasil freeze, replay identik 4.200 tick serta tiga lifecycle UI untuk kedua pemenang, pause/focus, input berskala, HUD bounds dan cleanup.

JSON memuat angka sebagai float. Trace membandingkan nilai scalar numerik secara exact, bukan nested `Array` yang membedakan tipe Variant. Tidak menggunakan toleransi untuk gold/tick/spawn.

**Belum diuji:** GPU/screenshot, Windows fisik, multi-touch/perangkat Android, pertandingan manual panjang dan balance/performa. Headless lifecycle/input adapter bukan pengganti pengujian tersebut. Upgrade Archer ([kontrak](UPGRADE_CONTRACT.md), 1.905 checks pada `7c96c83`), upgrade nexus ([kontrak](NEXUS_CONTRACT.md)), jalur Cannon ([kontrak](CANNON_CONTRACT.md), 3.713 checks pada `81765fd`), jalur Ice ([kontrak](ICE_CONTRACT.md), 4.035 checks pada `3e8ad59`), dan jalur Mage ([kontrak](MAGE_CONTRACT.md), 4.452 checks pada `f1b80b9`) sudah tersedia di mode ini. Scope berikutnya: hero/AI sebelum memperluas konten; jangan mengklaim prototipe ini sudah game lengkap.
