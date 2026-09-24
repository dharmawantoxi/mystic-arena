# L37 — PARITAS ARMOR / DAMAGE (sesi LOGIKA pygame, langkah pertama)
# ============================================================
# Scope 2026-09-23 (README): mulai L37 ke atas HANYA logika
# (damage/armor/crit/lifesteal/wave/gold/level) — tidak ada ubahan draw_*.
# Langkah ini mem-port formula armor 1:1 dari _entity.py pygame.
#
# SEBELUM L37: take_damage() semua unit = `hp -= amount` mentah — beli
#   Steel Aegis / Demon Maw (+armor) TIDAK mengurangi damage sama sekali.
# SESUDAH L37: formula pygame persis —
#   armor > 0 → red = a*0.06/(1+a*0.06), dmg = max(1, round(dmg*(1-red)))
#   armor < 0 → bonus = min(1, -a*0.06),  dmg = round(dmg*(1+bonus))
#
# ATURAN SCHOOL (paritas resolve_damage_school _entity.py:106):
#   • Serangan dasar hero        → "physical" → KENA armor target
#   • Skill Q/E hero             → "magic"    → TEMBUS armor (damage penuh,
#                                  persis seperti sekarang; magic_resist 0)
#   • Tembakan menara / pukulan minion (tanpa school) → TIDAK kena armor
#     target minion/tower …
#   • … TAPI kalau targetnya HERO: armor hero berlaku untuk SEMUA damage
#     non-'fire' (pygame menggate hero lewat damage_type, bukan school).
#
# ANGKA DASAR (paritas):
#   Hero    → BASE_ARMOR 0  (pygame: armor hero murni dari item)
#   Tower   → BASE_ARMOR 3  (pygame _entity.py:687 — 2 + level, level 1)
#   Minion  → armor 0       (pygame MINION_TYPES goblin: tanpa armor)
#   Nexus   → armor 0       (castle pygame pakai SHIELD 88%, langkah lain)
#
# ═══════════ CARA PASANG (urutan PENTING) ═══════════
# 1) BUAT FILE BARU res://scripts/CombatCalc.gd
#      isi = arena-guide/scripts/CombatCalc.gd   (file utuh)
#    (Wajib duluan: 4 file lain memanggil CombatCalc.mitigate. Setelah save,
#     biarkan editor rescan sebentar sampai class_name terdaftar.)
# 2) GANTI UTUH 4 file dari arena-guide/scripts/:
#      Hero.gd, Minion.gd, Tower.gd, Nexus.gd
# 3) Save All → F5. Tidak ada ubahan Main.gd / SidePanel.gd / Shop.gd.
#    (Compatibility: signature take_damage(amount, school="") — pemanggil
#     lama 1-argumen tetap jalan.)
#
# ═══════════ TEST (5 menit) ═══════════
# A. Hero tabrak tower merah: damage 22 → tercatat 19 (tower armor 3,
#    red = 15.25%). Dengan AMUK (44) → 37. HP tower turun lebih lambat
#    dari biasanya — itu memang paritas pygame.
# B. Toko (H) → beli Steel Aegis (+6 armor): pukulan minion merah 8 → 6,
#    tembakan tower merah 18 → 13 ke hero. Beli Demon Maw pula (+10 total)
#    → minion 8 → 5.
# C. Skill Q (60) & E (35) ke tower/minion: TETAP penuh (magic tembus
#    armor) — tidak berubah dari sebelumnya.
# D. Minion vs minion / tower tembak minion: damage utuh (tanpa school),
#    sama seperti sebelumnya — pygame juga begitu.
# E. Debug angka: set LOG_HITS := true di CombatCalc.gd baris 23 →
#    panel Output mencetak "[Armor] 22.0 -> 19 (armor 3.0)" tiap mitigasi.
#
# Catatan: lifesteal Demon Maw sengaja BELUM diubah langkah ini — pygame
# juga menghitung lifesteal dari damage SEBELUM mitigasi target
# (_entity.py:4354/4400), jadi perilaku sekarang sudah paritas.
# Antrean berikut: L38 CRIT (Dead Edge 25% ×200), lalu wave/gold/level.
