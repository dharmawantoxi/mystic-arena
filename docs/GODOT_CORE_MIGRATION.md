# Migrasi `_core.py` ke Godot 4

Tanggal: 2026-11-01. Branch: `arena/e11a12c5-mystic-arena`.

## Ruang lingkup

Permintaan pengguna adalah **seluruh `_core.py`**: gameplay, menu/progres/save-slot,
input/controller, pengaturan, developer mode, top-up/voucher, dan cloud. Port ini
memindahkan orkestrasi dan aturan inti ke GDScript native, bukan menjalankan Python
di dalam Godot. Sumber Python tetap disimpan sebagai referensi parity.

Yang sudah native dan dapat dimainkan secara data-driven:

- Loop pertandingan 60 Hz melalui `Main.gd` → `CoreGame.simulation_step()`.
- Ekonomi starting gold, passive income milli-gold, reward menang/replay, dan
  difficulty lock (`Economy.gd`, `SaveRepository.gd`).
- Wave director: komposisi minion per castle level, interval 1500 tick, spawn delay
  20, jadwal mini-boss acak easy 20–40 / normal-hard 11–30, true boss setelah 6
  tower merah hancur, auto-scale castle AI (`WaveDirector.gd`, `MatchModel.gd`).
- Unit combat: minion/tower/castle/hero/boss, shield, regen, armor/magic resist,
  debuff tower (burn/slow/atk-slow/skill-down/anti-heal/chain/splash/double-shot),
  item stats, lifesteal/crit/CDR/spell-vamp, respawn hero, dan reward kill
  (`BattleUnit.gd`, `StatusEffects.gd`, `UnitInventory.gd`, `MatchModel.gd`).
- Tactical hold/tap: gather, protect tower/castle, attack boss, attack damage
  dealer, release tail, dan auto-protect (`TacticalCommands.gd`).
- Menu native: pilih level dengan unlock/progres, 3 save slot, hero shop meta,
  pengaturan lengkap, top-up/voucher, cloud/backup lokal (`MenuView.gd`).
- Input/controller: cursor accel/deadzone, button edge, dpad repeat, trigger,
  scroll axis, rumble, dan label Xbox/PS/generic (`ControllerCore.gd`,
  `ControllerManager.gd`).
- Developer mode: F1/F2/F3, gold/AI gold, skip wave, max tower/castle/hero,
  kill enemies, god mode, instant victory/defeat (`DevMode.gd`). Hanya aktif pada
  debug build atau `MYSTIC_DEV=1`.
- Layanan eksternal sebagai kontrak eksplisit: `CloudSavePort.gd`,
  `TopupPort.gd`, `VoucherService.gd`, `CloudSaveCodec.gd`, `CurrencyFormat.gd`.

## Batas parity yang belum diklaim

Port ini **bukan** salinan visual/rig 1:1 dari seluruh dependensi Python. Bagian
berikut masih memerlukan pekerjaan lanjutan dan tidak boleh diklaim selesai:

1. Skill hero bespoke dan ability boss per-karakter. Saat ini skill Q/W/E/R adalah
   model data-driven generik (damage/single-target/AoE/heal) berdasarkan stat
   `skill_damage`, `skill_range`, dan cooldown. Handler `hero_skills` dan rig
   animasi Python belum diport satu per satu.
2. Renderer Pygame, sprite rig, cinematic intro/death, partikel, floating text,
   screen shake, dan side-panel lebar. `ArenaView.gd` menggambar arena native
   sederhana (lane, unit, health/shield bar, popup, hasil) agar pertandingan dapat
   dimainkan dan diuji tanpa mengklaim parity visual.
3. Projectile visual dan spatial-grid optimisasi. Damage tower diterapkan langsung
   pada target dengan efek splash/chain/debuff; belum ada renderer peluru terpisah.
4. Google Play Games Saved Games nyata. `CloudSavePort` default **unavailable**
   sampai adapter plugin memenuhi kontrak `poll/sign_in/upload/download`.
   Backup lokal dan checksum payload diuji, tetapi sign-in/upload/download Play
   Games belum diverifikasi di perangkat.
5. Top-up nyata. `TopupPort` memerlukan `MYSTIC_TOPUP_URL`; tanpa server ia
   mengembalikan `unavailable`, bukan sukses palsu. Voucher produksi memerlukan
   allowlist; mode demo hanya bila `MYSTIC_VOUCHER_DEMO=1` dan debug build.
