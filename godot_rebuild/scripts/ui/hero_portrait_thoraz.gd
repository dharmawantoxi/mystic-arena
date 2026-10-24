extends RefCounted
## Native canvas portrait: Thoraz — Boss/Fighter-Charger.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "fighter",
		"feature": "neutral",
		"variant": 5,
		"sigil": 5,
		"crowned": false,
		"horned": false,
		"primary": Color8(79, 88, 99),
		"accent": Color8(143, 155, 159),
		"light": Color8(227, 231, 212),
		"skin": Color8(153, 109, 92),
		"top": Color8(54, 62, 72),
		"bottom": Color8(25, 29, 35)
	}
	RENDERER.paint(canvas, box, spec)
