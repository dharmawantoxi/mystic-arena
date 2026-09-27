# Checkpoint migrasi native Godot — 167/222 teruji, 55 pending

Target tetap **222**. Sesi dari merge `50b7c07` (164/222).
Branch `arena/01a0e1cb-mystic-arena`, PR draft
[#287](https://github.com/dharmawantoxi/mystic-arena/pull/287). **Jangan merge.**

**Status batch 9: LULUS. 167/222 playable teruji, 55 pending.**
Kode terakhir `8fc39ee98c10d423164bdcd04278b9de5608d4cd` sudah push.
CI [36305280464](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36305280464), Godot **4.7.2**, **457372 checks**;
import, seluruh run_all lama/baru, scene/input/lifecycle PASS.
Lokal **4596 static PASS**, source-contract, semua *_oracle.py,
gdparse/gdlint/gdformat **4.5.0** PASS. Tidak ada kit WIP terdaftar.

Evaluasi kapasitas: tiga batch selesai dan teruji; tidak membuka kit berikutnya
sebelum handoff agar tidak meninggalkan implementasi parsial. Nyxarath hanya
dibaca/audit awal (belum ada handler/resource/registration baru). Blocker engine
lokal tetap TLS; CI resmi hijau. Langkah berikut: selesaikan sisa level6
Gravewake/Syrentha/Thalgryn, kemudian Nyxarath dan pending level7. Target222
belum selesai. Lanjut otomatis tiap batch lulus, tanpa meminta persetujuan.

Daftar tepat selesai/pending, harga summon, level, recipe dan bukti pengujian:
[HERO_ROSTER_STATUS.md](HERO_ROSTER_STATUS.md),
[`data/ai/hero_migration_status.json`](data/ai/hero_migration_status.json).
Registry eksplisit `scripts/data/hero_roster.gd`.

## Batch sesi ini

| Batch | Kit | Total / pending | Commit | CI Godot 4.7.2 |
|---|---|---|---|---|
| Baseline merge PR #285 | AA/Nyzrak/Ignis dan 161 sebelumnya | 164 / 58 | 50b7c07 | [413735](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36302839552) |
| 7 | Krobellus 1500G, level5 | 165 / 57 | 64633eb | [427984](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36304115611) |
| 8 | Vhalzun 1200G, level5 | 166 / 56 | 5492a87 | [442071](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36304610944) |
| 9 | Kunkka 900G, level6 | **167 / 55** | 8fc39ee | [457372](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36305280464) |

Setiap batch sebelumnya sudah commit+push setelah seluruh validasi lokal,
dan CI hijau sebelum mulai batch berikut. Engine lokal tidak tersedia:
unduh official 4.7.2 gagal TLS `release-assets.githubusercontent.com`.
Runtime/import/run_all dijalankan workflow resmi, bukan klaim runtime lokal.

## Perilaku yang dikunci

- **Krobellus:** Q150/1,5×; W120/1×/attack timer max75; E selected 1,3×
  + heal0,5× skill; R200/2,5× + heal15%. Tanpa ghost DOT/silence state baru.
- **Vhalzun:** Q130/1,5×; W150/1×/stun max60; E selected1,8× tanpa
  execute/threshold/heal; R150/1,4× + heal18%. Tanpa shield/immunity/DOT.
  W visual override **80**, bukan default90.
- **Kunkka:** Q strip strict 0<projection<250 dan perp<70, 1,8×;
  W target-centered120/1,5×/max60; E strict strip300/80, 2,2×/max90,
  heal15% hanya jika target tidak overlap; R target-centered200/3×/max120
  + heal20%. Tidak ada X return teleport, ship projectile, rum mitigation
  atau torrent delay yang tidak dikonsumsi sumber.
- Final visual Krobellus/Kunkka **60/90/60/100**. Cooldown W240/E420/R900;
  Q dari constructor sumber. Cooldown trigger menimpa visual recipe.
- Source ketiga kit memakai hit **netral tanpa source/school**, bukan
  otomatis magic/physical caster. Hero Thorne dan Tower asli membuktikan
  school, mitigasi, reflect dan tower tanpa attack_timer. Basic attack
  tetap sekolah caster: Krobellus/Vhalzun homing, Kunkka melee.
- Oracle `source_env` + state capture menjalankan recipe Python asli,
  clocks/projectiles/respawn/upgrade, tidak menyalin arithmetic ke oracle.
  Semua boundary, selected vs nearest, dead/friendly filtering, stun max,
  cooldown exact recast, move/upgrade/retarget/death traces, heal cap sebelum
  anti-heal Lv1/2/15, lifecycle/roster diuji native. Tambahan Kunkka: strip
  mirrored/vertical/diagonal, origin overlap, target-centered radial edges.
- `.tres` dari balanced `_core.get_all_hero_types` + constructor Hero
  (normalisasi/catchup), **bukan raw catalog**. Field speed/range/cooldown/
  HP/damage/skill/school/melee sekarang juga dibandingkan di native tests.
- 501 transaksi source (167 × harga−1/tepat/+1), upgrade boss1,6×,
  Lv1→2 **480G**, reserve±1, hidup/mati, registry dan clock tetap diuji.
  AA/Nyzrak/Ignis kini juga masuk oracle pembelian + Hero/Tower lintas-kit.

## Scope dan quirk yang wajib tetap

Hanya `godot_rebuild/`; Python asli read-only. QWER, basic, target selection,
radius, source/school, timer/lifecycle/upgrade/harga/quirk tetap. Kaizen gratis
kedua tim dan defender scene tetap. Tanpa item/forge, AIPlayer penuh,
rebalance, refactor besar atau art final; visual prosedural sederhana.
150 shared-source adalah allowlist tertutup berbukti dispatch sumber, bukan
izin fallback untuk pending. Handler tiga kit baru tersendiri, hanya target
gate, primitive hit/stun/heal dan harness perbandingan yang sama dipakai ulang.
AA w_dir/r_dir tetap di-set; Nyzrak shield_active tidak memberi mitigasi;
Ignis dragon_blood expiry tidak reset damage. Assertion lama tidak dikurangi.

**Sentinel pending:** batch7–8 tetap Kunkka900G. Karena Kunkka selesai batch9,
`ai_recruit_checks` dan `source_shared_boss_checks` sekarang memakai
**Gravewake1000G**, dengan assertion eksplisit masih pending. Gold1000/1100
cukup, sehingga penolakan menguji kit, bukan kurang uang. Semua 55 pending
juga diuji dengan100000G: tanpa debit, spawn parsial, atau substitusi.

## Daftar pending tepat dan koreksi checkpoint lama

Daftar informal di pesan lama bukan manifest aktual: Vhorethzir sudah
shared-source playable; Naraka2000G, Aurethzar2100G, dst. Jangan mengubah harga
sumber atau mengulang migrasi ID shared-source yang sudah terbukti.
Level5 sekarang selesai. Selanjutnya sisa level6 lalu level7 Nyxarath dkk:

- Level 6: `gravewake` 1000G, `syrentha` 1100G, `thalgryn` 1200G.
- Level 7: `akashari` 1200G, `malzareth` 1100G, `nyxarath` 1000G, `vorenmarr` 1300G.
- Level 9: `kenshiro` 1300G, `khazan` 1350G, `naraka` 2000G, `wiro` 1300G.
- Level 10: `aurethzar` 2100G, `krognarr` 1400G, `raz` 1400G, `vraskhan` 1400G.
- Level 11: `aeralith` 1450G, `aurex` 1500G, `nyxareva` 1500G, `thalakryon` 2200G.
- Level 12: `aurelix` 1550G, `aurelyssa` 1550G, `nazulmor` 2300G, `vargrath` 1600G.
- Level 13: `kaeldris` 1650G, `pyraklos` 1700G, `solvarin` 2400G, `velmyrth` 1700G.
- Level 14: `azureth` 1700G, `luminar` 1750G, `pyraethis` 2500G, `solara` 1800G.
- Level 15: `auroth` 1850G, `morvein` 1900G, `thorvak` 1950G, `yamako` 2600G.
- Level 16: `ignirus` 2000G, `leoric` 2050G, `seiryukong` 2700G, `shirotaka` 2100G.
- Level 17: `kaelthorn` 2150G, `nyxareth` 2800G, `solvanth` 2200G, `xyrael` 2250G.
- Level 18: `aurelion` 2900G, `cryssalia` 2300G, `kaelthar` 2350G, `morkhaera` 2400G.
- Level 19: `akahime` 2450G, `nyxthrael` 2500G, `sylvantheros` 2550G, `vaelindra` 3000G.
- Level 20: `astraelion` 2600G, `morthraxis` 3100G, `morvaenthir` 2650G, `thornvaegrim` 2700G.

Blocker 55 pending: recipe khusus belum diport dan belum punya source-execution
oracle/native behavior test. Jangan daftarkan baseline angka/metadata saja.
Tidak ada pengurangan target, tidak ada klaim 222 selesai.

## Validasi sebelum handoff

```sh
python godot_rebuild/tests/validate_project.py
python godot_rebuild/tests/check_source_contract.py
for t in godot_rebuild/tests/*_oracle.py; do python "$t" || exit; done
# *_oracle.py juga mencakup source_shared_boss_oracle.py
export PATH="$PWD/godot_rebuild/.venv/bin:$PATH" # gdtoolkit==4.5.0 lokal
 gdparse $(find godot_rebuild -name '*.gd')
 gdlint $(find godot_rebuild -name '*.gd')
 gdformat --check $(find godot_rebuild -name '*.gd')
# Godot 4.7.2 melalui CI bila engine tidak bisa diunduh lokal:
 godot --headless --path godot_rebuild --editor --import
 godot --headless --path godot_rebuild --script res://tests/run_all.gd
```

Batch8 lokal: **4556 static PASS**, source-contract, seluruh oracle,
gdparse/gdlint/gdformat4.5.0. Batch9 lokal: **4596 static PASS**, source-contract, seluruh *_oracle.py,
gdparse/gdlint/gdformat4.5.0 PASS. CI engine **457372 PASS**.
Oracle --write hanya untuk regenerate dari eksekusi sumber; jangan mengedit
fixture manual demi meloloskan drift. Setiap batch: oracle → resource →
handler/state → combat/transaksi/run_all → static/oracle/lint → commit/push →
CI; perbaiki kegagalan sebelum mulai batch berikut. Update manifest dan docs.

## Pesan siap-salin untuk newchat

> Lanjutkan migrasi native Godot dari PR **draft #287**, branch
> `arena/01a0e1cb-mystic-arena`, **bukan hanya main 50b7c07**.
> Kode teruji `8fc39ee` (checkpoint docs commit sesudahnya juga perlu diambil).
> Saat ini **167/222 playable teruji / 55 pending**. Sesi ini menyelesaikan
> Krobellus1500G, Vhalzun1200G, Kunkka900G. CI Godot4.7.2 **457372 checks**:
> https://github.com/dharmawantoxi/mystic-arena/actions/runs/36305280464
> Lokal static **4596 PASS**, source-contract, semua oracle, gdtoolkit4.5.0
> parser/lint/format PASS. Tidak ada WIP terdaftar, belum merge.
>
> Baca HERO_MIGRATION_PROGRESS.md, HERO_ROSTER_STATUS.md, manifest
> data/ai/hero_migration_status.json dan kontrak. **Daftar/harga informal lama
> salah sebagian**: Vhorethzir sudah shared-source playable; gunakan manifest
> + sumber asli. Selanjutnya sisa level6 Gravewake1000G, Syrentha1100G,
> Thalgryn1200G, kemudian Nyxarath1000G dan pending level7.
>
> Hanya ubah godot_rebuild; Python asli read-only. Target tetap222, tanpa
> fallback generik untuk pending. Oracle harus menjalankan source_env + state
> capture asli, .tres balanced dari core+constructor, handler per perilaku,
> tes cast/traces/basic/respawn/roster/transaksi. Pertahankan QWER/target/radius/
> school/source/cooldown/timer/lifecycle/upgrade/harga/quirk; boss upgrade480G.
> Kaizen gratis + defender tetap, tanpa item/forge, AIPlayer penuh, rebalance,
> refactor besar atau art final. AA directions, Nyzrak shield tanpa mitigasi,
> Ignis dragon_blood tidak reset damage tetap.
>
> **Kunkka kini playable**: sentinel penolakan ai_recruit/source_shared sudah
> pindah ke **Gravewake1000G**, dengan assert masih pending. Jangan kembalikan
> tes penolakan ke Kunkka/AA/Nyzrak/Ignis yang playable. 55 pending ditolak
> tanpa debit, spawn parsial, atau substitusi. Semua suite lama, semua
> *_oracle.py (termasuk source_shared_boss_oracle.py), validate_project,
> source-contract, gdtoolkit4.5.0 dan CI Godot4.7.2 wajib lulus sebelum batch
> berikutnya. Sandbox gagal unduh engine TLS, runtime dilakukan CI resmi.
>
> Gunakan branch Arena sesi yang ditetapkan sistem; ambil checkpoint PR287
> dulu jika checkout baru masih main. PR draft, commit+push tiap batch
> teruji, jangan merge tanpa perintah eksplisit. Update manifest/roster/docs
> dan jumlah sisa tiap batch. Sebelum konteks habis: validasi, simpan daftar
> tepat dan blocker/receipt CI/next steps, commit+push, verifikasi remote dan
> gh run list, berikan pesan lanjut. Jangan mendaftarkan WIP atau mengklaim222.

**55 ID pending tepat (harga/level pada tabel di atas):**

`gravewake`, `syrentha`, `thalgryn`, `akashari`, `malzareth`, `nyxarath`, `vorenmarr`, `kenshiro`, `khazan`, `naraka`, `wiro`, `aurethzar`, `krognarr`, `raz`, `vraskhan`, `aeralith`, `aurex`, `nyxareva`, `thalakryon`, `aurelix`, `aurelyssa`, `nazulmor`, `vargrath`, `kaeldris`, `pyraklos`, `solvarin`, `velmyrth`, `azureth`, `luminar`, `pyraethis`, `solara`, `auroth`, `morvein`, `thorvak`, `yamako`, `ignirus`, `leoric`, `seiryukong`, `shirotaka`, `kaelthorn`, `nyxareth`, `solvanth`, `xyrael`, `aurelion`, `cryssalia`, `kaelthar`, `morkhaera`, `akahime`, `nyxthrael`, `sylvantheros`, `vaelindra`, `astraelion`, `morthraxis`, `morvaenthir`, `thornvaegrim`.
