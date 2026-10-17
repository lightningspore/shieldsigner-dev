"""Build/search a private source index. No network calls or external AI services."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import html
import json
import os
from pathlib import Path
import re
import sqlite3
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

ROOT = Path(__file__).resolve().parent / 'private'
RULES = {
 'build': r'\b(luckfox|buildroot|solder\w*|pcb|st7789|sc3336|pinout|gpio|schematic|bom|enclosure|3d print\w*|ribbon|waveshare)\b',
 'multisig': r'\b(multisig|multi.sig|cosigner|co.signer|2.of.3|3.of.5|quorum|descriptor|inheritance)\b',
 'smartcards': r'\b(seedkeeper|satochip|satodime|keycard|smartcard|smart.card|sec1210|javacard|pc/sc|apdu)\b',
 'backups': r'\b(backup\w*|recover\w*|seedqr|compactseedqr|slip.?39|bip.?85|passphrase|steel|seed phrase)\b',
 'troubleshooting': r'\b(error|fail\w*|doesn.t work|not working|won.t boot|blank screen|timeout|workaround|fix\w*|bug)\b',
 'security': r'\b(entropy|randomness|dice|air.?gap|threat model|secure boot|supply chain|malicious|vulnerab\w*|nonce|firmware verification)\b',
 'wallets': r'\b(sparrow|specter|bluewallet|nunchuk|keeper|electrum|bitcoin core|psbt|taproot|address verification)\b',
 'development': r'\b(pull request|github|commit|release|python|driver|regression|unit test|buildroot|firmware)\b',
}
PATTERNS = {k:re.compile(v,re.I) for k,v in RULES.items()}
URL = re.compile(r'https?://[^\s<>"\x00-\x1f]+',re.I)

def reference(chat,mid):
    return f'https://t.me/c/{str(chat).removeprefix("-100")}/{mid}' if str(chat).startswith('-100') else ''

def normalize(raw):
    raw=raw.rstrip('.,;:!?)]}*`\\')
    try:
        p=urlsplit(raw)
        # Keep non-HTTP URLs and signed/credential-bearing links out of the catalog.
        if not p.hostname or p.username or p.password or p.port not in (None,80,443): return None
        pairs=parse_qsl(p.query,keep_blank_values=True)
        if any(re.search(r'token|secret|password|auth|signature|api.?key|credential',k,re.I) for k,v in pairs): return None
        pairs=[(k,v) for k,v in pairs if not k.lower().startswith('utm_') and k.lower() not in ('fbclid','gclid')]
        return urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path or '/',urlencode(pairs),p.fragment))
    except ValueError: return None

def build():
    config=json.loads((ROOT/'config.json').read_text())
    groups={g['id']:g['slug'] for g in config['groups']}
    target=ROOT/'knowledge.building.sqlite3'
    target.unlink(missing_ok=True)
    with sqlite3.connect(f'file:{ROOT / "messages.sqlite3"}?mode=ro',uri=True) as source, sqlite3.connect(target) as db:
        db.executescript('''DROP TABLE IF EXISTS search; DROP TABLE IF EXISTS links; DROP TABLE IF EXISTS topics;
        CREATE VIRTUAL TABLE search USING fts5(text,chat_id UNINDEXED,message_id UNINDEXED,date UNINDEXED,group_slug UNINDEXED,reply_to UNINDEXED,tokenize='unicode61');
        CREATE TABLE links(url TEXT,domain TEXT,chat_id INTEGER,message_id INTEGER,date TEXT,PRIMARY KEY(url,chat_id,message_id));
        CREATE TABLE topics(topic TEXT,chat_id INTEGER,message_id INTEGER,PRIMARY KEY(topic,chat_id,message_id));''')
        counts=Counter()
        for chat,mid,date,text,reply in source.execute('SELECT chat_id,id,date,text,reply_to FROM messages ORDER BY chat_id,id'):
            if chat not in groups: continue
            text=text or ''
            db.execute('INSERT INTO search VALUES (?,?,?,?,?,?)',(text,chat,mid,date,groups[chat],reply))
            for topic,pattern in PATTERNS.items():
                if pattern.search(text):
                    db.execute('INSERT INTO topics VALUES (?,?,?)',(topic,chat,mid)); counts[topic]+=1
            for raw in set(URL.findall(text)):
                url=normalize(raw)
                if url: db.execute('INSERT OR IGNORE INTO links VALUES (?,?,?,?,?)',(url,urlsplit(url).hostname,chat,mid,date))
        db.executescript('CREATE INDEX link_url ON links(url); CREATE INDEX topic_name ON topics(topic);')
        db.commit()
        rows=db.execute('SELECT url,domain,COUNT(*),COUNT(DISTINCT chat_id),MAX(date) FROM links GROUP BY url ORDER BY COUNT(DISTINCT chat_id) DESC,COUNT(*) DESC,MAX(date) DESC').fetchall()
        url_topics={u:tags or '' for u,tags in db.execute('SELECT l.url,GROUP_CONCAT(DISTINCT t.topic) FROM links l LEFT JOIN topics t ON t.chat_id=l.chat_id AND t.message_id=l.message_id GROUP BY l.url')}
        report=['# Private Telegram source catalog','',f'Generated {datetime.now(timezone.utc).isoformat()}. Links are untrusted leads, not verified recommendations. Frequency is not a quality score. No links were fetched.','', 'Tracking parameters are removed; URLs with obvious credential query keys are excluded. This is a heuristic, not a secret scanner. Original text remains private.','', '## Topic candidates','']
        report += [f'- **{topic}**: {count:,} keyword-matching messages' for topic,count in counts.most_common()]
        report += ['', '## External links','',f'{len(rows):,} distinct normalized URLs. Repeated links are deduplicated; individual message references remain in SQLite. Telegram links are listed separately from external resources.','']
        for heading,telegram in [('External resources',False),('Telegram references',True)]:
            report += [f'### {heading}','']
            for url,domain,count,chats,last in rows:
                if (domain in ('t.me','telegram.me','www.t.me')) != telegram: continue
                refs=db.execute('SELECT chat_id,message_id FROM links WHERE url=? ORDER BY date DESC LIMIT 3',(url,)).fetchall()
                origins=' · '.join(f'[{groups[c]}:{m}]({reference(c,m)})' for c,m in refs)
                report += [f'- <{url}> — {count} mentions / {chats} groups; latest {last[:10]}; topics: {url_topics[url] or 'unclassified'}. {origins}']
        (ROOT/'SOURCE-CATALOG.md').write_text('\n'.join(report)+'\n')
        # Local-only HTML makes the full catalog easy to filter without a server.
        cards=[]
        for url,domain,count,chats,last in rows:
            refs=db.execute('SELECT chat_id,message_id FROM links WHERE url=? ORDER BY date DESC LIMIT 3',(url,)).fetchall()
            refs_html=' '.join(f'<a href="{reference(c,m)}">{html.escape(groups[c])}:{m}</a>' for c,m in refs)
            cards.append(f'<tr><td><a href="{html.escape(url,quote=True)}" rel="noreferrer">{html.escape(url)}</a><small>{html.escape(url_topics[url])}</small></td><td>{count}</td><td>{chats}</td><td>{last[:10]}</td><td>{refs_html}</td></tr>')
        (ROOT/'sources.html').write_text('''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"><title>Private Telegram sources</title><style>body{font:16px system-ui;max-width:1500px;margin:2rem auto;padding:1rem}input{padding:.8rem;width:90%}td,th{padding:.7rem;text-align:left;border-bottom:1px solid #bbb;overflow-wrap:anywhere}table{width:100%;table-layout:fixed}td:first-child{width:45%}a{color:#1463a0}small{display:block}</style><h1>Private Telegram sources</h1><p>Unverified leads, ranked by group coverage and mention count. Repetition does not establish correctness. Nothing is fetched until you open a link. Telegram references require group access.</p><input id="q" aria-label="Filter sources" placeholder="Filter: github, luckfox, multisig, display…"><p id="count"></p><table><thead><tr><th>URL</th><th>Mentions</th><th>Groups</th><th>Latest</th><th>Source messages</th></tr></thead><tbody>'''+''.join(cards)+'''</tbody></table><script>const rows=[...document.querySelectorAll('tbody tr')],q=document.querySelector('#q');function filter(){let n=0;for(const r of rows){r.hidden=!r.textContent.toLowerCase().includes(q.value.toLowerCase());if(!r.hidden)n++}document.querySelector('#count').textContent=n+' matching links'}q.addEventListener('input',filter);filter();</script>''')
        print(json.dumps({'messages':db.execute('SELECT COUNT(*) FROM search').fetchone()[0],'unique_links':len(rows),'topic_candidates':counts},indent=2))

    target.replace(ROOT/'knowledge.sqlite3')

def search(args):
    db=sqlite3.connect(f'file:{ROOT / "knowledge.sqlite3"}?mode=ro',uri=True)
    where=['search MATCH ?']; params=[args.query]
    if args.topic:
        where.append('EXISTS (SELECT 1 FROM topics t WHERE t.topic=? AND t.chat_id=search.chat_id AND t.message_id=search.message_id)'); params.append(args.topic)
    if args.group: where.append('group_slug=?');params.append(args.group)
    if args.since: where.append('date>=?');params.append(args.since)
    for text,chat,mid,date,group,reply in db.execute('SELECT text,chat_id,message_id,date,group_slug,reply_to FROM search WHERE '+' AND '.join(where)+' ORDER BY bm25(search), date DESC LIMIT ?',[*params,args.limit]):
        print(f'\n[{group} {date} #{mid}] {reference(chat,mid)}\n{text[:args.chars]}')
        if args.context:
            for cid,body in db.execute('SELECT message_id,text FROM search WHERE chat_id=? AND (message_id=? OR reply_to=?) ORDER BY message_id LIMIT 8',(chat,reply,mid)):
                print(f'  CONTEXT #{cid}: {body[:args.chars]}')
    db.close()

if __name__=='__main__':
    os.umask(0o077)
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('build'); s=sub.add_parser('search'); s.add_argument('query');s.add_argument('--topic',choices=RULES);s.add_argument('--group');s.add_argument('--since');s.add_argument('--limit',type=int,default=15);s.add_argument('--chars',type=int,default=1200);s.add_argument('--context',action='store_true')
    args=p.parse_args()
    if args.command=='build': build()
    else: search(args)
