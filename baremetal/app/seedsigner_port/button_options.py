# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner
class ButtonOption:
    """
    Note: The babel config in setup.cfg will extract the `button_label` string for translation
    """

    def __init__(
        self,
        button_label,
        icon_name=None,
        icon_color=None,
        right_icon_name=None,
        button_label_color=None,
        return_data=None,
        active_button_label=None,
        font_name=None,
        font_size=None,
    ):
        self.button_label = button_label
        self.icon_name = icon_name
        self.icon_color = icon_color
        self.right_icon_name = right_icon_name
        self.button_label_color = button_label_color
        self.return_data = return_data
        self.active_button_label = active_button_label
        self.font_name = font_name
        self.font_size = font_size

    def __eq__(self, other):
        return (
            type(self) is type(other)
            and self.button_label == other.button_label
            and (self.icon_name == other.icon_name)
            and (self.icon_color == other.icon_color)
            and (self.right_icon_name == other.right_icon_name)
            and (self.button_label_color == other.button_label_color)
            and (self.return_data == other.return_data)
            and (self.active_button_label == other.active_button_label)
            and (self.font_name == other.font_name)
            and (self.font_size == other.font_size)
        )


class ButtonOptionWithoutTranslation(ButtonOption):
    """
    Same as ButtonOption but does NOT translate button_label or active_button_label.
    The labels are also not extracted for translation by babel.
    """
