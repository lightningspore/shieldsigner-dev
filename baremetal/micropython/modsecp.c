// SPDX-License-Identifier: MIT
// Buffer-validated portable binding to the actual pinned libsecp256k1.
#include <stdint.h>
#include <string.h>
#include "py/runtime.h"
#include "py/objstr.h"
#include "secp256k1.h"
#include "secp256k1_preallocated.h"
#include "secp256k1_extrakeys.h"
#include "secp256k1_schnorrsig.h"
#include "secp256k1_ecdh.h"
#include "secp256k1_recovery.h"
static unsigned char context_memory[4096] __attribute__((aligned(16)));
static secp256k1_context *context;
static bool randomized;
extern void bm_uart_write(const void *,size_t);
extern void bm_runtime_fault(void);
static void fatal(void){const char message[]="@@FAIL curve-library-invariant\r\n";bm_uart_write(message,sizeof(message)-1);bm_runtime_fault();for(;;){}}
void secp256k1_default_illegal_callback_fn(const char *message,void *data){(void)message;(void)data;fatal();}
void secp256k1_default_error_callback_fn(const char *message,void *data){(void)message;(void)data;fatal();}
static secp256k1_context *ctx(void){
    if(!context){
        if(secp256k1_context_preallocated_size(SECP256K1_CONTEXT_NONE)>sizeof(context_memory))mp_raise_msg(&mp_type_RuntimeError,MP_ERROR_TEXT("curve context capacity"));
        context=secp256k1_context_preallocated_create(context_memory,SECP256K1_CONTEXT_NONE);
        if(!context){fatal();}
    }
    return context;
}
static void wipe(void *p,size_t n){volatile unsigned char *v=p;while(n--)*v++=0;}
static void invalid(void){mp_raise_ValueError(MP_ERROR_TEXT("invalid curve encoding, scalar or result"));}
static mp_buffer_info_t buffer(mp_obj_t value,size_t size){
    if(mp_obj_is_str(value))mp_raise_TypeError(MP_ERROR_TEXT("curve input must be bytes-like"));
    mp_buffer_info_t b;mp_get_buffer_raise(value,&b,MP_BUFFER_READ);
    if(size!=(size_t)-1&&b.len!=size){invalid();}
    return b;
}
// Points cross the Python boundary as validated big-endian X||Y, never raw C structs.
static void point_in(mp_obj_t value,secp256k1_pubkey *p){
    mp_buffer_info_t b=buffer(value,64);unsigned char sec[65];sec[0]=4;memcpy(sec+1,b.buf,64);
    if(!secp256k1_ec_pubkey_parse(ctx(),p,sec,sizeof(sec))){invalid();}
}
static mp_obj_t point_out(const secp256k1_pubkey *p){
    unsigned char sec[65];size_t size=sizeof(sec);
    if(!secp256k1_ec_pubkey_serialize(ctx(),sec,&size,p,SECP256K1_EC_UNCOMPRESSED)||size!=65){fatal();}
    return mp_obj_new_bytes(sec+1,64);
}
// Signatures use canonical compact big-endian R||S, rather than opaque limb layouts.
static void signature_in(mp_obj_t value,secp256k1_ecdsa_signature *sig){
    mp_buffer_info_t b=buffer(value,64);if(!secp256k1_ecdsa_signature_parse_compact(ctx(),sig,b.buf)){invalid();}
}
static mp_obj_t signature_out(const secp256k1_ecdsa_signature *sig){
    unsigned char data[64];secp256k1_ecdsa_signature_serialize_compact(ctx(),data,sig);return mp_obj_new_bytes(data,64);
}
static mp_obj_t key_valid(mp_obj_t secret){mp_buffer_info_t b=buffer(secret,32);return mp_obj_new_bool(secp256k1_ec_seckey_verify(ctx(),b.buf));}
static MP_DEFINE_CONST_FUN_OBJ_1(key_valid_obj,key_valid);
static mp_obj_t point_create(mp_obj_t secret){
    mp_buffer_info_t b=buffer(secret,32);secp256k1_pubkey p;
    if(!secp256k1_ec_pubkey_create(ctx(),&p,b.buf)){invalid();}return point_out(&p);
}
static MP_DEFINE_CONST_FUN_OBJ_1(point_create_obj,point_create);
static mp_obj_t point_parse(mp_obj_t encoded){
    mp_buffer_info_t b=buffer(encoded,(size_t)-1);if(b.len!=33&&b.len!=65){invalid();}
    secp256k1_pubkey p;if(!secp256k1_ec_pubkey_parse(ctx(),&p,b.buf,b.len)){invalid();}return point_out(&p);
}
static MP_DEFINE_CONST_FUN_OBJ_1(point_parse_obj,point_parse);
static mp_obj_t point_serialize(mp_obj_t point,mp_obj_t flag){
    mp_int_t f=mp_obj_get_int(flag);if(f!=SECP256K1_EC_COMPRESSED&&f!=SECP256K1_EC_UNCOMPRESSED){invalid();}
    secp256k1_pubkey p;point_in(point,&p);unsigned char sec[65];size_t size=sizeof(sec);
    if(!secp256k1_ec_pubkey_serialize(ctx(),sec,&size,&p,f)){fatal();}return mp_obj_new_bytes(sec,size);
}
static MP_DEFINE_CONST_FUN_OBJ_2(point_serialize_obj,point_serialize);
static mp_obj_t scalar_op(mp_obj_t mode,mp_obj_t secret,mp_obj_t tweak){
    mp_int_t op=mp_obj_get_int(mode);if(op<0||op>2){invalid();}
    mp_buffer_info_t s=buffer(secret,32),t={0};if(op)t=buffer(tweak,32);
    vstr_t result;vstr_init_len(&result,32);memcpy(result.buf,s.buf,32);int ok;
    if(op==0)ok=secp256k1_ec_seckey_negate(ctx(),(unsigned char*)result.buf);
    else if(op==1)ok=secp256k1_ec_seckey_tweak_add(ctx(),(unsigned char*)result.buf,t.buf);
    else ok=secp256k1_ec_seckey_tweak_mul(ctx(),(unsigned char*)result.buf,t.buf);
    if(!ok){wipe(result.buf,32);vstr_clear(&result);invalid();}
    return mp_obj_new_bytes_from_vstr(&result);
}
static MP_DEFINE_CONST_FUN_OBJ_3(scalar_op_obj,scalar_op);
static mp_obj_t point_op(mp_obj_t mode,mp_obj_t point,mp_obj_t tweak){
    mp_int_t op=mp_obj_get_int(mode);if(op<0||op>2){invalid();}secp256k1_pubkey p;point_in(point,&p);
    mp_buffer_info_t t={0};if(op)t=buffer(tweak,32);int ok;
    if(op==0)ok=secp256k1_ec_pubkey_negate(ctx(),&p);
    else if(op==1)ok=secp256k1_ec_pubkey_tweak_add(ctx(),&p,t.buf);
    else ok=secp256k1_ec_pubkey_tweak_mul(ctx(),&p,t.buf);
    if(!ok){invalid();}return point_out(&p);
}
static MP_DEFINE_CONST_FUN_OBJ_3(point_op_obj,point_op);
static mp_obj_t signature_parse(mp_obj_t encoded,mp_obj_t compact){
    bool raw=mp_obj_is_true(compact);mp_buffer_info_t b=buffer(encoded,raw?64:(size_t)-1);secp256k1_ecdsa_signature sig;
    if(!b.len||b.len>80){invalid();}
    int ok=raw?secp256k1_ecdsa_signature_parse_compact(ctx(),&sig,b.buf):secp256k1_ecdsa_signature_parse_der(ctx(),&sig,b.buf,b.len);
    if(!ok){invalid();}return signature_out(&sig);
}
static MP_DEFINE_CONST_FUN_OBJ_2(signature_parse_obj,signature_parse);
static mp_obj_t signature_serialize(mp_obj_t signature,mp_obj_t compact){
    secp256k1_ecdsa_signature sig;signature_in(signature,&sig);
    if(mp_obj_is_true(compact))return signature_out(&sig);
    unsigned char der[72];size_t n=sizeof(der);if(!secp256k1_ecdsa_signature_serialize_der(ctx(),der,&n,&sig)){fatal();}
    return mp_obj_new_bytes(der,n);
}
static MP_DEFINE_CONST_FUN_OBJ_2(signature_serialize_obj,signature_serialize);
static mp_obj_t signature_normalize(mp_obj_t signature){
    secp256k1_ecdsa_signature sig,out;signature_in(signature,&sig);secp256k1_ecdsa_signature_normalize(ctx(),&out,&sig);return signature_out(&out);
}
static MP_DEFINE_CONST_FUN_OBJ_1(signature_normalize_obj,signature_normalize);
static mp_obj_t ecdsa_sign(size_t n,const mp_obj_t *args){
    (void)n;mp_buffer_info_t m=buffer(args[0],32),s=buffer(args[1],32),extra={0};
    if(args[2]!=mp_const_none)extra=buffer(args[2],32);
    bool recover=mp_obj_is_true(args[3]);unsigned char output[65];int ok;
    if(recover){
        secp256k1_ecdsa_recoverable_signature sig;ok=secp256k1_ecdsa_sign_recoverable(ctx(),&sig,m.buf,s.buf,NULL,extra.buf);
        if(!ok){invalid();}int recid;secp256k1_ecdsa_recoverable_signature_serialize_compact(ctx(),output,&recid,&sig);output[64]=recid;
    }else{
        secp256k1_ecdsa_signature sig;ok=secp256k1_ecdsa_sign(ctx(),&sig,m.buf,s.buf,NULL,extra.buf);
        if(!ok){invalid();}secp256k1_ecdsa_signature_serialize_compact(ctx(),output,&sig);
    }
    return mp_obj_new_bytes(output,recover?65:64);
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(ecdsa_sign_obj,4,4,ecdsa_sign);
static mp_obj_t ecdsa_verify(mp_obj_t signature,mp_obj_t message,mp_obj_t point){
    secp256k1_ecdsa_signature sig;signature_in(signature,&sig);mp_buffer_info_t m=buffer(message,32);secp256k1_pubkey p;point_in(point,&p);
    return mp_obj_new_bool(secp256k1_ecdsa_verify(ctx(),&sig,m.buf,&p));
}
static MP_DEFINE_CONST_FUN_OBJ_3(ecdsa_verify_obj,ecdsa_verify);
static mp_obj_t recover(mp_obj_t signature,mp_obj_t message){
    mp_buffer_info_t b=buffer(signature,65),m=buffer(message,32);const unsigned char *data=b.buf;secp256k1_ecdsa_recoverable_signature sig;
    if(data[64]>3||!secp256k1_ecdsa_recoverable_signature_parse_compact(ctx(),&sig,data,data[64])){invalid();}
    secp256k1_pubkey p;if(!secp256k1_ecdsa_recover(ctx(),&p,&sig,m.buf)){invalid();}return point_out(&p);
}
static MP_DEFINE_CONST_FUN_OBJ_2(recover_obj,recover);
static mp_obj_t xonly(mp_obj_t point){
    secp256k1_pubkey p;point_in(point,&p);secp256k1_xonly_pubkey x;int parity;
    if(!secp256k1_xonly_pubkey_from_pubkey(ctx(),&x,&parity,&p)){fatal();}
    unsigned char sec[33];sec[0]=2;secp256k1_xonly_pubkey_serialize(ctx(),sec+1,&x);
    if(!secp256k1_ec_pubkey_parse(ctx(),&p,sec,33)){fatal();}
    mp_obj_t items[2]={point_out(&p),MP_OBJ_NEW_SMALL_INT(parity)};return mp_obj_new_tuple(2,items);
}
static MP_DEFINE_CONST_FUN_OBJ_1(xonly_obj,xonly);
static mp_obj_t schnorr_sign(mp_obj_t message,mp_obj_t secret,mp_obj_t aux){
    mp_buffer_info_t m=buffer(message,(size_t)-1),s=buffer(secret,32),a={0};if(m.len>1048576){invalid();}
    if(aux!=mp_const_none)a=buffer(aux,32);
    secp256k1_keypair keypair;if(!secp256k1_keypair_create(ctx(),&keypair,s.buf)){invalid();}
    secp256k1_schnorrsig_extraparams options=SECP256K1_SCHNORRSIG_EXTRAPARAMS_INIT;options.ndata=a.buf;
    unsigned char signature[64];int ok=secp256k1_schnorrsig_sign_custom(ctx(),signature,m.buf,m.len,&keypair,&options);wipe(&keypair,sizeof(keypair));
    if(!ok){invalid();}return mp_obj_new_bytes(signature,64);
}
static MP_DEFINE_CONST_FUN_OBJ_3(schnorr_sign_obj,schnorr_sign);
static mp_obj_t schnorr_verify(mp_obj_t signature,mp_obj_t message,mp_obj_t point){
    mp_buffer_info_t s=buffer(signature,64),m=buffer(message,(size_t)-1);if(m.len>1048576){invalid();}
    secp256k1_pubkey p;point_in(point,&p);secp256k1_xonly_pubkey x;int parity;
    if(!secp256k1_xonly_pubkey_from_pubkey(ctx(),&x,&parity,&p)){fatal();}
    return mp_obj_new_bool(secp256k1_schnorrsig_verify(ctx(),s.buf,m.buf,m.len,&x));
}
static MP_DEFINE_CONST_FUN_OBJ_3(schnorr_verify_obj,schnorr_verify);
static mp_obj_t ecdh(mp_obj_t point,mp_obj_t secret){
    secp256k1_pubkey p;point_in(point,&p);mp_buffer_info_t s=buffer(secret,32);vstr_t result;vstr_init_len(&result,32);
    if(!secp256k1_ecdh(ctx(),(unsigned char*)result.buf,&p,s.buf,NULL,NULL)){wipe(result.buf,32);vstr_clear(&result);invalid();}
    return mp_obj_new_bytes_from_vstr(&result);
}
static MP_DEFINE_CONST_FUN_OBJ_2(ecdh_obj,ecdh);
static mp_obj_t randomize(mp_obj_t seed){
    mp_buffer_info_t s={0};if(seed!=mp_const_none)s=buffer(seed,32);
    if(!secp256k1_context_randomize(ctx(),s.buf)){fatal();}randomized=seed!=mp_const_none;return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(randomize_obj,randomize);
static mp_obj_t status(void){mp_obj_t result=mp_obj_new_dict(0);
    mp_obj_dict_store(result,MP_OBJ_NEW_QSTR(MP_QSTR_randomized),mp_obj_new_bool(randomized));
    mp_obj_dict_store(result,MP_OBJ_NEW_QSTR(MP_QSTR_context_bytes),mp_obj_new_int_from_uint(secp256k1_context_preallocated_size(SECP256K1_CONTEXT_NONE)));
    return result;
}
static MP_DEFINE_CONST_FUN_OBJ_0(status_obj,status);
#define ENTRY(name,obj) {MP_ROM_QSTR(MP_QSTR_##name),MP_ROM_PTR(&obj##_obj)}
static const mp_rom_map_elem_t globals_table[]={
    {MP_ROM_QSTR(MP_QSTR___name__),MP_ROM_QSTR(MP_QSTR__native_secp)},
    ENTRY(key_valid,key_valid),ENTRY(point_create,point_create),ENTRY(point_parse,point_parse),ENTRY(point_serialize,point_serialize),
    ENTRY(scalar_op,scalar_op),ENTRY(point_op,point_op),ENTRY(signature_parse,signature_parse),ENTRY(signature_serialize,signature_serialize),ENTRY(signature_normalize,signature_normalize),
    ENTRY(ecdsa_sign,ecdsa_sign),ENTRY(ecdsa_verify,ecdsa_verify),ENTRY(recover,recover),ENTRY(xonly,xonly),ENTRY(schnorr_sign,schnorr_sign),ENTRY(schnorr_verify,schnorr_verify),ENTRY(ecdh,ecdh),ENTRY(randomize,randomize),ENTRY(status,status)};
static MP_DEFINE_CONST_DICT(globals,globals_table);
const mp_obj_module_t secp_module={.base={&mp_type_module},.globals=(mp_obj_dict_t*)&globals};
MP_REGISTER_MODULE(MP_QSTR__native_secp,secp_module);
