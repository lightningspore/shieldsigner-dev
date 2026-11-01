"""Canonical locations for generated firmware artifacts; paths do not create files."""
from pathlib import Path
import argparse
import json

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / 'dist/firmware'
SOURCES = ARTIFACTS / 'sources'
LVGL_SOURCES = SOURCES / 'lvgl'
OS_SOURCE = SOURCES / 'seedsigner-os'
LVGL_WORK = ARTIFACTS / 'work/lvgl'
DEMO_WORK = ARTIFACTS / 'work/lvgl-demo'
OS_WORK = ARTIFACTS / 'work/os'
STAGING = ARTIFACTS / 'staging'
IMAGES = ARTIFACTS / 'images'
CHECKS = ARTIFACTS / 'checks'
JOBS = ARTIFACTS / 'jobs'
ARCHIVE = ARTIFACTS / 'archive'
LVGL_HARDWARE_CHECKS = CHECKS / 'lvgl/hardware'
LVGL_HOST_CHECKS = CHECKS / 'lvgl/host'

PATHS = {
    'root': ROOT,
    'artifacts': ARTIFACTS,
    'sources': SOURCES,
    'lvgl-sources': LVGL_SOURCES,
    'os-source': OS_SOURCE,
    'lvgl-work': LVGL_WORK,
    'demo-work': DEMO_WORK,
    'os-work': OS_WORK,
    'staging': STAGING,
    'images': IMAGES,
    'checks': CHECKS,
    'jobs': JOBS,
    'archive': ARCHIVE,
    'lvgl-hardware-checks': LVGL_HARDWARE_CHECKS,
    'lvgl-host-checks': LVGL_HOST_CHECKS,
}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('key', nargs='?', choices=sorted(PATHS))
    parser.add_argument('--json', action='store_true', help='Print the complete path map')
    args = parser.parse_args()
    if args.json:
        print(json.dumps({key: str(value) for key, value in PATHS.items()}, indent=2))
    elif args.key:
        print(PATHS[args.key])
    else:
        parser.error('Choose a path key or --json')

if __name__ == '__main__':
    main()
