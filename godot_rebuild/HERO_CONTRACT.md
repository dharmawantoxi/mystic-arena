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

Item/forge, unlock 400 G, dash/jump/tornado VFX, starter lain di scene otomatis, AIPlayer lengkap (beli hero/upgrade lawan). Jangan mengklaim pertandingan Python selesai.

## Adapter upgrade red (WIP AIPlayer)

Domain menyediakan upgrade red per kandidat dengan reserve gold; hero red mati
atau respawning tetap eligible sesuai sumber AIPlayer, tanpa mengubah HP/alive
atau respawn timer. UI blue masih menolak hero mati. Belum ada scheduler AI yang
memanggilnya otomatis; lihat [AI_CONTRACT.md](AI_CONTRACT.md).

## Rekrut AI — fase awal, bukan roster playable lengkap

Domain red kini memiliki transaksi Kaizen/Thorne/Grimjaw/Sylara/Vex/Zephyr berbayar eksplisit melalui
draft (lihat [AI_CONTRACT.md](AI_CONTRACT.md)). Kaizen merah gratis di scene
tetap, tidak dihitung sebagai pembelian dan tidak diganti. Baseline numerik
222 Hero sumber tersedia; 216 lainnya belum punya handler native, sehingga
pembeliannya ditolak tanpa debit atau mengganti skill.

Thorne (500 G) adalah hero melee nyata dengan Q Viscous Nose (cone/slow),
W Bristleback (mitigasi fisik/magic dan reflect), E Quill Spray AOE, R Warpath
(buff attack/cooldown sementara). Fixture `thorne_source.json` diambil dari
Hero + ThorneSkills Python, termasuk upgrade saat buff dan respawn.
Resource `.tres` statis tidak dimutasi oleh buff. Kaizen lama tetap memakai
kit sendiri. Belum ada animasi/UI Thorne atau AI controller di scene.

Grimjaw (450 G) memakai Q spin 180 tick, W Healing Ward, E critical buff
berulang 300 tick + radial AOE, R target-lock 90 tick. Oracle sumber
`grimjaw_source.json` dibandingkan dengan combat native dan pembayaran red
nyata. Seluruh ID hero kini memiliki marker polygon/warna prosedural sederhana
berdasarkan ID dengan lingkar tim, mata arah hadap, HP dan seleksi. Ini
**placeholder** bebas aset; bukan animasi/visual hero final atau bukti 216
kit lainnya dapat dimainkan.

Sylara (380 G) adalah marksman ranged native pertama: serangan dasar homing
9,5px/tick, Q line-pierce dan Focus Fire, W Windrun + evasion fisik 75%,
E Shackle, R Powershot setelah charge. Oracle `sylara_source.json` menjalankan
skill dan loop projectile sumber Python nyata. Peluru sementara hanya titik
prosedural; bukan panah/efek final. Masih 216 kit yang belum playable.

## Batch starter lanjutan setelah #283

Vex dan Zephyr selesai: masing-masing 420 G, magic homing basic attack,
handler Q/W/E/R tersendiri dan lifecycle sumber. Vex: orb/line, eclipse
burst + ring DOT, prison/stun, flux AOE. Zephyr: bramble fixed-origin,
Shadow Realm heal/immunity, curse DOT dan Bedlam. `starter_finish_source_oracle.py`
mengeksekusi kode sumber asli untuk batas, cooldown, moving/dead target,
upgrade saat efek, respawn serta projectile. Helper bersama hanya BaseSkill
atau blok sumber yang identik. CI 4.7.2 commit `63778c4`: 50.666 checks;
**6 playable, 216 boss pending**, semuanya ditolak tanpa debit/substitusi.
Daftar/progres batch: [HERO_MIGRATION_PROGRESS.md](HERO_MIGRATION_PROGRESS.md).
