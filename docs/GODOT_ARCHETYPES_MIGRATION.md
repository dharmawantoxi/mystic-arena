# Migrasi `hero_archetypes.py` → Godot (`godot_rebuild/`)

Status: **native GDScript, tanpa Python saat runtime**. Melanjutkan migrasi
`main.py` (#377), `_core.py` (#378), `_entity.py` (#379), `_render.py` (#380),
dan `_system.py` (#381). Sumber kebenaran tetap `hero_archetypes.py`; port ini
**tidak** menjalankan ulang analyzer, tidak mengubah skor, dan tidak melakukan
rebalance diam-diam.

## Cakupan

| Sumber Python | Native Godot | Catatan |
|---|---|---|
| `ARCHETYPES`, `DEFAULT_DMG_TYPE` | `scripts/core/HeroArchetypes.gd` + `data/hero_archetypes.json` | 222 hero playable: 120 MAGIC / 102 PHYSICAL; 137 FIGHTER / 64 TANK / 21 CARRY. |
| `get_archetype`, `school_of` | `HeroArchetypes.get_archetype()`, `school_of()` | Override manual `stats.dmg_type` menang; nilai tak dikenal jatuh ke PHYSICAL; hero tak terdaftar mendapat fallback `derived=true`. Lookup mengembalikan salinan defensif agar UI tidak memutasi tabel sumber. |
| `BOSS_RESISTANCES` | `HeroArchetypes.get_boss_resistances()` | 216 boss: 162 mini + 54 true. Entri tabel menang atas kelas yang diminta; boss tak terdaftar memakai fallback profil balanced. |
| `BOSS_RESIST_BASE`, `BOSS_RESIST_PROFILE_MODS`, `BOSS_RESIST_SCALE`, `BOSS_RESIST_TARGET_RATIO`, `_resist_from_profile` | `HeroArchetypes.resist_from_profile()` | Baseline, modifier, skala, clamp armor 0–40 dan MR 0–0.45. Pembulatan armor memakai half-to-even agar sama dengan `round()` Python, bukan `roundf()` Godot. |
| `ARMOR_FACTOR`, `physical_mitigation` | `HeroArchetypes.physical_mitigation()` | Mengembalikan fraksi damage yang **lolos**: `1 - armor*0.06/(1+armor*0.06)`, armor negatif dianggap 0. |
| Clamp `Boss.__init__` | `HeroArchetypes.boss_resistances_for()` + `BattleUnit.setup_boss()` | Override manual `armor`/`magic_resist`/`resist_profile` dipertahankan, lalu di-clamp. Sebelumnya native membaca field yang tidak ada di katalog sehingga boss default ke armor/MR 0. |
| Label sekolah/UI `_core.py` | `MenuView.show_heroes()`, `ArenaView` | Toko menampilkan PHY/MAG, penanda TNK, tier/power snapshot, dan tooltip mitigasi. Arena menampilkan sekolah hero terpilih serta panel armor/MR/profil boss aktif. |

## Integrasi runtime

```
CoreData
  └── archetypes: HeroArchetypes
        ├── get_archetype(hero_type, stats) ──► BattleUnit.setup_hero()
        │       ├── dmg_type / playstyle / archetype
        │       └── dmg_school lowercase ──► projectile, skill, mitigasi
        └── boss_resistances_for(type, class, stats) ──► BattleUnit.setup_boss()
                ├── armor / magic_resist / resist_profile
                └── EntityCombat.boss_pre_damage()

MenuView / ArenaView ──► short_label(), detail_label(), school_color()
```

- Sekolah damage hero kini berasal dari tabel analisis, bukan tebakan role.
  Contoh: `vex`/`gornak` menjadi MAGIC; `kaizen` tetap PHYSICAL.
- Atribut item `magic_only` tetap terpisah: `BattleUnit.is_magic_hero()` masih
  mengikuti atribut Magic berbasis role dari `hero_items.py`. Override sekolah
  damage tidak boleh otomatis menulis ulang atribut item tersebut.
- Jalur armor boss mengikuti `base_boss.py`: hitung reduksi armor mentah,
  kurangi shred Corroder (`amount * 0.06`), baru clamp reduksi 0–0.60. Ini
  berbeda dari jalur armor hero yang mengekang reduksi lewat helper terpisah.
- Magic resistance boss memakai cap sumber 0.45, bukan cap hero 0.60.
- `CoreData.valid()` kini juga menolak kontrak arketipe yang hilang/rusak, agar
  pertandingan tidak diam-diam berjalan dengan sekolah dan resistansi salah.

## Kontrak data & tooling

```bash
# Setelah mengubah hero_archetypes.py atau katalog hero/boss:
python3 tools/prepare_godot_core.py
python3 tools/prepare_godot_archetypes.py
python3 tools/prepare_godot_archetypes.py --check
python3 tools/test_godot_archetypes_prepare.py
```

`prepare_godot_archetypes.py` hanya mengimpor modul data murni (tanpa pygame),
memvalidasi cakupan katalog secara fail-closed, lalu menulis:

- `godot_rebuild/data/hero_archetypes.json` — tabel runtime + konstanta + hash
  sumber. SHA-256 kontrak saat migrasi: `19d0e08bb74c`.
- `godot_rebuild/tests/fixtures/hero_archetypes_parity.json` — oracle Python
  independen untuk seluruh hero/boss, override manual, fallback, profil, clamp,
  pembulatan half-to-even, dan kurva mitigasi.

`--check` membandingkan byte kedua file dan tidak menulis apa pun. Kekurangan
hero/boss, entri basi, profil/kelas salah, armor/MR di luar clamp, atau hash sumber
yang bergeser membuat gate gagal.

## Integrasi CI

- Path filter `godot-check.yml` dan `godot-rebuild.yml` mencakup
  `hero_archetypes.py` serta tool prepare/test arketipe.
- Kedua workflow menjalankan `prepare_godot_archetypes.py --check` dan
  `test_godot_archetypes_prepare.py` setelah kontrak core siap.
- `validate_project.py` menambah pemeriksaan modul, hash, cakupan 222/216,
  konstanta sumber, wiring hero/boss/combat/UI, dan kehadiran gate CI.
- `run_all.gd` menambah `_test_archetypes()` yang membandingkan runtime GDScript
  dengan fixture oracle Python dan menguji wiring `BattleUnit`/`EntityCombat`.

## Batasan yang jujur

- Tier/power adalah snapshot analisis sumber, bukan DPS runtime setelah item,
  level, buff, atau perubahan katalog. Port tidak menghitung ulang skor tersebut.
- Generator lama `tools/analyze_hero_archetypes.py --emit-gdscript` dan
  `tools/convert_to_godot.py` masih menunjuk proyek legacy `godot/` yang sudah
tidak aktif. Jalur resmi migrasi ini adalah `godot_rebuild/` + prepare tool di
atas; komentar header sumber sudah diperbarui agar tidak menyesatkan.
- Paritas penuh seluruh pipeline damage boss (rounding tiap tahap, blind/true
  strike, resilience, dan cap per-hit) tetap milik migrasi `_entity.py`/boss.
  Perubahan di sini membatasi diri pada sekolah hero, nilai armor/MR, urutan
  shred armor boss, dan cap MR yang consumed oleh pipeline tersebut.
- Verifikasi headless tidak membuktikan piksel GPU, perangkat Android, audio,
  Play Games, top-up produksi, atau signing keystore. Lihat
  `GODOT_ARCHETYPES_VERIFICATION.md` untuk hasil uji aktual.
