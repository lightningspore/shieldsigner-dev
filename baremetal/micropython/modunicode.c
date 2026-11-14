// SPDX-License-Identifier: MIT
#include <stdint.h>
#include <string.h>
#include "py/runtime.h"
#include "py/objstr.h"
extern int bm_unicode_normalize(uint32_t,const void *,size_t,void *,size_t);
static int mode(mp_obj_t form){if(!mp_obj_is_str(form))mp_raise_TypeError(MP_ERROR_TEXT("normalization form must be str"));size_t n;const char *s=mp_obj_str_get_data(form,&n);if(n==3&&!memcmp(s,"NFC",3))return 0;if(n==3&&!memcmp(s,"NFD",3))return 1;if(n==4&&!memcmp(s,"NFKC",4))return 2;if(n==4&&!memcmp(s,"NFKD",4))return 3;mp_raise_ValueError(MP_ERROR_TEXT("invalid normalization form"));}
static void error(int status){if(status==-2)mp_raise_type(&mp_type_KeyboardInterrupt);mp_raise_ValueError(MP_ERROR_TEXT("normalization input/output limit or invalid UTF8"));}
static mp_obj_t normalize(mp_obj_t form,mp_obj_t text){if(!mp_obj_is_str(form)||!mp_obj_is_str(text))mp_raise_TypeError(MP_ERROR_TEXT("normalize requires str arguments"));size_t n;const char *data=mp_obj_str_get_data(text,&n);if(n==0)return MP_OBJ_NEW_QSTR(MP_QSTR_);int op=mode(form);int size=bm_unicode_normalize(op,data,n,NULL,0);if(size<0)error(size);if(size==0)return MP_OBJ_NEW_QSTR(MP_QSTR_);vstr_t output;vstr_init_len(&output,size);int count=bm_unicode_normalize(op,data,n,output.buf,size);if(count!=size){for(size_t i=0;i<output.len;i++)((volatile char*)output.buf)[i]=0;vstr_clear(&output);error(count);}return mp_obj_new_str_from_vstr(&output);}
static MP_DEFINE_CONST_FUN_OBJ_2(normalize_obj,normalize);
static mp_obj_t is_normalized(mp_obj_t form,mp_obj_t text){return mp_obj_new_bool(mp_obj_equal(normalize(form,text),text));}
static MP_DEFINE_CONST_FUN_OBJ_2(is_normalized_obj,is_normalized);
static MP_DEFINE_STR_OBJ(version_obj,"15.0.0");
static const mp_rom_map_elem_t unicode_globals_table[]={
 {MP_ROM_QSTR(MP_QSTR___name__),MP_ROM_QSTR(MP_QSTR_unicodedata)},
 {MP_ROM_QSTR(MP_QSTR_unidata_version),MP_ROM_PTR(&version_obj)},
 {MP_ROM_QSTR(MP_QSTR_normalize),MP_ROM_PTR(&normalize_obj)},
 {MP_ROM_QSTR(MP_QSTR_is_normalized),MP_ROM_PTR(&is_normalized_obj)}};
static MP_DEFINE_CONST_DICT(unicode_globals,unicode_globals_table);
const mp_obj_module_t unicode_module={.base={&mp_type_module},.globals=(mp_obj_dict_t *)&unicode_globals};
MP_REGISTER_MODULE(MP_QSTR_unicodedata,unicode_module);
