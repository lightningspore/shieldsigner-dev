// SPDX-License-Identifier: MIT
// In-process port of the existing locked SeedSigner LVGL screen library.
// No wallet logic, GPIO policy, Linux subprocess/pipe or filesystem transport.
#include "lvgl.h"
#include "src/misc/cache/instance/lv_image_cache.h"
#include "seedsigner.h"
#include "registry.h"
#include "gui_constants.h"
#include "input_profile.h"
#include "overlay_manager.h"
#include "nul_text.h"
#include "camera_preview_overlay.h"
#include "screen_scaffold.h"
#include <array>
#include <new>
#include <stdexcept>
#include <cstring>
#include <cstdlib>
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
static unsigned event_length=0;
static bool passphrase_screen=false,qr_screen=false;
static uint32_t qr_exit_key=0;
static char event_text[256]={0},error[256]={0};
static bool io_error=false,initialized=false;
static void copy_text(char *out,const char *value){
    if(!value)value="";size_t n=strlen(value);if(n>255)n=255;
    memcpy(out,value,n);out[n]=0;
}
// Same actual widget snapshot used by the existing native Linux host. Preserve
// NUL bytes and text-at-Back; no selected result or text is synthesized.
static lv_obj_t *find_textarea(lv_obj_t *node){
    if(lv_obj_check_type(node,&lv_textarea_class))return node;
    for(uint32_t i=0;i<lv_obj_get_child_count(node);++i){
        if(auto *found=find_textarea(lv_obj_get_child(node,i)))return found;
    }
    return nullptr;
}
static void text_event(uint32_t kind,uint32_t value,const char *text,size_t length){
    if(length>=sizeof(event_text)){
        event_kind=0;event_length=0;io_error=true;
        copy_text(error,"Native text event exceeds current255-byte limit");return;
    }
    event_kind=kind;event_value=value;event_length=length;
    if(length)memcpy(event_text,text,length);event_text[length]=0;
}
static void passphrase_event(bool back){
    auto *area=find_textarea(lv_screen_active());
    if(!area){event_kind=0;io_error=true;copy_text(error,"Passphrase widget missing");return;}
    auto raw=nul_result(area);
    text_event(back?6:2,back?1:0,raw.data(),raw.size());
}
extern "C" void seedsigner_lvgl_on_button_selected(uint32_t index,const char*){
    if(qr_screen && index==SEEDSIGNER_RET_BACK_BUTTON)qr_exit_key=pressed?key:0;
    if(passphrase_screen && index==SEEDSIGNER_RET_BACK_BUTTON){passphrase_event(true);return;}
    event_kind=1;event_value=index;event_length=0;
}
extern "C" void seedsigner_lvgl_on_text_entered(const char *text){
    if(passphrase_screen){passphrase_event(false);return;}
    text_event(2,0,text?text:"",text?strlen(text):0);
}
extern "C" void seedsigner_lvgl_on_aux_key(const char *text){event_kind=3;copy_text(event_text,text);event_length=strlen(event_text);}
extern "C" void seedsigner_lvgl_on_qr_brightness(uint8_t value){event_kind=4;event_value=value;event_length=0;}
extern "C" void seedsigner_lvgl_on_qr_density(uint8_t value){event_kind=5;event_value=value;event_length=0;}
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
        error[0]=0;io_error=false;event_kind=0;event_length=0;
        volatile char *old_text=event_text;for(size_t i=0;i<sizeof(event_text);++i)old_text[i]=0;
        // Same genuine locked screen registry as the existing native host.
        // Registration is availability, not per-screen app-flow qualification.
        const ScreenEntry *entry=nullptr;
        for(const auto &candidate:registry)if(!strcmp(name,candidate.name)){entry=&candidate;break;}
        if(!entry){copy_text(error,"Unknown native screen builder");return -1;}
        entry->build((void*)config);
        passphrase_screen=!strcmp(name,"seed_add_passphrase_screen");
        qr_screen=!strcmp(name,"qr_display_screen");qr_exit_key=0;
        // Settle LVGL reset/group reassignment while input is released, as the
        // existing native host does before acknowledging a new screen.
        pressed=false;lv_indev_read(keypad);
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
extern "C" unsigned bm_nativeui_event_length(){return event_length;}
extern "C" void bm_nativeui_consume_event(){
    event_kind=0;event_value=0;event_length=0;
    volatile char *bytes=event_text;for(size_t i=0;i<sizeof(event_text);++i)bytes[i]=0;
}

