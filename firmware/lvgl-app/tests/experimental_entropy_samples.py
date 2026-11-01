"""Byte-equivalence/pairing experiments, NOT the production entropy path."""
class GrayscaleSample:
    """Only the two original pool-admission/sample operations; final capture stays RGB."""
    def __init__(self,image):self.image=image
    def getextrema(self):
        # Original small-RAM Camera presents R=G=B, so variation is identical.
        return (self.image.getextrema(),)*3
    def convert(self,mode):
        if mode!='L':raise ValueError('Unexpected entropy sample conversion')
        return self.image.copy()

def sample(camera):
    stream=camera._video_stream
    if getattr(stream,'transport',None)!='nv12':return camera.read_video_stream(as_image=True)
    from shieldsigner_native_stream import NativeVideoStream
    from PIL import Image
    frame=_sample_native_frame(camera)
    if frame is None:return None
    if frame.format!='nv12':raise ValueError('Unexpected native entropy frame format')
    image=Image.frombytes('L',frame.size,frame.luma_bytes())
    image=image.rotate(90+camera._camera_rotation,expand=True)
    return GrayscaleSample(image)


def _enable_pairing(camera):
    stream=camera._video_stream
    if getattr(stream,'transport',None)!='nv12':return
    original=stream._prepare
    camera._lvgl_pair_stream=stream;camera._lvgl_pair_ready=False;camera._lvgl_pair_frame=None
    camera._lvgl_pair_hits=0;camera._lvgl_pair_misses=0
    def prepare(frame,preview=False,display=False,rotation=0):
        if preview:
            camera._lvgl_pair_ready=True;camera._lvgl_pair_frame=frame
        return original(frame,preview,display,rotation)
    prepare.__lvgl_pair__=True;stream._prepare=prepare

def _sample_native_frame(camera):
    if getattr(camera,'_lvgl_pair_ready',False):
        frame=camera._lvgl_pair_frame
        camera._lvgl_pair_ready=False;camera._lvgl_pair_frame=None
        if frame is None:camera._lvgl_pair_misses+=1
        else:camera._lvgl_pair_hits+=1
        return frame
    from shieldsigner_native_stream import NativeVideoStream
    return NativeVideoStream.read(camera._video_stream)

def release_pair(camera):
    stream=getattr(camera,'_lvgl_pair_stream',None)
    if stream is not None and getattr(stream._prepare,'__lvgl_pair__',False):del stream._prepare
    camera._lvgl_pair_frame=None;camera._lvgl_pair_ready=False;camera._lvgl_pair_stream=None
