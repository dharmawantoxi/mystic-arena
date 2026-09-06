#!/usr/bin/env python3
"""
Render Kaizen (procedural rig) to PNG using the SAME vertex data that
kaizen_body_builder.gd uses in Godot.

Why this exists: this sandbox has no Godot binary, so we can't capture a
real Godot render. The next-best thing is to render the same polygons with
the same colours using Pillow — the output matches what Godot would draw,
because the geometry is identical.

Hierarchy (mirrors Godot scene tree):

    Body
    ├── Torso, Chest, Sash, Pelvis
    ├── LeftThigh, RightThigh, LeftBoot, RightBoot
    ├── Scabbard (pivot at hip)
    │   ├── ScabbardBody, ScabbardTip
    ├── SwordArm (pivot at right shoulder, x=10, y=-2)
    │   ├── UpperArm, Forearm, Glove
    │   └── Sword (pivot at hilt, rotated -0.6 rad, x=10, y=22)
    │       ├── SwordHandle, SwordGuard, SwordBlade, SwordEdge
    └── Head (pivot at y=-22)
        ├── Neck, Skull, HairBack, HairFront, TopKnot, Band
        ├── Eye, Iris

To change a pose we mutate the *local* rotation/position of a node; the
draw pass walks the tree and applies the accumulated transform.

Outputs (PNG, 220x260, base at (110, 200)):
    kaizen_idle, kaizen_idle_left, kaizen_walk, kaizen_q1, kaizen_q2,
    kaizen_e, kaizen_r, kaizen_q1_vfx, kaizen_r_vfx, kaizen_sheet
"""

import math
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter

# ---------------------------------------------------------------------------
# 1. Palette (mirrors kaizen_body_builder.gd's P dict)
# ---------------------------------------------------------------------------

P = {
    "ink":          (24, 26, 40),
    "skin_dark":    (120, 84, 66),
    "skin_mid":     (196, 150, 112),
    "skin_light":   (226, 186, 146),
    "hair_dark":    (29, 24, 22),
    "hair_mid":     (86, 68, 50),
    "cloth_dark":   (38, 50, 86),
    "cloth_mid":    (62, 84, 134),
    "cloth_light":  (102, 138, 194),
    "sash":         (86, 130, 206),
    "pants_mid":    (46, 60, 110),
    "pants_dark":   (26, 36, 66),
    "boot":         (21, 16, 11),
    "steel_dark":   (76, 82, 94),
    "steel_mid":    (126, 134, 148),
    "steel_light":  (184, 190, 202),
    "steel_shine":  (230, 236, 246),
    "gold_mid":     (169, 126, 42),
    "saya_dark":    (115, 30, 44),
    "saya_mid":     (161, 45, 63),
    "wrap_mid":     (118, 42, 52),
    "eye_white":    (247, 253, 255),
    "eye_iris":     (206, 152, 54),
    "wind":         (112, 178, 230),
    "wind_bright":  (216, 242, 255),
}


# ---------------------------------------------------------------------------
# 2. Rig data — hierarchical so child transforms compose with parent
# ---------------------------------------------------------------------------

@dataclass
class Node:
    """A rig node. Polygon is in local space (relative to this node's
    own pivot). The node's [position] is in *parent* space (the offset
    from the parent's pivot to this node's pivot). [rotation] is applied
    in the node's local frame."""
    name: str
    color_key: str
    polygon: List[Tuple[float, float]]
    position: Tuple[float, float] = (0.0, 0.0)
    rotation: float = 0.0
    z: int = 0
    children: List["Node"] = field(default_factory=list)
    parent: Optional["Node"] = None
    polygon_offset: Tuple[float, float] = (0.0, 0.0)  # extra offset for the polygon (vs pivot)


def add_child(parent: Node, child: Node) -> Node:
    child.parent = parent
    parent.children.append(child)
    return child


# ---------------------------------------------------------------------------
# 3. Build the rig — same vertex lists as kaizen_body_builder.gd
# ---------------------------------------------------------------------------

