class_name BossCatalog
extends RefCounted

## Native bosses/ catalog: renderer index, smart-AI dispatch set, and the
## pristine -> rebalanced -> smoothed -> curved -> hero-unlock pipeline.
const DEFAULT_PATH := "res://data/bosses.json"
var data: Dictionary = {}
var load_error := ""


func _init(path := DEFAULT_PATH) -> void:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		load_error = "Cannot open %s" % path
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary or int(parsed.get("schema", 0)) != 1:
		load_error = "Invalid bosses JSON: %s" % path
		return
	for key: String in [
		"files",
		"bosses",
		"pristine",
		"curves",
		"smart_ai",
		"kite_types",
		"mini_boss_waves",
		"level_true_boss",
		"melee_role_hints",
		"pristine_order",
		"counts"
	]:
		if not parsed.has(key):
			load_error = "Missing bosses field: %s" % key
			return
	data = parsed
	var counts: Dictionary = data.counts
	if (
		int(counts.get("files", 0)) != 61
		or int(counts.get("mini", 0)) != 162
		or int(counts.get("true", 0)) != 54
		or int(counts.get("smart_ai", 0)) != 79
	):
		load_error = "Unexpected bosses coverage counts"
	elif data.bosses.size() != 216 or data.files.size() != 61:
		load_error = "Boss catalog/index must cover 216 bosses and 61 source files"


func valid() -> bool:
	return load_error.is_empty() and not data.is_empty()


func has_smart_ai(boss_type: String) -> bool:
	return boss_type in data.get("smart_ai", [])


func kites(boss_type: String) -> bool:
	return boss_type in data.get("kite_types", [])


func label_top(boss_type: String, radius: float) -> float:
	var row: Dictionary = data.get("bosses", {}).get(boss_type, {})
	return maxf(float(row.get("label_top", radius)), radius)


func renderer(boss_type: String) -> Dictionary:
	return data.get("bosses", {}).get(boss_type, {})


func matches_core(core: Dictionary) -> bool:
	if not valid():
		return false
	var bosses: Dictionary = core.get("bosses", {})
	if (
		set_diff(bosses.get("mini", {}), data.pristine.mini)
		or set_diff(bosses.get("true", {}), data.pristine["true"])
	):
		return false
	var normalized := normalize(core.get("levels", []))
	for kind: String in ["mini", "true"]:
		for key: String in normalized[kind]:
			var row: Dictionary = normalized[kind][key]
			var tracked: Dictionary = bosses[kind][key]
			for field: String in row:
				if field == "hero_unlock":
					var unlock: Dictionary = row.hero_unlock
					var core_unlock: Dictionary = tracked.get("hero_unlock", {})
					for uf: String in unlock:
						if not _same(unlock[uf], core_unlock.get(uf)):
							return false
				elif not _same(row[field], tracked.get(field)):
					return false
	return true


static func set_diff(a: Dictionary, b: Dictionary) -> bool:
	if a.size() != b.size():
		return true
	for key: Variant in a:
		if not b.has(key):
			return true
	return false


static func _same(a: Variant, b: Variant) -> bool:
	if (a is float or a is int) and (b is float or b is int):
		return absf(float(a) - float(b)) < 0.000001
	return a == b


func normalize(levels: Array) -> Dictionary:
	var tables: Dictionary = data.pristine.duplicate(true)
	_rebalance(tables.mini, false)
	_rebalance(tables["true"], true)
	_smooth(tables, levels)
	_curves(tables["true"])
	_unlock_stats(tables.mini, data.pristine_order.mini)
	_unlock_stats(tables["true"], data.pristine_order["true"])
	_unlock_range(tables.mini)
	_unlock_range(tables["true"])
	return tables


