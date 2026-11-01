"""Read-only ADB accounting for an existing interactive LVGL Python process.

No second Python process on the board, memory contents, object walk, addresses,
wallet data, full command line or arbitrary mapped filenames are recorded.
"""
import argparse,datetime,json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'python'))
from resources import smaps_snapshot

def capture(pid):
    if type(pid) is not int or pid<=0:raise ValueError('Positive PID required')
    def read(name):return subprocess.check_output(['adb','shell','cat',f'/proc/{pid}/{name}'],timeout=15)
    command=read('cmdline')
    if b'/userdata/shieldsigner-lvgl-app/app.py' not in command.split(b'\0'):raise ValueError('PID is not the temporary interactive LVGL entry')
    def started():return read('stat').rsplit(b')',1)[1].split()[19]
    initial=started();result=smaps_snapshot(read('smaps').decode())
    if started()!=initial or read('cmdline')!=command:raise ValueError('Process changed during observation')
    result.update(observedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='One uncontrolled interactive Python memory-map observation. No UI-state, object attribution, total-system measurement or causal memory-saving claim.',addressesRecorded=False,objectValuesRecorded=False)
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid',type=int,required=True)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args();result=capture(args.pid)
    if args.output:args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(processTotals=result['processTotals'],largestMappings=result['mappings'][:5],scope=result['scope']),indent=2))

if __name__=='__main__':main()
