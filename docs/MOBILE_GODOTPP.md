# Migrasi `mobile/` → godot++ (GDExtension C++)

Port lapisan keputusan Android — `mobile/` (8 submodul: ambang gesture
`touch`, geometri + visibilitas tombol `hud`, preset/gubernur kualitas
`perf`, safe area + posisi panel `platform_utils`, overlay `debug`,
konfigurasi suara tempur `combat_audio`, validasi payload `cloud_save`,
label build `buildinfo`) — ke C++ (`MysticMobile`, GDExtension
`mystic_mobile`), dibangkitkan dari AST oleh `tools/gen_mobile_cpp.py`.
Status paritas menyeluruh: [`docs/GODOT_PARITY.md`](GODOT_PARITY.md)
(FASE 37).

Cakupan yang SENGAJA keluar (lihat §"Tidak diport"): semua yang menyentuh
SDL/pygame/JNI — `fastblit`, `blitwatch`, `spritecache`, `_bench_core`,
`bootcheck`, `diagnostics`, `sidepanel` (sudah teruji paritasnya lewat
jalur UI), mixer audio, sha256/checksum, strftime, dan gambar. Yang
dimigrasi di sini adalah **lapisan keputusan murni** yang dibaca game
puluhan kali per frame.

## Kenapa C++ untuk mobile/?

Alasan yang sama dengan ui (FASE 36) plus dua alasan khusus Android:

1. **Ambang gesture = rasa sentuhan.** TAP_SLOP 14 px, LONG_PRESS 450 ms,
   DOUBLE_TAP 280 ms, SCROLL_STEP 42 px, FRICTION 0.90 — angka-angka ini
   yang membuat kontrol terasa "pas". Selama hanya ada di pygame, versi
   Godot harus menebak. Kini satu AST menghasilkan kedua backend.
2. **Payload cloud = data pemain.** Urutan pesan error `parse_payload`
   dan semantik try/except `get_payload_summary` (slot rusak di tengah
   → hasil parsial slot itu dibuang, slot lain lanjut) adalah kontrak
   data; duplikasi tangan berisiko menelan save yang seharusnya ditolak.
3. **Drop-in nanti.** Class `MysticMobile` terdaftar di ClassDB; kalau
   suatu saat HUD/gesture dipindah ke node Godot, ambangnya tinggal
   dipanggil — tanpa menyalin angka lagi.

## Arsitektur

```
mobile/*.py (8 submodul)              (sumber kebenaran, TIDAK disunting)
  │ AST (tools/gen_mobile_cpp.py)
  ▼
gdext/mystic_mobile/
  src/mobile_processor.h    (116 baris; 66 method static bound)
  src/mobile_processor.cpp  (1.133 baris; setiap fungsi menyebut baris sumber)
  selftest/mobile_dispatch.inc (271 baris; tabel perintah harness)
  selftest/mobile_selftest.cpp (harness TAB, port ui_selftest.cpp)
  selftest/godot_stub.hpp + shim/godot_cpp/**  (stub Variant; BUKAN bagian lib)
        │
        ▼
addons/mystic_mobile/mystic_mobile.gdextension  (entry mystic_mobile_library_init)
tools/test_mobile_cpp_selftest.py (oracle: mobile/*.py dieksekusi TANPA pygame)
```

### Peta berkas

| Berkas | Peran |
|---|---|
| `tools/gen_mobile_cpp.py` | AST `mobile/*.py` → `mobile_processor.h/.cpp` + `mobile_dispatch.inc` (`--check` byte-identik; gagal-keras, tidak menebak) |
| `godot/gdext/mystic_mobile/src/` | `MysticMobile : RefCounted` — 66 method static, `ClassDB::bind_static_method` |
| `godot/gdext/mystic_mobile/selftest/` | Stub Variant + harness TAB (dipakai self-test, tidak ikut build scons) |
| `godot/addons/mystic_mobile/` | `.gdextension` (kunci Godot `linux.debug.x86_64` → nama berkas scons `.linux.template_debug.x86_64.so`) + `bin/.gitkeep` |
| `tools/test_mobile_cpp_selftest.py` | Eksekusi `mobile_processor.cpp` tanpa engine; oracle = `mobile/*.py` ASLI (AST tanpa node import + stub pygame), **1.564 cek** |
| `.github/workflows/godot-gdext.yml` | `--check` + self-test SEBELUM build godot-cpp; build lib ke-5; `nm -D` + strings-case |
| `godot/tools/godot_log_gate.py` | Allowlist SEMPIT `libmystic_mobile` / `addons/mystic_mobile` |

## Semantik yang dikunci (contoh; daftar lengkap di generator)

* **touch** — TAP_SLOP 14, LONG_PRESS 450, DOUBLE_TAP 280, SCROLL_STEP 42,
  FRICTION 0.90, MIN_SPEED 0.6, radius dbl-tap 40, arm fling 4, divisor
  0.35 cap 3 langkah, smoothing velocity 0.6/0.4. `scroll_notch` memakai
  kontrak SATU langkah loop Python (`while abs(accum) >= SCROLL_STEP`) —
  pemanggil mengulang. `dispatch_button` = urutan prioritas
  `dispatch_to_game` (tap→1, long_press→3, scroll→4/5).
