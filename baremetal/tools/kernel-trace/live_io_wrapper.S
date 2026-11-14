/* SPDX-License-Identifier: GPL-2.0-only */
/* Preserve original write-call state, execute its barrier, then observe it. */
.syntax unified
.thumb
.text
.balign 4
.global bm_io_wrapper
.type bm_io_wrapper,%function
.thumb_func
bm_io_wrapper:
    push.w {r0-r12,lr}
    mrs r2,cpsr
    push {r2,r3}
    bl arm_heavy_mb
    add r0,sp,#8
    bl bm_trace_io_snapshot
    pop {r2,r3}
    msr APSR_nzcvqg,r2
    pop.w {r0-r12,lr}
    bx lr
.size bm_io_wrapper,.-bm_io_wrapper
