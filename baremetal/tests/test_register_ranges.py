"""Validate framing/coverage before a hardware snapshot can become evidence."""
import base64
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from decode_register_ranges import decode

class RegisterRangesTest(unittest.TestCase):
    def test_complete_crc_and_resource_validation(self):
        payload=bytes(range(256))*16
        records=[{'kind':'begin','block':'pmu','base':0xff300000,'length':4096},
                 {'kind':'data','offset':0,'data':base64.b64encode(payload).decode()},
                 {'kind':'end','bytes':4096,'crc32':zlib.crc32(payload)}]
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'pmu.jsonl'
            def write(data):path.write_text('\r\n'.join(map(json.dumps,data))+'\r\n')
            write(records);self.assertEqual(decode(path)[1],payload)
            for change in ['truncated','crc','base','offset','short']:
                changed=json.loads(json.dumps(records))
                if change=='truncated':changed.pop()
                elif change=='crc':changed[-1]['crc32']^=1
                elif change=='base':changed[0]['base']+=4
                elif change=='offset':changed[1]['offset']=4
                else:changed[1]['data']=base64.b64encode(payload[:-4]).decode()
                write(changed)
                with self.subTest(change=change),self.assertRaises(ValueError):decode(path)
