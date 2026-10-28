// Persistent QR-only worker. Binary frames/payloads remain in memory, never logs.
#include "ReadBarcode.h"
#include <csignal>
#include <cstdio>
#include <cstring>
#include <limits>
#include <vector>
#ifdef __linux__
#include <sys/prctl.h>
#include <unistd.h>
#endif

static uint32_t le32(const unsigned char* p) {
    return uint32_t(p[0]) | uint32_t(p[1])<<8 | uint32_t(p[2])<<16 | uint32_t(p[3])<<24;
}
static void put32(unsigned char* p, uint32_t v) {
    for (int i = 0; i < 4; i++) p[i] = v >> (8*i);
}
int main() {
#ifdef __linux__
    pid_t parent = getppid();
    if (prctl(PR_SET_PDEATHSIG, SIGTERM) || getppid() != parent) return 2;
#endif
    if (std::fwrite("SSQR001\n", 1, 8, stdout) != 8 || std::fflush(stdout)) return 2;
    ZXing::ReaderOptions options;
    options.setFormats(ZXing::BarcodeFormat::QRCode);
    options.setBinarizer(ZXing::Binarizer::LocalAverage);
    std::vector<uint8_t> pixels;
    unsigned char header[12];
    while (true) {
        size_t read = std::fread(header, 1, sizeof(header), stdin);
        if (!read && std::feof(stdin)) return 0;
        if (read != sizeof(header) || std::memcmp(header, "QRI1", 4)) return 2;
        uint32_t width = le32(header+4), height = le32(header+8);
        if (!width || !height || width > 1920 || height > 1920 || uint64_t(width)*height > 2073600) return 2;
        pixels.resize(size_t(width)*height);
        if (std::fread(pixels.data(), 1, pixels.size(), stdin) != pixels.size()) return 2;
        try {
            auto symbols = ZXing::ReadBarcodes(ZXing::ImageView(pixels.data(), width, height, ZXing::ImageFormat::Lum), options);
            const std::vector<uint8_t>* payload = nullptr;
            for (const auto& symbol : symbols) if (symbol.isValid()) { payload = &symbol.bytes(); break; }
            unsigned char response[8] = {'Q','R','O','1'};
            if (payload && payload->size() > 8192) return 2;
            put32(response+4, payload ? uint32_t(payload->size()) : UINT32_MAX);
            if (std::fwrite(response, 1, sizeof(response), stdout) != sizeof(response)) return 2;
            if (payload && std::fwrite(payload->data(), 1, payload->size(), stdout) != payload->size()) return 2;
            if (std::fflush(stdout)) return 2;
        } catch (...) { return 2; }
    }
}
