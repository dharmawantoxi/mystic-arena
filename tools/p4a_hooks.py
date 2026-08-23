"""
python-for-android hooks for Mystic Arena.

Buildozer 1.5.0 currently quotes android.extra_manifest_application_arguments
incorrectly when it calls p4a through subprocess(list). To keep Android 12+
backup rules without editing the GitHub workflow, the build uses this p4a hook
instead: after p4a renders AndroidManifest.xml, add
android:dataExtractionRules to the <application> element directly.
"""

from __future__ import annotations

from pathlib import Path


DATA_EXTRACTION_ATTR = 'android:dataExtractionRules="@xml/data_extraction_rules"'


def _patch_manifest() -> None:
    manifest = Path("src/main/AndroidManifest.xml")
    if not manifest.exists():
        print(f"[p4a-hook] AndroidManifest.xml tidak ditemukan: {manifest}")
        return

    text = manifest.read_text(encoding="utf-8")
    if "android:dataExtractionRules=" in text:
        print("[p4a-hook] android:dataExtractionRules sudah ada di manifest")
        return

    app_pos = text.find("<application")
    if app_pos < 0:
        raise RuntimeError("Tag <application> tidak ditemukan di AndroidManifest.xml")

    tag_end = text.find(">", app_pos)
    if tag_end < 0:
        raise RuntimeError("Tag <application> tidak tertutup di AndroidManifest.xml")

    text = text[:tag_end] + f"\n                 {DATA_EXTRACTION_ATTR}" + text[tag_end:]
    manifest.write_text(text, encoding="utf-8")
    print(f"[p4a-hook] Menambahkan {DATA_EXTRACTION_ATTR} ke {manifest}")


def after_apk_build(toolchain) -> None:
    # Called after p4a generated the Gradle project/manifest and before assemble.
    _patch_manifest()


def before_apk_assemble(toolchain) -> None:
    # Defensive second pass in case p4a changes hook order in a future release.
    _patch_manifest()
