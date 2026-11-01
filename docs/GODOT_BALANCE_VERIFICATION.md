# Verifikasi migrasi `hero_balance.py` → Godot

Tanggal: 2026-11-01 · Branch: `arena/295140de-mystic-arena` · Proyek: `godot_rebuild/`

## Hasil lokal

| Pemeriksaan | Hasil |
|---|---|
| `tools/prepare_godot_main.py --check` | PASS — 54 level, 32 aset |
| `tools/prepare_godot_core.py --check` | PASS — 222 hero, 216 boss; sha256 `068cbd7215bc` |
| `tools/prepare_godot_archetypes.py --check` | PASS — sha256 `19d0e08bb74c` |
| `tools/prepare_godot_balance.py --check` | PASS — 216 pristine boss, 6 starter; sha256 `21f081a432de` |
| `tools/prepare_godot_entities.py --check` | PASS — sha256 `9cba05ebd821` |
| `tools/prepare_godot_render.py --check` | PASS — 54 tema; sha256 `77d01b73d863` |
| `tools/prepare_godot_system.py --check` | PASS — 17 suara, 3 slot; sha256 `a6b5508c7681` |
| Exporter tests core/main/entity/archetypes/balance/render/system | **33 passed** (4/2/3/7/7/5/5) |
| `tools/test_cloud_save.py` | 18 lulus, 0 gagal |
| `godot_rebuild/tests/validate_project.py` | **PASS: 241 checks** |
| `gdparse` (58 `.gd`, termasuk generated) | PASS |
| `gdlint` + `gdformat --check` (56 non-generated) | PASS |
| Runtime suite headless | **PASS: 2858 checks, 0 failures** |
| Boot main scene headless `--quit-after 180` | rc 0, log Mystic Arena `state=splash`, tanpa `SCRIPT ERROR:`/`ERROR:` |
| `git diff --check` | PASS |

Suite naik dari baseline 832 menjadi 2858 checks. Tambahan `_test_balance()`
membandingkan runtime GDScript dengan oracle Python untuk 222 metrik hero,
222 baris tabel resolve, 222 baris tabel akhir, 216 stat final boss, laporan
parity/jangkar/fixpoint, 512 kombinasi catch-up, 36 kasus stat starter,
8 kasus hitung unlock, 216 hasil kalibrasi resistansi, helper pembulatan/statistik,
fixpoint cell-band, dan 2 varian roster. Tes juga menguji idempotensi dari baseline
pristine, starter yang tidak berubah di katalog toko, wiring `MatchModel.setup`
dan pembelian hero AI, serta fail-closed `CoreData` saat kontrak balance hilang.

## Paritas data dan angka kunci

- `hero_balance.py` tidak diubah. SHA-256 sumber:
  `ecc5cffdd017274d9214822824d81a5cae9d3466d34760dda45dfc2564a61fb7`.
- Replay Python atas katalog mentah menghasilkan **0 perbedaan** stat final dan
  metadata `__bal` terhadap `godot_rebuild/data/core_data.json` yang sudah ada.
- Cakupan fixture: raw 222, pristine 216, `resolve_table` 222, `table` 222,
  `final_stats` 216, metrik 222, kalibrasi 216.
- `LAST.pool_means`: DPS **486.1**, EHP **2495.4**, n **216**.
- `LAST.pool_anchor`: DPS `1.0937411506268484`, EHP `1.089304840932699`.
- `LAST.fix`: 1 pass, last_move `0.0004`, faktor `0.9998..1.0004`, n 216.
- Skala kalibrasi resistansi: mini armor `1.3333333333333333` / MR
  `1.8000000000000003`; true armor `1.2333333333333334` / MR
  `1.8000000000000003`.
- Determinisme JSON diuji dengan `PYTHONHASHSEED=1` dan `99`; `--check` lulus
  tanpa menulis ulang file. Urutan key fixture memakai `sort_keys=True` karena
  iterasi set Python pada paritas sel dapat berubah antar hash seed.

Contoh runtime Kaizen (level 1, **setelah** kompensasi melee native +15% HP /
+20% damage, sebelum item/upgrade):

