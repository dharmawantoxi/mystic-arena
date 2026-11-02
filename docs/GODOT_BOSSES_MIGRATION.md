# Migrasi `bosses/` ke Godot

Status: selesai untuk runtime, data, AI, presentasi, dan gerbang paritas. PR ini
tidak menggabungkan sendiri; merge hanya dilakukan atas permintaan eksplisit.

## Cakupan sumber

Folder `bosses/` diperlakukan sebagai closed world:

- 61 file Python, termasuk `__init__.py` satu baris.
- `boss_data.py`: 162 mini boss + 54 true boss, jadwal wave, kurva, dan
  normalisasi hero-unlock.
- `base_boss.py`: inisialisasi, scaling, target, basic attack/cleave, kiting,
  enrage/heal, damage/death, debuff, aura/entrance/nameplate, dan 79 smart-AI.
- `_boss_index.py`: indeks renderer generated 216 entri. Tidak diedit tangan.
- 54 renderer `levelN.py` dan 3 helper rig v4 (`razak_v4`, `nyzrak_v4`,
  `thalgryn_v4`). Pixel prosedural pygame sudah dibake menjadi strip PNG pada
  migrasi entity sebelumnya; migrasi ini memakai ulang 216 strip boss tersebut
  dan mengunci hash sumber + PNG agar renderer yang berubah tidak lolos tanpa
  bake ulang.

## Artefak native

| Artefak | Isi |
|---|---|
| `godot_rebuild/data/bosses.json` | Kontrak: hash 61 sumber, indeks renderer/art, pristine stats, urutan tie source, kurva, smart-AI/kiting set, label top. |
| `godot_rebuild/scripts/core/BossCatalog.gd` | Loader fail-closed + pipeline rebalance → smooth → curve → hero-unlock stats/range. |
| `godot_rebuild/scripts/entities/BossController.gd` | Tick `Boss.update`: timer, stun/burn, entrance, enrage/heal, target range+100, basic/cleave, smart-AI vs generic ability, kiting, lane budget. |
| `godot_rebuild/scripts/entities/BossCombat.gd` | Urutan damage sumber: blind → amp/shred → armor/MR → resilience → cap → floor 1. |
| `godot_rebuild/scripts/entities/BossVisuals.gd` | Aura ability/enrage/true, entrance, bayangan, nameplate/HP bar ber-anchor `BOSS_LABEL_TOP`. |
| `godot_rebuild/tests/BossParityTest.gd` | Replay oracle pygame: normalisasi, 216 init/enrage, 237 trace smart-AI, 10 controller, 10 combat. |
| `godot_rebuild/tests/fixtures/bosses_parity.json` | Oracle dari `Boss` pygame asli, bukan reimplementasi rumus. |
| `tools/prepare_godot_bosses.py` | Prepare/check fail-closed; `--bake` memanggil bake sprite entity sebelum menulis kontrak. |

Integrasi runtime:

- `CoreData` memuat `BossCatalog` dan menolak kontrak yang tidak cocok dengan
  `core_data.json`.
- `BattleUnit.setup_boss` memakai timer ability awal 0, entrance 180/120,
  tenacity 0.50, reduction 0.30/0.20, cap 8%/12%, cleave 80px/40%, dan facing
  awal -1.
- `BattleUnit.take_damage` merutekan boss ke `BossCombat`; tidak ada lagi
  armor ganda setelah mitigasi boss.
- `EntityMovement` mendelegasikan boss ke `BossController`; `MatchModel` tidak
  melakukan tick timer boss dua kali.
- `ArenaView` menggambar aura/nameplate boss; `CoreGame`/`AudioDirector`
  memutar suara basic attack melee/ranged bila aset tersedia.

## Perintah

```bash
python tools/prepare_godot_bosses.py          # tulis kontrak + oracle
python tools/prepare_godot_bosses.py --check  # gagal bila sumber/art/oracle stale
python tools/prepare_godot_bosses.py --bake   # bake ulang sprite lalu tulis kontrak
python -m unittest tools.test_godot_bosses_prepare tools.test_godot_bosses_parity
python godot_rebuild/tests/validate_project.py
```

Gerbang `--check` memverifikasi hash semua file `bosses/*.py`, semua entri
indeks renderer, semua strip PNG boss, dan fixture oracle. Bila sumber renderer
berubah tetapi PNG belum dibake ulang, prepare menolak dengan pesan menjalankan
`--bake`.

## Keputusan parity

- Angka, warna, kurva, dan nama tidak di-retune diam-diam. Stats final tetap
  berasal dari `boss_data.py` yang sudah dinormalisasi; `BossCatalog` memvalidasi
  pipeline native terhadap hasil tersebut.
- Smart-AI 79 boss tetap memakai `BossKit.gd` generated dari
  `tools/gen_boss_smart_ai.py`. Boss non-smart memakai generic ability hanya
  sebagai fallback, bukan tambahan di atas smart-AI.
- Target boss dicari dalam `range + 100` dari pusat target, tanpa radius allowance.
- Kiting 12 boss ranged memakai min/prefer distance dan hysteresis 12px.
- Enrage true: HP ≤50%, speed ×1.25, damage ×1.25, cooldown ×0.75 min 18.
  Mini: HP ≤40%, speed ×1.15, damage ×1.20, cooldown ×0.80 min 20.
- Damage boss truncates ke int setelah resilience, lalu cap per-hit, lalu
  minimum 1. Blind hanya untuk `damage_type == "normal"` dan dapat dibatalkan
  true-strike.

## Batasan jujur

- Tubuh boss adalah strip PNG hasil bake pygame, bukan eksekusi renderer
  prosedural pygame per-frame di Godot. Kontrak mengunci hash sumber renderer dan
  PNG, tetapi tidak mengklaim pixel-exact untuk setiap frame animasi prosedural.
- Trace controller memberi toleransi posisi 0.02px karena `Vector2` Godot
  float32 sedangkan oracle pygame float64; timer, HP, damage, dan event tetap
  dibandingkan ketat.
- Aura/nameplate native mengikuti geometri/formula sumber, bukan screenshot
  pixel-diff pygame.
- Audio basic attack bersifat opsional mengikuti aset yang dibake; tidak ada
  verifikasi perangkat Android, GPU, atau audio output nyata di CI headless.
