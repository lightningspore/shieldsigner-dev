"""Guarded LVGL-only import policy; installed source and payload parsing unchanged.

QR image rendering imports become method-local. Pixel extraction uses the
existing Rust ZXing client, so the legacy zbar/OpenCV/NumPy probes are omitted.
Install before importing either reviewed module; use a fresh process to change
policies. Uninstall removes the finder and closes its optional compatibility
client; it does not hot-reload already imported application modules.
"""
import ast,copy,hashlib,json,os,sys
from pathlib import Path
from importlib.machinery import PathFinder

def defer_pillow(tree,extra_modules=()):
    imports=[];names=set();kept=[]
    for node in tree.body:
        if isinstance(node,ast.ImportFrom) and node.module and (node.module=='PIL' or node.module.startswith('PIL.') or node.module in extra_modules):
            imports.append(node);names.update(alias.asname or alias.name for alias in node.names)
        else:kept.append(node)
    if not imports:raise ValueError('Expected reviewed Pillow imports')
    tree.body=kept
    for node in ast.walk(tree):
        for key in ('annotation','returns'):
            value=getattr(node,key,None)
            if value is not None and any(isinstance(item,ast.Name) and item.id in names for item in ast.walk(value)):
                setattr(node,key,ast.copy_location(ast.Constant(ast.unparse(value)),value))
    for method in [node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef)]:
        for defaults in (method.args.defaults,method.args.kw_defaults):
            for index,value in enumerate(defaults):
                if value is not None and any(isinstance(item,ast.Name) and item.id in names for item in ast.walk(value)):
                    if ast.unparse(value)!='Image.Resampling.NEAREST':raise ValueError('Unreviewed eager Pillow default')
                    # Pillow Resampling.NEAREST is integer zero, including legacy
                    # versions; retain its exact resampling behavior on demand.
                    defaults[index]=ast.copy_location(ast.Constant(0),value)
        used={node.id for statement in method.body for node in ast.walk(statement) if isinstance(node,ast.Name) and isinstance(node.ctx,ast.Load)}
        needed=[]
        for node in imports:
            aliases=[alias for alias in node.names if (alias.asname or alias.name) in used]
            if aliases:
                moved=copy.deepcopy(node);moved.names=aliases;needed.append(moved)
        method.body[0:0]=needed
    return tree

def bind_original_pillow(tree,namespace):
    """Retain local image imports when an adapter recompiles an original method."""
    file=namespace.get('__file__')
    if not file:return tree
    with Path(file).open() as source:
        lines=''.join(line for line in source if line.startswith('from PIL'))
    lines+=namespace.get('__shieldsigner_deferred_imports__','')
    if not lines:return tree
    imports=ast.parse(lines).body
    tree.body[0:0]=imports
    if any(isinstance(n,ast.ImportFrom) and n.module and n.module.startswith('PIL') for n in tree.body):tree=defer_pillow(tree)
    return defer_feature_blocks(tree,record=False)

def remove_type_imports(tree,expected):
    names=set();kept=[]
    for node in tree.body:
        if isinstance(node,ast.ImportFrom) and node.module in expected:
            actual={alias.name for alias in node.names}
            if actual!=expected[node.module]:raise ValueError('Changed type-only import')
            names.update(alias.asname or alias.name for alias in node.names)
        else:kept.append(node)
    if len(names)!=sum(len(values) for values in expected.values()):raise ValueError('Missing type-only import')
    tree.body=kept
    for node in ast.walk(tree):
        for key in ('annotation','returns'):
            value=getattr(node,key,None)
            if value is not None and any(isinstance(item,ast.Name) and item.id in names for item in ast.walk(value)):
                setattr(node,key,ast.copy_location(ast.Constant(ast.unparse(value)),value))
    if any(isinstance(node,ast.Name) and node.id in names and isinstance(node.ctx,ast.Load) for node in ast.walk(tree)):
        raise ValueError('Purported type-only import has runtime uses')
    return tree

TOOLS_OPTIONAL_MODULES=('seedsigner.helpers','seedsigner.helpers.satochip_signer','seedsigner.helpers.iso7816','pysatochip.CardConnector','pysatochip.JCconstants','pysatochip.util','seedsigner.models.encode_qr')

