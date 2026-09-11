# CombatSystem.gd — Autoload. Port pipeline damage _entity.py + hero_items.py.
#
# Urutan penyelesaian damage (audit jalur basic hero — paritas
# Hero.take_damage pygame 4525-4712 DAN take_damage tiap jenis target):
#   1. guard kit hero   : Shadow Realm → Windrun (75% fisik) → Wind Wall
#                         (blokir "projectile" non-magic) → Tempest Veil
#   2. evasion / blind  : HERO = item evasion target + blind PENYERANG
#                         (True Strike menembus); BOSS = blind hanya utk
#                         damage_type "normal" yang punya source
#   3. mitigasi TARGET  : per jenis unit, urutan pygame masing-masing:
#                         hero    = amp int(round) → armor ITEM utk SEMUA
#                                   damage non-"fire" (live dari inventory,
#                                   dikikis shred, negatif = bonus) → block
#                                   (roll + aura guard, floor 0) →
#                                   Bristleback keep 0.70/0.85.
#                                   Hero pygame TIDAK punya magic_resist.
#                         minion  = amp → shred bonus → armor−shred / MR.
#                         boss    = amp → shred bonus → reduction−shred*0.06
#                                   (cap 0.60) / MR → resilience+anti-burst.
#                         tower   = armor / MR sekolah saja.
#                         nexus   = tanpa mitigasi sekolah (hanya shield).
#   4. hp berkurang     : shield tower/nexus menyerap dulu (castle:
#                         int truncation 88%) + damage number
#   4b. credit_hero     : source.damage_dealt += int(dealt) SETELAH HP
#                         (bukan shield) — `_entity.py:26-45`. Nested
#                         reflect memakai source=null jadi defender
#                         tidak ter-kredit.
#   5. reflect          : Bristleback 25% ("normal" netral → kena armor
#                         penyerang) + Thornmail int(dmg*0.85) "magic"
#   6. on-hit penyerang : lifesteal (basis damage PRA-mitigasi; ranged
#                         dibayar saat spawn di Hero.try_attack), cleave
#                         netral, corroder shred
#
# Blok kedua yang diport ke sini: singleton `_grid` tingkat modul dari
# `_system.py:145-200` (`SpatialGrid` + `update_spatial_grid` +
# `query_enemies_in_range`). Di pygame grid itulah satu-satunya jalur
# targeting per-unit (±100 kueri/frame), jadi padanannya ikut di/autoload
# query unit ini — lihat bagian SPATIAL GRID di bawah.
extends Node

const DAMAGE_NUMBER_SCENE := preload("res://scenes/fx/DamageNumber.tscn")
const SpatialGridScript := preload("res://scripts/systems/SpatialGrid.gd")

## Group yang dianggap "unit" saat mencari musuh (nexus = base yang bisa dihancurkan)
const UNIT_GROUPS: Array = ["heroes", "bosses", "minions", "towers", "nexus"]

## Dispatcher kematian terpusat. pygame `take_damage` TIDAK memanggil die():
## kematian diproses loop `Game.update` (_core.py:2196-2265). Di Godot SEMUA
## jalur damage lewat `apply_damage`, jadi keputusan "unit ini mati" ditaruh
## DI SINI — satu pintu — supaya pemanggil mana pun (serangan dasar, peluru
## menara, kit boss, kit skill hero, item on-hit, cleave, reflect, ranged)
## memicu `die()` unit yang benar + reward/popup/counter via register_*.
## Harness mitigasi murni (mis. HeroSkillParityTest yang hanya menyentuh HP,
## bukan kematian) menonaktifkannya — perilaku produksi tidak berubah.
var death_dispatch_enabled: bool = true


# ══════════════════════════════════════════════════════════
#  QUERY UNIT
# ══════════════════════════════════════════════════════════

## Semua unit hidup milik satu tim (dipakai skill AOE, aura, AI)
func units_of(team: String) -> Array:
	var out: Array = []
	for group in UNIT_GROUPS:
		for n in get_tree().get_nodes_in_group(group):
			if not is_instance_valid(n) or not (n is Node2D):
				continue
			if str(n.get("team")) != team:
				continue
			if bool(n.get("is_dead")):
				continue
			out.append(n)
	return out


## Semua musuh hidup dari sudut pandang `team`
func enemies_of(team: String) -> Array:
	var out: Array = []
	for group in UNIT_GROUPS:
		for n in get_tree().get_nodes_in_group(group):
			if not is_instance_valid(n) or not (n is Node2D):
				continue
			if str(n.get("team")) == team:
				continue
			if bool(n.get("is_dead")):
				continue
			if not _targetable(n):
				continue
			out.append(n)
	return out


## Musuh dalam radius dari sebuah titik
func enemies_in_radius(team: String, center: Vector2, radius: float) -> Array:
	var out: Array = []
	for e in enemies_of(team):
		if (e as Node2D).global_position.distance_to(center) <= radius:
			out.append(e)
	return out


