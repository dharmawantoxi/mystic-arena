# ================================
# bosses/base_boss.py
# Base Boss class (shared oleh mini boss & true boss)
# ================================

import pygame
import math
from settings import *
from bosses.boss_data import get_all_boss_types
from _render import get_font


# ═══════════════════════════════════════════════════════
# OFFSET LABEL NAMA BOSS
# Tinggi puncak sprite setiap boss di atas titik jangkar (kaki),
# diukur dari render idle asli. Label nama & HP bar digambar
# DI ATAS puncak ini supaya tidak pernah menutupi badan boss.
# Nilai = puncak sprite + jarak aman.
# ═══════════════════════════════════════════════════════
BOSS_LABEL_TOP = {
    "abaddon": 63,
    "aeralith": 69,
    "akahime": 53,
    "akaroth": 55,
    "akiraze": 55,
    "azkharion": 55,
    "aelyrion": 58,
    "akashari": 59,
    "alchemist": 66,
    "ancient_apparition": 61,
    "astraelion": 53,
    "aurelion": 83,
    "aurelix": 57,
    "aurelyssa": 51,
    "aurethzar": 71,
    "aurex": 57,
    "auroth": 42,
    "azureth": 53,
    "cryssalia": 73,
    "cogsworth": 72,
    "celwynn": 55,
    "drakar": 53,
    "deidara": 72,
    "drav": 57,
    "gorath": 57,
    "grondarthul": 62,
    "grondmauris": 85,
    "grimjack": 55,
    "grimstalker": 55,
    "gornak": 51,
    "broggmar": 60,
    "brumhar": 60,
    "grimkor": 75,
    "bhorgathul": 58,
    "ghrakmaal": 62,
    "gravefang": 59,
    "gravewake": 61,
    "emberwick": 58,
    "ignirus": 53,
    "infrakzaar": 55,
    "ignakhor": 60,
    "ignis_drachorn": 68,
    "kaeldris": 73,
    "kaizoku_raijin": 58,
    "kassadin": 55,
    "kaedrin": 55,
    "kyrenzai": 70,
    "kazreth": 55,
    "kaerinya": 70,
    "kaelvyrn": 55,
    "kazureth": 52,
    "kyumirra": 50,
    "khalzaredh": 57,
    "kaerissa": 55,
    "kaervosth": 60,
    "kaelthar": 53,
    "kagetsuka": 72,
    "kaineroth": 72,
    "kaelthorn": 35,
    "kenshiro": 53,
    "khalros": 57,
    "khazan": 34,
    "krobellus": 68,
    "krognarr": 59,
    "korokai": 55,
    "kunkka": 47,
    "kurogari": 55,
    "kryvoxar": 62,
    "leoric": 35,
    "lyssarethys": 78,
    "luminar": 60,
    "lyrenya": 55,
    "lyrienne": 56,
    "malzareth": 46,
    "morgath": 51,
    "morvaeth2": 58,
    "morkhelvis": 60,
    "malzeroth": 72,
    "morthyrax": 55,
    "morvakhul": 58,
    "morvekhar": 57,
    "molgravar": 90,
    "morkhaera": 58,
    "morthraxis": 87,
    "morvaenthir": 73,
    "morvein": 31,
    "morvaeth": 58,
    "morvyssk": 46,
    "naraka": 67,
    "nazulmor": 73,
    "nexthyrius": 85,
    "nyxara": 73,
    "nyxarath": 66,
    "nyxaroth": 62,
    "nixweaver": 55,
    "nyxallaria": 55,
    "nyxharr": 90,
    "nyrellieth": 82,
    "nyrethzalv": 78,
    "okeanora": 90,
    "nyxareth": 81,
    "nyxareva": 53,
    "nyxraal": 58,
    "nyxariel": 45,
    "nyxthrael": 38,
    "nyzrak": 77,
    "pyraethis": 77,
    "pyraena": 75,
    "pyraklos": 57,
    "pyrenth": 79,
    "raz": 51,
    "rakzhan": 55,
    "ravokkar": 82,
    "razak": 73,
    "rynvara": 55,
    "seiryukong": 100,
    "sunakage": 75,
    "selunara": 55,
    "sethrakhar": 62,
    "seraphienne": 92,
    "shirotaka": 35,
    "sanguiveth": 55,
    "solara": 55,
    "solvanth": 50,
    "solvarin": 75,
    "sirakzan": 55,
    "sylvantheros": 55,
    "shimorakh": 58,
    "syrindra": 60,
    "solareth": 88,
    "syrentha": 59,
    "thalakryon": 71,
    "thalryndel": 72,
    "thargoroth": 62,
    "thalgryn": 50,
    "thorgaruk": 60,
    "thornvaegrim": 31,
    "thorvak": 47,
    "thorvin": 55,
    "vaelindra": 85,
    "vhaerinth": 55,
    "valthar": 58,
    "vaerith": 23,
    "vargrath": 48,
    "varkul": 60,
    "urgharun": 58,
    "velmyrth": 51,
    "vyraeth": 55,
    "vardrok": 60,
    "vorthakul": 58,
    "varkuthar": 58,
    "vessyra": 58,
    "vhalzun": 59,
    "ursath": 58,
    "verdanix": 58,
    "valekris": 58,
    "vaelmyrra": 82,
    "vulkareth": 62,
    "veshtrax": 60,
    "vargroth": 58,
    "vhorethzir": 67,
    "vhyssarion": 47,
    "vokrahn": 46,
    "vorenmarr": 61,
    "vorgath": 61,
    "vraskhan": 55,
    "wiro": 51,
    "xerathis": 59,
    "xarnthuul": 55,
    "xareth": 55,
    "xaelmoran": 75,
    "xelnarath": 72,
    "xharokh": 58,
    "xarnathul": 55,
    "xaerissa": 60,
    "xerakhotep": 58,
    "xirthalis": 26,
    "xyrael": 53,
    "yamako": 65,
    "yhoranth": 55,
    "zharok": 59,
    "zhaeris": 55,
    "zorashi": 55,
    "zorothrax": 58,
    "zulkhaven": 60,
    "zhyvrek": 55,
    "zorathiel": 55,
    "zhyrakaan": 60,
    "zharakzuul": 78,
    "zyvareth": 78,
    "zahkareth": 58,
    "zarethyr": 72,
    "kairenji": 55,
    "karzhul": 60,
    "xerakkuth": 58,
    "yomigetsu": 75,
    "kaelthys": 58,
    "kaoruken": 55,
    "vaelkorr": 60,
    "akirakumo": 78,
    "aurelian": 60,
    "morvath": 62,
    "pyrhaan": 55,
    "kaithros": 75,
    "garumenshi": 62,
    "thoraz": 62,
    "vhaerith": 58,
    "nyxaris": 75,
    "dorakai": 60,
    "hitokage": 58,
    "kazuren": 55,
    "tsukiyora": 78,
    "obanai": 58,
    "sanguire": 60,
    "sasori": 55,
    "hollowbane": 78,
}

# ═══════════════════════════════════════════════════════
# DISPATCH RENDERER BOSS (lazy + cache)
# Peta boss -> modul dibuat oleh: python tools/gen_boss_index.py
# ═══════════════════════════════════════════════════════
_MISSING_RENDERER = object()
_BOSS_DRAW_CACHE = {}


def _get_boss_draw_func(boss_type):
    """Ambil fungsi draw_<boss>() - impor modulnya sekali saja."""
    func = _BOSS_DRAW_CACHE.get(boss_type, _MISSING_RENDERER)
    if func is not _MISSING_RENDERER:
        return func

    func = None
    entry = None
    try:
        from bosses._boss_index import BOSS_INDEX
        entry = BOSS_INDEX.get(boss_type)
    except ImportError:
        print("[BOSS] bosses/_boss_index.py belum dibuat - "
              "jalankan: python tools/gen_boss_index.py")

    if entry:
        import importlib
        try:
            module = importlib.import_module("bosses." + entry[0])
            candidate = getattr(module, entry[1], None)
            if callable(candidate):
                func = candidate
        except Exception as exc:
            print("[BOSS] gagal memuat renderer %s: %s: %s"
                  % (boss_type, type(exc).__name__, exc))

    if func is None:
        # Cadangan: registry di heroes/ (berkas boss per-file lama)
        try:
            from heroes import BOSS_RENDERERS
            candidate = BOSS_RENDERERS.get(boss_type)
            if callable(candidate):
                func = candidate
        except Exception:
            pass

    _BOSS_DRAW_CACHE[boss_type] = func
    return func


