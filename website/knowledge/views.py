import json
from pathlib import Path
from xml.sax.saxutils import escape
from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.safestring import mark_safe
from markdown import markdown
from .catalog import GUIDES

def entries(query=""):
    result = []
    for slug, source, category, title, description in GUIDES:
        body = (settings.CONTENT_DIR / f"{slug}.md").read_text()
        if query and query.casefold() not in (title + description + body).casefold(): continue
        result.append(dict(slug=slug, source=source, category=category, title=title, description=description))
    return result

def home(request):
    return render(request, "knowledge/home.html", {"featured": [p for p in entries() if p["slug"] in {"hardware", "smartcards", "bom", "os-build"}]})

def guides(request):
    query = request.GET.get("q", "").strip()[:200]
    context = {"guides": entries(query), "query": query, "title": "Build knowledge", "description": "Search hardware, smartcards, firmware and assembly guides."}
    template = "knowledge/results.html" if request.headers.get("HX-Request") == "true" and request.headers.get("HX-Boosted") != "true" else "knowledge/guides.html"
    response = render(request, template, context)
    response.headers["Vary"] = "HX-Request, HX-Boosted"
    return response

def detail(request, slug):
    item = next((p for p in entries() if p["slug"] == slug), None)
    if item is None: raise Http404
    body = (settings.CONTENT_DIR / f"{slug}.md").read_text()
    # Only reviewed, explicitly allowlisted repository Markdown is trusted HTML.
    html = markdown(body, extensions=["extra", "sane_lists", "toc"])
    return render(request, "knowledge/detail.html", {**item, "body": mark_safe(html), "guides": entries()})

def downloads(request):
    files = json.loads((settings.PUBLIC_DIR / "manifest.json").read_text())
    return render(request, "knowledge/downloads.html", {"files": files, "title": "Board files & sources", "description": "Native KiCad files, manufacturing review outputs and saved datasheets."})

def file(request, name):
    root = settings.PUBLIC_DIR.resolve()
    candidate = (root / name).resolve()
    if not candidate.is_relative_to(root) or not candidate.is_file(): raise Http404
    return FileResponse(candidate.open("rb"), as_attachment=candidate.suffix not in {".pdf", ".svg"}, filename=candidate.name)

def health(request): return JsonResponse({"status": "ok", "guides": len(entries())})
def robots(request): return HttpResponse("User-agent: *\nAllow: /\nSitemap: https://shieldsigner.dev/sitemap.xml\n", content_type="text/plain")
def sitemap(request):
    paths = ["/", "/guides/", "/downloads/", *(f"/guides/{p['slug']}/" for p in entries())]
    return HttpResponse('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f"<url><loc>https://shieldsigner.dev{escape(p)}</loc></url>" for p in paths)+"</urlset>", content_type="application/xml")
