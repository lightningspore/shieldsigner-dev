"""Verify immutable camera files and selected Linux DTB by packed SD-image readback. Linux squashfs-tools required. This does not boot or flash the image."""
import shutil
import re
import zlib
import argparse, hashlib, json, mmap, pathlib, struct, subprocess

def fdt_properties(data):
    magic, _, structure, strings, _, _, _, _, _, _ = struct.unpack_from('>10I', data)
    if magic != 3490578157:
        raise ValueError('Invalid compiled DTB')
    cursor, stack, nodes = (structure, [], {})
    while True:
        token = struct.unpack_from('>I', data, cursor)[0]
        cursor += 4
        if token == 1:
            end = data.index(0, cursor)
            stack.append(data[cursor:end].decode())
            cursor = end + 4 & ~3
            nodes.setdefault('/' + '/'.join(filter(None, stack)), {})
        elif token == 2:
            stack.pop()
        elif token == 3:
            size, name_offset = struct.unpack_from('>II', data, cursor)
            cursor += 8
            end = data.index(0, strings + name_offset)
            name = data[strings + name_offset:end].decode()
            nodes['/' + '/'.join(filter(None, stack))][name] = data[cursor:cursor + size]
            cursor = cursor + size + 3 & ~3
        elif token == 9:
            return nodes
        elif token != 4:
            raise ValueError('Unsupported DTB token')

def qemu_arm_wrapper(binary):
    """Forward runtime geometry and other arguments to the packed ARM binary."""
    import shlex
    return '#!/bin/sh\nexec qemu-arm -cpu cortex-a7 '+shlex.quote(str(binary.resolve()))+' "$@"\n'

