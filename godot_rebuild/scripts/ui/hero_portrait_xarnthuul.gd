extends RefCounted
## Native canvas portrait: Xarn'thuul — Boss/Void Sovereign.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "void",
		"variant": 2,
		"sigil": 2,
		"crowned": true,
		"horned": false,
		"primary": Color8(61, 49, 92),
		"accent": Color8(147, 87, 189),
		"light": Color8(213, 196, 243),
		"skin": Color8(137, 131, 155),
		"top": Color8(37, 30, 64),
		"bottom": Color8(16, 18, 32)
	}
	RENDERER.paint(canvas, box, spec)
