# TACTICAL CONTRACT — perintah taktis pemain (blue)

Status: **dimigrasikan** dari `tactical_commands.py` (1051 baris) ke
`scripts/match/tactical_commands.gd`, dipakai pertandingan nyata lewat
`scripts/match/prototype_battle.gd` → `scripts/simulation/prototype_session.gd`
→ `scenes/prototype/prototype_screen.gd` / `prototype_view.gd`.

Sumber baca-saja (jangan diubah): `tactical_commands.py`,
`_core.py::InputHandler.handle_key`/`handle_key_up` (tuts), `_core.py::Game.update`
(urutan tick), `_core.py::Game.__init__` (instansiasi), `main.py` + `mobile/hud.py`
+ `mobile/sidepanel.py` (panel HOLD), `_entity.py::credit_hero_damage` dan
`Hero.move_to`/`Hero.update` (state hero yang diperintah).

## 1. Lima perintah

| Perintah | Tuts desktop | Tombol panel | Efek sumber | Suara (tidak silent) |
|---|---|---|---|---|
| `gather` | `G` / `F` (titik kursor, ikut kursor selama ditahan) | `GATHER [G]` | semua hero biru `move_to` cincin spread `35 + (i%3)*15`, `follow_target`/`target` dikosongkan | `ui_click` 0.8 |
| `protect_tower` | `T` (tower biru terpilih bila ada) | `PROTECT TOWER [T]` | 2–3 hero terdekat ke tower paling terancam; spread `30 + i*10` | `ui_click` 0.8 |
| `protect_castle` | `C` | `PROTECT CASTLE [C]` | semua hero cincin `80 + (i%2)*30` di sekitar castle, di-clamp `x 50..1230`, `y 50..670` | `ui_click` 0.8 |
| `attack_boss` | `B` | `ATTACK BOSS [B]` | semua hero mengunci `active_boss` (`follow_target` + `target`) lalu `move_to` cincin `range*0.5 + i*8` | `hero_skill` 0.9 |
| `attack_damage_dealer` | `D` | `ATTACK DMG DEALER [D]` | sama, target = hero merah AI hidup dengan `damage_dealt` terbesar (`max` Python → maksimum PERTAMA) | `hero_skill` 0.9 |

Aturan visibilitas panel disalin dari `mobile/sidepanel.py`: tombol disembunyikan
kalau syaratnya belum ada (`alive_heroes > 0`, `>= 1`, `has_boss`, `has_enemy_hero`),
dan perintah yang sedang ditahan mendapat sorotan + chip `HOLD`.

## 2. Timer & state (identik dengan sumber)

| Nilai | Angka | Arti |
|---|---|---|
| `COOLDOWN_MAX` | 30 tick | jeda antar perintah; gagal terbit → `max(cooldown, 15)` |
| `COMMAND_TICKS` | 600 | durasi perintah aktif (10 detik) |
| `MARKER_TICKS` | 150 | penanda titik kumpul di map (2.5 detik) |
| `FEEDBACK_TICKS` | 180 | banner teks umpan balik (3 detik) |
| `HOLD_TAP_MAX_FRAMES` | 20 | di bawah ini = TAP (durasi normal dipertahankan) |
| `HOLD_RELEASE_TAIL` | 30 | ekor yang tersisa saat HOLD panjang dilepas |
| `GATHER_PUSH_DELAY_FRAMES` | 240 | HOLD gather: push bersama mulai detik ke-4 |
| `AUTO_CHECK_TICKS` | 90 | evaluasi AUTO-PROTECT tiap 1.5 detik |

Urutan `update()` disalin persis: decrement `cooldown` → `command_timer` (habis →
`active_command`/`command_target` dibersihkan) → `gather_point_timer` (habis →
titik kumpul dilepas) → `feedback_timer` → penegakkan HOLD → follow-up GATHER →
AUTO-PROTECT. `Game.update` memanggilnya setelah pass reward dan SEBELUM
`self.ai.update(...)`; `prototype_battle.step_tick()` menaruh `tactical.update()`
di posisi yang sama (setelah `_step_hero_respawns()`, sebelum dispatch AI).

## 3. HOLD vs TAP

