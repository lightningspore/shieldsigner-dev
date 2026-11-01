"""Defer SLIP39 recovery exports; retain original wordlist/wipe protection.

Only the reviewed shamir-mnemonic 0.3.0 package initializer is replaced. Every
export resolves to its original module/object on first access; no algorithms,
wordlist contents or secure-delete behavior are replaced.
"""
import sys
from importlib.machinery import PathFinder
REFERENCE='''# flake8: noqa

from .cipher import decrypt, encrypt
from .shamir import (
    EncryptedMasterSecret,
    combine_mnemonics,
    decode_mnemonics,
    generate_mnemonics,
    recover_ems,
    split_ems,
)
from .share import Share
from .utils import MnemonicError

__all__ = [
    "encrypt",
    "decrypt",
    "combine_mnemonics",
    "decode_mnemonics",
    "generate_mnemonics",
    "split_ems",
    "recover_ems",
    "EncryptedMasterSecret",
    "MnemonicError",
    "Share",
]
'''
EXPORTS={'decrypt':'cipher','encrypt':'cipher','EncryptedMasterSecret':'shamir','combine_mnemonics':'shamir','decode_mnemonics':'shamir','generate_mnemonics':'shamir','recover_ems':'shamir','split_ems':'shamir','Share':'share','MnemonicError':'utils'}

def validate(code):
    expected=compile(REFERENCE,'<reviewed shamir-mnemonic 0.3.0 initializer>','exec')
    if any(getattr(code,key)!=getattr(expected,key) for key in ('co_code','co_consts','co_names','co_flags')):
        raise ValueError('Unreviewed shamir-mnemonic package initializer')

def install():
    if 'shamir_mnemonic' in sys.modules:raise RuntimeError('Install optional imports before SLIP39 loads')
    class Loader:
        def __init__(self,original):self.original=original
        def create_module(self,spec):return None
        def exec_module(self,module):
            validate(self.original.get_code(module.__name__))
            module.__all__=['encrypt','decrypt','combine_mnemonics','decode_mnemonics','generate_mnemonics','split_ems','recover_ems','EncryptedMasterSecret','MnemonicError','Share']
            def resolve(name):
                if name not in EXPORTS:raise AttributeError(name)
                from importlib import import_module
                value=getattr(import_module('.'+EXPORTS[name],module.__name__),name)
                setattr(module,name,value);return value
            module.__getattr__=resolve
            module.__shieldsigner_lazy_exports__=True
    class Finder:
        def find_spec(self,fullname,path=None,target=None):
            if fullname!='shamir_mnemonic':return None
            spec=PathFinder.find_spec(fullname,path,target)
            if spec is None or spec.submodule_search_locations is None:raise ValueError('Expected installed SLIP39 package')
            spec.loader=Loader(spec.loader);return spec
    finder=Finder();sys.meta_path.insert(0,finder)
    def restore():
        if finder in sys.meta_path:sys.meta_path.remove(finder)
    return restore