* **hud** — MIN_TAP 80; hit rect = `pygame.Rect.inflate` SEMANTIK ASLI
  (ukuran tumbuh TOTAL dx, bukan per sisi — quirk `inflate(50,50)` pada
  rect 30 px menghasilkan 80, bukan 130); visibilitas 6 tombol dari 7
  primitif `sync()`; peluruhan press_anim 0.12; palet + label skill.
* **perf** — 3 preset (`Quality.apply`) + properti perangkat `__init__`
  (cheap_alpha, max_alpha_px 1_000_000, ...), FX_SMOOTH 0.40 MIN 0.10
  EXP 1.5, lantai token 140/18/10 → 56/10/5, `AdaptiveQuality` 26/52
  window 90 cooldown 180/300 (transisi HIGH↔MEDIUM↔LOW direplikasi).
* **platform_utils** — logis 1280x720, safe area (sentuh 28 px), zona
  panel (ZONA_POPUP_Y 430, ZONA_BAWAH_H 120), popup NIL kalau tidak ada
  panel atau w > pw−8, panel bawah slot 430 + dorong-naik,
  window/pointer→logis (scale falsy → 1.0).
* **debug** — mode 0–3, warna FPS 50/30, frame lambat > 33 ms, format
  baris `[PERF]` pin per-baris.
* **combat_audio** — 7 jenis, `_KONFIG` (volume/jeda/rebut), `POLA`
  fnmatch (pencarian berkas tetap backend), AMBANG_RANGED 100, gerbang
  play jeda→anggaran (rebut melewati anggaran), `ringkas()` persis.
* **cloud_save** — konstanta payload, urutan `parse_payload` LENGKAP
  termasuk `"File corrupt (bad version)"` untuk `int(version)` gagal;
  `payload_summary` = try/except per slot: `max()` ATOMIK (list dengan
  item rusak tidak boleh bocorkan max parsial), tipe `max(0, x)`
  dipertahankan (int tetap int, float tetap float), `int("12.5")` gagal
  → sisa slot dibuang; `exported_at_str` (strftime localtime) tetap
  backend.
* **buildinfo** — BUILD_ID/BUILD_DATE, daftar berkas kunci, format
  `"%05X/%d"`, format label.

## Tidak diport (sengaja, v1)

* `apply_device_profile`, `PhaseTimer`/`FrameTimer` (butuh ukur waktu
  engine); draw semuanya; mixer + pemilihan berkas fnmatch (gerbang
  play saja yang C++); sha256 + canonical-JSON + parse JSON (backend
  engine); strftime (summary mengekspor `exported_at` double);
  JNI/`CloudSaveManager`; `bootcheck`, `diagnostics`, `fastblit`,
  `blitwatch`, `spritecache`, `_bench_core`, `sidepanel`.

## Verifikasi

1. **`gen_mobile_cpp.py --check`** — 3 berkas byte-identik, di **kedua**
   workflow (kesegaran transpile).
2. **`test_mobile_cpp_selftest.py`** — MENG-EXECUTE `mobile_processor.cpp`
   apa adanya lewat stub Variant (g++ saja, tanpa godot-cpp, tanpa
   pygame): oracle = `mobile/*.py` ASLI yang dieksekusi sebagai pohon AST
   tanpa node import (stub `pygame.Rect` semantik SDL, stub
   `platform_utils`/`Quality`/`ui_theme`), **1.564 cek**: konstanta +
   perilaku nyata (gesture didorong lewat `TouchManager` asli, preset
   lewat `Quality.apply` asli, `AdaptiveQuality` diberi makan FPS asli,
   `parse_payload`/`get_payload_summary` asli) — **closed-world** (tabel
   perintah == `bind_static_method` == deklarasi `.h`; setiap fungsi
   ter-bind wajib diuji) + **audit wiring** (entry symbol, `.gdextension`,
   allowlist log gate SEMPIT, path filter kedua workflow, `.gitignore`,
   `mobile/` tetap bersih). Ditemukan & dikunci di sini: quirk
   `Rect.inflate`, `max()` atomik `payload_summary`, `float 1.0` vs
   `int 1` di `cnum`.
3. **Build CI** (`godot-gdext.yml`) — lib ke-5: symlink `godot-cpp`
   bersama, scons, `nm -D " T mystic_mobile_library_init"`, string khas
   tahan-strip `mobile_v1:8mod:66fn:` + `MysticMobile` (visibility=hidden
   + debug_symbols=no membunuh symbol table statis — pelajaran PR #234).

## Status

**DALAM PROSES** (pola FASE 36): class terdaftar + teruji self-test +
terbuild CI, **belum ada** saklar backend di jalur produksi
(`mobile/` pygame tetap satu-satunya jalur pemain), belum ada scene
paritas engine. Flag `mystic/mobile/use_gdext_mobile` sengaja belum
dibuat sampai ada pemakaian pertama di jalur GDScript.
