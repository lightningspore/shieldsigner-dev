"""Run a public-fixture check via temporary ADB deployment; never flash/install.

Example: mise run lvgl:app:hardware transcription-protocol
The normal app must already be stopped. Results/logs stay in ignored dist.
"""
import argparse,datetime,json,shlex,subprocess,sys,time
from pathlib import Path
from build_manifest import inputs,sha256
def remote_command(adb,arguments):
    # adb shell joins its arguments before the remote shell parses them.
    return [*adb,'shell',shlex.join(arguments)]

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
from artifact_paths import DIST,LVGL_HARDWARE_CHECKS
CASES={
 'typing-import-cost':('wallet_import_cost.py',['typing']),
 'typing-import-audit':('typing_import_audit.py',[]),
 'qr-export-memory-cycles':('qr_output_flow.py',['--display','--dependencies','--memory-cycles']),
 'camera-memory-cycles':('camera_flow.py',['--display','--tools-loaded','--memory-cycles']),
 'preview-protocol':('preview_protocol.py',['--display']),
 'preview-faults':('preview_faults.py',[]),
 'source-cache-eviction':('source_cache_cost.py',['--evict-on-read']),
 'source-cache-cost':('source_cache_cost.py',[]),
 'encoder-payloads':('encoder_payloads.py',[]),
 'dependency-coin':('dependency_coin_flow.py',['--display']),
 'dependency-entropy-generate':('dependency_entropy_flow.py',['--small-ram','--generate']),
 'tools-import-cost':('wallet_import_cost.py',['seedsigner.views.tools_views']),
 'decoder-payloads':('decoder_payloads.py',[]),
 'dependency-wallet-export':('dependency_wallet_export.py',[]),
 'wallet-import-cost':('wallet_import_cost.py',[]),
 'dependency-camera-eager-stream':('frontend_resources.py',['--dependencies','--camera','--eager-stream']),
 'dependency-camera-audit':('frontend_resources.py',['--dependencies','--camera']),
 'dependency-cost':('dependency_cost.py',[]),
 'dependency-audit':('frontend_resources.py',['--dependencies']),
 'controller-wallet-export':('controller_wallet_export.py',[]),
 'controller-address-receive':('controller_address.py',[]),
 'controller-address-change':('controller_address.py',['--change']),
 'input-latency':('input_latency.py',[]),
 'controller-passphrase':('controller_passphrase.py',[]),
 'nul-entry':('nul_entry.py',['--display']),
 'nul-passphrase-flow':('passphrase_flow.py',['/opt/src','--display']),
 'camera-long-soak':('camera_flow.py',['--display','--tools-loaded','--long-soak']),
 'grid-color':('grid_color.py',['--display']),
 'controller-encrypted-ecb-v1':('controller_camera_iv.py',['--roundtrip','--mode','AES-ECB v1']),
 'controller-encrypted-ecb':('controller_camera_iv.py',['--roundtrip','--mode','AES-ECB']),
 'controller-camera-encrypted-cbc-v1':('controller_camera_iv.py',['--roundtrip','--mode','AES-CBC v1']),
 'controller-slip39-33':('controller_slip39.py',['33']),
 'controller-slip39-20':('controller_slip39.py',['20','--discard']),
 'controller-bip85-18':('controller_bip85.py',['18']),
 'controller-bip85-12':('controller_bip85.py',['12']),
 'controller-bip85-24':('controller_bip85.py',['24']),
 'controller-locale':('controller_locale.py',[]),
 'locale-native':('locale_native.py',['/userdata/shieldsigner-lvgl-locales','--display']),
 'controller-camera-encrypted-cbc':('controller_camera_iv.py',['--roundtrip']),
 'controller-camera-encrypted-ctr':('controller_camera_iv.py',['--roundtrip','--mode','AES-CTR']),
 'controller-camera-encrypted-gcm':('controller_camera_iv.py',['--roundtrip','--mode','AES-GCM']),
 'preview-throughput':('preview_throughput.py',['--display']),
 'controller-camera-iv-cbc':('controller_camera_iv.py',[]),
 'controller-camera-iv-ctr':('controller_camera_iv.py',['--mode','AES-CTR']),
 'controller-camera-iv-gcm':('controller_camera_iv.py',['--mode','AES-GCM']),
 'controller-camera-iv-cancel-preview':('controller_camera_iv.py',['--cancel','preview']),
 'controller-camera-iv-cancel-review':('controller_camera_iv.py',['--cancel','review']),
 'status-protocol':('status_protocol.py',[]),
 'dependency-wallet-flow':('dependency_wallet_flow.py',['--select-seed','--load-descriptor','--scan-psbt','--import-seed']),
 'dependency-closure':('dependency_hardware.py',[]),
 'resources-lvgl-camera':('frontend_resources.py',['--camera']),
 'resources-pil-camera':('frontend_resources.py',['--legacy','--camera']),
 'home-display-recovery':('renderer_settings_ui.py',['--home-recovery']),
 'st7735-settings-ui':('renderer_settings_ui.py',['--st7735']),
 'st7735-integration':('st7735_integration.py',[]),
 'display-scaler-pipeline':('display_scaler_pipeline.py',[]),
 'frame-completion':('frame_completion.py',[]),
 'display-spi-pipeline':('display_spi_pipeline.py',[]),
 'renderer-settings-ui':('renderer_settings_ui.py',[]),
 'renderer-geometry':('renderer_geometry.py',[]),
 'display-handoff':('display_handoff.py',[]),
 'display-geometry':('display_geometry.py',[]),
 'app-entry-settings-ui':('app_entry_flow.py',['--settings-ui']),
 'app-entry-settings-flush':('app_entry_flow.py',['--persistent']),
 'controller-multisig-import-signer':('controller_multisig_flow.py',['--select-seed','--load-descriptor','--scan-psbt','--import-seed']),
 'profile-lvgl-idle':('frontend_resources.py',['--profile']),
 'resources-lvgl':('frontend_resources.py',[]),
 'resources-pil':('frontend_resources.py',['--legacy']),
 'controller-seed-scan-12':('controller_seed_scan.py',[]),
 'controller-seed-scan-24':('controller_seed_scan.py',['--24']),
 'controller-multisig-mismatch':('controller_multisig_flow.py',['--mismatch']),
 'controller-multisig-scan':('controller_multisig_flow.py',['--select-seed','--load-descriptor','--scan-psbt']),
 'controller-multisig-descriptor':('controller_multisig_flow.py',['--select-seed','--load-descriptor']),
 'controller-multisig-select-seed':('controller_multisig_flow.py',['--select-seed']),
 'controller-multisig-cancel':('controller_multisig_flow.py',['--cancel']),
 'controller-multisig':('controller_multisig_flow.py',[]),
 'multisig-signing':('multisig_signing_flow.py',['--display']),
 'multisig-model':('multisig_model.py',[]),
 'microsd-events':('microsd_events.py',[]),
 'app-entry-sigterm-camera':('app_entry_flow.py',['--sigterm','--camera']),
 'app-entry-sigterm':('app_entry_flow.py',['--sigterm']),
 'app-entry-flow':('app_entry_flow.py',[]),
 'app-entry-check':('app_entry_check.py',[]),
 'controller-home-battery':('controller_flow.py',['--small-ram','--home-battery-fixture']),
 'home-battery-protocol':('home_battery_protocol.py',[]),
 'io-wipe':('wipe_flow.py',['--small-ram','--io']),
 'controller-io':('controller_io_flow.py',[]),
 'io-protocol':('io_protocol.py',[]),
 'controller-donate':('controller_info_flow.py',['--small-ram','--donate']),
 'controller-calibration-charging':('controller_calibration_flow.py',['--display','--charging-abort']),
 'controller-calibration':('controller_calibration_flow.py',['--display']),
 'calibration':('calibration_flow.py',['--display']),
 'controller-network-fixture':('controller_info_flow.py',['--small-ram','--network-fixture']),
 'controller-network-absent':('controller_info_flow.py',['--small-ram','--network-absent']),
 'controller-hardening':('controller_info_flow.py',['--small-ram','--hardening']),
 'controller-battery-fixture':('controller_info_flow.py',['--small-ram','--battery-fixture']),
 'controller-battery-absent':('controller_info_flow.py',['--small-ram','--battery-not-detected']),
 'live-info-protocol':('live_info_protocol.py',[]),
 'controller-memory-info':('controller_info_flow.py',['--small-ram','--memory-info']),
 'controller-version':('controller_info_flow.py',['--small-ram']),
 'controller-system-info':('controller_info_flow.py',['--small-ram','--system-info']),
 'textqr-output-confirm':('textqr_more_flow.py',['--display']),
 'textqr':('textqr_flow.py',['--display']),
 'power-presentation':('power_flow.py',['--display']),
 'controller-settingsqr-scan':('controller_settingsqr_flow.py',['--small-ram','--scan']),
 'controller-settingsqr':('controller_settingsqr_flow.py',['--small-ram']),
 'controller-settingsqr-cancel':('controller_settingsqr_flow.py',['--small-ram','--cancel']),
 'settingsqr':('settingsqr_flow.py',['--display']),
 'entropy-wipe-timer':('wipe_flow.py',['--small-ram','--entropy','--real-timer']),
 'entropy-wipe':('wipe_flow.py',['--small-ram','--entropy']),
 'controller-entropy-generate':('controller_entropy_flow.py',['--small-ram','--generate']),
 'controller-entropy-luma':('controller_entropy_flow.py',['--small-ram','--cancel','--sample-luma']),
 'controller-entropy-gc':('controller_entropy_flow.py',['--small-ram','--cancel','--collect-before-camera']),
 'controller-entropy':('controller_entropy_flow.py',['--small-ram']),
 'controller-entropy-cancel':('controller_entropy_flow.py',['--small-ram','--cancel']),
 'entropy-fallback':('entropy_fallback_hardware.py',['--display']),
 'camera-loaded-soak':('camera_flow.py',['--display','--tools-loaded','--soak']),
 'entropy-sample-pixels':('entropy_sample_pixels.py',[]),
 'image-entropy-control':('image_entropy_physical.py',['--display','--no-display-updates']),
 'camera':('camera_flow.py',['--display']),
 'camera-loaded':('camera_flow.py',['--display','--tools-loaded']),
 'image-entropy-physical':('image_entropy_physical.py',['--display']),
 'entropy-camera':('entropy_camera_hardware.py',[]),
 'import-profile':('import_profile.py',[]),
 'image-entropy':('image_entropy_flow.py',['--display']),
 'coin':('coin_flow.py',['--display']),
 'final-word':('final_word_flow.py',['--display']),
 'explorer':('explorer_flow.py',['--display']),
 'descriptor':('descriptor_flow.py',['--display']),
 'message-signing':('message_signing_flow.py',['--display']),
 'transcription-registration':('transcription_registration.py',[]),
 'encrypted-review':('encrypted_review_flow.py',['--display']),
 'encrypted-entry':('encrypted_entry_flow.py',['--display']),
 'backup-quiz':('backup_quiz_flow.py',[]),
 'seedqr-confirmation':('seedqr_confirmation_flow.py',[]),
 'transcription':('transcription_flow.py',[]),
 'transcription-protocol':('transcription_protocol.py',[]),
 'screensaver':('screensaver_flow.py',[]),
 'startup':('controller_flow.py',['--startup','--small-ram']),
}

