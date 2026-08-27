# Mystic Arena — MOBA Tower Defense (pygame → Android)

Game tower-defense/MOBA berbasis **pygame-ce**, 54 level, 200+ boss,
6 hero dengan skill Q/W/E/R, dan 20+ tema peta.
Repositori ini berisi versi yang sudah disiapkan untuk **Android /
Google Play**, dengan kontrol **layar sentuh penuh**.

> 📖 Panduan lengkap langkah demi langkah (build APK, GitHub Actions,
> publikasi Play Store): **[docs/PANDUAN_ANDROID.md](docs/PANDUAN_ANDROID.md)**

---

## Struktur proyek

```
main.py                  entry point (sentuh + fallback mouse/keyboard)
main_desktop_legacy.py   entry point lama (keyboard + gamepad) — arsip
_core.py                 settings, game, menu, input, UI, dev tools
_entity.py               tower, castle, hero, minion, ai_player
_render.py               map renderer, efek, cinematic, cache font
_system.py               performance, fps, sound, save
splash_screen.py         splash pembuka
ui_theme.py              design system menu: palet, komponen premium, ikon vektor

mobile/                  ◀ LAPISAN BARU KHUSUS ANDROID
├── platform_utils.py    deteksi Android, display SCALED, safe area, jnius
├── cloud_save.py        Cloud Save -> Google Play Games Saved Games
├── touch.py             mesin gesture: tap / long-press / drag / fling
├── hud.py               tombol layar: skill QWER, shop, pause, skip
├── debug.py             overlay FPS + crash handler ke file
├── perf.py              cache font/teks, darken/flash, pool, preset kualitas
└── spritecache.py       cache sprite (opsional - lihat catatan hasil ukur)

src/                     Java bridge Cloud Save (dikompilasi oleh p4a)
└── io/github/.../CloudSaveBridge.java  Play Games v2 Snapshots API

bosses/                  base_boss, boss_data, level1..level54
heroes/ hero_skills/     renderer & skill hero
levels/                  konfigurasi 54 level
map_components/          palet, tema, generator, renderer peta
minions/ towers/         renderer unit & menara
ui_components/           panel, popup, shop, notifikasi

buildozer.spec           konfigurasi build Android
p4a-recipes/pygame-ce/   resep kompilasi pygame-ce untuk Android
.github/workflows/       CI: APK debug tiap push, AAB release tiap tag
bosses/_boss_index.py    peta boss→modul (dibuat tools/gen_boss_index.py)
tools/                   benchmark, uji cache sprite, generator indeks
```

## Hero procedural HD

Semua hero tetap dirender murni dari kode (tanpa sprite gambar eksternal),
namun memakai **HD readability pass** setelah `smoothscale`: ukuran badan
lebih mudah dibaca pada layar 720p dan outline solid 1 px dibentuk ulang
setelah resize. Outline hanya dihitung saat cache miss, sehingga frame cache
berikutnya tetap berupa satu operasi blit dan efek aura transparan tidak ikut
menjadi tebal. Warna tepi memiliki bias biru/merah tipis agar kedua tim mudah
dibedakan ketika unit bertumpuk.

### Contoh maksimal: Kaizen Masterwork

Kaizen menjadi hero pertama yang menerima renderer procedural tingkat lanjut.
Tubuh lama dibangun ulang sebagai **bone rig 2D berlapis** dengan siluet
3/4 samping: ponytail berumbai, scarf dinamis, stance berkaki terpisah dengan
tabi/sandal, saya katana berlapis lacquer, obi braided, wajah ber-scar, serta
katana melengkung dengan garis temper *hamon*. Pose idle, walk, attack dan
arah katana dihitung dari sendi/parameter animasi; slash bertumpuk dan skill
angin tetap dihasilkan dari primitive pygame dan masuk pipeline cache normal.

Preview karakter dan skill:
[docs/kaizen_masterwork_preview.png](docs/kaizen_masterwork_preview.png).
Contact sheet rig idle/walk/attack:
[docs/kaizen_animation_strip.png](docs/kaizen_animation_strip.png).

Uji regresi: `python tools/test_hero_hd_render.py` dan
`python tools/test_kaizen_masterwork.py`.

## Item Forge (16 item, 2 halaman TIER I / TIER II)

Hero punya 6 slot item yang dibeli dengan GOLD di **ITEM FORGE**.
Semua item terinspirasi item MOBA legendaris dengan nama diganti
bebas hak cipta; lihat [hero_items.py](hero_items.py).

