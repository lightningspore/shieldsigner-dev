// SPDX-License-Identifier: MIT
// In-process port of the existing locked SeedSigner LVGL screen library.
// No wallet logic, GPIO policy, Linux subprocess/pipe or filesystem transport.
#include "lvgl.h"
#include "seedsigner.h"
#include "gui_constants.h"
#include "input_profile.h"
#include "overlay_manager.h"
#include <cstring>
#include <exception>
#include <string>
extern "C" uint32_t bm_ticks_ms();
extern "C" int bm_ui_flush(unsigned,unsigned,unsigned,unsigned,const uint8_t*,unsigned);
extern "C" void bm_ui_fatal();
static lv_display_t *display=nullptr;
static lv_indev_t *keypad=nullptr;
static uint8_t pixels[240*20*2] __attribute__((aligned(16)));
static uint32_t key=LV_KEY_ENTER;
static bool pressed=false;
static uint32_t event_kind=0,event_value=0,frames=0,flushes=0;
static char event_text[256]={0},error[256]={0};
static bool io_error=false,initialized=false;
static void copy_text(char *out,const char *value){
    if(!value)value="";size_t n=strlen(value);if(n>255)n=255;
    memcpy(out,value,n);out[n]=0;
}
extern "C" void seedsigner_lvgl_on_button_selected(uint32_t index,const char*){event_kind=1;event_value=index;}
extern "C" void seedsigner_lvgl_on_text_entered(const char *text){event_kind=2;copy_text(event_text,text);}
extern "C" void seedsigner_lvgl_on_aux_key(const char *text){event_kind=3;copy_text(event_text,text);}
extern "C" void seedsigner_lvgl_on_qr_brightness(uint8_t value){event_kind=4;event_value=value;}
extern "C" void seedsigner_lvgl_on_qr_density(uint8_t value){event_kind=5;event_value=value;}
static void flush(lv_display_t *d,const lv_area_t *area,uint8_t *bytes){
    const unsigned w=area->x2-area->x1+1,h=area->y2-area->y1+1;
    lv_draw_sw_rgb565_swap(bytes,w*h);
    if(bm_ui_flush(area->x1,area->y1,w,h,bytes,w*h*2)<0)io_error=true;
    ++flushes;if(lv_display_flush_is_last(d))++frames;
    lv_display_flush_ready(d);
}
static void read_input(lv_indev_t*,lv_indev_data_t *data){
    data->key=key;data->state=pressed?LV_INDEV_STATE_PRESSED:LV_INDEV_STATE_RELEASED;
}
extern "C" int bm_nativeui_init(){
    try {
        if(initialized)return 0;
        if(display){copy_text(error,"Partial UI initialization; reset required");return -1;}
        lv_init();lv_tick_set_cb(bm_ticks_ms);set_display(240,240);
        input_profile_set_mode(INPUT_MODE_HARDWARE);
        display=lv_display_create(240,240);
        if(!display){copy_text(error,"Display allocation failed");return -1;}
        lv_display_set_color_format(display,LV_COLOR_FORMAT_RGB565);
        lv_display_set_buffers(display,pixels,nullptr,sizeof(pixels),LV_DISPLAY_RENDER_MODE_PARTIAL);
        lv_display_set_flush_cb(display,flush);
        keypad=lv_indev_create();
        if(!keypad){copy_text(error,"Input allocation failed");return -1;}
        lv_indev_set_type(keypad,LV_INDEV_TYPE_KEYPAD);
        lv_indev_set_read_cb(keypad,read_input);
        overlay_manager_init();overlay_manager_set_screensaver_timeout(0);
        initialized=true;
        return 0;
    }catch(const std::exception &e){copy_text(error,e.what());return -1;}
    catch(...){copy_text(error,"Unknown native UI initialization failure");return -1;}
}
extern "C" int bm_nativeui_render(const char *name,const char *config){
    if(!initialized){copy_text(error,"Initialize UI first");return -1;}
    try {
        error[0]=0;io_error=false;event_kind=0;
        // Staged registry: unknown screens fail explicitly, no fallback drawing.
        if(!strcmp(name,"main_menu_screen"))main_menu_screen((void*)config);
        else {copy_text(error,"Screen not ported into native registry");return -1;}
        lv_timer_handler();lv_refr_now(display);
        if(io_error){copy_text(error,"Display flush failed");return -1;}
        return 0;
    }catch(const std::exception &e){copy_text(error,e.what());return -1;}
    catch(...){copy_text(error,"Unknown native UI screen failure");return -1;}
}
extern "C" int bm_nativeui_key(uint32_t value,int down){
    if(!initialized)return -1;
    try {
        key=value;pressed=down!=0;
        lv_indev_read(keypad);lv_timer_handler();lv_refr_now(display);return io_error?-1:0;
    }catch(const std::exception &e){copy_text(error,e.what());return -1;}
    catch(...){copy_text(error,"Unknown native UI input failure");return -1;}
}
extern "C" int bm_nativeui_tick(){
    if(!initialized)return -1;
    try {lv_timer_handler();return io_error?-1:0;}
    catch(const std::exception &e){copy_text(error,e.what());return -1;}
    catch(...){copy_text(error,"Unknown native UI timer failure");return -1;}
}
extern "C" uint32_t bm_nativeui_stat(uint32_t field){return field==0?frames:field==1?flushes:field==2?event_kind:field==3?event_value:0;}
extern "C" const char *bm_nativeui_error(){return error;}
extern "C" const char *bm_nativeui_event_text(){return event_text;}
extern "C" void bm_nativeui_consume_event(){event_kind=0;event_text[0]=0;}
