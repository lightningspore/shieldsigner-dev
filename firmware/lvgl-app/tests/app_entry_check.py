"""Read-only launch preflight on actual image; no GPIO/Controller acquisition."""
import json,sys,tempfile
from pathlib import Path
from app import options,run
with tempfile.TemporaryDirectory(prefix='lvgl-entry-preflight-') as temporary:
    args=options(['--binary',sys.argv[1],'--settings',str(Path(temporary)/'settings.json'),'--check'])
    run(args)
    dummy=Path(temporary)/'mismatched-native';dummy.write_bytes(b'public mismatch fixture');dummy.chmod(0o700)
    invalid=options(['--binary',str(dummy),'--native-manifest',sys.argv[1]+'.manifest.json','--settings',str(Path(temporary)/'other.json'),'--check'])
    try:run(invalid)
    except ValueError as error:assert str(error)=='Native artifact hash mismatch'
    else:raise AssertionError('Mismatched native artifact accepted')
    from seedsigner.models.settings import Settings
    assert Settings._instance is None
    assert 'luckfox' not in sys.modules and 'seedsigner.controller' not in sys.modules
    assert not args.settings.exists()
    print(json.dumps(dict(passed=True,artifactMismatchRejected=True,guardedOriginalMain=True,settingsInstanceNotCreated=True,hardwareNotImported=True,controllerNotImported=True,settingsNotWritten=True,physicalDisplay=False)),flush=True)
