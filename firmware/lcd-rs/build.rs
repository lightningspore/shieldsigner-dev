fn main() {
    if std::env::var("CARGO_CFG_TARGET_OS").as_deref() == Ok("linux")
        && std::env::var("CARGO_CFG_TARGET_ENV").as_deref() == Ok("uclibc")
    {
        println!("cargo:rustc-link-arg=-Wl,--wrap=getauxval");
    }
    if std::env::var_os("CARGO_FEATURE_PYTHON").is_some() {
        pyo3_build_config::add_extension_module_link_args();
    }
}
