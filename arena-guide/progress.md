# Progress — mystic-godot-471 (port manual Godot)

> Untuk agent di chat baru: baca seluruh file ini sebelum menjawab user.

## Status terakhir

- **L37 (PARITAS ARMOR/DAMAGE — logika, langkah pertama scope pygame-sync):
  SNIPPET SIAP 2026-09-24.** File baru `scripts/CombatCalc.gd` (formula 1:1
  `_entity.py`); `Hero.gd`/`Minion.gd`/`Tower.gd`/`Nexus.gd` signature
  `take_damage(amount, school := "")` + gate school; armor dasar hero 0
  (item-only), tower 3 (2+level), minion 0, nexus 0 (shield = langkah lain).
  Skill Q/E → "magic" (tembus armor, angka tetap 60/35); auto-attack hero →
  "physical". Verifikasi lokal: gdparse OK semua file + uji aritmetika
  20.000 kasus vs blok pygame verbatim = 0 selisih. `steps/L37-armor-parity.gd`.
- **Perbaikan arsip 2026-09-24 (bukan langkah):** `scripts/Main.gd` punya 2
  baris sisa-instruksi TANPA `#` (asal L27 & L17) yang membuat file gagal
  parse bila ditempel utuh — kini dikomentari. `project/Main.gd` (salinan
  user) punya 1 artefak serupa di baris 195 yang TIDAK disentuh (aturan:
  project/ hanya dari paste user; file asli user jelas jalan — L31 verified).
- **L31 (panel kanan bata + STATUS/HERO/SKILL/TACTICAL): PASANG & VERIFIED 2026-09-23.**
  Screenshot user `1.png` → panel 344px bata, STATUS GOLD/LV/Wave, HEROES Kaizen 550, SKILLS QWER, TACTICAL 5 tombol — 100% parity `mobile/sidepanel.py`. Viewport 1624x720 OK.
- **L33 2026-09-23 — TACTICAL FULL (G/T/C/B/D): SNIPPET SIAP.** Stub L31 (`print` + gather mini) → 5 perintah penuh: GATHER (250,580), PROTECT TOWER (tower biru terdekat/slot), PROTECT CASTLE (BASE_BLUE), ATTACK BOSS (640,360 tengah sungai), ATTACK DD (musuh terdekat → nexus). + hotkey G/T/C/B/D. `scripts/Main.gd` + `SidePanel.gd` + `FULL_L31` updated, `steps/L33-tactical-full.gd` baru.
- L30 lane-clean **REVISI 2026-09-23 — DIKEMBALIKAN KE PYGAME FINAL**: L30a mid-smooth
  (280,450...) DIBATALKAN atas instruksi user — lane harus 1:1 pygame. L30b/c
  (hapus cobble + hide hint) TETAP. `scripts/Main.gd` + `project/Main_FULL_L31.gd`
  + `steps/L30` sudah sync ke waypoint pygame `map_components/_bundle.py`.
- **L32 2026-09-23 — FIX PATAH + RAPAT CASTLE (dari screenshot 1.png) DIBATALKAN:**
  Atas instruksi user kedua “samakan dengan pygame game saja”, L32 halus (TOP+1wp,
  BOT geser, MID halus, SMOOTH 14, BASE_RED 1180) **DIKEMBALIKAN ke PYGAME FINAL**
  `map_components/_bundle.py`. `scripts/Main.gd` + `FULL_L31` kembali ke TOP
  (120,220/170,180/240,100), MID (300,420... 65°), BOT (1070,620/1170,500),
  SMOOTH [10,8,10], BASE_RED 1145,175 (spase 35px memang ada di pygame). L32
  snippet diarsipkan sebagai referensi visual saja, tidak dipakai.
- L29 heartbeat DONE. Audit map #1–#6 DONE. **Audit lane 2026-09-23 FINAL: 100%
  PYGAME — TOP 12wp / MID 9wp / BOT 11wp / RIVER 7wp + smooth [10,8,10] + trunc
  int(x),int(y). Patah & spase di 1.png memang ada di pygame asli.**
- `project/Main.gd` = pasca-L29 (sudah paritas, belum L31). `scripts/Main.gd` = L15-L29 + L30b/c + L31 panneau + L33 tactical full.
- CATATAN PLATFORM: fetch → reset --soft origin/branch → add → commit → push.

## Geometri panel (pygame paritas)

- VIEW 1624x720; ARENA 0..1280; PANEL_X=1280 PANEL_W=344
- Latar bata 16px path_stone + outline
- Zona: pause y14 | STATUS ~96 | HEROES | SKILLS QWER | TACTICAL 5 tombol

## Jejak

| Step | Isi | Status |
|---|---|---|
| L15–L29 | map parity + heartbeat | DONE |
| L30 | REVISI pygame: kembalikan mid ke (300,420...) + no cobble + hide hint | **SYNC PYGAME 2026-09-23** |
| L31 | side panel brick + status/hero/skill/tactical | **PASANG & VERIFIED 1.png 2026-09-23** |
| L32 | halus patah + rapat castle → **DIBATALKAN** per instruksi “samakan pygame” | **ARSIP — KEMBALI PYGAME FINAL** |
| L33 | tactical 5 penuh G/T/C/B/D + hotkey (gather/tower/castle/boss/DD) | **SNIPPET SIAP 2026-09-23** |
| L34–L36 | shop: 33 item + JUAL 70% + hero shrine (kode sudah terpasang di `scripts/Shop.gd` + integrasi `scripts/Main.gd` `# L34 shop`) | **TERPASANG (arsip 2026-09-23)** |
| L37 | paritas armor/damage: CombatCalc + school physical/magic, armor hero 0/tower 3/minion 0 | **SNIPPET SIAP 2026-09-24** |

## File baru

- `arena-guide/scripts/SidePanel.gd` + `steps/L31-side-panel.gd` + `steps/L33-tactical-full.gd` (tactical full)
- `arena-guide/scripts/CombatCalc.gd` (BARU L37) + `scripts/Hero.gd`/`Minion.gd`/`Tower.gd`/`Nexus.gd` versi L37 + `steps/L37-armor-parity.gd`
