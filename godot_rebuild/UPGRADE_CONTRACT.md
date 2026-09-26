# Kontrak upgrade Archer — level 1–6

Tersedia hanya lewat mode **Pertandingan awal**. Laboratorium siege tetap memulai Archer tier 1 tanpa tombol upgrade. Jalur Cannon level 2–6 kini tersedia terpisah, lihat [kontrak cannon](CANNON_CONTRACT.md). Jalur Ice level 2–6 kini tersedia terpisah, lihat [kontrak ice](ICE_CONTRACT.md). Belum ada Mage atau paid regen shield. Upgrade nexus kini tersedia terpisah, lihat [kontrak nexus](NEXUS_CONTRACT.md).

## Sumber dan angka yang diuji

Sumber: `_core.ARCHER_LEVELS`, `TOWER_HP_MULTIPLIER`, `TOWER_MAX_LEVEL`, `Tower.can_upgrade/upgrade_cost/upgrade/_apply_level_stats/sell_value/_shoot_archer` di `_entity.py`, serta `get_archer_bow_position` di `towers/_bundle.py`. `tests/upgrade_source_oracle.py` mengeksekusi metode asli tersebut, bukan menyalin expected result dari implementasi Godot. Import presentasi diganti helper numerik asli; Bullet menjadi pencatat numerik tanpa Pygame.

| Level | Biaya masuk level | HP efektif | Shield | Damage/panah | Range | CD tick | Armor | Panah/volley | Refund jual |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | Build 100 | 2000 | 800 | 20 | 180 | 35 | 3 | 1 | 50 |
| 2 | 175 | 2625 | 1050 | 33 | 190 | 32 | 4 | 1 | 87 |
| 3 | 325 | 3375 | 1350 | 50 | 200 | 30 | 5 | 1 | 250 |
| 4 | 550 | 4375 | 1750 | 72 | 210 | 27 | 6 | 1 | 525 |
| 5 | 850 | 5500 | 2200 | 98 | 220 | 24 | 7 | 2 | 950 |
| 6 | 1300 | 7000 | 2800 | 130 | 230 | 22 | 8 | 3 | 1600 |

Harga upgrade adalah harga **level tujuan**. Refund level 2+ adalah `int(0.5 × total biaya upgrade)`, **tidak** memasukkan biaya build 100 G. Refund 50 G level 1 adalah fallback UI Python ketika `sell_value()` menghasilkan nol. Paid regen shield dapat memengaruhi refund di sumber, tetapi belum ada dalam mode ini.

## Transaksi dan state

- Level 1 → 2 memilih jalur **Archer** secara eksplisit, sesuai kebutuhan `Tower.upgrade("archer")`. Belum ada selector jalur alternatif.
- Hanya tower blue hidup yang masih mengisi slot miliknya dapat di-upgrade. Nexus, minion, tower lawan/mati, ID terjual dan hasil pertandingan ditolak.
- Command membawa **entity ID + expected level**, bukan referensi seleksi. Perubahan seleksi tidak memindahkan target transaksi; expected level berbeda menolak command lama, bukan membeli level berikut tanpa persetujuan baru.
- Maksimal satu command per physics tick. Saldo, ownership, level/cap dan status pertandingan diperiksa ulang sebelum debit. Tidak ada callback/await di tengah mutasi.
- Upgrade mengganti referensi resource immutable; tidak memodifikasi resource yang dibagi tower/match lain.
- HP dan shield **dipulihkan penuh** ke kapasitas baru. Cooldown yang sedang berjalan, target, regen clock dan projectile lama **tidak direset**. Upgrade bukan cara menembak segera tanpa cooldown.
- Projectile lama menyimpan damage/posisi peluncuran lama; upgrade tidak mengubah panah yang sudah terbang.
- Ledger tetap `opening + passive + earned + refunded − spent = gold`. UI harga/refund/pesan hasil membaca angka tier yang benar.
- Pause/focus membatalkan upgrade tertunda; hasil menonaktifkannya; restart mengembalikan resource tier 1 dan saldo awal.

