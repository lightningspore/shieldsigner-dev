# SPDX-License-Identifier: MIT
import sys, unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / 'app'))
from seedsigner_port.screen_contracts import result
from seedsigner_port import visible_text


class PassphraseScreenTest(unittest.TestCase):
    def test_exact_native_text_and_back_result_contract(self):
        for text in ('', 'public', 'a\0b', '\\u00E9', 'é🙂', ' ' * 3, 'x' * 255):
            self.assertEqual(
                result((2, 0, text), 0, 'SeedAddPassphraseScreen'), {'passphrase': text}
            )
            self.assertEqual(
                result((6, 1, text), 0, 'SeedAddPassphraseScreen'),
                {'passphrase': text, 'is_back_button': True},
            )

    def test_non_text_events_cannot_discard_the_edit_buffer(self):
        for event in (
            (1, 1000, ''),
            (2, 1, 'text'),
            (6, 0, 'text'),
            (6, True, 'text'),
            (2, False, 'text'),
            (2, 0, b'text'),
            1000,
        ):
            with self.assertRaises(ValueError):
                result(event, 0, 'SeedAddPassphraseScreen')

    def test_nul_display_mapping_matches_existing_native_host(self):
        import importlib.util

        path = Path(__file__).resolve().parents[2] / 'firmware/lvgl-app/python/visible_text.py'
        spec = importlib.util.spec_from_file_location('original_visible_text', path)
        original = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(original)
        for value in ('public', 'a\0b', 'a\\0b', 'a\\\0b', 'é\0🙂'):
            self.assertEqual(visible_text.display(value), original.display(value))
            self.assertEqual(
                visible_text.title(value, 'Passphrase'), original.title(value, 'Passphrase')
            )
