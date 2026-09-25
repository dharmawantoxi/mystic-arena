# Status & handoff — Godot Rebuild

Diperbarui: 25 September 2026. Pengguna memakai **Windows 11, Godot 4.7.2 standard** dan meminta implementasi langsung di repo, bukan tutorial pengerjaan manual.

## Aturan pekerjaan

- Gunakan proyek **`godot_rebuild/`**, bukan migrasi Godot lama.
- Python/Pygame tetap menjadi referensi; jangan mengubah game Python untuk membuat port baru lolos.
- Branch sesi: **`arena/01a0d776-mystic-arena`**.
- Pengguna meminta push sebelum sesi habis. Lakukan checkpoint/push berkala, jangan menunggu batas sesi yang tidak memiliki indikator pasti.
- Jangan menandai seluruh migrasi selesai hanya karena laboratorium ini berjalan.

## Checkpoint yang sudah dipush

1. **`f4a71ee`** — fondasi baru: menu, sandbox input, 60 Hz, pause/restart/navigasi, tests/CI, rencana migrasi.
   - [CI fondasi lulus](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36113676693).
2. **`741b660`** — laboratorium combat minion, fixture sumber, tes domain/lifecycle.
   - [CI tahap 2 lulus](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36114379895).
   - Job `validate`, annotation `Native Godot tests`: **PASS: 745 checks**.
3. **`5d2d0e0`** — inti siege: Archer/nexus tier 1, projectile, shield/regen dan oracle sumber numerik. CI lulus 1.072 pemeriksaan.
4. **`d09ce35`** — UI Tower & nexus, hasil, wave pilihan tim, lifecycle dan replay.
   - [CI tahap 3 lulus](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36117033161).
   - Job `validate`, annotation `Native Godot tests`: **PASS: 1158 checks**.
5. Perbaikan dokumentasi/handoff setelah checkpoint tersebut tercatat di `git log`. Periksa workflow terbaru pada branch untuk hasil paling baru.

