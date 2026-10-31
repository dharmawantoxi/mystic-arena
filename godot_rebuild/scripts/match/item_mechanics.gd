extends RefCounted
## Port of the `hero_items.py` DETAIL POPUP mechanics half (layer 9ck).
##
## `_FIELD_LABELS`, `_GROUP_LABELS`, `_MECH_GROUPS`, `_PCT_KEYS` and
## `_FRAME_KEYS` plus `_fmt_mech_value` / `_build_item_mechanics` turn one
## `ITEM_CATALOG` entry into the ordered `[GROUP] name` headers and
## "• label: value" bullets the item detail popup prints. The lists stay in
## source order (stats, passive, active, aura, block, on_attack, multishot,
## bash) and every label keeps both languages.
##
## `fmt_value` mirrors Python `f"{value:g}"`: six significant digits with the
## trailing zeros stripped, percentages times 100, frame counts divided by 60
## and spelled `dtk` / `s`.
##
## Sync: python3 godot_rebuild/tests/hero_items_source_oracle.py --write

const FIELD_LABELS := {
	"damage": ["Damage", "Damage"],
	"hp": ["Max HP", "Max HP"],
	"hp_pct": ["Max HP", "Max HP"],
	"hp_regen": ["HP Regen", "HP Regen"],
	"armor": ["Armor", "Armor"],
	"attack_speed": ["Attack Speed", "Attack Speed"],
	"crit_chance": ["Peluang Crit", "Crit Chance"],
	"crit_mult": ["Pengali Crit", "Crit Multiplier"],
	"lifesteal": ["Lifesteal", "Lifesteal"],
	"lifesteal_bonus": ["Bonus Lifesteal", "Lifesteal Bonus"],
	"cooldown_reduction": ["Cooldown Reduction", "Cooldown Reduction"],
	"spell_vamp": ["Spell Lifesteal", "Spell Lifesteal"],
	"skill_amp": ["Skill Amp", "Skill Amp"],
	"evasion": ["Evasion", "Evasion"],
	"move_speed_pct": ["Move Speed", "Move Speed"],
	"heal_amp": ["Heal Diterima", "Incoming Heal"],
	"slow_resist": ["Tahan Slow", "Slow Resist"],
	"range_bonus": ["Bonus Jangkauan", "Attack Range Bonus"],
	"hp_threshold": ["Ambang HP", "HP Threshold"],
	"duration": ["Durasi", "Duration"],
	"cooldown": ["Cooldown", "Cooldown"],
	"ally_radius": ["Radius Sekutu", "Ally Radius"],
	"ally_armor": ["Armor Sekutu", "Ally Armor"],
	"ally_attack_speed": ["AS Sekutu", "Ally Attack Speed"],
	"base_block": ["Block Dasar", "Base Block"],
	"max_hp_block_pct": ["Block (% Max HP)", "Block (% Max HP)"],
	"stun": ["Stun", "Stun"],
	"silence": ["Silence", "Silence"],
	"silence_duration": ["Durasi Silence", "Silence Duration"],
	"trigger_enemies": ["Pemicu Musuh Dekat", "Trigger Enemies"],
	"trigger_radius": ["Radius Pemicu", "Trigger Radius"],
	"root_radius": ["Radius Root", "Root Radius"],
	"root_duration": ["Durasi Root", "Root Duration"],
	"proc_chance": ["Peluang Aktif", "Proc Chance"],
	"tick": ["Interval Tick", "Tick Interval"],
	"targets": ["Jumlah Target", "Targets"],
	"radius": ["Radius", "Radius"],
	"slow": ["Slow Gerak", "Move Slow"],
	"atk_slow": ["Slow Serang", "Attack Slow"],
	"slow_duration": ["Durasi Slow", "Slow Duration"],
	"burn_dps": ["Bakar (dmg/dtk)", "Burn (dmg/s)"],
	"burn_duration": ["Durasi Bakar", "Burn Duration"],
	"dash_distance": ["Jarak Dorong", "Dash Distance"],
	"as_bonus": ["Bonus Attack Speed", "Attack Speed Bonus"],
	"heal_pct": ["Heal (% Max HP)", "Heal (% Max HP)"],
	"reflect_pct": ["Pantulan Damage", "Damage Reflect"],
	"damage_amp": ["Amplifikasi Damage", "Damage Amp"],
	"chance": ["Peluang", "Chance"],
	"cleave_pct": ["Splash Damage", "Cleave Damage"],
	"cleave_radius": ["Radius Splash", "Cleave Radius"],
	"out_of_combat_regen_pct": ["Regen Luar Tempur", "Out-of-Combat Regen"],
	"combat_timeout": ["Timeout Tempur", "Combat Timeout"],
	"armor_shred": ["Kikis Armor", "Armor Shred"],
	"charge_time": ["Waktu Isi Muatan", "Charge Time"],
	"enemy_radius": ["Radius Musuh", "Enemy Radius"],
	"enemy_armor_reduction": ["Kurangi Armor Musuh", "Enemy Armor Reduction"],
	"enemy_atk_slow": ["AS Musuh Berkurang", "Enemy AS Reduction"],
	"enemy_anti_heal": ["Anti-Heal Musuh", "Enemy Anti-Heal"],
	"blind": ["Musuh Melenceng", "Enemy Miss Chance"],
	"melee_block": ["Block (Melee)", "Block (Melee)"],
	"ranged_block": ["Block (Ranged)", "Block (Ranged)"],
	"anti_heal": ["Anti-Heal", "Anti-Heal"],
	"max_hp_pct_per_tick": ["Racun (% Max HP/tick)", "Poison (% Max HP/tick)"],
	"cap_damage": ["Batas Damage", "Damage Cap"],
	"damage_pct": ["Damage Tembakan Ekstra", "Extra Shot Damage"],
}

