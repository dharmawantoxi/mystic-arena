# Kontrak upgrade nexus — level 1–5 + dependensi

Tersedia hanya lewat mode **Pertandingan awal**. Laboratorium minion/siege tetap tier 1 tanpa tombol upgrade nexus. Lawan tetap builder terjadwal tanpa auto-scaling castle.

## Sumber dan angka

Sumber: `_core.NEXUS_LEVELS`, `NEXUS_WAVE_COMPOSITION`, `CASTLE_SHIELD_*`, `MAX_NEXUS_LEVEL`, `Castle._apply_level_stats/upgrade/upgrade_cost/set_wave/get_minion_composition/take_damage` di `_entity.py`, formula scaling `Minion.__init__`, `Game._get_wave_composition/_auto_scale_ai_castle/update_waves`, serta `Minion._find_target_smart`. `tests/nexus_source_oracle.py` mengeksekusi metode asli tersebut (presentasi/audio di-stub, tanpa Pygame), bukan menyalin angka dari Godot.

| Level | Biaya masuk | HP | DMG | Range | CD | Shield cap | Scale | AI | Upgrade cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | — | 4000 | 35 | 150 | 45 | 4000 | 1.0 | 1 | 500 |
| 2 | 500 | 6000 | 55 | 165 | 40 | 6000 | 1.2 | 2 | 900 |
| 3 | 900 | 8500 | 80 | 180 | 35 | 8500 | 1.4 | 3 | 1500 |
| 4 | 1500 | 11500 | 115 | 195 | 30 | 11500 | 1.7 | 4 | 2400 |
| 5 | 2400 | 15000 | 160 | 210 | 25 | 15000 | 2.0 | 5 | 0 (maks) |

Harga upgrade adalah harga **level tujuan** (`NEXUS_LEVELS[level_lama]["upgrade_cost"]`). Nexus tidak bisa dijual (`sale_refund` 0, domain menolak).

## Aturan HP/shield saat upgrade (bukan full heal Archer)

`Castle._apply_level_stats` asli:

1. `hp_ratio = old_hp / old_max`, `hp = int(new_max × ratio) + (new_max − old_max)`, lalu `min(new_max, hp + 500)`. Truncation `int()` Python dipertahankan.
2. Damage/range/cooldown diganti ke tier baru. Cooldown, target, regen clock, dan projectile lama **tidak direset**.
3. Kapasitas/persentase shield **hanya** diperbarui bila `castle_shield_purchased` true: `ratio = clamp(shield / old_max)`, `shield_max = int(new_max × 1.0)`, `shield = int(new_max × ratio)`. Tanpa pembelian, `shield_max/shield/shield_active` tidak berubah (quirk sumber dipertahankan, bukan “diperbaiki” diam-diam).
4. `set_wave`: gratis aktif bila `wave ≤ 10`. Bila gratis: `shield_active = true`, isi ulang ke `shield_max` bila kosong. Bila lewat wave 10 dan belum dibeli: `shield_active = false`, `shield = 0`. Bila sudah dibeli: tetap aktif tanpa isi ulang otomatis.
5. Shield nexus menyerap raw damage dulu, sisa direduksi 88% lalu `int()`. Reduksi tetap berlaku meski shield 0 selama flag aktif; damage kecil bisa menjadi 0. Regen 3.5/tick setelah 120 tick tanpa damage, cap `shield_max` instance (bukan kapasitas definisi baru bila belum dibeli).

Pembelian paid shield (`CASTLE_SHIELD_COST` 850) **belum** diaktifkan sebagai transaksi UI. Flag purchased hanya dipakai internal untuk aturan resize di atas dan diuji via fixture.

## Scaling stat minion (snapshot saat spawn)

`Minion.__init__` asli membaca tier nexus pemilik **ketika spawn**:

- `max_hp = int(base_hp × scale)`, `damage = int(base_dmg × scale)`, `gold = int(base_gold × scale)`
- `speed = base_speed × (1 + (scale−1) × 0.3)`
- `cooldown = max(10, int(base_cd / (1 + (scale−1) × 0.2)))`
- `regen = base_regen × scale` (float)
- `range/radius/armor/magic_resist` tidak berubah; `ai_level` dari tabel.

