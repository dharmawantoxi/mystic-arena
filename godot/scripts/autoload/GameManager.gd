# GameManager.gd — Autoload, port dari _core.py Game class
# Menggantikan Game loop pygame (60 FPS) dengan Godot SceneTree
#
# Yang diport di sesi ini (sebelumnya cuma print + emit signal):
#   • EKONOMI paritas _core.py: GOLD_PER_SECOND 3 (+0.3/level), starting gold
#     base + 100/level, multiplier difficulty (easy 1.25 / normal 1.0 / hard 0.75),
#     akumulasi pecahan lewat _gold_income_milli (bukan int() per detik).
#   • STATE MATCH: "playing" / "victory" / "defeat" / "idle" — nexus hancur
#     menentukan hasil (paritas Game.update 2281-2292), wave & gold berhenti
#     saat match usai; "idle" = sedang di menu utama (in_menu).
#   • MINION_TYPES + komposisi wave dibaca dari data/economy.json (hasil convert),
#     bukan hardcode; late-wave scale mengikuti wave.
#   • gold AI (tim red) terpisah supaya AI bisa membangun/meng-upgrade menara.
#   • aura item diproses 4×/detik (paritas hero_items.update_auras).
#
# Update sesi progresi level + menu utama:
#   • PROGRESI LEVEL: is_replay + next_level() (ENTER setelah menang lanjut ke
#     level berikutnya, paritas get_next_level main.py:566-576), restart_match()
#     kini is_replay=true, return_to_menu() (paritas main.py:582-586).
#   • META REWARD paritas _grant_meta_reward (_core.py:2365-2456): menang
#     pertama meta_gold_reward_win (3000), replay 1500 sekali lalu 200
#     unlimited lewat save replay_reward_counts, kalah 0 — ditulis ke kunci
#     save "meta_gold" (bukan "gold"), di-guard _meta_reward_granted.
#   • ENEMY SCALING (paritas _core.py:1460/1476-1483): aktif hanya difficulty
#     hard; enemy_hp_mult x1.15, damage x1.10 dari levels.json — diterapkan
#     Main ke minion merah (1792-1796) dan boss (1822/2097) saat spawn.
#   • AUTO-UNLOCK HERO BOSS (paritas _auto_unlock_defeated_boss_heroes
#     _core.py:2322): boss yang dikalahkan + match menang -> hero gratis masuk
#     SaveManager.unlocked_heroes (muncul di HERO SHOP + tab HERO toko).
#   • Hook BGM per level: levels.json["bgm_track"] -> AudioManager.play_bgm.
extends Node

signal level_started(level_num: int)
signal wave_started(wave_num: int)
signal boss_spawned(boss_type: String)
signal hero_died(hero: Node)
signal gold_changed(new_gold: int)
signal minion_died(minion: Node, killer_team: String)
signal tower_destroyed(tower: Node, killer_team: String)
signal nexus_destroyed(team: String, killer_team: String)
signal nexus_upgraded(team: String, level: int)
signal game_over(victory: bool)
signal difficulty_changed(difficulty: String)
signal selection_changed
signal shop_changed
signal tower_built(tower: Node)

const FPS := 60.0

# ═══ FALLBACK MINION_TYPES — port persis dari _core.py (dipakai kalau
# data/economy.json belum di-generate; warna = GRASS/GOBLIN_COLOR dkk) ═══
const FALLBACK_MINION_TYPES: Dictionary = {
	"goblin": {"name": "Goblin", "hp": 45, "damage": 5, "speed": 1.5, "range": 25,
		"attack_cooldown": 45, "gold_reward": 8, "radius": 9, "color": "#64b450"},
	"orc": {"name": "Orc", "hp": 110, "damage": 13, "speed": 0.95, "range": 30,
		"attack_cooldown": 60, "gold_reward": 18, "radius": 12, "color": "#c8643c"},
	"troll": {"name": "Troll", "hp": 320, "damage": 18, "speed": 0.65, "range": 28,
		"attack_cooldown": 75, "gold_reward": 45, "radius": 14, "color": "#648caa",
		"armor": 2, "magic_resist": 0.05},
	"undead": {"name": "Undead", "hp": 65, "damage": 11, "speed": 0.85, "range": 100,
		"attack_cooldown": 60, "gold_reward": 16, "radius": 10, "color": "#c8c8dc",
		"armor": 0, "magic_resist": 0.15},
	"dark_rider": {"name": "Dark Rider", "hp": 280, "damage": 32, "speed": 2.0, "range": 35,
		"attack_cooldown": 50, "gold_reward": 65, "radius": 13, "color": "#643c8c",
		"armor": 1, "magic_resist": 0.05},
}

# ═══ FALLBACK NEXUS_WAVE_COMPOSITION (wave 1-5) ═══
const FALLBACK_WAVE_COMPOSITION: Dictionary = {
	1: ["goblin", "goblin", "goblin"],
	2: ["goblin", "goblin", "goblin", "orc"],
	3: ["goblin", "orc", "goblin", "orc", "undead"],
	4: ["orc", "goblin", "orc", "undead", "goblin", "goblin"],
	5: ["orc", "orc", "undead", "troll", "goblin", "goblin"],
}
## Wave > 5: pygame memakai komposisi wave 5 terus + minion_scale naik per level
const LATE_WAVE_MIX: Array = ["orc", "undead", "troll", "goblin", "dark_rider", "orc"]

