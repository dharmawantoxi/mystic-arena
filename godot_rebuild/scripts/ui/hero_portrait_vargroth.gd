extends RefCounted
## Native canvas portrait: Vargroth — Boss/Bloodmoon Werewolf.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "beast",
		"feature": "blood",
		"variant": 3,
		"sigil": 1,
		"crowned": false,
		"horned": false,
		"primary": Color8(115, 33, 47),
		"accent": Color8(196, 48, 59),
		"light": Color8(255, 194, 162),
		"skin": Color8(145, 63, 77),
		"top": Color8(89, 35, 47),
		"bottom": Color8(32, 26, 35)
	}
	RENDERER.paint(canvas, box, spec)
