# SPDX-License-Identifier: MIT
"""Hands-free optical scan suite: monitor QR -> DUT camera -> original ScanView.

Requires `tools/qr_screen.py serve` on the second display and the camera aimed
at it. RAM-only console use; PUBLIC fixtures only. Each case shows a QR (static
or animated UR), runs micropython/optical_scan_gate.py and checks the original
routing result against independently computed host values.

  uv run --python 3.13 --with segno --with urtypes --with embit --with pyserial==3.5 \
      python baremetal/tools/optical_scan_test.py [case ...] [--fps 6 --fragment 60]
"""
import argparse,ast,base64,hashlib,json,re,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import qr_screen
from embit.psbt import PSBT
from embit.wordlists.bip39 import WORDLIST
BASE=Path(__file__).resolve().parents[1]
ADDRESS='bc1qd30z5a5e50jtgx28rvt64483tq65r9pkj623wh' # abandon x11 about, m/84'/0'/0'/0/10
SEED=['abandon']*11+['about']
def fixture_psbt():
    text=(BASE/'micropython/psbt_flow_gate.py').read_text()
    return bytes.fromhex(re.search(r"'wireHex': '([0-9a-f]+)'",text).group(1))
def psbt_digest(raw):return hashlib.sha256(PSBT.parse(raw).serialize()).hexdigest()[:16]

def cases(a):
    raw=fixture_psbt()
    seedqr=''.join('%04d'%WORDLIST.index(w) for w in SEED)
    return {
        'address':(lambda:qr_screen.set_text(ADDRESS),{'view':'AddressVerificationStartView','address':ADDRESS}),
        'seedqr':(lambda:qr_screen.set_text(seedqr,'SeedQR (PUBLIC abandon..about)'),{'words':12,'first_last':('abandon','about')}),
        'ur-psbt':(lambda:qr_screen.set_ur_psbt(raw,a.fragment,a.fps),{'view':'PSBTSelectSeedView','psbt_sha256':psbt_digest(raw)}),
        'base64-psbt':(lambda:qr_screen.set_text(base64.b64encode(raw).decode(),'PSBT base64 %d bytes'%len(raw)),{'view':'PSBTSelectSeedView','psbt_sha256':psbt_digest(raw)}),
    }

# base64-psbt: dense 440-char static QR; decodes once the lens is focused.
DEFAULT=['address','seedqr','ur-psbt','base64-psbt']
def run_case(name,show,expect,timeout):
    show();time.sleep(1.5)
    gate=(BASE/'micropython/optical_scan_gate.py').read_text()
    tmp=BASE/'build/optical_scan_case.py';tmp.write_text('CASE=%r\n'%name+gate)
    out=subprocess.run([sys.executable,str(BASE/'tools/usb_console.py'),str(tmp),'--serial','rv1103-dut1','--timeout',str(timeout)],capture_output=True,text=True,cwd=BASE)
    evidence=re.search(r'Evidence: (\S+)',out.stdout+out.stderr)
    serial=(Path(evidence.group(1))/'serial.bin').read_bytes().decode('latin-1') if evidence else ''
    m=re.search(r'@@SCAN_RESULT (\{.*\})',serial)
    if not m:
        tail=[l for l in serial.splitlines() if 'Error' in l or l.startswith('@@')][-4:]
        return {'case':name,'passed':False,'error':'no scan result','tail':tail,'evidence':evidence and evidence.group(1)}
    got=ast.literal_eval(m.group(1))
    if 'first_last' in got:got['first_last']=tuple(got['first_last'])
    bad={k:(got.get(k),v) for k,v in expect.items() if got.get(k)!=v}
    return {'case':name,'passed':not bad,'mismatch':bad,'result':got,'evidence':evidence.group(1)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('cases',nargs='*');ap.add_argument('--fps',type=float,default=6);ap.add_argument('--fragment',type=int,default=60);ap.add_argument('--timeout',type=int,default=60);ap.add_argument('--size',type=float,default=75,help='QR height %% of screen; 94 puts module edges in soft lens corners')
    a=ap.parse_args();qr_screen.SIZE=a.size;table=cases(a);names=a.cases or DEFAULT
    results=[]
    for name in names:
        show,expect=table[name];r=run_case(name,show,expect,a.timeout);results.append(r)
        print(json.dumps(r,default=str),flush=True)
    qr_screen.blank()
    print('SUMMARY',{r['case']:r['passed'] for r in results})
    sys.exit(0 if all(r['passed'] for r in results) else 1)
if __name__=='__main__':main()
