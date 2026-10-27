#!/usr/bin/env python3
"""Verify pinned kernel parameter ABI with an ARM-targeting C compiler."""
from pathlib import Path
import hashlib,json,subprocess,struct,shutil
from elftools.elf.elffile import ELFFile
ROOT=Path(__file__).resolve().parents[3]
cache=ROOT/'.tools/reverse-engineering/kernel-uapi'
manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text())
for item in manifest['kernelHeaders']:
    assert hashlib.sha256((cache/'linux'/item['name']).read_bytes()).hexdigest()==item['sha256']
# Kernel headers_install removes kernel-only compiler includes and __user
# annotations. Keep original pinned downloads intact and sanitize a build copy.
installed=cache/'installed';(installed/'linux').mkdir(parents=True,exist_ok=True)
for item in manifest['kernelHeaders']:
    source=cache/'linux'/item['name'];target=installed/'linux'/item['name']
    if item['name'] in ('videodev2.h','media.h'):
        target.write_text(source.read_text().replace('#include <linux/compiler.h>','').replace('__user',''))
    else:shutil.copyfile(source,target)
obj=cache/'layout-arm.o'
subprocess.run(['mise','exec','zig@0.15.2','--','zig','cc','-target','arm-linux-musleabihf','-I',str(installed),'-c',str(Path(__file__).with_suffix('.c')),'-o',str(obj)],check=True)
with obj.open('rb') as source:
    elf=ELFFile(source)
    assert elf['e_machine']=='EM_ARM'
    symbol=elf.get_section_by_name('.symtab').get_symbol_by_name('recovered_layout')[0]
    section=elf.get_section(symbol['st_shndx'])
    offset=symbol['st_value']-section['sh_addr']
    layout=struct.unpack('<3I',section.data()[offset:offset+12])
assert layout==(11145,4645,32),layout
print('PASS: ARM kernel parameter bytes=%d, AWB offset=%d, AWB bytes=%d'%layout)

with obj.open('rb') as source:
    elf=ELFFile(source);symbol=elf.get_section_by_name('.symtab').get_symbol_by_name('statistics_layout')[0]
    section=elf.get_section(symbol['st_shndx']);offset=symbol['st_value']-section['sh_addr']
    statistics=struct.unpack('<14I',section.data()[offset:offset+56])
assert statistics==(13036,13024,13028,13032,2736,4096,11008,12816,12944,12960,225,4,8,4),statistics
print('PASS: full ISP32 statistics payload=13036, measurements=0x32e0; AE/AWB offsets and counts verified')

# Compile the verbatim SDK output-record declaration independently of Rust.
import re
item=next(x for x in manifest['headers'] if x['name']=='rk_aiq_types_ae_hw.h')
header=ROOT/'.tools/reverse-engineering/headers'/item['name']
assert hashlib.sha256(header.read_bytes()).hexdigest()==item['sha256']
text=header.read_text()
def declaration(pattern):
    match=re.search(pattern,text,re.S);assert match,pattern;return match.group(0)
record=declaration(r'typedef struct rawaebig_stat \{.*?\} rawaebig_stat_t;')
macros='\n'.join(declaration(r'#define '+name+r'[^\n]*') for name in ['RAWAEBIG_WIN_NUM','RAWAEBIG_SUBWIN_NUM'])
source=cache/'ae-sdk-layout.c'
source.write_text('#include <stdint.h>\n#include <stddef.h>\n'+macros+'\n'+record+'''
_Static_assert(sizeof(rawaebig_stat_t)==1928,"big AE record size");
_Static_assert(offsetof(rawaebig_stat_t,wndx_channelr)==1800,"preserved window channel offset");
_Static_assert(offsetof(rawaebig_stat_t,wndx_sumr)==1832,"red sums offset");
_Static_assert(offsetof(rawaebig_stat_t,wndx_sumg)==1864,"green sums offset");
_Static_assert(offsetof(rawaebig_stat_t,wndx_sumb)==1896,"blue sums offset");
''')
subprocess.run(['mise','exec','zig@0.15.2','--','zig','cc','-target','arm-linux-musleabihf','-c',str(source),'-o',str(cache/'ae-sdk-layout.o')],check=True)
print('PASS: pinned SDK big AE record=1928 bytes; preserved channels and RGB sum offsets verified')

