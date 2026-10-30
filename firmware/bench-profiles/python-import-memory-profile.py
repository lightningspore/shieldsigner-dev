#!/usr/bin/env python3
"""ARM image import allocations under explicit qemu-user; no hardware or RSS claim.

Run the image's own Python with its library paths, passing ROOTFS OUTPUT.
Emulation provides room for diagnostic snapshots, not target RAM measurements.
Exports code paths, type names and counts only, never object values.
"""
import importlib
import json
from pathlib import Path
import sys
import tracemalloc

root = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2]); output.mkdir(parents=True, exist_ok=False)
sys.path[:0] = [str(root/'usr/lib/shieldsigner-camera/python'), str(root/'opt/src')]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import importlib.util
spec = importlib.util.spec_from_file_location('memory_profile',Path(__file__).with_name('python-memory-profile.py'))
profile = importlib.util.module_from_spec(spec);spec.loader.exec_module(profile)
profile.proc_memory = lambda: {}  # /proc is the host's QEMU process, not board PSS.
def source_name(name):
    if name.startswith(str(root)+'/'):
        return name[len(str(root))+1:]
    if name.startswith(('/usr/lib/python3.12/', '/opt/src/', '/usr/lib/shieldsigner-camera/python/')):
        return name.lstrip('/')
    if name.startswith('<frozen ') and name.endswith('>'):
        return name
    if name.startswith(str(Path(__file__).parent)+'/'):
        return '<profiler>'
    return '<runtime-or-other>'
profile.source_name = source_name
stages = [
    ('baseline', []),
    ('entry_imports', ['main']),
    ('startup_routes', ['seedsigner.views.smartcard_views', 'seedsigner.views.screensaver', 'seedsigner.views.desktop_warning', 'seedsigner.views.developer_os_warning', 'seedsigner.helpers.seedsigner_os', 'seedsigner.gui.toast']),
    ('scan_imports', ['seedsigner.views.scan_views']),
    ('seed_views', ['seedsigner.views.seed_views']),
    ('tools_views', ['seedsigner.views.tools_views']),
    ('settings_views', ['seedsigner.views.settings_views']),
    ('smartcard_views', ['seedsigner.views.smartcard_views']),
]
tracemalloc.start(1)
for phase, modules in stages:
    try:
        if phase == 'entry_imports':
            integration = importlib.import_module('shieldsigner_integration')
            integration.ensure_app_import_root(root/'opt/src')
            integration.configure_lcd_backend(root/'opt/src', 'rust')
            integration.install_camera_backend(root/'opt/src')
            integration.install_small_ram_profile(root/'opt/src')
            integration.install_lazy_scan_views(root/'opt/src')
        for module in modules:
            importlib.import_module(module)
        profile.report(phase, output)
        path = output/(phase+'.json'); record=json.loads(path.read_text())
        record['scope']='Actual packed ARM Python import graph under qemu-user; no Controller initialization, hardware, live GUI or target RSS measurement.'
        path.write_text(json.dumps(record,indent=2)+'\n')
    except Exception as error:
        (output/(phase+'-error.json')).write_text(json.dumps({'phase':phase,'errorType':type(error).__name__})+'\n')
        raise
