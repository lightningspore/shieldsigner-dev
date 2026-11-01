#!/usr/bin/env python3
"""Compare two native PCB files; allow only top-level front/back silkscreen art.

Read-only with respect to both boards. This does not replace KiCad DRC or a
visual silkscreen clearance review. Failed comparisons exit nonzero.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import runpy

SX = runpy.run_path(str(Path(__file__).with_name('kicad-sexpr.py')))
SILK_LAYERS = {'F.SilkS', 'B.SilkS'}
SILK_GRAPHICS = {'gr_arc', 'gr_circle', 'gr_curve', 'gr_line', 'gr_poly',
                 'gr_rect', 'gr_text', 'gr_text_box'}
# These containers are explicitly ordered: in particular, sorting (xy ...) in
# a polygon could turn a changed outline into an apparent semantic match.
ORDERED = {'pts', 'stackup'}
UNORDERED = {'kicad_pcb', 'footprint', 'module'}


def read_board(path):
    text = Path(path).read_text()
    depth = roots = 0
    for token in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text):
        if token == '(':
            roots += depth == 0
            depth += 1
        elif token == ')':
            depth -= 1
            if depth < 0:
                raise ValueError('Unbalanced PCB expression')
        elif depth == 0:
            raise ValueError('Unexpected content outside PCB expression')
    if depth or roots != 1:
        raise ValueError('Expected one balanced PCB expression')
    board = SX['parse'](text)
    if not board or board[0] != 'kicad_pcb':
        raise ValueError('Expected native kicad_pcb root')
    return board


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def canonical(node):
    """Normalize metadata/object order without sorting positional coordinates.

    Scalar atom values (including numeric spelling and UUIDs) remain exact.
    Unknown repeated children retain order: an unsupported serializer rewrite
    may fail conservatively, rather than conceal a geometry/rule change.
    """
    if not isinstance(node, list):
        return node
    values = [canonical(value) for value in node]
    if not values or values[0] in ORDERED:
        return values
    scalars = [value for value in values if not isinstance(value, list)]
    nested = [value for value in values if isinstance(value, list)]
    tags = [value[0] if value else None for value in nested]
    # A scalar occurring after child nodes may be positional syntax; retain it.
    prefix_only = values == scalars + nested
    if prefix_only and (values[0] in UNORDERED or len(tags) == len(set(tags))):
        return scalars + sorted(nested, key=encoded)
    return values


def silk(node):
    return (isinstance(node, list) and bool(node) and node[0] in SILK_GRAPHICS
            and len(SX['children'](node, 'layer')) == 1
            and SX['one'](node, 'layer')[1:] in [['F.SilkS'], ['B.SilkS']])


def digest(value):
    return hashlib.sha256(encoded(value).encode()).hexdigest()


def protected(board):
    return canonical([value for value in board if not silk(value)])


def counts(nodes):
    return dict(sorted(collections.Counter(
        node[0] + ':' + SX['one'](node, 'layer')[1] for node in nodes).items()))


def protected_counts(board):
    result = dict(sorted(collections.Counter(
        node[0] for node in board if isinstance(node, list) and node and not silk(node)).items()))
    result['footprintPads'] = sum(len(SX['children'](node, 'pad')) for node in SX['children'](board, 'footprint'))
    return result


def compare(baseline, candidate):
    before, after = read_board(baseline), read_board(candidate)
    before_protected, after_protected = protected(before), protected(after)
    before_art = [node for node in before if silk(node)]
    after_art = [node for node in after if silk(node)]
    before_map = collections.Counter(encoded(canonical(node)) for node in before_art)
    after_map = collections.Counter(encoded(canonical(node)) for node in after_art)
    added = [json.loads(value) for value, count in (after_map - before_map).items() for _ in range(count)]
    removed = [json.loads(value) for value, count in (before_map - after_map).items() for _ in range(count)]
    def uuid(node):
        return tuple(SX['one'](node, 'uuid')[1:] or SX['one'](node, 'tstamp')[1:])
    old_ids = {uuid(node) for node in removed if uuid(node)}
    changed_ids = old_ids & {uuid(node) for node in added if uuid(node)}
    changed_protected = []
    for tag in sorted({value[0] for board in (before, after) for value in board if isinstance(value, list) and value and not silk(value)}):
        left = sorted((encoded(canonical(value)) for value in SX['children'](before, tag) if not silk(value)))
        right = sorted((encoded(canonical(value)) for value in SX['children'](after, tag) if not silk(value)))
        if left != right:
            changed_protected.append(tag)
    report = dict(schema=1, kind='shieldsigner-pcb-artwork-only-audit',
        passed=before_protected == after_protected,
        baseline=dict(path=str(Path(baseline)), sha256=hashlib.sha256(Path(baseline).read_bytes()).hexdigest(), protectedSha256=digest(before_protected), protectedCounts=protected_counts(before)),
        candidate=dict(path=str(Path(candidate)), sha256=hashlib.sha256(Path(candidate).read_bytes()).hexdigest(), protectedSha256=digest(after_protected), protectedCounts=protected_counts(after)),
        protectedChangedTags=changed_protected,
        silkscreen=dict(baseline=counts(before_art), candidate=counts(after_art),
            addedOrChanged=counts(added), removedOrChanged=counts(removed), changedExistingUuidCount=len(changed_ids),
            addedPolygonCount=sum(node[0] == 'gr_poly' and uuid(node) not in changed_ids for node in added),
            addedTextCount=sum(node[0] in {'gr_text', 'gr_text_box'} and uuid(node) not in changed_ids for node in added)),
        scope='Exact protected PCB tree modulo harmless object/unique-key metadata ordering; only known top-level F.SilkS/B.SilkS graphics may differ. Footprints (including silk/properties/pads/poses), tracks, vias, zones, edges, layers, nets, setup and UUID values remain protected.',
        limits='Not DRC, fabrication qualification or visual artwork-clearance approval. Numeric atom spelling changes and unsupported repeated-child reorderings fail conservatively.')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, help='Optional JSON report; boards are never written')
    args = parser.parse_args()
    report = compare(args.baseline, args.candidate)
    text = json.dumps(report, indent=2) + '\n'
    if args.output:
        if args.output.resolve() in {args.baseline.resolve(), args.candidate.resolve()}:
            parser.error('Report output must not overwrite a board')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text, end='')
    if not report['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
