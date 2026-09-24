# AUDIT ULANG DARI AWAL — Godot vs Pygame (tanpa dokumen migrasi)

> **PATOKAN TUNGGAL paritas Godot ↔ Pygame per 2026-09-23 (diperbarui 2026-09-24).**
> Dokumen migrasi/paritas lama **dan** work-log per-fitur + PNG review di
> `docs/` telah **dihapus** dan tidak boleh lagi dijadikan acuan:
> - baseline lama: `GODOT_PARITY.md`, `GODOT_MIGRATION.md`, `MIGRASI_1_1.md`,
>   `MIGRASI_1_1_REPORT.md`, `PARITY_AUDIT.md`, `AUDIT_PARITAS.md`
> - work-log: `*_GODOTPP.md`, `*_PY_COVERAGE.md`, `*_V2_RENDERER.md`,
>   `*_V3_COMBAT_FX.md`, `*_V4_*.md`, `BOSS_HERO_SMOOTH_PARITY.md`, dan PNG
>   review di akar `docs/` (isi lamanya masih di riwayat git).
> Yang **tetap ada** di `docs/`: patokan ini, runbook operasional
> (`PANDUAN_ANDROID.md`, `PLAYSTORE_RELEASE.md`, `GDEXT_VERIFIKASI_LOKAL.md`,
> `GODOT_DEBUG_DI_GITHUB.md`, `CARA_CONVERT_TANPA_HAPUS_PYGAME.md`,
> `PERF_ANDROID_LOWEND.md`, `PERF_FX_BENCH.md`, `balance_audit.md`,
> `hero_kategori.md`), plus `workflow_transaksi/` (screenshot alur bayar).
> Laporan mesin (bukan patokan): `docs/GODOT_PYGAME_SYNC_REPORT.md`
> (`tools/godot_pygame_sync.py --report md`) dan `docs/VISUAL_PARITY_REPORT.md`
> (`tools/visual_parity_audit.py --report md`).

**Tanggal audit:** 2026-09-23
**Metode:** Membandingkan kode sumber Pygame secara langsung dengan kode/data Godot,
**TANPA** membaca dokumen migrasi/paritas lama (kini sudah dihapus, lihat di atas).
Semua klaim di bawah diverifikasi dari kode + data mentah.

Pygame = sumber kebenaran (root repo). Godot = port (`godot/`).
**Aturan oracle tetap berlaku (warisan `MIGRASI_1_1.md`):** Pygame adalah sumber
kebenaran tunggal — Godot HANYA membaca; sumber Pygame tidak pernah disunting
untuk menyesuaikan Godot. Semua perbaikan dilakukan di sisi Godot.

---

## LANGKAH AUDIT (step by step)