## Paritas `_system.query_enemies_in_range(x, y, radius, team)` +
## `Minion._get_enemies` (`_entity.py:5635-5679`): minion/hero/boss diambil dari
## SpatialGrid (urutan bucket = urutan pygame), lalu tower & base diperiksa
## LANGSUNG dan appended di belakang — keduanya memang sengaja tidak diindeks
## grid (`_system.py:155-158`).
##
## Beda dengan `enemies_in_radius` di atas: fungsi itu tetap scan-grup dan
## dipakai jalur AoE/splash/aura/item, yang di pygame juga membaca list biasa
## (`game.minions + game.heroes`, bukan grid). Jadi kueri area besar TIDAK ikut
## berubah urutan saat grid dinyalakan.
##
## Kalau grid belum berlaku (menu, pause, atau harness headless yang men-step
## unit tanpa `Main._process`) -> fallback ke scan grup: himpunan hasilnya sama,
## hanya urutannya yang mengikuti grup alih-alih bucket.
func query_enemies_in_range(team: String, center: Vector2, radius: float) -> Array:
	if not spatial_grid_fresh():
		return enemies_in_radius(team, center, radius)
	var out: Array = []
	for e in _spatial_grid.query_enemies(center.x, center.y, radius, team):
		# Penjaga Godot (tidak ada padanannya di pygame): unit yang sedang tidak
		# bisa ditarget (mis. Shadow Realm) tetap tidak boleh jadi target.
		if not _targetable(e):
			continue
		out.append(e)
	var r2 := radius * radius
	for group in ["towers", "nexus"]:
		for n in get_tree().get_nodes_in_group(group):
			if not is_instance_valid(n) or not (n is Node2D):
				continue
			if str(n.get("team")) == team or bool(n.get("is_dead")):
				continue
			if not _targetable(n):
				continue
			var d: Vector2 = (n as Node2D).global_position - center
			if d.x * d.x + d.y * d.y <= r2:
				out.append(n)
	return out


# ══════════════════════════════════════════════════════════
#  SPATIAL GRID — singleton `_grid` tingkat modul (_system.py:145)
# ══════════════════════════════════════════════════════════

## Paritas `SpatialGrid(cell_size=60)` — _system.py:55/145
const GRID_CELL_SIZE := 60.0
## `_core.py:2009`: grid dibangun ulang hanya pada frame GENAP
## (`if self.animation_time % 2 == 0`) — jadi hasil kueri boleh basi 1 frame.
const GRID_REBUILD_EVERY := 2
## Jendela "masih dipakai": 2 frame = maksimum 1 frame basi seperti pygame.
## Lewat itu berarti yang membangun tidak jalan (menu/pause/harness) dan
## pemanggil harus jatuh ke scan langsung.
const GRID_STALE_FRAMES := 2
## Urutan insert = urutan pygame: `game.minions` lalu `get_all_heroes()`,
## dengan boss di-append paling akhir (_core.py:2010-2013).
const GRID_GROUPS: Array = ["minions", "heroes", "bosses"]

var _spatial_grid = SpatialGridScript.new()
var _grid_build_frame: int = -1000000
var _grid_ready: bool = false


func _ready() -> void:
	_spatial_grid.cell_size = GRID_CELL_SIZE


## Hasil build grid masih berlaku? False sebelum build pertama.
func spatial_grid_fresh() -> bool:
	if not _grid_ready:
		return false
	return Engine.get_process_frames() - _grid_build_frame <= GRID_STALE_FRAMES


## Jumlah entri terindeks (debug overlay + tes; pygame tidak punya padanan).
func spatial_grid_count() -> int:
	return _spatial_grid.count()


## Buang grid (harness/tes; produksi memanggil `update_spatial_grid` lagi).
func reset_spatial_grid() -> void:
	_spatial_grid.clear()
	_grid_ready = false
	_grid_build_frame = -1000000


## Padanan `update_spatial_grid(minions, heroes)` (_system.py:147-167): sekali
## per frame (frame genap) dari `Main._process`. Hanya minion & hero/boss yang
## diindeks; yang mati dilewati — persis seperti pygame.
func update_spatial_grid(minions: Array, heroes: Array) -> void:
	_spatial_grid.update_from(_alive_only(minions), _alive_only(heroes))
	_grid_build_frame = Engine.get_process_frames()
	_grid_ready = true


## Guard umur node Godot: `is_instance_valid` diperlukan karena array pemanggil
## bisa memegang node yang sudah di-free di tengah frame (pygame cukup membaca
## `.alive`). Aturan "unit mati tidak diindeks" sendiri ada di SpatialGrid.
static func _alive_only(units: Array) -> Array:
	var out: Array = []
	for u in units:
		if u != null and is_instance_valid(u):
			out.append(u)
	return out


## Varian produksi: daftar unit diambil dari grup scene tree dengan urutan
## yang sama dengan pygame, lalu diteruskan ke `update_spatial_grid`.
func update_spatial_grid_from_tree() -> void:
	var minions := _group_nodes("minions")
	var heroes := _group_nodes("heroes")
	heroes.append_array(_group_nodes("bosses"))
	update_spatial_grid(minions, heroes)


func _group_nodes(group: String) -> Array:
	var out: Array = []
	for n in get_tree().get_nodes_in_group(group):
		if is_instance_valid(n) and n is Node2D:
			out.append(n)
	return out


static func _targetable(unit) -> bool:
	var st = unit.get("status")
	if st != null and st.has_method("can_be_targeted"):
		return st.can_be_targeted()
	return true


## Unit terdekat yang bisa diserang (paritas _find_hunt_target: murni jarak)
func nearest_enemy(unit, max_distance: float) -> Node2D:
	var best: Node2D = null
	var best_d := max_distance
	var from: Vector2 = unit.global_position
	for e in enemies_of(str(unit.get("team"))):
		var d: float = from.distance_to((e as Node2D).global_position)
		if d < best_d:
			best_d = d
			best = e as Node2D
	return best


# ══════════════════════════════════════════════════════════
#  DAMAGE PENYERANG (sebelum mitigasi)
# ══════════════════════════════════════════════════════════