6. Ekspor Android, keystore, GPU/audio perangkat, dan benchmark performa.

## Kontrak layanan

### Cloud save

`CloudSaveCodec` memakai magic `MYSTIC_ARENA_BACKUP`, versi 1, 3 slot, dan checksum
SHA-256 atas JSON kanonis. Fixture `tests/fixtures/cloud_payload.json` dibuat dari
`mobile/cloud_save.compute_checksum` Python dan divalidasi oleh tes native.
Karena Godot JSON mem-parse angka sebagai float, codec menormalkan angka integral
dan menerima tiga varian kanonis (typed, int-normal, float-normal) agar payload
Python/Godot dapat saling baca tanpa menolak checksum yang sah.

`CloudSavePort` tidak membundel plugin. Adapter nyata harus menyediakan:

- `poll() -> void`
- `sign_in() -> Dictionary`
- `upload(payload: Dictionary) -> Dictionary`
- `download() -> Dictionary` dengan `payload` bila sukses

Kegagalan cloud tidak boleh menggagalkan save lokal. `CoreGame` menyimpan reward
secara lokal terlebih dahulu, lalu mencoba upload best-effort.

### Top-up/voucher

Endpoint mengikuti `_core.py`:

- `POST /api/topup/create`
- `GET /api/topup/status/{id}`
- `GET /api/topup/qr/{id}`

`TopupPort` hanya memberi sinyal `settled` bila server mengembalikan status
`settled`. `SaveRepository.grant_topup` melakukan dedupe berdasarkan transaction id.
`SaveRepository.grant_voucher` melakukan dedupe kode dan menyimpan riwayat 50
transaksi terakhir. Tidak ada sukses pembayaran yang disimulasikan di produksi.

## Data

`tools/prepare_godot_core.py` mengekstrak data tanpa menjalankan pygame:

- 145 aturan dari `_core.py`
- 54 level dari `levels/level_data.py`
- 222 hero (starter + boss unlock) setelah `hero_balance.apply_to_catalog`
- 216 boss (162 mini + 54 true)
- 33 item forge
- Lane top/mid/bot/river dari `PathGenerator` di `map_components/_bundle.py`
- Localization id/en dan tabel mata uang statis

Hasil: `godot_rebuild/data/core_data.json`, sha256 prefix `068cbd7215bc`.
Regenerasi setelah mengubah data sumber:

```bash
python3 tools/prepare_godot_core.py
python3 tools/prepare_godot_core.py --check
```

## Pemetaan berkas

| Python | Godot |
|---|---|
| `Game.update/reset` | `MatchModel.gd`, `CoreGame.gd` |
| Wave/boss schedule | `WaveDirector.gd` |
| `TowerDebuffMixin` | `StatusEffects.gd` |
| Tower/Castle/Hero/Minion/Boss stats | `BattleUnit.gd` |
| `HeroItemInventory` | `UnitInventory.gd` |
| `TacticalCommandManager` | `TacticalCommands.gd` |
| `SaveManager` + level stats/reward | `SaveRepository.gd` |
| `Menu` | `MenuView.gd` |
| `GameSettings` | `GameSettings.gd` |
| `ControllerManager` | `ControllerCore.gd`, `ControllerManager.gd` |
| `DevMode` | `DevMode.gd` |
| `mobile/cloud_save.py` payload | `CloudSaveCodec.gd`, `CloudSavePort.gd` |
| Top-up HTTP | `TopupPort.gd` |
| `topup_voucher.py` | `VoucherService.gd` |
| `topup_currency.py` | `CurrencyFormat.gd` |
| `UIRenderer`/`MapRenderer` | `ArenaView.gd` (native sederhana, bukan parity rig) |

## Perbedaan yang disengaja

- Save native ditulis ke `user://godot_core/slot_N.json`, bukan `saves/` Python.
  Import/restore Python dilakukan lewat payload cloud/backup eksplisit.
- Pengaturan native ditulis ke `user://godot_settings.cfg`; `settings.json` Python
  tidak ditimpa.
- Tidak ada embedded Python, GDExtension, atau plugin .NET.
- Layanan yang memerlukan kredensial/perangkat mengembalikan status tidak tersedia
  atau belum terverifikasi, bukan sukses palsu.
