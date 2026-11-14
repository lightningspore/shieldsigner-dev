// SPDX-License-Identifier: MIT
#include <stdint.h>
#include "py/runtime.h"
#include "py/objstr.h"
#include "py/mperrno.h"
extern int bm_hash_size(uint32_t);
extern int bm_hash_init(void *,uint32_t);
extern void bm_hash_update(void *,const void *,size_t);
extern int bm_hash_digest(const void *,void *);
extern void bm_hash_copy(void *,const void *);
extern void bm_hash_clear(void *);
extern int bm_hash_hmac(uint32_t,const void *,size_t,const void *,size_t,void *);
extern int bm_hash_pbkdf2(uint32_t,const void *,size_t,const void *,size_t,uint32_t,void *,size_t);
extern int bm_hash_compare(const void *,size_t,const void *,size_t);
typedef struct {mp_obj_base_t base;uint32_t closed;unsigned char state[512] __attribute__((aligned(16)));} native_hash_t;
static const mp_obj_type_t native_hash_type;
static void buffer(mp_obj_t obj,mp_buffer_info_t *info){if(mp_obj_is_str(obj))mp_raise_TypeError(MP_ERROR_TEXT("hash input must be bytes-like"));mp_get_buffer_raise(obj,info,MP_BUFFER_READ);}
static native_hash_t *allocate(void){native_hash_t *obj=mp_obj_malloc_with_finaliser(native_hash_t,&native_hash_type);obj->closed=1;if((uintptr_t)obj->state%16)mp_raise_OSError(MP_ENOMEM);bm_hash_clear(obj->state);return obj;}
static void checked(native_hash_t *obj){if(obj->closed)mp_raise_ValueError(MP_ERROR_TEXT("hash context cleared"));}
static mp_obj_t native_new(mp_obj_t id_obj,mp_obj_t data){mp_int_t id=mp_obj_get_int(id_obj);if(id<0||bm_hash_size(id)<0)mp_raise_ValueError(MP_ERROR_TEXT("unsupported hash"));mp_buffer_info_t b;buffer(data,&b);native_hash_t *obj=allocate();if(bm_hash_init(obj->state,id)<0)mp_raise_OSError(MP_EINVAL);obj->closed=0;bm_hash_update(obj->state,b.buf,b.len);return MP_OBJ_FROM_PTR(obj);}
static MP_DEFINE_CONST_FUN_OBJ_2(native_new_obj,native_new);
static mp_obj_t native_update(mp_obj_t self,mp_obj_t data){native_hash_t *obj=MP_OBJ_TO_PTR(self);checked(obj);mp_buffer_info_t b;buffer(data,&b);bm_hash_update(obj->state,b.buf,b.len);return mp_const_none;}
static MP_DEFINE_CONST_FUN_OBJ_2(native_update_obj,native_update);
static mp_obj_t native_digest(mp_obj_t self){native_hash_t *obj=MP_OBJ_TO_PTR(self);checked(obj);unsigned char output[64];int n=bm_hash_digest(obj->state,output);if(n<0)mp_raise_OSError(MP_EINVAL);mp_obj_t result=mp_obj_new_bytes(output,n);for(unsigned i=0;i<sizeof(output);i++)((volatile unsigned char *)output)[i]=0;return result;}
static MP_DEFINE_CONST_FUN_OBJ_1(native_digest_obj,native_digest);
static mp_obj_t native_copy(mp_obj_t self){native_hash_t *obj=MP_OBJ_TO_PTR(self);checked(obj);native_hash_t *copy=allocate();bm_hash_copy(copy->state,obj->state);copy->closed=0;return MP_OBJ_FROM_PTR(copy);}
static MP_DEFINE_CONST_FUN_OBJ_1(native_copy_obj,native_copy);
static mp_obj_t native_clear(mp_obj_t self){native_hash_t *obj=MP_OBJ_TO_PTR(self);bm_hash_clear(obj->state);obj->closed=1;return mp_const_none;}
static MP_DEFINE_CONST_FUN_OBJ_1(native_clear_obj,native_clear);
static const mp_rom_map_elem_t native_hash_locals_table[]={
 {MP_ROM_QSTR(MP_QSTR_update),MP_ROM_PTR(&native_update_obj)},
 {MP_ROM_QSTR(MP_QSTR_digest),MP_ROM_PTR(&native_digest_obj)},
 {MP_ROM_QSTR(MP_QSTR_copy),MP_ROM_PTR(&native_copy_obj)},
 {MP_ROM_QSTR(MP_QSTR___del__),MP_ROM_PTR(&native_clear_obj)}};
