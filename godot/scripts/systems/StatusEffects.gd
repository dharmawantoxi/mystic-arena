# StatusEffects.gd — port _core.TowerDebuffMixin (status effect universal).
#
# Dipakai Hero / Minion / Boss / Nexus lewat `var status = StatusEffects.new(self)`.
# pygame menyimpan timer dalam FRAME; di sini DETIK (Godot delta-time).
#
# Aturan stack (paritas apply_debuff): "terkuat menang, durasi di-refresh".
#   slow        - move speed turun          (Ice Tower / skill)
#   atk_slow    - attack speed turun        (Ice Tower / aura Everfrost)
#   skill_down  - damage skill turun        (Mage Tower)
#   anti_heal   - heal yang masuk dipotong  (Mage Tower / aura Cauterize)
#   burn        - damage per detik, tick 0.5 s (Cannon Tower / aura Scorched)
#   stun        - tidak bisa gerak & serang (skill; boss resist 55%)
#   armor_shred - armor dikikis             (Corroder)
#   dmg_amp     - damage diterima naik
#   heal_amp    - heal diterima naik        (Abyss Breaker)
#   blind       - peluang serangan fisik meleset (aura Solar Brand)
extends RefCounted

const FPS := 60.0
## TOWER_DEBUFF_BURN_TICK = 30 frame
const BURN_TICK := 30.0 / FPS
## Boss mini/true punya resist stun 55% (paritas apply_stun)
const BOSS_STUN_FACTOR := 0.45

var owner = null

# ── debuff menara / aura ──
var slow_amount: float = 0.0
var slow_timer: float = 0.0
var atk_slow_amount: float = 0.0
var atk_slow_timer: float = 0.0
var skill_down_amount: float = 0.0
var skill_down_timer: float = 0.0
var anti_heal_amount: float = 0.0
var anti_heal_timer: float = 0.0
var burn_dps: float = 0.0
var burn_timer: float = 0.0
var burn_accum: float = 0.0
var burn_tick_cd: float = BURN_TICK
var burn_team: String = ""
var stun_timer: float = 0.0
## SILENCE — hanya memblokir skill QWER; korban tetap bisa bergerak &
## menyerang biasa. Sengaja TERPISAH dari stun_timer: item Hexcraft
## (hex_idol) memberi stun 150 DAN silence 150 sekaligus, dan Soul Rend
## (sanguine_thorn) memberi silence TANPA stun — kalau digabung, Soul Rend
## akan ikut membekukan target dan itu jauh lebih kuat dari pygame.
var silence_timer: float = 0.0
var armor_shred_amount: float = 0.0
var armor_shred_timer: float = 0.0
var dmg_amp_amount: float = 0.0
var dmg_amp_timer: float = 0.0
var heal_amp_amount: float = 0.0
var heal_amp_timer: float = 0.0
var blind_amount: float = 0.0
var blind_timer: float = 0.0

# ── buff skill (SkillBook): id -> {timer, ...data} ──
var buffs: Dictionary = {}


func _init(p_owner = null) -> void:
	owner = p_owner


func clear() -> void:
	slow_amount = 0.0; slow_timer = 0.0
	atk_slow_amount = 0.0; atk_slow_timer = 0.0
	skill_down_amount = 0.0; skill_down_timer = 0.0
	anti_heal_amount = 0.0; anti_heal_timer = 0.0
	burn_dps = 0.0; burn_timer = 0.0; burn_accum = 0.0
	burn_tick_cd = BURN_TICK; burn_team = ""
	stun_timer = 0.0
	silence_timer = 0.0
	armor_shred_amount = 0.0; armor_shred_timer = 0.0
	dmg_amp_amount = 0.0; dmg_amp_timer = 0.0
	heal_amp_amount = 0.0; heal_amp_timer = 0.0
	blind_amount = 0.0; blind_timer = 0.0
	buffs.clear()


func _alive() -> bool:
	if owner == null:
		return true
	return not bool(owner.get("is_dead"))


# ══════════════════════════════════════════════════════════
#  APPLY
# ══════════════════════════════════════════════════════════

