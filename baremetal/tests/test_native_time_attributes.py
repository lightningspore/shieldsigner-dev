# SPDX-License-Identifier: MIT
"""Frozen app code may only call time attributes the baremetal C module exports.

Host CPython provides time.time/ticks_diff, which masks AttributeError failures
that appear only on device (the same class of defect as the math.log2 report).
"""
import ast,re,unittest
from pathlib import Path
root=Path(__file__).resolve().parents[1]
# Uses guarded by hasattr/getattr fallbacks, reviewed individually.
GUARDED={('seedsigner_port/qr_display.py','ticks_diff')}
def native_time_exports():
    text=(root/'micropython/modmachine.c').read_text()
    table=re.search(r'time_globals_table\[\]=\{(.*?)\};',text,re.S).group(1)
    return set(re.findall(r'MP_QSTR_(\w+)',table))-{'__name__','time'}
def frozen_modules():
    text=(root/'micropython/manifest.py').read_text()
    return sorted(set(re.findall(r'"([\w/]+\.py)"|\'([\w/]+\.py)\'',text)))
class NativeTimeAttributeTests(unittest.TestCase):
    def test_frozen_modules_use_only_exported_time_attributes(self):
        exported=native_time_exports();self.assertEqual(exported,{'ticks_ms','sleep_ms'})
        missing=[]
        names=[a or b for a,b in frozen_modules()];self.assertGreater(len(names),100)
        for name in names:
            tree=ast.parse((root/'app'/name).read_text())
            aliases={a.asname or a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names if a.name=='time'}
            for n in ast.walk(tree):
                if isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name) and n.value.id in aliases:
                    if n.attr not in exported and (name,n.attr) not in GUARDED:missing.append((name,n.lineno,n.attr))
        self.assertEqual(missing,[])
if __name__=='__main__':unittest.main()
