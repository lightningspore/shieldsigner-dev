# SPDX-License-Identifier: MIT
"""Differential checks against original Seed's exact CPython codec expression."""

import importlib.util, json, random, re, unittest, unicodedata
from pathlib import Path

p = Path(__file__).resolve().parents[1] / 'app/seedsigner_port/passphrase.py'
spec = importlib.util.spec_from_file_location('native_passphrase', p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def reference(value):
    if not value:
        return ''
    saved = value
    value = re.sub(r'\\(?!u)', r'\\\\', value)
    try:
        value = bytes(value, encoding='raw_unicode_escape').decode('unicode_escape')
    except UnicodeDecodeError:
        value = saved
    return unicodedata.normalize('NFKD', value)


class PassphraseTests(unittest.TestCase):
    def test_original_codec_differential(self):
        values = [
            '',
            'é',
            'e\u0301',
            '㍍ガバヴァぱばぐゞちぢ十人十色',
            '\x00',
            '\\u0061',
            '\\\\u0061',
            '\\u005cu0061',
            '\\uD800\\uZ',
            '\\u',
            '\\u123',
            '\\U0001f600',
            '\\n',
            'abc\\',
            '\\x41',
        ]
        r = random.Random(20261114)
        atoms = [
            'a',
            'u',
            'U',
            '\\',
            '\\u0061',
            '\\u00e9',
            '\\uD800',
            '\\uDFFF',
            '\\uZ',
            '\\u123',
            '\\x20',
            'é',
            '\x00',
            '😀',
            'ガ',
            '\ufdfa',
        ]
        values.extend(
            ''.join(r.choice(atoms) for _ in range(r.randrange(1, 15))) for _ in range(10000)
        )
        for value in values:
            expected = reference(value)
            if any(0xD800 <= ord(c) <= 0xDFFF for c in expected):
                with self.assertRaises(UnicodeError):
                    m.normalize_passphrase(value)
            else:
                self.assertEqual(m.normalize_passphrase(value), expected, repr(value))

    def test_saved_ref_oracle(self):
        data = json.loads((p.parents[2] / 'unicode/passphrase-ref-oracle.json').read_text())
        for row in data['cases']:
            if row['utf8']:
                self.assertEqual(m.normalize_passphrase(row['input']), row['expected'])
            else:
                with self.assertRaises(UnicodeError):
                    m.normalize_passphrase(row['input'])

    def test_empty_and_types(self):
        for value in (None, False, 0):
            self.assertEqual(m.normalize_passphrase(value), '')
        for value in (True, 1, b'x'):
            with self.assertRaises(TypeError):
                m.normalize_passphrase(value)
