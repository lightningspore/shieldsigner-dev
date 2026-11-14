/* SPDX-License-Identifier: GPL-2.0-only */
#ifndef BM_LIVE_PREFLIGHT_H
#define BM_LIVE_PREFLIGHT_H
#include "live_ir.h"
int bm_preflight_acquire(void);
void bm_preflight_release(void);
bm_u32 bm_preflight_base(unsigned int index);
#endif
