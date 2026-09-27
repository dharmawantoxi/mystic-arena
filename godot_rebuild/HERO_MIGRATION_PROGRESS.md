# Checkpoint migrasi setelah PR #284 — 163/222, BELUM selesai

**159 dari 220 hero yang diminta di sesi-sesi ini selesai; 59 masih pending.**
Target tetap semua 222 kit, tidak dikurangi. Progres disimpan di branch sesi
`arena/01a0e179-mystic-arena` dengan PR draft sesi ini.
**Jangan merge tanpa perintah pengguna.**

**Sinkronisasi GitHub:** PR #284 sudah ter-merge sebagai checkpoint `cf936ac`.
Sesi ini memakai branch baru `arena/01a0e179-mystic-arena`; setiap batch teruji
di-commit dan di-push ke branch itu, lalu CI Godot 4.7.2 menjadi satu-satunya
bukti runtime. Unduhan engine ke `release-assets.githubusercontent.com` dan
`downloads.tuxfamily.org` diblokir TLS di sandbox ini, sama seperti sesi
sebelumnya — jadi **tidak ada klaim engine lokal**; CI yang menjalankan import
dan `run_all.gd`.


Daftar tepat **semua 163 selesai dan semua 59 belum selesai**, harga summon,
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
| 5 (sesi ini) | Ancient Apparition, Nyzrak | **163 / 59** | menunggu CI branch sesi |

Semua suite lama tetap dijalankan. Oracle sumber, source-contract, static
validation (**4.445 checks**, termasuk guard manifest dan generator tabel roster),
gdparse, gdlint dan gdformat juga lulus. Engine sandbox tidak dapat
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
  dikunci CI; **tidak ada fallback native untuk 59 recipe yang belum diport**.
- **Alchemist (750 G):** target-centered W100/slow, E rage 360 + heal 15%,
  R200/heal 100 per kill nyata. Uji zero/multiple kill, radius, anti-heal,
  timer expiry saat upgrade, attack, respawn, summon dan upgrade.
- **Ancient Apparition (800 G):** Q vortex fixed-position 180 tick + burst 0,6×;
  DOT `update_timers` asli 0,3×/slow 0,5 per 60 tick selama 180 tick lalu berhenti
  (8 hit) dan di-rearm saat Q di-cast ulang. W beam 400/30 1,5× slow 0,6/180,
  E single 2,5× + `attack_timer` max 90, R beam 500/60 3,0× slow 0,7/240.
  Arah W/R yang kembali dini **tidak** menimpa `w_dir`/`r_dir` sebelumnya.
- **Nyzrak (850 G):** Q beam 240/26 1,2× slow 0,4/120 dariAim nol (`hypot or 1`)
  tidak mengenai siapa pun; W burst r80 di target 1,0× slow 0,3/60; E single
  1,1× + `attack_timer` max 90 + slow 0,7/180; R nova r200 2,0× slow 0,5/180 +
  heal `int(max_hp*0,15)` mengikuti HP setter. **Audit konsumen:** `shield_active`
  dan `shield_timer` tidak pernah dibaca Hero di `_entity.py` — tidak ada pool
  shield, absorb, atau mitigasi; flag hanya direkam dan tes mengunci 100 damage
  penuh untuk physical **dan** magic. Tidak ada shield karangan.
  Durasi visual Nyzrak memakai override sumber 50/50/70/90, AA default 60/90/60/100.
- **Interaksi:** oracle memakai Hero Thorne dan Tower asli, bukan hanya receipt
  HP. Sekolah/source attribution, mitigasi, reflect, shield, dan tower yang
  tidak mempunyai `attack_timer` diuji. Skill tanpa source/school di Python
  tetap **netral**, tidak otomatis memakai sekolah caster.
- **Ekonomi:** 489 pembelian sumber (163 × harga−1/tepat/+1). Boss upgrade
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

