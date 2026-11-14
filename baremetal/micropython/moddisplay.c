// SPDX-License-Identifier: MIT
// Explicit bench240 hardware API; not a generic GPIO-output escape hatch.
#include <string.h>
#include "py/runtime.h"
#include "py/mperrno.h"
extern int bm_display(uint32_t,uint32_t,uint32_t,uint32_t,uint32_t,const uint8_t *,size_t);
static void checked(int status){if(status<0)mp_raise_OSError(MP_EIO);}
static mp_obj_t display_init(size_t n,const mp_obj_t *args,mp_map_t *kwargs){
    static const mp_arg_t allowed[]={
        {MP_QSTR_profile,MP_ARG_REQUIRED|MP_ARG_OBJ,{.u_obj=MP_OBJ_NULL}},
        {MP_QSTR_software_spi,MP_ARG_KW_ONLY|MP_ARG_BOOL,{.u_bool=false}}};
    mp_arg_val_t v[2];mp_arg_parse_all(n,args,kwargs,2,allowed,v);
    if(strcmp(mp_obj_str_get_str(v[0].u_obj),"bench240"))mp_raise_ValueError(MP_ERROR_TEXT("explicit bench240 profile required"));
    checked(bm_display(0,v[1].u_bool,0,0,0,NULL,0));return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(display_init_obj,1,display_init);
static mp_obj_t display_fill(mp_obj_t color){
    mp_int_t value=mp_obj_get_int(color);if(value<0||value>65535)mp_raise_ValueError(MP_ERROR_TEXT("RGB565 color0..65535 required"));
    checked(bm_display(1,value,0,0,0,NULL,0));return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(display_fill_obj,display_fill);
static mp_obj_t display_blit(size_t n,const mp_obj_t *args){
    (void)n;mp_int_t v[4];for(size_t i=0;i<4;i++)v[i]=mp_obj_get_int(args[i]);
    if(v[0]<0||v[1]<0||v[2]<=0||v[3]<=0||v[0]>240||v[1]>240||v[2]>240||v[3]>240||v[0]+v[2]>240||v[1]+v[3]>240)mp_raise_ValueError(MP_ERROR_TEXT("window outside240x240"));
    mp_buffer_info_t data;mp_get_buffer_raise(args[4],&data,MP_BUFFER_READ);
    if(data.len!=(size_t)(v[2]*v[3]*2))mp_raise_ValueError(MP_ERROR_TEXT("RGB565 big-endian buffer length mismatch"));
    checked(bm_display(2,v[0],v[1],v[2],v[3],data.buf,data.len));return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(display_blit_obj,5,5,display_blit);
static mp_obj_t display_buttons(void){int value=bm_display(3,0,0,0,0,NULL,0);checked(value);return MP_OBJ_NEW_SMALL_INT(value);}
static MP_DEFINE_CONST_FUN_OBJ_0(display_buttons_obj,display_buttons);
static mp_obj_t display_status(void){
    static const qstr names[]={MP_QSTR_gpio_levels,MP_QSTR_gpio_ddr_low,MP_QSTR_gpio_ddr_high,MP_QSTR_mux_b,MP_QSTR_mux_c,MP_QSTR_mux_d,MP_QSTR_pull_b,MP_QSTR_pull_c,MP_QSTR_pull_d,MP_QSTR_spi_mux,MP_QSTR_spi_divisor,MP_QSTR_spi_cr0,MP_QSTR_spi_count,MP_QSTR_software_spi};
    mp_obj_t result=mp_obj_new_dict(0);
    for(size_t i=0;i<14;i++){int v=bm_display(4,i,0,0,0,NULL,0);checked(v);mp_obj_dict_store(result,MP_OBJ_NEW_QSTR(names[i]),mp_obj_new_int_from_uint(v));}
    return result;
}
static MP_DEFINE_CONST_FUN_OBJ_0(display_status_obj,display_status);
static const mp_rom_map_elem_t globals_table[]={
    {MP_ROM_QSTR(MP_QSTR___name__),MP_ROM_QSTR(MP_QSTR_display)},
    {MP_ROM_QSTR(MP_QSTR_init),MP_ROM_PTR(&display_init_obj)},
    {MP_ROM_QSTR(MP_QSTR_fill),MP_ROM_PTR(&display_fill_obj)},
    {MP_ROM_QSTR(MP_QSTR_blit),MP_ROM_PTR(&display_blit_obj)},
    {MP_ROM_QSTR(MP_QSTR_buttons),MP_ROM_PTR(&display_buttons_obj)},
    {MP_ROM_QSTR(MP_QSTR_status),MP_ROM_PTR(&display_status_obj)},
    {MP_ROM_QSTR(MP_QSTR_WIDTH),MP_ROM_INT(240)},
    {MP_ROM_QSTR(MP_QSTR_HEIGHT),MP_ROM_INT(240)}};
static MP_DEFINE_CONST_DICT(globals,globals_table);
const mp_obj_module_t display_module={.base={&mp_type_module},.globals=(mp_obj_dict_t *)&globals};
MP_REGISTER_MODULE(MP_QSTR_display,display_module);
