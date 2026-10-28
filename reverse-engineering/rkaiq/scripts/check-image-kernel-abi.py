#!/usr/bin/env python3
"""Compile actual image SDK UAPI and inspect its config/DTB without boot claims."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import tempfile

from elftools.elf.elffile import ELFFile

ROOT = Path(__file__).resolve().parents[3]


def fdt_properties(data):
    magic, _, structure, strings, _, _, _, _, _, _ = struct.unpack_from('>10I', data)
    if magic != 0xd00dfeed:
        raise ValueError('Invalid compiled DTB')
    cursor, stack, nodes = structure, [], {}
    while True:
        token = struct.unpack_from('>I', data, cursor)[0]
        cursor += 4
        if token == 1:
            end = data.index(0, cursor)
            stack.append(data[cursor:end].decode())
            cursor = (end+4) & ~3
            nodes.setdefault('/' + '/'.join(filter(None, stack)), {})
        elif token == 2:
            stack.pop()
        elif token == 3:
            size, name_offset = struct.unpack_from('>II', data, cursor)
            cursor += 8
            end = data.index(0, strings+name_offset)
            name = data[strings+name_offset:end].decode()
            nodes['/' + '/'.join(filter(None, stack))][name] = data[cursor:cursor+size]
            cursor = (cursor+size+3) & ~3
        elif token == 9:
            return nodes
        elif token != 4:
            raise ValueError('Unsupported DTB token')


def strings(value):
    return [part.decode() for part in value.rstrip(b'\0').split(b'\0')] if value else []


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--uapi', type=Path, required=True, help='Actual SDK include/uapi directory snapshot')
    parser.add_argument('--kernel-config', type=Path, required=True)
    parser.add_argument('--dtb', type=Path, required=True)
    parser.add_argument('--sdk-source', type=Path, required=True,
                        help='Read-only SDK source snapshot, including generated utsrelease.h and camera drivers')
    parser.add_argument('--sdk-revision', required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument("--image-variant", choices=["production", "dev"], default="production")
    args = parser.parse_args()
    if args.report.exists():
        parser.error('Choose a new report filename')
    if args.sdk_revision != '0b5c1f30ca6333b7ec5af70d26511da9ef8d39af':
        parser.error('Unexpected SDK revision')
    manifest = json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text())
    headers = []
    with tempfile.TemporaryDirectory(prefix='image-uapi-') as temporary:
        temporary = Path(temporary)
        installed = temporary/'include/linux'; installed.mkdir(parents=True)
        for record in manifest['kernelHeaders']:
            path = args.uapi/'linux'/record['name']
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            assert digest == record['sha256'], 'SDK UAPI differs from Rust pinned header: ' + record['name']
            text = path.read_text()
            if record['name'] in ('videodev2.h', 'media.h'):
                text = text.replace('#include <linux/compiler.h>', '').replace('__user', '')
            (installed/record['name']).write_text(text)
            headers.append({'name': record['name'], 'sha256': digest})
        source = ROOT/'reverse-engineering/rkaiq/scripts/check-layout.c'
        probe = temporary/'probe.c'
        probe.write_text(source.read_text() + '''
_Static_assert(sizeof(struct isp32_bay3d_cfg)==253,"BAY3D kernel size");
_Static_assert(offsetof(struct isp32_isp_params_cfg,others.bay3d_cfg)==0x2869,"BAY3D kernel offset");
_Static_assert(sizeof(struct isp32_ynr_cfg)==162,"YNR kernel size");
_Static_assert(offsetof(struct isp32_isp_params_cfg,others.ynr_cfg)==0x2966,"YNR kernel offset");
_Static_assert(sizeof(struct isp32_sharp_cfg)==175,"SHARP kernel size");
_Static_assert(offsetof(struct isp32_isp_params_cfg,others.sharp_cfg)==0x2a43,"SHARP kernel offset");
const unsigned int image_extra_layout[]={offsetof(struct isp32_isp_params_cfg,others.bay3d_cfg),sizeof(struct isp32_bay3d_cfg),offsetof(struct isp32_isp_params_cfg,others.ynr_cfg),sizeof(struct isp32_ynr_cfg),offsetof(struct isp32_isp_params_cfg,others.sharp_cfg),sizeof(struct isp32_sharp_cfg)};
''')
        obj = temporary/'image-layout.o'
        subprocess.run(['mise','exec','zig@0.15.2','--','zig','cc','-target','arm-linux-musleabihf',
                        '-I',str(temporary/'include'),'-c',str(probe),'-o',str(obj)], check=True)
        with obj.open('rb') as file:
            elf = ELFFile(file)
            assert elf['e_machine'] == 'EM_ARM'
            def vector(name, count):
                symbol = elf.get_section_by_name('.symtab').get_symbol_by_name(name)[0]
                section = elf.get_section(symbol['st_shndx'])
                offset = symbol['st_value']-section['sh_addr']
                return struct.unpack_from('<'+'I'*count, section.data(), offset)
            parameters = vector('recovered_layout', 3)
            statistics = vector('statistics_layout', 14)
            extra = vector('image_extra_layout', 6)
        assert parameters == (11145,4645,32)
        assert statistics == (13036,13024,13028,13032,2736,4096,11008,12816,12944,12960,225,4,8,4)
        for index, module in enumerate(['bay3d','ynr','sharp']):
            rust = (ROOT/'firmware/rkaiq-rs/src'/('isp_'+module+'.rs')).read_text()
            offset = int(re.search(r'pub const OFFSET: usize = (0x[0-9a-f]+|\d+)', rust)[1], 0)
            size = int(re.search(r'pub const BYTES: usize = (\d+)', rust)[1])
            assert extra[index*2:index*2+2] == (offset, size), module
    config_text = args.kernel_config.read_text()
    config = dict(re.findall(r'^(CONFIG_\w+)=(\S+)$', config_text, re.M))
    required = {'CONFIG_CPU_RV1106':'y', 'CONFIG_VIDEO_ROCKCHIP_ISP_VERSION_V32':'y', 'CONFIG_COMPAT_32BIT_TIME':'y',
                'CONFIG_MEDIA_CONTROLLER':'y', 'CONFIG_VIDEO_V4L2_SUBDEV_API':'y',
                'CONFIG_VIDEO_ROCKCHIP_CIF':'m', 'CONFIG_VIDEO_ROCKCHIP_ISP':'m',
                'CONFIG_VIDEO_SC3336':'m', 'CONFIG_PHY_ROCKCHIP_CSI2_DPHY':'m', 'CONFIG_ROCKCHIP_DVBM':'m'}
    assert all(config.get(key) == value for key, value in required.items()), 'Unexpected camera kernel configuration'
    dtb = fdt_properties(args.dtb.read_bytes())
    root = dtb['/']
    usb_mode = strings(dtb['/usbdrd/usb@ffb00000']['dr_mode'])[0]
    assert usb_mode == ('peripheral' if args.image_variant == 'dev' else 'host'), 'Unexpected USB role for image variant'
    media = []
    for path, properties in dtb.items():
        compatible = strings(properties.get('compatible', b''))
        if not any(any(word in name for word in ['sc3336','rkisp','rkcif','csi2-dphy']) for name in compatible):
            continue
        enabled = True
        parts = path.strip('/').split('/')
        for index in range(len(parts)+1):
            ancestor = '/' + '/'.join(parts[:index])
            status = strings(dtb.get(ancestor, {}).get('status', b'okay\0'))
            enabled &= status[0] in ('okay','ok')
        media.append({'path':path,'compatible':compatible,'enabled':enabled})
    assert any('smartsens,sc3336' in record['compatible'] and record['enabled'] for record in media), 'SC3336 is not enabled in compiled DTB'
    kernel_release = (args.sdk_source/'sysdrv/source/objs_kernel/include/generated/utsrelease.h').read_text()
    kernel_version = re.search(r'#define UTS_RELEASE "([^"]+)"', kernel_release)[1]
    assert kernel_version == '5.10.160', 'Unexpected generated kernel release'
    kernel = args.sdk_source/'sysdrv/source/kernel'
    driver_files = ['drivers/media/platform/rockchip/isp/'+name for name in
                    ['hw.c','isp_stats_v32.c','isp_params_v32.c','rkisp.c','rkisp.h','dev.c','Makefile']]
    driver_files += ['drivers/media/platform/rockchip/cif/dev.c', 'drivers/media/platform/rockchip/cif/Makefile',
                     'drivers/media/i2c/Makefile', 'drivers/phy/rockchip/Makefile']
    drivers = {name:(kernel/name).read_text() for name in driver_files}
    hw = drivers['drivers/media/platform/rockchip/isp/hw.c']
    match = re.search(r'static const struct isp_match_data rv1106_isp_match_data = \{(.*?)\};', hw, re.S)[1]
    assert re.search(r'\.isp_ver\s*=\s*ISP_V32\s*,', match)
    assert re.search(r'\.unite\s*=\s*false\s*,', match)
    assert re.search(r'\.compatible\s*=\s*"rockchip,rv1106-rkisp"\s*,\s*\.data\s*=\s*&rv1106_isp_match_data', hw)
    assert any('rockchip,rv1106-rkisp' in item['compatible'] and item['enabled'] for item in media)
    stats = drivers['drivers/media/platform/rockchip/isp/isp_stats_v32.c']
    assert re.search(r'if \(stats_vdev->dev->isp_ver == ISP_V32\)\s*sizes\[0\] = ALIGN\(sizeof\(struct rkisp32_isp_stat_buffer\), 16\)', stats)
    params = drivers['drivers/media/platform/rockchip/isp/isp_params_v32.c']
    assert 'sizes[0] = sizeof(struct isp32_isp_params_cfg) * mult;' in params
    rkisp = drivers['drivers/media/platform/rockchip/isp/rkisp.c']
    assert 'isp_dev->unite_div = ISP_UNITE_DIV1;' in rkisp
    assert 'else if (crop->width * crop->height > size)' in rkisp
    limits = drivers['drivers/media/platform/rockchip/isp/rkisp.h']
    maximum = tuple(int(re.search(r'#define CIF_ISP_INPUT_'+axis+r'_MAX_V32\s+(\d+)', limits)[1]) for axis in ['W','H'])
    assert 2304*1296 <= maximum[0]*maximum[1]
    module_rules = {'video_rkisp':'drivers/media/platform/rockchip/isp/Makefile',
                    'video_rkcif':'drivers/media/platform/rockchip/cif/Makefile',
                    'sc3336':'drivers/media/i2c/Makefile',
                    'phy-rockchip-csi2-dphy-hw':'drivers/phy/rockchip/Makefile',
                    'phy-rockchip-csi2-dphy':'drivers/phy/rockchip/Makefile'}
    assert all(name+'.o' in drivers[path] for name,path in module_rules.items())
    for name in ['isp','cif']:
        assert 'module_param_call(clr_unready_dev,' in drivers['drivers/media/platform/rockchip/'+name+'/dev.c']
    report = {'kind':'image-sdk-kernel-camera-abi-validation','passed':True,'sdkRevision':args.sdk_revision,
              'kernelVersion':kernel_version,'imageVariant':args.image_variant,'compiledUsbMode':usb_mode,'actualSdkHeaderHashes':headers,
              'armCompiledKernelAssertions':len(re.findall(r'_Static_assert\(', source.read_text()))+6,
              'parameterBytes':parameters[0],'awbGainOffset':parameters[1],'awbGainBytes':parameters[2],
              'statisticsLayout':statistics,'additionalIspBlockLayout':extra,'requiredKernelConfig':required,
              'kernelConfigSha256':hashlib.sha256(args.kernel_config.read_bytes()).hexdigest(),
              'compiledDtbSha256':hashlib.sha256(args.dtb.read_bytes()).hexdigest(),
              'compiledDtbModel':strings(root['model'])[0],'compiledDtbCompatible':strings(root['compatible']),
              'compiledDtbCameraNodes':media,
              'driverRoute':{'compatible':'rockchip,rv1106-rkisp','ispVersion':'ISP_V32','litePathSelected':False,
                             'hardwareUnite':False,'sensorSize':[2304,1296],'maximumSingleIspSize':maximum,
                             'expectedParameterBytes':11145,'expectedAlignedStatisticsBufferBytes':13040,
                             'initialUniteMultiplier':1,'clrUnreadyDevParameterPresentIn':['video_rkcif','video_rkisp'],
                             'moduleBuildRules':module_rules},
              'driverSourceSha256':{name:hashlib.sha256((kernel/name).read_bytes()).hexdigest() for name in driver_files},
              'probeSourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),
              'limits':['Compile-time SDK UAPI and compiled DTB/config checks, not a boot of this image.',
                        'Fixed video/subdev/media entity numbers are assigned at registration time and still need a booted-image inventory/capture check.',
                        'Driver module binaries/install paths must be checked in the finished image; source/config checks alone do not prove module installation.']}
    args.report.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
