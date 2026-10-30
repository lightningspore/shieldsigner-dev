"""Opt-in entry point: use Rust camera capture without editing installed app files."""
import argparse
import difflib
import hashlib
import importlib
import importlib.util
import io
import json
import linecache
import os
from pathlib import Path
import runpy
import sys
import types

CAMERA_SOURCE_SHA256 = "7cf9c67797d5b14cfbea206e91bc5c85292ec01f36fca68edbaee13977a5809e"
REPLACEMENTS = (
    ("from seedsigner.hardware.pivideostream import PiVideoStream",
     "from shieldsigner_video_stream import PiVideoStream"),
    ("return img.rotate(90 + self._camera_rotation)",
     "return img.rotate(90 + self._camera_rotation, expand=True)"),
)
IMAGE_CAMERA_SOURCE_SHA256 = "f5a927cdf7fd99f9c21aff793b540f59c1e9523a8945daaec96e1cb35375f6f2"
CAMERA_PROFILES = {
    CAMERA_SOURCE_SHA256: [(before, after, 1) for before, after in REPLACEMENTS],
    IMAGE_CAMERA_SOURCE_SHA256: [
        ("        if self._video_stream is not None:\n            self._video_stream.stop()\n            self._video_stream = None\n",
         "        stream = self._video_stream\n        if stream is not None:\n            try:\n                stream.stop()\n            finally:\n                if self._video_stream is stream:\n                    self._video_stream = None\n", 1),
        ("self._capture = VideoStream(\n                resolution=luckfox_config[\"resolution\"],",
         "self._capture = VideoStream(\n                for_still=True,\n                resolution=luckfox_config[\"resolution\"],", 1),
        ("from seedsigner.hardware.pivideostream import VideoStream",
         "from shieldsigner_camera_compat import VideoStream", 2),
        ("return image.rotate(90 + self._camera_rotation)",
         "return image.rotate(90 + self._camera_rotation, expand=True)", 2),
    ],
}


def install_qr_fallback(decoder):
    """Retry a missed PIL frame in memory; keep raw successes and payloads intact."""
    from PIL import Image
    marker = "__shieldsigner_qr_fallback__"
    existing = getattr(decoder, marker, None)
    if existing is not None:
        return existing
    original = decoder.extract_qr_data
    stats = {"kind": "jpeg85-after-no-raw-symbol", "attempts": 0, "successes": 0}

    def extract(image, is_binary=False):
        data = original(image, is_binary=is_binary)
        if data is not None or not isinstance(image, Image.Image):
            return data
        stats["attempts"] += 1
        with io.BytesIO() as buffer:
            prepared = image if image.mode in ("RGB", "L") else image.convert("RGB")
            prepared.save(buffer, format="JPEG", quality=85, subsampling=0)
            buffer.seek(0)
            with Image.open(buffer) as cleaned:
                data = original(cleaned, is_binary=is_binary)
        if data is not None:
            stats["successes"] += 1
        return data

    decoder.extract_qr_data = staticmethod(extract)
    setattr(decoder, marker, stats)
    return stats


def install_qr_backend(module):
    from PIL import Image
    from seedsigner.models.decode_qr import DecodeQR
    requested = os.environ.get("SHIELDSIGNER_QR_READER")
    native_frontend = os.environ.get("SHIELDSIGNER_FRONTEND_BACKEND", "python") == "rust"
    configuration = (requested, native_frontend)
    if hasattr(module, "__shieldsigner_qr_configuration__"):
        if module.__shieldsigner_qr_configuration__ != configuration:
            raise RuntimeError("Restart the application to change QR backends")
        return
    if requested:
        from shieldsigner_qr_decoder import NativeQrReader, RustTransportQrReader
        client = (RustTransportQrReader if native_frontend else NativeQrReader)(requested)
        if native_frontend:
            from shieldsigner_lcd import NativeFrame
        original = DecodeQR.extract_qr_data

        def extract(image, is_binary=False):
            if native_frontend and isinstance(image, NativeFrame):
                return client.decode(image)
            if image is None or not isinstance(image, Image.Image):
                return original(image, is_binary=is_binary)
            try:
                return client.decode(image)
            except (OSError, RuntimeError):
                # Keep the installed decoder available if a worker fails.
                # Error counts remain visible; no payload or scene is logged.
                return original(image, is_binary=is_binary)

        DecodeQR.extract_qr_data = staticmethod(extract)
        if hasattr(DecodeQR, "is_qr_scanner_available"):
            DecodeQR.is_qr_scanner_available = staticmethod(lambda: True)
        original_stop = module.Camera.stop_video_stream_mode

        def stop(camera):
            try:
                return original_stop(camera)
            finally:
                client.close()

        module.Camera.stop_video_stream_mode = stop
        module.__shieldsigner_qr_client__ = client
        module.__shieldsigner_camera_patch__["qrDecoder"] = client.stats
    else:
        if native_frontend:
            raise ValueError("Native frontend requires SHIELDSIGNER_QR_READER")
        module.__shieldsigner_camera_patch__["qrFallback"] = install_qr_fallback(DecodeQR)
    module.__shieldsigner_qr_configuration__ = configuration


