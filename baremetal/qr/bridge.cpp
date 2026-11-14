// SPDX-License-Identifier: MIT
// ZXing is Apache-2.0; its unchanged sources/license remain in the pinned cache.
#include "ReadBarcode.h"
#include <algorithm>
#include <cstdint>
#include <new>
// Return -1 on invalid arguments/error, -2 on oversize output, 0 on no code,
// or payload length + 1 (therefore a valid empty QR is distinguishable).
extern "C" int bm_qr_decode(const uint8_t* image, unsigned width, unsigned height,
                             uint8_t* output, unsigned capacity) noexcept {
    if (!image || !output || !width || !height || width > 640 || height > 480)
        return -1;
    try {
        auto options = ZXing::ReaderOptions().setFormats(ZXing::BarcodeFormat::QRCode)
            .setTryHarder(true).setTryRotate(true).setTryInvert(true)
            .setBinarizer(ZXing::Binarizer::LocalAverage);
        auto result = ZXing::ReadBarcode(ZXing::ImageView(image, width, height, ZXing::ImageFormat::Lum), options);
        if (!result.isValid()) return 0;
        const auto& bytes = result.bytes();
        if (bytes.size() > capacity) return -2;
        std::copy(bytes.begin(), bytes.end(), output);
        return static_cast<int>(bytes.size()) + 1;
    } catch (...) { return -1; }
}
