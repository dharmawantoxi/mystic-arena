#!/usr/bin/env python3
"""
Render Kaizen (procedural rig) to PNG — V2: polished version.

Improvements over V1:
* Outline pass (dark border on every polygon) for clean pixel-art silhouette.
* 4x supersampling + LANCZOS downscale for smooth edges without aliasing.
* Rebalanced proportions: taller torso, longer legs, smaller head.
* Eye repositioned to the profile view (left side, since the character
  faces right and we only draw the visible eye).
* Sword 1.7x longer, blade thicker, more readable.
* Subtle body shading: each part gets a darker shadow polygon for depth.
* Floor shadow with multi-layer falloff.

Vertex lists are still the same character (kept in sync with
kaizen_body_builder.gd) but the *proportions* and *details* are upgraded.
"""

import math
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter

# ---------------------------------------------------------------------------
# 1. Palette (matches kaizen_body_builder.gd, plus shading tints)
# ---------------------------------------------------------------------------

P = {
    # Material
    "ink":          (24, 26, 40),
    "ink_soft":     (44, 38, 54),
    # Skin
    "skin_dark":    (120, 84, 66),
    "skin_mid":     (196, 150, 112),
    "skin_light":   (226, 186, 146),
    "skin_shine":   (246, 218, 182),
    # Hair
    "hair_dark":    (29, 24, 22),
    "hair_mid":     (86, 68, 50),
    # Cloth (indigo with depth)
    "cloth_darkest": (16, 20, 32),
    "cloth_dark":   (38, 50, 86),
    "cloth_mid":    (62, 84, 134),
    "cloth_light":  (102, 138, 194),
    # Sash
    "sash":         (86, 130, 206),
    "sash_dark":    (46, 76, 148),
    # Pants / hakama
    "pants_dark":   (26, 36, 66),
    "pants_mid":    (46, 60, 110),
    "pants_light":  (80, 102, 162),
    # Boots
    "boot":         (21, 16, 11),
    "boot_light":   (52, 38, 24),
    # Steel
    "steel_dark":   (76, 82, 94),
    "steel_mid":    (126, 134, 148),
    "steel_light":  (184, 190, 202),
    "steel_shine":  (230, 236, 246),
    # Gold
    "gold_dark":    (106, 72, 24),
    "gold_mid":     (169, 126, 42),
    "gold_light":   (226, 186, 82),
    # Saya
    "saya_dark":    (64, 16, 24),
    "saya_mid":     (114, 30, 44),
    "saya_light":   (162, 50, 62),
    # Wrap
    "wrap_dark":    (64, 22, 28),
    "wrap_mid":     (118, 42, 52),
    "wrap_light":   (176, 72, 84),
    # Eye
    "eye_white":    (247, 253, 255),
    "eye_iris":     (206, 152, 54),
    "eye_glow":     (160, 228, 255),
    # FX
    "wind":         (112, 178, 230),
    "wind_bright":  (216, 242, 255),
    # BG
    "bg":           (38, 34, 28),
    "bg_warm":      (50, 42, 32),
    "shadow":       (0, 0, 0),
}

# Outline palette: each base color has a darker outline.
# We use a single outline color for consistency (pixel-art convention).
OUTLINE = P["ink"]


# ---------------------------------------------------------------------------
# 2. Rig data — hierarchical Node tree (mirrors Godot scene)
# ---------------------------------------------------------------------------

@dataclass
class Node:
    name: str
    color_key: str
    polygon: List[Tuple[float, float]]
    position: Tuple[float, float] = (0.0, 0.0)
    rotation: float = 0.0
    z: int = 0
    children: List["Node"] = field(default_factory=list)
    parent: Optional["Node"] = None
    outline: bool = True
    shadow: Optional[str] = None      # colour key for shadow polygon
    highlight: Optional[str] = None   # colour key for highlight polygon


# ---------------------------------------------------------------------------
# 3. Build the rig — V2 proportions
# ---------------------------------------------------------------------------

