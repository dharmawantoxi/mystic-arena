# Peta cakupan `_entity.py` → Godot

**Apa ini:** audit kelas/blok `_entity.py` (sumber kebenaran pygame) terhadap
port Godot di `godot/`. Dipakai untuk menjawab "sisa celah mana yang sudah
diisi, mana yang sengaja terbuka" tanpa menebak dari nama berkas.

**Cara baca:** setiap baris = blok pygame dengan rentang baris, padanannya di
Godot, dan statusnya.

| Status | Arti |
|---|---|
| ✅ PORTED | Perilaku diport dan **dikunci tes** (atau overlay visual 1:1 tanpa oracle piksel) |
| 🟡 PARSIAL | Ada padanannya, sebagian belum ada / belum diuji |
| ❌ BELUM | Tidak ada padanan di Godot |
| ⚪ N/A | No-op / renderer cache pygame / tidak relevan di Godot |

Acuan lebih luas: [GODOT_PARITY.md](GODOT_PARITY.md). Roadmap:
[GODOT_MIGRATION.md](GODOT_MIGRATION.md). **Jangan edit runtime pygame.**

---

## 1. Utilitas & peluru — `_entity.py:26-430`

| Blok | Padanan Godot | Status |
|---|---|---|
| `credit_hero_damage` (`:26-45`) — `source.damage_dealt += int(amount)` setelah HP, skip amount≤0 / source None | `CombatSystem._credit_hero_damage` dipanggil dari `apply_damage` langkah 4b; `Hero.kit_hit` **tidak** menambah lagi | ✅ `EntityPyParityTest` |
| `Bullet` homing + `_on_hit` (cannon splash 60%, ice slow, mage debuff; **tanpa source**) | `scenes/tower/TowerBullet.gd` | ✅ `DeathDispatchParityTest` |
| `Bullet._draw_hd_arrow` (`:345-430`) shaft/feather/head per tim | `TowerBullet._draw_hd_arrow` | ✅ visual (tanpa oracle piksel) |

---

## 2. Tower — `_entity.py:600-1330`

| Blok | Padanan Godot | Status |
|---|---|---|
| Stat 4 jalur × 6 level, shield 40%, regen HP, Regen Shield berbayar | `Tower.gd` + `TowerDB` / `towers.json` | ✅ |
| `_shoot_archer` (`:904-937`): L5=2 offset `(-8,0)/(8,0)`; L6=3 `(-11,3)/(0,-2)/(11,3)`; SCALE 0.7 lalu `int()`; pad target sama; `double_shot` **hanya L&lt;5** | `Tower._shoot_archer_volley` + `_spawn_bullet(..., spawn_offset)` | ✅ `EntityPyParityTest` |
| `_draw_shield_crest` (`:1295-1317`) size 14 @ `(+26, −28−level)` | `ArmorCrest.draw` di `Tower._draw_overlays` | ✅ visual |
| `shield_regen_flash` 3 frame tiap tick regen / 6 saat beli | `Tower.shield_regen_flash` (detik = frame/60) | ✅ |

---

## 3. Castle / Nexus — `_entity.py:1480-1920`, `:3063-3184`

| Blok | Padanan Godot | Status |
|---|---|---|
| Stat per level, Castle Shield gratis s/d wave 10, DR 88% int | `Nexus.gd` + `nexus.json` | ✅ `HeroBasicAttackParityTest` |
| `_draw_castle_shield` crest size 18 + bob | `ArmorCrest` di `Nexus._draw_overlays` | ✅ visual |
| Label `SHIELD n%` di atas bar | `draw_string` ThemeDB | ✅ visual |
| Torch gerbang L4+ + aura L6 (`_render_dynamic_effects`) | `_draw_gate_torch` / `_draw_magic_aura` (elips pygame → busur; no `draw_ellipse`) | ✅ visual |
| `shield_regen_flash = 4` tiap tick regen | `Nexus.shield_regen_flash` | ✅ |

---

## 4. Hero — `_entity.py:3300-5350`

| Blok | Padanan Godot | Status |
|---|---|---|
| Stat/catch-up, kit QWER, retreat, auto-cast, item | `Hero.gd` + `HeroSkillKit` + `ItemInventory` | ✅ harness skill/basic/rng/item |
| `damage_dealt` lewat `credit_hero_damage` (bukan `kit_hit` kedua kali) | `CombatSystem._credit_hero_damage`; `kit_hit` hanya `apply_damage` | ✅ `EntityPyParityTest` |
| `_do_attack` **tanpa** `combat_feel.hit_stop` / trauma 0.15 | `Hero.try_attack` tidak memanggil `request_hit_stop` / `add_trauma` | ✅ `EntityPyParityTest` |
| `_build_name_badge` (`:4931-4970`): nama saja; L≤5 bintang, L>5 `xN` | `name_label = display_name`; `_draw_level_stars` @ y−72 | ✅ `EntityPyParityTest` (teks) |
| `_draw_projectile` sylara/vex/zephyr/morgath/aa/generic | `SkillProjectile.gd` kind arrow/orb/bolt/lightning/ice/generic | ✅ kind dikunci tes; piksel terbuka |
| `_spawn_skill_projectile` visual-only | `Hero.kit_skill_proj` / `spawn_skill_projectile` | ✅ (damage instan — PARITY) |

---

## 5. Minion — `_entity.py:5400-5965`

| Blok | Padanan Godot | Status |
|---|---|---|
| Stat economy, lane, AI 1–5, ranged undead | `Minion.gd` | ✅ |
| `_spawn_slash_effect` 12f, 7 titik, span 1.1 | `Minion._spawn_slash` + `_draw` polyline | ✅ visual |
| `_draw_death_animation` dust 4 arah | `_death_progress` 20f + `_draw` circle | ✅ visual |
| Pukulan netral tanpa source | `try_attack` `source=null` | ✅ `DeathDispatchParityTest` |

---

## 6. AIPlayer — `_entity.py:6000+`

| Blok | Padanan Godot | Status |
|---|---|---|
| Brain/elite, build/draft/upgrade/item/shield | `AIPlayer.gd` | ✅ `AIPlayerTest` |
| Statistik `total_*` (damage/gold tracking pygame) | — | ⚪ sengaja dilewati (bukan gameplay) |

---

## Tes

`godot --headless --path godot res://tests/EntityPyParityTest.tscn --quit-after 60`

Require `[EntityPyParityTest] PASS`. Binary Godot sering tidak ada di sandbox;
langkah CI `4e2` di `.github/workflows/godot-check.yml` yang menjalankan replay.
