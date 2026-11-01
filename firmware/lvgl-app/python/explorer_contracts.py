"""Native explorer presentation; original Views derive/cache all addresses."""
from gettext import gettext as _
NAMES={'ToolsAddressExplorerAddressTypeScreen','ToolsAddressExplorerAddressListScreen'}
def text(value):
    if not isinstance(value,str) or not value or '\0' in value:raise ValueError('Missing explorer display text')
    return value

def configure(name,a,cfg):
    if name=='ToolsAddressExplorerAddressTypeScreen':
        cfg['top_nav']['title']=_('Address Explorer');cfg['is_bottom_list']=True
        if a.get('fingerprint'):
            cfg.update(fingerprint=text(a['fingerprint']),fingerprint_label=_('Fingerprint'),derivation_label=_('Derivation'))
            from seedsigner.models.settings_definition import SettingsConstants as C,SettingsDefinition
            cfg['derivation_text']=text(a['custom_derivation_path']) if a['script_type']==C.CUSTOM_DERIVATION else SettingsDefinition.get_settings_entry(attr_name=C.SETTING__SCRIPT_TYPES).get_selection_option_display_name_by_value(value=a['script_type'])
        else:cfg.update(wallet_descriptor_text=text(a['wallet_descriptor_display_name']),wallet_descriptor_label=_('Wallet descriptor'))
        return 'tools_address_explorer_address_type_screen',cfg
    if name=='ToolsAddressExplorerAddressListScreen':
        addresses=a['addresses'];start=a.get('start_index',0)
        if not isinstance(addresses,(list,tuple)) or not addresses:raise ValueError('Missing address page')
        if type(start) is not int or start<0:raise ValueError('Invalid address start index')
        cfg.update(addresses=[text(value) for value in addresses],start_index=start,next_label=_('Next {}').format(len(addresses)))
        # Native builder composes its own labels. Retain the exact result count
        # for Runtime validation: one action per address plus paging.
        cfg['button_list']=[*addresses,cfg['next_label']]
        return 'tools_address_explorer_address_list_screen',cfg
    raise NotImplementedError(name)
