/* SPDX-License-Identifier: GPL-2.0-only */
#ifndef BM_LIVE_MEMORY_H
#define BM_LIVE_MEMORY_H
#include "live_ir.h"
int bm_live_physical(bm_u32 virtual_address,bm_u32 *physical_address);
int bm_live_read_ddr(bm_u32 virtual_address,bm_u32 *value,void *unused);
#endif
