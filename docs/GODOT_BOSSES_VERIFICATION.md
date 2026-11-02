# Verifikasi migrasi `bosses/`

Tanggal: 2026-11-02. Branch: `arena/291f0c31-mystic-arena`.

## Hasil lokal

| Gerbang | Hasil |
|---|---|
| `python tools/prepare_godot_bosses.py` | 61 file, 162 mini + 54 true, 79 smart-AI, 10 controller case, 10 combat case. |
| `python tools/prepare_godot_bosses.py --check` | Lulus; kontrak/oracle byte-exact. |
| `python -m unittest tools.test_godot_bosses_prepare tools.test_godot_bosses_parity` | 11 tes lulus. |
| `python godot_rebuild/tests/validate_project.py` | **PASS: 538** pemeriksaan native/project/source. |
| Native suite Godot headless | **PASS: 4353 checks, 0 failures**. |
| Boot smoke `--quit-after 240` | rc 0, tanpa script error. |
| `gdparse` | Seluruh GDScript native lulus. |
| `gdlint` | Lulus untuk modul non-generated. |

Engine lokal: `godot_rebuild/godot-test` versi `4.7.2.stable.custom_build`
(headless Linux, tidak di-commit). CI memakai Godot 4.7.2-stable resmi.

## Cakupan oracle

- Normalisasi pristine→final: 216 baris boss, termasuk hero-unlock hp/damage/
  skill_damage/range dan urutan tie sumber.
- Runtime init/enrage: 216 boss, membandingkan HP, damage, speed, range,
  cooldown, radius, armor/MR, reduction, cap, tenacity, entrance, cleave,
  ability, ability2, dan status smart-AI.
- Smart-AI: 79 boss × 3 skenario (`cluster`, `duo_low`, `solo_edge`) = 237 trace.
  Event cast/damage/slow/knockback/lock/facing/enrage dan state kit akhir
  dibandingkan dengan harness pygame asli.
- Controller: 10 skenario basic, kite, entrance, stun, lane, heal. Snapshot
  per-frame dan event dibandingkan; posisi memakai toleransi 0.02px untuk
  drift float32.
- Combat: 10 kasus physical, magic, fire, amp+shred, defense boost, cap,
  blind miss/hit, true-strike, dan lethal.

## Gerbang fail-closed

`tools/test_godot_bosses_prepare.py` membuktikan:

1. `--check` lulus pada kontrak saat ini.
2. Menambah komentar ke `bosses/base_boss.py` membuat `--check` gagal
   (`Stale bosses`), lalu file dipulihkan.
3. Perubahan hash sumber renderer dengan PNG yang sama ditolak dan meminta
   `tools/prepare_godot_bosses.py --bake`.

Validator juga memverifikasi hash setiap file `bosses/*.py` terhadap kontrak,
cakupan 216 boss/61 file/79 smart-AI, keberadaan modul native, integrasi
`CoreData`/`BattleUnit`/`EntityMovement`/`MatchModel`/`ArenaView`, dan wiring CI.

## CI

Kedua workflow Godot menjalankan:

```text
python tools/prepare_godot_bosses.py --check
python tools/test_godot_bosses_prepare.py
python tools/test_godot_bosses_parity.py
```

Status CI PR akan diperbarui setelah push. Belum ada klaim lulus CI sebelum
check GitHub benar-benar selesai.

## Tidak diverifikasi

- Pixel-exact renderer prosedural pygame per-frame di Godot.
- Output GPU/audio nyata, Android/device, signing, Play Games, atau top-up.
- Merge PR; menunggu permintaan eksplisit.
