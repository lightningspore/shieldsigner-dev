"""Task content and sourcing data packaged from the reviewed project docs."""
import json
import re
from django.conf import settings


def load(name):
    return json.loads((settings.CONTENT_DIR / f"{name}.json").read_text())


def tasks():
    return load("workflows")["tasks"]


def search_text(value):
    return re.sub(r"\s+", "", value.casefold().replace("µ", "u").replace("μ", "u").replace("ω", "ohm"))


def shopping(params):
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
    carrier = load("carrier-parts")
    system = load("system-parts")["parts"]
    system.sort(key=lambda part: not part["required"])
    if query:
        carrier = [p for p in carrier if search_text(query) in search_text(" ".join(str(v) for v in p.values()))]
        system = [p for p in system if search_text(query) in search_text(" ".join(str(v) for v in p.values()))]
    for part in carrier:
        part["total"] = part["qty"] * quantity
    for part in system:
        part["total"] = part["qty"] * quantity
    return {"query": query, "scope": scope, "quantity": quantity, "quantity_error": error,
            "carrier": carrier if scope != "system" else [],
            "system": system if scope != "carrier" else [],
            "carrier_count": len(carrier), "system_count": len(system)}
