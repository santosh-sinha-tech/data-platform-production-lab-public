"""Integer micro-USD ledger; one connection/transaction per operation."""

import json
import sqlite3
from contextlib import contextmanager


class Denied(Exception):
    def __init__(self, code, status=403, retry=None):
        self.code, self.status, self.retry = code, status, retry


class Store:
    def __init__(self, path):
        self.path = str(path)
        with self.tx() as c:
            c.executescript(
                """
            CREATE TABLE IF NOT EXISTS requests (
              tenant TEXT, app TEXT, key TEXT, fingerprint TEXT, period TEXT,
              state TEXT, reserved INTEGER, charged INTEGER DEFAULT 0,
              response TEXT, PRIMARY KEY(tenant,app,key));
            CREATE TABLE IF NOT EXISTS windows (
              tenant TEXT, minute INTEGER, requests INTEGER, tokens INTEGER,
              PRIMARY KEY(tenant,minute));
            CREATE TABLE IF NOT EXISTS audits (
              tenant TEXT, app TEXT, request_id TEXT, decision TEXT);
            """
            )

    @contextmanager
    def tx(self):
        c = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        c.row_factory = sqlite3.Row
        try:
            c.execute("BEGIN IMMEDIATE")
            yield c
            c.commit()
        except BaseException:
            c.rollback()
            raise
        finally:
            c.close()

    def recover(self):
        with self.tx() as c:
            c.execute("UPDATE requests SET state='unresolved' WHERE state='reserved'")

    def audit(self, tenant, app, rid, decision):
        with self.tx() as c:
            c.execute(
                "INSERT INTO audits VALUES (?,?,?,?)", (tenant, app, rid, decision)
            )

    def reserve(
        self, tenant, app, key, fingerprint, period, amount, tokens, policy, minute
    ):
        with self.tx() as c:
            old = c.execute(
                "SELECT * FROM requests WHERE tenant=? AND app=? AND key=?",
                (tenant, app, key),
            ).fetchone()
            if old:
                if old["fingerprint"] != fingerprint:
                    raise Denied("idempotency_conflict", 409)
                if old["state"] == "completed":
                    return json.loads(old["response"])
                raise Denied(old["state"], 409)
            rows = c.execute(
                "SELECT app,SUM(charged + CASE WHEN state IN ('reserved','unresolved') THEN reserved ELSE 0 END) AS total FROM requests WHERE tenant=? AND period=? GROUP BY app",
                (tenant, period),
            ).fetchall()
            if (
                sum(r["total"] for r in rows) + amount > policy["budget"]
                or sum(r["total"] for r in rows if r["app"] == app) + amount
                > policy["app_budget"]
            ):
                raise Denied("budget_exceeded", 402)
            w = c.execute(
                "SELECT * FROM windows WHERE tenant=? AND minute=?", (tenant, minute)
            ).fetchone()
            if w and (
                w["requests"] >= policy["rpm"] or w["tokens"] + tokens > policy["tpm"]
            ):
                raise Denied("rate_limit", 429, 60)
            if tokens > policy["tpm"]:
                raise Denied("rate_limit", 429, 60)
            active = c.execute(
                "SELECT COUNT(*) FROM requests WHERE tenant=? AND state='reserved'",
                (tenant,),
            ).fetchone()[0]
            if active >= policy["concurrency"]:
                raise Denied("concurrency_limit", 429, 1)
            c.execute(
                "INSERT INTO windows VALUES (?,?,1,?) ON CONFLICT(tenant,minute) DO UPDATE SET requests=requests+1,tokens=tokens+excluded.tokens",
                (tenant, minute, tokens),
            )
            c.execute(
                "INSERT INTO requests(tenant,app,key,fingerprint,period,state,reserved) VALUES (?,?,?,?,?,'reserved',?)",
                (tenant, app, key, fingerprint, period, amount),
            )

    def finish(self, tenant, app, key, state, charged=0, response=None):
        with self.tx() as c:
            c.execute(
                "UPDATE requests SET state=?,charged=?,response=? WHERE tenant=? AND app=? AND key=? AND state='reserved'",
                (state, charged, json.dumps(response), tenant, app, key),
            )

    def records(self, table, tenant):
        assert table in ("requests", "audits")
        with self.tx() as c:
            return [
                dict(r)
                for r in c.execute(f"SELECT * FROM {table} WHERE tenant=?", (tenant,))
            ]
