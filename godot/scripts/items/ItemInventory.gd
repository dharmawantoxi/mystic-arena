# ItemInventory.gd — port hero_items.HeroItemInventory (agregasi stat per hero).
#
# pygame: 6 slot, semua item 4500 gold, stat dijumlahkan lewat _sum_stat()
# dengan cap per-stat (evasion 50%, CDR 50%, move speed 40%, lifesteal 175%, ...).
# Semua cap di bawah disalin apa adanya supaya angka Godot = angka pygame.
#
# Yang SUDAH: seluruh stat flat/persen, crit, cleave, corrosion (armor shred),
#   block, aura (Steel/Freezing/Scorched/Cauterize) lewat CombatSystem.update_auras,
#   17 ITEM AKTIF (lihat blok "ITEM AKTIF" di bawah — semuanya auto-trigger,
#   pygame tidak punya tombol untuk item), seluruh efek ON-ATTACK
#   (bash x2, chain x2, Frostbite, Miasma + multishot, Empower Strike,
#   Entangle), pasif Leviathan Vitality, dan SOUL REND (Sanguine Thorn):
#   trigger otomatis + penandaan rend_target + crit pasti 1.5x di
#   CombatSystem.calc_damage (pygame _do_attack 4261-4267).
# Roll RNG proc (bash/chain/multishot/static/blind boss) lewat pintu
#   ParityRng — oracle `item_procs` (ItemProcParityTest) mengunci
#   jumlah+nilai+urutan konsumsinya vs pygame.
# Dengan itu Fase 5b lengkap: tidak ada lagi kunci di items.json yang
#   ("active"/"on_attack"/"bash"/"multishot"/"block"/"aura"/"passive")
#   tidak punya pembaca di sisi Godot.
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


## Holy Rapier rontok saat mati; item biasa tetap di slot yang sama.
## Paritas HeroItemInventory.clear_on_death, memakai metadata catalog.
func clear_on_death() -> bool:
	var dropped := false
	var db = _db()
	if db == null:
		return false
	for i in range(slots.size()):
		var item: Dictionary = db.get_item(str(slots[i]))
		if bool(item.get("drops_on_death", false)):
			remove_at(i)
			dropped = true
	return dropped


## Jual kembali: pygame tidak punya refund item, jadi 0 (dijaga eksplisit).
func sell_value(_index: int) -> int:
	return 0


func can_equip(item_id: String) -> bool:
	var db = _db()
	if db == null:
		return false
	if is_full():
		return false
	if db.is_melee_only(item_id) and not is_melee_for_equip():
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


## Gate MELEE khusus equip (hero_items.py:4057): melee_only DITOLAK kalau
## range hero SAAT INI > 80. BEDA dari is_melee() (flag/<110 — gate
## get_range_bonus/block); 0 dari 222 hero di 80..110 jadi tak divergen,
## tapi angka 80 evidence-anchored untuk jalur equip.
func is_melee_for_equip() -> bool:
	if hero == null:
		return true
	var rng := 100.0
	if "attack_range" in hero and hero.get("attack_range") != null:
		rng = float(hero.get("attack_range"))
	return HudLayout.is_melee_range(rng)


func is_magic() -> bool:
	if hero == null:
		return false
	# Paritas is_magic_hero: ROLE (mage/sorcerer/...) — BUKAN dmg_school.
	# 46 hero role-magic punya dmg_school fisik/None, jadi cek lama salah.
	var db = _db()
	if db != null and db.has_method("is_magic_hero"):
		return bool(db.is_magic_hero(hero))
	return str(hero.get("dmg_school")).to_lower() == "magic"


## Alasan item tak bisa dipakai: "" (bisa) | "OWNED" | "FULL" |
## "MELEE ONLY" | "MAGIC ONLY" (dua terakhir = label kartu pygame).
func equip_block_reason(item_id: String) -> String:
	var db = _db()
	if db == null:
		return ""
	if has(item_id):
		return "OWNED"
	if is_full():
		return "FULL"
	if bool(db.is_melee_only(item_id)) and not is_melee_for_equip():
		return "MELEE ONLY"
	if bool(db.get_item(item_id).get("magic_only", false)) and not is_magic():
		return "MAGIC ONLY"
	return ""


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
	var ls := _sum_stat("lifesteal")
	# Blood Frenzy (demon_maw) sedang menyala: +lifesteal_bonus sementara.
	# pygame menambahkannya di jalur yang sama sebelum cap 1.75
	# (hero_items.py:1940 `ls += 1.50  # Demon Maw active`), jadi cap tetap
	# berlaku sesudah bonus — bukan sebelum.
	if active_running("demon_maw"):
		var db = _db()
		if db != null:
			var act = db.get_item("demon_maw").get("active")
			if act is Dictionary:
				ls += float(act.get("lifesteal_bonus", 0.0))
	return minf(1.75, ls)


