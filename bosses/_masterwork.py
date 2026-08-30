"""
bosses/_masterwork.py - Mesin "Procedural Masterwork" bersama untuk boss.

Standar yang dipakai Kaizen / Gornak / Drakar (lihat bosses/level1.py):

* SATU bone rig 2D berlapis - sendi (pinggul, lutut, mata kaki, bahu, siku,
  pergelangan) dihitung TIAP frame dari ``phase``/``action``. Siluet tidak
  pernah pecah saat berjalan/memukul.
* Telapak kaki DIPATOK ke ``GROUND_DY`` sementara badan bernapas/bob.
* Senjata POSE-DRIVEN: sudut senjata diturunkan dari garis lengan
  (siku -> pergelangan) + tilt per-pose, jadi senjata selalu menempel tangan.
* Idle bob >= 4 px terlihat.
* Walk: kaki alternating stride + lift, badan sway.
* Attack: windup + lunge + impact yang distinktif (beda dari idle).
* Skill FX: ground ring + partikel + kilat dramatis per fase
  (charge / burst / afterglow).
* Portrait HD (``_portrait_hd=True``): skip aura/ground FX.
* Kedua arah (facing kiri/kanan) benar.

Modul ini menyuplai primitif gambar + solver sendi + composer outline +
FX skill generik, sehingga tiap namespace boss di level2.py hanya perlu
menyediakan PALETTE dan painter bagian tubuh spesifik.
"""

import math

import pygame

try:                                   # pass cahaya bersama; opsional
    import lighting as _lighting
except Exception:                      # pragma: no cover
    _lighting = None

HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
HAS_AALINES = hasattr(pygame.draw, "aalines")


# ======================================================================
# PRIMITIF HELPER (mendukung warna alpha lewat surface sementara)
# ======================================================================
def clamp(color):
    return tuple(max(0, min(255, int(c))) for c in color)


def alpha(v):
    return max(0, min(255, int(v)))


def aacircle(surface, color, center, radius, width=0):
    color = clamp(color)
    cx, cy = int(center[0]), int(center[1])
    radius = max(0, int(radius))
    if radius <= 0:
        return
    if len(color) == 4 and color[3] < 255:
        temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4),
                              pygame.SRCALPHA)
        pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius,
                           width)
        surface.blit(temp, (cx - radius - 2, cy - radius - 2))
        return
    if HAS_AACIRCLE and radius > 1:
        try:
            pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
            return
        except Exception:
            pass
    pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


def aaline(surface, color, start, end, width=1):
    color = clamp(color)
    sx, sy = int(start[0]), int(start[1])
    ex, ey = int(end[0]), int(end[1])
    width = max(1, int(width))
    if len(color) == 4 and color[3] < 255:
        min_x = min(sx, ex) - width - 2
        min_y = min(sy, ey) - width - 2
        w = abs(ex - sx) + width * 4 + 6
        h = abs(ey - sy) + width * 4 + 6
        if w <= 0 or h <= 0:
            return
        temp = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.line(temp, color, (sx - min_x, sy - min_y),
                         (ex - min_x, ey - min_y), width)
        surface.blit(temp, (min_x, min_y))
        return
    if HAS_AALINES and width == 1:
        try:
            pygame.draw.aaline(surface, color[:3], (sx, sy), (ex, ey))
            return
        except Exception:
            pass
    pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), width)


def poly(surface, color, points):
    if not points or len(points) < 3:
        return
    color = clamp(color)
    if len(color) == 4 and color[3] < 255:
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        min_x, min_y = min(xs) - 2, min(ys) - 2
        w = max(xs) - min_x + 4
        h = max(ys) - min_y + 4
        if w <= 0 or h <= 0:
            return
        temp = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.polygon(temp, color,
                            [(p[0] - min_x, p[1] - min_y) for p in points])
        surface.blit(temp, (min_x, min_y))
        return
    pygame.draw.polygon(surface, color[:3], points)


