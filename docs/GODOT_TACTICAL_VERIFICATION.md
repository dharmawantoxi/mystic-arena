# Verifikasi migrasi `tactical_commands.py` ke Godot

Tanggal: 2026-11-02  
Branch: `arena/bb9896c7-mystic-arena`

## Hasil lokal

| Gate | Hasil |
|---|---|
| `tools/prepare_godot_tactical.py --check` | PASS, sha256 sumber `000dec0edb21…` |
| `tools/test_godot_tactical_prepare.py` | OK, 4 tes |
| `tools/test_godot_tactical_parity.py` | OK, 4 tes |
| `godot_rebuild/tests/validate_project.py` | PASS, **377** checks |
| `gdformat --check` | 69 berkas tidak berubah (di luar generated) |
| `gdlint` | Success: no problems found |
| `gdparse` | bersih |
| Suite native Godot | **PASS: 3761 checks; 0 failures** |
| Boot headless `--quit-after 240` | rc 0 |
| Battery prepare/exporter lain | PASS (core, entities, archetypes, render, system, balance, items, lighting, localization, splash, main) |

Suite native memakai binary Godot 4.7.2 headless `template_debug` yang dibangun
dari source resmi untuk verifikasi lokal. Warning bawaan lokal:

- `4 ObjectDB instances were leaked at exit` — baseline pre-existing build
  headless lokal, bukan regresi tactical.
- `[AUDIO] 1 stream opsional belum tersedia` — aset audio opsional, tidak
  memengaruhi parity taktis dan tidak diklaim sebagai verifikasi output audio.

## Cakupan parity tactical

Fixture `godot_rebuild/tests/fixtures/tactical_parity.json` dibuat dari
`TacticalCommandManager` pygame 2.6.1 asli secara headless melalui harness
closed-world `tools/test_godot_match_parity.py::make_tactical_commands_fixture`:

- 37 skenario closed-world, dijalankan dua kali dengan seed 1701/1702 dan
  dibandingkan identik sebelum diekspor.
- Operasi: tap/gather/protect/attack, hold start/end, mismatch hold,
  follow-mouse, armed hold ketika boss muncul, gather push lock, cooldown,
  blokir state non-playing, auto-protect castle/tower/boss, helper
  count/nearest/threatened/dealer, serta clear retreat/destination.
- Snapshot tiap langkah: state manager, hero biru (posisi, destination,
  destination_auto, follow_target, target, retreat, range), seluruh
  unit/castle (HP, alive, team, damage_dealt), dan state game terpilih.
- 3 kasus `draw_world` pada timer 150/75/10 dan ticks 0/12345/999:
  cincin, titik pusat, dan garis dashed hero. Warna RGB 3-komponen pygame
  dinormalisasi menjadi alpha 255 saat dibandingkan dengan `Color` Godot.
- 5 kasus `draw_ui` pada timer 180/165/150/30/15: alpha teks/shadow,
  border width/radius, dan posisi center. Alpha background tidak diklaim
  identik piksel karena jalur blend native berbeda.
- Fail-closed saat kontrak `data/tactical.json` hilang.

## Perintah reproduksi

```bash
python3 -m pip install pygame==2.6.1 gdtoolkit==4.5.0
python3 tools/prepare_godot_tactical.py --check
python3 tools/test_godot_tactical_prepare.py
python3 tools/test_godot_tactical_parity.py
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

- Oracle menutup dunia taktis saja: tidak ada combat/reward/wave penuh di
  dalam fixture. Integrasi simulasi penuh tetap diuji oleh suite native lain.
- Overlay native memakai primitif Godot dari geometri/alpha oracle; bukan
  replika piksel pygame (anti-alias circle/line, border radius, raster font).
- Peluang auto-boss 20% memakai RNG Godot di produksi; parity numerik
  menyuntikkan roll yang sama dengan oracle, bukan klaim stream Mersenne
  Twister Python.
- `command_origin` source selalu `None`; port mempertahankannya sebagai
  `null` dan tidak mengarang asal perintah.
- Tidak ada verifikasi perangkat Android, audio output, atau visual GPU layar
  nyata.