# Extract the exact SDK input declaration, without importing unrelated algorithm
# headers or substituting a hand-written equivalent struct.
item=next(x for x in manifest['headers'] if x['name']=='rk_aiq_types_ablc_algo_int_v32.h')
header=ROOT/'.tools/reverse-engineering/headers'/item['name']
assert hashlib.sha256(header.read_bytes()).hexdigest()==item['sha256']
match=re.search(r'typedef struct AblcProc_V32_s \{.*?\} AblcProc_V32_t;',header.read_text(),re.S);assert match
source=cache/'blc-sdk-layout.c'
source.write_text('#include <stdbool.h>\n#include <stddef.h>\n'+match.group(0)+'''
_Static_assert(sizeof(AblcProc_V32_t)==32,"black-level SDK input size");
_Static_assert(offsetof(AblcProc_V32_t,enable)==0,"main enable");
_Static_assert(offsetof(AblcProc_V32_t,blc_r)==2,"fixed channels");
_Static_assert(offsetof(AblcProc_V32_t,blc1_enable)==10,"stage1 enable");
_Static_assert(offsetof(AblcProc_V32_t,blc1_r)==12,"stage1 channels");
_Static_assert(offsetof(AblcProc_V32_t,blc_ob_enable)==20,"optical-black enable");
_Static_assert(offsetof(AblcProc_V32_t,isp_ob_offset)==22,"optical-black offset");
_Static_assert(offsetof(AblcProc_V32_t,isp_ob_predgain)==24,"optical-black predgain");
_Static_assert(offsetof(AblcProc_V32_t,isp_ob_max)==28,"optical-black maximum");
''')
subprocess.run(['mise','exec','zig@0.15.2','--','zig','cc','-target','arm-linux-musleabihf','-c',str(source),'-o',str(cache/'blc-sdk-layout.o')],check=True)
print('PASS: pinned SDK black-level input=32 bytes; full kernel BLS block=44 bytes at 0x7ae')

# Both SDK demosaic declarations are compiled verbatim, independently of the
# Rust value struct and its explicit byte decoding/serialization.
def sdk_record(name,pattern):
    item=next(x for x in manifest['headers'] if x['name']==name)
    path=ROOT/'.tools/reverse-engineering/headers'/item['name']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']
    match=re.search(pattern,path.read_text(),re.S);assert match
    return match.group(0)
selected=sdk_record('rk_aiq_types_adebayer_algo_int.h',r'typedef struct AdebayerSeletedParamV2_s \{.*?\} AdebayerSeletedParamV2_t;')
hardware=sdk_record('rk_aiq_types_adebayer_hw.h',r'typedef struct AdebayerHwConfigV2_s \{.*?\} AdebayerHwConfigV2_t;')
source=cache/'demosaic-sdk-layout.c'
assertions=['_Static_assert(sizeof(AdebayerSeletedParamV2_t)==132,"selected size");','_Static_assert(sizeof(AdebayerHwConfigV2_t)==112,"hardware size");']
for field,offset in [('debayer_en',0),('lowfreq_filter1',4),('highfreq_filter2',20),('c_alpha_gaus_coe',36),('c_guid_gaus_coe',48),('c_ce_gaus_coe',60),('debayer_clip_en',72),('debayer_gain_offset',74),('debayer_max_ratio',76),('debayer_hf_offset',78),('debayer_thed0',80),('debayer_thed1',81),('debayer_dist_scale',82),('debayer_select_thed',83),('debayer_gfilter_en',84),('debayer_gfilter_offset',86),('debayer_cfilter_en',88),('debayer_loggd_offset',90),('debayer_cfilter_str',92),('debayer_wet_clip',96),('debayer_wet_ghost',100),('debayer_wgtslope',104),('debayer_bf_sgm',108),('debayer_bf_clip',112),('debayer_bf_curwgt',113),('debayer_loghf_offset',114),('debayer_alpha_offset',116),('debayer_alpha_scale',120),('debayer_edge_offset',124),('debayer_edge_scale',128)]:
    assertions.append(f'_Static_assert(offsetof(AdebayerSeletedParamV2_t,{field})=={offset},"{field}");')
for field,offset in [('updatecfg',0),('enable',1),('filter_g_en',2),('filter_c_en',3),('clip_en',4),('dist_scale',5),('thed0',6),('thed1',7),('select_thed',8),('max_ratio',9),('filter1_coe',12),('filter2_coe',28),('guid_gaus_coe',44),('ce_gaus_coe',56),('alpha_gaus_coe',68),('ce_sgm',80),('exp_shift',81),('wet_clip',82),('wet_ghost',83),('bf_clip',84),('bf_curwgt',85),('bf_sgm',86),('hf_offset',88),('gain_offset',90),('offset',92),('loghf_offset',94),('loggd_offset',96),('wgtslope',98),('alpha_offset',100),('edge_offset',102),('edge_scale',104),('alpha_scale',108)]:
    assertions.append(f'_Static_assert(offsetof(AdebayerHwConfigV2_t,{field})=={offset},"{field}");')
