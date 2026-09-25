# Kontrak tower, projectile & nexus — tahap 3

Mode **Tower & nexus** memperluas simulasi minion tanpa mengubah aturan mode Laboratorium minion. Masih laboratorium: wave manual, bangunan sudah tersedia, tanpa ekonomi atau progres tersimpan.

## Implementasi

- Enam Archer level 1 (satu per lane/tim) dan dua nexus level 1.
- Tower menembakkan projectile homing, bukan damage instan saat launch.
- Minion dapat menarget dan menghancurkan bangunan musuh. Setelah jalur selesai, minion terus menuju nexus, bukan keluar arena.
- HP/shield, regen, cooldown, projectile, death dan hasil berjalan pada 60 physics tick/detik.
- Hasil pertama ketika nexus hancur membekukan world. Tidak ada wave atau damage baru setelah hasil final.
- Inspeksi bangunan/unit, indikator HP/shield, pilihan wave kedua tim/biru/merah, pause, restart dan kembali menu.
- Mode input dan minion lama tetap tersedia sebagai regresi.

## Sumber dan nilai efektif

| Bagian | Sumber Python | Nilai tahap ini |
|---|---|---|
| HP Archer | `ARCHER_LEVELS[1].hp × TOWER_HP_MULTIPLIER` | 800 × 2.5 = **2000** |
| Shield Archer | HP efektif × `TOWER_SHIELD_HP_RATIO` | 2000 × 0.4 = **800** |
| Serangan Archer | `_entity.py:Tower._apply_level_stats` | Damage 20, range 180, cooldown 35 tick, armor 3 |
| HP regen Archer | `Tower._update_regen` | 0.3 HP/tick setelah 300 tick tanpa damage |
| Shield regen Archer | `Tower._update_regen` | **Tidak aktif** secara default; pembelian regen belum tersedia |
| Kredit tower | `Tower.__init__`, default outer | 100, hanya counter audit laboratorium |
| Nexus | `NEXUS_LEVELS[1]`, `Castle` | HP 4000, damage 35, range 150, cooldown 45 tick |
| Shield nexus | `CASTLE_SHIELD_*` | 4000; regen 3.5/tick setelah 120 tick; proteksi sampai wave 10 |
| Projectile | `Bullet.update`, `BULLET_SPEED`, `BULLET_RADIUS` | Speed 8 px/tick; impact jika distance < 8 + 4 |
| Asal projectile Archer | `towers/_bundle.py:get_archer_bow_position` | Helper level 1, skala 0.7 dan truncation integer dipertahankan |
| Asal projectile nexus | `Castle._shoot` | Posisi nexus + (0, -25) |

Posisi tower adalah subset data sumber `BLUE_TOWERS` / `RED_TOWERS`, indeks 2, 5, 8 masing-masing; bukan seluruh sembilan tower per tim atau sistem build-slot produksi. Posisi nexus mengikuti koordinat sumber (100,620) dan (1180,100).

## Dua aturan damage bangunan yang berbeda

### Tower

1. Hit valid mereset clock regen, meski seluruh damage diserap shield.
2. Physical melewati mitigasi armor; magic melewati magic resist jika ada.
3. Armor tower <=0 tidak memperbesar damage, berbeda dari minion.
4. Shield menyerap **damage setelah mitigasi**.
5. Sisa masuk HP; kematian dan kredit tower terjadi satu kali.

### Nexus

1. Nexus belum memakai armor/magic resist dalam kode sumber yang dipindahkan.
2. Shield aktif menyerap raw damage terlebih dahulu.
3. Sisa damage saat perlindungan aktif direduksi **88%**, lalu diubah menjadi integer seperti Python.
4. Bahkan saat HP shield habis, flag perlindungan yang masih aktif tetap memberi reduksi. Damage kecil dapat menjadi **0 HP damage**; jangan memaksakan minimum 1 pada jalur nexus.
5. `set_wave(10)` masih aktif. `set_wave(11)` mematikan shield yang belum dibeli dan mengosongkannya.
6. Sesuai helper sumber, `set_wave` selama periode gratis mengisi ulang shield yang sudah habis. Di laboratorium ini helper dipanggil saat wave uji berhasil ditambahkan.

Pembelian shield nexus/regen tower belum diimplementasikan. Resource menyimpan parameter dasar, bukan transaksi atau upgrade.

## Urutan dan lifecycle

