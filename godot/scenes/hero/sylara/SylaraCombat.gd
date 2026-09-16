# SylaraCombat.gd — kebijakan combat FEEL Sylara (v2 rebuild).
#
# Aturan MASTER PROMPT yang dikunci di sini (single source of feel):
#   * SERANGAN DASAR — TIDAK ADA hit-stop, TIDAK ADA impact FX, TIDAK ADA
#     hurt flash. Damage + feedback milik TowerBullet._on_hit (paritas
#     pygame; lihat tools/test_basic_attack_no_impact_fx.py). Node ini
#     sengaja tidak menyentuh serangan dasar.
#   * SKILL — feedback proporsional:
#       Q/W/E: shake cast sudah ditangani kit (kit_shake 8/5/6/15);
#             tidak ada freeze tambahan agar ritme volley/sprint tetap.
#       R (Powershot, ultimit): camera trauma KUAT. Hit-stop handled by
#             VFXManager.impact tier 3 di SkillFX (satu freeze, satu sumber).
class_name SylaraCombat
extends Node2D

var _skeleton: SylaraSkeleton = null


func setup(skeleton: SylaraSkeleton) -> void:
	_skeleton = skeleton
	if _skeleton != null and _skeleton.has_signal("skill_release"):
		_skeleton.skill_release.connect(_on_skill_release)


func _on_skill_release(key: String) -> void:
	match key:
		"r":
			# Ultimit: kamera kuat (trauma 1.0 = ~60px; 0.45 = ~27px).
			_shake_camera(0.45)
		_:
			pass  # Q/W/E — shake cast kit sudah cukup (kontrak feel)


func _shake_camera(trauma: float) -> void:
	var tree := get_tree()
	if tree != null:
		tree.call_group("camera", "add_trauma", trauma)
