// SPDX-License-Identifier: MIT
#include "py/runtime.h"
#include "py/mperrno.h"
extern int bm_qr_decode(const unsigned char *,unsigned int,unsigned int,unsigned char *,unsigned int);
static mp_obj_t qr_decode(mp_obj_t pixels,mp_obj_t width_obj,mp_obj_t height_obj){
    mp_int_t width=mp_obj_get_int(width_obj),height=mp_obj_get_int(height_obj);
    if(width<=0||width>640||height<=0||height>480)mp_raise_ValueError(MP_ERROR_TEXT("QR luma dimensions outside640x480"));
    mp_buffer_info_t image;mp_get_buffer_raise(pixels,&image,MP_BUFFER_READ);
    if(image.len!=(size_t)(width*height))mp_raise_ValueError(MP_ERROR_TEXT("packed luma buffer length mismatch"));
    unsigned char output[8192];
    int count=bm_qr_decode(image.buf,width,height,output,sizeof(output));
    if(count<0)mp_raise_OSError(MP_EIO);
    if(count==0)return mp_const_none;
    return mp_obj_new_bytes(output,count-1);
}
static MP_DEFINE_CONST_FUN_OBJ_3(qr_decode_obj,qr_decode);
static const mp_rom_map_elem_t qr_globals_table[]={
    {MP_ROM_QSTR(MP_QSTR___name__),MP_ROM_QSTR(MP_QSTR_qr)},
    {MP_ROM_QSTR(MP_QSTR_decode),MP_ROM_PTR(&qr_decode_obj)}};
static MP_DEFINE_CONST_DICT(qr_globals,qr_globals_table);
const mp_obj_module_t qr_module={.base={&mp_type_module},.globals=(mp_obj_dict_t *)&qr_globals};
MP_REGISTER_MODULE(MP_QSTR_qr,qr_module);
