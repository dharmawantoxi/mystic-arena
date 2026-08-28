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
Renderer memakai **LOD dua tingkat**: arena mempertahankan siluet/kontras yang
bersih, sedangkan portrait Hero Shop/panel otomatis menambah serat rambut,
bidang wajah, textile weave, jahitan hakama, dan engraving armor. Kedua LOD
tetap 100% procedural.

Preview karakter dan skill:
[docs/kaizen_masterwork_preview.png](docs/kaizen_masterwork_preview.png).
Contact sheet rig idle/walk/attack:
[docs/kaizen_animation_strip.png](docs/kaizen_animation_strip.png).

Uji regresi: `python tools/test_hero_hd_render.py` dan
`python tools/test_kaizen_masterwork.py`.

### Contoh maksimal kedua: Thorne Masterwork

Thorne menerima perlakuan yang sama seperti Kaizen: tubuh lama dibangun
ulang sebagai **bone rig 2D berlapis** — surai quill berumbai dengan
animasi per-quill (flare saat smash), stance berkaki terpisah bercakar,
perut berat ber-sabuk dengan kantong & gesper emas, vest perang sobek,
pauldron baja berlapis dengan duri, kepala babi hutan ber-moncong &
taring, serta gada flanged berduri yang posenya dihitung dari parameter
animasi (wind-up, smash, recovery) lengkap dengan impact spark. Renderer
memakai **LOD dua tingkat** yang sama: arena mempertahankan siluet yang
bersih, sedangkan portrait menambah barb quill, serat bulu, kerut
moncong, alur taring, anyaman vest, jahitan hem, dan goresan pauldron.
Kedua LOD tetap 100% procedural.

Preview karakter dan skill:
[docs/thorne_masterwork_preview.png](docs/thorne_masterwork_preview.png).
Contact sheet rig idle/walk/attack:
[docs/thorne_animation_strip.png](docs/thorne_animation_strip.png).

Uji regresi: `python tools/test_thorne_masterwork.py`.

### Contoh maksimal ketiga: Sylara Masterwork

Sylara mendapat perlakuan yang sama, dan rig lamanya (torso/quiver/hood/
lengan/busur sebagai fungsi terpisah) **dihapus total**, diganti satu
**bone rig 2D berlapis**: cape hijau per-panel dengan lipatan & tepi
robek yang beranimasi angin, quiver berisi anak panah berbulu, korset
kulit-hijau ber-strap dengan gesper emas, boot tinggi bertali, hood
runcing ber-brim dengan rambut merah menyembul, serta **busur recurve
pose-driven**: limb melentur mengikuti tarikan, tali menegang ke nock,
dan anak panah ternock hanya saat tali ditarik (`_bow_nock` menghitung
posisi tangan penarik, jadi lengan benar-benar menempel pada tali).
Seluruh siluet dirender ke buffer lalu diberi **outline gelap 1 px**
seperti sprite sheet referensi. Pose yang tersedia: idle, walk, bow
draw/release, dan windrun (stance dash + speed-line).

**LOD dua tingkat** yang sama: arena memakai siluet bersih, portrait
menambah helai rambut halus, bulu mata, jahitan hood, anyaman korset,
rivet sabuk, serat fletching quiver, dan tali boot. Di portrait,
aura/platform/proyektil dilewati supaya auto-crop terisi wajah &
material, bukan lingkaran efek. Biaya render ±0.8 ms/frame (setara
Thorne) dan tetap 100% procedural — tanpa PNG hero atau `image.load`.

Preview karakter dan skill:
[docs/sylara_masterwork_preview.png](docs/sylara_masterwork_preview.png).
Contact sheet rig idle/walk/attack:
[docs/sylara_animation_strip.png](docs/sylara_animation_strip.png).

Uji regresi: `python tools/test_sylara_masterwork.py`.

### Contoh maksimal keempat: Zephyr Masterwork

Zephyr kini menerima upgrade penuh yang sama: renderer tubuh lama berupa
potongan torso/lengan/rok terpisah **dihapus** dan diganti satu **bone rig
2D berlapis** bertema dark-fey. Rig baru memiliki mahkota rambut crimson
berduri dengan helai individual, dua pasang sayap moth transparan berurat,
mantel asimetris, gaun petal berpanel, tights dan ankle boot yang benar-benar
menapak, korset ber-lacing/rune, serta staff blackwood hidup dengan sulur
duri dan kristal amethyst. Siluet rambut petal kini tersapu ke belakang dan
orb staff berada di samping bahu (bukan melayang di atas kepala), mengikuti
arah pose pada referensi Zephyr. Posisi ujung staff dipakai bersama oleh tangan,
cast flash, magic bolt, dan Casket Curse — jadi semua tetap tersambung ketika
wind-up dan release, bukan dekorasi yang bergerak sendiri.

