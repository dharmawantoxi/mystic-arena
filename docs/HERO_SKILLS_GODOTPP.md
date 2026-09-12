# Migrasi hero_skills → godot++ (GDExtension C++)

> **Status:** 2026-09-12 — lib C++ **terbuild + ter-link** (`MysticHeroSkills`),
> paritas runtime dikunci `HeroSkillGdextParityTest` di workflow
> `.github/workflows/godot-gdext.yml`. Jalur produksi tetap GDScript
> (`mystic/skills/use_gdext_skills=false`) sampai benchmark Android diputuskan —
> lihat "Batas yang disengaja".

`hero_skills/_bundle.py` (5.221 baris Python: `BaseSkill` 28 method,
6 kelas starter, `BossHeroSkills` 273 method / 270 `_cast_*`, `_SKILL_REGISTRY`
66 boss-hero) sekarang punya **tiga** representasi yang dibangkitkan dari AST
yang sama:

| Lapisan | Berkas | Generator | Peran |
|---|---|---|---|
| Python (sumber kebenaran) | `hero_skills/_bundle.py` | — | dimainkan pygame; oracle fixture |
| GDScript | `godot/scenes/hero/HeroSkillKit.gd` (5.807 baris, 330 `static func`) | `tools/gen_hero_skill_kit.py` | jalur default Godot, tanpa compiler |
| **C++ (godot++)** | `godot/gdext/mystic_skills/src/hero_skills_processor.{h,cpp}` (459 + 6.802 baris, 432 definisi) | `tools/gen_hero_skills_cpp.py` | hot-path native, opt-in |
| Saklar | `godot/scenes/hero/HeroSkillKitLoader.gd` | tangan | `Hero.gd` tidak tahu backend mana yang jalan |

Tidak ada satu pun angka (koefisien damage, radius, durasi, cooldown) yang
disalin tangan ke C++: semuanya hasil transpile, dan **kedua** generator punya
mode `--check` yang dijalankan CI supaya `_bundle.py` tidak bisa berubah tanpa
C++ ikut dibangkitkan ulang.

---

## Kenapa C++ (bukan berhenti di GDScript)?

Skill adalah satu-satunya logika gameplay yang dieksekusi **tiap frame untuk
tiap unit**: `Hero._step_skill_frames()` → `HeroSkillKit.update_timers()` jalan
untuk semua hero hidup, dan tiap cast menelusuri daftar unit/tower/base lawan
(`kit_enemies` → filter tim+hidup → jarak → damage). Di GDScript itu berarti
puluhan ribu akses properti + aritmetika Variant per detik pada HP low-end.

| Aspek | GDScript (`HeroSkillKit.gd`) | C++ (`MysticHeroSkills`) |
|---|---|---|
| Akses state hero | `h.kit[...]`, `h.skill_timer` lewat lookup script | `Object::get/set` + helper bertipe (`double`, `int`) |
| Loop musuh per cast | interpreter, boxing Variant per elemen | loop `Array` native, cast sekali |
| `update_timers` 66 boss | dipanggil tiap frame per hero | fungsi native, tanpa dispatch GDScript |
| Deploy | selalu jalan | butuh `scons` + lib per platform |

Paritas tetap prioritas di atas kecepatan: C++ **tidak** boleh mengubah satu
angka pun, karena itu jalur ujinya adalah oracle Pygame yang sama dengan jalur
GDScript (bukan "C++ vs C++").

---

## Arsitektur

```
hero_skills/_bundle.py                     ← sumber kebenaran (pygame)
        │                                      │
        │ tools/gen_hero_skill_kit.py          │ tools/gen_hero_skills_cpp.py
        ▼                                      ▼
godot/scenes/hero/HeroSkillKit.gd   godot/gdext/mystic_skills/src/*.cpp
        │                                      │  scons + godot-cpp
        │                                      ▼
        │                    godot/addons/mystic_skills/bin/libmystic_skills.*
        │                                      │  (mystic_skills.gdextension)
        └────────► HeroSkillKitLoader.gd ◄─────┘   ClassDB "MysticHeroSkills"
                        ▲
                        │ const HeroSkillKit = preload(Loader)
                   Hero.gd (init_state / update_timers / cast_q..r / __by_pair0)
```

Loader memilih backend sekali (`_resolve()`), lalu **meng-cache instance**
GDExt: semua method `MysticHeroSkills` di-bind `ClassDB::bind_static_method`,
tapi Godot tetap butuh sebuah `Object` untuk `callv()` — tanpa cache, tiap
panggilan (termasuk tiap pembanding `sort_custom(__by_pair0)`!) mengalokasikan
instance baru.

