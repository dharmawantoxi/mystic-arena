extends RefCounted
## Native canvas portrait: Naraka — True Boss/Cursed Warrior.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "shadow",
		"variant": 4,
		"sigil": 0,
		"crowned": false,
		"horned": false,
		"primary": Color8(48, 49, 71),
		"accent": Color8(107, 101, 150),
		"light": Color8(196, 216, 222),
		"skin": Color8(136, 130, 154),
		"top": Color8(38, 39, 59),
		"bottom": Color8(18, 21, 31)
	}
	RENDERER.paint(canvas, box, spec)
