"""Mutation tests for the artwork link in the protected native audit chain."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import uuid

SCRIPT=Path(__file__).resolve().parents[1]/'audit-front-artwork.py'
spec=importlib.util.spec_from_file_location('front_artwork_audit',SCRIPT)
audit=importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
BASE='''(kicad_pcb (version 20260101)
 (setup (pad_to_mask_clearance 0.05))
 (segment (start 1 1) (end 2 2) (width 0.2) (layer "F.Cu") (net 1) (uuid "track"))
 (gr_text "PIN 1" (at 1 1) (layer "F.SilkS") (uuid "pin"))
 (gr_text "UPSTREAM" (at 2 2) (layer "B.SilkS") (uuid "rear")))'''
ID=str(uuid.uuid5(uuid.NAMESPACE_URL,'shieldsigner-front-orbital:0'))
GRAPHIC=f'(gr_line (start 3 3) (end 4 4) (stroke (width 0.2) (type solid)) (layer "F.SilkS") (uuid "{ID}"))'
GROUP=f'(group "Front art" (uuid "art-group") (members "{ID}"))'
CANDIDATE=BASE[:-1]+GRAPHIC+GROUP+')'


class FrontArtworkTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        (self.root/'hardware').mkdir()
        self.board=self.root/'candidate.kicad_pcb'
        self.record=self.root/'record.json'
        self.rec=dict(baselineCommit='fixture',baselineBoardSha256=hashlib.sha256(BASE.encode()).hexdigest(),
                      graphics=1,groupUuid='art-group',groupName='Front art',
                      protectedTreeSha256=audit.art['digest'](audit.art['protected'](audit.sx['parse'](BASE))),
                      scope='Front graphics only',minimumStrokeMm=.15,maskClearanceMm=.35)

    def verify(self,text):
        self.board.write_text(text)
        self.rec['boardSha256']=hashlib.sha256(text.encode()).hexdigest()
        self.record.write_text(json.dumps(self.rec))
        with patch.object(audit,'ROOT',self.root),patch.object(audit,'PCB',self.board),patch.object(audit,'RECORD',self.record),patch.object(audit.subprocess,'check_output',return_value=BASE.encode()):
            return audit.verify()

    def test_grouped_front_addition_returns_exact_predecessor(self):
        self.assertEqual(self.verify(CANDIDATE),BASE.encode())
        self.assertTrue(json.loads((self.root/'hardware/front-artwork-audit.json').read_text())['passed'])

    def test_mutations_fail_even_if_new_board_hash_is_recorded(self):
        mutations=[
            CANDIDATE.replace('(width 0.2) (layer "F.Cu")','(width 0.3) (layer "F.Cu")'),
            CANDIDATE.replace('"PIN 1"','"PIN 2"'),
            CANDIDATE.replace('"UPSTREAM"','"CHANGED"'),
            CANDIDATE.replace('(members "'+ID+'")','(members "track")'),
            CANDIDATE.replace(GRAPHIC,GRAPHIC.replace('F.SilkS','F.Cu')),
            CANDIDATE.replace(GRAPHIC,GRAPHIC+GRAPHIC),
        ]
        for candidate in mutations:
            with self.subTest(candidate=candidate),self.assertRaises(AssertionError):
                self.verify(candidate)


if __name__=='__main__':
    unittest.main()
