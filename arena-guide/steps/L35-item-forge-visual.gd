# L35-item-forge-visual.gd — Implementasi 1:1 Item Forge Pygame di Godot (CanvasItem)
# Referensi: hero_items.py (ItemShopUI._draw_item_grid, _draw_item_card, _draw_owned_slots, _draw_detail_popup)
# Panel 1100x720, Kartu 250x200, Ikon 56px, Grid 4x2, 6 Tab Kelas, Inv 6 slot (Jual 70%), Popup Detail 880x520.

const MAX_SLOTS := 6
const ITEMS_PER_PAGE := 8
const COLS_ITEM := 4
const ITEM_COST := 100

const SHOP_PAGES: Array = [
	["dead_edge", "holy_rapier", "demon_maw", "cleave_axe", "moon_shard", "monarch_wings", "corroder", "fenrir_chain"],
	["sanguine_thorn", "thunder_coil", "sundering_cudgel", "frostbound_eye", "gale_pike", "basilisk_breath"],
	["octarine_core", "runic_gavel", "astral_codex", "sage_scepter", "fulgur_scepter", "hex_idol", "rift_veil", "vital_stone"],
	["vine_rod", "spectral_charm"],
	["leviathan_heart", "steel_aegis", "scarlet_bulwark", "tempest_vane", "abyss_breaker", "razor_carapace", "everfrost_guard", "solar_brand"],
	["searbrand"]
]

const PAGE_LABELS: Array = [
	"PHYSICAL 1/2", "PHYSICAL 2/2",
	"MAGIC 1/2", "MAGIC 2/2",
	"TANK 1/2", "TANK 2/2"
]

const PAGE_COLORS: Array = [
	Color8(255, 150, 80), Color8(255, 150, 80),
	Color8(200, 145, 255), Color8(200, 145, 255),
	Color8(115, 225, 145), Color8(115, 225, 145)
]
