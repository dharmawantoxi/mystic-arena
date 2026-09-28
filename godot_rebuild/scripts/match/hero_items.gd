extends RefCounted
## Port of the hero_items.py metadata the AI reads: catalog lookup,
## is_magic_hero and suggest_item_for_hero. NO stat effects, passives, actives,
## auras or Forge UI: those stay in a separate, much larger phase.

const METADATA := "res://data/ai/item_catalog.json"
const MELEE_RANGE_LIMIT := 80.0
# Source MAGIC_ROLE_KEYWORDS. "Anti-Mage" is deliberately excluded below: a mage
# hunter is not a mage, so magic_only items stay locked for that role.
const MAGIC_ROLE_KEYWORDS: Array[String] = [
	"mage",
	"magic",
	"sorcer",
	"caster",
	"warlock",
	"witch",
	"sage",
	"prophet",
	"priestess",
	"pyro",
	"necro",
	"shaman",
	"summoner",
	"chorister",
	"farseer",
	"starweaver",
	"hex",
	"eldritch",
]
const TANK_POOL: Array[String] = [
	"leviathan_heart",
	"scarlet_bulwark",
	"searbrand",
	"razor_carapace",
	"everfrost_guard",
	"steel_aegis",
	"abyss_breaker",
	"solar_brand",
	"demon_maw",
	"corroder",
	"fenrir_chain",
	"octarine_core",
	"moon_shard",
]
const MARKSMAN_POOL: Array[String] = [
	"dead_edge",
	"basilisk_breath",
	"gale_pike",
	"frostbound_eye",
	"sundering_cudgel",
	"searbrand",
	"monarch_wings",
	"thunder_coil",
	"sanguine_thorn",
	"moon_shard",
	"runic_gavel",
	"corroder",
	"demon_maw",
	"octarine_core",
	"steel_aegis",
]
const MAGIC_POOL: Array[String] = [
	"astral_codex",
	"fulgur_scepter",
	"sage_scepter",
	"hex_idol",
	"rift_veil",
	"vital_stone",
	"spectral_charm",
	"vine_rod",
	"octarine_core",
	"runic_gavel",
	"searbrand",
	"solar_brand",
	"frostbound_eye",
	"everfrost_guard",
	"tempest_vane",
	"corroder",
	"moon_shard",
	"thunder_coil",
	"steel_aegis",
	"demon_maw",
	"dead_edge",
]
const FALLBACK_POOL: Array[String] = [
	"steel_aegis",
	"searbrand",
	"sundering_cudgel",
	"frostbound_eye",
	"razor_carapace",
	"moon_shard",
	"demon_maw",
	"leviathan_heart",
	"scarlet_bulwark",
	"solar_brand",
	"thunder_coil",
	"monarch_wings",
	"octarine_core",
	"gale_pike",
	"dead_edge",
	"corroder",
	"everfrost_guard",
]

var catalog: Dictionary


func _init(metadata: Dictionary = {}) -> void:
	if metadata.is_empty():
		catalog = JSON.parse_string(FileAccess.get_file_as_string(METADATA))
	else:
		catalog = metadata.duplicate(true)


func max_slots() -> int:
	return int(catalog.max_slots)


func item(item_id: String) -> Dictionary:
	var items: Dictionary = catalog.items
	return items.get(item_id, {})


func item_cost(item_id: String) -> int:
	return int(item(item_id).get("cost", 0))


static func source_range(attack_range: float) -> float:
	# Source reads `getattr(hero, "range", 100) or 100`: 0 falls back to 100.
	return 100.0 if attack_range <= 0.0 else attack_range


static func is_melee(attack_range: float) -> bool:
	return source_range(attack_range) <= MELEE_RANGE_LIMIT


static func is_magic_hero(role: String) -> bool:
	var lowered := role.to_lower()
	if lowered.strip_edges().is_empty():
		return false
	if lowered.contains("anti-mage"):
		return false
	for keyword in MAGIC_ROLE_KEYWORDS:
		if lowered.contains(keyword):
			return true
	return false


static func role_pool(role: String, magic: bool) -> Array[String]:
	var lowered := role.to_lower()
	if lowered.contains("tank") or lowered.contains("bruiser") or lowered.contains("fighter"):
		return TANK_POOL
	if lowered.contains("marksman") or lowered.contains("assassin"):
		return MARKSMAN_POOL
	if lowered.contains("mage") or lowered.contains("trickster") or magic:
		return MAGIC_POOL
	return FALLBACK_POOL


func suggest_item_for_hero(role: String, attack_range: float, owned: Array) -> String:
	var melee := is_melee(attack_range)
	# Source: melee inserts cleave_axe first and holy_rapier last, ranged only
	# appends holy_rapier. Owned slots are skipped, then the melee_only and
	# magic_only gates decide the first affordable candidate.
	var candidates: Array[String] = []
	if melee:
		candidates.append("cleave_axe")
	for item_id in role_pool(role, is_magic_hero(role)):
		candidates.append(item_id)
	candidates.append("holy_rapier")
	for item_id in candidates:
		if owned.has(item_id):
			continue
		var data := item(item_id)
		if bool(data.get("melee_only", false)) and not melee:
			continue
		if bool(data.get("magic_only", false)) and not is_magic_hero(role):
			continue
		return item_id
	return ""
