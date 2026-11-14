/* SPDX-License-Identifier: GPL-2.0-only */
/* Read-only translation validation. No camera register accesses. */
#include <linux/module.h>
#include <linux/io.h>
#include <linux/slab.h>
#include <asm/memory.h>
#include "live_memory.h"
static const u32 module_word=0x33361103;

static int __init probe_init(void)
{
    u32 *word,physical=0,value=0;
    void __iomem *mapping;
    int result=-EINVAL;
    word=kmalloc(sizeof(*word),GFP_KERNEL);
    if(!word)return -ENOMEM;
    *word=0x1103cafe;
    if(bm_live_physical((u32)word,&physical) || physical!=__pa(word))goto out;
    if(bm_live_read_ddr((u32)word,&value,NULL) || value!=*word)goto out;
    pr_info("bm_memory_probe: RAM translation/read PASS phys=%08x\n",physical);
    if(bm_live_physical((u32)&module_word,&physical) || physical>=0x04000000)goto out;
    if(bm_live_read_ddr((u32)&module_word,&value,NULL) || value!=module_word)goto out;
    pr_info("bm_memory_probe: module-data translation/read PASS\n");
    /* ioremap creates a mapping only. Deliberately never dereference it. */
    mapping=ioremap(0xffa10000,0x10000);
    if(!mapping){result=-ENOMEM;goto out;}
    if(bm_live_physical((u32)mapping,&physical) || physical!=0xffa10000)goto unmap;
    if(bm_live_physical((u32)mapping+0xfffc,&physical) || physical!=0xffa1fffc)goto unmap;
    if(bm_live_read_ddr((u32)mapping,&value,NULL)!=-1)goto unmap;
    if(bm_live_physical(0x1000,&physical)!=-1)goto unmap;
    pr_info("bm_memory_probe: device translation and device-read rejection PASS\n");
    result=0;
unmap:
    iounmap(mapping);
out:
    kfree(word);
    if(result)pr_err("bm_memory_probe: FAIL %d\n",result);
    return result;
}
static void __exit probe_exit(void){}
module_init(probe_init);module_exit(probe_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Temporary read-only REF address translation self-test");