## Tempest Veil (tempest_vane) menyala = KEBAL semua damage.
## pygame memakainya di tiga tempat (_entity.py:3799/4241/4589) dan
## menampilkan teks "IMMUNE" alih-alih angka damage.
func is_veiled() -> bool:
	return active_running("tempest_vane")


## Bulwark Guard (scarlet_bulwark) menyala = block tambahan untuk diri
## sendiri DAN sekutu dalam ally_radius (update_auras hero_items.py:2776-2790).
func is_guarding() -> bool:
	return active_running("scarlet_bulwark")


## Persen damage yang dipantulkan balik ke penyerang saat Thornmail
## (razor_carapace) menyala. 0.0 = tidak aktif. Dibaca CombatSystem saat
## hero ini menerima serangan.
func get_active_reflect_pct() -> float:
	if not active_running("razor_carapace"):
		return 0.0
	var db = _db()
	if db == null:
		return 0.0
	var act = db.get_item("razor_carapace").get("active")
	if not (act is Dictionary):
		return 0.0
	return float(act.get("reflect_pct", 0.0))


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
## Roll lewat ParityRng supaya harness parity bisa meng-script-nya
## (oracle pygame: random.random di hero_items.roll_crit 2475-2483).
func roll_crit() -> Array:
	var chance := get_crit_chance()
	if chance <= 0.0:
		return [false, 1.0]
	if ParityRng.next() < chance:
		return [true, get_crit_mult()]
	return [false, 1.0]


## get_rend_crit() pygame — pengali crit PASTI selama Soul Rend aktif,
## else 0.0. Tanpa roll: CombatSystem.calc_damage yang membandingkan
## rend_target dengan defender (pygame _do_attack 4261-4267).
func get_rend_crit() -> float:
	if active_running("sanguine_thorn") and has("sanguine_thorn"):
		var db = _db()
		if db != null:
			var act = db.get_item("sanguine_thorn").get("active")
			if act is Dictionary:
				return float(act.get("crit_mult", 0.0))
	return 0.0


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
	# PENGECUALIAN Spectral Form (spectral_charm): selama aktif pemilik
	# berwujud hantu — SEMUA serangan fisik meleset (evasion efektif 100%,
	# sihir tetap mengenai). Paritas get_evasion hero_items.py:1985-1994,
	# termasuk posisinya SEBELUM cap 0.5 supaya 1.0 tidak ikut terpotong.
	if active_running("spectral_charm"):
		return 1.0
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


## Scarlet Bulwark: block [chance, amount] — amount mengikuti melee/ranged
## PEMILIK item (hero.range <= 80 pygame; setelah normalisasi melee = 70 =
## is_melee_hero), BUKAN jenis serangan yang masuk. Kalau ada beberapa
## sumber block, ambil peluang & angka tertinggi. aura_guard_block BUKAN
## bagian get_block pygame — penimpaannya (max, tanpa roll) ada di
## CombatSystem._hero_mitigate. Paritas get_block hero_items.py:2051-2070.
func get_block() -> Array:
	var db = _db()
	if db == null:
		return [0.0, 0.0]
	var best := [0.0, 0.0]
	for s in slots:
		if str(s) == "":
			continue
		var b = db.get_item(str(s)).get("block")
		if not (b is Dictionary):
			continue
		var amount := float(b.get("melee_block", 0)) if is_melee() \
			else float(b.get("ranged_block", 0))
		var chance := float(b.get("chance", 0))
		if chance > best[0] or amount > best[1]:
			best = [chance, amount]
	return best


## True Strike (Sundering Cudgel): serangan basic pemilik tidak pernah
## meleset — menembus evasion + blind. Paritas has_true_strike
## hero_items.py:2025-2031.
func has_true_strike() -> bool:
	return has("sundering_cudgel")


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


# ══════════════════════════════════════════════════════════
#  ITEM AKTIF — port hero_items.HeroItemInventory.update()
#  (hero_items.py:2133-2400, dipanggil _entity.py:3801 tiap frame)
# ══════════════════════════════════════════════════════════
#
# TEMUAN PENTING saat port: 17 "item aktif" ini TIDAK punya tombol dan TIDAK
# punya UI cooldown di pygame — semuanya AUTO-TRIGGER. Tiap deskripsi item
# menuliskan "(auto)" secara eksplisit (mis. hero_items.py:628, 668, 1283).
# Pemicunya cuma tiga pola:
#   1. hp_threshold    -> HP turun di bawah ambang (Blood Frenzy, Thornmail, ...)
#   2. trigger_enemies -> N musuh masuk radius (Arctic Blast, Binding Chains, ...)
#   3. target hidup    -> saat hero punya target (Soul Rend, Overwhelm, ...)
# Karena itu port ini TIDAK membuat tombol/hotbar: menambah input manual justru
# menyimpang dari sumber kebenaran. Yang diport adalah mesin pemicunya.
#
# SATUAN WAKTU: pygame menghitung frame @60 FPS (cooldown 1500 = 25 detik),
# Godot memakai detik. Semua nilai dibagi FPS lewat _sec().

