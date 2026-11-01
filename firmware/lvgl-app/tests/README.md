# Test and fixture map

Audit snapshot: 2026-10-31. This directory has **153 test/fixture files**: 152 Python
files and one pinned SDK function fixture, plus this index. Python bytecode caches are excluded.
There are **60 `test_*.py` modules / 245 discoverable host cases** (Python 3.12,
Pillow 11.3.0, qrcode 7.3.1; zero discovery errors). This is a discovery count,
not an assertion that every standalone script is a host unit test.

## Choose a runner

| Layer | Entry point | Meaning and boundary |
|---|---|---|
| Host unit contracts | `mise run lvgl:app:test` | Imports/contracts, guards, cache invalidation, lifecycle and byte-equivalence fixtures; no board. Some read pinned sources under `dist/firmware/sources/lvgl/`. |
| Native host protocol | `mise run lvgl:app:build:host`, then `mise run lvgl:app:test:host` | Nine groups exercise renderer events/pixels on this computer; no camera, GPIO or physical panel claim. |
| ARM integration | `mise run lvgl:app:hardware --help` | Select one named case only after reviewing its scope and explicitly arranging device ownership. The runner temporarily deploys files and can use physical peripherals; it is not part of host discovery. |
| Packed image | `mise run firmware:verify` | Verifies frozen staged payloads, packed receipt and image hashes; does not repeat board tests or build/flash. |

Do not run every `.py` here as a batch. Standalone files commonly expect an ARM
installation at `/opt/src`, the camera extension, command arguments or temporary
renderer deployment. `hardware_check.py` is the authoritative dispatch table:
**139 named cases use 79 distinct scripts**, with multiple variants sharing scripts.
Eight scripts are also used by the native host groups; these counts overlap.

## Public fixture rules

- [multisig_fixture.py](multisig_fixture.py) carries a clearly marked upstream
  regtest 2-of-3 fixture, its original source SHA and deliberately public keys.
  Preserve its provenance; these are not user wallet material.
- [synthetic_frames.py](synthetic_frames.py) constructs public QR/NV12 pixels in
  memory. [qr_scan_fixtures.py](qr_scan_fixtures.py) injects only the camera source;
  success does not establish optical camera performance.
- [psbt_signing_flow.py](psbt_signing_flow.py) and
  [multisig_signing_flow.py](multisig_signing_flow.py) exercise public transaction
  fixtures. Signing/export evidence is distinct from the pending user's-wallet test.
- [experimental_entropy_samples.py](experimental_entropy_samples.py) and
  [entropy_sample_pixels.py](entropy_sample_pixels.py) are experimental comparison
  helpers, explicitly **not** the production entropy implementation. Keep them
  separate from production claims.
- [sdk-release-function.sh.txt](sdk-release-function.sh.txt) is a review fixture
  for an exact upstream SDK function, not a generated shell build log.
- Physical camera/entropy scripts may temporarily handle real frames. Keep their
  captures and fresh diagnostic logs in ignored `dist/firmware/checks/`, never here.

## Host unit module index

The module name describes the contract; inspect the assertions before expanding
its claim to a full user workflow.

