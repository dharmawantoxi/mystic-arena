# Batch 8 — Vhalzun, level 5 selesai

**166 implementasi / 56 pending**; target tetap 222. Batch 7 Krobellus teruji:
commit `64633eb`, CI [36304115611](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36304115611),
**427984 native checks**, Godot 4.7.2; static 4516. Sudah push, PR draft
[#287](https://github.com/dharmawantoxi/mystic-arena/pull/287), jangan merge.

Batch 8 implementasi selesai; validasi lokal PASS: static 4555, source-contract,
semua *_oracle.py, gdparse/gdlint/gdformat 4.5.0. CI baru menunggu.
Vhalzun 1200G: Q130/1,5×; W150/1×/stun max60; E selected 1,8× tanpa heal
atau execute threshold; R150/1,4× + heal18%, tanpa shield/immunity/DOT.
Visual final **60/80/60/100** (override Vhalzun, bukan default W90).
Oracle eksekusi sumber, radius batas, stun max, selection, trace clocks,
upgrade/retarget/death, heal+anti-heal, no defense, basic homing, respawn,
lifecycle, summon±1, boss upgrade480G, Hero-v-Hero/Tower attribution.
Handler tersendiri; tidak memperluas allowlist 150 shared-source.

Sisa tepat di manifest dan HERO_ROSTER_STATUS.md. Level berikutnya **6**:
Gravewake 1000G, Kunkka900G, Syrentha1100G, Thalgryn1200G. Kunkka tetap ID
penolakan pending; bila kelak selesai, pindahkan sentinel ke pending murah
nyata dengan assert status manifest, jangan menguji penolakan kit playable.

---

# Checkpoint sesi PR lanjutan — batch 7 Krobellus

**165 implementasi playable / 57 pending; target tetap 222.**
Krobellus selesai implementasi dan oracle; validasi lokal PASS (4516 static,
source-contract, semua oracle termasuk shared 150, gdparse/gdlint/gdformat
4.5.0). CI engine branch ini menunggu.
Baseline merge `50b7c07` tetap 164 teruji, run [36302839552](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36302839552).
Branch aktif `arena/01a0e1cb-mystic-arena`; PR draft akan dibuat, jangan merge.

Batch 7: Q150/1,5×; W120/1×/attack timer max75; E selected target 1,3× +
heal 0,5× skill; R200/2,5× + heal 15%. Semua skill netral tanpa source,
bukan atribusi magic caster. Cooldown 220/240/420/900, visual final
60/90/60/100 (trigger cooldown menimpa timer visual recipe). Tidak ada ghost
DOT atau silence state tambahan. Basic magic homing; Lv1→2 480G.

Oracle + native: radius batas, target retention/reselection, dead/friendly
filter, stun max, traces move/upgrade/retarget/death, cooldown recast tepat,
heal cap sebelum anti-heal Lv1/2/15, attack, respawn, lifecycle, roster,
purchase ±1 dan upgrade reserve ±1. Tambah coverage pembelian dan
Hero-v-Hero/Tower untuk AA/Nyzrak/Ignis yang terlewat oracle lintas-hero lama.

**Koreksi handoff lama:** manifest sumber berbeda dari daftar informal. Vhorethzir
sudah shared-source playable. Naraka 2000G, Aurethzar 2100G, dst: jangan
mengganti harga dengan angka di pesan lama. Daftar tepat selesai/pending dan
harga sekarang di [HERO_ROSTER_STATUS.md](HERO_ROSTER_STATUS.md).
Kunkka 900G tetap pending dan tetap ID tes penolakan. Level 5 masih Vhalzun
1200G; level 6 Gravewake 1000G/Kunkka 900G. Lanjut urutan level sumber.

Unduh Godot lokal 4.7.2 masih gagal TLS release-assets; engine dijalankan CI
resmi, bukan klaim runtime lokal. Python read-only, hanya godot_rebuild berubah.

---

## Arsip checkpoint merge sebelumnya (angka di bawah historis)

# Checkpoint migrasi setelah PR #283 — 164/222, BELUM selesai

**164 dari 222 hero target selesai; 58 masih pending.**
Target tetap semua 222 kit, tidak dikurangi. Progres disimpan di branch sesi
`arena/01a0e17d-mystic-arena`, PR draft #285 dari branch ini.
**Jangan merge tanpa perintah pengguna.**

**Sinkronisasi GitHub:** batch 5+6 (Ancient Apparition 800G, Nyzrak 850G, Ignis Drachorn 850G) sudah ter-push ke `arena/01a0e17d-mystic-arena` dan CI hijau 413735 checks (run 36302839552). Manifest dan docs sudah remote.

Daftar tepat **semua 164 selesai dan semua 58 belum selesai**, harga summon,
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

**58 boss** mempunyai empat recipe khusus yang belum diport dan belum memiliki
oracle/native test per perilakunya. Metode Q/W/E/R untuk masing-masing ID
tercantum di [daftar status](HERO_ROSTER_STATUS.md#belum-selesai--58-id-dan-recipe-yang-menjadi-blocker).
Blocker implementasi: sisa 58 recipe (level 5 dst) belum diport; batch 5+6 sudah lulus CI. Tidak ada klaim 222 playable.

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
