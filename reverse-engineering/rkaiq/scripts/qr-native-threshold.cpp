// Common preprocessing experiment: ZXing local thresholding, without QR decoding.
#include "HybridBinarizer.h"
#include "BitMatrix.h"
#include <chrono>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>

int main(int argc, char** argv) {
    if (argc != 5) return 2;
    int width = std::stoi(argv[2]), height = std::stoi(argv[3]);
    if (width <= 0 || height <= 0 || width > 4096 || height > 4096) return 2;
    std::ifstream file(argv[1], std::ios::binary);
    std::vector<uint8_t> pixels{std::istreambuf_iterator<char>(file), {}};
    if (pixels.size() != size_t(width) * height) return 2;
    auto start = std::chrono::steady_clock::now();
    ZXing::HybridBinarizer binarizer(ZXing::ImageView(pixels.data(), width, height, ZXing::ImageFormat::Lum));
    auto matrix = binarizer.getBlackMatrix();
    if (!matrix) return 2;
    for (int y = 0; y < height; y++)
        for (int x = 0; x < width; x++) pixels[y*width+x] = matrix->get(x,y) ? 0 : 255;
    double seconds = std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
    std::ofstream output(argv[4], std::ios::binary);
    output.write(reinterpret_cast<const char*>(pixels.data()), pixels.size());
    if (!output) return 2;
    std::printf("{\"preprocessing\":\"zxing-hybrid-local-threshold\",\"seconds\":%.9f}\n", seconds);
}
