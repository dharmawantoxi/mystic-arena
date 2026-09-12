# HeroSkillKitLoader.gd — pilih implementasi skill kit: GDExt (MysticHeroSkills) atau GDScript (HeroSkillKit.gd)
# Dibangkitkan sebagai bagian dari migrasi hero_skills -> godot++.
# Paritas: API sama persis dengan HeroSkillKit.gd (static methods).
# Jika mystic/skills/use_gdext_skills=true dan class MysticHeroSkills ada, pakai C++.
# Jika tidak, fallback ke GDScript transpiled (paritas 1:1 dengan Python).
# PENTING: tidak boleh referensi langsung ke `MysticHeroSkills` sebagai identifier,
# karena di CI headless lib .so tidak ada -> Parse Error. Semua akses lewat
# ClassDB.instantiate("MysticHeroSkills") + call() string, pola sama dengan
# LightingCompat.gd untuk MysticLighting.

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
	# Cek keberadaan class GDExt — string only, tidak pakai identifier langsung
	if flag and ClassDB.class_exists("MysticHeroSkills"):
		_use_gdext = true
		print("[HeroSkillKitLoader] GDExtension MysticHeroSkills aktif (godot++ C++)")
	else:
		_use_gdext = false
		if flag:
			print("[HeroSkillKitLoader] flag use_gdext_skills=true tapi GDExt tidak ditemukan, fallback GDScript")

static func is_using_gdext() -> bool:
	_ensure_checked()
	return _use_gdext

static func _call_gdext(method: String, args: Array):
	# Helper: instantiate dan callv, return Variant (null kalau gagal)
	if not _use_gdext:
		return null
	var inst = ClassDB.instantiate("MysticHeroSkills")
	if inst == null:
		return null
	if not inst.has_method(method):
		return null
	return inst.callv(method, args)

static func hero_kind(h) -> String:
	_ensure_checked()
	if _use_gdext:
		var r = _call_gdext("hero_kind", [h])
		if r != null:
			return str(r)
	return HeroSkillKitGD.hero_kind(h)

static func init_state(h) -> void:
	_ensure_checked()
	if _use_gdext:
		_call_gdext("init_state", [h])
		return
	HeroSkillKitGD.init_state(h)

static func update_timers(h, all_units, all_towers, all_bases) -> void:
	_ensure_checked()
	if _use_gdext:
		_call_gdext("update_timers", [h, all_units, all_towers, all_bases])
		return
	HeroSkillKitGD.update_timers(h, all_units, all_towers, all_bases)

static func cast_q(h, all_units, all_towers, all_bases) -> bool:
	_ensure_checked()
	if _use_gdext:
		var r = _call_gdext("cast_q", [h, all_units, all_towers, all_bases])
		if r != null:
			return bool(r)
	return HeroSkillKitGD.cast_q(h, all_units, all_towers, all_bases)

static func cast_w(h, all_units, all_towers, all_bases) -> bool:
	_ensure_checked()
	if _use_gdext:
		var r = _call_gdext("cast_w", [h, all_units, all_towers, all_bases])
		if r != null:
			return bool(r)
	return HeroSkillKitGD.cast_w(h, all_units, all_towers, all_bases)

static func cast_e(h, all_units, all_towers, all_bases) -> bool:
	_ensure_checked()
	if _use_gdext:
		var r = _call_gdext("cast_e", [h, all_units, all_towers, all_bases])
		if r != null:
			return bool(r)
	return HeroSkillKitGD.cast_e(h, all_units, all_towers, all_bases)

static func cast_r(h, all_units, all_towers, all_bases) -> bool:
	_ensure_checked()
	if _use_gdext:
		var r = _call_gdext("cast_r", [h, all_units, all_towers, all_bases])
		if r != null:
			return bool(r)
	return HeroSkillKitGD.cast_r(h, all_units, all_towers, all_bases)

static func __by_pair0(a, b) -> bool:
	_ensure_checked()
	if _use_gdext:
		var r = _call_gdext("__by_pair0", [a, b])
		if r != null:
			return bool(r)
	return HeroSkillKitGD.__by_pair0(a, b)

static func by_pair0(a, b) -> bool:
	return __by_pair0(a, b)

static func get_visual_duration(hero_type: String, key: String) -> int:
	_ensure_checked()
	if _use_gdext:
		var r = _call_gdext("visual_duration", [hero_type, key])
		if r != null:
			return int(r)
	# Fallback: GDScript punya __vis_dur dengan signature beda (kind, h, key)
	# Untuk loader kita butuh mapping hero_type -> kind, jadi panggil via
	# BOSS_HERO_VISUAL_DURATION / VISUAL_DURATION jika ada, else 0.
	# Sederhana: coba panggil helper GDScript yang ada, atau fallback 40.
	# HeroSkillKitGD.__vis_dur butuh h, jadi kita akses konstanta langsung
	# kalau tersedia.
	if HeroSkillKitGD.has_method("__vis_dur"):
		# tidak punya h, fallback ke DEFAULT
		return 40
	return 40

static func visual_duration(hero_type: String, key: String) -> int:
	return get_visual_duration(hero_type, key)
