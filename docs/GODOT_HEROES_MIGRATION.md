# Migrasi `heroes/` ke Godot

## Cakupan

Runtime tidak mengimpor Python: `EntityVisuals.gd` menggambar atlas yang telah
tersedia, `HeroVisuals.gd` memilih pose native. Kontrak
`data/heroes_renderers.json` mencatat seluruh sumber Python `heroes/`, hash
manifest dan hash/dimensi atlas **222 unit** (6 renderer starter dan 216 renderer
boss yang juga dapat digunakan sebagai hero). Ini melengkapi, bukan mengganti,
migrasi `hero_skills/`, balance, archetype dan items sebelumnya.

Pemilihan pose memprioritaskan attack di atas walk/idle. Animasi skill hero
mengikuti progress timer cast, bukan frame global; sampel terakhir ditahan,
bukan di-loop. `BattleUnit.active_skill_timer` menyimpan durasi awal ketika
skill berubah atau timer dinaikkan, termasuk assignment dari generated kits.
Tidak ada perubahan durasi/cooldown gameplay. Boss tetap memakai loop lama.
Skill null dari generated kits aman dan kembali ke pose biasa.

## Regenerasi dan pemeriksaan

```bash
# jika renderer berubah: bake ulang dengan dependensi pygame/numpy
python3 tools/prepare_godot_entities.py --bake
python3 tools/prepare_godot_heroes.py

python3 tools/prepare_godot_heroes.py --check
python3 tools/test_godot_heroes_prepare.py
godot --headless --path godot_rebuild --editor --import
godot --headless --path godot_rebuild --script res://tests/run_all.gd
```

Generator gagal jika atlas hilang, bukan PNG, geometri sel tidak valid atau
rentang pose keluar atlas. Mode `--check` juga mendeteksi perubahan sumber,
manifest, dan byte atlas. CI menjalankan kontrak dan tes Python; tes pemilihan
pose native masuk `run_all.gd`.

## Bus game-feel native dan feedback starter

`HeroCombatFeel.gd` memigrasikan `heroes/combat_feel.py`: hit-stop 0.03–0.08 s,
maksimal lima langkah, permintaan tidak ditumpuk, pembulatan ties-to-even
Python, shake dengan peluruhan linear, filtering strength < 4, scaling kamera,
clock yang di-cache per milidetik, FX slow-motion 0.18, dan reset saat teardown.
Satu bus dimiliki `MatchModel`. Freeze menghentikan simulasi, bukan render atau
update `CombatEffects`. Sinyal kamera diteruskan satu kali ke `CombatEffects`;
`offset()` bus tidak ditambahkan lagi ke transform arena.

`generated/HeroFeedback.gd` adalah transpilasi AST **hanya slice game-feel**
`on_cast`/`on_impact` Grimjaw, Kaizen, Sylara, Vex, Zephyr. Formula dan urutan
branch diambil dari sumber, bukan profil generik. `BattleUnit.cast_skill`
memanggil feedback setelah cast sukses. Impact projectile hanya diteruskan
ketika `is_skill == true`; basic attack tidak mendapatkan hit-stop baru.
Konversi damage→power Sylara/Vex/Zephyr juga diambil dari hook Python asli.
Thorne tidak punya modul FX tersendiri di sumber dan tidak diberi efek palsu.

Fixture bus mengeksekusi modul Python asli dengan SDL clock palsu (7 skenario,
52 langkah). Fixture feedback mengeksekusi slice AST sumber (88 kasus);
ini **bukan** oracle untuk rig, partikel, projectile geometry atau director.
Tes GDScript terhubung ke `run_all.gd`, tetapi belum dieksekusi secara lokal.

```bash
python3 tools/prepare_godot_combat_feel.py --check
python3 tools/test_godot_combat_feel_prepare.py
python3 tools/prepare_godot_hero_feedback.py --check
python3 tools/test_godot_hero_feedback_prepare.py
```

## Bolt Zephyr prosedural native

`ZephyrBolt.gd` menggambar proyektil Zephyr tanpa atlas dan tanpa Python runtime:
ekor meruncing, halo, badan berarah, dua pass outline, highlight, duri fey,
inti piksel dan glint orbit. `EntityVisuals.draw_projectiles` mengirim projectile
yang sumbernya Zephyr ke renderer ini; projectile lain tetap memakai jalurnya
masing-masing. Palette diekspor dari `ZEPHYR_PALETTE` sumber, bukan disalin
ke GDScript secara manual. Radius default 6 sama dengan `_entity.py`.

`prepare_godot_zephyr_bolt.py` mengeksekusi fungsi `draw_bolt` Python asli dengan
recorder pengganti surface/draw. Fixture mencatat 15 command per kasus, termasuk
posisi global setelah scratch blit, warna, dan urutan lapisan. Delapan puluh
kasus mencakup posisi positif/negatif, 10 sudut, critical/non-critical, dua
pasangan umur/radius. `ZephyrBoltTest.gd` membandingkan command native secara
rekursif melalui `run_all.gd`; eksekusi native masih menunggu binary Godot.

**Batas:** ini oracle geometri/order, bukan oracle piksel. `CanvasItem`
menggunakan alpha compositing; Pygame memakai scratch overwrite dan
`BLEND_RGB_ADD` untuk halo. Rasterisasi garis/polygon juga belum dibuktikan sama.
Renderer native saat ini tidak menyamai blending additive tersebut. Director,
full director, semua partikel, skill FX, dan rig badan Zephyr tetap belum dimigrasikan penuh.
SwingTrail dan subset partikel impact dijelaskan di bagian berikut.

```bash
python3 tools/prepare_godot_zephyr_bolt.py
python3 tools/prepare_godot_zephyr_bolt.py --check
python3 tools/test_godot_zephyr_bolt_prepare.py
```

