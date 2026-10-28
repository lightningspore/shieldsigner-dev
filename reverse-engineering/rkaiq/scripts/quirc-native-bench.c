/* Benchmark-only quirc reader. Payloads are compared as bytes, never printed. */
#include "quirc.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/resource.h>

static double now(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec / 1e9;
}
static int compare(const void *a, const void *b) {
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}
int main(int argc, char **argv) {
    if (argc != 5 && argc != 6) return 2;
    int width = atoi(argv[2]), height = atoi(argv[3]), runs = atoi(argv[4]);
    if (width <= 0 || height <= 0 || width > 4096 || height > 4096 || runs < 1 || runs > 100) return 2;
    size_t size = (size_t)width * height;
    unsigned char *pixels = malloc(size), target[4096];
    if (!pixels) return 2;
    FILE *file = fopen(argv[1], "rb");
    if (!file || fread(pixels, 1, size, file) != size || fgetc(file) != EOF) return 2;
    fclose(file);
    const char *address = "1BoatSLRHtKNngkdXEeobR76b53LETtpyT";
    size_t target_len = strlen(address);
    memcpy(target, address, target_len);
    if (argc == 6) {
        file = fopen(argv[5], "rb");
        if (!file) return 2;
        target_len = fread(target, 1, sizeof(target), file);
        if (ferror(file) || fgetc(file) != EOF) return 2;
        fclose(file);
    }
    struct quirc *reader = quirc_new();
    if (!reader || quirc_resize(reader, width, height)) return 2;
    double times[100];
    int matches = 0, symbols = 0, candidates = 0;
    for (int run = 0; run < runs; run++) {
        double start = now();
        memcpy(quirc_begin(reader, NULL, NULL), pixels, size);
        quirc_end(reader);
        int matched = 0, count = quirc_count(reader);
        candidates += count;
        for (int i = 0; i < count; i++) {
            struct quirc_code code;
            struct quirc_data data;
            quirc_extract(reader, i, &code);
            quirc_decode_error_t err = quirc_decode(&code, &data);
            if (err == QUIRC_ERROR_DATA_ECC) {
                quirc_flip(&code);
                err = quirc_decode(&code, &data);
            }
            if (err == QUIRC_SUCCESS) {
                symbols++;
                if (data.payload_len == (int)target_len && !memcmp(data.payload, target, target_len)) matched = 1;
            }
        }
        times[run] = now() - start;
        matches += matched;
    }
    double first = times[0];
    qsort(times, runs, sizeof(double), compare);
    struct rusage usage;
    getrusage(RUSAGE_SELF, &usage);
    double cpu = usage.ru_utime.tv_sec + usage.ru_utime.tv_usec/1e6 + usage.ru_stime.tv_sec + usage.ru_stime.tv_usec/1e6;
    long rss = 0;
    file = fopen("/proc/self/status", "r");
    if (file) {
        char line[256];
        while (fgets(line, sizeof(line), file)) if (sscanf(line, "VmHWM: %ld kB", &rss) == 1) break;
        fclose(file);
    }
#ifdef QUIRC_FLOAT_TYPE
    const char *name = "quirc-float";
#else
    const char *name = "quirc-default";
#endif
    printf("{\"decoder\":\"%s\",\"runs\":%d,\"matches\":%d,\"symbols\":%d,\"candidates\":%d,\"firstSeconds\":%.9f,\"medianSeconds\":%.9f,\"minSeconds\":%.9f,\"maxSeconds\":%.9f,\"processCpuSeconds\":%.9f,\"processMaxRssKiB\":%ld}\n",
           name, runs, matches, symbols, candidates, first, times[runs/2], times[0], times[runs-1], cpu, rss);
    quirc_destroy(reader);
    free(pixels);
    return 0;
}