## Cooldown & durasi aktif per item (detik). Kunci = item_id.
## Dipisah dari `slots` supaya menjual lalu membeli ulang item tidak
## me-reset cooldown-nya (paritas pygame yang menyimpan cd di inventory).
var _active_cd: Dictionary = {}
var _active_timer: Dictionary = {}
## Timer tick untuk efek berkala (Static Charge thunder_coil)
var _tick_cd: Dictionary = {}
## Target Soul Rend (Sanguine Thorn) yang sedang bertanda — serangan
## dasar pemilik ke unit ini crit pasti act.crit_mult (pygame
## rend_target, dikosongkan saat rend_timer habis, hero_items.py:2167).
var rend_target = null

## frame pygame -> detik Godot
static func _sec(frames: float) -> float:
	return float(frames) / FPS

## Pygame menghitung timer dalam FRAME INTEGER (140 - 140 = 0 persis);
## Godot mengurangi detik float (140 x 1/60 menyisakan ~1e-15), jadi
## SEMUA gate "masihcooldown / masihaktif" memakai ambang ini, bukan
## "> 0.0" telanjang — kalau tidak, kedaluarsa pas N frame bisa tetap
## terbuka dan proc meleset satu serangan (tertangkap oracle item_procs).
const EPS := 0.000000001


## Sisa cooldown item aktif (detik) — dipakai HUD/tooltip kalau nanti perlu.
func active_cooldown(item_id: String) -> float:
	return float(_active_cd.get(item_id, 0.0))


## Item aktif sedang menyala? (mis. Thornmail memantulkan damage)
func active_running(item_id: String) -> bool:
	return float(_active_timer.get(item_id, 0.0)) > EPS


## Dipanggil Hero._physics_process tiap frame — paritas inv.update(1, enemies)
## di _entity.py:3801. `enemies` diambil dari CombatSystem, bukan disimpan,
## supaya tidak ada referensi unit mati yang menggantung.
func tick(delta: float) -> void:
	# Turunkan semua timer dulu (pygame: dt dikurangi di awal update()).
	for k in _active_cd.keys():
		_active_cd[k] = maxf(0.0, float(_active_cd[k]) - delta)
	for k in _active_timer.keys():
		_active_timer[k] = maxf(0.0, float(_active_timer[k]) - delta)
	# static_tick pygame ikut loop timer generik hero_items.py:2149-2162
	# DAN di-decrement sekali lagi di blok Static Charge (2206) — total
	# DUA kali per frame. Itu quirk sumber: zap efektif tiap 15 frame,
	# bukan 30. Mirror persis: loop di sini + decrement di
	# _tick_static_charge.
	for k in _tick_cd.keys():
		if float(_tick_cd[k]) > 0.0:
			_tick_cd[k] = maxf(0.0, float(_tick_cd[k]) - delta)
	# Penandaan Soul Rend gugur bersama timernya (pygame 2166-2167).
	if not active_running("sanguine_thorn"):
		rend_target = null
	# Cooldown proc on-attack + racun Miasma (blok ON-ATTACK di bawah).
	_tick_procs(delta)
	if hero == null or bool(hero.get("is_dead")):
		return
	var db = _db()
	if db == null:
		return
	var max_hp := float(hero.get("max_hp"))
	if max_hp <= 0.0:
		return
	var ratio := float(hero.get("hp")) / max_hp
	for item_id in item_ids():
		var data: Dictionary = db.get_item(str(item_id))
		if not (data.get("active") is Dictionary):
			continue
		_try_active(str(item_id), data["active"], ratio, delta)


