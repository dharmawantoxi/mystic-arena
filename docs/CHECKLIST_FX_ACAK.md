# Checklist Visual — "Skill FX Keluar Random di Peta"

Dokumen ini untuk uji visual manual setelah perbaikan koordinat FX.
Semua hero di bawah hidup di lapisan "LIVE FX" yang digambar **1:1 ke
layar**, sedangkan `_render_scale` hanya konversi di dalam canvas sprite.
Jadi:

- **Titik target / titik mendarat** = offset DUNIA terhadap unit
  (`tgt.x - hero.x`), **tanpa** `_render_scale`.
- **Radius AoE / ring tanah** = radius DUNIA (`WORLD_RADIUS`), **tanpa**
  `body_scale`.
- Offset **lokal badan** (pegangan senjata, garis kaki, ketebalan garis,
  jarak partikel dekat tubuh) boleh tetap memakai `body_scale`.

---

## 0. Persiapan

1. Jalankan game di resolusi 1280x720 (atau target Android).
2. Aktifkan debug overlay bila tersedia:
   `DEBUG_CHARACTER = True` di `heroes/*_fx.py` yang diuji.
3. Paksa hero berada di **lane** (tim pemain / musuh), bukan portrait.
4. Untuk menguji "FX terpanggang di cache": panggil
   `heroes.clear_hero_sprite_cache()` sekali, lalu jalankan beberapa detik.
   Efek yang benar TIDAK menempel di sekitar badan hero dan TIDAK ikut
   berkedip saat pose cache terpakai ulang.
5. Benching di HP/device rendah: pastikan tidak ada slow-motion
   (target ≥ 60 FPS di arena, ≥ 30 FPS di HP).

---

## 1. Hero dengan perbaikan TITIK TARGET / LANDING

Untuk tiap hero, uji **Q/W/E/R** satu per satu sambil hero bergerak dan
musuh bergerak. Yang perlu diperhatikan:

- Proyektil / gelombang / molotov mendarat **tepat di posisi musuh**
  (toleransi ±8 px), bukan di titik kosong di tengah peta.
- FX tidak "melompat" jauh dari arah hadap.
- Fallback saat target mati: FX normal ke depan sesuai `direction`.

| Hero | Q | W | E | R | Catatan penting |
|---|---|---|---|---|---|
| **Alchemist** | botol acid → musuh | ledakan AOE | aura badan | badai koin | Molotov Q di `_watch_engine_events`; `target_screen()` 1:1 |
| **Ancient Apparition** | vortex → posisi `vortex_x/y` | beam | ice blast | erupsi | `world_anchor()` sudah 1:1; fallback 160 px ke depan |
| **Razak** | molotov Sticky Napalm → target | cone api | firefly dash → landing | pilar api | E harus mendarat di titik BARU setelah dash, bukan titik awal |
| **Nyzrak** | lanset es | beam arctic | tombak thrust | kubah es | E (thrust) lepas dari ujung tombak; Q/W/E/R cast target 1:1 |
| **Pyrenth** | Doom Bolt → target | DEVOUR (self) | SCORCHED EARTH (self) | INFERNAL BLADE (self/lunge) | Q bolt harus sampai ke target; E/W berpusat di kaki, R di ujung lunge |
| **Vokrahn** | Chaos Bolt → target | soul ember (self) | Chaos Strike (dash 80 px) | infernal arc (self) | E target = titik pendaratan dash, bukan caster |
| **Zharok** | Strafe volley → target | skeleton walk (self) | death pact (self) | burning army (self) | Anak panah harus mendarat di target, bukan `range/_render_scale` |

**Kriteria LOLOS:**

- [ ] Titik impact / landing berubah mengikuti target secara halus.
- [ ] Saat target bergerak, FX tetap menempel pada target (tidak telat jau
      / tidak meleset konstan).
- [ ] Saat target mati di tengah cast, FX tetap berakhir wajar (tidak
      menembak ke koordinat sisa).

---

## 2. Hero dengan perbaikan RADIUS AoE (ring tanah)

Untuk tiap hero, uji Q/W/E/R dan bandingkan: **cincin tanah harus kira-kira
selebar `skill_range` hero** (world px), bukan mengecil mengikuti sprite
yang di-scale.

