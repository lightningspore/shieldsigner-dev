"""Test adapters with original installed screen classes; no GPIO construction."""
import hashlib
import json
from pathlib import Path
import sys
import time
sys.path[:0]=[str(Path(__file__).resolve().parent),'/opt/src']
from contracts import configuration
from transport import NativeHost
root=Path('/opt/src/seedsigner')
for path,digest in json.loads(Path(sys.argv[2]).read_text()).items():
    if hashlib.sha256((root/path).read_bytes()).hexdigest()!=digest:raise ValueError('Unreviewed installed app source: '+path)
from seedsigner.gui.screens import screen,settings_screens,seed_screens
from seedsigner.gui.screens.screen import ButtonOption
cases={
 'ButtonListScreen':dict(title='Menu',button_data=[ButtonOption('First'),ButtonOption('Second')]),
 'MainMenuScreen':dict(title='Home',button_data=[ButtonOption(x) for x in ['Scan','Seeds','Tools','Settings']]),
 'LargeIconStatusScreen':dict(title='Test',text='Public test fixture',button_data=[ButtonOption('OK')]),
 'WarningScreen':dict(text='Public test fixture'),
 'DireWarningScreen':dict(text='Public test fixture'),
 'ErrorScreen':dict(text='Public test fixture'),
 'PagedTextScreen':dict(title='Details',paged_info=['First public page','Second public page'],page_num=1),
 'SettingsEntryUpdateSelectionScreen':dict(display_name='Network',help_text='Public selection test',button_data=[ButtonOption('Mainnet'),ButtonOption('Testnet')],checked_buttons=[1]),
 'SeedOptionsScreen':dict(fingerprint='00000000',button_data=[ButtonOption('Done')]),
 'SeedSelectSeedScreen':dict(title='Seeds',text='Public fixture',button_data=[ButtonOption('Test seed')]),
 'AddressVerificationSigTypeScreen':dict(title='Signature type',text='Public fixture',button_data=[ButtonOption('Single sig')]),
 'SeedWordsScreen':dict(words=['abandon']*4,page_index=1,num_pages=3,button_data=[ButtonOption('Next')]),
 'SeedFinalizeScreen':dict(fingerprint='00000000',button_data=[ButtonOption('Done')]),
}
rectangles=0
def sink(*args):
    global rectangles
    rectangles+=1
host=NativeHost(sys.argv[1],sink)
try:
    for index,(name,args) in enumerate(cases.items()):
        cls=next(getattr(module,name) for module in [screen,settings_screens,seed_screens] if hasattr(module,name))
        builder,cfg=configuration(cls,args)
        host.send('screen',name=builder,config=cfg,request=index+1)
        while True:
            event=host.next_event()
            if event['event']=='error':raise ValueError('Invalid adapter: '+name)
            if event['event']=='screen_ready':break
        time.sleep(.1)
    print(json.dumps(dict(passed=True,classes=list(cases),rectangles=rectangles,sourceGuardsPassed=True)))
finally:host.close()
