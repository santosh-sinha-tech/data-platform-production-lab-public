"""Resolve configuration for source-tree and installed-wheel execution."""
import sys
from pathlib import Path


def config_path(name: str) -> Path:
    source = Path(__file__).resolve().parents[2] / "config" / name
    if source.exists():
        return source
    return Path(sys.prefix) / "share" / "agent-lab" / "config" / name