def install_native_preview(module):
    if os.environ.get("SHIELDSIGNER_FRONTEND_BACKEND", "python") != "rust":
        return
    if getattr(module, "__shieldsigner_native_preview__", False):
        return
    if module.__shieldsigner_camera_patch__["sourceSha256"] != IMAGE_CAMERA_SOURCE_SHA256:
        raise RuntimeError("Native frontend requires the reviewed image Camera profile")
    original = module.Camera.read_video_stream
    def read(camera, as_image=False, preview=False, greyscale=True):
        stream = camera._video_stream
        if as_image and preview and stream is not None and getattr(stream, "transport", None) == "nv12":
            return stream.read_native_preview(90 + camera._camera_rotation)
        return original(camera, as_image=as_image, preview=preview, greyscale=greyscale)
    module.Camera.read_video_stream = read
    module.__shieldsigner_native_preview__ = True
    module.__shieldsigner_camera_patch__["frontend"] = "rust"


def camera_source(app_root):
    path = Path(app_root).resolve() / "seedsigner/hardware/camera.py"
    original = path.read_bytes()
    profile = CAMERA_PROFILES.get(hashlib.sha256(original).hexdigest())
    if profile is None:
        raise ValueError("Unsupported installed camera.py; review its changes before updating the pinned integration")
    source = original.decode("utf-8")
    patched = source
    for before, after, count in profile:
        if patched.count(before) != count:
            raise ValueError("Camera integration replacement is not unique")
        patched = patched.replace(before, after)
    return path, source, patched



def ensure_app_import_root(app_root):
    """Make script-launched app imports explicit without accepting foreign packages."""
    root = Path(app_root).resolve()
    for name in ("seedsigner", "seedsigner.hardware", "seedsigner.hardware.displays"):
        existing = sys.modules.get(name)
        if existing is None:
            continue
        expected = root.joinpath(*name.split("."))
        paths = {Path(value).resolve() for value in getattr(existing, "__path__", ())}
        if paths != {expected}:
            raise RuntimeError("Imported application package differs from requested root: " + name)
    value = str(root)
    # Script execution sets sys.path[0] to the runtime helper directory, not
    # necessarily cwd. Put the validated app first before native LCD imports.
    sys.path[:] = [value] + [entry for entry in sys.path if entry != value]
    return root


def install_camera_backend(app_root):
    path, original, patched = camera_source(app_root)
    name = "seedsigner.hardware.camera"
    existing = sys.modules.get(name)
    if existing is not None:
        if getattr(existing, "__shieldsigner_camera_patch__", None) and existing.__file__ == str(path):
            install_native_preview(existing)
            install_qr_backend(existing)
            install_camera_error_cleanup(app_root, existing)
            return existing
        raise RuntimeError("Install the Rust camera backend before importing the application Camera")
    ensure_app_import_root(app_root)
    parent = importlib.import_module("seedsigner.hardware")
    if str(path.parent) not in {str(Path(value).resolve()) for value in parent.__path__}:
        raise RuntimeError("Imported hardware package does not match the requested application root")
    module = types.ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = "seedsigner.hardware"
    virtual_filename = str(path) + " [Rust camera integration]"
    linecache.cache[virtual_filename] = (len(patched), None, patched.splitlines(True), virtual_filename)
    sys.modules[name] = module
    try:
        exec(compile(patched, virtual_filename, "exec"), module.__dict__)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    parent.camera = module
    module.__shieldsigner_camera_patch__ = {
        "sourceSha256": hashlib.sha256(original.encode()).hexdigest(),
        "patchedSourceSha256": hashlib.sha256(patched.encode()).hexdigest(),
        "changes": ["Rust camera stream import", "Preserve complete rotated preview canvas"],
        "installedFilesModified": False,
    }
    install_native_preview(module)
    install_qr_backend(module)
    install_camera_error_cleanup(app_root, module)
    return module


