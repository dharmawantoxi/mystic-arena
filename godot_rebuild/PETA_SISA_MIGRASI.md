# Peta Sisa Migrasi — status singkat

Dokumen ini hanya mencatat **slice portrait Hero Shop** yang dikerjakan pada
branch `arena/2aa50b3c-mystic-arena`. Bukan audit sistem lain.

## Catatan penting tentang handoff sebelumnya

Sesi ini **tidak mewarisi worktree dirty** dari handoff sebelumnya:

- Branch `arena/2aa50b3c-mystic-arena` dibuat baru dari `cd77e4d` (merge PR #325).
- `git status` bersih, `git stash list` kosong, tidak ada commit di branch ini.
- `godot_rebuild/PETA_SISA_MIGRASI.md` belum pernah ada di repo.
- Tidak ada satu pun kode portrait di `godot_rebuild/` sebelum sesi ini.

Karena itu slice ini **dibangun dari nol**, bukan diselesaikan dari WIP lama.
Kalau WIP aslinya masih ada di sandbox/branch lain, dokumen ini yang perlu
digabung sebelum lanjut.

## Yang sudah selesai (slice Kaizen/Thorne)

| Berkas | Peran |
|---|---|
| `scripts/ui/hero_portrait.gd` | Kanvas prosedural. `kaizen` dan `thorne` punya canvas sendiri; id lain jatuh ke bust generik deterministik dari hash id. |
| `scripts/ui/hero_shop_card.gd` | Shared Hero Shop card. Tetap `extends Button` agar scene suite tetap menemukan baris lewat `tooltip_text` dan tetap membaca `.text` / `.disabled`. |
| `scripts/ui/hero_shop_panel.gd` | Panel in-match memakai shared card (lebar 485). |
| `scripts/ui/meta_hero_shop_panel.gd` | Panel main-menu memakai shared card (lebar 525). |
| `tests/hero_shop_portrait_checks.gd` | Suite native: dispatch, fallback deterministik, kontrak card, wiring panel. |
| `tests/run_all.gd` | Suite portrait terdaftar. |

Kontrak yang sengaja dijaga:

- `hero_requested.emit(hero_type)` tetap di panel in-match.
- `unlock_requested.emit(hero_type)` tetap di panel permanent, dan panel tetap
  request-only (tanpa `save_state`).
- Portrait punya `mouse_filter = MOUSE_FILTER_IGNORE` supaya tidak memakan klik baris.
- Teks card digeser lewat `content_margin_left` stylebox, bukan child label.

## Validasi yang sudah dijalankan

```
gdparse   $(find godot_rebuild -name '*.gd')        -> OK
gdlint    $(find godot_rebuild -name '*.gd')        -> Success: no problems found
gdformat --check $(find godot_rebuild -name '*.gd') -> 248 files unchanged
git diff --check                                    -> OK
python3 godot_rebuild/tests/validate_project.py     -> PASS: 12333 static checks
```

`gdtoolkit 4.5.0` dipasang di sandbox untuk menjalankan batch di atas.

## Validasi yang BELUM dijalankan

**Runtime test Godot belum dijalankan.** Engine tidak tersedia di sandbox ini
(tidak ada binary `godot`, dan CI mengunduh engine terpisah). Yang belum
terverifikasi sampai CI jalan:

- `--headless --path godot_rebuild --script res://tests/run_all.gd`
- `--headless --path godot_rebuild --editor --import`

Risiko runtime yang perlu dilihat pertama kalinya gagal:

1. `add_child()` dipanggil sebelum card masuk tree (lewat `setup()` /
   `_ready()`). Ini pola umum, tapi belum terbukti di engine.
2. Hasil gambar portrait belum dilihat mata — baru benar secara prosedural.

## Sisa pekerjaan slice ini

- Verifikasi runtime di CI (`godot-rebuild.yml`).
- Koreksi visual portrait Kaizen/Thorne setelah ada render nyata.

## Batas scope

- Tidak ada portrait hero lain yang dimulai (hanya Kaizen + Thorne + fallback generik).
- Tidak ada sistem lain yang diaudit atau diubah.
- Top-up flow Python dan voucher allowlist tidak disentuh.
