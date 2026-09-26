# Kontrak jalur Mage — level 2–6, chain + skill-down/anti-heal

Tersedia hanya lewat mode **Pertandingan awal**. Tower level 1 memilih jalur **Archer**, **Cannon**, **Ice**, atau **Mage** secara eksplisit; level 2+ mengabaikan argumen jalur dan mempertahankan jalurnya (quirk sumber yang dikunci fixture). Skill-down hanya berupa state pada minion (konsumennya `Hero.skill_damage`, di luar scope); belum ada hero/skill, paid regen shield, atau efek status lain.

## Sumber dan angka yang diuji

Sumber: `MAGE_LEVELS`, `TOWER_HP_MULTIPLIER`, `TOWER_SHIELD_HP_RATIO`, `Tower.can_upgrade/upgrade_cost/upgrade/sell_value/_apply_level_stats/_shoot_mage` dan `Bullet._on_hit` cabang `"mage"` di `_entity.py`, `TowerDebuffMixin.apply_debuff/_tick_tower_debuffs` + property `hp` anti-heal di `_core.py`, serta `get_mage_crystal_position` + `LEVEL_CONFIGS` di `towers/_bundle.py`. `tests/mage_source_oracle.py` mengeksekusi metode asli tersebut; korban chain memakai `Minion.take_damage`/`apply_debuff` dan setter `hp` asli sehingga semantik debuff tercatat apa adanya.

| Level | Biaya masuk | HP efektif | Shield | Damage | Range | CD tick | Armor | Chain | Skill-down | Anti-heal | Durasi | Refund |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---:|---:|
| 2 | 175 | 2125 | 850 | 17 | 180 | 20 | 4 | 2 | 0.20 | 0.40 | 120 | 87 |
| 3 | 325 | 2750 | 1100 | 26 | 190 | 18 | 5 | 2 | 0.25 | 0.50 | 130 | 250 |
| 4 | 550 | 3625 | 1450 | 39 | 200 | 16 | 6 | 3 | 0.30 | 0.60 | 140 | 525 |
| 5 | 850 | 4625 | 1850 | 55 | 210 | 14 | 7 | 3 | 0.40 | 0.75 | 150 | 950 |
| 6 | 1300 | 5875 | 2350 | 70 | 230 | 12 | 8 | 4 | 0.50 | 1.00 | 180 | 1600 |

Biaya/refund per tier identik dengan ketiga jalur lain karena tabel `cost` sama. HP/shield dipulihkan penuh saat upgrade; cooldown, target, regen clock, dan projectile lama dipertahankan.

## Pemilihan jalur

- Level 1: `upgrade(None)`/`upgrade("bogus")` ditolak; keempat jalur berharga 175. Godot menerima keempatnya, menolak sisanya dengan error `path`.
- Level 2+: argumen jalur diabaikan — upgrade Mage dengan argumen `"archer"` tetap Mage. Bukan bug port; perilaku sumber.
- Resource Mage 2–6 immutable dan terpisah dari jalur lain; penjualan memakai refund tier Mage.

## Muzzle, volley, dan chain

- Tiap bolt `"mage"` membawa `skill_down/anti_heal/debuff_duration`. Tidak ada damage pada tick launch; satu cooldown per volley.
- Muzzle memakai helper kristal sumber + offset aim 5px dalam double 64-bit; cocok exact untuk level 2–6 dan 8 arah aim. Kristal x=500 face-independen; tinggi kristal 45/48/52/56/60/66.
- Chain: target utama + musuh dalam range menara sesuai urutan list, melewati identitas-target/mati/di-luar-range, dibatasi `chain`. **Tanpa refill** (solo = 1 bolt, bukan tembakan ganda ke target utama). Semua bolt memakai muzzle target utama. Tidak ada cek tim di dalam `_shoot_mage`; pemanggil menyuplai daftar musuh (Godot memfilter kawan saat membangun daftar).
- Tiap bolt chain adalah proyektil terpisah dengan targetnya sendiri; tiap korban menjalankan `_on_hit` sekali.

## Debuff

- Stack rule sama dengan slow: stronger ATAU longer menimpa kedua field (weaker+longer menimpa amount — quirk sumber).
- Struktur no-op (tidak punya `apply_debuff`); unit mati dilewati gate alive dan debuff dibersihkan saat mati (`clear_tower_debuffs`).
- Anti-heal bekerja di setter `hp`: kenaikan HP diskalakan `(1 − amount)`. Cap `max_hp` diterapkan SEBELUM scaling — quirk sumber: 44.8 + regen 0.6 dengan anti 0.5 menjadi 44.9, bukan 45.0. Anti 1.0 (Mage 6) memblokir regen penuh.
- Skill-down tidak mengubah perilaku minion; hanya state amount/timer yang di-tick. Efeknya (`int(round(base × (1 − amount)))`) hanya ada di `Hero.skill_damage`.

## UI dan transaksi

- Tujuh tombol dalam dua baris: baris perintah (Build/Sell/Upgrade/Nexus) + baris **Paths** (Cannon/Ice/Mage). Baris Paths tampil ⟺ tower biru level 1 dipilih; Nexus menyingkir saat itu. Maksimal enam tombol tampil.
- Command membawa ID + expected level + path; level 2+ mengunci pilihan. Guard stale/max/poor/dead/enemy/result/pause/focus sama dengan jalur lain; error `path` berpesan khusus.
- Inspeksi Mage menyebut **bolt** dengan jumlah chain (`2 bolt` di level 2), bukan panah. String harga lama dipertahankan.

## Bukti

- Domain `fbace74`: [4.425 native checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36208534296).
- UI `f1b80b9`: [4.452 native checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36208792355), Godot 4.7.2 resmi, Linux headless. Seluruh suite sebelumnya tetap berjalan.
- Fixture: 5 tier, muzzle kristal 5×8 arah, volley chain 5×(2 full + solo: order/cap/boundary/mati/luar), on-hit 3 level (mati = clear), stacking 2 jenis + 5 tick + 6 baris regen anti-heal.

Belum ada tes Windows/GPU/screenshots, Android nyata, performa perangkat, atau balance pertandingan panjang. Hero/skill/AI penuh belum dipindahkan.