def install_camera_error_cleanup(app_root, camera_module):
    """Release an active camera before the normal application error screen."""
    path = Path(app_root).resolve() / "seedsigner/controller.py"
    if hashlib.sha256(path.read_bytes()).hexdigest() != SMALL_RAM_CONTROLLER_SHA256:
        raise ValueError("Unsupported controller for camera error cleanup")
    controller = importlib.import_module("seedsigner.controller")
    if Path(controller.__file__).resolve() != path:
        raise RuntimeError("Foreign controller for camera error cleanup")
    if getattr(controller, "__shieldsigner_camera_error_cleanup__", False):
        return
    original = controller.Controller.handle_exception

    def handle_exception(self, error):
        camera = getattr(camera_module.Camera, "_instance", None)
        if camera is not None and getattr(camera, "_video_stream", None) is not None:
            try:
                camera.stop_video_stream_mode()
            except Exception as cleanup_error:
                # Preserve the original user-visible failure; don't dump data.
                import logging
                logging.getLogger(__name__).warning("Camera error cleanup failed: %s", type(cleanup_error).__name__)
        return original(self, error)

    controller.Controller.handle_exception = handle_exception
    controller.__shieldsigner_camera_error_cleanup__ = True



def import_memory_snapshot(phase):
    """Public module metadata only: no object walk, seeds, frames or settings."""
    if phase not in ("startup", "scan-start", "capture", "shutdown"):
        raise ValueError("Use a public diagnostic phase name")
    prefixes = ("seedsigner", "pysatochip", "smartcard", "Cryptodome",
                "cryptography", "pgpy", "PIL", "embit", "shamir_mnemonic")
    module_map = sys.modules.copy()
    modules = tuple(name for name, module in module_map.items() if module is not None)
    selected = ("seedsigner.views.scan_views", "seedsigner.views.seed_views",
                "seedsigner.views.tools_views", "seedsigner.views.smartcard_views",
                "seedsigner.gui.screens.seed_screens", "seedsigner.helpers.seedkeeper_utils",
                "seedsigner.helpers.keycard_connector", "pysatochip.CardConnector",
                "seedsigner.models.seed", "seedsigner.models.aezeed",
                "seedsigner.models.encryptedqr", "seedsigner.helpers.kef",
                "seedsigner.models.psbt_parser", "seedsigner.models.encode_qr",
                "seedsigner.models.decode_qr", "Cryptodome.Cipher.AES", "pgpy",
                "numpy", "cv2")
    scan = module_map.get("seedsigner.views.scan_views")
    controller = module_map.get("seedsigner.controller")
    return {"kind": "small-ram-import-presence", "phase": phase,
            "moduleCount": len(modules),
            "prefixCounts": {prefix: sum(name == prefix or name.startswith(prefix + ".") for name in modules)
                             for prefix in prefixes},
            "present": {name: name in modules for name in selected},
            "lazyScanHookRegistered": any(getattr(finder, "_shieldsigner_lazy_scan_path", None) is not None
                                          for finder in sys.meta_path),
            "loadedScanModulePatched": bool(getattr(scan, "__shieldsigner_lazy_scan__", None)),
            "controllerPreloadPatched": bool(getattr(controller, "__shieldsigner_small_ram_profile__", None)),
            "containsUserObjectsOrPayloads": False}


SCAN_VIEWS_SOURCE_SHA256 = "ad151a5b572c5cc5564f94163a3060e6f9abc5bcc63ab7a0ae69eac069ef7f0c"


