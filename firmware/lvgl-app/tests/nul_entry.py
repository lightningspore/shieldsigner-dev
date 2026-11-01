"""Public NUL-bearing input: exact Save/Back and atomic UTF-8/escape edits."""
import json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from contracts import configuration
from transport import NativeHost
hardware=None
if '--display' in sys.argv:
 sys.path.insert(0,'/opt/src')
 from luckfox import LuckfoxHardware
 hardware=LuckfoxHardware()
host=NativeHost(sys.argv[1],lambda area,data:hardware.pixels(area,data) if hardware is not None else None)
def key(value):host.send('key',key=value,pressed=True);host.send('key',key=value,pressed=False);time.sleep(.02)
def run(value,keys,expected,back=False):
 builder,cfg=configuration(type('SeedAddPassphraseScreen',(),{}),dict(passphrase=value,title='Public fixture',initial_keyboard='123'))
 host.send('screen',name=builder,config=cfg,request=1);assert host.next_event()==dict(event='screen_ready',request=1)
 for item in keys:key(item)
 actual=host.next_event();assert actual==dict(event='passphrase_result',text=expected,back=back),('Incorrect public exact-text result',len(expected),actual.get('event'))
try:
 values=['a\0b','\0','nul\0 literal\\0 slash\\ é e\u0301\r\n1','plain \\0']
 for value in values:run(value,[ord('3')],value)
 run('a\0b',[17]*6+[10],'a\0b',back=True)
 # Digits mode starts focused on trailing '1'. Reach Delete, then remove the
 # digit, the entire é codepoint and finally the NUL as one logical character.
 run('A\0é1',[18,18,19,19,10,10,10,ord('3')],'A')
 # Add a digit after a NUL without parsing visible backslash escapes as input.
 run('A\0'+'1',[10,ord('3')],'A\0'+'11')
 run('A\0'+'1',[18,18,18,19,10,17,10,ord('3')],'A1')
 run('A\0é1',[18,18,18,19,10,10,19,10,17,17,17,10,ord('3')],'A\0é41')
 host.send('clear');assert host.next_event()==dict(event='screen_cleared')
 print(json.dumps(dict(passed=True,saveFixtures=len(values),backExact=True,utf8AndNulDeletionAtomic=True,insertionExact=True,leftRightCursorExact=True,physicalDisplay=hardware is not None,publicFixtures=True,cryptoChanged=False)),flush=True)
finally:
 host.close()
 if hardware is not None:hardware.close()
