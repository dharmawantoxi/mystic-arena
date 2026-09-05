# Gornak v5 — Penulisan Ulang Total (Renderer + Lapisan FX Hidup)

Dokumen ini mencatat rewrite "dari nol" karakter Gornak (boss level 1 /
hero yang bisa direkrut), sesuai mandat: **100% pixel art prosedural, tanpa
aset bitmap eksternal, tanpa tambal-sulam kode lama**.

## 1. Pemecahan modul

| Modul | Peran |
|---|---|
| `bosses/gornak_v5.py` | Renderer + controller animasi penuh: kelas `_NS_gornak` dengan lapisan modular (`render_body`, `render_rig`, `render_shadow`, `render_skill_ground`, `render_skill_foreground`, dst.), pose router 12 state, kurva ayunan, telegraph dunia E/R, plus alias-alias lama (`draw_gornak`, `PALETTE`, `SKILL_DUR`, ...) untuk kompatibilitas tooling. |
| `bosses/level1.py` | Inang tipis: mengimpor ulang namespace gornak dari v5. **Tidak menyentuh** `morgath`/`drakar`/`abaddon` atau jalur publik `draw_*` karakter lain. |
| `heroes/gornak_fx.py` | "Lapisan hidup" 1:1 di luar cache sprite hero: `Particle`/`ParticleSystem` (pool + cap + budget kualitas), `SwingTrail` (pita bilah sector-arc), `ImpactFX` (4 bahasa: blade/mana/ward/void implosi), `GornakProjectile`+`ProjectileSystem` (bolt visual-only, damage TETAP milik `hero_skills`), `SkillFX` (lintasan 5-fase per skill), `GornakFXDirector` (watcher state engine + orkestrasi). |
| `heroes/combat_feel.py` | Bus SHARED hit-stop + screen-shake (juga dipakai Zephyr dkk.) — tidak ada salinan matematika per karakter. |

Kontrak dua-lane dipertahankan: lane **boss** menggambar unit + FX hidup di
kanvas penuh (FX ikut di-cache bersama pose), lane **hero** meng-cache
sprite badan saja lalu menggambar FX hidup per frame di atasnya dengan
`_render_scale`. Renderer mensupresi lapisan yang sudah diambil alih modul
FX (`_draw_crescent_slash`, `_draw_manabreak_foreground`) — dan jatuh
kembali ke fallback kanvas kalau modul FX tidak ada (dijaga
`test_jalur_boss_mengambil_alih_effect` / `test_fallback_canvas_saat_modul_fx_tidak_ada`).

## 2. Hal-hal yang dikunci test

- **Palet satu sumber**: `GORNAK_PALETTE` lapisan hidup = salinan hidup dari
  `_NS_gornak.PALETTE` lewat `_PALETTE_SYNC` + `_sync_palette()` (dipanggil
  saat import dan tiap pergantian arena). Tidak ada angka warna independen
  yang boleh melenceng (test drift palet).
- **`glow_surface` PREMULTIPLIED** — intensitas dikalikan ke RGB dan disalin
  ke alfa, gradien digambar luar→dalam. Ini memenuhi audit
  `tools/test_boss_no_white_cover.py`: blit `BLEND_RGB_ADD` tidak boleh
  berubah jadi cakram solid yang menutupi dada karakter. FX gornak kini
  2.7–8.5% piksel putih (ambang 12%) dan lum+≤31 (ambang 60).
- **Cincin dunia E/R** digambar lewat `_draw_e`/`_draw_r` (kontrak
  `tools/test_no_caster_light_pillar.py`: BUKAN pilar cahaya di badan;
  radius presisi = 100/180 px dunia, `ring_surface` berhenti tepat di
  radius gameplay).
- **Delta-time** di semua decay (partikel, trail 0.24 s, impact
  0.30+0.11·power, SkillFX per-timeline); `F.tick(dt=None)` memakai dt bus
  (`combat_feel.fx_dt()`, melambat saat hit-stop) dengan guard frame-sama
  sehingga N unit tidak menggandakan kecepatan FX.
- **Pool & cap**: partikel 170, proyektil 16, impact 8, SkillFX 4,
  registry director maksimum 12 (FIFO) — tidak ada alokasi objek per frame;
  `stats()["dropped"]` melaporkan tekanan.
- **Tidak ada efek abadi**: suite v3 mewajibkan `total_particles()==0`,
  impacts/trail kosong, dan surface bounding-box hampa setelah 400 frame.

### Timeline SkillFX (detik)

| skill | charge | release | area | impact | fade | total |
|---|---|---|---|---|---|---|
| Q | 0.20 | 0.10 | 0.20 | 0.12 | 0.16 | 0.78 |
| W | 0.14 | 0.20 | 0.08 | 0.04 | 0.06 | 0.52 |
| E | 0.30 | 0.34 | 0.24 | 0.14 | 0.14 | 1.16 |
| R | 0.46 | 0.20 | 0.46 | 0.22 | 0.38 | 1.72 |

Bahasa visual: Q = konduksi (shard tertarik ke genggaman, bolt lahir dari
UJUNG BILAH ≤10 px), W = siluet memudar + stretch void + burst di titik
ASAL blink, E = kubah heksagon menutup lalu pecah + cincin lantai presisi
100 px, R = pilar hisap gelap + cincin konvergen + IMPLOSI void + gelombang
kejut melebar. Fase pelepasan R ditiru dari engine (`mana_void_x` aktif saat
`timer <= SKILL_DUR − 24`), jadi impact muncul di pusat void, bukan di badan.

## 3. Performa

`draw_gornak` idle jalur boss: **1.46 ms/frame** di sandbox (anggaran < 5
ms). Anggaran `test_lapisan_hidup_cepat` (tick + dua lapisan per frame):
lolong dengan margin besar; cache surface dibatasi `_SURF_CACHE_MAX=384`
dengan daur- ulang paling-awam; kualitas mobile (`mobile.perf.Quality`)
memangkas jumlah partikel via `_budget_particles`.

## 4. Cara memverifikasi

```bash
python3 -m pytest tools/test_gornak_v3_combat.py -q        # 62 tes kontrak
python3 tools/test_gornak_masterwork.py                     # suite masterwork v5
python3 tools/test_boss_no_white_cover.py                   # audit "FX tak menutupi"
python3 tools/_shot_gornak_v5.py                            # regenerasi sheet
# hasil sheet: docs/gornak_v5_poses.png / _fx.png / _lanes.png
```

Status terakhir (2026-09-05): v3 combat **62/62**, masterwork **OK**,
starter-boss+fx-sweep **92/92**. Dua kegagalan yang MASIH ADA di kepala
repo dan bukan milik Gornak dibiarkan apa adanya: `nyzrak tidak tertutup FX`
(audit white-cover) dan penanda `heroes/_bundle.py` pada
`test_no_caster_light_pillar` — keduanya gagal di commit dasar dan menyentuh
karakter lain.

## 5. Yang TIDAK berubah

Data karakter, stat, kalkulasi damage, targeting, AI musuh, logika tower,
dan game loop tidak disentuh. `hero_skills`/`_bundle` tetap satu-satunya
pemegang kebenaran damage; bolt/proyeksi di lapisan hidup adalah visual
semata (`damage == 0` dijaga test).
