/* SPDX-License-Identifier: GPL-2.0-only */
/* Original ARM short-descriptor walker for observation, not a mapping editor. */
#include "live_translate.h"
int bm_translate_short(bm_u32 pgd,bm_u32 va,bm_read_word read_table,
                      void *context,bm_u32 *pa)
{
    bm_u32 first,second;
    if(pgd&0x3fffU)return -1;
    if(read_table(pgd+((va>>20)*4),&first,context))return -1;
    switch(first&3){
    case 2:
        /* Supersections can encode physical addresses above32 bits. Refuse. */
        if(first&(1U<<18))return -1;
        *pa=(first&0xfff00000U)|(va&0xfffffU);return 0;
    case 1:
        if(read_table((first&0xfffffc00U)+(((va>>12)&255)*4),&second,context))return -1;
        if((second&3)==1){*pa=(second&0xffff0000U)|(va&65535);return 0;}
        if(second&2){*pa=(second&0xfffff000U)|(va&4095);return 0;}
        return -1;
    default:return -1;
    }
}
