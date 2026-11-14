# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner
from collections import namedtuple as _namedtuple
from seedsigner_port.decode_platform import dependency as _dependency, FeatureUnavailable
"""Utilities for working with aezeed mnemonics."""
import hashlib
__all__ = ['DEFAULT_PASSPHRASE', 'DecipheredCipherSeed', 'InvalidMnemonicError', 'InvalidPassphraseError', 'decode_mnemonic', 'mnemonic_to_bytes', 'validate_mnemonic', 'has_valid_checksum']
DEFAULT_PASSPHRASE = 'aezeed'
EncipheredCipherSeedSize = 33
DecipheredCipherSeedSize = 19
SaltSize = 5
CipherTextExpansion = 4
BitsPerWord = 11
CipherSeedVersion = 0

class AezeedError(Exception):
    """Base class for aezeed errors."""

class InvalidMnemonicError(AezeedError):
    """Raised when the mnemonic words fail basic validation."""

class InvalidPassphraseError(AezeedError):
    """Raised when decryption fails due to an incorrect passphrase."""

class DecipheredCipherSeed(_namedtuple('_DecipheredCipherSeedFields', ('entropy', 'salt', 'internal_version', 'birthday'))):

    def __setattr__(self, name, value):
        raise AttributeError('frozen record')

    def __delattr__(self, name):
        raise AttributeError('frozen record')

    def __eq__(self, other):
        return type(self) is type(other) and tuple(self) == tuple(other)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(tuple(self))
_CRC32C_POLY = 2197175160

def _crc32c_table():
    table = []
    for i in range(256):
        crc = i
        for _ in range(8):
            if crc & 1:
                crc = crc >> 1 ^ _CRC32C_POLY
            else:
                crc >>= 1
        table.append(crc & 4294967295)
    return table
_CRC32C_TABLE = _crc32c_table()

def _crc32c(data):
    crc = 4294967295
    for b in data:
        crc = _CRC32C_TABLE[(crc ^ b) & 255] ^ crc >> 8
    return ~crc & 4294967295
BLOCK_SIZE = 16
EXTRACTED_KEY_SIZE = 3 * BLOCK_SIZE

def _mk_block(size=BLOCK_SIZE):
    return bytearray(size)
ZERO_BLOCK = _mk_block()

def _xor_bytes1x16(a, b, dst):
    for i in range(BLOCK_SIZE):
        dst[i] = a[i] ^ b[i]

def _xor_bytes4x16(a, b, c, d, dst):
    for i in range(BLOCK_SIZE):
        dst[i] = a[i] ^ b[i] ^ c[i] ^ d[i]

def _xor_bytes(a, b, dst):
    for i in range(len(dst)):
        dst[i] = a[i] ^ b[i]

def _uint32(i):
    return i & 4294967295

def _uint8(i):
    return i & 255

def _extract_key(key):
    if len(key) == EXTRACTED_KEY_SIZE:
        return key
    return _dependency('hashlib', 'blake2b')(key, digest_size=EXTRACTED_KEY_SIZE).digest()

def _mult_block(x, src, dst):
    t = _mk_block()
    r = _mk_block()
    t[:] = src
    while x:
        if x & 1:
            _xor_bytes1x16(r, t, r)
        _double_block(t)
        x >>= 1
    dst[:] = r

def _double_block(p):
    tmp = p[0]
    for i in range(15):
        p[i] = (p[i] << 1 | p[i + 1] >> 7) & 255
    p[15] = p[15] << 1 & 254 ^ (135 if tmp & 128 else 0)

def _one_zero_pad(src, size, dst):
    dst[:] = b'\x00' * len(dst)
    if size:
        dst[:size] = src[:size]
    dst[size] = 128