## Satu item aktif: cek pemicu, lalu jalankan efeknya.
func _try_active(item_id: String, act: Dictionary, hp_ratio: float, delta: float) -> void:
	# Static Charge (thunder_coil) TIDAK terpicu dari sini: pemicunya adalah
	# hero KENA DAMAGE dengan peluang proc_chance 20% (hero_items.py:2449-2457
	# di on_damage_taken), bukan "punya target". Di sini yang jalan hanya zap
	# berkalanya selama aura menyala.
	if item_id == "thunder_coil":
		if active_running(item_id):
			_tick_static_charge(item_id, act, delta)
		return
	if float(_active_cd.get(item_id, 0.0)) > EPS:
		return
	# ── Pemicu 1: HP di bawah ambang ──
	if act.has("hp_threshold"):
		if hp_ratio >= float(act["hp_threshold"]):
			return
	# ── Pemicu 2: N musuh dalam radius ──
	var near: Array = []
	if act.has("trigger_enemies"):
		var radius := float(act.get("trigger_radius", act.get("radius", 240.0)))
		near = _enemies_near(radius)
		if near.size() < int(act["trigger_enemies"]):
			return
	# ── Pemicu 3: sedang punya target musuh hidup ──
	var needs_target := not act.has("hp_threshold") and not act.has("trigger_enemies")
	var tgt = hero.get("target")
	if needs_target:
		if tgt == null or not is_instance_valid(tgt) or bool(tgt.get("is_dead")):
			return
	_fire_active(item_id, act, near, tgt)


## Jalankan efek + pasang cooldown/durasi.
func _fire_active(item_id: String, act: Dictionary, near: Array, tgt) -> void:
	_active_cd[item_id] = _sec(float(act.get("cooldown", 0.0)))
	if act.has("duration"):
		_active_timer[item_id] = _sec(float(act["duration"]))
	match item_id:
		"fenrir_chain", "everfrost_guard", "searbrand", "astral_codex":
			_burst_aoe(item_id, act, near)
		"fulgur_scepter":
			_damage_one(tgt, float(act.get("damage", 0.0)))
		"abyss_breaker":
			_stun_one(tgt, _sec(float(act.get("stun", 0.0))))
		"hex_idol":
			_stun_one(tgt, _sec(float(act.get("stun", 0.0))))
			_silence_one(tgt, _sec(float(act.get("silence", 0.0))))
		"sanguine_thorn":
			_silence_one(tgt, _sec(float(act.get("duration", 0.0))))
			_amp_one(tgt, float(act.get("damage_amp", 0.0)),
				_sec(float(act.get("duration", 0.0))))
			# TANDAI target: serangan dasar pemilik ke unit ini crit
			# pasti (get_rend_crit dibaca CombatSystem.calc_damage,
			# pygame _do_attack 4261-4267).
			rend_target = tgt
		"rift_veil":
			for e in near:
				_amp_one(e, float(act.get("damage_amp", 0.0)),
					_sec(float(act.get("duration", 0.0))))
		"vital_stone":
			# Vitality Pact: pulihkan % Max HP seketika (hero_items.py:1275-1286)
			var heal := float(hero.get("max_hp")) * float(act.get("heal_pct", 0.0))
			if CombatSystem != null:
				CombatSystem.heal_unit(hero, heal)
		"gale_pike":
			_gale_leap(float(act.get("dash_distance", 0.0)), tgt)
		_:
			# Sisanya (Blood Frenzy, Bulwark Guard, Tempest Veil, Thornmail,
			# Spectral Form) murni buff bertimer: efeknya dibaca getter lain
			# lewat active_running(), tidak ada aksi seketika di sini.
			pass
	_notify(str(act.get("name", item_id)))


## Dipanggil Hero.take_damage SETELAH armor/block, dengan damage yang benar-
## benar mengurangi HP — paritas on_damage_taken (hero_items.py:2440-2457).
## Di sinilah Static Charge (thunder_coil) menyala: peluang proc_chance 20%
## tiap kali pemilik kena pukul, lalu aura zap hidup selama `duration`.
func on_damage_taken(amount: float) -> void:
	if amount <= 0.0 or hero == null or bool(hero.get("is_dead")):
		return
	if not has("thunder_coil"):
		return
	if float(_active_cd.get("thunder_coil", 0.0)) > EPS:
		return
	var db = _db()
	if db == null:
		return
	var act = db.get_item("thunder_coil").get("active")
	if not (act is Dictionary):
		return
	# Roll lewat ParityRng (oracle item_procs: random.random di
	# hero_items.notify_damage_taken 2449-2452). CD-ready selalu
	# mengonsumsi satu roll, proc atau tidak.
	if ParityRng.next() >= float(act.get("proc_chance", 0.0)):
		return
	_active_timer["thunder_coil"] = _sec(float(act.get("duration", 0.0)))
	_active_cd["thunder_coil"] = _sec(float(act.get("cooldown", 0.0)))
	_tick_cd["thunder_coil"] = _sec(float(act.get("tick", 30.0)))
	_notify(str(act.get("name", "Static Charge")))


