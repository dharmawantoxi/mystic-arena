# AUDIT VISUAL ITEM FORGE 1:1: PYGAME VS GODOT

> Sumber acuan Pygame final: `hero_items.py` (ItemShopUI: baris 3190–4150), `_core.py`, `_render.py`, `assets/items/` (33 PNG ikon).  
> Target Godot: `godot/scenes/ui/ShopPanel.gd`, `godot/scenes/ui/widgets/ItemForgeCard.gd`, `godot/scripts/utils/ItemIcons.gd`, `godot/scripts/core/ItemDB.gd`, `godot/scripts/core/HeroItems.gd`, `arena-guide/scripts/Shop.gd`.

---

## 1. Ringkasan Eksekutif Paritas

| Parameter | Sumber Pygame (`hero_items.py`) | Godot `ShopPanel.gd` / `ItemForgeCard.gd` | Godot `Shop.gd` (`arena-guide`) | Status Paritas |
|---|---|---|---|---|
| **Katalog Item** | 33 item lengkap (stats, active, passive, glow, color) | 33 item via `items.json` & `ItemDB.gd` | 33 item di `ITEM_CATALOG` | **LOGIK 33 LENGKAP** |
| **Dimensi Panel** | 1100 × 720 px (center pada 1280×720: `px=90, py=0`) | Modal adaptif / rail popup | 900 × 560 px (center `px=190, py=80`) | **DIVERGEN** (Shop.gd masih 900×560) |
| **Ukuran Kartu** | 250 × 200 px | 250 × 200 px (`ItemForgeCard.gd`) | 200 × 108 px | **DIVERGEN** (Shop.gd masih 200×108) |
| **Ukuran Ikon** | 56 × 56 px (`get_icon(sid, 56)`) di `(x+10, y+10)` | 56 × 56 px (`ItemIcons.texture(id, 56)`) | 36 × 36 px (kotak warna flat tanpa tekstur) | **DIVERGEN** (Shop.gd tanpa PNG) |
| **Format Grid** | 4 kolom × 2 baris (8 kartu per halaman) | 1–4 kolom (scroll vertikal per kategori) | 4 kolom × 3 baris (12 kartu per halaman) | **DIVERGEN** (ShopPanel scroll, Shop 4x3) |
| **Paginasi** | 6 tab kelas (`PHYSICAL 1/2`, `2/2`, `MAGIC 1/2`, `2/2`, `TANK 1/2`, `2/2`) | Scroll kontinu 33 kartu (tanpa tab kelas) | Paginasi angka `< PREV` `NEXT >` 3 halaman | **DIVERGEN** (belum ada tab kelas) |
| **Strip "BUY FOR:"** | Strip hero roster (h=42, nama, lv, used/6, dot warna) | Strip pill tombol sederhana | Belum ada (hanya hero aktif tunggal) | **PARSIAL** |
| **Ringkasan Hero** | Box 1060×49 px (`DMG->total`, `HP`, `Armor`, `AS`, `LS`, `CDR`, `RNG`) | 3 baris Label teks terpisah | Belum ada di Item Forge | **DIVERGEN** |
| **Inventory Bawah** | 6 slot (54×54 px, gap 8, label `INVENTORY`) | Tidak ada slot visual (hanya teks info) | 6 slot (48×32 px) di `py+ph-52` | **DIVERGEN** |
| **Sistem Jual (SELL)**| Klik kanan slot = Drop (Pygame) / Jual 70% (`Shop.gd`) | Belum ada refund item di `ShopPanel` | Klik kanan slot = Jual 70% refund | **PARITAS LOGIK DI SHOP.GD** |
| **Popup Detail Modal**| Modal 880×600 px (2 kolom stats, deskripsi, badges, flavor) | Belum diimplementasikan | Belum diimplementasikan | **BELUM ADA DI KEDUA FILE** |

---

## 2. Bedah Detail Visual 1:1

### A. Geometri Panel Toko
- **Pygame (`ItemShopUI`)**:
  - Ukuran: Lebar `1100 px`, Tinggi `720 px`.
  - Posisi: `px = (1280 - 1100) // 2 = 90`, `py = (720 - 720) // 2 = 0`.
  - Latar Gelap Luar: `darken(surface, 215)` (~84% hitam transparan).
  - Bayangan Panel: Rect `1120 × 740` px di `(px - 10, py - 10)`, warna `(0, 0, 0, 160)`, `border_radius=15`.
  - Latar Dalam: Gradasi vertikal `(30, 34, 62)` ke `(15, 18, 36)`, `radius=14` (solid fallback: `Color8(22, 26, 44)`).
  - Border: Luar `Color8(255, 205, 90)` tebal 3 px, dalam `Color8(140, 110, 58)` tebal 1 px di `inset=3`.
  - Sudut Emas: `corner_ticks` panjang 16 px, lebar 2 px, `inset=8`.