def ellipse(surface, color, rect, width=0):
    color = clamp(color)
    rx, ry, rw, rh = int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3])
    if rw <= 0 or rh <= 0:
        return
    if len(color) == 4 and color[3] < 255:
        temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
        pygame.draw.ellipse(temp, color, (2, 2, rw, rh), width)
        surface.blit(temp, (rx - 2, ry - 2))
        return
    pygame.draw.ellipse(surface, color[:3], (rx, ry, rw, rh), width)


def rect(surface, color, r):
    color = clamp(color)
    rx, ry, rw, rh = int(r[0]), int(r[1]), int(r[2]), int(r[3])
    if rw <= 0 or rh <= 0:
        return
    if len(color) == 4 and color[3] < 255:
        temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
        pygame.draw.rect(temp, color, (2, 2, rw, rh))
        surface.blit(temp, (rx - 2, ry - 2))
        return
    pygame.draw.rect(surface, color[:3], (rx, ry, rw, rh))


# ======================================================================
# SOLVER SENDI (two-bone IK)
# ======================================================================
def solve_joint(a, b, bend):
    """Titik tengah dua tulang + offset tegak lurus (siku / lutut).

    ``a`` pangkal, ``b`` ujung, ``bend`` besar & arah lengkungan.
    """
    mx = (a[0] + b[0]) * 0.5
    my = (a[1] + b[1]) * 0.5
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    ln = math.hypot(dx, dy) or 1.0
    return (int(mx + (-dy / ln) * bend), int(my + (dx / ln) * bend))


def limb_dir(a, b):
    """Sudut (radian) garis a->b dari sumbu +x."""
    return math.atan2(b[1] - a[1], b[0] - a[0])


# ======================================================================
# KONFIGURASI RIG
# ======================================================================
class RigConfig(object):
    """Parameter skala/buffer/durasi satu boss."""

    def __init__(self, name, palette, scale=1.3, lift=4, feet_dy=44,
                 rig_w=176, rig_h=168, rig_ox=88, rig_oy=100,
                 skill_dur=None, shadow=True):
        self.name = name
        self.PALETTE = palette
        self.SCALE = float(scale)
        self.LIFT = int(lift)
        self.FEET_DY = int(feet_dy)
        self.GROUND_DY = int(round(self.FEET_DY * self.SCALE)) - self.LIFT
        self.RIG_W = int(rig_w)
        self.RIG_H = int(rig_h)
        self.RIG_OX = int(rig_ox)
        self.RIG_OY = int(rig_oy)
        self.GRAD_BOX = (self.RIG_OX - 54, self.RIG_OY - 52, 126, 102)
        self.SKILL_DUR = skill_dur or {"q": 40, "w": 50, "e": 35, "r": 90}
        self.shadow = shadow


# ======================================================================
# STATE ANIMASI (murni, tanpa efek samping visual)
# ======================================================================
def update_attack_anim(boss, pfx, cooldown_default=40):
    cooldown = max(2, int(getattr(boss, "attack_cooldown", cooldown_default)))
    timer = int(getattr(boss, "timer", 0))
    previous = int(getattr(boss, pfx + "_prev_timer", 0))
    active = bool(getattr(boss, pfx + "_attack_active", False))

    if timer >= cooldown - 1 and previous <= 1:
        setattr(boss, pfx + "_attack_active", True)
        setattr(boss, pfx + "_attack_frame", 0)
        active = True
    elif active and timer > 0:
        setattr(boss, pfx + "_attack_frame",
                int(getattr(boss, pfx + "_attack_frame", 0)) + 1)
    elif timer <= 0:
        setattr(boss, pfx + "_attack_active", False)
        setattr(boss, pfx + "_attack_frame", 0)
        active = False

    setattr(boss, pfx + "_prev_timer", timer)
    setattr(boss, pfx + "_attack_progress",
            min(1.0, getattr(boss, pfx + "_attack_frame", 0) /
                max(1, cooldown - 1)) if active else 0.0)
    return active