extern "C" uint32_t bm_nativeui_screen_count(){return sizeof(registry)/sizeof(registry[0]);}
extern "C" const char *bm_nativeui_screen_name(uint32_t index){return index<bm_nativeui_screen_count()?registry[index].name:nullptr;}

// Real upstream cooperative overlays, owned by the same foreground LVGL loop.
extern "C" int bm_nativeui_overlay_control(unsigned operation,unsigned value){
    if(!initialized)return -1;
    try {
        switch(operation){
        case 0: overlay_manager_set_screensaver_timeout(value);break;
        case 1: overlay_manager_show_screensaver();break;
        case 2: overlay_manager_dismiss_screensaver();break;
        case 3: lv_display_trigger_activity(display);break;
        case 4: return overlay_manager_is_screensaver_active()?1:0;
        case 5: toast_overlay_dismiss();break;
        case 6: return toast_overlay_is_active()?1:0;
        default: copy_text(error,"Unknown overlay operation");return -1;
        }
        lv_timer_handler();lv_refr_now(display);return io_error?-1:0;
    }catch(const std::exception &e){copy_text(error,e.what());return -1;}
    catch(...){copy_text(error,"Native overlay failure");return -1;}
}
extern "C" int bm_nativeui_toast(const char *text,const char *icon,unsigned outline,unsigned font,unsigned duration){
    if(!initialized)return -1;
    try {
        if(!text||strlen(text)>255||(icon&&strlen(icon)>15)){copy_text(error,"Toast text exceeds reviewed bound");return -1;}
        if(overlay_manager_is_screensaver_active())overlay_manager_dismiss_screensaver();
        toast_overlay_spec_t spec{ text,icon&&*icon?icon:nullptr,outline,font,duration };
        toast_overlay_show(&spec);lv_timer_handler();lv_refr_now(display);return io_error?-1:0;
    }catch(const std::exception &e){copy_text(error,e.what());return -1;}
    catch(...){copy_text(error,"Native toast failure");return -1;}
}

// Reachable only from the opt-in diagnostic Rust probe; normal builds remove it.
extern "C" void bm_nativeui_abort_probe(){std::abort();}

