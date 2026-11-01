# Migration coverage inventory

Pinned app: `efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f`.

87 screen classes; 966 statically resolved view calls; 43 reusable upstream LVGL screen builders.

Candidate matches are names only, not compatibility or migration claims. Top-level Screen classes across the application are included; nested classes and dynamic calls require separate auditing. Scoped validation receipts remain separate from adapter status.

Evidence links below are historical scoped receipts with exact source/binary hashes, not qualification of every flow using a shared screen.

| App screen | Upstream candidate | Status | Scoped evidence |
|---|---|---|---|
| AddressVerificationSigTypeScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| BaseScreen | needs explicit mapping | inherited infrastructure; concrete adapters own rendering/lifecycle; no direct static View call |  |
| BaseTopNavScreen | needs explicit mapping | inherited infrastructure; concrete adapters own rendering/lifecycle; no direct static View call |  |
| BatteryInfoScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| ButtonListScreen | button_list_screen | adapter implemented; flow unverified |  |
| DireWarningScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| DonateScreen | donate_screen | adapter implemented; flow unverified |  |
| ErrorScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| HardeningTestScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| IOTestScreen | io_test_screen | adapter implemented; flow unverified |  |
| KeyboardScreen | keyboard_screen | adapter implemented; flow unverified |  |
| LargeButtonScreen | needs explicit mapping | grid adapter; scoped ARM navigation/tap/hold passed; custom styles incomplete; default/custom selected-color pixels and Right/Select passed on LCD; arbitrary custom fonts remain unqualified | [grid-color-arm](validation/grid-color-arm.json) |
| LargeIconStatusScreen | large_icon_status_screen | adapter implemented; full Controller static native-segwit xpub export/pixel decode/address handshake passed; other export formats not qualified by this receipt | [controller-wallet-export-arm](validation/controller-wallet-export-arm.json) |
| LoadMultisigWalletDescriptorScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| LogoScreen | needs explicit mapping | inherited infrastructure; concrete adapters own rendering/lifecycle; no direct static View call |  |
| MainMenuScreen | main_menu_screen | navigation/recovery-hold/battery adapters; scoped ARM/Controller display switching passed with LCD fixtures; physical battery and alternate LCD qualification incomplete; default/custom selected-color pixels and Right/Select passed on LCD; arbitrary custom fonts remain unqualified | [grid-color-arm](validation/grid-color-arm.json) |
| MemoryInfoScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| MultisigWalletDescriptorScreen | multisig_wallet_descriptor_screen | adapter implemented; flow unverified |  |
| OpeningSplashScreen | opening_splash_screen | adapter implemented; flow unverified |  |
| PSBTAddressDetailsScreen | psbt_address_details_screen | adapter implemented; flow unverified |  |
| PSBTChangeDetailsScreen | psbt_change_details_screen | adapter implemented; flow unverified |  |
| PSBTFinalizeScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| PSBTMathScreen | psbt_math_screen | adapter implemented; flow unverified |  |
| PSBTOpReturnScreen | psbt_op_return_screen | adapter implemented; flow unverified |  |
| PSBTOverviewScreen | psbt_overview_screen | adapter implemented; flow unverified |  |
| PagedTextScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| PowerOffNotRequiredScreen | power_off_not_required_screen | adapter implemented; flow unverified |  |
| QRDisplayScreen | qr_display_screen | adapter implemented; Controller encrypted export and original-View decrypt passed for strict KEF 0/1/6 fixtures; not optical import qualification; full Controller static native-segwit xpub export/pixel decode/address handshake passed; other export formats not qualified by this receipt | [controller-camera-encrypted-cbc-v1-arm](validation/controller-camera-encrypted-cbc-v1-arm.json), [controller-encrypted-ecb-v1-arm](validation/controller-encrypted-ecb-v1-arm.json), [controller-encrypted-ecb-arm](validation/controller-encrypted-ecb-arm.json), [controller-wallet-export-arm](validation/controller-wallet-export-arm.json) |
| RebootToLoaderScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| ResetScreen | reset_screen | adapter implemented; flow unverified |  |
| ScanAmbiguousQRScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| ScanEncryptedQRScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| ScanReviewEncryptionKeyScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| ScanScreen | needs explicit mapping | adapter implemented; SLIP39 2-of-2 QR recovery/review/quiz passed for 20/33-word shares on LCD; synthetic frames, not optical qualification; full Controller seed/passphrase scan, edit/review/save and finalize passed with public NUL/Unicode fixture; synthetic QR input | [controller-slip39-20-arm](validation/controller-slip39-20-arm.json), [controller-slip39-33-arm](validation/controller-slip39-33-arm.json), [controller-passphrase-arm](validation/controller-passphrase-arm.json) |
| ScanTypeEncryptionKeyScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| ScreensaverScreen | screensaver_screen | native lifecycle adapter; see scoped validation |  |
| SeedAddPassphraseScreen | seed_add_passphrase_screen | adapter implemented; full Controller seed/passphrase scan, edit/review/save and finalize passed with public NUL/Unicode fixture; synthetic QR input | [controller-passphrase-arm](validation/controller-passphrase-arm.json) |
| SeedAddressVerificationScreen | seed_address_verification_screen | adapter implemented; full Controller imported-seed address verification passed for native-segwit receive/change index 7; other scripts and expanded search not qualified by these checks | [controller-address-receive-arm](validation/controller-address-receive-arm.json), [controller-address-change-arm](validation/controller-address-change-arm.json) |
| SeedAddressVerificationSuccessScreen | seed_address_verification_success_screen | adapter implemented; full Controller imported-seed address verification passed for native-segwit receive/change index 7; other scripts and expanded search not qualified by these checks | [controller-address-receive-arm](validation/controller-address-receive-arm.json), [controller-address-change-arm](validation/controller-address-change-arm.json) |
| SeedBIP85SelectChildIndexScreen | needs explicit mapping | adapter implemented; BIP85 child-index-0 review/quiz/finalize passed for 12/18/24 words on LCD; other flows not qualified by these checks | [controller-bip85-12-arm](validation/controller-bip85-12-arm.json), [controller-bip85-18-arm](validation/controller-bip85-18-arm.json), [controller-bip85-24-arm](validation/controller-bip85-24-arm.json) |
| SeedEncryptedQRMnemonicIDScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| SeedEncryptedQRReviewMnemonicIDScreen | needs explicit mapping | adapter implemented; Controller encrypted export and original-View decrypt passed for strict KEF 0/1/6 fixtures; not optical import qualification | [controller-camera-encrypted-cbc-v1-arm](validation/controller-camera-encrypted-cbc-v1-arm.json), [controller-encrypted-ecb-v1-arm](validation/controller-encrypted-ecb-v1-arm.json), [controller-encrypted-ecb-arm](validation/controller-encrypted-ecb-arm.json) |
| SeedEncryptedQRTranscribeModePromptScreen | needs explicit mapping | adapter implemented; Controller encrypted export and original-View decrypt passed for strict KEF 0/1/6 fixtures; not optical import qualification | [controller-camera-encrypted-cbc-v1-arm](validation/controller-camera-encrypted-cbc-v1-arm.json), [controller-encrypted-ecb-v1-arm](validation/controller-encrypted-ecb-v1-arm.json), [controller-encrypted-ecb-arm](validation/controller-encrypted-ecb-arm.json) |
| SeedExportXpubAccountNumberScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| SeedExportXpubCustomDerivationScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| SeedExportXpubDetailsScreen | seed_export_xpub_details_screen | adapter implemented; full Controller static native-segwit xpub export/pixel decode/address handshake passed; other export formats not qualified by this receipt | [controller-wallet-export-arm](validation/controller-wallet-export-arm.json) |
| SeedFinalizeScreen | seed_finalize_screen | adapter implemented; BIP85 child-index-0 review/quiz/finalize passed for 12/18/24 words on LCD; other flows not qualified by these checks; SLIP39 2-of-2 QR recovery/review/quiz passed for 20/33-word shares on LCD; synthetic frames, not optical qualification; full Controller seed/passphrase scan, edit/review/save and finalize passed with public NUL/Unicode fixture; synthetic QR input | [controller-bip85-12-arm](validation/controller-bip85-12-arm.json), [controller-bip85-18-arm](validation/controller-bip85-18-arm.json), [controller-bip85-24-arm](validation/controller-bip85-24-arm.json), [controller-slip39-20-arm](validation/controller-slip39-20-arm.json), [controller-slip39-33-arm](validation/controller-slip39-33-arm.json), [controller-passphrase-arm](validation/controller-passphrase-arm.json) |
| SeedMnemonicEntryScreen | seed_mnemonic_entry_screen | adapter implemented; flow unverified |  |
| SeedOptionsScreen | needs explicit mapping | adapter implemented; BIP85 child-index-0 review/quiz/finalize passed for 12/18/24 words on LCD; other flows not qualified by these checks; SLIP39 2-of-2 QR recovery/review/quiz passed for 20/33-word shares on LCD; synthetic frames, not optical qualification; full Controller seed/passphrase scan, edit/review/save and finalize passed with public NUL/Unicode fixture; synthetic QR input | [controller-bip85-12-arm](validation/controller-bip85-12-arm.json), [controller-bip85-18-arm](validation/controller-bip85-18-arm.json), [controller-bip85-24-arm](validation/controller-bip85-24-arm.json), [controller-slip39-20-arm](validation/controller-slip39-20-arm.json), [controller-slip39-33-arm](validation/controller-slip39-33-arm.json), [controller-passphrase-arm](validation/controller-passphrase-arm.json) |
| SeedReviewPassphraseScreen | seed_review_passphrase_screen | adapter implemented; full Controller seed/passphrase scan, edit/review/save and finalize passed with public NUL/Unicode fixture; synthetic QR input | [controller-passphrase-arm](validation/controller-passphrase-arm.json) |
| SeedSelectSeedScreen | needs explicit mapping | adapter implemented; full Controller imported-seed address verification passed for native-segwit receive/change index 7; other scripts and expanded search not qualified by these checks | [controller-address-receive-arm](validation/controller-address-receive-arm.json), [controller-address-change-arm](validation/controller-address-change-arm.json) |
| SeedSignMessageConfirmAddressScreen | seed_sign_message_confirm_address_screen | adapter implemented; flow unverified |  |
| SeedSignMessageConfirmMessageScreen | seed_sign_message_confirm_message_screen | adapter implemented; flow unverified |  |
| SeedTranscribeEncryptedQRWholeQRScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| SeedTranscribeEncryptedQRZoomedInScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| SeedTranscribeSeedQRConfirmQRPromptScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| SeedTranscribeSeedQRFormatScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| SeedTranscribeSeedQRWholeQRScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| SeedTranscribeSeedQRZoomedInScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| SeedWordsBackupTestPromptScreen | needs explicit mapping | adapter implemented; BIP85 child-index-0 review/quiz/finalize passed for 12/18/24 words on LCD; other flows not qualified by these checks; SLIP39 2-of-2 QR recovery/review/quiz passed for 20/33-word shares on LCD; synthetic frames, not optical qualification | [controller-bip85-12-arm](validation/controller-bip85-12-arm.json), [controller-bip85-18-arm](validation/controller-bip85-18-arm.json), [controller-bip85-24-arm](validation/controller-bip85-24-arm.json), [controller-slip39-20-arm](validation/controller-slip39-20-arm.json), [controller-slip39-33-arm](validation/controller-slip39-33-arm.json) |
| SeedWordsScreen | seed_words_screen | adapter implemented; BIP85 child-index-0 review/quiz/finalize passed for 12/18/24 words on LCD; other flows not qualified by these checks; SLIP39 2-of-2 QR recovery/review/quiz passed for 20/33-word shares on LCD; synthetic frames, not optical qualification | [controller-bip85-12-arm](validation/controller-bip85-12-arm.json), [controller-bip85-18-arm](validation/controller-bip85-18-arm.json), [controller-bip85-24-arm](validation/controller-bip85-24-arm.json), [controller-slip39-20-arm](validation/controller-slip39-20-arm.json), [controller-slip39-33-arm](validation/controller-slip39-33-arm.json) |
| SettingPBFDK2IterationsScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| SettingsEntryUpdateSelectionScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| SettingsQRConfirmationScreen | settings_qr_confirmation_screen | adapter implemented; flow unverified |  |
| SettingsQRReviewScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| SystemInfoScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| ToolsAddressExplorerAddressListScreen | tools_address_explorer_address_list_screen | adapter implemented; flow unverified |  |
| ToolsAddressExplorerAddressTypeScreen | tools_address_explorer_address_type_screen | adapter implemented; flow unverified |  |
| ToolsBatteryCalibrationIntroScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| ToolsBatteryCalibrationRunningScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| ToolsBatteryCalibrationStartScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| ToolsCalcFinalWordDoneScreen | tools_calc_final_word_done_screen | adapter implemented; flow unverified |  |
| ToolsCalcFinalWordFinalizePromptScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| ToolsCalcFinalWordScreen | tools_calc_final_word_screen | adapter implemented; flow unverified |  |
| ToolsCoinFlipEntryScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| ToolsDiceEntropyEntryScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| ToolsImageEntropyFinalImageScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| ToolsImageEntropyLivePreviewScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| ToolsNetworkInfoScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| ToolsTextQRReviewTextScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| ToolsTextQRTextEntryScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| ToolsTextQRTranscribeModePromptScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| ToolsTranscribeTextQRConfirmQRPromptScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| ToolsTranscribeTextQRWholeQRScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| ToolsTranscribeTextQRZoomedInScreen | needs explicit mapping | adapter implemented; flow unverified |  |
| VersionScreen | version_screen | adapter implemented; flow unverified |  |
| WarningScreen | needs explicit mapping | adapter implemented; flow unverified |  |
