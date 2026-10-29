"""Host structural fixtures only: no kernel build, swap, GPIO or hardware."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
z=load('zram_profile',ROOT/'scripts/image-profiles/zram-image-profile.py')
hooks=load('camera_hooks',ROOT/'scripts/configure-os-camera.py')
packager=load('camera_packager',ROOT/'scripts/prepare-camera-image.py')

def put(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text);return path

def fake_module(name):
    raw=bytearray(52);raw[:6]=b'\x7fELF\x01\x01';struct.pack_into('<HH',raw,16,1,40)
    return bytes(raw)+b'vermagic=5.10.160 mod_unload ARMv7 thumb2 p2v8 \0name='+name.encode()+b'\0'

class ZramProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name)
        self.sdk=self.base/'sdk';self.bundle=self.base/'bundle';self.root=self.base/'root'
        put(self.sdk/'.BoardConfig.mk','export RK_KERNEL_DTS=rv1103g-luckfox-pico-mini.dts\nexport RK_KERNEL_DEFCONFIG=luckfox_rv1106_linux_defconfig\n')
        self.defconfig=put(self.sdk/'sysdrv/source/kernel/arch/arm/configs/luckfox_rv1106_linux_defconfig','CONFIG_EXISTING_CAMERA=y\n')
        self.revision=patch.object(z,'sdk_revision');self.revision.start();self.addCleanup(self.revision.stop)
    def tearDown(self):self.temp.cleanup()

    def test_disabled_profile_has_no_side_effect(self):
        put(self.bundle/'manifest.json','{}');self.assertFalse(z.selected(self.bundle))
        self.assertEqual(self.defconfig.read_text(),'CONFIG_EXISTING_CAMERA=y\n')
        put(self.bundle/'manifest.json','{"memoryProfile":"unknown"}')
        with self.assertRaises(ValueError):z.selected(self.bundle)

    def test_guarded_kernel_options_idempotent_and_preserve_camera(self):
        z.configure_kernel(self.sdk);first=self.defconfig.read_text();z.configure_kernel(self.sdk)
        self.assertEqual(first,self.defconfig.read_text());self.assertIn('CONFIG_EXISTING_CAMERA=y',first)
        self.assertEqual(z.states(first)['CONFIG_ZSMALLOC'],'m');self.assertEqual(z.states(first)['CONFIG_ZRAM'],'m')
        self.assertEqual(z.states(first)['CONFIG_ZRAM_WRITEBACK'],'n')
        self.defconfig.write_text(first.replace('CONFIG_ZRAM=m','CONFIG_ZRAM=y'))
        with self.assertRaises(ValueError):z.configure_kernel(self.sdk)

    def test_foreign_board_and_duplicate_option_rejected(self):
        put(self.sdk/'.BoardConfig.mk','export RK_KERNEL_DTS=other.dts\n')
        with self.assertRaises(ValueError):z.configure_kernel(self.sdk)
        with self.assertRaises(ValueError):z.states('CONFIG_ZRAM=m\nCONFIG_ZRAM=y\n')

    def fixture(self):
        config='\n'.join(k+'='+v if v!='n' else '# '+k+' is not set' for k,v in z.REQUIRED.items())+'\n'
        kernel=put(self.sdk/'sysdrv/source/objs_kernel/.config',config)
        sha=hashlib.sha256(kernel.read_bytes()).hexdigest()
        put(self.bundle/'payload/kernel-camera-abi.json',json.dumps({'kernelConfigSha256':sha}))
        for name in ['zsmalloc','zram']:
            path=self.sdk/'sysdrv/out/kernel_drv_ko'/(name+'.ko');path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(fake_module(name))
        for name in ['enable-zram-image.sh.in','S20zram']:
            put(self.bundle/'image-profiles'/name,(ROOT/'scripts/image-profiles'/name).read_text())
        launcher=put(self.root/'usr/bin/shieldsigner-launch','#!/bin/sh\nset -eu\numask 077\nexec python3 app.py\n');launcher.chmod(0o755)
        (self.root/'etc/init.d').mkdir(parents=True)
        camera={'kernelInputs':{'kernelConfigSha256':sha},'startupSha256':{'usr/bin/shieldsigner-launch':z.digest(launcher)},'startupModes':{'usr/bin/shieldsigner-launch':0o755}}
        put(self.root/z.INSTALL/'image-installation.json',json.dumps(camera))
        return kernel

    def test_install_adds_init_launcher_gate_and_all_strict_receipt_entries(self):
        self.fixture();result=z.install(self.root,self.sdk,self.bundle)
        self.assertEqual(result['logicalDiskBytes'],16777216);self.assertFalse(result['writeback'])
        launcher=self.root/'usr/bin/shieldsigner-launch';self.assertIn('enable-zram-image.sh\n',launcher.read_text())
        record=json.loads((self.root/z.INSTALL/'image-installation.json').read_text())
        for name,sha in record['startupSha256'].items():
            self.assertEqual(z.digest(self.root/name),sha)
            self.assertEqual((self.root/name).stat().st_mode&0o777,record['startupModes'][name])
        self.assertEqual(z.verify(self.root)['filesVerified'],4)
        for line in z.RUNTIME_LINES:self.assertIn(line,launcher.read_text().splitlines())
        (self.root/'etc/init.d/S20zram').write_text('# changed\n')
        with self.assertRaises(ValueError):z.verify(self.root)

    def test_stale_kernel_receipt_and_changed_launcher_fail_closed(self):
        kernel=self.fixture();kernel.write_text(kernel.read_text()+'CONFIG_EXTRA=y\n')
        with self.assertRaises(ValueError):z.install(self.root,self.sdk,self.bundle)
        kernel.write_text(kernel.read_text().replace('CONFIG_EXTRA=y\n',''))
        (self.root/'usr/bin/shieldsigner-launch').write_text('# foreign\n')
        with self.assertRaises(ValueError):z.install(self.root,self.sdk,self.bundle)

    def test_optin_hooks_order_and_prior_profile_reversibility(self):
        original='''    print_step "Building Kernel"
    sdk_build kernel
    print_step "Building Rootfs"
    sdk_build rootfs
    # Non-dev (production) rootfs hardening:
    # with CI via patch-oem-pre-hook.sh.
    if [[ "$SEEDSIGNER_BUILD_VARIANT" == "non-dev" ]]; then
    sdk_build firmware
'''
        desired=hooks.patched('opt/luckfox/os-build.sh',original)
        self.assertLess(desired.index('--kernel'),desired.index('    sdk_build kernel'))
        self.assertLess(desired.index('image-overlay.py --rootfs'),desired.index('zram-image-profile.py --rootfs'))
        self.assertGreater(desired.index('zram-image-profile.py --verify'),desired.index('    sdk_build firmware'))
        self.assertNotIn('zram-image-profile.py',hooks.patched('opt/luckfox/os-build.sh',original,memory=False))
        with self.assertRaises(ValueError):hooks.patched('opt/luckfox/os-build.sh',original.replace('Building Kernel','unknown'))

class PackageProfileTests(unittest.TestCase):
    def test_new_profile_requires_explicit_exact_proof(self):
        proof={'memoryProfile':z.PROFILE,'requiredKernelConfig':dict(z.REQUIRED)}
        packager.validate_memory_proof(proof,z.PROFILE,False)
        with self.assertRaises(ValueError):packager.validate_memory_proof({},z.PROFILE,False)
        proof['requiredKernelConfig']['CONFIG_ZRAM_WRITEBACK']='y'
        with self.assertRaises(ValueError):packager.validate_memory_proof(proof,z.PROFILE,False)

    def test_legacy_and_kernel_probe_keep_existing_scope(self):
        packager.validate_memory_proof({},'none',False)
        packager.validate_memory_proof({},z.PROFILE,True)

if __name__=='__main__':unittest.main()
