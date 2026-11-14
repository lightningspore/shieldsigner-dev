// SPDX-License-Identifier: GPL-2.0-only
/* Original runtime-only write recorder for studying the vendor camera modules. */
#include <linux/module.h>
#include <linux/debugfs.h>
#include <linux/io.h>
#include <linux/ktime.h>
#include <linux/seq_file.h>
#include <linux/spinlock.h>
#include <linux/uaccess.h>
#include <linux/vmalloc.h>
#define CAPACITY 32768
struct event { u64 ns; u32 block, offset, value, width; };
static struct event *events;
static u32 count, dropped;
static bool enabled;
static unsigned int readers;
static DEFINE_SPINLOCK(lock);
static struct dentry *directory;

static void record(u32 block,u32 offset,u32 value,u32 width)
{
    if (!enabled) return;
    if (count==CAPACITY) { dropped++; return; }
    events[count++]=(struct event){ktime_get_ns(),block,offset,value,width};
}
void bm_trace_mmio(u32 block,u32 offset,u32 value,void __iomem *address)
{
    unsigned long flags;
    spin_lock_irqsave(&lock,flags);
    writel(value,address);
    record(block,offset,value,4);
    spin_unlock_irqrestore(&lock,flags);
}
EXPORT_SYMBOL_GPL(bm_trace_mmio);
void bm_trace_value(u32 block,u32 offset,u32 value,u32 width)
{
    unsigned long flags;
    spin_lock_irqsave(&lock,flags);
    record(block,offset,value,width);
    spin_unlock_irqrestore(&lock,flags);
}
EXPORT_SYMBOL_GPL(bm_trace_value);
static int show(struct seq_file *out,void *unused)
{
    u32 i,n;
    unsigned long flags;
    spin_lock_irqsave(&lock,flags);
    n=count;
    seq_printf(out,"# enabled=%u count=%u dropped=%u\n",enabled,count,dropped);
    spin_unlock_irqrestore(&lock,flags);
    /* Read only after recording stopped; the controller rejects active reads. */
    for(i=0;i<n;i++) seq_printf(out,"%u %llu %u 0x%08x 0x%08x %u\n",i,events[i].ns,
        events[i].block,events[i].offset,events[i].value,events[i].width);
    return 0;
}
static int open_events(struct inode *inode,struct file *file)
{
    unsigned long flags;
    int result;
    spin_lock_irqsave(&lock,flags);
    if(enabled){spin_unlock_irqrestore(&lock,flags);return -EBUSY;}
    readers++;
    spin_unlock_irqrestore(&lock,flags);
    result=single_open(file,show,NULL);
    if(result){spin_lock_irqsave(&lock,flags);readers--;spin_unlock_irqrestore(&lock,flags);}
    return result;
}
static int release_events(struct inode *inode,struct file *file)
{
    unsigned long flags;
    int result=single_release(inode,file);
    spin_lock_irqsave(&lock,flags);readers--;spin_unlock_irqrestore(&lock,flags);
    return result;
}
static const struct file_operations event_ops={.owner=THIS_MODULE,.open=open_events,
    .read=seq_read,.llseek=seq_lseek,.release=release_events};
static ssize_t control(struct file *file,const char __user *buffer,size_t size,loff_t *position)
{
    char command;unsigned long flags;
    if(size<1||copy_from_user(&command,buffer,1))return -EFAULT;
    if(command!='0'&&command!='1')return -EINVAL;
    spin_lock_irqsave(&lock,flags);
    if(command=='1'&&readers){spin_unlock_irqrestore(&lock,flags);return -EBUSY;}
    if(command=='1'){count=0;dropped=0;enabled=true;}else enabled=false;
    spin_unlock_irqrestore(&lock,flags);
    return size;
}
static const struct file_operations control_ops={.owner=THIS_MODULE,.write=control,.llseek=no_llseek};
static int __init trace_init(void)
{
    events=vzalloc(sizeof(*events)*CAPACITY);if(!events)return -ENOMEM;
    directory=debugfs_create_dir("baremetal_camera_trace",NULL);
    if(IS_ERR_OR_NULL(directory)){vfree(events);return -ENODEV;}
    debugfs_create_file("control",0200,directory,NULL,&control_ops);
    debugfs_create_file("events",0400,directory,NULL,&event_ops);
    return 0;
}
static void __exit trace_exit(void){debugfs_remove_recursive(directory);vfree(events);}
module_init(trace_init);module_exit(trace_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Temporary bounded camera write recorder; no persistent changes");