## Damage basic attack — mirror Hero._do_attack pygame 4244-4270 persis:
## base (Warpath Thorne R di pygame MENIMPA hero.damage langsung, jadi sudah
## masuk lewat `base`) + bonus item → crit buff kit (Grimjaw E
## `_crit_buff_active`: int(damage*2) SETELAH bonus item) → SOUL REND
## (Sanguine Thorn: crit PASTI 1.5x ke rend_target, TANPA roll dan
## men-diskip roll crit item — _do_attack 4261-4267) → crit item
## (Dead Edge: int(damage*mult)). Tidak ada multiplier status lain —
## pygame tidak punya jalur itu di _do_attack.
func calc_damage(attacker: Node, defender: Node, base: float, _school: String) -> float:
	var dmg := base
	var inv = attacker.get("items")
	if inv != null:
		dmg += inv.get_bonus_damage()
	var kt = attacker.get("kit")
	if kt is Dictionary and bool((kt as Dictionary).get("_crit_buff_active", false)):
		return float(int(dmg * 2.0))
	# ═══ SOUL REND: crit pasti ke target bertanda, tanpa roll ═══
	# Pygame membandingkan identitas self.target dengan inv.rend_target;
	# guard is_instance_valid murni untuk umur node Godot (rend_target
	# bisa sudah freed saat timer belum habis) — tidak mengubah perilaku.
	if inv != null and defender != null:
		var rm := float(inv.get_rend_crit())
		if rm > 0.0 and inv.rend_target != null \
				and is_instance_valid(inv.rend_target) \
				and inv.rend_target == defender:
			return float(int(dmg * rm))
	if inv != null:
		var roll: Array = inv.roll_crit()
		if roll[0]:
			return float(int(dmg * float(roll[1])))
	return dmg


## Damage skill: skill_damage hero × amplifier item × skill_down (Mage Tower)
func calc_skill_damage(attacker: Node, multiplier: float) -> float:
	var base := float(attacker.get("skill_damage"))
	var out := base * multiplier
	var inv = attacker.get("items")
	if inv != null:
		out *= 1.0 + inv.get_skill_amp()
	var st = attacker.get("status")
	if st != null:
		out *= st.skill_damage_mult()
	return maxf(0.0, out)


## Mitigasi — per jenis target, mirror take_damage pygame masing-masing
# ══════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════
#  MITIGASI — per jenis target, mirror take_damage pygame masing-masing
# ══════════════════════════════════════════════════════════

## Konversi aman ke float: float(null) di Godot 4.3 error
## "Invalid call. Nonexistent 'float' constructor". Object.get()
## mengembalikan null untuk properti yang absen (mis. stub status
## ProbeStatus di test parity lama), jadi SEMUA baca timer/amount
## status duck-typed harus lewat sini (null -> 0.0 -> efek nonaktif).
func _num(v) -> float:
	if v == null:
		return 0.0
	return float(v)


## Deteksi jenis unit (duck-typing field khas masing-masing class).
func _is_hero(unit) -> bool:
	return unit != null and "hero_type" in unit and "skills" in unit


func _is_minion(unit) -> bool:
	return unit != null and "minion_type" in unit


## HERO — mirror Hero.take_damage pygame 4636-4693.
## Urutan: dmg_amp int(round) → armor (SEMUA damage non-'fire', dibaca LIVE
## dari inventory: stat + aura − aura_reduction, dikikis shred; negatif =
## bonus 6%/poin) → block (roll item pakai amount melee/ranged PEMILIK,
## aura_guard_block menimpa tanpa roll, floor 0) → Bristleback keep
## 0.70/0.85 per sekolah. TIDAK ada magic_resist untuk hero di pygame.
func _hero_mitigate(target, dmg: float, dmg_type: String, st, eff_school: String) -> float:
	# Baca timer lewat .get() (duck-typed, konvensi CombatSystem): stub status
	# test parity lama tidak punya var ini — null -> 0.0 -> efek nonaktif.
	if st != null and _num(st.get("dmg_amp_timer")) > 0.0:
		dmg = float(int(DamageSchool.py_round(
			dmg * (1.0 + _num(st.get("dmg_amp_amount"))))))
	var inv = target.get("items")
	if dmg_type != "fire" and dmg > 0.0:
		var armor := float(inv.get_armor()) if inv != null else 0.0
		if st != null:
			armor += st.armor_delta()
		if armor > 0.0:
			var red := armor * 0.06 / (1.0 + armor * 0.06)
			dmg = maxf(1.0, DamageSchool.py_round(dmg * (1.0 - red)))
		elif armor < 0.0:
			var bonus := minf(1.0, -armor * 0.06)
			dmg = float(int(DamageSchool.py_round(dmg * (1.0 + bonus))))
		# Damage block: roll pasif + aura guard menimpa (pygame 4660-4686).
		# Roll lewat ParityRng supaya harness parity bisa meng-script-nya
		# (oracle pygame: random.random di _entity.take_damage).
		var block_amt := 0.0
		if inv != null:
			var blk: Array = inv.get_block()
			if float(blk[0]) > 0.0 and ParityRng.next() < float(blk[0]):
				block_amt = float(blk[1])
			if float(inv.aura_guard_block) > block_amt:
				block_amt = float(inv.aura_guard_block)
		if block_amt > 0.0:
			dmg = maxf(0.0, dmg - block_amt)
			_float_text(target, "BLOCK", false)
	# Bristleback: duri menahan 30% (15% utk magic) — pygame 4687-4693
	var kt = target.get("kit")
	if kt is Dictionary and bool((kt as Dictionary).get("_bristleback_active", false)) \
			and dmg > 0.0:
		var keep := 0.70 if eff_school != "magic" else 0.85
		dmg = maxf(1.0, DamageSchool.py_round(dmg * keep))
	return dmg


