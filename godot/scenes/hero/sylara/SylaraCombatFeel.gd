# SylaraCombatFeel.gd — lapisan combat feel Sylara (Godot native).
#
# Satu tanggung jawab: menyinkronkan AUDIO + CAMERA SHAKE + HIT-STOP +
# VFX impact pada MOMEN yang benar. Node ini TIDAK PERNAH menyentuh
# gameplay (damage/cooldown/state kit milik HeroSkillKit).
#
# Pola Godot:
#   * EVENT-DRIVEN lewat sinyal root (bow_released, skill_released,
#     character_died) — tanpa _process polling, tanpa antrean manual.
#   * Event tertunda (impact Powershot = beberapa fraksi detik setelah
#     tebar) dijadwalkan dengan Tween node (aman dari freed-instance).
#
# Bobot feel (seimbang, tidak menyengal):
#   * BASIC ATTACK → kilatan nock KECIL saat tali snap (1 aktor, 0.08 dtk).
#     Tanpa hit-stop/shake — serangan dasar harus ringan & cepat.
#   * POWERSHOT (ultimate) → bunyi lepas di momen tebar, lalu paket impact
#     penuh (flash + ring + sparks terarah + hit-stop 0.04 + shake 0.12)
#     dijadwalkan pada MOMEN MENDARAT kerucut, bukan saat cast.
#   * KEMATIAN → paket perpisahan angin (3 aktor). Di arena, hero langsung
#     tersembunyi oleh alur respawn — VFX tetap terlihat karena aktor
#     VFXManager hidup di layer dunia.
class_name SylaraCombatFeel
extends Node

const Pal = preload("res://scenes/hero/sylara/SylaraPalette.gd")

## Perkiraan waktu tempuh kerucut Powershot (dtk) — impact dijadwalkan
## searah jarak bidik agar mendarat tepat di ujung kerucut.
const R_IMPACT_TRAVEL := 0.35

var _skel: SylaraSkeleton = null
var _hero = null


func _ready() -> void:
	var p := get_parent()
	if p is SylaraSkeleton:
		_skel = p as SylaraSkeleton
		_skel.bow_released.connect(_on_bow_released)
		_skel.skill_released.connect(_on_skill_released)
		_skel.character_died.connect(_on_character_died)
	# Hero = 2 kakek node (Hero/Visual/<rig>) — dipakai untuk hook kematian
	# arena (GameManager.hero_died) tanpa modifikasi hero.
	var n: Node = p
	if n != null:
		n = n.get_parent()
		if n != null:
			n = n.get_parent()
	if n != null and "hp" in n and "kit" in n:
		_hero = n
		_hook_arena_death()


## Kematian di arena: hero di-hide alur respawn; biarkan VFX perpisahan
## (layer dunia) tetap menyala di posisi hero.
func _hook_arena_death() -> void:
	# GameManager = autoload (selalu ada di project).
	if GameManager.has_signal("hero_died"):
		GameManager.hero_died.connect(_on_arena_hero_died)


func _on_arena_hero_died(h: Node) -> void:
	if _hero != null and h == _hero:
		_on_character_died()


# ══════════════════════════════════════════════════════════
#  BASIC ATTACK — kilatan tali snap
# ══════════════════════════════════════════════════════════

func _on_bow_released() -> void:
	if _skel == null or not is_instance_valid(_skel):
		return
	# Kilatan nock kecil tepat saat tali dilepas (1 aktor, 0.08 dtk).
	VFXManager.flash(_skel.get_bow_nock_global(), 5.0,
		Pal.WIND_BRIGHT, 0.0, 0.08)


# ══════════════════════════════════════════════════════════
#  POWERSHOT — audio tebar + impact terjadwal
# ══════════════════════════════════════════════════════════

func _on_skill_released(key: String, aim_point: Vector2) -> void:
	if key != "r" or _skel == null:
		return
	# Bunyi busur dilepas pada momen tebar (bukan saat charge mulai).
	AudioManager.play_combat("hero_ranged", 1.0)
	# Impact dijadwalkan pada MOMEN MENDARAT kerucut — lewat Tween milik
	# node ini: kalau rig dibebaskan sebelum timer habis, tween ikut
	# mati (aman, tidak ada callback ke instance bebas).
	if is_inside_tree():
		var tw := create_tween()
		tw.tween_interval(R_IMPACT_TRAVEL)
		tw.tween_callback(_fire_r_impact, aim_point)
	else:
		_fire_r_impact(aim_point)


func _fire_r_impact(pos: Vector2) -> void:
	# Paket impact ultimate (komposisi setara VFXManager.impact tier 3,
	# tetapi posisinya disinkronkan ke ujung kerucut bidik).
	VFXManager.flash(pos, 17.0, Pal.WIND_WHITE, 0.0, 0.16)
	VFXManager.ring(pos, 42.0, Pal.WIND, 0.02, 0.4, 2.8)
	VFXManager.sparks(pos, randf() * TAU, 6, 240.0, Pal.WIND_BRIGHT,
		0.0, 0.34, TAU * 0.4)
	# Hit-stop + shake proporsional ULTIMATE — singkat agar tidak macet.
	GameManager.request_hit_stop(0.04, 0.04)
	var tree := get_tree()
	if tree != null:
		tree.call_group("camera", "add_trauma", 0.12)
	AudioManager.play_sfx("explosion", 0.22)


# ══════════════════════════════════════════════════════════
#  DEATH — paket perpisahan angin (3 aktor)
# ══════════════════════════════════════════════════════════

func _on_character_died() -> void:
	if _skel == null or not is_instance_valid(_skel):
		return
	var c: Vector2 = _skel.global_position + Vector2(0.0, -14.0)
	VFXManager.flash(c, 9.0, Pal.WIND_LIGHT, 0.0, 0.16)
	VFXManager.ring(c, 26.0, Pal.WIND, 0.03, 0.38, 2.4)
	VFXManager.sparks(c, PI * 0.5, 5, 95.0, Pal.LEAF, 0.02, 0.4, 1.0)
