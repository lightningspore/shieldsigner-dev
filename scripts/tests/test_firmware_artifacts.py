"""Tiny local artifact fixtures; never build, migrate, flash, or access hardware."""
import importlib.util
import json
import lzma
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('firmware_artifact_manager', SCRIPTS / 'firmware-artifacts.py')
manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manager)


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.images = self.root / 'dist/firmware/images'
        self.directory = self.images / 'public-fixture'
        self.directory.mkdir(parents=True)
        self.addCleanup(patch.stopall)
        patch.object(manager, 'ROOT', self.root).start()
        patch.object(manager, 'IMAGES', self.images).start()

    def test_safe_build_names(self):
        for name in ('public-fixture', 'v0.1_test', '20261031'):
            self.assertEqual(manager.safe_name(name), name)
        for name in ('', '.', '..', 'current', '../escape', '/tmp/image', '-option', 'a/b', 'two names', 'a\n'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                manager.safe_name(name)

    def test_current_symlink_can_select_only_a_child_image(self):
        current = self.images / 'current'
        current.symlink_to(self.directory.name)
        self.assertEqual(manager.image_directory(), self.directory)
        current.unlink()
        current.symlink_to(self.root)
        with self.assertRaises(ValueError):
            manager.image_directory()
        current.unlink()
        current.symlink_to('.')
        with self.assertRaises(ValueError):
            manager.image_directory()

    def fixture(self):
        raw = self.directory / 'public.img'
        raw.write_bytes(b'public image fixture\x00' * 23)
        compressed = self.directory / 'public.img.xz'
        compressed.write_bytes(lzma.compress(raw.read_bytes()))
        self.record = dict(schema=1, kind='shieldsigner-verified-flash-image', version='public-fixture')
        for key, path in (('raw', raw), ('compressed', compressed)):
            self.record[key] = dict(file=path.name, sha256=manager.sha(path), bytes=path.stat().st_size)
        self.report = dict(imageSha256=manager.sha(raw), imageBytes=raw.stat().st_size,
                           lvglOverlayVerification=dict(verified=True))
        for key in ('qemuPythonDirectDataSmoke', 'qemuRustLcdSmoke', 'qemuNativeFrontendSmoke', 'qemuLvglSmoke'):
            self.report[key] = dict(passed=True)
        self.save_report()

    def save_report(self):
        report = self.directory / 'verification.json'
        report.write_text(json.dumps(self.report))
        self.record['verification'] = dict(file=report.name, sha256=manager.sha(report))
        self.save_record()

    def save_record(self):
        (self.directory / 'image.json').write_text(json.dumps(self.record))

    def test_corrupted_image_is_rejected_before_provenance_helpers(self):
        self.fixture()
        (self.directory / 'public.img').write_bytes(b'corrupted')
        with self.assertRaises(ValueError):
            manager.verify_image('public-fixture')

    def test_image_filename_cannot_escape_store(self):
        self.fixture()
        self.record['raw']['file'] = '../public.img'
        self.save_record()
        with self.assertRaises(ValueError):
            manager.verify_image('public-fixture')

    def test_image_symlinks_are_rejected(self):
        self.fixture()
        image = self.directory / 'public.img'
        outside = self.root / 'public.img'
        image.rename(outside)
        image.symlink_to(outside)
        with self.assertRaises(ValueError):
            manager.verify_image('public-fixture')

    def test_corrupted_verification_receipt_is_rejected(self):
        self.fixture()
        (self.directory / 'verification.json').write_text('{}')
        with self.assertRaises(ValueError):
            manager.verify_image('public-fixture')

    def test_receipt_must_describe_the_same_raw_image(self):
        self.fixture()
        self.report['imageSha256'] = '0' * 64
        self.save_report()
        with self.assertRaises(ValueError):
            manager.verify_image('public-fixture')

    def test_tiny_matching_xz_and_raw_image_verifies(self):
        self.fixture()
        with patch.object(manager, 'verify_provenance') as provenance:
            self.assertEqual(manager.verify_image('public-fixture'), self.record)
        provenance.assert_called_once_with(self.record, self.report)

    def test_self_consistent_hashes_cannot_hide_xz_raw_mismatch(self):
        self.fixture()
        compressed = self.directory / 'public.img.xz'
        compressed.write_bytes(lzma.compress(b'a different public image'))
        self.record['compressed'].update(sha256=manager.sha(compressed), bytes=compressed.stat().st_size)
        self.save_record()
        with patch.object(manager, 'verify_provenance'), self.assertRaises(ValueError):
            manager.verify_image('public-fixture')

    def test_provenance_failures_are_not_ignored(self):
        self.fixture()
        with patch.object(manager, 'verify_provenance', side_effect=ValueError('Public fixture provenance differs')):
            with self.assertRaisesRegex(ValueError, 'provenance differs'):
                manager.verify_image('public-fixture')

    def test_provenance_rejects_parent_and_absolute_paths_before_loading_helpers(self):
        for path in ('../escape', str(self.root)):
            with self.subTest(path=path), self.assertRaises(ValueError):
                manager.verify_provenance(dict(inputs=dict(runtime=path)), {})

    def test_provenance_rejects_symlink_escape_before_loading_helpers(self):
        outside = self.root.parent / (self.root.name + '-outside')
        (self.root / 'escape').symlink_to(outside)
        with self.assertRaises(ValueError):
            manager.verify_provenance(dict(inputs=dict(runtime='escape')), {})

    def provenance_fixture(self):
        self.fixture()
        paths = {key: self.root / key for key in ('runtime', 'overlay', 'camera_bundle', 'camera_base')}
        for path in paths.values():
            path.mkdir()
        runtime = paths['runtime'] / 'runtime-manifest.json'
        runtime.write_text('{}')
        identity = manager.sha(runtime)
        self.record.update(runtimeManifestSha256=identity, inputs={key: key for key in paths})
        plan = dict(runtimeManifestSha256=identity, runtimeManifest={}, version=dict(name='public-fixture'), files={})
        plan_path = paths['overlay'] / 'integration-plan.json'
        plan_path.write_text(json.dumps(plan))
        attached = paths['camera_bundle'] / 'lvgl-overlay'
        attached.mkdir()
        (attached / 'integration-plan.json').write_bytes(plan_path.read_bytes())
        base = dict(files={'image-overlay.py': dict(sha256='base-helper')})
        combined = dict(files={'image-overlay.py': dict(sha256='extended-helper')}, lvglOverlay=dict(
            planSha256=manager.sha(plan_path), sdkStripBaseHelperSha256='base-helper', sdkStripHelperSha256='extended-helper'))
        for key, value in (('camera_base', base), ('camera_bundle', combined)):
            (paths[key] / 'manifest.json').write_text(json.dumps(value))
        self.report['rootfsVerification'] = dict(bundleManifestSha256=manager.sha(paths['camera_bundle'] / 'manifest.json'))
        # Only the existing payload validators are replaced: exercise real
        # manager cross-artifact bindings independently of full ELF fixtures.
        validators = {name: SimpleNamespace(verify=lambda path: None) for name in ('package', 'image_stage')}
        patch.dict(sys.modules, validators).start()
        camera = SimpleNamespace(verify=lambda path: json.loads((path / 'manifest.json').read_text()))
        loader = SimpleNamespace(exec_module=lambda module: None)
        patch.object(manager.importlib.util, 'spec_from_file_location', return_value=SimpleNamespace(loader=loader)).start()
        patch.object(manager.importlib.util, 'module_from_spec', return_value=camera).start()

    def test_frozen_provenance_binds_matching_artifacts(self):
        self.provenance_fixture()
        manager.verify_provenance(self.record, self.report)

    def test_record_runtime_identity_must_match_frozen_manifest(self):
        self.provenance_fixture()
        self.record['runtimeManifestSha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'Runtime provenance'):
            manager.verify_provenance(self.record, self.report)

    def test_packed_receipt_must_bind_the_frozen_camera_manifest(self):
        self.provenance_fixture()
        self.report['rootfsVerification']['bundleManifestSha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'Packed image camera manifest'):
            manager.verify_provenance(self.record, self.report)

    def test_stage_groups_all_payloads_under_one_named_destination(self):
        staging = self.root / 'dist/firmware/staging'
        camera = self.root / 'public-camera-base'
        camera.mkdir()
        destination = staging / 'public-build'

        def create_mock_output(command, **kwargs):
            if '--output' in command:
                Path(command[command.index('--output') + 1]).mkdir(parents=True)

        with patch.object(manager, 'STAGING', staging), \
             patch.object(manager.subprocess, 'run', side_effect=create_mock_output) as run, \
             patch.object(manager.subprocess, 'check_output', return_value='1700000000\n'):
            result = manager.stage('public-build', camera)
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(commands, [
            ['mise', 'run', 'lvgl:app:build'],
            ['mise', 'run', 'lvgl:app:bundle', '--output', str(destination / 'runtime')],
            ['mise', 'run', 'lvgl:app:image-draft', '--runtime', str(destination / 'runtime'),
             '--output', str(destination / 'overlay'), '--source-date-epoch', '1700000000', '--default-frontend', 'lvgl'],
            ['mise', 'run', 'lvgl:app:image-attach', '--camera', str(camera), '--draft', str(destination / 'overlay'),
             '--output', str(destination / 'camera-bundle')],
        ])
        self.assertFalse(result['imageBuilt'])
        self.assertEqual(json.loads((destination / 'stage.json').read_text()), result)
        for key, child in (('runtime', 'runtime'), ('overlay', 'overlay'), ('camera_bundle', 'camera-bundle')):
            self.assertEqual(self.root / result[key], destination / child)

    def test_stage_rejects_existing_destination_without_starting_a_build(self):
        staging = self.root / 'staging'
        (staging / 'existing').mkdir(parents=True)
        with patch.object(manager, 'STAGING', staging), patch.object(manager.subprocess, 'run') as run:
            with self.assertRaises(ValueError):
                manager.stage('existing', self.root)
        run.assert_not_called()

    def test_stage_rejects_unsafe_names_without_starting_a_build(self):
        with patch.object(manager.subprocess, 'run') as run:
            for name in ('../escape', 'current', '/absolute'):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    manager.stage(name, self.root)
        run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
