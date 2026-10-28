extends RefCounted
## Layer 9bv17: `_render.py::_STYLE_FONT_MAP` as a native font lookup.
##
## Every text op emitted by the source-derived UI layouts carries a `style`
## (`title`, `body`, `body_medium`, `body_semibold`, `body_bold`). `_render.py`
## resolves it to one of the five bundled TTFs via `_font_path(style)`, falling
## back to `Barlow-Regular.ttf` for an unknown style. The rebuild used to own
## only Regular / SemiBold / Cinzel and drew EVERY op with Barlow-SemiBold,
## so gold HUD digits, combo counts and crit labels lost their source weight.
## The two missing TTFs are now byte copies of the source assets and this
## stateless lookup lets painters pick the same family for the same style.

const REGULAR = preload("res://assets/fonts/Barlow-Regular.ttf")
const MEDIUM = preload("res://assets/fonts/Barlow-Medium.ttf")
const SEMI_BOLD = preload("res://assets/fonts/Barlow-SemiBold.ttf")
const BOLD = preload("res://assets/fonts/Barlow-Bold.ttf")
const TITLE = preload("res://assets/fonts/Cinzel.ttf")

## Pinned by `tests/source_fonts_source_oracle.py` against `_render.py`.
const STYLE_FILES := {
	"title": "Cinzel.ttf",
	"body": "Barlow-Regular.ttf",
	"body_medium": "Barlow-Medium.ttf",
	"body_semibold": "Barlow-SemiBold.ttf",
	"body_bold": "Barlow-Bold.ttf",
}
const DEFAULT_FILE := "Barlow-Regular.ttf"


static func has_style(style: String) -> bool:
	return STYLE_FILES.has(style)


## `_font_path` uses `_STYLE_FONT_MAP.get(style, "Barlow-Regular.ttf")`.
static func file_for_style(style: String) -> String:
	return String(STYLE_FILES.get(style, DEFAULT_FILE))


## The font resource for `style`; unknown styles get the source default.
static func for_style(style: String) -> Font:
	match style:
		"title":
			return TITLE
		"body_medium":
			return MEDIUM
		"body_semibold":
			return SEMI_BOLD
		"body_bold":
			return BOLD
		_:
			return REGULAR
