"""Home battery metadata from original BatteryHat; no extra polling thread."""
import time

def sample(hat,shown=False):
    if not hat.is_enabled():return None
    if not hat.detected:
        return dict(visible=True,percent=None,charging=False) if shown else dict(visible=False)
    percent=hat.get_percent();current=hat.get_current()
    # Match original UpdateThread's truncation and positive-current charging.
    return dict(visible=True,percent=int(percent) if percent is not None else None,charging=current is not None and current>0)

def monitor(runtime):
    from seedsigner.hardware.battery_hat import BatteryHat
    hat=BatteryHat.get_instance();deadline=[0];previous=[None]
    runtime.home_battery_stats=dict(samples=0,updates=0,refreshInterval=1,extraThreads=0)
    def poll():
        now=time.monotonic()
        if now<deadline[0]:return None
        deadline[0]=now+1
        state=sample(hat,shown=bool(previous[0] and previous[0].get('visible')));runtime.home_battery_stats['samples']+=1
        if state is not None and state!=previous[0]:
            runtime.host.send('home_battery',**state)
            previous[0]=state;runtime.home_battery_stats['updates']+=1
        return None
    return poll