def build_rig() -> Node:
    """Rebalanced rig in rig-units (~32 wide, ~98 tall). All coordinates
    here are in rig-units. The renderer scales them up at draw time."""
    body = Node(name="Body", color_key="ink", polygon=[],
                position=(0.0, 0.0), z=-1, outline=False)

    # ----- Pelvis (sits at hip line) -----
    body.children.append(Node("Pelvis", "cloth_darkest",
        polygon=[(-11, 18), (11, 18), (10, 32), (-10, 32)], z=2))

    # ----- Sash (winds around waist) -----
    body.children.append(Node("Sash", "sash",
        polygon=[(-14, 6), (14, 6), (12, 18), (-12, 18)], z=7))
    body.children.append(Node("SashTail", "sash_dark",
        polygon=[(-12, 16), (-4, 16), (-2, 30), (-10, 30)], z=6))

    # ----- Torso (taller, more tapered) -----
    body.children.append(Node("Torso", "cloth_dark",
        polygon=[(-13, -10), (13, -10), (15, 14), (12, 22), (-12, 22), (-15, 14)], z=5,
        shadow="cloth_darkest"))
    body.children.append(Node("Chest", "cloth_mid",
        polygon=[(-10, -6), (10, -6), (9, 4), (-9, 4)], z=6))
    # Shoulder pads (give the silhouette mass at the top).
    body.children.append(Node("ShoulderR", "cloth_mid",
        polygon=[(8, -10), (16, -10), (15, -2), (8, -2)], z=5))
    body.children.append(Node("ShoulderL", "cloth_dark",
        polygon=[(-16, -10), (-8, -10), (-8, -2), (-15, -2)], z=4))
    # Collar accent.
    body.children.append(Node("Collar", "sash_dark",
        polygon=[(-7, -10), (7, -10), (5, -6), (-5, -6)], z=7))

    # ----- Legs (longer, with thigh + calf distinction) -----
    # Thighs (top, lighter shade).
    body.children.append(Node("LeftThigh", "pants_mid",
        polygon=[(-9, 30), (-1, 30), (-2, 50), (-8, 50)], z=0,
        shadow="pants_dark"))
    body.children.append(Node("RightThigh", "pants_mid",
        polygon=[(1, 30), (9, 30), (8, 50), (2, 50)], z=0,
        shadow="pants_dark"))
    # Calves (bottom, darker).
    body.children.append(Node("LeftCalf", "pants_dark",
        polygon=[(-8, 48), (-2, 48), (-1, 70), (-7, 70)], z=1))
    body.children.append(Node("RightCalf", "pants_dark",
        polygon=[(2, 48), (8, 48), (7, 70), (1, 70)], z=1))
    # Boots (chunky, dark).
    body.children.append(Node("LeftBoot", "boot",
        polygon=[(-9, 68), (-1, 68), (0, 78), (-10, 78)], z=2,
        highlight="boot_light"))
    body.children.append(Node("RightBoot", "boot",
        polygon=[(1, 68), (9, 68), (10, 78), (0, 78)], z=2,
        highlight="boot_light"))

    # ----- Scabbard (longer, off left hip) -----
    scabbard = Node("Scabbard", "saya_mid", polygon=[],
                    position=(-9, 16), z=3, outline=True)
    scabbard.children.append(Node("ScabbardBody", "saya_mid",
        polygon=[(-4, 0), (4, 0), (3, 42), (-3, 42)], z=3,
        shadow="saya_dark"))
    scabbard.children.append(Node("ScabbardCord", "wrap_mid",
        polygon=[(-5, 6), (5, 6), (5, 10), (-5, 10)], z=4))
    scabbard.children.append(Node("ScabbardTip", "saya_dark",
        polygon=[(-3, 40), (3, 40), (0, 46)], z=4))
    body.children.append(scabbard)

    # ----- Sword arm (pivot at right shoulder) -----
    # Shoulder is at (12, -8). Arm hangs down + slightly forward.
    sword_arm = Node("SwordArm", "cloth_dark", polygon=[],
                     position=(12, -8), z=16, outline=True)
    # Upper arm (cloth sleeve).
    sword_arm.children.append(Node("UpperArm", "cloth_dark",
        polygon=[(-5, 0), (5, 0), (6, 16), (-6, 16)], z=16))
    # Elbow joint.
    sword_arm.children.append(Node("Elbow", "skin_mid",
        polygon=[(-4, 14), (4, 14), (4, 18), (-4, 18)], z=17))
    # Forearm (skin).
    sword_arm.children.append(Node("Forearm", "skin_mid",
        polygon=[(-4, 16), (4, 16), (5, 32), (-5, 32)], z=17,
        shadow="skin_dark"))
    # Glove.
    sword_arm.children.append(Node("Glove", "boot",
        polygon=[(-5, 30), (5, 30), (6, 36), (-6, 36)], z=18,
        highlight="boot_light"))

    # ----- Sword (pivot at hilt, rotated -0.4 rad at rest — pointing
    #       forward+up, classic katana-at-rest carry) -----
    sword = Node("Sword", "steel_light", polygon=[],
                 position=(0, 34), rotation=-0.4, z=19, outline=True)
    # Handle wrap (longer for readability).
    sword.children.append(Node("SwordHandle", "wrap_mid",
        polygon=[(-3, 0), (3, 0), (3, 12), (-3, 12)], z=19,
        highlight="wrap_light"))
    # Pommel.
    sword.children.append(Node("SwordPommel", "gold_mid",
        polygon=[(-3, -3), (3, -3), (4, 0), (-4, 0)], z=18))
    # Hand guard.
    sword.children.append(Node("SwordGuard", "gold_mid",
        polygon=[(-8, 10), (8, 10), (8, 14), (-8, 14)], z=20,
        highlight="gold_light"))
    # Blade (long, tapered).
    sword.children.append(Node("SwordBlade", "steel_light",
        polygon=[(-3, 14), (3, 14), (2, 78), (-2, 78)], z=21,
        highlight="steel_shine"))
    # Edge highlight (thin line on the cutting side).
    sword.children.append(Node("SwordEdge", "steel_shine",
        polygon=[(0, 14), (3, 14), (2, 78), (0, 78)], z=22))
    # Tip.
    sword.children.append(Node("SwordTip", "steel_mid",
        polygon=[(-2, 76), (2, 76), (0, 82)], z=21))
    sword_arm.children.append(sword)
    body.children.append(sword_arm)

    # ----- Head (smaller, more proportional) -----
    # Anchor at neck (y = -16).
    head = Node("Head", "skin_mid", polygon=[],
                position=(0, -16), z=8, outline=True)
    # Neck.
    head.children.append(Node("Neck", "skin_mid",
        polygon=[(-4, 8), (4, 8), (3, 14), (-3, 14)], z=8,
        shadow="skin_dark"))
    # Skull.
    head.children.append(Node("Skull", "skin_mid",
        polygon=[(-9, -12), (9, -12), (10, -2), (9, 4), (-9, 4), (-10, -2)], z=9,
        shadow="skin_dark", highlight="skin_light"))
    # Hair back (long, flowing).
    head.children.append(Node("HairBack", "hair_dark",
        polygon=[(-11, -14), (11, -14), (12, -4), (10, 8),
                  (-10, 8), (-12, -4)], z=10))
    # Hair front (fringe).
    head.children.append(Node("HairFront", "hair_dark",
        polygon=[(-10, -12), (10, -12), (8, -6), (-8, -6)], z=11))
    # Top knot (tied up).
    head.children.append(Node("TopKnot", "hair_dark",
        polygon=[(-3, -20), (3, -20), (2, -12), (-2, -12)], z=12))
    # Headband (red, just above forehead).
    head.children.append(Node("Band", "wrap_mid",
        polygon=[(-10, -8), (10, -8), (10, -6), (-10, -6)], z=13,
        highlight="wrap_light"))
    # Eye (profile view — single eye, on the visible side).
    head.children.append(Node("Eye", "eye_white",
        polygon=[(-5, -3), (-1, -3), (-1, 0), (-5, 0)], z=14))
    # Iris (smaller, deep inside).
    head.children.append(Node("Iris", "eye_iris",
        polygon=[(-4, -2), (-2, -2), (-2, -1), (-4, -1)], z=15))
    # Pupil (tiny dot for sharp focus).
    head.children.append(Node("Pupil", "ink",
        polygon=[(-3, -2), (-2, -2), (-2, -1), (-3, -1)], z=16))
    # Eyebrow (sharp, fierce).
    head.children.append(Node("Brow", "ink",
        polygon=[(-5, -5), (-1, -5), (-1, -4), (-5, -4)], z=13,
        outline=False))
    body.children.append(head)

    # CRITICAL: set parent pointers for compute_world_matrix traversal.
    def _link(n: Node, p: Optional[Node]) -> None:
        n.parent = p
        for c in n.children:
            _link(c, n)
    _link(body, None)
    return body


