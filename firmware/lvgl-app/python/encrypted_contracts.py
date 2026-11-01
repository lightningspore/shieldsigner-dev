"""Encrypted-backup UI contracts; cryptography remains in original Views/models."""
from gettext import gettext as _
from visible_text import display,title
TEXT_FIELDS={'ScanTypeEncryptionKeyScreen':'encryptionkey','SeedEncryptedQRMnemonicIDScreen':'mnemonic_id'}
REVIEW_FIELDS={'ScanReviewEncryptionKeyScreen':'encryptionkey','SeedEncryptedQRReviewMnemonicIDScreen':'mnemonic_id'}
NAMES=set(TEXT_FIELDS)|set(REVIEW_FIELDS)|{'ScanEncryptedQRScreen','ScanAmbiguousQRScreen','SeedEncryptedQRTranscribeModePromptScreen'}

def configure(name,a,cfg):
    if name in TEXT_FIELDS:
        value=a.get(TEXT_FIELDS[name]) or ''
        if not isinstance(value,str):raise TypeError('Text entry requires a string')
        cfg['top_nav']['title']=cfg['top_nav'].get('title') or (_('Encryption Key') if name=='ScanTypeEncryptionKeyScreen' else _('Mnemonic ID'))
        cfg['top_nav']['title']=title(value,cfg['top_nav']['title'])
        cfg['initial_text']=value
        cfg['initial_mode']={'ABC':'upper','123':'digits','!@#':'symbols','*[]':'symbols'}.get(a.get('initial_keyboard'),'lower')
        cfg.pop('button_list',None)
        return 'seed_add_passphrase_screen',cfg
    if name in REVIEW_FIELDS:
        value=a[REVIEW_FIELDS[name]]
        if not isinstance(value,str):raise TypeError('Review requires original text')
        cfg['top_nav']['title']=_('Review Encryption Key') if name=='ScanReviewEncryptionKeyScreen' else _('Review Mnemonic ID')
        cfg['top_nav']['title']=title(value,cfg['top_nav']['title'])
        cfg['is_bottom_list']=True;cfg['text']=display(value) or _('(empty)')
        cfg['review_spaces']=(' ' in value) if name=='ScanReviewEncryptionKeyScreen' else (value!=value.strip() or '  ' in value)
        cfg['read_first']=True;cfg.pop('initial_selected_index',None)
        return 'button_list_screen',cfg
    cfg['is_bottom_list']=True
    if name=='ScanEncryptedQRScreen':
        cfg['top_nav'].update(title=_('Decrypt?'),show_back_button=False);cfg['text']=a.get('public_data') or ''
    elif name=='ScanAmbiguousQRScreen':
        cfg['top_nav'].update(title=_('Select QR Type'),show_back_button=False);cfg['text']=a.get('message') or ''
    elif name=='SeedEncryptedQRTranscribeModePromptScreen':cfg['text']=_('The QR codes output in both modes may differ, but both are valid QR codes.')
    else:raise NotImplementedError(name)
    return 'button_list_screen',cfg

def typed_result(name,value):
    if not isinstance(value,dict) or 'passphrase' not in value:raise ValueError('Invalid encrypted text-entry response')
    result={TEXT_FIELDS[name]:value['passphrase']}
    if value.get('is_back_button'):result['is_back_button']=True
    return result