def detect_moving(boss, pfx):
    cur_x = float(getattr(boss, "x", 0.0))
    cur_y = float(getattr(boss, "y", 0.0))
    if not hasattr(boss, pfx + "_last_x"):
        setattr(boss, pfx + "_last_x", cur_x)
        setattr(boss, pfx + "_last_y", cur_y)
        return False
    moved = (abs(cur_x - getattr(boss, pfx + "_last_x")) +
             abs(cur_y - getattr(boss, pfx + "_last_y")))
    setattr(boss, pfx + "_last_x", cur_x)
    setattr(boss, pfx + "_last_y", cur_y)
    return moved > 0.3


def attack_curve(ap):
    """Remap progres mentah -> waktu pose: anticipation, swing cepat,
    IMPACT hold, lalu recovery. MONOTON naik (lihat gornak)."""
    if ap <= 0.0:
        return 0.0
    if ap < 0.28:
        t = ap / 0.28
        return 0.26 * (t ** 0.75)
    if ap < 0.50:
        t = (ap - 0.28) / 0.22
        return 0.26 + 0.53 * (t ** 0.5)
    if ap < 0.62:
        t = (ap - 0.50) / 0.12
        return 0.79 + 0.05 * t
    t = (ap - 0.62) / 0.38
    return 0.84 + 0.16 * (t ** 0.85)


def resolve_pose(boss, pfx, moving=False, skill_map=None):
    """(action, phase, ap). action = idle/walk/attack atau huruf skill."""
    skill_map = skill_map or {}
    active_skill = getattr(boss, "active_skill", None)
    if active_skill in ("q", "w", "e", "r"):
        action = skill_map.get(active_skill, active_skill)
    elif (getattr(boss, pfx + "_attack_active", False)
          or getattr(boss, "timer", 0) >
          getattr(boss, "attack_cooldown", 40) - 15):
        action = "attack"
    elif moving:
        action = "walk"
    else:
        action = "idle"

    phase = float(getattr(boss, "pulse", 0.0))
    if action == "walk":
        phase *= 2.0
    ap = 0.0
    if action == "attack":
        raw = max(0.0, min(1.0, float(getattr(boss, pfx + "_attack_progress",
                                              0.0))))
        ap = attack_curve(raw)
    return action, phase, ap


def rig_shift(action, phase, ap):
    """(lean, root_y) badan; kaki TIDAK ikut (menapak)."""
    lean = 0
    # idle bob >= 4 px layar (root_y lokal * SCALE). Dengan SCALE ~1.3,
    # amplitudo lokal 3.2 -> ~4.2 px.
    root_y = int(round(math.sin(phase * 0.62) * 3.2))
    if action == "walk":
        lean = int(math.sin(phase * 1.72) * 2)
        root_y -= int(abs(math.sin(phase * 1.15)) * 3.0)
    elif action == "attack":
        t = math.sin(ap * math.pi)
        lean = int(t * 6)
        root_y += int(t * 2)
    elif action in ("q", "surge"):
        lean = 3
        root_y -= 2
    elif action in ("e", "r", "ward", "void"):
        root_y -= 3
    elif action in ("w", "blink"):
        lean = 1
        root_y -= 2
    return lean, root_y