# ---------------------------------------------------------------------------
# 4. Walk the tree and draw
# ---------------------------------------------------------------------------

def collect_leaves(root: Node) -> List[Node]:
    out: List[Node] = []
    def walk(n: Node):
        if n.polygon and n.outline:
            out.append(n)
        for c in n.children:
            walk(c)
    walk(root)
    out.sort(key=lambda n: n.z)
    return out


def collect_shadows(root: Node) -> List[Tuple[Node, str]]:
    """Return list of (node, colour_key) for shadow/highlight overlays."""
    out: List[Tuple[Node, str]] = []
    def walk(n: Node):
        if n.polygon:
            if n.shadow:
                out.append((n, n.shadow))
        for c in n.children:
            walk(c)
    walk(root)
    return out


def compute_world_matrix(node: Node) -> Tuple[float, float, float, float]:
    chain: List[Node] = []
    n = node
    while n is not None:
        chain.append(n)
        n = n.parent
    chain.reverse()
    cos_t = math.cos(chain[0].rotation)
    sin_t = math.sin(chain[0].rotation)
    dx = chain[0].position[0]
    dy = chain[0].position[1]
    for c in chain[1:]:
        rx = c.position[0] * cos_t - c.position[1] * sin_t
        ry = c.position[0] * sin_t + c.position[1] * cos_t
        dx += rx
        dy += ry
        ca = math.cos(c.rotation)
        sa = math.sin(c.rotation)
        cos_t, sin_t = cos_t * ca - sin_t * sa, cos_t * sa + sin_t * ca
    return cos_t, sin_t, dx, dy


