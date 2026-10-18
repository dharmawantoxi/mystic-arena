extends RefCounted
## Layer 9bh: the ambient tint at the end of `_render.py::MapRenderer.draw()` as a
## pure op list.
##
## Every theme of `map_components/_bundle.py` carries an `ambient_tint` `(r, g, b,
## a)` (forest: none). `ops()` returns the single op the source draws over the whole
## map, under the units:
##   fill {rect, color, mult, blend}.
## With `Quality.cheap_alpha` (the PC default) the source blits a screen-sized SRCALPHA
## surface filled with the tint (`blend` 0, colour RGBA as is). Without it the screen is
## multiplied by `255 - (255 - c) * a / 255` per channel (`BLEND_RGB_MULT`, blend 3).
## An unknown theme falls back to forest, so it draws nothing. `TINTS` is checked
## against the source by `map_tint_draw_source_oracle.py` (fixture `tints`), the
## validator and `map_tint_draw_checks.gd`.

const BLEND_NORMAL := 0
const BLEND_RGB_MULT := 3
const TINTS := {
	"forest": null,
	"desert": [255, 220, 150, 15],
	"ice": [150, 200, 255, 20],
	"volcanic": [255, 100, 40, 20],
	"haunted": [24, 42, 44, 12],
	"ocean": [30, 70, 120, 15],
	"abyss": [40, 10, 10, 20],
	"nethervenom": [25, 45, 15, 22],
	"soulforged": [18, 32, 42, 22],
	"radiant": [50, 32, 8, 20],
	"abyssal": [15, 40, 55, 22],
	"eldritch": [10, 45, 55, 22],
	"sanctum": [40, 45, 60, 20],
	"eternalflame": [60, 30, 15, 20],
	"primordial": [30, 60, 30, 20],
	"celestialpeaks": [120, 95, 60, 20],
	"cosmic": [35, 15, 70, 20],
	"royal": [90, 60, 20, 20],
	"violet": [45, 15, 90, 20],
	"crimson": [30, 5, 12, 20],
	"spectral": [5, 25, 30, 20],
	"sundered": [40, 18, 6, 20],
	"empyrean": [60, 45, 15, 20],
	"solaris": [70, 45, 10, 20],
	"abysstide": [8, 35, 35, 20],
	"crimsonmatriarch": [40, 8, 12, 20],
	"astral": [12, 20, 50, 20],
	"shadowchain": [30, 10, 45, 20],
	"frostveil": [15, 30, 60, 20],
	"warshade": [8, 25, 30, 20],
	"outlaw": [50, 30, 25, 20],
	"hexbound": [40, 20, 60, 20],
	"voidbound": [35, 15, 60, 20],
	"earthborn": [35, 45, 20, 20],
	"heartbane": [45, 15, 45, 20],
	"sunfist": [70, 45, 10, 20],
	"voidwing": [35, 12, 55, 20],
	"crimsondevourer": [45, 8, 12, 20],
	"elementweave": [40, 25, 60, 20],
	"tempest": [20, 35, 80, 20],
	"sawmill": [60, 40, 15, 20],
	"croweye": [45, 10, 16, 20],
	"crystalstorm": [25, 40, 75, 20],
	"eternalwarlord": [55, 12, 16, 20],
	"explosiveart": [55, 15, 15, 20],
	"sandshadow": [75, 30, 20, 20],
	"emberweaver": [85, 25, 20, 20],
	"skyfury": [60, 40, 20, 20],
	"moonreaper": [45, 30, 80, 25],
	"moonfang": [65, 60, 95, 22],
	"emberlion": [80, 40, 15, 22],
	"lunarherald": [35, 50, 80, 22],
	"moonborn": [70, 60, 90, 20],
	"hollowbane": [70, 45, 25, 20],
}


## The tint of `theme_name` as RGBA, or null when the theme has none.
static func tint_for(theme_name: String) -> Variant:
	return TINTS.get(theme_name, null)


## One frame of the tint step for a theme on a `screen`-sized map.
static func ops(
	theme_name: String, screen: Vector2i = Vector2i(1280, 720), cheap_alpha: bool = true
) -> Array:
	var tint: Variant = tint_for(theme_name)
	if not (tint is Array):
		return []
	var rect: Array = [0, 0, screen.x, screen.y]
	if cheap_alpha:
		var color: Array = [int(tint[0]), int(tint[1]), int(tint[2]), int(tint[3])]
		return [{"kind": "fill", "rect": rect, "color": color, "mult": 255, "blend": BLEND_NORMAL}]
	var strength: float = float(tint[3]) / 255.0
	var multiplier: Array = [
		int(255.0 - (255.0 - float(tint[0])) * strength),
		int(255.0 - (255.0 - float(tint[1])) * strength),
		int(255.0 - (255.0 - float(tint[2])) * strength),
		255,
	]
	return [
		{"kind": "fill", "rect": rect, "color": multiplier, "mult": 255, "blend": BLEND_RGB_MULT}
	]
