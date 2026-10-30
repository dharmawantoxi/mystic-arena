# Migrasi folder `bosses/` (Pygame) → Godot

Status: **selesai — seluruh 61 berkas terklasifikasi, tidak ada perilaku runtime
yang tertinggal.** Layer ini (9bx) menambahkan inventaris per-berkas yang
diturunkan dari sumber, oracle + fixture, suite native, dan guard validator yang
mengunci klaim tersebut. Dokumen ini adalah laporan auditnya.

Sumber: `bosses/` (read-only oracle) · 61 berkas · 361.451 baris · 216 boss.
Target: `godot_rebuild/` · 216 body WebP (35 MB) · 216 baris stat · 80 arm AI ·
66 kit skill bos + 150 fallback sumber.

---

## 1. Cara membaca laporan ini

`tests/bosses_folder_source_oracle.py` menurunkan seluruh inventaris **dari
folder sumber**, tanpa pygame:

| Bagian sumber | Cara dibaca | Yang dihasilkan |
|---|---|---|
| `_boss_index.py` | `ast.literal_eval` pada `BOSS_INDEX` | 216 pasangan `id → (modul, draw_fn)` |
| `level*.py` | `ast` (tidak dieksekusi) | 219 definisi `draw_*`, 216 kelas `_NS_`, daftar modul per id |
| `base_boss.py` | `ast` + regex pada `Boss.update` | 79 `_smart_ai_*` dan urutan arm dispatch-nya |
| `boss_data.py` | `runpy` (modul ini tidak mengimpor pygame) | 162 mini + 54 true, `hero_unlock`, 6 tabel konstruksi |
| `*_v4.py` | `ast` | 3 renderer prosedural + bundle level yang me-re-export |

Hasilnya ditulis ke `tests/fixtures/bosses_folder_source.json` (`--write`) dan
dibandingkan setiap kali validator jalan, jadi klaim di bawah ini diperiksa,
bukan diketik manual.

Label status yang dipakai:

* **Diport** — logika/perilaku ada padanannya di Godot dan dikunci tes.
* **Diport (bake)** — piksel digambar ulang dari sumber saat build, hasilnya
  disimpan sebagai atlas; runtime tidak menggambar prosedural lagi.
* **Input-only** — hanya dipakai untuk membangun data lain saat build; tidak
  pernah dibaca saat permainan berjalan.
* **N/A** — konsep Python yang tidak punya padanan runtime (paket, peta impor).

---

## 2. Empat berkas struktural

| Berkas | Baris | Isi di Pygame | Padanan Godot | Status |
|---|---:|---|---|---|
| `__init__.py` | 1 | penanda paket `bosses` | tidak perlu: Godot memakai `preload` eksplisit per skrip | **N/A** |
| `_boss_index.py` | 228 | peta 216 `id → (modul, draw_fn)` untuk lazy import, dibuat `tools/gen_boss_index.py` | digantikan atlas yang di-key per `id` (`scripts/ui/boss_art.gd` + `boss_anim.gd`) dan `data/bosses/boss_stats.json`; peta 216 entrinya tetap dilacak di fixture | **N/A** (dikunci) |
| `base_boss.py` | 8.488 | kelas `Boss(TowerDebuffMixin)`: 210 method, 79 `_smart_ai_*`, `update()` sebagai dispatcher, heal anti-heal, enrage, entrance, aura, debuff | `scripts/match/boss_state.gd` (entitas, clock entrance/enrage, debuff, kite, kematian) + `scripts/match/boss_ai.gd` (80 arm) + `scripts/ui/boss_aura_fx_layout.gd` (aura/entrance FX) | **Diport** |
| `boss_data.py` | 11.842 | 216 baris stat (`MINI_BOSS_TYPES` 162 + `TRUE_BOSS_TYPES` 54), `hero_unlock` per bos, 6 tabel konstruksi | `data/bosses/boss_stats.json` (216 baris + `rules`) dan `data/heroes/*.tres` | **Diport** + 6 tabel **Input-only** |

