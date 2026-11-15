# SPDX-License-Identifier: MIT
"""Reviewed basic app-screen arguments/results for the native renderer.

Follows firmware/lvgl-app/python/contracts.py, using extracted original defaults
instead of runtime CPython dataclass introspection. No fallback screen or wallet
flow. Additional Screen subclasses require their own reviewed adapter.
"""
from seedsigner_port.screen_defaults import DEFAULTS
BASIC={'ButtonListScreen':'button_list_screen','LargeButtonScreen':'power_options_screen','MainMenuScreen':'main_menu_screen'}
class UnmigratedScreen(NotImplementedError):
    pass

def color(value):
    named={'red':'#ff0000','blue':'#0000ff','green':'#008000','black':'#000000','white':'#ffffff','gray':'#808080','grey':'#808080','yellow':'#ffff00','orange':'#ffa500','cyan':'#00ffff','magenta':'#ff00ff'}
    if isinstance(value,str):
        value=named.get(value.lower(),value)
        if len(value)==4 and value.startswith('#'):value='#'+''.join(c*2 for c in value[1:])
    return value

def configuration(screen_class,passed,translate=None):
    name=screen_class if isinstance(screen_class,str) else screen_class.__name__
    if name not in BASIC:raise UnmigratedScreen(name)
    a=DEFAULTS[name].copy();a.update(passed)
    if a.get('long_press_key') is not None:raise UnmigratedScreen('Long-hold action requires its reviewed adapter')
    if a.get('Button_cls') is not None:raise UnmigratedScreen('Button class styling requires its reviewed adapter')
    tr=translate if translate is not None else lambda text:text
    def text(value):
        if not isinstance(value,str) or '\0' in value:raise ValueError('Screen text must be a string without NUL')
        return value
    def button(option):
        if isinstance(option,str):return text(tr(option))
        label=getattr(option,'button_label',None)
        if not isinstance(label,str):raise TypeError('Expected a screen button label')
        if type(option).__name__!='ButtonOptionWithoutTranslation':label=tr(label)
        out={'label':text(label)}
        for source,target in [('icon_name','icon'),('right_icon_name','right_icon'),('icon_color','icon_color'),('button_label_color','label_color')]:
            value=getattr(option,source,None)
            if value is not None:out[target]=color(value) if target.endswith('color') else value
        return out
    cfg={'top_nav':{'title':text(tr(a.get('title') or '')),'show_back_button':a.get('show_back_button',True),'show_power_button':a.get('show_power_button',False)},'allow_screensaver':True}
    for source,target in [('selected_button','initial_selected_index'),('is_bottom_list','is_bottom_list'),('is_button_text_centered','is_button_text_centered'),('checked_buttons','checked_buttons'),('scroll_y_initial_offset','initial_scroll_y')]:
        if a.get(source) is not None:
            if source=='scroll_y_initial_offset' and not a[source]:continue
            cfg[target]=a[source]
    for source,target in [('top_nav_icon_name','icon'),('top_nav_icon_color','icon_color')]:
        if a.get(source):cfg['top_nav'][target]=color(a[source]) if target.endswith('color') else a[source]
    cfg['button_list']=[button(x) for x in (a.get('button_data') or [])]
    if name in ('LargeButtonScreen','MainMenuScreen') and a.get('button_selected_color') is not None:cfg['button_selected_color']=color(a['button_selected_color'])
    count=len(cfg['button_list'])
    if name=='LargeButtonScreen' and count not in (2,4):raise ValueError('LargeButtonScreen requires two or four buttons')
    if name=='MainMenuScreen' and count!=4:raise ValueError('MainMenuScreen requires four buttons')
    return BASIC[name],cfg

def result(event,button_count,screen_name=None):
    if screen_name=='SeedAddPassphraseScreen':
        if not isinstance(event,tuple) or len(event)!=3 or event[0] not in (2,6) or type(event[2]) is not str:
            raise ValueError("Invalid passphrase result")
        if type(event[1]) is not int or event[1]!=(1 if event[0]==6 else 0):raise ValueError("Invalid passphrase back flag")
        answer={'passphrase':event[2]}
        if event[0]==6:answer['is_back_button']=True
        return answer
    if screen_name=='SeedMnemonicEntryScreen' and isinstance(event,tuple) and len(event)==3 and event[0]==2:
        if type(event[1]) is not int or event[1]!=0 or type(event[2]) is not str or not event[2] or '\0' in event[2]:raise ValueError('Invalid mnemonic word result')
        return event[2]
    if event==1000:return 1000  # Existing ButtonInput override.
    if not isinstance(event,tuple) or len(event)!=3 or event[0]!=1:raise ValueError('Not a reviewed basic screen result')
    index=event[1]
    if type(index) is not int or not(index in (1000,1001) or 0<=index<button_count):raise ValueError('Invalid screen selection')
    return index

