# Validation evidence index

Audit snapshot: 2026-10-31. **295 JSON receipts** are retained: **248** have
`passed: true`, **29** have `passed: false`, and **18** have no top-level `passed`.
The last group includes structured packed-image verification and notice audits;
absence of that field is neither an automatic failure nor a pass. Every JSON
file parsed successfully. No receipt was rewritten, moved or deleted for this index.

## Start here

- [image-memory-cleanup-built.json](image-memory-cleanup-built.json) binds the
  built image to runtime manifest `cb6170a37a5a…`. Its `flashed` / boot fields
  describe the build-time claim and are intentionally not rewritten after later use.
- [image-memory-cleanup-packed.json](image-memory-cleanup-packed.json) records
  packed rootfs/profile checks and ARM userspace QEMU smoke checks. Its
  `imageBootQualified: false` is deliberate: userspace QEMU is not physical boot.
- [memory-cleanup-acceptance.json](memory-cleanup-acceptance.json) maps memory
  requirements to receipts and documents limits; it is not production qualification.
- [memory-cleanup-summary.json](memory-cleanup-summary.json) compares named
  workloads. [packaged-source-cache-memory-summary.json](packaged-source-cache-memory-summary.json)
  covers the cache behavior actually staged in the image.
- [notice-audit-host.json](notice-audit-host.json) and
  [../licenses/README.txt](../licenses/README.txt) retain unresolved license gaps;
  `licenseClosureVerified: false` must not become a release-clearance claim.

The current user-facing artifact is selected by `mise run firmware:where` and
verified by `mise run firmware:verify`. Its immutable source is
`dist/firmware/images/lvgl-dev.cb6170a37a5a/`; the later user report of boot/UI/camera
success is kept separately in `acceptance.json` there. The user's own-wallet
acceptance remains pending. Do not infer image qualification from the newest
receipt or from all-green public fixtures.

## Reading and maintaining receipts

`-host` means host evidence; `-arm` identifies an ARM-side run, but can still use
synthetic pixels or injected button events. Read `scope`, fixture substitutions,
`check`, `result`, exit/timing fields and build/bundle hashes inside each receipt.
A passing test only supports its named conditions. Before/after memory comparisons
must use matching workloads and metric definitions; RSS alone does not measure
private RAM plus swap.

The tables below list every receipt exactly once. **Pass/fail** is only the literal
top-level `passed` field; **structured** means inspect the receipt's own verification
fields. Baseline grouping is a navigation aid, not an assertion that all these
runs share a binary or that historical tests were rerun after cleanup.

New raw runs go to ignored `dist/firmware/checks/lvgl/{host,hardware}/`. Copy a
curated receipt here only after checking fixture provenance and logs for private
camera pixels, mnemonics, passphrases, wallet identifiers, paths and credentials.
Keep original failures beside successful fixes; add interpretation in docs rather
than changing their outcome. Historical `dist/lvgl-app` / `dist/os` strings remain
original evidence, currently supported by compatibility aliases; do not rewrite
old build identities when aliases are eventually retired.

## Baseline build and memory-cleanup evidence

16 receipts.

