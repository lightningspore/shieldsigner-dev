/* SPDX-License-Identifier: GPL-2.0-only */
/* Original bounded observer for the pinned REF kernel. No device graph changes. */
#include <linux/module.h>
#include <linux/debugfs.h>
#include <linux/seq_file.h>
#include <linux/uaccess.h>
#include <linux/vmalloc.h>
#include <linux/ktime.h>
#include <linux/mutex.h>
#include <linux/stop_machine.h>
#include <linux/regmap.h>
#include <linux/i2c.h>
#include <asm/cacheflush.h>
#include <asm/barrier.h>
#include "live_sites.h"
#include "live_memory.h"
#include "live_preflight.h"
#include "live_patch.h"
#if defined(CONFIG_SMP) || !defined(CONFIG_PREEMPT_NONE) || defined(CONFIG_STRICT_KERNEL_RWX)
#error Observer requires the verified single-core nonpreemptible writable-text REF configuration
#endif
#define CAPACITY 32768
struct observation { u64 ns; u32 kind,site,address,value,width; };
static struct observation *events;
static u32 count,dropped,errors;
static bool recording,applied;
static unsigned int readers;
static atomic_t active=ATOMIC_INIT(0);
static DEFINE_SPINLOCK(event_lock);
static DEFINE_MUTEX(control_lock);
static struct dentry *directory;
static u32 original[ARRAY_SIZE(bm_sites)],replacement[ARRAY_SIZE(bm_sites)];
static u32 pcs[ARRAY_SIZE(bm_sites)];
extern void bm_io_wrapper(void);

static void observe(u32 kind,u32 site,u32 address,u32 value,u32 width)
{
    unsigned long flags;
    spin_lock_irqsave(&event_lock,flags);
    if(recording){
        if(count==CAPACITY)dropped++;
        else events[count++]=(struct observation){ktime_get_ns(),kind,site,address,value,width};
    }
    spin_unlock_irqrestore(&event_lock,flags);
}
static void failed_observation(void)
{
    unsigned long flags;
    spin_lock_irqsave(&event_lock,flags);if(recording)errors++;spin_unlock_irqrestore(&event_lock,flags);
}
void bm_trace_io_snapshot(const u32 *saved)
{
    unsigned int i;
    u32 regs[16],address,value,physical,pc=(saved[13]&~1U)-4;
    atomic_inc(&active);
    if(!READ_ONCE(recording))goto out;
    for(i=0;i<ARRAY_SIZE(bm_sites);i++){
        const struct bm_site_spec *site=&bm_sites[i];
        u32 base=bm_preflight_base(site->module);
        if(site->kind || base+site->offset!=pc)continue;
        memcpy(regs,saved,13*sizeof(u32));regs[13]=(u32)saved+56;regs[14]=saved[13];regs[15]=0;
        if(bm_predict(site->ops,site->count,regs,base,bm_live_read_ddr,NULL,&address,&value) ||
           bm_live_physical(address,&physical)){failed_observation();goto out;}
        observe(0,i,physical,value,4);goto out;
    }
    failed_observation();
out:
    atomic_dec(&active);
}
static int observe_regmap(u32 site,struct regmap *map,unsigned int reg,unsigned int value)
{
    int result;
    atomic_inc(&active);result=regmap_write(map,reg,value);
    if(!result)observe(1,site,reg,value,4);
    atomic_dec(&active);return result;
}
#define REGMAP_WRAPPER(n) static noinline int regmap_##n(struct regmap *map,unsigned int reg,unsigned int value) \
{return observe_regmap(n,map,reg,value);}
REGMAP_WRAPPER(3)
REGMAP_WRAPPER(15)
REGMAP_WRAPPER(16)
static noinline int sensor_17(const struct i2c_client *client,char *buffer,int length,u16 flags)
{
    int result,i;
    u32 reg,value=0;
    atomic_inc(&active);
    result=i2c_transfer_buffer_flags(client,buffer,length,flags);
    if(result==length && !(flags&I2C_M_RD) && length>=3 && length<=6){
        reg=((u8)buffer[0]<<8)|(u8)buffer[1];
        for(i=2;i<length;i++)value=(value<<8)|(u8)buffer[i];
        observe(2,17,reg,value,length-2);
    }else if(result==length && READ_ONCE(recording))failed_observation();
    atomic_dec(&active);return result;
}
static u32 hook_target(unsigned int i)
{
    if(bm_sites[i].kind==0)return (u32)bm_io_wrapper;
    if(i==3)return (u32)regmap_3;
    if(i==15)return (u32)regmap_15;
    if(i==16)return (u32)regmap_16;
    if(i==17)return (u32)sensor_17;
    return 0;
}
static u32 site_pc(unsigned int i)
{
    return bm_preflight_base(bm_sites[i].module)+bm_sites[i].offset;
}
static int read_code(u32 pc,u32 *word,void *unused)
{
    return copy_from_kernel_nofault(word,(void *)pc,4)?-1:0;
}
static void write_code(u32 pc,u32 word,void *unused)
{
    /* Thumb calls may be halfword-aligned; do not issue unaligned u32 stores. */
    WRITE_ONCE(*(u16 *)pc,(u16)word);WRITE_ONCE(*(u16 *)(pc+2),(u16)(word>>16));
    flush_icache_range(pc,pc+4);
}
static int patch_stopped(void *context)
{
    bool install=*(bool *)context;
    /* No writes until every word has passed validation in the stopped context. */
    if(atomic_read(&active))return -EBUSY;
    return bm_patch_batch(pcs,install?original:replacement,install?replacement:original,
                          ARRAY_SIZE(bm_sites),read_code,write_code,NULL)?-EINVAL:0;
}
static int change_hooks(bool install)
{
    unsigned int i;
    int result;
    if(install==applied)return -EINVAL;
    if(install){
        for(i=0;i<ARRAY_SIZE(bm_sites);i++){
            u32 pc=site_pc(i),target=hook_target(i);
            u32 destination,expected;
            int link;
            pcs[i]=pc;
            if(!target || (bm_sites[i].kind==0 && !bm_sites[i].link))return -EINVAL;
            if(copy_from_kernel_nofault(&original[i],(void *)pc,4))return -EFAULT;
            if(bm_decode_call(pc,original[i],&destination,&link))return -EINVAL;
            expected=bm_sites[i].kind==0?(u32)arm_heavy_mb:bm_sites[i].kind==1?(u32)regmap_write:(u32)i2c_transfer_buffer_flags;
            if(destination!=(expected&~1U)||link!=bm_sites[i].link)return -EINVAL;
            if(bm_encode_call(pc,target,bm_sites[i].link,&replacement[i]))return -ERANGE;
        }
        /* Keep this module resident even after the control file closes. */
        if(!try_module_get(THIS_MODULE))return -ENODEV;
    }
    result=stop_machine(patch_stopped,&install,NULL);
    if(result){if(install)module_put(THIS_MODULE);return result;}
    applied=install;
    if(!install)module_put(THIS_MODULE);
    return 0;
}
static int show(struct seq_file *out,void *unused)
{
    u32 i;
    seq_printf(out,"# applied=%u count=%u dropped=%u errors=%u; kind0=pre-store-MMIO kind1=successful-regmap kind2=successful-sensor\n",applied,count,dropped,errors);
    for(i=0;i<count;i++)seq_printf(out,"%u %llu %u %u 0x%08x 0x%08x %u\n",i,events[i].ns,
        events[i].kind,events[i].site,events[i].address,events[i].value,events[i].width);
    return 0;
}
static int open_events(struct inode *inode,struct file *file)
{
    int result;
    mutex_lock(&control_lock);
    if(recording){mutex_unlock(&control_lock);return -EBUSY;}
    readers++;result=single_open(file,show,NULL);if(result)readers--;
    mutex_unlock(&control_lock);return result;
}
static int release_events(struct inode *inode,struct file *file)
{
    int result=single_release(inode,file);
    mutex_lock(&control_lock);readers--;mutex_unlock(&control_lock);return result;
}
static const struct file_operations event_ops={.owner=THIS_MODULE,.open=open_events,.read=seq_read,
    .llseek=seq_lseek,.release=release_events};
