# ScrollIndicator.gd — indikator scroll ramping (port
# ui_theme.scroll_indicator 1:1).
#
# Track (28,32,52) lebar 6px radius 3 + thumb gradasi GOLD_BRIGHT->(196,138,40)
# dengan `thumb_h = max(18, int(height * height/(height+max_scroll)))` dan
# `thumb_y = y + int((height - thumb_h) * scroll_pos / max_scroll)`.
#
# Dua cara pakai:
#   * `follow(scroll_container)` — menempel ke ScrollContainer Godot (nilai
#     dibaca dari VScrollBar-nya, jadi tetap sinkron saat daftar digulir).
#   * `set_scroll(pos, max)` — angka mentah, seperti pemanggil pygame yang
#     menyimpan `scroll_pos`/`max_scroll` sendiri.
extends Control
class_name ScrollIndicator

var scroll_pos: float = 0.0
var max_scroll: float = 0.0
var bar_width: float = 6.0

var _bar: Range = null


func _init(p_width: float = 6.0) -> void:
	bar_width = p_width
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	custom_minimum_size = Vector2(p_width, 0)


## Tempel ke ScrollContainer (default: batang gulir vertikal).
func follow(scroll: ScrollContainer, vertical: bool = true) -> ScrollIndicator:
	if scroll == null:
		return self
	_bar = scroll.get_v_scroll_bar() if vertical else scroll.get_h_scroll_bar()
	if _bar != null:
		_bar.changed.connect(_sync)
		_bar.value_changed.connect(_on_value)
		_sync.call_deferred()
	return self


func _on_value(_v: float) -> void:
	_sync()


func _sync() -> void:
	if _bar == null:
		return
	set_scroll(_bar.value, _bar.max_value)


## Set posisi/manual (paritas pemanggil pygame).
func set_scroll(pos: float, max_pos: float) -> void:
	scroll_pos = pos
	max_scroll = max_pos
	queue_redraw()


## Rect thumb yang digambar (untuk tes/hit-test; kosong bila tak ada scroll).
func thumb_rect() -> Rect2:
	return UiTheme.scroll_thumb_rect(Vector2.ZERO, size.y, scroll_pos,
		max_scroll, bar_width)


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		queue_redraw()


func _draw() -> void:
	if size.y <= 0.0:
		return
	UiTheme.draw_scroll_indicator(self, Vector2.ZERO, size.y, scroll_pos,
		max_scroll, bar_width)