| Receipt | Recorded result |
|---|---|
| [image-memory-cleanup-built.json](image-memory-cleanup-built.json) | pass |
| [image-memory-cleanup-packed.json](image-memory-cleanup-packed.json) | structured |
| [memory-cleanup-acceptance.json](memory-cleanup-acceptance.json) | pass |
| [memory-cleanup-camera-arm.json](memory-cleanup-camera-arm.json) | pass |
| [memory-cleanup-camera-encryption-arm.json](memory-cleanup-camera-encryption-arm.json) | pass |
| [memory-cleanup-current-home-arm.json](memory-cleanup-current-home-arm.json) | pass |
| [memory-cleanup-slip39-arm.json](memory-cleanup-slip39-arm.json) | pass |
| [memory-cleanup-summary.json](memory-cleanup-summary.json) | pass |
| [memory-cleanup-uncached-regression-arm.json](memory-cleanup-uncached-regression-arm.json) | pass |
| [memory-cleanup-wallet-arm.json](memory-cleanup-wallet-arm.json) | pass |
| [packaged-entry-default-cache-arm.json](packaged-entry-default-cache-arm.json) | pass |
| [packaged-source-cache-after-arm.json](packaged-source-cache-after-arm.json) | pass |
| [packaged-source-cache-entropy-arm.json](packaged-source-cache-entropy-arm.json) | pass |
| [packaged-source-cache-memory-summary.json](packaged-source-cache-memory-summary.json) | pass |
| [packaged-source-cache-settings-arm.json](packaged-source-cache-settings-arm.json) | pass |
| [packaged-source-cache-wallet-arm.json](packaged-source-cache-wallet-arm.json) | pass |

## Failures and investigations (preserve)

31 receipts.

| Receipt | Recorded result |
|---|---|
| [app-entry-microsd-shutdown-failure-arm.json](app-entry-microsd-shutdown-failure-arm.json) | fail |
| [app-entry-sigterm-camera-initial-failure-arm.json](app-entry-sigterm-camera-initial-failure-arm.json) | fail |
| [calibration-intentional-timeout-arm.json](calibration-intentional-timeout-arm.json) | fail |
| [controller-entropy-failure-arm.json](controller-entropy-failure-arm.json) | fail |
| [controller-entropy-gc-experiment-arm.json](controller-entropy-gc-experiment-arm.json) | fail |
| [controller-entropy-luma-experiment-arm.json](controller-entropy-luma-experiment-arm.json) | fail |
| [controller-multisig-descriptor-menu-failure-arm.json](controller-multisig-descriptor-menu-failure-arm.json) | fail |
| [controller-multisig-descriptor-option-failure-arm.json](controller-multisig-descriptor-option-failure-arm.json) | fail |
| [controller-multisig-scan-history-failure-arm.json](controller-multisig-scan-history-failure-arm.json) | fail |
| [controller-passphrase-initial-fixture-failure-arm.json](controller-passphrase-initial-fixture-failure-arm.json) | fail |
| [controller-slip39-33-initial-wipe-failure-arm.json](controller-slip39-33-initial-wipe-failure-arm.json) | fail |
| [dependency-slip39-initial-inspection-failure-arm.json](dependency-slip39-initial-inspection-failure-arm.json) | fail |
| [encrypted-entry-initial-timeout-arm.json](encrypted-entry-initial-timeout-arm.json) | fail |
| [entropy-diagnostic-memory-failure.json](entropy-diagnostic-memory-failure.json) | structured |
| [entropy-sampling-experiments.json](entropy-sampling-experiments.json) | pass |
| [grid-back-navigation-failure-arm.json](grid-back-navigation-failure-arm.json) | fail |
| [grid-wake-disabled-saver-failure-arm.json](grid-wake-disabled-saver-failure-arm.json) | fail |
| [grid-wake-hold-initial-failure-arm.json](grid-wake-hold-initial-failure-arm.json) | fail |
| [home-battery-fixture-initialization-failure-arm.json](home-battery-fixture-initialization-failure-arm.json) | fail |
| [home-battery-fixture-thread-status-failure-arm.json](home-battery-fixture-thread-status-failure-arm.json) | fail |
| [image-entropy-initial-failures-arm.json](image-entropy-initial-failures-arm.json) | fail |
| [image-entropy-physical-failure-arm.json](image-entropy-physical-failure-arm.json) | fail |
| [lazy-screens-camera-failure-arm.json](lazy-screens-camera-failure-arm.json) | fail |
| [network-initial-navigation-failure-arm.json](network-initial-navigation-failure-arm.json) | fail |
| [parser-import-initial-refusal-fixture-failure-arm.json](parser-import-initial-refusal-fixture-failure-arm.json) | fail |
| [renderer-settings-history-failure-arm.json](renderer-settings-history-failure-arm.json) | fail |
| [resources-lvgl-camera-short-input-failure-arm.json](resources-lvgl-camera-short-input-failure-arm.json) | fail |
| [resources-pil-camera-baseline-setup-failure-arm.json](resources-pil-camera-baseline-setup-failure-arm.json) | fail |
| [userdata-bundle-camera-failure-arm.json](userdata-bundle-camera-failure-arm.json) | fail |
| [wipe-camera-baseline-home-failure-arm.json](wipe-camera-baseline-home-failure-arm.json) | fail |
| [wipe-camera-failure-arm.json](wipe-camera-failure-arm.json) | fail |