- [test_address_search](test_address_search.py)
- [test_app_entry](test_app_entry.py)
- [test_battery_info](test_battery_info.py)
- [test_bytecode_cache](test_bytecode_cache.py)
- [test_calibration](test_calibration.py)
- [test_camera_iv](test_camera_iv.py)
- [test_camera_scan](test_camera_scan.py)
- [test_contracts](test_contracts.py)
- [test_dependency_policy](test_dependency_policy.py)
- [test_descriptor_contracts](test_descriptor_contracts.py)
- [test_diagnostic_scope](test_diagnostic_scope.py)
- [test_display_allocation](test_display_allocation.py)
- [test_display_handoff](test_display_handoff.py)
- [test_display_scaler](test_display_scaler.py)
- [test_display_window](test_display_window.py)
- [test_donate_contract](test_donate_contract.py)
- [test_encrypted_contracts](test_encrypted_contracts.py)
- [test_entropy_camera](test_entropy_camera.py)
- [test_entropy_fallback](test_entropy_fallback.py)
- [test_entropy_source](test_entropy_source.py)
- [test_explorer_contracts](test_explorer_contracts.py)
- [test_final_word_contracts](test_final_word_contracts.py)
- [test_grid_hold](test_grid_hold.py)
- [test_hardware_check](test_hardware_check.py)
- [test_home_battery](test_home_battery.py)
- [test_home_recovery](test_home_recovery.py)
- [test_image_stage](test_image_stage.py)
- [test_import_cache](test_import_cache.py)
- [test_info_contracts](test_info_contracts.py)
- [test_input_override](test_input_override.py)
- [test_io_capture](test_io_capture.py)
- [test_lazy_screens](test_lazy_screens.py)
- [test_lifecycle](test_lifecycle.py)
- [test_live_info](test_live_info.py)
- [test_loading](test_loading.py)
- [test_locale_assets](test_locale_assets.py)
- [test_locale_supplement](test_locale_supplement.py)
- [test_message_contracts](test_message_contracts.py)
- [test_microsd_lifecycle](test_microsd_lifecycle.py)
- [test_optional_imports](test_optional_imports.py)
- [test_overlay_apply](test_overlay_apply.py)
- [test_paged_info](test_paged_info.py)
- [test_power_contract](test_power_contract.py)
- [test_renderer_bridge](test_renderer_bridge.py)
- [test_resource_maps](test_resource_maps.py)
- [test_runtime](test_runtime.py)
- [test_screen_bridge](test_screen_bridge.py)
- [test_screensaver_bridge](test_screensaver_bridge.py)
- [test_sdk_strip](test_sdk_strip.py)
- [test_settingsqr_contract](test_settingsqr_contract.py)
- [test_slip39_lifecycle](test_slip39_lifecycle.py)
- [test_source_text](test_source_text.py)
- [test_startup_policy](test_startup_policy.py)
- [test_startup_splash](test_startup_splash.py)
- [test_stream_imports](test_stream_imports.py)
- [test_textqr_contracts](test_textqr_contracts.py)
- [test_toast_bridge](test_toast_bridge.py)
- [test_transcription](test_transcription.py)
- [test_transport](test_transport.py)
- [test_word_pagination](test_word_pagination.py)

## Native host group index

| Group | Script |
|---|---|
| `status` | [status_protocol.py](status_protocol.py) |
| `frames` | [frame_completion.py](frame_completion.py) |
| `geometry` | [display_geometry.py](display_geometry.py) |
| `preview` | [preview_protocol.py](preview_protocol.py) |
| `live-info` | [live_info_protocol.py](live_info_protocol.py) |
| `transcription` | [transcription_protocol.py](transcription_protocol.py) |
| `io` | [io_protocol.py](io_protocol.py) |
| `home-battery` | [home_battery_protocol.py](home_battery_protocol.py) |
| `corpus` | [native_smoke.py](native_smoke.py) |

## ARM case dispatch index

Named cases below are a lookup map, not instructions to execute them all. The
runner source specifies arguments and ownership checks.

