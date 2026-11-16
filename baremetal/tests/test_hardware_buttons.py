# SPDX-License-Identifier: MIT
"""Scanner raw-low checks must honor debounce/release and update real activity."""

import importlib.util, sys, types, unittest
from pathlib import Path
from unittest.mock import patch

root = Path(__file__).resolve().parents[1]
sys.path.append(str(root / 'app'))
import seedsigner_port


class HardwareActivityTest(unittest.TestCase):
    def test_low_check_activity_and_initial_hold(self):
        state = {'ms': 0, 'mask': 8}
        clock = types.SimpleNamespace(time=lambda: state['ms'] / 1000)
        spec = importlib.util.spec_from_file_location(
            'ss_hardware_buttons_test', root / 'app/seedsigner_port/hardware_buttons.py'
        )
        module = importlib.util.module_from_spec(spec)
        with patch.object(seedsigner_port, 'clock', clock, create=True), patch.dict(
            sys.modules, {'seedsigner_port.clock': clock}
        ):
            spec.loader.exec_module(module)
        buttons = module.HardwareButtons(read_mask=lambda: state['mask'], clock=lambda: state['ms'])
        state['ms'] = 50
        self.assertFalse(buttons.check_for_low('KEY_RIGHT'))  # Held at reset stays blocked.
        self.assertEqual(buttons.last_input_time, 0)
        state.update(mask=0, ms=51)
        buttons.check_for_low('KEY_RIGHT')
        state['ms'] = 62
        buttons.check_for_low('KEY_RIGHT')
        state.update(mask=8, ms=63)
        self.assertFalse(buttons.check_for_low('KEY_RIGHT'))
        self.assertEqual(buttons.last_input_time, 0)
        state['ms'] = 74
        self.assertTrue(buttons.check_for_low('KEY_RIGHT'))
        self.assertEqual(buttons.last_input_time, 74)
        self.assertFalse(buttons.check_for_low('KEY_LEFT'))
        self.assertEqual(buttons.last_input_time, 74)
        state.update(mask=0, ms=75)
        self.assertTrue(buttons.check_for_low('KEY_RIGHT'))  # Debounced release is not stable yet.
        state['ms'] = 86
        self.assertFalse(buttons.check_for_low('KEY_RIGHT'))
        self.assertEqual(buttons.last_input_time, 75)