Pose **idle**, **walk**, dan **cast** menghitung ulang akar tubuh, langkah,
sayap, panel gaun, rambut, tangan, serta staff setiap frame. LOD arena
mempertahankan siluet magenta yang bersih dan hemat; Hero Shop memakai pass
portrait tambahan untuk jahitan hem, jewel, material sayap, circlet, detail
wajah, dan embroidery. Q Bramble Maze, W Shadow Realm, E Casket Curse, dan
R Bedlam tetap memakai timer gameplay yang sama, dengan efek visual baru
yang dibangun penuh dari primitive pygame.

Preview karakter dan skill:
[docs/zephyr_masterwork_preview.png](docs/zephyr_masterwork_preview.png) dan
[docs/zephyr_skills_preview.png](docs/zephyr_skills_preview.png).
Contact sheet rig idle/walk/cast:
[docs/zephyr_animation_strip.png](docs/zephyr_animation_strip.png).

Uji regresi: `python tools/test_zephyr_masterwork.py`.

### Contoh maksimal kelima: Grimjaw Masterwork

Grimjaw (Juggernaut — *The Blade Fury*) kini menerima upgrade penuh yang
sama: kumpulan body-part statis lama (torso/pauldron/head-mask/hair
back-front/left-sword arm/fire sword) **dihapus** dan diganti satu
**bone rig 2D berlapis**. Rig baru memiliki sare api menyala dengan helai
individual, mask putih ber-strip darah, pauldron baja ber-gold dan spike,
sabuk + loincloth merah, serta kaki dan boot perang yang benar-benar
menapak. **Flame blade** menggantikan pedang garis lurus: bilah melengkung
yang sudut, panjang, dan pegangan dihitung dari sendi (wind-up → swing →
recovery), jadi ikut badan saat idle/walk/attack, bukan dekorasi yang
bergeser sendiri.

Pose **idle**, **walk**, **attack**, **Blade Fury (spin)**, dan
**Omnislash** menghitung ulang akar tubuh, langkah, mane, lengan, dan bilah
setiap frame. LOD arena mempertahankan siluet yang bersih dan hemat;
Hero Shop memakai pass portrait tambahan untuk serat rambut, engraving
pauldron, jahitan loincloth, dan ember api. Q Blade Fury, W Healing Ward,
E Critical Strike, dan R Omnislash tetap memakai timer gameplay yang sama,
dengan efek visual yang dibangun penuh dari primitive pygame.

Preview karakter dan pose:
[docs/grimjaw_masterwork_preview.png](docs/grimjaw_masterwork_preview.png).
Portrait LOD Hero Shop:
[docs/grimjaw_portrait_preview.png](docs/grimjaw_portrait_preview.png).
Contact sheet rig idle/walk/attack:
[docs/grimjaw_animation_strip.png](docs/grimjaw_animation_strip.png).

Uji regresi: `python tools/test_grimjaw_masterwork.py`.
Review sheet dirender ulang dengan
`python tools/_shot_grimjaw_masterwork.py`.

### Contoh maksimal keenam: Vex Masterwork

Vex (Outworld Destroyer — *Harbringer of the Void*) kini menerima upgrade
penuh yang sama: kumpulan body-part statis lama (cloak/lower robe/torso/
idle-attack arms/arm segment/hand/staff/head crown/body particles)
**dihapus** dan diganti satu **bone rig 2D berlapis**. Rig baru memiliki
crown void menyala dengan ujung cyan, hood berwajah shadow dengan celah
mata menyala, pauldron armor spiky, robe robek yang mengambang (tanpa
kaki), serta **staff surgawi diagonal** yang posisi orb dihitung dari
sendi (wind-up → release → recovery) — jadi Arcane Orb dan Astral
Imprisonment muncul tepat dari ujung staff, bukan dari pinggang.

Pose **idle**, **walk**, dan **attack** menghitung ulang akar tubuh,
crown, hood, lengan, dan orb staff setiap frame. LOD arena mempertahankan
siluet yang bersih dan hemat; Hero Shop memakai pass portrait tambahan
untuk rim crown, jahitan hood, rune robe, dan ember void. Q Arcane Orb,
W Astral Imprisonment, E Sanity's Eclipse, dan R Essence Flux tetap
memakai timer gameplay yang sama, dengan efek visual yang dibangun penuh
dari primitive pygame.

