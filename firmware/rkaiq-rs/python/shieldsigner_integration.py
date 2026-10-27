"""Opt-in entry point: use Rust camera capture without editing installed app files."""
import argparse
import difflib
import hashlib
import importlib
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


def camera_source(app_root):
    path = Path(app_root).resolve() / "seedsigner/hardware/camera.py"
    original = path.read_bytes()
    if hashlib.sha256(original).hexdigest() != CAMERA_SOURCE_SHA256:
        raise ValueError("Unsupported installed camera.py; review its changes before updating the pinned integration")
    source = original.decode("utf-8")
    patched = source
    for before, after in REPLACEMENTS:
        if patched.count(before) != 1:
            raise ValueError("Camera integration replacement is not unique")
        patched = patched.replace(before, after, 1)
    return path, source, patched


def install_camera_backend(app_root):
    path, original, patched = camera_source(app_root)
    name = "seedsigner.hardware.camera"
    existing = sys.modules.get(name)
    if existing is not None:
        if getattr(existing, "__shieldsigner_camera_patch__", None) and existing.__file__ == str(path):
            return existing
        raise RuntimeError("Install the Rust camera backend before importing the application Camera")
    sys.path.insert(0, str(Path(app_root).resolve()))
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
        "changes": ["Rust PiVideoStream import", "Preserve complete rotated preview canvas"],
        "installedFilesModified": False,
    }
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-root", required=True)
    parser.add_argument("--config", help="Absolute-path owner JSON configuration")
    parser.add_argument("--print-patch", action="store_true")
    parser.add_argument("application_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
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
    module = install_camera_backend(root)
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
            sys.argv = old_argv
            os.chdir(old_cwd)


if __name__ == "__main__":
    main()
