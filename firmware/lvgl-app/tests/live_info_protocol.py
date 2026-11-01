"""Public native live-label update, preserved selection/scroll, rejection/recovery."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from transport import NativeHost
host=NativeHost(sys.argv[1],lambda *args:None);outcomes=[]
text='\n'.join('Public row %02d'%i for i in range(30))
try:
    for update in (False,True):
        host.send('screen',name='button_list_screen',request=1,config=dict(top_nav=dict(title='Public memory test',show_back_button=True),text=text,button_list=['Done'],live_info=True,initial_scroll_y=100))
        assert host.next_event()==dict(event='screen_ready',request=1)
        if update:
            host.send('info_text',text=text.replace('Public','Sample'))
            assert host.next_event()==dict(event='info_updated')
        host.send('key',key=10,pressed=True)
        event=host.next_event();assert event.get('event')=='button_selected',event
        outcomes.append(dict(index=event['index'],scroll=event['scroll_y']))
        host.send('key',key=10,pressed=False)
    assert outcomes[0]==outcomes[1] and outcomes[0]['scroll']>0,outcomes
    for invalid in ('','x'*4097,'bad\0text'):
        host.send('info_text',text=invalid);assert host.next_event().get('event')=='error'
    host.send('clear');assert host.next_event()['event']=='screen_cleared'
    host.send('info_text',text='Inactive');assert host.next_event()['event']=='error'
    host.send('screen',name='button_list_screen',request=2,config=dict(top_nav=dict(title='Recovery'),button_list=['Done']))
    assert host.next_event()==dict(event='screen_ready',request=2)
    print(json.dumps(dict(passed=True,selectionAndNonzeroScrollPreserved=True,outcomes=outcomes,malformedUpdatesRejected=3,inactiveRejected=True,processRecovered=host.child.poll() is None,physicalDisplay=False)),flush=True)
finally:host.close()
