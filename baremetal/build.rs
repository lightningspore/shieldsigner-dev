// SPDX-License-Identifier: MIT
fn main() {
    println!("cargo:rerun-if-changed=build.rs");
    let root = std::path::PathBuf::from(std::env::var_os("CARGO_MANIFEST_DIR").unwrap());
    let ui = std::env::var_os("CARGO_FEATURE_NATIVE_UI").is_some();
    let script = if ui {"link-ui.ld"} else {"link.ld"};
    println!("cargo:rustc-link-arg=-T{}", root.join(script).display());
    println!("cargo:rerun-if-changed={}",script);
    if ui {
        // GNU bare-metal EHABI type tables use relative TARGET2 relocations.
        // LLD defaults to Linux GOT-relative, incompatible with this libgcc.
        println!("cargo:rustc-link-arg=--target2=rel");
        let tools=root.join(".tools/arm-gnu-toolchain-14.3.rel1-darwin-arm64-arm-none-eabi/bin/arm-none-eabi-g++");
        println!("cargo:rustc-link-search=native={}",root.join("build/ui").display());
        println!("cargo:rustc-link-lib=static=signerui");
        println!("cargo:rerun-if-changed=build/ui/libsignerui.a");
        for name in ["stdc++", "m", "c", "gcc"] {
            let output=std::process::Command::new(&tools).args(["-mthumb","-mcpu=cortex-a7","-mfloat-abi=soft",&format!("-print-file-name=lib{}.a",name)]).output().expect("Run baremetal:cxx:setup");
            assert!(output.status.success());
            let path=std::path::PathBuf::from(String::from_utf8(output.stdout).unwrap().trim());
            assert!(path.is_file(),"Missing runtime {}",name);
            println!("cargo:rustc-link-search=native={}",path.parent().unwrap().display());
            println!("cargo:rustc-link-lib=static={}",name);
        }
    }
    if std::env::var_os("CARGO_FEATURE_RUNTIME_REPL").is_some() {
        let root = std::path::PathBuf::from(std::env::var_os("CARGO_MANIFEST_DIR").unwrap());
        let path = if ui {
            "build/micropython-ui"
        } else if std::env::var_os("CARGO_FEATURE_RUNTIME_BOARD").is_some() {
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