[PR #278](https://github.com/dharmawantoxi/mystic-arena/pull/278) sudah dibuka atas permintaan pengguna; **belum di-merge**. Push ke branch sesi memperbarui PR yang sama. Nomor milestone implementasi di dokumen ini berbeda dari nomor bab rencana manual awal.

## Yang tersedia saat F5

- **Tower & nexus**: enam Archer level 1, dua nexus, projectile homing, shield/regen, seleksi bangunan, wave manual untuk satu/dua tim, dan hasil setelah nexus hancur.
- **Laboratorium minion**: tiga lane asli (277 titik), lima tipe minion tier 1, targeting, movement, cooldown, physical/magic dasar, regen, kematian/kredit uji satu kali, inspeksi unit, wave manual, pause/restart.
- **Uji input**: sandbox penanda hijau lama untuk regression test seleksi, perintah gerak, transform input dan cleanup.
- **Keluar**.

Semua scene dan script sudah dibuat. Pengguna cukup mengimpor `godot_rebuild/project.godot` lalu F5.

## Validasi yang ada

- Native Godot **4.7.2** dijalankan lewat GitHub Actions Linux: import dan runner berhasil.
- 1.158 native checks: stat bangunan, 60 fixture damage sumber, muzzle, regen/shield, projectile sekali hit/owner-target death/TTL, hasil dan replay siege; ditambah 277 titik lane, stat resource, damage/rounding/cooldown, target tie, death/credit, capacity/regen, determinisme 2.400 tick, sandbox lama 10 siklus, combat baru 3 siklus, pause, scaled input, rendering-independent simulation dan cleanup.
- Lokal: parser/linter/formatter GDScript, TSCN/TRES parser, 381 guardrail statis dan fixture-versus-source checker lulus.
- **Belum diuji:** tampilan GPU/screenshots, Windows nyata, resize visual, export Android, multi-touch HP, thermal/performa, save/cloud/pembayaran.
- Binary Godot belum dapat diunduh di sandbox akibat koneksi TLS ke host aset. CI berhasil mengunduh dan menjalankannya, jadi runtime dibuktikan melalui CI, bukan engine lokal.
- Unduhan log CI juga dapat gagal pada host log. Hasil tes penting diterbitkan sebagai annotation GitHub Checks agar dapat dibaca melalui `gh api`.

## File penting

- [`../godot_rebuild/README.md`](../godot_rebuild/README.md): cara membuka di Windows dan status.
- [`../godot_rebuild/COMBAT_CONTRACT.md`](../godot_rebuild/COMBAT_CONTRACT.md): sumber perilaku, batas scope, perbedaan yang disengaja.
- `godot_rebuild/app/app.gd`: satu pemilik screen/navigasi.
- `godot_rebuild/scripts/combat/minion_battle.gd`: simulasi murni `RefCounted`.
- `godot_rebuild/scripts/combat/damage_rules.gd`: **hanya** damage dasar minion, bukan damage generik semua entitas.
- [`../godot_rebuild/SIEGE_CONTRACT.md`](../godot_rebuild/SIEGE_CONTRACT.md): aturan sumber tower/nexus, lifecycle, dan batas scope.
- `godot_rebuild/scripts/combat/siege_battle.gd`: memperluas world minion; bangunan dan projectile.
- `godot_rebuild/scripts/combat/structure_state.gd`: shield/regen/absorb khusus struktur.
- `godot_rebuild/scripts/simulation/siege_session.gd`: antrean tim/wave dan state terminal.
- `godot_rebuild/scenes/siege/`: scene, HUD hasil, visual read-only.
- `godot_rebuild/tests/structure_source_oracle.py`: mengeksekusi metode numerik asli Tower/Castle, bukan mengimpor Pygame.
- `godot_rebuild/tests/siege_checks.gd`: tes domain siege dan determinisme.
- `godot_rebuild/scripts/simulation/combat_session.gd`: physics tick dan antrean command wave.
- `godot_rebuild/scripts/data/lane_layout.gd`: port generator jalur.
- `godot_rebuild/data/minions/*.tres`: lima definisi read-only.
- `godot_rebuild/tests/run_all.gd`, `combat_checks.gd`: runner native tanpa addon.
- `godot_rebuild/tests/check_source_contract.py`: fixture lawan Python asli, tanpa import Pygame.
- `.github/workflows/godot-rebuild.yml`: workflow baru terisolasi dari converter/migrasi lama.

## Batasan penting, jangan dianggap bug/fitur selesai secara keliru

- Wave manual berisi 6 unit kedua tim, atau 3 unit satu tim pada mode siege. Bukan jadwal/komposisi wave produksi.
- **Mode minion lama:** base hanya penanda dan unit keluar di ujung rute. **Mode siege:** unit melanjutkan ke nexus yang dapat diserang; kematian nexus mengakhiri laboratorium.
- Random spawn jitter belum dipindahkan. Urutan update deterministik menggunakan spawn ID.
- Belum ada physics separation antar minion, build/sell/upgrade, tower selain Archer, paid shield, hero, item/debuff, ekonomi pemain, boss, 54 level, save atau audio. Hasil siege belum sama dengan seluruh aturan kemenangan level/boss produksi.
- Archer: HP final 2000 + shield 800; armor sebelum shield. Nexus: shield dulu, lalu reduksi 88% saat perlindungan aktif; damage HP bisa 0. Jangan menyamakan dua formula.
- Tower tidak boleh menggunakan hit instan; hanya projectile. Owner/target mati membatalkan shot. TTL 180 tick dan cap 256 projectile merupakan guard laboratorium.
- Wave uji ikut menentukan perlindungan nexus sampai wave 10. Paid shield/regen belum ada; jangan menyebutnya sistem ekonomi lengkap.
- HP kematian dijepit ke 0, perbedaan normalisasi terdokumentasi.
- Kredit gold adalah counter uji, bukan currency yang disimpan.
- Troll memiliki regen sumber 0.6 per tick, sehingga duel seimbang bisa tidak selesai. Jangan mengubah menjadi per detik secara diam-diam.
- Penampilan masih placeholder. Tes headless bukan jaminan kualitas visual/performa.

## Langkah berikutnya (disarankan)

1. Audit `Game.update_waves` dan `NEXUS_WAVE_COMPOSITION`, termasuk field-clear gating, delay spawn, timer pertama dan per-level/difficulty modifiers.
2. Tulis fixture ekonomi awal/pasif serta harga build/sell/upgrade dari sumber. Jangan hanya menyalin konstanta atas bila ada fungsi penyesuaian runtime.
3. Tambahkan scheduler wave dan ekonomi minimum dalam mode pertandingan terpisah dari kontrol laboratorium, dengan tes transaksi atomik.
4. Port satu jalur build/sell tower dan slot dari lane; tegaskan sumber reward audit vs currency pemain.
5. Selesaikan loop pertandingan kecil, lalu hero/skill dan perluasan konten.
6. Tambahkan validasi visual Windows/GPU bila tersedia; native CI saat ini headless Linux.
7. Pertahankan seluruh tes lama; push checkpoint dan tunggu native CI sebelum menyebut lulus.

## Perintah pemeriksaan

Dari root repo:

```text
python godot_rebuild/tests/validate_project.py
python godot_rebuild/tests/check_source_contract.py
python godot_rebuild/tests/structure_source_oracle.py
```

Jika engine tersedia:

```text
godot --headless --path godot_rebuild --editor --import
godot --headless --path godot_rebuild --script res://tests/run_all.gd
```

Untuk Windows, script siap pakai ada di `godot_rebuild/tests/run_windows.ps1` (lihat README).

GitHub:

```text
gh run list --branch arena/01a0d776-mystic-arena --limit 5
gh run view RUN_ID --json status,conclusion,jobs,headSha,url
gh api repos/dharmawantoxi/mystic-arena/commits/COMMIT_SHA/check-runs
```

Baca annotations pada check-run `validate` bila unduhan log gagal. Untuk push:

```text
git push origin arena/01a0d776-mystic-arena
```

Jangan menyimpan key, credential, binary engine, `.godot/`, save nyata atau output build dalam repo.

## Checkpoint lanjutan — inti prototipe pertandingan (belum ada menu/UI)

- Ditambahkan scheduler otomatis, ledger gold lokal pertandingan, 18 slot sumber, transaksi Archer 100 G / jual 50 G, pelepasan slot hancur, serta session command yang dibatalkan saat pause.
- Prototipe terpisah dari ketiga laboratorium: level 1 / normal, nexus tier 1, tanpa AI asli. Lawan sementara membeli tiga Archer berbayar secara terjadwal.
- `tests/match_source_oracle.py` menjalankan potongan AST Python asli untuk dua trace wave 3.800 tick, komposisi, slot, 12 skenario pemasukan, dan jalur build → UI sale. Stub hanya dependensi di luar scope (render/audio/boss/auto-upgrade AI).
- Guardrail lokal 448 checks, lint/format dan oracle sumber lulus. **Native untuk checkpoint inti ini masih menunggu CI**; angka 1.158 di atas milik milestone siege sebelumnya.
- Berikutnya: tunggu/fix CI inti, lalu buat scene/HUD/menu build-sell, tes input/lifecycle, dokumentasi kontrak prototipe dan push berikutnya. Jangan menganggap inti ini sudah tersedia saat F5.