## MINION — mirror Minion.take_damage pygame 5795-5821.
## Urutan: dmg_amp → shred bonus damage ×(1+min(1,shred*0.06)) utk non-fire
## (double-dip Corroder) → school: physical memakai armor−shred (negatif =
## bonus), magic memakai magic_resist. Netral tanpa mitigasi sekolah.
func _minion_mitigate(target, dmg: float, dmg_type: String, st,
		eff_school: String, shred: float) -> float:
	if dmg > 0.0:
		if st != null and _num(st.get("dmg_amp_timer")) > 0.0:
			dmg = float(int(DamageSchool.py_round(
				dmg * (1.0 + _num(st.get("dmg_amp_amount"))))))
		if dmg_type != "fire" and shred > 0.0:
			dmg = float(int(DamageSchool.py_round(
				dmg * (1.0 + minf(1.0, shred * 0.06)))))
		var armor := float(target.get("armor")) - shred
		if eff_school == "physical" and armor != 0.0:
			if armor > 0.0:
				var red := armor * 0.06 / (1.0 + armor * 0.06)
				dmg = maxf(1.0, DamageSchool.py_round(dmg * (1.0 - red)))
			else:
				var bonus := minf(1.0, -armor * 0.06)
				dmg = float(int(DamageSchool.py_round(dmg * (1.0 + bonus))))
		elif eff_school == "magic" and float(target.get("magic_resist")) > 0.0:
			dmg = maxf(1.0, DamageSchool.py_round(
				dmg * (1.0 - float(target.get("magic_resist")))))
	return dmg


## BOSS — mirror Boss.take_damage pygame 5978-6037 (sebelum resilience).
## Urutan: dmg_amp → shred bonus → school: physical = reduction dikurangi
## shred×0.06 (bukan armor yang dikikis!) clamp [0, 0.60]; magic = MR.
## Resilience + anti-burst dipanggil terpisah lewat
## apply_boss_inherent_mitigation (sudah ada di Boss.gd).
func _boss_mitigate(target, dmg: float, dmg_type: String, st,
		eff_school: String, shred: float) -> float:
	if dmg > 0.0:
		if st != null and _num(st.get("dmg_amp_timer")) > 0.0:
			dmg = float(int(DamageSchool.py_round(
				dmg * (1.0 + _num(st.get("dmg_amp_amount"))))))
		if dmg_type != "fire" and shred > 0.0:
			dmg = float(int(DamageSchool.py_round(
				dmg * (1.0 + minf(1.0, shred * 0.06)))))
		var armor := float(target.get("armor"))
		if eff_school == "physical" and armor > 0.0:
			var red := armor * 0.06 / (1.0 + armor * 0.06)
			red = minf(0.60, maxf(0.0, red - shred * 0.06))
			dmg = maxf(1.0, DamageSchool.py_round(dmg * (1.0 - red)))
		elif eff_school == "magic" and float(target.get("magic_resist")) > 0.0:
			dmg = maxf(1.0, DamageSchool.py_round(
				dmg * (1.0 - float(target.get("magic_resist")))))
	return dmg


## TOWER — mirror Tower.take_damage pygame 1053-1071 (tanpa shred/amp:
## menara pygame tidak punya status itu). Nexus/castle TANPA mitigasi
## sekolah sama sekali (Castle.take_damage 1758 hanya shield).
func _tower_mitigate(target, dmg: float, eff_school: String) -> float:
	var armor := float(target.get("armor"))
	if eff_school == "physical" and armor > 0.0:
		var red := armor * 0.06 / (1.0 + armor * 0.06)
		dmg = maxf(1.0, DamageSchool.py_round(dmg * (1.0 - red)))
	elif eff_school == "magic" and float(target.get("magic_resist")) > 0.0:
		dmg = maxf(1.0, DamageSchool.py_round(
			dmg * (1.0 - float(target.get("magic_resist")))))
	return dmg


# ══════════════════════════════════════════════════════════
#  PIPELINE UTAMA
# ══════════════════════════════════════════════════════════