def defer_feature_blocks(tree,record=True):
    blocks=[];kept=[]
    def aliases(block):
        nodes=block.body if isinstance(block,ast.Try) else [block]
        return {alias.asname or alias.name for node in nodes for alias in node.names}
    def selected(node):return isinstance(node,ast.ImportFrom) and node.module in TOOLS_OPTIONAL_MODULES
    for node in tree.body:
        if selected(node):
            for alias in node.names:
                block=copy.deepcopy(node);block.names=[alias];blocks.append(block)
        elif isinstance(node,ast.Try) and node.body and all(selected(item) for item in node.body) and not node.orelse and not node.finalbody:blocks.append(node)
        else:kept.append(node)
    if not blocks:return tree
    names=set().union(*(aliases(block) for block in blocks))
    for node in ast.walk(tree):
        for key in ('annotation','returns'):
            value=getattr(node,key,None)
            if value is not None and any(isinstance(item,ast.Name) and item.id in names for item in ast.walk(value)):
                setattr(node,key,ast.copy_location(ast.Constant(ast.unparse(value)),value))
    unsafe=set()
    class Globals(ast.NodeVisitor):
        def visit_FunctionDef(self,node):
            for value in [*node.decorator_list,*node.args.defaults,*[v for v in node.args.kw_defaults if v is not None]]:self.visit(value)
        def visit_Name(self,node):
            if node.id in names and isinstance(node.ctx,ast.Load):unsafe.add(node.id)
    for node in kept:Globals().visit(node)
    methods=[node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef)]
    for method in methods:
        unsafe.update(names & {arg.arg for arg in [*method.args.posonlyargs,*method.args.args,*method.args.kwonlyargs,*([method.args.vararg] if method.args.vararg else []),*([method.args.kwarg] if method.args.kwarg else [])]})
        unsafe.update(names & {node.id for node in ast.walk(method) if isinstance(node,ast.Name) and isinstance(node.ctx,ast.Store)})
    deferred=[block for block in blocks if not aliases(block)&unsafe]
    # Rebuild normal grouped imports with just the aliases required at module
    # definition time; preserve optional try/except blocks as atomic units.
    rebuilt=[]
    for node in tree.body:
        if selected(node):
            aliases_to_keep=[a for a in node.names if (a.asname or a.name) in unsafe]
            if aliases_to_keep:
                node.names=aliases_to_keep;rebuilt.append(node)
        elif node not in deferred:rebuilt.append(node)
    tree.body=rebuilt
    for method in methods:
        used={node.id for statement in method.body for node in ast.walk(statement) if isinstance(node,ast.Name) and isinstance(node.ctx,ast.Load)}
        method.body[0:0]=[copy.deepcopy(block) for block in deferred if aliases(block)&used]
    if record:
        value=ast.Assign(targets=[ast.Name(id='__shieldsigner_deferred_imports__',ctx=ast.Store())],value=ast.Constant('\n'.join(ast.unparse(block) for block in deferred)))
        tree.body.append(value)
    return tree