- **Status Godot**:
  - `ShopPanel.gd` memakai layout modal adaptif dari `MobileLayout`.
  - `Shop.gd` masih memakai `pw=900, ph=560` (ukuran lama). Perlu diselaraskan menjadi `1100 × 720` px.

### B. Header Toko
- **Pygame**:
  - Judul: "ITEM FORGE" (Font `Cinzel` 46 px, center di `cx = 640`, `py + 32`). Glow radial `(255, 205, 90, 40)` ukuran 420×90 di tengah.
  - Chip Emas: Posisi `(px + 22, py + 18)`, label "GOLD", nilai format ribuan `f"{gold:,}"` warna `Color8(255, 220, 100)`.
  - Hint: `tr("item_card_detail_hint")` di kanan atas sebelum tombol X.
  - Tombol Tutup (X): Lingkaran diameter 44 px di `(px + PANEL_W - 56, 2)`, merah `Color8(180, 60, 60)` hover `(255, 90, 90)`, border putih 2 px, huruf "X" 28 px.

### C. Strip Pemilihan Hero ("BUY FOR:")
- **Pygame**:
  - Posisi: `y = py + 57`, tinggi `42 px`.
  - Label: `"BUY FOR:"` font 20 px semibold, warna `Color8(255, 220, 100)` di `px + 22`.
  - Area Chip: Lebar area hero dinamis, chip per hero lebar 110–180 px, tinggi 42 px, gap 8 px.
  - Render Chip: Latar `Color8(48, 64, 100)` (terpilih) / `Color8(26, 30, 48)` (tidak terpilih). Border 2 px warna hero / `Color8(70, 80, 110)`. Dot warna hero radius 6 px di `(x+14, y_mid)`.
  - Baris 1: Nama hero (font 19 px semibold, warna `Color8(240, 245, 255)`).
  - Baris 2: Status `"Lv.{level}  Item {used}/6"` (atau `"DEAD"` / antrean), font 14 px.

### D. Banner Informasi Statistik Hero
- **Pygame**:
  - Kotak: Rect `(px + 20, py + 105, 1060, 49)`, radius 8. Latar `Color8(30, 36, 58)`, border warna hero 2 px.
  - Baris 1: `{Hero Name}  Lv.{level}` (font 20 px semibold, warna hero).
  - Baris 2: `{MELEE/RANGED} {MAGIC}   DMG {base}->{total}   HP {max}   Armor {arm}   AS x{as:.2f}   LS {ls}%   CDR {cdr}% {+RNG}` (font 16 px, warna `Color8(200, 210, 230)`).
  - Indikator Mati: Pesan `"Item dikirim setelah respawn"` di kanan atas box warna `Color8(255, 175, 175)`.

### E. Tab Kategori & Paginasi (Grid 4x2)
- **Pygame**:
  - Halaman terbagi 6 tab berdasarkan batas kelas (`HeroItems.build_shop_pages`):
    1. `PHYSICAL 1/2` (8 item): dead_edge, holy_rapier, demon_maw, cleave_axe, moon_shard, monarch_wings, corroder, fenrir_chain.
    2. `PHYSICAL 2/2` (6 item): sanguine_thorn, thunder_coil, sundering_cudgel, frostbound_eye, gale_pike, basilisk_breath.
    3. `MAGIC 1/2` (8 item): octarine_core, runic_gavel, astral_codex, sage_scepter, fulgur_scepter, hex_idol, rift_veil, vital_stone.
    4. `MAGIC 2/2` (2 item): vine_rod, spectral_charm.
    5. `TANK 1/2` (8 item): leviathan_heart, steel_aegis, scarlet_bulwark, tempest_vane, abyss_breaker, razor_carapace, everfrost_guard, solar_brand.
    6. `TANK 2/2` (1 item): searbrand.
  - Posisi Tab: `y = py + 160`, tinggi `36 px`, gap `10 px`.
  - Warna Tab:
    - PHYSICAL: `Color8(255, 150, 80)`
    - MAGIC: `Color8(200, 145, 255)`
    - TANK: `Color8(115, 225, 145)`
  - Grid Item: Posisi `start_x = px + 32 = 122`, `start_y = py + 202 = 202`.
    - 4 kolom × 2 baris (maks 8 kartu per halaman).
    - Jarak horizontal (`gap_x`) = 12 px, jarak vertikal (`gap_y`) = 14 px.
    - Total ukuran grid: `(4 × 250) + (3 × 12) = 1036 px` lebar, `(2 × 200) + 14 = 414 px` tinggi.

