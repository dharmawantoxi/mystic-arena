# Kontrak hero prototipe — Kaizen-1 di pertandingan awal

Mode **Pertandingan awal** men-spawn **satu Kaizen biru** saat arena diinisialisasi. Ini bukan katalog pembelian, bukan roster 6 hero, dan bukan AI hero. Domain Q/level/death sudah dikunci di `tests/kaizen_checks.gd` + `fixtures/kaizen_source.json`.

## Yang masuk scope

- Spawn gratis di `HERO_SPAWN` `(220, 540)` dekat nexus biru. Lawan tidak mendapat hero.
- Hero dihitung sebagai unit (`MAX_UNITS`) tetapi **bukan** minion: tidak mengikuti lane, tidak memblokir `field_clear` wave, kill tidak memberi gold (`gold_reward = 0`), dan jenazah tetap addressable.
- Auto-act prototipe (cuplikan Hero.update state 4–5): jika ada musuh dalam `eff_attack_range` (`<=`) → basic attack, **tidak jalan**. Jika tidak, kejar musuh terdekat dengan jarak **`< 900`** (`hunt_range` sumber) lewat `_move_toward` + `_eff_speed`. Unit dulu, lalu bangunan. Stun/dash/mati = diam.
- Tombol **Skill Q** (dan tombol fisik Q) hanya ketika hero biru dipilih. Cast lewat `cast_hero_q` sumber: butuh target dalam jangkauan, satu command per tick, fizzle tanpa cooldown bila tidak ada target.
- Inspeksi menampilkan nama, HP/`max_hp` level, Q stack, dan skill CD.
- Pause, kehilangan fokus, dan hasil membatalkan command Q. Restart men-spawn Kaizen baru (timer/stack nol).

## Yang sengaja ditunda

W/E/R, dash visual penuh, respawn, item, unlock gold 400, hero merah, retreat/klik-destination/follow/push ke nexus, auto-cast, upgrade hero via UI, dan lima hero starter lainnya. Hunt prototipe **bukan** port AIPlayer.

Angka kit tetap milik resource `data/heroes/kaizen.tres` dan tabel `HERO_LEVELS` global.