def verify_carrier_rootfs(root,bundle,pcsc_service_sha='51d83ab6cb5f8e532818fb4fa59c02c25bca367233f4204a8523521579cb32a6'):
    """Check packed configuration, never acquire GPIO/SPI or start services."""
    import shlex
    root=pathlib.Path(root).resolve();bundle=pathlib.Path(bundle)
    manifest=json.loads((bundle/'manifest.json').read_text())
    if manifest.get('ioProfile')!='carrier':return None
    def require(condition,message):
        if not condition:raise ValueError(message)
    data=json.loads((root/'opt/src/seedsigner/hardware/io_config.json').read_text())
    profiles=[p for p in data['models'] if p.get('shortname')=='FOX_22']
    require(len(profiles)==1,'Packed image requires exactly one carrier FOX_22 profile')
    profile=profiles[0];display=profile['display']
    expected={'dc':['/dev/gpiochip-bank1',20],'rst':['/dev/gpiochip-bank1',19],
              'bl':'disabled','spi_bus':0,'spi_device':0,'spi_hz':10_000_000}
    require(all(display.get(k)==v for k,v in expected.items()) and display.get('cs')!='disabled','Packed carrier display pin/clock/CS mismatch')
    pins={'KEY_UP':(1,25),'KEY_DOWN':(1,23),'KEY_LEFT':(1,24),'KEY_RIGHT':(0,4),
          'KEY_PRESS':(1,22),'KEY1':(4,16),'KEY2':(4,17),'KEY3':(1,21)}
    require(profile['buttons']=={k:[f'/dev/gpiochip-bank{b}',n,'pull_up'] for k,(b,n) in pins.items()},'Packed carrier button map/bias mismatch')
    bank_init=root/'etc/init.d/S41shieldsigner-gpio-banks'
    require(bank_init.is_file() and bank_init.stat().st_mode & 0o111 and '--gpio-aliases' in bank_init.read_text(),'Packed GPIO bank startup missing')
    require((root/'usr/lib/shieldsigner-camera/gpio-bank-profile.py').read_bytes()==(bundle/'configure-image-io-profile.py').read_bytes(),'Packed bank-label helper differs from reviewed bundle')
    pulls=root/'usr/bin/configure-gpio.sh'
    require(pulls.is_file() and hashlib.sha256(pulls.read_bytes()).hexdigest()=='695d8df632f8a11610dec6c4d77c120b014d387ec3e59d332c36319dd7108ce5' and pulls.stat().st_mode & 0o111,'Packed button pull-up setup differs from pinned source')
    startup=(root/'start-seedsigner.sh').read_text()
    require('/usr/bin/configure-gpio.sh 2>&1' in startup and '/usr/bin/shieldsigner-launch >>' in startup and startup.index('/usr/bin/configure-gpio.sh 2>&1')<startup.index('/usr/bin/shieldsigner-launch >>'),'Packed button pull-up setup must precede application launch')
    plan_path=bundle/'lvgl-overlay/integration-plan.json'
    plan=json.loads(plan_path.read_text()) if plan_path.exists() else {}
    panel=plan.get('panelProfile');geometry=plan.get('displayConfiguration')
    if geometry=='st7789_320x240':
        require(panel=='hothmi_htm_tft028a16_spi','Packed pill stage requires explicit HOTHMI panel profile')
        require(json.loads((root/'usr/share/shieldsigner-lvgl/panel-profile.json').read_text())=={'profile':panel},'Packed HOTHMI profile mismatch')
        require(json.loads((root/'opt/src/settings.json').read_text())=={'display_config':geometry},'Packed display first-run template mismatch')
    def fields(path):
        result={}
        for line in path.read_text().splitlines():
            words=shlex.split(line,comments=True)
            if words:
                require(words[0] not in result,'Duplicate reader configuration field')
                result[words[0]]=words[1:]
        return result
    reader=fields(root/'etc/reader.conf.d/sec1210')
    require(reader.get('DEVICENAME')==['/dev/ttyS2:SEC1210UR2'],'Packed reader must select UART2 SEC1210UR2')
    legacy=root/'etc/readers.d/sec1210'
    if legacy.exists():require(fields(legacy)==reader,'Packed legacy reader configuration disagrees')
    library=reader.get('LIBPATH',[])
    require(len(library)==1 and library[0].startswith('/'),'Missing reader library path')
    lib=root/library[0].lstrip('/')
    for _ in range(16):
        if not lib.is_symlink():break
        target=lib.readlink();lib=root/str(target).lstrip('/') if target.is_absolute() else lib.parent/target
    lib=lib.resolve();require(root in lib.parents and lib.is_file(),'Reader library missing or outside extracted rootfs')
    library_bytes=lib.read_bytes();header=library_bytes[:20]
    require(header[:6]==b'\x7fELF\x01\x01' and len(header)==20 and struct.unpack_from('<H',header,18)[0]==40,'Packed reader library is not 32-bit little-endian ARM ELF')
    require(b'SEC1210UR2' in library_bytes,'Packed reader library lacks the selected UR2 identity')
    service=root/'etc/init.d/S60pcscd'
    require(hashlib.sha256(service.read_bytes()).hexdigest()==pcsc_service_sha,'Packed PCSC startup differs from reviewed active service')
    require(service.stat().st_mode & 0o111,'Packed PCSC service is not executable')
    inittab=root/'etc/inittab'
    active='\n'.join(line.split('#',1)[0] for line in inittab.read_text().splitlines())
    require(not re.search(r'\b(?:ttyS2|ttyFIQ0)\b',active),'Packed getty/init still uses reader UART')
    return {'ioProfile':'carrier','displayHz':display['spi_hz'],'buttonsChecked':8,
            'gpioSelectorPolicy':'kernel-label-aliases','gpioBankStartupVerified':True,
            'buttonPullUpSetupSourceVerified':True,'pullUpSetupBeforeApp':True,
            'firstRunDisplayConfiguration':geometry,'panelProfile':panel,
            'readerDevice':reader['DEVICENAME'][0],'readerLibraryArmElf':True,'readerUr2IdentityPresent':True,
            'pcscServiceSha256':pcsc_service_sha,'serialGettyConflict':False,
            'scope':'Packed configuration and library architecture, not boot, GPIO voltages or card operation'}
