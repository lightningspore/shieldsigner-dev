// SPDX-License-Identifier: MIT
// Original port glue. Core interpreter and GC helpers remain upstream MIT.
#include "py/runtime.h"
#include "py/builtin.h"
#include "py/gc.h"
#include "py/cstack.h"
#include "py/lexer.h"
#include "py/mperrno.h"
#include "shared/runtime/gchelper.h"
#include "shared/runtime/pyexec.h"
extern int bm_uart_getc(void);
extern void bm_uart_write(const char *,size_t);
extern uint32_t bm_ticks_us(void);
extern uint32_t bm_ticks_ms(void);
extern void bm_delay_us(uint32_t);
extern void bm_runtime_fault(void);
extern void bm_repl_ready(void);
extern int bm_console_poll(void);
extern void bm_set_interrupt_char(int);
void mp_hal_set_interrupt_char(int c) { bm_set_interrupt_char(c); }
void bm_micropython_poll(void) {
    if (bm_console_poll()) { mp_sched_keyboard_interrupt(); }
}
void bm_micropython_main(void) {
    mp_cstack_init_with_sp_here(768*1024);
    gc_init((void *)0x01000000,(void *)0x01800000);
    mp_init();
    bm_repl_ready();
    static const char ready[]="\r\n@@REPL_READY reset=Ctrl-]\r\n";
    bm_uart_write(ready,sizeof(ready)-1);
    for (;;) { pyexec_friendly_repl(); }
}
int mp_hal_stdin_rx_chr(void) { int c;while ((c=bm_uart_getc())<0) {}return c; }
mp_uint_t mp_hal_stdout_tx_strn(const char *s,size_t len) {bm_uart_write(s,len);return len;}
mp_uint_t mp_hal_ticks_us(void) {return bm_ticks_us();}
mp_uint_t mp_hal_ticks_ms(void) {return bm_ticks_ms();}
void mp_hal_delay_us(mp_uint_t us) {bm_delay_us(us);}
void mp_hal_delay_ms(mp_uint_t ms) {while(ms--)bm_delay_us(1000);}
void gc_collect(void) {gc_collect_start();gc_helper_collect_regs_and_stack();gc_collect_end();}
mp_lexer_t *mp_lexer_new_from_file(qstr filename) {(void)filename;mp_raise_OSError(MP_ENOENT);}
void nlr_jump_fail(void *value) {(void)value;bm_runtime_fault();for(;;){}}
void __fatal_error(const char *message) {(void)message;bm_runtime_fault();for(;;){}}

// Core io.BytesIO is available; filesystem-backed open awaits the SD driver.
static mp_obj_t port_open(size_t n,const mp_obj_t *args,mp_map_t *kwargs) {
    (void)n;(void)args;(void)kwargs;mp_raise_OSError(MP_ENODEV);
}
MP_DEFINE_CONST_FUN_OBJ_KW(mp_builtin_open_obj,1,port_open);

mp_import_stat_t mp_import_stat(const char *path) {(void)path;return MP_IMPORT_STAT_NO_EXIST;}