API yang dipakai `Hero.gd` (identik di kedua backend):

```gdscript
HeroSkillKit.init_state(self)
HeroSkillKit.update_timers(self, units, towers, bases)
HeroSkillKit.cast_q(self, units, towers, bases)   # + cast_w / cast_e / cast_r
enemies.sort_custom(Callable(HeroSkillKit, "__by_pair0"))
```

### Peta berkas

```
godot/gdext/mystic_skills/
  SConstruct                       # output -> ../../addons/mystic_skills/bin/
  README.md                        # cara build + pemetaan transpiler
  src/register_types.{h,cpp}       # entry mystic_skills_library_init
  src/hero_skills_processor.h      # class MysticHeroSkills : RefCounted (generated)
  src/hero_skills_processor.cpp    # 432 definisi: helper + 6 starter + 66 boss (generated)
godot/addons/mystic_skills/
  mystic_skills.gdextension        # kunci linux.debug.x86_64 -> berkas template_debug
  bin/                             # hasil build (di-gitignore, kecuali .gitkeep)
godot/scenes/hero/HeroSkillKitLoader.gd
godot/tests/HeroSkillGdextParityTest.{gd,tscn}
tools/gen_hero_skills_cpp.py       # Python AST -> C++ (+ --check)
.github/workflows/godot-gdext.yml  # build lib + uji paritas C++
```

---

## Nama berkas lib: `debug` ≠ `template_debug`

Ini jebakan yang membuat GDExtension "sudah dibuild tapi tidak pernah dipakai".
Kunci di `[libraries]` memakai **nama target Godot** (`debug`/`release`/
`editor`), sedangkan **nilai**nya harus nama berkas hasil scons yang memakai
**nama target godot-cpp** (`template_debug`/`template_release`):

```ini
linux.debug.x86_64 = "res://addons/mystic_skills/bin/libmystic_skills.linux.template_debug.x86_64.so"
linux.release.x86_64 = "res://addons/mystic_skills/bin/libmystic_skills.linux.template_release.x86_64.so"
```

`libmystic_skills.linux.debug.x86_64.so` (nama lama di repo ini) **tidak pernah
dihasilkan** SConstruct — `env["suffix"]` godot-cpp adalah
`.linux.template_debug.x86_64`. Konvensi resmi:
`godot-cpp/test/project/example.gdextension`. Arch Android juga mengikuti
godot-cpp (`arm64`/`arm32`/`x86_64`), bukan nama `android_arch` scons
(`arm64v8`/`armeabi-v7a`). `mystic_lighting.gdextension` punya bug yang sama
dan ikut dikoreksi.

---

## Build

```bash
cd godot/gdext/mystic_skills
git clone -b godot-4.3-stable --depth 1 \
  https://github.com/godotengine/godot-cpp godot-cpp     # di-gitignore
scons platform=linux target=template_debug -j4           # dev / editor
scons platform=linux target=template_release -j4         # export release
# -> godot/addons/mystic_skills/bin/libmystic_skills.linux.template_debug.x86_64.so
```

Versi godot-cpp **harus** se-minor dengan engine (`compatibility_minimum = 4.3`
↔ `godot-4.3-stable`); ABI GDExtension berubah antar minor.

Nyalakan jalurnya di `godot/project.godot`:

```ini
[mystic]
skills/use_gdext_skills=true
```

Atau paksa dari kode (dipakai harness):

```gdscript
HeroSkillKitLoader.force_backend("gdext")     # "gdscript" | "" = ikut setting
print(HeroSkillKitLoader.backend_name())      # "gdext" / "gdscript"
```

Tanpa lib, atau dengan flag `false`, semuanya jatuh ke `HeroSkillKit.gd` —
tidak ada error, tidak ada perubahan perilaku.

---

## Paritas yang dikunci

### 1. Oracle Pygame (uji utama)

`HeroSkillGdextParityTest` **mewarisi** `HeroSkillParityTest` dan hanya
memaksa backend loader ke `gdext`, lalu memutar ulang fixture
`match_parity.json["hero_skills"]` yang direkam `tools/test_godot_match_parity.py`
dari `Hero.update` pygame ASLI: **222 hero × 4 skenario** (cluster / edge /
combo / empty), cast ber-skrip per frame, jejak event per frame (`bhp`, `dmg`,
`slow`, `alock`, `emove`, `bmove`, `bspd`, `batk`, `bdmg`, `bface`, `cast`,
`ask`, `attempt`) + state final (cooldown QWER, `active_skill`(+timer), kit,
HP/posisi/attack_timer probe). Rantainya jadi:

```
_bundle.py (pygame asli) ──rekam──► fixture ──bandingkan──► Hero.gd → Loader → MysticHeroSkills (C++)
```

Kalau lib tidak termuat, scene **GAGAL** (bukan skip) — CI yang menjalankannya
baru saja membuild lib, jadi "fallback diam-diam" harus terdeteksi. Penanda
yang di-require gate: `[HeroSkillGdextParityTest] PASS` **dan** baris loader
`GDExtension MysticHeroSkills aktif`.

### 2. A/B backend (closed-world)

Untuk API yang tidak pasti tersentuh replay, test yang sama membandingkan C++
vs GDScript langsung, untuk **semua** `hero_type` di `HeroDB.get_all_types()`:

- `hero_kind()` — dispatch starter vs boss (hero baru yang lupa masuk
  generator C++ ketahuan di sini);
- `visual_duration(hero_type, q/w/e/r)` — tabel `SKILL_VISUAL_DURATION` per
  kelas + `BOSS_HERO_VISUAL_DURATION` + default;
- `__by_pair0` dengan jarak **seri** — tie-break indeks = stabilitas `sort`
  Python.

### 3. Kesegaran transpile

`python3 tools/gen_hero_skills_cpp.py --check` (dan `gen_hero_skill_kit.py
--check`) jalan di **kedua** workflow: `godot-check.yml` (statis, tanpa
compiler) dan `godot-gdext.yml` (sebelum build). Berkas C++ yang ter-commit
harus byte-identik dengan hasil transpile `_bundle.py`.

---

## Bug paritas C++ yang ditemukan & diperbaiki (PR ini)

Semuanya di helper **tulis-tangan** generator (bodi 270 `_cast_*` hasil
transpile AST sudah 1:1 dengan GDScript):

| # | Gejala di C++ lama | Perilaku Python/GDScript | Perbaikan |
|---|---|---|---|
| 1 | `.gdextension` menunjuk `libmystic_skills.linux.debug.x86_64.so` | scons menghasilkan `...linux.template_debug.x86_64.so` | nilai `[libraries]` diperbaiki (+ arch Android `arm64`/`arm32`); `mystic_lighting` ikut |
| 2 | `by_pair0(a,b)` hanya membandingkan `a[0] < b[0]` | `nearby.sort(key=lambda t: t[0])` Python **stabil**; GDScript tie-break `int(a[2]) < int(b[2])` | pembanding C++ memakai (dist, idx) |
| 3 | `boss_generic` mengurutkan `nearby` dengan bubble-sort tukar-pasangan (tidak stabil) | urutan musuh berjarak sama harus tetap urut kemunculan | insertion sort dengan kunci (dist, idx) — identik sort stabil |
| 4 | `fallback_cast` memanggil `kit_hit(..., Variant(), school)` | `h.kit_hit(e, dmg, h.team, h, school)` — `src` = hero | `src = h`, kalau tidak atribusi damage/reflect (`CombatSystem.apply_damage`) kehilangan sumber |
| 5 | `trigger_q/w/e/r` menerima `kind` lalu **membuangnya**; durasi visual selalu dihitung dari `hero_type` | `__vis_dur(kind, h, key)`: kind `"boss"` → tabel boss, kind starter → tabel kelas | `visual_duration_kind(kind, hero_type, key)` + `set_active_skill(h, kind, key, duration)`; tabel **dibangkitkan dari data Python**, bukan angka hardcoded |
| 6 | `visual_duration()` (API loader) mencampur tabel boss & starter berdasarkan `hero_type` saja | kind diturunkan dari kelas handler | `is_starter_kind()` + delegasi ke `visual_duration_kind` |
| 7 | Loader mengalokasikan `ClassDB.instantiate()` **tiap panggilan** (termasuk tiap pembanding sort) | — | instance di-cache di `static var _inst` |
| 8 | Fallback GDScript `get_visual_duration()` mengembalikan angka 40 hardcoded | tabel durasi sebenarnya (60/90/60/100 + override) | fallback membaca konstanta `HeroSkillKit.gd` |
| 9 | `has_target` di-bind tanpa `DEFVAL` untuk `range_val` | `__has_target(..., range_val = null)` | `DEFVAL(Variant())` |
| 10 | `get_attack_cooldown_frames()` mengembalikan `attack_cooldown * 60.0` mentah (float) | GDScript: `int(roundf(float(h.attack_cooldown) * 60.0))` — **frame bulat** | `(double)(int64_t)round(v * 60.0)`. Tanpa ini `kit["_original_attack_cd"]` (Thorne R, Sylara Q) menyimpan 49.99998 alih-alih 50, dan `maxf(15, int(frame / 1.5))` bisa meleset satu frame |
| 11 | `X.attack_timer = N` (assign langsung) dipetakan ke `kit_lock` | Python `_bundle.py:4227` `h._shackle_target.attack_timer = 30` → GDScript `.attack_timer = float(30) / 60.0` (tulis apa adanya) | helper baru `set_atk_timer_frames(h, target, frames)` (guard `kit_has_atk_timer`, tulis `frames / 60.0`); `kit_lock` — yang memakai `maxf` — tetap untuk 74 situs berbentuk `max(X.attack_timer, N)` |
| 12 | `kit_catalog_all(h)[get_hero_type(h)]["damage"]` — index berantai `Dictionary::operator[]` **non-const** di atas temporary | GDScript `h.kit_catalog_all()[(h).hero_type]["damage"]` = 124 (alchemist) | helper `dict_at(container, key)` (`.get()` const, balik by-value, tanpa `ptrw()`/detach COW, tanpa menyisipkan NIL). Ketemu dari CI: **33 kegagalan / 22.594 check** — buff damage 7 skill boss (alchemist, drakar, ignis_drachorn, nyxarath, syrentha, thalgryn) jadi `int(100 × mult)` alih-alih `int(damage_katalog × mult)`, mis. 186 → 150 |
| 13 | `(double)(Variant)` / `(int)(Variant)` di 1.000+ situs | GDScript memperlakukan `null` sebagai 0 | `var_num()` / `var_int()`: switch eksplisit per tipe Variant, NIL/non-numerik → 0. godot-cpp `Variant::operator double()` menulis ke `double result;` **tanpa inisialisasi** lewat `to_type_constructor[FLOAT]`; kalau constructor gagal (sumber NIL/Dictionary) buffer dibiarkan → angka acak dari stack (inilah asal `100.0` = sisa `skill_range` di bug 12) |