| # | Langkah | Cara cek | Hasil |
|---|---------|----------|-------|
| 1 | Petakan struktur kedua engine | `ls` + hitung berkas | Pygame: 4 modul inti (_core 10.281 baris, _entity 6.536, _render 3.671, _system 1.125) + 6 bundle data/renderer (50.311 baris). Godot: 9 paket skrip + 14 grup scene + 17 JSON data + 44 parity test |
| 2 | Bandingkan katalog hero | `get_all_hero_types()` Pygame vs `godot/data/heroes.json` | **222/222 kunci sama, semua stat combat identik** |
| 3 | Bandingkan arketipe hero | `hero_archetypes.ARCHETYPES` vs `hero_archetypes.json` | **222/222 kunci + nilai identik** |
| 4 | Bandingkan katalog boss | `boss_data.get_all_boss_types()` vs `bosses.json` | **216/216; hp/damage/warna cocok**; Godot menambah armor/MR/label_top precomputed |
| 5 | Bandingkan level | `level_data.ALL_LEVELS` vs `levels.json` | **54/54 semua field skalar identik**; mini_bosses sama (beda format kunci int→string) |
| 6 | Bandingkan item | `hero_items.ITEM_CATALOG` vs `items.json` | **33/33 kunci + nilai identik** |
| 7 | Bandingkan ekonomi | Konstanta `_core.py` vs `economy.json` | **9/9 identik** (gold 350, 3/dtk, +0.3/level, +100/level, mult 1.25/1.0/0.75, wave 1500f, delay 20f, max 5 hero) |
| 8 | Lokalisasi | `localization._TEXT` vs `Localization.gd` const TEXT | **209 kunci × 2 bahasa, semua nilai identik** (5 kunci multi-baris dicek manual — utuh) |
| 9 | Menu & state | `MenuState` vs enum State MainMenu.gd | **8/8 state sama** |
| 10 | Isi Settings | `_draw_settings` vs `_build_settings` | Semua baris ada di dua engine: 4 slider volume, difficulty, screen shake, damage numbers, game speed, bahasa, FPS limit, reset save; Godot Cloud Save menambah sign-in, upload/download, status, dan restore terkonfirmasi |
| 11 | Perintah taktis | `tactical_commands.py` vs `TacticalCommands.gd` | **5/5 perintah + semua konstanta HOLD identik** (240/600/150/180/90/30 frame) |
| 12 | Smart-AI boss | `def _smart_ai` di `base_boss.py` vs BossKit.gd + flag `uses_smart_ai` | **79/79**; BossKit.gd di-generate 1:1 (7.081 baris) |
| 13 | Skill hero | `hero_skills/_bundle.py` vs HeroSkillKit.gd | Di-generate 1:1 (5.806 baris); `--check` generator lulus |
| 14 | Jalankan oracle perilaku | `tools/godot_pygame_sync.py` (tanpa stub) | **PASS** — fixture cocok: 54 level, 50 komposisi wave, 25 kombinasi minion/nexus, 216 boss-core, 79 smart-AI (237 skenario), trace skill hero |
| 15 | Konstanta hardcoded | langkah [6/7] sync tool | **PASS** (FIRST_WAVE 300, RESPAWN 600, HUNT 900, AGGRO 250, RETREAT 0.20/0.80, FPS 60) |
| 16 | Aset visual bake | `tools/visual_parity_audit` + hitung file | **455 unit PNG + 54 map PNG + 20 props PNG ada**; fresh-check tak bisa jalan di sandbox ini (numpy tidak ada) — isi file tetap ada |
| 17 | SFX/BGM | `assets/sounds/` (23 wav + lisensi) vs AudioManager.gd | Katalog 1:1; converter menyalin ke `godot/assets/sounds/` (di-gitignore; ekstensi diluruskan 16 wav + 7 ogg + 1 mp3) |
| 18 | Fitur mobile | `mobile/*.py` vs godot autoload/scene | vibrate/safe-area/long-press/debug overlay 4-mode **SUDAH (2026-09-23, Fase 32)**; particle_ratio budget **SUDAH (2026-09-24, Fase 34)**; cloud save kini dipindah ke `CloudSaveManager` + Android v2 plugin (runtime perlu Project ID/OAuth dan uji perangkat) |
| 19 | Perilaku mikro | baca kode target menara, forge, popup | Ditemukan **3 gap nyata** (lihat checklist belum-sama) |
| 20 | Meta/topup | `topup_*`, `_system.SaveManager`, meta_gold | Save 3 slot + meta_gold paritas; multi-currency topup ✅ **1:1 sejak 2026-09-24** (`TopupCurrency.gd` = port `topup_currency.py`, 20 mata uang + deteksi locale + riwayat `cur`/`price_cur`) |

---

## CHECKLIST — SUDAH SAMA ✅

### A. Data (lapisan konten) — 100%
- [x] **Hero 222/222** — semua stat combat (cost/hp/damage/speed/range/attack_cooldown/skill_cooldown/skill_damage/skill_range) identik per hero
- [x] **Arketipe hero 222/222** — dmg_type/playstyle/tier/power identik
- [x] **Boss 216/216** — stat dasar (hp/damage), warna, nama skill identik; field armor/MR/min_distance Godot = hasil precompute dari aturan Pygame
- [x] **Level 54/54** — semua field (mult musuh, gold awal, reward meta, mini/true boss, tema map, bgm, syarat unlock) identik
- [x] **Item 33/33** — cost, stats, kategori, drop-rule, flag melee/magic identik
- [x] **Minion 5 jenis** — goblin/orc/troll/undead/dark_rider: hp/dmg/speed/range/cd/gold/radius sama
- [x] **Ekonomi 9/9 konstanta** — starting gold, gold/detik, bonus level, mult kesulitan, interval wave, spawn delay, max hero
- [x] **Lokalisasi 209 kunci × id+en** — semua nilai string identik (fallback id, template `{nama}` sama)
- [x] **Konstanta gameplay hardcoded** — FIRST_WAVE/RESPAWN/HUNT/AGGRO/RETREAT/FPS cocok (audit statis PASS)
- [x] **Tower 14 definisi** (towers.json) + nexus 4 — dikunci oracle & parity test
- [x] **Katalog audio 23 SFX + BGM** — AudioManager membaca katalog yang sama (converter menyalin file)