def build_rig() -> Node:
    """Build the rig in the same hierarchy as the Godot scene.

    Returns the Body root. Each node is a (pivot-anchored) child of its
    parent, so changing a parent's rotation propagates to all children."""
    body = Node(name="Body", color_key="ink", polygon=[],
                position=(0.0, 0.0), z=-1)

    # ---- Legs (z=0..1) ----
    body.children.append(Node("LeftThigh",  "pants_mid",
        polygon=[(-8, 26), (-2, 26), (-3, 42), (-7, 42)], z=0))
    body.children.append(Node("RightThigh", "pants_mid",
        polygon=[(2, 26), (8, 26), (7, 42), (3, 42)], z=0))
    body.children.append(Node("LeftBoot",  "boot",
        polygon=[(-8, 40), (-2, 40), (-1, 48), (-9, 48)], z=1))
    body.children.append(Node("RightBoot", "boot",
        polygon=[(2, 40), (8, 40), (9, 48), (1, 48)], z=1))

    # ---- Pelvis / sash / torso ----
    body.children.append(Node("Pelvis",  "cloth_dark",
        polygon=[(-10, 18), (10, 18), (8, 28), (-8, 28)], z=2))
    body.children.append(Node("Sash",  "sash",
        polygon=[(-13, 8), (13, 8), (11, 16), (-11, 16)], z=7))
    body.children.append(Node("Torso",  "cloth_mid",
        polygon=[(-12, -8), (12, -8), (14, 14), (10, 22), (-10, 22), (-14, 14)], z=5))
    body.children.append(Node("Chest", "cloth_dark",
        polygon=[(-10, -4), (10, -4), (8, 4), (-8, 4)], z=6))

    # ---- Scabbard (group, pivot at left hip) ----
    scabbard = Node("Scabbard", "saya_mid", polygon=[],
                    position=(-8, 14), z=3)
    scabbard.children.append(Node("ScabbardBody", "saya_mid",
        polygon=[(-3, 0), (3, 0), (2, 30), (-2, 30)], z=3))
    scabbard.children.append(Node("ScabbardTip", "saya_dark",
        polygon=[(-3, 0), (3, 0), (0, 4)], position=(0, 30), z=4))
    body.children.append(scabbard)

    # ---- Sword arm (pivot at right shoulder) ----
    sword_arm = Node("SwordArm", "cloth_dark", polygon=[],
                     position=(10, -2), z=16)
    sword_arm.children.append(Node("UpperArm", "cloth_dark",
        polygon=[(-4, 0), (4, 0), (5, 14), (-5, 14)], z=16))
    sword_arm.children.append(Node("Forearm", "skin_mid",
        polygon=[(-3, 0), (3, 0), (4, 12), (-4, 12)],
        position=(0, 12), z=17))
    sword_arm.children.append(Node("Glove", "boot",
        polygon=[(-4, 0), (4, 0), (5, 4), (-5, 4)],
        position=(0, 22), z=18))

    # ---- Sword (pivot at hilt, inside sword arm) ----
    # In Godot, the sword is rotated -0.6 rad at rest. We bake that as the
    # node's rotation. Children of the sword inherit this rotation.
    sword = Node("Sword", "steel_light", polygon=[],
                 position=(0, 24), rotation=-0.6, z=19)
    sword.children.append(Node("SwordHandle", "wrap_mid",
        polygon=[(-2, 0), (2, 0), (2, 8), (-2, 8)], z=19))
    sword.children.append(Node("SwordGuard", "gold_mid",
        polygon=[(-5, -1), (5, -1), (5, 2), (-5, 2)],
        position=(0, 8), z=20))
    sword.children.append(Node("SwordBlade", "steel_light",
        polygon=[(-2, 0), (2, 0), (1, 38), (-1, 38)],
        position=(0, 10), z=21))
    sword.children.append(Node("SwordEdge", "steel_shine",
        polygon=[(0, 0), (2, 0), (1, 36), (0, 36)],
        position=(0, 11), z=22))
    sword_arm.children.append(sword)
    body.children.append(sword_arm)

    # ---- Head (pivot at y=-22) ----
    head = Node("Head", "skin_mid", polygon=[],
                position=(0, -22), z=8)
    head.children.append(Node("Neck", "skin_mid",
        polygon=[(-4, 8), (4, 8), (3, 14), (-3, 14)], z=8))
    head.children.append(Node("Skull", "skin_mid",
        polygon=[(-9, -10), (9, -10), (10, 0), (8, 6), (-8, 6), (-10, 0)], z=9))
    head.children.append(Node("HairBack", "hair_dark",
        polygon=[(-11, -12), (11, -12), (10, -4), (6, -2), (-6, -2), (-10, -4)], z=10))
    head.children.append(Node("HairFront", "hair_dark",
        polygon=[(-10, -10), (10, -10), (8, -4), (-8, -4)], z=11))
    head.children.append(Node("TopKnot", "hair_dark",
        polygon=[(-4, -16), (4, -16), (3, -10), (-3, -10)], z=12))
    head.children.append(Node("Band", "wrap_mid",
        polygon=[(-10, -6), (10, -6), (9, -4), (-9, -4)], z=13))
    head.children.append(Node("Eye", "eye_white",
        polygon=[(-6, -2), (-2, -2), (-2, 1), (-6, 1)], z=14))
    head.children.append(Node("Iris", "eye_iris",
        polygon=[(-5, -1), (-3, -1), (-3, 0), (-5, 0)], z=15))
    body.children.append(head)

    return body


