# SPDX-License-Identifier: MIT
"""Exact character identities for review with the current native ASCII fonts.

This is display-only. Model values and Unicode normalization remain upstream.
Escapes are never broken across lines; all printable backslashes are escaped.
"""
COLUMNS=24
LINES=4
SHORT_LIMIT=16
LEGEND=('Review every page. Spaces are \\u0020; NUL is \\u0000; '
        'a backslash is \\\\. Other characters use \\uXXXX or \\UXXXXXXXX. '
        'Numbers identify character positions. Display line breaks are not part of the passphrase.')

def short_visible(value):
    return len(value)<=SHORT_LIMIT and all(33<=ord(c)<=126 and c!='\\' for c in value)

def character(c):
    cp=ord(c)
    if 0xd800<=cp<=0xdfff:raise ValueError('Review requires Unicode scalar values')
    if c=='\\':return '\\\\'
    if 33<=cp<=126:return c
    if cp<=0xffff:return '\\u%04X'%cp
    return '\\U%08X'%cp

def pages(value,columns=COLUMNS,lines=LINES):
    if columns<10 or lines<1:raise ValueError('Review page geometry too small')
    result=[];rows=[];row='';first=0
    for index,c in enumerate(value):
        token=character(c)
        if len(row)+len(token)>columns:
            rows.append(row);row=''
            if len(rows)==lines:
                result.append((first,index,tuple(rows)))
                rows=[];first=index
        row+=token
    if row:rows.append(row)
    if rows:result.append((first,len(value),tuple(rows)))
    return result

def page_config(value,page,index,total):
    first,end,rows=page
    return {'top_nav':{'title':'Passphrase %d/%d'%(index+1,total),'show_back_button':True},
            'text':'Chars %d-%d/%d\n%s'%(first+1,end,len(value),'\n'.join(rows)),
            'text_monospace':True,'read_first':True,'is_bottom_list':True,
            'button_list':['Next'],'allow_screensaver':True}
