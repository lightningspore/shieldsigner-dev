# ISP parameter queue transport

`parameter_queue::Queue` reconstructs the **metadata-output** branches of the pinned library's `V4l2Device`. The Linux diagnostic now has an MMAP adapter and bounded `submit-parameters` command. Successful real-device submission remains untested. This is queue transport, not the complete ISP startup controller or a generator of complete initial IQ.

## Recovered lifecycle

| Native method | ELF entry | Recovered behavior |
| --- | --- | --- |
| `V4l2Buffer::reset` | `0x5a930` | Clears time, timecode, sequence and queued flag; preserves other descriptor fields |
| `request_buffer` | `0x5afd8` | REQBUFS record/count update; negative ioctl maps to -9 |
| `prepare` | `0x5bdd8` | Request buffers, reset queued count, initialize pool; META_OUTPUT skips automatic QBUF |
| `start` | `0x5bea8` | Optional preparation, STREAMON; close on negative stream-on result; mark active on success |
| `queue_buffer` | `0x5a95c` | Reset cached state, queue temporary descriptor, roll back flag/count on failure |
| `dequeue_buffer` | `0x5b54c` | Require active queue, DQBUF, copy time/sequence/length, decrement queued count |
| `return_buffer_to_pool` | `0x5b068` | Reset cached state under the pool lock |
| `stop` | `0x5bb14` | STREAMOFF when active, clear active flag, finalize an existing pool |

Metadata QBUF sets `bytesused=length` in the **temporary ioctl descriptor**. Optional cache-sync mode replaces its flags with 0x1800. These changes do not overwrite the cached descriptor. Queue count and queued flag change before the ioctl; a negative result reverses them. Positive nonzero ioctl results count as success, matching the native comparison.

Metadata DQBUF copies only timestamp, timecode and sequence into the cached record and records returned `length` separately. It does not clear the metadata buffer's queued flag; explicit pool return does that. Its native index check admits `index==count`, which would access beyond the pool. Checked Rust rejects that response before any mutation; a unit test covers this intentional correction.

The safe core owns state through exclusive mutable references. Lock/unlock boundaries remain explicit in the backend trait, but this does not claim proof of native mutex implementation or concurrent scheduling. The Linux diagnostic has one exclusive owner, so its backend lock methods require no mutex.

`mise run camera:rust:parameter-queue` compares 1,000 native ARM traces across prepare/start/queue/dequeue/return/stop, including both lock modes, cache-sync flags, positive/negative results, count changes, inactive dequeue and invalid returned indices. It compares ioctl request bytes, call order, all cached descriptor bytes, counts/flags and unrelated context preservation. Original reset, request wrapper and state-control instructions execute. Pool allocation/finalization, close, mutex/destructor and vector/smart-pointer operations are controlled boundaries; standard memcpy/memset are explicit helpers. [Report](parameter-queue-equivalence.json).

## Linux adapter

`camera-probe submit-parameters NODE FULL_PARAMETERS.bin [--timeout-ms 3000] [--hold-ms 30000]` is available on ARM32 Linux. It requires an already complete 11,145-byte `isp32_isp_params_cfg` record with final masks, control bits, frame ID and payload. This is **not** an IQ JSON file, vendor binary IQ database, selected-algorithm record or individual module block. The command does not complete missing modules, alter the header or invent tuning. Byte length and nonempty masks do not establish that the IQ contents are correct. Modules with external buffer/mesh handles also require valid resources owned by the submitting process; this diagnostic does not allocate or transfer those resources.

No complete initial IQ record is shipped yet. The kit's per-module fixtures and the synthetic rejection-test payload are not suitable substitutes. Independent full initial configuration remains required work.

The command:

1. Rejects wrong file lengths, empty update masks, unsupported options and known vendor camera processes before any queue setup.
2. Verifies metadata-output/streaming capabilities and RK1P with exactly 11,145-byte format. It leaves the format unchanged.
3. Requests two MMAP buffers, accepts only a returned count of 2–8, checks descriptors/lengths and maps the pool. The kernel driver clamps its metadata pool to that range.
4. Starts the metadata stream without queuing uninitialized buffers, zeroes mapped padding, copies the supplied record and queues the first buffer through the recovered core.
5. Polls/dequeues with a deadline, handles EAGAIN, rejects driver error flags and invalid completion bounds/type, then returns the buffer to the pool.
6. Emits a `parameters-dequeued` JSON event and keeps the parameter stream open for the hold interval (0–300,000 ms; default 30 seconds).
7. Stops the stream, unmaps the pool and releases driver buffers. It emits a final JSON report including ioctl outcomes, an aggregate transient-DQBUF-EAGAIN count and cleanup failures. Closing the file also releases ownership after errors.

Transient EAGAIN retries are aggregated rather than appended indefinitely to the log, keeping memory bounded while waiting. The bounded poll, explicit descriptor/input guards and cleanup-error reporting are diagnostic API behavior, not claims that the native library implements those safeguards. Timeout may mean parameters are awaiting image streaming. The initial driver queue path can also copy configuration into saved startup storage and complete its buffer **before a frame uses it**. `parameterQueued` and completion therefore never establish that registers or pixels changed; reports retain `frameApplicationVerified=false` and `coldStartProven=false`.

Normal stream-off disables ISP parameter-controlled blocks and clears saved first parameters. The driver's fast/pre-on path has special handling instead. Keep the parameter stream open throughout a coordinated capture; ending this diagnostic can disturb an ongoing image stream. See the pinned [parameter driver](https://github.com/LuckfoxTECH/luckfox-pico/blob/0b5c1f30ca6333b7ec5af70d26511da9ef8d39af/sysdrv/source/kernel/drivers/media/platform/rockchip/isp/isp_params.c) and [ISP32 first-configuration code](https://github.com/LuckfoxTECH/luckfox-pico/blob/0b5c1f30ca6333b7ec5af70d26511da9ef8d39af/sysdrv/source/kernel/drivers/media/platform/rockchip/isp/isp_params_v32.c).

## ABI and validation limits

The adapter deliberately uses the native legacy ARM32 68-byte V4L2 buffer record, with 32-bit timeval fields, even though current musl time types are 64-bit. Header cross-compilation explicitly substitutes the legacy timeval/timespec declarations and checks field offsets, metadata constants and ioctl numbers. Ghidra's native 68-byte descriptor copies independently corroborate that layout. Using musl's current time64 record here would select different offsets/request numbers.

ARM/Linux emulation replays the entire native-reference corpus and checks the new command's invalid-device, short/oversized file, empty update-mask and option-range rejection paths. The synthetic payload used only against `/dev/null`/nonexistent devices is excluded from the kit. No test so far exercises successful real parameter MMAP, submission, image-frame application, stop/restart or complete cold startup. [Hardware session guide](HARDWARE-TEST.md).