def owners(output):
    found=[]
    for line in output.splitlines()[1:]:
        fields=line.split()
        if len(fields)<3 or not fields[0].isdigit():continue
        command=' '.join(fields[2:])
        if command.startswith('['):continue # Zombie/kernel task, no live device owner.
        names=[word.rsplit('/',1)[-1].strip('{}') for word in fields[2:4]]
        if any(name.startswith('python') or name in ('shieldsigner-lvgl-host','shieldsigner-qr-reader') for name in names) or 'stream-sc3336' in fields[2:]:
            found.append(dict(pid=int(fields[0]),command=command))
    return found

def diagnostic_pids(call,script):
    """Match full NUL-delimited argv, never ps's truncated command column."""
    matches=[]
    for owner in owners(call('shell','ps','-o','pid,ppid,args')):
        try: argv=call('shell','cat',f'/proc/{owner["pid"]}/cmdline').split('\0')
        except subprocess.CalledProcessError:continue # Process exited during observation.
        if argv and Path(argv[0]).name.startswith('python') and script in argv[1:]:
            matches.append(owner['pid'])
    return matches

def assess(output,exit_code,timed_out=False):
    receipts=[]
    for line in output.splitlines():
        try:value=json.loads(line)
        except ValueError:continue
        if isinstance(value,dict) and 'passed' in value:receipts.append(value)
    receipt=receipts[0] if len(receipts)==1 else None
    passed=not timed_out and exit_code==0 and receipt is not None and receipt.get('passed') is True and 'Traceback (most recent call last):' not in output
    return passed,receipt

