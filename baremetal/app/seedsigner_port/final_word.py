# SPDX-License-Identifier: MIT
"""Final-word presentation contracts and coin-flip keyboard for native builders.

Mirrors firmware/lvgl-app/python/final_word_contracts.py and its
ToolsCoinFlipEntryScreen keyboard contract. Original Views calculate entropy and
checksum; this module only shapes native screen configuration/results.
"""

NAMES = {
    'ToolsCalcFinalWordFinalizePromptScreen',
    'ToolsCalcFinalWordScreen',
    'ToolsCalcFinalWordDoneScreen',
}


def configure(name, a, cfg, _):
    cfg['is_bottom_list'] = True
    if name == 'ToolsCalcFinalWordFinalizePromptScreen':
        length = a['mnemonic_length']
        bits = a['num_entropy_bits']
        if (length, bits) not in ((12, 7), (24, 3)):
            raise ValueError('Unsupported mnemonic entropy size')
        cfg['top_nav']['title'] = _('Build Final Word')
        cfg['text'] = _(
            'The {mnemonic_length}th word is built from {num_bits} more entropy bits plus auto-calculated checksum.'
        ).format(mnemonic_length=length, num_bits=bits)
        return 'button_list_screen', cfg
    if name == 'ToolsCalcFinalWordScreen':
        selected = a['selected_final_bits']
        checksum = a['checksum_bits']
        word = a['actual_final_word']
        input_word = a.get('selected_final_word')
        if (
            not isinstance(selected, str)
            or not isinstance(checksum, str)
            or not selected
            or not checksum
            or set(selected + checksum) - {'0', '1'}
        ):
            raise ValueError('Invalid final-word bits')
        if len(checksum) not in (4, 8) or len(selected) not in (11, 11 - len(checksum)):
            raise ValueError('Inconsistent final-word bit lengths')
        if not isinstance(word, str) or not word or '\0' in word:
            raise ValueError('Missing final word')
        if input_word is not None and (not isinstance(input_word, str) or '\0' in input_word):
            raise ValueError('Invalid selected word')
        cfg.update(
            your_input_text=_('Your input: "{}"').format(input_word or selected),
            checksum_label=_('Checksum'),
            final_word_text=_('Final Word: "{}"').format(word),
            selected_final_bits=selected,
            checksum_bits=checksum,
            has_selected_word=bool(input_word),
        )
        return 'tools_calc_final_word_screen', cfg
    if name == 'ToolsCalcFinalWordDoneScreen':
        length = a['mnemonic_word_length']
        if length not in (12, 24):
            raise ValueError('Unsupported mnemonic size')
        for key in ('final_word', 'fingerprint'):
            if not isinstance(a[key], str) or not a[key] or '\0' in a[key]:
                raise ValueError('Missing final-word display value')
            cfg[key] = a[key]
        cfg['top_nav']['title'] = _('12th Word') if length == 12 else _('24th Word')
        cfg['fingerprint_label'] = _('fingerprint')
        return 'tools_calc_final_word_done_screen', cfg
    raise NotImplementedError(name)


class ToolsCoinFlipEntryScreen:
    """Original coin-flip keyboard (charset "10", 4 columns) via native keyboard."""

    def __init__(self, return_after_n_chars):
        if type(return_after_n_chars) is not int or return_after_n_chars not in (3, 4, 5, 6, 7):
            raise ValueError('Unsupported coin flip count')
        self.total = return_after_n_chars

    def display(self):
        from seedsigner_port.renderer import Renderer
        from seedsigner_port.localization import gettext as _

        cfg = {
            'top_nav': {
                'title': _('Coin Flip {}/{}').format(1, self.total),
                'show_back_button': True,
                'show_power_button': False,
            },
            'keys': ['1', '0'],
            'cols': 4,
            'title_keystroke_template': _('Coin Flip {}/{}').format('{n}', '{total}'),
            'guidance_text': _('Heads = 1') + '\n' + _('Tails = 0'),
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
            raise ValueError('Unexpected native coin-flip keyboard result')
        value = event[2]
        if len(value) != self.total or any(c not in '01' for c in value):
            raise ValueError('Invalid native coin-flip entry')
        return value


def builtin_format(value, spec=''):
    """CPython format() equivalent; MicroPython has no format builtin."""
    return ('{:' + spec + '}').format(value)