### Audit literal per fungsi (cara bug 10 & 11 ketemu)

Selain oracle runtime, semua fungsi yang ada di **kedua** bahasa dibandingkan
secara statis: ekstraksi literal numerik & string dari badan fungsi GDScript
(`static func X`) dan C++ (`T MysticHeroSkills::X(Object* h, ...)`), lalu
normalisasi scaffolding (deklarasi `Variant x;`, loop `__i`, cast, `MAX(`/
`Math::fmod`, nama properti di `->set("hp", ...)` / `get_kit_value(h, "k")`,
komentar `## _bundle.py:NNNN-NNNN`). Hasil akhir: **312 fungsi dibandingkan,
0 selisih semantik**. Sisa selisih yang muncul semuanya struktural dan sudah
dijelaskan satu per satu:

| Selisih | Kenapa bukan bug |
|---|---|
| `60.0` ada di GDScript, tidak di C++ (7 fungsi: `sylara_cast_q/w`, `sylara_init_state`, `sylara_update_timers`, `thorne_cast_r`, `thorne_init_state`, `thorne_update_timers`) | faktor konversi frame↔detik pindah ke helper (`get/set_attack_cooldown_frames`, `get/set_speed_frames`, `set_atk_timer_frames`) — **arah & pembulatannya** diverifikasi per situs (bug 10 berasal dari sini) |
| `"boss"` hanya di GDScript (`init_state`, `update_timers`) | GDScript memakai `match kind:` dengan label `"boss"`; C++ memakai rantai `if/else` dengan `else` — `hero_kind()` hanya bisa mengembalikan 7 nilai, jadi `_ : pass` di GDScript tak terjangkau |
| `"skill_range"` hanya di C++ (`grimjaw_update_timers`) | bentuk `get_skill_data(h).get(Variant("skill_range"), 80)` vs `(h).skill_data.get("skill_range", 80)` — pembungkus `Variant(` lolos dari normalisasi |
| `hero_kind` (multiset label berbeda) | label `match` vs literal di rantai `||` — nilai kembalinya sama untuk tiap `hero_type` (dibuktikan A/B battery di `HeroSkillGdextParityTest`) |

Bug 12 & 13 **tidak** terlihat dari audit literal (angkanya sama persis dengan
GDScript: `1.5`, `124` tidak muncul sebagai literal karena datang dari katalog) —
yang menangkapnya oracle Pygame di CI. Pelengkapnya: audit literal menangkap bug
10 & 11, oracle menangkap 12 & 13; keduanya dibutuhkan.

