# SPDX-License-Identifier: MIT
"""Native address-explorer presentation; original Views derive/cache addresses.

Mirrors firmware/lvgl-app/python/explorer_contracts.py with the baremetal
settings schema and explicit translation callback.
"""

NAMES = {'ToolsAddressExplorerAddressTypeScreen', 'ToolsAddressExplorerAddressListScreen'}


def text(value):
    if not isinstance(value, str) or not value or '\0' in value:
        raise ValueError('Missing explorer display text')
    return value


def configure(name, a, cfg, _):
    if name == 'ToolsAddressExplorerAddressTypeScreen':
        cfg['top_nav']['title'] = _('Address Explorer')
        cfg['is_bottom_list'] = True
        if a.get('fingerprint'):
            cfg.update(
                fingerprint=text(a['fingerprint']),
                fingerprint_label=_('Fingerprint'),
                derivation_label=_('Derivation'),
            )
            from seedsigner_port.settings_schema import SettingsConstants as C, SettingsDefinition

            cfg['derivation_text'] = (
                text(a['custom_derivation_path'])
                if a['script_type'] == C.CUSTOM_DERIVATION
                else SettingsDefinition.get_settings_entry(
                    attr_name=C.SETTING__SCRIPT_TYPES
                ).get_selection_option_display_name_by_value(value=a['script_type'])
            )
        else:
            cfg.update(
                wallet_descriptor_text=text(a['wallet_descriptor_display_name']),
                wallet_descriptor_label=_('Wallet descriptor'),
            )
        return 'tools_address_explorer_address_type_screen', cfg
    if name == 'ToolsAddressExplorerAddressListScreen':
        addresses = a['addresses']
        start = a.get('start_index', 0)
        if not isinstance(addresses, (list, tuple)) or not addresses:
            raise ValueError('Missing address page')
        if type(start) is not int or start < 0:
            raise ValueError('Invalid address start index')
        cfg.update(
            addresses=[text(value) for value in addresses],
            start_index=start,
            next_label=_('Next {}').format(len(addresses)),
        )
        cfg['button_list'] = list(addresses) + [cfg['next_label']]
        return 'tools_address_explorer_address_list_screen', cfg
    raise NotImplementedError(name)