* `hold_start` menerbitkan SEKARANG dengan umpan balik penuh, lalu `update()`
  menerbitkan ulang **senyap** tiap `cooldown <= 0` selama masih ditahan, jadi
  durasi 600 tidak pernah habis dan hero tidak kembali ke AI masing-masing.
* Penekanan berulang untuk perintah yang sama (`hold_elapsed > 0`) = no-op
  (anti key-repeat / tombol panel yang ditahan).
* `hold_end(name)` hanya melepas kalau namanya cocok; HOLD ≥ 20 tick memotong
  `command_timer` ke `min(timer, 30)`, TAP membiarkan 600 berjalan.
* HOLD tetap **dipersenjatai** walau syarat belum ada (mis. belum ada boss):
  keberhasilan PERTAMA diumumkan sekali secara loud (`cooldown = 0` → replay loud).
* `main.py` melepas semua hold saat pause / app background; di rebuild ini
  `PrototypeSession.cancel_pending_input()` memanggil `tactical.hold_end()`.
* Input lewat antrean `tactical_queue` sesi (press+release bisa jatuh di tick
  yang sama), dieksekusi sebelum `world.step_tick()` — sama seperti KEYDOWN yang
  selalu mendahului `Game.update`.

## 4. GATHER follow-up push

* HOLD: tiap tick mulai `hold_elapsed >= 240`, bila ≥ 60% hero sudah tiba dalam
  100 px dari titik kumpul dan ada musuh → semua hero mengunci musuh terdekat
  (`follow_target` + `destination = None`; `target`, `destination_auto`,
  `is_retreating` SENGAJA tidak disentuh sumber) dan banner
  `GATHER ATTACK! N heroes push together!` muncul.
* Setelah push, refresh HOLD memakai `_gather_hold_push`: mengunci ulang musuh
  terdekat; bila musuh habis → regroup senyap ke `hold_args` (atau titik kumpul).
* **Quirk sumber yang dikunci fixture**: cabang `command_timer == 300` tidak
  pernah tercapai untuk TAP, karena `gather_point` sudah dilepas di tick 150
  (`MARKER_TICKS`). Push nyata hanya lewat jalur HOLD. Port mempertahankan
  struktur dan akibatnya apa adanya (lihat skenario
  `gather_tap_marker_expires_before_push`).

## 5. Pemilihan target

* `_find_most_threatened_tower`: `enemies_near(220) * 10 + (1 - hp_ratio) * 15`,
  `+2` bila `x < 400`, sort descending **stabil**; bila skor terbaik `== 0` →
  tower dengan hp_ratio terendah (stabil).
* `_count_enemies_near`: minion merah hidup + hero merah **milik AI** hidup
  (`game.ai.heroes`, bukan semua hero merah) + boss merah dihitung **2**.
* `_find_nearest_enemy_target`: boss hidup dicek pertama (tanpa cek team di
  sumber), lalu tower merah, lalu hero merah AI; minion HANYA bila belum ada
  target besar; castle merah jadi fallback terakhir. Pembanding `<` ketat dengan
  seed `9999` → seri dimenangkan yang ditemukan lebih dulu (boss).
* Fallback tower untuk `protect_tower`: sort `(-x, hp_ratio)` stabil.
* Semua sort Python yang stabil direproduksi dengan dekorasi indeks + tie-break
  indeks (sort GDScript tidak dijamin stabil).

## 6. AUTO-PROTECT (tanpa perintah aktif, cooldown 0, tiap 90 tick)

1. Castle: `hp_ratio < 0.4` dan `enemies_near(300) >= 2` → `protect_castle`.
2. Tower: `hp_ratio < 0.6 && enemies_near(250) >= 2`, ATAU `enemies_near >= 4`
   → sort `(-enemies, hp_ratio)` → `protect_tower`.
3. Boss: hidup, `hp_ratio < 0.8`, `wave_number >= 11` → `random() < 0.2` →
   `attack_boss`. Roll native memakai `RandomNumberGenerator` ber-seed
   (`SPAWN_SEED`) atau `auto_roll_override` di test; stream Godot TIDAK diklaim
   identik dengan Mersenne Twister CPython, hanya ambang 0.2 yang dikunci.

