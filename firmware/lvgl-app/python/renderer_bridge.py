"""Isolated Renderer lifecycle adapter; no PIL canvas or fallback drawing.

Install before original Controller.configure_instance(). The Controller keeps its
models, health monitors and timers. Unmigrated rendering fails explicitly.
"""
from contracts import UnmigratedScreen

def install(runtime,hardware,renderer_class):
    names=('configure_instance','initialize_display','show_image','show_image_pan','display_blank_screen')
    originals={name:renderer_class.__dict__.get(name) for name in names}
    previous=renderer_class._instance
    if previous is not None:raise RuntimeError('Install LVGL renderer before Controller startup')
    override_owned='consume_input_override' in vars(runtime)
    previous_override=getattr(runtime,'consume_input_override',None)
    runtime.consume_input_override=lambda:setattr(hardware.buttons,'override_ind',False)
    def initialize(renderer):
        from seedsigner.models.settings import Settings
        from seedsigner.models.settings_definition import SettingsConstants as C
        config=Settings.get_instance().get_value(C.SETTING__DISPLAY_CONFIGURATION,default_if_none=True)
        geometries={'st7789_240x240':(240,240),'st7789_320x240':(320,240),'st7735_128x128':(128,128)}
        if config not in geometries:raise ValueError('Unsupported LVGL display configuration')
        physical_width,physical_height=geometries[config]
        width,height=(240,240) if config=='st7735_128x128' else (physical_width,physical_height)
        inverted=Settings.get_instance().get_value(C.SETTING__DISPLAY_COLOR_INVERTED,default_if_none=True)==C.OPTION__ENABLED
        if (width,height)!=(getattr(runtime,'width',240),getattr(runtime,'height',240)) or (physical_width,physical_height)!=(getattr(hardware.lcd,'width',240),getattr(hardware.lcd,'height',240)):
            runtime.reconfigure_display(width,height,lambda:hardware.configure_display(physical_width,physical_height,inverted))
        else:hardware.lcd.set_color_inversion(inverted)
        renderer.canvas_width=width;renderer.canvas_height=height
        renderer.disp=hardware.lcd;renderer.display_type=config.split('_')[0]
        renderer.canvas=renderer.draw=None
        renderer._needs_resize=(width,height)!=(physical_width,physical_height);renderer._display_size=(physical_width,physical_height)
    @classmethod
    def configure(cls):
        if cls._instance is not None:raise RuntimeError('Renderer already configured')
        instance=cls.__new__(cls)
        instance.initialize_display();cls._instance=instance
    def legacy(*args,**kwargs):raise UnmigratedScreen('Legacy PIL Renderer drawing call')
    def blank(renderer):runtime.clear()
    for name,value in zip(names,(configure,initialize,legacy,legacy,blank)):setattr(renderer_class,name,value)
    def restore():
        if override_owned:runtime.consume_input_override=previous_override
        else:delattr(runtime,'consume_input_override')
        renderer_class._instance=previous
        for name,value in originals.items():
            if value is None:delattr(renderer_class,name)
            else:setattr(renderer_class,name,value)
    return restore
