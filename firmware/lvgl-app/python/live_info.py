"""Reuse original memory sampling/formatting; refresh one native label on the UI loop."""
from gettext import gettext as _
from types import SimpleNamespace
import time

def state(screen_class):
    return SimpleNamespace(row_labels=[(attr,_(label)) for attr,label in screen_class.ROWS])
def lines(screen_class,screen):
    values=screen_class._build_lines(screen)
    if len(values)!=len(screen_class.ROWS) or any(not isinstance(value,str) or '\0' in value for value in values):raise ValueError('Unexpected memory information rows')
    text='\n'.join(values)
    if not text or len(text.encode())>4096:raise ValueError('Memory information exceeds display bound')
    return text
def configure(screen_class,cfg):
    cfg['top_nav']['title']=_('Memory Info');cfg.update(text=lines(screen_class,state(screen_class)),button_list=[],live_info=True)
    return 'button_list_screen',cfg
def monitor(runtime,screen_class,cfg):
    screen=state(screen_class);previous=[cfg['text']];deadline=[time.monotonic()+screen_class.REFRESH_INTERVAL]
    runtime.memory_info_stats=dict(samples=1,updates=0,refreshInterval=screen_class.REFRESH_INTERVAL,extraThreads=0)
    def poll():
        now=time.monotonic()
        if now<deadline[0]:return None
        deadline[0]=now+screen_class.REFRESH_INTERVAL
        text=lines(screen_class,screen);runtime.memory_info_stats['samples']+=1
        if text!=previous[0]:
            runtime.host.send('info_text',text=text);previous[0]=text;runtime.memory_info_stats['updates']+=1
        return None
    return poll
