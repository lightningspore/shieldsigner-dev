// SPDX-License-Identifier: MIT
#include "py/runtime.h"
#include "py/mperrno.h"
extern int bm_camera_init(void);
extern int bm_camera_capture(void);
extern int bm_camera_setting(int,int);
static mp_obj_t camera_init(void){if(bm_camera_init()<0)mp_raise_OSError(MP_EIO);return mp_const_none;}
static MP_DEFINE_CONST_FUN_OBJ_0(camera_init_obj,camera_init);
static mp_obj_t camera_capture(void){if(bm_camera_capture()<0)mp_raise_OSError(MP_EIO);return mp_obj_new_memoryview('B',640*480*3/2,(void *)0x03800000);}
static MP_DEFINE_CONST_FUN_OBJ_0(camera_capture_obj,camera_capture);
static mp_obj_t camera_settings(size_t n,const mp_obj_t *args,mp_map_t *kwargs){
    static const mp_arg_t allowed[]={
        {MP_QSTR_ae_target,MP_ARG_KW_ONLY|MP_ARG_INT,{.u_int=-1}},
        {MP_QSTR_exposure_seed,MP_ARG_KW_ONLY|MP_ARG_INT,{.u_int=-1}}};
    mp_arg_val_t v[2];mp_arg_parse_all(n,args,kwargs,2,allowed,v);
    if(v[0].u_int!=-1&&v[0].u_int!=0&&(v[0].u_int<8||v[0].u_int>200))mp_raise_ValueError(MP_ERROR_TEXT("ae_target must be0 or8..200"));
    if(v[1].u_int!=-1&&(v[1].u_int<1||v[1].u_int>1352))mp_raise_ValueError(MP_ERROR_TEXT("exposure_seed must be1..1352"));
    for(int i=0;i<2;i++)if(v[i].u_int!=-1&&bm_camera_setting(i,v[i].u_int)<0)mp_raise_ValueError(MP_ERROR_TEXT("invalid camera setting"));
    mp_obj_t result=mp_obj_new_dict(0);
    mp_obj_dict_store(result,MP_OBJ_NEW_QSTR(MP_QSTR_width),mp_obj_new_int(640));
    mp_obj_dict_store(result,MP_OBJ_NEW_QSTR(MP_QSTR_height),mp_obj_new_int(480));
    mp_obj_dict_store(result,MP_OBJ_NEW_QSTR(MP_QSTR_format),mp_obj_new_str("NV12",4));
    mp_obj_dict_store(result,MP_OBJ_NEW_QSTR(MP_QSTR_ae_target),mp_obj_new_int(bm_camera_setting(0,-1)));
    mp_obj_dict_store(result,MP_OBJ_NEW_QSTR(MP_QSTR_exposure_seed),mp_obj_new_int(bm_camera_setting(1,-1)));
    mp_obj_dict_store(result,MP_OBJ_NEW_QSTR(MP_QSTR_exposure_lines),mp_obj_new_int(bm_camera_setting(2,-1)));
    mp_obj_dict_store(result,MP_OBJ_NEW_QSTR(MP_QSTR_gain_code),mp_obj_new_int(bm_camera_setting(3,-1)));
    mp_obj_dict_store(result,MP_OBJ_NEW_QSTR(MP_QSTR_rust_heap_bytes),mp_obj_new_int(bm_camera_setting(4,-1)));
    return result;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(camera_settings_obj,0,camera_settings);
static const mp_rom_map_elem_t camera_globals_table[]={
    {MP_ROM_QSTR(MP_QSTR___name__),MP_ROM_QSTR(MP_QSTR_camera)},
    {MP_ROM_QSTR(MP_QSTR_init),MP_ROM_PTR(&camera_init_obj)},
    {MP_ROM_QSTR(MP_QSTR_capture),MP_ROM_PTR(&camera_capture_obj)},
    {MP_ROM_QSTR(MP_QSTR_settings),MP_ROM_PTR(&camera_settings_obj)}};
static MP_DEFINE_CONST_DICT(camera_globals,camera_globals_table);
const mp_obj_module_t camera_module={.base={&mp_type_module},.globals=(mp_obj_dict_t *)&camera_globals};
MP_REGISTER_MODULE(MP_QSTR_camera,camera_module);
