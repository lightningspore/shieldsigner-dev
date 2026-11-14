/* SPDX-License-Identifier: GPL-2.0-only */
/* Original narrow interpreter: predict the original instruction's store; never perform it. */
#include "live_ir.h"
static bm_u32 operand(const struct bm_operand *op,const bm_u32 *regs)
{
    return op->reg<0 ? op->immediate : regs[op->reg]<<op->shift;
}
int bm_predict(const struct bm_op *ops,bm_u32 count,bm_u32 *regs,bm_u32 text_base,
    bm_read_word read_word,void *context,bm_u32 *address,bm_u32 *value)
{
    bm_u32 i;
    if(count>4)return -1;
    for(i=0;i<count;i++){
        const struct bm_op *op=&ops[i];
        bm_u32 target;
        if(op->reg>15 || op->kind>3)return -1;
        regs[15]=(text_base+op->pc+4)&~3U;
        if(op->kind<2){
            if(op->memory.base<0 || op->memory.base>15 || op->memory.index>15 || op->memory.shift>31)return -1;
            target=regs[op->memory.base]+op->memory.displacement;
            if(op->memory.index>=0)target+=regs[op->memory.index]<<op->memory.shift;
            if(op->kind==1){*address=target;*value=regs[op->reg];return 0;}
            if(read_word(target,&regs[op->reg],context))return -1;
        }else{
            if(op->a.reg>15 || op->b.reg>15 || op->a.shift>31 || op->b.shift>31)return -1;
            target=operand(&op->a,regs);
            if(op->kind==3)target+=operand(&op->b,regs);
            regs[op->reg]=target;
        }
    }
    return -1;
}
int bm_encode_call(bm_u32 pc,bm_u32 target,int link,bm_u32 *result)
{
    bm_s32 offset=(bm_s32)((target&~1U)-pc-4);
    bm_u32 bits,s,i1,i2,first,second;
    if((offset&1) || offset<-(1<<24) || offset>((1<<24)-2))return -1;
    bits=(bm_u32)offset;s=(bits>>24)&1;i1=(bits>>23)&1;i2=(bits>>22)&1;
    first=0xf000|(s<<10)|((bits>>12)&1023);
    second=(link?0xd000:0x9000)|((1^(i1^s))<<13)|((1^(i2^s))<<11)|((bits>>1)&2047);
    *result=first|(second<<16);
    return 0;
}
int bm_decode_call(bm_u32 pc,bm_u32 instruction,bm_u32 *target,int *link)
{
    bm_u32 first=instruction&65535,second=instruction>>16;
    bm_u32 s,i1,i2,bits,base=pc+4;
    if((first&0xf800)!=0xf000)return -1;
    if((second&0xd001)==0xc000){*link=1;base&=~3U;}
    else if((second&0xd000)==0xd000)*link=1;
    else if((second&0xd000)==0x9000)*link=0;
    else return -1;
    s=(first>>10)&1;i1=1^(((second>>13)&1)^s);i2=1^(((second>>11)&1)^s);
    bits=(s<<24)|(i1<<23)|(i2<<22)|((first&1023)<<12)|((second&2047)<<1);
    if(s)bits|=0xfe000000;
    *target=base+bits;
    return 0;
}
