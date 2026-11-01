/* Isolated LVGL UI experiment. All wallet data and QR content are public fixtures. */
#include "lvgl.h"
#include "src/misc/cache/instance/lv_image_cache.h"
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <time.h>
#include <stdint.h>
static lv_obj_t *rows[3], *status, *bar, *picture;
static unsigned selected, page, setting=50;
static uint8_t pixels[240*20*2] __attribute__((aligned(8)));
static uint8_t camera[240*160*3];
static lv_image_dsc_t camera_image;
static const char *names[]={"Live camera", "Public link QR", "Display lab"};
static uint32_t ticks(void) { struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec*1000+t.tv_nsec/1000000; }
static void flush(lv_display_t *d,const lv_area_t *a,uint8_t *p) {
 uint16_t h[4]={a->x1,a->y1,a->x2,a->y2};size_t n=(a->x2-a->x1+1)*(a->y2-a->y1+1)*2;
 lv_draw_sw_rgb565_swap(p,n/2);
 if(fwrite(h,1,8,stdout)!=8||fwrite(p,1,n,stdout)!=n||fflush(stdout))_exit(2);
 lv_display_flush_ready(d);
}
static lv_obj_t *label(const char *text,int x,int y) {lv_obj_t *l=lv_label_create(lv_screen_active());lv_label_set_text(l,text);lv_obj_set_pos(l,x,y);return l;}
static void highlight(void) {for(unsigned i=0;i<3;i++){lv_obj_set_style_bg_color(rows[i],lv_color_hex(i==selected?0x54D6B2:0x202B37),0);lv_obj_set_style_text_color(rows[i],lv_color_hex(i==selected?0x08141C:0xE5EEF5),0);}}
static void show(unsigned next) {
 page=next;FILE *f=fopen("/tmp/lvgl-demo-page","w");if(f){fprintf(f,"%u",page);fclose(f);}
 lv_obj_clean(lv_screen_active());picture=NULL;bar=NULL;status=NULL;
 lv_obj_t *title=label(page==0?"ShieldSigner":page==1?"Live camera":page==2?"Public demo QR":"Display lab",12,8);
 lv_obj_set_style_text_font(title,&lv_font_montserrat_20,0);
 if(!page){label("LVGL native UI / Linux",12,35);for(unsigned i=0;i<3;i++){rows[i]=lv_obj_create(lv_screen_active());lv_obj_set_pos(rows[i],12,62+i*43);lv_obj_set_size(rows[i],216,36);lv_obj_set_style_border_width(rows[i],0,0);lv_obj_set_style_radius(rows[i],7,0);lv_obj_remove_flag(rows[i],LV_OBJ_FLAG_SCROLLABLE);lv_obj_t *l=lv_label_create(rows[i]);lv_label_set_text(l,names[i]);lv_obj_center(l);}highlight();label("Up/Down + Press   |   DEMO",12,207);}
 if(page==1){label("Rust ISP + native preview",12,34);picture=lv_image_create(lv_screen_active());lv_obj_set_pos(picture,0,58);lv_image_set_src(picture,&camera_image);status=label("Starting camera...",12,220);}
 if(page==2){lv_obj_t *quiet=lv_obj_create(lv_screen_active());lv_obj_set_pos(quiet,34,35);lv_obj_set_size(quiet,172,172);lv_obj_set_style_bg_color(quiet,lv_color_white(),0);lv_obj_set_style_border_width(quiet,0,0);lv_obj_set_style_radius(quiet,0,0);lv_obj_t *qr=lv_qrcode_create(lv_screen_active());lv_qrcode_set_size(qr,156);lv_qrcode_set_dark_color(qr,lv_color_black());lv_qrcode_set_light_color(qr,lv_color_white());lv_qrcode_update(qr,"https://shieldsigner.dev",23);lv_obj_set_pos(qr,42,43);label("shieldsigner.dev / public",12,204);}
 if(page==3){label("RGB color test",12,38);for(unsigned i=0;i<3;i++){lv_obj_t *o=lv_obj_create(lv_screen_active());lv_obj_set_pos(o,12+i*74,65);lv_obj_set_size(o,68,65);lv_obj_set_style_bg_color(o,lv_color_hex(i==0?0xFF0000:i==1?0x00FF00:0x0000FF),0);lv_obj_set_style_border_width(o,0,0);}bar=lv_bar_create(lv_screen_active());lv_obj_set_pos(bar,12,154);lv_obj_set_size(bar,216,14);lv_bar_set_value(bar,setting,LV_ANIM_OFF);status=label("",12,181);lv_label_set_text_fmt(status,"Test level: %u%%",setting);label("Up/Down adjusts test bar",12,203);}
 if(page && page!=1)label("Left / KEY2: back",12,224);
 fprintf(stderr,"page=%u\n",page);
}
int main(void){
 setvbuf(stdout,NULL,_IONBF,0);fcntl(0,F_SETFL,O_NONBLOCK);lv_init();lv_tick_set_cb(ticks);
 lv_display_t *d=lv_display_create(240,240);lv_display_set_color_format(d,LV_COLOR_FORMAT_RGB565);lv_display_set_buffers(d,pixels,NULL,sizeof(pixels),LV_DISPLAY_RENDER_MODE_PARTIAL);lv_display_set_flush_cb(d,flush);
 lv_obj_set_style_bg_color(lv_screen_active(),lv_color_hex(0x0B1520),0);lv_obj_set_style_text_color(lv_screen_active(),lv_color_hex(0xE5EEF5),0);
 camera_image.header.magic=LV_IMAGE_HEADER_MAGIC;camera_image.header.cf=LV_COLOR_FORMAT_RGB888;camera_image.header.w=240;camera_image.header.h=160;camera_image.header.stride=720;camera_image.data_size=sizeof(camera);camera_image.data=camera;
 show(0);uint32_t last=0;
 for(;;){char k;while(read(0,&k,1)==1){if(k=='q'){show(0);return 0;}if(k=='b')show(0);else if(!page){if(k=='u')selected=(selected+2)%3;if(k=='d')selected=(selected+1)%3;if(k=='p')show(selected+1);else highlight();}else if(page==3&&(k=='u'||k=='d')){if(k=='u'&&setting<100)setting+=5;if(k=='d'&&setting>0)setting-=5;lv_bar_set_value(bar,setting,LV_ANIM_ON);lv_label_set_text_fmt(status,"Test level: %u%%",setting);}fprintf(stderr,"input=%c page=%u selected=%u\n",k,page,selected);}
 uint32_t now=ticks();if(page==1&&now-last>=200){FILE *f=fopen("/tmp/lvgl-camera.rgb","rb");if(f){if(fread(camera,1,sizeof(camera),f)==sizeof(camera)){lv_image_cache_drop(&camera_image);lv_obj_invalidate(picture);lv_label_set_text(status,"LIVE   |   Left: back");}fclose(f);}last=now;}
 lv_timer_handler();usleep(10000);}
}
