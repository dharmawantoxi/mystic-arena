#!/usr/bin/env python3
"""SNAPSHOT renderer morgath v1 (sebelum upgrade Pixel Masterwork v2).

Dibuat otomatis sebelum rewrite `_NS_morgath` di bosses/level1.py.
Dipakai tools/_audit_morgath_v2.py untuk lembar before/after —
jangan diedit manual; kalau perlu regenerasi, ambil dari git history.
"""
import math
import pygame

try:
    import lighting as _lighting
except Exception:  # pragma: no cover
    _lighting = None

class _NS_morgath:
    """Namespace morgath - Arc Warden mini boss (ranged lightning caster)."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Robe / cloak (dark purple)
        "robe_darkest": (12, 8, 25),
        "robe_dark": (30, 20, 55),
        "robe_mid": (60, 40, 100),
        "robe_light": (105, 75, 160),
        "robe_edge": (155, 120, 210),

        # Armor plating (dark blue-steel)
        "armor_darkest": (8, 12, 25),
        "armor_dark": (25, 40, 65),
        "armor_mid": (55, 85, 120),
        "armor_light": (110, 150, 190),
        "armor_shine": (180, 210, 240),

        # Gold trim (armor accents)
        "gold_dark": (75, 55, 20),
        "gold_mid": (160, 125, 55),
        "gold_light": (230, 195, 110),
        "gold_shine": (255, 235, 170),

        # Crystal orb (bright cyan-blue, main magic color)
        "orb_darkest": (5, 15, 40),
        "orb_dark": (20, 55, 130),
        "orb_mid": (60, 130, 220),
        "orb_light": (130, 200, 255),
        "orb_hot": (200, 235, 255),
        "orb_shine": (240, 250, 255),

        # Lightning/arc (bright electric blue-white)
        "arc_darkest": (15, 30, 80),
        "arc_dark": (40, 90, 190),
        "arc_mid": (90, 160, 240),
        "arc_light": (180, 220, 255),
        "arc_hot": (230, 245, 255),
        "arc_shine": (255, 255, 255),

        # Flux purple (ability accent)
        "flux_darkest": (25, 8, 45),
        "flux_dark": (65, 25, 110),
        "flux_mid": (130, 60, 200),
        "flux_light": (190, 130, 240),
        "flux_hot": (225, 180, 255),

        # Skin (visible on hands/face if any) - shadowed
        "skin_darkest": (35, 30, 55),
        "skin_dark": (75, 65, 100),
        "skin_mid": (130, 115, 160),
        "skin_light": (180, 165, 210),

        # Ground rune
        "rune_dark": (15, 25, 60),
        "rune_mid": (60, 110, 200),
        "rune_light": (150, 200, 255),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 3, 8),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_morgath._clamp(color)
        if _NS_morgath.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_morgath._clamp(color)
        if _NS_morgath.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_morgath._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            # Konversi koordinat DUNIA target ke ruang jangkar (x, y)
            # DENGAN kompensasi scale. Hero di-render ke canvas
            # offscreen lalu di-scale saat blit (heroes/__init__.py),
            # jadi titik canvas harus = (delta dunia)/scale supaya
            # beam/proyektil mendarat TEPAT di target setelah blit.
            # Boss yang digambar langsung di layar tidak terpengaruh
            # (scale = 1).
            scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        return int(x + 240 / float(getattr(boss, "_render_scale", 1.0) or 1.0) * getattr(boss, "direction", 1)), int(y)

    def _jagged_line(surface, color, start, end, jitter=4, segments=6, width=2):
        """Draw jagged lightning line between two points."""
        color = _NS_morgath._clamp(color)
        prev = start
        for i in range(1, segments + 1):
            t = i / segments
            bx = int(start[0] + (end[0] - start[0]) * t)
            by = int(start[1] + (end[1] - start[1]) * t)
            if i < segments:
                # Perpendicular jitter
                dx = end[0] - start[0]
                dy = end[1] - start[1]
                length = max(1, math.hypot(dx, dy))
                perp_x = -dy / length
                perp_y = dx / length
                jit = (math.sin(t * 12 + start[0]) - 0.5) * jitter * 2
                bx += int(perp_x * jit)
                by += int(perp_y * jit)
            pygame.draw.line(surface, color, prev, (bx, by), width)
            prev = (bx, by)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_morgath(surface, boss, x, y):
        """Entry point untuk Boss.draw() sekaligus heroes.render_hero()."""
        # Beam-only pass (hero): body sudah di-blit ter-scale oleh
        # heroes/__init__.py; di sini hanya beam yang digambar, pada
        # koordinat & skala dunia = identik dengan versi mini boss.
        if getattr(boss, "_beam_pass_only", False):
            _NS_morgath._draw_mor_beam_pass(surface, boss, x, y)
            return

        # Jalur hero (lane): heroes/__init__ men-set _render_scale, dan
        # _finish_hd_sprite sudah menambah rim/terminator -> pass cahaya
        # di _draw_mor_rig_at dilewati (supaya tidak dobel).
        _NS_morgath._MOR_LANE.v = hasattr(boss, "_render_scale")
        _NS_morgath._update_mor_attack_anim(boss)
        action, pulse, ap = _NS_morgath._resolve_mor_pose(
            boss, _NS_morgath._detect_moving(boss))
        boss._mor_pose_action = action
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        portrait = bool(getattr(boss, "_portrait_hd", False))
        facing = getattr(boss, "direction", 1) or 1
        flash = _NS_morgath._alpha(170 * (getattr(boss, "hurt_flash_timer", 0)
                                          / 8.0))

        # ── Latar. Dibuang total saat portrait supaya auto-crop Hero
        #    Shop terisi wajah & material (orb), bukan lingkaran efek.
        if not portrait:
            _NS_morgath._draw_arc_aura(surface, x, y, pulse)
            _NS_morgath._draw_ground_rune(surface, x,
                                          y + _NS_morgath.GROUND_DY,
                                          pulse, active_skill)
            if active_skill == "q":
                _NS_morgath._draw_sparkwraith_ground(surface, boss, x, y,
                                                      skill_timer, pulse)
            elif active_skill == "w":
                _NS_morgath._draw_flux_ground(surface, boss, x, y,
                                               skill_timer, pulse)
            elif active_skill == "e":
                _NS_morgath._draw_magneticfield_ground(surface, boss, x, y,
                                                        skill_timer, pulse)
            elif active_skill == "r":
                _NS_morgath._draw_tempest_ground(surface, boss, x, y,
                                                  skill_timer, pulse)
            # PERTAGAS: gelombang kejut aktivasi skill (12 frame pertama)
            _MOR_DUR = {"q": 50, "w": 80, "e": 90, "r": 100}
            if active_skill in _MOR_DUR:
                age = _MOR_DUR[active_skill] - skill_timer
                if 0 <= age < 12:
                    st = age / 12.0
                    a = _NS_morgath._alpha(235 * (1 - st))
                    rr = int(16 + st * 50)
                    gy = y + _NS_morgath.GROUND_DY
                    _NS_morgath._aacircle(surface,
                                          (*_NS_morgath.PALETTE["arc_mid"], a),
                                          (x, gy), rr, 2)
                    _NS_morgath._aacircle(surface,
                                          (*_NS_morgath.PALETTE["arc_shine"], a),
                                          (x, gy), max(1, rr // 2), 1)

        # ── Karakter (SATU rig masterwork; hem dipatok di GROUND_DY)
        if not portrait:
            _NS_morgath._draw_shadow(surface, x, y + _NS_morgath.GROUND_DY)
        _NS_morgath._draw_mor_rig_at(surface, x, y, facing, pulse, action,
                                     ap, portrait, flash)

        # Beam petir lahir dari telapak cast (MOR_MUZZLE). Skip saat beam
        # digambar terpisah langsung di layar skala 1.0 (heroes/__init__),
        # supaya beam hero = persis beam mini boss (tidak kena smoothscale).
        if action == "attack" and not getattr(boss, "_skip_beam", False):
            _NS_morgath._draw_lightning_projectile(
                surface, boss, x, y, _NS_morgath._mor_progress(boss))

        # Tempest Double clone
        if active_skill == "r":
            _NS_morgath._draw_tempest_clone(surface, boss, x, y, skill_timer, pulse)

        # Foreground FX
        if active_skill == "q":
            _NS_morgath._draw_sparkwraith_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_morgath._draw_flux_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_morgath._draw_magneticfield_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_morgath._draw_tempest_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_mor_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_mor_previous_timer", 0))
        active = bool(getattr(boss, "_mor_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._mor_attack_active = True
            boss._mor_attack_frame = 0
            # Kunci arah + posisi target saat serangan dimulai.
            # Beam petir jadi terbang lurus ke titik target yang
            # SAMA selama animasi, tidak ikut "lompat" kalau hero
            # (versi summon) berbalik / ganti target di tengah cast.
            boss._mor_attack_dir = int(getattr(boss, "direction", 1))
            # Simpan sebagai OFFSET DUNIA relatif terhadap posisi boss
            # (bukan ruang canvas). Saat render ter-scale,
            # _draw_lightning_projectile membaginya dengan
            # _render_scale; saat render di layar (skala 1.0, termasuk
            # beam pass hero) offset dipakai apa adanya. Dengan cara
            # ini tidak ada galat pembulatan dari konversi int canvas.
            _t = getattr(boss, "target", None)
            if _t is not None and getattr(_t, "alive", True):
                boss._mor_attack_target = (
                    int(_t.x) - int(getattr(boss, "x", 0)),
                    int(_t.y) - int(getattr(boss, "y", 0)))
            else:
                tx, ty = _NS_morgath._target_position(
                    boss, getattr(boss, "x", 0), getattr(boss, "y", 0))
                boss._mor_attack_target = (
                    int(tx) - int(getattr(boss, "x", 0)),
                    int(ty) - int(getattr(boss, "y", 0)))
            active = True
        elif active and timer > 0:
            boss._mor_attack_frame = int(getattr(boss, "_mor_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._mor_attack_active = False
            boss._mor_attack_frame = 0
            active = False

        boss._mor_previous_timer = timer
        boss._mor_attack_progress = (
            min(1.0, getattr(boss, "_mor_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_mor_last_x"):
            boss._mor_last_x = boss.x
            boss._mor_last_y = boss.y
            return False
        dx = abs(boss.x - boss._mor_last_x)
        dy = abs(boss.y - boss._mor_last_y)
        boss._mor_last_x = boss.x
        boss._mor_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _mor_progress(boss):
        # LIVE dari attack_timer (bukan counter frame yang cuma naik
        # saat renderer dipanggil). Dengan body hero di-cache (renderer
        # dipanggil tiap N frame), progress tetap maju tiap frame ->
        # beam live tetap mulus 60fps.
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_mor_attack_active", False):
            return max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        return 0.0

    # ---- PROCEDURAL MASTERWORK RIG ----------------------------------
    # Badan lama terukur hanya 35x55 px (alpha>=1) vs rujukan keluarga
    # morgath H82/W120 (gornak 115x121, drakar 138x190): caster-nya
    # terlihat seperti stik di samping mini boss lain, detailnya
    # tenggelam. Rig ini membangun ulang tubuh sebagai SATU bone rig 2D
    # berlapis: sendi bahu/siku/telapak dihitung per-pose, hem jubah
    # DIPATOK di GROUND_DY (jubah tidak melayang), bahu melebar lewat
    # pauldron berlapis, dan hierarki nilai dijaga: orb kepala paling
    # terang (focal point), lalu arc FX, emas, armor, baru jubah.
    # Kalibrasi ke keluarga: badan padat boss 1x ~= H84/W50 (rujukan
    # "morgath H82/W120" di _NS_gornak diukur DENGAN FX; padat + arc
    # aura + rune tanah = H~95/W~110 di sini). Di bawah gornak (119),
    # sejajar urutan keluarga, dan jauh dari rig lama (35x55).
    SCALE = 0.9
    # Jangkar boss = pusat hitbox; LIFT menurunkan badan supaya wajah
    # (orb) tidak tertutup HP bar (digambar di y-r-15..y-r-7, r=51).
    LIFT = 4
    # Hem jubah dalam RUANG LOKAL; garis tanah dunia diturunkan dari
    # sini supaya bayangan/rune/hem tidak pernah saling lepas.
    FEET_DY = 40
    GROUND_DY = int(round(FEET_DY * SCALE)) - LIFT        # ~32

    # Buffer rig: dibatasi dari extents TERUKUR semua pose (idle/walk/
    # attack/4 stance skill, dua LOD) + margin 4 px (outline digambar
    # di luar buffer, jadi tidak dihitung di sini). Dikunci
    # tools/test_morgath_masterwork.py.
    RIG_W, RIG_H = 74, 100
    RIG_OX, RIG_OY = 33, 58

    # Bidang acuan cahaya TETAP (alasan: sama seperti GRAD_BOX gornak -
    # kalau ikut bbox, arah cahaya bergeser tiap pose = lampu berkedip).
    GRAD_BOX = (RIG_OX - 28, RIG_OY - 46, 62, 92)

    # Sendi dalam RUANG LOKAL (y=0 jangkar, + ke bawah).
    WAIST_Y = -8
    SHOULDER_Y = -22
    SHOULDER_FRONT = (10, SHOULDER_Y)
    SHOULDER_BACK = (-11, SHOULDER_Y - 1)
    ORB_CENTER = (2, -31)
    ORB_R = 9
    CROWN_Y = -42

    # Muzzle beam = telapak cast di puncak thrust. Beam lahir dari
    # TELAPAK (bukan angka lepas) supaya selalu tersambung ke tangan.
    MOR_MUZZLE = (27, -15)

    # Penanda "render ke canvas hero" (lane). Dipasang per-frame oleh
    # draw_morgath; dipakai _draw_mor_rig_at untuk pass cahaya.
    class _MOR_LANE:
        v = False

    # ------------------------------------------------------------
    # POSE
    # ------------------------------------------------------------
    def _mor_attack_curve(ap):
        """Progres mentah 0..1 -> waktu pose 0..1, MONOTON naik.

        Sama seperti kurva Gornak: yang membuat serangan 2D terasa
        mahal adalah (a) anticipation jelas, (b) HOLD di impact,
        (c) follow-through yang tidak ditarik balik. Batas segmen:
        0.35 = puncak charge, 0.9 = tangan penuh ke depan & beam mulai
        mengalir (beam live mulai di progres mentah 0.55 -> pose 0.77,
        telapak praktis sudah di muzzle).
        """
        if ap <= 0.0:
            return 0.0
        if ap < 0.45:                       # charge: menarik bahu, diperlambat
            t = ap / 0.45
            return 0.35 * (t ** 0.7)
        if ap < 0.62:                       # thrust: sangat cepat
            t = (ap - 0.45) / 0.17
            return 0.35 + 0.55 * (t ** 0.5)
        if ap < 0.80:                       # IMPACT HOLD (nyaris beku)
            t = (ap - 0.62) / 0.18
            return 0.90 + 0.06 * t
        t = (ap - 0.80) / 0.20              # release -> siap
        return 0.96 + 0.04 * (t ** 0.8)

    def _resolve_mor_pose(boss, moving=False):
        """(action, phase, ap) - dipakai rig DAN jangkar FX agar sinkron."""
        skill = getattr(boss, "active_skill", None)
        if skill == "q":
            action = "point"
        elif skill == "w":
            action = "channel"
        elif skill == "e":
            action = "erect"
        elif skill == "r":
            action = "ascend"
        elif (getattr(boss, "_mor_attack_active", False)
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
            ap = _NS_morgath._mor_attack_curve(_NS_morgath._mor_progress(boss))
        return action, phase, ap

    def _cast_hand_local(action, ap, phase):
        """Telapak tangan depan (pe cast) dalam ruang lokal."""
        bob = math.sin(phase * 0.9)
        if action == "attack":
            # idle -> tarik belakang (charge) -> muzzle (thrust/hold)
            if ap < 0.35:
                t = ap / 0.35
                a, b = (15, -7), (7, -13)
            elif ap < 0.9:
                t = (ap - 0.35) / 0.55
                a, b = (7, -13), _NS_morgath.MOR_MUZZLE
            else:
                t = 0.0
                a = b = _NS_morgath.MOR_MUZZLE
            e = t * t * (3.0 - 2.0 * t)
            return (a[0] + (b[0] - a[0]) * e, a[1] + (b[1] - a[1]) * e)
        if action == "point":                    # Q: menunjuk, summon wraith
            return (22, -26 + bob)
        if action == "channel":                  # W: kedua tangan menyalurkan
            return (15, -3 + bob)
        if action == "erect":                    # E: merentang mendirikan field
            return (20, 1.0)
        if action == "ascend":                   # R: mengangkat memanggil double
            return (11, -32)
        if action == "walk":
            return (13 + math.sin(phase * 2.0) * 2.0, -7)
        return (15, -7 + bob)                    # idle: tangan di sisi badan

    def _back_hand_local(action, ap, phase):
        bob = math.sin(phase * 0.9 + 0.6)
        if action == "attack":
            return (-17, -3)
        if action == "channel":
            return (-15, -3 + bob)
        if action == "erect":
            return (-20, 1.0)
        if action == "ascend":
            return (-12, -31)
        if action == "walk":
            return (-13 - math.sin(phase * 2.0) * 2.0, -5)
        return (-15, -5 + bob)

    def _mor_elbow(a, b, bend):
        """Sendi siku: titik tengah digeser tegak-lurus sepanjang `bend`."""
        mx, my = (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = max(1.0, math.hypot(dx, dy))
        return (mx - dy / length * bend, my + dx / length * bend)

    def _mor_shift(action, phase, ap):
        """(lean_x, root_y) - lean geser badan atas; root = napas pada
        bagian ATAS hem (hem/telapak tetap dipatok di garis tanah)."""
        bob = math.sin(phase * 0.9) * 1.3
        lean, root = 0.0, bob
        if action == "walk":
            root = -abs(math.sin(phase * 2.0)) * 1.6
            lean = math.sin(phase) * 0.8
        elif action == "attack":
            if ap < 0.35:
                lean = -2.0 * (ap / 0.35)
            elif ap < 0.9:
                lean = -2.0 + 4.5 * ((ap - 0.35) / 0.55)
            else:
                lean = 2.5
            root = 0.0
        elif action == "ascend":
            root = -3.0 - bob
        return lean, root

    def _muzzle_offset_world():
        """(dx, dy) dunia dari jangkar ke muzzle (facing=+1)."""
        k = _NS_morgath.SCALE
        return (int(round(_NS_morgath.MOR_MUZZLE[0] * k)),
                int(round(-_NS_morgath.LIFT +
                          _NS_morgath.MOR_MUZZLE[1] * k)))

    def _skill_hand_world(boss, x, y, skill):
        """Posisi telapak cast dunia untuk stance skill - anchor FX skill
        selalu menempel di tangan rig, di semua skala render."""
        action = {"q": "point", "w": "channel", "e": "erect",
                  "r": "ascend"}.get(skill, "idle")
        phase = float(getattr(boss, "pulse", 0.0))
        hx, hy = _NS_morgath._cast_hand_local(action, 0.0, phase)
        f = getattr(boss, "direction", 1) or 1
        k = _NS_morgath.SCALE
        return (int(x + hx * f * k),
                int(y - _NS_morgath.LIFT + hy * k))

    # ------------------------------------------------------------
    # POSE ROUTERS (wrapper tipis, kompatibel tool preview lama)
    # ------------------------------------------------------------
    def _draw_mor_idle(surface, boss, x, y):
        _NS_morgath._draw_mor_rig_at(
            surface, x, y, getattr(boss, "direction", 1) or 1,
            float(getattr(boss, "pulse", 0.0)), "idle", 0.0, False)

    def _draw_mor_walk(surface, boss, x, y):
        _NS_morgath._draw_mor_rig_at(
            surface, x, y, getattr(boss, "direction", 1) or 1,
            float(getattr(boss, "pulse", 0.0)) * 2.0, "walk", 0.0, False)

    def _draw_mor_attack(surface, boss, x, y):
        progress = _NS_morgath._mor_progress(boss)
        _NS_morgath._draw_mor_rig_at(
            surface, x, y, getattr(boss, "direction", 1) or 1,
            float(getattr(boss, "pulse", 0.0)), "attack",
            _NS_morgath._mor_attack_curve(progress), False)
        if not getattr(boss, "_skip_beam", False):
            _NS_morgath._draw_lightning_projectile(surface, boss, x, y,
                                                    progress)

    def _draw_mor_beam_pass(surface, boss, x, y):
        """Gambar HANYA beam pada koordinat dunia (skala 1.0).

        Dipanggil heroes/__init__.py setelah body hero di-blit ter-scale.
        Hasilnya beam berukuran & berkecerahan persis sama seperti saat
        entity ini jadi mini boss.

        Catatan: _update_mor_attack_anim dipanggil di sini (tiap frame,
        idempoten) supaya state kunci arah/target tetap terinisialisasi
        walau frame pertama serangan kena cache hit (body hero di-cache,
        renderer tidak selalu dipanggil).
        """
        _NS_morgath._update_mor_attack_anim(boss)
        _NS_morgath._draw_lightning_projectile(
            surface, boss, x, y, _NS_morgath._mor_progress(boss))

    # ============================================================
    # RIG RENDER
    # ============================================================
    def _draw_mor_rig_at(surface, x, y, facing, phase, action, ap, detail,
                         flash=0):
        """Rig -> buffer -> outline gelap 1 px -> satu blit (pola Gornak).

        Mode portrait Hero Shop meng-crop dari bbox: konten dipusatkan
        pada bbox-nya sendiri; jalur boss (1x) tidak berubah.
        """
        buf = pygame.Surface((_NS_morgath.RIG_W, _NS_morgath.RIG_H),
                             pygame.SRCALPHA)
        _NS_morgath._draw_mor_rig(buf, _NS_morgath.RIG_OX,
                                  _NS_morgath.RIG_OY, facing, phase,
                                  action, ap, detail)
        if flash > 0:
            lit = buf.copy()
            lit.fill((255, 240, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
            lit.set_alpha(flash)
            buf.blit(lit, (0, 0))
        # Pass cahaya dipasang DI SINI hanya kalau sprite ini TIDAK akan
        # dilewatkan ke heroes._finish_hd_sprite (jalur lane hero sudah
        # memberi rim+terminator - dipasang dua kali jadi dobel).
        #   * boss 1x (tanpa _render_scale)  -> pasang di sini
        #   * lane hero (_render_scale di-set) -> jangan (nanti dobel)
        #   * Hero Shop (portrait, tanpa _render_scale) -> pasang di sini
        if _lighting is not None and not _NS_morgath._MOR_LANE.v:
            _lighting.apply_to_rig(
                buf, rim_add=(30, 34, 52), shade_mul=160,
                box=_NS_morgath.GRAD_BOX if not detail else None)
        ox = int(x) - _NS_morgath.RIG_OX
        oy = int(y) - _NS_morgath.RIG_OY
        if detail:                       # portrait: pusatkan konten
            used = buf.get_bounding_rect(min_alpha=1)
            if used.width > 0:
                ox = int(x) - (used.left + used.width // 2)
                oy = int(y) - (used.top + used.height // 2)
        # Outline siluet (4 arah) - acuan keluarga masterwork.
        edge = buf.copy()
        edge.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        for ddx, ddy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            surface.blit(edge, (ox + ddx, oy + ddy))
        surface.blit(buf, (ox, oy))
        return buf

    def _draw_mor_rig(surface, cx, cy, facing, phase, action, ap=0.0,
                      detail=False):
        """Satu bone rig 2D berlapis: cape -> lengan belakang -> sepatu ->
        rok jubah -> torso -> sabuk -> pauldron belakang -> kepala ->
        lengan cast -> pauldron depan. Semua titik lewat pt()/ptg()
        supaya ukuran cukup diubah dari SATU konstanta SCALE."""
        P = _NS_morgath.PALETTE
        k = _NS_morgath.SCALE
        f = 1 if facing >= 0 else -1
        lean, root = _NS_morgath._mor_shift(action, phase, ap)

        def pt(dx, dy):
            """Bagian yang ikut napas/lean (badan atas)."""
            return (int(cx + (dx * f + lean * f) * k),
                    int(cy - _NS_morgath.LIFT + (dy + root) * k))

        def ptg(dx, dy):
            """Bagian yang DIPATOK ke tanah (hem jubah, telapak)."""
            return (int(cx + (dx * f + lean * f) * k),
                    int(cy - _NS_morgath.LIFT + dy * k))

        def _w(v):
            return max(1, int(round(v * k)))

        # ---- bagian tubuh, belakang -> depan ----
        _NS_morgath._mor_draw_cape(surface, ptg, f, phase, action)
        _NS_morgath._mor_draw_arm_back(surface, pt, _w, f, phase, action,
                                       ap)
        if action == "walk":
            _NS_morgath._mor_draw_boots(surface, ptg, f, phase)
        _NS_morgath._mor_draw_skirt(surface, ptg, _w, f, phase, action)
        _NS_morgath._mor_draw_torso(surface, pt, _w, f, phase)
        _NS_morgath._mor_draw_belt(surface, ptg, _w, f, phase, action)
        _NS_morgath._mor_draw_pauldron(surface, pt, _w, f, phase,
                                       back=True)
        _NS_morgath._mor_draw_head(surface, pt, _w, f, phase, action, ap)
        _NS_morgath._mor_draw_arm_cast(surface, pt, _w, f, phase, action,
                                       ap)
        _NS_morgath._mor_draw_pauldron(surface, pt, _w, f, phase,
                                       back=False)

    # ------------------------------------------------------------
    # BAGIAN TUBUH (ruang lokal: y=0 jangkar, + ke bawah; +x = depan)
    # ------------------------------------------------------------
    def _mor_draw_cape(surface, ptg, f, phase, action):
        """Cape mengalir di belakang badan; hem ikut garis tanah."""
        P = _NS_morgath.PALETTE
        sway = math.sin(phase * 0.8) * 2.0
        if action == "walk":
            sway += math.sin(phase * 1.5) * 2.0
        elif action == "ascend":
            sway -= 2.5                       # jubah berkibar saat naik

        def cp(dx, dy):
            # sway membesar ke arah hem (bawah), nol di bahu
            grow = max(0.0, (dy + 24.0) / 62.0)
            return ptg(dx - f * sway * grow, dy)

        # Siluet cape: dari bahu melebar ke hem belakang
        panel = [(-9, -23), (10, -23), (13, -14), (8, 6),
                 (2, 22), (-2, 34), (-6, 37), (-12, 39.5),
                 (-18, 38.5), (-23, 39.5), (-27, 38),
                 (-25, 26), (-21, 6), (-16, -10)]
        _NS_morgath._poly(surface, P["shadow_deep"],
                          [cp(x + 1, y + 1) for x, y in panel])
        _NS_morgath._poly(surface, P["robe_darkest"],
                          [cp(x, y) for x, y in panel])
        # Bidang tengah
        mid = [(-7, -22), (8, -22), (10, -12), (5, 8),
               (0, 24), (-4, 35), (-10, 37), (-16, 36),
               (-20, 30), (-17, 8), (-12, -8)]
        _NS_morgath._poly(surface, P["robe_dark"], [cp(x, y) for x, y in mid])
        # Garis lipatan (3 nada dari gelap ke tengah)
        for i, tone in enumerate(("robe_darkest", "robe_darkest", "robe_mid")):
            bx = -19 + i * 7
            pygame.draw.line(surface, P[tone], cp(bx, -6 + i * 2),
                             cp(bx - 2, 33 - i), 1)
        # Tepi depan tertangkap cahaya orb
        pygame.draw.line(surface, P["robe_light"], cp(10, -20), cp(11, -8), 1)
        pygame.draw.line(surface, P["robe_mid"], cp(11, -8), cp(7, 10), 1)

    def _mor_draw_skirt(surface, ptg, _w, f, phase, action):
        """Rok jubah A-line; hem lebar DIPATOK di FEET_DY (tidak melayang)."""
        P = _NS_morgath.PALETTE
        FE = _NS_morgath.FEET_DY
        hem_sway = math.sin(phase * 1.7) * 1.2 if action == "walk" else 0.0

        def sp(dx, dy):
            return ptg(dx + f * hem_sway * max(0.0, dy / FE), dy)

        # Siluet luar rok (pinggang -> hem bergigi/scallop)
        skirt = [(-10, -8), (10, -8), (13, 2), (17, 16),
                 (21, 28), (24, FE - 3), (22, FE),
                 (16, FE - 1), (10, FE), (4, FE - 1),
                 (-2, FE), (-8, FE - 1), (-14, FE),
                 (-20, FE - 2), (-22, FE - 5), (-18, 16), (-13, 2)]
        _NS_morgath._poly(surface, P["shadow_deep"],
                          [sp(x + 1, y + 1) for x, y in skirt])
        _NS_morgath._poly(surface, P["robe_mid"],
                          [sp(x, y) for x, y in skirt])
        # Bidang depan lebih terang (puncak jubah ke depan)
        front = [(-6, -7), (10, -7), (12, 4), (16, 18),
                 (20, FE - 4), (12, FE - 2), (6, FE - 1),
                 (0, FE - 2), (-4, FE - 1), (-2, 16), (-5, 4)]
        _NS_morgath._poly(surface, P["robe_light"],
                          [sp(x, y) for x, y in front])
        # Sisi belakang masuk bayangan
        back = [(-6, -7), (-5, 4), (-2, 16), (-4, FE - 1),
                (-12, FE - 2), (-18, FE - 4), (-14, 16), (-9, 4)]
        _NS_morgath._poly(surface, P["robe_dark"],
                          [sp(x, y) for x, y in back])
        # Lipatan vertikal meruncing ke pinggang
        for fx, tone in ((-2, "robe_mid"), (5, "robe_edge"),
                         (-9, "robe_darkest"), (12, "robe_mid")):
            pygame.draw.line(surface, P[tone], sp(fx, -4), sp(fx * 1.7, FE - 3), 1)
        # Tabard tengah: pita logam gelap + trim emas + rune arc
        tab = [(-4, -7), (4, -7), (5, 14), (3, 30), (0, 33), (-3, 30), (-5, 14)]
        _NS_morgath._poly(surface, P["armor_darkest"], [sp(x, y) for x, y in tab])
        pygame.draw.line(surface, P["gold_mid"], sp(-4, -6), sp(-5, 14), 1)
        pygame.draw.line(surface, P["gold_mid"], sp(-5, 14), sp(-3, 30), 1)
        pygame.draw.line(surface, P["gold_mid"], sp(4, -6), sp(5, 14), 1)
        pygame.draw.line(surface, P["gold_mid"], sp(5, 14), sp(3, 30), 1)
        rune = [(0, 12), (3, 16), (0, 20), (-3, 16)]
        _NS_morgath._poly(surface, P["arc_mid"], [sp(x, y) for x, y in rune])
        dot = sp(0, 16)
        pygame.draw.rect(surface, P["arc_hot"], (dot[0], dot[1], _w(1), _w(1)))
        # Pita hem emas redup + titik rune
        pygame.draw.line(surface, P["gold_dark"], sp(-19, FE - 4), sp(21, FE - 4), 1)
        for i in range(-2, 3):
            rx = i * 7
            pygame.draw.rect(surface, P["rune_mid"],
                             (sp(rx, FE - 4)[0], sp(rx, FE - 4)[1], _w(1), _w(1)))

    def _mor_draw_boots(surface, ptg, f, phase):
        """Ujung sepatu mengintip dari hem saat walk; TELAPAK DIPATOK."""
        P = _NS_morgath.PALETTE
        FE = _NS_morgath.FEET_DY
        stride = math.sin(phase * 2.0) * 3.0
        for sx, lift in ((8.0 + stride, 0.0), (-7.0 - stride, 0.0)):
            toe = [(sx - 3, FE - 4 - lift), (sx + 4, FE - 4 - lift),
                   (sx + 5, FE), (sx - 3, FE)]
            _NS_morgath._poly(surface, P["armor_dark"],
                              [ptg(x, y) for x, y in toe])
            pygame.draw.line(surface, P["armor_mid"], ptg(sx - 2, FE - 4 - lift),
                             ptg(sx + 3, FE - 4 - lift), 1)

    def _mor_draw_torso(surface, pt, _w, f, phase):
        """Cuirass dada: pelat baja-biru dengan trim emas & keystone arc."""
        P = _NS_morgath.PALETTE
        breath = math.sin(phase * 0.9) * 0.7
        bw = 1.0 + breath * 0.06

        def tp(dx, dy):
            if dy > -22:                     # lebar napas hanya di dada
                dx *= bw
            return pt(dx, dy)

        chest = [(-10, -23), (10, -23), (12, -14), (10, -5), (-10, -5), (-12, -14)]
        _NS_morgath._poly(surface, P["armor_dark"],
                          [tp(x + 1, y + 1) for x, y in chest])
        _NS_morgath._poly(surface, P["armor_mid"], [tp(x, y) for x, y in chest])
        # Pelat dada kiri-kanan (nada terang menangkap cahaya dari atas)
        _NS_morgath._poly(surface, P["armor_light"],
                          [tp(x, y) for x, y in
                           [(-9, -22), (-1, -22), (-1, -10), (-4, -12), (-8, -14)]])
        _NS_morgath._poly(surface, P["armor_light"],
                          [tp(x, y) for x, y in
                           [(1, -22), (9, -22), (8, -14), (4, -12), (1, -10)]])
        _NS_morgath._poly(surface, P["armor_shine"],
                          [tp(x, y) for x, y in
                           [(-7, -21), (-2, -21), (-2, -16), (-6, -17)]])
        _NS_morgath._poly(surface, P["armor_shine"],
                          [tp(x, y) for x, y in
                           [(2, -21), (7, -21), (6, -17), (2, -16)]])
        # Garis tengah + jahitan pelat
        pygame.draw.line(surface, P["armor_darkest"], tp(0, -22), tp(0, -6), 1)
        pygame.draw.line(surface, P["armor_darkest"], tp(-10, -13), tp(10, -13), 1)
        # Keystone arc di ulu hati (ikon faksi: sumber petir)
        key = [(0, -19), (3, -16), (0, -12), (-3, -16)]
        _NS_morgath._poly(surface, P["arc_dark"], [tp(x, y) for x, y in key])
        _NS_morgath._poly(surface, P["arc_mid"],
                          [tp(x * 0.7, y + (-16 - y) * 0.3 + 0) for x, y in key])
        hot = tp(0, -16)
        pygame.draw.rect(surface, P["arc_hot"], (hot[0], hot[1], _w(1), _w(1)))
        # Kerah gorget: pita emas gelap di leher
        collar = [(-8, -24), (8, -24), (10, -22), (-10, -22)]
        _NS_morgath._poly(surface, P["gold_dark"], [tp(x, y) for x, y in collar])
        pygame.draw.line(surface, P["gold_light"], tp(-7, -23), tp(7, -23), 1)

    def _mor_draw_belt(surface, ptg, _w, f, phase, action):
        """Sabuk pinggang + dua rumbai; menyembunyikan sambungan rok/torso."""
        P = _NS_morgath.PALETTE
        band = [(-11, -9), (11, -9), (11, -4), (-11, -4)]
        _NS_morgath._poly(surface, P["robe_darkest"],
                          [ptg(x, y) for x, y in band])
        pygame.draw.line(surface, P["gold_mid"], ptg(-11, -8), ptg(11, -8), 1)
        pygame.draw.line(surface, P["gold_dark"], ptg(-11, -4), ptg(11, -4), 1)
        # Gesper arc
        buck = [(0, -10), (3, -7), (0, -4), (-3, -7)]
        _NS_morgath._poly(surface, P["gold_mid"], [ptg(x, y) for x, y in buck])
        c = ptg(0, -7)
        pygame.draw.rect(surface, P["arc_light"], (c[0], c[1], _w(1), _w(1)))
        # Rumbai: mengayun saat walk, menggantung saat idle
        sway = math.sin(phase * 1.3) * 1.0
        if action == "walk":
            sway += math.sin(phase * 2.0) * 1.6
        for hx in (-6, 6):
            ex = hx + f * sway
            pygame.draw.line(surface, P["gold_dark"], ptg(hx, -4),
                             ptg(ex, 12), 1)
            bead = ptg(ex, 13)
            _NS_morgath._aacircle(surface, P["gold_light"], bead, _w(1.4))
            dot = ptg(ex - 0.4, 12.6)
            pygame.draw.rect(surface, P["gold_shine"], (dot[0], dot[1], 1, 1))

    def _mor_morph_shoulder_chain(shoulder, hand, bend):
        elbow = _NS_morgath._mor_elbow(shoulder, hand, bend)
        return elbow

    def _mor_draw_arm_back(surface, pt, _w, f, phase, action, ap):
        """Lengan belakang: lebih redup; menggenggam muatan cadangan."""
        P = _NS_morgath.PALETTE
        shoulder = _NS_morgath.SHOULDER_BACK
        hand = _NS_morgath._back_hand_local(action, ap, phase)
        elbow = _NS_morgath._mor_morph_shoulder_chain(shoulder, hand, -3.0)
        _NS_morgath._mor_sleeve(surface, pt, _w, f, shoulder, elbow, hand,
                                P["robe_darkest"], P["robe_dark"], dim=True)
        # Gauntlet + node redup
        hp = pt(*hand)
        _NS_morgath._aacircle(surface, P["armor_dark"], hp, _w(2.6))
        _NS_morgath._aacircle(surface, P["armor_mid"], hp, _w(1.8))
        glow = 1.0 if action == "attack" else 0.5
        _NS_morgath._aacircle(surface, P["arc_dark"], hp, _w(2.0 * glow), 1)
        if action == "attack" and ap < 0.4:
            _NS_morgath._aacircle(surface, P["arc_mid"], hp, _w(1.2), 1)

    def _mor_draw_arm_cast(surface, pt, _w, f, phase, action, ap):
        """Lengan cast depan: pose-driven; telapak = muzzle beam."""
        P = _NS_morgath.PALETTE
        shoulder = _NS_morgath.SHOULDER_FRONT
        hand = _NS_morgath._cast_hand_local(action, ap, phase)
        elbow = _NS_morgath._mor_morph_shoulder_chain(shoulder, hand, 3.5)
        _NS_morgath._mor_sleeve(surface, pt, _w, f, shoulder, elbow, hand,
                                P["robe_dark"], P["robe_mid"], dim=False)

        hp = pt(*hand)
        # Gauntlet
        _NS_morgath._aacircle(surface, P["armor_mid"], hp, _w(3.0))
        _NS_morgath._aacircle(surface, P["armor_light"], hp, _w(2.0))
        _NS_morgath._aacircle(surface, P["armor_shine"],
                              (hp[0] - _w(0.6), hp[1] - _w(0.6)), _w(0.9))

        # Node sihir di telapak: ukurannya mengikuti pose
        if action == "attack":
            charge = 1.0 if ap >= 0.9 else min(1.0, ap / 0.35)
            node_r = 2.0 + 3.0 * charge
        elif action in ("point", "channel", "ascend"):
            node_r = 3.0
        elif action == "erect":
            node_r = 2.2
        else:
            node_r = 1.6
        pulse = math.sin(phase * 4.0) * 0.5 + 0.5
        nr = node_r + pulse * 0.6
        _NS_morgath._aacircle(surface, (*P["arc_mid"], 70), hp, _w(nr + 3))
        _NS_morgath._aacircle(surface, P["arc_dark"], hp, _w(nr))
        _NS_morgath._aacircle(surface, P["arc_mid"], hp, _w(nr - 1))
        _NS_morgath._aacircle(surface, P["arc_hot"], hp, _w(max(1, nr - 2.2)))
        _NS_morgath._aacircle(surface, P["arc_shine"], hp, _w(max(1, nr - 3.4)))
        # Mini fork berdenyut saat charge penuh / stance skill
        if (action == "attack" and ap >= 0.35) or action in ("point", "ascend"):
            for i in range(3):
                ang = phase * 5.0 + i * math.pi * 2.0 / 3.0
                tip = pt(hand[0] + math.cos(ang) * 6.0,
                         hand[1] + math.sin(ang) * 6.0)
                _NS_morgath._jagged_line(surface, P["arc_hot"], hp, tip,
                                         jitter=1.5, segments=2, width=_w(1))

    def _mor_sleeve(surface, pt, _w, f, shoulder, elbow, hand,
                    base, edge, dim=False):
        """Lengan berjubah: dua segmen meruncing (atas & lengan bawah)."""
        P = _NS_morgath.PALETTE
        sh, el, hd = pt(*shoulder), pt(*elbow), pt(*hand)

        def seg(a, b, w_a, w_b, color):
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = max(1.0, math.hypot(dx, dy))
            px, py = -dy / L, dx / L
            pts = [(a[0] + px * w_a, a[1] + py * w_a),
                   (b[0] + px * w_b, b[1] + py * w_b),
                   (b[0] - px * w_b, b[1] - py * w_b),
                   (a[0] - px * w_a, a[1] - py * w_a)]
            _NS_morgath._poly(surface, color,
                              [(int(qx), int(qy)) for qx, qy in pts])

        seg(sh, el, _w(4.2), _w(3.4), base)
        seg(el, hd, _w(3.4), _w(2.8), base)
        # Garis tepi terang di sisi atas lengan
        pygame.draw.line(surface, edge, sh, hd, 1)
        # Manset emas di pergelangan
        ex, ey = el[0] + (hd[0] - el[0]) * 0.8, el[1] + (hd[1] - el[1]) * 0.8
        wx, wy = el[0] + (hd[0] - el[0]) * 0.97, el[1] + (hd[1] - el[1]) * 0.97
        pygame.draw.line(surface, P["gold_dark"], (int(ex), int(ey)),
                         (int(wx), int(wy)), _w(4.4))
        pygame.draw.line(surface, P["gold_mid"], (int(ex), int(ey)),
                         (int(wx), int(wy)), _w(2.6))

    def _mor_draw_pauldron(surface, pt, _w, f, phase, back=False):
        """Pelat bahu berlapis: sumber siluet 'penuh' ke samping."""
        P = _NS_morgath.PALETTE
        breath = math.sin(phase * 0.9) * 0.5
        if back:
            cx0, cy0 = -12.0, -24.0 + breath * 0.5
            sizes = ((6.5, 4.0), (7.5, 4.5))
            base, top, rim = P["armor_dark"], P["armor_mid"], P["armor_darkest"]
            edge = P["armor_mid"]
        else:
            cx0, cy0 = 12.0, -25.0 + breath * 0.5
            sizes = ((7.0, 4.5), (8.5, 5.0), (9.5, 5.5))
            base, top, rim = P["armor_mid"], P["armor_light"], P["armor_darkest"]
            edge = P["gold_mid"]
        for i, (rx, ry) in enumerate(sizes):
            ox = cx0 - i * 1.0
            oy = cy0 + i * 3.2
            plate = [(ox - rx, oy + ry * 0.4), (ox - rx * 0.7, oy - ry),
                     (ox + rx * 0.4, oy - ry * 0.9), (ox + rx, oy - ry * 0.2),
                     (ox + rx * 0.8, oy + ry * 0.6), (ox, oy + ry)]
            _NS_morgath._poly(surface, rim if i == 0 else rim,
                              [pt(x + 0.8, y + 0.8) for x, y in plate])
            _NS_morgath._poly(surface, base if i else rim,
                              [pt(x, y) for x, y in plate])
            _NS_morgath._poly(surface, top,
                              [pt(x, y) for x, y in
                               [(ox - rx * 0.6, oy - ry * 0.7),
                                (ox + rx * 0.2, oy - ry * 0.6),
                                (ox + rx * 0.5, oy - ry * 0.1),
                                (ox - rx * 0.4, oy - ry * 0.2)]])
            if i == len(sizes) - 1:
                pygame.draw.line(surface, edge, pt(ox - rx + 1, oy + ry * 0.5),
                                 pt(ox + rx * 0.4, oy + ry * 0.7), 1)
        # Paku arc kecil di pelat teratas
        stud = pt(cx0 + (2.0 if not back else -1.0), cy0 - 2.0)
        _NS_morgath._aacircle(surface, P["arc_light"], stud, _w(1.2))
        _NS_morgath._aacircle(surface, P["arc_shine"], stud, _w(0.6))

    def _mor_draw_head(surface, pt, _w, f, phase, action, ap):
        """Hood dalam + orb kristal (focal point PALING terang) + antena."""
        P = _NS_morgath.PALETTE
        ox, oy = _NS_morgath.ORB_CENTER
        hover = math.sin(phase * 1.3) * 0.5

        # --- Antena arc (sirip logam) dari sisi hood -----------------
        fin_f = [(5, -41), (10, -52), (13, -50), (9, -40)]
        fin_b = [(-6, -41), (-10, -50), (-8, -52), (-3, -42)]
        _NS_morgath._poly(surface, P["armor_dark"], [pt(x, y) for x, y in fin_b])
        _NS_morgath._poly(surface, P["armor_mid"], [pt(x, y) for x, y in fin_f])
        tip_f, tip_b = pt(11.5, -51), pt(-9, -51)
        pygame.draw.rect(surface, P["arc_light"],
                         (tip_f[0], tip_f[1], _w(1.4), _w(1.4)))
        pygame.draw.rect(surface, P["arc_mid"],
                         (tip_b[0], tip_b[1], _w(1.2), _w(1.2)))
        # Saat charge serangan: percikan melompat antar ujung antena -
        # tell yang bisa dibaca pemain sebelum beam keluar.
        if action == "attack" and 0.02 < ap < 0.9:
            a = _NS_morgath._alpha(min(1.0, ap / 0.3) * 230)
            _NS_morgath._jagged_line(surface, (*P["arc_hot"], a),
                                     tip_b, tip_f, jitter=2, segments=4,
                                     width=_w(1))
            _NS_morgath._jagged_line(surface, (*P["arc_light"], a),
                                     pt(-9, -50.5), pt(11.5, -49),
                                     jitter=2, segments=4, width=_w(1))

        # --- Hood luar ------------------------------------------------
        hood = [(-11, -23), (-14, -30), (-11, -38), (-5, -43),
                (0, -44), (6, -43), (11, -38), (13, -30),
                (11, -24), (6, -21), (-5, -21)]
        _NS_morgath._poly(surface, P["shadow_deep"],
                          [pt(x + 1, y + 1) for x, y in hood])
        _NS_morgath._poly(surface, P["robe_dark"], [pt(x, y) for x, y in hood])
        # Volume sisi terang (cahaya dari depan-atas)
        _NS_morgath._poly(surface, P["robe_mid"],
                          [pt(x, y) for x, y in
                           [(-3, -42), (5, -41), (10, -36), (12, -29),
                            (9, -25), (4, -38)]])
        _NS_morgath._poly(surface, P["robe_light"],
                          [pt(x, y) for x, y in
                           [(0, -43), (5, -41), (8, -37), (2, -39)]])
        # Lipatan hood
        for lx, tone in ((-8, "robe_darkest"), (-4, "robe_darkest"),
                         (8, "robe_edge")):
            pygame.draw.line(surface, P[tone], pt(lx, -37), pt(lx + f * 1, -26), 1)
        # Puncak hood menukik ke depan
        peak = [(-2, -44), (3, -45), (7, -42), (2, -43)]
        _NS_morgath._poly(surface, P["robe_mid"], [pt(x, y) for x, y in peak])

        # --- Lubang wajah: gelap pekat, jadi orb menonjol --------------
        hole = [(-6, -38), (6, -38), (8, -30), (6, -26), (-5, -27), (-7, -31)]
        _NS_morgath._poly(surface, P["shadow_deep"], [pt(x, y) for x, y in hole])
        _NS_morgath._poly(surface, P["robe_darkest"],
                          [pt(x, y) for x, y in
                           [(-6, -38), (6, -38), (7, -34), (-6, -35)]])

        # --- ORB kristal (ruang terang TERTINGGI di seluruh sprite) ----
        oc = pt(ox, oy + hover)
        orad = _NS_morgath.ORB_R
        pulse = math.sin(phase * 2.2) * 0.5 + 0.5
        # Halo lembut (murah: dua lingkaran alpha)
        _NS_morgath._aacircle(surface, (*P["orb_dark"], 46), oc, _w(orad + 5))
        _NS_morgath._aacircle(surface, (*P["orb_mid"], 60), oc, _w(orad + 2))
        # Cangkang kristal
        _NS_morgath._aacircle(surface, P["orb_dark"], oc, _w(orad))
        _NS_morgath._aacircle(surface, P["orb_mid"], oc, _w(orad - 1.5))
        # Bayangan kristal: pita gelap bawah-kanan
        low = (oc[0] + _w(1.5), oc[1] + _w(2.0))
        _NS_morgath._aacircle(surface, P["orb_darkest"], low, _w(orad - 4.5))
        _NS_morgath._aacircle(surface, P["orb_dark"], low, _w(orad - 6.0))
        # Pusaran energi: dua busur orbit (ikuti phase)
        for i in range(2):
            ang = phase * 2.4 + i * math.pi
            sx = math.cos(ang) * (orad - 3.5)
            sy = math.sin(ang) * (orad - 3.5) * 0.55
            p1 = pt(ox + sx, oy + hover + sy)
            p2 = pt(ox + sx * 0.4, oy + hover + sy * 0.4 - 1.5)
            pygame.draw.line(surface, P["orb_light"], p1, p2, _w(1.4))
        # Inti panas: denyut dengan phase
        core = (oc[0], oc[1] - _w(1.5))
        _NS_morgath._aacircle(surface, P["orb_hot"], core, _w(2.6 + pulse))
        _NS_morgath._aacircle(surface, P["orb_shine"], core, _w(1.4 + pulse * 0.5))
        # Glint kaca kiri-atas
        _NS_morgath._aacircle(surface, P["orb_shine"],
                              (oc[0] - _w(4.0), oc[1] - _w(4.5)), _w(1.3))
        # Pecahan rune mengorbit orb
        for i in range(3):
            ang = phase * 1.6 + i * (math.pi * 2.0 / 3.0)
            rx = math.cos(ang) * (orad + 4.5)
            ry = math.sin(ang) * (orad + 4.5) * 0.6
            shp = pt(ox + rx, oy + hover + ry)
            s = _w(1.2)
            _NS_morgath._poly(surface, P["arc_light"],
                              [(shp[0], shp[1] - s), (shp[0] + s, shp[1]),
                               (shp[0], shp[1] + s), (shp[0] - s, shp[1])])

        # --- Bibir hood menangkap cahaya orb ---------------------------
        pygame.draw.line(surface, P["robe_light"], pt(-5, -27), pt(6, -27), 1)
        pygame.draw.line(surface, P["robe_edge"], pt(6, -27), pt(8, -31), 1)

    # ============================================================
    # LIGHTNING PROJECTILE (basic attack)
    # ============================================================
    def _draw_lightning_projectile(surface, boss, x, y, progress):
        """Lightning bolt projectile from hand."""
        if progress < 0.55:
            return

        # ═══ KOMPENSASI SCALE HERO ═══
        # Hero dirender ke canvas lalu di-scale (heroes/__init__.py).
        # Supaya beam terlihat SAMA PERSIS seperti saat jadi mini boss
        # (tebal penuh, kepala besar, jitter & impact sama), semua
        # ukuran beam digambar 1/_render_scale kali lebih besar di
        # canvas, sehingga setelah di-scale hasilnya = ukuran asli
        # boss. Boss asli digambar langsung di layar: _render_scale=1,
        # jadi fungsi ini berperilaku persis seperti sebelumnya.
        inv = 1.0 / max(0.3, float(getattr(boss, "_render_scale", 1.0) or 1.0))

        def W(w):
            # ceil: garis 1px tetap terang setelah smoothscale
            # (round membuatnya 1px lalu blur jadi redup).
            return max(1, int(math.ceil(w * inv)))

        def _A(a):
            # Alpha dinaikkan sebesar inv: smoothscale menurunkan
            # cakupan alpha ~scale kali, jadi ini mengembalikan
            # kecerahan beam ke level asli boss setelah di-blit.
            return _NS_morgath._alpha(a * min(1.4, inv))

        def R(r):
            return max(1, int(round(r * inv)))

        # Arah & target terkunci saat serangan dimulai (lihat
        # _update_mor_attack_anim) supaya beam tidak patah arah /
        # pindah tujuan di tengah cast. Fallback ke live kalau
        # state kunci tidak ada.
        facing = getattr(boss, "_mor_attack_dir", None)
        if facing is None:
            facing = boss.direction
        if hasattr(boss, "_mor_attack_target"):
            # Offset tersimpan dalam ruang DUNIA; konversi ke ruang
            # render saat ini (canvas ter-scale atau layar skala 1.0).
            scl = float(getattr(boss, "_render_scale", 1.0) or 1.0)
            ox, oy = boss._mor_attack_target
            tx, ty = int(x + ox / scl), int(y + oy / scl)
        else:
            tx, ty = _NS_morgath._target_position(boss, x, y)

        # Lahir dari TELAPAK cast rig masterwork (MOR_MUZZLE), bukan
        # angka lepas: start beam selalu menempel di tangan yang sedang
        # thrust, di semua skala render.
        mdx, mdy = _NS_morgath._muzzle_offset_world()
        start_x = x + facing * int(round(mdx * inv))
        start_y = y + int(round(mdy * inv))

        t = (progress - 0.55) / 0.45
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Jagged lightning beam from start to bolt head
        segments = 8
        prev = (start_x, start_y)
        for i in range(1, segments + 1):
            seg_t = i / segments
            px = int(start_x + (bx - start_x) * seg_t)
            py = int(start_y + (by - start_y) * seg_t)
            if i < segments:
                # Add jitter perpendicular to path
                dx = bx - start_x
                dy = by - start_y
                length = max(1, math.hypot(dx, dy))
                perp_x = -dy / length
                perp_y = dx / length
                jitter = math.sin(seg_t * 15 + progress * 20) * (4 * inv)
                px += int(perp_x * jitter)
                py += int(perp_y * jitter)

            # Beam colors (layered)
            alpha = _A(220 * (1 - seg_t * 0.3))
            pygame.draw.line(surface, (*_NS_morgath.PALETTE["arc_darkest"], alpha),
                             prev, (px, py), W(5))
            pygame.draw.line(surface, (*_NS_morgath.PALETTE["arc_dark"], alpha),
                             prev, (px, py), W(4))
            pygame.draw.line(surface, (*_NS_morgath.PALETTE["arc_mid"], alpha),
                             prev, (px, py), W(3))
            pygame.draw.line(surface, (*_NS_morgath.PALETTE["arc_light"], alpha),
                             prev, (px, py), W(2))
            pygame.draw.line(surface, (*_NS_morgath.PALETTE["arc_hot"], alpha),
                             prev, (px, py), W(1))
            prev = (px, py)

        # Bolt head (bright ball)
        for r in range(10, 3, -1):
            alpha = _A(100 * (10 - r) / 10)
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_light"], alpha),
                                  (bx, by), R(r))
        _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_darkest"], (bx, by), R(6))
        _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_dark"], (bx, by), R(4))
        _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_light"], (bx, by), R(3))
        _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_hot"], (bx, by), R(2))
        _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_shine"], (bx, by), R(1))
        pygame.draw.rect(surface, _NS_morgath.PALETTE["white"], (bx, by, W(1), W(1)))

        # Radiating jagged forks near head
        for i in range(4):
            angle = i * math.pi / 2 + progress * 3
            fork_end_x = bx + int(math.cos(angle) * 8 * inv)
            fork_end_y = by + int(math.sin(angle) * 8 * inv)
            _NS_morgath._jagged_line(surface, _NS_morgath.PALETTE["arc_hot"],
                                     (bx, by), (fork_end_x, fork_end_y),
                                     jitter=2 * inv, segments=3, width=W(1))

        # Impact
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(10 + st * 24)
            alpha = _A(240 * (1 - st))
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_darkest"], alpha),
                                  (tx, ty), R(radius + 3), W(3))
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_dark"], alpha),
                                  (tx, ty), R(radius), W(3))
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_mid"], alpha),
                                  (tx, ty), R(max(1, radius - 5)), W(2))
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_light"], alpha),
                                  (tx, ty), R(max(1, radius - 10)), W(1))

            # Lightning tendrils outward
            for i in range(8):
                angle = i * math.pi / 4
                end_x = tx + int(math.cos(angle) * radius * inv)
                end_y = ty + int(math.sin(angle) * radius * 0.7 * inv)
                _NS_morgath._jagged_line(surface, _NS_morgath.PALETTE["arc_shine"],
                                         (tx, ty), (end_x, end_y),
                                         jitter=3 * inv, segments=4, width=W(1))
                pygame.draw.rect(surface, (*_NS_morgath.PALETTE["white"], alpha),
                                 (end_x, end_y, W(2), W(2)))

    def _draw_shadow(surface, x, y):
        # Bayangan mengikuti lebar hem rig masterwork (~46 px), bukan
        # badan lama yang lebih ramping.
        shadow = pygame.Surface((64, 16), pygame.SRCALPHA)
        for radius in range(8, 0, -1):
            alpha = max(0, (8 - radius) * 20)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (8 - radius, 8 - radius, 48 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (2, 5, 12, 190), (4, 4, 56, 8))
        surface.blit(shadow, (x - 32, y - 8))

    def _draw_arc_aura(surface, x, y, phase):
        """Blue electric aura behind boss."""
        pulse = math.sin(phase * 0.6) * 0.25 + 0.75

        aura = pygame.Surface((160, 140), pygame.SRCALPHA)
        for radius in range(70, 5, -4):
            alpha = _NS_morgath._alpha((70 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_morgath._aacircle(aura, (*_NS_morgath.PALETTE["arc_darkest"], alpha),
                                      (80, 70), radius)
        for radius in range(45, 5, -3):
            alpha = _NS_morgath._alpha((45 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_morgath._aacircle(aura, (*_NS_morgath.PALETTE["arc_dark"], alpha),
                                      (80, 70), radius)
        surface.blit(aura, (x - 80, y - 70))

        # Floating electric sparkles
        for i in range(12):
            angle = phase * 0.4 + i * math.pi / 6
            r = 32 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * r)
            sy = y - 5 + int(math.sin(angle) * r * 0.5)
            alpha = _NS_morgath._alpha(220 + math.sin(phase * 4 + i) * 35)
            pygame.draw.rect(surface, _NS_morgath.PALETTE["arc_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_morgath.PALETTE["arc_hot"], (sx, sy, 1, 1))

        # Occasional lightning arc between random sparkles
        arc_frame = int(phase * 3) % 8
        if arc_frame < 2:
            for k in range(2):
                a1 = phase * 0.4 + k * math.pi / 6
                a2 = phase * 0.4 + (k + 3) * math.pi / 6
                r = 32
                p1 = (x + int(math.cos(a1) * r),
                      y - 5 + int(math.sin(a1) * r * 0.5))
                p2 = (x + int(math.cos(a2) * r),
                      y - 5 + int(math.sin(a2) * r * 0.5))
                _NS_morgath._jagged_line(surface, _NS_morgath.PALETTE["arc_light"],
                                         p1, p2, jitter=3, segments=5, width=1)

    def _draw_ground_rune(surface, x, y, phase, skill):
        """Blue magic rune circle - rapat di bawah hem jubah.

        Pelajaran dari konvensi masterwork Gornak: rune tidak boleh
        lebih lebar/lebih terang dari badan (versi lama 130 px), jadi
        dikunci ~64 px dengan spoke redup.
        """
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((68, 24), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_morgath.PALETTE["arc_darkest"], 190),
                            (3, 8, 62, 12), 2)
        pygame.draw.ellipse(ring, (*_NS_morgath.PALETTE["arc_dark"], 200),
                            (8, 10, 52, 8), 1)
        pygame.draw.ellipse(ring, (*_NS_morgath.PALETTE["arc_mid"], 150),
                            (16, 11, 36, 6), 1)

        # Rune spokes (pendek, di dalam cincin)
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 34 + int(math.cos(angle) * 17)
            y1 = 14 + int(math.sin(angle) * 4)
            x2 = 34 + int(math.cos(angle) * 28)
            y2 = 14 + int(math.sin(angle) * 6)
            pygame.draw.line(ring, (*_NS_morgath.PALETTE["arc_dark"], 190),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_morgath.PALETTE["arc_hot"],
                                       _NS_morgath._alpha(150 * pulse)),
                                (5, 5, 58, 16), 1)
        surface.blit(ring, (x - 34, y - 12))

    # ============================================================
    # SKILL Q: SPARK WRAITH (homing electric orb)
    # ============================================================
    def _draw_sparkwraith_ground(surface, boss, x, y, timer, phase):
        """Launch rune."""
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.25:
            t = progress / 0.25
            r = int(22 * t)
            alpha = _NS_morgath._alpha(200 * t)
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_mid"], alpha),
                                  (x, y + 40), r, 2)
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_light"], alpha),
                                  (x, y + 40), max(1, r - 3), 1)

    def _draw_sparkwraith_foreground(surface, boss, x, y, timer, phase):
        """Sparking electric orb that flies to target."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_morgath._target_position(boss, x, y)

        if progress < 0.3:
            # Charge di telapak cast (stance point) - menempel di rig
            t = progress / 0.3
            charge_x, charge_y = _NS_morgath._skill_hand_world(
                boss, x, y, "q")
            cr = int(5 + t * 8)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_morgath._alpha(220 * (cr + 5 - r) / (cr + 5))
                _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_darkest"], alpha),
                                      (charge_x, charge_y), r)
            for r in range(cr + 2, 0, -1):
                alpha = _NS_morgath._alpha(240 * (cr + 2 - r) / (cr + 2))
                _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_dark"], alpha),
                                      (charge_x, charge_y), r)
            _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_mid"],
                                  (charge_x, charge_y), cr - 2)
            _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_light"],
                                  (charge_x, charge_y), max(1, cr - 4))
            _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_shine"],
                                  (charge_x, charge_y), max(1, cr - 6))

            # Sparks
            for i in range(6):
                angle = phase * 5 + i * math.pi / 3
                sx = charge_x + int(math.cos(angle) * (cr + 3))
                sy = charge_y + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface, _NS_morgath.PALETTE["arc_hot"], (sx, sy, 1, 1))

            # Jagged arcs from orb
            for i in range(3):
                ea_x = charge_x + int(math.cos(phase * 6 + i) * (cr + 5))
                ea_y = charge_y + int(math.sin(phase * 6 + i) * (cr + 5))
                _NS_morgath._jagged_line(surface, _NS_morgath.PALETTE["arc_light"],
                                         (charge_x, charge_y), (ea_x, ea_y),
                                         jitter=2, segments=3, width=1)
        else:
            # Orb travels toward target (curved wraith) dari telapak rig
            t = (progress - 0.3) / 0.7
            start_x, start_y = _NS_morgath._skill_hand_world(
                boss, x, y, "q")

            # Slight arc trajectory
            mid_x = (start_x + tx) / 2
            mid_y = min(start_y, ty) - 30
            bx = int((1 - t) ** 2 * start_x + 2 * (1 - t) * t * mid_x + t ** 2 * tx)
            by = int((1 - t) ** 2 * start_y + 2 * (1 - t) * t * mid_y + t ** 2 * ty)

            # Trail behind
            for i in range(8):
                trail_t = max(0.0, t - i * 0.06)
                px = int((1 - trail_t) ** 2 * start_x + 2 * (1 - trail_t) * trail_t * mid_x
                         + trail_t ** 2 * tx)
                py = int((1 - trail_t) ** 2 * start_y + 2 * (1 - trail_t) * trail_t * mid_y
                         + trail_t ** 2 * ty)
                alpha = _NS_morgath._alpha(240 - i * 28)
                size = max(1, 8 - i)
                _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_darkest"], alpha),
                                      (px, py), size)
                _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_dark"], alpha),
                                      (px, py), max(1, size - 1))
                _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_mid"], alpha),
                                      (px, py), max(1, size - 2))
                _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_light"], alpha),
                                      (px, py), max(1, size - 3))

            # Bright orb head with electric aura
            for r in range(14, 4, -2):
                alpha = _NS_morgath._alpha(90 * (14 - r) / 14)
                _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_light"], alpha),
                                      (bx, by), r)
            _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_darkest"], (bx, by), 11)
            _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_dark"], (bx, by), 9)
            _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_mid"], (bx, by), 6)
            _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_light"], (bx, by), 4)
            _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_shine"], (bx, by), 2)
            pygame.draw.rect(surface, _NS_morgath.PALETTE["white"], (bx, by, 1, 1))

            # Electric tendrils around orb
            for i in range(5):
                angle = phase * 6 + i * math.pi * 2 / 5
                tend_end_x = bx + int(math.cos(angle) * 10)
                tend_end_y = by + int(math.sin(angle) * 10)
                _NS_morgath._jagged_line(surface, _NS_morgath.PALETTE["arc_hot"],
                                         (bx, by), (tend_end_x, tend_end_y),
                                         jitter=3, segments=3, width=1)

            # Impact
            if t > 0.88:
                st = (t - 0.88) / 0.12
                radius = int(14 + st * 30)
                alpha = _NS_morgath._alpha(240 * (1 - st))
                _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_darkest"], alpha),
                                      (tx, ty), radius + 4, 3)
                _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_dark"], alpha),
                                      (tx, ty), radius, 3)
                _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_light"], alpha),
                                      (tx, ty), max(1, radius - 8), 2)

                for i in range(10):
                    angle_s = i * math.pi / 5
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    _NS_morgath._jagged_line(surface, _NS_morgath.PALETTE["arc_shine"],
                                             (tx, ty), (ex, ey),
                                             jitter=3, segments=4, width=1)

    # ============================================================
    # SKILL W: FLUX (purple debuff aura on target)
    # ============================================================
    def _draw_flux_ground(surface, boss, x, y, timer, phase):
        """Purple pool at target."""
        tx, ty = _NS_morgath._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(38 * min(1.0, progress * 3))
        if r > 3:
            # PERTAGAS: rim panas luar + alpha pool dinaikkan
            pygame.draw.ellipse(surface, (*_NS_morgath.PALETTE["flux_hot"], 120),
                                (tx - r - 3, ty - (r + 3) // 3,
                                 (r + 3) * 2, (r + 3) * 2 // 3), 2)
            pygame.draw.ellipse(surface, (*_NS_morgath.PALETTE["flux_darkest"], 240),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_morgath.PALETTE["flux_dark"], 220),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_morgath.PALETTE["flux_mid"], 180),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))

    def _draw_flux_foreground(surface, boss, x, y, timer, phase):
        """Rising purple energy tendrils around target."""
        tx, ty = _NS_morgath._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(38 * min(1.0, progress * 3))

        if r < 5:
            return

        # Rising purple tendrils/wisps
        for i in range(8):
            wisp_t = (phase * 0.7 + i * 0.15) % 1.0
            angle = i * math.pi / 4 + phase * 0.3
            wx = tx + int(math.cos(angle) * r * 0.6)
            wy_base = ty + int(math.sin(angle) * r * 0.3)
            wy = wy_base - int(wisp_t * 30)
            alpha = _NS_morgath._alpha(230 * (1 - wisp_t))

            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["flux_dark"], alpha),
                                  (wx, wy), 5)
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["flux_mid"], alpha),
                                  (wx, wy - 1), 4)
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["flux_light"], alpha),
                                  (wx, wy - 1), 2)
            pygame.draw.rect(surface, (*_NS_morgath.PALETTE["flux_hot"], alpha),
                             (wx, wy - 1, 1, 1))

        # Central bubbling core
        core_pulse = math.sin(phase * 3) * 0.4 + 0.6
        for cr in range(8, 0, -1):
            alpha = _NS_morgath._alpha(220 * (8 - cr) / 8 * core_pulse)
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["flux_mid"], alpha),
                                  (tx, ty), cr)
        _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["flux_light"], (tx, ty), 3)
        _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["flux_hot"], (tx, ty), 1)

        # Sparkles on ground
        for i in range(14):
            angle = i * math.pi * 2 / 14 + phase * 0.4
            sp_r = int(r * (0.5 + (i % 3) * 0.2))
            sx = tx + int(math.cos(angle) * sp_r)
            sy = ty + int(math.sin(angle) * sp_r * 0.4)
            pygame.draw.rect(surface, _NS_morgath.PALETTE["flux_light"], (sx, sy, 1, 1))
            pygame.draw.rect(surface, _NS_morgath.PALETTE["flux_hot"], (sx, sy, 1, 1))

    # ============================================================
    # SKILL E: MAGNETIC FIELD (dome shield)
    # ============================================================
    def _draw_magneticfield_ground(surface, boss, x, y, timer, phase):
        """Ground ring under dome."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for i in range(3):
            r = int(48 + i * 4 + math.sin(phase * 2) * 2)
            alpha = _NS_morgath._alpha(250 * pulse - i * 40)
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_mid"], alpha),
                                  (x, y + 42), r, 2)
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_light"], alpha),
                                  (x, y + 42), r, 1)

    def _draw_magneticfield_foreground(surface, boss, x, y, timer, phase):
        """Big blue dome shield over boss."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Dome dimensions
        breath = math.sin(phase * 2) * 2
        r = 52 + int(breath)

        # Draw dome (semi-circle top-half)
        dome_surf = pygame.Surface((r * 2 + 30, r + 30), pygame.SRCALPHA)
        center = (r + 15, r + 15)

        # Multi-ring dome
        for layer_i, (thickness, alpha_val) in enumerate([
            (4, 100), (3, 140), (2, 190), (1, 240),
        ]):
            # Draw arc (top half)
            arc_rect = pygame.Rect(center[0] - r + layer_i, center[1] - r + layer_i,
                                   (r - layer_i) * 2, (r - layer_i) * 2)
            pygame.draw.arc(dome_surf, (*_NS_morgath.PALETTE["arc_dark"], alpha_val),
                            arc_rect, 0, math.pi, thickness)
            pygame.draw.arc(dome_surf, (*_NS_morgath.PALETTE["arc_mid"], alpha_val),
                            arc_rect, 0, math.pi, max(1, thickness - 1))
            pygame.draw.arc(dome_surf, (*_NS_morgath.PALETTE["arc_light"], alpha_val),
                            arc_rect, 0, math.pi, max(1, thickness - 2))

        # Hex/grid pattern inside dome
        for h_row in range(4):
            for h_col in range(-3, 4):
                grid_x = center[0] + h_col * 12 + (h_row % 2) * 6
                grid_y = center[1] - h_row * 10
                dist_from_center = math.hypot(grid_x - center[0], grid_y - center[1])
                if dist_from_center < r - 5:
                    alpha = _NS_morgath._alpha(180 * (1 - dist_from_center / r))
                    pygame.draw.rect(dome_surf,
                                     (*_NS_morgath.PALETTE["arc_mid"], alpha),
                                     (grid_x - 1, grid_y - 1, 3, 3), 1)

        # Rotating electric arcs on dome surface
        for i in range(6):
            angle = phase * 1.5 + i * math.pi / 3
            arc_angle = math.pi + angle  # constrain to top half
            arc_angle = math.pi * (0.1 + (i / 6) * 0.8)
            ax = center[0] + int(math.cos(math.pi + arc_angle) * r)
            ay = center[1] + int(math.sin(math.pi + arc_angle) * r)
            pygame.draw.rect(dome_surf, (*_NS_morgath.PALETTE["arc_hot"], 240),
                             (ax, ay, 2, 2))
            pygame.draw.rect(dome_surf, (*_NS_morgath.PALETTE["arc_shine"], 255),
                             (ax, ay, 1, 1))

        surface.blit(dome_surf, (x - r - 15, y - r - 15 + 10))

        # Random lightning arcs across dome interior
        arc_frame = int(phase * 4) % 5
        if arc_frame < 2:
            for k in range(2):
                a1 = phase * 2 + k * 1.7
                a2 = phase * 2 + k * 1.7 + 1.5
                arc_angle1 = math.pi * (0.15 + ((math.sin(a1) + 1) / 2) * 0.7)
                arc_angle2 = math.pi * (0.15 + ((math.sin(a2) + 1) / 2) * 0.7)
                p1 = (x + int(math.cos(math.pi + arc_angle1) * r),
                      y + 10 + int(math.sin(math.pi + arc_angle1) * r))
                p2 = (x + int(math.cos(math.pi + arc_angle2) * r),
                      y + 10 + int(math.sin(math.pi + arc_angle2) * r))
                _NS_morgath._jagged_line(surface, _NS_morgath.PALETTE["arc_hot"],
                                         p1, p2, jitter=4, segments=6, width=1)

    # ============================================================
    # SKILL R: TEMPEST DOUBLE (spawn clone + lightning)
    # ============================================================
    def _draw_tempest_ground(surface, boss, x, y, timer, phase):
        """Twin rune circles."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction

        # Original boss ring
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        r = int(25 + math.sin(phase * 2) * 2)
        for i in range(2):
            alpha = _NS_morgath._alpha(240 * pulse - i * 50)
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["flux_mid"], alpha),
                                  (x, y + 42), r + i * 2, 2)

        # Clone spawn ring (offset)
        if progress > 0.2:
            clone_offset = -facing * 40
            clone_alpha_mult = min(1.0, (progress - 0.2) / 0.2)
            for i in range(2):
                alpha = _NS_morgath._alpha(240 * pulse * clone_alpha_mult - i * 50)
                _NS_morgath._aacircle(surface,
                                      (*_NS_morgath.PALETTE["flux_mid"], alpha),
                                      (x + clone_offset, y + 42), r + i * 2, 2)

    def _draw_tempest_clone(surface, boss, x, y, timer, phase):
        """Ghostly duplicate of boss."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction

        if progress < 0.2:
            return

        # Clone spawn animation
        spawn_t = min(1.0, (progress - 0.2) / 0.3)
        alpha_val = int(220 * spawn_t)

        clone_offset = -facing * 40
        clone_x = x + clone_offset

        # Draw clone body (rig masterwork, pose idle) ke buffer rig
        clone_surf = pygame.Surface((_NS_morgath.RIG_W, _NS_morgath.RIG_H),
                                    pygame.SRCALPHA)
        _NS_morgath._draw_mor_rig(clone_surf, _NS_morgath.RIG_OX,
                                  _NS_morgath.RIG_OY, facing, phase,
                                  "idle", 0.0, False)

        # Tint clone slightly blue (alpha 255 supaya RGBA_MULT tidak
        # menggerus alpha badan - dulu clone nyaris transparan)
        tint = pygame.Surface((_NS_morgath.RIG_W, _NS_morgath.RIG_H),
                              pygame.SRCALPHA)
        tint.fill((110, 150, 235, 255))
        clone_surf.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        clone_surf.set_alpha(alpha_val)

        surface.blit(clone_surf, (clone_x - _NS_morgath.RIG_OX,
                                  y - _NS_morgath.RIG_OY))

        # Electric arcs between clone and original
        arc_frame = int(phase * 6) % 4
        if arc_frame < 2:
            _NS_morgath._jagged_line(surface, _NS_morgath.PALETTE["arc_hot"],
                                     (x, y - 10), (clone_x, y - 10),
                                     jitter=6, segments=8, width=2)
            _NS_morgath._jagged_line(surface, _NS_morgath.PALETTE["arc_shine"],
                                     (x, y - 10), (clone_x, y - 10),
                                     jitter=5, segments=8, width=1)

    def _draw_tempest_foreground(surface, boss, x, y, timer, phase):
        """Lightning storm burst FX."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction

        if progress < 0.2:
            # Charge phase - purple ground swirl
            t = progress / 0.2
            for arm in range(3):
                for step in range(15):
                    s_t = step / 15
                    spiral_angle = phase * 3 + arm * math.pi * 2 / 3 + s_t * math.pi * 3
                    s_r = int(30 * (1 - s_t) * t)
                    sx = x + int(math.cos(spiral_angle) * s_r)
                    sy = y + 30 + int(math.sin(spiral_angle) * s_r * 0.4)
                    alpha = _NS_morgath._alpha(200 * (1 - s_t) * t)
                    pygame.draw.rect(surface,
                                     (*_NS_morgath.PALETTE["flux_light"], alpha),
                                     (sx, sy, 2, 2))
                    pygame.draw.rect(surface,
                                     (*_NS_morgath.PALETTE["flux_hot"], alpha),
                                     (sx, sy, 1, 1))

        elif progress < 0.5:
            # Burst
            t = (progress - 0.2) / 0.3
            intensity = math.sin(t * math.pi)
            burst_r = int(30 + t * 40)

            # Radial lightning bolts from boss
            for i in range(12):
                angle = i * math.pi / 6 + phase * 0.5
                end_x = x + int(math.cos(angle) * burst_r)
                end_y = y - 10 + int(math.sin(angle) * burst_r * 0.8)
                alpha = _NS_morgath._alpha(240 * intensity)
                _NS_morgath._jagged_line(surface,
                                         _NS_morgath.PALETTE["arc_darkest"],
                                         (x, y - 10), (end_x, end_y),
                                         jitter=4, segments=6, width=4)
                _NS_morgath._jagged_line(surface,
                                         _NS_morgath.PALETTE["arc_mid"],
                                         (x, y - 10), (end_x, end_y),
                                         jitter=4, segments=6, width=2)
                _NS_morgath._jagged_line(surface,
                                         _NS_morgath.PALETTE["arc_shine"],
                                         (x, y - 10), (end_x, end_y),
                                         jitter=3, segments=6, width=1)
                pygame.draw.rect(surface, (*_NS_morgath.PALETTE["white"], alpha),
                                 (end_x, end_y, 2, 2))

            # Bright core flash
            for r in range(15, 0, -1):
                alpha = _NS_morgath._alpha(220 * intensity * (15 - r) / 15)
                _NS_morgath._aacircle(surface,
                                      (*_NS_morgath.PALETTE["arc_light"], alpha),
                                      (x, y - 10), r)
        else:
            # Aftermath - lingering sparks
            t = (progress - 0.5) / 0.5
            for i in range(16):
                rise_t = (phase * 0.7 + i * 0.06) % 1.0
                angle = i * math.pi * 2 / 16 + phase * 0.3
                r_sp = 35 + int(math.sin(phase + i) * 8)
                rx = x + int(math.cos(angle) * r_sp)
                ry = y + 10 + int(math.sin(angle) * r_sp * 0.4) - int(rise_t * 20)
                alpha = _NS_morgath._alpha(220 * (1 - t) * (1 - rise_t * 0.5))
                if alpha > 0:
                    pygame.draw.rect(surface,
                                     (*_NS_morgath.PALETTE["arc_light"], alpha),
                                     (rx, ry, 2, 2))
                    pygame.draw.rect(surface,
                                     (*_NS_morgath.PALETTE["arc_shine"], alpha),
                                     (rx, ry, 1, 1))

            # Occasional lingering arcs
            arc_frame = int(phase * 4) % 6
            if arc_frame < 2:
                clone_offset = -facing * 40
                _NS_morgath._jagged_line(surface, _NS_morgath.PALETTE["arc_hot"],
                                         (x, y - 10),
                                         (x + clone_offset, y - 10),
                                         jitter=5, segments=6, width=1)

# ====================================================================


def draw_morgath_v1(surface, boss, x, y):
    """Entry point v1 (untuk before/after)."""
    return _NS_morgath.draw_morgath(surface, boss, x, y)
