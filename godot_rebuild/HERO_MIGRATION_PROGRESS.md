# Migrasi roster setelah PR #283 — WIP, jangan merge

Target tetap **222 kit playable**. Baseline angka tidak dihitung sebagai kit.
Branch sesi: `arena/01a0e134-mystic-arena`. Python sumber read-only.

## Batch 1 — dua starter tersisa

- Baseline teruji sebelum sesi: Kaizen, Thorne, Grimjaw, Sylara (4/222).
- Vex dan Zephyr: implementasi native + oracle sumber + tes native ditulis;
  **menunggu engine/CI, belum dihitung selesai**. Sisa terkonfirmasi: **218**.
- Harga summon keduanya **420 G** (bukan unlock menu).
- Vex: Q orb/line, W burst/slow dan ring bergerak 30 < r <= 55 tiap 20 tick,
  E prison 150 tick/stun max/pulsa 10 tick, R AOE 180/2.5×.
- Zephyr: Q trap snapshot posisi target/240 tick, W heal 40+2/tick dan
  immunity semua damage positif/180 tick, E curse 180 tick/pulsa 20,
  R Bedlam 240 tick/pulsa 15. Basic keduanya magic homing, bukan hit instan.
- Shared helper hanya menyalin BaseSkill dan pemilihan target E yang identik.
  Kit tetap terpisah. Dispatcher menolak ID tanpa handler.
- Oracle mengeksekusi skill asli, pernyataan clock Hero.update asli, loop
  projectile asli, Hero.upgrade/respawn asli. Uji batas, cast kosong/ulang,
  target mati/bergerak, upgrade selama efek, damage realm, respawn.
- Seluruh oracle lama + source contract lulus lokal. Static: 2.154 checks;
  gdparse/gdlint/gdformat lulus. Download engine 4.7.2 di sandbox gagal TLS
  ke release-assets; engine testing dilakukan lewat workflow Godot yang ada.

## Batch berikutnya

Setelah batch starter lulus engine/CI, langsung lanjut boss berdasarkan urutan
level sumber. **216 boss belum diport**, bukan pengganti generic kit. Daftar
ID authoritative ada di `data/ai/recruitment.json` (catalog dengan
`is_boss_hero=true`). Sebelum berhenti sesi, manifest selesai/pending per-ID
akan diperbarui. Tidak ada perubahan AIPlayer scene, item/forge, balance,
Kaizen gratis, defender, maupun art final.
