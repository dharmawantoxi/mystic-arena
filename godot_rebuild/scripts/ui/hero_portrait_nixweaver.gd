extends RefCounted
## Native canvas portrait: Nixweaver — Boss/Woodland Trickster.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "assassin",
		"feature": "nature",
		"variant": 4,
		"sigil": 7,
		"crowned": false,
		"horned": false,
		"primary": Color8(59, 97, 57),
		"accent": Color8(121, 162, 78),
		"light": Color8(215, 230, 151),
		"skin": Color8(126, 91, 82),
		"top": Color8(63, 88, 58),
		"bottom": Color8(24, 33, 28)
	}
	RENDERER.paint(canvas, box, spec)
