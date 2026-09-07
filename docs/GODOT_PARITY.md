# Status paritas Godot ↔ Pygame

**Acuan perilaku adalah versi Pygame di repository ini. Godot belum setara
sepenuhnya.** Data catalog yang sama, sprite hasil bake, dan build Android yang
berhasil tidak membuktikan bahwa alur permainan, UI, atau efeknya sudah sama.

Dokumen ini membedakan koreksi yang diuji dari bagian port yang masih parsial.
Roadmap lama di `GODOT_MIGRATION.md` mencatat implementasi komponen, bukan
sertifikasi paritas seluruh game.

## Koreksi alur pertandingan — 7 September 2026

| Bagian | Godot sebelumnya | Perilaku sekarang / acuan Pygame |
|---|---|---|
| Roster awal | 6 hero gratis per tim | Kedua tim mulai kosong. Pemain dan AI membeli hero dengan gold (`Game.reset`, `AIPlayer.__init__`). |
| Unlock awal | Keenam starter langsung terbuka | Save baru mendapat Kaizen. Unlock pada save lama **tidak dicabut**. Unlock permanen hanya izin membeli, bukan summon gratis. |
| Pembelian hero | API menerima hero terkunci, duplikat, dan roster tanpa batas | Catalog valid, unlocked, gold cukup, satu hero per tipe, maksimal 5 hero **termasuk yang mati**. Spawn pemain di depan toko Radiant (`Game.try_buy_hero`). |
| Kematian hero | Node dihapus; satu tim habis memulai ulang seluruh arena setelah 3 detik | Hero yang sama respawn setelah 10 detik di base sendiri. Level, item biasa, dan statistik tetap. Holy Rapier rontok. Debuff dan cast tertunda dibersihkan. Nexus, tower, wave, dan progres boss tidak direset (`Game.update`, `Hero.respawn`). |
| Waktu respawn | Callback timer bisa bertahan melewati restart/pause | Timer milik match, membeku ketika pause/intro, dibuang saat restart/menu. |
| Wave pertama | Langsung, termasuk selama intro | Persiapan 5 detik **setelah** intro dilewati; mulai pada wave 0 (`Game.reset`). |
| Wave berikutnya | Otomatis setiap 25 detik walau wave sebelumnya hidup | Interval 25 detik adalah minimum. Antrean kedua tim dan semua minion hidup harus sudah habis (`Game.update_waves`). |
| Spawn minion | Satu komposisi dibagi ke tiga lane, spawn serentak, cap 24/tim | Satu komposisi penuh **per lane**, urutan top → mid → bot, interval 20 frame/60 FPS per tim. Tidak memotong wave elite yang berisi 33 minion/tim. |
| Komposisi wave | Tabel diindeks nomor wave | Tabel diindeks **level nexus tim sendiri**, lalu tambahan elite pada wave 4/7/10/13 (`Game._get_wave_composition`). |
| Stat minion | Skala dari nexus terkuat kedua tim + bonus 8%/wave | HP/damage, kecepatan, cooldown, gold reward, regen dan prioritas target mengikuti level nexus sendiri. Hard scaling diterapkan hanya pada minion merah ketika spawn (`Minion.__init__`, `Game.update_waves`). |
| Jalur minion | Lane hanya label; berjalan diagonal ke base lawan | Mulai dari ujung lane yang benar dan mengikuti waypoint maju/mundur sesuai tim (`Minion._move_forward`). |
| Ekonomi AI | Gold awal dan income sama dengan pemain | Mulai dengan `STARTING_GOLD` (350), income `GOLD_PER_SECOND + wave_number`. AI membangun/draft memakai saldo ini (`AIPlayer.__init__`, `Game.update`). |
| Nexus AI | Tidak ada eskalasi wave otomatis | Naik ke level 2/3/4/5 pada wave 4/7/10/13, sebelum menghitung komposisi baru (`Game._auto_scale_ai_castle`). |
| Mini boss | Wave tetap dari JSON | Wave unik diacak tiap match: easy 20–40, normal/hard 11–30, urutan dan tipe boss tetap (`Game._roll_mini_boss_schedule`). |
| Data boss | BossDB hanya hp/damage/speed/range/cooldown/radius | `bosses.json` diekspor converter dari `boss_data.py` + `hero_archetypes`: armor/MR tematik, ability/ability2 (cooldown, damage, range, heal), jarak kiting, dan bendera `uses_smart_ai` hasil AST `Boss.update` — 216 baris cocok dengan oracle Pygame (`BossCoreParityTest`). |
| Resilience boss | Tidak ada; hit besar menembus | `damage_reduction` 30% (true) / 20% (mini), anti-burst cap 8% / 12% max HP, tenacity slow/atk_slow (×0.5, cap 0.35) dan resist stun 55% (`Boss.__init__`, `Boss.take_damage`, `Boss.apply_slow/apply_debuff`). |
| Enrage / Frenzy | Tidak ada | True boss enrage di HP ≤50% (×1.25/×1.25/cd ×0.75 min 18), mini frenzy di HP ≤40% (×1.15/×1.20/cd ×0.80 min 20) + callout + shake; nilai dibandingkan dengan hasil `Boss.update()` Pygame sungguhan di fixture. |
| Entrance boss | Langsung bergerak/menyerang | Freeze entrance 3 s (true) / 2 s (mini); cooldown serangan tidak jalan selama entrance. |
| True boss ability2 | Tidak ada | Heal `max_hp × ability2_heal_pct` saat HP < 30% dengan cooldown ability2. |
| Cleave & ability generik | Serangan dasar hanya kena target | Cleave 40% radius 80 ke musuh lain (netral sekolah); boss tanpa smart-AI memakai `_use_ability` (damage/range/cooldown dari data, lock serangan 60 frame, shake) persis `base_boss.py`. |
| Kaizen | Rig buatan ulang selalu mengalahkan sprite Pygame | Arena normal memakai bake renderer Pygame. Rig alternatif tetap ada di `KaizenDemo.tscn`, atau opt-in `mystic/rendering/experimental_hero_rigs`. |
| Kontrol demo | D/F1/T/SPACE mengubah match normal | Dinonaktifkan default; hanya aktif dengan `Main.enable_debug_controls`. Pilih difficulty di menu sebelum bermain. |

