// SPDX-License-Identifier: MIT
// Genuine in-process LVGL screens; errors do not fall back to substitute screens.
#include <string.h>
#include "py/runtime.h"
#include "py/objarray.h"
#include "py/objtuple.h"
extern int bm_ui_init(void);
extern uint32_t bm_nativeui_screen_count(void);
extern const char *bm_nativeui_screen_name(uint32_t);
extern unsigned bm_ui_heap_used(void);
extern int bm_nativeui_render(const char *,const char *);
extern int bm_nativeui_key(uint32_t,int);
extern int bm_nativeui_tick(void);
extern uint32_t bm_nativeui_stat(uint32_t);
extern const char *bm_nativeui_error(void);
extern const char *bm_nativeui_event_text(void);
extern void bm_nativeui_consume_event(void);
static void checked(int value){if(value<0)mp_raise_msg_varg(&mp_type_RuntimeError,MP_ERROR_TEXT("Native UI: %s"),bm_nativeui_error());}
static mp_obj_t ui_init(void){checked(bm_ui_init());return mp_const_none;}
static MP_DEFINE_CONST_FUN_OBJ_0(ui_init_obj,ui_init);
static mp_obj_t ui_render(mp_obj_t name,mp_obj_t config){
    checked(bm_nativeui_render(mp_obj_str_get_str(name),mp_obj_str_get_str(config)));return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_2(ui_render_obj,ui_render);
static mp_obj_t ui_key(mp_obj_t key,mp_obj_t down){
    mp_int_t value=mp_obj_get_int(key);
    if(value<0||value>255)mp_raise_ValueError(MP_ERROR_TEXT("Key0..255 required"));
    checked(bm_nativeui_key(value,mp_obj_is_true(down)));return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_2(ui_key_obj,ui_key);
static mp_obj_t ui_tick(void){checked(bm_nativeui_tick());return mp_const_none;}
static MP_DEFINE_CONST_FUN_OBJ_0(ui_tick_obj,ui_tick);
static mp_obj_t ui_framebuffer(void){return mp_obj_new_memoryview('B',240*240*2,(void *)0x02000000);}
static MP_DEFINE_CONST_FUN_OBJ_0(ui_framebuffer_obj,ui_framebuffer);
static mp_obj_t ui_status(void){
    mp_obj_t d=mp_obj_new_dict(4);
    mp_obj_dict_store(d,MP_OBJ_NEW_QSTR(MP_QSTR_frames),mp_obj_new_int_from_uint(bm_nativeui_stat(0)));
    mp_obj_dict_store(d,MP_OBJ_NEW_QSTR(MP_QSTR_flushes),mp_obj_new_int_from_uint(bm_nativeui_stat(1)));
    mp_obj_dict_store(d,MP_OBJ_NEW_QSTR(MP_QSTR_heap_bytes),mp_obj_new_int_from_uint(bm_ui_heap_used()));return d;
}
static MP_DEFINE_CONST_FUN_OBJ_0(ui_status_obj,ui_status);
static mp_obj_t ui_event(void){
    unsigned kind=bm_nativeui_stat(2);if(!kind)return mp_const_none;
    mp_obj_t values[]={mp_obj_new_int_from_uint(kind),mp_obj_new_int_from_uint(bm_nativeui_stat(3)),mp_obj_new_str(bm_nativeui_event_text(),strlen(bm_nativeui_event_text()))};
    mp_obj_t result=mp_obj_new_tuple(3,values);bm_nativeui_consume_event();return result;
}
static MP_DEFINE_CONST_FUN_OBJ_0(ui_event_obj,ui_event);
static mp_obj_t ui_screens(void){
    size_t count=bm_nativeui_screen_count();mp_obj_t result=mp_obj_new_tuple(count,NULL);
    mp_obj_tuple_t *tuple=MP_OBJ_TO_PTR(result);
    for(size_t i=0;i<count;i++){const char *name=bm_nativeui_screen_name(i);tuple->items[i]=mp_obj_new_str(name,strlen(name));}
    return result;
}
static MP_DEFINE_CONST_FUN_OBJ_0(ui_screens_obj,ui_screens);
static const mp_rom_map_elem_t globals_table[]={
    {MP_ROM_QSTR(MP_QSTR___name__),MP_ROM_QSTR(MP_QSTR_ui)},
    {MP_ROM_QSTR(MP_QSTR_screens),MP_ROM_PTR(&ui_screens_obj)},
    {MP_ROM_QSTR(MP_QSTR_init),MP_ROM_PTR(&ui_init_obj)},
    {MP_ROM_QSTR(MP_QSTR_render),MP_ROM_PTR(&ui_render_obj)},
    {MP_ROM_QSTR(MP_QSTR_key),MP_ROM_PTR(&ui_key_obj)},
    {MP_ROM_QSTR(MP_QSTR_tick),MP_ROM_PTR(&ui_tick_obj)},
    {MP_ROM_QSTR(MP_QSTR_framebuffer),MP_ROM_PTR(&ui_framebuffer_obj)},
    {MP_ROM_QSTR(MP_QSTR_status),MP_ROM_PTR(&ui_status_obj)},
    {MP_ROM_QSTR(MP_QSTR_event),MP_ROM_PTR(&ui_event_obj)},
};
static MP_DEFINE_CONST_DICT(globals,globals_table);
const mp_obj_module_t ui_module={.base={&mp_type_module},.globals=(mp_obj_dict_t *)&globals};
MP_REGISTER_MODULE(MP_QSTR_ui,ui_module);
