# tactical_commands.py
# Sistem Perintah Taktis: GATHER, PROTECT TOWER, PROTECT CASTLE, ATTACK BOSS
# ================================
# Implementasi untuk player team (blue).
# Semua hero akan merespon sesuai perintah.
#
# MODE HOLD (request user)
# ────────────────────────
# Perintah bisa DITAHAN (tombol panel ditekan terus / tuts keyboard
# ditahan): selama masih di-hold, perintah itu terus aktif - manager
# menerbitkannya ulang setiap 0,5 detik supaya hero terus menaatinya
# (tidak kembali ke AI masing-masing) dan durasi 10 detiknya tidak
# pernah habis. Perintah berhenti ditegakkan begitu hold DILEPAS.
#
# TAP cepat (tekan-lepas < 0,33 detik) berperilaku seperti dulu:
# perintah aktif selama durasi normalnya (10 detik).
#
# API:  hold_start(nama, *args, follow_mouse=False)  -> tekan/tahan
#       hold_end(nama=None)                          -> lepas
# Nama perintah sama dengan konstanta TacticalCommand / action panel:
# "gather", "protect_tower", "protect_castle", "attack_boss",
# "attack_damage_dealer".

import math
import random

try:
    from settings import (
        BLUE_BASE_X, BLUE_BASE_Y, RED_BASE_X, RED_BASE_Y,
        SCREEN_WIDTH, SCREEN_HEIGHT,
    )
except ImportError:
    BLUE_BASE_X = 100
    BLUE_BASE_Y = 620
    RED_BASE_X = 1180
    RED_BASE_Y = 100
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 720

# ── Konstanta mode HOLD ──
HOLD_TAP_MAX_FRAMES = 20       # tahan < 0,33 detik dihitung TAP cepat
HOLD_RELEASE_TAIL = 30         # ekor 0,5 detik setelah hold dilepas
GATHER_PUSH_DELAY_FRAMES = 240  # mulai cek push setelah 4 detik menahan


class TacticalCommand:
    GATHER = "gather"
    PROTECT_TOWER = "protect_tower"
    PROTECT_CASTLE = "protect_castle"
    ATTACK_BOSS = "attack_boss"
    ATTACK_DAMAGE_DEALER = "attack_damage_dealer"


