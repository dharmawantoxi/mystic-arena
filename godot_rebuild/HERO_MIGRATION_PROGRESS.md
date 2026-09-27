# Checkpoint migrasi setelah PR #283 — 161/222, BELUM selesai

**157 dari 218 hero yang diminta di sesi ini selesai; 61 masih pending.**
Target tetap semua 222 kit, tidak dikurangi. Progres disimpan di branch sesi
`arena/01a0e134-mystic-arena`, [PR draft #284](https://github.com/dharmawantoxi/mystic-arena/pull/284).
**Jangan merge tanpa perintah pengguna.**

**Batas sinkronisasi GitHub saat checkpoint:** kode teruji sampai `c029d50`
sudah ter-push dan CI hijau. Push commit dokumentasi/manifest `639abeb`
gagal autentikasi (`git`: credentials unavailable; `gh`: HTTP 401). Perubahan
akhir tersimpan lokal/snapshot Arena, tidak hilang. **Reconnect GitHub di
Arena** sebelum push lanjutan atau update PR; tidak memerlukan token/password
di chat. Update judul/body PR terakhir juga gagal, sehingga isi PR remote
mungkin masih menunjukkan hitungan lama. Jangan membuang commit lokal.


Daftar tepat **semua 161 selesai dan semua 61 belum selesai**, harga summon,
level sumber, handler, oracle/native test dan recipe yang menjadi blocker:
[HERO_ROSTER_STATUS.md](HERO_ROSTER_STATUS.md). Manifest mesin:
[`data/ai/hero_migration_status.json`](data/ai/hero_migration_status.json).
Registry: `scripts/data/hero_roster.gd`; transaksi menolak semua pending tanpa
debit/substitusi. Metadata/baseline angka 222 bukan bukti kit playable.

## Batch yang telah lulus

| Batch | Hero selesai dalam batch | Total / sisa | CI Godot 4.7.2 |
|---|---|---|---|
| Baseline PR #283 | Kaizen, Thorne, Grimjaw, Sylara | 4 / 218 | Baseline diterima |
| 1 | Vex, Zephyr | 6 / 216 | [50.666 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36295879312) |
| 2 | Gornak, Morgath, Drakar, Abaddon | 10 / 212 | [95.314 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36296265931) |
| 3 | 150 ID shared-source eksplisit (lihat daftar) | 160 / 62 | [340.054 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36297544475) |
| 4 | Alchemist | **161 / 61** | [**358.305 checks**, c029d50](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36298034563) |

Semua suite lama tetap dijalankan. Oracle sumber, source-contract, static
validation (**4.390 checks**, termasuk guard manifest), gdparse, gdlint dan
gdformat juga lulus. Engine sandbox tidak dapat
diunduh (TLS ke release-assets/CDN gagal), sehingga import dan seluruh tes
engine dijalankan di workflow Godot resmi yang sudah ada. **Bukan klaim engine
lokal, GPU, perangkat fisik atau visual final teruji.**

## Apa yang diport dan dikunci oleh tes

- **Vex (420 G):** Q orb/line, W burst/slow dan moving ring DOT (30 < r ≤ 55),
  E prison 150 tick/stun max/pulsa 10, R AOE 180/2,5×. Magic homing basic.
- **Zephyr (420 G):** Q fixed-origin trap 240 tick, W heal + immunity 180,
  E curse DOT, R Bedlam. Magic homing basic. Burn diproses sebelum timer realm
  habis, sehingga tick aktif terakhir tetap immune.
- **Gornak:** blink berhenti 60px dari target; counterspell AOE/stun; mana void.
  **Morgath:** basic beam/hit instan adalah pengecualian sumber, bukan arrow;
  flux DOT dan clone mengikuti target/timer sumber. **Drakar:** rage reset ke
  damage katalog, bukan level aktif; execute strictly <30%; flag defense tidak
  diberi mitigasi rekaan. **Abaddon:** heal bukan shield baru; dash 80px tetap
  dapat melewati target sebagaimana sumber.
- **150 boss shared-source:** sumber sendiri tidak mempunyai entry recipe untuk
  ID-ID ini dan benar-benar dispatch ke `BossHeroSkills._fallback_cast`.
  Oracle merekam jalur itu **per ID**, menjalankan QWER, exact cooldown/recast,
  melee/homing, upgrade level 1–15, respawn dan pembelian asli. Allowlist eksplisit
  dikunci CI; **tidak ada fallback native untuk 61 recipe yang belum diport**.
- **Alchemist (750 G):** target-centered W100/slow, E rage 360 + heal 15%,
  R200/heal 100 per kill nyata. Uji zero/multiple kill, radius, anti-heal,
  timer expiry saat upgrade, attack, respawn, summon dan upgrade.
- **Interaksi:** oracle memakai Hero Thorne dan Tower asli, bukan hanya receipt
  HP. Sekolah/source attribution, mitigasi, reflect, shield, dan tower yang
  tidak mempunyai `attack_timer` diuji. Skill tanpa source/school di Python
  tetap **netral**, tidak otomatis memakai sekolah caster.
- **Ekonomi:** 483 pembelian sumber (161 × harga−1/tepat/+1). Boss upgrade
  **1,6×** starter: Lv1→2 **480 G**; threshold reserve ±1, hero hidup/mati,
  saldo, registry dan clock diuji. Anti-heal mengikuti HP setter: cap dahulu,
  baru potong kenaikan HP. Resource bersama tidak dimutasi.

## Yang tidak berubah

Hanya `godot_rebuild/` diubah; Python asli read-only. Kaizen gratis kedua tim,
defender scene lama, UI/scene scheduler lama tetap. Tidak ada AIPlayer penuh,
item/forge, desain ulang balance, pembelian AI otomatis atau art final. Marker
hero/proyektil tetap prosedural sederhana. “Playable” di sini adalah kit/domain
native tervalidasi, bukan semua fitur pertandingan Python sudah bermigrasi.

## Sisa dan blocker tepat

**61 boss** mempunyai empat recipe khusus yang belum diport dan belum memiliki
oracle/native test per perilakunya. Metode Q/W/E/R untuk masing-masing ID
tercantum di [daftar status](HERO_ROSTER_STATUS.md#belum-selesai--61-id-dan-recipe-yang-menjadi-blocker).
Blocker implementasi: sisa recipe/verifikasi melebihi konteks kerja aman sesi
ini. Blocker sinkronisasi tambahan: koneksi GitHub perlu direconnect (lihat
catatan awal); kode native teruji sudah remote, manifest akhir masih lokal. Tidak ada klaim 222 playable.

Lanjut berdasarkan level sumber:
1. **Nyzrak + Ancient Apparition** (sisa level 3), kemudian **Ignis Drachorn**
   (sisa level 4). Lihat `hero_skills/_bundle.py` read-only: registry dispatch,
   `update_timers` bersama dan metode recipe masing-masing.
2. AA membutuhkan vortex DOT fixed position, beam geometry serta stun clock.
   Nyzrak membutuhkan beam/radial/curse/heal; audit konsumen `shield_active` /
   `shield_timer` di Hero asli—jangan mengarang shield yang tidak dikonsumsi.
   Ignis membutuhkan cone, sweep dan dua buff dengan expiry/reset berbeda.
3. Berikutnya level 5 dst sesuai manifest. Jangan memasukkan mereka ke handler
   150 shared-source: source mereka memang berbeda.
4. Per batch: oracle → handler/state/resource → native combat/transactions →
   semua oracle lama + static/parser/lint/format → CI import + run_all → update
   jumlah/manifest/dokumentasi. Jangan melanjutkan batch kalau masih gagal.

## Menjalankan validasi

```sh
python godot_rebuild/tests/validate_project.py
python godot_rebuild/tests/check_source_contract.py
# Seluruh oracle lama/new yang berakhiran source_oracle.py:
for t in godot_rebuild/tests/*source_oracle.py; do python "$t" || exit; done
# Oracle kelompok 150 juga dijalankan otomatis oleh validate_project.py:
python godot_rebuild/tests/source_shared_boss_oracle.py
gdparse $(find godot_rebuild -name '*.gd')
gdlint $(find godot_rebuild -name '*.gd')
gdformat --check $(find godot_rebuild -name '*.gd')
# Dengan Godot 4.7.2 tersedia:
godot --headless --path godot_rebuild --editor --import
godot --headless --path godot_rebuild --script res://tests/run_all.gd
```

Parser/lint menggunakan `gdtoolkit==4.5.0`. Oracle `--write` hanya menulis artefak
native; setelah membangkitkan daftar GDScript lakukan gdformat. Jangan mengedit
fixture manual untuk meloloskan hasil yang berbeda dari sumber.

## Pesan siap-salin untuk sesi berikutnya

> Lanjutkan migrasi 222 hero dari snapshot checkpoint Arena terbaru untuk PR
> draft #284 (jangan hanya mengambil main). Reconnect GitHub di Arena dahulu:
> kode teruji c029d50 sudah remote, commit manifest/dokumentasi 639abeb dan
> catatan handoff berikutnya masih lokal karena autentikasi terputus. Saat ini 161/222
> kit native teruji (6 starter + Gornak, Morgath, Drakar, Abaddon, Alchemist +
> 150 ID yang benar-benar memakai shared handler di sumber), tersisa tepat 61.
> Baca godot_rebuild/AI_CONTRACT.md, SHIELD_CONTRACT.md, HERO_CONTRACT.md,
> HERO_MIGRATION_PROGRESS.md, HERO_ROSTER_STATUS.md dan manifest
> data/ai/hero_migration_status.json. Mulai batch Nyzrak + Ancient Apparition,
> lalu Ignis Drachorn dan seluruh sisa sesuai level sumber; lanjut otomatis
> setelah tiap batch lulus, jangan berhenti untuk meminta instruksi berikutnya.
> Hanya ubah godot_rebuild/; Python asli read-only. Jangan memakai kit generik
> pengganti: 61 pending mempunyai recipe khusus. Pertahankan skill, serangan,
> cooldown, lifecycle, school/source dan harga (upgrade boss 1,6×), dengan
> source oracle dan tes native tiap perilaku. Jalankan semua tes lama, static,
> parser/lint/format dan CI Godot 4.7.2; perbaiki sebelum lanjut. Pending harus
> tetap ditolak tanpa debit/substitusi. Kaizen gratis dan defender scene tetap;
> tanpa item/forge, AIPlayer penuh, rebalance atau art final. Pakai branch sesi
> Arena yang ditetapkan dan PR draft, jangan merge. Update daftar/jumlah tiap
> batch. Jika konteks habis, simpan progres teruji, daftar tepat pending beserta
> blocker dan pesan lanjutan; jangan mengurangi target atau klaim 222 selesai.