## Belum setara — jangan ditandai selesai

- **UI/HUD/toko/menu:** state dan beberapa transaksi tersedia, tetapi layout,
  popup detail, ikon, navigasi dan interaksi belum sama dengan Pygame.
- **Visual unit:** bake menyamakan sumber pose hero/boss, bukan seluruh komposit
  live FX. Minion, tower dan nexus masih memakai gambar prosedural pengganti.
  Kuantisasi pose, lighting, cuaca dan efek skill juga belum lolos perbandingan
  screenshot menyeluruh.
- **Skill:** enam starter punya implementasi khusus, tetapi masih perlu audit
  koefisien, target dan timing. Banyak boss-hero memakai skill generik.
- **Smart-AI boss musuh (79 tipe):** rantai `elif self.boss_type ==` pada
  `Boss.update` belum diport — Q/W/E/R per boss, efek khas (summon, dash,
  transform, dot/debuff area, dst.) dan visualnya belum ada di Godot. Yang
  sudah setara dan diuji: data 216 boss, resilience + anti-burst, tenacity,
  entrance, enrage/frenzy, heal true boss, cleave, dan ability generik boss
  tanpa smart-AI. Aura ability/enrage gambar Godot belum diverifikasi
  piksel-per-piksel (test `test_boss_true_aura_parity` baru mencakup aura true
  boss).
- **Perintah taktis dan kontrol pemain:** `tactical_commands.py` belum diport;
  kontrol gerak/target dan overlay sentuh Android belum lengkap.
- **Progresi/settings:** kunci difficulty sepanjang run, reset progresi karena
  ganti mode, statistik/achievement, semua pilihan settings dan migrasi/cloud
  save belum setara. Tidak menghapus save pengguna untuk menyamarkan selisih.
- **Android/performa:** lolos tes headless bukan pengujian visual, sentuh,
  performa perangkat, ataupun verifikasi APK/AAB.

## Tes yang menjaga koreksi ini

Dari root repository, dengan `pygame-ce` dan Godot 4.3+ terpasang:

```bash
# Fixture dievaluasi dari fungsi Pygame asli, bukan salinan rumus Godot:
python tools/test_godot_match_parity.py

# Import resource lalu jalankan empat scene regresi:
godot --headless --path godot --editor --import
godot --headless --path godot res://tests/GameplayParityTest.tscn --quit-after 300
godot --headless --path godot res://tests/BattleSmokeTest.tscn --quit-after 180
godot --headless --path godot res://tests/AIPlayerTest.tscn --quit-after 120
godot --headless --path godot res://tests/CinematicTest.tscn --quit-after 960
godot --headless --path godot res://tests/BossCoreParityTest.tscn --quit-after 420
```

`GameplayParityTest` membaca `godot/tests/fixtures/match_parity.json`: ekonomi
54 level × 3 difficulty, 50 komposisi wave, 25 kombinasi minion/nexus, eskalasi
nexus AI dan titik spawn. Tes runtime juga memeriksa pembelian/duplikat/cap,
respawn individu dan team wipe, pause, antrean wave, jalur, restart dan menu.
`BattleSmokeTest` membeli hero melalui API yang sebenarnya, bukan lagi
menganggap roster demo sebagai syarat sukses.

`BossCoreParityTest` membandingkan `godot/data/bosses.json` dengan 216 baris
oracle `boss_core` (stat boss + flag smart-AI dari `Boss.update`, dan nilai
enrage dari pemanggilan `update()` Pygame yang sebenarnya), lalu menguji
perilaku runtime node Boss.gd: resilience/anti-burst, entrance freeze, aggro,
tenacity (slow/atk_slow/stun), heal true boss, cleave, dan ability generik
boss tanpa smart-AI.

Jika aturan Pygame memang berubah, sesuaikan Godot, **kemudian** regenerasi:

```bash
python tools/test_godot_match_parity.py --write-fixture
```

CI `godot-check.yml` memeriksa freshness fixture dan log runtime. Sukses berarti
ada penanda `PASS` **dan** tidak ada `SCRIPT ERROR`, `Parse Error`, atau
`Compile Error`; exit code Godot saja tidak cukup.

### Hasil validasi perubahan ini

- Fixture Pygame dan pemeriksaan GDScript, scene/referensi, serta properti
  partikel lulus. Regresi aura boss, serangan dasar tanpa impact FX, dan AI
  easy-mode Pygame juga lulus.
- Godot 4.3: `GameplayParityTest` **1.453 pemeriksaan lulus**;
  `BattleSmokeTest`, `AIPlayerTest`, dan `CinematicTest` juga `PASS`, tanpa
  error script/kompilasi/animasi. `BossCoreParityTest` lulus di CI dengan
  3.717 pemeriksaan (data 216 boss + perilaku inti boss). Gate kini turut
  menolak animasi yang tidak ada dan body fisika yang belum terdaftar di
  space.
- Engine lokal dibangun dari source untuk **headless saja**, tanpa backend
  Vulkan/OpenGL. Pesan engine `No renderers available` pada lingkungan ini
  adalah batasan build pengujian; hasil di atas **bukan** validasi gambar GPU,
  sentuhan perangkat, atau APK/AAB. CI memakai binary Godot standar.
