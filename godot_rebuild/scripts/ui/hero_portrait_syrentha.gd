extends RefCounted
## Native canvas portrait: Syrentha — Boss/Naga Siren.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "serpent",
		"feature": "neutral",
		"variant": 4,
		"sigil": 1,
		"crowned": false,
		"horned": false,
		"primary": Color8(71, 80, 91),
		"accent": Color8(138, 150, 154),
		"light": Color8(227, 231, 212),
		"skin": Color8(101, 110, 121),
		"top": Color8(54, 62, 72),
		"bottom": Color8(23, 27, 33)
	}
	RENDERER.paint(canvas, box, spec)
