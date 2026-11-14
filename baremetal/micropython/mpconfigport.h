// SPDX-License-Identifier: MIT
#include <stdint.h>
#include <alloca.h>
#define MICROPY_CONFIG_ROM_LEVEL MICROPY_CONFIG_ROM_LEVEL_CORE_FEATURES
#define MICROPY_LONGINT_IMPL MICROPY_LONGINT_IMPL_MPZ
#define MICROPY_ENABLE_COMPILER (1)
#define MICROPY_ENABLE_GC (1)
#define MICROPY_HELPER_REPL (1)
#define MICROPY_ENABLE_EXTERNAL_IMPORT (1)
#define MICROPY_ENABLE_SOURCE_LINE (1)
#define MICROPY_PY_BUILTINS_BYTEARRAY (1)
#define MICROPY_PY_BUILTINS_MEMORYVIEW (1)
#define MICROPY_PY_BUILTINS_MIN_MAX (1)
#define MICROPY_PY_BUILTINS_ENUMERATE (1)
#define MICROPY_PY_GC (1)
#define MICROPY_HW_BOARD_NAME "Luckfox Pico Mini"
#define MICROPY_HW_MCU_NAME "RV1103 Cortex-A7"
#define MICROPY_NLR_THUMB_USE_LONG_JUMP (1)
#define MP_STATE_PORT MP_STATE_VM
typedef long mp_off_t;

// Service the console at VM branches, including a running Python loop.
#define MICROPY_KBD_EXCEPTION (1)
void bm_micropython_poll(void);
#define MICROPY_VM_HOOK_LOOP do { bm_micropython_poll(); } while (0);
#define MICROPY_PY_STRUCT_UNSAFE_TYPECODES (0)

// Native screen configs use upstream JSON, with no filesystem dependency.
#define MICROPY_PY_JSON (1)

// Original app settings parsing requires real CPython-compatible double values.
// Native UI builds link the pinned complete newlib/libm runtime.
#if BM_NATIVE_UI
#define MICROPY_ENABLE_FINALISER (1)
#define MICROPY_PY_COLLECTIONS_ORDEREDDICT (1)
#define MICROPY_PY_ARRAY_SLICE_ASSIGN (1)
#define MICROPY_PY_BINASCII (1)
#define MICROPY_PY_BUILTINS_BYTES_HEX (1)
#define MICROPY_PY_BUILTINS_STR_UNICODE (1)
#define MICROPY_PY_BUILTINS_STR_UNICODE_CHECK (1)
#define MICROPY_FLOAT_IMPL MICROPY_FLOAT_IMPL_DOUBLE
#endif

// Preserve dataclass-equivalent rich comparison fallback semantics.
#define MICROPY_PY_BUILTINS_NOTIMPLEMENTED (1)