TE0 = [3328402341, 4168907908, 4000806809, 4135287693, 4294111757, 3597364157, 3731845041, 2445657428, 1613770832, 33620227, 3462883241, 1445669757, 3892248089, 3050821474, 1303096294, 3967186586, 2412431941, 528646813, 2311702848, 4202528135, 4026202645, 2992200171, 2387036105, 4226871307, 1101901292, 3017069671, 1604494077, 1169141738, 597466303, 1403299063, 3832705686, 2613100635, 1974974402, 3791519004, 1033081774, 1277568618, 1815492186, 2118074177, 4126668546, 2211236943, 1748251740, 1369810420, 3521504564, 4193382664, 3799085459, 2883115123, 1647391059, 706024767, 134480908, 2512897874, 1176707941, 2646852446, 806885416, 932615841, 168101135, 798661301, 235341577, 605164086, 461406363, 3756188221, 3454790438, 1311188841, 2142417613, 3933566367, 302582043, 495158174, 1479289972, 874125870, 907746093, 3698224818, 3025820398, 1537253627, 2756858614, 1983593293, 3084310113, 2108928974, 1378429307, 3722699582, 1580150641, 327451799, 2790478837, 3117535592, 0, 3253595436, 1075847264, 3825007647, 2041688520, 3059440621, 3563743934, 2378943302, 1740553945, 1916352843, 2487896798, 2555137236, 2958579944, 2244988746, 3151024235, 3320835882, 1336584933, 3992714006, 2252555205, 2588757463, 1714631509, 293963156, 2319795663, 3925473552, 67240454, 4269768577, 2689618160, 2017213508, 631218106, 1269344483, 2723238387, 1571005438, 2151694528, 93294474, 1066570413, 563977660, 1882732616, 4059428100, 1673313503, 2008463041, 2950355573, 1109467491, 537923632, 3858759450, 4260623118, 3218264685, 2177748300, 403442708, 638784309, 3287084079, 3193921505, 899127202, 2286175436, 773265209, 2479146071, 1437050866, 4236148354, 2050833735, 3362022572, 3126681063, 840505643, 3866325909, 3227541664, 427917720, 2655997905, 2749160575, 1143087718, 1412049534, 999329963, 193497219, 2353415882, 3354324521, 1807268051, 672404540, 2816401017, 3160301282, 369822493, 2916866934, 3688947771, 1681011286, 1949973070, 336202270, 2454276571, 201721354, 1210328172, 3093060836, 2680341085, 3184776046, 1135389935, 3294782118, 965841320, 831886756, 3554993207, 4068047243, 3588745010, 2345191491, 1849112409, 3664604599, 26054028, 2983581028, 2622377682, 1235855840, 3630984372, 2891339514, 4092916743, 3488279077, 3395642799, 4101667470, 1202630377, 268961816, 1874508501, 4034427016, 1243948399, 1546530418, 941366308, 1470539505, 1941222599, 2546386513, 3421038627, 2715671932, 3899946140, 1042226977, 2521517021, 1639824860, 227249030, 260737669, 3765465232, 2084453954, 1907733956, 3429263018, 2420656344, 100860677, 4160157185, 470683154, 3261161891, 1781871967, 2924959737, 1773779408, 394692241, 2579611992, 974986535, 664706745, 3655459128, 3958962195, 731420851, 571543859, 3530123707, 2849626480, 126783113, 865375399, 765172662, 1008606754, 361203602, 3387549984, 2278477385, 2857719295, 1344809080, 2782912378, 59542671, 1503764984, 160008576, 437062935, 1707065306, 3622233649, 2218934982, 3496503480, 2185314755, 697932208, 1512910199, 504303377, 2075177163, 2824099068, 1841019862, 739644986]
TE1 = [2781242211, 2230877308, 2582542199, 2381740923, 234877682, 3184946027, 2984144751, 1418839493, 1348481072, 50462977, 2848876391, 2102799147, 434634494, 1656084439, 3863849899, 2599188086, 1167051466, 2636087938, 1082771913, 2281340285, 368048890, 3954334041, 3381544775, 201060592, 3963727277, 1739838676, 4250903202, 3930435503, 3206782108, 4149453988, 2531553906, 1536934080, 3262494647, 484572669, 2923271059, 1783375398, 1517041206, 1098792767, 49674231, 1334037708, 1550332980, 4098991525, 886171109, 150598129, 2481090929, 1940642008, 1398944049, 1059722517, 201851908, 1385547719, 1699095331, 1587397571, 674240536, 2704774806, 252314885, 3039795866, 151914247, 908333586, 2602270848, 1038082786, 651029483, 1766729511, 3447698098, 2682942837, 454166793, 2652734339, 1951935532, 775166490, 758520603, 3000790638, 4004797018, 4217086112, 4137964114, 1299594043, 1639438038, 3464344499, 2068982057, 1054729187, 1901997871, 2534638724, 4121318227, 1757008337, 0, 750906861, 1614815264, 535035132, 3363418545, 3988151131, 3201591914, 1183697867, 3647454910, 1265776953, 3734260298, 3566750796, 3903871064, 1250283471, 1807470800, 717615087, 3847203498, 384695291, 3313910595, 3617213773, 1432761139, 2484176261, 3481945413, 283769337, 100925954, 2180939647, 4037038160, 1148730428, 3123027871, 3813386408, 4087501137, 4267549603, 3229630528, 2315620239, 2906624658, 3156319645, 1215313976, 82966005, 3747855548, 3245848246, 1974459098, 1665278241, 807407632, 451280895, 251524083, 1841287890, 1283575245, 337120268, 891687699, 801369324, 3787349855, 2721421207, 3431482436, 959321879, 1469301956, 4065699751, 2197585534, 1199193405, 2898814052, 3887750493, 724703513, 2514908019, 2696962144, 2551808385, 3516813135, 2141445340, 1715741218, 2119445034, 2872807568, 2198571144, 3398190662, 700968686, 3547052216, 1009259540, 2041044702, 3803995742, 487983883, 1991105499, 1004265696, 1449407026, 1316239930, 504629770, 3683797321, 168560134, 1816667172, 3837287516, 1570751170, 1857934291, 4014189740, 2797888098, 2822345105, 2754712981, 936633572, 2347923833, 852879335, 1133234376, 1500395319, 3084545389, 2348912013, 1689376213, 3533459022, 3762923945, 3034082412, 4205598294, 133428468, 634383082, 2949277029, 2398386810, 3913789102, 403703816, 3580869306, 2297460856, 1867130149, 1918643758, 607656988, 4049053350, 3346248884, 1368901318, 600565992, 2090982877, 2632479860, 557719327, 3717614411, 3697393085, 2249034635, 2232388234, 2430627952, 1115438654, 3295786421, 2865522278, 3633334344, 84280067, 33027830, 303828494, 2747425121, 1600795957, 4188952407, 3496589753, 2434238086, 1486471617, 658119965, 3106381470, 953803233, 334231800, 3005978776, 857870609, 3151128937, 1890179545, 2298973838, 2805175444, 3056442267, 574365214, 2450884487, 550103529, 1233637070, 4289353045, 2018519080, 2057691103, 2399374476, 4166623649, 2148108681, 387583245, 3664101311, 836232934, 3330556482, 3100665960, 3280093505, 2955516313, 2002398509, 287182607, 3413881008, 4238890068, 3597515707, 975967766]
TE2 = [1671808611, 2089089148, 2006576759, 2072901243, 4061003762, 1807603307, 1873927791, 3310653893, 810573872, 16974337, 1739181671, 729634347, 4263110654, 3613570519, 2883997099, 1989864566, 3393556426, 2191335298, 3376449993, 2106063485, 4195741690, 1508618841, 1204391495, 4027317232, 2917941677, 3563566036, 2734514082, 2951366063, 2629772188, 2767672228, 1922491506, 3227229120, 3082974647, 4246528509, 2477669779, 644500518, 911895606, 1061256767, 4144166391, 3427763148, 878471220, 2784252325, 3845444069, 4043897329, 1905517169, 3631459288, 827548209, 356461077, 67897348, 3344078279, 593839651, 3277757891, 405286936, 2527147926, 84871685, 2595565466, 118033927, 305538066, 2157648768, 3795705826, 3945188843, 661212711, 2999812018, 1973414517, 152769033, 2208177539, 745822252, 439235610, 455947803, 1857215598, 1525593178, 2700827552, 1391895634, 994932283, 3596728278, 3016654259, 695947817, 3812548067, 795958831, 2224493444, 1408607827, 3513301457, 0, 3979133421, 543178784, 4229948412, 2982705585, 1542305371, 1790891114, 3410398667, 3201918910, 961245753, 1256100938, 1289001036, 1491644504, 3477767631, 3496721360, 4012557807, 2867154858, 4212583931, 1137018435, 1305975373, 861234739, 2241073541, 1171229253, 4178635257, 33948674, 2139225727, 1357946960, 1011120188, 2679776671, 2833468328, 1374921297, 2751356323, 1086357568, 2408187279, 2460827538, 2646352285, 944271416, 4110742005, 3168756668, 3066132406, 3665145818, 560153121, 271589392, 4279952895, 4077846003, 3530407890, 3444343245, 202643468, 322250259, 3962553324, 1608629855, 2543990167, 1154254916, 389623319, 3294073796, 2817676711, 2122513534, 1028094525, 1689045092, 1575467613, 422261273, 1939203699, 1621147744, 2174228865, 1339137615, 3699352540, 577127458, 712922154, 2427141008, 2290289544, 1187679302, 3995715566, 3100863416, 339486740, 3732514782, 1591917662, 186455563, 3681988059, 3762019296, 844522546, 978220090, 169743370, 1239126601, 101321734, 611076132, 1558493276, 3260915650, 3547250131, 2901361580, 1655096418, 2443721105, 2510565781, 3828863972, 2039214713, 3878868455, 3359869896, 928607799, 1840765549, 2374762893, 3580146133, 1322425422, 2850048425, 1823791212, 1459268694, 4094161908, 3928346602, 1706019429, 2056189050, 2934523822, 135794696, 3134549946, 2022240376, 628050469, 779246638, 472135708, 2800834470, 3032970164, 3327236038, 3894660072, 3715932637, 1956440180, 522272287, 1272813131, 3185336765, 2340818315, 2323976074, 1888542832, 1044544574, 3049550261, 1722469478, 1222152264, 50660867, 4127324150, 236067854, 1638122081, 895445557, 1475980887, 3117443513, 2257655686, 3243809217, 489110045, 2662934430, 3778599393, 4162055160, 2561878936, 288563729, 1773916777, 3648039385, 2391345038, 2493985684, 2612407707, 505560094, 2274497927, 3911240169, 3460925390, 1442818645, 678973480, 3749357023, 2358182796, 2717407649, 2306869641, 219617805, 3218761151, 3862026214, 1120306242, 1756942440, 1103331905, 2578459033, 762796589, 252780047, 2966125488, 1425844308, 3151392187, 372911126]
TE3 = [1667474886, 2088535288, 2004326894, 2071694838, 4075949567, 1802223062, 1869591006, 3318043793, 808472672, 16843522, 1734846926, 724270422, 4278065639, 3621216949, 2880169549, 1987484396, 3402253711, 2189597983, 3385409673, 2105378810, 4210693615, 1499065266, 1195886990, 4042263547, 2913856577, 3570689971, 2728590687, 2947541573, 2627518243, 2762274643, 1920112356, 3233831835, 3082273397, 4261223649, 2475929149, 640051788, 909531756, 1061110142, 4160160501, 3435941763, 875846760, 2779116625, 3857003729, 4059105529, 1903268834, 3638064043, 825316194, 353713962, 67374088, 3351728789, 589522246, 3284360861, 404236336, 2526454071, 84217610, 2593830191, 117901582, 303183396, 2155911963, 3806477791, 3958056653, 656894286, 2998062463, 1970642922, 151591698, 2206440989, 741110872, 437923380, 454765878, 1852748508, 1515908788, 2694904667, 1381168804, 993742198, 3604373943, 3014905469, 690584402, 3823320797, 791638366, 2223281939, 1398011302, 3520161977, 0, 3991743681, 538992704, 4244381667, 2981218425, 1532751286, 1785380564, 3419096717, 3200178535, 960056178, 1246420628, 1280103576, 1482221744, 3486468741, 3503319995, 4025428677, 2863326543, 4227536621, 1128514950, 1296947098, 859002214, 2240123921, 1162203018, 4193849577, 33687044, 2139062782, 1347481760, 1010582648, 2678045221, 2829640523, 1364325282, 2745433693, 1077985408, 2408548869, 2459086143, 2644360225, 943212656, 4126475505, 3166494563, 3065430391, 3671750063, 555836226, 269496352, 4294908645, 4092792573, 3537006015, 3452783745, 202118168, 320025894, 3974901699, 1600119230, 2543297077, 1145359496, 387397934, 3301201811, 2812801621, 2122220284, 1027426170, 1684319432, 1566435258, 421079858, 1936954854, 1616945344, 2172753945, 1330631070, 3705438115, 572679748, 707427924, 2425400123, 2290647819, 1179044492, 4008585671, 3099120491, 336870440, 3739122087, 1583276732, 185277718, 3688593069, 3772791771, 842159716, 976899700, 168435220, 1229577106, 101059084, 606366792, 1549591736, 3267517855, 3553849021, 2897014595, 1650632388, 2442242105, 2509612081, 3840161747, 2038008818, 3890688725, 3368567691, 926374254, 1835907034, 2374863873, 3587531953, 1313788572, 2846482505, 1819063512, 1448540844, 4109633523, 3941213647, 1701162954, 2054852340, 2930698567, 134748176, 3132806511, 2021165296, 623210314, 774795868, 471606328, 2795958615, 3031746419, 3334885783, 3907527627, 3722280097, 1953799400, 522133822, 1263263126, 3183336545, 2341176845, 2324333839, 1886425312, 1044267644, 3048588401, 1718004428, 1212733584, 50529542, 4143317495, 235803164, 1633788866, 892690282, 1465383342, 3115962473, 2256965911, 3250673817, 488449850, 2661202215, 3789633753, 4177007595, 2560144171, 286339874, 1768537042, 3654906025, 2391705863, 2492770099, 2610673197, 505291324, 2273808917, 3924369609, 3469625735, 1431699370, 673740880, 3755965093, 2358021891, 2711746649, 2307489801, 218961690, 3217021541, 3873845719, 1111672452, 1751693520, 1094828930, 2576986153, 757954394, 252645662, 2964376443, 1414855848, 3149649517, 370555436]