## Ledakan AoE sekali jalan (Binding Chains / Arctic Blast / Brand Burst /
## Arcane Nova) — pola sama di pygame, hanya beda efek sampingan.
func _burst_aoe(item_id: String, act: Dictionary, near: Array) -> void:
	var dmg := float(act.get("damage", 0.0))
	for e in near:
		_damage_one(e, dmg)
		match item_id:
			"fenrir_chain":
				# root = stun singkat (Godot belum punya root terpisah;
				# efek pygame _apply_stun_to juga memakai stun).
				_stun_one(e, _sec(float(act.get("root_duration", 0.0))))
			"everfrost_guard":
				var st = e.get("status")
				if st != null and st.has_method("apply_slow"):
					st.apply_slow(float(act.get("slow", 0.0)),
						_sec(float(act.get("slow_duration", 0.0))))
			"searbrand":
				var stb = e.get("status")
				if stb != null and stb.has_method("apply_burn"):
					stb.apply_burn(float(act.get("burn_dps", 0.0)),
						_sec(float(act.get("burn_duration", 0.0))),
						str(hero.get("team")))
			"astral_codex":
				_silence_one(e, _sec(float(act.get("silence_duration", 0.0))))


## Static Charge: zap N musuh terdekat tiap `tick` frame selama aura menyala.
func _tick_static_charge(item_id: String, act: Dictionary, delta: float) -> void:
	var cd := float(_tick_cd.get(item_id, 0.0)) - delta
	if cd > EPS:
		_tick_cd[item_id] = cd
		return
	_tick_cd[item_id] = _sec(float(act.get("tick", 30.0)))
	var near := _enemies_near(float(act.get("radius", 260.0)))
	var limit := int(act.get("targets", 4))
	for i in range(mini(limit, near.size())):
		_damage_one(near[i], float(act.get("damage", 0.0)))


## Gale Leap: lompat MENJAUH dari target (mundur), paritas hero_items.py:2297-2317.
func _gale_leap(distance: float, tgt) -> void:
	if distance <= 0.0:
		return
	var away := Vector2.ZERO
	if tgt != null and is_instance_valid(tgt):
		away = (hero.global_position - tgt.global_position)
	if away.length() < 0.001:
		# Tanpa target: dorong ke belakang sesuai arah hadap (pygame memakai
		# h.facing yang bernilai -1/+1).
		away = Vector2(-float(hero.get("facing")), 0.0)
	hero.global_position += away.normalized() * distance


# ── Pembantu kecil: semua lewat CombatSystem/StatusEffects yang sudah ada ──

func _enemies_near(radius: float) -> Array:
	if CombatSystem == null or hero == null:
		return []
	return CombatSystem.enemies_in_radius(str(hero.get("team")),
		hero.global_position, radius)


func _damage_one(target, amount: float, dmg_type: String = "magic") -> void:
	if amount <= 0.0 or target == null or not is_instance_valid(target):
		return
	if CombatSystem != null:
		# default "magic": mayoritas proc pygame memanggil
		# take_damage(dmg, team, "magic"); bash Abyss Breaker NETRAL
		# (take_damage(dmg, team) — lihat _bash_procs).
		CombatSystem.apply_damage(target, amount, str(hero.get("team")), dmg_type)


func _stun_one(target, seconds: float) -> void:
	if seconds <= 0.0 or target == null or not is_instance_valid(target):
		return
	var st = target.get("status")
	if st != null and st.has_method("apply_stun"):
		st.apply_stun(seconds)


func _silence_one(target, seconds: float) -> void:
	if seconds <= 0.0 or target == null or not is_instance_valid(target):
		return
	var st = target.get("status")
	if st != null and st.has_method("apply_silence"):
		st.apply_silence(seconds)


func _amp_one(target, amount: float, seconds: float) -> void:
	if amount <= 0.0 or seconds <= 0.0 or target == null or not is_instance_valid(target):
		return
	var st = target.get("status")
	if st != null and st.has_method("apply_damage_amp"):
		st.apply_damage_amp(amount, seconds)


## Teks mengambang di atas hero — paritas _fx_notify pygame ("ARCTIC BLAST!").
func _notify(text: String) -> void:
	if CombatSystem != null and CombatSystem.has_method("_float_text"):
		CombatSystem._float_text(hero, text.to_upper() + "!", true)


