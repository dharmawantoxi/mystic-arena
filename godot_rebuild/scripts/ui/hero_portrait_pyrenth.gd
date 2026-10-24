extends RefCounted
## Native canvas portrait: Pyrenth — Boss/Demon Lord.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "neutral",
		"variant": 3,
		"sigil": 2,
		"crowned": true,
		"horned": true,
		"primary": Color8(66, 75, 86),
		"accent": Color8(142, 154, 158),
		"light": Color8(227, 231, 212),
		"skin": Color8(153, 109, 92),
		"top": Color8(54, 62, 72),
		"bottom": Color8(22, 26, 32)
	}
	RENDERER.paint(canvas, box, spec)
