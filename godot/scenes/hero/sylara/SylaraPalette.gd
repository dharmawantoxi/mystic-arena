# SylaraPalette.gd — palette terkontrol Sylara (Godot 4.x rebuild).
#
# Struktur palette sesuai standar FX proyek:
#   BASE → SHADOW → HIGHLIGHT → MAGIC ACCENT
# Semua sistem Sylara (renderer, animator, skill FX) mengambil warna dari
# sini supaya identitas visual konsisten dan tidak ada warna liar.
#
# Identitas Sylara: Elven Wind Ranger — rambut auburn hangat + jubah hijau
# hutan + korset kulit bergesper emas + sihir angin zamrud bercahaya.
extends Object

# ── Garis luar (outline tinta — halus & elegan, bukan hitam mati kasar) ──
const INK := Color("#0c1c10")
const INK_SOFT := Color(0.06, 0.12, 0.08, 0.65)

# ── Kulit elven: porselen hangat bercahaya, blush pipi lembut & bibir mawar ──
const SKIN := Color("#fae4d4")
const SKIN_SHADOW := Color("#d69e82")
const SKIN_DEEP := Color("#b0765c")
const SKIN_LIGHT := Color("#fff5ec")
const SKIN_BLUSH := Color("#ee8478")
const LIP := Color("#d66462")
const LIP_SHINE := Color("#ff9896")

# ── Rambut: auburn tembaga hangat berkilau (sesuai konsep masterwork) ──
const HAIR := Color("#7e3518")
const HAIR_DARK := Color("#461c0a")
const HAIR_LIGHT := Color("#b65e28")
const HAIR_SHINE := Color("#e28c50")

# ── Jubah hijau (cloth): hijau zamrud hutan beludru ──
const CLOTH := Color("#2c5a32")
const CLOTH_DARK := Color("#16381c")
const CLOTH_LIGHT := Color("#4a8a52")
const CLOTH_SHINE := Color("#6cb874")
const CLOTH_TRIM := Color("#dba232")

# ── Hood / tudung — cowl fitted yang membingkai wajah elven ──
const HOOD := Color("#224c28")
const HOOD_DARK := Color("#122e18")
const HOOD_LIGHT := Color("#387842")

# ── Cape / selendang angin berlapis — berkibar dinamis ──
const CAPE := Color("#387a3e")
const CAPE_DARK := Color("#204e26")
const CAPE_LIGHT := Color("#58a85e")
const CAPE_BRIGHT := Color("#7ecc82")

# ── Kayu busur pusaka recurve (aged ironwood + urat emas) ──
const WOOD := Color("#7c5228")
const WOOD_DARK := Color("#482c14")
const WOOD_LIGHT := Color("#a4723e")
const WOOD_SHINE := Color("#cca05c")
const HORN_TIP := Color("#ede4d0")

# ── Tali busur: benang angin ajaib bercahaya (luminous mana string) ──
const STRING := Color("#90ffcc")
const STRING_DARK := Color("#38b47a")
const STRING_GLOW := Color("#40e890")

# ── Anak panah wind-ranger ──
const SHAFT := Color("#c8af82")
const SHAFT_DARK := Color("#8c6e46")
const HEAD := Color("#c6dcf0")
const HEAD_DARK := Color("#7088a4")
const HEAD_SHINE := Color("#f4faff")
const FEATHER := Color("#5ce078")
const FEATHER_DARK := Color("#2c8c44")

# ── Emas hardware (gesper, trim armor, quiver band, clasp) ──
const GOLD := Color("#dba232")
const GOLD_DARK := Color("#7c5614")
const GOLD_LIGHT := Color("#fcd25a")
const GOLD_HOT := Color("#fff4aa")

# ── Armor kulit: korset & bracer kulit lentur berkualitas tinggi ──
const LEATHER := Color("#704626")
const LEATHER_DARK := Color("#442612")
const LEATHER_LIGHT := Color("#9a6438")
const LEATHER_SHINE := Color("#c68a52")

# ── MAGIC ACCENT — angin hijau mint bercahaya ──
const WIND := Color("#4eed98")
const WIND_DEEP := Color("#143c1c")
const WIND_DARK := Color("#2a8848")
const WIND_LIGHT := Color("#96ffcc")
const WIND_BRIGHT := Color("#c6ffea")
const WIND_WHITE := Color("#f2fff8")

# ── Daun (aksen alam berhamburan) ──
const LEAF := Color("#add834")
const LEAF_DARK := Color("#58741c")
const LEAF_GOLD := Color("#eaf24e")
const LEAF_EMBER := Color("#f4b03c")
const LEAF_PALE := Color("#f8f8b8")

# ── Sulur Shackle (E) ──
const VINE := Color("#3a7c36")
const VINE_DARK := Color("#183e1c")
const VINE_LIGHT := Color("#76c860")

# ── Mata elven bercahaya (emerald catchlights) ──
const EYE := Color("#38b846")
const EYE_DARK := Color("#165c22")
const EYE_LIGHT := Color("#78f060")
const EYE_WHITE := Color("#f6fbf8")

# ── Perlengkapan & Efek ──
const QUIVER := Color("#583c22")
const QUIVER_DARK := Color("#342012")
const RIM := Color("#d8ffdc")
const SHADOW_GROUND := Color(0.02, 0.05, 0.02, 0.28)
const HURT_TINT := Color(1.0, 0.32, 0.28)
