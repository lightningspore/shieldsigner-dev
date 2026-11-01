import ast,builtins,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from dependency_policy import transform,native_extractor
SOURCE=Path(__file__).resolve().parents[3]/'dist/firmware/sources/lvgl/application/src/seedsigner'

class DependencyPolicyTests(unittest.TestCase):
    def test_font_imports_are_local_and_keyboard_unused_import_is_removed(self):
        for relative in ('gui/components.py','gui/keyboard.py'):
            tree=transform((SOURCE/relative).read_text(),'pil')
            self.assertFalse(any(isinstance(n,ast.ImportFrom) and n.module=='PIL' and any(a.name=='ImageFont' for a in n.names) for n in tree.body))
            compile(tree,'<public deferred fonts>','exec')
            if relative.endswith('components.py'):
                cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Fonts')
                method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='get_font')
                self.assertIsInstance(method.body[0],ast.ImportFrom)
                self.assertEqual(method.body[0].names[0].name,'ImageFont')
                self.assertEqual(method.returns.value,'ImageFont.FreeTypeFont')

    def test_optional_seed_imports_move_without_changing_model_logic(self):
        source=(SOURCE/'models/seed.py').read_text()
        original=ast.parse(source);adapted=transform(source,'seed')
        self.assertFalse(any(isinstance(n,ast.Import) and any(a.name=='shamir_mnemonic' for a in n.names) for n in adapted.body))
        for node in ast.walk(adapted):
            if isinstance(node,ast.FunctionDef):
                node.body=[n for n in node.body if not (isinstance(n,ast.Import) and any(a.name=='shamir_mnemonic' for a in n.names) or isinstance(n,ast.ImportFrom) and (n.module=='seedsigner.models' and any(a.name=='aezeed' for a in n.names) or n.module=='embit' and all(a.name in ('bip32','bip85') for a in n.names)))]
        classes=lambda tree:[ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.ClassDef)]
        self.assertEqual(classes(original),classes(adapted))

    def test_original_decoder_classes_and_payload_parser_are_unchanged(self):
        source=(SOURCE/'models/decode_qr.py').read_text()
        original=ast.parse(source);adapted=transform(source,'decode')
        for node in ast.walk(adapted):
            if isinstance(node,ast.FunctionDef):
                while node.body and isinstance(node.body[0],(ast.Import,ast.ImportFrom)) and node.body[0].lineno<node.lineno:node.body.pop(0)
        classes=lambda tree:[ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.ClassDef)]
        self.assertEqual(classes(original),classes(adapted))
        self.assertFalse(any(isinstance(n,ast.Try) for n in adapted.body))
        with self.assertRaises(ValueError):transform(source.replace('import cv2','import different_backend'),'decode')

    def test_encoder_construction_does_not_import_legacy_renderers(self):
        source=(SOURCE/'helpers/qr.py').read_text();attempts=[]
        def import_module(name,*args,**kwargs):
            if name=='qrcode' or name.startswith('qrcode.') or name=='PIL':
                attempts.append(name);raise ImportError('fixture renderer unavailable')
            return builtins.__import__(name,*args,**kwargs)
        namespace={'__builtins__':dict(vars(builtins),__import__=import_module)}
        exec(compile(transform(source,'qr'),'<lazy legacy QR>','exec'),namespace)
        qr=namespace['QR']();self.assertEqual(attempts,[])
        with self.assertRaises(ImportError):qr.qrsize('public')
        self.assertEqual(attempts,['qrcode'])
        original=ast.parse(source);changed=transform(source,'qr')
        old=next(n for n in original.body if isinstance(n,ast.ClassDef));new=next(n for n in changed.body if isinstance(n,ast.ClassDef))
        for before,after in zip(old.body,new.body):
            if isinstance(before,ast.FunctionDef) and before.name in ('qrsize','qrimage','qrimage_io'):
                if before.name=='qrsize':continue
                inserted=len(after.body)-len(before.body)
                self.assertTrue(all(isinstance(n,(ast.Import,ast.ImportFrom)) for n in after.body[:inserted]))
                body=after.body[inserted:]
                self.assertEqual([ast.dump(n) for n in before.body],[ast.dump(n) for n in body])

    def test_matrix_only_dimensions_match_original_rendered_dimensions(self):
        source=(SOURCE/'helpers/qr.py').read_text();old={};new={}
        exec(compile(source,'<original QR dimensions>','exec'),old)
        exec(compile(transform(source,'qr'),'<matrix QR dimensions>','exec'),new)
        for payload in ('','1234567890'*20,'public café e\u0301',b'\0\xffbinary',bytes(range(256)),b'public '*120):
            with self.subTest(length=len(payload)):
                self.assertEqual(old['QR']().qrsize(payload),new['QR']().qrsize(payload))

    def test_native_compatibility_extraction_preserves_binary_and_closes_worker(self):
        events=[];payload=bytes(range(256));image=object()
        class Reader:
            def __init__(self,binary):events.append('construct')
            def decode(self,value):
                self_assert=value is image
                if not self_assert:raise ValueError('fixture')
                return payload
            def close(self):events.append('close')
        with tempfile.TemporaryDirectory() as temporary:
            binary=Path(temporary)/'reader';binary.write_bytes(b'fixture');binary.chmod(0o700)
            class DecodeQR:pass
            module=SimpleNamespace(DecodeQR=DecodeQR)
            close=native_extractor(module,binary,Reader)
            self.assertTrue(DecodeQR.is_qr_scanner_available())
            self.assertIsNone(DecodeQR.extract_qr_data(None))
            self.assertEqual(DecodeQR.extract_qr_data(image,is_binary=True),payload)
            with self.assertRaises(ValueError):DecodeQR.extract_qr_data(object())
            self.assertEqual(events,['construct','close','close'])
            close();self.assertEqual(events[-1],'close')
            binary.unlink();self.assertFalse(DecodeQR.is_qr_scanner_available())