Queue sumber menyimpan `kind/lane`; tier dibaca saat spawn. Upgrade di tengah antrean memengaruhi spawn berikutnya, **tanpa** mengubah unit lama. Godot memakai duplikat definisi per-unit untuk tier >1 (tier 1 memakai resource dasar); resource dasar tidak dimutasi.

## AI tier 1–5 (`_find_target_smart`)

- `in_range`: `dist ≤ range`. Bila kosong: kejar musuh terdekat dengan `dist < range+30`, pertama menang tie.
- Bila ada: AI1 terdekat; AI2 minion satu lane pertama, else pertama; AI3 HP terendah; AI4 minion HP terendah else terdekat; AI5 base (`max_hp ≥ 1500`) pertama, else tower HP terendah, else minion HP terendah, else pertama. Tie HP/jarak: pertama menang (scan `<`, tanpa sort tak-stabil).
- Urutan Godot: ID spawn stabil (merge units+structures), bukan urutan spatial-hash Python. Skenario uji dipilih agar hasil sama untuk kedua urutan pada kasus yang diuji; perbedaan urutan hash vs ID adalah deviasi terdokumentasi.
- Quirk sumber: `Tower` menyimpan `tower_type`, bukan `tower_kind`, sehingga cabang `hasattr(tower_kind)` tidak pernah cocok. Karena semua tower/nexus saat ini `max_hp ≥ 1500`, cabang base sudah menangkapnya; Godot memeriksa `structure_kind == "tower"` setelah base dengan hasil observasi identik untuk stat saat ini.

Hero/boss belum dipindahkan; tidak ada klaim parity daftar target hero/boss.

## Komposisi wave per-tier

Base per castle tier (`NEXUS_WAVE_COMPOSITION`):

- 1: `g,g,g`; 2: `g,g,g,orc`; 3: `g,orc,g,orc,undead`; 4: `orc,goblin,orc,undead,g,g`; 5: `orc,orc,undead,troll,g,g`.

Scaling nomor wave (di atas base, sesuai `_get_wave_composition`):

- 1–3: base; 4–6: +`orc`; 7–9: +`orc,undead`; 10–12: +`troll,dark_rider,undead`; 13+: +`troll,troll,dark,dark,undead`.

Komposisi dibaca **saat wave start** per tim (bisa beda bila tier beda). Antrean dikuras 1/tim/20 tick (biru lalu merah). Timer 1500, wave baru menunggu antrean kosong + lapangan bersih (tanpa minion hidup). `set_wave` dipanggil saat wave start.

`_auto_scale_ai_castle` sumber (merah ke 2/3/4/5 pada wave 4/7/10/13) **tetap nonaktif** di prototipe agar replay lama stabil. Merah tetap tier 1 kecuali diuji eksplisit via scheduler.

## Transaksi dan UI

- Hanya nexus biru hidup yang bisa di-upgrade. Nexus lawan/mati, tower, minion, ID terjual, dan hasil ditolak.
- Command membawa **entity ID + expected level**, satu command/tick, validasi ulang saat eksekusi. Pause/focus membatalkan; restart mereset ke tier 1 + 1000 G.
- Ledger tetap `opening + passive + earned + refunded − spent = gold`.
- Tombol terpisah **Upgrade Nexus** (bukan reuse Upgrade Archer) agar tes lama “Upgrade Archer disabled saat nexus dipilih” tetap berlaku. Quote dinamis 500/900/1500/2400, lalu “Nexus maksimum”. Inspeksi nexus menampilkan Shield/DMG tanpa jumlah panah.

## Bukti dan batas

- Fixture `nexus_source.json`: 5 tier, 120 kasus HP/shield, 36 kasus `set_wave`, 25 scaling (5 kind × 5 tier), komposisi 5 tier × 10 wave, 20 kasus AI.
- Tes native `nexus_checks.gd` + `nexus_scene_checks.gd` terintegrasi di `run_all.gd`, seluruh suite lama tetap berjalan.
- Belum diuji: Windows fisik/GPU, Android, balance pertandingan panjang, paid shield sebagai transaksi, auto-scaling AI, hero/boss.
