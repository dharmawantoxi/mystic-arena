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


## Layer 5b-3: one damage amount for a unit target: school mitigation with the
## effective armor, then the Soul Rend damage amp (source take_damage order).
static func item_aware_amount(unit: Object, raw_damage: int, school: String) -> int:
	if school == "neutral":
		return raw_damage
	var damage: int = resolve(
		raw_damage, effective_armor(unit), float(unit.definition.magic_resist), school
	)
	if unit.dmg_amp_timer > 0 and damage > 0:
		damage = rounded_like_python(float(damage) * (1.0 + unit.dmg_amp_amount))
	return damage


static func resolve(raw_damage: int, armor: float, resist: float, school: String) -> int:
	if raw_damage <= 0 or school not in ["physical", "magic"]:
		return 0
	if school == "physical" and armor > 0:
		var reduction := armor * 0.06 / (1.0 + armor * 0.06)
		return maxi(1, rounded_like_python(raw_damage * (1.0 - reduction)))
	if school == "physical" and armor < 0:
		return rounded_like_python(raw_damage * (1.0 + minf(1.0, -armor * 0.06)))
	if school == "magic" and resist > 0:
		return maxi(1, rounded_like_python(raw_damage * (1.0 - clampf(resist, 0, 1))))
	return raw_damage