p = argparse.ArgumentParser()
p.add_argument('--image', type=pathlib.Path, required=True)
p.add_argument('--bundle', type=pathlib.Path, required=True)
p.add_argument('--output', type=pathlib.Path, required=True)
p.add_argument('--qemu-python', action='store_true', help='Run packed ARM Python/app direct-data checks with qemu-arm; no camera or boot')
a = p.parse_args()
a.image = a.image.resolve()
a.bundle = a.bundle.resolve()
a.output = a.output.resolve()
if not shutil.which('unsquashfs'):
    p.error('Linux squashfs-tools is required (unsquashfs)')
if a.qemu_python and (not shutil.which('qemu-arm')):
    p.error('Explicit qemu-user qemu-arm required for --qemu-python; binfmt registration is unnecessary')
a.output.mkdir(parents=True, exist_ok=False)
parse = fdt_properties
sha = hashlib.sha256()
size = 0
with a.image.open('rb') as f:
    while (chunk := f.read(8 * 1024 * 1024)):
        sha.update(chunk)
        size += len(chunk)
report = {'helperSha256': hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(), 'imageSha256': sha.hexdigest(), 'imageBytes': size, 'imageBootQualified': False, 'scope': 'Packed image static readback, not boot validation'}
with a.image.open('rb') as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
    environment = bytes(mm[:32768])
    if len(environment) != 32768 or struct.unpack_from('<I', environment)[0] != zlib.crc32(environment[4:]) & 0xffffffff:
        raise ValueError('Invalid fixed32KiB U-Boot environment CRC')
    payload = environment[4:]
    end = payload.find(b'\0\0')
    if end < 0 or any(payload[end+2:]):
        raise ValueError('Unexpected U-Boot environment termination/padding')
    entries = [entry for entry in payload[:end].split(b'\0') if entry.startswith(b'sys_bootargs=')]
    values = re.findall(rb'(?:^|\s)rk_dma_heap_cma=(\S+)', entries[0]) if len(entries) == 1 else []
    expected_cma = json.loads((a.bundle / 'manifest.json').read_text()).get('cameraCmaSize')
    if expected_cma is not None and (len(entries) != 1 or values != [expected_cma.encode()]):
        raise ValueError('Packed boot CMA differs from requested camera bundle')
    report['bootCmaSize'] = values[0].decode() if len(values) == 1 else None
    report['bootEnvironmentCrc32'] = hex(struct.unpack_from('<I', environment)[0])
    squashes = []
    pos = 0
    while (pos := mm.find(b'hsqs', pos)) >= 0:
        try:
            block = struct.unpack_from('<I', mm, pos + 12)[0]
            major = struct.unpack_from('<H', mm, pos + 28)[0]
            used = struct.unpack_from('<Q', mm, pos + 40)[0]
            if major == 4 and block >= 4096 and (not block & block - 1) and (96 <= used <= len(mm) - pos):
                squashes.append((pos, used))
        except struct.error:
            pass
        pos += 4
    if len(squashes) != 1:
        raise ValueError(('Expected exactly one packed rootfs', squashes))
    off, used = squashes[0]
    sq = a.output / 'rootfs.squashfs'
    sq.write_bytes(mm[off:off + used])
    report['rootfs'] = {'offset': off, 'bytesUsed': used}
    fits = []
    pos = 0
    while (pos := mm.find(b'\xd0\r\xfe\xed', pos)) >= 0:
        try:
            total = struct.unpack_from('>I', mm, pos + 4)[0]
            if not 40 <= total <= 4 * 1024 * 1024:
                raise ValueError('size')
            tree = parse(mm[pos:pos + total])
            cfgname = tree.get('/configurations', {}).get('default', b'').rstrip(b'\x00').decode()
            cfg = tree.get('/configurations/' + cfgname, {})
            if 'kernel' in cfg and 'fdt' in cfg:
                name = cfg['fdt'].rstrip(b'\x00').decode()
                node = tree['/images/' + name]
                if 'data' in node:
                    dtb = node['data']
                else:
                    datapos = int.from_bytes(node['data-position'], 'big') if 'data-position' in node else (total + 3 & ~3) + int.from_bytes(node['data-offset'], 'big')
                    length = int.from_bytes(node['data-size'], 'big')
                    dtb = mm[pos + datapos:pos + datapos + length]
                props = parse(dtb)
                model = props['/']['model'].rstrip(b'\x00').decode()
                digest = hashlib.sha256(dtb).hexdigest()
                expected = json.loads((a.bundle / 'payload/kernel-camera-abi.json').read_text())
                assert digest == expected['compiledDtbSha256'] and model == expected['compiledDtbModel'], 'Packed active boot DTB differs from reviewed SDK'
                for path, prop in tree.items():
                    if path.startswith('/images/' + name + '/') and 'algo' in prop:
                        algo = prop['algo'].rstrip(b'\x00').decode()
                        assert hashlib.new(algo, dtb).digest() == prop['value'], 'FIT DTB hash mismatch'
                fits.append({'fitOffset': pos, 'defaultConfiguration': cfgname, 'dtbSha256': digest, 'model': model})
                (a.output / 'boot.dtb').write_bytes(dtb)
        except (KeyError, UnicodeError, struct.error, IndexError):
            pass
        except ValueError as e:
            if str(e) != 'size':
                raise
        pos += 4
    if len(fits) != 1:
        raise ValueError(('Expected one active Linux FIT', fits))
    report['linuxBootFits'] = fits