# ══════════════════════════════════════════════════════════
#  ON-ATTACK / BASH / MULTISHOT — port _on_hit_common()
#  (hero_items.py:2519-2666, dipanggil tiap basic attack kena)
# ══════════════════════════════════════════════════════════
#
# Berbeda dari item aktif di atas yang terpicu HP/jumlah-musuh, kelompok ini
# terpicu SETIAP SERANGAN DASAR yang mengenai target. pygame memanggilnya dari
# dua tempat (on_basic_attack_hit untuk melee, on_ranged_attack_hit untuk
# proyektil) yang keduanya bermuara ke _on_hit_common — jadi di Godot cukup
# satu pintu: CombatSystem._on_attacker_hit().
#
# Cooldown internal (bash 140 frame, pierce 120, vine 540) DIPISAH dari
# _active_cd item aktif supaya tidak saling menimpa: abyss_breaker punya
# `active` (Overwhelm) DAN `bash` sekaligus, dua-duanya pakai item_id sama.
var _proc_cd: Dictionary = {}
## Racun Miasma yang sedang berjalan: [target, sisa_detik, tick_cd, damage]
## Paritas _MIASMA global pygame (hero_items.py:209-234) — di sana global
## MODUL yang di-tick oleh SETIAP pemanggilan update() (tiap unit dengan
## ItemInventory men-decrement SEMUA racun 1x per frame; dengan 2 unit,
## racun yang sama menumpuk 2x/frame — lihat oracle item_procs). Maka
## wajib static (dibagi lintas instance), bukan per-instance — kalau tidak,
## tick racun hanya berjalan 1x/frame dan HP oracle meleset.
static var _miasma: Array = []


## Turunkan cooldown proc + jalankan racun Miasma. Dipanggil dari tick().
func _tick_procs(delta: float) -> void:
	for k in _proc_cd.keys():
		_proc_cd[k] = maxf(0.0, float(_proc_cd[k]) - delta)
	# Charge Empower Strike terisi turun seiring waktu (pygame
	# hero_items.py:2170-2172 — hanya saat runic_gavel dipakai).
	if hero != null and has("runic_gavel"):
		_empower_charge_init()
		if _empower_charge > 0.0:
			_empower_charge = maxf(0.0, _empower_charge - delta)
	if _miasma.is_empty():
		return
	var still: Array = []
	for m in _miasma:
		var tgt = m[0]
		if tgt == null or not is_instance_valid(tgt) or bool(tgt.get("is_dead")):
			continue
		m[1] -= delta
		m[2] -= delta
		if m[2] <= EPS:
			m[2] = 0.5  # tick 30 frame = 0.5 dtk (hero_items.py:224)
			# pygame: tgt.take_damage(m["damage"], team, "magic") dgn
			# team = getattr(src, "team") — tim dari SOURCE (hero
			# penabur racun), BUKAN dari inventory yang kebetulan
			# men-tick frame ini (_MIASMA global di-tick SEMUA unit;
			# kalau tim diambil dari pemilik inventory, tick via update
			# korban jadi damage satu tim sendiri dan tertahan — CI 4o).
			var src_team := "blue"
			if m.size() > 4 and m[4] != null and is_instance_valid(m[4]):
				src_team = str(m[4].get("team"))
			if CombatSystem != null:
				CombatSystem.apply_damage(tgt, float(m[3]), src_team,
						"magic")
		if m[1] > 0.0:
			still.append(m)
	_miasma = still


## Dipanggil CombatSystem._on_attacker_hit setiap serangan dasar kena.
## `damage` = damage yang benar-benar masuk, dipakai multishot (damage_pct).
##
## URUTAN = urutan situs di _on_hit_common pygame (hero_items.py:2519-2666),
## penting untuk oracle item_procs yang mengunci urutan roll:
##   bash Abyss -> chain -> pierce Cudgel -> frostbite -> miasma(+multishot)
##   -> empower -> entangle.
func on_attack_hit(target, damage: float) -> void:
	if hero == null or target == null or not is_instance_valid(target):
		return
	if bool(target.get("is_dead")):
		return
	var db = _db()
	if db == null:
		return
	_bash_procs(db, target)
	_chain_proc(db, target)
	_pierce_bash(db, target)
	_frostbite(db, target)
	_miasma_proc(db, target, damage)
	_empower(db, target)
	_entangle(db, target)


## Bash (abyss_breaker 22%): stun singkat + damage NETRAL — pygame
## memanggil take_damage(dmg, team) TANPA school (hero_items.py:2549-2551),
## jadi kena armor seperti serangan fisik, BUKAN magic.
func _bash_procs(db, target) -> void:
	var key := "abyss_breaker:bash"
	if not has("abyss_breaker"):
		return
	if float(_proc_cd.get(key, 0.0)) > EPS:
		return
	var b = db.get_item("abyss_breaker").get("bash")
	if not (b is Dictionary):
		return
	# Roll lewat ParityRng (oracle item_procs: random.random di
	# hero_items._on_hit_common); CD-ready selalu mengonsumsi roll.
	if ParityRng.next() >= float(b.get("chance", 0.0)):
		return
	_proc_cd[key] = _sec(float(b.get("cooldown", 0.0)))
	_stun_one(target, _sec(float(b.get("stun", 0.0))))
	_damage_one(target, float(b.get("damage", 0.0)), "normal")
	_notify_at(target, "BASH")