static MP_DEFINE_CONST_DICT(native_hash_locals,native_hash_locals_table);
static MP_DEFINE_CONST_OBJ_TYPE(native_hash_type,MP_QSTR_HashState,MP_TYPE_FLAG_NONE,locals_dict,&native_hash_locals);
static mp_obj_t native_hmac(size_t argc,const mp_obj_t *argv){(void)argc;mp_int_t id=mp_obj_get_int(argv[0]);if(id<0||bm_hash_size(id)<0)mp_raise_ValueError(MP_ERROR_TEXT("unsupported hash"));mp_buffer_info_t key,msg;buffer(argv[1],&key);buffer(argv[2],&msg);unsigned char output[64];int n=bm_hash_hmac(id,key.buf,key.len,msg.buf,msg.len,output);if(n<0)mp_raise_OSError(MP_EINVAL);mp_obj_t result=mp_obj_new_bytes(output,n);for(unsigned i=0;i<sizeof(output);i++)((volatile unsigned char *)output)[i]=0;return result;}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(native_hmac_obj,3,3,native_hmac);
static mp_obj_t native_pbkdf2(size_t argc,const mp_obj_t *argv){(void)argc;mp_int_t id=mp_obj_get_int(argv[0]),rounds=mp_obj_get_int(argv[3]),len=mp_obj_get_int(argv[4]);int size=id<0?-1:bm_hash_size(id);
 if(size<0||rounds<1||rounds>1000000||len<1||len>4096||(uint64_t)rounds*((len+size-1)/size)>1000000)mp_raise_ValueError(MP_ERROR_TEXT("PBKDF2 parameter or native work limit"));
 mp_buffer_info_t password,salt;buffer(argv[1],&password);buffer(argv[2],&salt);if(password.len>1048576||salt.len>1048576)mp_raise_ValueError(MP_ERROR_TEXT("PBKDF2 input limit"));
 vstr_t output;vstr_init_len(&output,len);int status=bm_hash_pbkdf2(id,password.buf,password.len,salt.buf,salt.len,rounds,output.buf,len);
 if(status<0){vstr_clear(&output);if(status==-2)mp_raise_type(&mp_type_KeyboardInterrupt);mp_raise_ValueError(MP_ERROR_TEXT("PBKDF2 failed"));}
 return mp_obj_new_bytes_from_vstr(&output);
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(native_pbkdf2_obj,5,5,native_pbkdf2);
static mp_obj_t native_compare(mp_obj_t a,mp_obj_t b){bool text=mp_obj_is_str(a);if(text!=mp_obj_is_str(b))mp_raise_TypeError(MP_ERROR_TEXT("compare_digest types must match"));
 mp_buffer_info_t x,y;if(text){size_t nx,ny;const unsigned char *sx=(const unsigned char *)mp_obj_str_get_data(a,&nx),*sy=(const unsigned char *)mp_obj_str_get_data(b,&ny);for(size_t i=0;i<nx;i++)if(sx[i]>127)mp_raise_TypeError(MP_ERROR_TEXT("compare_digest str must be ASCII"));for(size_t i=0;i<ny;i++)if(sy[i]>127)mp_raise_TypeError(MP_ERROR_TEXT("compare_digest str must be ASCII"));x.buf=(void *)sx;x.len=nx;y.buf=(void *)sy;y.len=ny;}else{buffer(a,&x);buffer(b,&y);}
 return mp_obj_new_bool(bm_hash_compare(x.buf,x.len,y.buf,y.len));}
static MP_DEFINE_CONST_FUN_OBJ_2(native_compare_obj,native_compare);
static const mp_rom_map_elem_t native_globals_table[]={
 {MP_ROM_QSTR(MP_QSTR___name__),MP_ROM_QSTR(MP_QSTR__native_hash)},
 {MP_ROM_QSTR(MP_QSTR_context),MP_ROM_PTR(&native_new_obj)},
 {MP_ROM_QSTR(MP_QSTR_hmac),MP_ROM_PTR(&native_hmac_obj)},
 {MP_ROM_QSTR(MP_QSTR_pbkdf2),MP_ROM_PTR(&native_pbkdf2_obj)},
 {MP_ROM_QSTR(MP_QSTR_compare_digest),MP_ROM_PTR(&native_compare_obj)}};
static MP_DEFINE_CONST_DICT(native_globals,native_globals_table);
const mp_obj_module_t native_hash_module={.base={&mp_type_module},.globals=(mp_obj_dict_t *)&native_globals};
MP_REGISTER_MODULE(MP_QSTR__native_hash,native_hash_module);