source.write_text('#include <stdbool.h>\n#include <stddef.h>\n'+selected+'\n'+hardware+'\n'+'\n'.join(assertions)+'\n')
subprocess.run(['mise','exec','zig@0.15.2','--','zig','cc','-target','arm-linux-musleabihf','-c',str(source),'-o',str(cache/'demosaic-sdk-layout.o')],check=True)
print('PASS: SDK demosaic selected=132/hardware=112 bytes; full kernel block=57 bytes at 0x1282')

# Verify the complete public calibration table used by native automatic Process.
item=next(x for x in manifest['headers'] if x['name']=='debayer_head.h')
header=ROOT/'.tools/reverse-engineering/headers'/item['name']
assert hashlib.sha256(header.read_bytes()).hexdigest()==item['sha256']
text=header.read_text();records=[]
for name in ['GInterp','GDirectWgt','GFilter','CFilter','Tuning']:
    match=re.search(r'typedef struct CalibDbV2_Debayer_'+name+r'_s \{.*?\} CalibDbV2_Debayer_'+name+r'_t;',text,re.S);assert match
    records.append(match.group(0))
source=cache/'demosaic-calibration-layout.c'
assertions=[]
for name,size in [('GInterp',108),('GDirectWgt',132),('GFilter',92),('CFilter',564),('Tuning',968)]:
    assertions.append(f'_Static_assert(sizeof(CalibDbV2_Debayer_{name}_t)=={size},"{name} size");')
for name,fields in [
 ('Tuning',[('debayer_en',0),('lowfreq_filter1',4),('highfreq_filter2',20),('c_alpha_gaus_coe',36),('c_guid_gaus_coe',48),('c_ce_gaus_coe',60),('g_interp',72),('g_drctwgt',180),('g_filter',312),('c_filter',404)]),
 ('GInterp',[('iso',0),('debayer_clip_en',52),('debayer_gain_offset',66),('debayer_max_ratio',92)]),
 ('GDirectWgt',[('iso',0),('debayer_hf_offset',52),('debayer_thed0',78),('debayer_thed1',91),('debayer_dist_scale',104),('debayer_select_thed',117)]),
 ('GFilter',[('iso',0),('debayer_gfilter_en',52),('debayer_gfilter_offset',66)]),
 ('CFilter',[('iso',0),('debayer_cfilter_en',52),('debayer_loggd_offset',66),('debayer_cfilter_str',92),('debayer_wet_clip',144),('debayer_wet_ghost',196),('debayer_wgtslope',248),('debayer_bf_sgm',300),('debayer_bf_clip',352),('debayer_bf_curwgt',365),('debayer_loghf_offset',378),('debayer_alpha_offset',404),('debayer_alpha_scale',432),('debayer_edge_offset',484),('debayer_edge_scale',512)])]:
    for field,offset in fields:assertions.append(f'_Static_assert(offsetof(CalibDbV2_Debayer_{name}_t,{field})=={offset},"{name}.{field}");')
source.write_text('#include <stdbool.h>\n#include <stddef.h>\n#define DEBAYER_ISO_STEP_MAX 13\n'+'\n'.join(records+assertions)+'\n')
subprocess.run(['mise','exec','zig@0.15.2','--','zig','cc','-target','arm-linux-musleabihf','-c',str(source),'-o',str(cache/'demosaic-calibration-layout.o')],check=True)
print('PASS: SDK demosaic calibration=968 bytes; all four 13-step ISO table layouts verified')

# Compile selected-measurement inputs using the SDK's actual ISP_HW_V32 shape
# and its original packed leaf-record rules, not the V20/V30 four-input shape.
item=next(x for x in manifest['headers'] if x['name']=='rk_aiq_types_ae_hw.h')
header=ROOT/'.tools/reverse-engineering/headers'/item['name']
assert hashlib.sha256(header.read_bytes()).hexdigest()==item['sha256']
text=header.read_text();leaf=[];outer=[]
for name in ['window','rawaebig_meas_cfg','rawaelite_meas_cfg','rawhistbig_cfg','rawhistlite_cfg']:
    match=re.search(r'typedef struct '+name+r' \{.*?\} '+name+r'_t;',text,re.S);assert match;leaf.append(match.group(0))
for name in ['ae','hist']:
    match=re.search(r'typedef struct rk_aiq_'+name+r'_meas_params_s \{.*?\} rk_aiq_'+name+r'_meas_params_t;',text,re.S);assert match;outer.append(match.group(0))
