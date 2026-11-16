# SPDX-License-Identifier: MIT
"""Original six-face dice entry presented by the existing native keyboard."""


class ToolsDiceEntropyEntryScreen:
    def __init__(self, return_after_n_chars):
        from seedsigner_port.camera_entropy_mnemonic import DICE_ROLLS_REQUIRED

        if (
            type(return_after_n_chars) is not int
            or return_after_n_chars not in DICE_ROLLS_REQUIRED.values()
        ):
            raise ValueError('Unsupported source dice roll count')
        self.total = return_after_n_chars

    def display(self):
        from seedsigner_port.renderer import Renderer
        from seedsigner_port.localization import gettext as _
        from seedsigner_port.gui_constants import FontAwesomeIconConstants as F

        keys = [F.DICE_ONE, F.DICE_TWO, F.DICE_THREE, F.DICE_FOUR, F.DICE_FIVE, F.DICE_SIX]
        cfg = {
            'top_nav': {
                'title': _('Dice Roll {}/{}').format(1, self.total),
                'show_back_button': True,
                'show_power_button': False,
            },
            'keys': keys,
            'cols': 3,
            'keys_to_values': {key: str(index + 1) for index, key in enumerate(keys)},
            'keyboard_font': 'icon',
            'title_keystroke_template': _('Dice Roll {}/{}').format('{n}', '{total}'),
            'return_after_n_chars': self.total,
            'show_save_button': False,
            'show_cursor_keys': False,
            'initial_value': '',
        }
        renderer = Renderer.get_instance()
        renderer.session.show('keyboard_screen', cfg)
        event = renderer.session.wait()
        if event == 1000 or (
            isinstance(event, tuple) and len(event) == 3 and event[0] == 1 and event[1] == 1000
        ):
            return 1000
        if (
            not isinstance(event, tuple)
            or len(event) != 3
            or event[0] != 2
            or event[1] != 0
            or type(event[2]) is not str
        ):
            raise ValueError('Unexpected native dice keyboard result')
        value = event[2]
        if len(value) != self.total or any(char not in '123456' for char in value):
            raise ValueError('Invalid native dice roll entry')
        return value
