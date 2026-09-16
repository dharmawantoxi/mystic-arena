# SylaraCombatFeel.gd — lapisan combat feel Sylara (Godot 4.x).
#
# SATU tanggung jawab: menyinkronkan ANIMATION + VFX + AUDIO + HIT-STOP +
# CAMERA pada momen yang benar. Node ini TIDAK PERNAH menyentuh gameplay:
# tidak ada damage, cooldown, atau state kit di sini (itu milik
# HeroSkillKit + CombatSystem yang parity-locked).
#
# Batasan kontrak (test_basic_attack_no_impact_fx):
#   * BASIC ATTACK → NOL impact FX, NOL hit-stop, NOL shake. Hanya kilatan
#     nock KECIL di busur (1 aktor, 0.1 dtk) + sabit tebasan tunggal untuk
#     melee riposte. Suara tembakan tetap milik Hero.try_attack (tidak
#     boleh dobel).
#   * SKILL → impact penuh hanya untuk R (ultimate) dan diledakkan pada
#     MOMEN DAMAGE (±1.0 dtk setelah cast, saat powershot_timer habis),
#     bukan saat cast. Q/W/E memakai shake+suara dari kit (sudah ada).
#
# Penjadwalan event tertunda memakai antrean kecil + _process yang HANYA
# hidup saat antrean tidak kosong (hemat baterai Android).
class_name SylaraCombatFeel
extends Node

const Pal = preload("res://scenes/hero/sylara/SylaraPalette.gd")

## Antrean event tertunda: {t, kind, pos, dir}.
var _pending: Array[Dictionary] = []

var _skel: SylaraSkeleton = null


func _ready() -> void:
	set_process(false)
	var p := get_parent()
	if p is SylaraSkeleton:
		_skel = p as SylaraSkeleton
		if not _skel.attack_impact.is_connected(_on_attack_impact):
			_skel.attack_impact.connect(_on_attack_impact)
		if not _skel.character_died.is_connected(_on_character_died):
			_skel.character_died.connect(_on_character_died)


# ══════════════════════════════════════════════════════════
#  BASIC ATTACK — kilatan nock / sabit tunggal
# ══════════════════════════════════════════════════════════

func _on_attack_impact() -> void:
	if _skel == null or not is_instance_valid(_skel):
		return
	if _skel.last_attack_kind == "swing":
		# Melee riposte: SATU sabit angin di ujung busur (pengganti trail
		# global yang rusak — world-space, pooled, auto-release).
		var tip: Vector2 = _skel.get_bow_tip_global()
		var grip: Vector2 = _skel.get_bow_grip_global()
		var d: Vector2 = tip - grip
		var ang := 0.0
		if d.length_squared() > 0.01:
			ang = atan2(-d.y, d.x)
		VFXManager.slash(tip, ang, 30.0, 1.9, Pal.WIND, 0.0, 0.26, 0.0, 7.0)
	else:
		# Ranged loose: kilatan nock kecil tepat saat tali dilepas.
		VFXManager.flash(_skel.get_bow_nock_global(), 5.0,
			Pal.WIND_BRIGHT, 0.0, 0.10)


# ══════════════════════════════════════════════════════════
#  DEATH — paket perpisahan sekali pakai (3 aktor)
# ══════════════════════════════════════════════════════════

func _on_character_died() -> void:
	if _skel == null or not is_instance_valid(_skel):
		return
	var c: Vector2 = _skel.global_position + Vector2(0.0, -14.0)
	VFXManager.flash(c, 9.0, Pal.WIND_LIGHT, 0.0, 0.16)
	VFXManager.ring(c, 26.0, Pal.WIND, 0.03, 0.38, 2.4)
	VFXManager.sparks(c, PI * 0.5, 5, 95.0, Pal.LEAF, 0.02, 0.4, 1.0)


# ══════════════════════════════════════════════════════════
#  SKILL R — event tertunda (release & impact)
# ══════════════════════════════════════════════════════════

## Bunyi busur dilepas pada momen release visual (t ≈ 0.45 dtk).
func schedule_r_release(delay: float) -> void:
	_pending.append({"t": maxf(0.0, delay), "kind": "r_audio",
		"pos": Vector2.ZERO, "dir": Vector2.RIGHT})
	set_process(true)


## Paket impact R pada MOMEN DAMAGE (t ≈ 0.95 dtk): flash + ring + sparks
## terarah + hit-stop + shake — komposisi setara VFXManager.impact(tier 3)
## tetapi WAKTUNYA disinkronkan ke powershot_timer, bukan ke cast.
func schedule_r_impact(pos: Vector2, beam_dir: Vector2, delay: float) -> void:
	_pending.append({"t": maxf(0.0, delay), "kind": "r_impact",
		"pos": pos, "dir": beam_dir})
	set_process(true)


func _process(delta: float) -> void:
	if _pending.is_empty():
		set_process(false)
		return
	for i in range(_pending.size() - 1, -1, -1):
		var ev: Dictionary = _pending[i]
		ev["t"] = float(ev["t"]) - delta
		if float(ev["t"]) > 0.0:
			continue
		_pending.remove_at(i)
		_fire(ev)
	if _pending.is_empty():
		set_process(false)


func _fire(ev: Dictionary) -> void:
	match String(ev.get("kind", "")):
		"r_audio":
			AudioManager.play_combat("hero_ranged", 0.9)
		"r_impact":
			_fire_r_impact(ev["pos"] as Vector2, ev["dir"] as Vector2)


func _fire_r_impact(pos: Vector2, beam_dir: Vector2) -> void:
	VFXManager.flash(pos, 17.0, Pal.WIND_WHITE, 0.0, 0.16)
	VFXManager.ring(pos, 42.0, Pal.WIND, 0.02, 0.4, 2.8)
	var ang := 0.0
	if beam_dir.length_squared() > 0.01:
		ang = atan2(-beam_dir.y, beam_dir.x)
	VFXManager.sparks(pos, ang, 6, 240.0, Pal.WIND_BRIGHT, 0.0, 0.34, 0.55)
	# Hit-stop + shake proporsional ULTIMATE (sama seperti tier 3):
	# singkat agar game tidak terasa macet.
	GameManager.request_hit_stop(0.05, 0.05)
	var tree := get_tree()
	if tree != null:
		tree.call_group("camera", "add_trauma", 0.14)
	AudioManager.play_sfx("explosion", 0.22)
	if _skel != null and is_instance_valid(_skel):
		_skel.skill_impact.emit("r", pos)
