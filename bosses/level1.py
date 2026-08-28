"""
bosses/level1.py - Semua boss Level 1

Gabungan dari 4 file terpisah:
  - gornak               (mini boss)
  - morgath              (mini boss)
  - drakar               (mini boss)
  - abaddon              (TRUE BOSS)

Tiap boss dibungkus dalam kelas namespace `_NS_<nama>`
supaya PALETTE dan fungsi helper-nya TIDAK saling
menimpa - 91 simbol bentrok antar file boss, termasuk
PALETTE, _aacircle, _draw_shadow, _target_position.

Kode di dalam tiap namespace aslinya TIDAK diubah isinya; hanya
referensi antar-simbol yang diberi prefix.

KECUALI gornak dan drakar: kedua namespace-nya sudah dibangun ulang
sebagai "Procedural Masterwork" (satu bone rig 2D berlapis + outline
siluet + LOD portrait, senjata pose-driven). Regresi gornak:
tools/test_gornak_masterwork.py, drakar: tools/test_drakar_masterwork.py;
sheet review masing-masing: tools/_shot_*_masterwork.py.

Entry point publik ada di bagian paling bawah file.
"""

import math
import random
import pygame

# Penanda: file ini berisi BANYAK boss (1 true + 3 mini).
# Dipakai heroes/__init__.py agar tidak menebak fungsi draw_*
# secara longgar, yang bisa mengembalikan boss yang salah.
_IS_LEVEL_BUNDLE = True

# ====================================================================
# GORNAK (ANTI-MAGE) - Mini Boss  ·  PROCEDURAL MASTERWORK RIG
# ====================================================================
import math
import pygame

try:                     # pass cahaya bersama; opsional supaya file boss
    import lighting as _lighting          # tetap bisa di-load sendiri
except Exception:        # pragma: no cover
    _lighting = None


