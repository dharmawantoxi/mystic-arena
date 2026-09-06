# ItemInventory.gd — port hero_items.HeroItemInventory (agregasi stat per hero).
#
# pygame: 6 slot, semua item 4500 gold, stat dijumlahkan lewat _sum_stat()
# dengan cap per-stat (evasion 50%, CDR 50%, move speed 40%, lifesteal 175%, ...).
# Semua cap di bawah disalin apa adanya supaya angka Godot = angka pygame.
#
# Yang BELUM diport (butuh timer/proyektil tersendiri, lihat docs/GODOT_MIGRATION.md):
#   active item (Blood Frenzy, Arctic Blast, Brand Burst, Bulwark Guard, ...),
#   on_attack / bash / multishot, pasif Empower Strike & Leviathan Vitality.
# Yang SUDAH: seluruh stat flat/persen, crit, cleave, corrosion (armor shred),
#   block, dan aura (Steel/Freezing/Scorched/Cauterize) lewat CombatSystem.update_auras.
extends RefCounted

const FPS := 60.0

## Kapasitas fallback — paritas hero_items.MAX_ITEM_SLOTS
const FALLBACK_MAX_SLOTS := 6

var hero = null                 # Hero.gd (weak-ish: dipakai untuk is_melee/dmg_type)
var slots: Array = []           # [item_id | ""] × max_slots

# ── Aura yang DITERIMA (di-set CombatSystem.update_auras tiap 0.25 s) ──
var aura_armor: float = 0.0
var aura_attack_speed: float = 0.0
var aura_armor_reduction: float = 0.0
var aura_atk_slow: float = 0.0
var aura_anti_heal: float = 0.0
var aura_burn_dps: float = 0.0
var aura_blind: float = 0.0
var aura_guard_block: float = 0.0


func _init(p_hero = null) -> void:
	hero = p_hero
	slots.resize(max_slots())
	for i in range(slots.size()):
		slots[i] = ""


func max_slots() -> int:
	var db = _db()
	return db.max_slots() if db != null else FALLBACK_MAX_SLOTS


var _cached_db = null


## ItemDB adalah autoload; diambil lewat SceneTree (bukan identifier global)
## supaya script ini tidak gagal parse kalau autoload-nya belum terdaftar
## (mis. dipakai dari tools/ headless). Hasilnya di-cache — getter stat
## dipanggil puluhan kali per frame.
func _db():
	if _cached_db != null and is_instance_valid(_cached_db):
		return _cached_db
	var ml := Engine.get_main_loop()
	if ml is SceneTree:
		_cached_db = (ml as SceneTree).root.get_node_or_null("ItemDB")
	return _cached_db


# ══════════════════════════════════════════════════════════
#  SLOT
# ══════════════════════════════════════════════════════════

func count() -> int:
	var n := 0
	for s in slots:
		if str(s) != "":
			n += 1
	return n


func is_full() -> bool:
	return count() >= slots.size()


func free_slot() -> int:
	for i in range(slots.size()):
		if str(slots[i]) == "":
			return i
	return -1


func has(item_id: String) -> bool:
	return slots.has(item_id)


func item_ids() -> Array:
	var out: Array = []
	for s in slots:
		if str(s) != "":
			out.append(str(s))
	return out


## Beli/pasang item. Return false kalau slot penuh atau item tidak dikenal.
func add_item(item_id: String) -> bool:
	var db = _db()
	if db == null or not db.has_item(item_id):
		return false
	var idx := free_slot()
	if idx < 0:
		return false
	slots[idx] = item_id
	return true


func remove_at(index: int) -> String:
	if index < 0 or index >= slots.size():
		return ""
	var old := str(slots[index])
	slots[index] = ""
	return old


## Jual kembali: pygame tidak punya refund item, jadi 0 (dijaga eksplisit).
func sell_value(_index: int) -> int:
	return 0


func can_equip(item_id: String) -> bool:
	var db = _db()
	if db == null:
		return false
	if is_full():
		return false
	if db.is_melee_only(item_id) and not is_melee():
		return false
	if bool(db.get_item(item_id).get("magic_only", false)) and not is_magic():
		return false
	return true


func is_melee() -> bool:
	if hero == null:
		return true
	if "is_melee_hero" in hero:
		return bool(hero.is_melee_hero)
	return float(hero.get("attack_range")) < 110.0


func is_magic() -> bool:
	if hero == null:
		return false
	return str(hero.get("dmg_school")).to_lower() == "magic"


# ══════════════════════════════════════════════════════════
#  AGREGASI STAT (paritas _sum_stat + cap per getter)
# ══════════════════════════════════════════════════════════

func _sum_stat(key: String) -> float:
	var db = _db()
	if db == null:
		return 0.0
	var total := 0.0
	for s in slots:
		if str(s) == "":
			continue
		total += db.stat(str(s), key, 0.0)
	return total


