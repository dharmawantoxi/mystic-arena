# Kontrak jalur Cannon — level 2–6, splash + burn

Tersedia hanya lewat mode **Pertandingan awal**. Tower level 1 memilih jalur **Archer** atau **Cannon** secara eksplisit; level 2+ mengabaikan argumen jalur dan mempertahankan jalurnya (quirk sumber yang dikunci fixture). Belum ada Ice/Mage, paid regen shield, atau efek status selain burn.

## Sumber dan angka yang diuji

Sumber: `_core.CANNON_LEVELS`, `TOWER_HP_MULTIPLIER`, `TOWER_SHIELD_HP_RATIO`, `Tower.can_upgrade/upgrade_cost/upgrade/sell_value/_apply_level_stats/_shoot_cannon` dan `Bullet._on_hit` cabang `"cannon"` di `_entity.py`, `TowerDebuffMixin.apply_debuff/_tick_tower_debuffs` di `_core.py`, serta `get_cannon_muzzle_position` + `LEVEL_CONFIGS` di `towers/_bundle.py`. `tests/cannon_source_oracle.py` mengeksekusi metode asli tersebut; korban splash/burn memakai `Minion.take_damage` dan `resolve_damage_school` asli sehingga semantik kematian tercatat apa adanya.

| Level | Biaya masuk | HP efektif | Shield | Damage | Range | CD tick | Armor | Splash | Burn | Refund |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| 2 | 175 | 3000 | 1200 | 42 | 165 | 44 | 4 | 45 | 8/s · 120 | 87 |
| 3 | 325 | 3750 | 1500 | 60 | 175 | 40 | 5 | 55 | 12/s · 150 | 250 |
| 4 | 550 | 4750 | 1900 | 84 | 185 | 36 | 6 | 65 | 16/s · 150 | 525 |
| 5 | 850 | 6000 | 2400 | 116 | 195 | 32 | 7 | 80 | 22/s · 180 | 950 |
| 6 | 1300 | 7500 | 3000 | 155 | 210 | 28 | 8 | 100 | 30/s · 180 | 1600 |

Biaya/refund per tier identik dengan Archer karena tabel `cost` sama. HP/shield dipulihkan penuh saat upgrade; cooldown, target, regen clock, dan projectile lama dipertahankan.

## Pemilihan jalur

- Level 1: `upgrade(None)`/`upgrade("bogus")` ditolak; keempat jalur berharga 175. Godot menerima `"archer"`/`"cannon"`, menolak sisanya dengan error `path`.
- Level 2+: argumen jalur diabaikan — upgrade Cannon dengan argumen `"archer"` tetap Cannon. Bukan bug port; perilaku sumber.
- Resource Cannon 2–6 immutable dan terpisah dari Archer; penjualan memakai refund tier Cannon.

## Muzzle dan volley

- Satu peluru `"cannon"` per tembakan, membawa `splash/burn_dps/burn_duration`. Tidak ada damage pada tick launch; satu cooldown per volley.
- Muzzle memakai helper sumber dengan recoil 0: cabang recoil tidak terjangkau saat menembak karena `_shoot` hanya dipanggil saat `timer == 0` (`0 > cd − 8` selalu salah untuk cd 28–44). Fixture mengunci ini per level.
- Urutan float dan truncation `int()` dipertahankan; posisi muzzle cocok exact dengan helper untuk level 2–6 dan kedua sisi.

## Splash

1. Target utama menerima damage penuh, lalu burn (hanya bila masih hidup).
2. Unit musuh lain dalam radius dari titik target menerima `int(damage × 0.6)`, lalu burn bila selamat. Batas radius inklusif (`d <= splash`).
3. Kawan, unit mati, dan target utama dilewati. **Bangunan tidak kena splash** karena `all_units` sumber tidak berisi tower/nexus.
4. Urutan korban mengikuti urutan spawn; tiap korban independen.

**Deviasi terdokumentasi:** splash Godot lewat jalur `_deliver_hit` `"physical"` yang sama dengan semua impact tower, sehingga armor minion (Troll 2, Dark Rider 1) mereduksi splash. Sumber memakai school `None` (tanpa mitigasi). Deviasi yang sama sudah ada untuk semua tembakan tower langsung; pass school-None umum adalah pekerjaan terpisah.

## Burn

- Apply: burn baru mengeset dps/akumulator-0/cd-30; refresh mengambil dps terbesar dan timer terpanjang. **`burn_team` selalu ditimpa** penerap terbaru, bahkan saat dps lebih lemah — quirk sumber.
- Sumber tidak memeriksa tim saat apply; Godot mengikutinya. Kredit kill burn mengikuti aturan korban sumber: selalu ke **lawan korban** (`1 − team`), bukan ke tim penerap.
- Tick: `accum += dps/60` per tick; tiap 30 tick memberi `int(accum)` tanpa mitigasi (`"fire"` → school None). Akumulasi float direproduksi bit-identik: dps 8 memberi **3/5/4/4** (bukan 4/4/4/4) karena error float — dikunci fixture.
- Urutan per tick: burn dulu, lalu regen (sesuai `Minion.update`). Unit mati tidak men-tick burn (early return sumber); timer burn-nya membeku, bukan jalan terus. Kasus `_tick` langsung pada unit mati di fixture hanya mendokumentasikan level mixin yang tak terjangkau lewat `Minion.update`.
- Kematian burn membersihkan debuff, memberi satu kill/kredit, dan tidak menular.

## UI dan transaksi

- Tower biru level 1 menampilkan dua pilihan: **Upgrade** (Archer) dan **Cannon Lv.2 · 175 G**. Command membawa ID + expected level + path; seleksi baru tidak mengubah target tertunda.
- Level 2+ mengunci pilihan: tombol Cannon nonaktif, tombol Upgrade melanjutkan jalur yang terkunci. Guard stale/max/poor/dead/enemy/result/pause/focus sama dengan Archer; error `path` berpesan khusus.
- Lima tombol perintah muat dalam HUD 1280; `%StatusLabel` pindah ke baris sendiri. Inspeksi Cannon menyebut **peluru**, bukan panah.

## Bukti

- Domain `76a7676`: [3.688 native checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36204725077).
- UI `81765fd`: [3.713 native checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36204985361), Godot 4.7.2 resmi, Linux headless. Seluruh suite sebelumnya tetap berjalan.
- Fixture: 5 tier, muzzle 5×2, volley 5×2, splash 3 level (boundary/luar/frail/kawan/mati), burn stacking + 2 deret tick + fallback/kematian.

Belum ada tes Windows/GPU/screenshots, Android nyata, performa perangkat, atau balance pertandingan panjang. Ice (slow), Mage (chain/debuff), dan efek status lain belum dipindahkan.