def lazy_scan_source(app_root):
    path = Path(app_root).resolve() / "seedsigner/views/scan_views.py"
    original = path.read_bytes()
    if hashlib.sha256(original).hexdigest() != SCAN_VIEWS_SOURCE_SHA256:
        raise ValueError("Unsupported scan_views.py for lazy SLIP39 imports")
    source = original.decode()
    replacements = [
        ("from seedsigner.views.seed_views import SeedSlip39MoreSharesView, SeedSlip39ShareInvalidView\n", "", 1),
        ("Destination(SeedSlip39MoreSharesView)", 'Destination(_shieldsigner_slip39_view("SeedSlip39MoreSharesView"))', 2),
        ("                    SeedSlip39ShareInvalidView,", '                    _shieldsigner_slip39_view("SeedSlip39ShareInvalidView"),', 1),
        ("                SeedSlip39ShareInvalidView,", '                _shieldsigner_slip39_view("SeedSlip39ShareInvalidView"),', 1),
    ]
    for before, after, count in replacements:
        if source.count(before) != count:
            raise ValueError("Lazy SLIP39 replacement count differs from reviewed source")
        source = source.replace(before, after)
    source += '''

def _shieldsigner_slip39_view(name):
    # Resolve the original classes only when a SLIP39 routing branch uses them.
    from importlib import import_module
    if name not in ("SeedSlip39MoreSharesView", "SeedSlip39ShareInvalidView"):
        raise ValueError("Unreviewed SLIP39 destination")
    return getattr(import_module("seedsigner.views.seed_views"), name)
'''
    return path, original.decode(), source


def install_lazy_scan_views(app_root):
    """Register only the pinned scan module; leave normal/default imports intact."""
    path, _, patched = lazy_scan_source(app_root)
    name = "seedsigner.views.scan_views"
    existing = sys.modules.get(name)
    if existing is not None:
        info = getattr(existing, "__shieldsigner_lazy_scan__", None)
        if info and Path(existing.__file__).resolve() == path:
            return info
        raise RuntimeError("Install lazy scan imports before scan_views is imported")
    for finder in sys.meta_path:
        if getattr(finder, "_shieldsigner_lazy_scan_path", None) == path:
            return finder.info
    parent = importlib.import_module("seedsigner.views")
    if str(path.parent) not in {str(Path(value).resolve()) for value in parent.__path__}:
        raise RuntimeError("Imported views package differs from requested application root")
    info = {"kind": "slip39-scan-destinations-imported-on-demand",
            "sourceSha256": SCAN_VIEWS_SOURCE_SHA256,
            "patchedSourceSha256": hashlib.sha256(patched.encode()).hexdigest(),
            "installedFilesModified": False, "featuresRemoved": False}

    class ScanLoader:
        _shieldsigner_lazy_scan_path = path

        def create_module(self, spec):
            return None

        def exec_module(self, module):
            # Recheck at execution, rather than trusting a previously read file.
            checked_path, _, checked = lazy_scan_source(app_root)
            if checked_path != path or checked != patched:
                raise RuntimeError("Reviewed scan source changed before import")
            filename = str(path) + " [small-RAM lazy scan imports]"
            linecache.cache[filename] = (len(patched), None, patched.splitlines(True), filename)
            exec(compile(patched, filename, "exec"), module.__dict__)
            module.__shieldsigner_lazy_scan__ = info

        def find_spec(self, fullname, package_path=None, target=None):
            if fullname != name:
                return None
            spec = importlib.util.spec_from_loader(fullname, self, origin=str(path))
            spec.has_location = True
            return spec

    finder = ScanLoader()
    finder.info = info
    sys.meta_path.insert(0, finder)
    return info


SMALL_RAM_CONTROLLER_SHA256 = "2c080563d12cef837f25799a7139277ad7c3756a05329822f81d961c2e7e031e"


def install_small_ram_profile(app_root):
    """Skip optional preloading; preserve both mandatory storage initializers.

    Existing destination handlers retain their local imports. This does not
    unload modules, remove features or promise a particular memory saving.
    Must run before Controller.configure_instance starts background imports.
    """
    path = Path(app_root).resolve() / "seedsigner/controller.py"
    source = path.read_bytes()
    if hashlib.sha256(source).hexdigest() != SMALL_RAM_CONTROLLER_SHA256:
        raise ValueError("Unsupported controller.py for small-RAM profile")
    module = importlib.import_module("seedsigner.controller")
    if Path(module.__file__).resolve() != path:
        raise RuntimeError("Imported controller does not match requested app root")
    marker = "__shieldsigner_small_ram_profile__"
    if hasattr(module, marker):
        return getattr(module, marker)
    if getattr(module.Controller, "_instance", None) is not None:
        raise RuntimeError("Small-RAM profile must be installed before Controller initialization")

    def initialize_storage(self):
        controller = module.Controller.get_instance()
        # Keep the original initialization ordering and both independent stores;
        # storage/storage2 properties otherwise wait forever for this thread.
        controller._storage = module.SeedStorage()
        controller._storage2 = module.EncryptedQRStorage()

    module.BackgroundImportThread.run = initialize_storage
    info = {"kind": "optional-background-preloads-disabled",
            "controllerSourceSha256": SMALL_RAM_CONTROLLER_SHA256,
            "mandatoryStorageInitializers": ["SeedStorage", "EncryptedQRStorage"],
            "optionalViewsRemainOnDemand": True,
            "installedFilesModified": False}
    setattr(module, marker, info)
    return info



