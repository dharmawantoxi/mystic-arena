"""DEPRECATED wrapper.

Old version baked 8 copies of thorne_attack.png (club frozen overhead).
Swing frames now come from tools/process_thorne_anim.py so the club actually
travels hip → overhead → down → impact → hip.
"""
import os
import runpy
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, "tools", "process_thorne_anim.py")
print("make_hd_swing.py is deprecated; running process_thorne_anim.py")
sys.argv[0] = TARGET
runpy.run_path(TARGET, run_name="__main__")
