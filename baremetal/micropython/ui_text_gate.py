# SPDX-License-Identifier: MIT
# Real passphrase keyboard widget with PUBLIC test strings, no wallet/model use.
import ui
import json
ui.init()
home={'top_nav':{'title':'Home'},'button_list':['Scan','Seeds','Tools','Settings']}
def render(text):
    ui.render('seed_add_passphrase_screen',json.dumps({'top_nav':{'title':'Text test'},'initial_text':text}))
for text in ('x'*255,'é'*127,'a\0'+'x'*253):
    render(text)
    ui.key(51,True)
    ui.key(51,False)
    event=ui.event()
    assert event is not None and event[0]==2 and event[2]==text
    assert ui.event() is None
print('@@UI_TEXT_EXACT_ASCII_UTF8')
for text in ('x'*256,'é'*128,'a\0'+'x'*254):
    render(text)
    try:
        ui.key(51,True)
        assert False
    except RuntimeError as error:
        assert '255-byte limit' in str(error)
    ui.render('main_menu_screen',json.dumps(home))
    assert ui.event() is None
print('@@PASS native-text-no-silent-truncation')
