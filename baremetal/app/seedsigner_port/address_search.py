# SPDX-License-Identifier: MIT
"""Foreground ownership for original address-search generators; no OS threads."""


class Counter:
    def __init__(self, initial_value=0):
        self.cur_count = initial_value
        self.worker = None

    def set_value(self, value):
        self.cur_count = value

    def increment(self, step=1):
        self.cur_count += step


class Worker:
    def __init__(self):
        self.keep_running = False
        self.active = False
        self._steps = None

    def start(self):
        if self.active:
            raise RuntimeError('Address worker already active')
        if self.threadsafe_counter.worker is not None:
            raise RuntimeError('Address counter already owned')
        self.keep_running = True
        self._steps = self.run()
        self.active = True
        self.threadsafe_counter.worker = self

    def step(self):
        if not self.active:
            return False
        try:
            next(self._steps)
        except StopIteration:
            self.stop()
            return False
        except BaseException:
            self.stop()
            raise
        return True

    def stop(self):
        self.keep_running = False
        try:
            if self._steps is not None:
                self._steps.close()
        finally:
            self._steps = None
            self.active = False
            if self.threadsafe_counter.worker is self:
                self.threadsafe_counter.worker = None

    def is_alive(self):
        return self.active


class SeedAddressVerificationScreen:
    def __init__(self, **kwargs):
        self.args = kwargs

    def display(self):
        from seedsigner_port.renderer import Renderer
        from seedsigner_port.localization import gettext as _

        renderer = Renderer.get_instance()
        a = self.args
        counter = a['threadsafe_counter']
        verified = a['verified_index']
        worker = counter.worker
        if worker is None or not worker.active:
            raise RuntimeError('Address search must be running')
        renderer.session.show_screen(type(self), a)
        display_counter = a.get('display_index_counter') or counter
        last_value = display_counter.cur_count
        last_update = renderer.session.clock()
        while True:
            event = renderer.session.poll()
            if event is not None:
                return renderer.session.screen_result(event)
            if verified.cur_count is not None:
                return 1
            if a.get('max_iterations') is not None and counter.cur_count >= a['max_iterations']:
                return 1000
            worker.step()
            now = renderer.session.clock()
            value = display_counter.cur_count
            finished = verified.cur_count is not None or not worker.active
            if value != last_value and (finished or ((now - last_update) & 0xFFFFFFFF) >= 50):
                renderer.backend.address_progress(_('Checking address {}').format(value))
                last_value = value
                last_update = now
            if verified.cur_count is not None:
                return 1
            if not worker.active:
                return 1000
            renderer.session.sleep(1)