def remote_digests(call,remote,paths,relative_root=None):
    result={}
    # ADB rejects shell commands beyond its bounded command-string length.
    for offset in range(0,len(paths),16):
        names=[remote+'/'+(str(path.relative_to(relative_root)) if relative_root is not None else path.name) for path in paths[offset:offset+16]]
        for line in call('shell','sha256sum',*names).splitlines():
            digest,name=line.split()
            if name not in names or name in result:raise RuntimeError('Unexpected deployed hash response')
            result[name]=digest
    return result

def owner_log_paths(call):
    try:return set(call('shell','find','/tmp/shieldsigner-camera','-type','f','-name','owner.log').splitlines())
    except subprocess.CalledProcessError:return set()

def owner_events(output):
    events=[]
    for line in output.splitlines():
        try:event=json.loads(line)
        except ValueError:continue
        if isinstance(event,dict) and (event.get('error') or event.get('event')=='ae-event-channel-metrics'):
            events.append({key:event[key] for key in ('event','error','success','cleanupErrors','metrics') if key in event})
    return events

def owner_failure_metadata(call,before):
    records=[]
    for path in sorted(owner_log_paths(call)-before):
        if not path.startswith('/tmp/shieldsigner-camera/') or not path.endswith('/owner.log') or '..' in Path(path).parts:raise ValueError('Unexpected owner log path')
        records.append(dict(path=path,events=owner_events(call('shell','tail','-c','131072',path))))
    return records

