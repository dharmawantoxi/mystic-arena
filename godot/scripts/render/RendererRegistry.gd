# RendererRegistry.gd — daftar renderer CUSTOM per unit.
#
# Baseline arena: SEMUA hero/boss/minion pakai UnitSilhouette
# (pygame.draw.circle / polygon, 0 sprite, 0 tulang, 0 shader).
# Upgrade satu-satu dengan mengisi dict di bawah — Hero.gd / Boss.gd
# / Minion.gd otomatis instantiate scene custom kalau key-nya ada.
#
# Scene custom boleh punya method drive(phase, action, attack_progress,
# facing, is_moving, skill, delta) — kalau ada, Hero.gd memanggilnya
# tiap frame (paritas KaizenSkeleton.gd).
extends Object

## hero_type -> PackedScene. Key yang tidak terdaftar tetap memakai
## silhouette pygame — jadi Kaizen bisa "naik kelas" sendiri tanpa
## mengganggu 221 hero lain.
##
## Kaizen terdaftar: rig Skeleton2D 19 tulang (port _NS_kaizen 2906 baris)
## sudah punya drive() dengan signature persis yang dipanggil Hero.gd,
## sehingga di arena ia tampil sebagai karakter bertulang + shader hamon
## + wind ribbon, bukan lingkaran generik.
const HERO := {
	"kaizen": preload("res://scenes/hero/kaizen/KaizenSkeleton.tscn"),
}
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
