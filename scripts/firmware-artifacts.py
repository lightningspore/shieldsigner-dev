"""Manage firmware artifacts without changing or flashing the device."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import lzma
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile

from firmware_paths import (ROOT, ARTIFACTS, SOURCES, LVGL_SOURCES, LVGL_WORK,
                           STAGING, IMAGES, CHECKS, JOBS, ARCHIVE)

KNOWN = 'lvgl-dev.cb6170a37a5a'
KNOWN_XZ = '834b2ca4d24055dbc533997e43e92bb54932e75c49dff27698316a51a6859853'
KNOWN_RAW = 'e605e47ab21dc4785a24ee356966b8cf649fe1716248de126cfce9605601e862'


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for chunk in iter(lambda: source.read(8 * 1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path):
    return str(Path(path).relative_to(ROOT))


def safe_name(name):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', name) or name in {'.', '..', 'current'}:
        raise ValueError('Use a unique build name containing letters, digits, dots, dashes or underscores')
    return name


def image_directory(name='current'):
    directory = IMAGES / (name if name == 'current' else safe_name(name))
    resolved = directory.resolve()
    if not resolved.is_relative_to(IMAGES.resolve()) or resolved == IMAGES.resolve():
        raise ValueError('Image directory escaped the verified-image store')
    return resolved


def verify_provenance(record, report):
    """Check frozen staging inputs without requiring today's build inputs."""
    paths = {}
    for key in ('runtime', 'overlay', 'camera_bundle', 'camera_base'):
        value = Path(record['inputs'][key])
        path = (ROOT / value).resolve()
        if value.is_absolute() or '..' in value.parts or not path.is_relative_to(ROOT.resolve()):
            raise ValueError('Unsafe provenance path: ' + key)
        paths[key] = path
    app = ROOT / 'firmware/lvgl-app'
    original_path = sys.path[:]
    try:
        sys.path[:0] = [str(app), str(app / 'python')]
        from package import verify as verify_runtime
        from image_stage import verify as verify_overlay
        verify_runtime(paths['runtime'])
        verify_overlay(paths['overlay'])
        spec = importlib.util.spec_from_file_location('artifact_camera_bundle', ROOT / 'scripts/prepare-camera-image.py')
        camera = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(camera)
        combined = camera.verify(paths['camera_bundle'])
        base = camera.verify(paths['camera_base'])
    finally:
        sys.path[:] = original_path
    runtime = json.loads((paths['runtime'] / 'runtime-manifest.json').read_text())
    plan_path = paths['overlay'] / 'integration-plan.json'
    plan = json.loads(plan_path.read_text())
    identity = sha(paths['runtime'] / 'runtime-manifest.json')
    if record['runtimeManifestSha256'] != identity or plan['runtimeManifestSha256'] != identity or plan['runtimeManifest'] != runtime:
        raise ValueError('Runtime provenance differs from overlay')
    if plan['version']['name'] != record['version']:
        raise ValueError('Image version differs from overlay')
    if combined.get('lvglOverlay', {}).get('planSha256') != sha(plan_path):
        raise ValueError('Camera bundle differs from overlay plan')
    embedded_plan = paths['camera_bundle'] / 'lvgl-overlay/integration-plan.json'
    if sha(embedded_plan) != sha(plan_path):
        raise ValueError('Attached overlay plan differs')
    overlay_files = list(plan['files'])
    if plan.get('applyHelperSha256'):
        overlay_files.append('overlay-apply.py')
    for relative in overlay_files:
        if sha(paths['overlay'] / relative) != sha(paths['camera_bundle'] / 'lvgl-overlay' / relative):
            raise ValueError('Attached overlay payload differs: ' + relative)
    layer = combined['lvglOverlay']
    if layer.get('sdkStripBaseHelperSha256') != base['files']['image-overlay.py']['sha256'] or layer.get('sdkStripHelperSha256') != combined['files']['image-overlay.py']['sha256']:
        raise ValueError('Camera overlay helper provenance differs')
    for key, value in base.items():
        if key != 'files' and combined.get(key) != value:
            raise ValueError('Camera base provenance differs: ' + key)
    for relative, entry in base['files'].items():
        if relative != 'image-overlay.py' and combined['files'].get(relative) != entry:
            raise ValueError('Camera base payload differs: ' + relative)
    if report.get('rootfsVerification', {}).get('bundleManifestSha256') != sha(paths['camera_bundle'] / 'manifest.json'):
        raise ValueError('Packed image camera manifest differs')


