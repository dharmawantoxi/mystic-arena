"""
hero_skills/_bundle.py - semua skill handler hero

Gabungan dari 8 file:
  - base_skill.py            level modul
  - boss_hero_skills.py      namespace _NS_boss_hero_skills
  - grimjaw_skills.py        namespace _NS_grimjaw_skills
  - kaizen_skills.py         namespace _NS_kaizen_skills
  - sylara_skills.py         namespace _NS_sylara_skills
  - thorne_skills.py         namespace _NS_thorne_skills
  - vex_skills.py            namespace _NS_vex_skills
  - zephyr_skills.py         namespace _NS_zephyr_skills

Modul dibungkus kelas `_NS_<nama>` supaya simbol bernama
sama tidak saling menimpa.

Di level modul (tidak dibungkus): base_skill

File asli dihapus; nama submodul didaftarkan ke
sys.modules oleh __init__.py, jadi semua baris
`from hero_skills.<modul> import ...` tetap jalan.
"""
import math
from sound_manager import SoundManager
from settings import HERO_TYPES, HERO_LEVELS


# ====================================================================
# base_skill.py  (dependensi internal - modul lain mengimpor simbolnya langsung)
# ====================================================================
# ================================
# hero_skills/base_skill.py
# Base class untuk semua skill handler
# ================================



class BaseSkill:
    """
    Base class untuk semua skill handler hero.

    Setiap hero-specific skill class akan inherit dari ini
    dan implement:
    - init_state()
    - update_timers()
    - cast_q(), cast_w(), cast_e(), cast_r()
    """

    def __init__(self, hero):
        self.hero = hero

    # ═══════════════════════════════════════
    # ABSTRACT METHODS (implement di subclass)
    # ═══════════════════════════════════════

    def init_state(self):
        """Init state variables khusus hero ini"""
        pass

    def update_timers(self, all_units, all_towers, all_bases):
        """Update timers per frame"""
        pass

    def cast_q(self, all_units, all_towers, all_bases):
        """Q skill - basic skill"""
        return False

    def cast_w(self, all_units, all_towers, all_bases):
        """W skill - utility/defensive"""
        return False

    def cast_e(self, all_units, all_towers, all_bases):
        """E skill - mobility/combat"""
        return False

    def cast_r(self, all_units, all_towers, all_bases):
        """R skill - ULTIMATE"""
        return False

    # ═══════════════════════════════════════
    # SHARED UTILITIES (bisa dipakai semua hero)
    # ═══════════════════════════════════════

    def _get_enemies(self, all_units, all_towers, all_bases):
        """Get semua musuh dalam 1 list"""
        return self.hero._get_all_enemies(
            all_units, all_towers, all_bases)

    def _get_enemies_in_range(self, all_units, all_towers, all_bases,
                                range_val, center_x=None, center_y=None):
        """Get semua musuh dalam range tertentu"""
        if center_x is None:
            center_x = self.hero.x
        if center_y is None:
            center_y = self.hero.y

        enemies = self._get_enemies(all_units, all_towers, all_bases)
        in_range = []
        for e in enemies:
            dist = math.hypot(e.x - center_x, e.y - center_y)
            if dist <= range_val:
                in_range.append((e, dist))
        return in_range

    def _deal_aoe_damage(self, all_units, all_towers, all_bases,
                          range_val, damage_multiplier=1.0):
        """Deal AOE damage ke semua musuh dalam range"""
        enemies = self._get_enemies(all_units, all_towers, all_bases)
        hit_count = 0
        for e in enemies:
            dist = math.hypot(e.x - self.hero.x, e.y - self.hero.y)
            if dist <= range_val:
                damage = int(self.hero.skill_damage * damage_multiplier)
                # source=hero supaya damage skill ikut tercatat di
                # hero.damage_dealt (command ATTACK DAMAGE DEALER).
                e.take_damage(damage, self.hero.team, source=self.hero,
                          school=getattr(self.hero,
                                     "dmg_school", None))
                hit_count += 1
        return hit_count

    def _apply_slow(self, target, amount, duration):
        """Apply slow effect ke target (kalau bisa)"""
        if hasattr(target, 'apply_slow'):
            target.apply_slow(amount, duration)

    def _apply_stun(self, target, duration):
        """Stun target dengan set attack_timer"""
        if hasattr(target, 'attack_timer'):
            target.attack_timer = max(target.attack_timer, duration)

    def _shake_screen(self, intensity):
        """Screen shake effect"""
        try:
            import __main__
            if hasattr(__main__, 'game_instance'):
                __main__.game_instance.effects.shake_screen(intensity)
        except Exception:
            pass

    def _play_skill_sound(self, volume=0.7):
        """Play skill sound (blue team only)"""
        if self.hero.team == "blue":
            SoundManager().play('hero_skill', volume_mult=volume)

    def _add_popup(self, x, y, text, is_critical=False,
                    damage_type='normal'):
        """Add damage number popup"""
        try:
            import __main__
            if hasattr(__main__, 'game_instance'):
                __main__.game_instance.effects.add_damage_number(
                    x, y, text,
                    is_critical=is_critical,
                    damage_type=damage_type)
        except Exception:
            pass

    # ═══════════════════════════════════════
    # COOLDOWN HELPERS
    # ═══════════════════════════════════════

    def _check_q_cooldown(self):
        """Cek Q cooldown (self.hero.skill_timer)"""
        return self.hero.skill_timer <= 0

    def _check_w_cooldown(self):
        """Cek W cooldown"""
        return self.hero.w_cooldown <= 0

    def _check_e_cooldown(self):
        """Cek E cooldown"""
        return self.hero.e_cooldown <= 0

    def _check_r_cooldown(self):
        """Cek R cooldown"""
        return self.hero.r_cooldown <= 0

    # ═══════════════════════════════════════
    # AUTO-TARGETING
    #
    # Supaya skill tidak terbuang ke tempat kosong:
    #   - skill ofensif hanya keluar kalau ADA musuh terjangkau
    #   - kalau hero belum punya target, target terdekat dipilih
    #     otomatis lalu di-set jadi hero.target
    #
    # Skill self-buff (Wind Wall, Windrun, dll) TIDAK memakai guard
    # ini karena memang tidak butuh target.
    # ═══════════════════════════════════════

    # Set False di subclass kalau hero boleh cast tanpa target.
    REQUIRE_TARGET = True

    # Toleransi jangkauan: skill masih boleh keluar kalau musuh
    # sedikit di luar radius nominal.
    TARGET_RANGE_SLACK = 1.15

    def _skill_range(self, fallback=200):
        """Radius efektif skill hero ini."""
        h = self.hero
        rng = getattr(h, 'skill_range', None)
        if not rng:
            data = getattr(h, 'skill_data', None) or {}
            rng = data.get('skill_range', fallback)
        try:
            rng = float(rng)
        except Exception:
            rng = float(fallback)
        return max(float(getattr(h, 'range', 0) or 0), rng)

    def _acquire_target(self, all_units, all_towers, all_bases,
                        range_val=None):
        """
        Cari musuh terdekat yang terjangkau.

        Kalau hero sudah punya target valid & masih dalam jangkauan,
        target itu dipertahankan. Kalau tidak, ambil yang terdekat
        dan set jadi hero.target supaya konsisten.

        Return objek musuh, atau None kalau tidak ada.
        """
        h = self.hero
        if range_val is None:
            range_val = self._skill_range()
        reach = range_val * self.TARGET_RANGE_SLACK

        cur = getattr(h, 'target', None)
        if cur is not None and getattr(cur, 'alive', False):
            if math.hypot(cur.x - h.x, cur.y - h.y) <= reach:
                return cur

        best, best_dist = None, reach
        for e in self._get_enemies(all_units, all_towers, all_bases):
            if not getattr(e, 'alive', False):
                continue
            d = math.hypot(e.x - h.x, e.y - h.y)
            if d <= best_dist:
                best, best_dist = e, d

        if best is not None:
            h.target = best
        return best

    def _has_target(self, all_units, all_towers, all_bases,
                    range_val=None):
        """
        True kalau ada musuh terjangkau.

        Dipakai sebagai guard di awal cast_*: kalau False, skill
        tidak jadi keluar dan cooldown TIDAK terbakar.
        """
        if not self.REQUIRE_TARGET:
            return True
        return self._acquire_target(
            all_units, all_towers, all_bases, range_val) is not None

    # ══════════════════════════════════════
    # VISUAL SKILL STATE
    # ══════════════════════════════════════

    # Durasi default animasi per slot skill (frame @60fps).
    # Di-override per hero lewat SKILL_VISUAL_DURATION.
    _DEFAULT_VISUAL_DURATION = {"q": 60, "w": 90, "e": 60, "r": 100}

    # Override per hero. Angka disesuaikan dengan pembagi
    # `1 - timer / N` di dalam renderer heroes/*.py supaya
    # progress animasi jalan 0.0 -> 1.0 dengan pas.
    SKILL_VISUAL_DURATION = {}

    def _get_visual_duration(self, key):
        """Ambil durasi animasi untuk slot skill tertentu"""
        override = self.SKILL_VISUAL_DURATION.get(key)
        if override is not None:
            return override
        return self._DEFAULT_VISUAL_DURATION.get(key, 60)

    def _set_active_skill(self, key, duration=None):
        """
        Set state visual skill supaya renderer di heroes/*.py
        menggambar efek Q/W/E/R yang sesuai.

        Renderer membaca:
          hero.active_skill        -> "q" / "w" / "e" / "r" / None
          hero.active_skill_timer  -> countdown frame

        Timer di-tick oleh Hero.update().
        """
        if duration is None:
            duration = self._get_visual_duration(key)
        self.hero.active_skill = key
        self.hero.active_skill_timer = duration

    # ══════════════════════════════════════
    # COOLDOWN TRIGGERS
    # ══════════════════════════════════════

    def _trigger_q_cooldown(self, shake_amount=8, visual_duration=None):
        """Trigger Q cooldown + effects"""
        self.hero.skill_timer = self.hero.skill_cooldown_max
        self._set_active_skill("q", visual_duration)
        self._shake_screen(shake_amount)
        self._play_skill_sound(volume=0.7)

    def _trigger_w_cooldown(self, shake_amount=5, visual_duration=None):
        """Trigger W cooldown + effects"""
        self.hero.w_cooldown = self.hero.w_cooldown_max
        self._set_active_skill("w", visual_duration)
        self._shake_screen(shake_amount)
        self._play_skill_sound(volume=0.6)

    def _trigger_e_cooldown(self, shake_amount=6, visual_duration=None):
        """Trigger E cooldown + effects"""
        self.hero.e_cooldown = self.hero.e_cooldown_max
        self._set_active_skill("e", visual_duration)
        self._shake_screen(shake_amount)
        self._play_skill_sound(volume=0.7)

    def _trigger_r_cooldown(self, shake_amount=15, visual_duration=None):
        """Trigger R cooldown + effects"""
        self.hero.r_cooldown = self.hero.r_cooldown_max
        self._set_active_skill("r", visual_duration)
        self._shake_screen(shake_amount)
        self._play_skill_sound(volume=1.0)

