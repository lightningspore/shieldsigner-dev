# SPDX-License-Identifier: MIT
"""Host source/contract checks; scripted Back is not hardware UI qualification."""

import ast, copy, hashlib, json, sys, types, unittest
from pathlib import Path
from unittest.mock import patch

root = Path(__file__).resolve().parents[1]
sys.path.append(str(root / 'app'))


class PSBTViewsTest(unittest.TestCase):
    def test_provenance_and_complete_original_method_coverage(self):
        r = json.loads((root / 'app/psbt-views-provenance.json').read_text())
        source = (
            root.parent
            / 'dist/firmware/sources/lvgl/application/src/seedsigner/views/psbt_views.py'
        )
        out = root / 'app/seedsigner_port/view_psbt.py'
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), r['sourceSha256'])
        self.assertEqual(hashlib.sha256(out.read_bytes()).hexdigest(), r['outputSha256'])
        old = {
            n.name: n
            for n in ast.walk(ast.parse(source.read_bytes()))
            if isinstance(n, ast.ClassDef)
        }
        new = {
            n.name: n for n in ast.walk(ast.parse(out.read_bytes())) if isinstance(n, ast.ClassDef)
        }
        self.assertEqual(set(old), set(new))
        for name in old:
            methods = lambda n: {x.name for x in n.body if isinstance(x, ast.FunctionDef)}
            self.assertTrue(methods(old[name]) <= methods(new[name]), name)

    def test_original_approval_back_never_signs(self):
        from seedsigner_port import view_psbt as port
        from seedsigner_port.navigation import Destination
        from seedsigner_port.psbt_parser import RiskWarning

        back = type('BackStackView', (), {})

        class View:
            pass

        dependencies = {
            ('seedsigner.views.view', 'View'): View,
            ('seedsigner.gui.screens.screen', 'ButtonOption'): lambda text: text,
            ('seedsigner.gui.screens.screen', 'RET_CODE__BACK_BUTTON'): -1,
            ('seedsigner.views.view', 'BackStackView'): back,
            ('seedsigner.models.psbt_parser', 'RiskWarning'): RiskWarning,
            ('seedsigner_port.navigation', 'Destination'): Destination,
            ('seedsigner.gui.screens.psbt_screens', 'PSBTFinalizeScreen'): object,
        }

        def dependency(module, name=None):
            if (module, name) not in dependencies:
                raise AssertionError('Back reached provider ' + str((module, name)))
            return dependencies[module, name]

        # Calling the factory avoids mutating the production lazy class cache.
        with patch.object(port, '_dependency', dependency):
            cls = port._make_PSBTFinalizeView()
            view = cls()

            class NeverSign:
                def sign_with(self, *args):
                    raise AssertionError('Back signed a PSBT')

            psbt = NeverSign()
            parser = types.SimpleNamespace(locktime_is_enforced=False, risk_warnings=[])
            view.controller = types.SimpleNamespace(
                psbt=psbt, psbt_parser=parser, psbt_sign_with_satochip=False
            )
            screens = []
            view.run_screen = lambda screen, **kwargs: screens.append(kwargs) or -1
            result = view.run()
            self.assertIs(result.View_cls, back)
            self.assertIs(view.controller.psbt, psbt)
            self.assertEqual(screens[0]['button_data'], ['Approve transaction'])

    def test_original_contracts_and_op_return_visibility(self):
        from seedsigner_port import (
            psbt_contracts as port,
            psbt_formatting,
            settings_store as settings,
        )

        source = root.parent / 'firmware/lvgl-app/python/psbt_contracts.py'
        tree = ast.parse(source.read_bytes())
        # Execute the unchanged original configure function with its real native
        # formatting/settings and English catalog, not reconstructed expectations.
        scope = {'_': lambda s: s, 'ngettext': lambda a, b, n: a if n == 1 else b}
        for name in ('btc_amount_from_sats', 'format_btc', 'format_sats'):
            scope[name] = getattr(psbt_formatting, name)
        exec(
            compile(
                ast.Module(
                    body=[n for n in tree.body if isinstance(n, ast.FunctionDef)], type_ignores=[]
                ),
                str(source),
                'exec',
            ),
            scope,
        )
        cases = [
            (
                'PSBTOverviewScreen',
                {'spend_amount': 1, 'change_amount': 2, 'destination_addresses': ['bc1public']},
            ),
            (
                'PSBTMathScreen',
                {
                    'input_amount': 2100000000000000,
                    'num_inputs': 2,
                    'num_recipients': 1,
                    'spend_amount': 2099999999999900,
                    'fee_amount': 99,
                    'change_amount': 1,
                },
            ),
            ('PSBTAddressDetailsScreen', {'amount': 1, 'address': 'bc1public'}),
            (
                'PSBTChangeDetailsScreen',
                {'amount': 1, 'address': 'bc1public', 'is_change_addr_verified': True},
            ),
            ('PSBTFinalizeScreen', {'is_rbf': True, 'locktime_text': 'Locked until ~Mar 2031'}),
        ]
        cases += [
            ('PSBTOpReturnScreen', {'op_return_data': data})
            for data in (b'', b'hello', b'\xc3\xa9', b'\xff', b'a\0b')
        ]
        with patch.dict(sys.modules, {'seedsigner.models.settings': settings}):
            for name, args in cases:
                cfg = {'top_nav': {}, 'initial_selected_index': 0}
                self.assertEqual(
                    scope['configure'](name, args, copy.deepcopy(cfg)),
                    port.configure(name, args, copy.deepcopy(cfg)),
                    (name, args),
                )
            for fn in (scope['configure'], port.configure):
                with self.assertRaises(ValueError):
                    fn('PSBTAddressDetailsScreen', {'amount': -1}, {'top_nav': {}})
