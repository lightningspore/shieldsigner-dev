"""Message-signing presentation only; original Views derive and sign unchanged."""
from gettext import gettext as _
NAMES={'SeedSignMessageConfirmMessageScreen','SeedSignMessageConfirmAddressScreen'}

def prepare(screen,controller=None):
    if controller is None:
        from seedsigner.controller import Controller
        controller=Controller.get_instance()
    data=controller.sign_message_data
    message=data['message']
    if not isinstance(message,str):raise TypeError('Message must be original text')
    if '\0' in message:raise ValueError('Embedded NUL message review is not yet supported')
    # The pinned native screen scrolls a complete message. Retain the original
    # View's page-loop contract, without creating PIL pages or changing signing data.
    if 'paged_message' not in data:data['paged_message']=[message]
    pages=data['paged_message'];page=screen.page_num
    if type(page) is not int or not 0<=page<len(pages):raise ValueError('Invalid message review page')
    if not all(isinstance(p,str) and '\0' not in p for p in pages):raise ValueError('Invalid message review text')
    screen.message=pages[page]
    screen.message_page_count=len(pages)

def configure(name,a,cfg):
    cfg.update(is_bottom_list=True,is_button_text_centered=True)
    cfg.pop('initial_selected_index',None)
    if name=='SeedSignMessageConfirmMessageScreen':
        text=a['message']
        if not isinstance(text,str) or '\0' in text:raise ValueError('Unsupported message review text')
        page=a['page_num'];count=a['message_page_count']
        cfg['top_nav']['title']=_('Review Message') if count==1 else f'Message (pt {page+1}/{count})'
        cfg['message']=text;cfg['button_list']=[_('Next')]
        return 'seed_sign_message_confirm_message_screen',cfg
    if name=='SeedSignMessageConfirmAddressScreen':
        for field in ('address','derivation_path'):
            value=a[field]
            if not isinstance(value,str) or not value or '\0' in value:raise ValueError('Missing signing address/path')
            cfg[field]=value
        cfg['top_nav']['title']=_('Confirm Address');cfg['derivation_path_label']=_('derivation path')
        cfg['button_list']=[_('Sign message')]
        return 'seed_sign_message_confirm_address_screen',cfg
    raise NotImplementedError(name)