## 7. `damage_dealt` (input ATTACK DAMAGE DEALER)

`_entity.credit_hero_damage(source, amount)` dipanggil setiap `take_damage`
(minion, hero, tower, castle, boss) SETELAH mitigasi, dengan `int(amount)`
(truncate ke nol) dan skip bila `amount <= 0` atau `source is None`. Port:

* `scripts/combat/unit_state.gd` → `var damage_dealt := 0` (atribut dinamis
  sumber ada di semua entitas, jadi disimpan di UnitState).
* `scripts/combat/minion_battle.gd::_credit_damage_dealt` dipanggil dari
  `_deliver_hit` tepat setelah `hp` berkurang (jalur bersama melee/proyektil/AOE/
  item). `source_id == -1` = `source=None` sumber (pantulan Bristleback, resep
  boss) → tidak ada kredit.
* `scripts/match/prototype_battle.gd::_deliver_hit` cabang BossState mengkredit
  `dealt` (post-cap), sama dengan `bosses/base_boss.py`.
* Burn/DOT tidak mengkredit apa pun di kedua codebase (tidak ada source).

## 8. Deviasi yang disengaja

1. `Vector2` Godot f32: semua aritmetika formasi dihitung di double dan baru
   menjadi `Vector2` pada panggilan terakhir (`order_move`), jadi nilai tujuan
   sama sampai presisi f32 (fixture merekam nilai f32).
2. Jarak dihitung `sqrt(dx*dx + dy*dy)` di double, bukan `Vector2.distance_to`
   (f32); sumber memakai `math.hypot`. Skenario oracle menjaga margin dari
   ambang sehingga hasilnya identik.
3. `AudioManager` hasil migrasi audio tidak punya parameter volume; hanya NAMA
   suara (`ui_click`, `hero_skill`) yang dipertahankan. Volume sumber (0.8/0.9)
   direkam fixture sebagai kontrak.
4. `_set_feedback` sumber juga memanggil `ui.add_notification` (no-op di sumber)
   dan `effects.add_damage_number` (presentasi). Rebuild menyimpan teks/warna/
   timer banner; `draw_ui` diport ke `prototype_view.gd` (fade in/out 30 tick,
   bayangan, bingkai) dan `draw_world` (lingkaran 50→26, titik pusat, garis
   putus-putus 3 segmen bila jarak > 80). Pulse memakai jam dinding seperti
   `pygame.time.get_ticks()` — presentasi saja, di luar domain deterministik.
5. `command_bar` desktop (`ui.draw_tactical_commands`) memang DINONAKTIFKAN di
   sumber ("hanya di side panel"), jadi rebuild menampilkan tombol ala panel
   side panel + tuts desktop, bukan bar HUD baru.

## 9. Bukti parity

* `tests/tactical_source_oracle.py` — menjalankan `TacticalCommandManager` ASLI
  (modul itu tidak mengimpor pygame) terhadap stub entitas: 58 skenario, 142
  snapshot, plus tabel truncation `credit_hero_damage` dari AST `_entity.py`.
  Fixture: `tests/fixtures/tactical_source.json`.
* `tests/tactical_checks.gd` — replay fixture yang sama di GDScript (stub world
  duck-typed + kelas state asli), membandingkan scalar exact: state perintah,
  timer, destination/follow/target/retreat per hero, teks & warna feedback,
  `get_status_text`, suara, keputusan AUTO-PROTECT; plus kredit damage lewat
  jalur damage nyata.
* `tests/tactical_scene_checks.gd` — lifecycle scene: tuts G/T/C/B, tombol panel
  (press/release = hold), visibilitas tombol ala side panel, HOLD vs TAP, hero
  benar-benar berjalan di `step_tick`, pause melepas hold, match selesai menolak
  perintah, restart mereset manager, draw marker/banner tidak mengubah state,
  tidak ada node bocor.
* `tests/validate_project.py` — guard drift fixture + keharusan registrasi suite
  + `tactical.update()` di world + akumulator `damage_dealt` + oracle di CI.
* CI: `.github/workflows/godot-rebuild.yml` menjalankan oracle ini dan trigger
  path-nya mencakup `tactical_commands.py`.