| TIER I (4500G) | TIER II (4500-6000G) |
|---|---|
| Dead Edge (crit) | Scarlet Bulwark — block + aura Guard tim |
| Holy Rapier (rontok saat mati) | Monarch Wings — evasion 28% |
| Demon Maw (lifesteal + Blood Frenzy) | Corroder — kikis 6 armor target |
| Leviathan Heart (+35% HP, regen) | Tempest Vane — kebal 2.5 dtk saat kritis |
| Cleave Axe (splash melee) | Fenrir Chain — root AOE + sambaran petir |
| Steel Aegis (aura armor/AS) | Sanguine Thorn — Soul Rend: silence + crit pasti |
| Moon Shard (+60 AS) | Abyss Breaker — bash stun + Overwhelm |
| Octarine Core (CDR + spell vamp) | Thunder Coil — chain lightning + Static Charge |

Mekanik baru yang didukung engine: `evasion`, `damage block`,
`armor shred`, `damage amp`, `heal amp`, `slow resist`, `stun/root`
(boss punya resist 55%), dan `move speed` — semua lewat
`TowerDebuffMixin` di [_core.py](_core.py). Screenshot toko:
[docs/item_forge_tier1.png](docs/item_forge_tier1.png) &
[docs/item_forge_tier2.png](docs/item_forge_tier2.png).

## Tactical Commands & Achievement

Perintah taktis untuk semua hero biru (tombol di panel kanan /
hotkey): **GATHER [G]**, **PROTECT TOWER [T]**, **PROTECT CASTLE
[C]**, **ATTACK BOSS [B]**, dan **ATTACK DAMAGE DEALER [D]** —
semua hero fokus menyerang hero musuh dengan total damage terbanyak
(ditrack lewat `hero.damage_dealt` di [_entity.py](_entity.py)).

Achievement hanya dihitung saat **hero membunuh hero lain, mini
boss, atau true boss** (pukulan terakhir harus dari hero). Popup
achievement & combo muncul **di map** (arena), bukan di panel —
kotak notifikasi & kill feed sudah dihapus, panel kanan berisi
command saja. Lihat [tactical_commands.py](tactical_commands.py).

Uji: `python tools/test_gale_morgath.py`,
`python tools/test_achievement_command.py`,
`python tools/test_sidepanel.py`.

Uji: `python tools/test_item_shop.py`,
`python tools/test_item_tier2.py`,
`python tools/test_tier2_ingame.py`.

## Difficulty & AI Hero Pool

- **Easy** — enemy scaling OFF; tiga mini boss level muncul pada wave
  unik yang diacak di rentang **20-40** setiap run.
- **Normal** — enemy scaling OFF; mini boss diacak pada wave **11-30**.
- **Hard** — enemy scaling ON; mini boss diacak pada wave **11-30**.

Pada Level N, pool summon hero AI berisi semua starter hero serta semua
mini boss dan true boss dari Level 1 sampai N-1. AI memilih starter secara
acak, menjamin draft boss pertamanya berasal dari level terbaru yang sudah
lewat, lalu memilih dari seluruh pool lama dengan bobot ke level yang lebih
baru. AI menabung gold untuk target itu agar tidak selalu membeli boss Level
1 yang paling murah.

Uji regresi: `python tools/test_easy_mode_ai_pool.py`.

## Save — Google Play Games (satu-satunya fitur save)

Save pemain **hanya** lewat **Google Play Games Saved Games** — sama
seperti game komersial. Fitur save lokal lama (backup export/import
ke folder Download, Android Auto Backup ke Google Drive) sudah
dihapus/dimatikan:

- `mobile/cloud_save.py` — logika Python (status, auto-upload, poll).
- `src/io/github/dharmawantoxi/mysticarena/CloudSaveBridge.java` —
  bridge Java ke Snapshots API (Play Games Services v2).
- `buildozer.spec` — dependency `play-services-games-v2` + `src`;
  `android.allow_backup = False` (Auto Backup Drive mati supaya
  restore selalu datang dari Play Games).

Alurnya: tiap `SaveManager.save`, isi slot working copy lokal
diunggah otomatis ke **Google Play Games Saved Games** milik akun
Google pemain. Saat game dibuka di HP baru dengan akun Google yang
sama, game mendeteksi slot kosong lalu menawarkan **RESTORE** dari
cloud.