# ═══ FALLBACK EKONOMI — paritas _core.py 209-229, 253 ═══
const FALLBACK_ECONOMY: Dictionary = {
	"starting_gold": 350,
	"gold_per_second": 3,
	"gold_per_second_level_bonus": 0.3,
	"gold_per_level_bonus": 100,
	"difficulty_gold_mult": {"easy": 1.25, "normal": 1.0, "hard": 0.75},
	"minion_wave_interval_frames": 1500,
}

const ECONOMY_PATH := "res://data/economy.json"

# State global (mirip _core.Game)
var level_number: int = 1
var wave_number: int = 1
var gold: int = 1000:
	set(v):
		gold = v
		gold_changed.emit(v)
var is_paused: bool = false
## "playing" | "victory" | "defeat" | "idle" — paritas Game.state; "idle" =
## sedang di menu utama (belum/tidak ada match berjalan).
var state: String = "idle"
## "easy" | "normal" | "hard"
var difficulty: String = "normal"

# ── PROGRESI LEVEL + MENU (paritas _core.py 1578-1584) ──
## True kalau level ini dimulai ULANG padahal sudah pernah ditamatkan
## (pygame: Game(screen, level_number, is_replay=True) dari main.py:576).
## Menentukan reward replay di end_match() (_core.py:2387).
var is_replay: bool = false
## True saat menu utama terbuka (boot + MAIN MENU dari pause/menang-kalah).
## _process gold/wave berhenti; pygame menjalankan menu di state terpisah.
var in_menu: bool = true
## Reward meta yang TERAKHIR diberikan (dibaca HUD; paritas Game.meta_reward_earned)
var meta_reward_earned: int = 0
## Guard anti dobel reward (paritas _meta_reward_granted _core.py:1581/2456)
var _meta_reward_granted: bool = false
## Boss (mini/true) yang dikalahkan di match INI — baru di-unlock gratis
## kalau match dimenangkan (paritas bosses_defeated_this_match _core.py:1594).
var bosses_defeated_this_match: Array = []

# ── ENEMY SCALING (Hard mode; paritas _core.py:1460 + 1476-1483) ──
## enemy_scaling_enabled = (difficulty == "hard"); multiplier HP/dmg/speed
## musuh (merah) diambil dari levels.json lalu dikali 1.15/1.10/1.0.
var enemy_scaling_enabled: bool = false
var enemy_hp_mult: float = 1.0
var enemy_damage_mult: float = 1.0
var enemy_speed_mult: float = 1.0

# Referensi node yang di-set oleh Main.tscn (lewat GameManagerConnector)
var hero_container: Node
var boss_container: Node
var minion_container: Node
var tower_container: Node
var fx_container: Node

# Nexus (Castle) per tim — diisi Nexus.gd saat _ready
var blue_nexus = null
var red_nexus = null

# Data hasil convert
var economy: Dictionary = {}
var minion_types: Dictionary = {}
var wave_composition_table: Dictionary = {}

# Config dari levels (port dari _core.NEXUS_LEVELS)
var starting_gold: int = 1000
var gold_per_second: float = 3.0

## Gold AI (tim red). pygame: AIPlayer punya saldo sendiri untuk build/upgrade.
var ai_gold: int = 0

# Gelombang minion — paritas _core.MINION_WAVE_INTERVAL = 1500 frame @60fps
@export var waves_enabled: bool = true
@export var wave_interval: float = 25.0
@export var max_minions_per_team: int = 24

var _gold_timer: float = 0.0
var _gold_income_milli: int = 0
var _ai_gold_milli: int = 0
var _wave_timer: float = 0.0
var _aura_timer: float = 0.0
var _hit_stop_active: bool = false
var _hit_stop_until_ms: int = 0


func _ready():
	# Autoload harus tetap jalan walau SceneTree di-pause (P/ESC dari Main.gd):
	# watchdog Engine.time_scale tinggal di sini. Flag is_paused sudah menahan
	# timer gold/wave, jadi "pause" tetap benar.
	process_mode = Node.PROCESS_MODE_ALWAYS
	load_economy()
	nexus_destroyed.connect(_on_nexus_destroyed)


func load_economy() -> void:
	economy = FALLBACK_ECONOMY.duplicate(true)
	if FileAccess.file_exists(ECONOMY_PATH):
		var f := FileAccess.open(ECONOMY_PATH, FileAccess.READ)
		var parsed = JSON.parse_string(f.get_as_text())
		if parsed is Dictionary:
			economy.merge(parsed, true)
	else:
		push_warning("[GameManager] economy.json belum ada — pakai fallback. "
			+ "Jalankan tools/convert_to_godot.py")
	minion_types = economy.get("minion_types", {})
	if minion_types.is_empty():
		minion_types = FALLBACK_MINION_TYPES.duplicate(true)
	wave_composition_table = economy.get("wave_composition", {})
	if wave_composition_table.is_empty():
		for k in FALLBACK_WAVE_COMPOSITION:
			wave_composition_table[str(k)] = FALLBACK_WAVE_COMPOSITION[k]
	wave_interval = float(economy.get("minion_wave_interval_frames", 1500)) / FPS
	print("[GameManager] ekonomi: %s gold/s · wave tiap %.0fs · %d tipe minion" % [
		format_gold_rate(float(economy.get("gold_per_second", 3))),
		wave_interval, minion_types.size()])


func minion_type_data(minion_type: String) -> Dictionary:
	var d = minion_types.get(minion_type)
	if d is Dictionary:
		return d
	return FALLBACK_MINION_TYPES.get(minion_type, {})


# ══════════════════════════════════════════════════════════
#  EKONOMI (port compute_starting_gold / compute_gold_per_second)
# ══════════════════════════════════════════════════════════