## Partikel impact Zephyr native

`ZephyrParticle.gd` memindahkan integrator Particle: acceleration/gravity,
linear drag, life/death, rotation, alpha, fade dan warna akhir. Posisi/velocity
menggunakan scalar double agar tidak mengakumulasi drift Vector2 float32.
Command draw mencakup **pixel, streak, shard, spark dan glow**, termasuk floor
negatif Python pada geometri shard. Bentuk tak dikenal memakai fallback pixel
seperti sumber. Spark meneruskan ukuran, origin dan alpha ke helper native
bersama ImpactFX; glow meneruskan radius dan power fade dua desimal. Ambang
alpha <= 3 diterapkan sebelum kedua helper. Glow sumber memakai RGB_ADD;
native masih memakai alpha compositing, jadi ini bukan parity piksel.
Helper spark/glow di fixture adalah descriptor semantik, bukan bitmap cache.

`ZephyrParticlePool.gd` menyediakan pool reusable, cap default 96 dari sumber,
burst, budget/thinning dan recycle. RNG terpisah dari RNG gameplay; algoritma
RNG Godot **tidak** diklaim identik dengan Python. Oracle memasok tape angka
acak yang sama untuk membandingkan gerak/pool tanpa mencampur beda RNG.

`HeroLiveFx.gd` memiliki pool per owner (hanya ID, tanpa referensi hero),
merutekan **impact projectile skill Zephyr** ke burst streak/shard dari resep
`ZephyrFXDirector.on_impact`. Feedback hit-stop/shake tetap lewat bus tunggal.
Basic attack tidak diberi burst impact; debu start swing dipindahkan terpisah. Pool kosong dibuang setelah partikel habis;
semua state FX dibersihkan oleh `MatchModel.clear_unit_refs()`.

Update memakai real-time clock bersama, sekali per timestamp, di luar loop
speed/catch-up. FX masih maju dengan faktor 0.18 saat hit-stop. Input quality
mengatur budget dan visibility. Gambar partikel dilakukan di world transform
arena, sebelum overlay UI. Urutan lintas-unit dan compositing Pygame belum
parity piksel.

Fixture `zephyr_particles.json` mengeksekusi AST class Particle/ParticleSystem
asli dengan shim penyimpanan Vector2, recorder draw, dan random tape; tidak
menyalin formula integrasi. Cakupan: 12 trajectory/geometry (lima bentuk + fallback), 4 skenario pool/budget,
16 resep impact. `ZephyrParticlesTest.gd` juga memeriksa recycling, cap,
slow-motion, timestamp duplikat, expiry, quality-off, teardown, alpha gate serta
recycle spark/glow. Tes Python juga menggambar 18 frame dengan Pygame asli.
**Tes native tersebut belum dieksekusi lokal karena binary Godot belum tersedia.**

```bash
python3 tools/prepare_godot_zephyr_particles.py
python3 tools/prepare_godot_zephyr_particles.py --check
python3 tools/test_godot_zephyr_particles_prepare.py
```

Belum termasuk dalam slice partikel: full FX director/state machine Zephyr,
wiring lengkap visual projectile, rig
prosedural dan seluruh FX khusus hero lain. ImpactFX dipindahkan terpisah.
SwingTrail dipindahkan terpisah di bagian berikut.

## SwingTrail dan attachment tongkat Zephyr

`ZephyrSwingTrail.gd` memindahkan lifecycle SwingTrail: histori pasangan
grip/tip, batas sampel, reset, expiry 0.26 s, width boost, serta tiga pass
**semua body ribbon → semua core → semua garis ujung**. Perhitungan memakai
array scalar double dan truncation Python; guard bounding-box 1400 px juga
dipertahankan. Draw command diuji terpisah dari rasterisasi CanvasItem.
Polygon zero-area/tidak bisa ditriangulasi dilewati saat menggambar untuk
mencegah error Godot pada pose atlas yang berulang; command oracle tetap utuh.

`tools/prepare_godot_zephyr_trail.py` mengeksekusi SwingTrail asli, fungsi
`ZephyrFXDirector._staff_points`, dan subset dependency `_staff_tip_local`
dari `_NS_zephyr`, tanpa mengimpor paket heroes/Pygame. Attachment diekspor
pada **8 progress pose dan pulse yang diambil dari baker**. Perubahan jumlah
frame yang tidak cocok dengan manifest gagal tertutup. Hash source FX, bundle,
baker, dan manifest dicatat di `data/zephyr_trail.json`.

Ini **sampled attachment contract**, bukan transpilasi seluruh rig atau bukti
pixel-perfect attachment pada body. Root motion, lighting dan compositing
renderer Python belum diverifikasi melalui capture runtime Godot.

Body Zephyr kini memakai `HeroVisuals.attack_frame`, berdasarkan timer dan
durasi animasi serangan unit, bukan frame global. Helper yang sama memilih
attachment trail. Hanya playback visual Zephyr yang berubah; perhitungan
hit/cooldown/gameplay tidak diubah. Skill override tidak membuat attachment
attack baru. Pose SWING/IMPACT merekam sampel; sisa trail memudar setelah
swing, owner hilang/mati, atau animasi berganti.

`HeroLiveFx.capture_trails` dipanggil setelah langkah simulasi, menggunakan
real-time FX delta yang sama (termasuk slow-motion hit-stop), sekali per
timestamp. State hanya menyimpan instance ID, tidak mempertahankan referensi
owner. Trail digambar sebelum projectile/partikel, dan dibersihkan saat
quality dinonaktifkan atau match di-teardown.