class _NS_gornak:
    """Namespace gornak - Anti-Mage mini boss.

    Renderer 100% prosedural (tanpa PNG, sprite sheet, atau image.load),
    dibangun ulang mengikuti standar "Procedural Masterwork" yang sudah
    dipakai Kaizen / Thorne / Sylara / Zephyr / Grimjaw / Vex:

    * SATU bone rig 2D berlapis - bukan kumpulan body-part statis. Sendi
      (pinggul, lutut, mata kaki, bahu, siku, pergelangan) dihitung tiap
      frame dari ``phase``/``action``, sehingga siluet tidak pernah pecah
      saat berjalan atau memukul. Telapak kaki DIPATOK ke garis tanah
      (``GROUND_DY``) sementara badan bernapas/bob - karakter berdiri,
      bukan melayang.
    * Twin blade pose-driven: arah bilah diturunkan dari garis lengan
      (siku -> pergelangan) + tilt per-pose, jadi bilah selalu menempel
      di tangan. Ujung bilah adalah satu-satunya sumber posisi untuk
      slash arc, proc Mana Break, dan kilau Counterspell.
    * Siluet dirender ke buffer lalu diberi outline gelap 1 px, sehingga
      tiap bagian tetap terpisah saat unit bertumpuk di lane.
    * LOD dua tingkat: arena memakai siluet bersih & hemat; portrait Hero
      Shop (``_portrait_hd``) menambah pass material (serat rambut, grain
      kulit, jahitan, ukiran baja, garis hamon bilah, tato rune) dan
      membuang aura/platform supaya auto-crop terisi wajah, bukan
      lingkaran efek.
    * Efek skill ditundukan pada karakter: rune tanah cuma lingkaran kecil
      di bawah kaki, Counterspell berupa kubah heksagon yang memeluk badan,
      Blink memakai after-image rig yang sama.
    """

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    # ── SKALA BADAN ───────────────────────────────────────────────
    # Rujuran keluarga (diukur dari render, alpha>=100):
    #   boss 1x : morgath H82/W120, drakar H138/W190, abaddon H122/W150
    #   hero    : kaizen 75x83, grimjaw 74x79, vex 75x83, sylara 77x90
    # Renderer lama hanya 87x53 (W/H 0.61) -> terlihat seperti tiang kecil
    # di samping boss/hero lain. SCALE memperbesar rig, LIFT memindahkan
    # jangkar ke bawah (kepala lebih tinggi di atas titik (x,y)) supaya
    # pipeline HD hero menormalkan tingginya SAMA seperti hero lain, dan
    # stance/blade spread membuat rasio W/H masuk ~1.0 seperti sepupunya.
    SCALE = 1.32
    # Jangkar boss = pusat hitbox; LIFT memindahkan badan ke bawah supaya
    # wajah tidak tertutup HP bar boss (digambar di y-r-15..y-r-7) TAPI
    # tinggi di atas jangkar tetap besar - itu yang dipakai pipeline HD hero
    # untuk menormalkan ukuran, jadi hero Gornak tetap setinggi Kaizen/
    # Grimjaw (75-77 px) alih-alih membesar 2x.
    LIFT = 4
    # Telapak dalam RUANG LOKAL; garis tanah dunia diturunkan dari sini
    # supaya bayangan, rune tanah, dan telapak tidak pernah saling lepas.
    FEET_DY = 44
    GROUND_DY = int(round(FEET_DY * SCALE)) - LIFT        # ~ 46

    # Buffer rig: dibatasi dari extents TERUKUR semua pose (idle/walk/
    # attack/surge/ward/void/blink, dua LOD): anchor -> left -66, top -88,
    # right +96, bottom +58, + margin 4 px. Buffer sekecil mungkin karena
    # outline siluet meng-copy-nya 5x per frame.
    RIG_W, RIG_H = 176, 160
    RIG_OX, RIG_OY = 74, 96

    # Bidang acuan untuk pass cahaya (lighting.py): kotak TETAP di dalam
    # buffer rig, bukan bbox hasil render per frame. Alasannya dua: (a) kalau
    # acuan ikut bbox, arah cahaya bergeser tiap ganti pose dan terbaca
    # sebagai lampu berkedip; (b) bbox yang berubah-buat membuat cache
    # ukuran gradien miss tiap frame (+1,5 ms, terukur).
    GRAD_BOX = (RIG_OX - 54, RIG_OY - 52, 126, 102)

    # Durasi status skill (frame) - HARUS sama dengan active_skill_timer yang
    # diisi AI boss (bosses/base_boss.py) dan skill hero
    # (hero_skills/_bundle.py). Kalau konstanta ini lebih kecil, pose skill
    # "menggantung" di frame terakhir; kalau lebih besar, animasinya
    # terpotong di tengah. Dikunci oleh tools/test_gornak_masterwork.py.
    SKILL_DUR = {"q": 40, "w": 25, "e": 60, "r": 90}

    # Penanda "sedang di-render ke canvas hero" (lane). Dipasang per-frame
    # oleh draw_gornak, dipakai _draw_gnk_rig_at untuk memutuskan siapa yang
    # mengerjakan pass cahaya - hindari rim dobel di lane dan rim nol di shop.
    class _HERO_LANE:
        v = False

    PALETTE = {
        # Kulit sawo matang berdebu (cahaya dari depan-atas)
        "skin_darkest": (34, 17, 11),
        "skin_dark": (84, 44, 25),
        "skin_mid": (154, 94, 52),
        "skin_light": (205, 148, 96),
        "skin_shine": (240, 192, 142),
        "skin_high": (252, 222, 182),

        # Mohawk (ungu sihir)
        "hair_darkest": (24, 8, 38),
        "hair_dark": (52, 18, 84),
        "hair_mid": (106, 45, 158),
        "hair_light": (160, 98, 214),
        "hair_shine": (216, 172, 252),

        # Jenggot & alis
        "beard_darkest": (22, 12, 12),
        "beard_dark": (44, 25, 22),
        "beard_mid": (72, 43, 34),

        # Kain jubah / loincloth
        "robe_darkest": (12, 7, 21),
        "robe_dark": (32, 19, 52),
        "robe_mid": (60, 38, 92),
        "robe_light": (98, 66, 140),
        "robe_edge": (152, 116, 194),

        # Baja "spellbreaker"
        "armor_darkest": (7, 6, 12),
        "armor_dark": (24, 22, 34),
        "armor_mid": (74, 70, 96),
        "armor_light": (138, 132, 164),
        "armor_shine": (206, 202, 232),

        # Bilah silver-biru + garis temper
        # Bilah sengaja DITURUNKAN satu tingkat dari nilai tertinggi:
        # selama blade_shine = 246, mata (yang harusnya focal point) kalah
        # terangi senjatanya sendiri, dan pandangan jatuh ke pedang.
        # Hierarki nilai yang benar: mata > krist > pelat > bilah.
        "blade_dark": (34, 32, 50),
        "blade_mid": (98, 102, 130),
        "blade_light": (166, 172, 198),
        "blade_shine": (214, 220, 244),
        "blade_hamon": (168, 196, 236),

        # Kulit tan & kuningan paku
        "leather_dark": (48, 29, 18),
        "leather_mid": (88, 55, 33),
        "leather_light": (132, 89, 54),
        "brass_dark": (96, 68, 24),
        "brass_mid": (170, 130, 50),
        "brass_light": (228, 200, 114),

        # Aura anti-sihir (FX utama)
        "magic_darkest": (25, 5, 45),
        "magic_dark": (60, 20, 110),
        "magic_mid": (130, 55, 200),
        "magic_light": (185, 110, 240),
        "magic_hot": (220, 160, 255),
        "magic_shine": (245, 210, 255),

        # Mata menyala
        "eye_dark": (58, 18, 78),
        "eye_mid": (180, 90, 220),
        "eye_light": (240, 180, 255),
        "eye_glow": (255, 235, 255),

        "shadow": (0, 0, 0),
        "shadow_deep": (4, 2, 8),
        "white": (255, 255, 255),
    }

    # ==================================================================
    # PRIMITIF HELPER (mendukung warna alpha lewat surface sementara)
    # ==================================================================
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_gornak._clamp(color)
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
        if _NS_gornak.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius,
                                     width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_gornak._clamp(color)
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
        if _NS_gornak.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color[:3], (sx, sy), (ex, ey))
                return
            except Exception:
                pass
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), width)

    def _poly(surface, color, points):
        if not points or len(points) < 3:
            return
        color = _NS_gornak._clamp(color)
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

    def _ellipse(surface, color, rect, width=0):
        color = _NS_gornak._clamp(color)
        rx, ry, rw, rh = int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3])
        if rw <= 0 or rh <= 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, rw, rh), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3], (rx, ry, rw, rh), width)

    def _rect(surface, color, rect):
        color = _NS_gornak._clamp(color)
        rx, ry, rw, rh = int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3])
        if rw <= 0 or rh <= 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, rw, rh))
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3], (rx, ry, rw, rh))

    # ==================================================================
    # KOORDINAT TARGET (kompensasi scale untuk jalur hero offscreen)
    # ==================================================================
    def _target_position(boss, x, y):
        """Posisi target dalam ruang jangkar (x, y) renderer ini."""
        target = getattr(boss, "target", None)
        scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
        if target is not None and getattr(target, "alive", True):
            # Hero di-render ke canvas offscreen lalu di-scale saat blit
            # (heroes/__init__.py), jadi titik canvas harus
            # = (delta dunia)/scale supaya proyektil mendarat TEPAT di
            # target setelah blit. Boss digambar langsung di layar
            # (scale = 1) jadi tidak terpengaruh.
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        return (int(x + 120.0 / scale * getattr(boss, "direction", 1)),
                int(y))

    # ==================================================================
    # STATE ANIMASI
    # ==================================================================
    def _update_gnk_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 38)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_gnk_previous_timer", 0))
        active = bool(getattr(boss, "_gnk_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._gnk_attack_active = True
            boss._gnk_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._gnk_attack_frame = int(getattr(boss, "_gnk_attack_frame",
                                                  0)) + 1
        elif timer <= 0:
            boss._gnk_attack_active = False
            boss._gnk_attack_frame = 0
            active = False

        boss._gnk_previous_timer = timer
        boss._gnk_attack_progress = (
            min(1.0, boss._gnk_attack_frame / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        cur_x = float(getattr(boss, "x", 0.0))
        cur_y = float(getattr(boss, "y", 0.0))
        if not hasattr(boss, "_gnk_last_x"):
            boss._gnk_last_x = cur_x
            boss._gnk_last_y = cur_y
            return False
        moved = abs(cur_x - boss._gnk_last_x) + abs(cur_y - boss._gnk_last_y)
        boss._gnk_last_x = cur_x
        boss._gnk_last_y = cur_y
        return moved > 0.3

    # ==================================================================
    # POSE STATE - satu sumber kebenaran untuk rig DAN semua FX
    # ==================================================================
    ACTIONS = ("idle", "walk", "attack", "surge", "ward", "void")

    def _resolve_pose(boss, moving=False):
        """(action, phase, ap) - dipakai rig DAN anchor FX agar sinkron.

        Murni/tanpa efek samping: boleh dipanggil ulang oleh fungsi efek.
        """
        active_skill = getattr(boss, "active_skill", None)
        if active_skill == "e":
            action = "ward"
        elif active_skill == "r":
            action = "void"
        elif active_skill == "q":
            action = "surge"
        elif active_skill == "w":
            action = "blink"
        elif (getattr(boss, "_gnk_attack_active", False)
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
            raw = max(0.0, min(1.0, float(getattr(boss, "_gnk_attack_progress",
                                                  0.0))))
            # anticipation / impact hold / rebound - lihat _attack_curve
            ap = _NS_gornak._attack_curve(raw)
            boss._gnk_attack_raw = raw
        return action, phase, ap

    # Tinggi badan dalam RUANG LOKAL (y=0 = garis pinggang, + = ke bawah).
    # Punggung bahu & pusat kepala dibuat konstanta supaya seluruh bagian
    # (dan semua anchor FX) ikut berubah konsisten saat dituning.
    # Total badan (ruang lokal, sebelum SCALE): krist -40 -> telapak +44.
    # Setelah SCALE x1.32 + LIFT: ~115 px tinggi, cukup untuk mini boss tapi
    # wajah tetap di bawah HP bar boss (y-r-15..y-r-7).
    HEAD_Y = -24
    SHOULDER_Y = -14
    # Sendi bahu (x = ke depan mengikuti arah hadap)
    SHOULDER_FRONT = (12, SHOULDER_Y)
    SHOULDER_BACK = (-11, SHOULDER_Y - 1)

    def _attack_curve(ap):
        """Remap progres mentah (0..1) -> waktu pose (0..1), MONOTON naik.

        Yang membuat animasi serangan 2D terasa murah bukan jumlah frame,
        tapi tidak adanya: (a) anticipation yang jelas, (b) HOLD satu-dua
        frame di impact, (c) follow-through yang tidak langsung "ditarik"
        balik. Kurva ini memberi ketiganya; recovery sengaja tidak pernah
        turun (versi sinus dulu membuat bilah terlihat mundur sesaat).

        Batas segmen dipilih supaya jatuh PERSIS di batas fase
        _blade_angle / _front_grip_local: pose-time 0.26 = puncak wind-up,
        0.79 = impact, dan setelahnya recovery.
        """
        if ap <= 0.0:
            return 0.0
        if ap < 0.28:                       # anticipation: diperlambat
            t = ap / 0.28
            return 0.26 * (t ** 0.75)
        if ap < 0.50:                       # tebasan: sangat cepat
            t = (ap - 0.28) / 0.22
            return 0.26 + 0.53 * (t ** 0.5)
        if ap < 0.62:                       # IMPACT HOLD (nyaris beku)
            t = (ap - 0.50) / 0.12
            return 0.79 + 0.05 * t
        t = (ap - 0.62) / 0.38              # follow-through -> siap
        return 0.84 + 0.16 * (t ** 0.85)

    def _portrait_blade_angle(back=False):
        """Sudut bilah mode portrait: rapat ke badan, ujung menukik ke bawah.

        Lihat _front_grip_local(compact=...): HeroPortraits meng-crop bbox
        lalu men-scale-nya ke kartu, jadi figur yang LEBAR (bilah terentang)
        justru terKECIL di kartu yang sama. Dengan bilah ditarik masuk, bbox
        menyempit dan figur ter-render ~1.3x lebih besar - wajah & zirah
        akhirnya terbaca di Hero Shop.
        """
        return 0.62 if not back else -0.68

    def _blade_angle(phase, action, ap=0.0, back=False):
        """Sudut bilah (radian, dari garis lurus-bawah; + = ke depan).

        0 = moncong ke bawah, +pi/2 = lurus ke depan, ~pi = ke atas,
        -pi/2 = lurus ke belakang. Ditabel per-pose, BUKAN diturunkan dari
        arah lengan, supaya bilah tidak pernah menyayat menembus badannya
        sendiri. Depan dan belakang sengaja TIDAK simetris: bilah depan
        diangkat (memberi arah + massa di kuadran atas, seperti surai
        Grimjam / ponytail Kaizen yang membuat hero lain terbaca di lane),
        bilah belakang menukik ke bawah-belakang (menyeimbangkan bobot dan
        tetap melebar ke kiri supaya siluet tidak jadi tiang sempit).
        """
        s = math.sin(phase * 1.72)
        if action == "attack":
            # Semua jalur rotasi ada di SISI DEPAN badan, jadi tidak ada satu
            # frame pun bilah melintasi torso atau kepala. `ap` di sini sudah
            # lewat _attack_curve() (anticipation -> swing -> HOLD -> rebound).
            if ap < 0.26:                       # wind-up (1.78 -> 2.92)
                t = ap / 0.26
                return (1.78 + 1.14 * t, -1.00 - 1.92 * t)[back]
            if ap < 0.79:                       # tebasan (2.92 -> 0.30)
                t = (ap - 0.26) / 0.53
                return (2.92 - 2.62 * t, -2.92 + 1.92 * t)[back]
            t = (ap - 0.79) / 0.21             # recovery -> siap
            return (0.30 + 1.48 * t, -1.00)[back]
        if action == "surge":                  # Q: tusukan mana medatar
            return (1.45, -1.45)[back]
        if action == "ward":                   # E: dua bilah tegak = garda
            return (3.02, -3.02)[back]
        if action == "void":                   # R: kedua bilah dibuka ke atas
            return (2.40, -2.40)[back]
        if action == "blink":
            return (0.62, -0.62)[back]
        if action == "walk":
            return (1.78 + s * 0.10, -1.00 - s * 0.10)[back]
        # Siap: bilah DEPAN terangkat diagonal ke depan-atas, bilah belakang
        # menukik ke belakang-bawah. Versi dua bilah sejajar horizontal
        # terbaca sebagai "palang" putih lebar yang menenggelamkan badan di
        # skala hero; sudut asimetris ini tetap menjaga lebar siluet
        # (W/H ~1.05) tapi membuat kepala & dada jadi subjek. Nilai ini
        # juga titik awal/akhir ayunan -> tidak ada frame "snap".
        w = math.sin(phase * 0.5) * 0.05
        return (1.78 + w, -1.00 - w)[back]

    def _front_grip_local(action, ap=0.0, phase=0.0, compact=False):
        """Pergelangan tangan depan (pegangan bilah utama), ruang lokal.

        compact=True dipakai mode portrait: HeroPortraits meng-crop bbox
        lalu men-scale-nya ke kartu, jadi konten yang LEBAR (bilah terentang
        ke kanan-kiri) justru membuat figur terKECIL di kartu yang sama.
        Dengan bilah ditarik rapat ke badan, bbox menyempit -> figur
        ter-render ~1.3x lebih besar, wajah & zirah terbaca.
        """
        rest = _NS_gornak.SHOULDER_Y + 16
        if compact:
            return (12, rest + 2)
        if action == "attack":
            # Tangan tetap di sisi depan badan sepanjang ayunan - x tidak
            # pernah melewati garis tengah, jadi bilah tidak menutupi wajah.
            # Batas segmen mengikuti _attack_curve(): 0-0.26 angkat,
            # 0.26-0.79 tebas (dengan HOLD di ~0.78), 0.79-1 recovery.
            if ap < 0.26:
                t = min(1.0, ap / 0.26) ** 0.9
                return (int(15 - 13 * t), int(rest - 27 * t))
            if ap < 0.79:
                t = (ap - 0.26) / 0.53
                return (int(2 + 21 * t), int(rest - 27 + 33 * t))
            t = (ap - 0.79) / 0.18
            return (int(23 - 8 * t), int(rest + 6 - 4 * t))
        if action == "surge":
            return (23, rest + 3)
        if action == "ward":
            return (14, rest - 9)
        if action == "void":
            return (19, rest - 15)
        if action == "blink":
            return (16, rest - 2)
        if action == "walk":
            s = math.sin(phase * 1.72)
            return (int(15 + s * 3), int(rest - s * 2))
        return (15, rest + int(math.sin(phase * 0.62)))

    def _back_grip_local(action, ap=0.0, phase=0.0, compact=False):
        """Pergelangan tangan belakang (bilah pendek, grip terbalik)."""
        rest = _NS_gornak.SHOULDER_Y + 17
        if compact:
            return (-13, rest + 3)
        if action == "attack":
            if ap < 0.26:
                t = min(1.0, ap / 0.26) ** 0.9
                return (int(-19 - 5 * t), int(rest - 24 * t))
            if ap < 0.79:
                t = (ap - 0.26) / 0.53
                return (int(-24 - 3 * t), int(rest - 24 + 30 * t))
            t = (ap - 0.79) / 0.21
            return (int(-27 + 8 * t), int(rest + 6 - 3 * t))
        if action == "surge":
            return (-21, rest - 3)
        if action == "ward":
            return (-20, rest - 11)
        if action == "void":
            return (-21, rest - 14)
        if action == "blink":
            return (-20, rest - 1)
        if action == "walk":
            s = math.sin(phase * 1.72)
            return (int(-19 + s * 3), int(rest + s * 2))
        return (-19, rest + int(math.sin(phase * 0.62 + 1.1)))

    def _elbow(a, b, bend):
        """Siku 2-tulang: titik tengah + offset tegak lurus.

        Membuat lengan selalu tersambung (tidak pernah "lepas" seperti
        sticker) dan lengkungannya bisa diarahkan per sisi.
        """
        mx = (a[0] + b[0]) * 0.5
        my = (a[1] + b[1]) * 0.5
        dx = b[0] - a[0]
        dy = b[1] - a[1]
        ln = math.hypot(dx, dy) or 1.0
        return (int(mx + (-dy / ln) * bend), int(my + (dx / ln) * bend))

    def _arm_chain(shoulder, grip, phase, action, ap=0.0, back=False):
        """(elbow, blade_angle) - siku dari lengan, sudut dari tabel pose."""
        elbow = _NS_gornak._elbow(shoulder, grip, -4.5 if not back else 5.0)
        return elbow, _NS_gornak._blade_angle(phase, action, ap, back)

    def _blade_len(action, back=False):
        # Panjang bilah adalah sumber LEBAR utamanya siluet: pedang yang
        # dipegang menyamping membuat karakter pemegang dua bilah terbaca
        # penuh, bukan setiinggi tiang.
        if back:
            return 25 if action != "attack" else 29
        if action == "attack":
            return 42
        if action == "surge":
            return 44
        return 36

    def _head_bob(action, phase, ap):
        """Offset kepala (dx, dy) ruang lokal.

        Yang membuat rig terasa "hidup" bukan jumlah sendi, tapi kepala yang
        TIDAK merekat mati ke torso: dia mengangkat sedikit saat langkah
        (ayunan kontrarotasi), menunduk saat ayunan bilah, dan bergoyang
        halus saat idle.
        """
        if action == "walk":
            sw = math.sin(phase * 1.72)
            return (int(-sw * 1.2), int(abs(math.sin(phase * 1.15)) * -1.4))
        if action == "attack":
            return (int(math.sin(ap * math.pi) * 2.4),
                    -int(math.sin(ap * math.pi) * 1.4))
        if action == "void":
            return (-1, -2)
        if action == "ward":
            return (0, -1)
        return (int(math.sin(phase * 0.31) * 0.9),
                int(math.sin(phase * 0.62 + 0.8) * 0.8))

    def _rig_shift(action, phase, ap):
        """(lean, root_y) badan; kaki TIDAK ikut bergeser (menapak)."""
        lean = 0
        root_y = int(math.sin(phase * 0.62) * 1.2)
        if action == "walk":
            lean = int(math.sin(phase * 1.72) * 2)
            root_y -= int(abs(math.sin(phase * 1.15)) * 2.5)
        elif action == "attack":
            t = math.sin(ap * math.pi)
            lean = int(t * 6)
            root_y += int(t * 2)
        elif action == "surge":
            lean = 3
            root_y -= 1
        elif action in ("void", "ward"):
            root_y -= 2
        elif action == "surge":
            lean = 3
            root_y -= 1
        elif action == "blink":
            lean = 1
            root_y -= 1
        return lean, root_y

    def _s(v):
        """Ukuran ruang lokal (lebar garis, radius) -> piksel layar."""
        return max(1, int(round(v * _NS_gornak.SCALE)))

    def _local_to_screen(cx, cy, facing, lean, root_y, lx, ly):
        """SATU pemetaan lokal -> layar: skala, arah hadap, bob/lean.

        Semua bagian tubuh dan semua titik jangkar efek (ujung bilah,
        pergelangan tangan) melewati fungsi ini, jadi ukuran boleh diubah
        lewat satu angka tanpa membuat efek lepas dari badan.
        """
        f = 1 if facing >= 0 else -1
        k = _NS_gornak.SCALE
        return (int(cx + (lx * f + lean * f) * k),
                int(cy - _NS_gornak.LIFT + (ly + root_y) * k))

    def _local(boss, x, y, action, phase, ap, lx, ly):
        """Ruang lokal rig -> piksel surface (dipakai FX eksternal)."""
        facing = getattr(boss, "direction", 1) or 1
        lean, root_y = _NS_gornak._rig_shift(action, phase, ap)
        return _NS_gornak._local_to_screen(x, y, facing, lean, root_y, lx, ly)

    def _tip_local(action, phase, ap=0.0, back=False):
        """Ujung bilah dalam ruang lokal (rig & FX pakai angka yang sama)."""
        grip = (_NS_gornak._front_grip_local(action, ap, phase) if not back
                else _NS_gornak._back_grip_local(action, ap, phase))
        shoulder = (_NS_gornak.SHOULDER_FRONT if not back
                    else _NS_gornak.SHOULDER_BACK)
        _, angle = _NS_gornak._arm_chain(shoulder, grip, phase, action, ap,
                                        back)
        L = _NS_gornak._blade_len(action, back)
        return (int(grip[0] + math.sin(angle) * L),
                int(grip[1] + math.cos(angle) * L))

    def _tip_screen(boss, x, y, back=False):
        action, phase, ap = _NS_gornak._resolve_pose(boss)
        # FX selalu memakai pose yang sama dengan badan (lihat
        # _resolve_pose yang murni), jadi bolt/proc tidak pernah lepas.
        return _NS_gornak._local(boss, x, y, action, phase, ap,
                                 *_NS_gornak._tip_local(action, phase, ap, back))

    # ==================================================================
    # ENTRY POINT
    # ==================================================================
    def draw_gornak(surface, boss, x, y):
        """Entry point Boss.draw() sekaligus heroes.render_hero()."""
        # jalur hero (lane): heroes/__init__ men-set _render_scale sebelum
        # memanggil renderer, dan _finish_hd_sprite sudah menambah
        # rim/terminator -> pass di sini dilewati (lihat _draw_gnk_rig_at).
        _NS_gornak._HERO_LANE.v = hasattr(boss, "_render_scale")
        _NS_gornak._update_gnk_attack_anim(boss)
        action, phase, ap = _NS_gornak._resolve_pose(
            boss, _NS_gornak._detect_moving(boss))
        boss._gnk_pose_action = action
        skill = getattr(boss, "active_skill", None)
        timer = int(getattr(boss, "active_skill_timer", 0))
        portrait = bool(getattr(boss, "_portrait_hd", False))
        facing = getattr(boss, "direction", 1) or 1
        flash = _NS_gornak._alpha(170 * (getattr(boss, "hurt_flash_timer", 0)
                                         / 8.0))

        # ── Latar. Dibuang total saat portrait supaya auto-crop Hero Shop
        #    terisi wajah & material, bukan lingkaran efek.
        if not portrait:
            _NS_gornak._draw_anti_magic_field(surface, x, y, phase, skill)
            _NS_gornak._draw_ground_rune(surface, x, y, phase, skill)
            if skill == "q":
                _NS_gornak._draw_manabreak_ground(surface, boss, x, y, timer,
                                                   phase)
            elif skill == "w":
                _NS_gornak._draw_blink_ground(surface, boss, x, y, timer,
                                              phase)
            elif skill == "r":
                _NS_gornak._draw_manavoid_ground(surface, boss, x, y, timer,
                                                 phase)

        # ── Karakter
        if action == "blink":
            _NS_gornak._draw_gnk_blink(surface, boss, x, y, timer, portrait,
                                       flash)
        else:
            if not portrait:
                _NS_gornak._draw_shadow(surface, x, y + _NS_gornak.GROUND_DY)
            _NS_gornak._draw_gnk_rig_at(surface, x, y, facing, phase, action,
                                        ap, portrait, flash)
            if action == "attack" and not portrait:
                _NS_gornak._draw_crescent_slash(surface, x, y, facing, phase,
                                                ap)
            elif action == "walk" and not portrait:
                # Debu langkah: dua kepul kecil tepat saat telapak mendarat,
                # jadi bobot badan terasa menekan tanah (bukan character
                # meluncur di atas lantai).
                _NS_gornak._draw_footfall_dust(surface, x, y, facing, phase)

        # ── Foreground FX
        if not portrait:
            if skill == "q":
                _NS_gornak._draw_manabreak_foreground(surface, boss, x, y,
                                                       timer, phase)
            elif skill == "e":
                _NS_gornak._draw_counterspell_foreground(surface, boss, x, y,
                                                          timer, phase)
            elif skill == "r":
                _NS_gornak._draw_manavoid_foreground(surface, boss, x, y,
                                                     timer, phase)

    def _draw_gnk_rig_at(surface, x, y, facing, phase, action, ap, detail,
                         flash=0):
        """Rig -> buffer -> outline gelap 1 px -> satu blit murah.

        Mode portrait Hero Shop memakai kanvas kecil (160x160 di
        ui_components HeroPortraits) dan meng-crop dari bbox: kalau badan
        digambar dengan anchor di pinggang, bilah depan yang panjang
        melewati tepi kanan dan TERPOTONG. Jadi di mode itu konten dipusatkan
        pada bbox-nya sendiri; jalur boss (1x) tidak berubah sama sekali.
        """
        buf = pygame.Surface((_NS_gornak.RIG_W, _NS_gornak.RIG_H),
                             pygame.SRCALPHA)
        _NS_gornak._draw_gnk_rig(buf, _NS_gornak.RIG_OX, _NS_gornak.RIG_OY,
                                 facing, phase, action, ap, detail)
        if flash > 0:
            lit = buf.copy()
            lit.fill((255, 246, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
            lit.set_alpha(flash)
            buf.blit(lit, (0, 0))
        # Jalur BOSS digambar langsung ke layar 1:1, jadi TIDAK melewati
        # _finish_hd_sprite (yang sudah memberi rim+terminator ke hero).
        # Di sinilah cahaya itu dipasang untuk boss. Saat hero-path
        # (scale != 1.0) pass-nya dilewati supaya tidak dua kali; mode
        # portrait tetap dipakai karena HeroPortraits tidak memanggil
        # _finish_hd_sprite sama sekali.
        # Aturan: pass cahaya dipasang di SINI hanya kalau sprite ini TIDAK
        # akan dilewatkan ke heroes._finish_hd_sprite (yang sudah memasang
        # pass yang sama):
        #   * boss 1x (scale 1.0)          -> pasang di sini
        #   * lane hero (scale != 1.0)      -> jangan (nanti dobel)
        #   * Hero Shop (tanpa _render_scale, portrait) -> pasang di sini,
        #     karena HeroPortraits tidak memanggil _finish_hd_sprite sama
        #     sekali. Ciri mode shop: attribute hero TIDAK punya
        #     _render_scale sama sekali (jalur lane selalu men-set-nya).
        if _lighting is not None and not _NS_gornak._HERO_LANE.v:
            _lighting.apply_to_rig(
                buf, rim_add=(32, 26, 46), shade_mul=160,
                box=_NS_gornak.GRAD_BOX if not detail else None)
        ox = int(x) - _NS_gornak.RIG_OX
        oy = int(y) - _NS_gornak.RIG_OY
        if detail:                      # portrait: pusatkan konten
            used = buf.get_bounding_rect(min_alpha=1)
            if used.width > 0:
                ox = int(x) - (used.left + used.width // 2)
                oy = int(y) - (used.top + used.height // 2)
        # Outline siluet (4 arah) - sama seperti Sylara: jalur hero memang
        # menambah satu tepi lagi di _finish_hd_sprite, dan hasilnya justru
        # dipakai sebagai acuan keluarga, jadi tidak perlu di-skip.
        edge = buf.copy()
        edge.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            surface.blit(edge, (ox + dx, oy + dy))
        surface.blit(buf, (ox, oy))
        return buf

    # Pose lama tetap tersedia (dipakai tool debug/preview).
    def _draw_gnk_idle(surface, boss, x, y):
        _NS_gornak._draw_gnk_rig_at(surface, x, y,
                                    getattr(boss, "direction", 1) or 1,
                                    float(getattr(boss, "pulse", 0.0)),
                                    "idle", 0.0, False)

    def _draw_gnk_walk(surface, boss, x, y):
        _NS_gornak._draw_gnk_rig_at(surface, x, y,
                                    getattr(boss, "direction", 1) or 1,
                                    float(getattr(boss, "pulse", 0.0)) * 2.0,
                                    "walk", 0.0, False)

    def _draw_gnk_attack(surface, boss, x, y, ap=0.5):
        _NS_gornak._draw_gnk_rig_at(surface, x, y,
                                    getattr(boss, "direction", 1) or 1,
                                    float(getattr(boss, "pulse", 0.0)),
                                    "attack", ap, False)

    def _draw_gnk_blink(surface, boss, x, y, timer, portrait, flash):
        """Blink: after-image RIG YANG SAMA + dissolve di garis kaki."""
        duration = _NS_gornak.SKILL_DUR["w"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = getattr(boss, "direction", 1) or 1
        phase = float(getattr(boss, "pulse", 0.0))
        if progress < 0.30:
            alpha_t = 1.0 - progress / 0.30
        elif progress < 0.68:
            alpha_t = 0.14
        else:
            alpha_t = (progress - 0.68) / 0.32

        if not portrait:
            _NS_gornak._draw_shadow(surface, x, y + _NS_gornak.GROUND_DY)

        rig, ax, ay = _NS_gornak._compose_outline(x, y, facing, phase, "blink",
                                                  0.0, portrait)
        if progress < 0.80:
            for i in (3, 2, 1):
                rig.set_alpha(_NS_gornak._alpha(80 * alpha_t / i))
                surface.blit(rig, (x - ax - facing * i * 8, y - ay + i))
        rig.set_alpha(_NS_gornak._alpha(70 + 185 * min(1.0, alpha_t)))
        surface.blit(rig, (x - ax, y - ay))
        rig.set_alpha(255)

        if not portrait:
            p = _NS_gornak.PALETTE
            gy = y + _NS_gornak.GROUND_DY
            for i in range(8):
                t = (phase * 0.5 + i * 0.125) % 1.0
                gx = x + int(math.sin(i * 1.7) * (10 + t * 16))
                a = _NS_gornak._alpha(190 * (1 - t) * alpha_t)
                if a > 0:
                    _NS_gornak._aacircle(surface, (*p["magic_mid"], a),
                                         (gx, gy - int(t * 12)), 2)
                    _NS_gornak._aacircle(surface, (*p["magic_shine"], a),
                                         (gx, gy - int(t * 12)), 1)

    def _compose_outline(x, y, facing, phase, action, ap, detail):
        """Rig + outline gelap 1 px sebagai SATU surface (perlu untuk
        after-image blink yang mengatur alpha sendiri).

        Return ``(surface, anchor_x, anchor_y)``: titik dalam surface yang
        jatuh tepat di dunia ``(x, y)``.
        """
        buf = pygame.Surface((_NS_gornak.RIG_W, _NS_gornak.RIG_H),
                             pygame.SRCALPHA)
        _NS_gornak._draw_gnk_rig(buf, _NS_gornak.RIG_OX, _NS_gornak.RIG_OY,
                                 facing, phase, action, ap, detail)
        pad = 1
        out = pygame.Surface((_NS_gornak.RIG_W + pad * 2,
                              _NS_gornak.RIG_H + pad * 2), pygame.SRCALPHA)
        edge = buf.copy()
        edge.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            out.blit(edge, (pad + dx, pad + dy))
        out.blit(buf, (pad, pad))
        return out, _NS_gornak.RIG_OX + pad, _NS_gornak.RIG_OY + pad

    def _draw_gnk_rig(surface, cx, cy, facing, phase, action, ap=0.0,
                      detail=False):
        """BONE RIG 2D BERLAPIS - seluruh badan dihitung dari sendi.

        ``cx, cy`` = anchor (pusat boss / garis pinggul). Urutan gambar
        belakang -> depan, jadi pedang belakang di balik torso dan pedang
        depan paling depan, seperti sprite sheet referensi.
        """
        p = _NS_gornak.PALETTE
        f = 1 if facing >= 0 else -1
        lean, root_y = _NS_gornak._rig_shift(action, phase, ap)

        def pt(dx, dy):
            """Sendi badan (ikut bob/lean)."""
            return _NS_gornak._local_to_screen(cx, cy, f, lean, root_y, dx, dy)

        def ptg(dx, dy):
            """Sendi yang terpatok tanah (telapak kaki tidak ikut bob)."""
            return _NS_gornak._local_to_screen(cx, cy, f, lean, 0, dx, dy)

        def poly(color, coords, outline=True):
            pts = [pt(dx, dy) for dx, dy in coords]
            if outline:
                _NS_gornak._poly(surface, p["shadow_deep"],
                                  [(qx + f, qy + 1) for qx, qy in pts])
            _NS_gornak._poly(surface, color, pts)
            return pts

        def poly_free(color, pts, outline=True):
            if outline:
                _NS_gornak._poly(surface, p["shadow_deep"],
                                  [(qx + f, qy + 1) for qx, qy in pts])
            _NS_gornak._poly(surface, color, pts)

        def dot(color, dx, dy, r, outline=True):
            sx, sy = pt(dx, dy)
            rr = _NS_gornak._s(r)
            if outline:
                _NS_gornak._aacircle(surface, p["shadow_deep"],
                                     (sx + f, sy + 1), rr + 1)
            _NS_gornak._aacircle(surface, color, (sx, sy), rr)

        def limb(a, b, width, base, light=None):
            aa, bb = pt(*a), pt(*b)
            w = _NS_gornak._s(width)
            _NS_gornak._aaline(surface, p["shadow_deep"],
                               (aa[0] + f, aa[1] + 1),
                               (bb[0] + f, bb[1] + 1), w + 2)
            _NS_gornak._aaline(surface, base, aa, bb, w)
            if light:
                off = -1 if f > 0 else 1
                _NS_gornak._aaline(surface, light, (aa[0] + off, aa[1] - 1),
                                   (bb[0] + off, bb[1] - 1),
                                   max(1, _NS_gornak._s(width // 3)))

        breath = math.sin(phase * 0.62)
        stride = (math.sin(phase * 1.72) if action == "walk" else 0.0)
        ward = action == "ward"
        void = action == "void"
        surge = action == "surge"

        portrait = bool(detail)
        front_grip = _NS_gornak._front_grip_local(action, ap, phase,
                                                 compact=portrait)
        back_grip = _NS_gornak._back_grip_local(action, ap, phase,
                                               compact=portrait)
        front_elbow, front_angle = _NS_gornak._arm_chain(
            _NS_gornak.SHOULDER_FRONT, front_grip, phase, action, ap)
        back_elbow, back_angle = _NS_gornak._arm_chain(
            _NS_gornak.SHOULDER_BACK, back_grip, phase, action, ap, back=True)
        if portrait:
            front_angle = _NS_gornak._portrait_blade_angle(False)
            back_angle = _NS_gornak._portrait_blade_angle(True)

        # 1. Jubah belakang - memberi kedalaman pada siluet
        _NS_gornak._draw_gnk_cape_back(surface, pt, poly_free, f, phase,
                                       action)

        # 2. Kaki - telapak dipatok di GROUND_DY
        _NS_gornak._draw_gnk_legs(surface, pt, ptg, poly_free, f, phase,
                                  action, stride)

        # 3. Tangan + bilah belakang (di balik badan)
        _NS_gornak._draw_gnk_arm(surface, pt, poly_free, dot, limb, f, phase,
                                 action, ap, _NS_gornak.SHOULDER_BACK,
                                 back_elbow, back_grip, back_angle,
                                 _NS_gornak._blade_len(action, True),
                                 back=True)

        # 4. Torso + harness + pelat spellbreaker
        _NS_gornak._draw_gnk_torso(surface, pt, poly_free, dot, f, phase,
                                   breath, ward, void)

        # 5. Sabuk, loincloth, rantai besi
        _NS_gornak._draw_gnk_belt(surface, pt, poly_free, dot, f, phase,
                                  action, stride)

        # 6. Pauldron bertingkat
        _NS_gornak._draw_gnk_pauldrons(surface, pt, poly_free, dot, f, phase,
                                       breath)

        # 7. Leher + kepala (rahang, jenggot kepang, mohawk nempel)
        _NS_gornak._draw_gnk_head(surface, pt, poly_free, dot, f, phase,
                                  action, ward, void)

        # 8. Tangan + bilah depan (paling depan)
        _NS_gornak._draw_gnk_arm(surface, pt, poly_free, dot, limb, f, phase,
                                 action, ap, _NS_gornak.SHOULDER_FRONT,
                                 front_elbow, front_grip, front_angle,
                                 _NS_gornak._blade_len(action), back=False,
                                 ward=ward, void=void, surge=surge)

        # 9. Rim light ungu - sinyal warna tema (lihat docstring-nya)
        _NS_gornak._draw_gnk_rimlight(surface, pt, f, phase, ward, void)

        # 10. Pass material portrait-only
        if detail:
            _NS_gornak._draw_gnk_masterwork_details(surface, pt, f, phase,
                                                    action)
            _NS_gornak._draw_gnk_weave(surface, pt, f)

    # ==================================================================
    # BAGIAN TUBUH
    # ==================================================================
    # Prinsip di 720p: yang dibaca hanyalah NILAI (terang/gelap) dan
    # SILUET, bukan garis halus. Setiap bagian karenanya dibatasi 2-3
    # lapis nilai, dan garis penanda (otot, jahitan) hanya muncul di
    # pass portrait.
    # ==================================================================

    def _draw_gnk_cape_back(surface, pt, poly_free, f, phase, action):
        """Half-mantle kulit di punggung: MEMBINGKAI badan, tidak
        melebarinya. Tepi bawah robek dan berayun oleh phase."""
        p = _NS_gornak.PALETTE
        sway = int(math.sin(phase * 1.05) * 2)
        if action in ("walk", "attack"):
            sway -= 2
        outer = [(-15, -19), (-19, -6), (-22 + sway, 10), (-17 + sway, 17),
                 (-11 + sway, 9), (-6 + sway, 16), (0, 7), (4, -8), (2, -19)]
        poly_free(p["robe_darkest"], [pt(*q) for q in outer])
        inner = [(-14, -17), (-17, -6), (-20 + sway, 8), (-15 + sway, 14),
                 (-10 + sway, 8), (-5 + sway, 13), (0, 6), (3, -8), (1, -17)]
        poly_free(p["robe_dark"], [pt(*q) for q in inner], outline=False)
        _NS_gornak._aaline(surface, p["robe_mid"], pt(-10, -14),
                           pt(-12 + sway, 4), 1)
        poly_free(p["robe_light"], [pt(-9, -12), pt(-12 + sway, 1),
                                   pt(-9 + sway, 7), pt(-6, -6)],
                  outline=False)
        # Rim di tepi robek: 1 px terang membuat sobekan terbaca sebagai
        # KAIN (bukan lubang gelap) di skala 1x.
        hem = [(-16 + sway, 9), (-12 + sway, 15), (-8 + sway, 8),
               (-4 + sway, 14), (0, 6)]
        for i in range(len(hem) - 1):
            _NS_gornak._aaline(surface, p["robe_edge"], pt(*hem[i]),
                               pt(*hem[i + 1]), 1)

    def _draw_gnk_legs(surface, pt, ptg, poly_free, f, phase, action, stride):
        """Dua kaki berotot: paha -> pelindung lutut -> greave -> boot.

        Pass hero-baru: blok tulang kering tidak lagi memakai armor_light
        (di skala hero kaki terbaca sebagai dua balok abu-abu pucat yang
        menyatu dengan loincloth). Sekarang paha & betis gelap dengan SATU
        garis tepi terang di sisi cahaya + kap kuningan di ujung boot, jadi
        kedua kaki terpisah dan tetap terbaca.
        """
        p = _NS_gornak.PALETTE
        hip_y = 4
        ground = _NS_gornak.FEET_DY
        for side in (-1, 1):
            if action == "walk":
                dx = int(stride * 8) * side
                lift = int(max(0.0, -stride * side) * 4)
            elif action == "attack":
                dx = 8 if side > 0 else -7
                lift = 0
            elif action in ("surge", "void"):
                dx = 7 if side > 0 else -7
                lift = 0
            else:
                dx = 4 if side > 0 else -6
                lift = 0
            front = side > 0
            hip_x = side * 7
            knee_x = hip_x + int(dx * 0.55) + side
            foot_x = hip_x + dx + side * 2
            knee_y = (hip_y + ground) // 2 - lift
            fy = ground - lift
            # Paha: satu blok gelap + satu blok tengah + garis cahaya tipis
            poly_free(p["skin_darkest"], [pt(hip_x - 6, hip_y),
                                          pt(hip_x + 5, hip_y),
                                          pt(knee_x + 4, knee_y),
                                          pt(knee_x - 5, knee_y)])
            if front:
                poly_free(p["skin_dark"], [pt(hip_x - 5, hip_y + 1),
                                          pt(hip_x + 4, hip_y + 1),
                                          pt(knee_x + 3, knee_y - 1),
                                          pt(knee_x - 4, knee_y - 1)],
                          outline=False)
                poly_free(p["skin_mid"], [pt(hip_x - 4, hip_y + 2),
                                          pt(hip_x + 1, hip_y + 2),
                                          pt(knee_x - 1, knee_y - 4),
                                          pt(knee_x - 3, knee_y - 4)],
                          outline=False)
            # Pembungkus kain di paha (identik dengan loincloth -> kaki
            # menyatu dengan badan, bukan dua tabung terpisah)
            poly_free(p["robe_dark"], [pt(hip_x - 6, hip_y + 7),
                                       pt(hip_x + 5, hip_y + 7),
                                       pt(hip_x + 5, hip_y + 13),
                                       pt(hip_x - 6, hip_y + 13)])
            if front:
                poly_free(p["robe_mid"], [pt(hip_x - 4, hip_y + 8),
                                          pt(hip_x + 2, hip_y + 8),
                                          pt(hip_x + 2, hip_y + 12),
                                          pt(hip_x - 4, hip_y + 12)],
                          outline=False)
            # Pelindung lutut
            poly_free(p["armor_darkest"], [pt(knee_x - 4, knee_y - 3),
                                           pt(knee_x + 4, knee_y - 3),
                                           pt(knee_x + 4, knee_y + 3),
                                           pt(knee_x - 4, knee_y + 3)])
            poly_free(p["armor_mid"], [pt(knee_x - 3, knee_y - 2),
                                       pt(knee_x + 2, knee_y - 2),
                                       pt(knee_x + 2, knee_y + 2),
                                       pt(knee_x - 3, knee_y + 2)],
                          outline=False)
            _NS_gornak._aacircle(surface, p["armor_shine"], pt(knee_x - 1,
                                                              knee_y - 1), 1)
            # Shina gelap + satu garis tepi cahaya
            poly_free(p["armor_dark"], [pt(knee_x - 4, knee_y + 2),
                                        pt(knee_x + 4, knee_y + 2),
                                        ptg(foot_x + 4, fy - 7),
                                        ptg(foot_x - 4, fy - 7)])
            if front:
                poly_free(p["armor_mid"], [pt(knee_x - 3, knee_y + 3),
                                           pt(knee_x + 1, knee_y + 3),
                                           ptg(foot_x + 1, fy - 8),
                                           ptg(foot_x - 3, fy - 8)],
                          outline=False)
                _NS_gornak._aaline(surface, p["armor_light"],
                                   pt(knee_x - 2, knee_y + 4),
                                   ptg(foot_x - 2, fy - 7), 1)
            # Boot gelap + kap kuningan, sol DATAR di garis tanah
            toe = 4 if f > 0 else -4
            poly_free(p["leather_dark"], [ptg(foot_x - 5, fy - 7),
                                          ptg(foot_x + 5, fy - 7),
                                          ptg(foot_x + toe + 2, fy - 2),
                                          ptg(foot_x + toe, fy),
                                          ptg(foot_x - toe, fy),
                                          ptg(foot_x - 6, fy - 3)])
            poly_free(p["leather_mid"], [ptg(foot_x - 4, fy - 6),
                                         ptg(foot_x + 4, fy - 6),
                                         ptg(foot_x + toe + 1, fy - 3),
                                         ptg(foot_x - 5, fy - 3)],
                        outline=False)
            # Garis break terang di pergelangan: tanpa ini paha-celana-boot
            # jadi satu kolom cokelat dan kaki "hilang" di skala hero.
            _NS_gornak._aaline(surface, p["leather_light"],
                               ptg(foot_x - 5, fy - 7),
                               ptg(foot_x + 4, fy - 7), 1)
            _NS_gornak._aaline(surface, p["brass_mid"],
                               ptg(foot_x + toe - 1, fy - 4),
                               ptg(foot_x + toe + 2, fy - 2), 2)
            if lift <= 0:
                _NS_gornak._aaline(surface, p["shadow_deep"],
                                   ptg(foot_x - 5, fy + 1),
                                   ptg(foot_x + 5, fy + 1), 2)
            else:
                _NS_gornak._aaline(surface, (*p["shadow"], 80),
                                   ptg(foot_x - 4, _NS_gornak.FEET_DY),
                                   ptg(foot_x + 4, _NS_gornak.FEET_DY), 2)

    def _draw_gnk_torso(surface, pt, poly_free, dot, f, phase, breath, ward,
                        void):
        """Dada bidang (V-taper) + pelat spellbreaker BERCAHAYA + rune ungu.

        Pass hero-baru: pelat baja dinaikkan ke armor_light/shine (sebelumnya
        armor_mid yang di skala hero menyatu dengan kulit sehingga seluruh
        badan jadi satu blob coklat), dan rantai pemutus sihir dibuat jadi
        tiga titik magic_hot yang jelas - itu "sinyal warna" yang dipakai
        Grimjaw (api) / Vex (void cyan) / Kaizen (angin biru) supaya unit
        terbaca dari jauh.
        """
        p = _NS_gornak.PALETTE
        sh = _NS_gornak.SHOULDER_Y
        twist = int(math.sin(phase * 1.05))
        poly_free(p["skin_darkest"], [pt(-14 + twist, sh - 1),
                                      pt(13 + twist, sh - 1), pt(10, 4),
                                      pt(-11, 4)])
        poly_free(p["skin_dark"], [pt(-12 + twist, sh), pt(12 + twist, sh),
                                   pt(9, 3), pt(-10, 3)], outline=False)
        poly_free(p["skin_mid"], [pt(-10 + twist, sh + 1),
                                  pt(9 + twist, sh + 1), pt(7, -2),
                                  pt(-8, -2)], outline=False)
        # Blok cahaya di bahu-dada (satu bentuk besar, bukan garis halus)
        poly_free(p["skin_light"], [pt(-9 + twist, sh + 1),
                                    pt(6 + twist, sh + 1), pt(4, sh + 7),
                                    pt(-8, sh + 6)], outline=False)
        poly_free(p["skin_shine"], [pt(-7 + twist, sh + 2),
                                    pt(2 + twist, sh + 2), pt(1, sh + 5),
                                    pt(-6, sh + 5)], outline=False)
        # Bayangan miring di bawah pektoral + highlight mikro: dua nilai
        # ini yang membuat dada terbaca BERBUKUK, bukan papan cokelat datar
        # saat di-zoom di kartu Hero Shop.
        poly_free(p["skin_dark"], [pt(-9 + twist, sh + 7), pt(-1 + twist, sh + 8),
                                   pt(-2 + twist, sh + 10),
                                   pt(-9 + twist, sh + 9)], outline=False)
        _NS_gornak._aaline(surface, p["skin_high"], pt(-7 + twist, sh + 4),
                           pt(-2 + twist, sh + 4), 1)
        # Garis tengah + perut (nilai, bukan outline)
        _NS_gornak._aaline(surface, p["skin_dark"], pt(twist, sh + 3),
                           pt(0, 2), 1)
        _NS_gornak._aaline(surface, p["skin_dark"], pt(-5, -2), pt(5, -2), 1)
        _NS_gornak._aaline(surface, p["skin_dark"], pt(-4, 1), pt(4, 1), 1)
        # Sabuk kulit diagonal - satu jalur tipis (dulu 5 px: jadi palang)
        _NS_gornak._aaline(surface, p["leather_dark"], pt(12 + twist, sh),
                           pt(-9, 3), 3)
        _NS_gornak._aaline(surface, p["leather_light"], pt(12 + twist, sh),
                           pt(-9, 3), 1)
        # Pelat spellbreaker: satu bentuk gelap dengan TEPI atas terang dan
        # SATU permata ungu. Pass-pass sebelumnya menaruh garis silang +
        # tiga titik rune di sini; di skala 720p itu terbaca sebagai noda
        # lavender, bukan detail. Satu fokus terang = satu bacaan jelas.
        poly_free(p["armor_darkest"], [pt(-12, sh + 1), pt(-1, sh + 2),
                                       pt(0, -5), pt(-11, -6)])
        poly_free(p["armor_mid"], [pt(-11, sh + 2), pt(-2, sh + 3),
                                   pt(-1, -5), pt(-10, -6)], outline=False)
        _NS_gornak._aaline(surface, p["armor_shine"], pt(-11, sh + 3),
                           pt(-2, sh + 4), 2)
        _NS_gornak._aaline(surface, p["armor_darkest"], pt(-1, sh + 3),
                           pt(0, -5), 1)
        hot = 0.40 + (0.60 if (ward or void) else 0.0)
        a = _NS_gornak._alpha(150 + 105 * hot *
                              (0.72 + 0.28 * math.sin(phase * 2.2)))
        gemx, gemy = pt(-6, sh + 5)
        _NS_gornak._aacircle(surface, (*p["magic_mid"], a), (gemx, gemy), 3)
        _NS_gornak._aacircle(surface, (*p["magic_hot"], min(255, a + 40)),
                             (gemx, gemy), 2)
        _NS_gornak._rect(surface, (*p["magic_shine"], 255),
                         (gemx - 1, gemy - 1, 2, 2))
        # Cincin kuningan di ujung harness - geser ke tengah-tulang-dada
        # (di sisi kiri dia terbaca sebagai bintik nyasar) dan buang
        # highlight putihnya: satu nilai saja sudah cukup terbaca.
        dot(p["brass_dark"], -1, -7, 2)
        dot(p["brass_mid"], -1, -7, 1)

    def _draw_gnk_belt(surface, pt, poly_free, dot, f, phase, action, stride):
        """Sabuk + gesper berlian ungu, loincloth, rantai lempengan besi."""
        p = _NS_gornak.PALETTE
        sway = int(math.sin(phase * 1.1) * 2)
        if action == "walk":
            sway += int(stride * 2)
        poly_free(p["leather_dark"], [pt(-12, 1), pt(12, 1), pt(12, 7),
                                      pt(-12, 7)])
        poly_free(p["leather_mid"], [pt(-11, 2), pt(11, 2), pt(11, 6),
                                     pt(-11, 6)], outline=False)
        _NS_gornak._aaline(surface, p["leather_light"], pt(-11, 2), pt(11, 2),
                           1)
        for bx in (-8, -3, 7):
            _NS_gornak._aacircle(surface, p["brass_mid"], pt(bx, 4), 1)
        poly_free(p["armor_darkest"], [pt(-3, 0), pt(4, 0), pt(4, 8),
                                       pt(-3, 8)])
        poly_free(p["armor_light"], [pt(-2, 1), pt(3, 1), pt(3, 6), pt(-2, 6)],
                  outline=False)
        _NS_gornak._aacircle(surface, p["magic_hot"], pt(0, 4), 2)
        _NS_gornak._aacircle(surface, p["magic_shine"], pt(0, 4), 1)
        # Loincloth bertepi robek. Sengaja sempit (lebar 12, panjang 20):
        # versi lebar mengubah kedua kaki jadi satu tiang ungu dan
        # menghapus silhouette "berdiri".
        # Kain dijatuhkan ke sisi BELAKANG garis tengah: sebelumnya simetris
        # sehingga menutup paha depan dan kaki tampak hilang satu.
        outer = [(-8, 7), (3, 7), (4 + sway, 18), (1 + sway, 24), (-2, 18),
                 (-3, 24), (-6, 18), (-8 + sway, 22), (-10 + sway, 16)]
        poly_free(p["robe_darkest"], [pt(*q) for q in outer])
        inner = [(-7, 8), (2, 8), (3 + sway, 17), (0 + sway, 21), (-2, 17),
                 (-4, 21), (-7 + sway, 15)]
        poly_free(p["robe_dark"], [pt(*q) for q in inner], outline=False)
        poly_free(p["robe_mid"], [pt(-3, 9), pt(3, 9), pt(3 + sway, 18),
                                  pt(0, 22), pt(-3 + sway, 17)],
                  outline=False)
        _NS_gornak._aaline(surface, p["robe_edge"], pt(-6, 9),
                           pt(-8 + sway, 20), 1)
        # Rantai lempengan pemutus sihir
        for i in range(3):
            yy = 9 + i * 4
            _NS_gornak._aaline(surface, p["armor_shine"], pt(9, yy),
                               pt(11 + int(sway * 0.3), yy + 3), 1)
            _NS_gornak._aacircle(surface, p["armor_light"], pt(10, yy + 1), 1)
        # Kantong kulit
        poly_free(p["leather_dark"], [pt(-13, 8), pt(-8, 8), pt(-7, 15),
                                      pt(-13, 15)])
        poly_free(p["leather_mid"], [pt(-12, 9), pt(-9, 9), pt(-8, 14),
                                     pt(-12, 14)], outline=False)

    def _draw_gnk_pauldrons(surface, pt, poly_free, dot, f, phase, breath):
        """Pauldron baja bertingkat + duri + permata ungu di sisi belakang."""
        p = _NS_gornak.PALETTE
        sh = _NS_gornak.SHOULDER_Y
        for side, scale in ((-1, 0.80), (1, 1.0)):
            sx = side * 15
            sy = sh - 2 - int(breath if side > 0 else 0)
            w = max(4, int(8 * scale))
            h = max(3, int(6 * scale))
            poly_free(p["armor_darkest"], [pt(sx - w, sy - h + 2),
                                          pt(sx + w, sy - h),
                                          pt(sx + w + 1, sy + 2),
                                          pt(sx, sy + h),
                                          pt(sx - w - 1, sy + 2)])
            poly_free(p["armor_mid"], [pt(sx - w + 1, sy - h + 3),
                                       pt(sx + w - 1, sy - h + 3),
                                       pt(sx + w, sy), pt(sx, sy + h - 2),
                                       pt(sx - w, sy)], outline=False)
            # Sisi JAUH dibiarkan gelap (dulu armor_light + shine: jadi
            # "sayat" pucat yang mengungguli wajah). Cahaya dan permata
            # tema ditaruh di sisi DEPAN, searah cahaya.
            lit = p["armor_light"] if side > 0 else p["armor_dark"]
            poly_free(lit, [pt(sx - w + 2, sy - h + 4),
                            pt(sx - 1, sy - h + 4),
                            pt(sx - 1, sy - 1),
                            pt(sx - w + 2, sy - 1)], outline=False)
            if side > 0:
                _NS_gornak._aaline(surface, p["armor_shine"],
                                   pt(sx - w + 2, sy - h + 4),
                                   pt(sx + w - 1, sy - h + 3), 1)
            spike = sy - h - (6 if side > 0 else 4)
            poly_free(p["armor_darkest"], [pt(sx - 2, sy - h + 1),
                                           pt(sx + 1, spike),
                                           pt(sx + 3, sy - h + 1)])
            poly_free(p["armor_light"], [pt(sx - 1, sy - h + 1),
                                         pt(sx + 1, spike + 1),
                                         pt(sx + 2, sy - h + 1)],
                      outline=False)
            _NS_gornak._aacircle(surface, p["brass_mid"], pt(sx + side * 4,
                                                            sy + 2), 1)
            if side > 0:
                # Permata tema: 2px saja. Versi 3+2 px tadi jadi blob ungu
                # yang mengambang di bahu dan mencuri fokus dari wajah.
                _NS_gornak._aacircle(surface, p["magic_mid"], pt(sx - 3,
                                                                sy - 1), 2)
                _NS_gornak._rect(surface, p["magic_shine"],
                                 (pt(sx - 3, sy - 1)[0],
                                  pt(sx - 3, sy - 1)[1], 1, 1))

    def _draw_gnk_head(surface, pt, poly_free, dot, f, phase, action, ward,
                       void):
        """KEPALA sebagai subjek: krist mohawk solid, wajah terang, mata
        menyala ber-halo ungu, jenggot kepang, circlet ber-taring.

        Versi awal masterwork masih terlalu "halus": rongga mata selebar 1 px
        dan helai rambut 1 px hilang setelah smoothscale jalur hero, sehingga
        kepala terbaca sebagai blob gelap. Sekarang volume rambut jadi SATU
        massa terang dengan 3 duri (bukan helaian), wajah blok TERANG, dan
        mata dua garis tebal + halo - persis cara Grimjaw (mask putih) atau
        Kaizen (ponytail) mempertahankan focal point di skala kecil.
        """
        p = _NS_gornak.PALETTE
        hy = _NS_gornak.HEAD_Y + int(math.sin(phase * 0.62) * 0.8)
        hx = 2 if action == "attack" else (0 if action == "void" else 1)
        sh = _NS_gornak.SHOULDER_Y

        # Leher & trapezius
        poly_free(p["skin_darkest"], [pt(-6, sh + 1), pt(6, sh + 1),
                                      pt(9, sh + 5), pt(-9, sh + 5)])
        poly_free(p["skin_mid"], [pt(-4, sh + 2), pt(4, sh + 2),
                                  pt(6, sh + 5), pt(-5, sh + 5)],
                  outline=False)

        # Massa rambut belakang (krist) - lebih besar dari tengkorak
        wave = int(math.sin(phase * 1.35) * 1.5)
        if action in ("walk", "attack", "surge"):
            wave -= 2
        crest = [(hx - 10, hy + 6), (hx - 13 + wave, hy - 2),
                 (hx - 11 + wave, hy - 12), (hx - 4, hy - 15),
                 (hx + 4, hy - 11), (hx + 7, hy - 3), (hx + 6, hy + 6)]
        poly_free(p["hair_darkest"], [pt(*q) for q in crest])
        # Pangkal krist ditebelkan 1 px supaya rambut tidak menempel langsung
        # ke dahi terang (kalau menempel, wajah kehilangan bentuknya).
        _NS_gornak._aaline(surface, p["shadow_deep"], pt(hx - 8, hy - 7),
                           pt(hx + 7, hy - 7), 1)
        crest_in = [(hx - 9, hy + 4), (hx - 11 + wave, hy - 2),
                    (hx - 9 + wave, hy - 10), (hx - 4, hy - 13),
                    (hx + 2, hy - 9), (hx + 5, hy - 2), (hx + 4, hy + 4)]
        poly_free(p["hair_mid"], [pt(*q) for q in crest_in], outline=False)
        # 3 duri krist - bentuk besar, BUKAN helai 1 px (hilang saat
        # di-scale). Duri tengah sedikit lebih pendek dan tiap duri
        # dipisah 1 px gelap supaya tidak jadi satu kerucut "topi penyihir".
        for i, (bx, bh) in enumerate(((-10, 11), (-3, 13), (4, 9))):
            tipx = hx + bx - 4 + wave
            tipy = hy - bh
            poly_free(p["hair_light"], [pt(hx + bx - 1, hy - 3), pt(tipx, tipy),
                                       pt(hx + bx + 4, hy - 5)],
                      outline=False)
            poly_free(p["hair_shine"], [pt(hx + bx, hy - 4), pt(tipx + 1,
                                                                tipy + 2),
                                       pt(hx + bx + 2, hy - 5)],
                      outline=False)
        for bx in (-6, 1):
            _NS_gornak._aaline(surface, p["hair_darkest"], pt(hx + bx, hy - 4),
                               pt(hx + bx - 3 + wave, hy - 12), 1)
        # Kuncir: pita rambut ramping yang keluar dari samping kepala dan
        # diikat cincin kuningan - menambah massa di belakang kepala tanpa
        # jadi gumpalan di atas bahu.
        poly_free(p["hair_dark"], [pt(hx - 10, hy - 2), pt(hx - 15 + wave, hy - 1),
                                   pt(hx - 16 + wave, hy + 5),
                                   pt(hx - 12, hy + 4), pt(hx - 9, hy + 1)])
        poly_free(p["hair_mid"], [pt(hx - 11, hy), pt(hx - 14 + wave, hy + 1),
                                 pt(hx - 12, hy + 3)], outline=False)
        _NS_gornak._aacircle(surface, p["brass_mid"], pt(hx - 10, hy), 2)

        # Tengkorak + rahang bidang
        poly_free(p["skin_darkest"], [pt(hx - 8, hy - 7), pt(hx + 8, hy - 7),
                                      pt(hx + 9, hy + 2), pt(hx + 7, hy + 9),
                                      pt(hx - 4, hy + 10), pt(hx - 8, hy + 3)])
        poly_free(p["skin_mid"], [pt(hx - 7, hy - 6), pt(hx + 7, hy - 6),
                                  pt(hx + 8, hy + 2), pt(hx + 6, hy + 8),
                                  pt(hx - 3, hy + 9), pt(hx - 7, hy + 2)],
                  outline=False)
        # WAJAH: terang di tulang pipi, gelap di rongga mata. Aturan yang
        # dipakai Grimjam (mask putih) / Kaizen (belang biru): SATU blok
        # terang kecil + SATU blok gelap, bukan gradasi lebar - kalau lebar,
        # di skala hero wajah jadi "topeng merah muda" tanpa fitur.
        poly_free(p["skin_light"], [pt(hx - 5, hy - 1), pt(hx + 6, hy - 1),
                                    pt(hx + 5, hy + 3), pt(hx - 3, hy + 4)],
                  outline=False)
        poly_free(p["skin_shine"], [pt(hx + 1, hy + 1), pt(hx + 5, hy + 1),
                                     pt(hx + 5, hy + 3),
                                     pt(hx + 1, hy + 3)], outline=False)
        # Dahi (terang, dipisah alis gelap) + cavum mata 4 px
        poly_free(p["skin_mid"], [pt(hx - 6, hy - 6), pt(hx + 7, hy - 6),
                                  pt(hx + 7, hy - 4),
                                  pt(hx - 6, hy - 4)], outline=False)
        poly_free(p["skin_darkest"], [pt(hx - 6, hy - 4), pt(hx + 7, hy - 4),
                                      pt(hx + 7, hy + 0), pt(hx - 6, hy + 0)],
                  outline=False)
        # Mata menyala: dua blok + halo ungu. PLUS kedip berkala - satu
        # frame kelopak turun tiap ~4 dtk, cukup untuk membuat unit terasa
        # hidup di lane tanpa mengorbankan satu piksel pun di pose lain.
        blink = ((phase * 0.6) % 4.2) < 0.16
        if blink:
            poly_free(p["skin_dark"], [pt(hx - 6, hy - 4), pt(hx + 7, hy - 4),
                                       pt(hx + 7, hy - 1),
                                       pt(hx - 6, hy - 1)], outline=False)
        # DUA mata, bukan satu bar: tiap mata 2 px dengan batang hidung gelap
        # 2 px di antaranya. Tanpa pemisah itu, wajah terbaca sebagai satu
        # garis putih (keluhan "wajah masih pita terang" di pass sebelumnya).
        for ex in ((hx - 1, hx + 4) if not blink else ()):
            _NS_gornak._aaline(surface, p["eye_mid"], pt(ex, hy - 2.5),
                               pt(ex + 1, hy - 2.5), 2)
            _NS_gornak._aaline(surface, p["eye_glow"], pt(ex, hy - 2.5),
                               pt(ex + 1, hy - 2.5), 1)
        if not blink:
            _NS_gornak._aaline(surface, p["skin_darkest"], pt(hx + 2, hy - 4),
                               pt(hx + 2, hy + 0), 2)   # batang hidung
        ga = _NS_gornak._alpha(85 + (115 if (ward or void) else 0))
        gx, gy = pt(hx + 1.5, hy - 2.5)
        _NS_gornak._aacircle(surface, (*p["eye_light"], ga), (gx, gy), 3)
        _NS_gornak._aacircle(surface, (*p["magic_hot"], ga // 2), (gx, gy), 5)
        # War paint ungu di pipi (sinyal warna tema, terlihat di 1x)
        wp = _NS_gornak._alpha(190)
        _NS_gornak._aaline(surface, (*p["magic_light"], wp), pt(hx - 4, hy + 1),
                           pt(hx - 1, hy + 3), 1)
        _NS_gornak._aaline(surface, (*p["magic_light"], wp), pt(hx - 5, hy + 2),
                           pt(hx - 2, hy + 4), 1)
        # Hidung & mulut
        _NS_gornak._aaline(surface, p["skin_darkest"], pt(hx + 8, hy + 1),
                           pt(hx + 8, hy + 4), 1)
        _NS_gornak._aaline(surface, p["skin_darkest"], pt(hx + 4, hy + 5),
                           pt(hx + 7, hy + 5), 1)

        # Jenggot kepang: hanya RAHANG BAWAH (dulu sampai hy+16 -> menyatu
        # dengan leher & dada jadi satu massa gelap).
        poly_free(p["beard_darkest"], [pt(hx - 5, hy + 5), pt(hx + 7, hy + 5),
                                       pt(hx + 6, hy + 10), pt(hx + 2, hy + 13),
                                       pt(hx - 3, hy + 10)])
        poly_free(p["beard_mid"], [pt(hx - 3, hy + 6), pt(hx + 5, hy + 6),
                                   pt(hx + 4, hy + 9), pt(hx + 2, hy + 11),
                                   pt(hx - 2, hy + 9)], outline=False)
        # Garis gelap di bawah rahang: memisahkan jenggot dari leher/dada,
        # kalau tidak semuanya jadi satu massa coklat.
        _NS_gornak._aaline(surface, p["shadow_deep"], pt(hx - 5, hy + 11),
                           pt(hx + 6, hy + 10), 1)
        poly_free(p["beard_mid"], [pt(hx + 1, hy + 12), pt(hx + 4, hy + 12),
                                   pt(hx + 3, hy + 15)], outline=False)
        for i in range(3):
            _NS_gornak._aaline(surface, p["beard_darkest"],
                               pt(hx - 2 + i * 3, hy + 6),
                               pt(hx - 1 + i * 3, hy + 13), 1)
        dot(p["brass_dark"], hx + 2, hy + 13, 2)
        _NS_gornak._aacircle(surface, p["brass_mid"], pt(hx + 2, hy + 13), 1)

        # Circlet besi + taring pelipis + permata ungu di dahi
        poly_free(p["armor_darkest"], [pt(hx - 8, hy - 7), pt(hx + 8, hy - 7),
                                       pt(hx + 8, hy - 4), pt(hx - 8, hy - 4)])
        poly_free(p["armor_light"], [pt(hx - 7, hy - 6.5), pt(hx + 7, hy - 6.5),
                                     pt(hx + 7, hy - 5),
                                     pt(hx - 7, hy - 5)], outline=False)
        _NS_gornak._aacircle(surface, p["magic_hot"], pt(hx + 6, hy - 6), 1)
        poly_free(p["armor_mid"], [pt(hx - 9, hy - 6), pt(hx - 9, hy - 11),
                                   pt(hx - 7, hy - 6)], outline=False)
        poly_free(p["armor_mid"], [pt(hx + 8, hy - 6), pt(hx + 9, hy - 11),
                                   pt(hx + 7, hy - 6)], outline=False)

    def _draw_gnk_rimlight(surface, pt, f, phase, ward, void):
        """Rim light ungu tipis di tepi yang menghadap cahaya.

        Ini yang paling hilang dari render sebelumnya: semua hero masterwork
        lain punya "sinyal" warna di tepian (Grimjam api, Vex void cyan,
        Kaizen angin biru) sehingga terbaca saat unit bertumpuk. Gornak
        memakai ungu anti-sihir; 1 px saja, tapi di posisi yang tepat
        (puncak bahu, tepi pelat, punggung bilah, ujung boot).
        """
        p = _NS_gornak.PALETTE
        sh = _NS_gornak.SHOULDER_Y
        hy = _NS_gornak.HEAD_Y + int(math.sin(phase * 0.62) * 0.8)
        pulse = 1.0 if (ward or void) else (0.72 + 0.28 * math.sin(phase * 1.8))
        a = _NS_gornak._alpha(150 * pulse)
        col = (*p["magic_light"], a)
        # Puncak krist saja + tepi pelat: garis di bahu tumpang tindih
        # dengan armor_shine pauldron jadi terlihat seperti noda.
        _NS_gornak._aaline(surface, col, pt(-8, hy - 12), pt(2, hy - 13), 1)
        # Tepi pelat dada & sabuk
        _NS_gornak._aaline(surface, col, pt(-11, sh + 1), pt(-11, -5), 1)
        _NS_gornak._aaline(surface, (*p["magic_hot"], a), pt(-12, 1),
                           pt(12, 1), 1)
        # Garis cahaya di lutut & ujung boot
        for sx in (-5, 9):
            _NS_gornak._aaline(surface, col, pt(sx, 22), pt(sx + 1, 30), 1)
            _NS_gornak._aacircle(surface, col, pt(sx + 1, 41), 1)

    def _draw_gnk_arm(surface, pt, poly_free, dot, limb, f, phase, action, ap,
                      shoulder, elbow, grip, blade_angle, blade_len, back=False,
                      ward=False, void=False, surge=False):
        """Lengan 2-tulang + bracer + bilah. Bayangan antar-bagian cukup
        +2 px; outline luar sudah memberi pemisah, jadi tidak perlu tebal."""
        p = _NS_gornak.PALETTE
        base = p["skin_dark"] if back else p["skin_mid"]
        high = p["skin_mid"] if back else p["skin_light"]
        # Satu tingkat lebih berisi daripada pass sebelumnya: di skala hero
        # bilah yang panjang+terang sempat mendominasi sampai lengan terlihat
        # seperti ranting dan pedang seperti menempel sendiri di dada.
        limb(shoulder, elbow, 6 if back else 7, base, high)
        limb(elbow, grip, 5 if back else 6, base, high)
        # Bracer besi: satu blok di tengah lengan bawah
        bx = int(elbow[0] * 0.4 + grip[0] * 0.6)
        by = int(elbow[1] * 0.4 + grip[1] * 0.6)
        poly_free(p["armor_darkest"], [pt(bx - 3, by - 3), pt(bx + 3, by - 3),
                                       pt(bx + 3, by + 3), pt(bx - 3, by + 3)])
        poly_free(p["armor_light"], [pt(bx - 2, by - 2), pt(bx + 1, by - 2),
                                     pt(bx + 1, by + 2), pt(bx - 2, by + 2)],
                  outline=False)
        # Tangan + highlight buku jari: tanpa ini bilah terlihat "menempel"
        # di dada, bukan digenggam.
        dot(p["skin_darkest"], *grip, 3 if back else 4)
        dot(high, *grip, 2 if back else 3)
        if not back:
            kx, ky = pt(grip[0] + 1, grip[1] - 2)
            _NS_gornak._aacircle(surface, p["skin_shine"], (kx, ky), 2)
        _NS_gornak._draw_gnk_blade(surface, pt, f, grip, blade_angle,
                                   blade_len, phase, action, back=back,
                                   ward=ward, void=void, surge=surge)

    def _draw_gnk_blade(surface, pt, f, grip, angle, length, phase, action,
                        back=False, ward=False, void=False, surge=False):
        """Bilah "spellbreaker" melengkung - dihitung dari grip + sudut.

        Dibuat TERANG (nilai tertinggi ke-2 setelah mata) supaya senjata
        terbaca sebagai senjata, bukan tonjolan gelap seperti sebelumnya.
        """
        p = _NS_gornak.PALETTE
        s, c = math.sin(angle), math.cos(angle)
        segs = 6
        curve = 5.0 if not back else 3.0
        centers = []
        for i in range(segs + 1):
            t = i / segs
            bend = curve * (t * t)
            centers.append((grip[0] + s * length * t + c * bend,
                            grip[1] + c * length * t - s * bend))
        n_x, n_y = c, -s
        left, right = [], []
        for i, (x, y) in enumerate(centers):
            t = i / segs
            wd = (3.0 if not back else 2.2) * (1.0 - t) + 0.7 * t
            left.append((x + n_x * wd, y + n_y * wd))
            right.append((x - n_x * wd, y - n_y * wd))
        body = left + right[::-1]
        poly_pts = [pt(*q) for q in body]
        _NS_gornak._poly(surface, p["shadow_deep"],
                         [(q[0] + f, q[1] + 1) for q in poly_pts])
        _NS_gornak._poly(surface, p["blade_mid"], poly_pts)

        def inset(k):
            out = []
            for (x, y) in body:
                dx = (x - grip[0]) * k
                dy = (y - grip[1]) * k
                out.append(pt(int(x - dx), int(y - dy)))
            return out

        _NS_gornak._poly(surface, p["blade_light"], inset(0.22))
        _NS_gornak._poly(surface, p["blade_shine"], inset(0.52))
        # Rune penyedot mana - hanya saat menyerang / skill
        hot = 0.30 + (0.70 if (ward or void or surge or action == "attack")
                      else 0.0)
        glow_a = _NS_gornak._alpha(150 * hot *
                                   (0.8 + 0.2 * math.sin(phase * 2.2)))
        core = [pt(*q) for q in centers]
        if not back:
            for i in range(len(core) - 1):
                _NS_gornak._aaline(surface, (*p["magic_light"], glow_a),
                                   core[i], core[i + 1], 1)
        # Gagang kulit + cross-guard + pommel
        g1 = pt(grip[0] - int(c * 3), grip[1] + int(s * 3))
        g2 = pt(grip[0] + int(c * 3), grip[1] - int(s * 3))
        _NS_gornak._aaline(surface, p["shadow_deep"], (g1[0] + f, g1[1] + 1),
                           (g2[0] + f, g2[1] + 1), 4)
        _NS_gornak._aaline(surface, p["armor_mid"], g1, g2, 2)
        butt = pt(grip[0] - int(s * 6), grip[1] - int(c * 6))
        gx, gy = pt(*grip)
        _NS_gornak._aaline(surface, p["leather_dark"], (gx, gy), butt, 4)
        _NS_gornak._aaline(surface, p["leather_light"], (gx, gy), butt, 1)
        _NS_gornak._aacircle(surface, p["brass_mid"], butt, 2)
        tip = core[-1]
        _NS_gornak._aacircle(surface, (*p["magic_hot"], glow_a), tip, 2)

    # ==================================================================
    # PORTRAIT LOD - material tambahan (Hero Shop / panel)
    # ==================================================================
    def _draw_gnk_weave(surface, pt, f):
        """Tenun kain & grain kulit - HANYA portrait LOD.

        Dither 1-px seperti ini justru jadi noise/kasar setelah jalur hero
        men-smoothscale sprite ke 0.7-0.8, jadi dibatasi ke mode detail.
        """
        p = _NS_gornak.PALETTE
        for i in range(9):
            wx, wy = pt(-8 + (i % 4) * 4, 8 + (i // 4) * 4)
            _NS_gornak._rect(surface, (*p["robe_light"], 90), (wx, wy, 1, 1))
        for i in range(7):
            x0, y0 = -12 + i * 4, -12 + (i % 3) * 6
            _NS_gornak._rect(surface, (*p["skin_shine"], 70),
                             (pt(x0, y0)[0], pt(x0, y0)[1], 1, 1))

    def _draw_gnk_masterwork_details(surface, pt, f, phase, action):
        """Detail frekuensi tinggi; di skala arena tanda-tanda ini hanya
        akan menjadi noise, jadi hanya dinyalakan saat portrait."""
        p = _NS_gornak.PALETTE
        hx = 1 if f > 0 else -1
        cy = _NS_gornak.HEAD_Y + int(math.sin(phase * 0.62) * 0.8)
        # Helai rambut ekstra di atas krist
        for i in range(7):
            bx = hx - 7 + i * 2
            by = cy - 7 - abs(i - 3)
            wx = bx - 3 + int(math.sin(phase * 1.4 + i) * 2)
            _NS_gornak._aaline(surface, p["hair_shine"], pt(bx, by),
                               pt(wx, by - 10 - (i % 3)), 1)
        # Serat jenggot
        for i in range(4):
            _NS_gornak._aaline(surface, p["beard_mid"],
                               pt(hx - 4 + i * 2, cy + 5),
                               pt(hx - 3 + i * 2, cy + 12), 1)
        # Alis tebal
        _NS_gornak._aaline(surface, p["beard_darkest"], pt(hx - 1, cy - 4),
                           pt(hx + 6, cy - 5), 1)
        # Grain kulit pada bahu & dada
        for i in range(10):
            dx = -9 + (i % 5) * 4
            dy = -17 + (i // 5) * 8
            _NS_gornak._aaline(surface, (*p["skin_shine"], 110), pt(dx, dy),
                               pt(dx + 1, dy), 1)
        # Otot leher
        _NS_gornak._aaline(surface, p["skin_dark"], pt(hx - 4, -20),
                           pt(hx - 1, -16), 1)
        # Jahitan jubah & loincloth
        for yy in (8, 13, 18):
            _NS_gornak._aaline(surface, (*p["robe_edge"], 150), pt(-15, yy),
                               pt(-10, yy + 1), 1)
        for xx in (-5, 0, 5):
            _NS_gornak._aaline(surface, (*p["robe_light"], 120), pt(xx, 8),
                               pt(xx + 1, 23), 1)
        # Tato rune anti-sihir
        for i in range(4):
            _NS_gornak._aaline(surface, (*p["magic_light"], 140),
                               pt(-12 + i * 2, -13 + i * 6),
                               pt(-10 + i * 2, -11 + i * 6), 1)
        # Ukiran pelat & paku pauldron
        _NS_gornak._aaline(surface, (*p["armor_shine"], 165), pt(-9, -15),
                           pt(0, -14), 1)
        _NS_gornak._aaline(surface, (*p["armor_shine"], 165), pt(-9, -11),
                           pt(-1, -10), 1)
        for sx, sy in ((13, -22), (15, -19), (11, -18), (-13, -21)):
            _NS_gornak._aacircle(surface, (*p["armor_shine"], 150), pt(sx, sy),
                                 1)
        # Ringgit gagang & garis hamon bilah
        for i in range(5):
            t = i / 5
            _NS_gornak._aaline(surface, (*p["blade_hamon"], 170),
                               pt(13 + int(t * 12), 3 - int(t * 15)),
                               pt(14 + int(t * 12), 4 - int(t * 15)), 1)

    def _draw_footfall_dust(surface, x, y, facing, phase):
        """Kepul debu di tapak yang mendarat (deterministik dari phase)."""
        p = _NS_gornak.PALETTE
        contact = abs(math.sin(phase * 1.15))
        if contact > 0.72:
            return
        gy = y + _NS_gornak.GROUND_DY
        k = _NS_gornak._s
        for side in (-1, 1):
            for i in range(3):
                t = (contact + i * 0.3) % 1.0
                a = _NS_gornak._alpha(150 * (1.0 - t) * (0.72 - contact))
                if a <= 0:
                    continue
                px = x + side * k(7 + i * 2 + t * 5) + facing * k(t * 4)
                py = gy - k(t * 5)
                _NS_gornak._aacircle(surface, (*p["robe_edge"], a), (px, py),
                                     max(1, k(2 - t)))
                _NS_gornak._rect(surface, (*p["white"], a // 2),
                                 (px, py, 1, 1))

    # ==================================================================
    # EFEK DASAR - ditundukan pada karakter
    # ==================================================================
    def _draw_shadow(surface, x, y):
        """Bayangan kontak tunggal yang lembek (base_boss menggambar satu
        lagi; ini dipertipis supaya tidak jadi dua piringan hitam)."""
        p = _NS_gornak.PALETTE
        K = _NS_gornak.SCALE
        bw, bh = int(60 * K), int(18 * K)
        sh = pygame.Surface((bw, bh), pygame.SRCALPHA)
        for w, h, a in ((int(42 * K), int(10 * K), 70),
                        (int(30 * K), int(7 * K), 90),
                        (int(18 * K), int(4 * K), 110)):
            _NS_gornak._ellipse(sh, (0, 0, 0, a),
                                (bw // 2 - w // 2, bh // 2 - h // 2, w, h))
        _NS_gornak._ellipse(sh, (*p["magic_darkest"], 60),
                            (int(6 * K), int(3 * K), int(48 * K), int(12 * K)))
        # Titik kontak per telapak: bikin badan "menekan" tanah, bukan
        # mengapung di atas elips umum.
        for side in (-1, 1):
            fx = bw // 2 + int(side * 9 * K)
            _NS_gornak._ellipse(sh, (0, 0, 0, 130),
                                (fx - int(5 * K), int(bh * 0.62),
                                 int(10 * K), int(4 * K)))
        surface.blit(sh, (int(x) - bw // 2, int(y) - bh // 2))

    def _draw_anti_magic_field(surface, x, y, phase, skill):
        """Cahaya lembut MENEMPEL badan + percikan mengorbit siluet."""
        p = _NS_gornak.PALETTE
        pulse = 1.0 if skill else math.sin(phase * 0.7) * 0.25 + 0.72
        K = _NS_gornak.SCALE
        # Cakram cahaya di belakang badan. Kaizen punya piringan biru, Vex
        # cyan, Grimjam oranye - itu yang membuat mereka "menyala" di lane
        # walau sprite-nya kecil. Pass sebelumnya alpha Gornak cuma 34-55
        # sehingga hilang sama sekali di skala hero; sekarang 78-120 dengan
        # radius lebih rapat ke badan (biar tidak jadi kabut lebar).
        glow = pygame.Surface((int(80 * K), int(96 * K)), pygame.SRCALPHA)
        cx, cy = int(40 * K), int(50 * K)
        for rx, ry, col, a in ((int(30 * K), int(38 * K), "magic_darkest", 78),
                               (int(23 * K), int(30 * K), "magic_dark", 96),
                               (int(16 * K), int(22 * K), "magic_mid", 120)):
            _NS_gornak._ellipse(glow, (*p[col], _NS_gornak._alpha(a * pulse)),
                                (cx - rx, cy - ry, rx * 2, ry * 2))
        _NS_gornak._ellipse(glow, (*p["magic_light"],
                                   _NS_gornak._alpha(70 * pulse)),
                            (cx - int(16 * K), cy - int(22 * K),
                             int(32 * K), int(44 * K)), 1)
        surface.blit(glow, (int(x) - cx, int(y) - cy + 8))

        n = 6
        for i in range(n):
            ang = ((phase * 0.35 + i / n) % 1.0) * math.tau
            r = _NS_gornak._s(20) + int(math.sin(phase * 1.3 + i * 2) * 3)
            sx = x + int(math.cos(ang) * r * 1.25)
            sy = y + 2 + int(math.sin(ang) * r * 0.8)
            a = _NS_gornak._alpha(120 + 80 * math.sin(phase * 3 + i))
            _NS_gornak._aacircle(surface, (*p["magic_mid"], a), (sx, sy), 2)
            _NS_gornak._aacircle(surface, (*p["magic_shine"], a), (sx, sy), 1)

    def _draw_ground_rune(surface, x, y, phase, skill):
        """Cincin rune di bawah kaki - kecil TAPI terang.

        Dulu 110 px lebarnya dan lebih terang dari badan. Sekarang
        seukuran telapak (radius ~29 px) dengan alpha tinggi: keluarga hero
        masterwork (kaizen / vex / grimjam) punya cincin tanah yang jelas
        terbaca di lane, dan versi redup sebelumnya membuat Gornak terlihat
        "mati" di samping mereka.
        """
        p = _NS_gornak.PALETTE
        pulse = math.sin(phase * 1.1) * 0.25 + 0.75
        gy = y + _NS_gornak.GROUND_DY
        bright = 1.15 if skill else 0.95
        rw, rh = _NS_gornak._s(22), _NS_gornak._s(6)
        _NS_gornak._ellipse(surface,
                            (*p["magic_darkest"],
                             _NS_gornak._alpha(150 * pulse * bright)),
                            (x - rw, gy - rh, rw * 2, rh * 2), 2)
        rw2, rh2 = _NS_gornak._s(15), _NS_gornak._s(4)
        _NS_gornak._ellipse(surface,
                            (*p["magic_mid"],
                             _NS_gornak._alpha(140 * pulse * bright)),
                            (x - rw2, gy - rh2, rw2 * 2, rh2 * 2), 1)
        t0, t1 = _NS_gornak._s(18), _NS_gornak._s(24)
        ty0, ty1 = _NS_gornak._s(5), _NS_gornak._s(6)
        for i in range(6):
            ang = phase * 0.4 + i * math.tau / 6
            _NS_gornak._aaline(
                surface,
                (*p["magic_light"], _NS_gornak._alpha(170 * pulse * bright)),
                (x + int(math.cos(ang) * t0), gy + int(math.sin(ang) * ty0)),
                (x + int(math.cos(ang) * t1), gy + int(math.sin(ang) * ty1)), 1)
        # Ring dalam tipis: bikin cincin terbaca sebagai "lambang", bukan
        # elips kabur, tanpa menambah lebar tapak.
        irw, irh = _NS_gornak._s(11), _NS_gornak._s(3)
        _NS_gornak._ellipse(surface,
                            (*p["magic_light"],
                             _NS_gornak._alpha(150 * pulse * bright)),
                            (x - irw, gy - irh, irw * 2, irh * 2), 1)
        _NS_gornak._aacircle(surface, (*p["magic_shine"],
                                       _NS_gornak._alpha(200 * pulse)),
                             (int(x), int(gy)), 2)
        if skill in ("e", "r"):
            ew, eh = _NS_gornak._s(26), _NS_gornak._s(7)
            _NS_gornak._ellipse(
                surface, (*p["magic_hot"], _NS_gornak._alpha(120 * pulse)),
                (x - ew, gy - eh, ew * 2, eh * 2), 1)

    # ==================================================================
    # SLASH ARC - mengikuti lintasan ujung bilah yang sebenarnya
    # ==================================================================
    def _draw_crescent_slash(surface, x, y, facing, phase, progress):
        """Pita slash dari trail UJUNG BILAH (bukan busur titik melayang)."""
        if progress < 0.24 or progress > 0.92:
            return
        p = _NS_gornak.PALETTE
        lean, root_y = _NS_gornak._rig_shift("attack", phase, progress)

        def scr(lx, ly):
            return _NS_gornak._local_to_screen(x, y, facing, lean, root_y,
                                               lx, ly)

        def tip_at(ap):
            return scr(*_NS_gornak._tip_local("attack", phase, ap))

        steps = 7
        trail = []
        for i in range(steps):
            t = i / (steps - 1)
            trail.append(tip_at(max(0.0, min(1.0, progress - 0.30 + t * 0.30))))
        pivot = scr(*_NS_gornak._front_grip_local("attack", progress, phase))
        fade = 1.0 - max(0.0, (progress - 0.70) / 0.22)
        alpha = _NS_gornak._alpha(230 * fade)
        if alpha <= 0:
            return
        for col, off, mul in (("magic_darkest", 8, 0.62),
                              ("magic_mid", 4, 0.9),
                              ("magic_shine", 1, 1.0)):
            outer, inner = [], []
            for i, q in enumerate(trail):
                t = i / (steps - 1)
                # Lebar pita memuncak dekat bilah dan menipis ke ekor,
                # supaya trail terbaca menyatu dengan senjata (versi
                # seragam menyisakan "serpihan" terpisah di ujung arc).
                w = max(0.5, (1 - abs(t - 0.8)) * off * (0.35 + 0.65 * t))
                vx, vy = q[0] - pivot[0], q[1] - pivot[1]
                ln = math.hypot(vx, vy) or 1.0
                nx, ny = -vy / ln, vx / ln
                outer.append((q[0] + nx * w, q[1] + ny * w))
                inner.append((q[0] - nx * w * 0.55, q[1] - ny * w * 0.55))
            _NS_gornak._poly(surface,
                              (*p[col], _NS_gornak._alpha(alpha * mul)),
                              outer + inner[::-1])
        if 0.40 <= progress <= 0.62:
            tip = trail[-1]
            for i in range(5):
                ang = -math.pi / 2 + i * math.pi / 4
                ex = tip[0] + int(math.cos(ang) * 7)
                ey = tip[1] + int(math.sin(ang) * 7)
                _NS_gornak._aaline(surface, (*p["magic_hot"], alpha), tip,
                                   (ex, ey), 1)

    # ==================================================================
    # SKILL Q - MANA BREAK (proc di ujung bilah, bolt ke target)
    # ==================================================================
    def _draw_manabreak_ground(surface, boss, x, y, timer, phase):
        """Konsentrasi energi di UJUNG BILAH sebelum bolt lepas."""
        p = _NS_gornak.PALETTE
        duration = _NS_gornak.SKILL_DUR["q"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress > 0.34:
            return
        t = progress / 0.34
        tx, ty = _NS_gornak._tip_screen(boss, x, y)
        r = 3 + int(t * 7)
        for k in range(r + 3, 0, -1):
            a = _NS_gornak._alpha(200 * (r + 3 - k) / (r + 3) * (0.4 + t))
            _NS_gornak._aacircle(surface, (*p["magic_dark"], a), (tx, ty), k)
        for col, rr in (("magic_mid", r), ("magic_light", max(1, r - 2)),
                        ("magic_shine", max(1, r - 4))):
            _NS_gornak._aacircle(surface, p[col], (tx, ty), rr)
        for i in range(5):
            ang = phase * 4 + i * math.tau / 5
            sx = tx + int(math.cos(ang) * (r + 4))
            sy = ty + int(math.sin(ang) * (r + 4))
            _NS_gornak._aaline(surface, (*p["magic_hot"], 190), (sx, sy),
                               (tx, ty), 1)

    def _draw_manabreak_foreground(surface, boss, x, y, timer, phase):
        """Bolt mana dari ujung bilah ke target + impact rune retak."""
        p = _NS_gornak.PALETTE
        duration = _NS_gornak.SKILL_DUR["q"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress <= 0.30:
            return
        t = (progress - 0.30) / 0.70
        sx, sy = _NS_gornak._tip_screen(boss, x, y)
        tx, ty = _NS_gornak._target_position(boss, x, y)
        bx, by = int(sx + (tx - sx) * t), int(sy + (ty - sy) * t)

        for i in range(9):
            tt = max(0.0, t - i * 0.05)
            px = int(sx + (tx - sx) * tt)
            py = int(sy + (ty - sy) * tt)
            a = _NS_gornak._alpha(230 - i * 25)
            size = max(1, 6 - i)
            for col, off in (("magic_darkest", size + 1), ("magic_mid", size),
                             ("magic_light", max(1, size - 2))):
                if off > 0:
                    _NS_gornak._aacircle(surface, (*p[col], a), (px, py), off)
            _NS_gornak._rect(surface, (*p["magic_hot"], a), (px, py, 1, 1))

        for col, rr in (("magic_dark", 8), ("magic_mid", 6),
                        ("magic_light", 4), ("magic_shine", 2),
                        ("white", 1)):
            _NS_gornak._aacircle(surface, p[col], (bx, by), rr)
        for i in range(4):
            ang = phase * 5 + i * math.pi / 2
            r1 = 12 + int(3 * math.sin(phase * 6 + i))
            _NS_gornak._aaline(surface, (*p["magic_light"], 200),
                               (bx + int(math.cos(ang) * 7),
                                by + int(math.sin(ang) * 7)),
                               (bx + int(math.cos(ang) * r1),
                                by + int(math.sin(ang) * r1)), 1)

        if t > 0.86:
            st = (t - 0.86) / 0.14
            radius = int(9 + st * 20)
            a = _NS_gornak._alpha(240 * (1 - st))
            _NS_gornak._aacircle(surface, (*p["magic_darkest"], a), (tx, ty),
                                 radius + 2, 3)
            _NS_gornak._aacircle(surface, (*p["magic_mid"], a), (tx, ty),
                                 max(1, radius - 4), 2)
            for i in range(8):
                ang = i * math.pi / 4 + st * 0.5
                ex = tx + int(math.cos(ang) * radius)
                ey = ty + int(math.sin(ang) * radius * 0.8)
                _NS_gornak._aaline(surface, (*p["magic_hot"], a), (tx, ty),
                                   (ex, ey), 2 if i % 2 == 0 else 1)
                _NS_gornak._rect(surface, (*p["magic_shine"], a),
                                 (ex, ey, 1, 1))

    # ==================================================================
    # SKILL W - BLINK (lingkaran berangkat/tiba kecil)
    # ==================================================================
    def _draw_blink_ground(surface, boss, x, y, timer, phase):
        p = _NS_gornak.PALETTE
        duration = _NS_gornak.SKILL_DUR["w"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        gy = y + _NS_gornak.GROUND_DY
        if progress < 0.5:
            t = progress / 0.5
            r = int(9 + t * 13)
            a = _NS_gornak._alpha(200 * (1 - t))
        else:
            t = (progress - 0.5) / 0.5
            r = int(22 - t * 11)
            a = _NS_gornak._alpha(200 * t)
        if a <= 0:
            return
        _NS_gornak._ellipse(surface, (*p["magic_mid"], a),
                            (x - r, gy - r // 3, r * 2, max(3, r // 2)), 1)
        _NS_gornak._ellipse(surface, (*p["magic_hot"], a),
                            (x - r // 2, gy - r // 6, r, max(2, r // 4)), 1)
        for i in range(7):
            ang = phase * 2 + i * math.tau / 7
            _NS_gornak._rect(surface, (*p["magic_shine"], a),
                             (x + int(math.cos(ang) * (r + 3)),
                              gy + int(math.sin(ang) * max(1, r // 4)), 1, 1))

    # ==================================================================
    # SKILL E - COUNTERSPELL (kubah memeluk badan, bukan bola raksasa)
    # ==================================================================
    def _draw_counterspell_foreground(surface, boss, x, y, timer, phase):
        p = _NS_gornak.PALETTE
        duration = _NS_gornak.SKILL_DUR["e"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        grow = 1.0
        if progress < 0.16:
            grow = 0.55 + (progress / 0.16) * 0.45
        elif progress > 0.86:
            grow = 1.0 - (progress - 0.86) / 0.14 * 0.35
        rx = int(_NS_gornak._s(24) * grow)
        ry = int(_NS_gornak._s(33) * grow)
        cx0, cy0 = int(x), int(y) - 3
        breath = math.sin(phase * 2.4) * 1.2
        pts = []
        for i in range(6):
            ang = -math.pi / 2 + i * math.tau / 6 + phase * 0.25
            pts.append((cx0 + int(math.cos(ang) * (rx + breath)),
                        cy0 + int(math.sin(ang) * (ry + breath))))
        fade = 1.0 - max(0.0, (progress - 0.9)) * 8
        a_main = _NS_gornak._alpha(190 * fade)
        x0 = min(q[0] for q in pts) - 4
        y0 = min(q[1] for q in pts) - 4
        w = max(q[0] for q in pts) - x0 + 8
        h = max(q[1] for q in pts) - y0 + 8
        fill = pygame.Surface((max(4, w), max(4, h)), pygame.SRCALPHA)
        sh = [(q[0] - x0, q[1] - y0) for q in pts]
        _NS_gornak._poly(fill, (*p["magic_darkest"],
                                _NS_gornak._alpha(46 * grow)), sh)
        _NS_gornak._poly(fill, (*p["magic_dark"], _NS_gornak._alpha(52 * grow)),
                         sh[1:-1] + [sh[0]])
        surface.blit(fill, (x0, y0))
        for i in range(6):
            q, r2 = pts[i], pts[(i + 1) % 6]
            _NS_gornak._aaline(surface, (*p["magic_mid"], a_main), q, r2, 2)
            _NS_gornak._aaline(surface, (*p["magic_shine"], a_main), q, r2, 1)
            _NS_gornak._aacircle(surface, (*p["magic_hot"], a_main), q, 2)
            _NS_gornak._rect(surface, (*p["white"], a_main), (q[0], q[1], 1, 1))
            ang = i * math.tau / 6 + phase * 0.9
            _NS_gornak._aaline(
                surface, (*p["magic_light"], _NS_gornak._alpha(a_main * 0.7)),
                q, (q[0] + int(math.cos(ang) * 5), q[1] + int(math.sin(ang) * 5)),
                1)

    # ==================================================================
    # SKILL R - MANA VOID
    # ==================================================================
    def _draw_manavoid_ground(surface, boss, x, y, timer, phase):
        p = _NS_gornak.PALETTE
        tx, ty = _NS_gornak._target_position(boss, x, y)
        duration = _NS_gornak.SKILL_DUR["r"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.5:
            t = progress / 0.5
            r = int(28 * t)
            a = _NS_gornak._alpha(190 * t)
            _NS_gornak._ellipse(surface, (*p["magic_darkest"], a),
                                (tx - r, ty - r // 3 + 6, r * 2,
                                 max(3, r * 2 // 3)), 2)
            _NS_gornak._ellipse(surface, (*p["magic_mid"], a),
                                (tx - r + 4, ty - r // 3 + 8, r * 2 - 8,
                                 max(1, r * 2 // 3 - 8)), 1)
        else:
            t = (progress - 0.5) / 0.5
            r = int(28 + t * 20)
            a = _NS_gornak._alpha(220 * (1 - t))
            _NS_gornak._ellipse(surface, (*p["magic_darkest"], a),
                                (tx - r, ty - r // 3 + 6, r * 2,
                                 max(3, r * 2 // 3)), 2)
        if progress < 0.62:
            t = min(1.0, progress / 0.62)
            for i in range(6):
                ang = i * math.tau / 6 + 0.3
                _NS_gornak._aaline(
                    surface, (*p["magic_mid"], _NS_gornak._alpha(180 * t)),
                    (tx + int(math.cos(ang) * 10 * t),
                     ty + 8 + int(math.sin(ang) * 4 * t)),
                    (tx + int(math.cos(ang) * 32 * t),
                     ty + 8 + int(math.sin(ang) * 11 * t)), 1)

    def _draw_manavoid_foreground(surface, boss, x, y, timer, phase):
        p = _NS_gornak.PALETTE
        tx, ty = _NS_gornak._target_position(boss, x, y)
        duration = _NS_gornak.SKILL_DUR["r"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        action = "void"
        if progress < 0.50:
            t = progress / 0.5
            # Lengan void: energi DARI KEDUA TANGAN ke target
            for back in (False, True):
                grip = (_NS_gornak._front_grip_local(action, 0.0, phase)
                        if not back else
                        _NS_gornak._back_grip_local(action, 0.0, phase))
                hx, hy = _NS_gornak._local(boss, x, y, action, phase, 0.0,
                                           *grip)
                _NS_gornak._aaline(surface,
                                   (*p["magic_dark"], _NS_gornak._alpha(110 * t)),
                                   (hx, hy), (tx, ty), 3)
                _NS_gornak._aaline(surface,
                                   (*p["magic_mid"], _NS_gornak._alpha(150 * t)),
                                   (hx, hy), (tx, ty), 1)
                for i in range(4):
                    tt = (phase * 0.9 + i * 0.25) % 1.0
                    px = int(hx + (tx - hx) * tt)
                    py = int(hy + (ty - hy) * tt)
                    a = _NS_gornak._alpha(200 * (1 - abs(tt - 0.5) * 1.3) * t)
                    if a > 0:
                        _NS_gornak._aacircle(surface, (*p["magic_light"], a),
                                             (px, py), 2)
                        _NS_gornak._rect(surface, (*p["magic_shine"], a),
                                         (px, py, 1, 1))
            # Motes mana TERSEDOT dari target ke dada Gornak - tanpa ini R
            # cuma "bola di musuh"; arah aliran yang jelas membuat skill
            # terbaca sebagai pencurian mana.
            chest = _NS_gornak._local(boss, x, y, action, phase, 0.0,
                                      0, _NS_gornak.SHOULDER_Y + 4)
            for i in range(6):
                tt = (phase * 0.7 + i / 6.0) % 1.0
                mx = int(tx + (chest[0] - tx) * tt)
                my = int(ty + (chest[1] - ty) * tt - math.sin(tt * math.pi) * 7)
                a = _NS_gornak._alpha(210 * (1 - abs(tt - 0.5) * 1.2) * t)
                if a > 0:
                    _NS_gornak._aacircle(surface, (*p["magic_light"], a),
                                         (mx, my), 2)
                    _NS_gornak._rect(surface, (*p["magic_shine"], a),
                                     (mx, my, 1, 1))
            core = int(5 + t * 6)
            for r in range(core + 2, 0, -1):
                a = _NS_gornak._alpha(235 * (core + 2 - r) / (core + 2))
                _NS_gornak._aacircle(surface, (*p["magic_darkest"], a),
                                     (tx, ty), r)
            _NS_gornak._aacircle(surface, p["magic_mid"], (tx, ty), core)
            _NS_gornak._aacircle(surface, p["magic_hot"], (tx, ty),
                                 max(1, core - 3))
            for i in range(3):
                ang = phase * 3 + i * math.tau / 3
                r = 9 + int(t * 7)
                _NS_gornak._aaline(surface, (*p["magic_light"], 210),
                                   (tx + int(math.cos(ang) * r * 0.4),
                                    ty + int(math.sin(ang) * r * 0.4)),
                                   (tx + int(math.cos(ang) * r),
                                    ty + int(math.sin(ang) * r)), 1)
        elif progress < 0.68:
            t = (progress - 0.50) / 0.18
            intensity = math.sin(t * math.pi)
            r = int(18 + t * 26)
            a = _NS_gornak._alpha(240 * intensity)
            _NS_gornak._aacircle(surface, (*p["magic_darkest"], a), (tx, ty),
                                 r + 3, 4)
            _NS_gornak._aacircle(surface, (*p["magic_dark"], a), (tx, ty), r, 3)
            _NS_gornak._aacircle(surface, (*p["magic_mid"], a), (tx, ty),
                                 max(1, r - 6), 2)
            _NS_gornak._aacircle(surface, (*p["magic_shine"], a), (tx, ty),
                                 max(1, int(r * 0.35)))
            for i in range(12):
                ang = i * math.tau / 12
                ex = tx + int(math.cos(ang) * (r + 4))
                ey = ty + int(math.sin(ang) * (r + 4) * 0.85)
                _NS_gornak._aaline(surface, (*p["magic_hot"], a), (tx, ty),
                                   (ex, ey), 2 if i % 3 == 0 else 1)
        else:
            t = (progress - 0.68) / 0.32
            for i in range(10):
                tt = (phase * 0.5 + i * 0.1) % 1.0
                px = tx + int(math.sin(phase * 1.4 + i) * (14 + i))
                py = ty - int(tt * 30)
                a = _NS_gornak._alpha(200 * (1 - t) * (1 - tt))
                if a > 0:
                    _NS_gornak._aacircle(surface, (*p["magic_dark"], a),
                                         (px, py), 3)
                    _NS_gornak._aacircle(surface, (*p["magic_mid"], a),
                                         (px, py), 2)
                    _NS_gornak._rect(surface, (*p["magic_shine"], a),
                                     (px, py, 1, 1))
        # Rim violet di badan saat mengisi (badan tetap jadi subjek)
        rim = _NS_gornak._alpha(110 * min(1.0, progress * 3))
        rw, rh = _NS_gornak._s(15), _NS_gornak._s(21)
        _NS_gornak._ellipse(surface, (*p["magic_light"], rim),
                            (int(x) - rw, int(y) - rh - _NS_gornak.LIFT,
                             rw * 2, rh * 2 + _NS_gornak._s(2)), 1)

# ====================================================================
# MORGATH (ARC WARDEN) - Mini Boss
# ====================================================================
import math
import pygame


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
            cr = int(4 + t * 6)
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
            _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_darkest"], (bx, by), 9)
            _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_dark"], (bx, by), 7)
            _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_mid"], (bx, by), 5)
            _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_light"], (bx, by), 3)
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
                radius = int(12 + st * 26)
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
            pygame.draw.ellipse(surface, (*_NS_morgath.PALETTE["flux_darkest"], 200),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_morgath.PALETTE["flux_dark"], 180),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_morgath.PALETTE["flux_mid"], 140),
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
                                  (wx, wy), 4)
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["flux_mid"], alpha),
                                  (wx, wy - 1), 3)
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["flux_light"], alpha),
                                  (wx, wy - 1), 2)
            pygame.draw.rect(surface, (*_NS_morgath.PALETTE["flux_hot"], alpha),
                             (wx, wy - 1, 1, 1))

        # Central bubbling core
        core_pulse = math.sin(phase * 3) * 0.4 + 0.6
        for cr in range(6, 0, -1):
            alpha = _NS_morgath._alpha(200 * (6 - cr) / 6 * core_pulse)
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["flux_mid"], alpha),
                                  (tx, ty), cr)
        _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["flux_light"], (tx, ty), 2)

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
            alpha = _NS_morgath._alpha(220 * pulse - i * 50)
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
            alpha = _NS_morgath._alpha(200 * pulse - i * 60)
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["flux_mid"], alpha),
                                  (x, y + 42), r + i * 2, 2)

        # Clone spawn ring (offset)
        if progress > 0.2:
            clone_offset = -facing * 40
            clone_alpha_mult = min(1.0, (progress - 0.2) / 0.2)
            for i in range(2):
                alpha = _NS_morgath._alpha(200 * pulse * clone_alpha_mult - i * 60)
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
        alpha_val = int(180 * spawn_t)

        clone_offset = -facing * 40
        clone_x = x + clone_offset

        # Draw clone body (rig masterwork, pose idle) ke buffer rig
        clone_surf = pygame.Surface((_NS_morgath.RIG_W, _NS_morgath.RIG_H),
                                    pygame.SRCALPHA)
        _NS_morgath._draw_mor_rig(clone_surf, _NS_morgath.RIG_OX,
                                  _NS_morgath.RIG_OY, facing, phase,
                                  "idle", 0.0, False)

        # Tint clone slightly blue
        tint = pygame.Surface((_NS_morgath.RIG_W, _NS_morgath.RIG_H),
                              pygame.SRCALPHA)
        tint.fill((80, 130, 220, 60))
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
# DRAKAR (AXE) - PROCEDURAL MASTERWORK
# ====================================================================
# Rebuild total (para dengan gornak/morgath): SATU bone rig 2D berlapis.
#
# Drakar lama ditumpuk dari body-part statis (_draw_drk_body/_legs/_head):
# badan kotak yang menyatu, kepala gumpalan, dan kapak "kertas" yang tidak
# pernah tersambung ke tangan. Sekarang:
#   * 100% prosedural - tanpa PNG / sprite sheet.
#   * Semua bagian lahir dari SENDI di ruang lokal (y=0 = pinggul);
#     kaki terpatok tanah (ptg), badan ikut bob/lean (pt).
#   * Kapak dua tangan: kedua lengan menempel ke TITIK DI GAGANG yang
#     dihitung dari sudut pose -> kapak tidak pernah lepas dari tangan.
#   * Sudut kapak DITABEL per pose (bukan diturunkan dari lengan) supaya
#     bilah tidak pernah menyayat badannya sendiri.
#   * Outline siluet gelap 1 px (4 arah) -> unit tetap terpisah saat
#     bertumpuk di lane.
#   * LOD portrait: efek tanah/aura dibuang, konten dipusatkan ke bbox.
#   * FX (cleave trail, helix, roar, culling) memakai pose yang SAMA
#     dengan badan lewat _resolve_pose + _tip_screen.
#
# Regresi: tools/test_drakar_masterwork.py,
# sheet   : tools/_shot_drakar_masterwork.py
# ====================================================================
import math
import pygame


class _NS_drakar:
    """Namespace drakar - axe berserker mini boss (procedural masterwork).

    "The Might of the Red Mist": berserker merah terbesar di keluarga
    mini boss (rujukan H138). Sinyal warna keluarga: DARAH & EMBER
    (crimson/oranye) - sama seperti Grimjam (api) / Vex (void cyan),
    supaya terbaca dari jauh. Focal point: mata amber menyala + kapak
    perang dua tangan yang selalu terbaca sebagai senjata.
    """

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    # ------------------------------------------------------------------
    # KALIBRASI KELUARGA (diukur dari render, alpha >= 100):
    #   boss 1x : morgath H82/W120, drakar H138/W190, abaddon H122/W150
    # Badan padat baru menarget ~H130-140 (boss terbesar se-level),
    # rasio W/H ~1.0 lewat kapak-di-bahu + pauldron duri + pelt.
    # ------------------------------------------------------------------
    SCALE = 1.10
    # Jangkar boss = pusat hitbox; LIFT menurunkan badan sedikit supaya
    # dagu tidak menempel ke HP bar (y-r-15..y-r-7, r=32).
    LIFT = 6
    # Telapak dalam RUANG LOKAL; garis tanah dunia diturunkan dari sini
    # supaya bayangan, rune tanah, dan telapak tidak pernah saling lepas.
    FEET_DY = 48
    GROUND_DY = int(round(FEET_DY * SCALE)) - LIFT        # ~ 47

    # Buffer rig: dibatasi dari extents TERUKUR semua pose (idle/walk/
    # attack/4 stance skill, dua LOD) + margin 4 px (outline digambar di
    # luar buffer, jadi tidak dihitung). Dikunci oleh
    # tools/test_drakar_masterwork.py.
    RIG_W, RIG_H = 198, 184
    RIG_OX, RIG_OY = 99, 118

    # Bidang acuan pass cahaya TETAP di dalam buffer (alasan sama dengan
    # GRAD_BOX gornak: kalau ikut bbox, arah cahaya bergeser tiap ganti
    # pose dan terbaca sebagai lampu berkedip).
    GRAD_BOX = (RIG_OX - 46, RIG_OY - 66, 92, 118)

    # Durasi status skill (frame) - HARUS sama dengan active_skill_timer
    # yang diisi AI boss (bosses/base_boss.py: q=90 w=45 e=60 r=60) dan
    # skill hero (hero_skills/_bundle.py). Dikunci oleh
    # tools/test_drakar_masterwork.py.
    SKILL_DUR = {"q": 90, "w": 45, "e": 60, "r": 60}

    # Penanda "sedang di-render ke canvas hero" (lane). Dipasang
    # per-frame oleh draw_drakar, dipakai _draw_drk_rig_at untuk memutuskan
    # siapa yang mengerjakan pass cahaya (hindari rim dobel di lane).
    class _HERO_LANE:
        v = False

    PALETTE = {
        # Kulit merah bata (cahaya dari depan-atas)
        "skin_darkest": (28, 7, 10),
        "skin_dark": (72, 16, 19),
        "skin_mid": (122, 32, 28),
        "skin_light": (172, 56, 42),
        "skin_shine": (216, 100, 66),

        # Rambut / jenggot hitam kebiruan
        "hair_darkest": (7, 6, 10),
        "hair_dark": (26, 22, 30),
        "hair_mid": (52, 46, 58),
        "hair_light": (94, 84, 96),
        "hair_shine": (134, 124, 138),

        # Kulit (leather) cokelat gelap
        "leather_darkest": (19, 11, 6),
        "leather_dark": (52, 30, 17),
        "leather_mid": (92, 60, 36),
        "leather_light": (138, 98, 62),
        "leather_edge": (178, 132, 84),

        # Zirah besi gelap
        "armor_darkest": (13, 11, 16),
        "armor_dark": (40, 36, 48),
        "armor_mid": (84, 78, 92),
        "armor_light": (138, 130, 144),
        "armor_shine": (204, 198, 212),

        # Bilah kapak (baja)
        "blade_darkest": (15, 12, 20),
        "blade_dark": (50, 44, 60),
        "blade_mid": (112, 104, 126),
        "blade_light": (184, 176, 198),
        "blade_shine": (242, 236, 252),

        # Darah / rage (sinyal warna tema)
        "blood_darkest": (56, 8, 10),
        "blood_dark": (142, 24, 20),
        "blood_mid": (218, 52, 32),
        "blood_light": (252, 106, 56),
        "blood_hot": (255, 172, 112),
        "blood_shine": (255, 214, 168),

        # Kabut rage (aura)
        "mist_darkest": (44, 6, 8),
        "mist_dark": (116, 18, 18),
        "mist_mid": (192, 40, 34),
        "mist_light": (238, 84, 52),
        "mist_shine": (255, 152, 110),

        # Mata amber berserker
        "eye_dark": (92, 32, 8),
        "eye_mid": (214, 102, 22),
        "eye_light": (255, 184, 62),
        "eye_glow": (255, 242, 190),

        # Kuningan
        "brass_dark": (72, 46, 16),
        "brass_mid": (148, 102, 34),
        "brass_light": (208, 162, 74),

        # Tulang (tanduk helm, gesper tengkorak)
        "bone_darkest": (50, 42, 34),
        "bone_dark": (106, 94, 74),
        "bone_mid": (170, 156, 126),
        "bone_light": (224, 214, 184),

        # Rune tanah
        "rune_dark": (34, 6, 10),
        "rune_mid": (166, 30, 30),
        "rune_light": (234, 72, 56),
        "rune_shine": (255, 142, 110),

        # Debu langkah
        "dust": (118, 86, 64),

        "shadow": (0, 0, 0),
        "shadow_deep": (3, 1, 2),
        "white": (255, 255, 255),
    }

    # ------------------------------------------------------------------
    # HELPER GAMBAR (aman terhadap warna rgba & backend tanpa aacircle)
    # ------------------------------------------------------------------
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _rgba(color, alpha):
        r, g, b = color[0], color[1], color[2]
        return (max(0, min(255, int(r))),
                max(0, min(255, int(g))),
                max(0, min(255, int(b))),
                max(0, min(255, int(alpha))))

    def _aacircle(surface, color, center, radius, width=0):
        if len(color) == 4:
            color = (max(0, min(255, int(color[0]))),
                     max(0, min(255, int(color[1]))),
                     max(0, min(255, int(color[2]))),
                     max(0, min(255, int(color[3]))))
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
            color = (max(0, min(255, int(color[0]))),
                     max(0, min(255, int(color[1]))),
                     max(0, min(255, int(color[2]))),
                     max(0, min(255, int(color[3]))))
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

    def _ellipse(surface, color, rect, width=0):
        if width and len(color) == 4:
            rx, ry, rw, rh = (int(rect[0]), int(rect[1]),
                              int(rect[2]), int(rect[3]))
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, rw, rh), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, _NS_drakar._clamp(color),
                            (int(rect[0]), int(rect[1]),
                             int(rect[2]), int(rect[3])), width)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            # Konversi koordinat DUNIA target ke ruang jangkar (x, y)
            # DENGAN kompensasi scale. Hero di-render ke canvas offscreen
            # lalu di-scale saat blit (heroes/__init__.py), jadi titik
            # canvas = (delta dunia)/scale supaya FX mendarat TEPAT di
            # target setelah blit. Boss 1x (scale=1) tidak terpengaruh.
            scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        return (int(x + 120.0 / float(getattr(boss, "_render_scale", 1.0)
                                 or 1.0) * getattr(boss, "direction", 1)),
                int(y))

    # ==================================================================
    # STATE ANIMASI
    # ==================================================================
    def _update_drk_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 46)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_drk_previous_timer", 0))
        active = bool(getattr(boss, "_drk_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._drk_attack_active = True
            boss._drk_attack_frame = 0
            # Kunci arah swing saat serangan dimulai: hero (versi summon)
            # yang kena hit lalu retreat/chase berbalik tiap frame, sehingga
            # tanpa kunci ini lunge, trail & impact ikut terbalik-balik.
            boss._drk_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._drk_attack_frame = int(getattr(boss, "_drk_attack_frame",
                                                  0)) + 1
        elif timer <= 0:
            boss._drk_attack_active = False
            boss._drk_attack_frame = 0
            active = False

        boss._drk_previous_timer = timer
        boss._drk_attack_progress = (
            min(1.0, boss._drk_attack_frame / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        cur_x = float(getattr(boss, "x", 0.0))
        cur_y = float(getattr(boss, "y", 0.0))
        if not hasattr(boss, "_drk_last_x"):
            boss._drk_last_x = cur_x
            boss._drk_last_y = cur_y
            return False
        moved = abs(cur_x - boss._drk_last_x) + abs(cur_y - boss._drk_last_y)
        boss._drk_last_x = cur_x
        boss._drk_last_y = cur_y
        return moved > 0.3

    # ==================================================================
    # POSE STATE - satu sumber kebenaran untuk rig DAN semua FX
    # ==================================================================
    ACTIONS = ("idle", "walk", "attack", "rage", "helix", "call", "cull")

    def _resolve_pose(boss, moving=False):
        """(action, phase, ap) - dipakai rig DAN anchor FX agar sinkron.

        Murni/tanpa efek samping: boleh dipanggil ulang oleh fungsi efek.
        """
        active_skill = getattr(boss, "active_skill", None)
        if active_skill == "e":
            action = "call"
        elif active_skill == "r":
            action = "cull"
        elif active_skill == "q":
            action = "rage"
        elif active_skill == "w":
            action = "helix"
        elif (getattr(boss, "_drk_attack_active", False)
              or getattr(boss, "timer", 0) >
              getattr(boss, "attack_cooldown", 46) - 15):
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
            raw = max(0.0, min(1.0, float(
                getattr(boss, "_drk_attack_progress", 0.0))))
            # anticipation / impact hold / rebound - lihat _attack_curve
            ap = _NS_drakar._attack_curve(raw)
        return action, phase, ap

    # Tinggi badan dalam RUANG LOKAL (y=0 = pinggul, + = ke bawah).
    # Total badan: puncak tanduk -78 -> telapak +48 (sebelum SCALE).
    HEAD_Y = -58
    SHOULDER_Y = -34
    # Sendi bahu (x = ke depan mengikuti arah hadap)
    SHOULDER_FRONT = (17, SHOULDER_Y + 1)
    SHOULDER_BACK = (-15, SHOULDER_Y)

    def _attack_curve(ap):
        """Remap progres mentah (0..1) -> waktu pose (0..1), MONOTON naik.

        Kapak besar butuh: (a) wind-up jelas (kapak diangkat jauh ke
        belakang), (b) tebasan yang JAUH lebih cepat dari wind-up,
        (c) HOLD singkat di impact (bobot kapak terasa), (d) recovery
        yang tidak "menarik mundur". Batas segmen jatuh PERSIS di batas
        fase _axe_angle / _front_grip_local: pose-time 0.26 = puncak
        wind-up, 0.79 = impact.
        """
        if ap <= 0.0:
            return 0.0
        if ap < 0.28:                       # anticipation: diperlambat
            t = ap / 0.28
            return 0.26 * (t ** 0.8)
        if ap < 0.50:                       # tebasan: sangat cepat
            t = (ap - 0.28) / 0.22
            return 0.26 + 0.53 * (t ** 0.45)
        if ap < 0.62:                       # IMPACT HOLD (nyaris beku)
            t = (ap - 0.50) / 0.12
            return 0.79 + 0.05 * t
        t = (ap - 0.62) / 0.38              # follow-through -> siap
        return 0.84 + 0.16 * (t ** 0.85)

    def _portrait_axe_angle():
        """Sudut kapak mode portrait: rapat ke badan, kepala di bahu.

        HeroPortraits meng-crop bbox lalu men-scale ke kartu, jadi figur
        yang LEBAR (kapak terentang) terKECIL di kartu. Kapak ditarik
        masuk -> bbox menyempit -> figur ter-render lebih besar.
        """
        return 2.02

    def _axe_angle(phase, action, ap=0.0):
        """Sudut kapak (radian dari garis lurus-bawah; + = ke depan).

        0 = mata kapak ke bawah, +pi/2 = lurus ke depan, ~pi = ke atas.
        Ditabel per-pose, BUKAN diturunkan dari arah lengan, supaya bilah
        tidak pernah menyayat menembus badannya sendiri. Batas segmen
        attack mengikuti _attack_curve(): 0-0.26 angkat, 0.26-0.79 tebas
        (HOLD di ~0.79), 0.79-1 recovery. Nilai idle = titik akhir
        recovery -> tidak ada frame "snap".
        """
        if action == "attack":
            if ap < 0.26:                       # wind-up (2.55 -> 3.42)
                t = ap / 0.26
                return 2.55 + 0.87 * t
            if ap < 0.79:                       # tebasan (3.42 -> 0.42)
                t = (ap - 0.26) / 0.53
                return 3.42 - 3.00 * t
            t = (ap - 0.79) / 0.21              # recovery -> siap
            return 0.42 + 1.88 * t
        if action == "cull":                    # R: eksekusi lebih dalam
            if ap < 0.30:
                t = ap / 0.30
                return 2.55 + 1.00 * t
            if ap < 0.74:
                t = (ap - 0.30) / 0.44
                return 3.55 - 3.25 * t
            t = (ap - 0.74) / 0.26
            return 0.30 + 1.10 * t
        if action == "rage":                    # Q: kapak siap di samping
            return 2.32 + math.sin(phase * 2.2) * 0.10
        if action == "helix":                   # W: kapak mendatar
            return 1.52 + math.sin(phase * 7.0) * 0.12
        if action == "call":                    # E: kapak tertancap depan
            return 0.42
        if action == "walk":
            return 1.80 + math.sin(phase * 1.66) * 0.10
        # Siap: kapak istirahat di samping bahu, mata kapak ~sejajar
        # dagu. Versi "digendong menyamping" membuat badan terbaca
        # sebagai palang abu-abu; sudut diagonal ini menjaga kepala &
        # dada sebagai subjek dan massa kapak mengisi kuadran atas.
        return 1.74 + math.sin(phase * 0.55) * 0.06

    def _axe_len(action):
        """Panjang gagang (grip -> mata kapak) per pose."""
        if action == "attack":
            return 46
        if action == "cull":
            return 48
        if action in ("rage", "helix"):
            return 44
        if action == "call":
            return 46
        return 42

    def _front_grip_local(action, ap=0.0, phase=0.0, compact=False):
        """Tangan depan (pegangan utama gagang), ruang lokal.

        compact=True dipakai mode portrait (lihat _portrait_axe_angle).
        """
        rest = -14
        if compact:
            return (10, rest + 1)
        if action == "attack":
            # Tangan tetap di sisi depan badan sepanjang ayunan.
            if ap < 0.26:
                t = min(1.0, ap / 0.26) ** 0.9
                return (int(13 - 6 * t), int(rest - 26 * t))
            if ap < 0.79:
                t = (ap - 0.26) / 0.53
                return (int(7 + 17 * t), int(rest - 26 + 42 * t))
            t = (ap - 0.79) / 0.18
            return (int(24 - 13 * t), int(rest + 16 - 3 * t))
        if action == "cull":
            if ap < 0.30:
                t = min(1.0, ap / 0.30) ** 0.9
                return (int(12 - 7 * t), int(rest - 28 * t))
            if ap < 0.74:
                t = (ap - 0.30) / 0.44
                return (int(5 + 19 * t), int(rest - 28 + 46 * t))
            t = (ap - 0.74) / 0.26
            return (int(24 - 14 * t), int(rest + 18 - 3 * t))
        if action == "rage":
            return (13, rest - 4)
        if action == "helix":
            return (14, rest - 2)
        if action == "call":
            return (13, rest + 8)
        if action == "walk":
            s = math.sin(phase * 1.66)
            return (int(11 + s * 3), int(rest - abs(s) * 2))
        return (11, rest + int(math.sin(phase * 0.55)))

    def _back_hand_u(action, ap=0.0):
        """Posisi tangan belakang DI sepanjang gagang (u dari grip; - =
        ke arah gagang bawah/pommel). Kedua tangan DIJAMIN menempel ke
        gagang karena lahir dari titik yang sama dengan kapak."""
        if action == "call":
            return -4                       # tangan bertumpuk di atas
        if action == "rage":
            return -10
        if action in ("attack", "cull"):
            return -11
        if action == "helix":
            return -12
        return -9

    def _back_grip_local(action, ap=0.0, phase=0.0, compact=False):
        """Tangan belakang: titik di gagang + toleransi kecil ke badan."""
        ang = (_NS_drakar._axe_angle(phase, action, ap)
               if not compact else _NS_drakar._portrait_axe_angle())
        gx, gy = _NS_drakar._front_grip_local(action, ap, phase,
                                               compact=compact)
        u = _NS_drakar._back_hand_u(action, ap)
        return (int(gx - math.sin(ang) * u), int(gy - math.cos(ang) * u))

    def _elbow(a, b, bend):
        """Siku 2-tulang: titik tengah + offset tegak lurus.

        Lengan selalu tersambung (tidak pernah "lepas" seperti stiker)
        dan lengkungannya bisa diarahkan per sisi.
        """
        mx = (a[0] + b[0]) * 0.5
        my = (a[1] + b[1]) * 0.5
        dx = b[0] - a[0]
        dy = b[1] - a[1]
        ln = math.hypot(dx, dy) or 1.0
        return (int(mx + (-dy / ln) * bend), int(my + (dx / ln) * bend))

    def _arm_chain(shoulder, grip, phase, action, ap=0.0, back=False):
        """(siku, sudut kapak) - siku dari lengan, sudut dari tabel pose."""
        bend = 6.0 if back else -7.0
        if action in ("rage", "cull") and not back:
            bend = -4.0
        elbow = _NS_drakar._elbow(shoulder, grip, bend)
        return elbow, _NS_drakar._axe_angle(phase, action, ap)

    def _head_bob(action, phase, ap):
        """Offset kepala (dx, dy) ruang lokal.

        Kepala TIDAK merekat mati ke torso: mengangkat saat langkah,
        menunduk mengikuti tebasan, mendongak saat roar (call), dan
        bergetar halus saat rage.
        """
        if action == "walk":
            sw = math.sin(phase * 1.66)
            return (int(-sw * 1.4), int(abs(math.sin(phase * 1.1)) * -1.6))
        if action == "attack":
            return (int(math.sin(ap * math.pi) * 2.6),
                    int(math.sin(ap * math.pi) * 1.8))
        if action == "cull":
            return (int(math.sin(ap * math.pi) * 3.0),
                    int(math.sin(ap * math.pi) * 2.2))
        if action == "rage":
            return (int(math.sin(phase * 5.5) * 0.8), -2)
        if action == "call":
            return (-1, -4)
        if action == "helix":
            return (int(math.sin(phase * 7.0) * 1.2), -1)
        return (int(math.sin(phase * 0.31) * 1.0),
                int(math.sin(phase * 0.55 + 0.8) * 0.9))

    def _rig_shift(action, phase, ap):
        """(lean, root_y) badan; kaki TIDAK ikut bergeser (menapak)."""
        lean = 0
        root_y = int(math.sin(phase * 0.55) * 1.3)
        if action == "walk":
            lean = int(math.sin(phase * 1.66) * 2.4)
            root_y -= int(abs(math.sin(phase * 1.1)) * 2.8)
        elif action == "attack":
            t = math.sin(ap * math.pi)
            lean = int(t * 7)
            root_y += int(t * 2.5)
        elif action == "cull":
            t = math.sin(ap * math.pi)
            lean = int(t * 9)
            root_y += int(t * 4)
        elif action == "rage":
            lean = int(math.sin(phase * 9.0))
            root_y -= 2
        elif action == "call":
            lean = 2
            root_y -= 1
        elif action == "helix":
            lean = int(math.sin(phase * 7.0) * 2)
            root_y -= 1
        return lean, root_y

    def _s(v):
        """Ukuran ruang lokal (lebar garis, radius) -> piksel layar."""
        return max(1, int(round(v * _NS_drakar.SCALE)))

    def _local_to_screen(cx, cy, facing, lean, root_y, lx, ly):
        """SATU pemetaan lokal -> layar: skala, arah hadap, bob/lean.

        Semua bagian tubuh dan semua titik jangkar efek (mata kapak,
        pergelangan) melewati fungsi ini, jadi ukuran boleh diubah lewat
        satu angka tanpa membuat efek lepas dari badan.
        """
        f = 1 if facing >= 0 else -1
        k = _NS_drakar.SCALE
        return (int(cx + (lx * f + lean * f) * k),
                int(cy - _NS_drakar.LIFT + (ly + root_y) * k))

    def _local(boss, x, y, action, phase, ap, lx, ly):
        """Ruang lokal rig -> piksel surface (dipakai FX eksternal)."""
        facing = getattr(boss, "direction", 1) or 1
        lean, root_y = _NS_drakar._rig_shift(action, phase, ap)
        return _NS_drakar._local_to_screen(x, y, facing, lean, root_y,
                                            lx, ly)

    def _axe_head_local(action, phase, ap=0.0):
        """Mata kapak (pusat bilah) dalam ruang lokal - rig & FX pakai
        angka yang sama, jadi trail selalu lahir dari ujung senjata."""
        grip = _NS_drakar._front_grip_local(action, ap, phase)
        ang = _NS_drakar._axe_angle(phase, action, ap)
        L = _NS_drakar._axe_len(action)
        return (int(grip[0] + math.sin(ang) * L),
                int(grip[1] + math.cos(ang) * L))

    def _tip_local(action, phase, ap=0.0):
        """Ujung terjauh bilah (tepi luar) dalam ruang lokal."""
        hx, hy = _NS_drakar._axe_head_local(action, phase, ap)
        ang = _NS_drakar._axe_angle(phase, action, ap)
        # Tepi terjauh bilah ~13 px di sisi +v dari mata kapak.
        return (int(hx + math.cos(ang) * 13), int(hy - math.sin(ang) * 13))

    def _tip_screen(boss, x, y):
        action, phase, ap = _NS_drakar._resolve_pose(boss)
        # FX selalu memakai pose yang sama dengan badan (lihat
        # _resolve_pose yang murni), jadi trail tidak pernah lepas.
        return _NS_drakar._local(boss, x, y, action, phase, ap,
                                 *_NS_drakar._tip_local(action, phase, ap))

    # ==================================================================
    # ENTRY POINT
    # ==================================================================
    def draw_drakar(surface, boss, x, y):
        """Entry point Boss.draw() sekaligus heroes.render_hero()."""
        # jalur hero (lane): heroes/__init__ men-set _render_scale sebelum
        # memanggil renderer, dan _finish_hd_sprite sudah menambah
        # rim/terminator -> pass di sini dilewati (lihat _draw_drk_rig_at).
        _NS_drakar._HERO_LANE.v = hasattr(boss, "_render_scale")
        _NS_drakar._update_drk_attack_anim(boss)
        action, phase, ap = _NS_drakar._resolve_pose(
            boss, _NS_drakar._detect_moving(boss))
        boss._drk_pose_action = action
        skill = getattr(boss, "active_skill", None)
        timer = int(getattr(boss, "active_skill_timer", 0))
        portrait = bool(getattr(boss, "_portrait_hd", False))
        facing = getattr(boss, "direction", 1) or 1
        flash = _NS_drakar._alpha(170 * (getattr(boss, "hurt_flash_timer", 0)
                                         / 8.0))

        # ── Latar. Dibuang total saat portrait supaya auto-crop Hero Shop
        #    terisi wajah & material, bukan lingkaran efek.
        if not portrait:
            _NS_drakar._draw_rage_aura(surface, x, y, phase, skill)
            _NS_drakar._draw_ground_ring(surface, x, y, phase, skill)
            if skill == "q":
                _NS_drakar._draw_battlehunger_ground(surface, boss, x, y,
                                                      timer, phase)
            elif skill == "w":
                _NS_drakar._draw_counterhelix_ground(surface, boss, x, y,
                                                      timer, phase)
            elif skill == "e":
                _NS_drakar._draw_berserkerscall_ground(surface, boss, x, y,
                                                        timer, phase)
            elif skill == "r":
                _NS_drakar._draw_cullingblade_ground(surface, boss, x, y,
                                                      timer, phase)

        # ── Karakter
        if not portrait:
            _NS_drakar._draw_shadow(surface, x, y + _NS_drakar.GROUND_DY)
        _NS_drakar._draw_drk_rig_at(surface, x, y, facing, phase, action,
                                     ap, portrait, flash)
        if not portrait:
            if action == "attack":
                # Pita cleave dari lintasan mata kapak yang sebenarnya.
                _NS_drakar._draw_cleave_trail(surface, boss, x, y, facing,
                                               phase, ap)
            elif action == "walk":
                # Debu langkah tepat saat telapak mendarat.
                _NS_drakar._draw_footfall_dust(surface, x, y, facing, phase)

        # ── Foreground FX
        if not portrait:
            if skill == "q":
                _NS_drakar._draw_battlehunger_foreground(surface, boss, x, y,
                                                          timer, phase)
            elif skill == "w":
                _NS_drakar._draw_counterhelix_foreground(surface, boss, x, y,
                                                          timer, phase)
            elif skill == "e":
                _NS_drakar._draw_berserkerscall_foreground(surface, boss,
                                                            x, y, timer,
                                                            phase)
            elif skill == "r":
                _NS_drakar._draw_cullingblade_foreground(surface, boss, x, y,
                                                          timer, phase)

    def _draw_drk_rig_at(surface, x, y, facing, phase, action, ap, detail,
                         flash=0):
        """Rig -> buffer -> outline gelap 1 px -> satu blit murah.

        Mode portrait Hero Shop memakai kanvas kecil (200x200 di
        ui_components) dan meng-crop dari bbox: kalau badan digambar
        dengan anchor di pinggul, mata kapak yang menjulang TERPOTONG.
        Jadi di mode itu konten dipusatkan pada bbox-nya sendiri; jalur
        boss (1x) tidak berubah sama sekali.
        """
        buf = pygame.Surface((_NS_drakar.RIG_W, _NS_drakar.RIG_H),
                             pygame.SRCALPHA)
        _NS_drakar._draw_drk_rig(buf, _NS_drakar.RIG_OX, _NS_drakar.RIG_OY,
                                  facing, phase, action, ap, detail)
        if flash > 0:
            lit = buf.copy()
            lit.fill((255, 246, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
            lit.set_alpha(flash)
            buf.blit(lit, (0, 0))
        # Jalur BOSS digambar langsung ke layar 1:1, jadi TIDAK melewati
        # _finish_hd_sprite (yang sudah memberi rim+terminator ke hero).
        # Di sinilah cahaya itu dipasang untuk boss. Aturan: pass cahaya
        # dipasang di SINI hanya kalau sprite ini TIDAK akan dilewatkan ke
        # heroes._finish_hd_sprite:
        #   * boss 1x (scale 1.0)      -> pasang di sini
        #   * lane hero (scale != 1.0) -> jangan (nanti dobel)
        #   * Hero Shop (portrait)     -> pasang di sini
        if _lighting is not None and not _NS_drakar._HERO_LANE.v:
            _lighting.apply_to_rig(
                buf, rim_add=(46, 20, 22), shade_mul=160,
                box=_NS_drakar.GRAD_BOX if not detail else None)
        ox = int(x) - _NS_drakar.RIG_OX
        oy = int(y) - _NS_drakar.RIG_OY
        if detail:                      # portrait: pusatkan konten
            used = buf.get_bounding_rect(min_alpha=1)
            if used.width > 0:
                ox = int(x) - (used.left + used.width // 2)
                oy = int(y) - (used.top + used.height // 2)
        # Outline siluet (4 arah) - bagian tetap terpisah saat unit
        # bertumpuk di lane.
        edge = buf.copy()
        edge.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            surface.blit(edge, (ox + dx, oy + dy))
        surface.blit(buf, (ox, oy))
        return buf

    def _compose_outline(x, y, facing, phase, action, ap, detail):
        """Rig + outline gelap 1 px sebagai SATU surface.

        Return ``(surface, anchor_x, anchor_y)``: titik dalam surface yang
        jatuh tepat di dunia ``(x, y)``. Dipakai tool review.
        """
        buf = pygame.Surface((_NS_drakar.RIG_W, _NS_drakar.RIG_H),
                             pygame.SRCALPHA)
        _NS_drakar._draw_drk_rig(buf, _NS_drakar.RIG_OX, _NS_drakar.RIG_OY,
                                  facing, phase, action, ap, detail)
        pad = 1
        out = pygame.Surface((_NS_drakar.RIG_W + pad * 2,
                              _NS_drakar.RIG_H + pad * 2), pygame.SRCALPHA)
        edge = buf.copy()
        edge.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            out.blit(edge, (pad + dx, pad + dy))
        out.blit(buf, (pad, pad))
        return out, _NS_drakar.RIG_OX + pad, _NS_drakar.RIG_OY + pad

    def _draw_drk_rig(surface, cx, cy, facing, phase, action, ap=0.0,
                      detail=False):
        """BONE RIG 2D BERLAPIS - seluruh badan dihitung dari sendi.

        ``cx, cy`` = anchor (pusat boss / garis pinggul). Urutan gambar
        belakang -> depan: pelt -> kaki -> lengan belakang -> torso ->
        sabuk -> pauldron -> kepala -> lengan depan + kapak -> rim.
        """
        p = _NS_drakar.PALETTE
        f = 1 if facing >= 0 else -1
        lean, root_y = _NS_drakar._rig_shift(action, phase, ap)

        def pt(dx, dy):
            """Sendi badan (ikut bob/lean)."""
            return _NS_drakar._local_to_screen(cx, cy, f, lean, root_y,
                                                dx, dy)

        def ptg(dx, dy):
            """Sendi yang terpatok tanah (telapak kaki tidak ikut bob)."""
            return _NS_drakar._local_to_screen(cx, cy, f, lean, 0, dx, dy)

        def poly_free(color, pts, outline=True):
            if outline:
                _NS_drakar._poly(surface, p["shadow_deep"],
                                  [(q[0] + f, q[1] + 1) for q in pts])
            _NS_drakar._poly(surface, color, pts)

        def dot(color, dx, dy, r, outline=True):
            sx, sy = pt(dx, dy)
            rr = _NS_drakar._s(r)
            if outline:
                _NS_drakar._aacircle(surface, p["shadow_deep"],
                                     (sx + f, sy + 1), rr + 1)
            _NS_drakar._aacircle(surface, color, (sx, sy), rr)

        def limb(a, b, width, base, light=None, ground=False):
            tf = ptg if ground else pt
            aa, bb = tf(*a), tf(*b)
            w = _NS_drakar._s(width)
            _NS_drakar._aaline(surface, p["shadow_deep"],
                               (aa[0] + f, aa[1] + 1),
                               (bb[0] + f, bb[1] + 1), w + 2)
            _NS_drakar._aaline(surface, base, aa, bb, w)
            if light:
                off = -1 if f > 0 else 1
                _NS_drakar._aaline(surface, light,
                                   (aa[0] + off, aa[1] - 1),
                                   (bb[0] + off, bb[1] - 1),
                                   max(1, _NS_drakar._s(width // 3)))

        breath = math.sin(phase * 0.55)
        stride = (math.sin(phase * 1.66) if action == "walk" else 0.0)
        rage = action == "rage"
        helix = action == "helix"
        call = action == "call"
        cull = action == "cull"
        hot = rage or helix or call or cull or action == "attack"

        portrait = bool(detail)
        front_grip = _NS_drakar._front_grip_local(action, ap, phase,
                                                   compact=portrait)
        back_grip = _NS_drakar._back_grip_local(action, ap, phase,
                                                 compact=portrait)
        front_elbow, front_angle = _NS_drakar._arm_chain(
            _NS_drakar.SHOULDER_FRONT, front_grip, phase, action, ap)
        back_elbow, back_angle = _NS_drakar._arm_chain(
            _NS_drakar.SHOULDER_BACK, back_grip, phase, action, ap, back=True)
        if portrait:
            front_angle = _NS_drakar._portrait_axe_angle()

        # 1. Pelt bulu di punggung - membingkai badan, tidak melebarinya
        _NS_drakar._draw_drk_pelt_back(surface, pt, poly_free, f, phase,
                                        action)

        # 2. Kaki - telapak dipatok di GROUND_DY
        _NS_drakar._draw_drk_legs(surface, pt, ptg, poly_free, f, phase,
                                   action, stride)

        # 3. Tangan belakang (memegang gagang di bawah tangan depan)
        _NS_drakar._draw_drk_arm(surface, pt, poly_free, dot, limb, f, phase,
                                  action, ap, _NS_drakar.SHOULDER_BACK,
                                  back_elbow, back_grip, back_angle, back=True)

        # 4. Torso merah + harness kulit + permata rage
        _NS_drakar._draw_drk_torso(surface, pt, poly_free, dot, f, phase,
                                    breath, hot)

        # 5. Sabuk, loincloth, buckle tengkorak
        _NS_drakar._draw_drk_belt(surface, pt, poly_free, dot, f, phase,
                                   action, stride)

        # 6. Pauldron besi bertingkat + duri
        _NS_drakar._draw_drk_pauldrons(surface, pt, poly_free, dot, f, phase,
                                        breath)

        # 7. Leher + kepala (mane hitam, tanduk helm, mata amber)
        _NS_drakar._draw_drk_head(surface, pt, poly_free, dot, f, phase,
                                   action, rage, call)

        # 8. Tangan depan + KAPAK (paling depan)
        _NS_drakar._draw_drk_arm(surface, pt, poly_free, dot, limb, f, phase,
                                  action, ap, _NS_drakar.SHOULDER_FRONT,
                                  front_elbow, front_grip, front_angle,
                                  back=False, hot=hot)

        # 9. Rim light merah - sinyal warna tema
        _NS_drakar._draw_drk_rimlight(surface, pt, f, phase, rage, call, hot)

        # 10. Pass material portrait-only
        if portrait:
            _NS_drakar._draw_drk_masterwork_details(surface, pt, f, phase,
                                                     action)
            _NS_drakar._draw_drk_weave(surface, pt, f)

    # ==================================================================
    # BAGIAN TUBUH
    # ==================================================================
    # Prinsip di 720p: yang dibaca hanyalah NILAI (terang/gelap) dan
    # SILUET, bukan garis halus. Setiap bagian dibatasi 2-3 lapis nilai,
    # dan garis penanda (otot, jahitan) hanya muncul di pass portrait.
    # ==================================================================

    def _draw_drk_pelt_back(surface, pt, poly_free, f, phase, action):
        """Pelt bulu hitam berujung merah di punggung: MEMBINGKAI badan.

        Menggantikan cape: tepi bawah bergerigi dan berayun oleh phase.
        Ujung berwarna darah memberi tepi terbaca sebagai BULU (bukan
        lubang gelap) di skala 1x.
        """
        p = _NS_drakar.PALETTE
        sway = int(math.sin(phase * 1.05) * 2)
        if action in ("walk", "attack", "cull"):
            sway -= 2
        outer = [(-18, -24), (-24, -12), (-28 + sway, 4), (-22 + sway, 14),
                 (-15 + sway, 7), (-8 + sway, 15), (-1, 6), (3, -10),
                 (1, -24)]
        poly_free(p["hair_darkest"], [pt(*q) for q in outer])
        inner = [(-15, -22), (-19, -12), (-22 + sway, 3), (-17 + sway, 11),
                 (-12 + sway, 6), (-7 + sway, 12), (-1, 4), (2, -10),
                 (0, -22)]
        poly_free(p["hair_dark"], [pt(*q) for q in inner], outline=False)
        # Helai pelt: 3 segitiga gelap menjuntai
        for i, (bx, by) in enumerate(((-19, 6), (-12, 8), (-4, 7))):
            tipx = bx + sway - 2 + (i % 2)
            poly_free(p["hair_darkest"], [pt(bx, by), pt(tipx, by + 9 + i),
                                           pt(bx + 5, by)])
        # Ujung merah: rim darah di tepi bawah pelt
        hem = [(-20 + sway, 6), (-16 + sway, 12), (-11 + sway, 9),
               (-6 + sway, 13), (-1, 6)]
        for i in range(len(hem) - 1):
            _NS_drakar._aaline(surface, p["blood_dark"], pt(*hem[i]),
                               pt(*hem[i + 1]), 1)
        _NS_drakar._aaline(surface, p["blood_mid"], pt(-16 + sway, 10),
                           pt(-11 + sway, 9), 1)

    def _draw_drk_legs(surface, pt, ptg, poly_free, f, phase, action, stride):
        """Dua kaki raksasa: paha merah -> pelindung lutut -> greave ->
        boot berujung baja. Telapak DATAR di garis tanah."""
        p = _NS_drakar.PALETTE
        hip_y = 2
        ground = _NS_drakar.FEET_DY
        for side in (-1, 1):
            if action == "walk":
                dx = int(stride * 9) * side
                lift = int(max(0.0, -stride * side) * 5)
            elif action in ("attack", "cull"):
                # Lunge: kaki depan melangkah, kaki belakang menahan
                dx = 10 if side > 0 else -8
                lift = 0
            elif action in ("rage", "helix"):
                dx = 8 if side > 0 else -8
                lift = 0
            elif action == "call":
                dx = 9 if side > 0 else -9
                lift = 0
            else:
                dx = 8 if side > 0 else -10
                lift = 0
            front = side > 0
            hip_x = side * 9
            knee_x = hip_x + int(dx * 0.55) + side
            foot_x = hip_x + dx + side * 2
            knee_y = (hip_y + ground) // 2 - lift
            fy = ground - lift
            # Paha merah: blok gelap + tengah + garis cahaya tipis
            poly_free(p["skin_darkest"], [pt(hip_x - 7, hip_y),
                                          pt(hip_x + 6, hip_y),
                                          pt(knee_x + 5, knee_y),
                                          pt(knee_x - 6, knee_y)])
            if front:
                poly_free(p["skin_dark"], [pt(hip_x - 6, hip_y + 1),
                                           pt(hip_x + 5, hip_y + 1),
                                           pt(knee_x + 4, knee_y - 1),
                                           pt(knee_x - 5, knee_y - 1)],
                          outline=False)
                poly_free(p["skin_mid"], [pt(hip_x - 5, hip_y + 2),
                                          pt(hip_x + 1, hip_y + 2),
                                          pt(knee_x - 1, knee_y - 4),
                                          pt(knee_x - 4, knee_y - 4)],
                          outline=False)
            # Pembungkus kain kulit di paha (identik dengan loincloth)
            poly_free(p["leather_dark"], [pt(hip_x - 6, hip_y + 8),
                                          pt(hip_x + 5, hip_y + 8),
                                          pt(hip_x + 5, hip_y + 15),
                                          pt(hip_x - 6, hip_y + 15)])
            if front:
                poly_free(p["leather_mid"], [pt(hip_x - 5, hip_y + 9),
                                             pt(hip_x + 3, hip_y + 9),
                                             pt(hip_x + 3, hip_y + 14),
                                             pt(hip_x - 5, hip_y + 14)],
                          outline=False)
                _NS_drakar._aaline(surface, p["leather_light"],
                                   pt(hip_x - 5, hip_y + 9),
                                   pt(hip_x + 3, hip_y + 9), 1)
            # Pelindung lutut besi
            poly_free(p["armor_darkest"], [pt(knee_x - 5, knee_y - 3),
                                           pt(knee_x + 5, knee_y - 3),
                                           pt(knee_x + 5, knee_y + 3),
                                           pt(knee_x - 5, knee_y + 3)])
            poly_free(p["armor_mid"], [pt(knee_x - 4, knee_y - 2),
                                       pt(knee_x + 3, knee_y - 2),
                                       pt(knee_x + 3, knee_y + 2),
                                       pt(knee_x - 4, knee_y + 2)],
                      outline=False)
            _NS_drakar._aacircle(surface, p["armor_shine"],
                                 pt(knee_x - 1, knee_y - 1), 1)
            # Betis kulit gelap + satu garis tepi cahaya
            poly_free(p["leather_dark"], [pt(knee_x - 5, knee_y + 2),
                                          pt(knee_x + 5, knee_y + 2),
                                          ptg(foot_x + 5, fy - 8),
                                          ptg(foot_x - 5, fy - 8)])
            if front:
                poly_free(p["leather_mid"], [pt(knee_x - 4, knee_y + 3),
                                             pt(knee_x + 2, knee_y + 3),
                                             ptg(foot_x + 2, fy - 9),
                                             ptg(foot_x - 4, fy - 9)],
                          outline=False)
                _NS_drakar._aaline(surface, p["leather_light"],
                                   pt(knee_x - 3, knee_y + 4),
                                   ptg(foot_x - 3, fy - 8), 1)
            # Boot gelap + kap baja, sol DATAR di garis tanah
            toe = 5 if f > 0 else -5
            poly_free(p["leather_darkest"], [ptg(foot_x - 6, fy - 8),
                                             ptg(foot_x + 6, fy - 8),
                                             ptg(foot_x + toe + 3, fy - 2),
                                             ptg(foot_x + toe, fy),
                                             ptg(foot_x - toe, fy),
                                             ptg(foot_x - 7, fy - 3)])
            poly_free(p["leather_mid"], [ptg(foot_x - 5, fy - 7),
                                         ptg(foot_x + 5, fy - 7),
                                         ptg(foot_x + toe + 2, fy - 3),
                                         ptg(foot_x - 6, fy - 3)],
                      outline=False)
            # Kap baja di ujung boot: nilai BESI, bukan cokelat, supaya
            # kedua kaki tetap terpisah dan terbaca di skala hero.
            poly_free(p["armor_dark"], [ptg(foot_x + toe - 2, fy - 6),
                                        ptg(foot_x + toe + 3, fy - 4),
                                        ptg(foot_x + toe + 3, fy - 1),
                                        ptg(foot_x + toe - 1, fy),
                                        ptg(foot_x + toe - 3, fy)],
                      outline=False)
            # Garis break terang di pergelangan
            _NS_drakar._aaline(surface, p["leather_light"],
                               ptg(foot_x - 6, fy - 8),
                               ptg(foot_x + 5, fy - 8), 1)
            if lift <= 0:
                _NS_drakar._aaline(surface, p["shadow_deep"],
                                   ptg(foot_x - 6, fy + 1),
                                   ptg(foot_x + 6, fy + 1), 2)
            else:
                _NS_drakar._aaline(surface, (*p["shadow"], 80),
                                   ptg(foot_x - 5, _NS_drakar.FEET_DY),
                                   ptg(foot_x + 5, _NS_drakar.FEET_DY), 2)

    def _draw_drk_torso(surface, pt, poly_free, dot, f, phase, breath, hot):
        """Dada merah raksasa (V-taper) + harness kulit + permata rage.

        Nilai dijaga: kulit merah dengan SATU blok terang di dada depan,
        rongga gelap di bawah pektoral. Permata rage di tulang dada adalah
        sinyal warna tema - menyala saat skill/attack (hot).
        """
        p = _NS_drakar.PALETTE
        sh = _NS_drakar.SHOULDER_Y
        twist = int(math.sin(phase * 1.05))
        poly_free(p["skin_darkest"], [pt(-18 + twist, sh - 1),
                                      pt(17 + twist, sh - 1), pt(13, 4),
                                      pt(-14, 4)])
        poly_free(p["skin_dark"], [pt(-16 + twist, sh), pt(15 + twist, sh),
                                   pt(12, 3), pt(-13, 3)], outline=False)
        poly_free(p["skin_mid"], [pt(-12 + twist, sh + 1),
                                  pt(11 + twist, sh + 1), pt(9, -2),
                                  pt(-10, -2)], outline=False)
        # Nilai dominan gelap; terang hanya wedge kecil sisi cahaya -
        # kulit pink terang dulu membuat badan kehilangan mood nan duri.
        poly_free(p["skin_light"], [pt(2 + twist, sh + 1),
                                    pt(9 + twist, sh + 1), pt(6, sh + 6),
                                    pt(1, sh + 6)], outline=False)
        poly_free(p["skin_shine"], [pt(4 + twist, sh + 2),
                                    pt(7 + twist, sh + 2), pt(5, sh + 5),
                                    pt(4, sh + 5)], outline=False)
        # Bayangan miring di bawah pektoral + highlight mikro: dua nilai
        # ini yang membuat dada terbaca BERBUKUK.
        poly_free(p["skin_dark"], [pt(-11 + twist, sh + 8),
                                   pt(-1 + twist, sh + 9),
                                   pt(-2 + twist, sh + 11),
                                   pt(-11 + twist, sh + 10)], outline=False)
        _NS_drakar._aaline(surface, p["skin_light"],
                           pt(-9 + twist, sh + 5), pt(-2 + twist, sh + 5), 1)
        # Garis tengah + otot perut (nilai, bukan outline)
        _NS_drakar._aaline(surface, p["skin_dark"], pt(twist, sh + 4),
                           pt(0, 2), 1)
        _NS_drakar._aaline(surface, p["skin_dark"], pt(-6, -2), pt(6, -2), 1)
        _NS_drakar._aaline(surface, p["skin_dark"], pt(-5, 1), pt(5, 1), 1)
        # Scar diagonal di dada (kenangan perang - satu nilai saja)
        _NS_drakar._aaline(surface, p["skin_darkest"], pt(5 + twist, sh + 3),
                           pt(9 + twist, sh + 9), 1)
        # Harness kulit diagonal + pelat besi kecil
        _NS_drakar._aaline(surface, p["leather_dark"], pt(14 + twist, sh),
                           pt(-11, 3), 4)
        _NS_drakar._aaline(surface, p["leather_light"], pt(14 + twist, sh),
                           pt(-11, 3), 1)
        poly_free(p["armor_darkest"], [pt(-2, sh + 5), pt(5, sh + 6),
                                       pt(4, sh + 11), pt(-3, sh + 10)])
        poly_free(p["armor_mid"], [pt(-1, sh + 6), pt(4, sh + 7),
                                   pt(3, sh + 10), pt(-2, sh + 9)],
                  outline=False)
        for bx in (9, 2):
            _NS_drakar._aacircle(surface, p["brass_mid"],
                                 pt(bx + twist, sh + 2), 1)
        # Permata rage di tulang dada - SATU fokus terang per tubuh
        ga = 0.35 + (0.65 if hot else 0.0)
        a = _NS_drakar._alpha(150 + 105 * ga *
                              (0.72 + 0.28 * math.sin(phase * 2.2)))
        gemx, gemy = pt(-7, sh + 6)
        _NS_drakar._aacircle(surface, (*p["blood_dark"], a), (gemx, gemy), 3)
        _NS_drakar._aacircle(surface, (*p["blood_mid"], min(255, a + 30)),
                             (gemx, gemy), 2)
        _NS_drakar._rect_st(surface, (*p["blood_shine"], 255),
                            (gemx - 1, gemy - 1, 2, 2))

    def _rect_st(surface, color, rect):
        """Rect kecil dengan alpha (nama berbeda dari closure _rect)."""
        rx, ry, rw, rh = int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3])
        if rw <= 0 or rh <= 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, rw, rh))
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, _NS_drakar._clamp(color),
                         (rx, ry, rw, rh))

    def _draw_drk_belt(surface, pt, poly_free, dot, f, phase, action, stride):
        """Sabuk kulit lebar + gesper tengkorak + loincloth robek."""
        p = _NS_drakar.PALETTE
        sway = int(math.sin(phase * 1.1) * 2)
        if action == "walk":
            sway += int(stride * 2)
        poly_free(p["leather_dark"], [pt(-14, 1), pt(14, 1), pt(14, 8),
                                      pt(-14, 8)])
        poly_free(p["leather_mid"], [pt(-13, 2), pt(13, 2), pt(13, 7),
                                     pt(-13, 7)], outline=False)
        _NS_drakar._aaline(surface, p["leather_light"], pt(-13, 2),
                           pt(13, 2), 1)
        for bx in (-10, -4, 9):
            _NS_drakar._aacircle(surface, p["brass_mid"], pt(bx, 4), 1)
        # Gesper tengkorak: bidang tulang dengan dua rongga mata gelap
        poly_free(p["bone_darkest"], [pt(-3, 0), pt(5, 0), pt(5, 9),
                                      pt(-3, 9)])
        poly_free(p["bone_mid"], [pt(-2, 1), pt(4, 1), pt(4, 8), pt(-2, 8)],
                  outline=False)
        _NS_drakar._aacircle(surface, p["bone_darkest"], pt(0, 3), 1)
        _NS_drakar._aacircle(surface, p["bone_darkest"], pt(3, 3), 1)
        _NS_drakar._aaline(surface, p["bone_dark"], pt(-1, 6), pt(3, 6), 1)
        # Loincloth bertepi robek. Sengaja sempit: versi lebar mengubah
        # kedua kaki jadi satu tiang dan menghapus siluet "berdiri".
        outer = [(-9, 8), (4, 8), (5 + sway, 20), (2 + sway, 26), (-1, 20),
                 (-2, 26), (-5, 20), (-6 + sway, 24), (-8 + sway, 18)]
        poly_free(p["leather_darkest"], [pt(*q) for q in outer])
        inner = [(-8, 9), (3, 9), (4 + sway, 19), (1 + sway, 23), (-2, 19),
                 (-3, 23), (-6 + sway, 17)]
        poly_free(p["leather_dark"], [pt(*q) for q in inner], outline=False)
        poly_free(p["leather_mid"], [pt(-4, 10), pt(3, 10), pt(3 + sway, 19),
                                     pt(0, 23), pt(-4 + sway, 18)],
                  outline=False)
        _NS_drakar._aaline(surface, p["blood_dark"], pt(-6, 10),
                           pt(-8 + sway, 21), 1)
        # Cincin tengkorak kecil di sisi sabuk
        _NS_drakar._aacircle(surface, p["bone_dark"], pt(-11, 6), 2)
        _NS_drakar._aacircle(surface, p["bone_light"], pt(-11, 6), 1)

    def _draw_drk_pauldrons(surface, pt, poly_free, dot, f, phase, breath):
        """Pauldron besi bertingkat MENEMPEL bahu + duri pendek tebal.

        Versi pertama masterwork punya duri tulang tinggi di ujung luar
        yang terbaca sebagai sayap kelelawar terpisah dari badan; sekarang
        pelat duduk di garis bahu dan duri mengarah ke atas-depan, pendek.
        """
        p = _NS_drakar.PALETTE
        sh = _NS_drakar.SHOULDER_Y
        for side, scale in ((-1, 0.78), (1, 1.0)):
            sx = side * 17
            sy = sh - 1 - int(breath if side > 0 else 0)
            w = max(5, int(10 * scale))
            h = max(3, int(6 * scale))
            # Pelat utama: kubah rendah, tepi bawah menyatu ke lengan
            poly_free(p["armor_darkest"], [pt(sx - w, sy - h + 2),
                                           pt(sx + w, sy - h),
                                           pt(sx + w + 1, sy + 3),
                                           pt(sx, sy + h + 1),
                                           pt(sx - w - 1, sy + 3)])
            poly_free(p["armor_mid"], [pt(sx - w + 1, sy - h + 3),
                                       pt(sx + w - 1, sy - h + 3),
                                       pt(sx + w, sy + 1),
                                       pt(sx, sy + h - 1),
                                       pt(sx - w, sy + 1)], outline=False)
            lit = p["armor_light"] if side > 0 else p["armor_dark"]
            poly_free(lit, [pt(sx - w + 2, sy - h + 4),
                            pt(sx - 1, sy - h + 4),
                            pt(sx - 1, sy),
                            pt(sx - w + 2, sy)], outline=False)
            if side > 0:
                _NS_drakar._aaline(surface, p["armor_shine"],
                                   pt(sx - w + 2, sy - h + 4),
                                   pt(sx + w - 1, sy - h + 3), 1)
            # Duri pendek tebal ke atas-depan (bukan tanduk panjang)
            spike = sy - h - (5 if side > 0 else 4)
            poly_free(p["armor_darkest"], [pt(sx - 3, sy - h + 2),
                                           pt(sx + 1, spike),
                                           pt(sx + 4, sy - h + 2)])
            poly_free(p["armor_mid"], [pt(sx - 2, sy - h + 2),
                                       pt(sx + 1, spike + 1),
                                       pt(sx + 3, sy - h + 2)],
                      outline=False)
            _NS_drakar._aacircle(surface, p["brass_mid"],
                                 pt(sx + side * 4, sy + 2), 1)
            if side > 0:
                # Rivet darah di pauldron depan: 2px, tema, tidak mencuri
                # fokus dari mata.
                _NS_drakar._aacircle(surface, p["blood_dark"],
                                     pt(sx - 3, sy - 1), 2)
                _NS_drakar._aacircle(surface, p["blood_mid"],
                                     pt(sx - 3, sy - 1), 1)

    def _draw_drk_head(surface, pt, poly_free, dot, f, phase, action, rage,
                       call):
        """KEPALA sebagai subjek: leher tebal terlihat, mane hitam yang
        JATUH ke bahu (tidak ada rongga antara kepala dan torso), helm
        setengah besi di atas (tidak menutupi mata), dua tanduk banteng
        ke ATAS, wajah merah terang dengan mata amber menyala.

        Versi pertama masterwork: kepala kecil melayang dengan rongga
        gelap di leher, helm menutupi baris mata sehingga wajah terbaca
        sebagai helm berkaca merah, dan tanduk mendatar terbaca sebagai
        sayap. Semua itu dibetulkan di sini.
        """
        p = _NS_drakar.PALETTE
        hy = _NS_drakar.HEAD_Y + int(math.sin(phase * 0.55) * 0.9)
        hx = 2 if action in ("attack", "cull") else 1
        sh = _NS_drakar.SHOULDER_Y

        # Leher tebal: dari tengkorak SAMPAI di bawah garis bahu, jadi
        # tidak pernah ada rongga antara kepala dan torso.
        poly_free(p["skin_darkest"], [pt(-8, hy + 6), pt(8, hy + 6),
                                      pt(11, sh + 6), pt(-11, sh + 6)])
        poly_free(p["skin_dark"], [pt(-6, hy + 7), pt(6, hy + 7),
                                   pt(9, sh + 5), pt(-9, sh + 5)],
                  outline=False)
        poly_free(p["skin_mid"], [pt(-4, hy + 8), pt(4, hy + 8),
                                  pt(6, sh + 3), pt(-5, sh + 3)],
                  outline=False)

        # Mane belakang: massa besar yang BERAKHIR di bahu (menimpa torso
        # atas), berayun pelan.
        wave = int(math.sin(phase * 1.35) * 1.5)
        if action in ("walk", "attack", "cull", "rage"):
            wave -= 2
        mane = [(hx - 12, sh + 4), (hx - 16 + wave, hy - 1),
                (hx - 14 + wave, hy - 13), (hx - 5, hy - 18),
                (hx + 5, hy - 14), (hx + 10, hy - 3), (hx + 9, sh + 4)]
        poly_free(p["hair_darkest"], [pt(*q) for q in mane])
        mane_in = [(hx - 10, sh + 2), (hx - 13 + wave, hy - 1),
                   (hx - 11 + wave, hy - 11), (hx - 4, hy - 15),
                   (hx + 2, hy - 11), (hx + 7, hy - 2), (hx + 6, sh + 2)]
        poly_free(p["hair_mid"], [pt(*q) for q in mane_in], outline=False)
        # 3 duri mane - bentuk besar (helai 1 px hilang saat di-scale)
        for i, (bx, bh) in enumerate(((-12, 10), (-4, 14), (4, 9))):
            tipx = hx + bx - 3 + wave
            tipy = hy - bh
            poly_free(p["hair_light"], [pt(hx + bx - 2, hy - 4),
                                        pt(tipx, tipy),
                                        pt(hx + bx + 3, hy - 6)],
                      outline=False)
            poly_free(p["hair_shine"], [pt(hx + bx, hy - 5),
                                        pt(tipx + 1, tipy + 2),
                                        pt(hx + bx + 2, hy - 6)],
                      outline=False)

        # Tengkorak + rahang lebar (lebih besar dari versi pertama)
        poly_free(p["skin_darkest"], [pt(hx - 10, hy - 7), pt(hx + 10, hy - 7),
                                      pt(hx + 11, hy + 3), pt(hx + 9, hy + 11),
                                      pt(hx - 4, hy + 12), pt(hx - 10, hy + 3)])
        poly_free(p["skin_mid"], [pt(hx - 9, hy - 6), pt(hx + 9, hy - 6),
                                  pt(hx + 10, hy + 3), pt(hx + 8, hy + 10),
                                  pt(hx - 3, hy + 11), pt(hx - 9, hy + 2)],
                  outline=False)
        # WAJAH: merah terang dari tulang pipi ke rahang; TANPA strip
        # gelap selebar wajah dan TANPA blok shine lebar (keduanya dulu
        # membaca sebagai "helm berkaca/visor"). Focal point = DUA mata
        # amber besar dengan cavum kecil per mata - bukan satu halo
        # tengah yang melebur jadi pita.
        poly_free(p["skin_light"], [pt(hx - 6, hy + 1), pt(hx + 8, hy + 1),
                                    pt(hx + 8, hy + 7), pt(hx - 2, hy + 8)],
                  outline=False)
        poly_free(p["skin_shine"], [pt(hx + 4, hy + 3), pt(hx + 8, hy + 3),
                                    pt(hx + 8, hy + 6),
                                    pt(hx + 4, hy + 6)], outline=False)
        blink = ((phase * 0.6) % 4.2) < 0.16
        if not blink:
            # Urutan PENTING: halo dulu (glow latar), baru blok mata
            # opaque - dulu halo digambar setelahnya dan MENIMPA mata
            # dengan alpha rendah (draw pygame menimpa, bukan blend)
            # sehingga kedua mata jadi totol redup yang melebur.
            flare = 1.0 if (rage or call) else 0.6
            for ex in (hx - 5, hx + 2):
                exx, exy = pt(ex, hy - 1)
                _NS_drakar._aacircle(surface,
                                     (*p["eye_light"],
                                      _NS_drakar._alpha(70 * flare)),
                                     (exx + 1, exy + 1), 3)
                _NS_drakar._rect_st(surface, p["skin_darkest"],
                                    (exx - 1, exy, 5, 4))
                _NS_drakar._rect_st(surface, p["eye_mid"], (exx, exy, 3, 3))
                _NS_drakar._rect_st(surface, p["eye_glow"], (exx, exy, 2, 2))
        else:
            for ex in (hx - 5, hx + 2):
                exx, exy = pt(ex, hy)
                _NS_drakar._rect_st(surface, p["skin_dark"],
                                    (exx - 1, exy, 5, 2))
        # Batang hidung pendek di antara mata
        _NS_drakar._aaline(surface, p["skin_darkest"], pt(hx + 0, hy + 1),
                           pt(hx + 0, hy + 3), 1)
        # Hidung & mulut geram (dua taring tulang)
        _NS_drakar._aaline(surface, p["skin_darkest"], pt(hx + 10, hy + 2),
                           pt(hx + 10, hy + 5), 1)
        _NS_drakar._aaline(surface, p["skin_darkest"], pt(hx + 4, hy + 8),
                           pt(hx + 9, hy + 8), 1)
        poly_free(p["bone_light"], [pt(hx + 3, hy + 8), pt(hx + 4, hy + 10),
                                    pt(hx + 5, hy + 8)], outline=False)
        poly_free(p["bone_light"], [pt(hx + 7, hy + 8), pt(hx + 8, hy + 10),
                                    pt(hx + 9, hy + 8)], outline=False)

        # Jenggot kepang: hanya RAHANG BAWAH (mulai di hy+8 supaya dagu
        # merah terlihat) + satu kepang bercincin kuningan
        poly_free(p["hair_darkest"], [pt(hx - 5, hy + 8), pt(hx + 8, hy + 8),
                                      pt(hx + 7, hy + 13), pt(hx + 2, hy + 16),
                                      pt(hx - 3, hy + 13)])
        poly_free(p["hair_mid"], [pt(hx - 3, hy + 9), pt(hx + 6, hy + 9),
                                  pt(hx + 5, hy + 12), pt(hx + 2, hy + 14),
                                  pt(hx - 2, hy + 12)], outline=False)
        _NS_drakar._aaline(surface, p["shadow_deep"], pt(hx - 5, hy + 14),
                           pt(hx + 7, hy + 13), 1)
        poly_free(p["hair_dark"], [pt(hx + 1, hy + 14), pt(hx + 5, hy + 14),
                                   pt(hx + 4 + wave, hy + 20),
                                   pt(hx + 1 + wave, hy + 21)],
                  outline=False)
        _NS_drakar._aacircle(surface, p["brass_mid"], pt(hx + 3, hy + 15), 1)
        for i in range(3):
            _NS_drakar._aaline(surface, p["hair_darkest"],
                               pt(hx - 2 + i * 3, hy + 9),
                               pt(hx - 1 + i * 3, hy + 15), 1)

        # Helm setengah besi: HANYA dahi (hy-8..hy-5) - tidak menutupi
        # baris mata. Rivet darah di pelipis.
        poly_free(p["armor_darkest"], [pt(hx - 10, hy - 8), pt(hx + 10, hy - 8),
                                       pt(hx + 10, hy - 6), pt(hx - 10, hy - 6)])
        poly_free(p["armor_light"], [pt(hx - 9, hy - 7.5), pt(hx + 9, hy - 7.5),
                                     pt(hx + 9, hy - 6.5),
                                     pt(hx - 9, hy - 6.5)], outline=False)
        _NS_drakar._aacircle(surface, p["blood_mid"], pt(hx + 8, hy - 7), 1)
        _NS_drakar._aacircle(surface, p["blood_mid"], pt(hx - 8, hy - 7), 1)
        # Dua tanduk BANTENG ke ATAS: pangkal tebal di pelipis, ujung
        # menyipit melengkung sedikit ke depan. (Versi mendatar lama
        # terbaca sebagai sayap kelelawar.)
        for sgn in (1, -1):
            basex = hx + sgn * 9
            tipx = basex + sgn * 5 + wave
            midx = basex + sgn * 4
            poly_free(p["bone_darkest"], [pt(basex - sgn * 2, hy - 6),
                                          pt(midx, hy - 13),
                                          pt(tipx, hy - 20),
                                          pt(basex + sgn * 2, hy - 7)])
            poly_free(p["bone_mid"], [pt(basex, hy - 7),
                                      pt(midx - sgn, hy - 13),
                                      pt(tipx + sgn * 0, hy - 18),
                                      pt(tipx + sgn, hy - 19)],
                      outline=False)
            poly_free(p["bone_light"], [pt(basex + sgn, hy - 7),
                                        pt(midx - sgn * 0, hy - 13),
                                        pt(tipx - sgn, hy - 18)],
                      outline=False)

    def _draw_drk_arm(surface, pt, poly_free, dot, limb, f, phase, action, ap,
                      shoulder, elbow, grip, axe_angle, back=False, hot=False):
        """Lengan 2-tulang merah + bracer besi + kepalan di gagang."""
        p = _NS_drakar.PALETTE
        base = p["skin_dark"] if back else p["skin_mid"]
        high = p["skin_mid"] if back else p["skin_light"]
        limb(shoulder, elbow, 8 if back else 9, base, high)
        limb(elbow, grip, 7 if back else 8, base, high)
        # Bracer besi: satu blok di tengah lengan bawah + paku
        bx = int(elbow[0] * 0.4 + grip[0] * 0.6)
        by = int(elbow[1] * 0.4 + grip[1] * 0.6)
        poly_free(p["armor_darkest"], [pt(bx - 4, by - 4), pt(bx + 4, by - 4),
                                       pt(bx + 4, by + 4), pt(bx - 4, by + 4)])
        poly_free(p["armor_mid"], [pt(bx - 3, by - 3), pt(bx + 2, by - 3),
                                   pt(bx + 2, by + 3), pt(bx - 3, by + 3)],
                  outline=False)
        _NS_drakar._aaline(surface, p["armor_light"], pt(bx - 3, by - 2),
                           pt(bx - 3, by + 2), 1)
        _NS_drakar._aacircle(surface, p["brass_mid"], pt(bx + 1, by - 1), 1)
        # Kepalan + highlight buku jari: tanpa ini gagang terlihat
        # "menempel" di tangan, bukan digenggam.
        dot(p["skin_darkest"], *grip, 4 if not back else 3)
        dot(high, *grip, 3 if not back else 2)
        if not back:
            kx, ky = pt(grip[0] + 1, grip[1] - 2)
            _NS_drakar._aacircle(surface, p["skin_shine"], (kx, ky), 2)
        if not back:
            _NS_drakar._draw_drk_axe(surface, pt, f, grip, axe_angle, phase,
                                      action, ap, hot)

    def _draw_drk_axe(surface, pt, f, grip, ang, phase, action, ap, hot):
        """KAPAK PERANG DUA TANGAN - dihitung dari grip + sudut pose.

        Semua titik digambar dalam frame gagang (u = sepanjang gagang ke
        arah mata kapak, v = tegak lurus ke sisi bilah) lalu diputar ke
        ruang lokal. Bilah dibuat TERANG (nilai tertinggi ke-2 setelah
        mata) supaya senjata terbaca sebagai senjata, bukan tonjolan
        gelap. Saat hot (attack/rage/cull) rune darah di bilah menyala.
        """
        p = _NS_drakar.PALETTE
        s, c = math.sin(ang), math.cos(ang)

        def poly(color, pts, outline=True):
            if outline:
                _NS_drakar._poly(surface, p["shadow_deep"],
                                 [(q[0] + f, q[1] + 1) for q in pts])
            _NS_drakar._poly(surface, color, pts)

        def hpt(u, v):
            lx = grip[0] + s * u + c * v
            ly = grip[1] + c * u - s * v
            return pt(lx, ly)

        L = _NS_drakar._axe_len(action)
        # ── Gagang: dari pommel sampai lewat mata kapak
        poly(p["leather_darkest"], [hpt(-10, -2.1), hpt(L + 2, -1.7),
                                         hpt(L + 2, 1.7), hpt(-10, 2.1)])
        poly(p["leather_dark"], [hpt(-8, -0.9), hpt(L + 2, -0.7),
                                      hpt(L + 2, 0.7), hpt(-8, 0.9)],
                  outline=False)
        _NS_drakar._aaline(surface, p["leather_light"], hpt(-8, -0.7),
                           hpt(L + 2, -0.5), 1)
        # Lilitan kulit di gagang (3 band)
        for gu in (-4, 0, 4):
            _NS_drakar._aaline(surface, p["leather_edge"], hpt(gu, -1.6),
                               hpt(gu, 1.6), 1)
        # Pommel kuningan
        px_, py_ = hpt(-9, 0)
        _NS_drakar._aacircle(surface, p["brass_dark"], (px_, py_), 2)
        _NS_drakar._aacircle(surface, p["brass_light"], (px_, py_), 1)

        # ── Mata kapak (socket) + polling belakang
        su = L - 7
        poly(p["armor_darkest"], [hpt(su, -3.2), hpt(su + 5, -3.2),
                                       hpt(su + 5, 3.2), hpt(su, 3.2)])
        poly(p["armor_mid"], [hpt(su + 1, -2.2), hpt(su + 4, -2.2),
                                   hpt(su + 4, 2.2), hpt(su + 1, 2.2)],
                  outline=False)
        _NS_drakar._aaline(surface, p["armor_shine"], hpt(su + 1, -2.0),
                           hpt(su + 4, -2.0), 1)
        for ru in (su + 2,):
            _NS_drakar._aacircle(surface, p["brass_mid"], hpt(ru, 0), 1)

        # ── Bilah JENGGRANG (bearded axe) di sisi +v - lebar hampir
        #    setengah panjang gagang supaya terbaca "kapak perang", bukan
        #    daun putih kecil.
        b0 = su - 2
        blade = [
            (b0, 2.2),            # pangkal bawah socket
            (b0 + 2, 6),          # leher
            (b0 + 1, 16),         # jenggar ke bawah (beard)
            (b0 + 3, 26),         # ujung jenggot
            (b0 + 8, 29),         # busur bawah
            (b0 + 14, 26),        # sisi muka
            (b0 + 18, 17),        # busur depan
            (b0 + 19, 9),         # tanduk atas
            (b0 + 16, 3),         # atas
            (b0 + 9, 0.5),        # duduk di gagang
            (b0 + 2, -1.6),       # pangkal atas
        ]
        poly_pts = [hpt(u, v) for u, v in blade]
        _NS_drakar._poly(surface, p["shadow_deep"],
                         [(q[0] + f, q[1] + 1) for q in poly_pts])
        _NS_drakar._poly(surface, p["blade_mid"], poly_pts)
        # Badan bilah satu tingkat terang (inset dari SEMUA sisi)
        def inset(k):
            out = []
            for (u, v) in blade:
                uu = b0 + (u - b0) * k
                vv = v * k
                out.append(hpt(uu, vv))
            return out

        _NS_drakar._poly(surface, p["blade_light"], inset(0.72))
        # SISI PEMOTONG: pita shine menempel busur luar (dari tanduk
        # atas sampai ujung jenggot) - dulu lapisan terang justru
        # menumpuk di dekat socket sehingga bilah terbaca kecil & redup.
        edge_out = [(b0 + 3, 25.0), (b0 + 8, 28.5), (b0 + 14, 25.5),
                    (b0 + 17.6, 17.0), (b0 + 18.6, 9.2)]
        edge_in = [(u, v - 3.8) for (u, v) in edge_out]
        _NS_drakar._poly(surface, p["blade_shine"],
                         [hpt(u, v) for (u, v) in edge_out + edge_in[::-1]])
        # Garis kecerunan dari shine ke badan (anti-"stiker putih")
        _NS_drakar._aaline(surface, p["blade_light"],
                           hpt(b0 + 15.4, 10), hpt(b0 + 5.4, 22.6), 1)
        # Alur darah di bilah - menyala saat hot
        groove = [hpt(b0 + 3, 8), hpt(b0 + 8, 17), hpt(b0 + 14, 20)]
        ga = _NS_drakar._alpha(90 + 165 * (1.0 if hot else 0.15) *
                               (0.75 + 0.25 * math.sin(phase * 2.6)))
        _NS_drakar._aaline(surface, p["blade_dark"], groove[0], groove[1], 1)
        _NS_drakar._aaline(surface, (*p["blood_mid"], ga), groove[0],
                           groove[2], 1)
        if hot:
            _NS_drakar._aaline(surface, (*p["blood_hot"], ga), groove[1],
                               groove[2], 1)
        # Spike belakang (-v): pembacaan "senjata berat, dua arah"
        poly(p["armor_darkest"], [hpt(b0 + 1, -1.8), hpt(b0 + 10, -4),
                                       hpt(b0 + 11, -8), hpt(b0 + 5, -5),
                                       hpt(b0 + 1, -3.4)])
        poly(p["armor_mid"], [hpt(b0 + 2, -2), hpt(b0 + 8, -4),
                                   hpt(b0 + 8.5, -6)], outline=False)

    def _draw_drk_rimlight(surface, pt, f, phase, rage, call, hot):
        """Rim light merah tipis di tepi yang menghadap cahaya.

        Semua unit masterwork lain punya "sinyal" warna di tepian
        (Grimjam api, Vex void cyan, Gornak ungu) sehingga terbaca saat
        bertumpuk. Drakar memakai darah/ember; 1 px saja tapi di posisi
        yang tepat: puncak tanduk, tepi pauldron, mata kapak, ujung boot.
        """
        p = _NS_drakar.PALETTE
        sh = _NS_drakar.SHOULDER_Y
        hy = _NS_drakar.HEAD_Y + int(math.sin(phase * 0.55) * 0.9)
        pulse = 1.0 if hot else (0.72 + 0.28 * math.sin(phase * 1.8))
        a = _NS_drakar._alpha(150 * pulse)
        col = (*p["blood_mid"], a)
        # Puncak mane + tanduk depan
        _NS_drakar._aaline(surface, col, pt(-10, hy - 13), pt(0, hy - 15), 1)
        # Tepi pelat dada & sabuk
        _NS_drakar._aaline(surface, col, pt(14, sh + 1), pt(14, -8), 1)
        _NS_drakar._aaline(surface, (*p["blood_hot"], min(255, a + 30)),
                           pt(-13, 1), pt(13, 1), 1)
        # Garis cahaya di lutut & ujung boot
        for sx in (-6, 11):
            _NS_drakar._aaline(surface, col, pt(sx, 24), pt(sx + 1, 32), 1)
            _NS_drakar._aacircle(surface, col, pt(sx + 1, 45), 1)

    # ==================================================================
    # PORTRAIT LOD - material tambahan (Hero Shop / panel)
    # ==================================================================
    def _draw_drk_weave(surface, pt, f):
        """Tenun kain & grain kulit - HANYA portrait LOD.

        Dither 1-px seperti ini justru jadi noise setelah jalur hero
        men-smoothscale sprite, jadi dibatasi ke mode detail.
        """
        p = _NS_drakar.PALETTE
        for i in range(9):
            wx, wy = pt(-10 + (i % 4) * 4, 9 + (i // 4) * 4)
            _NS_drakar._rect_st(surface, (*p["leather_light"], 90),
                                (wx, wy, 1, 1))
        for i in range(7):
            x0, y0 = -12 + i * 4, -14 + (i % 3) * 6
            _NS_drakar._rect_st(surface, (*p["skin_shine"], 70),
                                (pt(x0, y0)[0], pt(x0, y0)[1], 1, 1))

    def _draw_drk_masterwork_details(surface, pt, f, phase, action):
        """Detail frekuensi tinggi; di skala arena tanda-tanda ini hanya
        menjadi noise, jadi hanya dinyalakan saat portrait."""
        p = _NS_drakar.PALETTE
        hx = 1 if f > 0 else -1
        cy = _NS_drakar.HEAD_Y + int(math.sin(phase * 0.55) * 0.9)
        # Helai mane ekstra di atas krist
        for i in range(7):
            bx = hx - 8 + i * 2
            by = cy - 8 - abs(i - 3)
            wx = bx - 3 + int(math.sin(phase * 1.4 + i) * 2)
            _NS_drakar._aaline(surface, p["hair_shine"], pt(bx, by),
                               pt(wx, by - 11 - (i % 3)), 1)
        # Serat jenggot
        for i in range(4):
            _NS_drakar._aaline(surface, p["hair_mid"],
                               pt(hx - 4 + i * 2, cy + 7),
                               pt(hx - 3 + i * 2, cy + 14), 1)
        # Alis tebal
        _NS_drakar._aaline(surface, p["hair_darkest"], pt(hx - 2, cy - 4),
                           pt(hx + 7, cy - 5), 1)
        # Grain kulit pada bahu & dada
        for i in range(10):
            dx = -10 + (i % 5) * 4
            dy = -19 + (i // 5) * 8
            _NS_drakar._aaline(surface, (*p["skin_shine"], 110), pt(dx, dy),
                               pt(dx + 1, dy), 1)
        # Otot leher
        _NS_drakar._aaline(surface, p["skin_dark"], pt(hx - 4, -21),
                           pt(hx - 1, -17), 1)
        # Jahitan loincloth
        for xx in (-5, 0, 5):
            _NS_drakar._aaline(surface, (*p["leather_edge"], 120), pt(xx, 10),
                               pt(xx + 1, 24), 1)
        # Tato perang di lengan (dua garis merah)
        for i in range(3):
            _NS_drakar._aaline(surface, (*p["blood_mid"], 150),
                               pt(10 + i * 2, -28 + i * 6),
                               pt(13 + i * 2, -26 + i * 6), 1)
        # Ukiran pelat & paku pauldron
        _NS_drakar._aaline(surface, (*p["armor_shine"], 165), pt(9, -33),
                           pt(15, -32), 1)
        _NS_drakar._aaline(surface, (*p["armor_shine"], 165), pt(9, -29),
                           pt(15, -28), 1)
        for sx, sy in ((16, -40), (18, -36), (13, -35), (-16, -39)):
            _NS_drakar._aacircle(surface, (*p["armor_shine"], 150),
                                 pt(sx, sy), 1)
        # Ukiran rune darah di bilah (di atas alur)
        for i in range(4):
            t = i / 4
            _NS_drakar._aaline(surface, (*p["blood_light"], 170),
                               pt(14 + int(t * 9), -6 - int(t * 12)),
                               pt(15 + int(t * 9), -5 - int(t * 12)), 1)

    # ==================================================================
    # EFEK DASAR - ditundukan pada karakter
    # ==================================================================
    def _draw_shadow(surface, x, y):
        """Bayangan kontak tunggal yang lembek (base_boss menggambar satu
        lagi; ini dipertipis supaya tidak jadi dua piringan hitam)."""
        p = _NS_drakar.PALETTE
        K = _NS_drakar.SCALE
        bw, bh = int(66 * K), int(19 * K)
        sh = pygame.Surface((bw, bh), pygame.SRCALPHA)
        for w, h, a in ((int(48 * K), int(11 * K), 70),
                        (int(34 * K), int(8 * K), 90),
                        (int(20 * K), int(5 * K), 110)):
            _NS_drakar._ellipse(sh, (0, 0, 0, a),
                                (bw // 2 - w // 2, bh // 2 - h // 2, w, h))
        _NS_drakar._ellipse(sh, (*p["mist_darkest"], 60),
                            (int(8 * K), int(3 * K), int(50 * K), int(12 * K)))
        # Titik kontak per telapak: badan "menekan" tanah, bukan mengapung
        for side in (-1, 1):
            fx = bw // 2 + int(side * 10 * K)
            _NS_drakar._ellipse(sh, (0, 0, 0, 130),
                                (fx - int(6 * K), int(bh * 0.62),
                                 int(12 * K), int(4 * K)))
        surface.blit(sh, (int(x) - bw // 2, int(y) - bh // 2))

    def _draw_rage_aura(surface, x, y, phase, skill):
        """KABUT MERAH - identitas "The Might of the Red Mist".

        Kabut digambar LANGSUNG ke surface dalam beberapa LOBUS yang
        bergeser mengikuti fase (bukan satu oval geometris) supaya
        terbaca sebagai kabut yang bergolak. Alpha tiap lapis < 100:
        menumpuk tebal di layar, tapi di canvas SRCALPHA (pengukuran
        skala hero) tidak pernah ikut terhitung badan padat.
        """
        p = _NS_drakar.PALETTE
        pulse = 1.0 if skill else math.sin(phase * 0.7) * 0.25 + 0.72
        K = _NS_drakar.SCALE

        # ── Lobus kabut bergolak: 4 gumpalan besar yang naik-turun &
        #    bergeser dengan fase sendiri (organik, bukan kapsul)
        lobes = ((-20, -18, 30, 38, 0.0), (16, -10, 28, 34, 1.7),
                 (-4, 22, 32, 26, 3.1), (2, -44, 22, 20, 4.4))
        for bx, by, rx, ry, seed in lobes:
            dx = int(math.sin(phase * 0.8 + seed) * 4)
            dy = int(math.sin(phase * 0.62 + seed * 1.3) * 3)
            for k, (col, a) in enumerate((("mist_darkest", 85),
                                          ("mist_dark", 72),
                                          ("mist_mid", 62))):
                shrink = 1 - k * 0.18
                rxk, ryk = int(rx * K * shrink), int(ry * K * shrink)
                _NS_drakar._ellipse(
                    surface, (*p[col], _NS_drakar._alpha(a * pulse)),
                    (int(x) + int(bx * K) + dx - rxk,
                     int(y) + int(by * K) + dy - ryk, rxk * 2, ryk * 2))

        # ── Inti gelap: siluet badan tetap POP dari kabutnya sendiri
        _NS_drakar._ellipse(surface, (14, 2, 5, _NS_drakar._alpha(92 * pulse)),
                            (int(x) - int(26 * K), int(y) - int(40 * K),
                             int(52 * K), int(70 * K)))
        # Rim menyala mengelilingi inti
        _NS_drakar._ellipse(surface, (*p["mist_mid"],
                                      _NS_drakar._alpha(92 * pulse)),
                            (int(x) - int(26 * K), int(y) - int(40 * K),
                             int(52 * K), int(70 * K)), 2)
        _NS_drakar._ellipse(surface, (*p["mist_light"],
                                      _NS_drakar._alpha(88 * pulse)),
                            (int(x) - int(28 * K), int(y) - int(42 * K),
                             int(56 * K), int(74 * K)), 1)

        # ── Bara orbit: presence versi lama, alpha rendah
        n = 13
        for i in range(n):
            t = ((phase * 0.33 + i / n) % 1.0)
            ang = t * math.tau
            r = _NS_drakar._s(24) + int(math.sin(phase * 1.3 + i * 2) * 4)
            sx = int(x) + int(math.cos(ang) * r * 1.3)
            sy = int(y) + 6 - int(t * 32)
            a = _NS_drakar._alpha(110 * (1 - t) + 50 *
                                  math.sin(phase * 3 + i))
            if a <= 0:
                continue
            rad = 3 if i % 3 == 0 else 2
            _NS_drakar._aacircle(surface, (*p["blood_mid"], a), (sx, sy), rad)
            _NS_drakar._aacircle(surface, (*p["blood_hot"], a), (sx, sy), 1)
            if i % 3 == 0:
                _NS_drakar._rect_st(surface, (*p["blood_shine"], a),
                                    (sx, sy - 2, 1, 3))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Kolam darah + cincin rune di bawah kaki - gelap penuh dengan
        rim menyala (jangkar visual boss, mood versi lama)."""
        p = _NS_drakar.PALETTE
        pulse = math.sin(phase * 1.1) * 0.25 + 0.75
        gy = y + _NS_drakar.GROUND_DY
        bright = 1.15 if skill else 0.95
        # Kolam gelap penuh (bukan ring) - jangkar visual boss
        rw, rh = _NS_drakar._s(32), _NS_drakar._s(9)
        _NS_drakar._ellipse(surface,
                            (20, 2, 4, _NS_drakar._alpha(230 * pulse * bright)),
                            (x - rw, gy - rh, rw * 2, rh * 2))
        _NS_drakar._ellipse(surface,
                            (*p["rune_dark"],
                             _NS_drakar._alpha(210 * pulse * bright)),
                            (x - rw + 3, gy - rh + 1, rw * 2 - 6,
                             rh * 2 - 2))
        # Kabut darah di atas kolam
        rw3, rh3 = _NS_drakar._s(27), _NS_drakar._s(7)
        _NS_drakar._ellipse(surface,
                            (*p["mist_dark"],
                             _NS_drakar._alpha(150 * pulse * bright)),
                            (x - rw3, gy - rh3, rw3 * 2, rh3 * 2))
        # Rim menyala + retakan rune
        rw2, rh2 = _NS_drakar._s(25), _NS_drakar._s(6)
        _NS_drakar._ellipse(surface,
                            (*p["rune_mid"],
                             _NS_drakar._alpha(210 * pulse * bright)),
                            (x - rw2, gy - rh2, rw2 * 2, rh2 * 2), 2)
        t0, t1 = _NS_drakar._s(23), _NS_drakar._s(31)
        ty0, ty1 = _NS_drakar._s(5), _NS_drakar._s(8)
        for i in range(8):
            ang = phase * 0.4 + i * math.tau / 8
            _NS_drakar._aaline(
                surface,
                (*p["rune_light"], _NS_drakar._alpha(220 * pulse * bright)),
                (x + int(math.cos(ang) * t0), gy + int(math.sin(ang) * ty0)),
                (x + int(math.cos(ang) * t1), gy + int(math.sin(ang) * ty1)),
                1)
        irw, irh = _NS_drakar._s(14), _NS_drakar._s(4)
        _NS_drakar._ellipse(surface,
                            (*p["rune_light"],
                             _NS_drakar._alpha(190 * pulse * bright)),
                            (x - irw, gy - irh, irw * 2, irh * 2), 1)
        _NS_drakar._aacircle(surface, (*p["rune_shine"],
                                       _NS_drakar._alpha(230 * pulse)),
                             (int(x), int(gy)), 2)
        if skill in ("e", "r"):
            ew, eh = _NS_drakar._s(34), _NS_drakar._s(9)
            _NS_drakar._ellipse(
                surface, (*p["rune_shine"], _NS_drakar._alpha(170 * pulse)),
                (x - ew, gy - eh, ew * 2, eh * 2), 1)

    def _draw_footfall_dust(surface, x, y, facing, phase):
        """Kepul debu di tapak yang mendarat (deterministik dari phase)."""
        p = _NS_drakar.PALETTE
        contact = abs(math.sin(phase * 1.1))
        if contact > 0.72:
            return
        gy = y + _NS_drakar.GROUND_DY
        k = _NS_drakar._s
        for side in (-1, 1):
            for i in range(3):
                t = (contact + i * 0.3) % 1.0
                a = _NS_drakar._alpha(150 * (1.0 - t) * (0.72 - contact))
                if a <= 0:
                    continue
                px = x + side * k(8 + i * 2 + t * 6) + facing * k(t * 4)
                py = gy - k(t * 5)
                _NS_drakar._aacircle(surface, (*p["dust"], a), (px, py),
                                     max(1, k(2 - t)))
                _NS_drakar._rect_st(surface, (*p["white"], a // 2),
                                    (px, py, 1, 1))

    # ==================================================================
    # CLEAVE TRAIL - mengikuti lintasan mata kapak yang sebenarnya
    # ==================================================================
    def _draw_cleave_trail(surface, boss, x, y, facing, phase, progress):
        """Pita slash dari trail MATA KAPAK (bukan busur titik melayang).

        trail dihitung dari tabel sudut yang sama dengan rig, jadi pita
        selalu menyatu dengan bilah dan otomatis benar saat kapak
        diperbesar/dikecilkan.
        """
        if progress < 0.24 or progress > 0.92:
            return
        p = _NS_drakar.PALETTE
        lean, root_y = _NS_drakar._rig_shift("attack", phase, progress)

        def scr(lx, ly):
            return _NS_drakar._local_to_screen(x, y, facing, lean, root_y,
                                                lx, ly)

        def tip_at(ap):
            hx, hy = _NS_drakar._axe_head_local("attack", phase, ap)
            ang = _NS_drakar._axe_angle(phase, "attack", ap)
            tx = hx + math.cos(ang) * 13
            ty = hy - math.sin(ang) * 13
            return scr(tx, ty)

        steps = 7
        trail = []
        for i in range(steps):
            t = i / (steps - 1)
            trail.append(tip_at(max(0.0, min(1.0,
                                             progress - 0.30 + t * 0.30))))
        pivot = scr(*_NS_drakar._front_grip_local("attack", progress, phase))
        fade = 1.0 - max(0.0, (progress - 0.70) / 0.22)
        alpha = _NS_drakar._alpha(230 * fade)
        if alpha <= 0:
            return
        # Kapak = senjata berat: pita lebih lebar dari pedang gornak dan
        # warna darah/ember (bukan ungu) supaya tema keluarga terbaca.
        for col, off, mul in (("blood_darkest", 10, 0.62),
                              ("blood_mid", 5, 0.9),
                              ("blood_shine", 1, 1.0)):
            outer, inner = [], []
            for i, q in enumerate(trail):
                t = i / (steps - 1)
                w = max(0.5, (1 - abs(t - 0.8)) * off * (0.35 + 0.65 * t))
                vx, vy = q[0] - pivot[0], q[1] - pivot[1]
                ln = math.hypot(vx, vy) or 1.0
                nx, ny = -vy / ln, vx / ln
                outer.append((q[0] + nx * w, q[1] + ny * w))
                inner.append((q[0] - nx * w * 0.55, q[1] - ny * w * 0.55))
            _NS_drakar._poly(surface,
                             (*p[col], _NS_drakar._alpha(alpha * mul)),
                             outer + inner[::-1])
        if 0.40 <= progress <= 0.62:
            # Impact: percikan dari mata kapak + guncangan mikro
            tip = trail[-1]
            for i in range(5):
                ang = -math.pi / 2 + i * math.pi / 4
                ex = tip[0] + int(math.cos(ang) * 9)
                ey = tip[1] + int(math.sin(ang) * 9)
                _NS_drakar._aaline(surface, (*p["blood_hot"], alpha), tip,
                                   (ex, ey), 1)

    # ==================================================================
    # SKILL Q - BATTLE HUNGER (rage self-buff, 90 frame)
    # ==================================================================
    def _draw_battlehunger_ground(surface, boss, x, y, timer, phase):
        """Rune tanah membakar lebih terang + bara merambat naik."""
        p = _NS_drakar.PALETTE
        duration = _NS_drakar.SKILL_DUR["q"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        intensity = math.sin(min(1.0, progress * 3) * math.pi * 0.5)
        gy = y + _NS_drakar.GROUND_DY
        rw = int(_NS_drakar._s(26) * (1 + 0.12 * math.sin(phase * 3)))
        rh = int(rw * 0.25)
        _NS_drakar._ellipse(surface, (*p["blood_dark"],
                                      _NS_drakar._alpha(170 * intensity)),
                            (x - rw, gy - rh, rw * 2, rh * 2), 2)
        for i in range(8):
            ang = i * math.tau / 8 + phase * 0.8
            _NS_drakar._aaline(surface, (*p["blood_mid"],
                                         _NS_drakar._alpha(190 * intensity)),
                               (x + int(math.cos(ang) * rw * 0.55),
                                gy + int(math.sin(ang) * rh * 0.55)),
                               (x + int(math.cos(ang) * rw),
                                gy + int(math.sin(ang) * rh)), 1)
        # Bara merambat naik dari tanah ke badan
        for i in range(5):
            t = ((phase * 0.5 + i * 0.2) % 1.0)
            px = x + int(math.sin(i * 2.1 + phase) * 10 * (1 - t))
            py = gy - int(t * 60 * _NS_drakar.SCALE)
            a = _NS_drakar._alpha(200 * intensity * (1 - t))
            if a <= 0:
                continue
            _NS_drakar._aacircle(surface, (*p["blood_mid"], a), (px, py), 2)
            _NS_drakar._aacircle(surface, (*p["blood_hot"], a), (px, py), 1)

    def _draw_battlehunger_foreground(surface, boss, x, y, timer, phase):
        """Vortex bara mengorbit torso + mata membara (rig) + rim merah."""
        p = _NS_drakar.PALETTE
        duration = _NS_drakar.SKILL_DUR["q"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress > 0.92:
            fade = (1.0 - progress) / 0.08
        else:
            fade = min(1.0, progress * 6)
        # Orbit bara: dua lapis, radius napas
        for layer, (rr, n) in enumerate(((_NS_drakar._s(20), 5),
                                          (_NS_drakar._s(27), 7))):
            for i in range(n):
                t = ((phase * (0.55 + 0.12 * layer) + i / n) % 1.0)
                ang = t * math.tau
                rx = rr * (1.18 + 0.1 * math.sin(phase + i))
                ry = rr * 0.8
                px = x + int(math.cos(ang) * rx)
                py = y - _NS_drakar._s(6) + int(math.sin(ang) * ry)
                a = _NS_drakar._alpha(170 * fade * (1 - abs(t - 0.5) * 0.8))
                if a <= 0:
                    continue
                _NS_drakar._aacircle(surface, (*p["blood_dark"], a),
                                     (px, py), 2)
                _NS_drakar._aacircle(surface, (*p["blood_light"], a),
                                     (px, py), 1)
                if i % 2 == 0:
                    _NS_drakar._rect_st(surface, (*p["blood_shine"], a),
                                        (px, py - 2, 1, 3))
        # Rim merah di badan (badan tetap subjek)
        rim = _NS_drakar._alpha(100 * fade)
        rw, rh = _NS_drakar._s(16), _NS_drakar._s(22)
        _NS_drakar._ellipse(surface, (*p["blood_mid"], rim),
                            (int(x) - rw, int(y) - rh - _NS_drakar.LIFT,
                             rw * 2, rh * 2 + _NS_drakar._s(2)), 1)

    # ==================================================================
    # SKILL W - COUNTER HELIX (spin AOE, 45 frame)
    # ==================================================================
    def _draw_counterhelix_ground(surface, boss, x, y, timer, phase):
        """Cincin tanah berputar + retakan radial."""
        p = _NS_drakar.PALETTE
        duration = _NS_drakar.SKILL_DUR["w"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        grow = 1.0 if progress < 0.8 else (1.0 - progress) / 0.2
        gy = y + _NS_drakar.GROUND_DY
        r = int(_NS_drakar._s(24) * min(1.0, progress * 4) * grow) + 4
        _NS_drakar._ellipse(surface, (*p["blood_darkest"],
                                      _NS_drakar._alpha(150 * grow)),
                            (x - r, gy - r // 3, r * 2, max(3, r * 2 // 3)), 2)
        for i in range(10):
            ang = phase * 5.2 + i * math.tau / 10
            _NS_drakar._aaline(surface, (*p["blood_mid"],
                                         _NS_drakar._alpha(200 * grow)),
                               (x + int(math.cos(ang) * r * 0.45),
                                gy + int(math.sin(ang) * r * 0.15)),
                               (x + int(math.cos(ang) * r),
                                gy + int(math.sin(ang) * r * 0.33)), 1)

    def _draw_counterhelix_foreground(surface, boss, x, y, timer, phase):
        """Piringan helix kapak: dua pita mengikuti MATA KAPAK yang
        berputar + percikan di tepi depan.

        Sudut putar memakai rumus yang sama dengan _axe_angle("helix"),
        jadi pita selalu lahir dari bilah, bukan dari elips kosong.
        """
        p = _NS_drakar.PALETTE
        duration = _NS_drakar.SKILL_DUR["w"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.12:
            grow = progress / 0.12
        elif progress > 0.82:
            grow = max(0.0, (1.0 - progress) / 0.18)
        else:
            grow = 1.0
        if grow <= 0:
            return
        lean, root_y = _NS_drakar._rig_shift("helix", phase, 0.0)
        facing = getattr(boss, "direction", 1) or 1
        cy0 = y - _NS_drakar._s(4)

        def scr(lx, ly):
            return _NS_drakar._local_to_screen(x, y, facing, lean, root_y,
                                                lx, ly)

        grip = _NS_drakar._front_grip_local("helix", 0.0, phase)
        L = _NS_drakar._axe_len("helix")
        rx = _NS_drakar._s(L + 6) * (0.5 + 0.5 * grow)
        ry = _NS_drakar._s(11) * (0.5 + 0.5 * grow)

        def blade_point(spin):
            """Mata kapak pada fase putaran spin (mengikuti pose rig)."""
            ang0 = _NS_drakar._axe_angle(phase, "helix", 0.0)
            hx = grip[0] + math.sin(ang0) * L
            hy = grip[1] + math.cos(ang0) * L
            # Orbit elips di sekitar dada - fase = spin
            return scr(grip[0] + math.sin(spin) * (L + 6),
                       grip[1] + math.cos(spin) * 11)

        spin0 = phase * 7.0
        steps = 9
        for band, (col, off, mul) in enumerate(
                (("blood_darkest", 9, 0.6), ("blood_mid", 4, 0.9),
                 ("blood_shine", 1, 1.0))):
            pts = []
            for i in range(steps):
                t = i / (steps - 1)
                spin = spin0 - t * 1.5
                pts.append(blade_point(spin))
            alpha = _NS_drakar._alpha(220 * grow)
            for i in range(len(pts) - 1):
                t = 1 - i / (len(pts) - 1)
                w = max(1, int(off * t * (0.4 + 0.6 * grow)))
                _NS_drakar._aaline(surface,
                                   (*p[col], _NS_drakar._alpha(alpha * mul * t)),
                                   pts[i], pts[i + 1], w)
        # Ujung depan: percik bara keluar dari arah putar
        lead = blade_point(spin0)
        for i in range(4):
            ang = spin0 + i * 0.5
            ex = lead[0] + int(math.cos(ang) * (7 + i * 3))
            ey = lead[1] + int(math.sin(ang) * 3) - i * 2
            a = _NS_drakar._alpha(200 * grow * (1 - i * 0.2))
            _NS_drakar._aacircle(surface, (*p["blood_light"], a), (ex, ey), 2)
            _NS_drakar._rect_st(surface, (*p["blood_shine"], a),
                                (ex, ey, 1, 1))
        # Goresan kecepatan di lingkar luar
        for i in range(3):
            t = ((phase * 1.6 + i / 3.0) % 1.0)
            spin = spin0 - (0.6 + t * 2.4)
            qx, qy = blade_point(spin)
            vx = x + (qx - x) * 1.12
            vy = cy0 + (qy - cy0) * 1.12
            _NS_drakar._aaline(surface, (*p["blood_mid"],
                                         _NS_drakar._alpha(120 * grow)),
                               (qx, qy), (int(vx), int(vy)), 1)

    # ==================================================================
    # SKILL E - BERSERKER'S CALL (roar taunt, 60 frame)
    # ==================================================================
    def _draw_berserkerscall_ground(surface, boss, x, y, timer, phase):
        """Rune meledak terang + retakan tanah radiasi."""
        p = _NS_drakar.PALETTE
        duration = _NS_drakar.SKILL_DUR["e"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Roar: denyut cepat di awal, mereda di akhir
        punch = math.sin(min(1.0, progress * 3.5) * math.pi)
        fade = 1.0 if progress < 0.78 else (1.0 - progress) / 0.22
        gy = y + _NS_drakar.GROUND_DY
        r = int(_NS_drakar._s(27) * (1 + 0.1 * math.sin(phase * 9)))
        _NS_drakar._ellipse(surface, (*p["blood_dark"],
                                      _NS_drakar._alpha((120 + 90 * punch)
                                                        * fade)),
                            (x - r, gy - r // 3, r * 2, max(3, r * 2 // 3)), 2)
        _NS_drakar._ellipse(surface, (*p["rune_shine"],
                                      _NS_drakar._alpha(110 * fade)),
                            (x - r + 4, gy - r // 3 + 2, r * 2 - 8,
                             max(2, r * 2 // 3 - 6)), 1)
        # Retakan radiasi (deterministik)
        for i in range(6):
            ang = i * math.tau / 6 + 0.35
            r1 = int(r * 0.7)
            r2 = int(r * (1.25 + 0.12 * math.sin(phase * 6 + i)))
            x1 = x + int(math.cos(ang) * r1)
            y1 = gy + int(math.sin(ang) * r1 * 0.32)
            x2 = x + int(math.cos(ang) * r2)
            y2 = gy + int(math.sin(ang) * r2 * 0.32)
            _NS_drakar._aaline(surface, (*p["blood_mid"],
                                         _NS_drakar._alpha(180 * fade)),
                               (x1, y1), (x2, y2), 1)
            _NS_drakar._aacircle(surface, (*p["blood_hot"],
                                           _NS_drakar._alpha(160 * fade)),
                                 (x2, y2), 1)

    def _draw_berserkerscall_foreground(surface, boss, x, y, timer, phase):
        """Gelombang roar dari mulut + getaran + debu terangkat.

        2-3 busur memuai dari kepala (bukan lingkaran penuh yang
        menenggelamkan badan), lalu memudar.
        """
        p = _NS_drakar.PALETTE
        duration = _NS_drakar.SKILL_DUR["e"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress > 0.72:
            return
        facing = getattr(boss, "direction", 1) or 1
        head_y = y - _NS_drakar._s(_NS_drakar.HEAD_Y * -1) - 4
        mouth_x = x + facing * _NS_drakar._s(8)
        # Busur roar: 3 gelombang berjalan
        for i in range(3):
            t = ((progress * 2.6 + i * 0.24) % 1.0)
            r = _NS_drakar._s(10) + t * _NS_drakar._s(30)
            a = _NS_drakar._alpha(200 * (1 - t))
            if a <= 0:
                continue
            rect = (int(mouth_x - r), int(head_y - r * 0.8),
                    int(r * 2), int(r * 1.6))
            temp = pygame.Surface((rect[2] + 6, rect[3] + 6), pygame.SRCALPHA)
            ccx, ccy = rect[2] // 2 + 3, rect[3] // 2 + 3
            # Busur setengah menghadap arah hadap (roar, bukan dome)
            for wdt, mul in ((3, 0.6), (1, 1.0)):
                _arc = []
                for k in range(9):
                    ang = -0.55 + k * (1.1 / 8)
                    _arc.append((int(ccx + math.cos(ang) * (r - wdt)),
                                 int(ccy + math.sin(ang) * (r * 0.8 - wdt))))
                if facing < 0:
                    _arc = [(rect[2] + 6 - qx, qy) for qx, qy in _arc]
                _NS_drakar._aaline(surface,
                                   (*p["blood_mid"],
                                    _NS_drakar._alpha(a * mul)),
                                   _arc[0], _arc[-1], wdt)
                for qx, qy in _arc[1:-1]:
                    _NS_drakar._aacircle(surface,
                                         (*p["blood_light"],
                                          _NS_drakar._alpha(a * mul * 0.7)),
                                         (qx, qy), 1)
        # Debu terangkat di kaki (gema langkah kencang)
        gy = y + _NS_drakar.GROUND_DY
        for i in range(6):
            t = ((phase * 0.9 + i / 6.0) % 1.0)
            px = x + int(math.sin(i * 2.4 + phase) * (14 + t * 22))
            py = gy - int(t * 10)
            a = _NS_drakar._alpha(140 * (1 - t))
            if a > 0:
                _NS_drakar._aacircle(surface, (*p["dust"], a), (px, py),
                                     max(1, _NS_drakar._s(2 - t)))

    # ==================================================================
    # SKILL R - CULLING BLADE (eksekusi, 60 frame)
    # ==================================================================
    def _draw_cullingblade_ground(surface, boss, x, y, timer, phase):
        """Rune eksekusi di bawah TARGET + garis pengisian dari kapak."""
        p = _NS_drakar.PALETTE
        tx, ty = _NS_drakar._target_position(boss, x, y)
        duration = _NS_drakar.SKILL_DUR["r"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        t = min(1.0, progress * 2.5)
        fade = 1.0 if progress < 0.8 else (1.0 - progress) / 0.2
        rw = int(_NS_drakar._s(26) * t) + 2
        rh = max(2, rw // 3)
        _NS_drakar._ellipse(surface, (*p["blood_darkest"],
                                      _NS_drakar._alpha(190 * t * fade)),
                            (tx - rw, ty - rh + 4, rw * 2, rh * 2), 2)
        _NS_drakar._ellipse(surface, (*p["blood_mid"],
                                      _NS_drakar._alpha(170 * t * fade)),
                            (tx - rw + 4, ty - rh + 6, rw * 2 - 8,
                             max(1, rh * 2 - 8)), 1)
        if progress < 0.55:
            # Garis pengisian: dari mata kapak menuju target
            tip = _NS_drakar._tip_screen(boss, x, y)
            k = progress / 0.55
            for i in range(6):
                tt = (phase * 1.1 + i / 6.0) % 1.0 * k
                px = int(tip[0] + (tx - tip[0]) * tt)
                py = int(tip[1] + (ty - tip[1]) * tt)
                a = _NS_drakar._alpha(200 * (1 - abs(tt - 0.5) * 1.4) * k)
                if a > 0:
                    _NS_drakar._aacircle(surface, (*p["blood_light"], a),
                                         (px, py), 2)
                    _NS_drakar._rect_st(surface, (*p["blood_shine"], a),
                                        (px, py, 1, 1))

    def _draw_cullingblade_foreground(surface, boss, x, y, timer, phase):
        """Tiga babak: (1) kapak membara terangkat, (2) tebasan raksasa
        lintasan mata kapak -> target + kilat putih, (3) ledakan eksekusi
        di target + bara yang jatuh."""
        p = _NS_drakar.PALETTE
        tx, ty = _NS_drakar._target_position(boss, x, y)
        duration = _NS_drakar.SKILL_DUR["r"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = getattr(boss, "direction", 1) or 1
        tip = _NS_drakar._tip_screen(boss, x, y)

        if progress < 0.42:
            # (1) Charge: bara CONVERGE ke mata kapak (arah aliran jelas)
            t = progress / 0.42
            r_core = 3 + int(t * 6)
            for k in range(r_core + 3, 0, -1):
                a = _NS_drakar._alpha(190 * (r_core + 3 - k) / (r_core + 3)
                                      * (0.4 + t))
                _NS_drakar._aacircle(surface, (*p["blood_dark"], a),
                                     (tip[0], tip[1]), k)
            for col, rr in (("blood_mid", r_core),
                            ("blood_light", max(1, r_core - 2)),
                            ("blood_shine", max(1, r_core - 4))):
                _NS_drakar._aacircle(surface, p[col], (tip[0], tip[1]), rr)
            for i in range(6):
                ang = phase * 4 + i * math.tau / 6
                dist = (1 - t) * _NS_drakar._s(16) + 4
                sx = tip[0] + int(math.cos(ang) * dist)
                sy = tip[1] + int(math.sin(ang) * dist)
                _NS_drakar._aaline(surface, (*p["blood_mid"], 190),
                                   (sx, sy), (tip[0], tip[1]), 1)
        elif progress < 0.62:
            # (2) Cleave raksasa: SABIT melengkung melintasi target
            # (busur radius dari grip, menyapu dari arah wind-up ke arah
            # impact) - dulu kerucut lurus yang terbaca sebagai balok.
            t = (progress - 0.42) / 0.20
            lean, root_y = _NS_drakar._rig_shift("cull", phase, 0.6)

            def scr(lx, ly):
                return _NS_drakar._local_to_screen(x, y, facing, lean,
                                                    root_y, lx, ly)
            grip = scr(*_NS_drakar._front_grip_local("cull", 0.6, phase))
            base = math.atan2(ty - grip[1], tx - grip[0])
            sweep = 1.6 * (1.0 - t)          # busur menyusut saat selesai
            a0 = base - sweep
            r_in = _NS_drakar._s(22)
            r_out = _NS_drakar._s(34) * (0.7 + 0.3 * (1 - t))
            alpha = _NS_drakar._alpha(225 * (1 - t * 0.6))
            seg = 10
            span = (base + 0.35) - a0
            for col, w_out, w_in, mul in (("blood_darkest", 6, 3, 0.55),
                                          ("blood_mid", 4, 2, 0.85),
                                          ("blood_shine", 2, 1, 1.0)):
                outer, inner = [], []
                for i in range(seg + 1):
                    ang = a0 + span * i / seg
                    # Lebar pita memuncak di dekat lead edge (sisi target)
                    k = i / seg
                    w = (w_in + (w_out - w_in) * k) * (0.5 + 0.5 * k)
                    outer.append((grip[0] + math.cos(ang) *
                                  (r_out + w), grip[1] + math.sin(ang) *
                                  (r_out + w) * 0.92))
                    inner.append((grip[0] + math.cos(ang) *
                                  (r_out - w), grip[1] + math.sin(ang) *
                                  (r_out - w) * 0.92))
                _NS_drakar._poly(surface,
                                 (*p[col], _NS_drakar._alpha(alpha * mul)),
                                 outer + inner[::-1])
            # Lead edge: kilat putih kecil tepat di depan target
            lead = (int(grip[0] + math.cos(base + 0.2) * r_out),
                    int(grip[1] + math.sin(base + 0.2) * r_out))
            _NS_drakar._aacircle(surface, (*p["white"],
                                           _NS_drakar._alpha(210 *
                                                             (1 - t))),
                                 lead, 3)
        else:
            # (3) Eksekusi: busur mekar + sumbu radial + bara jatuh
            t = (progress - 0.62) / 0.38
            r = int(_NS_drakar._s(16) + t * _NS_drakar._s(22))
            a = _NS_drakar._alpha(235 * (1 - t))
            _NS_drakar._aacircle(surface, (*p["blood_darkest"], a),
                                 (tx, ty), r + 3, 4)
            _NS_drakar._aacircle(surface, (*p["blood_dark"], a),
                                 (tx, ty), r, 3)
            _NS_drakar._aacircle(surface, (*p["blood_mid"], a), (tx, ty),
                                 max(1, r - 7), 2)
            _NS_drakar._aacircle(surface, (*p["blood_shine"], a), (tx, ty),
                                 max(1, int(r * 0.35)))
            for i in range(12):
                ang = i * math.tau / 12 + t * 0.4
                ex = tx + int(math.cos(ang) * (r + 4))
                ey = ty + int(math.sin(ang) * (r + 4) * 0.85)
                _NS_drakar._aaline(surface, (*p["blood_hot"], a), (tx, ty),
                                   (ex, ey), 2 if i % 3 == 0 else 1)
                _NS_drakar._rect_st(surface, (*p["white"], a),
                                    (ex, ey, 1, 1))
            for i in range(8):
                tt = (phase * 0.5 + i * 0.13) % 1.0
                px = tx + int(math.sin(phase * 1.4 + i) * (12 + i))
                py = ty - int(tt * 26)
                aa = _NS_drakar._alpha(200 * (1 - t) * (1 - tt))
                if aa > 0:
                    _NS_drakar._aacircle(surface, (*p["blood_dark"], aa),
                                         (px, py), 3)
                    _NS_drakar._aacircle(surface, (*p["blood_mid"], aa),
                                         (px, py), 2)
                    _NS_drakar._rect_st(surface, (*p["blood_shine"], aa),
                                        (px, py, 1, 1))
        # Rim merah di badan saat mengisi (badan tetap subjek)
        rim = _NS_drakar._alpha(110 * min(1.0, progress * 3))
        rw, rh = _NS_drakar._s(16), _NS_drakar._s(23)
        _NS_drakar._ellipse(surface, (*p["blood_mid"], rim),
                            (int(x) - rw, int(y) - rh - _NS_drakar.LIFT,
                             rw * 2, rh * 2 + _NS_drakar._s(2)), 1)


# ====================================================================
# ABADDON
# ====================================================================
class _NS_abaddon:
    """Namespace abaddon - isi asli tidak diubah."""

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ---------------------------------------------------------------------------
    # HD Color Palette - Abaddon inspired dark purple / cyan flame
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Cape / cloth - deep purple
        "cape_darkest":   (18,   8,  32),
        "cape_dark":      (35,  20,  62),
        "cape_mid":       (60,  38, 105),
        "cape_light":     (95,  70, 155),
        "cape_high":      (140, 115, 195),
        "cape_shine":     (185, 165, 225),

        # Armor - dark purple/black with gold trim
        "armor_darkest":  (12,   8,  22),
        "armor_dark":     (28,  20,  48),
        "armor_mid":      (55,  42,  85),
        "armor_light":    (95,  78, 130),
        "armor_high":     (150, 130, 180),

        # Gold trim
        "gold_darkest":   (65,  42,  10),
        "gold_dark":      (115, 85,  25),
        "gold_mid":       (175, 140, 45),
        "gold_light":     (225, 190, 85),
        "gold_shine":     (250, 225, 145),

        # Horse body - dark blue-purple
        "horse_darkest":  (10,  15,  30),
        "horse_dark":     (25,  35,  60),
        "horse_mid":      (50,  70, 105),
        "horse_light":    (85, 115, 155),
        "horse_high":     (135, 170, 200),

        # Cyan flame / mist - the signature color
        "flame_darkest":  (5,   45,  55),
        "flame_dark":     (15,  95, 115),
        "flame_mid":      (40, 170, 185),
        "flame_light":    (95, 230, 235),
        "flame_bright":   (160, 250, 250),
        "flame_hot":      (215, 255, 255),
        "flame_white":    (240, 255, 255),

        # Sword blade - cyan energy blade
        "blade_darkest":  (30,  55,  70),
        "blade_dark":     (60, 120, 145),
        "blade_mid":      (110, 190, 210),
        "blade_light":    (170, 235, 240),
        "blade_shine":    (220, 250, 250),

        # Purple magic (for skills)
        "magic_darkest":  (20,   5,  50),
        "magic_dark":     (55,  25, 115),
        "magic_mid":      (105, 60, 180),
        "magic_light":    (165, 120, 225),
        "magic_bright":   (210, 175, 250),
        "magic_hot":      (240, 220, 255),

        # Eye glow
        "eye_dark":       (30,  90, 100),
        "eye_mid":        (90, 200, 205),
        "eye_bright":     (170, 245, 245),
        "eye_hot":        (230, 255, 255),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (3,   4,   8),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_abaddon._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_abaddon.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_abaddon._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width
            min_y = min(sy, ey) - width
            w = abs(ex - sx) + width * 4 + 4
            h = abs(ey - sy) + width * 4 + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.line(temp, color,
                             (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), max(1, width))
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), max(1, width))


    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_abaddon._clamp(color)
        if len(color) == 4 and color[3] < 255:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, min_y = min(xs) - 2, min(ys) - 2
            w = max(xs) - min_x + 4
            h = max(ys) - min_y + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            shifted = [(p[0] - min_x, p[1] - min_y) for p in points]
            pygame.draw.polygon(temp, color, shifted)
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.polygon(surface, color[:3], points)


    def _ellipse(surface, color, rect, width=0):
        color = _NS_abaddon._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, rw, rh), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3], rect, width)


    def _rect(surface, color, rect, border_radius=0):
        color = _NS_abaddon._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, rw, rh), border_radius=border_radius)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3], rect, border_radius=border_radius)


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
        return int(x + 200 / float(getattr(boss, "_render_scale", 1.0) or 1.0) * getattr(boss, "direction", 1)), int(y)


    # ---------------------------------------------------------------------------
    # Cyan flame helper
    # ---------------------------------------------------------------------------
    def _draw_cyan_flame(surface, x, y, size, phase, alpha=255):
        """Draw a cyan mist flame particle."""
        flick = math.sin(phase * 3) * 0.15 + 1.0
        s = int(size * flick)
        if s < 1:
            return
        _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_darkest"], alpha // 3), (x, y), s + 3)
        _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_dark"], alpha // 2), (x, y), s + 1)
        _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_mid"], alpha), (x, y), s)
        _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_light"], alpha), (x, y - 1),
                  max(1, s - 2))
        _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], min(255, alpha)),
                  (x, y - 2), max(1, s - 4))
        if s > 3:
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_hot"], min(255, alpha)),
                      (x, y - 3), max(1, s - 6))


    def _draw_flame_streamer(surface, x, y, height, phase, alpha=220):
        """Draw a rising cyan flame streamer."""
        for i in range(height):
            t = i / max(1, height)
            wave = math.sin(phase * 3 + t * 5) * 2
            size = int(3 * (1 - t * 0.7))
            if size < 1:
                break
            fx = x + int(wave)
            fy = y - i
            f_alpha = int(alpha * (1 - t * 0.6))
            _NS_abaddon._draw_cyan_flame(surface, fx, fy, size, phase, f_alpha)


    # ---------------------------------------------------------------------------
    # PROJECTILE / EFFECT SYSTEM
    # ---------------------------------------------------------------------------
    class MistCoilProjectile:
        """Q - Purple/cyan orb projectile."""
        def __init__(self, sx, sy, tx, ty, speed=6.0):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            self.trail = []

        def update(self):
            if not self.alive:
                return
            self.age += 1
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < self.speed + 4:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 14:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            if not self.alive and self.age < 3:
                return

            # Long misty trail (purple/cyan)
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(40 + i * 15)
                r = max(1, 6 - (len(self.trail) - i) // 2)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_dark"], alpha), (tx, ty), r + 2)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_mid"], alpha), (tx, ty), r)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_mid"], alpha // 2),
                          (tx, ty), max(1, r - 1))

            if self.alive:
                px, py = int(self.x), int(self.y)
                # Multi-layer orb
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_darkest"], 180), (px, py), 10)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_dark"], 220), (px, py), 8)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_mid"], 240), (px, py), 6)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_mid"], 240), (px, py), 4)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], 250), (px, py), 3)
                _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_hot"], (px, py), 2)
                _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_white"], (px, py), 1)

                # Mist trails
                for i in range(4):
                    angle = phase * 4 + i * math.pi / 2
                    sx = px + int(math.cos(angle) * 10)
                    sy = py + int(math.sin(angle) * 10)
                    _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_light"], 200), (sx, sy), 2)
                    _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_hot"], (sx, sy), 1)


    class DarknessGaleProjectile:
        """E - Dark wave/gale that travels forward."""
        def __init__(self, sx, sy, direction, max_dist=250):
            self.x = float(sx)
            self.y = float(sy)
            self.direction = direction
            self.max_dist = max_dist
            self.speed = 11.0
            self.alive = True
            self.age = 0
            self.max_age = 25

        def update(self):
            if not self.alive:
                return
            self.age += 1
            self.x += self.speed * self.direction
            if self.age >= self.max_age:
                self.alive = False

        def draw(self, surface, phase):
            if not self.alive and self.age < 2:
                return
            t = self.age / self.max_age
            alpha = int(255 * (1 - t * 0.5))
            px, py = int(self.x), int(self.y)

            # Elongated gale/wind streak
            for i in range(-6, 7):
                # Multiple parallel streaks
                for streak_off in (-4, 0, 4):
                    streak_y = py + i * 2 + streak_off
                    # Length varies
                    for length_i in range(20):
                        lt = length_i / 20
                        lx = px - int(lt * 40) * self.direction
                        ly = streak_y + int(math.sin(lt * 5 + phase + i) * 2)

                        w_alpha = int(alpha * (1 - abs(i) / 7) * (1 - lt * 0.4))
                        if w_alpha <= 0:
                            continue

                        _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_dark"], w_alpha),
                                  (lx, ly), 2)
                        _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_dark"], w_alpha),
                                  (lx, ly), 1)

            # Bright forward core
            for i in range(-4, 5):
                core_y = py + i * 2
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_mid"], alpha),
                          (px, core_y), 3)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], alpha),
                          (px, core_y), 2)
                _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_hot"], (px, core_y), 1)

            # Bright tip
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], alpha),
                      (px + 8 * self.direction, py), 4)
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_hot"],
                      (px + 8 * self.direction, py), 3)
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_white"],
                      (px + 8 * self.direction, py), 1)


    class DeathSeverWave:
        """R - Purple crescent wave."""
        def __init__(self, sx, sy, direction, max_dist=200):
            self.x = float(sx)
            self.y = float(sy)
            self.direction = direction
            self.max_dist = max_dist
            self.speed = 9.0
            self.alive = True
            self.age = 0
            self.max_age = 22

        def update(self):
            if not self.alive:
                return
            self.age += 1
            self.x += self.speed * self.direction
            if self.age >= self.max_age:
                self.alive = False

        def draw(self, surface, phase):
            if not self.alive:
                return
            t = self.age / self.max_age
            alpha = int(255 * (1 - t * 0.4))
            px, py = int(self.x), int(self.y)

            # Purple crescent wave
            for i in range(-14, 15):
                curve = math.cos(i * 0.2) * 8
                vy = py + i * 2
                vx = px + int(curve) * self.direction

                w_alpha = int(alpha * (1 - abs(i) / 15))
                if w_alpha <= 0:
                    continue

                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_darkest"], w_alpha),
                          (vx, vy), 5)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_dark"], w_alpha),
                          (vx, vy), 4)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_mid"], w_alpha),
                          (vx, vy), 3)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_light"], w_alpha),
                          (vx, vy), 2)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_bright"], w_alpha),
                          (vx, vy), 1)

            # Bright core arc
            for i in range(-12, 13):
                curve = math.cos(i * 0.2) * 8
                vy = py + i * 2
                vx = px + int(curve) * self.direction
                core_alpha = int(alpha * (1 - abs(i) / 13))
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_hot"], core_alpha),
                          (vx, vy), 2)
                _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["white"], (vx, vy), 1)

            # Trailing purple sparks
            for i in range(6):
                angle = phase * 3 + i * math.pi / 3
                r = 15 + int(math.sin(phase + i) * 4)
                sx = px + int(math.cos(angle) * r) * self.direction
                sy = py + int(math.sin(angle) * r)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_bright"], alpha), (sx, sy), 2)
                _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["magic_hot"], (sx, sy), 1)


    # ---------------------------------------------------------------------------
    # State management
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_ab_last_x"):
            boss._ab_last_x = boss.x
            boss._ab_last_y = boss.y
            return False
        dx = abs(boss.x - boss._ab_last_x)
        dy = abs(boss.y - boss._ab_last_y)
        boss._ab_last_x = boss.x
        boss._ab_last_y = boss.y
        return dx + dy > 0.3


    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_ab_prev_timer", 0))
        active = bool(getattr(boss, "_ab_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._ab_attack_active = True
            boss._ab_attack_frame = 0
            active = True
        elif active:
            boss._ab_attack_frame = int(getattr(boss, "_ab_attack_frame", 0)) + 1
            if boss._ab_attack_frame > cooldown:
                boss._ab_attack_active = False
                boss._ab_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._ab_attack_active = False
            boss._ab_attack_frame = 0
            active = False

        boss._ab_prev_timer = timer
        boss._ab_attack_progress = (
            min(1.0, getattr(boss, "_ab_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_ab_projectiles"):
            boss._ab_projectiles = []
        for p in boss._ab_projectiles:
            p.update()
            p.draw(surface, phase)
        boss._ab_projectiles = [p for p in boss._ab_projectiles
                               if p.alive or p.age < 8]


    def _spawn_mist_coil(boss, x, y):
        if not hasattr(boss, "_ab_projectiles"):
            boss._ab_projectiles = []
        tx, ty = _NS_abaddon._target_position(boss, x, y)
        sx = x + 26 * boss.direction
        sy = y - 10
        boss._ab_projectiles.append(_NS_abaddon.MistCoilProjectile(sx, sy, tx, ty, speed=6.5))


    def _spawn_darkness_gale(boss, x, y):
        if not hasattr(boss, "_ab_projectiles"):
            boss._ab_projectiles = []
        sx = x + 30 * boss.direction
        sy = y - 8
        boss._ab_projectiles.append(_NS_abaddon.DarknessGaleProjectile(sx, sy, boss.direction))


    def _spawn_death_sever(boss, x, y):
        if not hasattr(boss, "_ab_projectiles"):
            boss._ab_projectiles = []
        sx = x + 30 * boss.direction
        sy = y - 8
        boss._ab_projectiles.append(_NS_abaddon.DeathSeverWave(sx, sy, boss.direction))


    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_abaddon(surface, boss, x, y):
        """Entry point."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_abaddon._detect_moving(boss)
        _NS_abaddon._update_attack_anim(boss)

        attacking = (
            getattr(boss, "_ab_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 50) - 15
        )

        # ---------- Background layers ----------
        _NS_abaddon._draw_dark_aura(surface, x, y, pulse)
        _NS_abaddon._draw_ground_runes(surface, x, y + 48, pulse, active_skill)

        # ---------- Character body ----------
        if active_skill == "q":
            _NS_abaddon._draw_abaddon_mist_coil(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_abaddon._draw_abaddon_darkness_gale(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_abaddon._draw_abaddon_death_sever(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_abaddon._draw_abaddon_melee_attack(surface, boss, x, y)
        elif moving:
            _NS_abaddon._draw_abaddon_walk(surface, boss, x, y)
        else:
            _NS_abaddon._draw_abaddon_idle(surface, boss, x, y)

        # Aphotic Shield goes over body
        if active_skill == "w":
            _NS_abaddon._draw_aphotic_shield(surface, boss, x, y, skill_timer, pulse)

        # ---------- Projectiles ----------
        _NS_abaddon._manage_projectiles(boss, surface, pulse)


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_abaddon_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.8) * 2)
        _NS_abaddon._draw_shadow(surface, x, y + 58)
        _NS_abaddon._draw_horse_flame_base(surface, x, y + 45, boss.pulse)
        _NS_abaddon._draw_abaddon_full(surface, x, y + bob, boss.direction, boss.pulse, "idle")


    def _draw_abaddon_walk(surface, boss, x, y):
        phase = boss.pulse * 2.2
        bob = int(abs(math.sin(phase * 1.3)) * 3)
        sway = int(math.sin(phase) * 2)
        _NS_abaddon._draw_shadow(surface, x + sway, y + 58)
        _NS_abaddon._draw_horse_flame_base(surface, x + sway, y + 45, phase, trail=True,
                              facing=boss.direction)
        _NS_abaddon._draw_abaddon_full(surface, x + sway, y - bob, boss.direction, phase, "walk")


    def _draw_abaddon_melee_attack(surface, boss, x, y):
        """Sword swing on horseback."""
        progress = getattr(boss, "_ab_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        lunge = int(math.sin(progress * math.pi) * 4) * boss.direction
        _NS_abaddon._draw_shadow(surface, x + lunge, y + 58)
        _NS_abaddon._draw_horse_flame_base(surface, x + lunge, y + 45, boss.pulse, intense=True)
        _NS_abaddon._draw_abaddon_full(surface, x + lunge, y, boss.direction, boss.pulse,
                          "melee", progress)
        _NS_abaddon._draw_sword_swing_trail(surface, x + lunge, y - 8, boss.direction, progress)


    def _draw_abaddon_mist_coil(surface, boss, x, y, timer, phase):
        """Q - Mist Coil cast."""
        cast_duration = 45
        elapsed = cast_duration - timer
        progress = max(0.0, min(1.0, elapsed / cast_duration))

        if 0.3 < progress < 0.4 and not getattr(boss, "_ab_coil_spawned", False):
            _NS_abaddon._spawn_mist_coil(boss, x, y)
            boss._ab_coil_spawned = True
        if progress < 0.2 or progress > 0.9:
            boss._ab_coil_spawned = False

        _NS_abaddon._draw_shadow(surface, x, y + 58)
        _NS_abaddon._draw_horse_flame_base(surface, x, y + 45, phase, intense=True)
        _NS_abaddon._draw_abaddon_full(surface, x, y, boss.direction, phase, "cast", progress)

        # Casting glow on sword tip
        if 0.15 < progress < 0.5:
            sword_x = x + 32 * boss.direction
            sword_y = y - 20
            glow_pulse = math.sin(phase * 4) * 0.3 + 0.7
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_dark"], 180),
                      (sword_x, sword_y), int(12 * glow_pulse))
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_mid"], 220),
                      (sword_x, sword_y), int(8 * glow_pulse))
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], 240),
                      (sword_x, sword_y), int(5 * glow_pulse))
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_hot"],
                      (sword_x, sword_y), max(1, int(3 * glow_pulse)))


    def _draw_abaddon_darkness_gale(surface, boss, x, y, timer, phase):
        """E - Darkness Gale cast."""
        cast_duration = 40
        elapsed = cast_duration - timer
        progress = max(0.0, min(1.0, elapsed / cast_duration))

        if 0.3 < progress < 0.4 and not getattr(boss, "_ab_gale_spawned", False):
            _NS_abaddon._spawn_darkness_gale(boss, x, y)
            boss._ab_gale_spawned = True
        if progress < 0.2 or progress > 0.9:
            boss._ab_gale_spawned = False

        _NS_abaddon._draw_shadow(surface, x, y + 58)
        _NS_abaddon._draw_horse_flame_base(surface, x, y + 45, phase, intense=True)
        _NS_abaddon._draw_abaddon_full(surface, x, y, boss.direction, phase, "cast", progress)


    def _draw_abaddon_death_sever(surface, boss, x, y, timer, phase):
        """R - Death Sever cast."""
        cast_duration = 50
        elapsed = cast_duration - timer
        progress = max(0.0, min(1.0, elapsed / cast_duration))

        if 0.35 < progress < 0.45 and not getattr(boss, "_ab_sever_spawned", False):
            _NS_abaddon._spawn_death_sever(boss, x, y)
            boss._ab_sever_spawned = True
        if progress < 0.2 or progress > 0.9:
            boss._ab_sever_spawned = False

        lunge = int(math.sin(progress * math.pi) * 6) * boss.direction
        _NS_abaddon._draw_shadow(surface, x + lunge, y + 58)
        _NS_abaddon._draw_horse_flame_base(surface, x + lunge, y + 45, phase, intense=True)
        _NS_abaddon._draw_abaddon_full(surface, x + lunge, y, boss.direction, phase,
                          "melee", progress)
        _NS_abaddon._draw_sword_purple_trail(surface, x + lunge, y - 8, boss.direction,
                                 progress, phase)


    # ===================================================================
    # FULL COMPOSITE - Abaddon + Horse
    # ===================================================================
    def _draw_abaddon_full(surface, cx, cy, facing, phase, action,
                          attack_progress=0):
        """Draw horse + Abaddon rider composition."""
        # Horse (drawn first as background)
        _NS_abaddon._draw_horse(surface, cx, cy + 15, facing, phase)

        # Abaddon rider on top
        _NS_abaddon._draw_abaddon_rider(surface, cx, cy - 8, facing, phase, action,
                           attack_progress)


    # ===================================================================
    # HORSE (ghostly mount)
    # ===================================================================
    def _draw_horse(surface, cx, cy, facing, phase):
        """Ghostly horse mount with cyan flames."""
        step = math.sin(phase * 1.5) * 1

        # Horse body (elongated oval)
        body_pts = [
            (cx - 25 * facing, cy - 2),
            (cx - 22 * facing, cy - 10),
            (cx - 10 * facing, cy - 12),
            (cx + 10 * facing, cy - 12),
            (cx + 20 * facing, cy - 10),
            (cx + 25 * facing, cy - 5),
            (cx + 23 * facing, cy + 8),
            (cx + 12 * facing, cy + 12),
            (cx - 12 * facing, cy + 12),
            (cx - 22 * facing, cy + 8),
        ]
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in body_pts])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_darkest"], body_pts)
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_dark"], [
            (cx - 23 * facing, cy - 1),
            (cx - 20 * facing, cy - 8),
            (cx - 10 * facing, cy - 10),
            (cx + 10 * facing, cy - 10),
            (cx + 18 * facing, cy - 8),
            (cx + 23 * facing, cy - 4),
            (cx + 21 * facing, cy + 7),
            (cx + 10 * facing, cy + 10),
            (cx - 10 * facing, cy + 10),
            (cx - 20 * facing, cy + 7),
        ])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_mid"], [
            (cx - 18 * facing, cy - 3),
            (cx - 15 * facing, cy - 7),
            (cx - 5 * facing, cy - 8),
            (cx + 5 * facing, cy - 8),
            (cx + 15 * facing, cy - 7),
            (cx + 20 * facing, cy - 3),
            (cx + 15 * facing, cy + 6),
            (cx - 15 * facing, cy + 6),
        ])

        # Body highlight (top of back)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["horse_light"], (cx - 5 * facing, cy - 7), 3)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["horse_high"], (cx - 6 * facing, cy - 8), 1)

        # ===== FRONT LEGS =====
        for leg_off in (-8, 0):
            lx = cx + (12 + leg_off) * facing
            # Upper leg
            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["shadow_deep"],
                    (lx + 1, cy + 11), (lx + int(step) + 1, cy + 20), 4)
            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["horse_darkest"],
                    (lx, cy + 11), (lx + int(step), cy + 20), 3)
            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["horse_dark"],
                    (lx, cy + 11), (lx + int(step), cy + 20), 2)
            # Lower leg (dissolves into flame)
            for h in range(8):
                t = h / 8
                fy = cy + 20 + h
                fx = lx + int(step)
                f_alpha = int(200 * (1 - t * 0.5))
                _NS_abaddon._draw_cyan_flame(surface, fx, fy, max(1, 3 - h // 2),
                                phase + h, f_alpha)

        # ===== BACK LEGS =====
        for leg_off in (-8, 0):
            lx = cx + (-12 - leg_off) * facing
            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["shadow_deep"],
                    (lx + 1, cy + 11), (lx - int(step) + 1, cy + 20), 4)
            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["horse_darkest"],
                    (lx, cy + 11), (lx - int(step), cy + 20), 3)
            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["horse_dark"],
                    (lx, cy + 11), (lx - int(step), cy + 20), 2)
            # Flame at hoof
            for h in range(8):
                t = h / 8
                fy = cy + 20 + h
                fx = lx - int(step)
                f_alpha = int(200 * (1 - t * 0.5))
                _NS_abaddon._draw_cyan_flame(surface, fx, fy, max(1, 3 - h // 2),
                                phase + h + 2, f_alpha)

        # ===== HORSE NECK =====
        neck_x = cx + 20 * facing
        neck_y = cy - 8
        neck_top_x = cx + 26 * facing
        neck_top_y = cy - 20

        # Neck shape
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_darkest"], [
            (neck_x - 3 * facing, neck_y),
            (neck_x + 3 * facing, neck_y - 2),
            (neck_top_x + 4 * facing, neck_top_y),
            (neck_top_x - 3 * facing, neck_top_y + 3),
        ])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_dark"], [
            (neck_x - 2 * facing, neck_y - 1),
            (neck_x + 3 * facing, neck_y - 2),
            (neck_top_x + 3 * facing, neck_top_y + 1),
            (neck_top_x - 2 * facing, neck_top_y + 3),
        ])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_mid"], [
            (neck_x, neck_y - 1),
            (neck_x + 2 * facing, neck_y - 2),
            (neck_top_x + 2 * facing, neck_top_y + 1),
            (neck_top_x - 1 * facing, neck_top_y + 3),
        ])

        # ===== HORSE HEAD =====
        head_x = neck_top_x + 2 * facing
        head_y = neck_top_y

        # Head shape (elongated)
        head_pts = [
            (head_x - 5 * facing, head_y - 3),
            (head_x + 3 * facing, head_y - 5),
            (head_x + 12 * facing, head_y - 2),
            (head_x + 13 * facing, head_y + 3),
            (head_x + 8 * facing, head_y + 6),
            (head_x - 3 * facing, head_y + 5),
            (head_x - 6 * facing, head_y + 2),
        ]
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["shadow_deep"], [(p[0] + 1, p[1] + 1) for p in head_pts])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_darkest"], head_pts)
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_dark"], [
            (head_x - 4 * facing, head_y - 2),
            (head_x + 3 * facing, head_y - 4),
            (head_x + 11 * facing, head_y - 1),
            (head_x + 12 * facing, head_y + 3),
            (head_x + 7 * facing, head_y + 5),
            (head_x - 3 * facing, head_y + 4),
            (head_x - 5 * facing, head_y + 1),
        ])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_mid"], [
            (head_x - 2 * facing, head_y - 1),
            (head_x + 2 * facing, head_y - 3),
            (head_x + 9 * facing, head_y - 1),
            (head_x + 10 * facing, head_y + 2),
            (head_x + 5 * facing, head_y + 4),
            (head_x - 2 * facing, head_y + 3),
        ])

        # Horse ears
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_darkest"], [
            (head_x + 1 * facing, head_y - 5),
            (head_x + 3 * facing, head_y - 5),
            (head_x + 2 * facing, head_y - 9),
        ])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_darkest"], [
            (head_x + 5 * facing, head_y - 5),
            (head_x + 7 * facing, head_y - 5),
            (head_x + 6 * facing, head_y - 9),
        ])

        # Horse glowing eye
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["shadow_deep"],
                  (head_x + 5 * facing, head_y), 2)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_dark"],
                  (head_x + 5 * facing, head_y), max(1, int(2 * eye_pulse)))
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_bright"],
                  (head_x + 5 * facing, head_y), 1)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_hot"],
                  (head_x + 5 * facing, head_y - 1), 1)

        # Nostril
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["shadow_deep"],
                  (head_x + 11 * facing, head_y + 2), 1)

        # ===== HORSE MANE (cyan flames along neck) =====
        for i in range(6):
            t = i / 6
            mane_x = neck_x + int((neck_top_x - neck_x) * t) - 3 * facing
            mane_y = neck_y + int((neck_top_y - neck_y) * t) - 2
            _NS_abaddon._draw_flame_streamer(surface, mane_x, mane_y + 3, 6 + i, phase + i,
                                200)

        # ===== HORSE TAIL (flame) =====
        tail_x = cx - 25 * facing
        tail_y = cy - 3
        for i in range(6):
            t = i / 6
            # Tail curves down
            tx = tail_x - int(t * 15) * facing
            ty = tail_y + int(t * 15) + int(math.sin(phase + i) * 2)
            _NS_abaddon._draw_flame_streamer(surface, tx, ty, 8 - i, phase + i, 200)

        # Also curling tail flame
        for i in range(4):
            angle = math.pi * (0.6 + i * 0.15)
            fx = tail_x + int(math.cos(angle) * 10) * facing
            fy = tail_y + int(math.sin(angle) * 12)
            _NS_abaddon._draw_cyan_flame(surface, fx, fy, 4 - i, phase + i, 220)

        # ===== HORSE SADDLE/HARNESS =====
        # Saddle blanket (purple)
        saddle_pts = [
            (cx - 10 * facing, cy - 12),
            (cx + 12 * facing, cy - 12),
            (cx + 10 * facing, cy - 5),
            (cx - 12 * facing, cy - 5),
        ]
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["cape_darkest"], saddle_pts)
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["cape_dark"], [
            (cx - 8 * facing, cy - 11),
            (cx + 10 * facing, cy - 11),
            (cx + 8 * facing, cy - 6),
            (cx - 10 * facing, cy - 6),
        ])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["cape_mid"], [
            (cx - 6 * facing, cy - 10),
            (cx + 6 * facing, cy - 10),
            (cx + 5 * facing, cy - 7),
            (cx - 7 * facing, cy - 7),
        ])

        # Gold saddle trim
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_dark"],
                (cx - 10 * facing, cy - 5), (cx + 10 * facing, cy - 5), 2)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_mid"],
                (cx - 10 * facing, cy - 5), (cx + 10 * facing, cy - 5), 1)

        # Reins (from Abaddon's hand to horse head)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["leather_mid"] if "leather_mid" in _NS_abaddon.PALETTE
                else _NS_abaddon.PALETTE["cape_darkest"],
                (cx + 5 * facing, cy - 10), (head_x + 2 * facing, head_y + 3), 1)


    # ===================================================================
    # ABADDON RIDER
    # ===================================================================
    def _draw_abaddon_rider(surface, cx, cy, facing, phase, action,
                           attack_progress=0):
        """Draw Abaddon on horseback."""
        # Cape (flowing behind)
        _NS_abaddon._draw_cape(surface, cx, cy + 5, facing, phase, action)

        # Rider legs (visible sitting on horse)
        _NS_abaddon._draw_rider_legs(surface, cx, cy + 12, facing, phase)

        # Torso armor
        _NS_abaddon._draw_torso(surface, cx, cy - 3, phase)

        # Pauldrons
        _NS_abaddon._draw_pauldrons(surface, cx, cy - 10, phase)

        # Arms (one holding sword, one holding reins)
        if action in ("melee",):
            _NS_abaddon._draw_melee_arms(surface, cx, cy - 3, facing, phase, attack_progress)
        elif action == "cast":
            _NS_abaddon._draw_casting_arms(surface, cx, cy - 3, facing, phase, attack_progress)
        else:
            _NS_abaddon._draw_idle_arms(surface, cx, cy - 3, facing, phase)

        # Head with hood
        _NS_abaddon._draw_hooded_head(surface, cx, cy - 22, facing, phase)

        # Floating cyan flames around body
        _NS_abaddon._draw_body_flames(surface, cx, cy, phase)


    def _draw_cape(surface, cx, cy, facing, phase, action):
        """Purple flowing cape."""
        wave = math.sin(phase * 0.8) * 3
        wave2 = math.sin(phase * 1.2 + 0.5) * 2

        cape_outer = [
            (cx - 14, cy - 20),
            (cx - 20, cy - 5),
            (cx - 24 - int(wave), cy + 12),
            (cx - 22 - int(wave2), cy + 25),
            (cx - 10, cy + 30 + int(abs(wave))),
            (cx + 10, cy + 30 + int(abs(wave))),
            (cx + 22 + int(wave2), cy + 25),
            (cx + 24 + int(wave), cy + 12),
            (cx + 20, cy - 5),
            (cx + 14, cy - 20),
        ]
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in cape_outer])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["cape_darkest"], cape_outer)

        cape_mid = [
            (cx - 12, cy - 18),
            (cx - 18, cy - 5),
            (cx - 22 - int(wave * 0.7), cy + 10),
            (cx - 18 - int(wave2 * 0.7), cy + 22),
            (cx - 6, cy + 26),
            (cx + 6, cy + 26),
            (cx + 18 + int(wave2 * 0.7), cy + 22),
            (cx + 22 + int(wave * 0.7), cy + 10),
            (cx + 18, cy - 5),
            (cx + 12, cy - 18),
        ]
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["cape_dark"], cape_mid)

        cape_inner = [
            (cx - 10, cy - 15),
            (cx - 15, cy - 5),
            (cx - 18, cy + 8),
            (cx - 10, cy + 20),
            (cx, cy + 22),
            (cx + 10, cy + 20),
            (cx + 18, cy + 8),
            (cx + 15, cy - 5),
            (cx + 10, cy - 15),
        ]
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["cape_mid"], cape_inner)

        # Cape highlights
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["cape_light"],
                (cx - 8, cy - 12), (cx - 12, cy + 15), 1)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["cape_light"],
                (cx + 8, cy - 12), (cx + 12, cy + 15), 1)


    def _draw_rider_legs(surface, cx, cy, facing, phase):
        """Rider legs on horse."""
        for side in (-1, 1):
            # Thigh (goes to knee)
            thigh_x = cx + side * 5
            thigh_top = cy
            thigh_bot = cy + 8

            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["shadow_deep"],
                    (thigh_x + 1, thigh_top + 1), (thigh_x + 1, thigh_bot + 1), 6)
            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["armor_darkest"],
                    (thigh_x, thigh_top), (thigh_x, thigh_bot), 5)
            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["armor_dark"],
                    (thigh_x, thigh_top), (thigh_x, thigh_bot), 3)
            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["armor_mid"],
                    (thigh_x - 1, thigh_top), (thigh_x - 1, thigh_bot), 1)

            # Boot area (sticking out below horse)
            boot_x = thigh_x
            boot_y = thigh_bot + 4
            _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["shadow_deep"],
                  (boot_x - 4, boot_y - 2, 8, 8))
            _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["armor_darkest"],
                  (boot_x - 3, boot_y - 2, 7, 7))
            _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["armor_dark"],
                  (boot_x - 3, boot_y - 2, 7, 5))
            # Gold boot detail
            _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["gold_dark"], (boot_x - 3, boot_y, 7, 1))
            _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["gold_mid"], (boot_x - 3, boot_y, 6, 1))


    def _draw_torso(surface, cx, cy, phase):
        """Torso armor."""
        # Shadow
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["shadow_deep"], [
            (cx - 12 + 2, cy - 8 + 2), (cx + 12 + 2, cy - 8 + 2),
            (cx + 11 + 2, cy + 12 + 2), (cx - 11 + 2, cy + 12 + 2),
        ])

        torso_pts = [
            (cx - 12, cy - 8),
            (cx + 12, cy - 8),
            (cx + 13, cy + 5),
            (cx + 10, cy + 12),
            (cx - 10, cy + 12),
            (cx - 13, cy + 5),
        ]
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["armor_darkest"], torso_pts)
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["armor_dark"], [
            (cx - 10, cy - 6),
            (cx + 10, cy - 6),
            (cx + 11, cy + 5),
            (cx + 8, cy + 10),
            (cx - 8, cy + 10),
            (cx - 11, cy + 5),
        ])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["armor_mid"], [
            (cx - 7, cy - 3),
            (cx + 7, cy - 3),
            (cx + 8, cy + 4),
            (cx + 5, cy + 8),
            (cx - 5, cy + 8),
            (cx - 8, cy + 4),
        ])

        # Gold trim (V-shape on chest)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_dark"],
                (cx - 10, cy - 6), (cx, cy + 8), 2)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_dark"],
                (cx + 10, cy - 6), (cx, cy + 8), 2)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_mid"],
                (cx - 9, cy - 5), (cx, cy + 7), 1)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_mid"],
                (cx + 9, cy - 5), (cx, cy + 7), 1)

        # Central gem (cyan)
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_darkest"], (cx, cy + 1), 4)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_dark"], (cx, cy + 1), 3)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_mid"], (cx, cy + 1),
                  max(1, int(3 * pulse)))
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_bright"], (cx, cy + 1),
                  max(1, int(2 * pulse)))
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_hot"], (cx, cy + 1), 1)

        # Gold outline
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["gold_mid"], (cx, cy + 1), 4, 1)

        # Belt
        _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["cape_darkest"], (cx - 13, cy + 10, 26, 4))
        _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["cape_dark"], (cx - 12, cy + 10, 24, 3))
        _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["gold_dark"], (cx - 3, cy + 10, 6, 4))
        _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["gold_mid"], (cx - 2, cy + 10, 4, 3))


    def _draw_pauldrons(surface, cx, cy, phase):
        """Shoulder pauldrons with spikes."""
        for side in (-1, 1):
            sx = cx + side * 14
            # Shadow
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["shadow_deep"], (sx + 2, cy + 2), 8)
            # Pauldron
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["armor_darkest"], (sx, cy), 7)
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["armor_dark"], (sx - side, cy - 1), 5)
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["armor_mid"], (sx - side, cy - 2), 3)

            # Gold trim
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["gold_dark"], (sx, cy), 7, 2)
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["gold_mid"], (sx, cy), 6, 1)

            # Small spike on top
            _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["armor_darkest"], [
                (sx - 2, cy - 6),
                (sx + 2, cy - 6),
                (sx + side * 2, cy - 12),
            ])
            _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["armor_dark"], [
                (sx - 1, cy - 6),
                (sx + 1, cy - 6),
                (sx + side * 1, cy - 11),
            ])
            # Gold tip
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["gold_mid"],
                      (sx + side * 2, cy - 12), 1)


    def _draw_idle_arms(surface, cx, cy, facing, phase):
        """Idle - one arm with sword down, one holding reins."""
        sway = math.sin(phase * 0.7) * 1

        # Sword arm (facing side)
        ss_x = cx + facing * 13
        ss_y = cy + 2
        se_x = ss_x + facing * 6
        se_y = cy + 10 + int(sway)
        sh_x = se_x + facing * 4
        sh_y = se_y + 12
        _NS_abaddon._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_abaddon._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)

        # Sword pointing down
        _NS_abaddon._draw_energy_sword(surface, sh_x, sh_y, facing, phase, angle=math.pi/2 - 0.2)

        # Reins arm (opposite side, holding reins forward)
        ra_x = cx + (-facing) * 13
        ra_y = cy + 2
        re_x = ra_x + (-facing) * 5
        re_y = cy + 8
        rh_x = re_x + (-facing) * 3
        rh_y = re_y + 4
        _NS_abaddon._draw_arm_segment(surface, ra_x, ra_y, re_x, re_y)
        _NS_abaddon._draw_arm_segment(surface, re_x, re_y, rh_x, rh_y)
        _NS_abaddon._draw_gloved_hand(surface, rh_x, rh_y)


    def _draw_melee_arms(surface, cx, cy, facing, phase, progress):
        """Melee sword swing."""
        # Reins arm stable
        ra_x = cx + (-facing) * 13
        ra_y = cy + 2
        re_x = ra_x + (-facing) * 5
        re_y = cy + 8
        rh_x = re_x + (-facing) * 3
        rh_y = re_y + 4
        _NS_abaddon._draw_arm_segment(surface, ra_x, ra_y, re_x, re_y)
        _NS_abaddon._draw_arm_segment(surface, re_x, re_y, rh_x, rh_y)
        _NS_abaddon._draw_gloved_hand(surface, rh_x, rh_y)

        # Sword arm - swing motion
        ss_x = cx + facing * 13
        ss_y = cy + 2

        if progress < 0.3:
            t = progress / 0.3
            arm_angle = -0.8 + (-1.0) * t
        elif progress < 0.6:
            t = (progress - 0.3) / 0.3
            arm_angle = -1.8 + 2.8 * t
        else:
            t = (progress - 0.6) / 0.4
            arm_angle = 1.0 - 1.5 * t

        se_x = ss_x + int(math.cos(arm_angle) * 12) * facing
        se_y = ss_y + int(math.sin(arm_angle) * 12)
        sh_x = se_x + int(math.cos(arm_angle) * 10) * facing
        sh_y = se_y + int(math.sin(arm_angle) * 10)

        _NS_abaddon._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_abaddon._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)

        # Sword with rotation
        sword_angle = arm_angle + (0.3 if facing > 0 else -0.3)
        _NS_abaddon._draw_energy_sword(surface, sh_x, sh_y, facing, phase, angle=sword_angle,
                          intense=(0.3 < progress < 0.7))


    def _draw_casting_arms(surface, cx, cy, facing, phase, progress):
        """Casting - sword extended forward."""
        # Reins arm
        ra_x = cx + (-facing) * 13
        ra_y = cy + 2
        re_x = ra_x + (-facing) * 5
        re_y = cy + 8
        rh_x = re_x + (-facing) * 3
        rh_y = re_y + 4
        _NS_abaddon._draw_arm_segment(surface, ra_x, ra_y, re_x, re_y)
        _NS_abaddon._draw_arm_segment(surface, re_x, re_y, rh_x, rh_y)
        _NS_abaddon._draw_gloved_hand(surface, rh_x, rh_y)

        # Sword arm - point forward
        ss_x = cx + facing * 13
        ss_y = cy + 2

        if progress < 0.3:
            t = progress / 0.3
            arm_angle = -0.5 - 0.5 * t
        elif progress < 0.5:
            t = (progress - 0.3) / 0.2
            arm_angle = -1.0 + 1.3 * t
        else:
            t = (progress - 0.5) / 0.5
            arm_angle = 0.3 - 0.5 * t

        se_x = ss_x + int(math.cos(arm_angle) * 12) * facing
        se_y = ss_y + int(math.sin(arm_angle) * 12)
        sh_x = se_x + int(math.cos(arm_angle) * 10) * facing
        sh_y = se_y + int(math.sin(arm_angle) * 10)

        _NS_abaddon._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_abaddon._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)

        _NS_abaddon._draw_energy_sword(surface, sh_x, sh_y, facing, phase, angle=arm_angle,
                          intense=(0.2 < progress < 0.5))


    def _draw_arm_segment(surface, x1, y1, x2, y2):
        """Armored arm segment."""
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["shadow_deep"],
                (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), 6)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["armor_darkest"], (x1, y1), (x2, y2), 5)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["armor_dark"], (x1, y1), (x2, y2), 4)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["armor_mid"], (x1, y1), (x2, y2), 2)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["armor_light"], (x1 - 1, y1), (x2 - 1, y2), 1)
        # Gold joint
        mx, my = (x1 + x2) // 2, (y1 + y2) // 2
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["gold_dark"], (mx, my), 3)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["gold_mid"], (mx, my), 2)


    def _draw_gloved_hand(surface, x, y):
        """Armored gauntlet hand."""
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["shadow_deep"], (x + 1, y + 1), 4)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["armor_darkest"], (x, y), 3)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["armor_dark"], (x, y - 1), 2)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["armor_mid"], (x - 1, y - 1), 1)


    def _draw_energy_sword(surface, hx, hy, facing, phase, angle=0, intense=False):
        """Abaddon's cyan energy sword."""
        length = 32
        tip_x = hx + int(math.cos(angle) * length) * facing
        tip_y = hy + int(math.sin(angle) * length)

        perp_angle = angle + math.pi / 2
        px = math.cos(perp_angle) * facing
        py = math.sin(perp_angle)

        # Blade base - crystalline shape
        blade_pts = [
            (hx + int(px * 3), hy + int(py * 3)),
            (hx - int(px * 2), hy - int(py * 2)),
            (tip_x - int(math.cos(angle) * 4) * facing - int(px * 1),
             tip_y - int(math.sin(angle) * 4) - int(py * 1)),
            (tip_x, tip_y),
            (tip_x - int(math.cos(angle) * 4) * facing + int(px * 3),
             tip_y - int(math.sin(angle) * 4) + int(py * 3)),
        ]
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in blade_pts])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["blade_darkest"], blade_pts)

        # Layers
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["blade_dark"], [
            (hx + int(px * 2), hy + int(py * 2)),
            (hx - int(px * 1), hy - int(py * 1)),
            (tip_x, tip_y),
            (hx + int(px * 2) + int(math.cos(angle) * length * 0.5) * facing,
             hy + int(py * 2) + int(math.sin(angle) * length * 0.5)),
        ])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["blade_mid"], [
            (hx + int(px * 1), hy + int(py * 1)),
            (hx, hy),
            (tip_x, tip_y),
        ])

        # Energy glow along blade
        for i in range(6):
            t = i / 6
            bx = int(hx + (tip_x - hx) * t)
            by = int(hy + (tip_y - hy) * t)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_mid"], 200), (bx, by), 3)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], 220), (bx, by), 2)
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_hot"], (bx, by), 1)

        # Bright edge
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["blade_shine"], (hx, hy), (tip_x, tip_y), 2)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["flame_white"], (hx, hy), (tip_x, tip_y), 1)

        # Extra intense glow when swinging
        if intense:
            # Aura around blade
            for i in range(4):
                t = i / 4
                bx = int(hx + (tip_x - hx) * t)
                by = int(hy + (tip_y - hy) * t)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_mid"], 100), (bx, by), 6)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], 150), (bx, by), 4)

        # Guard (crossguard - gold)
        guard_perp_x = int(px * 6)
        guard_perp_y = int(py * 6)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_darkest"],
                (hx + guard_perp_x, hy + guard_perp_y),
                (hx - guard_perp_x, hy - guard_perp_y), 4)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_dark"],
                (hx + guard_perp_x, hy + guard_perp_y),
                (hx - guard_perp_x, hy - guard_perp_y), 3)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_mid"],
                (hx + guard_perp_x, hy + guard_perp_y),
                (hx - guard_perp_x, hy - guard_perp_y), 1)

        # Pommel with cyan gem
        pommel_x = hx - int(math.cos(angle) * 5) * facing
        pommel_y = hy - int(math.sin(angle) * 5)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["gold_darkest"], (pommel_x, pommel_y), 3)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["gold_dark"], (pommel_x, pommel_y), 2)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_bright"], (pommel_x, pommel_y), 1)


    def _draw_hooded_head(surface, cx, cy, facing, phase):
        """Hood with glowing eyes inside."""
        # Neck
        _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["armor_darkest"], (cx - 3, cy + 8, 6, 5))
        _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["armor_dark"], (cx - 2, cy + 8, 4, 4))

        # Hood shape (large purple hood covering head)
        hood_pts = [
            (cx - 12, cy - 2),
            (cx - 11, cy - 10),
            (cx - 6, cy - 14),
            (cx, cy - 16),
            (cx + 6, cy - 14),
            (cx + 11, cy - 10),
            (cx + 12, cy - 2),
            (cx + 13, cy + 8),
            (cx + 7, cy + 12),
            (cx - 7, cy + 12),
            (cx - 13, cy + 8),
        ]
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["shadow_deep"], [(p[0] + 2, p[1] + 2) for p in hood_pts])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["cape_darkest"], hood_pts)

        hood_mid = [
            (cx - 10, cy - 1),
            (cx - 9, cy - 9),
            (cx - 5, cy - 13),
            (cx, cy - 15),
            (cx + 5, cy - 13),
            (cx + 9, cy - 9),
            (cx + 10, cy - 1),
            (cx + 11, cy + 6),
            (cx + 6, cy + 10),
            (cx - 6, cy + 10),
            (cx - 11, cy + 6),
        ]
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["cape_dark"], hood_mid)

        # Hood highlight edge
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["cape_mid"],
                (cx - 9, cy - 9), (cx, cy - 15), 1)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["cape_mid"],
                (cx + 9, cy - 9), (cx, cy - 15), 1)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["cape_light"],
                (cx - 5, cy - 13), (cx, cy - 15), 1)

        # Dark interior of hood
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["shadow_deep"], [
            (cx - 8, cy - 6),
            (cx - 7, cy - 10),
            (cx, cy - 12),
            (cx + 7, cy - 10),
            (cx + 8, cy - 6),
            (cx + 7, cy + 5),
            (cx, cy + 8),
            (cx - 7, cy + 5),
        ])

        # ===== HELM inside hood =====
        # Simple helm shape (visible under hood)
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["armor_darkest"], [
            (cx - 6, cy - 3),
            (cx - 5, cy - 8),
            (cx, cy - 10),
            (cx + 5, cy - 8),
            (cx + 6, cy - 3),
            (cx + 5, cy + 4),
            (cx, cy + 6),
            (cx - 5, cy + 4),
        ])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["armor_dark"], [
            (cx - 5, cy - 2),
            (cx - 4, cy - 7),
            (cx, cy - 9),
            (cx + 4, cy - 7),
            (cx + 5, cy - 2),
            (cx + 4, cy + 3),
            (cx, cy + 5),
            (cx - 4, cy + 3),
        ])

        # Gold helm brow
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_dark"],
                (cx - 5, cy - 5), (cx + 5, cy - 5), 2)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_mid"],
                (cx - 5, cy - 5), (cx + 5, cy - 5), 1)

        # ===== GLOWING EYES =====
        eye_pulse = math.sin(phase * 2) * 0.2 + 0.8
        eye_size = max(1, int(2 * eye_pulse))
        # Eye sockets (dark slits)
        _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["shadow_deep"], (cx - 5, cy - 2, 4, 2))
        _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["shadow_deep"], (cx + 1, cy - 2, 4, 2))
        # Bright cyan eye glow
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_dark"], (cx - 3, cy - 1), eye_size + 1)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_mid"], (cx - 3, cy - 1), eye_size)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_bright"], (cx - 3, cy - 1),
                  max(1, eye_size - 1))
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_hot"], (cx - 3, cy - 1), 1)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_dark"], (cx + 3, cy - 1), eye_size + 1)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_mid"], (cx + 3, cy - 1), eye_size)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_bright"], (cx + 3, cy - 1),
                  max(1, eye_size - 1))
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_hot"], (cx + 3, cy - 1), 1)

        # Eye emission glow
        _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["eye_bright"], int(80 * eye_pulse)),
                  (cx - 3, cy - 1), 5)
        _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["eye_bright"], int(80 * eye_pulse)),
                  (cx + 3, cy - 1), 5)

        # ===== HELM HORNS =====
        for side in (-1, 1):
            # Curved horn
            _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["armor_darkest"], [
                (cx + side * 5, cy - 8),
                (cx + side * 8, cy - 12),
                (cx + side * 12, cy - 20),
                (cx + side * 14, cy - 22),
                (cx + side * 11, cy - 19),
                (cx + side * 7, cy - 11),
            ])
            _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["armor_dark"], [
                (cx + side * 6, cy - 9),
                (cx + side * 8, cy - 12),
                (cx + side * 11, cy - 18),
                (cx + side * 13, cy - 21),
                (cx + side * 10, cy - 18),
                (cx + side * 7, cy - 11),
            ])
            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["armor_mid"],
                    (cx + side * 8, cy - 12),
                    (cx + side * 13, cy - 21), 1)
            # Small cyan glow on horn tip
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_mid"], 180),
                      (cx + side * 14, cy - 22), 2)
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_bright"],
                      (cx + side * 14, cy - 22), 1)

        # Cyan flame streamers coming up from head
        for i in (-4, 0, 4):
            _NS_abaddon._draw_flame_streamer(surface, cx + i, cy - 10, 6, phase + i * 0.3, 180)


    def _draw_body_flames(surface, cx, cy, phase):
        """Cyan flames rising from body."""
        for i in range(6):
            angle = phase * 0.4 + i * math.pi / 3
            radius = 22 + int(math.sin(phase * 0.7 + i) * 4)
            px = cx + int(math.cos(angle) * radius)
            py = cy - 5 + int(math.sin(angle) * radius * 0.5)
            alpha = int(140 + math.sin(phase + i * 0.7) * 60)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_dark"], alpha), (px, py), 2)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], alpha // 2), (px, py), 1)


    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_horse_flame_base(surface, cx, cy, phase, trail=False,
                              facing=1, intense=False):
        """Cyan flame base beneath the ghostly horse."""
        strength = 1.5 if intense else 1.0

        # Base flame mist
        mist = pygame.Surface((150, 45), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        for radius in range(42, 3, -4):
            alpha = int((42 - radius) * 2.0 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_abaddon.PALETTE["flame_darkest"], min(255, alpha)),
                    (75 - radius * 2, 22 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 75, cy - 12))

        # Rising cyan flames
        for i, offset in enumerate((-30, -18, -6, 6, 18, 30)):
            t = (phase * 0.5 + i * 0.17) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 25)
            alpha = max(0, min(255, int(220 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_abaddon._draw_cyan_flame(surface, sx, sy, max(1, 4 - int(t * 3)),
                            phase + i, alpha)

        # Orbiting flame orbs
        for i in range(5):
            angle = phase * 0.9 + i * math.pi * 2 / 5
            r = 28 + int(math.sin(phase + i * 1.3) * 4)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 7)
            _NS_abaddon._draw_cyan_flame(surface, sx, sy, 3, phase + i, 220)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 140 - i * 25)
                _NS_abaddon._draw_cyan_flame(surface, sx, sy, max(2, 4 - i), phase + i, alpha)


    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((130, 24), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, (12 - radius) * 15)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (12 - radius, 12 - radius, 106 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (*_NS_abaddon.PALETTE["flame_darkest"], 60),
                           (10, 5, 108, 12))
        surface.blit(shadow, (x - 65, y - 12))


    def _draw_dark_aura(surface, x, y, phase):
        """Dark purple/cyan background aura."""
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        for radius in range(88, 5, -4):
            alpha = int((88 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_abaddon._aacircle(aura, (*_NS_abaddon.PALETTE["cape_darkest"], min(255, alpha)),
                          (110, 100), radius)
        surface.blit(aura, (x - 110, y - 100))

        # Cyan glow overlay
        aura2 = pygame.Surface((160, 140), pygame.SRCALPHA)
        for radius in range(64, 5, -3):
            alpha = int((64 - radius) * 0.7 * pulse)
            if alpha > 0:
                _NS_abaddon._aacircle(aura2, (*_NS_abaddon.PALETTE["flame_darkest"], min(255, alpha)),
                          (80, 70), radius)
        surface.blit(aura2, (x - 80, y - 70))


    def _draw_ground_runes(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((160, 52), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_abaddon.PALETTE["cape_dark"], 140),
                            (5, 12, 150, 30), 3)
        pygame.draw.ellipse(ring, (*_NS_abaddon.PALETTE["flame_dark"], 170),
                            (25, 16, 110, 22), 2)

        for i in range(10):
            angle = phase * 0.2 + i * math.pi / 5
            x1 = 80 + int(math.cos(angle) * 38)
            y1 = 27 + int(math.sin(angle) * 8)
            x2 = 80 + int(math.cos(angle) * 68)
            y2 = 27 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_abaddon.PALETTE["flame_bright"], 160),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_abaddon.PALETTE["flame_hot"], int(80 * pulse)),
                                (15, 10, 130, 34), 1)

        surface.blit(ring, (x - 80, y - 26))


    def _draw_sword_swing_trail(surface, x, y, facing, progress):
        """Cyan trail during basic sword swing."""
        if progress < 0.3 or progress > 0.7:
            return
        t = (progress - 0.3) / 0.4
        center_x = x + facing * 5
        center_y = y
        radius = 45

        start_angle = -math.pi / 2 - 0.5
        end_angle = math.pi / 4
        current_angle = start_angle + (end_angle - start_angle) * t

        trail_length = 1.5
        segments = 14
        for i in range(segments):
            seg_t = i / segments
            angle = current_angle - trail_length * seg_t
            if angle < start_angle:
                continue

            ax = center_x + int(math.cos(angle) * radius) * facing
            ay = center_y + int(math.sin(angle) * radius)

            alpha_seg = int(220 * (1 - seg_t))
            size = int(4 * (1 - seg_t * 0.4))
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_dark"], alpha_seg),
                      (ax, ay), size + 2)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_mid"], alpha_seg),
                      (ax, ay), size + 1)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], alpha_seg),
                      (ax, ay), size)
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_hot"],
                      (ax, ay), max(1, size - 1))


    def _draw_sword_purple_trail(surface, x, y, facing, progress, phase):
        """Purple trail during Death Sever."""
        if progress < 0.15 or progress > 0.75:
            return

        t = (progress - 0.15) / 0.6
        center_x = x + facing * 5
        center_y = y
        radius = 50

        start_angle = -math.pi / 2 - 0.5
        end_angle = math.pi / 4
        current_angle = start_angle + (end_angle - start_angle) * t

        trail_length = 2.0
        segments = 16
        for i in range(segments):
            seg_t = i / segments
            angle = current_angle - trail_length * seg_t
            if angle < start_angle:
                continue

            ax = center_x + int(math.cos(angle) * radius) * facing
            ay = center_y + int(math.sin(angle) * radius)

            alpha_seg = int(240 * (1 - seg_t))
            size = int(5 * (1 - seg_t * 0.3))
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_darkest"], alpha_seg),
                      (ax, ay), size + 3)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_dark"], alpha_seg),
                      (ax, ay), size + 2)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_mid"], alpha_seg),
                      (ax, ay), size + 1)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_bright"], alpha_seg),
                      (ax, ay), size)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_hot"], alpha_seg),
                      (ax, ay), max(1, size - 1))


    # ===================================================================
    # SKILL W: APHOTIC SHIELD
    # ===================================================================
    def _draw_aphotic_shield(surface, boss, x, y, timer, phase):
        """Bubble shield around Abaddon."""
        progress = max(0.0, min(1.0, 1 - timer / 100))
        pulse = math.sin(phase * 2) * 0.2 + 0.8

        # Shield radius
        radius = int(45 + progress * 5)

        # Multi-layer shield sphere
        shield_layers = [
            (radius + 3, _NS_abaddon.PALETTE["flame_dark"], 100),
            (radius, _NS_abaddon.PALETTE["flame_mid"], 180),
            (radius - 3, _NS_abaddon.PALETTE["flame_light"], 150),
            (radius - 6, _NS_abaddon.PALETTE["flame_bright"], 100),
        ]

        for r, color, alpha in shield_layers:
            a = int(alpha * pulse)
            _NS_abaddon._aacircle(surface, (*color, a), (x, y - 8), r, 3)

        # Bright edge highlights
        _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], int(220 * pulse)),
                  (x, y - 8), radius, 2)
        _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_hot"], int(200 * pulse)),
                  (x, y - 8), radius, 1)

        # Rotating energy bands
        for band_i in range(3):
            band_phase = phase * 1.5 + band_i * math.pi / 3
            # Draw as arc segments (approximated with lines)
            for j in range(-6, 7):
                angle = band_phase + j * 0.15
                bx = x + int(math.cos(angle) * radius * math.cos(band_i * 0.4))
                by = y - 8 + int(math.sin(angle) * radius * math.cos(band_i * 0.4))
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_hot"], 200), (bx, by), 2)
                _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_white"], (bx, by), 1)

        # Small orbs orbiting the shield
        for i in range(6):
            angle = phase * 1.2 + i * math.pi / 3
            ox = x + int(math.cos(angle) * radius)
            oy = y - 8 + int(math.sin(angle) * radius * 0.6)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], 220), (ox, oy), 3)
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_hot"], (ox, oy), 2)
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_white"], (ox, oy), 1)

        # Bright sparks
        for i in range(8):
            angle = phase * 0.8 + i * math.pi / 4
            sx = x + int(math.cos(angle) * (radius + 5))
            sy = y - 8 + int(math.sin(angle) * (radius + 5))
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_shine"] if "flame_shine" in _NS_abaddon.PALETTE
                      else _NS_abaddon.PALETTE["flame_hot"], (sx, sy), 1)


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_abaddon.draw_abaddon(surface, boss, x, y)


# ====================================================================
# ENTRY POINT PUBLIK (dipanggil base_boss.Boss.draw)
# ====================================================================

def draw_gornak(surface, boss, x, y):
    """Entry point gornak."""
    return _NS_gornak.draw_gornak(surface, boss, x, y)

def draw_morgath(surface, boss, x, y):
    """Entry point morgath."""
    return _NS_morgath.draw_morgath(surface, boss, x, y)

def draw_drakar(surface, boss, x, y):
    """Entry point drakar."""
    return _NS_drakar.draw_drakar(surface, boss, x, y)

def draw_abaddon(surface, boss, x, y):
    """Entry point abaddon."""
    return _NS_abaddon.draw_abaddon(surface, boss, x, y)
