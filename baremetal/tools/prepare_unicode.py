# SPDX-License-Identifier: MIT
"""Fetch the pinned public Unicode conformance corpus; verify the saved REF oracle."""
import hashlib,json,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parents[1]
meta=json.loads((root/'unicode/provenance.json').read_text())
oracle=(root/'unicode/ref-oracle.json').read_bytes()
assert hashlib.sha256(oracle).hexdigest()==meta['refOracleSha256']
path=root/'.tools/unicode-15.0.0/NormalizationTest.txt'
if not path.exists():
 data=urllib.request.urlopen(meta['datasetUrl'],timeout=60).read()
 assert hashlib.sha256(data).hexdigest()==meta['datasetSha256']
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_bytes(data)
assert hashlib.sha256(path.read_bytes()).hexdigest()==meta['datasetSha256']
print('Verified Unicode15 corpus and saved read-only REF oracle')
