# SparkLayer.gd — view world-space untuk `GameManager.spark_fx`
# (port sisi gambar `EffectManager.draw` `_render.py:788-796`).
#
# Datanya (partikel + ledakan + batas 500/80) ada di `SparkField` dan
# di-tick `GameManager` — sama seperti `WorldPopups` yang hanya membaca
# `GameManager.world_popups`. Node ini tidak punya state sendiri, jadi
# harness bisa menguji mesinnya tanpa scene.
#
# z_index 800: pygame menggambar effects SETELAH semua entitas
# (`_core.py:2917`), sedangkan z unit = `int(global_position.y)` (maks 720).
# Raster `draw_circle` vs sprite hasil `transform.scale` pygame TIDAK
# diklaim identik; geometri/warna/urutan dikunci RenderFxParityTest.
extends Node2D


func _ready() -> void:
	z_index = 800
	z_as_relative = false
	# Tetap redraw saat pause: pygame tetap meng-blit dunia (termasuk efek)
	# saat STATE_PAUSE, hanya update-nya yang berhenti.
	process_mode = Node.PROCESS_MODE_ALWAYS


func _process(_delta: float) -> void:
	queue_redraw()


func _draw() -> void:
	if GameManager.in_menu:
		return
	for op in GameManager.spark_fx.build_ops():
		if str(op["op"]) == "circle":
			draw_circle(Vector2(float(op["x"]), float(op["y"])),
				float(op["r"]), _rgba(op["color"]))


static func _rgba(c: Array) -> Color:
	return Color(float(c[0]) / 255.0, float(c[1]) / 255.0,
		float(c[2]) / 255.0, float(c[3]) / 255.0)
