// SPDX-License-Identifier: MIT
#define PCRE2_CODE_UNIT_WIDTH 8
#include "pcre2.h"
#include "py/runtime.h"
#include "py/objstr.h"
#include "py/mperrno.h"
static mp_obj_t regex_run(size_t argc,const mp_obj_t *argv){
    (void)argc;
    bool binary=mp_obj_is_type(argv[0],&mp_type_bytes);
    if(!binary&&!mp_obj_is_str(argv[0]))mp_raise_TypeError(MP_ERROR_TEXT("pattern must be str or bytes"));
    if(binary!=mp_obj_is_type(argv[1],&mp_type_bytes)||(!binary&&!mp_obj_is_str(argv[1])))mp_raise_TypeError(MP_ERROR_TEXT("pattern and subject types must match"));
    size_t plen,slen;const byte *pattern=(const byte *)mp_obj_str_get_data(argv[0],&plen),*subject=(const byte *)mp_obj_str_get_data(argv[1],&slen);
    if(plen>8192||slen>1048576)mp_raise_ValueError(MP_ERROR_TEXT("regex input limit"));
    int flags=mp_obj_get_int(argv[2]),mode=mp_obj_get_int(argv[3]);
    if(flags&~378||mode<0||mode>2)mp_raise_ValueError(MP_ERROR_TEXT("unsupported regex flags or mode"));
    if((binary&&(flags&32))||((flags&256)&&(flags&32)))mp_raise_ValueError(MP_ERROR_TEXT("incompatible regex flags"));
    uint32_t options=binary?0:PCRE2_UTF;
    if(!binary&&!(flags&256))options|=PCRE2_UCP;
    if(flags&2)options|=PCRE2_CASELESS;
    if(flags&8)options|=PCRE2_MULTILINE;
    if(flags&16)options|=PCRE2_DOTALL;
    if(flags&64)options|=PCRE2_EXTENDED;
    int error;PCRE2_SIZE where;
    pcre2_code *code=pcre2_compile(pattern,plen,options,&error,&where,NULL);
    if(!code)mp_raise_ValueError(MP_ERROR_TEXT("invalid regex pattern"));
    uint32_t captures=0;pcre2_pattern_info(code,PCRE2_INFO_CAPTURECOUNT,&captures);
    if(captures>=64){pcre2_code_free(code);mp_raise_ValueError(MP_ERROR_TEXT("regex capture limit"));}
    pcre2_match_data *data=pcre2_match_data_create_from_pattern(code,NULL);
    pcre2_match_context *context=pcre2_match_context_create(NULL);
    if(!data||!context){pcre2_match_data_free(data);pcre2_match_context_free(context);pcre2_code_free(code);mp_raise_OSError(MP_ENOMEM);}
    pcre2_set_match_limit(context,100000);pcre2_set_depth_limit(context,256);pcre2_set_heap_limit(context,512);
    int count=pcre2_match(code,subject,slen,0,(mode?PCRE2_ANCHORED:0)|(mode==2?PCRE2_ENDANCHORED:0),data,context);
    PCRE2_SIZE spans[128];
    if(count>=0){PCRE2_SIZE *ov=pcre2_get_ovector_pointer(data);for(unsigned i=0;i<(captures+1)*2;i++)spans[i]=ov[i];}
    pcre2_match_data_free(data);pcre2_match_context_free(context);pcre2_code_free(code);
    // All native resources are released before any Python object allocation/NLR.
    if(count==PCRE2_ERROR_NOMATCH)return mp_const_none;
    if(count<0)mp_raise_ValueError(MP_ERROR_TEXT("regex execution limit or invalid UTF8"));
    mp_obj_t groups[64],positions[64];
    for(unsigned i=0;i<=captures;i++){
        mp_int_t start=-1,end=-1;
        if(spans[i*2]!=PCRE2_UNSET){
            size_t a=spans[i*2],b=spans[i*2+1];
            groups[i]=binary?mp_obj_new_bytes(subject+a,b-a):mp_obj_new_str((const char *)subject+a,b-a);
            start=a;end=b;
            if(!binary){start=0;end=0;for(size_t j=0;j<b;j++)if((subject[j]&0xc0)!=0x80){end++;if(j<a)start++;}}
        }else groups[i]=mp_const_none;
        mp_obj_t pair[]={mp_obj_new_int(start),mp_obj_new_int(end)};positions[i]=mp_obj_new_tuple(2,pair);
    }
    mp_obj_t result[]={mp_obj_new_tuple(captures+1,groups),mp_obj_new_tuple(captures+1,positions)};
    return mp_obj_new_tuple(2,result);
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(regex_run_obj,4,4,regex_run);
static const mp_rom_map_elem_t regex_globals_table[]={
    {MP_ROM_QSTR(MP_QSTR___name__),MP_ROM_QSTR(MP_QSTR__regex)},
    {MP_ROM_QSTR(MP_QSTR_run),MP_ROM_PTR(&regex_run_obj)}};
static MP_DEFINE_CONST_DICT(regex_globals,regex_globals_table);
const mp_obj_module_t regex_module={.base={&mp_type_module},.globals=(mp_obj_dict_t *)&regex_globals};
MP_REGISTER_MODULE(MP_QSTR__regex,regex_module);