### 2.1 Enam tabel yang hanya jadi input build

Semuanya didefinisikan di `boss_data.py` dan **tidak punya konsumen runtime** —
oracle memverifikasi ini dengan menyisir seluruh `*.py` di luar `bosses/`:

| Tabel | Isi | Konsumen |
|---|---|---|
| `MINI_BOSS_WAVES` | `{5: gornak, 10: morgath, 15: drakar}` | hanya `tools/convert_to_godot.py` |
| `LEVEL_TRUE_BOSS` | 54 entri level → bos true | hanya `tools/convert_to_godot.py` |
| `TRUE_BOSS_HP_CURVE` | 33 id, 52.000–167.000 | hanya `tools/convert_to_godot.py` |
| `TRUE_BOSS_DMG_CURVE` | 5 id, 150–318 | hanya `tools/convert_to_godot.py` |
| `TRUE_BOSS_ABILITY_CURVE` | 5 id, 423–495 | hanya `tools/convert_to_godot.py` |
| `MELEE_ROLE_HINTS` | 27 id melee | hanya `tools/` (converter + parity test) |

Nilainya sudah ter-embed ke hasil akhir: kurva/override masuk ke
`boss_stats.json`, dan hint melee sudah terlipat ke `attack_range` di
`data/heroes/*.tres`. `MINI_BOSS_WAVES` pun tidak dipakai permainan Pygame —
ke-54 konfigurasi level membawa daftar `mini_bosses` sendiri (level 1:
10=gornak, 15=morgath, 25=drakar), dan semua `data/levels/level_*.json` di
Godot sudah memuatnya.

---

## 3. Lima puluh empat modul level (216 body bos)

Satu modul = 4 bos = 4 kelas `_NS_<bos>` (body piksel) + 4 fungsi `draw_<bos>`
(komposisi frame). Godot tidak lagi menjalankan kode gambar ini: `bake/bake_boss_atlas.py`
memanggil jalur `Boss.draw` yang sama, mengambil keyframe idle/walk/attack/skill
untuk kedua facing, lalu menyimpannya sebagai satu atlas WebP per bos
(`assets/art/bosses/<id>.webp`, total 35 MB, `format: webp-lossless-v0`,
0 pose gagal di-bake). Status seluruh baris di bawah: **Diport (bake)**.