## Terapkan damage ke `target`. Return damage yang benar-benar mengurangi HP.
## `target.hp` diubah di sini supaya urutan mitigasi/reflect identik dengan pygame.
func apply_damage(target, amount: float, from_team: String = "",
		dmg_type: String = "normal", source = null, school: String = "",
		trigger_on_hit: bool = true) -> float:
	if target == null or not is_instance_valid(target):
		return 0.0
	if bool(target.get("is_dead")):
		return 0.0
	if amount <= 0.0:
		return 0.0

	# Boss.take_damage pygame tidak memfilter from_team. Atribusi boss
	# memakai team SOURCE, bukan label from_team (dikunci FASE 14).
	# Guard target lain tetap seperti sebelumnya; pemilihan target normal
	# sudah menyaring kawan di enemies_of().
	if not ("boss_type" in target) and from_team != "" \
			and str(target.get("team")) == from_team:
		return 0.0

	var st = target.get("status")
	# Sekolah damage = milik PENYERANG, bukan target (paritas
	# resolve_damage_school di _entity.py 106-131: school eksplisit ->
	# dmg_type dot yang netral -> source.dmg_school). Versi sebelumnya salah
	# mengambil dmg_school TARGET, sehingga serangan fisik ke hero berschool
	# magic ikut dianggap magic dan menembus armor.
	var eff_school := DamageSchool.resolve(school, dmg_type, source)
	var is_physical := DamageSchool.is_physical_hit(dmg_type, eff_school)

	# ── 0a. GUARD SKILL HERO (mirror _entity.py:4537-4585) ──
	# State handler hidup di h.kit (key = nama field pygame persis) dan
	# dicek SEBELUM semua mitigasi, dengan urutan persis pygame: shadow
	# realm → windrun → wind wall → veil. Cek sekolah memakai sekolah
	# PENAHAN PUKULAN (self._school di pygame = dmg_school unit), bukan
	# sekolah penyerang — sengaja, sama seperti sumbernya.
	var kt = target.get("kit")
	if kt != null and kt is Dictionary:
		# Shadow Realm (Zephyr W): kebal total selama di dalam realm —
		# dipotong PALING AWAL, sebelum Tempest Veil sekalipun.
		if bool((kt as Dictionary).get("_shadow_realm_active", false)):
			_float_text(target, "SHADOW", false)
			return 0.0
		# Windrun (Sylara W): 75% serangan fisik meleset; sihir tetap
		# menembus supaya status ini bukan invulnerability penuh. Roll
		# lewat ParityRng (harness parity meng-script nilainya; oracle
		# pygame: random.random di _entity.take_damage 4553-4557).
		if bool((kt as Dictionary).get("_windrun_active", false)) \
				and is_physical and ParityRng.next() < 0.75:
			_float_text(target, "WIND", false)
			return 0.0
		# Wind Wall (Kaizen W): memantulkan PROJECTILE mentah-mentah —
		# kecuali sekolah TERKirim = magic. Pygame memakai self._school yang
		# DI-SET DI AWAL take_damage dari serangan yang masuk
		# (resolve_damage_school), jadi ekuivalen dengan eff_school di sini —
		# BUKAN dmg_school statis milik penahan.
		if int((kt as Dictionary).get("_wind_wall_timer", 0)) > 0 \
				and dmg_type == "projectile" and eff_school != "magic":
			_float_text(target, "WALL", false)
			return 0.0

	# ── 0b. Tempest Veil: KEBAL total selama aktif ──
	# Item aktif auto-trigger saat HP < 40% (hero_items.py:2188-2194). Di
	# pygame guard ini berada SETELAH tiga guard kit hero di atas
	# (_entity.py:4589-4600) — urutan dipertahankan.
	var tv = target.get("items")
	if tv != null and tv.has_method("is_veiled") and tv.is_veiled():
		_float_text(target, "IMMUNE", false)
		return 0.0

	# ── 1. HERO: evasion item + blind PENYERANG (pygame 4605-4635) ──
	# Evasion dibaca dari item target, blind dari STATUS PENYERANG (aura
	# Solar Brand membutakan unit yang menyerang). True Strike (Sundering
	# Cudgel penyerang) menembus keduanya. Hanya untuk hit fisik.
	if _is_hero(target) and is_physical and amount > 0.0:
		if not _source_has_true_strike(source):
			var inv = target.get("items")
			var ev := float(inv.get_evasion()) if inv != null else 0.0
			var blind := _source_blind(source)
			var miss := maxf(ev, blind)
			# Roll lewat ParityRng (harness parity; oracle pygame:
			# random.random di _entity.take_damage 4620-4626).
			if miss > 0.0 and ParityRng.next() < miss:
				_float_text(target, "MISS", false)
				return 0.0

	# ── 1b. BOSS: blind hanya utk damage_type 'normal' DENGAN source ──
	# (pygame base_boss 5986-6003: serangan ranged 'projectile' tidak ikut
	# blind; boss tidak punya evasion sendiri.)
	if target.has_method("apply_boss_inherent_mitigation") \
			and dmg_type == "normal" and amount > 0.0 \
			and source != null and is_instance_valid(source):
		if not _source_has_true_strike(source):
			var bblind := _source_blind(source)
			# Roll lewat ParityRng (harness parity; oracle pygame:
			# random.random di base_boss.take_damage 5991-5994 —
			# dulu randf() langsung, tanpa pintu parity).
			if bblind > 0.0 and ParityRng.next() < bblind:
				_float_text(target, "MISS", false)
				return 0.0

	# ── 2-5. mitigasi PER JENIS TARGET (mirror take_damage pygame
	# masing-masing: urutan amp→armor→block→bristleback utk hero,
	# amp→shred-bonus→school utk minion/boss, school saja utk tower;
	# nexus tanpa mitigasi sekolah). ──
	var shred := 0.0
	if st != null and _num(st.get("armor_shred_timer")) > 0.0:
		shred = _num(st.get("armor_shred_amount"))
	var dmg := amount
	if _is_hero(target):
		dmg = _hero_mitigate(target, dmg, dmg_type, st, eff_school)
	elif target.has_method("apply_boss_inherent_mitigation"):
		dmg = _boss_mitigate(target, dmg, dmg_type, st, eff_school, shred)
		# Resilience (true 30% / mini 20%) + anti-burst cap — SETELAH
		# mitigasi sekolah, sebelum HP (pygame 6025-6037).
		dmg = target.apply_boss_inherent_mitigation(dmg)
	elif _is_minion(target):
		dmg = _minion_mitigate(target, dmg, dmg_type, st, eff_school, shred)
	elif "armor" in target and "magic_resist" in target and "tower_type" in target:
		dmg = _tower_mitigate(target, dmg, eff_school)

	dmg = maxf(0.0, dmg)
	if dmg <= 0.0:
		return 0.0

	# ── 6. kurangi HP (shield tower/nexus menyerap lebih dulu) ──
	var shield_pass: Array = _shield_pass(target, dmg)
	var absorbed := float(shield_pass[0])
	dmg = float(shield_pass[1])
	if dmg > 0.0:
		target.hp = float(target.get("hp")) - dmg
	var dealt := dmg
	var shown := dealt + absorbed
	_spawn_damage_number(target, shown, shown > float(target.get("max_hp")) * 0.12)
	# credit_hero_damage (_entity.py:26-45): integer HP yang mendarat
	# (sisa setelah shield), sebelum Bristleback. kit_hit TIDAK boleh
	# menambah lagi — kalau tidak skill terhitung dua kali.
	_credit_hero_damage(source, dealt)

	# ── 7. reset timer regen (tower/nexus: no_damage_timer, hero: combat_timer) ──
	if "combat_timer" in target:
		target.combat_timer = float(target.get("combat_reset"))

	# ── 8. reflect Bristleback 25% (source diputus: tidak bisa loop) ──
	# Mirror _entity.py:4699-4710: max(1, int(damage*0.25)) SETELAH damage
	# mendarat, target hidup, tim beda, dan sumber bukan diri sendiri.
	if kt != null and kt is Dictionary \
			and bool((kt as Dictionary).get("_bristleback_active", false)) \
			and dealt > 0.0 \
			and source != null and is_instance_valid(source) and source != target \
			and not bool(source.get("is_dead")) \
			and str(source.get("team")) != str(target.get("team")):
		apply_damage(source, maxf(1.0, floor(dealt * 0.25)), str(target.get("team")),
			"normal", null, "")

	# ── 8b. Thornmail (razor_carapace) — pantulkan reflect_pct damage ──
	# Item aktif auto-trigger saat HP < 55% (hero_items.py:2266-2273).
	# Mirror notify_damage_taken pygame: dmg = int(damage*refl) (boleh 0 =
	# tidak memantul apa-apa, TANPA max(1,..)) dan bertipe 'MAGIC' —
	# pantulan kena armor item / MR korban sesuai take_damage-nya.
	# `source` diputus supaya pantulan tidak memantul balik jadi loop.
	var tinv = target.get("items")
	if tinv != null and dealt > 0.0 and source != null and is_instance_valid(source) \
			and source != target and str(source.get("team")) != str(target.get("team")) \
			and tinv.has_method("get_active_reflect_pct"):
		var rpct := float(tinv.get_active_reflect_pct())
		if rpct > 0.0:
			var rdmg := float(int(dealt * rpct))
			if rdmg > 0.0:
				apply_damage(source, rdmg,
					str(target.get("team")), "magic", null, "")

	# ── 9. lifesteal + cleave + corroder penyerang (basis damage
	# PRA-mitigasi, paritas on_basic_attack_hit pygame) ──
	# trigger_on_hit=false: DAMAGE SKILL hero. Pygame memanggil
	# take_damage(dmg, team, source=hero, school=...) dari _bundle.py,
	# yang TIDAK memicu on_basic_attack_hit penyerang (jaket item on-hit
	# hanya untuk serangan dasar); source tetap diisi supaya atribusi
	# kill/reflect/blind/dispatch benar.
	if trigger_on_hit and source != null and is_instance_valid(source) and dealt > 0.0:
		_on_attacker_hit(source, target, dealt, is_physical, amount, dmg_type)

	# ── 10. DISPATCH KEMATIAN — paritas loop Game.update pygame ──
	# Pygame menandai alive=False di take_damage dan membayar reward di loop
	# Game.update; Godot memotong DI SINI supaya jalur damage mana pun yang
	# menulis HP <= 0 (peluru menara, kit boss, kit skill hero, item on-hit,
	# cleave, reflect Bristleback, serangan ranged) memanggil die() unit yang
	# benar. Urutan damping: SETELAH reflect/thornmail/on-hit penyerang —
	# persis pygame yang masih mengeksekusi reflect saat korban "baru mati";
	# reward tetap tepat sekali berkat guard `reward_processed` + guard
	# `is_dead` di setiap die().
	if death_dispatch_enabled and dmg > 0.0 and float(target.get("hp")) <= 0.0:
		_dispatch_death(target, source, from_team)

	return dealt


