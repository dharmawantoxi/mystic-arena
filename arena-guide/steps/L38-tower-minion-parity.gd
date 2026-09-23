# L38-tower-minion-parity.gd — Paritas Tower AI & Minion Wave System 1:1 Pygame (_entity.py & _core.py)
# 1. Tower AI:
#    - Tower Dive Aggro: Menara mengalihkan tembakan ke musuh yang menyerang hero kawan di dalam jangkauan menara
#    - 4 Tipe Menara (Archer, Cannon, Ice, Mage) dengan stat spesifik, upgrade Lv 1-6, AOE splash, slow, chain, debuff
#    - Shield 40% Max HP + Out-of-combat HP/Shield regen setelah 5 detik
#    - Hadiah bounty gold saat menara hancur (Outer: 100G, Inner: 150G)
# 2. Minion Wave System:
#    - 5 Tipe Minion (Goblin, Orc, Troll, Undead ranged, Dark Rider cavalry)
#    - Komposisi wave berjenjang (Wave 1: goblins, Wave 2: +orcs, Wave 3: +undead ranged, Wave 4+: +troll, Wave 7+: +dark rider)
#    - Status debuff menara (Slow, Atk Slow, Burn DOT, Anti-Heal)
#    - Sistem Last-Hit: Floating gold text +<gold>G, penambahan gold tim, dan bonus XP ke hero
#
# Pasang berkas ini ke res://scripts/Tower.gd dan res://scripts/Minion.gd