Preview karakter dan pose:
[docs/vex_masterwork_preview.png](docs/vex_masterwork_preview.png).
Portrait LOD Hero Shop:
[docs/vex_portrait_preview.png](docs/vex_portrait_preview.png).
Contact sheet rig idle/walk/attack:
[docs/vex_animation_strip.png](docs/vex_animation_strip.png).

Uji regresi: `python tools/test_vex_masterwork.py`.
Review sheet dirender ulang dengan
`python tools/_shot_vex_masterwork.py`.

### Contoh maksimal ketujuh: Gornak Masterwork (mini boss + hero)

Gornak — *The Warrior Against Magic*, mini boss level 1 yang juga bisa
di-unlock jadi hero — adalah **boss pertama** yang menerima perlakuan yang
sama. Renderer lamanya (`_draw_gnk_robe`, `_draw_leg`, `_draw_gnk_arm_back/
front`, `_draw_blade`, `_draw_mohawk`: tumpukan body-part `pygame.draw.rect`)
**dihapus total** dan diganti satu **bone rig 2D berlapis** di
`bosses/level1.py`.

Diukur dari render (bukan perasaan), yang salah waktu itu:

| | sebelum | sesudah | rujukan keluarga |
|---|---|---|---|
| badan padat boss 1x | 87 x 53 px | **115 x 121 px** | morgath 82x120, drakar 138x190, abaddon (true) 122x150 |
| rasio lebar:tinggi | 0.61 (tiang sempit) | **1.05** | hero lain 0.90–1.17 |
| hasil di lane sebagai hero | 50 x 45 px, di-*upscale* 1.13x (kabur) | **74 x 79 px, tanpa upscale** | grimjaw 74x79, kaizen 75x83 |
| rune tanah | 110 px, lebih terang dari badan | 58 px di bawah kaki | — |
| biaya render | 1.15 ms/frame | **1.11 ms/frame** | — |

Yang dilakukan:

* **Ukuran disamakan, bukan digedein sembarangan.** `SCALE = 1.32`
  memperbesar rig, `LIFT = 4` memindahkan jangkar ke bawah. `LIFT` penting:
  pipeline HD hero menormalkan ukuran dari **tinggi badan di atas titik
  jangkar**, jadi tanpa LIFT, boss setinggi 115 px akan jadi 99 px di lane
  (lebih gemuk dari Kaizen) atau sebaliknya — sekarang tingginya 74 px,
  sama persis dengan Grimjaw.
* **Siluet diisi ke samping**, bukan cuma tinggi: stance kaki melebar,
  bahu/pauldron keluar, dan kedua bilah dipegang menyamping (depan
  `+1.02`, belakang `-1.02` rad). Itulah yang membuat Kaizen/Grimjaw/Vex
  terasa "penuh"; Gornak sebelumnya menumpuk semua massanya di satu kolom.
* **Kaki menapak.** Telapak dipatok di `GROUND_DY` (garis bayangan) dan
  garis itu sendiri diturunkan dari `FEET_DY * SCALE`, jadi tidak mungkin
  lagi badan melayang saat ukuran diubah.
* **Bilah pose-driven & tidak pernah menembus badan.** Sudut bilah ditabel
  per-pose; ayunan attack ditulis sebagai satu sapuan yang lewat depan
  wajah lalu menyayat ke depan-bawah, sehingga tidak ada frame bilah
  melintang di dada. Ujung bilah = satu-satunya sumber posisi slash arc,
  proc Mana Break, dan kilau Counterspell.
* **LOD dua tingkat.** Arena = siluet bersih; portrait Hero Shop
  (`_portrait_hd`) menambah pass material (serat mohawk, grain kulit,
  jahitan loincloth, ukiran pelat, garis hamon bilah, tato rune) dan
  membuang aura/rune/bayangan supaya auto-crop mengisi wajah.
* **Efek skill ditundukan**: Counterspell jadi kubah heksagon yang memeluk
  badan (bukan bola r=42), Blink memakai after-image rig yang sama, dan
  durasi animasi disamakan dengan `active_skill_timer` AI (`SKILL_DUR`,
  dikunci test). `hurt_flash_timer` boss akhirnya dibaca.
* Buffer rig dibatasi dari extents terukur semua pose (176x160) supaya
  outline siluet (5 salinan per frame) tidak membayar ruang kosong, dan
  ada test yang memastikan tidak ada bilah terpotong.

