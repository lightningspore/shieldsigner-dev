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
 * current native timeval/timespec are time64 and must not determine ioctls. */
#include <sys/time.h>
struct recovered_timespec32 { int32_t tv_sec; int32_t tv_nsec; };
struct recovered_timeval32 { int32_t tv_sec; int32_t tv_usec; };
#define timespec recovered_timespec32
#define timeval recovered_timeval32
#include <linux/videodev2.h>
#undef timespec
#undef timeval
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
#include <linux/rk-video-format.h>
_Static_assert(V4L2_BUF_TYPE_META_CAPTURE==13,"metadata capture type");
_Static_assert(V4L2_CAP_META_CAPTURE==0x00800000,"metadata capture capability");
_Static_assert(V4L2_META_FMT_RK_ISP1_STAT_3A==0x53314b52,"RK1S statistics FourCC");
_Static_assert(offsetof(struct v4l2_meta_format,dataformat)==0,"metadata FourCC offset");
_Static_assert(offsetof(struct v4l2_meta_format,buffersize)==4,"metadata size offset");
_Static_assert(sizeof(struct isp2x_bls_fixed_val)==8,"signed BLS/gain record size");
_Static_assert(offsetof(struct isp2x_bls_fixed_val,b)==6,"BLS blue offset");
#include <linux/v4l2-subdev.h>
#include <linux/rk-camera-module.h>
_Static_assert(sizeof(struct v4l2_subdev_format)==88,"subdevice format size");
_Static_assert(offsetof(struct v4l2_subdev_format,format.width)==8,"subdevice width offset");
_Static_assert(offsetof(struct v4l2_subdev_format,format.height)==12,"subdevice height offset");
_Static_assert(offsetof(struct v4l2_subdev_format,format.code)==16,"subdevice bus code offset");
_Static_assert(VIDIOC_SUBDEV_G_FMT==0xc0585604,"subdevice format request");
_Static_assert(offsetof(struct v4l2_subdev_format,which)==0,"format which");
_Static_assert(offsetof(struct v4l2_subdev_format,pad)==4,"format pad");
_Static_assert(VIDIOC_SUBDEV_S_FMT==0xc0585605,"set format request");
_Static_assert(sizeof(struct v4l2_subdev_selection)==64,"subdevice selection size");
_Static_assert(offsetof(struct v4l2_subdev_selection,which)==0,"selection which");
_Static_assert(offsetof(struct v4l2_subdev_selection,pad)==4,"selection pad");
_Static_assert(offsetof(struct v4l2_subdev_selection,target)==8,"selection target");
_Static_assert(offsetof(struct v4l2_subdev_selection,flags)==12,"selection flags");
_Static_assert(offsetof(struct v4l2_subdev_selection,r)==16,"selection rectangle");
_Static_assert(offsetof(struct v4l2_subdev_selection,reserved)==32,"selection reserved");
_Static_assert(V4L2_SUBDEV_FORMAT_ACTIVE==1,"active format enum");
_Static_assert(V4L2_SEL_TGT_CROP==0,"crop target enum");
_Static_assert(VIDIOC_SUBDEV_S_SELECTION==0xc040563e,"set selection request");
_Static_assert(sizeof(struct v4l2_subdev_frame_interval)==48,"subdevice interval size");
_Static_assert(offsetof(struct v4l2_subdev_frame_interval,interval)==4,"interval fraction offset");
_Static_assert(VIDIOC_SUBDEV_G_FRAME_INTERVAL==0xc0305615,"interval request");
_Static_assert(sizeof(struct v4l2_queryctrl)==68,"control query size");
_Static_assert(offsetof(struct v4l2_queryctrl,minimum)==40,"minimum control offset");
_Static_assert(sizeof(struct v4l2_ext_control)==20,"extended control size");
_Static_assert(offsetof(struct v4l2_ext_control,value64)==12,"pixel-rate value offset");
_Static_assert(sizeof(struct v4l2_ext_controls)==24,"ARM extended controls size");
_Static_assert(offsetof(struct v4l2_ext_controls,controls)==20,"ARM control pointer offset");
_Static_assert(VIDIOC_G_EXT_CTRLS==0xc0185647,"extended controls request");
_Static_assert(RKMODULE_GET_NR_SWITCH_THRESHOLD==0x801056c9,"noise-switch query");
_Static_assert(RKMODULE_GET_DCG_RATIO==0x800c56d2,"DCG ratio query");
_Static_assert(sizeof(struct v4l2_control)==8,"control write/read payload");
_Static_assert(offsetof(struct v4l2_control,value)==4,"control value offset");
_Static_assert(VIDIOC_G_CTRL==0xc008561b,"control read request");
_Static_assert(VIDIOC_S_CTRL==0xc008561c,"control write request");
_Static_assert(RKMODULE_SET_CONVERSION_GAIN==0x400456c6,"conversion gain write request");
_Static_assert(V4L2_CID_VBLANK==0x009e0901,"VBLANK ID");
_Static_assert(V4L2_CID_ANALOGUE_GAIN==0x009e0903,"analogue gain ID");
_Static_assert(V4L2_CID_GAIN==0x00980913,"native digital gain control ID");
_Static_assert(V4L2_CID_EXPOSURE==0x00980911,"exposure control ID");
_Static_assert(ISP32_MODULE_BLS==2,"black-level module mask");
_Static_assert(offsetof(struct isp32_isp_params_cfg,others.bls_cfg)==0x7ae,"black-level block offset");
_Static_assert(sizeof(struct isp32_bls_cfg)==44,"black-level block size");
_Static_assert(offsetof(struct isp32_bls_cfg,fixed_val)==20,"black-level fixed channel offset");
_Static_assert(offsetof(struct isp32_bls_cfg,bls1_val)==28,"black-level stage1 offset");
_Static_assert(offsetof(struct isp32_bls_cfg,isp_ob_offset)==36,"optical-black offset");
_Static_assert(offsetof(struct isp32_bls_cfg,isp_ob_predgain)==38,"optical-black gain");
_Static_assert(offsetof(struct isp32_bls_cfg,isp_ob_max)==40,"optical-black maximum");
_Static_assert(ISP32_MODULE_DEBAYER==(1ULL<<35),"demosaic module mask");
_Static_assert(offsetof(struct isp32_isp_params_cfg,others.debayer_cfg)==0x1282,"demosaic block offset");
_Static_assert(sizeof(struct isp32_debayer_cfg)==57,"demosaic block size");
_Static_assert(offsetof(struct isp32_debayer_cfg,filter1_coe1)==8,"demosaic coefficients");
_Static_assert(offsetof(struct isp32_debayer_cfg,ce_sgm)==25,"demosaic normalization");
_Static_assert(offsetof(struct isp32_debayer_cfg,bf_sgm)==31,"demosaic sigma");
_Static_assert(offsetof(struct isp32_debayer_cfg,hf_offset)==33,"demosaic offset");
_Static_assert(offsetof(struct isp32_debayer_cfg,edge_scale)==49,"demosaic edge scale");
_Static_assert(offsetof(struct isp32_debayer_cfg,alpha_scale)==53,"demosaic alpha scale");
_Static_assert(V4L2_BUF_TYPE_META_OUTPUT==14,"metadata output type");
_Static_assert(V4L2_CAP_META_OUTPUT==0x08000000,"metadata output capability");
_Static_assert(V4L2_META_FMT_RK_ISP1_PARAMS==0x50314b52,"RK1P parameter FourCC");
_Static_assert(offsetof(struct v4l2_buffer,bytesused)==8,"buffer payload size");
_Static_assert(offsetof(struct v4l2_buffer,flags)==12,"buffer flags");
_Static_assert(offsetof(struct v4l2_buffer,timestamp)==20,"legacy ARM timestamp");
_Static_assert(offsetof(struct v4l2_buffer,timecode)==28,"legacy ARM timecode");
_Static_assert(offsetof(struct v4l2_buffer,sequence)==44,"legacy ARM sequence");
_Static_assert(offsetof(struct v4l2_buffer,memory)==48,"legacy ARM memory");
_Static_assert(offsetof(struct v4l2_buffer,length)==56,"legacy ARM length");
_Static_assert(VIDIOC_REQBUFS==0xc0145608,"request buffer ioctl");
_Static_assert(VIDIOC_QBUF==0xc044560f,"queue buffer ioctl");
_Static_assert(VIDIOC_DQBUF==0xc0445611,"dequeue buffer ioctl");
_Static_assert(VIDIOC_STREAMON==0x40045612,"stream on ioctl");
_Static_assert(VIDIOC_STREAMOFF==0x40045613,"stream off ioctl");
_Static_assert(sizeof(struct isp2x_rawaelite_meas_cfg)==10,"AE lite size");
_Static_assert(sizeof(struct isp2x_rawaebig_meas_cfg)==46,"AE big size");
_Static_assert(sizeof(struct isp2x_rawhistlite_cfg)==41,"histogram lite size");
_Static_assert(sizeof(struct isp2x_rawhistbig_cfg)==242,"histogram big size");
_Static_assert(offsetof(struct isp32_isp_params_cfg,meas.rawae0)==0x41b,"AE0 offset");
_Static_assert(offsetof(struct isp32_isp_params_cfg,meas.rawae1)==0x425,"AE1 offset");
_Static_assert(offsetof(struct isp32_isp_params_cfg,meas.rawae2)==0x453,"AE2 offset");
_Static_assert(offsetof(struct isp32_isp_params_cfg,meas.rawae3)==0x481,"AE3 offset");
_Static_assert(offsetof(struct isp32_isp_params_cfg,meas.rawhist0)==0x4af,"histogram0 offset");
_Static_assert(offsetof(struct isp32_isp_params_cfg,meas.rawhist1)==0x4d8,"histogram1 offset");
_Static_assert(offsetof(struct isp32_isp_params_cfg,meas.rawhist2)==0x5ca,"histogram2 offset");
_Static_assert(offsetof(struct isp32_isp_params_cfg,meas.rawhist3)==0x6bc,"histogram3 offset");
_Static_assert((ISP32_MODULE_RAWAE0|ISP32_MODULE_RAWAE1|ISP32_MODULE_RAWAE2|ISP32_MODULE_RAWAE3|ISP2X_MODULE_YUVAE)==0x3c4000,"native AE mask including inherited bit");
_Static_assert((ISP32_MODULE_RAWHIST0|ISP32_MODULE_RAWHIST1|ISP32_MODULE_RAWHIST2|ISP32_MODULE_RAWHIST3|ISP2X_MODULE_SIHST)==0x7800008,"native histogram mask including inherited bit");
_Static_assert(sizeof(struct isp32_rawawb_meas_cfg)==807,"AWB measurement bytes");
_Static_assert(offsetof(struct isp32_isp_params_cfg,meas.rawawb)==0xf4,"AWB measurement offset");
_Static_assert(ISP32_MODULE_RAWAWB==(1ULL<<22),"AWB measurement mask");
_Static_assert(offsetof(struct isp32_rawawb_meas_cfg,bnr2awb_sel)==2,"AWB preserved BNR selector");
_Static_assert(offsetof(struct isp32_rawawb_meas_cfg,wp_blk_wei_w)==0x61,"AWB weights");
_Static_assert(offsetof(struct isp32_rawawb_meas_cfg,bls2_val)==799,"AWB black-level tail");
#include <linux/rkcif-config.h>
_Static_assert(VIDIOC_SUBDEV_G_SELECTION==0xc040563d,"get crop bounds ioctl");
_Static_assert(V4L2_SEL_TGT_CROP_BOUNDS==2,"crop bounds target");
_Static_assert(MEDIA_IOC_ENUM_ENTITIES==0xc1007c01,"media entity query");
_Static_assert(MEDIA_IOC_SETUP_LINK==0xc0347c03,"media setup link ioctl");
_Static_assert(VIDIOC_S_FMT==0xc0cc5605,"ARM32 set video format");
_Static_assert(VIDIOC_QUERYCAP==0x80685600,"video capability request");
_Static_assert(V4L2_BUF_TYPE_VIDEO_OUTPUT==2 && V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE==10,"raw RX types");
_Static_assert(V4L2_FIELD_NONE==1,"raw no-field selector");
_Static_assert(RKCIF_CMD_SET_CSI_MEMORY_MODE==0x400456c1,"CIF high-alignment ioctl");
_Static_assert(RKISP_CMD_SET_CSI_MEMORY_MODE==0x40045725,"ISP high-alignment ioctl");
_Static_assert(CSI_LVDS_MEM_WORD_HIGH_ALIGN==2 && CSI_MEM_WORD_BIG_ALIGN==2,"paired high-alignment enum");

