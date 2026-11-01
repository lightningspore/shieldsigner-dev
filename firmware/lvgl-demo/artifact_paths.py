"""Host-only locations for the historical isolated LVGL experiment."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from firmware_paths import DEMO_WORK
