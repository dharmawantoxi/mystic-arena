# HUD.gd — Port ringan dari _core.py Game._draw_gold_hud + _render.WaveAnnouncer
# Di Pygame: chip emas (gold + income/s) digambar manual tiap frame.
# Di Godot: Control statis, label hanya di-update saat signal GameManager berubah.
extends Control

var _banner_tween: Tween

@onready var gold_label: Label = $TopLeft/GoldChip/GoldRow/GoldValue
@onready var income_label: Label = $TopLeft/GoldChip/GoldRow/IncomeValue
@onready var level_label: Label = $TopLeft/LevelBadge/LevelRow/LevelValue
@onready var wave_label: Label = $TopLeft/LevelBadge/LevelRow/WaveValue
@onready var wave_banner: Label = $WaveBanner

func _ready():
	wave_banner.modulate.a = 0.0
	GameManager.gold_changed.connect(_on_gold_changed)
	GameManager.wave_started.connect(_on_wave_started)
	GameManager.level_started.connect(_on_level_started)
	refresh()

# Sinkronkan seluruh HUD dari state GameManager (dipakai saat _ready + level_started)
func refresh():
	_on_gold_changed(GameManager.gold)
	level_label.text = "LEVEL %d" % GameManager.level_number
	wave_label.text = "WAVE %d" % GameManager.wave_number

func _on_gold_changed(new_gold: int):
	gold_label.text = _format_thousands(new_gold)
	income_label.text = "+%s/s" % _format_gold_rate(GameManager.gold_per_second)

func _on_level_started(_level_num: int):
	refresh()

func _on_wave_started(wave_num: int):
	wave_label.text = "WAVE %d" % wave_num
	announce_wave(wave_num)

# Banner besar "WAVE N" di tengah layar (mirip WaveAnnouncer: pop-in -> tahan -> fade out)
func announce_wave(wave_num: int):
	wave_banner.text = "WAVE %d" % wave_num
	if _banner_tween and _banner_tween.is_valid():
		_banner_tween.kill()
	wave_banner.pivot_offset = wave_banner.size / 2.0 # scale dari tengah
	wave_banner.modulate.a = 0.0
	wave_banner.scale = Vector2(0.8, 0.8)
	_banner_tween = create_tween()
	_banner_tween.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	_banner_tween.tween_property(wave_banner, "modulate:a", 1.0, 0.35)
	_banner_tween.parallel().tween_property(wave_banner, "scale", Vector2(1.0, 1.0), 0.35)
	_banner_tween.tween_interval(1.2)
	_banner_tween.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN)
	_banner_tween.tween_property(wave_banner, "modulate:a", 0.0, 0.5)

# 1234567 -> "1,234,567" (paritas f"{self.gold:,}" di pygame)
static func _format_thousands(n: int) -> String:
	var s := str(absi(n))
	var out := ""
	var count := 0
	for i in range(s.length() - 1, -1, -1):
		out = s[i] + out
		count += 1
		if count % 3 == 0 and i > 0:
			out = "," + out
	return ("-" + out) if n < 0 else out

# 3.0 -> "3", 5.7 -> "5.7", 3.75 -> "3.8" (paritas _core.format_gold_rate)
static func _format_gold_rate(rate: float) -> String:
	var s := "%.1f" % rate
	if s.ends_with(".0"):
		s = s.substr(0, s.length() - 2)
	return s
