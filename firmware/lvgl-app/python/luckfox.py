"""Reuse the installed reviewed display and button handles for temporary tests.

The regular app must be stopped before acquiring this context. Native LVGL owns
only rendering; this adapter preserves the existing GPIO/init/inversion policy.
"""
import threading

def set_window(display,area):
    """Inclusive LVGL rectangle to ST7789's full 16-bit CASET/RASET fields."""
    x1,y1,x2,y2=area
    if any(type(value) is not int for value in area) or not (0<=x1<=x2<display.width and 0<=y1<=y2<display.height):
        raise ValueError('Invalid display rectangle')
    for command,start,end in ((0x2a,x1,x2),(0x2b,y1,y2)):
        display.command(command)
        # One parameter transaction per axis, with the same full 16-bit wire
        # bytes. Avoid eight separate GPIO/SPI calls for every partial flush.
        display._dc.write(True)
        display._chunked_transfer(bytes((start>>8,start&255,end>>8,end&255)))
    display.command(0x2c)

class LuckfoxHardware:
    def __init__(self):
        from seedsigner.hardware.buttons import HardwareButtons
        self.lock=threading.Lock()
        self.lcd=None
        self.scaler=None
        self.buttons=None
        try:
            self.configure_display(240,240,False)
            self.buttons=HardwareButtons.get_instance()
        except BaseException:
            self.close();raise

    def configure_display(self,width,height,inverted):
        """Caller must quiesce the native pixel reader before changing geometry."""
        if (width,height) not in ((240,240),(320,240),(128,128)):raise ValueError('Unsupported display geometry')
        if (width,height)==(128,128):
            from seedsigner.hardware.displays.ST7735 import ST7735 as Driver
        else:
            from seedsigner.hardware.displays.ST7789 import ST7789 as Driver
        with self.lock:
            if self.lcd is not None and (self.lcd.width,self.lcd.height)==(width,height):
                self.lcd.set_color_inversion(inverted);return
            if self.scaler is not None:self.scaler.wipe();self.scaler=None
            previous=self.lcd;self.lcd=None
            if previous is not None:previous.close()
            display=Driver(width,height)
            try:
                display._ensure_initialized();display.set_color_inversion(inverted)
                scaler=None
                if (width,height)==(128,128):
                    from display_scaler import FrameScaler
                    scaler=FrameScaler()
            except BaseException:
                display.close();raise
            self.lcd=display;self.scaler=scaler

    def pixels(self,area,raw):
        x1,y1,x2,y2=area
        with self.lock:
            if len(raw)!=(x2-x1+1)*(y2-y1+1)*2:raise ValueError('Invalid RGB565 rectangle size')
            if self.scaler is not None:self.scaler.update(area,raw);return
            set_window(self.lcd,area)
            self.lcd._dc.write(True)
            self.lcd._chunked_transfer(raw)

    def frame_complete(self):
        if self.scaler is None:return
        with self.lock:
            image=self.scaler.complete()
            if image is not None:
                try:self.lcd.show_image(image,0,0)
                finally:image.close()

    def frame_reset(self):
        with self.lock:
            if self.scaler is not None:self.scaler.wipe()

    def read_buttons(self):
        return {name for name,pin in self.buttons._gpio_pins.items() if not pin.read()}

    def close(self):
        self.frame_reset()
        if self.buttons is not None:
            for pin in self.buttons._gpio_pins.values():pin.close()
            self.buttons=None
        if self.lcd is not None:self.lcd.close();self.lcd=None
