"""Original calibration control/logging loop, native presentation and private camera."""
from source_text import getsource as adapter_source
import ast,textwrap
from types import SimpleNamespace
from gettext import gettext as _
NAMES={'ToolsBatteryCalibrationIntroScreen','ToolsBatteryCalibrationStartScreen','ToolsBatteryCalibrationRunningScreen'}
def configure(name,cfg):
    if name not in ('ToolsBatteryCalibrationIntroScreen','ToolsBatteryCalibrationStartScreen'):raise ValueError('Running calibration requires its runtime adapter')
    cfg['top_nav']['title']=_('Battery Calibration');cfg['is_bottom_list']=True;cfg['is_button_text_centered']=True
    intro=name=='ToolsBatteryCalibrationIntroScreen'
    cfg.update(text=_('Charge the battery fully. Select Next to start the discharge test.') if intro else _('Test runs until empty. Leave the device unplugged.'),button_list=[_('Next') if intro else _('Start')])
    return 'button_list_screen',cfg

def compile_loop(source,namespace):
    tree=ast.parse(textwrap.dedent(source));count=[0]
    class Drawing(ast.NodeTransformer):
        def visit_With(self,node):
            if len(node.items)==1 and ast.unparse(node.items[0].context_expr)=='self.renderer.lock':
                count[0]+=1
                return ast.copy_location(ast.Expr(value=ast.Call(func=ast.Attribute(value=ast.Name(id='self',ctx=ast.Load()),attr='_lvgl_status',ctx=ast.Load()),args=[ast.Name(id=name,ctx=ast.Load()) for name in ('elapsed_text','voltage_text','current_text','status_text')],keywords=[])),node)
            return self.generic_visit(node)
    tree=Drawing().visit(tree)
    if count[0]!=1 or len(tree.body)!=1 or not isinstance(tree.body[0],ast.FunctionDef) or tree.body[0].name!='_run':raise ValueError('Unexpected calibration drawing structure')
    if any(isinstance(node,ast.Attribute) and isinstance(node.value,ast.Name) and node.value.id=='self' and node.attr=='renderer' for node in ast.walk(tree)):raise ValueError('Unreviewed calibration drawing')
    local={};exec(compile(ast.fix_missing_locations(tree),'<original calibration; LVGL presentation>','exec'),namespace,local)
    return local['_run']

def run(runtime,screen_class,arguments):
    from seedsigner.gui.screens import tools_screens
    from entropy_camera import create,start
    camera=create()
    class Camera:
        def start_video_stream_mode(self,**kwargs):return start(camera,**kwargs)
        def stop_video_stream_mode(self):return camera.stop_video_stream_mode()
    def input_active():
        if runtime.lifecycle_check is not None:runtime.lifecycle_check()
        return bool(runtime.read_buttons())
    from seedsigner.hardware.buttons import HardwareButtons
    class Inputs:
        has_any_input=staticmethod(input_active)
        @property
        def override_ind(self):return HardwareButtons.get_instance().override_ind
    runtime.calibration_stats=dict(displayUpdates=0)
    def status(elapsed,voltage,current,state):
        text='\n'.join([_('Elapsed: ')+elapsed,_('Voltage: ')+voltage,_('Current: ')+current,_('Status: ')+state])
        runtime.host.send('info_text',text=text)
        while True:
            if runtime.lifecycle_check is not None:runtime.lifecycle_check()
            event=runtime.host.next_event()
            if event.get('event')=='error':raise RuntimeError('Calibration update rejected')
            if event.get('event')=='info_updated':break
        runtime.calibration_stats['displayUpdates']+=1
    screen=SimpleNamespace(log_path=arguments['log_path'],battery_hat=arguments['battery_hat'],camera=Camera(),hw_inputs=Inputs(),_lvgl_status=status)
    for name in ('_format_elapsed','_write_log_line'):setattr(screen,name,getattr(screen_class,name).__get__(screen))
    loop=compile_loop(adapter_source(screen_class._run),vars(tools_screens))
    runtime.request+=1;runtime.host.send('key',key=runtime.last_key,pressed=False)
    runtime.host.send('screen',name='button_list_screen',request=runtime.request,config=dict(top_nav=dict(title=_('Battery Calibration'),show_back_button=False,show_power_button=False),text=_('Elapsed: ')+'00:00:00\n'+_('Voltage: ')+'--\n'+_('Current: ')+'--\n'+_('Status: ')+'--',button_list=[],live_info=True,allow_screensaver=False))
    try:
        while True:
            event=runtime.host.next_event()
            if event.get('event')=='error':raise RuntimeError('Calibration display rejected')
            if event.get('event')=='screen_ready' and event['request']==runtime.request:break
        return loop(screen)
    finally:runtime.clear()