| Modul | Baris | Bos | Catatan |
|---|---:|---|---|
| `level1.py` | 10193 | `abaddon`, `drakar`, `gornak`, `morgath` |  |
| `level2.py` | 10774 | `alchemist`, `gorath`, `khalros`, `razak` | **re-export `razak_v4`** |
| `level3.py` | 5685 | `ancient_apparition`, `nyzrak`, `varkul`, `xerathis` | **re-export `nyzrak_v4`** |
| `level4.py` | 11116 | `ignis_drachorn`, `pyrenth`, `vokrahn`, `zharok` |  |
| `level5.py` | 6335 | `gravefang`, `krobellus`, `nyxara`, `vhalzun` | **⚠ `draw_morgath` mati** |
| `level6.py` | 6228 | `gravewake`, `kunkka`, `syrentha`, `thalgryn` | **re-export `thalgryn_v4`** |
| `level7.py` | 5398 | `akashari`, `malzareth`, `nyxarath`, `vorenmarr` |  |
| `level8.py` | 5595 | `vaerith`, `vhorethzir`, `vhyssarion`, `xirthalis` |  |
| `level9.py` | 7727 | `kenshiro`, `khazan`, `naraka`, `wiro` |  |
| `level10.py` | 6534 | `aurethzar`, `krognarr`, `raz`, `vraskhan` |  |
| `level11.py` | 4907 | `aeralith`, `aurex`, `nyxareva`, `thalakryon` |  |
| `level12.py` | 6572 | `aurelix`, `aurelyssa`, `nazulmor`, `vargrath` |  |
| `level13.py` | 6707 | `kaeldris`, `pyraklos`, `solvarin`, `velmyrth` |  |
| `level14.py` | 5987 | `azureth`, `luminar`, `pyraethis`, `solara` |  |
| `level15.py` | 6434 | `auroth`, `morvein`, `thorvak`, `yamako` |  |
| `level16.py` | 6158 | `ignirus`, `leoric`, `seiryukong`, `shirotaka` |  |
| `level17.py` | 5931 | `kaelthorn`, `nyxareth`, `solvanth`, `xyrael` |  |
| `level18.py` | 7225 | `aurelion`, `cryssalia`, `kaelthar`, `morkhaera` |  |
| `level19.py` | 6432 | `akahime`, `nyxthrael`, `sylvantheros`, `vaelindra` |  |
| `level20.py` | 6774 | `astraelion`, `morthraxis`, `morvaenthir`, `thornvaegrim` |  |
| `level21.py` | 5118 | `kurogari`, `morvekhar`, `nexthyrius`, `vorgath` |  |
| `level22.py` | 4922 | `grimstalker`, `kryvoxar`, `molgravar`, `vargroth` |  |
| `level23.py` | 5760 | `drav`, `lyrienne`, `seraphienne`, `valthar` |  |
| `level24.py` | 5768 | `khalzaredh`, `nyxaroth`, `solareth`, `veshtrax` |  |
| `level25.py` | 6538 | `grimjack`, `morvaeth`, `okeanora`, `vulkareth` |  |
| `level26.py` | 5307 | `aelyrion`, `kaervosth`, `morvyssk`, `vaelmyrra` |  |
| `level27.py` | 5701 | `kyumirra`, `morvakhul`, `nyxariel`, `zarethyr` |  |
| `level28.py` | 6256 | `morthyrax`, `nyrethzalv`, `sanguiveth`, `xerakhotep` |  |
| `level29.py` | 6894 | `ignakhor`, `kazureth`, `nyrellieth`, `sethrakhar` |  |
| `level30.py` | 5760 | `kaelvyrn`, `nyxharr`, `thorvin`, `xaerissa` |  |
| `level31.py` | 6166 | `celwynn`, `ravokkar`, `rynvara`, `syrindra` |  |
| `level32.py` | 5903 | `ghrakmaal`, `malzeroth`, `selunara`, `vessyra` |  |
| `level33.py` | 5970 | `rakzhan`, `sirakzan`, `valekris`, `zharakzuul` |  |
| `level34.py` | 5544 | `grondmauris`, `infrakzaar`, `xarnathul`, `zhyrakaan` |  |
| `level35.py` | 5477 | `kaerissa`, `lyssarethys`, `thorgaruk`, `zorathiel` |  |
| `level36.py` | 5560 | `kaerinya`, `nyxallaria`, `vhaerinth`, `xharokh` |  |
| `level37.py` | 6137 | `kazreth`, `varkuthar`, `xelnarath`, `zhyvrek` |  |
| `level38.py` | 5950 | `azkharion`, `kyrenzai`, `thargoroth`, `zahkareth` |  |
| `level39.py` | 5194 | `bhorgathul`, `morkhelvis`, `vorthakul`, `xaelmoran` |  |
| `level40.py` | 5371 | `thalryndel`, `urgharun`, `yhoranth`, `zulkhaven` |  |
| `level41.py` | 4669 | `emberwick`, `grimkor`, `grondarthul`, `xareth` |  |
| `level42.py` | 4927 | `kaedrin`, `kaineroth`, `morvaeth2`, `vardrok` |  |
| `level43.py` | 4802 | `nixweaver`, `nyxraal`, `xarnthuul`, `zyvareth` |  |
| `level44.py` | 4784 | `kagetsuka`, `lyrenya`, `vyraeth`, `zorothrax` |  |
| `level45.py` | 5251 | `akiraze`, `brumhar`, `deidara`, `zorashi` |  |
| `level46.py` | 6172 | `akaroth`, `kassadin`, `shimorakh`, `sunakage` |  |
| `level47.py` | 6247 | `kaizoku_raijin`, `korokai`, `pyraena`, `verdanix` | **⚠ `draw_kaizoku_raijin` didefinisikan 2×** |
| `level48.py` | 5793 | `broggmar`, `cogsworth`, `ursath`, `zhaeris` | **⚠ `draw_ursath` didefinisikan 2×** |
| `level49.py` | 6945 | `kairenji`, `karzhul`, `xerakkuth`, `yomigetsu` |  |
| `level50.py` | 5960 | `akirakumo`, `kaelthys`, `kaoruken`, `vaelkorr` |  |
| `level51.py` | 6139 | `aurelian`, `kaithros`, `morvath`, `pyrhaan` |  |
| `level52.py` | 6166 | `garumenshi`, `nyxaris`, `thoraz`, `vhaerith` |  |
| `level53.py` | 6188 | `dorakai`, `hitokage`, `kazuren`, `tsukiyora` |  |
| `level54.py` | 5202 | `hollowbane`, `obanai`, `sanguire`, `sasori` |  |

