"""Tes tanpa pygame untuk pilihan Bahasa Indonesia / English."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from localization import get_language, get_language_label, set_language, tr

assert set_language("en") == "en"
assert get_language() == "en"
assert get_language_label() == "English"
assert tr("forge_queued", item="Moon Shard", hero="Aldric") == \
    "Moon Shard for Aldric will be delivered after respawn!"

assert set_language("id") == "id"
assert get_language_label() == "Bahasa Indonesia"
assert tr("forge_queued", item="Moon Shard", hero="Aldric") == \
    "Moon Shard untuk Aldric dikirim setelah respawn!"

assert set_language("invalid") == "id"
print("Localization language switching: OK")
