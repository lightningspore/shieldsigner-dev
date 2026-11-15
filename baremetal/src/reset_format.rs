// SPDX-License-Identifier: MIT
//! Fixed numeric reset evidence; checksum detects damage, not an authentication tag.
pub const WORDS:usize=16;
pub const MAGIC:u32=0x53465231;
pub const VERSION:u32=1;
pub fn checksum(words:&[u32;WORDS])->u32 {
    words[1..13].iter().fold(0x811c9dc5,|sum,value|(sum^value).wrapping_mul(0x01000193))
}
pub fn valid(words:&[u32;WORDS])->bool {
    words[0]==MAGIC && words[1]==VERSION && words[14]==!MAGIC && words[15]==0 && words[13]==checksum(words)
}
#[cfg(test)]
mod tests {
    use super::*;
    fn record()->[u32;WORDS]{let mut w=[0;WORDS];w[0]=MAGIC;w[1]=VERSION;w[2]=5;w[3]=123;w[8]=0x01a00000;w[14]=!MAGIC;w[13]=checksum(&w);w}
    #[test] fn valid_numeric_record(){assert!(valid(&record()));}
    #[test] fn every_single_word_corruption_rejected(){for i in 0..WORDS{let mut w=record();w[i]^=1;assert!(!valid(&w),"word{}",i);}}
    #[test] fn uncommitted_or_zero_record_rejected(){assert!(!valid(&[0;WORDS]));let mut w=record();w[0]=0;assert!(!valid(&w));}
    #[test] fn different_version_rejected_even_with_checksum(){let mut w=record();w[1]+=1;w[13]=checksum(&w);assert!(!valid(&w));}
}