Yang **tidak** diubah karena sudah benar (diaudit baris per baris vs GDScript):
`hero_kind`, dispatch `cast_q/w/e/r` + `update_timers` + `init_state`,
`skill_range` (fallback 200 + `max(attack_range, r)`), `enemies_in_range`,
`deal_aoe` (`int(skill_damage * mult)`, src=hero, school=`dmg_school`),
`acquire_target` (slack 1.15 + retarget), `cast_range` boss
(`max(int(skill_range or 100), 140)`), 66 resep `_SKILL_REGISTRY` (dibuktikan
sama dengan `RECIPE_TYPES` GDScript: 66 = 66, selisih himpunan kosong), dan
`_fallback_cast` (mult q1.0/w1.2/e1.5/r2.5, AOE 150/200).

Catatan: objek yang sudah `free()` aman di C++ — `Variant::operator Object*()`
me-resolve ObjectID dan memberi `nullptr`, jadi `if (tgt && ...)` setara
`is_instance_valid(tgt)` di GDScript.

---

## Testing

```bash
# 1. kesegaran transpile (tanpa compiler, detik)
python3 tools/gen_hero_skill_kit.py --check
python3 tools/gen_hero_skills_cpp.py --check

# 2. compile-check cepat tanpa build godot-cpp penuh (butuh gen/include)
g++ -fsyntax-only -std=c++17 -DGDEXTENSION \
  -I godot-cpp/gdextension -I godot-cpp/include -I godot-cpp/gen/include \
  -I src src/hero_skills_processor.cpp

# 3. build + link lib
scons platform=linux target=template_debug -j4

# 4. paritas runtime (butuh lib + Godot 4.3)
godot --headless --path godot res://tests/HeroSkillGdextParityTest.tscn --quit-after 900
godot --headless --path godot res://tests/HeroSkillParityTest.tscn --quit-after 900  # baseline GDScript
```

CI: `.github/workflows/godot-gdext.yml` menjalankan 1→4 (godot-cpp + binary
Godot di-cache; ±10 menit cache-hit, ±25 menit cold), lalu `godot-check.yml`
menjalankan langkah 1 + baseline GDScript tanpa compiler.

---

## Batas yang disengaja

1. **Flag produksi tetap `false`.** GDScript sudah paritas-terkunci dan tidak
   butuh toolchain; menyalakan C++ untuk semua pemain berarti mewajibkan lib
   per platform (termasuk 2 arch Android) di setiap rilis. Urutannya: paritas
   hijau di CI → benchmark di HP low-end → baru default dinyalakan.
2. **Android belum dibuild.** `build-android-godot.yml` tidak memanggil scons;
   export AAB tetap jalan dengan fallback GDScript. Butuh
   `scons platform=android target=template_release android_arch=arm64v8` +
   NDK, dan `.so` per arch masuk `addons/mystic_skills/bin/`.
3. **Tidak ada RNG di `hero_skills`** (`grep random` kosong) — jadi paritas
   deterministik penuh; tidak perlu `ParityRng` di jalur C++.
4. **`reloadable = true`** supaya hot-reload editor tidak perlu restart, tapi
   artinya lib boleh di-unload: loader menyimpan `Object` instance, bukan
   pointer C++.

## Next step (opsional)

- [ ] Benchmark `update_timers` 40 hero hidup: GDScript vs C++ (ms/frame) di
      Android low-end; jadikan dasar menyalakan flag default.
- [ ] Build `template_release` + Android arm64/arm32 di `build-android-godot.yml`.
- [ ] Sama untuk `mystic_lighting` (bug nama lib sudah diperbaiki, tapi belum
      ada workflow build + uji paritasnya).
- [ ] Perf: `kit_enemies` masih memanggil balik ke GDScript (`h.call(...)`)
      tiap cast — bisa dipindah ke C++ murni kalau profil menunjukkan itu
      bottleneck (perlu port filter tim/hidup, bukan sekadar copy).

## Referensi

- `hero_skills/_bundle.py` — sumber kebenaran (5.221 baris)
- `tools/gen_hero_skills_cpp.py` — transpiler C++ (+ `--check`)
- `tools/gen_hero_skill_kit.py` — transpiler GDScript (+ `--check`)
- `godot/gdext/mystic_skills/README.md` — pemetaan transpiler + cara build
- `godot/tests/HeroSkillGdextParityTest.gd` — harness C++
- `docs/GODOT_PARITY.md` — status paritas menyeluruh
- `docs/LIGHTING_GODOTPP.md` — pola godot++ pertama di repo ini