### B. Perilaku gameplay (dikunci oracle PASS + 44 parity test)
- [x] **Alur match** — roster kosong → beli hero → wave minion → mini boss → true boss → victory/defeat
- [x] **Oracle match parity** — 54 level, 50 komposisi wave, 25 kombinasi minion+nexus, 216 rekaman boss-core, 79 rekaman smart-AI (237 skenario), trace skill hero: **PASS**
- [x] **Smart-AI boss 79/79** — rantai `_smart_ai_*` di-port generate ke BossKit.gd
- [x] **Skill hero** — HeroSkillKit.gd generated 1:1 dari hero_skills/_bundle.py (QWER 6 starter + boss-hero generik); auto-cast r→e→w→q, CDR, spell vamp
- [x] **Perintah taktis 5/5** — gather / protect_tower / protect_castle / attack_boss / attack_damage_dealer + mode HOLD (tap<0,33s vs tahan), re-issue tiap 0,5 dtk
- [x] **Respawn, timer wave, aggro/retreat AI hero** — konstanta identik
- [x] **Damage & mitigasi** — armor/MR, crit, block, evasion, item proc (dikunci ItemProcParityTest), death dispatch, reward kill
- [x] **Difficulty & enemy scaling** — mult gold 1.25/1.0/0.75, scaling musuh khusus `hard`
- [x] **Game speed** — 0.5/1.0/1.5/2.0 via Engine.time_scale
- [x] **Adaptive quality** — transisi HIGH↔MEDIUM↔LOW dari rata-rata FPS (window 90 frame)

### C. Menu, settings, save
- [x] **Menu state 8/8** — main, slot_select, level_select, hero_shop, settings, how_to_play, credits, pause
- [x] **Settings lengkap** — 4 slider volume (+catatan voice tanpa aset di KEDUA engine), difficulty (+kunci LOCKED run), screen shake, damage numbers, game speed, bahasa id/en, FPS limit, tombol reset save
- [x] **Save 3 slot** — file per slot, migrasi save lama ke slot 1, info slot, format playtime, hapus slot
- [x] **Meta progression** — meta_gold, reward win/replay/repeat, unlock level berurutan
- [x] **Hero shop menu** — katalog 222 hero, harga, arketipe tier/power
- [x] **Topup dialog** — pilih paket, metode bayar, simulasi pembayaran, redeem voucher + keypad layar
- [x] **Layar game over** — judul menang/kalah, statistik, popup unlock hero (slide-in delay 90 frame)
- [x] **Input controller** — ControllerManager (796 baris) + ControllerRouter (573) + parity test input

### D. Visual & sinematik (struktur 1:1, piksel lewat bake)
- [x] **Banner intro boss** — strip 600×92, timeline 100 frame (fade 12/slide 18/fade-out 20), skip SPACE/ESC/klik ditelan
- [x] **Animasi mati boss** — fase pause 90f (true)/60f (mini), white flash 15f, gelombang cincin
- [x] **Level intro, wave announcer (WavePlate), combo counter+badge, achievement popup** — semua ter-wire lewat signal
- [x] **Screen shake kamera** — model trauma (maks, bukan jumlah; 1.0 = 60 px)
- [x] **KillFeed DIHAPUS di dua engine** — paritas (sengaja)
- [x] **Floating text/damage number, HitSpark, DeathBurst, PathPreview** — ada padanan
- [x] **FPS overlay (F8)** — panel + grafik histori, layout di-port persis; ops gambar dikunci fixture
- [x] **Aset bake** — 455 PNG unit (hero/boss/minion/tower/nexus), 54 PNG map, 20 PNG props — semuanya hasil render Pygame
- [x] **Lighting** — Lighting.gd + LightingCompat (preset tema map)
- [x] **HUD lengkap** — HUD, ShopPanel, SkillBar, SidePanel, TouchHUD, VirtualCursor, BossPlate/BossOverlay

---

## CHECKLIST — BELUM SAMA ❌

