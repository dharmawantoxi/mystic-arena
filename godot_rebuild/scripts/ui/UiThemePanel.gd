class_name UiThemePanel
extends PanelContainer

## PanelContainer that paints the source ui_theme panel behind its children.


func _ready() -> void:
	if not has_theme_stylebox_override("panel"):
		add_theme_stylebox_override("panel", StyleBoxEmpty.new())
	resized.connect(queue_redraw)


func _draw() -> void:
	if not UiTheme.ensure_loaded() or size.x <= 0 or size.y <= 0:
		return
	var data := UiThemeComponents.panel(
		Rect2i(0, 0, int(size.x), int(size.y)),
		UiTheme.palette.get("edge_gold", []),
		UiTheme.palette.get("panel_top", []),
		UiTheme.palette.get("panel_bottom", []),
		true,
		true,
		1
	)
	UiThemeDraw.render(self, data.ops, Ui.font(), 22)