Fixture: **4 skenario lifecycle/geometri** (25 langkah), **32 attachment world**
(8 pose × 2 facing × 2 scale). Tes GDScript mencakup sinkronisasi pose,
mirroring, skill override, duplikasi timestamp, orphan expiry, quality, dan
cleanup; **belum dieksekusi lokal** karena binary Godot tidak tersedia.

```bash
python3 tools/prepare_godot_zephyr_trail.py
python3 tools/prepare_godot_zephyr_trail.py --check
python3 tools/test_godot_zephyr_trail_prepare.py
```

Full director, wiring lengkap visual projectile, dan rig
prosedural masih belum selesai. ImpactFX dipindahkan terpisah
di bagian berikut.

## ImpactFX Zephyr: flash, shockwave, slash dan spark

`ZephyrImpact.gd` memigrasikan lifecycle ImpactFX (power clamp, durasi, age,
active/death) dan urutan command: glow + flare radial, shockwave elips ganda,
spoke debris, tiga slash arc, lalu spark inti. `HeroLiveFx` merutekannya hanya
untuk impact projectile **skill Zephyr**, setelah partikel. Overlay dibatasi
**8 per owner**, yang paling lama dibuang lebih dulu. Update memakai clock FX
bersama sehingga hit-stop memperlambatnya dan timestamp duplikat tidak
menggandakan umur. Expiry, quality-off dan teardown membersihkan state tanpa
menahan referensi owner. Tidak ada permintaan shake/hit-stop kedua dari overlay.

Dua bug sumber dibetulkan di `heroes/zephyr_fx.py::ImpactFX.draw`: loop flash
dan spoke memakai `for i` tetapi membaca `k` sebelum terikat. Keduanya kini
memakai `for k`. Oracle menjalankan kode yang **sudah diperbaiki**; satu tes
regresi mengembalikan typo lama dan memastikan `UnboundLocalError` terdeteksi.
Source fingerprint terkait feedback/bolt/particle/trail/renderer diregenerasi.
Body atlas tidak di-bake ulang karena perubahan berada di live ImpactFX.

`prepare_godot_zephyr_impact.py` mengeksekusi class Python asli. Fixture mencakup
**36 kombinasi input × 8 umur absolut**, lifecycle dt, **6 spark helper** dari
fungsi `spark_surface` asli, dan **7 kuantisasi sudut elips** dari ekspresi
helper sumber (termasuk floor negatif). Smoke test tambahan menggambar **30
frame offscreen dengan Pygame asli**, tanpa mengimpor runtime heroes penuh.

**Batas oracle/render:** ellipse/spark di main ImpactFX fixture adalah semantic
helper descriptors; rotated bitmap bounds, scratch overwrite, cache surface,
RGB_ADD dan rasterisasi bukan oracle piksel. Helper spark diuji geometri
primitifnya secara terpisah. Godot menggambar elips dengan polyline dan arc
melalui CanvasItem; arah sudut dan kuantisasi mengikuti kontrak sumber, tetapi
pixel coverage/thickness/compositing belum dibuktikan identik. Glow tetap
menggunakan alpha compositing, bukan Pygame RGB_ADD.

`ZephyrImpactTest.gd` memeriksa lifecycle/command/helper, cap, eviksi, slow-motion,
expiry, quality dan cleanup melalui `run_all.gd`. **Tes runtime Godot belum
dijalankan lokal**; smoke test Pygame bukan pengganti tes native tersebut.

```bash
python3 tools/prepare_godot_zephyr_impact.py
python3 tools/prepare_godot_zephyr_impact.py --check
python3 tools/test_godot_zephyr_impact_prepare.py
# tes offscreen asli memerlukan pygame==2.6.1 (sudah dipasang di CI)
```

Masih tertinggal: full director/state machine, skill visual
projectile independen, serta rig prosedural penuh
Zephyr dan FX khusus hero lainnya.

## Hurt Zephyr: HP observer, streak dan hit flash

`ZephyrHurt.gd` memindahkan slice director untuk observasi HP dan hit flash:
sampel HP pertama hanya menjadi baseline; penurunan **lebih dari 0.01**
memicu tiga streak pada `(x, y-8)`, lalu flash direset ke **0.16 detik** dan
dikurangi dt frame yang sama. Heal atau penurunan kecil tidak memicu burst.
Posisi glow mengikuti posisi hero saat ini; radius dan power mengikuti
`_draw_hit_flash` sumber, termasuk pemotongan koordinat negatif dengan `int`.

`HeroLiveFx.update` menerima daftar hero aktif dari CoreGame, mengobservasi HP
sebelum meng-update pool sehingga partikel baru ikut di-age pada frame tersebut.
**Timing adapter:** observasi dilakukan pada awal tick FX, sebelum langkah
simulasi; damage dalam langkah itu terlihat pada tick FX berikutnya. Tidak ada
klaim identik dengan urutan render/update legacy dalam satu frame. Clock FX
bersama memberikan slow-motion hit-stop dan deduplikasi timestamp. State hanya
menyimpan ID/angka, dibuang saat owner hilang, quality-off atau clear. Tidak
menambahkan gameplay damage, shake atau hit-stop; budget partikel tetap berlaku.

Fixture partikel kini memuat dua skenario hurt/sepuluh sampel. Generator
mengeksekusi `on_hurt`, `_draw_hit_flash`, dan **prefix update HP/flash** dari AST
sumber; bukan seluruh director/state machine. Tes mutasi membuktikan durasi
flash berasal dari kode Python. `ZephyrParticlesTest.gd` membandingkan kontrak
ini dan menambahkan tes integrasi baseline, damage, deduplikasi, removal serta
cleanup. Tes native masih belum dijalankan lokal. Glow menggunakan renderer
bersama, dengan batas alpha vs RGB_ADD/rasterisasi yang sama seperti di atas.

## SkillFX Zephyr: lifecycle dan emisi q/w/e/r