def transform_polygon(polygon: List[Tuple[float, float]],
                      cos_t: float, sin_t: float,
                      dx: float, dy: float,
                      facing: int = 1) -> List[Tuple[float, float]]:
    out: List[Tuple[float, float]] = []
    for (x, y) in polygon:
        wx = x * cos_t - y * sin_t + dx
        wy = x * sin_t + y * cos_t + dy
        wx = wx * facing
        wy = wy
        out.append((wx, wy))
    return out


def draw_rig(img: Image.Image, root: Node, body_origin: Tuple[int, int],
             facing: int = 1, draw_outline: bool = True,
             scale: float = 1.0) -> None:
    """Render the rig onto [img]. [scale] uniformly scales rig-units to
    image pixels (e.g. scale=14.4 means a 1-unit rig vector becomes 14.4
    image pixels). body_origin is the image-space position of the rig's
    (0, 0) — typically the feet at the centre of the canvas."""
    draw = ImageDraw.Draw(img, "RGBA")
    leaves = collect_leaves(root)

    def to_img(polygon, cos_t, sin_t, dx, dy):
        out = []
        for (x, y) in transform_polygon(polygon, cos_t, sin_t, dx, dy, facing):
            # x, y are in rig-units * facing; multiply by scale to
            # convert to image pixels, then add body_origin.
            out.append((x * scale + body_origin[0],
                        y * scale + body_origin[1]))
        return out

    # Pass 1: shadow polygons.
    for node, col_key in collect_shadows(root):
        cos_t, sin_t, dx, dy = compute_world_matrix(node)
        world = to_img(node.polygon, cos_t, sin_t, dx, dy)
        cx = sum(p[0] for p in world) / len(world)
        cy = sum(p[1] for p in world) / len(world)
        shrunk = [
            (cx + (p[0] - cx) * 0.55, cy + (p[1] - cy) * 0.55 + scale)
            for p in world
        ]
        draw.polygon(shrunk, fill=(*P[col_key], 255))

    # Pass 2: fill + outline.
    for node in leaves:
        cos_t, sin_t, dx, dy = compute_world_matrix(node)
        world = to_img(node.polygon, cos_t, sin_t, dx, dy)
        fill = P.get(node.color_key, (200, 0, 200))
        draw.polygon(world, fill=fill)
        if draw_outline and node.outline:
            outline_w = max(1, int(round(scale * 0.18)))
            for i in range(len(world)):
                a = world[i]
                b = world[(i + 1) % len(world)]
                draw.line([a, b], fill=(*OUTLINE, 255), width=outline_w)

        # Highlight.
        if node.highlight:
            col = P[node.highlight]
            cx = sum(p[0] for p in world) / len(world)
            cy = sum(p[1] for p in world) / len(world)
            top = min(world, key=lambda p: p[1])
            hx = cx + (top[0] - cx) * 0.4
            hy = cy + (top[1] - cy) * 0.4
            r = max(2.0, min(8.0, 0.18 * math.hypot(top[0] - cx, top[1] - cy)))
            draw.ellipse((hx - r, hy - r, hx + r, hy + r), fill=(*col, 220))