# ---------------------------------------------------------------------------
# 4. Walk the tree and draw
# ---------------------------------------------------------------------------

def collect_draw_order(root: Node) -> List[Node]:
    """Return leaves and shape-nodes in the correct z-order. Group nodes
    (with no polygon) are skipped — they only carry children."""
    out: List[Node] = []

    def walk(node: Node):
        if node.polygon:
            out.append(node)
        for c in node.children:
            walk(c)

    walk(root)
    out.sort(key=lambda n: n.z)
    return out


def compute_world_matrix(node: Node) -> Tuple[float, float, float, float]:
    """Walk up the parent chain and accumulate rotation+translation.

    Returns (cos_total, sin_total, dx, dy) where (dx, dy) is the
    translation that maps the node's *local* polygon to the world.

    Godot 2D transform composition:
        M_world = M_parent * M_local
        where M_local = translate(local_pos) * rotate(local_rot).
    We accumulate by:
        R := R_parent * R_local
        pos := pos_parent + R_parent * local_pos
    """
    # Build chain from root to this node.
    chain: List[Node] = []
    n = node
    while n is not None:
        chain.append(n)
        n = n.parent
    chain.reverse()

    # The chain[0] is the root (Body) — its rotation/position is the
    # identity for the rig (we apply facing/origin at the draw level).
    # We start with the root's rotation, then for each child we compose.
    cos_t = math.cos(chain[0].rotation)
    sin_t = math.sin(chain[0].rotation)
    dx = chain[0].position[0]
    dy = chain[0].position[1]
    for c in chain[1:]:
        # Position offset, rotated by current R (which is the parent's
        # accumulated rotation — NOT yet including c.rotation).
        rx = c.position[0] * cos_t - c.position[1] * sin_t
        ry = c.position[0] * sin_t + c.position[1] * cos_t
        dx += rx
        dy += ry
        # Apply child's local rotation.
        ca = math.cos(c.rotation)
        sa = math.sin(c.rotation)
        cos_t, sin_t = cos_t * ca - sin_t * sa, cos_t * sa + sin_t * ca
    return cos_t, sin_t, dx, dy


def draw_rig(img: Image.Image, root: Node, body_origin: Tuple[int, int],
             facing: int = 1) -> None:
    draw = ImageDraw.Draw(img, "RGBA")
    nodes = collect_draw_order(root)
    for node in nodes:
        cos_t, sin_t, dx, dy = compute_world_matrix(node)
        # Polygon -> world coords.
        world: List[Tuple[float, float]] = []
        for (x, y) in node.polygon:
            # Apply polygon offset (in node-local space).
            x += node.polygon_offset[0]
            y += node.polygon_offset[1]
            # Apply accumulated transform.
            wx = x * cos_t - y * sin_t + dx
            wy = x * sin_t + y * cos_t + dy
            # Apply facing flip.
            wx = wx * facing + body_origin[0]
            wy = wy + body_origin[1]
            world.append((wx, wy))
        color = P.get(node.color_key, (200, 0, 200))
        draw.polygon(world, fill=color)


# ---------------------------------------------------------------------------
# 5. Pose variants
# ---------------------------------------------------------------------------

def find_node(root: Node, name: str) -> Optional[Node]:
    """Depth-first search by name."""
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
    r = build_rig()
    # Leg stagger.
    find_node(r, "LeftThigh").position = (-5, 27)
    find_node(r, "LeftBoot").position = (-5, 41)
    find_node(r, "RightThigh").position = (5, 25)
    find_node(r, "RightBoot").position = (5, 39)
    # Sword arm swings slightly.
    find_node(r, "SwordArm").rotation = 0.12
    return r


def pose_q1() -> Node:
    """Q1 — Steel Wind: horizontal slash, sword arm swung down/forward.
    To swing the entire arm, rotate the SwordArm group. The Sword
    inside it is rotated -0.6 by default, so the total blade angle
    ends up roughly horizontal."""
    r = build_rig()
    sa = find_node(r, "SwordArm")
    sa.rotation = 0.9          # arm rotated forward
    # Forearm adds a small extra fold.
    find_node(r, "Forearm").rotation = -0.3
    return r


