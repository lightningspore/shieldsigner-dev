/* SPDX-License-Identifier: GPL-2.0-only */
#ifndef BM_LIVE_TRANSLATE_H
#define BM_LIVE_TRANSLATE_H
#include "live_ir.h"
/* read_table reads physical DDR page-table words, never the mapped target. */
int bm_translate_short(bm_u32 pgd,bm_u32 virtual_address,bm_read_word read_table,
                      void *context,bm_u32 *physical_address);
#endif
