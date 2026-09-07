import json
import sqlite3
import time
from pathlib import Path


class PayloadLedger:
    """Önce kalıcı niyet, sonra komut. Çökme halinde otomatik tekrar yok."""
    def __init__(self, root, sortie):
        Path(root).mkdir(parents=True, exist_ok=True)
        self.path = Path(root)/'payloads.sqlite3'
        self.sortie = sortie
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS payloads (sortie TEXT, color TEXT, status TEXT, body TEXT, PRIMARY KEY(sortie,color))')

    def connect(self):
        db = sqlite3.connect(self.path, timeout=.1)
        db.execute('PRAGMA synchronous=FULL')
        return db

    def reserve(self, color, body):
        try:
            with self.connect() as db:
                db.execute('INSERT INTO payloads VALUES (?,?,?,?)', (self.sortie, color, 'UNCERTAIN', json.dumps(body)))
            return True
        except sqlite3.IntegrityError:
            return False

    def update(self, color, status):
        with self.connect() as db:
            db.execute('UPDATE payloads SET status=? WHERE sortie=? AND color=?', (status, self.sortie, color))

    def statuses(self):
        with self.connect() as db:
            return dict(db.execute('SELECT color,status FROM payloads WHERE sortie=?', (self.sortie,)))
