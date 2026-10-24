extends RefCounted
## Native canvas portrait: Mor'khaera — Boss/Dark Witch.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "shadow",
		"variant": 3,
		"sigil": 4,
		"crowned": false,
		"horned": false,
		"primary": Color8(54, 55, 77),
		"accent": Color8(107, 101, 150),
		"light": Color8(196, 216, 222),
		"skin": Color8(147, 141, 165),
		"top": Color8(36, 37, 57),
		"bottom": Color8(16, 17, 27)
	}
	RENDERER.paint(canvas, box, spec)
