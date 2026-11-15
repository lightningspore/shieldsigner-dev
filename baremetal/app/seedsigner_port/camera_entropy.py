# SPDX-License-Identifier: MIT
"""Owned camera entropy inputs for the original preview→final SHA256 chain.

Only camera bytes supply entropy here. No PRNG, OS RNG, monitor-health flag,
serial number or timing value is substituted for an unavailable Linux provider.
The acquisition/quality checks reject gross sensor failures, not certify entropy.
"""
import hashlib

WIDTH=640
HEIGHT=480
FRAME_BYTES=WIDTH*HEIGHT*3//2
SAMPLE_SIDE=96
SAMPLE_BYTES=SAMPLE_SIDE*SAMPLE_SIDE
PREVIEW_POOL_SIZE=5

def _wipe(value):
    if isinstance(value,bytearray):value[:]=bytes(len(value))

class CameraFrame:
    """One owned, unmodified640×480 NV12 capture; never aliases camera DMA."""
    def __init__(self,frame):
        if len(frame)!=FRAME_BYTES:raise ValueError('640x480 NV12 capture required')
        self.data=bytearray(frame)
        self.closed=False
    def tobytes(self):
        # Bytes-like owned storage. Avoid a second full-image allocation on MCU.
        if self.closed:raise ValueError('Camera capture has been cleared')
        return self.data
    def clear(self):_wipe(self.data);self.closed=True

class CameraSample:
    """Owned96×96 grayscale preview input, matching the source pool's volume."""
    def __init__(self,data):
        if len(data)!=SAMPLE_BYTES:raise ValueError('96x96 preview sample required')
        self.data=bytearray(data)
        self.closed=False
    def tobytes(self):
        if self.closed:raise ValueError('Camera sample has been cleared')
        return self.data
    def clear(self):_wipe(self.data);self.closed=True

def sample_luma(frame):
    """Sample the actual NV12 Y plane; no display crop/contrast enters entropy.

    Native camera exposes NV12 rather than PIL RGB. Nearest center sampling is
    explicit here; it replaces the Linux PIL convert(L)/bilinear resize boundary.
    The full NV12 capture below is hashed without resampling or enhancement.
    """
    if len(frame)!=FRAME_BYTES:raise ValueError('640x480 NV12 preview required')
    data=bytearray(SAMPLE_BYTES)
    for y in range(SAMPLE_SIDE):
        sy=((2*y+1)*HEIGHT)//(2*SAMPLE_SIDE)
        for x in range(SAMPLE_SIDE):
            sx=((2*x+1)*WIDTH)//(2*SAMPLE_SIDE)
            data[y*SAMPLE_SIDE+x]=frame[sy*WIDTH+sx]
    return CameraSample(data)

class CameraPool:
    """Original moving pool: five owned samples, flat/frozen inputs rejected.

    Like the source, seen hashes live until capture/clear; this set grows with
    distinct frames during a long preview even though image storage is bounded.
    """
    def __init__(self):self.samples=[];self.seen=set()
    @property
    def ready(self):return len(self.samples)==PREVIEW_POOL_SIZE
    def add(self,frame):
        sample=sample_luma(frame);data=sample.tobytes()
        if min(data)==max(data):sample.clear();return False
        fingerprint=hashlib.sha256(data).digest()
        if fingerprint in self.seen:sample.clear();return False
        self.seen.add(fingerprint)
        if self.ready:self.samples.pop(0).clear()
        self.samples.append(sample)
        return True
    def transfer(self):
        if not self.ready:raise ValueError('Camera preview pool is incomplete')
        samples=self.samples;self.samples=[];self.seen.clear()
        return samples
    def clear(self):
        for sample in self.samples:sample.clear()
        self.samples=[];self.seen.clear()

def derive_camera_entropy_bytes(preview_images,final_image):
    """The original camera SHA256 chaining/quality tail with camera-only start.

    `_derive_camera_entropy_bytes` in the Linux fork prefixes camera inputs with
    procfs/time/system-RNG contributions. Camera is the configured source on this
    port: begin with an empty chain instead, retain the original ordered preview
    hashing and final image quality/hash, and do not invent an RNG health result.
    """
    from seedsigner_port.camera_entropy_mnemonic import byte_entropy_is_sufficient
    if preview_images is None or len(preview_images)!=PREVIEW_POOL_SIZE:return None
    seen=set();hash_bytes=b''
    for frame in preview_images:
        data=frame.tobytes()
        if len(data)!=SAMPLE_BYTES or min(data)==max(data):return None
        digest=hashlib.sha256(data).digest()
        if digest in seen:return None
        seen.add(digest)
        chain=hashlib.sha256(hash_bytes);chain.update(data);hash_bytes=chain.digest()
    data=final_image.tobytes()
    if len(data)!=FRAME_BYTES or not byte_entropy_is_sufficient(data):return None
    chain=hashlib.sha256(hash_bytes);chain.update(data);return chain.digest()

def clear_images(samples,final):
    if samples is not None:
        for sample in samples:
            if isinstance(sample,CameraSample):sample.clear()
    if isinstance(final,CameraFrame):final.clear()

def clear_controller_images(controller):
    clear_images(getattr(controller,'image_entropy_preview_frames',None),getattr(controller,'image_entropy_final_image',None))
    controller.image_entropy_preview_frames=None
    controller.image_entropy_final_image=None
