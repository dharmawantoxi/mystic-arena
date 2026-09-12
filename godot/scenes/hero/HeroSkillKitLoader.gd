# HeroSkillKitLoader.gd — pilih implementasi skill kit: GDExt (MysticHeroSkills) atau GDScript (HeroSkillKit.gd)
# Dibangkitkan sebagai bagian dari migrasi hero_skills -> godot++.
# Paritas: API sama persis dengan HeroSkillKit.gd (static methods).
# Jika mystic/skills/use_gdext_skills=true dan class MysticHeroSkills ada, pakai C++.
# Jika tidak, fallback ke GDScript transpiled (paritas 1:1 dengan Python).

extends RefCounted

const HeroSkillKitGD = preload("res://scenes/hero/HeroSkillKit.gd")

static var _use_gdext: bool = false
static var _checked: bool = false

static func _ensure_checked() -> void:
	if _checked:
		return
	_checked = true
	var flag = false
	if ProjectSettings.has_setting("mystic/skills/use_gdext_skills"):
		flag = bool(ProjectSettings.get_setting("mystic/skills/use_gdext_skills"))
	# Juga cek keberadaan class GDExt
	if flag and ClassDB.class_exists("MysticHeroSkills"):
		_use_gdext = true
	else:
		_use_gdext = false

static func is_using_gdext() -> bool:
	_ensure_checked()
	return _use_gdext

static func hero_kind(h) -> String:
	_ensure_checked()
	if _use_gdext:
		return MysticHeroSkills.hero_kind(h)
	return HeroSkillKitGD.hero_kind(h)

static func init_state(h) -> void:
	_ensure_checked()
	if _use_gdext:
		MysticHeroSkills.init_state(h)
	else:
		HeroSkillKitGD.init_state(h)

static func update_timers(h, all_units, all_towers, all_bases) -> void:
	_ensure_checked()
	if _use_gdext:
		MysticHeroSkills.update_timers(h, all_units, all_towers, all_bases)
	else:
		HeroSkillKitGD.update_timers(h, all_units, all_towers, all_bases)

static func cast_q(h, all_units, all_towers, all_bases) -> bool:
	_ensure_checked()
	if _use_gdext:
		return MysticHeroSkills.cast_q(h, all_units, all_towers, all_bases)
	return HeroSkillKitGD.cast_q(h, all_units, all_towers, all_bases)

static func cast_w(h, all_units, all_towers, all_bases) -> bool:
	_ensure_checked()
	if _use_gdext:
		return MysticHeroSkills.cast_w(h, all_units, all_towers, all_bases)
	return HeroSkillKitGD.cast_w(h, all_units, all_towers, all_bases)

static func cast_e(h, all_units, all_towers, all_bases) -> bool:
	_ensure_checked()
	if _use_gdext:
		return MysticHeroSkills.cast_e(h, all_units, all_towers, all_bases)
	return HeroSkillKitGD.cast_e(h, all_units, all_towers, all_bases)

static func cast_r(h, all_units, all_towers, all_bases) -> bool:
	_ensure_checked()
	if _use_gdext:
		return MysticHeroSkills.cast_r(h, all_units, all_towers, all_bases)
	return HeroSkillKitGD.cast_r(h, all_units, all_towers, all_bases)

static func __by_pair0(a, b) -> bool:
	_ensure_checked()
	if _use_gdext:
		return MysticHeroSkills.__by_pair0(a, b)
	return HeroSkillKitGD.__by_pair0(a, b)

static func by_pair0(a, b) -> bool:
	return __by_pair0(a, b)

# Untuk kompatibilitas: expose visual duration constants via function
static func get_visual_duration(hero_type: String, key: String) -> int:
	_ensure_checked()
	if _use_gdext:
		return MysticHeroSkills.visual_duration(hero_type, key)
	return HeroSkillKitGD.__vis_dur(hero_type, key)
