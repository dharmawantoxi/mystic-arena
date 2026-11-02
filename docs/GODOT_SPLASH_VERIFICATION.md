# Verifikasi migrasi `splash_screen.py` ke Godot

Tanggal: 2026-11-02  
Branch: `arena/48a6ffc7-mystic-arena`

## Hasil lokal

| Gate | Hasil |
|---|---|
| `tools/prepare_godot_splash.py --check` | PASS, sha256 sumber `f25d8a8edeb2…` |
| `tools/test_godot_splash_prepare.py` | OK, 5 tes |
| `tools/test_godot_splash_parity.py` | OK, 5 tes |
| `godot_rebuild/tests/validate_project.py` | PASS, **347** checks |
| `gdformat --check` | 66 berkas tidak berubah |
| `gdlint` | Success: no problems found |
| `gdparse` | bersih |
| Suite native Godot | **PASS: 3711 checks; 0 failures** |
| Boot headless `--quit-after 240` | rc 0 |
| Battery prepare/exporter lain | PASS (core, entities, archetypes, render, system, balance, items, lighting, localization, main) |

Suite native memakai binary Godot 4.7.2 headless `template_debug` yang dibangun
dari source resmi untuk verifikasi lokal. Warning bawaan lokal:

- `4 ObjectDB instances were leaked at exit` — baseline pre-existing build
  headless lokal, bukan regresi splash.
- `[AUDIO] 1 stream opsional belum tersedia` — aset audio opsional, tidak
  memengaruhi splash dan tidak diklaim sebagai verifikasi output audio.

## Cakupan parity splash

Fixture `godot_rebuild/tests/fixtures/splash_parity.json` dibuat dari
`SplashScreen` pygame 2.6.1 asli secara headless:

- 5 timeline: normal, skip pada 0.0, 0.1, 1.0, dan 2.0 detik; 200 frame per
  skenario, `dt = 1/60`.
- 46 partikel: state awal, evolusi 240 frame dengan stream respawn yang
  disuntikkan, dan gambar twinkle pada `elapsed = 1.5`.
- 4 ukuran background: 64×48, 320×240, 1280×720, 1277×719; sampel RGB dan
  hash RGB penuh untuk ukuran kecil.
- 16 kasus layout: tanpa logo dan logo 1024×1024, 800×300, 64×32 pada
  elapsed 0.0, 0.45, 0.9, 1.5; rect logo/title/subtitle/hint, garis aksen,
  dan rect glow judul.
- 3 profil alpha glow logo: radius 30, 47, 190.
- Kuantisasi grow half-to-even CPython (`18.5 → 18`, `19.5 → 20`).
- Fail-closed saat kontrak hilang.

## Perintah reproduksi

```bash
python3 -m pip install pygame==2.6.1 gdtoolkit==4.5.0
python3 tools/prepare_godot_splash.py --check
python3 tools/test_godot_splash_prepare.py
python3 tools/test_godot_splash_parity.py
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

- Tidak ada verifikasi visual GPU/piksel layar nyata; parity background dan
  glow logo bersifat numerik terhadap oracle pygame, bukan screenshot.
- Font asli Godot tidak diklaim memiliki metrik raster identik dengan pygame;
  fixture layout memakai metrik font palsu deterministik.
- Resize logo dan glow judul adalah pendekatan native yang diuji geometri dan
  alpha factor-nya, bukan replika piksel `smoothscale`/`BLEND_RGBA_MULT`.
- Distribusi partikel memakai RNG Godot; parity numerik memakai state awal dan
  respawn oracle, bukan klaim kesamaan stream Mersenne Twister.
- Tidak ada verifikasi perangkat Android, audio output, atau benchmark
  adaptif `cheap_alpha` pygame.
