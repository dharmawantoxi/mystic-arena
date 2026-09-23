# KitShockRing.gd — cincin ekspansi satu-pakai untuk skill smart-AI boss.
#
# Pengganti lapisan FX heroes/<boss>_fx pygame (notify_skill_cast /
# notify_skill_impact) di port Godot: dipasang Boss.gd.kit_fx_cast /
# kit_fx_impact pada POSISI + RADIUS yang sama dengan panggilan pygame.
# Ini aproksimasi visual (draw_arc dua lapis + pudar), bukan salinan piksel
# renderer pygame — audit visual per-boss dicatat terbuka di
# docs/AUDIT_ULANG_DARI_AWAL.md. CPU-only (aman GLES/Android), tanpa partikel.
extends Node2D

var _color: Color = Color.WHITE
var _radius: float = 60.0
var _t: float = 0.0
const _DURATION := 0.42

func setup(center: Vector2, r: float, col: Color) -> void:
	global_position = center
	_radius = maxf(4.0, r)
	_color = col
	z_index = 50
	z_as_relative = false

func _process(delta: float) -> void:
	_t += delta
	if _t >= _DURATION:
		queue_free()

func _draw() -> void:
	var k := _t / _DURATION
	var ease_k := 1.0 - pow(1.0 - k, 2.0)
	var r := _radius * (0.35 + 0.65 * ease_k)
	var a := (1.0 - k) * 0.8
	draw_arc(Vector2.ZERO, r, 0.0, TAU, 40,
		Color(_color.r, _color.g, _color.b, a), 3.0)
	draw_arc(Vector2.ZERO, r * 0.72, 0.0, TAU, 32,
		Color(_color.r, _color.g, _color.b, a * 0.5), 2.0)
