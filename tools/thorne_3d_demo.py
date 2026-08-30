#!/usr/bin/env python3
"""
Thorne 3D — demo software-rendered 3D low-poly untuk pygame (tanpa OpenGL).

Semua 3D dirasterisasi manual:
  - model bone-rig (kotak + kerucut) sebagai pohon node ber-sendi
  - transformasi 3x3 + Rodrigues rotation per sendi
  - kamera look-at + perspektif sederhana
  - backface culling + painter's algorithm
  - flat shading dengan 1 lampu directional
  - pygame.draw.polygon untuk fill

Render di resolusi internal kecil lalu di-upscale NEAREST -> tetap terasa
seperti pixel art (bukan 3D halus ala engine). 100% prosedural, tanpa aset,
tanpa dependensi baru (hanya pygame + math).

Hanya butuh: Python 3.9+ dan pygame  (pip install pygame).

Jalankan (dari folder root repo mystic-arena):
  python tools/thorne_3d_demo.py           # sheet PNG -> tools/_out/
  python tools/thorne_3d_demo.py --live    # jendela pygame interaktif
    kunci: 1=idle  2=walk  3=attack  ESC=keluar
"""
import math
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame
from heroes._bundle import _NS_thorne as T

P = T.PALETTE  # pakai palet resmi Thorne agar konsisten dengan versi 2D


# ═══════════════════════════════════════════════════════════════════
# MATH 3D minimal (list flat, tanpa numpy)
# ═══════════════════════════════════════════════════════════════════
def vadd(a, b): return (a[0]+b[0], a[1]+b[1], a[2]+b[2])
def vsub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def vmul(a, s): return (a[0]*s, a[1]*s, a[2]*s)
def vdot(a, b): return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]
def vcross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])

def vnorm(a):
    d = math.sqrt(vdot(a, a)) or 1.0
    return (a[0]/d, a[1]/d, a[2]/d)


def rot_matrix(axis, ang):
    """Matriks rotasi 3x3 (row-major, 9 elem) sumbu sembarang (Rodrigues)."""
    if abs(ang) < 1e-6:
        return (1, 0, 0, 0, 1, 0, 0, 0, 1)
    ax = vnorm(axis)
    c, s = math.cos(ang), math.sin(ang)
    C = 1.0 - c
    kx, ky, kz = ax
    return (
        c + kx*kx*C,        kx*ky*C - kz*s,  kx*kz*C + ky*s,
        ky*kx*C + kz*s,     c + ky*ky*C,     ky*kz*C - kx*s,
        kz*kx*C - ky*s,     kz*ky*C + kx*s,  c + kz*kz*C,
    )


IDENT3 = (1, 0, 0, 0, 1, 0, 0, 0, 1)


def m3mul(a, b):
    return (
        a[0]*b[0]+a[1]*b[3]+a[2]*b[6], a[0]*b[1]+a[1]*b[4]+a[2]*b[7], a[0]*b[2]+a[1]*b[5]+a[2]*b[8],
        a[3]*b[0]+a[4]*b[3]+a[5]*b[6], a[3]*b[1]+a[4]*b[4]+a[5]*b[7], a[3]*b[2]+a[4]*b[5]+a[5]*b[8],
        a[6]*b[0]+a[7]*b[3]+a[8]*b[6], a[6]*b[1]+a[7]*b[4]+a[8]*b[7], a[6]*b[2]+a[7]*b[5]+a[8]*b[8],
    )


def m3v(m, v):
    return (
        m[0]*v[0]+m[1]*v[1]+m[2]*v[2],
        m[3]*v[0]+m[4]*v[1]+m[5]*v[2],
        m[6]*v[0]+m[7]*v[1]+m[8]*v[2],
    )


# ═══════════════════════════════════════════════════════════════════
# MODEL: node = sendi (pivot + rotasi sumbu) + wajah-wajah lokal
# ═══════════════════════════════════════════════════════════════════
class Node:
    __slots__ = ("pivot", "axis", "ang", "verts", "faces", "children", "name")

    def __init__(self, pivot=(0, 0, 0), axis=(0, 1, 0), ang=0.0, name=""):
        self.pivot = pivot
        self.axis = axis
        self.ang = ang
        self.verts = []
        self.faces = []   # (color, [idx...], normal_local)
        self.children = []
        self.name = name

    def add_verts(self, vs):
        start = len(self.verts)
        self.verts.extend(vs)
        return start

    def add_face(self, color, idxs, center):
        p0, p1, p2 = self.verts[idxs[0]], self.verts[idxs[1]], self.verts[idxs[2]]
        n = vcross(vsub(p1, p0), vsub(p2, p0))
        if vdot(n, vsub(center, p0)) < 0:
            idxs = idxs[::-1]
        self.faces.append((color, list(idxs), n))


def box(node, cx, cy, cz, sx, sy, sz, color):
    """Kotak berpusat (cx,cy,cz), ukuran (sx,sy,sz)."""
    x0, x1 = cx - sx/2, cx + sx/2
    y0, y1 = cy - sy/2, cy + sy/2
    z0, z1 = cz - sz/2, cz + sz/2
    s = node.add_verts([
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
    ])
    for f in ((0, 1, 2, 3), (5, 4, 7, 6), (4, 0, 3, 7),
              (1, 5, 6, 2), (3, 2, 6, 7), (4, 5, 1, 0)):
        node.add_face(color, [s + i for i in f], (cx, cy, cz))


