/* SPDX-License-Identifier: GPL-2.0-only */
/* Caller holds execution stopped and guarantees validated writable code addresses. */
#include "live_patch.h"
int bm_patch_batch(const bm_u32 *pcs,const bm_u32 *from,const bm_u32 *to,bm_u32 count,
                   bm_read_word read_code,bm_write_code write_code,void *context)
{
    bm_u32 i,actual;
    if(!count || count>32)return -1;
    for(i=0;i<count;i++){
        if(read_code(pcs[i],&actual,context) || actual!=from[i])return -1;
    }
    for(i=0;i<count;i++)write_code(pcs[i],to[i],context);
    return 0;
}
