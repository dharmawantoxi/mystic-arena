# Verifikasi migrasi core Godot

Tanggal: 2026-11-01.

| Pemeriksaan | Hasil lokal |
|---|---|
| Persiapan aset/metadata main | 54 level; 32 aset; `--check` lulus |
| Persiapan data core | 54 level, 222 hero, 216 boss, 33 item; `--check` lulus |
| Guardrail proyek/sumber | 110 pemeriksaan lulus |
| Tes exporter main | 2 unittest lulus |
| Tes exporter core + fixture cloud | 4 unittest lulus |
| Oracle cloud Python | 18 lulus, 0 gagal |
| `gdparse` | 37 berkas GDScript lulus |
| `gdlint` | Tidak ada masalah (kebijakan `gdlintrc`) |
| `gdformat --check` | Seluruh berkas sesuai |
| Runtime native headless | **176 pemeriksaan lulus, 0 kegagalan** |
| Boot scene utama headless | Splash → menu berjalan; exit 0 |
| Diff hygiene | `git diff --check` lulus |

## Lingkungan uji lokal

Engine uji dikompilasi dari source resmi Godot tag `4.7.2-stable`, target Linux
headless tanpa GPU/audio backend (`vulkan=no`, `disable_3d=yes`, tanpa
X11/Wayland/ALSA/PulseAudio). Versi engine melaporkan
`4.7.2.stable.custom_build`. Binary rilis official tidak dapat diunduh di sandbox
karena host redirect unduhan berada di luar allowlist jaringan. Karena target uji
bukan editor binary, uji runtime memakai cache kelas global dan
`application/run/main_loop_type=MysticTestRunner` sementara melalui `override.cfg`
yang dihapus setelah tes. Scene utama diuji lewat konfigurasi proyek normal tanpa
override tersebut.

Tes native mencakup suite shell sebelumnya (state, fixed clock, gesture, input
ownership, pause/background, audio, HUD safe-area, adapter palsu) ditambah:

- Data core: jumlah level/hero/boss/item, lane, balance, localization.
- Ekonomi: starting gold easy/hard, milli-gold income.
- Status effect: strongest slow, anti-heal, burn tick integer.
- Inventory: slot, stat aggregation, tower shield/upgrade/sell, castle shield.
- Wave: jadwal mini-boss deterministik dengan seed, rentang normal, komposisi late.
- Tactical: quick tap durasi penuh, long hold release tail.
- Save: slot isolation, reward first/replay/repeat, defeat stats, difficulty lock,
  hero purchase, voucher/topup dedupe, delete slot.
- Cloud: fixture checksum Python valid, bad checksum ditolak, native roundtrip,
  restore menghapus slot yang tidak ada di cloud.
- Voucher: format, allowlist wajib di produksi, nominal allowlist.
- Controller: family, deadzone, button edge, cursor movement.
- Layanan: cloud/topup default unavailable, tidak ada sukses palsu.
- Match: setup, tower layout, build slot, wave spawn, income, build tower, skill,
  tactical move, victory.
- DevMode: toggle, gold cheat, cheat terkunci saat dev off.
- CoreGame: combat-ready, fixed step, shop, pointer selection, dev hotkey, result
  overlay, reward guard anti double-grant.

Peringatan `ObjectDB instances were leaked at exit` dapat muncul saat engine
headless keluar cepat setelah suite/boot. Ini bukan error script; tes memberikan
beberapa frame pembersihan node/stream. CI memperlakukan `SCRIPT ERROR:`/`ERROR:`
sebagai kegagalan, bukan peringatan cleanup Dummy backend.

## Belum diverifikasi lokal

- `--editor --import` dan `--script` pada binary Standard official: disiapkan di
  CI dan harus dilihat pada PR/commit terkait.
- Rendering visual/GPU, audio terdengar, controller fisik, Android nyata, signing,
  APK/AAB, Play Games plugin, dan server top-up nyata.
- Parity skill/rig bespoke per hero/boss dan cinematic Pygame. Lihat
  [batas migrasi core](GODOT_CORE_MIGRATION.md).
