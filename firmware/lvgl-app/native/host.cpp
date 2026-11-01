// Isolated host for pinned upstream screens. No wallet logic or GPIO policy.
#include "lvgl.h"
#include "seedsigner.h"
#include "gui_constants.h"
#include "input_profile.h"
#include "overlay_manager.h"
#include "toast_overlay.h"
#include "registry.h"
#include "locale_loader.h"
#include "locale_picker.h"
#include <sys/stat.h>
#include <vector>
#include <nlohmann/json.hpp>
#include <unistd.h>
#include <fcntl.h>
#include <time.h>
#include <cstdio>
#include <cstdint>
#include <string>
#include <stdexcept>
using nlohmann::json;
#include "live_preview.h"
#include "nul_text.h"
static uint8_t pixels[320*20*2] __attribute__((aligned(8)));
static uint32_t key=LV_KEY_ENTER;
static uint64_t toast_token=0;
static bool pressed=false;
static std::string current_screen;
static lv_indev_t *keypad=nullptr;
static lv_obj_t *live_info_label=nullptr;
static lv_obj_t *home_battery_label=nullptr;
static lv_obj_t *home_battery_icon=nullptr;
static lv_obj_t *home_battery_screen=nullptr;
static void find_info_label(lv_obj_t *obj,const std::string &text,int &matches){
 if(lv_obj_check_type(obj,&lv_label_class)&&text==lv_label_get_text(obj)){live_info_label=obj;++matches;}
 for(uint32_t i=0;i<lv_obj_get_child_count(obj);++i)find_info_label(lv_obj_get_child(obj,i),text,matches);
}
// The pinned scaffold creates its scrollable body as a direct screen child.
// Pick its tallest scrollable child; TopNav is shorter and not the body.
static lv_obj_t *body(){
 auto *screen=lv_screen_active();lv_obj_t *best=nullptr;int height=-1;
 for(uint32_t i=0;i<lv_obj_get_child_count(screen);++i){auto *child=lv_obj_get_child(screen,i);if(lv_obj_has_flag(child,LV_OBJ_FLAG_SCROLLABLE)&&lv_obj_get_height(child)>height){best=child;height=lv_obj_get_height(child);}}
 return best;
}
static int scroll_y(){auto *b=body();return b?lv_obj_get_scroll_y(b):0;}
static uint32_t tick(){timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec*1000+t.tv_nsec/1000000;}
static void packet(uint8_t type,const void *data,uint32_t size){
 uint8_t header[8]={'S','L',1,type,uint8_t(size),uint8_t(size>>8),uint8_t(size>>16),uint8_t(size>>24)};
 if(fwrite(header,1,8,stdout)!=8||fwrite(data,1,size,stdout)!=size||fflush(stdout))_exit(2);
}
static void result(const json &j){auto s=j.dump();packet(2,s.data(),s.size());}
static lv_obj_t *find_textarea(lv_obj_t *node){
 if(lv_obj_check_type(node,&lv_textarea_class))return node;
 for(uint32_t i=0;i<lv_obj_get_child_count(node);++i){auto *found=find_textarea(lv_obj_get_child(node,i));if(found)return found;}
 return nullptr;
}
static std::optional<std::string> passphrase_text(){auto *ta=find_textarea(lv_screen_active());return ta?std::optional<std::string>(nul_result(ta)):std::nullopt;}
extern "C" void seedsigner_lvgl_on_button_selected(uint32_t index,const char *){
 if(current_screen=="seed_add_passphrase_screen" && index==SEEDSIGNER_RET_BACK_BUTTON){auto text=passphrase_text();if(!text){result({{"event","error"},{"kind","missing_passphrase_widget"}});return;}result({{"event","passphrase_result"},{"text",*text},{"back",true}});return;}
 if(current_screen=="qr_display_screen"){result({{"event","button_selected"},{"index",index},{"exit_key",key}});return;}
 result({{"event","button_selected"},{"index",index},{"scroll_y",scroll_y()}});
}
extern "C" void seedsigner_lvgl_on_text_entered(const char *text){
 if(current_screen=="seed_add_passphrase_screen"){auto value=passphrase_text();if(!value){result({{"event","error"},{"kind","missing_passphrase_widget"}});return;}result({{"event","passphrase_result"},{"text",*value},{"back",false}});return;}
 result({{"event","text_entered"},{"text",text?text:""}});
}
extern "C" void seedsigner_lvgl_on_aux_key(const char *name){result({{"event","aux_key"},{"key",name?name:""}});}
extern "C" void seedsigner_lvgl_on_qr_brightness(uint8_t n){result({{"event","qr_brightness"},{"value",n}});}
extern "C" void seedsigner_lvgl_on_qr_density(uint8_t n){result({{"event","qr_density"},{"value",n}});}
static void flush(lv_display_t *d,const lv_area_t *a,uint8_t *p){
 size_t n=(a->x2-a->x1+1)*(a->y2-a->y1+1)*2;
 uint8_t body[8+sizeof(pixels)];uint16_t area[4]={uint16_t(a->x1),uint16_t(a->y1),uint16_t(a->x2),uint16_t(a->y2)};
 lv_draw_sw_rgb565_swap(p,n/2);memcpy(body,area,8);memcpy(body+8,p,n);packet(1,body,n+8);if(lv_display_flush_is_last(d))result({{"event","frame_complete"}});lv_display_flush_ready(d);
}
static void read_input(lv_indev_t*,lv_indev_data_t *d){d->key=key;d->state=pressed?LV_INDEV_STATE_PRESSED:LV_INDEV_STATE_RELEASED;}
// Private filesystem provider for pinned, preflight-verified locale assets.
// Bound each read and refuse traversal/symlinks; upstream owns retained copies.
static std::string locale_root;
static std::vector<uint8_t> locale_scratch;
static bool locale_component(const std::string &s){
 if(s.empty()||s.size()>96||s=="."||s=="..")return false;
 for(unsigned char c:s)if(!((c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='_'||c=='.'||c=='-'))return false;
 return true;
}
static bool locale_bytes(const char *locale,const char *file,const uint8_t **bytes,size_t *len,void*){
 if(locale_root.empty()||!locale_component(locale)||!locale_component(file))return false;
 int root=open(locale_root.c_str(),O_RDONLY|O_DIRECTORY|O_NOFOLLOW);if(root<0)return false;
 int dir=openat(root,locale,O_RDONLY|O_DIRECTORY|O_NOFOLLOW);close(root);if(dir<0)return false;
 int fd=openat(dir,file,O_RDONLY|O_NOFOLLOW);close(dir);if(fd<0)return false;
 struct stat st{};if(fstat(fd,&st)||!S_ISREG(st.st_mode)||st.st_size<=0||st.st_size>524288){close(fd);return false;}
 locale_scratch.resize(size_t(st.st_size));size_t offset=0;
 while(offset<locale_scratch.size()){ssize_t n=read(fd,locale_scratch.data()+offset,locale_scratch.size()-offset);if(n<=0){close(fd);return false;}offset+=size_t(n);}
 close(fd);*bytes=locale_scratch.data();*len=locale_scratch.size();return true;
}
static void release_locale_scratch(){std::vector<uint8_t>().swap(locale_scratch);}
static void command(const json &j){
 auto op=j.at("op").get<std::string>();
 if(op=="locale"){
  auto locale=j.at("locale").get<std::string>();
  if(!locale_component(locale))throw std::runtime_error("Invalid locale");
  if(j.contains("root")){
   auto root=j.at("root").get<std::string>();
   if(root.empty()||root[0]!='/'||root.size()>4096||root.find('\0')!=std::string::npos)throw std::runtime_error("Invalid locale root");
   locale_root=root;
   for(const auto &entry:j.at("manifests")){
    auto code=entry.get<std::string>();const uint8_t *bytes=nullptr;size_t len=0;
    if(!locale_bytes(code.c_str(),"manifest.json",&bytes,&len,nullptr)||!ss_register_pack_manifest(reinterpret_cast<const char*>(bytes),len)){release_locale_scratch();throw std::runtime_error("Invalid locale manifest");}
   }
   locale_picker_set_image_provider(locale_bytes,nullptr);
  }
  bool loaded=ss_load_locale(locale.c_str(),locale_bytes,nullptr);release_locale_scratch();
  result({{"event","locale_ready"},{"locale",locale},{"loaded",loaded}});
 }else if(op=="scan"){
  auto text=j.at("instructions").get<std::string>();start_live_preview(text.c_str());current_screen="scan";
  if(keypad)lv_indev_read(keypad);lv_refr_now(nullptr);
  result({{"event","screen_ready"},{"request",j.value("request",0)}});
 }else if(op=="entropy_caption"){
  update_live_caption(j.at("text").get<std::string>(),j.at("level").get<int>());result({{"event","caption_ready"}});
 }else if(op=="toast"){
  auto text=j.at("text").get<std::string>();auto icon=j.value("icon",std::string(""));
  auto outline=j.at("outline").get<std::string>();auto font=j.at("font").get<std::string>();
  auto rgb=[](std::string value){if(value.size()!=7||value[0]!='#')throw std::runtime_error("Invalid toast color");return uint32_t(std::stoul(value.substr(1),nullptr,16));};
  toast_overlay_spec_t spec{};spec.label_text=text.c_str();spec.icon_glyph=icon.c_str();
  spec.outline_color=rgb(outline);spec.font_color=rgb(font);spec.duration_ms=j.at("duration_ms").get<uint32_t>();
  toast_token=j.at("token").get<uint64_t>();overlay_manager_show_toast(&spec);
 }else if(op=="toast_stop"){
  if(j.at("token").get<uint64_t>()==toast_token)toast_overlay_dismiss();
 }else if(op=="activity"){
  lv_display_trigger_activity(nullptr);
 }else if(op=="screensaver_dismiss"){
  overlay_manager_dismiss_screensaver();lv_refr_now(nullptr);
 }else if(op=="screensaver_show"){
  if(!lv_obj_has_flag(lv_screen_active(),SS_OBJ_FLAG_NO_SCREENSAVER))overlay_manager_show_screensaver();
  lv_refr_now(nullptr);
 }else if(op=="overlays"){
  overlay_manager_set_screensaver_timeout(j.at("timeout_ms").get<uint32_t>());
 }else if(op=="overlay_state"){
  result({{"event","overlay_state"},{"toast",toast_overlay_is_active()},{"screensaver",overlay_manager_is_screensaver_active()}});
 }else if(op=="home_battery"){
  if(current_screen!="main_menu_screen")throw std::runtime_error("Home battery inactive");
  bool visible=j.at("visible").get<bool>();
  std::string text;bool low=false;const char *icon=LV_SYMBOL_BATTERY_EMPTY;
  if(visible){
   bool charging=j.at("charging").get<bool>();
   if(!j.at("percent").is_null()){
    int percent=j.at("percent").get<int>();
    if(percent < -1000 || percent > 1000)throw std::runtime_error("Invalid battery percent");
    text=charging?LV_SYMBOL_CHARGE:std::to_string(percent)+"%";low=percent<20;
    icon=percent>=75?LV_SYMBOL_BATTERY_FULL:percent>=50?LV_SYMBOL_BATTERY_2:percent>=25?LV_SYMBOL_BATTERY_1:LV_SYMBOL_BATTERY_EMPTY;
   }else text=charging?LV_SYMBOL_CHARGE:"--%";
  }
  if(!home_battery_label && visible){
   home_battery_icon=lv_label_create(home_battery_screen);
   lv_obj_set_pos(home_battery_icon,EDGE_PADDING,0);
   lv_obj_set_style_text_font(home_battery_icon,&lv_font_montserrat_14,0);
   lv_obj_remove_flag(home_battery_icon,LV_OBJ_FLAG_CLICKABLE);
   home_battery_label=lv_label_create(home_battery_screen);
   lv_obj_set_pos(home_battery_label,EDGE_PADDING+20,0);
   lv_obj_set_style_text_font(home_battery_label,&lv_font_montserrat_14,0);
   lv_obj_remove_flag(home_battery_label,LV_OBJ_FLAG_CLICKABLE);
  }
  if(home_battery_label){
   if(visible)lv_obj_remove_flag(home_battery_label,LV_OBJ_FLAG_HIDDEN);
   else lv_obj_add_flag(home_battery_label,LV_OBJ_FLAG_HIDDEN);
   if(visible)lv_obj_remove_flag(home_battery_icon,LV_OBJ_FLAG_HIDDEN);
   else lv_obj_add_flag(home_battery_icon,LV_OBJ_FLAG_HIDDEN);
   lv_label_set_text(home_battery_icon,icon);
   lv_label_set_text(home_battery_label,text.c_str());
   lv_obj_set_style_text_color(home_battery_icon,lv_color_hex(low?ERROR_COLOR:0xfcfcfc),0);
   lv_obj_set_style_text_color(home_battery_label,lv_color_hex(0xfcfcfc),0);
  }
  lv_refr_now(nullptr);result({{"event","home_battery_updated"}});
 }else if(op=="io_state"){
  if(current_screen!="io_test_screen")throw std::runtime_error("I/O test inactive");
  int state=j.at("state").get<int>();if(state<0||state>2)throw std::runtime_error("Invalid I/O capture state");
  io_test_set_capture_state(static_cast<io_test_capture_state_t>(state));lv_refr_now(nullptr);result({{"event","io_state_ready"}});
 }else if(op=="io_frame"){
  if(current_screen!="io_test_screen")throw std::runtime_error("I/O test inactive");
  int width=0,height=0;io_test_get_camera_plane_dims(&width,&height);
  auto hex=j.at("hex").get<std::string>();if(width!=240||height!=240||hex.size()!=240*240*4)throw std::runtime_error("Invalid I/O frame size");
  auto nibble=[](char c)->uint8_t{if(c>='0'&&c<='9')return c-'0';if(c>='a'&&c<='f')return c-'a'+10;if(c>='A'&&c<='F')return c-'A'+10;throw std::runtime_error("Invalid I/O frame hex");};
  std::vector<uint8_t> data(hex.size()/2);for(size_t i=0;i<data.size();++i)data[i]=(nibble(hex[i*2])<<4)|nibble(hex[i*2+1]);
  io_test_blit_camera(data.data(),data.size());io_test_set_capture_state(IO_TEST_CAPTURE_CAPTURED);lv_refr_now(nullptr);result({{"event","io_frame_ready"}});
 }else if(op=="info_text"){
  if(current_screen!="button_list_screen"||!live_info_label)throw std::runtime_error("Live info inactive");
  auto text=j.at("text").get<std::string>();if(text.empty()||text.size()>4096||text.find('\0')!=std::string::npos)throw std::runtime_error("Invalid live info text");
  auto *container=lv_obj_get_parent(live_info_label);
  while(container&&!lv_obj_has_flag(container,LV_OBJ_FLAG_SCROLLABLE))container=lv_obj_get_parent(container);
  int previous=container?lv_obj_get_scroll_y(container):0;
  lv_label_set_text(live_info_label,text.c_str());lv_obj_update_layout(lv_obj_get_screen(live_info_label));
  if(container)lv_obj_scroll_to_y(container,previous,LV_ANIM_OFF);
  lv_refr_now(nullptr);result({{"event","info_updated"}});
 }else if(op=="address_progress"){
  if(current_screen!="seed_address_verification_screen")throw std::runtime_error("Address search inactive");
  auto text=j.at("text").get<std::string>();if(text.size()>512)throw std::runtime_error("Address progress too long");
  seed_address_verification_set_progress(text.c_str());lv_refr_now(nullptr);
 }else if(op=="qr_state"){
  result({{"event","qr_state"},{"tip_active",qr_display_is_tip_active()}});
 }else if(op=="qr_frame"){
  if(current_screen!="qr_display_screen")throw std::runtime_error("QR screen inactive");
  auto hex=j.at("hex").get<std::string>();if(hex.size()%2 || hex.size()>16384)throw std::runtime_error("Invalid QR frame size");
  std::vector<uint8_t> data(hex.size()/2);
  auto nibble=[](char c)->uint8_t{if(c>='0'&&c<='9')return c-'0';if(c>='a'&&c<='f')return c-'a'+10;if(c>='A'&&c<='F')return c-'A'+10;throw std::runtime_error("Invalid QR frame hex");};
  for(size_t i=0;i<data.size();++i)data[i]=(nibble(hex[i*2])<<4)|nibble(hex[i*2+1]);
  qr_display_set_frame(data.data(),data.size());lv_refr_now(nullptr);result({{"event","qr_frame_ready"}});
 }else if(op=="scan_stop"||op=="clear"){
  live_info_label=nullptr;home_battery_label=nullptr;home_battery_icon=nullptr;home_battery_screen=nullptr;overlay_manager_dismiss_screensaver();stop_live_overlay();auto *black=lv_obj_create(nullptr);lv_obj_set_style_bg_color(black,lv_color_black(),0);load_screen_and_cleanup_previous(black);current_screen="";lv_refr_now(nullptr);result({{"event",op=="clear"?"screen_cleared":"scan_stopped"}});
 }else if(op=="screen"){
  live_info_label=nullptr;home_battery_label=nullptr;home_battery_icon=nullptr;home_battery_screen=nullptr;overlay_manager_dismiss_screensaver();stop_live_overlay();
  auto name=j.at("name").get<std::string>();auto cfg=j.at("config").dump();bool found=false;
  for(const auto &entry:registry)if(name==entry.name){entry.build((void*)cfg.c_str());found=true;break;}
  if(!found)throw std::runtime_error("Unknown screen builder");
  release_locale_scratch();
  current_screen=name;
  if(name=="main_menu_screen")home_battery_screen=lv_screen_active();
  if(j.at("config").value("live_info",false)){
   if(name!="button_list_screen")throw std::runtime_error("Invalid live info builder");
   int matches=0;find_info_label(lv_screen_active(),j.at("config").at("text").get<std::string>(),matches);
   if(matches!=1){live_info_label=nullptr;throw std::runtime_error("Ambiguous live info label");}
  }
  lv_obj_update_layout(lv_screen_active());
  if(j.at("config").contains("initial_scroll_y")){auto *b=body();if(b)lv_obj_scroll_to_y(b,j.at("config").at("initial_scroll_y").get<int>(),LV_ANIM_OFF);}
  // A screen is ready only after its initial pixels and keypad reset settle.
  if(keypad)lv_indev_read(keypad);
  lv_refr_now(nullptr);
  result({{"event","screen_ready"},{"request",j.value("request",0)}});
 }else if(op=="key"){
  key=j.at("key").get<uint32_t>();pressed=j.at("pressed").get<bool>();if(keypad)lv_indev_read(keypad);
 }else if(op=="quit"){lv_deinit();_exit(0);}
 else throw std::runtime_error("Unknown operation");
}
int main(int argc,char **argv){
 int width=240,height=240;
 if(argc!=1){
  if(argc!=5||std::string(argv[1])!="--width"||std::string(argv[3])!="--height"||std::string(argv[4])!="240")return 64;
  auto value=std::string(argv[2]);if(value!="240"&&value!="320")return 64;
  width=value=="320"?320:240;
 }
 setvbuf(stdout,nullptr,_IONBF,0);fcntl(0,F_SETFL,O_NONBLOCK);lv_init();lv_tick_set_cb(tick);set_display(width,height);input_profile_set_mode(INPUT_MODE_HARDWARE);
 auto *d=lv_display_create(width,height);lv_display_set_color_format(d,LV_COLOR_FORMAT_RGB565);lv_display_set_buffers(d,pixels,nullptr,width*20*2,LV_DISPLAY_RENDER_MODE_PARTIAL);lv_display_set_flush_cb(d,flush);
 keypad=lv_indev_create();lv_indev_set_type(keypad,LV_INDEV_TYPE_KEYPAD);lv_indev_set_read_cb(keypad,read_input);
 overlay_manager_init();overlay_manager_set_screensaver_timeout(0);
 result({{"event","ready"},{"protocol",1}});
 std::string pending;char buf[4096];json preview_header;size_t preview_size=0;uint32_t preview_started=0;
 for(;;){if(preview_size && uint32_t(tick()-preview_started)>3000){result({{"event","error"},{"kind","preview_timeout"}});stop_live_overlay();lv_deinit();return 4;}ssize_t count=read(0,buf,sizeof(buf));if(count==0)break;if(count>0)pending.append(buf,count);
  if(pending.size()>1024*1024){result({{"event","error"},{"kind","request_too_large"}});return 3;}
  for(;;){
   if(preview_size){
    if(pending.size()<preview_size)break;
    try{update_live_preview((const uint8_t*)pending.data(),preview_size,preview_header.at("width"),preview_header.at("height"),preview_header.value("percent",0),preview_header.value("status",0));lv_refr_now(nullptr);result({{"event","preview_ready"}});}
    catch(const std::exception &){result({{"event","error"},{"kind","invalid_preview"}});}
    std::fill(pending.begin(),pending.begin()+preview_size,'\0');pending.erase(0,preview_size);preview_size=0;continue;
   }
   size_t end=pending.find('\n');if(end==std::string::npos)break;
   auto line=pending.substr(0,end);pending.erase(0,end+1);
   try{
    auto request=json::parse(line);
    if(request.at("op")=="preview"){
     auto bytes=request.at("bytes").get<size_t>();
     if(bytes!=sizeof(live_pixels)){result({{"event","error"},{"kind","invalid_preview_size"}});stop_live_overlay();lv_deinit();return 5;}
     preview_started=tick();preview_size=bytes;preview_header=std::move(request);
    }else{
     command(request);
     // A preview grows the input accumulator to a whole frame. Once cleared,
     // keep queued bytes but release the no-longer-needed frame capacity.
     if(request.at("op")=="clear"||request.at("op")=="scan_stop")pending.shrink_to_fit();
    }
   }catch(const std::exception &){result({{"event","error"},{"kind","invalid_request"}});}
  }
  lv_timer_handler();
  static bool saver_was_active=false;
  bool saver_active=overlay_manager_is_screensaver_active();
  if(saver_active!=saver_was_active){saver_was_active=saver_active;result({{"event","overlay_changed"},{"screensaver",saver_active}});}
  // Drain available preview bytes without a per-4-KiB sleep. Each iteration
  // still services LVGL timers; only an idle/non-ready read needs backoff.
  if(count<0)usleep(5000);
 }
 stop_live_overlay();lv_deinit();return 0;
}
