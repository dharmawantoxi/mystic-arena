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
- Jitter spawn wave sudah diport (layer 7b): `uniform(-8, 8)` pada x/y lalu offset lane `-20/0/20`, dengan stream ter-seed supaya replay identik (aliran `random` Python tidak direproduksi). Castle scaling lawan juga sudah diport (layer 7a). Sumber tidak punya rutin separation terpisah — spread-nya hanya offset lane + jitter ini. Yang masih belum: sebagian besar sistem produksi. **Inti entity boss sudah diport (layer 8a)**: `scripts/match/boss_state.gd` + `data/bosses/boss_stats.json` (216 tipe dari `bosses/boss_data.py`), diuji `tests/boss_core_checks.gd`. **Kondisi match boss layer 8b juga sudah diport** di `scripts/match/prototype_battle.gd`: jadwal mini acak, pending FIFO, spawn mini/true, counter `red_towers_destroyed`, reward dan daftar unlock; oracle `match_source_oracle.py` + `tests/boss_match_checks.gd` menguncinya. **Layer 8c menambah** movement waypoint/chase, target terdekat, basic physical attack, cooldown/facing, cleave dan hero target/death registry; `boss_motion_source_oracle.py` + `boss_motion_checks.gd` menguncinya. **Layer 8d menambah** generic ability, smart AI slice awal Gornak/Morgath/Drakar/Abaddon, Q/W/E/R timers, active-skill/cooldown clocks dan true-boss heal; sub-layer 8d-1 menambah smart AI Alchemist, Malzareth, Akashari, Vorenmarr, Nyxarath dan Thalgryn; `boss_ability_source_oracle.py` + `boss_ability_checks.gd` mengunci parity source (fixture 42 kasus). **Layer 8e**
menambah `boss_clock_source_oracle.py` + `boss_clock_checks.gd`: entrance gate
mini/true, `anim_time`/`pulse`, threshold enrage, modifier sekali, cooldown pulse
dan interaksi slow. **Layer 8f** menambah presentasi intro/death boss saja:
`boss_presentation_source_oracle.py` + `boss_presentation_checks.gd` mengunci
entrance aura/text, death snapshot dan FX tick setelah registry cleanup.
Yang belum: sebagian besar sistem produksi. Jangan menyebut replay ini parity
seluruh pertandingan Python.
- Kematian nexus pertama menentukan pemenang, membekukan world/economy, membuang antrean spawn/projectile dan membuka hasil otomatis. Entity boss (layer 8a), kondisi match (layer 8b), perilaku dasar (layer 8c), ability/smart AI slice awal (layer 8d + sub-layer 8d-1), entrance/enrage clock (layer 8e) dan presentasi intro/death boss (layer 8f) sudah dipindahkan, termasuk owner tunggal `active_boss`, jadwal/pending mini, trigger true boss, counter `red_towers_destroyed`, reward, daftar unlock, target hero, basic attack, cleave, generic ability, smart recipe Gornak/Morgath/Drakar/Abaddon/Alchemist/Malzareth/Akashari/Vorenmarr/Nyxarath/Thalgryn, true-boss heal, entrance gate, death flash/sparks dan screen shake.
- Restart membuat world, scheduler, ledger dan seleksi baru. Tidak ada saldo/progres yang dibawa lintas pertandingan.

## Bukti dan batas pengujian

Checkpoint Kaizen-1 `0078e79`: [CI Godot 4.7.2 Linux](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36218349274), **4.780 native checks** termasuk suite sebelumnya. Mencakup fixture sumber, kapasitas antrean, seluruh slot, ledger, duplicate/stale/dead transactions, reward, projectile sale cancellation, hasil freeze, replay identik 4.200 tick serta tiga lifecycle UI untuk kedua pemenang, pause/focus, input berskala, HUD bounds dan cleanup.

JSON memuat angka sebagai float. Trace membandingkan nilai scalar numerik secara exact, bukan nested `Array` yang membedakan tipe Variant. Tidak menggunakan toleransi untuk gold/tick/spawn.

**Belum diuji:** GPU/screenshot, Windows fisik, multi-touch/perangkat Android, pertandingan manual panjang dan balance/performa. Headless lifecycle/input adapter bukan pengganti pengujian tersebut. Upgrade Archer ([kontrak](UPGRADE_CONTRACT.md), 1.905 checks pada `7c96c83`), upgrade nexus ([kontrak](NEXUS_CONTRACT.md)), jalur Cannon ([kontrak](CANNON_CONTRACT.md), 3.713 checks pada `81765fd`), jalur Ice ([kontrak](ICE_CONTRACT.md), 4.035 checks pada `3e8ad59`), dan jalur Mage ([kontrak](MAGE_CONTRACT.md), 4.452 checks pada `f1b80b9`) sudah tersedia di mode ini. Scope berikutnya: hero/AI sebelum memperluas konten; jangan mengklaim prototipe ini sudah game lengkap.