root = a.output / 'rootfs'
subprocess.run(['unsquashfs', '-no-xattrs', '-d', str(root), str(sq)], check=True, stdout=subprocess.DEVNULL)
result = subprocess.run(['python3', str(a.bundle / 'image-overlay.py'), '--verify', str(root)], check=True, text=True, stdout=subprocess.PIPE)
report['rootfsVerification'] = json.loads(result.stdout)
profile_manifest = json.loads((a.bundle / 'manifest.json').read_text())
carrier_config=verify_carrier_rootfs(root,a.bundle)
if carrier_config is not None:report['carrierConfigurationVerification']=carrier_config
for key, value, helper, field in [
    ('memoryProfile', 'zram16-lzo', 'zram-image-profile.py', 'memoryProfileVerification'),
    ('lcdBackend', 'rust', 'lcd-image-profile.py', 'lcdProfileVerification'),
]:
    if profile_manifest.get(key) == value:
        checked = subprocess.run(['python3', str(a.bundle / helper), '--verify', str(root)], check=True, text=True, stdout=subprocess.PIPE)
        report[field] = json.loads(checked.stdout)
lvgl_helper = a.bundle / 'lvgl-overlay/overlay-apply.py'
if lvgl_helper.is_file():
    checked = subprocess.run(['python3', str(lvgl_helper), '--verify', str(root)], check=True, text=True, stdout=subprocess.PIPE)
    report['lvglOverlayVerification'] = json.loads(checked.stdout)
