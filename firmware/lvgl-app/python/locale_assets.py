"""Private pinned locale assets; gettext and Settings remain upstream-owned."""
import hashlib
import json
import os
from pathlib import Path

MAX_FILE_BYTES=524288

class LocaleAssets:
    def __init__(self,root):
        self.root=Path(root).resolve()
        index_path=self.root/'runtime-index.json'
        if index_path.stat().st_size>MAX_FILE_BYTES:raise ValueError('Locale index too large')
        self.index=json.loads(index_path.read_text())
        if self.index.get('schema')!=1 or self.index.get('kind')!='shieldsigner-lvgl-locale-assets':raise ValueError('Unknown locale asset index')
        for relative,entry in self.index['files'].items():
            path=self.root/relative
            if Path(relative).is_absolute() or '..' in Path(relative).parts or path.is_symlink() or self.root not in path.resolve().parents:raise ValueError('Unsafe locale asset path')
            if not 0<entry['bytes']<=MAX_FILE_BYTES or not path.is_file() or path.stat().st_size!=entry['bytes']:raise ValueError('Invalid locale asset size')
            digest=hashlib.sha256()
            with path.open('rb') as stream:
                for chunk in iter(lambda:stream.read(65536),b''):digest.update(chunk)
            if digest.hexdigest()!=entry['sha256']:raise ValueError('Locale asset hash mismatch')
        for locale in self.index['manifests']:
            if locale+'/manifest.json' not in self.index['files']:raise ValueError('Unindexed locale manifest')
        self.host=None;self.locale=None

    def sync(self,host):
        locale=os.environ.get('LANGUAGE','en')
        if locale not in self.index['locales']:raise ValueError('Locale absent from pinned assets')
        if self.host is host and self.locale==locale:return
        options=dict(locale=locale)
        if self.host is not host:options.update(root=str(self.root),manifests=sorted(self.index['manifests']))
        host.send('locale',**options)
        event=host.next_event()
        if event!={'event':'locale_ready','locale':locale,'loaded':True}:raise RuntimeError('Native locale loading failed')
        self.host=host;self.locale=locale

    def picker(self,screen_class,kwargs,cfg):
        if screen_class.__name__!='SettingsEntryUpdateSelectionScreen':return None
        from seedsigner.models.settings_definition import SettingsDefinition,SettingsConstants
        entry=SettingsDefinition.get_settings_entry(SettingsConstants.SETTING__LOCALE)
        from gettext import gettext
        if kwargs.get('display_name') not in (entry.display_name,gettext(entry.display_name)):return None
        options=entry.selection_options
        labels=[getattr(item,'button_label',item) for item in kwargs.get('button_data',[])]
        if labels!=[name for code,name in options]:raise ValueError('Locale picker order differs from upstream')
        rows=[]
        for code,name in options:
            if code not in self.index['locales']:raise ValueError('Locale picker asset missing')
            row=dict(locale=code,english=code if code in self.index['manifests'] else name,native=name)
            if code in self.index['manifests']:row['image']='endonym_240.bin'
            rows.append(row)
        out=dict(top_nav=cfg['top_nav'],rows=rows,active_locale=os.environ.get('LANGUAGE','en'))
        if 'initial_selected_index' in cfg:out['initial_selected_index']=cfg['initial_selected_index']
        return 'settings_locale_picker_screen',out
