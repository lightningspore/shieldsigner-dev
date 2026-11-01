"""Run public upstream screen fixtures against the real native host, no GPIO."""
import importlib.util
import json
from pathlib import Path
import sys
import time
transport=Path(sys.argv[1]); binary=Path(sys.argv[2]); scenarios=Path(sys.argv[3])
spec=importlib.util.spec_from_file_location('transport',transport);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
count=0
rectangles=0
def pixels(area,data):
    global rectangles
    rectangles+=1
host=module.NativeHost(binary,pixels)
results=[]
try:
    corpus=json.loads(scenarios.read_text())
    for name,fixture in corpus.items():
        if not name.endswith('_screen'):continue
        before=rectangles
        host.send('screen',name=name,config=fixture.get('context',{}),request=len(results)+1)
        while True:
            event=host.next_event()
            if event['event']=='error':raise RuntimeError('Native screen rejected '+name)
            if event['event']=='screen_ready':break
        time.sleep(.15)
        results.append(dict(screen=name,renderedRectangles=rectangles-before))
    # The actual navigation path must emit the same index expected by Python Views.
    host.send('screen',name='button_list_screen',config={'top_nav':{'title':'Test','show_back_button':False},'button_list':['One','Two']},request=1000)
    while host.next_event()['event']!='screen_ready':pass
    time.sleep(.1)
    host.send('key',key=10,pressed=False) # LV_KEY_ENTER
    time.sleep(.1)
    host.send('key',key=10,pressed=True)
    time.sleep(.15)
    host.send('key',key=10,pressed=False)
    event=host.next_event()
    if event.get('event')!='button_selected' or event.get('index')!=0:raise AssertionError(event)
    print(json.dumps(dict(passed=True,screens=len(results),results=results,navigation=event,totalRectangles=rectangles)))
finally:host.close()