## Piercing Bash (sundering_cudgel 28%, cd internal sendiri pierce_bash_cd):
## site pygame SETELAH chain (hero_items.py:2584-2597) — damage-nya MAGIC.
func _pierce_bash(db, target) -> void:
	var key := "sundering_cudgel:bash"
	if not has("sundering_cudgel"):
		return
	if float(_proc_cd.get(key, 0.0)) > EPS:
		return
	var b = db.get_item("sundering_cudgel").get("bash")
	if not (b is Dictionary):
		return
	if ParityRng.next() >= float(b.get("chance", 0.0)):
		return
	_proc_cd[key] = _sec(float(b.get("cooldown", 0.0)))
	_stun_one(target, _sec(float(b.get("stun", 0.0))))
	_damage_one(target, float(b.get("damage", 0.0)), "magic")
	_notify_at(target, "PIERCE")


## Arc Chain (fenrir_chain 20%) / Arc Lightning (thunder_coil 22%):
## sambaran berantai ke N musuh sekitar TARGET (bukan sekitar hero).
func _chain_proc(db, target) -> void:
	# pygame get_on_attack_chain (hero_items.py:2082-2103): dict chain
	# dari SLOT PERTAMA yang layak — thunder_coil TIDAK otomatis menang;
	# yang dipakai statistik & peluangnya adalah item terdepan di slot.
	var chain: Dictionary = {}
	for s in slots:
		var sid := str(s)
		if sid == "":
			continue
		var oa = db.get_item(sid).get("on_attack")
		if oa is Dictionary and oa.has("chance") and oa.has("targets") \
				and oa.has("radius") and oa.has("damage"):
			chain = oa
			break
	if chain.is_empty():
		return
	# Roll lewat ParityRng (oracle item_procs: random.random di
	# hero_items._on_hit_common 2559).
	if ParityRng.next() >= float(chain.get("chance", 0.0)):
		return
	var limit := int(chain.get("targets", 3))
	var dmg := float(chain.get("damage", 0.0))
	_damage_one(target, dmg, "magic")
	var hit := 1
	for e in _enemies_near_point((target as Node2D).global_position,
			float(chain.get("radius", 240.0))):
		if hit >= limit:
			break
		if e == target:
			continue
		_damage_one(e, dmg, "magic")
		hit += 1


## Frostbite (frostbound_eye): slow + attack-slow + anti-heal sekaligus.
## Tanpa peluang & tanpa cooldown — tiap serangan kena (hero_items.py:2596-2615).
func _frostbite(db, target) -> void:
	if not has("frostbound_eye"):
		return
	var oa = db.get_item("frostbound_eye").get("on_attack")
	if not (oa is Dictionary):
		return
	var st = target.get("status")
	if st == null:
		return
	var dur := _sec(float(oa.get("duration", 0.0)))
	if st.has_method("apply_slow"):
		st.apply_slow(float(oa.get("slow", 0.0)), dur)
	if st.has_method("apply_attack_slow"):
		st.apply_attack_slow(float(oa.get("atk_slow", 0.0)), dur)
	if st.has_method("apply_anti_heal"):
		st.apply_anti_heal(float(oa.get("anti_heal", 0.0)), dur)


## Miasma (basilisk_breath): racun % Max HP target per tick, di-cap cap_damage.
## Sekalian Polycephaly (multishot 30%) — tembakan ekstra ke musuh terdekat,
## HANYA untuk hero ranged (hero_items.py:2621-2641). Racunnya sendiri
## TANPA roll; multishot me-roll sekali (ParityRng) dan damage ekstranya
## int(damage×pct) PRA-mitigasi seperti pygame (2637).
func _miasma_proc(db, target, damage: float) -> void:
	if not has("basilisk_breath"):
		return
	var data: Dictionary = db.get_item("basilisk_breath")
	var oa = data.get("on_attack")
	if oa is Dictionary:
		_apply_miasma(target, hero, oa)
	var ms = data.get("multishot")
	if not (ms is Dictionary) or is_melee():
		return
	if ParityRng.next() >= float(ms.get("chance", 0.0)):
		return
	var extra := int(ms.get("targets", 2))
	var pct := float(ms.get("damage_pct", 0.0))
	var n := 0
	for e in _enemies_near_point((target as Node2D).global_position,
			float(ms.get("radius", 200.0))):
		if n >= extra:
			break
		if e == target:
			continue
		_damage_one(e, float(int(damage * pct)), "magic")
		if oa is Dictionary:
			_apply_miasma(e, hero, oa)
		n += 1