# ======================================================================
# KONTEKS POSE - dikirim ke painter bagian tubuh
# ======================================================================
class Pose(object):
    """Semua nilai per-frame yang dibutuhkan painter.

    Atribut utama: action, phase, ap, facing(f), lean, root_y, breath,
    stride, dan closure pt/ptg/poly/limb/dot.
    """

    def __init__(self, cfg, surface, cx, cy, facing, phase, action, ap,
                 detail=False):
        self.cfg = cfg
        self.surface = surface
        self.cx = cx
        self.cy = cy
        self.f = 1 if facing >= 0 else -1
        self.phase = phase
        self.action = action
        self.ap = ap
        self.detail = detail
        self.lean, self.root_y = rig_shift(action, phase, ap)
        self.breath = math.sin(phase * 0.62)
        self.stride = math.sin(phase * 1.72) if action == "walk" else 0.0
        p = cfg.PALETTE

        def pt(dx, dy):
            return self._l2s(self.lean, self.root_y, dx, dy)

        def ptg(dx, dy):
            # kaki menapak: root_y = 0
            return self._l2s(self.lean, 0, dx, dy)

        self.pt = pt
        self.ptg = ptg

        def poly_free(color, pts, outline=True):
            if outline:
                poly(surface, p.get("shadow_deep", (0, 0, 0)),
                     [(q[0] + self.f, q[1] + 1) for q in pts])
            poly(surface, color, pts)
            return pts

        self.poly_free = poly_free

        def dot(dx, dy, r, color, outline=True):
            sx, sy = pt(dx, dy)
            rr = self._s(r)
            if outline:
                aacircle(surface, p.get("shadow_deep", (0, 0, 0)),
                         (sx + self.f, sy + 1), rr + 1)
            aacircle(surface, color, (sx, sy), rr)

        self.dot = dot

        def limb(a, b, width, base, light=None):
            aa, bb = pt(*a), pt(*b)
            w = self._s(width)
            aaline(surface, p.get("shadow_deep", (0, 0, 0)),
                   (aa[0] + self.f, aa[1] + 1), (bb[0] + self.f, bb[1] + 1),
                   w + 2)
            aaline(surface, base, aa, bb, w)
            if light:
                off = -1 if self.f > 0 else 1
                aaline(surface, light, (aa[0] + off, aa[1] - 1),
                       (bb[0] + off, bb[1] - 1), max(1, self._s(width // 3)))

        self.limb = limb

    def _s(self, v):
        return max(1, int(round(v * self.cfg.SCALE)))

    def _l2s(self, lean, root_y, lx, ly):
        f = self.f
        k = self.cfg.SCALE
        return (int(self.cx + (lx * f + lean * f) * k),
                int(self.cy - self.cfg.LIFT + (ly + root_y) * k))

    s = property(lambda self: self._s)


# ======================================================================
# KAKI 2-TULANG (pinggul -> lutut -> mata kaki -> telapak) menapak
# ======================================================================
def leg_joints(P, side, hip_y=4, ground=None, stride_amt=8, lift_amt=5,
               stance=4):
    """Return (hip, knee, ankle, foot) dalam koordinat layar.

    ``side`` -1 = kaki belakang, +1 = kaki depan. Telapak dipatok ke
    ``ground`` (FEET_DY lokal) dikurangi lift; lutut dihitung two-bone.
    """
    cfg = P.cfg
    ground = cfg.FEET_DY if ground is None else ground
    action = P.action
    if action == "walk":
        dx = int(P.stride * stride_amt) * side
        lift = int(max(0.0, -P.stride * side) * lift_amt)
    elif action == "attack":
        dx = stance + 3 if side > 0 else -(stance + 3)
        lift = 0
    elif action in ("q", "surge", "e", "r", "w", "ward", "void"):
        dx = stance + 2 if side > 0 else -(stance + 2)
        lift = 0
    else:
        dx = stance if side > 0 else -(stance + 2)
        lift = 0
    hip_x = side * 7
    hip = (hip_x, hip_y)
    foot = (hip_x + dx + side * 2, ground - lift)
    knee = solve_joint(hip, foot, 4.0 * P.f if P.f else 4.0)
    # lutut menekuk ke DEPAN (arah hadap)
    knee = (int((hip[0] + foot[0]) * 0.5 + P.f * 3),
            int((hip[1] + foot[1]) * 0.5 - 1 - lift * 0.3))
    ankle = (foot[0], foot[1] - 3)
    return hip, knee, ankle, foot


# ======================================================================
# LENGAN 2-TULANG + senjata pose-driven
# ======================================================================
def arm_joints(P, shoulder, grip, bend=-4.5):
    elbow = solve_joint(shoulder, grip, bend)
    return elbow


def weapon_angle_from_arm(elbow, wrist, tilt=0.0):
    """Sudut senjata diturunkan dari garis lengan + tilt per-pose."""
    return limb_dir(elbow, wrist) + tilt


def weapon_tip(wrist, angle, length):
    return (int(wrist[0] + math.cos(angle) * length),
            int(wrist[1] + math.sin(angle) * length))


# ======================================================================
# PEMBANGUN BAGIAN TUBUH GENERIK (dipakai painter per-boss)
# ======================================================================
def draw_leg(P, side, colors, stance=4, stride_amt=8, lift_amt=5,
             thigh_w=5, shin_w=4, boot=True):
    """Kaki two-bone menapak: paha -> lutut -> tulang kering -> boot."""
    hip, knee, ankle, foot = leg_joints(P, side, stance=stance,
                                        stride_amt=stride_amt,
                                        lift_amt=lift_amt)
    sd = colors.get("shadow_deep", (0, 0, 0))
    # pinggul ikut bob badan (pt); lutut->telapak TERPATOK tanah (ptg)
    hp = P.pt(*hip)
    kn = P.ptg(*knee)
    an = P.ptg(*ankle)
    ft = P.ptg(*foot)
    # paha (pinggul->lutut)
    w = P._s(thigh_w)
    aaline(P.surface, sd, (hp[0] + P.f, hp[1] + 1), (kn[0] + P.f, kn[1] + 1), w + 2)
    aaline(P.surface, colors["thigh"], hp, kn, w)
    if colors.get("thigh_light"):
        off = -1 if P.f > 0 else 1
        aaline(P.surface, colors["thigh_light"], (hp[0] + off, hp[1] - 1),
               (kn[0] + off, kn[1] - 1), max(1, P._s(thigh_w // 3)))
    # lutut
    aacircle(P.surface, sd, (kn[0] + P.f, kn[1] + 1), P._s(2.4) + 1)
    aacircle(P.surface, colors["knee"], kn, P._s(2.4))
    # shin (lutut->mata kaki)
    w2 = P._s(shin_w)
    aaline(P.surface, sd, (kn[0] + P.f, kn[1] + 1), (an[0] + P.f, an[1] + 1), w2 + 2)
    aaline(P.surface, colors["shin"], kn, an, w2)
    if colors.get("shin_light"):
        off = -1 if P.f > 0 else 1
        aaline(P.surface, colors["shin_light"], (kn[0] + off, kn[1] - 1),
               (an[0] + off, an[1] - 1), max(1, P._s(shin_w // 3)))
    # boot / telapak menapak
    if boot:
        f = P.f
        toe = (ft[0] + f * P._s(5), ft[1])
        poly(P.surface, colors["boot"], [an, ft, toe, (an[0], an[1] - 1)])
        aaline(P.surface, colors.get("boot_edge", colors["boot"]), an, toe, 1)
    return hip, knee, ankle, foot


def draw_arm(P, shoulder, grip, bend, colors, weapon=None, hand_r=2.4):
    """Lengan two-bone + tangan + senjata pose-driven opsional.

    ``weapon`` dict: {len, tilt, blade, edge, glow} -> gambar bilah dari
    pergelangan mengikuti sudut lengan."""
    elbow = arm_joints(P, shoulder, grip, bend)
    sh, el, wr = P.pt(*shoulder), P.pt(*elbow), P.pt(*grip)
    P.limb(shoulder, elbow, colors.get("upper_w", 4), colors["upper"],
           colors.get("upper_light"))
    P.limb(elbow, grip, colors.get("fore_w", 3.5), colors["fore"],
           colors.get("fore_light"))
    P.dot(*grip, hand_r, colors["hand"])
    tip = None
    if weapon:
        # sudut dari garis lengan LOKAL, tapi ujung bilah dihitung di
        # koordinat LAYAR dari pergelangan (wr) supaya menempel di tangan.
        ang = weapon_angle_from_arm(elbow, grip, weapon.get("tilt", 0.0))
        L = weapon["len"]
        tip = weapon_tip(wr, ang, L)
        # bayangan lalu bilah
        aaline(P.surface, colors.get("shadow_deep", (0, 0, 0)),
               (wr[0] + P.f, wr[1] + 1), (tip[0] + P.f, tip[1] + 1),
               P._s(weapon.get("w", 3)) + 2)
        aaline(P.surface, weapon["blade"], wr, tip, P._s(weapon.get("w", 3)))
        aaline(P.surface, weapon["edge"], wr, tip, max(1, P._s(1)))
        if weapon.get("glow"):
            aaline(P.surface, (*weapon["glow"], 140), wr, tip, 1)
    return elbow, wr, tip


def draw_torso(P, colors, hip_y=4, shoulder_y=-14, w=12, breath=None):
    """Torso pelvis->dada dengan napas (breath) menggeser dada."""
    b = P.breath if breath is None else breath
    lift = int(b * 1.2)
    sd = colors.get("shadow_deep", (0, 0, 0))
    pelvis = [(-w + 2, hip_y - 2), (w - 2, hip_y - 2), (w - 4, hip_y + 4),
              (-w + 4, hip_y + 4)]
    P.poly_free(colors["pelvis"], [P.pt(*q) for q in pelvis])
    chest = [(-w, shoulder_y + 2 - lift), (w, shoulder_y + 2 - lift),
             (w - 2, hip_y - 2), (-w + 2, hip_y - 2)]
    P.poly_free(colors["chest"], [P.pt(*q) for q in chest])
    P.poly_free(colors["chest_light"],
                [P.pt(*q) for q in [(-w + 3, shoulder_y + 3 - lift),
                                    (0, shoulder_y + 3 - lift),
                                    (-1, hip_y - 4), (-w + 4, hip_y - 4)]],
                outline=False)
    return lift


# ======================================================================
# COMPOSER: rig -> buffer + outline + lighting + portrait centering
# ======================================================================
def compose(cfg, painter, facing, phase, action, ap, detail=False,
            flash=0, hero_lane=False):
    """Gambar rig ke buffer, beri outline 1px + pass cahaya, return
    (surface, ox, oy) dimana (ox,oy) adalah offset anchor dalam surface."""
    buf = pygame.Surface((cfg.RIG_W, cfg.RIG_H), pygame.SRCALPHA)
    P = Pose(cfg, buf, cfg.RIG_OX, cfg.RIG_OY, facing, phase, action, ap,
             detail)
    painter(P)
    if flash > 0:
        lit = buf.copy()
        lit.fill((255, 246, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
        lit.set_alpha(flash)
        buf.blit(lit, (0, 0))
    if _lighting is not None and not hero_lane:
        try:
            _lighting.apply_to_rig(
                buf, rim_add=(32, 26, 46), shade_mul=160,
                box=cfg.GRAD_BOX if not detail else None)
        except Exception:
            pass
    return buf


def blit_rig(surface, cfg, buf, x, y, detail=False):
    """Blit buffer + outline siluet; di portrait pusatkan pada bbox."""
    ox = int(x) - cfg.RIG_OX
    oy = int(y) - cfg.RIG_OY
    if detail:
        used = buf.get_bounding_rect(min_alpha=1)
        if used.width > 0:
            ox = int(x) - (used.left + used.width // 2)
            oy = int(y) - (used.top + used.height // 2)
    edge = buf.copy()
    edge.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        surface.blit(edge, (ox + dx, oy + dy))
    surface.blit(buf, (ox, oy))


def draw_shadow(surface, x, y, cfg, w=34):
    ellipse(surface, (0, 0, 0, 150), (x - w, y - 6, w * 2, 12))


# ======================================================================
# SKILL FX generik: ground ring + partikel + kilat (charge/burst/afterglow)
# ======================================================================
def skill_phase(timer, duration):
    """(phase_name, t) dimana t 0..1 dalam fase itu.

    charge  = 30% pertama (membangun), burst = 35% tengah (ledakan),
    afterglow = sisa (mereda)."""
    progress = max(0.0, min(1.0, 1.0 - timer / max(1, int(duration))))
    if progress < 0.30:
        return "charge", progress / 0.30
    if progress < 0.65:
        return "burst", (progress - 0.30) / 0.35
    return "afterglow", (progress - 0.65) / 0.35


def draw_skill_fx(surface, x, y, cfg, timer, duration, colors, phase=0.0,
                  radius=52, bolts=5):
    """Ground ring + partikel + kilat dramatis per fase."""
    p = cfg.PALETTE
    name, t = skill_phase(timer, duration)
    gy = y + cfg.GROUND_DY
    c_ring = colors.get("ring", p.get("magic_mid", (130, 55, 200)))
    c_hot = colors.get("hot", p.get("magic_hot", (220, 160, 255)))
    c_shine = colors.get("shine", p.get("magic_shine", (245, 210, 255)))

    if name == "charge":
        # ring mengecil masuk + partikel naik
        r = int(radius * (1.0 - 0.5 * t))
        a = alpha(140 + 90 * t)
        ellipse(surface, (*c_ring, a), (x - r, gy - r // 3, r * 2, r * 2 // 3), 2)
        for i in range(6):
            tt = (phase * 0.6 + i * 0.16) % 1.0
            px = x + int(math.sin(i * 2.1 + phase) * r * 0.8)
            py = gy - int(tt * 26 * t)
            aacircle(surface, (*c_hot, alpha(160 * (1 - tt))), (px, py), 2)
    elif name == "burst":
        # ring membesar cepat + kilat dramatis + partikel menyebar
        r = int(radius * (0.5 + 0.9 * t))
        a = alpha(230 * (1 - t * 0.5))
        ellipse(surface, (*c_hot, a), (x - r, gy - r // 3, r * 2, r * 2 // 3), 3)
        ellipse(surface, (*c_shine, alpha(180 * (1 - t))),
                (x - r // 2, gy - r // 6, r, r // 3), 2)
        for i in range(bolts):
            ang = (i / float(bolts)) * math.tau + phase * 0.3
            bx = x + int(math.cos(ang) * r * 0.9)
            by = gy + int(math.sin(ang) * r * 0.25)
            tx = x + int(math.cos(ang) * r * 1.5)
            ty = gy - int(30 + 20 * abs(math.sin(ang * 3 + phase)))
            _lightning(surface, (bx, by), (tx, ty), c_shine, c_hot,
                       alpha(200 * (1 - t)))
        for i in range(10):
            tt = (t + i * 0.1) % 1.0
            ang = i * 0.7 + phase
            px = x + int(math.cos(ang) * r * (0.6 + tt))
            py = gy - int(tt * 30)
            aacircle(surface, (*c_hot, alpha(180 * (1 - tt))), (px, py), 2)
    else:  # afterglow
        r = int(radius * (1.4 - 0.6 * t))
        a = alpha(120 * (1 - t))
        ellipse(surface, (*c_ring, a), (x - r, gy - r // 3, r * 2, r * 2 // 3), 1)
        for i in range(5):
            tt = (phase * 0.4 + i * 0.2) % 1.0
            px = x + int(math.sin(i * 1.7 + phase) * r * 0.6)
            py = gy - int(tt * 18)
            aacircle(surface, (*c_shine, alpha(90 * (1 - tt) * (1 - t))),
                     (px, py), 1)


def _lightning(surface, a, b, c1, c2, a_alpha):
    """Kilat zig-zag dramatis dari a ke b."""
    segs = 4
    pts = [a]
    for i in range(1, segs):
        t = i / float(segs)
        mx = a[0] + (b[0] - a[0]) * t
        my = a[1] + (b[1] - a[1]) * t
        off = int(math.sin(i * 7.3) * 6)
        pts.append((int(mx + off), int(my - abs(off))))
    pts.append(b)
    for i in range(len(pts) - 1):
        aaline(surface, (*c2, a_alpha), pts[i], pts[i + 1], 2)
        aaline(surface, (*c1, a_alpha), pts[i], pts[i + 1], 1)