## Host renderer, staging and notice evidence

14 receipts.

| Receipt | Recorded result |
|---|---|
| [image-candidate-01-staging-host.json](image-candidate-01-staging-host.json) | pass |
| [image-overlay-draft-host.json](image-overlay-draft-host.json) | pass |
| [locale-assets-host.json](locale-assets-host.json) | structured |
| [locale-supplement-host.json](locale-supplement-host.json) | pass |
| [lvgl-sdk-hooks-host.json](lvgl-sdk-hooks-host.json) | pass |
| [native-corpus-host.json](native-corpus-host.json) | pass |
| [native-grid-color-host.json](native-grid-color-host.json) | pass |
| [native-preview-host.json](native-preview-host.json) | pass |
| [native-protocol-host.json](native-protocol-host.json) | pass |
| [notice-audit-host.json](notice-audit-host.json) | structured |
| [notice-stage-host.json](notice-stage-host.json) | pass |
| [overlay-apply-host.json](overlay-apply-host.json) | pass |
| [runtime-slip39-stage-host.json](runtime-slip39-stage-host.json) | pass |
| [runtime-stage-host.json](runtime-stage-host.json) | structured |

## Resource and dependency history

73 receipts.

| Receipt | Recorded result |
|---|---|
| [checked-bytecode-import-arm.json](checked-bytecode-import-arm.json) | pass |
| [controller-memory-info-arm.json](controller-memory-info-arm.json) | pass |
| [controller-multisig-import-signer-arm.json](controller-multisig-import-signer-arm.json) | pass |
| [decimal-import-after-arm.json](decimal-import-after-arm.json) | pass |
| [decimal-import-before-arm.json](decimal-import-before-arm.json) | pass |
| [decimal-import-memory-summary.json](decimal-import-memory-summary.json) | pass |
| [decimal-import-wallet-flow-arm.json](decimal-import-wallet-flow-arm.json) | pass |
| [dependency-audit-after-arm.json](dependency-audit-after-arm.json) | pass |
| [dependency-audit-before-arm.json](dependency-audit-before-arm.json) | pass |
| [dependency-cleanup-wallet-flow-arm.json](dependency-cleanup-wallet-flow-arm.json) | pass |
| [dependency-closure-arm.json](dependency-closure-arm.json) | pass |
| [dependency-font-audit-arm.json](dependency-font-audit-arm.json) | pass |
| [dependency-import-cost-arm.json](dependency-import-cost-arm.json) | pass |
| [dependency-removal-first-pair.json](dependency-removal-first-pair.json) | pass |
| [dependency-slip39-recovery-arm.json](dependency-slip39-recovery-arm.json) | pass |
| [dependency-wallet-flow-arm.json](dependency-wallet-flow-arm.json) | pass |
| [dependency-wallet-flow-nul-current-arm.json](dependency-wallet-flow-nul-current-arm.json) | pass |
| [encoder-import-after-arm.json](encoder-import-after-arm.json) | pass |
| [encoder-import-memory-summary.json](encoder-import-memory-summary.json) | pass |
| [encoder-import-payloads-arm.json](encoder-import-payloads-arm.json) | pass |
| [encoder-import-wallet-export-arm.json](encoder-import-wallet-export-arm.json) | pass |
| [image-entropy-resources-arm.json](image-entropy-resources-arm.json) | pass |
| [import-profile-arm.json](import-profile-arm.json) | pass |
| [interactive-python-memory-maps.json](interactive-python-memory-maps.json) | structured |
| [native-preview-memory-summary.json](native-preview-memory-summary.json) | pass |
| [packaged-entry-prepared-control-arm.json](packaged-entry-prepared-control-arm.json) | pass |
| [packaged-source-cache-before-arm.json](packaged-source-cache-before-arm.json) | pass |
| [parser-import-memory-summary.json](parser-import-memory-summary.json) | pass |
| [parser-import-payloads-arm.json](parser-import-payloads-arm.json) | pass |
| [parser-import-scan-after-arm.json](parser-import-scan-after-arm.json) | pass |
| [parser-import-scan-before-arm.json](parser-import-scan-before-arm.json) | pass |
| [parser-import-wallet-arm.json](parser-import-wallet-arm.json) | pass |
| [preview-throughput-arm.json](preview-throughput-arm.json) | pass |
| [preview-throughput-batched-spi-arm.json](preview-throughput-batched-spi-arm.json) | pass |
| [resources-lvgl-arm.json](resources-lvgl-arm.json) | pass |
| [resources-lvgl-camera-arm.json](resources-lvgl-camera-arm.json) | pass |
| [resources-lvgl-camera-batched-spi-arm.json](resources-lvgl-camera-batched-spi-arm.json) | pass |
| [resources-lvgl-camera-current-a-arm.json](resources-lvgl-camera-current-a-arm.json) | pass |
| [resources-lvgl-camera-current-b-arm.json](resources-lvgl-camera-current-b-arm.json) | pass |
| [resources-lvgl-camera-fast-input-arm.json](resources-lvgl-camera-fast-input-arm.json) | pass |
| [resources-lvgl-camera-matched-arm.json](resources-lvgl-camera-matched-arm.json) | pass |
| [resources-lvgl-input-fastpath-arm.json](resources-lvgl-input-fastpath-arm.json) | pass |
| [resources-pil-arm.json](resources-pil-arm.json) | pass |
| [resources-pil-camera-current-a-arm.json](resources-pil-camera-current-a-arm.json) | pass |
| [resources-pil-camera-current-b-arm.json](resources-pil-camera-current-b-arm.json) | pass |
| [resources-pil-camera-fast-input-arm.json](resources-pil-camera-fast-input-arm.json) | pass |
| [resources-pil-camera-matched-arm.json](resources-pil-camera-matched-arm.json) | pass |
| [resources-pil-input-fastpath-arm.json](resources-pil-input-fastpath-arm.json) | pass |
| [retention-camera-cycles-arm.json](retention-camera-cycles-arm.json) | pass |
| [retention-memory-summary.json](retention-memory-summary.json) | pass |
| [retention-qr-cycles-arm.json](retention-qr-cycles-arm.json) | pass |
| [retention-typing-cost-arm.json](retention-typing-cost-arm.json) | pass |
| [retention-typing-imports-arm.json](retention-typing-imports-arm.json) | pass |
| [source-cache-after-arm.json](source-cache-after-arm.json) | pass |
| [source-cache-app-entry-arm.json](source-cache-app-entry-arm.json) | pass |
| [source-cache-before-arm.json](source-cache-before-arm.json) | pass |
| [source-cache-entropy-arm.json](source-cache-entropy-arm.json) | pass |
| [source-cache-memory-summary.json](source-cache-memory-summary.json) | pass |
| [startup-helper-memory-summary.json](startup-helper-memory-summary.json) | pass |
| [stream-import-camera-encryption-arm.json](stream-import-camera-encryption-arm.json) | pass |
| [stream-import-deferred-prepared-arm.json](stream-import-deferred-prepared-arm.json) | pass |
| [stream-import-eager-arm.json](stream-import-eager-arm.json) | pass |
| [stream-import-memory-summary.json](stream-import-memory-summary.json) | pass |
| [tools-import-after-arm.json](tools-import-after-arm.json) | pass |
| [tools-import-before-arm.json](tools-import-before-arm.json) | pass |
| [tools-import-coin-arm.json](tools-import-coin-arm.json) | pass |
| [tools-import-entropy-arm.json](tools-import-entropy-arm.json) | pass |
| [tools-import-memory-summary.json](tools-import-memory-summary.json) | pass |
| [wallet-optional-import-after-arm.json](wallet-optional-import-after-arm.json) | pass |
| [wallet-optional-import-before-arm.json](wallet-optional-import-before-arm.json) | pass |
| [wallet-optional-import-export-arm.json](wallet-optional-import-export-arm.json) | pass |
| [wallet-optional-import-memory-summary.json](wallet-optional-import-memory-summary.json) | pass |
| [wallet-optional-import-transaction-arm.json](wallet-optional-import-transaction-arm.json) | pass |