def cone(node, pivot, direction, length, radius, color, sides=4):
    """Kerucut (piramida) dari pivot menuju direction, sisi N.
    Dipakai untuk quill, telinga, duri gada, taring."""
    d = vnorm(direction)
    ref = (0, 1, 0) if abs(d[0]) < 0.9 else (1, 0, 0)
    u = vnorm(vcross(d, ref))
    w = vcross(d, u)
    base = []
    pivot_i = node.add_verts([(0.0, 0.0, 0.0)])  # pivot (dipakai semua sisi)
    for i in range(sides):
        a = i * math.tau / sides
        p = vadd(vadd(vmul(u, radius * math.cos(a)),
                      vmul(w, radius * math.sin(a))), pivot)
        base.append(node.add_verts([p]))
    tip = node.add_verts([vadd(pivot, vmul(d, length))])
    mid = vadd(pivot, vmul(d, length * 0.5))
    for i in range(sides):
        node.add_face(color, [tip, pivot_i, base[i], base[(i+1) % sides]], mid)


def cone2(node, pivot, direction, length, radius,
          c_root, c_tip, sides=4):
    """Kerucut 2 segmen (pangkal gelap, ujung terang) — quill ber-pita
    ala Thorne 2D."""
    d = vnorm(direction)
    mid_len = length * 0.6
    cone(node, pivot, d, mid_len, radius, c_root, sides)
    cone(node, vadd(pivot, vmul(d, mid_len * 0.82)), d, length - mid_len * 0.75,
         radius * 0.72, c_tip, sides)


# ═══════════════════════════════════════════════════════════════════
# BANGUN MODEL THORNE (koordinat lokal: Y atas, karakter menghadap +Z)
# ═══════════════════════════════════════════════════════════════════
ROOT_Y = 0.0  # origin di tanah
QUILL_NODES = []
LEG_L, LEG_R = None, None
SHIN_L, SHIN_R = None, None
ARM_L, ARM_R = None, None
ELBOW_L, ELBOW_R = None, None
MACE = None
HEAD = None
EAR_L, EAR_R = None, None


