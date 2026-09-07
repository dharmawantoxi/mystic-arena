# RendererRegistry.gd — daftar renderer CUSTOM per unit.
#
# Lookup 3 tingkat sejak Fase 5 (bake batch 222 unit):
#   1. scene custom di dict HERO/BOSS di bawah (rig hand-made),
#   2. strip bake pygame (BakedSprite.tscn + baked_units.json),
#   3. UnitSilhouette (pygame.draw.circle/polygon, fallback).
# Minion belum punya jalur bake (tetap silhouette).
#
# Scene custom boleh punya method drive(phase, action, attack_progress,
# facing, is_moving, skill, delta) — kalau ada, Hero.gd memanggilnya
# tiap frame (paritas KaizenSkeleton.gd).
extends Object

const BakedUnitDB = preload("res://scripts/render/BakedUnitDB.gd")
## Scene generik untuk 222 unit hasil bake renderer pygame (Fase 5
## Opsi A). Identitas unit diambil dari manifest saat
## configure_baked() dipanggil Hero.gd/Boss.gd — registry cukup
## mengembalikan scene yang sama untuk semua unit ter-bake.
const BakedSpriteScene = preload("res://scenes/render/BakedSprite.tscn")

## hero_type -> PackedScene. Key yang tidak terdaftar tetap memakai
## silhouette pygame — jadi Kaizen bisa "naik kelas" sendiri tanpa
## mengganggu 221 hero lain.
##
## Kaizen terdaftar: rig Skeleton2D 19 tulang (port _NS_kaizen 2906 baris)
## sudah punya drive() dengan signature persis yang dipanggil Hero.gd,
## sehingga di arena ia tampil sebagai karakter bertulang + shader hamon
## + wind ribbon, bukan lingkaran generik.
##
## URUTAN lookup hero_scene(): scene custom di atas > strip bake >
## silhouette. Rig hand-made selalu menang karena itu upgrade yang lebih
## tinggi dari bake; bake menang dari silhouette karena pose-nya berasal
## dari renderer pygame asli (tools/convert_to_godot.py --units-png).
const HERO := {
	"kaizen": preload("res://scenes/hero/kaizen/KaizenSkeleton.tscn"),
}
## boss_type -> PackedScene.
const BOSS := {}
## minion_type -> PackedScene.
const MINION := {}


static func hero_scene(hero_type: String) -> PackedScene:
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
