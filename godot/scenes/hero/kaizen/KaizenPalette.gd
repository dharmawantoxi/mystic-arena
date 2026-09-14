# KaizenPalette.gd — palette terkontrol Kaizen (v4 Godot rebuild).
#
# Struktur palette sesuai standar FX proyek:
#   BASE → SHADOW → HIGHLIGHT → MAGIC ACCENT
# Semua sistem Kaizen (renderer, animator, skill FX) mengambil warna dari
# sini supaya identitas visual konsisten dan tidak ada warna liar.
#
# Identitas Kaizen: indigo pekat (gi/hakama) + baja dingin (katana) +
# emas redup (trim) + sihir angin cyan-putih sebagai AKSEN (bukan dominan).
extends Object

# ── Garis luar (outline tinta — siluet harus terbaca saat zoom out) ──
const INK := Color("#141116")

# ── Kulit: BASE / SHADOW / HIGHLIGHT ──
const SKIN := Color("#c49670")
const SKIN_SHADOW := Color("#9e7256")
const SKIN_LIGHT := Color("#e2ba92")

# ── Rambut ──
const HAIR := Color("#342a22")
const HAIR_LIGHT := Color("#8c6a46")

# ── Gi indigo (baju): BASE / SHADOW / HIGHLIGHT ──
const CLOTH := Color("#3e5486")
const CLOTH_DARK := Color("#263256")
const CLOTH_LIGHT := Color("#668ac2")

# ── Hakama (celana rok) — selangkah lebih gelap dari gi ──
const HAKAMA := Color("#2a3760")
const HAKAMA_DARK := Color("#1e2846")

# ── Scarf angin — warna identitas sekunder ──
const SCARF := Color("#5482ce")
const SCARF_DARK := Color("#2e4c94")
const SCARF_LIGHT := Color("#88b6f2")

# ── Baja katana ──
const STEEL := Color("#7e8694")
const STEEL_DARK := Color("#4c525e")
const STEEL_LIGHT := Color("#b8beca")
const STEEL_SHINE := Color("#e6ecf6")

# ── Emas redup (trim, tsuba, simpul obi) ──
const GOLD := Color("#e2ba52")
const GOLD_DARK := Color("#a87e2c")

# ── MAGIC ACCENT — angin. HANYA aksen, jangan mendominasi layar. ──
const WIND := Color("#70b2e6")
const WIND_DEEP := Color("#2e4c94")
const WIND_LIGHT := Color("#b0defa")
const WIND_BRIGHT := Color("#d8f2ff")

# ── Lain-lain ──
const EYE := Color("#e2a33c")          # iris amber — titik fokus wajah
const BAND := Color("#dfe8f4")         # hachimaki putih-biru
const BAND_SHADOW := Color("#a8bcd8")
const RIM := Color("#cfe4ff")          # rim light dingin dari atas-kiri
const SHADOW_GROUND := Color(0.02, 0.03, 0.07, 0.26)
const HURT_TINT := Color(1.0, 0.32, 0.24)
