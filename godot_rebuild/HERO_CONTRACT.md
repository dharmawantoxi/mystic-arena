# Kontrak hero prototipe — Kaizen biru + merah di pertandingan awal

Mode **Pertandingan awal** men-spawn **satu Kaizen biru** dan **satu Kaizen merah** saat arena diinisialisasi. Domain angka Q/level/death tetap di `tests/kaizen_checks.gd` + `fixtures/kaizen_source.json`. Ini menutup kit + loop Hero.update state 1–6 untuk **pasangan** hero, bukan roster 6, bukan AIPlayer, bukan item.

## Scope yang dikunci

- Spawn gratis biru `HERO_SPAWN` `(220, 540)`. Spawn gratis merah `RED_HERO_SPAWN` `(1120, 130)` (sumber AI: `RED_BASE − 60, +30`).
- Bukan minion: tidak lane-march, tidak menahan `field_clear`, kill gold 0, jenazah addressable.
- **State 1 retreat:** HP `< 20%` → jalan ke nexus sendiri; dekat `< 100` px heal `+3` HP/tick; keluar retreat pada `≥ 80%`. Tetap boleh melee dalam range.
- **State 2 destination:** klik kanan tanah **hanya biru**. Hunt tidak menimpa. Snap-clear `dist <= speed`.
- **State 3 follow:** klik kanan musuh **hanya biru**. Destination dan follow saling menimpa. Target mati → clear.
- **State 4 melee:** `<= eff_attack_range`, tidak jalan.
- **State 5 hunt:** musuh terdekat jarak **`< 900`**.
- **State 6 push:** tidak ada hunt → biru ke `RED_BASE`, merah ke `BLUE_BASE`.
- Passive heal `+0.15` HP/tick bila tidak penuh.
- **Q** Steel Wind (butuh target, CD skill), **W** Wind Wall 180/CD 240 memantulkan proyektil fisik, **E** Sweep AOE 100 `skill×1` CD 420, **R** Tornado AOE 150 `skill×2` CD 900 / ulti 90. UI skill hanya untuk hero biru yang dipilih.
- **Auto-cast (biru + merah):** `auto_cast_enabled` default **true** untuk kedua hero (sumber v27: auto-cast selalu aktif, pemain tidak perlu menekan skill). Setiap 20 tick, hanya jika ada musuh hidup dalam `skill_range`. Prioritas R → E (2+ target) → W (HP `< 40%`) → Q. Stun membatalkan.
- **Tombol Auto-cast (status, hanya biru):** port tombol `toggle_autocast` sumber. Sumber v29 menghapus jalur OFF — tombol adalah penanda status; klik hanya memaksa `auto_cast_enabled = true` (tidak ada cara mematikan). Pesan aksi: "Auto-cast sudah aktif." / "Auto-cast diaktifkan.".
- **QWER manual biru tetap** sebagai tambahan rebuild (sumber v29 menghapus tombol skill): manual dan auto-cast berbagi cooldown yang sama — cast manual menghabiskan CD sehingga auto-cast tidak mengulang sampai CD selesai, dan sebaliknya.
- Upgrade hero UI: harga `HERO_LEVELS` (Lv.1→2 = **300 G**), expected-level, tanpa mengubah HP (quirk item-inventory sumber). Hanya biru.
- Respawn **600** tick di spawn timnya, HP penuh, perintah/debuff/CD clear.
- Stun/dash: tidak act. Pause/fokus/hasil membatalkan command antrean.
- Pemain **tidak** memerintah hero merah. Merah memakai loop yang sama tanpa dest/follow pemain.
- **Baris UI hero:** Q/W/E/R + tombol Auto-cast + upgrade hero berada di baris `HeroCommands` khusus (hanya saat hero biru dipilih) supaya seluruhnya muat dalam viewport 1280×720; baris build/sell/upgrade/nexus tidak lagi terpotong.

## Sengaja di luar

Item/forge, unlock 400 G, dash/jump/tornado VFX, lima hero starter lain, AIPlayer (beli hero/upgrade lawan). Jangan mengklaim pertandingan Python selesai.