def _read_uint32_be(block, offset):
    return int.from_bytes(bytes(block[offset:offset + 4]), 'big')

def _write_uint32_be(block, offset, value):
    block[offset:offset + 4] = value.to_bytes(4, 'big')

class _AESRound:

    def __init__(self, key):
        words = [_read_uint32_be(key, 4 * i) for i in range(12)]
        self.aes10_key = [0] * (4 * 10)
        self.aes4_key = [0] * (4 * 4)
        self.aes10_key[0:12] = words
        self.aes10_key[12:24] = words
        self.aes10_key[24:36] = words
        self.aes10_key[36:40] = words[0:4]
        self.aes4_key[0:4] = words[4:8]
        self.aes4_key[4:8] = words[0:4]
        self.aes4_key[8:12] = words[8:12]

    def reset(self):
        for i in range(len(self.aes10_key)):
            self.aes10_key[i] = 0
        for i in range(len(self.aes4_key)):
            self.aes4_key[i] = 0

    def AES4(self, j, i_vec, l_vec, src, dst):
        _xor_bytes4x16(j, i_vec, l_vec, src, dst)
        self.rounds(dst, 4)

    def AES10(self, l_vec, src, dst):
        _xor_bytes1x16(src, l_vec, dst)
        self.rounds(dst, 10)

    def rounds(self, block, rounds):
        keys = self.aes4_key if rounds == 4 else self.aes10_key
        s0 = _read_uint32_be(block, 0)
        s1 = _read_uint32_be(block, 4)
        s2 = _read_uint32_be(block, 8)
        s3 = _read_uint32_be(block, 12)
        for r in range(rounds):
            rk_off = r * 4
            t0 = TE0[_uint8(s0 >> 24)] ^ TE1[_uint8(s1 >> 16)] ^ TE2[_uint8(s2 >> 8)] ^ TE3[_uint8(s3)] ^ keys[rk_off]
            t1 = TE0[_uint8(s1 >> 24)] ^ TE1[_uint8(s2 >> 16)] ^ TE2[_uint8(s3 >> 8)] ^ TE3[_uint8(s0)] ^ keys[rk_off + 1]
            t2 = TE0[_uint8(s2 >> 24)] ^ TE1[_uint8(s3 >> 16)] ^ TE2[_uint8(s0 >> 8)] ^ TE3[_uint8(s1)] ^ keys[rk_off + 2]
            t3 = TE0[_uint8(s3 >> 24)] ^ TE1[_uint8(s0 >> 16)] ^ TE2[_uint8(s1 >> 8)] ^ TE3[_uint8(s2)] ^ keys[rk_off + 3]
            s0 = _uint32(t0)
            s1 = _uint32(t1)
            s2 = _uint32(t2)
            s3 = _uint32(t3)
        _write_uint32_be(block, 0, s0)
        _write_uint32_be(block, 4, s1)
        _write_uint32_be(block, 8, s2)
        _write_uint32_be(block, 12, s3)

