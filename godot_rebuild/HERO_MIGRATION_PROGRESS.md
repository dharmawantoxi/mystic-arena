# Progress migrasi kit hero Godot — checkpoint sesi Arena

## Status saat ini

**Target tetap 222. Manifest staged: 165 playable, 57 pending; batch registry final masih menunggu CI.** Tidak ada pengurangan target atau klaim 222 selesai. Baseline branch sesi berasal dari `50b7c07` (merge PR #285 ke `main`). Semua perubahan sesi hanya di `godot_rebuild/`; Python asli read-only.

- Branch Arena wajib: `arena/01a0e1d3-mystic-arena`; PR draft [#288](https://github.com/dharmawantoxi/mystic-arena/pull/288).
- CI baseline sebelum perubahan sesi: [Godot 4.7.2, 413735 native checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36302839552), static 4476 PASS.
- **Krobellus (1500G)** source oracle, handler, native cast/trace/attack/respawn/roster test sudah ditambahkan. Direct handler/native kit test hijau pada [CI run 36305961876: 431437 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36305961876). Setelah itu dispatch, registry, manifest dan source recruit transaction fixture diperbarui; **integrasi final belum terverifikasi CI**, sehingga jangan lanjut batch lain/merge sebelum CI hijau. Jika gagal, pertahankan penolakan Krobellus dan perbaiki.
- Dua kegagalan sebelumnya sudah ditangani: [36304792506](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36304792506) compile type inference (`before` kini `int`); [36305416457](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36305416457) native runner 212/431433 karena visual timer harus default source dispatcher 60/90/60/100 dan transaksi dites melalui `prototype_battle`. Run langsung sesudah perbaikan lulus, kemudian integrasi roster dibuat.
- Validasi lokal sebelum integrasi registry lulus (4508 static checks). Sesudah registry/recruitment fixture diperbarui seluruh lokal validasi dijalankan ulang dan lulus: `validate_project.py` **4513 static checks**, source-contract, semua source oracle termasuk source-shared (150 ID), dan gdparse/gdlint/gdformat 4.5.0. Final native CI integrated masih menunggu.

Daftar mesin resmi `data/ai/hero_migration_status.json`; daftar lengkap ID/harga/recipe ada di [HERO_ROSTER_STATUS.md](HERO_ROSTER_STATUS.md). Manifest staged kini 165/222; final CI untuk dispatch, pembelian dan roster Krobellus masih wajib.

## Batch selesai sebelum sesi ini

| Batch | Hasil | Total / sisa | Hasil CI Godot 4.7.2 |
|---|---|---:|---|
| Baseline PR #283 | Kaizen, Thorne, Grimjaw, Sylara | 4 / 218 | Baseline diterima |
| 1 | Vex, Zephyr | 6 / 216 | [50.666 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36295879312) |
| 2 | Gornak, Morgath, Drakar, Abaddon | 10 / 212 | [95.314 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36296265931) |
| 3 | 150 ID shared-source eksplisit | 160 / 62 | [340.054 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36297544475) |
| 4 | Alchemist | 161 / 61 | [358.305 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36298034563) |
| 5–6 | Ancient Apparition, Nyzrak, Ignis Drachorn | **164 / 58** | [413735 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36302839552) |
| 7 staged | Krobellus (1500G) — kit direct test PASS; roster/source recruit integration staged | **165 / 57** | Direct test [431437 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36305961876); final integration CI pending |

## Perilaku/paritas yang sudah dikunci

- QWER, basic attack, source target gate, range/radius, cooldown, visual timer,
  school/source semantics, upgrade, respawn, harga sumber dan lifecycle diuji
  pada tiap kit yang playable.
- Krobellus draft berasal dari recipe sumber yang dieksekusi, bukan metadata:
  Exorcism radius 150 / skill damage ×1.5; Silence radius 120 / skill damage
  ×1 / stun 75; Siphon selected target / ×1.3 / heal 50% skill damage; Crypt
  radius 200 / ×2.5 / heal 15% max HP. Source methods set brief visual timers,
  tetapi wrapper menetapkan source dispatcher defaults Q/W/E/R 60/90/60/100.
  Oracle juga merekam cooldown Q220/W240/E420/R900,
  basic projectile, level 1–15, gate, timer trace dan respawn.
- Krobellus kini memiliki dispatch/roster eksplisit dan source recruit oracle
  menambahkan transaksi aktual. Direct native test sudah lulus; final CI harus
  memastikan pembelian 1500G tepat, debit/identity, roster dan seluruh suite lama.
- Pending lain tetap tidak di-dispatch: transaksi menolak tanpa debit, partial
  spawn atau substitusi; `ai_recruit` dan `source_shared` memakai Kunkka (900G)
  sebagai ID pending murah.
- Harga upgrade boss tetap 1,6×; starter Lv1→2 = 480G. Kaizen gratis dan
  defender scene dipertahankan.

## Yang tidak termasuk

Hanya migrasi kit hero dan dukungan paritas. Tidak ada item/forge, AIPlayer
penuh, fitur pertandingan lain, refactor besar, rebalance atau art final.
Visual tetap prosedural. “Playable” berarti kit/domain native tervalidasi,
bukan seluruh fitur game Python selesai dimigrasikan.

## Langkah berikut (wajib, jangan melompati gate)

1. Jalankan ulang semua validasi lokal setelah integrasi registry/recruitment
   fixture, commit+push ke branch Arena ini dan pertahankan PR draft #288. Tunggu
   **CI Godot 4.7.2 import + `tests/run_all.gd` hijau** untuk versi integrasi.
2. Jika CI gagal, Krobellus belum selesai: perbaiki atau pulihkan roster/dispatch/
   manifest ke pending tanpa debit/substitusi; ulangi semua suite, push dan CI.
   Hanya final green yang mengunci batch pada **165 playable / 57 pending**.
3. Sesudah final green, lanjut recipe unik manifest: Vhalzun (level 5), lalu
   Gravewake/Kunkka/Syrentha/Thalgryn (6), Akashari/Malzareth/Nyxarath/Vorenmarr
   (7), dan seterusnya. Sisa tepat 57 ID tercantum dalam `HERO_ROSTER_STATUS.md`;
   harga dan recipe sumber tetap.
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
> PR draft #288 pada branch yang sama. Manifest staged 165 playable / 57 pending;
> Krobellus 1500G sudah di roster/dispatch setelah direct handler + native test
> hijau 431437 checks di CI run
> https://github.com/dharmawantoxi/mystic-arena/actions/runs/36305961876.
> Integrasi roster/purchase dan source-recruit fixture baru saja ditambahkan,
> sehingga batch BELUM final sampai CI terbaru Godot 4.7.2 full `run_all` hijau.
> Sebelumnya run 36304792506 gagal compile (`before` type); 36305416457 lulus
> import tetapi gagal 212/431433 assertions. Sudah diperbaiki visual source
> default 60/90/60/100 dan tes transaction memakai prototype_battle.
> Validasi lokal sesudah integrasi: validate_project 4513, source-contract,
> semua source oracle termasuk 150 shared, gdparse/gdlint/gdformat 4.5.0 PASS.
> `ai_recruit_source_oracle` kini mencatat 486 transaksi kit terdaftar. Tunggu CI;
> jika gagal, kembalikan Krobellus ke pending/ditolak tanpa debit sampai fix.
> Jika final pass lanjut Vhalzun, Gravewake, Kunkka, Syrentha, Thalgryn dst sesuai
> manifest. Hanya ubah godot_rebuild; Python read-only. Tanpa item/forge,
> AIPlayer penuh, fitur lain, refactor besar, rebalance atau final art. Pertahankan
> Kaizen gratis dan defender. Jangan kurangi 222, jangan fallback generik untuk
> pending, jangan klaim selesai sebelum 222. Jangan merge tanpa perintah. Commit+
> push progres per batch ke branch ini.