| Script | Named cases |
|---|---|
| [app_entry_check.py](app_entry_check.py) | `app-entry-check` |
| [app_entry_flow.py](app_entry_flow.py) | `app-entry-settings-ui`, `app-entry-settings-flush`, `app-entry-sigterm-camera`, `app-entry-sigterm`, `app-entry-flow` |
| [backup_quiz_flow.py](backup_quiz_flow.py) | `backup-quiz` |
| [calibration_flow.py](calibration_flow.py) | `calibration` |
| [camera_flow.py](camera_flow.py) | `camera-memory-cycles`, `camera-long-soak`, `camera-loaded-soak`, `camera`, `camera-loaded` |
| [coin_flow.py](coin_flow.py) | `coin` |
| [controller_address.py](controller_address.py) | `controller-address-receive`, `controller-address-change` |
| [controller_bip85.py](controller_bip85.py) | `controller-bip85-18`, `controller-bip85-12`, `controller-bip85-24` |
| [controller_calibration_flow.py](controller_calibration_flow.py) | `controller-calibration-charging`, `controller-calibration` |
| [controller_camera_iv.py](controller_camera_iv.py) | `controller-encrypted-ecb-v1`, `controller-encrypted-ecb`, `controller-camera-encrypted-cbc-v1`, `controller-camera-encrypted-cbc`, `controller-camera-encrypted-ctr`, `controller-camera-encrypted-gcm`, `controller-camera-iv-cbc`, `controller-camera-iv-ctr`, `controller-camera-iv-gcm`, `controller-camera-iv-cancel-preview`, `controller-camera-iv-cancel-review` |
| [controller_entropy_flow.py](controller_entropy_flow.py) | `controller-entropy-generate`, `controller-entropy-luma`, `controller-entropy-gc`, `controller-entropy`, `controller-entropy-cancel` |
| [controller_flow.py](controller_flow.py) | `controller-home-battery`, `startup` |
| [controller_info_flow.py](controller_info_flow.py) | `controller-donate`, `controller-network-fixture`, `controller-network-absent`, `controller-hardening`, `controller-battery-fixture`, `controller-battery-absent`, `controller-memory-info`, `controller-version`, `controller-system-info` |
| [controller_io_flow.py](controller_io_flow.py) | `controller-io` |
| [controller_locale.py](controller_locale.py) | `controller-locale` |
| [controller_multisig_flow.py](controller_multisig_flow.py) | `controller-multisig-import-signer`, `controller-multisig-mismatch`, `controller-multisig-scan`, `controller-multisig-descriptor`, `controller-multisig-select-seed`, `controller-multisig-cancel`, `controller-multisig` |
| [controller_passphrase.py](controller_passphrase.py) | `controller-passphrase` |
| [controller_seed_scan.py](controller_seed_scan.py) | `controller-seed-scan-12`, `controller-seed-scan-24` |
| [controller_settingsqr_flow.py](controller_settingsqr_flow.py) | `controller-settingsqr-scan`, `controller-settingsqr`, `controller-settingsqr-cancel` |
| [controller_slip39.py](controller_slip39.py) | `controller-slip39-33`, `controller-slip39-20` |
| [controller_wallet_export.py](controller_wallet_export.py) | `controller-wallet-export` |
| [decoder_payloads.py](decoder_payloads.py) | `decoder-payloads` |
| [dependency_coin_flow.py](dependency_coin_flow.py) | `dependency-coin` |
| [dependency_cost.py](dependency_cost.py) | `dependency-cost` |
| [dependency_entropy_flow.py](dependency_entropy_flow.py) | `dependency-entropy-generate` |
| [dependency_hardware.py](dependency_hardware.py) | `dependency-closure` |
| [dependency_wallet_export.py](dependency_wallet_export.py) | `dependency-wallet-export` |
| [dependency_wallet_flow.py](dependency_wallet_flow.py) | `dependency-wallet-flow` |
| [descriptor_flow.py](descriptor_flow.py) | `descriptor` |
| [display_geometry.py](display_geometry.py) | `display-geometry` |
| [display_handoff.py](display_handoff.py) | `display-handoff` |
| [display_scaler_pipeline.py](display_scaler_pipeline.py) | `display-scaler-pipeline` |
| [display_spi_pipeline.py](display_spi_pipeline.py) | `display-spi-pipeline` |
| [encoder_payloads.py](encoder_payloads.py) | `encoder-payloads` |
| [encrypted_entry_flow.py](encrypted_entry_flow.py) | `encrypted-entry` |
| [encrypted_review_flow.py](encrypted_review_flow.py) | `encrypted-review` |
| [entropy_camera_hardware.py](entropy_camera_hardware.py) | `entropy-camera` |
| [entropy_fallback_hardware.py](entropy_fallback_hardware.py) | `entropy-fallback` |
| [entropy_sample_pixels.py](entropy_sample_pixels.py) | `entropy-sample-pixels` |
| [explorer_flow.py](explorer_flow.py) | `explorer` |
| [final_word_flow.py](final_word_flow.py) | `final-word` |
| [frame_completion.py](frame_completion.py) | `frame-completion` |
| [frontend_resources.py](frontend_resources.py) | `dependency-camera-eager-stream`, `dependency-camera-audit`, `dependency-audit`, `resources-lvgl-camera`, `resources-pil-camera`, `profile-lvgl-idle`, `resources-lvgl`, `resources-pil` |
| [grid_color.py](grid_color.py) | `grid-color` |
| [home_battery_protocol.py](home_battery_protocol.py) | `home-battery-protocol` |
| [image_entropy_flow.py](image_entropy_flow.py) | `image-entropy` |
| [image_entropy_physical.py](image_entropy_physical.py) | `image-entropy-control`, `image-entropy-physical` |
| [import_profile.py](import_profile.py) | `import-profile` |
| [input_latency.py](input_latency.py) | `input-latency` |
| [io_protocol.py](io_protocol.py) | `io-protocol` |
| [live_info_protocol.py](live_info_protocol.py) | `live-info-protocol` |
| [locale_native.py](locale_native.py) | `locale-native` |
| [message_signing_flow.py](message_signing_flow.py) | `message-signing` |
| [microsd_events.py](microsd_events.py) | `microsd-events` |
| [multisig_model.py](multisig_model.py) | `multisig-model` |
| [multisig_signing_flow.py](multisig_signing_flow.py) | `multisig-signing` |
| [nul_entry.py](nul_entry.py) | `nul-entry` |
| [passphrase_flow.py](passphrase_flow.py) | `nul-passphrase-flow` |
| [power_flow.py](power_flow.py) | `power-presentation` |
| [preview_faults.py](preview_faults.py) | `preview-faults` |
| [preview_protocol.py](preview_protocol.py) | `preview-protocol` |
| [preview_throughput.py](preview_throughput.py) | `preview-throughput` |
| [qr_output_flow.py](qr_output_flow.py) | `qr-export-memory-cycles` |
| [renderer_geometry.py](renderer_geometry.py) | `renderer-geometry` |
| [renderer_settings_ui.py](renderer_settings_ui.py) | `home-display-recovery`, `st7735-settings-ui`, `renderer-settings-ui` |
| [screensaver_flow.py](screensaver_flow.py) | `screensaver` |
| [seedqr_confirmation_flow.py](seedqr_confirmation_flow.py) | `seedqr-confirmation` |
| [settingsqr_flow.py](settingsqr_flow.py) | `settingsqr` |
| [source_cache_cost.py](source_cache_cost.py) | `source-cache-eviction`, `source-cache-cost` |
| [st7735_integration.py](st7735_integration.py) | `st7735-integration` |
| [status_protocol.py](status_protocol.py) | `status-protocol` |
| [textqr_flow.py](textqr_flow.py) | `textqr` |
| [textqr_more_flow.py](textqr_more_flow.py) | `textqr-output-confirm` |
| [transcription_flow.py](transcription_flow.py) | `transcription` |
| [transcription_protocol.py](transcription_protocol.py) | `transcription-protocol` |
| [transcription_registration.py](transcription_registration.py) | `transcription-registration` |
| [typing_import_audit.py](typing_import_audit.py) | `typing-import-audit` |
| [wallet_import_cost.py](wallet_import_cost.py) | `typing-import-cost`, `tools-import-cost`, `wallet-import-cost` |
| [wipe_flow.py](wipe_flow.py) | `io-wipe`, `entropy-wipe-timer`, `entropy-wipe` |

## Supporting and earlier direct harnesses

These 12 files are not directly selected by either current runner. Keep them for
fixture support or prior direct-screen evidence; inspect their imports/arguments
before use. Do not count them as currently wired acceptance cases.

- [address_search_flow.py](address_search_flow.py)
- [app_contract_smoke.py](app_contract_smoke.py)
- [experimental_entropy_samples.py](experimental_entropy_samples.py)
- [keyboard_flow.py](keyboard_flow.py)
- [multisig_fixture.py](multisig_fixture.py)
- [psbt_screen_flow.py](psbt_screen_flow.py)
- [psbt_signing_flow.py](psbt_signing_flow.py)
- [qr_scan_fixtures.py](qr_scan_fixtures.py)
- [seed_recovery_flow.py](seed_recovery_flow.py)
- [settings_flow.py](settings_flow.py)
- [synthetic_frames.py](synthetic_frames.py)
- [xpub_flow.py](xpub_flow.py)

See the [evidence index](../validation/README.md) for outcomes and limitations,
and the [source inventory](../../../docs/FIRMWARE-SOURCE-INVENTORY.md) for privacy
and checkpoint boundaries.
