"""Render the explicit public content into an ordinary static document root."""
import json
from pathlib import Path
import shutil
import sys
from xml.sax.saxutils import escape

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup
from markdown import markdown

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE))
from knowledge.catalog import GUIDES
from knowledge import workflows

OUT = SITE/'dist'
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir()
shutil.copytree(SITE/'public', OUT/'files')
shutil.copytree(SITE/'static', OUT/'static')
env = Environment(loader=FileSystemLoader(SITE/'templates'), autoescape=select_autoescape(['html']))
env.filters['pluralize'] = lambda count: '' if count == 1 else 's'
version = workflows.load('site-version')
common = dict(site_version=version['version'], site_revision=version['revision'][:7],
              site_dirty=version['dirty'], site_revision_url='https://github.com/lightningspore/shieldsigner-dev/commit/'+version['revision'])
paths = []

def render(url, template, **context):
    target = OUT/url.lstrip('/')/'index.html'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(env.get_template(template).render(**common, page_path=url, **context))
    paths.append(url)

assets=workflows.load('enclosure-assets')
enclosure = dict(enclosure_files=[{**a,'href':f"/files/{a['name']}?v={a['sha256'][:12]}"} for a in assets['assets']],
                enclosure_models={a['name'].removeprefix('shieldsigner-enclosure-').removesuffix('.glb'):f"/files/{a['name']}?v={a['sha256'][:12]}" for a in assets['assets'] if a['name'].endswith('.glb')})
guides = []
search = {}
for slug, source, category, title, description in GUIDES:
    body=(SITE/'content'/f'{slug}.md').read_text()
    guides.append(dict(slug=slug,source=source,category=category,title=title,description=description))
    search[slug]=(title+' '+description+' '+body).casefold()
render('/', 'knowledge/home.html', tasks=workflows.tasks(), **enclosure)
render('/guides/', 'knowledge/guides.html', guides=guides, query='', title='Build knowledge', description='Search hardware, smartcards, firmware and assembly guides.')
for guide in guides:
    html=markdown((SITE/'content'/f"{guide['slug']}.md").read_text(), extensions=['extra','sane_lists','toc'])
    context={**guide,'body':Markup(html),'guides':guides}
    if guide['slug']=='enclosure':
        lead, section=html.split('<h2',1)
        context.update(lead=Markup(lead), body=Markup('<h2'+section), **enclosure)
    render(f"/guides/{guide['slug']}/",'knowledge/detail.html',**context)

def task_context(task):
    tasks=workflows.tasks()
    context=dict(task=task, tasks=tasks, title=task['title'],description=task['summary'],
                 next_task=next((t for t in tasks if t['slug']==task.get('next')),None))
    if task['slug']=='pcb': context['pcb_spec']=workflows.load('modular-pcb-spec')
    if task['slug']=='parts':
        # Complete static tables remain readable when scripting is unavailable.
        context.update(workflows.shopping({'scope':'all'}))
        context['part_variants']={v:Markup(env.get_template('knowledge/parts-results.html').render(**workflows.shopping({'variant':v,'scope':'all'}))) for v in ['modular','standard']}
    return context

for task in workflows.tasks():
    context=task_context(task)
    if task['slug']=='cards':
        flows=workflows.load('card-workflows')
        for card, flow in flows.items():
            render(f'/build/cards/{card}/','knowledge/workflow.html',**context,card=card,card_flow=flow)
        context.update(card='seedkeeper', card_flow=flows['seedkeeper'])
    render(f"/build/{task['slug']}/",'knowledge/workflow.html',**context)

files=json.loads((SITE/'public/manifest.json').read_text())
primary={'shieldsigner-jlcpcb-order.zip','shieldsigner-carrier-gerbers.zip','shieldsigner-luckfox-kicad.zip','schematic.pdf'}
render('/downloads/','knowledge/downloads.html', files=files, primary_files=[p for p in files if p['name'] in primary],
       modular_version=json.loads((SITE.parent/'assets/modular-downloads.json').read_text())['release'].removeprefix('pill-preview-'),
       enclosure_version=assets['version'],
       modular_files=[p for p in files if p['name'].startswith('shieldsigner-modular-')],
       enclosure_files=[p for p in files if p['name'].startswith('shieldsigner-enclosure-')],
       pdfs=[p for p in files if p['name'].startswith('reference/pdfs/')],
       title='Board files & sources', description='Native KiCad files, manufacturing review outputs and saved datasheets.')
(OUT/'static/guide-search.json').write_text(json.dumps(search)+'\n')
(OUT/'healthz').write_text(json.dumps(dict(status='ok',hosting='static',guides=len(guides),tasks=len(workflows.tasks()),version=version['version'],revision=version['revision'][:7]))+'\n')
(OUT/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: https://shieldsigner.dev/sitemap.xml\n')
(OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>https://shieldsigner.dev{escape(p)}</loc></url>' for p in paths)+'</urlset>')
(OUT/'404.html').write_text(env.get_template('knowledge/not-found.html').render(**common,page_path='/404.html',title='Page not found'))
print(f'Static site: {len(paths)} HTML routes, {len(files)} downloadable files → {OUT}')
