"""Verify immutable camera files and selected Linux DTB by packed SD-image readback. Linux squashfs-tools required. This does not boot or flash the image."""
import shutil
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
if a.qemu_python:
    smoke = a.output / 'public-python-api-smoke.py'
    smoke.write_text('"""Public direct-data API smoke; no pixels, worker, camera, or boot claim."""\nimport hashlib,json,sys\nfrom pathlib import Path\nroot=Path(sys.argv[1]); sys.path.insert(0,str(root/\'opt/src\'))\nimport Cryptodome\nfrom Cryptodome.Cipher import AES\nassert Cryptodome.__version__==\'3.23.0\'\nassert AES.new(bytes(16),AES.MODE_ECB).encrypt(bytes(16)).hex()==\'66e94bd4ef8a2c3b884cfa59ca342b2e\'\nfrom seedsigner.models.decode_qr import DecodeQR,DecodeQRStatus\nfrom seedsigner.helpers.ur2.ur import UR\nfrom seedsigner.helpers.ur2.ur_encoder import UREncoder\nfrom urtypes.crypto import PSBT as UR_PSBT\nfrom embit import bip39,psbt,transaction,script\nfor length in (16,32):\n entropy=bytes(range(length)); decoder=DecodeQR()\n assert decoder.add_data(entropy)==DecodeQRStatus.COMPLETE\n assert decoder.get_seed_phrase()==bip39.mnemonic_from_bytes(entropy).split()\ntx=transaction.Transaction(vin=[transaction.TransactionInput(bytes(32),0)],vout=[transaction.TransactionOutput(0,script.Script(b\'\\x6a\\x4c\\xc8\'+bytes(range(200))))])\npayload=psbt.PSBT(tx).serialize(); encoder=UREncoder(UR(\'crypto-psbt\',UR_PSBT(payload).to_cbor()),max_fragment_len=60)\nfragments=[]\nfor _ in range(20):\n fragments.append(encoder.next_part())\n if encoder.is_complete(): break\nassert len(fragments)>1\nframes=list(reversed(fragments)); decoder=DecodeQR()\nfor part in [frames[0],*frames]: decoder.add_data(part.encode(\'ascii\'))\nassert decoder.complete and decoder.get_data_psbt()==payload\nprint(json.dumps({\'passed\':True,\'pythonVersion\':sys.version,\'cryptodomeVersion\':Cryptodome.__version__,\'aesKnownVector\':True,\'compactSeedEntropyBytes\':[16,32],\'animatedUr\':{\'fragments\':len(fragments),\'reversedOrder\':True,\'duplicateHandled\':True,\'byteExactPsbt\':True},\'scope\':\'Actual packed Python/app direct-data APIs under explicit userspace QEMU, no QR pixels or camera\',\'imageBootQualified\':False}))\n')
    command = ['qemu-arm', '-cpu', 'cortex-a7', '-L', str(root), '-E', 'PYTHONHOME=' + str(root / 'usr'), '-E', 'PYTHONPATH=' + str(root / 'usr/lib/python3.12/site-packages'), '-E', 'LD_LIBRARY_PATH=' + str(root / 'lib') + ':' + str(root / 'usr/lib'), '-E', 'PYTHONDONTWRITEBYTECODE=1', str(root / 'usr/bin/python3.12'), str(smoke), str(root)]
    result = subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE)
    report['qemuPythonDirectDataSmoke'] = json.loads(result.stdout)
(a.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
