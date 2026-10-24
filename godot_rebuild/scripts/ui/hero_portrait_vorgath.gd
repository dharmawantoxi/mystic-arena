extends RefCounted
## Native canvas portrait: Vorgath — Boss/Demon Warden.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "neutral",
		"variant": 0,
		"sigil": 0,
		"crowned": false,
		"horned": true,
		"primary": Color8(77, 86, 97),
		"accent": Color8(141, 153, 157),
		"light": Color8(227, 231, 212),
		"skin": Color8(190, 145, 124),
		"top": Color8(57, 65, 75),
		"bottom": Color8(23, 27, 33)
	}
	RENDERER.paint(canvas, box, spec)
