// SPDX-License-Identifier: MIT
// Original bounded Python API over the proven Rust board drivers.
#include "py/runtime.h"
#include "py/mphal.h"
#include "py/mperrno.h"
extern int bm_pin(uint32_t,int,int);
extern int bm_i2c_init(void);
extern int bm_i2c_read(uint32_t,uint32_t,uint8_t *,size_t);
extern int bm_i2c_write(uint32_t,uint32_t,const uint8_t *,size_t);
extern int bm_spi_transfer(uint32_t,const uint8_t *,uint8_t *,size_t);
extern uint32_t bm_led_status(uint32_t);
extern uint32_t bm_watchdog_status(uint32_t);
static mp_obj_t watchdog_status(void){mp_obj_t t[5];for(unsigned i=0;i<5;i++)t[i]=mp_obj_new_int_from_uint(bm_watchdog_status(i));return mp_obj_new_tuple(5,t);}
static MP_DEFINE_CONST_FUN_OBJ_0(watchdog_status_obj,watchdog_status);
extern void bm_watchdog_selftest(void) __attribute__((noreturn));
extern void bm_machine_reset(uint32_t) __attribute__((noreturn));
static mp_obj_t machine_reset(size_t n,const mp_obj_t *a){mp_int_t mode=n?mp_obj_get_int(a[0]):0;if(mode<0||mode>1)mp_raise_ValueError(MP_ERROR_TEXT("reset mode 0 or 1"));bm_machine_reset(mode);}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(machine_reset_obj,0,1,machine_reset);
static mp_obj_t watchdog_selftest(void){bm_watchdog_selftest();}
static MP_DEFINE_CONST_FUN_OBJ_0(watchdog_selftest_obj,watchdog_selftest);
extern uint32_t bm_console_status(uint32_t);
static mp_obj_t console_status(void) {
    static const qstr names[]={MP_QSTR_usb_only,MP_QSTR_uart_pad_mux,MP_QSTR_uart_gpio_output,MP_QSTR_uart_ier,MP_QSTR_uart_irq_enabled,MP_QSTR_usb_ready};
    mp_obj_t result=mp_obj_new_dict(0);
    for (size_t i=0;i<6;i++) mp_obj_dict_store(result,MP_OBJ_NEW_QSTR(names[i]),mp_obj_new_int_from_uint(bm_console_status(i)));
    return result;
}
static MP_DEFINE_CONST_FUN_OBJ_0(console_status_obj,console_status);
static mp_obj_t led_status(void) {
    mp_obj_t result=mp_obj_new_dict(0);
    mp_obj_dict_store(result,MP_OBJ_NEW_QSTR(MP_QSTR_enabled),mp_obj_new_bool(bm_led_status(0)));
    mp_obj_dict_store(result,MP_OBJ_NEW_QSTR(MP_QSTR_transitions),mp_obj_new_int_from_uint(bm_led_status(1)));
    mp_obj_dict_store(result,MP_OBJ_NEW_QSTR(MP_QSTR_pad_errors),mp_obj_new_int_from_uint(bm_led_status(2)));
    mp_obj_dict_store(result,MP_OBJ_NEW_QSTR(MP_QSTR_state),mp_obj_new_int_from_uint(bm_led_status(3)));
    mp_obj_dict_store(result,MP_OBJ_NEW_QSTR(MP_QSTR_hz),mp_obj_new_int_from_uint(bm_led_status(4)));
    return result;
}
static MP_DEFINE_CONST_FUN_OBJ_0(led_status_obj,led_status);
static void checked(int status) {if(status<0)mp_raise_OSError(MP_EIO);}
typedef struct {mp_obj_base_t base;uint32_t id;} pin_obj;
static mp_obj_t pin_new(const mp_obj_type_t *type,size_t n,size_t kw,const mp_obj_t *args) {
    enum {ID,MODE,VALUE};
    static const mp_arg_t allowed[]={
        {MP_QSTR_id,MP_ARG_REQUIRED|MP_ARG_INT,{.u_int=0}},
        {MP_QSTR_mode,MP_ARG_INT,{.u_int=0}},
        {MP_QSTR_value,MP_ARG_KW_ONLY|MP_ARG_INT,{.u_int=-1}}};
    mp_arg_val_t v[3];mp_arg_parse_all_kw_array(n,kw,args,3,allowed,v);
    if((v[ID].u_int!=52&&v[ID].u_int!=53)||(v[MODE].u_int!=0&&v[MODE].u_int!=1))mp_raise_ValueError(MP_ERROR_TEXT("Pins52/53, IN/OUT only"));
    checked(bm_pin(v[ID].u_int,v[MODE].u_int,v[VALUE].u_int));
    pin_obj *self=mp_obj_malloc(pin_obj,type);self->id=v[ID].u_int;return MP_OBJ_FROM_PTR(self);
}
static mp_obj_t pin_value(size_t n,const mp_obj_t *args) {
    pin_obj *self=MP_OBJ_TO_PTR(args[0]);int result=bm_pin(self->id,-1,n==2?mp_obj_is_true(args[1]):-1);checked(result);return n==2?mp_const_none:mp_obj_new_int(result);
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(pin_value_obj,1,2,pin_value);
static const mp_rom_map_elem_t pin_locals_table[]={
    {MP_ROM_QSTR(MP_QSTR_IN),MP_ROM_INT(0)},{MP_ROM_QSTR(MP_QSTR_OUT),MP_ROM_INT(1)},
    {MP_ROM_QSTR(MP_QSTR_value),MP_ROM_PTR(&pin_value_obj)}};
static MP_DEFINE_CONST_DICT(pin_locals,pin_locals_table);
static MP_DEFINE_CONST_OBJ_TYPE(pin_type,MP_QSTR_Pin,MP_TYPE_FLAG_NONE,make_new,pin_new,locals_dict,&pin_locals);
typedef struct {mp_obj_base_t base;} i2c_obj;
static mp_obj_t i2c_new(const mp_obj_type_t *type,size_t n,size_t kw,const mp_obj_t *args) {
    static const mp_arg_t allowed[]={{MP_QSTR_id,MP_ARG_REQUIRED|MP_ARG_INT,{.u_int=4}},{MP_QSTR_freq,MP_ARG_KW_ONLY|MP_ARG_INT,{.u_int=100000}}};
    mp_arg_val_t v[2];mp_arg_parse_all_kw_array(n,kw,args,2,allowed,v);
    if(v[0].u_int!=4||v[1].u_int!=100000)mp_raise_ValueError(MP_ERROR_TEXT("I2C4 at100kHz only"));
    checked(bm_i2c_init());return MP_OBJ_FROM_PTR(mp_obj_malloc(i2c_obj,type));
}
static void addrsize(size_t n,const mp_obj_t *args,mp_map_t *kwargs) {
    (void)args;mp_arg_check_num(n,kwargs->used,4,4,true);
    static const mp_arg_t allowed[]={{MP_QSTR_addrsize,MP_ARG_KW_ONLY|MP_ARG_INT,{.u_int=16}}};
    mp_arg_val_t v[1];mp_arg_parse_all(0,NULL,kwargs,1,allowed,v);
    if(v[0].u_int!=16)mp_raise_ValueError(MP_ERROR_TEXT("16-bit sensor register addresses required"));
}
static mp_obj_t i2c_read(size_t n,const mp_obj_t *args,mp_map_t *kwargs) {
    addrsize(n,args,kwargs);mp_int_t count=mp_obj_get_int(args[3]);
    if(count<0||count>32)mp_raise_ValueError(MP_ERROR_TEXT("read length0..32"));
    vstr_t buffer;vstr_init_len(&buffer,count);
    int status=bm_i2c_read(mp_obj_get_int(args[1]),mp_obj_get_int(args[2]),(uint8_t *)buffer.buf,count);
    if(status<0){vstr_clear(&buffer);checked(status);}
    return mp_obj_new_bytes_from_vstr(&buffer);
}
static MP_DEFINE_CONST_FUN_OBJ_KW(i2c_read_obj,4,i2c_read);
static mp_obj_t i2c_write(size_t n,const mp_obj_t *args,mp_map_t *kwargs) {
    addrsize(n,args,kwargs);mp_buffer_info_t buffer;mp_get_buffer_raise(args[3],&buffer,MP_BUFFER_READ);
    checked(bm_i2c_write(mp_obj_get_int(args[1]),mp_obj_get_int(args[2]),buffer.buf,buffer.len));return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(i2c_write_obj,4,i2c_write);
static const mp_rom_map_elem_t i2c_locals_table[]={
    {MP_ROM_QSTR(MP_QSTR_readfrom_mem),MP_ROM_PTR(&i2c_read_obj)},
    {MP_ROM_QSTR(MP_QSTR_writeto_mem),MP_ROM_PTR(&i2c_write_obj)}};
static MP_DEFINE_CONST_DICT(i2c_locals,i2c_locals_table);
static MP_DEFINE_CONST_OBJ_TYPE(i2c_type,MP_QSTR_I2C,MP_TYPE_FLAG_NONE,make_new,i2c_new,locals_dict,&i2c_locals);
typedef struct {mp_obj_base_t base;uint32_t baudrate;} spi_obj;
static mp_obj_t spi_new(const mp_obj_type_t *type,size_t n,size_t kw,const mp_obj_t *args) {
    static const mp_arg_t allowed[]={{MP_QSTR_id,MP_ARG_REQUIRED|MP_ARG_INT,{.u_int=0}},{MP_QSTR_baudrate,MP_ARG_KW_ONLY|MP_ARG_INT,{.u_int=1000000}}};
    mp_arg_val_t v[2];mp_arg_parse_all_kw_array(n,kw,args,2,allowed,v);
    if(v[0].u_int!=0||v[1].u_int<100000||v[1].u_int>50000000)mp_raise_ValueError(MP_ERROR_TEXT("SPI0,100kHz..50MHz only"));
    spi_obj *self=mp_obj_malloc(spi_obj,type);self->baudrate=v[1].u_int;return MP_OBJ_FROM_PTR(self);
}
static mp_obj_t spi_exchange(mp_obj_t self_in,mp_obj_t tx_in,mp_obj_t rx_in) {
    spi_obj *self=MP_OBJ_TO_PTR(self_in);mp_buffer_info_t tx,rx;
    mp_get_buffer_raise(tx_in,&tx,MP_BUFFER_READ);mp_get_buffer_raise(rx_in,&rx,MP_BUFFER_WRITE);
    if(tx.len!=rx.len||tx.len<1||tx.len>4096)mp_raise_ValueError(MP_ERROR_TEXT("equal buffers of1..4096 bytes required"));
    checked(bm_spi_transfer(self->baudrate,tx.buf,rx.buf,tx.len));return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_3(spi_exchange_obj,spi_exchange);
static const mp_rom_map_elem_t spi_locals_table[]={{MP_ROM_QSTR(MP_QSTR_write_readinto),MP_ROM_PTR(&spi_exchange_obj)}};
static MP_DEFINE_CONST_DICT(spi_locals,spi_locals_table);
static MP_DEFINE_CONST_OBJ_TYPE(spi_type,MP_QSTR_SPI,MP_TYPE_FLAG_NONE,make_new,spi_new,locals_dict,&spi_locals);
// Read actual traceback metadata without printing exception arguments to USB/UART.
static mp_obj_t exception_location(mp_obj_t exception) {
    if(!mp_obj_is_exception_instance(exception))mp_raise_TypeError(MP_ERROR_TEXT("Exception required"));
    size_t count,*values;mp_obj_exception_get_traceback(exception,&count,&values);
    if(count<3)return mp_const_none;
    mp_obj_t fields[]={MP_OBJ_NEW_QSTR(values[0]),mp_obj_new_int_from_uint(values[1]),values[2]?MP_OBJ_NEW_QSTR(values[2]):MP_OBJ_NEW_QSTR(MP_QSTR_)};
    return mp_obj_new_tuple(3,fields);
}
static MP_DEFINE_CONST_FUN_OBJ_1(exception_location_obj,exception_location);
extern int bm_reset_info(uint32_t *,uint32_t);
extern void bm_reset_clear(void);
extern void bm_reset_marker(uint32_t);
extern uint32_t bm_reset_probe_enabled(void);
extern int bm_reset_probe(uint32_t);
static mp_obj_t reset_info(void){
    uint32_t words[16];int result=bm_reset_info(words,16);
    if(result==0)return mp_const_none;
    if(result!=16)mp_raise_msg(&mp_type_RuntimeError,MP_ERROR_TEXT("Reset record read failed"));
    static const qstr names[]={MP_QSTR_format_version,MP_QSTR_reason,MP_QSTR_marker,MP_QSTR_lr,MP_QSTR_spsr,MP_QSTR_mode,MP_QSTR_dfsr,MP_QSTR_dfar,MP_QSTR_ifsr,MP_QSTR_ifar,MP_QSTR_counter_low,MP_QSTR_counter_high};
    mp_obj_t out=mp_obj_new_dict(0);
    for(size_t i=0;i<12;i++)mp_obj_dict_store(out,MP_OBJ_NEW_QSTR(names[i]),mp_obj_new_int_from_uint(words[i+1]));
    return out;
}
static MP_DEFINE_CONST_FUN_OBJ_0(reset_info_obj,reset_info);
static mp_obj_t reset_clear(void){bm_reset_clear();return mp_const_none;}
static MP_DEFINE_CONST_FUN_OBJ_0(reset_clear_obj,reset_clear);
static mp_obj_t reset_marker(mp_obj_t value){mp_int_t marker=mp_obj_get_int(value);if(marker<0)mp_raise_ValueError(MP_ERROR_TEXT("Nonnegative marker required"));bm_reset_marker(marker);return mp_const_none;}
static MP_DEFINE_CONST_FUN_OBJ_1(reset_marker_obj,reset_marker);
static mp_obj_t reset_probe_enabled(void){return mp_obj_new_bool(bm_reset_probe_enabled());}
static MP_DEFINE_CONST_FUN_OBJ_0(reset_probe_enabled_obj,reset_probe_enabled);
static mp_obj_t reset_probe(mp_obj_t value){mp_int_t kind=mp_obj_get_int(value);if(kind<1||kind>4)mp_raise_ValueError(MP_ERROR_TEXT("Diagnostic probe1..4 required"));if(bm_reset_probe(kind)<0)mp_raise_msg(&mp_type_NotImplementedError,MP_ERROR_TEXT("Fault probes disabled or unavailable"));return mp_const_none;}
static MP_DEFINE_CONST_FUN_OBJ_1(reset_probe_obj,reset_probe);
static const mp_rom_map_elem_t machine_globals_table[]={
    {MP_ROM_QSTR(MP_QSTR___name__),MP_ROM_QSTR(MP_QSTR_machine)},
    {MP_ROM_QSTR(MP_QSTR_last_reset),MP_ROM_PTR(&reset_info_obj)},
    {MP_ROM_QSTR(MP_QSTR_clear_reset_record),MP_ROM_PTR(&reset_clear_obj)},
    {MP_ROM_QSTR(MP_QSTR_set_reset_marker),MP_ROM_PTR(&reset_marker_obj)},
    {MP_ROM_QSTR(MP_QSTR_fault_probes_enabled),MP_ROM_PTR(&reset_probe_enabled_obj)},
    {MP_ROM_QSTR(MP_QSTR_fault_probe),MP_ROM_PTR(&reset_probe_obj)},
    {MP_ROM_QSTR(MP_QSTR_Pin),MP_ROM_PTR(&pin_type)},
    {MP_ROM_QSTR(MP_QSTR_led_status),MP_ROM_PTR(&led_status_obj)},
    {MP_ROM_QSTR(MP_QSTR_reset),MP_ROM_PTR(&machine_reset_obj)},
    {MP_ROM_QSTR(MP_QSTR_watchdog_status),MP_ROM_PTR(&watchdog_status_obj)},
    {MP_ROM_QSTR(MP_QSTR_watchdog_selftest),MP_ROM_PTR(&watchdog_selftest_obj)},
    {MP_ROM_QSTR(MP_QSTR_console_status),MP_ROM_PTR(&console_status_obj)},
    {MP_ROM_QSTR(MP_QSTR_exception_location),MP_ROM_PTR(&exception_location_obj)},
    {MP_ROM_QSTR(MP_QSTR_I2C),MP_ROM_PTR(&i2c_type)},
    {MP_ROM_QSTR(MP_QSTR_SPI),MP_ROM_PTR(&spi_type)}};
static MP_DEFINE_CONST_DICT(machine_globals,machine_globals_table);
const mp_obj_module_t machine_module={.base={&mp_type_module},.globals=(mp_obj_dict_t *)&machine_globals};
MP_REGISTER_MODULE(MP_QSTR_machine,machine_module);

static mp_obj_t time_ticks(void){return mp_obj_new_int_from_uint(mp_hal_ticks_ms());}
static MP_DEFINE_CONST_FUN_OBJ_0(time_ticks_obj,time_ticks);
static mp_obj_t time_sleep(mp_obj_t ms){mp_int_t value=mp_obj_get_int(ms);if(value<0)mp_raise_ValueError(MP_ERROR_TEXT("negative delay"));mp_hal_delay_ms(value);return mp_const_none;}
static MP_DEFINE_CONST_FUN_OBJ_1(time_sleep_obj,time_sleep);
static const mp_rom_map_elem_t time_globals_table[]={
    {MP_ROM_QSTR(MP_QSTR___name__),MP_ROM_QSTR(MP_QSTR_time)},
    {MP_ROM_QSTR(MP_QSTR_ticks_ms),MP_ROM_PTR(&time_ticks_obj)},
    {MP_ROM_QSTR(MP_QSTR_sleep_ms),MP_ROM_PTR(&time_sleep_obj)}};
static MP_DEFINE_CONST_DICT(time_globals,time_globals_table);
const mp_obj_module_t time_module={.base={&mp_type_module},.globals=(mp_obj_dict_t *)&time_globals};
MP_REGISTER_MODULE(MP_QSTR_time,time_module);
