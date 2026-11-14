/* SPDX-License-Identifier: GPL-2.0-only */
/* Temporary clock references for read-only snapshots; no device detach or reset. */
#include <linux/module.h>
#include <linux/device.h>
#include <linux/platform_device.h>
#include <linux/clk.h>
struct held_device {
    const char *name;
    struct device *device;
    struct module *owner;
    struct clk_bulk_data *clocks;
    int count;
    bool enabled;
};
static struct held_device devices[]={
    {.name="ffa10000.rkcif"},
    {.name="ffa20000.mipi-csi2-hw"},
    {.name="ff3e8000.csi2-dphy-hw"},
    {.name="ffa00000.rkisp"},
};
static void release_all(void)
{
    int i;
    for(i=ARRAY_SIZE(devices)-1;i>=0;i--){
        struct held_device *held=&devices[i];
        if(held->enabled){clk_bulk_disable_unprepare(held->count,held->clocks);held->enabled=false;}
        if(held->count>0){clk_bulk_put_all(held->count,held->clocks);held->count=0;}
        if(held->owner){module_put(held->owner);held->owner=NULL;}
        if(held->device){put_device(held->device);held->device=NULL;}
    }
}
static int __init hold_init(void)
{
    unsigned int i;
    int result=-ENODEV;
    for(i=0;i<ARRAY_SIZE(devices);i++){
        struct held_device *held=&devices[i];
        result=-ENODEV;
        held->device=bus_find_device_by_name(&platform_bus_type,NULL,held->name);
        if(!held->device)goto fail;
        device_lock(held->device);
        if(held->device->driver && held->device->driver->owner && try_module_get(held->device->driver->owner))
            held->owner=held->device->driver->owner;
        device_unlock(held->device);
        if(!held->owner)goto fail;
        held->count=clk_bulk_get_all(held->device,&held->clocks);
        if(held->count<=0){result=held->count?held->count:-ENODEV;goto fail;}
        result=clk_bulk_prepare_enable(held->count,held->clocks);
        if(result)goto fail;
        held->enabled=true;
        pr_info("bm_snapshot_clocks: held %s clocks=%d\n",held->name,held->count);
    }
    pr_info("bm_snapshot_clocks: ready; clock rates/resets/device graph unchanged\n");
    return 0;
fail:
    release_all();return result;
}
static void __exit hold_exit(void){release_all();}
module_init(hold_init);module_exit(hold_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Temporary camera clock references for register snapshots");
