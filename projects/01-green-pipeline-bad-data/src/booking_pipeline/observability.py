"""One structured event boundary; collectors can be added without changing rules."""

import json
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, value: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def emit(event: str, **fields):
    print(json.dumps({"event": event, "timestamp": now(), **fields}, sort_keys=True), flush=True)