`ZephyrSkill.gd` memindahkan constructor, timeline, phase selection, emitter
accumulator, serta one-shot release/impact dari `SkillFX`. Konfigurasi timeline,
radius/tint dan cap director **3** diekstrak dari AST ke `data/zephyr_skill.json`.
Urutan fase adalah cast (constructor), charge, release, area, impact lalu fade;
expiry terjadi pada total durasi. Kind tak dikenal fallback ke q, radius nol
memakai default sumber, dan tanpa particle system hanya lifecycle yang berjalan.
Langkah dt besar **tidak** mengulang fase yang terlewati, sesuai sumber.

Emitter mengirim partikel charge yang tersedot ke pusat, dua burst release,
bara area dan burst shard impact. `HeroLiveFx` menampung maksimal tiga efek
per owner, mengeluarkan yang tertua, dan menerapkan emission requests sesudah
pool partikel di-update, sesuai urutan source director. State tidak menahan
referensi owner/pool; expiry, quality-off dan clear membuangnya. Clock FX
memberikan slow-motion dan deduplikasi timestamp.

**Adapter cast:** hanya cast gameplay yang berhasil di `BattleUnit.cast_skill`
memulai efek di `(x, y+18)`. Ini bukan observer edge `active_skill` legacy;
full director masih tertinggal. Shake cast tetap melalui HeroFeedback yang
sudah ada, tanpa permintaan shake/hit-stop kedua dari SkillFX.

Oracle `zephyr_skill.json` mengeksekusi class SkillFX asli dengan recorder
spawn/burst, fixed visual seed dan random tape; tujuh skenario mencakup q/w/e/r,
fallback, radius custom, tanpa pool, dan dt yang melewati fase. Tes mutasi
memastikan formula emisi berasal dari Python. Tes native membandingkan
snapshot/emission requests dan mengecek cap, eviksi, clock, expiry dan cleanup,
tetapi **belum dijalankan lokal**. RNG visual native dipisahkan dari RNG gameplay;
kesamaan algoritma atau urutan RNG lintas subsistem tidak diklaim.

Ground/front SkillFX dipindahkan terpisah di bagian berikut. Keseluruhan
skill tetap belum parity piksel.

```bash
python3 tools/prepare_godot_zephyr_skill.py
python3 tools/prepare_godot_zephyr_skill.py --check
python3 tools/test_godot_zephyr_skill_prepare.py
```

## SkillFX Zephyr: visual depan

`ZephyrSkill.front_commands` memindahkan `draw_front` dan `_rune_ring`: glow
release dengan radius kelipatan tiga dan ring ber-alpha, dua orbit rune area
berlawanan arah, serta ring shockwave impact. Charge sengaja tidak menggambar
pilar (sesuai revisi sumber), cast/fade/expired juga tidak menggambar lapisan
depan. Detail produksi memakai minimum 0.35 seperti `skill_detail` sumber;
jumlah rune memakai round ties-to-even Python, bukan roundi bawaan Godot.

Oracle SkillFX menambahkan **312 kasus** (q/w/e/r, dua posisi termasuk negatif,
tiga detail, 13 sampel fase/umur). Rune direkam dari polygon sumber; helper
`ring_surface` asli juga dieksekusi dengan surface recorder sehingga center,
radius, thickness dan alpha bukan descriptor perkiraan. Glow tetap helper
request semantik (bukan bitmap/piksel). Tes mutasi memastikan rotasi rune
mengikuti sumber, dan smoke Pygame menggambar **20 frame front** dari fungsi
asli dengan helper sesungguhnya.

Renderer bersama menambahkan outline circle via arc 96 titik; radius stroke
digeser setengah ketebalan ke dalam untuk mendekati Pygame yang menggambar
stroke inward. Ini **bukan** pembuktian pixel coverage/ketebalan identik.
Glow alpha vs RGB_ADD dan scratch overwrite tetap berbeda. HeroLiveFx
menggambar front skill sesudah partikel, sebelum impact/hurt; pengelompokan
lintas-owner belum mengklaim urutan per-director legacy identik.

`ZephyrSkillTest.gd` membandingkan semua front command dan ties-to-even.
Tes native tersebut masih belum dijalankan lokal. Full director,
wiring lengkap visual projectile, rig prosedural dan FX hero lain tetap
belum selesai.

## SkillFX Zephyr: ground haze, ring dan retakan

`ZephyrSkill.ground_commands` memindahkan `draw_ground`, `_ground_ring`,
`_ground_cracks` dan geometri `ground_glow_surface`: haze elips berlapis,
radius/power terkuantisasi, ring solid dengan inner highlight, ring putus-putus
berdetail adaptif, dan retakan deterministik dari hash seed 32-bit sumber.
Retakan memakai RGB opaque seperti sumber; alpha hanya menjadi gate, bukan
opacity garis. Pembulatan ties-to-even, floor negatif dan truncation lokal
scratch dipertahankan pada command geometry.

Oracle menambah **288 kasus ground** (q/w/e/r × dua posisi × tiga detail ×
12 sampel). Helper haze asli dieksekusi menjadi primitive elips, bukan descriptor
haze. Recorder Rect mengimplementasikan inflate dan dites terhadap Pygame
asli untuk tinggi genap/ganjil. Tes mutasi hash membuktikan retakan mengikuti
sumber; smoke Pygame merender **20 frame ground** dengan helper sesungguhnya.
Native test membandingkan semua ground command dengan fixed visual seed 1234.