| Boss unlock dihitung | Multiplier HP/damage | Base HP | Base damage |
|---:|---|---:|---:|
| 0 | 1.4000 / 1.2720 | 886 | 53 |
| 2 | 1.3333 / 1.2267 | 843 | 52 |
| 12 atau 216 | 1.0000 / 1.0000 | 632.5 | 42 |

Angka toko tetap 550 HP / 35 damage; catch-up tidak dibake ke katalog. Saat roster
penuh, multiplier tepat 1 sehingga kompensasi melee native tidak dibulatkan ulang.

## Cara menjalankan

```bash
# Gate Python dan kontrak (tanpa pygame)
python3 tools/prepare_godot_main.py
python3 tools/prepare_godot_core.py
python3 tools/prepare_godot_balance.py --check
python3 tools/test_godot_balance_prepare.py
python3 godot_rebuild/tests/validate_project.py

# Godot resmi (CI)
godot --headless --path godot_rebuild --editor --import
godot --headless --path godot_rebuild --script res://tests/run_all.gd
godot --headless --path godot_rebuild --quit-after 180
```

### Runner lokal sandbox

Binary resmi Linux tidak tersedia di sandbox, jadi verifikasi lokal memakai build
headless kustom **4.7.2.stable.custom_build** dari source resmi tag `4.7.2-stable`
(elapsed **00:22:57.83**, exit 0):

```bash
scons platform=linuxbsd target=template_debug production=no use_lto=no \
  disable_3d=yes vulkan=no x11=no wayland=no alsa=no pulseaudio=no \
  dbus=no fontconfig=no udev=no speechd=no accesskit=no -j2
cp bin/godot.linuxbsd.template_debug.x86_64 godot_rebuild/godot-test
```

Build tersebut menonaktifkan path override (`--path`/`--script` abort). Runner
lokal memakai `override.cfg` sementara (`run/main_loop_type="MysticTestRunner"`)
dan `.godot/global_script_class_cache.cfg` tulisan tangan berisi 54 kelas dengan
`is_abstract`/`is_tool`:

```bash
cd godot_rebuild
./godot-test --headless          # dengan override.cfg suite
rm override.cfg
./godot-test --headless --quit-after 180
```

`godot-test`, `.godot/`, `override.cfg`, dan salinan audio hasil prepare tetap
di-gitignore. CI memakai binary resmi yang dipin ke 4.7.2 dan perintah normal di
atas; hasil CI dicatat pada pull request, bukan diasumsikan dari runner lokal.

## Catatan / batasan verifikasi

- `WARNING: 4 ObjectDB instances were leaked at exit` muncul pada run headless
  suite/boot (sudah ada sebelum migrasi ini). Tidak ada `SCRIPT ERROR:` atau
  `ERROR:`; warning ini tidak disembunyikan atau diklaim sebagai nol.
- Boot menyebut 1 stream audio opsional belum tersedia. Tes audio memverifikasi
  state/throttle/gating, bukan output suara nyata.
- Headless memverifikasi state/API/paritas data, bukan piksel GPU, perangkat
  Android, signing keystore, Play Games, atau top-up produksi.
- Parity dikunci pada katalog sumber dan baterai oracle di atas, bukan klaim
  bit-identik untuk seluruh ruang float yang mungkin. `py_round_n()` memakai
  formatting desimal Godot karena scaling `round(x*10^n)/10^n` salah pada kasus
  tie binary; seluruh kasus tie oracle lulus.
- Native sengaja menerapkan catch-up hanya untuk starter, setelah kompensasi
  melee, dan hanya saat multiplier ≠ 1. Ini tidak menyalin efek samping
  `_entity.Hero` Python yang memanggil helper untuk semua hero lalu mereset base
  stat non-starter ke angka katalog mentah. Helper balance sendiri tetap parity.
- `ENABLE_REBUDGET` dan saklar audit lain diekspor mengikuti sumber; tidak semua
  menjadi cabang runtime baru. Tidak ada reklasifikasi arketipe atau rebalance.
- Atribut item `magic_only` tetap berbasis role seperti `hero_items.py`, terpisah
  dari sekolah damage balance. Keyword role native yang sudah ada tidak diperluas.
- Tidak ada klaim layanan produksi aktif tanpa konfigurasi/plugin yang sebenarnya.
