# Status & handoff — Godot Rebuild

Diperbarui: 26 September 2026 (Push C ditutup: Kaizen-1 prototipe). Pengguna memakai **Windows 11, Godot 4.7.2 standard** dan meminta implementasi langsung di repo.

## Aturan pekerjaan

- Gunakan proyek **`godot_rebuild/`**, bukan migrasi lama. Python/Pygame tetap referensi; jangan mengubahnya agar port lolos.
- Branch sesi **`arena/01a0db9f-mystic-arena`**, bercabang dari `main` pada merge `8a940fd` (PR #279). Jangan memakai branch sesi lama.
- [PR #278](https://github.com/dharmawantoxi/mystic-arena/pull/278) **sudah MERGED** ke `main` (`64e45e9`). Catatan historis yang menyebut PR #278 OPEN adalah status sebelum merge.
- Push checkpoint berkala ke branch sesi baru sebelum sesi habis; tidak ada indikator batas sesi yang pasti. Jangan menunggu batas sesi untuk push.
- Jangan mengklaim seluruh migrasi selesai karena laboratorium/prototipe ini berjalan.

## Checkpoint yang sudah dipush dan diverifikasi

| Commit | Cakupan | Bukti native |
|---|---|---|
| `f4a71ee` | Fondasi menu, sandbox, pause/restart, tests/CI | [CI fondasi](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36113676693) |
| `741b660` | Combat minion dan fixture sumber | [745 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36114379895) |
| `5d2d0e0` | Archer/nexus/projectile, oracle numerik | [1.072 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36116716287) |
| `d09ce35` | UI siege, hasil dan lifecycle | [1.158 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36117033161) |
| `e3b592d` | Dokumen siege/handoff | [1.158 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36117480660) |
| `868cfc2` → `a218073` | Wave otomatis, ledger, slot dan transaksi; perbaikan pembanding JSON tes | [1.418 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36151766743) |
| `ff5d2af` | Mode **Pertandingan awal**, HUD/build/sell/hasil dan lifecycle | [1.511 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36152202295) |
| `6e115e4` | Inti upgrade Archer 1–6, resource/refund/source volley | [1.879 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36153624268) |
| `7c96c83` | UI upgrade/refund, expected-level command, impact/overkill | [1.905 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36153883271) |
| `0078e79` | Kaizen-1 prototipe: QWER, dest/follow, hunt/push, retreat, heal, upgrade, respawn | [4.780 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36218349274) |
| `21dd08c` | Kaizen merah: spawn `(1120, 130)`, loop retreat/push/hunt/respawn, tanpa perintah pemain | [4.789 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36218605585) |
| `77801fb` | Auto-cast merah: R / E(2+) / W(<40%) / Q tiap 20 tick dalam skill_range | [4.796 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36218756768) |

Commit dokumentasi setelahnya tercatat di `git log`. Native HEAD Kaizen-1: run **36218349274**, PASS 4780.

## Yang tersedia saat F5

Import `godot_rebuild/project.godot` → F5; tidak perlu membuat scene/script manual.

- **Pertandingan awal**: subset level 1/normal, 1000 G, 9 slot biru, Archer 100 G, upgrade sampai level 6 / refund dinamis; wave otomatis; **Kaizen biru** (QWER, klik-kanan, hunt/push/retreat, upgrade, respawn); lawan sementara membeli tiga Archer berbayar; hasil nexus, pause/restart. Bukan AI asli, item, hero merah, atau seluruh level Python.
- **Tower & nexus**: enam Archer dan dua nexus, projectile/shield, wave manual satu/dua tim, hasil. Laboratorium ini tidak diganti prototipe.
- **Laboratorium minion**: tiga lane asli, lima tipe minion, combat/regen/death, wave manual, inspeksi.
- **Uji input**: sandbox penanda hijau untuk regresi input/lifecycle. Bukan hero hasil porting.
- **Keluar**.

## Validasi dan batas bukti

- Import + **1.905 native checks Godot 4.7.2** di GitHub Actions Linux telah lulus untuk UI prototipe. Termasuk suite fondasi/minion/siege, fixture wave/income/slots/build-sale, ledger, stale/dead/duplicate transactions, replay 4.200 tick, tiga lifecycle prototype serta kedua pemenang; ditambah upgrade/refund enam tier, 36 source volleys, cap/impact/overkill dan UI upgrade.
- Lokal: 585 guardrail, empat checker/oracle Python sumber, parser/lint/format GDScript. Scene/resource syntax juga diperiksa; parser pihak ketiga bukan pengganti engine.
- **Belum diuji:** tampilan GPU/screenshots, Windows fisik, resize visual, pertandingan manual panjang/balance, Android export, multi-touch HP, thermal/performa, save/cloud/pembayaran.
- Binary engine di sandbox gagal diunduh karena TLS host aset; jangan mengulang probe atau memakai binary tidak tepercaya. Bukti runtime melalui engine resmi yang dipin dalam CI.
- Log archive CI dapat gagal diunduh; hasil penting diterbitkan sebagai **Checks annotations**, bisa dibaca lewat `gh api`.
- Kegagalan pertama inti (6 dari 1.418 checks) disebabkan nested Array comparison terhadap angka float JSON. Sudah diperbaiki dengan perbandingan scalar exact, tanpa truncation/toleransi dan tanpa mengubah scheduler; CI sesudahnya lulus.

## File utama dan aturan penting

- [`../godot_rebuild/README.md`](../godot_rebuild/README.md): cara menjalankan di Windows dan checklist manual.
- [`COMBAT`](../godot_rebuild/COMBAT_CONTRACT.md), [`SIEGE`](../godot_rebuild/SIEGE_CONTRACT.md), [`MATCH`](../godot_rebuild/MATCH_CONTRACT.md), [`UPGRADE`](../godot_rebuild/UPGRADE_CONTRACT.md), [`NEXUS`](../godot_rebuild/NEXUS_CONTRACT.md): aturan sumber, batas scope, deviasi yang disengaja.
- `app/app.gd`: navigasi deferred/satu screen; `start_prototype`, `start_siege`, `start_combat`, `start_match` (sandbox). Restart terikat ke scene asal.
- `scripts/combat/`: RefCounted worlds, ID monotonic, satu death/credit, shield dan projectile. `structure_limit()` default 16, override prototipe 20. `UnitState.ai_level`, `StructureState.shield_max/purchased/free`, targeting AI 1–5.
- `scripts/match/`: `archer_upgrades` 1–6, `nexus_upgrades` 1–5 + scale/AI, `wave_scheduler` per-tim, `match_economy`, `slot_layout`, `build_slot`, `prototype_battle` (scaling saat spawn + `upgrade_nexus`).
- `scripts/simulation/prototype_session.gd`: immutable command IDs (build/sell/upgrade/nexus), satu command/tick, cancel saat pause/focus. Tidak ada manual wave dalam mode ini.
- `scenes/prototype/`: HUD empat tombol (build/sell/Archer/nexus), hasil otomatis, input berskala dan view read-only.
- `tests/nexus_source_oracle.py`, `nexus_checks.gd`, `nexus_scene_checks.gd`: tier/HP/shield/scaling/komposisi/AI dan UI lifecycle.
- `tests/upgrade_source_oracle.py`, `upgrade_checks.gd`, `upgrade_scene_checks.gd`: metode Archer/muzzle/volley dan UI lifecycle.
- `tests/match_source_oracle.py`: potongan AST sumber asli; `fixtures/match_source.json`; `prototype_checks.gd` dan `run_all.gd` untuk domain/lifecycle.
- `tests/check_source_contract.py`, `structure_source_oracle.py`: minion/lane serta metode numerik Tower/Castle.
- `.github/workflows/godot-rebuild.yml`: engine resmi 4.7.2, oracle/parser/lint, import + tes native. Memantau sumber kontrak termasuk `levels/level_data.py`.

Ringkasan aturan yang rawan salah:

- Wave pertama **tick 301**, queue tetap dikuras setiap 20 tick saat timer 1500 berjalan; wave berikutnya menunggu lapangan bersih. Komposisi per-tim: base tier nexus + scaling nomor wave; queue фиксирована saat wave start, scaling dibaca saat spawn.
- Level 1 normal **1000 G**; lawan 350 G. Passive milli-gold memakai ties-to-even Python; income sebelum scheduler. Jual tier 1 **50 G** berasal dari fallback UI, bukan `Tower.sell_value()` yang bernilai 0.
- Build/sale/upgrade harus validasi sebelum mutasi; dead/duplicate/stale tidak memberi refund/ganda. Death membebaskan slot (perbaikan bug sumber yang disengaja). Sale membatalkan projectile terkait tanpa kill reward.
- Lawan sementara membeli pada tick 300/600/900, bukan AIPlayer asli. Tidak ada castle auto-scaling (`_auto_scale_ai_castle` nonaktif), hero/boss, save, ekonomi permanen atau paid shield sebagai transaksi.
- Archer full heal/shield; nexus `int(new×ratio)+(new−old)` +500 cap, shield resize hanya-bila-purchased. Nexus shield dulu lalu reduksi 88%; wave 11 mematikan shield gratis bila belum dibeli.
- Minion lama tidak berubah retroaktif; AI tier dari nexus pemilik saat spawn. Urutan Godot ID stabil, bukan spatial-hash; quirk `tower_kind` sumber didokumentasikan.
- Batas prototipe: 120 minion / 20 struktur / 256 projectile / 64 event; antrean menahan spawn bila penuh. Hasil nexus membekukan economy/world dan membatalkan antrean.

## Tahap nexus: selesai di CI Linux (sesi baru)

Upgrade nexus biru 1–5 **bersama** scaling minion, AI tier 1–5, komposisi per-tier, dan aturan HP/shield — **lulus 3.418 native checks** Godot 4.7.2 di Linux.

| Commit (branch `arena/01a0d939-mystic-arena`) | Cakupan | Bukti native |
|---|---|---|
| `f80b411` | Oracle/fixture nexus (5 tier, 120 HP, 36 wave, 25 scaling, 5×10 komposisi, 20 AI) | [CI oracle](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36156238323) |
| `94778bf` + `1029828` | Domain + tes nexus (gagal import: konstanta ganda) | [gagal 36156714136](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36156714136), [gagal 36157084685](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36157084685) |
| `07b87ed` | Fix duplikat `StructureState` di `siege_battle` | [3.418 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36157214557), check-run `108144581314` |
| `4f2cfac` | Kontrak nexus + README/match/upgrade/handoff | [3.418 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36157499177), check-run `108145527681` |

Keputusan scope: lawan tetap builder terjadwal tanpa `_auto_scale_ai_castle` agar replay lama stabil. Paid shield belum transaksi UI; flag purchased hanya untuk resize shield. Hero/boss/AI penuh, tower selain Archer, 54 level tetap di luar scope. Windows/Android belum diuji langsung.

## Tahap cannon: selesai di CI Linux (sesi lanjutan)

Jalur Cannon 2–6 **bersama** splash 60% + burn DOT, muzzle sumber, dan pilihan jalur eksplisit — **lulus 3.713 native checks** Godot 4.7.2 di Linux.

| Commit (branch `arena/01a0d939-mystic-arena`) | Cakupan | Bukti native |
|---|---|---|
| `e17b717` | Oracle/fixture Cannon (path, 5 tier, muzzle 5×2, volley, splash 3 level, burn stacking + tick) | [CI oracle](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36203891056) |
| `57a83b5` + `8cf3352` + `1c5283a` | Domain + tes Cannon (tiga run gagal: edit hilang, inferensi tipe) | [gagal 36204165113](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36204165113), [gagal 36204324548](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36204324548), [gagal 36204407681](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36204407681) |
| `96e72a2` | Fix aritas burn test | [gagal 5/3688](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36204618819) → diperbaiki |
| `76a7676` | Burn tanpa cek tim + kredit via earned (paritas sumber) | [3.688 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36204725077) |
| `81765fd` | Tombol pilih jalur + scene checks UI/lifecycle | [3.713 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36204985361) |

Temuan yang dikunci: burn dps 8 memberi 3/5/4/4 (float exact); `burn_team` selalu ditimpa penerap terbaru; apply tanpa cek tim; kredit selalu ke lawan korban; splash inklusif + bangunan kebal; recoil muzzle tak terjangkau (0); argumen jalur diabaikan setelah level 1. Deviasi: splash lewat mitigasi physical Godot (sumber None) — pass school-None umum ditunda. Lawan tetap Archer; Ice/Mage, hero/boss/AI penuh, 54 level tetap di luar scope.

## Tahap ice: selesai di CI Linux (sesi lanjutan)

Jalur Ice 2–6 **bersama** slow gerak + attack-slow, AOE slow L6, muzzle kristal sumber, pilihan jalur eksplisit, dan tombol UI kontekstual — **lulus 4.035 native checks** Godot 4.7.2 di Linux.

| Commit (branch `arena/01a0d939-mystic-arena`) | Cakupan | Bukti native |
|---|---|---|
| `b68e3e9` | Oracle/fixture Ice (path, 5 tier, muzzle kristal 5×8 arah, volley 5×2 sisi, on-hit 3 level, stacking + tick + speed + attack-cd) | [CI oracle](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36206373550) |
| `d1a2644` | Domain + tes Ice (slow/atk-slow, muzzle f64, `_ice_impact` + AOE L6, 5 tier `.tres`, `ice_checks.gd`) | [4.008 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36206784333) |
| `3e8ad59` | Tombol Ice + visibilitas kontekstual + scene checks UI/lifecycle | [4.035 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36207205305) |

Temuan yang dikunci: `apply_slow`/`atk_slow` overwrite saat stronger ATAU longer (weaker+longer menimpa amount — quirk sumber); tick decrement lalu nolkan amount; `_eff_speed` f64 exact; attack-cd 45→53/60/75 dan 22→26/29/37; AOE L6 inklusif 80px tanpa damage ke korban AOE, ally/mati diskip; muzzle kristal x=500 face-independen + offset aim 5px dalam double (Vector2 f32 dilarang sebelum penjumlahan akhir). Skema UI: 6 tombol, Cannon/Ice visible ⟺ tower biru L1 dipilih, Nexus disembunyikan saat itu (maksimal 5 tampil).

## Tahap mage: selesai di CI Linux (sesi lanjutan)

Jalur Mage 2–6 **bersama** chain 2–4 tanpa refill, skill-down + anti-heal, muzzle kristal sumber, pilihan 4 jalur eksplisit, dan baris UI Paths — **lulus 4.452 native checks** Godot 4.7.2 di Linux.

| Commit (branch `arena/01a0d939-mystic-arena`) | Cakupan | Bukti native |
|---|---|---|
| `c10de78` | Oracle/fixture Mage (path, 5 tier, muzzle kristal 5×8 arah, volley chain 5×3, on-hit 3 level, stacking 2 debuff + tick + regen anti-heal) | [CI oracle](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36208070832) |
| `fbace74` | Domain + tes Mage (skill-down/anti-heal, chain tanpa refill, muzzle f64, `_mage_impact`, 5 tier `.tres`, `mage_checks.gd`) | [4.425 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36208534296) |
| `f1b80b9` | Tombol Mage + baris Paths + scene checks UI/lifecycle | [4.452 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36208792355) |

Temuan yang dikunci: chain melewati identitas-target/mati/luar-range sesuai urutan, cap chain, tanpa refill (solo = 1 bolt); semua bolt satu muzzle target utama; stack rule quirk sama (weaker+longer menimpa); anti-heal di setter HP dengan quirk cap-then-scale (44.8→44.9) dan full-block 1.0 di L6; mati = clear debuff; skill-down tanpa efek pada minion (konsumen `Hero.skill_damage` di luar scope). UI: 7 tombol dua baris, Paths visible ⟺ tower biru L1, Nexus menyingkir (maksimal 6 tampil). Keempat jalur tower selesai; berikutnya hero/skill + AI.

## Langkah berikutnya

1. Uji Windows F5 → **Pertandingan awal** (Kaizen QWER, klik-kanan, retreat/push, upgrade, respawn).
2. Kaizen-1 prototipe ditutup di `HERO_CONTRACT.md`. Jangan klaim 6 hero / item / AIPlayer.
3. Berikutnya: hero starter kedua **atau** ganti lawan Archer terjadwal setelah AI sumber diuji. 54 level, Android, audio tetap di luar.
4. Lengkapi satu pertandingan kecil, lalu level/boss/konten/UI/audio. Android pilot dan profiling harus dibuktikan pada perangkat, bukan dengan headless Linux.
5. Push bertahap pada branch sesi baru, pantau CI dan perbarui handoff ini.

## Perintah praktis

```text
python godot_rebuild/tests/validate_project.py
python godot_rebuild/tests/check_source_contract.py
python godot_rebuild/tests/structure_source_oracle.py
python godot_rebuild/tests/match_source_oracle.py
python godot_rebuild/tests/upgrade_source_oracle.py
python godot_rebuild/tests/nexus_source_oracle.py
gh run list --branch arena/01a0d939-mystic-arena --limit 5 --json databaseId,status,conclusion,headSha,url
gh api repos/dharmawantoxi/mystic-arena/check-runs/CHECK_ID/annotations
git push origin arena/01a0d939-mystic-arena
```

Windows: `powershell -ExecutionPolicy Bypass -File .\tests\run_windows.ps1 -Godot "C:\Tools\Godot_v4.7.2-stable_win64_console.exe"` dari `godot_rebuild/`.

`gh pr edit` pada versi CLI sandbox pernah gagal karena Projects classic deprecated. Gunakan REST PATCH `gh api --method PATCH repos/dharmawantoxi/mystic-arena/pulls/278` untuk title/body. Jangan menyimpan credential, binary engine, `.godot/`, save nyata atau output build di repo. Jangan menjalankan generator migrasi lama atau scratch script lama yang dapat menimpa proyek ini.

## Detail milestone upgrade (sudah native-verified)

- [Kontrak upgrade Archer](../godot_rebuild/UPGRADE_CONTRACT.md) memuat angka tier, behavior dan dependency nexus.
- Harga masuk tier 2–6: **175/325/550/850/1300 G**. Refund tier 1–6: **50/87/250/525/950/1600 G**, tidak memasukkan biaya build pada tier 2+.
- Archer upgrade memulihkan HP/shield penuh, tetapi mempertahankan cooldown, target, regen clock dan projectile lama. Resource shared tidak dimutasi; projectile lama tetap memakai damage lama.
- Source `_shoot_archer`: level 5 **dua** panah; level 6 **tiga**, bukan “double” menurut label data. Target tambahan mengikuti urutan source; kekurangan target diisi target utama. Cap volley atomik tambahan keselamatan.
- UI menangkap ID **dan expected level** untuk upgrade. Klik ganda/stale/paused/dead/poor/enemy/max/result tidak menggandakan biaya atau membeli level tanpa persetujuan. Sale message menampilkan refund aktual.
- Lawan sementara tetap tiga Archer level 1 berbayar, tanpa upgrade otomatis. Laboratorium tidak mendapat tombol upgrade.
- Nexus belum diaktifkan: HP formula berbeda, shield resize hanya jika purchased, minion scale/AI tier berubah. Queue source menyimpan kind/lane; tier stat dibaca ketika spawn, composition saat wave start. Minion lama tidak boleh ikut berubah secara retroaktif.
- Checkpoint inti dan UI **keduanya lulus**. Tidak ada fitur upgrade yang masih menunggu CI pada checkpoint UI `7c96c83`; verifikasi HEAD dokumentasi lewat run terbaru.
