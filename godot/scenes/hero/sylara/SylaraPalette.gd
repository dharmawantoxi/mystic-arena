# SylaraPalette.gd — palette terkontrol Sylara (v2 rebuild).
#
# Struktur sesuai disiplin pixel-art v2: setiap material punya ramp
# 4–5 nilai (BASE → SHADOW → MID → HIGHLIGHT → SHINE) dengan hue-shift
# halus — bayangan didinginkan, highlight dihangatkan — sehingga bentuk
# tetap tajam setelah di-scale & disinari (konsisten dengan key light
# kiri-atas LIGHT_DIR = (-1,-1) di lighting).
#
# IDENTITAS SYLARA (sumber: masterwork pygame `heroes/_bundle.py::_NS_sylara`,
# di-bake ke `assets/units/sylara.png`):
#   * Hood + jubah hijau hutan (ranger).
#   * RAMBUT ORANYE-MERAH berkibar — penanda identitas paling kuat.
#   * Kulit pucat hangat, mata hijau zamrud.
#   * Busur recurve kayu + quiver + armor kulit + gesper emas.
#   * Sihir angin hijau-muda = AKSEN saja (bukan dominan layar).
#
# Semua sistem Sylara (renderer, animator, skill FX, demo) mengambil warna
# dari sini — tidak ada warna liar.
extends Object

# ── Garis luar (outline tinta — siluet harus terbaca saat zoom out) ──
const INK := Color("#0a140c")

# ── Kulit: 5 nilai, bayangan didinginkan, highlight dihangatkan ──
const SKIN := Color("#f0c8aa")          # mid
const SKIN_DARK := Color("#d2a082")     # shadow
const SKIN_SHADE := Color("#9b6955")    # shadow gelap (dagu, lipatan)
const SKIN_LIGHT := Color("#fadcc3")    # highlight
const SKIN_HIGH := Color("#fff0dc")     # shine (tengkorok, hidung)
## Alias lama (dipakai skill FX / demo lama).
const SKIN_SHADOW := Color("#d2a082")

# ── Rambut ORANYE-MERAH — identitas utama (bukan hijau!) ──
const HAIR := Color("#c85523")          # mid
const HAIR_DARK := Color("#913219")     # shadow
const HAIR_DARKEST := Color("#55190f")  # shadow dalam
const HAIR_LIGHT := Color("#f08237")    # highlight
const HAIR_SHINE := Color("#ffb45f")    # kilai
const HAIR_HIGH := Color("#ffd68c")     # shine puncak (flicker)

# ── Jubah hijau hutan (cloth): 5 nilai ──
const CLOTH := Color("#3c6937")         # mid
const CLOTH_DARK := Color("#234123")    # shadow
const CLOTH_DARKEST := Color("#0f2314") # shadow dalam
const CLOTH_LIGHT := Color("#5f9650")   # highlight
const CLOTH_HIGH := Color("#8cc373")    # shine (rim angin)

# ── Hood / tudung — lebih gelap dari jubah ──
const HOOD := Color("#375f32")          # mid
const HOOD_DARK := Color("#1e371e")     # shadow
const HOOD_DARKEST := Color("#122414")  # bayangan dalam cowl
const HOOD_LIGHT := Color("#558746")    # highlight (pinggiran depan)

# ── Cape / jubah angin — identitas sekunder, sedikit lebih terang ──
const CAPE := Color("#416e37")          # mid
const CAPE_DARK := Color("#284b28")     # shadow
const CAPE_DARKEST := Color("#142819")  # shadow dalam
const CAPE_LIGHT := Color("#649b50")    # highlight
const CAPE_HIGH := Color("#94c676")     # shine (rim)

# ── Kayu busur recurve ──
const WOOD := Color("#825a32")          # mid
const WOOD_DARK := Color("#55371e")     # shadow
const WOOD_DARKEST := Color("#2d190f")  # shadow dalam (grip)
const WOOD_LIGHT := Color("#aa7d4b")    # highlight
const WOOD_SHINE := Color("#cda569")    # shine (horn, wring)

# ── Tali busur ──
const STRING := Color("#dcd2b4")
const STRING_DARK := Color("#9e9478")
const STRING_SHINE := Color("#faf5dc")

# ── Anak panah ──
const SHAFT := Color("#c8af82")
const SHAFT_DARK := Color("#8c6e46")
const HEAD := Color("#b4c3d2")
const HEAD_DARK := Color("#647388")
const HEAD_SHINE := Color("#ebf5ff")
const FEATHER := Color("#8cc85f")
const FEATHER_DARK := Color("#467837")

# ── Emas hardware (gesper, trim armor, quiver) ──
const GOLD := Color("#aa8228")          # mid
const GOLD_DARK := Color("#5f4614")     # shadow
const GOLD_LIGHT := Color("#e6c35a")    # highlight
const GOLD_HOT := Color("#ffec96")      # shine (glint)

# ── Armor kulit (vest, belt, boots, quiver) ──
const LEATHER := Color("#6e4b2d")       # mid
const LEATHER_DARK := Color("#462d19")  # shadow
const LEATHER_DARKEST := Color("#23140a")
const LEATHER_LIGHT := Color("#9b6e46") # highlight
const LEATHER_HIGH := Color("#c69660")  # shine (tutup sepatu)
const QUIVER := Color("#462d19")        # badan quiver (kulit gelap)
const QUIVER_DARK := Color("#23140a")
const QUIVER_LIGHT := Color("#9b6e46")

# ── MAGIC ACCENT — angin hijau. HANYA aksen, jangan mendominasi layar. ──
const WIND := Color("#6ec35a")          # mid
const WIND_DEEP := Color("#143c19")     # shadow (telegraph tanah)
const WIND_DARK := Color("#327832")     # shadow terang
const WIND_LIGHT := Color("#aaeb87")    # highlight
const WIND_BRIGHT := Color("#d2ffaf")   # bright (intim)
const WIND_WHITE := Color("#f0ffdc")    # white (inti)

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

# ── Wajah & tanah ──
const EYE := Color("#78d246")           # iris zamrud — titik fokus wajah
const EYE_WHITE := Color("#f0f8ff")
const RIM := Color("#d6f0c8")           # rim light hangat-hijau dari atas-kiri
const SHADOW_GROUND := Color(0.02, 0.05, 0.02, 0.30)
const DUST := Color("#8c6e46")          # debu kontak kaki
const HURT_TINT := Color(1.0, 0.32, 0.24)
