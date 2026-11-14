// SPDX-License-Identifier: MIT
#[cfg(not(feature = "reclaiming-heap"))]
#[path = "heap_bump.rs"]
mod implementation;
#[cfg(feature = "reclaiming-heap")]
#[path = "heap_reclaim.rs"]
mod implementation;
pub use implementation::*;