def runtime_cache_files(directory,native_sha):
    """Check that the frozen cache belongs to this exact diagnostic runtime."""
    import package
    package.verify(directory)
    manifest=json.loads((directory/'runtime-manifest.json').read_text())
    if manifest['nativeBuild']['binarySha256']!=native_sha:raise ValueError('Runtime bundle native binary differs')
    root=directory/package.PREFIX/'python'
    for path in root.glob('*.py'):
        source=HERE/'python'/path.name
        if not source.is_file() or sha256(source)!=sha256(path):raise ValueError('Runtime bundle Python differs: '+path.name)
    if sha256(root/'source-guards.json')!=sha256(HERE/'source-guards.json'):raise ValueError('Runtime bundle source guards differ')
    return root/'import-cache',dict(manifestSha256=sha256(directory/'runtime-manifest.json'),hasSourceCache=bool(manifest.get('compiledSourceCache')),normalBytecodePrefix='/usr/lib/shieldsigner-lvgl/bytecode' if manifest.get('compiledSourceCache') else None)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('check',choices=CASES)
    parser.add_argument('--serial',help='ADB target; omitted only when exactly one device is connected')
    parser.add_argument('--timeout',type=int,default=180)
    parser.add_argument('--bytecode-cache',action='store_true',help='Use isolated checked-hash bytecode under /userdata')
    parser.add_argument('--fresh-normal-cache',action='store_true',help='With --runtime-bundle, simulate first boot without ordinary source caches')
    parser.add_argument('--runtime-bundle',type=Path,help='Use a frozen bundle import cache with the staged launcher cache mode; no installation')
    parser.add_argument('--import-profile',action='store_true',help='Include Python importtime metadata in the diagnostic log')
    args=parser.parse_args()
    if args.fresh_normal_cache and not args.runtime_bundle:parser.error('--fresh-normal-cache requires --runtime-bundle')
    if args.runtime_bundle and args.bytecode_cache:parser.error('--runtime-bundle and --bytecode-cache select different cache modes')
    if args.timeout<=0:parser.error("--timeout must be positive")
    binary=DIST/'build/shieldsigner-lvgl';manifest=json.loads((binary.parent/'build-manifest.json').read_text())
    if manifest['target']!='arm-linux-musleabihf' or manifest['inputs']!=inputs(HERE) or manifest['binarySha256']!=sha256(binary):raise RuntimeError('Native artifact is stale; run mise run lvgl:app:build')
    devices=subprocess.check_output(['adb','devices'],text=True,timeout=30)
    serials=[line.split()[0] for line in devices.splitlines()[1:] if len(line.split())==2 and line.split()[1]=='device']
    serial=args.serial
    if serial is None:
        if len(serials)!=1:raise RuntimeError('Select one connected board with --serial')
        serial=serials[0]
    if serial not in serials:raise RuntimeError('Selected board is not connected/authorized')
    adb=['adb','-s',serial]
    def call(*command):return subprocess.check_output([*adb,*command],text=True,stderr=subprocess.STDOUT,timeout=30)
    # Read-only ownership check. Never stop an app or camera behind the user.
    processes=call('shell','ps','-o','pid,ppid,args')
    if owners(processes):raise RuntimeError('A Python/native owner is already running; finish that session before hardware checks')
    previous_owner_logs=owner_log_paths(call)
    script,arguments=CASES[args.check]
    bundle=[*sorted((HERE/'python').glob('*.py')),*sorted((HERE/'tests').glob('*.py')),HERE/'source-guards.json']
    bundle_hashes={str(path.relative_to(HERE)):sha256(path) for path in bundle}
    if len({path.name for path in bundle})!=len(bundle):raise RuntimeError('Diagnostic bundle has colliding basenames')
    runner_hash=sha256(__file__)
    remote='/userdata/shieldsigner-lvgl-app'
    remote_binary='/tmp/shieldsigner-lvgl-host'
    call('shell','mkdir','-p',remote)
    call('shell','rm','-rf',remote+'/import-cache',remote+'/source-cache')
    call('push',str(binary),remote_binary)
    call('push',str(binary.parent/'build-manifest.json'),remote_binary+'.manifest.json')
    if json.loads(call('shell','cat',remote_binary+'.manifest.json'))!=manifest:raise RuntimeError('Deployed native build manifest mismatch')
    call('push',*[str(path) for path in bundle],remote+'/')
    remote_hashes=remote_digests(call,remote,bundle)
    if any(remote_hashes.get(remote+'/'+path.name)!=bundle_hashes[str(path.relative_to(HERE))] for path in bundle):raise RuntimeError('Deployed Python/test bundle hash mismatch')
    deployed=call('shell','sha256sum',remote_binary).split()[0]
    if deployed!=manifest['binarySha256']:raise RuntimeError('Deployed native binary hash mismatch')
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    destination=LVGL_HARDWARE_CHECKS;destination.mkdir(parents=True,exist_ok=True)
    prefix=destination/(args.check+'-'+stamp)
    runtime_info=None
    if args.runtime_bundle:
        local_cache,runtime_info=runtime_cache_files(args.runtime_bundle.resolve(),deployed)
        cached=sorted(p for p in local_cache.iterdir() if p.is_file())
        call('push',str(local_cache),remote+'/import-cache')
        uploaded=remote_digests(call,remote+'/import-cache',cached)
        if any(uploaded.get(remote+'/import-cache/'+p.name)!=sha256(p) for p in cached):raise ValueError('Deployed runtime cache differs')
        runtime_info['files']={p.name:sha256(p) for p in cached}
        if runtime_info['hasSourceCache']:
            local_sources=local_cache.parent.parent/'bytecode';remote_sources=remote+'/source-cache'
            source_files=sorted(p for p in local_sources.rglob('*') if p.is_file())
            call('push',str(local_sources),remote_sources)
            uploaded=remote_digests(call,remote_sources,source_files,relative_root=local_sources)
            if any(uploaded.get(remote_sources+'/'+str(p.relative_to(local_sources)))!=sha256(p) for p in source_files):raise ValueError('Deployed source cache differs')
            # Rebase only the diagnostic copy's cache lookup paths. CPython
            # fixes cached code filenames to the actual matching source path.
            record=json.loads((local_sources/'index.json').read_text());rebased=[]
            call('shell','mkdir','-p',remote_sources+remote)
            for item in record['entries']:
                if item['filename'].startswith('/usr/lib/shieldsigner-lvgl/python/'):
                    destination=remote_sources+remote+'/'+Path(item['file']).name
                    call('shell','cp',remote_sources+'/'+item['file'],destination);rebased.append(item['filename'])
            runtime_info['sourceCacheIndexSha256']=sha256(local_sources/'index.json')
            runtime_info['rebasedDiagnosticSources']=rebased
    cache_info=None
    cache_prefix='/tmp/lvgl-check-'+stamp
    if args.bytecode_cache:
        cache_prefix='/userdata/shieldsigner-lvgl-bytecode'
        preparation=[*adb,'shell','python3','-B','-X','pycache_prefix='+cache_prefix,remote+'/bytecode_cache.py','/opt/src/seedsigner','/usr/lib/shieldsigner-camera/python',remote]
        output=subprocess.check_output(preparation,text=True,timeout=360)
        cache_info=json.loads(output.strip())
        if not cache_info.get('prepared') or not cache_info.get('checkedHash'):raise RuntimeError('Bytecode cache preparation failed')

        imports=subprocess.check_output(remote_command(adb,['python3','-B',remote+'/import_cache.py','/opt/src',remote+'/source-guards.json',cache_prefix+'/lvgl-imports']),text=True,timeout=120)
        cache_info['guardedImports']=json.loads(imports.strip())
        prefix.with_suffix('.cache.json').write_text(json.dumps(cache_info,indent=2)+'\n')
    python_options=['-X','importtime'] if args.import_profile else []
    selected_prefix=cache_prefix
    if args.runtime_bundle:
        selected_prefix=remote+'/source-cache' if runtime_info['hasSourceCache'] and not args.fresh_normal_cache else cache_prefix if args.fresh_normal_cache else None
        runtime_info.update(normalBytecodePrefix=selected_prefix,coldSourceSimulation=args.fresh_normal_cache,shippedSourceCacheUsed=runtime_info['hasSourceCache'] and not args.fresh_normal_cache)
    cache_options=['-X','pycache_prefix='+selected_prefix] if selected_prefix else []
    command=remote_command(adb,['python3',*python_options,'-B',*cache_options,remote+'/'+script,remote_binary,*arguments])
    timed_out=False;exit_code=None;interrupted=False
    with prefix.with_suffix('.log').open('w') as log:
        process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
        try:exit_code=process.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            timed_out=True
            # Keep ADB alive while the exact remote Python owner runs finally.
            for pid in diagnostic_pids(call,remote+'/'+script):
                call('shell','kill','-INT',str(pid));interrupted=True
            deadline=time.monotonic()+10
            while time.monotonic()<deadline:
                if not diagnostic_pids(call,remote+'/'+script):break
                time.sleep(.25)
            try:exit_code=process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                # Do not force-kill remote owners; report any remaining below.
                process.terminate()
                try:exit_code=process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill();exit_code=process.wait()
    output=prefix.with_suffix('.log').read_text()
    passed,receipt=assess(output,exit_code,timed_out)
    remaining=owners(call('shell','ps','-o','pid,ppid,args'))
    if args.runtime_bundle:call('shell','rm','-rf',remote+'/import-cache',remote+'/source-cache')
    worktree_changed=manifest['inputs']!=inputs(HERE) or any(sha256(path)!=bundle_hashes[str(path.relative_to(HERE))] for path in bundle) or sha256(__file__)!=runner_hash
    passed=passed and not remaining and not worktree_changed
    owner_diagnostics=None
    if not passed:
        try:owner_diagnostics=owner_failure_metadata(call,previous_owner_logs)
        except (OSError,ValueError,subprocess.SubprocessError) as exc:owner_diagnostics={'collectionError':str(exc)}
    result=dict(deploymentRoot=remote,remoteBinary=remote_binary,ownerDiagnostics=owner_diagnostics,passed=passed,check=args.check,importProfile=args.import_profile,bytecodeCache=cache_info,runtimeBundleImportCache=runtime_info,binarySha256=deployed,buildManifest=manifest,bundleSha256=bundle_hashes,remoteBundleVerified=True,freshBytecodeCachePrefix=not args.bytecode_cache and (not args.runtime_bundle or args.fresh_normal_cache),checkedHashBytecodeCache=bool(cache_info),worktreeChangedDuringCheck=worktree_changed,result=receipt,exitCode=exit_code,timedOut=timed_out,ownedDiagnosticInterrupted=interrupted,remainingOwnerPids=[owner['pid'] for owner in remaining],runnerSha256=runner_hash,log=str(prefix.with_suffix('.log').relative_to(REPO)))
    prefix.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=passed,check=args.check,receipt=str(prefix.with_suffix('.json').relative_to(REPO)),log=result['log'])))
    if not passed:raise RuntimeError('Hardware check did not produce one successful receipt; inspect the log')
if __name__=='__main__':main()