class _AEZState:

    def __init__(self):
        self.I = [_mk_block(), _mk_block()]
        self.J = [_mk_block(), _mk_block(), _mk_block()]
        self.L = [_mk_block() for _ in range(8)]
        self.aes = None

    def reset(self):
        for buf in self.I + self.J + self.L:
            for i in range(len(buf)):
                buf[i] = 0
        if self.aes:
            self.aes.reset()

    def init(self, key):
        extracted = _extract_key(key)
        self.I[0][:] = extracted[0:16]
        _mult_block(2, self.I[0], self.I[1])
        self.J[0][:] = extracted[16:32]
        _mult_block(2, self.J[0], self.J[1])
        _mult_block(2, self.J[1], self.J[2])
        self.L[1][:] = extracted[32:48]
        _mult_block(2, self.L[1], self.L[2])
        _xor_bytes1x16(self.L[2], self.L[1], self.L[3])
        _mult_block(2, self.L[2], self.L[4])
        _xor_bytes1x16(self.L[4], self.L[1], self.L[5])
        _mult_block(2, self.L[3], self.L[6])
        _xor_bytes1x16(self.L[6], self.L[1], self.L[7])
        self.aes = _AESRound(extracted)

    def aez_hash(self, nonce, ad, tau):
        assert self.aes is not None
        buf = _mk_block()
        sum_block = _mk_block()
        I_tmp = _mk_block()
        J_tmp = _mk_block()
        buf[12:16] = _uint32(tau).to_bytes(4, 'big')
        _xor_bytes1x16(self.J[0], self.J[1], J_tmp)
        self.aes.AES4(J_tmp, self.I[1], self.L[1], buf, sum_block)
        empty_nonce = not nonce
        n_bytes = len(nonce) if nonce else 0
        I_tmp[:] = self.I[1]
        offset = 0
        i = 1
        while n_bytes >= BLOCK_SIZE:
            block = nonce[offset:offset + BLOCK_SIZE]
            tmp = _mk_block()
            tmp[:BLOCK_SIZE] = block
            self.aes.AES4(self.J[2], I_tmp, self.L[i % 8], tmp, buf)
            _xor_bytes1x16(sum_block, buf, sum_block)
            offset += BLOCK_SIZE
            n_bytes -= BLOCK_SIZE
            if i % 8 == 0:
                _double_block(I_tmp)
            i += 1
        if n_bytes > 0 or empty_nonce:
            buf[:] = b'\x00' * BLOCK_SIZE
            if not empty_nonce and nonce is not None:
                buf[:n_bytes] = nonce[offset:offset + n_bytes]
            buf[n_bytes] = 128
            self.aes.AES4(self.J[2], self.I[0], self.L[0], buf, buf)
            _xor_bytes1x16(sum_block, buf, sum_block)
        for k, piece in enumerate(ad):
            empty_piece = not piece
            bytes_left = len(piece) if piece else 0
            I_tmp[:] = self.I[1]
            J_tmp2 = _mk_block()
            _mult_block(5 + k, self.J[0], J_tmp2)
            offset = 0
            i = 1
            while bytes_left >= BLOCK_SIZE:
                tmp_in = piece[offset:offset + BLOCK_SIZE]
                tmp = _mk_block()
                tmp[:BLOCK_SIZE] = tmp_in
                self.aes.AES4(J_tmp2, I_tmp, self.L[i % 8], tmp, buf)
                _xor_bytes1x16(sum_block, buf, sum_block)
                offset += BLOCK_SIZE
                bytes_left -= BLOCK_SIZE
                if i % 8 == 0:
                    _double_block(I_tmp)
                i += 1
            if bytes_left > 0 or empty_piece:
                buf[:] = b'\x00' * BLOCK_SIZE
                if not empty_piece and piece:
                    buf[:bytes_left] = piece[offset:offset + bytes_left]
                buf[bytes_left] = 128
                self.aes.AES4(J_tmp2, self.I[0], self.L[0], buf, buf)
                _xor_bytes1x16(sum_block, buf, sum_block)
        return sum_block

    def aez_prf(self, delta, tau, dst):
        assert self.aes is not None
        buf = _mk_block()
        ctr = _mk_block()
        off = 0
        remaining = tau
        while remaining >= BLOCK_SIZE:
            _xor_bytes1x16(delta, ctr, buf)
            self.aes.AES10(self.L[3], buf, buf)
            dst[off:off + BLOCK_SIZE] = buf
            for idx in range(15, -1, -1):
                ctr[idx] = ctr[idx] + 1 & 255
                if ctr[idx] != 0:
                    break
            off += BLOCK_SIZE
            remaining -= BLOCK_SIZE
        if remaining > 0:
            _xor_bytes1x16(delta, ctr, buf)
            self.aes.AES10(self.L[3], buf, buf)
            dst[off:off + remaining] = buf[:remaining]

    def encipher(self, delta, data, dst):
        if not data:
            return
        if len(data) < 32:
            self.aez_tiny(delta, data, 0, dst)
        else:
            self.aez_core(delta, data, 0, dst)

    def decipher(self, delta, data, dst):
        if not data:
            return
        if len(data) < 32:
            self.aez_tiny(delta, data, 1, dst)
        else:
            self.aez_core(delta, data, 1, dst)

    def aez_tiny(self, delta, data, direction, dst):
        assert self.aes is not None
        in_bytes = len(data)
        buf = bytearray(2 * BLOCK_SIZE)
        buf_view = memoryview(buf)
        L = _mk_block()
        R = _mk_block()
        tmp = _mk_block()
        mask = 0
        pad = 128
        idx_param = 7
        if in_bytes == 1:
            rounds = 24
        elif in_bytes == 2:
            rounds = 16
        elif in_bytes < BLOCK_SIZE:
            rounds = 10
        else:
            idx_param = 6
            rounds = 8
        left_len = (in_bytes + 1) // 2
        right_start = in_bytes // 2
        L[:left_len] = data[:left_len]
        R[:left_len] = data[right_start:right_start + left_len]
        if in_bytes & 1:
            half = in_bytes // 2
            for k in range(half):
                R[k] = (R[k] << 4 | R[k + 1] >> 4) & 255
            R[half] = R[half] << 4 & 255
            pad = 8
            mask = 240
        if direction != 0:
            if in_bytes < BLOCK_SIZE:
                buf[:BLOCK_SIZE] = b'\x00' * BLOCK_SIZE
                buf[:in_bytes] = data
                buf[0] |= 128
                _xor_bytes1x16(delta, buf_view[:BLOCK_SIZE], buf_view[:BLOCK_SIZE])
                self.aes.AES4(ZERO_BLOCK, self.I[1], self.L[3], buf_view[:BLOCK_SIZE], tmp)
                L[0] ^= tmp[0] & 128
            j = rounds - 1
            step = -1
        else:
            j = 0
            step = 1
        for _ in range(rounds // 2):
            buf[:BLOCK_SIZE] = b'\x00' * BLOCK_SIZE
            buf[:left_len] = R[:left_len]
            mid_index = in_bytes // 2
            buf[mid_index] = buf[mid_index] & mask | pad
            _xor_bytes1x16(buf_view[:BLOCK_SIZE], delta, buf_view[:BLOCK_SIZE])
            buf[15] ^= j & 255
            self.aes.AES4(ZERO_BLOCK, self.I[1], self.L[idx_param], buf_view[:BLOCK_SIZE], tmp)
            _xor_bytes1x16(L, tmp, L)
            buf[:BLOCK_SIZE] = b'\x00' * BLOCK_SIZE
            buf[:left_len] = L[:left_len]
            buf[mid_index] = buf[mid_index] & mask | pad
            _xor_bytes1x16(buf_view[:BLOCK_SIZE], delta, buf_view[:BLOCK_SIZE])
            buf[15] ^= j + step & 255
            self.aes.AES4(ZERO_BLOCK, self.I[1], self.L[idx_param], buf_view[:BLOCK_SIZE], tmp)
            _xor_bytes1x16(R, tmp, R)
            j += step * 2
        half = in_bytes // 2
        buf[:half] = R[:half]
        buf[half:half + left_len] = L[:left_len]
        if in_bytes & 1:
            for k in range(in_bytes - 1, half, -1):
                buf[k] = (buf[k] >> 4 | buf[k - 1] << 4) & 255
            buf[half] = L[0] >> 4 & 15 | R[half] & 240
        dst[:in_bytes] = buf[:in_bytes]
        if in_bytes < BLOCK_SIZE and direction == 0:
            buf[in_bytes:BLOCK_SIZE] = b'\x00' * (BLOCK_SIZE - in_bytes)
            buf[0] |= 128
            _xor_bytes1x16(delta, buf_view[:BLOCK_SIZE], buf_view[:BLOCK_SIZE])
            self.aes.AES4(ZERO_BLOCK, self.I[1], self.L[3], buf_view[:BLOCK_SIZE], tmp)
            dst[0] ^= tmp[0] & 128

    def aez_core(self, delta, data, direction, dst):
        assert self.aes is not None
        in_bytes = len(data)
        frag_bytes = in_bytes % 32
        initial_bytes = in_bytes - frag_bytes - 32
        tmp = _mk_block()
        X = _mk_block()
        Y = _mk_block()
        S = _mk_block()
        input_bytes = bytearray(data)
        if in_bytes >= 64:
            self.aez_core_pass1(input_bytes, dst, X)
        tail = input_bytes[initial_bytes:]
        if frag_bytes >= BLOCK_SIZE:
            buf = _mk_block()
            buf[:BLOCK_SIZE] = tail[BLOCK_SIZE:BLOCK_SIZE * 2]
            self.aes.AES4(ZERO_BLOCK, self.I[1], self.L[4], buf, tmp)
            _xor_bytes1x16(X, tmp, X)
            padded = _mk_block()
            _one_zero_pad(tail[BLOCK_SIZE:], frag_bytes - BLOCK_SIZE, padded)
            self.aes.AES4(ZERO_BLOCK, self.I[1], self.L[5], padded, tmp)
            _xor_bytes1x16(X, tmp, X)
        elif frag_bytes > 0:
            padded = _mk_block()
            _one_zero_pad(tail, frag_bytes, padded)
            self.aes.AES4(ZERO_BLOCK, self.I[1], self.L[4], padded, tmp)
            _xor_bytes1x16(X, tmp, X)
        dst_tail = dst[in_bytes - 32:in_bytes]
        input_tail = input_bytes[in_bytes - 32:in_bytes]
        block1 = _mk_block()
        block1[:BLOCK_SIZE] = input_tail[:BLOCK_SIZE]
        block2 = _mk_block()
        block2[:BLOCK_SIZE] = input_tail[BLOCK_SIZE:BLOCK_SIZE * 2]
        self.aes.AES4(ZERO_BLOCK, self.I[1], self.L[(1 + direction) % 8], block2, tmp)
        first_dst = _mk_block()
        _xor_bytes4x16(X, block1, delta, tmp, first_dst)
        dst_tail[:BLOCK_SIZE] = first_dst
        tmp2 = _mk_block()
        self.aes.AES10(self.L[(1 + direction) % 8], first_dst, tmp2)
        second_dst = bytearray(block2)
        _xor_bytes1x16(second_dst, tmp2, second_dst)
        dst_tail[BLOCK_SIZE:BLOCK_SIZE * 2] = second_dst
        _xor_bytes1x16(first_dst, second_dst, S)
        if in_bytes >= 64:
            self.aez_core_pass2(input_bytes, dst, Y, S)
        dst_fragment = dst[initial_bytes:]
        input_fragment = input_bytes[initial_bytes:]
        if frag_bytes >= BLOCK_SIZE:
            tmp_block = _mk_block()
            self.aes.AES10(self.L[4], S, tmp_block)
            block = bytearray(input_fragment[:BLOCK_SIZE])
            _xor_bytes1x16(block, tmp_block, block)
            dst_fragment[:BLOCK_SIZE] = block
            self.aes.AES4(ZERO_BLOCK, self.I[1], self.L[4], block, tmp)
            _xor_bytes1x16(Y, tmp, Y)
            remaining = frag_bytes - BLOCK_SIZE
            tmp_block = _mk_block()
            self.aes.AES10(self.L[5], S, tmp_block)
            buf = bytearray(tmp_block)
            fragment = bytearray(input_fragment[BLOCK_SIZE:BLOCK_SIZE + remaining])
            for idx in range(remaining):
                buf[idx] ^= fragment[idx]
            dst_fragment[BLOCK_SIZE:BLOCK_SIZE + remaining] = buf[:remaining]
            buf[:] = b'\x00' * BLOCK_SIZE
            buf[:remaining] = dst_fragment[BLOCK_SIZE:BLOCK_SIZE + remaining]
            buf[remaining] = 128
            self.aes.AES4(ZERO_BLOCK, self.I[1], self.L[5], buf, tmp)
            _xor_bytes1x16(Y, tmp, Y)
            dst_fragment = dst_fragment[BLOCK_SIZE + remaining:]
            input_fragment = input_fragment[BLOCK_SIZE + remaining:]
        elif frag_bytes > 0:
            tmp_block = _mk_block()
            self.aes.AES10(self.L[4], S, tmp_block)
            buf = bytearray(tmp_block)
            fragment = bytearray(input_fragment[:frag_bytes])
            for idx in range(frag_bytes):
                buf[idx] ^= fragment[idx]
            dst_fragment[:frag_bytes] = buf[:frag_bytes]
            buf[:] = b'\x00' * BLOCK_SIZE
            buf[:frag_bytes] = dst_fragment[:frag_bytes]
            buf[frag_bytes] = 128
            self.aes.AES4(ZERO_BLOCK, self.I[1], self.L[4], buf, tmp)
            _xor_bytes1x16(Y, tmp, Y)
            dst_fragment = dst_fragment[frag_bytes:]
            input_fragment = input_fragment[frag_bytes:]
        dst_tail = dst[in_bytes - 32:in_bytes]
        second_half = bytearray(dst_tail[BLOCK_SIZE:BLOCK_SIZE * 2])
        tmp_block = _mk_block()
        self.aes.AES10(self.L[(2 - direction) % 8], second_half, tmp_block)
        first_half = bytearray(dst_tail[:BLOCK_SIZE])
        _xor_bytes1x16(first_half, tmp_block, first_half)
        dst_tail[:BLOCK_SIZE] = first_half
        self.aes.AES4(ZERO_BLOCK, self.I[1], self.L[(2 - direction) % 8], first_half, tmp)
        combined = _mk_block()
        _xor_bytes4x16(tmp, dst_tail[BLOCK_SIZE:BLOCK_SIZE * 2], delta, Y, combined)
        dst_tail[BLOCK_SIZE:BLOCK_SIZE * 2] = combined
        tmp_copy = bytearray(dst_tail[:BLOCK_SIZE])
        dst_tail[:BLOCK_SIZE] = combined
        dst_tail[BLOCK_SIZE:BLOCK_SIZE * 2] = tmp_copy

    def aez_core_pass1(self, input_bytes, output, X):
        assert self.aes is not None
        tmp = _mk_block()
        I_tmp = _mk_block()
        I_tmp[:] = self.I[1]
        offset = 0
        remaining = len(input_bytes)
        i = 1
        while remaining >= 64:
            block1 = bytearray(input_bytes[offset + BLOCK_SIZE:offset + BLOCK_SIZE * 2])
            self.aes.AES4(self.J[0], I_tmp, self.L[i % 8], block1, tmp)
            first_out = bytearray(input_bytes[offset:offset + BLOCK_SIZE])
            _xor_bytes1x16(first_out, tmp, first_out)
            output[offset:offset + BLOCK_SIZE] = first_out
            self.aes.AES4(ZERO_BLOCK, self.I[0], self.L[0], first_out, tmp)
            second_out = bytearray(input_bytes[offset + BLOCK_SIZE:offset + BLOCK_SIZE * 2])
            _xor_bytes1x16(second_out, tmp, second_out)
            output[offset + BLOCK_SIZE:offset + BLOCK_SIZE * 2] = second_out
            _xor_bytes1x16(second_out, X, X)
            offset += 32
            remaining -= 32
            i += 1
            if i % 8 == 0:
                _double_block(I_tmp)

    def aez_core_pass2(self, input_bytes, output, Y, S):
        assert self.aes is not None
        tmp = _mk_block()
        I_tmp = _mk_block()
        I_tmp[:] = self.I[1]
        offset = 0
        remaining = len(input_bytes)
        i = 1
        while remaining >= 64:
            first_out = bytearray(output[offset:offset + BLOCK_SIZE])
            second_out = bytearray(output[offset + BLOCK_SIZE:offset + BLOCK_SIZE * 2])
            self.aes.AES4(self.J[1], I_tmp, self.L[i % 8], S, tmp)
            _xor_bytes1x16(first_out, tmp, first_out)
            _xor_bytes1x16(second_out, tmp, second_out)
            _xor_bytes1x16(first_out, Y, Y)
            self.aes.AES4(ZERO_BLOCK, self.I[0], self.L[0], second_out, tmp)
            _xor_bytes1x16(first_out, tmp, first_out)
            self.aes.AES4(self.J[0], I_tmp, self.L[i % 8], first_out, tmp)
            _xor_bytes1x16(second_out, tmp, second_out)
            temp = bytearray(first_out)
            first_out[:] = second_out
            second_out[:] = temp
            output[offset:offset + BLOCK_SIZE] = first_out
            output[offset + BLOCK_SIZE:offset + BLOCK_SIZE * 2] = second_out
            offset += 32
            remaining -= 32
            i += 1
            if i % 8 == 0:
                _double_block(I_tmp)

def _aez_decrypt(key, ad_list, tau, ciphertext):
    state = _AEZState()
    state.reset()
    state.init(key)
    delta = state.aez_hash(None, list(ad_list), tau * 8)
    x = bytearray(len(ciphertext))
    if len(ciphertext) == tau:
        state.aez_prf(delta, tau, x)
        mismatch = 0
        for i in range(tau):
            mismatch |= x[i] ^ ciphertext[i]
        if mismatch != 0:
            return None
        return bytes()
    state.decipher(delta, ciphertext, x)
    mismatch = 0
    for i in range(tau):
        mismatch |= x[len(ciphertext) - tau + i]
    if mismatch != 0:
        return None
    return bytes(x[:len(ciphertext) - tau])

def mnemonic_to_bytes(words, word_to_index):
    if len(words) != 24:
        raise InvalidMnemonicError('aezeed mnemonics must have 24 words')
    bits = 0
    bit_len = 0
    out = bytearray(EncipheredCipherSeedSize)
    pos = 0
    for word in words:
        try:
            idx = word_to_index[word]
        except KeyError as exc:
            raise InvalidMnemonicError(f'unknown word: {word}') from exc
        bits = bits << BitsPerWord | idx
        bit_len += BitsPerWord
        while bit_len >= 8:
            bit_len -= 8
            out[pos] = bits >> bit_len & 255
            bits &= (1 << bit_len) - 1 if bit_len else 0
            pos += 1
    return bytes(out)

def validate_mnemonic(words, word_to_index):
    try:
        cipher_bytes = mnemonic_to_bytes(words, word_to_index)
    except InvalidMnemonicError:
        return False
    if cipher_bytes[0] != CipherSeedVersion:
        return False
    expected = int.from_bytes(cipher_bytes[-4:], 'big')
    computed = _crc32c(cipher_bytes[:EncipheredCipherSeedSize - 4])
    return expected == computed

def _encode_ad(version, salt):
    return bytes([version]) + salt

def decode_mnemonic(words, passphrase, word_to_index):
    cipher_bytes = mnemonic_to_bytes(words, word_to_index)
    version = cipher_bytes[0]
    if version != CipherSeedVersion:
        raise InvalidMnemonicError('unsupported aezeed version')
    checksum = int.from_bytes(cipher_bytes[-4:], 'big')
    computed = _crc32c(cipher_bytes[:EncipheredCipherSeedSize - 4])
    if checksum != computed:
        raise InvalidMnemonicError('checksum mismatch')
    salt = cipher_bytes[EncipheredCipherSeedSize - 4 - SaltSize:EncipheredCipherSeedSize - 4]
    ciphertext = cipher_bytes[1:EncipheredCipherSeedSize - 4 - SaltSize]
    candidate_passphrases = []
    if passphrase:
        candidate_passphrases.append(passphrase)
        candidate_passphrases.append(DEFAULT_PASSPHRASE + passphrase)
    else:
        candidate_passphrases.append(DEFAULT_PASSPHRASE)
    ad = _encode_ad(version, salt)
    plaintext = None
    for candidate in candidate_passphrases:
        pass_bytes = candidate.encode('utf-8')
        key = _dependency('hashlib', 'scrypt')(pass_bytes, salt=salt, n=32768, r=8, p=1, dklen=32, maxmem=2000000000)
        plaintext = _aez_decrypt(key, [ad], CipherTextExpansion, ciphertext)
        if plaintext is not None and len(plaintext) == DecipheredCipherSeedSize:
            break
    if plaintext is None or len(plaintext) != DecipheredCipherSeedSize:
        raise InvalidPassphraseError('invalid passphrase')
    internal_version = plaintext[0]
    birthday = int.from_bytes(plaintext[1:3], 'big')
    entropy = plaintext[3:]
    return DecipheredCipherSeed(entropy=bytes(entropy), salt=bytes(salt), internal_version=internal_version, birthday=birthday)

def has_valid_checksum(words, word_to_index):
    """Backwards-compatible alias for checksum validation-only checks."""
    return validate_mnemonic(words, word_to_index)
