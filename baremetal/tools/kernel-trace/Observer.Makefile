ccflags-y += -DBM_PREFLIGHT_LIBRARY
obj-m += bm_live_observer.o
bm_live_observer-y := live_observer.o live_preflight.o live_ir.o live_memory.o live_translate.o live_io_wrapper.o live_patch.o
