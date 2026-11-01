"""Public native font/picker lifecycle probe; no wallet or hardware ownership."""
import argparse,json,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from locale_assets import LocaleAssets
from transport import NativeHost

def main():
    parser=argparse.ArgumentParser();parser.add_argument('binary');parser.add_argument('assets');parser.add_argument('--display',action='store_true');args=parser.parse_args()
    hardware=None
    if args.display:
        sys.path.insert(0,'/opt/src')
        from luckfox import LuckfoxHardware
        hardware=LuckfoxHardware()
    assets=LocaleAssets(args.assets);frames=[0]
    def pixels(area,data):
        frames[0]+=1
        if hardware is not None:hardware.pixels(area,data)
    host=NativeHost(args.binary,pixels)
    memory=[]
    def snapshot(code):
        path=Path('/proc')/str(host.child.pid)/'status'
        if not path.exists():return
        fields={}
        for line in path.read_text().splitlines():
            key,_,value=line.partition(':')
            if key in ('VmRSS','RssAnon','VmSwap','Threads'):fields[key]=int(value.split()[0])
        memory.append(dict(locale=code,**fields))
    previous=os.environ.get('LANGUAGE')
    try:
        for code in assets.index['locales']+['en']:
            os.environ['LANGUAGE']=code;assets.sync(host)
            host.send('screen',name='button_list_screen',config={'top_nav':{'title':'Public fixture'},'button_list':['OK'],'text':assets.index['manifests'].get(code,{}).get('endonym','Public text')},request=1)
            assert host.next_event()=={'event':'screen_ready','request':1}
            snapshot(code)
        supplemental=Path(args.assets)/'supplemental-shaping.json'
        samples=json.loads(supplemental.read_text()) if supplemental.exists() else []
        for row in samples:
            os.environ['LANGUAGE']=row['locale'];assets.sync(host)
            host.send('screen',name='large_icon_status_screen',config={'top_nav':{'title':'Public translation fixture'},'button_list':['OK'],'status_type':'warning','text':row['text']},request=3)
            assert host.next_event()=={'event':'screen_ready','request':3}
        rows=[dict(locale=code,english=code,native=manifest['endonym'],image='endonym_240.bin') for code,manifest in assets.index['manifests'].items()]
        host.send('screen',name='settings_locale_picker_screen',config={'top_nav':{'title':'Language'},'rows':rows,'active_locale':'en'},request=2)
        assert host.next_event()=={'event':'screen_ready','request':2}
        host.send('locale',locale='../en')
        assert host.next_event()=={'event':'error','kind':'invalid_request'}
        host.send('clear');assert host.next_event()=={'event':'screen_cleared'}
        assert frames[0]>0
        print(json.dumps(dict(passed=True,locales=len(assets.index['locales']),fontLocales=len(rows),pixelPackets=frames[0],supplementalVariantsRendered=len(samples),physicalDisplayUsed=hardware is not None,physicalDisplayQualified=False,nativeMemoryKiBExceptThreads=memory,shapingTemplateGaps=assets.index['unsupportedShapingTemplates'])))
    finally:
        host.close()
        if hardware is not None:hardware.close()
        if previous is None:os.environ.pop('LANGUAGE',None)
        else:os.environ['LANGUAGE']=previous
if __name__=='__main__':main()