source=cache/'ae-measurement-sdk-layout.c'
assertions=['_Static_assert(sizeof(rk_aiq_ae_meas_params_t)==104,"SDK AE result");','_Static_assert(sizeof(rk_aiq_hist_meas_params_t)==529,"SDK histogram result");']
for name,size,fields in [
 ('window',8,[('h_offs',0),('v_offs',2),('h_size',4),('v_size',6)]),
 ('rawaelite_meas_cfg',10,[('rawae_sel',0),('wnd_num',1),('win',2)]),
 ('rawaebig_meas_cfg',46,[('rawae_sel',0),('wnd_num',1),('subwin_en',2),('win',6),('subwin',14)]),
 ('rawhistlite_cfg',41,[('data_sel',0),('waterline',1),('mode',2),('stepsize',3),('off',4),('bcc',5),('gcc',6),('rcc',7),('win',8),('weight',16)]),
 ('rawhistbig_cfg',242,[('wnd_num',0),('data_sel',1),('waterline',2),('mode',3),('stepsize',4),('off',5),('bcc',6),('gcc',7),('rcc',8),('win',9),('weight',17)]),
 ('rk_aiq_ae_meas_params',104,[('ae_meas_en',0),('ae_meas_update',1),('rawae0',2),('rawae1',12),('rawae3',58)]),
 ('rk_aiq_hist_meas_params',529,[('hist_meas_en',0),('hist_meas_update',1),('ae_swap',2),('ae_sel',3),('rawhist0',4),('rawhist1',45),('rawhist3',287)])]:
    assertions.append(f'_Static_assert(sizeof({name}_t)=={size},"{name} size");')
    for field,offset in fields:assertions.append(f'_Static_assert(offsetof({name}_t,{field})=={offset},"{name}.{field}");')
source.write_text('#include <stdint.h>\n#include <stdbool.h>\n#include <stddef.h>\n#define ISP_HW_V32 1\n#define RAWAEBIG_SUBWIN_NUM 4\n#define RAWHISTBIG_WIN_NUM 225\n#define RAWHISTLITE_WIN_NUM 25\n#pragma pack(push,1)\n'+'\n'.join(leaf)+'\n#pragma pack(pop)\n'+'\n'.join(outer+assertions)+'\n')
subprocess.run(['mise','exec','zig@0.15.2','--','zig','cc','-target','arm-linux-musleabihf','-c',str(source),'-o',str(cache/'ae-measurement-sdk-layout.o')],check=True)
print('PASS: SDK AE=104/histogram=529 bytes; packed kernel blocks, routing offsets and masks verified')

# AWB v32 public declarations, compiled verbatim with only needed constants.
awb_declarations=[]
for header,kind,tag,alias in [
 ('v2xx','enum','rk_aiq_down_scale_mode_e','rk_aiq_down_scale_mode_t'),
 ('v2xx','enum','rk_aiq_awb_exc_range_domain_e','rk_aiq_awb_exc_range_domain_t'),
 ('v201','enum','rk_aiq_awb_xy_type_v201_e','rk_aiq_awb_xy_type_v201_t'),
 ('v201','enum','rk_aiq_awb_blk_stat_mode_v201_e','rk_aiq_awb_blk_stat_mode_v201_t'),
 ('v201','enum','RK_AIQ_AWB_BLK_STAT_REALWP_ILL_S','rk_aiq_awb_blk_stat_realwp_ill_e'),
 ('v2xx','struct','rk_aiq_rgb2xy_para_s','rk_aiq_rgb2xy_para_t'),
 ('v2xx','struct','rk_aiq_awb_xy_range_para_s','rk_aiq_awb_xy_range_para_t'),
 ('v2xx','struct','rk_aiq_awb_uv_range_para_s','rk_aiq_awb_uv_range_para_t'),
 ('v2xx','struct','rk_aiq_awb_rt3dyuv_range_para_s','rk_aiq_awb_rt3dyuv_range_para_t'),
 ('v32','struct','rk_aiq_awb_exc_range_v32_s','rk_aiq_awb_exc_range_v32_t'),
 ('v32','struct','rk_aiq_awb_blc_s','rk_aiq_awb_blc_t'),
 ('v32','struct','rk_aiq_awb_stat_cfg_v32_s','rk_aiq_awb_stat_cfg_v32_t')]:
    pattern=r'typedef '+kind+' '+tag+r' \{.*?\} '+alias+';'
    record=sdk_record('rk_aiq_types_awb_stat_'+header+'.h',pattern)
    if tag=='rk_aiq_down_scale_mode_e':
        # The second declaration is the full-V32 branch, rather than V32LT.
        record=re.findall(pattern,(ROOT/'.tools/reverse-engineering/headers/rk_aiq_types_awb_stat_v2xx.h').read_text(),re.S)[-1]
    awb_declarations.append(record)
