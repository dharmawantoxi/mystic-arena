# Mystic UI GDExtension (godot++)

Port `ui_components/_bundle.py` (lapisan **LAYOUT + STATE + LABEL** dari 11
submodul komponen UI) ke Godot C++ GDExtension.

Dokumen status paritas: [`docs/GODOT_PARITY.md`](../../../docs/GODOT_PARITY.md)
(FASE 36). **Status: generator + self-test tanpa engine HIJAU, backend GDScript
belum disakelar — tidak ada perilaku pemain yang berubah.** Lihat "Yang belum"
di bawah sebelum mengaktifkan flag.

## Tujuan

- **Satu sumber** — `src/ui_processor.{h,cpp}` dibangkitkan dari AST
  `ui_components/_bundle.py` (`tools/gen_ui_cpp.py`), bukan ditulis tangan.
  Angka layout (popup build 400x300, kartu toko 340x120, panel hero 280x276,
  cooldown, slide popup unlock, label) datang dari AST + `_core.py` +
  `ui_theme.py`.
- **Yang diport hanya yang deterministik** — geometri, state tombol, teks
  label, predikat hover. Piksel (`pygame.draw`, `Surface`, cache tekstur, RNG
  partikel) dan **metrik font** tetap di renderer masing-masing backend; lebar
  teks dikirim sebagai argumen supaya kedua backend memakai angka yang sama
  tanpa bergantung font engine (pola oracle `ui_theme` FASE 31).
- **Fail-hard** — generator MENOLAK (bukan menebak) kalau literal/ekspresi
  yang dibutuhkan hilang atau berubah bentuk.

## Struktur

```
godot/gdext/mystic_ui/
  SConstruct                          # output -> ../../addons/mystic_ui/bin/
  src/register_types.{h,cpp}          # entry mystic_ui_library_init (level SCENE)
  src/ui_processor.h                  # GENERATED — class MysticUI : RefCounted
  src/ui_processor.cpp                # GENERATED — 80 fungsi ter-bind
  selftest/godot_stub.hpp             # stub Variant/String/Color/Rect2 (BUKAN bagian lib)
  selftest/ui_selftest.cpp            # harness stdin TAB — menjalankan .cpp di luar engine
  selftest/ui_dispatch.inc            # GENERATED — tabel perintah (wajib 1:1 dengan API)
  selftest/shim/godot_cpp/**          # header kosong: include godot-cpp jadi no-op
godot/addons/mystic_ui/
  mystic_ui.gdextension               # kunci debug/release -> berkas template_*
  bin/                                # hasil build (di-gitignore kecuali .gitkeep)
tools/gen_ui_cpp.py                   # Python AST -> C++ (+ --check)
tools/test_ui_cpp_selftest.py         # compile + jalankan C++ tanpa engine
```

`src/ui_processor.{h,cpp}` dan `selftest/ui_dispatch.inc` adalah **hasil
generate** — jangan disunting tangan. Ubah `tools/gen_ui_cpp.py`, lalu:

```bash
python3 tools/gen_ui_cpp.py          # regenerasi (3 berkas)
python3 tools/gen_ui_cpp.py --check  # CI: berkas ter-commit harus identik
```

## Cakupan API (80 fungsi, 11 modul)

| Modul | Contoh |
| --- | --- |
| `base_ui` | `close_button_rect`, `hp_bar_color`, `hp_bar_fill`, `shadow_rect` |
| `hero_portraits` | `portrait_scan_step`, `portrait_crop_box`, `portrait_scale_size`, `portrait_gray_weight` |
| `build_popup` | `build_popup_rect`, `build_popup_buttons`, `build_button_style`, `build_cost` |
| `build_slots` | `slot_blit_offset`, `slot_surface_rect`, `slot_cost_bg`, `slot_pulse` |
| `hero_panel` | `hero_panel_layout`, `skill_badge_rect`, `cooldown_seconds`, `cooldown_overlay_h` |
| `hero_shop` | `shop_panel_rect`, `shop_tabs`, `shop_grid`, `shop_card_state`, `shop_scroll_thumb` |
| `hover_indicators` | `hover_target`, `tower_tooltip_lines`, `tooltip_rects`, `hover_pulses` |
| `notification` | `notification_entry`, `notification_push`, `notification_duration` |
| `overlay` | `newly_unlocked_level`, `unlock_popup`, `overlay_stats_panel`, `action_hint_tokens` |
| `popup_renderer` | `tower_specials`, `tower_title`, `castle_name`, `tower_max_layout`, `upgrade_preview_text` |
| `shop_hints` | `shop_hint_pos`, `shop_hint_bg`, `shop_hint_pulse` |