def transform(source,kind):
    tree=ast.parse(source)
    if kind=='encoder':
        tree=defer_pillow(tree,extra_modules=('embit','embit.networks','embit.psbt','seedsigner.helpers.ur2.ur_encoder','seedsigner.helpers.ur2.ur','seedsigner.helpers.ur2.cbor_lite','urtypes.bytes','urtypes.crypto','seedsigner.helpers.qr','seedsigner.models.seed'))
    elif kind=='tools':
        if any(isinstance(n,ast.ImportFrom) and n.module and n.module.startswith('PIL') for n in tree.body):tree=defer_pillow(tree)
        tree=defer_feature_blocks(tree)
    elif kind=='storage':
        tree=remove_type_imports(tree,{'seedsigner.models.encryption':{'EncryptedQRCode'}})
    elif kind in ('pil','controller','screen','settings'):
        tree=defer_pillow(tree,extra_modules=('decimal',))
        if kind=='pil' and any(isinstance(n,ast.ImportFrom) and n.module=='seedsigner.helpers.version' for n in tree.body):
            tree=remove_type_imports(tree,{'seedsigner.helpers.version':{'Version'}})
        if kind=='settings':tree=remove_type_imports(tree,{'seedsigner.gui.screens.scan_screens':{'ScanScreen'}})
        if kind=='screen':tree=remove_type_imports(tree,{'seedsigner.models.encode_qr':{'BaseQrEncoder'}})
        if kind=='controller':
            tree=remove_type_imports(tree,{'datetime':{'datetime'},'embit.descriptor':{'Descriptor'},'embit.psbt':{'PSBT'},'seedsigner.models.psbt_parser':{'PSBTParser'}})
            cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Controller')
            method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='configure_instance')
            removed=0
            for index,node in enumerate(method.body):
                if isinstance(node,ast.ImportFrom) and node.module=='PIL' and [n.name for n in node.names]==['features']:
                    check=method.body[index+1]
                    if not isinstance(check,ast.If) or ast.unparse(check.test)!="not features.check('raqm')" or len(check.body)!=1 or not ast.unparse(check.body[0]).startswith('logger.warning('):raise ValueError('Changed legacy text-engine diagnostic')
                    del method.body[index:index+2];removed+=1;break
            if removed!=1:raise ValueError('Missing reviewed text-engine diagnostic')
    elif kind=='qr':
        imports=[];kept=[]
        for node in tree.body:
            if isinstance(node,ast.Import) and any(n.name=='qrcode' for n in node.names):imports.append(node)
            elif isinstance(node,ast.ImportFrom) and (node.module=='PIL' or node.module.startswith('qrcode.')):imports.append(node)
            else:kept.append(node)
        if len(imports)!=4:raise ValueError('Changed legacy QR rendering imports')
        cls=next(n for n in kept if isinstance(n,ast.ClassDef) and n.name=='QR')
        methods=[n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name in ('qrsize','qrimage','qrimage_io')]
        if len(methods)!=3:raise ValueError('Changed QR image API')
        for method in methods:
            if method.name=='qrsize':
                if len(method.body)!=8 or ast.unparse(method.body[-4])!='qr_image = qr.make_image(image_factory=StyledPilImage)':raise ValueError('Changed QR dimension calculation')
                # Same QR fitting/version policy; dimensions need no bitmap.
                method.body=method.body[:-4]+ast.parse('qr.make(fit=True)\nreturn qr.modules_count').body
            used={n.id for n in ast.walk(method) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Load)}
            needed=[]
            for node in imports:
                names=[name for name in node.names if (name.asname or name.name.split('.')[0]) in used]
                if names:
                    relocated=copy.deepcopy(node);relocated.names=names;needed.append(relocated)
            method.body[0:0]=needed
        tree.body=kept
    elif kind in ('seed','seed_views'):
        imports={};kept=[]
        for node in tree.body:
            if isinstance(node,ast.Import) and len(node.names)==1 and node.names[0].name=='shamir_mnemonic':imports['shamir_mnemonic']=node
            elif kind=='seed' and isinstance(node,ast.ImportFrom) and node.module=='embit':
                optional=[alias for alias in node.names if alias.name in ('bip32','bip85')]
                for alias in optional:
                    moved=copy.deepcopy(node);moved.names=[alias];imports[alias.name]=moved
                node.names=[alias for alias in node.names if alias.name not in ('bip32','bip85')]
                if node.names:kept.append(node)
            elif isinstance(node,ast.ImportFrom) and node.module=='seedsigner.models' and len(node.names)==1 and node.names[0].name=='aezeed':imports['aezeed']=node
            else:kept.append(node)
        if set(imports)!=({'shamir_mnemonic','aezeed','bip32','bip85'} if kind=='seed' else {'shamir_mnemonic'}):raise ValueError('Changed optional seed imports')
        moved={name:0 for name in imports}
        for cls in kept:
            if not isinstance(cls,ast.ClassDef):continue
            for method in cls.body:
                if not isinstance(method,ast.FunctionDef):continue
                used={node.id for node in ast.walk(method) if isinstance(node,ast.Name) and isinstance(node.ctx,ast.Load)}
                for name,node in imports.items():
                    if name in used:method.body.insert(0,copy.deepcopy(node));moved[name]+=1
        if not all(moved.values()):raise ValueError('Optional seed import has no reviewed consumer')
        tree.body=kept
        if kind=='seed_views':
            tree=remove_type_imports(tree,{'embit.descriptor':{'Descriptor'}})
            tree=defer_pillow(tree,extra_modules=('seedsigner.helpers.bitbox02_backup','seedsigner.helpers.passport_backup','seedsigner.helpers.tapsigner_backup','seedsigner.models.encode_qr','pysatochip.JCconstants','pysatochip.util','seedsigner.helpers'))
    elif kind=='decode':
        replaced=0
        for index,node in enumerate(tree.body):
            if not isinstance(node,ast.Try):continue
            imports=[n for n in node.body if isinstance(n,(ast.Import,ast.ImportFrom))]
            names={alias.asname or alias.name for n in imports for alias in n.names}
            if names not in ({'pyzbar','ZBarSymbol'},{'cv2','np'}):continue
            if len(imports)!=len(node.body):raise ValueError('Changed QR backend import block')
            tree.body[index]=ast.Assign(targets=[ast.Name(id=name,ctx=ast.Store()) for name in sorted(names)],value=ast.Constant(None))
            replaced+=1
        if replaced!=2:raise ValueError('Changed QR backend probes')
        tree=defer_pillow(tree,extra_modules=('urtypes.crypto','urtypes.bytes','seedsigner.helpers.ur2.ur_decoder','seedsigner.models.psbt_framing','seedsigner.models.psbt_parser','embit','datetime','seedsigner.models.aezeed'))
    else:raise ValueError('Unknown dependency policy')
    return ast.fix_missing_locations(tree)

