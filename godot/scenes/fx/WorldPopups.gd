# WorldPopups — view world-space untuk antrean FloatingTextQueue.
# Reward + data gerak/lifetime diuji headless; raster font, shadow, glow
# dan komposit terhadap cinematic BELUM diuji piksel-per-piksel.
extends Node2D

const MEDIUM_FONT = preload("res://assets/fonts/Barlow-SemiBold.ttf")
const CRITICAL_FONT = preload("res://assets/fonts/Barlow-Bold.ttf")
## Setengah lebar maksimal teks popup (lebar "+123456G" di size 18 + ascent).
## Dipakai ambang culling, sama seperti pygame memberi radius 10 untuk
## proyektil hero (`_core.py:2899`).
const POPUP_RADIUS := 24.0


func _ready() -> void:
	z_index = 100
	# Tetap redraw saat pause agar reset/akhir antrean tak meninggalkan
	# gambar lama. Mesin datanya HANYA di-tick GameManager, bukan view.
	process_mode = Node.PROCESS_MODE_ALWAYS


func _process(_delta: float) -> void:
	queue_redraw()


func _draw() -> void:
	if GameManager.in_menu:
		return
	# ── FRUSTUM CULLER (port `_system.FrustumCuller`, _system.py:40-50) ──
	# pygame melewatkan blit entitas di luar layar; di Godot CanvasItem sudah
	# di-cull GPU, jadi yang benar-benar dihemat adalah draw_string yang
	# dibangun manual tiap frame (2 call per popup: bayangan + teks).
	# Entri diuji di RUANG LAYAR lewat transform canvas + global, karena
	# Godot punya camera (pygame: world == screen selalu).
	var vp := get_viewport()
	var xform := Transform2D()
	var screen := Vector2(1280.0, 720.0)
	if vp != null:
		xform = vp.get_canvas_transform() * get_global_transform()
		screen = vp.get_visible_rect().size
	for t in GameManager.world_popups.floating_texts:
		var alpha := mini(255, int(255.0 * minf(1.0,
			float(t["lifetime"]) / (float(t["max_lifetime"]) * 0.5))))
		if alpha <= 0:
			continue
		var at := Vector2(int(t["x"]), int(t["y"]))
		if not FrustumCuller.is_visible_world(at, xform, screen, POPUP_RADIUS):
			continue
		var font: Font = CRITICAL_FONT if bool(t["critical"]) else MEDIUM_FONT
		var size := clampi(int(float(t["font_size"]) * float(t["scale"])), 8, 64)
		var text := str(t["text"])
		var extent := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, size)
		at += Vector2(-extent.x * 0.5, (font.get_ascent(size) - font.get_descent(size)) * 0.5)
		var rgb: Array = t["color"]
		var color := Color(float(rgb[0]) / 255.0, float(rgb[1]) / 255.0,
			float(rgb[2]) / 255.0, alpha / 255.0)
		draw_string(font, at + Vector2(1, 2), text, HORIZONTAL_ALIGNMENT_LEFT,
			-1, size, Color(8.0 / 255.0, 8.0 / 255.0, 14.0 / 255.0,
			minf(220, alpha) / 255.0))
		draw_string(font, at, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, color)
