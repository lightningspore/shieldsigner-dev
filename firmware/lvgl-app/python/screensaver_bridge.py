"""Controller facade for pinned native screensaver save/restore and animation."""
def install(runtime,controller):
    previous=controller.screensaver
    original_reset=controller.reset_screensaver_timeout
    own_reset=controller.__dict__.get('reset_screensaver_timeout')
    def reset_timeout():
        original_reset()
        runtime.host.send('activity')
    controller.reset_screensaver_timeout=reset_timeout
    class NativeScreensaver:
        @property
        def is_running(self):return runtime.host.screensaver_active
        def start(self):runtime.host.send('screensaver_show')
        def stop(self):runtime.host.send('screensaver_dismiss')
    controller.screensaver=NativeScreensaver()
    runtime.configure_screensaver(controller.screensaver_activation_ms)
    def restore():
        runtime.configure_screensaver(0)
        controller.screensaver=previous
        if own_reset is None:del controller.reset_screensaver_timeout
        else:controller.reset_screensaver_timeout=own_reset
    return restore
