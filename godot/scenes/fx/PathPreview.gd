# PathPreview.gd — port 1:1 `_render.PathPreview` (`_render.py:1275-1370`).
#
# Panah merah beranimasi di sepanjang jalur lane selama 2 detik (120 frame)
# tiap wave dimulai. Di pygame: dibuat `EffectManager.__init__` (`:623`),
# di-update `EffectManager.update` (`:784`), digambar PALING AWAL di
# `EffectManager.draw` (`:789`), dipicu `Game._spawn_wave` dengan
# `[top, mid, bot]` dari `map_renderer.get_lane_path` (`_core.py:1756-1762`).
# Di Godot: node dibuat `Main._ready`, dipicu `Main._on_wave_started` dengan
# `ArenaMap.get_lane_path` (port PathGenerator yang sama).
#
# Semua angka di bawah berasal dari teks sumber pygame dan di-PIN oleh
# `tools/test_render_parity.py` (pola regex hilang = tool gagal). Geometri
# panah direplay dari jejak `pygame.draw.polygon` + `Surface.blit` SUNGGUHAN
# di fixture `render_fx.json`, termasuk trik `// 2` (floor) dan `int()`
# (trunc) pygame pada titik segitiganya.
extends Node2D

## `self.duration = 120  # 2 detik` (`_render.py:1281`).
const DURATION := 120
## `if self.timer > self.duration - 20` — fade in 20 frame (`:1300`).
const FADE_IN := 20
## `elif self.timer < 40` — fade out 40 frame (`:1303`).
const FADE_OUT := 40
## `alpha = int(200 * alpha_ratio)` (`:1307`).
const BASE_ALPHA := 200
## `offset = int(animation_time * 2) % 20` (`:1311`).
const OFFSET_SPEED := 2
const OFFSET_MOD := 20
## `for i in range(0, len(lane_path) - 1, 8)` (`:1317`).
const ARROW_STEP := 8
## `if i + 4 < len(lane_path)` (`:1322`).
const DIR_AHEAD := 4
## `pulse_i = (i // 8 + offset // 5) % 4` (`:1331`).
const PULSE_SHIFT := 5
const PULSE_CYCLE := 4
## `(255, 100, 100, alpha)` / `alpha // 2`, ukuran 8 vs 5 (`:1333-1339`).
const ARROW_COLOR: Array = [255, 100, 100]
const SIZE_PULSE := 8
const SIZE_DIM := 5
const FPS := 60.0

## `self.active` / `self.paths` / `self.timer` pygame.
var active := false
var paths: Array = []
var timer := 0
## Padanan `Game.animation_time` (frame counter 60 Hz milik match).
var frame := 0
var _accum := 0.0


func _ready() -> void:
	z_index = 790
	z_as_relative = false
	# Digambar di atas unit (z unit = y ≤ 720) tapi di BAWAH SparkLayer (800)
	# dan WorldPopups (100 relatif): urutan `EffectManager.draw` pygame
	# path_preview -> explosions -> particles -> floating texts.
	process_mode = Node.PROCESS_MODE_PAUSABLE


func _process(delta: float) -> void:
	queue_redraw()
	# pygame hanya men-update efek di STATE_GAME (`Game.update`), jadi menu
	# dan pause tidak menjalankan timer-nya.
	if GameManager.in_menu or GameManager.is_paused or get_tree().paused:
		return
	_accum += delta
	while _accum >= 1.0 / FPS:
		_accum -= 1.0 / FPS
		tick()


## `PathPreview.show` (`_render.py:1283-1287`).
func show_paths(lane_paths: Array) -> void:
	active = true
	paths = lane_paths
	timer = DURATION


## `PathPreview.update` (`_render.py:1289-1295`): SATU frame pygame.
## `frame` ikut naik saat tidak aktif karena `animation_time` pygame adalah
## counter milik Game, bukan milik path preview.
func tick() -> void:
	frame += 1
	if not active:
		return
	timer -= 1
	if timer <= 0:
		active = false
		paths = []


