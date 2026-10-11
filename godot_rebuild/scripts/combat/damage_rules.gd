extends RefCounted
## Plain minion damage only. No item amp/shred, debuffs, shields, or hero/boss rules yet.


static func rounded_like_python(value: float) -> int:
	var lower := int(floor(value))
	var fraction := value - lower
	if fraction == 0.5:
		return lower if lower % 2 == 0 else lower + 1
	return lower + 1 if fraction > 0.5 else lower


## Layer 5b-3: armor actually used for a hit: definition armor, plus the
## owner's item armor (heroes), minus any Corroder armor shred on the target.
static func effective_armor(unit: Object) -> float:
	var armor: float = float(unit.definition.armor) - float(unit.armor_shred_amount)
	var inventory: Variant = unit.get("items")
	if inventory != null:
		armor += float(inventory.get_armor())
	return armor


## Layer 5b-3: one damage amount for a non-hero unit target.
## Layer 9l: heroes run the source ladder instead (`hero_amount`).
## Layer 9n: live minions run the source ladder of `Minion.take_damage`
## (`_entity.py:5795-5825`) - amp, then the Corroder shred bonus, then the
## school mitigation - and a school-free hit keeps that amp instead of landing
## raw. Bosses keep the older school-first order, because their mitigation is
## its own port (`BaseBoss.take_damage`).
static func item_aware_amount(
	unit: Object, raw_damage: int, school: String, damage_type: String = "normal"
) -> int:
	if unit.get("is_hero") == true:
		return hero_amount(unit, raw_damage, damage_type)
	if unit.get("boss_type") != null:
		return _school_first_amount(unit, raw_damage, school)
	return minion_amount(unit, raw_damage, school, damage_type)


## The source minion ladder (`_entity.py:5795-5825`): the Soul Rend amp, then
## the Corroder shred bonus on every non-fire hit, then physical armour (with
## the same shred subtracted a second time, exactly like the source) or the
## magic resistance cut. A school-free hit only keeps the two bonuses.
static func minion_amount(
	unit: Object, raw_damage: int, school: String, damage_type: String = "normal"
) -> int:
	if raw_damage <= 0:
		return 0
	var damage := raw_damage
	if int(unit.dmg_amp_timer) > 0:
		damage = rounded_like_python(float(damage) * (1.0 + float(unit.dmg_amp_amount)))
	if damage_type != "fire":
		var shred := float(unit.armor_shred_amount)
		if shred > 0.0:
			damage = rounded_like_python(float(damage) * (1.0 + minf(1.0, shred * 0.06)))
	if damage <= 0:
		return damage
	if school == "physical":
		return resolve_armor(damage, effective_armor(unit))
	if school == "magic":
		var magic_resist := clampf(float(unit.definition.magic_resist), 0.0, 1.0)
		if magic_resist > 0.0:
			return maxi(1, rounded_like_python(float(damage) * (1.0 - magic_resist)))
	return damage


## Pre-9n order, kept for boss targets: school mitigation with the effective
## armour first, the Soul Rend amp after it, and a school-free hit lands raw.
static func _school_first_amount(unit: Object, raw_damage: int, school: String) -> int:
	if school == "neutral":
		return raw_damage
	var damage: int = resolve(
		raw_damage, effective_armor(unit), float(unit.definition.magic_resist), school
	)
	if int(unit.dmg_amp_timer) > 0 and damage > 0:
		damage = rounded_like_python(float(damage) * (1.0 + float(unit.dmg_amp_amount)))
	return damage


## Layer 9l: `Hero.take_damage` mitigation (`_entity.py:4638-4672`). The Soul
## Rend amp runs FIRST, then the armour formula runs for every non-fire hit
## regardless of school - the source never reads `magic_resist` for heroes, and
## all 222 hero definitions carry `armor = 0`, so the only armour a hero ever
## has comes from items (`get_armor()` minus `armor_shred_amount`).
static func hero_amount(unit: Object, raw_damage: int, damage_type: String) -> int:
	if raw_damage <= 0:
		return 0
	var damage := raw_damage
	if unit.dmg_amp_timer > 0:
		damage = rounded_like_python(float(damage) * (1.0 + unit.dmg_amp_amount))
	if damage_type == "fire" or damage <= 0:
		return damage
	return resolve_armor(damage, effective_armor(unit))


## The MOBA armour formula of the source, both signs, no school involved.
static func resolve_armor(raw_damage: int, armor: float) -> int:
	if raw_damage <= 0:
		return 0
	if armor > 0:
		var reduction := armor * 0.06 / (1.0 + armor * 0.06)
		return maxi(1, rounded_like_python(float(raw_damage) * (1.0 - reduction)))
	if armor < 0:
		return rounded_like_python(float(raw_damage) * (1.0 + minf(1.0, -armor * 0.06)))
	return raw_damage


static func resolve(raw_damage: int, armor: float, resist: float, school: String) -> int:
	if raw_damage <= 0 or school not in ["physical", "magic"]:
		return 0
	if school == "physical":
		return resolve_armor(raw_damage, armor)
	if school == "magic" and resist > 0:
		return maxi(1, rounded_like_python(raw_damage * (1.0 - clampf(resist, 0, 1))))
	return raw_damage