def pose_q2() -> Node:
    """Q2 — Dash Strike: crouch + sword pulled back over the shoulder."""
    r = build_rig()
    # Crouch.
    for n in ["Pelvis", "LeftThigh", "RightThigh", "LeftBoot", "RightBoot",
              "Torso", "Chest", "Sash", "Scabbard"]:
        node = find_node(r, n)
        if node is not None:
            node.position = (node.position[0], node.position[1] + 3)
    # Sword arm pulled way back (rotation = -1.6 rad).
    sa = find_node(r, "SwordArm")
    sa.rotation = -1.5
    find_node(r, "Forearm").rotation = 0.3
    return r


def pose_e() -> Node:
    """E — Sweep: mid-jump, sweeping low."""
    r = build_rig()
    # Jump (everything moves up by 6).
    for n in ["LeftThigh", "RightThigh", "LeftBoot", "RightBoot",
              "Pelvis", "Torso", "Chest", "Sash", "Scabbard"]:
        node = find_node(r, n)
        if node is not None:
            node.position = (node.position[0], node.position[1] - 6)
    # Slight forward lean.
    for n in ["Torso", "Chest", "Sash"]:
        node = find_node(r, n)
        if node is not None:
            node.rotation = 0.2
    # Sword sweeps low: arm forward, forearm angled down.
    sa = find_node(r, "SwordArm")
    sa.rotation = 1.4
    find_node(r, "Forearm").rotation = 0.5
    return r


def pose_r() -> Node:
    """R — Tornado: sword held high overhead, ready to spin."""
    r = build_rig()
    sa = find_node(r, "SwordArm")
    sa.rotation = -2.4
    # Forearm adds a small angle.
    find_node(r, "Forearm").rotation = -0.3
    return r


# ---------------------------------------------------------------------------
# 6. VFX overlays
# ---------------------------------------------------------------------------

def draw_slash_vfx(img: Image.Image, origin: Tuple[int, int],
                   facing: int = 1, scale: float = 1.0) -> None:
    """Crescent slash effect — matches the Godot KaizenSlash.gd scene."""
    draw = ImageDraw.Draw(img, "RGBA")
    cx, cy = origin
    arc_deg = 120
    outer = int(64 * scale)
    thickness = int(16 * scale)
    half = math.radians(arc_deg * 0.5)
    steps = 32

    def arc(radius: float) -> List[Tuple[float, float]]:
        pts: List[Tuple[float, float]] = []
        for i in range(steps + 1):
            t = i / steps
            a = -half + t * 2.0 * half
            pts.append((cx + math.cos(a) * radius * facing,
                        cy + math.sin(a) * radius))
        return pts

    outer_pts = arc(outer)
    inner_pts = arc(outer - thickness)
    crescent = outer_pts + list(reversed(inner_pts))
    glow_outer = arc(outer + 22)
    glow_inner = arc(outer - thickness - 22)
    glow = glow_outer + list(reversed(glow_inner))

    # Layered draw: glow (back), main crescent, inner accent.
    draw.polygon(glow, fill=(*P["wind"], 90))
    draw.polygon(crescent, fill=P["wind_bright"])
    # Inner accent wedge (small bright triangle).
    half_acc = half * 0.35
    inner: List[Tuple[float, float]] = []
    for i in range(steps + 1):
        t = i / steps
        a = -half_acc + t * 2.0 * half_acc
        inner.append((cx + math.cos(a) * (outer - thickness - 4) * facing,
                      cy + math.sin(a) * (outer - thickness - 4)))
    for i in range(steps + 1):
        t = i / steps
        a = half_acc - t * 2.0 * half_acc
        inner.append((cx + math.cos(a) * 4 * facing, cy + math.sin(a) * 4))
    draw.polygon(inner, fill=(255, 255, 255))