## Port `credit_hero_damage` `_entity.py:26-45`. `int(amount)` memotong
## ke 0; source tanpa field `damage_dealt` diabaikan (bukan hero). Nested
## reflect memakai source=null jadi defender tidak ter-kredit.
func _credit_hero_damage(source, amount: float) -> void:
	if source == null or not is_instance_valid(source) or amount <= 0.0:
		return
	if not ("damage_dealt" in source):
		return
	source.damage_dealt = float(source.get("damage_dealt")) + float(int(amount))


## Panggil die() unit dengan argumen sesuai jenisnya (pygame: take_damage
## tidak punya die(); Godot `die()` menerima killer/source untuk hero/boss
## dan killer_team untuk minion/tower/nexus). Sudah mati -> no-op; unit
## tanpa `die` (harness probe) -> no-op.
func _dispatch_death(target, source, from_team: String) -> void:
	if target == null or not is_instance_valid(target):
		return
	if bool(target.get("is_dead")):
		return
	if not target.has_method("die"):
		return
	if "boss_type" in target or "hero_type" in target:
		# Hero.die(killer) / Boss.die(killer): atribusi kill hero-vs-hero dan
		# killed_by boss memakai OBJEK source, bukan label team.
		target.die(source)
	elif "tower_type" in target:
		target.die(from_team, source)
	else:
		# Minion.die(killer_team) / Nexus.die(killer_team).
		target.die(from_team)