// Camera and chrome share the real LVGL compositing/flush path. This buffer is
// owned by the surface, never aliases camera DMA or the output shadow, and is
// wiped before release. Original overlay widgets own instruction/progress UI.
extern "C" int bm_ui_scan_convert(const uint8_t*,size_t,uint8_t*,size_t);
namespace {
struct scan_surface_t {
    lv_obj_t *root=nullptr,*image=nullptr;
    camera_preview_overlay_t *overlay=nullptr;
    lv_image_dsc_t descriptor{};
    std::array<uint8_t,240*240*2> rgb{};
    uint32_t count=0,progress=0,status=0;
    bool scanning=false;
    ~scan_surface_t(){volatile uint8_t *p=rgb.data();for(size_t i=0;i<rgb.size();++i)p[i]=0;}
};
scan_surface_t *scan_surface=nullptr;
void scan_surface_deleted(lv_event_t *event){
    auto *context=static_cast<scan_surface_t*>(lv_event_get_user_data(event));
    if(scan_surface==context)scan_surface=nullptr;
    if(context->overlay)camera_preview_overlay_destroy(context->overlay);
    // Image source points into context, so delete the child/cache while it lives.
    if(context->image){lv_image_cache_drop(&context->descriptor);lv_obj_delete(context->image);}
    delete context;
}
void scan_refresh(){
    lv_timer_handler();lv_refr_now(display);
}
}
extern "C" int bm_nativeui_scan_end();
extern "C" int bm_nativeui_blank();
extern "C" int bm_nativeui_scan_begin(const char *instructions){
    if(!initialized){copy_text(error,"Initialize UI first");return -1;}
    if(scan_surface){copy_text(error,"Scan surface already active");return -1;}
    scan_surface_t *context=nullptr;
    try {
        error[0]=0;io_error=false;
        context=new scan_surface_t;
        context->root=lv_obj_create(nullptr);
        if(!context->root)throw std::bad_alloc();
        lv_obj_add_event_cb(context->root,scan_surface_deleted,LV_EVENT_DELETE,context);
        lv_obj_set_style_bg_color(context->root,lv_color_black(),LV_PART_MAIN);
        lv_obj_set_style_bg_opa(context->root,LV_OPA_COVER,LV_PART_MAIN);
        lv_obj_set_style_pad_all(context->root,0,LV_PART_MAIN);
        lv_obj_set_style_border_width(context->root,0,LV_PART_MAIN);
        lv_obj_remove_flag(context->root,LV_OBJ_FLAG_SCROLLABLE);
        lv_obj_add_flag(context->root,SS_OBJ_FLAG_NO_SCREENSAVER);
        auto &d=context->descriptor;
        d.header.magic=LV_IMAGE_HEADER_MAGIC;d.header.cf=LV_COLOR_FORMAT_RGB565;
        d.header.w=240;d.header.h=240;d.header.stride=480;
        d.data_size=context->rgb.size();d.data=context->rgb.data();
        context->image=lv_image_create(context->root);
        if(!context->image)throw std::bad_alloc();
        lv_image_set_src(context->image,&d);lv_obj_set_pos(context->image,0,0);
        camera_preview_overlay_spec_t spec{};
        spec.instructions_text=instructions;spec.square_w=240;spec.square_h=240;
        spec.frame_status=CAMERA_OVERLAY_FRAME_MISS;spec.just_decoded_index=-1;
        context->overlay=camera_preview_overlay_create(context->root,&spec);
        if(!context->overlay)throw std::bad_alloc();
        scan_surface=context;passphrase_screen=false;qr_screen=false;qr_exit_key=0;bm_nativeui_consume_event();
        load_screen_and_cleanup_previous(context->root);
        pressed=false;lv_indev_read(keypad);scan_refresh();
        if(io_error)throw std::runtime_error("Scan display flush failed");
        return 0;
    }catch(const std::exception &e){copy_text(error,e.what());}
    catch(...){copy_text(error,"Native scan initialization failed");}
    if(context){
        char saved[256];memcpy(saved,error,sizeof(saved));
        if(context->root && lv_screen_active()==context->root)bm_nativeui_scan_end();
        else if(context->root)lv_obj_delete(context->root);else delete context;
        memcpy(error,saved,sizeof(saved));
    }
    return -1;
}
extern "C" int bm_nativeui_scan_frame(const uint8_t *frame,size_t length){
    if(!scan_surface){copy_text(error,"Begin scan surface first");return -1;}
    try {
        if(bm_ui_scan_convert(frame,length,scan_surface->rgb.data(),scan_surface->rgb.size())<0){copy_text(error,"Invalid scan NV12 frame");return -1;}
        ++scan_surface->count;
        lv_obj_invalidate(scan_surface->image);scan_refresh();
        if(io_error){copy_text(error,"Scan frame flush failed");return -1;}
        return 0;
    }catch(const std::exception &e){copy_text(error,e.what());return -1;}
    catch(...){copy_text(error,"Native scan frame failed");return -1;}
}
extern "C" int bm_nativeui_scan_status(unsigned percent,unsigned status,int scanning){
    if(!scan_surface){copy_text(error,"Begin scan surface first");return -1;}
    if(percent>100||status>3){copy_text(error,"Invalid scan progress/status");return -1;}
    try {
        if(scanning)camera_preview_overlay_set_progress(scan_surface->overlay,percent,static_cast<camera_overlay_frame_status_t>(status));
        else camera_preview_overlay_set_scanning(scan_surface->overlay,false);
        scan_surface->progress=percent;scan_surface->status=status;scan_surface->scanning=scanning!=0;
        scan_refresh();return io_error?-1:0;
    }catch(const std::exception &e){copy_text(error,e.what());return -1;}
    catch(...){copy_text(error,"Native scan progress failed");return -1;}
}
extern "C" int bm_nativeui_scan_end(){return scan_surface?bm_nativeui_blank():0;}
extern "C" int bm_nativeui_blank(){
    if(!initialized){copy_text(error,"Initialize UI first");return -1;}
    try {
        auto *blank=lv_obj_create(nullptr);
        if(!blank)throw std::bad_alloc();
        lv_obj_set_style_bg_color(blank,lv_color_black(),LV_PART_MAIN);
        lv_obj_set_style_bg_opa(blank,LV_OPA_COVER,LV_PART_MAIN);
        lv_obj_set_style_border_width(blank,0,LV_PART_MAIN);
        load_screen_and_cleanup_previous(blank);passphrase_screen=false;qr_screen=false;qr_exit_key=0;bm_nativeui_consume_event();
        scan_refresh();return io_error?-1:0;
    }catch(const std::exception &e){copy_text(error,e.what());return -1;}
    catch(...){copy_text(error,"Native scan teardown failed");return -1;}
}
extern "C" unsigned bm_nativeui_scan_stat(unsigned field){
    if(!scan_surface)return 0;
    switch(field){case 0:return 1;case 1:return scan_surface->count;case 2:return scan_surface->progress;case 3:return scan_surface->status;case 4:return scan_surface->scanning;default:return 0;}
}