### F. Kartu Item (`ItemForgeCard`)
- **Pygame Visual**:
  - Ukuran: `250 px × 200 px`, `border_radius=8`.
  - Latar: Gradasi vertikal `Color8(34, 40, 68)` ke `Color8(17, 20, 38)` (bisa beli) / `Color8(26, 26, 38)` ke `Color8(16, 16, 26)` (tidak bisa beli).
  - Border: Warna katalog item `data["color"]` (bisa beli) / `Color8(70, 70, 80)` (tidak bisa beli), tebal 2 px.
  - Sudut Emas: Ticks emas 9 px di 4 sudut jika `can_buy`.
  - Ikon: Ukuran `56 × 56 px` di koordinat lokal `(10, 10)`, dimuat via `ItemIcons.texture(id, 56)`.
  - Badge Kelas: Kanan atas `(x + 250 - badge_w - 8, 8, badge_w, 20)`, bg `Color8(18, 22, 36)`, border 1 px warna kelas, teks font 14 px bold.
  - Nama Item: Di `(74, 12)`, font 24 px bold, warna `data["glow"]`, teks terpotong rapi dengan elipsis.
  - Badge Kategori: Di `(74, 38)`, font 17 px bold, warna kategori (`CATEGORY_INFO`).
  - Harga: Di `(74, 56)`, font 21 px bold, teks `"{cost}G"`, warna emas `Color8(255, 220, 100)` (mampu) / merah `Color8(200, 80, 80)` (tidak mampu).
  - Jumlah Dimiliki: Di `(250 - 90, 58)`, font 17 px bold, warna hijau `Color8(150, 255, 170)`, teks `"Owned: {count}"`.
  - Deskripsi: Dimulai `y = 84`, font 17 px medium, warna `Color8(220, 225, 240)`, wrap maksimal 230 px (`w - 20`), maksimal 4 baris (baris ke-4 dipotong + `…`).
  - Tombol Beli (Pill): Rect `(10, 166, 230, 26)`:
    - `BUY`: Font 18 px bold, gaya hijau success (bg `Color8(48, 100, 64)`, border `Color8(120, 235, 140)`).
    - Status Tidak Bisa: `"MELEE ONLY"`, `"MAGIC ONLY"`, `"NOT AFFORDABLE"`, atau `"SELECT HERO"`, font 14 px bold, gaya locked (bg `Color8(44, 44, 54)`, border `Color8(90, 90, 100)`).

### G. Strip Inventory Bawah (6 Slot) & Mekanisme Jual 70%
- **Pygame**:
  - Posisi: `sy = py + 720 - 66 = 654`.
  - Label: `INVENTORY` di `y = 632`, font 17 px semibold, warna `Color8(170, 180, 205)`.
  - Hint: `tr("item_inventory_hint")` ("Klik slot untuk detail / klik kanan untuk buang").
  - 6 Slot Kotak: Ukuran `54 × 54 px`, `gap = 8 px`. Total lebar = `(6 × 54) + (5 × 8) = 364 px`.
  - Posisi `sx = px + (1100 - 364) // 2 = 90 + 368 = 458`.
  - Slot Kosong: Latar `Color8(14, 17, 30)`, border `Color8(66, 74, 104)` 1 px.
  - Slot Terisi: Latar `Color8(14, 17, 30)`, border warna item `data["color"]` 2 px, ikon item `48 × 48 px` di `(x+3, y+3)`.
  - Interaksi:
    - Klik Kiri slot terisi: Buka popup detail item modal.
    - Klik Kanan / Tahan: Jual item dengan refund 70% (`refund = int(cost * 0.7)`).

---

## 3. Rencana Patch Terstruktur (Roadmap Giliran Berikutnya)

1. **Patch 1: `ShopPanel.gd`**
   - Integrasikan 6 tab kelas paginasi (`PHYSICAL 1/2`, `2/2`, `MAGIC 1/2`, `2/2`, `TANK 1/2`, `2/2`) menggantikan scroll kontinu panjang.
   - Tetapkan grid kartu 4 kolom × 2 baris (8 kartu per halaman) di-center dengan rapi.
   - Tambahkan strip visual 6 slot Inventory di bagian bawah panel lengkap dengan ikon 48px dan aksi klik kanan jual (refund 70%).
   - Tampilkan banner ringkasan stat hero 2-baris sesuai format Pygame (`DMG`, `HP`, `Armor`, `AS`, `LS`, `CDR`, `RNG`).

2. **Patch 2: `ItemForgeCard.gd`**
   - Pastikan interaksi klik kartu membuka modal popup detail, sedangkan tombol BUY mengeksekusi pembelian.
   - Sinkronisasi visual pixel-perfect (ikon 56px, badge, nama glow, cost emas/merah, pill BUY/locked).

3. **Patch 3: `Shop.gd` (`arena-guide/scripts/Shop.gd` & `godot/scripts/Shop.gd`)**
   - Perbarui geometri panel dari 900×560 menjadi 1100×720.
   - Perbarui ukuran kartu dari 200×108 menjadi 250×200.
   - Ganti rendering ikon kotak warna flat 36px dengan `ItemIcons.texture(id, 56)` 56px.
   - Samakan layout grid menjadi 4 kolom × 2 baris (8 kartu) dan slot inventory 54×54 px.

4. **Patch 4: `ItemIcons.gd`**
   - Pastikan dukungan ukuran tekstur untuk semua titik pemanggilan: 56px (kartu toko), 48px (slot inventory), 64px (popup detail), dan 26px (HUD).
