# SylaraPalette.gd — palette terkontrol Sylara (Godot 4.x rebuild).
#
# Struktur palette sesuai standar FX proyek:
#   BASE → SHADOW → HIGHLIGHT → MAGIC ACCENT
# Semua sistem Sylara (renderer, animator, skill FX) mengambil warna dari
# sini supaya identitas visual konsisten dan tidak ada warna liar.
#
# Identitas Sylara: hijau hutan (jubah/hood) + emas daun (aksen hangat) +
# kayu busur recurve + sihir angin hijau-muda sebagai AKSEN (bukan dominan).
# Wind Ranger archer — busur, daun, angin laminar.
extends Object

# ── Garis luar (outline tinta — siluet harus terbaca saat zoom out) ──
const INK := Color("#09140c")

# ── Kulit: BASE / SHADOW / HIGHLIGHT ──
const SKIN := Color("#c8a882")
const SKIN_SHADOW := Color("#a07e5e")
const SKIN_LIGHT := Color("#e6ccb0")

# ── Rambut (hijau gelap / hitam kehijauan) ──
const HAIR := Color("#1a3018")
const HAIR_LIGHT := Color("#3a6832")

# ── Jubah hijau (cloth): BASE / SHADOW / HIGHLIGHT ──
const CLOTH := Color("#376234")
const CLOTH_DARK := Color("#1e3a1c")
const CLOTH_LIGHT := Color("#5e9650")

# ── Hood / tudung — sedikit lebih gelap dari jubah ──
const HOOD := Color("#2a4e26")
const HOOD_DARK := Color("#142e12")

# ── Cape / selendang angin — warna identitas sekunder ──
const CAPE := Color("#4a8842")
const CAPE_DARK := Color("#2c5a28")
const CAPE_LIGHT := Color("#72b866")

# ── Kayu busur recurve ──
const WOOD := Color("#825a32")
const WOOD_DARK := Color("#4e2e18")
const WOOD_LIGHT := Color("#aa7e4a")
const WOOD_SHINE := Color("#cda568")

# ── Tali busur ──
const STRING := Color("#dcd2b4")
const STRING_DARK := Color("#9e9478")

# ── Anak panah ──
const SHAFT := Color("#c8af82")
const SHAFT_DARK := Color("#8c6e46")
const HEAD := Color("#b4c3d2")
const HEAD_DARK := Color("#647388")
const HEAD_SHINE := Color("#ebf5ff")
const FEATHER := Color("#8cc85e")
const FEATHER_DARK := Color("#467838")

# ── Emas hardware (gesper, trim armor, quiver) ──
const GOLD := Color("#aa8228")
const GOLD_DARK := Color("#5e4614")
const GOLD_LIGHT := Color("#e6c35a")
const GOLD_HOT := Color("#ffec96")

# ── Armor kulit ──
const LEATHER := Color("#6e5030")
const LEATHER_DARK := Color("#3e2c1a")
const LEATHER_LIGHT := Color("#96724a")

# ── MAGIC ACCENT — angin hijau. HANYA aksen, jangan mendominasi layar. ──
const WIND := Color("#6ec35a")
const WIND_DEEP := Color("#143c10")
const WIND_DARK := Color("#327832")
const WIND_LIGHT := Color("#aaeb88")
const WIND_BRIGHT := Color("#d2ffb0")
const WIND_WHITE := Color("#e8ffd6")

# ── Daun (aksen hangat satu-satunya) ──
const LEAF := Color("#92a834")
const LEAF_DARK := Color("#4e601e")
const LEAF_GOLD := Color("#c4d648")
const LEAF_EMBER := Color("#eca83a")
const LEAF_PALE := Color("#f2f0a8")

# ── Sulur Shackle (E) ──
const VINE := Color("#427c38")
const VINE_DARK := Color("#183e1e")
const VINE_LIGHT := Color("#80be60")

# ── Lain-lain ──
const EYE := Color("#78d246")          # iris hijau terang — titik fokus wajah
const QUIVER := Color("#5a3e22")       # quiver kulit
const QUIVER_DARK := Color("#342214")
const RIM := Color("#d6f0c8")          # rim light hangat-hijau dari atas-kiri
const SHADOW_GROUND := Color(0.02, 0.05, 0.02, 0.26)
const HURT_TINT := Color(1.0, 0.32, 0.24)