# ---------------------------------------------------------------------------
# 5. Pose variants
# ---------------------------------------------------------------------------

def find_node(root: Node, name: str) -> Optional[Node]:
    if root.name == name:
        return root
    for c in root.children:
        r = find_node(c, name)
        if r is not None:
            return r
    return None


def pose_idle() -> Node:
    return build_rig()


def pose_walk() -> Node:
    """Walk: legs alternating, body bob, sword swung slightly forward."""
    r = build_rig()
    # Leg stagger: left leg forward, right leg back.
    find_node(r, "LeftThigh").position = (-9, 30)
    find_node(r, "LeftCalf").position = (-9, 48)
    find_node(r, "LeftBoot").position = (-9, 68)
    find_node(r, "RightThigh").position = (9, 30)
    find_node(r, "RightCalf").position = (9, 48)
    find_node(r, "RightBoot").position = (9, 68)
    # Sword arm swings.
    find_node(r, "SwordArm").rotation = 0.18
    return r


def pose_q1() -> Node:
    """Q1 — Steel Wind: horizontal slash, sword arm fully forward."""
    r = build_rig()
    sa = find_node(r, "SwordArm")
    sa.rotation = 1.1
    find_node(r, "Forearm").rotation = -0.3
    # Body leans into the swing.
    find_node(r, "Torso").rotation = 0.08
    return r


def pose_q2() -> Node:
    """Q2 — Dash Strike: crouch, sword pulled back ready to strike."""
    r = build_rig()
    # Crouch (everything down).
    for n in ["Pelvis", "LeftThigh", "RightThigh", "LeftCalf", "RightCalf",
              "LeftBoot", "RightBoot", "Torso", "Chest", "ShoulderR",
              "ShoulderL", "Collar", "Sash", "SashTail", "Scabbard"]:
        node = find_node(r, n)
        if node is not None:
            node.position = (node.position[0], node.position[1] + 4)
    # Body leans forward.
    find_node(r, "Torso").rotation = 0.12
    # Sword pulled back.
    find_node(r, "SwordArm").rotation = -1.6
    find_node(r, "Forearm").rotation = 0.4
    return r


def pose_e() -> Node:
    """E — Sweep: mid-jump, sword sweeping low."""
    r = build_rig()
    # Jump.
    for n in ["LeftThigh", "RightThigh", "LeftCalf", "RightCalf",
              "LeftBoot", "RightBoot", "Pelvis", "Torso", "Chest",
              "ShoulderR", "ShoulderL", "Collar", "Sash", "SashTail",
              "Scabbard"]:
        node = find_node(r, n)
        if node is not None:
            node.position = (node.position[0], node.position[1] - 8)
    # Forward lean.
    find_node(r, "Torso").rotation = 0.25
    # Sword sweep low.
    find_node(r, "SwordArm").rotation = 1.6
    find_node(r, "Forearm").rotation = 0.6
    return r


