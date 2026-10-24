extends RefCounted
## Native canvas portrait: Morvaenthir — Boss/Soul Reaper.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "reaper",
		"feature": "shadow",
		"variant": 1,
		"sigil": 2,
		"crowned": false,
		"horned": false,
		"primary": Color8(40, 41, 63),
		"accent": Color8(94, 88, 137),
		"light": Color8(196, 216, 222),
		"skin": Color8(147, 141, 165),
		"top": Color8(37, 38, 58),
		"bottom": Color8(16, 16, 26)
	}
	RENDERER.paint(canvas, box, spec)
