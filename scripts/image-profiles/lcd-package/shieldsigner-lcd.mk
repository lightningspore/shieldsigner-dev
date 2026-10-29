################################################################################
# Local immutable, Cargo-vendored ShieldSigner LCD inputs; no build-time network.
################################################################################
SHIELDSIGNER_LCD_VERSION = @LCD_SOURCE_SHA256@
SHIELDSIGNER_LCD_SITE = /build/shieldsigner-camera/lcd-source
SHIELDSIGNER_LCD_SITE_METHOD = local
SHIELDSIGNER_LCD_LICENSE = MIT, Apache-2.0 or MIT (Rust and vendored dependencies)
SHIELDSIGNER_LCD_LICENSE_FILES = LICENSE
SHIELDSIGNER_LCD_DEPENDENCIES = host-rust python3

define SHIELDSIGNER_LCD_BUILD_CMDS
	test "$(RUSTC_TARGET_NAME)" = armv7-unknown-linux-uclibceabihf
	cd $(@D) && $(TARGET_MAKE_ENV) $(TARGET_CONFIGURE_OPTS) $(PKG_CARGO_ENV) \
		PYO3_NO_PYTHON=1 CARGO_TARGET_DIR=$(@D)/target \
		CARGO_PROFILE_RELEASE_OPT_LEVEL=s CARGO_PROFILE_RELEASE_LTO=true \
		CARGO_PROFILE_RELEASE_CODEGEN_UNITS=1 \
		RUSTFLAGS="-C link-arg=--sysroot=$(STAGING_DIR) -C target-cpu=cortex-a7" \
		CARGO_TARGET_ARMV7_UNKNOWN_LINUX_UCLIBCEABIHF_RUSTFLAGS="-C link-arg=--sysroot=$(STAGING_DIR) -C target-cpu=cortex-a7" \
		cargo build --locked --offline --release --features python \
		--target armv7-unknown-linux-uclibceabihf
endef

define SHIELDSIGNER_LCD_INSTALL_TARGET_CMDS
	$(INSTALL) -D -m 0644 $(@D)/target/armv7-unknown-linux-uclibceabihf/release/libshieldsigner_lcd.so \
		$(TARGET_DIR)/usr/lib/shieldsigner-camera/python/shieldsigner_lcd.abi3.so
	$(INSTALL) -D -m 0644 $(@D)/python/shieldsigner_lcd_driver.py \
		$(TARGET_DIR)/usr/lib/shieldsigner-camera/python/shieldsigner_lcd_driver.py
	$(HOST_DIR)/bin/python3 /build/shieldsigner-camera/lcd-image-profile.py \
		--record-build $(@D) --rootfs $(TARGET_DIR) \
		--cc "$(TARGET_CC)" --rustc $(HOST_DIR)/bin/rustc
endef

$(eval $(generic-package))
