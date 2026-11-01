"""Isolated LVGL entry point over the pinned original application main().

Temporary deployment only: no launcher installation, firmware writing or flashing.
"""
import argparse
import hashlib,json
import importlib.util
import os
from pathlib import Path
import sys
from contextlib import ExitStack,contextmanager
import signal

def options(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app-root',default='/opt/src',type=Path)
    parser.add_argument('--camera-root',default='/usr/lib/shieldsigner-camera/python',type=Path)
    parser.add_argument('--binary',default='/tmp/shieldsigner-lvgl-host',type=Path)
    parser.add_argument('--locale-root',type=Path,help='Verified pinned locale asset directory')
    parser.add_argument('--native-manifest',type=Path,help='Native build manifest; defaults to BINARY.manifest.json')
    parser.add_argument('--settings',required=True,type=Path,help='Separate LVGL settings file; original settings are rejected')
    parser.add_argument('--check',action='store_true',help='Verify source/settings paths without acquiring devices')
    parser.add_argument('upstream',nargs=argparse.REMAINDER,help='Original app arguments after --')
    args=parser.parse_args(argv)
    if args.upstream[:1]==['--']:args.upstream=args.upstream[1:]
    if not args.settings.is_absolute():parser.error('--settings must be absolute')
    return args

def manifest_path():
    here=Path(__file__).resolve().parent
    return here/'source-guards.json' if (here/'source-guards.json').exists() else here.parent/'source-guards.json'

def check_settings_destination(destination,original):
    destination=Path(destination);original=Path(original)
    if not destination.is_absolute():raise ValueError('Settings destination must be absolute')
    if destination.resolve()==original.resolve():raise ValueError('LVGL requires separate settings')
    if destination.is_symlink():raise ValueError('LVGL settings must not be a symlink')
    if destination.exists():
        if not destination.is_file():raise ValueError('Settings destination must be a regular file')
        if original.exists() and os.path.samefile(destination,original):raise ValueError('Settings destination aliases original settings')
    if not destination.parent.is_dir():raise ValueError('Settings directory unavailable')

def verify_native_artifact(binary,manifest):
    metadata=json.loads(Path(manifest).read_text())
    if not isinstance(metadata,dict) or metadata.get('target')!='arm-linux-musleabihf' or not isinstance(metadata.get('inputs'),dict) or not metadata['inputs']:
        raise ValueError('Invalid native build manifest')
    digest=hashlib.sha256()
    with Path(binary).open('rb') as source:
        for chunk in iter(lambda:source.read(65536),b''):digest.update(chunk)
    if digest.hexdigest()!=metadata.get('binarySha256'):raise ValueError('Native artifact hash mismatch')
    return metadata

def check(args):
    from guards import verify
    count=verify(args.app_root,manifest_path())
    if not args.binary.is_file() or not os.access(args.binary,os.X_OK):raise ValueError('Native executable unavailable')
    verify_native_artifact(args.binary,args.native_manifest or args.binary.with_name(args.binary.name+'.manifest.json'))
    sys.path.insert(0,str(args.app_root.resolve()))
    from seedsigner.models.settings import Settings
    check_settings_destination(args.settings,Settings.SETTINGS_FILENAME)
    return count

def check_owners(proc=Path('/proc')):
    """Refuse competing Python/camera/LVGL owners; never stop another app."""
    for path in proc.iterdir():
        if not path.name.isdigit() or int(path.name)==os.getpid():continue
        try:argv=(path/'cmdline').read_bytes().split(b'\0')
        except (FileNotFoundError,PermissionError,ProcessLookupError):continue
        if not argv or not argv[0]:continue # Kernel/zombie tasks have no argv.
        name=Path(os.fsdecode(argv[0])).name
        if name.startswith('python') or name in ('shieldsigner-lvgl-host','shieldsigner-qr-reader') or b'stream-sc3336' in argv:
            raise RuntimeError('Another application/camera owner is running')

def stop_workers(controller):
    """Attempt every owned worker even if a sibling's stop/join fails."""
    if controller is None:return
    workers=[];seen=set();failed=[]
    for name in ('toast_notification_thread','battery_hat','wipe_timer_thread','rng_monitor_thread','microsd'):
        worker=getattr(controller,name,None)
        if worker is not None and id(worker) not in seen:
            seen.add(id(worker));workers.append((name,worker))
    for name,worker in workers:
        try:
            if hasattr(worker,'stop') and hasattr(worker,'is_alive') and worker.is_alive():worker.stop()
        except Exception:failed.append(name+':stop')
    for name,worker in workers:
        try:
            if hasattr(worker,'join') and hasattr(worker,'is_alive') and worker.is_alive():
                worker.join(3)
                if worker.is_alive():failed.append(name+':alive')
        except Exception:failed.append(name+':join')
    if failed:raise RuntimeError('Application shutdown incomplete: '+', '.join(failed))

@contextmanager
def termination_signals():
    """Use Python unwinding for service stop; repeated TERM cannot split cleanup."""
    previous=signal.getsignal(signal.SIGTERM);requested=[False]
    def terminate(signum,frame):
        if not requested[0]:
            requested[0]=True
            raise KeyboardInterrupt('Application termination requested')
    signal.signal(signal.SIGTERM,terminate)
    try:yield
    finally:signal.signal(signal.SIGTERM,previous)

def run(args):
    check(args)
    if args.check:return
    check_owners()
    from dependency_policy import install as dependencies
    restore=dependencies(args.app_root,manifest_path())
    try:return run_application(args)
    finally:restore()

def run_application(args):
    from startup_policy import install as startup
    startup(str(args.app_root),str(args.camera_root))
    from seedsigner.models.settings import Settings
    Settings.SETTINGS_FILENAME=str(args.settings)
    from seedsigner.gui.renderer import Renderer
    import seedsigner.gui.toast as toast
    from luckfox import LuckfoxHardware
    from runtime import Runtime,install_view_dispatch
    from renderer_bridge import install as renderer
    from toast_bridge import install as toasts
    from lifecycle import install as lifecycle
    from screensaver_bridge import install as screensaver
    from seedsigner.controller import Controller
    with ExitStack() as stack:
        stack.enter_context(termination_signals())
        hardware=LuckfoxHardware();stack.callback(hardware.close)
        runtime=Runtime(str(args.binary),hardware.pixels,hardware.read_buttons,hardware.buttons.update_last_input_time,locale_root=args.locale_root)
        stack.callback(runtime.close)
        stack.callback(install_view_dispatch(runtime,args.app_root,manifest_path()))
        stack.callback(renderer(runtime,hardware,Renderer))
        stack.callback(toasts(runtime,toast))
        stack.callback(lifecycle(runtime,Controller))
        from microsd_lifecycle import install as microsd_lifecycle
        from seedsigner.hardware.microsd import MicroSD
        stack.callback(microsd_lifecycle(MicroSD,args.app_root,manifest_path()))
        original_start=Controller.start
        def start(controller,*positional,**keywords):
            with ExitStack() as local:
                local.callback(screensaver(runtime,controller))
                return original_start(controller,*positional,**keywords)
        Controller.start=start
        stack.callback(setattr,Controller,'start',original_start)
        # Execute the reviewed original CLI/logging/startup decisions unchanged.
        spec=importlib.util.spec_from_file_location('_shieldsigner_original_main',args.app_root/'main.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        try:module.main(args.upstream)
        finally:
            # Original Controller stops its workers; join before restoring native
            # adapters or closing GPIO to prevent late worker/device access.
            try:stop_workers(Controller._instance)
            finally:
                # Use original persistence gating/locking/fsync behavior. A
                # pending daemon save must not be lost when this process exits.
                if Settings._instance is not None:Settings._instance.flush_save()

if __name__=='__main__':
    run(options())
