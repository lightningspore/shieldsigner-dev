# SPDX-License-Identifier: MIT
"""Extract original defaults for specifically reviewed native app screens."""
import ast,json,hashlib,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=root.parent/'dist/firmware/sources/lvgl/application/src/seedsigner'
lock=json.loads((root.parent/'firmware/lvgl-app/sources.lock.json').read_text())['application']
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=source.parents[1],text=True).strip()==lock['commit']
constants={}
for c in ast.parse((source/'gui/components.py').read_text()).body:
 if isinstance(c,ast.ClassDef) and c.name in ('GUIConstants','SeedSignerIconConstants'):
  values={}
  for n in c.body:
   if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name):
    try:values[n.targets[0].id]=ast.literal_eval(n.value)
    except (ValueError,TypeError):pass
  constants[c.name]=type(c.name,(),values)
classes={};hashes={}
for name in ('screen.py','seed_screens.py'):
 p=source/'gui/screens'/name;hashes[name]=hashlib.sha256(p.read_bytes()).hexdigest()
 classes.update({n.name:n for n in ast.parse(p.read_text()).body if isinstance(n,ast.ClassDef)})
fields={'address','script_type','sig_type','network','is_mainnet','threadsafe_counter','verified_index','max_iterations','display_index_counter','verified_index_is_change','script_type_display','is_non_standard','derivation_path','xpub','button_label','title','show_back_button','show_power_button','selected_button','is_bottom_list','is_button_text_centered','checked_buttons','scroll_y_initial_offset','top_nav_icon_name','top_nav_icon_color','button_selected_color','button_data','fingerprint','text','status_icon_name','status_icon_size','status_color','status_headline','passphrase','initial_keyboard','fingerprint_without','fingerprint_with','wordlist','initial_letters','words','page_index','num_pages','is_compactqr','is_encryptedqr','qr_data','num_modules','initial_zone_x','initial_zone_y'}
namespace=dict(constants,_mft=lambda x:x,ButtonOption=lambda label:label,field=lambda **kw:kw['default_factory']())
def defaults(name):
 n=classes[name];out={}
 for b in n.bases:
  if isinstance(b,ast.Name) and b.id in classes:out.update(defaults(b.id))
 for a in n.body:
  if isinstance(a,ast.AnnAssign) and a.target.id in fields:
   out[a.target.id]=eval(compile(ast.Expression(a.value),'<pinned default>','eval'),namespace)
 return out
names=('SeedAddressVerificationScreen','SeedAddressVerificationSuccessScreen','SeedExportXpubDetailsScreen','LargeIconStatusScreen','WarningScreen','DireWarningScreen','ErrorScreen','SeedFinalizeScreen','SeedOptionsScreen','SeedSelectSeedScreen','SeedAddPassphraseScreen','SeedReviewPassphraseScreen','SeedMnemonicEntryScreen','SeedWordsScreen','SeedWordsBackupTestPromptScreen','SeedTranscribeSeedQRFormatScreen','SeedTranscribeSeedQRWholeQRScreen','SeedTranscribeSeedQRZoomedInScreen','SeedTranscribeSeedQRConfirmQRPromptScreen')
values={name:defaults(name) for name in names}
labels={a.targets[0].id:ast.literal_eval(a.value) for a in classes['SeedAddPassphraseScreen'].body if isinstance(a,ast.Assign) and isinstance(a.targets[0],ast.Name) and a.targets[0].id.startswith('KEYBOARD__')}
p=root/'app/seedsigner_port/app_screen_defaults.py'
def literal(fields):
 return '{'+','.join(repr(k)+':'+('['+','.join('ButtonOption('+repr(label)+')' for label in v)+']' if k=='button_data' and v else repr(v)) for k,v in fields.items())+'}'
p.write_text('# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner\n# Generated reviewed original defaults.\nfrom seedsigner_port.button_options import ButtonOption\nDEFAULTS={'+','.join(repr(name)+':'+literal(fields) for name,fields in values.items())+'}\nKEYBOARD_LABELS='+repr(labels)+'\n')

(root/'app/app-screens-provenance.json').write_text(json.dumps({'application':lock,'sources':dict(hashes,components=hashlib.sha256((source/'gui/components.py').read_bytes()).hexdigest()),'reviewedFields':sorted(fields),'outputSha256':hashlib.sha256(p.read_bytes()).hexdigest()},indent=2)+'\n')
