import sys
from pathlib import Path
from dataclasses import dataclass
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from contracts import configuration,result,UnmigratedScreen
@dataclass
class ButtonListScreen:
    title:str='Menu'
    button_data:object=None
    selected_button:int=0
    show_back_button:bool=True
    show_power_button:bool=False
@dataclass
class MainMenuScreen(ButtonListScreen):pass
@dataclass
class LargeButtonScreen(ButtonListScreen):pass
@dataclass
class SettingsEntryUpdateSelectionScreen(ButtonListScreen):
    settings_entry_type:str='multiselect'
@dataclass
class SeedWordsScreen(ButtonListScreen):
    page_index:int=0
    num_pages:int=3
@dataclass
class ButtonOption:
    button_label:str
    icon_name:str=None
class ContractTests(unittest.TestCase):
    def test_status_default_action_custom_icon_and_hidden_icon_contract(self):
        cls=type('LargeIconStatusScreen',(),{})
        _,cfg=configuration(cls,dict(title='Public status',status_icon_name='glyph',status_color='#123456',status_icon_size=0))
        self.assertEqual(cfg['button_list'],['OK'])
        self.assertEqual(cfg['status_type'],'custom')
        self.assertEqual(cfg['icon'],'glyph');self.assertEqual(cfg['icon_color'],'#123456')
        self.assertFalse(cfg['show_status_icon'])
        _,cfg=configuration(type('WarningScreen',(),{}),dict(button_data=['Cancel','Continue']))
        self.assertEqual(cfg['status_type'],'warning');self.assertEqual(cfg['button_list'],['Cancel','Continue'])
    def test_large_grid_selected_color_preserved(self):
        for cls in (LargeButtonScreen,MainMenuScreen):
            _,cfg=configuration(cls,dict(button_data=['One','Two'],button_selected_color='cyan'))
            self.assertEqual(cfg['button_selected_color'],'#00ffff')
        _,cfg=configuration(LargeButtonScreen,dict(button_data=['One','Two']))
        self.assertNotIn('button_selected_color',cfg)

    def test_menu_order_and_selected_index(self):
        name,cfg=configuration(MainMenuScreen,dict(button_data=['Scan','Seeds','Tools','Settings'],selected_button=2))
        self.assertEqual(name,'main_menu_screen');self.assertEqual(cfg['button_list'],['Scan','Seeds','Tools','Settings']);self.assertEqual(cfg['initial_selected_index'],2)
    def test_no_screen_constructor(self):
        def bad(*args):raise AssertionError('PIL constructor called')
        old=ButtonListScreen.__init__;ButtonListScreen.__init__=bad
        try:configuration(ButtonListScreen,dict(button_data=['One']))
        finally:ButtonListScreen.__init__=old
    def test_buttons_keep_icons_and_order(self):
        _,cfg=configuration(ButtonListScreen,dict(button_data=[ButtonOption('Alpha','icon'),'Beta']))
        self.assertEqual(cfg['button_list'],[{'label':'Alpha','icon':'icon'},'Beta'])
    def test_checked_settings_preserve_indices_and_help(self):
        _,cfg=configuration(SettingsEntryUpdateSelectionScreen,dict(button_data=['A','B'],display_name='Network',help_text='Choose',checked_buttons=[1]))
        self.assertEqual(cfg['button_style'],'checkbox');self.assertEqual(cfg['checked_buttons'],[1]);self.assertEqual(cfg['text'],'Network\n\nChoose')
    def test_seed_words_remain_exact(self):
        words=['abandon','ability','able','about'];_,cfg=configuration(SeedWordsScreen,dict(words=words,page_index=2,num_pages=6,button_data=['Next']))
        self.assertEqual(cfg['words'],words);self.assertEqual(cfg['top_nav']['title'],'Seed Words: 3/6');self.assertEqual(cfg['page_index'],2)
    def test_unreviewed_signing_screen_rejected(self):
        class UnreviewedSigningApprovalScreen:pass
        with self.assertRaises(UnmigratedScreen):configuration(UnreviewedSigningApprovalScreen,{})
    def test_selection_is_index_and_back_power_preserved(self):
        for value in [0,1,1000,1001]:self.assertEqual(result({'event':'button_selected','index':value},2),value)
    def test_invalid_index_rejected(self):
        for value in [-1,2,True,'0']:
            with self.assertRaises(ValueError):result({'event':'button_selected','index':value},2)
    def test_text_binary_content_untouched(self):
        self.assertEqual(result({'event':'text_entered','text':' space \u0000é '},0),' space \u0000é ')