class PillowDeferralTests(unittest.TestCase):
    def test_image_functions_still_work_and_nearest_default_is_identical(self):
        from PIL import Image
        source="""from PIL import Image
from dataclasses import dataclass
@dataclass
class Picture:
    image: Image.Image = None
def make():
    return Image.new('RGB',(2,2),(255,0,0))
def resize(image,sampling=Image.Resampling.NEAREST):
    return image.resize((1,1),sampling)
"""
        attempted=[];original=builtins.__import__
        def guarded(name,*args,**kwargs):
            if name.startswith('PIL'):attempted.append(name)
            return original(name,*args,**kwargs)
        namespace={'__name__':__name__,'__builtins__':dict(vars(builtins),__import__=guarded)}
        exec(compile(transform(source,'pil'),'<public image import fixture>','exec'),namespace)
        self.assertEqual(attempted,[])
        self.assertIsNone(namespace['Picture']().image)
        self.assertEqual(namespace['resize'].__defaults__,(Image.Resampling.NEAREST,))
        image=namespace['make']();resized=namespace['resize'](image)
        try:self.assertEqual(resized.getpixel((0,0)),(255,0,0));self.assertEqual(attempted,['PIL'])
        finally:image.close();resized.close()
    def test_only_the_unused_controller_text_probe_is_removed(self):
        source=(SOURCE/'controller.py').read_text();tree=transform(source,'controller')
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Controller')
        method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='configure_instance')
        self.assertNotIn("features.check('raqm')",ast.unparse(method))
        self.assertIn('Settings.get_instance()',ast.unparse(method))
        self.assertIn('Renderer.configure_instance()',ast.unparse(method))

class TypeOnlyImportTests(unittest.TestCase):
    def test_encrypted_storage_works_without_importing_cipher_code(self):
        source=(SOURCE/'models/encryptedqr.py').read_text();namespace={}
        exec(compile(transform(source,'storage'),'<public encrypted storage>','exec'),namespace)
        self.assertNotIn('EncryptedQRCode',namespace)
        value=object();item=namespace['EncryptedQR'](value,'public')
        self.assertIs(item.encrypted_qr,value);self.assertEqual(item.public_data,'public')
    def test_type_only_import_removal_rejects_runtime_use(self):
        from dependency_policy import remove_type_imports
        with self.assertRaises(ValueError):remove_type_imports(ast.parse('from public import Thing\nx=Thing()'),{'public':{'Thing'}})
    def test_settings_no_longer_imports_unused_scan_screen(self):
        source=(SOURCE/'gui/screens/settings_screens.py').read_text();tree=transform(source,'settings')
        self.assertFalse(any(isinstance(n,ast.ImportFrom) and n.module=='seedsigner.gui.screens.scan_screens' for n in tree.body))

