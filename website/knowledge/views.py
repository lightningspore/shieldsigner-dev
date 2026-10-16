import json
from pathlib import Path
from xml.sax.saxutils import escape
from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.safestring import mark_safe
from markdown import markdown
from .catalog import GUIDES
from . import workflows

def entries(query=""):
    result = []
    for slug, source, category, title, description in GUIDES:
        body = (settings.CONTENT_DIR / f"{slug}.md").read_text()
        if query and query.casefold() not in (title + description + body).casefold(): continue
        result.append(dict(slug=slug, source=source, category=category, title=title, description=description))
    return result

def home(request):
    return render(request, "knowledge/home.html", {"tasks": workflows.tasks()})

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
    context={**item, "body": mark_safe(html), "guides": entries()}
    if slug=='enclosure':
        lead,section=html.split('<h2',1)
        assets=json.loads((settings.CONTENT_DIR/'enclosure-assets.json').read_text())
        context.update(lead=mark_safe(lead),body=mark_safe('<h2'+section),
            enclosure_files=[{**a,'href':f"/files/{a['name']}?v={a['sha256'][:12]}"} for a in assets['assets']])
        context['enclosure_models']={a['name'].removeprefix('shieldsigner-enclosure-').removesuffix('.glb'):f"/files/{a['name']}?v={a['sha256'][:12]}" for a in assets['assets'] if a['name'].endswith('.glb')}
    return render(request, "knowledge/detail.html", context)

def workflow(request, slug):
    tasks = workflows.tasks()
    task = next((p for p in tasks if p['slug']==slug), None)
    if task is None: raise Http404
    context = {'task':task, 'tasks':tasks, 'title':task['title'], 'description':task['summary'], 'next_task':next((p for p in tasks if p['slug']==task.get('next')),None)}
    if slug=='pcb': context['pcb_spec']=workflows.load('modular-pcb-spec')
    if slug=='parts':
        context.update(workflows.shopping(request.GET))
        if request.headers.get('HX-Request')=='true' and request.headers.get('HX-Boosted')!='true':
            response=render(request, 'knowledge/parts-results.html',context)
            response.headers['Vary']='HX-Request, HX-Boosted'
            return response
    if slug=='cards':
        card=request.GET.get('card','seedkeeper')
        flows=workflows.load('card-workflows')
        if card not in flows: card='seedkeeper'
        context.update(card=card, card_flow=flows[card])
    response=render(request,'knowledge/workflow.html',context)
    response.headers['Vary']='HX-Request, HX-Boosted'
    return response


def downloads(request):
    files = json.loads((settings.PUBLIC_DIR / "manifest.json").read_text())
    primary_names = {"shieldsigner-jlcpcb-order.zip", "shieldsigner-carrier-gerbers.zip", "shieldsigner-luckfox-kicad.zip", "schematic.pdf"}
    return render(request, "knowledge/downloads.html", {"files": files, "primary_files":[p for p in files if p["name"] in primary_names], "modular_files":[p for p in files if p["name"].startswith("shieldsigner-modular-")], "enclosure_files":[p for p in files if p["name"].startswith("shieldsigner-enclosure-")], "pdfs":[p for p in files if p["name"].startswith("reference/pdfs/")], "title": "Board files & sources", "description": "Native KiCad files, manufacturing review outputs and saved datasheets."})

def file(request, name):
    root = settings.PUBLIC_DIR.resolve()
    candidate = (root / name).resolve()
    if not candidate.is_relative_to(root) or not candidate.is_file(): raise Http404
    response = FileResponse(candidate.open("rb"), as_attachment=candidate.suffix not in {".pdf", ".svg", ".png"}, filename=candidate.name)
    response['Cache-Control'] = 'no-cache'
    return response

def health(request):
    version=workflows.load('site-version')
    return JsonResponse({'status':'ok','guides':len(entries()),'tasks':len(workflows.tasks()),'version':version['version'],'revision':version['revision'][:7]})
def robots(request): return HttpResponse("User-agent: *\nAllow: /\nSitemap: https://shieldsigner.dev/sitemap.xml\n", content_type="text/plain")
def sitemap(request):
    paths = ["/", "/guides/", "/downloads/", *(f"/build/{task['slug']}/" for task in workflows.tasks()), *(f"/guides/{p['slug']}/" for p in entries())]
    return HttpResponse('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f"<url><loc>https://shieldsigner.dev{escape(p)}</loc></url>" for p in paths)+"</urlset>", content_type="application/xml")
