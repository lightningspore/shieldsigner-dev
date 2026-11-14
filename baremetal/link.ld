ENTRY(_start)
SECTIONS {
    . = 0;
    .text : { KEEP(*(.text.entry)) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : {
        . = ALIGN(4); __bss_start = .;
        *(.bss .bss.*) *(COMMON)
        . = ALIGN(4); __bss_end = .;
    }
    /DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) }
    ASSERT(. < 0x00100000, "Image overlaps reserved stack area")
}
