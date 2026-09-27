extends RefCounted
## Temporary, asset-free hero silhouettes. Visual polish belongs after migration.
## Stable ID-derived shape/color; team ring and facing remain readable.


static func fingerprint(hero_type: String) -> int:
	var value := 0
	for index in range(hero_type.length()):
		value = (value * 31 + hero_type.unicode_at(index)) % 1000003
	return value


static func fill(hero_type: String) -> Color:
	var code := fingerprint(hero_type)
	return Color.from_hsv(float(code % 360) / 360.0, 0.52, 0.83)


static func body(point: Vector2, radius: float, hero_type: String) -> PackedVector2Array:
	var sides := 4 + fingerprint(hero_type) % 3
	var polygon := PackedVector2Array()
	for index in range(sides):
		var angle := -PI / 2.0 + TAU * float(index) / float(sides)
		polygon.append(point + Vector2(cos(angle), sin(angle)) * (radius + 3.0))
	return polygon