func difficulty_mult(d: String = "") -> float:
	var key := d if d != "" else difficulty
	var mults: Dictionary = economy.get("difficulty_gold_mult",
		FALLBACK_ECONOMY["difficulty_gold_mult"])
	return float(mults.get(key, 1.0))


## (base starting_gold level + 100 × (level-1)) × multiplier kesulitan
func compute_starting_gold(level_config: Dictionary, level_num: int,
		d: String = "") -> int:
	var base := int(level_config.get("starting_gold", 1000))
	var lv := maxi(1, level_num)
	var bonus: float = float(lv - 1) * float(economy.get("gold_per_level_bonus",
		FALLBACK_ECONOMY["gold_per_level_bonus"]))
	return int((float(base) + bonus) * difficulty_mult(d))


## (GOLD_PER_SECOND + 0.3 × (level-1)) × multiplier kesulitan
func compute_gold_per_second(level_num: int, d: String = "") -> float:
	var lv := maxi(1, level_num)
	var bonus: float = float(lv - 1) * float(economy.get("gold_per_second_level_bonus",
		FALLBACK_ECONOMY["gold_per_second_level_bonus"]))
	return (float(economy.get("gold_per_second", 3)) + bonus) * difficulty_mult(d)


## 3.0 -> "3", 5.7 -> "5.7", 3.75 -> "3.8" (paritas _core.format_gold_rate)
static func format_gold_rate(rate: float) -> String:
	var s := "%.1f" % rate
	if s.ends_with(".0"):
		s = s.substr(0, s.length() - 2)
	return s


func set_difficulty(d: String) -> void:
	if not ["easy", "normal", "hard"].has(d):
		return
	difficulty = d
	# Gold/s mengikuti kesulitan langsung; starting gold hanya saat match mulai.
	gold_per_second = compute_gold_per_second(level_number)
	# Enemy scaling ikut kesulitan (paritas _core.py:1460: aktif hanya "hard").
	# Di pygame difficulty dikunci per run (reset Game); di sini pergantian
	# mid-match (tombol D) hanya memengaruhi unit yang DI-SPAWN berikutnya —
	# minion/boss lama mempertahankan stat spawn-nya (pygame juga menerapkan
	# scaling saat spawn: _core.py:1792 dan 1822).
	var lv_data: Dictionary = BossDB.get_level(level_number)
	enemy_scaling_enabled = (difficulty == "hard")
	if enemy_scaling_enabled:
		enemy_hp_mult = float(lv_data.get("enemy_hp_mult", 1.0)) * 1.15
		enemy_damage_mult = float(lv_data.get("enemy_damage_mult", 1.0)) * 1.10
		enemy_speed_mult = float(lv_data.get("enemy_speed_mult", 1.0))
	else:
		enemy_hp_mult = 1.0
		enemy_damage_mult = 1.0
		enemy_speed_mult = 1.0
	difficulty_changed.emit(difficulty)
	print("[GameManager] difficulty -> %s (gold/s %s)%s" % [
		difficulty, format_gold_rate(gold_per_second),
		" · enemy scaling AKTIF" if enemy_scaling_enabled else ""])


func cycle_difficulty() -> String:
	var order := ["easy", "normal", "hard"]
	var idx := order.find(difficulty)
	set_difficulty(order[(idx + 1) % order.size()])
	return difficulty


# ══════════════════════════════════════════════════════════
#  LOOP
# ══════════════════════════════════════════════════════════

func _process(delta):
	# Watchdog hit-stop DULU: Engine.time_scale tidak boleh bisa "nyangkut" kecil
	_watch_hit_stop()
	if is_paused or in_menu:
		return
	if state != "playing":
		return
	# Passive gold (paritas Game: tiap 60 frame, pecahan disimpan di milli)
	_gold_timer += delta
	if _gold_timer >= 1.0:
		_gold_timer -= 1.0
		_gold_income_milli += int(round(gold_per_second * 1000.0))
		var gain: int = _gold_income_milli / 1000
		_gold_income_milli = _gold_income_milli % 1000
		if gain > 0:
			gold += gain
		# AI (tim red) menabung dengan laju yang sama
		_ai_gold_milli += int(round(gold_per_second * 1000.0))
		var ai_gain: int = _ai_gold_milli / 1000
		_ai_gold_milli = _ai_gold_milli % 1000
		ai_gold += ai_gain
	# Wave timer -> emit wave_started, yang spawn-nya ditangani scene (Main.gd)
	if waves_enabled and get_tree().current_scene != null:
		_wave_timer += delta
		if _wave_timer >= wave_interval:
			_wave_timer = 0.0
			next_wave()
	# Aura item (Steel Aegis / Everfrost / Solar Brand / Searbrand)
	_aura_timer += delta
	if _aura_timer >= 0.25:
		_aura_timer = 0.0
		if CombatSystem.has_method("update_auras"):
			CombatSystem.update_auras()