assertions=['_Static_assert(sizeof(rk_aiq_awb_stat_cfg_v32_t)==1204,"AWB SDK size");', '_Static_assert(sizeof(rk_aiq_awb_exc_range_v32_t)==28,"exclusion stride");']
for field,offset in [('awbEnable',0),('inputShiftEnable',8),('blc',12),('uvDetectionEnable',32),('threeDyuvIllu',38),('wpDiffWeiEnable',46),('blkWeightEnable',48),('dsMode',52),('blkMeasureMode',56),('frameChoose',62),('windowSet',64),('maxR',74),('pre_wbgain_inv_r',90),('overexposure_value',96),('icrgb2RYuv_matrix',100),('ic3Dyuv2Range_param',124),('uvRange_param',252),('rgb2xy_param',396),('xyRange_param',420),('multiwindow',612),('excludeWpRange',644),('wpDiffwei_y',840),('wpDiffwei_w',849),('xyRangeTypeForWpHist',860),('blkWeight',864),('xyRangeTypeForBlkStatistics',1092),('illIdxForBlkStatistics',1096),('blkStatisticsWithLumaWeightEn',1100),('timeSign',1124),('preWbgainSw',1188)]:
    assertions.append(f'_Static_assert(offsetof(rk_aiq_awb_stat_cfg_v32_t,{field})=={offset},"AWB {field}");')
macros=[]
for version,names in [
 ('v2xx',['RK_AIQ_AWB_YUV_LS_PARA_NUM','RK_AIQ_AWB_EXCLUDE_WP_RANGE_NUM','RK_AIQ_AWB_GRID_NUM_VERHOR','RK_AIQ_AWB_GRID_NUM_TOTAL']),
 ('v201',['RK_AIQ_AWB_MULTIWINDOW_NUM_V201','RK_AIQ_AWB_WP_HIST_BIN_NUM','RK_AIQ_AWBWP_WEIGHT_CURVE_DOT_NUM']),
 ('v32',['RK_AIQ_AWB_MAX_WHITEREGIONS_NUM_V32'])]:
    for name in names:macros.append(sdk_record('rk_aiq_types_awb_stat_'+version+'.h',r'#define '+name+r'[^\n]*'))
macros='\n'.join(macros)
source=cache/'awb-measurement-sdk-layout.c';source.write_text('#include <stdint.h>\n#include <stdbool.h>\n#include <stddef.h>\n'+macros+'\n'+'\n'.join(awb_declarations+assertions)+'\n')
subprocess.run(['mise','exec','zig@0.15.2','--','zig','cc','-target','arm-linux-musleabihf','-c',str(source),'-o',str(cache/'awb-measurement-sdk-layout.o')],check=True)
print('PASS: AWB v32 SDK=1204 bytes, seven exclusion records and all used input groups verified')

# The gain-statistics aggregate is passed by value across r0-r3 and the stack.
weighted=sdk_record('rk_aiq_types_awb_stat_v201.h',r'typedef struct rk_aiq_awb_stat_wp_res_v201_s \{.*?\} rk_aiq_awb_stat_wp_res_v201_t;')
gain=sdk_record('rk_aiq_types_awb_algo.h',r'typedef struct rk_aiq_wb_gain_v32_s \{.*?\} rk_aiq_wb_gain_v32_t;')
position=sdk_record('rk_aiq_types_awb_algo.h',r'typedef enum rk_aiq_wb_gapin_aplly_pos_s\{.*?\}rk_aiq_wb_gapin_aplly_pos_e;')
source=cache/'awb-gain-sdk-layout.c'
source.write_text('#include <stddef.h>\n'+weighted+'\n'+position+'\n'+gain+'''
_Static_assert(sizeof(rk_aiq_awb_stat_wp_res_v201_t)==24,"weighted AWB record size");
_Static_assert(_Alignof(rk_aiq_awb_stat_wp_res_v201_t)==8,"weighted AWB alignment");
_Static_assert(offsetof(rk_aiq_awb_stat_wp_res_v201_t,WpNo)==0,"weighted count");
_Static_assert(offsetof(rk_aiq_awb_stat_wp_res_v201_t,RgainValue)==8,"red gain total");
_Static_assert(offsetof(rk_aiq_awb_stat_wp_res_v201_t,BgainValue)==16,"blue gain total");
_Static_assert(sizeof(rk_aiq_wb_gain_v32_t)==20,"AWB gain result size");
_Static_assert(offsetof(rk_aiq_wb_gain_v32_t,applyPosition)==16,"gain position");
''')
subprocess.run(['mise','exec','zig@0.15.2','--','zig','cc','-target','arm-linux-musleabihf','-c',str(source),'-o',str(cache/'awb-gain-sdk-layout.o')],check=True)
print('PASS: SDK weighted AWB statistics=24 bytes/alignment 8, gain result=20 bytes')

