assert 6 * 7 == 42
assert "R" == chr(82)
import gc

data = [bytearray(257) for _ in range(128)]
data = None
gc.collect()
try:
    raise ValueError("test")
except ValueError:
    print("@@PASS phase-9-exception")
print("@@PASS phase-9-repl")