const GROUP_LABELS := {
	"stats": ["STAT", "STATS"],
	"passive": ["PASIF", "PASSIVE"],
	"active": ["AKTIF", "ACTIVE"],
	"aura": ["AURA", "AURA"],
	"block": ["BLOCK", "BLOCK"],
	"on_attack": ["EFEK SERANGAN", "ON-ATTACK"],
	"multishot": ["MULTISHOT", "MULTISHOT"],
	"bash": ["BASH", "BASH"],
}

const MECH_GROUPS := [
	"stats",
	"passive",
	"active",
	"aura",
	"block",
	"on_attack",
	"multishot",
	"bash",
]

const PCT_KEYS := [
	"anti_heal", "atk_slow", "blind", "chance", "cleave_pct", "cooldown_reduction",
	"crit_chance", "damage_amp", "damage_pct", "enemy_anti_heal", "enemy_atk_slow", "evasion",
	"heal_amp", "heal_pct", "hp_pct", "hp_threshold", "lifesteal", "lifesteal_bonus",
	"max_hp_block_pct", "max_hp_pct_per_tick", "move_speed_pct", "out_of_combat_regen_pct",
	"proc_chance", "reflect_pct", "skill_amp", "slow", "slow_resist", "spell_vamp",
]

const FRAME_KEYS := [
	"burn_duration", "charge_time", "combat_timeout", "cooldown", "duration", "root_duration",
	"silence", "silence_duration", "slow_duration", "stun", "tick",
]



static func fmt_value(key: String, value: Variant, en: bool = false) -> String:
	# Source _fmt_mech_value, same branch order: crit multiplier, percent,
	# frames-per-second, then the plain value.
	if key == "crit_mult":
		return "x" + _g(float(value))
	if PCT_KEYS.has(key):
		return _g(float(value) * 100.0) + "%"
	if FRAME_KEYS.has(key):
		var secs := float(value) / 60.0
		return _g(secs) + ("s" if en else " dtk")
	return _plain(value)


static func build(data: Dictionary, en: bool = false) -> Array:
	# Source _build_item_mechanics: one header per non-empty group in
	# MECH_GROUPS order, then one bullet per field in the catalog order.
	var lines: Array = []
	for raw_group in MECH_GROUPS:
		var gkey := String(raw_group)
		var group: Variant = data.get(gkey)
		if not group is Dictionary or (group as Dictionary).is_empty():
			continue
		var labels: Array = GROUP_LABELS[gkey]
		var group_name := String((group as Dictionary).get("name", ""))
		var header := "[%s]" % String(labels[1] if en else labels[0])
		if not group_name.is_empty():
			header += " " + group_name
		lines.append(["header", header])
		for field in group:
			if String(field) == "name":
				continue
			var label: Array = FIELD_LABELS.get(field, [field, field])
			lines.append(
				[
					"bullet",
					"• %s: %s" % [
						String(label[1] if en else label[0]),
						fmt_value(String(field), (group as Dictionary)[field], en),
					],
				]
			)
	return lines


static func _plain(value: Variant) -> String:
	# Python str(): ints stay ints even after the JSON round trip takes them
	# through a float, booleans keep their capitalised spelling.
	if value is bool:
		return "True" if bool(value) else "False"
	if value is int:
		return str(value)
	if value is float:
		return _g(float(value))
	if value is Array:
		var parts: Array[String] = []
		for entry in value:
			parts.append(_plain(entry))
		return "[" + ", ".join(parts) + "]"
	return str(value)


static func _g(value: float) -> String:
	# Python "%g": six significant digits, trailing zeros stripped.
	if is_nan(value):
		return "nan"
	if is_inf(value):
		return "inf" if value > 0.0 else "-inf"
	if value == 0.0:
		return "0"
	var exponent := int(floor(log(absf(value)) / log(10.0)))
	if exponent >= 6 or exponent < -4:
		var mantissa := value / pow(10.0, float(exponent))
		var sign := "-" if exponent < 0 else "+"
		return "%se%s%02d" % [_trim(String.num(mantissa, 5)), sign, absi(exponent)]
	var decimals := 5 - exponent
	if decimals < 0:
		var factor := int(roundf(pow(10.0, float(-decimals))))
		return str(int(roundf(value / float(factor))) * factor)
	return _trim(String.num(value, decimals))


static func _trim(text: String) -> String:
	if not text.contains("."):
		return text
	while text.ends_with("0"):
		text = text.substr(0, text.length() - 1)
	if text.ends_with("."):
		text = text.substr(0, text.length() - 1)
	return text
