# AIPlayer — target paritas penuh, implementasi bertahap

## Status paket

**Belum port AIPlayer lengkap. Jangan merge sebagai pengganti lawan sementara.**
Target yang disepakati: AIPlayer lengkap beserta roster dan item dependensinya,
bukan pembatasan diam-diam ke Kaizen. Scene pertandingan masih memakai defender
lama dan pasangan Kaizen gratis. Tidak ada transaksi ekonomi yang berubah pada
tahap policy ini; seluruh suite lama tetap dijalankan.

Sumber read-only: `_entity.py::AIPlayer`, konstanta `_core.py`,
`Game.update` (pemanggilan AI setelah loop entity), `levels/level_data.py`,
registry hero dan `hero_items.py`. Tidak mengimpor runtime Python ke Godot.

## Implementasi saat ini

`ai_policy.gd` memisahkan jadwal dan urutan keputusan dari adapter aksi domain.
Belum dihubungkan ke scene. Callback aksi hanya menandai berhasil/tidak; callback
kontrol hero harus dipanggil sekali setiap tick, bahkan saat belum waktunya berpikir.

- Timer awal 90 tick, tidak langsung memakai interval elite.
- Brain `min(1, (max(1, level)-1)/19)`.
- Elite nol sampai level 20, kemudian `min(1, (level-20)/(max(21, count)-20))`;
  jumlah level default 54. Tidak bergantung pada flag enemy scaling.
- Reset timer `max(8, int(90*(1-0.65*brain)-22*elite))`.
- Budget `1 + round(2*elite)` memakai ties-to-even Python, bukan round Godot.
- Loop aksi berhenti saat aksi tidak berhasil. Urutan setiap langkah:
  build → beli hero → upgrade hero → item → upgrade tower → regen shield →
  castle shield → upgrade nexus.
- Build gate gold **150**, berbeda dari debit build **100** pada adapter nanti.
- Roll memakai `< min(0.98, base+0.45*elite)`, tanpa roll shield.
  Tidak menggambar RNG pada cabang yang tidak eligible atau sesudah sukses.
- Hero count mencakup hero mati; tower count hanya tower hidup milik AI.
  Regen shield memakai semua tower hidup termasuk tower max level.

## Oracle dan tes

`tests/ai_source_oracle.py` mengeksekusi AST metode Python asli: init, brain,
elite, update dan step. Dependensi aksi diganti probe; ini bukan bukti transaksi,
kontrol hero atau roster lengkap. Fixture mencakup 52 trace jadwal 200 tick,
batas round tepat pada elite 0.25/0.75 (count 24), level clamp, step gagal,
dan 486 skenario prioritas/RNG. Tes native membandingkan scalar JSON numerik
sebagai integer/float, tidak membandingkan array Variant numerik secara langsung.
Delapan oracle lama tetap berjalan; oracle policy ditambahkan sebagai kesembilan.

## Dependensi yang wajib selesai sebelum integrasi penuh

- [ ] Roster enam starter dan seluruh boss yang eligible dari level sebelumnya:
  data, kit, scene/presentasi, upgrade, death/respawn, oracle.
- [ ] Pool terurut boss lalu starter, deduplikasi, source-level pertama; tidak
  memasukkan boss level saat ini. Draft starter pertama acak, boss pertama dari
  level terbaru, berikutnya berbobot source-level; tipe owned termasuk hero mati.
- [ ] Target draft persisten sampai terbeli, reserve harga; jangan mengganti target
  hanya karena kurang gold. Hapus target ketika available kosong atau pembelian sukses.
- [ ] Transaksi red memakai ledger yang sama, reserve pada seluruh belanja non-hero,
  tanpa bonus gold. Hero spawn `RED_BASE_X-60, RED_BASE_Y+30+(count*40-40)`.
- [ ] Build slot acak; jenis archer/cannon/ice/mage berbobot .35/.25/.20/.20.
- [ ] Upgrade tower kills descending stabil; Lv1 path cannon/ice/archer/mage.
- [ ] Upgrade hero termasuk yang mati, kills descending, batas level sumber.
- [ ] Item/inventory/stat effects/forge dan suggestion role+range; kandidat hidup
  dengan slot kosong, kills lalu level descending; reserve dipatuhi.
- [ ] Regen shield Lv4+ termasuk tower Lv6, prioritas kills; castle shield,
  upgrade nexus, eligibility/cost/debit identik sumber.
- [ ] Kontrol hero setiap tick: jalur auto-cast bersama pemain, skill counter
  berdasarkan perubahan active timer; lane ancaman maksimum (tie top/mid/bot),
  minion terdekat secara Euclidean, destination auto; fallback tower terdekat
  dengan offset 60. Jangan mengganti prioritas target dengan urutan x.
- [ ] Integrasi scene/session setelah entity loop tanpa double auto-cast,
  seeded RNG yang bisa diuji (bukan klaim stream identik Python), pause/reset/hasil.
- [ ] Ganti assertion defender lama hanya setelah perilakunya benar-benar diganti;
  pertahankan suite dan invariant wallet/slot/replay.
- [ ] Runtime CI hijau untuk setiap tahap dan uji integrasi penuh sebelum ready PR.

Tidak mengklaim parity item, roster, AI lawan playable, balance, visual atau
perangkat fisik dari tes policy ini.