/* RawStreamProcUnit linear per-frame trigger payload. */
_Static_assert(sizeof(struct isp2x_csi_trigger)==28,"readback trigger bytes");
_Static_assert(offsetof(struct isp2x_csi_trigger,sof_timestamp)==0,"SOF timestamp offset");
_Static_assert(offsetof(struct isp2x_csi_trigger,frame_timestamp)==8,"frame timestamp offset");
_Static_assert(offsetof(struct isp2x_csi_trigger,frame_id)==16,"trigger frame offset");
_Static_assert(offsetof(struct isp2x_csi_trigger,times)==20,"trigger times offset");
_Static_assert(offsetof(struct isp2x_csi_trigger,mode)==24,"trigger mode offset");
_Static_assert(T_START_X1==16,"linear trigger mode");
_Static_assert(RKISP_CMD_TRIGGER_READ_BACK==0x401c56c0,"readback trigger ioctl");
_Static_assert(sizeof(struct v4l2_exportbuffer)==64,"raw export buffer bytes");
_Static_assert(offsetof(struct v4l2_exportbuffer,fd)==16,"raw export fd offset");
_Static_assert(VIDIOC_EXPBUF==0xc0405610,"raw export ioctl");
_Static_assert(V4L2_MEMORY_DMABUF==4,"raw import memory mode");
_Static_assert(V4L2_PIX_FMT_SBGGR10==0x30314742 && V4L2_PIX_FMT_SGBRG10==0x30314247 && V4L2_PIX_FMT_SGRBG10==0x30314142 && V4L2_PIX_FMT_SRGGB10==0x30314752,"RAW10 formats");
_Static_assert(V4L2_EVENT_FRAME_SYNC==4,"SOF event type");
_Static_assert(offsetof(struct v4l2_event,u.frame_sync.frame_sequence)==8,"SOF frame ID");
_Static_assert(offsetof(struct v4l2_event,timestamp)==80,"SOF old-time timestamp");
_Static_assert(offsetof(struct v4l2_event,sequence)==76,"event sequence differs from frame ID");
_Static_assert(sizeof(struct v4l2_event)==128,"SOF event bytes");
_Static_assert(VIDIOC_SUBSCRIBE_EVENT==0x4020565a && VIDIOC_DQEVENT==0x80805659,"SOF ioctls");
_Static_assert(offsetof(struct isp32_stat,rawae1_0)==0x390,"linear AE1 packed grid");
_Static_assert(offsetof(struct isp32_stat,rawae1_1)==0xb98,"linear AE1 subwindow sums");
_Static_assert(offsetof(struct isp32_stat,rawhist1)==0x1400,"linear AE1 histogram");
_Static_assert(sizeof(struct isp32_rawaebig_stat1)==48,"AE RGB sums record");
_Static_assert(offsetof(struct isp32_rawaebig_stat1,sumg)==16 && offsetof(struct isp32_rawaebig_stat1,sumb)==32,"AE green/blue sum arrays");
