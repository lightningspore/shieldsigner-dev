// SPDX-License-Identifier: MIT
// Only the newlib ABI needed by the in-process UI. No files or OS emulation.
#include <errno.h>
#include <stddef.h>
#include <stdint.h>
#include <sys/stat.h>
#include <sys/time.h>
extern void bm_uart_write(const void *,size_t);
extern void bm_ui_fatal(void);
void *__dso_handle=0;
int _write(int fd,const void *data,size_t length){if(fd!=1&&fd!=2){errno=EBADF;return -1;}bm_uart_write(data,length);return (int)length;}
int _read(int fd,void *data,size_t length){(void)fd;(void)data;(void)length;errno=EAGAIN;return -1;}
int _close(int fd){(void)fd;errno=EBADF;return -1;}
int _fstat(int fd,struct stat *st){if(fd<0||fd>2){errno=EBADF;return -1;}st->st_mode=S_IFCHR;return 0;}
int _isatty(int fd){return fd>=0&&fd<=2;}
int _lseek(int fd,int offset,int whence){(void)fd;(void)offset;(void)whence;errno=ESPIPE;return -1;}
void *_sbrk(ptrdiff_t increment){(void)increment;errno=ENOMEM;return (void*)-1;}
int _getpid(void){return 1;}
int _kill(int pid,int signal){(void)pid;(void)signal;errno=EINVAL;return -1;}
int _gettimeofday(struct timeval *tv,void *tz){(void)tv;(void)tz;errno=ENOSYS;return -1;}
void _exit(int status){(void)status;bm_ui_fatal();__builtin_unreachable();}
