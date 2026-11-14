# Copy this and memory_probe.c/live_memory.c/live_translate.c with their headers
# to an ignored external-module build directory; name this file Makefile there.
obj-m += bm_memory_probe.o
bm_memory_probe-y := memory_probe.o live_memory.o live_translate.o