**Adaptasi defensif:** constructor SkillFX meninggalkan phase `cast`; jika
`draw_ground` sumber dipanggil sebelum update pertama, cabang fallback dapat
menghasilkan alpha >255 dan Pygame melempar ValueError. Tes mereproduksinya.
Legacy normal menggambar sesudah update phase; native bisa menerima cast
setelah FX update dalam tick yang sama, jadi ground native ditunda sampai
update phase pertama. Kasus constructor-only ini sengaja tidak menjadi oracle
parity ground. Kode Python sumber tidak diubah untuk kasus tersebut.

`ArenaView` menggambar ground skill sesudah tower/base dan sebelum minion/hero.
Renderer memakai polygon elips 64 segmen, atau polyline inset setengah width
untuk mendekati stroke Pygame inward. Rasterisasi, scratch overwrite dan RGB_ADD
masih bukan parity piksel; urutan lintas-owner juga belum identik dengan full
director. Tes native tetap belum dijalankan lokal. Migrasi full director,
wiring lengkap visual projectile, procedural rig dan FX hero lain masih tertinggal.

## Director Zephyr: state machine dan event swing

`ZephyrDirectorState.gd` memindahkan `_resolve_state`, `_update_state`,
`attack_phase` serta event `on_swing_start/end`. Prioritas dan enam interval
attack phase diekstrak dari sumber ke `data/zephyr_director.json`. Urutan
resolusi tetap death, hurt, skill/special, attack phase, moving/run, idle.
Transisi ke prioritas rendah menunggu **state_time > 0.05** (bukan >=);
DEATH terkunci seperti sumber, termasuk jika input alive berubah lagi.
Anim phase tetap diperbarui terlepas dari state yang sedang mengunci.

Start swing mereset flag dan menghasilkan dua pixel debu pada `(x+facing*6,
y+42)` dengan resep sumber; swing berkelanjutan tidak mengulang burst. End
swing mematikan flag. Reset/push/expiry trail tetap ditangani slice sampled
SwingTrail yang sudah ada, bukan oleh state class baru.

Adapter `HeroLiveFx.capture_trails` memperbarui state sesudah simulasi dengan
clock FX yang sama, sekali per timestamp. Input memakai normalized timer
attack native, `active_skill`, flag movement, speed dan hurt flash yang sudah
ada. Ini bukan live rig/lean/root_y legacy. Dust menggunakan phase kontinu
sedangkan titik trail masih attachment pose sampel; keduanya belum diklaim
identik subframe. Dust baru dibuat setelah update pool frame itu, sehingga
mulai bergerak pada tick FX berikutnya (beda urutan dari director legacy).
State hanya menyimpan angka/string/ID; removal owner, quality-off dan clear
membersihkannya. Tidak ada damage atau feedback shake/hit-stop baru.

Oracle mengeksekusi method state dan potongan swing-update asli, dengan
constructor director asli dan subsystem stub; **bukan full director update**.
Empat sequence/31 sampel mencakup prioritas, lock threshold, DEATH, phase
boundary/clamp, arah, dan swing berulang. Tes mutasi guard membuktikan aturan
berasal dari Python. `ZephyrDirectorTest.gd` membandingkan snapshot/burst dan
menambahkan tes adapter/deduplikasi/removal/cleanup. Tes native belum dijalankan
lokal. State baru ini mengatur observasi/event FX; belum menggerakkan body rig
atau menggantikan seluruh orchestration director legacy.

```bash
python3 tools/prepare_godot_zephyr_director.py
python3 tools/prepare_godot_zephyr_director.py --check
python3 tools/test_godot_zephyr_director_prepare.py
```

## Projectile visual Zephyr independen

`ZephyrVisualProjectile.gd` memindahkan class `ZephyrProjectile`: gerak scalar
double, homing terhadap snapshot target, umur maksimal 2.6 detik (strict >),
16 sampel ribbon trail berumur 0.20 detik, emisi pixel ekor setiap >=0.028 detik,
collision radius sederhana, kill idempotent, lalu impact yang hilang setelah
umur >0.28 dan trail kosong. Metadata damage tetap disimpan tetapi **tidak
pernah diterapkan**. Hit callback sumber diadaptasi menjadi daftar hit requests;
API ini tidak menjalankan callable Python atau menambah shake/hit-stop.

`ZephyrVisualProjectileSystem.gd` menyediakan spawn/update/draw/clear dengan
cap **14** dari sumber. `HeroLiveFx.spawn_visual_projectile` menerima spawn
visual eksplisit; tiap owner mempunyai manager sendiri, target memakai ID dan
snapshot transient dari `model.all_units()`, bukan referensi hero yang ditahan.
Update berjalan pada clock FX, sesudah aging partikel dan sebelum impact/skill.
Gambar ribbon/body sebelum partikel, lalu skill/impact/hurt. Quality-off, clear,
dan expiry membersihkan manager; partikel ekor yang tersisa hidup sampai expiry.

**Wiring sengaja terbatas:** tidak menambahkan bolt baru otomatis pada semua
cast, dan tidak mengganti `EntityProjectiles` gameplay. Source director memiliki
manager independen, tetapi trigger spawn/consumer hit requests penuh masih
perlu dipetakan dalam orchestration. Jadi class/API sudah native, bukan klaim
semua skill kini memakai independent visual projectile.

Oracle mengeksekusi class projectile/managernya dari AST, dengan tujuh skenario
(straight, zero aim, moving/dead target, collision, trail cap, parameter custom,
dan strict expiry) serta manager cap/cleanup. Vektor shim double diuji terhadap
**Pygame Vector2 asli**, termasuk kesamaan draw commands di fixture; smoke test
Pygame merender 12 frame ribbon/body dan draw sesudah kill. Tes mutasi membuktikan
integrator berasal dari Python. Random tape menguji emisi, bukan kesamaan RNG
produksi antar subsistem.