func get_bonus_damage() -> float:
	return _sum_stat("damage")


func get_bonus_hp() -> float:
	return _sum_stat("hp")


func get_hp_pct() -> float:
	return _sum_stat("hp_pct")


func get_armor() -> float:
	return _sum_stat("armor") + aura_armor - aura_armor_reduction


func get_hp_regen() -> float:
	return _sum_stat("hp_regen")


## Max HP = (base + flat) × (1 + hp_pct) — paritas HeroItemInventory.get_max_hp
func get_max_hp(base_hp: float) -> int:
	return int((base_hp + get_bonus_hp()) * (1.0 + get_hp_pct()))


## 1 attack speed = +1% lebih cepat; cap [0.2 .. 2.5]
func get_attack_speed_mult() -> float:
	var as_total := _sum_stat("attack_speed") + aura_attack_speed
	return clampf(1.0 + as_total / 100.0, 0.2, 2.5)


func get_lifesteal_pct() -> float:
	return minf(1.75, _sum_stat("lifesteal"))


func get_crit_chance() -> float:
	var db = _db()
	if db == null:
		return 0.0
	var chance := 0.0
	for s in slots:
		if str(s) == "":
			continue
		chance = maxf(chance, db.stat(str(s), "crit_chance", 0.0))
	return chance


func get_crit_mult() -> float:
	var db = _db()
	if db == null:
		return 2.0
	var mult := 2.0
	for s in slots:
		if str(s) == "":
			continue
		if db.stat(str(s), "crit_chance", 0.0) > 0.0:
			mult = maxf(mult, db.stat(str(s), "crit_mult", 2.25))
	return mult


## roll_crit() pygame -> [is_crit, multiplier]
func roll_crit() -> Array:
	var chance := get_crit_chance()
	if chance <= 0.0:
		return [false, 1.0]
	if randf() < chance:
		return [true, get_crit_mult()]
	return [false, 1.0]


## Cleave Axe: [pct, radius] atau [] — hanya berlaku untuk hero melee
func get_cleave() -> Array:
	if not is_melee():
		return []
	var db = _db()
	if db == null:
		return []
	for s in slots:
		if str(s) == "":
			continue
		var p: Dictionary = db.passive(str(s))
		if str(p.get("name", "")) == "Cleave":
			return [float(p.get("cleave_pct", 0.5)), float(p.get("cleave_radius", 110))]
	return []


## Corroder: armor shred (dipakai CombatSystem sebelum mitigasi)
func get_armor_shred() -> float:
	var db = _db()
	if db == null:
		return 0.0
	var total := 0.0
	for s in slots:
		if str(s) == "":
			continue
		var p: Dictionary = db.passive(str(s))
		total += float(p.get("armor_shred", 0.0))
	return total


func get_cooldown_reduction() -> float:
	return minf(0.5, _sum_stat("cooldown_reduction"))


func get_spell_vamp() -> float:
	return _sum_stat("spell_vamp")


func get_skill_amp() -> float:
	return minf(0.5, _sum_stat("skill_amp"))


func get_evasion() -> float:
	return minf(0.5, _sum_stat("evasion"))


func get_move_speed_pct() -> float:
	return minf(0.40, _sum_stat("move_speed_pct"))


func get_heal_amp() -> float:
	return minf(0.5, _sum_stat("heal_amp"))


func get_slow_resist() -> float:
	return minf(0.6, _sum_stat("slow_resist"))


## Range bonus hanya untuk hero ranged (paritas get_range_bonus)
func get_range_bonus() -> float:
	if is_melee():
		return 0.0
	return _sum_stat("range_bonus")


## Scarlet Bulwark: block [chance, amount]
func get_block(is_melee_attack: bool) -> Array:
	var db = _db()
	if db == null:
		return [0.0, 0.0]
	for s in slots:
		if str(s) == "":
			continue
		var b = db.get_item(str(s)).get("block")
		if b is Dictionary:
			var amount := float(b.get("melee_block", 0)) if is_melee_attack \
				else float(b.get("ranged_block", 0))
			var chance := float(b.get("chance", 0))
			if aura_guard_block > 0.0:
				amount += aura_guard_block
			return [chance, amount]
	if aura_guard_block > 0.0:
		return [1.0, aura_guard_block]
	return [0.0, 0.0]


## Aura yang DIPANCARKAN hero ini (diproses CombatSystem.update_auras)
func get_emitted_auras() -> Array:
	var db = _db()
	if db == null:
		return []
	var out: Array = []
	for s in slots:
		if str(s) == "":
			continue
		var a: Dictionary = db.aura(str(s))
		if not a.is_empty():
			out.append(a)
	return out


func summary() -> String:
	var db = _db()
	if db == null:
		return ""
	var parts: Array = []
	for s in slots:
		if str(s) == "":
			parts.append("—")
		else:
			parts.append(db.item_name(str(s)))
	return " · ".join(parts)
