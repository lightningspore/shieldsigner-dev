# SPDX-License-Identifier: MIT
"""Interrupt the original scan loop with the real DUT0 camera/ZXing backend."""
import argparse,datetime,json,re,time
from pathlib import Path
import serial
from serial.tools import list_ports
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--serial',choices=('rv1103-dev-001','rv1103-dut1'),default='rv1103-dev-001')
parser.add_argument('--lcd',action='store_true')
parser.add_argument('--seconds',type=float,default=3)
args=parser.parse_args()
if args.lcd and args.serial!='rv1103-dut1':parser.error('LCD output is only authorized on the actual Mini PCB DUT1; wired DUT0 retains its SPI jumper')
if not 1<=args.seconds<=30:parser.error('duration must be1..30seconds')
ports=[p for p in list_ports.comports() if (p.vid,p.pid)==(0x1209,0x0003) and p.serial_number==args.serial]
assert len(ports)==1,ports
folder=root/'logs/phase-12'/('scan-interrupt-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ'));folder.mkdir(parents=True)
script=b'''import camera
from seedsigner_port.scan_screen import NativeScanScreen,CooperativePreview
from seedsigner_port.decode_qr import DecodeQR
class Input:
    def reset_input(self):pass
    def check_for_low(self,key):return False
preview=CooperativePreview(lambda frame:None)
screen=NativeScanScreen(DecodeQR(),preview=preview,buttons=Input())
baseline=camera.settings()['rust_heap_bytes']
print('@@SCAN_INTERRUPT_READY')
try:
    screen.run()
finally:
    print('@@SCAN_INTERRUPT_CLEAN',camera.preview_status(),camera.settings()['rust_heap_bytes']==baseline,preview.frames)
'''
if args.lcd:
    home=b"from seedsigner_port.native_ui import ScreenSession\nhome=ScreenSession()\nhome.show('main_menu_screen',{'top_nav':{'title':'Home'},'button_list':['Scan','Seeds','Tools','Settings']})\n"
    script=script.replace(b'preview=CooperativePreview(lambda frame:None)\n',home+b'preview=CooperativePreview()\n')
    script=script.replace(b"    print('@@SCAN_INTERRUPT_CLEAN'",b"    home.show('main_menu_screen',{'top_nav':{'title':'Home'},'button_list':['Scan','Seeds','Tools','Settings']})\n    print('@@SCAN_INTERRUPT_CLEAN'")
report={'serial':args.serial,'scope':'Original scan loop, real local camera and ZXing; '+('actual Mini PCB LCD' if args.lcd else 'headless sink')+'; scripted no-back input; no optical QR qualification','passed':False}
out=b''
try:
    with serial.Serial(ports[0].device,115200,timeout=.1,write_timeout=3,exclusive=True) as console:
        console.write(b'\x03\x02\r');time.sleep(.2);console.reset_input_buffer();console.write(b'\x05');time.sleep(.2);console.read_all()
        for offset in range(0,len(script),128):
            console.write(script[offset:offset+128]);console.read_all();time.sleep(.01)
        console.write(b'\x04');deadline=time.monotonic()+8
        while b'@@SCAN_INTERRUPT_READY\r\n' not in out and time.monotonic()<deadline:out+=console.read(4096)
        assert b'@@SCAN_INTERRUPT_READY\r\n' in out,'No scan start marker'
        time.sleep(args.seconds);console.write(b'\x03');deadline=time.monotonic()+5
        while b'>>> ' not in out and time.monotonic()<deadline:out+=console.read(4096)
        match=re.search(rb'@@SCAN_INTERRUPT_CLEAN \(False, 0\) True (\d+)\r\n',out)
        assert match and int(match.group(1))>=1,'No clean scan shutdown with frames'
        assert b'KeyboardInterrupt' in out,'Expected KeyboardInterrupt'
        report.update(passed=True,frames=int(match.group(1)))
except Exception as error:report['error']=str(error)
finally:
    (folder/'script.py').write_bytes(script)
    (folder/'serial.bin').write_bytes(out)
    (folder/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(out.decode(errors='replace'));print(json.dumps(report,indent=2));print('Evidence:',folder)
raise SystemExit(0 if report['passed'] else 1)
