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

**Layer 8n** (`f94583e`; perbaikan CI `bb69832` dan `4e88687`, final code run
[37134838416](https://github.com/dharmawantoxi/mystic-arena/actions/runs/37134838416))
port visibilitas boss pada targeting minion. Boss hidup tim lawan masuk kandidat
sesuai kueri source `range + 30` inklusif, setelah unit musuh dan sebelum tower/
nexus; boss mati, setim, atau di luar radius didelegasikan ke target dasar.
Boss tidak ikut grup `Minion` untuk AI lane/low-HP, tetapi tetap dapat dipilih
secara umum dan tetap memenuhi prioritas siege `max_hp >= 1500`. Oracle
`boss_minion_targeting_source_oracle.py` dan replay `boss_minion_targets_checks.gd`
mencakup empat skenario untuk tiap 216 tipe boss (**864 kasus**) serta tick
minion hidup yang mengejar dan memukul boss. CI Godot 4.7.2 hijau:
**1.223.709 native checks**, `validate_project.py` **6.220 static checks**.

**Layer 8o** (`1436fc9`; perbaikan registrasi suite `4c4f057`, CI final
[37136981760](https://github.com/dharmawantoxi/mystic-arena/actions/runs/37136981760))
menyelaraskan urutan combat: source `Game.update` dan `_update_gameplay` menjalankan
hero hidup sebelum `Boss.update`, sedangkan native sebelumnya men-tick boss dulu.
Kini aksi hero terjadi setelah unit/struktur dan sebelum true-boss check serta
fase boss; respawn tetap sesudah hasil boss. Oracle AST dan `boss_phase_order_checks.gd`
menguji empat kasus untuk tiap 216 boss (**864 kasus**): hit hero lethal/nonlethal,
masuk ke attack range dan keluar dari radius target source. CI Godot 4.7.2 hijau:
**1.227.818 native checks**, `validate_project.py` **6.249 static checks**.

**Layer 8p** (`b46ef88`; perbaikan scope suite `e2aa540`, CI final
[37141379984](https://github.com/dharmawantoxi/mystic-arena/actions/runs/37141379984))
membuat AOE freeze menara es level-6 mengenai boss. Source menjalankan lengan
`'slow_aoe' in self.special_data and all_units` di atas `all_units` yang berisi
boss hidup sebagai elemen terakhir, dengan radius inklusif `d <= aoe` dan slow
polimorfik (`Boss.apply_slow` / `Boss.apply_debuff('atk_slow')`, tenacity 0.50,
cap 0.35). Native hanya memindai `units`, sehingga boss tidak pernah kena AOE.
`siege_battle._ice_impact()` kini memakai `_ice_aoe()` yang ditimpa
`PrototypeBattle` untuk menambahkan boss hidup dengan guard sumber. Oracle
`boss_ice_aoe_source_oracle.py` dan replay `boss_ice_aoe_checks.gd` mencakup
empat skenario untuk tiap 216 tipe boss (**864 kasus**) plus tick hidup menara
es level-6 dan guard tim sama/boss mati/tanpa AOE di bawah level 6. CI Godot
4.7.2 hijau: **1.232.368 native checks**, `validate_project.py`
**6.292 static checks**.

**Layer 8q** (`79feb79`, CI
[37142715818](https://github.com/dharmawantoxi/mystic-arena/actions/runs/37142715818))
meluruskan damage proyektil menara/nexus pada boss. Source menembak dengan
`damage_type='projectile'` tanpa `school=`/`source=`, dan
`_entity.resolve_damage_school` mengembalikan `None`, jadi `Boss.take_damage`
tidak menerapkan mitigasi armor maupun magic-resist - hanya resilience dan cap
anti-burst. Native menyerahkan sekolah deklarasi penembak, sehingga damage
terpotong armor boss (Gornak 62 vs 42 pada es L6, Abaddon 108 vs 43 pada cannon
L6). `_update_projectiles()` kini memakai `_projectile_school()`; match layer
mengembalikan `"neutral"` untuk `BossState` sementara minion/hero tetap pada
sekolah deklarasi. Oracle `boss_tower_damage_source_oracle.py` dan replay
`boss_tower_damage_checks.gd` mencakup empat jenis peluru untuk tiap 216 tipe
boss (**864 kasus**), masing-masing dengan kolom hasil sebelum layer, plus tick
hidup archer L1. CI Godot 4.7.2 hijau: **1.236.052 native checks**,
`validate_project.py` **6.333 static checks**.

**Layer 8r** (`0397e9e`, CI
[37144074482](https://github.com/dharmawantoxi/mystic-arena/actions/runs/37144074482))
membuat splash/burn cannon mengenai boss. Source menjalankan loop splash di atas
`all_units` (boss hidup adalah elemen terakhirnya), inklusif pada
`d <= splash_radius`, dengan `int(damage * 0.6)` tanpa school/source lalu burn
`source_team=self.team`. Native hanya memindai `units`, sehingga boss tidak
pernah kena splash. `_cannon_impact()` kini memakai `_cannon_splash()` yang
ditimpa `Prototype` untuk menambahkan boss hidup; pukulannya memakai source id
`-1` (splash lethal menulis `_killed_by = None`) dan burn lewat
`BossState.apply_debuff`. Oracle `boss_cannon_splash_source_oracle.py` dan
replay `boss_cannon_splash_checks.gd` mencakup empat skenario untuk tiap 216
tipe boss (**864 kasus**), termasuk tepi 100 px dan splash lethal, plus tick
hidup cannon L6 dan guard tim sama/boss mati/tanpa radius. CI Godot 4.7.2 hijau:
**1.240.385 native checks**, `validate_project.py` **6.376 static checks**.

**Layer 8s** (`00b7986`; perbaikan guard suite `d2de987`, CI final
[37145481944](https://github.com/dharmawantoxi/mystic-arena/actions/runs/37145481944))
membuat slow target utama menara es pada boss lewat aturan boss. Source memanggil
`self.target.apply_slow(...)` / `self.target.apply_debuff('atk_slow', ...)`
secara polimorfik, sehingga tenacity 0.50 memotong magnitude dan durasi dengan
cap 0.35 (es L6 0.65/150 -> 0.325/75, atk 0.40 -> 0.20); native menyimpan nilai
mentah aturan mixin, jadi boss yang diincar menara es beku dua kali lebih berat
dan dua kali lebih lama. `_ice_impact()` kini memakai `_ice_main()` yang ditimpa
`Prototype` untuk target boss, sementara minion/hero tetap pada store dunia.
Oracle `boss_ice_main_slow_source_oracle.py` dan replay
`boss_ice_main_slow_checks.gd` mencakup empat skenario untuk tiap 216 tipe boss
(**864 kasus**), masing-masing dengan kolom `expected_mixin` dari
`TowerDebuffMixin.apply_slow` asli, plus tick hidup menara es L6 dan guard boss
mati/AOE. CI Godot 4.7.2 hijau: **1.243.204 native checks**,
`validate_project.py` **6.417 static checks**.

**Layer 8t** (`9ee759d`, CI
[37152741018](https://github.com/dharmawantoxi/mystic-arena/actions/runs/37152741018))
membuat boss aktif terlihat oleh pemilihan target sekunder volley archer (level
5/6) dan chain mage (level 2..6). Di sumber (`_entity.py:815-831`),
`Tower.update` menambahkan boss musuh hidup di dalam `self.range` (inklusif) ke
ekor `enemies` lalu meneruskannya ke `self._shoot(enemies)` ->
`_shoot_archer(enemies)` (`_entity.py:915-925`) dan `_shoot_mage(enemies)`
(`_entity.py:1031-1049`). Sebelum layer ini, `fire_projectile()` hanya memindai
`units`, sehingga saat unit biasa yang lebih dekat menjadi target utama, archer
L5/L6 me-refill panah ekstra ke unit utama dan mage L2..L6 tidak menembakkan
bolt chain ke boss. `fire_projectile()` kini memakai
`_append_volley_targets(source, target, targets, count)` yang ditimpa
`Prototype` untuk menambahkan `active_boss` hidup tim lawan di dalam
`attack_range_px` (inklusif) setelah kandidat unit biasa dan sebelum refill
archer. Oracle `boss_tower_volley_source_oracle.py` dan replay
`boss_tower_volley_checks.gd` mencakup empat skenario untuk tiap 216 tipe boss
(**864 kasus**), masing-masing dengan kolom `expected_without_boss`, plus tick
hidup archer L5/mage L2 dan guard boss mati/tim sama/target utama tunggal/slot
penuh. CI Godot 4.7.2 hijau: **1.249.483 native checks**,
`validate_project.py` **6.466 static checks**.

**Layer 8u** (`13ea126`, CI [run 37155935998](https://github.com/dharmawantoxi/mystic-arena/actions/runs/37155935998))
menyelaraskan atribusi `source` pada seluruh hit ability dan skill boss. Di
`bosses/base_boss.py`, hanya serangan dasar utama di `Boss.update`
(`bosses/base_boss.py:707-709`) yang mengirim `source=self`, sementara seluruh
177 pemanggilan `take_damage(damage, self.team)` pada `Boss._use_ability`
(`bosses/base_boss.py:1079`) serta seluruh 79 recipe `_smart_ai_*` dan tick
persisten (`bosses/base_boss.py:1168-8485`) tidak memberi `source=`
(`source=None`). Sebelumnya `BossAI._hit` (`boss_ai.gd:3699`) mengirim
`boss.id` ke `_deliver_hit()`, sehingga ability boss ikut terkena blind
penyerang, memicu pantulan 25% Bristleback (`_entity.py:4695-4706`) dan 35%
Razor Carapace (`hero_items.py:2461-2472`) ke boss, serta menulis `killed_by =
boss.id` (`_entity.py:4731-4732`). `BossAI._hit()` kini mengirim `-1`: blind
pada boss tidak menggagalkan ability, Bristleback dan armor Razor Carapace
tetap memitigasi damage serta me-reset `last_damage_timer = 300` Leviathan
Heart tanpa memantulkan damage ke boss, dan ability lethal membiarkan
`killed_by = -1`. Oracle `boss_ability_source_attribution_oracle.py` dan replay
`boss_ability_source_attribution_checks.gd` mencakup empat skenario untuk tiap
216 tipe boss (**864 kasus**), masing-masing dengan kolom kontras
`expected_with_boss_source`, plus kontras hidup `_step_active_boss()` (basic
attack `boss.id` vs ability `-1`) dan tick persisten Morgath/Kunkka. CI Godot
4.7.2 hijau: **1.252.306 native checks**, `validate_project.py` **6.504 static
checks**.

**Layer 8v** (`a67a04b`, CI [run 37161245400](https://github.com/dharmawantoxi/mystic-arena/actions/runs/37161245400))
memindahkan pengiriman stun item hero ke boss aktif. Di `hero_items.py`
(`_apply_stun_to`, baris 2681-2690), seluruh stun item (`fenrir_chain`,
`abyss_breaker` Overwhelm & Bash, `sundering_cudgel` Pierce Bash, dan
`hex_idol` Hex) memanggil `target.apply_stun(int(duration))`, sehingga boss
menjalankan `TowerDebuffMixin.apply_stun` (`_core.py:870-879`, 55% resist stun
`int(duration * 0.45)`, `max(stun_timer, duration)`) dan `Boss.update`
(`bosses/base_boss.py:595-600`) mendekremen `stun_timer` serta menahan gerak,
serangan dasar, dan ability selama `stun_timer > 0`. Sebelumnya
`BattleItemEffects` (`battle_item_effects.gd`) lupa meng-override `apply_stun`,
sehingga terwarisi `ItemEffects.apply_stun` (`item_effects.gd:65-75`) yang
hanya menerima `UnitState` dan mengabaikan `BossState`.
`BattleItemEffects.apply_stun()` kini mendelegasikan ke `t.apply_stun(duration)`
saat `t != null and t.has_method("apply_stun")`. Oracle
`boss_item_stun_source_oracle.py` dan replay `boss_item_stun_checks.gd` mencakup
empat skenario untuk tiap 216 tipe boss (**864 kasus**), masing-masing dengan
kolom kontras `expected_without_boss_stun`, plus `fenrir_chain`, aturan stacking
durasi maksimum, dan kontras hidup `_tick_auras_and_items()` +
`_step_active_boss()`. CI Godot 4.7.2 hijau: **1.254.911 native checks**,
`validate_project.py` **6.546 static checks**.

**Layer 8w** (`724b656`; perbaikan oracle 8v `f80b5f2`, CI [run 37198385902](https://github.com/dharmawantoxi/mystic-arena/actions/runs/37198385902))
memindahkan pengiriman silence item hero ke boss aktif. Di `hero_items.py`
(`_apply_silence_to`, baris 2693-2697), Soul Rend (`sanguine_thorn`), Arcane Nova
(`astral_codex`) dan Hexcraft (`hex_idol`) memanggil
`target.apply_debuff('atk_slow', 1.0, duration)` lalu
`target.apply_debuff('skill_down', 1.0, duration)`, sehingga boss menjalankan
`Boss.apply_debuff` (`bosses/base_boss.py:540-552`): `atk_slow` dipotong tenacity 0.50
(`min(0.35, 1.0 * 0.5)`, `int(duration * 0.5)`) dan disimpan dengan aturan
terkuat-menang `TowerDebuffMixin` (`_core.py:918-947`), `skill_down` tetap 1.0 penuh.
Sebelumnya `BattleItemEffects.apply_silence` (`battle_item_effects.gd:35-44`) menulis
field langsung untuk target non-Hero, jadi boss memakai slow serang 1.0 penuh selama
durasi item (`effective_attack_cooldown` faktor 0.05 alih-alih 0.65).
`BattleItemEffects.apply_silence()` kini mendelegasikan ke `t.apply_debuff(...)` saat
target mengimplementasikannya. Oracle `boss_item_silence_source_oracle.py` dan replay
`boss_item_silence_checks.gd` mencakup empat skenario untuk tiap 216 tipe boss
(**864 kasus**), masing-masing dengan kolom kontras `expected_without_boss_tenacity`,
plus kontras hidup `_tick_auras_and_items()` + `_step_active_boss()`, aturan store,
dan payload mentah untuk minion. CI Godot 4.7.2 hijau: **1.257.516 native checks**,
`validate_project.py` **6.586 static checks**.

**Layer 8x** (`d51d696`; perbaikan parse suite `2b8ca4a`, CI [run 37199736341](https://github.com/dharmawantoxi/mystic-arena/actions/runs/37199736341))
memindahkan slow/root item hero ke boss aktif. Di `hero_items.py`, Vine Rod Entangle
memanggil `target.apply_slow(1.0, vr['root_duration'])` (baris 2652-2663), Everfrost
Arctic Blast `e.apply_slow(act['slow'], act['slow_duration'])` untuk setiap musuh dalam
radius 280 px (baris 2283-2293), dan Frostbound Frostbite
`target.apply_slow(oa['slow'], oa['duration'])` plus `apply_debuff('atk_slow', ...)`
(baris 2589-2600), semuanya di balik `hasattr(target, 'apply_slow')`. Boss menjalankan
`Boss.apply_slow` (`bosses/base_boss.py:528-538`): tenacity 0.50 memotong magnitude
(`min(0.35, ...)`) dan durasi (`int(duration * 0.50)`) dengan store
amount-besar-atau-durasi-panjang, sedang `Boss.apply_debuff` memotong hanya `atk_slow`.
Sebelumnya `BattleItemEffects.apply_slow` menulis field mentah (max-wins) dan
`apply_atk_slow` menuju store dunia, jadi root Vine Rod membekukan boss total 1.0/60 tick
(`eff_speed()` = 0) alih-alih 0.35/30 tick (0.65x), Arctic Blast 0.45/210 alih-alih
0.225/105, dan Frostbite 0.28/180 alih-alih 0.14/90. Kini keduanya mendelegasikan ke
`BossState` saat target mengimplementasikannya, dan minion/hero tetap memakai store dunia.
Oracle `boss_item_slow_source_oracle.py` dan replay `boss_item_slow_checks.gd` mencakup
empat skenario untuk tiap 216 tipe boss (**864 kasus**), masing-masing dengan kolom
kontras `expected_without_boss_tenacity`, plus kontras hidup Vine Rod/Frostbite dan tick
`_step_active_boss()` serta Everfrost lewat `_tick_auras_and_items()`. CI Godot 4.7.2
hijau: **1.260.125 native checks**, `validate_project.py` **6.631 static checks**.

**Layer 8y** (`51e94c1`, CI [run 37201527679](https://github.com/dharmawantoxi/mystic-arena/actions/runs/37201527679)) memindahkan lengan aura item
hero ke boss aktif dan meluruskan store burn item. `update_auras(all_heroes)` mengumpulkan
seluruh unit hidup lewat `all_units = _collect_all_units(all_heroes)` (`hero_items.py:2772`,
helper `2913-2930` yang menambahkan `active_boss` hidup), lalu menjalankan tiga aura Tier III:
Freezing Aura `u.apply_debuff('atk_slow', f_as, 30)` + anti_heal 0.40/30 (radius 300),
Scorched Earth burn 28/30 + `apply_miss_chance(0.18, 30)` (radius 280), dan Cauterize
anti_heal 0.50/30 + burn 6/30 (radius 300). Boss menjalankan `Boss.apply_debuff`
(`bosses/base_boss.py:540-552`): tenacity 0.50 memotong hanya `atk_slow` (0.30/30 menjadi
0.15/15), dan cabang burn-nya mereset `burn_accum`/`burn_tick_cd` pada burn baru
(`_core.py:939-948`). Sebelumnya Freezing Aura memakai store dunia (boss 0.30/30 mentah) dan
`BattleItemEffects.apply_burn` menulis field burn boss mentah sehingga `burn_tick_cd` basi
terpakai (tick pertama 7 frame lebih awal, 8 damage di frame 23). Kini lengan aura lewat
`_aura_item_effects()` dan burn item lewat delegasi `BossState.apply_debuff`, sementara
minion/hero tetap pada store dunia. Oracle `boss_item_aura_source_oracle.py` dan replay
`boss_item_aura_checks.gd` mencakup empat skenario untuk tiap 216 tipe boss (**864 kasus**),
masing-masing dengan kolom kontras `expected_without_boss_store`, plus kontras hidup
Everfrost (boss 0.15/15 vs minion 0.30/30), tick burn Scorched Earth dan gate heal
Cauterize. Anti-heal/burn aura dan blind Scorched Earth terbukti identik di kedua kolom
(non-gap, tidak diport). Perbaikan suite `29d7bff` (CI final [run 37203602541](https://github.com/dharmawantoxi/mystic-arena/actions/runs/37203602541)) membuang graph pertempuran tiap dunia uji lewat `_reset_world` dan memindahkan rekaman panggilan bus ke dictionary milik dunia sehingga tidak ada siklus RefCounted `world <-> bus` yang bocor di akhir proses Godot. CI Godot 4.7.2 hijau: **1.262.735 native checks**,
`validate_project.py` **6.671 static checks**.

Yang belum: sebagian besar sistem produksi. Jangan menyebut replay ini parity
seluruh pertandingan Python.
- Restart membuat world, scheduler, ledger dan seleksi baru. Tidak ada saldo/progres yang dibawa lintas pertandingan.
- Kematian nexus pertama menentukan pemenang, membekukan world/economy, membuang antrean spawn/projectile dan membuka hasil otomatis. Entity boss (layer 8a), kondisi match (8b), perilaku dasar (8c), ability/smart AI slice (8d + 8d-1), entrance/enrage clock (8e), presentasi intro/death (8f), TowerDebuffMixin clocks/heal setter (8g), target handoff AI boss hero sebelum lane assignment (8h), audit atribusi `burn_team` (`1aa2352`), ranged-boss kiting/hysteresis (8i), smart-AI attack-range gate (8j), source ID hit dasar (8k), atribusi kill boss `Game._process_boss_kill` (8l), visibilitas boss pada targeting tower/nexus (8m) dan targeting minion (8n), urutan aksi hero sebelum tick boss (8o), AOE freeze es level-6 yang mengenai boss dengan tenacity source (8p), damage proyektil menara/nexus pada boss yang bebas mitigasi sekolah sesuai `resolve_damage_school` (8q), splash/burn cannon yang mengenai boss dengan atribusi tanpa source (8r), slow target utama es pada boss yang memakai tenacity source (8s), visibilitas boss pada target sekunder volley archer L5/L6 dan chain mage L2..L6 (8t), atribusi tanpa source (`source_id=-1`) pada seluruh hit ability dan skill boss (8u), pengiriman stun item hero ke boss aktif lewat `BattleItemEffects.apply_stun` dengan 55% resist stun boss (8v), pengiriman silence item hero (Soul Rend/Arcane Nova/Hexcraft) lewat `BattleItemEffects.apply_silence` dengan tenacity 0.50 pada `atk_slow` dan payload `skill_down` utuh (8w), serta pengiriman slow/root item (Vine Rod Entangle, Everfrost Arctic Blast, Frostbound Frostbite) lewat delegasi `apply_slow`/`apply_atk_slow` ke `BossState` dengan tenacity 0.50 dan cap 0.35 (8x), lengan aura item (Freezing Aura/Scorched Earth/Cauterize) ke `BossState` dengan tenacity pada `atk_slow` serta reset clock burn item `apply_burn` (8y), serta target sekunder cleave/chain item hero pada boss aktif lewat `_onhit_boss()` di `BattleItemEffects.cleave_splash`/`chain_targets` (8z), juga sudah dikerjakan. Cakupan boss yang terport mencakup owner tunggal `active_boss`, jadwal/pending mini, trigger true boss, counter `red_towers_destroyed`, reward/unlock, target hero, basic attack/cleave dengan identitas penyerang pada hit utama, kredit kills hero pada kematian boss beserta counter mini/true boss, boss sebagai sasaran serangan tower/nexus (batas inklusif + seri), generic ability, smart recipe Gornak/Morgath/Drakar/Abaddon/Alchemist/Malzareth/Akashari/Vorenmarr/Nyxarath/Thalgryn/Syrentha/Gravewake/Kunkka/Razak/Kenshiro/Khazan/Wiro/Naraka/Krognarr/Raz/Vraskhan + 41 boss L9 tersisa + final 17 non-L9, true-boss heal, entrance/enrage, status/item-debuff clocks, burn, anti-heal/heal amplification, death flash/sparks dan screen shake.

## Bukti dan batas pengujian

Checkpoint Kaizen-1 `0078e79`: [CI Godot 4.7.2 Linux](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36218349274), **4.780 native checks** termasuk suite sebelumnya. Mencakup fixture sumber, kapasitas antrean, seluruh slot, ledger, duplicate/stale/dead transactions, reward, projectile sale cancellation, hasil freeze, replay identik 4.200 tick serta tiga lifecycle UI untuk kedua pemenang, pause/focus, input berskala, HUD bounds dan cleanup.

JSON memuat angka sebagai float. Trace membandingkan nilai scalar numerik secara exact, bukan nested `Array` yang membedakan tipe Variant. Tidak menggunakan toleransi untuk gold/tick/spawn.

**Belum diuji:** GPU/screenshot, Windows fisik, multi-touch/perangkat Android, pertandingan manual panjang dan balance/performa. Headless lifecycle/input adapter bukan pengganti pengujian tersebut. Upgrade Archer ([kontrak](UPGRADE_CONTRACT.md), 1.905 checks pada `7c96c83`), upgrade nexus ([kontrak](NEXUS_CONTRACT.md)), jalur Cannon ([kontrak](CANNON_CONTRACT.md), 3.713 checks pada `81765fd`), jalur Ice ([kontrak](ICE_CONTRACT.md), 4.035 checks pada `3e8ad59`), dan jalur Mage ([kontrak](MAGE_CONTRACT.md), 4.452 checks pada `f1b80b9`) sudah tersedia di mode ini. Scope berikutnya: hanya satu slice gameplay boss yang terbukti dari source; bila tidak ada gap jelas, berhenti dan jangan beralih ke hero/AI. Jangan mengklaim prototipe ini sudah game lengkap.


Lapisan **9a** (`7baf2be`, CI [37210567064](https://github.com/dharmawantoxi/mystic-arena/actions/runs/37210567064)) menyelaraskan urutan jarak Polycephaly Basilisk Breath saat boss aktif menjadi kandidat sekunder. Kandidat awal boss hilang dari daftar terbukti bukan gap: `_hero_enemy_list()` sudah menambahkan boss hidup (`prototype_battle.gd:1893-1906`) dan diteruskan ke on-hit ranged/melee. Gap berikutnya yang disetujui adalah pembanding jarak: source `extras.sort(key=lambda x: x[0])` (`hero_items.py:2629`) memakai jarak persis, sedangkan `_nearby_enemies_sorted_from()` native sebelum slice (`hero_item_inventory.gd:997`) menganggap selisih sampai 0.001 sebagai seri. Dengan minion pada 10 dan 20.0005 px serta boss terakhir pada 20 px, source menembak minion pertama lalu boss sebesar `int(50 * 0.70) = 35` magic, tetapi native lama menghabiskan dua slot pada minion. Lengan Polycephaly kini meminta pembanding jarak persis; hanya jarak benar-benar sama yang mempertahankan urutan insertion. Konsumen helper item lain tetap memakai perilaku lama agar tidak memperluas slice.

Oracle AST read-only `boss_polycephaly_source_oracle.py` mengeksekusi `_on_hit_common` dan `_apply_miasma` asli bersama inventory dan tipe Boss sumber, mencatat **864 kasus = empat skenario per 216 tipe boss**: boss lebih dekat merebut slot terakhir, jarak identik mempertahankan minion, boss menjadi tembakan pertama walaupun insertion terakhir, serta boss sedikit lebih jauh tidak mendapat slot. Setiap baris membawa `expected` dan `expected_without_exact_sort`; counterfactual hanya mengganti pembanding sort dengan epsilon pra-9a. `boss_polycephaly_checks.gd` mereplay inventory ranged -> bus -> `_deliver_hit`, membandingkan urutan dari rekaman delivery dan payload 35 magic secara numerik, serta mengecek urutan helper pra-fix. Suite memakai helper dunia dari suite 8z tanpa mengubahnya dan membuang graph dunia lewat `_reset_world`. Fixture lama tidak berubah. CI Godot hijau: **1.270.528 native checks**; `validate_project.py` **7.589 static checks**; `gdformat`/`gdlint`/`gdparse` dan `git diff --check` bersih. Batas slice: hanya sorting Polycephaly, bukan perubahan hero, balance, FX, UI, konfigurasi atau perluasan Miasma; tidak mengklaim parity seluruh pertandingan. PR draft [#314](https://github.com/dharmawantoxi/mystic-arena/pull/314), tidak di-merge. Berhenti setelah 9a; tidak memulai 9a-1/9b.

Lapisan **9b** (`d53769f`, PR draft [#315](https://github.com/dharmawantoxi/mystic-arena/pull/315), CI [37214031539](https://github.com/dharmawantoxi/mystic-arena/actions/runs/37214031539)) menutup gap reapply Basilisk Breath Miasma lintas dua hero pada boss aktif. Di checkpoint `4935af8`, source `hero_items.py:189-206` memakai tracker global per `id(target)`, memindahkan source ke pemilik reapply terakhir, lalu menggabungkan `max(damage)`, `max(timer)`, `min(tick_cd)`; tick mengatribusikan damage ke source itu (`hero_items.py:209-233`). Native lama mempunyai satu tracker per inventory (`hero_item_inventory.gd:123,768-813`), sedangkan prototype memanggil `tick_miasma` sekali untuk tiap hero hidup (`prototype_battle.gd:1956,1986-1993`), jadi dua poison terpisah tidak menyamai satu tracker gabungan. Bukti gameplay konkret pada oracle: A apply, 14 frame berlalu, lalu B reapply; Python mempertahankan countdown 2 dan menghasilkan satu tick 60 magic dari B pada world-frame berikutnya. Native lama mempertahankan cooldown A=16 dan B=30, menjadi 15/29 pada frame tersebut dan belum memberi tick. Dua jadwal lain memverifikasi source B sesudah tick awal maupun saat pemilik B mati.

`PrototypeBattle._bind_miasma_registry` kini mengikat inventory ke dictionary bersama per match sambil menggabungkan tracker lokal yang sudah ada; `apply_miasma` mentransfer source id/team/pos dan tick menggunakan `BattleItemEffects.deal_damage_from`. Oracle AST read-only `boss_miasma_source_oracle.py` membandingkan source Python asli dengan `native_old` untuk **864 kasus (4 jadwal x 216 boss)**; `boss_miasma_checks.gd` menjalankan `hero_basic_attack` dan tick update prototype nyata, bukan helper saja. CI Godot 4.7.2 hijau: **1.280.033 native checks**; `validate_project.py` **10.198 static checks**; gdtoolkit 4.5.0 (`gdformat`/`gdlint`/`gdparse`) dan `git diff --check` bersih. Batas: slice Miasma ini saja; tidak mengubah Python source, hero, balance, FX/presentation, UI, settings atau CI, dan tidak mengklaim parity seluruh permainan. PR [#315](https://github.com/dharmawantoxi/mystic-arena/pull/315) draft, tidak di-merge; berhenti setelah 9b tanpa memulai 9b-1/9c.


Lapisan **9c** (`7941095`, PR draft [#316](https://github.com/dharmawantoxi/mystic-arena/pull/316), CI [37259207365](https://github.com/dharmawantoxi/mystic-arena/actions/runs/37259207365)) memastikan satu tick racun Basilisk Breath tidak bisa ditelan oleh status buta pemiliknya. Di source, `_tick_miasma` (`hero_items.py:209-233`) mengirim `tgt.take_damage(m["damage"], team, "magic")`, jadi `Boss.take_damage` (`bosses/base_boss.py:5978-5993`) melihat `damage_type="magic"` dengan `source=None` dan blok buta (Solar Brand) — yang hanya berlaku untuk pukulan `'normal'` dari penyerang yang ada — tidak pernah menyala. Native sebelum slice mengirim tick lewat `BattleItemEffects.deal_damage_from` -> `world._deliver_hit(...)` (`battle_item_effects.gd:20-37`) tanpa `damage_type`, sehingga `prototype_battle.gd:1366` memakai default `"normal"` bersama pemilik racun yang hidup sebagai source; `BossState.blind_live` (`boss_state.gd:662,689`) lalu menggulung peluang buta pemilik dan tick hilang seluruhnya (terukur: 60 magic vs 0 pada tick yang sama).

`deal_damage_from` kini membawa `damage_type` (default `"magic"`) sampai ke `_deliver_hit`. Oracle AST read-only `boss_miasma_blind_source_oracle.py` mengeksekusi helper Python asli plus blok buta asli `Boss.take_damage`, menghasilkan **864 kasus (4 jadwal x 216 tipe boss)** dengan kolom `expected` dan `native_old`; `boss_miasma_blind_checks.gd` mereplay jalur `hero_basic_attack` -> update item prototype -> bus -> `_deliver_hit` -> `BossState.take_damage` untuk kedua kolom, dengan bus legacy yang memakai tubuh `deal_damage_from` pra-9c. Dua skenario kontrol (`blind_owner_true_strike_pierces`, `blind_owner_zero_amount`) terbukti identik di kedua kolom, jadi bukan gap. CI Godot 4.7.2 hijau: **1.288.243 native checks**; `validate_project.py` **11.087 static checks**; `gdformat`/`gdlint`/`gdparse` dan `git diff --check` bersih. Batas: hanya jalur Miasma tick -> damage boss -> gate buta; lengan damage item lain belum diselaraskan dan tidak ada perubahan atribusi source/kill-credit generik. Tidak mengklaim parity penuh. PR draft, tidak di-merge; berhenti setelah 9c.
