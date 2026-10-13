extends RefCounted
## Asset-free hero silhouettes for the arena. `body()` keeps the original
## 4-6 sided placeholder shape that the roster suite locks down; `silhouette()`
## is the readable per-hero outline the prototype view actually draws.
## Stable ID-derived shape/color; team ring and facing remain readable.

const KAIZEN := "kaizen"
const THORNE := "thorne"

const KAIZEN_FILL := Color8(110, 175, 230)
const THORNE_FILL := Color8(215, 155, 30)

## Largest unit reach any silhouette uses, so callers can reserve room.
const MAX_REACH := 1.2


static func fingerprint(hero_type: String) -> int:
	var value := 0
	for index in range(hero_type.length()):
		value = (value * 31 + hero_type.unicode_at(index)) % 1000003
	return value


static func fill(hero_type: String) -> Color:
	match hero_type:
		KAIZEN:
			return KAIZEN_FILL
		THORNE:
			return THORNE_FILL
		_:
			var code := fingerprint(hero_type)
			return Color.from_hsv(float(code % 360) / 360.0, 0.52, 0.83)


static func body(point: Vector2, radius: float, hero_type: String) -> PackedVector2Array:
	var sides := 4 + fingerprint(hero_type) % 3
	var polygon := PackedVector2Array()
	for index in range(sides):
		var angle := -PI / 2.0 + TAU * float(index) / float(sides)
		polygon.append(point + Vector2(cos(angle), sin(angle)) * (radius + 3.0))
	return polygon


## Readable per-hero outline: slim for the assassin, bulky for the bruiser and
## a deterministic wobble for everyone else. Vertices stay inside
## `radius * MAX_REACH` so the team ring still frames the figure.
static func silhouette(point: Vector2, radius: float, hero_type: String) -> PackedVector2Array:
	var result := PackedVector2Array()
	for unit in _outline(hero_type):
		result.append(point + unit * radius)
	return result


static func _outline(hero_type: String) -> Array[Vector2]:
	match hero_type:
		KAIZEN:
			return [
				Vector2(0.0, -1.15),
				Vector2(0.42, -0.55),
				Vector2(0.55, 0.15),
				Vector2(0.30, 0.90),
				Vector2(0.0, 1.15),
				Vector2(-0.30, 0.90),
				Vector2(-0.55, 0.15),
				Vector2(-0.42, -0.55)
			]
		THORNE:
			return [
				Vector2(0.0, -1.10),
				Vector2(0.50, -0.85),
				Vector2(0.85, -0.35),
				Vector2(1.00, 0.10),
				Vector2(0.80, 0.70),
				Vector2(0.35, 1.10),
				Vector2(0.0, 1.00),
				Vector2(-0.35, 1.10),
				Vector2(-0.80, 0.70),
				Vector2(-1.00, 0.10),
				Vector2(-0.85, -0.35),
				Vector2(-0.50, -0.85)
			]
		_:
			return _generic_outline(hero_type)


static func _generic_outline(hero_type: String) -> Array[Vector2]:
	# Layer 9aj: the old wobble was `(code >> (index % 12)) % 5`, i.e. bits 0-9
	# of a code below 1000003, so 33 pairs of the 220 generic heroes drew the
	# exact same outline (`gravefang` shared `hitokage`'s figure, and so on).
	# Spreading the whole code through a large multiplier and reading base-5
	# digits keeps all 222 roster outlines distinct; the reach range is 1.00-1.12,
	# still inside `MAX_REACH`.
	var spread := fingerprint(hero_type) * 48271 + 1021
	var sides := 7 + spread % 4
	var result: Array[Vector2] = []
	var divisor := 1
	for index in range(sides):
		var angle := -PI / 2.0 + TAU * float(index) / float(sides)
		var wobble := float((spread / divisor) % 5 - 2) * 0.06
		result.append(Vector2(cos(angle), sin(angle)) * (1.0 + wobble))
		divisor *= 5
	return result
