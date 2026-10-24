extends RefCounted
## Native canvas portrait: Vhalzun — Boss/Soul Reaper.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "reaper",
		"feature": "shadow",
		"variant": 5,
		"sigil": 1,
		"crowned": false,
		"horned": false,
		"primary": Color8(49, 50, 72),
		"accent": Color8(98, 92, 141),
		"light": Color8(196, 216, 222),
		"skin": Color8(139, 133, 157),
		"top": Color8(37, 38, 58),
		"bottom": Color8(21, 24, 34)
	}
	RENDERER.paint(canvas, box, spec)
