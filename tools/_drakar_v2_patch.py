#!/usr/bin/env python3
"""Patch script: replace _NS_drakar in bosses/level1.py with v2 masterwork."""
import os, sys

NEW_NAMESPACE = r'''class _NS_drakar:
    """Namespace drakar - PIXEL MASTERWORK v2 + SKILL FX v2.1.

    Rewrite penuh renderer _NS_drakar di bosses/level1.py.
    Tetap 100% prosedural: tidak ada PNG / sprite-sheet / image.load.

    Upgrade dari v1 (ORIGINAL-MAX):
    - RIG ~1.5x lebih besar (240->360) di resolusi native
    - Disiplin pixel-art: ramp 4-5 band hue-shift, selout, siluet bergerigi,
      specular cluster, dither band, key light kiri-atas
    - Anatomi detail: barbarian dengan axe besar, pauldron ber-spike,
      bandolier, rambut liar, janggut ber-lapis
    - Animasi: foot solver, inersia, idle hidup (napas, kedip, dengus),
      serangan 7 keyframe + IMPACT + smear
    - Skill FX world-space via _fx_scale (kompensasi _render_scale, cap 2.6)
    - 3 fase per skill: AKTIVASI, STEADY, TELEGRAPH
    - Primitif FX: _spark_star, _chevron, _dashed_ring, _jagged_crack
    - Body bereaksi ke state skill (crest menyala saat buff)
    - Cache permukaan statis (aura, shadow, mist)
    """

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        "skin_darkest": (55, 15, 15), "skin_dark": (110, 30, 25),
        "skin_mid": (170, 55, 40), "skin_light": (215, 95, 70),
        "skin_shine": (240, 145, 110), "skin_rim": (252, 170, 130),
        "hair_darkest": (8, 6, 10), "hair_dark": (28, 22, 28),
        "hair_mid": (55, 45, 50), "hair_light": (95, 80, 85),
        "leather_darkest": (22, 12, 6), "leather_dark": (55, 32, 18),
        "leather_mid": (95, 62, 38), "leather_light": (140, 100, 65),
        "armor_darkest": (15, 12, 15), "armor_dark": (42, 38, 45),
        "armor_mid": (85, 78, 88), "armor_light": (140, 132, 142),
        "armor_shine": (200, 195, 205),
        "blade_darkest": (18, 15, 22), "blade_dark": (55, 50, 62),
        "blade_mid": (115, 108, 125), "blade_light": (185, 178, 195),
        "blade_shine": (240, 235, 250),
        "blood_darkest": (45, 5, 10), "blood_dark": (110, 15, 20),
        "blood_mid": (185, 25, 35), "blood_light": (235, 55, 60),
        "blood_hot": (255, 100, 90), "blood_shine": (255, 180, 160),
        "rage_darkest": (60, 10, 5), "rage_dark": (140, 30, 15),
        "rage_mid": (220, 55, 30), "rage_light": (255, 110, 60),
        "rage_hot": (255, 180, 120),
        "eye_dark": (80, 30, 10), "eye_mid": (200, 90, 20),
        "eye_light": (255, 180, 60), "eye_glow": (255, 240, 180),
        "rune_dark": (30, 8, 10), "rune_mid": (140, 30, 30),
        "rune_light": (230, 70, 60),
        "gold_dark": (96, 68, 20), "gold_mid": (180, 136, 44),
        "gold_light": (238, 202, 92),
        "ember_dark": (140, 40, 10), "ember_mid": (220, 90, 20),
        "ember_light": (255, 170, 50), "ember_hot": (255, 220, 120),
        "shadow": (0, 0, 0), "shadow_deep": (3, 1, 2),
        "white": (255, 255, 255),
    }

    BODY_W, BODY_H = 360, 360
    BODY_OX, BODY_OY = 180, 186
    _RIG_SCALE = 1.5
    _STATIC_SURFACES = {}
    _DRK_TX = {}
    _DRK_FIN = None
    _DRK_SHADE = None
    _DRK_BUF = None

    def _static(key, builder):
        surf = _NS_drakar._STATIC_SURFACES.get(key)
        if surf is None:
            surf = builder()
            _NS_drakar._STATIC_SURFACES[key] = surf
        return surf

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _rgba(color, alpha):
        r, g, b = color[0], color[1], color[2]
        return (max(0, min(255, int(r))), max(0, min(255, int(g))),
                max(0, min(255, int(b))), max(0, min(255, int(alpha))))

    def _mix(a, b, t):
        t = max(0.0, min(1.0, t))
        return _NS_drakar._clamp(
            (a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t, a[2]+(b[2]-a[2])*t))

    def _hash01(i):
        x = math.sin(i * 127.1 + 311.7) * 43758.5453
        return x - math.floor(x)

    def _aacircle(surface, color, center, radius, width=0):
        if len(color) == 4:
            color = (max(0,min(255,int(color[0]))), max(0,min(255,int(color[1]))),
                     max(0,min(255,int(color[2]))), max(0,min(255,int(color[3]))))
        else:
            color = _NS_drakar._clamp(color)
        if _NS_drakar.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        if len(color) == 4:
            color = (max(0,min(255,int(color[0]))), max(0,min(255,int(color[1]))),
                     max(0,min(255,int(color[2]))), max(0,min(255,int(color[3]))))
        else:
            color = _NS_drakar._clamp(color)
        if _NS_drakar.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_drakar._clamp(color), points)

    def _fx_scale(boss):
        scale = getattr(boss, "_render_scale", None)
        if not scale:
            return 1.0
        return max(1.0, min(2.6, 1.0 / float(scale)))

    def _spark_star(surface, cx, cy, size, color, alpha, spikes=6, rot=0.4, core=None):
        if alpha <= 0 or size <= 0:
            return
        for k in range(spikes):
            ang = rot + k * math.pi * 2 / spikes
            ln = size * (1.0 if k % 2 == 0 else 0.55)
            _NS_drakar._aaline(surface, (*_NS_drakar._clamp(color), alpha),
                               (int(cx), int(cy)),
                               (int(cx+math.cos(ang)*ln), int(cy+math.sin(ang)*ln*.8)),
                               2 if k%2==0 else 1)
        if core:
            _NS_drakar._aacircle(surface, (*core, alpha), (int(cx), int(cy)),
                                 max(1, int(size*.3)))

    def _chevron(surface, cx, cy, ang, size, color, alpha, width=3):
        if alpha <= 0 or size <= 0:
            return
        ca, sa = math.cos(ang), math.sin(ang)
        px, py = -sa, ca
        tipx, tipy = cx+ca*size, cy+sa*size
        for s in (-1, 1):
            _NS_drakar._aaline(
                surface, (*_NS_drakar._clamp(color), alpha),
                (int(cx+px*s*size*.55-ca*size*.5), int(cy+py*s*size*.55-sa*size*.5)),
                (int(tipx), int(tipy)), width)

    def _dashed_ring(surface, cx, cy, radius, color, alpha, phase,
                     segments=10, thick=3, span=0.6, squash=.92):
        if alpha <= 0 or radius <= 1:
            return
        for i in range(segments):
            a0 = phase + i * math.pi * 2 / segments
            a1 = a0 + math.pi * 2 / segments * span
            p0 = (cx+math.cos(a0)*radius, cy+math.sin(a0)*radius*squash)
            p1 = (cx+math.cos(a1)*radius, cy+math.sin(a1)*radius*squash)
            _NS_drakar._aaline(surface, (*_NS_drakar._clamp(color), alpha), p0, p1, thick)

    def _jagged_crack(surface, cx, cy, ang, length, colors, alpha, seed, width=3):
        if alpha <= 0 or length <= 0:
            return
        x, y, a = cx, cy, ang
        pts = [(x, y)]
        for i in range(3):
            a += (_NS_drakar._hash01(seed*7+i*13)-.5)*.8
            seg = length / 3.0
            x += math.cos(a) * seg
            y += math.sin(a) * seg * .55
            pts.append((x, y))
        for i in range(len(pts)-1):
            _NS_drakar._aaline(surface, (*_NS_drakar._clamp(colors[0]), alpha),
                              pts[i], pts[i+1], width+2)
            _NS_drakar._aaline(surface, (*_NS_drakar._clamp(colors[1]), alpha),
                              pts[i], pts[i+1], width)

    def _tuft_points(spine, depth=4.0, min_len=7.0, seed=0):
        out = [spine[0]]
        for i in range(len(spine)-1):
            ax, ay = spine[i]
            bx, by = spine[i+1]
            seg = math.hypot(bx-ax, by-ay)
            n = max(1, int(seg / min_len))
            nx, ny = (by-ay), -(bx-ax)
            ln = math.hypot(nx, ny) or 1.0
            nx, ny = nx/ln, ny/ln
            for j in range(n):
                t = (j+0.5)/n
                px, py = ax+(bx-ax)*t, ay+(by-ay)*t
                d = depth*(0.55+0.45*_NS_drakar._hash01(i*7+j*13+seed))
                if j % 2 == 0:
                    out.append((px+nx*d, py+ny*d))
                else:
                    out.append((px-nx*d*0.45, py-ny*d*0.45))
            out.append((bx, by))
        return out

    def _drk_glow(radius, color, peak=190):
        key = (int(radius), color, int(peak))
        if key not in _NS_drakar._DRK_TX:
            r = int(radius)
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            fmax = peak / 255.0
            for rad in range(r, 0, -1):
                t = 1.0 - rad / float(r)
                f = (t ** 1.8) * fmax
                _NS_drakar._aacircle(s, (int(color[0]*f), int(color[1]*f),
                                         int(color[2]*f), 255), (r, r), rad)
            _NS_drakar._DRK_TX[key] = s
        return _NS_drakar._DRK_TX[key]

    def _drk_outline(buf, flash=0):
        B = _NS_drakar
        if B._DRK_FIN is None:
            B._DRK_FIN = pygame.Surface((B.BODY_W+2, B.BODY_H+2), pygame.SRCALPHA)
            sh = pygame.Surface((B.BODY_W+2, B.BODY_H+2), pygame.SRCALPHA)
            h, w = B.BODY_H+2, B.BODY_W+2
            for yy in range(h):
                v = int(255 - 70*(yy/float(h)))
                pygame.draw.line(sh, (v,v,v,255), (0,yy), (w,yy))
            for xx in range(0, w, 2):
                v = int(255 - 30*(xx/float(w)))
                s2 = pygame.Surface((2, h), pygame.SRCALPHA)
                s2.fill((v,v,v,255))
                sh.blit(s2, (xx, 0), special_flags=pygame.BLEND_RGBA_MULT)
            B._DRK_SHADE = sh
        out = B._DRK_FIN
        out.fill((0,0,0,0))
        pad = 1
        edge = buf.copy()
        edge.fill((0,0,0,255), special_flags=pygame.BLEND_RGBA_MULT)
        light = edge.copy()
        light.fill((255,214,170,0), special_flags=pygame.BLEND_RGB_ADD)
        dark = edge.copy()
        dark.fill((10,5,7,0), special_flags=pygame.BLEND_RGB_ADD)
        out.blit(light, (pad-1, pad-1))
        out.blit(light, (pad, pad-1))
        out.blit(light, (pad-1, pad))
        out.blit(dark, (pad+1, pad))
        out.blit(dark, (pad, pad+1))
        out.blit(dark, (pad+1, pad+1))
        out.blit(buf, (pad, pad))
        out.blit(B._DRK_SHADE, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
        if flash > 0:
            w = int(235 * min(1.0, flash/8.0))
            if w > 0:
                m = pygame.mask.from_surface(buf, 50)
                wht = m.to_surface(setcolor=(w, int(w*0.92), int(w*0.82), 255),
                                   unsetcolor=(0,0,0,0))
                out.blit(wht, (pad, pad), special_flags=pygame.BLEND_RGB_ADD)
        return out

    def _drk_body_surface(mode, facing, phase_q, prog_q, flash=0, **kwargs):
        B = _NS_drakar
        if B._DRK_BUF is None:
            B._DRK_BUF = pygame.Surface((B.BODY_W, B.BODY_H), pygame.SRCALPHA)
        buf = B._DRK_BUF
        buf.fill((0,0,0,0))
        ox, oy = B.BODY_OX, B.BODY_OY
        if mode == "idle":
            bob = int(math.sin(phase_q*0.5)*9)
            B._draw_drk_body(buf, ox, oy+bob, facing, phase_q, "idle", **kwargs)
        elif mode == "walk":
            bob = int(abs(math.sin(phase_q*1.1))*7)
            sway = int(math.sin(phase_q*0.8)*4)
            B._draw_drk_body(buf, ox+sway, oy-bob+3, facing, phase_q, "walk", **kwargs)
        elif mode == "attack":
            B._draw_drk_body(buf, ox, oy, facing, phase_q, "attack", prog_q, **kwargs)
        else:
            spin = prog_q * math.pi * 8
            bob = int(math.sin(prog_q*math.pi)*-7)
            B._draw_drk_body(buf, ox, oy+bob, facing, phase_q, "helix",
                             spin_angle=spin, **kwargs)
        return B._drk_outline(buf, flash)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        return int(x + 220/float(getattr(boss,"_render_scale",1.0) or 1.0)*getattr(boss,"direction",1)), int(y)

    def draw_drakar(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_drakar._detect_moving(boss)
        _NS_drakar._update_drk_attack_anim(boss)
        attacking = (getattr(boss, "_drk_attack_active", False)
                     or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15)
        fs = _NS_drakar._fx_scale(boss)

        _NS_drakar._draw_rage_aura(surface, x, y, pulse)
        _NS_drakar._draw_ground_ring(surface, boss, x, y+114, pulse, active_skill)

        if active_skill == "q":
            _NS_drakar._draw_battlehunger_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_drakar._draw_counterhelix_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_drakar._draw_berserkerscall_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_drakar._draw_cullingblade_ground(surface, boss, x, y, skill_timer, pulse)

        if active_skill in ("q","w","e","r"):
            dur = {"q":90,"w":45,"e":60,"r":60}[active_skill]
            age = dur - skill_timer
            if 0 <= age < 12:
                st = age / 12.0
                a = int(235*(1-st))
                rr = int((16+st*50)*fs)
                gy = y + 114
                pygame.draw.ellipse(surface, (255,80,50,a),
                                    (x-rr, gy-rr//3, rr*2, max(4,rr*2//3)), 2)
                pygame.draw.ellipse(surface, (255,200,150,a),
                                    (x-rr//2, gy-rr//6, rr, max(3,rr//3)), 1)
                _NS_drakar._spark_star(surface, x, gy, int(20*fs),
                                       _NS_drakar.PALETTE["rage_light"],
                                       a, spikes=8, rot=pulse,
                                       core=_NS_drakar.PALETTE["rage_hot"])

        facing = int(getattr(boss, "direction", 1)) or 1
        cd = max(2, int(getattr(boss, "attack_cooldown", 46)))
        t_now = int(getattr(boss, "timer", 0))
        atk_p = max(0.0, min(1.0, (cd-1-t_now)/float(cd-1))) if attacking else 0.0
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        ox, oy = _NS_drakar.BODY_OX, _NS_drakar.BODY_OY

        body_kw = {}
        if active_skill == "q": body_kw["battlehunger"] = True
        if active_skill == "w": body_kw["helix_active"] = True
        if active_skill == "e": body_kw["berserk_call"] = True
        if getattr(boss, "rage_active", False): body_kw["rage_mode"] = True

        def _blit_body(spr):
            img = spr if facing > 0 else pygame.transform.flip(spr, True, False)
            surface.blit(img, (x-ox, y-oy))

        if active_skill == "w":
            p = max(0.0, min(1.0, 1-skill_timer/45.0))
            lift_h = int(math.sin(p*math.pi)*7)
            _NS_drakar._draw_shadow(surface, x, y+120, lift_h)
            _NS_drakar._draw_rage_mist(surface, x, y+90, pulse, intense=True)
            _NS_drakar._draw_drk_helix_fx(surface, boss, x, y, skill_timer, pulse)
            _blit_body(_NS_drakar._drk_body_surface("helix", facing, pulse, p, flash, **body_kw))
        elif attacking:
            if atk_p < 0.15:
                t2 = atk_p / 0.15; lunge = -int(t2*6)*facing; lift = -int(t2*6)
            elif atk_p < 0.40:
                t2 = (atk_p-0.15)/0.25; lunge = -int(6+t2*6)*facing; lift = int(-6+t2*15)
            elif atk_p < 0.55:
                t2 = (atk_p-0.40)/0.15; t_ease = 1-(1-t2)**2
                lunge = int((-12+t_ease*42))*facing; lift = int(9-t_ease*15)
            elif atk_p < 0.70:
                t2 = (atk_p-0.55)/0.15; shake_x = int(math.sin(t2*30)*4*(1-t2))
                lunge = int(30+shake_x)*facing; lift = int(-6-t2*3)
            else:
                t2 = (atk_p-0.70)/0.30; t_ease = 1-(1-t2)**2
                lunge = int(30*(1-t_ease))*facing; lift = int(-9+t_ease*9)
            _NS_drakar._draw_shadow(surface, x+lunge, y+120, lift)
            _NS_drakar._draw_rage_mist(surface, x+lunge, y+90, pulse, intense=True)
            _blit_body(_NS_drakar._drk_body_surface("attack", facing, pulse, atk_p, flash, **body_kw))
            _NS_drakar._draw_axe_slash_trail(surface, boss, x+lunge, y-lift, atk_p)
            if 0.53 <= atk_p <= 0.70:
                _NS_drakar._draw_impact_burst(surface, boss, x+lunge, y-lift, atk_p)
        elif moving:
            phase = pulse * 2.0
            bob = int(abs(math.sin(phase*1.1))*7)
            sway = int(math.sin(phase*0.8)*4)
            _NS_drakar._draw_shadow(surface, x+sway, y+120, bob)
            _NS_drakar._draw_rage_mist(surface, x+sway, y+90, phase, trail=True, facing=facing)
            _blit_body(_NS_drakar._drk_body_surface("walk", facing, phase, 0.0, flash, **body_kw))
        else:
            bob_i = int(math.sin(pulse*0.5)*9)
            _NS_drakar._draw_shadow(surface, x, y+120, max(0, -bob_i))
            _NS_drakar._draw_rage_mist(surface, x, y+90, pulse)
            _blit_body(_NS_drakar._drk_body_surface("idle", facing, pulse, 0.0, flash, **body_kw))

        if getattr(boss, "rage_active", False):
            g = _NS_drakar._drk_glow(69, _NS_drakar.PALETTE["rage_mid"], 70)
            surface.blit(g, (x-69, y-90), special_flags=pygame.BLEND_RGBA_ADD)
            g2 = _NS_drakar._drk_glow(10, _NS_drakar.PALETTE["rage_light"], 110)
            surface.blit(g2, (x+9*facing-10, y-60), special_flags=pygame.BLEND_RGBA_ADD)
        if getattr(boss, "defense_boost", False):
            for i in range(3):
                a = pulse*3+i*2.1
                sx = x-18+int(math.sin(a)*6)
                sy = y-36+int(math.cos(a*1.3)*7)
                _NS_drakar._aacircle(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["armor_shine"],
                                     150+int(70*math.sin(a*2))), (sx, sy), 2)

        if active_skill == "q":
            _NS_drakar._draw_battlehunger_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_drakar._draw_berserkerscall_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_drakar._draw_cullingblade_foreground(surface, boss, x, y, skill_timer, pulse)

    def _update_drk_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_drk_previous_timer", 0))
        active = bool(getattr(boss, "_drk_attack_active", False))
        if timer >= cooldown-1 and previous <= 1:
            boss._drk_attack_active = True; boss._drk_attack_frame = 0
            boss._drk_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._drk_attack_frame = int(getattr(boss, "_drk_attack_frame", 0))+1
        elif timer <= 0:
            boss._drk_attack_active = False; boss._drk_attack_frame = 0; active = False
        boss._drk_previous_timer = timer
        boss._drk_attack_progress = (
            min(1.0, getattr(boss, "_drk_attack_frame", 0)/max(1, cooldown-1))
            if active else 0.0)

    def _detect_moving(boss):
        if not hasattr(boss, "_drk_last_x"):
            boss._drk_last_x = boss.x; boss._drk_last_y = boss.y; return False
        dx = abs(boss.x - boss._drk_last_x); dy = abs(boss.y - boss._drk_last_y)
        boss._drk_last_x = boss.x; boss._drk_last_y = boss.y
        return dx + dy > 0.3

    def _draw_drk_helix_fx(surface, boss, x, y, timer, phase):
        duration = 45
        progress = max(0.0, min(1.0, 1-timer/duration))
        spin = progress * math.pi * 8
        bob = int(math.sin(progress*math.pi)*-7)
        fs = _NS_drakar._fx_scale(boss)
        slash_surf = pygame.Surface((420, 420), pygame.SRCALPHA)
        center = (210, 210)
        radius = int(108 * fs)
        for arm_i in range(2):
            arm_start = spin + arm_i * math.pi
            arc_pts = []
            for i in range(25):
                a = arm_start + math.pi*0.9*i/24
                arc_pts.append((center[0]+int(math.cos(a)*radius),
                                center[1]+int(math.sin(a)*radius*0.7)))
            for r_off, thick, color, a_mult in [
                (6,15,"blood_darkest",0.7),(3,12,"blood_dark",0.85),
                (0,9,"blood_mid",1.0),(-2,6,"blood_light",1.0),(-3,3,"blood_hot",1.0)]:
                for k in range(len(arc_pts)-1):
                    fade = 1-(k/len(arc_pts))
                    av = _NS_drakar._alpha(240*a_mult*fade)
                    if av <= 0: continue
                    pygame.draw.line(slash_surf,
                        _NS_drakar._rgba(_NS_drakar.PALETTE[color], av),
                        arc_pts[k], arc_pts[k+1], thick)
            if arc_pts:
                tip = arc_pts[-1]
                pygame.draw.rect(slash_surf, _NS_drakar._rgba(_NS_drakar.PALETTE["blade_shine"],255), (tip[0],tip[1],4,4))
                pygame.draw.rect(slash_surf, _NS_drakar._rgba(_NS_drakar.PALETTE["white"],255), (tip[0],tip[1],3,3))
        for i in range(28):
            angle = spin*0.5+i*math.pi/14
            r_p = radius+int(math.sin(phase+i)*18)-12
            px = center[0]+int(math.cos(angle)*r_p)
            py = center[1]+int(math.sin(angle)*r_p*0.7)
            alpha = _NS_drakar._alpha(220)
            pygame.draw.rect(slash_surf, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"],alpha), (px,py,4,4))
            pygame.draw.rect(slash_surf, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_hot"],alpha), (px,py,3,3))
        surface.blit(slash_surf, (x-210, y-210+bob))

    def _draw_drk_body(surface, cx, cy, facing, phase, action, attack_progress=0,
                       spin_angle=0, **kwargs):
        rage_mode = kwargs.get("rage_mode", False)
        _NS_drakar._draw_drk_legs(surface, cx, cy+42, facing, phase, action)
        _NS_drakar._draw_drk_waist(surface, cx, cy+21, facing, phase)
        _NS_drakar._draw_drk_torso(surface, cx, cy-9, facing, phase, action, rage_mode=rage_mode)
        _NS_drakar._draw_drk_head(surface, cx, cy-45, facing, phase, action)
        grip_data = _NS_drakar._compute_two_handed_grip(cx, cy, facing, phase, action, attack_progress, spin_angle)
        _NS_drakar._draw_drk_arm_two_handed_back(surface, cx, cy-6, facing, phase, grip_data["back_hand"], action)
        _NS_drakar._draw_axe(surface, grip_data["axe_head"][0], grip_data["axe_head"][1],
                             facing, grip_data["axe_angle"], action, attack_progress, pommel_pos=grip_data["pommel"])
        _NS_drakar._draw_drk_arm_two_handed_front(surface, cx, cy-6, facing, phase, grip_data["front_hand"], action, attack_progress)

    def _draw_drk_legs(surface, cx, cy, facing, phase, action):
        if action == "walk":
            stride = math.sin(phase*2)*7
            back_lift = max(0,-math.sin(phase*2))*6
            front_lift = max(0,math.sin(phase*2))*6
        else:
            stride = 0; back_lift = front_lift = 0
        _NS_drakar._draw_leg(surface, cx-13+int(stride), cy-int(back_lift), facing, back=True)
        _NS_drakar._draw_leg(surface, cx+13-int(stride), cy-int(front_lift), facing, back=False)

    def _draw_leg(surface, cx, cy, facing, back=False):
        pygame.draw.rect(surface, _NS_drakar.PALETTE["shadow_deep"], (cx-10,cy-21,22,27))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_darkest"], (cx-10,cy-21,21,25))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_dark"], (cx-9,cy-21,16,24))
        if not back:
            pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_mid"], (cx-6,cy-19,10,21))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_light"], (cx-3,cy-18,3,15))
        for strap_y in (cy-15, cy-6):
            pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_darkest"], (cx-10,strap_y,21,3))
            if not back:
                pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_mid"], (cx-9,strap_y,18,1))
            for stud_x in (cx-6, cx+4):
                pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_dark"], (stud_x,strap_y,3,3))
                if not back: pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_light"], (stud_x,strap_y,1,1))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["shadow_deep"], (cx-9,cy+6,19,9))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_darkest"], (cx-9,cy+6,18,9))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_dark"], (cx-7,cy+6,15,7))
        if not back:
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_mid"], (cx-7,cy+6,12,4))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_light"], (cx-6,cy+6,7,1))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_shine"], (cx-4,cy+6,3,1))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["shadow_deep"], (cx-12,cy+15,27,15))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_darkest"], (cx-12,cy+15,25,13))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_dark"], (cx-10,cy+15,21,12))
        if not back:
            pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_mid"], (cx-9,cy+15,15,7))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_light"], (cx-7,cy+16,9,4))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_darkest"], (cx-12,cy+22,27,6))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_dark"], (cx-12,cy+22,25,4))
        if not back:
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_mid"], (cx-10,cy+22,22,3))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_light"], (cx-9,cy+22,18,1))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_light"], (cx+facing*9,cy+25,3,3))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_shine"], (cx+facing*9,cy+25,1,1))

    def _draw_drk_waist(surface, cx, cy, facing, phase):
        pygame.draw.rect(surface, _NS_drakar.PALETTE["shadow_deep"], (cx-33,cy-9,67,15))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_darkest"], (cx-31,cy-9,64,15))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_dark"], (cx-31,cy-9,63,12))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_mid"], (cx-30,cy-7,60,7))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_light"], (cx-27,cy-7,9,3))
        for sx_off in (-24,-15,-6,12,21):
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_darkest"], (cx+sx_off-1,cy-3,6,6))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_dark"], (cx+sx_off,cy-3,4,4))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_mid"], (cx+sx_off,cy-3,3,3))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_light"], (cx+sx_off,cy-3,1,1))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["shadow_deep"], (cx-9,cy-9,21,16))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_darkest"], (cx-9,cy-9,19,16))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_dark"], (cx-7,cy-9,16,15))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_mid"], (cx-6,cy-7,13,12))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_light"], (cx-6,cy-7,4,3))
        rune_pulse = math.sin(phase*2)*0.3+0.7
        for r in range(7,0,-1):
            _NS_drakar._aacircle(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"],
                _NS_drakar._alpha(120*(7-r)/7*rune_pulse)), (cx+1,cy), r)
        pygame.draw.rect(surface, _NS_drakar.PALETTE["blood_darkest"], (cx-3,cy-3,8,7))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["blood_mid"], (cx-1,cy-1,6,4))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["blood_hot"], (cx,cy,3,1))
        loin_pts = [(cx-13,cy+4),(cx+13,cy+4),(cx+10,cy+18),(cx+4,cy+24),(cx-4,cy+24),(cx-10,cy+18)]
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["shadow_deep"], [(px+1,py+1) for px,py in loin_pts])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["leather_darkest"], loin_pts)
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["leather_dark"],
            [(cx-10,cy+4),(cx+10,cy+4),(cx+7,cy+18),(cx,cy+22),(cx-7,cy+18)])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["leather_mid"],
            [(cx-4,cy+6),(cx+4,cy+6),(cx+3,cy+18),(cx,cy+21),(cx-3,cy+18)])
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_darkest"], (cx,cy+6), (cx,cy+22), 1)
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_dark"], (cx-1,cy+22,4,3))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_light"], (cx,cy+22,2,1))

    def _draw_drk_torso(surface, cx, cy, facing, phase, action, rage_mode=False):
        breath = math.sin(phase*0.6)*3
        if action == "attack": breath += math.sin(phase*3)*1.5
        skin_base = _NS_drakar.PALETTE["skin_mid"]
        if rage_mode:
            rp = 0.3+0.2*math.sin(phase*4)
            skin_base = _NS_drakar._mix(skin_base, _NS_drakar.PALETTE["blood_mid"], rp)
        torso_pts = [(cx-27,cy-6),(cx-30,cy+9),(cx-25,cy+24),(cx+25,cy+24),
                     (cx+30,cy+9),(cx+27,cy-6),(cx+18,cy-15),(cx-18,cy-15)]
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["shadow_deep"], [(px+3,py+3) for px,py in torso_pts])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["skin_darkest"], torso_pts)
        _NS_drakar._poly(surface, _NS_drakar._clamp(skin_base),
            [(cx-25,cy-3+int(breath)),(cx-28,cy+9),(cx-22,cy+22),(cx+22,cy+22),
             (cx+28,cy+9),(cx+25,cy-3+int(breath)),(cx+15,cy-13),(cx-15,cy-13)])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["skin_light"],
            [(cx-21,cy+int(breath)),(cx-24,cy+9),(cx-18,cy+18),(cx+18,cy+18),
             (cx+24,cy+9),(cx+21,cy+int(breath)),(cx+12,cy-10),(cx-12,cy-10)])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["skin_shine"],
            [(cx-15,cy+1+int(breath)),(cx-4,cy+1+int(breath)),(cx-7,cy+12),(cx-15,cy+9)])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["skin_shine"],
            [(cx+4,cy+1+int(breath)),(cx+15,cy+1+int(breath)),(cx+15,cy+9),(cx+7,cy+12)])
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_rim"], (cx-12,cy+3+int(breath),4,1))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_rim"], (cx+7,cy+3+int(breath),4,1))
        pygame.draw.line(surface, _NS_drakar.PALETTE["skin_darkest"], (cx,cy-7+int(breath)), (cx,cy+18), 3)
        for i,y_off in enumerate((9,15,19)):
            for x_side in (-1,1):
                pygame.draw.line(surface, _NS_drakar.PALETTE["skin_darkest"],
                    (cx+x_side*3,cy+y_off),(cx+x_side*10,cy+y_off),1)
            pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_light"], (cx-7,cy+y_off-1,3,1))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_light"], (cx+4,cy+y_off-1,3,1))
        pygame.draw.line(surface, _NS_drakar.PALETTE["skin_darkest"], (cx+6,cy-4+int(breath)), (cx+15,cy+4), 1)
        pygame.draw.line(surface, _NS_drakar.PALETTE["skin_shine"], (cx+7,cy-3+int(breath)), (cx+13,cy+3), 1)
        for dx_off in (-8,-4,4,8):
            pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_light"], (cx+dx_off,cy+16,1,1))
        strap_start = (cx-27,cy-4); strap_end = (cx+27,cy+22)
        pygame.draw.line(surface, _NS_drakar.PALETTE["shadow_deep"],
            (strap_start[0]+1,strap_start[1]+1),(strap_end[0]+1,strap_end[1]+1),8)
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_darkest"], strap_start, strap_end, 7)
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_dark"], strap_start, strap_end, 6)
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_mid"],
            (strap_start[0],strap_start[1]-1),(strap_end[0],strap_end[1]-1),3)
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_light"],
            (strap_start[0],strap_start[1]-2),(strap_end[0],strap_end[1]-2),1)
        _NS_drakar._draw_shoulder_pauldron(surface, cx-facing*24, cy-12, facing)
        _NS_drakar._draw_bare_shoulder(surface, cx+facing*21, cy-12, facing)

    def _draw_shoulder_pauldron(surface, cx, cy, facing):
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["shadow_deep"],
            [(cx-13,cy+12),(cx-15,cy+4),(cx-10,cy-7),(cx-4,cy-12),
             (cx+6,cy-12),(cx+12,cy-7),(cx+15,cy+4),(cx+13,cy+12)])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["armor_darkest"],
            [(cx-12,cy+10),(cx-13,cy+4),(cx-9,cy-6),(cx-4,cy-10),
             (cx+6,cy-10),(cx+10,cy-6),(cx+13,cy+4),(cx+12,cy+10)])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["armor_dark"],
            [(cx-10,cy+9),(cx-12,cy+4),(cx-7,cy-4),(cx-3,cy-9),
             (cx+4,cy-9),(cx+9,cy-4),(cx+12,cy+4),(cx+10,cy+9)])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["armor_mid"],
            [(cx-7,cy+7),(cx-10,cy+3),(cx-6,cy-3),(cx-1,cy-7),
             (cx+3,cy-7),(cx+7,cy-3),(cx+10,cy+3),(cx+7,cy+7)])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["armor_light"],
            [(cx-4,cy),(cx-1,cy-4),(cx+1,cy-4),(cx+3,cy),(cx,cy+3),(cx-3,cy+3)])
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_shine"], (cx-1,cy-1,3,3))
        for x_off, height in [(-7,9),(-1,12),(6,9)]:
            sx = cx+x_off; st_y = cy-10-height
            _NS_drakar._poly(surface, _NS_drakar.PALETTE["shadow_deep"],
                [(sx+1,st_y+1),(sx-4+1,cy-7+1),(sx+4+1,cy-7+1)])
            _NS_drakar._poly(surface, _NS_drakar.PALETTE["armor_darkest"],
                [(sx,st_y),(sx-4,cy-7),(sx+4,cy-7)])
            _NS_drakar._poly(surface, _NS_drakar.PALETTE["armor_dark"],
                [(sx,st_y),(sx-3,cy-7),(sx+3,cy-7)])
            _NS_drakar._poly(surface, _NS_drakar.PALETTE["armor_mid"],
                [(sx,st_y),(sx-1,cy-7),(sx+3,cy-7)])
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_light"], (sx,st_y,1,3))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_shine"], (sx,st_y,1,1))
        for rx_off in (-9,0,9):
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_darkest"], (cx+rx_off-1,cy+6,3,3))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_light"], (cx+rx_off,cy+6,1,1))

    def _draw_bare_shoulder(surface, cx, cy, facing):
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_darkest"], (cx-8,cy-4,16,18))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_dark"], (cx-7,cy-3,14,16))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_mid"], (cx-5,cy-2,10,14))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_light"], (cx-3,cy-1,6,8))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_shine"], (cx-1,cy,2,2))

    def _draw_drk_arm_two_handed_front(surface, cx, cy, facing, phase, hand_pos, action, attack_progress=0):
        hx, hy = hand_pos
        pygame.draw.line(surface, _NS_drakar.PALETTE["shadow_deep"], (cx+facing*20,cy+2), (hx,hy), 12)
        pygame.draw.line(surface, _NS_drakar.PALETTE["skin_darkest"], (cx+facing*20,cy+2), (hx,hy), 10)
        pygame.draw.line(surface, _NS_drakar.PALETTE["skin_dark"], (cx+facing*20,cy+2), (hx,hy), 8)
        pygame.draw.line(surface, _NS_drakar.PALETTE["skin_mid"], (cx+facing*20,cy+1), (hx,hy), 4)
        pygame.draw.line(surface, _NS_drakar.PALETTE["skin_light"], (cx+facing*20,cy), (hx,hy), 2)
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_darkest"], (hx,hy), (hx+facing*5,hy+8), 10)
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_dark"], (hx,hy), (hx+facing*5,hy+8), 8)
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_mid"], (hx,hy), (hx+facing*5,hy+7), 4)
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_darkest"], (hx-5,hy-3,12,10))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_dark"], (hx-4,hy-2,10,8))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_mid"], (hx-3,hy-1,7,6))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_dark"], (hx-4,hy+2,10,4))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_mid"], (hx-3,hy+2,8,2))

    def _draw_drk_arm_two_handed_back(surface, cx, cy, facing, phase, hand_pos, action):
        hx, hy = hand_pos
        pygame.draw.line(surface, _NS_drakar.PALETTE["shadow_deep"], (cx-facing*18,cy+2), (hx,hy), 12)
        pygame.draw.line(surface, _NS_drakar.PALETTE["skin_darkest"], (cx-facing*18,cy+2), (hx,hy), 10)
        pygame.draw.line(surface, _NS_drakar.PALETTE["skin_dark"], (cx-facing*18,cy+2), (hx,hy), 8)
        pygame.draw.line(surface, _NS_drakar.PALETTE["skin_mid"], (cx-facing*18,cy+1), (hx,hy), 4)

    def _compute_two_handed_grip(cx, cy, facing, phase, action, attack_progress=0, spin_angle=0):
        if action == "attack":
            p = attack_progress
            if p < 0.15:
                t=p/0.15; axe_angle=-0.8-t*0.5; axe_x=cx+facing*(30-t*10); axe_y=cy-20-t*15
            elif p < 0.40:
                t=(p-0.15)/0.25; axe_angle=-1.3+t*0.3; axe_x=cx+facing*(20+t*5); axe_y=cy-35+t*10
            elif p < 0.55:
                t=(p-0.40)/0.15; t_ease=1-(1-t)**2
                axe_angle=-1.0+t_ease*2.5; axe_x=cx+facing*(25+t_ease*40); axe_y=cy-25+t_ease*20
            elif p < 0.70:
                t=(p-0.55)/0.15; axe_angle=1.5-t*0.5; axe_x=cx+facing*(65-t*20); axe_y=cy-5+t*5
            else:
                t=(p-0.70)/0.30; t_ease=1-(1-t)**2
                axe_angle=1.0*(1-t_ease)-0.8*t_ease; axe_x=cx+facing*(45-t_ease*15); axe_y=cy+t_ease*5
        elif action == "helix":
            axe_angle = spin_angle
            axe_x = cx+int(math.cos(spin_angle)*40)*facing
            axe_y = cy-10+int(math.sin(spin_angle)*15)
        else:
            bob = math.sin(phase*0.6)*2; axe_angle = -0.8
            axe_x = cx+facing*30; axe_y = cy-20+int(bob)
        pommel_x = axe_x-int(math.cos(axe_angle)*30)*facing
        pommel_y = axe_y-int(math.sin(axe_angle)*30)
        front_hand = (axe_x-int(math.cos(axe_angle)*15)*facing, axe_y-int(math.sin(axe_angle)*15))
        back_hand = (axe_x-int(math.cos(axe_angle)*25)*facing, axe_y-int(math.sin(axe_angle)*25))
        return {"axe_head":(axe_x,axe_y),"axe_angle":axe_angle,"pommel":(pommel_x,pommel_y),
                "front_hand":front_hand,"back_hand":back_hand}

    def _draw_axe(surface, cx, cy, facing, angle, action, attack_progress, pommel_pos=None):
        if pommel_pos is None:
            pommel_pos = (cx-int(math.cos(angle)*30)*facing, cy-int(math.sin(angle)*30))
        px, py = pommel_pos
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_darkest"], (px,py), (cx,cy), 9)
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_dark"], (px,py), (cx,cy), 7)
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_mid"], (px,py), (cx,cy), 5)
        mid_x=(px+cx)//2; mid_y=(py+cy)//2
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_light"], (mid_x-2,mid_y-2), (mid_x+2,mid_y+2), 1)
        for i in range(3):
            gx=px+int((cx-px)*(0.3+i*0.15)); gy=py+int((cy-py)*(0.3+i*0.15))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_darkest"], (gx-2,gy-1,5,3))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["gold_dark"], (px-3,py-3,7,7))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["gold_mid"], (px-2,py-2,5,5))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["gold_light"], (px-1,py-1,2,2))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_dark"], (cx-4,cy-4,9,9))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_mid"], (cx-3,cy-3,7,7))
        blade_size = 28
        for off, color in [(3,"shadow_deep"),(2,"blade_darkest"),(0,"blade_dark"),
                           (-1,"blade_mid"),(-2,"blade_light"),(-3,"blade_shine")]:
            bx=cx+facing*(8+off); by=cy+off
            _NS_drakar._poly(surface, _NS_drakar.PALETTE[color],
                [(bx,by-2),(bx+facing*blade_size,by-blade_size//2+off),
                 (bx+facing*(blade_size-4),by+off),(bx,by+2)])
            _NS_drakar._poly(surface, _NS_drakar.PALETTE[color],
                [(bx,by+2),(bx+facing*blade_size,by+blade_size//2+off),
                 (bx+facing*(blade_size-4),by+off),(bx,by-2)])
        pygame.draw.rect(surface, _NS_drakar.PALETTE["blade_shine"], (cx+facing*18,cy-4,3,1))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["white"], (cx+facing*18,cy-4,1,1))
        if action == "attack" and attack_progress > 0.4:
            for i in range(4):
                bx=cx+facing*(12+i*4); by=cy-8+int(_NS_drakar._hash01(i*7)*16)
                pygame.draw.rect(surface, _NS_drakar.PALETTE["blood_dark"], (bx,by,2,2))
                pygame.draw.rect(surface, _NS_drakar.PALETTE["blood_mid"], (bx,by,1,1))

    def _draw_drk_head(surface, cx, cy, facing, phase, action):
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_darkest"], (cx-8,cy+12,16,10))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_dark"], (cx-7,cy+12,14,9))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_mid"], (cx-5,cy+13,10,7))
        head_pts = [(cx-12,cy+8),(cx-14,cy),(cx-12,cy-10),(cx-8,cy-15),(cx+8,cy-15),
                    (cx+12,cy-10),(cx+14,cy),(cx+12,cy+8),(cx+8,cy+12),(cx-8,cy+12)]
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["shadow_deep"], [(px+2,py+2) for px,py in head_pts])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["skin_darkest"], head_pts)
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["skin_dark"],
            [(cx-11,cy+7),(cx-13,cy),(cx-11,cy-9),(cx-7,cy-14),(cx+7,cy-14),
             (cx+11,cy-9),(cx+13,cy),(cx+11,cy+7)])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["skin_mid"],
            [(cx-9,cy+5),(cx-11,cy-1),(cx-9,cy-8),(cx-5,cy-12),(cx+5,cy-12),
             (cx+9,cy-8),(cx+11,cy-1),(cx+9,cy+5)])
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_light"], (cx-6,cy-6,8,5))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_shine"], (cx-4,cy-5,4,2))
        for eye_side in (-1, 1):
            ex=cx+eye_side*5; ey=cy-3
            pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_darkest"], (ex-3,ey-2,6,4))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["eye_dark"], (ex-2,ey-1,4,3))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["eye_mid"], (ex-1,ey-1,3,2))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["eye_light"], (ex,ey-1,1,1))
            if action == "attack":
                _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["eye_glow"], (ex,ey), 3)
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_darkest"], (cx-9,cy-6,18,3))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_dark"], (cx-8,cy-6,16,2))
        _NS_drakar._draw_wild_hair(surface, cx, cy-14, facing, phase)
        _NS_drakar._draw_beard(surface, cx, cy+6, facing, phase)
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_dark"], (cx-2,cy-1,4,5))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_mid"], (cx-1,cy,2,3))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_light"], (cx-1,cy,1,1))

    def _draw_wild_hair(surface, cx, cy, facing, phase):
        hair_pts = [(cx-14,cy+4),(cx-16,cy-2),(cx-14,cy-8),(cx-8,cy-12),(cx,cy-14),
                    (cx+8,cy-12),(cx+14,cy-8),(cx+16,cy-2),(cx+14,cy+4)]
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["hair_darkest"], hair_pts)
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["hair_dark"],
            [(cx-12,cy+3),(cx-14,cy-2),(cx-12,cy-7),(cx-6,cy-11),(cx,cy-13),
             (cx+6,cy-11),(cx+12,cy-7),(cx+14,cy-2),(cx+12,cy+3)])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["hair_mid"],
            [(cx-8,cy),(cx-10,cy-4),(cx-6,cy-8),(cx,cy-10),(cx+6,cy-8),(cx+10,cy-4),(cx+8,cy)])
        spine = [(cx-14,cy+2),(cx-10,cy-6),(cx,cy-12),(cx+10,cy-6),(cx+14,cy+2)]
        tufts = _NS_drakar._tuft_points(spine, depth=5.0, min_len=6, seed=42)
        if len(tufts) > 2:
            pygame.draw.lines(surface, _NS_drakar.PALETTE["hair_dark"], False,
                             [(int(x),int(y)) for x,y in tufts], 2)
        for i in range(3):
            hx=cx-4+i*4; hy=cy-8-int(_NS_drakar._hash01(i*11)*4)
            pygame.draw.rect(surface, _NS_drakar.PALETTE["hair_light"], (hx,hy,2,1))

    def _draw_beard(surface, cx, cy, facing, phase):
        beard_pts = [(cx-10,cy),(cx-12,cy+6),(cx-8,cy+14),(cx-3,cy+18),
                     (cx+3,cy+18),(cx+8,cy+14),(cx+12,cy+6),(cx+10,cy)]
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["hair_darkest"], beard_pts)
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["hair_dark"],
            [(cx-8,cy+1),(cx-10,cy+6),(cx-6,cy+13),(cx-2,cy+16),(cx+2,cy+16),
             (cx+6,cy+13),(cx+10,cy+6),(cx+8,cy+1)])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["hair_mid"],
            [(cx-5,cy+2),(cx-7,cy+6),(cx-4,cy+11),(cx,cy+14),(cx+4,cy+11),
             (cx+7,cy+6),(cx+5,cy+2)])
        for i in range(5):
            bx=cx-4+i*2; by=cy+5+int(_NS_drakar._hash01(i*17)*6)
            pygame.draw.rect(surface, _NS_drakar.PALETTE["hair_light"], (bx,by,1,1))

    def _draw_axe_slash_trail(surface, boss, cx, cy, progress):
        if progress < 0.3 or progress > 0.75: return
        t = (progress-0.3)/0.45
        alpha = _NS_drakar._alpha(220*(1-abs(t-0.5)*2))
        facing = getattr(boss, "_drk_attack_dir", 1)
        trail_surf = pygame.Surface((300, 200), pygame.SRCALPHA)
        tcx, tcy = 150, 100
        for thick, color, a_mult in [
            (14,"blood_darkest",0.5),(10,"blood_dark",0.7),
            (6,"blood_mid",1.0),(3,"blood_light",1.0),(1,"blood_hot",1.0)]:
            arc_pts = []
            start_ang = -math.pi*0.4+t*math.pi*0.3
            end_ang = start_ang+math.pi*0.8
            for step in range(16):
                st = step/15; a = start_ang+st*(end_ang-start_ang)
                r = 50+st*20
                arc_pts.append((tcx+int(math.cos(a)*r)*facing, tcy+int(math.sin(a)*r*0.7)))
            for k in range(len(arc_pts)-1):
                fade = 1-(k/len(arc_pts))
                a_val = _NS_drakar._alpha(alpha*a_mult*fade)
                if a_val <= 0: continue
                pygame.draw.line(trail_surf, _NS_drakar._rgba(_NS_drakar.PALETTE[color], a_val),
                                 arc_pts[k], arc_pts[k+1], thick)
        surface.blit(trail_surf, (cx-150, cy-100))

    def _draw_impact_burst(surface, boss, cx, cy, progress):
        t = (progress-0.53)/0.17
        intensity = math.sin(t*math.pi)
        fs = _NS_drakar._fx_scale(boss)
        _NS_drakar._spark_star(surface, cx+int(30*boss.direction), cy,
            int(24*fs*intensity), _NS_drakar.PALETTE["blood_light"],
            int(220*intensity), spikes=6, rot=progress*3, core=_NS_drakar.PALETTE["blood_hot"])
        rr = int(35*fs*(0.5+t*0.5))
        if rr > 2:
            pygame.draw.ellipse(surface,
                _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"], int(180*intensity)),
                (cx-rr,cy-rr//3,rr*2,max(4,rr*2//3)), 3)
            pygame.draw.ellipse(surface,
                _NS_drakar._rgba(_NS_drakar.PALETTE["blood_hot"], int(140*intensity)),
                (cx-rr+4,cy-rr//3+2,max(1,rr*2-8),max(2,rr*2//3-4)), 2)
        for i in range(5):
            ang=i*math.pi*2/5+progress*2; dist=int(20*fs*t)
            sx=cx+int(math.cos(ang)*dist); sy=cy+int(math.sin(ang)*dist*0.6)
            sz=max(1,int(4*(1-t)))
            pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["armor_dark"], int(200*intensity)),
                (sx,sy,sz,sz))

    def _draw_rage_mist(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        count = 12 if intense else 6
        for i in range(count):
            t = (phase*0.3+i*0.15)%1.0
            px = cx+int(math.sin(phase+i*1.7)*20)+(facing*int(t*10) if trail else 0)
            py = cy-int(t*40)
            alpha = _NS_drakar._alpha(180*(1-t))
            size = max(1, int(3*(1-t)))
            if i%3==0:
                pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["ember_dark"],alpha),
                    (px,py,size+1,size+1))
            pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["ember_mid"],alpha),
                (px,py,size,size))
            if t < 0.5:
                pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["ember_light"],alpha),
                    (px,py,1,1))

    def _draw_shadow(surface, x, y, lift=0):
        def build_shadow():
            s = pygame.Surface((150, 40), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (0,0,0,120), (10,5,130,30))
            pygame.draw.ellipse(s, (0,0,0,80), (20,10,110,20))
            return s
        shadow = _NS_drakar._static("shadow", build_shadow)
        sy = y + min(20, lift)
        surface.blit(shadow, (x-75, sy-15))

    def _draw_rage_aura(surface, x, y, phase):
        def build_aura():
            s = pygame.Surface((390, 260), pygame.SRCALPHA)
            for r in range(120, 0, -2):
                a = int(40*(120-r)/120)
                pygame.draw.ellipse(s, (*_NS_drakar.PALETTE["rage_darkest"], a),
                    (195-r, 130-r//2, r*2, r))
            return s
        aura = _NS_drakar._static("rage_aura", build_aura)
        pulse_alpha = int(200+55*math.sin(phase*1.5))
        aura.set_alpha(min(255, pulse_alpha))
        surface.blit(aura, (x-195, y-50))

    def _draw_ground_ring(surface, boss, x, y, phase, skill):
        fs = _NS_drakar._fx_scale(boss)
        r = int(65 * fs)
        pulse = 0.7 + 0.3*math.sin(phase*2)
        alpha = _NS_drakar._alpha(180*pulse)
        _NS_drakar._dashed_ring(surface, x, y, r,
            _NS_drakar.PALETTE["rune_dark"], alpha, phase*0.3, segments=12, thick=3, squash=0.4)
        _NS_drakar._dashed_ring(surface, x, y, int(r*0.7),
            _NS_drakar.PALETTE["rune_mid"], int(alpha*0.7),
            -phase*0.5, segments=8, thick=2, squash=0.4)
        for i in range(6):
            ang=phase*0.2+i*math.pi/3
            rx=x+int(math.cos(ang)*r*0.85); ry=y+int(math.sin(ang)*r*0.35)
            pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["rune_light"], alpha), (rx,ry,3,3))

    def _draw_battlehunger_ground(surface, boss, x, y, timer, phase):
        fs = _NS_drakar._fx_scale(boss)
        duration = 90
        progress = max(0.0, min(1.0, 1-timer/duration))
        tx, ty = x, y+105
        if progress < 0.15:
            t = progress/0.15; rr = int(80*fs*t)
            a = int(230*(1-t*0.5))
            pygame.draw.ellipse(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_dark"],a),
                (tx-rr,ty-rr//3,rr*2,max(4,rr*2//3)), 3)
            _NS_drakar._spark_star(surface, tx, ty, int(22*fs),
                _NS_drakar.PALETTE["blood_light"], int(200*(1-t)),
                spikes=8, rot=phase, core=_NS_drakar.PALETTE["rage_light"])
        if progress >= 0.1:
            r = int(80*fs*min(1.0,(progress-0.1)*2))
            if r > 3:
                for off, color, a_mult in [
                    (0,"blood_darkest",1.0),(4,"blood_dark",0.85),(8,"rage_mid",0.7)]:
                    pygame.draw.ellipse(surface,
                        _NS_drakar._rgba(_NS_drakar.PALETTE[color], _NS_drakar._alpha(220*a_mult)),
                        (tx-r+off, ty-r//3+off, max(1,r*2-off*2), max(2,r*2//3-off)))
                if progress > 0.2:
                    for i in range(5):
                        ang=i*math.pi*2/5+phase*0.1
                        _NS_drakar._jagged_crack(surface, tx, ty, ang, int(50*fs),
                            (_NS_drakar.PALETTE["blood_darkest"], _NS_drakar.PALETTE["blood_mid"]),
                            int(160*min(1.0,(progress-0.2)*3)), seed=i*7+13)
                for i in range(8):
                    t=(phase*0.5+i*0.12)%1.0
                    mx=tx+int(math.sin(phase+i*2)*r*0.4); my=ty-int(t*30*fs)
                    a=int(160*(1-t))
                    pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["ember_mid"],a), (mx,my,2,2))

    def _draw_battlehunger_foreground(surface, boss, x, y, timer, phase):
        fs = _NS_drakar._fx_scale(boss)
        duration = 90
        progress = max(0.0, min(1.0, 1-timer/duration))
        tx, ty = x, y+105
        r = int(80*fs*min(1.0, progress*3))
        if r < 5: return
        for i in range(8):
            col_angle=i*math.pi*2/8+phase*0.15
            col_dist=int(r*0.55)
            col_x=tx+int(math.cos(col_angle)*col_dist)
            col_y_base=ty+int(math.sin(col_angle)*col_dist*0.4)
            for layer in range(6):
                layer_t=(phase*0.7+i*0.3+layer*0.15)%1.0
                layer_y=col_y_base-int(layer_t*54)
                layer_alpha=_NS_drakar._alpha(220*(1-layer_t))
                layer_w=int(9+layer_t*4); layer_h=int(6+layer_t*4)
                pygame.draw.ellipse(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_darkest"],layer_alpha),
                    (col_x-layer_w, layer_y-layer_h, layer_w*2, layer_h*2))
                pygame.draw.ellipse(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["rage_mid"],layer_alpha),
                    (col_x-layer_w+3, layer_y-layer_h+3, max(1,layer_w*2-6), max(1,layer_h*2-6)))
                pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["rage_light"],layer_alpha),
                    (col_x,layer_y-2,2,2))
        core_pulse = math.sin(phase*3)*0.4+0.6
        for cr in range(15,0,-1):
            alpha = _NS_drakar._alpha(200*(15-cr)/15*core_pulse)
            _NS_drakar._aacircle(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"],alpha), (tx,ty), cr)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["rage_light"], (tx,ty), 5)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["rage_hot"], (tx,ty), 2)
        for i in range(24):
            angle=i*math.pi*2/24+phase*0.4
            sp_r=int(r*(0.4+(i%3)*0.2))
            sx=tx+int(math.cos(angle)*sp_r); sy=ty+int(math.sin(angle)*sp_r*0.4)
            alpha = _NS_drakar._alpha(200)
            pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"],alpha), (sx,sy,3,3))
            pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_light"],alpha), (sx,sy,1,1))

    def _draw_counterhelix_ground(surface, boss, x, y, timer, phase):
        fs = _NS_drakar._fx_scale(boss)
        duration = 45
        progress = max(0.0, min(1.0, 1-timer/duration))
        r = int((90+progress*45)*fs)
        alpha = _NS_drakar._alpha(240*(1-progress*0.5))
        if progress < 0.1:
            t = progress/0.1
            _NS_drakar._spark_star(surface, x, y+114, int(28*fs),
                _NS_drakar.PALETTE["blood_light"], int(200*(1-t)),
                spikes=8, rot=phase*2, core=_NS_drakar.PALETTE["blood_hot"])
        _NS_drakar._dashed_ring(surface, x, y+114, r,
            _NS_drakar.PALETTE["blood_dark"], alpha, phase*0.8, segments=12, thick=4, squash=0.4)
        _NS_drakar._dashed_ring(surface, x, y+114, int(r*0.75),
            _NS_drakar.PALETTE["blood_mid"], int(alpha*0.8),
            -phase*1.2, segments=10, thick=3, squash=0.4)
        spin = progress*math.pi*6
        for i in range(4):
            a = spin+i*math.pi/2
            arc_pts = []
            for step in range(12):
                st = step/11; arc_a = a+st*math.pi/3
                arc_pts.append((x+int(math.cos(arc_a)*(r-8)), y+114+int(math.sin(arc_a)*(r-8)*0.4)))
            for k in range(len(arc_pts)-1):
                pygame.draw.line(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_light"],alpha),
                    arc_pts[k], arc_pts[k+1], 4)
                pygame.draw.line(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_hot"],alpha),
                    arc_pts[k], arc_pts[k+1], 2)
        for i in range(6):
            ga = phase*2+i*math.pi/3
            gx = x+int(math.cos(ga)*r*0.6); gy = y+114+int(math.sin(ga)*r*0.25)
            pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_shine"],alpha), (gx,gy,2,2))

    def _draw_berserkerscall_ground(surface, boss, x, y, timer, phase):
        fs = _NS_drakar._fx_scale(boss)
        duration = 60
        progress = max(0.0, min(1.0, 1-timer/duration))
        if progress < 0.2:
            t = progress/0.2; rr = int(40*fs*t); a = int(230*(1-t*0.3))
            pygame.draw.ellipse(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"],a),
                (x-rr,y+114-rr//3,rr*2,max(4,rr*2//3)), 3)
            _NS_drakar._spark_star(surface, x, y+114, int(18*fs),
                _NS_drakar.PALETTE["rage_light"], int(200*(1-t)), spikes=6, rot=phase)
        if progress > 0.15:
            t = (progress-0.15)/0.85
            r = int((67+t*120)*fs)
            base_alpha = _NS_drakar._alpha(240*(1-t))
            _NS_drakar._dashed_ring(surface, x, y+114, r,
                _NS_drakar.PALETTE["blood_mid"], base_alpha, phase*0.6, segments=14, thick=3, squash=0.4)
            for i in range(8):
                ang = i*math.pi*2/8+phase*0.3
                _NS_drakar._chevron(surface,
                    x+int(math.cos(ang)*r), y+114+int(math.sin(ang)*r*0.4),
                    ang, int(10*fs), _NS_drakar.PALETTE["blood_light"], base_alpha, width=2)

    def _draw_berserkerscall_foreground(surface, boss, x, y, timer, phase):
        fs = _NS_drakar._fx_scale(boss)
        duration = 60
        progress = max(0.0, min(1.0, 1-timer/duration))
        if progress < 0.3:
            t = progress/0.3; glow_r = int((18+t*18)*fs)
            for r in range(glow_r+9,0,-1):
                alpha = _NS_drakar._alpha(180*(glow_r+9-r)/(glow_r+9)*t)
                _NS_drakar._aacircle(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_dark"],alpha), (x,y-6), r)
            _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["blood_mid"], (x,y-6), 15)
            _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["rage_light"], (x,y-6), 9)
            _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["rage_hot"], (x,y-6), 4)
            _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["white"], (x,y-6), 2)
            for i in range(12):
                angle=i*math.pi/6
                mist_x=x+int(math.cos(angle)*45*fs*t); mist_y=y-12+int(math.sin(angle)*37*fs*t)
                alpha = _NS_drakar._alpha(200*t)
                _NS_drakar._aacircle(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"],alpha), (mist_x,mist_y), 6)
                _NS_drakar._aacircle(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["rage_light"],alpha), (mist_x,mist_y), 3)
        else:
            t = (progress-0.3)/0.7; wave_r = int(t*195*fs)
            for i in range(28):
                angle=i*math.pi*2/28
                px=x+int(math.cos(angle)*wave_r); py=y-12+int(math.sin(angle)*wave_r*0.7)
                alpha = _NS_drakar._alpha(240*(1-t))
                _NS_drakar._aacircle(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_dark"],alpha), (px,py), 7)
                _NS_drakar._aacircle(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"],alpha), (px,py), 6)
                _NS_drakar._aacircle(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["rage_light"],alpha), (px,py), 3)
                pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["rage_hot"],alpha), (px,py,3,3))
                pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["white"],alpha), (px,py,1,1))
            for i in range(14):
                angle=i*math.pi/7
                inner_r=int(wave_r*0.65); outer_r=wave_r
                p1=(x+int(math.cos(angle)*inner_r), y-12+int(math.sin(angle)*inner_r*0.7))
                p2=(x+int(math.cos(angle)*outer_r), y-12+int(math.sin(angle)*outer_r*0.7))
                alpha = _NS_drakar._alpha(220*(1-t))
                pygame.draw.line(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_light"],alpha), p1, p2, 4)
                pygame.draw.line(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["rage_hot"],alpha), p1, p2, 2)

    def _draw_cullingblade_ground(surface, boss, x, y, timer, phase):
        fs = _NS_drakar._fx_scale(boss)
        tx, ty = _NS_drakar._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1-timer/duration))
        if progress < 0.4:
            t = progress/0.4; r = int(75*fs*t); alpha = _NS_drakar._alpha(200*t)
            _NS_drakar._dashed_ring(surface, tx, ty, r,
                _NS_drakar.PALETTE["blood_dark"], alpha, phase*0.8, segments=10, thick=4, squash=0.4)
            for i in range(6):
                ang=i*math.pi/3+phase*0.5
                _NS_drakar._chevron(surface, tx+int(math.cos(ang)*r), ty+int(math.sin(ang)*r*0.4),
                    ang+math.pi, int(12*fs), _NS_drakar.PALETTE["blood_light"], alpha, width=2)
            _NS_drakar._spark_star(surface, tx, ty, int(15*fs*t),
                _NS_drakar.PALETTE["blood_hot"], int(180*t), spikes=4, rot=phase*2)
        if progress >= 0.4:
            t = (progress-0.4)/0.6
            r = int((75+t*45)*fs); alpha = _NS_drakar._alpha(240*(1-t*0.5))
            pygame.draw.ellipse(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_darkest"],alpha),
                (tx-r,ty-r//3,r*2,r*2//3))
            pygame.draw.ellipse(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_dark"],alpha),
                (tx-r+7,ty-r//3+6,max(1,r*2-14),max(2,r*2//3-12)))
            for i in range(7):
                ang=i*math.pi*2/7+0.3
                _NS_drakar._jagged_crack(surface, tx, ty, ang, int(60*fs),
                    (_NS_drakar.PALETTE["blood_darkest"], _NS_drakar.PALETTE["blood_mid"]),
                    int(180*(1-t)), seed=i*11+7)

    def _draw_cullingblade_foreground(surface, boss, x, y, timer, phase):
        fs = _NS_drakar._fx_scale(boss)
        tx, ty = _NS_drakar._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1-timer/duration))
        if progress < 0.4:
            t = progress/0.4; facing = boss.direction
            charge_x = x+facing*60; charge_y = y-9; cr = int((12+t*15)*fs)
            for r in range(cr+10,0,-1):
                alpha = _NS_drakar._alpha(220*(cr+10-r)/(cr+10))
                _NS_drakar._aacircle(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_darkest"],alpha), (charge_x,charge_y), r)
            for r in range(cr,0,-1):
                alpha = _NS_drakar._alpha(240*(cr-r+1)/cr)
                _NS_drakar._aacircle(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"],alpha), (charge_x,charge_y), r)
            _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["blood_light"], (charge_x,charge_y), max(1,cr-4))
            _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["rage_light"], (charge_x,charge_y), max(1,cr-7))
            _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["rage_hot"], (charge_x,charge_y), max(1,cr-10))
            _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["white"], (charge_x,charge_y), max(1,cr-13))
        elif progress < 0.65:
            t = (progress-0.4)/0.25; intensity = math.sin(t*math.pi)
            slash_len = int((97+t*37)*fs)
            for slash_dir in [(1,1),(1,-1)]:
                dx,dy = slash_dir
                p1 = (tx-dx*slash_len, ty-dy*slash_len); p2 = (tx+dx*slash_len, ty+dy*slash_len)
                for thick, color, a_mult in [
                    (16,"blood_darkest",0.6),(12,"blood_dark",0.8),(8,"blood_mid",1.0),
                    (5,"blood_light",1.0),(3,"blood_hot",1.0),(1,"blood_shine",1.0)]:
                    alpha = _NS_drakar._alpha(255*intensity*a_mult)
                    if alpha <= 0: continue
                    pygame.draw.line(surface, _NS_drakar._rgba(_NS_drakar.PALETTE[color], alpha), p1, p2, thick)
            for r in range(int(37*fs),0,-1):
                alpha = _NS_drakar._alpha(240*intensity*(int(37*fs)-r)/max(1,int(37*fs)))
                _NS_drakar._aacircle(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_hot"],alpha), (tx,ty), r)
            _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["blood_shine"], (tx,ty), int(15*fs))
            _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["white"], (tx,ty), int(7*fs))
            _NS_drakar._spark_star(surface, tx, ty, int(30*fs*intensity),
                _NS_drakar.PALETTE["blood_light"], int(220*intensity),
                spikes=8, rot=phase*4, core=_NS_drakar.PALETTE["white"])
            for i in range(20):
                angle=i*math.pi/10; spatter_len=int(slash_len*0.8)
                sx=tx+int(math.cos(angle)*spatter_len); sy=ty+int(math.sin(angle)*spatter_len)
                alpha = _NS_drakar._alpha(240*intensity)
                pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"],alpha), (sx,sy,5,5))
                pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_hot"],alpha), (sx,sy,4,4))
                pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_shine"],alpha), (sx,sy,2,2))
        else:
            t = (progress-0.65)/0.35
            for i in range(18):
                fall_t = (phase*0.5+i*0.1)%1.0
                rx=tx+int(math.sin(phase+i)*60); ry=ty-36+int(fall_t*60)
                alpha = _NS_drakar._alpha(220*(1-t)*(1-fall_t*0.5))
                if alpha > 0:
                    pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_dark"],alpha), (rx,ry,4,6))
                    pygame.draw.rect(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"],alpha), (rx,ry,3,4))
            for slash_dir in [(1,1),(1,-1)]:
                dx,dy = slash_dir; slash_len=60
                p1=(tx-dx*slash_len, ty-dy*slash_len); p2=(tx+dx*slash_len, ty+dy*slash_len)
                alpha = _NS_drakar._alpha(150*(1-t))
                pygame.draw.line(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_dark"],alpha), p1, p2, 4)
                pygame.draw.line(surface, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"],alpha), p1, p2, 2)

'''

def main():
    """Replace _NS_drakar in bosses/level1.py"""
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'bosses', 'level1.py')
    with open(path, 'r') as f:
        content = f.read()

    # Find start and end of _NS_drakar class
    lines = content.split('\n')
    start_idx = None
    end_idx = None
    for i, line in enumerate(lines):
        if line.startswith('class _NS_drakar:'):
            start_idx = i
        elif start_idx is not None and line.startswith('class '):
            end_idx = i
            break

    if start_idx is None:
        print("ERROR: Could not find _NS_drakar class")
        return 1
    if end_idx is None:
        print("ERROR: Could not find end of _NS_drakar class")
        return 1

    print(f"Found _NS_drakar at lines {start_idx+1}-{end_idx}")

    # Build new content
    new_lines = lines[:start_idx] + NEW_NAMESPACE.rstrip().split('\n') + [''] + lines[end_idx:]
    new_content = '\n'.join(new_lines)

    with open(path, 'w') as f:
        f.write(new_content)

    print(f"Patched: removed {end_idx - start_idx} lines, inserted {len(NEW_NAMESPACE.strip().split(chr(10)))} lines")
    return 0

if __name__ == '__main__':
    sys.exit(main())
