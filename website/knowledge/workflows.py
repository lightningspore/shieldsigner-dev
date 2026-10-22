"""Task content and sourcing data packaged from the reviewed project docs."""
import json
import re
from pathlib import Path

CONTENT_DIR = Path(__file__).resolve().parents[1] / 'content'


def load(name):
    return json.loads((CONTENT_DIR / f"{name}.json").read_text())


def tasks():
    return load("workflows")["tasks"]


def search_text(value):
    return re.sub(r"\s+", "", value.casefold().replace("µ", "u").replace("μ", "u").replace("ω", "ohm"))


def shopping(params):
    variant = params.get('variant', 'modular')
    if variant not in {'modular', 'standard'}:
        variant = 'modular'
    query = params.get("q", "").strip()[:200]
    scope = params.get("scope", "system")
    if scope not in {"all", "system", "carrier"}:
        scope = "all"
    try:
        quantity = int(params.get("quantity", "1"))
        if not 1 <= quantity <= 100:
            raise ValueError
        error = ""
    except (ValueError, TypeError):
        quantity = 1
        error = "Choose 1–100 boards. Showing quantities for one board."
    carrier = load('modular-carrier-parts' if variant == 'modular' else 'carrier-parts')
    system = load('modular-system-parts' if variant == 'modular' else 'system-parts')["parts"]
    piece_count = sum(part['qty'] for part in carrier)
    line_count = len(carrier)
    checked_at = min(part['checkedAt'] for part in carrier)
    system.sort(key=lambda part: not part["required"])
    if query:
        carrier = [p for p in carrier if search_text(query) in search_text(" ".join(str(v) for v in p.values()))]
        system = [p for p in system if search_text(query) in search_text(" ".join(str(v) for v in p.values()))]
    for part in carrier:
        part["total"] = part["qty"] * quantity
    for part in system:
        part["total"] = part["qty"] * quantity
    return {"query": query, "scope": scope, "quantity": quantity, "quantity_error": error,
            "variant": variant, "piece_count": piece_count, "line_count": line_count, "checked_at": checked_at,
            "bom_url": '/files/variants/lcd-module-2.8/manufacturing/bom-jlcpcb.csv' if variant == 'modular' else '/files/manufacturing/jlcpcb/bom-carrier-jlcpcb.csv',
            "carrier": carrier if scope != "system" else [],
            "system": system if scope != "carrier" else [],
            "carrier_count": len(carrier), "system_count": len(system)}
