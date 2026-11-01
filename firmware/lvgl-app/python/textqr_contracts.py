"""Text QR presentation; original Views retain escape parsing and encoding."""
from gettext import gettext as _
NAMES={'ToolsTextQRTextEntryScreen','ToolsTextQRReviewTextScreen','ToolsTextQRTranscribeModePromptScreen','ToolsTranscribeTextQRWholeQRScreen','ToolsTranscribeTextQRZoomedInScreen','ToolsTranscribeTextQRConfirmQRPromptScreen'}
def configure(name,a,cfg):
    if name in ('ToolsTextQRTextEntryScreen','ToolsTextQRReviewTextScreen'):
        value=a.get('textToEncode') or ''
        if not isinstance(value,str) or '\0' in value:raise ValueError('Unsupported TextQR display input')
        if name=='ToolsTextQRTextEntryScreen':
            cfg.update(initial_text=value,initial_mode={'ABC':'upper','123':'digits','!@#':'symbols','*[]':'symbols'}.get(a.get('initial_keyboard'),'lower'))
            cfg['top_nav']['title']=cfg['top_nav']['title'] or _('Text to Encode')
            cfg.pop('button_list',None)
            return 'seed_add_passphrase_screen',cfg
        cfg.update(text=value,review_spaces=bool(a.get('visible_space',True)),read_first=True,is_bottom_list=True)
        cfg.pop('initial_selected_index',None)
        return 'button_list_screen',cfg
    cfg['is_bottom_list']=True
    if name=='ToolsTextQRTranscribeModePromptScreen':
        cfg['text']=_('The QR codes output in both modes may differ, but both are valid QR codes.')
        return 'button_list_screen',cfg
    if name=='ToolsTranscribeTextQRConfirmQRPromptScreen':
        cfg['text']=_('Optionally scan your transcribed text QR code to confirm that it reads back correctly.')
        return 'button_list_screen',cfg
    from transcription import matrix
    data=a['qr_data'];n=a['num_modules']
    if not isinstance(data,str) or not data:raise ValueError('Missing TextQR payload')
    cfg.update(matrix_hex=matrix(data,n),num_modules=n,qr_data=data,data_encoding='utf8',qr_mode='auto')
    if name=='ToolsTranscribeTextQRWholeQRScreen':
        cfg['top_nav']['title']=_('Transcribe Text QR');cfg['button_list']=[_('Begin {}x{}').format(n,n)]
        return 'seed_transcribe_whole_qr_screen',cfg
    if name=='ToolsTranscribeTextQRZoomedInScreen':
        cfg.update(border_modules=5,initial_zone_x=a.get('initial_block_x',0),initial_zone_y=a.get('initial_block_y',0),exit_text=_('click to exit'),allow_screensaver=False)
        return 'seed_transcribe_zoomed_qr_screen',cfg
    raise NotImplementedError(name)
def typed_result(value):
    if not isinstance(value,dict) or not isinstance(value.get('passphrase'),str):raise ValueError('Invalid TextQR entry response')
    result={'textToEncode':value['passphrase']}
    if value.get('is_back_button'):result['is_back_button']=True
    return result
