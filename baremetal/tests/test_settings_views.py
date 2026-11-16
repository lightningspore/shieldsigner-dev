# SPDX-License-Identifier: MIT
"""Original settings business decisions and native selection contract boundaries."""

import ast, copy, hashlib, json, sys, types, unittest
from pathlib import Path
from unittest.mock import patch

root = Path(__file__).resolve().parents[1]
sys.path.append(str(root / 'app'))
from seedsigner_port import view_settings, settings_screens
from seedsigner_port.settings_store import Settings, SettingsConstants as C, SettingsDefinition as D
from seedsigner_port.navigation import Destination
from seedsigner_port.button_options import ButtonOption
from seedsigner_port.gui_constants import GUIConstants, SeedSignerIconConstants


class HarnessView:
    reply = 1000
    calls = []

    def __init__(self):
        self.settings = Settings.get_instance()

    def run_screen(self, screen_class, **kwargs):
        self.calls.append((screen_class.__name__, kwargs))
        self.screen = types.SimpleNamespace(
            scroll_y=112, buttons=[types.SimpleNamespace(scroll_y=112)]
        )
        return self.reply


class MainMenuView:
    pass


class BackStackView:
    pass


class WarningScreen:
    pass


class SettingsViewTests(unittest.TestCase):
    def setUp(self):
        Settings._instance = None
        view_settings._CACHE.clear()
        HarnessView.calls = []
        HarnessView.reply = 1000
        actual = view_settings._dependency

        def dependency(module, attribute=None):
            if module == 'seedsigner.views.view' and attribute == 'View':
                return HarnessView
            if module == 'seedsigner.views.view' and attribute == 'MainMenuView':
                return MainMenuView
            if module == 'seedsigner.views.view' and attribute == 'BackStackView':
                return BackStackView
            if module == 'seedsigner.gui.screens.screen' and attribute == 'WarningScreen':
                return WarningScreen
            return actual(module, attribute)

        self.patch = patch.object(view_settings, '_dependency', dependency)
        self.patch.start()
        source = (
            root.parent
            / 'dist/firmware/sources/lvgl/application/src/seedsigner/views/settings_views.py'
        )
        classes = [
            n
            for n in ast.parse(source.read_text()).body
            if isinstance(n, ast.ClassDef) and n.name in view_settings._SUPPORTED
        ]
        scope = {
            'RET_CODE__BACK_BUTTON': 1000,
            'View': HarnessView,
            'Settings': Settings,
            'SettingsConstants': C,
            'SettingsDefinition': D,
            'ButtonOption': ButtonOption,
            'GUIConstants': GUIConstants,
            'SeedSignerIconConstants': SeedSignerIconConstants,
            'Destination': Destination,
            'MainMenuView': MainMenuView,
            'BackStackView': BackStackView,
            'ButtonListScreen': settings_screens.SettingsButtonListScreen,
            'settings_screens': settings_screens,
            'WarningScreen': WarningScreen,
            '_': lambda text: text,
        }
        # The original local WarningScreen import is a presentation boundary only.
        for node in ast.walk(ast.Module(body=classes, type_ignores=[])):
            if isinstance(node, ast.FunctionDef):
                node.body = [
                    n for n in node.body if not isinstance(n, (ast.Import, ast.ImportFrom))
                ]
        exec(
            compile(
                ast.fix_missing_locations(ast.Module(body=classes, type_ignores=[])),
                str(source),
                'exec',
            ),
            scope,
        )
        self.reference = scope

    def tearDown(self):
        self.patch.stop()
        view_settings._CACHE.clear()
        Settings._instance = None

    def result(self, namespace, name, args, reply, initial=None):
        Settings._instance = None
        if initial:
            for key, value in initial.items():
                Settings.get_instance().set_value(key, copy.deepcopy(value), save=False)
        HarnessView.reply = reply
        HarnessView.calls = []
        cls = namespace[name] if isinstance(namespace, dict) else getattr(namespace, name)
        value = cls(**args).run()
        normalize = lambda data: {
            k: (v.__name__ if isinstance(v, type) else v) for k, v in (data or {}).items()
        }
        return (
            value.View_cls.__name__,
            normalize(value.view_args),
            value.skip_current_view,
            value.clear_history,
            copy.deepcopy(Settings.get_instance()._data),
        )

    def test_original_single_select_and_return_position(self):
        args = {'attr_name': C.SETTING__NETWORK, 'parent_initial_scroll': 112}
        for reply in (0, 1, 1000):
            self.assertEqual(
                self.result(self.reference, 'SettingsEntryUpdateSelectionView', args, reply),
                self.result(view_settings, 'SettingsEntryUpdateSelectionView', args, reply),
            )

    def test_original_multiselect_empty_requires_selection_on_back(self):
        args = {'attr_name': C.SETTING__SIG_TYPES}
        initial = {C.SETTING__SIG_TYPES: [C.SINGLE_SIG]}
        self.assertEqual(
            self.result(self.reference, 'SettingsEntryUpdateSelectionView', args, 0, initial),
            self.result(view_settings, 'SettingsEntryUpdateSelectionView', args, 0, initial),
        )
        result = self.result(
            view_settings,
            'SettingsEntryUpdateSelectionView',
            args,
            1000,
            {C.SETTING__SIG_TYPES: []},
        )
        self.assertEqual(result[0], 'SettingsSelectionRequiredWarningView')
        self.assertEqual(
            self.result(
                self.reference,
                'SettingsEntryUpdateSelectionView',
                args,
                1000,
                {C.SETTING__SIG_TYPES: []},
            ),
            result,
        )

    def test_original_menu_back_destinations_and_actual_scroll_metadata(self):
        for visibility in (
            C.VISIBILITY__GENERAL,
            C.VISIBILITY__ADVANCED,
            C.VISIBILITY__HARDWARE,
            C.VISIBILITY__DEVELOPER,
        ):
            args = {'visibility': visibility}
            self.assertEqual(
                self.result(self.reference, 'SettingsMenuView', args, 1000),
                self.result(view_settings, 'SettingsMenuView', args, 1000),
            )
        visibility = D.get_settings_entry(C.SETTING__NETWORK).visibility
        entries = D.get_settings_entries(visibility=visibility)
        index = next(i for i, e in enumerate(entries) if e.attr_name == C.SETTING__NETWORK)
        value = self.result(view_settings, 'SettingsMenuView', {'visibility': visibility}, index)
        self.assertEqual(value[1], {'attr_name': C.SETTING__NETWORK, 'parent_initial_scroll': 112})
        self.assertEqual(
            self.result(self.reference, 'SettingsMenuView', {'visibility': visibility}, index),
            value,
        )

    def test_fixed_platform_change_fails_before_mutation(self):
        from seedsigner_port.settings_platform import UnsupportedSettingsAction

        settings = Settings.get_instance()
        old = copy.deepcopy(settings._data)
        HarnessView.reply = 0
        with self.assertRaises(UnsupportedSettingsAction):
            view_settings.SettingsEntryUpdateSelectionView(C.SETTING__PERSISTENT_SETTINGS).run()
        self.assertEqual(settings._data, old)

    def test_unported_os_utilities_are_explicitly_unavailable(self):
        from seedsigner_port.decode_platform import FeatureUnavailable

        for name in (
            'SystemInfoView',
            'RestartPCSCView',
            'SCardReaderTestView',
            'SettingPBKDF2IterationsView',
        ):
            with self.assertRaises(FeatureUnavailable):
                getattr(view_settings, name)

    def test_original_source_coverage_and_provenance(self):
        r = json.loads((root / 'app/settings-views-provenance.json').read_text())
        source = (
            root.parent
            / 'dist/firmware/sources/lvgl/application/src/seedsigner/views/settings_views.py'
        )
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), r['sourceSha256'])
        self.assertEqual(
            hashlib.sha256(
                (root / 'app/seedsigner_port/view_settings.py').read_bytes()
            ).hexdigest(),
            r['outputSha256'],
        )
        original = {
            n.name: n for n in ast.parse(source.read_text()).body if isinstance(n, ast.ClassDef)
        }
        actual = {
            n.body[0].name: n.body[0]
            for n in ast.parse((root / 'app/seedsigner_port/view_settings.py').read_text()).body
            if isinstance(n, ast.FunctionDef) and n.name.startswith('_make_')
        }
        self.assertEqual(set(original), set(actual))
        for name in original:
            methods = lambda n: {m.name for m in n.body if isinstance(m, ast.FunctionDef)}
            self.assertEqual(methods(original[name]), methods(actual[name]))