# ====================================================================
# boss_hero_skills.py
# ====================================================================
class _NS_boss_hero_skills:
    """Namespace boss_hero_skills - isi asli tidak diubah."""

    # ================================
    # hero_skills/boss_hero_skills.py
    # Generic skill handler untuk hero yang berasal dari boss
    # Reuse boss skill logic
    # ================================



    class BossHeroSkills(BaseSkill):
        """
        Generic skill handler untuk boss heroes.
        Reuse skill logic dari boss AI (dari base_boss.py).
        """

        def init_state(self):
            """Init state - reuse boss state variables"""
            h = self.hero

            # Skill visual state (untuk boss renderer)
            h.active_skill = None
            h.active_skill_timer = 0

            # Skill-specific state
            h.flux_target = None
            h.flux_active_timer = 0
            h.vortex_x = 0
            h.vortex_y = 0
            h.vortex_active_timer = 0
            h.mana_void_x = 0
            h.mana_void_y = 0
            h.blink_from_x = 0
            h.blink_from_y = 0
            h.rage_active = False
            h.rage_timer = 0
            h.defense_boost = False
            h.defense_timer = 0
            h.clones_active_timer = 0
            h.clones_positions = []
            h.w_target_x = 0
            h.w_target_y = 0
            h.w_dir_x = 1
            h.w_dir_y = 0
            h.r_dir_x = 1
            h.r_dir_y = 0
            h.cold_feet_target_x = 0
            h.cold_feet_target_y = 0
            # Ignis Drachorn specific
            h.dragon_form_active = False
            h.dragon_form_timer = 0
            h.dragon_blood_active = False
            h.dragon_blood_timer = 0

        def update_timers(self, all_units, all_towers, all_bases):
            """Update state timers per frame"""
            h = self.hero

            # NOTE: active_skill_timer di-tick oleh Hero.update().
            # Jangan tick di sini juga -> dobel decrement,
            # animasi jadi 2x lebih cepat.

            # Rage buff (Drakar)
            if h.rage_active:
                h.rage_timer -= 1
                if h.rage_timer <= 0:
                    h.rage_active = False
                    # Reset damage
                    from settings import get_all_hero_types
                    stats = get_all_hero_types()[h.hero_type]
                    h.damage = stats["damage"]

            # Defense boost (Drakar)
            if h.defense_boost:
                h.defense_timer -= 1
                if h.defense_timer <= 0:
                    h.defense_boost = False

            # Vortex DOT (Ancient Apparition)
            if h.vortex_active_timer > 0:
                h.vortex_active_timer -= 1
                if h.vortex_active_timer % 20 == 0:
                    enemies = self._get_enemies(
                        all_units, all_towers, all_bases)
                    for e in enemies:
                        dist = math.hypot(e.x - h.vortex_x,
                                           e.y - h.vortex_y)
                        if dist <= 80:
                            e.take_damage(
                                int(h.skill_damage * 0.3), h.team)
                            if hasattr(e, 'apply_slow'):
                                e.apply_slow(0.5, 60)

            # Flux DOT (Morgath)
            if h.flux_active_timer > 0:
                h.flux_active_timer -= 1
                if h.flux_active_timer % 30 == 0:
                    if h.flux_target and h.flux_target.alive:
                        h.flux_target.take_damage(
                            int(h.skill_damage * 0.3), h.team)
                        if hasattr(h.flux_target, 'apply_slow'):
                            h.flux_target.apply_slow(0.4, 60)

            # Clones active (Morgath)
            if h.clones_active_timer > 0:
                h.clones_active_timer -= 1
                if h.clones_active_timer % 40 == 0:
                    if h.target and h.target.alive:
                        clone_damage = int(h.damage * 0.5)
                        h.target.take_damage(clone_damage, h.team)

                # Dragon Form (Ignis Drachorn)
            if getattr(h, 'dragon_form_active', False):
                h.dragon_form_timer -= 1
                if h.dragon_form_timer <= 0:
                    h.dragon_form_active = False
                    # Reset damage
                    from settings import get_all_hero_types
                    stats = get_all_hero_types()[h.hero_type]
                    h.damage = stats["damage"]

                # Dragon Blood buff (Ignis Drachorn)
            if getattr(h, 'dragon_blood_active', False):
                h.dragon_blood_timer -= 1
                if h.dragon_blood_timer <= 0:
                    h.dragon_blood_active = False
        # ═══════════════════════════════════════
        # SKILL REGISTRY per boss type
        # (Auto-loaded, tambah boss baru = tambah entry)
        # ═══════════════════════════════════════

        # Override durasi visual PER HERO boss (frame).  Nyzrak butuh
        # 50/50/70/90 agar sinkron 1:1 dengan renderer v2
        # (bosses/level3.py SKILL_DUR) dan lapisan FX hidup
        # (heroes/nyzrak_fx.py SKILL_DUR) — CAST->CHARGE->RELEASE
        # #match# dengan AI.  Vhalzun (rewrite v2) memakai 60/80/60/100
        # supaya lifecycle FX identik dengan versi boss-nya.  Hero lain
        # tetap memakai default _DEFAULT_VISUAL_DURATION /
        # SKILL_VISUAL_DURATION.
        BOSS_HERO_VISUAL_DURATION = {
            "nyzrak": {"q": 50, "w": 50, "e": 70, "r": 90},
            "vhalzun": {"q": 60, "w": 80, "e": 60, "r": 100},
        }

        def _get_visual_duration(self, key):
            """Durasi visual: override per-hero boss -> override kelas
            -> default bersama (urutan presedensi)."""
            per_hero = self.BOSS_HERO_VISUAL_DURATION.get(
                getattr(self.hero, "hero_type", ""))
            if per_hero:
                override = per_hero.get(key)
                if override is not None:
                    return override
            return super()._get_visual_duration(key)


        _SKILL_REGISTRY = {
            "gornak": {
                'q': '_cast_q_mana_break',
                'w': '_cast_w_blink',
                'e': '_cast_e_counterspell',
                'r': '_cast_r_mana_void',
            },
            "morgath": {
                'q': '_cast_q_spark_wraith',
                'w': '_cast_w_flux',
                'e': '_cast_e_magnetic_field',
                'r': '_cast_r_tempest_double',
            },
            "drakar": {
                'q': '_cast_q_battle_hunger',
                'w': '_cast_w_counter_helix',
                'e': '_cast_e_berserkers_call',
                'r': '_cast_r_culling_blade',
            },
            "abaddon": {
                'q': '_cast_q_mist_coil',
                'w': '_cast_w_aphotic_shield',
                'e': '_cast_e_darkness_gale',
                'r': '_cast_r_death_sever',
            },
            "alchemist": {
                'q': '_cast_q_acid_spray',
                'w': '_cast_w_unstable_concoction',
                'e': '_cast_e_chemical_rage',
                'r': '_cast_r_greevils_greed',
            },
            "ancient_apparition": {
                'q': '_cast_q_ice_vortex',
                'w': '_cast_w_chilling_touch',
                'e': '_cast_e_ice_blast',
                'r': '_cast_r_cold_feet',
            },
            "nyzrak": {
                'q': '_cast_q_arctic_burn',
                'w': '_cast_w_splinter_blast',
                'e': '_cast_e_winters_curse',
                'r': '_cast_r_cold_embrace',
            },
            "ignis_drachorn": {
                'q': '_cast_q_dragon_breath',
                'w': '_cast_w_dragon_tail',
                'e': '_cast_e_dragon_blood',
                'r': '_cast_r_elder_dragon_form',
            },
            "krobellus": {
                'q': '_cast_q_krobellus_exorcism',
                'w': '_cast_w_krobellus_silence',
                'e': '_cast_e_krobellus_siphon',
                'r': '_cast_r_krobellus_crypt',
            },
            "vhalzun": {
                'q': '_cast_q_vhalzun_death_pulse',
                'w': '_cast_w_vhalzun_heartstopper',
                'e': '_cast_e_vhalzun_reapers_scythe',
                'r': '_cast_r_vhalzun_ghost_shroud',
            },
            "kunkka": {
                'q': '_cast_q_kunkka_tide',
                'w': '_cast_w_kunkka_xmark',
                'e': '_cast_e_kunkka_ghost',
                'r': '_cast_r_kunkka_torrent',
            },
            "nyxarath": {
                'q': '_cast_q_nyxarath_shadowraze',
                'w': '_cast_w_nyxarath_necro',
                'e': '_cast_e_nyxarath_presence',
                'r': '_cast_r_nyxarath_requiem',
            },
            "gravewake": {
                'q': '_cast_q_gravewake_anchor',
                'w': '_cast_w_gravewake_tide',
                'e': '_cast_e_gravewake_shell',
                'r': '_cast_r_gravewake_ravage',
            },
            "syrentha": {
                'q': '_cast_q_syrentha_riptide',
                'w': '_cast_w_syrentha_song',
                'e': '_cast_e_syrentha_mirror',
                'r': '_cast_r_syrentha_siren',
            },
            "thalgryn": {
                'q': '_cast_q_thalgryn_waveform',
                'w': '_cast_w_thalgryn_adaptive',
                'e': '_cast_e_thalgryn_morph',
                'r': '_cast_r_thalgryn_replicate',
            },
            "malzareth": {
                'q': '_cast_q_malzareth_disruption',
                'w': '_cast_w_malzareth_soul',
                'e': '_cast_e_malzareth_poison',
                'r': '_cast_r_malzareth_disillusion',
            },
            "akashari": {
                'q': '_cast_q_akashari_strike',
                'w': '_cast_w_akashari_blink',
                'e': '_cast_e_akashari_scream',
                'r': '_cast_r_akashari_sonic',
            },
            "vorenmarr": {
                'q': '_cast_q_vorenmarr_bonds',
                'w': '_cast_w_vorenmarr_power',
                'e': '_cast_e_vorenmarr_upheaval',
                'r': '_cast_r_vorenmarr_golem',
            },
            "kenshiro": {
                'q': '_cast_q_kenshiro_swiftslash',
                'w': '_cast_w_kenshiro_assault',
                'e': '_cast_e_kenshiro_gale',
                'r': '_cast_r_kenshiro_supremacy',
            },
            "khazan": {
                'q': '_cast_q_khazan_chained',
                'w': '_cast_w_khazan_leap',
                'e': '_cast_e_khazan_spin',
                'r': '_cast_r_khazan_vanish',
            },
            "wiro": {
                'q': '_cast_q_wiro_windcut',
                'w': '_cast_w_wiro_whirl',
                'e': '_cast_e_wiro_dash',
                'r': '_cast_r_wiro_typhoon',
            },
            "naraka": {
                'q': '_cast_q_naraka_chaos',
                'w': '_cast_w_naraka_shadowstep',
                'e': '_cast_e_naraka_hammer',
                'r': '_cast_r_naraka_execution',
            },
            "krognarr": {
                'q': '_cast_q_krognarr_strike',
                'w': '_cast_w_krognarr_seismic',
                'e': '_cast_e_krognarr_rampart',
                'r': '_cast_r_krognarr_eruption',
            },
            "raz": {
                'q': '_cast_q_raz_overdrive',
                'w': '_cast_w_raz_searing',
                'e': '_cast_e_raz_surge',
                'r': '_cast_r_raz_gloom',
            },
            "vraskhan": {
                'q': '_cast_q_vraskhan_thorned',
                'w': '_cast_w_vraskhan_leap',
                'e': '_cast_e_vraskhan_deathslash',
                'r': '_cast_r_vraskhan_omni',
            },
            "aurethzar": {
                'q': '_cast_q_aurethzar_marksman',
                'w': '_cast_w_aurethzar_piercing',
                'e': '_cast_e_aurethzar_frost',
                'r': '_cast_r_aurethzar_thunder',
            },
            "aeralith": {
                'q': '_cast_q_aeralith_tailwind',
                'w': '_cast_w_aeralith_windblade',
                'e': '_cast_e_aeralith_vacuum',
                'r': '_cast_r_aeralith_skyrider',
            },
            "aurex": {
                'q': '_cast_q_aurex_shieldcrash',
                'w': '_cast_w_aurex_voltblast',
                'e': '_cast_e_aurex_aegis',
                'r': '_cast_r_aurex_spin',
            },
            "nyxareva": {
                'q': '_cast_q_nyxareva_darkslash',
                'w': '_cast_w_nyxareva_mortalwound',
                'e': '_cast_e_nyxareva_sacrifice',
                'r': '_cast_r_nyxareva_avatar',
            },
            "thalakryon": {
                'q': '_cast_q_thalakryon_bolt',
                'w': '_cast_w_thalakryon_aquashield',
                'e': '_cast_e_thalakryon_tidalrage',
                'r': '_cast_r_thalakryon_metamorph',
            },
            "aurelix": {
                'q': '_cast_q_aurelix_timebomb',
                'w': '_cast_w_aurelix_will',
                'e': '_cast_e_aurelix_shockwave',
                'r': '_cast_r_aurelix_transcend',
            },
            "aurelyssa": {
                'q': '_cast_q_aurelyssa_whirlwind',
                'w': '_cast_w_aurelyssa_sweep',
                'e': '_cast_e_aurelyssa_wings',
                'r': '_cast_r_aurelyssa_phantom',
            },
            "vargrath": {
                'q': '_cast_q_vargrath_bloodthirst',
                'w': '_cast_w_vargrath_charge',
                'e': '_cast_e_vargrath_devilstrike',
                'r': '_cast_r_vargrath_souldom',
            },
            "nazulmor": {
                'q': '_cast_q_nazulmor_typhoon',
                'w': '_cast_w_nazulmor_aquashield',
                'e': '_cast_e_nazulmor_tidalrage',
                'r': '_cast_r_nazulmor_chaotic',
            },
            "kaeldris": {
                'q': '_cast_q_kaeldris_overwhelming',
                'w': '_cast_w_kaeldris_press',
                'e': '_cast_e_kaeldris_moment',
                'r': '_cast_r_kaeldris_duel',
            },
            "pyraklos": {
                'q': '_cast_q_pyraklos_spearmars',
                'w': '_cast_w_pyraklos_rebuke',
                'e': '_cast_e_pyraklos_bulwark',
                'r': '_cast_r_pyraklos_arena',
            },
            "velmyrth": {
                'q': '_cast_q_velmyrth_dagger',
                'w': '_cast_w_velmyrth_strike',
                'e': '_cast_e_velmyrth_blur',
                'r': '_cast_r_velmyrth_coup',
            },
            "solvarin": {
                'q': '_cast_q_solvarin_purification',
                'w': '_cast_w_solvarin_repel',
                'e': '_cast_e_solvarin_degen',
                'r': '_cast_r_solvarin_guardian',
            },
            "azureth": {
                'q': '_cast_q_azureth_arcanebolt',
                'w': '_cast_w_azureth_concussive',
                'e': '_cast_e_azureth_ancientseal',
                'r': '_cast_r_azureth_mysticflare',
            },
            "luminar": {
                'q': '_cast_q_luminar_illuminate',
                'w': '_cast_w_luminar_blindinglight',
                'e': '_cast_e_luminar_wisp',
                'r': '_cast_r_luminar_spiritform',
            },
            "solara": {
                'q': '_cast_q_solara_starbreaker',
                'w': '_cast_w_solara_celestialhammer',
                'e': '_cast_e_solara_luminosity',
                'r': '_cast_r_solara_solarguardian',
            },
            "pyraethis": {
                'q': '_cast_q_pyraethis_icarusdive',
                'w': '_cast_w_pyraethis_firespirits',
                'e': '_cast_e_pyraethis_sunray',
                'r': '_cast_r_pyraethis_supernova',
            },
            "auroth": {
                'q': '_cast_q_auroth_ionicedge',
                'w': '_cast_w_auroth_ward',
                'e': '_cast_e_auroth_consecration',
                'r': '_cast_r_auroth_guardian',
            },
            "morvein": {
                'q': '_cast_q_morvein_puncture',
                'w': '_cast_w_morvein_violentstrike',
                'e': '_cast_e_morvein_spectralcharge',
                'r': '_cast_r_morvein_phantomform',
            },
            "thorvak": {
                'q': '_cast_q_thorvak_seed',
                'w': '_cast_w_thorvak_natureswrath',
                'e': '_cast_e_thorvak_vengeance',
                'r': '_cast_r_thorvak_dryad',
            },
            "yamako": {
                'q': '_cast_q_yamako_deepforest',
                'w': '_cast_w_yamako_woodcreation',
                'e': '_cast_e_yamako_woodgolem',
                'r': '_cast_r_yamako_kannon',
            },
            "ignirus": {
                'q': '_cast_q_ignirus_searingtorrent',
                'w': '_cast_w_ignirus_flameshot',
                'e': '_cast_e_ignirus_burstfireball',
                'r': '_cast_r_ignirus_vengeance',
            },
            "leoric": {
                'q': '_cast_q_leoric_fearlesscharge',
                'w': '_cast_w_leoric_sacredhammer',
                'e': '_cast_e_leoric_concealblast',
                'r': '_cast_r_leoric_immortality',
            },
            "shirotaka": {
                'q': '_cast_q_shirotaka_hiraishin',
                'w': '_cast_w_shirotaka_waterboundary',
                'e': '_cast_e_shirotaka_shadowclones',
                'r': '_cast_r_shirotaka_paperbomb',
            },
            "seiryukong": {
                'q': '_cast_q_seiryukong_boundless',
                'w': '_cast_w_seiryukong_treedance',
                'e': '_cast_e_seiryukong_jingusoldiers',
                'r': '_cast_r_seiryukong_wukong',
            },
            "kaelthorn": {
                'q': '_cast_q_kaelthorn_bravestfighter',
                'w': '_cast_w_kaelthorn_justiceblade',
                'e': '_cast_e_kaelthorn_defendersassault',
                'r': '_cast_r_kaelthorn_chivalryfists',
            },
            "solvanth": {
                'q': '_cast_q_solvanth_ringpunishment',
                'w': '_cast_w_solvanth_gloriouspathway',
                'e': '_cast_e_solvanth_laworder',
                'r': '_cast_r_solvanth_wrath',
            },
            "xyrael": {
                'q': '_cast_q_xyrael_finch',
                'w': '_cast_w_xyrael_defiant',
                'e': '_cast_e_xyrael_tempest',
                'r': '_cast_r_xyrael_lightness',
            },
            "nyxareth": {
                'q': '_cast_q_nyxareth_starsplit',
                'w': '_cast_w_nyxareth_realworld',
                'e': '_cast_e_nyxareth_spacetime',
                'r': '_cast_r_nyxareth_astrorealm',
            },
            "cryssalia": {
                'q': '_cast_q_cryssalia_frostshock',
                'w': '_cast_w_cryssalia_bitterfrost',
                'e': '_cast_e_cryssalia_frostbites',
                'r': '_cast_r_cryssalia_coldest',
            },
            "kaelthar": {
                'q': '_cast_q_kaelthar_chargingfist',
                'w': '_cast_w_kaelthar_quake',
                'e': '_cast_e_kaelthar_fistcrack',
                'r': '_cast_r_kaelthar_fistbreak',
            },
            "morkhaera": {
                'q': '_cast_q_morkhaera_spiritburst',
                'w': '_cast_w_morkhaera_airstrike',
                'e': '_cast_e_morkhaera_energyimpact',
                'r': '_cast_r_morkhaera_ethereal',
            },
            "aurelion": {
                'q': '_cast_q_aurelion_callcourage',
                'w': '_cast_w_aurelion_guardianassault',
                'e': '_cast_e_aurelion_kingscommand',
                'r': '_cast_r_aurelion_kingssummon',
            },
            "akahime": {
                'q': '_cast_q_akahime_petalbarrage',
                'w': '_cast_w_akahime_soulscroll',
                'e': '_cast_e_akahime_shadow',
                'r': '_cast_r_akahime_higanbana',
            },
            "nyxthrael": {
                'q': '_cast_q_nyxthrael_ambush',
                'w': '_cast_w_nyxthrael_nightfall',
                'e': '_cast_e_nyxthrael_darknightfall',
                'r': '_cast_r_nyxthrael_shadowbringer',
            },
            "sylvantheros": {
                'q': '_cast_q_sylvantheros_sprout',
                'w': '_cast_w_sylvantheros_teleport',
                'e': '_cast_e_sylvantheros_treants',
                'r': '_cast_r_sylvantheros_wrath',
            },
            "vaelindra": {
                'q': '_cast_q_vaelindra_energywave',
                'w': '_cast_w_vaelindra_spacering',
                'e': '_cast_e_vaelindra_violetrequiem',
                'r': '_cast_r_vaelindra_realm',
            },
            "astraelion": {
                'q': '_cast_q_astraelion_swordfall',
                'w': '_cast_w_astraelion_spiritblade',
                'e': '_cast_e_astraelion_forceescape',
                'r': '_cast_r_astraelion_zeroreturn',
            },
            "morvaenthir": {
                'q': '_cast_q_morvaenthir_soulfragment',
                'w': '_cast_w_morvaenthir_spiritbind',
                'e': '_cast_e_morvaenthir_essence',
                'r': '_cast_r_morvaenthir_shadowrealm',
            },
            "thornvaegrim": {
                'q': '_cast_q_thornvaegrim_bramble',
                'w': '_cast_w_thornvaegrim_twistedadvance',
                'e': '_cast_e_thornvaegrim_saplingthrow',
                'r': '_cast_r_thornvaegrim_grasp',
            },
            "morthraxis": {
                'q': '_cast_q_morthraxis_batimpale',
                'w': '_cast_w_morthraxis_sanguine',
                'e': '_cast_e_morthraxis_phantommob',
                'r': '_cast_r_morthraxis_baleful',
            },
        }

        # ═══════════════════════════════════════
        # GENERIC CAST DISPATCHER
        # ═══════════════════════════════════════

        def _generic_cast(self, skill_key, all_units,
                           all_towers, all_bases,
                           cooldown_check, cooldown_trigger,
                           shake_amount):
            """Generic skill dispatch berdasarkan registry"""
            if not cooldown_check():
                return False

            h = self.hero
            enemies = self._get_enemies(
                all_units, all_towers, all_bases)

            # ═══ GUARD ANTI BUANG SKILL ═══
            # Wajib ada musuh hidup dalam jangkauan skill, kalau
            # tidak skill TIDAK di-cast sama sekali (cooldown tidak
            # terpicu) - skill tidak pernah keluar ke area kosong.
            cast_range = max(int(getattr(h, 'skill_range', 100) or 100),
                             140)
            nearby = []
            for e in enemies:
                d = math.hypot(e.x - h.x, e.y - h.y)
                if d <= cast_range:
                    nearby.append((d, e))
            if not nearby:
                return False
            nearby.sort(key=lambda t: t[0])

            # Arahkan target ke musuh TERDEKAT supaya skill yang
            # menyerang target (mana break, culling blade, spark
            # wraith, dll.) pasti mengenai, bukan meleset ke
            # target lama yang sudah jauh/mati.
            tgt = h.target
            if not (tgt is not None and getattr(tgt, 'alive', False)
                    and math.hypot(tgt.x - h.x, tgt.y - h.y)
                    <= cast_range):
                h.target = nearby[0][1]

            # Lookup skill method dari registry
            recipe = self._SKILL_REGISTRY.get(h.hero_type)
            if not recipe:
                # Fallback: generic damage attack
                self._fallback_cast(h, enemies, skill_key)
                cooldown_trigger(shake_amount=shake_amount)
                return True

            method_name = recipe.get(skill_key)
            if not method_name:
                return False

            method = getattr(self, method_name, None)
            if not method:
                print(f"[BOSS_SKILL] Method {method_name} "
                      f"tidak ditemukan untuk {h.hero_type}")
                return False

            # Call skill method (bisa terima h+enemies, h saja, dll)
            import inspect
            sig = inspect.signature(method)
            num_params = len(sig.parameters)

            try:
                if num_params == 2:
                    method(h, enemies)
                elif num_params == 1:
                    method(h)
                else:
                    method()
            except Exception as e:
                print(f"[BOSS_SKILL] Cast error {method_name}: {e}")
                return False

            cooldown_trigger(shake_amount=shake_amount)
            return True

        def _fallback_cast(self, h, enemies, skill_key):
            """
            Fallback untuk boss baru yang belum ada recipe.
            Damage generic AOE atau single target.
            """
            h.active_skill = skill_key
            h.active_skill_timer = 40

            # Damage multiplier per skill
            mult = {
                'q': 1.0,
                'w': 1.2,
                'e': 1.5,
                'r': 2.5,
            }.get(skill_key, 1.0)

            # Q/W = single target, E/R = AOE
            _school = getattr(h, "dmg_school", None)
            if skill_key in ('q', 'w'):
                if h.target and h.target.alive:
                    h.target.take_damage(
                        int(h.skill_damage * mult), h.team,
                        source=h, school=_school)
            else:
                # AOE
                aoe_range = 150 if skill_key == 'e' else 200
                for e in enemies:
                    dist = math.hypot(e.x - h.x, e.y - h.y)
                    if dist <= aoe_range:
                        e.take_damage(
                            int(h.skill_damage * mult), h.team,
                            source=h, school=_school)

        # ═══════════════════════════════════════
        # PUBLIC CAST METHODS (dispatch ke _generic_cast)
        # ═══════════════════════════════════════

        def cast_q(self, all_units, all_towers, all_bases):
            return self._generic_cast(
                'q', all_units, all_towers, all_bases,
                self._check_q_cooldown,
                self._trigger_q_cooldown,
                shake_amount=10)

        def cast_w(self, all_units, all_towers, all_bases):
            return self._generic_cast(
                'w', all_units, all_towers, all_bases,
                self._check_w_cooldown,
                self._trigger_w_cooldown,
                shake_amount=8)

        def cast_e(self, all_units, all_towers, all_bases):
            return self._generic_cast(
                'e', all_units, all_towers, all_bases,
                self._check_e_cooldown,
                self._trigger_e_cooldown,
                shake_amount=8)

        def cast_r(self, all_units, all_towers, all_bases):
            return self._generic_cast(
                'r', all_units, all_towers, all_bases,
                self._check_r_cooldown,
                self._trigger_r_cooldown,
                shake_amount=15)

        # ═══════════════════════════════════════
        # GORNAK skills
        # ═══════════════════════════════════════

        def _cast_q_mana_break(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                h.target.take_damage(
                    int(h.skill_damage * 1.2), h.team)

        def _cast_w_blink(self, h):
            h.active_skill = 'w'
            h.active_skill_timer = 25
            if h.target and h.target.alive:
                h.blink_from_x = h.x
                h.blink_from_y = h.y
                dx = h.target.x - h.x
                dy = h.target.y - h.y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    offset = max(0, dist - 60)
                    h.x = h.x + (dx / dist) * offset
                    h.y = h.y + (dy / dist) * offset

        def _cast_e_counterspell(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 60
            for e in enemies:
                dist = math.hypot(e.x - h.x, e.y - h.y)
                if dist <= 100:
                    e.take_damage(int(h.skill_damage * 0.8), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 60)

        def _cast_r_mana_void(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 90
            h.mana_void_x = h.x
            h.mana_void_y = h.y
            for e in enemies:
                dist = math.hypot(e.x - h.mana_void_x,
                                   e.y - h.mana_void_y)
                if dist <= 180:
                    e.take_damage(
                        int(h.skill_damage * 2.0), h.team)

        # ═══════════════════════════════════════
        # MORGATH skills
        # ═══════════════════════════════════════

        def _cast_q_spark_wraith(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 50
            if h.target and h.target.alive:
                h.target.take_damage(
                    int(h.skill_damage * 1.3), h.team)

        def _cast_w_flux(self, h):
            h.active_skill = 'w'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                h.flux_target = h.target
                h.flux_active_timer = 240
                h.target.take_damage(
                    int(h.skill_damage * 0.5), h.team)
                if hasattr(h.target, 'apply_slow'):
                    h.target.apply_slow(0.5, 240)

        def _cast_e_magnetic_field(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 90
            for e in enemies:
                dist = math.hypot(e.x - h.x, e.y - h.y)
                if dist <= 90:
                    e.take_damage(int(h.skill_damage * 0.7), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 45)
            heal = int(h.max_hp * 0.08)
            h.hp = min(h.max_hp, h.hp + heal)

        def _cast_r_tempest_double(self, h):
            h.active_skill = 'r'
            h.active_skill_timer = 60
            h.clones_active_timer = 480
            heal = int(h.max_hp * 0.15)
            h.hp = min(h.max_hp, h.hp + heal)

        # ═══════════════════════════════════════
        # DRAKAR skills
        # ═══════════════════════════════════════

        def _cast_q_battle_hunger(self, h):
            h.active_skill = 'q'
            h.active_skill_timer = 90
            h.rage_active = True
            h.rage_timer = 300

            # Buff damage
            from settings import get_all_hero_types
            base_damage = get_all_hero_types()[h.hero_type]["damage"]
            h.damage = int(base_damage * 1.5)

            heal = int(h.max_hp * 0.1)
            h.hp = min(h.max_hp, h.hp + heal)

        def _cast_w_counter_helix(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 45
            for e in enemies:
                dist = math.hypot(e.x - h.x, e.y - h.y)
                if dist <= 100:
                    e.take_damage(
                        int(h.skill_damage * 1.5), h.team)

        def _cast_e_berserkers_call(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 60
            h.defense_boost = True
            h.defense_timer = 180

            for e in enemies:
                dist = math.hypot(e.x - h.x, e.y - h.y)
                if dist <= 120:
                    e.take_damage(int(h.skill_damage * 1.0), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 30)

        def _cast_r_culling_blade(self, h):
            h.active_skill = 'r'
            h.active_skill_timer = 60
            if h.target and h.target.alive:
                damage = int(h.skill_damage * 2.5)
                # Execute bonus
                if h.target.hp / h.target.max_hp < 0.3:
                    damage = int(damage * 2)
                h.target.take_damage(damage, h.team)

        # ═══════════════════════════════════════
        # ABADDON skills
        # ═══════════════════════════════════════

        def _cast_q_mist_coil(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 30
            if h.target and h.target.alive:
                h.target.take_damage(
                    int(h.skill_damage * 1.3), h.team)

        def _cast_w_aphotic_shield(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 90
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 100:
                    e.take_damage(int(h.skill_damage * 1.5), h.team)
            shield_hp = int(h.max_hp * 0.25)
            h.hp = min(h.max_hp, h.hp + shield_hp)

        def _cast_e_darkness_gale(self, h):
            h.active_skill = 'e'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                dx = h.target.x - h.x
                dy = h.target.y - h.y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    h.x += (dx / dist) * 80
                    h.y += (dy / dist) * 80
                h.target.take_damage(
                    int(h.skill_damage * 1.0), h.team)

        def _cast_r_death_sever(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 60
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 180:
                    e.take_damage(int(h.skill_damage * 2.5), h.team)

        # ═══════════════════════════════════════
        # ALCHEMIST skills
        # ═══════════════════════════════════════

        def _cast_q_acid_spray(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                h.target.take_damage(
                    int(h.skill_damage * 1.1), h.team)

        def _cast_w_unstable_concoction(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 60
            if h.target and h.target.alive:
                target_x = h.target.x
                target_y = h.target.y
            else:
                target_x = h.x
                target_y = h.y

            for e in enemies:
                if math.hypot(e.x - target_x,
                               e.y - target_y) <= 100:
                    e.take_damage(int(h.skill_damage * 1.5), h.team)
                    if hasattr(e, 'apply_slow'):
                        e.apply_slow(0.5, 180)

            h.w_target_x = target_x
            h.w_target_y = target_y

        def _cast_e_chemical_rage(self, h):
            h.active_skill = 'e'
            h.active_skill_timer = 60
            h.rage_active = True
            h.rage_timer = 360

            from settings import get_all_hero_types
            base_damage = get_all_hero_types()[h.hero_type]["damage"]
            h.damage = int(base_damage * 1.5)

            heal = int(h.max_hp * 0.15)
            h.hp = min(h.max_hp, h.hp + heal)

        def _cast_r_greevils_greed(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 90
            kills = 0
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 200:
                    e.take_damage(int(h.skill_damage * 2.5), h.team)
                    if not e.alive:
                        kills += 1

            if kills > 0:
                heal = kills * 100
                h.hp = min(h.max_hp, h.hp + heal)

        # ═══════════════════════════════════════
        # ANCIENT APPARITION skills
        # ═══════════════════════════════════════

        def _cast_q_ice_vortex(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 60
            if h.target and h.target.alive:
                h.vortex_x = h.target.x
                h.vortex_y = h.target.y
            else:
                h.vortex_x = h.x + 100
                h.vortex_y = h.y

            h.vortex_active_timer = 180

            for e in enemies:
                dist = math.hypot(e.x - h.vortex_x,
                                   e.y - h.vortex_y)
                if dist <= 80:
                    e.take_damage(int(h.skill_damage * 0.6), h.team)

        def _cast_w_chilling_touch(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 45

            if not h.target or not h.target.alive:
                return

            dx = h.target.x - h.x
            dy = h.target.y - h.y
            dist = math.hypot(dx, dy)
            if dist == 0:
                return

            dx /= dist
            dy /= dist

            max_range = 400
            line_width = 30

            for e in enemies:
                ex = e.x - h.x
                ey = e.y - h.y
                proj = ex * dx + ey * dy
                if 0 < proj < max_range:
                    perp = abs(ex * (-dy) + ey * dx)
                    if perp < line_width:
                        e.take_damage(
                            int(h.skill_damage * 1.5), h.team)
                        if hasattr(e, 'apply_slow'):
                            e.apply_slow(0.6, 180)

            h.w_dir_x = dx
            h.w_dir_y = dy

        def _cast_e_ice_blast(self, h):
            h.active_skill = 'e'
            h.active_skill_timer = 50
            if h.target and h.target.alive:
                h.target.take_damage(
                    int(h.skill_damage * 2.5), h.team)
                if hasattr(h.target, 'attack_timer'):
                    h.target.attack_timer = max(
                        h.target.attack_timer, 90)

        def _cast_r_cold_feet(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 90

            if not h.target or not h.target.alive:
                return

            dx = h.target.x - h.x
            dy = h.target.y - h.y
            dist = math.hypot(dx, dy)
            if dist == 0:
                return

            dx /= dist
            dy /= dist

            max_range = 500
            line_width = 60

            for e in enemies:
                ex = e.x - h.x
                ey = e.y - h.y
                proj = ex * dx + ey * dy
                if 0 < proj < max_range:
                    perp = abs(ex * (-dy) + ey * dx)
                    if perp < line_width:
                        e.take_damage(
                            int(h.skill_damage * 3.0), h.team)
                        if hasattr(e, 'apply_slow'):
                            e.apply_slow(0.7, 240)

            h.r_dir_x = dx
            h.r_dir_y = dy

        # ═══════════════════════════════════════
        # NYZRAK skills (The Hollow Blizzard)
        # Semantik 1:1 dengan AI boss (bosses/boss_data.py):
        # Q Arctic Burn / W Splinter Blast / E Winter's Curse /
        # R Cold Embrace. Visual hidup di heroes/nyzrak_fx.py.
        # ═══════════════════════════════════════

        def _cast_q_arctic_burn(self, h, enemies):
            """Q - Arctic Burn: beam frost lurus + slow 40%/120t."""
            h.active_skill = 'q'
            h.active_skill_timer = 50
            if h.target and h.target.alive:
                tx, ty = h.target.x, h.target.y
            else:
                tx, ty = h.x, h.y
            sx, sy = h.x, h.y
            max_range, line_width = 240.0, 26.0
            ln = math.hypot(tx - sx, ty - sy) or 1.0
            ux, uy = (tx - sx) / ln, (ty - sy) / ln
            for e in enemies:
                ex, ey = e.x - sx, e.y - sy
                proj = ex * ux + ey * uy
                if 0 < proj < max_range:
                    if abs(ex * -uy + ey * ux) < line_width:
                        e.take_damage(int(h.skill_damage * 1.2), h.team)
                        if hasattr(e, 'apply_slow'):
                            e.apply_slow(0.4, 120)
            try:
                from heroes import nyzrak_fx
                nyzrak_fx.notify_skill_impact(h, tx, ty, 60, 'q')
            except Exception:
                pass

        def _cast_w_splinter_blast(self, h, enemies):
            """W - Splinter Blast: ledakan serpihan es r80 di target."""
            h.active_skill = 'w'
            h.active_skill_timer = 50
            if h.target and h.target.alive:
                tx, ty = h.target.x, h.target.y
            else:
                tx, ty = h.x, h.y
            for e in enemies:
                if math.hypot(e.x - tx, e.y - ty) <= 80:
                    e.take_damage(int(h.skill_damage * 1.0), h.team)
                    if hasattr(e, 'apply_slow'):
                        e.apply_slow(0.3, 60)
            try:
                from heroes import nyzrak_fx
                nyzrak_fx.notify_skill_impact(h, tx, ty, 80, 'w')
            except Exception:
                pass

        def _cast_e_winters_curse(self, h, enemies):
            """E - Winter's Curse: kutukan kristal — kunci serangan
            target 90t + slow 70%/180t."""
            h.active_skill = 'e'
            h.active_skill_timer = 70
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.1), h.team)
                if hasattr(h.target, 'attack_timer'):
                    h.target.attack_timer = max(
                        getattr(h.target, 'attack_timer', 0), 90)
                if hasattr(h.target, 'apply_slow'):
                    h.target.apply_slow(0.7, 180)
                try:
                    from heroes import nyzrak_fx
                    nyzrak_fx.notify_skill_impact(
                        h, h.target.x, h.target.y, 44, 'e')
                except Exception:
                    pass

        def _cast_r_cold_embrace(self, h, enemies):
            """R - Cold Embrace: nova es r200, heal 15%, perisai 240t."""
            h.active_skill = 'r'
            h.active_skill_timer = 90
            h.shield_active = True
            h.shield_timer = 240
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 200:
                    e.take_damage(int(h.skill_damage * 2.0), h.team)
                    if hasattr(e, 'apply_slow'):
                        e.apply_slow(0.5, 180)
            heal = int(getattr(h, 'max_hp', h.hp) * 0.15)
            h.hp = min(getattr(h, 'max_hp', h.hp), h.hp + heal)
            try:
                from heroes import nyzrak_fx
                nyzrak_fx.notify_skill_impact(h, h.x, h.y, 200, 'r')
            except Exception:
                pass

        # ═══════════════════════════════════════
        # IGNIS DRACHORN skills
        # ═══════════════════════════════════════

        def _cast_q_dragon_breath(self, h, enemies):
            """Q - Dragon Breath: cone fire"""
            h.active_skill = 'q'
            h.active_skill_timer = 45

            if not h.target or not h.target.alive:
                return

            dx = h.target.x - h.x
            dy = h.target.y - h.y
            dist = math.hypot(dx, dy)
            if dist == 0:
                return
            dx /= dist
            dy /= dist

            max_range = 250
            cone_width = 60

            for e in enemies:
                ex = e.x - h.x
                ey = e.y - h.y
                proj = ex * dx + ey * dy
                if 0 < proj < max_range:
                    perp = abs(ex * (-dy) + ey * dx)
                    allowed_width = cone_width * (
                            0.3 + proj / max_range * 0.7)
                    if perp < allowed_width:
                        e.take_damage(
                            int(h.skill_damage * 1.6), h.team)
                        if hasattr(e, 'attack_timer'):
                            e.attack_timer = max(e.attack_timer, 45)

        def _cast_w_dragon_tail(self, h, enemies):
            """W - Dragon Tail: 360 AOE sweep"""
            h.active_skill = 'w'
            h.active_skill_timer = 40

            for e in enemies:
                dist = math.hypot(e.x - h.x, e.y - h.y)
                if dist <= 130:
                    e.take_damage(int(h.skill_damage * 1.9), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 60)

        def _cast_e_dragon_blood(self, h):
            """E - Dragon Blood: buff + heal"""
            h.active_skill = 'e'
            h.active_skill_timer = 60
            h.dragon_blood_active = True
            h.dragon_blood_timer = 480

            from settings import get_all_hero_types
            base_damage = get_all_hero_types()[h.hero_type]["damage"]
            h.damage = int(base_damage * 1.3)

            heal = int(h.max_hp * 0.20)
            h.hp = min(h.max_hp, h.hp + heal)

        def _cast_r_elder_dragon_form(self, h, enemies):
            """R - Elder Dragon Form: transform + massive AOE"""
            h.active_skill = 'r'
            h.active_skill_timer = 90

            h.dragon_form_active = True
            h.dragon_form_timer = 600

            from settings import get_all_hero_types
            base_damage = get_all_hero_types()[h.hero_type]["damage"]
            h.damage = int(base_damage * 1.8)

            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 220:
                    e.take_damage(int(h.skill_damage * 3.0), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 90)

            heal = int(h.max_hp * 0.25)
            h.hp = min(h.max_hp, h.hp + heal)

        # ═══════════════════════════════════════
        # KROBELLUS skills (Level 5 True Boss)
        # ═══════════════════════════════════════

        def _cast_q_krobellus_exorcism(self, h, enemies):
            h.active_skill = 'q'; h.active_skill_timer = 50
            for e in enemies:
                if math.hypot(e.x-h.x, e.y-h.y) <= 150:
                    e.take_damage(int(h.skill_damage * 1.5), h.team)
            # ═══ SKILL FX KROBELLS (Exorcism: blade-burst + impact) ═══
            try:
                from heroes import krobellus_fx
                krobellus_fx.notify_skill_cast(h, 'q')
                krobellus_fx.notify_skill_impact(h, h.x, h.y, 150, 'q')
            except Exception:
                pass

        def _cast_w_krobellus_silence(self, h, enemies):
            h.active_skill = 'w'; h.active_skill_timer = 60
            for e in enemies:
                if math.hypot(e.x-h.x, e.y-h.y) <= 120:
                    e.take_damage(int(h.skill_damage * 1.0), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 75)
            # ═══ SKILL FX KROBELLS (Silence: bolt void + hex) ═══
            try:
                from heroes import krobellus_fx
                krobellus_fx.notify_skill_cast(h, 'w')
                krobellus_fx.notify_skill_impact(h, h.x, h.y, 120, 'w')
            except Exception:
                pass

        def _cast_e_krobellus_siphon(self, h):
            h.active_skill = 'e'; h.active_skill_timer = 50
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.3), h.team)
                heal = int(h.skill_damage * 0.5)
                h.hp = min(h.max_hp, h.hp + heal)
                # ═══ SKILL FX KROBELLS (Siphon: arus jiwa + vortex) ═══
                try:
                    from heroes import krobellus_fx
                    krobellus_fx.notify_skill_cast(h, 'e')
                    krobellus_fx.notify_skill_impact(
                        h, h.target.x, h.target.y, 44, 'e')
                except Exception:
                    pass

        def _cast_r_krobellus_crypt(self, h, enemies):
            h.active_skill = 'r'; h.active_skill_timer = 90
            for e in enemies:
                if math.hypot(e.x-h.x, e.y-h.y) <= 200:
                    e.take_damage(int(h.skill_damage * 2.5), h.team)
            heal = int(h.max_hp * 0.15); h.hp = min(h.max_hp, h.hp + heal)
            # ═══ SKILL FX KROBELLS (Crypt: erupsi + ghost wave) ═══
            try:
                from heroes import krobellus_fx
                krobellus_fx.notify_skill_cast(h, 'r')
                krobellus_fx.notify_skill_impact(h, h.x, h.y, 200, 'r')
            except Exception:
                pass

        # ═══════════════════════════════════════
        # VHALZUN skills (Level 5 Mini Boss — hero unlock)
        # Kit identik versi boss: Death Pulse / Heartstopper /
        # Reaper's Scythe / Ghost Shroud. FX hidup di
        # heroes/vhalzun_fx.py (nova jiwa, sigil heks + leech,
        # gelombang sabit, wraith + cangkang spektral).
        # ═══════════════════════════════════════

        def _cast_q_vhalzun_death_pulse(self, h, enemies):
            h.active_skill = 'q'; h.active_skill_timer = 60
            for e in enemies:
                if math.hypot(e.x-h.x, e.y-h.y) <= 130:
                    e.take_damage(int(h.skill_damage * 1.5), h.team)
            # ═══ SKILL FX VHALZUN (Death Pulse: nova jiwa bergerigi) ═══
            try:
                from heroes import vhalzun_fx
                vhalzun_fx.notify_skill_cast(h, 'q')
                vhalzun_fx.notify_skill_impact(h, h.x, h.y, 130, 'q')
            except Exception:
                pass

        def _cast_w_vhalzun_heartstopper(self, h, enemies):
            h.active_skill = 'w'; h.active_skill_timer = 80
            for e in enemies:
                if math.hypot(e.x-h.x, e.y-h.y) <= 150:
                    e.take_damage(int(h.skill_damage * 1.0), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 60)
            # ═══ SKILL FX VHALZUN (Heartstopper: sigil heks + leech) ═══
            try:
                from heroes import vhalzun_fx
                vhalzun_fx.notify_skill_cast(h, 'w')
                vhalzun_fx.notify_skill_impact(h, h.x, h.y, 150, 'w')
            except Exception:
                pass

        def _cast_e_vhalzun_reapers_scythe(self, h, enemies):
            h.active_skill = 'e'; h.active_skill_timer = 60
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.8), h.team)
            # ═══ SKILL FX VHALZUN (Reaper's Scythe: gelombang sabit) ═══
            try:
                from heroes import vhalzun_fx
                vhalzun_fx.notify_skill_cast(h, 'e')
            except Exception:
                pass

        def _cast_r_vhalzun_ghost_shroud(self, h, enemies):
            h.active_skill = 'r'; h.active_skill_timer = 100
            for e in enemies:
                if math.hypot(e.x-h.x, e.y-h.y) <= 150:
                    e.take_damage(int(h.skill_damage * 1.4), h.team)
            heal = int(h.max_hp * 0.18); h.hp = min(h.max_hp, h.hp + heal)
            # ═══ SKILL FX VHALZUN (Ghost Shroud: wraith + cangkang) ═══
            try:
                from heroes import vhalzun_fx
                vhalzun_fx.notify_skill_cast(h, 'r')
                vhalzun_fx.notify_skill_impact(h, h.x, h.y, 150, 'r')
            except Exception:
                pass

        # ═══════════════════════════════════════
        # KUNKKA skills (Level 6 True Boss)
        # ═══════════════════════════════════════

        def _cast_q_kunkka_tide(self, h, enemies):
            h.active_skill = 'q'; h.active_skill_timer = 45
            if not h.target or not h.target.alive: return
            dx = h.target.x-h.x; dy = h.target.y-h.y; dist = math.hypot(dx,dy)
            if dist == 0: return
            dx/=dist; dy/=dist
            for e in enemies:
                ex = e.x-h.x; ey = e.y-h.y; proj = ex*dx+ey*dy
                if 0 < proj < 250:
                    perp = abs(ex*(-dy)+ey*dx)
                    if perp < 70: e.take_damage(int(h.skill_damage*1.8), h.team)

        def _cast_w_kunkka_xmark(self, h, enemies):
            h.active_skill = 'w'; h.active_skill_timer = 80
            if h.target and h.target.alive:
                tx, ty = h.target.x, h.target.y
                for e in enemies:
                    if math.hypot(e.x-tx, e.y-ty) <= 120:
                        e.take_damage(int(h.skill_damage*1.5), h.team)
                        if hasattr(e, 'attack_timer'):
                            e.attack_timer = max(e.attack_timer, 60)

        def _cast_e_kunkka_ghost(self, h, enemies):
            h.active_skill = 'e'; h.active_skill_timer = 90
            if not h.target or not h.target.alive: return
            dx = h.target.x-h.x; dy = h.target.y-h.y; dist = math.hypot(dx,dy)
            if dist == 0: return
            dx/=dist; dy/=dist
            for e in enemies:
                ex = e.x-h.x; ey = e.y-h.y; proj = ex*dx+ey*dy
                if 0 < proj < 300:
                    perp = abs(ex*(-dy)+ey*dx)
                    if perp < 80:
                        e.take_damage(int(h.skill_damage*2.2), h.team)
                        if hasattr(e, 'attack_timer'):
                            e.attack_timer = max(e.attack_timer, 90)
            heal = int(h.max_hp * 0.15); h.hp = min(h.max_hp, h.hp + heal)

        def _cast_r_kunkka_torrent(self, h, enemies):
            h.active_skill = 'r'; h.active_skill_timer = 100
            if h.target and h.target.alive:
                tx, ty = h.target.x, h.target.y
            else:
                tx, ty = h.x, h.y
            for e in enemies:
                if math.hypot(e.x-tx, e.y-ty) <= 200:
                    e.take_damage(int(h.skill_damage*3.0), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 120)
            heal = int(h.max_hp * 0.20); h.hp = min(h.max_hp, h.hp + heal)

        # ═══════════════════════════════════════
        # NYXARATH skills (Level 7 True Boss)
        # ═══════════════════════════════════════

        def _cast_q_nyxarath_shadowraze(self, h, enemies):
            h.active_skill = 'q'; h.active_skill_timer = 40
            # Auto-target terdekat
            closest = None; closest_dist = 9999
            for e in enemies:
                d = math.hypot(e.x-h.x, e.y-h.y)
                if d < closest_dist: closest_dist = d; closest = e
            if not closest or closest_dist > 300: return
            dx = closest.x-h.x; dy = closest.y-h.y; dist = math.hypot(dx,dy)
            if dist == 0: return
            dx/=dist; dy/=dist
            for e in enemies:
                ex = e.x-h.x; ey = e.y-h.y; proj = ex*dx+ey*dy
                if 0 < proj < 280:
                    perp = abs(ex*(-dy)+ey*dx)
                    if perp < 50:
                        e.take_damage(int(h.skill_damage*1.8), h.team)
                        if hasattr(e, 'attack_timer'):
                            e.attack_timer = max(e.attack_timer, 45)

        def _cast_w_nyxarath_necro(self, h, enemies):
            h.active_skill = 'w'; h.active_skill_timer = 70
            kills = 0
            for e in enemies:
                if math.hypot(e.x-h.x, e.y-h.y) <= 180:
                    e.take_damage(int(h.skill_damage*1.7), h.team)
                    if not e.alive: kills += 1
            from settings import get_all_hero_types
            base_damage = get_all_hero_types()[h.hero_type]["damage"]
            h.damage = int(base_damage * 1.4)
            h.rage_active = True; h.rage_timer = 480
            heal = int(h.max_hp * 0.08) + kills * 30
            h.hp = min(h.max_hp, h.hp + heal)

        def _cast_e_nyxarath_presence(self, h, enemies):
            h.active_skill = 'e'; h.active_skill_timer = 80
            for e in enemies:
                if math.hypot(e.x-h.x, e.y-h.y) <= 200:
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 90)
                    if hasattr(e, 'apply_slow'):
                        e.apply_slow(0.5, 240)
            heal = int(h.max_hp * 0.12); h.hp = min(h.max_hp, h.hp + heal)

        def _cast_r_nyxarath_requiem(self, h, enemies):
            h.active_skill = 'r'; h.active_skill_timer = 110
            for e in enemies:
                if math.hypot(e.x-h.x, e.y-h.y) <= 220:
                    e.take_damage(int(h.skill_damage*3.0), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 120)
            heal = int(h.max_hp * 0.15); h.hp = min(h.max_hp, h.hp + heal)

        # ═══════════════════════════════════════
        # GRAVEWAKE skills (Level 6 Mini Boss)
        # ═══════════════════════════════════════

        def _cast_q_gravewake_anchor(self, h, enemies):
            h.active_skill = 'q'; h.active_skill_timer = 45
            if not h.target or not h.target.alive: return
            dx = h.target.x-h.x; dy = h.target.y-h.y; dist = math.hypot(dx,dy)
            if dist == 0: return
            dx/=dist; dy/=dist
            for e in enemies:
                ex = e.x-h.x; ey = e.y-h.y; proj = ex*dx+ey*dy
                if 0 < proj < 200:
                    perp = abs(ex*(-dy)+ey*dx)
                    if perp < 60:
                        e.take_damage(int(h.skill_damage*1.4), h.team)
                        if hasattr(e, 'apply_slow'):
                            e.apply_slow(0.5, 180)

        def _cast_w_gravewake_tide(self, h, enemies):
            h.active_skill = 'w'; h.active_skill_timer = 80
            if h.target and h.target.alive:
                tx, ty = h.target.x, h.target.y
            else:
                tx, ty = h.x, h.y
            for e in enemies:
                if math.hypot(e.x-tx, e.y-ty) <= 120:
                    e.take_damage(int(h.skill_damage*1.3), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 60)

        def _cast_e_gravewake_shell(self, h):
            h.active_skill = 'e'; h.active_skill_timer = 70
            h.defense_boost = True; h.defense_timer = 300
            heal = int(h.max_hp * 0.12); h.hp = min(h.max_hp, h.hp + heal)

        def _cast_r_gravewake_ravage(self, h, enemies):
            h.active_skill = 'r'; h.active_skill_timer = 90
            for e in enemies:
                if math.hypot(e.x-h.x, e.y-h.y) <= 200:
                    e.take_damage(int(h.skill_damage*2.0), h.team)
                    if hasattr(e, 'apply_slow'):
                        e.apply_slow(0.5, 180)
            heal = int(h.max_hp * 0.10); h.hp = min(h.max_hp, h.hp + heal)

        # ═══════════════════════════════════════
        # SYRENTHA skills (Level 6 Mini Boss)
        # ═══════════════════════════════════════

        def _cast_q_syrentha_riptide(self, h, enemies):
            h.active_skill = 'q'; h.active_skill_timer = 45
            if not h.target or not h.target.alive: return
            dx = h.target.x-h.x; dy = h.target.y-h.y; dist = math.hypot(dx,dy)
            if dist == 0: return
            dx/=dist; dy/=dist
            for e in enemies:
                ex = e.x-h.x; ey = e.y-h.y; proj = ex*dx+ey*dy
                if 0 < proj < 250:
                    perp = abs(ex*(-dy)+ey*dx)
                    if perp < 70:
                        e.take_damage(int(h.skill_damage*1.3), h.team)
                        if hasattr(e, 'apply_slow'):
                            e.apply_slow(0.5, 180)

        def _cast_w_syrentha_song(self, h, enemies):
            h.active_skill = 'w'; h.active_skill_timer = 80
            for e in enemies:
                if math.hypot(e.x-h.x, e.y-h.y) <= 150:
                    e.take_damage(int(h.skill_damage*1.0), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 120)
                    if hasattr(e, 'apply_slow'):
                        e.apply_slow(0.7, 240)

        def _cast_e_syrentha_mirror(self, h):
            h.active_skill = 'e'; h.active_skill_timer = 70
            h.rage_active = True; h.rage_timer = 360
            from settings import get_all_hero_types
            base_damage = get_all_hero_types()[h.hero_type]["damage"]
            h.damage = int(base_damage * 1.4)
            heal = int(h.max_hp * 0.12); h.hp = min(h.max_hp, h.hp + heal)

        def _cast_r_syrentha_siren(self, h, enemies):
            h.active_skill = 'r'; h.active_skill_timer = 90
            for e in enemies:
                if math.hypot(e.x-h.x, e.y-h.y) <= 220:
                    e.take_damage(int(h.skill_damage*2.2), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 150)
            heal = int(h.max_hp * 0.10); h.hp = min(h.max_hp, h.hp + heal)

        # ═══════════════════════════════════════
        # THALGRYN skills (Level 6 Mini Boss)
        # ═══════════════════════════════════════

        def _cast_q_thalgryn_waveform(self, h, enemies):
            h.active_skill = 'q'; h.active_skill_timer = 60
            if not h.target or not h.target.alive: return
            dx = h.target.x-h.x; dy = h.target.y-h.y; dist = math.hypot(dx,dy)
            if dist == 0: return
            dx/=dist; dy/=dist
            for e in enemies:
                ex = e.x-h.x; ey = e.y-h.y; proj = ex*dx+ey*dy
                if 0 < proj < 250:
                    perp = abs(ex*(-dy)+ey*dx)
                    if perp < 50: e.take_damage(int(h.skill_damage*1.6), h.team)
            surge = min(dist, 200); h.x += dx*surge; h.y += dy*surge

        def _cast_w_thalgryn_adaptive(self, h, enemies):
            h.active_skill = 'w'; h.active_skill_timer = 50
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage*2.0), h.team)
                for e in enemies:
                    if e != h.target and math.hypot(e.x-h.target.x, e.y-h.target.y) <= 60:
                        e.take_damage(int(h.skill_damage*0.7), h.team)

        def _cast_e_thalgryn_morph(self, h):
            h.active_skill = 'e'; h.active_skill_timer = 60
            h.rage_active = True; h.rage_timer = 300
            from settings import get_all_hero_types
            base_damage = get_all_hero_types()[h.hero_type]["damage"]
            h.damage = int(base_damage * 1.35)
            heal = int(h.max_hp * 0.14); h.hp = min(h.max_hp, h.hp + heal)

        def _cast_r_thalgryn_replicate(self, h, enemies):
            h.active_skill = 'r'; h.active_skill_timer = 80
            for e in enemies:
                if math.hypot(e.x-h.x, e.y-h.y) <= 200:
                    e.take_damage(int(h.skill_damage*2.0), h.team)
                    if hasattr(e, 'apply_slow'):
                        e.apply_slow(0.4, 180)
            heal = int(h.max_hp * 0.10); h.hp = min(h.max_hp, h.hp + heal)

        # ═══════════════════════════════════════
        # MALZARETH skills (Level 7 Mini Boss)
        # ═══════════════════════════════════════

        def _cast_q_malzareth_disruption(self, h, enemies):
            h.active_skill = 'q'; h.active_skill_timer = 60
            if h.target and h.target.alive:
                tx, ty = h.target.x, h.target.y
            else:
                tx, ty = h.x+100, h.y
            for e in enemies:
                if math.hypot(e.x-tx, e.y-ty) <= 100:
                    e.take_damage(int(h.skill_damage*1.5), h.team)

        def _cast_w_malzareth_soul(self, h, enemies):
            h.active_skill = 'w'; h.active_skill_timer = 50
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage*1.4), h.team)
                for e in enemies:
                    if e != h.target and math.hypot(e.x-h.target.x, e.y-h.target.y) <= 60:
                        e.take_damage(int(h.skill_damage*0.7), h.team)

        def _cast_e_malzareth_poison(self, h, enemies):
            h.active_skill = 'e'; h.active_skill_timer = 45
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage*1.1), h.team)
                if hasattr(h.target, 'apply_slow'):
                    h.target.apply_slow(0.5, 180)

        def _cast_r_malzareth_disillusion(self, h, enemies):
            h.active_skill = 'r'; h.active_skill_timer = 90
            for e in enemies:
                if math.hypot(e.x-h.x, e.y-h.y) <= 200:
                    e.take_damage(int(h.skill_damage*2.0), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 90)
            heal = int(h.max_hp * 0.10); h.hp = min(h.max_hp, h.hp + heal)

        # ═══════════════════════════════════════
        # AKASHARI skills (Level 7 Mini Boss)
        # ═══════════════════════════════════════

        def _cast_q_akashari_strike(self, h, enemies):
            h.active_skill = 'q'; h.active_skill_timer = 50
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage*1.6), h.team)
                if hasattr(h.target, 'apply_slow'):
                    h.target.apply_slow(0.4, 120)

        def _cast_w_akashari_blink(self, h, enemies):
            h.active_skill = 'w'; h.active_skill_timer = 55
            if h.target and h.target.alive:
                dx = h.target.x-h.x; dy = h.target.y-h.y; dist = math.hypot(dx,dy)
                if dist > 0:
                    h.x += (dx/dist)*min(dist, 150); h.y += (dy/dist)*min(dist, 150)
                for e in enemies:
                    if math.hypot(e.x-h.x, e.y-h.y) <= 80:
                        e.take_damage(int(h.skill_damage*1.3), h.team)
            heal = int(h.max_hp * 0.08); h.hp = min(h.max_hp, h.hp + heal)

        def _cast_e_akashari_scream(self, h, enemies):
            h.active_skill = 'e'; h.active_skill_timer = 60
            for e in enemies:
                if math.hypot(e.x-h.x, e.y-h.y) <= 150:
                    e.take_damage(int(h.skill_damage*1.5), h.team)

        def _cast_r_akashari_sonic(self, h, enemies):
            h.active_skill = 'r'; h.active_skill_timer = 90
            for e in enemies:
                if math.hypot(e.x-h.x, e.y-h.y) <= 220:
                    e.take_damage(int(h.skill_damage*2.3), h.team)
                    if hasattr(e, 'apply_slow'):
                        e.apply_slow(0.5, 240)
            heal = int(h.max_hp * 0.10); h.hp = min(h.max_hp, h.hp + heal)

        # ═══════════════════════════════════════
        # VORENMARR skills (Level 7 Mini Boss)
        # ═══════════════════════════════════════

        def _cast_q_vorenmarr_bonds(self, h, enemies):
            h.active_skill = 'q'; h.active_skill_timer = 70
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage*1.3), h.team)
                for e in enemies:
                    if e != h.target and math.hypot(e.x-h.target.x, e.y-h.target.y) <= 80:
                        e.take_damage(int(h.skill_damage*0.6), h.team)

        def _cast_w_vorenmarr_power(self, h):
            h.active_skill = 'w'; h.active_skill_timer = 70
            heal = int(h.max_hp * 0.14); h.hp = min(h.max_hp, h.hp + heal)

        def _cast_e_vorenmarr_upheaval(self, h, enemies):
            h.active_skill = 'e'; h.active_skill_timer = 80
            if h.target and h.target.alive:
                tx, ty = h.target.x, h.target.y
            else:
                tx, ty = h.x, h.y
            for e in enemies:
                if math.hypot(e.x-tx, e.y-ty) <= 120:
                    e.take_damage(int(h.skill_damage*1.8), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 60)

        def _cast_r_vorenmarr_golem(self, h, enemies):
            h.active_skill = 'r'; h.active_skill_timer = 100
            for e in enemies:
                if math.hypot(e.x-h.x, e.y-h.y) <= 200:
                    e.take_damage(int(h.skill_damage*2.2), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 90)
            heal = int(h.max_hp * 0.12); h.hp = min(h.max_hp, h.hp + heal)

        # ═══════════════════════════════════════════════════════
        # LEVEL 9 BOSSES skills
        # ═══════════════════════════════════════════════════════

        # ── KENSHIRO ──
        def _cast_q_kenshiro_swiftslash(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 35
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.2), h.team)

        def _cast_w_kenshiro_assault(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 45
            if h.target and h.target.alive:
                dx = h.target.x - h.x
                dy = h.target.y - h.y
                d = math.hypot(dx, dy)
                if d > 1:
                    step = min(d, 90)
                    h.x += dx / d * step
                    h.y += dy / d * step
                    h.facing = 1 if dx > 0 else -1
                h.target.take_damage(int(h.skill_damage * 1.4), h.team)

        def _cast_e_kenshiro_gale(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 150:
                    e.take_damage(int(h.skill_damage * 1.1), h.team)

        def _cast_r_kenshiro_supremacy(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 70
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 190:
                    e.take_damage(int(h.skill_damage * 1.8), h.team)

        # ── KHAZAN ──
        def _cast_q_khazan_chained(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.3), h.team)

        def _cast_w_khazan_leap(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 50
            if h.target and h.target.alive:
                dx = h.target.x - h.x
                dy = h.target.y - h.y
                d = math.hypot(dx, dy)
                if d > 1:
                    step = min(d, 110)
                    h.x += dx / d * step
                    h.y += dy / d * step
                    h.facing = 1 if dx > 0 else -1
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 90:
                    e.take_damage(int(h.skill_damage * 1.2), h.team)

        def _cast_e_khazan_spin(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 60
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 160:
                    e.take_damage(int(h.skill_damage * 1.1), h.team)

        def _cast_r_khazan_vanish(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 75
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 210:
                    e.take_damage(int(h.skill_damage * 1.9), h.team)
            heal = int(h.max_hp * 0.08)
            h.hp = min(h.max_hp, h.hp + heal)

        # ── WIRO ──
        def _cast_q_wiro_windcut(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 30
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.2), h.team)

        def _cast_w_wiro_whirl(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 45
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 140:
                    e.take_damage(int(h.skill_damage * 1.1), h.team)

        def _cast_e_wiro_dash(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                dx = h.target.x - h.x
                dy = h.target.y - h.y
                d = math.hypot(dx, dy)
                if d > 1:
                    step = min(d, 100)
                    h.x += dx / d * step
                    h.y += dy / d * step
                    h.facing = 1 if dx > 0 else -1
                h.target.take_damage(int(h.skill_damage * 1.1), h.team)

        def _cast_r_wiro_typhoon(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 80
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 200:
                    e.take_damage(int(h.skill_damage * 1.8), h.team)
                    if hasattr(e, 'apply_slow'):
                        e.apply_slow(0.5, 90)

        # ── NARAKA ──
        def _cast_q_naraka_chaos(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.3), h.team)

        def _cast_w_naraka_shadowstep(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 50
            if h.target and h.target.alive:
                dx = h.target.x - h.x
                dy = h.target.y - h.y
                d = math.hypot(dx, dy)
                if d > 1:
                    step = min(d, 120)
                    h.x += dx / d * step
                    h.y += dy / d * step
                    h.facing = 1 if dx > 0 else -1
                h.target.take_damage(int(h.skill_damage * 1.3), h.team)

        def _cast_e_naraka_hammer(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 60
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 180:
                    e.take_damage(int(h.skill_damage * 1.1), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 30)

        def _cast_r_naraka_execution(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 90
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 230:
                    dmg = int(h.skill_damage * 1.8)
                    # Execute bonus untuk target HP rendah
                    if e.hp / max(1, e.max_hp) < 0.3:
                        dmg = int(dmg * 1.6)
                    e.take_damage(dmg, h.team)
            heal = int(h.max_hp * 0.1)
            h.hp = min(h.max_hp, h.hp + heal)

        # ═══════════════════════════════════════════════════════
        # LEVEL 10 BOSSES skills
        # ═══════════════════════════════════════════════════════

        # ── KROGNARR (stone golem) ──
        def _cast_q_krognarr_strike(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.3), h.team)

        def _cast_w_krognarr_seismic(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 170:
                    e.take_damage(int(h.skill_damage * 1.1), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 30)

        def _cast_e_krognarr_rampart(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 65
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 120:
                    e.take_damage(int(h.skill_damage * 0.9), h.team)
            heal = int(h.max_hp * 0.08)
            h.hp = min(h.max_hp, h.hp + heal)

        def _cast_r_krognarr_eruption(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 85
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 210:
                    e.take_damage(int(h.skill_damage * 1.8), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 60)

        # ── RAZ (fire monk) ──
        def _cast_q_raz_overdrive(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 35
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.2), h.team)

        def _cast_w_raz_searing(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 45
            if h.target and h.target.alive:
                dx = h.target.x - h.x
                dy = h.target.y - h.y
                d = math.hypot(dx, dy)
                if d > 1:
                    step = min(d, 100)
                    h.x += dx / d * step
                    h.y += dy / d * step
                    h.facing = 1 if dx > 0 else -1
                h.target.take_damage(int(h.skill_damage * 1.4), h.team)

        def _cast_e_raz_surge(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 160:
                    e.take_damage(int(h.skill_damage * 1.1), h.team)

        def _cast_r_raz_gloom(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 80
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 200:
                    e.take_damage(int(h.skill_damage * 1.8), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 50)

        # ── VRASKHAN (shadow assassin) ──
        def _cast_q_vraskhan_thorned(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 35
            if h.target and h.target.alive:
                dx = h.target.x - h.x
                dy = h.target.y - h.y
                d = math.hypot(dx, dy)
                if d > 1:
                    step = min(d, 90)
                    h.x += dx / d * step
                    h.y += dy / d * step
                    h.facing = 1 if dx > 0 else -1
                h.target.take_damage(int(h.skill_damage * 1.2), h.team)

        def _cast_w_vraskhan_leap(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                h.x = float(h.target.x)
                h.y = float(h.target.y - 20)
                h.facing = 1 if h.target.x > h.x else -1
                h.target.take_damage(int(h.skill_damage * 1.3), h.team)

        def _cast_e_vraskhan_deathslash(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 170:
                    e.take_damage(int(h.skill_damage * 1.1), h.team)

        def _cast_r_vraskhan_omni(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 85
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 220:
                    e.take_damage(int(h.skill_damage * 1.8), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 60)

        # ── AURETHZAR (true boss - solar archer) ──
        def _cast_q_aurethzar_marksman(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.3), h.team)

        def _cast_w_aurethzar_piercing(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 200:
                    e.take_damage(int(h.skill_damage * 1.1), h.team)

        def _cast_e_aurethzar_frost(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 45
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.0), h.team)
                if hasattr(h.target, 'apply_slow'):
                    h.target.apply_slow(0.5, 90)

        def _cast_r_aurethzar_thunder(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 95
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 250:
                    e.take_damage(int(h.skill_damage * 1.9), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 70)

        # ═══════════════════════════════════════════════════════
        # LEVEL 11 BOSSES skills
        # ═══════════════════════════════════════════════════════

        # ── AERALITH (wind ranger) ──
        def _cast_q_aeralith_tailwind(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 35
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.2), h.team)

        def _cast_w_aeralith_windblade(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 45
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 190:
                    e.take_damage(int(h.skill_damage * 1.1), h.team)

        def _cast_e_aeralith_vacuum(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 55
            for e in enemies:
                d = math.hypot(e.x - h.x, e.y - h.y)
                if d <= 170:
                    e.take_damage(int(h.skill_damage * 1.1), h.team)
                    if hasattr(e, 'apply_slow'):
                        e.apply_slow(0.5, 90)

        def _cast_r_aeralith_skyrider(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 80
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 240:
                    e.take_damage(int(h.skill_damage * 1.8), h.team)

        # ── AUREX (omega knight) ──
        def _cast_q_aurex_shieldcrash(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 35
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.3), h.team)

        def _cast_w_aurex_voltblast(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.4), h.team)

        def _cast_e_aurex_aegis(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 65
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 130:
                    e.take_damage(int(h.skill_damage * 0.9), h.team)
            heal = int(h.max_hp * 0.1)
            h.hp = min(h.max_hp, h.hp + heal)

        def _cast_r_aurex_spin(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 75
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 210:
                    e.take_damage(int(h.skill_damage * 1.8), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 60)

        # ── NYXAREVA (fallen queen) ──
        def _cast_q_nyxareva_darkslash(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 35
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.2), h.team)

        def _cast_w_nyxareva_mortalwound(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 45
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.4), h.team)
                if hasattr(h.target, 'apply_slow'):
                    h.target.apply_slow(0.5, 90)

        def _cast_e_nyxareva_sacrifice(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 170:
                    e.take_damage(int(h.skill_damage * 1.1), h.team)

        def _cast_r_nyxareva_avatar(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 85
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 220:
                    e.take_damage(int(h.skill_damage * 1.8), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 60)

        # ── THALAKRYON (true boss - abyssal sovereign) ──
        def _cast_q_thalakryon_bolt(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.3), h.team)

        def _cast_w_thalakryon_aquashield(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 150:
                    e.take_damage(int(h.skill_damage * 0.8), h.team)
            heal = int(h.max_hp * 0.12)
            h.hp = min(h.max_hp, h.hp + heal)

        def _cast_e_thalakryon_tidalrage(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 60
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 190:
                    e.take_damage(int(h.skill_damage * 1.2), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 40)

        def _cast_r_thalakryon_metamorph(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 95
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 260:
                    e.take_damage(int(h.skill_damage * 2.0), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 75)
            heal = int(h.max_hp * 0.1)
            h.hp = min(h.max_hp, h.hp + heal)

        # ═══════════════════════════════════════════════════════
        # LEVEL 12 BOSSES skills
        # ═══════════════════════════════════════════════════════

        # ── AURELIX (time sovereign) ──
        def _cast_q_aurelix_timebomb(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.2), h.team)

        def _cast_w_aurelix_will(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 60
            heal = int(h.max_hp * 0.12)
            h.hp = min(h.max_hp, h.hp + heal)

        def _cast_e_aurelix_shockwave(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 170:
                    e.take_damage(int(h.skill_damage * 1.1), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 40)

        def _cast_r_aurelix_transcend(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 85
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 240:
                    e.take_damage(int(h.skill_damage * 1.8), h.team)
                    if hasattr(e, 'apply_slow'):
                        e.apply_slow(0.5, 90)

        # ── AURELYSSA (golden blade dancer) ──
        def _cast_q_aurelyssa_whirlwind(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 35
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 140:
                    e.take_damage(int(h.skill_damage * 1.1), h.team)

        def _cast_w_aurelyssa_sweep(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 45
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 160:
                    e.take_damage(int(h.skill_damage * 1.2), h.team)

        def _cast_e_aurelyssa_wings(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 55
            if h.target and h.target.alive:
                dx = h.target.x - h.x
                dy = h.target.y - h.y
                d = math.hypot(dx, dy)
                if d > 1:
                    step = min(d, 100)
                    h.x += dx / d * step
                    h.y += dy / d * step
                    h.facing = 1 if dx > 0 else -1
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 120:
                    e.take_damage(int(h.skill_damage * 1.1), h.team)

        def _cast_r_aurelyssa_phantom(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 80
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 220:
                    e.take_damage(int(h.skill_damage * 1.8), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 60)

        # ── VARGRATH (demonic warlord) ──
        def _cast_q_vargrath_bloodthirst(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 35
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.2), h.team)

        def _cast_w_vargrath_charge(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 45
            if h.target and h.target.alive:
                dx = h.target.x - h.x
                dy = h.target.y - h.y
                d = math.hypot(dx, dy)
                if d > 1:
                    step = min(d, 110)
                    h.x += dx / d * step
                    h.y += dy / d * step
                    h.facing = 1 if dx > 0 else -1
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 100:
                    e.take_damage(int(h.skill_damage * 1.2), h.team)

        def _cast_e_vargrath_devilstrike(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 170:
                    e.take_damage(int(h.skill_damage * 1.1), h.team)

        def _cast_r_vargrath_souldom(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 85
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 230:
                    e.take_damage(int(h.skill_damage * 1.8), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 60)

        # ── NAZULMOR (true boss - deepborn herald) ──
        def _cast_q_nazulmor_typhoon(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 190:
                    e.take_damage(int(h.skill_damage * 1.1), h.team)

        def _cast_w_nazulmor_aquashield(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 150:
                    e.take_damage(int(h.skill_damage * 0.8), h.team)
            heal = int(h.max_hp * 0.12)
            h.hp = min(h.max_hp, h.hp + heal)

        def _cast_e_nazulmor_tidalrage(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 60
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 200:
                    e.take_damage(int(h.skill_damage * 1.2), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 40)

        def _cast_r_nazulmor_chaotic(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 95
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 270:
                    e.take_damage(int(h.skill_damage * 2.0), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 75)
            heal = int(h.max_hp * 0.1)
            h.hp = min(h.max_hp, h.hp + heal)

        # ═══════════════════════════════════════════════════════
        # LEVEL 13 BOSSES skills
        # ═══════════════════════════════════════════════════════

        # ── KAELDRIS (warrior commander) ──
        def _cast_q_kaeldris_overwhelming(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 35
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.2), h.team)

        def _cast_w_kaeldris_press(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 45
            if h.target and h.target.alive:
                dx = h.target.x - h.x
                dy = h.target.y - h.y
                d = math.hypot(dx, dy)
                if d > 1:
                    step = min(d, 110)
                    h.x += dx / d * step
                    h.y += dy / d * step
                    h.facing = 1 if dx > 0 else -1
                h.target.take_damage(int(h.skill_damage * 1.3), h.team)

        def _cast_e_kaeldris_moment(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 170:
                    e.take_damage(int(h.skill_damage * 1.1), h.team)

        def _cast_r_kaeldris_duel(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 80
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 220:
                    e.take_damage(int(h.skill_damage * 1.8), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 60)

        # ── PYRAKLOS (spartan champion) ──
        def _cast_q_pyraklos_spearmars(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 35
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.3), h.team)

        def _cast_w_pyraklos_rebuke(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 170:
                    e.take_damage(int(h.skill_damage * 1.1), h.team)

        def _cast_e_pyraklos_bulwark(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 65
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 130:
                    e.take_damage(int(h.skill_damage * 0.7), h.team)
            heal = int(h.max_hp * 0.12)
            h.hp = min(h.max_hp, h.hp + heal)

        def _cast_r_pyraklos_arena(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 85
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 230:
                    e.take_damage(int(h.skill_damage * 1.8), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 60)

        # ── VELMYRTH (phantom assassin) ──
        def _cast_q_velmyrth_dagger(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 35
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.2), h.team)
                if hasattr(h.target, 'apply_slow'):
                    h.target.apply_slow(0.5, 90)

        def _cast_w_velmyrth_strike(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                h.x = float(h.target.x)
                h.y = float(h.target.y - 20)
                h.facing = 1 if h.target.x > h.x else -1
                h.target.take_damage(int(h.skill_damage * 1.3), h.team)

        def _cast_e_velmyrth_blur(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 170:
                    e.take_damage(int(h.skill_damage * 1.1), h.team)

        def _cast_r_velmyrth_coup(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 80
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 220:
                    dmg = int(h.skill_damage * 1.8)
                    # Execute bonus untuk target HP rendah
                    if e.hp / max(1, e.max_hp) < 0.3:
                        dmg = int(dmg * 1.6)
                    e.take_damage(dmg, h.team)

        # ── SOLVARIN (true boss - holy paladin warden) ──
        def _cast_q_solvarin_purification(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.3), h.team)

        def _cast_w_solvarin_repel(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 180:
                    e.take_damage(int(h.skill_damage * 1.2), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 40)

        def _cast_e_solvarin_degen(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 60
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 200:
                    e.take_damage(int(h.skill_damage * 0.9), h.team)
                    if hasattr(e, 'apply_slow'):
                        e.apply_slow(0.4, 90)

        def _cast_r_solvarin_guardian(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 95
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 280:
                    e.take_damage(int(h.skill_damage * 2.0), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 75)
            heal = int(h.max_hp * 0.12)
            h.hp = min(h.max_hp, h.hp + heal)

        # ── AZURETH (arcane sky-scribe) ──
        def _cast_q_azureth_arcanebolt(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.2), h.team)

        def _cast_w_azureth_concussive(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 170:
                    e.take_damage(int(h.skill_damage * 1.15), h.team)

        def _cast_e_azureth_ancientseal(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 60
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 200:
                    e.take_damage(int(h.skill_damage * 1.0), h.team)
                    if hasattr(e, 'apply_slow'):
                        e.apply_slow(0.5, 100)

        def _cast_r_azureth_mysticflare(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 85
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 240:
                    e.take_damage(int(h.skill_damage * 1.9), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 65)

        # ── LUMINAR (eternal custodian) ──
        def _cast_q_luminar_illuminate(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.2), h.team)

        def _cast_w_luminar_blindinglight(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 190:
                    e.take_damage(int(h.skill_damage * 1.15), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 45)

        def _cast_e_luminar_wisp(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 60
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 205:
                    e.take_damage(int(h.skill_damage * 1.0), h.team)

        def _cast_r_luminar_spiritform(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 90
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 280:
                    e.take_damage(int(h.skill_damage * 1.95), h.team)
            heal = int(h.max_hp * 0.15)
            h.hp = min(h.max_hp, h.hp + heal)

        # ── SOLARA (dawnforged sentinel) ──
        def _cast_q_solara_starbreaker(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.25), h.team)

        def _cast_w_solara_celestialhammer(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 185:
                    e.take_damage(int(h.skill_damage * 1.15), h.team)

        def _cast_e_solara_luminosity(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 60
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 195:
                    e.take_damage(int(h.skill_damage * 0.95), h.team)
            heal = int(h.max_hp * 0.1)
            h.hp = min(h.max_hp, h.hp + heal)

        def _cast_r_solara_solarguardian(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 90
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 240:
                    e.take_damage(int(h.skill_damage * 1.9), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 70)

        # ── PYRAETHIS (true boss - eternal firebird) ──
        def _cast_q_pyraethis_icarusdive(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 45
            if h.target and h.target.alive:
                dmg = int(h.skill_damage * 1.3)
                if h.target.hp / max(1, h.target.max_hp) < 0.3:
                    dmg = int(dmg * 1.5)
                h.target.take_damage(dmg, h.team)

        def _cast_w_pyraethis_firespirits(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 200:
                    e.take_damage(int(h.skill_damage * 1.2), h.team)

        def _cast_e_pyraethis_sunray(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 65
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 220:
                    e.take_damage(int(h.skill_damage * 1.05), h.team)
                    if hasattr(e, 'apply_slow'):
                        e.apply_slow(0.35, 90)

        def _cast_r_pyraethis_supernova(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 95
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 300:
                    e.take_damage(int(h.skill_damage * 2.1), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 80)
            heal = int(h.max_hp * 0.12)
            h.hp = min(h.max_hp, h.hp + heal)

        # ── AUROTH (celestial bastion) ──
        def _cast_q_auroth_ionicedge(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.25), h.team)

        def _cast_w_auroth_ward(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 60
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 185:
                    e.take_damage(int(h.skill_damage * 1.1), h.team)
            heal = int(h.max_hp * 0.1)
            h.hp = min(h.max_hp, h.hp + heal)

        def _cast_e_auroth_consecration(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 60
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 195:
                    e.take_damage(int(h.skill_damage * 1.0), h.team)
                    if hasattr(e, 'apply_slow'):
                        e.apply_slow(0.4, 90)

        def _cast_r_auroth_guardian(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 90
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 240:
                    e.take_damage(int(h.skill_damage * 1.9), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 70)

        # ── MORVEIN (phantom lancer) ──
        def _cast_q_morvein_puncture(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                dmg = int(h.skill_damage * 1.3)
                if h.target.hp / max(1, h.target.max_hp) < 0.3:
                    dmg = int(dmg * 1.5)
                h.target.take_damage(dmg, h.team)

        def _cast_w_morvein_violentstrike(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 190:
                    e.take_damage(int(h.skill_damage * 1.2), h.team)

        def _cast_e_morvein_spectralcharge(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 60
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 205:
                    e.take_damage(int(h.skill_damage * 1.05), h.team)

        def _cast_r_morvein_phantomform(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 90
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 250:
                    e.take_damage(int(h.skill_damage * 1.95), h.team)
            heal = int(h.max_hp * 0.12)
            h.hp = min(h.max_hp, h.hp + heal)

        # ── THORVAK (ancient grovewarden) ──
        def _cast_q_thorvak_seed(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.2), h.team)
                if hasattr(h.target, 'apply_slow'):
                    h.target.apply_slow(0.4, 90)

        def _cast_w_thorvak_natureswrath(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 195:
                    e.take_damage(int(h.skill_damage * 1.15), h.team)

        def _cast_e_thorvak_vengeance(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 60
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 200:
                    e.take_damage(int(h.skill_damage * 1.0), h.team)

        def _cast_r_thorvak_dryad(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 90
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 250:
                    e.take_damage(int(h.skill_damage * 1.9), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 70)
            heal = int(h.max_hp * 0.1)
            h.hp = min(h.max_hp, h.hp + heal)

        # ── YAMAKO (true boss - primordial woodshaper) ──
        def _cast_q_yamako_deepforest(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 45
            if h.target and h.target.alive:
                dmg = int(h.skill_damage * 1.3)
                if h.target.hp / max(1, h.target.max_hp) < 0.3:
                    dmg = int(dmg * 1.4)
                h.target.take_damage(dmg, h.team)

        def _cast_w_yamako_woodcreation(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 205:
                    e.take_damage(int(h.skill_damage * 1.15), h.team)

        def _cast_e_yamako_woodgolem(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 65
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 220:
                    e.take_damage(int(h.skill_damage * 1.0), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 50)

        def _cast_r_yamako_kannon(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 95
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 300:
                    e.take_damage(int(h.skill_damage * 2.1), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 80)
            heal = int(h.max_hp * 0.12)
            h.hp = min(h.max_hp, h.hp + heal)

        # ── IGNIRUS (infernal pyromancer) ──
        def _cast_q_ignirus_searingtorrent(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.2), h.team)

        def _cast_w_ignirus_flameshot(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 195:
                    e.take_damage(int(h.skill_damage * 1.15), h.team)

        def _cast_e_ignirus_burstfireball(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 65
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 210:
                    e.take_damage(int(h.skill_damage * 1.0), h.team)
                    if hasattr(e, 'apply_slow'):
                        e.apply_slow(0.35, 90)

        def _cast_r_ignirus_vengeance(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 90
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 280:
                    e.take_damage(int(h.skill_damage * 1.95), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 70)

        # ── LEORIC (lionheart guardian) ──
        def _cast_q_leoric_fearlesscharge(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                dx = h.target.x - h.x
                dy = h.target.y - h.y
                d = math.hypot(dx, dy)
                if d > 1:
                    step = min(d, 100)
                    h.x += dx / d * step
                    h.y += dy / d * step
                    h.facing = 1 if dx > 0 else -1
                h.target.take_damage(int(h.skill_damage * 1.25), h.team)

        def _cast_w_leoric_sacredhammer(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 190:
                    e.take_damage(int(h.skill_damage * 1.15), h.team)

        def _cast_e_leoric_concealblast(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 60
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 200:
                    e.take_damage(int(h.skill_damage * 1.0), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 50)

        def _cast_r_leoric_immortality(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 95
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 250:
                    e.take_damage(int(h.skill_damage * 1.9), h.team)
            heal = int(h.max_hp * 0.2)
            h.hp = min(h.max_hp, h.hp + heal)

        # ── SHIROTAKA (tideborn tactician) ──
        def _cast_q_shirotaka_hiraishin(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                h.x = float(h.target.x)
                h.y = float(h.target.y - 20)
                h.facing = 1 if h.target.x > h.x else -1
                dmg = int(h.skill_damage * 1.3)
                if h.target.hp / max(1, h.target.max_hp) < 0.3:
                    dmg = int(dmg * 1.5)
                h.target.take_damage(dmg, h.team)

        def _cast_w_shirotaka_waterboundary(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 190:
                    e.take_damage(int(h.skill_damage * 1.15), h.team)
                    if hasattr(e, 'apply_slow'):
                        e.apply_slow(0.5, 90)

        def _cast_e_shirotaka_shadowclones(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 60
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 205:
                    e.take_damage(int(h.skill_damage * 1.0), h.team)

        def _cast_r_shirotaka_paperbomb(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 90
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 250:
                    e.take_damage(int(h.skill_damage * 1.95), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 70)

        # ── SEIRYUKONG (true boss - celestial simian) ──
        def _cast_q_seiryukong_boundless(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 45
            if h.target and h.target.alive:
                dmg = int(h.skill_damage * 1.3)
                if h.target.hp / max(1, h.target.max_hp) < 0.3:
                    dmg = int(dmg * 1.4)
                h.target.take_damage(dmg, h.team)

        def _cast_w_seiryukong_treedance(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 205:
                    e.take_damage(int(h.skill_damage * 1.2), h.team)

        def _cast_e_seiryukong_jingusoldiers(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 65
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 220:
                    e.take_damage(int(h.skill_damage * 1.0), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 55)

        def _cast_r_seiryukong_wukong(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 95
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 300:
                    e.take_damage(int(h.skill_damage * 2.15), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 80)
            heal = int(h.max_hp * 0.12)
            h.hp = min(h.max_hp, h.hp + heal)

        # ── KAELTHORN (azure vanguard) ──
        def _cast_q_kaelthorn_bravestfighter(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                dx = h.target.x - h.x
                dy = h.target.y - h.y
                d = math.hypot(dx, dy)
                if d > 1:
                    step = min(d, 110)
                    h.x += dx / d * step
                    h.y += dy / d * step
                    h.facing = 1 if dx > 0 else -1
                h.target.take_damage(int(h.skill_damage * 1.25), h.team)

        def _cast_w_kaelthorn_justiceblade(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 190:
                    e.take_damage(int(h.skill_damage * 1.15), h.team)

        def _cast_e_kaelthorn_defendersassault(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 60
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 205:
                    e.take_damage(int(h.skill_damage * 1.0), h.team)

        def _cast_r_kaelthorn_chivalryfists(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 90
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 250:
                    e.take_damage(int(h.skill_damage * 1.9), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 70)

        # ── SOLVANTH (radiant guardian) ──
        def _cast_q_solvanth_ringpunishment(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.25), h.team)

        def _cast_w_solvanth_gloriouspathway(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 195:
                    e.take_damage(int(h.skill_damage * 1.15), h.team)
                    if hasattr(e, 'apply_slow'):
                        e.apply_slow(0.4, 90)

        def _cast_e_solvanth_laworder(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 60
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 210:
                    e.take_damage(int(h.skill_damage * 1.0), h.team)

        def _cast_r_solvanth_wrath(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 90
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 260:
                    e.take_damage(int(h.skill_damage * 1.95), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 70)

        # ── XYRAEL (cyan wraith) ──
        def _cast_q_xyrael_finch(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                h.x = float(h.target.x)
                h.y = float(h.target.y - 20)
                h.facing = 1 if h.target.x > h.x else -1
                dmg = int(h.skill_damage * 1.3)
                if h.target.hp / max(1, h.target.max_hp) < 0.3:
                    dmg = int(dmg * 1.5)
                h.target.take_damage(dmg, h.team)

        def _cast_w_xyrael_defiant(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 190:
                    e.take_damage(int(h.skill_damage * 1.15), h.team)

        def _cast_e_xyrael_tempest(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 60
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 205:
                    e.take_damage(int(h.skill_damage * 1.0), h.team)

        def _cast_r_xyrael_lightness(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 90
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 250:
                    e.take_damage(int(h.skill_damage * 1.95), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 75)

        # ── NYXARETH (true boss - cosmic sovereign) ──
        # Renderer nyxareth pakai key skill "1"-"4", jadi cast method
        # menyetel active_skill ke "1"-"4" supaya FX-nya muncul.
        def _cast_q_nyxareth_starsplit(self, h, enemies):
            h.active_skill = '1'
            h.active_skill_timer = 45
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.3), h.team)

        def _cast_w_nyxareth_realworld(self, h, enemies):
            h.active_skill = '2'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 205:
                    e.take_damage(int(h.skill_damage * 1.2), h.team)

        def _cast_e_nyxareth_spacetime(self, h, enemies):
            h.active_skill = '3'
            h.active_skill_timer = 65
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 220:
                    e.take_damage(int(h.skill_damage * 1.05), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 55)

        def _cast_r_nyxareth_astrorealm(self, h, enemies):
            h.active_skill = '4'
            h.active_skill_timer = 95
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 300:
                    e.take_damage(int(h.skill_damage * 2.2), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 80)
            heal = int(h.max_hp * 0.12)
            h.hp = min(h.max_hp, h.hp + heal)

        # ── CRYSSALIA (glacial empress) ──
        def _cast_q_cryssalia_frostshock(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.25), h.team)

        def _cast_w_cryssalia_bitterfrost(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 200:
                    e.take_damage(int(h.skill_damage * 1.15), h.team)
                    if hasattr(e, 'apply_slow'):
                        e.apply_slow(0.5, 90)

        def _cast_e_cryssalia_frostbites(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 65
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 215:
                    e.take_damage(int(h.skill_damage * 1.0), h.team)

        def _cast_r_cryssalia_coldest(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 90
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 280:
                    e.take_damage(int(h.skill_damage * 1.95), h.team)
                    if hasattr(e, 'apply_slow'):
                        e.apply_slow(0.5, 120)

        # ── KAELTHAR (storm fist) ──
        def _cast_q_kaelthar_chargingfist(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                dx = h.target.x - h.x
                dy = h.target.y - h.y
                d = math.hypot(dx, dy)
                if d > 1:
                    step = min(d, 110)
                    h.x += dx / d * step
                    h.y += dy / d * step
                    h.facing = 1 if dx > 0 else -1
                h.target.take_damage(int(h.skill_damage * 1.3), h.team)

        def _cast_w_kaelthar_quake(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 190:
                    e.take_damage(int(h.skill_damage * 1.2), h.team)

        def _cast_e_kaelthar_fistcrack(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 60
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 200:
                    e.take_damage(int(h.skill_damage * 1.05), h.team)

        def _cast_r_kaelthar_fistbreak(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 90
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 250:
                    e.take_damage(int(h.skill_damage * 2.0), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 75)

        # ── MORKHAERA (blood-feather witch) ──
        def _cast_q_morkhaera_spiritburst(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.25), h.team)

        def _cast_w_morkhaera_airstrike(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 200:
                    e.take_damage(int(h.skill_damage * 1.15), h.team)

        def _cast_e_morkhaera_energyimpact(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 65
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 215:
                    e.take_damage(int(h.skill_damage * 1.0), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 55)

        def _cast_r_morkhaera_ethereal(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 90
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 280:
                    e.take_damage(int(h.skill_damage * 1.95), h.team)
            heal = int(h.max_hp * 0.12)
            h.hp = min(h.max_hp, h.hp + heal)

        # ── AURELION (true boss - golden sovereign) ──
        def _cast_q_aurelion_callcourage(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 45
            if h.target and h.target.alive:
                dmg = int(h.skill_damage * 1.3)
                if h.target.hp / max(1, h.target.max_hp) < 0.3:
                    dmg = int(dmg * 1.4)
                h.target.take_damage(dmg, h.team)

        def _cast_w_aurelion_guardianassault(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 210:
                    e.take_damage(int(h.skill_damage * 1.2), h.team)

        def _cast_e_aurelion_kingscommand(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 65
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 225:
                    e.take_damage(int(h.skill_damage * 1.0), h.team)
                    if hasattr(e, 'apply_slow'):
                        e.apply_slow(0.35, 90)

        def _cast_r_aurelion_kingssummon(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 95
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 300:
                    e.take_damage(int(h.skill_damage * 2.2), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 80)
            heal = int(h.max_hp * 0.12)
            h.hp = min(h.max_hp, h.hp + heal)

        # ── AKAHIME (scarlet blossom) ──
        def _cast_q_akahime_petalbarrage(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.25), h.team)

        def _cast_w_akahime_soulscroll(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 195:
                    e.take_damage(int(h.skill_damage * 1.15), h.team)
                    if hasattr(e, 'apply_slow'):
                        e.apply_slow(0.4, 90)

        def _cast_e_akahime_shadow(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 65
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 210:
                    e.take_damage(int(h.skill_damage * 1.0), h.team)

        def _cast_r_akahime_higanbana(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 90
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 270:
                    e.take_damage(int(h.skill_damage * 1.95), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 70)

        # ── NYXTHRAEL (cursed executioner) ──
        def _cast_q_nyxthrael_ambush(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                dmg = int(h.skill_damage * 1.3)
                if h.target.hp / max(1, h.target.max_hp) < 0.3:
                    dmg = int(dmg * 1.5)
                h.target.take_damage(dmg, h.team)

        def _cast_w_nyxthrael_nightfall(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 195:
                    e.take_damage(int(h.skill_damage * 1.15), h.team)

        def _cast_e_nyxthrael_darknightfall(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 60
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 210:
                    e.take_damage(int(h.skill_damage * 1.0), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 55)

        def _cast_r_nyxthrael_shadowbringer(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 90
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 260:
                    e.take_damage(int(h.skill_damage * 1.95), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 75)

        # ── SYLVANTHEROS (verdant farseer) ──
        def _cast_q_sylvantheros_sprout(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.2), h.team)
                if hasattr(h.target, 'apply_slow'):
                    h.target.apply_slow(0.4, 90)

        def _cast_w_sylvantheros_teleport(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 200:
                    e.take_damage(int(h.skill_damage * 1.15), h.team)

        def _cast_e_sylvantheros_treants(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 65
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 215:
                    e.take_damage(int(h.skill_damage * 1.0), h.team)

        def _cast_r_sylvantheros_wrath(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 90
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 280:
                    e.take_damage(int(h.skill_damage * 1.95), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 70)

        # ── VAELINDRA (true boss - violet sovereign) ──
        def _cast_q_vaelindra_energywave(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 45
            if h.target and h.target.alive:
                dmg = int(h.skill_damage * 1.3)
                if h.target.hp / max(1, h.target.max_hp) < 0.3:
                    dmg = int(dmg * 1.4)
                h.target.take_damage(dmg, h.team)

        def _cast_w_vaelindra_spacering(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 215:
                    e.take_damage(int(h.skill_damage * 1.2), h.team)

        def _cast_e_vaelindra_violetrequiem(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 65
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 230:
                    e.take_damage(int(h.skill_damage * 1.05), h.team)
                    if hasattr(e, 'apply_slow'):
                        e.apply_slow(0.35, 90)

        def _cast_r_vaelindra_realm(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 95
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 310:
                    e.take_damage(int(h.skill_damage * 2.25), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 80)
            heal = int(h.max_hp * 0.12)
            h.hp = min(h.max_hp, h.hp + heal)

        # ── ASTRAELION (starlight swordmaster) ──
        def _cast_q_astraelion_swordfall(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                dmg = int(h.skill_damage * 1.3)
                if h.target.hp / max(1, h.target.max_hp) < 0.3:
                    dmg = int(dmg * 1.5)
                h.target.take_damage(dmg, h.team)

        def _cast_w_astraelion_spiritblade(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 195:
                    e.take_damage(int(h.skill_damage * 1.15), h.team)

        def _cast_e_astraelion_forceescape(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 60
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 205:
                    e.take_damage(int(h.skill_damage * 1.0), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 55)

        def _cast_r_astraelion_zeroreturn(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 90
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 260:
                    e.take_damage(int(h.skill_damage * 1.95), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 75)

        # ── MORVAENTHIR (soul reaper) ──
        def _cast_q_morvaenthir_soulfragment(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.25), h.team)

        def _cast_w_morvaenthir_spiritbind(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 205:
                    e.take_damage(int(h.skill_damage * 1.15), h.team)
                    if hasattr(e, 'apply_slow'):
                        e.apply_slow(0.5, 100)

        def _cast_e_morvaenthir_essence(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 65
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 220:
                    e.take_damage(int(h.skill_damage * 1.0), h.team)

        def _cast_r_morvaenthir_shadowrealm(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 90
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 290:
                    e.take_damage(int(h.skill_damage * 1.95), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 75)

        # ── THORNVAEGRIM (twisted elderwood) ──
        def _cast_q_thornvaegrim_bramble(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 40
            if h.target and h.target.alive:
                h.target.take_damage(int(h.skill_damage * 1.25), h.team)
                if hasattr(h.target, 'apply_slow'):
                    h.target.apply_slow(0.4, 90)

        def _cast_w_thornvaegrim_twistedadvance(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 200:
                    e.take_damage(int(h.skill_damage * 1.15), h.team)

        def _cast_e_thornvaegrim_saplingthrow(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 60
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 215:
                    e.take_damage(int(h.skill_damage * 1.0), h.team)

        def _cast_r_thornvaegrim_grasp(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 90
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 270:
                    e.take_damage(int(h.skill_damage * 1.95), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 70)

        # ── MORTHRAXIS (true boss - crimson sovereign) ──
        def _cast_q_morthraxis_batimpale(self, h, enemies):
            h.active_skill = 'q'
            h.active_skill_timer = 45
            if h.target and h.target.alive:
                dmg = int(h.skill_damage * 1.3)
                if h.target.hp / max(1, h.target.max_hp) < 0.3:
                    dmg = int(dmg * 1.4)
                h.target.take_damage(dmg, h.team)

        def _cast_w_morthraxis_sanguine(self, h, enemies):
            h.active_skill = 'w'
            h.active_skill_timer = 55
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 210:
                    e.take_damage(int(h.skill_damage * 1.2), h.team)
            heal = int(h.max_hp * 0.08)
            h.hp = min(h.max_hp, h.hp + heal)

        def _cast_e_morthraxis_phantommob(self, h, enemies):
            h.active_skill = 'e'
            h.active_skill_timer = 65
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 225:
                    e.take_damage(int(h.skill_damage * 1.05), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 55)

        def _cast_r_morthraxis_baleful(self, h, enemies):
            h.active_skill = 'r'
            h.active_skill_timer = 95
            for e in enemies:
                if math.hypot(e.x - h.x, e.y - h.y) <= 310:
                    e.take_damage(int(h.skill_damage * 2.25), h.team)
                    if hasattr(e, 'attack_timer'):
                        e.attack_timer = max(e.attack_timer, 80)
            heal = int(h.max_hp * 0.15)
            h.hp = min(h.max_hp, h.hp + heal)

# ====================================================================
# grimjaw_skills.py
# ====================================================================
class _NS_grimjaw_skills:
    """Namespace grimjaw_skills - isi asli tidak diubah."""

    # ================================
    # hero_skills/grimjaw_skills.py
    # Grimjaw (Juggernaut - Blade Fury) skill logic
    # ================================



    class GrimjawSkills(BaseSkill):
        """
        Skills untuk Grimjaw - Juggernaut / The Blade Fury

        Skill Set:
        - Q: Blade Fury (spin AOE damage 3 detik)
        - W: Healing Ward (drop totem heal area)
        - E: Critical Strike (buff next attacks 2x damage + cone)
        - R: Omnislash (lock target + multi-hit strikes)
        """

        # Durasi animasi skill, dicocokkan dengan pembagi
        # `1 - timer / N` di renderer.
        # heroes/grimjaw.py: healing_ward_ground 90 (L1365).
        # Q Blade Fury & R Omnislash pakai `phase`, bukan progress,
        # jadi durasi disamakan dengan durasi gameplay-nya.
        SKILL_VISUAL_DURATION = {"q": 180, "w": 90, "e": 60, "r": 90}

        def init_state(self):
            """Init state variables khusus Grimjaw"""
            h = self.hero

            # Q - Blade Fury (spin)
            h._blade_fury_active = False
            h._blade_fury_timer = 0

            # W - Healing Ward
            h._heal_ward_active = False
            h._heal_ward_timer = 0
            h._heal_ward_pos = (0, 0)

            # R - Omnislash Ultimate
            h._omnislash_active = False
            h._omnislash_timer = 0
            h._omnislash_target = None

            # E - Critical Strike buff
            h._crit_buff_active = False
            h._crit_buff_timer = 0

            # Legacy (tidak dipakai lagi tapi safety)
            h._rage_active = False
            h._rage_timer = 0
            h._war_cry_timer = 0

        def update_timers(self, all_units, all_towers, all_bases):
            """Update Grimjaw-specific timers per frame"""
            h = self.hero

            # ═══ BLADE FURY SPIN (Q) - deal damage per tick ═══
            if h._blade_fury_timer > 0:
                h._blade_fury_timer -= 1
                # Deal damage setiap 15 frames
                if h._blade_fury_timer % 15 == 0:
                    enemies = self._get_enemies(
                        all_units, all_towers, all_bases)
                    # Radius spin diambil dari data hero (single
                    # source of truth, sejajar guard auto-cast).
                    spin_range = h.skill_data.get("skill_range", 80)
                    for e in enemies:
                        dist = math.hypot(e.x - h.x, e.y - h.y)
                        if dist <= spin_range:
                            e.take_damage(h.skill_damage, h.team,
                                          source=h)
                if h._blade_fury_timer <= 0:
                    h._blade_fury_active = False

            # ═══ HEALING WARD (W) - heal Grimjaw + allies dekat ward ═══
            if h._heal_ward_timer > 0:
                h._heal_ward_timer -= 1

                # Heal Grimjaw kalau dekat ward
                dist_ward = math.hypot(
                    h.x - h._heal_ward_pos[0],
                    h.y - h._heal_ward_pos[1])
                if dist_ward <= 100 and h.hp < h.max_hp:
                    h.hp = min(h.max_hp, h.hp + 2)

                # Heal allies juga
                for u in all_units:
                    if u.team == h.team and u.alive and u != h:
                        d = math.hypot(
                            u.x - h._heal_ward_pos[0],
                            u.y - h._heal_ward_pos[1])
                        if d <= 100 and hasattr(u, 'hp'):
                            u.hp = min(u.max_hp, u.hp + 1)

                if h._heal_ward_timer <= 0:
                    h._heal_ward_active = False

            # ═══ OMNISLASH ULTIMATE (R) - multi-hit strikes ═══
            if h._omnislash_timer > 0:
                h._omnislash_timer -= 1
                # Deal damage setiap 8 frames
                if h._omnislash_timer % 8 == 0:
                    if h._omnislash_target and h._omnislash_target.alive:
                        h._omnislash_target.take_damage(
                            int(h.skill_damage * 0.6),
                            h.team, source=h)
                if h._omnislash_timer <= 0:
                    h._omnislash_active = False
                    h._omnislash_target = None

            # ═══ CRITICAL STRIKE BUFF (E) - buff active ═══
            if h._crit_buff_timer > 0:
                h._crit_buff_timer -= 1
                if h._crit_buff_timer <= 0:
                    h._crit_buff_active = False

        # ═══════════════════════════════════════
        # Q - BLADE FURY (Spin damage AOE)
        # ═══════════════════════════════════════

        def cast_q(self, all_units, all_towers, all_bases):
            """Q - Blade Fury (spin 3 detik)"""
            if not self._check_q_cooldown():
                return False

            # Jangan buang skill ke tempat kosong: kalau tidak ada
            # musuh terjangkau, batalkan dan cooldown tidak terbakar.
            if not self._has_target(all_units, all_towers,
                                    all_bases):
                return False

            self.hero._blade_fury_active = True
            self.hero._blade_fury_timer = 180  # 3 detik

            self._trigger_q_cooldown(shake_amount=8)
            return True

        # ═══════════════════════════════════════
        # W - HEALING WARD (Drop totem)
        # ═══════════════════════════════════════

        def cast_w(self, all_units, all_towers, all_bases):
            """W - Healing Ward (drop heal totem)"""
            if not self._check_w_cooldown():
                return False

            h = self.hero
            h._heal_ward_active = True
            h._heal_ward_timer = 360  # 6 detik
            h._heal_ward_pos = (h.x, h.y)

            # Instant heal
            h.hp = min(h.max_hp, h.hp + 30)

            self._trigger_w_cooldown(shake_amount=5)
            return True

        # ═══════════════════════════════════════
        # E - CRITICAL STRIKE (Buff + cone damage)
        # ═══════════════════════════════════════

        def cast_e(self, all_units, all_towers, all_bases):
            """E - Critical Strike (buff next attacks 2x)"""
            if not self._check_e_cooldown():
                return False

            # Jangan buang skill ke tempat kosong: kalau tidak ada
            # musuh terjangkau, batalkan dan cooldown tidak terbakar.
            if not self._has_target(all_units, all_towers,
                                    all_bases):
                return False

            h = self.hero
            h._crit_buff_active = True
            h._crit_buff_timer = 300  # 5 detik untuk pakai

            # Instant cone damage
            self._deal_aoe_damage(
                all_units, all_towers, all_bases,
                range_val=60,
                damage_multiplier=1.5)

            self._trigger_e_cooldown(shake_amount=6)
            return True

        # ═══════════════════════════════════════
        # R - OMNISLASH ULTIMATE
        # ═══════════════════════════════════════

        def cast_r(self, all_units, all_towers, all_bases):
            """R - Omnislash (lock target + multi-hit)"""
            if not self._check_r_cooldown():
                return False

            # Jangan buang skill ke tempat kosong: kalau tidak ada
            # musuh terjangkau, batalkan dan cooldown tidak terbakar.
            if not self._has_target(all_units, all_towers,
                                    all_bases):
                return False

            h = self.hero

            if h.target and h.target.alive:
                # Locked target
                h._omnislash_active = True
                h._omnislash_timer = 90  # 1.5 detik
                h._omnislash_target = h.target

                # Immediate big damage
                h.target.take_damage(
                    int(h.skill_damage * 2.5), h.team)
            else:
                # Fallback: AOE
                self._deal_aoe_damage(
                    all_units, all_towers, all_bases,
                    range_val=150,
                    damage_multiplier=2.0)
                h._omnislash_active = True
                h._omnislash_timer = 90

            self._trigger_r_cooldown(shake_amount=15)
            return True

# ====================================================================
# kaizen_skills.py
# ====================================================================
class _NS_kaizen_skills:
    """Namespace kaizen_skills - isi asli tidak diubah."""

    # ================================
    # hero_skills/kaizen_skills.py
    # Kaizen (Wind Blade Assassin) skill logic
    # ================================



    class KaizenSkills(BaseSkill):
        """
        Skills untuk Kaizen - Wind Blade Assassin

        Skill Set:
        - Q: Steel Wind → Dash Strike (alternating combo)
        - W: Wind Wall (block projectiles)
        - E: Sweep (AOE jump attack)
        - R: Tornado Ultimate (massive AOE)
        """

        # Durasi animasi skill, dicocokkan dengan pembagi
        # `1 - timer / N` di renderer.
        # heroes/kaizen.py: dash 60 (L1358) / wind_wall 90 (L1400)
        #                   sweep 60 (L1471) / tornado 100 (L1524)
        SKILL_VISUAL_DURATION = {"q": 60, "w": 90, "e": 60, "r": 100}

        def init_state(self):
            """Init state variables khusus Kaizen"""
            h = self.hero
            h._q_stack = 0
            h._q_reset_timer = 0
            h._is_dashing = False
            h._dash_timer = 0
            h._wind_wall_timer = 0
            h._ulti_active = False
            h._ulti_timer = 0

        def update_timers(self, all_units, all_towers, all_bases):
            """Update Kaizen-specific timers per frame"""
            h = self.hero

            # Q combo reset timer
            if h._q_reset_timer > 0:
                h._q_reset_timer -= 1
                if h._q_reset_timer <= 0:
                    h._q_stack = 0

            # Dash timer
            if h._dash_timer > 0:
                h._dash_timer -= 1
                if h._dash_timer <= 0:
                    h._is_dashing = False

            # Wind Wall timer
            if h._wind_wall_timer > 0:
                h._wind_wall_timer -= 1

            # Ultimate timer
            if h._ulti_timer > 0:
                h._ulti_timer -= 1
                if h._ulti_timer <= 0:
                    h._ulti_active = False

        # ═══════════════════════════════════════
        # Q - STEEL WIND / DASH STRIKE (Alternating)
        # ═══════════════════════════════════════

        def cast_q(self, all_units, all_towers, all_bases):
            """Q - Alternating Steel Wind → Dash Strike"""
            if not self._check_q_cooldown():
                return False

            # Jangan buang skill ke tempat kosong: kalau tidak ada
            # musuh terjangkau, batalkan dan cooldown tidak terbakar.
            if not self._has_target(all_units, all_towers,
                                    all_bases):
                return False

            h = self.hero
            h._q_reset_timer = 180  # 3 detik untuk combo

            if h._q_stack == 0:
                # Q1: Steel Wind (basic AOE)
                self._cast_steel_wind(all_units, all_towers, all_bases)
                h._q_stack = 1
            else:
                # Q2: Dash Strike
                self._cast_dash_strike(all_units, all_towers, all_bases)
                h._q_stack = 0

            self._trigger_q_cooldown(shake_amount=8)
            return True

        def _cast_steel_wind(self, all_units, all_towers, all_bases):
            """Q1 - Steel Wind (basic AOE slash)"""
            skill_range = self.hero.skill_data["skill_range"]
            self._deal_aoe_damage(
                all_units, all_towers, all_bases,
                range_val=skill_range,
                damage_multiplier=1.0)

        def _cast_dash_strike(self, all_units, all_towers, all_bases):
            """Q2 - Dash Strike (dash + damage)"""
            h = self.hero
            if not h.target:
                return

            dx = h.target.x - h.x
            dy = h.target.y - h.y
            dist = math.hypot(dx, dy)

            if dist > 0:
                # Dash ke target
                h.x += dx * 0.7
                h.y += dy * 0.7

                # Trigger dash animation
                h._is_dashing = True
                h._dash_timer = 15

                # Damage all enemies dalam path
                self._deal_aoe_damage(
                    all_units, all_towers, all_bases,
                    range_val=80,
                    damage_multiplier=1.5)

        # ═══════════════════════════════════════
        # W - WIND WALL
        # ═══════════════════════════════════════

        def cast_w(self, all_units, all_towers, all_bases):
            """W - Wind Wall (block projectiles 3 detik)"""
            if not self._check_w_cooldown():
                return False

            self.hero._wind_wall_timer = 180
            self._trigger_w_cooldown(shake_amount=5)
            return True

        # ═══════════════════════════════════════
        # E - SWEEP
        # ═══════════════════════════════════════

        def cast_e(self, all_units, all_towers, all_bases):
            """E - Sweep (AOE jump attack)"""
            if not self._check_e_cooldown():
                return False

            # Jangan buang skill ke tempat kosong: kalau tidak ada
            # musuh terjangkau, batalkan dan cooldown tidak terbakar.
            if not self._has_target(all_units, all_towers,
                                    all_bases):
                return False

            self._deal_aoe_damage(
                all_units, all_towers, all_bases,
                range_val=100,
                damage_multiplier=1.0)

            self._trigger_e_cooldown(shake_amount=6)
            return True

        # ═══════════════════════════════════════
        # R - TORNADO ULTIMATE
        # ═══════════════════════════════════════

        def cast_r(self, all_units, all_towers, all_bases):
            """R - Tornado Ultimate (massive AOE)"""
            if not self._check_r_cooldown():
                return False

            # Jangan buang skill ke tempat kosong: kalau tidak ada
            # musuh terjangkau, batalkan dan cooldown tidak terbakar.
            if not self._has_target(all_units, all_towers,
                                    all_bases):
                return False

            h = self.hero
            h._ulti_active = True
            h._ulti_timer = 90

            self._deal_aoe_damage(
                all_units, all_towers, all_bases,
                range_val=150,
                damage_multiplier=2.0)

            self._trigger_r_cooldown(shake_amount=15)
            return True

# ====================================================================
# sylara_skills.py
# ====================================================================
class _NS_sylara_skills:
    """Namespace sylara_skills - isi asli tidak diubah."""

    # ================================
    # hero_skills/sylara_skills.py
    # Sylara (Wind Ranger - Wind's Arrow) skill logic
    # ================================



    class SylaraSkills(BaseSkill):
        """
        Skills untuk Sylara - Wind Ranger / The Wind's Arrow

        Skill Set:
        - Q: Focus Fire (attack speed buff + piercing shot)
        - W: Windrun (speed boost + heal)
        - E: Shackle Shot (bind target + damage per tick + stun)
        - R: Powershot (charge → release 5-arrow cone)
        """

        # Efek channel/bind harus terlihat selama status gameplay aktif.
        # Q Focus Fire = 3 dtk dan E Shackle = 2.5 dtk; R tetap memakai
        # 1 dtk charge agar panah dilepas tepat pada akhir animasi.
        SKILL_VISUAL_DURATION = {"q": 180, "w": 180, "e": 150, "r": 60}

        def init_state(self):
            """Init state variables khusus Sylara"""
            h = self.hero

            # Q - Focus Fire buff
            h._focus_fire_active = False
            h._focus_fire_timer = 0

            # W - Windrun (speed + evasion)
            h._windrun_active = False
            h._windrun_timer = 0
            h._original_speed = h.speed

            # E - Shackle Shot (chain enemies)
            h._shackle_active = False
            h._shackle_timer = 0
            h._shackle_target = None

            # R - Powershot (charge system)
            h._powershot_charging = False
            h._powershot_timer = 0

        def update_timers(self, all_units, all_towers, all_bases):
            """Update Sylara-specific timers per frame"""
            h = self.hero

            # ═══ FOCUS FIRE (Q) - attack speed boost ═══
            if h._focus_fire_timer > 0:
                h._focus_fire_timer -= 1
                if h._focus_fire_timer <= 0:
                    h._focus_fire_active = False
                    # Reset attack cooldown
                    stats = HERO_TYPES[h.hero_type]
                    h.attack_cooldown = stats["attack_cooldown"]

            # ═══ WINDRUN (W) - speed boost ═══
            if h._windrun_timer > 0:
                h._windrun_timer -= 1
                if h._windrun_timer <= 0:
                    h._windrun_active = False
                    # Reset speed
                    h.speed = h._original_speed

            # ═══ SHACKLE SHOT (E) - chain damage per tick ═══
            if h._shackle_timer > 0:
                h._shackle_timer -= 1

                if h._shackle_target and h._shackle_target.alive:
                    # Damage tick setiap 15 frames
                    if h._shackle_timer % 15 == 0:
                        h._shackle_target.take_damage(
                            int(h.skill_damage * 0.4), h.team)
                        # Stun
                        if hasattr(h._shackle_target, 'attack_timer'):
                            h._shackle_target.attack_timer = 30
                else:
                    # Target mati, batalkan
                    h._shackle_active = False
                    h._shackle_target = None

                if h._shackle_timer <= 0:
                    h._shackle_active = False
                    h._shackle_target = None

            # ═══ POWERSHOT (R) - charging phase ═══
            if h._powershot_timer > 0:
                h._powershot_timer -= 1
                if h._powershot_timer <= 0:
                    # RELEASE powershot!
                    h._powershot_charging = False
                    self._release_powershot(
                        all_units, all_towers, all_bases)

        # ═══════════════════════════════════════
        # Q - FOCUS FIRE (Attack speed buff + piercing)
        # ═══════════════════════════════════════

        def cast_q(self, all_units, all_towers, all_bases):
            """Q - Focus Fire (attack speed buff + piercing shot)"""
            if not self._check_q_cooldown():
                return False

            # Jangan buang skill ke tempat kosong: kalau tidak ada
            # musuh terjangkau, batalkan dan cooldown tidak terbakar.
            if not self._has_target(all_units, all_towers,
                                    all_bases):
                return False

            h = self.hero

            # Activate buff (3 detik)
            h._focus_fire_active = True
            h._focus_fire_timer = 180

            # Boost attack speed 1.7x
            h.attack_cooldown = max(20,
                                     int(h.attack_cooldown / 1.7))

            # Volley visual dibuat oleh renderer Sylara selama channel.
            # Tidak spawn projectile generik di awal, supaya satu Focus
            # Fire tidak menghasilkan panah duplikat.

            # Piercing damage (single line)
            if h.target:
                dx = h.target.x - h.x
                dy = h.target.y - h.y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    dx /= dist
                    dy /= dist

                    skill_range = h.skill_data["skill_range"]
                    enemies = self._get_enemies(
                        all_units, all_towers, all_bases)

                    # Damage all enemies dalam line dengan falloff
                    hit_count = 0
                    for e in enemies:
                        ex = e.x - h.x
                        ey = e.y - h.y
                        proj = ex * dx + ey * dy
                        if 0 < proj < skill_range:
                            perp_dist = abs(ex * (-dy) + ey * dx)
                            if perp_dist < 15:
                                # Damage falloff per hit
                                damage_falloff = max(0.5,
                                                      1.0 - hit_count * 0.15)
                                e.take_damage(
                                    int(h.skill_damage * damage_falloff),
                                    h.team)
                                hit_count += 1

            self._trigger_q_cooldown(shake_amount=8)
            return True

        # ═══════════════════════════════════════
        # W - WINDRUN (Speed + heal)
        # ═══════════════════════════════════════

        def cast_w(self, all_units, all_towers, all_bases):
            """W - Windrun (2x speed + heal 3 detik)"""
            if not self._check_w_cooldown():
                return False

            h = self.hero
            h._windrun_active = True
            h._windrun_timer = 180  # 3 detik
            h._original_speed = h.speed
            h.speed *= 2.0

            # Heal moderate
            if hasattr(h, 'hp'):
                h.hp = min(h.max_hp, h.hp + 30)

            self._trigger_w_cooldown(shake_amount=5)
            return True

        # ═══════════════════════════════════════
        # E - SHACKLE SHOT (Bind + stun + damage)
        # ═══════════════════════════════════════

        def cast_e(self, all_units, all_towers, all_bases):
            """E - Shackle Shot (bind target for 2.5 detik)"""
            if not self._check_e_cooldown():
                return False

            # Jangan buang skill ke tempat kosong: kalau tidak ada
            # musuh terjangkau, batalkan dan cooldown tidak terbakar.
            if not self._has_target(all_units, all_towers,
                                    all_bases):
                return False

            h = self.hero

            # Range check
            shackle_range = 200

            target = None

            # Cek target manual dulu
            if h.target and h.target.alive:
                dist = math.hypot(h.target.x - h.x, h.target.y - h.y)
                if dist <= shackle_range:
                    target = h.target

            # Fallback: nearest enemy dalam range
            if not target:
                enemies = self._get_enemies(all_units, all_towers, all_bases)
                nearest_dist = shackle_range
                for e in enemies:
                    dist = math.hypot(e.x - h.x, e.y - h.y)
                    if dist < nearest_dist:
                        target = e
                        nearest_dist = dist

            # Apply shackle
            if target:
                h._shackle_active = True
                h._shackle_timer = 150  # 2.5 detik
                h._shackle_target = target

                # Initial damage
                target.take_damage(
                    int(h.skill_damage * 0.7), h.team)

                # Initial stun
                self._apply_stun(target, 45)

                self._trigger_e_cooldown(shake_amount=6)
                return True
            else:
                # No target found, don't consume cooldown
                return False

        # ═══════════════════════════════════════
        # R - POWERSHOT (Charge → release cone)
        # ═══════════════════════════════════════

        def cast_r(self, all_units, all_towers, all_bases):
            """R - Powershot (charge 1 detik → release cone)"""
            if not self._check_r_cooldown():
                return False

            # Jangan buang skill ke tempat kosong: kalau tidak ada
            # musuh terjangkau, batalkan dan cooldown tidak terbakar.
            if not self._has_target(all_units, all_towers,
                                    all_bases):
                return False

            h = self.hero
            h._powershot_charging = True
            h._powershot_timer = 60  # 1 detik charge

            self._trigger_r_cooldown(shake_amount=15)
            return True

        def _release_powershot(self, all_units, all_towers, all_bases):
            """Release powershot - multi-arrow cone attack"""
            h = self.hero
            enemies = self._get_enemies(all_units, all_towers, all_bases)

            # Get target direction
            if h.target and h.target.alive:
                dx = h.target.x - h.x
                dy = h.target.y - h.y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    dx /= dist
                    dy /= dist
                else:
                    dx, dy = h.facing, 0
            else:
                dx, dy = h.facing, 0

            # 5 arrows dalam cone 30°, range 300
            num_arrows = 5
            cone_angle = math.pi / 6  # 30° (dulu 45° - terlalu lebar)
            max_range = 300

            # Track enemies hit (avoid double-count)
            hit_enemies = set()

            for arrow_i in range(num_arrows):
                spread = (arrow_i / (num_arrows - 1) - 0.5) * cone_angle
                base_angle = math.atan2(dy, dx)
                arrow_angle = base_angle + spread

                arrow_dx = math.cos(arrow_angle)
                arrow_dy = math.sin(arrow_angle)

                for e in enemies:
                    if id(e) in hit_enemies:
                        continue

                    ex = e.x - h.x
                    ey = e.y - h.y
                    proj = ex * arrow_dx + ey * arrow_dy
                    if 0 < proj < max_range:
                        perp_dist = abs(ex * (-arrow_dy) + ey * arrow_dx)
                        if perp_dist < 20:
                            # Damage berkurang dengan jarak
                            distance_falloff = max(0.6,
                                                    1.0 - (proj / max_range) * 0.4)
                            damage = int(h.skill_damage * 1.0 * distance_falloff)
                            e.take_damage(damage, h.team)
                            hit_enemies.add(id(e))
                            # Visual: projectile homing terarah ke musuh
                            # kena (via sistem generic _entity.py).
                            h._spawn_skill_projectile(e, speed=13.0)

# ====================================================================
# thorne_skills.py
# ====================================================================
class _NS_thorne_skills:
    """Namespace thorne_skills - isi asli tidak diubah."""

    # ================================
    # hero_skills/thorne_skills.py
    # Thorne (Bristleback) skill logic
    # ================================



    class ThorneSkills(BaseSkill):
        """
        Skills untuk Thorne - Bristleback / The Quill Sprayer

        Skill Set:
        - Q: Viscous Nose (goop spray - slow + damage)
        - W: Bristleback (defensive buff - reflect damage)
        - E: Quill Spray (radial quill AOE damage)
        - R: Warpath (rage - attack speed & damage buff)
        """

        # Durasi animasi skill, dicocokkan dengan pembagi
        # `1 - timer / N` di renderer.
        # heroes/thorne.py: viscous 40 (L1449) / bristleback 100 (L1490)
        #                   quill_spray 60 (L1536) / warpath 120 (L1569)
        SKILL_VISUAL_DURATION = {"q": 40, "w": 100, "e": 60, "r": 120}

        def init_state(self):
            """Init state variables khusus Thorne"""
            h = self.hero

            # Q - Viscous Nose (goop spray)
            h._viscous_nose_active = False
            h._viscous_nose_timer = 0

            # W - Bristleback buff (defensive)
            h._bristleback_active = False
            h._bristleback_timer = 0

            # E - Quill Spray (visual only, damage instant)
            h._spraying_quills = False
            h._spray_timer = 0

            # R - Warpath ultimate
            h._warpath_active = False
            h._warpath_timer = 0
            h._original_damage = h.damage
            h._original_attack_cd = h.attack_cooldown

            # Legacy (safety)
            h._fortify_active = False
            h._fortify_timer = 0
            h._holy_shield_active = False
            h._holy_shield_timer = 0

        def update_timers(self, all_units, all_towers, all_bases):
            """Update Thorne-specific timers per frame"""
            h = self.hero

            # ═══ VISCOUS NOSE (Q) - visual + slow duration ═══
            if h._viscous_nose_timer > 0:
                h._viscous_nose_timer -= 1
                if h._viscous_nose_timer <= 0:
                    h._viscous_nose_active = False

            # ═══ BRISTLEBACK (W) - buff duration ═══
            if h._bristleback_timer > 0:
                h._bristleback_timer -= 1
                if h._bristleback_timer <= 0:
                    h._bristleback_active = False

            # ═══ QUILL SPRAY visual timer ═══
            if h._spray_timer > 0:
                h._spray_timer -= 1
                if h._spray_timer <= 0:
                    h._spraying_quills = False

            # ═══ WARPATH (R) - rage buff ═══
            if h._warpath_timer > 0:
                h._warpath_timer -= 1
                if h._warpath_timer <= 0:
                    h._warpath_active = False
                    # Reset damage dari data level SEKARANG (bukan
                    # snapshot _original_damage): kalau hero di-upgrade
                    # saat buff aktif, bonus upgrade tidak hilang.
                    # attack_cooldown tidak diskalakan per level, jadi
                    # snapshot awal tetap benar.
                    _lvl = HERO_LEVELS.get(h.level)
                    if _lvl:
                        h.damage = int(
                            h.base_damage * _lvl["dmg_mult"])
                    h.attack_cooldown = h._original_attack_cd

        # ═══════════════════════════════════════
        # Q - VISCOUS NOSE (Goop spray)
        # ═══════════════════════════════════════

        def cast_q(self, all_units, all_towers, all_bases):
            """Q - Viscous Nose (goop cone spray)"""
            if not self._check_q_cooldown():
                return False

            # Jangan buang skill ke tempat kosong: kalau tidak ada
            # musuh terjangkau, batalkan dan cooldown tidak terbakar.
            if not self._has_target(all_units, all_towers,
                                    all_bases):
                return False

            h = self.hero
            h._viscous_nose_active = True
            h._viscous_nose_timer = 30  # visual 0.5 detik

            # Cone attack di depan
            cone_length = 60
            cone_width = math.pi / 3  # 60°

            enemies = self._get_enemies(all_units, all_towers, all_bases)
            for e in enemies:
                dx = e.x - h.x
                dy = e.y - h.y
                dist = math.hypot(dx, dy)

                if dist > cone_length:
                    continue

                # Check if in cone (in front)
                enemy_angle = math.atan2(dy, dx)
                facing_angle = 0 if h.facing > 0 else math.pi

                angle_diff = abs(enemy_angle - facing_angle)
                if angle_diff > math.pi:
                    angle_diff = 2 * math.pi - angle_diff

                if angle_diff < cone_width / 2:
                    # Damage
                    e.take_damage(int(h.skill_damage * 0.8), h.team)
                    # Slow effect (goop)
                    self._apply_slow(e, 0.4, 180)

            self._trigger_q_cooldown(shake_amount=6)
            return True

        # ═══════════════════════════════════════
        # W - BRISTLEBACK (Defensive buff)
        # ═══════════════════════════════════════

        def cast_w(self, all_units, all_towers, all_bases):
            """W - Bristleback (armor buff + reflect damage 4 detik)"""
            if not self._check_w_cooldown():
                return False

            h = self.hero
            h._bristleback_active = True
            h._bristleback_timer = 240  # 4 detik

            # Instant AOE damage (spikes push out)
            self._deal_aoe_damage(
                all_units, all_towers, all_bases,
                range_val=60,
                damage_multiplier=0.5)

            # Small heal
            if hasattr(h, 'hp'):
                h.hp = min(h.max_hp, h.hp + 20)

            self._trigger_w_cooldown(shake_amount=5)
            return True

        # ═══════════════════════════════════════
        # E - QUILL SPRAY (Radial AOE)
        # ═══════════════════════════════════════

        def cast_e(self, all_units, all_towers, all_bases):
            """E - Quill Spray (radial AOE damage)"""
            if not self._check_e_cooldown():
                return False

            # Jangan buang skill ke tempat kosong: kalau tidak ada
            # musuh terjangkau, batalkan dan cooldown tidak terbakar.
            if not self._has_target(all_units, all_towers,
                                    all_bases):
                return False

            h = self.hero
            h._spraying_quills = True
            h._spray_timer = 30  # visual

            # Radial AOE (360 degrees)
            self._deal_aoe_damage(
                all_units, all_towers, all_bases,
                range_val=100,
                damage_multiplier=1.2)

            self._trigger_e_cooldown(shake_amount=8)
            return True

        # ═══════════════════════════════════════
        # R - WARPATH (Rage buff)
        # ═══════════════════════════════════════

        def cast_r(self, all_units, all_towers, all_bases):
            """R - Warpath (rage: 1.5x damage + 1.5x attack speed 5 detik)"""
            if not self._check_r_cooldown():
                return False

            # Jangan buang skill ke tempat kosong: kalau tidak ada
            # musuh terjangkau, batalkan dan cooldown tidak terbakar.
            if not self._has_target(all_units, all_towers,
                                    all_bases):
                return False

            h = self.hero
            h._warpath_active = True
            h._warpath_timer = 300  # 5 detik

            # Save original stats
            h._original_damage = h.damage
            h._original_attack_cd = h.attack_cooldown

            # Buff stats
            h.damage = int(h.damage * 1.5)
            h.attack_cooldown = max(15, int(h.attack_cooldown / 1.5))

            # Instant AOE damage
            self._deal_aoe_damage(
                all_units, all_towers, all_bases,
                range_val=120,
                damage_multiplier=1.5)

            # Small heal
            if hasattr(h, 'hp'):
                h.hp = min(h.max_hp, h.hp + 50)

            self._trigger_r_cooldown(shake_amount=15)
            return True

# ====================================================================
# vex_skills.py
# ====================================================================
class _NS_vex_skills:
    """Namespace vex_skills - isi asli tidak diubah."""

    # ================================
    # hero_skills/vex_skills.py
    # Vex (Outworld Destroyer) skill logic
    # ================================



    class VexSkills(BaseSkill):
        """
        Skills untuk Vex - Outworld Destroyer / Harbinger of the Void

        Skill Set:
        - Q: Arcane Orb (long-range magic missile)
        - W: Sanity's Eclipse (ground crystal spikes AOE)
        - E: Astral Imprisonment (bubble prison + damage)
        - R: Essence Flux (green void explosion)
        """

        # Durasi animasi skill, dicocokkan dengan pembagi
        # `1 - timer / N` di renderer.
        # heroes/vex.py: arcane_orb 40 (L1342) / sanity_eclipse 100 (L1391/L1410)
        #                essence_flux 80 (L1505/L1530)
        SKILL_VISUAL_DURATION = {"q": 40, "w": 100, "e": 60, "r": 80}

        def init_state(self):
            """Init state variables khusus Vex"""
            h = self.hero

            # Q - Arcane Orb (instant, no state)

            # W - Sanity's Eclipse (crystal spikes)
            h._sanity_eclipse_active = False
            h._sanity_eclipse_timer = 0

            # E - Astral Imprisonment
            h._astral_prison_active = False
            h._astral_prison_timer = 0
            h._astral_prison_target = None

            # R - Essence Flux ultimate
            h._essence_flux_active = False
            h._essence_flux_timer = 0

        def update_timers(self, all_units, all_towers, all_bases):
            """Update Vex-specific timers per frame"""
            h = self.hero

            # ═══ SANITY'S ECLIPSE - damage per tick ═══
            if h._sanity_eclipse_timer > 0:
                h._sanity_eclipse_timer -= 1
                # Damage every 20 frames (3x per second)
                if h._sanity_eclipse_timer % 20 == 0:
                    enemies = self._get_enemies(
                        all_units, all_towers, all_bases)
                    for e in enemies:
                        dist = math.hypot(e.x - h.x, e.y - h.y)
                        if 30 < dist <= 55:  # ring damage
                            e.take_damage(
                                int(h.skill_damage * 0.4), h.team,
                                source=h)
                if h._sanity_eclipse_timer <= 0:
                    h._sanity_eclipse_active = False

            # ═══ ASTRAL IMPRISONMENT - stun + damage ═══
            if h._astral_prison_timer > 0:
                h._astral_prison_timer -= 1

                if h._astral_prison_target and h._astral_prison_target.alive:
                    # Keep target stunned
                    self._apply_stun(h._astral_prison_target, 15)
                    # Damage per tick
                    if h._astral_prison_timer % 10 == 0:
                        h._astral_prison_target.take_damage(
                            int(h.skill_damage * 0.3), h.team,
                            source=h)
                else:
                    h._astral_prison_active = False
                    h._astral_prison_target = None

                if h._astral_prison_timer <= 0:
                    h._astral_prison_active = False
                    h._astral_prison_target = None

            # ═══ ESSENCE FLUX explosion active ═══
            if h._essence_flux_timer > 0:
                h._essence_flux_timer -= 1
                if h._essence_flux_timer <= 0:
                    h._essence_flux_active = False

        # ═══════════════════════════════════════
        # Q - ARCANE ORB (Long-range magic missile)
        # ═══════════════════════════════════════

        def cast_q(self, all_units, all_towers, all_bases):
            """Q - Arcane Orb (deal high damage ke target + line)"""
            if not self._check_q_cooldown():
                return False

            # Jangan buang skill ke tempat kosong: kalau tidak ada
            # musuh terjangkau, batalkan dan cooldown tidak terbakar.
            if not self._has_target(all_units, all_towers,
                                    all_bases):
                return False

            h = self.hero

            if not h.target:
                return False

            # Visual: arcane orb homing terarah ke target (via sistem
            # generic _entity.py; damage=0, cuma visual).
            if getattr(h.target, 'alive', False):
                h._spawn_skill_projectile(h.target, speed=13.0)

            # Big single-target damage
            h.target.take_damage(
                int(h.skill_damage * 1.2), h.team)

            # Bonus: enemies in line antara Vex dan target juga kena
            dx = h.target.x - h.x
            dy = h.target.y - h.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                dx /= dist
                dy /= dist

                enemies = self._get_enemies(all_units, all_towers, all_bases)
                for e in enemies:
                    if e == h.target:
                        continue
                    ex = e.x - h.x
                    ey = e.y - h.y
                    proj = ex * dx + ey * dy
                    if 0 < proj < dist:
                        perp_dist = abs(ex * (-dy) + ey * dx)
                        if perp_dist < 18:
                            e.take_damage(
                                int(h.skill_damage * 0.5), h.team)

            self._trigger_q_cooldown(shake_amount=8)
            return True

        # ═══════════════════════════════════════
        # W - SANITY'S ECLIPSE (Ground crystal spikes)
        # ═══════════════════════════════════════

        def cast_w(self, all_units, all_towers, all_bases):
            """W - Sanity's Eclipse (AOE ground spikes 3 detik)"""
            if not self._check_w_cooldown():
                return False

            # Jangan buang skill ke tempat kosong: kalau tidak ada
            # musuh terjangkau, batalkan dan cooldown tidak terbakar.
            if not self._has_target(all_units, all_towers,
                                    all_bases):
                return False

            h = self.hero
            h._sanity_eclipse_active = True
            h._sanity_eclipse_timer = 180  # 3 detik

            # Instant damage burst
            enemies = self._get_enemies(all_units, all_towers, all_bases)
            for e in enemies:
                dist = math.hypot(e.x - h.x, e.y - h.y)
                if dist <= 60:
                    e.take_damage(
                        int(h.skill_damage * 0.8), h.team)
                    # Slow effect
                    self._apply_slow(e, 0.5, 180)

            self._trigger_w_cooldown(shake_amount=5)
            return True

        # ═══════════════════════════════════════
        # E - ASTRAL IMPRISONMENT (Bubble prison)
        # ═══════════════════════════════════════

        def cast_e(self, all_units, all_towers, all_bases):
            """E - Astral Imprisonment (stun target 2.5 detik + damage)"""
            if not self._check_e_cooldown():
                return False

            # Jangan buang skill ke tempat kosong: kalau tidak ada
            # musuh terjangkau, batalkan dan cooldown tidak terbakar.
            if not self._has_target(all_units, all_towers,
                                    all_bases):
                return False

            h = self.hero

            # Cari target (prioritas: current target, else nearest)
            target = None
            prison_range = 200

            if h.target and h.target.alive:
                dist = math.hypot(h.target.x - h.x, h.target.y - h.y)
                if dist <= prison_range:
                    target = h.target

            if not target:
                enemies = self._get_enemies(all_units, all_towers, all_bases)
                nearest_dist = prison_range
                for e in enemies:
                    dist = math.hypot(e.x - h.x, e.y - h.y)
                    if dist < nearest_dist:
                        target = e
                        nearest_dist = dist

            if target:
                h._astral_prison_active = True
                h._astral_prison_timer = 150  # 2.5 detik
                h._astral_prison_target = target

                # Visual: astral orb homing terarah ke target (via
                # sistem generic _entity.py; damage=0, cuma visual).
                h._spawn_skill_projectile(target, speed=13.0)

                # Initial damage
                target.take_damage(
                    int(h.skill_damage * 0.6), h.team)

                self._trigger_e_cooldown(shake_amount=6)
                return True
            else:
                return False

        # ═══════════════════════════════════════
        # R - ESSENCE FLUX (Void explosion ultimate)
        # ═══════════════════════════════════════

        def cast_r(self, all_units, all_towers, all_bases):
            """R - Essence Flux (massive AOE void explosion)"""
            if not self._check_r_cooldown():
                return False

            # Jangan buang skill ke tempat kosong: kalau tidak ada
            # musuh terjangkau, batalkan dan cooldown tidak terbakar.
            if not self._has_target(all_units, all_towers,
                                    all_bases):
                return False

            h = self.hero
            h._essence_flux_active = True
            h._essence_flux_timer = 60  # 1 detik visual

            # HUGE AOE damage
            self._deal_aoe_damage(
                all_units, all_towers, all_bases,
                range_val=180,
                damage_multiplier=2.5)

            self._trigger_r_cooldown(shake_amount=15)
            return True

# ====================================================================
# zephyr_skills.py
# ====================================================================
class _NS_zephyr_skills:
    """Namespace zephyr_skills - isi asli tidak diubah."""

    # ================================
    # hero_skills/zephyr_skills.py
    # Zephyr (Dark Willow) skill logic
    # ================================



    class ZephyrSkills(BaseSkill):
        """
        Skills untuk Zephyr - Dark Willow / Meander of Mischief

        Skill Set:
        - Q: Bramble Maze (thorn ring trap - damage + slow)
        - W: Shadow Realm (invisibility + heal)
        - E: Casket Curse (skull follows target + damage per tick)
        - R: Bedlam (clones spin around + damage AOE)
        """

        # Visual harus hidup sepanjang status gameplay. Sebelumnya efek
        # lenyap di tengah durasi damage/buff sehingga terasa tidak sinkron.
        # Renderer Zephyr memakai angka yang sama untuk progress 0.0 -> 1.0.
        SKILL_VISUAL_DURATION = {"q": 240, "w": 180, "e": 180, "r": 240}

        def init_state(self):
            """Init state variables khusus Zephyr"""
            h = self.hero

            # Q - Bramble Maze
            h._bramble_active = False
            h._bramble_timer = 0
            # Snapshot titik cast: Bramble adalah perangkap di tanah,
            # jadi tidak ikut bergerak saat target berpindah.
            h._bramble_origin = None

            # W - Shadow Realm (invisibility)
            h._shadow_realm_active = False
            h._shadow_realm_timer = 0

            # E - Casket Curse
            h._curse_active = False
            h._curse_timer = 0
            h._curse_target = None

            # R - Bedlam Ultimate
            h._bedlam_active = False
            h._bedlam_timer = 0

        def update_timers(self, all_units, all_towers, all_bases):
            """Update Zephyr-specific timers per frame"""
            h = self.hero

            # ═══ BRAMBLE MAZE (Q) - damage per tick ═══
            if h._bramble_timer > 0:
                h._bramble_timer -= 1
                # Damage enemies in ring every 20 frames
                if h._bramble_timer % 20 == 0:
                    enemies = self._get_enemies(
                        all_units, all_towers, all_bases)
                    ox, oy = h._bramble_origin or (h.x, h.y)
                    for e in enemies:
                        dist = math.hypot(e.x - ox, e.y - oy)
                        if 40 < dist <= 60:  # ring damage pada lokasi trap
                            e.take_damage(
                                int(h.skill_damage * 0.3), h.team,
                                source=h)
                            self._apply_slow(e, 0.5, 60)
                if h._bramble_timer <= 0:
                    h._bramble_active = False
                    h._bramble_origin = None

            # ═══ SHADOW REALM (W) - invisibility + heal ═══
            if h._shadow_realm_timer > 0:
                h._shadow_realm_timer -= 1
                # Heal per tick
                if h.hp < h.max_hp:
                    h.hp = min(h.max_hp, h.hp + 2)
                if h._shadow_realm_timer <= 0:
                    h._shadow_realm_active = False

            # ═══ CASKET CURSE (E) - skull damage per tick ═══
            if h._curse_timer > 0:
                h._curse_timer -= 1

                if h._curse_target and h._curse_target.alive:
                    # Damage tick setiap 20 frames
                    if h._curse_timer % 20 == 0:
                        h._curse_target.take_damage(
                            int(h.skill_damage * 0.35), h.team,
                            source=h)
                else:
                    h._curse_active = False
                    h._curse_target = None

                if h._curse_timer <= 0:
                    h._curse_active = False
                    h._curse_target = None

            # ═══ BEDLAM (R) - clones damage per tick ═══
            if h._bedlam_timer > 0:
                h._bedlam_timer -= 1
                # AOE damage per tick
                if h._bedlam_timer % 15 == 0:
                    enemies = self._get_enemies(
                        all_units, all_towers, all_bases)
                    for e in enemies:
                        dist = math.hypot(e.x - h.x, e.y - h.y)
                        if dist <= 80:
                            e.take_damage(
                                int(h.skill_damage * 0.5), h.team,
                                source=h)
                if h._bedlam_timer <= 0:
                    h._bedlam_active = False

        # ═══════════════════════════════════════
        # Q - BRAMBLE MAZE (Thorn ring trap)
        # ═══════════════════════════════════════

        def cast_q(self, all_units, all_towers, all_bases):
            """Q - Bramble Maze (thorn ring damage + slow area)"""
            if not self._check_q_cooldown():
                return False

            # Jangan buang skill ke tempat kosong: kalau tidak ada
            # musuh terjangkau, batalkan dan cooldown tidak terbakar.
            if not self._has_target(all_units, all_towers,
                                    all_bases):
                return False

            h = self.hero
            # Kunci posisi target ketika Q ditekan. Ini menyamakan titik
            # duri yang digambar dengan titik damage yang diterapkan.
            target = self._acquire_target(all_units, all_towers, all_bases)
            if target is None:
                return False
            h._bramble_origin = (float(target.x), float(target.y))
            h._bramble_active = True
            h._bramble_timer = 240  # 4 detik

            # Initial damage tepat di pusat perangkap, bukan di tubuh hero.
            ox, oy = h._bramble_origin
            enemies = self._get_enemies(all_units, all_towers, all_bases)
            for e in enemies:
                dist = math.hypot(e.x - ox, e.y - oy)
                if dist <= 60:
                    e.take_damage(
                        int(h.skill_damage * 0.8), h.team)
                    self._apply_slow(e, 0.5, 180)

            self._trigger_q_cooldown(shake_amount=8)
            return True

        # ═══════════════════════════════════════
        # W - SHADOW REALM (Invisibility + heal)
        # ═══════════════════════════════════════

        def cast_w(self, all_units, all_towers, all_bases):
            """W - Shadow Realm (invisibility + heal 3 detik)"""
            if not self._check_w_cooldown():
                return False

            h = self.hero
            h._shadow_realm_active = True
            h._shadow_realm_timer = 180  # 3 detik

            # Instant heal
            if hasattr(h, 'hp'):
                h.hp = min(h.max_hp, h.hp + 40)

            self._trigger_w_cooldown(shake_amount=5)
            return True

        # ═══════════════════════════════════════
        # E - CASKET CURSE (Skull curse mengejar)
        # ═══════════════════════════════════════

        def cast_e(self, all_units, all_towers, all_bases):
            """E - Casket Curse (skull follows target 3 detik)"""
            if not self._check_e_cooldown():
                return False

            # Jangan buang skill ke tempat kosong: kalau tidak ada
            # musuh terjangkau, batalkan dan cooldown tidak terbakar.
            if not self._has_target(all_units, all_towers,
                                    all_bases):
                return False

            h = self.hero

            # Cari target
            target = None
            curse_range = 200

            if h.target and h.target.alive:
                dist = math.hypot(h.target.x - h.x, h.target.y - h.y)
                if dist <= curse_range:
                    target = h.target

            if not target:
                enemies = self._get_enemies(all_units, all_towers, all_bases)
                nearest_dist = curse_range
                for e in enemies:
                    dist = math.hypot(e.x - h.x, e.y - h.y)
                    if dist < nearest_dist:
                        target = e
                        nearest_dist = dist

            if target:
                h._curse_active = True
                h._curse_timer = 180  # 3 detik
                h._curse_target = target

                # Visual CasketProjectile dibuat oleh renderer Zephyr.
                # Jangan spawn projectile generik di sini: sebelumnya dua
                # tengkorak terbang untuk satu cast dan terlihat berantakan.

                # Initial damage
                target.take_damage(
                    int(h.skill_damage * 0.6), h.team)

                self._trigger_e_cooldown(shake_amount=6)
                return True
            else:
                return False

        # ═══════════════════════════════════════
        # R - BEDLAM (Multiple clones ultimate)
        # ═══════════════════════════════════════

        def cast_r(self, all_units, all_towers, all_bases):
            """R - Bedlam (clones spin damage AOE)"""
            if not self._check_r_cooldown():
                return False

            # Jangan buang skill ke tempat kosong: kalau tidak ada
            # musuh terjangkau, batalkan dan cooldown tidak terbakar.
            if not self._has_target(all_units, all_towers,
                                    all_bases):
                return False

            h = self.hero
            h._bedlam_active = True
            h._bedlam_timer = 240  # 4 detik

            # Initial big AOE damage
            self._deal_aoe_damage(
                all_units, all_towers, all_bases,
                range_val=80,
                damage_multiplier=1.8)

            self._trigger_r_cooldown(shake_amount=15)
            return True