static ssize_t control(struct file *file,const char __user *buffer,size_t size,loff_t *position)
{
    char command;int result=0;unsigned long flags;
    if(size<1||copy_from_user(&command,buffer,1))return -EFAULT;
    mutex_lock(&control_lock);
    if(command=='A'||command=='R'){
        if(recording||readers)result=-EBUSY;else result=change_hooks(command=='A');
    }else if(command=='1'||command=='0'){
        if(command=='1'&&(!applied||readers))result=-EBUSY;
        else{
            spin_lock_irqsave(&event_lock,flags);
            if(command=='1'){count=0;dropped=0;errors=0;recording=true;}else recording=false;
            spin_unlock_irqrestore(&event_lock,flags);
        }
    }else result=-EINVAL;
    mutex_unlock(&control_lock);return result?result:size;
}
static const struct file_operations control_ops={.owner=THIS_MODULE,.write=control,.llseek=no_llseek};
static int __init observer_init(void)
{
    int result=bm_preflight_acquire();
    if(result)return result;
    events=vzalloc(CAPACITY*sizeof(*events));if(!events){result=-ENOMEM;goto fail;}
    directory=debugfs_create_dir("baremetal_live_trace",NULL);
    if(IS_ERR_OR_NULL(directory)){result=-ENODEV;vfree(events);goto fail;}
    debugfs_create_file("control",0200,directory,NULL,&control_ops);
    debugfs_create_file("events",0400,directory,NULL,&event_ops);
    return 0;
fail:
    bm_preflight_release();return result;
}
static void __exit observer_exit(void)
{
    debugfs_remove_recursive(directory);vfree(events);bm_preflight_release();
}
module_init(observer_init);module_exit(observer_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Temporary camera write observer with explicit validated apply/restore");
