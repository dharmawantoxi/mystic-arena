# DamageSchool.gd — Port dari _entity.py resolve_damage_school + pembulatan Python
extends RefCounted
class_name DamageSchool

# Di pygame: _is_physical_hit + resolve_damage_school.
# Mitigasi armor/MR TIDAK lagi universal di sini: tiap jenis target
# (hero/minion/boss/tower) memakai blok take_damage-nya sendiri di
# CombatSystem (audit jalur damage basic hero — lihat docs/AUDIT_ULANG_DARI_AWAL.md).

static func resolve(school: String, dmg_type: String, source) -> String:
	if school in ["physical","magic"]:
		return school
	if dmg_type in ["fire","ice","heal","crit"]:
		return ""
	if source and "dmg_school" in source:
		var s = source.dmg_school
		if s in ["physical","magic"]:
			return s
	return ""

static func is_physical_hit(dmg_type: String, school: String) -> bool:
	if dmg_type not in ["normal","projectile"]:
		return false
	return school != "magic"


## round() Python = banker's rounding (half to even); round() GDScript
## membulatkan half AWAY from zero. pygame memakai int(round(x)) di seluruh
## pipeline damage, jadi hasil .5 persis harus mengikuti Python
## (contoh terkunci: reflect Bristleback 17*0.7353.. = 12.5 -> 12, bukan 13).
static func py_round(x: float) -> float:
	# floorf() (bukan floor()): floor() global mengembalikan Variant di
	# Godot 4.3 → inferensi := gagal ("Cannot infer the type of 'diff'").
	var f := floorf(x)
	var diff := x - f
	if diff > 0.5:
		return f + 1.0
	if diff < 0.5:
		return f
	# half -> genap (12.5 -> 12, 13.5 -> 13, -2.5 -> -2)
	return f if int(f) % 2 == 0 else f + 1.0
