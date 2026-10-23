extends RefCounted
## Native canvas portrait: Nyxthrael — Boss/Cursed Executioner.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "shadow",
		"variant": 4,
		"sigil": 0,
		"crowned": false,
		"horned": false,
		"primary": Color8(44, 45, 67),
		"accent": Color8(105, 99, 148),
		"light": Color8(196, 216, 222),
		"skin": Color8(141, 135, 159),
		"top": Color8(40, 41, 61),
		"bottom": Color8(16, 17, 27)
	}
	RENDERER.paint(canvas, box, spec)
