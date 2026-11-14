// SPDX-License-Identifier: MIT
#include <stdint.h>
int mp_hal_stdin_rx_chr(void);
mp_uint_t mp_hal_stdout_tx_strn(const char *s, size_t len);
mp_uint_t mp_hal_ticks_ms(void);
mp_uint_t mp_hal_ticks_us(void);
void mp_hal_delay_ms(mp_uint_t ms);
void mp_hal_delay_us(mp_uint_t us);
static inline void mp_hal_set_interrupt_char(char c) {(void)c;}