## True Strike penyerang (Sundering Cudgel): serangan basic tidak pernah
## meleset (menembus evasion + blind). Mirror has_true_strike hero_items.
func _source_has_true_strike(source) -> bool:
	if source == null or not is_instance_valid(source):
		return false
	var sinv = source.get("items")
	if sinv != null and sinv.has_method("has_true_strike"):
		return bool(sinv.has_true_strike())
	return false


## Blind PENYERANG (aura Solar Brand membutakan unit di sekitarnya):
## peluang serangan fisiknya meleset. Mirror blind_timer/blind_amount
## yang dibaca dari source di take_damage pygame.
func _source_blind(source) -> float:
	if source == null or not is_instance_valid(source):
		return 0.0
	var sst = source.get("status")
	if sst != null and _num(sst.get("blind_timer")) > 0.0:
		return _num(sst.get("blind_amount"))
	return 0.0


## Shield menyerap damage 1:1 lebih dulu (paritas Tower.take_damage 476-487 dan
## Castle.take_damage 201-225). Castle punya lapisan kedua: sisa damage tetap
## dipotong CASTLE_SHIELD_DAMAGE_REDUCTION (88%) selama shield_active.
## Return [diserap_shield, damage_yang_masuk_hp].
func _shield_pass(target, dmg: float) -> Array:
	if not ("shield" in target):
		return [0.0, dmg]
	if "no_damage_timer" in target:
		target.no_damage_timer = 0.0
	if "shield_active" in target and not bool(target.get("shield_active")):
		return [0.0, dmg]
	var shield := float(target.get("shield"))
	var remaining := dmg
	var absorbed := 0.0
	if shield > 0.0:
		absorbed = minf(shield, remaining)
		target.shield = shield - absorbed
		remaining -= absorbed
	if remaining > 0.0 and "shield_damage_reduction" in target:
		# pygame Castle.take_damage 1791: int(x * (1 - 0.88)) — truncation
		# Python (30*0.12 = 3.5999.. -> 3), bukan float bulat.
		remaining = float(int(remaining * (1.0 - float(target.get("shield_damage_reduction")))))
	return [absorbed, remaining]


## Heal lewat semantik property `hp` pygame: pemanggil mem-min ke max_hp
## DULU, lalu setter memotong kenaikan dengan anti-heal dan/atau
## memperbesarnya dengan heal_amp (debuff, _core.py:829-845). Dipakai
## lifesteal supaya identik dengan `h.hp = min(h.max_hp, h.hp + dmg*ls)`.
func heal_gain_py(unit, gain: float) -> void:
	if gain <= 0.0 or unit == null or not is_instance_valid(unit):
		return
	if bool(unit.get("is_dead")):
		return
	var max_hp := float(unit.get("max_hp"))
	var before := float(unit.get("hp"))
	var value := minf(max_hp, before + gain)
	var st = unit.get("status")
	if st != null and value > before:
		if _num(st.get("anti_heal_timer")) > 0.0:
			value = before + (value - before) * (1.0 - _num(st.get("anti_heal_amount")))
		if _num(st.get("heal_amp_timer")) > 0.0 and value > before:
			value = before + (value - before) * (1.0 + _num(st.get("heal_amp_amount")))
	unit.hp = value


## On-hit pasif penyerang — basis damage PRA-mitigasi (pygame
## on_basic_attack_hit menerima `damage` serangan, bukan damage mendarat).
## Lifesteal ranged TIDAK dibayar di sini: pygame membayarnya saat
## proyektil dilepas (Hero.try_attack), jalur 'projectile' di-skip.
func _on_attacker_hit(attacker, target, dealt: float, is_physical: bool,
		attack_amount: float, dmg_type: String) -> void:
	var inv = attacker.get("items")
	if inv == null:
		return
	# Lifesteal (Demon Maw): hp = min(max, hp + damage*ls) float via
	# semantik setter pygame — hanya untuk serangan non-projectile.
	var ls := float(inv.get_lifesteal_pct())
	if ls > 0.0 and dmg_type != "projectile" and attack_amount > 0.0:
		heal_gain_py(attacker, attack_amount * ls)
	# Cleave (Cleave Axe, melee only): splash int(damage*pct) ke musuh lain
	# radius 110 dari TARGET — netral 'normal' TANPA source (pygame 2478-2493),
	# jadi kena mitigasi take_damage korban, bukan school physical.
	var cleave: Array = inv.get_cleave()
	if cleave.size() == 2 and dmg_type == "normal" and attack_amount > 0.0:
		var splash := int(attack_amount * float(cleave[0]))
		if splash > 0:
			# pygame _collect_onhit_units: minion + hero + boss saja (BUKAN
			# tower/nexus), tanpa filter targetability — mirror loop cleave
			# hero_items.py:2478-2493.
			var center: Vector2 = (target as Node2D).global_position
			var atk_team := str(attacker.get("team"))
			for group in ["heroes", "bosses", "minions"]:
				for e in get_tree().get_nodes_in_group(group):
					if e == target or not is_instance_valid(e):
						continue
					if str(e.get("team")) == atk_team:
						continue
					if bool(e.get("is_dead")):
						continue
					if (e as Node2D).global_position.distance_to(center) > float(cleave[1]):
						continue
					apply_damage(e, float(splash), atk_team,
						"normal", null, "")
	# Corroder: kikis armor target
	var shred := float(inv.get_armor_shred())
	if shred > 0.0:
		var tst = target.get("status")
		if tst != null:
			tst.apply_armor_shred(shred, 360.0 / 60.0)


