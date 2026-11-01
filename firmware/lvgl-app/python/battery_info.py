"""Battery presentation over original BatteryHat API; no charging/control changes."""
from gettext import gettext as _
import time
PLACEHOLDERS='Load Voltage: --\nCurrent: --\nPower: --\nPercent: --%\nCurve: --'

def sample(hat):
    if not hat.is_enabled():return None
    voltage=current=power=percent=None
    if hat.detected:
        voltage=hat.get_voltage();current=hat.get_current();power=hat.get_power();percent=hat.get_percent()
    curve=hat.get_curve_label()
    return '\n'.join([
        f'Load Voltage: {voltage:.3f} V' if voltage is not None else 'Load Voltage: --',
        f'Current: {current/1000:.3f} A' if current is not None else 'Current: --',
        f'Power: {power:.3f} W' if power is not None else 'Power: --',
        f'Percent: {percent:.1f}%' if percent is not None else 'Percent: --%',
        f'Curve: {curve}' if curve else 'Curve: default',
    ])
def configure(cfg):
    cfg['top_nav']['title']=_('Battery Info');cfg.update(text=PLACEHOLDERS,button_list=[],live_info=True)
    return 'button_list_screen',cfg

def monitor(runtime):
    from seedsigner.hardware.battery_hat import BatteryHat
    hat=BatteryHat.get_instance();previous=[PLACEHOLDERS];deadline=[0]
    runtime.battery_info_stats=dict(samples=0,updates=0,refreshInterval=5,extraThreads=0)
    def poll():
        now=time.monotonic()
        if now<deadline[0]:return None
        deadline[0]=now+5
        text=sample(hat);runtime.battery_info_stats['samples']+=1
        if text is not None and text!=previous[0]:
            if '\0' in text or len(text.encode())>4096:raise ValueError('Battery information exceeds display bound')
            runtime.host.send('info_text',text=text);previous[0]=text;runtime.battery_info_stats['updates']+=1
        return None
    return poll
