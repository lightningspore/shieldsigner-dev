"""Readable nominal values and catalog ratings for passive components."""
import re


def nominal(value, refs):
    family = refs[0][0] if refs else ''
    value = value.strip()
    if family == 'R':
        match = re.fullmatch(r'(\d+(?:\.\d+)?)([RrKkMm])(\d*)', value)
        if match:
            number, prefix, fraction = match.groups()
            number += '.'+fraction if fraction else ''
            return number+' '+({'r':'','k':'k','m':'M'}[prefix.lower()])+'Ω'
        if re.fullmatch(r'\d+(?:\.\d+)?', value): return value+' Ω'
    if family in {'C','L'}:
        match = re.fullmatch(r'(\d+(?:\.\d+)?)([fpnumµμk]?)(?:[FH])?', value, re.I)
        if match:
            number, prefix = match.groups()
            prefix = 'µ' if prefix in {'u','µ','μ'} else prefix
            return number+' '+prefix+('F' if family=='C' else 'H')
    return value


def spaced(value):
    return re.sub(r'^(\d+(?:\.\d+)?)([fpnumkMµ]?[VFHAWΩ])$', r'\1 \2', value.replace('uF','µF').replace('uH','µH'))


def ratings(catalog, refs):
    family=refs[0][0] if refs else ''
    attributes={a['attribute_name_en']:a['attribute_value_name'] for a in catalog.get('attributes',[])}
    wanted={'C':['Voltage Rating','Tolerance','Temperature Coefficient'],
            'R':['Power(Watts)','Tolerance'],
            'L':['Current Rating','Tolerance']} .get(family,[])
    return ' · '.join(spaced(attributes[key]) for key in wanted if key in attributes)
