"""Native PCB structural fixtures: no KiCad, router, board writes or hardware."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'audit-pcb-artwork.py'
spec = importlib.util.spec_from_file_location('pcb_artwork_audit', SCRIPT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

BOARD = '''(kicad_pcb
 (version 20241229)
 (general (thickness 1.6))
 (layers (0 "F.Cu" signal) (31 "B.Cu" signal))
 (setup (pad_to_mask_clearance 0) (stackup (layer "F.Cu" (type "copper")) (layer "B.Cu" (type "copper"))))
 (net 1 "GND")
 (footprint "fixture" (layer "F.Cu") (uuid "fp-1") (at 10 20 90)
  (property "Reference" "J1" (at 0 0) (layer "F.SilkS"))
  (pad "1" thru_hole circle (at 0 0) (size 1 1) (drill 0.5) (layers "*.Cu" "*.Mask") (net 1 "GND")))
 (segment (start 1 2) (end 3 4) (width 0.2) (layer "F.Cu") (net 1) (uuid "track-1"))
 (via (at 3 4) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net 1) (uuid "via-1"))
 (zone (net 1) (layer "F.Cu") (uuid "zone-1") (polygon (pts (xy 0 0) (xy 5 0) (xy 5 5))))
 (gr_line (start 0 0) (end 5 0) (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "edge-1"))
 (gr_text "Before" (at 1 1) (layer "F.SilkS") (uuid "text-1"))
)'''


class ArtworkAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.before = Path(self.tmp.name) / 'before.kicad_pcb'
        self.after = Path(self.tmp.name) / 'after.kicad_pcb'
        self.before.write_text(BOARD)

    def compare(self, candidate):
        self.after.write_text(candidate)
        return audit.compare(self.before, self.after)

    def test_identical_board_and_reordered_top_objects_pass(self):
        self.assertTrue(self.compare(BOARD)['passed'])
        tree = audit.read_board(self.before)
        reordered = '(kicad_pcb ' + ' '.join(self.sexpr(node) for node in reversed(tree[1:])) + ')'
        result = self.compare(reordered)
        self.assertTrue(result['passed'])
        self.assertEqual(result['baseline']['protectedSha256'], result['candidate']['protectedSha256'])

    @staticmethod
    def sexpr(value):
        import json
        if isinstance(value, list):
            return '(' + ' '.join(ArtworkAuditTests.sexpr(child) for child in value) + ')'
        return json.dumps(value) if any(char.isspace() for char in value) else value

    def test_only_top_level_silk_changes_and_logo_additions_pass(self):
        polygon = '(gr_poly (pts (xy 0 0) (xy 1 0) (xy 1 1)) (layer "B.SilkS") (uuid "logo-1"))'
        text = '(gr_text "ShieldSigner" (at 2 2) (layer "F.SilkS") (uuid "text-2"))'
        result = self.compare(BOARD.replace('"Before"', '"After"')[:-1] + polygon + text + ')')
        self.assertTrue(result['passed'])
        self.assertEqual(result['silkscreen']['changedExistingUuidCount'], 1)
        self.assertEqual(result['silkscreen']['addedPolygonCount'], 1)
        self.assertEqual(result['silkscreen']['addedTextCount'], 1)

    def test_protected_geometry_and_rules_cannot_change(self):
        mutations = [
            ('(at 10 20 90)', '(at 11 20 90)', 'footprint'),
            ('"Reference" "J1"', '"Reference" "J2"', 'footprint'),
            ('(size 1 1)', '(size 2 1)', 'footprint'),
            ('(net 1 "GND")))', '(net 2 "VCC")))', 'footprint'),
            ('(width 0.2)', '(width 0.3)', 'segment'),
            ('(drill 0.3)', '(drill 0.4)', 'via'),
            ('(xy 0 0) (xy 5 0) (xy 5 5)', '(xy 5 0) (xy 0 0) (xy 5 5)', 'zone'),
            ('(end 5 0)', '(end 6 0)', 'gr_line'),
            ('(pad_to_mask_clearance 0)', '(pad_to_mask_clearance 0.1)', 'setup'),
            ('(thickness 1.6)', '(thickness 2.0)', 'general'),
            ('"track-1"', '"track-2"', 'segment'),
        ]
        for old, new, tag in mutations:
            with self.subTest(tag=tag, old=old):
                result = self.compare(BOARD.replace(old, new))
                self.assertFalse(result['passed'])
                self.assertIn(tag, result['protectedChangedTags'])

    def test_footprint_silkscreen_is_protected(self):
        result = self.compare(BOARD.replace('(property "Reference" "J1" (at 0 0)', '(property "Reference" "J1" (at 1 0)'))
        self.assertFalse(result['passed'])

    def test_silk_cannot_be_moved_to_copper_or_edge_layer(self):
        for layer in ('F.Cu', 'Edge.Cuts'):
            with self.subTest(layer=layer):
                result = self.compare(BOARD.replace('(layer "F.SilkS") (uuid "text-1")', '(layer "' + layer + '") (uuid "text-1")'))
                self.assertFalse(result['passed'])

    def test_ambiguous_duplicate_layer_does_not_bypass_protection(self):
        result = self.compare(BOARD.replace('(layer "F.SilkS") (uuid "text-1")', '(layer "F.SilkS") (layer "F.Cu") (uuid "text-1")'))
        self.assertFalse(result['passed'])

    def test_stackup_layer_order_is_protected(self):
        result = self.compare(BOARD.replace('(layer "F.Cu" (type "copper")) (layer "B.Cu" (type "copper"))', '(layer "B.Cu" (type "copper")) (layer "F.Cu" (type "copper"))'))
        self.assertFalse(result['passed'])

    def test_multiple_roots_and_unbalanced_input_are_rejected(self):
        for value in (BOARD + '(kicad_pcb)', BOARD[:-1], BOARD + ')'):
            with self.subTest(value=value[-20:]), self.assertRaises(ValueError):
                self.compare(value)


if __name__ == '__main__':
    unittest.main()