def configure_lcd_backend(app_root, backend):
    """Explicit process-local selection before any Controller/display creation."""
    if backend not in ("python", "rust"):
        raise ValueError("LCD backend must be python or rust")
    if backend == "python":
        return {"lcdBackend": "python", "nativeLcdInstallRequested": False}
    try:
        driver = importlib.import_module("shieldsigner_lcd_driver")
    except ImportError as exc:
        raise RuntimeError("Rust LCD requested but its runtime Python shim is unavailable") from exc
    # The reviewed shim validates source/path and is idempotent when a harness
    # already selected the same native class. Never silently fall back on errors.
    info = driver.install(app_root)
    return {"lcdBackend": "rust", "nativeLcdInstallRequested": True, "driver": info}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-root", required=True)
    parser.add_argument("--config", help="Absolute-path owner JSON configuration")
    parser.add_argument("--print-patch", action="store_true")
    parser.add_argument("--qr-reader", help="Absolute path to the optional native QR worker")
    parser.add_argument("--lcd-backend", choices=("python", "rust"),
                        default=os.environ.get("SHIELDSIGNER_LCD_BACKEND", "python"),
                        help="Display transport (default python; Rust must be explicitly selected)")
    parser.add_argument("--frontend-backend", choices=("python", "rust"),
                        default=os.environ.get("SHIELDSIGNER_FRONTEND_BACKEND", "python"),
                        help="Frame reception, preview and QR transport backend")
    parser.add_argument("application_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.lcd_backend not in ("python", "rust"):
        parser.error("SHIELDSIGNER_LCD_BACKEND must be python or rust")
    if args.frontend_backend not in ("python", "rust"):
        parser.error("SHIELDSIGNER_FRONTEND_BACKEND must be python or rust")
    os.environ["SHIELDSIGNER_FRONTEND_BACKEND"] = args.frontend_backend
    root = Path(args.app_root).resolve()
    _, original, patched = camera_source(root)
    if args.print_patch:
        sys.stdout.writelines(difflib.unified_diff(
            original.splitlines(True), patched.splitlines(True),
            fromfile="a/seedsigner/hardware/camera.py", tofile="b/seedsigner/hardware/camera.py"))
        return
    if not args.config:
        parser.error("--config is required to launch the application")
    config_path = Path(args.config).resolve()
    with config_path.open() as source:
        config = json.load(source)
    from shieldsigner_video_stream import PiVideoStream
    PiVideoStream(owner_config=config)  # Validate without starting a process.
    if any(not os.path.isabs(value) for value in config.values()):
        raise ValueError("Application launcher requires absolute owner configuration paths")
    os.environ["SHIELDSIGNER_CAMERA_CONFIG"] = str(config_path)
    if args.qr_reader:
        os.environ["SHIELDSIGNER_QR_READER"] = args.qr_reader
    ensure_app_import_root(root)
    print(json.dumps(configure_lcd_backend(root, args.lcd_backend)), file=sys.stderr)
    module = install_camera_backend(root)
    if os.environ.get("SHIELDSIGNER_SMALL_RAM") == "1":
        print(json.dumps(install_small_ram_profile(root)), file=sys.stderr)
        print(json.dumps(install_lazy_scan_views(root)), file=sys.stderr)
    print(json.dumps(module.__shieldsigner_camera_patch__), file=sys.stderr)
    app_args = args.application_args[1:] if args.application_args[:1] == ["--"] else args.application_args
    old_argv, old_cwd = sys.argv, os.getcwd()
    try:
        os.chdir(root)
        sys.argv = [str(root / "main.py")] + app_args
        runpy.run_path(str(root / "main.py"), run_name="__main__")
    finally:
        try:
            camera = getattr(module.Camera, "_instance", None)
            if camera is not None and camera._video_stream is not None:
                camera.stop_video_stream_mode()
        finally:
            client = getattr(module, "__shieldsigner_qr_client__", None)
            if client is not None:
                client.close()
            sys.argv = old_argv
            os.chdir(old_cwd)


if __name__ == "__main__":
    main()
