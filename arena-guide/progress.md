# Progress Porting Mystic Arena (Pygame -> Godot 4)

Catatan langkah porting dan status verifikasi per 2026-09-23.

## Ringkasan Langkah

| No  | Modul / Fitur | Status |
| --- | ------------- | ------ |
| L01 | Main bootstrap, window 1600x900, camera scroll/zoom | DONE |
| L02 | Dual background map (map.png vs fallback grid) | DONE |
| L03 | Base tower structure (Radiant vs Dire base & tower) | DONE |
| L04 | Lane waypoints & pathing 3 lanes (Top, Mid, Bot) | DONE |
| L05 | Minion spawning waves & creep AI (aggro, attack, path) | DONE |
| L06 | Hero controller (WASD + Right-Click move, attack target) | DONE |
| L07 | Hero stats, HP/MP bars, XP bar, Level up system | DONE |
| L08 | Hero skills Q, W, E, R (cooldown, cost, area damage, VFX) | DONE |
| L09 | Item system: 33 items, catalog, inventory 6 slots | DONE |
| L10 | Shop UI: buy, sell (70%), inventory dock, drag/drop | DONE |
| L11 | Tower AI: target priority, attack projectile, destruction | DONE |
| L12 | Base Core: destruction condition, victory/defeat banner | DONE |
| L13 | Jungle camps: 4 neutral creep camps, respawn timer | DONE |
| L14 | Jungle Boss: Leviathan pit, special attacks, team buff | DONE |
| L15 | Fog of War (TileMap / CanvasItem reveal system) | DONE |
| L16 | Minimap 1:1 pygame: terrain, towers, hero dot, minion dots | DONE |
| L17 | HUD Bottom: hero portrait, HP/MP/XP, skill buttons, CD | DONE |
| L18 | HUD Top: game clock, kill score Radiant vs Dire, team gold | DONE |
| L19 | Sound Manager: SFX attack, skill, buy, death, victory | DONE |
| L20 | Visual polish: damage numbers float, attack trails, hit VFX | DONE |
| L21 | Settings menu: Audio sliders, hotkey remap, fullscreen | DONE |
| L22 | Pause menu & Game Over summary screen | DONE |
| L23 | Hero select screen: 6 starter heroes (Kaizen, Grimjaw, Sylara, ...) | DONE |
| L24 | Enemy AI Hero: simple lane farming, retreat at low HP, combo | DONE |
| L25 | Scoreboard (TAB modal): KDA, CS, Net Worth, items for all 10 heroes | DONE |
| L26 | Chat & ping system: Alt+Click ping alert on map/minimap | DONE |
| L27 | Replay system / spectator camera free-roam mode | DONE |
| L28 | Performance profiler: FPS, draw calls, creep count clamp | DONE |
| L29 | Balance audit vs Pygame: match HP/DMG/armor/scaling numbers | DONE |
| L30 | Final export setup: Windows, Linux, HTML5 presets | DONE |
| L31 | Side panel taktis 1:1 pygame (stats, tactical buttons, hotkeys) | **SNIPPET SIAP 2026-09-23** |
| L32 | Paritas visual minimap 1:1 pygame (garis lane, ikon tower/hero) | **DONE 2026-09-23** |
| L33 | tactical 5 penuh G/T/C/B/D + hotkey (gather/tower/castle/boss/DD) | **SNIPPET SIAP 2026-09-23** |
| L34 | audit visual Item Forge 1:1 pygame vs Godot (panel 1100x720, kartu 250px, ikon 56px, grid 4x2, tab kelas, inv 6) | **AUDIT DONE 2026-09-23** |
| L35 | visual Item Forge 1:1 pygame (panel 1100x720, kartu 250x200, ikon 56px, grid 4x2, 6 tab kelas, inv 6 slot jual 70%, popup detail) | **VERIFIED 1.png 2026-09-23** |
| L36 | Hero Shrine / Hero Shop (6 starter heroes Kaizen, Grimjaw, Sylara, Vex, Thorne, Zephyr, compact 480x145 cards, transfer inventory, swap QWER skill kit) | **VERIFIED 2026-09-23** |
| L37 | Paritas Logika Tempur Hero & Item (Mitigasi Armor MOBA, Crit 25%, Cleave 45%, Lifesteal/Blood Frenzy, Out-of-combat Regen, Holy Rapier drop, Skill QWER 6 hero) | **DONE 2026-09-23** |
| L38 | Paritas Tower AI (Tower Dive Aggro, 4 Tipe Menara Archer/Cannon/Ice/Mage, Shield) & Minion Wave (5 Tipe Goblin/Orc/Troll/Undead/Dark Rider, Last-Hit Bounty) | **DONE 2026-09-23** |

## File baru

- `arena-guide/scripts/SidePanel.gd` + `steps/L31-side-panel.gd` + `steps/L33-tactical-full.gd` (tactical full)
- `arena-guide/docs/AUDIT_ITEM_FORGE.md` (audit item forge 1:1 pygame vs godot)
- `arena-guide/scripts/Shop.gd` + `godot/scripts/Shop.gd` (visual item forge + hero shrine 1:1 pygame)
- `arena-guide/steps/L36-hero-shrine.gd` (hero shrine compact cards & switch logic)
- `arena-guide/scripts/Hero.gd` + `godot/scripts/Hero.gd` + `steps/L37-combat-parity.gd` (combat logic parity)
- `arena-guide/scripts/Tower.gd` + `godot/scripts/Tower.gd` + `arena-guide/scripts/Minion.gd` + `godot/scripts/Minion.gd` + `steps/L38-tower-minion-parity.gd` (tower & minion parity)
