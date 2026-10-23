extends RefCounted
## Native canvas portrait: Morvyssk — Boss/Purple Ooze.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "elemental",
		"feature": "venom",
		"variant": 4,
		"sigil": 6,
		"crowned": false,
		"horned": false,
		"primary": Color8(69, 90, 45),
		"accent": Color8(150, 189, 73),
		"light": Color8(218, 238, 143),
		"skin": Color8(214, 183, 156),
		"top": Color8(53, 68, 39),
		"bottom": Color8(25, 31, 26)
	}
	RENDERER.paint(canvas, box, spec)