class TacticalCommandManager:
    """
    Mengelola perintah taktis untuk semua hero blue.
    - GATHER: semua hero berkumpul dan menyerang bersama
    - PROTECT_TOWER: minimal 2 hero melindungi tower
    - PROTECT_CASTLE: semua hero melindungi castle
    - ATTACK_BOSS: semua hero menyerang mini boss / true boss
    - ATTACK_DAMAGE_DEALER: semua hero fokus ke hero musuh dengan
      total damage terbanyak (damage_dealt)
    """

    def __init__(self, game):
        self.game = game
        self.active_command = None
        self.command_timer = 0
        self.command_target = None  # bisa tower, boss, atau posisi
        self.command_origin = None
        self.feedback_timer = 0
        self.feedback_text = ""
        self.feedback_color = (255, 255, 255)

        # Cooldown antar perintah (anti spam)
        self.cooldown = 0
        self.cooldown_max = 30  # 0.5 detik

        # Untuk visual gather point
        self.gather_point = None
        self.gather_point_timer = 0

        # ── HOLD: perintah yang sedang DITAHAN ──
        # Selama held_command terisi, update() menerbitkan ulang
        # perintah itu setiap cooldown_max frame supaya terus ditaati
        # hero (durasi 10 detiknya tidak pernah habis) sampai
        # hold_end() dipanggil. Diisi oleh hold_start().
        self.held_command = None       # nama perintah yang di-hold
        self.hold_args = ()            # argumen saat hold_start
        self.hold_kwargs = {}
        self.hold_follow_mouse = False  # GATHER keyboard: ikut kursor
        self.hold_elapsed = 0          # frame sejak hold_start
        self._hold_has_fired = False   # sudah pernah sukses terbit?
        self._gather_push_fired = False  # push GATHER sudah terpicu?

    # ═══════════════════════════════════════
    # CORE COMMAND ISSUERS
    # ═══════════════════════════════════════

    def can_issue(self):
        return self.cooldown <= 0 and self.game.state == "playing"

    def _set_feedback(self, text, color=(255, 220, 100)):
        self.feedback_text = text
        self.feedback_timer = 180  # 3 detik
        self.feedback_color = color
        # Kirim ke UI notification juga
        try:
            if hasattr(self.game, 'ui') and self.game.ui:
                self.game.ui.add_notification(text, color)
        except Exception:
            pass
        try:
            from mobile import sidepanel as sp
            sp.beri_tahu_global(text, color, 3000)
        except Exception:
            pass
        # Efek visual
        try:
            self.game.effects.add_damage_number(
                640, 100, text, is_critical=True
            )
        except Exception:
            pass

    def _get_alive_blue_heroes(self):
        return [h for h in getattr(self.game, 'heroes', []) if getattr(h, 'alive', False)]

    def _clear_hero_retreat(self, heroes):
        for h in heroes:
            h.is_retreating = False
            h.destination_auto = False

    # ═══════════════════════════════════════
    # HOLD: tahan perintah supaya terus aktif
    # ═══════════════════════════════════════

    def _issuers(self):
        return {
            TacticalCommand.GATHER: self.command_gather,
            TacticalCommand.PROTECT_TOWER: self.command_protect_tower,
            TacticalCommand.PROTECT_CASTLE: self.command_protect_castle,
            TacticalCommand.ATTACK_BOSS: self.command_attack_boss,
            TacticalCommand.ATTACK_DAMAGE_DEALER:
                self.command_attack_damage_dealer,
        }

    def hold_start(self, name, *args, follow_mouse=False, **kwargs):
        """Mulai MENAHAN perintah taktis.

        Perintah diterbitkan SEKARANG dengan umpan balik penuh
        (suara + teks) seperti tekanan biasa, lalu update()
        menerbitkannya ulang secara senyap setiap 0,5 detik selama
        masih ditahan - sampai hold_end() dipanggil.

        Kalau syarat belum terpenuhi saat ditekan (mis. belum ada
        boss untuk ATTACK BOSS), hold tetap "dipersenjatai":
        penerbitan ulang dicoba terus dan aktivasi PERTAMA yang
        berhasil tetap bersuara. Dengan begitu pemain bisa menahan
        tombol sambil menunggu boss muncul.

        follow_mouse=True (GATHER via keyboard): titik kumpul mengikuti
        kursor selama ditahan.
        """
        if name not in self._issuers():
            return False
        if name == self.held_command and self.hold_elapsed > 0:
            # Penekanan berulang untuk hold yang sama (mis. key repeat /
            # tombol controller yang ditahan) = masih menahan; jangan
            # reset hitungan waktu dan jangan terbitkan ulang dengan
            # suara penuh (anti spam).
            return True
        # Hold baru menggantikan hold lama (satu perintah aktif).
        self.held_command = name
        self.hold_args = args
        self.hold_kwargs = dict(kwargs)
        self.hold_follow_mouse = bool(follow_mouse)
        self.hold_elapsed = 0
        self._hold_has_fired = False
        self._gather_push_fired = False
        ok = self._issue_held(loud=True)
        if ok:
            self._hold_has_fired = True
        return ok

    def hold_end(self, name=None):
        """Lepaskan hold.

        - TAP cepat (< 0,33 detik): perintah berjalan sampai durasi
          normalnya habis (10 detik) - perilaku tekan-sekali yang lama
          tidak berubah.
        - HOLD lama: penegakkan berhenti SAAT DILEPAS (request user);
          perintah terakhir dibiarkan selesai sebentar (ekor 0,5
          detik) lalu hero kembali ke AI masing-masing.

        name=None  -> lepas apa pun yang sedang di-hold.
        name cocok -> hanya lepas kalau perintah itu yang sedang
                      di-hold (tombol lama yang dilepas tidak boleh
                      membatalkan hold tombol yang lebih baru).
        """
        if self.held_command is None:
            return
        if name is not None and name != self.held_command:
            return
        elapsed = self.hold_elapsed
        self.held_command = None
        self.hold_args = ()
        self.hold_kwargs = {}
        self.hold_follow_mouse = False
        self.hold_elapsed = 0
        self._hold_has_fired = False
        if elapsed >= HOLD_TAP_MAX_FRAMES and self.command_timer > 0:
            # HOLD lama dilepas -> perintah tidak lagi ditegakkan.
            self.command_timer = min(self.command_timer,
                                     HOLD_RELEASE_TAIL)


    def _issue_held(self, loud):
        """Terbitkan perintah yang sedang di-hold SEKALI.

        loud=True  -> umpan balik penuh (aktivasi pertama).
        loud=False -> senyap (refresh berkala selama ditahan) supaya
                      suara/teks tidak berdentum tiap 0,5 detik.
        """
        name = self.held_command
        if name is None:
            return False
        # GATHER yang SUDAH push (hero tiba & mulai menyerang bersama)
        # tidak boleh diseret balik ke titik kumpul oleh refresh;
        # selama di-hold yang dikunci ulang adalah target musuhnya.
        if (name == TacticalCommand.GATHER and not loud
                and self._gather_push_fired):
            ok = self._gather_hold_push()
            self.cooldown = self.cooldown_max
            return ok
        issuer = self._issuers().get(name)
        if issuer is None:
            return False
        args = self.hold_args
        kwargs = self.hold_kwargs
        if name == TacticalCommand.GATHER and self.hold_follow_mouse:
            # Titik kumpul mengikuti kursor selama ditahan.
            mx = getattr(self.game, 'mouse_x', 0)
            my = getattr(self.game, 'mouse_y', 0)
            if 0 <= mx < SCREEN_WIDTH and 0 <= my < SCREEN_HEIGHT:
                args = (mx, my)
            else:
                args = ()
        ok = issuer(*args, silent=not loud, **kwargs)
        if not ok:
            # Syarat belum terpenuhi (mis. belum ada boss): pace
            # percobaan ulang supaya tidak 60x/detik, tapi jangan
            # kunci penuh supaya tombol lain masih cepat merespons.
            self.cooldown = max(self.cooldown, self.cooldown_max // 2)
        return ok

    def _gather_hold_push(self):
        """GATHER lanjutan selama di-hold: regroup sudah selesai dan
        push sudah terpicu -> kunci ulang musuh terdekat dari titik
        kumpul supaya semua hero terus menyerang bersama."""
        heroes = self._get_alive_blue_heroes()
        if not heroes or not self.gather_point:
            return False
        gx, gy = self.gather_point
        target = self._find_nearest_enemy_target(gx, gy)
        if target is None:
            # Tidak ada musuh: tetap diam berkumpul di titik.
            args = self.hold_args or (gx, gy)
            return self.command_gather(*args, silent=True,
                                       **self.hold_kwargs)
        for hero in heroes:
            hero.follow_target = target
            hero.destination = None
            hero.destination_auto = False
            hero.is_retreating = False
            hero.target = target
        self.command_timer = 600       # jaga perintah tetap hidup
        self.gather_point_timer = 150  # visual titik tetap tampak
        return True

    def _try_gather_push(self):
        """Setelah regroup (>=60% hero tiba di titik), perintahkan
        push bersama ke musuh terdekat. Return True kalau terpicu."""
        heroes = self._get_alive_blue_heroes()
        if not heroes or not self.gather_point:
            return False
        gx, gy = self.gather_point
        arrived = 0
        for h in heroes:
            if math.hypot(h.x - gx, h.y - gy) < 100:
                arrived += 1
        if arrived < len(heroes) * 0.6:
            return False
        target = self._find_nearest_enemy_target(gx, gy)
        if not target:
            return False
        for hero in heroes:
            hero.follow_target = target
            hero.destination = None
        self._gather_push_fired = True
        self._set_feedback(
            f"GATHER ATTACK! {len(heroes)} heroes push together!",
            (100, 220, 255))
        return True

    # ───────────────────────────────────────
    # GATHER: semua hero berkumpul dan menyerang bersama
    # ───────────────────────────────────────
    def command_gather(self, gather_x=None, gather_y=None, silent=False):
        """
        GATHER - Semua hero berkumpul di satu titik dan menyerang bersama.
        Jika gather_x/y None, pakai posisi hero terpilih atau tengah peta.

        silent=True dipakai refresh mode-HOLD: tanpa suara/feedback
        (penerbitan ulang tiap 0,5 detik tidak boleh berisik).
        """
        if not self.can_issue():
            return False

        heroes = self._get_alive_blue_heroes()
        if not heroes:
            if not silent:
                self._set_feedback("No heroes alive!", (255, 100, 100))
            return False

        # Tentukan titik kumpul
        if gather_x is None or gather_y is None:
            # Prioritas: hero selected > rata-rata posisi hero > tengah map
            sel = getattr(self.game, 'selected_hero', None)
            if sel and getattr(sel, 'alive', False) and sel.team == "blue":
                gather_x, gather_y = sel.x, sel.y
            else:
                # Rata-rata posisi hero
                if len(heroes) >= 2:
                    avg_x = sum(h.x for h in heroes) / len(heroes)
                    avg_y = sum(h.y for h in heroes) / len(heroes)
                    # Sedikit maju ke arah musuh (mid point antara avg dan red base)
                    # supaya tidak kumpul di base terus
                    mid_mix = 0.35
                    gather_x = avg_x * (1 - mid_mix) + RED_BASE_X * mid_mix
                    gather_y = avg_y * (1 - mid_mix) + RED_BASE_Y * mid_mix
                    # Clamp ke tengah arena
                    gather_x = max(200, min(1080, gather_x))
                    gather_y = max(100, min(620, gather_y))
                else:
                    gather_x, gather_y = 640, 360

        self.active_command = TacticalCommand.GATHER
        self.command_timer = 600  # 10 detik durasi command aktif
        self.gather_point = (gather_x, gather_y)
        self.gather_point_timer = 150  # 2.5 detik visual sesaat di map (request user)
        self.cooldown = self.cooldown_max
        if not silent:
            # Perintah gather BARU -> push follow-up belum terpicu.
            # (Refresh senyap mode-HOLD tidak mereset supaya push
            #  yang sudah terpicu tidak batal.)
            self._gather_push_fired = False

        self._clear_hero_retreat(heroes)

        # Perintahkan semua hero ke titik kumpul dengan spread kecil
        # biar tidak numpuk
        for i, hero in enumerate(heroes):
            angle = (i / max(1, len(heroes))) * math.pi * 2
            spread = 35 + (i % 3) * 15
            tx = gather_x + math.cos(angle) * spread
            ty = gather_y + math.sin(angle) * spread
            hero.move_to(tx, ty, auto=False)
            # Reset target supaya fokus ke perintah
            hero.follow_target = None
            hero.target = None

        # Sound & feedback
        if not silent:
            try:
                from _system import SoundManager
                SoundManager().play('ui_click', volume_mult=0.8)
            except Exception:
                pass

            self._set_feedback(f"GATHER! {len(heroes)} heroes regrouping!", (100, 220, 255))
            print(f"[TACTICAL] GATHER at ({int(gather_x)}, {int(gather_y)}) - {len(heroes)} heroes")

            # Efek visual di titik kumpul
            try:
                self.game.effects.add_death_explosion(gather_x, gather_y, team="blue", size='small')
            except Exception:
                pass

        return True

    # ───────────────────────────────────────
    # PROTECT TOWER: minimal 2 hero melindungi tower
    # ───────────────────────────────────────
    def command_protect_tower(self, tower=None, silent=False):
        """
        PROTECT TOWER - Minimal 2 hero melindungi tower yang terancam.
        Jika tower None, otomatis cari tower yang paling terancam.

        silent=True dipakai refresh mode-HOLD (tanpa suara/feedback).
        Tower yang sudah hancur dianggap None -> pilih ulang otomatis
        (penting saat tower target hancur di tengah hold).
        """
        if not self.can_issue():
            return False

        heroes = self._get_alive_blue_heroes()
        if len(heroes) < 1:
            if not silent:
                self._set_feedback("No heroes alive!", (255, 100, 100))
            return False

        # Cari tower target
        target_tower = tower
        if target_tower is not None and not getattr(target_tower, 'alive', False):
            target_tower = None
        if target_tower is None:
            target_tower = self._find_most_threatened_tower()

        if target_tower is None:
            # Fallback: tower dengan HP terendah atau terdepan
            blue_towers = [t for t in getattr(self.game, 'towers', []) if t.team == "blue" and t.alive]
            if not blue_towers:
                if not silent:
                    self._set_feedback("No tower to protect!", (255, 150, 100))
                return False
            # Pilih yang paling dekat ke musuh (x terbesar untuk blue)
            blue_towers.sort(key=lambda t: (-t.x, t.hp / max(1, t.max_hp)))
            target_tower = blue_towers[0]

        self.active_command = TacticalCommand.PROTECT_TOWER
        self.command_timer = 600
        self.command_target = target_tower
        self.gather_point = (target_tower.x, target_tower.y)
        self.gather_point_timer = 150  # sesaat di map
        self.cooldown = self.cooldown_max

        # Minimal 2 hero, maksimal semua jika ada 2 saja
        num_needed = min(max(2, 2), len(heroes))  # minimal 2, sesuai spec
        # Jika hero banyak, kirim 2-3 terdekat, sisanya tetap bebas? Spec bilang minimal 2 respon
        # Kita kirim minimal 2, tapi jika hero <=3 kirim semua, jika >3 kirim 2-3 terdekat + 1 cadangan
        if len(heroes) <= 3:
            protectors = heroes
        else:
            # Urutkan berdasarkan jarak ke tower
            heroes_sorted = sorted(heroes, key=lambda h: math.hypot(h.x - target_tower.x, h.y - target_tower.y))
            # Kirim 2-3 terdekat, minimal 2
            # Jika tower sangat terancam (banyak musuh), kirim 3
            threat = self._count_enemies_near(target_tower.x, target_tower.y, 250)
            num_to_send = 3 if threat >= 3 else 2
            protectors = heroes_sorted[:num_to_send]

        self._clear_hero_retreat(protectors)

        for i, hero in enumerate(protectors):
            angle = (i / len(protectors)) * math.pi * 2 if len(protectors) > 1 else 0
            spread = 30 + i * 10
            tx = target_tower.x + math.cos(angle) * spread
            ty = target_tower.y + math.sin(angle) * spread
            hero.move_to(tx, ty, auto=False)
            hero.follow_target = None
            hero.target = None

        if not silent:
            try:
                from _system import SoundManager
                SoundManager().play('ui_click', volume_mult=0.8)
            except Exception:
                pass

            self._set_feedback(f"PROTECT TOWER! {len(protectors)} heroes defending {target_tower.name}!", (100, 255, 100))
            print(f"[TACTICAL] PROTECT TOWER {target_tower.name} at ({int(target_tower.x)}, {int(target_tower.y)}) - {len(protectors)} heroes, threat={self._count_enemies_near(target_tower.x, target_tower.y, 250)}")

        return True

    # ───────────────────────────────────────
    # PROTECT CASTLE: semua hero melindungi castle
    # ───────────────────────────────────────
    def command_protect_castle(self, silent=False):
        """
        PROTECT CASTLE - Semua hero berkumpul dan melindungi castle (base biru)

        silent=True dipakai refresh mode-HOLD (tanpa suara/feedback).
        """
        if not self.can_issue():
            return False

        heroes = self._get_alive_blue_heroes()
        if not heroes:
            if not silent:
                self._set_feedback("No heroes alive!", (255, 100, 100))
            return False

        castle = getattr(self.game, 'blue_base', None)
        if not castle or not getattr(castle, 'alive', False):
            if not silent:
                self._set_feedback("Castle destroyed!", (255, 100, 100))
            return False

        self.active_command = TacticalCommand.PROTECT_CASTLE
        self.command_timer = 600
        self.command_target = castle
        self.gather_point = (castle.x, castle.y)
        self.gather_point_timer = 150  # sesaat di map
        self.cooldown = self.cooldown_max

        self._clear_hero_retreat(heroes)

        # Formasi melingkar di sekitar castle
        for i, hero in enumerate(heroes):
            angle = (i / len(heroes)) * math.pi * 2
            # Jarak dari castle: dekat tapi tidak di dalam
            radius = 80 + (i % 2) * 30
            tx = castle.x + math.cos(angle) * radius
            ty = castle.y + math.sin(angle) * radius
            # Clamp agar tidak keluar map
            tx = max(50, min(1230, tx))
            ty = max(50, min(670, ty))
            hero.move_to(tx, ty, auto=False)
            hero.follow_target = None
            hero.target = None

        if not silent:
            try:
                from _system import SoundManager
                SoundManager().play('ui_click', volume_mult=0.8)
            except Exception:
                pass

            self._set_feedback(f"PROTECT CASTLE! {len(heroes)} heroes defending base!", (255, 220, 50))
            print(f"[TACTICAL] PROTECT CASTLE at ({int(castle.x)}, {int(castle.y)}) - {len(heroes)} heroes")

            try:
                self.game.effects.add_death_explosion(castle.x, castle.y, team="blue", size='small')
            except Exception:
                pass

        return True

    # ───────────────────────────────────────
    # ATTACK BOSS: semua hero menyerang mini boss / true boss
    # ───────────────────────────────────────
    def command_attack_boss(self, silent=False):
        """
        ATTACK BOSS - Semua hero menyerang mini boss atau true boss yang aktif

        silent=True dipakai refresh mode-HOLD (tanpa suara/feedback).
        """
        if not self.can_issue():
            return False

        heroes = self._get_alive_blue_heroes()
        if not heroes:
            if not silent:
                self._set_feedback("No heroes alive!", (255, 100, 100))
            return False

        boss = getattr(self.game, 'active_boss', None)
        if not boss or not getattr(boss, 'alive', False):
            # Untuk sekarang, feedback no boss
            if not silent:
                self._set_feedback("No boss active!", (255, 150, 100))
                print("[TACTICAL] ATTACK BOSS - No active boss found")
            return False

        self.active_command = TacticalCommand.ATTACK_BOSS
        self.command_timer = 600
        self.command_target = boss
        self.gather_point = (boss.x, boss.y)
        self.gather_point_timer = 150  # sesaat di map
        self.cooldown = self.cooldown_max

        self._clear_hero_retreat(heroes)

        for i, hero in enumerate(heroes):
            # Semua hero langsung set follow_target ke boss
            hero.follow_target = boss
            hero.destination = None
            hero.destination_auto = False
            hero.target = boss
            # Juga move_to untuk memastikan mereka mendekat
            # dengan sedikit spread supaya tidak numpuk di satu titik
            angle = (i / len(heroes)) * math.pi * 2
            spread = hero.range * 0.5 + i * 8
            tx = boss.x + math.cos(angle) * spread
            ty = boss.y + math.sin(angle) * spread
            hero.move_to(tx, ty, auto=False)
            # Override lagi follow_target setelah move_to (move_to clear follow_target)
            hero.follow_target = boss

        if not silent:
            try:
                from _system import SoundManager
                SoundManager().play('hero_skill', volume_mult=0.9)
            except Exception:
                pass

            boss_name = getattr(boss, 'name', 'BOSS')
            self._set_feedback(f"ATTACK BOSS! All heroes attack {boss_name}!", (255, 100, 100))
            print(f"[TACTICAL] ATTACK BOSS {boss_name} at ({int(boss.x)}, {int(boss.y)}) - {len(heroes)} heroes")

        return True

    # ───────────────────────────────────────
    # ATTACK DAMAGE DEALER: fokus hero musuh dengan damage terbanyak
    # ───────────────────────────────────────
    def _find_enemy_damage_dealer(self):
        """Hero musuh (merah) hidup dengan total damage terbanyak.

        ``damage_dealt`` diakumulasi di take_damage() semua entitas
        (basic attack, projectile, on-hit, AOE skill) - lihat
        _entity.credit_hero_damage.
        """
        ai = getattr(self.game, 'ai', None)
        candidates = [h for h in getattr(ai, 'heroes', [])
                      if getattr(h, 'alive', False)]
        if not candidates:
            return None
        return max(candidates,
                   key=lambda h: getattr(h, 'damage_dealt', 0))

    def command_attack_damage_dealer(self, silent=False):
        """
        ATTACK DAMAGE DEALER - Semua hero biru fokus menyerang hero
        musuh dengan total damage terbanyak (damage dealer utama
        tim lawan).

        silent=True dipakai refresh mode-HOLD (tanpa suara/feedback).
        Target dievaluasi ulang tiap penerbitan - kalau damage
        dealer terbanyak berganti, fokus hero ikut pindah.
        """
        if not self.can_issue():
            return False

        heroes = self._get_alive_blue_heroes()
        if not heroes:
            if not silent:
                self._set_feedback("No heroes alive!", (255, 100, 100))
            return False

        dealer = self._find_enemy_damage_dealer()
        if dealer is None:
            if not silent:
                self._set_feedback("No enemy heroes!", (255, 150, 100))
                print("[TACTICAL] ATTACK DAMAGE DEALER - no enemy hero")
            return False

        self.active_command = TacticalCommand.ATTACK_DAMAGE_DEALER
        self.command_timer = 600
        self.command_target = dealer
        self.gather_point = (dealer.x, dealer.y)
        self.gather_point_timer = 150  # sesaat di map
        self.cooldown = self.cooldown_max

        self._clear_hero_retreat(heroes)

        for i, hero in enumerate(heroes):
            # Semua hero mengunci follow ke damage dealer
            hero.follow_target = dealer
            hero.destination = None
            hero.destination_auto = False
            hero.target = dealer
            # Dekati dengan spread supaya tidak numpuk
            angle = (i / len(heroes)) * math.pi * 2
            spread = hero.range * 0.5 + i * 8
            tx = dealer.x + math.cos(angle) * spread
            ty = dealer.y + math.sin(angle) * spread
            hero.move_to(tx, ty, auto=False)
            # move_to menghapus follow_target - pasang lagi
            hero.follow_target = dealer

        if not silent:
            try:
                from _system import SoundManager
                SoundManager().play('hero_skill', volume_mult=0.9)
            except Exception:
                pass

            dmg = int(getattr(dealer, 'damage_dealt', 0))
            self._set_feedback(
                f"ATTACK DAMAGE DEALER! Focus {dealer.name} ({dmg} dmg)!",
                (255, 130, 255))
            print(f"[TACTICAL] ATTACK DAMAGE DEALER {dealer.name} "
                  f"({dmg} dmg) at ({int(dealer.x)}, {int(dealer.y)}) - "
                  f"{len(heroes)} heroes")

        return True

    # ═══════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════

    def _find_most_threatened_tower(self):
        """Cari tower biru yang paling terancam"""
        blue_towers = [t for t in getattr(self.game, 'towers', []) if t.team == "blue" and t.alive]
        if not blue_towers:
            return None

        # Hitung threat untuk tiap tower
        scored = []
        for tower in blue_towers:
            enemies_near = self._count_enemies_near(tower.x, tower.y, 220)
            hp_ratio = tower.hp / max(1, tower.max_hp)
            # Score: lebih banyak musuh + HP rendah = lebih terancam
            # HP rendah diberi bobot tinggi
            threat_score = enemies_near * 10 + (1 - hp_ratio) * 15
            # Bonus jika tower adalah outer (lebih rentan)
            if tower.x < 400:  # dekat base biru tapi masih outer
                threat_score += 2
            scored.append((threat_score, tower))

        if not scored:
            return None

        # Sort descending threat
        scored.sort(key=lambda x: -x[0])
        # Jika top threat 0 (tidak ada musuh dekat), tetap pilih yang HP terendah
        if scored[0][0] == 0:
            blue_towers.sort(key=lambda t: t.hp / max(1, t.max_hp))
            return blue_towers[0]

        return scored[0][1]

    def _count_enemies_near(self, x, y, radius):
        """Hitung musuh merah di dekat posisi"""
        count = 0
        try:
            # Minions merah
            for m in getattr(self.game, 'minions', []):
                if m.team == "red" and getattr(m, 'alive', False):
                    if math.hypot(m.x - x, m.y - y) <= radius:
                        count += 1
            # Heroes merah
            ai = getattr(self.game, 'ai', None)
            if ai:
                for h in getattr(ai, 'heroes', []):
                    if getattr(h, 'alive', False):
                        if math.hypot(h.x - x, h.y - y) <= radius:
                            count += 1
            # Boss jika team red
            boss = getattr(self.game, 'active_boss', None)
            if boss and getattr(boss, 'alive', False) and getattr(boss, 'team', 'red') == 'red':
                if math.hypot(boss.x - x, boss.y - y) <= radius:
                    count += 2  # boss dihitung 2
        except Exception:
            pass
        return count

    def _find_nearest_enemy_target(self, x, y):
        """Cari target musuh terdekat dari posisi x,y (tower, hero, minion, boss)"""
        try:
            best = None
            best_dist = 9999
            game = self.game

            # Boss prioritas tertinggi untuk gather attack
            boss = getattr(game, 'active_boss', None)
            if boss and getattr(boss, 'alive', False):
                d = math.hypot(boss.x - x, boss.y - y)
                if d < best_dist:
                    best_dist = d
                    best = boss

            # Towers merah
            for t in getattr(game, 'towers', []):
                if t.team == "red" and t.alive:
                    d = math.hypot(t.x - x, t.y - y)
                    if d < best_dist:
                        best_dist = d
                        best = t

            # Heroes merah
            ai = getattr(game, 'ai', None)
            if ai:
                for h in getattr(ai, 'heroes', []):
                    if getattr(h, 'alive', False):
                        d = math.hypot(h.x - x, h.y - y)
                        if d < best_dist:
                            best_dist = d
                            best = h

            # Minions merah (jika tidak ada target besar)
            if best is None:
                for m in getattr(game, 'minions', []):
                    if m.team == "red" and getattr(m, 'alive', False):
                        d = math.hypot(m.x - x, m.y - y)
                        if d < best_dist:
                            best_dist = d
                            best = m

            # Fallback ke red castle
            if best is None:
                red_base = getattr(game, 'red_base', None)
                if red_base and getattr(red_base, 'alive', False):
                    best = red_base

            return best
        except Exception:
            return None

    def update(self):
        """Update timers tiap frame + penegakkan HOLD + auto-protect"""
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.command_timer > 0:
            self.command_timer -= 1
            if self.command_timer <= 0:
                self.active_command = None
                self.command_target = None
        if self.gather_point_timer > 0:
            self.gather_point_timer -= 1
            if self.gather_point_timer <= 0:
                self.gather_point = None
        if self.feedback_timer > 0:
            self.feedback_timer -= 1

        # ═══ HOLD: perintah yang ditahan terus ditegakkan ═══
        # Selama tombol/tuts ditahan, terbitkan ulang perintahnya
        # tiap cooldown_max frame (0,5 detik) - senyap - supaya:
        #   1. durasi 10 detiknya tidak pernah habis (timer terisi
        #      terus), dan
        #   2. hero tidak kabur kembali ke AI masing-masing (perintah
        #      di-refresh sebelum mereka selesai/beralih).
        if self.held_command is not None \
                and getattr(self.game, 'state', '') == 'playing':
            self.hold_elapsed += 1
            if self.cooldown <= 0:
                # Refresh selalu SENYAP supaya tidak ada spam
                # suara/teks tiap 0,5 detik (kegagalan bersenjata -
                # mis. menunggu boss - pun diam saja). Pengecualian:
                # keberhasilan PERTAMA diumumkan sekali lewat replay
                # loud supaya pemain sadar perintahnya sudah jalan
                # (mis. boss akhirnya muncul saat tombol ditahan).
                ok = self._issue_held(loud=False)
                if ok and not self._hold_has_fired:
                    self.cooldown = 0
                    self._issue_held(loud=True)
                if ok:
                    self._hold_has_fired = True

        # ═══ GATHER FOLLOW-UP: setelah berkumpul, serang bersama ═══
        if self.active_command == TacticalCommand.GATHER and self.gather_point:
            try:
                if self.held_command == TacticalCommand.GATHER:
                    # Mode HOLD: command_timer terus terisi ulang
                    # sehingga tidak pernah menyentuh 300 - pakai
                    # lama hold sebagai gantinya. Dicek TIAP frame
                    # mulai detik ke-4 sampai benar-benar terpicu
                    # (hero yang terlambat tiba tetap kebagian push).
                    if (not self._gather_push_fired
                            and self.hold_elapsed >= GATHER_PUSH_DELAY_FRAMES):
                        self._try_gather_push()
                elif self.command_timer == 300:  # tepat setengah dari 600
                    self._try_gather_push()
            except Exception:
                pass

        # ═══ AUTO-PROTECT TOWER (ketika tidak ada perintah aktif) ═══
        # Jika tower biru dalam bahaya (HP < 60% dan ada musuh dekat),
        # otomatis kirim minimal 2 hero untuk protect, sesuai spec.
        # Ini membantu pemain yang tidak sempat tekan tombol manual.
        if self.active_command is None and self.cooldown <= 0:
            try:
                # Cek setiap 90 frame (~1.5 detik) agar tidak spam
                if not hasattr(self, '_auto_check_timer'):
                    self._auto_check_timer = 0
                self._auto_check_timer += 1
                if self._auto_check_timer >= 90:
                    self._auto_check_timer = 0
                    self._auto_evaluate_protect()
            except Exception:
                pass

    def _auto_evaluate_protect(self):
        """Otomatis evaluasi apakah perlu protect tower / castle"""
        try:
            game = self.game
            if getattr(game, 'state', '') != 'playing':
                return

            # 1. Cek castle dalam bahaya besar (HP < 40% dan musuh dekat)
            castle = getattr(game, 'blue_base', None)
            if castle and getattr(castle, 'alive', False):
                hp_ratio = castle.hp / max(1, castle.max_hp)
                enemies_near_castle = self._count_enemies_near(castle.x, castle.y, 300)
                if hp_ratio < 0.4 and enemies_near_castle >= 2:
                    # Auto protect castle
                    self.command_protect_castle()
                    return

            # 2. Cek tower dalam bahaya (HP < 50% dan ada musuh)
            blue_towers = [t for t in getattr(game, 'towers', []) if t.team == "blue" and t.alive]
            threatened = []
            for tower in blue_towers:
                hp_ratio = tower.hp / max(1, tower.max_hp)
                enemies_near = self._count_enemies_near(tower.x, tower.y, 250)
                if hp_ratio < 0.6 and enemies_near >= 2:
                    threatened.append((enemies_near, hp_ratio, tower))
                elif enemies_near >= 4:
                    threatened.append((enemies_near, hp_ratio, tower))

            if threatened:
                # Pilih yang paling terancam
                threatened.sort(key=lambda x: (-x[0], x[1]))
                self.command_protect_tower(threatened[0][2])
                return

            # 3. Cek boss muncul dan hero menganggur - auto attack boss jika boss HP < 70%?
            boss = getattr(game, 'active_boss', None)
            if boss and getattr(boss, 'alive', False):
                # Jika boss sudah ada lama dan tidak ada perintah, hero bisa auto-focus boss
                # Hanya jika boss sudah di bawah 80% HP (sudah engaged)
                try:
                    boss_hp_ratio = boss.hp / max(1, boss.max_hp)
                    if boss_hp_ratio < 0.8:
                        # Jangan auto spam, hanya jika sudah beberapa wave
                        if getattr(game, 'wave_number', 0) >= 11:
                            # 20% chance auto attack boss tiap evaluasi
                            import random
                            if random.random() < 0.2:
                                self.command_attack_boss()
                except Exception:
                    pass

        except Exception as e:
            print(f"[TACTICAL AUTO] eval error: {e}")

    def _get_command_color(self):
        if self.active_command == TacticalCommand.GATHER:
            return (100, 220, 255)
        elif self.active_command == TacticalCommand.PROTECT_TOWER:
            return (100, 255, 100)
        elif self.active_command == TacticalCommand.PROTECT_CASTLE:
            return (255, 220, 50)
        elif self.active_command == TacticalCommand.ATTACK_BOSS:
            return (255, 100, 100)
        elif self.active_command == TacticalCommand.ATTACK_DAMAGE_DEALER:
            return (255, 130, 255)
        return (255, 220, 100)

    def draw_world(self, surface):
        """Gambar di world layer (gather point, garis hero)"""
        if not surface:
            return
        if not (self.gather_point and self.gather_point_timer > 0):
            return
        gx, gy = self.gather_point
        alpha_ratio = self.gather_point_timer / 150.0
        alpha_ratio = max(0.0, min(1.0, alpha_ratio))
        import pygame
        pulse = (math.sin(pygame.time.get_ticks() * 0.008) * 0.3 + 0.7) * alpha_ratio
        col = self._get_command_color()

        # Lingkaran luar
        for r in range(50, 20, -8):
            a = int((50 - r) * 4 * pulse)
            if a > 0:
                try:
                    pygame.draw.circle(surface, (*col, a), (int(gx), int(gy)), r, 2)
                except Exception:
                    pygame.draw.circle(surface, col, (int(gx), int(gy)), r, 2)

        # Titik pusat
        pygame.draw.circle(surface, col, (int(gx), int(gy)), 6)
        pygame.draw.circle(surface, (255, 255, 255), (int(gx), int(gy)), 2)

        # Garis dari hero ke titik kumpul
        if self.active_command in (TacticalCommand.GATHER, TacticalCommand.PROTECT_CASTLE, TacticalCommand.ATTACK_BOSS, TacticalCommand.PROTECT_TOWER):
            for hero in self._get_alive_blue_heroes():
                dx = gx - hero.x
                dy = gy - hero.y
                dist = math.hypot(dx, dy)
                if dist > 80:
                    for seg in range(3):
                        t1 = seg * 0.33
                        t2 = t1 + 0.18
                        x1 = hero.x + dx * t1
                        y1 = hero.y + dy * t1
                        x2 = hero.x + dx * t2
                        y2 = hero.y + dy * t2
                        try:
                            pygame.draw.line(surface, (*col, int(120 * pulse)), (int(x1), int(y1)), (int(x2), int(y2)), 2)
                        except Exception:
                            pygame.draw.line(surface, col, (int(x1), int(y1)), (int(x2), int(y2)), 2)

    def draw_ui(self, surface):
        """Gambar feedback text di UI layer (tidak kena shake)"""
        if not surface:
            return
        if self.feedback_timer <= 0:
            return
        import pygame
        try:
            from _render import get_font
            font = get_font(28, "body_bold")
        except Exception:
            font = pygame.font.Font(None, 28)

        alpha = 255
        if self.feedback_timer < 30:
            alpha = int(255 * (self.feedback_timer / 30))

        if self.feedback_timer > 150:
            prog = (180 - self.feedback_timer) / 30.0
            prog = max(0, min(1, prog))
            alpha = int(255 * prog)
            y_offset = int((1 - prog) * 20)
        else:
            y_offset = 0

        text_surf = font.render(self.feedback_text, True, self.feedback_color)
        shadow = font.render(self.feedback_text, True, (0, 0, 0))
        shadow.set_alpha(alpha // 2)
        text_rect = text_surf.get_rect(center=(640, 90 + y_offset))

        bg_rect = text_rect.inflate(20, 8)
        bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, int(160 * alpha / 255)))
        surface.blit(bg_surf, bg_rect.topleft)

        border_color = (*self.feedback_color, alpha)
        try:
            pygame.draw.rect(surface, border_color, bg_rect, 2, border_radius=6)
        except Exception:
            pygame.draw.rect(surface, border_color, bg_rect, 2)

        text_surf.set_alpha(alpha)
        surface.blit(shadow, (text_rect.x + 2, text_rect.y + 2))
        surface.blit(text_surf, text_rect)

    def draw(self, surface):
        """Legacy wrapper - gambar world + ui sekaligus"""
        self.draw_world(surface)
        self.draw_ui(surface)

