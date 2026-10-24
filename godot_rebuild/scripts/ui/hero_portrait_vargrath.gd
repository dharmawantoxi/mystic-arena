extends RefCounted
## Native canvas portrait: Vargrath — Boss/Demon Warlord.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "neutral",
		"variant": 3,
		"sigil": 6,
		"crowned": true,
		"horned": true,
		"primary": Color8(79, 88, 99),
		"accent": Color8(144, 156, 160),
		"light": Color8(227, 231, 212),
		"skin": Color8(153, 109, 92),
		"top": Color8(56, 64, 74),
		"bottom": Color8(27, 31, 37)
	}
	RENDERER.paint(canvas, box, spec)
