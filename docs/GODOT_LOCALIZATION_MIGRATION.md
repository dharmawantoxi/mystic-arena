# Migrasi `localization.py` → Godot (`godot_rebuild/`)

Status: **native GDScript, tanpa Python saat runtime**. Melanjutkan migrasi
`main.py`, `_core.py`, `_entity.py`, `_render.py`, `_system.py`,
`hero_archetypes.py`, `hero_balance.py`, `hero_items.py`, dan `lighting.py`.
Python tetap menjadi sumber kebenaran/oracle; port ini **tidak** menambah atau
mengubah teks, bahasa, atau placeholder.

## Cakupan

| Sumber Python | Native Godot | Catatan |
|---|---|---|
| `LANGUAGES`, `LANGUAGE_LABELS`, bahasa default `id` | `scripts/core/Localization.gd` + `data/localization.json` | Kontrak fail-closed, SHA-256 `localization.py`. |
| `_TEXT` 224 kunci × `id`/`en` | `Localization.texts`, `CoreData.text()` | Urutan kunci id/en identik; tabel sama dengan `core_data.json`. |
| `set_language/get_language` | `Localization.set_language/get_language` | Nilai invalid aman kembali ke `id`. |
| `get_language_label` | `Localization.get_language_label` | Label kosong memakai bahasa aktif; label tidak dikenal fallback Indonesia. |
| `tr(key, **values)` | `Localization.tr_text/tr_for` | Fallback bahasa aktif → Indonesia → kunci. |
| `str.format` subset `{nama}` | `Localization.format_template` | Placeholder hilang/malformed mengembalikan template utuh, seperti `KeyError/ValueError` di sumber. |
| Pilihan bahasa di settings | `GameSettings`, `Main`, `MenuView`, `CoreGame` | Label bahasa ditampilkan dari kontrak; perubahan settings diterapkan ke menu dan match. |

## Arsitektur runtime

```text
data/localization.json
  └── Localization.gd
        ├── set_language/get_language/get_language_label
        ├── tr/tr_for + format_template subset Python
        └── fail-closed load_error/valid()

CoreData
  ├── localization: Localization
  └── text(key, language, args) -> localization.tr_for(...)

Main / MenuView / CoreGame
  ├── settings.language -> Localization.set_language()
  ├── MenuView menampilkan LANGUAGE_LABELS, bukan kode mentah
  └── CoreGame.apply_language() saat configure dan saat settings berubah
```

- `CoreData.text()` sekarang memakai semantik Python: bila satu placeholder
  hilang, template dikembalikan utuh; nilai ekstra diabaikan; bahasa invalid
  fallback ke Indonesia.
- Tabel lokalisasi tetap ada di `core_data.json` untuk kompatibilitas.prepare
  localization menolak bila tabel core drift dari `localization.py`.
- Ini migrasi modul lokalisasi dan jalur settings, **bukan** klaim bahwa semua
  literal UI lama sudah diganti. Pemakaian kunci `hud_*`, `shop_*`, `menu_*`,
  dan seterusnya dapat diadopsi bertahap melalui `CoreData.text()`/`tr()` tanpa
  mengubah tabel sumber.

## Kontrak data & tooling

```bash
# Setelah mengubah localization.py:
python3 tools/prepare_godot_core.py          # jaga tabel core tetap sinkron
python3 tools/prepare_godot_localization.py
python3 tools/prepare_godot_localization.py --check
python3 tools/test_godot_localization_prepare.py
python3 tools/test_godot_localization_parity.py
python3 tools/test_localization.py
```

Exporter tidak membutuhkan pygame/Godot. Ia mengimpor `localization.py` asli,
mengaudit placeholder (hanya `{nama}` polos, tanpa format spec/posisional),
memastikan kunci/urutan id/en identik, lalu menulis:

- `godot_rebuild/data/localization.json`: bahasa, label, urutan kunci, jumlah
  kunci, placeholder per kunci, tabel teks, SHA-256 sumber.
- `godot_rebuild/tests/fixtures/localization_parity.json`: 448 kasus `tr`
  (224 kunci × 2 bahasa), 22 kasus placeholder hilang, 5 kasus ganti bahasa,
  4 kasus label fallback, 4 kasus tepi.

`--check` tidak menulis ulang file; ia gagal bila kontrak/fixture hilang atau
tidak byte-identik dengan hasil ekspor deterministik.

## Batas jujur

- Belum semua layar UI memakai kunci lokalisasi; literal yang belum dipanggil
  melalui `CoreData.text()` tidak berubah otomatis.
- Tidak ada terjemahan bahasa baru; hanya `id` dan `en` sesuai sumber.
- Tidak ada perubahan angka/teks sumber. Drift satu spasi pun gagal di gate.
- Layanan nyata (cloud, top-up, Play Games) tidak disentuh oleh migrasi ini.
