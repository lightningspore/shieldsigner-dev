# Verify the5Hz LED heartbeat through native status and real pad readbacks.
import machine
import time
start = machine.led_status()
assert start["enabled"] and start["hz"] == 5
states = []
for _ in range(100):
    states.append(machine.led_status()["state"])
    time.sleep_ms(10)
end = machine.led_status()
delta = end["transitions"] - start["transitions"]
assert 9 <= delta <= 11
assert min(states) == 0 and max(states) == 1
assert end["pad_errors"] == 0
print("@@LED_TEST transitions", delta, "pad_errors", end["pad_errors"])
print("@@PASS led-5hz")
