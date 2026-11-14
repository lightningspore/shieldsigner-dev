ENTRY(_start)
SECTIONS {
    . = 0;
    .text : { KEEP(*(.text.entry)) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .ARM.extab : { *(.ARM.extab* .gnu.linkonce.armextab.*) }
    .ARM.exidx : { __exidx_start = .; *(.ARM.exidx* .gnu.linkonce.armexidx.*) __exidx_end = .; }
    .init_array : { . = ALIGN(4); __init_array_start = .; KEEP(*(SORT_BY_INIT_PRIORITY(.init_array.*))) KEEP(*(.init_array)) __init_array_end = .; }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : {
        . = ALIGN(8); __bss_start = .;
        *(.bss .bss.*) *(COMMON)
        . = ALIGN(8); __bss_end = .;
    }
    ASSERT(. < 0x00400000, "Native UI image overlaps Rust heap at4MiB")
}