func start_level(lv: int, replay: bool = false):
	level_number = lv
	state = "playing"
	in_menu = false
	is_replay = replay
	var lv_data = BossDB.get_level(lv)
	# paritas Game.reset: gold awal & laju pasif dihitung dari level + difficulty
	starting_gold = compute_starting_gold(lv_data, lv)
	gold_per_second = compute_gold_per_second(lv)
	gold = starting_gold
	ai_gold = starting_gold
	_gold_income_milli = 0
	_ai_gold_milli = 0
	_gold_timer = 0.0
	_wave_timer = 0.0
	wave_number = 0
	# ── Meta reward match ini direset (paritas _core.py:1578-1581) ──
	meta_reward_earned = 0
	_meta_reward_granted = false
	bosses_defeated_this_match.clear()
	# ── ENEMY SCALING (paritas _core.py:1460 + 1476-1483): hanya Hard ──
	enemy_scaling_enabled = (difficulty == "hard")
	if enemy_scaling_enabled:
		enemy_hp_mult = float(lv_data.get("enemy_hp_mult", 1.0)) * 1.15
		enemy_damage_mult = float(lv_data.get("enemy_damage_mult", 1.0)) * 1.10
		enemy_speed_mult = float(lv_data.get("enemy_speed_mult", 1.0))
	else:
		enemy_hp_mult = 1.0
		enemy_damage_mult = 1.0
		enemy_speed_mult = 1.0
	# Hook BGM per level (levels.json["bgm_track"]; pygame main.py:521).
	# AudioManager no-op + log kalau aset wav belum disalin converter.
	AudioManager.play_bgm(str(lv_data.get("bgm_track", "bgm_battle.wav")))
	# Ambient loop hutan (paritas main.py:164 sound_mgr.play_ambient(
	# 'ambient_forest', volume_mult=0.8)). Kanal terpisah dari BGM, jadi
	# musik dan suara lingkungan berbunyi bersamaan seperti di pygame.
	AudioManager.play_ambient()
	print("[GameManager] Start Level %d%s — gold %d (%s/s, %s)%s" % [
		lv, " (replay)" if replay else "", gold, format_gold_rate(gold_per_second),
		difficulty, " · enemy scaling x%.2f HP" % enemy_hp_mult if enemy_scaling_enabled else ""])
	level_started.emit(lv)
	# call_deferred: antrian deferred itu FIFO — Main._on_level_started sudah
	# mengantri _start_battle (bersihkan arena lama + spawn nexus/hero) lebih
	# dulu, jadi wave 1 baru spawn SETELAH medan bersih. Kalau dipanggil
	# langsung, minion wave 1 lahir di arena lama lalu terhapus bersama
	# sisa match sebelumnya (arena kosong sampai wave 2, 25 detik).
	next_wave.call_deferred()


## Mulai ulang match yang sama (R setelah menang/kalah, atau ENTER saat kalah).
## Replay level yang sudah ditamatkan -> is_replay=true (paritas main.py:576:
## Game(screen, level_number=..., is_replay=True)) sehingga end_match()
## membayar reward replay, bukan reward menang pertama.
func restart_match() -> void:
	print("[GameManager] replay level %d" % level_number)
	start_level(level_number, true)


## Lanjut ke level berikutnya setelah VICTORY (ENTER). Paritas
## levels/level_data.py get_next_level (2340-2346): level+1 kalau masih ada
## konfigurasinya, kalau terakhir -> balik False dan pemain tinggal replay.
func next_level() -> bool:
	var nxt := next_level_number(level_number)
	if nxt <= 0:
		print("[GameManager] sudah level terakhir (%d) — tidak ada level berikutnya" % level_number)
		return false
	print("[GameManager] lanjut ke level %d" % nxt)
	start_level(nxt, false)
	return true


## Nomor level berikutnya (0 = tidak ada) — paritas get_next_level.
func next_level_number(after: int = -1) -> int:
	var cur := level_number if after < 0 else after
	var nxt := cur + 1
	var cfg: Dictionary = BossDB.get_level(nxt)
	if cfg.is_empty():
		return 0
	return nxt


## Total level (paritas levels/level_data.py get_level_count).
func level_count() -> int:
	return BossDB.levels.size()


## Kunci level di LEVEL_SELECT (paritas is_level_unlocked level_data.py:2318-2337):
## unlock_after_level == null -> selalu terbuka; selain itu butuh level itu
## ada di SaveManager.completed_levels.
func is_level_unlocked(level_num: int) -> bool:
	var cfg: Dictionary = BossDB.get_level(level_num)
	if cfg.is_empty():
		return false
	var required = cfg.get("unlock_after_level")
	if required == null:
		return true
	return SaveManager.is_level_completed(int(required))


## Kembali ke menu utama dari dalam match (PAUSE -> MAIN MENU, atau ESC
## setelah menang/kalah; paritas return_to_menu_requested main.py:582-586).
func return_to_menu() -> void:
	in_menu = true
	is_paused = false
	state = "idle"
	wave_number = 0
	shop_open = false
	AudioManager.stop_bgm()
	# Ambient ikut mati di menu — pygame memulainya sekali di main() dan
	# hanya hidup selama sesi match; di sini pasangan stop-nya eksplisit.
	AudioManager.stop_ambient()
	print("[GameManager] kembali ke menu utama")


func next_wave() -> void:
	wave_number += 1
	# Terompet wave baru (paritas Game.update _core.py:1740, volume_mult 0.6 —
	# dipelankan karena berbunyi tiap 25 detik dan tidak boleh menutupi SFX tempur).
	AudioManager.play_sfx("wave_start", 0.6)
	print("[GameManager] Wave %d" % wave_number)
	wave_started.emit(wave_number)
	# Castle shield gratis hanya sampai wave 10 (paritas Castle.set_wave)
	for nexus in [blue_nexus, red_nexus]:
		if nexus != null and is_instance_valid(nexus) and nexus.has_method("set_wave"):
			nexus.set_wave(wave_number)


