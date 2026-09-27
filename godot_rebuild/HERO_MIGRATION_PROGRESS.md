# Migrasi roster setelah PR #283 — WIP, jangan merge

Target tetap **222 kit playable**. Baseline angka tidak dihitung sebagai kit.
Branch sesi: `arena/01a0e134-mystic-arena`. Python sumber read-only.

## Batch 1 — dua starter tersisa

- Baseline teruji sebelum sesi: Kaizen, Thorne, Grimjaw, Sylara (4/222).
- Vex dan Zephyr: selesai dan lulus CI Godot 4.7.2 pada commit `63778c4`.
  **6/222 selesai, 216 boss tersisa**. CI [36295879312](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36295879312): **50.666 native checks** (seluruh suite lama ikut).
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

Batch starter lulus; langsung lanjut Gornak, Morgath, Drakar, Abaddon
(boss level sumber 1). **216 boss belum diport**, bukan pengganti generic kit. Daftar
ID authoritative ada di `data/ai/recruitment.json` (catalog dengan
`is_boss_hero=true`). Sebelum berhenti sesi, manifest selesai/pending per-ID
akan diperbarui. Tidak ada perubahan AIPlayer scene, item/forge, balance,
Kaizen gratis, defender, maupun art final.

## Batch 2 — boss level sumber 1 (menunggu CI)

Gornak, Morgath, Drakar, Abaddon: implementasi + oracle + tes native ditulis.
Belum menambah hitungan selesai sebelum engine lulus. Port memakai recipe
`BossHeroSkills._SKILL_REGISTRY` asli, bukan `_fallback_cast` untuk empat ID ini.
Gate boss max(skill_range, 140), tanpa slack starter; visual duration final
berasal dari trigger cooldown, bukan nilai sementara di recipe. Morgath memakai
basic beam/hit langsung sesuai pengecualian `_do_attack`, bukan homing arrow.
Oracle menguji seluruh QWER, target tie/stale, radius, teleport overshoot,
DOT/clone retarget/dead target, heal, rage reset saat upgrade, execute <30%,
flag defense yang tidak mengurangi damage, respawn dan harga sumber. Static
2.216 checks + seluruh oracle lama/new dan parser/lint/format lulus lokal.

### Batch 2 lulus

Commit `3efc68e`, [CI 36296265931](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36296265931):
**95.314 native checks**, **2.234 static checks**. Keempat boss level 1 selesai;
**10/222 kit, sisa 212**. Tambahan interaksi nyata source HP setter anti-heal
(cap dahulu baru potong gain), serta burn sebelum expiry Shadow Realm.

## Batch 3 — 150 boss yang benar-benar berbagi jalur sumber (belum selesai)

Audit registry sumber: 66 boss mempunyai recipe khusus; 150 lainnya memang
menjalankan `BossHeroSkills._fallback_cast` asli. Port berikutnya akan memakai
allowlist eksplisit yang dibuktikan dari registry source, bukan fallback untuk
semua boss native. Setiap ID harus punya oracle QWER/attack/cooldown/lifecycle,
level dan harga serta tes native sebelum dianggap playable. 62 boss dengan
recipe khusus yang belum diport tetap ditolak. Hitungan selesai tetap 10 sampai
batch ini lulus CI.