def native_extractor(module,binary,reader_factory=None):
    client=[None]
    def available():return binary.is_absolute() and binary.is_file() and os.access(binary,os.X_OK)
    def extract(image,is_binary=False):
        if image is None:return None
        if client[0] is None:
            if reader_factory is None:
                from shieldsigner_qr_decoder import RustTransportQrReader
                factory=RustTransportQrReader
            else:factory=reader_factory
            client[0]=factory(str(binary))
        try:return client[0].decode(image)
        finally:client[0].close()
    def close():
        if client[0] is not None:client[0].close()
    module.DecodeQR.is_qr_scanner_available=staticmethod(available)
    module.DecodeQR.extract_qr_data=staticmethod(extract)
    module.__shieldsigner_lvgl_dependencies__={'pixelDecoder':'rust-zxing','legacyBackendImports':False}
    return close

def specifications():
    specs={'seedsigner.gui.components':('gui/components.py','pil'),'seedsigner.gui.keyboard':('gui/keyboard.py','pil'),'seedsigner.views.seed_views':('views/seed_views.py','seed_views'),'seedsigner.models.seed':('models/seed.py','seed'),'seedsigner.helpers.qr':('helpers/qr.py','qr'),'seedsigner.models.decode_qr':('models/decode_qr.py','decode')}
    for relative in ('gui/renderer.py','gui/screens/screen.py','gui/screens/seed_screens.py','gui/screens/settings_screens.py','gui/screens/tools_screens.py','gui/screens/scan_screens.py','gui/screens/psbt_screens.py','views/screensaver.py','hardware/camera.py'):
        specs['seedsigner.'+relative[:-3].replace('/','.')]=(relative,'pil')
    specs['seedsigner.models.encode_qr']=('models/encode_qr.py','encoder')
    specs['seedsigner.models.encryptedqr']=('models/encryptedqr.py','storage')
    specs['seedsigner.controller']=('controller.py','controller')
    specs['seedsigner.gui.screens.screen']=('gui/screens/screen.py','screen')
    specs['seedsigner.gui.screens.settings_screens']=('gui/screens/settings_screens.py','settings')
    for name in ('tools_views','microsd_views','smartcard_views','gpg_views','password_generator_views','satochip_bias','keycard_bias'):
        specs['seedsigner.views.'+name]=('views/'+name+'.py','tools')
    return specs

def install(app_root,manifest):
    base=Path(app_root).resolve()/'seedsigner';guards=json.loads(Path(manifest).read_text())
    specs=specifications()
    if any(name in sys.modules for name in specs):raise RuntimeError('Install LVGL dependencies before app/UI modules load')
    from optional_imports import install as optional
    from stream_imports import install as stream_imports
    closers=[optional(),stream_imports()]
    class Loader:
        def __init__(self,name):self.name=name
        def create_module(self,spec):return None
        def exec_module(self,module):
            relative,kind=specs[self.name];path=base/relative;source=path.read_bytes()
            if hashlib.sha256(source).hexdigest()!=guards[relative]:raise ValueError('Unreviewed LVGL dependency source')
            filename=str(path) if kind in ('seed_views','pil','controller','screen','settings','storage','tools') else str(path)+' [LVGL dependency policy]'
            from import_cache import load
            code=load(self.name,source,filename=filename)
            if code is None:code=compile(transform(source,kind),filename,'exec')
            exec(code,module.__dict__)
            if kind=='decode':closers.append(native_extractor(module,Path(os.environ.get('SHIELDSIGNER_QR_READER','/usr/lib/shieldsigner-camera/shieldsigner-qr-reader'))))
    class Finder:
        def lvgl_dependency_spec(self,fullname,spec):
            if fullname not in specs:return spec
            if spec is None or Path(spec.origin).resolve()!=base/specs[fullname][0]:raise ValueError('Unexpected LVGL dependency origin')
            spec.loader=Loader(fullname);return spec
        def find_spec(self,fullname,path=None,target=None):
            if fullname not in specs:return None
            return self.lvgl_dependency_spec(fullname,PathFinder.find_spec(fullname,path,target))
    finder=Finder();sys.meta_path.insert(0,finder)
    def restore():
        if finder in sys.meta_path:sys.meta_path.remove(finder)
        for close in reversed(closers):close()
    return restore
