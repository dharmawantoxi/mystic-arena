"""Deterministic RGBA atlas packing shared by the character art bakes."""
from __future__ import annotations

import hashlib

import numpy as np


def pack(frames, columns=10, gap=0, tight=False, max_width=2048):
    """Pack ``(key, rgba, ax, ay)`` rows and deduplicate identical pixels.

    Aliases retain their own anchors: two poses can have identical pixels while their
    world anchors differ. The manifest therefore shares the source rectangle, never
    the anchor. No renderer state or source pixels are changed.
    """
    assert frames and columns > 0 and gap >= 0
    unique = []
    aliases = []
    seen = {}
    for key, pixels, ax, ay in frames:
        assert pixels.dtype == np.uint8 and pixels.ndim == 3 and pixels.shape[2] == 4
        digest = hashlib.sha256()
        digest.update(f"{pixels.shape[0]}x{pixels.shape[1]}:".encode("ascii"))
        digest.update(pixels.tobytes())
        fingerprint = digest.digest()
        if fingerprint not in seen:
            seen[fingerprint] = len(unique)
            unique.append(pixels)
        aliases.append((key, seen[fingerprint], int(ax), int(ay)))

    cell_w = max(int(pixels.shape[1]) for pixels in unique)
    cell_h = max(int(pixels.shape[0]) for pixels in unique)
    placements = [None] * len(unique)
    if tight:
        # Height-sorted shelves prevent one large skill crop from inflating every cell.
        order = sorted(
            range(len(unique)),
            key=lambda index: (-unique[index].shape[0], -unique[index].shape[1], index),
        )
        x = y = row_h = sheet_w = 0
        for index in order:
            height, width = unique[index].shape[:2]
            if x and x + width > max_width:
                x = 0
                y += row_h + gap
                row_h = 0
            placements[index] = (x, y, int(width), int(height))
            x += width + gap
            row_h = max(row_h, height)
            sheet_w = max(sheet_w, x - gap)
        sheet = np.zeros((y + row_h, sheet_w, 4), dtype=np.uint8)
    else:
        columns = min(columns, len(unique))
        rows = -(-len(unique) // columns)
        sheet = np.zeros(
            (rows * cell_h + (rows - 1) * gap, columns * cell_w + (columns - 1) * gap, 4),
            dtype=np.uint8,
        )
        for index, pixels in enumerate(unique):
            height, width = pixels.shape[:2]
            placements[index] = (
                (index % columns) * (cell_w + gap),
                (index // columns) * (cell_h + gap),
                int(width),
                int(height),
            )
    for index, pixels in enumerate(unique):
        x, y, width, height = placements[index]
        sheet[y : y + height, x : x + width] = pixels

    table = {}
    for key, index, ax, ay in aliases:
        x, y, width, height = placements[index]
        table[key] = [x, y, width, height, ax, ay]
    return sheet, table, [cell_w, cell_h], len(unique)