class WalletViewImportTests(unittest.TestCase):
    def test_wallet_logic_is_unchanged_except_imports_and_type_hints(self):
        source=(SOURCE/'views/seed_views.py').read_text()
        original=ast.parse(source);adapted=transform(source,'seed_views')
        for node in ast.walk(adapted):
            if isinstance(node,ast.FunctionDef):
                while node.body and isinstance(node.body[0],(ast.Import,ast.ImportFrom)) and node.body[0].lineno<node.lineno:node.body.pop(0)
        def normalize(before,after):
            if isinstance(before,list):
                self.assertEqual(len(before),len(after))
                for left,right in zip(before,after):normalize(left,right)
            elif isinstance(before,ast.AST):
                for key,value in ast.iter_fields(before):
                    changed=getattr(after,key)
                    if key in ('annotation','returns') and isinstance(value,ast.AST) and not isinstance(value,ast.Constant) and isinstance(changed,ast.Constant) and isinstance(changed.value,str):
                        setattr(after,key,ast.parse(changed.value,mode='eval').body)
                    else:normalize(value,changed)
        old=[n for n in original.body if isinstance(n,ast.ClassDef)];new=[n for n in adapted.body if isinstance(n,ast.ClassDef)]
        normalize(old,new)
        self.assertEqual([ast.dump(n,include_attributes=False) for n in old],[ast.dump(n,include_attributes=False) for n in new])


class ToolsImportTests(unittest.TestCase):
    def test_tools_logic_and_wildcard_exports_are_preserved(self):
        for name in ('tools_views','microsd_views','smartcard_views','gpg_views','password_generator_views','satochip_bias','keycard_bias','encode_qr'):
            with self.subTest(module=name):
                source=(SOURCE/('models' if name=='encode_qr' else 'views')/f'{name}.py').read_text()
                old=ast.parse(source);new=transform(source,'encoder' if name=='encode_qr' else 'tools')
                compile(new,'<reviewed Tools imports>','exec')
                for node in ast.walk(new):
                    if isinstance(node,ast.FunctionDef):
                        while node.body and isinstance(node.body[0],(ast.Import,ast.ImportFrom,ast.Try)) and node.body[0].lineno<node.lineno:node.body.pop(0)
                def normalize(before,after):
                    if isinstance(before,list):
                        self.assertEqual(len(before),len(after))
                        for left,right in zip(before,after):normalize(left,right)
                    elif isinstance(before,ast.AST):
                        for key,value in ast.iter_fields(before):
                            changed=getattr(after,key)
                            if key in ('annotation','returns') and isinstance(value,ast.AST) and not isinstance(value,ast.Constant) and isinstance(changed,ast.Constant) and isinstance(changed.value,str):
                                setattr(after,key,ast.parse(changed.value,mode='eval').body)
                            else:normalize(value,changed)
                definitions=lambda tree:[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef))]
                before=definitions(old);after=definitions(new);normalize(before,after)
                self.assertEqual([ast.dump(n) for n in before],[ast.dump(n) for n in after])
                stars=lambda tree:[ast.dump(n) for n in tree.body if isinstance(n,ast.ImportFrom) and any(a.name=='*' for a in n.names)]
                self.assertEqual(stars(old),stars(new))

    def test_grouped_import_retains_only_definition_time_alias(self):
        source="""from seedsigner.helpers import satodime_coins, seedkeeper_utils
class Public:
    label=satodime_coins.label
    def use(self):return seedkeeper_utils.run()
"""
        tree=transform(source,'tools')
        self.assertEqual([a.name for a in tree.body[0].names],['satodime_coins'])
        method=tree.body[1].body[1]
        self.assertEqual(method.body[0].names[0].name,'seedkeeper_utils')

    def test_optional_import_handler_is_preserved_and_shadowed_alias_stays_global(self):
        source="""from seedsigner.helpers import embit_utils
try:
    from pysatochip.JCconstants import JCconstants
except ImportError:
    JCconstants=None
def use():return JCconstants
def shadow(embit_utils):return embit_utils
"""
        tree=transform(source,'tools')
        self.assertIsInstance(tree.body[0],ast.ImportFrom)
        method=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='use')
        self.assertEqual(ast.dump(method.body[0]),ast.dump(ast.parse(source).body[1]))