func _draw() -> void:
	if GameManager.in_menu:
		return
	for op in build_ops(paths, frame, timer):
		var pts := PackedVector2Array()
		for pt in op["points"]:
			pts.append(Vector2(float(pt[0]), float(pt[1])))
		draw_colored_polygon(pts, _rgba(op["color"]))


## Daftar perintah gambar (`PathPreview.draw` `_render.py:1297-1367`).
## Static supaya harness bisa mereplay jejak polygon pygame tanpa GPU.
static func build_ops(lane_paths: Array, animation_time: int,
		timer_left: int) -> Array:
	var out: Array = []
	if timer_left <= 0:
		return out
	var ratio := 1.0
	if timer_left > DURATION - FADE_IN:
		ratio = float(DURATION - timer_left) / float(FADE_IN)
	elif timer_left < FADE_OUT:
		ratio = float(timer_left) / float(FADE_OUT)
	var alpha := int(float(BASE_ALPHA) * ratio)
	if alpha <= 0:
		return out
	var dim_alpha := int(floorf(float(alpha) / 2.0))
	var offset := (int(float(animation_time) * float(OFFSET_SPEED))) % OFFSET_MOD
	var shift := int(floorf(float(offset) / float(PULSE_SHIFT)))
	for lane in lane_paths:
		var count: int = lane.size()
		if count < 2:
			continue
		var i := 0
		while i < count - 1:
			var at = lane[i]
			var px := float(at.x)
			var py := float(at.y)
			var dx := 1.0
			var dy := 0.0
			if i + DIR_AHEAD < count:
				var ahead = lane[i + DIR_AHEAD]
				dx = float(ahead.x) - px
				dy = float(ahead.y) - py
				var dist := sqrtf(dx * dx + dy * dy)
				if dist == 0.0:
					dist = 1.0
				dx /= dist
				dy /= dist
			var size := SIZE_PULSE
			var color_a := alpha
			if (int(floorf(float(i) / float(ARROW_STEP))) + shift) \
					% PULSE_CYCLE != 0:
				size = SIZE_DIM
				color_a = dim_alpha
			var angle := atan2(dy, dx)
			var cos_a := cos(angle)
			var sin_a := sin(angle)
			var ox := float(int(px))
			var oy := float(int(py))
			# Setengah panah memakai FLOOR pygame (`// 2`). Empat suku ini
			# TIDAK boleh disederhanakan jadi `-floor(x)` : pygame menulis
			# `- cos_a*S//2 - sin_a*S//2` = floor(-cos*S/2) − floor(sin*S/2),
			# dan `−floor(x)` beda 1 dengan `floor(−x)` untuk x non-bulat.
			var neg_cos_half := floorf((-cos_a * float(size)) / 2.0)
			var neg_sin_half := floorf((-sin_a * float(size)) / 2.0)
			var pos_cos_half := floorf((cos_a * float(size)) / 2.0)
			var pos_sin_half := floorf((sin_a * float(size)) / 2.0)
			var points: Array = [
				[ox + float(int(cos_a * float(size))),
					oy + float(int(sin_a * float(size)))],
				[ox + float(int(neg_cos_half - pos_sin_half)),
					oy + float(int(neg_sin_half + pos_cos_half))],
				[ox + float(int(neg_cos_half + pos_sin_half)),
					oy + float(int(neg_sin_half - pos_cos_half))],
			]
			out.append({"op": "polygon", "points": points,
				"color": [int(ARROW_COLOR[0]), int(ARROW_COLOR[1]),
					int(ARROW_COLOR[2]), color_a]})
			i += ARROW_STEP
	return out


static func _rgba(c: Array) -> Color:
	return Color(float(c[0]) / 255.0, float(c[1]) / 255.0,
		float(c[2]) / 255.0, float(c[3]) / 255.0)
