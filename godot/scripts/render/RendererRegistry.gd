# RendererRegistry.gd — daftar renderer CUSTOM per unit.
#
# Baseline arena: SEMUA hero/boss/minion pakai UnitSilhouette
# (pygame.draw.circle / polygon, 0 sprite, 0 tulang, 0 shader).
# Upgrade satu-satu dengan mengisi dict di bawah — Hero.gd / Boss.gd
# / Minion.gd otomatis instantiate scene custom kalau key-nya ada.
#
# Contoh nanti, setelah renderer Kaizen siap dipakai di arena:
#   const HERO := {
#       "kaizen": preload("res://scenes/hero/kaizen/KaizenSkeleton.tscn"),
#   }
# Scene custom boleh punya method drive(phase, action, attack_progress,
# facing, is_moving, skill, delta) — kalau ada, Hero.gd memanggilnya
# tiap frame (paritas KaizenSkeleton.gd).
extends Object

## hero_type -> PackedScene. Kosong = semua pakai silhouette pygame.
const HERO := {}
## boss_type -> PackedScene.
const BOSS := {}
## minion_type -> PackedScene.
const MINION := {}


static func hero_scene(hero_type: String) -> PackedScene:
	return HERO.get(hero_type) as PackedScene


static func boss_scene(boss_type: String) -> PackedScene:
	return BOSS.get(boss_type) as PackedScene


static func minion_scene(minion_type: String) -> PackedScene:
	return MINION.get(minion_type) as PackedScene