class SelectionContractTests(unittest.TestCase):
    def test_original_selection_style_and_checked_values(self):
        from seedsigner_port.button_options import ButtonOption

        for kind, style in (('multiselect', 'checkbox'), ('select_1', 'checked_selection')):
            screen = settings_screens.SettingsEntryUpdateSelectionScreen(
                display_name='Public setting',
                help_text='Public help',
                settings_entry_type=kind,
                button_data=[ButtonOption('One'), ButtonOption('Two')],
                checked_buttons=[1],
                selected_button=1,
            )
            builder, cfg = screen.configuration()
            self.assertEqual(builder, 'button_list_screen')
            self.assertEqual(cfg['button_style'], style)
            self.assertEqual(cfg['text'], 'Public setting\n\nPublic help')
            self.assertEqual(cfg['checked_buttons'], [1])
            self.assertEqual(cfg['initial_selected_index'], 1)

    def test_original_no_options_placeholder_and_hidden_text_rejection(self):
        builder, cfg = settings_screens.SettingsEntryUpdateSelectionScreen(
            display_name='Public', button_data=[]
        ).configuration()
        self.assertEqual(cfg['button_list'], ['No options available'])
        with self.assertRaises(ValueError):
            settings_screens.SettingsEntryUpdateSelectionScreen(
                display_name='Hidden\0value'
            ).configuration()


class NativeSettingsScrollTests(unittest.TestCase):
    def test_real_session_scroll_restore_and_snapshot(self):
        calls = []
        backend = types.SimpleNamespace(
            scroll_to_y=lambda y: calls.append(('restore', y)), scroll_y=lambda: 137
        )
        session = types.SimpleNamespace(
            show_screen=lambda name, args: calls.append(('show', name)),
            wait=lambda: ('select', 2),
            screen_result=lambda event: 2,
        )
        renderer = types.SimpleNamespace(backend=backend, session=session)
        with patch.dict(
            sys.modules,
            {
                'seedsigner_port.renderer': types.SimpleNamespace(
                    Renderer=types.SimpleNamespace(get_instance=lambda: renderer)
                )
            },
        ):
            screen = settings_screens.SettingsButtonListScreen(scroll_y_initial_offset=112)
            self.assertEqual(screen.display(), 2)
        self.assertEqual(calls, [('show', 'ButtonListScreen'), ('restore', 112)])
        self.assertEqual(screen.scroll_y, 137)
