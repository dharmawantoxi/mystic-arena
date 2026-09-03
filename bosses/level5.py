"""
bosses/level5.py - Semua boss Level 5

Gabungan dari 4 file terpisah:
  - nyxara               (mini boss)
  - gravefang            (mini boss)
  - vhalzun              (mini boss)
  - krobellus            (TRUE BOSS)

Tiap boss dibungkus dalam kelas namespace `_NS_<nama>`
supaya PALETTE dan fungsi helper-nya TIDAK saling
menimpa - 91 simbol bentrok antar file boss, termasuk
PALETTE, _aacircle, _draw_shadow, _target_position.

Kode di dalam tiap namespace TIDAK diubah isinya;
hanya referensi antar-simbol yang diberi prefix.

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
# NYXARA — THE NETHER MATRON  (FULL REWRITE)
# ====================================================================
# Arsitektur "masterwork" (patron: vhalzun/krobellus di file yang sama):
#
#   * RENDERER (file ini) — rig pixel-art + controller animasi + pose +
#     geometri tongkat + telegraph tanah + fallback FX canvas.  Semua
#     bentuk digambar prosedural (pygame.draw) dengan palet terbatas,
#     tepi keras (chunky pixel), dan surface statis di-cache.
#   * LAPISAN HIDUP (heroes/nyxara_fx.py) — trail ayunan tongkat,
#     partikel, proyektil (nether orb & nether blast), FX skill Q/W/E/R,
#     impact flash, shockwave, screen shake, hit-stop 0.03-0.08 s.
#     Digambar 1:1 ke layar, DI LUAR cache sprite supaya tetap 60 fps.
#   * GAME FEEL BUS (heroes/combat_feel.py) — satu sumber hit-stop &
#     shake untuk seluruh arena.
#
# Kontrak publik (dipakai heroes/__init__, bosses/base_boss, hero_skills,
# tools, dan modul FX):
#   draw_nyxara(surface, boss, x, y)   entry point (Boss.draw & render_hero)
#   PALETTE                            palet karakter + FX (sumber benar)
#   pose_of / anim_state / attack_phase  state animasi (sinkron dgn FX)
#   staff_points(boss, x, y)           (pivot, tip) Vector2 ruang layar
#   body_scale / ground_dy             skala & garis tanah
#   DEBUG_CHARACTER                    overlay hitbox/hurtbox/state
#
# 100% PROSEDURAL: tanpa PNG/JPG/GIF/sprite-sheet/aset eksternal.
# ====================================================================
class _NS_nyxara:
    """Namespace nyxara — renderer The Nether Matron (rewrite v2).

    Gaya: 2D pixel art dark-fantasy — chunky pixels, silhouette kuat
    (mahkota bertanduk + jubah lebar + tongkat tengkorak), palet
    terbatas, tepi keras, highlight/shadow per-pixel.  100% prosedural.
    """

    # ------------------------------------------------------------------
    # KONFIGURASI KARAKTER & KONTRAK TIMING
    # ------------------------------------------------------------------
    CHARACTER_NAME = "nyxara"

    #: Overlay debug (hitbox, hurtbox, range, state, FPS, partikel).
    DEBUG_CHARACTER = False

    #: Jarak dunia (px) — di bawahnya Nyxara MENGAYUN tongkatnya,
    #: di atasnya ia melempar nether orb.  Hook benturan di
    #: bosses/base_boss.py dan modul FX memakai angka yang sama.
    MELEE_REACH = 88.0

    #: Garis tanah dari titik jangkar (px lokal).
    GROUND_DY = 48

    #: Fase serangan (fraksi 0..1 dari durasi serangan) — satu
    #: kosakata untuk renderer, lapisan hidup, dan overlay debug.
    ATTACK_PHASES = (
        ("ANTICIPATION", 0.00, 0.12),
        ("WINDUP",       0.12, 0.30),
        ("SWING",        0.30, 0.50),
        ("IMPACT",       0.50, 0.62),
        ("FOLLOW",       0.62, 0.82),
        ("RECOVERY",     0.82, 1.00),
    )

    #: Jendela hit aktif + frame benturan (swing) & rilis (orb).
    ATTACK_ACTIVE_WINDOW = (0.30, 0.55)
    ATTACK_IMPACT_FRAME = 0.42
    ATTACK_RELEASE_FRAME = 0.32

    #: Durasi pose skill dalam FRAME — HARUS sama dengan timer yang
    #: di-set _smart_ai_nyxara (q 60, w 70, e 80, r 90).
    SKILL_DUR = {"q": 60, "w": 70, "e": 80, "r": 90}

    #: Radius efek di RUANG DUNIA — sama dengan radius damage AI
    #: (q target tunggal + splash 130, w single 280 -> kurva 150,
    #: e ward 100, r drain single 240 -> tether).
    SKILL_RADIUS = {"q": 130.0, "w": 150.0, "e": 100.0, "r": 150.0}

    #: Prioritas state animasi — angka besar menang, DEATH mengunci.
    ANIM_STATES = {
        "IDLE": 0,
        "WALK": 10,
        "RUN": 15,
        "CHARGE": 30,
        "CAST": 35,
        "ATTACK": 40,
        "SWING": 45,
        "SKILL": 50,
        "SPECIAL": 55,
        "HIT": 60,
        "HURT": 65,
        "DEATH": 100,
    }

    #: Lifecycle skill: CAST -> CHARGE -> RELEASE -> AREA -> IMPACT
    #: -> AFTER (-> FADE saat SkillFX dibuang).
    SKILL_PHASES = (
        ("CAST",    0.00, 0.16),
        ("CHARGE",  0.16, 0.34),
        ("RELEASE", 0.34, 0.46),
        ("AREA",    0.46, 0.74),
        ("IMPACT",  0.74, 0.86),
        ("AFTER",   0.86, 1.00),
    )

    # ------------------------------------------------------------------
    # PALETTE — Nether Matron: nether kuning-hijau + jubah ungu gelap +
    # tulang olive + trim emas + tanduk merah.  Kunci identik dengan
    # heroes/nyxara_fx.NYXARA_PALETTE (modul FX menyalin dari sini).
    # ------------------------------------------------------------------
    PALETTE = {
        # outline gelap (pixel-art hard edge)
        "outline":        (6,   5,   10),

        # Kulit malformed olive
        "skin_darkest":   (25,  38,  15),
        "skin_dark":      (55,  75,  30),
        "skin_mid":       (95,  120, 50),
        "skin_light":     (140, 165, 75),
        "skin_shine":     (185, 210, 110),

        # Jubah - ungu gelap berlapis
        "robe_darkest":   (18,  10,  22),
        "robe_dark":      (38,  22,  44),
        "robe_mid":       (68,  38,  70),
        "robe_light":     (105, 65,  105),
        "robe_high":      (145, 100, 140),
        "robe_shine":     (190, 155, 185),

        # Jubah dalam
        "inner_darkest":  (10,  6,   14),
        "inner_dark":     (22,  13,  28),
        "inner_mid":      (40,  24,  48),

        # Kulit/leather
        "leather_dark":   (28,  18,  12),
        "leather_mid":    (55,  35,  20),
        "leather_light":  (90,  62,  35),

        # Nether kuning-hijau — warna sihir utama
        "nether_darkest": (25,  35,  5),
        "nether_dark":    (70,  95,  15),
        "nether_mid":     (140, 180, 30),
        "nether_light":   (200, 240, 60),
        "nether_bright":  (230, 255, 120),
        "nether_hot":     (245, 255, 180),
        "nether_white":   (255, 255, 220),

        # Tulang olive
        "bone_dark":      (75,  85,  50),
        "bone_mid":       (130, 145, 90),
        "bone_light":     (185, 200, 140),
        "bone_shine":     (225, 235, 190),

        # Trim emas
        "gold_dark":      (90,  62,  15),
        "gold_mid":       (165, 125, 35),
        "gold_light":     (225, 185, 70),
        "gold_shine":     (250, 225, 140),

        # Tanduk / aksen merah
        "horn_dark":      (60,  20,  15),
        "horn_mid":       (110, 40,  25),
        "horn_light":     (170, 75,  40),
        "horn_high":      (220, 130, 70),

        # Kayu tongkat
        "wood_dark":      (35,  22,  15),
        "wood_mid":       (65,  42,  22),
        "wood_light":     (100, 70,  40),

        # Glow mata
        "eye_dark":       (70,  95,  5),
        "eye_mid":        (170, 220, 30),
        "eye_bright":     (220, 250, 100),
        "eye_hot":        (245, 255, 200),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (4,   6,   3),
        "white":          (255, 255, 255),
    }

    # ------------------------------------------------------------------
    # GEOMETRI TONGKAT (ruang lokal facing-kanan; cermin via x*facing)
    # ------------------------------------------------------------------
    STAFF_SHAFT = 42.0         # panjang gagang dari genggaman ke kepala
    STAFF_BUTT = 14.0          # panjang gagang di bawah genggaman
    STAFF_SKULL_R = 6.0        # radius tengkorak di puncak tongkat
    _STAFF_REST = -1.35        # sudut istirahat (tongkat hampir tegak)

    # ===================================================================
    # HELPERS MATEMATIKA & PIXEL
    # ===================================================================
    @staticmethod
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    @staticmethod
    def _lerp(a, b, t):
        return a + (b - a) * t

    @staticmethod
    def _lerp_pt(a, b, t):
        return (_NS_nyxara._lerp(a[0], b[0], t),
                _NS_nyxara._lerp(a[1], b[1], t))

    @staticmethod
    def _ease_out_cubic(t):
        t = max(0.0, min(1.0, t))
        return 1.0 - (1.0 - t) ** 3

    @staticmethod
    def _ease_in_cubic(t):
        t = max(0.0, min(1.0, t))
        return t * t * t

    @staticmethod
    def _ease_in_out(t):
        t = max(0.0, min(1.0, t))
        return t * t * (3.0 - 2.0 * t)

    @staticmethod
    def _snap(v):
        """Snap koordinat ke pixel penuh (pixel-art: tanpa sub-pixel)."""
        return int(round(v))

    @staticmethod
    def _qphase(phase, buckets=12):
        """Kuantisasi fase animasi supaya surface cache tetap kecil."""
        return int(phase * buckets) % buckets

    @staticmethod
    def attack_phase(progress):
        """Nama fase serangan untuk progress 0..1."""
        p = max(0.0, min(1.0, float(progress)))
        for name, a, b in _NS_nyxara.ATTACK_PHASES:
            if a <= p < b:
                return name
        return "RECOVERY"

    @staticmethod
    def attack_phases_order():
        return tuple(n for n, _a, _b in _NS_nyxara.ATTACK_PHASES)

    @staticmethod
    def skill_phase(t):
        """Nama fase skill untuk t 0..1."""
        p = max(0.0, min(1.0, float(t)))
        for name, a, b in _NS_nyxara.SKILL_PHASES:
            if a <= p < b:
                return name
        return "AFTER"

    # ===================================================================
    # CACHE SURFACE STATIS (dibangun sekali, dipakai semua unit)
    # ===================================================================
    _CACHE = {}
    _CACHE_MAX = 96

    @staticmethod
    def clear_cache():
        _NS_nyxara._CACHE.clear()

    @staticmethod
    def cache_size():
        return len(_NS_nyxara._CACHE)

    @staticmethod
    def _cached(key, builder):
        s = _NS_nyxara._CACHE.get(key)
        if s is None:
            if len(_NS_nyxara._CACHE) >= _NS_nyxara._CACHE_MAX:
                _NS_nyxara._CACHE.pop(next(iter(_NS_nyxara._CACHE)))
            s = builder()
            _NS_nyxara._CACHE[key] = s
        return s

    @staticmethod
    def _shadow_surf():
        """Bayangan kontak (ellipse chunky berlapis, dibangun sekali)."""
        w, h = 92, 22
        c = _NS_nyxara.PALETTE
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (0, 0, 0, 115), (4, 4, w - 8, h - 8))
        pygame.draw.ellipse(s, (0, 0, 0, 85), (12, 6, w - 24, h - 12))
        pygame.draw.ellipse(s, (*c["nether_darkest"], 70),
                            (18, 8, w - 36, h - 16))
        return s

    @staticmethod
    def _mist_surf(bucket):
        """Kabut nether di bawah jubah Nyxara (6 bucket fase)."""
        c = _NS_nyxara.PALETTE
        w, h = 112, 30
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        off = (bucket % 6) / 6.0
        for i, (dx, rw) in enumerate(((-24, 32), (-4, 44), (20, 30))):
            t = (off + i * 0.33) % 1.0
            cy = 20 - int(t * 8)
            a = int(72 * (1.0 - t))
            if a <= 0:
                continue
            pygame.draw.ellipse(
                s, (*c["nether_darkest"], min(255, a)),
                (w // 2 + dx - rw // 2, cy - 4,
                 rw, max(3, 8 - int(t * 4))))
            pygame.draw.ellipse(
                s, (*c["nether_dark"], a // 2),
                (w // 2 + dx - rw // 2 + 3, cy - 3,
                 rw - 6, max(2, 5 - int(t * 3))))
        return s

    @staticmethod
    def _rune_surf(bucket, skill):
        """Rune circle di tanah (8 bucket rotasi; versi skill lebih terang)."""
        c = _NS_nyxara.PALETTE
        w, h = 128, 48
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, h // 2
        base_a = 190 if skill else 145
        pygame.draw.ellipse(s, (*c["nether_dark"], base_a),
                            (6, 12, w - 12, 24), 3)
        pygame.draw.ellipse(s, (*c["nether_mid"], base_a - 20),
                            (20, 17, w - 40, 14), 2)
        # rune tick yang berputar (garis pendek chunky)
        rot = bucket * (math.pi / 4.0)
        for i in range(10):
            ang = rot + i * (math.pi / 5.0)
            x1 = cx + int(math.cos(ang) * 34)
            y1 = cy + int(math.sin(ang) * 8)
            x2 = cx + int(math.cos(ang) * 54)
            y2 = cy + int(math.sin(ang) * 13)
            pygame.draw.line(s, (*c["nether_bright"], base_a - 30),
                             (x1, y1), (x2, y2), 2)
        # glyph segitiga kecil (bukan lingkaran) di 4 penjuru
        for i in range(4):
            ang = rot * 0.5 + i * (math.pi / 2.0)
            gx = cx + int(math.cos(ang) * 44)
            gy = cy + int(math.sin(ang) * 11)
            pygame.draw.polygon(s, (*c["nether_light"], base_a),
                                [(gx, gy - 4), (gx + 4, gy + 3),
                                 (gx - 4, gy + 3)])
        return s

    @staticmethod
    def _glow_surf(radius, color):
        """Glow lembut (mata/orb) — dibangun sekali per radius+warna."""
        radius = max(1, int(radius))
        size = radius * 2 + 2
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        for r in range(radius, 0, -1):
            a = int(125 * (1.0 - r / float(radius)) ** 1.6)
            if a > 0:
                pygame.draw.circle(s, (*color[:3], min(255, a)),
                                   (size // 2, size // 2), r)
        return s

    @staticmethod
    def _target_position(boss, x, y):
        """Posisi target di ruang jangkar (dengan kompensasi scale).

        Hero di-render ke canvas offscreen lalu di-scale saat blit
        (heroes/__init__.py), jadi titik canvas harus = (delta dunia)/scale
        supaya beam/proyektil mendarat TEPAT di target setelah blit.
        Boss yang digambar langsung di layar tidak terpengaruh (scale = 1).
        """
        target = getattr(boss, "target", None)
        scale = float(getattr(boss, "_render_scale", 1.0) or 1.0) or 1.0
        if target is not None and getattr(target, "alive", True):
            tx = x + (float(getattr(target, "x", x))
                      - float(getattr(boss, "x", x))) / scale
            ty = y + (float(getattr(target, "y", y))
                      - float(getattr(boss, "y", y))) / scale
            return int(tx), int(ty)
        return (int(x + 200.0 / scale * (getattr(boss, "direction", 1) or 1)),
                int(y))

    # ===================================================================
    # CONTROLLER ANIMASI
    #   Atribut state di-simpan di boss dengan prefix `_nx_` (kompatibel
    #   dengan versi lama):
    #     _nx_state/_prev/_time/_frame  state machine + prioritas
    #     _nx_attack_active/_frame/_progress/_phase/_kind/_hit_active
    #     _nx_skill/_skill_progress/_skill_total
    #     _nx_moving, _nx_hurt_frames, _nx_death_age, _nx_dt
    # ===================================================================
    @staticmethod
    def _update_nyxara_anim(boss):
        G = _NS_nyxara

        # ── delta time nyata ─────────────────────────────────────────
        try:
            now = pygame.time.get_ticks()
        except Exception:                          # pragma: no cover
            now = 0
        prev_ms = getattr(boss, "_nx_last_ms", None)
        if prev_ms is None:
            dt = 1.0 / 60.0
        else:
            dt = (now - prev_ms) / 1000.0
            if dt <= 0.0 or dt > 0.05:
                dt = 1.0 / 60.0
        boss._nx_last_ms = now
        boss._nx_dt = dt

        # ── deteksi gerak ────────────────────────────────────────────
        moving = G._detect_moving(boss)
        boss._nx_moving = moving

        # ── timeline serangan ────────────────────────────────────────
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 42)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_nx_prev_timer", 0))
        active = bool(getattr(boss, "_nx_attack_active", False))

        triggered = timer >= cooldown - 1 and previous <= 1
        if triggered:
            boss._nx_attack_active = True
            boss._nx_attack_frame = 0
            boss._nx_attack_manual = False
            tgt = getattr(boss, "target", None)
            if tgt is not None and getattr(tgt, "alive", True):
                dist = math.hypot(
                    float(getattr(tgt, "x", 0.0)) - float(getattr(boss, "x", 0.0)),
                    float(getattr(tgt, "y", 0.0)) - float(getattr(boss, "y", 0.0)))
            else:
                dist = 1e9
            boss._nx_attack_kind = "swing" if dist <= G.MELEE_REACH else "orb"
            active = True
        elif active and timer > 0:
            boss._nx_attack_frame = int(getattr(
                boss, "_nx_attack_frame", 0)) + 1
        elif timer <= 0:
            if active and not getattr(boss, "_nx_attack_manual", False) \
                    and float(getattr(boss, "_nx_attack_progress", 0.0)) > 0.0:
                # pemanggil eksternal menggerakkan progress manual (alat
                # uji) — hormati, tandai manual
                boss._nx_attack_manual = True
            elif not getattr(boss, "_nx_attack_manual", False):
                boss._nx_attack_active = False
                boss._nx_attack_frame = 0
                active = False
            if not active:
                boss._nx_attack_active = False
                boss._nx_attack_frame = 0
        boss._nx_prev_timer = timer

        frame = int(getattr(boss, "_nx_attack_frame", 0)) if active else 0
        span = max(1, cooldown - 1)
        if bool(getattr(boss, "_nx_attack_manual", False)) and active:
            progress = min(1.0, max(0.0, float(getattr(
                boss, "_nx_attack_progress", 0.0))))
            boss._nx_attack_frame = int(round(progress * span))
        else:
            progress = min(1.0, frame / float(span)) if active else 0.0
            boss._nx_attack_progress = progress

        # ── fase + jendela hit ───────────────────────────────────────
        if not getattr(boss, "_nx_attack_active", False):
            boss._nx_attack_active = False
            boss._nx_attack_manual = False
            active = False
        boss._nx_attack_phase = G.attack_phase(progress) if active else "NONE"
        lo, hi = G.ATTACK_ACTIVE_WINDOW
        boss._nx_hit_active = bool(active and lo <= progress < hi)

        # ── respons kena damage (HURT) ───────────────────────────────
        hurt = int(getattr(boss, "_nx_hurt_frames", 0))
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        if flash >= 8 and hurt <= 0:
            hurt = 10
        boss._nx_hurt_frames = max(0, hurt - 1) if hurt > 0 else 0

        # ── skill (active_skill; jalur boss generik: ability -> 'q') ──
        skill = getattr(boss, "active_skill", None)
        if skill is None and getattr(boss, "ability_active", False) \
                and int(getattr(boss, "ability_active_timer", 0) or 0) > 0:
            skill = "q"
        if skill is not None:
            timer_s = int(getattr(boss, "active_skill_timer", 0) or 0)
            if skill == "q" and getattr(boss, "active_skill", None) is None:
                timer_s = int(getattr(boss, "ability_active_timer", 0) or 0)
            total = int(getattr(boss, "_nx_skill_total", 0) or 0)
            if getattr(boss, "_nx_skill", None) != skill:
                total = max(timer_s, G.SKILL_DUR.get(skill, 60))
            boss._nx_skill_total = max(total, timer_s, 1)
            boss._nx_skill_progress = max(
                0.0, min(1.0, 1.0 - timer_s / float(boss._nx_skill_total)))
            boss._nx_skill = skill
        else:
            boss._nx_skill = None
            boss._nx_skill_progress = 0.0
            boss._nx_skill_total = 0

        # ── death age ────────────────────────────────────────────────
        if not getattr(boss, "alive", True):
            boss._nx_death_age = int(getattr(boss, "_nx_death_age", 0)) + 1
        else:
            boss._nx_death_age = 0

        # ── state machine (prioritas) ────────────────────────────────
        if not getattr(boss, "alive", True):
            state = "DEATH"
        elif boss._nx_hurt_frames > 0:
            state = "HURT"
        elif skill is not None:
            state = "SKILL" if skill in ("q", "w") else "SPECIAL"
        elif active:
            state = "SWING" if getattr(boss, "_nx_attack_kind",
                                       "orb") == "swing" else "ATTACK"
        elif moving:
            state = "RUN" if getattr(boss, "is_enraged", False) else "WALK"
        else:
            state = "IDLE"
        if state != getattr(boss, "_nx_state", None):
            boss._nx_state_prev = getattr(boss, "_nx_state", state)
            boss._nx_state = state
            boss._nx_state_time = 0
            boss._nx_state_frame = 0
        else:
            boss._nx_state_time = getattr(boss, "_nx_state_time", 0) + dt
            boss._nx_state_frame = int(getattr(boss, "_nx_state_frame", 0)) + 1
        return state

    @staticmethod
    def _detect_moving(boss):
        """Deteksi gerak dari delta posisi (cache 2 frame terakhir)."""
        if not hasattr(boss, "_nx_last_x"):
            boss._nx_last_x = boss.x
            boss._nx_last_y = boss.y
            return False
        dx = abs(boss.x - boss._nx_last_x)
        dy = abs(boss.y - boss._nx_last_y)
        boss._nx_last_x = boss.x
        boss._nx_last_y = boss.y
        return dx + dy > 0.3

    # ===================================================================
    # POSE STATE — satu sumber kebenaran untuk rig DAN semua FX
    # ===================================================================
    ACTIONS = ("idle", "walk", "attack", "swing", "cast_q", "cast_w",
               "cast_e", "cast_r", "hurt", "death")

    @staticmethod
    def _resolve_pose(boss, moving=False):
        """(action, phase, ap) setelah controller dijalankan."""
        if not getattr(boss, "alive", True):
            return ("death", float(getattr(boss, "pulse", 0.0)), 0.0)
        skill = getattr(boss, "_nx_skill", None)
        if skill is not None:
            action = {"q": "cast_q", "w": "cast_w",
                      "e": "cast_e", "r": "cast_r"}.get(skill, "cast_q")
            return (action, float(getattr(boss, "pulse", 0.0)),
                    float(getattr(boss, "_nx_skill_progress", 0.0) or 0.0))
        if getattr(boss, "_nx_attack_active", False):
            action = "swing" if getattr(boss, "_nx_attack_kind",
                                        "orb") == "swing" else "attack"
            return (action, float(getattr(boss, "pulse", 0.0)),
                    max(0.0, min(1.0, float(getattr(
                        boss, "_nx_attack_progress", 0.0)))))
        if int(getattr(boss, "_nx_hurt_frames", 0)) > 0:
            return ("hurt", float(getattr(boss, "pulse", 0.0)), 0.0)
        if moving:
            return ("walk", float(getattr(boss, "pulse", 0.0)), 0.0)
        return ("idle", float(getattr(boss, "pulse", 0.0)), 0.0)

    @staticmethod
    def pose_of(boss):
        """Publik: pose tersimpan (dipakai modul FX tanpa efek samping)."""
        return _NS_nyxara._resolve_pose(
            boss, bool(getattr(boss, "_nx_moving", False)))

    @staticmethod
    def anim_state(boss):
        """Publik: nama state animasi aktif (IDLE/WALK/.../DEATH)."""
        return str(getattr(boss, "_nx_state", "IDLE"))

    @staticmethod
    def attack_kind(boss):
        return str(getattr(boss, "_nx_attack_kind", "orb"))

    @staticmethod
    def body_scale(boss):
        sc = getattr(boss, "_render_scale", 1.0)
        try:
            sc = float(sc)
        except (TypeError, ValueError):
            sc = 1.0
        return sc if sc > 0.01 else 1.0

    @staticmethod
    def ground_dy(boss):
        return float(_NS_nyxara.GROUND_DY) * _NS_nyxara.body_scale(boss)

    # ===================================================================
    # GEOMETRI TONGKAT — pivot + sudut per pose.
    # Dipakai renderer (gambar) DAN heroes/nyxara_fx (trail + titik lahir
    # proyektil) lewat staff_points() — mustahil beda satu frame.
    # ===================================================================
    @staticmethod
    def _staff_pivot_local(action, ap, phase, boss=None):
        """Posisi genggaman (pivot tongkat) ruang lokal, per pose."""
        G = _NS_nyxara
        if action == "swing":
            # langkah kecil ke depan saat mengayun, mundur saat antisipasi
            if ap < 0.12:
                t = G._ease_out_cubic(ap / 0.12)
                return G._lerp_pt((11, -18), (8, -18), t)
            if ap < 0.30:
                t = G._ease_out_cubic((ap - 0.12) / 0.18)
                return G._lerp_pt((8, -18), (7, -21), t)
            if ap < 0.62:
                t = G._ease_in_out((ap - 0.30) / 0.32)
                return G._lerp_pt((7, -21), (16, -12), t)
            return G._lerp_pt((16, -12), (11, -18),
                              G._ease_in_out((ap - 0.62) / 0.38))
        if action == "attack":        # lempar nether orb
            if ap < 0.32:
                t = G._ease_out_cubic(ap / 0.32)
                return G._lerp_pt((10, -17), (7, -23), t)
            if ap < 0.50:
                t = G._ease_in_cubic((ap - 0.32) / 0.18)
                return G._lerp_pt((7, -23), (17, -15), t)
            return G._lerp_pt((17, -15), (10, -17),
                              G._ease_in_out((ap - 0.50) / 0.50))
        if action == "cast_q":        # Nether Blast: tongkat terangkat
            return (10, -22 - int(math.sin(min(1.0, ap * 1.4) * math.pi) * 5))
        if action == "cast_w":        # Decrepify: tongkat menunjuk
            return (7, -24)
        if action == "cast_e":        # Nether Ward: tancap ke tanah
            if ap < 0.5:
                return (13, -24)
            return (15, -14)
        if action == "cast_r":        # Life Drain: dua tangan terangkat
            return (9, -21 - int(math.sin(min(1.0, ap * 1.6) * math.pi) * 6))
        if action == "hurt":
            return (6, -16)
        if action == "death":
            return (13, -8 + min(1.0, ap + 0.4) * 10)
        if action == "walk":
            return (11, -18 + int(math.sin(phase * 2.2) * 2))
        # idle + fallback: sway pelan
        return (11, -18 + int(math.sin(phase * 0.8) * 1.5))

    @staticmethod
    def _staff_angle(action, ap, phase, boss=None):
        """Sudut gagang tongkat (radian, ruang lokal facing-kanan).

        Swing adalah busur KONTINYU: ANTICIPATION mundur -> WINDUP
        terangkat -> SWING menyapu cepat -> IMPACT decel -> FOLLOW
        THROUGH -> RECOVERY kembali.  Tidak ada lompatan sudut.
        """
        G = _NS_nyxara
        rest = G._STAFF_REST + math.sin(phase * 0.8) * 0.05
        if action == "swing":
            if ap < 0.12:                       # ANTICIPATION
                t = G._ease_out_cubic(ap / 0.12)
                return G._lerp(rest, -1.55, t)
            if ap < 0.30:                       # WINDUP
                t = G._ease_out_cubic((ap - 0.12) / 0.18)
                return G._lerp(-1.55, -2.05, t)
            if ap < 0.50:                       # SWING (cepat)
                t = G._ease_in_cubic((ap - 0.30) / 0.20)
                return G._lerp(-2.05, 0.25, t)
            if ap < 0.62:                       # IMPACT (decel)
                t = G._ease_out_cubic((ap - 0.50) / 0.12)
                return G._lerp(0.25, 0.62, t)
            if ap < 0.82:                       # FOLLOW THROUGH
                t = G._ease_in_out((ap - 0.62) / 0.20)
                return G._lerp(0.62, 0.92, t)
            # RECOVERY
            t = G._ease_in_out((ap - 0.82) / 0.18)
            return G._lerp(0.92, rest, t)
        if action == "attack":                  # jab lempar orb
            if ap < 0.32:
                t = G._ease_out_cubic(ap / 0.32)
                return G._lerp(rest, -1.85, t)
            if ap < 0.50:
                t = G._ease_in_cubic((ap - 0.32) / 0.18)
                return G._lerp(-1.85, -0.75, t)
            return G._lerp(-0.75, rest,
                           G._ease_in_out((ap - 0.50) / 0.50))
        if action == "cast_e":                  # putar tongkat lalu tancap
            if ap < 0.55:
                return rest + ap * (math.pi * 3.0) / 0.55
            return G._lerp(rest + math.pi * 3.0, -1.05,
                           G._ease_out_cubic((ap - 0.55) / 0.45))
        if action == "cast_q":
            return rest - 0.20 - math.sin(min(1.0, ap * 1.4) * math.pi) * 0.30
        if action == "cast_w":
            return -0.35 + math.sin(phase * 2.0) * 0.10
        if action == "cast_r":
            return rest - 0.30 + math.sin(phase * 1.4) * 0.08
        if action == "hurt":
            return rest + 0.45
        if action == "death":
            return rest + min(1.0, ap + 0.4) * 1.9
        if action == "walk":
            return rest + math.sin(phase * 2.2) * 0.12
        return rest + math.sin(phase * 0.8) * 0.05

    @staticmethod
    def staff_points(boss, x, y):
        """(pivot, tip) pygame.Vector2 ruang LAYAR.

        ``tip`` = pusat tengkorak di puncak tongkat.  Dipakai
        heroes/nyxara_fx (trail ayunan, titik lahir proyektil) dan
        overlay debug — jembatan satu-satunya ke geometri tongkat.
        """
        G = _NS_nyxara
        action, phase, ap = G.pose_of(boss)
        facing = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        sc = G.body_scale(boss)
        p = G._staff_pivot_local(action, ap, phase, boss)
        th = G._staff_angle(action, ap, phase, boss)
        head = (p[0] + G.STAFF_SHAFT * math.cos(th),
                p[1] + G.STAFF_SHAFT * math.sin(th))
        pivot = pygame.Vector2(x + p[0] * facing * sc, y + p[1] * sc)
        tip = pygame.Vector2(x + head[0] * facing * sc, y + head[1] * sc)
        return (pivot, tip)

    #: Alias kompatibilitas — beberapa alat memakai nama generik.
    @staticmethod
    def weapon_points(boss, x, y):
        return _NS_nyxara.staff_points(boss, x, y)

    @staticmethod
    def _swing_hitbox(boss, cx, cy):
        """Rect hitbox ayunan (ruang canvas, sc=1) saat jendela aktif."""
        if not getattr(boss, "_nx_hit_active", False):
            return None
        f = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        reach = int(_NS_nyxara.MELEE_REACH * 0.9)
        top = int(cy - 42)
        h = 74
        left = int(cx) if f > 0 else int(cx) - reach
        return pygame.Rect(left, top, max(8, reach), max(10, h))

    @staticmethod
    def _hurtbox(boss, cx, cy):
        """Hurtbox badan (ruang canvas, sc=1; untuk overlay debug)."""
        w, h = 44, 70
        return pygame.Rect(int(cx - w / 2), int(cy - 50), w, h)

    # ===================================================================
    # GERBANG LAPISAN HIDUP (heroes/nyxara_fx)
    #   Trail ayunan, partikel, proyektil, skill FX, impact, hit-stop,
    #   dan screen shake hidup di RUANG LAYAR skala 1:1 supaya tidak
    #   ikut beku / menyusut bersama sprite cache di lane hero. Kalau
    #   modulnya tidak ada, owns() False dan renderer menggambar
    #   fallback canvas sendiri (kehilangan polish, BUKAN efek).
    # ===================================================================
    _LIVE_MOD = None            # None = belum dicari, False = tidak ada

    @staticmethod
    def _live_module():
        NS = _NS_nyxara
        if NS._LIVE_MOD is None:
            try:
                from heroes import nyxara_fx as mod
                NS._LIVE_MOD = mod if getattr(mod, "NYXARA_FX_ENABLED",
                                              True) else False
            except Exception:
                NS._LIVE_MOD = False
        return NS._LIVE_MOD or None

    @staticmethod
    def live_fx_ready():
        return _NS_nyxara._live_module() is not None

    @staticmethod
    def _live_fx(boss, surface, x, y, want_draw, portrait):
        """Pasang/gambar lapisan hidup. Return (mod_untuk_draw, owned)."""
        NS = _NS_nyxara
        if portrait:
            return None, False
        mod = NS._live_module()
        if mod is None:
            return None, False
        try:
            if want_draw:
                mod.draw_ground_layer(surface, boss, x, y)
            else:
                mod.attach(boss)
        except Exception:
            return None, False
        try:
            owned = bool(mod.owns(boss))
            if owned and not want_draw:
                # Lane hero: yang menggambar lapisan hidup adalah
                # pipeline heroes/__init__. Kalau ternyata TIDAK ada
                # yang menggambarnya, jangan matikan fallback canvas.
                checker = getattr(mod, "recently_drawn", None)
                if checker is not None:
                    owned = bool(checker(boss))
        except Exception:
            owned = False
        return (mod if want_draw else None), owned

    # ===================================================================
    # OFFSET BADAN per pose (bob napas, lean, flare hem)
    # ===================================================================
    @staticmethod
    def _body_offsets(action, ap, phase, boss=None):
        """(dx, dy, flare) — offset badan relatif jangkar."""
        G = _NS_nyxara
        if action == "idle":
            breathe = math.sin(phase * 0.8)
            return (0.0, breathe * 2.0, 0.25 + 0.1 * breathe)
        if action == "walk":
            step = math.sin(phase * 2.2)
            return (step * 2.0, -abs(math.sin(phase * 2.2)) * 3.0,
                    0.55 + 0.2 * abs(step))
        if action == "swing":
            if ap < 0.30:
                t = G._ease_out_cubic(ap / 0.30)
                return (G._lerp(0, -4, t), -1.0, G._lerp(0.3, 0.9, t))
            if ap < 0.62:
                t = G._ease_in_out((ap - 0.30) / 0.32)
                return (G._lerp(-4, 7, t), 1.0, G._lerp(0.9, 1.5, t))
            return (G._lerp(7, 0, G._ease_in_out((ap - 0.62) / 0.38)),
                    0.0, G._lerp(1.5, 0.3, (ap - 0.62) / 0.38))
        if action == "attack":
            if ap < 0.32:
                return (-2.0, -1.0, 0.6)
            if ap < 0.50:
                return (4.0, 0.0, 1.0)
            return (2.0, 0.0, 0.5)
        if action == "cast_q":
            return (0.0, -3.0 * math.sin(min(1.0, ap * 1.4) * math.pi), 1.0)
        if action == "cast_w":
            return (1.0, -2.0, 1.2)
        if action == "cast_e":
            return (1.0 if ap >= 0.55 else -1.0, -1.0, 1.3)
        if action == "cast_r":
            return (0.0, -5.0 * math.sin(min(1.0, ap * 1.6) * math.pi), 1.6)
        if action == "hurt":
            return (-4.0, 1.0, 0.4)
        if action == "death":
            age = int(getattr(boss, "_nx_death_age", 0) or 0) \
                if boss is not None else 0
            return (2.0, min(26.0, age * 0.55), 0.2)
        return (0.0, 0.0, 0.3)

    # ===================================================================
    # RIG PIXEL-ART — komposisi berlapis
    #   SHADOW -> BACK LIMB -> HEM -> TORSO -> ARMOR -> HEAD -> WEAPON
    #   -> FRONT LIMB -> HIGHLIGHT
    # ===================================================================
    @staticmethod
    def _map(cx, cy, sc, facing, lx, ly):
        """Peta koordinat lokal -> layar (mirror + snap pixel)."""
        return (_NS_nyxara._snap(cx + lx * facing * sc),
                _NS_nyxara._snap(cy + ly * sc))

    @staticmethod
    def _draw_hem(surface, bx, by, phase, flare, action):
        """HEM jubah lebar compang-camping (silhouette dasar)."""
        c = _NS_nyxara.PALETTE
        sway = math.sin(phase * 1.5) * 2
        sway2 = math.sin(phase * 0.9 + 1.3) * 2
        fl = flare * 4
        pts = [
            (bx - 19 - fl, by + 2),
            (bx + 19 + fl, by + 2),
            (bx + 25 + fl + sway, by + 16),
            (bx + 23 + sway2, by + 30),
            (bx + 17, by + 40),
            # tepi compang: gigi segitiga chunky
            (bx + 12, by + 34), (bx + 9 + sway2, by + 46),
            (bx + 4, by + 38), (bx, by + 48 + sway),
            (bx - 4, by + 38), (bx - 9 + sway2, by + 46),
            (bx - 12, by + 34), (bx - 17, by + 40),
            (bx - 23 - sway2, by + 30),
            (bx - 25 - fl - sway, by + 16),
        ]
        # outline gelap 1px (offset), lalu isi dasar
        pygame.draw.polygon(surface, c["outline"],
                            [(px + 2, py + 2) for px, py in pts])
        pygame.draw.polygon(surface, c["robe_dark"], pts)

        # --- shading vertikal: bahu jubah terang -> hem gelap ---------------
        # Pita horizontal chunky (pixel-art banding) memberi volume pada rok.
        # Digambar pada layer terpisah lalu di-mask ke siluet hem supaya
        # tidak pernah bocor keluar polygon.
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        ox, oy = int(min(xs)) - 2, int(min(ys)) - 2
        lw = max(1, int(max(xs) - min(xs)) + 5)
        lh = max(1, int(max(ys) - min(ys)) + 5)
        layer = pygame.Surface((lw, lh), pygame.SRCALPHA)
        _bands = (
            (2,  11, "robe_mid"),
            (11, 21, "robe_dark"),
            (21, 32, "robe_dark"),
            (32, 52, "robe_darkest"),
        )
        for y0, y1, key in _bands:
            w_top = 19 + fl + (y0 * 0.30)
            w_bot = 19 + fl + (y1 * 0.30)
            sw_t = sway * (y0 / 30.0)
            sw_b = sway * (y1 / 30.0)
            pygame.draw.polygon(layer, c[key], [
                (bx - w_top + sw_t - ox, by + y0 - oy),
                (bx + w_top + sw_t - ox, by + y0 - oy),
                (bx + w_bot + sw_b - ox, by + y1 - oy),
                (bx - w_bot + sw_b - ox, by + y1 - oy),
            ])
        # mask: hanya piksel di dalam siluet hem yang dipertahankan
        mask = pygame.Surface((lw, lh), pygame.SRCALPHA)
        pygame.draw.polygon(mask, (255, 255, 255, 255),
                            [(px - ox, py - oy) for px, py in pts])
        layer.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surface.blit(layer, (ox, oy))
        pygame.draw.polygon(surface, c["outline"], pts, 1)

        # --- gigi compang bawah: sisi dalam gelap, ujung ter-rim ------------
        _teeth = ((12, 34, 9, 46), (4, 38, 0, 48), (-4, 38, -9, 46),
                  (-12, 34, -17, 40))
        for ax, ay, tx, ty in _teeth:
            sw = sway2 * 0.5
            pygame.draw.polygon(surface, c["robe_darkest"], [
                (bx + ax, by + ay), (bx + tx + sw, by + ty),
                (bx + (ax + tx) * 0.5 + sw, by + ay + 3),
            ])

        # --- lipatan jubah (garis vertikal chunky, gelap + highlight) -------
        for xoff in (-13, -7, -1, 6, 12):
            top = by + 8
            bot = by + 30 + math.sin(phase * 1.2 + xoff) * 2
            sw = sway * 0.55
            pygame.draw.line(surface, c["robe_darkest"],
                             (bx + xoff + sw, top), (bx + xoff + sw, bot), 1)
            pygame.draw.line(surface, c["robe_mid"],
                             (bx + xoff + 1 + sw, top + 2),
                             (bx + xoff + 1 + sw, bot - 3), 1)

        # --- rim light nether di kedua tepi ---------------------------------
        pygame.draw.line(surface, c["robe_high"],
                         (bx - 17 - fl * 0.7, by + 5),
                         (bx - 23 - sway, by + 26), 2)
        pygame.draw.line(surface, c["robe_light"],
                         (bx + 18 + fl * 0.7, by + 6),
                         (bx + 23 + sway, by + 24), 1)

    @staticmethod
    def _draw_torso(surface, bx, by, phase, action):
        """TORSO gempal + sash + gem nether di dada."""
        c = _NS_nyxara.PALETTE
        pygame.draw.polygon(surface, c["outline"], [
            (bx - 13, by - 25), (bx + 13, by - 25),
            (bx + 15, by - 11), (bx + 12, by + 4),
            (bx - 12, by + 4), (bx - 15, by - 11)])
        pygame.draw.polygon(surface, c["robe_dark"], [
            (bx - 12, by - 24), (bx + 12, by - 24),
            (bx + 14, by - 11), (bx + 11, by + 3),
            (bx - 11, by + 3), (bx - 14, by - 11)])
        # panel dalam (lebih gelap)
        pygame.draw.polygon(surface, c["inner_darkest"], [
            (bx - 8, by - 21), (bx + 8, by - 21),
            (bx + 9, by - 7), (bx - 9, by - 7)])
        # kulit dada malformed yang mengintip
        pygame.draw.rect(surface, c["skin_dark"], (bx - 5, by - 20, 10, 6))
        pygame.draw.rect(surface, c["skin_mid"], (bx - 4, by - 19, 8, 3))
        pygame.draw.rect(surface, c["skin_light"], (bx - 3, by - 19, 3, 1))
        # sash pinggang + trim emas
        pygame.draw.rect(surface, c["robe_darkest"],
                         (bx - 15, by - 2, 30, 5))
        pygame.draw.rect(surface, c["gold_dark"], (bx - 14, by - 1, 28, 1))
        pygame.draw.rect(surface, c["gold_mid"], (bx - 12, by + 1, 24, 1))
        # gem nether dada (berdenyut)
        pulse = 0.65 + 0.35 * math.sin(phase * 3.0)
        pygame.draw.rect(surface, c["nether_dark"], (bx - 3, by - 15, 6, 6))
        pygame.draw.rect(surface, c["nether_mid"], (bx - 2, by - 14, 4, 4))
        if pulse > 0.55:
            pygame.draw.rect(surface, c["nether_bright"],
                             (bx - 1, by - 13, 2, 2))

    @staticmethod
    def _draw_pauldrons(surface, bx, by, phase, action):
        """PAULDRON bahu chunky + kerah jubah tinggi (silhouette)."""
        c = _NS_nyxara.PALETTE
        lift = 1 if action in ("cast_w", "cast_r") else 0
        # kerah tinggi di belakang leher
        pygame.draw.polygon(surface, c["outline"], [
            (bx - 15, by - 22), (bx - 11, by - 34), (bx + 11, by - 34),
            (bx + 15, by - 22)])
        pygame.draw.polygon(surface, c["robe_darkest"], [
            (bx - 13, by - 23), (bx - 10, by - 33), (bx + 10, by - 33),
            (bx + 13, by - 23)])
        pygame.draw.polygon(surface, c["robe_mid"], [
            (bx - 10, by - 24), (bx - 8, by - 31), (bx + 8, by - 31),
            (bx + 10, by - 24)])
        for side in (-1, 1):
            sx = bx + side * 14
            sy = by - 23 - (lift if side == -1 else 0)
            pygame.draw.rect(surface, c["outline"], (sx - 7, sy - 4, 15, 10))
            pygame.draw.rect(surface, c["robe_darkest"], (sx - 6, sy - 3, 13, 8))
            pygame.draw.rect(surface, c["robe_dark"], (sx - 5, sy - 3, 11, 4))
            # spike pauldron (silhouette)
            pygame.draw.polygon(surface, c["robe_mid"], [
                (sx - side * 6, sy - 3), (sx - side * 10, sy + 1),
                (sx - side * 5, sy + 3)])
            # trim emas + pixel highlight
            pygame.draw.rect(surface, c["gold_dark"], (sx - 6, sy + 4, 13, 1))
            pygame.draw.rect(surface, c["robe_light"], (sx - 4, sy - 2, 3, 1))

    @staticmethod
    def _draw_head(surface, bx, by, facing, phase, action):
        """KEPALA malformed + mahkota bertanduk (silhouette khas Nyxara)."""
        c = _NS_nyxara.PALETTE
        tilt = 0
        if action == "idle":
            tilt = int(math.sin(phase * 0.8) * 1)
        elif action == "walk":
            tilt = int(math.sin(phase * 2.2) * 1.5)
        elif action == "hurt":
            tilt = -2
        elif action == "death":
            tilt = 4
        hx, hy = bx + tilt * 0.5, by - 34 + tilt

        # ── TENGKORAK/KEPALA: dome olive lonjong ──────────────────
        skull = [
            (hx - 9, hy + 6), (hx - 10, hy - 3), (hx - 6, hy - 10),
            (hx + 2, hy - 12), (hx + 9, hy - 8), (hx + 10, hy + 1),
            (hx + 7, hy + 8), (hx - 4, hy + 9),
        ]
        pygame.draw.polygon(surface, c["outline"],
                            [(px + 2, py + 2) for px, py in skull])
        pygame.draw.polygon(surface, c["skin_darkest"], skull)
        pygame.draw.polygon(surface, c["skin_dark"], [
            (hx - 8, hy + 5), (hx - 9, hy - 3), (hx - 5, hy - 9),
            (hx + 2, hy - 11), (hx + 8, hy - 7), (hx + 9, hy + 1),
            (hx + 6, hy + 7), (hx - 3, hy + 8)])
        # band terang di dahi (light dari atas)
        pygame.draw.polygon(surface, c["skin_mid"], [
            (hx - 6, hy - 6), (hx + 6, hy - 8), (hx + 7, hy - 2),
            (hx - 6, hy - 1)])
        pygame.draw.rect(surface, c["skin_light"], (hx - 4, hy - 7, 6, 2))
        pygame.draw.rect(surface, c["skin_shine"], (hx - 3, hy - 7, 2, 1))

        # ── MAHKOTA BERTANDUK (2 tanduk besar + 2 kecil) ──────────
        for side, ln, lift in ((-1, 13, 0), (1, 15, -1)):
            base_x = hx + side * 7
            base_y = hy - 6 + lift
            horn = [
                (base_x, base_y + 2),
                (base_x + side * 3, base_y - 3),
                (base_x + side * 6, base_y - ln + 3),
                (base_x + side * 3, base_y - ln),
                (base_x - side * 1, base_y - ln + 5),
                (base_x - side * 3, base_y - 1),
            ]
            pygame.draw.polygon(surface, c["outline"],
                                [(px + 1, py + 1) for px, py in horn])
            pygame.draw.polygon(surface, c["horn_dark"], horn)
            pygame.draw.polygon(surface, c["horn_mid"], [
                (base_x + side * 1, base_y),
                (base_x + side * 4, base_y - ln + 4),
                (base_x + side * 2, base_y - ln + 1),
                (base_x - side * 1, base_y - 1)])
            pygame.draw.line(surface, c["horn_light"],
                             (base_x + side * 2, base_y - 2),
                             (base_x + side * 3, base_y - ln + 4), 1)
            pygame.draw.rect(surface, c["horn_high"],
                             (base_x + side * 3, base_y - ln + 4, 1, 1))
        # tanduk kecil tengah (crown ridge)
        for dx in (-3, 1):
            pygame.draw.polygon(surface, c["horn_dark"], [
                (hx + dx, hy - 10), (hx + dx + 3, hy - 10),
                (hx + dx + 1, hy - 15)])
            pygame.draw.line(surface, c["horn_mid"],
                             (hx + dx + 1, hy - 11), (hx + dx + 1, hy - 14), 1)
        # band mahkota emas
        pygame.draw.rect(surface, c["gold_dark"], (hx - 8, hy - 6, 17, 3))
        pygame.draw.rect(surface, c["gold_mid"], (hx - 7, hy - 6, 15, 1))
        pygame.draw.rect(surface, c["gold_shine"], (hx - 5, hy - 6, 2, 1))

        # ── MATA nether menyala (selalu hidup, intensitas naik-turun)
        glow = _NS_nyxara._cached(
            ("eyeglow", 4),
            lambda: _NS_nyxara._glow_surf(4, c["nether_mid"]))
        glow.set_alpha(150)
        surface.blit(glow, (int(hx) - glow.get_width() // 2,
                            int(hy) - glow.get_height() // 2))
        glow.set_alpha(255)
        eye_pulse = 0.6 + 0.4 * math.sin(phase * 4.0)
        ex = 1 if facing > 0 else 0
        pygame.draw.rect(surface, c["shadow_deep"], (hx - 6 + ex, hy - 3, 4, 4))
        pygame.draw.rect(surface, c["shadow_deep"], (hx + 1 + ex, hy - 3, 4, 4))
        pygame.draw.rect(surface, c["eye_dark"], (hx - 6 + ex, hy - 2, 3, 3))
        pygame.draw.rect(surface, c["eye_dark"], (hx + 1 + ex, hy - 2, 3, 3))
        pygame.draw.rect(surface, c["eye_mid"], (hx - 5 + ex, hy - 2, 2, 2))
        pygame.draw.rect(surface, c["eye_mid"], (hx + 2 + ex, hy - 2, 2, 2))
        if eye_pulse > 0.55:
            pygame.draw.rect(surface, c["eye_bright"], (hx - 5 + ex, hy - 2, 2, 1))
            pygame.draw.rect(surface, c["eye_bright"], (hx + 2 + ex, hy - 2, 2, 1))
        if eye_pulse > 0.85:
            pygame.draw.rect(surface, c["eye_hot"], (hx - 5 + ex, hy - 2, 1, 1))
            pygame.draw.rect(surface, c["eye_hot"], (hx + 3 + ex, hy - 2, 1, 1))

        # ── mulut bergigi (chunky) ────────────────────────────────
        pygame.draw.rect(surface, c["shadow_deep"], (hx - 5, hy + 3, 11, 3))
        for i in range(4):
            pygame.draw.rect(surface, c["bone_light"],
                             (hx - 4 + i * 3, hy + 3, 1, 2))
        # rim light tepi kanan kepala
        pygame.draw.line(surface, c["skin_light"],
                         (hx + 9, hy - 6), (hx + 8, hy + 4), 1)

    @staticmethod
    def _draw_staff_at(surface, bx, by, sc, facing, angle, pivot, glow_k,
                       phase):
        """TONGKAT: gagang kayu + tengkorak nether bercahaya di puncak.

        glow_k 0..1 mengatur intensitas cahaya nether di kepala tongkat.
        """
        G = _NS_nyxara
        c = G.PALETTE
        P = lambda lx, ly: G._map(bx, by, sc, facing, lx, ly)  # noqa: E731
        head = (pivot[0] + G.STAFF_SHAFT * math.cos(angle),
                pivot[1] + G.STAFF_SHAFT * math.sin(angle))
        butt = (pivot[0] - G.STAFF_BUTT * math.cos(angle),
                pivot[1] - G.STAFF_BUTT * math.sin(angle))
        p_head = P(head[0], head[1])
        p_butt = P(butt[0], butt[1])
        w_shaft = max(2, int(5 * sc))

        # ── gagang: outline + kayu 3 band ─────────────────────────
        pygame.draw.line(surface, c["outline"],
                         (p_butt[0] + 1, p_butt[1] + 1),
                         (p_head[0] + 1, p_head[1] + 1), w_shaft + 2)
        pygame.draw.line(surface, c["wood_dark"], p_butt, p_head, w_shaft)
        pygame.draw.line(surface, c["wood_mid"], p_butt, p_head,
                         max(1, w_shaft - 2))
        pygame.draw.line(surface, c["wood_light"],
                         (p_butt[0], p_butt[1] - 1),
                         (p_head[0], p_head[1] - 1), 1)
        # bungkus emas di gagang (3 titik chunky)
        for i in range(3):
            t = 0.28 + i * 0.14
            gp = P(butt[0] + (head[0] - butt[0]) * t,
                   butt[1] + (head[1] - butt[1]) * t)
            pygame.draw.rect(surface, c["gold_dark"], (gp[0] - 1, gp[1] - 1, 3, 3))
            pygame.draw.rect(surface, c["gold_mid"], (gp[0] - 1, gp[1] - 1, 2, 1))

        # ── CAKAR penyangga (4 taring emas memeluk tengkorak) ─────
        for k in (-1, 1):
            a = angle + k * 0.55
            c0 = P(head[0] - math.cos(angle) * 7.0,
                   head[1] - math.sin(angle) * 7.0)
            c1 = P(head[0] - math.cos(angle) * 7.0 + math.cos(a) * 9.0,
                   head[1] - math.sin(angle) * 7.0 + math.sin(a) * 9.0)
            pygame.draw.line(surface, c["outline"],
                             (c0[0] + 1, c0[1] + 1), (c1[0] + 1, c1[1] + 1), 4)
            pygame.draw.line(surface, c["gold_dark"], c0, c1, 3)
            pygame.draw.line(surface, c["gold_mid"], c0, c1, 1)

        # ── GLOW nether di sekitar tengkorak ──────────────────────
        gr = int(9 + 7 * max(0.0, min(1.0, glow_k)))
        halo = G._cached(("staffglow", gr),
                         lambda r=gr: G._glow_surf(r, c["nether_mid"]))
        gpulse = 0.55 + 0.45 * math.sin(phase * 5.0)
        halo.set_alpha(int(200 * gpulse * max(0.35, glow_k)))
        surface.blit(halo, (p_head[0] - halo.get_width() // 2,
                            p_head[1] - halo.get_height() // 2))
        halo.set_alpha(255)

        # ── TENGKORAK di puncak (chunky pixel) ────────────────────
        r = max(3, int(G.STAFF_SKULL_R * sc))
        hx0, hy0 = p_head
        pygame.draw.circle(surface, c["outline"], (hx0, hy0), r + 1)
        pygame.draw.circle(surface, c["bone_dark"], (hx0, hy0), r)
        pygame.draw.circle(surface, c["bone_mid"], (hx0 - 1, hy0 - 1), r - 1)
        pygame.draw.rect(surface, c["bone_light"], (hx0 - 3, hy0 - r, 3, 2))
        # rahang
        pygame.draw.rect(surface, c["bone_dark"], (hx0 - 3, hy0 + r - 2, 7, 3))
        pygame.draw.rect(surface, c["bone_mid"], (hx0 - 3, hy0 + r - 2, 7, 1))
        for i in range(3):
            pygame.draw.rect(surface, c["shadow_deep"],
                             (hx0 - 3 + i * 3, hy0 + r - 2, 1, 2))
        # socket mata nether
        pygame.draw.rect(surface, c["shadow_deep"], (hx0 - 3, hy0 - 2, 3, 3))
        pygame.draw.rect(surface, c["shadow_deep"], (hx0 + 1, hy0 - 2, 3, 3))
        eye_col = c["nether_bright"] if gpulse > 0.55 else c["nether_mid"]
        pygame.draw.rect(surface, eye_col, (hx0 - 3, hy0 - 1, 2, 2))
        pygame.draw.rect(surface, eye_col, (hx0 + 1, hy0 - 1, 2, 2))
        if glow_k > 0.6 and gpulse > 0.8:
            pygame.draw.rect(surface, c["nether_hot"], (hx0 - 2, hy0 - 1, 1, 1))
            pygame.draw.rect(surface, c["nether_hot"], (hx0 + 2, hy0 - 1, 1, 1))

        # ── percikan orbit di sekitar tengkorak saat cast/swing ───
        if glow_k > 0.35:
            for i in range(3):
                a = phase * 5.0 + i * (math.tau / 3.0)
                spx = hx0 + int(math.cos(a) * (r + 5))
                spy = hy0 + int(math.sin(a) * (r + 5))
                pygame.draw.rect(surface, c["nether_light"], (spx, spy, 2, 2))
                pygame.draw.rect(surface, c["nether_hot"], (spx, spy, 1, 1))

    @staticmethod
    def _draw_arms(surface, bx, by, sc, facing, action, ap, phase, pivot):
        """Lengan jubah (sleeve chunky 2 segmen) + tangan cakar."""
        G = _NS_nyxara
        c = G.PALETTE
        P = lambda lx, ly: G._map(bx, by, sc, facing, lx, ly)  # noqa: E731

        def sleeve(p_from, p_to, width):
            a = P(*p_from)
            b = P(*p_to)
            pygame.draw.line(surface, c["outline"],
                             (a[0] + 1, a[1] + 1), (b[0] + 1, b[1] + 1),
                             width + 2)
            pygame.draw.line(surface, c["robe_darkest"], a, b, width)
            pygame.draw.line(surface, c["robe_dark"], a, b, max(1, width - 2))
            pygame.draw.line(surface, c["robe_mid"],
                             (a[0], a[1] - 1), (b[0], b[1] - 1), 1)

        def claw_hand(p_xy, spread=1.0):
            h = P(*p_xy)
            pygame.draw.circle(surface, c["outline"], h, max(3, int(3 * sc)))
            pygame.draw.circle(surface, c["skin_dark"], h, max(2, int(2.5 * sc)))
            pygame.draw.circle(surface, c["skin_mid"],
                               (h[0] - 1, h[1] - 1), max(1, int(1.5 * sc)))
            # 3 cakar pendek
            for k in (-1, 0, 1):
                cx2 = h[0] + int(k * 3 * spread)
                pygame.draw.rect(surface, c["bone_light"],
                                 (cx2, h[1] + 2, 1, 2))

        # ── lengan TONGKAT (memegang pivot) ───────────────────────
        shoulder = (pivot[0] - 7, pivot[1] + 10)
        elbow = (pivot[0] - 3, pivot[1] + 4)
        sleeve(shoulder, elbow, max(3, int(5 * sc)))
        sleeve(elbow, pivot, max(3, int(4 * sc)))
        claw_hand(pivot, 0.8)

        # ── lengan BEBAS (pengatur sihir) ─────────────────────────
        if action == "attack":
            if ap < 0.32:
                t = G._ease_out_cubic(ap / 0.32)
                free_to = G._lerp_pt((-14, -8), (-6, -17), t)
            elif ap < 0.50:
                t = G._ease_in_cubic((ap - 0.32) / 0.18)
                free_to = G._lerp_pt((-6, -17), (17, -13), t)
            else:
                t = G._ease_in_out((ap - 0.50) / 0.50)
                free_to = G._lerp_pt((17, -13), (-14, -8), t)
        elif action == "swing":
            if ap < 0.30:
                free_to = (-5, -24)
            elif ap < 0.62:
                free_to = (6, -6)
            else:
                free_to = (-12, -10)
        elif action in ("cast_q", "cast_w"):
            free_to = (14, -20 - int(math.sin(phase * 3.0) * 2))
        elif action == "cast_e":
            free_to = (14, -20) if ap >= 0.55 else (-12, -20)
        elif action == "cast_r":
            free_to = (13, -24 - int(math.sin(phase * 2.4) * 2))
        elif action == "hurt":
            free_to = (-15, -12)
        elif action == "death":
            free_to = (-6, -2)
        elif action == "walk":
            free_to = (-13, -10 + int(math.sin(phase * 2.2) * 2))
        else:
            free_to = (-14, -9 + int(math.sin(phase * 0.9) * 1.5))
        f_shoulder = (-11, -16)
        f_elbow = G._lerp_pt(f_shoulder, free_to, 0.55)
        sleeve(f_shoulder, f_elbow, max(3, int(4 * sc)))
        sleeve(f_elbow, free_to, max(2, int(3 * sc)))
        claw_hand(free_to)

        # ── glow tangan saat cast / rilis orb ─────────────────────
        charging = (action == "attack" and 0.20 <= ap <= 0.55) or \
                   action in ("cast_q", "cast_w", "cast_e", "cast_r")
        if charging:
            hp = P(*free_to)
            k = math.sin(ap * math.pi) if action == "attack" else \
                math.sin(phase * 5.0) * 0.5 + 0.5
            r = int(3 + 4 * k)
            hand_glow = G._cached(
                ("handglow", r),
                lambda r=r: G._glow_surf(r, c["nether_light"]))
            hand_glow.set_alpha(int(200 * max(0.3, k)))
            surface.blit(hand_glow, (hp[0] - hand_glow.get_width() // 2,
                                     hp[1] - hand_glow.get_height() // 2))
            hand_glow.set_alpha(255)
            pygame.draw.rect(surface, c["nether_bright"],
                             (hp[0] - 1, hp[1] - 1, 3, 3))
            pygame.draw.rect(surface, c["nether_hot"], (hp[0], hp[1], 1, 1))

    @staticmethod
    def _draw_highlights(surface, bx, by, phase, action):
        """Highlight pixel: rim light + bara nether naik dari hem."""
        c = _NS_nyxara.PALETTE
        # rim kiri torso
        pygame.draw.line(surface, c["robe_light"],
                         (bx - 13, by - 21), (bx - 14, by - 5), 1)
        # dua titik terang di sash
        pygame.draw.rect(surface, c["gold_shine"], (bx - 6, by - 1, 1, 1))
        pygame.draw.rect(surface, c["gold_shine"], (bx + 5, by + 1, 1, 1))
        # bara nether naik dari hem (2 pixel berdenyut)
        t = (phase * 0.5) % 1.0
        y0 = by + 34 - int(t * 26)
        if (1.0 - t) > 0.25:
            pygame.draw.rect(surface, c["nether_light"],
                             (bx - 18 + int(math.sin(phase + 1) * 3), y0, 1, 1))
            pygame.draw.rect(surface, c["nether_hot"],
                             (bx + 16 + int(math.sin(phase) * 3), y0 + 4, 1, 1))

    @staticmethod
    def _draw_flash_hurt(surface, bx, by, flash, facing):
        """Tint putih singkat saat kena damage (hurt_flash_timer)."""
        if flash <= 0:
            return
        overlay = pygame.Surface((52, 84), pygame.SRCALPHA)
        pygame.draw.polygon(overlay, (255, 255, 255, min(90, int(flash))),
                            [(2, 10), (50, 10), (48, 50), (30, 78), (8, 50)])
        surface.blit(overlay, (int(bx) - 26, int(by) - 44))

    # ===================================================================
    # LAPISAN TANAH (bayangan + mist + runes + telegraph skill)
    # ===================================================================
    @staticmethod
    def _draw_ground_layer(surface, boss, x, y, phase, skill, owned):
        G = _NS_nyxara
        c = G.PALETTE
        gy = y + G.GROUND_DY
        # bayangan kontak
        shadow = G._cached("shadow", G._shadow_surf)
        surface.blit(shadow, (x - shadow.get_width() // 2,
                              gy - shadow.get_height() // 2))
        # kabut nether (melayang)
        mb = G._qphase(phase, 6)
        mist = G._cached(("mist", mb), lambda b=mb: G._mist_surf(b))
        surface.blit(mist, (x - mist.get_width() // 2, gy - 26))
        # rune circle
        rb = G._qphase(phase, 8)
        rune = G._cached(("rune", rb, bool(skill)),
                         lambda b=rb, s=bool(skill): G._rune_surf(b, s))
        surface.blit(rune, (x - rune.get_width() // 2, gy - 24))
        # telegraph skill di tanah (canvas fallback; versi hidup di
        # nyxara_fx.draw_ground_layer)
        if not owned and skill:
            prog = float(getattr(boss, "_nx_skill_progress", 0.0) or 0.0)
            r = int(G.SKILL_RADIUS.get(skill, 130))
            color = c["nether_mid"] if skill in ("q", "w") else c["nether_light"]
            pygame.draw.ellipse(surface, (*color, 120),
                                (x - r, gy - r // 3, r * 2, r * 2 // 3), 2)
            if prog > 0.34:
                pygame.draw.ellipse(
                    surface, (*c["nether_bright"], 150),
                    (x - r + 4, gy - r // 3 + 2, r * 2 - 8, r * 2 // 3 - 4), 1)

    # ===================================================================
    # FALLBACK FX CANVAS (hanya jika modul hidup tidak tersedia)
    # ===================================================================
    @staticmethod
    def _manage_projectiles(boss, surface, phase):
        """Proyektil fallback sederhana (jalur tanpa heroes/nyxara_fx)."""
        projs = getattr(boss, "_nx_projectiles", None)
        if not projs:
            return
        c = _NS_nyxara.PALETTE
        keep = []
        for p in projs:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["age"] += 1
            dist = math.hypot(p["tx"] - p["x"], p["ty"] - p["y"])
            if dist < 8.0 or p["age"] > 140:
                continue
            px, py = int(p["x"]), int(p["y"])
            # orb chunky 4 band (bukan lingkaran polos: ada inti panas)
            pygame.draw.circle(surface, c["nether_dark"], (px, py), 7)
            pygame.draw.circle(surface, c["nether_mid"], (px, py), 5)
            pygame.draw.circle(surface, c["nether_light"], (px - 1, py - 1), 3)
            pygame.draw.rect(surface, c["nether_hot"], (px - 1, py - 2, 2, 2))
            keep.append(p)
        boss._nx_projectiles = keep

    @staticmethod
    def _spawn_fallback_projectile(boss, x, y, blast=False):
        G = _NS_nyxara
        if not hasattr(boss, "_nx_projectiles"):
            boss._nx_projectiles = []
        if len(boss._nx_projectiles) >= 12:      # cap keras fallback
            return
        tx, ty = G._target_position(boss, x, y)
        sx = x + 22 * (getattr(boss, "direction", 1) or 1)
        sy = y - 14
        dx, dy = tx - sx, ty - sy
        d = math.hypot(dx, dy) or 1.0
        speed = 8.0 if blast else 5.5
        boss._nx_projectiles.append({
            "x": float(sx), "y": float(sy),
            "vx": dx / d * speed, "vy": dy / d * speed,
            "tx": float(tx), "ty": float(ty), "age": 0})

    # ===================================================================
    # ENTRY POINT
    # ===================================================================
    @staticmethod
    def draw_nyxara(surface, boss, x, y):
        """Entry point Boss.draw() sekaligus heroes.render_hero().

        Urutan lapisan (kontrak render order proyek):
          GROUND FX -> SHADOW -> BACK FX -> BODY/ARMOR/HEAD -> WEAPON
          -> ATTACK TRAIL -> PROJECTILE -> FRONT PARTICLES -> SKILL FX
          -> IMPACT FX -> DEBUG.
        Trail ayunan, partikel, proyektil, skill FX, impact, hit-stop,
        dan shake hidup di heroes/nyxara_fx.py (layar 1:1, di luar
        cache); canvas hanya fallback bila modul itu tidak tersedia.
        """
        NS = _NS_nyxara
        pulse = float(getattr(boss, "pulse", 0.0))
        portrait = bool(getattr(boss, "_portrait_hd", False))
        hero_lane = hasattr(boss, "_render_scale")

        # ── CONTROLLER ANIMASI ─────────────────────────────────────
        NS._update_nyxara_anim(boss)
        moving = bool(getattr(boss, "_nx_moving", False))
        action, phase, ap = NS._resolve_pose(boss, moving)
        boss._nx_pose_action = action

        # ── LAPISAN HIDUP (ground) ─────────────────────────────────
        live, owned = NS._live_fx(boss, surface, x, y, not hero_lane,
                                  portrait)
        boss._nx_suppress_canvas_fx = owned

        # ── GROUND: bayangan + mist + runes + telegraph ─────────────
        if not portrait:
            NS._draw_ground_layer(surface, boss, x, y, pulse,
                                  getattr(boss, "_nx_skill", None), owned)

        # ── RIG (komposit satu pose) ───────────────────────────────
        # Konvensi pipeline hero (heroes/__init__): rig SELALU digambar
        # 1:1 di ruang canvas; smoothscale pipeline yang mengecilkan.
        # ``body_scale`` hanya untuk FX ruang layar (staff_points) dan
        # konversi dunia->canvas (target position).
        facing = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        sc = 1.0
        dx, dy, flare = NS._body_offsets(action, ap, phase, boss)
        if action == "death":
            age = int(getattr(boss, "_nx_death_age", 0) or 0)
            dy += min(26.0, age * 0.55)
        bx = x + dx * facing
        by = y - 14 + dy

        pivot = NS._staff_pivot_local(action, ap, phase, boss)
        angle = NS._staff_angle(action, ap, phase, boss)
        glow_k = 0.0
        if action == "swing":
            glow_k = 1.0 if 0.24 <= ap <= 0.60 else 0.45
        elif action == "attack":
            glow_k = 0.9 if 0.28 <= ap <= 0.55 else 0.3
        elif action == "cast_e":
            glow_k = 1.0
        elif action.startswith("cast"):
            glow_k = 0.75

        NS._draw_hem(surface, bx, by + 4, phase, flare, action)
        NS._draw_torso(surface, bx, by, phase, action)
        NS._draw_pauldrons(surface, bx, by, phase, action)
        NS._draw_head(surface, bx, by, facing, phase, action)
        NS._draw_staff_at(surface, bx, by, sc, facing, angle, pivot,
                          glow_k, pulse)
        NS._draw_arms(surface, bx, by, sc, facing, action, ap, phase, pivot)
        if not portrait:
            NS._draw_highlights(surface, bx, by, pulse, action)

        # flash hurt (di atas semuanya)
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        if flash > 0:
            NS._draw_flash_hurt(surface, bx, by, flash * 6, facing)

        # ── FALLBACK CANVAS FX (jalur boss tanpa modul hidup) ──────
        if not portrait and not owned and not hero_lane:
            kind = NS.attack_kind(boss)
            active = bool(getattr(boss, "_nx_attack_active", False))
            if active and kind == "orb" and \
                    not getattr(boss, "_nx_fallback_spawned", False) and \
                    ap >= NS.ATTACK_RELEASE_FRAME:
                NS._spawn_fallback_projectile(boss, x, y)
                boss._nx_fallback_spawned = True
            if not active:
                boss._nx_fallback_spawned = False
            skill = getattr(boss, "_nx_skill", None)
            if skill == "q" and \
                    not getattr(boss, "_nx_fallback_blast", False) and \
                    ap >= 0.42:
                NS._spawn_fallback_projectile(boss, x, y, blast=True)
                boss._nx_fallback_blast = True
            if skill != "q":
                boss._nx_fallback_blast = False
            NS._manage_projectiles(boss, surface, pulse)

        # ── LAPISAN HIDUP DI ATAS (trail/proyektil/impact/skill) ───
        if live is not None:
            try:
                live.draw_live_layer(surface, boss, x, y)
            except Exception:
                pass

        # ── DEBUG ──────────────────────────────────────────────────
        if NS.DEBUG_CHARACTER and not portrait:
            NS._draw_nx_debug(surface, boss, x, y)

    # ===================================================================
    # OVERLAY DEBUG (DEBUG_CHARACTER = True)
    # ===================================================================
    _DBG_FONT = None

    @staticmethod
    def _dbg_font(size=12):
        if _NS_nyxara._DBG_FONT is None:
            try:
                _NS_nyxara._DBG_FONT = pygame.font.Font(None, size + 4)
            except Exception:                      # pragma: no cover
                _NS_nyxara._DBG_FONT = pygame.font.Font(None, 16)
        return _NS_nyxara._DBG_FONT

    @staticmethod
    def _draw_nx_debug(surface, boss, x, y):
        G = _NS_nyxara
        hb = G._swing_hitbox(boss, x, y)
        if hb is not None:
            pygame.draw.rect(surface, (255, 80, 80), hb, 1)
        pygame.draw.rect(surface, (80, 160, 255), G._hurtbox(boss, x, y), 1)
        pygame.draw.circle(surface, (255, 200, 60), (int(x), int(y)),
                           int(G.MELEE_REACH), 1)
        pv, tip = G.staff_points(boss, x, y)
        pygame.draw.line(surface, (200, 255, 90),
                         (int(pv.x), int(pv.y)), (int(tip.x), int(tip.y)), 1)
        pygame.draw.circle(surface, (200, 255, 90),
                           (int(tip.x), int(tip.y)), 3, 1)
        parts = 0
        fps = 0.0
        mod = G._live_module()
        if mod is not None:
            try:
                parts = int(mod.total_particles())
            except Exception:
                parts = 0
            d = getattr(boss, "_nyxara_fx", None)
            if d is not None:
                fps = float(getattr(d, "fps", 0.0))
        lines = [
            f"NYXARA  state={getattr(boss, '_nx_state', 'IDLE')}"
            f"<{getattr(boss, '_nx_state_prev', '-')}>",
            f"pose={getattr(boss, '_nx_pose_action', '-')} "
            f"kind={G.attack_kind(boss)} "
            f"phase={getattr(boss, '_nx_attack_phase', '-')}",
            f"atk_t={float(getattr(boss, '_nx_attack_progress', 0.0)):.2f} "
            f"hit={bool(getattr(boss, '_nx_hit_active', False))} "
            f"frame={int(getattr(boss, '_nx_state_frame', 0))}",
            f"skill={getattr(boss, '_nx_skill', '-')} "
            f"t={float(getattr(boss, '_nx_skill_progress', 0.0)):.2f}",
            f"partikel={parts} fps~{fps:.0f}",
        ]
        font = G._dbg_font()
        yy = int(y) - 100
        for ln in lines:
            img = font.render(ln, True, (210, 255, 140))
            surface.blit(img, (int(x) - 95, yy))
            yy += 13

    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    @staticmethod
    def draw_boss(surface, boss, x, y):
        _NS_nyxara.draw_nyxara(surface, boss, x, y)


# ====================================================================
# GRAVEFANG
# ====================================================================
class _NS_gravefang:
    """Namespace gravefang - isi asli tidak diubah."""

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    # ---------------------------------------------------------------------------
    # HD Color Palette - Arc Warden inspired deep purple / electric blue
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Armor – dark indigo / gold trim
        "armor_darkest":  (12,  10,  28),
        "armor_dark":     (28,  22,  58),
        "armor_mid":      (52,  42,  95),
        "armor_light":    (85,  72, 140),
        "armor_high":     (130, 115, 185),
        "armor_shine":    (195, 185, 230),

        # Gold trim
        "gold_dark":      (100, 72,  18),
        "gold_mid":       (175, 135, 42),
        "gold_light":     (230, 195, 85),
        "gold_shine":     (255, 235, 160),

        # Cape / cloth
        "cape_darkest":   (8,   5,   22),
        "cape_dark":      (22,  14,  52),
        "cape_mid":       (42,  28,  88),
        "cape_light":     (68,  48, 125),
        "cape_high":      (95,  72, 165),

        # Arcane energy – electric blue / purple
        "arc_darkest":    (15,  20,  80),
        "arc_dark":       (35,  55, 160),
        "arc_mid":        (75, 105, 220),
        "arc_light":      (130, 165, 255),
        "arc_bright":     (180, 210, 255),
        "arc_hot":        (220, 235, 255),
        "arc_white":      (245, 248, 255),

        # Purple magic
        "magic_darkest":  (25,   8,  55),
        "magic_dark":     (65,  20, 120),
        "magic_mid":      (115, 45, 185),
        "magic_light":    (165, 85, 225),
        "magic_bright":   (200, 140, 255),
        "magic_hot":      (235, 200, 255),

        # Face gem
        "gem_dark":       (20,  25, 100),
        "gem_mid":        (55,  75, 190),
        "gem_light":      (100, 135, 240),
        "gem_bright":     (160, 195, 255),
        "gem_hot":        (210, 230, 255),
        "gem_white":      (240, 248, 255),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (4,   3,   10),
        "white":          (255, 255, 255),

        # Spark / lightning
        "spark_dark":     (40,  60, 180),
        "spark_mid":      (90, 130, 240),
        "spark_light":    (160, 200, 255),
        "spark_hot":      (220, 240, 255),
    }


    def _clamp(color):
        """Clamp color channels, supports both RGB and RGBA."""
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_gravefang._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_gravefang.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_gravefang._clamp(color)
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
        color = _NS_gravefang._clamp(color)
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
        color = _NS_gravefang._clamp(color)
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
        color = _NS_gravefang._clamp(color)
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
    # Lightning / electrical arc drawing helpers
    # ---------------------------------------------------------------------------
    def _draw_lightning_bolt(surface, start, end, color_inner, color_outer,
                             segments=8, jitter=8, width_outer=3, width_inner=1):
        """Draw a jagged lightning bolt between two points."""
        sx, sy = start
        ex, ey = end
        points = [(sx, sy)]
        for i in range(1, segments):
            t = i / segments
            mx = sx + (ex - sx) * t + (hash((sx, sy, i, ex)) % (jitter * 2) - jitter)
            my = sy + (ey - sy) * t + (hash((sy, sx, i, ey)) % (jitter * 2) - jitter)
            points.append((int(mx), int(my)))
        points.append((ex, ey))

        for i in range(len(points) - 1):
            _NS_gravefang._aaline(surface, color_outer, points[i], points[i + 1], width_outer)
        for i in range(len(points) - 1):
            _NS_gravefang._aaline(surface, color_inner, points[i], points[i + 1], width_inner)


    def _draw_lightning_arc(surface, cx, cy, radius, phase, count=6,
                            color=None):
        """Draw arcing lightning around a circle."""
        if color is None:
            color = _NS_gravefang.PALETTE["arc_light"]
        for i in range(count):
            angle1 = phase + i * math.pi * 2 / count
            angle2 = angle1 + 0.4 + math.sin(phase * 3 + i) * 0.3
            x1 = cx + int(math.cos(angle1) * radius)
            y1 = cy + int(math.sin(angle1) * radius * 0.5)
            x2 = cx + int(math.cos(angle2) * (radius + 8))
            y2 = cy + int(math.sin(angle2) * (radius + 8) * 0.5)
            _NS_gravefang._draw_lightning_bolt(surface, (x1, y1), (x2, y2),
                                 _NS_gravefang.PALETTE["arc_bright"], color,
                                 segments=4, jitter=5, width_outer=2, width_inner=1)


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM
    # ---------------------------------------------------------------------------
    class ArcProjectile:
        """A lightning projectile that travels toward a target."""
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
            if len(self.trail) > 12:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            if not self.alive and self.age < 2:
                return
            # Trail
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(60 + i * 12)
                r = max(1, 6 - (len(self.trail) - i))
                _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_dark"], alpha), (tx, ty), r)
                _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_light"], alpha // 2), (tx, ty), r + 2)

            if self.alive:
                px, py = int(self.x), int(self.y)
                # Outer glow
                _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_dark"], 80), (px, py), 14)
                _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_mid"], 120), (px, py), 10)
                # Core
                _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["arc_light"], (px, py), 6)
                _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["arc_bright"], (px, py), 4)
                _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["arc_hot"], (px, py), 2)
                # Mini lightning
                for i in range(4):
                    angle = phase * 4 + i * math.pi / 2
                    ex = px + int(math.cos(angle) * 11)
                    ey = py + int(math.sin(angle) * 11)
                    _NS_gravefang._draw_lightning_bolt(surface, (px, py), (ex, ey),
                                         _NS_gravefang.PALETTE["arc_bright"], _NS_gravefang.PALETTE["arc_mid"],
                                         segments=3, jitter=4, width_outer=2, width_inner=1)


    # ---------------------------------------------------------------------------
    # State management helpers
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_morg_last_x"):
            boss._morg_last_x = boss.x
            boss._morg_last_y = boss.y
            return False
        dx = abs(boss.x - boss._morg_last_x)
        dy = abs(boss.y - boss._morg_last_y)
        boss._morg_last_x = boss.x
        boss._morg_last_y = boss.y
        return dx + dy > 0.3


    def _update_attack_anim(boss):
        """Track ranged attack animation timeline."""
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_morg_prev_timer", 0))
        active = bool(getattr(boss, "_morg_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._morg_attack_active = True
            boss._morg_attack_frame = 0
            active = True
        elif active:
            boss._morg_attack_frame = int(
                getattr(boss, "_morg_attack_frame", 0)) + 1
            if boss._morg_attack_frame > cooldown:
                boss._morg_attack_active = False
                boss._morg_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._morg_attack_active = False
            boss._morg_attack_frame = 0
            active = False

        boss._morg_prev_timer = timer
        boss._morg_attack_progress = (
            min(1.0, getattr(boss, "_morg_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_projectiles(boss, surface, phase):
        """Update and draw all active projectiles."""
        if not hasattr(boss, "_morg_projectiles"):
            boss._morg_projectiles = []
        for proj in boss._morg_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._morg_projectiles = [p for p in boss._morg_projectiles if p.alive or p.age < 8]


    def _spawn_projectile(boss, x, y):
        """Spawn a new arc projectile toward target."""
        if not hasattr(boss, "_morg_projectiles"):
            boss._morg_projectiles = []
        tx, ty = _NS_gravefang._target_position(boss, x, y)
        sx = x + 22 * getattr(boss, "direction", 1)
        sy = y - 12
        boss._morg_projectiles.append(_NS_gravefang.ArcProjectile(sx, sy, tx, ty, speed=5.5))


    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_morgath(surface, boss, x, y):
        """Entry point for Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_gravefang._detect_moving(boss)
        _NS_gravefang._update_attack_anim(boss)

        attacking = (
            getattr(boss, "_morg_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 50) - 15
        )

        # ---------- Background layers ----------
        _NS_gravefang._draw_arcane_aura(surface, x, y, pulse)
        _NS_gravefang._draw_ground_runes(surface, x, y + 38, pulse, active_skill)

        # ---------- Skill ground effects ----------
        if active_skill == "q":
            _NS_gravefang._draw_spark_wraith_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_gravefang._draw_magnetic_field(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_gravefang._draw_tempest_double_ground(surface, boss, x, y, skill_timer, pulse)

        # ---------- Character body ----------
        if attacking:
            _NS_gravefang._draw_morgath_attack(surface, boss, x, y)
        elif moving:
            _NS_gravefang._draw_morgath_walk(surface, boss, x, y)
        else:
            _NS_gravefang._draw_morgath_idle(surface, boss, x, y)

        # ---------- Projectiles ----------
        _NS_gravefang._manage_projectiles(boss, surface, pulse)

        # ---------- Skill foreground effects ----------
        if active_skill == "q":
            _NS_gravefang._draw_spark_wraith(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_gravefang._draw_flux(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_gravefang._draw_magnetic_field_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_gravefang._draw_tempest_double(surface, boss, x, y, skill_timer, pulse)


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_morgath_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.8) * 2)
        _NS_gravefang._draw_shadow(surface, x, y + 48)
        _NS_gravefang._draw_floating_wisps(surface, x, y + 35, boss.pulse)
        _NS_gravefang._draw_morgath_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")


    def _draw_morgath_walk(surface, boss, x, y):
        phase = boss.pulse * 2.2
        bob = int(abs(math.sin(phase * 1.3)) * 3)
        sway = int(math.sin(phase) * 2)
        _NS_gravefang._draw_shadow(surface, x + sway, y + 48)
        _NS_gravefang._draw_floating_wisps(surface, x + sway, y + 35, phase, trail=True,
                             facing=boss.direction)
        _NS_gravefang._draw_morgath_body(surface, x + sway, y - bob, boss.direction, phase, "walk")


    def _draw_morgath_attack(surface, boss, x, y):
        progress = getattr(boss, "_morg_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        # Spawn projectile at the right moment
        if 0.28 < progress < 0.35 and not getattr(boss, "_morg_proj_spawned", False):
            _NS_gravefang._spawn_projectile(boss, x, y)
            boss._morg_proj_spawned = True
        if progress < 0.1 or progress > 0.9:
            boss._morg_proj_spawned = False

        recoil = int(math.sin(progress * math.pi) * 3) * -boss.direction
        _NS_gravefang._draw_shadow(surface, x + recoil, y + 48)
        _NS_gravefang._draw_floating_wisps(surface, x + recoil, y + 35, boss.pulse, intense=True)
        _NS_gravefang._draw_morgath_body(surface, x + recoil, y, boss.direction, boss.pulse,
                           "attack", progress)
        _NS_gravefang._draw_cast_flash(surface, x + recoil, y, boss.direction, progress)


    # ===================================================================
    # BODY RENDERING – HD detailed
    # ===================================================================
    def _draw_morgath_body(surface, cx, cy, facing, phase, action,
                           attack_progress=0):
        sway = int(math.sin(phase * 0.6) * (2 if action != "idle" else 1))

        # Cape (drawn behind body)
        _NS_gravefang._draw_cape(surface, cx, cy, facing, phase, action)

        # Lower robes / floating lower body
        _NS_gravefang._draw_lower_robes(surface, cx, cy + 5, phase, sway)

        # Torso armor
        _NS_gravefang._draw_torso(surface, cx, cy - 8, phase)

        # Shoulder pauldrons
        _NS_gravefang._draw_pauldrons(surface, cx, cy - 16, phase)

        # Arms
        if action == "attack":
            _NS_gravefang._draw_casting_arms(surface, cx, cy - 8, facing, phase, attack_progress)
        else:
            _NS_gravefang._draw_idle_arms(surface, cx, cy - 8, facing, phase)

        # Head
        _NS_gravefang._draw_head(surface, cx, cy - 30, phase)

        # Floating arcane particles around body
        _NS_gravefang._draw_body_particles(surface, cx, cy, phase)


    def _draw_cape(surface, cx, cy, facing, phase, action):
        """Flowing cape behind the character."""
        wave = math.sin(phase * 0.8) * 3
        wave2 = math.sin(phase * 1.2 + 0.5) * 2

        # Cape shape - multiple layers for depth
        cape_points_outer = [
            (cx - 14, cy - 14),
            (cx - 18, cy + 5),
            (cx - 24 - int(wave), cy + 30),
            (cx - 18 - int(wave2), cy + 42),
            (cx - 5, cy + 45 + int(abs(wave))),
            (cx + 5, cy + 45 + int(abs(wave))),
            (cx + 18 + int(wave2), cy + 42),
            (cx + 24 + int(wave), cy + 30),
            (cx + 18, cy + 5),
            (cx + 14, cy - 14),
        ]
        _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["cape_darkest"], cape_points_outer)

        cape_mid = [
            (cx - 12, cy - 12),
            (cx - 16, cy + 5),
            (cx - 20 - int(wave * 0.7), cy + 28),
            (cx - 14 - int(wave2 * 0.7), cy + 38),
            (cx - 3, cy + 40),
            (cx + 3, cy + 40),
            (cx + 14 + int(wave2 * 0.7), cy + 38),
            (cx + 20 + int(wave * 0.7), cy + 28),
            (cx + 16, cy + 5),
            (cx + 12, cy - 12),
        ]
        _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["cape_dark"], cape_mid)

        cape_inner = [
            (cx - 9, cy - 8),
            (cx - 12, cy + 5),
            (cx - 15 - int(wave * 0.4), cy + 22),
            (cx - 8, cy + 32),
            (cx, cy + 34),
            (cx + 8, cy + 32),
            (cx + 15 + int(wave * 0.4), cy + 22),
            (cx + 12, cy + 5),
            (cx + 9, cy - 8),
        ]
        _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["cape_mid"], cape_inner)

        # Cape edge lightning streaks
        for i in range(4):
            t = (phase * 0.3 + i * 0.25) % 1.0
            idx = int(t * (len(cape_points_outer) - 1))
            px, py = cape_points_outer[idx]
            _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_mid"], 100), (px, py), 3)


    def _draw_lower_robes(surface, cx, cy, phase, sway):
        """Floating lower body with tattered robes."""
        # Outer robe shape
        robe_outer = [
            (cx - 18, cy),
            (cx + 18, cy),
            (cx + 22 + sway, cy + 12),
            (cx + 16, cy + 22),
            (cx + 8, cy + 28),
            (cx + 3, cy + 30),
            (cx - 3, cy + 30),
            (cx - 8, cy + 28),
            (cx - 16, cy + 22),
            (cx - 22 - sway, cy + 12),
        ]
        _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["shadow_deep"], [(p[0] + 2, p[1] + 2) for p in robe_outer])
        _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["armor_darkest"], robe_outer)

        robe_mid = [
            (cx - 15, cy + 2),
            (cx + 15, cy + 2),
            (cx + 18 + sway, cy + 12),
            (cx + 12, cy + 20),
            (cx + 5, cy + 25),
            (cx - 5, cy + 25),
            (cx - 12, cy + 20),
            (cx - 18 - sway, cy + 12),
        ]
        _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["armor_dark"], robe_mid)

        robe_inner = [
            (cx - 11, cy + 4),
            (cx + 11, cy + 4),
            (cx + 14 + sway, cy + 12),
            (cx + 8, cy + 18),
            (cx - 8, cy + 18),
            (cx - 14 - sway, cy + 12),
        ]
        _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["armor_mid"], robe_inner)

        # Tattered bottom edges
        for i in range(7):
            tx = cx - 15 + i * 5
            ty = cy + 26 + int(math.sin(phase * 1.5 + i) * 3)
            _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["cape_dark"], [
                (tx - 3, cy + 24), (tx + 3, cy + 24),
                (tx + 1, ty + 4), (tx - 1, ty + 4),
            ])

        # Gold belt line
        _NS_gravefang._rect(surface, _NS_gravefang.PALETTE["gold_dark"], (cx - 19, cy - 1, 38, 5))
        _NS_gravefang._rect(surface, _NS_gravefang.PALETTE["gold_mid"], (cx - 17, cy, 34, 3))
        _NS_gravefang._rect(surface, _NS_gravefang.PALETTE["gold_light"], (cx - 14, cy + 1, 28, 1))

        # Belt buckle gem
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gem_dark"], (cx, cy + 1), 4)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gem_mid"], (cx, cy + 1), 3)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gem_light"], (cx - 1, cy), 2)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gem_bright"], (cx - 1, cy), 1)


    def _draw_torso(surface, cx, cy, phase):
        """Main chest armor with gold trim."""
        # Shadow
        _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["shadow_deep"], [
            (cx - 14 + 2, cy - 10 + 2), (cx + 14 + 2, cy - 10 + 2),
            (cx + 12 + 2, cy + 14 + 2), (cx + 5 + 2, cy + 19 + 2),
            (cx - 5 + 2, cy + 19 + 2), (cx - 12 + 2, cy + 14 + 2),
        ])

        # Main chest plate
        chest = [
            (cx - 14, cy - 10), (cx + 14, cy - 10),
            (cx + 12, cy + 14), (cx + 5, cy + 19),
            (cx - 5, cy + 19), (cx - 12, cy + 14),
        ]
        _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["armor_darkest"], chest)
        _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["armor_dark"], [
            (cx - 12, cy - 8), (cx + 12, cy - 8),
            (cx + 10, cy + 12), (cx + 4, cy + 16),
            (cx - 4, cy + 16), (cx - 10, cy + 12),
        ])
        _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["armor_mid"], [
            (cx - 9, cy - 5), (cx + 9, cy - 5),
            (cx + 7, cy + 9), (cx + 3, cy + 13),
            (cx - 3, cy + 13), (cx - 7, cy + 9),
        ])

        # Gold chest accent lines
        _NS_gravefang._aaline(surface, _NS_gravefang.PALETTE["gold_dark"], (cx - 12, cy - 8), (cx, cy + 14), 2)
        _NS_gravefang._aaline(surface, _NS_gravefang.PALETTE["gold_dark"], (cx + 12, cy - 8), (cx, cy + 14), 2)
        _NS_gravefang._aaline(surface, _NS_gravefang.PALETTE["gold_mid"], (cx - 11, cy - 7), (cx, cy + 13), 1)
        _NS_gravefang._aaline(surface, _NS_gravefang.PALETTE["gold_mid"], (cx + 11, cy - 7), (cx, cy + 13), 1)

        # Center gem
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["arc_darkest"], (cx, cy + 2), 5)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["arc_dark"], (cx, cy + 2), 4)
        pulse_r = 3 + int(math.sin(phase * 1.5) * 1)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["arc_mid"], (cx, cy + 1), pulse_r)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["arc_light"], (cx, cy + 1), 2)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["arc_hot"], (cx, cy + 1), 1)

        # Seam details
        for xoff, yoff in [(-8, 0), (6, 1), (-6, 8), (5, 9)]:
            pygame.draw.line(surface, _NS_gravefang.PALETTE["armor_darkest"],
                             (cx + xoff, cy + yoff),
                             (cx + xoff + 3, cy + yoff + 3), 1)

        # Gold trim around edges
        for i in range(len(chest)):
            p1 = chest[i]
            p2 = chest[(i + 1) % len(chest)]
            _NS_gravefang._aaline(surface, _NS_gravefang.PALETTE["gold_dark"], p1, p2, 2)


    def _draw_pauldrons(surface, cx, cy, phase):
        """Shoulder pauldrons with gold trim."""
        for side in (-1, 1):
            sx = cx + side * 16
            # Shadow
            _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["shadow_deep"], (sx + 2, cy + 2), 11)
            # Main pauldron
            _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["armor_darkest"], (sx, cy), 10)
            _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["armor_dark"], (sx - side, cy - 1), 8)
            _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["armor_mid"], (sx - side * 2, cy - 2), 6)
            _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["armor_light"], (sx - side * 3, cy - 4), 3)

            # Gold trim ring
            _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gold_dark"], (sx, cy), 10, 2)
            _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gold_mid"], (sx, cy), 9, 1)

            # Pauldron gem
            _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gem_dark"], (sx, cy - 2), 3)
            _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gem_mid"], (sx, cy - 2), 2)
            p = math.sin(phase * 1.2 + side) * 0.5 + 0.5
            _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gem_light"], (sx, cy - 2), max(1, int(2 * p)))

            # Spike on top
            _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["armor_darkest"], [
                (sx - 2, cy - 8),
                (sx + 2, cy - 8),
                (sx + side * 2, cy - 16),
            ])
            _NS_gravefang._aaline(surface, _NS_gravefang.PALETTE["gold_mid"],
                    (sx, cy - 8), (sx + side * 2, cy - 16), 1)


    def _draw_idle_arms(surface, cx, cy, facing, phase):
        """Arms in resting position with arcane energy in hands."""
        sway = math.sin(phase * 0.7) * 2
        for side in (-1, 1):
            shoulder_x = cx + side * 14
            shoulder_y = cy + 2
            elbow_x = shoulder_x + side * 8
            elbow_y = cy + 12 + int(sway)
            hand_x = elbow_x + side * 4
            hand_y = elbow_y + 10

            _NS_gravefang._draw_arm_segment(surface, shoulder_x, shoulder_y,
                              elbow_x, elbow_y, phase)
            _NS_gravefang._draw_arm_segment(surface, elbow_x, elbow_y,
                              hand_x, hand_y, phase)
            _NS_gravefang._draw_hand_glow(surface, hand_x, hand_y, phase + side, 5)


    def _draw_casting_arms(surface, cx, cy, facing, phase, progress):
        """Arms in casting pose – one arm raised forward shooting."""
        sway = math.sin(phase * 0.7) * 1

        # Back arm (away from facing)
        back_side = -facing
        bs_x = cx + back_side * 14
        bs_y = cy + 2
        be_x = bs_x + back_side * 8
        be_y = cy + 10
        bh_x = be_x + back_side * 5
        bh_y = be_y + 8
        _NS_gravefang._draw_arm_segment(surface, bs_x, bs_y, be_x, be_y, phase)
        _NS_gravefang._draw_arm_segment(surface, be_x, be_y, bh_x, bh_y, phase)
        _NS_gravefang._draw_hand_glow(surface, bh_x, bh_y, phase, 4)

        # Front arm (casting arm) – extends forward
        fs_x = cx + facing * 14
        fs_y = cy + 2

        # Wind up then thrust forward
        if progress < 0.3:
            t = progress / 0.3
            arm_angle = -0.8 * t
        elif progress < 0.5:
            t = (progress - 0.3) / 0.2
            arm_angle = -0.8 + 1.6 * t
        else:
            t = (progress - 0.5) / 0.5
            arm_angle = 0.8 - 0.5 * t

        fe_x = fs_x + int(math.cos(arm_angle) * 14) * facing
        fe_y = fs_y + int(math.sin(arm_angle) * 14) - 4
        fh_x = fe_x + int(math.cos(arm_angle) * 12) * facing
        fh_y = fe_y + int(math.sin(arm_angle) * 12)

        _NS_gravefang._draw_arm_segment(surface, fs_x, fs_y, fe_x, fe_y, phase)
        _NS_gravefang._draw_arm_segment(surface, fe_x, fe_y, fh_x, fh_y, phase)

        # Larger glow on casting hand
        glow_size = 6 + int(math.sin(progress * math.pi) * 5)
        _NS_gravefang._draw_hand_glow(surface, fh_x, fh_y, phase, glow_size)

        # Arc energy from hand during cast
        if 0.2 < progress < 0.6:
            intensity = math.sin((progress - 0.2) / 0.4 * math.pi)
            for i in range(3):
                angle = phase * 5 + i * math.pi * 2 / 3
                ex = fh_x + int(math.cos(angle) * 15 * intensity) * facing
                ey = fh_y + int(math.sin(angle) * 12 * intensity)
                _NS_gravefang._draw_lightning_bolt(surface, (fh_x, fh_y), (ex, ey),
                                     _NS_gravefang.PALETTE["arc_bright"], _NS_gravefang.PALETTE["arc_mid"],
                                     segments=3, jitter=4, width_outer=2, width_inner=1)


    def _draw_arm_segment(surface, x1, y1, x2, y2, phase):
        """Draw a single arm segment with armor detail."""
        _NS_gravefang._aaline(surface, _NS_gravefang.PALETTE["shadow_deep"], (x1 + 2, y1 + 2), (x2 + 2, y2 + 2), 8)
        _NS_gravefang._aaline(surface, _NS_gravefang.PALETTE["armor_darkest"], (x1, y1), (x2, y2), 7)
        _NS_gravefang._aaline(surface, _NS_gravefang.PALETTE["armor_dark"], (x1, y1), (x2, y2), 5)
        _NS_gravefang._aaline(surface, _NS_gravefang.PALETTE["armor_mid"], (x1, y1), (x2, y2), 3)
        _NS_gravefang._aaline(surface, _NS_gravefang.PALETTE["armor_light"], (x1, y1 - 1), (x2, y2 - 1), 1)
        # Gold joint ring
        mx, my = (x1 + x2) // 2, (y1 + y2) // 2
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gold_dark"], (mx, my), 4)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gold_mid"], (mx, my), 3)


    def _draw_hand_glow(surface, x, y, phase, size=5):
        """Draw glowing arcane energy in hand."""
        pulse = math.sin(phase * 2.0) * 0.3 + 0.7
        s = int(size * pulse)
        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_dark"], 80), (x, y), s + 6)
        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_mid"], 130), (x, y), s + 3)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["arc_light"], (x, y), s)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["arc_bright"], (x, y), max(1, s - 2))
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["arc_hot"], (x, y), max(1, s - 4))

        # Tiny sparks
        for i in range(3):
            angle = phase * 3 + i * math.pi * 2 / 3
            sx = x + int(math.cos(angle) * (s + 4))
            sy = y + int(math.sin(angle) * (s + 4))
            _NS_gravefang._rect(surface, _NS_gravefang.PALETTE["arc_bright"], (sx, sy, 2, 2))


    def _draw_head(surface, cx, cy, phase):
        """Ornate helm with large central gem - Arc Warden style."""
        # Shadow
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["shadow_deep"], (cx + 2, cy + 2), 13)

        # Helm base
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["armor_darkest"], (cx, cy), 12)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["armor_dark"], (cx - 1, cy - 1), 10)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["armor_mid"], (cx - 2, cy - 2), 7)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["armor_light"], (cx - 3, cy - 4), 4)

        # Gold helm trim
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gold_dark"], (cx, cy), 12, 2)

        # Face plate – darker recessed area
        _NS_gravefang._rect(surface, _NS_gravefang.PALETTE["armor_darkest"], (cx - 8, cy - 4, 16, 10),
              border_radius=3)
        _NS_gravefang._rect(surface, _NS_gravefang.PALETTE["shadow_deep"], (cx - 6, cy - 2, 12, 7),
              border_radius=2)

        # Central gem (large, Arc Warden style)
        gem_pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        gem_r = int(6 * gem_pulse)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gem_dark"], (cx, cy), gem_r + 2)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gem_mid"], (cx, cy), gem_r)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gem_light"], (cx - 1, cy - 1), max(1, gem_r - 2))
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gem_bright"], (cx - 1, cy - 2), max(1, gem_r - 4))
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gem_hot"], (cx - 1, cy - 2), max(1, gem_r - 5))

        # Gem glow effect
        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["gem_light"], int(60 * gem_pulse)),
                  (cx, cy), gem_r + 6)

        # Gold frame around gem
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gold_mid"], (cx, cy), gem_r + 2, 2)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gold_light"], (cx, cy), gem_r + 1, 1)

        # Helm horns / crown
        for side in (-1, 1):
            # Main horn
            _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["armor_darkest"], [
                (cx + side * 8, cy - 6),
                (cx + side * 14, cy - 20),
                (cx + side * 10, cy - 5),
            ])
            _NS_gravefang._aaline(surface, _NS_gravefang.PALETTE["gold_mid"],
                    (cx + side * 9, cy - 6),
                    (cx + side * 14, cy - 20), 1)
            # Gold tip
            _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gold_light"],
                      (cx + side * 14, cy - 20), 2)

            # Secondary smaller horn
            _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["armor_dark"], [
                (cx + side * 5, cy - 9),
                (cx + side * 8, cy - 16),
                (cx + side * 6, cy - 8),
            ])

        # Chin guard
        _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["armor_darkest"], [
            (cx - 6, cy + 6),
            (cx + 6, cy + 6),
            (cx + 3, cy + 12),
            (cx, cy + 14),
            (cx - 3, cy + 12),
        ])
        _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["armor_dark"], [
            (cx - 4, cy + 7),
            (cx + 4, cy + 7),
            (cx + 2, cy + 11),
            (cx, cy + 12),
            (cx - 2, cy + 11),
        ])


    def _draw_body_particles(surface, cx, cy, phase):
        """Floating arcane particles around body."""
        for i in range(8):
            angle = phase * 0.4 + i * math.pi / 4
            radius = 25 + int(math.sin(phase * 0.7 + i) * 8)
            px = cx + int(math.cos(angle) * radius)
            py = cy - 5 + int(math.sin(angle) * radius * 0.5)
            alpha = int(120 + math.sin(phase + i * 0.7) * 60)
            _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_mid"], alpha), (px, py), 2)
            _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_bright"], alpha // 2), (px, py), 1)


    # ===================================================================
    # FLOATING EFFECTS (replaces legs)
    # ===================================================================
    def _draw_floating_wisps(surface, cx, cy, phase, trail=False,
                             facing=1, intense=False):
        """Arcane mist and energy wisps beneath floating Morgath."""
        strength = 1.5 if intense else 1.0

        # Misty base
        mist = pygame.Surface((120, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        for radius in range(32, 3, -4):
            alpha = int((32 - radius) * 2.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_gravefang.PALETTE["arc_dark"], min(255, alpha)),
                    (60 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 60, cy - 10))

        # Rising energy wisps
        for i, offset in enumerate((-20, -8, 8, 20)):
            t = (phase * 0.5 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 24)
            alpha = max(0, min(255, int(200 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_dark"], alpha), (sx, sy), 5)
            _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_mid"], alpha), (sx, sy - 2), 3)
            _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_light"], min(255, alpha)),
                      (sx, sy - 3), 1)

        # Small orbiting energy balls
        for i in range(5):
            angle = phase * 0.9 + i * math.pi * 2 / 5
            r = 20 + int(math.sin(phase + i * 1.3) * 5)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 7)
            _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["arc_mid"], (sx, sy), 3)
            _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["arc_light"], (sx, sy), 2)
            _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["arc_hot"], (sx, sy), 1)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 11 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 120 - i * 22)
                _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_mid"], alpha),
                          (sx, sy), max(2, 5 - i))


    def _draw_shadow(surface, x, y):
        """Ground shadow beneath floating entity."""
        shadow = pygame.Surface((100, 20), pygame.SRCALPHA)
        for radius in range(10, 0, -1):
            alpha = max(0, (10 - radius) * 16)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 10 - radius, 80 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (*_NS_gravefang.PALETTE["arc_dark"], 40), (8, 4, 84, 10))
        surface.blit(shadow, (x - 50, y - 10))


    def _draw_arcane_aura(surface, x, y, phase):
        """Large background aura."""
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        aura = pygame.Surface((180, 160), pygame.SRCALPHA)
        for radius in range(72, 5, -4):
            alpha = int((72 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_gravefang._aacircle(aura, (*_NS_gravefang.PALETTE["magic_darkest"], min(255, alpha)),
                          (90, 80), radius)
        surface.blit(aura, (x - 90, y - 80))


    def _draw_ground_runes(surface, x, y, phase, skill):
        """Arcane circle on the ground."""
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((130, 44), pygame.SRCALPHA)

        # Outer ring
        pygame.draw.ellipse(ring, (*_NS_gravefang.PALETTE["arc_dark"], 140),
                            (5, 10, 120, 24), 3)
        # Inner ring
        pygame.draw.ellipse(ring, (*_NS_gravefang.PALETTE["arc_mid"], 170),
                            (20, 14, 90, 16), 2)

        # Rune marks
        for i in range(10):
            angle = phase * 0.2 + i * math.pi / 5
            x1 = 65 + int(math.cos(angle) * 30)
            y1 = 22 + int(math.sin(angle) * 6)
            x2 = 65 + int(math.cos(angle) * 55)
            y2 = 22 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_gravefang.PALETTE["arc_light"], 160),
                             (x1, y1), (x2, y2), 1)

        # Pulsing inner glow when skill active
        if skill:
            pygame.draw.ellipse(ring, (*_NS_gravefang.PALETTE["arc_bright"], int(70 * pulse)),
                                (15, 8, 100, 28), 1)

        surface.blit(ring, (x - 65, y - 22))


    def _draw_cast_flash(surface, x, y, facing, progress):
        """Flash effect during ranged attack."""
        if progress < 0.2 or progress > 0.65:
            return
        t = (progress - 0.2) / 0.45
        intensity = math.sin(t * math.pi)

        flash_x = x + 22 * facing
        flash_y = y - 12

        alpha = int(180 * intensity)
        radius = int(8 + intensity * 18)

        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_mid"], alpha // 2), (flash_x, flash_y), radius + 8)
        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_light"], alpha), (flash_x, flash_y), radius)
        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_bright"], alpha), (flash_x, flash_y), radius // 2)
        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_hot"], min(255, alpha)),
                  (flash_x, flash_y), max(1, radius // 4))

        # Lightning sparks from flash
        for i in range(5):
            angle = progress * 8 + i * math.pi * 2 / 5
            ex = flash_x + int(math.cos(angle) * radius * 1.3)
            ey = flash_y + int(math.sin(angle) * radius * 1.3)
            _NS_gravefang._draw_lightning_bolt(surface, (flash_x, flash_y), (ex, ey),
                                 (*_NS_gravefang.PALETTE["arc_bright"], alpha),
                                 (*_NS_gravefang.PALETTE["arc_mid"], alpha // 2),
                                 segments=3, jitter=5, width_outer=2, width_inner=1)


    # ===================================================================
    # SKILL Q: SPARK WRAITH
    # ===================================================================
    def _draw_spark_wraith_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_gravefang._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 80))
        # Ground warning circle
        radius = int(20 + progress * 35)
        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["magic_dark"], 100), (tx, ty), radius, 2)
        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["magic_mid"], 80), (tx, ty), radius + 5, 1)


    def _draw_spark_wraith(surface, boss, x, y, timer, phase):
        tx, ty = _NS_gravefang._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 80))

        # Wraith forming at target location
        if progress < 0.4:
            # Forming phase
            form = progress / 0.4
            alpha = int(200 * form)
            radius = int(18 * form)
        else:
            alpha = 200
            radius = 18 + int(math.sin(phase * 3) * 4)

        # Wraith body - ghostly sphere
        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["magic_dark"], alpha // 2), (tx, ty), radius + 8)
        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["magic_mid"], alpha), (tx, ty), radius)
        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["magic_light"], alpha), (tx, ty), max(1, radius - 5))
        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["magic_bright"], min(255, alpha)),
                  (tx, ty), max(1, radius - 10))

        # Lightning arcs around wraith
        _NS_gravefang._draw_lightning_arc(surface, tx, ty, radius + 5, phase, count=5,
                            color=_NS_gravefang.PALETTE["arc_light"])

        # Sparks flying outward
        for i in range(6):
            angle = phase * 2 + i * math.pi / 3
            dist = radius + 10 + int(math.sin(phase * 3 + i) * 8)
            sx = tx + int(math.cos(angle) * dist)
            sy = ty + int(math.sin(angle) * dist * 0.6)
            _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["spark_light"], 180), (sx, sy), 2)
            _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["spark_hot"], 220), (sx, sy), 1)


    # ===================================================================
    # SKILL W: FLUX
    # ===================================================================
    def _draw_flux(surface, boss, x, y, timer, phase):
        tx, ty = _NS_gravefang._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 70))

        # Flux beam connecting Morgath to target
        start_x = x + 20 * boss.direction
        start_y = y - 10

        # Multiple lightning beams
        for i in range(3):
            offset = (i - 1) * 3
            _NS_gravefang._draw_lightning_bolt(
                surface,
                (start_x, start_y + offset),
                (tx, ty + offset),
                _NS_gravefang.PALETTE["arc_bright"],
                _NS_gravefang.PALETTE["arc_mid"],
                segments=12,
                jitter=12,
                width_outer=3,
                width_inner=1
            )

        # Energy nodes along the beam
        for i in range(8):
            t = (progress + i * 0.12) % 1.0
            px = int(start_x + (tx - start_x) * t)
            py = int(start_y + (ty - start_y) * t)
            _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_light"], 200), (px, py), 4)
            _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_hot"], 220), (px, py), 2)

        # Impact at target
        impact_pulse = math.sin(phase * 4) * 0.3 + 0.7
        impact_r = int(15 * impact_pulse)
        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_mid"], 150), (tx, ty), impact_r + 5)
        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_light"], 200), (tx, ty), impact_r)
        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_hot"], 230), (tx, ty), max(1, impact_r - 5))

        # Slow effect visual - pulsing rings at target
        for i in range(3):
            ring_r = int(20 + i * 12 + math.sin(phase * 2 + i) * 5)
            _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["magic_mid"], 80), (tx, ty), ring_r, 2)


    # ===================================================================
    # SKILL E: MAGNETIC FIELD
    # ===================================================================
    def _draw_magnetic_field(surface, boss, x, y, timer, phase):
        """Ground layer of magnetic field dome."""
        progress = max(0.0, min(1.0, 1 - timer / 90))
        radius = int(45 + progress * 30)
        pulse = math.sin(phase * 1.5) * 0.2 + 0.8

        # Ground ellipse
        _NS_gravefang._ellipse(surface, (*_NS_gravefang.PALETTE["arc_dark"], int(80 * pulse)),
                 (x - radius, y + 30 - radius // 4, radius * 2, radius // 2), 2)
        _NS_gravefang._ellipse(surface, (*_NS_gravefang.PALETTE["arc_mid"], int(60 * pulse)),
                 (x - radius + 5, y + 32 - radius // 4,
                  radius * 2 - 10, radius // 2 - 4), 1)


    def _draw_magnetic_field_foreground(surface, boss, x, y, timer, phase):
        """Dome and lightning of magnetic field."""
        progress = max(0.0, min(1.0, 1 - timer / 90))
        radius = int(45 + progress * 30)
        pulse = math.sin(phase * 1.5) * 0.2 + 0.8

        # Dome surface (semi-transparent)
        dome = pygame.Surface((radius * 2 + 20, radius + 40), pygame.SRCALPHA)
        dome_cx = radius + 10
        dome_cy = radius + 20

        # Draw dome arcs
        for i in range(8):
            angle1 = math.pi + i * math.pi / 8
            angle2 = angle1 + math.pi / 8
            x1 = dome_cx + int(math.cos(angle1) * radius)
            y1 = dome_cy + int(math.sin(angle1) * radius * 0.7)
            x2 = dome_cx + int(math.cos(angle2) * radius)
            y2 = dome_cy + int(math.sin(angle2) * radius * 0.7)
            alpha = int(120 * pulse)
            pygame.draw.line(dome, (*_NS_gravefang.PALETTE["arc_mid"], alpha),
                             (x1, y1), (x2, y2), 2)

        # Lightning crawling on dome surface
        for i in range(6):
            angle = phase * 1.2 + i * math.pi / 3
            lx1 = dome_cx + int(math.cos(angle) * radius * 0.8)
            ly1 = dome_cy + int(math.sin(angle) * radius * 0.5)
            lx2 = dome_cx + int(math.cos(angle + 0.5) * radius)
            ly2 = dome_cy + int(math.sin(angle + 0.5) * radius * 0.6)
            _NS_gravefang._draw_lightning_bolt(dome, (lx1, ly1), (lx2, ly2),
                                 (*_NS_gravefang.PALETTE["arc_bright"], 180),
                                 (*_NS_gravefang.PALETTE["arc_mid"], 120),
                                 segments=4, jitter=6, width_outer=2, width_inner=1)

        # Bright orbs on dome
        for i in range(4):
            angle = phase * 0.8 + i * math.pi / 2
            ox = dome_cx + int(math.cos(angle) * radius * 0.9)
            oy = dome_cy + int(math.sin(angle) * radius * 0.55)
            pygame.draw.circle(dome, (*_NS_gravefang.PALETTE["arc_light"], 200), (ox, oy), 5)
            pygame.draw.circle(dome, (*_NS_gravefang.PALETTE["arc_hot"], 230), (ox, oy), 3)
            pygame.draw.circle(dome, (*_NS_gravefang.PALETTE["arc_white"], 250), (ox, oy), 1)

        surface.blit(dome, (x - dome_cx, y - 20 - dome_cy + radius))


    # ===================================================================
    # SKILL R: TEMPEST DOUBLE
    # ===================================================================
    def _draw_tempest_double_ground(surface, boss, x, y, timer, phase):
        """Ground effects for summoning."""
        progress = max(0.0, min(1.0, 1 - timer / 100))
        # Summoning circle
        radius = int(30 + progress * 20)
        sx = x + 50 * boss.direction
        sy = y + 35

        pulse = math.sin(phase * 2) * 0.3 + 0.7
        _NS_gravefang._ellipse(surface, (*_NS_gravefang.PALETTE["magic_mid"], int(120 * pulse)),
                 (sx - radius, sy - radius // 4, radius * 2, radius // 2), 2)
        _NS_gravefang._ellipse(surface, (*_NS_gravefang.PALETTE["arc_mid"], int(100 * pulse)),
                 (sx - radius + 5, sy - radius // 4 + 2,
                  radius * 2 - 10, radius // 2 - 4), 1)

        # Rune marks in circle
        for i in range(6):
            angle = phase * 0.3 + i * math.pi / 3
            rx = sx + int(math.cos(angle) * (radius - 5))
            ry = sy + int(math.sin(angle) * (radius // 4 - 2))
            _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_light"], int(150 * pulse)),
                      (rx, ry), 3)


    def _draw_tempest_double(surface, boss, x, y, timer, phase):
        """Draw the tempest double forming/formed."""
        progress = max(0.0, min(1.0, 1 - timer / 100))
        sx = x + 50 * boss.direction
        sy = y

        if progress < 0.5:
            # Forming phase - ghostly silhouette rising
            form = progress / 0.5
            alpha = int(180 * form)

            # Rising energy pillar
            pillar_h = int(60 * form)
            for i in range(pillar_h):
                t = i / max(1, pillar_h)
                pw = int(15 * (1 - t * 0.3))
                pa = int(alpha * (1 - t * 0.5))
                _NS_gravefang._rect(surface, (*_NS_gravefang.PALETTE["magic_mid"], pa),
                      (sx - pw, sy + 20 - i, pw * 2, 2))

            # Lightning around pillar
            for i in range(4):
                angle = phase * 3 + i * math.pi / 2
                lx = sx + int(math.cos(angle) * 20)
                ly = sy + 20 - int(pillar_h * 0.5) + int(math.sin(angle) * pillar_h * 0.3)
                _NS_gravefang._draw_lightning_bolt(surface, (sx, sy + 20 - pillar_h // 2),
                                     (lx, ly),
                                     (*_NS_gravefang.PALETTE["arc_bright"], alpha),
                                     (*_NS_gravefang.PALETTE["arc_mid"], alpha // 2),
                                     segments=4, jitter=6)
        else:
            # Formed - draw ghostly copy of Morgath
            form = (progress - 0.5) / 0.5
            alpha = int(150 + form * 50)
            ghost = pygame.Surface((100, 120), pygame.SRCALPHA)
            # Draw a simplified ghostly version
            gcx, gcy = 50, 60
            # Body shape
            pygame.draw.circle(ghost, (*_NS_gravefang.PALETTE["magic_mid"], alpha), (gcx, gcy - 15), 10)
            pygame.draw.circle(ghost, (*_NS_gravefang.PALETTE["magic_light"], alpha // 2),
                               (gcx, gcy - 15), 7)
            # Torso
            _NS_gravefang._poly(ghost, (*_NS_gravefang.PALETTE["magic_dark"], alpha), [
                (gcx - 12, gcy - 8), (gcx + 12, gcy - 8),
                (gcx + 10, gcy + 12), (gcx - 10, gcy + 12),
            ])
            # Gem eye
            pygame.draw.circle(ghost, (*_NS_gravefang.PALETTE["gem_light"], min(255, alpha)),
                               (gcx, gcy - 15), 4)
            pygame.draw.circle(ghost, (*_NS_gravefang.PALETTE["gem_hot"], min(255, alpha)),
                               (gcx, gcy - 16), 2)
            # Cape wisps
            for i in range(3):
                wave = math.sin(phase + i) * 4
                _NS_gravefang._poly(ghost, (*_NS_gravefang.PALETTE["magic_dark"], alpha // 2), [
                    (gcx - 8 + i * 8, gcy + 10),
                    (gcx - 10 + i * 8 + int(wave), gcy + 30),
                    (gcx - 4 + i * 8 + int(wave * 0.5), gcy + 28),
                ])
            # Aura
            pygame.draw.circle(ghost, (*_NS_gravefang.PALETTE["arc_mid"], alpha // 3),
                               (gcx, gcy), 35, 2)

            surface.blit(ghost, (sx - 50, sy - 60))

            # Lightning connection between original and double
            _NS_gravefang._draw_lightning_bolt(surface, (x, y - 10), (sx, sy - 10),
                                 _NS_gravefang.PALETTE["arc_light"], _NS_gravefang.PALETTE["arc_mid"],
                                 segments=8, jitter=10, width_outer=2, width_inner=1)


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_gravefang.draw_morgath(surface, boss, x, y)

    # ===================================================================
    # ALIAS - nama fungsi yang dipakai registry heroes/__init__.py
    # File ini punya implementasi visual sendiri, tapi nama fungsinya
    # masih ikut template Morgath. Alias supaya import tidak gagal
    # diam-diam (yang bikin boss render jadi bulat generic).
    # ===================================================================
    def draw_gravefang(surface, boss, x, y):
        """Entry point resmi untuk Gravefang."""
        _NS_gravefang.draw_morgath(surface, boss, x, y)



# ====================================================================
# VHALZUN — THE REAPER OF SOULS  (FULL REWRITE v2)
# ====================================================================
# Arsitektur "masterwork" (pola yang sama dengan krobellus/zharok):
#
#   * RENDERER (namespace ini) — rig pixel-art prosedural + pose +
#     telegraph tanah.  Semua bentuk digambar via pygame.draw dengan
#     palet terbatas, tepi tajam (TANPA anti-aliasing), koordinat
#     ter-snap ke pixel, dan surface statis di-cache (bayangan, mist,
#     rune circle, glow lentera).
#   * LAPISAN HIDUP (heroes/vhalzun_fx.py) — trail sapuan sabit dari
#     histori posisi ujung bilah, particle system jiwa, proyektil
#     death pulse & reaper scythe (lifecycle penuh), FX skill Q/W/E/R,
#     impact flash + shockwave + debris, afterimage, screen shake, dan
#     hit-stop 0.03-0.08 s.  Digambar 1:1 ke layar, DI LUAR cache
#     sprite supaya tetap hidup 60 fps.
#   * GAME FEEL BUS (heroes/combat_feel.py) — satu sumber hit-stop &
#     shake untuk seluruh arena.
#
# Kontrak publik (dipakai heroes/__init__, bosses/base_boss,
# hero_skills, tools, dan heroes/vhalzun_fx):
#   draw_vhalzun(surface, boss, x, y)  entry (Boss.draw & render_hero)
#   draw_boss(surface, boss, x, y)     alias backward-compatible
#   PALETTE                            palet karakter + FX (sumber benar)
#   pose_of / anim_state / attack_phase / attack_kind
#   scythe_points(boss, x, y)          (pivot, tip) Vector2 ruang layar
#   body_scale / ground_dy             skala & garis tanah
#   MELEE_REACH / SKILL_DUR / SKILL_RADIUS / ATTACK_ACTIVE_WINDOW /
#   ATTACK_IMPACT_FRAME / ATTACK_RELEASE_FRAME        (dikunci tes)
#   DEBUG_CHARACTER                    overlay hitbox/hurtbox/state
# ====================================================================
class _NS_vhalzun:
    """Namespace vhalzun — renderer The Reaper of Souls (rewrite v2).

    Gaya: 2D pixel art dark-fantasy — chunky pixels, silhouette kuat
    (kerudung runcing + jubah lebar + sabit panjang), palet terbatas,
    tepi keras, highlight/shadow per-pixel.  100% prosedural.
    """

    # ------------------------------------------------------------------
    # KONFIGURASI KARAKTER & KONTRAK TIMING
    # ------------------------------------------------------------------
    CHARACTER_NAME = "vhalzun"

    #: Overlay debug (hitbox, hurtbox, range, state, FPS, partikel).
    DEBUG_CHARACTER = False

    #: Jarak dunia (px) — di bawahnya Vhalzun MENEBAS dengan sabit,
    #: di atasnya ia melempar death pulse.  Hook benturan di
    #: bosses/base_boss.py dan modul FX memakai angka yang sama.
    MELEE_REACH = 96.0

    #: Garis tanah dari titik jangkar (px lokal).
    GROUND_DY = 48

    #: Fase serangan (fraksi 0..1 dari durasi serangan) — satu
    #: kosakata untuk renderer, lapisan hidup, dan overlay debug.
    ATTACK_PHASES = (
        ("ANTICIPATION", 0.00, 0.12),
        ("WINDUP",       0.12, 0.30),
        ("SWING",        0.30, 0.50),
        ("IMPACT",       0.50, 0.62),
        ("FOLLOW",       0.62, 0.82),
        ("RECOVERY",     0.82, 1.00),
    )

    #: Jendela hit aktif + frame benturan (swing) & rilis (pulse).
    ATTACK_ACTIVE_WINDOW = (0.30, 0.55)
    ATTACK_IMPACT_FRAME = 0.42
    ATTACK_RELEASE_FRAME = 0.32

    #: Durasi pose skill dalam FRAME — HARUS sama dengan timer yang
    #: di-set _smart_ai_vhalzun / hero_skills (q 60, w 80, e 60, r 100).
    SKILL_DUR = {"q": 60, "w": 80, "e": 60, "r": 100}

    #: Radius efek di RUANG DUNIA — sama dengan radius damage AI.
    SKILL_RADIUS = {"q": 130.0, "w": 150.0, "e": 60.0, "r": 150.0}

    #: Prioritas state animasi — angka besar menang, DEATH mengunci.
    ANIM_STATES = {
        "IDLE": 0,
        "WALK": 10,
        "RUN": 15,
        "CHARGE": 30,
        "CAST": 35,
        "ATTACK": 40,
        "SWING": 45,
        "SKILL": 50,
        "SPECIAL": 55,
        "HIT": 60,
        "HURT": 65,
        "DEATH": 100,
    }

    #: Lifecycle skill: CAST -> CHARGE -> RELEASE -> AREA -> AFTER.
    SKILL_PHASES = (
        ("CAST",    0.00, 0.16),
        ("CHARGE",  0.16, 0.34),
        ("RELEASE", 0.34, 0.46),
        ("AREA",    0.46, 0.74),
        ("IMPACT",  0.74, 0.86),
        ("AFTER",   0.86, 1.00),
    )

    # ------------------------------------------------------------------
    # PALETTE — Necrophos inspired: necro green + robe teal gelap +
    # tulang pucat + trim emas + aksen ungu.  Kunci identik dengan
    # heroes/vhalzun_fx.VHALZUN_PALETTE (modul FX menyalin dari sini).
    # ------------------------------------------------------------------
    PALETTE = {
        # outline gelap (pixel-art hard edge)
        "outline":        (3,   8,   7),

        # Robe - dark teal/green
        "robe_darkest":   (8,   20,  18),
        "robe_dark":      (18,  42,  36),
        "robe_mid":       (35,  72,  58),
        "robe_light":     (58, 110,  88),
        "robe_high":      (95, 155, 125),
        "robe_shine":     (150, 200, 175),

        # Inner robe - darker
        "inner_darkest":  (5,   12,  10),
        "inner_dark":     (12,  25,  20),
        "inner_mid":      (22,  45,  35),

        # Skull - pale bone
        "bone_dark":      (60,  75,  55),
        "bone_mid":       (110, 130, 100),
        "bone_light":     (170, 185, 155),
        "bone_shine":     (215, 225, 200),

        # Necrotic green - main magical color
        "necro_darkest":  (5,   30,  10),
        "necro_dark":     (18,  75,  25),
        "necro_mid":      (40, 155, 55),
        "necro_light":    (90, 220, 95),
        "necro_bright":   (150, 250, 140),
        "necro_hot":      (200, 255, 180),
        "necro_white":    (235, 255, 220),

        # Scythe blade
        "blade_dark":     (35,  60,  40),
        "blade_mid":      (75, 130,  80),
        "blade_light":    (130, 200, 130),
        "blade_shine":    (200, 245, 200),

        # Gold trim
        "gold_dark":      (85,  60,  15),
        "gold_mid":       (155, 115, 35),
        "gold_light":     (215, 180, 70),
        "gold_shine":     (250, 225, 145),

        # Wood staff
        "wood_dark":      (40,  25,  15),
        "wood_mid":       (70,  45,  25),
        "wood_light":     (110, 78,  45),

        # Eye glow
        "eye_dark":       (25,  75,  20),
        "eye_mid":        (80, 200, 60),
        "eye_bright":     (170, 255, 130),
        "eye_hot":        (230, 255, 200),

        # Purple accent (small)
        "purple_dark":    (35,  15,  55),
        "purple_mid":     (75,  40,  115),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (3,   6,   4),
        "white":          (255, 255, 255),
    }

    # ------------------------------------------------------------------
    # GEOMETRI SABIT (ruang lokal facing-kanan; cermin via x*facing)
    # ------------------------------------------------------------------
    SCYTHE_SHAFT = 44.0        # panjang gagang dari pivot ke hub
    SCYTHE_R_OUT = 24.0        # radius luar bilah
    SCYTHE_R_IN = 10.0         # radius dalam bilah (ketebalan sabit)
    SCYTHE_TIP_OFF = 0.22      # offset sudut ujung bilah dari hub
    _SCYTHE_REST = -0.62       # sudut istirahat (bilah terangkat di punggung)

    # ===================================================================
    # HELPERS MATEMATIKA & PIXEL
    # ===================================================================
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _lerp(a, b, t):
        return a + (b - a) * t

    def _lerp_pt(a, b, t):
        return (_NS_vhalzun._lerp(a[0], b[0], t),
                _NS_vhalzun._lerp(a[1], b[1], t))

    def _ease_out_cubic(t):
        t = max(0.0, min(1.0, t))
        return 1.0 - (1.0 - t) ** 3

    def _ease_in_cubic(t):
        t = max(0.0, min(1.0, t))
        return t * t * t

    def _ease_in_out(t):
        t = max(0.0, min(1.0, t))
        return t * t * (3.0 - 2.0 * t)

    def _snap(v):
        """Snap koordinat ke pixel penuh (pixel-art: tanpa sub-pixel)."""
        return int(round(v))

    def _qphase(phase, buckets=12):
        """Kuantisasi fase animasi supaya surface cache tetap kecil."""
        return int(phase * buckets) % buckets

    def attack_phase(progress):
        """Nama fase serangan untuk progress 0..1."""
        p = max(0.0, min(1.0, float(progress)))
        for name, a, b in _NS_vhalzun.ATTACK_PHASES:
            if a <= p < b:
                return name
        return "RECOVERY"

    def attack_phases_order():
        return tuple(n for n, _a, _b in _NS_vhalzun.ATTACK_PHASES)

    def skill_phase(t):
        """Nama fase skill untuk t 0..1."""
        p = max(0.0, min(1.0, float(t)))
        for name, a, b in _NS_vhalzun.SKILL_PHASES:
            if a <= p < b:
                return name
        return "AFTER"

    # ===================================================================
    # CACHE SURFACE STATIS (dibangun sekali, dipakai semua unit)
    # ===================================================================
    _CACHE = {}
    _CACHE_MAX = 96

    def clear_cache():
        _NS_vhalzun._CACHE.clear()

    def _cached(key, builder):
        s = _NS_vhalzun._CACHE.get(key)
        if s is None:
            if len(_NS_vhalzun._CACHE) >= _NS_vhalzun._CACHE_MAX:
                _NS_vhalzun._CACHE.pop(next(iter(_NS_vhalzun._CACHE)))
            s = builder()
            _NS_vhalzun._CACHE[key] = s
        return s

    @staticmethod
    def _shadow_surf():
        """Bayangan kontak (ellipse chunky berlapis, dibangun sekali)."""
        w, h = 96, 22
        c = _NS_vhalzun.PALETTE
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (0, 0, 0, 110), (4, 4, w - 8, h - 8))
        pygame.draw.ellipse(s, (0, 0, 0, 80), (12, 6, w - 24, h - 12))
        pygame.draw.ellipse(s, (*c["necro_darkest"], 60),
                            (18, 8, w - 36, h - 16))
        return s

    @staticmethod
    def _mist_surf(bucket):
        """Mist nekrotik di bawah Vhalzun melayang (6 bucket fase)."""
        c = _NS_vhalzun.PALETTE
        w, h = 116, 30
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        off = (bucket % 6) / 6.0
        for i, (dx, rw) in enumerate(((-26, 34), (-6, 46), (18, 32))):
            t = (off + i * 0.33) % 1.0
            cy = 20 - int(t * 8)
            a = int(70 * (1.0 - t))
            if a <= 0:
                continue
            pygame.draw.ellipse(
                s, (*c["necro_darkest"], min(255, a)),
                (w // 2 + dx - rw // 2, cy - 4,
                 rw, max(3, 8 - int(t * 4))))
            pygame.draw.ellipse(
                s, (*c["necro_dark"], a // 2),
                (w // 2 + dx - rw // 2 + 3, cy - 3,
                 rw - 6, max(2, 5 - int(t * 3))))
        return s

    @staticmethod
    def _rune_surf(bucket, skill):
        """Rune circle di tanah (8 bucket rotasi; versi skill lebih terang)."""
        c = _NS_vhalzun.PALETTE
        w, h = 132, 48
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, h // 2
        # cincin ellipse chunky (3px, tepi keras)
        pygame.draw.ellipse(s, (*c["necro_dark"], 150),
                            (6, 12, w - 12, 24), 3)
        pygame.draw.ellipse(s, (*c["necro_mid"], 170),
                            (20, 17, w - 40, 14), 2)
        # rune tick yang berputar (garis pendek chunky)
        base = bucket * (math.pi / 4.0)
        for i in range(10):
            ang = base + i * (math.pi / 5.0)
            x1 = cx + int(math.cos(ang) * 34)
            y1 = cy + int(math.sin(ang) * 8)
            x2 = cx + int(math.cos(ang) * 56)
            y2 = cy + int(math.sin(ang) * 14)
            pygame.draw.line(s, (*c["necro_bright"], 160),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(s, (*c["necro_hot"], 90),
                                (12, 8, w - 24, 32), 1)
        return s

    @staticmethod
    def _glow_surf(radius, color):
        """Glow lembut (untuk mata/lentera) — dibangun sekali per radius."""
        size = radius * 2 + 2
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        for r in range(radius, 0, -1):
            a = int(120 * (1.0 - r / float(radius)) ** 1.6)
            if a > 0:
                pygame.draw.circle(s, (*color[:3], min(255, a)),
                                   (size // 2, size // 2), r)
        return s

    @staticmethod
    def _target_position(boss, x, y):
        """Posisi target di ruang jangkar (dengan kompensasi scale)."""
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        return int(x + 200 / (float(getattr(boss, "_render_scale", 1.0)) or 1.0)
                   * getattr(boss, "direction", 1)), int(y)

    # ===================================================================
    # ANIMATION CONTROLLER — satu sumber kebenaran state
    #
    # Menulis ke ``boss``:
    #   _vhz_dt                delta-time nyata (detik, dijepit)
    #   _vhz_moving            unit bergerak frame ini
    #   _vhz_attack_active     serangan sedang berjalan
    #   _vhz_attack_frame      frame ke-n dalam serangan
    #   _vhz_attack_progress   0..1 sepanjang serangan
    #   _vhz_attack_kind       'swing' | 'pulse' (diputuskan saat mulai)
    #   _vhz_attack_phase      ANTICIPATION..RECOVERY
    #   _vhz_hit_active        True hanya di jendela hit aktif
    #   _vhz_hurt_frames       sisa frame respons kena damage
    #   _vhz_skill             'q'/'w'/'e'/'r' (None = tidak ada)
    #   _vhz_skill_progress    0..1 sepanjang skill
    #   _vhz_skill_total       durasi frame skill aktif
    #   _vhz_state/_prev/_time/_frame   state machine + prioritas
    #   _vhz_death_age         umur frame pose kematian
    # ===================================================================
    @staticmethod
    def _update_vhalzun_anim(boss):
        G = _NS_vhalzun

        # ── delta time nyata ─────────────────────────────────────────
        try:
            now = pygame.time.get_ticks()
        except Exception:                          # pragma: no cover
            now = 0
        prev_ms = getattr(boss, "_vhz_last_ms", None)
        if prev_ms is None:
            dt = 1.0 / 60.0
        else:
            dt = (now - prev_ms) / 1000.0
            if dt <= 0.0 or dt > 0.05:
                dt = 1.0 / 60.0
        boss._vhz_last_ms = now
        boss._vhz_dt = dt

        # ── deteksi gerak ────────────────────────────────────────────
        moving = G._detect_moving(boss)
        boss._vhz_moving = moving

        # ── timeline serangan ────────────────────────────────────────
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 44)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_vhz_prev_timer", 0))
        active = bool(getattr(boss, "_vhz_attack_active", False))

        triggered = timer >= cooldown - 1 and previous <= 1
        if triggered:
            boss._vhz_attack_active = True
            boss._vhz_attack_frame = 0
            boss._vhz_attack_manual = False
            tgt = getattr(boss, "target", None)
            if tgt is not None and getattr(tgt, "alive", True):
                dist = math.hypot(
                    float(getattr(tgt, "x", 0.0)) - float(getattr(boss, "x", 0.0)),
                    float(getattr(tgt, "y", 0.0)) - float(getattr(boss, "y", 0.0)))
            else:
                dist = 1e9
            boss._vhz_attack_kind = "swing" if dist <= G.MELEE_REACH else "pulse"
            active = True
        elif active and timer > 0:
            boss._vhz_attack_frame = int(getattr(
                boss, "_vhz_attack_frame", 0)) + 1
        elif timer <= 0:
            if active and not getattr(boss, "_vhz_attack_manual", False) \
                    and float(getattr(boss, "_vhz_attack_progress", 0.0)) > 0.0:
                # pemanggil eksternal menggerakkan progress manual (alat
                # uji) — hormati, tandai manual
                boss._vhz_attack_manual = True
            elif not getattr(boss, "_vhz_attack_manual", False):
                boss._vhz_attack_active = False
                boss._vhz_attack_frame = 0
                active = False
            if not active:
                boss._vhz_attack_active = False
                boss._vhz_attack_frame = 0
        boss._vhz_prev_timer = timer

        frame = int(getattr(boss, "_vhz_attack_frame", 0)) if active else 0
        span = max(1, cooldown - 1)
        if bool(getattr(boss, "_vhz_attack_manual", False)) and active:
            progress = min(1.0, max(0.0, float(getattr(
                boss, "_vhz_attack_progress", 0.0))))
            boss._vhz_attack_frame = int(round(progress * span))
        else:
            progress = min(1.0, frame / float(span)) if active else 0.0
            boss._vhz_attack_progress = progress

        # ── fase + jendela hit ───────────────────────────────────────
        if not getattr(boss, "_vhz_attack_active", False):
            boss._vhz_attack_active = False
            boss._vhz_attack_manual = False
            active = False
        phase_name = G.attack_phase(progress) if active else "NONE"
        boss._vhz_attack_phase = phase_name
        lo, hi = G.ATTACK_ACTIVE_WINDOW
        boss._vhz_hit_active = bool(active and lo <= progress < hi)

        # ── respons kena damage (HURT) ───────────────────────────────
        hurt = int(getattr(boss, "_vhz_hurt_frames", 0))
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        if flash >= 8 and hurt <= 0:
            hurt = 10
        boss._vhz_hurt_frames = max(0, hurt - 1) if hurt > 0 else 0

        # ── skill (active_skill; jalur boss generik: ability -> 'q') ──
        skill = getattr(boss, "active_skill", None)
        if skill is None and getattr(boss, "ability_active", False) \
                and int(getattr(boss, "ability_active_timer", 0) or 0) > 0:
            skill = "q"
        if skill is not None:
            timer_s = int(getattr(boss, "active_skill_timer", 0) or 0)
            if skill == "q" and getattr(boss, "active_skill", None) is None:
                timer_s = int(getattr(boss, "ability_active_timer", 0) or 0)
            total = int(getattr(boss, "_vhz_skill_total", 0) or 0)
            if getattr(boss, "_vhz_skill", None) != skill:
                total = max(timer_s, G.SKILL_DUR.get(skill, 60))
            boss._vhz_skill_total = max(total, timer_s, 1)
            boss._vhz_skill_progress = max(
                0.0, min(1.0, 1.0 - timer_s / float(boss._vhz_skill_total)))
            boss._vhz_skill = skill
        else:
            boss._vhz_skill = None
            boss._vhz_skill_progress = 0.0
            boss._vhz_skill_total = 0

        # ── death age ────────────────────────────────────────────────
        if not getattr(boss, "alive", True):
            boss._vhz_death_age = int(getattr(boss, "_vhz_death_age", 0)) + 1
        else:
            boss._vhz_death_age = 0

        # ── state machine (prioritas) ────────────────────────────────
        if not getattr(boss, "alive", True):
            state = "DEATH"
        elif boss._vhz_hurt_frames > 0:
            state = "HURT"
        elif skill is not None:
            state = "SKILL" if skill in ("q", "w") else "SPECIAL"
        elif active:
            state = "SWING" if getattr(boss, "_vhz_attack_kind",
                                       "pulse") == "swing" else "ATTACK"
        elif moving:
            state = "RUN" if getattr(boss, "is_enraged", False) else "WALK"
        else:
            state = "IDLE"
        if state != getattr(boss, "_vhz_state", None):
            boss._vhz_state_prev = getattr(boss, "_vhz_state", state)
            boss._vhz_state = state
            boss._vhz_state_time = 0
            boss._vhz_state_frame = 0
        else:
            boss._vhz_state_time = getattr(boss, "_vhz_state_time", 0) + dt
            boss._vhz_state_frame = int(getattr(boss, "_vhz_state_frame", 0)) + 1
        return state

    @staticmethod
    def _detect_moving(boss):
        """Deteksi gerak dari delta posisi (cache 2 frame terakhir)."""
        if not hasattr(boss, "_vhz_last_x"):
            boss._vhz_last_x = boss.x
            boss._vhz_last_y = boss.y
            return False
        dx = abs(boss.x - boss._vhz_last_x)
        dy = abs(boss.y - boss._vhz_last_y)
        boss._vhz_last_x = boss.x
        boss._vhz_last_y = boss.y
        return dx + dy > 0.3

    # ===================================================================
    # POSE STATE — satu sumber kebenaran untuk rig DAN semua FX
    # ===================================================================
    ACTIONS = ("idle", "walk", "attack", "swing", "cast_q", "cast_w",
               "cast_e", "cast_r", "hurt", "death")

    @staticmethod
    def _resolve_pose(boss, moving=False):
        """(action, phase, ap) — murni, boleh dipanggil ulang oleh FX."""
        if not getattr(boss, "alive", True):
            return ("death", float(getattr(boss, "pulse", 0.0)), 0.0)
        skill = getattr(boss, "_vhz_skill", None)
        attacking = bool(getattr(boss, "_vhz_attack_active", False))
        if skill is not None:
            action = {"q": "cast_q", "w": "cast_w",
                      "e": "cast_e", "r": "cast_r"}.get(skill, "cast_q")
            ap = float(getattr(boss, "_vhz_skill_progress", 0.0) or 0.0)
        elif attacking:
            action = "swing" if getattr(boss, "_vhz_attack_kind",
                                        "pulse") == "swing" else "attack"
            ap = max(0.0, min(1.0, float(getattr(
                boss, "_vhz_attack_progress", 0.0))))
        elif int(getattr(boss, "_vhz_hurt_frames", 0)) > 0:
            action, ap = "hurt", 0.0
        elif moving:
            action, ap = "walk", 0.0
        else:
            action, ap = "idle", 0.0
        return action, float(getattr(boss, "pulse", 0.0)), ap

    @staticmethod
    def pose_of(boss):
        """Publik: pose tersimpan (dipakai modul FX tanpa efek samping)."""
        if not getattr(boss, "alive", True):
            return ("death", float(getattr(boss, "pulse", 0.0)), 0.0)
        skill = getattr(boss, "_vhz_skill", None)
        if skill is not None:
            action = {"q": "cast_q", "w": "cast_w",
                      "e": "cast_e", "r": "cast_r"}.get(skill, "cast_q")
            return (action, float(getattr(boss, "pulse", 0.0)),
                    float(getattr(boss, "_vhz_skill_progress", 0.0) or 0.0))
        if getattr(boss, "_vhz_attack_active", False):
            action = "swing" if getattr(boss, "_vhz_attack_kind",
                                        "pulse") == "swing" else "attack"
            return (action, float(getattr(boss, "pulse", 0.0)),
                    float(getattr(boss, "_vhz_attack_progress", 0.0) or 0.0))
        if bool(getattr(boss, "_vhz_moving", False)):
            return ("walk", float(getattr(boss, "pulse", 0.0)), 0.0)
        return ("idle", float(getattr(boss, "pulse", 0.0)), 0.0)

    @staticmethod
    def anim_state(boss):
        """Publik: nama state animasi aktif (IDLE/WALK/.../DEATH)."""
        return str(getattr(boss, "_vhz_state", "IDLE"))

    @staticmethod
    def attack_kind(boss):
        return str(getattr(boss, "_vhz_attack_kind", "pulse"))

    @staticmethod
    def body_scale(boss):
        sc = getattr(boss, "_render_scale", 1.0)
        try:
            sc = float(sc)
        except (TypeError, ValueError):
            sc = 1.0
        return sc if sc > 0.01 else 1.0

    @staticmethod
    def ground_dy(boss):
        return float(_NS_vhalzun.GROUND_DY) * _NS_vhalzun.body_scale(boss)

    # ===================================================================
    # GEOMETRI SABIT — pivot + sudut per pose.
    # Dipakai renderer (gambar) DAN heroes/vhalzun_fx (trail + titik
    # lahir proyektil) lewat scythe_points() — mustahil beda frame.
    # ===================================================================
    @staticmethod
    def _scythe_pivot_local(action, ap, phase, boss=None):
        """Posisi genggaman (pivot sabit) ruang lokal, per pose."""
        G = _NS_vhalzun
        if action == "swing":
            # langkah kecil ke depan saat menebas, mundur saat antisipasi
            if ap < 0.12:
                t = G._ease_out_cubic(ap / 0.12)
                return G._lerp_pt((12, -18), (9, -18), t)
            if ap < 0.30:
                t = G._ease_out_cubic((ap - 0.12) / 0.18)
                return G._lerp_pt((9, -18), (8, -20), t)
            if ap < 0.62:
                t = G._ease_in_out((ap - 0.30) / 0.32)
                return G._lerp_pt((8, -20), (17, -12), t)
            return G._lerp_pt((17, -12), (12, -18),
                              G._ease_in_out((ap - 0.62) / 0.38))
        if action == "attack":        # lempar death pulse
            if ap < 0.32:
                t = G._ease_out_cubic(ap / 0.32)
                return G._lerp_pt((10, -16), (8, -22), t)
            if ap < 0.50:
                t = G._ease_in_cubic((ap - 0.32) / 0.18)
                return G._lerp_pt((8, -22), (18, -14), t)
            return G._lerp_pt((18, -14), (10, -16),
                              G._ease_in_out((ap - 0.50) / 0.50))
        if action == "cast_q":
            return (10, -22 - int(math.sin(ap * math.pi) * 4))
        if action == "cast_w":
            return (6, -24)
        if action == "cast_e":
            if ap < 0.55:
                return (13, -24)
            return (16, -16)
        if action == "cast_r":
            return (9, -20 - int(math.sin(min(1.0, ap * 1.6) * math.pi) * 6))
        if action == "hurt":
            return (6, -16)
        if action == "death":
            return (14, -8 + min(1.0, ap + 0.4) * 10)
        if action == "walk":
            return (12, -18 + int(math.sin(phase * 2.2) * 2))
        # idle + fallback: sway pelan
        return (12, -18 + int(math.sin(phase * 0.8) * 1.5))

    @staticmethod
    def _scythe_angle(action, ap, phase, boss=None):
        """Sudut gagang sabit (radian, ruang lokal facing-kanan).

        Swing adalah busur KONTINYU: ANTICIPATION mundur -> WINDUP
        terangkat -> SWING menyapu cepat -> IMPACT decel -> FOLLOW
        THROUGH -> RECOVERY kembali.  Tidak ada lompatan sudut.
        """
        G = _NS_vhalzun
        rest = G._SCYTHE_REST + math.sin(phase * 0.8) * 0.05
        if action == "swing":
            if ap < 0.12:                       # ANTICIPATION
                t = G._ease_out_cubic(ap / 0.12)
                return G._lerp(rest, -0.50, t)
            if ap < 0.30:                       # WINDUP
                t = G._ease_out_cubic((ap - 0.12) / 0.18)
                return G._lerp(-0.50, -0.72, t)
            if ap < 0.50:                       # SWING (cepat)
                t = G._ease_in_cubic((ap - 0.30) / 0.20)
                return G._lerp(-0.72, 0.75, t)
            if ap < 0.62:                       # IMPACT (decel)
                t = G._ease_out_cubic((ap - 0.50) / 0.12)
                return G._lerp(0.75, 1.00, t)
            if ap < 0.82:                       # FOLLOW THROUGH
                t = G._ease_in_out((ap - 0.62) / 0.20)
                return G._lerp(1.00, 1.35, t)
            # RECOVERY
            t = G._ease_in_out((ap - 0.82) / 0.18)
            return G._lerp(1.35, rest, t)
        if action == "attack":                  # jab lempar pulse
            if ap < 0.32:
                t = G._ease_out_cubic(ap / 0.32)
                return G._lerp(rest, -0.95, t)
            if ap < 0.50:
                t = G._ease_in_cubic((ap - 0.32) / 0.18)
                return G._lerp(-0.95, -0.10, t)
            return G._lerp(-0.10, rest,
                           G._ease_in_out((ap - 0.50) / 0.50))
        if action == "cast_e":                  # spin-up lalu lepas
            if ap < 0.55:
                return rest + ap * (math.pi * 3.0) / 0.55
            return G._lerp(rest + math.pi * 3.0, -0.35,
                           G._ease_out_cubic((ap - 0.55) / 0.45))
        if action == "cast_q":
            return rest - ap * 0.55
        if action == "cast_w":
            return -1.55 + math.sin(phase * 2.0) * 0.10
        if action == "cast_r":
            return rest - 0.35 + math.sin(phase * 1.4) * 0.08
        if action == "hurt":
            return rest - 0.45
        if action == "death":
            return rest + min(1.0, ap + 0.4) * 1.25
        if action == "walk":
            return rest + math.sin(phase * 2.2) * 0.12
        return rest + math.sin(phase * 0.8) * 0.05

    @staticmethod
    def scythe_points(boss, x, y):
        """(pivot, tip) pygame.Vector2 ruang LAYAR.

        Dipakai heroes/vhalzun_fx (trail sapuan, titik lahir proyektil)
        dan overlay debug — jembatan satu-satunya ke geometri sabit.
        """
        G = _NS_vhalzun
        action, phase, ap = G.pose_of(boss)
        facing = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        sc = G.body_scale(boss)
        p = G._scythe_pivot_local(action, ap, phase, boss)
        th = G._scythe_angle(action, ap, phase, boss)
        hub = (p[0] + G.SCYTHE_SHAFT * math.cos(th),
               p[1] + G.SCYTHE_SHAFT * math.sin(th))
        tip_l = (hub[0] + G.SCYTHE_R_OUT * math.cos(th + G.SCYTHE_TIP_OFF + 0.9),
                 hub[1] + G.SCYTHE_R_OUT * math.sin(th + G.SCYTHE_TIP_OFF + 0.9))
        pivot = pygame.Vector2(x + p[0] * facing * sc, y + p[1] * sc)
        tip = pygame.Vector2(x + tip_l[0] * facing * sc, y + tip_l[1] * sc)
        return (pivot, tip)

    @staticmethod
    def _swing_hitbox(boss, cx, cy):
        """Rect hitbox ayunan (ruang canvas, sc=1) saat jendela aktif."""
        if not getattr(boss, "_vhz_hit_active", False):
            return None
        f = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        reach = int(_NS_vhalzun.MELEE_REACH * 0.9)
        top = int(cy - 44)
        h = 76
        left = int(cx) if f > 0 else int(cx) - reach
        return pygame.Rect(left, top, max(8, reach), max(10, h))

    @staticmethod
    def _hurtbox(boss, cx, cy):
        """Hurtbox badan (ruang canvas, sc=1; untuk overlay debug)."""
        w, h = 46, 74
        return pygame.Rect(int(cx - w / 2), int(cy - 52), w, h)

    # ===================================================================
    # GERBANG LAPISAN HIDUP (heroes/vhalzun_fx)
    #   Trail sabetan, partikel, proyektil, skill FX, impact, hit-stop,
    #   dan screen shake hidup di RUANG LAYAR skala 1:1 supaya tidak
    #   ikut beku / menyusut bersama sprite cache di lane hero. Kalau
    #   modulnya tidak ada, owns() False dan renderer menggambar
    #   fallback canvas sendiri (kehilangan polish, BUKAN efek).
    # ===================================================================
    _LIVE_MOD = None            # None = belum dicari, False = tidak ada

    @staticmethod
    def _live_module():
        NS = _NS_vhalzun
        if NS._LIVE_MOD is None:
            try:
                from heroes import vhalzun_fx as mod
                NS._LIVE_MOD = mod if getattr(mod, "VHALZUN_FX_ENABLED",
                                              True) else False
            except Exception:
                NS._LIVE_MOD = False
        return NS._LIVE_MOD or None

    @staticmethod
    def live_fx_ready():
        return _NS_vhalzun._live_module() is not None

    @staticmethod
    def _live_fx(boss, surface, x, y, want_draw, portrait):
        """Pasang/gambar lapisan hidup. Return (mod_untuk_draw, owned)."""
        NS = _NS_vhalzun
        if portrait:
            return None, False
        mod = NS._live_module()
        if mod is None:
            return None, False
        try:
            if want_draw:
                mod.draw_ground_layer(surface, boss, x, y)
            else:
                mod.attach(boss)
        except Exception:
            return None, False
        try:
            owned = bool(mod.owns(boss))
            if owned and not want_draw:
                # Lane hero: yang menggambar lapisan hidup adalah
                # pipeline heroes/__init__. Kalau ternyata TIDAK ada
                # yang menggambarnya, jangan matikan fallback canvas.
                checker = getattr(mod, "recently_drawn", None)
                if checker is not None:
                    owned = bool(checker(boss))
        except Exception:
            owned = False
        return (mod if want_draw else None), owned

    # ===================================================================
    # OFFSET BADAN per pose (bob napas, lean, flare hem)
    # ===================================================================
    @staticmethod
    def _body_offsets(action, ap, phase, boss=None):
        """(dx, dy, flare) — offset badan relatif jangkar."""
        G = _NS_vhalzun
        if action == "idle":
            breathe = math.sin(phase * 0.8)
            return (0.0, breathe * 2.0, 0.25 + 0.1 * breathe)
        if action == "walk":
            step = math.sin(phase * 2.2)
            return (step * 2.0, -abs(math.sin(phase * 2.2)) * 3.0,
                    0.55 + 0.2 * abs(step))
        if action == "swing":
            if ap < 0.30:
                t = G._ease_out_cubic(ap / 0.30)
                return (G._lerp(0, -4, t), -1.0, G._lerp(0.3, 0.9, t))
            if ap < 0.62:
                t = G._ease_in_out((ap - 0.30) / 0.32)
                return (G._lerp(-4, 7, t), 1.0, G._lerp(0.9, 1.5, t))
            return (G._lerp(7, 0, G._ease_in_out((ap - 0.62) / 0.38)),
                    0.0, G._lerp(1.5, 0.3, (ap - 0.62) / 0.38))
        if action == "attack":
            if ap < 0.32:
                return (-2.0, -1.0, 0.6)
            if ap < 0.50:
                return (4.0, 0.0, 1.0)
            return (2.0, 0.0, 0.5)
        if action == "cast_q":
            return (0.0, -3.0 * math.sin(min(1.0, ap * 1.4) * math.pi), 1.0)
        if action == "cast_w":
            return (0.0, -2.0, 1.2)
        if action == "cast_e":
            return (1.0 if ap >= 0.55 else -1.0, -1.0, 1.3)
        if action == "cast_r":
            return (0.0, -5.0 * math.sin(min(1.0, ap * 1.6) * math.pi), 1.6)
        if action == "hurt":
            return (-4.0, 1.0, 0.4)
        if action == "death":
            age = int(getattr(boss, "_vhz_death_age", 0) or 0) \
                if boss is not None else 0
            return (2.0, min(26.0, age * 0.55), 0.2)
        return (0.0, 0.0, 0.3)

    # ===================================================================
    # RIG PIXEL-ART — komposisi berlapis
    #   SHADOW -> HEM -> ROBE -> ARMOR -> HEAD -> WEAPON -> FRONT LIMB
    #   -> HIGHLIGHT
    # ===================================================================
    @staticmethod
    def _map(cx, cy, sc, facing, lx, ly):
        """Peta koordinat lokal -> layar (mirror + snap pixel)."""
        return (_NS_vhalzun._snap(cx + lx * facing * sc),
                _NS_vhalzun._snap(cy + ly * sc))

    @staticmethod
    def _draw_hem(surface, bx, by, phase, flare, action):
        """HEM jubah lebar compang-camping (silhouette dasar)."""
        c = _NS_vhalzun.PALETTE
        sway = math.sin(phase * 1.5) * 2
        sway2 = math.sin(phase * 0.9 + 1.3) * 2
        fl = flare * 4
        pts = [
            (bx - 20 - fl, by + 2),
            (bx + 20 + fl, by + 2),
            (bx + 26 + fl + sway, by + 16),
            (bx + 24 + sway2, by + 30),
            (bx + 18, by + 40),
            # tepi compang: gigi segitiga chunky
            (bx + 13, by + 34), (bx + 10 + sway2, by + 46),
            (bx + 5, by + 38), (bx, by + 48 + sway),
            (bx - 5, by + 38), (bx - 10 + sway2, by + 46),
            (bx - 13, by + 34), (bx - 18, by + 40),
            (bx - 24 - sway2, by + 30),
            (bx - 26 - fl - sway, by + 16),
        ]
        # outline gelap 1px (offset), lalu isi
        pygame.draw.polygon(surface, c["outline"],
                            [(px + 2, py + 2) for px, py in pts])
        pygame.draw.polygon(surface, c["robe_darkest"], pts)
        # band tengah lebih terang
        pygame.draw.polygon(surface, c["robe_dark"], [
            (bx - 15 - fl * 0.6, by + 4), (bx + 15 + fl * 0.6, by + 4),
            (bx + 20 + sway, by + 16), (bx + 18, by + 28),
            (bx + 12, by + 36), (bx - 12, by + 36),
            (bx - 18, by + 28), (bx - 20 - sway, by + 16),
        ])
        # lipatan jubah (garis vertikal chunky)
        for xoff in (-10, -4, 3, 9):
            top = by + 6
            bot = by + 30 + math.sin(phase * 1.2 + xoff) * 2
            pygame.draw.line(surface, c["robe_mid"],
                             (bx + xoff, top), (bx + xoff, bot), 1)
        # highlight rim kiri (cahaya jiwa)
        pygame.draw.line(surface, c["robe_light"],
                         (bx - 17 - fl * 0.7, by + 5),
                         (bx - 22 - sway, by + 26), 1)

    @staticmethod
    def _draw_torso(surface, bx, by, phase, action):
        """TORSO + sash + gem dada."""
        c = _NS_vhalzun.PALETTE
        pygame.draw.polygon(surface, c["outline"], [
            (bx - 13, by - 26), (bx + 13, by - 26),
            (bx + 15, by - 12), (bx + 12, by + 4),
            (bx - 12, by + 4), (bx - 15, by - 12)])
        pygame.draw.polygon(surface, c["robe_dark"], [
            (bx - 12, by - 25), (bx + 12, by - 25),
            (bx + 14, by - 12), (bx + 11, by + 3),
            (bx - 11, by + 3), (bx - 14, by - 12)])
        # interior kerudung (gelap)
        pygame.draw.polygon(surface, c["inner_darkest"], [
            (bx - 8, by - 22), (bx + 8, by - 22),
            (bx + 9, by - 8), (bx - 9, by - 8)])
        # sash pinggang + trim emas
        pygame.draw.rect(surface, c["robe_darkest"],
                         (bx - 15, by - 2, 30, 5))
        pygame.draw.rect(surface, c["gold_dark"],
                         (bx - 14, by - 1, 28, 1))
        pygame.draw.rect(surface, c["gold_mid"],
                         (bx - 12, by + 1, 24, 1))
        # gem nekrotik dada (berdenyut)
        pulse = 0.65 + 0.35 * math.sin(phase * 3.0)
        pygame.draw.rect(surface, c["necro_dark"],
                         (bx - 3, by - 16, 6, 6))
        pygame.draw.rect(surface, c["necro_mid"],
                         (bx - 2, by - 15, 4, 4))
        if pulse > 0.55:
            pygame.draw.rect(surface, c["necro_bright"],
                             (bx - 1, by - 14, 2, 2))

    @staticmethod
    def _draw_pauldrons(surface, bx, by, phase, action):
        """PAULDRON bahu chunky (armor band)."""
        c = _NS_vhalzun.PALETTE
        lift = 1 if action in ("cast_w", "cast_r") else 0
        for side in (-1, 1):
            sx = bx + side * 14
            sy = by - 24 - (lift if side == -1 else 0)
            pygame.draw.rect(surface, c["outline"],
                             (sx - 7, sy - 4, 15, 10))
            pygame.draw.rect(surface, c["robe_darkest"],
                             (sx - 6, sy - 3, 13, 8))
            pygame.draw.rect(surface, c["robe_dark"],
                             (sx - 5, sy - 3, 11, 4))
            # spike pauldron (silhouette)
            pygame.draw.polygon(surface, c["robe_mid"], [
                (sx - side * 6, sy - 3), (sx - side * 10, sy + 1),
                (sx - side * 5, sy + 3)])
            # pixel highlight
            pygame.draw.rect(surface, c["robe_light"],
                             (sx - 4, sy - 2, 3, 1))

    @staticmethod
    def _draw_head(surface, bx, by, facing, phase, action):
        """HOOD runcing + tengkorak bercahaya di dalamnya."""
        c = _NS_vhalzun.PALETTE
        tilt = 0
        if action == "idle":
            tilt = int(math.sin(phase * 0.8) * 1)
        elif action == "walk":
            tilt = int(math.sin(phase * 2.2) * 1.5)
        elif action == "hurt":
            tilt = -2
        elif action == "death":
            tilt = 4
        hx, hy = bx + tilt * 0.5, by - 34 + tilt
        # HOOD luar (silhouette runcing condong ke belakang)
        hood = [
            (hx - 13, hy + 8), (hx - 12, hy - 4), (hx - 7, hy - 13),
            (hx - facing * 2, hy - 17), (hx + 7, hy - 12),
            (hx + 12, hy - 2), (hx + 13, hy + 8),
            (hx + 8, hy + 12), (hx - 8, hy + 12),
        ]
        pygame.draw.polygon(surface, c["outline"],
                            [(px + 2, py + 2) for px, py in hood])
        pygame.draw.polygon(surface, c["robe_darkest"], hood)
        # HOOD dalam (lebih terang, band)
        pygame.draw.polygon(surface, c["robe_dark"], [
            (hx - 10, hy + 6), (hx - 9, hy - 3), (hx - 5, hy - 10),
            (hx + 5, hy - 10), (hx + 9, hy - 3), (hx + 10, hy + 6),
            (hx + 6, hy + 9), (hx - 6, hy + 9)])
        # bukaan hood (gelap total)
        pygame.draw.polygon(surface, c["shadow_deep"], [
            (hx - 7, hy + 5), (hx - 6, hy - 4), (hx, hy - 8),
            (hx + 6, hy - 4), (hx + 7, hy + 5), (hx + 4, hy + 8),
            (hx - 4, hy + 8)])
        # glow interior (dari mata) — surface cache kecil
        glow = _NS_vhalzun._cached(("eyeglow", 3), lambda:
                                   _NS_vhalzun._glow_surf(3, c["necro_mid"]))
        glow.set_alpha(150)
        surface.blit(glow, (hx - glow.get_width() // 2,
                            hy - glow.get_height() // 2))
        glow.set_alpha(255)
        # TENGKORAK: dome + rahang chunky
        pygame.draw.circle(surface, c["bone_dark"], (int(hx), int(hy)), 6)
        pygame.draw.circle(surface, c["bone_mid"], (int(hx - 1), int(hy - 1)), 5)
        pygame.draw.rect(surface, c["bone_mid"], (hx - 4, hy + 4, 8, 3))
        pygame.draw.rect(surface, c["bone_light"], (hx - 3, hy - 4, 3, 3))
        # socket mata gelap + api jiwa (selalu menyala, intensitas naik-turun)
        pygame.draw.rect(surface, c["shadow_deep"], (hx - 4, hy - 2, 3, 3))
        pygame.draw.rect(surface, c["shadow_deep"], (hx + 1, hy - 2, 3, 3))
        eye_pulse = 0.6 + 0.4 * math.sin(phase * 4.0)
        pygame.draw.rect(surface, c["eye_mid"],
                         (hx - 4 + (1 if facing > 0 else 0), hy - 1, 2, 2))
        pygame.draw.rect(surface, c["eye_mid"],
                         (hx + 1 + (1 if facing > 0 else 0), hy - 1, 2, 2))
        if eye_pulse > 0.55:
            pygame.draw.rect(surface, c["eye_bright"],
                             (hx - 4, hy - 1, 2, 1))
            pygame.draw.rect(surface, c["eye_bright"],
                             (hx + 2, hy - 1, 2, 1))
        if eye_pulse > 0.85:
            pygame.draw.rect(surface, c["eye_hot"], (hx - 3, hy - 1, 1, 1))
            pygame.draw.rect(surface, c["eye_hot"], (hx + 3, hy - 1, 1, 1))
        # rongga hidung + gigi
        pygame.draw.rect(surface, c["shadow_deep"], (hx - 1, hy + 2, 2, 1))
        for i in range(3):
            pygame.draw.rect(surface, c["shadow_deep"],
                             (hx - 3 + i * 3, hy + 5, 1, 2))
        # rim light atas hood
        pygame.draw.line(surface, c["robe_mid"],
                         (hx - 6, hy - 11), (hx + 4, hy - 11), 1)

    @staticmethod
    def _draw_scythe_at(surface, bx, by, sc, facing, angle, pivot, glow_k,
                        phase):
        """SABIT: gagang kayu + bilah sabit + lentera jiwa.

        Bilah digambar sebagai polygon sabit (dua busur radius berbeda)
        dengan glow nekrotik di tepi — glow_k 0..1 mengatur intensitas.
        """
        G = _NS_vhalzun
        c = G.PALETTE
        P = lambda lx, ly: G._map(bx, by, sc, facing, lx, ly)  # noqa: E731
        hub = (pivot[0] + G.SCYTHE_SHAFT * math.cos(angle),
               pivot[1] + G.SCYTHE_SHAFT * math.sin(angle))
        p0 = P(pivot[0], pivot[1])
        p1 = P(hub[0], hub[1])
        w_shaft = max(2, int(5 * sc))
        # gagang: outline + kayu 3 band
        pygame.draw.line(surface, c["outline"],
                         (p0[0] + 1, p0[1] + 1), (p1[0] + 1, p1[1] + 1),
                         w_shaft + 2)
        pygame.draw.line(surface, c["wood_dark"], p0, p1, w_shaft)
        pygame.draw.line(surface, c["wood_mid"], p0, p1, max(1, w_shaft - 2))
        pygame.draw.line(surface, c["wood_light"],
                         (p0[0], p0[1] - 1), (p1[0], p1[1] - 1), 1)
        # bungkus emas di gagang (3 titik chunky)
        for i in range(3):
            t = 0.15 + i * 0.11
            gp = P(pivot[0] + (hub[0] - pivot[0]) * t,
                   pivot[1] + (hub[1] - pivot[1]) * t)
            pygame.draw.rect(surface, c["gold_dark"],
                             (gp[0] - 1, gp[1] - 1, 3, 3))
            pygame.draw.rect(surface, c["gold_mid"],
                             (gp[0] - 1, gp[1] - 1, 2, 1))
        # hub (sambungan bilah)
        pygame.draw.circle(surface, c["gold_dark"], p1, max(2, int(3 * sc)))
        pygame.draw.circle(surface, c["gold_light"],
                           (p1[0] - 1, p1[1] - 1), max(1, int(1 * sc)))
        # BILAH SABIT: busur luar (r_out) vs dalam (r_in)
        th0 = angle - 0.35
        th1 = angle + 1.15
        n = 10
        outer = []
        for i in range(n + 1):
            t = th0 + (th1 - th0) * i / n
            outer.append(P(hub[0] + G.SCYTHE_R_OUT * math.cos(t),
                           hub[1] + G.SCYTHE_R_OUT * math.sin(t)))
        inner = []
        for i in range(n + 1):
            t = th1 - (th1 - th0) * i / n
            inner.append(P(hub[0] + (G.SCYTHE_R_IN - 2.0) * math.cos(t),
                           hub[1] + (G.SCYTHE_R_IN - 2.0) * math.sin(t)))
        blade = outer + inner
        pygame.draw.polygon(surface, c["outline"], blade)
        pygame.draw.polygon(surface, c["blade_dark"], blade)
        # band dalam bilah + shine tepi (hard edge)
        band = []
        for i in range(n + 1):
            t = th0 + (th1 - th0) * i / n
            band.append(P(hub[0] + (G.SCYTHE_R_OUT - 5.0) * math.cos(t),
                          hub[1] + (G.SCYTHE_R_OUT - 5.0) * math.sin(t)))
        pygame.draw.polygon(surface, c["blade_mid"], outer + band[::-1])
        pygame.draw.lines(surface, c["blade_shine"], False, outer, 1)
        # glow nekrotik di tepi bilah (pixel berdenyut, chunky)
        if glow_k > 0.05:
            gpulse = glow_k * (0.7 + 0.3 * math.sin(phase * 9.0))
            for i in range(0, n + 1, 2):
                t = th0 + (th1 - th0) * i / n
                gpx = P(hub[0] + (G.SCYTHE_R_OUT + 1.5) * math.cos(t),
                        hub[1] + (G.SCYTHE_R_OUT + 1.5) * math.sin(t))
                if gpulse > 0.55:
                    pygame.draw.rect(surface, c["necro_light"],
                                     (gpx[0] - 1, gpx[1] - 1, 2, 2))
                else:
                    pygame.draw.rect(surface, c["necro_mid"],
                                     (gpx[0], gpx[1], 1, 1))
        # LENTERA jiwa di ujung bawah gagang (kebalikan hub)
        lx = pivot[0] - math.cos(angle) * 12.0
        ly = pivot[1] - math.sin(angle) * 12.0
        lp = P(lx, ly)
        lant_glow = G._cached(
            ("lantglow", 5), lambda: G._glow_surf(5, c["necro_mid"]))
        fpulse = 0.6 + 0.4 * math.sin(phase * 5.0)
        lant_glow.set_alpha(int(160 * fpulse * max(0.4, glow_k)))
        surface.blit(lant_glow, (lp[0] - lant_glow.get_width() // 2,
                                 lp[1] - lant_glow.get_height() // 2))
        lant_glow.set_alpha(255)
        pygame.draw.rect(surface, c["gold_dark"],
                         (lp[0] - 3, lp[1] - 3, 7, 7))
        pygame.draw.rect(surface, c["gold_mid"],
                         (lp[0] - 2, lp[1] - 2, 5, 5))
        pygame.draw.rect(surface, c["necro_bright"],
                         (lp[0] - 1, lp[1] - 1, 3, 3))
        pygame.draw.rect(surface, c["necro_hot"], (lp[0], lp[1], 1, 1))

    @staticmethod
    def _draw_arms(surface, bx, by, sc, facing, action, ap, phase, pivot):
        """Lengan baju (sleeve chunky 2 segmen) + tangan tulang."""
        G = _NS_vhalzun
        c = G.PALETTE
        P = lambda lx, ly: G._map(bx, by, sc, facing, lx, ly)  # noqa: E731

        def sleeve(p_from, p_to, width):
            a = P(*p_from)
            b = P(*p_to)
            pygame.draw.line(surface, c["outline"],
                             (a[0] + 1, a[1] + 1), (b[0] + 1, b[1] + 1),
                             width + 2)
            pygame.draw.line(surface, c["robe_darkest"], a, b, width)
            pygame.draw.line(surface, c["robe_dark"], a, b, max(1, width - 2))
            pygame.draw.line(surface, c["robe_mid"],
                             (a[0], a[1] - 1), (b[0], b[1] - 1), 1)

        def bone_hand(p_xy):
            h = P(*p_xy)
            pygame.draw.circle(surface, c["bone_dark"], h,
                               max(2, int(2.5 * sc)))
            pygame.draw.circle(surface, c["bone_mid"],
                               (h[0] - 1, h[1] - 1), max(1, int(1.5 * sc)))

        # ── lengan SABIT (memegang pivot) ──────────────────────────
        shoulder = (pivot[0] - 7, pivot[1] + 10)
        elbow = (pivot[0] - 3, pivot[1] + 4)
        sleeve(shoulder, elbow, max(3, int(5 * sc)))
        sleeve(elbow, pivot, max(3, int(4 * sc)))
        bone_hand(pivot)

        # ── lengan BEBAS (belakang saat idle, lurus saat cast) ─────
        if action == "attack":
            if ap < 0.32:
                t = G._ease_out_cubic(ap / 0.32)
                free_to = G._lerp_pt((-14, -8), (-6, -16), t)
            elif ap < 0.50:
                t = G._ease_in_cubic((ap - 0.32) / 0.18)
                free_to = G._lerp_pt((-6, -16), (16, -12), t)
            else:
                t = G._ease_in_out((ap - 0.50) / 0.50)
                free_to = G._lerp_pt((16, -12), (-14, -8), t)
        elif action == "swing":
            if ap < 0.30:
                free_to = (-4, -24)
            elif ap < 0.62:
                free_to = (6, -6)
            else:
                free_to = (-12, -10)
        elif action in ("cast_q", "cast_w"):
            free_to = (-17, -18 - int(math.sin(phase * 3.0) * 2))
        elif action == "cast_e":
            free_to = (14, -20) if ap >= 0.55 else (-12, -20)
        elif action == "cast_r":
            free_to = (-8, -16)
        elif action == "hurt":
            free_to = (-15, -12)
        elif action == "death":
            free_to = (-6, -2)
        elif action == "walk":
            free_to = (-13, -10 + int(math.sin(phase * 2.2) * 2))
        else:
            free_to = (-14, -9 + int(math.sin(phase * 0.9) * 1.5))
        f_shoulder = (-11, -16)
        f_elbow = G._lerp_pt(f_shoulder, free_to, 0.55)
        sleeve(f_shoulder, f_elbow, max(3, int(4 * sc)))
        sleeve(f_elbow, free_to, max(2, int(3 * sc)))
        bone_hand(free_to)
        # glow tangan saat cast/pulse release
        charging = (action == "attack" and 0.20 <= ap <= 0.55) or \
                   action in ("cast_q", "cast_w", "cast_e", "cast_r")
        if charging:
            hp = P(*free_to)
            k = math.sin(ap * math.pi) if action == "attack" else \
                math.sin(phase * 5.0) * 0.5 + 0.5
            r = int(3 + 3 * k)
            hand_glow = G._cached(
                ("handglow", r), lambda r=r: G._glow_surf(r, c["necro_light"]))
            hand_glow.set_alpha(int(190 * max(0.3, k)))
            surface.blit(hand_glow, (hp[0] - hand_glow.get_width() // 2,
                                     hp[1] - hand_glow.get_height() // 2))
            hand_glow.set_alpha(255)
            pygame.draw.rect(surface, c["necro_bright"],
                             (hp[0] - 1, hp[1] - 1, 2, 2))

    @staticmethod
    def _draw_highlights(surface, bx, by, phase, action):
        """Highlight pixel: rim light + sparks jiwa statis di badan."""
        c = _NS_vhalzun.PALETTE
        # rim kiri torso
        pygame.draw.line(surface, c["robe_light"],
                         (bx - 13, by - 22), (bx - 14, by - 6), 1)
        # dua titik terang di sash
        pygame.draw.rect(surface, c["gold_shine"], (bx - 6, by - 1, 1, 1))
        pygame.draw.rect(surface, c["gold_shine"], (bx + 5, by + 1, 1, 1))
        # bara jiwa naik dari hem (2 pixel berdenyut)
        t = (phase * 0.5) % 1.0
        y0 = by + 34 - int(t * 26)
        a = 1.0 - t
        if a > 0.25:
            pygame.draw.rect(surface, c["necro_light"],
                             (bx - 18 + int(math.sin(phase + 1) * 3), y0, 1, 1))
            pygame.draw.rect(surface, c["necro_hot"],
                             (bx + 16 + int(math.sin(phase) * 3), y0 + 4, 1, 1))

    @staticmethod
    def _draw_flash_hurt(surface, bx, by, flash, facing):
        """Tint putih singkat saat kena damage (hurt_flash_timer)."""
        if flash <= 0:
            return
        overlay = pygame.Surface((52, 84), pygame.SRCALPHA)
        pygame.draw.polygon(overlay, (255, 255, 255, min(90, flash)),
                            [(2, 10), (50, 10), (48, 50), (30, 78),
                             (8, 50)])
        surface.blit(overlay, (bx - 26, by - 44))

    # ===================================================================
    # LAPISAN TANAH (runes + telegraph skill)
    # ===================================================================
    @staticmethod
    def _draw_ground_layer(surface, boss, x, y, phase, skill, owned):
        G = _NS_vhalzun
        c = G.PALETTE
        gy = y + G.GROUND_DY
        # bayangan kontak
        shadow = G._cached("shadow", G._shadow_surf)
        surface.blit(shadow, (x - shadow.get_width() // 2,
                              gy - shadow.get_height() // 2))
        # mist nekrotik (melayang)
        mist = G._cached(("mist", G._qphase(phase, 6)),
                         lambda b=G._qphase(phase, 6): G._mist_surf(b))
        surface.blit(mist, (x - mist.get_width() // 2, gy - 26))
        # rune circle
        rune = G._cached(("rune", G._qphase(phase, 8), bool(skill)),
                         lambda b=G._qphase(phase, 8), s=bool(skill):
                         G._rune_surf(b, s))
        surface.blit(rune, (x - rune.get_width() // 2, gy - 24))
        # telegraph skill di tanah (canvas fallback; versi hidup di
        # vhalzun_fx.draw_ground_layer)
        if not owned and skill:
            prog = float(getattr(boss, "_vhz_skill_progress", 0.0) or 0.0)
            r = int(G.SKILL_RADIUS.get(skill, 130))
            color = c["necro_mid"] if skill in ("q", "w") else c["necro_light"]
            pygame.draw.ellipse(surface, (*color, 120),
                                (x - r, gy - r // 3, r * 2, r * 2 // 3), 2)
            if prog > 0.34:
                pygame.draw.ellipse(
                    surface, (*c["necro_bright"], 150),
                    (x - r + 4, gy - r // 3 + 2,
                     r * 2 - 8, r * 2 // 3 - 4), 1)

    # ===================================================================
    # FALLBACK FX CANVAS (hanya jika modul hidup tidak tersedia)
    # ===================================================================
    @staticmethod
    def _manage_projectiles(boss, surface, phase):
        """Proyektil fallback sederhana (jalur tanpa heroes/vhalzun_fx)."""
        projs = getattr(boss, "_vhz_projectiles", None)
        if not projs:
            return
        c = _NS_vhalzun.PALETTE
        keep = []
        for p in projs:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["age"] += 1
            dist = math.hypot(p["tx"] - p["x"], p["ty"] - p["y"])
            if dist < 8.0 or p["age"] > 140:
                continue
            px, py = int(p["x"]), int(p["y"])
            # orb chunky 3 band
            pygame.draw.circle(surface, c["necro_dark"], (px, py), 7)
            pygame.draw.circle(surface, c["necro_mid"], (px, py), 5)
            pygame.draw.circle(surface, c["necro_light"], (px - 1, py - 1), 3)
            pygame.draw.circle(surface, c["necro_hot"], (px - 1, py - 2), 1)
            keep.append(p)
        boss._vhz_projectiles = keep

    @staticmethod
    def _spawn_fallback_projectile(boss, x, y, scythe=False):
        c = _NS_vhalzun
        if not hasattr(boss, "_vhz_projectiles"):
            boss._vhz_projectiles = []
        if len(boss._vhz_projectiles) >= 12:      # cap keras fallback
            return
        tx, ty = c._target_position(boss, x, y)
        sx = x + 22 * getattr(boss, "direction", 1)
        sy = y - 14
        dx, dy = tx - sx, ty - sy
        d = math.hypot(dx, dy) or 1.0
        speed = 9.0 if scythe else 5.5
        boss._vhz_projectiles.append({
            "x": float(sx), "y": float(sy),
            "vx": dx / d * speed, "vy": dy / d * speed,
            "tx": float(tx), "ty": float(ty), "age": 0})

    # ===================================================================
    # ENTRY POINT
    # ===================================================================
    def draw_vhalzun(surface, boss, x, y):
        """Entry point Boss.draw() sekaligus heroes.render_hero().

        Urutan lapisan (kontrak render order proyek):
          GROUND FX -> SHADOW -> BACK FX -> BODY/ARMOR/HEAD -> WEAPON
          -> ATTACK TRAIL -> PROJECTILE -> FRONT PARTICLES -> SKILL FX
          -> IMPACT FX -> DEBUG.
        Trail ayunan, partikel, proyektil, skill FX, impact, hit-stop,
        dan shake hidup di heroes/vhalzun_fx.py (layar 1:1, di luar
        cache); canvas hanya fallback bila modul itu tidak tersedia.
        """
        NS = _NS_vhalzun
        pulse = float(getattr(boss, "pulse", 0.0))
        portrait = bool(getattr(boss, "_portrait_hd", False))
        hero_lane = hasattr(boss, "_render_scale")

        # ── CONTROLLER ANIMASI ─────────────────────────────────────
        NS._update_vhalzun_anim(boss)
        moving = bool(getattr(boss, "_vhz_moving", False))
        action, phase, ap = NS._resolve_pose(boss, moving)
        boss._vhz_pose_action = action

        # ── LAPISAN HIDUP (ground) ─────────────────────────────────
        live, owned = NS._live_fx(boss, surface, x, y, not hero_lane,
                                  portrait)
        boss._vhz_suppress_canvas_fx = owned

        # ── GROUND: runes + telegraph ──────────────────────────────
        if not portrait:
            NS._draw_ground_layer(surface, boss, x, y, pulse,
                                  getattr(boss, "_vhz_skill", None), owned)

        # ── RIG (komposit satu pose) ───────────────────────────────
        # Konvensi pipeline hero (heroes/__init__): rig SELALU digambar
        # 1:1 di ruang canvas; smoothscale pipeline yang mengecilkan.
        # ``body_scale`` hanya untuk FX ruang layar (scythe_points)
        # dan konversi dunia->canvas (target position).
        facing = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        sc = 1.0
        dx, dy, flare = NS._body_offsets(action, ap, phase, boss)
        # death: dissolve naik + jatuh
        if action == "death":
            age = int(getattr(boss, "_vhz_death_age", 0) or 0)
            dy += min(26.0, age * 0.55)
        bx = x + dx * facing
        by = y - 14 + dy

        # lengan sabit (belakang) => hem => torso => armor => head
        pivot = NS._scythe_pivot_local(action, ap, phase, boss)
        angle = NS._scythe_angle(action, ap, phase, boss)
        glow_k = 0.0
        if action == "swing":
            glow_k = 1.0 if 0.24 <= ap <= 0.60 else 0.45
        elif action == "attack":
            glow_k = 0.9 if 0.28 <= ap <= 0.55 else 0.3
        elif action == "cast_e":
            glow_k = 1.0
        elif action.startswith("cast"):
            glow_k = 0.6

        NS._draw_hem(surface, bx, by + 4, phase, flare, action)
        NS._draw_torso(surface, bx, by, phase, action)
        NS._draw_pauldrons(surface, bx, by, phase, action)
        NS._draw_head(surface, bx, by, facing, phase, action)
        NS._draw_scythe_at(surface, bx, by, sc, facing, angle, pivot,
                           glow_k, pulse)
        NS._draw_arms(surface, bx, by, sc, facing, action, ap, phase, pivot)
        if not portrait:
            NS._draw_highlights(surface, bx, by, pulse, action)

        # flash hurt (di atas semuanya)
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        if flash > 0:
            NS._draw_flash_hurt(surface, bx, by, flash * 6, facing)

        # ── FALLBACK CANVAS FX (jalur boss tanpa modul hidup) ──────
        if not portrait and not owned and not hero_lane:
            kind = NS.attack_kind(boss)
            active = bool(getattr(boss, "_vhz_attack_active", False))
            if active and kind == "pulse" and \
                    not getattr(boss, "_vhz_fallback_spawned", False) and \
                    ap >= NS.ATTACK_RELEASE_FRAME:
                NS._spawn_fallback_projectile(boss, x, y)
                boss._vhz_fallback_spawned = True
            if not active:
                boss._vhz_fallback_spawned = False
            skill = getattr(boss, "_vhz_skill", None)
            if skill == "e" and \
                    not getattr(boss, "_vhz_fallback_scythe", False) and \
                    ap >= 0.42:
                NS._spawn_fallback_projectile(boss, x, y, scythe=True)
                boss._vhz_fallback_scythe = True
            if skill != "e":
                boss._vhz_fallback_scythe = False
            NS._manage_projectiles(boss, surface, pulse)

        # ── LAPISAN HIDUP DI ATAS (trail/proyektil/impact/skill) ───
        if live is not None:
            try:
                live.draw_live_layer(surface, boss, x, y)
            except Exception:
                pass

        # ── DEBUG ──────────────────────────────────────────────────
        if NS.DEBUG_CHARACTER and not portrait:
            NS._draw_vh_debug(surface, boss, x, y)

    # ===================================================================
    # OVERLAY DEBUG (DEBUG_CHARACTER = True)
    # ===================================================================
    _DBG_FONT = None

    @staticmethod
    def _dbg_font(size=12):
        if _NS_vhalzun._DBG_FONT is None or \
                _NS_vhalzun._DBG_FONT.get_height() != size:
            try:
                _NS_vhalzun._DBG_FONT = pygame.font.Font(None, size + 4)
            except Exception:
                _NS_vhalzun._DBG_FONT = pygame.font.Font(None, 16)
        return _NS_vhalzun._DBG_FONT

    @staticmethod
    def _draw_vh_debug(surface, boss, x, y):
        G = _NS_vhalzun
        hb = G._swing_hitbox(boss, x, y)
        if hb is not None:
            pygame.draw.rect(surface, (255, 80, 80), hb, 1)
        hurt = G._hurtbox(boss, x, y)
        pygame.draw.rect(surface, (80, 160, 255), hurt, 1)
        pygame.draw.circle(surface, (255, 200, 60),
                           (x, y), int(G.MELEE_REACH), 1)
        pv, tip = G.scythe_points(boss, x, y)
        pygame.draw.circle(surface, (90, 255, 90), (int(pv.x), int(pv.y)), 3, 1)
        pygame.draw.circle(surface, (90, 255, 90), (int(tip.x), int(tip.y)), 3, 1)
        pygame.draw.line(surface, (90, 255, 90),
                         (int(pv.x), int(pv.y)), (int(tip.x), int(tip.y)), 1)
        try:
            clock = pygame.time.Clock()
            fps = int(clock.get_fps())
        except Exception:
            fps = 0
        lines = [
            f"VHALZUN  state={getattr(boss, '_vhz_state', 'IDLE')}",
            f"pose={getattr(boss, '_vhz_pose_action', '-')} "
            f"kind={G.attack_kind(boss)} "
            f"phase={getattr(boss, '_vhz_attack_phase', '-')}",
            f"atk_t={float(getattr(boss, '_vhz_attack_progress', 0.0)):.2f} "
            f"hit={bool(getattr(boss, '_vhz_hit_active', False))}",
            f"skill={getattr(boss, '_vhz_skill', '-')} "
            f"t={float(getattr(boss, '_vhz_skill_progress', 0.0)):.2f}",
            f"fps~{fps}",
        ]
        font = G._dbg_font()
        yy = y - 96
        for ln in lines:
            img = font.render(ln, True, (180, 255, 180))
            surface.blit(img, (x - 90, yy))
            yy += 13

    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_vhalzun.draw_vhalzun(surface, boss, x, y)


# ====================================================================
# KROBELLUS — THE DEATH PROPHET  (FULL REWRITE)
# ====================================================================
# Arsitektur "masterwork" (patron: gornak/nyzrak di level1/level3):
#
#   * RENDERER (file ini) — rig pixel-art + pose + telegraph tanah.
#     Semua bentuk digambar prosedural (pygame.draw) dengan palet
#     terbatas, tepi tajam (tanpa anti-aliasing), dan surface statis
#     di-cache (bayangan, mist, rune circle, sprite hantu).
#   * LAPISAN HIDUP (heroes/krobellus_fx.py) — trail sabit, partikel
#     jiwa, proyektil soul bolt, FX skill Q/W/E/R, impact flash,
#     screen shake, hit-stop 0.03-0.08 s. Digambar 1:1 ke layar,
#     di luar cache sprite supaya tetap hidup 60 fps.
#   * GAME FEEL BUS (heroes/combat_feel.py) — satu sumber hit-stop &
#     shake untuk seluruh arena.
#
# Kontrak publik (dipakai heroes/__init__, bosses/base_boss, hero_skills,
# tools, dan modul FX):
#   draw_krobellus(surface, boss, x, y)   entry point (Boss.draw & render_hero)
#   PALETTE                               palet karakter + FX (sumber benar)
#   pose_of / anim_state / attack_phase   state animasi (sinkron dengan FX)
#   scythe_points(boss, x, y)             (pivot, tip) Vector2 ruang layar
#   body_scale / ground_dy                skala & garis tanah
#   DEBUG_CHARACTER                       overlay hitbox/hurtbox/state
# ====================================================================
class _NS_krobellus:
    """Namespace krobellus — renderer Death Prophet (full rewrite)."""

    # ------------------------------------------------------------------
    # PALETTE — dark fantasy: jubah ungu gelap, cahaya jiwa teal,
    # void ungu, trim emas, mata api merah. Kunci identik dengan
    # heroes/krobellus_fx.KROBELLS_PALETTE (modul FX menyalin dari sini).
    # ------------------------------------------------------------------
    PALETTE = {
        "outline":      (10,   6,  18),
        "shadow_deep":  (18,   8,  30),
        "shadow":       (30,  15,  48),
        "robe_dark":    (44,  24,  70),
        "robe_mid":     (70,  40, 106),
        "robe_light":   (106, 66, 152),
        "robe_shine":   (148, 106, 196),
        "robe_fade":    (24,  12,  40),
        "armor_dark":   (26,  13,  44),
        "armor_mid":    (56,  32,  86),
        "armor_light":  (92,  58, 130),
        "skin_dark":    (140, 148, 148),
        "skin_mid":     (188, 202, 198),
        "skin_light":   (226, 238, 232),
        "skin_shine":   (244, 252, 248),
        "soul_dark":    (18,  72,  68),
        "soul_mid":     (46, 148, 134),
        "soul_light":   (96, 216, 194),
        "soul_bright":  (168, 250, 232),
        "soul_hot":     (228, 255, 248),
        "soul_white":   (250, 255, 252),
        "void_dark":    (40,  14,  74),
        "void_mid":     (86,  34, 148),
        "void_light":   (142, 74, 208),
        "void_bright":  (196, 130, 244),
        "void_hot":     (236, 192, 255),
        "gold_dark":    (98,  64,  20),
        "gold_mid":     (178, 132,  40),
        "gold_light":   (238, 196,  84),
        "gold_shine":   (255, 236, 156),
        "eye_dark":     (96,  18,  28),
        "eye_mid":      (190, 44,  54),
        "eye_bright":   (240, 96,  86),
        "eye_hot":      (255, 168, 150),
        "scythe_dark":  (36,  30,  48),
        "scythe_mid":   (92,  84, 116),
        "scythe_light": (168, 160, 196),
        "fx_white":     (245, 250, 252),
    }

    # ------------------------------------------------------------------
    # KONSTANTA RIG (ruang lokal: y=0 = pusat badan, + ke bawah;
    # garis tanah +GROUND_DY; facing kanan, cermin untuk facing kiri)
    # ------------------------------------------------------------------
    GROUND_DY = 48
    HEAD_Y = -40
    SHOULDER_Y = -28
    BELT_Y = -10
    HEM_TOP = -8
    HEM_BOT = 42
    HOOD_R = 14
    FACE_R = 8
    # Sabit: panjang batang dari genggaman ke hub bilah
    SCYTHE_SHAFT = 40
    SCYTHE_R_OUT = 24
    SCYTHE_R_IN = 16
    SCYTHE_TIP_OFF = 0.42     # offset sudut ujung luar bilah dari θ
    # Jangkauan dunia (px) untuk memilih swing vs soul bolt
    MELEE_REACH = 110.0
    # Jendela aktif ayunan (busur bilah menyapu depan badan)
    ATTACK_ACTIVE_WINDOW = (0.30, 0.52)
    ATTACK_IMPACT_FRAME = 0.46
    ATTACK_RELEASE_FRAME = 0.52

    # ------------------------------------------------------------------
    # TIMELINE SERANGAN (fraksi durasi; patahan = kurva pose)
    # ------------------------------------------------------------------
    ATTACK_ANTICIPATION_END = 0.12
    ATTACK_WINDUP_END = 0.26
    ATTACK_SWING_END = 0.42
    ATTACK_IMPACT_END = 0.52
    ATTACK_FOLLOW_END = 0.72

    ATTACK_PHASES = (
        ("ANTICIPATION", 0.00, 0.12),
        ("WINDUP",       0.12, 0.26),
        ("SWING",        0.26, 0.42),
        ("IMPACT",       0.42, 0.52),
        ("FOLLOW",       0.52, 0.72),
        ("RECOVERY",     0.72, 1.00),
    )

    # Prioritas state. Angka besar menang; DEATH mengunci.
    ANIM_STATES = {
        "IDLE": 0,
        "WALK": 10,
        "RUN": 15,
        "CHARGE": 30,
        "CAST": 35,
        "ATTACK": 40,
        "SWING": 45,
        "HIT": 48,
        "SKILL": 50,
        "SPECIAL": 55,
        "HURT": 65,
        "DEATH": 100,
    }

    #: Overlay debug (jalur boss 1:1). Jalur lane: krobellus_fx.DEBUG_CHARACTER.
    DEBUG_CHARACTER = False

    # ==================================================================
    # UTIL
    # ==================================================================
    @staticmethod
    def _alpha(a):
        return int(max(0, min(255, int(a))))

    @staticmethod
    def _ease_out_quad(t):
        t = max(0.0, min(1.0, t))
        return 1.0 - (1.0 - t) ** 2

    @staticmethod
    def _ease_in_quad(t):
        t = max(0.0, min(1.0, t))
        return t * t

    @staticmethod
    def _ease_out_cubic(t):
        t = max(0.0, min(1.0, t))
        return 1.0 - (1.0 - t) ** 3

    @staticmethod
    def _ease_in_cubic(t):
        t = max(0.0, min(1.0, t))
        return t ** 3

    @staticmethod
    def _ease_in_out_sine(t):
        t = max(0.0, min(1.0, t))
        return -(math.cos(math.pi * t) - 1.0) / 2.0

    @staticmethod
    def _ease_in_out_cubic(t):
        t = max(0.0, min(1.0, t))
        return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2

    @staticmethod
    def _lerp(a, b, t):
        if isinstance(a, tuple):
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        return a + (b - a) * t

    @staticmethod
    def _keyframes(kfs, p, eases):
        """Interpolasi keyframe [(p, value), ...] dengan easing per segmen."""
        p = max(0.0, min(1.0, p))
        if p <= kfs[0][0]:
            return kfs[0][1]
        for i in range(len(kfs) - 1):
            p0, v0 = kfs[i]
            p1, v1 = kfs[i + 1]
            if p0 <= p <= p1:
                t = (p - p0) / max(1e-6, (p1 - p0))
                return _NS_krobellus._lerp(v0, v1, eases[i](t))
        return kfs[-1][1]

    # ==================================================================
    # API SKALA (dipakai modul FX & tools)
    # ==================================================================
    @staticmethod
    def body_scale(boss):
        sc = getattr(boss, "_render_scale", 1.0)
        try:
            sc = float(sc)
        except (TypeError, ValueError):
            sc = 1.0
        return sc if sc > 0.01 else 1.0

    @staticmethod
    def ground_dy(boss):
        return float(_NS_krobellus.GROUND_DY) * _NS_krobellus.body_scale(boss)

    # ==================================================================
    # ANIMATION CONTROLLER
    # ==================================================================
    def attack_phases_order():
        """Urutan nama fase (dipakai test & alat audit)."""
        return tuple(name for name, _a, _b in _NS_krobellus.ATTACK_PHASES)

    def attack_phase(progress):
        """Nama fase serangan untuk progress 0..1 (None di luar serangan)."""
        if progress is None:
            return "NONE"
        p = max(0.0, min(1.0, float(progress)))
        for name, a, b in _NS_krobellus.ATTACK_PHASES:
            if a <= p < b:
                return name
        return "RECOVERY"

    def attack_progress(boss):
        return float(getattr(boss, "_krb_attack_progress", 0.0) or 0.0)

    def _resolve_anim_state(boss, attacking, phase):
        """Tentukan state animasi yang DIINGINKAN frame ini."""
        if not getattr(boss, "alive", True):
            return "DEATH"
        if int(getattr(boss, "_krb_hurt_frames", 0)) > 0 and not attacking:
            return "HURT"
        skill = getattr(boss, "_krb_skill", None)
        if skill:
            return "SPECIAL" if skill == "r" else "SKILL"
        if attacking:
            kind = getattr(boss, "_krb_attack_kind", "swing")
            if phase in ("ANTICIPATION", "WINDUP"):
                return "CHARGE"
            if phase in ("SWING", "IMPACT"):
                if bool(getattr(boss, "_krb_hit_active", False)):
                    return "HIT"
                return "SWING" if kind == "swing" else "CAST"
            return "ATTACK"
        if getattr(boss, "_moving_cached", False):
            return "RUN" if float(getattr(boss, "speed", 1.0) or 1.0) >= 2.2 \
                else "WALK"
        return "IDLE"

    def _update_krb_anim(boss):
        """ANIMATION CONTROLLER Krobellus — satu sumber kebenaran state.

        Menulis ke ``boss``:
          * ``_krb_dt``                delta-time nyata (detik, dijepit)
          * ``_krb_attack_active``     serangan sedang berjalan
          * ``_krb_attack_frame``      frame ke-n dalam serangan
          * ``_krb_attack_progress``   0..1 sepanjang serangan
          * ``_krb_attack_raw``        progress sebelum remap
          * ``_krb_attack_kind``       'swing' | 'bolt' (diputuskan saat
                                       serangan mulai, dari jarak target)
          * ``_krb_attack_phase``      ANTICIPATION..RECOVERY
          * ``_krb_hit_active``        True hanya di jendela hit aktif
          * ``_krb_hurt_frames``       sisa frame respons kena damage
          * ``_krb_skill``             'q'/'w'/'e'/'r' (None = tidak ada)
          * ``_krb_skill_progress``    0..1 sepanjang skill
          * ``_krb_state`` / ``_krb_state_prev`` / ``_krb_state_time``
          * ``_krb_death_age``         umur frame pose kematian
        """
        G = _NS_krobellus

        # ── delta time nyata ─────────────────────────────────────────
        try:
            now = pygame.time.get_ticks()
        except Exception:                          # pragma: no cover
            now = 0
        prev_ms = getattr(boss, "_krb_last_ms", None)
        if prev_ms is None:
            dt = 1.0 / 60.0
        else:
            dt = (now - prev_ms) / 1000.0
            if dt <= 0.0 or dt > 0.05:
                dt = 1.0 / 60.0
        boss._krb_last_ms = now
        boss._krb_dt = dt

        # ── timeline serangan ────────────────────────────────────────
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 46)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_krb_prev_timer", 0))
        active = bool(getattr(boss, "_krb_attack_active", False))

        triggered = timer >= cooldown - 1 and previous <= 1
        if triggered:
            boss._krb_attack_active = True
            boss._krb_attack_frame = 0
            boss._krb_attack_manual = False
            # PUTUSKAN JENIS: target dekat -> SWING (sabit), jauh -> BOLT
            tgt = getattr(boss, "target", None)
            if tgt is not None and getattr(tgt, "alive", True):
                dist = math.hypot(
                    float(getattr(tgt, "x", 0.0)) - float(getattr(boss, "x", 0.0)),
                    float(getattr(tgt, "y", 0.0)) - float(getattr(boss, "y", 0.0)))
            else:
                dist = 1e9
            boss._krb_attack_kind = "swing" if dist <= G.MELEE_REACH else "bolt"
            active = True
        elif active and timer > 0:
            boss._krb_attack_frame = int(getattr(boss, "_krb_attack_frame",
                                                 0)) + 1
            boss._krb_attack_manual = False
        elif timer <= 0:
            if active and not getattr(boss, "_krb_attack_manual", False) \
                    and float(getattr(boss, "_krb_attack_progress", 0.0)) > 0.0:
                # pemanggil eksternal menggerakkan progress manual (alat
                # audit/test) — hormati, tandai manual
                boss._krb_attack_manual = True
                active = True
            elif not getattr(boss, "_krb_attack_manual", False):
                boss._krb_attack_active = False
                boss._krb_attack_frame = 0
                active = False
            if not active:
                boss._krb_attack_active = False
                boss._krb_attack_frame = 0

        boss._krb_prev_timer = timer
        frame = int(getattr(boss, "_krb_attack_frame", 0)) if active else 0
        span = max(1, cooldown - 1)
        boss._krb_attack_frame = frame
        if bool(getattr(boss, "_krb_attack_manual", False)) and active:
            progress = min(1.0, max(0.0, float(getattr(
                boss, "_krb_attack_progress", 0.0))))
            boss._krb_attack_frame = int(round(progress * span))
        else:
            progress = min(1.0, frame / float(span)) if active else 0.0
            boss._krb_attack_progress = progress
        boss._krb_attack_raw = progress

        # ── fase + jendela hit ───────────────────────────────────────
        if not getattr(boss, "_krb_attack_active", False):
            boss._krb_attack_active = False
            boss._krb_attack_manual = False
            active = False
        phase = G.attack_phase(progress) if active else "NONE"
        boss._krb_attack_phase = phase
        lo, hi = G.ATTACK_ACTIVE_WINDOW
        boss._krb_hit_active = bool(active and lo <= progress < hi)

        # ── respons kena damage (HURT) ───────────────────────────────
        hurt = int(getattr(boss, "_krb_hurt_frames", 0))
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        if flash >= 8 and hurt <= 0:
            hurt = 10
        boss._krb_hurt_frames = max(0, hurt - 1) if hurt > 0 else 0

        # ── skill (active_skill; jalur boss generik: ability -> 'q') ──
        skill = getattr(boss, "active_skill", None)
        if skill is None and getattr(boss, "ability_active", False) \
                and int(getattr(boss, "ability_active_timer", 0) or 0) > 0:
            skill = "q"
        timer_s = 0
        if skill:
            timer_s = int(getattr(boss, "active_skill_timer", 0) or 0)
            if timer_s <= 0 and getattr(boss, "active_skill", None) is None:
                timer_s = int(getattr(boss, "ability_active_timer", 0) or 0)
        prev_skill = getattr(boss, "_krb_skill_prev", None)
        if skill != prev_skill:
            if skill is not None and timer_s > 0:
                boss._krb_skill_total = max(1, timer_s)
        elif skill is not None and timer_s > 0:
            boss._krb_skill_total = max(int(getattr(boss, "_krb_skill_total",
                                                   60)), timer_s)
        boss._krb_skill_prev = skill
        boss._krb_skill = skill
        boss._krb_skill_timer = timer_s
        total = int(getattr(boss, "_krb_skill_total", 60) or 60)
        boss._krb_skill_progress = (
            max(0.0, min(1.0, 1.0 - timer_s / float(max(1, total))))
            if skill is not None else 0.0)

        # ── kematian (jalur probe/test; in-game Boss.draw skip mati) ──
        if not getattr(boss, "alive", True):
            boss._krb_death_age = int(getattr(boss, "_krb_death_age", 0)) + 1

        # ── state machine ber-prioritas ─────────────────────────────
        want = G._resolve_anim_state(boss, active, phase)
        cur = getattr(boss, "_krb_state", None)
        if cur is None:
            boss._krb_state = want
            boss._krb_state_prev = want
            boss._krb_state_time = 0.0
        elif want != cur:
            cur_p = G.ANIM_STATES.get(cur, 0)
            new_p = G.ANIM_STATES.get(want, 0)
            stime = float(getattr(boss, "_krb_state_time", 0.0))
            if cur != "DEATH" and (new_p >= cur_p or stime > 0.08):
                boss._krb_state_prev = cur
                boss._krb_state = want
                boss._krb_state_time = 0.0
            else:
                boss._krb_state_time = stime + dt
        else:
            boss._krb_state_time = float(getattr(boss, "_krb_state_time",
                                                 0.0)) + dt

    def _detect_moving(boss):
        cur_x = float(getattr(boss, "x", 0.0))
        cur_y = float(getattr(boss, "y", 0.0))
        if not hasattr(boss, "_krb_last_x"):
            boss._krb_last_x = cur_x
            boss._krb_last_y = cur_y
            boss._moving_cached = False
            return False
        moved = abs(cur_x - boss._krb_last_x) + abs(cur_y - boss._krb_last_y)
        boss._krb_last_x = cur_x
        boss._krb_last_y = cur_y
        moving = moved > 0.3
        boss._moving_cached = moving
        return moving

    # ==================================================================
    # POSE STATE — satu sumber kebenaran untuk rig DAN semua FX
    # ==================================================================
    ACTIONS = ("idle", "walk", "attack", "spin", "cast_w", "cast_e",
               "slam", "hurt", "death")

    def _resolve_pose(boss, moving=False):
        """(action, phase, ap) — murni, boleh dipanggil ulang oleh FX."""
        if not getattr(boss, "alive", True):
            return ("death", float(getattr(boss, "pulse", 0.0)), 0.0)
        skill = getattr(boss, "_krb_skill", None)
        attacking = bool(getattr(boss, "_krb_attack_active", False))
        if skill is not None:
            if skill == "q":
                action = "spin"
            elif skill == "w":
                action = "cast_w"
            elif skill == "e":
                action = "cast_e"
            else:
                action = "slam"
        elif attacking:
            action = "attack"
        elif int(getattr(boss, "_krb_hurt_frames", 0)) > 0:
            action = "hurt"
        elif moving:
            action = "walk"
        else:
            action = "idle"
        phase = float(getattr(boss, "pulse", 0.0))
        if action == "walk":
            phase *= 1.0        # fase sudah cukup cepat dari pulse engine
        ap = 0.0
        if action == "attack":
            ap = max(0.0, min(1.0,
                              float(getattr(boss, "_krb_attack_progress",
                                            0.0))))
        return action, phase, ap

    def pose_of(boss):
        """Publik: pose tersimpan (dipakai modul FX tanpa efek samping)."""
        if not getattr(boss, "alive", True):
            return ("death", float(getattr(boss, "pulse", 0.0)), 0.0)
        skill = getattr(boss, "_krb_skill", None)
        if skill is not None:
            action = {"q": "spin", "w": "cast_w", "e": "cast_e",
                      "r": "slam"}.get(skill, "idle")
            return (action, float(getattr(boss, "pulse", 0.0)),
                    float(getattr(boss, "_krb_skill_progress", 0.0) or 0.0))
        if getattr(boss, "_krb_attack_active", False):
            return ("attack", float(getattr(boss, "pulse", 0.0)),
                    float(getattr(boss, "_krb_attack_progress", 0.0) or 0.0))
        if getattr(boss, "_moving_cached", False):
            return ("walk", float(getattr(boss, "pulse", 0.0)), 0.0)
        return ("idle", float(getattr(boss, "pulse", 0.0)), 0.0)

    def anim_state(boss):
        """Publik: nama state animasi aktif (IDLE/WALK/.../DEATH)."""
        return str(getattr(boss, "_krb_state", "IDLE"))

    # ==================================================================
    # GEOMETRI SABIT (ruang lokal facing-kanan; cermin via x*facing)
    # ==================================================================
    _SCYTHE_REST = 1.10

    def _scythe_pivot_local(action, ap, phase, boss=None):
        """Posisi genggaman (pivot sabit) ruang lokal, per pose."""
        if action == "spin":
            return (12, -16)
        if action == "cast_w":
            return (15, -18)
        if action == "cast_e":
            return (16, -18)
        if action == "slam":
            if ap < 0.35:
                return _NS_krobellus._lerp_pt((12, -20), (13, -30),
                                               _NS_krobellus._ease_out_cubic(ap / 0.35))
            return (13, -16)
        if action == "hurt":
            return (10, -19)
        if action == "death":
            return (12, 8)
        if action == "attack":
            kind = getattr(boss, "_krb_attack_kind", "swing") if boss \
                else "swing"
            if kind == "bolt":
                kfs = ((0.0, (11, -20)), (0.12, (9, -21)),
                       (0.34, (12, -24)), (0.52, (14, -22)),
                       (1.0, (11, -20)))
                return _NS_krobellus._keyframes(
                    kfs, ap,
                    (_NS_krobellus._ease_out_quad,
                     _NS_krobellus._ease_out_cubic,
                     _NS_krobellus._ease_in_out_sine,
                     _NS_krobellus._ease_in_out_sine))
            kfs = ((0.0, (11, -20)), (0.12, (9, -21)),
                   (0.42, (13, -18)), (1.0, (11, -20)))
            p = _NS_krobellus._keyframes(
                kfs, ap,
                (_NS_krobellus._ease_out_quad,
                 _NS_krobellus._ease_in_out_sine,
                 _NS_krobellus._ease_in_out_sine))
            return p
        # idle / walk
        bob = math.sin(phase * 0.8) * 0.8
        return (11, -20 + bob)

    @staticmethod
    def _lerp_pt(a, b, t):
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

    def _scythe_angle(action, ap, phase, boss=None):
        """Sudut sabit θ (rad, ruang lokal, y ke bawah)."""
        if action == "death":
            age = min(1.0, (int(getattr(boss, "_krb_death_age", 0) or 0))
                      / 30.0) if boss else 1.0
            return _NS_krobellus._lerp(_NS_krobellus._SCYTHE_REST, 1.57,
                                       _NS_krobellus._ease_in_out_cubic(age))
        if action == "hurt":
            return _NS_krobellus._SCYTHE_REST + 0.22 * math.sin(phase * 6.0)
        if action == "spin":
            t = min(1.0, ap / 0.55)
            if t < 1.0:
                return _NS_krobellus._SCYTHE_REST + \
                    4.6 * _NS_krobellus._ease_in_out_cubic(t)
            t2 = max(0.0, min(1.0, (ap - 0.55) / 0.45))
            return _NS_krobellus._lerp(_NS_krobellus._SCYTHE_REST + 4.6,
                                       _NS_krobellus._SCYTHE_REST + 2 *
                                       math.pi,
                                       _NS_krobellus._ease_in_out_sine(t2))
        if action == "cast_w":
            return _NS_krobellus._lerp(_NS_krobellus._SCYTHE_REST, 1.52,
                                       _NS_krobellus._ease_out_cubic(
                                           min(1.0, ap / 0.35)))
        if action == "cast_e":
            return _NS_krobellus._lerp(_NS_krobellus._SCYTHE_REST, 1.58,
                                       _NS_krobellus._ease_out_cubic(
                                           min(1.0, ap / 0.35)))
        if action == "slam":
            if ap < 0.30:
                return _NS_krobellus._lerp(_NS_krobellus._SCYTHE_REST,
                                           -2.50,
                                           _NS_krobellus._ease_in_out_cubic(
                                               ap / 0.30))
            if ap < 0.38:
                return _NS_krobellus._lerp(-2.50, 1.57,
                                           _NS_krobellus._ease_in_quad(
                                               (ap - 0.30) / 0.08))
            if ap < 0.70:
                return 1.57 + 0.05 * math.sin(phase * 9.0)
            return _NS_krobellus._lerp(1.57, _NS_krobellus._SCYTHE_REST,
                                       _NS_krobellus._ease_in_out_sine(
                                           (ap - 0.70) / 0.30))
        if action == "attack":
            kind = getattr(boss, "_krb_attack_kind", "swing") if boss \
                else "swing"
            if kind == "bolt":
                kfs = ((0.0, _NS_krobellus._SCYTHE_REST),
                       (0.12, 1.45), (0.34, -0.90), (0.52, -0.85),
                       (0.72, 0.40), (1.0, _NS_krobellus._SCYTHE_REST))
                base = _NS_krobellus._keyframes(
                    kfs, ap,
                    (_NS_krobellus._ease_out_quad,
                     _NS_krobellus._ease_out_cubic,
                     _NS_krobellus._ease_in_out_sine,
                     _NS_krobellus._ease_in_out_sine,
                     _NS_krobellus._ease_in_out_sine))
                if 0.34 <= ap < 0.52:      # gemetar saat orb terkumpul
                    base += 0.05 * math.sin(phase * 10.0)
                return base
            # SWING — busur penuh khas sabit: sapu di bawah-behind,
            # naik di belakang kepala, lalu tebasan depan-bawah.
            # (konvensi: 0=depan, +pi/2=bawah, -pi/2=atas, pi=belakang)
            kfs = ((0.0, _NS_krobellus._SCYTHE_REST),
                   (0.12, 1.50),        # antisipasi: tarik ke bawah
                   (0.34, -2.45),       # wind-up: di belakang kepala
                   (0.46, 0.75),        # sapu selesai = frame benturan
                   (0.52, 0.90),        # overshoot impact
                   (0.72, 1.30),        # follow-through
                   (1.0, _NS_krobellus._SCYTHE_REST))
            return _NS_krobellus._keyframes(
                kfs, ap,
                (_NS_krobellus._ease_out_quad,    # pull-back
                 _NS_krobellus._ease_in_out_cubic,  # lift halus
                 _NS_krobellus._ease_in_quad,     # tebasan dipercepat
                 _NS_krobellus._ease_out_quad,    # stop + overshoot
                 _NS_krobellus._ease_in_out_sine,
                 _NS_krobellus._ease_in_out_sine))
        # idle / walk — sway pelan
        return _NS_krobellus._SCYTHE_REST + 0.09 * math.sin(phase * 0.8)

    def _scythe_hub_local(action, ap, phase, boss=None):
        p = _NS_krobellus._scythe_pivot_local(action, ap, phase, boss)
        th = _NS_krobellus._scythe_angle(action, ap, phase, boss)
        L = _NS_krobellus.SCYTHE_SHAFT
        return (p[0] + L * math.cos(th), p[1] + L * math.sin(th)), th

    @staticmethod
    def _map(cx, cy, sc, facing, lx, ly):
        """Ruang lokal -> ruang layar (cermin x saat facing kiri)."""
        return (int(cx + lx * facing * sc), int(cy + ly * sc))

    def scythe_points(boss, x, y):
        """(pivot, tip) pygame.Vector2 ruang LAYAR. Dipakai modul FX
        (trail sabit, titik lahir bolt) dan overlay debug."""
        action, phase, ap = _NS_krobellus.pose_of(boss)
        facing = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        sc = _NS_krobellus.body_scale(boss)
        p = _NS_krobellus._scythe_pivot_local(action, ap, phase, boss)
        hub, th = _NS_krobellus._scythe_hub_local(action, ap, phase, boss)
        tip_l = (hub[0] + _NS_krobellus.SCYTHE_R_OUT *
                 math.cos(th + _NS_krobellus.SCYTHE_TIP_OFF),
                 hub[1] + _NS_krobellus.SCYTHE_R_OUT *
                 math.sin(th + _NS_krobellus.SCYTHE_TIP_OFF))
        pivot = pygame.Vector2(x + p[0] * facing * sc, y + p[1] * sc)
        tip = pygame.Vector2(x + tip_l[0] * facing * sc, y + tip_l[1] * sc)
        return (pivot, tip)

    def _swing_hitbox(boss, cx, cy):
        """Rect hitbox ayunan (ruang permukaan) saat jendela hit aktif."""
        if not getattr(boss, "_krb_hit_active", False):
            return None
        f = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        sc = _NS_krobellus.body_scale(boss)
        reach = int(_NS_krobellus.MELEE_REACH * 0.85 * sc)
        top = int(cy - 34 * sc)
        h = int(64 * sc)
        left = int(cx) if f > 0 else int(cx) - reach
        return pygame.Rect(left, top, max(8, reach), max(10, h))

    # ==================================================================
    # CACHE SURFACE STATIS (dibangun sekali)
    # ==================================================================
    _CACHE = {}

    def clear_cache():
        _NS_krobellus._CACHE.clear()

    def _cached(key, builder):
        s = _NS_krobellus._CACHE.get(key)
        if s is None:
            s = builder()
            _NS_krobellus._CACHE[key] = s
        return s

    @staticmethod
    def _shadow_surf():
        """Bayangan kontak (gradient ellipse chunky)."""
        w, h = 104, 22
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        for i in range(9, 0, -1):
            a = max(0, (9 - i) * 17)
            pygame.draw.ellipse(s, (0, 0, 0, a),
                                (12 + i, 11 - i, w - 24 - i * 2, i * 2))
        pygame.draw.ellipse(s, (*_NS_krobellus.PALETTE["soul_dark"], 70),
                            (14, 6, w - 28, 10))
        return s

    @staticmethod
    def _mist_surf():
        """Mist spectral di bawah jubah (teal lembut)."""
        w, h = 150, 46
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        c = _NS_krobellus.PALETTE
        for i in range(10, 0, -1):
            a = max(0, (10 - i) * 14)
            pygame.draw.ellipse(s, (*c["soul_dark"], a),
                                (15 + i * 2, 23 - i, w - 30 - i * 4, i * 2))
        for i in range(6):
            a = 60 - i * 8
            pygame.draw.ellipse(s, (*c["soul_mid"], max(8, a)),
                                (30 + i * 4, 20 - i, w - 60 - i * 8, 4 + i))
        return s

    @staticmethod
    def _rune_surf():
        """Cincin rune necromantic (dasar statis; tick animasi live)."""
        w, h = 168, 60
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        c = _NS_krobellus.PALETTE
        cx, cy = w // 2, h // 2
        pygame.draw.ellipse(s, (*c["soul_dark"], 150), (8, 12, w - 16, h - 24), 3)
        pygame.draw.ellipse(s, (*c["soul_mid"], 130), (30, 20, w - 60, h - 40), 2)
        pygame.draw.ellipse(s, (*c["soul_light"], 90), (52, 28, w - 104, h - 56), 1)
        # rune marks (segmen pendek mengelilingi)
        for i in range(12):
            a = i * math.tau / 12
            r1, r2 = 0.78, 0.92
            p1 = (cx + math.cos(a) * (w / 2 - 12) * r1,
                  cy + math.sin(a) * (h / 2 - 14) * r1 * 0.42)
            p2 = (cx + math.cos(a) * (w / 2 - 12) * r2,
                  cy + math.sin(a) * (h / 2 - 14) * r2 * 0.42)
            pygame.draw.line(s, (*c["soul_bright"], 140), p1, p2, 1)
        return s

    @staticmethod
    def _ghost_surf(size):
        """Sprite hantu mini (untuk pendamping) — pixel art chunky."""
        n = max(4, int(size))
        w = n * 2 + 6
        h = n * 2 + 8
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        c = _NS_krobellus.PALETTE
        cx = w // 2
        top = n
        pts = [
            (cx - n, top + 2), (cx - n + 2, top - 2 + 1), (cx - 1, top),
            (cx + n - 3, top - 1), (cx + n, top + 2),
            (cx + n - 1, top + n - 2), (cx + n // 2, top + n - 4),
            (cx - n // 2, top + n - 3), (cx - n + 1, top + n - 2),
        ]
        pygame.draw.polygon(s, (*c["soul_dark"], 255), pts)
        inner = [
            (cx - n + 3, top + 2), (cx - n + 4, top + 1), (cx, top),
            (cx + n - 4, top + 1), (cx + n - 3, top + 3),
            (cx + n - 4, top + n - 4), (cx, top + n - 3),
            (cx - n + 4, top + n - 4),
        ]
        pygame.draw.polygon(s, (*c["soul_mid"], 255), inner)
        off = max(2, n // 3)
        pygame.draw.circle(s, (*c["soul_dark"], 255), (cx - off, top), 1)
        pygame.draw.circle(s, (*c["soul_dark"], 255), (cx + off, top), 1)
        pygame.draw.circle(s, (*c["soul_bright"], 255), (cx - off, top), 1)
        pygame.draw.circle(s, (*c["soul_hot"], 255), (cx + off, top), 1)
        return s

    def _glow_surf(radius, color):
        key = ("glow", int(radius), tuple(color))
        return _NS_krobellus._cached(key, lambda: (
            (lambda s: (pygame.draw.circle(
                s, (*color, 60), (int(radius) + 1, int(radius) + 1),
                int(radius)),
                pygame.draw.circle(
                    s, (*color, 110), (int(radius) + 1, int(radius) + 1),
                    max(1, int(radius * 0.6))),
                pygame.draw.circle(
                    s, (255, 255, 255, 140),
                    (int(radius) + 1, int(radius) + 1),
                    max(1, int(radius * 0.25))),
                s)[3])(pygame.Surface((radius * 2 + 2, radius * 2 + 2),
                                       pygame.SRCALPHA))))

    # ==================================================================
    # LAPISAN TANAH (ground)
    # ==================================================================
    def _draw_shadow(surface, x, y):
        s = _NS_krobellus._shadow_surf()
        surface.blit(s, (int(x - s.get_width() / 2),
                         int(y + _NS_krobellus.GROUND_DY - s.get_height() / 2)))

    def _draw_mist(surface, x, y, phase):
        s = _NS_krobellus._mist_surf()
        k = int(200 + 40 * math.sin(phase * 1.0))
        s.set_alpha(k)
        surface.blit(s, (int(x - s.get_width() / 2),
                         int(y + 24 - s.get_height() / 2)))
        s.set_alpha(255)

    def _draw_rune_circle(surface, x, y, phase, skill=None):
        s = _NS_krobellus._rune_surf()
        surface.blit(s, (int(x - s.get_width() / 2),
                         int(y + _NS_krobellus.GROUND_DY - 14)))
        # tick berputar (3 penanda live)
        c = _NS_krobellus.PALETTE
        cx = int(x)
        cy = int(y + _NS_krobellus.GROUND_DY - 2)
        for i in range(3):
            a = phase * 0.35 + i * math.tau / 3
            x1 = cx + math.cos(a) * 56
            y1 = cy + math.sin(a) * 13
            x2 = cx + math.cos(a) * 74
            y2 = cy + math.sin(a) * 17
            pygame.draw.line(surface, (*c["soul_bright"], 120),
                             (int(x1), int(y1)), (int(x2), int(y2)), 1)
        if skill:
            a = int(90 + 60 * math.sin(phase * 2.0))
            pygame.draw.ellipse(surface, (*c["soul_hot"], max(30, a)),
                                (int(x - 62), int(y + _NS_krobellus.GROUND_DY - 14),
                                 124, 28), 1)

    def _draw_companions(surface, x, y, phase, facing, front=False,
                         intense=False):
        """Hantu pendamping kecil mengorbit (2 belakang, 1 depan)."""
        c = _NS_krobellus.PALETTE
        idxs = (0, 1) if not front else (2,)
        for k, idx in enumerate(idxs):
            a = phase * 0.55 + idx * math.tau / 3
            rx = 40 + math.sin(phase * 0.8 + idx * 1.7) * 7
            ry = 16 + math.sin(phase * 0.6 + idx) * 4
            px = x + math.cos(a) * rx * facing
            py = y - 22 + math.sin(a) * ry + math.sin(phase * 2.0 + idx) * 2
            size = 7 if (intense or idx == 1) else 6
            spr = _NS_krobellus._cached(("ghost", size),
                                        lambda sz=size: _NS_krobellus._ghost_surf(sz))
            spr.set_alpha(170 if not intense else 220)
            surface.blit(spr, (int(px - spr.get_width() / 2),
                               int(py - spr.get_height() / 2)))
            spr.set_alpha(255)

    # ==================================================================
    # RIG — LAYERED PIXEL ART
    # Urutan: hem -> torso -> pauldron -> head -> sabit -> lengan depan
    #         -> highlight -> flash luka. Semua koordinat lokal
    #         (facing kanan), dipetakan _map().
    # ==================================================================
    def _body_offsets(action, ap, phase, boss):
        """(dx, dy, flare) offset badan per pose (ruang lokal, facing +)."""
        if action == "attack":
            kind = getattr(boss, "_krb_attack_kind", "swing") if boss else "swing"
            if kind == "bolt":
                dx = _NS_krobellus._keyframes(
                    ((0.0, 0.0), (0.34, 3.0), (0.52, 5.0), (1.0, 0.0)), ap,
                    (_NS_krobellus._ease_out_cubic,
                     _NS_krobellus._ease_in_out_sine,
                     _NS_krobellus._ease_in_out_sine))
                return dx, -1.0, 0.0
            dx = _NS_krobellus._keyframes(
                ((0.0, 0.0), (0.12, -2.0), (0.26, -4.0), (0.42, 5.0),
                 (0.62, 4.0), (1.0, 0.0)), ap,
                (_NS_krobellus._ease_out_quad,
                 _NS_krobellus._ease_in_quad,
                 _NS_krobellus._ease_in_out_sine,
                 _NS_krobellus._ease_in_out_sine,
                 _NS_krobellus._ease_in_out_sine))
            return dx, 0.0, 0.25
        if action == "spin":
            k = _NS_krobellus._ease_in_out_cubic(min(1.0, ap / 0.55))
            return 0.0, -5.0 * k, 0.35 * k
        if action == "slam":
            if ap < 0.30:
                return _NS_krobellus._lerp(0.0, -1.0, ap / 0.30), -4.0 * (ap / 0.30), 0.0
            if ap < 0.70:
                return 1.0, 3.0, 0.5
            return _NS_krobellus._lerp(1.0, 0.0, (ap - 0.70) / 0.30), \
                _NS_krobellus._lerp(3.0, 0.0, (ap - 0.70) / 0.30), 0.2
        if action in ("cast_w", "cast_e"):
            return 3.0, 0.0, 0.1
        if action == "hurt":
            return -3.0, 1.0, 0.15
        if action == "walk":
            bob = abs(math.sin(phase * 2.2)) * 2.5
            return 2.0, -bob, 0.15
        # idle
        return 0.0, math.sin(phase * 0.8) * 2.0, 0.0

    def _draw_hem(surface, cx, cy, sc, facing, phase, flare, action):
        """Jubah bawah tattered — siluet utama Krobellus.

        Semua titik dalam ruang LOKAL (0,0 = pusat badan), dipetakan
        sekali lewat _map() — konsisten dengan seluruh rig.
        """
        c = _NS_krobellus.PALETTE
        G = _NS_krobellus
        sway = math.sin(phase * 0.9) * (2.5 + 3.0 * flare)
        sway2 = math.sin(phase * 0.6 + 1.2) * (2.0 + 2.0 * flare)
        top = G.HEM_TOP
        bot = G.HEM_BOT + int(math.sin(phase * 0.7) * 2)
        w = 20 + int(7 * flare)
        P = lambda lx, ly: G._map(cx, cy, sc, facing, lx, ly)  # noqa: E731
        # siluet luar (outline gelap)
        outer = [
            (-w, top), (w, top),
            (w + 5, top + 12),
            (w + 3 + sway, top + 24),
            (w - 4, top + 34),
            (w - 14 + sway2, bot),
            (4, bot + 4),
            (-4, bot + 4 - int(sway * 0.4)),
            (-w + 12 - sway2, bot),
            (-w + 4, top + 34),
            (-w - 3 - sway, top + 24),
            (-w - 5, top + 12),
        ]
        pygame.draw.polygon(surface, (*c["outline"], 255),
                            [P(x, y) for x, y in outer])
        # isi jubah (2 pita warna)
        inner1 = [
            (-w + 2, top + 2), (w - 2, top + 2),
            (w + 1 + sway, top + 24),
            (w - 6, top + 33),
            (w - 15 + sway2, bot - 2),
            (-2, bot + 1),
            (-w + 14 - sway2, bot - 2),
            (-w + 6, top + 33),
            (-w - 1 - sway, top + 24),
        ]
        pygame.draw.polygon(surface, (*c["robe_dark"], 255),
                            [P(x, y) for x, y in inner1])
        inner2 = [
            (-w + 5, top + 3), (w - 5, top + 3),
            (w - 4 + sway, top + 20),
            (w - 10, top + 30),
            (w - 19 + sway2, bot - 6),
            (-2, bot - 2),
            (-w + 19 - sway2, bot - 6),
            (-w + 10, top + 30),
            (-w + 4 - sway, top + 20),
        ]
        pygame.draw.polygon(surface, (*c["robe_mid"], 255),
                            [P(x, y) for x, y in inner2])
        # garis lipatan (streaks)
        for off in (-10, -4, 4, 10):
            x1 = off + (sway if off > 0 else -sway) * 0.6
            y1 = top + 30 + (4 if abs(off) > 6 else 8)
            pygame.draw.line(surface, (*c["robe_light"], 200),
                             P(off, top + 6), P(x1, y1), 1)
        # ujung tattered
        for i in range(8):
            tx = -w + 3 + i * ((2 * w - 6) / 7.0)
            ty = bot + 3 + int(math.sin(phase * 1.6 + i * 1.1) * 3)
            pygame.draw.polygon(surface, (*c["robe_fade"], 255),
                                [P(tx, bot - 2), P(tx + 2, bot - 2),
                                 P(tx + 1, ty)])
        # cahaya jiwa di bawah jubah
        a = int(90 + 40 * math.sin(phase * 1.2))
        pygame.draw.ellipse(surface, (*c["soul_mid"], max(20, a)),
                            (int(cx - 18 * sc), int(cy + 38 * sc),
                             int(36 * sc), int(6 * sc)), 1)
        pygame.draw.ellipse(surface, (*c["soul_dark"], max(30, a + 30)),
                            (int(cx - 20 * sc), int(cy + 42 * sc),
                             int(40 * sc), int(5 * sc)))

    def _draw_torso(surface, cx, cy, sc, facing, phase, action):
        """Korset + trim emas + gem jiwa."""
        c = _NS_krobellus.PALETTE
        G = _NS_krobellus
        breathe = 1.0 if action in ("idle",) else 1.0
        # outline
        o = [
            (cx - 13, cy + G.SHOULDER_Y - 2), (cx + 13, cy + G.SHOULDER_Y - 2),
            (cx + 14, cy + G.BELT_Y + 2), (cx + 6, cy + G.BELT_Y + 6),
            (cx - 6, cy + G.BELT_Y + 6), (cx - 14, cy + G.BELT_Y + 2),
        ]
        pygame.draw.polygon(surface, (*c["outline"], 255),
                            [G._map(cx, cy, sc, facing, x - cx, y - cy)
                             for x, y in o])
        # bodi
        b1 = [
            (cx - 12, cy + G.SHOULDER_Y - 1), (cx + 12, cy + G.SHOULDER_Y - 1),
            (cx + 13, cy + G.BELT_Y + 1), (cx + 5, cy + G.BELT_Y + 5),
            (cx - 5, cy + G.BELT_Y + 5), (cx - 13, cy + G.BELT_Y + 1),
        ]
        pygame.draw.polygon(surface, (*c["armor_dark"], 255),
                            [G._map(cx, cy, sc, facing, x - cx, y - cy)
                             for x, y in b1])
        b2 = [
            (cx - 10, cy + G.SHOULDER_Y + 1), (cx + 10, cy + G.SHOULDER_Y + 1),
            (cx + 11, cy + G.BELT_Y), (cx + 4, cy + G.BELT_Y + 4),
            (cx - 4, cy + G.BELT_Y + 4), (cx - 11, cy + G.BELT_Y),
        ]
        pygame.draw.polygon(surface, (*c["armor_mid"], 255),
                            [G._map(cx, cy, sc, facing, x - cx, y - cy)
                             for x, y in b2])
        # trim V emas di dada
        v1 = [
            (cx - 6, cy + G.SHOULDER_Y + 2), (cx + 6, cy + G.SHOULDER_Y + 2),
            (cx, cy + G.BELT_Y - 2),
        ]
        pygame.draw.polygon(surface, (*c["gold_mid"], 255),
                            [G._map(cx, cy, sc, facing, x - cx, y - cy)
                             for x, y in v1])
        v2 = [
            (cx - 4, cy + G.SHOULDER_Y + 3), (cx + 4, cy + G.SHOULDER_Y + 3),
            (cx, cy + G.BELT_Y - 4),
        ]
        pygame.draw.polygon(surface, (*c["gold_dark"], 255),
                            [G._map(cx, cy, sc, facing, x - cx, y - cy)
                             for x, y in v2])
        # gem jiwa (teal, berdenyut)
        pulse = 0.7 + 0.3 * math.sin(phase * 2.0)
        gx, gy = G._map(cx, cy, sc, facing, 0, G.SHOULDER_Y + 8)
        pygame.draw.rect(surface, (*c["gold_dark"], 255), (gx - 2, gy - 2, 4, 4))
        pygame.draw.rect(surface, (*c["soul_mid"], 255), (gx - 1, gy - 1, 2, 2))
        pygame.draw.rect(surface, (*c["soul_bright"], 255), (gx, gy, 1, 1))
        if pulse > 0.85:
            pygame.draw.rect(surface, (*c["soul_hot"], 200), (gx, gy - 1, 1, 1))
        # ikat pinggang emas
        by = G._map(cx, cy, sc, facing, 0, G.BELT_Y)
        pygame.draw.rect(surface, (*c["gold_dark"], 255),
                         (int(cx - 13 * sc), int(by[1]) - 2, int(26 * sc), 3))
        pygame.draw.rect(surface, (*c["gold_light"], 255),
                         (int(cx - 11 * sc), int(by[1]) - 1, int(22 * sc), 1))
        # lacing
        for i in range(3):
            yy = G.SHOULDER_Y + 4 + i * 4
            p1 = G._map(cx, cy, sc, facing, -3, yy)
            p2 = G._map(cx, cy, sc, facing, 3, yy + 2)
            p3 = G._map(cx, cy, sc, facing, -3, yy + 2)
            p4 = G._map(cx, cy, sc, facing, 3, yy)
            pygame.draw.line(surface, (*c["gold_light"], 220), p1, p2, 1)
            pygame.draw.line(surface, (*c["gold_light"], 220), p3, p4, 1)

    def _draw_pauldrons(surface, cx, cy, sc, facing, action):
        """Bahu bersudut + spike (armor)."""
        c = _NS_krobellus.PALETTE
        G = _NS_krobellus
        for side in (-1, 1):
            sx = cx + side * 14
            sy = cy + G.SHOULDER_Y - 1
            p = lambda lx, ly: G._map(cx, cy, sc, facing, lx - cx, ly - cy)  # noqa: E731
            # plate
            plate = [
                (sx - 6, sy + 2), (sx + 6, sy + 2),
                (sx + side * 8, sy - 4), (sx + side * 5, sy - 8),
                (sx - side * 2, sy - 6),
            ]
            pygame.draw.polygon(surface, (*c["outline"], 255),
                                 [p(x, y) for x, y in plate])
            pygame.draw.polygon(surface, (*c["armor_dark"], 255),
                                 [p(x, y) for x, y in plate])
            inner = [
                (sx - 4, sy + 1), (sx + 5, sy + 1),
                (sx + side * 6, sy - 3), (sx + side * 3, sy - 6),
            ]
            pygame.draw.polygon(surface, (*c["armor_mid"], 255),
                                 [p(x, y) for x, y in inner])
            pygame.draw.polygon(surface, (*c["armor_light"], 255),
                                 [p(sx + side * 4, sy - 2),
                                  p(sx + side * 6, sy - 4),
                                  p(sx + side * 5, sy - 6)])
            # spike
            sp = [
                (sx + side * 3, sy - 5), (sx + side * 7, sy - 5),
                (sx + side * 9, sy - 11),
            ]
            pygame.draw.polygon(surface, (*c["armor_dark"], 255),
                                 [p(x, y) for x, y in sp])
            pygame.draw.polygon(surface, (*c["armor_light"], 255),
                                 [p(sx + side * 5, sy - 6),
                                  p(sx + side * 7, sy - 6),
                                  p(sx + side * 8.5, sy - 10)])
            # aksen emas
            ga = p(sx - 2, sy)
            pygame.draw.rect(surface, (*c["gold_mid"], 255),
                             (int(ga[0]), int(ga[1]), 2, 2))
            pygame.draw.rect(surface, (*c["gold_light"], 255),
                             (int(ga[0]) + 1, int(ga[1]) - 1, 1, 1))

    def _draw_head(surface, cx, cy, sc, facing, phase, action):
        """Tudung + wajah pucat + mata api merah."""
        c = _NS_krobellus.PALETTE
        G = _NS_krobellus
        hy = G.HEAD_Y
        bob = 0
        if action in ("idle", "walk"):
            bob = int(math.sin(phase * 0.8) * 1)
        p = lambda lx, ly: G._map(cx, cy, sc, facing, lx, ly)  # noqa: E731
        # leher
        pygame.draw.rect(surface, (*c["skin_dark"], 255),
                         (int(cx - 3 * sc * (1 if facing > 0 else 1)),
                          int(cy + (hy + 8) * sc), int(6 * sc), int(5 * sc)))
        # tudung: bentuk luar (siluet kuat: puncak runcing ke belakang)
        hood = [
            (cx - 13, cy + hy + 8), (cx + 13, cy + hy + 8),
            (cx + 15, cy + hy + 2), (cx + 13, cy + hy - 8),
            (cx + 6, cy + hy - 13), (cx - 4, cy + hy - 14),
            (cx - 12, cy + hy - 8), (cx - 16, cy + hy - 1),
            (cx - 16, cy + hy + 4),
        ]
        pygame.draw.polygon(surface, (*c["outline"], 255),
                             [p(x - cx, y - cy) for x, y in hood])
        pygame.draw.polygon(surface, (*c["robe_dark"], 255),
                             [p(x - cx, y - cy) for x, y in hood])
        hood2 = [
            (cx - 11, cy + hy + 7), (cx + 11, cy + hy + 7),
            (cx + 13, cy + hy + 1), (cx + 11, cy + hy - 7),
            (cx + 5, cy + hy - 11), (cx - 3, cy + hy - 12),
            (cx - 10, cy + hy - 6), (cx - 13, cy + hy),
            (cx - 13, cy + hy + 4),
        ]
        pygame.draw.polygon(surface, (*c["robe_mid"], 255),
                             [p(x - cx, y - cy) for x, y in hood2])
        # lipatan tudung
        for i in range(3):
            yy = hy - 9 + i * 3
            p1 = p(-8 + i, yy)
            p2 = p(-3 + i * 2, yy - 1)
            pygame.draw.line(surface, (*c["robe_light"], 180), p1, p2, 1)
        # interior gelap (frame wajah)
        pygame.draw.ellipse(surface, (*c["shadow_deep"], 255),
                            (int(cx - 8 * sc), int(cy + (hy - 3 + bob) * sc),
                             int(16 * sc), int(13 * sc)))
        # wajah pucat (kecil, condong ke arah hadap)
        fx0 = int(cx + facing * sc - 6 * sc)
        pygame.draw.ellipse(surface, (*c["skin_dark"], 255),
                            (fx0, int(cy + (hy - 2 + bob) * sc),
                             int(12 * sc), int(11 * sc)))
        pygame.draw.ellipse(surface, (*c["skin_mid"], 255),
                            (fx0 + 1, int(cy + (hy - 2 + bob) * sc),
                             int(10 * sc), int(10 * sc)))
        pygame.draw.ellipse(surface, (*c["skin_light"], 255),
                            (fx0 + facing * sc, int(cy + (hy - 4 + bob) * sc),
                             int(5 * sc), int(5 * sc)))
        # bayangan alis (kedalaman)
        pygame.draw.ellipse(surface, (*c["shadow_deep"], 160),
                            (fx0 + 1, int(cy + (hy - 3 + bob) * sc),
                             int(10 * sc), int(3 * sc)))
        # Mata API MERAH (identitas Krobellus) — besar & menyala
        eye_p = 0.75 + 0.25 * math.sin(phase * 2.2)
        for side in (-1, 1):
            ex = side * 3.2 + facing * 0.8
            ey = hy + bob + 1
            ep = p(ex, ey)
            exi, eyi = int(ep[0]), int(ep[1])
            pygame.draw.rect(surface, (*c["shadow_deep"], 255),
                             (exi - 2, eyi - 1, 5, 3))
            pygame.draw.rect(surface, (*c["eye_dark"], 255),
                             (exi - 1, eyi, 3, 2))
            pygame.draw.rect(surface, (*c["eye_bright"], 255),
                             (exi, eyi, 2, 2))
            pygame.draw.rect(surface, (*c["eye_hot"], 255),
                             (exi, eyi, 1, 1))
            # glow tipis di sekeliling mata
            pygame.draw.rect(surface, (*c["eye_mid"], 90),
                             (exi - 2, eyi - 2, 5, 5))
        # mulut pucat tipis
        pygame.draw.rect(surface, (*c["skin_dark"], 255),
                         (int(cx + facing * sc - sc), int(cy + (hy + 4 + bob) * sc),
                          int(3 * sc), 1))
        gp = p(0, hy - 8)
        pygame.draw.rect(surface, (*c["gold_dark"], 255), (int(gp[0]) - 1, int(gp[1]), 3, 2))
        pygame.draw.rect(surface, (*c["soul_bright"], 255), (int(gp[0]), int(gp[1]), 1, 1))

    def _draw_arm(surface, cx, cy, sc, facing, sx, sy, ex, ey, hand_x, hand_y,
                  sleeve=True):
        """Segmen lengan: bahu->siku->tangan (sleeve jubah atau kulit)."""
        c = _NS_krobellus.PALETTE
        G = _NS_krobellus
        P = lambda lx, ly: G._map(cx, cy, sc, facing, lx, ly)  # noqa: E731
        p0, p1, p2 = P(sx, sy), P(ex, ey), P(hand_x, hand_y)
        if sleeve:
            pygame.draw.line(surface, (*c["outline"], 255), p0, p1, max(2, int(6 * sc)))
            pygame.draw.line(surface, (*c["robe_dark"], 255), p0, p1, max(2, int(4 * sc)))
            pygame.draw.line(surface, (*c["robe_mid"], 255), p0, p1, max(1, int(2 * sc)))
            pygame.draw.line(surface, (*c["outline"], 255), p1, p2, max(2, int(5 * sc)))
            pygame.draw.line(surface, (*c["skin_dark"], 255), p1, p2, max(1, int(3 * sc)))
            pygame.draw.line(surface, (*c["skin_mid"], 255), p1, p2, max(1, int(1 * sc)))
        else:
            pygame.draw.line(surface, (*c["outline"], 255), p0, p1, max(2, int(5 * sc)))
            pygame.draw.line(surface, (*c["skin_dark"], 255), p0, p1, max(1, int(3 * sc)))
            pygame.draw.line(surface, (*c["skin_light"], 255), p0, p1, max(1, int(1 * sc)))
        # tangan + wisp jiwa
        pygame.draw.circle(surface, (*c["skin_mid"], 255), p2, max(2, int(2.5 * sc)))
        pygame.draw.circle(surface, (*c["soul_mid"], 120),
                           (int(p2[0]), int(p2[1])), max(2, int(4 * sc)))
        pygame.draw.circle(surface, (*c["soul_bright"], 160),
                           (int(p2[0]), int(p2[1] - 1)), max(1, int(2 * sc)))

    def _draw_arms(surface, cx, cy, sc, facing, action, ap, phase, p_front):
        """Lengan belakang + depan (depan memegang sabit di p_front)."""
        c = _NS_krobellus.PALETTE
        G = _NS_krobellus
        sh_y = G.SHOULDER_Y + 1
        # LEMBAR BELAKANG
        back_sh = (-12, sh_y)
        if action == "spin":
            back_h = (-14, -14)
        elif action == "slam" and ap < 0.38:
            back_h = (-13, -26)
        elif action in ("cast_w", "cast_e"):
            back_h = (-10, -6)
        else:
            back_h = (-13, -16 + math.sin(phase * 0.7) * 1)
        G._draw_arm(surface, cx, cy, sc, facing, back_sh[0], back_sh[1],
                    -15, sh_y + 9, back_h[0], back_h[1])
        # LENGAN DEPAN — ke genggaman sabit
        front_sh = (12, sh_y)
        if action == "attack":
            # siku mengikuti arah ayunan (bukan teleport)
            th = G._scythe_angle(action, ap, phase)
            kx = 15 + 3 * math.cos(th)
            ky = sh_y + 8 + 3 * math.sin(th)
        elif action == "spin":
            kx, ky = 16, sh_y + 6
        elif action in ("cast_w", "cast_e"):
            kx, ky = 18, -14
        elif action == "slam":
            kx, ky = (15, -30) if ap < 0.38 else (14, -8)
        elif action == "hurt":
            kx, ky = (14, -22)
        else:
            kx, ky = (14, sh_y + 7)
        G._draw_arm(surface, cx, cy, sc, facing, front_sh[0], front_sh[1],
                    kx, ky, p_front[0], p_front[1])
        return

    def _draw_highlights(surface, cx, cy, sc, phase, action):
        """Titik jiwa melayang di sekitar badan (tanpa surface temp)."""
        c = _NS_krobellus.PALETTE
        G = _NS_krobellus
        n = 5 if action == "idle" else 4
        for i in range(n):
            a = phase * 0.5 + i * math.tau / n
            r = 26 + math.sin(phase * 0.8 + i * 1.3) * 6
            lx = math.cos(a) * r
            ly = -6 + math.sin(a) * r * 0.5
            pt = G._map(cx, cy, sc, 1, lx, ly)   # orbit simetris (tak dicerminkan)
            a2 = int(120 + 60 * math.sin(phase * 1.4 + i))
            pygame.draw.circle(surface, (*c["soul_mid"], max(30, a2)), pt, 1)
            pygame.draw.circle(surface, (*c["soul_bright"], max(20, a2 // 2)),
                               (int(pt[0]), int(pt[1]) - 1), 1)

    def _draw_flash_hurt(surface, cx, cy, sc, flash, facing, action, ap, phase):
        """Overlay putih saat kena damage (hurt_flash_timer > 0)."""
        if flash < 8:
            return
        a = int(min(120.0, flash * 0.72))
        c = (255, 255, 255, a)
        G = _NS_krobellus
        # siluet: tudung + torso (bukan jubah — flash tetap terbaca sebagai
        # "kena" tanpa menelan seluruh karakter)
        hood = [
            (cx - 13, cy + G.HEAD_Y + 8), (cx + 13, cy + G.HEAD_Y + 8),
            (cx + 15, cy + G.HEAD_Y + 2), (cx + 13, cy + G.HEAD_Y - 8),
            (cx + 6, cy + G.HEAD_Y - 13), (cx - 4, cy + G.HEAD_Y - 14),
            (cx - 12, cy + G.HEAD_Y - 8), (cx - 16, cy + G.HEAD_Y - 1),
            (cx - 16, cy + G.HEAD_Y + 4),
        ]
        pygame.draw.polygon(surface, c,
                             [G._map(cx, cy, sc, facing, x - cx, y - cy)
                              for x, y in hood])
        torso = [
            (cx - 13, cy + G.SHOULDER_Y - 2), (cx + 13, cy + G.SHOULDER_Y - 2),
            (cx + 14, cy + G.BELT_Y + 2), (cx + 6, cy + G.BELT_Y + 6),
            (cx - 6, cy + G.BELT_Y + 6), (cx - 14, cy + G.BELT_Y + 2),
        ]
        pygame.draw.polygon(surface, c,
                             [G._map(cx, cy, sc, facing, x - cx, y - cy)
                              for x, y in torso])

    def _draw_krb_rig_at(surface, cx, cy, sc, facing, phase, action, ap,
                         portrait, flash, boss):
        """Komposisi penuh satu pose (dipakai entry point)."""
        G = _NS_krobellus
        dx, dy, flare = G._body_offsets(action, ap, phase, boss)
        # death: dissolve naik (bagian atas lenyap duluan) + jatuh
        dissolve = 0.0
        if action == "death":
            age = int(getattr(boss, "_krb_death_age", 0) or 0)
            dissolve = min(1.0, age / 45.0)
            dy += dissolve * 6.0
        bx = cx + dx * facing * sc
        by = cy + dy * sc
        # HEM (paling belakang)
        G._draw_hem(surface, bx, by, sc, facing, phase, flare, action)
        # TORSO + PAULDRON
        G._draw_torso(surface, bx, by, sc, facing, phase, action)
        G._draw_pauldrons(surface, bx, by, sc, facing, action)
        # HEAD
        G._draw_head(surface, bx, by, sc, facing, phase, action)
        # SABIT (di belakang lengan depan)
        th = G._scythe_angle(action, ap, phase, boss)
        p = G._scythe_pivot_local(action, ap, phase, boss)
        glow_k = 0.0
        if action == "attack":
            kind = getattr(boss, "_krb_attack_kind", "swing") if boss else "swing"
            if kind == "swing":
                glow_k = 1.0 if 0.24 <= ap <= 0.58 else 0.45
            else:
                glow_k = 0.9 if 0.30 <= ap <= 0.56 else 0.3
        elif action == "spin":
            glow_k = 1.0
        elif action == "slam":
            glow_k = 1.0 if ap < 0.42 else 0.5
        elif action in ("cast_w", "cast_e"):
            glow_k = 0.5
        G._draw_scythe_at(surface, bx, by, sc, facing, th, p, glow_k, action, ap, phase)
        # LENGAN DEPAN (menimpa pangkal sabit)
        G._draw_arms(surface, bx, by, sc, facing, action, ap, phase, p)
        # HIGHLIGHT
        if not portrait:
            G._draw_highlights(surface, bx, by, sc, phase, action)
        # CHARGE ORB (w/bolt): orb di ujung bilah saat gathering
        if (action == "attack" and boss is not None and
                getattr(boss, "_krb_attack_kind", "swing") == "bolt"
                and 0.30 <= ap <= 0.56) or action == "cast_w":
            hub, _th = G._scythe_hub_local(action, ap, phase, boss)
            hp = G._map(bx, by, sc, facing, hub[0], hub[1])
            pulse = 0.7 + 0.3 * math.sin(phase * 12.0)
            col = G.PALETTE["void_mid"] if action == "cast_w" else G.PALETTE["soul_mid"]
            hot = G.PALETTE["void_bright"] if action == "cast_w" else G.PALETTE["soul_bright"]
            s = G._glow_surf(12, col)
            s.set_alpha(int(170 * pulse))
            surface.blit(s, (int(hp[0] - s.get_width() / 2),
                             int(hp[1] - s.get_height() / 2)))
            s.set_alpha(255)
            pygame.draw.circle(surface, (*hot, 255), hp, 2)
            pygame.draw.circle(surface, (255, 255, 255, 235), hp, 1)
        # FLASH HURT
        G._draw_flash_hurt(surface, bx, by, sc, flash, facing, action, ap, phase)
        return

    def _draw_scythe_at(surface, cx, cy, sc, facing, angle, p, glow_k,
                        action, ap, phase):
        """Versi sabit dengan pivot eksplisit (dipanggil rig)."""
        c = _NS_krobellus.PALETTE
        G = _NS_krobellus
        hub_l = (p[0] + G.SCYTHE_SHAFT * math.cos(angle),
                 p[1] + G.SCYTHE_SHAFT * math.sin(angle))
        P = lambda lx, ly: G._map(cx, cy, sc, facing, lx, ly)  # noqa: E731
        p0 = P(p[0], p[1])
        p1 = P(hub_l[0], hub_l[1])
        pygame.draw.line(surface, (*c["outline"], 255), p0, p1, max(2, int(5 * sc)))
        pygame.draw.line(surface, (*c["scythe_dark"], 255), p0, p1, max(2, int(3 * sc)))
        pygame.draw.line(surface, (*c["scythe_mid"], 255), p0, p1, max(1, int(1 * sc)))
        for i in range(3):
            t = 0.12 + i * 0.10
            gx = p[0] + (hub_l[0] - p[0]) * t
            gy = p[1] + (hub_l[1] - p[1]) * t
            gp = P(gx, gy)
            pygame.draw.rect(surface, (*c["gold_dark"], 255),
                             (int(gp[0]) - 1, int(gp[1]) - 1, 3, 3))
        hp = P(hub_l[0], hub_l[1])
        pygame.draw.circle(surface, (*c["scythe_dark"], 255), hp, max(2, int(3 * sc)))
        pygame.draw.circle(surface, (*c["gold_mid"], 255),
                           (int(hp[0]), int(hp[1]) - 1), max(1, int(1 * sc)))
        th0, th1 = angle - 0.30, angle + 1.10
        n = 10
        outer, inner = [], []
        for i in range(n + 1):
            t = th0 + (th1 - th0) * i / n
            outer.append(P(hub_l[0] + G.SCYTHE_R_OUT * math.cos(t),
                           hub_l[1] + G.SCYTHE_R_OUT * math.sin(t)))
        for i in range(n + 1):
            t = th1 - (th1 - th0) * i / n
            inner.append(P(hub_l[0] + G.SCYTHE_R_IN * math.cos(t),
                           hub_l[1] + G.SCYTHE_R_IN * math.sin(t)))
        pygame.draw.polygon(surface, (*c["outline"], 255), outer + inner)
        inner2 = []
        for i in range(n + 1):
            t = th0 + (th1 - th0) * i / n
            inner2.append(P(hub_l[0] + (G.SCYTHE_R_OUT - 2) * math.cos(t),
                            hub_l[1] + (G.SCYTHE_R_OUT - 2) * math.sin(t)))
        inner3 = []
        for i in range(n + 1):
            t = th1 - (th1 - th0) * i / n
            inner3.append(P(hub_l[0] + G.SCYTHE_R_IN * math.cos(t),
                            hub_l[1] + G.SCYTHE_R_IN * math.sin(t)))
        pygame.draw.polygon(surface, (*c["scythe_mid"], 255), inner2 + inner3)
        pygame.draw.polygon(surface, (*c["scythe_light"], 255), outer, max(1, int(2 * sc)))
        if glow_k > 0.05:
            a = int(150 * min(1.0, glow_k))
            for i in range(0, n, 2):
                t = th0 + (th1 - th0) * i / n
                pt = P(hub_l[0] + G.SCYTHE_R_OUT * math.cos(t),
                       hub_l[1] + G.SCYTHE_R_OUT * math.sin(t))
                pygame.draw.circle(surface, (*c["soul_light"], a), pt, 1)
            if glow_k > 0.5:
                s = G._glow_surf(16, c["soul_mid"])
                s.set_alpha(int(120 * glow_k))
                surface.blit(s, (int(hp[0] - s.get_width() / 2),
                                 int(hp[1] - s.get_height() / 2)))
                s.set_alpha(255)

    # ==================================================================
    # LAPISAN FX HIDUP (heroes/krobellus_fx)
    # ==================================================================
    _LIVE_MOD = None

    def _live_module():
        """Muat ``heroes.krobellus_fx`` sekali; None kalau tidak tersedia."""
        NS = _NS_krobellus
        if NS._LIVE_MOD is None:
            try:
                from heroes import krobellus_fx as mod
                NS._LIVE_MOD = mod if getattr(mod, "KROBELLS_FX_ENABLED",
                                              True) else False
            except Exception:
                NS._LIVE_MOD = False
        return NS._LIVE_MOD or None

    def live_fx_ready():
        """True kalau lapisan hidup Krobellus bisa dipakai (dipakai tooling)."""
        return _NS_krobellus._live_module() is not None

    def _live_fx(boss, surface, x, y, want_draw, portrait):
        """Return (mod, owned). want_draw True pada jalur BOSS (draw tiap
        frame tanpa cache); jalur HERO digambar heroes/__init__.py."""
        NS = _NS_krobellus
        if portrait:
            return None, False
        mod = NS._live_module()
        if mod is None:
            return None, False
        try:
            if want_draw:
                mod.draw_ground_layer(surface, boss, x, y)
            else:
                mod.attach(boss)
        except Exception:
            return None, False
        try:
            owned = bool(mod.owns(boss))
        except Exception:
            owned = False
        return (mod if want_draw else None), owned

    # ==================================================================
    # FALLBACK FX CANVAS (hanya jika modul FX tidak bisa dimuat)
    # ==================================================================
    def _draw_fallback_fx(surface, boss, x, y, phase):
        """Versi sederhana di-canvas: bolt, orb, ghost, flash impact."""
        G = _NS_krobellus
        c = G.PALETTE
        f = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        active = bool(getattr(boss, "_krb_attack_active", False))
        kind = getattr(boss, "_krb_attack_kind", "swing")
        ap = float(getattr(boss, "_krb_attack_progress", 0.0) or 0.0)
        tgt = getattr(boss, "target", None)
        tx = float(getattr(tgt, "x", x + 130 * f)) if tgt else x + 130 * f
        ty = float(getattr(tgt, "y", y)) if tgt else y
        if active and kind == "bolt" and ap >= G.ATTACK_RELEASE_FRAME:
            # soul bolt sederhana: 3 lingkaran + trail
            k = min(1.0, (ap - G.ATTACK_RELEASE_FRAME) /
                    (1.0 - G.ATTACK_RELEASE_FRAME) * 1.6)
            sx = x + 52 * f
            sy = y - 18
            px = sx + (tx - sx) * k
            py = sy + (ty - sy) * k
            for i in range(3):
                bk = max(0.0, k - i * 0.06)
                bx = sx + (tx - sx) * bk
                by = sy + (ty - sy) * bk
                a = max(30, 120 - i * 35)
                pygame.draw.circle(surface, (*c["soul_mid"], a),
                                   (int(bx), int(by)), max(1, 3 - i))
            pygame.draw.circle(surface, (*c["soul_light"], 235),
                               (int(px), int(py)), 4)
            pygame.draw.circle(surface, (*c["soul_hot"], 255),
                               (int(px), int(py)), 2)
        skill = getattr(boss, "_krb_skill", None)
        sp = float(getattr(boss, "_krb_skill_progress", 0.0) or 0.0)
        if skill == "q" and sp >= 0.55:
            r = int(20 + 90 * min(1.0, (sp - 0.55) / 0.45))
            a = max(20, int(180 * (1 - (sp - 0.55) / 0.45)))
            pygame.draw.ellipse(surface, (*c["soul_bright"], a),
                                (int(x - r), int(y - 10 - r * 0.25),
                                 r * 2, r * 0.5), 2)
        elif skill == "w" and sp < 0.45:
            hx, hy = x + 14 * f, y - 18
            r = int(3 + 9 * (sp / 0.45))
            pygame.draw.circle(surface, (*c["void_mid"], 235),
                               (int(hx), int(hy)), r)
            pygame.draw.circle(surface, (*c["void_bright"], 255),
                               (int(hx), int(hy)), max(1, r - 3))
        elif skill == "e":
            # garis jiwa ke target
            for i in range(6):
                t = i / 5.0
                px = tx + (x - tx) * t
                py = ty + (y - 18 - ty) * t
                a = int(120 + 60 * math.sin(phase * 8.0 + i))
                pygame.draw.circle(surface, (*c["soul_mid"], max(40, a)),
                                   (int(px), int(py)), 2)
        elif skill == "r" and sp >= 0.35:
            k = min(1.0, (sp - 0.35) / 0.55)
            r = int(16 + 70 * (1 - (1 - k) ** 2))
            a = max(16, int(190 * (1 - k)))
            pygame.draw.ellipse(surface, (*c["void_bright"], a),
                                (int(x - r), int(y + 40 - r * 0.2),
                                 r * 2, r * 0.4), 2)
            for i in range(8):
                ang = i * math.tau / 8
                gx = x + math.cos(ang) * (30 + 26 * k)
                gy = y + 42 - k * 44 + math.sin(phase * 3.0 + i) * 2
                a2 = int(220 * min(1.0, k * 3.0))
                pygame.draw.circle(surface, (*c["soul_mid"], max(20, a2)),
                                   (int(gx), int(gy)), 3)
                pygame.draw.circle(surface, (*c["soul_bright"], max(20, a2)),
                                   (int(gx), int(gy - 1)), 1)
        # flash impact saat frame benturan
        if active and kind == "swing" and ap >= G.ATTACK_IMPACT_FRAME and \
                ap < G.ATTACK_IMPACT_FRAME + 0.06:
            if tgt is not None:
                pygame.draw.circle(surface, (*c["soul_hot"], 200),
                                   (int(tx), int(ty)), 5)
                pygame.draw.circle(surface, (255, 255, 255, 220),
                                   (int(tx), int(ty)), 2)

    # ==================================================================
    # DEBUG OVERLAY (DEBUG_CHARACTER = True)
    # ==================================================================
    _DEBUG_FONT = None

    def _debug_font():
        NS = _NS_krobellus
        if NS._DEBUG_FONT is None:
            try:
                NS._DEBUG_FONT = pygame.font.SysFont("monospace", 11)
            except Exception:                          # pragma: no cover
                NS._DEBUG_FONT = None
        return NS._DEBUG_FONT

    def _draw_krb_debug(surface, boss, x, y, action, owned):
        """Hitbox, hurtbox, jangkauan, state/frame, FPS, partikel, skill,
        timer serangan. Overlay PALING AKHIR (tidak pernah tertutup)."""
        fnt = _NS_krobellus._debug_font()
        if fnt is None:
            return
        G = _NS_krobellus
        sc = G.body_scale(boss)
        x, y = int(x), int(y)
        f = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        r = int(22 * sc)
        # hurtbox
        pygame.draw.rect(surface, (255, 80, 80),
                         (x - r, y - r - 20, r * 2, r * 2 + 20), 1)
        # jangkauan basic
        reach = int(G.MELEE_REACH)
        pygame.draw.circle(surface, (80, 200, 255), (x, y), reach, 1)
        pygame.draw.circle(surface, (80, 200, 255), (x, y), 4, 1)
        # hitbox ayunan
        hb = G._swing_hitbox(boss, x, y)
        if hb is not None:
            pygame.draw.rect(surface, (255, 220, 60), hb, 1)
        # teks
        ap = float(getattr(boss, "_krb_attack_progress", 0.0) or 0.0)
        phase = getattr(boss, "_krb_attack_phase", "-")
        skill = getattr(boss, "_krb_skill", None)
        kind = getattr(boss, "_krb_attack_kind", "-")
        n_parts = 0
        if owned:
            mod = G._live_module()
            if mod is not None:
                try:
                    n_parts = int(mod.total_particles())
                except Exception:
                    n_parts = 0
        lines = [
            "KROBELLS state=%s pose=%s" % (G.anim_state(boss), action),
            "atk %s p=%.2f ph=%s skill=%s" % (
                kind if getattr(boss, "_krb_attack_active", False) else "-",
                ap, phase, skill),
            "timer=%d cd=%d hurt=%d" % (
                int(getattr(boss, "timer", 0) or 0),
                int(getattr(boss, "attack_cooldown", 0) or 0),
                int(getattr(boss, "hurt_flash_timer", 0) or 0)),
            "parts=%d live=%s" % (n_parts, "yes" if owned else "no"),
        ]
        yy = y - 92
        for ln in lines:
            t = fnt.render(ln, True, (220, 255, 240))
            bg = t.copy()
            bg.fill((0, 0, 0, 180))
            surface.blit(bg, (x - 8, yy - 1))
            surface.blit(t, (x - 7, yy))
            yy += 13

    # ==================================================================
    # ENTRY POINT
    # ==================================================================
    def draw_krobellus(surface, boss, x, y):
        """Entry point Boss.draw() sekaligus heroes.render_hero().

        Urutan lapisan (kontrak render order proyek):
          GROUND FX -> SHADOW -> BACK PARTICLES -> BODY/ARMOR/HEAD ->
          WEAPON -> ATTACK TRAIL -> PROJECTILE -> FRONT PARTICLES ->
          SKILL FX -> IMPACT FX -> DEBUG.
        Trail ayunan, partikel, soul bolt, impact, shake, dan hit-stop
        hidup di heroes/krobellus_fx.py (layar 1:1, di luar cache).
        """
        NS = _NS_krobellus
        # jalur hero (lane): heroes/__init__ men-set _render_scale sebelum
        # memanggil renderer -> lapisan hidup sudah dipicu di sana
        hero_lane = hasattr(boss, "_render_scale")
        portrait = bool(getattr(boss, "_portrait_hd", False))
        NS._update_krb_anim(boss)
        moving = NS._detect_moving(boss)
        action, phase, ap = NS._resolve_pose(boss, moving)
        boss._krb_pose_action = action
        facing = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        flash = NS._alpha(170 * (getattr(boss, "hurt_flash_timer", 0) / 8.0))
        live, owned = NS._live_fx(boss, surface, x, y,
                                  not hero_lane, portrait)

        # ── Latar (dibuang saat portrait agar auto-crop Hero Shop bersih)
        if not portrait:
            NS._draw_rune_circle(surface, x, y, phase,
                                 getattr(boss, "_krb_skill", None))
            NS._draw_shadow(surface, x, y)
            NS._draw_mist(surface, x, y, phase)

        # ── Hantu pendamping (belakang)
        intense = bool(getattr(boss, "_krb_attack_active", False)) or \
            getattr(boss, "_krb_skill", None) is not None
        NS._draw_companions(surface, x, y, phase, facing, front=False,
                            intense=intense)

        # ── Karakter
        NS._draw_krb_rig_at(surface, x, y, NS.body_scale(boss), facing,
                            phase, action, ap, portrait, flash, boss)

        # ── Fallback FX (hanya jalur boss & modul FX tidak diambil alih)
        if not owned and not hero_lane and not portrait:
            NS._draw_fallback_fx(surface, boss, x, y, phase)

        # ── Hantu pendamping (depan)
        NS._draw_companions(surface, x, y, phase, facing, front=True,
                            intense=intense)

        # ── Lapisan hidup bagian ATAS + debug
        if live is not None:
            try:
                live.draw_live_layer(surface, boss, x, y)
            except Exception:
                pass
        if NS.DEBUG_CHARACTER and not portrait:
            NS._draw_krb_debug(surface, boss, x, y, action, owned)

    # ==================================================================
    # Backward-compatible alias
    # ==================================================================
    def draw_boss(surface, boss, x, y):
        _NS_krobellus.draw_krobellus(surface, boss, x, y)


# ====================================================================
# ENTRY POINT PUBLIK (dipanggil base_boss.Boss.draw)
# ====================================================================

def draw_nyxara(surface, boss, x, y):
    """Entry point nyxara."""
    return _NS_nyxara.draw_nyxara(surface, boss, x, y)

def draw_gravefang(surface, boss, x, y):
    """Entry point gravefang."""
    return _NS_gravefang.draw_gravefang(surface, boss, x, y)

def draw_vhalzun(surface, boss, x, y):
    """Entry point vhalzun."""
    return _NS_vhalzun.draw_vhalzun(surface, boss, x, y)

def draw_krobellus(surface, boss, x, y):
    """Entry point krobellus."""
    return _NS_krobellus.draw_krobellus(surface, boss, x, y)
