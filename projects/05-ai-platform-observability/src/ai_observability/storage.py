import json
import sqlite3
import threading

class Store:
    def __init__(self, path: str):
        self.db=sqlite3.connect(path,check_same_thread=False)
        self.lock=threading.Lock()
        self.db.execute('CREATE TABLE IF NOT EXISTS requests (id TEXT PRIMARY KEY, tenant TEXT, record TEXT)')
    def save(self, record: dict) -> None:
        with self.lock, self.db:
            self.db.execute('INSERT INTO requests VALUES (?,?,?)',
                            (record['request_id'],record['tenant'],json.dumps(record)))
    def records(self, tenant: str) -> list[dict]:
        with self.lock:
            return [json.loads(r[0]) for r in self.db.execute('SELECT record FROM requests WHERE tenant=?',(tenant,))]
    def close(self) -> None:
        self.db.close()
