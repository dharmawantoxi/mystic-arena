# Paid shields — domain native, WIP AIPlayer

Sumber read-only: `_entity.py::Tower` (`can_activate_regen_shield`,
`activate_regen_shield`, `_update_regen`, `sell_value`), `Castle`
(`can_activate_castle_shield`, `activate_castle_shield`, `_update_castle_shield`,
`set_wave`, `take_damage`), dan dua aksi shield `AIPlayer`. Angka dari `_core.py`.

## Status dan batas

Transaksi shield tersedia di domain pertandingan untuk kedua tim. Adapter
`ai_shields.gd` khusus red membaca reserve draft terkini, per kandidat. **Belum
ada tombol beli shield atau AI otomatis di scene**. Prioritas kandidat tower
kills descending masih pending, bukan diganti dengan total kill tim. Sumber
aksi shield tidak melempar RNG dan tidak menaikkan counter upgrade; port sama.

## Regen Shield tower

- Harga **850 G**, hidup, tower **Lv4–6**, belum dibeli. Tower Lv6 tetap eligible
  walaupun tidak bisa upgrade lagi. Semua empat path mengikuti aturan sama.
- Aktivasi mengisi shield ke `shield_max`, mengaktifkan `regen_shield_active`
  per instance; **tidak** mengubah HP atau mereset `no_damage_ticks`.
- Shield regen **1,8/tick** setelah clock mencapai **180**, dibatasi kapasitas
  instance. HP regen tetap 0,3/tick setelah 300 tick, tanpa bergantung pembelian.
- Hit yang diterima tower mereset clock meskipun seluruh damage diserap shield.
  Struktur mati tidak ditick. Flag paid bertahan melewati upgrade; resource `.tres`
  bersama tidak diubah. `shield_regen_enabled` pada resource tower tetap false
  sebagai keadaan awal, bukan tempat menyimpan pembelian.
- Refund jual menambahkan **425 G** (setengah biaya shield) pada refund upgrade
  tower yang sudah ada. `sale_value()` adalah quote yang sama untuk debit/refund
  domain dan label tombol **Jual**. Tanpa shield, refund lama tidak berubah.
  Jual tetap hanya blue; bukan death, tidak memberi gold lawan, hanya sekali.

## Castle Shield

- Harga **850 G** (`CASTLE_SHIELD_COST` alias harga tower), boleh dibeli setelah
  perlindungan gratis wave 10 berakhir, belum purchased. **Tidak ada gate Lv4**:
  metode Python sebenarnya mengizinkan Lv1 setelah wave 10, meskipun beberapa
  komentar sumber lama menyebut Lv4. Port mengikuti kode, bukan komentar lama.
- Aktivasi: purchased true, free false, shield aktif, kapasitas **100% HP max
  level saat ini**, isi penuh, clock regen **reset 0**; HP tidak dipulihkan.
- Regen **3,5/tick** setelah clock 120. Saat shield tidak aktif, clock tidak
  bertambah **dan hit tidak meresetnya**, sesuai early-return sumber. Ini
  memperbaiki clock native lama yang bergerak/reset walaupun nexus tanpa shield.
- Shield tetap aktif pada wave berikutnya; tidak diisi ulang oleh `set_wave`
  setelah fase gratis. Upgrade berbayar mempertahankan persentase shield dan
  memperbarui kapasitas (lihat [NEXUS_CONTRACT.md](NEXUS_CONTRACT.md)).
- Damage aktif: shield menyerap lebih dulu; sisa dikurangi 88% lalu `int`, bahkan
  saat shield kosong. Perilaku lama ini tidak diubah.

## Transaksi dan safety

Validasi selesai pertandingan, tim 0/1, ID/jenis, owner/slot atau nexus
registry authoritative, eligibility, dan saldo minimal `850 + max(0, reserve)`
sebelum activation/debit. Tidak ada await/callback di tengah operasi.
Duplicate, ID salah, sold/stale, musuh, mati dan finished tidak mengubah wallet
atau flag. **Tambahan safety native:** Castle Python tidak mengecek `alive` pada
eligibility-nya; domain native menolak castle mati dan nexus non-authoritative.
State helper sendiri hanya mengubah state; transaksi berbayar harus melewati
world, bukan memanggil helper state langsung dari command/AI.

## Bukti pengujian

`ai_shield_source_oracle.py` mengeksekusi metode sumber asli: 126 transaksi tower,
90 castle, 22 trace regen/hit (delay −1/tepat/+1, cap, shield gratis/off/paid),
refund tower semua path Lv4–6 dan upgrade castle purchased. Oracle `--write`
hanya menulis fixture native. Delapan oracle lama tetap dijalankan.

Suite native memakai world/ledger asli; tes tambahan mencakup reserve ±1,
isolasi instance tanpa mutasi `.tres`, sold ID, rebuild, owner/type/invalid team,
kematian dan hasil. Suite scene memeriksa label refund, double-click command,
restart/reset, dan cleanup node. Seluruh suite baseline tetap ada tanpa perubahan
assertion. Tidak ada klaim uji GPU, VFX flash sumber, perangkat fisik, atau
AIPlayer lengkap dari paket shield ini.
