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
3. Perbaikan dokumentasi/handoff dan margin HUD setelah checkpoint tersebut tercatat di `git log`. Periksa workflow terbaru pada branch untuk hasil paling baru.

Tidak ada PR/merge ke main yang dilakukan dalam checkpoint ini. Semua push diarahkan ke branch sesi di atas.

## Yang tersedia saat F5

- **Laboratorium minion**: tiga lane asli (277 titik), lima tipe minion tier 1, targeting, movement, cooldown, physical/magic dasar, regen, kematian/kredit uji satu kali, inspeksi unit, wave manual, pause/restart.
- **Uji input**: sandbox penanda hijau lama untuk regression test seleksi, perintah gerak, transform input dan cleanup.
- **Keluar**.

Semua scene dan script sudah dibuat. Pengguna cukup mengimpor `godot_rebuild/project.godot` lalu F5.

## Validasi yang ada

- Native Godot **4.7.2** dijalankan lewat GitHub Actions Linux: import dan runner berhasil.
- 745 native checks: 277 titik lane, stat resource, damage/rounding/cooldown, target tie, death/credit, capacity/regen, determinisme 2.400 tick, sandbox lama 10 siklus, combat baru 3 siklus, pause, scaled input, rendering-independent simulation dan cleanup.
- Lokal: parser/linter/formatter GDScript, TSCN/TRES parser, 254 guardrail statis dan fixture-versus-source checker lulus.
- **Belum diuji:** tampilan GPU/screenshots, Windows nyata, resize visual, export Android, multi-touch HP, thermal/performa, save/cloud/pembayaran.
- Binary Godot belum dapat diunduh di sandbox akibat koneksi TLS ke host aset. CI berhasil mengunduh dan menjalankannya, jadi runtime dibuktikan melalui CI, bukan engine lokal.
- Unduhan log CI juga dapat gagal pada host log. Hasil tes penting diterbitkan sebagai annotation GitHub Checks agar dapat dibaca melalui `gh api`.

## File penting

- [`../godot_rebuild/README.md`](../godot_rebuild/README.md): cara membuka di Windows dan status.
- [`../godot_rebuild/COMBAT_CONTRACT.md`](../godot_rebuild/COMBAT_CONTRACT.md): sumber perilaku, batas scope, perbedaan yang disengaja.
- `godot_rebuild/app/app.gd`: satu pemilik screen/navigasi.
- `godot_rebuild/scripts/combat/minion_battle.gd`: simulasi murni `RefCounted`.
- `godot_rebuild/scripts/combat/damage_rules.gd`: **hanya** damage dasar minion, bukan damage generik semua entitas.
- `godot_rebuild/scripts/simulation/combat_session.gd`: physics tick dan antrean command wave.
- `godot_rebuild/scripts/data/lane_layout.gd`: port generator jalur.
- `godot_rebuild/data/minions/*.tres`: lima definisi read-only.
- `godot_rebuild/tests/run_all.gd`, `combat_checks.gd`: runner native tanpa addon.
- `godot_rebuild/tests/check_source_contract.py`: fixture lawan Python asli, tanpa import Pygame.
- `.github/workflows/godot-rebuild.yml`: workflow baru terisolasi dari converter/migrasi lama.

## Batasan penting, jangan dianggap bug/fitur selesai secara keliru

- Wave manual berisi 6 unit, bukan jadwal/komposisi wave produksi.
- Nexus/base hanya penanda. Unit di ujung rute dihitung `exit`, tanpa kill reward.
- Random spawn jitter belum dipindahkan. Urutan update deterministik menggunakan spawn ID.
- Belum ada physics separation antar minion, tower, siege, projectile, hero, item/debuff, ekonomi pemain, boss, 54 level, menang/kalah, save atau audio.
- HP kematian dijepit ke 0, perbedaan normalisasi terdokumentasi.
- Kredit gold adalah counter uji, bukan currency yang disimpan.
- Troll memiliki regen sumber 0.6 per tick, sehingga duel seimbang bisa tidak selesai. Jangan mengubah menjadi per detik secara diam-diam.
- Penampilan masih placeholder. Tes headless bukan jaminan kualitas visual/performa.

## Langkah berikutnya (disarankan)

1. Audit source `Tower`, `Bullet`, `Castle` di `_entity.py` serta `TOWER_*`, `NEXUS_LEVELS`, shield/regen dan wave di `_core.py`.
2. Tulis kontrak dan fixture sebelum porting: stat final vs base, physical/magic, urutan shield/armor/reduction, kill/reward.
3. Implementasikan satu tower dan projectile dengan damage satu jalur. Jangan membuat visual memanggil damage.
4. Tambahkan nexus yang bisa diserang dan kondisi hasil sederhana. Ganti exit endpoint hanya setelah siege test tersedia.
5. Tambahkan scheduler wave/ekonomi minimum dan loop pertandingan utuh.
6. Setelah loop stabil, baru hero/skill dan perluasan konten.
7. Terus pertahankan semua tes yang sudah lulus; push checkpoint lalu lihat native CI sebelum menyebut selesai.

## Perintah pemeriksaan

Dari root repo:

```text
python godot_rebuild/tests/validate_project.py
python godot_rebuild/tests/check_source_contract.py
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
