# Migrasi `tactical_commands.py` ke Godot

`tactical_commands.py` (1051 baris) adalah **sistem perintah taktis** tim biru: GATHER, PROTECT TOWER, PROTECT CASTLE, ATTACK BOSS, ATTACK DAMAGE DEALER, plus mode HOLD (perintah ditegakkan ulang tiap 0,5 detik selama tombol ditahan) dan evaluasi otomatis yang memproteksi castle/tower saat terancam. Isinya 2 kelas (`TacticalCommand` = 5 konstanta, `TacticalCommandManager` = 28 method), 9 assign modul (3 konstanta HOLD + 6 fallback basis/layar), dan 3 impor (`settings` di dalam `try/except`, `math`, `random`).

Port domain-nya sudah ada — `scripts/match/tactical_commands.gd` (lapisan command) dan `scripts/ui/tactical_layout.gd` (lapisan visual, layer 9bi2) — dengan oracle eksekusi 10 kasus perilaku. Layer **9co** menutup sisanya: **seluruh 47 simbol diklasifikasikan eksplisit**, tiga callback presentasi yang hilang dikembalikan, dan oracle sekarang **merekam panggilan efek** sehingga kehilangan itu tidak bisa terulang diam-diam.

Sumber kebenaran: `godot_rebuild/tests/tactical_command_source_oracle.py` (menjalankan `TacticalCommandManager` asli di atas aktor berbentuk sumber; `--write` menulis dua fixture). Fixture: `tests/fixtures/tactical_command_source.json` (10 kasus perilaku, kini termasuk efek) dan `tests/fixtures/tactical_commands_inventory.json` (inventaris + klasifikasi). Suite native: `tests/tactical_command_checks.gd`, dibantu `tests/recording_effects.gd`.

## 1. Ringkasan

| Ukuran | Nilai |
| --- | --- |
| Baris `tactical_commands.py` | 1051 |
| Kelas | 2 |
| Method | 28 |
| Assign modul | 9 (3 konstanta HOLD + 6 fallback `settings`) |
| Impor | 3 (`settings` dalam `try/except`, `math`, `random`) |
| Simbol terklasifikasi | **47** |
| Kasus perilaku yang dipin | 10 |
| Panggilan efek yang dipin | 11 (10 angka feedback + marker burst) |

| Kind | Jumlah | Arti |
| --- | --- | --- |
| `ported` | 29 | 28 method + RNG |
| `data` | 12 | 3 konstanta HOLD, 5 nama perintah, `RED_BASE_X/Y`, `SCREEN_WIDTH/HEIGHT` |
| `folded` | 4 | `settings`, `math`, `_issuers` → `match`, `draw` → dua op list |
| `dead` | 2 | `BLUE_BASE_X`, `BLUE_BASE_Y` (didefinisikan, tidak pernah dibaca) |

## 2. Klasifikasi simbol

Tabel lengkap (47 baris: nama → kind → target → token hidup) ada di
`godot_rebuild/tests/fixtures/tactical_commands_inventory.json`, dan validator 9co memastikan
setiap token masih ada di berkas targetnya. Ringkasannya:

| Kelompok | Target native | Contoh token |
| --- | --- | --- |
| Konstanta HOLD + nama perintah | `scripts/match/tactical_commands.gd` | `const HOLD_TAP_MAX_TICKS := 20`, `const GATHER := "gather"` |
| Basis/layar | `scripts/match/tactical_commands.gd` | `const RED_BASE := Vector2(1180, 100)`, `const SCREEN_WIDTH := 1280` |
| 28 method | `scripts/match/tactical_commands.gd` | `func step_tick(world: Object) -> void:`, `func status_text(world: Object) -> String:` |
| `_get_command_color` | dua tempat | `func command_color() -> Color:` + `tactical_layout.command_rgb()` |
| `draw_world` / `draw_ui` | `scripts/ui/tactical_layout.gd` (9bi2) | `static func world_ops(`, `static func feedback_ops(` |
| `draw` (wrapper legacy) | `scenes/prototype/prototype_view.gd` | `TacticalLayout.feedback_ops(` |
| `settings` | `scripts/data/core_settings.gd` | `DATA_PATH` |
| `math` | `scripts/match/tactical_commands.gd` | `Vector2.from_angle(` (hypot/sin/cos/pi → vektor + `TAU`) |

Sembilan helper native yang tidak punya padanan langsung di sumber (`set_cursor`,
`_attack_target`, `_blue_towers`, `_is_blue_tower`, `_stable_distance_sort`, `_refuse`,
`_display_name`, `_explosion`, `_cursor_in_bounds`) juga dipin di fixture (`native_only`)
supaya differensi struktural ini tetap terlihat, bukan tersembunyi.

## 3. Yang ditutup di layer ini

| Celah | Perbaikan |
| --- | --- |
| Marker burst GATHER hilang | `_command_gather` memanggil `_explosion(world, point)` → `effects.add_death_explosion(x, y, "blue", "small")`, urutan setelah feedback seperti sumber |
| Marker burst PROTECT CASTLE hilang | `_command_protect_castle` memanggil `_explosion(world, castle.position)` |
| Volume suara diabaikan | `AudioRuntime.play` → `play_scaled` dengan `SOUND_CLICK_VOLUME := 0.8` (3 tempat) dan `SOUND_SKILL_VOLUME := 0.9` (2 tempat), sesuai `SoundManager().play(..., volume_mult=...)` |
| Gerbang kursor follow-mouse | `_cursor_in_bounds()` meniru `0 <= mx < 1280 and 0 <= my < 720`; konstanta `SCREEN_WIDTH`/`SCREEN_HEIGHT` kini ada di port |
| Efek tak terlihat oleh tes | stub `Effects` di oracle kini **merekam** `add_damage_number` / `add_death_explosion`, fixture memuat `state.effects`, dan `tests/recording_effects.gd` merekam hal yang sama di sisi native |