# Entire SDK AWB frame consumed by PrepareMeasureResult, including effect
# metadata and the final signed global RGB sum. Declarations remain verbatim.
records=[]
for version,tag,alias in [
 ('v201','rk_aiq_awb_stat_wp_res_v201_s','rk_aiq_awb_stat_wp_res_v201_t'),
 ('v201','rk_aiq_awb_stat_blk_res_v201_s','rk_aiq_awb_stat_blk_res_v201_t'),
 ('v201','rk_aiq_awb_stat_wp_res_light_v201_s','rk_aiq_awb_stat_wp_res_light_v201_t'),
 ('v32','rk_aiq_awb_stat_cfg_effect_v32_s','rk_aiq_awb_stat_cfg_effect_v32_t'),
 ('v32','rk_aiq_awb_stat_res_v32_s','rk_aiq_awb_stat_res_v32_t')]:
    records.append(sdk_record('rk_aiq_types_awb_stat_'+version+'.h',r'typedef struct '+tag+r' \{.*?\} '+alias+';'))
source=cache/'awb-preparation-sdk-layout.c'
assertions=['_Static_assert(sizeof(rk_aiq_awb_stat_res_v32_t)==0x1e00,"full AWB frame");','_Static_assert(sizeof(rk_aiq_awb_stat_cfg_effect_v32_t)==108,"AWB effect");']
for field,offset in [('light',0),('WpNo2',0xc0),('blockResult',0xd0),('excWpRangeResult',0x1cf0),('WpNoHist',0x1d50),('awb_cfg_effect_v32',0x1d70),('dbginfo_fd',0x1ddc),('sumBlkRGB',0x1de0)]:assertions.append(f'_Static_assert(offsetof(rk_aiq_awb_stat_res_v32_t,{field})=={offset},"AWB frame {field}");')
for field,offset in [('blkMeasureMode',0),('lightNum',4),('groupIllIndxCurrent',8),('IllIndxSetCurrent',12),('timeSign',28),('preWbgainSw',92)]:assertions.append(f'_Static_assert(offsetof(rk_aiq_awb_stat_cfg_effect_v32_t,{field})=={offset},"AWB effect {field}");')
source.write_text('#include <stdint.h>\n#include <stdbool.h>\n#include <stddef.h>\n'+macros+'\n'+sdk_record('rk_aiq_types_awb_stat_v201.h',r'#define RK_AIQ_AWB_STAT_WP_RANGE_NUM_V201[^\n]*')+'\n'+'\n'.join(awb_declarations+records+assertions)+'\n')
subprocess.run(['mise','exec','zig@0.15.2','--','zig','cc','-target','arm-linux-musleabihf','-c',str(source),'-o',str(cache/'awb-preparation-sdk-layout.o')],check=True)
print('PASS: complete SDK AWB frame=7680 bytes; effect=108, all prepared input offsets verified')

# Independently compile public DPCC IQ/result declarations under ARM32 ABI.
def dpcc_header(name):
    item=next(x for x in manifest['headers'] if x['name']==name)
    path=ROOT/'.tools/reverse-engineering/headers'/name
    assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']
    return path.read_text()
iq=dpcc_header('adpcc_head.h').replace('#include "rk_aiq_comm.h"','')
ext=dpcc_header('rk_aiq_types_adpcc_ext.h')
def dpcc_record(name,text):
    match=re.search(r'typedef struct '+name+r'\s*\{.*?\}\s*\w+;',text,re.S)
    assert match,name
    return match.group(0)
