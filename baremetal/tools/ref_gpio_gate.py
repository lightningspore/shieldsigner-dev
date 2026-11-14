"""Run on REF after confirmed wiring and DUT @@GPIO_READY. Uses only GPIO52/53."""
import json
import os
from pathlib import Path
import re
import select
import termios
import time

ROOT=Path('/sys/class/gpio')
def write(pin,name,value): (ROOT/f'gpio{pin}'/name).write_text(value)
def read(pin): return int((ROOT/f'gpio{pin}'/'value').read_text().strip())
fd=os.open('/dev/ttyS3',os.O_RDWR|os.O_NOCTTY|os.O_NONBLOCK)
a=termios.tcgetattr(fd)
a[0]=a[1]=a[3]=0; a[2]=termios.CS8|termios.CLOCAL|termios.CREAD
a[4]=a[5]=termios.B115200; a[6][termios.VMIN]=a[6][termios.VTIME]=0
termios.tcsetattr(fd,termios.TCSANOW,a); termios.tcflush(fd,termios.TCIFLUSH)
records=[]
report={'passed':False,'records':records}
def transact(command):
 os.write(fd,command); termios.tcdrain(fd)
 data=b''; end=time.monotonic()+1
 while time.monotonic()<end:
  if select.select([fd],[],[],0.1)[0]:
   data+=os.read(fd,4096)
   if b'\n' in data: return data.decode(errors='replace').strip()
 raise RuntimeError('DUT GPIO response timeout: '+repr(data))
try:
 write(52,'direction','in')
 write(53,'direction','high') # DUT C5 remains input; begin at 1 so first iteration is a transition
 for index in range(16):
  ref_output=index%2
  dut_output=1-ref_output
  write(53,'value',str(ref_output))
  time.sleep(0.002)
  response=transact(str(dut_output).encode())
  match=re.fullmatch(r'@@GPIO out=([01]) in=([01])',response)
  time.sleep(0.002)
  ref_input=read(52)
  sample={'index':index,'refOutput':ref_output,'expectedDutOutput':dut_output,'refInput':ref_input,'response':response,
          'passed':bool(match) and int(match[1])==dut_output and int(match[2])==ref_output and ref_input==dut_output}
  records.append(sample)
  if not sample['passed']: break
 report['passed']=len(records)==16 and all(row['passed'] for row in records)
except Exception as exc:
 report['error']=str(exc)
finally:
 try: report['release']=transact(b'Z')
 except Exception as exc: report['releaseError']=str(exc)
 for pin in [52,53]:
  try: write(pin,'direction','in')
  except Exception as exc: report['cleanupError']=str(exc)
 os.close(fd)
print('@@GPIO_REPORT '+json.dumps(report))