def pose_r() -> Node:
    """R — Tornado: sword held high overhead, body coiled."""
    r = build_rig()
    sa = find_node(r, "SwordArm")
    sa.rotation = -2.6
    find_node(r, "Forearm").rotation = -0.4
    # Slight back-arch for dramatic tornado pose.
    find_node(r, "Torso").rotation = -0.08
    return r


# ---------------------------------------------------------------------------
# 6. VFX overlays (improved — clearer hierarchy)
# ---------------------------------------------------------------------------

def draw_slash_vfx(img: Image.Image, origin: Tuple[int, int],
                   facing: int = 1, scale: float = 1.0) -> None:
    """Crescent slash — primary 70%, secondary 20%, accent 10%."""
    draw = ImageDraw.Draw(img, "RGBA")
    cx, cy = origin
    arc_deg = 130
    outer = int(78 * scale)
    thickness = int(22 * scale)
    half = math.radians(arc_deg * 0.5)
    steps = 40

    def arc(radius: float) -> List[Tuple[float, float]]:
        pts: List[Tuple[float, float]] = []
        for i in range(steps + 1):
            t = i / steps
            a = -half + t * 2.0 * half
            pts.append((cx + math.cos(a) * radius * facing,
                        cy + math.sin(a) * radius))
        return pts

    # Layer 1: Outer glow (secondary, big, very transparent).
    glow_outer = arc(outer + 28)
    glow_inner = arc(outer - thickness - 28)
    draw.polygon(glow_outer + list(reversed(glow_inner)),
                 fill=(*P["wind"], 60))
    # Layer 2: Bright primary crescent.
    outer_pts = arc(outer)
    inner_pts = arc(outer - thickness)
    draw.polygon(outer_pts + list(reversed(inner_pts)),
                 fill=P["wind_bright"])
    # Layer 3: Inner stroke (darker wind, gives edge).
    edge_pts = arc(outer - 2)
    edge_inner = arc(outer - thickness + 2)
    draw.polygon(edge_pts + list(reversed(edge_inner)),
                 fill=(*P["wind"], 255))
    # Layer 4: Bright white accent (small wedge at the impact point).
    half_acc = half * 0.25
    inner: List[Tuple[float, float]] = []
    for i in range(steps + 1):
        t = i / steps
        a = -half_acc + t * 2.0 * half_acc
        inner.append((cx + math.cos(a) * (outer - thickness - 4) * facing,
                      cy + math.sin(a) * (outer - thickness - 4)))
    for i in range(steps + 1):
        t = i / steps
        a = half_acc - t * 2.0 * half_acc
        inner.append((cx + math.cos(a) * 5 * facing, cy + math.sin(a) * 5))
    draw.polygon(inner, fill=(255, 255, 255, 255))