# Additional reviewed original screen contracts, using the same actual builders.
_basic_configuration=configuration
STATUS={'LargeIconStatusScreen':'custom','WarningScreen':'warning','DireWarningScreen':'dire_warning','ErrorScreen':'error'}
TRANSCRIPTION={'SeedTranscribeSeedQRFormatScreen','SeedTranscribeSeedQRWholeQRScreen','SeedTranscribeSeedQRZoomedInScreen','SeedTranscribeSeedQRConfirmQRPromptScreen'}
APP_SCREENS=TRANSCRIPTION|set(STATUS)|{'SeedFinalizeScreen','SeedOptionsScreen','SeedSelectSeedScreen','SeedAddPassphraseScreen','SeedReviewPassphraseScreen','SeedMnemonicEntryScreen','SeedWordsScreen','SeedWordsBackupTestPromptScreen'}
def configuration(screen_class,passed,translate=None):
    name=screen_class if isinstance(screen_class,str) else screen_class.__name__
    if name not in APP_SCREENS:return _basic_configuration(screen_class,passed,translate)
    from seedsigner_port.app_screen_defaults import DEFAULTS as APP_DEFAULTS
    from seedsigner_port.gui_constants import GUIConstants,SeedSignerIconConstants
    a=APP_DEFAULTS[name].copy();a.update(passed)
    tr=translate if translate is not None else lambda text:text
    builder,cfg=_basic_configuration('ButtonListScreen',a,translate)
    if name in TRANSCRIPTION:
        if name=='SeedTranscribeSeedQRZoomedInScreen':
            cfg['top_nav']['title']=tr(a.get('title') or '')
            for source,target in [('selected_button','initial_selected_index'),('is_bottom_list','is_bottom_list'),('is_button_text_centered','is_button_text_centered')]:
                if source not in a:cfg.pop(target,None)
        from seedsigner_port.transcription import configure
        return configure(name,a,cfg)
    if name in STATUS:
        builder='large_icon_status_screen';cfg['status_type']=STATUS[name]
        if not cfg['button_list']:cfg['button_list']=[tr('OK')]
        if a.get('status_icon_size')==0:cfg['show_status_icon']=False
        if cfg.get('initial_selected_index')==0:cfg.pop('initial_selected_index')
        for key in ('text','status_headline'):
            if a.get(key) is not None:cfg[key]=tr(a[key])
        if a.get('status_color'):cfg['icon_color']=color(a['status_color'])
        if a.get('status_icon_name'):cfg['icon']=a['status_icon_name']
    elif name=='SeedFinalizeScreen':
        builder='seed_finalize_screen'
        cfg['top_nav'].update(title=tr('Finalize Seed'),show_back_button=False)
        cfg['fingerprint']=a['fingerprint'];cfg['fingerprint_label']=tr('fingerprint')
    elif name=='SeedOptionsScreen':
        cfg['top_nav'].update(title=a['fingerprint'],icon=SeedSignerIconConstants.FINGERPRINT,icon_color=GUIConstants.INFO_COLOR)
        cfg['is_bottom_list']=True;cfg['is_button_text_centered']=False
    elif name=='SeedSelectSeedScreen':
        cfg['text']=a.get('text','');cfg['is_bottom_list']=True
    elif name=='SeedWordsScreen':
        builder='seed_words_screen'
        words=a.get('words');page=a.get('page_index',0);total=a.get('num_pages',3)
        if not isinstance(words,(list,tuple)) or not 1<=len(words)<=4 or any(type(word) is not str or not word or '\0' in word for word in words):raise ValueError('Seed page requires one to four words')
        if type(page) is not int or type(total) is not int or not 0<=page<total:raise ValueError('Invalid seed page index')
        cfg['words']=words;cfg['page_index']=page;cfg['start_number']=page*4+1
        cfg['top_nav']['title']=tr('Seed Words: {}/{}').format(page+1,total)
    elif name=='SeedWordsBackupTestPromptScreen':
        cfg['top_nav'].update(title=tr('Verify Backup?'),show_back_button=False)
        cfg['is_bottom_list']=True
        cfg['text']=tr('Optionally verify that your mnemonic backup is correct.')
    elif name=='SeedMnemonicEntryScreen':
        builder='seed_mnemonic_entry_screen'
        words=a.get('wordlist')
        if not isinstance(words,(list,tuple)) or not words or any(type(word) is not str or not word or '\0' in word for word in words):raise ValueError('Mnemonic entry requires the selected wordlist')
        cfg['wordlist']=words;cfg['initial_letters']=a.get('initial_letters') or []
        cfg.pop('button_list',None)
        for source,target in [('selected_button','initial_selected_index'),('is_bottom_list','is_bottom_list'),('is_button_text_centered','is_button_text_centered')]:
            if source not in a:cfg.pop(target,None)
    elif name=='SeedAddPassphraseScreen':
        from seedsigner_port.visible_text import title
        builder='seed_add_passphrase_screen'
        text=a.get('passphrase') or ''
        cfg['top_nav']['title']=title(text,cfg['top_nav']['title'] or tr('Passphrase'))
        cfg['initial_text']=text
        cfg['initial_mode']={'ABC':'upper','123':'digits','!@#':'symbols','*[]':'symbols'}.get(a.get('initial_keyboard'),'lower')
        cfg.pop('button_list',None)
        for source,target in [('selected_button','initial_selected_index'),('is_bottom_list','is_bottom_list'),('is_button_text_centered','is_button_text_centered')]:
            if source not in a:cfg.pop(target,None)
    elif name=='SeedReviewPassphraseScreen':
        from seedsigner_port.visible_text import display,title
        builder='seed_review_passphrase_screen'
        cfg['top_nav']['title']=title(a['passphrase'],tr('Verify Passphrase'))
        cfg['is_bottom_list']=True
        cfg['passphrase']=display(a['passphrase'])
        cfg['fingerprint_without']=a['fingerprint_without'];cfg['fingerprint_with']=a['fingerprint_with']
        cfg['changes_fingerprint_label']=tr('changes fingerprint')
    return builder,cfg
