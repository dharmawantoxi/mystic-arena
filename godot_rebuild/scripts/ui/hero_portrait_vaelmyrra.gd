extends RefCounted
## Native canvas portrait: Vaelmyrra — True Boss/Obsidian Warlord.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "neutral",
		"variant": 5,
		"sigil": 3,
		"crowned": true,
		"horned": false,
		"primary": Color8(76, 85, 96),
		"accent": Color8(142, 154, 158),
		"light": Color8(227, 231, 212),
		"skin": Color8(207, 168, 142),
		"top": Color8(60, 68, 78),
		"bottom": Color8(22, 26, 32)
	}
	RENDERER.paint(canvas, box, spec)