## Komposisi minion untuk wave ini (sudah di-scale untuk wave > 5)
func wave_composition(wave: int) -> Array:
	var key := str(wave)
	if wave_composition_table.has(key):
		var c = wave_composition_table[key]
		if c is Array:
			return c.duplicate()
	if wave <= 5 and FALLBACK_WAVE_COMPOSITION.has(wave):
		return FALLBACK_WAVE_COMPOSITION[wave].duplicate()
	# Late game: ulang LATE_WAVE_MIX, tambah 1 unit tiap 2 wave (maks 10 per tim)
	var reps := clampi(1 + (wave - 5) / 2, 1, 2)
	var out: Array = []
	for _r in reps:
		out.append_array(LATE_WAVE_MIX)
	while out.size() > 10:
		out.remove_at(out.size() - 1)
	return out


## Skala HP/damage minion untuk wave tinggi (paritas minion_scale NEXUS_LEVELS)
func minion_scale_for(wave: int) -> float:
	var base := 1.0
	if blue_nexus != null and is_instance_valid(blue_nexus):
		base = maxf(base, float(blue_nexus.get("minion_scale")))
	if red_nexus != null and is_instance_valid(red_nexus):
		base = maxf(base, float(red_nexus.get("minion_scale")))
	# wave > 5: +8% per wave (aproksimasi eskalasi late-game pygame)
	if wave > 5:
		base *= 1.0 + 0.08 * float(wave - 5)
	return base


# ══════════════════════════════════════════════════════════
#  GOLD
# ══════════════════════════════════════════════════════════

func spend_gold(amount: int) -> bool:
	if gold >= amount:
		gold -= amount
		return true
	return false


func ai_spend(amount: int) -> bool:
	if ai_gold >= amount:
		ai_gold -= amount
		return true
	return false


func award_kill(killer_team: String, amount: int) -> void:
	# Tim pemain (blue/radiant) menabung gold; AI (red) punya saldo sendiri
	if killer_team == "blue":
		gold += amount
	elif killer_team == "red":
		ai_gold += amount


# ══════════════════════════════════════════════════════════
#  SPAWN
# ══════════════════════════════════════════════════════════

func spawn_hero(hero_type: String, team: String, pos: Vector2):
	var hero_scene = preload("res://scenes/hero/Hero.tscn")
	var hero = hero_scene.instantiate()
	hero.hero_type = hero_type
	hero.team = team
	hero.position = pos
	(container_or_root(hero_container)).add_child(hero)
	return hero


func spawn_boss(boss_type: String, team: String, pos: Vector2):
	var boss_scene = preload("res://scenes/boss/Boss.tscn")
	var boss = boss_scene.instantiate()
	boss.boss_type = boss_type
	boss.team = team
	boss.position = pos
	(container_or_root(boss_container)).add_child(boss)
	boss_spawned.emit(boss_type)
	return boss


func spawn_minion(minion_type: String, team: String, pos: Vector2,
		scale_mult: float = 1.0) -> Node2D:
	var minion_scene = preload("res://scenes/minion/Minion.tscn")
	var m = minion_scene.instantiate()
	m.minion_type = minion_type
	m.team = team
	m.position = pos
	if scale_mult != 1.0 and "stat_scale" in m:
		m.stat_scale = scale_mult
	(container_or_root(minion_container)).add_child(m)
	return m


func spawn_tower(team: String, pos: Vector2, lane: String = "mid",
		tower_kind: String = "outer", tower_type: String = "archer",
		level: int = 1):
	var tower_scene = preload("res://scenes/tower/Tower.tscn")
	var t = tower_scene.instantiate()
	t.team = team
	t.lane = lane
	t.tower_kind = tower_kind
	t.tower_type = tower_type
	t.level = level
	t.position = pos
	t.is_player_built = (team == "blue")
	(container_or_root(tower_container)).add_child(t)
	return t


func spawn_nexus(team: String, pos: Vector2):
	var nexus_scene = preload("res://scenes/base/Nexus.tscn")
	var n = nexus_scene.instantiate()
	n.team = team
	n.position = pos
	# Nexus itu struktur, jadi satu container dengan menara (digambar di belakang
	# unit) — bukan di Bosses yang digambar paling depan.
	(container_or_root(tower_container)).add_child(n)
	return n


## FX (peluru, damage number) ditaruh di CanvasLayer FX kalau ada
func attach_fx(node: Node) -> void:
	var host: Node = fx_container
	if host == null or not is_instance_valid(host):
		host = get_tree().current_scene
	if host == null:
		host = get_tree().root
	host.add_child(node)


## Container dari Main.tscn bisa belum terpasang (scene lain / sebelum Connector
## jalan). Jangan pernah null-crash: fallback ke current_scene, lalu root.
func container_or_root(container: Node) -> Node:
	if container != null and is_instance_valid(container):
		return container
	var scene := get_tree().current_scene
	if scene != null:
		return scene
	return get_tree().root


func count_alive(group: String, team: String) -> int:
	var tree := get_tree()
	if tree == null:
		return 0
	var n := 0
	for node in tree.get_nodes_in_group(group):
		if is_instance_valid(node) and node.get("team") == team and not bool(node.get("is_dead")):
			n += 1
	return n


# ══════════════════════════════════════════════════════════
#  NEXUS / MENANG-KALAH
# ══════════════════════════════════════════════════════════

func register_nexus(nexus) -> void:
	var team := str(nexus.get("team"))
	if team == "blue":
		blue_nexus = nexus
	else:
		red_nexus = nexus
	nexus.set_wave(wave_number)


func unregister_nexus(nexus) -> void:
	if blue_nexus == nexus:
		blue_nexus = null
	if red_nexus == nexus:
		red_nexus = null