| Hero | Q | W | E | R |
|---|---|---|---|---|
| **Gravefang** | 120 | 150 | 100 | 180 |
| **Nyxara** | 130 | 150 | 100 | 150 |
| **Vhalzun** | 130 | 150 | 60 | 150 |
| **Alchemist** | 100 | 100 | 90 | 200 |
| **Razak** | 75 | 95 | 80 | 180 |
| **Ignis Drachorn** | 120 | 120 | 130 | 160 |

**Kriteria LOLOS:**

- [ ] Radius ring ≈ `WORLD_RADIUS` di atas (tidak terlihat 30–50% lebih
      kecil karena `body_scale`).
- [ ] Partikel yang meledak/naik dari dalam AoE berada di dalam ring
      (bukan hanya di dekat kaki).
- [ ] Pilar/batu/totem/retakan berada di dalam ring, bukan mengerucut ke
      badan.
- [ ] Hero yang di-smoothscale (tim lawan) tetap menunjukkan AoE dengan
      ukuran yang sama seperti saat menjadi mini boss.

---

## 3. Perbaikan cache — RX renderer tidak "terpanggang"

Berlaku untuk **seluruh hero live-FX** (`_LIVE_FX_HEROES`), khususnya yang
memakai list renderer:

`_sy_projectiles`, `_aa_beams`, `_vk_chain_orbs`, `_nyz_shards`,
`_gw_effects`, `_sy_effects`, `_kk_effects`, `_alch_patches`,
`_alch_coins`, `_zh_arrows`, `_zh_skulls`, `_pyr_arcs`, `_pyr_chains`,
`_razak_patches`, `_sel_eclipse_beams`, `_vok_bursts`, `_drk_projs`,
`_th_trail_samples`, `_kk_trail_samples`.

**Kriteria LOLOS:**

- [ ] Hero yang sedang menyerang: proyektil/panah TIDAK menempel diam di
      sekitar badan hero (gejala lama: orb "acak" di pinggir sprite).
- [ ] Setelah beberapa detik (cache hit), posisi proyektil tetap bergerak
      normal — tidak membeku pada pose yang di-cache.
- [ ] Saat mode "hero lane" dan "boss lane" dibandingkan, FX skill muncul
      di posisi yang sama.

---

## 4. Uji regresi cepat (semua hero live-FX)

Jalankan satu siklus `Q → W → E → R` pada setiap hero ini (27 hero):

`zephyr, gornak, grimjaw, kaizen, vex, sylara, abaddon, gorath, razak,
khalros, alchemist, ancient_apparition, nyzrak, xerathis, varkul,
ignis_drachorn, zharok, vokrahn, pyrenth, krobellus, vhalzun, nyxara,
gravefang, thalgryn, kunkka, syrentha, gravewake`

- [ ] Tidak ada TypeError/AttributeError di console saat cast.
- [ ] Tidak ada efek yang berkedip (hilang-muncul) di frame ganjil.
- [ ] Tidak ada efek yang "nyasar" ke titik di luar peta (koordinat
      negatif ekstrem / di luar arena).
- [ ] SETELAH battle selesai: tidak ada skill impact / partikel yang
      bertahan abadi di peta.

---

## 5. Cara menampung bukti

Paling mudah dijalankan dengan satu musuh di depan dan satu tanpa target:

1. Tembak Q ke musuh yang berdiri diam → cek titik mendarat.
2. Tembak Q sambil hero bergerak / target bergerak → cek titik mendarat
   tetap mengikuti target.
3. Cast W/E/R tanpa target → cek semua efek berpusat sesuai desain
   (self / landing / caster).
4. Cast W/E/R dengan target → cek AoE tidak mengecil, tidak mundur lebih
   dekat ke hero.
5. Bandingkan dengan mode `HERO_CACHE_ENABLED = False` (heroes/__init__.py)
   untuk memastikan posisi FX identik antara cache dan non-cache.

---

## 6. Catatan tambahan untuk dev

- Jangan pernah memakai `_render_scale` pada **titik target** di lapisan
  hidup. Konversi itu milik `bosses/level*.py::_world_to_local` / `_target_position`
  untuk **canvas** sprite.
- `ring_radius()` / `r_screen()` di `pyrenth/vokrahn/zharok` kini
  mengembalikan radius dunia (identitas) — jangan dikembalikan ke
  `world_px / render_scale`.
- Offset lokal (grip/tip/ground/tebal garis) tetap pakai `body_scale`.
