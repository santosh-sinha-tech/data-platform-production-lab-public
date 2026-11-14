import json
import re
import sqlite3
from pathlib import Path
from typing import Any
from .models import Conflict, EDGES

SCHEMA = """
CREATE TABLE IF NOT EXISTS executions (
 id TEXT PRIMARY KEY, tenant TEXT, subject TEXT, role TEXT, request_key TEXT,
 request_hash TEXT, plan TEXT, status TEXT, cursor INTEGER DEFAULT 0,
 cost REAL DEFAULT 0, deadline REAL, created REAL, error TEXT,
 UNIQUE(tenant,request_key));
CREATE TABLE IF NOT EXISTS steps (
 execution TEXT, idx INTEGER, status TEXT, attempts INTEGER DEFAULT 0,
 output TEXT, PRIMARY KEY(execution,idx));
CREATE TABLE IF NOT EXISTS approvals (
 execution TEXT, idx INTEGER, digest TEXT, expires REAL, decision TEXT,
 approver TEXT, requested REAL, decided REAL, PRIMARY KEY(execution,idx));
CREATE TABLE IF NOT EXISTS effects (
 tenant TEXT, step_key TEXT, tool TEXT, output TEXT, compensated INTEGER,
 PRIMARY KEY(tenant,step_key));
CREATE TABLE IF NOT EXISTS audit (
 seq INTEGER PRIMARY KEY, execution TEXT, at REAL, event TEXT, detail TEXT);
CREATE TABLE IF NOT EXISTS observations (
 seq INTEGER PRIMARY KEY, execution TEXT, name TEXT, tool TEXT, value REAL);
"""


def redact(value: Any) -> str:
    text = json.dumps(value, sort_keys=True)
    text = re.sub(
        r"(?i)(token|password|secret|api_key)=[^\s\";]+", r"\1=[REDACTED]", text
    )
    text = re.sub(r"[\w.+-]+@[\w.-]+", "[REDACTED_EMAIL]", text)
    return text


class Store:
    def __init__(self, path: str | Path) -> None:
        self.db = sqlite3.connect(path, timeout=10, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript(SCHEMA)
        self.db.commit()

    def transition(self, eid: str, target: str) -> None:
        old = self.db.execute(
            "SELECT status FROM executions WHERE id=?", (eid,)
        ).fetchone()[0]
        if target not in EDGES[old]:
            raise Conflict(f"invalid transition {old} -> {target}")
        self.db.execute("UPDATE executions SET status=? WHERE id=?", (target, eid))

    def audit(self, eid: str, at: float, event: str, detail: Any = None) -> None:
        safe = redact(detail or {})
        self.db.execute(
            "INSERT INTO audit(execution,at,event,detail) VALUES (?,?,?,?)",
            (eid, at, event, safe),
        )
        # Correlation is stored durably; optional caller can export as JSONL.

    def observe(
        self, eid: str, name: str, value: float = 1, tool: str = "workflow"
    ) -> None:
        self.db.execute(
            "INSERT INTO observations(execution,name,tool,value) VALUES (?,?,?,?)",
            (eid, name, tool, value),
        )

    def close(self) -> None:
        self.db.close()