Catatan atas tabel itu:

* `morvaeth` (level25) dan `morvaeth2` (level42) adalah **dua bos berbeda**;
  `level42.py` mendefinisikan `_NS_morvaeth` sendiri dan `draw_morvaeth2`
  memakainya. Di Godot keduanya id terpisah di `boss_stats.json` — sesuai sumber.
* `aurex` memakai kelas `_NS_aurex_omega`, jadi 216 kelas `_NS_` menghasilkan
  215 nama unik. Jumlah kelasnya tetap satu per bos dan itu yang dikunci suite.
* `level2.py`, `level3.py`, `level6.py` bukan hanya bundler: masing-masing
  me-re-export renderer `razak_v4` / `nyzrak_v4` / `thalgryn_v4` (bagian 4).

---

## 4. Tiga renderer prosedural (`*_v4.py`)

| Berkas | Baris | Isi | Diekspor oleh | Pemakai lain | Status |
|---|---:|---|---|---|---|
| `razak_v4.py` | 3.239 | kelas `_NS_razak` + helper piksel (`px_rect`, `px_line`, `px_poly`, `px_dither`, `px_ramp_h`), rig penuh | `level2.py:40` | `heroes/razak_fx.py` | **Diport (bake)** |
| `nyzrak_v4.py` | 2.663 | `_NS_nyzrak` + helper piksel | `level3.py:4025` | `heroes/nyzrak_fx.py` | **Diport (bake)** |
| `thalgryn_v4.py` | 1.737 | `_NS_thalgryn` + helper piksel | `level6.py:4192` | `heroes/thalgryn_fx.py` | **Diport (bake)** |

Ketiganya murni renderer (tidak menyentuh gameplay), sehingga padanan Godot-nya
adalah hasil bake yang sama persis dengan yang digambar `Boss.draw`. Rig yang
dipakai ulang oleh `heroes/*_fx.py` untuk potret hero Razak/Nyzrak/Thalgryn
masuk wilayah folder `heroes/`, bukan folder ini.

---

## 5. Tiga cacat di oracle sumber (bukan bug port)

Oracle menemukan tiga body yang tidak pernah dipakai permainan Pygame. Godot
tidak kehilangan perilaku apa pun, tetapi cacat ini harus tercatat supaya tidak
dikira "kurang diport":

| Lokasi | Jenis | Akibat |
|---|---|---|
| `level5.draw_morgath` | tidak ada di `BOSS_INDEX` (`morgath` di-index ke `level3.draw_morgath`) | body level5 tidak pernah dipanggil |
| `level47.draw_kaizoku_raijin` (2×) | definisi ganda dalam satu modul | Python memakai definisi **terakhir**; bake juga memakai yang terakhir |
| `level48.draw_ursath` (2×) | definisi ganda dalam satu modul | idem |

