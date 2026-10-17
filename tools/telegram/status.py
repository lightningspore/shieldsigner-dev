"""Report local sync metadata without connecting to Telegram or reading message text."""
import json
from pathlib import Path
import sqlite3
root = Path(__file__).resolve().parent / 'private'
config = json.loads((root/'config.json').read_text())
with sqlite3.connect(f'file:{root / "messages.sqlite3"}?mode=ro',uri=True) as db:
    for group in config['groups']:
        count,first,last = db.execute('SELECT COUNT(*),MIN(date),MAX(date) FROM messages WHERE chat_id=?',(group['id'],)).fetchone()
        complete = db.execute('SELECT completed_at FROM sync_state WHERE chat_id=?',(group['id'],)).fetchone()
        print(f'{group["title"]}: {count:,} stored messages; range {first} to {last}; last completed sync {complete[0] if complete else "not completed"}')
