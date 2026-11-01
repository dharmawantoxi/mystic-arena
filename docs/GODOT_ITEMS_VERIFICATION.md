# Verifikasi migrasi `hero_items.py` → Godot

Tanggal: **2026-11-01**. Branch: `arena/0950b1a8-mystic-arena`.
Lingkup: katalog 33 item, 6 halaman toko kelas, mekanik ID/EN, inventory,
trigger/on-hit/aura/miasma, aturan beli/drop/pending, dan wiring Forge native.

## Lingkungan uji lokal

- Godot **4.7.2.stable.custom_build** headless dibangun dari source resmi
  `godotengine/godot` tag `4.7.2-stable` (SCons, `disable_3d=yes`, tanpa
  Vulkan/X11/Wayland/audio backend). Binary uji tidak di-commit.
- Python 3.11.2, gdtoolkit 4.5.0 (`gdparse/gdlint/gdformat`).
- Runner suite memakai `override.cfg` sementara
  (`run/main_loop_type="MysticTestRunner"`) dan class cache tulis tangan;
  `override.cfg` dihapus sebelum boot main scene dan tidak di-commit.

## Hasil aktual

| Gate | Hasil |
|---|---|
| `python3 tools/prepare_godot_items.py --check` | PASS — 33 item, 6 halaman; SHA-256 kontrak `8736449a1cad` |
| Semua prepare `--check` (core/main/entities/archetypes/render/system/balance/items) | PASS |
| `python3 -m unittest discover -s tools -p 'test_godot_*_prepare.py'` | **41 OK** (items 7 tes) |
| `python3 godot_rebuild/tests/validate_project.py` | **266 PASS** |
| `gdparse` seluruh `.gd` | PASS |
| `gdlint` scripts/tests non-generated | PASS |
| `gdformat --check` scripts/tests non-generated | PASS — 58 file unchanged |
| Suite native `./godot-test --headless` | **3090 checks, 0 failures** |
| Boot main scene `./godot-test --headless --quit-after 120` | RC 0, tanpa SCRIPT ERROR |
| `python3 tools/test_cloud_save.py` | **18 lulus, 0 gagal** |
| `git diff --check` | PASS |

SHA prepare lain tetap: core `068cbd7215bc`, entity `9cba05ebd821`,
render `77d01b73d863`, system `a6b5508c7681`, archetypes `19d0e08bb74c`,
balance `21f081a432de`; main 54 level / 32 aset.

## Cakupan parity items

`HeroItemsParityTest.run()` membandingkan runtime GDScript dengan fixture
Python `hero_items_parity.json`:

- 25 kasus role Magic (`is_magic_hero`, termasuk Anti-Mage dikecualikan).
- 34 kasus kelas item (33 item + item hilang fallback physical).
- 66 teks mekanik (33 item × ID/EN), termasuk urutan field dan tipe int/float
  sumber yang diekspor eksplisit karena JSON sort-key menghilangkan urutan
  dan perbedaan `str(52)` vs `str(3.0)`.
- 18 loadout getter/stat/caps (crit max, block, chain, bash, rend, veil,
  ghost, gale, thorn, empower, aura, slow-resist, skill-amp, heal-amp).
- 19 trigger deterministik (auto-active, cooldown, regen, target debuff).
- 1 kasus aura multi-hero + minion + boss (Steel Aegis, Scarlet guard,
  Everfrost/Solar/Searbrand).
- 10 kasus on-hit dengan proc dipaksa deterministik (lifesteal, cleave,
  chain, bash, miasma/frostbite, empower, extra target).
- 33 kasus suggestion AI per role/range/owned.
- Regresi runtime: heal amp, slow resist, skill amp, silence, aura guard
  block, veil miss, true strike; aturan toko gold/slot/melee/magic, pending
  saat mati, kirim saat respawn, drop tanpa refund, Holy Rapier drop saat mati.

## CI

`godot-check.yml` dan `godot-rebuild.yml` menjalankan
`prepare_godot_items.py --check` dan `test_godot_items_prepare.py`, dengan
path filter `hero_items.py` serta tool items. `validate_project.py` mengunci
modul, hash, cakupan 33/6, konstanta sumber, wiring runtime, dan gate CI.
Status CI resmi dicatat pada PR migrasi ini.

## Batasan verifikasi

- Headless tidak membuktikan rendering GPU/piksel, perangkat Android,
  audio output, Play Games, top-up produksi, atau signing keystore.
- Forge UI native memakai halaman kelas dan target terpilih; renderer ikon
  dan animasi Pygame tidak disalin pixel-perfect.
- Masih ada 1 stream audio opsional yang belum tersedia di lingkungan uji;
  suite/boot tetap lulus dan tidak menganggap audio produksi terverifikasi.
- Efek visual/popup/chain FX disederhanakan ke popup/effect native; yang
  diuji parity adalah damage/debuff/timer/aturan, bukan fidelitas visual.