def draw_tornado_vfx(img: Image.Image, origin: Tuple[int, int],
                     facing: int = 1, scale: float = 1.0) -> None:
    """Tornado — concentric ellipse bands, central streak, orbiting sparks."""
    draw = ImageDraw.Draw(img, "RGBA")
    cx, cy = origin
    height = int(180 * scale)
    top_r = int(28 * scale)
    bottom_r = int(64 * scale)
    bands = 6
    for i in range(bands):
        t = i / max(1, bands - 1)
        y = cy - height // 2 + int(t * height)
        rx = max(4, int((bottom_r + (top_r - bottom_r) * t) * scale))
        ry = max(2, int(rx * 0.42))
        wobble = int(math.sin(i * 1.3) * 1.5)
        bbox = (cx - rx - wobble, y - ry, cx + rx + wobble, y + ry)
        col_a = P["wind_dark"] = (60, 110, 180)
        col_b = P["wind"]
        col = tuple(int(col_a[k] + (col_b[k] - col_a[k]) * t) for k in range(3))
        draw.ellipse(bbox, outline=(*col, 200), width=3)
    # Vertical core streak.
    draw.line((cx, cy - height // 2, cx, cy + height // 2),
              fill=(*P["wind_bright"], 230), width=4)
    # Sparks.
    rng = random.Random(7)
    for _ in range(10):
        t = rng.random()
        y = cy - height // 2 + int(t * height)
        r = int((bottom_r + (top_r - bottom_r) * t) * scale) + 8
        ang = rng.random() * 6.28318
        sx = int(cx + math.cos(ang) * r)
        sy = int(y + math.sin(ang) * r * 0.4)
        draw.ellipse((sx - 2, sy - 2, sx + 2, sy + 2), fill=P["wind_bright"])


# ---------------------------------------------------------------------------
# 7. Renderer
# ---------------------------------------------------------------------------

CANVAS_W = 220
CANVAS_H = 260
ORIGIN = (110, 210)        # feet line


def render(rig: Node, name: str, facing: int = 1, out_dir: str = "out") -> str:
    img = Image.new("RGBA", (CANVAS_W, CANVAS_H), (46, 42, 36, 255))
    # Floor shadow.
    shadow = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse((ORIGIN[0] - 32, ORIGIN[1] - 8, ORIGIN[0] + 32, ORIGIN[1] + 6),
               fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(3))
    img.alpha_composite(shadow)
    draw_rig(img, rig, ORIGIN, facing=facing)
    out_path = os.path.join(out_dir, name + ".png")
    os.makedirs(out_dir, exist_ok=True)
    img.save(out_path)
    return out_path


def render_with_vfx(rig: Node, name: str, vfx_fn: Callable,
                    facing: int = 1, out_dir: str = "out") -> str:
    img = Image.new("RGBA", (CANVAS_W, CANVAS_H), (46, 42, 36, 255))
    shadow = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse((ORIGIN[0] - 32, ORIGIN[1] - 8, ORIGIN[0] + 32, ORIGIN[1] + 6),
               fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(3))
    img.alpha_composite(shadow)
    draw_rig(img, rig, ORIGIN, facing=facing)
    vfx_origin = (ORIGIN[0] + 36 * facing, ORIGIN[1] - 50)
    vfx_fn(img, vfx_origin, facing=facing)
    out_path = os.path.join(out_dir, name + ".png")
    os.makedirs(out_dir, exist_ok=True)
    img.save(out_path)
    return out_path


def render_sheet(poses: List[Tuple[str, Callable[[], Node]]],
                 out_dir: str = "out", cols: int = 3) -> str:
    rows = (len(poses) + cols - 1) // cols
    sheet = Image.new("RGBA", (CANVAS_W * cols, CANVAS_H * rows),
                      (32, 28, 22, 255))
    for i, (label, factory) in enumerate(poses):
        col = i % cols
        row = i // cols
        rig = factory()
        tmp = Image.new("RGBA", (CANVAS_W, CANVAS_H), (46, 42, 36, 255))
        shadow = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.ellipse((ORIGIN[0] - 32, ORIGIN[1] - 8,
                    ORIGIN[0] + 32, ORIGIN[1] + 6),
                   fill=(0, 0, 0, 120))
        shadow = shadow.filter(ImageFilter.GaussianBlur(3))
        tmp.alpha_composite(shadow)
        draw_rig(tmp, rig, ORIGIN, facing=1)
        sheet.paste(tmp, (col * CANVAS_W, row * CANVAS_H))
        # Label.
        d = ImageDraw.Draw(sheet)
        d.rectangle((col * CANVAS_W + 4, row * CANVAS_H + 4,
                     col * CANVAS_W + 110, row * CANVAS_H + 24),
                    fill=(0, 0, 0, 180))
        d.text((col * CANVAS_W + 8, row * CANVAS_H + 6), label,
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

    # VFX overlays.
    outputs.append(render_with_vfx(pose_q1(), "kaizen_q1_vfx",
                                   draw_slash_vfx, facing=1, out_dir=out_dir))
    outputs.append(render_with_vfx(pose_r(), "kaizen_r_vfx",
                                   draw_tornado_vfx, facing=1, out_dir=out_dir))

    # Sprite sheet of all poses.
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
