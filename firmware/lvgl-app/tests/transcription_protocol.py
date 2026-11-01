"""Native malformed-matrix rejection/recovery, synthetic public payload only."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from transport import NativeHost
from transcription import pack_matrix
host=NativeHost(sys.argv[1],lambda *a:None);checks=[]
try:
    for name in ('seed_transcribe_whole_qr_screen','seed_transcribe_zoomed_qr_screen'):
        for label,matrix,n in [('invalid-hex','zz',21),('short-matrix','15',21),('unsupported-size','11'+'00'*37,17),('wrong-template',pack_matrix([[False]*21 for _ in range(21)],21),25)]:
            host.send('screen',name=name,request=1,config=dict(top_nav=dict(title='Public fixture'),button_list=['Begin'],qr_data='0000',num_modules=n,matrix_hex=matrix,exit_text='click to exit'))
            event=host.next_event();assert event.get('event')=='error',(name,label,event)
            assert host.child.poll() is None
            checks.append(dict(screen=name,case=label,rejected=True))
    host.send('screen',name='button_list_screen',request=9,config=dict(top_nav=dict(title='Recovery'),button_list=['Continue']))
    assert host.next_event()==dict(event='screen_ready',request=9)
    print(json.dumps(dict(passed=True,checks=checks,processRecovered=True,physicalDisplay=False)))
finally:host.close()
