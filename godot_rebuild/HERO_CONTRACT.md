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

## Roster kit native — 164 playable, 58 pending (bukan AIPlayer penuh)

Registry eksplisit `scripts/data/hero_roster.gd` berisi enam starter, Gornak,
Morgath, Drakar, Abaddon, Alchemist, Ancient Apparition, Nyzrak, Ignis
Drachorn, serta 150 ID yang benar-benar memakai jalur shared-source di Python
asli. Daftar tepat, source recipe dan bukti per
hero: [HERO_ROSTER_STATUS.md](HERO_ROSTER_STATUS.md). Sisa **58 boss** tidak
punya kit native dan ditolak tanpa debit/substitusi. Audit AST sumber
menampilkan keempat recipe asli keenam puluh satu boss pending **saling
berbeda**, jadi tidak ada satu pun yang boleh memakai handler bersama. Scene tetap pasangan
Kaizen gratis dan defender lama, tidak otomatis memakai seluruh registry.

Sumber `BossHeroSkills._fallback_cast` hanya dipakai untuk allowlist 150 ID
yang tidak mempunyai recipe sumber; bukan pengganti recipe khusus yang belum
diport. Setiap ID dites QWER, attack melee/homing, cooldown/recast, upgrade
1–15, respawn, summon threshold serta combat terhadap Hero/Tower asli.
Morgath mempertahankan basic beam/hit instan sesuai pengecualian sumber.

Vex dan Zephyr masing-masing 420 G, Alchemist 750 G, Ancient Apparition 800 G,
Nyzrak 850 G, Ignis Drachorn 850 G. Upgrade boss memakai
pengali sumber **1,6×**, jadi Lv1→2 480 G, bukan 300 G. Skill tanpa source/
school tetap netral; school eksplisit pada basic/shared-source tetap dibawa.
Anti-heal mengikuti HP setter sumber (cap sebelum memotong gain). Shadow Realm
memblokir burn termasuk tick aktif terakhir; tower tidak diberi stun yang
memerlukan atribut `attack_timer` yang tidak ada di sumber.

**Ancient Apparition:** Q menaruh vortex di posisi target (atau `h.x+100`),
clock 180 dan burst 0,6× r80; DOT `update_timers` asli 0,3× + slow 0,5/60
setiap 20 tick sampai clock habis lalu berhenti, dan di-rearm saat Q di-cast
ulang. W beam 400/30 1,5× slow 0,6/180; E single 2,5× plus `attack_timer` max
90; R beam 500/60 3,0× slow 0,7/240. `w_dir`/`r_dir` hanya berubah bila beam
memang dieksekusi.

**Nyzrak:** Q beam 240/26 1,2× slow 0,4/120 dengan aim nol yang tidak mengenai
apa pun (`math.hypot(...) or 1.0`); W burst r80 di target 1,0× slow 0,3/60;
E single 1,1× + `attack_timer` max 90 + slow 0,7/180; R nova r200 2,0× slow
0,5/180 dan heal `int(max_hp * 0.15)` lewat HP setter. `shield_active` dan
`shield_timer` **tidak punya konsumen di kelas `Hero` asli** (`_entity.py`):
tidak ada pool shield, absorb, atau mitigasi. Native hanya merekam kedua flag
dan menguji 100 damage penuh masuk untuk physical maupun magic — tidak ada
shield karangan. Durasi visual: Nyzrak override sumber 50/50/70/90, AA default
60/90/60/100, keduanya ditimpa trigger generic sumber.

**Ignis Drachorn:** Q cone 250/60 yang melebar dari 0,3 ke 1,0 sepanjang
reach, 1,6× stun 45; W sapuan r130 1,9× stun 60; E `dragon_blood` 480 tick
damage `int(katalog * 1,3)` + heal 20%; R `dragon_form` 600 tick damage
`int(katalog * 1,8)` + nova r220 3,0× stun 90 + heal 25%. Dua clock dengan
reset berbeda; quirk sumber dikunci, termasuk E menimpa damage R, kedaluwarsa R
mereset ke katalog sehingga buff E ikut hilang, dan kedaluwarsa E tidak
mengembalikan damage.

**Bentuk geometri bersama** (`boss_recipe_shapes.gd`) hanya transkripsi loop
sumber; damage, slow dan stun dalam satu pass atas daftar enemy yang sudah
difilter, sehingga unit yang mati oleh damage tetap kena slow/stun seperti di
sumber. Angka, urutan, dan efek tetap eksplisit per ID.

Fixture source dan suite native lama tetap dijalankan. CI Godot 4.7.2
`c029d50`: **358.305 native checks** (checkpoint #284). Progres batch, batas konteks sesi dan
pesan lanjutan: [HERO_MIGRATION_PROGRESS.md](HERO_MIGRATION_PROGRESS.md).
Placeholder polygon/warna hero dan titik proyektil tetap sederhana; bukan
art final, bukan klaim AIPlayer, item/forge atau seluruh pertandingan selesai.
