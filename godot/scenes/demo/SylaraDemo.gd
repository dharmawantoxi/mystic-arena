# SylaraDemo.gd — showcase Sylara V10.5 (rig satu file, Godot 4).
#
# Sylara di scene ini = instance SylaraV105.tscn (script SylaraV105.gd,
# SATU file berisi semuanya):
#   * DYNAMIC CAMERA — Camera2D smooth-lag (speed 6), dibuat script di _ready
#   * GHOST TRAILS — bayangan aura hijau di belakang saat Windrun
#   * WINDRUN SPRINT — lari 480 px/dtk (toggle), kaki berputar 0.04 dtk
#   * SKILL — basic attack, Q Focus Fire, W Windrun (toggle),
#     E Shackle Shot (tornado), R Powershot (channel)
#   * UI MOBILE BAWAAN — joystick virtual + tombol skill + HURT/DEATH/REVIVE
#   * DUNIA — grid rumput + pohon & batu prosedural (bagian dari script)
#
# Demo ini hanya LAPISAN TIPIS di atas rig — tidak mengubah perilaku
# SylaraV105.gd, hanya menambahkan:
#   * keyboard desktop: WASD → joystick_vector (variabel publik rig yang
#     dibaca tiap physics frame); tombol panah SUDAH ditangani rig sendiri
#     lewat Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
#   * shortcut skill: SPACE attack, 1/2/3/4 Q/W/E/R, H hurt, K death,
#     L revive (padanan tombol tes kiri-atas milik rig)
#   * HUD: judul + label mode (animasi aktif) + baris statistik
#
# KAMERA demo sengaja TIDAK ada: SylaraV105 membuat Camera2D-nya sendiri.
#
# Jalankan: godot --path godot res://scenes/demo/SylaraDemo.tscn
extends Node2D

# Untyped (bukan CharacterBody2D) karena SylaraV105.gd tidak punya class_name
# — akses properti/script (joystick_vector, trigger_skill, dst.) lewat base
# CharacterBody2D akan memunculkan analyzer warning unsafe-access.
@onready var sylara = $SylaraV105
@onready var label_mode: Label = $CanvasLayer/VBox/ModeLabel
@onready var label_stats: Label = $CanvasLayer/VBox/StatsLabel

var _ui_timer := 0.0


func _process(delta: float) -> void:
	_desktop_input()
	_ui_timer += delta
	if _ui_timer >= 0.1:
		_ui_timer = 0.0
		_update_labels()


## WASD → joystick virtual rig. `joystick_vector` adalah variabel publik
## SylaraV105 yang dibaca tiap physics frame (prioritas di atas tombol
## panah ui_*), jadi cara ini identik dengan cara joystick sentuh bekerja.
func _desktop_input() -> void:
	var v := Vector2.ZERO
	if Input.is_key_pressed(KEY_A):
		v.x -= 1.0
	if Input.is_key_pressed(KEY_D):
		v.x += 1.0
	if Input.is_key_pressed(KEY_W):
		v.y -= 1.0
	if Input.is_key_pressed(KEY_S):
		v.y += 1.0
	sylara.joystick_vector = v


func _unhandled_input(event: InputEvent) -> void:
	if not (event is InputEventKey) or not event.pressed or event.echo:
		return
	match event.keycode:
		KEY_SPACE:
			sylara.trigger_skill("attack")
		KEY_1:
			sylara.trigger_skill("focus_fire")
		KEY_2:
			sylara.toggle_windrun()
		KEY_3:
			sylara.trigger_skill("shackle")
		KEY_4:
			sylara.trigger_skill("powershot")
		KEY_H:
			sylara.trigger_skill("hurt")
		KEY_K:
			sylara.trigger_skill("death")
		KEY_L:
			sylara.is_dead = false
			sylara.is_busy = false
			sylara.is_windrun = false
			sylara.set_anim("idle")


func _update_labels() -> void:
	if label_mode != null:
		var mode := "DEATH" if sylara.is_dead else str(sylara.current_anim).to_upper()
		if sylara.is_windrun and not sylara.is_dead:
			mode += " — WINDRUN %d px/s" % int(sylara.windrun_speed)
		label_mode.text = "SYLARA V10.5 // " + mode
	if label_stats != null:
		var g: int = sylara.ghost_trails.size()
		var a: int = sylara.active_arrows.size()
		var p: int = sylara.active_particles.size()
		label_stats.text = (
			"1 script, 1 _draw() | kamera smooth-lag 6.0 | ghost trail 0.04 s | " +
			"%d ghost | %d panah | %d partikel" % [g, a, p]
		)
