"""Run the enclosure gates in dependency order; native hardware cache required."""
from pathlib import Path
import subprocess
import sys
root=Path(__file__).resolve().parents[1]
for script in ['build','check_hardware','check_fasteners','check_buttons',
               'check_exploded','print_plate','slice','package']:
    print(f'Enclosure: {script}',flush=True)
    subprocess.run([sys.executable,str(root/'enclosure'/f'{script}.py')],cwd=root,check=True)
