"""Small filesystem and Spark utilities shared by the pipeline stages."""

import hashlib
import json
import re
from pathlib import Path

from pyspark.sql import SparkSession


def spark_session():
    spark = (SparkSession.builder.master("local[2]")
             .appName("green-pipeline-bad-data")
             .config("spark.ui.enabled", "false")
             .config("spark.sql.session.timeZone", "UTC")
             .config("spark.sql.ansi.enabled", "true")
             .config("spark.sql.shuffle.partitions", "2")
             .getOrCreate())
    spark.sparkContext.setLogLevel("ERROR")
    return spark


def run_path(root, area, run_id):
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,99}", run_id):
        raise ValueError("Invalid run_id; use 1–100 letters, digits, underscores or hyphens")
    if area not in {"incoming", "processed", "published", "quarantine", "results", "staging"}:
        raise ValueError("Unknown data area")
    return Path(root) / area / run_id


def read_json(path):
    return json.loads(Path(path).read_text())


def fingerprint(directory):
    """Bind a decision to the exact Parquet bytes, including relative filenames."""
    files = sorted(Path(directory).rglob("*.parquet"))
    if not files:
        raise ValueError("No Parquet files available for validation")
    digest = hashlib.sha256()
    for path in files:
        if path.is_symlink():
            raise ValueError("Symlinked data is not supported")
        digest.update(str(path.relative_to(directory)).encode())
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()
