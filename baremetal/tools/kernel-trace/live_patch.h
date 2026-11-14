/* SPDX-License-Identifier: GPL-2.0-only */
#ifndef BM_LIVE_PATCH_H
#define BM_LIVE_PATCH_H
#include "live_ir.h"
typedef void (*bm_write_code)(bm_u32,bm_u32,void *);
int bm_patch_batch(const bm_u32 *pcs,const bm_u32 *from,const bm_u32 *to,bm_u32 count,
                   bm_read_word read_code,bm_write_code write_code,void *context);
#endif
