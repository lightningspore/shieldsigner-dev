"""Original Python QR matrices, native transcription drawing; no PIL images."""
from gettext import gettext as _
NAMES={'SeedTranscribeEncryptedQRWholeQRScreen','SeedTranscribeEncryptedQRZoomedInScreen','SeedWordsBackupTestPromptScreen','SeedTranscribeSeedQRFormatScreen','SeedTranscribeSeedQRWholeQRScreen','SeedTranscribeSeedQRZoomedInScreen','SeedTranscribeSeedQRConfirmQRPromptScreen'}

def pack_matrix(rows,expected):
    n=len(rows)
    if type(expected) is not int or n!=expected or n not in (21,25,29,33):raise ValueError('Transcription matrix/template size mismatch')
    result=bytearray(1+(n*n+7)//8);result[0]=n
    for y,row in enumerate(rows):
        if len(row)!=n:raise ValueError('Non-square transcription matrix')
        for x,value in enumerate(row):
            if type(value) is not bool:raise ValueError('Non-boolean QR module')
            if value:
                bit=y*n+x;result[1+bit//8]|=1<<(bit%8)
    return result.hex()

def matrix(data,expected):
    import qrcode
    qr=qrcode.QRCode(version=1,error_correction=qrcode.constants.ERROR_CORRECT_L,box_size=5,border=0)
    qr.add_data(data);qr.make(fit=True)
    return pack_matrix(qr.modules,expected)

def configure(name,a,cfg):
    if name=='SeedWordsBackupTestPromptScreen':
        cfg['top_nav'].update(title=_('Verify Backup?'),show_back_button=False)
        cfg['text']=_('Optionally verify that your mnemonic backup is correct.');cfg['is_bottom_list']=True
        return 'button_list_screen',cfg
    if name=='SeedTranscribeSeedQRConfirmQRPromptScreen':
        cfg['is_bottom_list']=True;cfg['text']=_('Optionally scan your transcribed SeedQR to confirm that it reads back correctly.')
        return 'button_list_screen',cfg
    if name=='SeedTranscribeSeedQRFormatScreen':
        compact=a.get('is_compactqr',False);encrypted=a.get('is_encryptedqr',False)
        if compact and encrypted:return 'button_list_screen',cfg
        cfg.update(is_bottom_list=True,standard_label=_('Standard'),standard_text=_('BIP-39 wordlist indices'),compact_label=_('Encrypted') if encrypted else _('Compact'),compact_text=_('Encrypted entropy bits') if encrypted else _('Raw entropy bits'),show_compact=bool(compact or encrypted))
        return 'seed_transcribe_seedqr_format_screen',cfg
    data=a['qr_data'];n=a['num_modules']
    if not isinstance(data,(str,bytes)) or not data:raise ValueError('Missing transcription payload')
    cfg.update(qr_data=data.hex() if isinstance(data,bytes) else data,data_encoding='hex' if isinstance(data,bytes) else 'utf8',qr_mode='auto',num_modules=n,matrix_hex=matrix(data,n))
    if name in ('SeedTranscribeSeedQRWholeQRScreen','SeedTranscribeEncryptedQRWholeQRScreen'):
        cfg['top_nav']['title']=_('Transcribe Encrypted QR') if 'Encrypted' in name else _('Transcribe SeedQR');cfg['is_bottom_list']=True
        cfg['button_list']=[_('Begin {}x{}').format(n,n)]
        return 'seed_transcribe_whole_qr_screen',cfg
    if name in ('SeedTranscribeSeedQRZoomedInScreen','SeedTranscribeEncryptedQRZoomedInScreen'):
        cfg.update(border_modules=5 if 'Encrypted' in name else 4,initial_zone_x=a.get('initial_zone_x',0),initial_zone_y=a.get('initial_zone_y',0),exit_text=_('click to exit'),allow_screensaver=False)
        return 'seed_transcribe_zoomed_qr_screen',cfg
    raise NotImplementedError(name)