**59 boss** mempunyai empat recipe khusus yang belum diport dan belum memiliki
oracle/native test per perilakunya. Metode Q/W/E/R untuk masing-masing ID
tercantum di [daftar status](HERO_ROSTER_STATUS.md#belum-selesai--59-id-dan-recipe-yang-menjadi-blocker).
Blocker implementasi: sisa recipe/verifikasi melebihi konteks kerja aman satu
sesi. **Tidak ada klaim 222 playable.**

Lanjut berdasarkan level sumber:
1. **Ignis Drachorn** (sisa level 4), lalu level 5: Krobellus, Vhalzun.
   Lihat `hero_skills/_bundle.py` read-only: registry dispatch, `update_timers`
   bersama dan metode recipe masing-masing.
2. Ignis membutuhkan cone, sweep dan dua buff (`dragon_form_active` reset damage
   ke katalog, `dragon_blood_active`) dengan expiry/reset berbeda.
3. Level 6 (Gravewake, Kunkka, Syrentha, Thalgryn), 7 (Akashari, Malzareth,
   Nyxarath, Vorenmarr), lalu 9–20 sesuai manifest. **Audit AST sudah dilakukan:
   61 recipe awal semuanya berbeda satu sama lain**, jadi tidak ada satu pun
   yang boleh memakai handler bersama. Bentuk geometri (beam/radial/cone/
   single) boleh dipakai ulang hanya sebagai helper; angka, ordering, slow,
   stun, heal, buff dan efek samping tiap ID tetap eksplisit.
4. Untuk setiap ID: cek konsumen semua atribut yang ditulis recipe di kelas
   `Hero` asli sebelum memberi efek apa pun. Flag yang tidak dikonsumsi hanya
   direkam, tidak dikarang jadi shield/stun/mitigasi.
4. Per batch: oracle → handler/state/resource → native combat/transactions →
   semua oracle lama + static/parser/lint/format → CI import + run_all → update
   jumlah/manifest/dokumentasi. Jangan melanjutkan batch kalau masih gagal.

## Menjalankan validasi

```sh
python godot_rebuild/tests/validate_project.py
python godot_rebuild/tests/check_source_contract.py
# Seluruh oracle lama/new yang berakhiran source_oracle.py:
for t in godot_rebuild/tests/*source_oracle.py; do python "$t" || exit; done
# Oracle kelompok 150 dan level-3 juga dijalankan otomatis oleh validate_project.py:
python godot_rebuild/tests/source_shared_boss_oracle.py
python godot_rebuild/tests/level_three_source_oracle.py
# Tabel roster di HERO_ROSTER_STATUS.md dibangkitkan dari manifest:
python godot_rebuild/tests/roster_doc.py
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

> Lanjutkan migrasi kit hero dari checkpoint PR #284 (`cf936ac`) pada branch
> sesi `arena/01a0e179-mystic-arena`; jangan mengambil main saja. Status saat
> checkpoint ini: **163/222 kit native teruji** (6 starter + Gornak, Morgath,
> Drakar, Abaddon, Alchemist, Ancient Apparition, Nyzrak + 150 ID yang benar-benar
> memakai shared handler di sumber), tersisa tepat **59** dengan recipe khusus.
> Baca AI_CONTRACT.md, SHIELD_CONTRACT.md, HERO_CONTRACT.md,
> HERO_MIGRATION_PROGRESS.md, HERO_ROSTER_STATUS.md dan manifest
> data/ai/hero_migration_status.json.
> **Batch berikutnya: Ignis Drachorn (sisa level 4), lalu Krobellus + Vhalzun
> (level 5),** lalu 6, 7, dan 9–20 menurut level sumber di manifest. Lanjut
> otomatis setelah tiap batch lulus; jangan berhenti untuk meminta instruksi.
> Audit AST: 61 recipe awal semuanya berbeda satu sama lain — tidak ada satu pun
> yang boleh memakai handler bersama; hanya bentuk geometri yang boleh
> dipakai ulang sebagai helper, angka/ordering/efek eksplisit per ID.
> Untuk setiap ID, audit konsumen tiap atribut yang ditulis recipe di kelas
> `Hero` asli sebelum memberi efek: flag yang tidak dibaca (mis. `shield_active`
> Nyzrak, `w_dir`/`r_dir` AA) hanya direkam, tidak dikarang jadi shield/mitigasi.
> Hanya ubah godot_rebuild/; Python asli read-only. Setiap batch perlu source
> oracle yang mengeksekusi metode asli + tes native + pembaruan
> `tests/roster_doc.py --write` (tabel roster dibangkitkan, jangan diedit manual).
> Jalankan semua oracle lama, validate_project.py, check_source_contract.py,
> gdparse/gdlint/gdformat, dan CI Godot 4.7.2; perbaiki kegagalan sebelum lanjut.
> Pending harus tetap ditolak tanpa debit/substitusi. Upgrade boss tetap 1,6×
> (Lv1→2 480 G). Kaizen gratis dan defender scene tetap; tanpa item/forge,
> AIPlayer penuh, rebalance atau art final. Jangan merge tanpa perintah eksplisit.
> Jika konteks hampir habis: selesaikan validasi yang sedang berjalan, jangan
> daftarkan kit belum selesai sebagai playable, commit+push, update PR draft,
> dan tuliskan daftar persis pending + blocker + hasil tes/CI + langkah berikut.
