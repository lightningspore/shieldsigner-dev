/* SPDX-License-Identifier: GPL-2.0-only */
#ifndef BM_LIVE_IR_H
#define BM_LIVE_IR_H
#ifdef __KERNEL__
#include <linux/types.h>
typedef u32 bm_u32; typedef s32 bm_s32;
#else
#include <stdint.h>
typedef uint32_t bm_u32; typedef int32_t bm_s32;
#endif
struct bm_operand { bm_s32 reg; bm_u32 shift, immediate; };
struct bm_memory { bm_s32 base,index; bm_u32 shift; bm_s32 displacement; };
struct bm_op { bm_u32 kind,reg,pc; struct bm_operand a,b; struct bm_memory memory; };
typedef int (*bm_read_word)(bm_u32,bm_u32 *,void *);
int bm_predict(const struct bm_op *,bm_u32,bm_u32 *,bm_u32,bm_read_word,void *,bm_u32 *,bm_u32 *);
int bm_encode_call(bm_u32,bm_u32,int,bm_u32 *);
int bm_decode_call(bm_u32,bm_u32,bm_u32 *,int *);
#endif