extern "C" int bm_nativeui_address_progress(const char *text){
    if(!initialized){copy_text(error,"Initialize UI first");return -1;}
    try {
        error[0]=0;io_error=false;
        seed_address_verification_set_progress(text);scan_refresh();
        if(io_error){copy_text(error,"Address progress flush failed");return -1;}
        return 0;
    }catch(const std::exception &e){copy_text(error,e.what());return -1;}
    catch(...){copy_text(error,"Native address progress failed");return -1;}
}


// Original QR host-push APIs. The native screen copies/encodes the borrowed frame
// synchronously, owns its qrcodegen buffers and releases them on root deletion.
extern "C" int bm_nativeui_qr_frame(const uint8_t *bytes,size_t length){
    if(!initialized||!qr_screen){copy_text(error,"Display QR screen first");return -1;}
    if(!bytes||!length||length>512){copy_text(error,"QR frame exceeds reviewed512-byte bound");return -1;}
    try {
        error[0]=0;io_error=false;
        qr_display_set_frame(bytes,length);scan_refresh();
        if(io_error){copy_text(error,"QR frame flush failed");return -1;}
        return 0;
    }catch(const std::exception &e){copy_text(error,e.what());return -1;}
    catch(...){copy_text(error,"Native QR frame failed");return -1;}
}
extern "C" int bm_nativeui_qr_tip_active(){return initialized&&qr_screen&&qr_display_is_tip_active()?1:0;}
extern "C" uint32_t bm_nativeui_qr_exit_key(){return qr_exit_key;}

// Same scaffold body selection as the existing Linux native host: the tallest
// direct scrollable child is the content body, not the shorter top navigation.
static lv_obj_t *native_scroll_body(){
    auto *screen=lv_screen_active();if(!screen)return nullptr;
    lv_obj_t *best=nullptr;int height=-1;
    for(uint32_t i=0;i<lv_obj_get_child_count(screen);++i){
        auto *child=lv_obj_get_child(screen,i);
        if(lv_obj_has_flag(child,LV_OBJ_FLAG_SCROLLABLE)&&lv_obj_get_height(child)>height){best=child;height=lv_obj_get_height(child);}
    }
    return best;
}
extern "C" int bm_nativeui_scroll_y(){auto *body=initialized?native_scroll_body():nullptr;return body?lv_obj_get_scroll_y(body):0;}
extern "C" int bm_nativeui_scroll_to_y(int value){
    if(!initialized){copy_text(error,"Initialize UI first");return -1;}
    try {
        error[0]=0;io_error=false;
        auto *body=native_scroll_body();
        if(body)lv_obj_scroll_to_y(body,value,LV_ANIM_OFF);
        scan_refresh();
        if(io_error){copy_text(error,"Native scroll flush failed");return -1;}
        return 0;
    }catch(const std::exception &e){copy_text(error,e.what());return -1;}
    catch(...){copy_text(error,"Native scroll restore failed");return -1;}
}