if a.qemu_python:
    smoke = a.output / 'public-python-api-smoke.py'
    smoke.write_text('"""Public direct-data API smoke; no pixels, worker, camera, or boot claim."""\nimport hashlib,json,sys\nfrom pathlib import Path\nroot=Path(sys.argv[1]); sys.path.insert(0,str(root/\'opt/src\'))\nimport Cryptodome\nfrom Cryptodome.Cipher import AES\nassert Cryptodome.__version__==\'3.23.0\'\nassert AES.new(bytes(16),AES.MODE_ECB).encrypt(bytes(16)).hex()==\'66e94bd4ef8a2c3b884cfa59ca342b2e\'\nfrom seedsigner.models.decode_qr import DecodeQR,DecodeQRStatus\nfrom seedsigner.helpers.ur2.ur import UR\nfrom seedsigner.helpers.ur2.ur_encoder import UREncoder\nfrom urtypes.crypto import PSBT as UR_PSBT\nfrom embit import bip39,psbt,transaction,script\nfor length in (16,32):\n entropy=bytes(range(length)); decoder=DecodeQR()\n assert decoder.add_data(entropy)==DecodeQRStatus.COMPLETE\n assert decoder.get_seed_phrase()==bip39.mnemonic_from_bytes(entropy).split()\ntx=transaction.Transaction(vin=[transaction.TransactionInput(bytes(32),0)],vout=[transaction.TransactionOutput(0,script.Script(b\'\\x6a\\x4c\\xc8\'+bytes(range(200))))])\npayload=psbt.PSBT(tx).serialize(); encoder=UREncoder(UR(\'crypto-psbt\',UR_PSBT(payload).to_cbor()),max_fragment_len=60)\nfragments=[]\nfor _ in range(20):\n fragments.append(encoder.next_part())\n if encoder.is_complete(): break\nassert len(fragments)>1\nframes=list(reversed(fragments)); decoder=DecodeQR()\nfor part in [frames[0],*frames]: decoder.add_data(part.encode(\'ascii\'))\nassert decoder.complete and decoder.get_data_psbt()==payload\nprint(json.dumps({\'passed\':True,\'pythonVersion\':sys.version,\'cryptodomeVersion\':Cryptodome.__version__,\'aesKnownVector\':True,\'compactSeedEntropyBytes\':[16,32],\'animatedUr\':{\'fragments\':len(fragments),\'reversedOrder\':True,\'duplicateHandled\':True,\'byteExactPsbt\':True},\'scope\':\'Actual packed Python/app direct-data APIs under explicit userspace QEMU, no QR pixels or camera\',\'imageBootQualified\':False}))\n')
    command = ['qemu-arm', '-cpu', 'cortex-a7', '-L', str(root), '-E', 'PYTHONHOME=' + str(root / 'usr'), '-E', 'PYTHONPATH=' + str(root / 'usr/lib/python3.12/site-packages'), '-E', 'LD_LIBRARY_PATH=' + str(root / 'lib') + ':' + str(root / 'usr/lib'), '-E', 'PYTHONDONTWRITEBYTECODE=1', str(root / 'usr/bin/python3.12'), str(smoke), str(root)]
    result = subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE)
    report['qemuPythonDirectDataSmoke'] = json.loads(result.stdout)
    if profile_manifest.get('lcdBackend') == 'rust':
        lcd_smoke = a.output / 'public-rust-lcd-smoke.py'
        lcd_smoke.write_text("""import array,json,sys
from pathlib import Path
root=Path(sys.argv[1])
sys.path[:0]=[str(root/'usr/lib/shieldsigner-camera/python'),str(root/'opt/src')]
import shieldsigner_lcd as native
from PIL import Image
rgb=bytes(channel for n in range(256) for channel in (n,n*7%256,255-n))
image=Image.frombytes('RGB',(256,1),rgb)
legacy=array.array('H',image.convert('BGR;16').tobytes());legacy.byteswap()
assert native.pack_rgb(rgb)==legacy.tobytes()
assert native.pack_rgb(bytes([255,0,0,0,255,0,0,0,255])).hex()=='f80007e0001f'
try:native.pack_rgb(b'x')
except ValueError:pass
else:raise AssertionError('Malformed pixel buffer accepted')
from shieldsigner_lcd_driver import install
info=install(root/'opt/src')
assert info['kind']=='rust-pyo3-lcd-frame-transport'
print(json.dumps({'passed':True,'nativeAbiImport':True,'originalPillowRgb565EquivalentPixels':256,'primaryColors':True,'malformedBufferRejected':True,'reviewedShimRegistration':True,'scope':'Packed ARM extension and shim; no display driver instantiated','imageBootQualified':False}))
""")
        lcd_command = command[:-2] + [str(lcd_smoke), str(root)]
        checked = subprocess.run(lcd_command, check=True, text=True, stdout=subprocess.PIPE)
        report['qemuRustLcdSmoke'] = json.loads(checked.stdout)
    if profile_manifest.get('frontendBackend') == 'rust':
        import shlex
        reader = root / 'usr/lib/shieldsigner-camera/shieldsigner-qr-reader'
        wrapper = a.output / 'packed-reader-qemu'
        wrapper.write_text('#!/bin/sh\nexec qemu-arm -cpu cortex-a7 ' + shlex.quote(str(reader.resolve())) + '\n')
        wrapper.chmod(0o700)
        frontend_command = command[:-2] + [str(a.bundle / 'native-frontend-smoke.py'), str(root), str(wrapper.resolve())]
        checked = subprocess.run(frontend_command, check=True, text=True, stdout=subprocess.PIPE)
        report['qemuNativeFrontendSmoke'] = json.loads(checked.stdout)
    if lvgl_helper.is_file():
        import shlex
        native = root / 'usr/lib/shieldsigner-lvgl/shieldsigner-lvgl'
        wrapper = a.output / 'packed-lvgl-qemu'
        wrapper.write_text(qemu_arm_wrapper(native))
        wrapper.chmod(0o700)
        smoke = a.output / 'public-lvgl-packed-smoke.py'
        smoke.write_text("""import json,sys
from pathlib import Path
root=Path(sys.argv[1]);wrapper=Path(sys.argv[2]);work=Path(sys.argv[3])
prefix=root/'usr/lib/shieldsigner-lvgl'
sys.path[:0]=[str(prefix/'python'),str(root/'opt/src'),str(root/'usr/lib/shieldsigner-camera/python')]
from app import options,check
from hothmi import image_profile
panel=image_profile(root/'usr/share/shieldsigner-lvgl/panel-profile.json')
arguments=['--app-root',str(root/'opt/src'),'--camera-root',str(root/'usr/lib/shieldsigner-camera/python'),'--binary',str(prefix/'shieldsigner-lvgl'),'--settings',str(work/'unused-public-settings.json'),'--check']
if panel:arguments.extend(['--panel-profile',panel])
count=check(options(arguments))
width=320 if panel else 240
template_loaded=False
if panel:
 import os
 from seedsigner.models.settings import Settings
 before=Path.cwd()
 try:
  os.chdir(root/'opt/src');Settings.SETTINGS_FILENAME=str(work/'unused-public-settings.json')
  settings=Settings.get_instance()
  assert settings.get_value('display_config',default_if_none=True)=='st7789_320x240'
  template_loaded=True
 finally:os.chdir(before)
from transport import NativeHost
from contracts import configuration
rectangles=[0];extents=[-1,-1]
def pixels(area,data):
 rectangles[0]+=1;extents[0]=max(extents[0],area[2]);extents[1]=max(extents[1],area[3])
host=NativeHost(wrapper,pixels,timeout=30,width=width,height=240)
try:
 host.send('screen',name='button_list_screen',request=1,config=dict(top_nav=dict(title='Public packed fixture'),button_list=['One','Two']))
 assert host.next_event()==dict(event='screen_ready',request=1)
 host.send('key',key=10,pressed=True);host.send('key',key=10,pressed=False)
 selected=host.next_event()
 assert selected['event']=='button_selected' and selected['index']==0 and type(selected['scroll_y']) is int
 value='public'+chr(0)+'literal'+chr(92)+'0'
 builder,cfg=configuration(type('SeedAddPassphraseScreen',(),{}),dict(passphrase=value))
 host.send('screen',name=builder,request=2,config=cfg)
 assert host.next_event()==dict(event='screen_ready',request=2)
 host.send('key',key=ord('3'),pressed=True);host.send('key',key=ord('3'),pressed=False)
 assert host.next_event()==dict(event='passphrase_result',text=value,back=False)
 host.send('clear');assert host.next_event()==dict(event='screen_cleared')
 assert rectangles[0]>0
 assert extents==[width-1,239]
finally:host.close()
assert not (work/'unused-public-settings.json').exists()
print(json.dumps(dict(passed=True,sourceGuards=count,nativeManifestVerified=True,packedPythonAndRenderer=True,publicMenuSelection=True,nulPassphraseExact=True,renderedRectangles=rectangles[0],maxRenderedCoordinate=extents,panelProfile=panel,displayWidth=width,firstRunTemplateLoaded=template_loaded,noDevicesAcquired=True,noSettingsWritten=True,imageBootQualified=False,scope='Packed ARM Python/adapters/native renderer under userspace QEMU; no GPIO/SPI/camera/boot claim')))
""")
        checked = subprocess.run(command[:-2] + [str(smoke), str(root), str(wrapper.resolve()), str(a.output)], check=True, text=True, stdout=subprocess.PIPE)
        report['qemuLvglSmoke'] = json.loads(checked.stdout)
(a.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
