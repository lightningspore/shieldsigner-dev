"""Native progress display for the original address-search worker/counters."""
from gettext import gettext as _
from types import SimpleNamespace
import time
from contracts import arguments

def monitor(runtime,screen_class,kwargs):
    state=SimpleNamespace(**arguments(screen_class,kwargs))
    # Reuse the original success-before-limit callback. No derivation or worker
    # lifecycle changes; the original View starts/stops/joins its worker.
    callback=screen_class._run_callback
    counter=state.display_index_counter or state.threadsafe_counter
    last=[None];next_update=[0.0]
    def poll():
        completed=callback(state)
        if completed is not None:return completed
        count=counter.cur_count
        now=time.monotonic()
        if count!=last[0] and now>=next_update[0]:
            runtime.host.send('address_progress',text=_('Checking address {}').format(count))
            last[0]=count;next_update[0]=now+.1
        return None
    return poll
