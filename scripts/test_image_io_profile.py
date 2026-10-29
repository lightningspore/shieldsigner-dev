"""Pinned public fixtures; no hardware access or mutable build tree."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('io_profile', ROOT/'scripts/configure-image-io-profile.py')
helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)


class ImageIoProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Reconstruct exact pinned upstream from the checked-in reviewed fixture:
        # both canonical versions have a fixed byte hash asserted by the helper.
        data = json.loads(helper.DEFAULT_TEMPLATE.read_text())
        fox = helper.selected(data)
        fox['display'] = {'dc':['/dev/gpiochip1',20], 'rst':['/dev/gpiochip1',19],
                          'bl':'disabled','spi_bus':0,'spi_device':0}
        lines = {'KEY_UP':(1,25),'KEY_DOWN':(1,23),'KEY_LEFT':(1,24),'KEY_RIGHT':(0,4),
                 'KEY_PRESS':(1,22),'KEY1':(4,16),'KEY2':(4,17),'KEY3':(1,21)}
        fox['buttons'] = {name:[f'/dev/gpiochip{chip}',line,'pull_up'] for name,(chip,line) in lines.items()}
        cls.original = (json.dumps(data,indent=2)+'\n\n').encode()
        assert helper.digest(cls.original) == helper.UPSTREAM_SHA256

    def test_default_carrier_and_opt_in_base_fork_only_change_fox22(self):
        with tempfile.TemporaryDirectory() as directory:
            for profile in ('carrier','base-fork'):
                path=Path(directory)/profile; path.write_bytes(self.original)
                receipt=helper.configure(path,profile)
                self.assertEqual(helper.verify(path,receipt,profile),receipt)
                self.assertEqual(helper.other_models(json.loads(path.read_bytes())),helper.other_models(json.loads(self.original)))
                display=helper.selected(json.loads(path.read_bytes()))['display']
                self.assertEqual(display['dc'],['/dev/gpiochip1',24 if profile=='base-fork' else 20])
                self.assertEqual(display['rst'],['/dev/gpiochip1',25 if profile=='base-fork' else 19])
                self.assertEqual(display['spi_hz'],10_000_000)
                self.assertEqual(display['bl'],'disabled')

    def test_unreviewed_input_or_template_rejected_before_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'io.json'; path.write_bytes(self.original+b' ')
            before=path.read_bytes()
            with self.assertRaisesRegex(ValueError,'upstream'):helper.configure(path,'base-fork')
            self.assertEqual(path.read_bytes(),before)
            path.write_bytes(self.original)
            template=Path(directory)/'changed-template';template.write_text(helper.DEFAULT_TEMPLATE.read_text()+' ')
            with self.assertRaisesRegex(ValueError,'template'):helper.configure(path,'base-fork',template)
            self.assertEqual(path.read_bytes(),self.original)

    def test_final_verifier_rejects_mode_payload_receipt_and_profile_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'io.json';path.write_bytes(self.original)
            receipt=helper.configure(path,'base-fork'); saved=path.read_bytes()
            path.chmod(0o600)
            with self.assertRaisesRegex(ValueError,'mode'):helper.verify(path,receipt,'base-fork')
            path.chmod(0o644);path.write_bytes(saved+b' ')
            with self.assertRaisesRegex(ValueError,'changed'):helper.verify(path,receipt,'base-fork')
            path.write_bytes(saved)
            bad=copy.deepcopy(receipt);bad['outputSha256']='0'*64
            with self.assertRaisesRegex(ValueError,'receipt'):helper.verify(path,bad,'base-fork')
            with self.assertRaisesRegex(ValueError,'receipt'):helper.verify(path,receipt,'carrier')
            link=Path(directory)/'symlink';link.symlink_to(path)
            with self.assertRaisesRegex(ValueError,'symlink'):helper.verify(link,receipt,'base-fork')


class BaseForkResourceTests(unittest.TestCase):
    def kernel_fixture(self, root):
        directory = Path(root) / helper.DTS_DIR
        directory.mkdir(parents=True)
        dts, dtsi = directory/helper.DTS_NAME, directory/helper.DTSI_NAME
        dts.write_bytes(b'/dts-v1/;\n#include "shared.dtsi"\n&uart2 { status = "okay"; };\n')
        dtsi.write_bytes(b'&uart2 { status = "okay"; };\n')
        return dts, dtsi

    def test_kernel_only_appends_last_wins_override_and_carrier_is_noop(self):
        with tempfile.TemporaryDirectory() as root:
            dts,dtsi=self.kernel_fixture(root); original,shared=dts.read_bytes(),dtsi.read_bytes()
            carrier=helper.configure_kernel(root,'carrier')
            helper.verify_kernel(root,carrier,'carrier')
            self.assertEqual(dts.read_bytes(),original)
            with patch.object(helper,'sdk_revision',return_value=helper.SDK_REVISION), patch.object(helper,'DTS_SHA256',helper.digest(original)), patch.object(helper,'DTSI_SHA256',helper.digest(shared)):
                receipt=helper.configure_kernel(root,'base-fork')
                self.assertEqual(dts.read_bytes(),original+helper.UART2_OVERRIDE)
                self.assertEqual(dtsi.read_bytes(),shared)
                self.assertEqual(helper.configure_kernel(root,'base-fork'),receipt)
                helper.verify_kernel(root,receipt,'base-fork')
                self.assertFalse(receipt['compiledDtbQualification'])
                dts.write_bytes(dts.read_bytes()+b'&uart2 { status = "okay"; };\n')
                with self.assertRaisesRegex(ValueError,'last-wins'):helper.verify_kernel(root,receipt,'base-fork')

    def test_unknown_sdk_or_source_fails_before_kernel_mutation(self):
        with tempfile.TemporaryDirectory() as root:
            dts,dtsi=self.kernel_fixture(root); original=dts.read_bytes()
            with patch.object(helper,'sdk_revision',return_value='wrong'):
                with self.assertRaisesRegex(ValueError,'revision'):helper.configure_kernel(root,'base-fork')
            with patch.object(helper,'sdk_revision',return_value=helper.SDK_REVISION):
                with self.assertRaisesRegex(ValueError,'DTSI'):helper.configure_kernel(root,'base-fork')
            self.assertEqual(dts.read_bytes(),original)

    def test_pcsc_hold_is_exact_guarded_and_mode_checked(self):
        with tempfile.TemporaryDirectory() as root:
            service=Path(root)/'etc/init.d/S60pcscd';service.parent.mkdir(parents=True)
            original=b'#!/bin/sh\necho fixture supervisor\n';service.write_bytes(original)
            carrier=helper.configure_resources(root,'carrier')
            helper.verify_resources(root,carrier,'carrier')
            self.assertEqual(service.read_bytes(),original)
            with self.assertRaisesRegex(ValueError,'Unreviewed'):helper.configure_resources(root,'base-fork')
            with patch.object(helper,'PCSCD_SOURCE_SHA256',helper.digest(original)):
                receipt=helper.configure_resources(root,'base-fork')
                self.assertEqual(service.read_bytes(),helper.PCSCD_HOLD)
                helper.verify_resources(root,receipt,'base-fork')
                self.assertEqual(helper.configure_resources(root,'base-fork'),receipt)
                service.chmod(0o644)
                with self.assertRaisesRegex(ValueError,'mode'):helper.verify_resources(root,receipt,'base-fork')
                service.chmod(0o755);service.write_bytes(helper.PCSCD_HOLD+b'# changed\n')
                with self.assertRaisesRegex(ValueError,'bytes'):helper.verify_resources(root,receipt,'base-fork')

if __name__=='__main__':unittest.main()