- Urutan per tick: minion → tower → nexus, mengikuti loop sumber untuk subset entitas ini.
- Per bangunan: cooldown/regen → update projectile lama → targeting → launch jika siap.
- Projectile baru belum bergerak atau memberi damage pada tick launch.
- Target minion tier 1 tetap memilih jarak terdekat dengan tie ID awal; tower/nexus menggunakan `<=` seperti sumber sehingga ID belakangan menang pada jarak persis sama.
- `_deliver_hit()` adalah jalur tunggal perubahan HP/death/event. Serangan melee dan impact projectile memanggilnya, visual tidak.
- `apply_hit()` dari penyerang bangunan ditolak; bangunan wajib memakai projectile.
- Projectile dimatikan **sebelum** damage impact diterapkan. Update berulang tidak dapat mengulang hit.
- Target mati/hilang membatalkan projectile. Penembak mati membatalkan projectile miliknya, sesuai model bullet yang dimiliki bangunan pada sumber.
- Registry memakai ID monoton per world, bukan referensi Node visual. Target ID mati dibersihkan.
- Kematian tower memakai counter `tower_kills` terpisah dari kill minion dan memberi kredit audit satu kali. Kematian nexus tidak menciptakan currency/reward.
- Nexus pertama yang hancur menentukan pemenang sesuai urutan deterministik. World berhenti, projectile dibatalkan, dan hasil tidak diterbitkan ulang.
- Restart membentuk world baru. Pause menghentikan seluruh clock dan membatalkan antrean wave beserta pilihan timnya.

## Batas dan keputusan laboratorium

1. Tidak ada build, upgrade, sell, tower Cannon/Ice/Mage, paid shield, hero, boss atau skill.
2. Wave tambahan tetap manual: 6 unit untuk kedua tim, 3 untuk satu tim. Memilih satu tim memudahkan uji siege tidak seimbang. Ini **bukan** scheduler wave produksi atau kontrol pemain final.
3. `wave_count` laboratorium juga menjadi input masa perlindungan nexus. Teks UI menyebutnya wave uji; produksi harus memakai scheduler asli nanti.
4. Batas 120 minion, 16 bangunan dan 256 projectile. Wave yang melebihi kapasitas ditolak atomik. Gagal launch karena cap tidak mengonsumsi cooldown.
5. TTL projectile **180 tick** merupakan guard baru yang terdokumentasi; sumber tidak mempunyai TTL eksplisit. Projectile kedaluwarsa tidak memberikan damage.
6. Bangunan dan unit digambar sederhana. Model tubuh, animasi, lighting, suara dan VFX produksi belum dipindahkan. Muzzle memakai helper sumber meskipun gambar Archer masih placeholder.
7. Kondisi menang/kalah adalah **hasil laboratorium berdasarkan nexus**, bukan seluruh aturan kemenangan level/boss game produksi.
8. Semua kredit hanya untuk audit. Tidak ada save, achievement, level unlock, cloud atau pembayaran.
9. Tidak ada jaminan keseimbangan duel simetris atau performa low-end. Uji Windows/GPU/Android nyata masih diperlukan.

## Bukti pengujian

`tests/structure_source_oracle.py` mengeksekusi **metode numerik terpilih dari sumber Python asli** (`Tower`, `Castle`, helper muzzle), bukan converter lama. Callback presentasi di-stub; modul Pygame/game tidak diimpor. Fixture mencakup:

- Stat setelah multiplier dan nilai shield/regen.
- 60 kombinasi damage physical/magic, shield tersisa dan overkill.
- Boundary regen, posisi tower dan posisi muzzle.

Tes native `siege_checks.gd` memeriksa fixture tersebut, launch tanpa damage instan, satu hit/credit, pembatalan owner/target, TTL/cap, cooldown 35 tick, shield wave 10/11, endpoint menuju nexus, hasil satu kali, dan replay deterministik selama 2.400 tick.

`run_all.gd` menambah tiga siklus scene siege: pilihan tim via UI, antrean tidak mengubah world sebelum tick, pause projectile, seleksi melalui transform skala, restart, hasil di HUD dan cleanup node. Seluruh suite sebelumnya tetap berjalan.

Checkpoint `d09ce35`: **1.158 pemeriksaan native lulus** di [GitHub Actions](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36117033161), Godot 4.7.2 headless Linux. Ini bukan pengujian visual atau perangkat Windows/Android.

## Pekerjaan berikutnya

Audit `Game.update_waves`, `NEXUS_WAVE_COMPOSITION`, ekonomi awal/pasif, build slot dan transaksi beli/jual. Tambahkan satu loop pertandingan dengan scheduler dan ekonomi minimum, disertai fixture, sebelum hero/skill atau seluruh 54 level. Jangan mengganti kontrol laboratorium menjadi mekanik produksi tanpa kontrak yang jelas.
