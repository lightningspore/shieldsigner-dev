// SPDX-License-Identifier: MIT
// Native best-effort clearing for explicitly discarded, caller-owned objects.
#include <stdint.h>
#include "py/runtime.h"
#include "py/gc.h"
#include "py/objstr.h"
#include "py/objarray.h"
static void clear(volatile uint8_t *p,size_t n){while(n--)*p++=0;}
static mp_obj_t wipe(mp_obj_t value){
    if(value==mp_const_none||mp_obj_is_qstr(value))return mp_const_false;
    bool string=mp_obj_is_str(value);
    bool bytes=mp_obj_is_type(value,&mp_type_bytes);
    bool array=mp_obj_is_type(value,&mp_type_bytearray);
    if(!string&&!bytes&&!array)mp_raise_TypeError(MP_ERROR_TEXT("wipe expects str, bytes or bytearray"));
    void *object=MP_OBJ_TO_PTR(value);
    // Frozen objects and externally owned buffers must never be written.
    size_t header=array?sizeof(mp_obj_array_t):sizeof(mp_obj_str_t);
    if(gc_nbytes(object)<header)return mp_const_false;
    size_t n;const byte *data;
    if(array){mp_obj_array_t *a=object;n=a->len;data=a->items;}
    else {mp_obj_str_t *s=object;n=s->len;data=s->data;}
    if(!n)return mp_const_false;
    // gc_nbytes accepts only an allocation HEAD, not an interior/view pointer.
    size_t need=n+(array?0:1);
    if(need<n||gc_nbytes(data)<need)return mp_const_false;
    if(string){qstr q=qstr_find_strn((const char*)data,n);if(q!=MP_QSTRnull){size_t len;if(qstr_data(q,&len)==data)return mp_const_false;}}
    clear((volatile uint8_t*)data,n);
    if(!array)((mp_obj_str_t*)object)->hash=0;
    return mp_const_true;
}
static MP_DEFINE_CONST_FUN_OBJ_1(wipe_obj,wipe);
static const mp_rom_map_elem_t globals_table[]={
 {MP_ROM_QSTR(MP_QSTR___name__),MP_ROM_QSTR(MP_QSTR__native_memory)},
 {MP_ROM_QSTR(MP_QSTR_wipe),MP_ROM_PTR(&wipe_obj)}};
static MP_DEFINE_CONST_DICT(globals,globals_table);
const mp_obj_module_t memory_module={.base={&mp_type_module},.globals=(mp_obj_dict_t*)&globals};
MP_REGISTER_MODULE(MP_QSTR__native_memory,memory_module);
