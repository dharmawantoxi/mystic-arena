# L29 — fix regresi heartbeat (dedent _flame_t) — DONE
# BUKAN append: perbaiki INDENT di func _process.
# Bug: `_flame_t += delta` ikut Tab di dalam `if wave_timer <= 0.0`
#   → torch/rune/asap/firefly/fog hanya update saat wave spawn.
# Fix: dedent `_flame_t += delta` ke level yang sama dengan `gold += ...`
#      (1 Tab, sejajar wave_timer -= delta).

# ═══════════════════════════════════════════
# LANGKAH 29 — ganti SELURUH func _process
# ═══════════════════════════════════════════
func _process(delta: float) -> void:
	if match_over or level_data.is_empty():
		return
	gold += INCOME_PER_SEC * delta
	wave_timer -= delta
	if wave_timer <= 0.0:
		wave_count += 1
		_spawn_wave(wave_count)
		wave_timer = wave_interval
	_flame_t += delta
	if _flame_t >= 0.15:
		_flame_t = 0.0
		_flame_frame = (_flame_frame + 1) % 4
		_anim_t += 9.0
		queue_redraw()
