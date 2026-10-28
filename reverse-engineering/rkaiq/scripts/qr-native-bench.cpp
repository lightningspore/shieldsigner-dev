// Benchmark-only native ZXing reader; never prints decoded payloads.
#include "ReadBarcode.h"
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <string>
#include <sys/resource.h>
#include <vector>

int main(int argc, char** argv) {
    if (argc != 5 && argc != 6) return 2;
    int width = std::stoi(argv[2]), height = std::stoi(argv[3]), runs = std::stoi(argv[4]);
    if (width <= 0 || height <= 0 || width > 4096 || height > 4096 || runs < 1 || runs > 100) return 2;
    std::ifstream file(argv[1], std::ios::binary);
    std::vector<uint8_t> pixels{std::istreambuf_iterator<char>(file), {}};
    if (pixels.size() != size_t(width) * height) return 2;
    ZXing::ImageView image(pixels.data(), width, height, ZXing::ImageFormat::Lum);
    ZXing::ReaderOptions options;
    options.setFormats(ZXing::BarcodeFormat::QRCode);
    options.setBinarizer(ZXing::Binarizer::LocalAverage);
    std::string target = "1BoatSLRHtKNngkdXEeobR76b53LETtpyT";
    if (argc == 6) {
        std::ifstream expected(argv[5], std::ios::binary);
        if (!expected) return 2;
        target.assign(std::istreambuf_iterator<char>(expected), {});
        if (target.size() > 4096) return 2;
    }
    std::vector<double> times;
    int matches = 0, symbols = 0;
    for (int i = 0; i < runs; ++i) {
        auto start = std::chrono::steady_clock::now();
        auto result = ZXing::ReadBarcodes(image, options);
        times.push_back(std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count());
        bool matched = false;
        for (const auto& barcode : result) {
            const auto& bytes = barcode.bytes();
            if (barcode.isValid() && std::string(bytes.begin(), bytes.end()) == target) matched = true;
        }
        matches += matched;
        symbols += result.size();
    }
    double first = times[0];
    std::sort(times.begin(), times.end());
    struct rusage usage{};
    getrusage(RUSAGE_SELF, &usage);
    // ru_maxrss can retain the launching Python process's pre-exec high water.
    // VmHWM belongs to this executable's current address space.
    long peak_rss = 0;
    std::ifstream status("/proc/self/status");
    for (std::string line; std::getline(status, line); ) {
        if (std::sscanf(line.c_str(), "VmHWM: %ld kB", &peak_rss) == 1) break;
    }
    double cpu = usage.ru_utime.tv_sec + usage.ru_utime.tv_usec/1e6 + usage.ru_stime.tv_sec + usage.ru_stime.tv_usec/1e6;
    std::printf("{\"decoder\":\"zxing-cpp-3.1.1\",\"runs\":%d,\"matches\":%d,\"symbols\":%d,\"firstSeconds\":%.9f,\"medianSeconds\":%.9f,\"minSeconds\":%.9f,\"maxSeconds\":%.9f,\"processCpuSeconds\":%.9f,\"processMaxRssKiB\":%ld}\n",
        runs, matches, symbols, first, times[times.size()/2], times.front(), times.back(), cpu, peak_rss);
}