Selain itu, `urgharun` adalah satu-satunya arm AI yang **hanya ada di Godot**
(`boss_ai.gd`), karena resep sumbernya tidak punya arm `_smart_ai_urgharun` di
`Boss.update` — 79 arm sumber, 80 arm native.

---

## 6. Bukti: apa yang mengunci apa

| Aspek | Oracle / fixture | Suite native |
|---|---|---|
| 216 baris stat + `rules` | `boss_core_source_oracle.py` → `fixtures/boss_core_source.json` (kesetaraan persis dengan `boss_stats.json`) | `boss_core_checks.gd`, `boss_match_checks.gd` |
| 216 body + keyframe | `bake/bake_boss_atlas.py` → `data/art/bosses.json` | `boss_art_checks.gd` (decode 216 WebP, anchor, facing, quantum pose) |
| 79 arm AI | `boss_ability_source_oracle.py`, `boss_ai_slow_source_oracle.py`, `boss_attack_lock_*`, `boss_buff_expiry_*`, `boss_buff_scaling_*`, `boss_shake_sites_*`, `boss_hero_ai_source` | `boss_ai_slow_checks.gd`, `boss_attack_lock_checks.gd`, `boss_level_*_checks.gd` (20 modul) |
| 66 kit skill bos | `boss_level_*_source_oracle.py`, `source_shared_boss_oracle.py` | 20 suite `boss_level_*_checks.gd` + `source_shared_boss_checks.gd` |
| 150 fallback sumber | `source_shared_boss_oracle.py` → `fixtures/source_shared_boss.json` | `source_shared_boss_checks.gd` |
| Harga/unlock hero bos | `meta_hero_unlock_source_oracle.py` (policy: starter 0, mini 4500, true 4500) | `meta_hero_unlock_checks.gd`, `hero_unlock_store` |
| **Inventaris 61 berkas** | **`bosses_folder_source_oracle.py` → `fixtures/bosses_folder_source.json`** | **`bosses_folder_checks.gd`** |

Total di sisi bos: **64 oracle** + **68 suite native** (`tests/boss_*`), plus
suite folder ini.

`schema` yang dikunci `bosses_folder_checks.gd` (bukan hanya hitungan):

1. 216 id sumber = 216 baris `boss_stats.json` = 216 `.tres` hero =
   216 body di `data/art/bosses.json`, dengan kelas mini/true identik.
2. `cost` di setiap `.tres` bos = `hero_unlock.cost` sumber (500–9.000).
   `unlock_cost` sengaja **0** karena `_core.py` menimpanya dengan kebijakan
   starter 0 / mini 4.500 / true 4.500 untuk seluruh 216 hero — lihat
   `docs/GODOT_PYGAME_PARITY_STATUS.md`.
3. Setiap id bos punya **tepat satu** rumah skill lewat resolver yang sama
   dengan yang dipakai pertandingan
   (`SourceSharedBossSkills.IDS` → 150, selain itu
   `BossRecipeRegistry.handler(id, NATIVE_SKILLS)` → 66). Tidak ada yang
   dobel, tidak ada yang yatim.
4. 80 arm `boss_ai.gd` = 79 arm sumber + `urgharun`; 136 bos sisanya masuk
   jalur ability generik, sama seperti sumber.

---

## 7. Sisa pekerjaan

Tidak ada pekerjaan port yang tersisa di folder ini: ke-61 berkas sudah
**Diport**, **Diport (bake)**, **Input-only**, atau **N/A** dengan bukti di atas.

Yang masih terbuka, tetapi berada di luar folder `bosses/`:

* verifikasi visual di perangkat Android nyata untuk komposit pertandingan
  (bukan hanya sprite bos yang sudah di-bake);
* screenshot pembanding per level/bos dari pengguna (`tools/measure_android_screenshot.py`);
* level 2–54 belum punya konfigurasi wave penuh di Godot untuk *seluruh*
  isi level (gelombang minion, tower, dst) — bosnya sudah siap, levelnya belum.
