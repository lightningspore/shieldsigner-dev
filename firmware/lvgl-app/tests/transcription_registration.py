"""Actual native registration geometry with a public synthetic module matrix."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from transport import NativeHost
from transcription import pack_matrix
frame=bytearray(115200)
def pixels(area,data):
    x1,y1,x2,y2=area;stride=(x2-x1+1)*2
    for row,y in enumerate(range(y1,y2+1)):frame[(y*240+x1)*2:(y*240+x2+1)*2]=data[row*stride:(row+1)*stride]
host=NativeHost(sys.argv[1],pixels);checks=[]
try:
    for border in (4,5):
        rows=[[False]*33 for _ in range(33)];rows[24][24]=True
        host.send('screen',name='seed_transcribe_zoomed_qr_screen',request=border,config=dict(qr_data='public',num_modules=33,matrix_hex=pack_matrix(rows,33),exit_text='click to exit',border_modules=border,initial_zone_x=4,initial_zone_y=4))
        assert host.next_event()==dict(event='screen_ready',request=border)
        # Zone 4 starts at module 20, centered at pixel 60. Module 24 starts
        # at 156. Its inset corner must be black for a square registration
        # module; the old circular data-dot path leaves this pixel white.
        offset=(158*240+158)*2
        assert frame[offset:offset+2]==b'\0\0',('registration corner is not solid',border,frame[offset:offset+2].hex())
        checks.append(dict(size=33,border=border,alignmentCornerSquare=True))
    for border in (0,6):
        host.send('screen',name='seed_transcribe_zoomed_qr_screen',request=10,config=dict(qr_data='public',num_modules=33,matrix_hex=pack_matrix(rows,33),exit_text='click to exit',border_modules=border))
        assert host.next_event().get('event')=='error'
    host.send('screen',name='button_list_screen',request=20,config=dict(top_nav=dict(title='Recovery'),button_list=['Continue']))
    assert host.next_event()==dict(event='screen_ready',request=20)
    print(json.dumps(dict(passed=True,checks=checks,invalidBordersRejected=True,processRecovered=True,physicalDisplay=False)))
finally:host.close()