### Gap perilaku nyata (berdampak gameplay/fitur)
- [x] **1. Antrean forge item untuk hero MATI** — ✅ **DITUTUP 2026-09-23.** Pygame: beli item untuk hero mati → antre `pending_forge_items` → terkirim saat respawn (`hero_items.py:3143`, dikirim `_core.py:2184`). Perbaikan Godot: field `_pending_forge_items` dideklarasikan di Hero.gd (akar masalah lama: properti dinamis tidak tersimpan di Node); `GameManager.itemshop_target_hero()` kini memprioritaskan target-tersimpan→terseleksi→hidup→mati persis `_resolve_shop_target`; `try_buy_item` mengantre item untuk hero mati dengan kapasitas `count+pending < 6`; pengiriman + recalc stat dipanggil di `_update_hero_respawns` (urutan paritas respawn→deliver); chip strip BUY FOR hero mati diaktifkan + badge `queued`; hint `dead_delivery_hint`/`queued_item_count` tampil di tab. Integrasi dikunci `GameplayParityTest` (antre 5 item → FULL ke-6 → respawn → 6 slot terisi).
- [x] **4. Tie-break target menara** — ✅ **DITUTUP 2026-09-23.** `CombatSystem.nearest_enemy` mendapat parameter `last_wins_ties` dan SEMUA call site dipetakan per padanan Pygame-nya: Tower/Nexus/Hero-attack/Hero-aggro kini `<=` (kandidat terakhir menang, `_entity.py:864-869/:1744-1749/:3663-3670/:3726-3731`); Hero-hunt dan Boss tetap `<` (`_entity.py:3707-3714`, `base_boss.py:688-692`).
- [x] **2. Multi-currency top-up** — ✅ **DITUTUP 2026-09-24.** Pygame: **20** mata uang (IDR, USD, EUR, GBP, SGD, MYR, THB, VND, PHP, JPY, KRW, CNY, AUD, CAD, BRL, INR, MXN, ZAR, AED, SAR — daftar lama di baris ini menulis "21" padahal tabel `IDR_PER_UNIT` `topup_currency.py:21-42` berisi 20 kunci, dan tidak ada HUF/TRY/NZD seperti yang kadang dikutip dari varian lama modul) + deteksi locale perangkat (pyjnius di Android → `locale.setlocale` di PC → env `LC_ALL`/`LC_CTYPE`/`LANG`), region dulu baru bahasa, fallback `USD`. Godot: `scripts/systems/TopupCurrency.gd` (port 1:1 semua tabel + `format_price`/`convert_idr`/`parse_locale_name`/`device_locale`/`currency_for`), `HudLayout.round_half_even_scaled` + `has_sign_bit` (satu-satunya pembulat uang; ties-to-even bit-eksak — `round()` engine mengubah `"¥93"`/`"₩870"` pada angka tie), dan `TopupDialog.gd` (`currency` = padanan `Game.topup_currency`, deteksi malas sekali di `_ready`, `_price_str` delegasi, riwayat beli menyimpan `cur` + `price_cur` 2 desimal seperti `_core.py:6107-6119`; redeem tetap `"IDR"`/0 seperti `:6065-6072`). **Bug nyata yang ikut ditutup:** dialog Godot mencetak `"Rp10.000"` — spasi simbol pygame (`"Rp "`) hilang, jadi label harganya tidak pernah identik walau mata uangnya IDR. Quirk yang sengaja DIPERTAHANKAN: lookup kurs tanpa normalisasi kapital (`convert_idr(x, "idr")` jatuh ke USD), `VND 0.62` per unit (`10.000 rupiah = "₫16,129"`), koma tetap koma untuk VND, `-0.00003` dolar tetap `$-0.00`, dan simbol "C$" dipakai CNY sekaligus CAD. Deviasi engine + alasan: 5 butir di header `TopupCurrency.gd` (tidak ada pyjnius/`setlocale`; `DisplayServer.get_locale()` + env; `MYSTIC_FORCE_LOCALE` untuk tes headless; badan `detect_currency` dipecah jadi fungsi murni; `None`→`""`). Dikunci `tools/test_godot_topup_currency_parity.py` (137 pin sumber + menjalankan modul pygame asli untuk 581 kasus fixture **dan** shadow-run 623 cek atas algoritma Godot, karena CI linter tidak punya engine) + `godot/tests/TopupCurrencyParityTest.tscn`. **Masih terbuka, di luar gap ini:** pygame mencetak `[TOP UP] +50.000 Hero Gold (PAKET 50K via GOPAY, USD 0.62, simulasi)` ke konsol (`_core.py:6133-6134`) dan Godot tidak punya baris log itu; dan blokir cloud-save (#3) belum tersentuh.
- [x] **3. Cloud save (Google Play Games)** — ✅ **Port Godot (2026-09-24).** `CloudSaveManager.gd` reuses payload magic/version + Python-compatible SHA-256 canonical JSON, polls the Java status-file bridge, best-effort uploads after a local save, validates downloads before any write, and stages slot restores with backup/rollback. Settings now exposes Play Games sign-in, upload/download, status, and a confirmation dialog (including the empty-install restore prompt). Android implementation is a Godot v2 AAR + `EditorExportPlugin`; `MYSTIC_GAMES_PROJECT_ID` or the root `android_games_app_id.txt` injects the required `game_services_project_id` resource / `APP_ID` metadata. Headless Python and Godot parity tests cover schema/checksum/provider/restore. **Still requires a real Play Games Project ID, matching OAuth package/SHA-1, Saved Games enabled, and on-device sign-in/snapshot verification before release.**

### Gap mobile/Android
- [x] **5. Vibrate/haptic** — ✅ **DITUTUP 2026-09-23.** Pygame: `mobile/platform_utils.py:142` `vibrate(ms=25)` (pyjnius Vibrator), dipanggil hanya dari dua tempat: `main.py:412` tahan tombol jeda **30 ms** dan `main.py:368` sentuhan yang ditangkap rail kanan **15 ms**. Godot: `MobileLayout.vibrate(ms)` -> `Input.vibrate_handheld(ms)`, mengembalikan false di luar mode sentuh (paritas `if not IS_ANDROID: return False`), dan dipanggil dari DUA titik yang sama (`Main._dispatch_gesture` tahan-jeda 30 ms; `SidePanel._on_pause_pressed` + `_open_shop` 15 ms). Deviasi: Godot tidak bisa menanya keberadaan vibrator, jadi `true` = "permintaan diteruskan ke engine". butuh izin `VIBRATE` di preset ekspor. Dikunci pin statik di `tools/test_godot_mobile_touch_parity.py` (jumlah + milidetik getar tidak bisa berubah sendiri).
- [x] **6. Safe-area (poni/cutout)** — ✅ **DITUTUP 2026-09-23.** Pygame: `platform_utils.get_safe_area()` = rect aman `(28, 10, 1280-56, 720-20)` HANYA di mode sentuh, rect penuh 1280x720 di desktop; dipakai overlay debug di tiga tempat (`debug.py:256/290/393`). Godot: `MobileLayout.safe_area()` dengan angka yang sama (`SAFE_MARGIN_LOGICAL 28`, `SAFE_TOP/BOTTOM 10`) + gerbang `AppShell.touch_mode()` yang sama; `DebugOverlay` mengambil rect ini dari `state_snapshot()` untuk mini/full/grafik, jadi titik jangkar panel ikut sama. Catatan yang harus tetap terbaca: pygame TIDAK membaca `WindowInsets` asli, hanya margin tetap — port ini sengaja TIDAK menambah `DisplayServer.screen_get_safe_area()` di atasnya (aturan proyek: paritas, bukan melampaui pygame); kalau nanti mau ditingkatkan, satu fungsi itu tempatnya. Dikunci fixture (`safe_area` dari `get_safe_area()` sungguhan) + regex rumus di kedua sumber.
- [x] **7. Gestur long-press** — ✅ **DITUTUP 2026-09-23.** `scripts/systems/TouchGestures.gd` adalah padanan 1:1 `mobile/touch.py`: `TAP_SLOP 14` (geser < 14 px masih tap), `LONG_PRESS_MS 450` (`>=`, sekali per tekanan lewat `long_fired`), `DOUBLE_TAP_MS 280` + radius 40 px, notch scroll setiap `SCROLL_STEP 42` dengan AKUMULATOR berisi sisa (bukan dinolkan), fling saat `moved and |v| > 4`, inersia `*= 0.9` sampai `|v| <= 0.6`, maks 3 notch per frame, kecepatan `0.6*lama + 0.4*baru`, dan `dispatch_button` = `dispatch_to_game` (tap->1, long_press->3, scroll->4/5, sisanya 0). Mouse dipakai sebagai jalur utama (juga di Android), `InputEventScreenTouch/Drag` dihitung untuk diagnostik dan menelan kembarannya — persis alasan yang ditulis `touch.py:120-135`. Rantai tahan-jeda (overlay debug + getar, `main.py:404-413`) dipindah apa adanya, TERMASUK urutannya yang dicek sebelum filter `claimed`. Gerbang klaim press memakai `_input`+`_unhandled_input`, bukan `_unhandled_input` saja, karena Godot memberi event ke Control di tengah. Dikunci 14 skenario replay di `tests/MobileTouchParityTest.tscn` (termasuk 449,9 vs 450 ms, 40 vs 41 px, dua jari, cancel, dan inersia per frame).
- [x] **8. Overlay debug mobile 4-mode** (off/mini/full/graph, `mobile/debug.py`) — ✅ **DITUTUP 2026-09-23.** `scenes/ui/DebugOverlay.gd` memindahkan aturan `mobile/debug.py`: `toggle = (mode+1)%4` + `[DEBUG] overlay = <nama>`, `set_mode = mode%4` (mode negatif pun jatuh ke 3 lewat `posmod`), `enabled = mode != OFF`, riwayat 180 sampel fps + frame-ms, `peak`, `frame_ms > 33`, tangga warna fps `>=50` hijau / `>=30` kuning / selain itu merah, mini `"%3.0f FPS  %4.1fms"` di `(safe.left+6, safe.top+6)` dengan panel `(-4,-3)`/`(+12,+8)` dan teks `(x+2, y+1)`, panel lengkap lewat BUFFER OPAQUE `(8,8,14)` + tepi `(90,90,120)` 1 px (`+18`/`19`/`+12`, teks di `(8, 6+19i)`), teks disegar maksimal 4x/dtk (`JEDA_SEGAR_MS 250`), grafik 240x70 di `safe.top+145` dengan skala TETAP 50 ms + panduan 16,7/33,3 ms + poly-line `(150,220,255)`, GRAFIK = LENGKAP + grafik, cincin jari `(90,220,255)` r=26 tebal 2 + titik putih r=3 yang datanya dibaca dari `TouchGestures.points`. Konsumennya disatukan: **tombol FPS di TouchHUD, tahan jeda, dan F8** semuanya mengiklusi mesin ini; overlay Label ad-hoc di `HUD.gd` DIHAPUS (dulu rute paralel yang bikin angka dua engine berbeda jadi tiga). `FpsCounter.gd` (`_system.py`, jalur desktop legacy) tetap ada + tetap dikunci `tests/SystemPerfParityTest`, tapi bukan lagi target F8, dan komentar yang menyatakan gap ini terbuka sudah diperbarui. Isi baris yang sumber datanya khusus pygame (konversi sprite, fastblit, cache memori/font, `blitwatch`, `perf.PHASES`) TIDAK dirender — daftar lengkap + alasan di `godot/README.md` (Fase 32). Format baris yang tersisa dibandingkan VERBATIM, dan geometri panel dibandingkan dengan jejak `pygame.draw.*`/`blit` sungguhan.
- [x] **9. Particle ratio budget** — ✅ **DITUTUP 2026-09-24 (Fase 34).** `mobile/perf.py` pygame punya tiga lapis penurun beban partikel, dan ketiganya kini dipindah 1:1: (1) **preset** — `AppShell.PARTICLE_RATIO` 0.20/0.40/0.70 untuk low/medium/high + `particles_enabled()` = `not low`, dipasang di `_detect_quality` dan `_apply_quality` (paritas `Quality.apply`, perf.py:555-561); (2) **governor beban combat** — `scripts/systems/FXLoadGovernor.gd` memindah `set_fx_load`/`fx_load`/`reset_fx_load` (smoothing 0.40, `(1.0/n) ** 1.5` terjepit [0.10, 1.0], n≤1 → 1.0) plus token per frame `claim/refund_fx_particle` cap 140 lantai 56, `claim/refund_fx_projectile` 18/10, `allow_skill_projectile` 10/5, dengan semua quirk: token beku saat aim berubah, nonaktif = tanpa batas, refund saat nonaktif = no-op, `reset` mematikan token + `_load`; (3) **rasio efektif tunggal** — `AppShell.particle_ratio()` = dasar preset × `fx_load()` (properti `Quality.particle_ratio`). Hook frame `_core.py:2888-2892` dipindah ke `GameManager._process` (`set_fx_load(count_busy_fx_units(...))` SEBELUM `spark_fx.advance`) + reset di `start_level` di samping `spark_fx.reset()`; hitungan sibuk `_fx_busy`/`count_busy_fx_heroes` dipindah dengan tabel 27 nama `_LIVE_FX_HEROES` persis (unit mati dilewati, `int(timer)` membulatkan pecahan ke bawah, proyektil hidup dihitung, hero_type kosong jatuh ke boss_type). Konsumen: `VFXManager` claims untuk ketujuh API bentuk (wall → `null` bila cap skill habis; paritas `_entity.py` yang mengembalikan None), `Hero.gd` menggate kedua jalur proyektil skill (serangan dasar MEMANG tidak digate — paritas `_spawn_projectile`), dan `SparkField.add_hit_particles` satu-satunya pembaca rasio dengan `max(0, _py_round(count*ratio))` + `particles_enabled` (ledakan kematian boss sengaja TETAP 1.0, paritas). **Bug diam-diam yang ikut tertutup:** bayangan `settings.quality` kini ditulis live (`persist=false`), jadi `max_damage_numbers` 8/16/32 di `start_level` membaca preset nyata, bukan default. Deviasi tercatat di header FXLoadGovernor.gd: refund otomatis ala `surplus == ParticleEqual` tidak di-port (butuh 27 modul FX per-boss — gap #11; API refund tetap tersedia), `_FX_BUSY_COUNT`/kuantisasi pose tidak diport (gap #10), `_fx_units` memakai grup `heroes`+`bosses` (Godot tidak punya `active_boss` tunggal yang sama; determinisme busy tetap sama karena penghitungan per-unit), `alive` ↔ `not is_dead`. Dikunci `tools/test_godot_particle_budget_parity.py` — oracle MENJALANKAN `mobile/perf.py` ASLI lewat stub pygame + menyadur AST `_fx_busy`/`count_busy_fx_heroes` dari heroes/__init__.py, tiga skenario claim/refund, kurva governor 36 langkah (termasuk input jahat → `int("`junk"` or 0)` try/except), 10 kasus busy, 123 pin statik dua arah di 11 berkas — plus `godot/tests/ParticleBudgetParityTest.tscn` + fixture `godot/tests/fixtures/particle_budget.json`.
- [ ] **10. Modul perf Android** tanpa padanan Godot: `blitwatch`, `bootcheck`, `buildinfo`, `diagnostics`, `fastblit`, `spritecache` (sebagian besar plumbing spesifik Pygame; `buildinfo/bootcheck` hanya terwakili crash-log AppShell). Sejak Fase 32 overlay debug Godot menampilkan baris BUILD dari `application/config/version` (bukan `mobile/buildinfo.py`) — modulnya tetap tidak diport, hanya kolomnya yang punya padanan.

### Deviasi disengaja / belum setara visual
- [ ] **11. FX skill boss per-boss** — Pygame punya 27 modul FX khusus (`heroes/*_fx.py`: abaddon_fx, ignis_drachorn_fx, dst). Godot mengganti SEMUA dengan aproksimasi generik `KitShockRing.gd` (komentar kode sendiri: *"bukan salinan piksel renderer pygame"*).
- [ ] **12. Struktur toko dalam match** — Pygame: item shop fullscreen terpisah dengan halaman (SHOP_PAGES) + toko tower/hero berbeda. Godot: panel terpadu 4 tab (tower/item/hero/nexus). Perilaku harga/item sama; **layout berbeda**.
- [ ] **13. Target pembelian item** — Pygame item shop punya state target hero internal; Godot membeli untuk hero yang dipilih via GameManager (chip hero strip).
- [ ] **14. Cakupan penyimpanan settings** — Pygame: settings GLOBAL (settings.json, berlaku semua slot). Godot: settings disimpan **per slot** (bahasa, volume, difficulty, speed ikut slot). Deviasi tercatat di SaveManager.gd:613-617.
- [ ] **15. Animasi slide-in popup menara** — `PopupAnimation` (\_render.py:1202, dipakai `_core.py:2577`) tidak punya padanan Godot; popup menara muncul tanpa animasi.
- [ ] **16. Permukaan UI untuk sebagian kunci lokalisasi** — komentar Localization.gd:41-44: kunci notifikasi forge / banner toko / detail item / chip MATI-antrean diport sebagai DATA saja karena **permukaan UI-nya belum ada** di port Godot (konsisten dengan gap #1).
- [ ] **17. Modul C++ GDExt tidak aktif** — 7 modul (levels, lighting, maps, mobile, skills, splash, ui) teruji paritas di CI, tetapi `project.godot` mematikan SEMUA flag (`use_gdext_*=false`); runtime pemain = GDScript. (Bukan bug — jalur akselerasi opsional.)
- [ ] **18. File audio tidak ikut di repo Godot** — `godot/assets/sounds/` di-gitignore; pemain/dev harus menjalankan converter agar suara ada (16 wav + 7 ogg + 1 mp3 hasil pelurusan ekstensi). Bake PNG unit/map/props SUDAH ter-commit.
- [ ] **19. Sertifikasi piksel runtime** — visual unit/map dijamin lewat bake (deretan PNG dari renderer Pygame), tetapi FX runtime (skill, hit, glow, komposit HUD) diimplementasikan ulang di Godot; belum ada bukti screenshot piksel-per-piksel end-to-end untuk itu.
- [ ] **20. Server payment (`server/app.py`)** — tooling sisi Pygame/PC; tidak ada padanan (dan memang di luar scope port Godot).

### Catatan kesetaraan "sama-sama tidak ada" (bukan gap)
- Slider Voice aktif di dua engine tetapi **tidak ada aset voice di dua-duanya** — paritas absen.
- `main_desktop_legacy.py` = launcher desktop lawas Pygame; Godot satu launcher — bukan gap.

---

## KESIMPULAN

| Lapisan | Status |
|---|---|
| Data konten (hero/boss/level/item/minion/ekonomi/teks) | ✅ **1:1 penuh** — diverifikasi kunci-per-kunci & nilai-per-nilai |
| Perilaku gameplay inti | ✅ **1:1 berlapis oracle** — fixture PASS (54 level, 216 boss, 79 smart-AI, trace skill) |
| Menu/settings/save/topup (struktur) | ✅ Hampir penuh (settings per-slot = deviasi tercatat; topup multi-currency penuh) |
| Visual struktural (sinematik, HUD, popup, shake) | ✅ 1:1; piksel unit/map lewat bake |
| FX skill boss (piksel) | ⚠️ Aproksimasi generik, bukan salinan |
| Fitur Android (vibrate, safe-area, long-press, debug overlay 4-mode) | ✅ **Ditutup 2026-09-23** (Fase 32) — `TouchGestures/DebugOverlay/MobileLayout` |
| Fitur Android (cloud save) | ✅ Port code selesai (conditional pada konfigurasi Play Games; perlu uji perangkat) |
| Forge item untuk hero mati | ❌ Belum di-wire (fitur Pygame nyata) |
| Multi-mata-uang topup | ✅ **Ditutup 2026-09-24** (Fase 33) — `TopupCurrency.gd` + `TopupDialog.gd`, diunci `test_godot_topup_currency_parity.py` |
| Tie-break target menara | ⚠️ Beda operator `<=` vs `<` |

**Status akhir: BELUM 1:1 penuh** — progres per 2026-09-24:
gap **#1 (forge hero mati)**, **#2 (multi-currency top-up)**, **#3
(cloud save)**, **#4 (tie-break)**, **#5-#9 (rantai fitur mobile dan
particle ratio budget)** ✅ implementasi ditutup.
Sisa terbuka: konfigurasi + verifikasi perangkat nyata untuk Play Games,
modul perf spesifik Pygame (#10), satu baris log `[TOP UP]` yang belum punya
padanan Godot, sejumlah deviasi disengaja, dan sertifikasi piksel FX runtime
yang masih terbuka.

Urutan prioritas penutupan gap berikutnya:
1. ~~Forge queue hero mati~~ ✅ selesai
2. ~~Tie-break menara~~ ✅ selesai (dipetakan per call site: `<=` untuk
   tower/nexus/attack/aggro, `<` tetap untuk hunt/boss)
3. ~~Long-press + overlay debug mobile 4-mode + vibrate (satu rantai fitur)~~
   ✅ selesai 2026-09-23 (`TouchGestures.gd`, `DebugOverlay.gd`,
   `Main._dispatch_gesture`, `MobileLayout.vibrate`; diunci
   `tools/test_godot_mobile_touch_parity.py` + `tests/MobileTouchParityTest.tscn`)
4. ~~Safe-area layout~~ ✅ selesai 2026-09-23 (`MobileLayout.safe_area()` =
   `(28, 10, 1224, 700)` di mode sentuh, dipakai jangkar overlay debug)
5. ~~Multi-currency topup~~ ✅ selesai 2026-09-24 (Fase 33 —
   `scripts/systems/TopupCurrency.gd` port 1:1 `topup_currency.py`,
   `HudLayout.round_half_even_scaled` untuk pembulatan ties-even,
   `TopupDialog.currency` + riwayat `cur`/`price_cur`; diunci
   `tools/test_godot_topup_currency_parity.py` +
   `godot/tests/TopupCurrencyParityTest.tscn`)
6. Cloud save backend.
7. ~~Particle ratio budget~~ ✅ selesai 2026-09-24 (Fase 34 —
   `scripts/systems/FXLoadGovernor.gd` port 1:1 governor `mobile/perf.py`
   (smoothing/exp/lantai token 140-18-10/56-10-5 + token nonaktif = gratis),
   `AppShell` preset 0.20/0.40/0.70 × fx_load + shadow `settings.quality`,
   hook `GameManager._process` + reset `start_level`, gate skill proyektil di
   `Hero.gd`, rasio tunggal di `SparkField`); diunci
   `tools/test_godot_particle_budget_parity.py` +
   `godot/tests/ParticleBudgetParityTest.tscn`)
8. FX boss per-boss (27 modul) bila ingin klaim piksel 1:1.
