"""Offline operator action: stop the gateway, obtain evidence, then reconcile.
No HTTP admin endpoint; local DB filesystem access is administrative authority.
"""

import argparse
from gateway.store import Store

p = argparse.ArgumentParser()
p.add_argument("--db", required=True)
p.add_argument("--tenant", required=True)
p.add_argument("--app", required=True)
p.add_argument("--key", required=True)
p.add_argument("--charge", type=int, required=True)
p.add_argument(
    "--evidence",
    required=True,
    help="Non-sensitive external evidence reference; never prompt text",
)
a = p.parse_args()
if a.charge < 0 or not a.evidence.strip():
    p.error("nonnegative charge and evidence required")
s = Store(a.db)
with s.tx() as c:
    row = c.execute(
        "SELECT * FROM requests WHERE tenant=? AND app=? AND key=?",
        (a.tenant, a.app, a.key),
    ).fetchone()
    if not row or row["state"] != "unresolved":
        p.error("only unresolved records can be reconciled")
    if a.charge > row["reserved"]:
        p.error("charge exceeds reservation; investigate contract violation")
    c.execute(
        "UPDATE requests SET state='reconciled',charged=? WHERE tenant=? AND app=? AND key=?",
        (a.charge, a.tenant, a.app, a.key),
    )
    c.execute(
        "INSERT INTO audits VALUES (?,?,?,?)",
        (a.tenant, a.app, "operator", "reconciled:" + a.evidence),
    )
print("Reconciled. Original key remains terminal and cannot redispatch.")