class LegacyAmountImportTests(unittest.TestCase):
    def test_decimal_moves_into_original_amount_renderer_without_logic_changes(self):
        source=(SOURCE/'gui/components.py').read_text()
        old=ast.parse(source);new=transform(source,'pil')
        self.assertFalse(any(isinstance(n,ast.ImportFrom) and n.module=='decimal' for n in new.body))
        def method(tree):
            cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='BtcAmount')
            return next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__post_init__')
        changed=method(new)
        self.assertTrue(any(isinstance(n,ast.ImportFrom) and n.module=='decimal' for n in changed.body))
        while isinstance(changed.body[0],ast.ImportFrom) and changed.body[0].lineno<changed.lineno:changed.body.pop(0)
        for node in ast.walk(changed):
            annotation=getattr(node,'annotation',None)
            if isinstance(annotation,ast.Constant) and annotation.value=='Image.Image':node.annotation=ast.parse('Image.Image',mode='eval').body
        self.assertEqual(ast.dump(method(old)),ast.dump(changed))

    def test_original_decimal_arithmetic_still_resolves_on_demand(self):
        from dependency_policy import defer_pillow
        source="""from decimal import Decimal
def calculate():
    return Decimal('1.23456789').quantize(Decimal('0.01'))
"""
        attempts=[];original=builtins.__import__
        def tracked(name,*args,**kwargs):
            if name=='decimal':attempts.append(name)
            return original(name,*args,**kwargs)
        namespace={'__builtins__':dict(vars(builtins),__import__=tracked)}
        tree=ast.fix_missing_locations(defer_pillow(ast.parse(source),extra_modules=('decimal',)))
        exec(compile(tree,'<deferred legacy amount>','exec'),namespace)
        self.assertEqual(attempts,[])
        self.assertEqual(str(namespace['calculate']()),'1.23')
        self.assertEqual(attempts,['decimal'])


class StartupHelperImportTests(unittest.TestCase):
    def test_unused_splash_version_import_is_removed_without_changing_definitions(self):
        source=(SOURCE/'views/screensaver.py').read_text();old=ast.parse(source);new=transform(source,'pil')
        self.assertFalse(any(isinstance(n,ast.ImportFrom) and n.module=='seedsigner.helpers.version' for n in new.body))
        for node in ast.walk(new):
            if isinstance(node,ast.FunctionDef):
                while node.body and isinstance(node.body[0],ast.ImportFrom) and node.body[0].lineno<node.lineno:node.body.pop(0)
            for key in ('annotation','returns'):
                value=getattr(node,key,None)
                if isinstance(value,ast.Constant) and value.value=='Image.Image':setattr(node,key,ast.parse('Image.Image',mode='eval').body)
        definitions=lambda tree:[ast.dump(n) for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef))]
        self.assertEqual(definitions(old),definitions(new))

    def test_decoder_helpers_are_deferred_into_existing_consumers(self):
        source=(SOURCE/'models/decode_qr.py').read_text();tree=transform(source,'decode')
        optional=('datetime','seedsigner.models.aezeed')
        self.assertFalse(any(isinstance(n,ast.ImportFrom) and n.module in optional for n in tree.body))
        for module in optional:
            self.assertTrue(any(isinstance(n,ast.ImportFrom) and n.module==module for cls in tree.body if isinstance(cls,ast.ClassDef) for n in ast.walk(cls)))
