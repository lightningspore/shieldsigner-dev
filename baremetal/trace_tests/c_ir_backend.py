"""Exercise the same C predictor/branch implementation intended for the kernel observer."""

from pathlib import Path
import ctypes as C
import subprocess

ROOT = Path(__file__).resolve().parents[1]
folder = ROOT / 'build/trace-c-test'
folder.mkdir(parents=True, exist_ok=True)
libpath = folder / 'live_ir.so'
subprocess.run(
    [
        'cc',
        '-shared',
        '-fPIC',
        '-Wall',
        '-Wextra',
        '-Werror',
        '-O2',
        str(ROOT / 'tools/kernel-trace/live_ir.c'),
        '-o',
        str(libpath),
    ],
    check=True,
)
LIB = C.CDLL(str(libpath))


class Operand(C.Structure):
    _fields_ = [('reg', C.c_int32), ('shift', C.c_uint32), ('immediate', C.c_uint32)]


class Memory(C.Structure):
    _fields_ = [
        ('base', C.c_int32),
        ('index', C.c_int32),
        ('shift', C.c_uint32),
        ('displacement', C.c_int32),
    ]


class Op(C.Structure):
    _fields_ = [
        ('kind', C.c_uint32),
        ('reg', C.c_uint32),
        ('pc', C.c_uint32),
        ('a', Operand),
        ('b', Operand),
        ('memory', Memory),
    ]


Reader = C.CFUNCTYPE(C.c_int, C.c_uint32, C.POINTER(C.c_uint32), C.c_void_p)
LIB.bm_predict.argtypes = [
    C.POINTER(Op),
    C.c_uint32,
    C.POINTER(C.c_uint32),
    C.c_uint32,
    Reader,
    C.c_void_p,
    C.POINTER(C.c_uint32),
    C.POINTER(C.c_uint32),
]
LIB.bm_encode_call.argtypes = [C.c_uint32, C.c_uint32, C.c_int, C.POINTER(C.c_uint32)]
LIB.bm_decode_call.argtypes = [C.c_uint32, C.c_uint32, C.POINTER(C.c_uint32), C.POINTER(C.c_int)]


def operand(item):
    return Operand(
        item.get('register', -1), item.get('shift', 0), item.get('immediate', 0) & 0xFFFFFFFF
    )


def predict_c(program, registers, base, read_word):
    ops = []
    for item in program:
        op = Op()
        op.kind = {'load': 0, 'store': 1, 'move': 2, 'add': 3}[item['kind']]
        op.reg = item['register']
        op.pc = item['pcOffset']
        if op.kind < 2:
            m = item['memory']
            op.memory = Memory(
                m['base'],
                m['index'] if m['index'] is not None else -1,
                m['shift'],
                m['displacement'],
            )
        elif op.kind == 2:
            op.a = operand(item['operand'])
        else:
            op.a = operand(item['left'])
            op.b = operand(item['right'])
        ops.append(op)
    array = (Op * len(ops))(*ops)
    regs = (C.c_uint32 * 16)(*registers)
    address = C.c_uint32()
    value = C.c_uint32()

    @Reader
    def reader(addr, out, context):
        out[0] = read_word(addr)
        return 0

    result = LIB.bm_predict(
        array, len(ops), regs, base, reader, None, C.byref(address), C.byref(value)
    )
    if result:
        raise RuntimeError('C predictor rejected program')
    return address.value, value.value


def call_c(pc, target, link):
    result = C.c_uint32()
    if LIB.bm_encode_call(pc, target, link, C.byref(result)):
        raise ValueError('Out of range')
    decoded = C.c_uint32()
    decoded_link = C.c_int()
    if LIB.bm_decode_call(pc, result.value, C.byref(decoded), C.byref(decoded_link)):
        raise ValueError('Decode failed')
    assert decoded.value == (target & ~1) and decoded_link.value == link
    return result.value.to_bytes(4, 'little')