## Pola tembak sumber, bukan label tabel

Tabel level 6 menyebut “DOUBLE SHOT”, tetapi metode `_shoot_archer` menghasilkan **dua panah pada level 5 dan tiga pada level 6**. Setiap panah memiliki damage penuh, bukan damage dibagi jumlah panah.

1. Panah pertama menuju target utama hasil targeting lama.
2. Cari target tambahan dari urutan enemy minion yang stabil, melewati target utama, unit mati, kawan dan yang di luar range. Hero/boss belum dipindahkan; tidak ada klaim parity daftar target hero/boss.
3. Jika target tambahan kurang, isi sisa dengan target utama. Tidak menghilangkan panah saat hanya satu lawan.
4. Semua panah memakai orientasi muzzle dari target utama, bukan mengubah arah bow untuk target sekunder.
5. Height platform untuk level 1–6: 38/42/46/52/56/62. Muzzle memakai float double lalu truncation `int` seperti helper sumber.
6. Offset volley setelah skala/truncation: level 5 `(-5,0)/(5,0)`; level 6 `(-7,2)/(0,-1)/(7,2)`.
7. Satu cooldown untuk seluruh volley. Tidak ada damage pada tick launch; masing-masing shot hanya boleh impact satu kali. Overkill target yang sama tetap satu death/reward.
8. **Safety extension:** reservasi kapasitas seluruh volley sebelum spawn. Jika tidak cukup tempat dalam cap 256, tidak ada panah parsial, ID atau cooldown yang terpakai. Source Python tidak mempunyai cap ini.
9. Sale/kematian owner membatalkan seluruh panah miliknya, mengikuti lifecycle projectile yang sudah ada.

## Upgrade nexus (terpisah, sudah diimplementasikan)

Audit awal menemukan ketergantungan yang tidak boleh diabaikan, kini semuanya dipindahkan bersama tombol nexus:

- `NEXUS_LEVELS` mengubah minion scale **dan AI level**, bukan hanya HP/damage castle.
- Komposisi wave dipilih berdasarkan tier nexus pada awal wave. Queue sumber menyimpan kind/lane; constructor minion membaca tier nexus **ketika spawn**, sehingga upgrade saat queue berjalan dapat memengaruhi spawn berikutnya, tanpa mengubah unit lama.
- Castle memakai formula HP berbeda dari tower: `int(new_max × old_hp / old_max) + (new_max − old_max)`, lalu bonus 500 dan cap. Bukan full heal sederhana.
- Kapasitas/persentase shield saat upgrade hanya diperbarui `_apply_level_stats` bila shield berbayar sudah dibeli. Jangan menyamakan dengan reset shield Archer atau diam-diam “membetulkan” sumber.

Detail angka, quirk `tower_kind`, urutan ID vs spatial-hash, dan batas auto-scaling: [kontrak nexus](NEXUS_CONTRACT.md). Jalur Archer (`upgrade_tower`) tetap menolak nexus; nexus memakai `upgrade_nexus` dengan formula HP/shield sendiri.

## Bukti

- Inti `6e115e4`: [1.879 native checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36153624268).
- UI `7c96c83`: [1.905 native checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36153883271), Godot 4.7.2 resmi, Linux headless. Seluruh suite sebelumnya tetap berjalan.
- Fixture enam tier dan 36 skenario muzzle/volley, exact prices/refunds/target order, state restoration/preservation, insufficient funds, dead/stale/max guards, shared-resource isolation, cap atomicity, impact/overkill, UI quote/refund, duplicate/stale command, pause/focus/result/restart dan bounds HUD.

Belum ada tes Windows/GPU/screenshots, Android nyata, performa perangkat atau balance pertandingan panjang. Penanda tier berupa titik dan inspeksi angka bukan port artwork/animasi Archer produksi.
