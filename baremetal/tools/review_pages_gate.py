# SPDX-License-Identifier: MIT
"""Run public native paged-review flows and independently decode displayed pages."""
import ast,codecs,datetime,json,re,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def verify(output,script):
    fixtures=next(ast.literal_eval(n.value) for n in ast.parse(script).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='fixtures' for t in n.targets))
    results=[]
    for match in re.finditer(r'^@@PUBLIC_REVIEW_PAGES (\d+) (\w+) (.+)\r?$',output,re.M):
        number=int(match[1]);display=fixtures[number][1];pages=json.loads(match[3]);position=0;reconstructed=''
        for text in pages:
            header,*rows=text.split('\n')
            bounds=re.fullmatch(r'Chars (\d+)-(\d+)/(\d+)',header)
            if not bounds or int(bounds[1])!=position+1 or int(bounds[3])!=len(display):raise ValueError('Incorrect displayed character range')
            if not 1<=len(rows)<=4 or any(not row or len(row)>24 or any(not 33<=ord(c)<=126 for c in row) for row in rows):raise ValueError('Page exceeds reviewed text geometry')
            decoded=codecs.decode(''.join(rows),'unicode_escape')
            end=int(bounds[2])
            if not position<end<=len(display):raise ValueError('Invalid displayed character span')
            if decoded!=display[position:end]:raise ValueError('Displayed characters differ from actual passphrase')
            position=end;reconstructed+=decoded
        if position!=len(display) or reconstructed!=display:raise ValueError('Display omitted or changed characters')
        results.append({'fixture':number,'mode':match[2],'characters':len(display),'pages':len(pages),'exact':True})
    if sorted(r['fixture'] for r in results)!=list(range(len(fixtures))):raise ValueError('Missing native review fixture')
    for number,mode in ((0,'revisit'),(0,'exit'),(0,'wipe'),(1,'accept'),(2,'accept')):
        if not re.search(r'^@@PASS original-paged-review '+str(number)+' '+mode+r' \d+ \d+\r?$',output,re.M):raise ValueError('Missing actual original View flow: '+mode)
    return results

def main():
    folder=ROOT/'logs/phase-12'/('review-pages-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ'))
    folder.mkdir(parents=True)
    script=ROOT/'micropython/review_pages_gate.py'
    report={'passed':False,'scope':'Public original View/native page flows, independently decoded display identities; not wallet or optical qualification'}
    def reset_snapshot(name,arm=False):
        probe=folder/(name+'.py')
        code="import machine,json\nif hasattr(machine,'last_reset'):\n    print('@@RESET_SNAPSHOT',json.dumps(machine.last_reset()))\n"
        if arm:code+="    machine.clear_reset_record()\n    machine.set_reset_marker(0x50414745)\n"
        code+="else:print('@@RESET_DIAGNOSTICS_UNAVAILABLE')\n"
        probe.write_text(code)
        status=subprocess.run([sys.executable,str(ROOT/'tools/usb_console.py'),str(probe),'--serial','rv1103-dut1','--timeout','8'],capture_output=True,text=True)
        text=status.stdout+status.stderr;(folder/(name+'.txt')).write_text(text)
        if status.returncode:raise RuntimeError('Reset diagnostic '+name+' failed; preserve this run and inspect maskrom/device state')
        found=re.search(r'^@@RESET_SNAPSHOT (.+)\r?$',text,re.M)
        return {'available':bool(found),'record':json.loads(found[1]) if found else None}
    try:
        manifest=json.loads((ROOT/'build/hello-manifest.json').read_text())
        report['buildDownloadSha256']=manifest['files']['build/hello-download.bin']
        shutil.copyfile(ROOT/'target/armv7a-none-eabi/release/rv1103-bringup',folder/'payload.elf')
        (folder/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        report['resetBefore']=reset_snapshot('reset-before',True)
        child=subprocess.run([sys.executable,str(ROOT/'tools/usb_console.py'),str(script),'--serial','rv1103-dut1','--timeout','55'],capture_output=True,text=True)
        output=child.stdout+child.stderr;(folder/'console.txt').write_text(output)
        if child.returncode:raise RuntimeError('Native gate did not complete successfully; inspect reset record before further tests')
        report['displayedPages']=verify(output,script.read_text())
        report['resetAfter']=reset_snapshot('reset-after')
        if report['resetAfter']['available'] and report['resetAfter']['record'] is not None:raise RuntimeError('Reset recorded during native review gate')
        report['passed']=True
        evidence=re.findall(r'Evidence: (.+)',output)
        if evidence:report['nativeEvidence']=evidence[-1]
    except Exception as error:report['error']=str(error)
    (folder/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));print('Evidence:',folder)
    return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
