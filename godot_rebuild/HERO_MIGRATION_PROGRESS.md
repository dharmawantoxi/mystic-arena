# Checkpoint migrasi — 222/222 selesai (menunggu review PR)

**222 dari 222 hero target selesai; 0 pending.** CI Godot 4.7.2 hijau.
Target tetap semua 222 kit, tidak dikurangi. Progres disimpan di branch sesi
`arena/01a0e17d-mystic-arena` / `arena/01a0e217-mystic-arena` (batch 9, merge PR #291 → main c4381c0) /
sesi lanjutan `arena/01a0e2f7-mystic-arena` (batch 10–22, PR draft #292), PR draft dari branch sesi.
**Jangan merge tanpa perintah pengguna.**

**Sinkronisasi GitHub:** batch 7 (Vhalzun 1200G, Krobellus 1500G — level 5) ditambahkan setelah PR #285; batch 5+6 (Ancient Apparition 800G, Nyzrak 850G, Ignis Drachorn 850G) CI hijau 413735 checks (run 36302839552). Manifest dan docs sudah remote.

Daftar tepat **semua 222 selesai (0 belum selesai)**, harga summon,
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
| 10 | Kenshiro (1300G), Wiro (1300G) — level sumber 9 | **176 / 46** | [CI hijau, 632.522 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36322892875) |
| 11 | Khazan (1350G), Naraka (2000G) — level sumber 9 selesai | **178 / 44** | [CI hijau, 632.522 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36322892875) |
| 12 | Krognarr (1400G), Raz (1400G), Vraskhan (1400G), Aurethzar (2100G) — level sumber 10 | **182 / 40** | [CI hijau](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36323731902) |
| 13 | Aeralith (1450G), Aurex (1500G), Nyxareva (1500G), Thalakryon (2200G) — level sumber 11 | **186 / 36** | [CI hijau](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36324671719) |
| 14 | Aurelix (1550G), Aurelyssa (1550G), Vargrath (1600G), Nazulmor (2300G) — level sumber 12 | **190 / 32** | [CI hijau](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36325304211) |
| 15 | Kaeldris (1650G), Pyraklos (1700G), Velmyrth (1700G), Solvarin (2400G) — level sumber 13 | **194 / 28** | [CI hijau](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36325917893) |
| 16 | Azureth (1700G), Luminar (1750G), Solara (1800G), Pyraethis (2500G) — level sumber 14 | **198 / 24** | [CI hijau](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36326753292) |
| 17 | Auroth (1850G), Morvein (1900G), Thorvak (1950G), Yamako (2600G) — level sumber 15 | **202 / 20** | [CI hijau](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36327433044) |
| 18 | Ignirus (2000G), Leoric (2050G), Shirotaka (2100G), Seiryukong (2700G) — level sumber 16 | **206 / 16** | [CI hijau](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36328353836) |
| 19 | Kaelthorn (2150G), Solvanth (2200G), Xyrael (2250G), Nyxareth (2800G) — level sumber 17 | **210 / 12** | [CI hijau](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36328859162) |
| 20 | Cryssalia (2300G), Kaelthar (2350G), Morkhaera (2400G), Aurelion (2900G) — level sumber 18 | **214 / 8** | [CI hijau](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36328859162) |
| 21 | Akahime (2450G), Nyxthrael (2500G), Sylvantheros (2550G), Vaelindra (3000G) — level sumber 19 | **218 / 4** | [CI hijau](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36328859162) |
| 22 | Astraelion (2600G), Morvaenthir (2650G), Thornvaegrim (2700G), Morthraxis (3100G) — level sumber 20 | **222 / 0** | [CI hijau](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36328859162) |

Semua suite lama tetap dijalankan. Oracle sumber, source-contract, static
validation (**5.186 checks**, termasuk guard manifest), gdparse, gdlint dan
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
  dikunci CI; **tidak ada fallback native untuk 20 recipe yang belum diport**.
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
  update oracle pembelian sumber kini mencakup seluruh 222 roster (666 baris).
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
  181 tick (tidak ada timer >90). Visual timer mengikuti dispatcher sumber
  (60/90/60/100 menimpa nilai recipe), dibuktikan CI.
  Khazan (Q chained 1.3×, W leap min(d,110) lalu AOE90 1.2× dari posisi BARU
  walau tanpa target, E spin AOE160 1.1×, R vanish AOE210 1.9× heal 8%) dan
  Naraka (Q chaos 1.3×, W shadowstep min(d,120) lalu 1.3×, E hammer AOE180
  1.1× + attack delay max(timer,30), R execution AOE230 int(1.8×), bila
  hp/max(1,max_hp) **< 0.3** sebelum hit → int(×1.6), heal 10%; execute diuji
  level 1/2/15 × hp 2999/3000/3001).
- **L10 (batch 12):** Krognarr (Q 1.3×, W AOE170 1.1× delay 30, E AOE120
  0.9× heal 8%, R AOE210 1.8× delay 60), Raz (Q 1.2×, W dash min(d,100) lalu
  1.4×, E AOE160 1.1×, R AOE200 1.8× delay 50), Vraskhan (Q dash min(d,90)
  lalu 1.2×, W teleport ke (target.x, target.y−20) lalu 1.3×, E AOE170 1.1×,
  R AOE220 1.8× delay 60), Aurethzar (Q 1.3×, W AOE200 1.1×, E target 1.0×
  slow 0.5/90, R AOE250 1.9× delay 70). Delay = `attack_timer = max(.., n)`
  (Common.stun). Hit netral. Dispatch lewat `boss_recipe_registry.gd` (IDS
  eksplisit per handler; ID pending → null, tanpa substitusi).
- **L11 (batch 13):** Aeralith (Q 1.2×, W AOE190 1.1×, E AOE170 1.1× slow
  0.5/90, R AOE240 1.8×), Aurex (Q 1.3×, W target 1.4×, E AOE130 0.9× heal
  10%, R AOE210 1.8× delay 60), Nyxareva (Q 1.2×, W target 1.4× slow 0.5/90,
  E AOE170 1.1×, R AOE220 1.8× delay 60), Thalakryon (Q 1.3×, W AOE150 0.8×
  heal 12%, E AOE190 1.2× delay 40, R AOE260 2.0× delay 75 heal 10%).
  Catatan: gdparse tidak mendeteksi jumlah argumen salah; CI Godot yang
  menangkap (signature `_radial` sempat tidak ikut diperbarui).
- **L12 (batch 14):** Aurelix (Q 1.2×, W heal 12% saja, E AOE170 1.1× delay
  40, R AOE240 1.8× slow 0.5/90), Aurelyssa (Q AOE140 1.1×, W AOE160 1.2×, E
  dash min(d,100) bila ada target lalu AOE120 1.1× dari posisi BARU, R AOE220
  1.8× delay 60), Vargrath (Q 1.2×, W dash min(d,110) lalu AOE100 1.2× dari
  posisi BARU, E AOE170 1.1×, R AOE230 1.8× delay 60), Nazulmor (Q AOE190
  1.1×, W AOE150 0.8× heal 12%, E AOE200 1.2× delay 40, R AOE270 2.0× delay
  75 heal 10%).
- **L13 (batch 15):** Kaeldris (Q 1.2×, W dash min(d,110) lalu 1.3×, E
  AOE170 1.1×, R AOE220 1.8× delay 60), Pyraklos (Q 1.3×, W AOE170 1.1×, E
  AOE130 0.7× heal 12%, R AOE230 1.8× delay 60), Velmyrth (Q 1.2× slow 0.5/90,
  W teleport (target.x, target.y−20) lalu 1.3×, E AOE170 1.1×, R coup AOE220
  int(1.8×), hp/max(1,max_hp) **< 0.3** pre-hit → int(×1.6), tanpa heal;
  execute diuji level 1/2/15 × hp 2999/3000/3001), Solvarin (Q 1.3×, W AOE180
  1.2× delay 40, E AOE200 0.9× slow 0.4/90, R AOE280 2.0× delay 75 heal 12%).
- **L14 (batch 16):** Azureth (Q 1.2×, W AOE170 1.15×, E AOE200 1.0× slow
  0.5/100, R AOE240 1.9× delay 65), Luminar (Q 1.2×, W AOE190 1.15× delay 45,
  E AOE205 1.0×, R AOE280 1.95× heal 15%), Solara (Q 1.25×, W AOE185 1.15×, E
  AOE195 0.95× heal 10%, R AOE240 1.9× delay 70), Pyraethis (Q icarus dive
  target int(1.3×), hp/max(1,max_hp) **< 0.3** pre-hit → int(×1.5), diuji
  level 1/2/15 × hp 2999/3000/3001; W AOE200 1.2×, E AOE220 1.05× slow
  0.35/90, R AOE300 2.1× delay 80 heal 12%).
- **L15 (batch 17):** Auroth (Q 1.25×, W AOE185 1.1× heal 10%, E AOE195
  1.0× slow 0.4/90, R AOE240 1.9× delay 70), Morvein (Q puncture int(1.3×),
  <30% → int(×1.5); W AOE190 1.2×, E AOE205 1.05×, R AOE250 1.95× heal 12%),
  Thorvak (Q 1.2× slow 0.4/90, W AOE195 1.15×, E AOE200 1.0×, R AOE250 1.9×
  delay 70 heal 10%), Yamako (Q deep forest int(1.3×), <30% → int(×1.4); W
  AOE205 1.15×, E AOE220 1.0× delay 50, R AOE300 2.1× delay 80 heal 12%).
  Execute kedua Q diuji level 1/2/15 × hp 2999/3000/3001.
- **L16–L20 (batch 18–22):** pola sama (Q target/dash/teleport, W/E/R AOE
  dengan delay/slow/heal sumber). Execute Q (<30% pre-hit, int lalu bonus)
  diuji level 1/2/15 × hp 2999/3000/3001 untuk Shirotaka ×1.5 (teleport y−20),
  Seiryukong ×1.4, Xyrael ×1.5 (teleport), Aurelion ×1.4, Nyxthrael ×1.5,
  Vaelindra ×1.4, Astraelion ×1.5, Morthraxis ×1.4. Dash: Leoric 100,
  Kaelthorn 110, Kaelthar 110. Heal R: Leoric 20%, Seiryukong/Nyxareth/
  Aurelion/Vaelindra/Morkhaera 12%, Morthraxis 15% (+W 8%). Nilai persis tiap
  hero ada di `boss_level_{sixteen..twenty}_skills.gd` dan oracle masing-masing.
  Nyxareth: `active_skill` visual sumber ditimpa dispatcher, jadi tidak diport.
- **Interaksi:** oracle memakai Hero Thorne dan Tower asli, bukan hanya receipt
  HP. Sekolah/source attribution, mitigasi, reflect, shield, dan tower yang
  tidak mempunyai `attack_timer` diuji. Skill tanpa source/school di Python
  tetap **netral**, tidak otomatis memakai sekolah caster.
- **Ekonomi:** 666 pembelian sumber (222 × harga−1/tepat/+1, seluruh roster
  playable termasuk 72 kit recipe khusus + 150 shared). Boss upgrade
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

**0 pending.** Semua 222 kit native mempunyai source oracle + tes native dan
lulus CI Godot 4.7.2 ([run 36328859162](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36328859162)) serta static lokal 5551 PASS.
Batch 10–11 memperbaiki 3 bug tes batch 9 (parse error `skill_key :=`, dana
roster L7, dana tes pending). Level 16–20 memakai `boss_level_{sixteen..twenty}_*`
dan handler di `HANDLERS` (`boss_recipe_registry.gd`); `minion_battle.gd` tetap
1000 baris (batas gdlint).

Tes penolakan setelah 0 pending: karena draft tidak lagi bisa memilih kit yang
hilang, `ai_recruit_checks._guards` kini menguji penolakan adapter lewat tabrakan
registry ID (`transaction_error == "capacity"`, draft/reserve tetap, tanpa debit;
didanai 4000G), harga palsu `_buy_ai_hero("astraelion", 400)` tetap ditolak
`kit`, dan `source_shared_boss_checks._no_fallback` memakai ID tak dikenal
`unported_probe` (tidak ada substitusi generik).

Yang tersisa di luar cakupan migrasi kit: AIPlayer penuh, item/forge, art final,
review/merge PR #292 atas perintah pengguna.

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

> Migrasi 222/222 kit hero native selesai di branch arena/01a0e2f7-mystic-arena
> (PR draft #292, basis main c4381c0), CI hijau Godot 4.7.2 run 36328859162, static
> lokal 5551 PASS, 0 pending. Baca HERO_MIGRATION_PROGRESS.md,
> HERO_ROSTER_STATUS.md dan data/ai/hero_migration_status.json. Jangan merge
> tanpa perintah pengguna. Hanya ubah godot_rebuild/; Python asli read-only.
> Pekerjaan berikutnya (di luar migrasi kit): review PR, AIPlayer penuh,
> item/forge atau art — hanya atas permintaan pengguna.