records=[dpcc_record(name,ext) for name in ['Adpcc_basic_params_select_s','Adpcc_basic_cfg_params_s','Adpcc_bpt_params_s','dpcc_pdaf_point_s','Adpcc_pdaf_params_s']]
records.append(dpcc_record('AdpccProcResult_s',dpcc_header('rk_aiq_types_adpcc_algo_int.h')))
source=cache/'dpcc-sdk-layout.c'
source.write_text('#include <stdbool.h>\n#include <stdint.h>\n#include <stddef.h>\n#define RKAIQ_BEGIN_DECLARE\n#define RKAIQ_END_DECLARE\n#define DPCC_PDAF_POINT_NUM 16\n'+iq+'\n'+'\n'.join(records)+'''
_Static_assert(offsetof(CalibDbV2_Dpcc_t,DpccTuningPara.Expert_Mode)==40,"DPCC expert offset");
_Static_assert(offsetof(CalibDbV2_Dpcc_t,DpccTuningPara.Expert_Mode.SetEnable.ISO)==48,"DPCC ISO offset");
_Static_assert(offsetof(CalibDbV2_Dpcc_t,DpccTuningPara.Expert_Mode.set1)==308,"DPCC set1 offset");
_Static_assert(sizeof(CalibDb_Dpcc_Expert_Mode_V20_t)==1204,"DPCC IQ expert size");
_Static_assert(sizeof(Adpcc_basic_params_select_t)==108,"DPCC ISO row");
_Static_assert(sizeof(Adpcc_basic_cfg_params_t)==103,"DPCC basic fields");
_Static_assert(sizeof(CalibDbV2_Dpcc_t)==0x548,"DPCC complete IQ record");
_Static_assert(sizeof(Adpcc_bpt_params_t)==24,"DPCC BPT record");
_Static_assert(sizeof(Adpcc_pdaf_params_t)==62,"DPCC PDAF record");
_Static_assert(sizeof(AdpccProcResult_t)==192,"DPCC complete result");
_Static_assert(offsetof(AdpccProcResult_t,stBpt)==104,"DPCC BPT offset");
_Static_assert(offsetof(AdpccProcResult_t,stPdaf)==128,"DPCC PDAF offset");
''')
subprocess.run(['mise','exec','zig@0.15.2','--','zig','cc','-target','arm-linux-musleabihf','-c',str(source),'-o',str(cache/'dpcc-sdk-layout.o')],check=True)
print('PASS: SDK DPCC expert=1204, row=108, basic=103, result=192 bytes; IQ/BPT/PDAF offsets verified')

# Complete CCM IQ and hardware result declarations, compiled verbatim for ARM32.
ccm_iq=dpcc_header('ccm_head.h').replace('#include "rk_aiq_comm.h"','')
ccm_hw=dpcc_header('rk_aiq_types_accm_hw.h').replace('#include "rk_aiq_comm.h"','')
ccm_sw=dpcc_record('accm_sw_info_s',dpcc_header('rk_aiq_types_accm_algo_int.h'))
source=cache/'ccm-sdk-layout.c'
source.write_text('#include <stdbool.h>\n#include <stdint.h>\n#include <stddef.h>\n#define RKAIQ_BEGIN_DECLARE\n#define RKAIQ_END_DECLARE\n'+ccm_iq+'\n'+ccm_hw+'\n'+ccm_sw+'''
_Static_assert(sizeof(accm_sw_info_t)==32,"CCM software info size");
_Static_assert(offsetof(accm_sw_info_t,awbIIRDampCoef)==12,"CCM input damping");
_Static_assert(offsetof(accm_sw_info_t,grayMode)==20,"CCM input gray");
_Static_assert(offsetof(accm_sw_info_t,awbConverged)==21,"CCM input AWB convergence");
_Static_assert(offsetof(accm_sw_info_t,prepare_type)==24,"CCM prepare word");
_Static_assert(offsetof(accm_sw_info_t,ccmConverged)==28,"CCM input/output convergence");
_Static_assert(sizeof(rk_aiq_ccm_cfg_v2_t)==156,"CCM result size");
_Static_assert(offsetof(rk_aiq_ccm_cfg_v2_t,matrix)==8,"CCM matrix");
_Static_assert(offsetof(rk_aiq_ccm_cfg_v2_t,offs)==44,"CCM offsets");
_Static_assert(offsetof(rk_aiq_ccm_cfg_v2_t,alp_y)==56,"CCM alpha");
_Static_assert(offsetof(rk_aiq_ccm_cfg_v2_t,right_bit)==128,"CCM right bound");
_Static_assert(offsetof(rk_aiq_ccm_cfg_v2_t,bound_bit)==132,"CCM left bound");
_Static_assert(offsetof(rk_aiq_ccm_cfg_v2_t,rgb2y_para)==136,"CCM luma coeffs");
_Static_assert(offsetof(rk_aiq_ccm_cfg_v2_t,enh_rgb2y_para)==148,"CCM enhancement coeffs");
_Static_assert(offsetof(rk_aiq_ccm_cfg_v2_t,enh_rat_max)==152,"CCM enhancement ratio");
_Static_assert(sizeof(CalibDbV2_Ccm_Para_V32_t)==0x874,"CCM complete IQ");
_Static_assert(offsetof(CalibDbV2_Ccm_Para_V32_t,lumaCCM)==12,"CCM IQ luma");
_Static_assert(offsetof(CalibDbV2_Ccm_Para_V32_t,lumaCCM.asym_enable)==0x18,"CCM IQ asym");
_Static_assert(offsetof(CalibDbV2_Ccm_Para_V32_t,lumaCCM.y_alp_sym)==0x1c,"CCM IQ sym");
_Static_assert(offsetof(CalibDbV2_Ccm_Para_V32_t,lumaCCM.y_alp_asym)==0x3cc,"CCM IQ asym config");
_Static_assert(offsetof(CalibDbV2_Ccm_Para_V32_t,enhCCM.enh_rgb2y_para)==0x844,"CCM IQ enhancement coeffs");
_Static_assert(offsetof(CalibDbV2_Ccm_Para_V32_t,TuningPara)==0x848,"CCM IQ tuning");
_Static_assert(sizeof(CalibDbV2_Ccm_Accm_Cof_Para_t)==56,"CCM illuminant");
_Static_assert(sizeof(CalibDbV2_Ccm_Matrix_Para_t)==60,"CCM profile");
_Static_assert(sizeof(CalibDbV2_Ccm_Gain_Yalp_t)==72,"CCM luma row");
_Static_assert(CCM_ILLUMINATION_MAX==9 && CCM_PROFILES_NUM_MAX==5,"CCM context capacity");
''')
subprocess.run(['mise','exec','zig@0.15.2','--','zig','cc','-target','arm-linux-musleabihf','-c',str(source),'-o',str(cache/'ccm-sdk-layout.o')],check=True)
print('PASS: SDK CCM IQ=2164/result=156, illuminant=56/profile=60/luma row=72 bytes; all used offsets verified')

