"""Host-tool access to the shared firmware layout; not shipped on the device."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from firmware_paths import (ARTIFACTS, SOURCES, LVGL_SOURCES, OS_SOURCE, LVGL_WORK,
                            OS_WORK, STAGING, IMAGES, CHECKS, JOBS, ARCHIVE,
                            LVGL_HARDWARE_CHECKS, LVGL_HOST_CHECKS)

# Preserve the existing tool API while giving its work directory one clear home.
DIST = LVGL_WORK
