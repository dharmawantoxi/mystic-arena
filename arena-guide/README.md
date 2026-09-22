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

- `progress.md` — status terakhir, geometri, urutan `_draw()`, jejak L15–L24, audit paritas.
- `steps/L15-note.md` — L15 (diagonal penuh) tidak tersimpan verbatim; baca catatannya.
- `steps/L16-decor4.gd` … `steps/L28-slash-polish.gd` — snippet per langkah (final, sudah termasuk fix).
- `project/` — (kosong) tempat salinan exact script user BILA user upload/attach file `.gd` ke chat.

## Aturan sesi (jangan dilanggar)

- 1 langkah per giliran; user entri manual sendiri.
- Jangan ubah/commit/push repo kecuali user minta eksplisit.
  Pengecualian: folder `arena-guide/` boleh diupdate tiap langkah selesai (commit + push
  HANYA ke branch sesi `arena/01a0ae7d-mystic-arena`, tidak pernah ke `main`).
- Setelah tiap langkah selesai: tulis blok SUMMARY di chat (self-contained, copy-paste aman).
