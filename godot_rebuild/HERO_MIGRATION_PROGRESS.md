# Checkpoint migrasi — 170/222, BELUM selesai

**170 dari 222 hero target selesai; 52 masih pending.**
Target tetap semua 222 kit, tidak dikurangi. Progres disimpan di branch sesi
`arena/01a0e17d-mystic-arena` / sesi lanjutan `arena/01a0e217-mystic-arena`, PR draft dari branch sesi.
**Jangan merge tanpa perintah pengguna.**

**Sinkronisasi GitHub:** batch 7 (Vhalzun 1200G, Krobellus 1500G — level 5) ditambahkan setelah PR #285; batch 5+6 (Ancient Apparition 800G, Nyzrak 850G, Ignis Drachorn 850G) CI hijau 413735 checks (run 36302839552). Manifest dan docs sudah remote.

Daftar tepat **semua 170 selesai dan semua 52 belum selesai**, harga summon,
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
| 4 | Alchemist | 161 / 61 | [358.305 checks, c029d50](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36298034563) |
| 5 | Ancient Apparition (800G), Nyzrak (850G) | 163 / 59 | [lint fixed, then 413735](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36302839552) |
| 6 | Ignis Drachorn (850G) | **164 / 58** | [413735 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36302839552) |
| 7 | Vhalzun (1200G), Krobellus (1500G) | **166 / 56** | [CI hijau](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36308407983) |
| 8 | Kunkka (900G), Gravewake (1000G), Syrentha (1100G), Thalgryn (1200G) | **170 / 52** | menunggu CI |

Semua suite lama tetap dijalankan. Oracle sumber, source-contract, static
validation (**4.476 checks**, termasuk guard manifest), gdparse, gdlint dan
gdformat juga lulus (413735 native checks di Godot 4.7.2). Engine sandbox tidak dapat
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
  dikunci CI; **tidak ada fallback native untuk 52 recipe yang belum diport**.
- **Alchemist (750 G):** target-centered W100/slow, E rage 360 + heal 15%,
  R200/heal 100 per kill nyata. Uji zero/multiple kill, radius, anti-heal,
  timer expiry saat upgrade, attack, respawn, summon dan upgrade.
- **L3–L4:** Ancient Apparition (vortex DOT 20-tick fixed origin, beam slow,
  stun, shield tanpa mitigasi—quirk sumber), Nyzrak (beam/radial/curse/shield
  quirk sama), Ignis Drachorn (cone 250×60 melebar, tail 360, dragon blood
  buff 480 **tidak** reset damage—quirk sumber, elder form 600 reset damage).
- **L5:** Vhalzun (AOE 130/150/target 1.8×/AOE 150 heal 18%, visual 60/80/60/100)
  dan Krobellus (AOE 150×1.5, AOE 120×1.0 stun 75, siphon target×1.3 heal
  0.5× skill, crypt AOE 200×2.5 heal 15%).
- **L6:** Kunkka (cone 250×70 1.8×, X-mark AOE 120 target 1.5× stun 60, ghost
  cone 300×80 2.2× stun 90 heal 15%, torrent AOE 200 3.0× stun 120 heal 20%),
  Gravewake (cone 200×60 slow, AOE target, shell defense 300 **tanpa**
  mitigasi—quirk, ravage AOE slow heal), Syrentha (cone slow, song AOE
  stun 120 slow 0.7/240, mirror rage 360 dari **catalog raw** ×1.4, siren
  AOE 220 stun 150) dan Thalgryn (cone 250×50 + surge min(dist,200) dari posisi
  pre-surge, adaptive target 2.0× + tetangga 60 0.7×, morph rage 300 ×1.35,
  replicate AOE slow 0.4/180). Rage expiry selalu reset damage ke katalog raw;
  update oracle pembelian sumber kini mencakup seluruh 170 roster (510 baris).