## Heal yang melewati anti-heal / heal_amp (paritas property `hp` setter pygame)
func heal_unit(unit, amount: float) -> float:
	if amount <= 0.0 or unit == null or not is_instance_valid(unit):
		return 0.0
	if bool(unit.get("is_dead")):
		return 0.0
	var st = unit.get("status")
	var healed := amount
	if st != null:
		healed = st.heal_amount(amount)
	if healed <= 0.0:
		return 0.0
	var max_hp := float(unit.get("max_hp"))
	var before := float(unit.get("hp"))
	unit.hp = minf(max_hp, before + healed)
	return float(unit.get("hp")) - before


# ══════════════════════════════════════════════════════════
#  AURA ITEM (Steel Aegis / Everfrost Guard / Solar Brand / Searbrand)
# ══════════════════════════════════════════════════════════

## Dipanggil GameManager ~4x/detik. pygame: hero_items.update_auras() tiap frame.
func update_auras() -> void:
	var all: Array = units_of("blue") + units_of("red")
	# reset aura yang diterima
	for u in all:
		var inv = u.get("items")
		if inv == null:
			continue
		inv.aura_armor = 0.0
		inv.aura_attack_speed = 0.0
		inv.aura_armor_reduction = 0.0
		inv.aura_atk_slow = 0.0
		inv.aura_anti_heal = 0.0
		inv.aura_burn_dps = 0.0
		inv.aura_blind = 0.0
		inv.aura_guard_block = 0.0
	# ── Bulwark Guard lebih dulu, sebelum aura biasa ──
	# pygame menghitungnya DULUAN dan terpisah dari Steel Aegis
	# (hero_items.py:2774-2795): hero ber-scarlet_bulwark yang guard-nya
	# menyala memberi block ke DIRINYA + sekutu dalam ally_radius.
	# aura_guard_block sudah lama ada di ItemInventory.get_block() tapi tak
	# pernah diisi siapa pun — nilainya selalu 0 sampai sekarang.
	for u in all:
		var ginv = u.get("items")
		if ginv == null or not ginv.has_method("is_guarding") or not ginv.is_guarding():
			continue
		var gdb = ItemDB.get_item("scarlet_bulwark")
		var gact = gdb.get("active")
		if not (gact is Dictionary):
			continue
		var g_radius := float(gact.get("ally_radius", 320.0))
		var g_team := str(u.get("team"))
		var g_pos: Vector2 = u.global_position
		for ally in all:
			if str(ally.get("team")) != g_team:
				continue
			if (ally as Node2D).global_position.distance_to(g_pos) > g_radius:
				continue
			var ainv = ally.get("items")
			if ainv == null:
				continue
			# block = base_block + max_hp_block_pct × Max HP sekutu
			var amt := float(gact.get("base_block", 0.0)) \
				+ float(gact.get("max_hp_block_pct", 0.0)) * float(ally.get("max_hp"))
			ainv.aura_guard_block = maxf(float(ainv.aura_guard_block), amt)
	# pancarkan
	for u in all:
		var inv = u.get("items")
		if inv == null:
			continue
		var auras: Array = inv.get_emitted_auras()
		if auras.is_empty():
			continue
		var pos: Vector2 = u.global_position
		var team := str(u.get("team"))
		for aura in auras:
			_apply_aura(u, aura, pos, team, all)


func _apply_aura(_caster, aura: Dictionary, pos: Vector2, team: String, all: Array) -> void:
	var ally_r := float(aura.get("ally_radius", 0))
	var enemy_r := float(aura.get("enemy_radius", 0))
	for u in all:
		if not is_instance_valid(u):
			continue
		var d: float = pos.distance_to(u.global_position)
		var inv = u.get("items")
		if inv == null:
			continue
		if str(u.get("team")) == team:
			if ally_r > 0.0 and d <= ally_r:
				inv.aura_armor += float(aura.get("ally_armor", 0))
				inv.aura_attack_speed += float(aura.get("ally_attack_speed", 0))
		else:
			if enemy_r > 0.0 and d <= enemy_r:
				inv.aura_armor_reduction += float(aura.get("enemy_armor_reduction", 0))
				var st = u.get("status")
				if st == null:
					continue
				var atk_slow := float(aura.get("enemy_atk_slow", 0))
				if atk_slow > 0.0:
					st.apply_attack_slow(atk_slow, 0.6)
				var anti_heal := float(aura.get("enemy_anti_heal", 0))
				if anti_heal > 0.0:
					st.apply_anti_heal(anti_heal, 0.6)
				var burn := float(aura.get("burn_dps", 0))
				if burn > 0.0:
					st.apply_burn(burn, 0.6, team)
				var blind := float(aura.get("blind", 0))
				if blind > 0.0:
					st.apply_blind(blind, 0.6)


# ══════════════════════════════════════════════════════════
#  FX TEKS
# ══════════════════════════════════════════════════════════

func _spawn_damage_number(target, amount: float, big: bool) -> void:
	if amount < 1.0:
		return
	_float_text(target, str(int(round(amount))), big)


func _float_text(target, text: String, big: bool) -> void:
	var tree := get_tree()
	if tree == null:
		return
	var host: Node = tree.current_scene
	if host == null:
		host = target
	var num = DAMAGE_NUMBER_SCENE.instantiate()
	num.setup(text, big)
	var radius := float(target.get("radius")) if "radius" in target else 16.0
	num.global_position = (target as Node2D).global_position \
		+ Vector2(randf_range(-radius * 0.6, radius * 0.6), -radius - 22.0)
	host.add_child(num)
