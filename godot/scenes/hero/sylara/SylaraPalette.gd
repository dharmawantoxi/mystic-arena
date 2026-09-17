# SylaraPalette.gd — palette terkontrol Sylara (Godot 4.x rebuild).
#
# Struktur palette sesuai standar FX proyek:
#   BASE → SHADOW → HIGHLIGHT → MAGIC ACCENT
# Semua sistem Sylara (renderer, animator, skill FX) mengambil warna dari
# sini supaya identitas visual konsisten dan tidak ada warna liar.
#
# PASS PIXEL-ART (v3, 2026-09-17): nilai warna di-tune ulang baris demi
# baris terhadap referensi sprite sheet "Wind Ranger — The Wind's Arrow"
# (pixel art: rambut oranye terang, hood + jubah hijau hutan, sihir angin
# hijau-kuning). Nama konstan TIDAK berubah supaya seluruh pemakai
# (SylaraRenderer/SkillFX/Feel/Arrow) tetap kompilasi.
extends Object

# ── Garis luar (outline tinta pixel-art — hijau-hitam pekat sheet) ──
const INK := Color("#101810")
const INK_SOFT := Color(0.06, 0.12, 0.08, 0.65)

# ── Kulit: cerah hangat khas sprite sheet ──
const SKIN := Color("#f6d7b3")
const SKIN_SHADOW := Color("#d8a878")
const SKIN_DEEP := Color("#b07e52")
const SKIN_LIGHT := Color("#ffe9cf")
const SKIN_BLUSH := Color("#ee8478")
const LIP := Color("#d66462")
const LIP_SHINE := Color("#ff9896")

# ── Rambut: oranye-merah terang (sheet) dengan kilau tembaga ──
const HAIR := Color("#c94f22")
const HAIR_DARK := Color("#8a2f12")
const HAIR_LIGHT := Color("#e06a30")
const HAIR_SHINE := Color("#f08a48")

# ── Jubah hijau (cloth): hijau hutan sheet ──
const CLOTH := Color("#3f8232")
const CLOTH_DARK := Color("#2a5c22")
const CLOTH_LIGHT := Color("#58a044")
const CLOTH_SHINE := Color("#74bc58")
const CLOTH_TRIM := Color("#dba232")

# ── Hood / tudung runcing — hijau sedang sheet ──
const HOOD := Color("#35722c")
const HOOD_DARK := Color("#1e4a1a")
const HOOD_LIGHT := Color("#4c9440")

# ── Cape / selendang — hijau gelap mengalir ke bawah-belakang ──
const CAPE := Color("#2f6d2a")
const CAPE_DARK := Color("#1c451a")
const CAPE_LIGHT := Color("#47953a")
const CAPE_BRIGHT := Color("#63b650")

# ── Kayu busur recurve keemasan (sheet: busur cokelat-emas) ──
const WOOD := Color("#8a5a28")
const WOOD_DARK := Color("#5a3814")
const WOOD_LIGHT := Color("#b07c3c")
const WOOD_SHINE := Color("#d09c58")
const HORN_TIP := Color("#ede4d0")

# ── Tali busur: benang pucat; glow hijau saat ditarik ──
const STRING := Color("#e6f2da")
const STRING_DARK := Color("#9ab888")
const STRING_GLOW := Color("#a8f878")

# ── Anak panah wind-ranger ──
const SHAFT := Color("#c8af82")
const SHAFT_DARK := Color("#8c6e46")
const HEAD := Color("#d6e4f0")
const HEAD_DARK := Color("#7088a4")
const HEAD_SHINE := Color("#f4faff")
const FEATHER := Color("#5ce078")
const FEATHER_DARK := Color("#2c8c44")

# ── Emas hardware (gesper, trim armor, quiver band, clasp) ──
const GOLD := Color("#d8a832")
const GOLD_DARK := Color("#7c5614")
const GOLD_LIGHT := Color("#fcd25a")
const GOLD_HOT := Color("#fff4aa")

# ── Armor kulit: boots lutut, belt, bracer, quiver ──
const LEATHER := Color("#7b4a24")
const LEATHER_DARK := Color("#4e2c12")
const LEATHER_LIGHT := Color("#a06a36")
const LEATHER_SHINE := Color("#c08848")

# ── MAGIC ACCENT — angin hijau-kuning bercahaya (powershot sheet) ──
const WIND := Color("#6ee848")
const WIND_DEEP := Color("#143c10")
const WIND_DARK := Color("#2e8820")
const WIND_LIGHT := Color("#a8f878")
const WIND_BRIGHT := Color("#d8ffc0")
const WIND_WHITE := Color("#f4ffe8")

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

# ── Mata zamrud pemanah ──
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
