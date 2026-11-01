# Verifikasi migrasi entity Godot

Tanggal: 2026-11-01.

| Pemeriksaan | Hasil lokal |
|---|---|
| Persiapan aset/metadata main | 54 level; 32 aset; `--check` lulus |
| Persiapan data core | 54 level, 222 hero, 216 boss, 33 item; `--check` lulus |
| Persiapan entity kit/sprite | 2 kit; 222 unit, 10 minion, 8 tower, 2 nexus; `--check` lulus |
| Tes exporter core | 4 unittest lulus |
| Tes exporter main | 2 unittest lulus |
| Tes exporter entity | 3 unittest lulus |
| Oracle cloud Python | 18 lulus, 0 gagal |
| Guardrail proyek/sumber | 139 pemeriksaan lulus |
| `gdparse` | 45 berkas GDScript lulus |
| `gdlint` | 43 berkas non-generated lulus |
| `gdformat --check` | 43 berkas non-generated sesuai |
| Runtime native headless | **195 pemeriksaan lulus, 0 kegagalan** |
| Boot scene utama headless | Splash → menu berjalan; exit 0 |
| Diff hygiene | `git diff --check` lulus |

## Lingkungan uji lokal

Engine uji dikompilasi dari source resmi Godot tag `4.7.2-stable`, target Linux
headless tanpa GPU/audio backend (`vulkan=no`, `disable_3d=yes`, tanpa
X11/Wayland/ALSA/PulseAudio). Versi engine melaporkan
`4.7.2.stable.custom_build`. Binary rilis official tidak dapat diunduh di sandbox
karena host redirect unduhan berada di luar allowlist jaringan. Uji runtime memakai
cache kelas global dan `application/run/main_loop_type=MysticTestRunner` sementara
melalui `override.cfg` yang dihapus setelah tes. Scene utama diuji lewat konfigurasi
proyek normal tanpa override tersebut.

## Cakupan tes entity

- Hero melee/ranged normalization, school damage, dan state kit.
- Projectile hero homing dan bullet tower (slow/impact).
- Boss per-hit cap, tenacity, enrage, entrance, dan dispatch smart-AI.
- AIPlayer: draft, reserve, build/upgrade, item, shield, nexus, lane.
- Item auto-trigger HP kritis dan saran katalog.
- Manifest bake unit/minion/tower/nexus dan jalur PNG.
- Suite core/shell: state, clock, gesture, save, cloud, voucher, top-up, tactical,
  wave, dev mode, CoreGame, HUD, audio nonfatal.

## Belum diverifikasi lokal

- `--editor --import` dan `--script` pada binary Standard official: disiapkan di
  CI dan harus dilihat pada PR/commit terkait.
- Rendering GPU, audio terdengar, controller fisik, Android nyata, signing,
  APK/AAB, Play Games plugin, dan server top-up nyata.
- Parity piksel penuh rig/cinematic Pygame dan seluruh passive item lanjutan.
  Lihat [batas migrasi entity](GODOT_ENTITY_MIGRATION.md).

Peringatan `ObjectDB instances were leaked at exit` dapat muncul saat engine
headless keluar cepat. Ini bukan error script; CI memperlakukan
`SCRIPT ERROR:`/`ERROR:` sebagai kegagalan, bukan peringatan cleanup Dummy backend.
