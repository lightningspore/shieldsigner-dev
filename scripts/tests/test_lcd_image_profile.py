"""Structural package/ELF/hook fixtures; no Cargo build or hardware I/O."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
lcd=load('lcd_profile',ROOT/'scripts/image-profiles/lcd-image-profile.py')
package=load('lcd_package_inputs',ROOT/'scripts/prepare-camera-image.py')
overlay=load('lcd_strip_policy',ROOT/'scripts/camera-image-overlay.py')
zram=load('lcd_zram_combination',ROOT/'scripts/image-profiles/zram-image-profile.py')
def put(path,text):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text);return path

def library(libc='libc.so.0'):
    strings=b'\0'+libc.encode()+b'\0libgcc_s.so.1\0PyInit_shieldsigner_lcd\0'
    dyn=struct.pack('<6I',1,1,1,strings.index(b'libgcc'),0,0)
    raw=bytearray(184+len(strings)+len(dyn));raw[:6]=b'\x7fELF\x01\x01';struct.pack_into('<HH',raw,16,3,40)
    struct.pack_into('<I',raw,32,64);struct.pack_into('<HH',raw,46,40,3)
    struct.pack_into('<10I',raw,104,0,3,0,0,184,len(strings),0,0,1,0)
    struct.pack_into('<10I',raw,144,0,6,0,0,184+len(strings),len(dyn),1,0,4,8)
    raw[184:184+len(strings)]=strings;raw[184+len(strings):]=dyn;return raw

class LcdImageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name);self.bundle=self.base/'bundle';self.br=self.base/'br';self.root=self.base/'root'
        self.inputs={'sourceManifestSha256':'a'*64,'buildRecipeSha256':'b'*64,'cargoLockSha256':'c'*64}
        self.data={'lcdBackend':'rust','lcdInputs':self.inputs,'files':{}}
    def tearDown(self):self.tmp.cleanup()

    def test_package_configuration_idempotent_and_foreign_package_rejected(self):
        for name in ['Config.in','shieldsigner-lcd.mk']:put(self.bundle/'lcd-package'/name,(ROOT/'scripts/image-profiles/lcd-package'/name).read_text())
        put(self.br/'package/Config.in','menu "Packages"\nendmenu\n')
        for name in ['.config','configs/luckfox_pico_defconfig','configs/luckfox_pico_w_defconfig']:put(self.br/name,'BR2_TOOLCHAIN_USES_UCLIBC=y\n')
        lcd.configure(self.br,self.bundle,self.data);first=(self.br/'.config').read_text();lcd.configure(self.br,self.bundle,self.data)
        self.assertEqual(first,(self.br/'.config').read_text());self.assertIn('BR2_PACKAGE_SHIELDSIGNER_LCD=y',first)
        text=(self.br/'package/shieldsigner-lcd/shieldsigner-lcd.mk').read_text()
        self.assertIn('--locked --offline',text);self.assertIn('host-rust python3',text);self.assertIn('PYO3_NO_PYTHON=1',text)
        self.assertIn('SHIELDSIGNER_LCD_VERSION = '+'b'*64,text);self.assertNotIn('--rootfs $(TARGET_DIR) --buildroot',text)
        put(self.br/'package/shieldsigner-lcd/Config.in','# foreign\n')
        with self.assertRaises(ValueError):lcd.configure(self.br,self.bundle,self.data)

    def install_fixture(self):
        so=self.root/lcd.INSTALL/'python/shieldsigner_lcd.abi3.so';so.parent.mkdir(parents=True);so.write_bytes(library())
        shim=put(self.root/lcd.INSTALL/'python/shieldsigner_lcd_driver.py','# fixture shim\n')
        self.data['files']['lcd-source/python/shieldsigner_lcd_driver.py']={'sha256':lcd.digest(shim)}
        source=self.base/'package-source';put(source/'python/shieldsigner_lcd_driver.py',shim.read_text());lock=put(source/'Cargo.lock','# fixturelock\n');self.inputs['cargoLockSha256']=lcd.digest(lock)
        launcher=put(self.root/'usr/bin/shieldsigner-launch','#!/bin/sh\nset -eu\nexec python3 app.py\n');launcher.chmod(0o755)
        put(self.root/lcd.INSTALL/'image-installation.json',json.dumps({'startupSha256':{'usr/bin/shieldsigner-launch':lcd.digest(launcher)},'startupModes':{'usr/bin/shieldsigner-launch':0o755}}))
        def version(cmd,**kw):return 'rustc 1.82.0 (fixture)' if 'rustc' in cmd[0] else 'gcc fixture8.3.0\n'
        with patch.object(lcd.subprocess,'check_output',side_effect=version):lcd.record_build(self.root,source,self.bundle,self.data,'gcc',Path('rustc'))
        return so,shim,launcher

    def test_actual_build_receipt_elf_contract_and_strict_install(self):
        so,shim,launcher=self.install_fixture();lcd.install(self.root,self.bundle,self.data)
        self.assertIn('export SHIELDSIGNER_LCD_BACKEND=rust',launcher.read_text());self.assertTrue(lcd.verify(self.root,self.data)['verified'])
        record=json.loads((self.root/lcd.INSTALL/'image-installation.json').read_text())
        for name,sha in record['startupSha256'].items():self.assertEqual(lcd.digest(self.root/name),sha)
        so.write_bytes(library('libc.so.6'))
        with self.assertRaises(ValueError):lcd.verify(self.root,self.data)

    def test_stale_receipt_and_foreign_launcher_rejected(self):
        so,shim,launcher=self.install_fixture();launcher.write_text('# changed\n')
        with self.assertRaises(ValueError):lcd.install(self.root,self.bundle,self.data)
        self.data['lcdInputs']=dict(self.inputs,buildRecipeSha256='d'*64)
        with self.assertRaises(ValueError):lcd.install(self.root,self.bundle,self.data)

    def test_lcd_elf_rejects_nonarm_or_wrong_libc(self):
        p=self.base/'module.so';p.write_bytes(library());self.assertEqual(lcd.elf_info(p)['neededLibraries'],['libc.so.0','libgcc_s.so.1'])
        p.write_bytes(library('libc.so.6'))
        with self.assertRaises(ValueError):lcd.elf_info(p)
        p.write_bytes(b'not ELF')
        with self.assertRaises(ValueError):lcd.elf_info(p)

    def test_locked_vendor_inputs_are_staged_without_compilation(self):
        repo=self.base/'repo';crate=repo/'firmware/lcd-rs'
        for name in ['Cargo.toml','Cargo.lock','build.rs','src/lib.rs','python/shieldsigner_lcd_driver.py']:put(crate/name,'# fixture\n')
        put(repo/'LICENSE','MIT fixture\n')
        for name in ['Config.in','shieldsigner-lcd.mk']:put(repo/'scripts/image-profiles/lcd-package'/name,'recipe\n')
        put(repo/'scripts/image-profiles/lcd-image-profile.py','# helper\n');stage=self.base/'stage';stage.mkdir();files={}
        def vendor(cmd,**kw):
            self.assertIn('vendor',cmd);self.assertIn('--locked',cmd)
            put(Path(kw['cwd'])/'vendor/example-1.0/LICENSE-MIT','MIT fixture\n')
        def add(name,data,mode=0o644):p=stage/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);files[name]=hashlib.sha256(data).hexdigest()
        with patch.object(package,'ROOT',repo),patch.object(package.subprocess,'run',side_effect=vendor):info=package.stage_lcd_inputs(stage,add)
        self.assertEqual(info['libc'],'uclibc');self.assertIn('lcd-source/.cargo/config.toml',files)
        self.assertIn('payload/licenses/lcd-vendored/example-1.0/LICENSE-MIT',files)
        self.assertFalse((stage/'_lcd_vendor_inputs').exists())

    def verify_combination(self, order):
        self.install_fixture()
        sdk=self.base/'sdk'
        config='\n'.join(k+'='+v if v!='n' else '# '+k+' is not set' for k,v in zram.REQUIRED.items())+'\n'
        cfg=put(sdk/'sysdrv/source/objs_kernel/.config',config);sha=zram.digest(cfg)
        put(self.bundle/'payload/kernel-camera-abi.json',json.dumps({'kernelConfigSha256':sha}))
        for name in ['zsmalloc','zram']:
            raw=bytearray(52);raw[:6]=b'\x7fELF\x01\x01';struct.pack_into('<HH',raw,16,1,40)
            file=sdk/'sysdrv/out/kernel_drv_ko'/(name+'.ko');file.parent.mkdir(parents=True,exist_ok=True)
            file.write_bytes(bytes(raw)+b'vermagic=5.10.160 mod_unload ARMv7 thumb2 p2v8 \0name='+name.encode()+b'\0')
        for name in ['S20zram','enable-zram-image.sh.in']:put(self.bundle/'image-profiles'/name,(ROOT/'scripts/image-profiles'/name).read_text())
        (self.root/'etc/init.d').mkdir(parents=True)
        record=self.root/lcd.INSTALL/'image-installation.json';data=json.loads(record.read_text());data['kernelInputs']={'kernelConfigSha256':sha};record.write_text(json.dumps(data))
        with patch.object(zram,'sdk_revision'):
            for name in order:
                if name=='lcd':lcd.install(self.root,self.bundle,self.data)
                else:zram.install(self.root,sdk,self.bundle)
        self.assertTrue(lcd.verify(self.root,self.data)['verified']);self.assertEqual(zram.verify(self.root)['filesVerified'],4)
        record=json.loads(record.read_text())
        for name,sha in record['startupSha256'].items():self.assertEqual(lcd.digest(self.root/name),sha)
        text=(self.root/'usr/bin/shieldsigner-launch').read_text()
        for line in zram.RUNTIME_LINES+['export SHIELDSIGNER_LCD_BACKEND=rust']:self.assertEqual(text.splitlines().count(line),1)

    def test_zram_then_lcd_preserves_complete_runtime_policy(self):
        self.verify_combination(['zram','lcd'])

    def test_lcd_then_zram_preserves_complete_runtime_policy(self):
        self.verify_combination(['lcd','zram'])

    def test_exact_shared_library_strip_exclusion_is_optin(self):
        sdk=self.base/'sdk';source="function __RELEASE_FILESYSTEM_FILES() {\n find src ! \\( -name '*.a' -o -name '*.ko' \\) -print0\n}\nfunction __COPY_FILES() {\n}\n"
        put(sdk/'project/build.sh',source);put(self.bundle/'payload/kernel-camera-abi.json','{"sdkRevision":"pin"}');put(self.bundle/'manifest.json','{}')
        def git(cmd,**kw):return 'pin\n' if 'rev-parse' in cmd else source
        with patch.object(overlay.subprocess,'check_output',side_effect=git):
            baseline=overlay.configure_sdk_strip(sdk,self.bundle);self.assertEqual(len(baseline['excludedPaths']),2)
            put(self.bundle/'manifest.json','{"lcdBackend":"rust"}')
            enabled=overlay.configure_sdk_strip(sdk,self.bundle);self.assertEqual(len(enabled['excludedPaths']),3)
            self.assertIn('shieldsigner_lcd.abi3.so',(sdk/'project/build.sh').read_text())
            self.assertEqual(overlay.configure_sdk_strip(sdk,self.bundle),enabled)
            p=sdk/'project/build.sh';p.write_text(p.read_text().replace('find src','find unknown'))
            with self.assertRaises(ValueError):overlay.configure_sdk_strip(sdk,self.bundle)

if __name__=='__main__':unittest.main()
