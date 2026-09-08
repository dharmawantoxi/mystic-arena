# ComboCounter.gd — port 1:1 _render.ComboCounter pygame (kill combo tracker).
#
# Mesin state FRAME @60fps, persis pygame (max_timer 120 frame = 2 detik):
#   add_kill() : count+1, timer reset 120, target_scale 1.3, flash 20,
#   update()   : satu frame pygame — countdown timer -> expiry
#                (count pindah ke last_combo), animasi display_scale,
#                countdown color_flash.
#
# Siapa yang menjalankan: GameManager._tick_combo(delta) mengakumulasi delta
# ke kadens 60Hz lalu memanggil update() — paritas EffectManager.update()
# pygame yang dipanggil sekali per Game.update. Harness replay
# (MatchScoringParityTest) memanggil update() langsung per frame script.
#
# add_kill dipanggil GameManager.register_minion_death untuk kematian minion
# RED — dan Game.max_combo pygame membaca count SEBELUM add_kill
# (_core.py:2209-2214): rantai N kill menghasilkan max_combo N-1. Quirk ini
# dikunci fixture match_scoring.
#
# draw() pygame (label ambang, warna, bar jam pasir 80x4 kanan atas) adalah
# VISUAL — komposit pikselnya tidak diaudit screenshot, tapi pemetaan
# label/warna/lebar bar direplay dari data draw pygame asli lewat helper
# static di bawah + HudLayout (kanon geometri).
class_name ComboCounter
extends RefCounted

## 2 detik reset (pygame: max_timer = 120 frame).
const MAX_TIMER := 120
## Lebar penuh bar jam pasir (pygame: timer_w = 80).
const BAR_WIDTH := 80
## Durasi flash warna putih saat kill (pygame: color_flash = 20).
const FLASH_FRAMES := 20

var count: int = 0
var timer: int = 0
var display_scale: float = 0.0
var target_scale: float = 1.0
var color_flash: int = 0
var last_combo: int = 0


func reset() -> void:
	count = 0
	timer = 0
	display_scale = 0.0
	target_scale = 1.0
	color_flash = 0
	last_combo = 0


## Paritas ComboCounter.add_kill. (Notifikasi tier ke panel kanan via
## mobile.sidepanel pygame TIDAK diport — Godot tidak punya sidepanel;
## label tier tetap tampil di badge combo untuk count >= 5.)
func add_kill() -> void:
	count += 1
	timer = MAX_TIMER
	target_scale = 1.3
	color_flash = FLASH_FRAMES


## Paritas ComboCounter.update — SATU frame pygame (60 fps).
func update() -> void:
	# Timer countdown
	if timer > 0:
		timer -= 1
		if timer <= 0:
			# Combo expired
			last_combo = count
			count = 0

	# Scale animation
	if count > 0:
		if display_scale < target_scale:
			display_scale += (target_scale - display_scale) * 0.3
		else:
			target_scale = 1.0
			display_scale += (1.0 - display_scale) * 0.15
	else:
		display_scale *= 0.85
		if display_scale < 0.05:
			display_scale = 0.0

	# Color flash
	if color_flash > 0:
		color_flash -= 1


# ══════════════════════════════════════════════════════════
#  DATA DRAW (dipakai ComboBadge; dikunci fixture match_scoring)
# ══════════════════════════════════════════════════════════

## Paritas teks hitungan: f"x{count}".
static func count_text(n: int) -> String:
	return "x%d" % n


## Paritas draw gate: counter hanya digambar saat count >= 2 ATAU sisa
## animasi scale masih terlihat (pygame: early-return keduanya nol).
static func is_drawn(n: int, scale: float) -> bool:
	return not (n < 2 and scale < 0.1)


## Label ambang (ComboCounter.draw): hanya digambar untuk count >= 5,
## tapi pemetaan count -> label berlaku untuk semua nilai.
static func tier_label(n: int) -> String:
	if n >= 20:
		return "GODLIKE!"
	if n >= 15:
		return "UNSTOPPABLE!"
	if n >= 10:
		return "RAMPAGE!"
	if n >= 5:
		return "KILLING SPREE!"
	return "COMBO"


## Warna dasar ambang dalam komponen 0..255 (tuple pygame apa adanya —
## dibandingkan fixture TANPA round-trip float Color).
static func tier_color_rgb(n: int) -> Vector3i:
	if n >= 20:
		return Vector3i(255, 50, 50)
	if n >= 15:
		return Vector3i(255, 100, 50)
	if n >= 10:
		return Vector3i(255, 200, 50)
	if n >= 5:
		return Vector3i(100, 255, 100)
	return Vector3i(255, 255, 255)


## Paritas pulsa putih saat kill: int(c + (255 - c) * flash/20) per kanal
## (masih di ruang 0..255 — konversi ke Color hanya untuk menggambar).
static func flash_color_rgb(base: Vector3i, flash_frames: int) -> Vector3i:
	if flash_frames <= 0:
		return base
	var ratio := float(flash_frames) / float(FLASH_FRAMES)
	return Vector3i(
		int(float(base.x) + (255 - float(base.x)) * ratio),
		int(float(base.y) + (255 - float(base.y)) * ratio),
		int(float(base.z) + (255 - float(base.z)) * ratio))


## Warna tampil (dasar + pulsa flash) dalam 0..255 — bentuk yang direplay.
static func display_color_rgb(n: int, flash_frames: int) -> Vector3i:
	return flash_color_rgb(tier_color_rgb(n), flash_frames)


## Versi Color (0..1) untuk menggambar — nilai visual.
static func display_color(n: int, flash_frames: int) -> Color:
	var c := display_color_rgb(n, flash_frames)
	return Color(c.x / 255.0, c.y / 255.0, c.z / 255.0)


## Paritas lebar isi bar jam pasir: int(80 * (timer/max_timer)) —
## rasio dibagi DULU seperti pygame, baru dikalikan lebar.
static func bar_fill_width(frames_left: int) -> int:
	return int(float(BAR_WIDTH) * (float(frames_left) / float(MAX_TIMER)))
