# SPDX-License-Identifier: MIT
"""Original settings screen contracts over actual native list/scroll state."""

from seedsigner_port.screen_contracts import configuration, result
from seedsigner_port.localization import gettext as _


class SettingsButtonListScreen:
    """Original Settings View's menu screen, with real native scroll metadata."""

    def __init__(self, **kwargs):
        self.args = kwargs
        self.scroll_y = 0

    def display(self):
        from seedsigner_port.renderer import Renderer

        renderer = Renderer.get_instance()
        session = renderer.session
        session.show_screen('ButtonListScreen', self.args)
        renderer.backend.scroll_to_y(self.args.get('scroll_y_initial_offset', 0))
        event = session.wait()
        self.scroll_y = renderer.backend.scroll_y()
        return session.screen_result(event)


class SettingsEntryUpdateSelectionScreen:
    def __init__(
        self,
        display_name=None,
        help_text=None,
        checked_buttons=None,
        settings_entry_type='enabled_disabled',
        **kwargs,
    ):
        self.args = kwargs
        self.display_name = display_name
        self.help_text = help_text
        self.checked_buttons = checked_buttons
        self.settings_entry_type = settings_entry_type

    def configuration(self):
        args = dict(
            self.args, title='Settings', is_bottom_list=True, checked_buttons=self.checked_buttons
        )
        builder, cfg = configuration('ButtonListScreen', args, _)
        text = []
        for value in (self.display_name, self.help_text):
            if value:
                if not isinstance(value, str) or '\0' in value:
                    raise ValueError('Invalid settings help text')
                text.append(_(value))
        cfg['text'] = '\n\n'.join(text)
        cfg['button_style'] = (
            'checkbox' if self.settings_entry_type == 'multiselect' else 'checked_selection'
        )
        if not cfg['button_list']:
            cfg['button_list'] = [_('No options available')]
        return builder, cfg

    def display(self):
        from seedsigner_port.renderer import Renderer

        renderer = Renderer.get_instance()
        builder, cfg = self.configuration()
        renderer.session.show(builder, cfg)
        return result(renderer.session.wait(), len(cfg['button_list']))


# No pretending that OS/hardware utility screens exist. Original source menus can
# retain their choices while unported providers fail before invoking OS commands.
def __getattr__(name):
    from seedsigner_port.decode_platform import FeatureUnavailable

    if name.startswith('__'):
        raise AttributeError(name)
    raise FeatureUnavailable('Native settings screen unavailable: ' + name)