func apply_slow(amount: float, duration: float) -> void:
	if not _alive():
		return
	# Slow resist item (paritas apply_slow: amount *= 1 - get_slow_resist())
	if owner != null and owner.get("items") != null:
		amount *= 1.0 - float(owner.items.get_slow_resist())
	# Boss tenacity (base_boss.py Boss.apply_slow 528-538): magnitude &
	# durasi dipotong 50%, magnitude maks 35% (0.35).
	# Catatan: `owner` bisa Node (Boss/Hero/Minion). Object.get() hanya
	# menerima SATU argumen — jangan pakai get("boss_class", "") (error
	# runtime); cek keberadaan properti dulu lewat operator `in`.
	if owner != null and "boss_class" in owner and str(owner.get("boss_class")) != "":
		amount = minf(0.35, amount * (1.0 - 0.50))
		duration *= 0.5
	if amount > slow_amount or slow_timer < duration:
		slow_amount = amount
		slow_timer = duration


func apply_attack_slow(amount: float, duration: float) -> void:
	if not _alive():
		return
	# Boss tenacity untuk atk_slow (base_boss.py apply_debuff 540-550)
	if owner != null and "boss_class" in owner and str(owner.get("boss_class")) != "":
		amount = minf(0.35, amount * (1.0 - 0.50))
		duration *= 0.5
	if amount > atk_slow_amount or atk_slow_timer < duration:
		atk_slow_amount = amount
		atk_slow_timer = duration


func apply_skill_down(amount: float, duration: float) -> void:
	if not _alive():
		return
	if amount > skill_down_amount or skill_down_timer < duration:
		skill_down_amount = amount
		skill_down_timer = duration


func apply_anti_heal(amount: float, duration: float) -> void:
	if not _alive():
		return
	if amount > anti_heal_amount or anti_heal_timer < duration:
		anti_heal_amount = amount
		anti_heal_timer = duration


func apply_burn(dps: float, duration: float, source_team: String = "") -> void:
	if not _alive():
		return
	if burn_timer <= 0.0:
		burn_dps = dps
		burn_accum = 0.0
		burn_tick_cd = BURN_TICK
	else:
		burn_dps = maxf(burn_dps, dps)
	burn_timer = maxf(burn_timer, duration)
	if source_team != "":
		burn_team = source_team


func apply_armor_shred(amount: float, duration: float) -> void:
	if not _alive():
		return
	if amount > armor_shred_amount or armor_shred_timer < duration:
		armor_shred_amount = amount
		armor_shred_timer = duration


func apply_damage_amp(amount: float, duration: float) -> void:
	if not _alive():
		return
	if amount > dmg_amp_amount or dmg_amp_timer < duration:
		dmg_amp_amount = amount
		dmg_amp_timer = duration


func apply_heal_amp(amount: float, duration: float) -> void:
	if not _alive():
		return
	if amount > heal_amp_amount or heal_amp_timer < duration:
		heal_amp_amount = amount
		heal_amp_timer = duration


func apply_blind(amount: float, duration: float) -> void:
	if not _alive():
		return
	if amount > blind_amount or blind_timer < duration:
		blind_amount = amount
		blind_timer = duration


func apply_stun(duration: float) -> void:
	if not _alive():
		return
	# Boss (mini/true) resist 55% supaya tidak di-stunlock
	if owner != null and str(owner.get("boss_class")) != "":
		duration *= BOSS_STUN_FACTOR
	if duration <= 0.0:
		return
	if duration > stun_timer:
		stun_timer = duration


## Silence: blokir cast skill selama `duration` detik (paritas
## _apply_silence_to hero_items.py — dipakai Soul Rend & Hexcraft).
func apply_silence(duration: float) -> void:
	if not _alive() or duration <= 0.0:
		return
	if duration > silence_timer:
		silence_timer = duration


func is_silenced() -> bool:
	return silence_timer > 0.0


