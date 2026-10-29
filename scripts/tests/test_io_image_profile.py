"""IO bundle/proof integration guards; no SDK build or hardware access."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module
packager = load('io_packager', ROOT/'scripts/prepare-camera-image.py')
hooks = load('io_hooks', ROOT/'scripts/configure-os-camera.py')

class IoImageTests(unittest.TestCase):
    def test_base_fork_requires_actual_single_disabled_uart_proof(self):
        good = {'ioProfile':'base-fork', 'compiledUart2':[{'path':'/serial@ff4c0000','status':'disabled','enabled':False}]}
        packager.validate_io_proof(good, 'base-fork', False)
        for bad in ({}, {'ioProfile':'carrier'}, dict(good, compiledUart2=[]),
                    dict(good, compiledUart2=good['compiledUart2']*2),
                    dict(good, compiledUart2=[{'path':'/serial@ff4c0000','status':'okay','enabled':True}])):
            with self.assertRaises(ValueError):packager.validate_io_proof(bad, 'base-fork', False)
        packager.validate_io_proof({}, 'carrier', False)
        packager.validate_io_proof({}, 'base-fork', True)  # kernel-only; no image

    def test_io_kernel_policy_runs_after_uart_patches_before_kernel(self):
        original='''    apply_uart2_console_dts_patch
    apply_uart2_fiq_kernel_patch
    print_step "Building Kernel"
    sdk_build kernel
    print_step "Building Rootfs"
    sdk_build rootfs
    # Non-dev (production) rootfs hardening:
    # with CI via patch-oem-pre-hook.sh.
    if [[ "$SEEDSIGNER_BUILD_VARIANT" == "non-dev" ]]; then
    sdk_build firmware
'''
        desired=hooks.patched('opt/luckfox/os-build.sh',original)
        anchor=desired.index('configure-image-io-profile.py --kernel-sdk')
        self.assertGreater(anchor,desired.index('apply_uart2_fiq_kernel_patch'))
        self.assertLess(anchor,desired.index('    sdk_build kernel'))
        self.assertIn('export SHIELDSIGNER_IO_KERNEL_RECEIPT=',desired)
        self.assertNotIn('configure-image-io-profile.py',hooks.patched('opt/luckfox/os-build.sh',original,io=False))

    def test_overlay_selects_helper_instead_of_pretransforming_base_fork(self):
        # Guard the essential raw-input contract and S60 inclusion at the install boundary.
        source=(ROOT/'scripts/camera-image-overlay.py').read_text()
        install=source[source.index('def install('):source.index('def verify(')]
        self.assertLess(install.index('io.configure(display_config'),install.index('display_module.configure(display_config)'))
        self.assertIn('elif io_profile == "carrier":',install)
        self.assertIn('io.configure_resources(root, io_profile)',install)
        self.assertIn('changes.append(root / "etc/init.d/S60pcscd")',install)

if __name__ == '__main__':unittest.main()
