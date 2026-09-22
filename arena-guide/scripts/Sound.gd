extends Node
## Langkah 12: suara prosedural - SFX + BGM tanpa file audio.

var streams: Dictionary = {}
var _players: Array = []
var _next_player: int = 0
var _last_play: Dictionary = {}
var muted: bool = false


func _ready() -> void:
	streams["click"] = _tone(880.0, 0.07, 0.5)
	streams["move"] = _tone(520.0, 0.08, 0.4)
	streams["build"] = _tone(220.0, 0.18, 0.5, 440.0)
	streams["error"] = _tone(160.0, 0.2, 0.5, 110.0)
	streams["shoot"] = _tone(1200.0, 0.06, 0.35, 300.0, 0.3)
	streams["hit"] = _tone(300.0, 0.05, 0.4, 150.0, 0.4)
	streams["wave"] = _tone(196.0, 0.5, 0.5, 392.0)
	streams["heal"] = _tone(440.0, 0.25, 0.4, 880.0)
	streams["buff"] = _tone(330.0, 0.3, 0.45, 660.0)
	streams["win"] = _tone(523.0, 0.4, 0.5, 1046.0)
	streams["lose"] = _tone(392.0, 0.5, 0.5, 130.0)
	for i in 6:
		var p := AudioStreamPlayer.new()
		p.volume_db = -10.0
		add_child(p)
		_players.append(p)
	var bgm := AudioStreamPlayer.new()
	bgm.stream = _make_bgm()
	bgm.volume_db = -18.0
	add_child(bgm)
	bgm.play()


func play(sname: String) -> void:
	if muted or not streams.has(sname):
		return
	var gap := 120 if (sname == "shoot" or sname == "hit") else 40
	var now := Time.get_ticks_msec()
	if int(_last_play.get(sname, 0)) + gap > now:
		return
	_last_play[sname] = now
	var p: AudioStreamPlayer = _players[_next_player]
	_next_player = (_next_player + 1) % _players.size()
	p.stream = streams[sname]
	p.play()


func toggle_mute() -> bool:
	muted = not muted
	AudioServer.set_bus_mute(0, muted)
	return muted


func _tone(freq: float, dur: float, vol: float, slide_to: float = 0.0, noise: float = 0.0) -> AudioStreamWAV:
	var rate := 22050
	var n := int(rate * dur)
	var data := PackedByteArray()
	data.resize(n)
	var phase := 0.0
	for i in n:
		var t := float(i) / rate
		var f := (freq + (slide_to - freq) * (t / dur)) if slide_to > 0.0 else freq
		phase += TAU * f / rate
		var env := 1.0 - t / dur
		env = env * env
		var s := sin(phase) * (1.0 - noise) + (randf() * 2.0 - 1.0) * noise
		data[i] = clampi(int(128 + s * env * vol * 127.0), 0, 255)
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_8_BITS
	w.mix_rate = rate
	w.data = data
	return w


func _make_bgm() -> AudioStreamWAV:
	var rate := 22050
	var dur := 6.0
	var n := int(rate * dur)
	var data := PackedByteArray()
	data.resize(n)
	for i in n:
		var t := float(i) / rate
		var trem := 0.7 + 0.3 * sin(TAU * 0.5 * t)
		var s := (sin(TAU * 110.0 * t) + sin(TAU * 165.0 * t) * 0.6 + sin(TAU * 220.0 * t) * 0.4) / 2.0
		var edge := minf(1.0, minf(t, dur - t) / 0.5)
		data[i] = clampi(int(128 + s * trem * edge * 0.25 * 127.0), 0, 255)
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_8_BITS
	w.mix_rate = rate
	w.loop_mode = AudioStreamWAV.LOOP_FORWARD
	w.loop_begin = 0
	w.loop_end = n
	w.data = data
	return w
