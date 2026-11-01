"""Transaction display contracts; original Views/parser still decide/sign."""
from gettext import gettext as _,ngettext
from formatting import btc_amount_from_sats,format_btc,format_sats
NAMES={'PSBTOverviewScreen','PSBTMathScreen','PSBTAddressDetailsScreen','PSBTChangeDetailsScreen','PSBTOpReturnScreen','PSBTFinalizeScreen'}

def configure(name,a,cfg):
    from seedsigner.models.settings import Settings,SettingsConstants as C
    settings=Settings.get_instance();network=settings.get_value(C.SETTING__NETWORK)
    for field in ('input_amount','spend_amount','fee_amount','change_amount','amount'):
        if field in a and (type(a[field]) is not int or a[field]<0):raise ValueError('Invalid transaction amount: '+field)
    cfg['is_bottom_list']=True
    if name=='PSBTOverviewScreen':
        cfg['top_nav']['title']=_('Review Transaction');cfg['button_list']=[_('Review details')]
        amount=a['spend_amount'] if a.get('destination_addresses') else a['change_amount']
        cfg['btc_amount']=btc_amount_from_sats(amount)
        for field in ('num_inputs','num_self_transfer_outputs','num_change_outputs','has_op_return','is_high_fee_tx'):
            cfg[field]=a.get(field,False if field.startswith(('has_','is_')) else 0)
        cfg['destination_addresses']=a.get('destination_addresses') or []
        cfg['labels']={'input_n':_('input {}'),'one_input':_('1 input'),'recipient_n':_('recipient {}'),'recipient_1':_('recipient 1'),'recipient_singular':_('recipient'),'ellipsis_series':'...','self_transfer':_('self-transfer'),'fee':_('fee')+(' (!)' if a.get('is_high_fee_tx') else ''),'op_return':'OP_RETURN','change':_('change')}
        return 'psbt_overview_screen',cfg
    if name=='PSBTMathScreen':
        cfg['top_nav']['title']=_('Transaction Math');cfg['button_list']=[_('Review recipients')]
        btc=a['input_amount']>1_000_000
        number=format_btc if btc else format_sats
        cfg['amounts']={'input':number(a['input_amount']),'spend':number(a['spend_amount']),'fee':str(a['fee_amount']) if btc else format_sats(a['fee_amount']),'change':number(a['change_amount'])}
        cfg['denomination']='btc' if btc else 'sats';cfg['num_recipients']=a['num_recipients'];cfg['is_high_fee_tx']=bool(a.get('is_high_fee_tx'))
        cfg['labels']={'inputs':ngettext('input','inputs',a['num_inputs']),'recipients':ngettext('recipient','recipients',a['num_recipients']),'fee':_('fee')+(' (!)' if a.get('is_high_fee_tx') else ''),'change':_('{} change').format(_('btc') if btc else _('sats'))}
        return 'psbt_math_screen',cfg
    if name in ('PSBTAddressDetailsScreen','PSBTChangeDetailsScreen'):
        cfg['btc_amount']=btc_amount_from_sats(a['amount']);cfg['address']=a['address'];cfg['network']=network
        if name=='PSBTAddressDetailsScreen':return 'psbt_address_details_screen',cfg
        kind=_('change address') if a.get('is_change_derivation_path',True) else _('receive address')
        cfg['address_type_label']=kind+' '+_('#')+str(a.get('derivation_path_addr_index',0))
        cfg['is_verified']=bool(a.get('is_change_addr_verified'));cfg['verified_text']=_('Address verified!')
        return 'psbt_change_details_screen',cfg
    if name=='PSBTOpReturnScreen':
        data=a['op_return_data']
        try:
            text=data.decode('utf-8',errors='strict')
            if '\0' in text:raise UnicodeError('NUL is not visible text')
            cfg['text']=text if text else _('Empty OP_RETURN')
        except UnicodeError:
            cfg['hex']=data.hex();cfg['hex_label']=_('raw hex data')
        return 'psbt_op_return_screen',cfg
    if name=='PSBTFinalizeScreen':
        cfg.pop('initial_selected_index',None)  # Read overflowing approval details before focusing Sign.
        cfg['top_nav']['title']=_('Sign Transaction')
        cfg['status_type']='custom';cfg['icon']='\ue921';cfg['icon_color']='#409CFF';cfg['warning_edges']=False
        lines=[_('Click to approve this transaction')]
        if a.get('is_rbf'):lines.append(_('Replaceable (RBF)'))
        if a.get('locktime_text'):lines.append(a['locktime_text'])
        cfg['text']='\n\n'.join(lines)
        return 'large_icon_status_screen',cfg
    raise NotImplementedError(name)
