"""Run public native-protocol regressions on this computer, without board access."""
import argparse,datetime,json,os,subprocess,sys,time
from pathlib import Path
from build_manifest import inputs,sha256
HERE=Path(__file__).resolve().parent
from artifact_paths import DIST,LVGL_SOURCES,LVGL_HOST_CHECKS
CASES={'status':'status_protocol.py','frames':'frame_completion.py','geometry':'display_geometry.py','preview':'preview_protocol.py','live-info':'live_info_protocol.py','transcription':'transcription_protocol.py','io':'io_protocol.py','home-battery':'home_battery_protocol.py','corpus':'native_smoke.py'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cases',nargs='*',choices=list(CASES))
    args=parser.parse_args()
    binary=DIST/'build-host/shieldsigner-lvgl'
    manifest=json.loads((binary.parent/'build-manifest.json').read_text())
    if manifest.get('target')!='host' or manifest.get('binarySha256')!=sha256(binary) or manifest.get('inputs')!=inputs(HERE):raise ValueError('Build the current host artifact first: mise run lvgl:app:build:host')
    environment=dict(os.environ,PYTHONPATH=str(HERE/'python'))
    results=[]
    for name in args.cases or CASES:
        script=HERE/'tests'/CASES[name];started=time.monotonic()
        arguments=[str(binary)];fixture_hash=None
        if name=='corpus':
            scenarios=LVGL_SOURCES/'screens/tools/scenarios/scenarios.json'
            arguments=[str(HERE/'python/transport.py'),str(binary),str(scenarios)]
            fixture_hash=sha256(scenarios)
        try:
            completed=subprocess.run([sys.executable,str(script),*arguments],env=environment,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=25)
            lines=completed.stdout.splitlines()
            receipts=[json.loads(line) for line in lines if line.startswith('{')]
            passed=completed.returncode==0 and len(receipts)==1 and receipts[0].get('passed') is True and 'Traceback' not in completed.stderr
            detail=dict(exitCode=completed.returncode,result=receipts[0] if len(receipts)==1 else None,error=completed.stderr[-4000:] if not passed else None)
        except subprocess.TimeoutExpired:
            passed=False;detail=dict(timedOut=True)
        results.append(dict(case=name,passed=passed,seconds=round(time.monotonic()-started,3),scriptSha256=sha256(script),fixtureSha256=fixture_hash,**detail))
        print(json.dumps(dict(case=name,passed=passed)),flush=True)
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    destination=LVGL_HOST_CHECKS/('native-'+stamp+'.json');destination.parent.mkdir(parents=True,exist_ok=True)
    receipt=dict(passed=all(row['passed'] for row in results),nativeBuild=manifest,pythonBundleSha256={str(path.relative_to(HERE)):sha256(path) for path in sorted((HERE/'python').glob('*.py'))},cases=results,scope='Host native-protocol regression with public pixels/metadata. No original Controller, camera, physical GPIO/LCD or ARM resource qualification.')
    destination.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(passed=receipt['passed'],receipt=str(destination))))
    if not receipt['passed']:raise SystemExit(1)

if __name__=='__main__':main()
