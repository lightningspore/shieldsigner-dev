import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from resources import smaps_snapshot

class ResourceMapTests(unittest.TestCase):
    def test_segments_aggregate_and_private_paths_addresses_are_omitted(self):
        text='''1000-2000 r-xp 0 00:00 1 /private/path/libpython3.12.so.1.0
Rss: 12 kB
Pss: 6 kB
2000-3000 rw-p 0 00:00 1 /private/path/libpython3.12.so.1.0
Rss: 4 kB
Swap: 8 kB
3000-4000 rw-p 0 00:00 0
Rss: 20 kB
Private_Dirty: 20 kB
4000-5000 r--p 0 00:00 2 /private/wallet-name
Rss: 4 kB
'''
        result=smaps_snapshot(text)
        groups={row['mapping']:row for row in result['mappings']}
        self.assertEqual(groups['libpython3.12.so.1.0']['Rss'],16)
        self.assertEqual(result['processTotals']['Rss'],40)
        self.assertEqual(result['processTotals']['Swap'],8)
        self.assertEqual(groups['[anonymous]']['Private_Dirty'],20)
        self.assertNotIn('private',str(result));self.assertNotIn('wallet-name',str(result));self.assertNotIn('1000',str(result))

    def test_unavailable_or_wrong_units_reject(self):
        with self.assertRaises(ValueError):smaps_snapshot('permission denied')
        with self.assertRaises(ValueError):smaps_snapshot('1000-2000 rw-p 0 00:00 0\nRss: 1 MB')