## ARM workflow and integration history

161 receipts.

| Receipt | Recorded result |
|---|---|
| [address-search-arm.json](address-search-arm.json) | pass |
| [app-entry-check-arm.json](app-entry-check-arm.json) | pass |
| [app-entry-current-arm.json](app-entry-current-arm.json) | pass |
| [app-entry-flow-arm.json](app-entry-flow-arm.json) | pass |
| [app-entry-manifest-flow-arm.json](app-entry-manifest-flow-arm.json) | pass |
| [app-entry-native-manifest-arm.json](app-entry-native-manifest-arm.json) | pass |
| [app-entry-settings-flush-arm.json](app-entry-settings-flush-arm.json) | pass |
| [app-entry-settings-isolation-arm.json](app-entry-settings-isolation-arm.json) | pass |
| [app-entry-settings-ui-arm.json](app-entry-settings-ui-arm.json) | pass |
| [app-entry-sigterm-arm.json](app-entry-sigterm-arm.json) | pass |
| [app-entry-sigterm-camera-arm.json](app-entry-sigterm-camera-arm.json) | pass |
| [app-entry-sigterm-camera-current-arm.json](app-entry-sigterm-camera-current-arm.json) | pass |
| [backup-quiz-arm.json](backup-quiz-arm.json) | pass |
| [calibration-arm.json](calibration-arm.json) | pass |
| [camera-base-bundle-device-match.json](camera-base-bundle-device-match.json) | structured |
| [camera-entropy-controls-arm.json](camera-entropy-controls-arm.json) | structured |
| [camera-fast-preview-soak-arm.json](camera-fast-preview-soak-arm.json) | pass |
| [camera-long-soak-arm.json](camera-long-soak-arm.json) | pass |
| [camera-long-soak-summary.json](camera-long-soak-summary.json) | pass |
| [camera-native-qr-arm.json](camera-native-qr-arm.json) | structured |
| [checked-bytecode-entropy-arm.json](checked-bytecode-entropy-arm.json) | pass |
| [coin-arm.json](coin-arm.json) | pass |
| [controller-address-change-arm.json](controller-address-change-arm.json) | pass |
| [controller-address-receive-arm.json](controller-address-receive-arm.json) | pass |
| [controller-arm.json](controller-arm.json) | pass |
| [controller-battery-absent-arm.json](controller-battery-absent-arm.json) | pass |
| [controller-battery-fixture-arm.json](controller-battery-fixture-arm.json) | pass |
| [controller-bip85-12-arm.json](controller-bip85-12-arm.json) | pass |
| [controller-bip85-18-arm.json](controller-bip85-18-arm.json) | pass |
| [controller-bip85-24-arm.json](controller-bip85-24-arm.json) | pass |
| [controller-calibration-arm.json](controller-calibration-arm.json) | pass |
| [controller-calibration-charging-arm.json](controller-calibration-charging-arm.json) | pass |
| [controller-camera-encrypted-cbc-arm.json](controller-camera-encrypted-cbc-arm.json) | pass |
| [controller-camera-encrypted-cbc-v1-arm.json](controller-camera-encrypted-cbc-v1-arm.json) | pass |
| [controller-camera-encrypted-ctr-arm.json](controller-camera-encrypted-ctr-arm.json) | pass |
| [controller-camera-encrypted-gcm-arm.json](controller-camera-encrypted-gcm-arm.json) | pass |
| [controller-camera-iv-cancel-preview-arm.json](controller-camera-iv-cancel-preview-arm.json) | pass |
| [controller-camera-iv-cancel-review-arm.json](controller-camera-iv-cancel-review-arm.json) | pass |
| [controller-camera-iv-cbc-arm.json](controller-camera-iv-cbc-arm.json) | pass |
| [controller-donate-arm.json](controller-donate-arm.json) | pass |
| [controller-encrypted-ecb-arm.json](controller-encrypted-ecb-arm.json) | pass |
| [controller-encrypted-ecb-v1-arm.json](controller-encrypted-ecb-v1-arm.json) | pass |
| [controller-entropy-cancel-arm.json](controller-entropy-cancel-arm.json) | pass |
| [controller-entropy-generate-arm.json](controller-entropy-generate-arm.json) | pass |
| [controller-entropy-review-arm.json](controller-entropy-review-arm.json) | pass |
| [controller-hardening-arm.json](controller-hardening-arm.json) | pass |
| [controller-home-battery-arm.json](controller-home-battery-arm.json) | pass |
| [controller-io-arm.json](controller-io-arm.json) | pass |
| [controller-locale-arm.json](controller-locale-arm.json) | pass |
| [controller-multisig-arm.json](controller-multisig-arm.json) | pass |
| [controller-multisig-cancel-arm.json](controller-multisig-cancel-arm.json) | pass |
| [controller-multisig-descriptor-arm.json](controller-multisig-descriptor-arm.json) | pass |
| [controller-multisig-mismatch-arm.json](controller-multisig-mismatch-arm.json) | pass |
| [controller-multisig-scan-arm.json](controller-multisig-scan-arm.json) | pass |
| [controller-multisig-select-seed-arm.json](controller-multisig-select-seed-arm.json) | pass |
| [controller-network-absent-arm.json](controller-network-absent-arm.json) | pass |
| [controller-network-fixture-arm.json](controller-network-fixture-arm.json) | pass |
| [controller-passphrase-arm.json](controller-passphrase-arm.json) | pass |
| [controller-seed-scan-12-arm.json](controller-seed-scan-12-arm.json) | pass |
| [controller-seed-scan-24-arm.json](controller-seed-scan-24-arm.json) | pass |
| [controller-settingsqr-apply-arm.json](controller-settingsqr-apply-arm.json) | pass |
| [controller-settingsqr-cancel-arm.json](controller-settingsqr-cancel-arm.json) | pass |
| [controller-settingsqr-scan-arm.json](controller-settingsqr-scan-arm.json) | pass |
| [controller-slip39-20-arm.json](controller-slip39-20-arm.json) | pass |
| [controller-slip39-33-arm.json](controller-slip39-33-arm.json) | pass |
| [controller-startup-arm.json](controller-startup-arm.json) | pass |
| [controller-system-info-arm.json](controller-system-info-arm.json) | pass |
| [controller-version-arm.json](controller-version-arm.json) | pass |
| [controller-wallet-export-arm.json](controller-wallet-export-arm.json) | pass |
| [descriptor-arm.json](descriptor-arm.json) | pass |
| [display-batched-spi-pipeline-arm.json](display-batched-spi-pipeline-arm.json) | pass |
| [display-geometry-arm.json](display-geometry-arm.json) | pass |
| [display-geometry-default-startup-arm.json](display-geometry-default-startup-arm.json) | pass |
| [display-handoff-arm.json](display-handoff-arm.json) | pass |
| [display-scaler-pipeline-arm.json](display-scaler-pipeline-arm.json) | pass |
| [display-spi-pipeline-arm.json](display-spi-pipeline-arm.json) | pass |
| [display-window-default-startup-arm.json](display-window-default-startup-arm.json) | pass |
| [encrypted-entry-arm.json](encrypted-entry-arm.json) | pass |
| [encrypted-qr-roundtrip-arm.json](encrypted-qr-roundtrip-arm.json) | pass |
| [encrypted-review-crypto-arm.json](encrypted-review-crypto-arm.json) | pass |
| [encrypted-transcription-arm.json](encrypted-transcription-arm.json) | pass |
| [entropy-camera-arm.json](entropy-camera-arm.json) | pass |
| [entropy-fallback-arm.json](entropy-fallback-arm.json) | pass |
| [entropy-wipe-arm.json](entropy-wipe-arm.json) | pass |
| [entropy-wipe-timer-arm.json](entropy-wipe-timer-arm.json) | pass |
| [explorer-arm.json](explorer-arm.json) | pass |
| [final-word-arm.json](final-word-arm.json) | pass |
| [frame-completion-arm.json](frame-completion-arm.json) | pass |
| [frame-completion-startup-arm.json](frame-completion-startup-arm.json) | pass |
| [frontend-camera-comparison.json](frontend-camera-comparison.json) | structured |
| [frontend-camera-current-order-a.json](frontend-camera-current-order-a.json) | structured |
| [frontend-camera-current-order-b.json](frontend-camera-current-order-b.json) | structured |
| [frontend-camera-current-reversed-orders.json](frontend-camera-current-reversed-orders.json) | pass |
| [frontend-camera-fast-input-comparison.json](frontend-camera-fast-input-comparison.json) | structured |
| [frontend-camera-lvgl-observation.json](frontend-camera-lvgl-observation.json) | structured |
| [frontend-idle-comparison-input-fastpath.json](frontend-idle-comparison-input-fastpath.json) | pass |
| [frontend-idle-comparison.json](frontend-idle-comparison.json) | pass |
| [grid-color-arm.json](grid-color-arm.json) | pass |
| [grid-hold-arm.json](grid-hold-arm.json) | pass |
| [grid-hold-startup-arm.json](grid-hold-startup-arm.json) | pass |
| [grid-startup-regression-arm.json](grid-startup-regression-arm.json) | pass |
| [grid-wake-hold-arm.json](grid-wake-hold-arm.json) | pass |
| [hardware-runner-arm.json](hardware-runner-arm.json) | pass |
| [home-battery-protocol-arm.json](home-battery-protocol-arm.json) | pass |
| [home-battery-startup-arm.json](home-battery-startup-arm.json) | pass |
| [home-display-recovery-arm.json](home-display-recovery-arm.json) | pass |
| [home-recovery-key-regression-arm.json](home-recovery-key-regression-arm.json) | pass |
| [image-entropy-physical-arm.json](image-entropy-physical-arm.json) | pass |
| [image-entropy-synthetic-arm.json](image-entropy-synthetic-arm.json) | pass |
| [initial-arm.json](initial-arm.json) | structured |
| [input-fastpath-holds-arm.json](input-fastpath-holds-arm.json) | pass |
| [input-latency-arm.json](input-latency-arm.json) | pass |
| [io-input-entropy-wipe-regression-arm.json](io-input-entropy-wipe-regression-arm.json) | pass |
| [io-protocol-arm.json](io-protocol-arm.json) | pass |
| [io-wipe-arm.json](io-wipe-arm.json) | pass |
| [large-grid-arm.json](large-grid-arm.json) | pass |
| [lazy-screens-startup-arm.json](lazy-screens-startup-arm.json) | pass |
| [live-info-protocol-arm.json](live-info-protocol-arm.json) | pass |
| [live-info-startup-regression-arm.json](live-info-startup-regression-arm.json) | pass |
| [locale-native-arm.json](locale-native-arm.json) | pass |
| [locale-supplement-arm.json](locale-supplement-arm.json) | pass |
| [message-signing-arm.json](message-signing-arm.json) | pass |
| [microsd-events-arm.json](microsd-events-arm.json) | pass |
| [multisig-model-arm.json](multisig-model-arm.json) | pass |
| [multisig-signing-arm.json](multisig-signing-arm.json) | pass |
| [native-preview-after-release-arm.json](native-preview-after-release-arm.json) | pass |
| [native-preview-before-release-arm.json](native-preview-before-release-arm.json) | pass |
| [native-preview-camera-arm.json](native-preview-camera-arm.json) | pass |
| [native-preview-faults-arm.json](native-preview-faults-arm.json) | pass |
| [network-font-startup-regression-arm.json](network-font-startup-regression-arm.json) | pass |
| [network-rejected-layout-arm.json](network-rejected-layout-arm.json) | pass |
| [nul-entry-arm.json](nul-entry-arm.json) | pass |
| [nul-passphrase-flow-arm.json](nul-passphrase-flow-arm.json) | pass |
| [passphrase-arm.json](passphrase-arm.json) | structured |
| [power-presentation-arm.json](power-presentation-arm.json) | pass |
| [preview-ingest-host-comparison.json](preview-ingest-host-comparison.json) | pass |
| [profile-lvgl-idle-arm.json](profile-lvgl-idle-arm.json) | pass |
| [psbt-signing-arm.json](psbt-signing-arm.json) | pass |
| [renderer-geometry-arm.json](renderer-geometry-arm.json) | pass |
| [renderer-geometry-default-startup-arm.json](renderer-geometry-default-startup-arm.json) | pass |
| [renderer-settings-ui-arm.json](renderer-settings-ui-arm.json) | pass |
| [screensaver-arm.json](screensaver-arm.json) | pass |
| [seedqr-confirmation-arm.json](seedqr-confirmation-arm.json) | pass |
| [settings-keyboards-seed-recovery-arm.json](settings-keyboards-seed-recovery-arm.json) | structured |
| [settingsqr-arm.json](settingsqr-arm.json) | pass |
| [st7735-default-startup-arm.json](st7735-default-startup-arm.json) | pass |
| [st7735-integration-arm.json](st7735-integration-arm.json) | pass |
| [st7735-settings-ui-arm.json](st7735-settings-ui-arm.json) | pass |
| [startup-branding-build.json](startup-branding-build.json) | structured |
| [startup-helper-after-arm.json](startup-helper-after-arm.json) | pass |
| [startup-helper-before-arm.json](startup-helper-before-arm.json) | pass |
| [startup-helper-payloads-arm.json](startup-helper-payloads-arm.json) | pass |
| [textqr-arm.json](textqr-arm.json) | pass |
| [textqr-output-confirm-arm.json](textqr-output-confirm-arm.json) | pass |
| [transcription-arm.json](transcription-arm.json) | pass |
| [transcription-protocol-arm.json](transcription-protocol-arm.json) | pass |
| [transcription-registration-arm.json](transcription-registration-arm.json) | pass |
| [wipe-arm.json](wipe-arm.json) | pass |
| [wipe-camera-direct-small-ram-arm.json](wipe-camera-direct-small-ram-arm.json) | pass |
| [wipe-camera-small-ram-arm.json](wipe-camera-small-ram-arm.json) | pass |
| [xpub-arm.json](xpub-arm.json) | pass |

See the [test map](../tests/README.md), [source inventory](../../../docs/FIRMWARE-SOURCE-INVENTORY.md)
and [artifact lifecycle](../../../docs/FIRMWARE-ARTIFACTS.md).