class KeyboardContractTests(unittest.TestCase):
    def make(self,name):return type(name,(),{})
    def test_numeric_keyboard_does_not_change_initial_input(self):
        name,cfg=configuration(self.make('SeedBIP85SelectChildIndexScreen'),{'initial_value':'00042'})
        self.assertEqual(name,'keyboard_screen');self.assertEqual(cfg['keys'],list('0123456789'));self.assertEqual(cfg['initial_value'],'00042');self.assertTrue(cfg['show_save_button']);self.assertFalse(cfg['show_cursor_keys'])
    def test_custom_derivation_charset_and_prefill(self):
        _,cfg=configuration(self.make('SeedExportXpubCustomDerivationScreen'),{'initial_value':"m/84'/0'/0'"})
        self.assertEqual(cfg['keys'],list("/'0123456789"));self.assertEqual(cfg['initial_value'],"m/84'/0'/0'")
    def test_dice_values_and_autocomplete_stay_exact(self):
        _,cfg=configuration(self.make('ToolsDiceEntropyEntryScreen'),{'return_after_n_chars':50})
        self.assertEqual([cfg['keys_to_values'][key] for key in cfg['keys']],list('123456'));self.assertEqual(cfg['return_after_n_chars'],50);self.assertEqual(cfg['title_keystroke_template'],'Dice Roll {n}/{total}');self.assertEqual(cfg['keyboard_font'],'icon')
    def test_coinflip_values_and_autocomplete_stay_exact(self):
        _,cfg=configuration(self.make('ToolsCoinFlipEntryScreen'),{'return_after_n_chars':128})
        self.assertEqual(cfg['keys'],list('10'));self.assertEqual(cfg['return_after_n_chars'],128);self.assertEqual(cfg['guidance_text'],'Heads = 1\nTails = 0')
    def test_zero_scroll_keeps_focus_auto_scroll(self):
        _,cfg=configuration(ButtonListScreen,{'button_data':['One'],'scroll_y_initial_offset':0})
        self.assertNotIn('initial_scroll_y',cfg)
        _,cfg=configuration(ButtonListScreen,{'button_data':['One'],'scroll_y_initial_offset':456})
        self.assertEqual(cfg['initial_scroll_y'],456)

class MnemonicContractTests(unittest.TestCase):
    def test_wordlist_and_prefilled_letters_are_not_replaced_or_mutated(self):
        cls=type('SeedMnemonicEntryScreen',(),{})
        words=['abandon','ability','about'];letters=list('about')
        builder,cfg=configuration(cls,dict(title='Seed Word #12',wordlist=words,initial_letters=letters))
        self.assertEqual(builder,'seed_mnemonic_entry_screen')
        self.assertIs(cfg['wordlist'],words);self.assertIs(cfg['initial_letters'],letters)
        self.assertEqual(letters,list('about'));self.assertNotIn('button_list',cfg)
    def test_missing_wordlist_is_rejected(self):
        with self.assertRaises(ValueError):configuration(type('SeedMnemonicEntryScreen',(),{}),{})

