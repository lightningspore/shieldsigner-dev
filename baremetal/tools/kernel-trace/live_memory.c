/* SPDX-License-Identifier: GPL-2.0-only */
/* REF-specific read-only adapter. No target MMIO reads or page-table writes. */
#include <linux/uaccess.h>
#include <linux/irqflags.h>
#include <asm/memory.h>
#include "live_memory.h"
#include "live_translate.h"

#if defined(CONFIG_ARM_LPAE) || defined(CONFIG_HIGHMEM)
#error This observer requires the verified REF non-LPAE low-memory configuration
#endif
#define REF_RAM_BYTES 0x04000000U

static int read_table(bm_u32 physical,bm_u32 *value,void *unused)
{
    /* Verified REF /proc/iomem: System RAM 00000000–03ffffff. */
    if((physical&3) || physical>REF_RAM_BYTES-4)return -1;
    return copy_from_kernel_nofault(value,__va(physical),4)?-1:0;
}

int bm_live_physical(bm_u32 virtual_address,bm_u32 *physical_address)
{
    unsigned long flags;
    bm_u32 control,root;
    int result;
    /* ARM module mappings sit below PAGE_OFFSET, above user TASK_SIZE. */
    if(virtual_address<MODULES_VADDR || PHYS_OFFSET!=0)return -1;
    local_irq_save(flags);
    asm volatile("mrc p15,0,%0,c2,c0,2" : "=r"(control));
    /* Pinned proc-v7-2level.S sets N=0 and keeps swapper PGD in TTBR1.
     * Reject a different setup rather than assuming its table geometry. */
    if(control!=0){local_irq_restore(flags);return -1;}
    asm volatile("mrc p15,0,%0,c2,c0,1" : "=r"(root));
    root&=0xffffc000U;
    result=bm_translate_short(root,virtual_address,read_table,NULL,physical_address);
    local_irq_restore(flags);
    return result;
}

int bm_live_read_ddr(bm_u32 virtual_address,bm_u32 *value,void *unused)
{
    bm_u32 physical;
    if((virtual_address&3) || bm_live_physical(virtual_address,&physical))return -1;
    /* Address-prediction loads may read normal DDR/module data, never devices. */
    if(physical>REF_RAM_BYTES-4)return -1;
    return read_table(physical,value,NULL);
}
