#include <stddef.h>
#include <stdint.h>
typedef uint8_t u8; typedef uint16_t u16; typedef uint32_t u32; typedef uint64_t u64;
typedef int8_t s8; typedef int16_t s16; typedef int32_t s32; typedef int64_t s64;
#define BIT(n) (1UL << (n))
#define BIT_ULL(n) (1ULL << (n))
#include <linux/rk-isp32-config.h>
_Static_assert(sizeof(struct isp32_awb_gain_cfg)==32,"AWB record size");
_Static_assert(offsetof(struct isp32_isp_params_cfg,others.awb_gain_cfg)==0x1225,"AWB record offset");
_Static_assert(ISP32_MODULE_AWB_GAIN==(1ULL<<5),"AWB enable mask");
const unsigned int recovered_layout[]={sizeof(struct isp32_isp_params_cfg),offsetof(struct isp32_isp_params_cfg,others.awb_gain_cfg),sizeof(struct isp32_awb_gain_cfg)};

/* Explicit old-time ARM32 userspace ABI used by the pinned daemon. musl's
 * current native struct timespec is time64 and must not determine this ioctl. */
#include <sys/time.h>
struct recovered_timespec32 { int32_t tv_sec; int32_t tv_nsec; };
#define timespec recovered_timespec32
#include <linux/videodev2.h>
#undef timespec
_Static_assert(sizeof(struct v4l2_event)==128,"ARM32 old-time event size");
_Static_assert(offsetof(struct v4l2_event,sequence)==76,"event sequence offset");
_Static_assert(sizeof(struct v4l2_event_subscription)==32,"subscription size");
_Static_assert(VIDIOC_DQEVENT==0x80805659,"old-time event ioctl");
_Static_assert(VIDIOC_SUBSCRIBE_EVENT==0x4020565a,"subscribe ioctl");
#include <linux/media.h>
_Static_assert(sizeof(struct media_pad_desc)==20,"media pad size");
_Static_assert(sizeof(struct media_link_desc)==52,"media link size");
_Static_assert(sizeof(struct media_links_enum)==28,"ARM media links query size");
_Static_assert(offsetof(struct media_entity_desc,pads)==52,"media entity pad count");
_Static_assert(offsetof(struct media_entity_desc,links)==54,"media entity link count");
_Static_assert(MEDIA_IOC_ENUM_LINKS==0xc01c7c02,"ARM media links ioctl");
_Static_assert(MEDIA_ENT_F_CAM_SENSOR==0x20001,"sensor entity type");
const unsigned int statistics_layout[]={
 sizeof(struct rkisp32_isp_stat_buffer),
 offsetof(struct rkisp32_isp_stat_buffer,meas_type),
 offsetof(struct rkisp32_isp_stat_buffer,frame_id),
 offsetof(struct rkisp32_isp_stat_buffer,params_id),
 offsetof(struct isp32_stat,rawae0),offsetof(struct isp32_stat,rawhist0),
 offsetof(struct isp32_stat,rawawb),offsetof(struct isp32_stat,rawawb.sum),
 offsetof(struct isp32_stat,rawawb.yhist_bin),offsetof(struct isp32_stat,rawawb.sum_exc),
 ISP32_RAWAWB_RAMDATA_NUM,ISP32_RAWAWB_SUM_NUM,ISP32_RAWAWB_HSTBIN_NUM,ISP32_RAWAWB_EXCL_STAT_NUM
};
