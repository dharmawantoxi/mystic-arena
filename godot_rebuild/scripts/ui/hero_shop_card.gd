extends Button
## Shared Hero Shop card. Both the in-match shop and the permanent main-menu
## shop build rows through this script so portrait dispatch lives in one place.
## The card deliberately stays a Button: scene suites locate rows by
## tooltip_text and still read `.text` and `.disabled` from the same node.

const UI_THEME = preload("res://scripts/ui/rebuild_theme.gd")
const HeroPortrait = preload("res://scripts/ui/hero_portrait.gd")

const CARD_WIDTH := 485.0
const CARD_HEIGHT := 92.0
const PORTRAIT_SIZE := 72.0
const PORTRAIT_INSET := 12.0

var _portrait: Control


func _init() -> void:
	custom_minimum_size = Vector2(CARD_WIDTH, CARD_HEIGHT)
	alignment = HORIZONTAL_ALIGNMENT_LEFT
	clip_text = true
	_apply_styleboxes()


func _ready() -> void:
	_ensure_portrait()


func setup(
	id: String,
	card_text: String,
	disabled_value: bool,
	width: float = CARD_WIDTH,
	definition: Variant = null
) -> void:
	text = card_text
	tooltip_text = id
	disabled = disabled_value
	custom_minimum_size = Vector2(width, CARD_HEIGHT)
	_ensure_portrait()
	_portrait.setup(id, definition, PORTRAIT_SIZE)


func get_portrait() -> Control:
	_ensure_portrait()
	return _portrait


func _ensure_portrait() -> void:
	if _portrait != null and is_instance_valid(_portrait):
		return
	_portrait = HeroPortrait.new()
	_portrait.name = "Portrait"
	# The portrait must never swallow the row click.
	_portrait.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_portrait.size = Vector2(PORTRAIT_SIZE, PORTRAIT_SIZE)
	_portrait.position = Vector2(PORTRAIT_INSET, (CARD_HEIGHT - PORTRAIT_SIZE) * 0.5)
	add_child(_portrait)


func _apply_styleboxes() -> void:
	add_theme_stylebox_override("normal", _card_box(Color("162d34"), Color("36514f"), 1))
	add_theme_stylebox_override("hover", _card_box(Color("25433f"), UI_THEME.TEAL, 1))
	add_theme_stylebox_override("pressed", _card_box(Color("102823"), UI_THEME.GOLD, 1))
	add_theme_stylebox_override("disabled", _card_box(Color("141c22"), Color("2a333a"), 1))
	add_theme_stylebox_override("focus", _card_box(Color(0, 0, 0, 0), UI_THEME.GOLD, 2))


func _card_box(fill: Color, edge: Color, width: int) -> StyleBoxFlat:
	var box := UI_THEME.panel(fill, edge)
	# Leave room for the portrait: Button text draws inside the content margin.
	box.content_margin_left = PORTRAIT_SIZE + PORTRAIT_INSET * 2.0
	box.content_margin_right = 18.0
	box.set_border_width_all(width)
	return box