static func _rebalance(table: Dictionary, is_true: bool) -> void:
	for key: String in table:
		var row: Dictionary = table[key]
		var hp := int(row.get("hp", 15000 if is_true else 3000))
		var dmg := int(row.get("damage", 100 if is_true else 50))
		var ab := int(row.get("ability_damage", 200 if is_true else 100))
		var new_hp: int
		var new_dmg: int
		if is_true:
			if hp < 20000:
				new_hp = maxi(36000, int(hp * 2.4))
			elif hp < 40000:
				new_hp = int(hp * 2.0)
			elif hp < 70000:
				new_hp = int(hp * 1.6)
			else:
				new_hp = int(hp * 1.45)
			if dmg < 120:
				new_dmg = maxi(145, int(dmg * 1.5))
			elif dmg < 250:
				new_dmg = int(dmg * 1.3)
			else:
				new_dmg = int(dmg * 1.25)
			row.ability_damage = maxi(ab, int(ab * 1.35))
		else:
			if hp < 10000:
				new_hp = maxi(7500, int(hp * 2.2))
			elif hp < 20000:
				new_hp = int(hp * 1.6)
			elif hp < 40000:
				new_hp = int(hp * 1.4)
			else:
				new_hp = int(hp * 1.3)
			if dmg < 100:
				new_dmg = maxi(85, int(dmg * 1.4))
			elif dmg < 200:
				new_dmg = int(dmg * 1.25)
			else:
				new_dmg = int(dmg * 1.2)
			row.ability_damage = maxi(ab, int(ab * 1.25))
		row.hp = new_hp
		row.damage = new_dmg
		for skill: String in ["q", "w", "e", "r"]:
			var field := "skill_%s_damage" % skill
			if row.has(field) and float(row[field]) > 0.0:
				row[field] = int(float(row[field]) * (1.35 if is_true else 1.25))


static func slot_of_wave(wave: int) -> String:
	if wave <= 12:
		return "w10"
	if wave <= 21:
		return "w18"
	return "w25"


func _smooth(tables: Dictionary, levels: Array) -> void:
	var ordered: Array = levels.duplicate()
	ordered.sort_custom(
		func(a: Dictionary, b: Dictionary) -> bool:
			return int(a.get("level_number", 0)) < int(b.get("level_number", 0))
	)
	var prev: Dictionary = {}
	for slot: String in ["w10", "w18", "w25"]:
		prev[slot] = {"hp": 0, "damage": 0, "ability_damage": 0}
	for level: Dictionary in ordered:
		var waves: Dictionary = level.get("mini_bosses", {})
		var keys: Array = waves.keys()
		keys.sort_custom(func(a: Variant, b: Variant) -> bool: return int(a) < int(b))
		for wave: Variant in keys:
			var name := str(waves[wave])
			if not tables.mini.has(name):
				continue
			var row: Dictionary = tables.mini[name]
			var slot := slot_of_wave(int(wave))
			for field: String in ["hp", "damage", "ability_damage"]:
				row[field] = maxi(int(row.get(field, 0)), int(prev[slot][field]))
				prev[slot][field] = row[field]
	var true_prev := {"hp": 0, "damage": 0, "ability_damage": 0}
	for level: Dictionary in ordered:
		var name := str(level.get("true_boss", ""))
		if not tables["true"].has(name):
			continue
		var row: Dictionary = tables["true"][name]
		for field: String in ["hp", "damage", "ability_damage"]:
			row[field] = maxi(int(row.get(field, 0)), int(true_prev[field]))
			true_prev[field] = row[field]


func _curves(true_table: Dictionary) -> void:
	for field: String in ["hp", "damage", "ability"]:
		var curve: Dictionary = data.curves.get(field, {})
		var target := "ability_damage" if field == "ability" else field
		for name: String in curve:
			if true_table.has(name):
				true_table[name][target] = int(curve[name])


static func trend(values: Array) -> Vector2:
	var n := values.size()
	if n == 0:
		return Vector2.ZERO
	var mx := 0.0
	var my := 0.0
	for pair: Array in values:
		mx += float(pair[0])
		my += float(pair[1])
	mx /= n
	my /= n
	var sxx := 0.0
	var sxy := 0.0
	for pair: Array in values:
		var c := float(pair[0])
		var v := float(pair[1])
		sxx += (c - mx) * (c - mx)
		sxy += (c - mx) * (v - my)
	if sxx == 0.0:
		return Vector2(0.0, my)
	var a := sxy / sxx
	return Vector2(a, my - a * mx)


