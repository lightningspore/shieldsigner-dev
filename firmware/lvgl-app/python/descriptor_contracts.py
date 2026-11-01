"""Descriptor presentation; parsing, policy and routing stay in original Views."""
from gettext import gettext as _
NAMES={'LoadMultisigWalletDescriptorScreen','MultisigWalletDescriptorScreen'}
def configure(name,a,cfg):
    cfg['is_bottom_list']=True;cfg.pop('initial_selected_index',None);cfg['read_first']=True
    if name=='LoadMultisigWalletDescriptorScreen':
        cfg['top_nav']['title']=_('Multisig Verification')
        cfg['text']=_('Load your multisig wallet descriptor to verify your receive/self-transfer or change address.')
        return 'button_list_screen',cfg
    if name=='MultisigWalletDescriptorScreen':
        policy=a['policy'];fingerprints=a['fingerprints']
        if not isinstance(policy,str) or not policy or '\0' in policy:raise ValueError('Missing descriptor policy')
        if not isinstance(fingerprints,(list,tuple)) or not fingerprints:raise ValueError('Missing signing keys')
        if any(not isinstance(value,str) or not value or '\0' in value for value in fingerprints):raise ValueError('Invalid signing key display')
        cfg['top_nav']['title']=_('Descriptor Loaded')
        cfg.update(policy=policy,fingerprints=list(fingerprints),policy_label=_('Policy'),signing_keys_label=_('Signing Keys'))
        return 'multisig_wallet_descriptor_screen',cfg
    raise NotImplementedError(name)