## Debuff menara dalam satu panggilan (dipakai TowerBullet.on_hit)
func apply_debuff(kind: String, amount: float, duration: float,
		source_team: String = "") -> void:
	match kind:
		"slow": apply_slow(amount, duration)
		"atk_slow": apply_attack_slow(amount, duration)
		"skill_down": apply_skill_down(amount, duration)
		"anti_heal": apply_anti_heal(amount, duration)
		"burn": apply_burn(amount, duration, source_team)
		"armor_shred": apply_armor_shred(amount, duration)
		"dmg_amp": apply_damage_amp(amount, duration)
		"heal_amp": apply_heal_amp(amount, duration)
		"blind": apply_blind(amount, duration)
		"stun": apply_stun(duration)
		"silence": apply_silence(duration)


# ══════════════════════════════════════════════════════════
#  BUFF SKILL (SkillBook)
# ══════════════════════════════════════════════════════════

func add_buff(id: String, duration: float, data: Dictionary = {}) -> void:
	var entry := data.duplicate()
	entry["timer"] = duration
	entry["duration"] = duration
	buffs[id] = entry


func has_buff(id: String) -> bool:
	return buffs.has(id)


func remove_buff(id: String) -> void:
	buffs.erase(id)


func buff(id: String) -> Dictionary:
	return buffs.get(id, {})


func buff_val(id: String, key: String, default: float = 0.0) -> float:
	var b = buffs.get(id)
	if b is Dictionary and b.has(key):
		return float(b[key])
	return default


## Sisa durasi buff 0..1 (untuk gambar cooldown/aura di unit)
func buff_ratio(id: String) -> float:
	var b = buffs.get(id)
	if not (b is Dictionary):
		return 0.0
	var total := float(b.get("duration", 0.0))
	if total <= 0.0:
		return 0.0
	return clampf(float(b.get("timer", 0.0)) / total, 0.0, 1.0)


# ══════════════════════════════════════════════════════════
#  QUERY (dipakai unit tiap frame)
# ══════════════════════════════════════════════════════════

func is_stunned() -> bool:
	return stun_timer > 0.0


## Pengali move speed: (1 - slow) × (1 + item move_speed_pct); 0 kalau stun
func move_speed_mult() -> float:
	if stun_timer > 0.0:
		return 0.0
	var m := 1.0 - slow_amount if slow_timer > 0.0 else 1.0
	if owner != null and owner.get("items") != null:
		m *= 1.0 + float(owner.items.get_move_speed_pct())
	# Windrun (Sylara W) = buff speed ×2
	if has_buff("speed"):
		m *= buff_val("speed", "mult", 1.0)
	return maxf(0.0, m)


## Attack cooldown efektif (detik) setelah atk_slow / stun
func attack_cd(base_cd: float) -> float:
	if stun_timer > 0.0:
		return 9999.0
	var cd := base_cd
	if atk_slow_timer > 0.0:
		cd = cd / maxf(0.05, 1.0 - atk_slow_amount)
	# Attack speed item/aura & buff skill (Focus Fire / Warpath)
	if owner != null and owner.get("items") != null:
		cd /= float(owner.items.get_attack_speed_mult())
	if has_buff("attack_speed"):
		cd /= maxf(0.05, buff_val("attack_speed", "mult", 1.0))
	return maxf(0.05, cd)


func damage_mult() -> float:
	var m := 1.0
	if has_buff("damage"):
		m *= buff_val("damage", "mult", 1.0)
	return m


## Potongan damage skill dari Mage Tower
func skill_damage_mult() -> float:
	var m := 1.0 - (skill_down_amount if skill_down_timer > 0.0 else 0.0)
	if has_buff("skill_amp"):
		m *= 1.0 + buff_val("skill_amp", "amount", 0.0)
	return maxf(0.0, m)


## Damage yang diterima naik (dmg_amp)
func incoming_mult() -> float:
	return 1.0 + (dmg_amp_amount if dmg_amp_timer > 0.0 else 0.0)


## Heal yang diterima: dipotong anti-heal, ditambah heal_amp (+ item heal_amp)
func heal_amount(amount: float) -> float:
	var out := amount
	if anti_heal_timer > 0.0:
		out *= 1.0 - anti_heal_amount
	var amp := 1.0
	if heal_amp_timer > 0.0:
		amp += heal_amp_amount
	if owner != null and owner.get("items") != null:
		amp += float(owner.items.get_heal_amp())
	return out * amp