lsc_hw=dpcc_header('rk_aiq_types_alsc_hw.h').replace('#include "rk_aiq_comm.h"','')
source=cache/'lsc-sdk-layout.c'
source.write_text('#include <stdbool.h>\n#include <stddef.h>\n#define RKAIQ_BEGIN_DECLARE\n#define RKAIQ_END_DECLARE\n'+lsc_hw+'''
_Static_assert(sizeof(rk_aiq_lsc_cfg_t)==2442,"LSC SDK result size");
_Static_assert(offsetof(rk_aiq_lsc_cfg_t,gr_data_tbl)==578,"LSC SDK green red plane");
_Static_assert(offsetof(rk_aiq_lsc_cfg_t,b_data_tbl)==1734,"LSC SDK blue plane");
_Static_assert(offsetof(rk_aiq_lsc_cfg_t,x_grad_tbl)==2312,"LSC SDK gradients");
_Static_assert(offsetof(rk_aiq_lsc_cfg_t,x_size_tbl)==2376,"LSC SDK sizes");
_Static_assert(offsetof(rk_aiq_lsc_cfg_t,lsc_en)==2440,"LSC SDK enable");
_Static_assert(LSC_DATA_TBL_SIZE==289,"LSC SDK plane count differs from kernel");
''')
subprocess.run(['mise','exec','zig@0.15.2','--','zig','cc','-target','arm-linux-musleabihf','-c',str(source),'-o',str(cache/'lsc-sdk-layout.o')],check=True)
print('PASS: SDK LSC result=2442/289 entries per plane; packed kernel=2449/290 entries per plane')

baynr_hw=dpcc_header('rk_aiq_types_abayer2dnr_hw_v23.h').replace('#include "rk_aiq_comm.h"','')
source=cache/'baynr-sdk-layout.c'
source.write_text('#include <stdint.h>\n#include <stddef.h>\n'+baynr_hw+'''
_Static_assert(sizeof(RK_Bayer2dnr_Fix_V23_t)==152,"BAYNR SDK result size");
_Static_assert(offsetof(RK_Bayer2dnr_Fix_V23_t,bayer_en)==4,"BAYNR SDK enable");
_Static_assert(offsetof(RK_Bayer2dnr_Fix_V23_t,dgain)==6,"BAYNR SDK digital gains");
_Static_assert(offsetof(RK_Bayer2dnr_Fix_V23_t,sigma_x)==22,"BAYNR SDK sigma x");
_Static_assert(offsetof(RK_Bayer2dnr_Fix_V23_t,sigma_y)==54,"BAYNR SDK sigma y");
_Static_assert(offsetof(RK_Bayer2dnr_Fix_V23_t,weit_d)==86,"BAYNR SDK spatial weights");
_Static_assert(offsetof(RK_Bayer2dnr_Fix_V23_t,dat_max)==96,"BAYNR SDK data maximum");
_Static_assert(offsetof(RK_Bayer2dnr_Fix_V23_t,gain_x)==104,"BAYNR SDK gain x");
_Static_assert(offsetof(RK_Bayer2dnr_Fix_V23_t,gain_y)==120,"BAYNR SDK gain y");
''')
subprocess.run(['mise','exec','zig@0.15.2','--','zig','cc','-target','arm-linux-musleabihf','-c',str(source),'-o',str(cache/'baynr-sdk-layout.o')],check=True)
print('PASS: BAYNR SDK=152/kernel=150, enable/dgain/sigma/weight/gain offsets and module mask verified')
