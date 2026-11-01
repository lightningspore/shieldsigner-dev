"""Explicit adapters from the pinned app's screen arguments to upstream LVGL.

Unsupported screens fail explicitly. Never substitute a generic confirmation
for a transaction, signing, seed, or smartcard screen with unreviewed semantics.
"""
from calibration import NAMES as CALIBRATION_SCREENS
from textqr_contracts import NAMES as TEXTQR_SCREENS
from dataclasses import MISSING, fields, is_dataclass
from gettext import gettext as _
from psbt_contracts import NAMES as PSBT_SCREENS
from transcription import NAMES as TRANSCRIPTION_SCREENS
from encrypted_contracts import NAMES as ENCRYPTED_SCREENS
from message_contracts import NAMES as MESSAGE_SCREENS
from descriptor_contracts import NAMES as DESCRIPTOR_SCREENS
from explorer_contracts import NAMES as EXPLORER_SCREENS
from final_word_contracts import NAMES as FINAL_WORD_SCREENS
from image_entropy import NAMES as IMAGE_ENTROPY_SCREENS

class UnmigratedScreen(NotImplementedError): pass

BASIC={'ButtonListScreen':'button_list_screen','MainMenuScreen':'main_menu_screen','LargeButtonScreen':'power_options_screen'}
STATUS={'LargeIconStatusScreen':'custom','WarningScreen':'warning','DireWarningScreen':'dire_warning','ErrorScreen':'error'}
KEYBOARDS={'KeyboardScreen','SettingPBFDK2IterationsScreen','SeedBIP85SelectChildIndexScreen','SeedExportXpubAccountNumberScreen','SeedExportXpubCustomDerivationScreen','ToolsDiceEntropyEntryScreen','ToolsCoinFlipEntryScreen'}
SUPPORTED={'IOTestScreen','DonateScreen'}|CALIBRATION_SCREENS|{'ToolsNetworkInfoScreen','HardeningTestScreen','BatteryInfoScreen','MemoryInfoScreen','VersionScreen','SystemInfoScreen'}|TEXTQR_SCREENS|{'ResetScreen','RebootToLoaderScreen','PowerOffNotRequiredScreen','SettingsQRReviewScreen','SettingsQRConfirmationScreen'}|IMAGE_ENTROPY_SCREENS|FINAL_WORD_SCREENS|EXPLORER_SCREENS|DESCRIPTOR_SCREENS|MESSAGE_SCREENS|ENCRYPTED_SCREENS|TRANSCRIPTION_SCREENS|{'OpeningSplashScreen','SeedExportXpubDetailsScreen','SeedAddressVerificationScreen','SeedAddressVerificationSuccessScreen'}|PSBT_SCREENS|{'ScanScreen','QRDisplayScreen'}|KEYBOARDS|set(BASIC)|set(STATUS)|{'PagedTextScreen','SettingsEntryUpdateSelectionScreen','SeedOptionsScreen','SeedSelectSeedScreen','AddressVerificationSigTypeScreen','SeedWordsScreen','SeedFinalizeScreen','SeedMnemonicEntryScreen','SeedAddPassphraseScreen','SeedReviewPassphraseScreen'}

def arguments(screen_class,passed):
    """Resolve dataclass defaults without constructing PIL widgets or hardware."""
    result={}
    if is_dataclass(screen_class):
        for field in fields(screen_class):
            if field.name in passed:continue
            if field.default is not MISSING:result[field.name]=field.default
            elif field.default_factory is not MISSING:result[field.name]=field.default_factory()
    result.update(passed)
    return result

def color(value):
    named={'red':'#ff0000','blue':'#0000ff','green':'#008000','black':'#000000','white':'#ffffff','gray':'#808080','grey':'#808080','yellow':'#ffff00','orange':'#ffa500','cyan':'#00ffff','magenta':'#ff00ff'}
    if isinstance(value,str):
        value=named.get(value.lower(),value)
        if len(value)==4 and value.startswith('#'):value='#'+''.join(c*2 for c in value[1:])
    return value

