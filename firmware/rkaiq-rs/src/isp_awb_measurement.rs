//! Recovered ISP32 AWB measurement configuration converter (ELF 0x2b71c).
//! SDK value-record input, not an AWB decision algorithm or calibrated startup.
use crate::isp32::PARAMETER_BYTES;
pub const INPUT_BYTES: usize = 1204;
pub const OFFSET: usize = 0xf4;
pub const BYTES: usize = 807;
pub const MASK: u64 = 1 << 22;
/// Exact little-endian SDK v32 record. Software-only metadata is preserved in
/// this input but ignored by the native converter. See AWB.md for its layout.
pub struct Measurement(pub [u8; INPUT_BYTES]);
impl Measurement {
    /// Update=false is a complete no-op. Disabled AWB still writes configuration
    /// on update=true and leaves all three existing masks unchanged.
    pub fn apply(&self, params: &mut [u8; PARAMETER_BYTES], update: bool) {
        if !update {
            return;
        }
        let input = &self.0;
        if input[0] != 0 {
            for offset in [0, 8, 16] {
                let value = u64::from_le_bytes(params[offset..offset + 8].try_into().unwrap());
                params[offset..offset + 8].copy_from_slice(&(value | MASK).to_le_bytes());
            }
        }
        for &(destination, source, length) in COPIES {
            params[destination..destination + length]
                .copy_from_slice(&input[source..source + length]);
        }
        params[0xf5] = 0;
        match input[0x3e] {
            // The original preserves bnr2awb_sel in DRC mode.
            4 => params[0xf7] = 1,
            3 => {
                params[0xf7] = 0;
                params[0xf6] = 1;
            }
            mode => {
                params[0xf7] = 0;
                params[0xf6] = 0;
                params[0xf5] = mode;
            }
        }
        params[0x23d..0x23f].copy_from_slice(&input[0x60..0x62]);
        params[0x100] = u8::from(input[0x60] != 0 || input[0x61] != 0);
        for i in 0..4 {
            let src = 0x264 + i * 8;
            let dst = 0x2ef + i * 8;
            let word = |o| u16::from_le_bytes(input[o..o + 2].try_into().unwrap());
            let h = word(src);
            let v = word(src + 2);
            for (j, value) in [
                v,
                h,
                v.wrapping_add(word(src + 6)),
                h.wrapping_add(word(src + 4)),
            ]
            .iter()
            .enumerate()
            {
                params[dst + j * 2..dst + j * 2 + 2].copy_from_slice(&value.to_le_bytes());
            }
        }
        for (i, dst) in [0x10d, 0x110, 0x113, 0x116, 0x119, 0x11b, 0x11d]
            .iter()
            .enumerate()
        {
            let src = 0x284 + i * 28;
            params[*dst] = input[src + 4].wrapping_add(input[src + 5].wrapping_mul(2));
        }
        params[0x155..0x236].copy_from_slice(&input[0x360..0x441]);
    }
}
// (absolute kernel-record offset, SDK-record offset, copied byte count).
// Low bytes intentionally implement native narrowing; untouched kernel bytes
// retain their previous values. This table covers direct assignments only;
// selectors, packed flags, arithmetic and grid weights are explicit above.
const COPIES: &[(usize, usize, usize)] = &[
    (0xf4, 0xc, 1),     // bls2_en
    (0x413, 0x10, 2),   // bls2_val
    (0x415, 0x14, 2),   // bls2_val
    (0x417, 0x18, 2),   // bls2_val
    (0x419, 0x1c, 2),   // bls2_val
    (0xf5, 0x3e, 1),    // rawawb_sel
    (0x107, 0x2, 1),    // low12bit_val
    (0xff, 0x8, 1),     // in_rshift_to_12bit_en
    (0xf9, 0x22, 1),    // xy_en0
    (0xf8, 0x20, 1),    // uv_en0
    (0xfa, 0x24, 1),    // yuv3d_en0
    (0x105, 0x23, 1),   // xy_en1
    (0x104, 0x21, 1),   // uv_en1
    (0x106, 0x25, 1),   // yuv3d_en1
    (0x10a, 0x30, 2),   // wp_blk_wei_en0 through wp_blk_wei_en1
    (0x102, 0x1, 1),    // rawlsc_bypass_en
    (0x236, 0x32, 1),   // blk_measure_enable
    (0x237, 0x38, 1),   // blk_measure_mode
    (0x238, 0x444, 1),  // blk_measure_xytype
    (0x23a, 0x448, 1),  // blk_measure_illu_idx
    (0x23c, 0x44c, 1),  // blk_with_luma_wei_en
    (0x108, 0x2e, 2),   // wp_luma_wei_en0 through wp_luma_wei_en1
    (0x10c, 0x35c, 1),  // wp_hist_xytype
    (0xfb, 0x26, 1),    // yuv3d_ls_idx0
    (0xfc, 0x28, 1),    // yuv3d_ls_idx1
    (0xfd, 0x2a, 1),    // yuv3d_ls_idx2
    (0xfe, 0x2c, 1),    // yuv3d_ls_idx3
    (0x103, 0x48, 1),   // light_num
    (0x24f, 0x40, 8),   // h_offs through v_size
    (0x101, 0x34, 1),   // wind_size
    (0x23f, 0x4a, 2),   // r_max
    (0x241, 0x4e, 2),   // g_max
    (0x243, 0x52, 2),   // b_max
    (0x245, 0x56, 2),   // y_max
    (0x247, 0x4c, 2),   // r_min
    (0x249, 0x50, 2),   // g_min
    (0x24b, 0x54, 2),   // b_min
    (0x24d, 0x58, 2),   // y_min
    (0x25d, 0xfc, 2),   // vertex0_u_0
    (0x25f, 0x106, 2),  // vertex0_v_0
    (0x261, 0xfe, 2),   // vertex1_u_0
    (0x263, 0x108, 2),  // vertex1_v_0
    (0x265, 0x100, 2),  // vertex2_u_0
    (0x267, 0x10a, 2),  // vertex2_v_0
    (0x269, 0x102, 2),  // vertex3_u_0
    (0x26b, 0x10c, 2),  // vertex3_v_0
    (0x3bf, 0x110, 16), // islope01_0 through islope30_0
    (0x26d, 0x120, 2),  // vertex0_u_1
    (0x26f, 0x12a, 2),  // vertex0_v_1
    (0x271, 0x122, 2),  // vertex1_u_1
    (0x273, 0x12c, 2),  // vertex1_v_1
    (0x275, 0x124, 2),  // vertex2_u_1
    (0x277, 0x12e, 2),  // vertex2_v_1
    (0x279, 0x126, 2),  // vertex3_u_1
    (0x27b, 0x130, 2),  // vertex3_v_1
    (0x3cf, 0x134, 16), // islope01_1 through islope30_1
    (0x27d, 0x144, 2),  // vertex0_u_2
    (0x27f, 0x14e, 2),  // vertex0_v_2
    (0x281, 0x146, 2),  // vertex1_u_2
    (0x283, 0x150, 2),  // vertex1_v_2
    (0x285, 0x148, 2),  // vertex2_u_2
    (0x287, 0x152, 2),  // vertex2_v_2
    (0x289, 0x14a, 2),  // vertex3_u_2
    (0x28b, 0x154, 2),  // vertex3_v_2
    (0x3df, 0x158, 16), // islope01_2 through islope30_2
    (0x28d, 0x168, 2),  // vertex0_u_3
    (0x28f, 0x172, 2),  // vertex0_v_3
    (0x291, 0x16a, 2),  // vertex1_u_3
    (0x293, 0x174, 2),  // vertex1_v_3
    (0x295, 0x16c, 2),  // vertex2_u_3
    (0x297, 0x176, 2),  // vertex2_v_3
    (0x299, 0x16e, 2),  // vertex3_u_3
    (0x29b, 0x178, 2),  // vertex3_v_3
    (0x3ef, 0x17c, 16), // islope01_3 through islope30_3
    (0x34f, 0x64, 16),  // rgb2ryuvmat0_u through rgb2ryuvofs_v
    (0x347, 0x74, 8),   // rgb2ryuvmat0_y through rgb2ryuvofs_y
    (0x133, 0x7c, 6),   // rotu0_ls0 through rotu5_ls0
    (0x38f, 0x82, 12),  // th0_ls0 through th5_ls0
    (0x363, 0x8e, 2),   // coor_x1_ls0_u
    (0x367, 0x90, 2),   // coor_x1_ls0_v
    (0x35f, 0x92, 2),   // coor_x1_ls0_y
    (0x365, 0x94, 2),   // vec_x21_ls0_u
    (0x369, 0x96, 2),   // vec_x21_ls0_v
    (0x361, 0x98, 2),   // vec_x21_ls0_y
    (0x132, 0x9a, 1),   // dis_x1x2_ls0
    (0x13a, 0x9c, 6),   // rotu0_ls1 through rotu5_ls1
    (0x39b, 0xa2, 12),  // th0_ls1 through th5_ls1
    (0x36f, 0xae, 2),   // coor_x1_ls1_u
    (0x373, 0xb0, 2),   // coor_x1_ls1_v
    (0x36b, 0xb2, 2),   // coor_x1_ls1_y
    (0x371, 0xb4, 2),   // vec_x21_ls1_u
    (0x375, 0xb6, 2),   // vec_x21_ls1_v
    (0x36d, 0xb8, 2),   // vec_x21_ls1_y
    (0x139, 0xba, 1),   // dis_x1x2_ls1
    (0x141, 0xbc, 6),   // rotu0_ls2 through rotu5_ls2
    (0x3a7, 0xc2, 12),  // th0_ls2 through th5_ls2
    (0x37b, 0xce, 2),   // coor_x1_ls2_u
    (0x37f, 0xd0, 2),   // coor_x1_ls2_v
    (0x377, 0xd2, 2),   // coor_x1_ls2_y
    (0x381, 0xd4, 2),   // vec_x21_ls2_u
    (0x37d, 0xd6, 2),   // vec_x21_ls2_v
    (0x379, 0xd8, 2),   // vec_x21_ls2_y
    (0x140, 0xda, 1),   // dis_x1x2_ls2
    (0x148, 0xdc, 6),   // rotu0_ls3 through rotu5_ls3
    (0x3b3, 0xe2, 12),  // th0_ls3 through th5_ls3
    (0x387, 0xee, 2),   // coor_x1_ls3_u
    (0x38b, 0xf0, 2),   // coor_x1_ls3_v
    (0x383, 0xf2, 2),   // coor_x1_ls3_y
    (0x389, 0xf4, 2),   // vec_x21_ls3_u
    (0x38d, 0xf6, 2),   // vec_x21_ls3_v
    (0x385, 0xf8, 2),   // vec_x21_ls3_y
    (0x147, 0xfa, 1),   // dis_x1x2_ls3
    (0x29d, 0x18c, 8),  // wt0 through mat0_x
    (0x2a7, 0x194, 2),  // mat1_x
    (0x2ab, 0x196, 2),  // mat2_x
    (0x2a5, 0x198, 2),  // mat0_y
    (0x2a9, 0x19a, 2),  // mat1_y
    (0x2ad, 0x19c, 2),  // mat2_y
    (0x2af, 0x1a4, 2),  // nor_x0_0
    (0x2b1, 0x1a8, 2),  // nor_x1_0
    (0x2b3, 0x1ac, 2),  // nor_y0_0
    (0x2b5, 0x1b0, 2),  // nor_y1_0
    (0x2cf, 0x1b4, 2),  // big_x0_0
    (0x2d1, 0x1b8, 2),  // big_x1_0
    (0x2d3, 0x1bc, 2),  // big_y0_0
    (0x2d5, 0x1c0, 2),  // big_y1_0
    (0x2b7, 0x1d4, 2),  // nor_x0_1
    (0x2b9, 0x1d8, 2),  // nor_x1_1
    (0x2bb, 0x1dc, 2),  // nor_y0_1
    (0x2bd, 0x1e0, 2),  // nor_y1_1
    (0x2d7, 0x1e4, 2),  // big_x0_1
    (0x2d9, 0x1e8, 2),  // big_x1_1
    (0x2db, 0x1ec, 2),  // big_y0_1
    (0x2dd, 0x1f0, 2),  // big_y1_1
    (0x2bf, 0x204, 2),  // nor_x0_2
    (0x2c1, 0x208, 2),  // nor_x1_2
    (0x2c3, 0x20c, 2),  // nor_y0_2
    (0x2c5, 0x210, 2),  // nor_y1_2
    (0x2df, 0x214, 2),  // big_x0_2
    (0x2e1, 0x218, 2),  // big_x1_2
    (0x2e3, 0x21c, 2),  // big_y0_2
    (0x2e5, 0x220, 2),  // big_y1_2
    (0x2c7, 0x234, 2),  // nor_x0_3
    (0x2c9, 0x238, 2),  // nor_x1_3
    (0x2cb, 0x23c, 2),  // nor_y0_3
    (0x2cd, 0x240, 2),  // nor_y1_3
    (0x2e7, 0x244, 2),  // big_x0_3
    (0x2e9, 0x248, 2),  // big_x1_3
    (0x2eb, 0x24c, 2),  // big_y0_3
    (0x2ed, 0x250, 2),  // big_y1_3
    (0x257, 0x5a, 6),   // pre_wbgain_inv_r through pre_wbgain_inv_b
    (0x11f, 0x3d, 1),   // multiwindow_en
    (0x2f1, 0x264, 2),  // multiwindow0_h_offs
    (0x2ef, 0x266, 2),  // multiwindow0_v_offs
    (0x2f9, 0x26c, 2),  // multiwindow1_h_offs
    (0x2f7, 0x26e, 2),  // multiwindow1_v_offs
    (0x301, 0x274, 2),  // multiwindow2_h_offs
    (0x2ff, 0x276, 2),  // multiwindow2_v_offs
    (0x309, 0x27c, 2),  // multiwindow3_h_offs
    (0x307, 0x27e, 2),  // multiwindow3_v_offs
    (0x10e, 0x28a, 1),  // exc_wp_region0_measen
    (0x10f, 0x284, 1),  // exc_wp_region0_domain
    (0x30f, 0x28c, 2),  // exc_wp_region0_xu0
    (0x311, 0x290, 2),  // exc_wp_region0_xu1
    (0x313, 0x294, 2),  // exc_wp_region0_yv0
    (0x315, 0x298, 2),  // exc_wp_region0_yv1
    (0x14e, 0x29c, 1),  // exc_wp_region0_weight
    (0x111, 0x2a6, 1),  // exc_wp_region1_measen
    (0x112, 0x2a0, 1),  // exc_wp_region1_domain
    (0x317, 0x2a8, 2),  // exc_wp_region1_xu0
    (0x319, 0x2ac, 2),  // exc_wp_region1_xu1
    (0x31b, 0x2b0, 2),  // exc_wp_region1_yv0
    (0x31d, 0x2b4, 2),  // exc_wp_region1_yv1
    (0x14f, 0x2b8, 1),  // exc_wp_region1_weight
    (0x114, 0x2c2, 1),  // exc_wp_region2_measen
    (0x115, 0x2bc, 1),  // exc_wp_region2_domain
    (0x31f, 0x2c4, 2),  // exc_wp_region2_xu0
    (0x321, 0x2c8, 2),  // exc_wp_region2_xu1
    (0x323, 0x2cc, 2),  // exc_wp_region2_yv0
    (0x325, 0x2d0, 2),  // exc_wp_region2_yv1
    (0x150, 0x2d4, 1),  // exc_wp_region2_weight
    (0x117, 0x2de, 1),  // exc_wp_region3_measen
    (0x118, 0x2d8, 1),  // exc_wp_region3_domain
    (0x327, 0x2e0, 2),  // exc_wp_region3_xu0
    (0x329, 0x2e4, 2),  // exc_wp_region3_xu1
    (0x32b, 0x2e8, 2),  // exc_wp_region3_yv0
    (0x32d, 0x2ec, 2),  // exc_wp_region3_yv1
    (0x151, 0x2f0, 1),  // exc_wp_region3_weight
    (0x11a, 0x2f4, 1),  // exc_wp_region4_domain
    (0x32f, 0x2fc, 2),  // exc_wp_region4_xu0
    (0x331, 0x300, 2),  // exc_wp_region4_xu1
    (0x333, 0x304, 2),  // exc_wp_region4_yv0
    (0x335, 0x308, 2),  // exc_wp_region4_yv1
    (0x152, 0x30c, 1),  // exc_wp_region4_weight
    (0x11c, 0x310, 1),  // exc_wp_region5_domain
    (0x337, 0x318, 2),  // exc_wp_region5_xu0
    (0x339, 0x31c, 2),  // exc_wp_region5_xu1
    (0x33b, 0x320, 2),  // exc_wp_region5_yv0
    (0x33d, 0x324, 2),  // exc_wp_region5_yv1
    (0x153, 0x328, 1),  // exc_wp_region5_weight
    (0x11e, 0x32c, 1),  // exc_wp_region6_domain
    (0x33f, 0x334, 2),  // exc_wp_region6_xu0
    (0x341, 0x338, 2),  // exc_wp_region6_xu1
    (0x343, 0x33c, 2),  // exc_wp_region6_yv0
    (0x345, 0x340, 2),  // exc_wp_region6_yv1
    (0x154, 0x344, 1),  // exc_wp_region6_weight
    (0x120, 0x348, 18), // wp_luma_weicurve_y0 through wp_luma_weicurve_w8
    (0x239, 0x3c, 1),   // blk_rtdw_measure_en
];