def draw_tornado_vfx(img: Image.Image, origin: Tuple[int, int],
                     facing: int = 1, scale: float = 1.0) -> None:
    """Tornado: 7-band funnel + central streak + orbiting sparks."""
    draw = ImageDraw.Draw(img, "RGBA")
    cx, cy = origin
    height = int(220 * scale)
    top_r = int(32 * scale)
    bottom_r = int(78 * scale)
    bands = 7
    for i in range(bands):
        t = i / max(1, bands - 1)
        y = cy - height // 2 + int(t * height)
        rx = max(4, int((bottom_r + (top_r - bottom_r) * t) * scale))
        ry = max(2, int(rx * 0.40))
        wobble = int(math.sin(i * 1.3) * 1.5)
        bbox = (cx - rx - wobble, y - ry, cx + rx + wobble, y + ry)
        col_a = (60, 110, 180)
        col_b = P["wind"]
        col = tuple(int(col_a[k] + (col_b[k] - col_a[k]) * t) for k in range(3))
        # Outline (dark) + fill (semi-transparent wind).
        draw.ellipse(bbox, outline=(*P["ink"], 200), width=2)
        # Inner fill (slightly transparent).
        inner_bbox = (bbox[0] + 3, bbox[1] + 2, bbox[2] - 3, bbox[3] - 2)
        draw.ellipse(inner_bbox, fill=(*col, 80))
    # Vertical core streak.
    draw.line((cx, cy - height // 2, cx, cy + height // 2),
              fill=(*P["wind_bright"], 230), width=5)
    draw.line((cx, cy - height // 2, cx, cy + height // 2),
              fill=(*(255, 255, 255), 160), width=2)
    # Sparks.
    rng = random.Random(11)
    for _ in range(12):
        t = rng.random()
        y = cy - height // 2 + int(t * height)
        r = int((bottom_r + (top_r - bottom_r) * t) * scale) + 10
        ang = rng.random() * 6.28318
        sx = int(cx + math.cos(ang) * r)
        sy = int(y + math.sin(ang) * r * 0.4)
        sz = rng.choice([2, 2, 3])
        draw.ellipse((sx - sz, sy - sz, sx + sz, sy + sz),
                     fill=P["wind_bright"])


# ---------------------------------------------------------------------------
# 7. Renderer
# ---------------------------------------------------------------------------

# Canvas dimensions in FINAL pixels. Rig is ~32x98 in rig-units. At
# RIG_SCALE=2.5 the rig is 80x245 image-pixels. TopKnot at y=-32 (rig)
# → y=-32*2.5+origin. SwordBlade tip at y=82*2.5+origin=205+origin.
# Want topknot top at y=10 (margin 10px) and sword tip at y=H-10.
# So origin_y = 10 - (-32)*2.5 = 10 + 80 = 90.
# Sword tip y = 82*2.5 + 90 = 295. So canvas_h = 305.
CANVAS_W = 220
CANVAS_H = 360
ORIGIN = (110, 90)        # rig's y=0 sits here; topknot at y=10, sword tip at y=295


def render(rig: Node, name: str, facing: int = 1, out_dir: str = "out",
           ss: int = 4) -> str:
    """Render with supersampling."""
    RIG_SCALE = 2.5
    W, H = CANVAS_W * ss, CANVAS_H * ss
    O = (ORIGIN[0] * ss, ORIGIN[1] * ss)
    s = RIG_SCALE * ss
    img = Image.new("RGBA", (W, H), (*P["bg"], 255))
    # Floor shadow.
    for r, alpha in [(50, 35), (38, 60), (28, 90)]:
        shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.ellipse((O[0] - r * s, O[1] - int(12 * s),
                    O[0] + r * s, O[1] + int(8 * s)),
                   fill=(0, 0, 0, alpha))
        shadow = shadow.filter(ImageFilter.GaussianBlur(int(4 * s)))
        img.alpha_composite(shadow)
    draw_rig(img, rig, O, facing=facing, draw_outline=True, scale=s)
    out_path = os.path.join(out_dir, name + ".png")
    os.makedirs(out_dir, exist_ok=True)
    final = img.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
    final.save(out_path)
    return out_path


def render_with_vfx(rig: Node, name: str, vfx_fn: Callable,
                    facing: int = 1, out_dir: str = "out",
                    ss: int = 4) -> str:
    RIG_SCALE = 2.5
    W, H = CANVAS_W * ss, CANVAS_H * ss
    O = (ORIGIN[0] * ss, ORIGIN[1] * ss)
    s = RIG_SCALE * ss
    img = Image.new("RGBA", (W, H), (*P["bg"], 255))
    for r, alpha in [(50, 35), (38, 60), (28, 90)]:
        shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.ellipse((O[0] - r * s, O[1] - int(12 * s),
                    O[0] + r * s, O[1] + int(8 * s)),
                   fill=(0, 0, 0, alpha))
        shadow = shadow.filter(ImageFilter.GaussianBlur(int(4 * s)))
        img.alpha_composite(shadow)
    draw_rig(img, rig, O, facing=facing, draw_outline=True, scale=s)
    # VFX anchor: in front of the character, at chest height. We work
    # in high-res image space (CANVAS_* x ss). O is the rig's y=0
    # position. Chest is about 60 rig-units above O (negative y).
    # In high-res pixels that's -60 * s. So vfx_origin_y should be
    # O[1] - 60*s. But O[1]=90*4=360 and 60*s=60*10=600 → vfx_y=-240
    # (way above canvas). Instead, place the VFX in the centre of the
    # upper-half of the canvas where it has room.
    H = CANVAS_H * ss
    W = CANVAS_W * ss
    vfx_origin = (int(W * 0.55), int(H * 0.45))
    vfx_scale = s * 0.10
    vfx_fn(img, vfx_origin, facing=facing, scale=vfx_scale)
    out_path = os.path.join(out_dir, name + ".png")
    os.makedirs(out_dir, exist_ok=True)
    final = img.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
    final.save(out_path)
    return out_path


def render_sheet(poses: List[Tuple[str, Callable[[], Node]]],
                 out_dir: str = "out", cols: int = 3, ss: int = 4) -> str:
    RIG_SCALE = 2.5
    rows = (len(poses) + cols - 1) // cols
    W, H = CANVAS_W * cols, CANVAS_H * rows
    sheet = Image.new("RGBA", (W, H), (*P["bg_warm"], 255))
    for i, (label, factory) in enumerate(poses):
        col = i % cols
        row = i // cols
        rig = factory()
        W2, H2 = CANVAS_W * ss, CANVAS_H * ss
        O = (ORIGIN[0] * ss, ORIGIN[1] * ss)
        s = RIG_SCALE * ss
        tmp = Image.new("RGBA", (W2, H2), (*P["bg"], 255))
        for r, alpha in [(50, 35), (38, 60), (28, 90)]:
            shadow = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
            sd = ImageDraw.Draw(shadow)
            sd.ellipse((O[0] - r * s, O[1] - int(12 * s),
                        O[0] + r * s, O[1] + int(8 * s)),
                       fill=(0, 0, 0, alpha))
            shadow = shadow.filter(ImageFilter.GaussianBlur(int(4 * s)))
            tmp.alpha_composite(shadow)
        draw_rig(tmp, rig, O, facing=1, draw_outline=True, scale=s)
        scaled = tmp.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
        sheet.paste(scaled, (col * CANVAS_W, row * CANVAS_H))
        d = ImageDraw.Draw(sheet)
        d.rectangle((col * CANVAS_W + 6, row * CANVAS_H + 6,
                     col * CANVAS_W + 160, row * CANVAS_H + 30),
                    fill=(0, 0, 0, 200))
        d.text((col * CANVAS_W + 12, row * CANVAS_H + 10), label,
               fill=(240, 240, 250))
    out_path = os.path.join(out_dir, "kaizen_sheet.png")
    os.makedirs(out_dir, exist_ok=True)
    sheet.save(out_path)
    return out_path


# ---------------------------------------------------------------------------
# 8. Main
# ---------------------------------------------------------------------------

def main() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(here, "out")
    os.makedirs(out_dir, exist_ok=True)

    outputs: List[str] = []
    outputs.append(render(pose_idle(), "kaizen_idle", facing=1, out_dir=out_dir))
    outputs.append(render(pose_idle(), "kaizen_idle_left", facing=-1, out_dir=out_dir))
    outputs.append(render(pose_walk(), "kaizen_walk", facing=1, out_dir=out_dir))
    outputs.append(render(pose_q1(), "kaizen_q1", facing=1, out_dir=out_dir))
    outputs.append(render(pose_q2(), "kaizen_q2", facing=1, out_dir=out_dir))
    outputs.append(render(pose_e(), "kaizen_e", facing=1, out_dir=out_dir))
    outputs.append(render(pose_r(), "kaizen_r", facing=1, out_dir=out_dir))

    outputs.append(render_with_vfx(pose_q1(), "kaizen_q1_vfx",
                                   draw_slash_vfx, facing=1, out_dir=out_dir))
    outputs.append(render_with_vfx(pose_r(), "kaizen_r_vfx",
                                   draw_tornado_vfx, facing=1, out_dir=out_dir))

    poses: List[Tuple[str, Callable[[], Node]]] = [
        ("IDLE", pose_idle),
        ("WALK", pose_walk),
        ("Q1 STEEL WIND", pose_q1),
        ("Q2 DASH STRIKE", pose_q2),
        ("E SWEEP", pose_e),
        ("R TORNADO", pose_r),
    ]
    outputs.append(render_sheet(poses, out_dir=out_dir, cols=3))

    print("Rendered:")
    for p in outputs:
        print("  " + os.path.relpath(p, here))
    return 0


if __name__ == "__main__":
    sys.exit(main())