class PassphraseContractTests(unittest.TestCase):
    def test_prefill_is_not_trimmed_or_normalized(self):
        value='  café e\u0301\n  '
        builder,cfg=configuration(type('SeedAddPassphraseScreen',(),{}),dict(passphrase=value,title='Test',initial_keyboard='ABC'))
        self.assertEqual(builder,'seed_add_passphrase_screen');self.assertEqual(cfg['initial_text'],value);self.assertEqual(cfg['initial_mode'],'upper')
    def test_save_and_back_responses_match_original_dictionary_contract(self):
        value='  exact\n é  '
        self.assertEqual(result(dict(event='passphrase_result',text=value,back=False),0),{'passphrase':value})
        self.assertEqual(result(dict(event='passphrase_result',text=value,back=True),0),dict(passphrase=value,is_back_button=True))
        self.assertEqual(result(dict(event='passphrase_result',text='',back=False),0),{'passphrase':''})
    def test_review_carries_both_fingerprints_and_full_text(self):
        _,cfg=configuration(type('SeedReviewPassphraseScreen',(),{}),dict(passphrase=' a ',fingerprint_without='00000000',fingerprint_with='12345678',button_data=['Done']))
        self.assertEqual(cfg['passphrase'],' a ');self.assertEqual(cfg['fingerprint_without'],'00000000');self.assertEqual(cfg['fingerprint_with'],'12345678');self.assertEqual(cfg['changes_fingerprint_label'],'changes fingerprint')
    def test_named_button_color_is_converted(self):
        option=ButtonOption('Discard');option.button_label_color='red'
        _,cfg=configuration(ButtonListScreen,dict(button_data=[option]))
        self.assertEqual(cfg['button_list'][0]['label_color'],'#ff0000')
    def test_nul_is_preserved_with_explicit_display_mode(self):
        _,cfg=configuration(type('SeedAddPassphraseScreen',(),{}),dict(passphrase='a\x00b'))
        self.assertEqual(cfg['initial_text'],'a\x00b')
        self.assertIn('NUL',cfg['top_nav']['title'])

if __name__=='__main__':unittest.main()

class XpubContractTests(unittest.TestCase):
    def test_exact_security_fields_and_custom_button(self):
        cls=type('SeedExportXpubDetailsScreen',(),{})
        values=dict(fingerprint='73c5da0a',derivation_path="m/84'/0'/7'",xpub='zpub-public-fixture',button_label='Export wallet')
        builder,cfg=configuration(cls,values)
        self.assertEqual(builder,'seed_export_xpub_details_screen')
        for key in ('fingerprint','derivation_path','xpub'):self.assertEqual(cfg[key],values[key])
        self.assertEqual(cfg['button_list'],['Export wallet'])
    def test_missing_security_field_rejected(self):
        cls=type('SeedExportXpubDetailsScreen',(),{})
        with self.assertRaises(ValueError):configuration(cls,dict(fingerprint='73c5da0a',derivation_path='m'))

class StatusReadingTests(unittest.TestCase):
    def test_default_warning_action_does_not_skip_overflowing_copy(self):
        cls=type('WarningScreen',(),{})
        text='Public warning '*40
        _,cfg=configuration(cls,dict(text=text,selected_button=0,button_data=['Understand']))
        self.assertEqual(cfg['text'],text)
        self.assertNotIn('initial_selected_index',cfg)
        _,cfg=configuration(cls,dict(text=text,selected_button=1,button_data=['Cancel','Continue']))
        self.assertEqual(cfg['initial_selected_index'],1)

    def test_large_grid_reuses_upstream_builder_preserving_icons_and_selection(self):
        for count in (2,4):
            options=[ButtonOption(str(i),'glyph'+str(i)) for i in range(count)]
            name,cfg=configuration(LargeButtonScreen,dict(title='Public menu',button_data=options,selected_button=count-1))
            self.assertEqual(name,'power_options_screen')
            self.assertEqual(cfg['initial_selected_index'],count-1)
            self.assertEqual(cfg['button_list'],[dict(label=str(i),icon='glyph'+str(i)) for i in range(count)])
            self.assertTrue(cfg['top_nav']['show_back_button'])
        for count in (0,1,3,5):
            with self.assertRaises(ValueError):configuration(LargeButtonScreen,dict(button_data=['x']*count))
