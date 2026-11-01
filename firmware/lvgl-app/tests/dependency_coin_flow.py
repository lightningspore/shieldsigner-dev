"""Original Controller coin-flip checksum fixture under the current import cleanup."""
import runpy,sys
from pathlib import Path
sys.path[:0]=['/opt/src','/usr/lib/shieldsigner-camera/python']
from dependency_policy import install
restore=install('/opt/src',Path(__file__).parent/'source-guards.json')
try:runpy.run_path(str(Path(__file__).with_name('coin_flow.py')),run_name='__main__')
finally:restore()
