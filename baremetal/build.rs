// SPDX-License-Identifier: MIT
fn main() {
    println!("cargo:rerun-if-changed=build.rs");
    if std::env::var_os("CARGO_FEATURE_RUNTIME_REPL").is_some() {
        let root = std::path::PathBuf::from(std::env::var_os("CARGO_MANIFEST_DIR").unwrap());
        let path = if std::env::var_os("CARGO_FEATURE_RUNTIME_BOARD").is_some() {
            "build/micropython-board"
        } else {
            "build/micropython"
        };
        println!(
            "cargo:rustc-link-search=native={}",
            root.join(path).display()
        );
        println!("cargo:rustc-link-lib=static=micropython");
        println!("cargo:rerun-if-changed={}/libmicropython.a", path);
    }
}