Preview karakter, ukuran 1x di arena, dan baris paritas ukuran:
[docs/gornak_masterwork_preview.png](docs/gornak_masterwork_preview.png).
Contact sheet rig idle/walk/attack:
[docs/gornak_animation_strip.png](docs/gornak_animation_strip.png).
Portrait LOD Hero Shop: [docs/gornak_portrait_preview.png](docs/gornak_portrait_preview.png).
Perbandingan sebelum/sesudah (baris atas = renderer lama, zoom sama):
[docs/gornak_before_after.png](docs/gornak_before_after.png).
Khusus pass visual jalur hero (lane + Hero Shop, ukuran sengaja tidak
diubah): [docs/gornak_hero_pass.png](docs/gornak_hero_pass.png) —
dirender ulang dengan `python tools/_shot_gornak_hero_pass.py`.

**Pass kedua — visual jalur HERO.** Setelah ukuran aman, keluhan berikutnya
adalah Gornak-as-hero tetap kalah "hidup" dibanding grimjaw/kaizen/vex.
Diukur dengan me-render lewat pipeline yang sama seperti game
(`render_hero` + cache untuk lane, dan `HeroPortraits` kanvas 160×160 untuk
Hero Shop), ketemu 5 cacat dan semuanya diperbaiki:

* **Wajah jadi subjek, bukan blob.** Pass pertama menaruh blok `skin_shine`
  selebar 11 px + rongga mata 1 px -> setelah `smoothscale` jalur hero wajah
  jadi "topeng merah muda" tanpa fitur. Sekarang aturan keluarga: satu blok
  terang kecil + satu blok gelap (dahi / cavum mata 4 px) dan MATA dua garis
  2-3 px ber-halo ungu, plus sapuan perang ungu di pipi.
* **Krist mohawk jadi massa, bukan helaian.** Helai 1 px hilang di skala
  hero; diganti tiga duri `hair_light`/`hair_shine` dengan 1 px pemisah, dan
  kuncir ramping ber-cincin kuningan di belakang kepala.
* **Satu titik fokus di dada.** Garis silang + tiga titik rune terbaca sebagai
  noda lavender -> sekarang pelat gelap dengan tepi atas `armor_shine` dan
  SATU permata `magic_hot` yang membesar saat Counterspell/Mana Void.
* **Sisi jauh dibiarkan gelap.** Pauldron belakang sempat memakai
  `armor_light`+`shine` sehingga muncul "sayap" pucat yang mengungguli wajah;
  cahaya dan permata tema sekarang hanya di sisi depan.
* **Anggota badan proporsional.** Dua bilah horizontal sejajar terbaca sebagai
  "palang" yang menenggelamkan badan -> bilah depan diangkat diagonal
  (+1.78 rad), belakang menukik (-1.00): lebar siluet tetap ~1.05 W/H tapi
  kepala & dada yang jadi subjek. Loincloth dipersempit (dulu mengubah dua
  kaki jadi satu tiang ungu) dan lengan dinaiki satu tingkat.
* **Sinyal warna keluarga.** Kaizen/Vex/Grimjam punya piringan cahaya +
  cincin tanah yang jelas; aura Gornak alpha 34-55 sehingga mati total di
  lane. Sekarang cakram ungu 78-120 + cincin rune dalam + titik terang.
* **Portrait Hero Shop tidak lagi terpotong.** Bilah depan (panjang +82 px
  dari jangkar) melewati tepi kanvas 160×160 lalu di-crop; di mode portrait
  konten dipusatkan pada bbox-nya sendiri, jalur boss 1× tidak berubah.

```
hero 1x (render akhir, alpha>=100)   H    W   kaki di bawah posisi
grimjaw 74x79 · kaizen 75x82 · vex 76x84 · gornak 83x84
```

**Pass ketiga — timing & gerak sekunder.** Yang masih "kaku" setelah
visualnya bagus adalah RITMENYA, jadi pass ini mengejar itu:

* `_attack_curve()` memetakan progres mentah -> waktu pose dengan
  **anticination diperlambat -> ayunan cepat -> HOLD 4-5 frame di impact ->
  follow-through**, semuanya monoton naik (kurva sinus versi awal sempat
  membuat bilah terlihat mundur sesaat - artefak baru).
* `_head_bob()`: kepala tidak lagi direkat ke torso - kontrarotasi saat
  langkah, menunduk saat ayunan, mikro weight-shift saat idle.
* Debu langkah (`_draw_footfall_dust`) hanya muncul saat telapak MENYENTUH
  tanah; titik kontak per boot ditambahkan ke bayangan.
