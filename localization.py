"""Lokalisasi ringan untuk teks UI game yang mendukung pilihan bahasa.

Gunakan ``tr(key, **values)`` untuk teks baru. Bahasa aktif disinkronkan
oleh ``GameSettings`` dan disimpan pada settings.json.

Sejak 2026-09-13 tabel ini juga memegang TEKS PERMUKAAN IN-MATCH port Godot
(HUD, toko, panel hero, layar hasil) — blok ``hud_*`` / ``shop_*`` /
``skillbar_*`` / ``over_*``. Nilainya sengaja dipakai DUA ARAH: bahasa ``id``
adalah teks yang selama ini di-hardcode di ``godot/scenes/ui/*.gd``, jadi
pemain Indonesia tidak melihat perbedaan apa pun, sementara ``en`` membuat
pilihan "English" benar-benar berlaku di dalam game (bukan hanya di label
Pengaturan). Pemakai pygame lama tidak berubah: pygame tetap memakai teks
campurannya sendiri di ``_core.py`` (lihat docs/LOCALIZATION_GODOTPP.md).
"""

_LANGUAGE = "id"

LANGUAGES = ("id", "en")
LANGUAGE_LABELS = {
    "id": "Bahasa Indonesia",
    "en": "English",
}

_TEXT = {
    "id": {
        "language": "Bahasa",
        "dead": "MATI",
        "queued": "+{count} antrean",
        "delivery_after_respawn": "(dikirim setelah respawn)",
        "dead_delivery_hint": "MATI — pembelian baru dikirim setelah respawn",
        "queued_item_count": "({count} item diantrikan)",
        "no_hero": "Tidak ada hero untuk menerima item.",
        "inventory_full": "Inventory {hero} penuh.",
        "magic_only_denied": ("{hero} bukan hero beratribut Magic - "
                              "item ini tidak bisa dipakai."),
        "forge_purchase": "{hero} membeli {item}!",
        "forge_queued": "{item} untuk {hero} dikirim setelah respawn!",
        "forge_delivered": "Item Forge dikirim ke {hero}: {items}!",
        "shop_no_hero_yet": "(belum ada hero - summon dulu di HERO SHOP)",
        "shop_no_hero_banner": ("TIDAK ADA HERO HIDUP - summon hero di HERO SHOP "
                                "dulu; item di bawah tetap bisa dilihat."),
        "shop_page_label": "HAL {page}",
        "item_dropped": "Melepas {item} (tanpa refund)",
        "item_dropped_short": "Melepas {item}",
        # ═══ DETAIL POPUP ITEM FORGE (info lengkap item) ═══
        "item_card_detail_hint": "TAP KARTU ITEM = INFO LENGKAP",
        "item_detail_description": "DESKRIPSI",
        "item_detail_stats": "STAT & EFEK",
        "item_detail_flavor": "RIWAYAT",
        "item_detail_owned": "DIMILIKI: {count}",
        "item_detail_close_hint": "Ketuk di luar kotak untuk menutup detail",
        "item_inventory_hint": "(ketuk: info  •  tahan/kanan: drop)",
        # ═══ PERMUKAAN IN-MATCH (HUD, TOKO, PANEL HERO, HASIL) ═══
        # Permintaan user 2026-09-13: pemilih bahasa di SETTINGS harus benar-
        # benar berlaku DI DALAM game. Di Godot teks ini dulunya literal
        # Indonesia, jadi "English" hanya mengubah satu baris di menu.
        # Nilai "id" = teks yang sudah dipakai port Godot (tidak ada yang
        # berubah untuk pemain Indonesia); "en" = padanan Inggrisnya.
        # Angka/placeholder ditulis sebagai %d/%s/%.2f apa adanya dan diisi
        # pemakai (GDScript `template % [...]`) supaya urutan kata tiap bahasa
        # bebas — tabel sengaja tidak menyimpan angka.
        "hud_hint_select": "pilih",
        "hud_hint_skill": "skill",
        "hud_hint_shop": "toko",
        "hud_hint_click": "klik",
        "hud_hint_right_click": "klik kanan",
        "hud_hint_pause": "jeda",
        "hud_hint_close": "tutup",
        "hud_hint_buy": "beli",
        "hud_hint_replay": "ulangi",
        "hud_hint_next": "lanjut",
        "hud_hint_menu": "menu",
        "shop_title": "TOKO",
        "shop_close": "TUTUP  (H)",
        "shop_tab_tower": "MENARA",
        "shop_tab_item": "ITEM",
        "shop_tab_hero": "HERO",
        "shop_tab_nexus": "NEXUS",
        "shop_context_none": "tidak ada yang dipilih",
        "shop_label_tower": "menara",
        "shop_label_slot": "slot",
        "shop_buy_for": "BELI UNTUK:",
        "shop_dead_no_forge": "DEAD - belum ada antrean Item Forge di build ini",
        "shop_item_note": "Item dibeli per hero: 6 slot, harga 4500-6000 gold per tier.",
        "shop_item_slots": "%s — %d/%d slot item",
        "shop_item_attack_type": "Tipe serangan: %s · %s — item bertanda hanya untuk tipe itu.",
        "shop_item_owned": "Dimiliki: %s",
        "shop_item_owned_suffix": "dimiliki",
        "shop_reason_owned": "Sudah dimiliki",
        "shop_reason_full": "Slot penuh (6/6)",
        "shop_reason_melee": "MELEE ONLY — hero ini ranged",
        "shop_reason_magic": "MAGIC ONLY — hero ini bukan magic",
        "shop_reason_poor": "Gold kurang",
        "shop_hero_select_hint": "Pilih hero Radiant untuk melihat status & upgrade.",
        "shop_hero_buy_list": "Beli hero (%d/%d dimiliki, termasuk yang respawn):",
        "shop_hero_others": "Hero lain (%d total di heroes.json) terbuka lewat progres level — "
                             "lihat SaveManager.unlocked_heroes.",
        "shop_hero_owned_badge": " · DIMILIKI",
        "shop_max_level": "Level maksimum tercapai.",
        "shop_max_level_count": "Level maksimum (%d) tercapai.",
        "shop_upgrade_to": "Upgrade ke Lv.%d — %d gold",
        "shop_upgrade_stat_note": "HP x%.2f, damage & jangkauan naik.",
        "shop_tower_hint": "Klik lingkaran slot di lane untuk membangun menara.",
        "shop_tower_free_slots": "Slot kosong: Radiant %d · Dire %d  (3 slot per lane per tim)",
        "shop_tower_click_upgrade": "Klik menara milikmu untuk upgrade / jual / Regen Shield.",
        "shop_tower_slot_dire": "Slot ini milik Dire — tidak bisa dibangun.",
        "shop_tower_slot_taken": "Slot sudah terisi menara.",
        "shop_tower_slot_empty": "Slot kosong di lane %s — bangun menara Lv1 (%d gold)",
        "shop_tower_build_note": "Catatan: stat Lv1 semua jalur sama (Archer Lv1); "
                                  "kekuatannya baru muncul setelah upgrade ke Lv2.",
        "shop_tower_path_note": "Upgrade Lv1 -> Lv2 memilih jalur dan menaikkan HP x%.2f.",
        "shop_tower_special": "Spesial: %s",
        "shop_tower_dire_locked": "Menara Dire — tidak bisa di-upgrade atau dijual.",
        "shop_tower_pick_path": "Pilih jalur upgrade ke Lv2:",
        "shop_regen_active": "Regen Shield: AKTIF (shield pulih setelah 3 detik tidak kena damage)",
        "shop_regen_buy": "Beli Regen Shield — %d gold",
        "shop_regen_note": "Shield menara ikut regen (paritas Tower.activate_regen_shield).",
        "shop_regen_locked": "Regen Shield terbuka di Lv.%d+ (harga %d gold)",
        "shop_tower_sell": "Jual menara (+%d gold)",
        "shop_tower_sell_note": "Refund 50% dari total biaya upgrade yang sudah dibayar.",
        "shop_nexus_dead": "Radiant Nexus sudah hancur.",
        "shop_nexus_max": "Nexus sudah level maksimum.",
        "shop_nexus_upgrade": "Upgrade Nexus ke Lv.%d — %d gold",
        "shop_nexus_free_shield": "Castle Shield GRATIS aktif (sampai wave 10) — damage tersisa "
                                  "dikurangi %.0f%%.",
        "shop_nexus_shield_buy": "Beli Castle Shield — %d gold",
        "shop_nexus_shield_note": "Shield permanen: menyerap damage 1:1, sisanya dimitigasi %.0f%%.",
        "shop_nexus_shield_owned": "Castle Shield sudah dibeli.",
        "shop_nexus_enemy": "Dire Nexus: Lv%d · HP %d/%d · shield %d/%d — hancurkan untuk MENANG.",
        "skillbar_no_hero": "tidak ada hero dipilih",
        "skillbar_buy_hint": "H → HERO: beli hero, lalu klik untuk memilih",
        "skillbar_close_tip": "Tutup panel (batal pilih hero)",
        "skillbar_autocast_tip": "Auto-cast selalu ON (paritas v29: toggle no-op)",
        "skillbar_slot_empty": "slot item %d kosong",
        "skillbar_forge_tip": "Buka ITEM FORGE untuk hero ini",
        "over_replay": "ULANGI  (R)",
        "over_menu": "MENU UTAMA  (ESC)",
        "over_replay_hint": "ulangi",
        "over_next_hint": "lanjut level",
        "over_menu_hint": "menu utama",
        "over_defeat_note": "Nexus Radiant hancur — kalah tidak dibayar.",
        "over_meta_reward": "Meta reward: +%d gold (%s) tersimpan ke save.",
        "over_next_button": "LANJUT KE LEVEL %d  (ENTER)",
        "over_reward_first_win": "menang pertama",
        "over_reward_first_replay": "replay pertama",
        "over_reward_replay": "replay berulang",
    },
    "en": {
        "language": "Language",
        "dead": "DEAD",
        "queued": "+{count} queued",
        "delivery_after_respawn": "(delivered after respawn)",
        "dead_delivery_hint": "DEAD — new purchases are delivered after respawn",
        "queued_item_count": "({count} item(s) queued)",
        "no_hero": "There is no hero to receive this item.",
        "inventory_full": "{hero}'s inventory is full.",
        "magic_only_denied": ("{hero} is not a Magic-attribute hero - "
                              "this item cannot be equipped."),
        "forge_purchase": "{hero} purchased {item}!",
        "forge_queued": "{item} for {hero} will be delivered after respawn!",
        "forge_delivered": "Forge items delivered to {hero}: {items}!",
        "shop_no_hero_yet": "(no heroes yet - summon one at HERO SHOP first)",
        "shop_no_hero_banner": ("NO HEROES ALIVE - summon a hero at HERO SHOP "
                                "first; items below can still be browsed."),
        "shop_page_label": "PAGE {page}",
        "item_dropped": "Dropped {item} (no refund)",
        "item_dropped_short": "Dropped {item}",
        # ═══ ITEM FORGE DETAIL POPUP (full item info) ═══
        "item_card_detail_hint": "TAP AN ITEM CARD = FULL INFO",
        "item_detail_description": "DESCRIPTION",
        "item_detail_stats": "STATS & EFFECTS",
        "item_detail_flavor": "LORE",
        "item_detail_owned": "OWNED: {count}",
        "item_detail_close_hint": "Tap outside the box to close details",
        "item_inventory_hint": "(tap: info  •  hold/right-click: drop)",
        # ═══ IN-MATCH SURFACES (HUD, SHOP, HERO PANEL, RESULT) ═══
        # Pasangan 1:1 dari blok "id" di atas — kunci + urutan WAJIB identik
        # (diaudit baris demi baris oleh tools/test_godot_localization_parity.py).
        "hud_hint_select": "select",
        "hud_hint_skill": "skill",
        "hud_hint_shop": "shop",
        "hud_hint_click": "click",
        "hud_hint_right_click": "right-click",
        "hud_hint_pause": "pause",
        "hud_hint_close": "close",
        "hud_hint_buy": "buy",
        "hud_hint_replay": "replay",
        "hud_hint_next": "next",
        "hud_hint_menu": "menu",
        "shop_title": "SHOP",
        "shop_close": "CLOSE  (H)",
        "shop_tab_tower": "TOWERS",
        "shop_tab_item": "ITEMS",
        "shop_tab_hero": "HERO",
        "shop_tab_nexus": "NEXUS",
        "shop_context_none": "nothing selected",
        "shop_label_tower": "tower",
        "shop_label_slot": "slot",
        "shop_buy_for": "BUY FOR:",
        "shop_dead_no_forge": "DEAD - no Item Forge queue in this build",
        "shop_item_note": "Items are bought per hero: 6 slots, priced 4500-6000 gold per tier.",
        "shop_item_slots": "%s — %d/%d item slots",
        "shop_item_attack_type": "Attack type: %s · %s — tagged items only fit that type.",
        "shop_item_owned": "Owned: %s",
        "shop_item_owned_suffix": "owned",
        "shop_reason_owned": "Already owned",
        "shop_reason_full": "Inventory full (6/6)",
        "shop_reason_melee": "MELEE ONLY — this hero is ranged",
        "shop_reason_magic": "MAGIC ONLY — this hero is not magic",
        "shop_reason_poor": "Not enough gold",
        "shop_hero_select_hint": "Select a Radiant hero to see its stats & upgrades.",
        "shop_hero_buy_list": "Buy heroes (%d/%d owned, including the ones waiting to respawn):",
        "shop_hero_others": "Other heroes (%d total in heroes.json) unlock through level progress — "
                             "see SaveManager.unlocked_heroes.",
        "shop_hero_owned_badge": " · OWNED",
        "shop_max_level": "Maximum level reached.",
        "shop_max_level_count": "Maximum level (%d) reached.",
        "shop_upgrade_to": "Upgrade to Lv.%d — %d gold",
        "shop_upgrade_stat_note": "HP x%.2f, damage and range go up.",
        "shop_tower_hint": "Click a slot circle on a lane to build a tower.",
        "shop_tower_free_slots": "Empty slots: Radiant %d · Dire %d  (3 slots per lane per team)",
        "shop_tower_click_upgrade": "Click one of your towers to upgrade / sell / Regen Shield.",
        "shop_tower_slot_dire": "This slot belongs to Dire — it cannot be built.",
        "shop_tower_slot_taken": "This slot already holds a tower.",
        "shop_tower_slot_empty": "Empty slot on lane %s — build a Lv1 tower (%d gold)",
        "shop_tower_build_note": "Note: Lv1 stats are the same on every path (Archer Lv1); "
                                  "its strength only appears after upgrading to Lv2.",
        "shop_tower_path_note": "Upgrading Lv1 -> Lv2 picks the path and raises HP by x%.2f.",
        "shop_tower_special": "Special: %s",
        "shop_tower_dire_locked": "Dire tower — it cannot be upgraded or sold.",
        "shop_tower_pick_path": "Pick the Lv2 upgrade path:",
        "shop_regen_active": "Regen Shield: ACTIVE (shield recovers after 3 seconds without damage)",
        "shop_regen_buy": "Buy Regen Shield — %d gold",
        "shop_regen_note": "The tower shield regenerates too (parity Tower.activate_regen_shield).",
        "shop_regen_locked": "Regen Shield unlocks at Lv.%d+ (costs %d gold)",
        "shop_tower_sell": "Sell tower (+%d gold)",
        "shop_tower_sell_note": "Refunds 50% of the upgrade costs already paid.",
        "shop_nexus_dead": "The Radiant Nexus is already destroyed.",
        "shop_nexus_max": "The Nexus is already at maximum level.",
        "shop_nexus_upgrade": "Upgrade Nexus to Lv.%d — %d gold",
        "shop_nexus_free_shield": "FREE Castle Shield is active (until wave 10) — leftover damage "
                                   "is reduced by %.0f%%.",
        "shop_nexus_shield_buy": "Buy Castle Shield — %d gold",
        "shop_nexus_shield_note": "Permanent shield: it absorbs damage 1:1, the rest is mitigated by %.0f%%.",
        "shop_nexus_shield_owned": "Castle Shield already purchased.",
        "shop_nexus_enemy": "Dire Nexus: Lv%d · HP %d/%d · shield %d/%d — destroy it to WIN.",
        "skillbar_no_hero": "no hero selected",
        "skillbar_buy_hint": "H → HERO: buy a hero, then click it to select",
        "skillbar_close_tip": "Close panel (deselect hero)",
        "skillbar_autocast_tip": "Auto-cast is always ON (parity v29: toggle no-op)",
        "skillbar_slot_empty": "item slot %d empty",
        "skillbar_forge_tip": "Open ITEM FORGE for this hero",
        "over_replay": "REPLAY  (R)",
        "over_menu": "MAIN MENU  (ESC)",
        "over_replay_hint": "replay",
        "over_next_hint": "next level",
        "over_menu_hint": "main menu",
        "over_defeat_note": "Radiant Nexus destroyed — a defeat pays nothing.",
        "over_meta_reward": "Meta reward: +%d gold (%s) saved to the save file.",
        "over_next_button": "NEXT LEVEL %d  (ENTER)",
        "over_reward_first_win": "first win",
        "over_reward_first_replay": "first replay",
        "over_reward_replay": "repeat replay",
    },
}


def set_language(language):
    """Set bahasa aktif. Nilai tidak valid aman kembali ke Indonesia."""
    global _LANGUAGE
    _LANGUAGE = language if language in LANGUAGES else "id"
    return _LANGUAGE


def get_language():
    return _LANGUAGE


def get_language_label(language=None):
    return LANGUAGE_LABELS.get(language or _LANGUAGE, LANGUAGE_LABELS["id"])


def tr(key, **values):
    """Ambil teks bahasa aktif dengan fallback aman ke bahasa Indonesia."""
    template = _TEXT.get(_LANGUAGE, _TEXT["id"]).get(key)
    if template is None:
        template = _TEXT["id"].get(key, key)
    try:
        return template.format(**values)
    except (KeyError, ValueError):
        return template