Body memakai renderer bolt yang sama; entry `commands_at` menerima scalar double
agar tidak menyempit ke Vector2 float32 sebelum pixel snap. Polyline trail tetap
satu command agar join tidak dianggap segmen terpisah. Native CanvasItem tidak
mengklaim scratch overwrite, RGB_ADD, polygon triangulation atau pixel parity.
Native oracle/manager/adapter tests terdaftar, tetapi **belum dijalankan lokal**.

```bash
python3 tools/prepare_godot_zephyr_projectile.py
python3 tools/prepare_godot_zephyr_projectile.py --check
python3 tools/test_godot_zephyr_projectile_prepare.py
```

## Grimjaw: foreground hurt streak dan hit flash

Migrasi mulai diperluas ke Grimjaw melalui `GrimjawHurt.gd`: baseline HP,
threshold penurunan >0.01, reset flash 0.16 detik dan pengurangan dt memakai
observer matematika bersama yang diuji terpisah terhadap AST Grimjaw. Resep
sumber memakai tiga streak pada `(x, y-10)` dengan palette fx_light/ember,
bukan warna Zephyr. Pool backend dibatasi **108** dari konstanta Grimjaw.

Flash menjalankan geometri **empat band posterized** `glow_surface` Grimjaw,
dengan radius, premultiplied RGB/alpha, hash jitter dan round ties-to-even sumber.
Oracle mengeksekusi helper asli dan merekam empat circle, bukan descriptor glow
Zephyr. Native CanvasItem masih memakai alpha blending dan tidak meniru surface
overwrite/RGB_ADD; kesamaan primitive bukan kesamaan piksel.

Budget berbeda dari Zephyr: `_budgeted(3)` memakai Python `round(3*ratio)`.
Pada rasio .1 menghasilkan nol streak, .5 menghasilkan dua. Adapter menghitung
sekali lalu memakai backend burst dengan budget 1 sementara agar tidak terkena
thinning kedua. Observer baru diproses pada awal tick FX, sebelum simulasi;
damage langkah simulasi terlihat tick berikutnya. Policy quality native tetap
menonaktifkan observer/flash pada budget nol atau particles-off.

Oracle mencakup dua sequence/sepuluh sampel HP, enam budget, dan dua trajectory
foreground streak dari class Particle Grimjaw asli. Backend motion/streak
bersama diuji terhadap source tersebut; ini **bukan** klaim full ParticleSystem
Grimjaw sudah dipindahkan. Ember/smoke/back layer ditambahkan di bagian berikut. Tes mutasi glow
membuktikan primitive berasal dari helper sumber; smoke Pygame asli merender
empat umur flash. Adapter punya tes cap, deduplikasi, hit-stop, removal, quality,
teardown dan budget setengah. State hanya memakai ID/angka, tanpa referensi hero.

Native suites kini dikelompokkan lewat `HeroMigrationTest.gd` agar runner utama
tidak melewati batas lint saat jumlah suite bertambah. Runtime Godot tetap
belum diuji: percobaan unduh engine resmi kembali gagal pada host release-assets
GitHub di lingkungan ini. Validasi parse/lint bukan bukti kompilasi/runtime Godot.

```bash
python3 tools/prepare_godot_grimjaw_hurt.py
python3 tools/prepare_godot_grimjaw_hurt.py --check
python3 tools/test_godot_grimjaw_hurt_prepare.py
```

## Grimjaw: death edge, ember/smoke dan pemisahan layer

`GrimjawParticle.gd` memindahkan bentuk ember (dua polygon dengan flicker dan
warna gelap), smoke (dua circle), palette pixel highlight Grimjaw, serta flag
back/front. Motion, streak dan shard memakai backend bersama yang diuji
terhadap class Particle Grimjaw asli. Ember memakai pembagian integer positif
sebelum pengurangan untuk inti diamond; ini berbeda dari floor negatif shard.
Glow/spark partikel Grimjaw dipindahkan pada milestone berikut, bukan memakai
bentuk/palette Zephyr. Helper flash hurt empat band tetap terpisah dan aktif.

`GrimjawParticlePool.gd` menambah factory partikel Grimjaw dan budget round-to-even,
termasuk default palette, cap, recycling dan clear. Backend Zephyr kini memiliki
factory hook serta filter draw back/front; perilaku bawaan Zephyr tetap foreground.
Particle stream Grimjaw dipindahkan pada milestone berikut. Oracle awal mencakup sepuluh
trajectory pada lima bentuk/dua ukuran dan lima skenario pool/budget/cap,
dengan random tape yang sama, bukan klaim algoritma RNG produksi identik.

`on_death` sumber dieksekusi untuk mengekstrak dua resep: **8 ember pada y-12**
dan **5 smoke pada y**, beserta **shake(3, 0.3)**. Observer `_was_alive` hanya
memicu transisi hidup ke mati, dapat di-arm ulang setelah respawn, dan tidak
mengulang pada corpse. Resep dan feedback terambil dari AST, bukan menambahkan
hit-stop/damage baru. Native memanggil bus feel sekali per edge. Hurt dan death
pada tick yang sama tetap dapat menghasilkan kedua paket seperti sumber.

Adapter mengamati sebelum simulasi lalu meng-age partikel baru pada dt frame
itu; death dalam simulasi terlihat tick FX berikutnya. Back smoke digambar di
`draw_ground` sebelum minion/hero, sementara ember/hurt streak di foreground.
Urutan per-owner/full director dan rasterisasi/scratch overwrite/RGB_ADD tetap
belum parity piksel. Quality-off/clear/removal mengikuti kebijakan adapter yang
sudah ada; partikel yang owner-nya hilang boleh menyelesaikan umur tanpa menahan
referensi owner. Smoke test Pygame mengeksekusi resep death dan menggambar
**12 frame × dua layer**. Native tests mencakup oracle geometry/pool, death
sekali, layer back, expiry serta respawn edge; runtime Godot belum dijalankan.

