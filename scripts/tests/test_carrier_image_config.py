"""Packed configuration rejection tests; no image/device execution."""
import ast,hashlib,json,pathlib,struct,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
namespace=dict(hashlib=hashlib,json=json,pathlib=pathlib,struct=struct,__name__='carrier_image_test')
import re,os,subprocess,sys
namespace['re']=re
source=ast.parse((ROOT/'scripts/verify-os-image.py').read_text())
node=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='verify_carrier_rootfs')
exec(compile(ast.Module(body=[node],type_ignores=[]),'verify-os-image.py','exec'),namespace)
verify=namespace['verify_carrier_rootfs']
node=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='qemu_arm_wrapper')
exec(compile(ast.Module(body=[node],type_ignores=[]),'verify-os-image.py','exec'),namespace)

class CarrierImageConfigTests(unittest.TestCase):
 def setUp(self):
  temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
  self.root=pathlib.Path(temporary.name)/'root';self.bundle=pathlib.Path(temporary.name)/'bundle'
  def write(relative,value):
   p=self.root/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(value)
  self.write=write
  write('usr/bin/configure-gpio.sh',(ROOT/'reference/research/firmware/configure-gpio-e7589465.sh').read_text());(self.root/'usr/bin/configure-gpio.sh').chmod(0o755)
  write('start-seedsigner.sh','/usr/bin/configure-gpio.sh 2>&1 | tee /tmp/public-log\n/usr/bin/shieldsigner-launch >> /tmp/public-app-log\n')
  data=json.loads((ROOT/'reference/research/firmware/io-config-efdd1cfd.json').read_text())
  fox=next(p for p in data['models'] if p['shortname']=='FOX_22');fox['display']['spi_hz']=10_000_000
  for value in [*fox['display'].values(),*fox['buttons'].values()]:
   if isinstance(value,list) and value and isinstance(value[0],str):value[0]=re.sub(r'^/dev/gpiochip(\d+)$',r'/dev/gpiochip-bank\1',value[0])
  write('opt/src/seedsigner/hardware/io_config.json',json.dumps(data))
  write('opt/src/settings.json','{"display_config":"st7789_320x240"}')
  write('usr/share/shieldsigner-lvgl/panel-profile.json','{"profile":"hothmi_htm_tft028a16_spi"}')
  write('etc/reader.conf.d/sec1210','DEVICENAME /dev/ttyS2:SEC1210UR2\nLIBPATH /usr/lib/serial.so\n')
  write('etc/init.d/S60pcscd','#!/bin/sh\nexec /usr/sbin/pcscd\n');(self.root/'etc/init.d/S60pcscd').chmod(0o755)
  self.service_sha=hashlib.sha256((self.root/'etc/init.d/S60pcscd').read_bytes()).hexdigest()
  write('etc/inittab','::sysinit:/etc/init.d/rcS\n')
  write('etc/init.d/S41shieldsigner-gpio-banks','#!/bin/sh\nexec python3 gpio-bank-profile.py --gpio-aliases\n');(self.root/'etc/init.d/S41shieldsigner-gpio-banks').chmod(0o755)
  self.library=b'\x7fELF\x01\x01'+bytes(12)+struct.pack('<H',40)+b'\0SEC1210UR2\0'
  (self.root/'usr/lib').mkdir(parents=True,exist_ok=True);(self.root/'usr/lib/serial.so').write_bytes(self.library)
  (self.bundle/'lvgl-overlay').mkdir(parents=True)
  (self.bundle/'manifest.json').write_text('{"ioProfile":"carrier"}')
  helper=(ROOT/'scripts/configure-image-io-profile.py').read_bytes();(self.bundle/'configure-image-io-profile.py').write_bytes(helper)
  (self.root/'usr/lib/shieldsigner-camera').mkdir(parents=True,exist_ok=True);(self.root/'usr/lib/shieldsigner-camera/gpio-bank-profile.py').write_bytes(helper)
  (self.bundle/'lvgl-overlay/integration-plan.json').write_text('{"panelProfile":"hothmi_htm_tft028a16_spi","displayConfiguration":"st7789_320x240"}')
 def check(self):return verify(self.root,self.bundle,self.service_sha)
 def test_complete_carrier_configuration(self):
  result=self.check();self.assertEqual(result['buttonsChecked'],8);self.assertEqual(result['displayHz'],10_000_000)
  self.assertTrue(result['readerLibraryArmElf']);self.assertTrue(result['readerUr2IdentityPresent'])
 def test_missing_bank_startup_is_rejected(self):
  (self.root/'etc/init.d/S41shieldsigner-gpio-banks').unlink()
  with self.assertRaisesRegex(ValueError,'bank startup'):self.check()
 def test_changed_bank_helper_is_rejected(self):
  (self.root/'usr/lib/shieldsigner-camera/gpio-bank-profile.py').write_text('raise RuntimeError()')
  with self.assertRaisesRegex(ValueError,'bank-label helper'):self.check()
 def test_pull_up_setup_must_precede_app(self):
  self.write('start-seedsigner.sh','/usr/bin/shieldsigner-launch >> /tmp/public-log\n/usr/bin/configure-gpio.sh 2>&1\n')
  with self.assertRaisesRegex(ValueError,'precede application'):self.check()
 def test_bench_reset_pin_is_rejected(self):
  p=self.root/'opt/src/seedsigner/hardware/io_config.json';data=json.loads(p.read_text());next(x for x in data['models'] if x['shortname']=='FOX_22')['display']['rst']=['/dev/gpiochip1',25];p.write_text(json.dumps(data))
  with self.assertRaisesRegex(ValueError,'display'):self.check()
 def test_wrong_first_run_geometry_is_rejected(self):
  self.write('opt/src/settings.json','{"display_config":"st7789_240x240"}')
  with self.assertRaisesRegex(ValueError,'template'):self.check()
 def test_wrong_reader_identity_and_missing_driver_support_are_rejected(self):
  p=self.root/'etc/reader.conf.d/sec1210';original=p.read_text();p.write_text(original.replace('UR2','URT'))
  with self.assertRaisesRegex(ValueError,'UR2'):self.check()
  p.write_text(original);(self.root/'usr/lib/serial.so').write_bytes(self.library.replace(b'SEC1210UR2',b'notreader'))
  with self.assertRaisesRegex(ValueError,'UR2 identity'):self.check()
 def test_held_service_and_reader_getty_are_rejected(self):
  p=self.root/'etc/init.d/S60pcscd';original=p.read_text();p.write_text('#!/bin/sh\nexit 0\n')
  with self.assertRaisesRegex(ValueError,'PCSC'):self.check()
  p.write_text(original);self.write('etc/inittab','ttyS2::respawn:/sbin/getty ttyS2 115200\n')
  with self.assertRaisesRegex(ValueError,'getty'):self.check()

class QemuWrapperTests(unittest.TestCase):
 def test_geometry_and_space_containing_paths_reach_renderer(self):
  with tempfile.TemporaryDirectory() as tmp:
   work=pathlib.Path(tmp);qemu=work/'qemu-arm'
   qemu.write_text('#!'+sys.executable+'\nimport json,sys\nprint(json.dumps(sys.argv[1:]))\n');qemu.chmod(0o755)
   binary=work/'public renderer';wrapper=work/'wrapper'
   wrapper.write_text(namespace['qemu_arm_wrapper'](binary));wrapper.chmod(0o755)
   result=subprocess.check_output([str(wrapper),'--width','320','--height','240'],env={**os.environ,'PATH':str(work)+os.pathsep+os.environ['PATH']},text=True)
   self.assertEqual(json.loads(result),['-cpu','cortex-a7',str(binary.resolve()),'--width','320','--height','240'])

if __name__=='__main__':unittest.main()