Sebelumnya ketiga callback itu tidak terlihat: sumber membungkusnya dengan `try/except`, oracle lama menelan panggilannya, dan port tanpa ledakan tetap lolos semua tes.

### Catatan lintas layer

`const SCREEN_WIDTH := 1280` / `const SCREEN_HEIGHT := 720` di
`scripts/match/tactical_commands.gd` sekarang menjadi pin **pertama** (pencocokan nama paling
spesifik) untuk dua konstanta `settings` di tabel `parity` milik layer 9cf. Karena itu
`tests/fixtures/core_source.json` diregenerasi dengan `python3
godot_rebuild/tests/core_source_oracle.py --write`: hanya 2 dari 16 baris `parity` berubah
target — `SCREEN_HEIGHT` dari `scenes/splash/splash_screen.gd` (`const HEIGHT`) dan
`SCREEN_WIDTH` dari `scripts/ui/boss_entrance_layout.gd` → `scripts/match/tactical_commands.gd`
baris 34/35. Nilai (1280×720) tidak berubah, `data/core/settings.json` identik, dan
`core_checks.gd` tetap memverifikasi literal tiap baris, jadi ini atribusi pin yang lebih tepat,
bukan regresi.

## 4. Deviasi terdokumentasi

| Kode | Hal | Deviasi | Alasan |
| --- | --- | --- | --- |
| D1 | `_set_feedback` notifikasi | hanya banner + angka kritikal (640, 100) yang diport | `_core.add_notification` mengembalikan `None` dan `sidepanel.beri_tahu_global` mengembalikan `False` — keduanya no-op di sumber |
| D2 | nama target di `get_status_text` | memakai `display_name` hero/structure, bukan atribut `name` pygame | rebuild tidak menyimpan `name` pygame; panjang tetap dipotong 15 karakter |
| D3 | `_get_command_color` | `Color` di runtime, array RGB di `tactical_layout.command_rgb()` | op list butuh array agar dibandingkan piksel-per-piksel dengan oracle 9bi2 |
| D4 | `_issuers` | dict dispatcher → `match` di `issue()` | struktur data Python tidak perlu dibawa; perilaku sama |
| D5 | `draw_world`/`draw_ui`/`draw` | produsen op list, bukan blit surface | Godot menggambar lewat node; oracle 9bi2 membandingkan op |
| D6 | `random.random() < 0.2` | `RandomNumberGenerator` ber-seed + hook `boss_auto_roll_override` | GDScript tidak bisa di-seed dari `random` Python; hook membuat tes deterministik |
| D7 | `try/except` di `_auto_evaluate_protect` | guard `world != null` / tipe | GDScript tidak punya exception; sumber hanya mencetak error lalu lanjut |
| D8 | `hold_start(name, *args, **kwargs)` | parameter eksplisit (`point`, `has_point`, `target_id`, ...) | varargs Python tidak bisa dipetakan; pemanggil native memakai bentuk yang sama |

## 5. Cara menjalankan

```bash
python3 godot_rebuild/tests/tactical_command_source_oracle.py --write   # tulis kedua fixture
python3 godot_rebuild/tests/tactical_command_source_oracle.py           # cek 10 kasus + 65 fakta inventaris
python3 godot_rebuild/tests/tactical_draw_source_oracle.py              # op visual (9bi2)
python3 godot_rebuild/tests/validate_project.py                         # blok 9bi2 + 9co
godot --headless --script tests/run_all.gd                              # suite native (PC/CI)
```

`tests/tactical_command_checks.gd` me-replay 10 kasus perilaku (penerimaan perintah, formasi,
target, timer, latch hold/push, auto-protect), kini termasuk **daftar panggilan efek** yang
dibandingkan lewat `JSON.stringify`, lalu memeriksa inventaris 47 simbol, konstanta
kebijakan (layar, basis, volume suara, tick), dan gerbang kursor.

## 6. Status paritas

Terbukti: perilaku perintah (pemilihan target, formasi, timing hold/push, auto-protect,
akuntansi damage) identik dengan sumber pada 10 kasus yang dijalankan dari kode Python asli;
seluruh 47 simbol terklasifikasi dengan token hidup; panggilan presentasi (angka feedback +
marker burst + volume suara) kini ikut dipin. Belum terbukti: tampilan akhir di layar
(posisi ring/dash/banner pada layar nyata) dan perilaku di perangkat Android — keduanya
butuh run Godot + screenshot seed/state sama, sesuai kriteria paritas proyek. Validator
statis dan fixture **bukan** bukti paritas visual.

`python3 godot_rebuild/tests/validate_project.py` → **PASS: 22942 static checks** (blok
9bi2 + 9co). Dari tiga kegagalan validator sebelumnya: dua adalah artefak string `res://%s` di
`tests/tactical_command_checks.gd` (kini `PROJECT_ROOT + entry.target`), satu adalah drift
`core_source.json` yang dijelaskan di §3.