def build_model():
    global QUILL_NODES, LEG_L, LEG_R, SHIN_L, SHIN_R
    global ARM_L, ARM_R, ELBOW_L, ELBOW_R, MACE, HEAD, EAR_L, EAR_R

    root = Node(name="root")

    # ── Badan: panggul + torso gempal ──
    box(root, 0, 0.92, 0, 0.60, 0.34, 0.42, P["fur_dark"])      # panggul
    box(root, 0, 1.34, 0, 0.74, 0.78, 0.52, P["fur_mid"])       # torso
    box(root, 0, 1.22, 0.27, 0.48, 0.44, 0.08, P["belly_mid"])  # perut
    box(root, 0, 1.56, 0.28, 0.44, 0.30, 0.08, P["fur_light"])  # dada
    # strap X (2 pita tipis berputar, menempel di dada)
    for sgn in (1, -1):
        st = Node(pivot=(0, 1.42, 0.26), axis=(0, 1, 0), ang=0.55 * sgn,
                  name="strap")
        box(st, 0, 0, 0, 0.11, 0.11, 0.72, P["cloth_light"])
        box(st, 0, 0.02, 0, 0.06, 0.06, 0.66, P["cloth_mid"])
        root.children.append(st)
    # sabuk + gesper
    box(root, 0, 0.86, 0, 0.66, 0.12, 0.46, P["leather_dark"])
    box(root, 0, 0.86, 0.24, 0.14, 0.12, 0.06, P["gold_mid"])
    # leher
    box(root, 0, 1.80, 0.04, 0.30, 0.18, 0.30, P["fur_dark"])

    # ── Kepala (koordinat RELATIF pivot leher (0,1.88,0.05)) ──
    HEAD = Node(pivot=(0, 1.88, 0.05), axis=(1, 0, 0), name="head")
    box(HEAD, 0, 0.18, 0.04, 0.56, 0.46, 0.52, P["fur_mid"])     # tengkorak
    box(HEAD, 0, 0.08, 0.40, 0.34, 0.26, 0.30, P["snout_mid"])   # moncong
    box(HEAD, 0, 0.08, 0.55, 0.22, 0.18, 0.10, P["snout_dark"])  # ujung hidung
    box(HEAD, 0, 0.34, 0.18, 0.30, 0.10, 0.14, P["fur_light"])   # bulu dahi
    # mata: sklera + iris, lebih rapat agar tidak "goblok"
    for sgn in (1, -1):
        box(HEAD, 0.16 * sgn, 0.28, 0.28, 0.13, 0.13, 0.07, P["eye_white"])
        box(HEAD, 0.16 * sgn, 0.28, 0.31, 0.09, 0.09, 0.06, P["eye_iris"])
        box(HEAD, 0.16 * sgn, 0.36, 0.26, 0.15, 0.05, 0.06, P["fur_darkest"])  # alis marah
    box(HEAD, 0, -0.12, 0.05, 0.34, 0.10, 0.30, P["fur_dark"])   # rahang
    # taring: kerucut tipis melengkung ke depan-atas
    for sgn in (1, -1):
        tk = Node(pivot=(0.13 * sgn, 0.02, 0.30), axis=(1, 0, 0),
                  ang=0.55, name="tusk")
        cone(tk, (0, 0, 0), (0, 0.55, 0.84), 0.40, 0.06,
             P["tusk_mid"], sides=4)
        HEAD.children.append(tk)
    # telinga
    EAR_L = Node(pivot=(-0.20, 0.36, -0.02), axis=(0, 1, 0), ang=-0.25)
    cone(EAR_L, (0, 0, 0), (0, 0.9, -0.35), 0.19, 0.08, P["fur_darkest"], 4)
    EAR_R = Node(pivot=(0.20, 0.36, -0.02), axis=(0, 1, 0), ang=0.25)
    cone(EAR_R, (0, 0, 0), (0, 0.9, -0.35), 0.19, 0.08, P["fur_darkest"], 4)
    HEAD.children.append(EAR_L)
    HEAD.children.append(EAR_R)
    # quill mane: kipas CREST 13 kerucut — menyapu dari ATAS (tengah) ke
    # LUAR-BELAKANG (sisi) seperti kipas merak di belakang kepala
    QUILL_NODES = []
    for i in range(13):
        side = (i - 6) / 6.0            # -1..1
        spread = abs(side)
        d = vnorm((side * (0.15 + spread * 0.95),
                   0.95 - spread * 0.55,
                   -(0.15 + spread * 0.55)))
        ln = 0.85 - spread * 0.18
        base = (side * 0.15, 0.30, -0.10)
        q = Node(pivot=base, axis=(1, 0, 0), ang=0.0, name=f"quill{i}")
        if abs(i - 6) <= 1:
            cone2(q, (0, 0, 0), d, ln, 0.11, P["quill_root"], P["quill_light"])
        elif abs(i - 6) <= 3:
            cone2(q, (0, 0, 0), d, ln * 0.9, 0.095, P["quill_dark"],
                  P["quill_mid"])
        else:
            cone(q, (0, 0, 0), d, ln * 0.8, 0.075, P["quill_dark"], 4)
        QUILL_NODES.append(q)
        HEAD.children.append(q)
    # baris quill kedua di leher (lebih gelap, mengisi siluet bawahan)
    for i in range(9):
        side = (i - 4) / 4.0
        spread = abs(side)
        d = vnorm((side * (0.25 + spread * 0.75),
                   0.5 - spread * 0.2,
                   -(0.5 + spread * 0.4)))
        ln = 0.52 - spread * 0.1
        q = Node(pivot=(side * 0.12, -0.10, -0.16),
                 axis=(1, 0, 0), ang=0.0, name=f"quillN{i}")
        col = P["quill_dark"] if i in (3, 4, 5) else P["quill_darkest"]
        cone(q, (0, 0, 0), d, ln, 0.08, col, 4)
        QUILL_NODES.append(q)
        HEAD.children.append(q)
    root.children.append(HEAD)

    # ── Lengan ──
    def make_arm(side, has_mace):
        sh = Node(pivot=(0.40 * side, 1.60, 0.02), axis=(1, 0, 0),
                  name=f"arm{'R' if side > 0 else 'L'}")
        box(sh, 0, -0.02, 0, 0.22, 0.18, 0.22, P["armor_mid"])  # pauldron
        box(sh, 0, -0.16, 0, 0.13, 0.32, 0.13, P["fur_dark"])   # paha lengan
        box(sh, 0, -0.10, 0, 0.12, 0.14, 0.12, P["fur_light"])
        el = Node(pivot=(0, -0.30, 0), axis=(1, 0, 0), name="elbow")
        box(el, 0, -0.14, 0, 0.11, 0.28, 0.11, P["fur_mid"])    # lengan bawah
        box(el, 0, -0.05, 0, 0.13, 0.10, 0.13, P["armor_dark"]) # bracer
        fist = Node(pivot=(0, -0.30, 0), axis=(1, 0, 0), name="fist")
        box(fist, 0, -0.07, 0, 0.16, 0.14, 0.16, P["fur_darkest"])
        if has_mace:
            m = Node(pivot=(0, -0.08, 0), axis=(1, 0, 0), name="mace")
            box(m, 0, -0.28, 0, 0.07, 0.52, 0.07, P["wood_mid"])   # gagang
            box(m, 0, -0.10, 0, 0.09, 0.12, 0.09, P["leather_dark"])
            box(m, 0, -0.62, 0, 0.34, 0.28, 0.34, P["armor_dark"])  # kepala gada
            box(m, 0, -0.62, 0, 0.38, 0.11, 0.38, P["armor_mid"])
            box(m, 0, -0.50, 0, 0.24, 0.07, 0.24, P["gold_mid"])    # cincin atas
            box(m, 0, -0.74, 0, 0.24, 0.07, 0.24, P["gold_mid"])    # cincin bawah
            # 6 duri gada + ujung berkilau (ref 2D: rim dingin)
            for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0),
                      (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                c = Node(pivot=(0, -0.62, 0), axis=(1, 0, 0), name="spike")
                cone(c, (0, 0, 0), d, 0.18, 0.055, P["armor_mid"], 3)
                cone(c, (0, 0, 0), d, 0.225, 0.03, P["armor_shine"], 3)
                m.children.append(c)
            # ujung duri depan beracun menyala (ref 2D)
            box(m, 0, -0.62, 0.215, 0.05, 0.05, 0.05, P["goo_bright"])
            box(m, 0, -0.62, 0.24, 0.03, 0.03, 0.03, P["quill_shine"])
            fist.children.append(m)
        el.children.append(fist)
        sh.children.append(el)
        return sh, el, fist

    ARM_L, ELBOW_L, _ = make_arm(-1, False)
    ARM_R, ELBOW_R, fist_r = make_arm(1, True)
    MACE = fist_r.children[0] if fist_r.children else None
    root.children.append(ARM_L)
    root.children.append(ARM_R)

    # ── Kaki ──
    def make_leg(side):
        hip = Node(pivot=(0.18 * side, 0.95, 0), axis=(1, 0, 0),
                   name=f"leg{'R' if side > 0 else 'L'}")
        box(hip, 0, -0.15, 0, 0.17, 0.32, 0.19, P["fur_dark"])
        box(hip, 0, -0.06, 0, 0.12, 0.12, 0.12, P["fur_light"])
        kn = Node(pivot=(0, -0.30, 0), axis=(1, 0, 0), name="knee")
        box(kn, 0, -0.13, 0, 0.14, 0.26, 0.15, P["fur_mid"])
        ank = Node(pivot=(0, -0.28, 0), name="ankle")
        box(ank, 0, -0.05, 0.06, 0.17, 0.11, 0.30, P["fur_darkest"])  # kaki
        box(ank, 0, -0.01, 0.06, 0.13, 0.06, 0.24, P["fur_mid"])      # punggung kaki
        box(ank, 0, -0.02, 0.17, 0.13, 0.05, 0.14, P["tusk_mid"])     # cakar
        kn.children.append(ank)
        hip.children.append(kn)
        return hip, kn

    LEG_L, SHIN_L = make_leg(-1)
    LEG_R, SHIN_R = make_leg(1)
    root.children.append(LEG_L)
    root.children.append(LEG_R)

    return root


# ═══════════════════════════════════════════════════════════════════
# ANIMASI: isi sudut sendi sesuai pose
# ═══════════════════════════════════════════════════════════════════
def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def pose_idle(t):
    # Sinkron 2D: bob sin(t*0.72) + sway samping sin(t*0.8) + quill
    # gelombang sin(t*1.25) — frekuensi sama persis dengan rig 2D.
    bob = 0.05 * math.sin(t * 0.72)
    sway = 0.05 * math.sin(t * 0.8)
    head_ang = 0.07 * math.sin(t * 0.8 + 0.7)
    armL = 0.10 * math.sin(t * 0.65)
    armR = 0.10 * math.sin(t * 0.65 + math.pi * 0.6)
    elbL = 0.25 + 0.08 * math.sin(t * 0.65 + 1.0)
    elbR = 0.25 + 0.08 * math.sin(t * 0.65 + 2.0)
    quill = [0.06 * math.sin(t * 1.25 + i * 0.5) for i in range(22)]
    return dict(root_bob=bob, sway=sway, head_ang=head_ang,
                armL=armL, armR=armR, elbL=elbL, elbR=elbR,
                legL=0.0, legR=0.0, shinL=0.06, shinR=0.06,
                quill=quill, mace=0.06 * math.sin(t), yaw=0.0,
                pitch=0.0, bob_extra=0.0)


def pose_walk(phase):
    # Sinkron 2D: fase = pulse*2 (di-sheet sudah), bob turun saat telapak
    # menapak (|sin|), lean depan, lutut fleksi saat kaki terangkat.
    l = 0.62 * math.sin(phase)
    r = 0.62 * math.sin(phase + math.pi)
    shinL = 0.80 * max(0.0, math.sin(phase + 2.4))
    shinR = 0.80 * max(0.0, math.sin(phase + 2.4 + math.pi))
    bob = -0.07 * abs(math.sin(phase * 1.2))
    return dict(root_bob=bob, sway=0.04 * math.sin(phase),
                head_ang=0.05 * math.sin(phase * 2),
                armL=0.30 * math.sin(phase + math.pi),
                armR=0.18 * math.sin(phase + math.pi),
                elbL=0.35 + 0.15 * math.sin(phase),
                elbR=0.50 + 0.15 * math.sin(phase),
                legL=l, legR=r, shinL=shinL, shinR=shinR,
                quill=[0.08 * math.sin(phase * 2 + i * 0.4) for i in range(22)],
                mace=0.12 * math.sin(phase), yaw=0.0,
                pitch=0.07, bob_extra=0.0)


def pose_attack(ap):
    # Sinkron 2D: windup (gada ke BELAKANG kepala) -> smash (ayun ke
    # DEPAN-bawah, langkah maju + badan condong depan) -> recover.
    # Sumbu X: sudut positif = lengan bergerak ke belakang, negatif =
    # ke depan (karakter menghadap +Z).
    if ap < 0.30:
        sh = 2.7 * smooth(ap / 0.30)
    elif ap < 0.62:
        sh = 2.7 - 3.7 * smooth((ap - 0.30) / 0.32)
    else:
        sh = -1.0 * (1.0 - smooth((ap - 0.62) / 0.38))
    elb = 0.35 + 1.1 * math.sin(ap * math.pi)
    lean = 0.30 * math.sin(ap * math.pi)
    lunge = 0.16 * math.sin(ap * math.pi)          # langkah maju
    flare = 0.20 * math.sin(ap * math.pi)          # quill menegak saat smash
    return dict(root_bob=0.0,
                sway=0.0,
                head_ang=0.12 * math.sin(ap * math.pi),
                armL=-0.5 * math.sin(ap * math.pi),
                armR=sh,
                elbL=0.3, elbR=elb,
                legL=-0.45 * math.sin(ap * math.pi),
                legR=0.55 * math.sin(ap * math.pi),
                shinL=0.25, shinR=0.6 * math.sin(ap * math.pi),
                quill=[flare * math.sin(0.6 + i * 0.9) for i in range(22)],
                mace=0.35 * math.sin(ap * math.pi - 0.6),
                yaw=0.0, pitch=lean,
                lunge=lunge,
                bob_extra=-0.10 * math.sin(ap * math.pi))


def root_transform(pose, yaw_extra=0.0):
    """Transformasi root MURNI (tanpa menyentuh node) — dipakai efek 3D
    untuk menghitung posisi dunia gada/kaki di sampel pose masa lalu."""
    M = rot_matrix((1, 0, 0), pose["pitch"])
    t = (pose.get("sway", 0.0),
         pose["root_bob"] + pose.get("bob_extra", 0.0),
         pose.get("lunge", 0.0))
    My = rot_matrix((0, 1, 0), yaw_extra + pose["yaw"])
    return m3mul(My, M), t


def apply_pose(pose, yaw_extra=0.0):
    """Tulis pose ke node-node model."""
    HEAD.ang = pose["head_ang"]
    ARM_L.ang = pose["armL"]
    ARM_R.ang = pose["armR"]
    ELBOW_L.ang = pose["elbL"]
    ELBOW_R.ang = pose["elbR"]
    LEG_L.ang = pose["legL"]
    LEG_R.ang = pose["legR"]
    SHIN_L.ang = pose["shinL"]
    SHIN_R.ang = pose["shinR"]
    if MACE is not None:
        MACE.ang = pose["mace"]
    for i, q in enumerate(QUILL_NODES):
        q.ang = pose["quill"][i] if i < len(pose["quill"]) else 0.0
    _, t = root_transform(pose, yaw_extra)
    return (yaw_extra + pose["yaw"], pose["pitch"], t[1], t[0], t[2])


def mace_world_from(pose, yaw_extra=0.0):
    """Posisi dunia pusat kepala gada untuk pose tertentu (murni).
    Chain harus persis sama dengan renderer: pivot anak di-transform
    oleh MASI induk (sebelum rotasi anak)."""
    M, t = root_transform(pose, yaw_extra)
    piv = (0.40, 1.60, 0.02)
    Ma = m3mul(M, rot_matrix((1, 0, 0), pose["armR"]))
    ta = vadd(m3v(M, piv), t)
    Me = m3mul(Ma, rot_matrix((1, 0, 0), pose["elbR"]))
    te = vadd(m3v(Ma, (0, -0.30, 0)), ta)
    Mf = Me                                          # fist tidak dirotasi
    tf = vadd(m3v(Me, (0, -0.30, 0)), te)
    Mm = m3mul(Mf, rot_matrix((1, 0, 0), pose["mace"]))
    tm = vadd(m3v(Mf, (0, -0.08, 0)), tf)
    return vadd(m3v(Mm, (0, -0.62, 0)), tm)


def foot_world_from(pose, side, yaw_extra=0.0):
    """Posisi dunia telapak kaki (untuk efek debu langkah)."""
    M, t = root_transform(pose, yaw_extra)
    ang = pose["legL"] if side < 0 else pose["legR"]
    shin = pose["shinL"] if side < 0 else pose["shinR"]
    piv = (0.18 * side, 0.95, 0)
    Mh = m3mul(M, rot_matrix((1, 0, 0), ang))
    th = vadd(m3v(M, piv), t)
    Mk = m3mul(Mh, rot_matrix((1, 0, 0), shin))
    tk = vadd(m3v(Mh, (0, -0.30, 0)), th)      # pivot lutut: M ASI induk
    # telapak: pivot ankle (0,-0.28,0) + pusat kaki (0,-0.05,0.06);
    # ankle tidak dirotasi -> titik (0,-0.33,0.06) relatif lutut
    return vadd(m3v(Mk, (0, -0.33, 0.06)), tk)


# ═══════════════════════════════════════════════════════════════════
# RENDERER: transformasi, culling, shading, painter
# ═══════════════════════════════════════════════════════════════════
LIGHT = vnorm((-0.38, 0.78, 0.55))
FILL = vnorm((0.55, 0.25, -0.40))  # fill lemah dari sisi gelap


class Renderer:
    def __init__(self, size, focal, target=(0, 1.15, 0), dist=5.4, elev=0.34,
                 azim=0.0):
        self.w, self.h = size
        self.focal = focal
        self.cx, self.cy = self.w / 2.0, size[1] * 0.55
        self.eye = (
            target[0] + dist * math.cos(elev) * math.sin(azim),
            target[1] + dist * math.sin(elev),
            target[2] + dist * math.cos(elev) * math.cos(azim),
        )
        f = vnorm(vsub(target, self.eye))
        s = vnorm(vcross(f, (0, 1, 0)))
        u = vcross(s, f)
        self.f, self.s, self.u = f, s, u

    def project(self, p):
        """Titik dunia -> layar, atau None kalau di belakang kamera."""
        d = vsub(p, self.eye)
        z = vdot(self.f, d)
        if z < 0.15:
            return None
        return (self.cx + self.focal * vdot(self.s, d) / z,
                self.cy - self.focal * vdot(self.u, d) / z)

    def render(self, surf, root, yaw, pitch, bob, dx=0.0, dz=0.0):
        w, h = self.w, self.h
        f, s, u, eye = self.f, self.s, self.u, self.eye

        # root matrix: offset (sway/lunge) + bob + pitch (X) + yaw (Y)
        M = rot_matrix((1, 0, 0), pitch)
        t = (dx, bob, dz)
        My = rot_matrix((0, 1, 0), yaw)
        M = m3mul(My, M)

        # flatten pohon (bawa parent bersamaan supaya O(N))
        draws = []
        stack = [(root, None, M, t)]
        while stack:
            n, par, Mn, tn = stack.pop()
            for c in n.children:
                Cm = m3mul(Mn, rot_matrix(c.axis, c.ang))
                Ct = vadd(m3v(Mn, c.pivot), tn)
                stack.append((c, n, Cm, Ct))
            for color, idxs, nlocal in n.faces:
                wp = [vadd(m3v(Mn, n.verts[i]), tn) for i in idxs]
                # normal dunia (M murni rotasi)
                nw = m3v(Mn, nlocal)
                fc = vadd(wp[0], vmul(vsub(wp[1], wp[0]), 0.5))
                # backface cull
                if vdot(nw, vsub(eye, fc)) <= 0.0:
                    continue
                # kamera
                cams = []
                ok = True
                for p in wp:
                    d = vsub(p, eye)
                    z = vdot(f, d)
                    if z < 0.15:
                        ok = False
                        break
                    cams.append((vdot(s, d), vdot(u, d), z))
                if not ok:
                    continue
                zmax = max(c[2] for c in cams)
                # flat shading: key light + fill lemah (sisi gelap tidak mati)
                br = (0.50
                      + 0.72 * max(0.0, vdot(nw, LIGHT))
                      + 0.18 * max(0.0, vdot(nw, FILL)))
                col = (
                    min(255, int(color[0] * br)),
                    min(255, int(color[1] * br)),
                    min(255, int(color[2] * br)),
                )
                pts = [
                    (int(self.cx + self.focal * c[0] / c[2]),
                     int(self.cy - self.focal * c[1] / c[2]))
                    for c in cams
                ]
                draws.append((zmax, col, pts))

        # painter: jauh dulu
        draws.sort(key=lambda d: d[0], reverse=True)
        for _, col, pts in draws:
            pygame.draw.polygon(surf, col, pts)
            pygame.draw.polygon(surf, col, pts, 1)  # tutup celah AA antar-wajah
        return len(draws)


def _outline(canvas, width=1):
    """Outline siluet gelap 1 px di sekeliling model — teknik yang sama
    dengan _finish_hd_sprite di game (pygame.mask dilasi). Menjadikan
    render 3D tetap terasa pixel-art, bukan gambar halus."""
    w, h = canvas.get_size()
    solid = pygame.mask.from_surface(canvas, 150)
    if solid.count() == 0:
        return canvas, 0
    ew, eh = w + 2 * width, h + 2 * width
    expanded = pygame.mask.Mask((ew, eh))
    for ox in range(width + 1):
        for oy in range(width + 1):
            if ox == width and oy == width:
                continue
            expanded.draw(solid, (ox, oy))
    core = pygame.mask.Mask((ew, eh))
    core.draw(solid, (width, width))
    expanded.erase(core, (width, width))
    edge = expanded.to_surface(setcolor=(4, 6, 15, 235),
                               unsetcolor=(0, 0, 0, 0))
    out = pygame.Surface((ew, eh), pygame.SRCALPHA)
    out.blit(edge, (0, 0))
    out.blit(canvas, (width, width))
    return out, width


def _effect_swing_trail(canvas, r, ap, yaw_extra):
    """Crescent trail ayunan gada — efek andalan 2D, kini dihitung dari
    jejak dunia kepala gada di 10 sampel pose sebelumnya."""
    if not (0.26 < ap < 0.78):
        return
    a0 = max(0.0, ap - 0.20)
    pts = []
    n = 10
    for i in range(n + 1):
        s = a0 + (ap - a0) * i / n
        sp = r.project(mace_world_from(pose_attack(s), yaw_extra))
        if sp is not None:
            pts.append((sp, (ap - s) / max(1e-6, ap - a0)))
    if len(pts) < 3:
        return
    tmp = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
    for i in range(len(pts) - 1):
        (x1, y1), age1 = pts[i]
        (x2, y2), age2 = pts[i + 1]
        ddx, ddy = x2 - x1, y2 - y1
        d = math.hypot(ddx, ddy) or 1.0
        px, py = -ddy / d, ddx / d
        w1, w2 = 1.0 + 2.5 * (1 - age1), 1.0 + 2.5 * (1 - age2)
        quad = ((x1 + px * w1, y1 + py * w1), (x2 + px * w2, y2 + py * w2),
                (x2 - px * w2, y2 - py * w2), (x1 - px * w1, y1 - py * w1))
        alpha = int(150 * (1 - (age1 + age2) / 2))
        if alpha <= 12:
            continue
        pygame.draw.polygon(tmp, (*P["quill_light"], alpha),
                            [(int(a), int(b)) for a, b in quad])
    canvas.blit(tmp, (0, 0))


def _effect_sparks(canvas, r, ap, yaw_extra):
    """Impact sparks saat smash (2D: ap ~0.52)."""
    impact = max(0.0, 1.0 - abs(ap - 0.52) / 0.18)
    if impact <= 0:
        return
    sp = r.project(mace_world_from(pose_attack(ap), yaw_extra))
    if sp is None:
        return
    tmp = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
    for i in range(6):
        ang = -1.2 + i * 0.48
        length = 5 + int(impact * (8 + i % 2 * 4))
        pygame.draw.line(
            tmp, (*P["quill_shine"], int(220 * impact)),
            (int(sp[0]), int(sp[1])),
            (int(sp[0] + math.cos(ang) * length),
             int(sp[1] + math.sin(ang) * length)),
            1 if i % 2 else 2)
    canvas.blit(tmp, (0, 0))


def _effect_walk_dust(canvas, r, phase, yaw_extra):
    """Debu di telapak kaki yang menapak — efek walk 2D."""
    pose = pose_walk(phase)
    tmp = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
    for side in (-1, 1):
        fp = foot_world_from(pose, side, yaw_extra)
        if fp[1] >= 0.16:
            continue
        alpha = int(150 * (0.16 - fp[1]) / 0.16)
        for i in range(3):
            bp = r.project((fp[0] - 0.04 * i, 0.04, fp[2] - 0.12 - 0.08 * i))
            if bp is None:
                continue
            pygame.draw.circle(
                tmp, (*P["fur_mid"], max(20, alpha - 40 * i)),
                (int(bp[0]), int(bp[1])), max(1, 3 - i // 2))
    canvas.blit(tmp, (0, 0))


def _effect_idle_motes(canvas, r, t):
    """Partikel bulu melayang saat idle — efek idle 2D."""
    tmp = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
    for i in range(3):
        tt = (t * 0.18 + i / 3.0) % 1.0
        mp = r.project((math.sin(t + i * 2.1) * 0.3, 0.4 - tt * 1.1, 0.15))
        if mp is None:
            continue
        pygame.draw.circle(tmp, (*P["fur_high"], int(110 * (1 - tt))),
                           (int(mp[0]), int(mp[1])), 1)
    canvas.blit(tmp, (0, 0))


def render_frame(w, h, root, action, t, ap=0.0, yaw_extra=0.0, focal=235.0):
    """Render satu frame. action: 'idle' (t=waktu) | 'walk' (t=fase) |
    'attack' (ap=progress 0..1)."""
    if action == "idle":
        pose = pose_idle(t)
    elif action == "walk":
        pose = pose_walk(t)
    else:
        pose = pose_attack(ap)
    yaw, pitch, bob, dx, dz = apply_pose(pose, yaw_extra)
    r = Renderer((w, h), focal)
    canvas = pygame.Surface((w, h), pygame.SRCALPHA)
    # bayangan tanah (geser mengikuti sway; lunge maju -> turun dikit)
    shx = int(dx * (focal / 5.4))
    shy = int(dz * (focal / 5.4) * 0.35)
    pygame.draw.ellipse(canvas, (0, 0, 0, 70),
                        (w // 2 - 42 + shx, int(h * 0.55) + 44 + shy,
                         84, 18))
    pygame.draw.ellipse(canvas, (0, 0, 0, 40),
                        (w // 2 - 30 + shx, int(h * 0.55) + 48 + shy,
                         60, 10))
    # model -> surface sendiri, outline siluet, lalu efek 3D di atasnya
    model = pygame.Surface((w, h), pygame.SRCALPHA)
    nfaces = r.render(model, root, yaw, pitch, bob, dx, dz)
    outlined, pad = _outline(model)
    canvas.blit(outlined, (-pad, -pad))
    if action == "idle":
        _effect_idle_motes(canvas, r, t)
    elif action == "walk":
        _effect_walk_dust(canvas, r, t, yaw_extra)
    else:
        _effect_swing_trail(canvas, r, ap, yaw_extra)
        _effect_sparks(canvas, r, ap, yaw_extra)
    return canvas, nfaces


# ═══════════════════════════════════════════════════════════════════
# SHEET DEMO
# ═══════════════════════════════════════════════════════════════════
def _label(sheet, text, x, y, size=22, color=(235, 235, 235)):
    # Font(None, ...) = font bawaan pygame -> ada di semua OS
    # (ukuran default font lebih kecil, jadi +4 supaya proporsinya sama).
    font = pygame.font.Font(None, size + 4)
    surf = font.render(text, True, color)
    sheet.blit(surf, (x, y))
    return surf.get_size()


def make_sheets(root, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    frame_w, frame_h = 120, 132
    scale = 2
    fw, fh = frame_w * scale, frame_h * scale

    def cell(t, action, yaw_extra=0.0, ap=0.0):
        img, _ = render_frame(frame_w, frame_h, root, action, t, ap,
                              yaw_extra)
        return pygame.transform.scale(img, (fw, fh))

    # ── Sheet 1: SPIN 360 (bukti 3D) ──
    n = 12
    sheet = pygame.Surface((n * fw + 40, fh + 90))
    sheet.fill((14, 18, 26))
    _label(sheet, "THORNE 3D — PUTARAN 360°", 20, 14, 26, (255, 205, 120))
    _label(sheet, "software-rendered low-poly di pygame • tanpa OpenGL • flat shading",
           20, 46, 15, (150, 158, 175))
    t0 = time.perf_counter()
    for i in range(n):
        img = cell(i / n * 4.0, "idle", yaw_extra=i / n * math.tau)
        sheet.blit(img, (20 + i * fw, 70))
    dt_spin = (time.perf_counter() - t0) / n * 1000
    p1 = os.path.join(out_dir, "thorne_3d_spin.png")
    pygame.image.save(sheet, p1)
    print(p1)

    # ── Sheet 2: animasi idle / walk / attack ──
    rows = (("IDLE", 6, "idle"), ("WALK", 8, "walk"), ("ATTACK", 8, "attack"))
    H = 90 + 3 * (fh + 60)
    W = max(8 * fw + 150, 900)
    sheet = pygame.Surface((W, H))
    sheet.fill((14, 18, 26))
    _label(sheet, "THORNE 3D — ANIMASI RIG", 20, 14, 26, (255, 205, 120))
    _label(sheet, "tiap frame dihitung ulang dari sendi (bukan sprite sheet)",
           20, 46, 15, (150, 158, 175))
    t0 = time.perf_counter()
    for row, (label, count, action) in enumerate(rows):
        top = 70 + row * (fh + 60)
        _label(sheet, label, 30, top + fh // 2 - 10, 20, (255, 199, 130))
        for i in range(count):
            if action == "attack":
                img = cell(0.0, action, ap=i / (count - 1))
            else:
                img = cell((i / count) * math.tau, action)
            sheet.blit(img, (150 + i * fw, top))
    dt_anim = (time.perf_counter() - t0) / 22 * 1000
    p2 = os.path.join(out_dir, "thorne_3d_anim.png")
    pygame.image.save(sheet, p2)
    print(p2)

    # ── Sheet 3: close-up hero (1 frame, 4x) + latar + glow ──
    img, _ = render_frame(150, 165, root, "idle", 0.9, 0.0, 0.35)
    big = pygame.transform.scale(img, (img.get_width() * 4,
                                       img.get_height() * 4))
    Wc, Hc = big.get_width(), big.get_height()
    close = pygame.Surface((Wc, Hc))
    close.fill((13, 16, 24))
    # glow radial hangat di belakang (lingkaran alfa menumpuk -> gradient)
    glow = pygame.Surface((Wc, Hc), pygame.SRCALPHA)
    cx, cy = Wc // 2, int(Hc * 0.48)
    maxr = max(Wc, Hc) // 2
    for rr in range(maxr, 0, -6):
        pygame.draw.circle(glow, (255, 176, 88, 5), (cx, cy), rr)
    close.blit(glow, (0, 0))
    close.blit(big, (cx - Wc // 2, int(Hc * 0.52) - Hc // 2))
    p3 = os.path.join(out_dir, "thorne_3d_closeup.png")
    pygame.image.save(close, p3)
    print(p3)
    print(f"render ~{dt_spin:.2f} ms/frame (spin)  ~{dt_anim:.2f} ms/frame (anim)")


# ═══════════════════════════════════════════════════════════════════
# MODE LIVE
# ═══════════════════════════════════════════════════════════════════
def run_live(root):
    try:
        pygame.display.set_mode((720, 520))
    except pygame.error as e:
        print(f"Gagal membuka jendela: {e}")
        print("Pastikan laptop punya display & driver graphics (Windows/Mac) —")
        print("atau jalankan mode sheet:  python tools/thorne_3d_demo.py")
        raise
    pygame.display.set_caption("Thorne 3D — demo (1 idle / 2 walk / 3 attack / ESC keluar)")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 22)
    t = 0.0
    seq = 0  # 0 idle, 1 walk, 2 attack
    ap = 0.0
    frames = 0
    t_fps = time.perf_counter()
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                return
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_1,
                                                        pygame.K_2, pygame.K_3):
                seq = ev.key - pygame.K_1
                ap = 0.0
        dt = clock.tick(60) / 1000.0
        t += dt
        if seq == 2:
            ap += dt / 1.1
            if ap > 1.15:
                ap = 0.0
        scr = pygame.display.get_surface()
        scr.fill((14, 18, 26))
        if seq == 0:
            label = "IDLE  (1 idle / 2 walk / 3 attack / ESC quit)"
            img, nfaces = render_frame(120, 132, root, "idle", t)
        elif seq == 1:
            label = "WALK"
            img, nfaces = render_frame(120, 132, root, "walk", t * 2.4)
        else:
            label = f"ATTACK {ap:.2f}"
            img, nfaces = render_frame(120, 132, root, "attack", t,
                                       min(1.0, ap))
        big = pygame.transform.scale(img, (600, 660))
        scr.blit(big, (60, -60))
        scr.blit(font.render(label, True, (255, 205, 120)), (20, 14))
        scr.blit(font.render(f"{nfaces} faces drawn", True, (150, 158, 175)),
                 (20, 38))
        pygame.display.flip()
        frames += 1
        now = time.perf_counter()
        if now - t_fps >= 1.0:
            print(f"FPS: {frames:.0f}  faces: {nfaces}")
            frames = 0
            t_fps = now


if __name__ == "__main__":
    LIVE = "--live" in sys.argv
    if not LIVE:
        # Sheet: render tanpa jendela (aman di terminal/CI)
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    # --live: biarkan driver asli (jendela sungguhan di laptop)
    pygame.init()
    pygame.display.set_mode((8, 8))
    root = build_model()
    if LIVE:
        run_live(root)
    else:
        out = os.path.join(ROOT, "tools", "_out")
        make_sheets(root, out)