class Boss(TowerDebuffMixin):
    """
    Boss entity - bisa mini boss atau true boss.
    Jalan di lane, punya ability, kalau kalah unlock hero.

    Boss (mini MAUPUN true) kena semua debuff menara Ice/Mage/Cannon
    lewat TowerDebuffMixin (dulu true boss kebal slow - sekarang tidak,
    sesuai desain terbaru: efek menara berlaku untuk SEMUA unit).

    Property `speed` di-override supaya SEMUA titik pergerakan boss
    (jalan lane, chase, retreat, dash) otomatis melambat saat kena
    slow - tanpa mengubah satu pun call site. Skill speed-boost tetap
    jalan karena mereka menulis base speed lewat setter.
    """

    @property
    def speed(self):
        base = self._speed_value
        if getattr(self, 'slow_timer', 0) > 0:
            return base * (1.0 - getattr(self, 'slow_amount', 0.0))
        return base

    @speed.setter
    def speed(self, value):
        self._speed_value = value

    # Skill/ability damage dipotong saat kena debuff Mage Tower
    @property
    def ability_damage(self):
        base = self._ability_damage_value
        if getattr(self, 'skill_down_timer', 0) > 0:
            f = max(0.0, 1.0 - getattr(self, 'skill_down_amount', 0.0))
            return int(round(base * f))
        return base

    @ability_damage.setter
    def ability_damage(self, value):
        self._ability_damage_value = value

    def __init__(self, boss_type, lane_path=None):
        self.boss_type = boss_type
        self._jenis_suara = None
        self.team = "red"

        all_bosses = get_all_boss_types()
        stats = all_bosses[boss_type]

        self.name = stats["name"]
        self.title = stats["title"]
        self.boss_class = stats.get("boss_class", "mini")
        self.max_hp = stats["hp"]
        self.hp = self.max_hp
        self.damage = stats["damage"]
        self.base_damage = self.damage
        self.speed = stats["speed"]
        self.range = stats["range"]
        self.attack_cooldown = stats["attack_cooldown"]
        self.radius = stats["radius"]
        self.gold_reward = stats["gold_reward"]
        self.color = stats["color"]
        self.color_dark = stats["color_dark"]
        self.ability_cooldown_max = stats["ability_cooldown"]
        self.ability_damage = stats["ability_damage"]
        self.ability_range = stats["ability_range"]
        self.entrance_text = stats["entrance_text"]
        self.entrance_color = stats["entrance_color"]

        # True boss extra ability
        self.ability2_cooldown_max = stats.get("ability2_cooldown", 0)
        self.ability2_heal_pct = stats.get("ability2_heal_pct", 0)
        self.ability2_timer = 0

        # Position
        self.lane_path = lane_path if lane_path else []
        if self.lane_path:
            sx, sy = self.lane_path[-1]
            self.x = float(sx)
            self.y = float(sy)
        else:
            self.x = float(RED_BASE_X - 50)
            self.y = float(RED_BASE_Y)

        self.waypoint_index = len(self.lane_path) - 1
        self.direction = -1

        # State
        self.alive = True
        self.timer = 0
        self.ability_timer = 0
        self.target = None
        self.defeated = False

        # ═══ BOSS RESILIENCE & MECHANICS ═══
        # Inherent damage reduction (True Boss: 30%, Mini Boss: 20%)
        self.damage_reduction = 0.30 if self.boss_class == "true" else 0.20
        # Tenacity: slow magnitude & duration reduced by 50%
        self.tenacity = 0.50
        # Anti-burst single hit damage cap (True: 8%, Mini: 12% max HP)
        self.max_damage_per_hit = int(self.max_hp * (0.08 if self.boss_class == "true" else 0.12))

        # Enrage / Frenzy State
        self.is_enraged = False
        self.enrage_triggered = False
        self.enrage_pulse = 0.0

        # Cleave attack
        self.cleave_radius = 80
        self.cleave_ratio = 0.40

        # Scaling multipliers (Hard mode)
        self.hp_scaling_mult = 1.0
        self.dmg_scaling_mult = 1.0
        self.spd_scaling_mult = 1.0

        # Animation
        self.anim_time = 0
        self.pulse = 0
        self.hurt_flash_timer = 0
        self.entrance_timer = 180 if self.boss_class == "true" else 120
        self.ability_active = False
        self.ability_active_timer = 0

        # ═══ DEBUFF MENARA (Ice/Mage/Cannon) ═══
        # slow gerak+serang, skill down, anti-heal, burn - semuanya
        # berlaku untuk mini boss dan true boss.
        self._init_tower_debuffs()

    def apply_scaling(self, hp_mult=1.0, dmg_mult=1.0, spd_mult=1.0):
        """Apply difficulty scaling (Hard Mode)"""
        self.hp_scaling_mult = hp_mult
        self.dmg_scaling_mult = dmg_mult
        self.spd_scaling_mult = spd_mult

        self.max_hp = int(self.max_hp * hp_mult)
        self.hp = self.max_hp
        self.damage = int(self.damage * dmg_mult)
        self.base_damage = self.damage
        self.ability_damage = int(self.ability_damage * dmg_mult)
        self.speed = self.speed * spd_mult
        self.base_speed = self.speed
        self.max_damage_per_hit = int(self.max_hp * (0.08 if self.boss_class == "true" else 0.12))

    def apply_slow(self, amount, duration):
        """Tenacity: resist 50% of slow magnitude and duration, max 35% slow."""
        if not getattr(self, "alive", True):
            return
        tenacity = getattr(self, "tenacity", 0.50)
        reduced_amount = min(0.35, amount * (1.0 - tenacity))
        reduced_duration = int(duration * (1.0 - tenacity))
        if reduced_amount > getattr(self, "slow_amount", 0.0) or \
                getattr(self, "slow_timer", 0) < reduced_duration:
            self.slow_amount = reduced_amount
            self.slow_timer = reduced_duration

    def apply_debuff(self, kind, amount, duration, source_team=None):
        if not getattr(self, "alive", True):
            return
        if kind == "slow":
            self.apply_slow(amount, duration)
            return
        elif kind == "atk_slow":
            tenacity = getattr(self, "tenacity", 0.50)
            amount = min(0.35, amount * (1.0 - tenacity))
            duration = int(duration * (1.0 - tenacity))
        super().apply_debuff(kind, amount, duration, source_team=source_team)

    def _suara_serangan(self):
        """
        Kembalikan jenis suara serangan boss: melee atau ranged.

        Sama seperti hero — mini boss maupun true boss memakai DUA
        jenis suara global yang sama (hero_melee / hero_ranged),
        dipilih dari jangkauan serangnya. Dihitung SEKALI lalu
        disimpan karena boss_data.py berisi ribuan entri.
        """
        if self._jenis_suara is not None:
            return self._jenis_suara
        from mobile import combat_audio as _ca
        self._jenis_suara = _ca.jenis_serangan(getattr(self, "range", 40))
        return self._jenis_suara

    def update(self, all_units, all_towers, all_bases):
        if not self.alive:
            return

        self.anim_time += 1
        self.pulse += 0.05

        # ═══ TICK DEBUFF MENARA (Ice/Mage/Cannon) ═══
        # slow, atk_slow, skill_down, anti_heal, burn (mini & true boss)
        self._tick_tower_debuffs()

        # ═══ STUN (item Tier II: Abyss Breaker / Fenrir Chain) ═══
        # Boss membeku (durasi sudah dipotong 55% oleh apply_stun
        # supaya true boss tidak di-stunlock).
        if self.stun_timer > 0:
            return

        if self.hurt_flash_timer > 0:
            self.hurt_flash_timer -= 1

        if self.entrance_timer > 0:
            self.entrance_timer -= 1
            return

        # ═══ ENRAGE / FRENZY CHECK ═══
        if not self.enrage_triggered:
            if self.boss_class == "true" and self.hp <= self.max_hp * 0.50:
                self.enrage_triggered = True
                self.is_enraged = True
                self.speed = self.speed * 1.25
                self.damage = int(self.damage * 1.25)
                self.attack_cooldown = max(18, int(self.attack_cooldown * 0.75))
                self._shake_screen(25)
                try:
                    import __main__
                    if hasattr(__main__, 'game_instance'):
                        __main__.game_instance.effects.add_damage_number(
                            self.x, self.y - self.radius - 30,
                            "ENRAGED!", is_critical=True, damage_type='crit')
                except Exception:
                    pass
            elif self.boss_class == "mini" and self.hp <= self.max_hp * 0.40:
                self.enrage_triggered = True
                self.is_enraged = True
                self.speed = self.speed * 1.15
                self.damage = int(self.damage * 1.20)
                self.attack_cooldown = max(20, int(self.attack_cooldown * 0.80))
                self._shake_screen(15)
                try:
                    import __main__
                    if hasattr(__main__, 'game_instance'):
                        __main__.game_instance.effects.add_damage_number(
                            self.x, self.y - self.radius - 30,
                            "FRENZY!", is_critical=True, damage_type='fire')
                except Exception:
                    pass

        if self.is_enraged:
            self.enrage_pulse += 0.08
            # Faster cooldown recovery when enraged
            if self.anim_time % 2 == 0:
                if self.timer > 0:
                    self.timer -= 1
                if self.ability_timer > 0:
                    self.ability_timer -= 1

        if self.timer > 0:
            self.timer -= 1
        if self.ability_timer > 0:
            self.ability_timer -= 1
        if self.ability2_timer > 0:
            self.ability2_timer -= 1
        if self.ability_active_timer > 0:
            self.ability_active_timer -= 1
            if self.ability_active_timer <= 0:
                self.ability_active = False

        # True boss: heal ability saat HP rendah
        if self.boss_class == "true" and self.ability2_timer == 0:
            if self.hp < self.max_hp * 0.3:
                self._use_heal_ability()

        # Find enemies
        enemies = []
        for u in all_units:
            if u.team != self.team and u.alive:
                enemies.append(u)
        for t in all_towers:
            if t.team != self.team and t.alive:
                enemies.append(t)
        for b in all_bases:
            if b.team != self.team and b.alive:
                enemies.append(b)

        # Nearest target
        self.target = None
        best_dist = self.range + 100
        for e in enemies:
            dist = math.hypot(e.x - self.x, e.y - self.y)
            if dist < best_dist:
                best_dist = dist
                self.target = e

        if self.target:
            dist = math.hypot(self.target.x - self.x,
                              self.target.y - self.y)

            if dist <= self.range:
                if self.timer == 0:
                    self.target.take_damage(self.damage, self.team,
                                            source=self)
                    # Cleave splash damage to nearby enemy units
                    cleave_dmg = int(self.damage * getattr(self, 'cleave_ratio', 0.40))
                    if cleave_dmg > 0:
                        c_rad = getattr(self, 'cleave_radius', 80)
                        for near_e in enemies:
                            if near_e != self.target and math.hypot(near_e.x - self.x, near_e.y - self.y) <= c_rad:
                                near_e.take_damage(cleave_dmg, self.team)
                    # Attack cooldown efektif (dipanjangkan saat kena
                    # debuff attack-speed dari Ice Tower)
                    self.timer = self._eff_attack_cd(self.attack_cooldown)
                    # Boss memakai DUA suara global yang sama seperti
                    # hero: melee vs ranged (lihat _suara_serangan).
                    try:
                        from mobile import combat_audio as _ca
                        _ca.play(self._suara_serangan())
                    except Exception:
                        pass

                # ═══ SMART AI per boss type ═══
                if self.boss_type == "abaddon":
                    self._smart_ai_abaddon(enemies, dist)
                elif self.boss_type == "alchemist":
                    self._smart_ai_alchemist(enemies, dist)
                elif self.boss_type == "ancient_apparition":
                    self._smart_ai_ancient_apparition(enemies, dist)
                elif self.boss_type == "ignis_drachorn":  # ← TAMBAH
                    self._smart_ai_ignis_drachorn(enemies, dist)
                elif self.boss_type == "gornak":
                    self._smart_ai_gornak(enemies, dist)
                elif self.boss_type == "morgath":
                    self._smart_ai_morgath(enemies, dist)
                elif self.boss_type == "drakar":
                    self._smart_ai_drakar(enemies, dist)
                elif self.boss_type == "razak":
                    self._smart_ai_razak(enemies, dist)
                elif self.boss_type == "khalros":
                    self._smart_ai_khalros(enemies, dist)
                elif self.boss_type == "gorath":
                    self._smart_ai_gorath(enemies, dist)
                elif self.boss_type == "varkul":
                    self._smart_ai_varkul(enemies, dist)
                elif self.boss_type == "xerathis":
                    self._smart_ai_xerathis(enemies, dist)
                elif self.boss_type == "nyzrak":
                    self._smart_ai_nyzrak(enemies, dist)
                elif self.boss_type == "zharok":
                    self._smart_ai_zharok(enemies, dist)
                elif self.boss_type == "pyrenth":
                    self._smart_ai_pyrenth(enemies, dist)
                elif self.boss_type == "vokrahn":
                    self._smart_ai_vokrahn(enemies, dist)
                elif self.boss_type == "nyxara":
                    self._smart_ai_nyxara(enemies, dist)
                elif self.boss_type == "gravefang":
                    self._smart_ai_gravefang(enemies, dist)
                elif self.boss_type == "vhalzun":
                    self._smart_ai_vhalzun(enemies, dist)
                elif self.boss_type == "kunkka":
                    self._smart_ai_kunkka(enemies, dist)
                elif self.boss_type == "gravewake":
                    self._smart_ai_gravewake(enemies, dist)
                elif self.boss_type == "syrentha":
                    self._smart_ai_syrentha(enemies, dist)
                elif self.boss_type == "thalgryn":
                    self._smart_ai_thalgryn(enemies, dist)
                elif self.boss_type == "nyxarath":
                    self._smart_ai_nyxarath(enemies, dist)
                elif self.boss_type == "vhorethzir":
                    self._smart_ai_vhorethzir(enemies, dist)
                elif self.boss_type == "vaerith":
                    self._smart_ai_vaerith(enemies, dist)
                elif self.boss_type == "xirthalis":
                    self._smart_ai_xirthalis(enemies, dist)
                elif self.boss_type == "vhyssarion":
                    self._smart_ai_vhyssarion(enemies, dist)
                elif self.boss_type == "kenshiro":
                    self._smart_ai_kenshiro(enemies, dist)
                elif self.boss_type == "khazan":
                    self._smart_ai_khazan(enemies, dist)
                elif self.boss_type == "wiro":
                    self._smart_ai_wiro(enemies, dist)
                elif self.boss_type == "naraka":
                    self._smart_ai_naraka(enemies, dist)
                elif self.boss_type == "krognarr":
                    self._smart_ai_krognarr(enemies, dist)
                elif self.boss_type == "raz":
                    self._smart_ai_raz(enemies, dist)
                elif self.boss_type == "vraskhan":
                    self._smart_ai_vraskhan(enemies, dist)
                elif self.boss_type == "aurethzar":
                    self._smart_ai_aurethzar(enemies, dist)
                elif self.boss_type == "aeralith":
                    self._smart_ai_aeralith(enemies, dist)
                elif self.boss_type == "aurex":
                    self._smart_ai_aurex(enemies, dist)
                elif self.boss_type == "nyxareva":
                    self._smart_ai_nyxareva(enemies, dist)
                elif self.boss_type == "thalakryon":
                    self._smart_ai_thalakryon(enemies, dist)
                elif self.boss_type == "aurelix":
                    self._smart_ai_aurelix(enemies, dist)
                elif self.boss_type == "aurelyssa":
                    self._smart_ai_aurelyssa(enemies, dist)
                elif self.boss_type == "vargrath":
                    self._smart_ai_vargrath(enemies, dist)
                elif self.boss_type == "nazulmor":
                    self._smart_ai_nazulmor(enemies, dist)
                elif self.boss_type == "kaeldris":
                    self._smart_ai_kaeldris(enemies, dist)
                elif self.boss_type == "pyraklos":
                    self._smart_ai_pyraklos(enemies, dist)
                elif self.boss_type == "velmyrth":
                    self._smart_ai_velmyrth(enemies, dist)
                elif self.boss_type == "solvarin":
                    self._smart_ai_solvarin(enemies, dist)
                elif self.boss_type == "malzareth":
                    self._smart_ai_malzareth(enemies, dist)
                elif self.boss_type == "akashari":
                    self._smart_ai_akashari(enemies, dist)
                elif self.boss_type == "vorenmarr":
                    self._smart_ai_vorenmarr(enemies, dist)
                elif self.boss_type == "azureth":
                    self._smart_ai_azureth(enemies, dist)
                elif self.boss_type == "luminar":
                    self._smart_ai_luminar(enemies, dist)
                elif self.boss_type == "solara":
                    self._smart_ai_solara(enemies, dist)
                elif self.boss_type == "pyraethis":
                    self._smart_ai_pyraethis(enemies, dist)
                elif self.boss_type == "auroth":
                    self._smart_ai_auroth(enemies, dist)
                elif self.boss_type == "morvein":
                    self._smart_ai_morvein(enemies, dist)
                elif self.boss_type == "thorvak":
                    self._smart_ai_thorvak(enemies, dist)
                elif self.boss_type == "yamako":
                    self._smart_ai_yamako(enemies, dist)
                elif self.boss_type == "ignirus":
                    self._smart_ai_ignirus(enemies, dist)
                elif self.boss_type == "leoric":
                    self._smart_ai_leoric(enemies, dist)
                elif self.boss_type == "shirotaka":
                    self._smart_ai_shirotaka(enemies, dist)
                elif self.boss_type == "seiryukong":
                    self._smart_ai_seiryukong(enemies, dist)
                elif self.boss_type == "kaelthorn":
                    self._smart_ai_kaelthorn(enemies, dist)
                elif self.boss_type == "solvanth":
                    self._smart_ai_solvanth(enemies, dist)
                elif self.boss_type == "xyrael":
                    self._smart_ai_xyrael(enemies, dist)
                elif self.boss_type == "nyxareth":
                    self._smart_ai_nyxareth(enemies, dist)
                elif self.boss_type == "cryssalia":
                    self._smart_ai_cryssalia(enemies, dist)
                elif self.boss_type == "kaelthar":
                    self._smart_ai_kaelthar(enemies, dist)
                elif self.boss_type == "morkhaera":
                    self._smart_ai_morkhaera(enemies, dist)
                elif self.boss_type == "aurelion":
                    self._smart_ai_aurelion(enemies, dist)
                elif self.boss_type == "akahime":
                    self._smart_ai_akahime(enemies, dist)
                elif self.boss_type == "nyxthrael":
                    self._smart_ai_nyxthrael(enemies, dist)
                elif self.boss_type == "sylvantheros":
                    self._smart_ai_sylvantheros(enemies, dist)
                elif self.boss_type == "vaelindra":
                    self._smart_ai_vaelindra(enemies, dist)
                elif self.boss_type == "astraelion":
                    self._smart_ai_astraelion(enemies, dist)
                elif self.boss_type == "morvaenthir":
                    self._smart_ai_morvaenthir(enemies, dist)
                elif self.boss_type == "thornvaegrim":
                    self._smart_ai_thornvaegrim(enemies, dist)
                elif self.boss_type == "morthraxis":
                    self._smart_ai_morthraxis(enemies, dist)
                else:
                    if self.ability_timer == 0:
                        self._use_ability(enemies)
            else:
                dx = self.target.x - self.x
                dy = self.target.y - self.y
                d = math.hypot(dx, dy)
                # ═══ RANGED BOSS KITING ═══
                if self.boss_type in ("ancient_apparition", "morgath",
                                      "razak", "varkul", "xerathis", "nyzrak",
                                      "syrentha", "thalgryn", "nyxarath",
                                      "malzareth", "akashari", "vorenmarr"):
                    stats = self._get_boss_stats()
                    min_dist = stats.get("min_distance", 200)
                    prefer_dist = stats.get("prefer_distance", 280)
                    if d < min_dist and d > 0:
                        # KITE: mundur dari target
                        self.x -= self.speed * dx / d
                        self.y -= self.speed * dy / d
                        self.direction = 1 if dx > 0 else -1
                    elif d > prefer_dist and d > 0:
                        # Approach ke prefer distance
                        self.x += self.speed * dx / d
                        self.y += self.speed * dy / d
                        self.direction = 1 if dx > 0 else -1
                    # Kalau di antara min & prefer → stay position
                else:
                    # Normal melee boss behavior
                    if d > 0:
                        self.x += self.speed * dx / d
                        self.y += self.speed * dy / d
                        self.direction = 1 if dx > 0 else -1
        else:
            self._move_forward()

    def _move_forward(self):
        if not self.lane_path or self.waypoint_index < 0:
            dx = BLUE_BASE_X - self.x
            dy = BLUE_BASE_Y - self.y
            d = math.hypot(dx, dy)
            if d > 1:
                self.x += self.speed * dx / d
                self.y += self.speed * dy / d
            return

        tx, ty = self.lane_path[self.waypoint_index]
        dx = tx - self.x
        dy = ty - self.y
        d = math.hypot(dx, dy)

        if d < 15:
            self.waypoint_index -= 1
            return
        if d > 0:
            self.x += self.speed * dx / d
            self.y += self.speed * dy / d

    def _use_ability(self, enemies):
        self.ability_timer = self.ability_cooldown_max
        self.ability_active = True
        self.ability_active_timer = 60

        for e in enemies:
            dist = math.hypot(e.x - self.x, e.y - self.y)
            if dist <= self.ability_range:
                e.take_damage(self.ability_damage, self.team)
                if hasattr(e, 'attack_timer'):
                    e.attack_timer = max(
                        getattr(e, 'attack_timer', 0), 60)

        try:
            import __main__
            if hasattr(__main__, 'game_instance'):
                shake = 15 if self.boss_class == "true" else 12
                __main__.game_instance.effects.shake_screen(shake)
        except Exception:
            pass

    def _smart_ai_abaddon(self, enemies, target_dist):
        """Smart AI: pilih skill Q/W/E/R berdasarkan situasi"""
        # Init skill timers kalau belum ada
        if not hasattr(self, 'q_timer'):
            self.q_timer = 0
            self.w_timer = 0
            self.e_timer = 0
            self.r_timer = 0
            self.active_skill = None
            self.active_skill_timer = 0

        # Decrement timers
        if self.q_timer > 0:
            self.q_timer -= 1
        if self.w_timer > 0:
            self.w_timer -= 1
        if self.e_timer > 0:
            self.e_timer -= 1
        if self.r_timer > 0:
            self.r_timer -= 1
        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0:
                self.active_skill = None

        # Count enemies dalam range
        nearby_count = sum(1 for e in enemies
                           if math.hypot(e.x - self.x, e.y - self.y) <= 150)

        hp_ratio = self.hp / self.max_hp

        # ═══ PRIORITY 1: HP kritis → W (Aphotic Shield) ═══
        if hp_ratio < 0.3 and self.w_timer == 0:
            self._cast_w_aphotic_shield(enemies)
            return

        # ═══ PRIORITY 2: Banyak enemy → R (Death Sever) ═══
        if nearby_count >= 3 and self.r_timer == 0:
            self._cast_r_death_sever(enemies)
            return

        # ═══ PRIORITY 3: Enemy dekat → Q (Mist Coil) ═══
        if target_dist < 130 and self.q_timer == 0:
            self._cast_q_mist_coil()
            return

        # ═══ PRIORITY 4: Enemy jauh → E (Darkness Gale) ═══
        if target_dist > 100 and self.e_timer == 0:
            self._cast_e_darkness_gale()
            return

    def _cast_q_mist_coil(self):
        """Q - Mist Coil: teal projectile"""
        self.q_timer = 240
        self.active_skill = 'q'
        self.active_skill_timer = 30

        stats = self._get_boss_stats()
        damage = stats.get("skill_q_damage", 250)

        if self.target and self.target.alive:
            self.target.take_damage(damage, self.team)

        self._shake_screen(10)

    def _cast_w_aphotic_shield(self, enemies):
        """W - Aphotic Shield: burst + shield"""
        self.w_timer = 360
        self.active_skill = 'w'
        self.active_skill_timer = 90

        stats = self._get_boss_stats()
        damage = stats.get("skill_w_damage", 300)
        shield_hp = stats.get("skill_w_shield", 500)

        # Burst damage AOE
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 100:
                e.take_damage(damage, self.team)

        # Shield HP (heal)
        self.hp = min(self.max_hp, self.hp + shield_hp)

        self._shake_screen(12)

    def _cast_e_darkness_gale(self):
        """E - Darkness Gale: dash cepat"""
        self.e_timer = 300
        self.active_skill = 'e'
        self.active_skill_timer = 40

        stats = self._get_boss_stats()
        damage = stats.get("skill_e_damage", 200)

        if self.target and self.target.alive:
            # Dash ke target
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                self.x += (dx / dist) * 80
                self.y += (dy / dist) * 80
            self.target.take_damage(damage, self.team)

        self._shake_screen(8)

    def _cast_r_death_sever(self, enemies):
        """R - Death Sever: AOE ultimate"""
        self.r_timer = 600
        self.active_skill = 'r'
        self.active_skill_timer = 60

        stats = self._get_boss_stats()
        damage = stats.get("skill_r_damage", 500)

        # Massive AOE
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 180:
                e.take_damage(damage, self.team)

        self._shake_screen(20)

    def _smart_ai_alchemist(self, enemies, target_dist):
        """Smart AI Alchemist: 4 skills Q/W/E/R"""
        # Init timers
        if not hasattr(self, 'q_timer'):
            self.q_timer = 0
            self.w_timer = 0
            self.e_timer = 0
            self.r_timer = 0
            self.active_skill = None
            self.active_skill_timer = 0
            self.rage_active = False
            self.rage_timer = 0

        # Decrement timers
        if self.q_timer > 0:
            self.q_timer -= 1
        if self.w_timer > 0:
            self.w_timer -= 1
        if self.e_timer > 0:
            self.e_timer -= 1
        if self.r_timer > 0:
            self.r_timer -= 1
        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0:
                self.active_skill = None

        # Rage buff timer
        if self.rage_active:
            self.rage_timer -= 1
            if self.rage_timer <= 0:
                self.rage_active = False

        # Count nearby enemies
        nearby_count = sum(1 for e in enemies
                           if math.hypot(e.x - self.x, e.y - self.y) <= 180)

        hp_ratio = self.hp / self.max_hp

        # ═══ PRIORITY 1: HP kritis + banyak enemy → R (Greevil's Greed) ═══
        if hp_ratio < 0.4 and nearby_count >= 3 and self.r_timer == 0:
            self._cast_r_greevils_greed(enemies)
            return

        # ═══ PRIORITY 2: HP menurun → E (Chemical Rage buff) ═══
        if hp_ratio < 0.6 and not self.rage_active and self.e_timer == 0:
            self._cast_e_chemical_rage()
            return

        # ═══ PRIORITY 3: Banyak enemy → W (Unstable Concoction AOE) ═══
        if nearby_count >= 2 and self.w_timer == 0:
            self._cast_w_unstable_concoction(enemies)
            return

        # ═══ PRIORITY 4: Enemy dalam range → Q (Acid Spray) ═══
        if target_dist < 200 and self.q_timer == 0:
            self._cast_q_acid_spray()
            return

    def _cast_q_acid_spray(self):
        """Q - Acid Spray: line projectile"""
        self.q_timer = 210
        self.active_skill = 'q'
        self.active_skill_timer = 40

        stats = self._get_boss_stats()
        damage = stats.get("skill_q_damage", 220)

        if self.target and self.target.alive:
            self.target.take_damage(damage, self.team)

        self._shake_screen(8)

    def _cast_w_unstable_concoction(self, enemies):
        """W - Unstable Concoction: throw potion → AOE"""
        self.w_timer = 300
        self.active_skill = 'w'
        self.active_skill_timer = 60

        stats = self._get_boss_stats()
        damage = stats.get("skill_w_damage", 320)

        # AOE damage di lokasi target
        if self.target and self.target.alive:
            target_x = self.target.x
            target_y = self.target.y
        else:
            target_x = self.x
            target_y = self.y

        for e in enemies:
            if math.hypot(e.x - target_x, e.y - target_y) <= 100:
                e.take_damage(damage, self.team)
                # Slow effect
                if hasattr(e, 'apply_slow'):
                    e.apply_slow(0.5, 180)

        # Store target position for visual
        self.w_target_x = target_x
        self.w_target_y = target_y

        self._shake_screen(15)

    def _cast_e_chemical_rage(self):
        """E - Chemical Rage: buff self"""
        self.e_timer = 480
        self.active_skill = 'e'
        self.active_skill_timer = 60
        self.rage_active = True
        self.rage_timer = 360  # 6 detik buff

        # Buff stats
        self.damage = int(self.damage * 1.5)

        # Heal 15%
        heal = int(self.max_hp * 0.15)
        self.hp = min(self.max_hp, self.hp + heal)

        self._shake_screen(12)

        try:
            import __main__
            if hasattr(__main__, 'game_instance'):
                game = __main__.game_instance
                game.effects.add_damage_number(
                    self.x, self.y - 30,
                    f"+{heal}", is_critical=True,
                    damage_type='heal')
        except Exception:
            pass

    def _cast_r_greevils_greed(self, enemies):
        """R - Greevil's Greed: massive AOE + gold"""
        self.r_timer = 720
        self.active_skill = 'r'
        self.active_skill_timer = 90

        stats = self._get_boss_stats()
        damage = stats.get("skill_r_damage", 550)

        # Massive AOE
        kills_count = 0
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 200:
                e.take_damage(damage, self.team)
                if not e.alive:
                    kills_count += 1

        # Bonus gold buat boss (heal effect)
        if kills_count > 0:
            heal = kills_count * 100
            self.hp = min(self.max_hp, self.hp + heal)

        self._shake_screen(25)

    def _smart_ai_ancient_apparition(self, enemies, target_dist):
        """Smart AI Ancient Apparition: 4 ice skills"""
        # Init timers
        if not hasattr(self, 'q_timer'):
            self.q_timer = 0
            self.w_timer = 0
            self.e_timer = 0
            self.r_timer = 0
            self.active_skill = None
            self.active_skill_timer = 0
            self.vortex_x = 0
            self.vortex_y = 0
            self.vortex_active_timer = 0
            self.cold_feet_target_x = 0
            self.cold_feet_target_y = 0

        # Decrement timers
        if self.q_timer > 0:
            self.q_timer -= 1
        if self.w_timer > 0:
            self.w_timer -= 1
        if self.e_timer > 0:
            self.e_timer -= 1
        if self.r_timer > 0:
            self.r_timer -= 1
        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0:
                self.active_skill = None

        # Vortex duration (DOT effect)
        if self.vortex_active_timer > 0:
            self.vortex_active_timer -= 1
            # Damage per tick
            if self.vortex_active_timer % 20 == 0:
                stats = self._get_boss_stats()
                damage = stats.get("skill_q_damage", 180) // 3
                for e in enemies:
                    dist = math.hypot(e.x - self.vortex_x,
                                      e.y - self.vortex_y)
                    if dist <= 80:
                        e.take_damage(damage, self.team)
                        if hasattr(e, 'apply_slow'):
                            e.apply_slow(0.5, 60)

        # Count enemies in medium range
        med_range_count = sum(1 for e in enemies
                              if math.hypot(e.x - self.x,
                                            e.y - self.y) <= 300)

        hp_ratio = self.hp / self.max_hp

        # ═══ PRIORITY 1: HP kritis + banyak enemy → R (Cold Feet ultimate) ═══
        if hp_ratio < 0.4 and med_range_count >= 2 and self.r_timer == 0:
            self._cast_r_cold_feet(enemies)
            return

        # ═══ PRIORITY 2: Banyak enemy clumped → Q (Ice Vortex AOE) ═══
        if med_range_count >= 3 and self.q_timer == 0:
            self._cast_q_ice_vortex(enemies)
            return

        # ═══ PRIORITY 3: Target isolated & jauh → E (Ice Blast burst) ═══
        if target_dist > 250 and self.e_timer == 0:
            self._cast_e_ice_blast()
            return

        # ═══ PRIORITY 4: Target dalam range → W (Chilling Touch line) ═══
        if target_dist < 320 and self.w_timer == 0:
            self._cast_w_chilling_touch(enemies)
            return

    def _cast_q_ice_vortex(self, enemies):
        """Q - Ice Vortex: AOE tornado di lokasi target"""
        self.q_timer = 300
        self.active_skill = 'q'
        self.active_skill_timer = 60

        # Spawn vortex di lokasi target
        if self.target and self.target.alive:
            self.vortex_x = self.target.x
            self.vortex_y = self.target.y
        else:
            self.vortex_x = self.x + 100
            self.vortex_y = self.y

        # Vortex active for 3 detik
        self.vortex_active_timer = 180

        stats = self._get_boss_stats()
        initial_damage = stats.get("skill_q_damage", 180) // 2

        # Initial damage burst
        for e in enemies:
            dist = math.hypot(e.x - self.vortex_x, e.y - self.vortex_y)
            if dist <= 80:
                e.take_damage(initial_damage, self.team)

        self._shake_screen(10)

    def _cast_w_chilling_touch(self, enemies):
        """W - Chilling Touch: line beam damage + slow"""
        self.w_timer = 240
        self.active_skill = 'w'
        self.active_skill_timer = 45

        stats = self._get_boss_stats()
        damage = stats.get("skill_w_damage", 250)

        if not self.target or not self.target.alive:
            return

        # Direction vector
        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.hypot(dx, dy)
        if dist == 0:
            return

        dx /= dist
        dy /= dist

        # Line hit: damage semua enemy dalam line width 30, jarak hingga 400
        max_range = 400
        line_width = 30

        for e in enemies:
            # Project enemy ke line
            ex = e.x - self.x
            ey = e.y - self.y
            proj = ex * dx + ey * dy  # projection onto line

            if 0 < proj < max_range:
                # Perpendicular distance
                perp = abs(ex * (-dy) + ey * dx)
                if perp < line_width:
                    e.take_damage(damage, self.team)
                    if hasattr(e, 'apply_slow'):
                        e.apply_slow(0.6, 180)  # heavy slow

        # Store direction for visual
        self.w_dir_x = dx
        self.w_dir_y = dy

        self._shake_screen(8)

    def _cast_e_ice_blast(self):
        """E - Ice Blast: single target heavy damage + stun"""
        self.e_timer = 360
        self.active_skill = 'e'
        self.active_skill_timer = 50

        stats = self._get_boss_stats()
        damage = stats.get("skill_e_damage", 450)

        if self.target and self.target.alive:
            self.target.take_damage(damage, self.team)
            # Stun (freeze) effect
            if hasattr(self.target, 'attack_timer'):
                self.target.attack_timer = max(
                    self.target.attack_timer, 90)

        self._shake_screen(15)

    def _cast_r_cold_feet(self, enemies):
        """R - Cold Feet: massive line AOE ice crystals from ground"""
        self.r_timer = 720
        self.active_skill = 'r'
        self.active_skill_timer = 90

        stats = self._get_boss_stats()
        damage = stats.get("skill_r_damage", 600)

        if not self.target or not self.target.alive:
            return

        # Direction to target
        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.hypot(dx, dy)
        if dist == 0:
            return

        dx /= dist
        dy /= dist

        # Line AOE: wide 60, range 500
        max_range = 500
        line_width = 60

        for e in enemies:
            ex = e.x - self.x
            ey = e.y - self.y
            proj = ex * dx + ey * dy

            if 0 < proj < max_range:
                perp = abs(ex * (-dy) + ey * dx)
                if perp < line_width:
                    e.take_damage(damage, self.team)
                    if hasattr(e, 'apply_slow'):
                        e.apply_slow(0.7, 240)

        # Store direction for visual
        self.r_dir_x = dx
        self.r_dir_y = dy

        self._shake_screen(25)

    def _smart_ai_ignis_drachorn(self, enemies, target_dist):
        """Smart AI Ignis Drachorn: 4 skills + dragon form"""
        # Init timers
        if not hasattr(self, 'q_timer'):
            self.q_timer = 0
            self.w_timer = 0
            self.e_timer = 0
            self.r_timer = 0
            self.active_skill = None
            self.active_skill_timer = 0
            self.dragon_form_active = False
            self.dragon_form_timer = 0
            self.dragon_blood_active = False
            self.dragon_blood_timer = 0

        # Decrement timers
        if self.q_timer > 0:
            self.q_timer -= 1
        if self.w_timer > 0:
            self.w_timer -= 1
        if self.e_timer > 0:
            self.e_timer -= 1
        if self.r_timer > 0:
            self.r_timer -= 1
        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0:
                self.active_skill = None

        # Dragon Form duration (from R)
        if self.dragon_form_active:
            self.dragon_form_timer -= 1
            if self.dragon_form_timer <= 0:
                self.dragon_form_active = False
                # Reset damage
                stats = self._get_boss_stats()
                self.damage = stats.get("damage", 120)

        # Dragon Blood buff (from E)
        if self.dragon_blood_active:
            self.dragon_blood_timer -= 1
            if self.dragon_blood_timer <= 0:
                self.dragon_blood_active = False

        # Count nearby enemies
        nearby_count = sum(1 for e in enemies
                           if math.hypot(e.x - self.x,
                                         e.y - self.y) <= 180)

        hp_ratio = self.hp / self.max_hp

        # ═══ PRIORITY 1: HP kritis + banyak enemy → R (Elder Dragon Form) ═══
        if hp_ratio < 0.5 and nearby_count >= 2 and self.r_timer == 0:
            self._cast_r_elder_dragon_form(enemies)
            return

        # ═══ PRIORITY 2: HP menurun → E (Dragon Blood defensive buff) ═══
        if hp_ratio < 0.65 and not self.dragon_blood_active and \
                self.e_timer == 0:
            self._cast_e_dragon_blood()
            return

        # ═══ PRIORITY 3: Banyak enemy → W (Dragon Tail AOE sweep) ═══
        if nearby_count >= 2 and self.w_timer == 0:
            self._cast_w_dragon_tail(enemies)
            return

        # ═══ PRIORITY 4: Target dalam range → Q (Dragon Breath) ═══
        if target_dist < 220 and self.q_timer == 0:
            self._cast_q_dragon_breath(enemies)
            return

    def _cast_q_dragon_breath(self, enemies):
        """Q - Dragon Breath: cone fire attack"""
        self.q_timer = 240
        self.active_skill = 'q'
        self.active_skill_timer = 45

        stats = self._get_boss_stats()
        damage = stats.get("skill_q_damage", 320)

        if not self.target or not self.target.alive:
            return

        # Direction vector
        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.hypot(dx, dy)
        if dist == 0:
            return
        dx /= dist
        dy /= dist

        # Cone attack: damage semua enemy dalam cone width 60, jarak 250
        max_range = 250
        cone_width = 60

        for e in enemies:
            ex = e.x - self.x
            ey = e.y - self.y
            proj = ex * dx + ey * dy
            if 0 < proj < max_range:
                perp = abs(ex * (-dy) + ey * dx)
                # Cone melebar sesuai jarak
                allowed_width = cone_width * (0.3 + proj / max_range * 0.7)
                if perp < allowed_width:
                    e.take_damage(damage, self.team)
                    # Burning DOT effect (via attack_timer)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 45)

        self._shake_screen(12)

    def _cast_w_dragon_tail(self, enemies):
        """W - Dragon Tail: 360° sweep AOE"""
        self.w_timer = 300
        self.active_skill = 'w'
        self.active_skill_timer = 40

        stats = self._get_boss_stats()
        damage = stats.get("skill_w_damage", 380)

        # 360° AOE + knockback effect (via stun)
        for e in enemies:
            dist = math.hypot(e.x - self.x, e.y - self.y)
            if dist <= 130:
                e.take_damage(damage, self.team)
                # Stun/knockback
                if hasattr(e, 'attack_timer'):
                    e.attack_timer = max(e.attack_timer, 60)
                # Knockback: HANYA untuk unit yang bisa bergerak.
                # Tower & Castle adalah bangunan statis - kalau
                # posisinya digeser, mereka pindah permanen dari
                # petak-nya. Unit punya .speed, bangunan tidak.
                dist = math.hypot(e.x - self.x, e.y - self.y)
                if dist > 0 and hasattr(e, 'speed'):
                    push_x = (e.x - self.x) / dist * 15
                    push_y = (e.y - self.y) / dist * 15
                    e.x += push_x
                    e.y += push_y

        self._shake_screen(15)

    def _cast_e_dragon_blood(self):
        """E - Dragon Blood: heal + damage buff"""
        self.e_timer = 420
        self.active_skill = 'e'
        self.active_skill_timer = 60
        self.dragon_blood_active = True
        self.dragon_blood_timer = 480  # 8 detik buff

        # Buff damage
        stats = self._get_boss_stats()
        base_damage = stats.get("damage", 120)
        self.damage = int(base_damage * 1.3)

        # Heal 20% max HP
        heal = int(self.max_hp * 0.20)
        self.hp = min(self.max_hp, self.hp + heal)

        self._shake_screen(10)

        try:
            import __main__
            if hasattr(__main__, 'game_instance'):
                game = __main__.game_instance
                game.effects.add_damage_number(
                    self.x, self.y - 30,
                    f"+{heal}", is_critical=True,
                    damage_type='heal')
        except Exception:
            pass

    def _cast_r_elder_dragon_form(self, enemies):
        """R - Elder Dragon Form: transform + massive AOE"""
        self.r_timer = 780
        self.active_skill = 'r'
        self.active_skill_timer = 90

        # Transform to dragon form
        self.dragon_form_active = True
        self.dragon_form_timer = 600  # 10 detik dragon form

        # Massive damage buff during dragon form
        stats = self._get_boss_stats()
        base_damage = stats.get("damage", 120)
        self.damage = int(base_damage * 1.8)

        # Massive AOE damage (initial burst)
        damage = stats.get("skill_r_damage", 600)
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 220:
                e.take_damage(damage, self.team)
                if hasattr(e, 'attack_timer'):
                    e.attack_timer = max(e.attack_timer, 90)

        # Heal 25% (transformation)
        heal = int(self.max_hp * 0.25)
        self.hp = min(self.max_hp, self.hp + heal)

        self._shake_screen(28)

    def _smart_ai_vhorethzir(self, enemies, target_dist):
        """Smart AI Vhoreth'zir: nethervenom wyrm, ranged poison caster."""
        if not hasattr(self, 'q_timer'):
            self.q_timer = 0
            self.w_timer = 0
            self.e_timer = 0
            self.r_timer = 0
            self.active_skill = None
            self.active_skill_timer = 0
            self.corrosive_active = False
            self.corrosive_timer = 0
        if self.q_timer > 0: self.q_timer -= 1
        if self.w_timer > 0: self.w_timer -= 1
        if self.e_timer > 0: self.e_timer -= 1
        if self.r_timer > 0: self.r_timer -= 1
        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0:
                self.active_skill = None

        # Corrosive Skin: aura defensif, kembalikan armor saat habis
        if self.corrosive_active:
            self.corrosive_timer -= 1
            if self.corrosive_timer <= 0:
                self.corrosive_active = False

        nearby = sum(
            1 for e in enemies
            if math.hypot(e.x - self.x, e.y - self.y) <= 200
        )
        hp_ratio = self.hp / self.max_hp

        # PRIORITY 1: HP kritis + banyak enemy -> R (Viper Strike)
        if hp_ratio < 0.4 and nearby >= 2 and self.r_timer == 0:
            self._vhorethzir_r(enemies)
            return
        # PRIORITY 2: HP menurun -> E (Corrosive Skin, defensif)
        if hp_ratio < 0.6 and not self.corrosive_active \
                and self.e_timer == 0:
            self._vhorethzir_e(enemies)
            return
        # PRIORITY 3: Banyak enemy -> W (Nethertoxin area)
        if nearby >= 2 and self.w_timer == 0:
            self._vhorethzir_w(enemies)
            return
        # PRIORITY 4: Target dalam range -> Q (Poison Attack)
        if target_dist < 280 and self.q_timer == 0:
            self._vhorethzir_q(enemies)
            return

    def _vhorethzir_q(self, enemies):
        """Q - Poison Attack: venom orb ke enemy terdekat + splash.
        active_skill_timer = 45 (cocok dgn duration di renderer)."""
        stats = self._get_boss_stats()
        self.q_timer = stats.get("skill_q_cooldown", 240)
        self.active_skill = 'q'
        self.active_skill_timer = 45
        damage = stats.get("skill_q_damage", 400)

        # Cari enemy TERDEKAT (tidak bergantung pada self.target)
        closest = None
        closest_dist = 9999
        for e in enemies:
            d = math.hypot(e.x - self.x, e.y - self.y)
            if d < closest_dist:
                closest_dist = d
                closest = e

        if not closest or closest_dist > 300:
            self._shake_screen(10)
            return

        # Damage utama + splash di sekitar titik jatuh
        for e in enemies:
            d = math.hypot(e.x - closest.x, e.y - closest.y)
            if d <= 70:
                falloff = 1.0 if e is closest else 0.6
                e.take_damage(int(damage * falloff), self.team)
                # Racun: perlambat serangan berikutnya
                if hasattr(e, 'attack_timer'):
                    e.attack_timer = max(
                        getattr(e, 'attack_timer', 0), 45)

        self._shake_screen(14)

    def _vhorethzir_w(self, enemies):
        """W - Nethertoxin: kolam racun area di posisi enemy terdekat.
        active_skill_timer = 90 (cocok dgn duration di renderer)."""
        stats = self._get_boss_stats()
        self.w_timer = stats.get("skill_w_cooldown", 300)
        self.active_skill = 'w'
        self.active_skill_timer = 90
        damage = stats.get("skill_w_damage", 360)

        closest = None
        closest_dist = 9999
        for e in enemies:
            d = math.hypot(e.x - self.x, e.y - self.y)
            if d < closest_dist:
                closest_dist = d
                closest = e

        if not closest or closest_dist > 320:
            self._shake_screen(12)
            return

        # AOE racun radius 110 di sekitar target
        for e in enemies:
            if math.hypot(e.x - closest.x, e.y - closest.y) <= 110:
                e.take_damage(damage, self.team)
                if hasattr(e, 'attack_timer'):
                    e.attack_timer = max(
                        getattr(e, 'attack_timer', 0), 60)
                if hasattr(e, 'apply_slow'):
                    e.apply_slow(0.6, 180)

        self._shake_screen(16)

    def _vhorethzir_e(self, enemies):
        """E - Corrosive Skin: aura defensif, slow musuh + heal.
        active_skill_timer = 80 (cocok dgn duration di renderer)."""
        stats = self._get_boss_stats()
        self.e_timer = stats.get("skill_e_cooldown", 420)
        self.active_skill = 'e'
        self.active_skill_timer = 80
        self.corrosive_active = True
        self.corrosive_timer = 360  # 6 detik aura

        # Semua musuh dekat kena korosi (slow, tanpa damage langsung)
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 200:
                if hasattr(e, 'attack_timer'):
                    e.attack_timer = max(
                        getattr(e, 'attack_timer', 0), 90)
                if hasattr(e, 'apply_slow'):
                    e.apply_slow(0.5, 240)

        # Heal 10% (nether regeneration)
        heal = int(self.max_hp * 0.10)
        self.hp = min(self.max_hp, self.hp + heal)

        self._shake_screen(14)

        try:
            import __main__
            if hasattr(__main__, 'game_instance'):
                game = __main__.game_instance
                game.effects.add_damage_number(
                    self.x, self.y - 30,
                    f"+{heal}", is_critical=True,
                    damage_type='heal')
        except Exception:
            pass

    def _vhorethzir_r(self, enemies):
        """R - Viper Strike: beam dari langit, AOE besar + slow berat.
        active_skill_timer = 100 (cocok dgn duration di renderer)."""
        stats = self._get_boss_stats()
        self.r_timer = stats.get("skill_r_cooldown", 780)
        self.active_skill = 'r'
        self.active_skill_timer = 100
        damage = stats.get("skill_r_damage", 720)

        closest = None
        closest_dist = 9999
        for e in enemies:
            d = math.hypot(e.x - self.x, e.y - self.y)
            if d < closest_dist:
                closest_dist = d
                closest = e

        cx = closest.x if closest else self.x
        cy = closest.y if closest else self.y

        # AOE masif radius 200 di titik hantam
        for e in enemies:
            if math.hypot(e.x - cx, e.y - cy) <= 200:
                e.take_damage(damage, self.team)
                if hasattr(e, 'attack_timer'):
                    e.attack_timer = max(
                        getattr(e, 'attack_timer', 0), 120)
                if hasattr(e, 'apply_slow'):
                    e.apply_slow(0.65, 300)

        self._shake_screen(30)

        # Heal 12% (menyerap racun korban)
        heal = int(self.max_hp * 0.12)
        self.hp = min(self.max_hp, self.hp + heal)


    def _smart_ai_vaerith(self, enemies, target_dist):
        """Smart AI Vaerith: web matriarch, melee bruiser + lifesteal."""
        if not hasattr(self, 'q_timer'):
            self.q_timer = 0
            self.w_timer = 0
            self.e_timer = 0
            self.r_timer = 0
            self.active_skill = None
            self.active_skill_timer = 0
        if self.q_timer > 0: self.q_timer -= 1
        if self.w_timer > 0: self.w_timer -= 1
        if self.e_timer > 0: self.e_timer -= 1
        if self.r_timer > 0: self.r_timer -= 1
        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0:
                self.active_skill = None

        nearby = sum(
            1 for e in enemies
            if math.hypot(e.x - self.x, e.y - self.y) <= 200
        )
        hp_ratio = self.hp / self.max_hp

        # PRIORITY 1: HP kritis -> R (Spawn Spiderlings, AOE + heal)
        if hp_ratio < 0.45 and self.r_timer == 0:
            self._vaerith_r(enemies)
            return
        # PRIORITY 2: HP menurun -> E (Insatiable Hunger, lifesteal)
        if hp_ratio < 0.7 and self.e_timer == 0:
            self._vaerith_e(enemies)
            return
        # PRIORITY 3: Banyak enemy -> W (Spin Web, slow area)
        if nearby >= 2 and self.w_timer == 0:
            self._vaerith_w(enemies)
            return
        # PRIORITY 4: Target dekat -> Q (Spiderling)
        if target_dist < 260 and self.q_timer == 0:
            self._vaerith_q(enemies)
            return

    def _vaerith_q(self, enemies):
        """Q - Spiderling: kirim laba-laba kecil ke enemy terdekat.
        active_skill_timer = 50 (cocok dgn duration renderer)."""
        stats = self._get_boss_stats()
        self.q_timer = stats.get("skill_q_cooldown", 200)
        self.active_skill = 'q'
        self.active_skill_timer = 50
        damage = stats.get("skill_q_damage", 300)

        closest = None
        closest_dist = 9999
        for e in enemies:
            d = math.hypot(e.x - self.x, e.y - self.y)
            if d < closest_dist:
                closest_dist = d
                closest = e

        if not closest or closest_dist > 280:
            self._shake_screen(8)
            return

        closest.take_damage(damage, self.team)
        if hasattr(closest, 'attack_timer'):
            closest.attack_timer = max(
                getattr(closest, 'attack_timer', 0), 40)

        self._shake_screen(10)

    def _vaerith_w(self, enemies):
        """W - Spin Web: jaring lengket, slow berat di area target.
        active_skill_timer = 70 (cocok dgn duration renderer)."""
        stats = self._get_boss_stats()
        self.w_timer = stats.get("skill_w_cooldown", 300)
        self.active_skill = 'w'
        self.active_skill_timer = 70
        damage = stats.get("skill_w_damage", 240)

        closest = None
        closest_dist = 9999
        for e in enemies:
            d = math.hypot(e.x - self.x, e.y - self.y)
            if d < closest_dist:
                closest_dist = d
                closest = e

        cx = closest.x if closest else self.x
        cy = closest.y if closest else self.y

        # Jaring radius 90: damage kecil tapi slow sangat berat
        for e in enemies:
            if math.hypot(e.x - cx, e.y - cy) <= 90:
                e.take_damage(damage, self.team)
                if hasattr(e, 'attack_timer'):
                    e.attack_timer = max(
                        getattr(e, 'attack_timer', 0), 75)
                if hasattr(e, 'apply_slow'):
                    e.apply_slow(0.7, 240)

        self._shake_screen(12)

    def _vaerith_e(self, enemies):
        """E - Insatiable Hunger: gigitan racun, curi HP.
        active_skill_timer = 55 (cocok dgn duration renderer)."""
        stats = self._get_boss_stats()
        self.e_timer = stats.get("skill_e_cooldown", 260)
        self.active_skill = 'e'
        self.active_skill_timer = 55
        damage = stats.get("skill_e_damage", 330)

        closest = None
        closest_dist = 9999
        for e in enemies:
            d = math.hypot(e.x - self.x, e.y - self.y)
            if d < closest_dist:
                closest_dist = d
                closest = e

        if not closest or closest_dist > 220:
            self._shake_screen(10)
            return

        closest.take_damage(damage, self.team)
        if hasattr(closest, 'attack_timer'):
            closest.attack_timer = max(
                getattr(closest, 'attack_timer', 0), 60)

        # Lifesteal 60% dari damage
        heal = int(damage * 0.6)
        self.hp = min(self.max_hp, self.hp + heal)

        self._shake_screen(14)

        try:
            import __main__
            if hasattr(__main__, 'game_instance'):
                game = __main__.game_instance
                game.effects.add_damage_number(
                    self.x, self.y - 30,
                    f"+{heal}", is_critical=True,
                    damage_type='heal')
        except Exception:
            pass

    def _vaerith_r(self, enemies):
        """R - Spawn Spiderlings: telur menetas, AOE besar + heal.
        active_skill_timer = 90 (cocok dgn duration renderer)."""
        stats = self._get_boss_stats()
        self.r_timer = stats.get("skill_r_cooldown", 620)
        self.active_skill = 'r'
        self.active_skill_timer = 90
        damage = stats.get("skill_r_damage", 470)

        # Kawanan menyebar dari boss: AOE radius 180
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 180:
                e.take_damage(damage, self.team)
                if hasattr(e, 'attack_timer'):
                    e.attack_timer = max(
                        getattr(e, 'attack_timer', 0), 100)
                if hasattr(e, 'apply_slow'):
                    e.apply_slow(0.6, 240)

        # Heal 15% (menyerap nutrisi korban)
        heal = int(self.max_hp * 0.15)
        self.hp = min(self.max_hp, self.hp + heal)

        self._shake_screen(24)

    def _smart_ai_xirthalis(self, enemies, target_dist):
        """Smart AI Xir'thalis: skitterer cepat, hit-and-run + rewind."""
        if not hasattr(self, 'q_timer'):
            self.q_timer = 0
            self.w_timer = 0
            self.e_timer = 0
            self.r_timer = 0
            self.active_skill = None
            self.active_skill_timer = 0
            self.shukuchi_active = False
            self.shukuchi_timer = 0
            self.timelapse_hp_mark = None
            self.timelapse_mark_timer = 0
        if self.q_timer > 0: self.q_timer -= 1
        if self.w_timer > 0: self.w_timer -= 1
        if self.e_timer > 0: self.e_timer -= 1
        if self.r_timer > 0: self.r_timer -= 1
        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0:
                self.active_skill = None

        # Shukuchi: buff kecepatan sementara
        if self.shukuchi_active:
            self.shukuchi_timer -= 1
            if self.shukuchi_timer <= 0:
                self.shukuchi_active = False
                stats = self._get_boss_stats()
                self.speed = stats.get("speed", 1.15)

        # Time Lapse menandai HP 5 detik lalu (untuk di-rewind)
        self.timelapse_mark_timer = getattr(
            self, 'timelapse_mark_timer', 0) + 1
        if self.timelapse_mark_timer >= 300:
            self.timelapse_mark_timer = 0
            self.timelapse_hp_mark = self.hp

        nearby = sum(
            1 for e in enemies
            if math.hypot(e.x - self.x, e.y - self.y) <= 200
        )
        hp_ratio = self.hp / self.max_hp

        # PRIORITY 1: HP kritis -> R (Time Lapse, kembalikan HP lampau)
        if hp_ratio < 0.4 and self.r_timer == 0:
            self._xirthalis_r(enemies)
            return
        # PRIORITY 2: HP menurun -> Q (Shukuchi, kabur + cepat)
        if hp_ratio < 0.65 and not self.shukuchi_active \
                and self.q_timer == 0:
            self._xirthalis_q(enemies)
            return
        # PRIORITY 3: Banyak enemy -> W (The Swarm)
        if nearby >= 2 and self.w_timer == 0:
            self._xirthalis_w(enemies)
            return
        # PRIORITY 4: Target dekat -> E (Geminate Attack, serangan ganda)
        if target_dist < 250 and self.e_timer == 0:
            self._xirthalis_e(enemies)
            return

    def _xirthalis_q(self, enemies):
        """Q - Shukuchi: menghilang + kecepatan naik (tanpa damage).
        active_skill_timer = 60; renderer Q tidak pakai durasi."""
        stats = self._get_boss_stats()
        self.q_timer = stats.get("skill_q_cooldown", 180)
        self.active_skill = 'q'
        self.active_skill_timer = 60
        self.shukuchi_active = True
        self.shukuchi_timer = 180  # 3 detik

        # Kecepatan naik 80% selama Shukuchi
        base_speed = stats.get("speed", 1.15)
        self.speed = base_speed * 1.8

        self._shake_screen(6)

    def _xirthalis_w(self, enemies):
        """W - The Swarm: kawanan laba-laba, slow + damage kecil.
        active_skill_timer = 70 (cocok dgn duration renderer)."""
        stats = self._get_boss_stats()
        self.w_timer = stats.get("skill_w_cooldown", 280)
        self.active_skill = 'w'
        self.active_skill_timer = 70
        damage = stats.get("skill_w_damage", 260)

        closest = None
        closest_dist = 9999
        for e in enemies:
            d = math.hypot(e.x - self.x, e.y - self.y)
            if d < closest_dist:
                closest_dist = d
                closest = e

        cx = closest.x if closest else self.x
        cy = closest.y if closest else self.y

        for e in enemies:
            if math.hypot(e.x - cx, e.y - cy) <= 100:
                e.take_damage(damage, self.team)
                if hasattr(e, 'attack_timer'):
                    e.attack_timer = max(
                        getattr(e, 'attack_timer', 0), 60)
                if hasattr(e, 'apply_slow'):
                    e.apply_slow(0.6, 200)

        self._shake_screen(12)

    def _xirthalis_e(self, enemies):
        """E - Geminate Attack: dua tebasan cepat ke satu target.
        active_skill_timer = 45 (cocok dgn duration renderer)."""
        stats = self._get_boss_stats()
        self.e_timer = stats.get("skill_e_cooldown", 220)
        self.active_skill = 'e'
        self.active_skill_timer = 45
        damage = stats.get("skill_e_damage", 340)

        closest = None
        closest_dist = 9999
        for e in enemies:
            d = math.hypot(e.x - self.x, e.y - self.y)
            if d < closest_dist:
                closest_dist = d
                closest = e

        if not closest or closest_dist > 270:
            self._shake_screen(8)
            return

        # DUA pukulan (geminate): 100% + 60%
        closest.take_damage(damage, self.team)
        if closest.alive:
            closest.take_damage(int(damage * 0.6), self.team)
        if hasattr(closest, 'attack_timer'):
            closest.attack_timer = max(
                getattr(closest, 'attack_timer', 0), 50)

        self._shake_screen(14)

    def _xirthalis_r(self, enemies):
        """R - Time Lapse: kembalikan HP ke kondisi 5 detik lalu.
        active_skill_timer = 60 (cocok dgn duration renderer)."""
        stats = self._get_boss_stats()
        self.r_timer = stats.get("skill_r_cooldown", 600)
        self.active_skill = 'r'
        self.active_skill_timer = 60

        # Rewind HP ke tanda 5 detik lalu (kalau lebih tinggi).
        mark = getattr(self, 'timelapse_hp_mark', None)
        if mark is None:
            mark = int(self.max_hp * 0.5)
        healed = max(0, min(self.max_hp, mark) - self.hp)
        self.hp = min(self.max_hp, max(self.hp, mark))

        # Dorong balik waktu musuh sekitar: stun singkat
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 160:
                if hasattr(e, 'attack_timer'):
                    e.attack_timer = max(
                        getattr(e, 'attack_timer', 0), 90)
                if hasattr(e, 'apply_slow'):
                    e.apply_slow(0.5, 180)

        self._shake_screen(20)

        if healed > 0:
            try:
                import __main__
                if hasattr(__main__, 'game_instance'):
                    game = __main__.game_instance
                    game.effects.add_damage_number(
                        self.x, self.y - 30,
                        f"+{healed}", is_critical=True,
                        damage_type='heal')
            except Exception:
                pass


    def _smart_ai_vhyssarion(self, enemies, target_dist):
        """Smart AI Vhyssarion: plague serpent, ranged poison/DoT caster."""
        if not hasattr(self, 'q_timer'):
            self.q_timer = 0
            self.w_timer = 0
            self.e_timer = 0
            self.r_timer = 0
            self.active_skill = None
            self.active_skill_timer = 0
        if self.q_timer > 0: self.q_timer -= 1
        if self.w_timer > 0: self.w_timer -= 1
        if self.e_timer > 0: self.e_timer -= 1
        if self.r_timer > 0: self.r_timer -= 1
        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0:
                self.active_skill = None

        nearby = sum(
            1 for e in enemies
            if math.hypot(e.x - self.x, e.y - self.y) <= 200
        )
        hp_ratio = self.hp / self.max_hp

        # PRIORITY 1: HP kritis + banyak musuh -> R (Poison Nova)
        if hp_ratio < 0.45 and nearby >= 2 and self.r_timer == 0:
            self._vhyssarion_r(enemies)
            return
        # PRIORITY 2: Banyak musuh -> Q (Noxious Plague, DoT area)
        if nearby >= 2 and self.q_timer == 0:
            self._vhyssarion_q(enemies)
            return
        # PRIORITY 3: Kerumunan -> E (Gale, tornado slow)
        if nearby >= 2 and self.e_timer == 0:
            self._vhyssarion_e(enemies)
            return
        # PRIORITY 4: Target dalam range -> W (Poison Sting)
        if target_dist < 270 and self.w_timer == 0:
            self._vhyssarion_w(enemies)
            return

    def _vhyssarion_q(self, enemies):
        """Q - Noxious Plague: kolam racun DoT di posisi musuh terdekat.
        active_skill_timer = 90 (cocok dgn duration renderer)."""
        stats = self._get_boss_stats()
        self.q_timer = stats.get("skill_q_cooldown", 240)
        self.active_skill = 'q'
        self.active_skill_timer = 90
        damage = stats.get("skill_q_damage", 280)

        closest = None
        closest_dist = 9999
        for e in enemies:
            d = math.hypot(e.x - self.x, e.y - self.y)
            if d < closest_dist:
                closest_dist = d
                closest = e

        cx = closest.x if closest else self.x
        cy = closest.y if closest else self.y

        # Kolam racun radius 100: damage + racun berkepanjangan
        for e in enemies:
            if math.hypot(e.x - cx, e.y - cy) <= 100:
                e.take_damage(damage, self.team)
                if hasattr(e, 'attack_timer'):
                    e.attack_timer = max(
                        getattr(e, 'attack_timer', 0), 70)
                if hasattr(e, 'apply_slow'):
                    e.apply_slow(0.65, 240)

        self._shake_screen(14)

    def _vhyssarion_w(self, enemies):
        """W - Poison Sting: sengat racun tunggal, damage tinggi.
        active_skill_timer = 40 (cocok dgn duration renderer)."""
        stats = self._get_boss_stats()
        self.w_timer = stats.get("skill_w_cooldown", 200)
        self.active_skill = 'w'
        self.active_skill_timer = 40
        damage = stats.get("skill_w_damage", 350)

        closest = None
        closest_dist = 9999
        for e in enemies:
            d = math.hypot(e.x - self.x, e.y - self.y)
            if d < closest_dist:
                closest_dist = d
                closest = e

        if not closest or closest_dist > 300:
            self._shake_screen(8)
            return

        closest.take_damage(damage, self.team)
        if hasattr(closest, 'attack_timer'):
            closest.attack_timer = max(
                getattr(closest, 'attack_timer', 0), 55)
        if hasattr(closest, 'apply_slow'):
            closest.apply_slow(0.5, 180)

        self._shake_screen(12)

    def _vhyssarion_e(self, enemies):
        """E - Gale: tornado racun, slow berat + damage sedang.
        active_skill_timer = 70 (cocok dgn duration renderer)."""
        stats = self._get_boss_stats()
        self.e_timer = stats.get("skill_e_cooldown", 280)
        self.active_skill = 'e'
        self.active_skill_timer = 70
        damage = stats.get("skill_e_damage", 300)

        closest = None
        closest_dist = 9999
        for e in enemies:
            d = math.hypot(e.x - self.x, e.y - self.y)
            if d < closest_dist:
                closest_dist = d
                closest = e

        cx = closest.x if closest else self.x
        cy = closest.y if closest else self.y

        # Tornado radius 85: slow paling berat di antara semua skill
        for e in enemies:
            if math.hypot(e.x - cx, e.y - cy) <= 85:
                e.take_damage(damage, self.team)
                if hasattr(e, 'attack_timer'):
                    e.attack_timer = max(
                        getattr(e, 'attack_timer', 0), 80)
                if hasattr(e, 'apply_slow'):
                    e.apply_slow(0.75, 200)

        self._shake_screen(16)

    def _vhyssarion_r(self, enemies):
        """R - Poison Nova: gelombang racun melingkar dari boss.
        active_skill_timer = 90 (cocok dgn duration renderer)."""
        stats = self._get_boss_stats()
        self.r_timer = stats.get("skill_r_cooldown", 640)
        self.active_skill = 'r'
        self.active_skill_timer = 90
        damage = stats.get("skill_r_damage", 430)

        # Nova radius 190 dari posisi boss (bukan target)
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 190:
                e.take_damage(damage, self.team)
                if hasattr(e, 'attack_timer'):
                    e.attack_timer = max(
                        getattr(e, 'attack_timer', 0), 110)
                if hasattr(e, 'apply_slow'):
                    e.apply_slow(0.6, 260)

        self._shake_screen(26)


    def _smart_ai_gornak(self, enemies, target_dist):
        """Smart AI Gornak: aggressive melee with 4 skills"""
        # Init timers
        if not hasattr(self, 'q_timer'):
            self.q_timer = 0
            self.w_timer = 0
            self.e_timer = 0
            self.r_timer = 0
            self.active_skill = None
            self.active_skill_timer = 0
            self.blink_target_x = 0
            self.blink_target_y = 0
            self.mana_void_x = 0
            self.mana_void_y = 0

        # Decrement timers
        if self.q_timer > 0:
            self.q_timer -= 1
        if self.w_timer > 0:
            self.w_timer -= 1
        if self.e_timer > 0:
            self.e_timer -= 1
        if self.r_timer > 0:
            self.r_timer -= 1
        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0:
                self.active_skill = None

        # Count nearby enemies
        nearby_count = sum(1 for e in enemies
                           if math.hypot(e.x - self.x,
                                         e.y - self.y) <= 150)

        hp_ratio = self.hp / self.max_hp

        # ═══ PRIORITY 1: HP kritis → R (Mana Void ultimate) ═══
        # Mana Void tidak lagi menunggu musuh berkerumun. Begitu HP Gornak
        # kritis dan ultimate siap, ia langsung mengeluarkannya.
        if hp_ratio < 0.4 and self.r_timer == 0:
            self._cast_r_mana_void(enemies)
            return

        # ═══ PRIORITY 2: Target jauh → W (Blink gap close) ═══
        if target_dist > 120 and self.w_timer == 0:
            self._cast_w_blink()
            return

        # ═══ PRIORITY 3: Banyak enemy → E (Counterspell shield) ═══
        if nearby_count >= 3 and self.e_timer == 0:
            self._cast_e_counterspell(enemies)
            return

        # ═══ PRIORITY 4: Target dekat → Q (Mana Break burst) ═══
        if target_dist < 200 and self.q_timer == 0:
            self._cast_q_mana_break()
            return

    def _cast_q_mana_break(self):
        """Q - Mana Break: energy projectile burst"""
        self.q_timer = 180
        self.active_skill = 'q'
        self.active_skill_timer = 40

        stats = self._get_boss_stats()
        damage = stats.get("skill_q_damage", 180)

        if self.target and self.target.alive:
            self.target.take_damage(damage, self.team)

        self._shake_screen(10)

    def _cast_w_blink(self):
        """W - Blink: teleport ke dekat target"""
        self.w_timer = 240
        self.active_skill = 'w'
        self.active_skill_timer = 25

        if self.target and self.target.alive:
            # Store old position untuk visual
            self.blink_from_x = self.x
            self.blink_from_y = self.y

            # Teleport ke posisi dekat target
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            dist = math.hypot(dx, dy)

            if dist > 0:
                # Stop 60 units before target
                offset = max(0, dist - 60)
                self.x = self.x + (dx / dist) * offset
                self.y = self.y + (dy / dist) * offset

            # Store new position
            self.blink_to_x = self.x
            self.blink_to_y = self.y

        self._shake_screen(8)

    def _cast_e_counterspell(self, enemies):
        """E - Counterspell: shield yang damage enemy dalam range"""
        self.e_timer = 300
        self.active_skill = 'e'
        self.active_skill_timer = 60

        stats = self._get_boss_stats()
        damage = stats.get("skill_e_damage", 150)

        # AOE damage semua enemy dekat
        for e in enemies:
            dist = math.hypot(e.x - self.x, e.y - self.y)
            if dist <= 100:
                e.take_damage(damage, self.team)
                # Silence effect (stun)
                if hasattr(e, 'attack_timer'):
                    e.attack_timer = max(e.attack_timer, 60)

        self._shake_screen(12)

    def _cast_r_mana_void(self, enemies):
        """R - Mana Void: massive AOE ultimate"""
        self.r_timer = 540
        self.active_skill = 'r'
        self.active_skill_timer = 90

        stats = self._get_boss_stats()
        damage = stats.get("skill_r_damage", 380)

        # Store void location (di posisi boss)
        self.mana_void_x = self.x
        self.mana_void_y = self.y

        # Massive AOE
        for e in enemies:
            if math.hypot(e.x - self.mana_void_x,
                          e.y - self.mana_void_y) <= 180:
                e.take_damage(damage, self.team)

        self._shake_screen(20)

    def _smart_ai_morgath(self, enemies, target_dist):
        """Smart AI Morgath: ranged temporal mage"""
        # Init timers
        if not hasattr(self, 'q_timer'):
            self.q_timer = 0
            self.w_timer = 0
            self.e_timer = 0
            self.r_timer = 0
            self.active_skill = None
            self.active_skill_timer = 0
            self.flux_target = None
            self.flux_active_timer = 0
            self.clones_active_timer = 0
            self.clones_positions = []

        # Decrement timers
        if self.q_timer > 0:
            self.q_timer -= 1
        if self.w_timer > 0:
            self.w_timer -= 1
        if self.e_timer > 0:
            self.e_timer -= 1
        if self.r_timer > 0:
            self.r_timer -= 1
        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0:
                self.active_skill = None

        # Flux DOT (persistent debuff)
        if self.flux_active_timer > 0:
            self.flux_active_timer -= 1
            # Damage per tick
            if self.flux_active_timer % 30 == 0:
                if self.flux_target and self.flux_target.alive:
                    stats = self._get_boss_stats()
                    dot_damage = stats.get("skill_w_damage", 150) // 4
                    self.flux_target.take_damage(dot_damage, self.team)
                    # Slow effect
                    if hasattr(self.flux_target, 'apply_slow'):
                        self.flux_target.apply_slow(0.4, 60)

        # Clones active (Tempest Double)
        if self.clones_active_timer > 0:
            self.clones_active_timer -= 1
            # Clones do basic attack
            if self.clones_active_timer % 40 == 0:
                if self.target and self.target.alive:
                    stats = self._get_boss_stats()
                    clone_damage = int(self.damage * 0.5)
                    self.target.take_damage(clone_damage, self.team)

        # Count nearby enemies
        close_count = sum(1 for e in enemies
                          if math.hypot(e.x - self.x,
                                        e.y - self.y) <= 200)

        hp_ratio = self.hp / self.max_hp

        # ═══ PRIORITY 1: HP kritis → R (Tempest Double clones) ═══
        if hp_ratio < 0.5 and self.r_timer == 0:
            self._cast_r_tempest_double()
            return

        # ═══ PRIORITY 2: Enemy dekat → E (Magnetic Field defensive) ═══
        if close_count >= 2 and self.e_timer == 0:
            self._cast_e_magnetic_field(enemies)
            return

        # ═══ PRIORITY 3: Target isolated → W (Flux debuff) ═══
        if target_dist < 300 and self.w_timer == 0 and \
                self.flux_active_timer <= 0:
            self._cast_w_flux()
            return

        # ═══ PRIORITY 4: Range attack → Q (Spark Wraith) ═══
        if target_dist < 350 and self.q_timer == 0:
            self._cast_q_spark_wraith()
            return

    def _cast_q_spark_wraith(self):
        """Q - Spark Wraith: purple orb projectile"""
        self.q_timer = 200
        self.active_skill = 'q'
        self.active_skill_timer = 50

        stats = self._get_boss_stats()
        damage = stats.get("skill_q_damage", 200)

        if self.target and self.target.alive:
            self.target.take_damage(damage, self.team)

        self._shake_screen(10)

    def _cast_w_flux(self):
        """W - Flux: debuff target dengan DOT + slow"""
        self.w_timer = 300
        self.active_skill = 'w'
        self.active_skill_timer = 40

        stats = self._get_boss_stats()
        damage = stats.get("skill_w_damage", 150)

        if self.target and self.target.alive:
            # Store target for DOT
            self.flux_target = self.target
            self.flux_active_timer = 240  # 4 detik DOT

            # Initial damage
            self.target.take_damage(damage // 2, self.team)

            # Initial slow
            if hasattr(self.target, 'apply_slow'):
                self.target.apply_slow(0.5, 240)

        self._shake_screen(8)

    def _cast_e_magnetic_field(self, enemies):
        """E - Magnetic Field: bubble shield yang damage nearby"""
        self.e_timer = 360
        self.active_skill = 'e'
        self.active_skill_timer = 90

        stats = self._get_boss_stats()
        damage = stats.get("skill_e_damage", 100)

        # AOE damage nearby
        for e in enemies:
            dist = math.hypot(e.x - self.x, e.y - self.y)
            if dist <= 90:
                e.take_damage(damage, self.team)
                # Stun sebentar
                if hasattr(e, 'attack_timer'):
                    e.attack_timer = max(e.attack_timer, 45)

        # Heal boss sedikit (defensive)
        heal = int(self.max_hp * 0.08)
        self.hp = min(self.max_hp, self.hp + heal)

        self._shake_screen(10)

    def _cast_r_tempest_double(self):
        """R - Tempest Double: summon 2 clones"""
        self.r_timer = 720
        self.active_skill = 'r'
        self.active_skill_timer = 60

        # Clones active for 8 detik
        self.clones_active_timer = 480

        # Store clone positions (kiri kanan boss)
        self.clones_positions = [
            (-60, 0),  # left offset
            (60, 0),  # right offset
        ]

        # Small heal (temporal restoration)
        heal = int(self.max_hp * 0.15)
        self.hp = min(self.max_hp, self.hp + heal)

        self._shake_screen(15)

    def _smart_ai_drakar(self, enemies, target_dist):
        """Smart AI Drakar: aggressive berserker with 4 skills"""
        # Init timers
        if not hasattr(self, 'q_timer'):
            self.q_timer = 0
            self.w_timer = 0
            self.e_timer = 0
            self.r_timer = 0
            self.active_skill = None
            self.active_skill_timer = 0
            self.rage_active = False
            self.rage_timer = 0
            self.defense_boost = False
            self.defense_timer = 0

        # Decrement timers
        if self.q_timer > 0:
            self.q_timer -= 1
        if self.w_timer > 0:
            self.w_timer -= 1
        if self.e_timer > 0:
            self.e_timer -= 1
        if self.r_timer > 0:
            self.r_timer -= 1
        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0:
                self.active_skill = None

        # Battle Hunger rage buff timer
        if self.rage_active:
            self.rage_timer -= 1
            if self.rage_timer <= 0:
                self.rage_active = False
                # Reset damage
                stats = self._get_boss_stats()
                self.damage = stats.get("damage", 80)

        # Berserker's Call defense boost timer
        if self.defense_boost:
            self.defense_timer -= 1
            if self.defense_timer <= 0:
                self.defense_boost = False

        # Count nearby enemies
        nearby_count = sum(1 for e in enemies
                           if math.hypot(e.x - self.x,
                                         e.y - self.y) <= 120)

        # Check low HP enemies (for execute)
        low_hp_target = None
        if self.target and self.target.alive:
            target_hp_ratio = self.target.hp / self.target.max_hp
            if target_hp_ratio < 0.3:
                low_hp_target = self.target

        hp_ratio = self.hp / self.max_hp

        # ═══ PRIORITY 1: Target low HP → R (Culling Blade execute!) ═══
        if low_hp_target and target_dist < 100 and self.r_timer == 0:
            self._cast_r_culling_blade()
            return

        # ═══ PRIORITY 2: HP kritis → Q (Battle Hunger rage) ═══
        if hp_ratio < 0.4 and not self.rage_active and \
                self.q_timer == 0:
            self._cast_q_battle_hunger()
            return

        # ═══ PRIORITY 3: Banyak enemy → W (Counter Helix spin) ═══
        if nearby_count >= 2 and self.w_timer == 0:
            self._cast_w_counter_helix(enemies)
            return

        # ═══ PRIORITY 4: HP menurun + no defense → E (Berserker's Call) ═══
        if hp_ratio < 0.6 and not self.defense_boost and \
                self.e_timer == 0:
            self._cast_e_berserkers_call(enemies)
            return

    def _cast_q_battle_hunger(self):
        """Q - Battle Hunger: self-buff rage mode"""
        self.q_timer = 420
        self.active_skill = 'q'
        self.active_skill_timer = 90
        self.rage_active = True
        self.rage_timer = 300  # 5 detik rage

        stats = self._get_boss_stats()
        base_damage = stats.get("damage", 80)
        self.damage = int(base_damage * 1.5)  # +50% damage

        # Sedikit heal
        heal = int(self.max_hp * 0.1)
        self.hp = min(self.max_hp, self.hp + heal)

        self._shake_screen(12)

        try:
            import __main__
            if hasattr(__main__, 'game_instance'):
                game = __main__.game_instance
                game.effects.add_damage_number(
                    self.x, self.y - 30,
                    f"RAGE! +{heal}", is_critical=True,
                    damage_type='heal')
        except Exception:
            pass

    def _cast_w_counter_helix(self, enemies):
        """W - Counter Helix: spin AOE damage"""
        self.w_timer = 240
        self.active_skill = 'w'
        self.active_skill_timer = 45

        stats = self._get_boss_stats()
        damage = stats.get("skill_w_damage", 220)

        # AOE damage all nearby
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 100:
                e.take_damage(damage, self.team)

        self._shake_screen(15)

    def _cast_e_berserkers_call(self, enemies):
        """E - Berserker's Call: roar + AOE damage + defense buff"""
        self.e_timer = 360
        self.active_skill = 'e'
        self.active_skill_timer = 60
        self.defense_boost = True
        self.defense_timer = 180  # 3 detik defense

        stats = self._get_boss_stats()
        damage = stats.get("skill_e_damage", 150)

        # AOE damage + slight push effect
        for e in enemies:
            dist = math.hypot(e.x - self.x, e.y - self.y)
            if dist <= 120:
                e.take_damage(damage, self.team)
                # Stun sebentar (dari roar effect)
                if hasattr(e, 'attack_timer'):
                    e.attack_timer = max(e.attack_timer, 30)

        self._shake_screen(18)

    def _cast_r_culling_blade(self):
        """R - Culling Blade: massive execute damage"""
        self.r_timer = 480
        self.active_skill = 'r'
        self.active_skill_timer = 60

        stats = self._get_boss_stats()
        damage = stats.get("skill_r_damage", 450)

        if self.target and self.target.alive:
            target_hp_ratio = self.target.hp / self.target.max_hp

            # Execute bonus damage kalau target < 30% HP
            if target_hp_ratio < 0.3:
                damage = int(damage * 2)  # Double damage for execute
                # Reset cooldown kalau execute successful
                self.r_timer = 120  # Fast reset

            self.target.take_damage(damage, self.team)

        self._shake_screen(25)

    # ═══════════════════════════════════════════════════
    # RAZAK AI (Batrider - ranged fire)
    # ═══════════════════════════════════════════════════

    def _smart_ai_razak(self, enemies, target_dist):
        if not hasattr(self, 'q_timer'):
            self.q_timer = 0
            self.w_timer = 0
            self.e_timer = 0
            self.r_timer = 0
            self.active_skill = None
            self.active_skill_timer = 0
        if self.q_timer > 0: self.q_timer -= 1
        if self.w_timer > 0: self.w_timer -= 1
        if self.e_timer > 0: self.e_timer -= 1
        if self.r_timer > 0: self.r_timer -= 1
        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0:
                self.active_skill = None

        nearby = sum(1 for e in enemies
                     if math.hypot(e.x - self.x, e.y - self.y) <= 180)

        if nearby >= 3 and self.r_timer == 0:
            self._razak_r(enemies);
            return
        if target_dist > 120 and target_dist < 260 and self.e_timer == 0:
            self._razak_e(enemies);
            return
        if target_dist <= 220 and self.w_timer == 0:
            self._razak_w(enemies);
            return
        if target_dist <= 260 and self.q_timer == 0:
            self._razak_q(enemies);
            return

    def _razak_q(self, enemies):
        stats = self._get_boss_stats()
        self.q_timer = stats.get("skill_q_cooldown", 220)
        self.active_skill = 'q'
        self.active_skill_timer = 40
        if self.target and self.target.alive:
            damage = stats.get("skill_q_damage", 160)
            for e in enemies:
                if math.hypot(e.x - self.target.x,
                              e.y - self.target.y) <= 75:
                    e.take_damage(damage, self.team)
                    if hasattr(e, 'apply_slow'):
                        e.apply_slow(0.35, 120)
        self._shake_screen(10)

    def _razak_w(self, enemies):
        stats = self._get_boss_stats()
        self.w_timer = stats.get("skill_w_cooldown", 260)
        self.active_skill = 'w'
        self.active_skill_timer = 50
        if self.target and self.target.alive:
            damage = stats.get("skill_w_damage", 220)
            for e in enemies:
                if math.hypot(e.x - self.target.x,
                              e.y - self.target.y) <= 95:
                    e.take_damage(damage, self.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(
                            getattr(e, 'attack_timer', 0), 45)
        self._shake_screen(14)

    def _razak_e(self, enemies):
        stats = self._get_boss_stats()
        self.e_timer = stats.get("skill_e_cooldown", 280)
        self.active_skill = 'e'
        self.active_skill_timer = 35
        if self.target and self.target.alive:
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                jump = min(110, max(40, dist - 50))
                self.x += (dx / dist) * jump
                self.y += (dy / dist) * jump
                self.direction = 1 if dx > 0 else -1
            damage = stats.get("skill_e_damage", 180)
            for e in enemies:
                if math.hypot(e.x - self.x, e.y - self.y) <= 80:
                    e.take_damage(damage, self.team)
        self._shake_screen(12)

    def _razak_r(self, enemies):
        stats = self._get_boss_stats()
        self.r_timer = stats.get("skill_r_cooldown", 520)
        self.active_skill = 'r'
        self.active_skill_timer = 90
        damage = stats.get("skill_r_damage", 340)
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 180:
                e.take_damage(damage, self.team)
        self._shake_screen(20)

    # ═══════════════════════════════════════════════════
    # KHALROS AI (Beastmaster - melee + summons)
    # ═══════════════════════════════════════════════════

    def _smart_ai_khalros(self, enemies, target_dist):
        if not hasattr(self, 'q_timer'):
            self.q_timer = 0
            self.w_timer = 0
            self.e_timer = 0
            self.r_timer = 0
            self.active_skill = None
            self.active_skill_timer = 0
        if self.q_timer > 0: self.q_timer -= 1
        if self.w_timer > 0: self.w_timer -= 1
        if self.e_timer > 0: self.e_timer -= 1
        if self.r_timer > 0: self.r_timer -= 1
        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0:
                self.active_skill = None

        nearby = sum(1 for e in enemies
                     if math.hypot(e.x - self.x, e.y - self.y) <= 140)
        hp_ratio = self.hp / self.max_hp

        if nearby >= 3 and self.r_timer == 0:
            self._khalros_r(enemies);
            return
        if hp_ratio < 0.7 and self.w_timer == 0:
            self._khalros_w(enemies);
            return
        if target_dist > 110 and self.e_timer == 0:
            self._khalros_e(enemies);
            return
        if target_dist <= 260 and self.q_timer == 0:
            self._khalros_q(enemies);
            return

    def _khalros_q(self, enemies):
        stats = self._get_boss_stats()
        self.q_timer = stats.get("skill_q_cooldown", 220)
        self.active_skill = 'q'
        self.active_skill_timer = 50
        if self.target and self.target.alive:
            damage = stats.get("skill_q_damage", 210)
            for e in enemies:
                if math.hypot(e.x - self.target.x,
                              e.y - self.target.y) <= 70:
                    e.take_damage(damage, self.team)
        self._shake_screen(10)

    def _khalros_w(self, enemies):
        stats = self._get_boss_stats()
        self.w_timer = stats.get("skill_w_cooldown", 300)
        self.active_skill = 'w'
        self.active_skill_timer = 60
        damage = stats.get("skill_w_damage", 160)
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 120:
                e.take_damage(damage, self.team)
                if hasattr(e, 'apply_slow'):
                    e.apply_slow(0.5, 90)
        heal = int(self.max_hp * 0.08)
        self.hp = min(self.max_hp, self.hp + heal)
        self._shake_screen(12)

    def _khalros_e(self, enemies):
        stats = self._get_boss_stats()
        self.e_timer = stats.get("skill_e_cooldown", 280)
        self.active_skill = 'e'
        self.active_skill_timer = 45
        if self.target and self.target.alive:
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                charge = min(90, max(35, dist - 45))
                self.x += (dx / dist) * charge
                self.y += (dy / dist) * charge
                self.direction = 1 if dx > 0 else -1
            damage = stats.get("skill_e_damage", 220)
            for e in enemies:
                if math.hypot(e.x - self.x, e.y - self.y) <= 85:
                    e.take_damage(damage, self.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(
                            getattr(e, 'attack_timer', 0), 40)
        self._shake_screen(14)

    def _khalros_r(self, enemies):
        stats = self._get_boss_stats()
        self.r_timer = stats.get("skill_r_cooldown", 560)
        self.active_skill = 'r'
        self.active_skill_timer = 70
        damage = stats.get("skill_r_damage", 380)
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 200:
                e.take_damage(damage, self.team)
                if hasattr(e, 'attack_timer'):
                    e.attack_timer = max(
                        getattr(e, 'attack_timer', 0), 30)
        self._shake_screen(20)

    # ═══════════════════════════════════════════════════
    # GORATH AI (Bloodseeker - aggressive melee)
    # ═══════════════════════════════════════════════════

    def _smart_ai_gorath(self, enemies, target_dist):
        if not hasattr(self, 'q_timer'):
            self.q_timer = 0
            self.w_timer = 0
            self.e_timer = 0
            self.r_timer = 0
            self.active_skill = None
            self.active_skill_timer = 0
            self.rage_active = False
            self.rage_timer = 0
        if self.q_timer > 0: self.q_timer -= 1
        if self.w_timer > 0: self.w_timer -= 1
        if self.e_timer > 0: self.e_timer -= 1
        if self.r_timer > 0: self.r_timer -= 1
        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0:
                self.active_skill = None
        if self.rage_active:
            self.rage_timer -= 1
            if self.rage_timer <= 0:
                self.rage_active = False
                stats = self._get_boss_stats()
                self.damage = stats.get("damage", 94)
                self.speed = stats.get("speed", 1.18)

        nearby = sum(1 for e in enemies
                     if math.hypot(e.x - self.x, e.y - self.y) <= 150)
        hp_ratio = self.hp / self.max_hp

        low_hp_target = (
                self.target and self.target.alive and
                (self.target.hp / max(1, self.target.max_hp)) < 0.35
        )

        if low_hp_target and self.r_timer == 0:
            self._gorath_r(enemies);
            return
        if not self.rage_active and hp_ratio < 0.7 and self.q_timer == 0:
            self._gorath_q();
            return
        if nearby >= 2 and self.w_timer == 0:
            self._gorath_w(enemies);
            return
        if target_dist > 90 and self.e_timer == 0:
            self._gorath_e(enemies);
            return
        if hp_ratio < 0.45 and self.r_timer == 0:
            self._gorath_r(enemies);
            return

    def _gorath_q(self):
        stats = self._get_boss_stats()
        self.q_timer = stats.get("skill_q_cooldown", 420)
        self.active_skill = 'q'
        self.active_skill_timer = 90
        self.rage_active = True
        self.rage_timer = 300
        self.damage = int(stats.get("damage", 94) * 1.4)
        self.speed = stats.get("speed", 1.18) * 1.2
        heal = int(self.max_hp * 0.08)
        self.hp = min(self.max_hp, self.hp + heal)
        self._shake_screen(12)

    def _gorath_w(self, enemies):
        stats = self._get_boss_stats()
        self.w_timer = stats.get("skill_w_cooldown", 240)
        self.active_skill = 'w'
        self.active_skill_timer = 60
        damage = stats.get("skill_w_damage", 210)
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 150:
                e.take_damage(damage, self.team)
                if hasattr(e, 'attack_timer'):
                    e.attack_timer = max(
                        getattr(e, 'attack_timer', 0), 50)
        self._shake_screen(15)

    def _gorath_e(self, enemies):
        stats = self._get_boss_stats()
        self.e_timer = stats.get("skill_e_cooldown", 260)
        self.active_skill = 'e'
        self.active_skill_timer = 35
        if self.target and self.target.alive:
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                leap = min(120, max(45, dist - 35))
                self.x += (dx / dist) * leap
                self.y += (dy / dist) * leap
                self.direction = 1 if dx > 0 else -1
            damage = stats.get("skill_e_damage", 190)
            for e in enemies:
                if math.hypot(e.x - self.x, e.y - self.y) <= 85:
                    e.take_damage(damage, self.team)
        self._shake_screen(12)

    def _gorath_r(self, enemies):
        stats = self._get_boss_stats()
        self.r_timer = stats.get("skill_r_cooldown", 560)
        self.active_skill = 'r'
        self.active_skill_timer = 90
        damage = stats.get("skill_r_damage", 420)
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 190:
                e.take_damage(damage, self.team)
        if self.target and self.target.alive:
            self.target.take_damage(damage // 2, self.team)
        self._shake_screen(22)

    # ═══════════════════════════════════════════════════
    # VARKUL AI (Frostbound Sorcerer - ranged)
    # ═══════════════════════════════════════════════════

    def _smart_ai_varkul(self, enemies, target_dist):
        if not hasattr(self, 'q_timer'):
            self.q_timer = 0
            self.w_timer = 0
            self.e_timer = 0
            self.r_timer = 0
            self.active_skill = None
            self.active_skill_timer = 0
        if self.q_timer > 0: self.q_timer -= 1
        if self.w_timer > 0: self.w_timer -= 1
        if self.e_timer > 0: self.e_timer -= 1
        if self.r_timer > 0: self.r_timer -= 1
        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0:
                self.active_skill = None

        nearby = sum(1 for e in enemies
                     if math.hypot(e.x - self.x, e.y - self.y) <= 200)
        hp_ratio = self.hp / self.max_hp

        if nearby >= 3 and self.r_timer == 0:
            self._varkul_r(enemies);
            return
        if hp_ratio < 0.5 and self.e_timer == 0:
            self._varkul_e();
            return
        if target_dist <= 250 and self.w_timer == 0:
            self._varkul_w(enemies);
            return
        if target_dist <= 280 and self.q_timer == 0:
            self._varkul_q();
            return

    def _varkul_q(self):
        stats = self._get_boss_stats()
        self.q_timer = stats.get("skill_q_cooldown", 240)
        self.active_skill = 'q'
        self.active_skill_timer = 50
        damage = stats.get("skill_q_damage", 220)
        if self.target and self.target.alive:
            self.target.take_damage(damage, self.team)
            if hasattr(self.target, 'apply_slow'):
                self.target.apply_slow(0.4, 120)
        self._shake_screen(10)

    def _varkul_w(self, enemies):
        stats = self._get_boss_stats()
        self.w_timer = stats.get("skill_w_cooldown", 300)
        self.active_skill = 'w'
        self.active_skill_timer = 60
        damage = stats.get("skill_w_damage", 280)
        if self.target and self.target.alive:
            self.target.take_damage(damage, self.team)
            if hasattr(self.target, 'attack_timer'):
                self.target.attack_timer = max(
                    getattr(self.target, 'attack_timer', 0), 60)
        self._shake_screen(14)

    def _varkul_e(self):
        stats = self._get_boss_stats()
        self.e_timer = stats.get("skill_e_cooldown", 360)
        self.active_skill = 'e'
        self.active_skill_timer = 50
        damage = stats.get("skill_e_damage", 160)
        if self.target and self.target.alive:
            self.target.take_damage(damage, self.team)
        heal = int(self.max_hp * 0.12)
        self.hp = min(self.max_hp, self.hp + heal)
        self._shake_screen(10)

    def _varkul_r(self, enemies):
        stats = self._get_boss_stats()
        self.r_timer = stats.get("skill_r_cooldown", 540)
        self.active_skill = 'r'
        self.active_skill_timer = 80
        damage = stats.get("skill_r_damage", 380)
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 220:
                e.take_damage(damage, self.team)
                if hasattr(e, 'apply_slow'):
                    e.apply_slow(0.5, 180)
        self._shake_screen(20)

    # ═══════════════════════════════════════════════════
    # XERATHIS AI (Crystal Sorceress - ranged AOE)
    # ═══════════════════════════════════════════════════

    def _smart_ai_xerathis(self, enemies, target_dist):
        if not hasattr(self, 'q_timer'):
            self.q_timer = 0
            self.w_timer = 0
            self.e_timer = 0
            self.r_timer = 0
            self.active_skill = None
            self.active_skill_timer = 0
            self.arcane_buff_active = False
            self.arcane_buff_timer = 0
        if self.q_timer > 0: self.q_timer -= 1
        if self.w_timer > 0: self.w_timer -= 1
        if self.e_timer > 0: self.e_timer -= 1
        if self.r_timer > 0: self.r_timer -= 1
        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0:
                self.active_skill = None
        if self.arcane_buff_active:
            self.arcane_buff_timer -= 1
            if self.arcane_buff_timer <= 0:
                self.arcane_buff_active = False
                self.damage = self.base_damage

        nearby = sum(1 for e in enemies
                     if math.hypot(e.x - self.x, e.y - self.y) <= 220)
        hp_ratio = self.hp / self.max_hp

        if nearby >= 4 and self.r_timer == 0:
            self._xerathis_r(enemies);
            return
        if not self.arcane_buff_active and self.e_timer == 0:
            self._xerathis_e();
            return
        if nearby >= 2 and self.q_timer == 0:
            self._xerathis_q(enemies);
            return
        if target_dist <= 280 and self.w_timer == 0:
            self._xerathis_w();
            return

    def _xerathis_q(self, enemies):
        stats = self._get_boss_stats()
        self.q_timer = stats.get("skill_q_cooldown", 260)
        self.active_skill = 'q'
        self.active_skill_timer = 60
        damage = stats.get("skill_q_damage", 200)
        if self.target and self.target.alive:
            tx, ty = self.target.x, self.target.y
            for e in enemies:
                if math.hypot(e.x - tx, e.y - ty) <= 90:
                    e.take_damage(damage, self.team)
                    if hasattr(e, 'apply_slow'):
                        e.apply_slow(0.4, 120)
        self._shake_screen(12)

    def _xerathis_w(self):
        stats = self._get_boss_stats()
        self.w_timer = stats.get("skill_w_cooldown", 240)
        self.active_skill = 'w'
        self.active_skill_timer = 50
        damage = stats.get("skill_w_damage", 280)
        if self.target and self.target.alive:
            self.target.take_damage(damage, self.team)
            if hasattr(self.target, 'attack_timer'):
                self.target.attack_timer = max(
                    getattr(self.target, 'attack_timer', 0), 75)
            if hasattr(self.target, 'apply_slow'):
                self.target.apply_slow(0.6, 180)
        self._shake_screen(14)

    def _xerathis_e(self):
        stats = self._get_boss_stats()
        self.e_timer = stats.get("skill_e_cooldown", 420)
        self.active_skill = 'e'
        self.active_skill_timer = 90
        self.arcane_buff_active = True
        self.arcane_buff_timer = 360
        self.damage = int(self.base_damage * 1.3)
        heal = int(self.max_hp * 0.1)
        self.hp = min(self.max_hp, self.hp + heal)
        self._shake_screen(10)

    def _xerathis_r(self, enemies):
        stats = self._get_boss_stats()
        self.r_timer = stats.get("skill_r_cooldown", 580)
        self.active_skill = 'r'
        self.active_skill_timer = 100
        damage = stats.get("skill_r_damage", 360)
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 240:
                e.take_damage(damage, self.team)
                if hasattr(e, 'apply_slow'):
                    e.apply_slow(0.55, 240)
        self._shake_screen(24)

    # ═══════════════════════════════════════════════════
    # NYZRAK AI (Wyvern Rider - hybrid ranged/melee)
    # ═══════════════════════════════════════════════════

    def _smart_ai_nyzrak(self, enemies, target_dist):
        if not hasattr(self, 'q_timer'):
            self.q_timer = 0
            self.w_timer = 0
            self.e_timer = 0
            self.r_timer = 0
            self.active_skill = None
            self.active_skill_timer = 0
            self.shield_active = False
            self.shield_timer = 0
        if self.q_timer > 0: self.q_timer -= 1
        if self.w_timer > 0: self.w_timer -= 1
        if self.e_timer > 0: self.e_timer -= 1
        if self.r_timer > 0: self.r_timer -= 1
        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0:
                self.active_skill = None
        if self.shield_active:
            self.shield_timer -= 1
            if self.shield_timer <= 0:
                self.shield_active = False

        nearby = sum(1 for e in enemies
                     if math.hypot(e.x - self.x, e.y - self.y) <= 180)
        hp_ratio = self.hp / self.max_hp

        if hp_ratio < 0.45 and not self.shield_active and self.r_timer == 0:
            self._nyzrak_r(enemies);
            return
        if target_dist <= 220 and self.e_timer == 0:
            self._nyzrak_e();
            return
        if nearby >= 2 and self.w_timer == 0:
            self._nyzrak_w(enemies);
            return
        if target_dist <= 260 and self.q_timer == 0:
            self._nyzrak_q();
            return

    def _nyzrak_q(self):
        stats = self._get_boss_stats()
        self.q_timer = stats.get("skill_q_cooldown", 240)
        self.active_skill = 'q'
        self.active_skill_timer = 50
        damage = stats.get("skill_q_damage", 240)
        if self.target and self.target.alive:
            self.target.take_damage(damage, self.team)
            if hasattr(self.target, 'apply_slow'):
                self.target.apply_slow(0.4, 120)
        self._shake_screen(12)

    def _nyzrak_w(self, enemies):
        stats = self._get_boss_stats()
        self.w_timer = stats.get("skill_w_cooldown", 260)
        self.active_skill = 'w'
        self.active_skill_timer = 50
        damage = stats.get("skill_w_damage", 200)
        if self.target and self.target.alive:
            tx, ty = self.target.x, self.target.y
            for e in enemies:
                if math.hypot(e.x - tx, e.y - ty) <= 80:
                    e.take_damage(damage, self.team)
        self._shake_screen(14)

    def _nyzrak_e(self):
        stats = self._get_boss_stats()
        self.e_timer = stats.get("skill_e_cooldown", 340)
        self.active_skill = 'e'
        self.active_skill_timer = 70
        damage = stats.get("skill_e_damage", 220)
        if self.target and self.target.alive:
            self.target.take_damage(damage, self.team)
            if hasattr(self.target, 'attack_timer'):
                self.target.attack_timer = max(
                    getattr(self.target, 'attack_timer', 0), 90)
            if hasattr(self.target, 'apply_slow'):
                self.target.apply_slow(0.7, 180)
        self._shake_screen(16)

    def _nyzrak_r(self, enemies):
        stats = self._get_boss_stats()
        self.r_timer = stats.get("skill_r_cooldown", 560)
        self.active_skill = 'r'
        self.active_skill_timer = 90
        self.shield_active = True
        self.shield_timer = 240
        damage = stats.get("skill_r_damage", 400)
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 200:
                e.take_damage(damage, self.team)
                if hasattr(e, 'apply_slow'):
                    e.apply_slow(0.5, 180)
        heal = int(self.max_hp * 0.15)
        self.hp = min(self.max_hp, self.hp + heal)
        self._shake_screen(22)

    # ===== ZHAROK AI (Flaming Archer) =====
    def _smart_ai_zharok(self, enemies, target_dist):
        if not hasattr(self, 'q_timer'):
            self.q_timer = 0
            self.w_timer = 0
            self.e_timer = 0
            self.r_timer = 0
            self.active_skill = None
            self.active_skill_timer = 0
        if self.q_timer > 0: self.q_timer -= 1
        if self.w_timer > 0: self.w_timer -= 1
        if self.e_timer > 0: self.e_timer -= 1
        if self.r_timer > 0: self.r_timer -= 1
        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0:
                self.active_skill = None

        hp_ratio = self.hp / self.max_hp
        nearby = sum(1 for e in enemies if math.hypot(e.x - self.x, e.y - self.y) <= 200)

        if hp_ratio < 0.4 and self.r_timer == 0:
            self._cast_zharok_r(enemies);
            return
        if nearby >= 2 and self.e_timer == 0:
            self._cast_zharok_e(enemies);
            return
        if target_dist < 200 and self.w_timer == 0:
            self._cast_zharok_w();
            return
        if target_dist < 250 and self.q_timer == 0:
            self._cast_zharok_q();
            return

    def _cast_zharok_q(self):
        stats = self._get_boss_stats()
        self.q_timer = stats.get("skill_q_cooldown", 200)
        self.active_skill = 'q'
        self.active_skill_timer = 50
        if self.target and self.target.alive:
            self.target.take_damage(stats.get("skill_q_damage", 220), self.team)
        self._shake_screen(10)

    def _cast_zharok_w(self):
        stats = self._get_boss_stats()
        self.w_timer = stats.get("skill_w_cooldown", 300)
        self.active_skill = 'w'
        self.active_skill_timer = 40
        self._shake_screen(5)

    def _cast_zharok_e(self, enemies):
        stats = self._get_boss_stats()
        self.e_timer = stats.get("skill_e_cooldown", 280)
        self.active_skill = 'e'
        self.active_skill_timer = 60
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 150:
                e.take_damage(stats.get("skill_e_damage", 280), self.team)
        self._shake_screen(15)

    def _cast_zharok_r(self, enemies):
        stats = self._get_boss_stats()
        self.r_timer = stats.get("skill_r_cooldown", 600)
        self.active_skill = 'r'
        self.active_skill_timer = 80
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 220:
                e.take_damage(stats.get("skill_r_damage", 400), self.team)
        self._shake_screen(20)

    # ===== PYRENTH AI (Demon Lord) =====
    def _smart_ai_pyrenth(self, enemies, target_dist):
        if not hasattr(self, 'q_timer'):
            self.q_timer = 0
            self.w_timer = 0
            self.e_timer = 0
            self.r_timer = 0
            self.active_skill = None
            self.active_skill_timer = 0
        if self.q_timer > 0: self.q_timer -= 1
        if self.w_timer > 0: self.w_timer -= 1
        if self.e_timer > 0: self.e_timer -= 1
        if self.r_timer > 0: self.r_timer -= 1
        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0:
                self.active_skill = None

        hp_ratio = self.hp / self.max_hp
        nearby = sum(1 for e in enemies if math.hypot(e.x - self.x, e.y - self.y) <= 180)

        if hp_ratio < 0.4 and self.r_timer == 0:
            self._cast_pyrenth_r(enemies);
            return
        if nearby >= 3 and self.e_timer == 0:
            self._cast_pyrenth_e(enemies);
            return
        if self.w_timer == 0 and hp_ratio < 0.6:
            self._cast_pyrenth_w();
            return
        if target_dist < 200 and self.q_timer == 0:
            self._cast_pyrenth_q();
            return

    def _cast_pyrenth_q(self):
        stats = self._get_boss_stats()
        self.q_timer = stats.get("skill_q_cooldown", 240)
        self.active_skill = 'q'
        self.active_skill_timer = 50
        if self.target and self.target.alive:
            self.target.take_damage(stats.get("skill_q_damage", 320), self.team)
        self._shake_screen(12)

    def _cast_pyrenth_w(self):
        stats = self._get_boss_stats()
        self.w_timer = stats.get("skill_w_cooldown", 360)
        self.active_skill = 'w'
        self.active_skill_timer = 40
        heal = int(self.max_hp * 0.08)
        self.hp = min(self.max_hp, self.hp + heal)
        self._shake_screen(10)

    def _cast_pyrenth_e(self, enemies):
        stats = self._get_boss_stats()
        self.e_timer = stats.get("skill_e_cooldown", 300)
        self.active_skill = 'e'
        self.active_skill_timer = 60
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 180:
                e.take_damage(stats.get("skill_e_damage", 380), self.team)
        self._shake_screen(18)

    def _cast_pyrenth_r(self, enemies):
        stats = self._get_boss_stats()
        self.r_timer = stats.get("skill_r_cooldown", 600)
        self.active_skill = 'r'
        self.active_skill_timer = 70
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 220:
                e.take_damage(stats.get("skill_r_damage", 550), self.team)
        self._shake_screen(25)

    # ===== VOKRAHN AI (Chaos Knight) =====
    def _smart_ai_vokrahn(self, enemies, target_dist):
        if not hasattr(self, 'q_timer'):
            self.q_timer = 0
            self.w_timer = 0
            self.e_timer = 0
            self.r_timer = 0
            self.active_skill = None
            self.active_skill_timer = 0
        if self.q_timer > 0: self.q_timer -= 1
        if self.w_timer > 0: self.w_timer -= 1
        if self.e_timer > 0: self.e_timer -= 1
        if self.r_timer > 0: self.r_timer -= 1
        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0:
                self.active_skill = None

        hp_ratio = self.hp / self.max_hp
        nearby = sum(1 for e in enemies if math.hypot(e.x - self.x, e.y - self.y) <= 200)

        if hp_ratio < 0.5 and self.r_timer == 0:
            self._cast_vokrahn_r(enemies);
            return
        if nearby >= 3 and self.w_timer == 0:
            self._cast_vokrahn_w(enemies);
            return
        if target_dist < 200 and self.e_timer == 0:
            self._cast_vokrahn_e();
            return
        if self.q_timer == 0:
            self._cast_vokrahn_q();
            return

    def _cast_vokrahn_q(self):
        stats = self._get_boss_stats()
        self.q_timer = stats.get("skill_q_cooldown", 220)
        self.active_skill = 'q'
        self.active_skill_timer = 50
        if self.target and self.target.alive:
            self.target.take_damage(stats.get("skill_q_damage", 350), self.team)
        self._shake_screen(12)

    def _cast_vokrahn_w(self, enemies):
        stats = self._get_boss_stats()
        self.w_timer = stats.get("skill_w_cooldown", 300)
        self.active_skill = 'w'
        self.active_skill_timer = 60
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 220:
                e.take_damage(stats.get("skill_w_damage", 250), self.team)
        self._shake_screen(18)

    def _cast_vokrahn_e(self):
        stats = self._get_boss_stats()
        self.e_timer = stats.get("skill_e_cooldown", 280)
        self.active_skill = 'e'
        self.active_skill_timer = 50
        if self.target and self.target.alive:
            self.target.take_damage(stats.get("skill_e_damage", 400), self.team)
        self._shake_screen(15)

    def _cast_vokrahn_r(self, enemies):
        stats = self._get_boss_stats()
        self.r_timer = stats.get("skill_r_cooldown", 600)
        self.active_skill = 'r'
        self.active_skill_timer = 80
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 220:
                e.take_damage(150, self.team)  # Phantasm illusions damage
        self._shake_screen(20)

    def _smart_ai_nyxara(self, enemies, target_dist):
        if not hasattr(self, "q_timer"):
            self.q_timer = 0
            self.w_timer = 0
            self.e_timer = 0
            self.r_timer = 0

            self.active_skill = None
            self.active_skill_timer = 0

        for attr in ("q_timer", "w_timer", "e_timer", "r_timer"):
            if getattr(self, attr) > 0:
                setattr(
                    self,
                    attr,
                    getattr(self, attr) - 1
                )

        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1

            if self.active_skill_timer <= 0:
                self.active_skill = None

        stats = self._get_boss_stats()

        nearby = sum(
            1
            for e in enemies
            if math.hypot(
                e.x - self.x,
                e.y - self.y
            ) <= 220
        )

        # R - Life Drain
        if (
                self.target
                and self.hp / self.max_hp < 0.55
                and self.r_timer == 0
        ):
            self.r_timer = stats.get(
                "skill_r_cooldown",
                560
            )

            self.active_skill = "r"
            self.active_skill_timer = 90

            damage = stats.get(
                "skill_r_damage",
                320
            )

            self.target.take_damage(
                damage,
                self.team
            )

            self.hp = min(
                self.max_hp,
                self.hp + int(self.max_hp * 0.135)
            )

            return

        # E - Nether Ward
        if nearby >= 3 and self.e_timer == 0:
            self.e_timer = stats.get(
                "skill_e_cooldown",
                280
            )

            self.active_skill = "e"
            self.active_skill_timer = 80

            for enemy in enemies:
                distance = math.hypot(
                    enemy.x - self.x,
                    enemy.y - self.y
                )

                if distance <= 100:
                    enemy.take_damage(
                        stats.get(
                            "skill_e_damage",
                            160
                        ),
                        self.team
                    )

            return

        # W - Decrepify
        if (
                self.target
                and target_dist <= 280
                and self.w_timer == 0
        ):
            self.w_timer = stats.get(
                "skill_w_cooldown",
                300
            )

            self.active_skill = "w"
            self.active_skill_timer = 70

            self.target.take_damage(
                stats.get(
                    "skill_w_damage",
                    140
                ),
                self.team
            )

            if hasattr(self.target, "attack_timer"):
                self.target.attack_timer = max(
                    self.target.attack_timer,
                    75
                )

            return

        # Q - Nether Blast
        if self.target and self.q_timer == 0:
            self.q_timer = stats.get(
                "skill_q_cooldown",
                220
            )

            self.active_skill = "q"
            self.active_skill_timer = 60

            self.target.take_damage(
                stats.get(
                    "skill_q_damage",
                    220
                ),
                self.team
            )

    def _smart_ai_gravefang(self, enemies, target_dist):
        if not hasattr(self, "q_timer"):
            self.q_timer = 0
            self.w_timer = 0
            self.e_timer = 0
            self.r_timer = 0
            self.active_skill = None
            self.active_skill_timer = 0

        for attr in ("q_timer", "w_timer", "e_timer", "r_timer"):
            if getattr(self, attr) > 0:
                setattr(self, attr, getattr(self, attr) - 1)

        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0:
                self.active_skill = None

        stats = self._get_boss_stats()
        nearby = sum(
            1 for e in enemies
            if math.hypot(e.x - self.x, e.y - self.y) <= 180
        )

        # R - Magnetize saat banyak target atau HP rendah
        if (nearby >= 3 or self.hp / self.max_hp < 0.35) and self.r_timer == 0:
            self.r_timer = stats.get("skill_r_cooldown", 620)
            self.active_skill = "r"
            self.active_skill_timer = 100
            for e in enemies:
                if math.hypot(e.x - self.x, e.y - self.y) <= 180:
                    e.take_damage(stats.get("skill_r_damage", 380), self.team)
            return

        # W - Rolling Boulder
        if self.target and target_dist > 90 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 300)
            self.active_skill = "w"
            self.active_skill_timer = 70
            self.target.take_damage(stats.get("skill_w_damage", 240), self.team)
            return

        # E - Geomagnetic Grip
        if self.target and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 280)
            self.active_skill = "e"
            self.active_skill_timer = 70
            self.target.take_damage(stats.get("skill_e_damage", 190), self.team)
            if hasattr(self.target, "attack_timer"):
                self.target.attack_timer = max(self.target.attack_timer, 60)
            return

        # Q - Boulder Smash
        if nearby >= 2 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 240)
            self.active_skill = "q"
            self.active_skill_timer = 60
            for e in enemies:
                if math.hypot(e.x - self.x, e.y - self.y) <= 120:
                    e.take_damage(stats.get("skill_q_damage", 260), self.team)

    def _smart_ai_vhalzun(self, enemies, target_dist):
        if not hasattr(self, "q_timer"):
            self.q_timer = 0
            self.w_timer = 0
            self.e_timer = 0
            self.r_timer = 0
            self.active_skill = None
            self.active_skill_timer = 0

        for attr in ("q_timer", "w_timer", "e_timer", "r_timer"):
            if getattr(self, attr) > 0:
                setattr(self, attr, getattr(self, attr) - 1)

        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0:
                self.active_skill = None

        stats = self._get_boss_stats()
        nearby = sum(
            1 for e in enemies
            if math.hypot(e.x - self.x, e.y - self.y) <= 220
        )

        # R - Ghost Shroud saat HP rendah
        if self.hp / self.max_hp < 0.40 and self.r_timer == 0:
            self.r_timer = stats.get("skill_r_cooldown", 620)
            self.active_skill = "r"
            self.active_skill_timer = 100
            self.hp = min(self.max_hp, self.hp + int(self.max_hp * 0.18))
            return

        # W - Heartstopper Aura saat banyak target
        if nearby >= 3 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 300)
            self.active_skill = "w"
            self.active_skill_timer = 80
            for e in enemies:
                if math.hypot(e.x - self.x, e.y - self.y) <= 150:
                    e.take_damage(stats.get("skill_w_damage", 170), self.team)
            return

        # E - Reaper's Scythe pada target jauh
        if self.target and target_dist > 150 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 320)
            self.active_skill = "e"
            self.active_skill_timer = 60
            self.target.take_damage(stats.get("skill_e_damage", 280), self.team)
            return

        # Q - Death Pulse
        if self.target and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 220)
            self.active_skill = "q"
            self.active_skill_timer = 60
            for e in enemies:
                if math.hypot(e.x - self.x, e.y - self.y) <= 130:
                    e.take_damage(stats.get("skill_q_damage", 230), self.team)

    # ═══════════════════════════════════════════════════
    # MALZARETH AI (Shadow Demon - ranged void magic)
    # ═══════════════════════════════════════════════════
    def _smart_ai_malzareth(self, enemies, target_dist):
        if not hasattr(self, 'q_timer'):
            self.q_timer = 0;
            self.w_timer = 0;
            self.e_timer = 0;
            self.r_timer = 0
            self.active_skill = None;
            self.active_skill_timer = 0
        for attr in ("q_timer", "w_timer", "e_timer", "r_timer"):
            if getattr(self, attr) > 0: setattr(self, attr, getattr(self, attr) - 1)
        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0: self.active_skill = None
        stats = self._get_boss_stats()
        nearby = sum(1 for e in enemies if math.hypot(e.x - self.x, e.y - self.y) <= 200)
        hp_ratio = self.hp / self.max_hp
        if hp_ratio < 0.4 and nearby >= 2 and self.r_timer == 0:
            self._malzareth_r(enemies);
            return
        if nearby >= 2 and self.w_timer == 0:
            self._malzareth_w(enemies);
            return
        if target_dist < 260 and self.e_timer == 0:
            self._malzareth_e(enemies);
            return
        if target_dist < 280 and self.q_timer == 0:
            self._malzareth_q(enemies);
            return

    def _malzareth_q(self, enemies):
        stats = self._get_boss_stats();
        self.q_timer = stats.get("skill_q_cooldown", 240)
        self.active_skill = 'q';
        self.active_skill_timer = 60;
        damage = stats.get("skill_q_damage", 300)
        if self.target and self.target.alive:
            tx, ty = self.target.x, self.target.y
            for e in enemies:
                if math.hypot(e.x - tx, e.y - ty) <= 100: e.take_damage(damage, self.team)
        self._shake_screen(14)

    def _malzareth_w(self, enemies):
        stats = self._get_boss_stats();
        self.w_timer = stats.get("skill_w_cooldown", 280)
        self.active_skill = 'w';
        self.active_skill_timer = 50;
        damage = stats.get("skill_w_damage", 280)
        if self.target and self.target.alive:
            self.target.take_damage(damage, self.team)
            for e in enemies:
                if e != self.target and math.hypot(e.x - self.target.x, e.y - self.target.y) <= 60:
                    e.take_damage(damage // 2, self.team)
        self._shake_screen(12)

    def _malzareth_e(self, enemies):
        stats = self._get_boss_stats();
        self.e_timer = stats.get("skill_e_cooldown", 260)
        self.active_skill = 'e';
        self.active_skill_timer = 45;
        damage = stats.get("skill_e_damage", 220)
        if self.target and self.target.alive:
            self.target.take_damage(damage, self.team)
            if hasattr(self.target, 'apply_slow'): self.target.apply_slow(0.5, 180)
        self._shake_screen(10)

    def _malzareth_r(self, enemies):
        stats = self._get_boss_stats();
        self.r_timer = stats.get("skill_r_cooldown", 600)
        self.active_skill = 'r';
        self.active_skill_timer = 90;
        damage = stats.get("skill_r_damage", 400)
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 200:
                e.take_damage(damage, self.team)
                if hasattr(e, 'attack_timer'): e.attack_timer = max(getattr(e, 'attack_timer', 0), 90)
        heal = int(self.max_hp * 0.12);
        self.hp = min(self.max_hp, self.hp + heal)
        self._shake_screen(22)
        try:
            import __main__
            if hasattr(__main__, 'game_instance'):
                __main__.game_instance.effects.add_damage_number(self.x, self.y - 30, f"+{heal}", is_critical=True,
                                                                 damage_type='heal')
        except:
            pass

    # ═══════════════════════════════════════════════════
    # AKASHARI AI (Queen of Pain - ranged pain magic)
    # ═══════════════════════════════════════════════════
    def _smart_ai_akashari(self, enemies, target_dist):
        if not hasattr(self, 'q_timer'):
            self.q_timer = 0;
            self.w_timer = 0;
            self.e_timer = 0;
            self.r_timer = 0
            self.active_skill = None;
            self.active_skill_timer = 0
        for attr in ("q_timer", "w_timer", "e_timer", "r_timer"):
            if getattr(self, attr) > 0: setattr(self, attr, getattr(self, attr) - 1)
        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0: self.active_skill = None
        nearby = sum(1 for e in enemies if math.hypot(e.x - self.x, e.y - self.y) <= 200)
        hp_ratio = self.hp / self.max_hp
        if hp_ratio < 0.4 and nearby >= 2 and self.r_timer == 0:
            self._akashari_r(enemies);
            return
        if nearby >= 3 and self.e_timer == 0:
            self._akashari_e(enemies);
            return
        if hp_ratio < 0.6 and self.w_timer == 0:
            self._akashari_w(enemies);
            return
        if target_dist < 280 and self.q_timer == 0:
            self._akashari_q(enemies);
            return

    def _akashari_q(self, enemies):
        stats = self._get_boss_stats();
        self.q_timer = stats.get("skill_q_cooldown", 220)
        self.active_skill = 'q';
        self.active_skill_timer = 50;
        damage = stats.get("skill_q_damage", 320)
        if self.target and self.target.alive:
            self.target.take_damage(damage, self.team)
            if hasattr(self.target, 'apply_slow'): self.target.apply_slow(0.4, 120)
        self._shake_screen(14)

    def _akashari_w(self, enemies):
        stats = self._get_boss_stats();
        self.w_timer = stats.get("skill_w_cooldown", 300)
        self.active_skill = 'w';
        self.active_skill_timer = 55;
        damage = stats.get("skill_w_damage", 250)
        if self.target and self.target.alive:
            dx = self.target.x - self.x;
            dy = self.target.y - self.y;
            dist = math.hypot(dx, dy)
            if dist > 0:
                self.x += (dx / dist) * min(dist, 150);
                self.y += (dy / dist) * min(dist, 150)
            for e in enemies:
                if math.hypot(e.x - self.x, e.y - self.y) <= 80: e.take_damage(damage, self.team)
        heal = int(self.max_hp * 0.08);
        self.hp = min(self.max_hp, self.hp + heal)
        self._shake_screen(12)

    def _akashari_e(self, enemies):
        stats = self._get_boss_stats();
        self.e_timer = stats.get("skill_e_cooldown", 260)
        self.active_skill = 'e';
        self.active_skill_timer = 60;
        damage = stats.get("skill_e_damage", 300)
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 150: e.take_damage(damage, self.team)
        self._shake_screen(16)

    def _akashari_r(self, enemies):
        stats = self._get_boss_stats();
        self.r_timer = stats.get("skill_r_cooldown", 600)
        self.active_skill = 'r';
        self.active_skill_timer = 90;
        damage = stats.get("skill_r_damage", 450)
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 220:
                e.take_damage(damage, self.team)
                if hasattr(e, 'apply_slow'): e.apply_slow(0.5, 240)
        heal = int(self.max_hp * 0.10);
        self.hp = min(self.max_hp, self.hp + heal)
        self._shake_screen(25)
        try:
            import __main__
            if hasattr(__main__, 'game_instance'):
                __main__.game_instance.effects.add_damage_number(self.x, self.y - 30, f"+{heal}", is_critical=True,
                                                                 damage_type='heal')
        except:
            pass

    # ═══════════════════════════════════════════════════
    # VORENMARR AI (Warlock - ranged hellfire + summon)
    # ═══════════════════════════════════════════════════
    def _smart_ai_vorenmarr(self, enemies, target_dist):
        if not hasattr(self, 'q_timer'):
            self.q_timer = 0;
            self.w_timer = 0;
            self.e_timer = 0;
            self.r_timer = 0
            self.active_skill = None;
            self.active_skill_timer = 0
        for attr in ("q_timer", "w_timer", "e_timer", "r_timer"):
            if getattr(self, attr) > 0: setattr(self, attr, getattr(self, attr) - 1)
        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0: self.active_skill = None
        nearby = sum(1 for e in enemies if math.hypot(e.x - self.x, e.y - self.y) <= 200)
        hp_ratio = self.hp / self.max_hp
        if hp_ratio < 0.4 and nearby >= 2 and self.r_timer == 0:
            self._vorenmarr_r(enemies);
            return
        if hp_ratio < 0.6 and self.w_timer == 0:
            self._vorenmarr_w();
            return
        if nearby >= 2 and self.e_timer == 0:
            self._vorenmarr_e(enemies);
            return
        if target_dist < 280 and self.q_timer == 0:
            self._vorenmarr_q(enemies);
            return

    def _vorenmarr_q(self, enemies):
        stats = self._get_boss_stats();
        self.q_timer = stats.get("skill_q_cooldown", 240)
        self.active_skill = 'q';
        self.active_skill_timer = 70;
        damage = stats.get("skill_q_damage", 260)
        if self.target and self.target.alive:
            self.target.take_damage(damage, self.team)
            for e in enemies:
                if e != self.target and math.hypot(e.x - self.target.x, e.y - self.target.y) <= 80:
                    e.take_damage(damage // 2, self.team)
        self._shake_screen(12)

    def _vorenmarr_w(self):
        stats = self._get_boss_stats();
        self.w_timer = stats.get("skill_w_cooldown", 300)
        self.active_skill = 'w';
        self.active_skill_timer = 70
        heal = int(self.max_hp * 0.14);
        self.hp = min(self.max_hp, self.hp + heal)
        self._shake_screen(8)
        try:
            import __main__
            if hasattr(__main__, 'game_instance'):
                __main__.game_instance.effects.add_damage_number(self.x, self.y - 30, f"+{heal}", is_critical=True,
                                                                 damage_type='heal')
        except:
            pass

    def _vorenmarr_e(self, enemies):
        stats = self._get_boss_stats();
        self.e_timer = stats.get("skill_e_cooldown", 280)
        self.active_skill = 'e';
        self.active_skill_timer = 80;
        damage = stats.get("skill_e_damage", 350)
        if self.target and self.target.alive:
            tx, ty = self.target.x, self.target.y
            for e in enemies:
                if math.hypot(e.x - tx, e.y - ty) <= 120:
                    e.take_damage(damage, self.team)
                    if hasattr(e, 'attack_timer'): e.attack_timer = max(getattr(e, 'attack_timer', 0), 60)
        self._shake_screen(18)

    def _vorenmarr_r(self, enemies):
        stats = self._get_boss_stats();
        self.r_timer = stats.get("skill_r_cooldown", 600)
        self.active_skill = 'r';
        self.active_skill_timer = 100;
        damage = stats.get("skill_r_damage", 420)
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 200:
                e.take_damage(damage, self.team)
                if hasattr(e, 'attack_timer'): e.attack_timer = max(e.attack_timer, 90)
        heal = int(self.max_hp * 0.12);
        self.hp = min(self.max_hp, self.hp + heal)
        self._shake_screen(25)
        try:
            import __main__
            if hasattr(__main__, 'game_instance'):
                __main__.game_instance.effects.add_damage_number(self.x, self.y - 30, f"+{heal}", is_critical=True,
                                                                 damage_type='heal')
        except:
            pass

    # ═══════════════════════════════════════════════════
    # NYXARATH AI (Shadow Fiend - ranged hellfire + soul devour)
    # ═══════════════════════════════════════════════════

    def _smart_ai_nyxarath(self, enemies, target_dist):
        """Smart AI Nyxarath: shadow fiend with hellfire + soul magic."""
        if not hasattr(self, 'q_timer'):
            self.q_timer = 0
            self.w_timer = 0
            self.e_timer = 0
            self.r_timer = 0
            self.active_skill = None
            self.active_skill_timer = 0
            self.necro_buff_active = False
            self.necro_buff_timer = 0
            self.presence_active = False
            self.presence_timer = 0
        if self.q_timer > 0: self.q_timer -= 1
        if self.w_timer > 0: self.w_timer -= 1
        if self.e_timer > 0: self.e_timer -= 1
        if self.r_timer > 0: self.r_timer -= 1
        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0:
                self.active_skill = None

        # Necromastery buff timer (+40% damage from collected souls)
        if self.necro_buff_active:
            self.necro_buff_timer -= 1
            if self.necro_buff_timer <= 0:
                self.necro_buff_active = False
                stats = self._get_boss_stats()
                self.damage = stats.get("damage", 130)

        # Presence of the Dark Lord aura timer
        if self.presence_active:
            self.presence_timer -= 1
            if self.presence_timer <= 0:
                self.presence_active = False

        nearby = sum(
            1 for e in enemies
            if math.hypot(e.x - self.x, e.y - self.y) <= 200
        )
        hp_ratio = self.hp / self.max_hp

        # PRIORITY 1: HP kritis + banyak enemy -> R (Requiem of Souls)
        if hp_ratio < 0.4 and nearby >= 2 and self.r_timer == 0:
            self._nyxarath_r(enemies);
            return
        # PRIORITY 2: HP menurun -> E (Presence of the Dark Lord + heal)
        if hp_ratio < 0.6 and not self.presence_active \
                and self.e_timer == 0:
            self._nyxarath_e(enemies);
            return
        # PRIORITY 3: Banyak enemy -> W (Necromastery skulls + buff)
        if nearby >= 2 and self.w_timer == 0:
            self._nyxarath_w(enemies);
            return
        # PRIORITY 4: Target dalam range -> Q (Shadowraze beam)
        if target_dist < 280 and self.q_timer == 0:
            self._nyxarath_q(enemies);
            return

    def _nyxarath_q(self, enemies):
        """Q - Shadowraze: bright red beam forward, line AOE.
        Auto-target enemy TERDEKAT (tidak butuh self.target)."""
        stats = self._get_boss_stats()
        self.q_timer = stats.get("skill_q_cooldown", 240)
        self.active_skill = 'q'
        self.active_skill_timer = 40
        damage = stats.get("skill_q_damage", 380)

        # Cari enemy TERDEKAT dari list
        closest = None
        closest_dist = 9999
        for e in enemies:
            d = math.hypot(e.x - self.x, e.y - self.y)
            if d < closest_dist:
                closest_dist = d
                closest = e

        if not closest or closest_dist > 300:
            self._shake_screen(12)
            return

        # Aim beam ke enemy terdekat
        dx = closest.x - self.x
        dy = closest.y - self.y
        dist = math.hypot(dx, dy)
        if dist == 0:
            self._shake_screen(12)
            return
        dx /= dist
        dy /= dist

        # Long line AOE forward (beam)
        max_range = 280
        line_width = 50
        for e in enemies:
            ex = e.x - self.x
            ey = e.y - self.y
            proj = ex * dx + ey * dy
            if 0 < proj < max_range:
                perp = abs(ex * (-dy) + ey * dx)
                if perp < line_width:
                    e.take_damage(damage, self.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(
                            getattr(e, 'attack_timer', 0), 45)

        self._shake_screen(18)

    def _nyxarath_w(self, enemies):
        """W - Necromastery: skulls AOE + damage buff + heal."""
        stats = self._get_boss_stats()
        self.w_timer = stats.get("skill_w_cooldown", 300)
        self.active_skill = 'w'
        self.active_skill_timer = 70
        damage = stats.get("skill_w_damage", 350)

        # AOE damage around boss (souls explode)
        kills_count = 0
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 180:
                e.take_damage(damage, self.team)
                if not e.alive:
                    kills_count += 1

        # Necromastery buff: +40% damage for 8 seconds
        self.necro_buff_active = True
        self.necro_buff_timer = 480
        base_damage = stats.get("damage", 130)
        self.damage = int(base_damage * 1.4)

        # Heal from collected souls (DINNERF: 12% -> 6%)
        heal = int(self.max_hp * 0.06) + kills_count * 30
        self.hp = min(self.max_hp, self.hp + heal)

        self._shake_screen(16)

        try:
            import __main__
            if hasattr(__main__, 'game_instance'):
                game = __main__.game_instance
                game.effects.add_damage_number(
                    self.x, self.y - 30,
                    f"+{heal}", is_critical=True,
                    damage_type='heal')
        except Exception:
            pass

    def _nyxarath_e(self, enemies):
        """E - Presence of the Dark Lord: aura debuff + heal."""
        stats = self._get_boss_stats()
        self.e_timer = stats.get("skill_e_cooldown", 420)
        self.active_skill = 'e'
        self.active_skill_timer = 80
        self.presence_active = True
        self.presence_timer = 360  # 6 seconds aura

        # Debuff all nearby enemies (reduce their combat effectiveness)
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 200:
                if hasattr(e, 'attack_timer'):
                    e.attack_timer = max(
                        getattr(e, 'attack_timer', 0), 90)
                if hasattr(e, 'apply_slow'):
                    e.apply_slow(0.5, 240)

        # Heal 18% (souls of the dark lord sustain him)
        # DINNERF: 18% -> 10%
        heal = int(self.max_hp * 0.10)
        self.hp = min(self.max_hp, self.hp + heal)

        self._shake_screen(14)

        try:
            import __main__
            if hasattr(__main__, 'game_instance'):
                game = __main__.game_instance
                game.effects.add_damage_number(
                    self.x, self.y - 30,
                    f"+{heal}", is_critical=True,
                    damage_type='heal')
        except Exception:
            pass

    def _nyxarath_r(self, enemies):
        """R - Requiem of Souls: massive AOE pillars ultimate."""
        stats = self._get_boss_stats()
        self.r_timer = stats.get("skill_r_cooldown", 780)
        self.active_skill = 'r'
        self.active_skill_timer = 110
        damage = stats.get("skill_r_damage", 700)

        # Massive AOE around boss (soul pillars erupt)
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 220:
                e.take_damage(damage, self.team)
                if hasattr(e, 'attack_timer'):
                    e.attack_timer = max(e.attack_timer, 120)
                if hasattr(e, 'apply_slow'):
                    e.apply_slow(0.6, 240)
                # Knockback: HANYA untuk unit yang bisa bergerak.
                # Tower & Castle adalah bangunan statis - kalau
                # posisinya digeser, mereka pindah permanen dari
                # petak-nya. Unit punya .speed, bangunan tidak.
                dist = math.hypot(e.x - self.x, e.y - self.y)
                if dist > 0 and hasattr(e, 'speed'):
                    push_x = (e.x - self.x) / dist * 20
                    push_y = (e.y - self.y) / dist * 20
                    e.x += push_x
                    e.y += push_y

        self._shake_screen(30)

        # Heal 22% (devour souls from requiem)
        # DINNERF: 22% -> 13%
        heal = int(self.max_hp * 0.13)
        self.hp = min(self.max_hp, self.hp + heal)

        try:
            import __main__
            if hasattr(__main__, 'game_instance'):
                game = __main__.game_instance
                game.effects.add_damage_number(
                    self.x, self.y - 30,
                    f"+{heal}", is_critical=True,
                    damage_type='heal')
        except Exception:
            pass

    # ═══════════════════════════════════════════════════
    # THALGRYN AI (Morphling - ranged water elemental)
    # ═══════════════════════════════════════════════════

    def _smart_ai_thalgryn(self, enemies, target_dist):
        """Smart AI Thalgryn: water elemental with adaptive strikes."""
        if not hasattr(self, 'q_timer'):
            self.q_timer = 0
            self.w_timer = 0
            self.e_timer = 0
            self.r_timer = 0
            self.active_skill = None
            self.active_skill_timer = 0
            self.morph_buff_active = False
            self.morph_buff_timer = 0
        if self.q_timer > 0: self.q_timer -= 1
        if self.w_timer > 0: self.w_timer -= 1
        if self.e_timer > 0: self.e_timer -= 1
        if self.r_timer > 0: self.r_timer -= 1
        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0:
                self.active_skill = None

        # Morph buff timer (+35% damage from attribute shift)
        if self.morph_buff_active:
            self.morph_buff_timer -= 1
            if self.morph_buff_timer <= 0:
                self.morph_buff_active = False
                stats = self._get_boss_stats()
                self.damage = stats.get("damage", 92)

        nearby = sum(
            1 for e in enemies
            if math.hypot(e.x - self.x, e.y - self.y) <= 200
        )
        hp_ratio = self.hp / self.max_hp

        # PRIORITY 1: HP kritis + banyak enemy -> R (Replicate)
        if hp_ratio < 0.4 and nearby >= 2 and self.r_timer == 0:
            self._thalgryn_r(enemies);
            return
        # PRIORITY 2: HP menurun -> E (Morph buff + heal)
        if hp_ratio < 0.55 and not self.morph_buff_active \
                and self.e_timer == 0:
            self._thalgryn_e();
            return
        # PRIORITY 3: Target jauh -> Q (Waveform surge/teleport)
        if target_dist > 150 and self.q_timer == 0:
            self._thalgryn_q(enemies);
            return
        # PRIORITY 4: Target dalam range -> W (Adaptive Strike)
        if target_dist < 280 and self.w_timer == 0:
            self._thalgryn_w(enemies);
            return

    def _thalgryn_q(self, enemies):
        """Q - Waveform: surge forward, damage enemies in path + teleport."""
        stats = self._get_boss_stats()
        self.q_timer = stats.get("skill_q_cooldown", 300)
        self.active_skill = 'q'
        self.active_skill_timer = 60
        damage = stats.get("skill_q_damage", 320)

        if not self.target or not self.target.alive:
            self._shake_screen(12);
            return

        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.hypot(dx, dy)
        if dist == 0:
            self._shake_screen(12);
            return
        dx /= dist;
        dy /= dist

        # Damage enemies in path (line AOE)
        max_range = 250
        line_width = 50
        for e in enemies:
            ex = e.x - self.x
            ey = e.y - self.y
            proj = ex * dx + ey * dy
            if 0 < proj < max_range:
                perp = abs(ex * (-dy) + ey * dx)
                if perp < line_width:
                    e.take_damage(damage, self.team)

        # Teleport forward (surge)
        surge_dist = min(dist, 200)
        self.x += dx * surge_dist
        self.y += dy * surge_dist

        self._shake_screen(18)

    def _thalgryn_w(self, enemies):
        """W - Adaptive Strike: big ranged water spear, single target heavy."""
        stats = self._get_boss_stats()
        self.w_timer = stats.get("skill_w_cooldown", 260)
        self.active_skill = 'w'
        self.active_skill_timer = 50
        damage = stats.get("skill_w_damage", 400)

        if self.target and self.target.alive:
            # Heavy single target damage
            self.target.take_damage(damage, self.team)
            if hasattr(self.target, 'attack_timer'):
                self.target.attack_timer = max(
                    getattr(self.target, 'attack_timer', 0), 60)
            # Small splash around target
            for e in enemies:
                if e != self.target and math.hypot(
                        e.x - self.target.x, e.y - self.target.y) <= 60:
                    e.take_damage(damage // 3, self.team)

        self._shake_screen(15)

    def _thalgryn_e(self):
        """E - Morph: attribute shift, damage buff + heal."""
        stats = self._get_boss_stats()
        self.e_timer = stats.get("skill_e_cooldown", 360)
        self.active_skill = 'e'
        self.active_skill_timer = 60
        self.morph_buff_active = True
        self.morph_buff_timer = 300  # 5 seconds buff

        # +35% damage from attribute shift
        base_damage = stats.get("damage", 92)
        self.damage = int(base_damage * 1.35)

        # Heal 14% (water regeneration)
        heal = int(self.max_hp * 0.14)
        self.hp = min(self.max_hp, self.hp + heal)

        self._shake_screen(10)

        try:
            import __main__
            if hasattr(__main__, 'game_instance'):
                game = __main__.game_instance
                game.effects.add_damage_number(
                    self.x, self.y - 30,
                    f"+{heal}", is_critical=True,
                    damage_type='heal')
        except Exception:
            pass

    def _thalgryn_r(self, enemies):
        """R - Replicate: water clones, AOE damage + buff."""
        stats = self._get_boss_stats()
        self.r_timer = stats.get("skill_r_cooldown", 600)
        self.active_skill = 'r'
        self.active_skill_timer = 80
        damage = stats.get("skill_r_damage", 380)

        # AOE damage around boss (clones attack)
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 200:
                e.take_damage(damage, self.team)
                if hasattr(e, 'apply_slow'):
                    e.apply_slow(0.4, 180)

        self._shake_screen(22)

        # Heal 10% (water clone vitality)
        heal = int(self.max_hp * 0.10)
        self.hp = min(self.max_hp, self.hp + heal)

        try:
            import __main__
            if hasattr(__main__, 'game_instance'):
                game = __main__.game_instance
                game.effects.add_damage_number(
                    self.x, self.y - 30,
                    f"+{heal}", is_critical=True,
                    damage_type='heal')
        except Exception:
            pass

    # ═══════════════════════════════════════════════════
    # SYRENTHA AI (Naga Siren - hybrid ranged/caster siren)
    # ═══════════════════════════════════════════════════

    def _smart_ai_syrentha(self, enemies, target_dist):
        """Smart AI Syrentha: siren with spear + enchanting song magic."""
        if not hasattr(self, 'q_timer'):
            self.q_timer = 0
            self.w_timer = 0
            self.e_timer = 0
            self.r_timer = 0
            self.active_skill = None
            self.active_skill_timer = 0
            self.mirror_buff_active = False
            self.mirror_buff_timer = 0
        if self.q_timer > 0: self.q_timer -= 1
        if self.w_timer > 0: self.w_timer -= 1
        if self.e_timer > 0: self.e_timer -= 1
        if self.r_timer > 0: self.r_timer -= 1
        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0:
                self.active_skill = None

        # Mirror Image buff timer (+40% damage from illusions)
        if self.mirror_buff_active:
            self.mirror_buff_timer -= 1
            if self.mirror_buff_timer <= 0:
                self.mirror_buff_active = False
                stats = self._get_boss_stats()
                self.damage = stats.get("damage", 98)

        nearby = sum(
            1 for e in enemies
            if math.hypot(e.x - self.x, e.y - self.y) <= 200
        )
        hp_ratio = self.hp / self.max_hp

        # PRIORITY 1: HP kritis + banyak enemy -> R (Song of the Siren)
        if hp_ratio < 0.45 and nearby >= 2 and self.r_timer == 0:
            self._syrentha_r(enemies);
            return
        # PRIORITY 2: HP menurun -> E (Mirror Image buff)
        if hp_ratio < 0.6 and not self.mirror_buff_active \
                and self.e_timer == 0:
            self._syrentha_e();
            return
        # PRIORITY 3: Banyak enemy dekat -> W (Enchanting Song stun)
        if nearby >= 3 and self.w_timer == 0:
            self._syrentha_w(enemies);
            return
        # PRIORITY 4: Target dalam range -> Q (Riptide wave)
        if target_dist < 260 and self.q_timer == 0:
            self._syrentha_q(enemies);
            return

    def _syrentha_q(self, enemies):
        """Q - Riptide: wave AOE forward + slow."""
        stats = self._get_boss_stats()
        self.q_timer = stats.get("skill_q_cooldown", 240)
        self.active_skill = 'q'
        self.active_skill_timer = 45
        damage = stats.get("skill_q_damage", 250)

        if not self.target or not self.target.alive:
            self._shake_screen(10);
            return

        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.hypot(dx, dy)
        if dist == 0:
            self._shake_screen(10);
            return
        dx /= dist;
        dy /= dist

        # Wave AOE forward
        max_range = 250
        line_width = 70
        for e in enemies:
            ex = e.x - self.x
            ey = e.y - self.y
            proj = ex * dx + ey * dy
            if 0 < proj < max_range:
                perp = abs(ex * (-dy) + ey * dx)
                if perp < line_width:
                    e.take_damage(damage, self.team)
                    if hasattr(e, 'apply_slow'):
                        e.apply_slow(0.5, 180)
        self._shake_screen(12)

    def _syrentha_w(self, enemies):
        """W - Enchanting Song: AOE stun/sleep around boss."""
        stats = self._get_boss_stats()
        self.w_timer = stats.get("skill_w_cooldown", 300)
        self.active_skill = 'w'
        self.active_skill_timer = 80
        damage = stats.get("skill_w_damage", 180)

        # AOE around boss
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 150:
                e.take_damage(damage, self.team)
                # Stun (sleep) effect
                if hasattr(e, 'attack_timer'):
                    e.attack_timer = max(
                        getattr(e, 'attack_timer', 0), 120)
                if hasattr(e, 'apply_slow'):
                    e.apply_slow(0.7, 240)
        self._shake_screen(14)

    def _syrentha_e(self):
        """E - Mirror Image: summon illusions + damage buff + heal."""
        stats = self._get_boss_stats()
        self.e_timer = stats.get("skill_e_cooldown", 420)
        self.active_skill = 'e'
        self.active_skill_timer = 70
        self.mirror_buff_active = True
        self.mirror_buff_timer = 360  # 6 seconds buff

        # +40% damage from illusion strikes
        base_damage = stats.get("damage", 98)
        self.damage = int(base_damage * 1.4)

        # Heal 12% (siren vitality)
        heal = int(self.max_hp * 0.12)
        self.hp = min(self.max_hp, self.hp + heal)

        self._shake_screen(10)

        try:
            import __main__
            if hasattr(__main__, 'game_instance'):
                game = __main__.game_instance
                game.effects.add_damage_number(
                    self.x, self.y - 30,
                    f"+{heal}", is_critical=True,
                    damage_type='heal')
        except Exception:
            pass

    def _syrentha_r(self, enemies):
        """R - Song of the Siren: massive spiral AOE stun around boss."""
        stats = self._get_boss_stats()
        self.r_timer = stats.get("skill_r_cooldown", 600)
        self.active_skill = 'r'
        self.active_skill_timer = 90
        damage = stats.get("skill_r_damage", 420)

        # Massive AOE around boss
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 220:
                e.take_damage(damage, self.team)
                # Long stun
                if hasattr(e, 'attack_timer'):
                    e.attack_timer = max(e.attack_timer, 150)
                if hasattr(e, 'apply_slow'):
                    e.apply_slow(0.8, 300)

        self._shake_screen(22)

        # Heal 10% (siren's song restores her)
        heal = int(self.max_hp * 0.10)
        self.hp = min(self.max_hp, self.hp + heal)

        try:
            import __main__
            if hasattr(__main__, 'game_instance'):
                game = __main__.game_instance
                game.effects.add_damage_number(
                    self.x, self.y - 30,
                    f"+{heal}", is_critical=True,
                    damage_type='heal')
        except Exception:
            pass

    # ═══════════════════════════════════════════════════
    # GRAVEWAKE AI (Tidehunter - melee kraken + tide magic)
    # ═══════════════════════════════════════════════════

    def _smart_ai_gravewake(self, enemies, target_dist):
        """Smart AI Gravewake: kraken melee with anchor + tide magic."""
        if not hasattr(self, 'q_timer'):
            self.q_timer = 0
            self.w_timer = 0
            self.e_timer = 0
            self.r_timer = 0
            self.active_skill = None
            self.active_skill_timer = 0
            self.shell_active = False
            self.shell_timer = 0
        if self.q_timer > 0: self.q_timer -= 1
        if self.w_timer > 0: self.w_timer -= 1
        if self.e_timer > 0: self.e_timer -= 1
        if self.r_timer > 0: self.r_timer -= 1
        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0:
                self.active_skill = None

        # Kraken Shell buff timer
        if self.shell_active:
            self.shell_timer -= 1
            if self.shell_timer <= 0:
                self.shell_active = False

        nearby = sum(
            1 for e in enemies
            if math.hypot(e.x - self.x, e.y - self.y) <= 180
        )
        hp_ratio = self.hp / self.max_hp

        # PRIORITY 1: HP kritis + banyak enemy -> R (Ravage)
        if hp_ratio < 0.4 and nearby >= 2 and self.r_timer == 0:
            self._gravewake_r(enemies);
            return
        # PRIORITY 2: HP menurun -> E (Kraken Shell defensive)
        if hp_ratio < 0.6 and not self.shell_active and self.e_timer == 0:
            self._gravewake_e();
            return
        # PRIORITY 3: Banyak enemy -> W (Tidebringer AOE totems)
        if nearby >= 2 and self.w_timer == 0:
            self._gravewake_w(enemies);
            return
        # PRIORITY 4: Target dalam range -> Q (Anchor Smash line)
        if target_dist < 220 and self.q_timer == 0:
            self._gravewake_q(enemies);
            return

    def _gravewake_q(self, enemies):
        """Q - Anchor Smash: line AOE in front + slow."""
        stats = self._get_boss_stats()
        self.q_timer = stats.get("skill_q_cooldown", 240)
        self.active_skill = 'q'
        self.active_skill_timer = 45
        damage = stats.get("skill_q_damage", 280)

        if not self.target or not self.target.alive:
            self._shake_screen(12);
            return

        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.hypot(dx, dy)
        if dist == 0:
            self._shake_screen(12);
            return
        dx /= dist;
        dy /= dist

        # Line AOE forward
        max_range = 200
        line_width = 60
        for e in enemies:
            ex = e.x - self.x
            ey = e.y - self.y
            proj = ex * dx + ey * dy
            if 0 < proj < max_range:
                perp = abs(ex * (-dy) + ey * dx)
                if perp < line_width:
                    e.take_damage(damage, self.team)
                    if hasattr(e, 'apply_slow'):
                        e.apply_slow(0.5, 180)
        self._shake_screen(15)

    def _gravewake_w(self, enemies):
        """W - Tidebringer: AOE around target with anchor totems."""
        stats = self._get_boss_stats()
        self.w_timer = stats.get("skill_w_cooldown", 300)
        self.active_skill = 'w'
        self.active_skill_timer = 80
        damage = stats.get("skill_w_damage", 250)

        if self.target and self.target.alive:
            tx, ty = self.target.x, self.target.y
        else:
            tx, ty = self.x, self.y

        for e in enemies:
            if math.hypot(e.x - tx, e.y - ty) <= 120:
                e.take_damage(damage, self.team)
                if hasattr(e, 'attack_timer'):
                    e.attack_timer = max(
                        getattr(e, 'attack_timer', 0), 60)
        self._shake_screen(14)

    def _gravewake_e(self):
        """E - Kraken Shell: defensive barrier + heal + damage reduction."""
        stats = self._get_boss_stats()
        self.e_timer = stats.get("skill_e_cooldown", 360)
        self.active_skill = 'e'
        self.active_skill_timer = 70
        self.shell_active = True
        self.shell_timer = 300  # 5 seconds shell

        # Heal 12% max HP
        heal = int(self.max_hp * 0.12)
        self.hp = min(self.max_hp, self.hp + heal)

        self._shake_screen(10)

        try:
            import __main__
            if hasattr(__main__, 'game_instance'):
                game = __main__.game_instance
                game.effects.add_damage_number(
                    self.x, self.y - 30,
                    f"+{heal}", is_critical=True,
                    damage_type='heal')
        except Exception:
            pass

    def _gravewake_r(self, enemies):
        """R - Ravage: massive AOE water eruption around boss."""
        stats = self._get_boss_stats()
        self.r_timer = stats.get("skill_r_cooldown", 600)
        self.active_skill = 'r'
        self.active_skill_timer = 90
        damage = stats.get("skill_r_damage", 400)

        # Massive AOE around boss
        for e in enemies:
            if math.hypot(e.x - self.x, e.y - self.y) <= 200:
                e.take_damage(damage, self.team)
                if hasattr(e, 'attack_timer'):
                    e.attack_timer = max(e.attack_timer, 90)
                if hasattr(e, 'apply_slow'):
                    e.apply_slow(0.5, 180)
                # Knockback: HANYA untuk unit yang bisa bergerak.
                # Tower & Castle adalah bangunan statis - kalau
                # posisinya digeser, mereka pindah permanen dari
                # petak-nya. Unit punya .speed, bangunan tidak.
                dist = math.hypot(e.x - self.x, e.y - self.y)
                if dist > 0 and hasattr(e, 'speed'):
                    push_x = (e.x - self.x) / dist * 18
                    push_y = (e.y - self.y) / dist * 18
                    e.x += push_x
                    e.y += push_y

        self._shake_screen(25)

        # Heal 10% (kraken regeneration)
        heal = int(self.max_hp * 0.10)
        self.hp = min(self.max_hp, self.hp + heal)

        try:
            import __main__
            if hasattr(__main__, 'game_instance'):
                game = __main__.game_instance
                game.effects.add_damage_number(
                    self.x, self.y - 30,
                    f"+{heal}", is_critical=True,
                    damage_type='heal')
        except Exception:
            pass

    # ═══════════════════════════════════════════════════
    # KUNKKA AI (Admiral of the Fleet - melee + tide magic)
    # ═══════════════════════════════════════════════════

    def _smart_ai_kunkka(self, enemies, target_dist):
        """Smart AI Kunkka: melee admiral with tide/naval magic."""
        # Init timers
        if not hasattr(self, 'q_timer'):
            self.q_timer = 0
            self.w_timer = 0
            self.e_timer = 0
            self.r_timer = 0
            self.active_skill = None
            self.active_skill_timer = 0
            self.rum_buff_active = False
            self.rum_buff_timer = 0
            self.x_mark_target = None
            self.x_mark_timer = 0

        # Decrement timers
        if self.q_timer > 0:
            self.q_timer -= 1
        if self.w_timer > 0:
            self.w_timer -= 1
        if self.e_timer > 0:
            self.e_timer -= 1
        if self.r_timer > 0:
            self.r_timer -= 1
        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0:
                self.active_skill = None

        # Rum buff (from E - Ghost Ship): +30% damage
        if self.rum_buff_active:
            self.rum_buff_timer -= 1
            if self.rum_buff_timer <= 0:
                self.rum_buff_active = False
                stats = self._get_boss_stats()
                self.damage = stats.get("damage", 125)

        # X Marks the Spot - delayed burst
        if self.x_mark_timer > 0:
            self.x_mark_timer -= 1
            if self.x_mark_timer <= 0 and self.x_mark_target:
                if self.x_mark_target.alive:
                    stats = self._get_boss_stats()
                    damage = stats.get("skill_w_damage", 300)
                    for e in enemies:
                        if math.hypot(
                                e.x - self.x_mark_target.x,
                                e.y - self.x_mark_target.y
                        ) <= 120:
                            e.take_damage(damage, self.team)
                            if hasattr(e, 'attack_timer'):
                                e.attack_timer = max(
                                    e.attack_timer, 60)
                self.x_mark_target = None

        # Count nearby enemies
        nearby_count = sum(
            1 for e in enemies
            if math.hypot(e.x - self.x, e.y - self.y) <= 180
        )

        hp_ratio = self.hp / self.max_hp

        # PRIORITY 1: HP kritis + banyak enemy -> R (Torrent)
        if hp_ratio < 0.4 and nearby_count >= 2 and self.r_timer == 0:
            self._cast_r_torrent(enemies)
            return

        # PRIORITY 2: HP menurun -> E (Ghost Ship + rum buff)
        if hp_ratio < 0.6 and not self.rum_buff_active \
                and self.e_timer == 0:
            self._cast_e_ghost_ship(enemies)
            return

        # PRIORITY 3: Banyak enemy -> W (X Marks the Spot)
        if nearby_count >= 2 and self.w_timer == 0:
            self._cast_w_x_marks(enemies)
            return

        # PRIORITY 4: Target dalam range -> Q (Tide Bringer cleave)
        if target_dist < 220 and self.q_timer == 0:
            self._cast_q_tide_bringer(enemies)
            return

    def _cast_q_tide_bringer(self, enemies):
        """Q - Tide Bringer: cleaving water slash (line AOE)."""
        self.q_timer = 240
        self.active_skill = 'q'
        self.active_skill_timer = 45

        stats = self._get_boss_stats()
        damage = stats.get("skill_q_damage", 380)

        if not self.target or not self.target.alive:
            return

        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.hypot(dx, dy)
        if dist == 0:
            return
        dx /= dist
        dy /= dist

        # Cleaving line: wide AOE forward
        max_range = 250
        line_width = 70

        for e in enemies:
            ex = e.x - self.x
            ey = e.y - self.y
            proj = ex * dx + ey * dy
            if 0 < proj < max_range:
                perp = abs(ex * (-dy) + ey * dx)
                if perp < line_width:
                    e.take_damage(damage, self.team)

        self._shake_screen(15)

    def _cast_w_x_marks(self, enemies):
        """W - X Marks the Spot: mark target, delayed burst."""
        self.w_timer = 300
        self.active_skill = 'w'
        self.active_skill_timer = 80

        if self.target and self.target.alive:
            self.x_mark_target = self.target
            self.x_mark_timer = 120  # 2 second delay

        self._shake_screen(8)

    def _cast_e_ghost_ship(self, enemies):
        """E - Ghost Ship: spectral ship AOE + rum buff."""
        self.e_timer = 480
        self.active_skill = 'e'
        self.active_skill_timer = 90

        stats = self._get_boss_stats()
        damage = stats.get("skill_e_damage", 450)

        if not self.target or not self.target.alive:
            return

        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.hypot(dx, dy)
        if dist == 0:
            return
        dx /= dist
        dy /= dist

        # Wide AOE along ship path
        max_range = 300
        ship_width = 80

        for e in enemies:
            ex = e.x - self.x
            ey = e.y - self.y
            proj = ex * dx + ey * dy
            if 0 < proj < max_range:
                perp = abs(ex * (-dy) + ey * dx)
                if perp < ship_width:
                    e.take_damage(damage, self.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 90)

        # Rum buff: +30% damage for 8 seconds
        self.rum_buff_active = True
        self.rum_buff_timer = 480
        base_damage = stats.get("damage", 125)
        self.damage = int(base_damage * 1.3)

        # Heal 15% (Dutch courage)
        heal = int(self.max_hp * 0.15)
        self.hp = min(self.max_hp, self.hp + heal)

        self._shake_screen(18)

        try:
            import __main__
            if hasattr(__main__, 'game_instance'):
                game = __main__.game_instance
                game.effects.add_damage_number(
                    self.x, self.y - 30,
                    f"+{heal}", is_critical=True,
                    damage_type='heal')
        except Exception:
            pass

    def _cast_r_torrent(self, enemies):
        """R - Torrent: rising water column, massive AOE + knockup."""
        self.r_timer = 720
        self.active_skill = 'r'
        self.active_skill_timer = 100

        stats = self._get_boss_stats()
        damage = stats.get("skill_r_damage", 650)

        # Massive AOE around target location
        if self.target and self.target.alive:
            tx, ty = self.target.x, self.target.y
        else:
            tx, ty = self.x, self.y

        for e in enemies:
            if math.hypot(e.x - tx, e.y - ty) <= 200:
                e.take_damage(damage, self.team)
                if hasattr(e, 'attack_timer'):
                    e.attack_timer = max(e.attack_timer, 120)
                # Knockback: HANYA untuk unit yang bisa bergerak.
                # Tower & Castle adalah bangunan statis - kalau
                # posisinya digeser, mereka pindah permanen dari
                # petak-nya. Unit punya .speed, bangunan tidak.
                dist = math.hypot(e.x - tx, e.y - ty)
                if dist > 0 and hasattr(e, 'speed'):
                    push_x = (e.x - tx) / dist * 20
                    push_y = (e.y - ty) / dist * 20
                    e.x += push_x
                    e.y += push_y

        self._shake_screen(28)

        # Heal 20% (torrent surge)
        heal = int(self.max_hp * 0.20)
        self.hp = min(self.max_hp, self.hp + heal)

        try:
            import __main__
            if hasattr(__main__, 'game_instance'):
                game = __main__.game_instance
                game.effects.add_damage_number(
                    self.x, self.y - 30,
                    f"+{heal}", is_critical=True,
                    damage_type='heal')
        except Exception:
            pass

    def take_damage_with_defense(self, damage, from_team):
        """Override take_damage untuk defense boost"""
        self.take_damage(damage, from_team)

    def _get_boss_stats(self):
        """Helper - get stats dari boss_data.

        Saat boss kena debuff SKILL-DOWN (Mage Tower), SEMUA key numerik
        ber-*damage* dikembalikan dalam versi scaled copy.
        Juga menerapkan scaling difficulty & multiplier Enrage.
        """
        from bosses.boss_data import get_all_boss_types
        all_bosses = get_all_boss_types()
        stats = all_bosses.get(self.boss_type, {})
        mult = 1.0
        if getattr(self, 'skill_down_timer', 0) > 0:
            mult *= max(0.0, 1.0 - getattr(self, 'skill_down_amount', 0.0))
        if getattr(self, 'dmg_scaling_mult', 1.0) != 1.0:
            mult *= getattr(self, 'dmg_scaling_mult', 1.0)
        if getattr(self, 'is_enraged', False):
            mult *= 1.25
        if mult != 1.0 and stats:
            scaled = dict(stats)
            for k, v in stats.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool) \
                        and 'damage' in k:
                    scaled[k] = int(round(v * mult))
            return scaled
        return stats

    def _shake_screen(self, intensity):
        """Screen shake helper"""
        try:
            import __main__
            if hasattr(__main__, 'game_instance'):
                __main__.game_instance.effects.shake_screen(intensity)
        except Exception:
            pass

    def _use_heal_ability(self):
        """True boss heal saat HP rendah"""
        if self.ability2_cooldown_max <= 0:
            return

        self.ability2_timer = self.ability2_cooldown_max
        heal_amount = int(self.max_hp * self.ability2_heal_pct)
        self.hp = min(self.max_hp, self.hp + heal_amount)

        try:
            import __main__
            if hasattr(__main__, 'game_instance'):
                game = __main__.game_instance
                game.effects.add_damage_number(
                    self.x, self.y - 30,
                    f"+{heal_amount}",
                    is_critical=True,
                    damage_type='heal')
                game.effects.shake_screen(8)
        except Exception:
            pass

    def take_damage(self, damage, from_team, damage_type='normal',
                    source=None):
        # ═══ BLIND (Solar Brand aura): serangan fisik penyerang
        #     yang sedang buta berpeluang meleset. Boss tidak
        #     mempunyai evasion sendiri. ═══
        if damage_type == 'normal' and damage > 0 and source is not None:
            true_strike = False
            src_inv = getattr(source, "items", None)
            if src_inv is not None:
                try:
                    true_strike = src_inv.has_true_strike()
                except Exception:
                    true_strike = False
            if (not true_strike and getattr(source, "blind_timer", 0) > 0
                    and random.random()
                    < getattr(source, "blind_amount", 0.0)):
                return

        # ═══ STATUS ITEM TIER II: Soul Rend amp + Corroder shred ═══
        if damage > 0:
            if getattr(self, "dmg_amp_timer", 0) > 0:
                damage = int(round(
                    damage * (1.0 + self.dmg_amp_amount)))
            shred = getattr(self, "armor_shred_amount", 0.0)
            if damage_type != 'fire' and shred > 0:
                damage = int(round(
                    damage * (1.0 + min(1.0, shred * 0.06))))

        # ═══ INHERENT BOSS RESILIENCE (True Boss: 30%, Mini Boss: 20%) ═══
        resilience = getattr(self, 'damage_reduction', 0.20)
        if getattr(self, 'defense_boost', False):
            resilience = max(resilience, 0.45)

        effective_damage = int(damage * (1.0 - resilience))

        # ═══ ANTI-BURST PROTECTION ═══
        # Cap single hit damage so bosses cannot be 1-shot
        cap = getattr(self, 'max_damage_per_hit', int(self.max_hp * 0.10))
        if effective_damage > cap:
            effective_damage = cap

        effective_damage = max(1, effective_damage)
        self.hp -= effective_damage
        self.hurt_flash_timer = 8

        try:
            import __main__
            if hasattr(__main__, 'game_instance'):
                game = __main__.game_instance
                game.effects.add_damage_number(
                    self.x, self.y - self.radius - 10,
                    effective_damage,
                    is_critical=(effective_damage > self.max_hp * 0.03),
                    damage_type=damage_type)
                game.effects.add_hit_particles(
                    self.x, self.y, team=self.team, count=6)
        except Exception:
            pass

        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            self.defeated = True
            # Bersihkan semua debuff (burn/slow/dll.) saat mati
            self.clear_tower_debuffs()

            try:
                import __main__
                if hasattr(__main__, 'game_instance'):
                    game = __main__.game_instance
                    game.effects.add_death_explosion(
                        self.x, self.y, team=self.team, size='large')
                    shake = 28 if self.boss_class == "true" else 20
                    game.effects.shake_screen(shake)
            except Exception:
                pass

    # CATATAN: dulu ada override `apply_slow = pass` (boss kebal slow).
    # Sudah DIHAPUS - sesuai desain terbaru, debuff menara berlaku untuk
    # SEMUA unit termasuk mini boss & true boss, jadi boss sekarang
    # memakai apply_slow() bawaan TowerDebuffMixin.

    def draw(self, surface):
        if not self.alive:
            return

        x, y = int(self.x), int(self.y)
        r = self.radius
        is_true = self.boss_class == "true"

        # ═══ ENTRANCE ═══
        if self.entrance_timer > 0:
            max_entrance = 180 if is_true else 120
            self._draw_entrance(surface, x, y, max_entrance)
            return

        # ═══ ABILITY AURA ═══
        if self.ability_active:
            pulse = math.sin(self.anim_time * 0.2) * 0.3 + 0.7
            aura_r = int(self.ability_range * pulse)
            aura_surf = pygame.Surface(
                (aura_r * 2, aura_r * 2), pygame.SRCALPHA)
            for ar in range(aura_r, aura_r - 20, -3):
                alpha = max(0, min(255,
                                   int((aura_r - ar) * 8 * pulse)))
                if alpha > 0:
                    pygame.draw.circle(aura_surf,
                                       (*self.entrance_color, alpha),
                                       (aura_r, aura_r), ar)
            surface.blit(aura_surf, (x - aura_r, y - aura_r))

        # ═══ ENRAGE / FRENZY AURA ═══
        if getattr(self, 'is_enraged', False):
            self._draw_enrage_aura(surface, x, y)

        # ═══ TRUE BOSS EXTRA AURA ═══
        if is_true:
            self._draw_true_boss_aura(surface, x, y)

        # ═══ SHADOW ═══
        shadow_w = r * 2 + (10 if is_true else 0)
        pygame.draw.ellipse(surface, (0, 0, 0, 120),
                            (x - shadow_w // 2, y + r - 5, shadow_w, 12))

        # ═══ INDIKATOR DEBUFF MENARA (slow ring, burn api, pip ikon) ═══
        self._draw_tower_debuff_fx(surface, x, y, r)

        # ═══ DISPATCH RENDER PER BOSS TYPE ═══
        # OPTIMASI: dulu rantai 215 cabang if/elif dengan 215 impor
        # lokal - rata-rata ~107 perbandingan string tiap boss tiap
        # frame, dan sulit dirawat. Sekarang satu lookup dict yang
        # dibangun dari bosses/_boss_index.py (impor tetap malas:
        # modul level hanya dimuat saat boss-nya pertama digambar).
        _draw_fn = _get_boss_draw_func(self.boss_type)
        if _draw_fn is not None:
            _draw_fn(surface, self, x, y)
        else:
            self._draw_generic_body(surface, x, y, is_true)

        # ═══ LABEL ═══
        prefix = "TRUE BOSS" if is_true else "BOSS"
        if getattr(self, 'is_enraged', False):
            enrage_tag = " [ENRAGED]" if is_true else " [FRENZY]"
        else:
            enrage_tag = ""
        font = get_font(18 if not is_true else 20, "body_bold")
        label_color = (255, 60, 60) if self.is_enraged else ((255, 100, 100) if is_true else (255, 220, 100))
        name_text = font.render(f"{prefix}: {self.name}{enrage_tag}", True,
                                label_color)
        name_rect = name_text.get_rect(center=(x, y - r - 25))
        bg_rect = name_rect.inflate(8, 4)
        pygame.draw.rect(surface, (0, 0, 0), bg_rect,
                         border_radius=3)
        border_c = (255, 60, 60) if self.is_enraged else ((255, 100, 100) if is_true else (255, 200, 50))
        pygame.draw.rect(surface, border_c, bg_rect, 1,
                         border_radius=3)
        surface.blit(name_text, name_rect)

        # ═══ HP BAR ═══
        bar_w = 70 if is_true else 60
        bar_h = 10 if is_true else 8
        bx = x - bar_w // 2
        by = y - r - 15

        pygame.draw.rect(surface, (40, 0, 0),
                         (bx, by, bar_w, bar_h))
        hp_ratio = self.hp / self.max_hp
        fill = int(bar_w * hp_ratio)
        if fill > 0:
            if hp_ratio > 0.5:
                hpc = (100, 220, 100)
            elif hp_ratio > 0.25:
                hpc = (240, 220, 60)
            else:
                hpc = (240, 60, 60)
            pygame.draw.rect(surface, hpc, (bx, by, fill, bar_h))
        pygame.draw.rect(surface, border_c,
                         (bx, by, bar_w, bar_h), 1)

    def _draw_enrage_aura(self, surface, x, y):
        """Enrage / Frenzy visual aura"""
        pulse = math.sin(getattr(self, 'enrage_pulse', 0.0)) * 0.3 + 0.7
        aura_r = self.radius + int(14 * pulse)
        aura_surf = pygame.Surface(
            (aura_r * 2 + 10, aura_r * 2 + 10), pygame.SRCALPHA)
        center = aura_r + 5
        color = (255, 50, 40) if self.boss_class == "true" else (255, 140, 30)

        for r_off in range(aura_r, max(5, aura_r - 18), -3):
            alpha = max(0, min(200, int((aura_r - r_off) * 12 * pulse)))
            if alpha > 0:
                pygame.draw.circle(aura_surf, (*color, alpha),
                                   (center, center), r_off, 2)

        surface.blit(aura_surf, (x - center, y - center))

    def _draw_generic_body(self, surface, x, y, is_true):
        """Generic boss body (dipakai boss yang belum punya custom render)"""
        r = self.radius

        # Body color
        body_color = self.color
        if self.hurt_flash_timer > 0:
            body_color = (255, 255, 255)

        pygame.draw.circle(surface, (0, 0, 0), (x + 1, y + 1), r + 2)
        pygame.draw.circle(surface, body_color, (x, y), r)
        pygame.draw.circle(surface, self.color_dark, (x, y), r, 3)

        hl = (min(255, body_color[0] + 50),
              min(255, body_color[1] + 50),
              min(255, body_color[2] + 50))
        pygame.draw.circle(surface, hl,
                           (x - r // 3, y - r // 3), r // 2)

        # Crown
        crown_count = 7 if is_true else 5
        crown_color = (255, 200, 50) if not is_true else (255, 100, 100)
        for i in range(crown_count):
            angle = math.pi + (i - crown_count // 2) * 0.25
            sx = x + int(math.cos(angle) * (r + 3))
            sy = y + int(math.sin(angle) * (r + 3))
            spike_h = 8 if is_true else 6
            pygame.draw.polygon(surface, crown_color, [
                (sx - 2, sy), (sx, sy - spike_h), (sx + 2, sy)])
            if is_true:
                pygame.draw.polygon(surface, (255, 255, 200), [
                    (sx - 1, sy), (sx, sy - spike_h + 2),
                    (sx + 1, sy)])

        # Eyes
        eye_color = (255, 50, 50) if not is_true else (100, 200, 255)
        pygame.draw.circle(surface, (0, 0, 0),
                           (x - r // 3, y - r // 4), 4)
        pygame.draw.circle(surface, (0, 0, 0),
                           (x + r // 3, y - r // 4), 4)
        pygame.draw.circle(surface, eye_color,
                           (x - r // 3, y - r // 4), 2)
        pygame.draw.circle(surface, eye_color,
                           (x + r // 3, y - r // 4), 2)

        glow_surf = pygame.Surface((20, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surf, (*eye_color, 100),
                            (0, 0, 20, 8))
        surface.blit(glow_surf, (x - 10, y - r // 4 - 4))

    def _draw_true_boss_aura(self, surface, x, y):
        """Extra dark aura untuk true boss"""
        pulse = math.sin(self.pulse) * 0.3 + 0.7
        aura_r = self.radius + 15
        aura_surf = pygame.Surface(
            (aura_r * 3, aura_r * 3), pygame.SRCALPHA)

        for r_off in range(aura_r, aura_r - 15, -2):
            alpha = max(0, min(255,
                               int((aura_r - r_off) * 5 * pulse)))
            if alpha > 0:
                pygame.draw.circle(aura_surf,
                                   (*self.color, alpha),
                                   (aura_r * 3 // 2, aura_r * 3 // 2), r_off)

        surface.blit(aura_surf,
                     (x - aura_r * 3 // 2, y - aura_r * 3 // 2))

    def _draw_entrance(self, surface, x, y, max_timer):
        progress = 1 - (self.entrance_timer / max_timer)
        size = int(self.radius * progress * 2)
        is_true = self.boss_class == "true"

        if size > 0:
            aura_surf = pygame.Surface(
                (size * 3, size * 3), pygame.SRCALPHA)
            alpha = max(0, min(255, int(200 * (1 - progress))))
            pygame.draw.circle(aura_surf,
                               (*self.entrance_color, alpha),
                               (size * 3 // 2, size * 3 // 2), size)
            surface.blit(aura_surf,
                         (x - size * 3 // 2, y - size * 3 // 2))

        if self.entrance_timer > max_timer // 2:
            # Ukuran lebih ramah (Cinzel/Barlow lebih lebar dari font default),
            # + word-wrap supaya teks panjang tidak keluar layar.
            font_size = 28 if is_true else 24
            font = get_font(font_size, 'body_semibold')
            pulse = math.sin(self.anim_time * 0.2) * 0.3 + 0.7
            alpha = max(0, min(255, int(255 * pulse)))

            # Wrap per kata, maks lebar 1000px (aman utk 1280 layar)
            words = str(self.entrance_text).split()
            lines = []
            cur = ""
            for w in words:
                trial = (cur + " " + w).strip()
                if font.size(trial)[0] <= 1000:
                    cur = trial
                else:
                    if cur:
                        lines.append(cur)
                    cur = w
            if cur:
                lines.append(cur)
            if not lines:
                lines = [str(self.entrance_text)]

            start_y = 84 - (len(lines) - 1) * 18
            for li, line in enumerate(lines):
                ly = start_y + li * 34
                text = font.render(line, True, self.entrance_color)
                text.set_alpha(alpha)
                text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, ly))
                shadow = font.render(line, True, (0, 0, 0))
                shadow.set_alpha(max(0, min(255, int(200 * pulse))))
                surface.blit(shadow, (text_rect.x + 2, text_rect.y + 2))
                surface.blit(text, text_rect)

    # ═══════════════════════════════════════════════════════
    # SMART AI - LEVEL 9 BOSSES
    # ═══════════════════════════════════════════════════════

    def _init_l9_timers(self):
        if not hasattr(self, 'q_timer'):
            self.q_timer = 0
            self.w_timer = 0
            self.e_timer = 0
            self.r_timer = 0
            self.active_skill = None
            self.active_skill_timer = 0

    def _tick_l9_timers(self):
        if self.q_timer > 0: self.q_timer -= 1
        if self.w_timer > 0: self.w_timer -= 1
        if self.e_timer > 0: self.e_timer -= 1
        if self.r_timer > 0: self.r_timer -= 1
        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0:
                self.active_skill = None

    def _l9_stats(self):
        try:
            from bosses.boss_data import get_all_boss_types
            return get_all_boss_types().get(self.boss_type, {})
        except Exception:
            return {}

    def _l9_target(self, enemies):
        """Musuh hidup terdekat (untuk skill single-target)."""
        best = None
        best_d = 999999
        for e in enemies:
            if not getattr(e, "alive", True):
                continue
            d = math.hypot(e.x - self.x, e.y - self.y)
            if d < best_d:
                best_d = d
                best = e
        return best

    def _l9_aoe(self, enemies, radius, damage):
        hit = 0
        for e in enemies:
            if not getattr(e, "alive", True):
                continue
            if math.hypot(e.x - self.x, e.y - self.y) <= radius:
                e.take_damage(damage, self.team)
                hit += 1
        return hit

    # ── KENSHIRO ──
    def _smart_ai_kenshiro(self, enemies, target_dist):
        """Kenshiro: melee burst ronin. R saat ramai, W saat HP turun,
        E AOE saat 2+, Q ke target terdekat."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 200)
        hp_ratio = self.hp / self.max_hp

        if nearby >= 3 and hp_ratio < 0.5 and self.r_timer == 0:
            self.r_timer = stats.get("skill_r_cooldown", 640)
            self.active_skill = 'r'
            self.active_skill_timer = 70
            self._l9_aoe(enemies, 190, stats.get("skill_r_damage", 520))
            return
        if hp_ratio < 0.55 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 260)
            self.active_skill = 'w'
            self.active_skill_timer = 45
            tgt = self._l9_target(enemies)
            if tgt:
                dx = tgt.x - self.x
                dy = tgt.y - self.y
                d = math.hypot(dx, dy)
                if d > 1:
                    step = min(d, 90)
                    self.x += dx / d * step
                    self.y += dy / d * step
                    self.direction = 1 if dx > 0 else -1
                tgt.take_damage(stats.get("skill_w_damage", 340), self.team)
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 300)
            self.active_skill = 'e'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 150, stats.get("skill_e_damage", 320))
            return
        if target_dist < 140 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 200)
            self.active_skill = 'q'
            self.active_skill_timer = 35
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 300), self.team)
            return

    # ── KHAZAN ──
    def _smart_ai_khazan(self, enemies, target_dist):
        """Khazan: melee lockdown. R execute saat HP kritis, E spin
        saat ramai, W leap, Q chained blade."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 210)
        hp_ratio = self.hp / self.max_hp

        if nearby >= 2 and hp_ratio < 0.45 and self.r_timer == 0:
            self.r_timer = stats.get("skill_r_cooldown", 660)
            self.active_skill = 'r'
            self.active_skill_timer = 75
            self._l9_aoe(enemies, 210, stats.get("skill_r_damage", 560))
            return
        if nearby >= 3 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 300)
            self.active_skill = 'e'
            self.active_skill_timer = 60
            self._l9_aoe(enemies, 160, stats.get("skill_e_damage", 340))
            return
        if target_dist > 120 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 280)
            self.active_skill = 'w'
            self.active_skill_timer = 50
            tgt = self._l9_target(enemies)
            if tgt:
                dx = tgt.x - self.x
                dy = tgt.y - self.y
                d = math.hypot(dx, dy)
                if d > 1:
                    step = min(d, 110)
                    self.x += dx / d * step
                    self.y += dy / d * step
                    self.direction = 1 if dx > 0 else -1
                self._l9_aoe(enemies, 90, stats.get("skill_w_damage", 360))
            return
        if target_dist < 150 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 200)
            self.active_skill = 'q'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 320), self.team)
            return

    # ── WIRO ──
    def _smart_ai_wiro(self, enemies, target_dist):
        """Wiro: wind combo cepat. R typhoon saat ramai, W whirl,
        E dash saat jauh, Q wind cut."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 200)
        hp_ratio = self.hp / self.max_hp

        if nearby >= 3 and self.r_timer == 0:
            self.r_timer = stats.get("skill_r_cooldown", 620)
            self.active_skill = 'r'
            self.active_skill_timer = 80
            self._l9_aoe(enemies, 200, stats.get("skill_r_damage", 540))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 260)
            self.active_skill = 'w'
            self.active_skill_timer = 45
            self._l9_aoe(enemies, 140, stats.get("skill_w_damage", 340))
            return
        if hp_ratio < 0.5 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 240)
            self.active_skill = 'e'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                dx = tgt.x - self.x
                dy = tgt.y - self.y
                d = math.hypot(dx, dy)
                if d > 1:
                    step = min(d, 100)
                    self.x += dx / d * step
                    self.y += dy / d * step
                    self.direction = 1 if dx > 0 else -1
                tgt.take_damage(stats.get("skill_e_damage", 330), self.team)
            return
        if target_dist < 140 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 190)
            self.active_skill = 'q'
            self.active_skill_timer = 30
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 300), self.team)
            return

    # ── NARAKA (TRUE BOSS) ──
    def _smart_ai_naraka(self, enemies, target_dist):
        """Naraka: true boss executioner. R execute saat HP musuh
        rendah/ramai, E chain hammer AOE, W shadowstep, Q chaos."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 240)
        hp_ratio = self.hp / self.max_hp

        # R: execute saat ramai ATAU HP sendiri menipis
        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 640)
            self.active_skill = 'r'
            self.active_skill_timer = 90
            self._l9_aoe(enemies, 230, stats.get("skill_r_damage", 700))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 300)
            self.active_skill = 'e'
            self.active_skill_timer = 60
            self._l9_aoe(enemies, 180, stats.get("skill_e_damage", 420))
            return
        if hp_ratio < 0.6 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 260)
            self.active_skill = 'w'
            self.active_skill_timer = 50
            tgt = self._l9_target(enemies)
            if tgt:
                dx = tgt.x - self.x
                dy = tgt.y - self.y
                d = math.hypot(dx, dy)
                if d > 1:
                    step = min(d, 120)
                    self.x += dx / d * step
                    self.y += dy / d * step
                    self.direction = 1 if dx > 0 else -1
                tgt.take_damage(stats.get("skill_w_damage", 400), self.team)
            return
        if target_dist < 170 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 220)
            self.active_skill = 'q'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 380), self.team)
            return

    # ═══════════════════════════════════════════════════════
    # SMART AI - LEVEL 10 BOSSES
    # ═══════════════════════════════════════════════════════

    # ── KROGNARR (earth golem - melee slam) ──
    def _smart_ai_krognarr(self, enemies, target_dist):
        """Krognarr: stone golem. R eruption saat ramai/HP kritis,
        E rampart defensif, W seismic AOE, Q stone strike."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 220)
        hp_ratio = self.hp / self.max_hp

        if nearby >= 3 and hp_ratio < 0.5 and self.r_timer == 0:
            self.r_timer = stats.get("skill_r_cooldown", 660)
            self.active_skill = 'r'
            self.active_skill_timer = 85
            self._l9_aoe(enemies, 210, stats.get("skill_r_damage", 600))
            return
        if hp_ratio < 0.55 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 320)
            self.active_skill = 'e'
            self.active_skill_timer = 65
            self._l9_aoe(enemies, 120, stats.get("skill_e_damage", 300))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 280)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 170, stats.get("skill_w_damage", 380))
            return
        if target_dist < 200 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 210)
            self.active_skill = 'q'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 340), self.team)
            return

    # ── RAZ (fire monk - dash & punch) ──
    def _smart_ai_raz(self, enemies, target_dist):
        """Raz: fire monk. R gloom leap saat ramai, W searing dash
        saat HP turun, E surge AOE, Q overdrive."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 210)
        hp_ratio = self.hp / self.max_hp

        if nearby >= 3 and self.r_timer == 0:
            self.r_timer = stats.get("skill_r_cooldown", 640)
            self.active_skill = 'r'
            self.active_skill_timer = 80
            self._l9_aoe(enemies, 200, stats.get("skill_r_damage", 580))
            return
        if hp_ratio < 0.55 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 260)
            self.active_skill = 'w'
            self.active_skill_timer = 45
            tgt = self._l9_target(enemies)
            if tgt:
                dx = tgt.x - self.x
                dy = tgt.y - self.y
                d = math.hypot(dx, dy)
                if d > 1:
                    step = min(d, 100)
                    self.x += dx / d * step
                    self.y += dy / d * step
                    self.direction = 1 if dx > 0 else -1
                tgt.take_damage(stats.get("skill_w_damage", 360), self.team)
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 280)
            self.active_skill = 'e'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 160, stats.get("skill_e_damage", 340))
            return
        if target_dist < 170 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 190)
            self.active_skill = 'q'
            self.active_skill_timer = 35
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 330), self.team)
            return

    # ── VRASKHAN (shadow assassin - teleport & burst) ──
    def _smart_ai_vraskhan(self, enemies, target_dist):
        """Vraskhan: shadow assassin. R omni arms saat ramai/HP kritis,
        W shadow leap saat target jauh, E death slash AOE, Q thorned."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 220)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 650)
            self.active_skill = 'r'
            self.active_skill_timer = 85
            self._l9_aoe(enemies, 220, stats.get("skill_r_damage", 590))
            return
        if target_dist > 150 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 260)
            self.active_skill = 'w'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                self.x = float(tgt.x)
                self.y = float(tgt.y - 20)
                self.direction = 1 if tgt.x > self.x else -1
                tgt.take_damage(stats.get("skill_w_damage", 360), self.team)
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 280)
            self.active_skill = 'e'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 170, stats.get("skill_e_damage", 350))
            return
        if target_dist < 160 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 190)
            self.active_skill = 'q'
            self.active_skill_timer = 35
            tgt = self._l9_target(enemies)
            if tgt:
                dx = tgt.x - self.x
                dy = tgt.y - self.y
                d = math.hypot(dx, dy)
                if d > 1:
                    step = min(d, 90)
                    self.x += dx / d * step
                    self.y += dy / d * step
                    self.direction = 1 if dx > 0 else -1
                tgt.take_damage(stats.get("skill_q_damage", 340), self.team)
            return

    # ── AURETHZAR (TRUE BOSS - solar archer ranged) ──
    def _smart_ai_aurethzar(self, enemies, target_dist):
        """Aurethzar: solar archer ranged. R arrow rain saat ramai,
        W piercing saat 2+ musuh sejajar, E frost shot saat target
        dekat, Q marksman jarak jauh."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 260)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 640)
            self.active_skill = 'r'
            self.active_skill_timer = 95
            self._l9_aoe(enemies, 250, stats.get("skill_r_damage", 740))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 260)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 200, stats.get("skill_w_damage", 440))
            return
        if target_dist < 160 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 280)
            self.active_skill = 'e'
            self.active_skill_timer = 45
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_e_damage", 380), self.team)
                if hasattr(tgt, 'apply_slow'):
                    tgt.apply_slow(0.5, 90)
            return
        if target_dist < 320 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 210)
            self.active_skill = 'q'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 400), self.team)
            return

    # ═══════════════════════════════════════════════════════
    # SMART AI - LEVEL 11 BOSSES
    # ═══════════════════════════════════════════════════════

    # ── AERALITH (wind ranger - RANGED kite) ──
    def _smart_ai_aeralith(self, enemies, target_dist):
        """Aeralith: wind ranger ranged. R sky rider saat ramai/HP
        kritis, E vacuum AOE, W wind blade saat 2+, Q tailwind."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 240)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 630)
            self.active_skill = 'r'
            self.active_skill_timer = 80
            self._l9_aoe(enemies, 240, stats.get("skill_r_damage", 570))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 280)
            self.active_skill = 'e'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 170, stats.get("skill_e_damage", 340))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 260)
            self.active_skill = 'w'
            self.active_skill_timer = 45
            self._l9_aoe(enemies, 190, stats.get("skill_w_damage", 350))
            return
        if target_dist < 320 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 190)
            self.active_skill = 'q'
            self.active_skill_timer = 35
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 330), self.team)
            return

    # ── AUREX (omega knight - tank & spin) ──
    def _smart_ai_aurex(self, enemies, target_dist):
        """Aurex: omega knight. R destructive spin saat ramai,
        E aegis barrier saat HP turun, W volt blast projectile,
        Q shield crash."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 220)
        hp_ratio = self.hp / self.max_hp

        if nearby >= 3 and self.r_timer == 0:
            self.r_timer = stats.get("skill_r_cooldown", 650)
            self.active_skill = 'r'
            self.active_skill_timer = 75
            self._l9_aoe(enemies, 210, stats.get("skill_r_damage", 580))
            return
        if hp_ratio < 0.55 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 300)
            self.active_skill = 'e'
            self.active_skill_timer = 65
            self._l9_aoe(enemies, 130, stats.get("skill_e_damage", 320))
            return
        if target_dist < 280 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 270)
            self.active_skill = 'w'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_w_damage", 370), self.team)
            return
        if target_dist < 160 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 200)
            self.active_skill = 'q'
            self.active_skill_timer = 35
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 340), self.team)
            return

    # ── NYXAREVA (fallen queen - shadow assassin) ──
    def _smart_ai_nyxareva(self, enemies, target_dist):
        """Nyxareva: fallen queen. R avatar saat ramai/HP kritis,
        E whirling sacrifice AOE, W mortal wound, Q dark slash."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 220)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.45):
            self.r_timer = stats.get("skill_r_cooldown", 640)
            self.active_skill = 'r'
            self.active_skill_timer = 85
            self._l9_aoe(enemies, 220, stats.get("skill_r_damage", 590))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 280)
            self.active_skill = 'e'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 170, stats.get("skill_e_damage", 350))
            return
        if hp_ratio < 0.55 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 260)
            self.active_skill = 'w'
            self.active_skill_timer = 45
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_w_damage", 360), self.team)
            return
        if target_dist < 170 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 190)
            self.active_skill = 'q'
            self.active_skill_timer = 35
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 340), self.team)
            return

    # ── THALAKRYON (TRUE BOSS - abyssal sovereign) ──
    def _smart_ai_thalakryon(self, enemies, target_dist):
        """Thalakryon: abyssal sovereign. R metamorph saat ramai/HP
        kritis, E tidal rage AOE, W aqua shield defensif,
        Q abyssal bolt."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 260)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 640)
            self.active_skill = 'r'
            self.active_skill_timer = 95
            self._l9_aoe(enemies, 260, stats.get("skill_r_damage", 760))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 300)
            self.active_skill = 'e'
            self.active_skill_timer = 60
            self._l9_aoe(enemies, 190, stats.get("skill_e_damage", 440))
            return
        if hp_ratio < 0.6 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 260)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_w_damage", 260), self.team)
            return
        if target_dist < 340 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 210)
            self.active_skill = 'q'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 420), self.team)
            return

    # ═══════════════════════════════════════════════════════
    # SMART AI - LEVEL 12 BOSSES
    # ═══════════════════════════════════════════════════════

    # ── AURELIX (time sovereign - RANGED) ──
    def _smart_ai_aurelix(self, enemies, target_dist):
        """Aurelix: time mage ranged. R transcend saat ramai/HP kritis,
        E shockwave AOE, W will shield saat HP turun, Q time bomb."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 240)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 650)
            self.active_skill = 'r'
            self.active_skill_timer = 85
            self._l9_aoe(enemies, 240, stats.get("skill_r_damage", 600))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 300)
            self.active_skill = 'e'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 170, stats.get("skill_e_damage", 360))
            return
        if hp_ratio < 0.55 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 280)
            self.active_skill = 'w'
            self.active_skill_timer = 60
            return
        if target_dist < 320 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 200)
            self.active_skill = 'q'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 350), self.team)
            return

    # ── AURELYSSA (golden blade dancer - melee agility) ──
    def _smart_ai_aurelyssa(self, enemies, target_dist):
        """Aurelyssa: blade dancer. R phantom saat ramai/HP kritis,
        E golden wings saat 2+, W lightning sweep, Q whirlwind."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 220)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.45):
            self.r_timer = stats.get("skill_r_cooldown", 640)
            self.active_skill = 'r'
            self.active_skill_timer = 80
            self._l9_aoe(enemies, 220, stats.get("skill_r_damage", 590))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 280)
            self.active_skill = 'e'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 160, stats.get("skill_e_damage", 350))
            return
        if hp_ratio < 0.55 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 260)
            self.active_skill = 'w'
            self.active_skill_timer = 45
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_w_damage", 360), self.team)
            return
        if target_dist < 160 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 190)
            self.active_skill = 'q'
            self.active_skill_timer = 35
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 340), self.team)
            return

    # ── VARGRATH (demonic warlord - melee bruiser) ──
    def _smart_ai_vargrath(self, enemies, target_dist):
        """Vargrath: demon warlord. R soul dom saat ramai/HP kritis,
        W charge saat target jauh, E devil strike AOE, Q bloodthirst."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 220)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 660)
            self.active_skill = 'r'
            self.active_skill_timer = 85
            self._l9_aoe(enemies, 230, stats.get("skill_r_damage", 620))
            return
        if target_dist > 140 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 270)
            self.active_skill = 'w'
            self.active_skill_timer = 45
            tgt = self._l9_target(enemies)
            if tgt:
                dx = tgt.x - self.x
                dy = tgt.y - self.y
                d = math.hypot(dx, dy)
                if d > 1:
                    step = min(d, 110)
                    self.x += dx / d * step
                    self.y += dy / d * step
                    self.direction = 1 if dx > 0 else -1
                self._l9_aoe(enemies, 100, stats.get("skill_w_damage", 380))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 290)
            self.active_skill = 'e'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 170, stats.get("skill_e_damage", 370))
            return
        if target_dist < 160 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 200)
            self.active_skill = 'q'
            self.active_skill_timer = 35
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 360), self.team)
            return

    # ── NAZULMOR (TRUE BOSS - deepborn herald) ──
    def _smart_ai_nazulmor(self, enemies, target_dist):
        """Nazulmor: eldritch herald. R chaotic saat ramai/HP kritis,
        E tidal rage AOE, W aqua shield defensif, Q typhoon."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 270)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 640)
            self.active_skill = 'r'
            self.active_skill_timer = 95
            self._l9_aoe(enemies, 270, stats.get("skill_r_damage", 800))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 300)
            self.active_skill = 'e'
            self.active_skill_timer = 60
            self._l9_aoe(enemies, 200, stats.get("skill_e_damage", 460))
            return
        if hp_ratio < 0.6 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 260)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_w_damage", 280), self.team)
            return
        if target_dist < 350 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 210)
            self.active_skill = 'q'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 440), self.team)
            return

    # ═══════════════════════════════════════════════════════
    # SMART AI - LEVEL 13 BOSSES
    # ═══════════════════════════════════════════════════════

    # ── KAELDRIS (warrior commander - melee) ──
    def _smart_ai_kaeldris(self, enemies, target_dist):
        """Kaeldris: warrior commander. R duel saat ramai/HP kritis,
        E moment AOE, W press dash saat jauh, Q overwhelming."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 220)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.45):
            self.r_timer = stats.get("skill_r_cooldown", 650)
            self.active_skill = 'r'
            self.active_skill_timer = 80
            self._l9_aoe(enemies, 220, stats.get("skill_r_damage", 620))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 290)
            self.active_skill = 'e'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 170, stats.get("skill_e_damage", 370))
            return
        if target_dist > 140 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 270)
            self.active_skill = 'w'
            self.active_skill_timer = 45
            tgt = self._l9_target(enemies)
            if tgt:
                dx = tgt.x - self.x
                dy = tgt.y - self.y
                d = math.hypot(dx, dy)
                if d > 1:
                    step = min(d, 110)
                    self.x += dx / d * step
                    self.y += dy / d * step
                    self.direction = 1 if dx > 0 else -1
                tgt.take_damage(stats.get("skill_w_damage", 380), self.team)
            return
        if target_dist < 160 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 200)
            self.active_skill = 'q'
            self.active_skill_timer = 35
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 360), self.team)
            return

    # ── PYRAKLOS (spartan champion - tank) ──
    def _smart_ai_pyraklos(self, enemies, target_dist):
        """Pyraklos: spartan. R arena saat ramai, E bulwark saat HP
        turun, W rebuke AOE, Q spear of mars."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 220)
        hp_ratio = self.hp / self.max_hp

        if nearby >= 3 and self.r_timer == 0:
            self.r_timer = stats.get("skill_r_cooldown", 660)
            self.active_skill = 'r'
            self.active_skill_timer = 85
            self._l9_aoe(enemies, 230, stats.get("skill_r_damage", 640))
            return
        if hp_ratio < 0.5 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 300)
            self.active_skill = 'e'
            self.active_skill_timer = 65
            self._l9_aoe(enemies, 130, stats.get("skill_e_damage", 240))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 280)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 170, stats.get("skill_w_damage", 390))
            return
        if target_dist < 180 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 200)
            self.active_skill = 'q'
            self.active_skill_timer = 35
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 370), self.team)
            return

    # ── VELMYRTH (phantom assassin - teleport & burst) ──
    def _smart_ai_velmyrth(self, enemies, target_dist):
        """Velmyrth: phantom assassin. R coup de grace saat target
        sekarat/ramai, W phantom strike saat jauh, E blur AOE,
        Q stifling dagger."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 220)
        hp_ratio = self.hp / self.max_hp

        # R: execute saat ada musuh HP rendah ATAU ramai
        low_target = any(getattr(e, "alive", True)
                         and e.hp / max(1, e.max_hp) < 0.3
                         for e in enemies)
        if self.r_timer == 0 and (low_target or nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 640)
            self.active_skill = 'r'
            self.active_skill_timer = 80
            self._l9_aoe(enemies, 220, stats.get("skill_r_damage", 630))
            return
        if target_dist > 150 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 260)
            self.active_skill = 'w'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                self.x = float(tgt.x)
                self.y = float(tgt.y - 20)
                self.direction = 1 if tgt.x > self.x else -1
                tgt.take_damage(stats.get("skill_w_damage", 380), self.team)
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 280)
            self.active_skill = 'e'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 170, stats.get("skill_e_damage", 370))
            return
        if target_dist < 160 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 190)
            self.active_skill = 'q'
            self.active_skill_timer = 35
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 360), self.team)
            return

    # ── SOLVARIN (TRUE BOSS - holy paladin warden) ──
    def _smart_ai_solvarin(self, enemies, target_dist):
        """Solvarin: holy paladin. R guardian saat ramai/HP kritis,
        E degen aura saat 2+, W repel AOE, Q purification."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 280)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 640)
            self.active_skill = 'r'
            self.active_skill_timer = 95
            self._l9_aoe(enemies, 280, stats.get("skill_r_damage", 840))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 300)
            self.active_skill = 'e'
            self.active_skill_timer = 60
            self._l9_aoe(enemies, 200, stats.get("skill_e_damage", 380))
            return
        if hp_ratio < 0.6 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 270)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 180, stats.get("skill_w_damage", 480))
            return
        if target_dist < 360 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 210)
            self.active_skill = 'q'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 460), self.team)
            return


    # ── AZURETH (arcane sky-scribe - RANGED) ──
    def _smart_ai_azureth(self, enemies, target_dist):
        """Azureth: arcane mage ranged. R mystic flare saat ramai/
        HP kritis, E ancient seal saat 2+, W concussive blast AOE,
        Q arcane bolt single target jarak jauh."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 270)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 650)
            self.active_skill = 'r'
            self.active_skill_timer = 85
            self._l9_aoe(enemies, 270, stats.get("skill_r_damage", 680))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 290)
            self.active_skill = 'e'
            self.active_skill_timer = 60
            self._l9_aoe(enemies, 200, stats.get("skill_e_damage", 370))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 270)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 190, stats.get("skill_w_damage", 400))
            return
        if target_dist < 400 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 200)
            self.active_skill = 'q'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 380), self.team)
            return

    # ── LUMINAR (eternal custodian - RANGED mounted) ──
    def _smart_ai_luminar(self, enemies, target_dist):
        """Luminar: light custodian ranged. R spirit form saat ramai/
        HP kritis, E wisp saat 2+, W blinding light AOE, Q illuminate."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 280)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 660)
            self.active_skill = 'r'
            self.active_skill_timer = 90
            self._l9_aoe(enemies, 280, stats.get("skill_r_damage", 700))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 295)
            self.active_skill = 'e'
            self.active_skill_timer = 60
            self._l9_aoe(enemies, 205, stats.get("skill_e_damage", 380))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 275)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 195, stats.get("skill_w_damage", 410))
            return
        if target_dist < 410 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 205)
            self.active_skill = 'q'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 390), self.team)
            return

    # ── SOLARA (dawnforged sentinel - MELEE) ──
    def _smart_ai_solara(self, enemies, target_dist):
        """Solara: dawnforged sentinel melee. R solar guardian saat
        ramai/HP kritis, W celestial hammer AOE, E luminosity AOE
        + self-heal, Q starbreaker."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 240)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 680)
            self.active_skill = 'r'
            self.active_skill_timer = 90
            self._l9_aoe(enemies, 240, stats.get("skill_r_damage", 720))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 270)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 185, stats.get("skill_w_damage", 420))
            return
        if hp_ratio < 0.65 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 300)
            self.active_skill = 'e'
            self.active_skill_timer = 60
            self._l9_aoe(enemies, 195, stats.get("skill_e_damage", 390))
            self.hp = min(self.max_hp, self.hp + int(self.max_hp * 0.1))
            return
        if target_dist < 360 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 210)
            self.active_skill = 'q'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 400), self.team)
            return

    # ── PYRAETHIS (true boss - eternal firebird RANGED) ──
    def _smart_ai_pyraethis(self, enemies, target_dist):
        """Pyraethis: eternal firebird ranged. R supernova saat ramai/
        HP kritis, E sun ray beam saat 2+, W fire spirits AOE,
        Q icarus dive (execute bonus untuk target HP rendah)."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 300)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 660)
            self.active_skill = 'r'
            self.active_skill_timer = 95
            self._l9_aoe(enemies, 300, stats.get("skill_r_damage", 900))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 310)
            self.active_skill = 'e'
            self.active_skill_timer = 65
            self._l9_aoe(enemies, 220, stats.get("skill_e_damage", 460))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 280)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 200, stats.get("skill_w_damage", 500))
            return
        if target_dist < 430 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 220)
            self.active_skill = 'q'
            self.active_skill_timer = 45
            tgt = self._l9_target(enemies)
            if tgt:
                dmg = int(stats.get("skill_q_damage", 480))
                if tgt.hp / max(1, tgt.max_hp) < 0.3:
                    dmg = int(dmg * 1.5)
                tgt.take_damage(dmg, self.team)
            return


    # ── AUROTH (celestial bastion - tank MELEE) ──
    def _smart_ai_auroth(self, enemies, target_dist):
        """Auroth: bastion tank. R guardian saat ramai/HP kritis,
        E consecration AOE, W ward AOE defensif, Q ionic edge."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 240)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 700)
            self.active_skill = 'r'
            self.active_skill_timer = 90
            self._l9_aoe(enemies, 240, stats.get("skill_r_damage", 740))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 310)
            self.active_skill = 'e'
            self.active_skill_timer = 60
            self._l9_aoe(enemies, 195, stats.get("skill_e_damage", 400))
            return
        if hp_ratio < 0.6 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 280)
            self.active_skill = 'w'
            self.active_skill_timer = 60
            self._l9_aoe(enemies, 185, stats.get("skill_w_damage", 420))
            self.hp = min(self.max_hp, self.hp + int(self.max_hp * 0.1))
            return
        if target_dist < 350 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 215)
            self.active_skill = 'q'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 410), self.team)
            return

    # ── MORVEIN (phantom lancer - MELEE) ──
    def _smart_ai_morvein(self, enemies, target_dist):
        """Morvein: phantom lancer. R phantom form saat ramai/HP
        kritis, E spectral charge dash AOE, W violent strike,
        Q puncture (execute bonus untuk target HP rendah)."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 250)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 690)
            self.active_skill = 'r'
            self.active_skill_timer = 90
            self._l9_aoe(enemies, 250, stats.get("skill_r_damage", 760))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 300)
            self.active_skill = 'e'
            self.active_skill_timer = 60
            self._l9_aoe(enemies, 205, stats.get("skill_e_damage", 410))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 275)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 190, stats.get("skill_w_damage", 440))
            return
        if target_dist < 360 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 215)
            self.active_skill = 'q'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                dmg = int(stats.get("skill_q_damage", 420))
                if tgt.hp / max(1, tgt.max_hp) < 0.3:
                    dmg = int(dmg * 1.5)
                tgt.take_damage(dmg, self.team)
            return

    # ── THORVAK (ancient grovewarden - treant tank MELEE) ──
    def _smart_ai_thorvak(self, enemies, target_dist):
        """Thorvak: treant tank. R dryad saat ramai/HP kritis,
        W nature's wrath AOE, E vengeance saat HP turun, Q seed."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 250)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 680)
            self.active_skill = 'r'
            self.active_skill_timer = 90
            self._l9_aoe(enemies, 250, stats.get("skill_r_damage", 760))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 280)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 195, stats.get("skill_w_damage", 440))
            return
        if hp_ratio < 0.65 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 310)
            self.active_skill = 'e'
            self.active_skill_timer = 60
            self._l9_aoe(enemies, 200, stats.get("skill_e_damage", 410))
            return
        if target_dist < 350 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 220)
            self.active_skill = 'q'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 420), self.team)
            return

    # ── YAMAKO (true boss - primordial woodshaper MELEE) ──
    def _smart_ai_yamako(self, enemies, target_dist):
        """Yamako: woodshaper. R kannon saat ramai/HP kritis,
        E wood golem saat 2+, W wood creation AOE, Q deep forest."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 300)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 670)
            self.active_skill = 'r'
            self.active_skill_timer = 95
            self._l9_aoe(enemies, 300, stats.get("skill_r_damage", 950))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 315)
            self.active_skill = 'e'
            self.active_skill_timer = 65
            self._l9_aoe(enemies, 220, stats.get("skill_e_damage", 480))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 285)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 205, stats.get("skill_w_damage", 520))
            return
        if target_dist < 400 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 225)
            self.active_skill = 'q'
            self.active_skill_timer = 45
            tgt = self._l9_target(enemies)
            if tgt:
                dmg = int(stats.get("skill_q_damage", 500))
                if tgt.hp / max(1, tgt.max_hp) < 0.3:
                    dmg = int(dmg * 1.4)
                tgt.take_damage(dmg, self.team)
            return


    # ── IGNIRUS (infernal pyromancer - RANGED) ──
    def _smart_ai_ignirus(self, enemies, target_dist):
        """Ignirus: mage api ranged. R vengeance saat ramai/HP kritis,
        E burst fireball saat 2+, W flame shot AOE, Q searing torrent."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 280)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 690)
            self.active_skill = 'r'
            self.active_skill_timer = 90
            self._l9_aoe(enemies, 280, stats.get("skill_r_damage", 800))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 315)
            self.active_skill = 'e'
            self.active_skill_timer = 65
            self._l9_aoe(enemies, 210, stats.get("skill_e_damage", 430))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 285)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 195, stats.get("skill_w_damage", 460))
            return
        if target_dist < 410 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 225)
            self.active_skill = 'q'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 440), self.team)
            return

    # ── LEORIC (lionheart guardian - tank MELEE) ──
    def _smart_ai_leoric(self, enemies, target_dist):
        """Leoric: tank. R immortality saat HP kritis (AOE + heal),
        E conceal blast saat 2+, W sacred hammer AOE, Q fearless charge."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 250)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and hp_ratio < 0.45:
            self.r_timer = stats.get("skill_r_cooldown", 700)
            self.active_skill = 'r'
            self.active_skill_timer = 95
            self._l9_aoe(enemies, 250, stats.get("skill_r_damage", 800))
            self.hp = min(self.max_hp, self.hp + int(self.max_hp * 0.2))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 310)
            self.active_skill = 'e'
            self.active_skill_timer = 60
            self._l9_aoe(enemies, 200, stats.get("skill_e_damage", 440))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 280)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 190, stats.get("skill_w_damage", 460))
            return
        if target_dist < 350 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 225)
            self.active_skill = 'q'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 450), self.team)
            return

    # ── SHIROTAKA (tideborn tactician - shinobi MELEE) ──
    def _smart_ai_shirotaka(self, enemies, target_dist):
        """Shirotaka: shinobi. R paper bomb saat ramai/HP kritis,
        E shadow clones saat 2+, W water boundary AOE, Q hiraishin
        (execute bonus untuk target HP rendah)."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 250)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 680)
            self.active_skill = 'r'
            self.active_skill_timer = 90
            self._l9_aoe(enemies, 250, stats.get("skill_r_damage", 820))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 310)
            self.active_skill = 'e'
            self.active_skill_timer = 60
            self._l9_aoe(enemies, 205, stats.get("skill_e_damage", 450))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 280)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 190, stats.get("skill_w_damage", 470))
            return
        if target_dist < 360 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 220)
            self.active_skill = 'q'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                dmg = int(stats.get("skill_q_damage", 460))
                if tgt.hp / max(1, tgt.max_hp) < 0.3:
                    dmg = int(dmg * 1.5)
                tgt.take_damage(dmg, self.team)
            return

    # ── SEIRYUKONG (true boss - celestial simian MELEE) ──
    def _smart_ai_seiryukong(self, enemies, target_dist):
        """Seiryukong: simian. R wukong saat ramai/HP kritis,
        E jingu soldiers saat 2+, W tree dance AOE, Q boundless
        (execute bonus untuk target HP rendah)."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 300)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 680)
            self.active_skill = 'r'
            self.active_skill_timer = 95
            self._l9_aoe(enemies, 300, stats.get("skill_r_damage", 1000))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 320)
            self.active_skill = 'e'
            self.active_skill_timer = 65
            self._l9_aoe(enemies, 220, stats.get("skill_e_damage", 500))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 290)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 205, stats.get("skill_w_damage", 540))
            return
        if target_dist < 400 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 230)
            self.active_skill = 'q'
            self.active_skill_timer = 45
            tgt = self._l9_target(enemies)
            if tgt:
                dmg = int(stats.get("skill_q_damage", 520))
                if tgt.hp / max(1, tgt.max_hp) < 0.3:
                    dmg = int(dmg * 1.4)
                tgt.take_damage(dmg, self.team)
            return


    # ── KAELTHORN (azure vanguard - MELEE) ──
    def _smart_ai_kaelthorn(self, enemies, target_dist):
        """Kaelthorn: vanguard. R chivalry fists saat ramai/HP kritis,
        E defender's assault saat 2+, W justice blade AOE,
        Q bravest fighter (dash)."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 250)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 690)
            self.active_skill = 'r'
            self.active_skill_timer = 90
            self._l9_aoe(enemies, 250, stats.get("skill_r_damage", 840))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 320)
            self.active_skill = 'e'
            self.active_skill_timer = 60
            self._l9_aoe(enemies, 205, stats.get("skill_e_damage", 460))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 290)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 190, stats.get("skill_w_damage", 480))
            return
        if target_dist < 360 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 230)
            self.active_skill = 'q'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 470), self.team)
            return

    # ── SOLVANTH (radiant guardian - centaur MELEE) ──
    def _smart_ai_solvanth(self, enemies, target_dist):
        """Solvanth: centaur. R wrath saat ramai/HP kritis,
        E law & order saat 2+, W glorious pathway AOE,
        Q ring punishment."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 260)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 700)
            self.active_skill = 'r'
            self.active_skill_timer = 90
            self._l9_aoe(enemies, 260, stats.get("skill_r_damage", 860))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 320)
            self.active_skill = 'e'
            self.active_skill_timer = 60
            self._l9_aoe(enemies, 210, stats.get("skill_e_damage", 470))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 290)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 195, stats.get("skill_w_damage", 490))
            return
        if target_dist < 360 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 235)
            self.active_skill = 'q'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 480), self.team)
            return

    # ── XYRAEL (cyan wraith - assassin MELEE) ──
    def _smart_ai_xyrael(self, enemies, target_dist):
        """Xy'rael: assassin. R lightness saat ramai/HP kritis,
        E tempest saat 2+, W defiant AOE, Q finch (dash + execute)."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 250)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 680)
            self.active_skill = 'r'
            self.active_skill_timer = 90
            self._l9_aoe(enemies, 250, stats.get("skill_r_damage", 880))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 315)
            self.active_skill = 'e'
            self.active_skill_timer = 60
            self._l9_aoe(enemies, 205, stats.get("skill_e_damage", 480))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 285)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 190, stats.get("skill_w_damage", 500))
            return
        if target_dist < 360 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 225)
            self.active_skill = 'q'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                dmg = int(stats.get("skill_q_damage", 490))
                if tgt.hp / max(1, tgt.max_hp) < 0.3:
                    dmg = int(dmg * 1.5)
                tgt.take_damage(dmg, self.team)
            return

    # ── NYXARETH (true boss - cosmic sovereign RANGED) ──
    # Renderer nyxareth pakai key skill "1"-"4" (1=Starsplit,
    # 2=Realworld, 3=Spacetime, 4=Astro Realm), jadi active_skill
    # disetel ke "1"-"4" supaya FX renderer-nya muncul.
    def _smart_ai_nyxareth(self, enemies, target_dist):
        """Nyxareth: cosmic mage ranged. R astro realm saat ramai/
        HP kritis, E spacetime saat 2+, W realworld AOE, Q starsplit."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 300)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 690)
            self.active_skill = '4'
            self.active_skill_timer = 95
            self._l9_aoe(enemies, 300, stats.get("skill_r_damage", 1050))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 325)
            self.active_skill = '3'
            self.active_skill_timer = 65
            self._l9_aoe(enemies, 220, stats.get("skill_e_damage", 520))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 295)
            self.active_skill = '2'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 205, stats.get("skill_w_damage", 560))
            return
        if target_dist < 420 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 235)
            self.active_skill = '1'
            self.active_skill_timer = 45
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 540), self.team)
            return


    # ── CRYSSALIA (glacial empress - RANGED) ──
    def _smart_ai_cryssalia(self, enemies, target_dist):
        """Cryssalia: ice mage ranged. R coldest saat ramai/HP kritis,
        E frostbites saat 2+, W bitter frost AOE, Q frostshock."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 280)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 700)
            self.active_skill = 'r'
            self.active_skill_timer = 90
            self._l9_aoe(enemies, 280, stats.get("skill_r_damage", 900))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 325)
            self.active_skill = 'e'
            self.active_skill_timer = 65
            self._l9_aoe(enemies, 215, stats.get("skill_e_damage", 490))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 295)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 200, stats.get("skill_w_damage", 510))
            return
        if target_dist < 420 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 235)
            self.active_skill = 'q'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 500), self.team)
            return

    # ── KAELTHAR (storm fist - MELEE) ──
    def _smart_ai_kaelthar(self, enemies, target_dist):
        """Kaelthar: martial artist. R fist break saat ramai/HP kritis,
        E fist crack saat 2+, W quake AOE, Q charging fist (dash)."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 250)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 690)
            self.active_skill = 'r'
            self.active_skill_timer = 90
            self._l9_aoe(enemies, 250, stats.get("skill_r_damage", 920))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 320)
            self.active_skill = 'e'
            self.active_skill_timer = 60
            self._l9_aoe(enemies, 200, stats.get("skill_e_damage", 500))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 290)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 190, stats.get("skill_w_damage", 520))
            return
        if target_dist < 360 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 230)
            self.active_skill = 'q'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 510), self.team)
            return

    # ── MORKHAERA (blood-feather witch - RANGED) ──
    def _smart_ai_morkhaera(self, enemies, target_dist):
        """Mor'khaera: dark mage ranged. R ethereal saat ramai/HP
        kritis, E energy impact saat 2+, W air strike AOE,
        Q spirit burst."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 280)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 700)
            self.active_skill = 'r'
            self.active_skill_timer = 90
            self._l9_aoe(enemies, 280, stats.get("skill_r_damage", 920))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 325)
            self.active_skill = 'e'
            self.active_skill_timer = 65
            self._l9_aoe(enemies, 215, stats.get("skill_e_damage", 500))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 295)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 200, stats.get("skill_w_damage", 520))
            return
        if target_dist < 420 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 235)
            self.active_skill = 'q'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 510), self.team)
            return

    # ── AURELION (true boss - golden sovereign MELEE) ──
    def _smart_ai_aurelion(self, enemies, target_dist):
        """Aurelion: royal king. R king's summon saat ramai/HP kritis,
        E king's command saat 2+, W guardian assault AOE,
        Q call courage."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 300)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 700)
            self.active_skill = 'r'
            self.active_skill_timer = 95
            self._l9_aoe(enemies, 300, stats.get("skill_r_damage", 1100))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 330)
            self.active_skill = 'e'
            self.active_skill_timer = 65
            self._l9_aoe(enemies, 225, stats.get("skill_e_damage", 540))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 300)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 210, stats.get("skill_w_damage", 580))
            return
        if target_dist < 400 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 240)
            self.active_skill = 'q'
            self.active_skill_timer = 45
            tgt = self._l9_target(enemies)
            if tgt:
                dmg = int(stats.get("skill_q_damage", 560))
                if tgt.hp / max(1, tgt.max_hp) < 0.3:
                    dmg = int(dmg * 1.4)
                tgt.take_damage(dmg, self.team)
            return


    # ── AKAHIME (scarlet blossom - RANGED) ──
    def _smart_ai_akahime(self, enemies, target_dist):
        """Akahime: kunoichi ranged. R higanbana saat ramai/HP kritis,
        E shadow saat 2+, W soul scroll AOE, Q petal barrage."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 270)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 710)
            self.active_skill = 'r'
            self.active_skill_timer = 90
            self._l9_aoe(enemies, 270, stats.get("skill_r_damage", 950))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 330)
            self.active_skill = 'e'
            self.active_skill_timer = 65
            self._l9_aoe(enemies, 210, stats.get("skill_e_damage", 510))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 300)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 195, stats.get("skill_w_damage", 530))
            return
        if target_dist < 410 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 240)
            self.active_skill = 'q'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 520), self.team)
            return

    # ── NYXTHRAEL (cursed executioner - MELEE) ──
    def _smart_ai_nyxthrael(self, enemies, target_dist):
        """Nyxthrael: executioner. R shadowbringer saat ramai/HP kritis,
        E dark nightfall saat 2+, W nightfall AOE, Q ambush (execute)."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 260)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 700)
            self.active_skill = 'r'
            self.active_skill_timer = 90
            self._l9_aoe(enemies, 260, stats.get("skill_r_damage", 960))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 325)
            self.active_skill = 'e'
            self.active_skill_timer = 60
            self._l9_aoe(enemies, 210, stats.get("skill_e_damage", 520))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 295)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 195, stats.get("skill_w_damage", 540))
            return
        if target_dist < 360 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 235)
            self.active_skill = 'q'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                dmg = int(stats.get("skill_q_damage", 530))
                if tgt.hp / max(1, tgt.max_hp) < 0.3:
                    dmg = int(dmg * 1.5)
                tgt.take_damage(dmg, self.team)
            return

    # ── SYLVANTHEROS (verdant farseer - RANGED) ──
    def _smart_ai_sylvantheros(self, enemies, target_dist):
        """Sylvantheros: farseer ranged. R wrath saat ramai/HP kritis,
        E treants saat 2+, W teleport AOE, Q sprout."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 280)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 710)
            self.active_skill = 'r'
            self.active_skill_timer = 90
            self._l9_aoe(enemies, 280, stats.get("skill_r_damage", 960))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 330)
            self.active_skill = 'e'
            self.active_skill_timer = 65
            self._l9_aoe(enemies, 215, stats.get("skill_e_damage", 520))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 300)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 200, stats.get("skill_w_damage", 540))
            return
        if target_dist < 420 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 240)
            self.active_skill = 'q'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 530), self.team)
            return

    # ── VAELINDRA (true boss - violet sovereign RANGED) ──
    def _smart_ai_vaelindra(self, enemies, target_dist):
        """Vaelindra: violet mage ranged. R realm saat ramai/HP kritis,
        E violet requiem saat 2+, W space ring AOE, Q energy wave
        (execute bonus untuk target HP rendah)."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 310)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 710)
            self.active_skill = 'r'
            self.active_skill_timer = 95
            self._l9_aoe(enemies, 310, stats.get("skill_r_damage", 1150))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 335)
            self.active_skill = 'e'
            self.active_skill_timer = 65
            self._l9_aoe(enemies, 230, stats.get("skill_e_damage", 560))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 305)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 215, stats.get("skill_w_damage", 600))
            return
        if target_dist < 430 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 245)
            self.active_skill = 'q'
            self.active_skill_timer = 45
            tgt = self._l9_target(enemies)
            if tgt:
                dmg = int(stats.get("skill_q_damage", 580))
                if tgt.hp / max(1, tgt.max_hp) < 0.3:
                    dmg = int(dmg * 1.4)
                tgt.take_damage(dmg, self.team)
            return


    # ── ASTRAELION (starlight swordmaster - MELEE) ──
    def _smart_ai_astraelion(self, enemies, target_dist):
        """Astraelion: assassin. R zero return saat ramai/HP kritis,
        E force escape saat 2+, W spirit blade AOE, Q swordfall
        (execute bonus untuk target HP rendah)."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 260)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 710)
            self.active_skill = 'r'
            self.active_skill_timer = 90
            self._l9_aoe(enemies, 260, stats.get("skill_r_damage", 1000))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 330)
            self.active_skill = 'e'
            self.active_skill_timer = 60
            self._l9_aoe(enemies, 205, stats.get("skill_e_damage", 540))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 300)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 195, stats.get("skill_w_damage", 560))
            return
        if target_dist < 360 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 240)
            self.active_skill = 'q'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                dmg = int(stats.get("skill_q_damage", 550))
                if tgt.hp / max(1, tgt.max_hp) < 0.3:
                    dmg = int(dmg * 1.5)
                tgt.take_damage(dmg, self.team)
            return

    # ── MORVAENTHIR (soul reaper - RANGED) ──
    def _smart_ai_morvaenthir(self, enemies, target_dist):
        """Morvaenthir: necromancer ranged. R shadow realm saat ramai/
        HP kritis, E essence saat 2+, W spirit bind AOE,
        Q soul fragment."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 290)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 720)
            self.active_skill = 'r'
            self.active_skill_timer = 90
            self._l9_aoe(enemies, 290, stats.get("skill_r_damage", 1010))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 335)
            self.active_skill = 'e'
            self.active_skill_timer = 65
            self._l9_aoe(enemies, 220, stats.get("skill_e_damage", 550))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 305)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 205, stats.get("skill_w_damage", 570))
            return
        if target_dist < 420 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 245)
            self.active_skill = 'q'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 560), self.team)
            return

    # ── THORNVAEGRIM (twisted elderwood - treant tank MELEE) ──
    def _smart_ai_thornvaegrim(self, enemies, target_dist):
        """Thornvaegrim: treant tank. R grasp saat ramai/HP kritis,
        E sapling throw saat 2+, W twisted advance AOE, Q bramble."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 270)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 710)
            self.active_skill = 'r'
            self.active_skill_timer = 90
            self._l9_aoe(enemies, 270, stats.get("skill_r_damage", 1010))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 330)
            self.active_skill = 'e'
            self.active_skill_timer = 60
            self._l9_aoe(enemies, 215, stats.get("skill_e_damage", 550))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 300)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 200, stats.get("skill_w_damage", 570))
            return
        if target_dist < 360 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 245)
            self.active_skill = 'q'
            self.active_skill_timer = 40
            tgt = self._l9_target(enemies)
            if tgt:
                tgt.take_damage(stats.get("skill_q_damage", 560), self.team)
            return

    # ── MORTHRAXIS (true boss - crimson sovereign RANGED) ──
    def _smart_ai_morthraxis(self, enemies, target_dist):
        """Morthraxis: vampire ranged. R baleful saat ramai/HP kritis,
        E phantom mob saat 2+, W sanguine AOE, Q bat impale
        (execute bonus untuk target HP rendah)."""
        self._init_l9_timers()
        self._tick_l9_timers()
        stats = self._l9_stats()
        nearby = sum(1 for e in enemies if getattr(e, "alive", True)
                     and math.hypot(e.x - self.x, e.y - self.y) <= 310)
        hp_ratio = self.hp / self.max_hp

        if self.r_timer == 0 and (nearby >= 3 or hp_ratio < 0.4):
            self.r_timer = stats.get("skill_r_cooldown", 720)
            self.active_skill = 'r'
            self.active_skill_timer = 95
            self._l9_aoe(enemies, 310, stats.get("skill_r_damage", 1200))
            return
        if nearby >= 2 and self.e_timer == 0:
            self.e_timer = stats.get("skill_e_cooldown", 340)
            self.active_skill = 'e'
            self.active_skill_timer = 65
            self._l9_aoe(enemies, 225, stats.get("skill_e_damage", 580))
            return
        if nearby >= 2 and self.w_timer == 0:
            self.w_timer = stats.get("skill_w_cooldown", 310)
            self.active_skill = 'w'
            self.active_skill_timer = 55
            self._l9_aoe(enemies, 210, stats.get("skill_w_damage", 620))
            return
        if target_dist < 430 and self.q_timer == 0:
            self.q_timer = stats.get("skill_q_cooldown", 250)
            self.active_skill = 'q'
            self.active_skill_timer = 45
            tgt = self._l9_target(enemies)
            if tgt:
                dmg = int(stats.get("skill_q_damage", 600))
                if tgt.hp / max(1, tgt.max_hp) < 0.3:
                    dmg = int(dmg * 1.4)
                tgt.take_damage(dmg, self.team)
            return
