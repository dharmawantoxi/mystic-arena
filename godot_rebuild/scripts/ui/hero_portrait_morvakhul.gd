extends RefCounted
## Native canvas portrait: Morvakhul — Boss/Undead Executioner.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "shadow",
		"variant": 5,
		"sigil": 0,
		"crowned": false,
		"horned": false,
		"primary": Color8(44, 45, 67),
		"accent": Color8(96, 90, 139),
		"light": Color8(196, 216, 222),
		"skin": Color8(138, 132, 156),
		"top": Color8(32, 33, 53),
		"bottom": Color8(19, 22, 32)
	}
	RENDERER.paint(canvas, box, spec)
