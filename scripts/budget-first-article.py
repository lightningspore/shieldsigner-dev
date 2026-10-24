#!/usr/bin/env python3
"""Price one first article and optional repeats; never turn missing costs into zero."""
import json
import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'variants/lcd-module-2.8/self-assembly'
data = json.loads((BASE / 'pricing-current.json').read_text())
with (BASE / 'bom-digikey.csv').open() as file:
    bom = list(csv.DictReader(file))
normalize = lambda value: ''.join(value.split()).casefold()
expected = {normalize(p['Manufacturer Part Number']): int(p['Quantity per board']) for p in bom}
actual = {normalize(p['mpn']): p['perBoard'] for p in data['parts']}
assert len(actual) == len(data['parts']) and actual == expected, 'Pricing does not cover the selected BOM exactly'

def money(n):
    return str(n.quantize(Decimal('.01'), rounding=ROUND_HALF_UP))

def scenario(boards, spares):
    lines = []
    total = Decimal(0)
    for part in data['parts']:
        installed = boards * part['perBoard']
        required = installed
        if spares:
            if part['mpn'].startswith(('CC0805', 'CL21', 'C0805', 'RC0805', 'CR0805')):
                required = max(10, installed + 2)
            elif part['perBoard'] == 8:
                required += 2
            else:
                required += 1
        tiers = part['priceTiers']
        def price(qty):
            return Decimal(max((t for t in tiers if t['quantity'] <= qty),
                               key=lambda t: t['quantity'])['unitUSD'])
        # A larger quantity at a price break can cost less in total. Retain
        # quantities explicitly so saved cost never disguises extra purchases.
        candidates = {required, *(t['quantity'] for t in tiers if t['quantity'] >= required)}
        qty = min(candidates, key=lambda q: (q * price(q), q))
        extension = (qty * price(qty)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
        total += extension
        lines.append({'mpn': part['mpn'], 'installed': installed,
                      'purchaseQuantity': qty, 'unitUSD': str(price(qty)),
                      'extensionUSD': str(extension), 'publicStock': part['publicStock'],
                      'stockSufficient': part['publicStock'] >= qty, 'url': part['url']})
    return {'populatedBoards': boards, 'sparesIncluded': spares,
            'partsSubtotalUSD': money(total),
            'allPartsAvailable': all(p['stockSufficient'] for p in lines), 'lines': lines}

report = {
    'currency': 'USD', 'pricingSource': 'pricing-current.json',
    'decision': 'First article only before repeat builds; complete landed cost remains unquoted.',
    'scenarios': [scenario(1, False), scenario(1, True), scenario(3, False)],
    'sparesPolicy': 'Illustrative only: at least 10 and two extras per passive line; two extra switches; one extra per other fitted line. Price-break quantity increases are shown. Not a purchase instruction.',
    'unquotedCostsUSD': {k: None for k in [
        'barePcbMinimumOrder', 'stencil', 'pasteFluxAndConsumables',
        'headersAndMechanicalHardware', 'lcd', 'luckfox', 'camera', 'microSd',
        'enclosure', 'testCard', 'shipping', 'taxAndTariffs',
        'missingAssemblyAndTestEquipment', 'outsourcedAssemblyIfChosen', 'laborAndRework']},
    'totalLandedCostUSD': None,
    'notes': [
        'All selected lines have dated public stock observations; confirm inventory and checkout charges before ordering.',
        'A three-board parts basket does not authorize populating repeats before first-article acceptance.',
        'No yield assumption, equipment ownership, free labor or shipping subsidy is assumed.',
        'Buying a PCB minimum does not require populating all delivered boards.',
        'Compare full self-assembly against a bottom-only assembly quote and full PCBA including setup, minimums and freight.'
    ]
}
system = json.loads((BASE / 'system-pricing-current.json').read_text())
module_subtotal = sum((Decimal(p['unitUSD']) for p in system['items']), Decimal(0))
lcd = Decimal(next(p['unitUSD'] for p in system['items'] if p['id'] == 'lcd'))
report['systemPricingSource'] = 'system-pricing-current.json'
report['identifiedModuleSubtotalUSD'] = money(module_subtotal)
report['oneArticleIdentifiedItemsUSD'] = money(Decimal(report['scenarios'][0]['partsSubtotalUSD']) + module_subtotal)
report['oneArticleWithSparesIdentifiedItemsUSD'] = money(Decimal(report['scenarios'][1]['partsSubtotalUSD']) + module_subtotal)
report['carrierComponentsPlusLcdUSD'] = money(Decimal(report['scenarios'][0]['partsSubtotalUSD']) + lcd)
report['comparison'] = {
    'existingHatWithLcdBaseUSD': system['comparisonOnly']['baseUSD'],
    'existingHatWithLcdSocketOptionUSD': system['comparisonOnly']['socketOptionUSD'],
    'note': system['comparisonOnly']['qualification'],
    'decision': system['decision']
}
for key in ['lcd', 'luckfox', 'camera']:
    report['unquotedCostsUSD'].pop(key)
report['notes'].append('Identified-items subtotals include selected LCD, bare Mini A and low-profile camera, but omit remaining unquoted costs.')
calc = json.loads((BASE.parent / 'manufacturing/jlc-calculator-estimate.json').read_text())
report['dimensionalBarePcbEstimateSource'] = '../manufacturing/jlc-calculator-estimate.json'
report['partialCashOutlayExamples'] = []
for case in calc['cases'][:2]:
    board = Decimal(case['pcbSubtotalUSD'])
    freight = Decimal(calc['shippingEstimates']['options'][0]['USD'])
    items = Decimal(report['oneArticleIdentifiedItemsUSD'])
    report['partialCashOutlayExamples'].append({
        'finish': case['surfaceFinish'], 'bareBoardsPurchased': 5, 'populatedBoardsPlanned': 1,
        'bareBoardBatchAndEstimatedJlcFreightUSD': money(board + freight),
        'identifiedComponentsModulesAndEstimatedBareBoardShipmentUSD': money(items + board + freight),
        'note': 'Partial cash outlay for one article, not divided by five. No Gerber validation; excludes assembly/stencil, other suppliers shipping/taxes, headers/hardware, SD/card/case, tools/labor. Slower shipping eligibility must be rechecked.'})
(BASE / 'first-article-budget.json').write_text(json.dumps(report, indent=2) + '\n')
for row in report['scenarios']:
    print(f"{row['populatedBoards']} board(s), spares={row['sparesIncluded']}: ${row['partsSubtotalUSD']} parts, complete stock={row['allPartsAvailable']}")
print('Landed cost: unknown; see first-article-budget.json for unquoted items.')
print('Identified first-article parts/modules: $' + report['oneArticleIdentifiedItemsUSD'] + ', or $' + report['oneArticleWithSparesIdentifiedItemsUSD'] + ' with illustrative component spares; not a complete build quote.')
