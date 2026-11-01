"""Target Pillow equivalence for NV12 grayscale sample representation; public pixels."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from PIL import Image
from experimental_entropy_samples import GrayscaleSample
base=Image.frombytes('L',(128,128),bytes(range(256))*64)
checks=[]
for rotation in (0,90,180,270):
    original=base.convert('RGB').rotate(rotation,expand=True)
    sample=GrayscaleSample(base.rotate(rotation,expand=True))
    assert sample.getextrema()==original.getextrema()
    assert sample.convert('L').tobytes()==original.convert('L').tobytes()
    assert sample.convert('L').resize((96,96),Image.Resampling.BILINEAR).tobytes()==original.convert('L').resize((96,96),Image.Resampling.BILINEAR).tobytes()
    checks.append(dict(rotation=rotation,all256Levels=True,extremaAndSampleBytesExact=True))
print(json.dumps(dict(passed=True,checks=checks,physicalCamera=False,physicalDisplay=False,finalCaptureFormatChanged=False)),flush=True)