## Grimjaw: stream, glow dan spark

`GrimjawParticlePool.stream` memindahkan sampler charge/hisap dari sumber:
round(count*budget), jitter origin, interpolasi titik menuju target, normalisasi
distance minimum 1, velocity, life/size, palette, rotasi dan rotation speed.
**Gate spawn kedua tetap dipertahankan**, berbeda dari burst yang bypass thinning
kedua. Source juga terus mengambil random untuk kandidat walau pool penuh;
native mengikuti urutan ini. Tidak ada RNG gameplay yang dipakai. API ini belum
berarti seluruh skill Grimjaw sudah otomatis memanggil stream.

Renderer `GrimjawParticle` kini mencakup glow empat band dan spark **lima jarum**
dengan hash deterministik, ketebalan garis bergantian serta core putih. Glow
menggunakan helper geometry yang sama dengan hurt flash; saat quality glow-off,
extent dibagi dua seperti sumber, bukan menghilangkan partikel. Quality dibaca
pool saat draw dan diteruskan dari konfigurasi HeroLiveFx. Semua tujuh shape
sumber kini memiliki command native (ditambah fallback pixel); full director,
Visual ground SkillFX, weapon trail, projectile Grimjaw dan procedural rig tetap tertinggal.

Oracle menjalankan helper `spark_surface` asli dan mengadaptasi global surface
alpha ke **effective primitive alpha**. Ini bukan simulasi overwrite scratch
atau raster/blending SDL. Alpha garis spark 235 dikalikan opacity/255; core putih
memakai opacity. Native masih memakai CanvasItem alpha blending, bukan RGB_ADD.
Kasus primitive, cache state dan hasil piksel tidak dianggap ekuivalen.

Fixture berkembang menjadi **16 trajectory/quality cases** (tujuh bentuk,
dua ukuran, ditambah dua low-glow), dan lima skenario pool yang kini menyertakan
stream saat penuh serta target coincident. Native suite membandingkan geometry,
snapshot, jumlah emisi dan posisi random tape; belum dijalankan di engine lokal.
Python menguji konsumsi RNG full/half/zero budget, mutasi formula stream, serta
smoke Pygame **16 frame glow/spark**. Semua suite lama tetap dijalankan.

## Grimjaw SkillFX: lifecycle/emisi q/w/e/r

`GrimjawSkill.gd` memindahkan constructor dan `update` SkillFX Grimjaw.
Penyimpanan scalar/tape/lifecycle snapshot memakai basis ZephyrSkill, tetapi
formula emisi, timeline, radius dan palette **berasal dari Grimjaw**, bukan
mengganti nama efek Zephyr. Snapshot menambahkan col_a/col_b sesuai constructor.
Kind tak dikenal fallback q; radius nol fallback default; tanpa pool lifecycle
berjalan tanpa RNG/emisi. Dt besar tidak mengulang fase yang sudah terlewati.

Charge memancarkan ember (atau mote pixel heal W). Release W hanya lima mote
hijau; Q/E/R memiliki streak + smoke belakang. Area Q menjadi vortex ember,
W mote hijau, E ember emas, R shard orbit. Impact Q/E/R memiliki tujuh shard;
W memperbarui flag impact tetapi tidak diberi ledakan. Emisi mengikuti threshold
0.034 charge dan interval area per-skill, dengan reset accumulator ke nol.

Cast sukses melalui hook BattleUnit yang sudah ada sekarang menerima Grimjaw,
mengalokasikan maksimal **3 SkillFX per owner**, eviksi tertua, origin y+16,
dan Q memakai skill_range hero seperti source on_cast. Emission requests
diterapkan ke GrimjawParticlePool sesudah update partikel. Clock FX, slow-motion,
deduplikasi, quality-off, expiry dan teardown menggunakan adapter bersama.
Tidak menambahkan shake/hit-stop kedua; feedback cast lama tetap melalui bus.

**Batas:** ini baru lifecycle dan emisi SkillFX. `on_cast` director masih punya
paket tambahan (burst awal, trail spin, timer raw dan posisi ward) yang belum
seluruhnya dipindahkan. Trigger native memakai cast sukses, bukan observer
edge active_skill/timer legacy. `draw_ground` Grimjaw sengaja belum menggambar apa pun. `draw_front`
dipindahkan terpisah pada milestone berikut, bukan memakai visual Zephyr.

Oracle mengeksekusi class SkillFX asli: tujuh skenario q/w/e/r, fallback, custom
radius, disconnected pool dan skip fase. Seed tetap 1234; randint cabang R
memakai tape deterministik terkontrol, bukan klaim kesamaan RNG produksi.
`_sync_palette` dimock untuk mengekspor **palette literal repository**; sinkronisasi
runtime ke material `_NS_grimjaw.PALETTE` belum dipindahkan. Konfigurasi ini tidak
boleh dianggap parity live palette renderer. Tes mutasi menguji formula charge.
Native suite membandingkan snapshot/emisi dan adapter, tetapi runtime Godot
masih belum dijalankan lokal.

```bash
python3 tools/prepare_godot_grimjaw_skill.py
python3 tools/prepare_godot_grimjaw_skill.py --check
python3 tools/test_godot_grimjaw_skill_prepare.py
```

## Grimjaw SkillFX: front ring coretan, rune dan chevron

`GrimjawSkill.front_commands` memindahkan `draw_front`, `_rune_ring`,
`_chevrons`, serta primitive helper `ring_surface` Grimjaw. Release memakai glow
empat band saat glow diizinkan dan ring ber-alpha; area Q/W/R memakai rune
berlawanan arah, E memakai chevron outline yang bergerak; impact memakai ring
coretan putih. Charge/cast/fade/expired tidak menggambar front, sesuai source.
Ground FX masih belum dipindahkan.

