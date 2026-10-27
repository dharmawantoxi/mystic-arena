extends RefCounted
## Native canvas portrait: Raz — The Heat of Despair, Boss/Fire Monk.
## Uses the source Fire Monk palette and the shared fighter/fire portrait composition.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func spec() -> Dictionary:
	return {
		"family": "fighter",
		"feature": "fire",
		"variant": 5,
		"sigil": 2,
		"crowned": false,
		"horned": false,
		"primary": Color8(55, 8, 12),
		"accent": Color8(230, 90, 20),
		"light": Color8(255, 220, 120),
		"skin": Color8(155, 95, 60),
		"top": Color8(185, 35, 40),
		"bottom": Color8(18, 12, 10),
		"hair": Color8(55, 42, 48),
		"gold": Color8(185, 138, 55)
	}


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var portrait := spec()
	RENDERER.paint(canvas, box, portrait)
	var unit := box.size.x / 96.0
	var hair: Color = portrait["hair"]
	var gold: Color = portrait["gold"]
	canvas.draw_line(_p(box, 39.0, 24.0), _p(box, 44.0, 22.0), hair, maxf(1.4 * unit, 1.0), true)
	canvas.draw_line(_p(box, 49.0, 22.0), _p(box, 54.0, 24.0), hair, maxf(1.4 * unit, 1.0), true)
	canvas.draw_line(_p(box, 43.0, 66.0), _p(box, 51.0, 66.0), gold, maxf(1.5 * unit, 1.0), true)


static func _p(box: Rect2, x: float, y: float) -> Vector2:
	return box.position + Vector2(x, y) * box.size.x / 96.0