### Cara mengaktifkan (direncanakan saat rilis ke Play Store)

Kamu sudah siap rilis ke Play Store nanti; cukup siapkan akun **Google
Play Console** saat game selesai:

1. **Google Play Console → Game services →** game ini → aktifkan
   **Saved Games**.
2. Salin **Project ID** (angka di halaman Configuration).
3. Sambungkan OAuth client Android (`package name` =
   `io.github.dharmawantoxi.mysticarena`, SHA1 ikut **App signing
   keystore** yang dipakai Play Console).
4. Masukkan Project ID saat build:
   - GitHub Actions: tambah **secret/repository variable**
     `MYSTIC_GAMES_PROJECT_ID`.
   - Build lokal: `MYSTIC_GAMES_PROJECT_ID=123456789012 buildozer android debug`
     (atau file `android_games_app_id.txt` yang di-ignore Git + env
     `MYSTIC_GAMES_PROJECT_ID_FILE` menunjuk ke file itu).
5. Build APK/AAB seperti biasa. Kalau Project ID belum diisi, aplikasi
   tetap jalan — cloud NONAKTIF (game bisa dimainkan, tapi tanpa
   save cloud).

### Tombol di dalam game

Settings → **☁ CLOUD SAVE**:
- **SIGN IN TO CLOUD** — masuk Google Play Games.
- **UPLOAD SAVE KE CLOUD** — kirim progres saat ini (dengan konfirmasi).
- **DOWNLOAD SAVE DARI CLOUD** — ambil progres cloud (dengan konfirmasi).

Auto-upload berjalan di background setiap save; kegagalan cloud tidak
pernah menghilangkan working copy lokal.

## Menjalankan di PC

```bash
python -m venv .venv && source .venv/bin/activate
pip install pygame-ce
python main.py                       # mouse + keyboard
MYSTIC_FORCE_TOUCH=1 python main.py  # simulasikan layout HP
```

## Membangun APK

```bash
pip install buildozer "cython<3.0"
buildozer android debug        # APK untuk uji di HP
buildozer android release      # AAB untuk Play Store
```

## Hasil optimasi (terukur, headless di CPU desktop)

| | Sebelum | Sesudah |
|---|---|---|
| Adegan intro boss | 29,4 ms/frame (34 FPS) | **5,4 ms/frame (185 FPS)** |
| Waktu buka aplikasi | 3,50 s | **0,14 s** |
| RAM saat start | 100 MB | **39 MB** |
| Modul boss dimuat saat start | 54 | **0** (impor malas) |

Rinciannya di [docs/PANDUAN_ANDROID.md § 3](docs/PANDUAN_ANDROID.md).

## Perkakas

```bash
python tools/bench_mobile.py       # benchmark adegan intro + uji gesture/HUD
python tools/bench_heavy.py        # benchmark gameplay (--quality low/high)
python tools/bench_minions.py      # skala jumlah minion
python tools/test_spritecache.py   # uji kebenaran cache sprite (piksel)
python tools/gen_boss_index.py     # regenerasi indeks boss setelah tambah boss
python tools/_shot_ui.py           # screenshot headless semua layar menu
python tools/_shot_game_ui.py      # screenshot headless UI in-game
python tools/_shot_endgame.py      # screenshot victory/defeat/popup toko
```

## Aset yang harus ada

`assets/fonts/` (Cinzel.ttf, Barlow-*.ttf), `assets/sounds/*.wav|ogg`,
`assets/icon.png` (512×512), `assets/presplash.png`.
Tanpa font/suara game tetap jalan (ada fallback), tanpa
`icon.png`/`presplash.png` build tetap jalan dengan gambar bawaan.

## Kontrol sentuh

| Aksi lama (keyboard/mouse) | Aksi baru (sentuh) |
|---|---|
| Klik kiri | Ketuk |
| Klik kanan | Tahan 0,45 detik |
| Scroll wheel | Geser vertikal + inersia |
| Q / W / E / R | 4 tombol skill di kanan bawah |
| H (shop) | Tombol SHOP kiri bawah |
| ESC (pause) | Tombol ⏸ kanan atas |
| SPACE (skip cinematic) | Ketuk layar / tombol LEWATI |
| F8 (FPS) | Tombol FPS kanan atas (4 mode debug) |
| R / N (ulangi / lanjut) | Tombol di layar menang/kalah |
