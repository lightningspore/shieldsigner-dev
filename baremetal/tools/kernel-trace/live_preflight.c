/* SPDX-License-Identifier: GPL-2.0-only */
/* Pin and validate original camera modules. This module never patches code. */
#include <linux/module.h>
#include <linux/device.h>
#include <linux/platform_device.h>
#include <linux/i2c.h>
#include <linux/regmap.h>
#include <linux/uaccess.h>
#include <asm/barrier.h>
#include "live_sites.h"

static struct module *owners[3];
static const char *const device_names[]={"mipi0-csi2","ff3e8000.csi2-dphy-hw","4-0030"};
void bm_preflight_release(void)
{
    unsigned int i;
    for(i=0;i<ARRAY_SIZE(owners);i++)if(owners[i]){module_put(owners[i]);owners[i]=NULL;}
}
static int pin_owner(unsigned int i)
{
    struct device *device=bus_find_device_by_name(i==2?&i2c_bus_type:&platform_bus_type,NULL,device_names[i]);
    struct module *owner;
    int result=-ENODEV;
    if(!device)return result;
    device_lock(device);
    owner=device->driver?device->driver->owner:NULL;
    if(owner && !strcmp(owner->name,bm_modules[i].name) && try_module_get(owner)){
        owners[i]=owner;result=0;
    }
    device_unlock(device);put_device(device);
    return result;
}
u32 bm_preflight_base(unsigned int index)
{
    return index<ARRAY_SIZE(owners)&&owners[index]?(u32)owners[index]->core_layout.base:0;
}
int bm_preflight_acquire(void)
{
    unsigned int i;
    int result=-EINVAL;
    for(i=0;i<ARRAY_SIZE(owners);i++){
        result=pin_owner(i);if(result)goto fail;
        if(owners[i]->core_layout.text_size<bm_modules[i].text_size){result=-EINVAL;goto fail;}
        pr_info("bm_preflight: pinned %s text=%08x\n",owners[i]->name,(u32)owners[i]->core_layout.base);
    }
    for(i=0;i<ARRAY_SIZE(bm_sites);i++){
        const struct bm_site_spec *site=&bm_sites[i];
        u32 pc=(u32)owners[site->module]->core_layout.base+site->offset;
        u32 instruction,target,expected;
        int link;
        unsigned char bytes[24];
        result=-EINVAL;
        if(site->offset+4+bm_post_lengths[i]>bm_modules[site->module].text_size)goto fail;
        if(copy_from_kernel_nofault(&instruction,(void *)pc,4))goto fail;
        if(bm_decode_call(pc,instruction,&target,&link))goto fail;
        expected=site->kind==0?(u32)arm_heavy_mb:site->kind==1?(u32)regmap_write:(u32)i2c_transfer_buffer_flags;
        if(target!=(expected&~1U) || link!=site->link){
            pr_err("bm_preflight: site%u target=%08x expected=%08x link=%d expected_link=%u\n",i,target,expected,link,site->link);
            goto fail;
        }
        if(copy_from_kernel_nofault(bytes,(void *)(pc+4),bm_post_lengths[i]))goto fail;
        if(memcmp(bytes,bm_post_bytes[i],bm_post_lengths[i]))goto fail;
        pr_info("bm_preflight: site%u pc=%08x target=%08x PASS\n",i,pc,target);
    }
    pr_info("bm_preflight: all%u sites PASS; no code writes\n",(unsigned int)ARRAY_SIZE(bm_sites));
    return 0;
fail:
    pr_err("bm_preflight: FAIL at index%u result%d; no code writes\n",i,result);
    bm_preflight_release();return result;
}
#ifndef BM_PREFLIGHT_LIBRARY
static void __exit preflight_exit(void){bm_preflight_release();}
module_init(bm_preflight_acquire);module_exit(preflight_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Read-only original camera callsite validation and module pinning");
#endif
