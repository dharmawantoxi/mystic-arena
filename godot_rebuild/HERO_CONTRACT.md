# Kontrak hero prototipe — Kaizen-1 selesai di pertandingan awal

Mode **Pertandingan awal** men-spawn **satu Kaizen biru** saat arena diinisialisasi. Domain angka Q/level/death tetap di `tests/kaizen_checks.gd` + `fixtures/kaizen_source.json`. Ini menutup kit + loop Hero.update state 1–6 untuk **satu** hero, bukan roster 6, bukan AIPlayer, bukan item.

## Scope yang dikunci

- Spawn gratis `HERO_SPAWN` `(220, 540)`. Lawan tidak mendapat hero.
- Bukan minion: tidak lane-march, tidak menahan `field_clear`, kill gold 0, jenazah addressable.
- **State 1 retreat:** HP `< 20%` → jalan ke nexus biru; dekat `< 100` px heal `+3` HP/tick; keluar retreat pada `≥ 80%`. Tetap boleh melee dalam range.
- **State 2 destination:** klik kanan tanah. Hunt tidak menimpa. Snap-clear `dist < speed`.
- **State 3 follow:** klik kanan musuh. Destination dan follow saling menimpa. Target mati → clear.
- **State 4 melee:** `<= eff_attack_range`, tidak jalan.
- **State 5 hunt:** musuh terdekat jarak **`< 900`**.
- **State 6 push:** tidak ada hunt → jalan ke `RED_BASE`.
- Passive heal `+0.15` HP/tick bila tidak penuh.
- **Q** Steel Wind (butuh target, CD skill), **W** Wind Wall 180/CD 240 memantulkan proyektil fisik, **E** Sweep AOE 100 `skill×1` CD 420, **R** Tornado AOE 150 `skill×2` CD 900 / ulti 90.
- Upgrade hero UI: harga `HERO_LEVELS` (Lv.1→2 = **300 G**), expected-level, tanpa mengubah HP (quirk item-inventory sumber).
- Respawn **600** tick di spawn, HP penuh, perintah/debuff/CD clear.
- Stun/dash: tidak act. Pause/fokus/hasil membatalkan command antrean.

## Sengaja di luar

Item/forge, unlock 400 G, hero merah, auto-cast, dash/jump/tornado VFX, lima hero starter lain, AIPlayer. Jangan mengklaim pertandingan Python selesai.
