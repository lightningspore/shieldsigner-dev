"""Offline-only closed-set shaping supplement for the pinned original catalog.

No translation text changes. Expand only the complete, finite value domains of
four templates rejected by upstream segmented shaping. Keep catalog production
upstream-owned; replace entries only for font/run compilation.
"""
import json,sys
from pathlib import Path
FINAL='The {mnemonic_length}th word is built from {num_bits} more entropy bits plus auto-calculated checksum.'
WARNINGS=("Transaction's {} address could not be generated from your seed.","Transaction's {} address could not be verified from wallet descriptor.")

def expand(locale,entries):
    entries=list(entries);catalog=dict(entries);replacements={};proof=[]
    if locale=='hi':
        if FINAL not in catalog:raise ValueError('Pinned Hindi final-word template missing')
        replacements[FINAL]=[catalog[FINAL].format(mnemonic_length=length,num_bits=bits) for length,bits in ((12,7),(24,3))]
    elif locale=='th':
        for template in WARNINGS:
            if template not in catalog:raise ValueError('Pinned Thai warning template missing')
            replacements[template]=[catalog[template].format(catalog.get(value,value)) for value in ('change','self-transfer')]
        template='{} change'
        if template not in catalog:raise ValueError('Pinned Thai denomination template missing')
        replacements[template]=[catalog[template].format(catalog.get(value,value)) for value in ('btc','sats')]
    result=[]
    for msgid,msgstr in entries:
        if msgid not in replacements:result.append((msgid,msgstr));continue
        for text in replacements[msgid]:
            if '{' in text or '}' in text:raise ValueError('Supplement retained a placeholder')
            # No brace-bearing msgid: upstream classifies this as a plain whole run.
            result.append(('Closed-set shaped display text',text))
            proof.append(dict(locale=locale,msgid=msgid,template=msgstr,text=text))
    return result,proof

def main():
    sys.path.insert(0,'/work/tools')
    import build_fontpacks as producer
    original=producer.iter_translations;proof=[]
    def translations(path):
        locale=Path(path).parents[1].name
        entries,rows=expand(locale,original(path));proof.extend(rows)
        return iter(entries)
    producer.iter_translations=translations
    result=producer.main()
    out=Path(sys.argv[sys.argv.index('--out-dir')+1])
    # Corpus extraction can call the iterator repeatedly; retain distinct rows.
    unique={json.dumps(row,sort_keys=True):row for row in proof}
    (out/'supplemental-shaping.json').write_text(json.dumps(list(unique.values()),ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    return result
if __name__=='__main__':raise SystemExit(main())
