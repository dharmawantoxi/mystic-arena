# Verifikasi migrasi `ui_theme.py` ke Godot

Tanggal: 2026-11-02  
Branch: `arena/c344b7c2-mystic-arena`

## Hasil lokal

| Gate | Hasil |
|---|---|
| `tools/prepare_godot_ui_theme.py --check` | PASS, sha256 sumber `38a9ab02aa8c…` |
| `tools/test_godot_ui_theme_prepare.py` | OK, 5 tes |
| `tools/test_godot_ui_theme_parity.py` | OK, 4 tes |
| `godot_rebuild/tests/validate_project.py` | PASS, **423** checks |
| `gdformat --check` | 80 berkas tidak berubah (di luar generated) |
| `gdlint` | Success: no problems found |
| `gdparse` | bersih |
| Suite native Godot | **PASS: 4076 checks; 0 failures** |
| Boot headless `--quit-after 240` | rc 0 |
| Battery prepare/exporter lain | PASS (core, entities, archetypes, render, system, balance, items, lighting, localization, splash, tactical, main) |

Suite native memakai binary Godot 4.7.2 headless `template_debug` yang dibangun
dari source resmi untuk verifikasi lokal. Warning bawaan lokal:

- `4 ObjectDB instances were leaked at exit` — baseline pre-existing build
  headless lokal, bukan regresi ui_theme.
- `[AUDIO] 1 stream opsional belum tersedia` — aset audio opsional, tidak
  memengaruhi parity tema dan tidak diklaim sebagai verifikasi output audio.

## Cakupan parity ui_theme

Fixture `godot_rebuild/tests/fixtures/ui_theme_parity.json` dibuat dari fungsi
`ui_theme.py` pygame 2.6.1 asli secara headless:

- 32 warna palet dan 29 nama ikon diekspor dari AST/anchor sumber.
- 90 kasus ikon: 29 ikon + unknown pada skala 0.6/1.0/1.5, dibandingkan
  sebagai primitif polygon/circle/rect/line/arc dengan urutan yang sama.
- 188 kasus komponen dalam mode `cheap_alpha` hidup/mati: panel, panel_solid,
  button (hover/ikon/letter-gap/font-size/label sempit), pill 8 kind +
  fallback/disabled, chip left/right + ikon/nilai, section header, toggle,
  slider clamp, option cycler, tab, screen title, back button, scroll
  indicator, HP bar, dan progress bar.
- Helper permukaan: 4 kasus gradient vertikal, 4 kasus radial ellips, dan
  3 kasus shadow small-surface. Baris gradient diambil sebelum mask rounded
  karena mask/raster adalah pendekatan native.
- Teks: letter-spacing termasuk Unicode/spasi ganda, ellipsis dengan glyph
  `…` ada/tidak ada, dan layout shadow menerima titik JSON.
- Corner ticks dan lebar tab auto-size.
- Fail-closed saat kontrak hilang, lalu pemulihan kontrak.

## Perintah reproduksi

```bash
python3 -m pip install pygame==2.6.1 gdtoolkit==4.5.0
python3 tools/prepare_godot_ui_theme.py --check
python3 tools/test_godot_ui_theme_prepare.py
python3 tools/test_godot_ui_theme_parity.py
python3 godot_rebuild/tests/validate_project.py
gdformat --check $(find godot_rebuild -name '*.gd' -not -path '*/entities/generated/*')
gdlint $(find godot_rebuild -name '*.gd' -not -path '*/entities/generated/*')
gdparse $(find godot_rebuild -name '*.gd')
```

Untuk suite native, siapkan aset dan impor proyek Godot seperti workflow
`godot-rebuild.yml`, lalu jalankan `res://tests/run_all.gd` sebagai main loop
test. Jangan menyertakan `override.cfg`, `godot-test`, atau `.godot/` dalam
commit; ketiganya adalah artefak verifikasi lokal.

## Batas verifikasi

- Parity menguji formula, geometri, warna, urutan draw-command, dan hit-rect
  komponen murni; bukan screenshot piksel GPU.
- Mask rounded, smoothscale shadow, arc ellips, dan raster font memakai
  primitif/tekstur Godot sehingga hasil visual akhir dapat berbeda dari pygame.
- Gradasi teks `Label` memakai shader native; metrik font Godot tidak diklaim
  identik dengan pygame/SDL_ttf.
- Wrapper `Button`/`PanelContainer` mempertahankan layout/hit-test Godot.
  Hover inflation 18×8 dijamin pada komponen murni, bukan sebagai perubahan
  ukuran control saat hover.
- Tidak ada verifikasi perangkat Android, audio output, atau visual GPU layar
  nyata. Migrasi tema tidak mengubah layanan top-up/voucher/cloud save.