* Kedip berkala (1 frame tiap ~4 dtk, deterministik dari phase).
* Kartu Hero Shop: mode portrait memakai pose "compact" (bilah ditarik
  rapat) - karena `HeroPortraits` meng-crop bbox lalu men-scale-nya, figur
  yang melebar justru TERKECIL di kartu; sekarang ~1.3x lebih besar.
* Hierarki nilai diperbaiki: `blade_shine` 246 -> 214 supaya MATA (bukan
  pedang) jadi piksel paling terang; garis break di pergelangan kaki;
  bayangan miring di bawah pektoral; rim terang di tepi robek jubah.

**Pass keempat — cahaya.** Gornak (jalur boss + Hero Shop) kini memakai pass
cahaya bersama di `lighting.py`; lihat bagian *Pass cahaya bersama* di bawah
untuk cara kerjanya dan test-nya.

Uji regresi: `python tools/test_gornak_masterwork.py` (16 pemeriksaan: rig
tunggal, kaki menapak, W/H dan **ukuran harus sama dengan keluarga**
(boss vs morgath/drakar/abaddon, hero vs grimjaw/kaizen), bilah tidak
menembus dada, proc di ujung bilah, outline, portrait LOD, frame per-sendi,
Q/W/E/R jalur boss **dan** hero, tidak di-upscale, budget ms/frame, plus
`test_hero_visual_quality` yang mengunci jalur hero: portrait tidak terpotong
di kanvas 160, mata & warna tema harus muncul di badan, dua kaki tetap
terpisah, dan cakram cahaya tetap ada di lane).
Review sheet: `python tools/_shot_gornak_masterwork.py` dan
`python tools/_shot_gornak_before_after.py`.

## Pass cahaya bersama (lighting.py)

Renderer prosedural membangun volume dengan blok nilai yang di-author manual
(`skin_dark` -> `skin_mid` -> `skin_light`). Itu cukup di ukuran besar, tapi
di 720p hasilnya tetap terbaca sebagai "tumpukan blok datar": tidak ada satu
arah cahaya yang konsisten, dan tidak ada terminator di sepanjang siluet.

`lighting.py` menambahkan tahap itu untuk SEMUA unit, tanpa satu pun sprite
bitmap:

| tahap | cara | biaya |
|---|---|---|
| gradien arah seluruh badan | kisi 28x28 pada sumbu cahaya, di-upscale sekali per ukuran lalu `BLEND_RGB_MULT` | 2 blit |
| rim light kiri-atas | `mask - geser(mask, +1,+1)` -> `BLEND_RGB_ADD` | 2 operasi mask |
| terminator kanan-bawah | `mask - geser(mask, -1,-1)` + band kedua 40% -> `BLEND_RGB_MULT` | 3 operasi mask |

Pemasangannya di satu choke point: **`heroes._finish_hd_sprite`** (dijalankan
hanya saat cache miss, di atas sprite HASIL resize, jadi rim-nya benar-benar
1 px pada resolusi layar) — sehingga keenam hero masterwork langsung ikut.
Boss yang menggambar sendiri ke layar (saat ini Gornak) memanggil
`lighting.apply_to_rig()` dengan `box` **konstanta rig**, dan melewatinya saat
dipakai sebagai hero (ada test yang mengunci ini: rim dobel = bingkai gelap
2 px yang membuat karakter terlihat kotor).

Yang dijamin test (`tools/test_hero_lighting.py`):

* alpha sprite tidak berubah (outline HD & colorkey mobile bergantung pada
  ini) dan ukuran/`pad` anchor tetap;
* delta terarah — sisi cahaya > sisi bayangan, diukur sebagai SELISIH
  sebelum/sesudah, karena luminance absolut tercemar art sprite itu sendiri
  (pedang Kaizen yang terang ada di kanan-bawah);
* tidak dobel di lane, tidak nol di Hero Shop;
* cache gradien terbatas (<= 64 entri) dan `apply()` < 0,35 ms per panggilan;
* kill switch `HD_LIGHTING_ENABLED = False` dan `import lighting` gagal sama
  -samanya tidak bikin render crash.

A/B untuk keluarga: `docs/lighting_ab.png` (regenerasi:
`python tools/_shot_lighting_ab.py`) — tiap sel menampilkan KIRI tanpa pass,
KANAN dengan pass, plus angka piksel yang berubah. Untuk Gornak sendiri:
`docs/gornak_hero_pass.png`.

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
