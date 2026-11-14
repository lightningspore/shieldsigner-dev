# SPDX-License-Identifier: MIT
# Original RV1103 port, linking the unchanged pinned MicroPython core.
MPY_TOP ?= $(abspath ../.tools/micropython)
BOARD_BINDINGS ?= 0
ifeq ($(BOARD_BINDINGS),1)
BUILD ?= $(abspath ../build/micropython-board)
else
BUILD ?= $(abspath ../build/micropython)
endif
CROSS_COMPILE = arm-none-eabi-
include $(MPY_TOP)/py/mkenv.mk
QSTR_DEFS = qstrdefsport.h
QSTR_GLOBAL_DEPENDENCIES += Makefile
MICROPY_ROM_TEXT_COMPRESSION = 0
include $(TOP)/py/py.mk
INC += -I. -I$(TOP) -I$(BUILD) -isystem $(abspath ../.tools/newlib/include)
CFLAGS += $(INC) -Wall -Werror -std=c99 -Os -g -DNDEBUG -ffreestanding -fno-common -fno-builtin -fdata-sections -ffunction-sections -mthumb -mcpu=cortex-a7 -mfloat-abi=soft -mno-unaligned-access
SRC_C = runtime.c shared/libc/printf.c shared/libc/string0.c shared/readline/readline.c shared/runtime/pyexec.c shared/runtime/stdout_helpers.c shared/runtime/gchelper_native.c
SRC_S = shared/runtime/gchelper_thumb2.s
ifeq ($(BOARD_BINDINGS),1)
SRC_C += modmachine.c modcamera.c
SRC_QSTR += modmachine.c modcamera.c
endif
SRC_QSTR += shared/readline/readline.c shared/runtime/pyexec.c
OBJ = $(PY_CORE_O) $(addprefix $(BUILD)/,$(SRC_C:.c=.o)) $(addprefix $(BUILD)/,$(SRC_S:.s=.o))
all: $(BUILD)/libmicropython.a
include $(TOP)/py/mkrules.mk