func _on_nexus_destroyed(team: String, killer_team: String) -> void:
	if state != "playing":
		return
	# Radiant (blue) hancur = kalah; Dire (red) hancur = menang
	end_match(team == "red", killer_team)


func end_match(victory: bool, killer_team: String = "") -> void:
	if state != "playing":
		return
	state = "victory" if victory else "defeat"
	_grant_meta_reward(victory)
	AudioManager.stop_bgm()
	AudioManager.stop_ambient()
	AudioManager.play_sfx("victory" if victory else "defeat")
	print("[GameManager] %s — %s menang (meta reward %d gold)" % [
		state.to_upper(), killer_team if killer_team != "" else ("blue" if victory else "red"),
		meta_reward_earned])
	game_over.emit(victory)


## Port _grant_meta_reward (_core.py:2365-2456). KEBIJAKAN REWARD (flat):
##   - Kalah                          : 0 gold
##   - Menang pertama kali level ini  : meta_gold_reward_win  (default 3000)
##   - Replay menang (pertama kali)   : meta_gold_reward_replay (1500, SEKALI)
##   - Replay menang berikutnya       : meta_gold_reward_replay_repeat (200, unlimited)
## Semua ditulis ke save kunci "meta_gold" (bukan "gold"), di-guard
## _meta_reward_granted supaya nexus ganda tidak membayar dua kali.
func _grant_meta_reward(victory: bool) -> void:
	if _meta_reward_granted:
		return
	var reward := 0
	var cfg: Dictionary = BossDB.get_level(level_number)
	if not victory:
		# Kalah: pygame membaca meta_gold_reward_lose dari config level
		# (_core.py:2378-2380 pola cfg.get yang sama dengan jalur menang),
		# BUKAN angka 0 mati. Saat ini 54/54 level memang bernilai 0, tapi
		# meng-hardcode-nya membuat Godot diam-diam menyimpang begitu ada
		# satu level pygame yang memberi hadiah hiburan saat kalah.
		reward = int(cfg.get("meta_gold_reward_lose", 0))
	if victory:
		var win_reward := int(cfg.get("meta_gold_reward_win", 3000))
		var replay_reward := int(cfg.get("meta_gold_reward_replay", 1500))
		# default 200 = META_REPLAY_REPEAT_REWARD (_core.py:75)
		var repeat_reward := int(cfg.get("meta_gold_reward_replay_repeat", 200))
		var replay_key := str(level_number)
		if not (SaveManager.data["replay_reward_counts"] is Dictionary):
			SaveManager.data["replay_reward_counts"] = {}
		var replay_counts: Dictionary = SaveManager.data["replay_reward_counts"]
		var replay_count := int(replay_counts.get(replay_key, 0))
		# "replay" = sengaja mengulang (is_replay) ATAU level ini memang sudah
		# pernah ditamatkan (paritas _core.py:2387-2389).
		if is_replay or SaveManager.is_level_completed(level_number):
			reward = replay_reward if replay_count == 0 else repeat_reward
			replay_counts[replay_key] = replay_count + 1
		else:
			reward = win_reward
	meta_reward_earned = reward
	SaveManager.data["meta_gold"] = SaveManager.meta_gold() + reward

	if victory:
		# ═══ AUTO-UNLOCK HERO BOSS YANG DIKALAHKAN (GRATIS) ═══
		# Paritas _auto_unlock_defeated_boss_heroes (_core.py:2322-2355, dipanggil
		# dari _grant_meta_reward 2406): boss yang mati di match ini masuk
		# unlocked_bosses + unlocked_heroes HANYA kalau castle musuh juga jatuh.
		_auto_unlock_defeated_boss_heroes()
		# Tandai level tamat (paritas 2408-2414) -> level berikutnya (yang
		# memasang unlock_after_level = level ini) terbuka di LEVEL_SELECT.
		SaveManager.complete_level(level_number)
	SaveManager.save()
	_meta_reward_granted = true


## Port _auto_unlock_defeated_boss_heroes (_core.py:2322): boss (mini/true)
## yang dikalahkan di match yang DIMENANGKAN langsung jadi hero milik pemain
## tanpa memotong meta gold — di Hero Shop statusnya "OWNED".
func _auto_unlock_defeated_boss_heroes() -> void:
	var newly: Array = []
	for boss_type in bosses_defeated_this_match:
		var bt := str(boss_type)
		SaveManager.unlock_boss(bt)
		if not SaveManager.is_unlocked(bt):
			SaveManager.unlock_hero(bt)
			newly.append(bt)
	if not newly.is_empty():
		var names: Array = []
		for bt in newly:
			names.append(str(HeroDB.get_hero(bt).get("name", bt)))
		print("[HERO UNLOCK] gratis karena castle musuh jatuh: %s" % ", ".join(names))


## Dicatat Main._boss_tick saat boss mati; baru dicairkan jadi hero kalau
## match dimenangkan (paritas bosses_defeated_this_match _core.py:1594-1597).
func record_boss_defeated(boss_type: String) -> void:
	if not bosses_defeated_this_match.has(boss_type):
		bosses_defeated_this_match.append(boss_type)


func nexus_hp(team: String) -> Array:
	var nexus = blue_nexus if team == "blue" else red_nexus
	if nexus == null or not is_instance_valid(nexus):
		return [0.0, 1.0, 0.0, 0.0]
	return [float(nexus.get("hp")), float(nexus.get("max_hp")),
		float(nexus.get("shield")), float(nexus.get("shield_max"))]


# ══════════════════════════════════════════════════════════
#  HIT-STOP & PAUSE
# ══════════════════════════════════════════════════════════

