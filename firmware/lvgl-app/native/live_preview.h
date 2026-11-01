#pragma once
#include "lvgl.h"
#include "camera_preview_overlay.h"
#include "screen_scaffold.h"
#include "src/misc/cache/instance/lv_image_cache.h"
#include <cstdint>
#include <cstring>
#include <stdexcept>
static uint8_t live_pixels[240*180*3];
static bool live_pixels_dirty=false;
static lv_image_dsc_t live_descriptor;
static lv_obj_t *live_image=nullptr;
static lv_obj_t *live_caption=nullptr;
static camera_preview_overlay_t *live_overlay=nullptr;
static void stop_live_overlay(){
 if(live_overlay){camera_preview_overlay_destroy(live_overlay);live_overlay=nullptr;}
 live_caption=nullptr;live_image=nullptr;
 // BSS starts zeroed. Touch preview pages only after receiving actual pixels.
 if(live_pixels_dirty){std::memset(live_pixels,0,sizeof(live_pixels));live_pixels_dirty=false;}
}
static void start_live_preview(const char *instructions){
 stop_live_overlay();
 auto *root=lv_obj_create(nullptr);lv_obj_set_style_bg_color(root,lv_color_black(),0);lv_obj_remove_flag(root,LV_OBJ_FLAG_SCROLLABLE);
 live_image=lv_image_create(root);
 std::memset(&live_descriptor,0,sizeof(live_descriptor));
 live_descriptor.header.magic=LV_IMAGE_HEADER_MAGIC;live_descriptor.header.cf=LV_COLOR_FORMAT_RGB888;
 live_descriptor.header.w=240;live_descriptor.header.h=180;live_descriptor.header.stride=720;
 live_descriptor.data_size=sizeof(live_pixels);live_descriptor.data=live_pixels;
 lv_image_set_src(live_image,&live_descriptor);lv_obj_center(live_image);
 camera_preview_overlay_spec_t spec={};spec.instructions_text=instructions;spec.square_w=240;spec.square_h=240;
 live_overlay=camera_preview_overlay_create(root,&spec);
 live_caption=lv_label_create(root);lv_label_set_text(live_caption,"");lv_obj_set_pos(live_caption,8,8);lv_obj_set_style_text_font(live_caption,&BODY_FONT,0);
 apply_screensaver_policy(root,nlohmann::json::object(),false);
 load_screen_and_cleanup_previous(root);
}
static void update_live_preview(const uint8_t *rgb,size_t size,int width,int height,int percent,int status){
 if(percent<0||percent>100||status<0||status>3)throw std::runtime_error("Invalid preview progress");
 if(!live_image || !live_overlay)throw std::runtime_error("No active live preview");
 if(!((width==240&&height==180)||(width==180&&height==240)) || size!=sizeof(live_pixels))throw std::runtime_error("Invalid preview dimensions");
 // LVGL RGB888 stores bytes as B,G,R; the transport accepts ordinary R,G,B.
 live_pixels_dirty=true;
 for(size_t i=0;i<size;i+=3){live_pixels[i]=rgb[i+2];live_pixels[i+1]=rgb[i+1];live_pixels[i+2]=rgb[i];}
 live_descriptor.header.w=width;live_descriptor.header.h=height;live_descriptor.header.stride=width*3;
 lv_image_cache_drop(&live_descriptor);lv_image_set_src(live_image,&live_descriptor);lv_obj_center(live_image);lv_obj_invalidate(live_image);
 if(percent>0)camera_preview_overlay_set_progress(live_overlay,percent,(camera_overlay_frame_status_t)status);
 else camera_preview_overlay_set_scanning(live_overlay,false);
}

static void update_live_caption(const std::string &text,int level){
 if(!live_caption || level<0 || level>2 || text.size()>256)throw std::runtime_error("Invalid live caption");
 lv_label_set_text(live_caption,text.c_str());
 lv_obj_set_style_text_color(live_caption,lv_color_hex(level==0?0xff4444:level==1?0xffaa00:0x55dd55),0);
 lv_obj_set_style_bg_color(live_caption,lv_color_black(),0);lv_obj_set_style_bg_opa(live_caption,LV_OPA_COVER,0);
}
