# Kontrak jalur Ice — level 2–6, slow + attack-slow

Tersedia hanya lewat mode **Pertandingan awal**. Tower level 1 memilih jalur **Archer**, **Cannon**, **Ice**, atau **Mage** secara eksplisit; level 2+ mengabaikan argumen jalur dan mempertahankan jalurnya (quirk sumber yang dikunci fixture). Belum ada paid regen shield atau efek status selain burn/slow/atk-slow/skill-down/anti-heal. Jalur Mage didokumentasikan terpisah, lihat [kontrak mage](MAGE_CONTRACT.md).

## Sumber dan angka yang diuji

Sumber: `ICE_LEVELS`, `TOWER_HP_MULTIPLIER`, `TOWER_SHIELD_HP_RATIO`, `Tower.can_upgrade/upgrade_cost/upgrade/sell_value/_apply_level_stats/_shoot_ice` dan `Bullet._on_hit` cabang `"ice"` di `_entity.py`, `Minion.apply_slow` + `TowerDebuffMixin.apply_debuff("atk_slow")/_tick_tower_debuffs` di `_core.py`/`_entity.py`, serta `get_ice_crystal_position` + `LEVEL_CONFIGS` di `towers/_bundle.py`. `tests/ice_source_oracle.py` mengeksekusi metode asli tersebut; korban on-hit memakai `Minion.take_damage`/`apply_slow`/`apply_debuff` asli sehingga semantik slow tercatat apa adanya.

| Level | Biaya masuk | HP efektif | Shield | Damage | Range | CD tick | Armor | Slow | Atk-slow | Refund |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---:|
| 2 | 175 | 2375 | 950 | 20 | 170 | 26 | 4 | 0.25 · 90 | 0.15 | 87 |
| 3 | 325 | 3125 | 1250 | 32 | 180 | 22 | 5 | 0.35 · 100 | 0.20 | 250 |
| 4 | 550 | 4000 | 1600 | 45 | 190 | 18 | 6 | 0.45 · 110 | 0.25 | 525 |
| 5 | 850 | 5125 | 2050 | 60 | 200 | 16 | 7 | 0.55 · 120 | 0.30 | 950 |
| 6 | 1300 | 6500 | 2600 | 78 | 220 | 14 | 8 | 0.65 · 150 + AOE 80 | 0.40 | 1600 |

Biaya/refund per tier identik dengan Archer/Cannon karena tabel `cost` sama. HP/shield dipulihkan penuh saat upgrade; cooldown, target, regen clock, dan projectile lama dipertahankan.

## Pemilihan jalur

- Level 1: `upgrade(None)`/`upgrade("bogus")` ditolak; ketiga jalur berharga 175. Godot menerima `"archer"`/`"cannon"`/`"ice"`, menolak sisanya dengan error `path`.
- Level 2+: argumen jalur diabaikan — upgrade Ice dengan argumen `"archer"` tetap Ice. Bukan bug port; perilaku sumber.
- Resource Ice 2–6 immutable dan terpisah dari Archer/Cannon; penjualan memakai refund tier Ice.

## Muzzle dan volley

- Satu shard `"ice"` per tembakan, membawa `slow/slow_duration/atk_slow` (+`slow_aoe` di level 6). Tidak ada damage pada tick launch; satu cooldown per volley.
- Muzzle memakai helper kristal sumber + offset aim 5px. Seluruh matematika sudut dalam double 64-bit (dilarang memakai `Vector2.angle()` f32); posisi muzzle cocok exact dengan helper untuk level 2–6 dan 8 arah aim.
- Kristal x=500 face-independen; tinggi kristal per level 40/44/48/54/58/64 dari `LEVEL_CONFIGS`.

## Slow gerak

- Apply: aturan `amount > slow_amount atau slow_timer < duration` menimpa **kedua** field — slow yang lebih lemah namun lebih lama tetap menimpa amount (quirk sumber, dikunci fixture).
- Struktur no-op (`Castle.apply_slow` adalah `pass` di sumber); tidak ada cek tim di level apply, pemanggil AOE yang memfilter kawan.
- Tick: decrement tiap tick, amount dinolkan saat timer habis. `_eff_speed` f64 exact: `speed × (1 − amount)` saat timer > 0.

## Attack-slow dan AOE level 6

- Attack-slow lewat `apply_debuff("atk_slow")` dengan stack rule yang sama; unit mati dilewati (gate alive sumber). Cooldown efektif: 45→53/60/75 dan 22→26/29/37.
- AOE hanya level 6: unit musuh dalam 80px dari target utama menerima slow + attack-slow **tanpa damage**. Batas radius inklusif; target utama, kawan, dan unit mati dilewati. **Bangunan kebal** karena `all_units` sumber tidak berisi tower/nexus.

## UI dan transaksi

- Visibilitas kontekstual: baris **Paths** (Cannon/Ice/Mage) tampil ⟺ tower biru level 1 dipilih; tombol Nexus menyingkir saat itu. Maksimal enam dari tujuh tombol tampil dalam dua baris sehingga HUD 1280 tidak berubah.
- Command membawa ID + expected level + path; seleksi baru tidak mengubah target tertunda. Level 2+ mengunci pilihan. Guard stale/max/poor/dead/enemy/result/pause/focus sama dengan Archer/Cannon; error `path` berpesan khusus.
- Inspeksi Ice menyebut **kristal**, bukan panah. String harga lama dipertahankan.

## Bukti

- Domain `d1a2644`: [4.008 native checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36206784333).
- UI `3e8ad59`: [4.035 native checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36207205305), Godot 4.7.2 resmi, Linux headless. Seluruh suite sebelumnya tetap berjalan.
- Fixture: 5 tier, muzzle kristal 5×8 arah, volley 5×2 sisi, on-hit 3 level (boundary/luar/kawan/mati), stacking + 5 tick + speed + attack-cd.

Belum ada tes Windows/GPU/screenshots, Android nyata, performa perangkat, atau balance pertandingan panjang. Mage (chain/debuff) dan efek status lain belum dipindahkan.
