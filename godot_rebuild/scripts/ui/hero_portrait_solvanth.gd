extends RefCounted
## Native canvas portrait: Solvanth — Boss/Radiant Centaur.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "rider",
		"feature": "holy",
		"variant": 0,
		"sigil": 1,
		"crowned": false,
		"horned": false,
		"primary": Color8(145, 113, 51),
		"accent": Color8(221, 182, 83),
		"light": Color8(255, 244, 190),
		"skin": Color8(214, 183, 156),
		"top": Color8(104, 84, 50),
		"bottom": Color8(31, 28, 27)
	}
	RENDERER.paint(canvas, box, spec)