## Pasang/refresh racun pada satu target (cap damage per tick).
func _apply_miasma(target, source, oa: Dictionary) -> void:
	# pygame: dmg = int(max_hp * pct); dmg = max(6, min(cap, dmg))
	# (hero_items.py:195-199) — truncation int() + floor 6 wajib,
	# kalau tidak HP pembanding melenceng perpecahan (oracle item_procs).
	var per_tick: float = float(int(float(target.get("max_hp")) * float(oa.get("max_hp_pct_per_tick", 0.0))))
	per_tick = maxf(6.0, minf(per_tick, float(oa.get("cap_damage", 9999.0))))
	for m in _miasma:
		if m[0] == target:
			# refresh pygame 201-203: timer MAX, tick_cd MIN, damage MAX,
			# source DIGANTI.
			m[1] = maxf(m[1], _sec(float(oa.get("duration", 0.0))))
			m[2] = minf(m[2], 0.5)
			m[3] = maxf(m[3], per_tick)
			if m.size() > 4:
				m[4] = source
			else:
				m.append(source)
			return
	_miasma.append([target, _sec(float(oa.get("duration", 0.0))), 0.5,
			per_tick, source])


## Charge Empower Strike — mirror empower_charge pygame: PENUH sejak
## __init__ (charge_time 540 frame), berkurang tiap frame lewat
## update(), dan baru bisa dikonsumsi saat habis (consume_empower_strike
## hero_items.py:2042-2048 mereset penuh setelah proc). Dulu sisi Godot
## langsung boleh proc di serangan pertama — beda dengan 9 detik pertama
## match pygame; kini di-mirror (init lazy dari ItemDB, fallback 540f).
var _empower_charge := -1.0


func _empower_charge_init() -> void:
	if _empower_charge >= 0.0:
		return
	var ct := 540.0
	var db = _db()
	if db != null:
		var p = db.get_item("runic_gavel").get("passive")
		if p is Dictionary:
			ct = float(p.get("charge_time", 540.0))
	_empower_charge = _sec(ct)


## Empower Strike (runic_gavel): serangan setelah charge habis memberi
## bonus magic damage 130, lalu charge terisi penuh lagi. Tanpa roll.
func _empower(db, target) -> void:
	if not has("runic_gavel"):
		return
	_empower_charge_init()
	if _empower_charge > EPS:
		return
	var p = db.get_item("runic_gavel").get("passive")
	if not (p is Dictionary):
		return
	_empower_charge = _sec(float(p.get("charge_time", 540.0)))
	_damage_one(target, float(p.get("damage", 0.0)), "magic")
	_notify_at(target, "EMPOWER")


## Entangle (vine_rod): ROOT = slow 100%. Target masih bisa menyerang &
## pakai skill, hanya tak bisa berpindah (catatan eksplisit hero_items.py:2660).
func _entangle(db, target) -> void:
	if not has("vine_rod"):
		return
	if float(_proc_cd.get("vine_rod:root", 0.0)) > EPS:
		return
	var vr = db.get_item("vine_rod").get("on_attack")
	if not (vr is Dictionary):
		return
	_proc_cd["vine_rod:root"] = _sec(float(vr.get("cooldown", 540.0)))
	var st = target.get("status")
	if st != null and st.has_method("apply_slow"):
		st.apply_slow(1.0, _sec(float(vr.get("root_duration", 0.0))))
		_notify_at(target, "ROOT")


## Bonus regen Leviathan Vitality: % Max HP per detik saat LUAR tempur.
## pygame memakai last_damage_timer sendiri (combat_timeout 300 frame);
## Hero.combat_timer Godot sudah melakukan hal yang sama (di-reset
## CombatSystem tiap kena damage), jadi dipakai ulang — tidak ada timer kedua.
func get_out_of_combat_regen() -> float:
	if not has("leviathan_heart") or hero == null:
		return 0.0
	if float(hero.get("combat_timer")) > 0.0:
		return 0.0
	var db = _db()
	if db == null:
		return 0.0
	var p = db.get_item("leviathan_heart").get("passive")
	if not (p is Dictionary):
		return 0.0
	return float(hero.get("max_hp")) * float(p.get("out_of_combat_regen_pct", 0.0))


func _enemies_near_point(center: Vector2, radius: float) -> Array:
	if CombatSystem == null or hero == null:
		return []
	return CombatSystem.enemies_in_radius(str(hero.get("team")), center, radius)


func _notify_at(target, text: String) -> void:
	if CombatSystem != null and CombatSystem.has_method("_float_text"):
		CombatSystem._float_text(target, text + "!", false)
