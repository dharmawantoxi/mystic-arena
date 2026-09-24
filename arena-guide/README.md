# arena-guide/ — arsip sesi port manual Godot

Folder ini menyimpan **panduan langkah per langkah** + **status progress** dari sesi
membangun ulang Mystic Arena di Godot 4.7.1 **manual dari nol** (project user di PC
sendiri: `D:\mystic-godot-471`, Godot 4.7.1, renderer Mobile, 1280x720, target desktop F5).

## Chat baru? Mulai dari sini

1. Baca `progress.md` sampai habis — itu memori sesi (status, geometri, jejak langkah, audit paritas).
2. File `steps/L*.gd` adalah **SNIPPET untuk ditempel ke `Main.gd` user, BUKAN file utuh** —
   tidak bisa di-run standalone. Tiap file diawali komentar cara pasang + hook.
3. Kode project user yang sebenarnya TIDAK ada di sini (lihat `project/README.md`).

## Isi folder

- `progress.md` — status terakhir, geometri, urutan `_draw()`, jejak L15–L37, audit paritas.
- `steps/L15-note.md` — L15 (diagonal penuh) tidak tersimpan verbatim; baca catatannya.
- `steps/L16-decor4.gd` … `steps/L37-armor-parity.gd` — snippet per langkah (final, sudah termasuk fix).
- `project/` — (kosong) tempat salinan exact script user BILA user upload/attach file `.gd` ke chat.

## Aturan sesi (jangan dilanggar)

- 1 langkah per giliran; user entri manual sendiri.
- Jangan ubah/commit/push repo kecuali user minta eksplisit.
  Pengecualian: folder `arena-guide/` boleh diupdate tiap langkah selesai (commit + push
  HANYA ke branch sesi — 2026-09-24+: `arena/01a0d0e5-mystic-arena`, sebelumnya
  `arena/01a0cbd1-mystic-arena`; tidak pernah ke `main`).
- Setelah tiap langkah selesai: tulis blok SUMMARY di chat (self-contained, copy-paste aman).
- **KONVENSI DELIVERY 2026-09-23 (permanen): SEMUA file yang diubah SELALU dikirim sebagai link `https://raw.githubusercontent.com/dharmawantoxi/mystic-arena/<branch-sesi>/...` biar user tinggal buka → Ctrl+A → copy paste manual.** Branch sesi 2026-09-24: `arena/01a0d0e5-mystic-arena` (link lama `arena/01a0cbd1-mystic-arena` masih valid untuk konten sampai L33). Berlaku untuk semua chat baru di branch ini — user tidak perlu menjelaskan lagi. Contoh: `Shop.gd` → `.../arena-guide/scripts/Shop.gd`, `Main.gd` → `.../project/Main_FULL_L31.gd`.
- **SCOPE 2026-09-23: SAMAKAN SEMUA LOGIKA GAME DENGAN PYGAME (`_core.py` / `_entity.py` / `_system.py` / `hero_items.py` / `hero_balance.py` / `levels/`), RENDER VISUAL TIDAK DISENTUH (user update sendiri).** Mulai L37 ke atas, ubahan hanya logic (damage/armor/crit/lifesteal/wave/gold/level), tidak ada ubahan `draw_*`.