## Peluang serangan fisik meleset (blind aura + evasion item)
func miss_chance(is_physical: bool) -> float:
	var chance := blind_amount if blind_timer > 0.0 else 0.0
	if is_physical and owner != null and owner.get("items") != null:
		chance = maxf(chance, float(owner.items.get_evasion()))
	# Shadow Realm (Zephyr W): tidak bisa ditarget sama sekali
	if has_buff("invis"):
		return 1.0
	return clampf(chance, 0.0, 1.0)


func armor_delta() -> float:
	return -(armor_shred_amount if armor_shred_timer > 0.0 else 0.0)


func can_be_targeted() -> bool:
	return not has_buff("invis")


func active_icon_list() -> Array:
	# Untuk HUD/debug: daftar debuff aktif
	var out: Array = []
	if slow_timer > 0.0: out.append("SLOW")
	if atk_slow_timer > 0.0: out.append("ATK-SLOW")
	if skill_down_timer > 0.0: out.append("SKILL-DOWN")
	if anti_heal_timer > 0.0: out.append("ANTI-HEAL")
	if burn_timer > 0.0: out.append("BURN")
	if stun_timer > 0.0: out.append("STUN")
	if armor_shred_timer > 0.0: out.append("SHRED")
	if blind_timer > 0.0: out.append("BLIND")
	return out


# ══════════════════════════════════════════════════════════
#  TICK
# ══════════════════════════════════════════════════════════

func tick(delta: float) -> void:
	if slow_timer > 0.0:
		slow_timer -= delta
		if slow_timer <= 0.0:
			slow_amount = 0.0
	if atk_slow_timer > 0.0:
		atk_slow_timer -= delta
		if atk_slow_timer <= 0.0:
			atk_slow_amount = 0.0
	if skill_down_timer > 0.0:
		skill_down_timer -= delta
		if skill_down_timer <= 0.0:
			skill_down_amount = 0.0
	if anti_heal_timer > 0.0:
		anti_heal_timer -= delta
		if anti_heal_timer <= 0.0:
			anti_heal_amount = 0.0
	if stun_timer > 0.0:
		stun_timer -= delta
	if silence_timer > 0.0:
		silence_timer -= delta
	if armor_shred_timer > 0.0:
		armor_shred_timer -= delta
		if armor_shred_timer <= 0.0:
			armor_shred_amount = 0.0
	if dmg_amp_timer > 0.0:
		dmg_amp_timer -= delta
		if dmg_amp_timer <= 0.0:
			dmg_amp_amount = 0.0
	if heal_amp_timer > 0.0:
		heal_amp_timer -= delta
		if heal_amp_timer <= 0.0:
			heal_amp_amount = 0.0
	if blind_timer > 0.0:
		blind_timer -= delta
		if blind_timer <= 0.0:
			blind_amount = 0.0

	# ── BURN: akumulasi dps lalu tick tiap 0.5 s (paritas _tick_tower_debuffs) ──
	if burn_timer > 0.0:
		burn_timer -= delta
		burn_accum += burn_dps * delta
		burn_tick_cd -= delta
		if burn_tick_cd <= 0.0:
			burn_tick_cd = BURN_TICK
			var dmg := int(burn_accum)
			if dmg > 0 and _alive():
				burn_accum -= float(dmg)
				_burn_damage(dmg)
		if burn_timer <= 0.0:
			burn_dps = 0.0
			burn_accum = 0.0

	# ── buff skill ──
	if not buffs.is_empty():
		var expired: Array = []
		for id in buffs:
			var b: Dictionary = buffs[id]
			b["timer"] = float(b["timer"]) - delta
			if float(b["timer"]) <= 0.0:
				expired.append(id)
		for id in expired:
			_on_buff_expired(str(id))
			buffs.erase(id)


func _burn_damage(dmg: int) -> void:
	if owner == null or not owner.has_method("take_damage"):
		return
	var team := burn_team if burn_team != "" else str(owner.get("team"))
	owner.take_damage(float(dmg), team, "fire", null, "")


## Buff yang habis perlu dinormalkan oleh pemiliknya (mis. damage ×1.5 Warpath)
func _on_buff_expired(id: String) -> void:
	if owner == null or not owner.has_method("on_buff_expired"):
		return
	owner.on_buff_expired(id)
