# Per-request camera timing only: not power-on or SeedSigner app boot timing.
import camera
import time
import gc

assert camera.timings() == {"first_isp_us": None, "capture_us": None}
baseline = camera.settings()["rust_heap_bytes"]
start = time.ticks_ms()
camera.init()
print("@@CAMERA_INIT_MS", time.ticks_ms() - start)
for index in range(3):
    start = time.ticks_ms()
    frame = camera.capture()
    total_ms = time.ticks_ms() - start
    timing = camera.timings()
    assert len(frame) == 460800
    assert 0 < timing["first_isp_us"] < timing["capture_us"]
    assert abs(timing["capture_us"] // 1000 - total_ms) < 20
    assert camera.settings()["rust_heap_bytes"] == baseline
    samples = [frame[i] for i in range(0, 307200, 997)]
    assert max(samples) > min(samples) + 10
    print("@@CAMERA_TIMING", index, timing, "outer_ms", total_ms)
    frame = None
    gc.collect()
    # Sleep deliberately between calls: the following timing must reset.
    time.sleep_ms(100)
print("@@PASS phase-10-camera-timing")