`module_names()` + `api_signature()` (`ui_v1:11mod:80fn:`) dipakai loader untuk
membuktikan backend C++ benar-benar aktif.

## Self-test tanpa engine (yang menjaga paritas)

```bash
python3 tools/test_ui_cpp_selftest.py     # butuh g++ saja
```

Harness menyala-nyalakan `ui_processor.cpp` APA ADANYA lewat
`selftest/godot_stub.hpp` (header asli ikut di-parse; include godot-cpp
diarahkan ke shim kosong), lalu membandingkan balasannya dengan oracle:

- fixture `ui_hud` di `godot/tests/fixtures/match_parity.json` — angka yang
  direkam dari **draw pygame asli** (`tools/test_godot_match_parity.py`):
  geometri 4 posisi popup build, rect panel hero, kurva slide popup unlock,
  tombol popup menara/nexus;
- `_core.py` + `ui_theme.py` (di-import apa adanya; kalau pygame tidak ada,
  konstanta dibaca dari AST berkas yang sama);
- built-in Python: `round()` half-to-even, `f"{v:,}"`, `int()`, `//`.

Selain nilai (210 cek; 206 di CI yang tidak punya checkout godot-cpp), skrip
mengunci **closed-world** (jumlah entri tabel
perintah == jumlah `bind_static_method` == deklarasi `.h`, setiap fungsi
ter-bind wajib punya perintah uji, tidak ada perintah di luar tabel) dan
**audit wiring** (entry symbol, `.gdextension`, `.gitignore`, rujukan kedua
workflow, allowlist SEMPIT `godot_log_gate`, bentuk cek symbol kelas yang
benar: `nm` statis + demangle, BUKAN `nm -D`).

Kalau ada checkout godot-cpp asli (`GODOT_CPP_DIR`, `godot/gdext/godot-cpp`,
atau `/tmp/godot-cpp`) dan `gen/include`-nya sudah dibangkitkan, skrip juga
mengompilasi `ui_processor.cpp` + `register_types.cpp` dengan `-fsyntax-only`
terhadap header **asli** — ini penangkap bug yang lolos dari stub (mis.
`color.r8()` alih-alih `color.get_r8()` di godot-cpp 4.3) — lalu
meng-compile+**link** `.so` probe dengan default godot-cpp
(`-fvisibility=hidden`) dan mengulang cek symbol langkah "Build mystic_ui":
kelas `godot::MysticUI::` di symbol table STATIS (`nm -C`) dan
`mystic_ui_library_init` di symbol table dinamis (`nm -D`). Dua bug nyata PR
#234 (mangling `_ZN6…` vs `_ZN5…`, dan `nm -D` untuk symbol kelas padahal
visibility-nya hidden) jadi ketahuan lokal dalam ±10 detik, bukan ±30 menit
siklus CI.

## Yang belum (jangan aktifkan `mystic/ui/use_gdext_ui` sebelum selesai)

1. `tools/test_godot_ui_components_parity.py` — oracle statis (spy surface
   pygame) seperti `tools/test_godot_map_data_parity.py`.
2. Backend GDScript + saklar loader (pola `MapDB.gd`/`MapDBLoader.gd`:
   ClassDB lewat string, `force_backend`/`reset_backend`, log sekali per
   backend, fallback senyap) dan setelan `mystic/ui/use_gdext_ui` (default
   **false**).
3. Scene paritas engine (`UiComponentsGdextParityTest`) — langkah build
   `mystic_ui` di `.github/workflows/godot-gdext.yml` (scons + cek symbol
   entry `mystic_ui_library_init` lewat `nm -D`, kelas `MysticUI` lewat `nm -C`
   statis) sudah ada dan menahan regresi link/registrasi.
4. `docs/UI_COMPONENTS_GODOTPP.md`.

Sampai itu selesai, Python/pygame adalah satu-satunya backend dan tidak ada
perilaku pemain yang berubah.