- **Interaksi:** oracle memakai Hero Thorne dan Tower asli, bukan hanya receipt
  HP. Sekolah/source attribution, mitigasi, reflect, shield, dan tower yang
  tidak mempunyai `attack_timer` diuji. Skill tanpa source/school di Python
  tetap **netral**, tidak otomatis memakai sekolah caster.
- **Ekonomi:** 510 pembelian sumber (170 × harga−1/tepat/+1, seluruh roster
  playable termasuk 20 kit recipe khusus + 150 shared). Boss upgrade
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

**52 boss** mempunyai empat recipe khusus yang belum diport dan belum memiliki
oracle/native test per perilakunya. Metode Q/W/E/R untuk masing-masing ID
tercantum di [daftar status](HERO_ROSTER_STATUS.md#belum-selesai--52-id-dan-recipe-yang-menjadi-blocker).
Blocker implementasi: sisa 52 recipe (level 7 dst) belum diport; batch 7 lulus CI
(Godot 4.7.2, run 36308407983), batch 8 lulus validasi lokal (oracle, static
checks, source contract, gdparse/gdlint/gdformat) dan menunggu CI. Tidak ada
klaim 222 playable.

Lanjut berdasarkan level sumber (lihat `hero_skills/_bundle.py` read-only:
registry dispatch, `update_timers` bersama dan metode recipe masing-masing):
1. Level 7: akashari, malzareth, nyxarath, vorenmarr (recipe `_cast_*_akashari_*`
   dst; nyxarath memakai rage + `get_all_hero_types` base damage).
2. Lanjut level 8 dst sesuai manifest sampai 222. Jangan memasukkan mereka ke
   handler 150 shared-source: source mereka memang berbeda.
3. Per batch: oracle → handler/state/resource → native combat/transactions →
   semua oracle lama + static/parser/lint/format → CI import + run_all → update
   jumlah/manifest/dokumentasi. Jangan melanjutkan batch kalau masih gagal.
4. Test penolakan pending (`ai_recruit` + `shared_no_fallback`) memakai ID yang
   **masih pending** (saat ini nyxarath 1000G); ganti mengikuti manifest tiap
   kali satu batch membuat ID tersebut playable.

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
> draft #285 (branch arena/01a0e17d-mystic-arena, jangan hanya main). Saat ini 164/222
> kit native teruji (6 starter + Gornak, Morgath, Drakar, Abaddon, Alchemist +
> Ancient Apparition, Nyzrak, Ignis Drachorn + 150 ID shared-handler), tersisa 58.
> CI hijau 413735 checks (Godot 4.7.2) pada run 36302839552, static 4476 checks PASS.
> Baca godot_rebuild/AI_CONTRACT.md, SHIELD_CONTRACT.md, HERO_CONTRACT.md,
> HERO_MIGRATION_PROGRESS.md, HERO_ROSTER_STATUS.md dan manifest
> data/ai/hero_migration_status.json. Lanjut batch level 5 dst (Krobellus, Kunkka,
> Nyxarath, Vhorethzir, Naraka, dst) sesuai level sumber; lanjut otomatis
> setelah tiap batch lulus. Hanya ubah godot_rebuild/; Python asli read-only.
> Jangan memakai kit generik pengganti: 58 pending mempunyai recipe khusus.
> Pertahankan skill, serangan, cooldown, lifecycle, school/source dan harga
> (upgrade boss 1,6×), dengan source oracle dan tes native tiap perilaku.
> Jalankan semua tes lama, static, parser/lint/format dan CI Godot 4.7.2;
> perbaiki sebelum lanjut. Pending harus tetap ditolak tanpa debit/substitusi.
> Kaizen gratis dan defender scene tetap; tanpa item/forge, AIPlayer penuh,
> rebalance atau art final. Pakai branch sesi Arena yang ditetapkan dan PR draft,
> jangan merge. Update daftar/jumlah tiap batch. Jika konteks habis, simpan
> progres teruji, daftar tepat pending beserta blocker dan pesan lanjutan;
> jangan mengurangi target atau klaim 222 selesai.
