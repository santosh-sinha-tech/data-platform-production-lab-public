"""Durable decisions and write reservations for a single SQLite gateway."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path


class Store:
    def __init__(self, path: Path):
        self.path = path
        self.ledger = path.with_name(path.stem + "-effects.sqlite")
        with closing(sqlite3.connect(self.ledger)) as db, db:
            db.execute("CREATE TABLE IF NOT EXISTS effects (tool TEXT, target TEXT)")
        with closing(sqlite3.connect(path)) as db, db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS approval (
                    id TEXT PRIMARY KEY, binding TEXT, approved REAL, expires REAL,
                    used INTEGER DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS operation (
                    id TEXT PRIMARY KEY, status TEXT
                );
                CREATE TABLE IF NOT EXISTS audit (event TEXT);
            """)

    def approve(self, identifier, binding, now, expires, event):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("INSERT INTO approval VALUES (?, ?, ?, ?, 0)",
                       (identifier, binding, now, expires))
            self._audit(db, event, "approval_issued")

    @staticmethod
    def _audit(db, event, outcome):
        db.execute("INSERT INTO audit VALUES (?)", (json.dumps({**event, "outcome": outcome}),))

    def start(self, event, operation, approval, binding, now):
        """Commit intent and approval consumption together before dispatch."""
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            started = "dispatched"
            wait_ms = None
            if approval is not None:
                row = db.execute(
                    "SELECT binding, approved, expires, used FROM approval WHERE id=?",
                    (approval,),
                ).fetchone()
                if row is None or row[0] != binding:
                    return "approval_binding", None
                if row[3]:
                    return "approval_replay", None
                if now >= row[2]:
                    return "approval_expired", None
                wait_ms = (now - row[1]) * 1000
            if operation is not None:
                inserted = db.execute("INSERT OR IGNORE INTO operation VALUES (?, ?)",
                                      (operation, "in_flight"))
                if not inserted.rowcount:
                    return "duplicate", None
            if approval is not None:
                db.execute("UPDATE approval SET used=1 WHERE id=?", (approval,))
            self._audit(db, event, started)
        return started, wait_ms

    def finish(self, event, outcome, operation=None):
        with closing(sqlite3.connect(self.path)) as db, db:
            if operation is not None:
                db.execute("UPDATE operation SET status=? WHERE id=?", (outcome, operation))
            self._audit(db, event, outcome)

    def events(self):
        with closing(sqlite3.connect(self.path)) as db:
            return [json.loads(row[0]) for row in db.execute("SELECT event FROM audit ORDER BY rowid")]

    def effect_count(self):
        with closing(sqlite3.connect(self.ledger)) as db:
            return db.execute("SELECT COUNT(*) FROM effects").fetchone()[0]
