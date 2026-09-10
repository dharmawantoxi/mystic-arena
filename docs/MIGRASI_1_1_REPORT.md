# Laporan Migrasi 1:1 Godot ↔ Pygame

> Pygame adalah sumber kebenaran tunggal. Godot HANYA membaca.

**Tanggal:** 2026-09-10T04:14:27.636212

**Status:** ✅ SEMUA LULUS

## Hasil Cek

### ✅ Pygame untouched

- Tidak ada isu

### ✅ Data JSON fresh

- Tidak ada isu

### ✅ Baked assets

- Tidak ada isu

### ✅ Parity oracle

- Tidak ada isu

### ✅ Static Godot

- Tidak ada isu

### ✅ Constants parity

- Tidak ada isu

### ✅ Data from Pygame

- Tidak ada isu

## Cara Pakai

```bash
# Cek parity tanpa ubah apa pun
python tools/godot_pygame_sync.py

# Auto-fix data JSON dari Pygame (tanpa ubah Pygame)
python tools/godot_pygame_sync.py --fix

# Generate laporan ini
python tools/godot_pygame_sync.py --report md

# Full pipeline (data + units + maps)
SDL_VIDEODRIVER=dummy python tools/convert_to_godot.py
SDL_VIDEODRIVER=dummy python tools/convert_to_godot.py --units-png
SDL_VIDEODRIVER=dummy python tools/convert_to_godot.py --maps-png
python tools/test_godot_match_parity.py
```

## Prinsip

- **Pygame tidak diubah** — semua perbaikan di sisi Godot
- **Data Godot dari Pygame** — via converter, bukan manual
- **Visual dari Pygame** — bake renderer asli, bukan port manual
- **Logic dari Pygame** — via parity fixture + generated code
- **Tidak perlu cek manual** — tool ini cek otomatis semua
