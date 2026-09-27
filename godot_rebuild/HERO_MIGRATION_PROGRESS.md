# Progress migrasi kit hero Godot — checkpoint sesi Arena

## Status saat ini

**Target tetap 222. Status terverifikasi pada manifest: 164 playable, 58 pending.**
Tidak ada pengurangan target dan tidak ada klaim selesai 222. Baseline branch sesi berasal dari `50b7c07` (merge PR #285 ke `main`). Semua perubahan sesi ini hanya di `godot_rebuild/`; Python asli tetap read-only.

- Branch kerja yang diwajibkan Arena: `arena/01a0e1d3-mystic-arena`.
- CI baseline sebelum perubahan sesi: [Godot 4.7.2, 413735 native checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36302839552), static 4.476 PASS.
- **Batch WIP Krobellus (1500G): belum playable dan tetap ditolak.** Oracle eksekusi sumber, fixture, handler khusus serta tes native langsung sudah ditambahkan. Handler belum dimasukkan ke `hero_roster.gd`/dispatch/manifest playable karena native Godot runtime belum dijalankan pada batch ini. Perlu jalankan CI Godot 4.7.2, perbaiki semua temuan, baru daftarkan kit dan ubah hitungan. Belum ada push/CI baru untuk WIP ini.
- Validasi lokal sesudah perbaikan: `validate_project.py` (**4508 static checks**), `check_source_contract.py`, seluruh `*source_oracle.py` termasuk source-shared (150 ID), serta `gdparse`, `gdlint`, `gdformat --check` dengan `gdtoolkit==4.5.0` semuanya PASS. Dua temuan CI sudah diperbaiki sebelum batch dapat didaftarkan: [36304792506](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36304792506) gagal compile karena tipe `before` belum eksplisit (ditetapkan `int`); [36305416457](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36305416457) compile/import lulus tetapi native runner gagal 212 dari 431433 assertions. Kegagalan Krobellus menunjukkan durasi visual recipe kembali memakai default dispatcher 60/90/60/100 (bukan timer lokal recipe), serta transaksi harus dites melalui `prototype_battle` bukan `minion_battle`. Keduanya sudah disesuaikan; seluruh validasi lokal diulang pass dan CI perlu dijalankan ulang. **Krobellus tetap pending/tidak di-roster.** Engine lokal tidak tersedia.

Daftar mesin dan status resmi tetap `data/ai/hero_migration_status.json`; daftar manusia dan recipe tepat ada di [HERO_ROSTER_STATUS.md](HERO_ROSTER_STATUS.md). Karena Krobellus belum terdaftar, status tepat masih **164/222 dan 58 pending**.

## Batch selesai sebelum sesi ini

| Batch | Hasil | Total / sisa | Hasil CI Godot 4.7.2 |
|---|---|---:|---|
| Baseline PR #283 | Kaizen, Thorne, Grimjaw, Sylara | 4 / 218 | Baseline diterima |
| 1 | Vex, Zephyr | 6 / 216 | [50.666 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36295879312) |
| 2 | Gornak, Morgath, Drakar, Abaddon | 10 / 212 | [95.314 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36296265931) |
| 3 | 150 ID shared-source eksplisit | 160 / 62 | [340.054 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36297544475) |
| 4 | Alchemist | 161 / 61 | [358.305 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36298034563) |
| 5–6 | Ancient Apparition, Nyzrak, Ignis Drachorn | **164 / 58** | [413735 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36302839552) |
| WIP sesi ini | Krobellus — source oracle + draft handler/test, belum masuk roster | **164 / 58** | Belum dijalankan |

## Perilaku/paritas yang sudah dikunci

- QWER, basic attack, source target gate, range/radius, cooldown, visual timer,
  school/source semantics, upgrade, respawn, harga sumber dan lifecycle diuji
  pada tiap kit yang playable.
- Krobellus draft berasal dari recipe sumber yang dieksekusi, bukan metadata:
  Exorcism radius 150 / skill damage ×1.5 (visual 50); Silence radius 120 /
  skill damage ×1 / stun 75 (visual 60); Siphon selected target / ×1.3 / heal
  50% skill damage (visual 50); Crypt radius 200 / ×2.5 / heal 15% max HP
  (visual 90). Source oracle juga merekam cooldown Q220/W240/E420/R900,
  basic projectile, level 1–15, gate, timer trace dan respawn.
- Draft Krobellus belum di-dispatch atau bisa dibeli: pengujian transaksi
  memastikan ID pending tidak debit dan tidak spawn/substitusi parsial.
- Harga upgrade boss tetap 1,6×; starter Lv1→2 = 480G. Kaizen gratis dan
  defender scene dipertahankan.

## Yang tidak termasuk

Hanya migrasi kit hero dan dukungan paritas. Tidak ada item/forge, AIPlayer
penuh, fitur pertandingan lain, refactor besar, rebalance atau art final.
Visual tetap prosedural. “Playable” berarti kit/domain native tervalidasi,
bukan seluruh fitur game Python selesai dimigrasikan.

## Langkah berikut (wajib, jangan melompati gate)

1. Periksa diff WIP dan jalankan ulang semua validasi lokal yang tercantum di
   bawah. Push WIP ke branch Arena ini dan buka/pertahankan PR draft, lalu
   tunggu **CI Godot 4.7.2 import + `tests/run_all.gd` hijau**.
2. Jika CI gagal, jangan daftarkan Krobellus; perbaiki, ulangi seluruh validasi,
   push commit perbaikan dan jalankan CI ulang. Jika lulus, buat commit berikutnya
   yang mendaftarkan kit (`hero_roster.gd`, dispatch dan manifest), update status
   ke 165 playable / 57 pending dan dokumen, kemudian jalankan CI ulang. Kit
   hanya dinyatakan playable bila hasil CI untuk registrasi final juga hijau.
3. Setelah batch final terverifikasi, lanjut berdasarkan recipe unik dalam
   manifest (bukan handler shared generik): Krobellus lalu Vhalzun (level sumber
   5), Gravewake/Kunkka/Syrentha/Thalgryn (6), Akashari/Malzareth/Nyxarath/
   Vorenmarr (7), dan seterusnya. Sisa tepat 58 ID tetap tercantum dalam
   `HERO_ROSTER_STATUS.md`; daftar biaya/recipe sumber tidak diubah.
4. Untuk tiap batch: jalankan oracle sumber → angka `.tres` dari katalog sumber
   seimbang `core.get_all_hero_types` → handler state → tes native cast/trace/
   attack/respawn/roster/transaksi → semua suite lama → source-contract/static/
   parser/lint/format → CI Godot 4.7.2. Jangan lanjut ke batch berikutnya bila
   ada kegagalan.

## Validasi lokal

```sh
python godot_rebuild/tests/validate_project.py
python godot_rebuild/tests/check_source_contract.py
for t in godot_rebuild/tests/*source_oracle.py; do python "$t" || exit; done
python godot_rebuild/tests/source_shared_boss_oracle.py
gdparse $(find godot_rebuild -name '*.gd')
gdlint $(find godot_rebuild -name '*.gd')
gdformat --check $(find godot_rebuild -name '*.gd')
# Saat Godot 4.7.2 tersedia:
godot --headless --path godot_rebuild --editor --import
godot --headless --path godot_rebuild --script res://tests/run_all.gd
```

`gdtoolkit==4.5.0` dipakai untuk parser/lint/format. Oracle hanya menjalankan
sumber Python asli dan menulis fixture di `godot_rebuild/tests/fixtures/`.

## Siap-salin untuk sesi berikutnya bila konteks habis

> Lanjutkan migrasi native Godot target 222 dari branch Arena
> `arena/01a0e1d3-mystic-arena`, baseline `50b7c07` (merge PR #285 ke main).
> Status resmi 164 playable / 58 pending; CI terakhir yang terverifikasi sebelum
> perubahan ini Godot 4.7.2 413735 checks, run
> https://github.com/dharmawantoxi/mystic-arena/actions/runs/36302839552,
> static lokal WIP 4508 PASS. Batch WIP Krobellus 1500G ada di godot_rebuild
> (oracle+fixture, handler khusus, tes direct); BELUM playable, BELUM di roster
> atau dispatch, dan harus tetap ditolak tanpa debit/spawn parsial. Validasi
> lokal sudah pass: validate_project 4508, check_source_contract, seluruh source
> oracle termasuk 150 shared, gdparse/gdlint/gdformat 4.5.0. CI run 36304792506 gagal compile karena tipe `before` belum eksplisit; run
> 36305416457 compile/import lulus tetapi runner gagal 212/431433 assertions.
> Disesuaikan timer visual ke default source dispatcher 60/90/60/100 dan tes
> transaksi ke prototype_battle; seluruh validasi lokal diulang pass. Wajib push
> commit fix dan tunggu CI Godot 4.7.2. Hanya setelah CI WIP hijau,
> daftarkan Krobellus dan ubah menjadi 165/57, lalu CI final harus hijau sebelum
> klaim batch selesai. Sesudah itu lanjut source recipes berikutnya (Vhalzun,
> Gravewake, Kunkka, Syrentha, Thalgryn, dst sesuai manifest), otomatis tiap
> batch lulus. Hanya ubah godot_rebuild; Python read-only. Tanpa item/forge,
> AIPlayer penuh, fitur lain, refactor besar, rebalance atau final art. Pertahankan
> Kaizen gratis dan defender. Jangan kurangi 222, jangan pakai fallback generik
> untuk pending, jangan klaim selesai sebelum 222. Jangan merge tanpa perintah.
> Update jumlah, pending tepat, blocker, hasil tes/CI tiap batch. Branch coding
> tetap yang di atas; commit+push progres batch demi batch.