def button(option):
    if isinstance(option,str):return _(option)
    # Preserve ButtonOptionWithoutTranslation's explicit opt-out.
    label=getattr(option,'button_label',None)
    if not isinstance(label,str):raise TypeError('Expected a screen button label')
    if type(option).__name__!='ButtonOptionWithoutTranslation':label=_(label)
    out={'label':label}
    for source,target in [('icon_name','icon'),('right_icon_name','right_icon'),('icon_color','icon_color'),('button_label_color','label_color')]:
        value=getattr(option,source,None)
        if value is not None:out[target]=color(value) if target.endswith("color") else value
    return out

def configuration(screen_class,passed):
    name=screen_class.__name__
    if name not in SUPPORTED:raise UnmigratedScreen(name)
    a=arguments(screen_class,passed)
    title=a.get('title') or ''
    back=a.get('show_back_button',True); power=a.get('show_power_button',False)
    cfg={'top_nav':{'title':_(title),'show_back_button':back,'show_power_button':power},'allow_screensaver':True}
    for source,target in [('selected_button','initial_selected_index'),('is_bottom_list','is_bottom_list'),('is_button_text_centered','is_button_text_centered'),('checked_buttons','checked_buttons'),('scroll_y_initial_offset','initial_scroll_y')]:
        if a.get(source) is not None:
            # The original list treats zero as 'auto-scroll selected row'.
            if source=='scroll_y_initial_offset' and not a[source]:continue
            cfg[target]=a[source]
    for source,target in [('top_nav_icon_name','icon'),('top_nav_icon_color','icon_color')]:
        if a.get(source):cfg['top_nav'][target]=color(a[source]) if target.endswith('color') else a[source]
    cfg['button_list']=[button(x) for x in (a.get('button_data') or [])]
    builder=BASIC.get(name,'button_list_screen')
    if name in ('LargeButtonScreen','MainMenuScreen') and a.get('button_selected_color') is not None:
        cfg['button_selected_color']=color(a['button_selected_color'])
    if name=='LargeButtonScreen':
        if len(cfg['button_list']) not in (2,4):raise ValueError('LargeButtonScreen requires two or four buttons')
        return 'power_options_screen',cfg
    if name=='DonateScreen':
        cfg['top_nav']['title']=_('Donate')
        cfg.update(text=_('SeedSigner is 100%% free & open source, funded solely by the Bitcoin community.\n\nDonate onchain or LN at:').replace('%%','%'),url='seedsigner.com')
        cfg.pop('button_list',None)
        return 'donate_screen',cfg
    if name in CALIBRATION_SCREENS:
        from calibration import configure
        return configure(name,cfg)
    if name=='BatteryInfoScreen':
        from battery_info import configure
        return configure(cfg)
    if name=='MemoryInfoScreen':
        from live_info import configure
        return configure(screen_class,cfg)
    if name=='VersionScreen':
        cfg['top_nav']['title']=_('Version')
        cfg.update(version_name=a['version_name'],version_fork=a.get('version_fork') or '',short_commit_hash=a.get('short_commit_hash') or '',version_timestamp=a['version_timestamp'].strftime('%Y-%m-%d %H:%M:%S UTC'))
        cfg.pop('button_list',None)
        return 'version_screen',cfg
    if name=='SystemInfoScreen':
        cfg['top_nav']['title']=_('System Info')
        rows=[_('Platform: {platform_name}').format(platform_name=a.get('platform_name','')),_('Variant: {platform_variant}').format(platform_variant=a.get('platform_variant',''))]
        for key,label in (('firmware_version','Firmware'),('source_location','Source'),('os_build','OS'),('app_build','App')):
            if a.get(key):rows.append(_(label+': {'+key+'}').format(**{key:a[key]}))
        rows.extend([_('Serial (CPU): {system_serial}').format(system_serial=a.get('system_serial','')),_('Serial (MicroSD): {microsd_serial}').format(microsd_serial=a.get('microsd_serial',''))])
        cfg['text']='\n'.join(rows);cfg['button_list']=[]
        return 'button_list_screen',cfg
    if name in TEXTQR_SCREENS:
        from textqr_contracts import configure
        return configure(name,a,cfg)
    if name in {'ResetScreen','RebootToLoaderScreen','PowerOffNotRequiredScreen'}:
        title,text,builder,back={
            'ResetScreen':('Restarting','SeedSigner is restarting.\n\nAll in-memory data will be wiped.','reset_screen',False),
            'RebootToLoaderScreen':('Flash Mode','Rebooting into USB flash (Loader) mode.\n\nConnect USB and use the Rockchip flash tool.','reset_screen',False),
            'PowerOffNotRequiredScreen':('Just Unplug It','It is safe to disconnect power at any time.','power_off_not_required_screen',True),
        }[name]
        cfg['top_nav'].update(title=_(title),show_back_button=back,show_power_button=False)
        cfg['text']=_(text);cfg.pop('button_list',None)
        return builder,cfg
    if name in {'SettingsQRReviewScreen','SettingsQRConfirmationScreen'}:
        config_name=a.get('config_name')
        if config_name is not None and (not isinstance(config_name,str) or '\0' in config_name):raise ValueError('Invalid SettingsQR display name')
        review=name=='SettingsQRReviewScreen'
        status=a.get('status_message') or ('Apply these settings? Nothing changes until you tap Apply.' if review else 'Settings updated...')
        if not isinstance(status,str) or '\0' in status:raise ValueError('Invalid SettingsQR status')
        cfg['top_nav'].update(title=_(title or 'Settings QR'),show_back_button=False)
        cfg['is_bottom_list']=True
        cfg['button_list']=[_('Apply'),_('Cancel')] if review else [_('Home')]
        if review:
            cfg['text']=('"'+config_name+'"\n\n' if config_name else '')+_(status)
            return 'button_list_screen',cfg
        cfg.update(config_name=config_name or '',status_message=_(status))
        return 'settings_qr_confirmation_screen',cfg
    if name in FINAL_WORD_SCREENS:
        from final_word_contracts import configure
        return configure(name,a,cfg)
    if name in EXPLORER_SCREENS:
        from explorer_contracts import configure
        return configure(name,a,cfg)
    if name in DESCRIPTOR_SCREENS:
        from descriptor_contracts import configure
        return configure(name,a,cfg)
    if name in MESSAGE_SCREENS:
        from message_contracts import configure
        return configure(name,a,cfg)
    if name in ENCRYPTED_SCREENS:
        from encrypted_contracts import configure
        return configure(name,a,cfg)
    if name in TRANSCRIPTION_SCREENS:
        from transcription import configure
        return configure(name,a,cfg)
    if name in PSBT_SCREENS:
        from psbt_contracts import configure
        return configure(name,a,cfg)
    if name in KEYBOARDS:
        builder='keyboard_screen'
        charset=a.get('keys_charset')
        cols=a.get('cols') or 10
        save=bool(a.get('show_save_button',False))
        cursor=True
        if name in {'SettingPBFDK2IterationsScreen','SeedBIP85SelectChildIndexScreen','SeedExportXpubAccountNumberScreen'}:
            charset='0123456789';cols=5;save=True;cursor=False
            if name=='SettingPBFDK2IterationsScreen':cfg['top_nav']['title']='PBKDF2 Iter.(in units of 10k)'
            if name=='SeedExportXpubAccountNumberScreen':cfg['top_nav']['title']=_('Account Number')
        elif name=='SeedExportXpubCustomDerivationScreen':
            charset="/'0123456789";cols=6;save=True;cursor=False
            cfg['top_nav']['title']=_('Derivation Path')
        elif name=='ToolsDiceEntropyEntryScreen':
            charset=''.join(chr(n) for n in [0xf525,0xf528,0xf527,0xf524,0xf523,0xf526])
            cols=3;cursor=False
            cfg['keys_to_values']={char:str(i+1) for i,char in enumerate(charset)}
            cfg['keyboard_font']='icon'
            cfg['title_keystroke_template']=_('Dice Roll {}/{}').format('{n}','{total}')
            cfg['top_nav']['title']=_('Dice Roll {}/{}').format(1,a['return_after_n_chars'])
        elif name=='ToolsCoinFlipEntryScreen':
            charset='10';cols=4;cursor=False
            cfg['title_keystroke_template']=_('Coin Flip {}/{}').format('{n}','{total}')
            cfg['top_nav']['title']=_('Coin Flip {}/{}').format(1,a['return_after_n_chars'])
            cfg['guidance_text']=_('Heads = 1')+'\n'+_('Tails = 0')
        if not charset:raise ValueError('Keyboard requires an explicit character set')
        cfg.update(keys=list(charset),cols=cols,show_save_button=save,show_cursor_keys=cursor,initial_value=a.get('initial_value') or '')
        if a.get('return_after_n_chars'):cfg['return_after_n_chars']=a['return_after_n_chars']
        if a.get('keys_to_values'):cfg['keys_to_values']=a['keys_to_values']
        cfg.pop('button_list',None)
    elif name in STATUS:
        builder='large_icon_status_screen';cfg['status_type']=STATUS[name]
        if not cfg['button_list']:cfg['button_list']=[_('OK')]
        if a.get('status_icon_size')==0:cfg['show_status_icon']=False
        if cfg.get('initial_selected_index')==0:cfg.pop('initial_selected_index')  # Read overflowing status/warning text before the default action.
        for key in ('text','status_headline'):
            if a.get(key) is not None:cfg[key]=_(a[key])
        if a.get('status_color'):cfg['icon_color']=color(a['status_color'])
        if a.get('status_icon_name'):cfg['icon']=a['status_icon_name']
    elif name=='SettingsEntryUpdateSelectionScreen':
        cfg['top_nav']['title']=_('Settings');cfg['is_bottom_list']=True
        cfg['text']='\n\n'.join(_(a[k]) for k in ('display_name','help_text') if a.get(k))
        cfg['button_style']='checkbox' if a.get('settings_entry_type')=='multiselect' else 'checked_selection'
        if not cfg['button_list']:cfg['button_list']=[_('No options available')]
    elif name in ('PagedTextScreen','HardeningTestScreen','ToolsNetworkInfoScreen'):
        if name=='ToolsNetworkInfoScreen':
            cfg['top_nav']['title']=_('Network Info');cfg['text_monospace']=True
            a=dict(a,next_button_text=_('Next'))
        if name=='HardeningTestScreen':cfg['top_nav']['title']=_('Test Hardening')
        cfg['read_first']=True;cfg.pop('initial_selected_index',None)
        pages=a.get('paged_info');page=a.get('page_num',0)
        if not pages or not 0<=page<len(pages):raise ValueError('Invalid text page')
        if len(pages)>1:cfg['top_nav']['title']=_('{title} {page}/{total}').format(title=cfg['top_nav']['title'],page=page+1,total=len(pages))
        cfg['text']=pages[page];cfg['is_bottom_list']=True
        cfg['button_list']=[a.get('done_button_text') or _('Done') if page==len(pages)-1 else a.get('next_button_text') or _('More')]
    elif name=='SeedOptionsScreen':
        cfg['top_nav']['title']=a['fingerprint'];cfg['is_bottom_list']=True;cfg['is_button_text_centered']=False
    elif name in ('SeedSelectSeedScreen','AddressVerificationSigTypeScreen'):
        cfg['text']=a.get('text','');cfg['is_bottom_list']=True
    elif name=='SeedAddressVerificationSuccessScreen':
        builder='seed_address_verification_success_screen'
        cfg['top_nav'].update(title=_('Success!'),show_back_button=False)
        cfg['is_bottom_list']=True;cfg.pop('initial_selected_index',None)
        cfg['address']=a['address'];cfg['status_headline']=_('Address Verified')
        cfg['address_type_text']=_('change address') if a['verified_index_is_change'] else _('receive address')
        cfg['index_text']=_('index {}').format(a['verified_index']);cfg['button_list']=[_('OK')]
        cfg['derivation_text']=a.get('derivation_path') or ''
        if cfg['derivation_text'] and a.get('script_type_display'):cfg['derivation_text']+=' ('+a['script_type_display']+')'
        cfg['is_non_standard']=bool(a.get('is_non_standard'))
        cfg['non_standard_text']=_('Non-standard path!') if cfg['is_non_standard'] else ''
    elif name=='SeedAddressVerificationScreen':
        builder='seed_address_verification_screen'
        cfg['top_nav'].update(title=_('Verify Address'),show_back_button=False)
        cfg['is_bottom_list']=True;cfg['address']=a['address'];cfg['network']=a['network']
        cfg['type_network']=f"{a['sig_type']} - {a['script_type']}"+(f" ({a['network']})" if not a['is_mainnet'] else '')
        counter=a.get('display_index_counter') or a['threadsafe_counter']
        cfg['progress_text']=_('Checking address {}').format(counter.cur_count)
        if not cfg['button_list']:raise ValueError('Address search needs original action buttons')
    elif name=='SeedExportXpubDetailsScreen':
        builder='seed_export_xpub_details_screen'
        cfg['top_nav']['title']=_('Xpub Details');cfg['is_bottom_list']=True
        for key in ('fingerprint','derivation_path','xpub'):
            if not isinstance(a.get(key),str) or not a[key]:raise ValueError('Missing xpub review '+key)
            cfg[key]=a[key]
        cfg.update(fingerprint_label=_('Fingerprint'),derivation_label=_('Derivation'),xpub_label=_('Xpub'))
        cfg['button_list']=[_(a.get('button_label') or 'Export xpub')]
    elif name=='SeedAddPassphraseScreen':
        builder='seed_add_passphrase_screen'
        text=a.get('passphrase') or ''
        from visible_text import title
        cfg['top_nav']['title']=title(text,cfg['top_nav']['title'] or _('Passphrase'))
        cfg['initial_text']=text
        cfg['initial_mode']={'ABC':'upper','123':'digits','!@#':'symbols','*[]':'symbols'}.get(a.get('initial_keyboard'),'lower')
        cfg.pop('button_list',None)
    elif name=='SeedReviewPassphraseScreen':
        builder='seed_review_passphrase_screen'
        cfg['top_nav']['title']=_('Verify Passphrase')
        cfg['is_bottom_list']=True
        from visible_text import display,title
        cfg['top_nav']['title']=title(a['passphrase'],cfg['top_nav']['title'])
        cfg['passphrase']=display(a['passphrase'])
        cfg['fingerprint_without']=a['fingerprint_without'];cfg['fingerprint_with']=a['fingerprint_with']
        cfg['changes_fingerprint_label']=_('changes fingerprint')
    elif name=='SeedMnemonicEntryScreen':
        builder='seed_mnemonic_entry_screen'
        if not a.get('wordlist'):raise ValueError('Mnemonic entry requires the selected wordlist')
        cfg['wordlist']=a['wordlist'];cfg['initial_letters']=a.get('initial_letters') or []
        cfg.pop('button_list',None)
    elif name=='SeedWordsScreen':
        builder='seed_words_screen';cfg['words']=a['words'];cfg['page_index']=a.get('page_index',0)
        cfg['start_number']=cfg['page_index']*4+1
        cfg['top_nav']['title']=_('Seed Words: {}/{}').format(cfg['page_index']+1,a.get('num_pages',3))
    elif name=='SeedFinalizeScreen':
        builder='seed_finalize_screen';cfg['fingerprint']=a['fingerprint'];cfg['fingerprint_label']=_('fingerprint');cfg['top_nav']['title']=_('Finalize Seed');cfg['top_nav']['show_back_button']=False
    return builder,cfg

def result(event,button_count):
    if event.get('event')=='passphrase_result':
        if not isinstance(event.get('text'),str) or type(event.get('back')) is not bool:raise ValueError('Invalid passphrase response')
        answer={'passphrase':event['text']}
        if event['back']:answer['is_back_button']=True
        return answer
    if event.get('event')=='text_entered':return event['text']
    if event.get('event')=='button_selected':
        index=event['index']
        if type(index) is not int or not(index in (1000,1001) or 0<=index<button_count):
            raise ValueError('Invalid screen selection')
        return index
    raise ValueError('Not a terminal screen result')
