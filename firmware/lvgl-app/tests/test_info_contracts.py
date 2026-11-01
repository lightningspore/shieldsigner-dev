import sys,unittest
from datetime import datetime
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from contracts import configuration
class InfoContractTests(unittest.TestCase):
    def test_version_uses_upstream_with_original_timestamp_format(self):
        builder,cfg=configuration(type('VersionScreen',(),{}),dict(version_name='0.1-dev',version_fork='public/fork',short_commit_hash='1234567',version_timestamp=datetime(2026,10,30,12,34,56)))
        self.assertEqual(builder,'version_screen');self.assertEqual(cfg['version_timestamp'],'2026-10-30 12:34:56 UTC')
        self.assertEqual(cfg['version_fork'],'public/fork');self.assertEqual(cfg['short_commit_hash'],'1234567')
    def test_system_info_preserves_order_and_omits_absent_provenance(self):
        builder,cfg=configuration(type('SystemInfoScreen',(),{}),dict(platform_name='Luckfox',platform_variant='Pico',firmware_version='test',source_location='MicroSD',system_serial='PUBLIC',microsd_serial='FIXTURE'))
        self.assertEqual(builder,'button_list_screen')
        self.assertEqual(cfg['text'].splitlines(),['Platform: Luckfox','Variant: Pico','Firmware: test','Source: MicroSD','Serial (CPU): PUBLIC','Serial (MicroSD): FIXTURE'])
        self.assertEqual(cfg['button_list'],[])
