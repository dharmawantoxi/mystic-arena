# VARKUL V3 — COMBAT FX / GAME FEEL (procedural)

Karakter: **`varkul`** — The Frostfang / Frost Sorcerer, mini-boss Level 3
(`bosses/level3.py`, class `_NS_varkul`). Penulisan ini mengikuti standar
rewrite **Thorne v2 / Xerathis v3**: renderer canvas tetap sumber pose,
semua yang bergerak 60 fps hidup di **lapisan layar 1:1**. 100% prosedural —
tanpa PNG / JPG / sprite-sheet.

## Pembagian kerja

| Renderer (canvas, di-cache)           | `heroes/varkul_fx.py` (layar, hidup)      |
| ------------------------------------- | ------------------------------------------ |
| Rig lich + outline siluet + rim light | trail sapuan staff dari histori posisi     |
| Bayangan, aura es, platform es        | particle (es, salju, debu, mist, shard)    |
| Pose idle/walk/attack/cast            | proyektil Frost Bolt (sistem nyata)        |
| **Ayunan ARK staff** (`_staff_arc`)   | orb Chain Frost memantul + petir es        |
| Hurt-flash (siluet badan)             | SkillFX cast → release → after → fade      |
| Fallback skill canvas q/w/e/r         | impact flash + shockwave + hit-stop + shake |

## File

- `heroes/varkul_fx.py` — paket game-feel lengkap (particle, trail,
  impact, proyektil, SkillFX, director, debug overlay).
- `bosses/level3.py` — animation controller V2 + tabel `_staff_arc` +
  pose CAST + bridge lapisan hidup.
- `bosses/base_boss.py` — hook impact bolt & 4 skill ke lapisan hidup.
- `heroes/__init__.py`, `_core.py` — registrasi pipeline FX / HUD perf.
- `tools/test_varkul_v3_combat.py` — regression test (14 grup).
- `tools/_shot_varkul_v3.py` — preview generator.

## Ayunan ARK (bukan translasi)

Staff tidak pernah dipindahkan dari titik A ke B. Sudut staff
(`theta`, radian dari vertikal) diinterpolasi lewat tabel
`_NS_varkul.STAFF_ARC` — satu sumber kebenaran yang dibaca renderer
canvas **dan** modul hidup (`staff_arc()`):

```text
ANTICIPATION 0.00-0.14  angkat (ease-out)
WIND-UP      0.14-0.32  putar ke belakang -66° (smoothstep)
SWING        0.32-0.52  sapu cepat +81° (out-cubic, momentum)
IMPACT       0.52-0.64  tahan + overshoot sinus
FOLLOW       0.64-0.82  rileks ke -28°
RECOVERY     0.82-1.00  kembali netral
```

Jendela hit aktif: `0.38-0.64`; proyektil dilepas `0.38-0.48`
(saat ark melewati vertikal). Trail mengikuti crystal head, jadi
membentuk **sabit** yang mengikuti arah serangan.

## Animation state

```text
IDLE WALK RUN ATTACK SWING CAST SKILL SPECIAL HIT HURT DEATH CHARGE
```

Pose baru **CAST** (q/w/e/r): staff terangkat, orb tangan membesar
mendekati rilis, rune berputar; transisi attack↔cast memakai tabel ark
yang sama.

## Skill FX (lifecycle cast → charge → release → after → fade)

| Skill | Nama          | Visual kunci                                                     |
| ----- | ------------- | ---------------------------------------------------------------- |
| q     | Frost Blast   | telegraph cincin putus → komets + halo shard → nova duri es       |
| w     | Frostbite     | bolt → **kurungan kristal poligonal** ber-facet + retak           |
| e     | Sacrifice     | **pentagram rune** elips + soul wisps naik + halo heal            |
| r     | Chain Frost   | charge spiral + dashed rune ring → **orb memantul 4x** + petir es |

Tiap pantulan orb: impact mini + serpihan; expire: impact penuh.

## Game feel

- Hit-stop di-bus `heroes/combat_feel.py` (0.03–0.08 s; R lebih berat).
- Screen shake trauma-based, decay bertahap (`shake_strength`,
  `shake_duration`).
- Impact bolt: flash + ring shockwave chunky + fragmen sabit + streak +
  shard (gravity) + mist — plus shake & hit-stop.
- Kematian: badan pecah jadi serpihan kristal (sekali per unit).
- Particle cap `MAX_PARTICLES = 190`; projectiles `18`; skills `5`;
  impacts `8`. `reset_all()` melepas semua director — tidak ada FX
  bocor antar match.

## Performance

- Semua glow/ring/spark/ellipse/snowflake = **cached surface** (satu
  blit per pemakaian, alpha via pool scratch buffer).
- Canvas boss tetap 1.46 ms/frame idle (budget 2.35 ms, `tools/
  test_level3_masterwork.py`).
- Fallback canvas q/w/e/r otomatis mati saat lapisan hidup mengambil
  alih (`owned`) — tidak ada efek digambar dua kali.

## Debug

Set `DEBUG_CHARACTER = True` di `heroes/varkul_fx.py` **atau**
`_NS_varkul.DEBUG_CHARACTER`: hitbox, hurtbox, jendela hit, jangkauan,
collision proyektil, state anim, fase, frame, FPS, jumlah partikel,
jumlah skill/impact, dan timer serangan.

## Uji

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 tools/test_varkul_v3_combat.py
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 tools/test_level3_masterwork.py
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 tools/_shot_varkul_v3.py
```
