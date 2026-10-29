import sys
import types
import unittest
from unittest.mock import patch
from shieldsigner_integration import import_memory_snapshot


class ImportSnapshotTests(unittest.TestCase):
    def test_only_module_presence_counts_and_patch_markers(self):
        modules = {'seedsigner': types.SimpleNamespace(),
                   'seedsigner.views.scan_views': types.SimpleNamespace(__shieldsigner_lazy_scan__={'static': True}),
                   'seedsigner.views.seed_views': None,
                   'pysatochip.CardConnector': types.SimpleNamespace(),
                   'PIL.Image': types.SimpleNamespace(),
                   'seedsigner.controller': types.SimpleNamespace(__shieldsigner_small_ram_profile__={'static': True})}
        with patch.object(sys, 'modules', modules):
            info = import_memory_snapshot('scan-start')
        self.assertEqual(info['moduleCount'], 5)
        self.assertEqual(info['prefixCounts']['seedsigner'], 3)
        self.assertFalse(info['present']['seedsigner.views.seed_views'])
        self.assertTrue(info['present']['pysatochip.CardConnector'])
        self.assertTrue(info['loadedScanModulePatched'])
        self.assertTrue(info['controllerPreloadPatched'])
        self.assertFalse(info['containsUserObjectsOrPayloads'])
        self.assertEqual(set(info['present']), set(import_memory_snapshot('startup')['present']))

    def test_phase_names_are_bounded_public_labels(self):
        with self.assertRaises(ValueError): import_memory_snapshot('arbitrary-user-content')

if __name__ == '__main__': unittest.main()