Ring bukan circle Zephyr: helper menghasilkan 10–22 vertex berjitter hash,
stroke utama yang bergantung thickness, dan pass kedua tipis bergeser untuk
radius >=8. Oracle menjalankan helper asli dengan dimensi surface dan global
alpha: pass kedua awalnya alpha 127, lalu dikalikan opacity/255. Native
mengirim dua closed polyline dengan geometri dan urutan yang sama. Rune tetap
polygon fill, chevron menjadi polygon outline; renderer bersama menambahkan
outline command tanpa mengubah polygon fill lama.

Grimjaw source `_chevrons` memakai `_facing` opsional dengan default kanan;
native juga default kanan dan menyediakan input arah untuk uji/API. Adapter
cast tidak mengarang perubahan arah dari hero, karena mapping source tersebut
belum ada di full director. Detail mempertahankan round ties-to-even/minimum,
dan quality glow hanya mematikan glow release, bukan ring/rune/chevron.

Oracle menambahkan **780 kasus front**: empat skill, dua posisi (termasuk
negatif), tiga detail, dua opsi glow, kedua arah E dan 13 sampel fase/umur.
Tes mutasi salt hash membuktikan vertex ring berasal dari sumber. Smoke Pygame
asli merender **40 frame** glow on/off × q/w/e/r × lima fase. Native suite
membandingkan semua primitive; belum dijalankan di engine lokal.

**Batas:** recorder mengubah global surface alpha menjadi effective primitive
alpha, bukan mensimulasikan scratch overwrite. Closed-polyline join, outline
stroke placement, RGB_ADD dan pixel coverage Godot belum parity. Palette masih
literal yang diekspor, belum live sync material renderer. Full orchestration,
ground FX, trail, projectile dan rig Grimjaw tetap tertinggal.

## Batas yang disengaja

Ini **bukan** transpilasi seluruh rig prosedural `heroes/_bundle.py`, seluruh
modul `*_fx.py` atau cache adaptif Python. Bus `combat_feel.py` sudah dipindah,
namun belum diuji runtime native. Atlas merupakan
sampel visual; live beam/proyektil, efek stateful dan fidelitas piksel belum
dibuktikan identik. Hash hanya membuktikan konsistensi artefak, bukan parity
visual. Kode Python tetap dipertahankan sebagai sumber bake/referensi.

## Verifikasi lingkungan pengerjaan

- 5 tes kontrak renderer, 5 tes oracle bus, 5 tes feedback, 5 tes bolt,
  12 tes partikel/pool/recipe/helper/hurt, 7 tes trail/attachment, 8 tes ImpactFX
  (termasuk smoke render offscreen Pygame), 14 tes lifecycle/emisi/ground/front SkillFX, 7 tes director state/swing, 8 tes independent visual projectile, 18 tes Grimjaw hurt/death/particle/pool/stream, 11 tes Grimjaw SkillFX lifecycle/emisi/front: lulus.
- Regresi persiapan entity (3 tes) dan hero skills (6 tes): lulus.
- `prepare_godot_heroes.py --check`: lulus.
- `validate_project.py`: 657 pemeriksaan lulus.
- gdparse/gdlint/gdformat pada GDScript yang berubah: lulus.
- Tes runtime/headless Godot belum dijalankan: binary Godot tidak tersedia; unduhan rilis terhalang host aset GitHub.

## Status seluruh modul `heroes/`

Daftar ini sengaja membedakan port native, feedback parsial, dan atlas.
**Migrasi seluruh rig/director belum selesai.** Status machine-readable ada
di `data/heroes_renderers.json` dan tidak menganggap hash sebagai parity.

| Modul | Status |
|---|---|
| `__init__.py` | Atlas; rig/cache prosedural belum native |
| `_bundle.py` | Atlas; rig/cache prosedural belum native |
| `abaddon_fx.py` | Belum native |
| `alchemist_fx.py` | Belum native |
| `ancient_apparition_fx.py` | Belum native |
| `combat_feel.py` | Bus native; tes runtime menunggu |
| `gorath_fx.py` | Belum native |
| `gornak_fx.py` | Belum native |
| `gravefang_fx.py` | Belum native |
| `gravewake_fx.py` | Belum native |
| `grimjaw_fx.py` | Feedback, hurt/death, ember/smoke dan back/front particle native; full director/rig dan wiring skill belum selesai |
| `grimjaw_v1.py` | Belum native |
| `ignis_drachorn_fx.py` | Belum native |
| `kaizen_fx.py` | Feedback native; visual/director belum native |
| `kaizen_v1.py` | Belum native |
| `khalros_fx.py` | Belum native |
| `krobellus_fx.py` | Belum native |
| `kunkka_fx.py` | Belum native |
| `nyxara_fx.py` | Belum native |
| `nyzrak_fx.py` | Belum native |
| `pyrenth_fx.py` | Belum native |
| `razak_fx.py` | Belum native |
| `sylara_fx.py` | Feedback native; visual/director belum native |
| `sylara_v1.py` | Belum native |
| `syrentha_fx.py` | Belum native |
| `thalgryn_fx.py` | Belum native |
| `varkul_fx.py` | Belum native |
| `vex_fx.py` | Feedback native; visual/director belum native |
| `vex_v1.py` | Belum native |
| `vhalzun_fx.py` | Belum native |
| `vokrahn_fx.py` | Belum native |
| `xerathis_fx.py` | Belum native |
| `zephyr_fx.py` | Feedback, bolt, partikel, SwingTrail, ImpactFX, SkillFX, hurt dan director state/swing native; sampled attachment; full director/rig dan parity piksel belum selesai |
| `zharok_fx.py` | Belum native |
