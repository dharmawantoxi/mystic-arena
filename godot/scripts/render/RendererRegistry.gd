# RendererRegistry.gd — daftar renderer CUSTOM per unit.
#
# Sejak 2026-09-15 rig Kaizen v4 (rebuild Godot native: renderer
# prosedural berlapis + animator pose + KaizenSkillFX + VFXManager pooled)
# adalah DEFAULT arena (mystic/rendering/experimental_hero_rigs=true di
# project.godot). Sylara v1 (rebuild Godot 4.x: renderer prosedural
# berlapis + animator pose + SylaraSkillFX + VFXManager pooled) ditambahkan
# sebagai hero rig kedua. Set flag false untuk fallback ke strip bake
# renderer pygame. Kontrak dua jalur ini dikunci GameplayParityTest.
# KaizenDemo.tscn selalu memakai rig langsung.
# Minion belum punya jalur bake (tetap silhouette).
#
# Scene custom boleh punya method drive(phase, action, attack_progress,
# facing, is_moving, skill, delta) — kalau ada, Hero.gd memanggilnya
# tiap frame (paritas KaizenSkeleton.gd). Rig yang menangani FX skill
# sendiri menyediakan handles_skill_fx(key) -> bool.
extends Object

const BakedUnitDB = preload("res://scripts/render/BakedUnitDB.gd")
## Scene generik untuk 222 unit hasil bake renderer pygame (Fase 5
## Opsi A). Identitas unit diambil dari manifest saat
## configure_baked() dipanggil Hero.gd/Boss.gd — registry cukup
## mengembalikan scene yang sama untuk semua unit ter-bake.
const BakedSpriteScene = preload("res://scenes/render/BakedSprite.tscn")

## Renderer alternatif. KaizenDemo.tscn tetap memakai rig langsung;
## arena memakainya selama experimental_hero_rigs tidak dimatikan (default ON).
const HERO := {
	"kaizen": preload("res://scenes/hero/kaizen/KaizenSkeleton.tscn"),
	"sylara": preload("res://scenes/hero/sylara/SylaraSkeleton.tscn"),
}
## boss_type -> PackedScene.
const BOSS := {}
## minion_type -> PackedScene.
const MINION := {}


static func hero_scene(hero_type: String) -> PackedScene:
	if BakedUnitDB.has_unit(hero_type) and not bool(ProjectSettings.get_setting(
			"mystic/rendering/experimental_hero_rigs", false)):
		return BakedSpriteScene
	var custom: PackedScene = HERO.get(hero_type) as PackedScene
	if custom != null:
		return custom
	if BakedUnitDB.has_unit(hero_type):
		return BakedSpriteScene
	return null


static func boss_scene(boss_type: String) -> PackedScene:
	var custom: PackedScene = BOSS.get(boss_type) as PackedScene
	if custom != null:
		return custom
	if BakedUnitDB.has_unit(boss_type):
		return BakedSpriteScene
	return null


static func minion_scene(minion_type: String) -> PackedScene:
	return MINION.get(minion_type) as PackedScene