def verify_image(name='current'):
    directory = image_directory(name)
    record = json.loads((directory / 'image.json').read_text())
    if record.get('schema') != 1 or record.get('kind') != 'shieldsigner-verified-flash-image':
        raise ValueError('Unsupported image record')
    for key in ('compressed', 'raw'):
        entry = record[key]
        if Path(entry['file']).name != entry['file']:
            raise ValueError('Unsafe image filename')
        path = directory / entry['file']
        if path.is_symlink() or path.stat().st_size != entry['bytes'] or sha(path) != entry['sha256']:
            raise ValueError('Image file differs: ' + key)
    report_entry = record['verification']
    if Path(report_entry['file']).name != report_entry['file']:
        raise ValueError('Unsafe verification filename')
    report_path = directory / report_entry['file']
    if sha(report_path) != report_entry['sha256']:
        raise ValueError('Verification receipt differs')
    report = json.loads(report_path.read_text())
    if report['imageSha256'] != record['raw']['sha256'] or report['imageBytes'] != record['raw']['bytes']:
        raise ValueError('Image does not match packed verification')
    if not report.get('lvglOverlayVerification', {}).get('verified'):
        raise ValueError('Missing packed LVGL verification')
    for key in ('qemuPythonDirectDataSmoke', 'qemuRustLcdSmoke', 'qemuNativeFrontendSmoke', 'qemuLvglSmoke'):
        if report.get(key, {}).get('passed') is not True:
            raise ValueError('Missing packed smoke: ' + key)
    verify_provenance(record, report)
    digest = hashlib.sha256()
    size = 0
    with lzma.open(directory / record['compressed']['file'], 'rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            size += len(chunk)
            if size > record['raw']['bytes']:
                raise ValueError('Compressed image expands beyond recorded raw size')
            digest.update(chunk)
    if size != record['raw']['bytes'] or digest.hexdigest() != record['raw']['sha256']:
        raise ValueError('Compressed image does not reproduce raw image')
    return record


def current_image():
    directory = image_directory()
    record = json.loads((directory / 'image.json').read_text())
    return dict(version=record['version'], directory=str(directory),
                compressed=str(directory / record['compressed']['file']),
                raw=str(directory / record['raw']['file']),
                verification=str(directory / record['verification']['file']))


def migrate():
    """One-time layout migration; rename on the same filesystem and retain aliases."""
    for path in (ARTIFACTS, LVGL_SOURCES, STAGING, IMAGES, CHECKS, JOBS, ARCHIVE):
        path.mkdir(parents=True, exist_ok=True)
    if (IMAGES / KNOWN / 'image.json').is_file():
        verify_image(KNOWN)
        return dict(alreadyMigrated=True, current=current_image())
    old_lvgl = ROOT / 'dist/lvgl-app'
    old_os = ROOT / 'dist/os'
    old_images = old_os / 'flash-images/lvgl-memory-cleanup-final'
    archive_file = old_images / 'shieldsigner-lvgl-dev-cb6170a37a5a.img.xz'
    raw_file = archive_file.with_suffix('')
    if sha(archive_file) != KNOWN_XZ or sha(raw_file) != KNOWN_RAW:
        raise ValueError('The known flashed image must verify before migration')

    # Refuse collisions before the first rename, rather than leaving half a layout.
    destinations = [IMAGES / KNOWN, STAGING / KNOWN,
                    STAGING / 'camera-base-native-cf4c428-02', LVGL_WORK,
                    CHECKS / 'lvgl/hardware', CHECKS / 'lvgl/host',
                    ARCHIVE / 'os-legacy', ARTIFACTS / 'work/lvgl-demo',
                    SOURCES / 'seedsigner-os']
    lock = json.loads((ROOT / 'firmware/lvgl-app/sources.lock.json').read_text())
    destinations.extend(LVGL_SOURCES / name for name in lock)
    destinations.extend(JOBS / path.name for path in (old_os / 'remote-jobs').glob('*.json'))
    destinations.extend(ARCHIVE / 'lvgl-legacy' / path.name for path in old_lvgl.iterdir()
                        if path.is_dir() and not path.is_symlink()
                        and path.name.startswith(('runtime-', 'image-'))
                        and path.name not in {'runtime-memory-cleanup-final', 'image-memory-cleanup-final'})
    for destination in destinations:
        if destination.exists() or destination.is_symlink():
            raise ValueError('Migration destination exists: ' + str(destination))

    snapshot = ARCHIVE / ('source-checkpoint-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    snapshot.mkdir()
    (snapshot / 'tracked.patch').write_bytes(subprocess.check_output(['git', 'diff', '--binary'], cwd=ROOT))
    with tarfile.open(snapshot / 'lvgl-source.tar.gz', 'w:gz') as archive:
        for source in (ROOT / 'firmware/lvgl-app', ROOT / 'firmware/lvgl-demo', ROOT / 'scripts'):
            for path in sorted(source.rglob('*')):
                if path.is_file() and '__pycache__' not in path.parts and path.name != '.DS_Store':
                    archive.add(path, arcname=relative(path), recursive=False)
        archive.add(ROOT / 'mise.toml', arcname='mise.toml', recursive=False)
    (snapshot / 'snapshot.json').write_text(json.dumps(dict(schema=1,
        purpose='Pre-migration source checkpoint; includes cleanup edits already made',
        head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        archiveSha256=sha(snapshot / 'lvgl-source.tar.gz'),
        patchSha256=sha(snapshot / 'tracked.patch')), indent=2) + '\n')

    journal = []

    def move(source, destination, alias=True):
        if source.is_symlink() or not source.exists():
            return
        if destination.exists() or destination.is_symlink():
            raise ValueError('Migration destination exists: ' + str(destination))
        destination.parent.mkdir(parents=True, exist_ok=True)
        source.rename(destination)
        if alias:
            source.symlink_to(os.path.relpath(destination, source.parent), target_is_directory=True)
        journal.append(dict(source=relative(source), destination=relative(destination), compatibilityAlias=alias))

    move(old_images, IMAGES / KNOWN)
    release = STAGING / KNOWN
    move(old_lvgl / 'runtime-memory-cleanup-final', release / 'runtime')
    move(old_lvgl / 'image-memory-cleanup-final', release / 'overlay')
    move(old_os / 'image-bundles/lvgl-memory-cleanup-final', release / 'camera-bundle')
    camera_base = STAGING / 'camera-base-native-cf4c428-02/camera-bundle'
    move(old_os / 'image-bundles/native-frontend-cf4c428-02', camera_base)

    lock = json.loads((ROOT / 'firmware/lvgl-app/sources.lock.json').read_text())
    for name in lock:
        move(old_lvgl / name, LVGL_SOURCES / name)
    move(old_lvgl / 'checks', CHECKS / 'lvgl/hardware')
    move(old_lvgl / 'host-checks', CHECKS / 'lvgl/host')
    for source in sorted(old_lvgl.iterdir()):
        if source.is_dir() and not source.is_symlink() and source.name.startswith(('runtime-', 'image-')):
            move(source, ARCHIVE / 'lvgl-legacy' / source.name)
    move(old_lvgl, LVGL_WORK)
    # Aliases created above are relative to the old parent. Recreate after its move.
    for row in journal:
        old = ROOT / row['source']
        if row['source'].startswith('dist/lvgl-app/') and row['compatibilityAlias']:
            link = LVGL_WORK / Path(row['source']).relative_to('dist/lvgl-app')
            if link.is_symlink():
                link.unlink()
                link.symlink_to(os.path.relpath(ROOT / row['destination'], link.parent), target_is_directory=True)
    for source in sorted((old_os / 'remote-jobs').glob('*.json')):
        move(source, JOBS / source.name, alias=False)
    move(old_os, ARCHIVE / 'os-legacy')
    # The old OS parent also moved; fix its compatibility links.
    for row in journal:
        if row['source'].startswith('dist/os/') and row['compatibilityAlias']:
            link = ARCHIVE / 'os-legacy' / Path(row['source']).relative_to('dist/os')
            if link.is_symlink():
                link.unlink()
                link.symlink_to(os.path.relpath(ROOT / row['destination'], link.parent), target_is_directory=True)
    legacy_jobs = ARCHIVE / 'os-legacy/remote-jobs'
    if legacy_jobs.is_dir() and not any(legacy_jobs.iterdir()):
        legacy_jobs.rmdir()
        legacy_jobs.symlink_to(os.path.relpath(JOBS, legacy_jobs.parent), target_is_directory=True)
    move(ROOT / 'dist/lvgl-demo', ARTIFACTS / 'work/lvgl-demo')
    move(ROOT / 'tools/os/seedsigner-os', SOURCES / 'seedsigner-os')

    directory = IMAGES / KNOWN
    report_path = directory / 'shieldsigner-lvgl-dev-cb6170a37a5a-verification.json'
    runtime = release / 'runtime/runtime-manifest.json'
    record = dict(schema=1, kind='shieldsigner-verified-flash-image', version=KNOWN,
                  compressed=dict(file=archive_file.name, sha256=KNOWN_XZ, bytes=(directory / archive_file.name).stat().st_size),
                  raw=dict(file=raw_file.name, sha256=KNOWN_RAW, bytes=(directory / raw_file.name).stat().st_size),
                  verification=dict(file=report_path.name, sha256=sha(report_path)),
                  runtimeManifestSha256=sha(runtime),
                  inputs=dict(runtime=relative(release / 'runtime'), overlay=relative(release / 'overlay'),
                              camera_bundle=relative(release / 'camera-bundle'), camera_base=relative(camera_base)))
    (directory / 'image.json').write_text(json.dumps(record, indent=2) + '\n')
    (directory / 'acceptance.json').write_text(json.dumps(dict(schema=1, version=KNOWN,
        userReported=dict(boot=True, uiUsable=True, cameraScan=True, source='User conversation'),
        automated=dict(packedImage=True, publicSigningFixture=True), realWalletAcceptance='pending; no wallet available'), indent=2) + '\n')
    (IMAGES / 'current').symlink_to(KNOWN, target_is_directory=True)
    (ARTIFACTS / 'legacy-paths.json').write_text(json.dumps(dict(schema=1, moves=journal, snapshot=relative(snapshot)), indent=2) + '\n')
    verify_image()
    return dict(migrated=True, moves=len(journal), current=current_image(), sourceSnapshot=relative(snapshot))


def stage(name, camera=None):
    name = safe_name(name)
    destination = STAGING / name
    if destination.exists():
        raise ValueError('Staging is immutable; choose a new name')
    if camera is None:
        current = json.loads((image_directory() / 'image.json').read_text())
        camera = ROOT / current['inputs']['camera_base']
    camera = camera.resolve()
    subprocess.run(['mise', 'run', 'lvgl:app:build'], cwd=ROOT, check=True)
    epoch = subprocess.check_output(['git', 'show', '-s', '--format=%ct', 'HEAD'], cwd=ROOT, text=True).strip()
    runtime, overlay, combined = [destination / name for name in ('runtime', 'overlay', 'camera-bundle')]
    subprocess.run(['mise', 'run', 'lvgl:app:bundle', '--output', str(runtime)], cwd=ROOT, check=True)
    subprocess.run(['mise', 'run', 'lvgl:app:image-draft', '--runtime', str(runtime), '--output', str(overlay), '--source-date-epoch', epoch, '--default-frontend', 'lvgl'], cwd=ROOT, check=True)
    subprocess.run(['mise', 'run', 'lvgl:app:image-attach', '--camera', str(camera), '--draft', str(overlay), '--output', str(combined)], cwd=ROOT, check=True)
    record = dict(schema=1, name=name, runtime=relative(runtime), overlay=relative(overlay), camera_bundle=relative(combined), camera_base=relative(camera), imageBuilt=False)
    (destination / 'stage.json').write_text(json.dumps(record, indent=2) + '\n')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('where')
    commands.add_parser('migrate-legacy')
    verify = commands.add_parser('verify');verify.add_argument('name', nargs='?', default='current')
    staging = commands.add_parser('stage');staging.add_argument('--name', required=True);staging.add_argument('--camera', type=Path)
    args = parser.parse_args()
    if args.command == 'where':
        result = current_image()
    elif args.command == 'verify':
        record = verify_image(args.name)
        result = dict(verified=True, version=record['version'])
        if args.name == 'current':
            result.update(current_image())
    elif args.command == 'migrate-legacy':
        result = migrate()
    else:
        result = stage(args.name, args.camera)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