## Dipanggil Hero/Boss; TIDAK await di node unit (lihat catatan di bawah)
func request_hit_stop(duration: float = 0.03, scale: float = 0.05) -> void:
	if _hit_stop_active:
		return
	_hit_stop_active = true
	_hit_stop_until_ms = Time.get_ticks_msec() + maxi(5, int(duration * 1000.0))
	Engine.time_scale = scale


func _watch_hit_stop() -> void:
	if not _hit_stop_active:
		return
	if Time.get_ticks_msec() >= _hit_stop_until_ms:
		_hit_stop_active = false
		Engine.time_scale = 1.0


## Dipanggil Main.gd (P / ESC). Yang membekukan simulasi adalah SceneTree, jadi
## flag ini cuma status untuk yang butuh tahu (mis. HUD / audio).
func set_paused(value: bool) -> void:
	is_paused = value


# ══════════════════════════════════════════════════════════
#  SELEKSI & TOKO
#  (port Game.selected_tower / selected_hero / build_slots / try_build_tower /
#   shop_open — sebelumnya tidak ada sama sekali di versi Godot)
# ══════════════════════════════════════════════════════════

## Slot bangun menara: [{pos, team, lane, taken, tower}] — diisi Main.gd dari
## lane path (paritas Game._generate_build_slots_from_lanes)
var build_slots: Array = []
var selected_hero = null
var selected_tower = null
var selected_nexus = null
## Index ke build_slots yang sedang dipilih (-1 = tidak ada)
var selected_slot: int = -1
var shop_open: bool = false


func clear_build_slots() -> void:
	build_slots.clear()
	selected_slot = -1


func add_build_slot(pos: Vector2, slot_team: String, lane: String) -> int:
	build_slots.append({"pos": pos, "team": slot_team, "lane": lane,
		"taken": false, "tower": null})
	return build_slots.size() - 1


func slot(index: int) -> Dictionary:
	if index < 0 or index >= build_slots.size():
		return {}
	return build_slots[index]


func free_slots_for(slot_team: String) -> Array:
	var out: Array = []
	for i in range(build_slots.size()):
		var s: Dictionary = build_slots[i]
		if str(s["team"]) == slot_team and not bool(s["taken"]):
			out.append(i)
	return out


func select_hero(hero) -> void:
	selected_hero = hero
	selected_tower = null
	selected_nexus = null
	selected_slot = -1
	selection_changed.emit()


func select_tower(tower) -> void:
	selected_tower = tower
	selected_hero = null
	selected_nexus = null
	selected_slot = -1
	selection_changed.emit()


func select_nexus(nexus) -> void:
	selected_nexus = nexus
	selected_hero = null
	selected_tower = null
	selected_slot = -1
	selection_changed.emit()


func select_slot_index(index: int) -> void:
	selected_slot = index
	selected_hero = null
	selected_tower = null
	selected_nexus = null
	selection_changed.emit()


func clear_selection() -> void:
	selected_hero = null
	selected_tower = null
	selected_nexus = null
	selected_slot = -1
	selection_changed.emit()


func toggle_shop() -> void:
	shop_open = not shop_open
	shop_changed.emit()


func open_shop() -> void:
	if not shop_open:
		shop_open = true
		shop_changed.emit()


func close_shop() -> void:
	if shop_open:
		shop_open = false
		shop_changed.emit()


## Titik spawn dekat base sendiri (dipakai toko hero)
func base_spawn_point(spawn_team: String, index: int = 0) -> Vector2:
	var am = get_tree().get_first_node_in_group("arena_map")
	if am != null and am.has_method("get_spawn_point"):
		return am.get_spawn_point(spawn_team, index)
	return Vector2(260, 480) if spawn_team == "blue" else Vector2(1020, 240)


# ── MENARA ────────────────────────────────────────────────

## Bangun menara di slot yang sedang dipilih (paritas Game.try_build_tower)
func try_build_tower(tower_type: String) -> bool:
	if state != "playing":
		return false
	var s := slot(selected_slot)
	if s.is_empty():
		print("[Shop] pilih slot bangun dulu")
		return false
	if bool(s["taken"]):
		print("[Shop] slot sudah terisi")
		return false
	if str(s["team"]) != "blue":
		print("[Shop] slot itu milik Dire")
		return false
	var cost := TowerDB.build_cost()
	if not spend_gold(cost):
		print("[Shop] gold kurang: butuh %d (punya %d)" % [cost, gold])
		return false
	# paritas Game.try_build_tower: tipe apa pun boleh dibangun di Lv1 seharga
	# 100 gold; stat non-archer Lv1 jatuh ke ARCHER_LEVELS[1] (TowerDB sudah
	# meniru fallback itu), jadi keuntungannya baru terasa setelah upgrade Lv2.
	var base_type := tower_type if TowerDB.tower_types().has(tower_type) else "archer"
	s["taken"] = true
	var t = spawn_tower("blue", s["pos"], str(s["lane"]), "outer", base_type, 1)
	s["tower"] = t
	select_tower(t)
	tower_built.emit(t)
	shop_changed.emit()
	print("[Shop] menara %s dibangun (-%d gold)" % [t.display_name, cost])
	return true


## Upgrade menara yang dipilih. Level 1 -> 2 wajib memilih jalur.
func try_upgrade_tower(target_type: String = "") -> bool:
	if state != "playing":
		return false
	var t = selected_tower
	if t == null or not is_instance_valid(t) or bool(t.get("is_dead")):
		return false
	if str(t.get("team")) != "blue":
		return false
	if not t.can_upgrade():
		print("[Shop] menara sudah level maksimum")
		return false
	var cost: int = t.upgrade_cost(target_type)
	if cost <= 0:
		return false
	if not spend_gold(cost):
		print("[Shop] gold kurang: upgrade butuh %d (punya %d)" % [cost, gold])
		return false
	if not t.upgrade(target_type):
		gold += cost
		return false
	shop_changed.emit()
	print("[Shop] menara jadi %s (-%d gold)" % [t.display_name, cost])
	return true