static func _clamp(value: float, pred: float) -> float:
	if pred <= 0.0:
		return value
	if value <= 0.0 or value < 0.70 * pred:
		return maxf(value, 0.80 * pred)
	if value > 1.30 * pred:
		return minf(value, 1.20 * pred)
	return value


func _unlock_stats(table: Dictionary, order: Array) -> void:
	var heroes: Array = []
	var ranks: Dictionary = {}
	for i in range(order.size()):
		ranks[str(order[i])] = i
	for key: String in table:
		var unlock: Variant = table[key].get("hero_unlock")
		if unlock is Dictionary and not unlock.is_empty():
			heroes.append({"key": key, "hu": unlock, "i": int(ranks.get(key, 100000))})
	heroes.sort_custom(
		func(a: Dictionary, b: Dictionary) -> bool:
			var ca := float(a.hu.get("cost", 0))
			var cb := float(b.hu.get("cost", 0))
			return ca < cb if ca != cb else int(a.i) < int(b.i)
	)
	var hp_pts: Array = []
	var dps_pts: Array = []
	var sk_pts: Array = []
	for item: Dictionary in heroes:
		var hu: Dictionary = item.hu
		var cost := float(hu.get("cost", 0))
		var cd := maxi(1, int(hu.get("attack_cooldown", 30)))
		hp_pts.append([cost, float(hu.get("hp", 0))])
		dps_pts.append([cost, float(hu.get("damage", 0)) / cd * 60.0])
		sk_pts.append([cost, float(hu.get("skill_damage", 0))])
	var hp_fit := trend(hp_pts)
	var dps_fit := trend(dps_pts)
	var sk_fit := trend(sk_pts)
	for item: Dictionary in heroes:
		var hu: Dictionary = item.hu
		var cost := float(hu.get("cost", 0))
		hu.skill_damage = HeroBalance.py_round(
			_clamp(float(hu.get("skill_damage", 0)), sk_fit.x * cost + sk_fit.y)
		)
		hu.hp = HeroBalance.py_round(_clamp(float(hu.get("hp", 0)), hp_fit.x * cost + hp_fit.y))
		var cd := maxi(1, int(hu.get("attack_cooldown", 30)))
		var cur := float(hu.get("damage", 0)) / cd * 60.0
		var new_dps := _clamp(cur, dps_fit.x * cost + dps_fit.y)
		if new_dps != cur:
			hu.damage = HeroBalance.py_round(new_dps * cd / 60.0)
	var m_hp := 0
	var m_dmg := 0
	var m_sk := 0
	for item: Dictionary in heroes:
		var hu: Dictionary = item.hu
		if int(hu.hp) < 0.85 * m_hp:
			hu.hp = m_hp
		else:
			m_hp = maxi(m_hp, int(hu.hp))
		if int(hu.damage) < 0.85 * m_dmg:
			hu.damage = m_dmg
		else:
			m_dmg = maxi(m_dmg, int(hu.damage))
		if int(hu.skill_damage) < 0.85 * m_sk:
			hu.skill_damage = m_sk
		else:
			m_sk = maxi(m_sk, int(hu.skill_damage))


func _unlock_range(table: Dictionary) -> void:
	for key: String in table:
		var hu: Variant = table[key].get("hero_unlock")
		if not hu is Dictionary or hu.is_empty():
			continue
		var role := str(hu.get("role", "")).to_lower()
		var orig := int(hu.get("range", 70))
		var melee := orig <= 90
		for hint: String in data.melee_role_hints:
			if role.contains(hint):
				melee = true
				break
		hu.range = 70 if melee else clampi(orig, 120, 220)
		var sr := int(hu.get("skill_range", 0))
		if sr > 0 and sr < int(hu.range):
			hu.skill_range = hu.range
