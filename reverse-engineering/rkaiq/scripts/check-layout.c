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
