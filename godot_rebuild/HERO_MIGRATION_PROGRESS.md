# Checkpoint migrasi — 178/222, BELUM selesai

**178 dari 222 hero target selesai; 44 masih pending.**
Target tetap semua 222 kit, tidak dikurangi. Progres disimpan di branch sesi
`arena/01a0e17d-mystic-arena` / `arena/01a0e217-mystic-arena` (batch 9, merge PR #291 → main c4381c0) /
sesi lanjutan `arena/01a0e2f7-mystic-arena` (batch 10–11, PR draft #292), PR draft dari branch sesi.
**Jangan merge tanpa perintah pengguna.**

**Sinkronisasi GitHub:** batch 7 (Vhalzun 1200G, Krobellus 1500G — level 5) ditambahkan setelah PR #285; batch 5+6 (Ancient Apparition 800G, Nyzrak 850G, Ignis Drachorn 850G) CI hijau 413735 checks (run 36302839552). Manifest dan docs sudah remote.

Daftar tepat **semua 178 selesai dan semua 44 belum selesai**, harga summon,
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
| 8 | Kunkka (900G), Gravewake (1000G), Syrentha (1100G), Thalgryn (1200G) | **170 / 52** | [CI hijau](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36309346449) |
| 9 | Akashari (1200G), Malzareth (1100G), Nyxarath (1000G), Vorenmarr (1300G) | **174 / 48** | merged PR #291 (main c4381c0) |
| 10 | Kenshiro (1300G), Wiro (1300G) — level sumber 9 | **176 / 46** | static lokal 4.720 PASS, menunggu CI |
| 11 | Khazan (1350G), Naraka (2000G) — level sumber 9 selesai | **178 / 44** | static lokal 4.744 PASS, menunggu CI |

Semua suite lama tetap dijalankan. Oracle sumber, source-contract, static
validation (**4.744 checks**, termasuk guard manifest), gdparse, gdlint dan
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
  dikunci CI; **tidak ada fallback native untuk 44 recipe yang belum diport**.
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
  update oracle pembelian sumber kini mencakup seluruh 178 roster (534 baris).
- **L7:** Akashari (Q strike 1.6×/slow, W blink min(dist,150) + AOE 80 dari
  posisi BARU, E scream AOE150, R sonic AOE220 2.3×/slow), Malzareth (Q
  disruption AOE100 di target/x+100, W soul target 1.4×+tetangga 60 0.7×, E
  poison 1.1×/slow, R disillusion AOE200 2.0×/stun90), Nyxarath (Q shadowraze
  **auto-target musuh terdekat dalam 300, mengabaikan hero.target** + cone
  280×50 1.8×/stun45, W necro AOE180 1.7× + hitung kill + rage 480 dari
  **catalog raw** ×1.4 + heal 8%+30/kill, E presence AOE200 stun90/slow0.5/240
  tanpa damage, R requiem AOE220 3.0×/stun120), Vorenmarr (Q bonds target
  1.3×+tetangga 80 0.6×, W power heal 14% saja, E upheaval AOE120 di target
  1.8×/stun60, R golem AOE200 2.2×/stun90). Rage expiry selalu reset damage ke
  katalog raw.
- **L9 (batch 10):** Kenshiro (Q swiftslash target 1.2×, W assault dash
  min(d,90) hanya bila d>1 lalu target 1.4×, E gale AOE150 1.1×, R supremacy
  AOE190 1.8×) dan Wiro (Q windcut target 1.2×, W whirl AOE140 1.1×, E dash
  min(d,100) bila d>1 lalu target 1.1×, R typhoon AOE200 1.8× slow 0.5/90).
  Sumber memanggil `take_damage(dmg, team)` tanpa source/school → hit
  **netral**. Fixture `boss_level_nine_source.json` compact 1 baris, trace
  181 tick (tidak ada timer >90).
  Khazan (Q chained 1.3×, W leap min(d,110) lalu AOE90 1.2× dari posisi BARU
  walau tanpa target, E spin AOE160 1.1×, R vanish AOE210 1.9× heal 8%) dan
  Naraka (Q chaos 1.3×, W shadowstep min(d,120) lalu 1.3×, E hammer AOE180
  1.1× + attack delay max(timer,30), R execution AOE230 int(1.8×), bila
  hp/max(1,max_hp) **< 0.3** sebelum hit → int(×1.6), heal 10%; execute diuji
  level 1/2/15 × hp 2999/3000/3001).
- **Interaksi:** oracle memakai Hero Thorne dan Tower asli, bukan hanya receipt
  HP. Sekolah/source attribution, mitigasi, reflect, shield, dan tower yang
  tidak mempunyai `attack_timer` diuji. Skill tanpa source/school di Python
  tetap **netral**, tidak otomatis memakai sekolah caster.
- **Ekonomi:** 534 pembelian sumber (178 × harga−1/tepat/+1, seluruh roster
  playable termasuk 28 kit recipe khusus + 150 shared). Boss upgrade
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

**44 boss** (level 10–20) mempunyai empat recipe khusus yang belum diport dan
belum memiliki oracle/native test per perilakunya. Metode Q/W/E/R untuk
masing-masing ID tercantum di
[daftar status](HERO_ROSTER_STATUS.md#belum-selesai--44-id-dan-recipe-yang-menjadi-blocker).
Blocker implementasi: sisa 44 recipe (level 10–20) belum diport; batch 7 (run
36308407983) dan batch 8 (run 36309346449) lulus CI Godot 4.7.2 plus validasi
lokal (oracle, static checks, source contract, gdparse/gdlint/gdformat);
batch 9 sudah merge (PR #291); batch 10–11 lulus validasi lokal dan menunggu CI.
Tidak ada klaim 222 playable.

Lanjut berdasarkan level sumber (lihat `hero_skills/_bundle.py` read-only:
registry dispatch, `update_timers` bersama dan metode recipe masing-masing):
1. Level 10: aurethzar (2100G), krognarr (1400G), raz (1400G), vraskhan
   (1400G) — buat `boss_level_ten_skills.gd` / oracle / checks meniru
   `boss_level_nine_*` (fixture compact 1 baris, trace pendek). Level 9 selesai
   (batch 10–11). Tidak ada level sumber 8 untuk recipe khusus.
2. Lanjut level 10 dst sesuai manifest sampai 222. Jangan memasukkan mereka ke
   handler 150 shared-source: source mereka memang berbeda.
3. Per batch: oracle → handler/state/resource → native combat/transactions →
   semua oracle lama + static/parser/lint/format → CI import + run_all → update
   jumlah/manifest/dokumentasi. Jangan melanjutkan batch kalau masih gagal.
4. Test penolakan pending (`ai_recruit` + `shared_no_fallback`) memakai ID yang
   **masih pending** (saat ini aurethzar 2100G); ganti mengikuti manifest tiap
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
> draft dari branch sesi batch 10 (arena/01a0e2f7-mystic-arena, basis main c4381c0).
> Saat ini 178/222 kit native teruji (6 starter + L1×4 + Alchemist + AA, Nyzrak,
> Ignis + L5×2, L6×4, L7×4, L9×4 + 150 ID shared-handler),
> tersisa 44 (level 10–20, 11 level × 4).
> CI hijau Godot 4.7.2 terakhir run 36309346449, static lokal 4744 checks PASS.
> Baca godot_rebuild/AI_CONTRACT.md, SHIELD_CONTRACT.md, HERO_CONTRACT.md,
> HERO_MIGRATION_PROGRESS.md, HERO_ROSTER_STATUS.md dan manifest
> data/ai/hero_migration_status.json. Lanjut level 10 (Aurethzar, Krognarr,
> Raz, Vraskhan) dst sesuai level sumber; lanjut otomatis
> setelah tiap batch lulus. Hanya ubah godot_rebuild/; Python asli read-only.
> Jangan memakai kit generik pengganti: 44 pending mempunyai recipe khusus.
> Pertahankan skill, serangan, cooldown, lifecycle, school/source dan harga
> (upgrade boss 1,6×), dengan source oracle dan tes native tiap perilaku.
> Jalankan semua tes lama, static, parser/lint/format dan CI Godot 4.7.2;
> perbaiki sebelum lanjut. Pending harus tetap ditolak tanpa debit/substitusi.
> Kaizen gratis dan defender scene tetap; tanpa item/forge, AIPlayer penuh,
> rebalance atau art final. Pakai branch sesi Arena yang ditetapkan dan PR draft,
> jangan merge. Update daftar/jumlah tiap batch. Jika konteks habis, simpan
> progres teruji, daftar tepat pending beserta blocker dan pesan lanjutan;
> jangan mengurangi target atau klaim 222 selesai.
