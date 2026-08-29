"""Lokalisasi ringan untuk teks UI yang mendukung pilihan bahasa.

Gunakan ``tr(key, **values)`` untuk teks baru. Bahasa aktif disinkronkan
oleh ``GameSettings`` dan disimpan pada settings.json.
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
