extends RefCounted
## Plain minion damage only. No item amp/shred, debuffs, shields, or hero/boss rules yet.


static func rounded_like_python(value: float) -> int:
	var lower := int(floor(value))
	var fraction := value - lower
	if fraction == 0.5:
		return lower if lower % 2 == 0 else lower + 1
	return lower + 1 if fraction > 0.5 else lower


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
