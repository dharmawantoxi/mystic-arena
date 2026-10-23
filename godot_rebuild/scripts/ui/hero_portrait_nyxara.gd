extends RefCounted
## Native canvas portrait: Nyxara — Boss/Nether Caster.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "void",
		"variant": 2,
		"sigil": 0,
		"crowned": false,
		"horned": false,
		"primary": Color8(51, 39, 82),
		"accent": Color8(145, 85, 187),
		"light": Color8(213, 196, 243),
		"skin": Color8(144, 138, 162),
		"top": Color8(43, 36, 70),
		"bottom": Color8(16, 18, 32)
	}
	RENDERER.paint(canvas, box, spec)
