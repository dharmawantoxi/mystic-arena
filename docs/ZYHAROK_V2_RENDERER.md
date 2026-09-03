# Zyharok / Zharok — penunjuk dokumentasi

Zharok punya DUA dokumen, keduanya masih berlaku:

- **[ZHAROK_V3_COMBAT_FX.md](ZHAROK_V3_COMBAT_FX.md)** — versi terkini.
  Renderer + mesin combat-FX & game feel (`heroes/zharok_fx.py`):
  controller animasi, ARC stave busur + Ember Cleave, swing trail,
  particle system, proyektil modular, skill FX 6 fase, impact,
  hit-stop 0.03-0.08 s, screen shake, debug mode, dan anggaran performa.
- **[ZHAROK_V2_RENDERER.md](ZHAROK_V2_RENDERER.md)** — fondasi rig yang
  masih dipakai v3 apa adanya:
  - Rig 1.5x native & skala mini-boss level-4
  - 55-swatch HD Emberborn palette & pixel-art discipline
  - Timeline archery 7-keyframe + IMPACT frame di `ap=0.52`
  - Skill FX world-space 3 tahap (Q 250 / W 200 / E 150 / R 220 px)
  - Proyektil kustom `FireArrow` & `BurningSkull` (fallback canvas)
  - Audit & benchmark performa
  - Preview sheets di `docs/zharok_v2_*.png`

v3 **membungkus** v2, tidak menggantinya: kalau `heroes/zharok_fx.py`
tidak tersedia, renderer jatuh balik ke seluruh FX canvas v2.
