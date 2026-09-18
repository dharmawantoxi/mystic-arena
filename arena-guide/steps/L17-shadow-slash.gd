# L17 — bayangan dekor16 + goresan merah lane (paritas bake)
# SNIPPET: tempel di AKHIR Main.gd.
# Hook: _draw_decor17() SEBELUM _draw_decor16() (bayangan di bawah dekor).

# ═══════════════════════════════════════════
# LANGKAH 17 — bayangan dekor16 + goresan merah lane (paritas bake)
# ═══════════════════════════════════════════
func _draw17_shadow(p: Vector2, w: float) -> void:
	draw_set_transform(p + Vector2(0, 2), 0.0, Vector2(1.0, 0.42))
	draw_circle(Vector2.ZERO, w, Color(0, 0, 0, 0.45))
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

func _draw17_slashes() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 1700
	var lanes: Array = [
		_curved_path(LANE_TOP_WP, 10),
		_curved_path(LANE_MID_WP, 8),
		_curved_path(LANE_BOT_WP, 10),
	]
	for i in range(42):
		var pts: Array = lanes[rng.randi_range(0, 2)]
		var idx: int = rng.randi_range(0, pts.size() - 1)
		var a: Vector2 = pts[max(idx - 1, 0)]
		var b: Vector2 = pts[min(idx + 1, pts.size() - 1)]
		var tang: Vector2 = b - a
		var nrm := Vector2.UP
		if tang.length() > 0.01:
			nrm = Vector2(-tang.y, tang.x).normalized()
		var p: Vector2 = pts[idx] + nrm * rng.randf_range(-14.0, 14.0)
		var ang := rng.randf_range(0.0, PI)
		var d := Vector2(cos(ang), sin(ang)) * rng.randf_range(5.0, 9.0)
		draw_line(p - d, p + d, Color8(150, 25, 25), 2.0)
		draw_line(p - d * 0.5 + Vector2(2, -1), p + d * 0.5 + Vector2(2, -1), Color8(200, 50, 50), 1.0)

func _draw_decor17() -> void:
	if _decor16_cache.is_empty():
		_gen_decor16()
	for e in _decor16_cache:
		var w := 5.0
		if e[0] == "ruin":
			w = 14.0 if int(e[2]) == 1 else 12.0
		elif e[0] == "spike":
			w = 9.0
		_draw17_shadow(e[1], w)
	_draw17_slashes()
