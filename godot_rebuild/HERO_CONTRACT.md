# Kontrak hero prototipe — Kaizen-1 di pertandingan awal

Mode **Pertandingan awal** men-spawn **satu Kaizen biru** saat arena diinisialisasi. Ini bukan katalog pembelian, bukan roster 6 hero, dan bukan AI hero. Domain Q/level/death sudah dikunci di `tests/kaizen_checks.gd` + `fixtures/kaizen_source.json`.

## Yang masuk scope

- Spawn gratis di `HERO_SPAWN` `(220, 540)` dekat nexus biru. Lawan tidak mendapat hero.
- Hero dihitung sebagai unit (`MAX_UNITS`) tetapi **bukan** minion: tidak mengikuti lane, tidak memblokir `field_clear` wave, kill tidak memberi gold (`gold_reward = 0`), dan jenazah tetap addressable.
- Auto-act prototipe: **klik kanan tanah** = destination (state 2); **klik kanan musuh** = follow (state 3). Destination menimpa follow dan sebaliknya. Follow: kejar target, melee jika `<=` range; target mati/ally → clear. Tanpa perintah: melee atau hunt `< 900`. Stun/dash/mati = diam.
- Tombol **Skill Q** (dan tombol fisik Q) hanya ketika hero biru dipilih. Cast lewat `cast_hero_q` sumber: butuh target dalam jangkauan, satu command per tick, fizzle tanpa cooldown bila tidak ada target.
- **Skill W** / tombol W: Wind Wall 180 tick, CD 240, tanpa target. Memantulkan proyektil fisik (bukan magic/mage, bukan melee).
- **Skill E** / tombol E: Sweep AOE 100px, `skill_damage * 1.0`, butuh target seperti Q, CD 420. Bukan jump visual.
- Inspeksi menampilkan nama, HP/`max_hp` level, Q stack, dan skill CD.
- Pause, kehilangan fokus, dan hasil membatalkan command Q. Restart men-spawn Kaizen baru (timer/stack nol).

## Yang sengaja ditunda

R, dash visual penuh, respawn, item, unlock gold 400, hero merah, retreat/push ke nexus, auto-cast, upgrade hero via UI, dan lima hero starter lainnya. Hunt/klik-gerak prototipe **bukan** port AIPlayer.

Angka kit tetap milik resource `data/heroes/kaizen.tres` dan tabel `HERO_LEVELS` global.