func try_sell_tower() -> bool:
	var t = selected_tower
	if t == null or not is_instance_valid(t) or bool(t.get("is_dead")):
		return false
	if not bool(t.get("is_player_built")):
		return false
	var refund: int = t.sell_value()
	for s in build_slots:
		if s.get("tower") == t:
			s["taken"] = false
			s["tower"] = null
	gold += refund
	t.queue_free()
	selected_tower = null
	selection_changed.emit()
	shop_changed.emit()
	print("[Shop] menara dijual (+%d gold)" % refund)
	return true


## Regen Shield menara (fitur berbayar 850 gold, menara Lv4+)
func try_buy_tower_regen_shield() -> bool:
	if state != "playing":
		return false
	var t = selected_tower
	if t == null or not is_instance_valid(t):
		return false
	if not t.can_activate_regen_shield():
		print("[Shop] Regen Shield butuh menara sendiri level %d+" % TowerDB.regen_shield_min_level())
		return false
	var cost: int = t.regen_shield_cost()
	if not spend_gold(cost):
		print("[Shop] gold kurang: Regen Shield butuh %d (punya %d)" % [cost, gold])
		return false
	if not t.activate_regen_shield():
		gold += cost
		return false
	shop_changed.emit()
	return true


# ── HERO ──────────────────────────────────────────────────

func try_buy_hero(hero_type: String) -> bool:
	if state != "playing":
		return false
	var cost := int(HeroDB.get_hero(hero_type).get("cost", 400))
	if not spend_gold(cost):
		print("[Shop] gold kurang: %s butuh %d (punya %d)" % [hero_type, cost, gold])
		return false
	var index := count_alive("heroes", "blue")
	var h = spawn_hero(hero_type, "blue", base_spawn_point("blue", index))
	# Seruan hero baru masuk medan (paritas Game.try_buy_hero _core.py:2637-2638:
	# ui_buy dibunyikan ShopPanel._run, hero_spawn di sini). Hanya hero yang
	# DIBELI pemain — hero AI lahir tanpa suara, sama seperti pygame.
	AudioManager.play_sfx("hero_spawn")
	select_hero(h)
	shop_changed.emit()
	print("[Shop] %s dibeli (-%d gold)" % [HeroDB.get_hero(hero_type).get("name", hero_type), cost])
	return true


func try_upgrade_hero() -> bool:
	if state != "playing":
		return false
	var h = selected_hero
	if h == null or not is_instance_valid(h) or bool(h.get("is_dead")):
		return false
	if str(h.get("team")) != "blue":
		return false
	if not h.can_upgrade():
		print("[Shop] hero sudah level maksimum")
		return false
	var cost: int = h.upgrade_cost()
	if not spend_gold(cost):
		print("[Shop] gold kurang: upgrade hero butuh %d (punya %d)" % [cost, gold])
		return false
	if not h.upgrade():
		gold += cost
		return false
	shop_changed.emit()
	return true


func try_buy_item(item_id: String) -> bool:
	if state != "playing":
		return false
	var h = selected_hero
	if h == null or not is_instance_valid(h) or bool(h.get("is_dead")):
		print("[Shop] pilih hero Radiant dulu untuk membeli item")
		return false
	if str(h.get("team")) != "blue":
		return false
	if not h.items.can_equip(item_id):
		if h.items.is_full():
			print("[Shop] 6 slot item %s sudah penuh" % h.name)
		else:
			print("[Shop] %s tidak bisa memakai %s (melee/magic only)" % [
				h.name, ItemDB.item_name(item_id)])
		return false
	var cost := ItemDB.item_cost(item_id)
	if not spend_gold(cost):
		print("[Shop] gold kurang: %s butuh %d (punya %d)" % [
			ItemDB.item_name(item_id), cost, gold])
		return false
	if not h.buy_item(item_id):
		gold += cost
		return false
	shop_changed.emit()
	return true


# ── NEXUS ─────────────────────────────────────────────────

func try_upgrade_nexus() -> bool:
	if state != "playing" or blue_nexus == null or not is_instance_valid(blue_nexus):
		return false
	if not blue_nexus.can_upgrade():
		return false
	var cost: int = blue_nexus.upgrade_cost()
	if not spend_gold(cost):
		print("[Shop] gold kurang: upgrade nexus butuh %d (punya %d)" % [cost, gold])
		return false
	if not blue_nexus.upgrade():
		gold += cost
		return false
	shop_changed.emit()
	print("[Shop] Radiant Nexus naik ke level %d (-%d gold)" % [blue_nexus.level, cost])
	return true


func try_buy_nexus_shield() -> bool:
	if state != "playing" or blue_nexus == null or not is_instance_valid(blue_nexus):
		return false
	if not blue_nexus.can_buy_shield():
		return false
	var cost: int = blue_nexus.shield_cost()
	if not spend_gold(cost):
		print("[Shop] gold kurang: Castle Shield butuh %d (punya %d)" % [cost, gold])
		return false
	if not blue_nexus.activate_castle_shield():
		gold += cost
		return false
	shop_changed.emit()
	print("[Shop] Castle Shield aktif (-%d gold)" % cost)
	return true



