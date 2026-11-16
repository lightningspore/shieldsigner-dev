# SPDX-License-Identifier: MIT
# Copyright2021 SeedSigner; notice: ../LICENSE.SeedSigner
# Generated original ScanScreen._run. Do not hand-edit.
def run_source(self):
    """
    _render() is mostly meant to be a one-time initial drawing call to set up the
    Screen. Once interaction starts, the display updates have to be managed in
    _run(). The live preview is an extra-complex case.
    """
    from seedsigner_port.decode_qr import DecodeQRStatus

    num_frames = 0
    start_time = self.clock.time()
    while True:
        frame = self.camera.read_video_stream()
        if frame is not None:
            status = self.decoder.add_image(frame)
            num_frames += 1
            elapsed = self.clock.time() - start_time
            decoder_fps = f'{num_frames / elapsed:0.2f}' if elapsed > 0 else '0.00'
            self.preview.decoder_fps = decoder_fps
            if status in (DecodeQRStatus.COMPLETE, DecodeQRStatus.INVALID):
                self.camera.stop_video_stream_mode()
                break
            if status == DecodeQRStatus.FALSE:
                self.frames_decode_status.set_value(self.FRAME__MISS)
            elif status == DecodeQRStatus.PART_COMPLETE:
                self.frames_decode_status.set_value(self.FRAME__ADDED_PART)
            elif status == DecodeQRStatus.PART_EXISTING:
                self.frames_decode_status.set_value(self.FRAME__REPEATED_PART)
            if self.hw_inputs.check_for_low('KEY_RIGHT') or self.hw_inputs.check_for_low(
                'KEY_LEFT'
            ):
                self.camera.stop_video_stream_mode()
                return False
